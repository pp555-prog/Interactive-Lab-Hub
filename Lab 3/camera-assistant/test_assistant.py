import threading
import time
import unittest

from activity import Activity, classify
from app import Session, create_app


class EvidenceTests(unittest.TestCase):
    def test_restart_bootstraps_detection_from_real_stats(self):
        self.a.availability(False)
        self.a.availability(True)
        self.a.ingest('frigate/entrance/person', 1)
        self.a.ingest('frigate/stats', {'cameras': {'entrance': {
            'camera_fps': 5, 'detection_enabled': True}}})
        self.assertTrue(self.a.snapshot()['available'])
        self.assertEqual(self.a.answer('current'), 'The camera currently detects 1 person.')

    def test_stats_do_not_override_explicit_detection_off(self):
        self.a.ingest('frigate/entrance/detect/state', 'OFF')
        self.a.ingest('frigate/stats', {'cameras': {'entrance': {
            'camera_fps': 5, 'detection_enabled': True}}})
        self.assertFalse(self.a.snapshot()['available'])
        self.assertFalse(self.a.snapshot()['detection_enabled'])

    def setUp(self):
        self.now = 1000
        self.a = Activity(clock=lambda: self.now)
        self.a.availability(True)
        self.a.ingest('frigate/entrance/detect/state', 'ON')
        self.a.ingest('frigate/stats', {'cameras': {'entrance': {'camera_fps': 5}}})

    def event(self, ident='one', frame=1000, end=None, camera='entrance', label='person'):
        self.a.ingest('frigate/events', {'type': 'end' if end else 'update', 'after': {
            'id': ident, 'start_time': 990, 'frame_time': frame,
            'end_time': end, 'camera': camera, 'label': label}})

    def test_dedup_and_out_of_order(self):
        self.event(); self.event(frame=1001); self.event(frame=999)
        self.assertEqual(len(self.a.events), 1)
        self.assertEqual(self.a.events['one']['frame'], 1001)
        self.event(frame=1002, end=1002); self.event(frame=1003)
        self.assertEqual(self.a.events['one']['end'], 1002)

    def test_filter_and_count(self):
        self.event(camera='other'); self.event(label='car')
        self.assertEqual(len(self.a.events), 0)
        self.a.ingest('frigate/entrance/person', 0)
        self.assertEqual(self.a.answer('current'), 'No person is currently detected.')
        self.a.ingest('frigate/entrance/person', 2)
        self.assertIn('2 people', self.a.answer('current'))

    def test_stale_camera_and_connection_gap(self):
        self.now += 26
        self.assertIn('unavailable', self.a.answer('current'))
        self.a.availability(False); self.a.availability(True)
        self.assertIsNone(self.a.count)
        self.assertFalse(self.a.snapshot()['available'])

    def test_detection_disabled_is_not_empty_scene(self):
        self.a.ingest('frigate/entrance/person', 0)
        self.a.ingest('frigate/entrance/detect/state', 'OFF')
        self.assertIn('unavailable', self.a.answer('current'))

    def test_history_and_zero_fps(self):
        self.assertIn('less than five minutes', self.a.answer('recent'))
        self.event(); self.event()
        self.assertIn('1 distinct', self.a.answer('recent'))
        self.a.ingest('frigate/stats', {'cameras': {'entrance': {'camera_fps': 0}}})
        self.assertFalse(self.a.snapshot()['available'])

    def test_camera_gap_invalidates_presence_and_coverage(self):
        self.a.ingest('frigate/entrance/person', 1)
        self.now += 100
        self.a.ingest('frigate/stats', {'cameras': {'entrance': {'camera_fps': 5}}})
        self.assertIsNone(self.a.count)
        self.assertEqual(self.a.coverage, self.now)
        self.assertIn('less than five minutes', self.a.answer('recent'))

    def test_intents(self):
        for text, expected in [('Who was it?', 'identity'), ('Is anyone still in view?', 'current'),
                               ('When did you last detect a person?', 'last'),
                               ('What happened in the last five minutes?', 'recent'),
                               ('', 'unclear'), ('Turn off recording', 'unsupported')]:
            self.assertEqual(classify(text), expected)


class ControllerTests(unittest.TestCase):
    def setUp(self):
        self.session = Session(Activity())
        self.client = create_app(self.session, 'test-token').test_client()
        self.headers = {'X-Controller-Token': 'test-token'}

    def test_auth_and_public_status(self):
        self.assertEqual(self.client.get('/api/controller').status_code, 403)
        self.assertEqual(self.client.post('/api/trigger', json={}).status_code, 403)
        self.assertEqual(self.client.get('/api/status').json, {'state': 'IDLE'})
        self.assertNotIn('test-token', self.client.get('/controller').get_data(as_text=True))

    def test_busy_and_stale_approval(self):
        r = self.client.post('/api/trigger', json={'text': 'Is anyone in view?'}, headers=self.headers)
        self.assertEqual(r.status_code, 202)
        self.assertEqual(self.client.post('/api/trigger', json={'text': 'another'}, headers=self.headers).status_code, 409)
        self.session.state = 'THINKING'
        self.assertEqual(self.client.post('/api/approve', json={'turn_id': 99, 'reply': 'No.'}, headers=self.headers).status_code, 409)
        self.assertEqual(self.client.post('/api/approve', json={'turn_id': 1, 'reply': 'No person detected.'}, headers=self.headers).status_code, 200)
        self.assertEqual(self.client.post('/api/approve', json={'turn_id': 1, 'reply': 'Again'}, headers=self.headers).status_code, 409)

    def test_worker_turn(self):
        thread = threading.Thread(target=self.session.worker, daemon=True)
        thread.start()
        self.assertTrue(self.session.trigger('Who was it?'))
        limit = time.monotonic() + 2
        while self.session.state != 'THINKING' and time.monotonic() < limit:
            time.sleep(.01)
        self.assertEqual(self.session.turn['intent'], 'identity')
        self.assertTrue(self.session.approve(1, self.session.activity.answer('identity')))
        limit = time.monotonic() + 2
        while self.session.state != 'IDLE' and time.monotonic() < limit:
            time.sleep(.01)
        self.assertEqual(self.session.turn['outcome'], 'simulated_reply')
        self.session.stop.set(); self.session.approval.set(); thread.join(1)

    def test_voice_worker_states_and_capture_failure(self):
        owner = self
        class FakeVoice:
            def say(self, text):
                owner.assertIn(owner.session.state, ('PREPARING', 'SPEAKING'))
                return time.monotonic()
            def listen(self, stop):
                owner.assertEqual(owner.session.state, 'LISTENING')
                raise RuntimeError('microphone unavailable')
        self.session.voice = FakeVoice()
        thread = threading.Thread(target=self.session.worker, daemon=True)
        thread.start()
        self.assertTrue(self.session.trigger())
        limit = time.monotonic() + 2
        while self.session.state != 'IDLE' and time.monotonic() < limit:
            time.sleep(.01)
        self.assertEqual(self.session.state, 'IDLE')
        self.assertIn('microphone unavailable', self.session.error)
        self.session.stop.set(); self.session.approval.set(); thread.join(1)


if __name__ == '__main__':
    unittest.main()
