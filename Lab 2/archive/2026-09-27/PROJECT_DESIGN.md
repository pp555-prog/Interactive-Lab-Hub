# PiClock — Project Design and Agent Handoff

Last updated: 2026-09-19. Intended home: `/home/pi/Interactive-Lab-Hub/Lab 2/PROJECT_DESIGN.md`.

This is the shared project specification and handoff log. Read it before editing; update status, decisions, test evidence, and next steps after work. **Documented proposals are not implemented features.**

## 1. Overview and assignment context

PiClock explores time as an experience: visual day progression, sound, and physical movement, with exact clock time available when useful. Raspberry Pi 5 coordinates a Mini PiTFT, speaker, rotary encoder, and eventually a servo.

Lab 2 context recovered from the previous conversation:
- Part D: get the barebones clock displaying time; the user reported success.
- Part E: brainstorm creative representations beyond a conventional digital/analog clock; document two distinct concepts with separate storyboards and Verplank interaction diagrams.
- Part 2: start with one small modification, demonstrate a barely modified PiClock in a short video, and refine incrementally.
- Document the design, implementation, tests, and AI contributions in the repository. Verify exact submission requirements against the assignment before submitting; the original assignment has not been independently checked for this document.

Design preference: avoid the assignment's coffee-unit example. Use daylight remaining, focus blocks, or sunset countdown if alternative units are developed. Keep the two concepts separate in design artifacts.

## 2. Current working baseline

**User-confirmed:** `screen_clock.py` displays current time on the Mini PiTFT.

| Item | Known location / behavior |
|---|---|
| Computer | Raspberry Pi 5 |
| Repository / working directory | `~/Interactive-Lab-Hub/Lab 2` |
| Python environment | `~/venv` |
| Existing display script | `screen_clock.py` |
| Display ownership | Stop `piscreen.service` before custom display scripts |
| Editing route | SSH and `nano` work for the user |
| Known issue | VS Code Remote-SSH server prerequisites failed on the Pi; cause unresolved |

Previous snippets use `datetime`, `time`, Pillow, `board`, `digitalio`, and `adafruit_rgb_display.st7789`. Inspect the actual script before changing imports, display initialization, pins, dimensions, fonts, or rotation. Prior indentation issues were resolved; use four spaces consistently.

On the Pi:
```bash
source ~/venv/bin/activate
cd ~/Interactive-Lab-Hub/"Lab 2"
sudo systemctl stop piscreen.service --now
python screen_clock.py
```
Stop the custom script with Ctrl+C before restoring the normal service:
```bash
sudo systemctl start piscreen.service --now
```
Do not run competing display processes. Record whether the service was running before testing and restore that state afterward.

**Access update (2026-09-19):** Password-free BatchMode SSH from Windows to `pi@pablo98pi` is verified using the existing Ed25519 key. Phase 1 is deployed on the Pi. Automated display writes passed; physical appearance and the demonstration video still require user verification. See the phase 1 evidence below.

## 3. Hardware inventory and intended roles

Inventory is supplied project context; exact breakout models, wiring, addresses, and operational status still need verification.

| Hardware | Role / scope |
|---|---|
| Raspberry Pi 5 | Time source, state controller, Python application |
| Adafruit Mini PiTFT | Working visual output; preserve existing initialization |
| Bluetooth speaker with microphone | Period soundscapes; microphone is optional and unused initially |
| Rotary encoder | Scrub represented time; push switch returns to live time if available |
| Servo + Servo pHAT | Physical pointer to represented time; later phase |
| APDS9960 ambient-light/proximity/RGB/gesture sensor | Optional ambient-light adaptation; other sensing functions deferred |
| IMU | Optional tilt/tap interaction; outside initial scope |
| PCF8574 | Optional I/O expansion if needed after pin planning |
| MPR121 | Optional capacitive-touch controls; outside initial scope |
| Breadboard | Prototype interconnections |
| Qwiic gear | Compatible sensor cabling/adapters; verify each board's electrical requirements |

