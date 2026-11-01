"""
Part I: the morning reveal. Turn night_log.jsonl into a short, honest report.

The numbers come from code, not from the model: time slept is wake minus bedtime,
visits are runs of readings that are not "nobody", and gaps are stretches with no
log line at all (no reading and no heartbeat), which mean the night was not watched.
The report is a template filled with those facts. Qwen is only asked for one warm
closing line, never told anything about the night, and the line is dropped if it
contains a number, a time or anything about the door: in the rehearsal Qwen turned
3 minutes 33 seconds into "four minutes" and invented that I never left the room.

    python morning.py                          # print the report
    python morning.py --say --screen           # also speak it (Piper) and show it on the PiTFT
    python morning.py --no-model               # template only, no Qwen
    python morning.py --log some_other.jsonl
"""
import argparse
import datetime
import json
import os
import re

GAP = datetime.timedelta(minutes=15)      # heartbeats come every 10 min, so a longer silence is a gap


def load(path):
    """Log entries, oldest first. Lines that are not valid JSON with a time are skipped and counted."""
    entries, bad = [], 0
    if not os.path.exists(path):
        return entries, bad
    for line in open(path):
        if not line.strip():
            continue
        try:
            e = json.loads(line)
            e["dt"] = datetime.datetime.fromisoformat(e["t"])
            entries.append(e)
        except (ValueError, KeyError, TypeError):
            bad += 1
    return entries, bad


def analyze(entries):
    """Facts for the report. Nothing here is guessed: missing data stays missing."""
    facts = {"tracked": bool(entries), "backwards": 0, "visits": [], "gaps": [],
             "bedtime": None, "wake": None, "slept": None, "start": None, "end": None}
    if not entries:
        return facts
    starts = [i for i, e in enumerate(entries) if e.get("event") == "bedtime"]
    if starts:                                     # the log grows night after night; keep the last one
        entries = entries[starts[-1]:]
    for a, b in zip(entries, entries[1:]):
        if b["dt"] < a["dt"]:
            facts["backwards"] += 1
    entries = sorted(entries, key=lambda e: e["dt"])
    facts["start"], facts["end"] = entries[0]["dt"], entries[-1]["dt"]
    for e in entries:
        if e.get("event") == "bedtime" and facts["bedtime"] is None:
            facts["bedtime"] = e["dt"]
        if e.get("event") == "wake":
            facts["wake"] = e["dt"]
    if facts["bedtime"] and facts["wake"] and facts["wake"] > facts["bedtime"]:
        facts["slept"] = facts["wake"] - facts["bedtime"]

    visit = None
    for e in entries:
        if "reading" not in e:
            continue
        if e["reading"] != "nobody" and visit is None:
            visit = {"start": e["dt"], "end": None, "reading": e["reading"]}
        elif e["reading"] == "nobody" and visit is not None:
            visit["end"] = e["dt"]
            facts["visits"].append(visit)
            visit = None
    if visit is not None:
        facts["visits"].append(visit)              # still in view when the log stopped

    for a, b in zip(entries, entries[1:]):
        if b["dt"] - a["dt"] > GAP:
            facts["gaps"].append((a["dt"], b["dt"]))
    return facts


def clock(t, seconds=False):
    h = t.hour % 12 or 12
    s = f":{t.second:02d}" if seconds else ""
    return f"{h}:{t.minute:02d}{s} {'am' if t.hour < 12 else 'pm'}"


def duration(d):
    mins = round(d.total_seconds() / 60)
    h, m = divmod(mins, 60)
    if h and m:
        return f"{h} hours {m} minutes" if h != 1 else f"1 hour {m} minutes"
    return f"{h} hours" if h else f"{m} minutes"


