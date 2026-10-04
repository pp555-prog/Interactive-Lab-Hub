# Camera Assistant — Frigate + Wizard-of-Oz

## Submission status - 2026-10-04

The combined button, voice, real camera-count, wizard-approved reply, and enlarged state display trial passed with Pablo's confirmation. Two busy presses did not start duplicate turns. Pablo recorded a prototype demo and saved the detector clip; the video folder and participant feedback are in the [lab report](../README.md). Participants reported that the system worked well but latency was too high. Faster hardware and automated approval are proposed improvements, not tested results. The dated setup and trial receipts below preserve the development history; pending items in older receipts describe their status at that time.

Implementation status (2026-10-03): deployed as an uncommitted new directory on the Pi.
Eleven automated behavior/controller tests and one synthetic MQTT integration test passed.
Official Frigate 0.16.4 ARM64 is pinned by digest; configuration validation and
OpenCV import passed on the Pi. Frigate and MQTT are running. The entrance feed
returned a JPEG and measured 4.6 camera FPS with detection disabled. Subsequent
approved person entry/exit and one-person spoken-answer trials passed with
Pablo's confirmation. Detection is now enabled in the Pi's private config.
The mini USB microphone cue/capture/playback test passed, and Pablo confirmed
clear playback at comfortable volume. The green Qwiic button responds at 0x6f;
one physical press/release check passed after an audible cue. A button-started
capture/ASR/manual-approval/playback turn completed on 2026-10-04; Pablo confirmed
both audio cues/reply and the listening LED. An informative fresh-count button
answer and display integration remain pending.
Part 1E feedback, live hardware validation, combined-load measurements, and participant
studies must be collected before claiming a completed Part 2 study.

## Architecture

Webcam → go2rtc → Frigate person detection → local Mosquitto → session event cache.
Green Qwiic button → spoken cue → dedicated USB microphone → Silero VAD → tiny.en
→ wizard approval → Piper → USB speaker. The PiTFT shows interaction states.

The human wizard approves or edits every reply. Detection comes from Frigate, not
from wizard-invented observations. This is not autonomous conversation or identity recognition.

## Pi preparation

Use the existing `Lab 3/.venv`. From `Lab 3/camera-assistant`:

```bash
../.venv/bin/pip install -r requirements.txt
# Only when physical button/display adapters are needed:
../.venv/bin/pip install -r requirements-hardware.txt
sudo apt-get install docker.io docker-compose
mkdir -p runtime/frigate
# First deployment only; preserve an existing runtime config:
test -e runtime/frigate/config.yml || cp frigate.example.yml runtime/frigate/config.yml
sudo docker-compose -f compose.yml config
sudo docker-compose -f compose.yml pull mqtt
sudo docker-compose -f compose.yml build frigate
```

The Compose project binds MQTT and Frigate to loopback. No credentials are needed
on this isolated broker. The example uses a CPU detector for a measured one-camera
trial, not a performance guarantee. The image's exact resolved digest should be
recorded after pulling. Runtime database/config and container logs stay on the Pi.
Video recording and saved snapshots are disabled.

Startup troubleshooting: the initially pulled stable image (`b93eb4c…`)
failed OpenCV import and had two runtime-library checksum mismatches inside
the container. An isolated rebuild also crashed. The official 0.16.4 image
(`9594684d…`, pinned in Compose) passed import and runtime-library checks and
started successfully. After a subsequent power cycle, host ldconfig corruption
and OpenCV import failure recurred. Restoring the exact checksum-verified libc-bin
version restored audio discovery; a container built from the pinned 0.16.4 base
with only opencv-contrib-python-headless 4.11.0.86 restored video. Compose now uses
that build. Thirteen assistant/resampling tests passed. Cause and durability across
another reboot are unproven; recheck integrity/readiness before subsequent trials.

Initial button startup used verified audio input 1/output 2 and address 0x6f.
Current shared-playback routing and completed button turn are described below.
`piscreen.service` remains active; display handover is pending.

2026-10-04 update: a further reboot produced a checksum mismatch in one bundled
OpenBLAS library. Exact-wheel replacement in the running container passed sync
and cache-evicted checksum read-back; camera frames returned. That repair is in
the container writable layer, not the image; recreation/durability remains a limit.
Unknown detection state now bootstraps from actual Frigate statistics after a
restart. The launcher uses shared `pulse` playback after verifying that its
default sink is the USB speaker, avoiding conflict with `pw-play` test cues.
Use `../.venv/bin/python run_pi.py` for normal button mode; `--display` temporarily
hands over the screen and restores its previous service on launcher exit.
The latest button question was recognized exactly and its manual waiting-count
reply played; no fresh count was invented. Pablo confirmed both audio and LED.
Run `../.venv/bin/python -m unittest test_assistant.py test_resampling.py test_launcher.py`
for the current 18-test set. Display/hardware observations are separate evidence.

