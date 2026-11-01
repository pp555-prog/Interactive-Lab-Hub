"""
The Quiet Coyote Sleep Tracker: the whole interaction in one program.

    DORMANT    the screen shows the sky for the time of day; waits for the Quiet Coyote
    GOODNIGHT  the screen sets like the sun; the device asks for the wake-up time and confirms it
    NIGHT      lullaby (fades out), doorway check every 15 s into night_log.jsonl, moonlit screen
    ALARM      sunrise screen from 10 minutes before; at the alarm time the sunrise song fades in
    REPORT     Quiet Coyote stops the alarm; the device says how long you slept and what happened

    python sleep_tracker.py                                  # run every night until Ctrl-C
    python sleep_tracker.py --once                           # one night, then exit
    python sleep_tracker.py --once --alarm-in 3 --music-minutes 1    # a short rehearsal

Run it in tmux. It pauses piscreen.service while it owns the screen and restarts it on exit.
"""
import argparse
import datetime
import json
import os
import subprocess
import threading
import time

import cv2

import audio
import coyote
import morning
import overnight
import sky_display
import voice

AUDIO = os.path.expanduser("~/lab5_audio")
LAST_ALARM = os.path.expanduser("~/.quiet_coyote_alarm")
RAMP = datetime.timedelta(minutes=10)          # the sunrise starts this long before the alarm


def say(text):
    voice.say(text)                                # voice.say also prints the line with the time


def log_event(path, **entry):
    with open(path, "a") as f:
        f.write(json.dumps({"t": datetime.datetime.now().isoformat(timespec="seconds"), **entry}) + "\n")


class Screen(threading.Thread):
    """Redraws the PiTFT in the background from the current state."""

    def __init__(self, enabled=True):
        super().__init__(daemon=True)
        self.state, self.since = "dormant", time.time()
        self.ctx = {"bedtime": datetime.datetime.now(), "alarm": datetime.datetime.now(), "events": [],
                    "slept": None, "show_events": False}
        self.display = sky_display.SkyDisplay() if enabled else None
        self.running = True

    def set(self, state, **ctx):
        self.ctx.update(ctx)
        self.state, self.since = state, time.time()

    def frame(self):
        now, age = datetime.datetime.now(), time.time() - self.since
        s, ctx = self.state, self.ctx
        if s == "goodnight":
            return sky_display.render("goodnight", ctx, now, p=min(1.0, age / 8), t=age), 0.1
        if s == "night":
            if now >= ctx["alarm"] - RAMP:          # the sunrise begins before the alarm
                p = 1 - (ctx["alarm"] - now) / RAMP
                return sky_display.render("alarm", ctx, now, p=min(1.0, max(0.0, p)), t=age), 0.5
            return sky_display.render("night", ctx, now, t=age), 2.0
        if s == "alarm":
            return sky_display.render("alarm", ctx, now, p=1.0, t=age), 0.1
        if s == "report":
            return sky_display.render("report", ctx, now), 1.0
        return sky_display.render("dormant", ctx, now, t=age), 1.0

    def run(self):
        while self.running:
            img, pause = self.frame()
            if self.display:
                self.display.show(img)
            time.sleep(pause)

    def close(self):
        self.running = False
        if self.display:
            time.sleep(0.3)
            self.display.close()