Before connecting additions, record occupied GPIO pins, bus/address assignments, exact board variants, supply requirements, and connector orientation. Check Pi 5 library compatibility and conflicts with the TFT/pHAT. Verify servo power and common-ground requirements from the actual hardware documentation; do not assume the Pi can power the motor safely. No pin numbers or servo pulse limits are approved by this document.

## 4. Two design concepts

### Idea 1 — Daylight / Energy Clock

“Feel the day” through a sun/moon arc, visual intensity, and a physical pointer. The clock communicates day progression rather than keeping numerical time central. Possible views include daylight remaining, focus blocks, and sunset countdown. In this concept, turning the encoder selects a view; pressing reveals exact time temporarily. Ambient light can adjust brightness, and an optional IMU interaction could reveal time.

Storyboard: morning arc appears → user glances at day progress → turns encoder to another view → room darkens and display dims → press reveals time → evening arc/pointer communicates completion.

Fixed day periods are a prototype metaphor, not calculated daylight. Actual sunrise/sunset and daylight remaining would require an agreed location, date-aware calculation, and explicit scope expansion. “Energy” is expressive, not a measured health value.

### Idea 2 — Soundscape Clock (preferred development direction)

Represent time through distinct soundscapes, synchronized with screen imagery and a physical pointer. Turn the encoder to scrub backward/forward through a day; press to return to the present and briefly reveal exact time. Morning may sound light and sparse, daytime more active, evening slower, and night minimal or silent. Start with one local sound per period; continuous sonic variation is a later refinement.

Storyboard: clock reflects present period → user turns knob → preview time moves → screen and sound change together → pointer follows → press returns all outputs to current time.

The two ideas share a time engine and outputs but have different encoder mappings. Implement Idea 2's scrub interaction for the preferred plan; do not silently combine it with Idea 1's view selection.

## 5. Development sequence and acceptance criteria

1. **Time-of-day screen:** modify the working script to display MORNING / DAY / EVENING / NIGHT from actual local time. Labels and short messages first; graphics later. Pass: all four periods and boundaries render correctly without extra hardware.
2. **Period audio:** play an associated local sound through the Bluetooth speaker. Pass: changes follow period transitions, unchanged periods do not restart playback, and speaker loss does not stop the display.
3. **Encoder time scrub:** turning changes represented time, visual, and sound together; pressing returns to live time. Pass: wraparound, debouncing, preview indication, and return-to-now work.
4. **Servo time position:** map represented day progress to a calibrated safe pointer range. Pass: live/preview use the same state, endpoints are safe, and movement is smooth enough without chatter.
5. **Optional ambient adaptation:** APDS9960 adjusts brightness and possibly volume within configured bounds. Pass: stable response, no flicker, and sensible fallback on sensor loss.

Complete and document one phase before expanding. Do not require optional devices to run earlier phases.

## 6. State model and time mapping

Use the Pi's configured local timezone; verify its clock/timezone rather than assuming the workstation's timezone. Never change the system clock to demonstrate transitions.

| Period | Local time, start inclusive / end exclusive | Initial message | Proposed visual / sound |
|---|---|---|---|
| MORNING | 05:00–11:00 | A new day begins | Sunrise / light sparse tones |
| DAY | 11:00–17:00 | Day in progress | Sun / active soundscape |
| EVENING | 17:00–21:00 | Day winding down | Sunset / slower soundscape |
| NIGHT | 21:00–05:00, across midnight | Time to rest | Moon / minimal sound or silence |

One authoritative state feeds every output:
- `mode`: `LIVE` or `PREVIEW`.
- `actual_now`: current local date/time, refreshed independently of preview.
- `represented_minute`: minute of day in `[0, 1439]`; live derives from `actual_now`, preview uses the encoder-selected value.
- `period`: derived only from `represented_minute` using the table above.
- `day_progress`: `represented_minute / 1440.0`, approximately 0 at midnight and approaching 1 before midnight.
- `exact_time_visible_until`: optional monotonic deadline for a temporary numerical overlay.
- `ambient_level` and device availability flags: optional inputs/status, not alternate time sources.