Check `v4l2-ctl --list-devices` and `--list-formats-ext`; update the mapped device
if `/dev/video0` changes. The detected webcam supports 640×480. Bring up the feed
with detection disabled, inspect it, then change `detect.enabled` to `true` in the
private config and restart Frigate for the detection trial:

```bash
sudo docker-compose -f compose.yml up -d
sudo docker-compose -f compose.yml logs --tail=50 frigate
```

Do not start an observed camera/audio trial until Pablo is ready. To stop this
project without deleting runtime data: `sudo docker-compose -f compose.yml stop`.

## Controller and voice

```bash
# Software-only controller check (no capture or playback):
../.venv/bin/python app.py --simulate
# List devices; choose dedicated microphone and USB speaker by their indices:
../.venv/bin/python -c 'import sounddevice as sd; print(sd.query_devices())'
# Actual voice mode, after confirming those indices:
../.venv/bin/python app.py --input-device INPUT_INDEX --output-device OUTPUT_INDEX
```

The wizard URL is `http://127.0.0.1:5050/controller`. Enter the private token printed
at startup. Access it from the laptop through an SSH tunnel:

```bash
ssh -L 5050:127.0.0.1:5050 pi@100.110.200.223
```

The participant status page `/` reveals neither transcript nor wizard controls.
Controller data, camera requests, activation, and approval require the token header.
Tokens and optional logs must not be committed. Use localhost/tunneling by default.

USB audio rate handling: capture uses 16 kHz when supported, otherwise the
microphone's native rate is resampled to 16 kHz. Piper audio is resampled to the
speaker's native rate. The tested mini USB microphone accepts 44.1/48 kHz and
the USB speaker accepts 48 kHz. The first direct-rate turn failed before its cue;
after this fix, a real voice turn recognized “Is anyone at the entrance?” exactly
and completed approved playback. Pablo confirmed that both the cue and reply were clear.
That new connection had no person-count message yet, so the reply correctly said
it was waiting for the current count. A subsequent real count update enabled a
one-person spoken reply; Pablo confirmed it was clear and correct. Do not infer
zero from no messages. This verifies one live integrated trial. Wizard/tool delay
was approximately 35 seconds; button/display and broader evaluation remain pending.

Phone-demo attempts were interrupted by tool approval prompts. One attempt
reported zero detections while Pablo reported being in view; it timed out before
reply approval. A later retry also timed out. A temporary single-run helper was
then launched with narrow preapproved replies for the exact entrance question
and real live counts. That helper differs from manual approval on each turn;
its outcome and a successful phone recording were not confirmed. Pablo cancelled
the demo work. Do not present these takes as successful demonstrations or studies.

Select a suggested reply or edit it, then press **Approve and speak**. Approval is
bound to the current turn ID, so duplicate/stale approvals cannot play a later turn.
If the wizard does not approve within 60 seconds, the interaction returns to idle.
The microphone is closed during processing and playback. Capture is limited to
30 seconds and times out after ten seconds if speech never starts.

## Button and display

Inspect wiring and address before enabling `--button-address 0x6f`; this is the
library default, not confirmation of the physical green button's address.
Use a verified Qwiic/I2C connection (3.3 V, SDA GPIO2, SCL GPIO3, ground). Never connect
the button as an ordinary GPIO switch or apply 5 V to its I2C lines.
The breadboard is optional; a verified Qwiic connection does not require it.

The existing `piscreen.service` owns the TFT. Coordinate a temporary handover before
using `--display`, then restore the service after the session:

```bash
sudo systemctl stop piscreen.service
../.venv/bin/python app.py --input-device INPUT_INDEX --output-device OUTPUT_INDEX --button-address 0x6f --display
# After exiting the assistant:
sudo systemctl start piscreen.service
```

The TFT adapter uses the documented ST7789 pins D5/D25/D22, 135×240 with offsets
53/40 and rotation 90. The green LED lights only while LISTENING. Hardware adapters
are opt-in; missing hardware must not be represented as successfully tested.

## Evidence and limitations

`frigate/events` updates are deduplicated by ID; `frigate/entrance/person` supplies
current count. `frigate/stats` confirms frames are arriving. A stale heartbeat,
zero camera FPS, broker loss, or offline Frigate prevents current-state claims.
Detection must report ON before any camera answer is suggested. Stationary persons
are included in the person count. Events are counts of tracks,
not unique identities. Earlier history is not imported at startup. Connection gaps
are disclosed, and current counts reset after an availability change.

