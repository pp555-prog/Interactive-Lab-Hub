# PiClock closeout and handoff

Updated: 2026-09-27 by Codex. **Lab 2 development is closed, as confirmed by Pablo.**
The next active project is Lab 3, Chatterboxes. No Lab 2 feature work is queued.

## Final project record

- Repository: https://github.com/pp555-prog/Interactive-Lab-Hub
- Submission branch: `Fall2026`.
- GitHub HEAD inspected at closeout: `89006eaa35f1420f821deba5891d5b8c59fe9b10`.
- The report includes Raspberry Pi photographs, both design concepts and images,
  peer feedback, source links, and SharePoint video-folder links. The hub already
  links Lab 2 and Lab 3. See [the report](README.md).
- This closeout changes documentation only. The final closeout commit is available
  in Git history, followed by the Pi synchronization documentation update.

## Delivered scope and verification

| Capability | Recorded status |
|---|---|
| LIVE time and four fixed periods on Mini PiTFT | Implemented in the published code |
| Labeled simulated time and bounded frame runs | Implemented; no system-clock changes required |
| Optional USB soundscapes with silent NIGHT | Implemented, using original generated WAV loops |
| Speaker loss/recovery and cleanup | Automated checks plus recorded physical reconnect acceptance |
| Encoder scrubbing, servo pointer, Bluetooth integration | Historical proposals; outside the closed scope |
| Ambient-light adaptation | Pi and Windows experiment; preserved in backups, outside published scope |

Historical checks from 2026-09-19/20: four screen tests and six audio tests passed
on the Pi, including all 1,440 minutes, period boundaries, text bounds, transitions,
failure handling, and cleanup. Actual TFT writes and USB routing were checked.
The student confirmed comfortable revised volume, sound recovery after physical
USB reconnection, and continued screen visibility. These are prior results, not
new hardware tests performed during closeout.

Video links now exist in the report, superseding old capture/link TODOs. The
recordings and sharing permissions were not independently reviewed during closeout;
a complete four-period visual acceptance record was not independently established.
The student's completion statement is recorded without asserting grading or
independently verified satisfaction of every assignment requirement.

## Preserved local differences

The Windows workspace contains `ambient_input.py`, `test_ambient_input.py`, and
a `screen_clock.py` with `--ambient`, unlike the published version. They remain
preserved locally and were not merged into the finished submission. The Pi also
contained this experiment in commit `09d2f43d22f4fde19bc1740c94bbfde0f3158bee`,
now retained on `backup/lab2-ambient-20260927`. Historical
notes describe hardware-free checks and a sensor-absent fallback run, not verified
physical bright/dark behavior. The supplied digital backlight uses on/off output,
so the experiment does not establish continuously variable physical brightness.

## Pi and recovery context

- SSH reverified 2026-09-27: `pi@pablo98pi.local`, IP `100.110.200.223`, using the existing key.
- Pi repository: `/home/pi/Interactive-Lab-Hub`, branch `Fall2026`, synchronized
  to the GitHub closeout; Lab 3 assignment and setup script are present.
- Lab 2 Python: `/home/pi/venv/bin/python`; timezone previously verified as `US/Eastern`.
- `piscreen.service` is active and runs `/home/pi/screen_boot_script.py` outside
  the repository. No custom Lab 2 clock or ffplay process was found.
- Initial hostname failures were followed by restored access. The cause of the
  earlier blank screen was not established; this synchronization did not change
  service configuration or claim to repair it.
- Original Pi branch retained as `archive/lab2-pi-before-closeout-20260927`.
- Backups: `/home/pi/piclock-backups/20260927-closeout/lab2-before-sync.bundle`
  (complete Git history) and `lab2-files.tar.gz` (Lab 2 directory snapshot).
  Both were copied to Windows `Lab 2/Workspace/pi-backups/20260927-closeout/`;
  SHA-256 checksums match. The Git bundle passed verification.
- Original backups remain under `/home/pi/piclock-backups/`, including
  `20260919-131109/screen_clock.py` and `20260920-144439-audio`.

Before any future display use, inspect current process/service state, stop competing
display owners, and restore the prior service state afterward. Lab 3 defines its
own environment; do not assume the Lab 2 virtual environment satisfies it.

## Historical record and next session

Verbatim pre-closeout [progress](archive/2026-09-27/PROGRESS.md),
[design](archive/2026-09-27/PROJECT_DESIGN.md), and
[report](archive/2026-09-27/README.md) are archival snapshots, not active task lists.
The Git bundle and other Windows backups remain intact.

Open the separate Lab 3 workspace and read its README.md and HANDOFF.md.
Start with the current Chatterboxes assignment and prep instructions. Do not
resume Lab 2 encoder, servo, sensor, or recording tasks from historical notes.
