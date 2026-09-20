import subprocess
import tempfile
import unittest
import wave
from pathlib import Path
from unittest.mock import Mock, patch

from audio_output import AudioOutput
from generate_audio import generate


class AudioTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        for name in ('morning', 'day', 'evening'):
            (Path(self.tmp.name) / (name + '.wav')).touch()
        self.audio = AudioOutput(assets=self.tmp.name)
        self.addCleanup(self.audio.stop)
        self.available = patch.object(self.audio, '_available', return_value=True).start()
        self.addCleanup(patch.stopall)
        self.players = []
        def spawn(*args, **kwargs):
            player = Mock()
            player.poll.return_value = None
            self.players.append(player)
            return player
        self.spawn = patch('audio_output.subprocess.Popen', side_effect=spawn).start()

    def test_unchanged_period_and_transition_ownership(self):
        self.audio.update('MORNING', 0)
        for second in range(1, 25):
            self.audio.update('MORNING', second)
        self.assertEqual(self.spawn.call_count, 1)
        self.audio.update('DAY', 25)
        self.players[0].terminate.assert_called_once()
        self.players[0].wait.assert_called_once()
        self.audio.update('EVENING', 26)
        self.players[1].terminate.assert_called_once()
        self.audio.update('NIGHT', 27)
        self.players[2].terminate.assert_called_once()
        self.assertIsNone(self.audio.player)
        self.audio.update('NIGHT', 40)
        self.assertEqual(self.spawn.call_count, 3)

    def test_disconnect_and_recovery(self):
        self.audio.update('DAY', 0)
        self.available.return_value = False
        self.audio.update('DAY', 5)
        self.players[0].terminate.assert_called_once()
        self.available.return_value = True
        self.audio.update('DAY', 9)
        self.assertEqual(self.spawn.call_count, 1)
        self.audio.update('DAY', 10)
        self.assertEqual(self.spawn.call_count, 2)

    def test_failed_player_is_retried(self):
        self.audio.update('DAY', 0)
        self.players[0].poll.return_value = 1
        self.audio.update('DAY', 1)
        self.assertEqual(self.spawn.call_count, 1)
        self.audio.update('DAY', 5)
        self.assertEqual(self.spawn.call_count, 2)

    def test_missing_asset_and_tool_errors_are_nonfatal(self):
        (Path(self.tmp.name) / 'day.wav').unlink()
        self.audio.update('DAY', 0)
        self.spawn.assert_not_called()
        self.available.side_effect = subprocess.TimeoutExpired('pactl', 0.5)
        self.audio.update('DAY', 5)
        self.available.side_effect = None
        self.spawn.side_effect = FileNotFoundError('ffplay')
        self.audio.update('MORNING', 6)
        self.assertIsNone(self.audio.player)

    def test_cleanup_kills_unresponsive_player(self):
        self.audio.update('DAY', 0)
        self.players[0].wait.side_effect = [subprocess.TimeoutExpired('ffplay', 0.5), 0]
        self.audio.stop()
        self.players[0].kill.assert_called_once()
        self.assertIsNone(self.audio.player)

    def test_assets(self):
        generate(self.tmp.name)
        for name in ('morning', 'day', 'evening'):
            with wave.open(str(Path(self.tmp.name) / (name + '.wav'))) as audio:
                self.assertEqual(audio.getnchannels(), 1)
                self.assertEqual(audio.getsampwidth(), 2)
                self.assertEqual(audio.getnframes(), 8 * audio.getframerate())
                data = audio.readframes(audio.getnframes())
                self.assertTrue(any(data))
                self.assertEqual(data[:2], b'\x00\x00')
                self.assertEqual(data[-2:], b'\x00\x00')


if __name__ == '__main__':
    unittest.main()