def template(f):
    """The report without the model. Always honest, sometimes plain."""
    if not f["tracked"]:
        return "The night was not tracked. I have no log, so I cannot say how you slept or what happened."
    parts = []
    short = f["end"] - f["start"] < datetime.timedelta(minutes=10)     # a fake night: show seconds
    if f["slept"]:
        parts.append(f"You slept {duration(f['slept'])}, from {clock(f['bedtime'])} to {clock(f['wake'])}.")
    else:
        parts.append(f"I watched from {clock(f['start'], short)} to {clock(f['end'], short)}, "
                     "but I do not know when you went to bed and woke up.")
    n = len(f["visits"])
    if n == 0:
        parts.append("Nobody came to the door.")
    elif n == 1:
        parts.append(f"Someone came to the door once, at {clock(f['visits'][0]['start'], short)}.")
    else:
        times = [clock(v["start"], short) for v in f["visits"]]
        parts.append(f"Someone came to the door {n} times, at {', '.join(times[:-1])} and {times[-1]}." if n <= 3 else
                     f"Someone came to the door {n} times, the first at {times[0]}.")
    if f["gaps"]:
        a, b = f["gaps"][0]
        parts.append(f"I was not watching from {clock(a)} to {clock(b)}, so I may have missed something.")
    if f["backwards"] or f.get("bad"):
        parts.append("Part of the log was out of order or unreadable, so take this with a grain of salt.")
    return " ".join(parts)


NUMBER_WORDS = re.compile(r"\b(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|"
                          r"fifteen|twenty|thirty|forty|fifty|hour|minute|o'clock|am|pm|once|twice)\b", re.I)
EVENT_WORDS = re.compile(r"\b(door|someone|somebody|person|people|visit|visitor|nobody|quiet night|camera)\b", re.I)


def closing_ok(text):
    """A closing line is kept only if it is one short sentence with no facts in it:
    no digits, no number or time words, and nothing about the door or visitors.
    (In the rehearsal Qwen wrote "four minutes" and invented that I never left the room.)"""
    text = (text or "").strip().strip('"')
    text = re.sub(r"^(good morning|morning)[,.!]*\s*", "", text, flags=re.I)   # the report already said it
    text = text[:1].upper() + text[1:]
    if not text or len(text.split()) > 25 or re.search(r"\d", text):
        return None
    if NUMBER_WORDS.search(text) or EVENT_WORDS.search(text):
        return None
    return text


def ask_closing(model, tries=3):
    """One warm closing sentence from Qwen, or None. It is never told anything about the night,
    and it gets a few tries because some of its sentences are too long or slip in a fact."""
    import requests
    prompt = ("You are a gentle bedside device. Write one short, warm sentence to wish someone a good day "
              "as they get up. Do not mention numbers, times, sleep, or anything that happened.")
    for _ in range(tries):
        try:
            r = requests.post("http://localhost:11434/api/generate", json={
                "model": model, "prompt": prompt, "think": False, "stream": False,
                "options": {"temperature": 0.7, "num_predict": 40},
            }, timeout=120)
            r.raise_for_status()
            line = closing_ok(r.json()["response"])
            if line:
                return line
        except Exception as e:
            print("model unavailable:", e, flush=True)
            return None
    return None


def report(f, model=None):
    """(facts sentence, closing line or None). The facts never come from the model."""
    closing = ask_closing(model) if model and f["tracked"] else None
    return template(f), closing


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", default="night_log.jsonl")
    parser.add_argument("--model", default="qwen3.5:0.8b")
    parser.add_argument("--no-model", action="store_true", help="template only")
    parser.add_argument("--say", action="store_true", help="speak the report with Piper (voice.py)")
    parser.add_argument("--screen", action="store_true", help="show the report screen on the PiTFT")
    args = parser.parse_args()

    entries, bad = load(args.log)
    f = analyze(entries)
    f["bad"] = bad
    print(f"{len(entries)} log lines ({bad} unreadable), {len(f['visits'])} visits, "
          f"{len(f['gaps'])} gaps, {f['backwards']} times going backwards")
    text, source = report(f, None if args.no_model else args.model)
    print(f"\n[{source}] {text}")

    if args.screen:
        import sky_display
        ctx = {"bedtime": f["bedtime"] or f["start"] or datetime.datetime.now(),
               "alarm": f["wake"] or f["end"] or datetime.datetime.now(),
               "slept": f["slept"], "events": [v["start"] for v in f["visits"]]}
        ctx["wake"] = ctx["alarm"]
        screen = sky_display.SkyDisplay()
        screen.show(sky_display.render("report", ctx, datetime.datetime.now()))
    if args.say:
        import voice
        voice.say(text + (" " + closing if closing else ""))
