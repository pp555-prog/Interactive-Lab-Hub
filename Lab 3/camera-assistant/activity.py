"""Session-only Frigate evidence. No identities, images, or audio are stored."""
import math
import threading
import time


class Activity:
    def __init__(self, camera="entrance", clock=time.time):
        self.camera, self.clock = camera, clock
        self.lock = threading.RLock()
        self.started = clock()
        self.coverage = self.started
        self.online = False
        self.stats_at = 0
        self.camera_fps = 0
        self.events = {}
        self.count = None
        self.detection_enabled = None

    def availability(self, online):
        with self.lock:
            if self.online != online:
                self.coverage = self.clock()
                self.count = None
                self.stats_at = 0
                self.detection_enabled = None
            self.online = online

    def ingest(self, topic, value):
        with self.lock:
            now = self.clock()
            if topic == "frigate/stats":
                camera = value.get("cameras", {}).get(self.camera, {})
                fps = float(camera.get("camera_fps", 0))
                if self.camera_fps <= 0 or now - self.stats_at >= 25 or fps <= 0:
                    self.coverage = now
                if fps <= 0 or (self.stats_at and now - self.stats_at >= 25):
                    self.count = None
                self.camera_fps = fps
                self.stats_at = now
                # A restart can publish detect/state before available. Bootstrap
                # only unknown state from real stats; never override explicit OFF.
                detected = camera.get("detection_enabled")
                if self.detection_enabled is None and isinstance(detected, bool):
                    self.detection_enabled = detected
                    if not detected:
                        self.count = None
            elif topic == f"frigate/{self.camera}/person":
                self.count = max(0, int(value))
            elif topic == f"frigate/{self.camera}/detect/state":
                self.detection_enabled = value == "ON"
                if not self.detection_enabled:
                    self.coverage = now
                    self.count = None
            elif topic == "frigate/events":
                item = value.get("after", {})
                if (item.get("camera") != self.camera or item.get("label") != "person"
                        or item.get("false_positive", False)):
                    return
                ident = item.get("id")
                start = float(item.get("start_time", now))
                frame = float(item.get("frame_time", start))
                end = item.get("end_time")
                if not ident or not all(math.isfinite(x) for x in (start, frame)):
                    return
                previous = self.events.get(ident)
                # Ignore reordered messages and never resurrect an ended event.
                if previous and (frame < previous["frame"] or
                                 (previous["end"] is not None and end is None)):
                    return
                self.events[ident] = {"start": start, "frame": frame, "end": end}
                # Recent history is bounded. Ongoing objects must remain visible.
                self.events = {k: v for k, v in self.events.items()
                               if v["end"] is None or v["frame"] >= now - 3600}

    def snapshot(self):
        with self.lock:
            now = self.clock()
            fresh = (self.online and self.detection_enabled is True
                     and now - self.stats_at < 25 and self.camera_fps > 0)
            return {"available": fresh, "mqtt_online": self.online,
                    "camera_fps": self.camera_fps, "coverage_since": self.coverage,
                    "detection_enabled": self.detection_enabled,
                    "started": self.started, "person_count": self.count,
                    "events": [{"id": k, **v} for k, v in self.events.items()]}

    def answer(self, intent):
        if intent == "identity":
            return "I can detect people, but I can't identify them."
        if intent == "unclear":
            return "I didn't catch that. Press the button and try again."
        if intent == "unsupported":
            return "Ask whether anyone is in view, when a person was last detected, or about the last five minutes."
        data = self.snapshot()
        now = self.clock()
        if not data["available"]:
            return "Camera data is unavailable, so I can't answer that right now."
        if intent == "current":
            count = data["person_count"]
            if count is None:
                return "I'm waiting for the camera's current person count."
            return ("No person is currently detected." if count == 0 else
                    f"The camera currently detects {count} {'person' if count == 1 else 'people'}.")
        events = data["events"]
        if intent == "last":
            if not events:
                return "No person detection has been received during this connection. Earlier activity may be missing."
            last = max(v["frame"] for v in events)
            age = max(0, round(now - last))
            return f"A person was last detected {age} seconds ago. This is based on received events."
        if intent == "recent":
            count = sum(v["frame"] >= now - 300 for v in events)
            prefix = ("I have less than five minutes of uninterrupted history. "
                      if now - data["coverage_since"] < 300 else "")
            return prefix + f"I received {count} distinct person detection events in the last five minutes. These are events, not unique people."
        return self.answer("unsupported")


def classify(text):
    text = text.lower().strip()
    if not text:
        return "unclear"
    if "who" in text or "identify" in text:
        return "identity"
    if "five minutes" in text or "5 minutes" in text or "what happened" in text:
        return "recent"
    if "when" in text or "last detect" in text:
        return "last"
    if any(x in text for x in ("anyone", "anybody", "in view", "right now", "still there")):
        return "current"
    return "unsupported"
