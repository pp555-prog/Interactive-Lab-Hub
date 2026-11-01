"""
Speaking and listening for the sleep tracker, using the Lab 3 speech setup.

Piper (text to speech) and faster-whisper (speech to text) are installed in the Lab 3
virtual environment, so they run there as small subprocesses; this file only needs the
standard library. Audio goes through the USB mic and speaker from Lab 3.

    python voice.py say "Good night."          # speak a sentence
    python voice.py ask                        # ask for a wake-up time and print what was understood
    python voice.py parse "seven fifteen"      # parse a time without the microphone
"""
import datetime
import os
import re
import subprocess
import sys
import tempfile

HUB = os.path.expanduser("~/Interactive-Lab-Hub")
LAB3_PY = os.path.join(HUB, "Lab 3", ".venv", "bin", "python")
VOICES = os.path.join(HUB, "Lab 3", "voices")
VOICE = "en_US-lessac-medium"


def usb_device(kind="aplay"):
    """ALSA name (plughw:N,0) of the USB sound card, found by name because the card numbers
    change between boots. The Lab 3 "USB PnP" mic is preferred over the webcam's mic."""
    try:
        out = subprocess.run([kind, "-l"], capture_output=True, text=True).stdout
    except FileNotFoundError:
        return "default"
    for pattern in (r"card (\d+): .*USB PnP", r"card (\d+): .*USB"):
        m = re.search(pattern, out)
        if m:
            return f"plughw:{m.group(1)},0"
    return "default"