class Preview:
    """Optional camera window on the Pi desktop (--preview), for rehearsals: what the camera
    sees, mirrored like a mirror, with the state written on it. Off for real nights."""

    def __init__(self, enabled):
        self.enabled = enabled
        if enabled and not os.environ.get("DISPLAY"):
            os.environ.update(DISPLAY=":0", WAYLAND_DISPLAY="wayland-0", XDG_RUNTIME_DIR="/run/user/1000")

    def show(self, frame, text):
        if not self.enabled:
            return
        view = cv2.flip(frame, 1)           # a mirror view is easiest to aim with
        cv2.putText(view, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 4)
        cv2.putText(view, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        cv2.imshow("Quiet Coyote camera", view)
        cv2.waitKey(1)

    def close(self):
        if self.enabled:
            cv2.destroyAllWindows()


def wait_for_coyote(cap, gesture, until=None, label="", preview=None):
    """Watch for the held Quiet Coyote. Returns True when seen, False at `until`."""
    print(f"{datetime.datetime.now():%H:%M:%S} waiting for the Quiet Coyote {label}", flush=True)
    while until is None or datetime.datetime.now() < until:
        ok, frame = cap.read()
        if not ok:
            time.sleep(0.5)
            continue
        fired = gesture.update(cv2.flip(frame, 1))
        if preview:
            hold = gesture.holding()
            hand = "hand seen" if gesture.last_ratios else "no hand"
            preview.show(frame, f"{label.strip('()')}: {hand}" + (f", holding {hold:.0%}" if hold else ""))
        if fired:
            print(f"{datetime.datetime.now():%H:%M:%S} Quiet Coyote!", flush=True)
            return True
    return False


def load_last_alarm():
    try:
        return datetime.datetime.strptime(open(LAST_ALARM).read().strip(), "%H:%M")
    except (OSError, ValueError):
        return datetime.datetime.strptime("07:00", "%H:%M")


def one_night(args, cap, gesture, screen, preview):
    last = load_last_alarm()
    screen.set("dormant", alarm=voice.next_at(last))
    wait_for_coyote(cap, gesture, label="(bedtime)", preview=preview)

    # Hand-off: bedtime is the gesture; the screen sets while we talk about the alarm.
    bedtime = datetime.datetime.now()
    log_event(args.log, event="bedtime")
    screen.set("goodnight", bedtime=bedtime)
    if args.alarm_in is not None:
        alarm = datetime.datetime.now().replace(second=0, microsecond=0) + datetime.timedelta(minutes=args.alarm_in + 1)
        say(f"Good night. This is a rehearsal, so I'll wake you at {voice.spoken(alarm)}. I'm tracking your sleep.")
    else:
        alarm, heard = voice.ask_time(last_alarm=last)
        print(f"heard {heard!r} -> {alarm}", flush=True)
    with open(LAST_ALARM, "w") as f:
        f.write(alarm.strftime("%H:%M"))
    log_event(args.log, event="alarm_set", alarm=alarm.strftime("%H:%M"))
    screen.ctx["alarm"] = alarm                    # keep the sunset running, just add the alarm time
    time.sleep(max(0.0, 8 - (time.time() - screen.since)))          # let the sunset finish

    # Night: lullaby that fades out, and the doorway check until the alarm.
    music = audio.Player(args.lullaby, loop=True, gain=0.5, stop_after=args.music_minutes * 60,
                         fade_out=min(60, args.music_minutes * 20)).start()
    screen.set("night", bedtime=bedtime, alarm=alarm)
    overnight.night_shift(stop=lambda: datetime.datetime.now() >= alarm, interval=args.interval,
                          log_path=args.log, cap=cap, events=False,
                          on_frame=(lambda f, text: preview.show(f, f"night: {text}")) if preview.enabled else None)
    music.stop()

    # Alarm: the sunrise song fades in and repeats until the Quiet Coyote.
    screen.set("alarm", bedtime=bedtime, alarm=alarm)
    ring = audio.Player(args.alarm_sound, loop=True, gain=1.0, start_gain=0.05, fade_in=60).start()
    closing = {}                                    # Qwen writes its closing line while the alarm rings,
    worker = None                                   # so it never competes with the spoken report
    if not args.no_model:
        worker = threading.Thread(target=lambda: closing.update(line=morning.ask_closing(args.model)), daemon=True)
        worker.start()
    stopped = wait_for_coyote(cap, gesture, until=alarm + datetime.timedelta(minutes=args.alarm_minutes),
                              label="(alarm)", preview=preview)
    ring.stop()
    log_event(args.log, event="wake" if stopped else "alarm_timeout")
    if not stopped:
        log_event(args.log, event="wake")

    # Report: the facts come from code and are spoken right away; Qwen only adds a closing
    # line, written while the facts are being spoken, and dropped if it says anything factual.
    entries, bad = morning.load(args.log)
    facts = morning.analyze(entries)
    facts["bad"] = bad
    screen.set("report", bedtime=facts["bedtime"] or bedtime, alarm=facts["wake"] or alarm,
               wake=facts["wake"] or alarm, slept=facts["slept"], events=[v["start"] for v in facts["visits"]])
    say("Good morning. " + morning.template(facts))
    if worker:
        worker.join(timeout=20)
        print(f"closing line from Qwen: {closing.get('line')!r}", flush=True)
        if closing.get("line"):
            say(closing["line"])
    time.sleep(args.report_seconds)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true", help="one night, then exit")
    parser.add_argument("--alarm-in", type=float, help="rehearsal: skip the question, alarm in N minutes")
    parser.add_argument("--music-minutes", type=float, default=30)
    parser.add_argument("--alarm-minutes", type=float, default=20, help="give up ringing after this long")
    parser.add_argument("--interval", type=float, default=15)
    parser.add_argument("--report-seconds", type=float, default=60)
    parser.add_argument("--lullaby", default=os.path.join(AUDIO, "quiet_coyote_lullaby.wav"))
    parser.add_argument("--alarm-sound", default=os.path.join(AUDIO, "quiet_coyote_sunrise.wav"))
    parser.add_argument("--log", default="night_log.jsonl")
    parser.add_argument("--model", default="qwen3.5:0.8b")
    parser.add_argument("--no-model", action="store_true")
    parser.add_argument("--no-screen", action="store_true")
    parser.add_argument("--preview", action="store_true", help="show the camera on the Pi desktop (rehearsals)")
    args = parser.parse_args()
    preview = Preview(args.preview)

    restore = False
    if not args.no_screen and subprocess.run(["systemctl", "is-active", "--quiet", "piscreen.service"]).returncode == 0:
        subprocess.run(["sudo", "-n", "systemctl", "stop", "piscreen.service"], check=True)
        restore = True
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    gesture = coyote.Coyote()
    screen = Screen(enabled=not args.no_screen)
    screen.start()
    try:
        while True:
            one_night(args, cap, gesture, screen, preview)
            if args.once:
                break
    except KeyboardInterrupt:
        pass
    finally:
        preview.close()
        screen.close()
        cap.release()
        if restore:
            subprocess.run(["sudo", "-n", "systemctl", "start", "piscreen.service"])
        print("sleep tracker stopped", flush=True)


if __name__ == "__main__":
    main()