Private JSONL logging is opt-in with `--log logs/session.jsonl`, after participant
agreement. It stores transcripts/replies/timing, not audio or camera frames.
`endpoint_to_play_request_s` includes ASR, wizard decision, and TTS work after VAD
endpointing. The VAD-based speech-end estimate and playback-request timestamp are
not measured last-word-to-audible-speaker latency. Measure that separately using
an agreed external recording; do not relabel these estimates as acoustic measurements.

Run automated checks with `../.venv/bin/python -m unittest -v test_assistant.py`.
The simulation mode never fabricates MQTT detections and is not a participant test.
`check_runtime.py` loads cached models and checks silent VAD input and speech generation
without recording or playback. `test_mqtt.py` is an opt-in synthetic broker test;
run it only with this project's broker running and Frigate stopped.

The Pi's corrupted `/sbin/ldconfig` was restored from its exact installed libc-bin
package version, after matching the replacement utility to the installed checksum.
Subsequent libc integrity and package-audit checks were clean. This repair restored
PortAudio discovery; the dedicated USB microphone was not present in the device list.
Optional button/display libraries installed successfully. Cached Whisper/Piper models,
silent VAD input, and TTS generation passed `check_runtime.py`; no microphone capture
or speaker playback occurred during that check. Physical button and TFT adapters
remain untested, and the existing screen service was left running.

### Proposed Part 2 interaction revision

Replace the Part 1D storyboard's Enter action with the green button. Wait for the
spoken cue to finish, then speak while its LED is on and the TFT says LISTENING.
After 1.5 seconds of silence, show THINKING while transcription and wizard approval
run; show SPEAKING during the approved reply, then return to IDLE. This is a proposed
hardware revision, not a redesign based on completed Part 1E feedback.

## Trial checklist

1. Complete recorded Part 1E; retain actual feedback and revise the dialogue.
2. Confirm readiness, check devices individually, and give an audible cue before speech.
3. Compare staged person entry/exit with Frigate events; include an empty scene.
4. Test pauses, recognition errors, unsupported questions, and camera/broker loss.
5. Run a ten-minute combined-load trial; record frame/inference rates, temperatures,
   errors, and actual speech response times. Stop if performance is unusable.
6. Test with at least two participants, recording system and controller with agreement.
7. Document findings about both interfaces, autonomous redesign, and potential datasets.