def say(text, volume=1.0):
    """Speak text through the USB speaker. Blocks until it has been said."""
    print(f"{datetime.datetime.now():%H:%M:%S} says: {text}", flush=True)
    # Synthesize the whole sentence first, then play it: streaming stuttered ("underrun")
    # in the rehearsal when Qwen was busy at the same time.
    fd, wav = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    try:
        subprocess.run([LAB3_PY, "-m", "piper", "--model", VOICE, "--data-dir", VOICES,
                        "--volume", str(volume), "--output-file", wav, "--", text],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        subprocess.run(["aplay", "-q", "-D", usb_device(), wav])
    finally:
        os.remove(wav)


TRANSCRIBE = """
import sys
from faster_whisper import WhisperModel
m = WhisperModel("tiny.en", device="cpu", compute_type="int8")
segments, _ = m.transcribe(sys.argv[1], beam_size=1, language="en")
print(" ".join(s.text.strip() for s in segments))
"""


def listen(seconds=4):
    """Record from the USB mic and return the transcript ("" if nothing was heard)."""
    fd, wav = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    try:
        subprocess.run(["arecord", "-q", "-D", usb_device("arecord"), "-f", "S16_LE", "-r", "16000",
                        "-c", "1", "-d", str(seconds), wav], check=True)
        out = subprocess.run([LAB3_PY, "-c", TRANSCRIBE, wav], capture_output=True, text=True)
        return out.stdout.strip()
    finally:
        os.remove(wav)                         # recordings are never kept


UNITS = {"zero": 0, "oh": 0, "o": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
         "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13,
         "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19}
TENS = {"twenty": 20, "thirty": 30, "forty": 40, "fifty": 50}


def numbers(text):
    """The numbers in a transcript, in order: "seven forty five" -> [7, 45], "6:30" -> [6, 30]."""
    text = re.sub(r"(\d)[:.](\d)", r"\1 \2", text.lower()).replace("-", " ")
    tokens = re.findall(r"\d+|[a-z']+", text)
    out, i = [], 0
    while i < len(tokens):
        tok = tokens[i]
        if tok.isdigit():
            if len(tok) in (3, 4) and int(tok[-2:]) < 60:         # "715" -> 7, 15
                out += [int(tok[:-2]), int(tok[-2:])]
            else:
                out.append(int(tok))
        elif tok in TENS:
            n = TENS[tok]
            if i + 1 < len(tokens) and tokens[i + 1] in UNITS and 0 < UNITS[tokens[i + 1]] < 10:
                n += UNITS[tokens[i + 1]]
                i += 1
            out.append(n)
        elif tok in ("oh", "o") and out and i + 1 < len(tokens) and tokens[i + 1] in UNITS:
            out.append(UNITS[tokens[i + 1]])                       # "seven oh five" -> 7, 5
            i += 1
        elif tok in UNITS and tok not in ("oh", "o"):
            out.append(UNITS[tok])
        i += 1
    return out


def parse_time(text, now=None):
    """The next datetime matching a spoken wake-up time, or None if there is no time in it."""
    now = now or datetime.datetime.now()
    t = text.lower()
    if "noon" in t:
        h, m = 12, 0
    elif "midnight" in t:
        h, m = 0, 0
    else:
        nums = numbers(t)
        if not nums:
            return None
        if "half past" in t:
            h, m = nums[0], 30
        elif "quarter past" in t:
            h, m = nums[0], 15
        elif "quarter to" in t:
            h, m = (nums[0] - 1) % 24, 45
        else:
            h, m = nums[0], nums[1] if len(nums) > 1 else 0
        if not (0 <= h <= 23 and 0 <= m <= 59):
            return None
    pm = re.search(r"\bp\.? ?m\b|evening|afternoon|tonight", t)
    am = re.search(r"\ba\.? ?m\b|morning", t)
    # Without am/pm, take whichever comes next: at bedtime "seven fifteen" is 7:15 am, and in a
    # rehearsal at 6 pm "six ten" is 6:10 pm. Whisper often drops "pm", and the confirmation
    # always says the part of day, so a wrong guess is heard right away.
    candidates = [h] if h > 12 or h == 0 or "noon" in t or "midnight" in t else \
        [h % 12 + 12] if pm else [h % 12] if am else [h % 12, h % 12 + 12]
    best = None
    for hour in candidates:
        c = now.replace(hour=hour, minute=m, second=0, microsecond=0)
        if c <= now:
            c += datetime.timedelta(days=1)
        if best is None or c < best:
            best = c
    return best


def next_at(t, now=None):
    """The next datetime at exactly t's hour and minute (24-hour, no guessing)."""
    now = now or datetime.datetime.now()
    c = now.replace(hour=t.hour, minute=t.minute, second=0, microsecond=0)
    return c if c > now else c + datetime.timedelta(days=1)


def is_no(text):
    return bool(re.search(r"\b(no|nope|nah|wrong|change|not right)\b", text.lower()))


def ask_time(last_alarm=None, tries=3):
    """Ask for the wake-up time by voice, read it back, and let the person correct it.

    After "Alarm set for ...", it listens a few seconds more: "no" asks again, and a
    new time ("no, six oh two") replaces the old one. Silence or anything else keeps it.
    Returns (alarm datetime, everything that was heard).
    """
    say("Good night. What time should I wake you?")
    heard, alarm = [], None
    for attempt in range(tries):
        text = listen(5)
        heard.append(text)
        alarm = parse_time(text) or alarm
        if not parse_time(text):
            if attempt < tries - 1:
                say("Sorry, I didn't catch that. What time should I wake you?")
            continue
        for _ in range(3):                            # read it back until it is accepted
            say(f"Alarm set for {spoken(alarm)}. Say no to change it.")
            reply = listen(3)
            heard.append(reply)
            new = parse_time(reply)
            if new and new != alarm:
                alarm = new                           # "no, six oh two": take the new time and read it back
                continue
            if is_no(reply):
                break                                 # ask again
            say("Okay. I'm tracking your sleep.")
            return alarm, " | ".join(heard)
        if attempt < tries - 1:
            alarm = None
            say("Okay. What time should I wake you?")
    heard = " | ".join(heard)
    if last_alarm:
        alarm = next_at(last_alarm)
        say(f"I still didn't catch it, so I kept your alarm at {spoken(alarm)}. I'm tracking your sleep.")
        return alarm, heard
    return None, heard


def spoken(t):
    """How the device says a time. Always with the part of day, so a misheard "pm" is audible."""
    h = t.hour % 12 or 12
    part = "in the morning" if t.hour < 12 else "in the afternoon" if t.hour < 18 else "in the evening"
    if not t.minute:
        return f"{h} o'clock {part}"
    return f"{h} oh {t.minute} {part}" if t.minute < 10 else f"{h} {t.minute} {part}"


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "say":
        say(" ".join(sys.argv[2:]))
    elif len(sys.argv) >= 3 and sys.argv[1] == "parse":
        print(parse_time(" ".join(sys.argv[2:])))
    elif len(sys.argv) == 2 and sys.argv[1] == "ask":
        print(ask_time())
    else:
        print(__doc__)
