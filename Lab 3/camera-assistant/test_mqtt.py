"""Opt-in broker integration with SYNTHETIC events, never participant evidence.

Run only with this project's broker running and Frigate stopped:
RUN_MQTT_TEST=1 ../.venv/bin/python -m unittest -v test_mqtt.py
"""
import json
import os
import time
import unittest

from activity import Activity
from app import start_mqtt


@unittest.skipUnless(os.environ.get('RUN_MQTT_TEST') == '1', 'requires isolated test broker')
class BrokerIntegration(unittest.TestCase):
    def test_message_delivery_and_disconnect(self):
        import paho.mqtt.client as mqtt
        evidence = Activity()
        subscriber = start_mqtt(evidence, '127.0.0.1', 1883)
        publisher = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        publisher.connect('127.0.0.1', 1883)
        publisher.loop_start()
        try:
            # Repeat availability until subscriptions have completed.
            limit = time.monotonic() + 5
            while not evidence.online and time.monotonic() < limit:
                publisher.publish('frigate/available', 'online').wait_for_publish()
                time.sleep(.1)
            self.assertTrue(evidence.online)
            publisher.publish('frigate/entrance/detect/state', 'ON').wait_for_publish()
            now = time.time()
            messages = {
                'frigate/stats': {'cameras': {'entrance': {'camera_fps': 5}}},
                'frigate/entrance/person': 1,
                'frigate/events': {'type': 'new', 'after': {'id': 'synthetic-test-event',
                    'camera': 'entrance', 'label': 'person', 'start_time': now,
                    'frame_time': now, 'end_time': None}},
            }
            for topic, data in messages.items():
                publisher.publish(topic, json.dumps(data)).wait_for_publish()
            limit = time.monotonic() + 5
            while len(evidence.events) != 1 and time.monotonic() < limit:
                time.sleep(.02)
            self.assertTrue(evidence.snapshot()['available'])
            self.assertEqual(evidence.count, 1)
            self.assertEqual(len(evidence.events), 1)
            subscriber.disconnect()
            limit = time.monotonic() + 2
            while evidence.online and time.monotonic() < limit:
                time.sleep(.02)
            self.assertFalse(evidence.snapshot()['available'])
        finally:
            subscriber.disconnect(); subscriber.loop_stop()
            publisher.disconnect(); publisher.loop_stop()


if __name__ == '__main__':
    unittest.main()