Proposed interaction defaults, adjustable after testing:
- Boot into LIVE. First encoder turn enters PREVIEW relative to current time.
- Each detent moves 15 minutes; wrap modulo 1440. Show a clear PREVIEW label.
- Encoder press returns to LIVE and reveals actual time for 3 seconds. No automatic preview timeout initially.
- An optional confirmation chime must not obscure or repeatedly restart period audio.
- Ambient light changes output intensity only; it must not redefine the time period.
- For demonstrations, inject a simulated time through a test option; mark it clearly and disable it for normal operation.

Iteration 1 may check every 30 seconds, giving up to 30 seconds of transition delay. When adding input, use a responsive event/tick loop and monotonic scheduling instead of a blocking 30-second sleep. Re-read wall time for live state so clock corrections are reflected.

## 7. Implementation architecture and files

Flow: local time + input events → state controller → one state snapshot → display, audio, servo. Ambient readings modify output settings. Only the controller owns state transitions; drivers must not independently decide what time is represented.

Preserve the working script and make the smallest first change. Extract modules as later phases need them, rather than creating an entire framework before the screen prototype works.

| File / folder | Responsibility / status |
|---|---|
| `PROJECT_DESIGN.md` | This specification, decisions, checklist, handoff |
| `screen_clock.py` | Existing entry point; initially contains minimal period display change |
| `clock_state.py` | Proposed pure period mapping and LIVE/PREVIEW state logic |
| `display_output.py` | Proposed rendering adapter using proven TFT setup |
| `audio_output.py` | Proposed local playback, transition handling, graceful disconnect behavior |
| `encoder_input.py` | Proposed encoder/button events and debounce |
| `servo_output.py` | Proposed calibrated/clamped position output and movement limiting |
| `ambient_input.py` | Proposed optional sensor readings, smoothing, fallback |
| `config.py` | Proposed centralized periods, input step, volume, device settings; no secrets |
| `assets/audio/`, `assets/images/` | Proposed licensed/attributed local assets |
| `tests/test_clock_state.py` | Proposed hardware-free mapping and transition tests |
| `README.md` | Existing or proposed setup, demo evidence, usage, AI disclosure |
| `requirements.txt` | Add/update only after inspecting actual environment and required packages |

Reuse installed working libraries; verify versions before adding dependencies. Audio transitions should stop/fade the previous track and start the next only when needed. Rapid scrubbing must not spawn overlapping players. Missing optional hardware should report a concise status and allow screen-only operation. On exit, stop audio and release device resources; choose a safe servo shutdown behavior after calibration.

For servo mapping, use `min_angle + day_progress * (max_angle - min_angle)` with verified limits and bounded movement. Midnight wraps from one end toward the other; test the return sweep safely before fitting a pointer. Real sunrise/sunset tracking is not part of this mapping.

## 8. Testing and evidence

- **Baseline:** inspect current code, confirm time display, record environment and service state before edits.
- **Pure logic:** test 04:59/05:00, 10:59/11:00, 16:59/17:00, 20:59/21:00, and 23:59/00:00; every minute belongs to exactly one period.
- **State transitions:** LIVE → PREVIEW, forward/backward wrap, return-to-now using fresh wall time, overlay expiry, and rapid encoder events.
- **Screen:** show all four simulated periods; check clipping, font size, rotation, contrast, and LIVE/PREVIEW distinction on the actual TFT.
- **Audio:** test each asset, single playback ownership, unchanged-period behavior, rapid crossings, missing files, disconnect/reconnect, and conservative volume.
- **Servo:** test without mechanical load first; verify limits, gradual updates, scrub response, and midnight rollover.
- **Ambient:** test bright/dark changes, smoothing, bounded brightness/volume, and sensor failure.
- **Integration:** run through a simulated day, then live time; confirm Ctrl+C cleanup and correct restoration of the screen service.
- **Evidence:** record commands/test inputs, expected vs actual results, date, and hardware used. Label simulated demonstrations. Do not claim hardware tests from desktop-only checks.

