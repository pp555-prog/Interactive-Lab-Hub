# PiClock progress and handoff

Updated: 2026-09-19 by Codex.

## Current status

Phases 1 and 2 are implemented on the Raspberry Pi (see latest checkpoint below): the screen shows LIVE, the current time-of-day period, a short message, and exact local time. Automated logic/render checks and actual display-write smoke tests passed. Physical appearance on the TFT and the required demonstration video remain pending.

Read `PROJECT_DESIGN.md` for the full specification before making changes. Continue one phase at a time; phase 2 USB audio is implemented; physical acceptance remains pending.

## Locations and access

- SSH: `pi@pablo98pi`; password-free `BatchMode=yes` access from this Windows computer verified.
- Reused the existing Windows `~/.ssh/id_ed25519` key pair without changing it.
- Pi project: `/home/pi/Interactive-Lab-Hub/Lab 2`.
- Python: `/home/pi/venv/bin/python`.
- Pi timezone: `US/Eastern`; EDT (UTC-04:00) at verification. System clock synchronized; NTP active.
- This handoff and `PROJECT_DESIGN.md` are saved in the Windows workspace and the Pi project folder. Application code and tests are on the Pi.

## Implemented

| Period | Local time (start inclusive, end exclusive) | Message |
|---|---|---|
| MORNING | 05:00–11:00 | A new day begins |
| DAY | 11:00–17:00 | Day in progress |
| EVENING | 17:00–21:00 | Day winding down |
| NIGHT | 21:00–05:00 | Time to rest |

`screen_clock.py` now contains pure period mapping and Pillow rendering functions. Hardware initialization is inside `main()` so tests can import the module without acquiring GPIO. Live frames reread local wall time every second. `--test-time HH:MM` fixes the displayed time with a visible SIMULATED label; `--frames N` limits a run. Normal exit and Ctrl+C release GPIO/SPI resources.

Display initialization was compared with the original and matches apart from indentation/whitespace: CS D5, DC D25, no reset pin, 64 MHz SPI, ST7789 135×240, offsets 53/40, 240×135 landscape canvas, rotation 90, DejaVuSans 18, and backlight D22. No dependencies, wiring, timezone, or system clock were changed.

## Baseline and Git state

- Repository branch: `Fall2026`.
- Baseline HEAD: `597248e1a2e2b873e96b52a71ca655e9e14bf938`.
- The user's numerical-clock changes were already uncommitted; they were preserved and extended.
- Original script backup: `/home/pi/piclock-backups/20260919-131109/screen_clock.py`.
- No applicable `AGENTS.md` was found during inspection.
- No commit or push was made.
- Expected pending files: modified `screen_clock.py`; new `test_screen_clock.py`, `PROJECT_DESIGN.md`, and `PROGRESS.md` in Lab 2. Inspect current Git status before staging; do not overwrite unrelated work.

## Verification completed

- `~/venv/bin/python -m unittest -v test_screen_clock`: all 4 tests passed on the Pi.
- Boundary checks passed immediately before/at 05:00, 11:00, 17:00, 21:00, and midnight.
- All 1,440 minutes checked: MORNING 360, DAY 360, EVENING 240, NIGHT 480; transitions only at the specified boundaries.
- Invalid out-of-range minutes rejected.
- All period messages and LIVE/SIMULATED labels fit the 240×135 canvas using the installed font; exact-time text checked.
- Python compilation and final `git diff --check` passed.
- Hardware smoke runs wrote two frames each at simulated 05:00, 11:00, 17:00, 21:00, then two LIVE frames. All five runs exited successfully.
- `piscreen.service` was active before testing, stopped during custom display runs, and restored afterward. It was active again when this handoff was created. The custom clock is not configured to run automatically.
- Local and Pi copies of `PROJECT_DESIGN.md` were verified identical by SHA-256.

Successful hardware writes do not establish human-visible orientation, contrast, or appearance. Those still need inspection on the actual TFT.

## Commands for the next session

Verify access from Windows PowerShell:

```powershell
& "$env:WINDIR\System32\OpenSSH\ssh.exe" -o BatchMode=yes pi@pablo98pi "date -Is"
```

On the Pi, run tests without taking ownership of the display:

```bash
cd ~/Interactive-Lab-Hub/"Lab 2"
~/venv/bin/python -m unittest -v test_screen_clock
```

Run the live clock after ensuring no other custom display process is running:

```bash
cd ~/Interactive-Lab-Hub/"Lab 2"
sudo systemctl stop piscreen.service
~/venv/bin/python screen_clock.py
# Press Ctrl+C, then restore the service:
sudo systemctl start piscreen.service
```

For a short simulated demonstration while the service is stopped:

```bash
~/venv/bin/python screen_clock.py --test-time 17:00 --frames 5
```

Use 05:00, 11:00, 17:00, and 21:00 to inspect all four periods. Never change the system clock to demonstrate a transition. Record service state before tests and restore it afterward; do not run competing display processes.

## Next actions

1. Inspect all four simulated periods and LIVE mode on the physical TFT for readability, clipping, rotation, and contrast.
2. Record the phase 1 demonstration video and link it from the README; update AI contribution disclosure there using the details in `PROJECT_DESIGN.md`.
3. Review the pending diff and tests before any requested commit/submission.
4. Begin phase 2 only after phase 1 visual acceptance: verify Bluetooth output, choose local audio assets and playback policy, and implement transition-based audio with graceful speaker-loss handling.

Encoder scrubbing, servo motion, and ambient adaptation remain unimplemented. Do not add those while completing phase 1 evidence.

## AI contribution

Codex inspected and backed up the baseline, implemented phase 1, authored and ran automated tests, performed remote hardware display-write checks, and updated the design and handoff documents. The user performed the password-authenticated public-key installation step. Student review, visible TFT acceptance, and video evidence are still pending.


## Continuation checkpoint — 2026-09-20

- Reconnected over SSH; branch Fall2026 and pending phase 1 changes match the handoff.
- All four test_screen_clock tests passed again; git diff --check passed before documentation edits.
- piscreen.service remained active; no custom screen_clock process was running.
- README now contains phase 1 review/recording commands, honest pending evidence markers,
  the agreed audio milestone, and AI disclosure. No video has been recorded by Codex.
- User selected looping generated tones for morning/day/evening and silence at night.
- Audio tools are installed, but only auto_null is available; no known Bluetooth devices were listed.
- Await physical TFT review and initial video. Then pair/verify the intended speaker
  and implement phase 2. No audio code, dependencies, wiring, commits, or pushes changed.


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
