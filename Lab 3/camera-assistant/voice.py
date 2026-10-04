"""One isolated microphone turn, followed by wizard-approved playback."""
import time
from math import gcd
from pathlib import Path


def resample_audio(samples, source_rate, target_rate):
    """Preserve duration and filter aliasing when matching USB device rates."""
    if source_rate == target_rate:
        return samples
    from scipy.signal import resample_poly
    divisor = gcd(int(source_rate), int(target_rate))
    return resample_poly(samples, int(target_rate) // divisor, int(source_rate) // divisor).astype('float32')


class Voice:
    def __init__(self, input_device=None, output_device=None, silence=1.5):
        import numpy as np
        import sounddevice as sd
        import sherpa_onnx
        from faster_whisper import WhisperModel
        from piper import PiperVoice
        self.np, self.sd, self.sherpa = np, sd, sherpa_onnx
        self.input, self.output, self.silence = input_device, output_device, silence
        self.input_rate = 16000
        try:
            sd.check_input_settings(device=input_device, channels=1, dtype='float32', samplerate=16000)
        except sd.PortAudioError:
            self.input_rate = int(sd.query_devices(input_device, 'input')['default_samplerate'])
            sd.check_input_settings(device=input_device, channels=1, dtype='float32', samplerate=self.input_rate)
        self.output_rate = int(sd.query_devices(output_device, 'output')['default_samplerate'])
        sd.check_output_settings(device=output_device, channels=1, dtype='float32', samplerate=self.output_rate)
        lab = Path(__file__).resolve().parent.parent
        self.recognizer = WhisperModel("tiny.en", device="cpu", compute_type="int8")
        self.speaker = PiperVoice.load(str(lab / "voices/en_US-lessac-medium.onnx"))
        self.vad_path = lab / "models/silero_vad.onnx"

    def say(self, text):
        first = None
        for chunk in self.speaker.synthesize(text):
            audio = self.np.frombuffer(chunk.audio_int16_bytes, dtype=self.np.int16).astype(self.np.float32) / 32768.0
            audio = resample_audio(audio, chunk.sample_rate, self.output_rate)
            if first is None:
                first = time.monotonic()
            self.sd.play(audio, samplerate=self.output_rate, device=self.output)
            self.sd.wait()
        return first

    def listen(self, stop):
        config = self.sherpa.VadModelConfig()
        config.silero_vad.model = str(self.vad_path)
        config.silero_vad.min_silence_duration = self.silence
        config.sample_rate = 16000
        vad = self.sherpa.VoiceActivityDetector(config, buffer_size_in_seconds=35)
        window = config.silero_vad.window_size
        buffer = self.np.empty(0, dtype=self.np.float32)
        begun, last_voice = False, None
        opened = time.monotonic()
        # InputStream exists only during LISTENING, so cues/replies cannot be captured.
        with self.sd.InputStream(channels=1, dtype="float32", samplerate=self.input_rate,
                                 device=self.input) as stream:
            while not stop.is_set():
                chunk, overflow = stream.read(self.input_rate // 10)
                if overflow:
                    raise RuntimeError("Microphone overflow; repeat this trial")
                chunk = resample_audio(chunk.reshape(-1), self.input_rate, 16000)
                buffer = self.np.concatenate([buffer, chunk])
                while len(buffer) >= window:
                    vad.accept_waveform(buffer[:window])
                    buffer = buffer[window:]
                    if vad.is_speech_detected():
                        begun, last_voice = True, time.monotonic()
                if not vad.empty():
                    samples = self.np.array(vad.front.samples, dtype=self.np.float32)
                    vad.pop()
                    endpoint = time.monotonic()
                    break
                elapsed = time.monotonic() - opened
                if (not begun and elapsed >= 10) or elapsed >= 30:
                    return None
            else:
                return None
        return samples, {"endpoint_at": endpoint, "last_vad_speech_at": last_voice}

    def transcribe(self, samples):
        began = time.monotonic()
        segments, _ = self.recognizer.transcribe(samples, beam_size=1)
        text = " ".join(s.text.strip() for s in segments)
        return text, time.monotonic() - began
