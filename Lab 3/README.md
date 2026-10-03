# Chatterboxes

**Author:** Pablo Penalba. **AI assistance:** Codex assisted with setup, scripts, and documentation; listening observations and voice selection are mine.

[![Watch the video](https://user-images.githubusercontent.com/1128669/135009222-111fe522-e6ba-46ad-b6dc-d1633d21129c.png)](https://youtu.be/LZ0VJClIlRI?si=Yy84mcyVYuVV19mn)

In this lab, we want you to design interaction with a speech-enabled device — something that listens and talks to you. This device can do anything *but* control lights (since we already did that in Lab 1). First, we want you to storyboard what you imagine the conversational interaction to be like. Then you will use wizarding techniques to elicit examples of what people might say, ask, or respond. We then want you to use the examples collected from at least two other people to inform the redesign of the device.

We will focus on **audio** as the main modality for interaction to start; these general techniques can be extended to **video**, **haptics** or other interactive mechanisms in the second part of the Lab.

A note on what you are building with. Speech interfaces are usually taught as two boxes — speech-in, speech-out — and that framing hides the part that actually determines whether an interaction works. Between listening and speaking sits the question of **whose turn it is**: when does the device decide you have finished talking, and how long does it make you wait before it answers? This lab gives you direct control over both, and we will ask you to notice what changes when you move them.

## Prep for Part 1: Get the Latest Content and Pick up Additional Parts

Please check instructions in [prep.md](prep.md) and complete the setup.

### Pick up Web Camera If You Don't Have One

Students who have not already received a web camera will receive their Webcam and at the beginning of lab. If you cannot make it to class this week, please contact the TAs to ensure you get these.

### Get the Latest Content

As always, pull updates from the class Interactive-Lab-Hub to both your Pi and your own GitHub repo.

**\[recommended\]** Option 1: On the Pi, `cd` to your `Interactive-Lab-Hub`, pull the updates from upstream (class lab-hub) and push the updates back to your own GitHub repo. You will need the *personal access token* for this.

```
pi@ixe00:~$ cd Interactive-Lab-Hub
pi@ixe00:~/Interactive-Lab-Hub $ git pull upstream Fall2026
pi@ixe00:~/Interactive-Lab-Hub $ git add .
pi@ixe00:~/Interactive-Lab-Hub $ git commit -m "get lab3 updates"
pi@ixe00:~/Interactive-Lab-Hub $ git push
```

Option 2: On your own GitHub repo, create a pull request to get updates from the class Interactive-Lab-Hub. After you have the latest updates online, go to your Pi, `cd` to your `Interactive-Lab-Hub` and use `git pull`.

---

# Part 1

## Setup

Create and activate a virtual environment for this lab:

```
pi@ixe00:~$ cd Interactive-Lab-Hub/Lab\ 3
pi@ixe00:~/Interactive-Lab-Hub/Lab 3 $ python3 -m venv .venv
pi@ixe00:~/Interactive-Lab-Hub/Lab 3 $ source .venv/bin/activate
(.venv) pi@ixe00:~/Interactive-Lab-Hub/Lab 3 $
```

Install the Python dependencies:

```
(.venv) $ pip install -r requirements.txt
```

This takes a few minutes. If you would like it to take considerably less time, [`uv`](https://docs.astral.sh/uv/) is a drop-in replacement for `pip` that is dramatically faster on the Pi:

```
(.venv) $ pip install uv && uv pip install -r requirements.txt
```

Then run the setup script, which installs the classic speech synthesizers, downloads the voice activity detection model, and pre-fetches a neural voice and a speech recognition model so you are not waiting on downloads during lab:

```
(.venv):~$ cd speech-scripts
(.venv) $ ./setup.sh
```

Check your audio devices before going further. `arecord -l` lists capture devices and `aplay -l` lists playback devices; if your webcam microphone or Bluetooth speaker does not appear, fix that first — every script below assumes the system defaults are the ones you want.

## A. Text to Speech

Your Pi can speak in several quite different ways, and the differences are audible in a way that matters for design. In `speech-scripts/` there are shell scripts for each.

### The classic engines

```
(.venv) $ cd speech-scripts

(.venv) $ sudo apt update
(.venv) $ sudo apt install -y espeak festival festvox-kallpc16k

(.venv) $ ./espeak_demo.sh
(.venv) $ ./festival_demo.sh
```

You can run these `.sh` files by typing `./filename`, and read one with `cat filename`. You can also play audio files directly with `aplay filename` — try `aplay lookdave.wav`.

These are all decades-old technology and they sound like it. `espeak-ng` is a *formant synthesizer*: it generates speech from an acoustic model of the vocal tract, which is why it sounds robotic but also why the whole thing fits in a couple of megabytes and responds instantly. `festival` is *concatenative*: they stitch together recorded fragments of a real speaker, which sounds more human but breaks audibly at the seams.

### Neural TTS with Piper

Note that the Piper command line changed in version 1.x — voices are now downloaded explicitly with `python3 -m piper.download_voices`, and you invoke it as `python3 -m piper`. Tutorials you find online may show the old `echo ... | piper --model ...` form, which no longer works. Browse the [voice samples](https://rhasspy.github.io/piper-samples) and download a different one if you'd like:

```
(.venv) $ python3 -m piper.download_voices en_US-lessac-medium
```

[Piper](https://github.com/OHF-Voice/piper1-gpl) synthesizes speech with a small neural network, runs comfortably on the Pi 5, and sounds markedly better than the above.

```
(.venv) $ ./piper_demo.sh
```

The demo script also shows `--output-raw`, which streams audio to the speaker as it is generated rather than writing a file first. Listen for the difference in how quickly speech begins. In a conversational system this gap is the thing your user experiences as responsiveness.

\*\***Write your own shell file to use your favorite of these TTS engines to have your Pi greet you by name.**\*\*
(This shell file should be saved to your own repo for this lab.)

\*\***Then answer: Is the same greeting, in these different voices, the same greeting? Describe one concrete way the voice changed what the utterance seemed to mean or who seemed to be speaking.**\*\*

### My greeting and voice comparison

I chose Piper (`en_US-lessac-medium`) for my [personalized greeting script](speech-scripts/greet_pablo.sh). It says: “Hello, Pablo. Welcome back. What would you like to work on today?” Run `./speech-scripts/greet_pablo.sh` from the Lab 3 directory.

The words were the same, but the greeting felt different depending on the voice. eSpeak sounded robotic, making it feel like a machine was addressing me. Festival sounded more human-like, although still robotic. Piper sounded best to me, so I chose it for my greeting.

I first listened to “Hello, Pablo,” but two words were too short to judge the voices well, so I compared all three with the longer greeting above. See [setup and listening notes](PART1A.md).

## B. Speech to Text

We use [faster-whisper](https://github.com/SYSTRAN/faster-whisper), a reimplementation of OpenAI's Whisper model that runs several times faster on CPU and does not require PyTorch. All processing happens on the Pi; nothing is sent to a server.

```
(.venv) $ python transcribe.py lookdave.wav
```

The transcript is not the interesting output here — the timings are. Run it again with a larger model and compare:

```
(.venv) $ python transcribe.py lookdave.wav --model base.en
(.venv) $ python transcribe.py lookdave.wav --model small.en
#  noted that the first run may take longer because the model is downloaded, and that the HF unauthenticated-request warning is expected and not an error.
```

Available sizes, smallest first: `tiny.en`, `base.en`, `small.en`, `medium.en`. The `.en` variants are English-only and faster than their multilingual counterparts at the same size.

\*\***Record a few seconds of your own speech (`arecord -d 5 -f cd -c 1 -r 16000 test.wav`) and transcribe it with at least two model sizes. Report the real-time factor for each. At what point does the accuracy improvement stop being worth the delay, for a system that has to answer you?**\*\*

\*\***Write your own script that verbally asks for a numerical input (a phone number, zipcode, number of pets) and records the answer the respondent provides.**\*\* Numbers are a good stress test — transcription systems make characteristic errors on digit strings, and you will want to know what they are before you design around them.

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

Storyboard and/or use a Verplank diagram to design a speech-enabled device. (Stuck? Make a device that talks for dogs. If that is too stupid, find an application that is better than that.)

\*\***Post your storyboard and diagram here.**\*\*

<img width="672" height="413" alt="image" src="https://github.com/user-attachments/assets/86d6cabd-876c-4c03-af6f-05f4a9ab5d06" />
<img width="678" height="387" alt="image" src="https://github.com/user-attachments/assets/17dc9275-f26b-4d39-b7fd-c030a9f531a8" />

Write out what you imagine the dialogue to be. Use cards, post-its, or whatever method helps you develop alternatives or group responses.

\*\***Please describe and document your process.**\*\*

Your script should include the pauses. Where does your device wait, and for how long? You now know from Part C that this is a parameter you have to choose, not something that happens for free.

## E. Acting out the dialogue

Find a partner, and *without sharing the script with your partner* try out the dialogue you've designed, where you (as the device designer) act as the device you are designing. Please record this interaction (for example, using Zoom's record feature).

\*\***Describe if the dialogue seemed different than what you imagined when it was acted out, and how.**\*\*


---

# Lab 3 Part 2

For Part 2, you will redesign the interaction with the speech-enabled device using the data collected, as well as feedback from part 1.

## Prep for Part 2

1. What are concrete things that could use improvement in the design of your device? For example: wording, timing, anticipation of misunderstandings.
2. What are other modes of interaction *beyond speech* that you might also use to clarify how to interact? In particular: how does someone know when the device is listening, and when it is thinking? You have a screen and an LED.
3. Make a new storyboard, diagram and/or script based on these reflections.
4. (optional) Integrate [input devices](inputs.md) in the system

## Prototype your system

The system should:
* use the Raspberry Pi
* use one or more sensors
* require participants to speak to it

*Document how the system works.*

*Include videos or screencaptures of both the system and the controller.*

## Test the system

Try to get at least two people to interact with your system. (Ideally, you would inform them that there is a wizard *after* the interaction, but we recognize that can be hard.)

Answer the following:

### What worked well about the system and what didn't?
\*\**your answer here*\*\*

### What worked well about the controller and what didn't?
\*\**your answer here*\*\*

### What lessons can you take away from the WoZ interactions for designing a more autonomous version of the system?
\*\**your answer here*\*\*

### How could you use your system to create a dataset of interaction? What other sensing modalities would make sense to capture?
\*\**your answer here*\*\*

<details>
  <summary><strong>Submission Cleanup Reminder (Click to Expand)</strong></summary>

  **Before submitting your README.md:**
  - This readme.md file has a lot of extra text for guidance.
  - Remove all instructional text and example prompts from this file.
  - You may either delete these sections or use the toggle/hide feature in VS Code to collapse them for a cleaner look.
  - Your final submission should be neat, focused on your own work, and easy to read for grading.
</details>
