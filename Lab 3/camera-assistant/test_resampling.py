"""Check real sample-rate conversion preserves pitch and rejects aliasing."""
import unittest
import numpy as np
from voice import resample_audio


class ResamplingTest(unittest.TestCase):
    def test_duration_and_pitch(self):
        for source, target in [(44100, 16000), (22050, 48000)]:
            with self.subTest(source=source, target=target):
                tone = np.sin(2*np.pi*1000*np.arange(source)/source).astype('float32')
                result = resample_audio(tone, source, target)
                self.assertEqual(len(result), target)
                self.assertEqual(np.argmax(np.abs(np.fft.rfft(result))), 1000)

    def test_rejects_above_nyquist_before_downsampling(self):
        high = np.sin(2*np.pi*12000*np.arange(48000)/48000).astype('float32')
        result = resample_audio(high, 48000, 16000)
        self.assertLess(np.sqrt(np.mean(result[100:-100]**2)), 0.02)


if __name__ == '__main__':
    unittest.main()
