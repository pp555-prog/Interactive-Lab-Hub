# Chatterboxes

**Author:** Pablo Penalba.

I built a speech-enabled Camera Assistant for checking entrance activity using real person detections and human-approved spoken replies.

**AI assistance:** Codex assisted with setup, scripts, implementation, tests, and documentation. I supplied the spoken trials, physical observations, voice preferences, and participant feedback. Details are noted in the relevant sections.

# Part 1

## Setup

I used a Raspberry Pi 5 with USB audio, a Lab 3 Python virtual environment, and the course speech scripts. Piper, Whisper, and Silero models were installed before the trials. I checked microphone capture and speaker playback before testing.

## A. Text to Speech

### My greeting and voice comparison

I chose Piper (`en_US-lessac-medium`) for my [personalized greeting script](speech-scripts/greet_pablo.sh). It says: “Hello, Pablo. Welcome back. What would you like to work on today?” Run `./speech-scripts/greet_pablo.sh` from the Lab 3 directory.

The words were the same, but the greeting felt different depending on the voice. eSpeak sounded robotic, making it feel like a machine was addressing me. Festival sounded more human-like, although still robotic. Piper sounded best to me, so I chose it for my greeting.

I first listened to “Hello, Pablo,” but two words were too short to judge the voices well, so I compared all three with the longer greeting above. See [setup and listening notes](PART1A.md).

## B. Speech to Text

### My speech recognition comparison

I recorded a 10-second clip, `comparison-05.wav`, after finding that five seconds was too short for my sentence. I confirmed that the selected recording captured my sentence and that both transcripts matched what I said:

> Hello, my name is Pablo and today I'm testing speech recognition.

Both runs used the same recording, CPU inference, int8 computation, and beam size 1. Models were downloaded before testing.

| Model | Audio duration | Model load | Transcription time | Real-time factor |
|---|---:|---:|---:|---:|
| tiny.en | 10.00 s | 0.53 s | 1.34 s | 0.13× |
| base.en | 10.00 s | 0.64 s | 2.07 s | 0.21× |

Real-time factor is transcription time divided by recording duration; the table uses the course script's rounded measurements. Model loading is reported separately. These factors include the silence in the 10-second recording and are not measurements of end-to-end conversational response time.

For this sentence, base.en took 0.73 seconds longer without improving the transcript. I would choose tiny.en for this test because it gave the same accuracy with less delay. This single example does not establish that the larger model is never useful. Raw outputs: [tiny.en](results/comparison-05-tiny.txt) and [base.en](results/comparison-05-base.txt).

### Asking for a numerical input

My [numerical-input script](speech-scripts/ask_pets.sh) uses Piper to ask “How many pets do you have?”, waits for playback to finish, records five seconds from the webcam microphone, and transcribes the saved WAV using tiny.en. Run `./speech-scripts/ask_pets.sh` from the Lab 3 directory. Recordings receive unique filenames; `LAB3_MIC_DEVICE` can override the webcam's ALSA device if needed.

I said **“I have one pet.”** The actual transcript was **“I have one tip.”** The number “one” was recognized correctly, but “pet” was substituted with “tip.” The script displays the uncorrected transcript. For this five-second response, model loading took 0.53 seconds and transcription took 0.91 seconds, giving a real-time factor of 0.18×. This test demonstrates a word-recognition error, not a numerical error.

Codex assisted with the scripts, timing runs, and documentation. I supplied the spoken responses and confirmed the transcript accuracy and the recognition error. Audio recordings remain on the Pi; raw comparison timing outputs are included in the repository.

### Larger-number follow-up: phone number

I repeated the numerical-input exercise with a nine-digit phone number. Piper asked “What is your phone number?”, then the Pi recorded for 10 seconds and transcribed with tiny.en. I confirmed that all nine digits were correct. Model loading took 0.54 seconds, transcription took 1.01 seconds, and the real-time factor was 0.10×. The actual digits and audio are private and are not included in this report.

The reusable [phone-number script](speech-scripts/ask_phone.sh) saves a uniquely named recording, waits until the question finishes before recording, and displays the uncorrected transcript. Run `./speech-scripts/ask_phone.sh`. The successful result above came from the equivalent question/record/transcribe command sequence before it was saved as a reusable script. The saved script was syntax-checked; a separate live run has not yet been performed.

## C. Turn-taking: knowing when someone has stopped talking

I tested `listen.py` and `echo_bot.py` with `tiny.en` at silence thresholds of **0.2, 0.7, and 1.5 seconds**. I used “I would like a cup of tea” as a fluent sentence and then repeated it with a brief thinking pause after “I would like.” For the listener tests, I waited approximately three seconds between the two sentences. The pauses were performed naturally, not precisely measured.

### Listening and segmentation

The first 0.2-second attempt had only a text readiness cue, so I was unsure when to speak. I excluded it and repeated the test with an audible “Speak now” cue after the listener was ready. The listener also picked up a fragment of that cue in the 0.2- and 0.7-second runs; those cue fragments are excluded below.

