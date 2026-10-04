import unittest
from run_pi import select_devices

class RoutingTests(unittest.TestCase):
    def setUp(self):
        self.devices = [
            {'name':'USB PnP Sound Device: Audio', 'max_input_channels':1,'max_output_channels':0},
            {'name':'UACDemoV1.0: USB Audio','max_input_channels':0,'max_output_channels':2},
            {'name':'pulse','max_input_channels':32,'max_output_channels':32}]
    def test_routes_through_shared_sink_instead_of_exclusive_hardware(self):
        self.assertEqual(select_devices(self.devices,'alsa_output.usb-UACDemoV1.0'),(0,2))
    def test_rejects_other_default_sink(self):
        with self.assertRaises(ValueError):
            select_devices(self.devices,'alsa_output.hdmi')
    def test_rejects_ambiguous_microphones(self):
        self.devices.append(dict(self.devices[0]))
        with self.assertRaises(ValueError):
            select_devices(self.devices,'alsa_output.usb-UACDemoV1.0')

if __name__=='__main__': unittest.main()