Sources: [Frigate webcam setup](https://docs.frigate.video/configuration/camera_specific/#usb-cameras-aka-webcams),
[MQTT](https://docs.frigate.video/integrations/mqtt/),
[CPU detector limitations](https://docs.frigate.video/configuration/object_detectors/#cpu-detector-not-recommended),
[SparkFun button library](https://github.com/sparkfun/Qwiic_Button_Py).

Design and engineering: Pablo designed the system, made engineering decisions,
and directed its implementation, hardware integration, and interaction revisions.
AI assistance: Codex assisted with code implementation, deployment, test commands,
wizard-controller operation during Pablo's checks, and documentation under his
direction. Hardware results and participant findings come from actual trials
and Pablo's reported observations.



Screen checkpoint 2026-10-04: Pablo confirmed button audio/LED and screen readiness. Initial display startup failed on missing venv lgpio; launcher automatically restored piscreen.service. Installed lgpio 0.2.2.0 for Python 3.11; pip check and board import passed. Recorded dependency in local/Pi requirements-hardware.txt. Newer adafruit-lgpio required Python 3.13 and was not installed. Guarded retry succeeded: launcher PID 83830, controller IDLE/no error, original screen service inactive for authorized display ownership. Await actual visible Camera Assistant/IDLE confirmation before voice/state trial. No visual/readability result or new audio trial claimed. Restore original service after display phase. No commit/push.

2026-10-04 requested screen revision: Pablo confirmed original title/IDLE visible, then requested only state in larger letters. Removed title; state uses centered bold text, largest size up to 64 px fitting 220x115 safe area. Compared Pi hardware.py against known hash before explicit deployment. Syntax check passed; guarded idle restart succeeded, launcher PID 84171, controller IDLE/no error, screen service inactive for display ownership. Interrupted watch command produced no observed turn (status turn null); no new voice trial claimed. Visual confirmation of revised layout pending. No commit/push; restore original service when display phase ends.

2026-10-04 screen trial confirmed by Pablo: saw LISTENING -> THINKING -> SPEAKING -> IDLE, each state readable, reply clear. This verifies the enlarged state-only display and button/voice feedback for this one waiting-for-count turn; ASR wording was imperfect, and fresh-count informative button answer remains pending. No participant study or successful demo recording claimed. Test phase ended by stopping verified idle launcher 84171; original screen service restoration checked. No commit/push. Next: real fresh-count button answer, then physical hold/busy checks before study/video workflow.

2026-10-04 fresh-count button trial: started button-only launcher PID 92256, original screen service retained. Spoken exit/re-entry cue; actual MQTT count 0 then 1, available camera ~5.1 FPS/detection true. Button turn observed PREPARING/LISTENING/TRANSCRIBING/THINKING. ASR misrecognized intended entrance question as 'Then you want to have the entrance.' (1.827 s), classified unsupported. Human wizard corrected intended trial question and approved factual 'The camera currently detects one person.' based on live count 1. Approval accepted. This is human correction, not successful autonomous question recognition. Actual audible correctness confirmation pending. No recording/participant result/commit/push.

2026-10-04 combined trial attempt: Pablo confirmed prior one-person reply clear/correct but screen lacked states because prior run was button-only. Authorized combined retry enabled display via guarded idle handover, launcher PID 101486, IDLE/no error, original screen service inactive. Movement cue played; new session received actual MQTT count 0, but no positive count within bounded 60-second monitoring window. Helper did not request a voice turn or approve a reply. Assistant remains in display mode for continued combined-test scope; actual screen/presence observation needed. No commit/push.

2026-10-04 combined retry: Pablo said he was in view during prior zero-only attempt. New real MQTT count 0 -> 1; display launcher 101486 retained. Observed PREPARING/LISTENING/TRANSCRIBING/THINKING, exact transcript 'Is anyone at the entrance?', ASR 2.033 s. At wizard-ready time actual available camera ~5.1 FPS had count 0 (last person event 18 s earlier), so manually approved 'No person is currently detected.' rather than reusing earlier positive count. Approval accepted. Actual screen/audio observation and whether Pablo stayed in view require confirmation; potential detection miss remains unresolved. Extra objects API probe returned 404; no conclusions derived from it. No source change/recording/commit/push. Display remains active for ongoing test scope.

2026-10-04 combined turn 2: Pablo clarified he had left view before prior zero-person answer; no detection miss established by that attempt. Authorized repeat retained state display (launcher 101486). Real fresh positive count 1; observed PREPARING/LISTENING/TRANSCRIBING/THINKING, exact 'Is anyone at the entrance?', current intent, ASR 1.356 s. At approval count 1/available camera ~5 FPS/detection true. Manually approved 'The camera currently detects one person.' accepted. Actual simultaneous screen readability/audio correctness and continued physical presence await Pablo. No new source/recording/commit/push. Leave display mode for current combined-test scope; restore original service when scope ends.

2026-10-04 combined acceptance: Pablo confirmed 'yes. perfect' to clear one-person reply and visible LISTENING -> THINKING -> SPEAKING -> IDLE. One combined example passed: physical button -> cue/capture -> exact ASR -> real Frigate count 1 -> manual wizard approval -> spoken answer with readable enlarged state-only screen. Controller confirmed reply_played/IDLE/no error. ASR 1.356 s; wizard 9.917 s; endpoint-to-play-request 11.961 s (software timing, includes human/tool delay). Not a general accuracy or acoustic-latency claim. Assistant left IDLE in display mode under current combined-test scope, launcher last known 101486; original screen service inactive. Restore original service when prototype display scope ends. Next proposed acceptance checks: hold/repeated press while busy; do not start until Pablo ready. Participant study/recording/report publication remain pending. No commit/push.

2026-10-04 saved detector demonstration: Pablo ready; first MP4 encoder attempt failed with FFmpeg filter parsing error and zero-byte output, not successful evidence. Retried direct MJPEG stream copy with actual Frigate bounding boxes/timestamp, spoken movement cue. Saved private Pi recordings/detector-test-20261004-174422.avi; ffprobe 35.000 s, MJPEG 480x360. Actual available MQTT count 0 -> 1 during monitored period; exit back to zero not observed before recording end. Copied this requested clip/count metadata to workspace artifacts/detector-demo (outside repo), converted with Windows FFmpeg to detector-test-20261004-174422.mp4. Visual inspection of frame at 25 s confirms visible person bounding box/label and timestamp. This is a new detector-only test recording, not earlier trials or device/controller recording; no audio track. No publication/commit/push. Await user's playback/movement confirmation. Assistant remains in display mode under recording scope.
