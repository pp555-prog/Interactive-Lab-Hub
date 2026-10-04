#!/usr/bin/env python3
"""Frigate-backed Camera Assistant with explicit wizard approval."""
import argparse
import json
import os
import queue
import secrets
import threading
import time
import urllib.request
from pathlib import Path

from flask import Flask, abort, jsonify, render_template, request, Response
from activity import Activity, classify


class Session:
    def __init__(self, activity, voice=None, log_path=None):
        self.activity, self.voice, self.log_path = activity, voice, log_path
        self.lock = threading.RLock()
        self.stop = threading.Event()
        self.work = queue.Queue(maxsize=1)
        self.approval = threading.Event()
        self.state = "IDLE"
        self.turn = None
        self.error = ""
        self.counter = 0

    def trigger(self, simulated_text=None):
        with self.lock:
            if self.state != "IDLE":
                return False
            if self.voice is None and simulated_text is None:
                return False
            self.counter += 1
            self.turn = {"id": self.counter, "text": "", "reply": "", "timing": {}}
            self.error = ""
            self.approval.clear()
            self.state = "PREPARING"
            self.work.put_nowait(simulated_text)
            return True

    def approve(self, turn_id, reply):
        with self.lock:
            if self.state != "THINKING" or not self.turn or self.turn["id"] != turn_id:
                return False
            self.turn["reply"] = reply
            self.turn["timing"]["approved_at"] = time.monotonic()
            self.state = "SPEAKING"
            self.approval.set()
            return True

    def snapshot(self):
        with self.lock:
            turn = json.loads(json.dumps(self.turn))
            suggestions = {intent: self.activity.answer(intent) for intent in
                           ("current", "last", "recent", "identity", "unclear", "unsupported")}
            return {"state": self.state, "turn": turn, "error": self.error,
                    "activity": self.activity.snapshot(), "suggestions": suggestions,
                    "simulation": self.voice is None}

    def worker(self):
        while not self.stop.is_set():
            try:
                simulated = self.work.get(timeout=0.5)
            except queue.Empty:
                continue
            try:
                if self.voice:
                    self.voice.say("I'm listening.")
                    with self.lock:
                        self.state = "LISTENING"
                    captured = self.voice.listen(self.stop)
                    if captured is None:
                        with self.lock:
                            self.turn["outcome"] = "no_speech_or_capture_limit"
                        continue
                    samples, timings = captured
                    # TRANSCRIBING avoids enabling approval while ASR is running.
                    with self.lock:
                        self.state = "TRANSCRIBING"
                    text, asr_s = self.voice.transcribe(samples)
                    timings["asr_s"] = asr_s
                else:
                    text = simulated
                    timings = {"endpoint_at": time.monotonic(), "asr_s": 0}
                timings["wizard_ready_at"] = time.monotonic()
                with self.lock:
                    self.turn.update(text=text, intent=classify(text), timing=timings)
                    self.state = "THINKING"
                if not self.approval.wait(60):
                    with self.lock:
                        self.turn["outcome"] = "wizard_timeout"
                    continue
                if self.stop.is_set():
                    break
                with self.lock:
                    reply = self.turn["reply"]
                first = self.voice.say(reply) if self.voice else time.monotonic()
                with self.lock:
                    t = self.turn["timing"]
                    t["wizard_s"] = t["approved_at"] - t["wizard_ready_at"]
                    t["first_play_request_at"] = first
                    t["endpoint_to_play_request_s"] = first - t["endpoint_at"] if first else None
                    if t.get("last_vad_speech_at") and first:
                        t["estimated_speech_end_to_play_request_s"] = first - t["last_vad_speech_at"]
                    self.turn["outcome"] = "reply_played" if self.voice else "simulated_reply"
            except Exception as exc:
                with self.lock:
                    self.error = f"{type(exc).__name__}: {exc}"
                    self.turn["outcome"] = "error"
            finally:
                with self.lock:
                    if self.log_path and self.turn:
                        try:
                            self.log_path.parent.mkdir(parents=True, exist_ok=True)
                            with self.log_path.open("a", encoding="utf-8") as handle:
                                handle.write(json.dumps({"recorded_at": time.time(), "turn": self.turn,
                                    "simulation": self.voice is None, "error": self.error}) + "\n")
                        except OSError as exc:
                            self.error = f"Private log write failed: {exc}"
                    self.state = "IDLE"