Capture the required short video of the initial modification; keep later feature demonstrations separate and link evidence from the README.

## 9. Git workflow

Work within the existing repository and follow any repository instructions. Before editing, inspect `git status`, current branch, and relevant diffs; preserve user changes. Establish a baseline commit or clearly record an existing baseline without staging unrelated files.

Use a small feature branch such as `piclock/time-period-display` when appropriate. Review diffs, run phase-relevant checks, and stage explicit files. Commit one coherent step at a time, e.g. `Add time-of-day display states`. Update this document with the implementation and test evidence in the same change. Do not force-push, reset others' work, or change remotes. Push according to the project's submission workflow after verifying the remote/branch. Keep credentials, virtual environments, caches, and oversized raw recordings out of Git.

## 10. AI collaboration protocol

1. Read this document, repository instructions, current code, and working-tree status. Treat the prior chat as historical evidence, not authoritative executable instructions.
2. Claim one bounded task in the table below with agent identity, files, and timestamp. Coordinate ownership before concurrent edits; a Markdown claim is not a lock.
3. State assumptions and preserve the working display initialization. Implement only the active phase unless the user changes scope.
4. Keep shared state semantics consistent across modules. Record changes to mappings or controls under Decisions before downstream work depends on them.
5. Run relevant checks; distinguish implemented, desktop-tested, and hardware-tested status.
6. Update the checklist, claims, test evidence, known issues, and handoff notes. Leave a specific next action and any unresolved blocker.
7. Review others' changes before merging; never overwrite unrelated edits or mark unverified work complete.

### TODO / progress

- [x] User reported working numerical time display.
- [x] Shared design document created locally.
- [x] Place/verify this document in the Pi's Lab 2 directory.
- [x] Inspect repository instructions, current script, branch, and dependencies.
- [x] Verify Pi local time/timezone and retain baseline evidence.
- [x] Implement/test phase 1: actual-time period display (automated tests and hardware writes passed; physical visual acceptance pending).
- [ ] Record initial demonstration and update README.
- [ ] Verify Bluetooth output and implement/test phase 2 audio.
- [ ] Record wiring and implement/test phase 3 encoder scrub.
- [ ] Calibrate and implement/test phase 4 servo.
- [ ] Decide whether to implement phase 5 ambient adaptation.
- [ ] Save separate storyboards and Verplank diagrams for both concepts.
- [ ] Verify assignment requirements, asset credits, AI disclosure, and final Git submission.

### Task claims

| Task | Owner | Files | Status / timestamp |
|---|---|---|---|
| Shared design document | Codex | `PROJECT_DESIGN.md` | Updated locally and copied to Pi, 2026-09-19 |
| Phase 1 period display | Codex | `screen_clock.py`, `test_screen_clock.py`, `PROJECT_DESIGN.md` | Implemented and automated checks passed, 2026-09-19 13:12 EDT; physical visual review pending |

### Decisions

- 2026-09-19: start with actual-time period labels on the working TFT; additional hardware follows incrementally.
- Preferred trajectory: Soundscape Clock; retain Daylight / Energy Clock as a separate design concept.
- Four fixed periods above are implemented phase 1 boundaries; they do not represent astronomical sunrise/sunset.
- 2026-09-19: preserve one-second refresh and numerical time alongside period/message; normal execution is LIVE. `--test-time HH:MM` fixes represented time and visibly labels it SIMULATED. No clock/timezone changes or new dependencies.
- Encoder defaults, audio selections, servo limits, and ambient settings remain proposals pending implementation/testing.

### Known issues / open questions

