"""Load models and test VAD/TTS generation without capture or playback."""
from voice import Voice

voice = Voice()
config = voice.sherpa.VadModelConfig()
config.silero_vad.model = str(voice.vad_path)
config.silero_vad.min_silence_duration = voice.silence
config.sample_rate = 16000
vad = voice.sherpa.VoiceActivityDetector(config, buffer_size_in_seconds=35)
vad.accept_waveform(voice.np.zeros(512, dtype=voice.np.float32))
assert not vad.is_speech_detected()
chunk = next(iter(voice.speaker.synthesize('Camera Assistant is ready.')))
assert chunk.audio_int16_bytes
print('Whisper and Piper loaded; silent VAD input and TTS generation passed. No capture or playback.')
