"""Optional period loops through the verified USB speaker and existing ffplay."""
import os
from pathlib import Path
import subprocess
import sys
import time

USB_SINK = 'alsa_output.usb-Jieli_Technology_UACDemoV1.0_415035473535330D-00.analog-stereo'
ASSETS = Path(__file__).resolve().parent / 'assets' / 'audio'


class AudioOutput:
    def __init__(self, sink=USB_SINK, assets=ASSETS):
        self.sink = sink
        self.assets = Path(assets)
        self.period = None
        self.player = None
        self.next_check = 0.0
        self.last_status = None

    def _status(self, message):
        if message != self.last_status:
            print('Audio: ' + message, file=sys.stderr, flush=True)
            self.last_status = message

    def _available(self):
        result = subprocess.run(['pactl', 'list', 'short', 'sinks'],
                                capture_output=True, text=True, timeout=0.5, check=True)
        return any(len(parts := line.split()) > 1 and parts[1] == self.sink
                   for line in result.stdout.splitlines())

    def stop(self):
        if self.player is not None:
            if self.player.poll() is None:
                self.player.terminate()
                try:
                    self.player.wait(timeout=0.5)
                except subprocess.TimeoutExpired:
                    self.player.kill()
                    self.player.wait()
            self.player = None

    def update(self, period, now=None):
        now = time.monotonic() if now is None else now
        if period != self.period:
            self.stop()
            self.period = period
            self.next_check = 0.0
        if period == 'NIGHT':
            self._status('night: silent')
            return
        if period not in ('MORNING', 'DAY', 'EVENING'):
            self._status('unknown period: silent')
            return
        if now < self.next_check:
            return
        self.next_check = now + 5.0
        try:
            if not self._available():
                self.stop()
                self._status('USB speaker unavailable; retrying every 5 seconds')
                return
            if self.player is not None and self.player.poll() is None:
                return
            self.stop()
            asset = self.assets / (period.lower() + '.wav')
            if not asset.is_file():
                self._status('missing ' + asset.name + '; retrying every 5 seconds')
                return
            env = dict(os.environ, SDL_AUDIODRIVER='pulseaudio', PULSE_SINK=self.sink)
            self.player = subprocess.Popen(
                ['ffplay', '-nodisp', '-autoexit', '-loglevel', 'error',
                 '-loop', '0', str(asset)], env=env,
                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL)
            self._status(period.lower() + ' playback started')
        except (OSError, subprocess.SubprocessError) as exc:
            self.stop()
            self._status(type(exc).__name__ + '; retrying every 5 seconds')