- Remote-SSH server prerequisites failed; SSH/nano remain the known working user workflow. Diagnose separately from clock development.
- Exact TFT variant, available pins, encoder switch, sensor variants, pHAT compatibility, and wiring are unverified.
- Bluetooth playback connection/backend and microphone availability are unverified. Microphone interaction is optional and not required.
- Sound assets, playback policy (loop versus brief cue), quiet behavior, and comfortable volume need selection during phase 2.
- Existing design images have not been copied into the repository; find/export and label each concept separately.
- Phase 1 remote inspection, deployment, and display-write smoke tests are complete; actual TFT appearance and video evidence remain unverified.

### Notes / handoff log

**2026-09-19 — Codex:** Drafted this document using the user's requested scope and retrieved prior conversation, including the user-confirmed baseline and descriptions of both concepts. No application code or wiring changed. Saved a local deliverable because Pi access was not established. Next agent: place this file in Lab 2, inspect the real script and repository instructions, then implement phase 1 only.

Future entry template: `Date | Agent/person | Task and changed files | Checks/evidence | Decisions/blockers | Next action`.

**2026-09-19 13:12 EDT — Codex, phase 1:** Inspected the Pi repository on branch `Fall2026`, baseline HEAD `597248e1a2e2b873e96b52a71ca655e9e14bf938`. No applicable AGENTS.md was found. Existing uncommitted numerical-clock edits were preserved in the implementation and backed up verbatim at `/home/pi/piclock-backups/20260919-131109/screen_clock.py`. No commit or push was made. Pi timezone is `US/Eastern` (EDT, UTC−04:00); system clock synchronized and NTP active. Installed Pillow is 11.3.0; existing board/digitalio/display imports succeeded in `~/venv`. No dependencies changed.

Implementation: `screen_clock.py` now exposes pure period mapping and Pillow rendering functions, with hardware initialization inside `main()` so tests can import it without acquiring GPIO. Retained CS D5, DC D25, no reset pin, 64 MHz baudrate, hardware SPI, ST7789 135×240 with offsets 53/40, landscape canvas 240×135, rotation 90, DejaVuSans 18, and backlight D22. The screen shows LIVE, the period, its specified message, and HH:MM:SS. Each one-second frame reads local wall time again. `--test-time HH:MM` provides a visibly SIMULATED frame; `--frames N` bounds a test run. Normal exit and Ctrl+C release GPIO/SPI resources.

Evidence:
- `~/venv/bin/python -m unittest -v test_screen_clock`: 4 tests passed on the Pi. Covered 04:59:59/05:00:00, 10:59:59/11:00:00, 16:59:59/17:00:00, 20:59:59/21:00:00, and 23:59:59/00:00:00; expected labels matched.
- Exhaustive 1,440-minute check passed: MORNING 360, DAY 360, EVENING 240, NIGHT 480 minutes; transitions occur only at minutes 300, 660, 1020, 1260. Out-of-range minutes rejected.
- Pillow text bounding boxes for every period in LIVE and SIMULATED fit the preserved canvas; exact-time labels checked. Compilation passed.
- Hardware smoke: stopped `piscreen.service`, ran two frames each at simulated 05:00, 11:00, 17:00, 21:00, then two LIVE frames; all five processes exited successfully with actual display writes. Service was active before testing and restored to active afterward. This verifies execution, not human observation of TFT orientation/contrast.

Run and inspect on the Pi (stop any other custom display process first):
```bash
cd ~/Interactive-Lab-Hub/"Lab 2"
sudo systemctl stop piscreen.service
~/venv/bin/python screen_clock.py
# Ctrl+C, then restore the original screen service:
sudo systemctl start piscreen.service
```
For a labeled demonstration, use `~/venv/bin/python screen_clock.py --test-time 17:00 --frames 5` while the service is stopped. Tests never change the system clock. Next action: inspect all four periods on the actual TFT and record the phase 1 video before beginning phase 2 audio.

AI contribution addition: Codex implemented the phase 1 mapping, rendering, simulated-time option, automated tests, and deployment over SSH; preserved and backed up the user's baseline; verified clock configuration and display execution; and updated this handoff. The student still needs to review the visible output and record demonstration evidence.

