"""Launch verified USB/button hardware; restore screen ownership on exit."""
import argparse
import signal
import subprocess
import sys
from pathlib import Path


def select_devices(devices, default_sink):
    inputs = [i for i, d in enumerate(devices) if 'USB PnP Sound Device' in d['name'] and d['max_input_channels']]
    speakers = [i for i, d in enumerate(devices) if 'UACDemo' in d['name'] and d['max_output_channels']]
    shared = [i for i, d in enumerate(devices) if d['name'] == 'pulse' and d['max_output_channels']]
    if len(inputs) != 1 or len(speakers) != 1 or len(shared) != 1:
        raise ValueError('Expected one mini USB microphone, UACDemo speaker and pulse playback device')
    if 'uacdemo' not in default_sink.lower():
        raise ValueError('The shared audio default is not the USB speaker; verify routing before playback')
    return inputs[0], shared[0]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--display', action='store_true')
    args = parser.parse_args()
    import sounddevice as sd
    devices = sd.query_devices()
    try:
        sink = subprocess.check_output(['pactl','get-default-sink'], text=True, encoding='utf-8').strip()
        input_device, output_device = select_devices(devices, sink)
    except (OSError, subprocess.CalledProcessError, ValueError) as error:
        parser.error(str(error))
    root = Path(__file__).resolve().parent
    command = [sys.executable, '-u', str(root/'app.py'), '--input-device', str(input_device),
               '--output-device', str(output_device), '--button-address', '0x6f']
    restore = False
    process = None
    def stop(signum, frame):
        if process is not None and process.poll() is None:
            process.terminate()
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    try:
        if args.display:
            restore = subprocess.run(['systemctl','is-active','--quiet','piscreen.service']).returncode == 0
            if restore:
                subprocess.run(['sudo','-n','systemctl','stop','piscreen.service'], check=True)
            command.append('--display')
        process = subprocess.Popen(command, cwd=root)
        return process.wait()
    except KeyboardInterrupt:
        return 130
    finally:
        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=8)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        if restore:
            subprocess.run(['sudo','-n','systemctl','start','piscreen.service'], check=True)


if __name__ == '__main__':
    raise SystemExit(main())
