# Live checks and participant evidence

Submission update (2026-10-04): Part 1E feedback and participant feedback are now documented in the [lab report](../README.md), which also links Pablo's prototype demo and detector recording. Participants said the prototype worked well but response latency was too high. No separate participant timing dataset was collected. The procedure and earlier checkpoint below are retained as planning history, not a statement that the report is still awaiting that feedback.

Status (2026-10-04): Pablo confirmed a combined physical-button, exact recognized
question, real one-person detection, manually approved spoken reply, and readable
state-display trial. Two presses during THINKING left the same turn active;
completion returned to IDLE without another turn. A three-second hold was not
verified and further button checks were stopped at Pablo's request. Successful
recordings, Part 1E feedback, and the two-person evaluation remain pending.

## Hardware acceptance, one step at a time

Confirm readiness before each step. Use the spoken cue before asking for action.
Run one audio session. Keep the existing screen service for button-only checks.

1. Stand in webcam view. Press/release once; after "I'm listening," ask
   "Is anyone at the entrance?" Wizard reviews transcript and fresh real count,
   edits if necessary, and approves. Confirm clear cue/reply and correct scene.
2. Hold the button through one turn. Confirm exactly one turn; release before
   starting another. Press during thinking/speaking; confirm no additional turn.
3. Repeat with an empty camera scene. Answer from a received fresh zero count,
   never from absent messages. Compare Frigate evidence with actual scene.
4. Run the display launcher. Observe Idle, Listening, Thinking, Speaking and
   return to Idle. Do not speak after a cue once to check capture timeout recovery.
   Check controller error/status rather than treating silence as success.
5. Stop the display launcher and confirm piscreen.service is restored.

Camera-data loss and busy/stale approvals also have automated tests. Deliberate
live camera shutdown is unnecessary for the first participant interaction.

## Part 1E and participant sessions

Arrange the pending partner acting-out exercise; note questions, pauses, missed
expectations, and recovery requests. Revise dialogue/storyboard only from actual
feedback. Preserve Pablo's original illustrations and describe revisions clearly.

Then invite at least two other people. Obtain agreement before recording and
explain the wizard role during debrief. Let them ask naturally rather than only
reciting the successful test question. Use these tasks as starting points:

- Ask whether anyone is currently in the camera view.
- Ask when a person was last detected or about recent activity.
- Try an identity or unsupported question and observe the explanation.

For each participant, record an anonymous ID, actual request, recognized words,
reply, actual scene, corrections, perceived delay, and their own feedback.
Do not put private identifying information or raw audio into the repository.
Record software processing/wizard timing separately from any phone-measured
end-of-speech-to-audible-reply delay. Neither is general performance evidence.

## Recording the device and controller

Next recording setup: keep the assistant in display mode. Position the phone so
the screen and green button are visible, and arrange the participant within the
webcam's view. The participant stays in that view through the entire reply. Give
the wizard access to the controller before starting the phone recording. Do not
depend on assistant tool calls during the take; earlier permission prompts
interrupted recording attempts.

For one short take, show IDLE, press/release the green button, wait for the spoken
listening cue, and ask "Is anyone at the entrance?" The wizard reviews the actual
transcript and fresh camera count, approves the appropriate reply, and lets the
device finish and return to IDLE. Record the controller in a separate take or
screen capture with its token concealed. This is a proposed recording sequence;
no saved video has been verified.

Finish setup and all permission prompts before recording. Use a second person
at the wizard controller; the participant presses the physical button and speaks.
Capture the device/cue/reply with the phone and capture the controller separately
with its private token concealed. Keep the real wizard delay visible in the raw
recording; label any trimmed edited version. Verify the saved recordings before
adding their links to the report. Do not restart cancelled demo scripts.

## Results to fill after sessions

For each session, write a short factual account under these prompts:

- What worked and failed for the participant? Include concrete examples.
- What worked and failed for the wizard/controller?
- What did feedback change in the wording, timing, sensor placement, or cues?
- What would an autonomous version need to handle that the wizard handled?

No participant observations or recording outcomes have been filled in yet.