| Silence threshold | Fluent sentence transcript | Paused sentence transcript segments |
|---|---|---|
| 0.2 s | “I would like.” | “I would like.” |
| 0.7 s | “I would like a couple of tea.” | “I would like.” |
| 1.5 s | “I would like a cup of tea.” | “I would like.” followed by “See you.” |

I confirmed that I finished both sentences in every run. In the last run I said “a cup of tea,” not “See you.” The 1.5-second listener captured the fluent sentence correctly, but the paused sentence was still split and its ending misrecognized. These transcripts show incomplete capture and recognition errors; they do not isolate silence detection as the sole cause. Since my pauses were not timed, these are observations from individual trials rather than a controlled benchmark.

### The complete loop: how the reply felt

I then used the echo bot with the same paused phrase at each setting, waiting for its spoken “I'm listening” cue. It replied once per trial using Piper.

| Silence threshold | What the bot repeated | My experience |
|---|---|---|
| 0.2 s | “You said: I would like.” | I felt interrupted. |
| 0.7 s | “You said: I would like.” | I still felt interrupted. |
| 1.5 s | “You said: I would like a cup of tea.” | The wait felt comfortable. A longer pause would feel uncomfortable. |

At 0.2 seconds, the normal thinking pause between “I would like” and my request was treated as the end of my turn, and the bot answered without the rest of the sentence. At 0.7 seconds, I had the same experience. At 1.5 seconds, the echo bot allowed enough time for me to finish and repeated the whole sentence. This run felt patient enough to let me speak without making the wait uncomfortable. My comment about a longer wait is a preference, not a result from testing a threshold above 1.5 seconds.

For this interaction, I preferred **1.5 seconds**. The listener and echo-bot trials did not give identical results at that setting, so it is not a guarantee that every pause will be handled correctly. I would use it as a starting point and retest with the dialogue and users of the final device.

### Processing times

| Echo-bot threshold | Speech recognition | TTS first audio | Reported processing gap |
|---|---:|---:|---:|
| 0.2 s | 0.89 s | 0.26 s | 1.15 s |
| 0.7 s | 0.86 s | 0.22 s | 1.08 s |
| 1.5 s | 1.05 s | 0.37 s | 1.42 s |

The script labels the final column “total gap,” but calculates it as recognition time plus time to generate the first speech audio after it has detected the end of a turn. It excludes the silence threshold and does not directly measure the full delay from my last spoken word to audible playback. I therefore keep these processing times separate from my experience of the overall wait.

**AI assistance:** Codex operated the tests and helped organize the observed transcripts and timings into this report. I performed the spoken trials, confirmed what I said, and supplied the interruption and comfort judgments.

## D. Storyboard

<img width="672" height="413" alt="image" src="https://github.com/user-attachments/assets/86d6cabd-876c-4c03-af6f-05f4a9ab5d06" />
<img width="668" height="391" alt="image" src="https://github.com/user-attachments/assets/4ca8f07e-5d51-4690-8586-884c050fac8b" />

I chose a camera assistant that lets someone ask about entrance activity while working at a desk, without turning around or opening a dashboard. I developed the storyboard around checking recent activity, asking a follow-up question, and recovering when the user asks something the device cannot answer, such as identifying a person.
The interaction starts with pressing Enter and hearing “I’m listening,” so the user knows when to speak. I chose 1.5 seconds of silence as the initial turn-ending threshold because that setting felt comfortable in my Part C echo-bot trial. It still needs testing with this dialogue. The Verplank diagram connects the user’s actions, the spoken and visual feedback, and their understanding of the interaction sequence.

## E. Acting out the dialogue

When we acted out the dialogue, it felt more confusing for the other person than I had imagined because there were no visual cues. Speech alone did not clearly show when the device was listening or thinking, making it harder to tell when to speak and when to wait. This showed me why the interaction needs visible feedback, such as an LED for listening and a screen showing the current state.

---

# Lab 3 Part 2

## Prototype and recordings

The working prototype and wizard controller are in [camera-assistant/](camera-assistant/README.md). On October 4, I confirmed one combined trial: pressing the green button started the listening cue, my entrance question was recognized exactly, Frigate detected one person, and the human wizard approved the correct spoken reply. The small screen showed readable LISTENING, THINKING, SPEAKING, and IDLE states. Two additional button presses during THINKING did not start another turn. A three-second hold was not verified; I chose to stop additional button checks and move on to recording and documentation.

The prototype runs on a Raspberry Pi 5. The webcam and mini USB microphone are its sensors; the green button starts a turn, its LED indicates listening, and a USB speaker and Mini PiTFT provide feedback. Frigate supplies actual person detections through MQTT. Silero detects speech boundaries with a 1.5-second silence threshold, Whisper transcribes the request, and Piper speaks the wizard-approved answer. The screen shows only the state in large centered letters. Missing camera counts produce an explicit waiting response rather than an assumed zero.