## 11. Required AI contribution disclosure

Keep an honest record of AI help in the project README/report: tool/model if known, what it drafted or changed, what the student reviewed/modified, and what was actually tested. Credit generated diagrams/media and third-party assets. Follow the course's exact disclosure format when available.

Initial disclosure text to adapt: “Codex assisted in organizing the PiClock design specification and development plan from my project requirements and earlier design discussion. Earlier ChatGPT assistance contributed design ideas and suggested display code. I am responsible for reviewing the design, verifying the implementation on the Raspberry Pi, and documenting tests. At the time this specification was created, Codex had not modified or tested the Pi application.” Add subsequent contributions and validation as work progresses; do not present AI-generated work as independently authored.


2026-09-20 | Codex | Phase 2 USB audio implementation claimed: screen_clock.py, audio_output.py, generate_audio.py, tests, assets and documentation. User authorized the next-step plan; physical phase 1 review/video remain pending. USB replaces planned Bluetooth after user-confirmed audible playback.


## Phase 2 implementation checkpoint ? 2026-09-20

- User authorized implementation of the next-step plan despite pending phase 1 physical review/video. USB speaker playback was confirmed by the student; Bluetooth is no longer needed for this milestone.
- Added optional --audio to screen_clock.py, audio_output.py, generate_audio.py, test_audio_output.py, and three original eight-second WAVs with attribution in assets/audio/README.md. Existing screen-only behavior and hardware initialization remain unchanged.
- One ffplay process owns playback, explicitly routed to the verified Jieli USB sink through SDL PulseAudio. Unchanged periods keep the player; transitions stop it first; NIGHT is silent. Missing sink/assets/tools or failed playback are retried every five seconds; sink queries time out after 0.5 seconds. System volume and startup configuration are unchanged.
- Student found initial loops too quiet. Generator amplitude increased from 6500 to 20000 (approximately +10 dB) and WAVs rebuilt. Final comfort/readability confirmation remains pending.
- All 10 screen/audio tests passed after the amplitude revision. Real routing checks found a RUNNING USB sink and a routed stream for each period, with unchanged player PID over ten seconds (beyond each eight-second loop). NIGHT stopped playback.
- Actual TFT integration: nine frames each at 05:00, 11:00, 17:00, 21:00 with --audio; two screen-only LIVE frames; all passed. Injecting an unavailable sink still completed seven TFT frames. Ctrl+C exited cleanly and removed the actual ffplay child. Unit tests simulated disconnect/reconnect, missing files/tools, timeout, player failure, rapid transitions, and forced cleanup.
- Physical unplug/reconnect has NOT been tested. Successful TFT writes do NOT establish appearance. Phase 1 and soundscape videos remain pending.
- piscreen.service restored to active; no custom playback intentionally left running. git diff --check passed. No packages installed, commits, pushes, wiring changes, encoder, servo, or ambient features added.
- Pre-audio backup: /home/pi/piclock-backups/20260920-144439-audio.
- Next: confirm revised sound comfort and TFT readability, then physically unplug/reconnect during --audio and verify recovery within about five seconds. Record the initial modification and audio evidence separately. Only after audio acceptance inspect encoder model/pins and implement scrubbing.
- AI contribution: Codex implemented, synthesized, tested and documented this milestone; the student confirmed USB audibility and requested louder loops.


### Physical audio acceptance ? 2026-09-20

Student confirmed the revised louder tones are comfortable. During the physical
USB reconnect test, monitoring detected removal at 28.4 seconds, reappearance at
42.6 seconds, and a RUNNING USB sink with routed playback at 43.6 seconds (about
one second after detection). The clock process remained running throughout.
Student confirmed sound returned and the screen stayed visible. Test playback
was stopped and the originally active piscreen.service restored afterward.
This supersedes earlier pending volume and physical reconnect notes. Complete
four-period visual review and demonstration recordings remain pending; next
hardware milestone is encoder identification and pin/wiring inspection.
