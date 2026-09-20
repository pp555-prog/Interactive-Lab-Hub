"""Generate original eight-second tonal loops using only the standard library."""
import math
from pathlib import Path
import struct
import wave

RATE = 24000
DURATION = 8


def generate(destination=None):
    destination = Path(destination) if destination else Path(__file__).resolve().parent / 'assets' / 'audio'
    destination.mkdir(parents=True, exist_ok=True)
    patterns = {
        'morning': [(0.3, 523.25, 1.1), (3.0, 659.25, 1.1), (5.7, 783.99, 1.1)],
        'day': [(0.2 + i * 0.9, (523.25, 659.25, 783.99, 659.25)[i % 4], 0.6) for i in range(8)],
        'evening': [(0.3, 261.63, 2.5), (4.1, 329.63, 2.5)],
    }
    for name, notes in patterns.items():
        samples = [0.0] * (RATE * DURATION)
        for start, frequency, length in notes:
            for i in range(int(length * RATE)):
                t = i / RATE
                envelope = math.sin(math.pi * t / length) ** 2
                samples[int(start * RATE) + i] += 20000 * envelope * math.sin(2 * math.pi * frequency * t)
        with wave.open(str(destination / (name + '.wav')), 'wb') as output:
            output.setparams((1, 2, RATE, 0, 'NONE', 'not compressed'))
            output.writeframes(b''.join(struct.pack('<h', round(sample)) for sample in samples))


if __name__ == '__main__':
    generate()
