"""
Part H: the night shift. Log the interpreter's readings all night, headless.
It only senses and logs; the reasoning waits for the morning (morning.py).

    python overnight.py                  # one look every 15 s until Ctrl-C
    python overnight.py --interval 5     # look more often (a fake night)
    python overnight.py --all            # log the other objects too, not only people (see Part E)
    python overnight.py --snaps          # also save a snapshot when someone is in view (off by default)

Fake a night first: run it for thirty seconds while you walk around, Ctrl-C, then run morning.py.

Writes night_log.jsonl (one JSON object per line): a "bedtime" event when it starts, a reading
whenever it changes, an "alive" line every 10 minutes so you can tell a quiet night from a
crashed one, and a "wake" event when it stops. The webcam mirrors its image (Part E), so each
frame is flipped back before YOLO sees it, and "left" means the room's left.
Start it in tmux or with nohup so it survives the ssh disconnect (see the README).
sleep_tracker.py calls night_shift() for the night part of the whole interaction.
"""
import argparse
import datetime
import json
import pathlib
import time

import cv2


HOT, COOL = 75.0, 70.0      # degrees C: above HOT, look once a minute and stop the motion check until below COOL


def cpu_temp():
    try:
        return int(open("/sys/class/thermal/thermal_zone0/temp").read()) / 1000
    except (OSError, ValueError):
        return None

from yolo_to_qwen import interpret, model      # the interpreter you tuned in Part E


def night_shift(stop=lambda: False, interval=15, classes=(0,), snaps=False, alarm=None,
                log_path="night_log.jsonl", on_tick=None, cap=None, events=True, motion=True,
                on_frame=None):
    """Look every `interval` seconds until stop() is true or Ctrl-C.

    With motion=True it also compares a tiny blurred frame every half second and looks right
    away when more than 2% of it changes, so a quick walk past the door is not missed. Only
    the readings are logged, never the frames. on_frame(frame, reading) receives each raw frame
    it reads (the controller's optional camera window); nothing is stored.

    on_tick(now) is called about once a second between looks. Pass an open cv2.VideoCapture
    as cap to reuse it. events=False leaves the bedtime/wake lines to the caller
    (sleep_tracker.py writes them at the gestures).
    """
    own_cap = cap is None
    if own_cap:
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    if snaps:
        pathlib.Path("snaps").mkdir(exist_ok=True)
    log = open(log_path, "a")

    def write(entry):
        entry = {"t": datetime.datetime.now().isoformat(timespec="seconds"), **entry}
        log.write(json.dumps(entry) + "\n")
        log.flush()

    if events:
        write({"event": "bedtime"})
        if alarm:
            write({"event": "alarm_set", "alarm": alarm.strftime("%H:%M")})
    last, last_beat, hot = None, 0.0, False
    print("night shift started, Ctrl-C to stop", flush=True)
    try:
        while not stop():
            try:
                for _ in range(4):          # the webcam buffers a few frames; skip the stale ones
                    cap.grab()
                ok, frame = cap.read()
                if not ok:
                    raise RuntimeError("no frame")
                raw = frame
                frame = cv2.flip(frame, 1)  # undo the webcam's mirror
                r = model.predict(frame, imgsz=320, conf=0.4, classes=list(classes) if classes else None,
                                  verbose=False)[0]
                reading = interpret(r)
                if reading != last:
                    write({"reading": reading})
                    if snaps and reading != "nobody":
                        cv2.imwrite(f"snaps/{datetime.datetime.now():%Y%m%d-%H%M%S}.jpg", frame)
                    last = reading
                if on_frame:
                    on_frame(raw, reading)
                temp = cpu_temp()
                if temp is not None and not hot and temp >= HOT:
                    hot = True                  # the Pi is getting warm: look less often until it cools
                    write({"event": "hot", "temp": temp})
                elif hot and temp is not None and temp < COOL:
                    hot = False
                    write({"event": "cool", "temp": temp})
                if time.time() - last_beat > 600:
                    write({"alive": True, "temp": temp})
                    last_beat = time.time()
            except Exception as e:
                print("hiccup:", e, flush=True)
            t_next = time.time() + (60 if hot else interval)
            prev = None
            while time.time() < t_next and not stop():
                if on_tick:
                    on_tick(datetime.datetime.now())
                time.sleep(min(0.5, max(0.0, t_next - time.time())))
                if motion and not hot:      # a quick pass can fall between two looks; look early if something moves
                    ok, small = cap.read()
                    if ok and on_frame:
                        on_frame(small, last or "looking")
                    if ok:
                        small = cv2.GaussianBlur(cv2.cvtColor(cv2.resize(small, (80, 60)), cv2.COLOR_BGR2GRAY), (5, 5), 0)
                        if prev is not None and (cv2.absdiff(small, prev) > 25).mean() > 0.02:
                            break
                        prev = small
    finally:                                # Ctrl-C passes through to the caller after the log is closed
        if events:
            write({"event": "wake"})
        log.close()
        if own_cap:
            cap.release()
        print("night shift stopped", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--interval", type=float, default=15, help="seconds between looks")
    parser.add_argument("--all", action="store_true", help="detect all 80 classes, not only people")
    parser.add_argument("--snaps", action="store_true", help="save a snapshot when someone is in view")
    parser.add_argument("--log", default="night_log.jsonl")
    parser.add_argument("--no-motion", action="store_true", help="only look every --interval seconds")
    args = parser.parse_args()
    try:
        night_shift(interval=args.interval, classes=None if args.all else (0,), snaps=args.snaps,
                    log_path=args.log, motion=not args.no_motion)
    except KeyboardInterrupt:
        pass
