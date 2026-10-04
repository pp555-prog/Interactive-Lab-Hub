# Part 1A — Text to speech

## Listening comparison

Pablo compared eSpeak, Festival, and Piper through the Pi's USB speaker with
the same greeting: “Hello, Pablo. Welcome back. What would you like to work
on today?” The initial two-word greeting was extended because it was too
short to judge the voices well.

- **eSpeak:** Sounded fine but a bit robotic on the short greeting; still
  robotic with the longer greeting.
- **Festival:** More human-like than eSpeak, but still robotic.
- **Piper (en_US-lessac-medium):** Sounded best; selected for the greeting.

The words stayed the same, but the perceived speaker changed: eSpeak sounded
robotic, while Festival sounded more human-like. Piper was Pablo's preferred
voice. This paragraph summarizes Pablo's listening feedback; the assignment reflection
is included in the lab README.

## Personalized greeting

Run from the Lab 3 directory on the Pi:

```bash
./speech-scripts/greet_pablo.sh
```

The script uses the lab virtual environment and downloaded Piper voice, creates
a temporary WAV, plays it through the default PipeWire speaker, and removes
the temporary file when finished. It also works from another working directory.

## Setup and checks

- Created the lab `.venv` and installed `requirements.txt`.
- Completed the course `speech-scripts/setup.sh`.
- Python dependency imports and `pip check` passed.
- Silero VAD loaded successfully; tiny.en was cached by setup.
- All three speech engines synthesized greetings and were played for Pablo.
- Webcam microphone recording and USB speaker playback passed with Pablo's
  confirmation. Speaker volume was set to 100% at his request.

## AI assistance

Pablo directed the setup and speech comparisons, assessed the voices, and chose
Piper for his greeting. Under his direction, Codex assisted with Pi setup, audio
checks, running comparison commands, implementing the greeting script, and
organizing these notes. No participant studies or later lab activities are
claimed here.
