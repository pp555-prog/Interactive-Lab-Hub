# Lab 3 agent instructions

## Read first

Read `README.md`, `prep.md`, and `camera-assistant/README.md`. When working in
Pablo's Windows workspace, also read its root `AGENTS.md`, `HANDOFF.md`, and
`PROGRESS.md`; these contain operating receipts and current work coordination.
Check Git status, branch, and revisions before changes. The canonical checkout
is `repo/` on `Fall2026`; archived copies and `.lab3-publish.git` are not current.
Preserve unrelated Lab 2 edits and Pablo's uploaded storyboard/Verplank diagram.

## Project behavior

- The Camera Assistant uses real Frigate person detections over local MQTT,
  Silero VAD, Whisper `tiny.en`, and Piper. The normal workflow requires a human
  wizard to approve every reply through the controller.
- Do not replace manual approval with automatic replies unless Pablo explicitly
  requests that behavior. Label any narrowly preapproved demo separately.
- Never manufacture detections, infer zero from missing MQTT messages, identify
  people, or present event counts as unique-person counts. Treat stale data,
  offline MQTT, disabled detection, and missing counts as unavailable evidence.
- Maintain isolated turns: cue before microphone capture; close the microphone
  before processing/playback; reject duplicate/stale approval and busy triggers.
- Keep controller and Frigate services on loopback; use the token-protected
  controller and authorized SSH access. Do not expose private tokens in docs.

## Hardware and Pi

- Pi checkout: `/home/pi/Interactive-Lab-Hub`; use `Lab 3/.venv`. Recheck actual
  devices, owners, and services after reboot; old PIDs and audio indices expire.
- The green SparkFun button is BOB-16842, verified at I2C address `0x6f`.
  Its Qwiic cable connects to the Adafruit Mini PiTFT 1.14-inch (4393) socket.
  Give plain, one-step wiring instructions; do not assume familiarity with names.
- Confirm hardware-test readiness, provide an audible cue, and collect Pablo's
  actual observations. Only one agent/process may conduct Pi audio trials.
- `piscreen.service` owns the display. Temporarily stop it only for the approved
  display phase; restore it when that phase ends. Keep it active for button-only
  trials. Existing TFT wiring is documented in the workspace handoff.
- Match native USB audio rates through the existing resampling code; never assume
  the microphone accepts 16 kHz or the speaker accepts Piper's generated rate.
- Runtime corruption recurred after a power cycle. Check package integrity and
  camera/audio readiness before trials. Do not claim a repair persists across
  reboot without checking, or claim the storage device is faulty without evidence.
- SSH/network permissions still apply. A persistent connection does not guarantee
  prompt-free tool execution. Prepare any phone-recorded take before recording;
  do not promise uninterrupted operation that the tools cannot guarantee.

## Checks and deployment

Run from `camera-assistant/` in the Lab 3 environment:

```bash
../.venv/bin/python -m unittest test_assistant.py test_resampling.py test_launcher.py
../.venv/bin/python -m pip check
```

The MQTT integration test is synthetic and opt-in; run it with the project broker
and Frigate stopped, never alongside live detections. Config validation, model
loading, unit tests, and synthetic messages do not establish live hardware success.
The Compose image now builds from the pinned official ARM64 base with one headless
OpenCV package; inspect `Dockerfile` and `.dockerignore` before building.

Compare local/Pi/remote state before synchronization. Transfer only intended files
and preserve private runtime configuration. Never force-push, reset, or overwrite
unknown edits. Stage explicit files and review diffs; do not use `git add .`.

## Privacy, evidence, and handoff

- Keep the real phone number, its raw transcript, and audio private on the Pi.
  Exclude credentials, runtime logs, recordings, models, and virtual environments.
  Enable optional recording/turn logs only with participant agreement.
- Use UTF-8 explicitly for text processing. Preserve LF for deployed shell scripts.
- Label measured results, user feedback, hypotheses, and untested behavior
  separately. Preserve accurate AI disclosure. Cancelled/unconfirmed phone demos
  are not successful recordings or participant studies.
- Lab 2 is closed. Follow Pablo's current scope; do not start additional assignment
  parts or participant experiments just because they appear next in the report.
- In the shared workspace, claim work in PROGRESS before edits; clear the claim
  when done. Update PROGRESS and HANDOFF after meaningful work with checks,
  commit/push state, remaining work, and the next action. Use separate worktrees
  for simultaneous repository edits and coordinate overlapping files.
