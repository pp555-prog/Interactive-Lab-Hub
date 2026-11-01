"""
Music and alarm playback with fades, for the sleep tracker.

A WAV file is streamed to aplay in small chunks, and every chunk is multiplied by a
gain that follows a ramp, so the lullaby can fade out after half an hour and the alarm
can start almost silent and grow. Runs in a background thread; stop() ends it.

    python audio.py lullaby.wav            # play once at half volume (Ctrl-C to stop)
"""
import subprocess
import sys
import threading
import time
import wave

import numpy as np

import voice


class Player:
    def __init__(self, path, loop=False, gain=1.0, fade_in=0.0, start_gain=None,
                 stop_after=None, fade_out=0.0):
        """gain: final volume 0..1. fade_in: seconds from start_gain to gain.
        stop_after: seconds until the music stops, ending with a fade_out of that many seconds."""
        self.path, self.loop = path, loop
        self.gain, self.fade_in = gain, fade_in
        self.start_gain = gain if start_gain is None else start_gain
        self.stop_after, self.fade_out = stop_after, fade_out
        self._stop = threading.Event()
        self.thread = threading.Thread(target=self._run, daemon=True)

    def start(self):
        self.thread.start()
        return self

    def stop(self, wait=True):
        self._stop.set()
        if wait and self.thread.is_alive():
            self.thread.join(timeout=3)

    def playing(self):
        return self.thread.is_alive()

    def gain_at(self, t):
        g = self.gain
        if self.fade_in and t < self.fade_in:
            g = self.start_gain + (self.gain - self.start_gain) * t / self.fade_in
        if self.stop_after is not None and self.fade_out and t > self.stop_after - self.fade_out:
            g *= max(0.0, (self.stop_after - t) / self.fade_out)
        return g

    def _run(self):
        w = wave.open(self.path)
        rate, ch = w.getframerate(), w.getnchannels()
        out = subprocess.Popen(["aplay", "-q", "-D", voice.usb_device(), "-r", str(rate), "-c", str(ch),
                                "-f", "S16_LE", "-t", "raw", "-"], stdin=subprocess.PIPE)
        chunk = rate // 10                                   # 0.1 s at a time
        t = 0.0
        try:
            while not self._stop.is_set():
                if self.stop_after is not None and t >= self.stop_after:
                    break
                data = w.readframes(chunk)
                if not data:
                    if not self.loop:
                        break
                    w.rewind()
                    continue
                samples = np.frombuffer(data, dtype=np.int16).astype(np.float32) * self.gain_at(t)
                out.stdin.write(np.clip(samples, -32768, 32767).astype(np.int16).tobytes())
                t += len(data) / (2 * ch * rate)
        except BrokenPipeError:
            pass
        finally:
            try:
                out.stdin.close()
            except BrokenPipeError:
                pass
            if self._stop.is_set():
                out.terminate()                              # stop now, do not finish the buffer
            out.wait()
            w.close()


if __name__ == "__main__":
    p = Player(sys.argv[1], gain=0.5).start()
    try:
        while p.playing():
            time.sleep(0.5)
    except KeyboardInterrupt:
        p.stop()