In the confirmed combined example, speech recognition took 1.36 seconds. The measured software interval from detected speech endpoint to playback request was 11.96 seconds, including 9.92 seconds waiting for human approval and tool interaction. These are single-trial software timings, not measured acoustic latency. Other trials included recognition errors and a manual correction. A zero-person answer after I left the camera view matched the received count.

Part 1E feedback is documented above. I also saved the detector video and recorded an earlier prototype demo. Participant feedback is summarized below. The hardware checks described here were my own prototype trials, separate from that feedback. See the [recording and evaluation procedure](camera-assistant/EVALUATION.md).

**Recordings:** [Lab 3 videos — prototype demo and detector recording](https://cornellprod-my.sharepoint.com/:f:/r/personal/pp555_cornell_edu/Documents/INFO%205345%20Lab%202%20Videos/Lab%203?d=w6f3a8c3fc42b4b46b473db28230b7c37&csf=1&web=1&e=EchU58).

**AI assistance:** Codex implemented and deployed the prototype, operated the wizard approvals during these checks, and helped document the evidence. I performed the physical trials and confirmed the observed screen states and spoken replies.


## Interaction redesign

The acting-out exercise showed that speech alone made the interaction confusing. The revised prototype replaces the original Enter-key trigger with the physical green button and adds a listening LED and large screen states. The screen originally included a title; I removed it and enlarged the state text to make it easier to read. The 1.5-second silence threshold remains the starting point from Part C. Participant feedback identifies response latency as the next improvement to address.

### Revised dialogue and state sequence

| Stage | User or device action | Feedback and waiting behavior |
|---|---|---|
| IDLE | User presses the green button. | The screen shows IDLE until the turn starts. |
| Listening cue | Device says “I'm listening.” | The cue finishes before microphone capture begins. |
| LISTENING | User asks “Is anyone at the entrance?” | The LED is on and the screen shows LISTENING. After 1.5 seconds of silence, capture ends. |
| THINKING | The request is transcribed; the wizard reviews it with fresh camera evidence. | The screen shows THINKING during processing and approval. Extra button presses do not start another turn. |
| SPEAKING | The wizard approves “The camera currently detects one person.” when the live count is one. | The screen shows SPEAKING while Piper plays the answer. |
| IDLE | The reply finishes. | The device returns to IDLE and accepts a new turn. |

For a fresh zero count, the reply says that no person is currently detected. If a count is unavailable, the reply explains that it is waiting for camera information. Unsupported questions, such as asking who a person is, require an explanation of the system's limits. The wizard can correct a misrecognized request before approving a reply. If no speech begins within ten seconds, capture times out; if the wizard does not approve within sixty seconds, the interaction returns to idle. These bounds prevent an indefinite wait, but they do not solve the response latency reported by participants.

## Evaluation

### What worked well about the system and what didn't?
The people who tried the prototype said it worked well, but the latency was too high. This suggests that the basic interaction was useful, while the wait for an answer made it less practical. In my own checks, the button, listening cue, LED, and readable screen states provided clear feedback, and the system could answer from real camera detections. Speech recognition sometimes made mistakes, requiring a human correction. The participant feedback is qualitative; I did not collect separate timing measurements for each person.

### What worked well about the controller and what didn't?
The controller let the wizard review the recognized request and camera evidence, correct recognition errors, and approve a factual reply. That flexibility helped recover from mistakes without inventing camera observations. The main limitation was the extra time needed for a human to review and approve the answer. Tool permission prompts also interrupted earlier demo attempts. In my confirmed combined trial, 9.92 seconds of the 11.96-second endpoint-to-playback-request interval were spent waiting for wizard approval and tool interaction, so processing speed alone would not remove most of that example's delay.

### What lessons can you take away from the WoZ interactions for designing a more autonomous version of the system?
The feedback pointed toward a more powerful device and full automation as possible improvements. Faster hardware could reduce speech-recognition and camera-processing time, while automation could remove the manual approval wait. These improvements have not been tested. An autonomous version would need to handle the corrections and decisions the wizard currently makes: recognize supported questions, ask for clarification when recognition is uncertain, use fresh camera evidence, and explain when information is unavailable. I would keep the listening cue, LED, and screen states so users can follow the interaction while waiting.

### How could you use your system to create a dataset of interaction? What other sensing modalities would make sense to capture?
With participant agreement, I could log each request, its recognized transcript, the camera count and availability, the wizard's correction or approved reply, and the interaction timestamps. These records could help identify common recognition errors, unsupported requests, and sources of delay. Button events and screen-state transitions would provide useful context about turn-taking. Consented audio could help evaluate recognition, and synchronized camera clips could help compare detections with the actual scene. A distance or motion sensor could provide an additional presence signal. These are proposed dataset extensions; I have not collected such a participant dataset.
