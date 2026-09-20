import datetime
import unittest
from collections import Counter
from PIL import Image, ImageDraw, ImageFont
from screen_clock import period_for_minute, render_frame


class PeriodTests(unittest.TestCase):
    def test_boundaries(self):
        for stamp, expected in [('04:59:59', 'NIGHT'), ('05:00:00', 'MORNING'),
                                ('10:59:59', 'MORNING'), ('11:00:00', 'DAY'),
                                ('16:59:59', 'DAY'), ('17:00:00', 'EVENING'),
                                ('20:59:59', 'EVENING'), ('21:00:00', 'NIGHT'),
                                ('23:59:59', 'NIGHT'), ('00:00:00', 'NIGHT')]:
            with self.subTest(time=stamp):
                now = datetime.datetime.strptime(stamp, '%H:%M:%S')
                self.assertEqual(period_for_minute(now.hour * 60 + now.minute)[0], expected)

    def test_entire_day(self):
        labels = [period_for_minute(m)[0] for m in range(1440)]
        self.assertEqual(Counter(labels), {'MORNING': 360, 'DAY': 360, 'EVENING': 240, 'NIGHT': 480})
        self.assertEqual([m for m in range(1, 1440) if labels[m] != labels[m-1]], [300, 660, 1020, 1260])

    def test_out_of_range(self):
        for minute in [-1, 1440]:
            with self.assertRaises(ValueError):
                period_for_minute(minute)

    def test_render_bounds_and_labels(self):
        font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 18)
        image = Image.new('RGB', (240, 135))
        draw = ImageDraw.Draw(image)
        for hour, label in [(5, 'MORNING'), (11, 'DAY'), (17, 'EVENING'), (21, 'NIGHT')]:
            for simulated in [False, True]:
                now = datetime.datetime(2026, 9, 19, hour)
                lines = render_frame(image, font, now, simulated)
                self.assertEqual(lines[0][2], 'SIMULATED' if simulated else 'LIVE')
                self.assertEqual(lines[1][2], label)
                self.assertEqual(lines[3][2], now.strftime('%H:%M:%S'))
                for x, y, text in lines:
                    left, top, right, bottom = draw.textbbox((x, y), text, font=font)
                    self.assertTrue(0 <= left < right <= 240 and 0 <= top < bottom <= 135, text)


if __name__ == '__main__':
    unittest.main()
