"""
The Quiet Coyote, as an on/off switch for the night.

Same rule as hand_pose.py (index and pinky up and apart, middle and ring touching the
thumb), but every distance is divided by the size of the hand (wrist to the middle
knuckle), so the gesture means the same thing close to the camera and at arm's length
(Part C). It only counts once it has been held for about a second.

    python coyote.py               # print QUIET COYOTE whenever the held gesture is seen (headless)
    python coyote.py --calibrate   # print the ratios for every frame with a hand, to tune APART and TOUCH
"""
import argparse
import math
import time

import cv2
import mediapipe as mp

# In hand sizes. Calibrated on my hand (2026-11-01): fingers apart measured 0.9-1.8 close up and
# down to about 0.6 at arm's length; touching fingertips stayed under 0.25.
APART, TOUCH = 0.5, 0.35


def ratios(lm):
    """Finger distances divided by hand size, from MediaPipe's 21 normalized landmarks."""
    d = lambda a, b: math.hypot(lm[a].x - lm[b].x, lm[a].y - lm[b].y)
    size = d(0, 9) or 1e-6
    return {"thumb_index": d(4, 8) / size, "index_middle": d(8, 12) / size,
            "middle_ring": d(12, 16) / size, "ring_pinky": d(16, 20) / size,
            "thumb_ring": d(4, 16) / size}


def is_coyote(r, apart=APART, touch=TOUCH):
    return (r["thumb_index"] > apart and r["index_middle"] > apart and r["ring_pinky"] > apart
            and r["middle_ring"] < touch and r["thumb_ring"] < touch)


class Coyote:
    """Feed it frames; trigger() is true once per held gesture."""

    def __init__(self, hold=1.0):
        self.hands = mp.solutions.hands.Hands(max_num_hands=1, model_complexity=0,
                                              min_detection_confidence=0.6, min_tracking_confidence=0.5)
        self.hold = hold
        self.since, self.fired, self.last_seen = None, False, 0.0
        self.last_ratios = None

    def update(self, frame_bgr, now=None):
        """True on the frame where the gesture has been held long enough."""
        now = now or time.time()
        result = self.hands.process(cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB))
        seen = False
        if result.multi_hand_landmarks:
            self.last_ratios = ratios(result.multi_hand_landmarks[0].landmark)
            seen = is_coyote(self.last_ratios)
        else:
            self.last_ratios = None
        if seen:
            self.last_seen = now
            if self.since is None:
                self.since = now
        elif now - self.last_seen > 0.3:          # allow one dropped frame without restarting the hold
            self.since, self.fired = None, False
        if self.since is not None and not self.fired and now - self.since >= self.hold:
            self.fired = True
            return True
        return False

    def holding(self, now=None):
        """0..1, how far into the hold we are (for feedback on the screen)."""
        if self.since is None or self.fired:
            return 0.0
        return min(1.0, ((now or time.time()) - self.since) / self.hold)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--calibrate", action="store_true")
    args = parser.parse_args()
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    coyote = Coyote()
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                time.sleep(0.5)
                continue
            if coyote.update(cv2.flip(frame, 1)):
                print(time.strftime("%H:%M:%S"), "QUIET COYOTE", flush=True)
            if args.calibrate and coyote.last_ratios:
                r = coyote.last_ratios
                print(f"{time.time():.1f}", " ".join(f"{k}={v:.2f}" for k, v in r.items()),
                      "COYOTE" if is_coyote(r) else "", flush=True)
    except KeyboardInterrupt:
        pass
    finally:
        cap.release()