def create_app(session, token, frigate_url="http://127.0.0.1:5000"):
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = 4096

    def authorized():
        # A custom header also prevents cross-site form submissions.
        if not secrets.compare_digest(request.headers.get("X-Controller-Token", ""), token):
            abort(403)

    @app.get("/")
    def participant():
        return render_template("participant.html")

    @app.get("/controller")
    def controller():
        # Token is entered by the wizard and held only in this browser tab.
        return render_template("controller.html")

    @app.get("/api/status")
    def status():
        with session.lock:
            public_state = "THINKING" if session.state == "TRANSCRIBING" else session.state
            return jsonify(state=public_state)

    @app.get("/api/controller")
    def snapshot():
        authorized()
        return jsonify(session.snapshot())

    @app.post("/api/trigger")
    def trigger():
        authorized()
        body = request.get_json(silent=True) or {}
        text = body.get("text")
        if text is not None and (session.voice or not isinstance(text, str) or len(text) > 500):
            abort(400)
        accepted = session.trigger(text)
        return jsonify(accepted=accepted), 202 if accepted else 409

    @app.post("/api/approve")
    def approve():
        authorized()
        body = request.get_json(silent=True) or {}
        reply = body.get("reply")
        if not isinstance(reply, str) or not reply.strip() or len(reply) > 500:
            abort(400)
        accepted = session.approve(body.get("turn_id"), reply.strip())
        return jsonify(accepted=accepted), 200 if accepted else 409

    @app.get("/api/camera.jpg")
    def camera():
        authorized()
        try:
            # Fixed server/camera path; browsers cannot choose an arbitrary URL.
            url = frigate_url.rstrip("/") + f"/api/{session.activity.camera}/latest.jpg"
            with urllib.request.urlopen(url, timeout=3) as result:
                data = result.read(4 * 1024 * 1024)
            return Response(data, mimetype="image/jpeg", headers={"Cache-Control": "no-store"})
        except Exception:
            abort(503)

    return app


def start_mqtt(activity, host, port):
    import paho.mqtt.client as mqtt
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

    def connected(client, userdata, flags, reason, properties):
        if reason == 0:
            for topic in ("frigate/available", "frigate/events", "frigate/stats",
                          f"frigate/{activity.camera}/person", f"frigate/{activity.camera}/detect/state"):
                client.subscribe(topic)

    def disconnected(client, userdata, flags, reason, properties):
        activity.availability(False)

    def message(client, userdata, msg):
        try:
            raw = msg.payload.decode("utf-8")
            if msg.topic == "frigate/available":
                activity.availability(raw == "online")
            elif msg.topic.endswith('/detect/state'):
                activity.ingest(msg.topic, raw)
            else:
                activity.ingest(msg.topic, json.loads(raw))
        except (ValueError, TypeError, AttributeError, KeyError, OverflowError):
            # Malformed messages do not kill the callback thread.
            pass

    client.on_connect, client.on_disconnect, client.on_message = connected, disconnected, message
    client.connect_async(host, port, keepalive=20)
    client.loop_start()
    return client


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--simulate", action="store_true", help="No audio or physical hardware; MQTT still real")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5050)
    parser.add_argument("--mqtt-port", type=int, default=1883)
    parser.add_argument("--input-device", type=int)
    parser.add_argument("--output-device", type=int)
    parser.add_argument("--silence", type=float, default=1.5)
    parser.add_argument("--button-address", type=lambda x: int(x, 0))
    parser.add_argument("--display", action="store_true")
    parser.add_argument("--log", type=Path, help="Optional private JSONL; never enable without participant agreement")
    args = parser.parse_args()
    if args.silence <= 0:
        parser.error("--silence must be positive")
    voice = None
    if not args.simulate:
        from voice import Voice
        voice = Voice(args.input_device, args.output_device, args.silence)
    activity = Activity()
    session = Session(activity, voice, args.log)
    mqtt_client = start_mqtt(activity, "127.0.0.1", args.mqtt_port)
    threading.Thread(target=session.worker, daemon=True).start()
    hardware = None
    hardware_thread = None
    if args.button_address is not None or args.display:
        if args.simulate:
            parser.error("Hardware flags cannot be combined with --simulate")
        from hardware import Hardware
        def hardware_error(message):
            with session.lock:
                session.error = message
        hardware = Hardware(session.trigger,
            lambda: "THINKING" if session.state == "TRANSCRIBING" else session.state,
            args.button_address, args.display, hardware_error)
        hardware_thread = threading.Thread(target=hardware.run, daemon=True)
        hardware_thread.start()
    token = os.environ.get("CAMERA_CONTROLLER_TOKEN") or secrets.token_urlsafe(24)
    print(f"Wizard controller: http://{args.host}:{args.port}/controller", flush=True)
    print(f"Controller token (keep private): {token}", flush=True)
    try:
        from waitress import serve
        serve(create_app(session, token), host=args.host, port=args.port)
    finally:
        session.stop.set()
        session.approval.set()
        if hardware:
            hardware.stop.set()
            hardware_thread.join(2)
        mqtt_client.disconnect()
        mqtt_client.loop_stop()


if __name__ == "__main__":
    main()
