# PiClock final design record

Closed: 2026-09-27, following Pablo's confirmation that Lab 2 is done.
This document supersedes the historical development roadmap. See
[progress and verification](PROGRESS.md) and [the report](README.md).

## Delivered Soundscape Clock

The Raspberry Pi 5 reads local time each second and displays LIVE, a fixed
time-of-day period, its message, and HH:MM:SS on the Mini PiTFT. The boundaries
are expressive time periods, not astronomical sunrise or sunset calculations.

| Period | Local time, start inclusive | Message | Optional USB audio |
|---|---|---|---|
| MORNING | 05:00–11:00 | A new day begins | Sparse higher tones |
| DAY | 11:00–17:00 | Day in progress | More frequent notes |
| EVENING | 17:00–21:00 | Day winding down | Lower sustained tones |
| NIGHT | 21:00–05:00 | Time to rest | Silence |

`screen_clock.py` owns the time/render loop. `audio_output.py` owns one ffplay
child, explicitly routed to the Jieli USB sink. Unchanged periods retain playback;
transitions stop the previous player. Missing playback resources leave the display
running, with five-second retry intervals and bounded sink checks. Exit stops the
owned player and releases the display resources.

The published command interface is `--audio`, `--test-time HH:MM`, and `--frames N`.
Simulated frames are labeled SIMULATED; normal operation reads fresh local time.
There is no implemented encoder PREVIEW mode or servo control.

## Hardware configuration retained

The published TFT setup uses hardware SPI, CS D5, DC D25, no reset pin, 64 MHz,
ST7789 135×240 with offsets 53/40, a 240×135 landscape canvas, rotation 90,
DejaVuSans 18, and backlight D22. Preserve this known configuration when revisiting
Lab 2. Do not run the custom clock concurrently with `piscreen.service`.

The three audio assets are eight-second, mono, 24 kHz, 16-bit WAVs synthesized by
`generate_audio.py`. No sampled third-party recordings were used. USB replaced
the original Bluetooth proposal. The student accepted the revised louder loops.

## Concepts retained as design history

The report preserves two distinct concepts: the Daylight / Energy Clock and the
Soundscape Clock. The former proposed a sun/moon arc, alternate time views, and
a pointer; the latter proposed scrubbing represented time with an encoder.
Encoder controls, servo motion, alternate views, IMU, capacitive touch, microphone
interaction, and astronomical calculations are proposals, not delivered features
or tasks for the next workspace.

The separate Pi and Windows ambient-light experiment is preserved outside the published
implementation. Its sensor-absent fallback was historically exercised, but physical
sensor response was not established. It must not be described as validated smooth
TFT dimming: the current digital backlight path applies an on/off threshold.

## Evidence, authorship, and archive

The report retains the student's photographs, concept images, feedback, and video
links. Prior automated and hardware checks are summarized in PROGRESS.md with
their dates and limitations. No new hardware acceptance is claimed at closeout.

Codex assisted with design organization, period/render logic, simulated-time
controls, USB playback, synthesized tones, tests, deployment checks, and the
documentation closeout. The student confirmed audio behavior and supplied the
report evidence and completion decision. Earlier ChatGPT assistance contributed
design ideas and suggested display code, as recorded in the original notes.

The [original design and test log](archive/2026-09-27/PROJECT_DESIGN.md) is preserved
verbatim. Its pending tasks and agent continuation instructions are historical.
Lab 2 remains closed unless the student explicitly requests further work.
