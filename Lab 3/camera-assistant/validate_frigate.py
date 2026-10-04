"""Run inside the pinned Frigate image, without webcam devices or services."""
from pathlib import Path
import sys
sys.path.insert(0, '/opt/frigate')
from frigate.config import FrigateConfig

config = FrigateConfig.parse_yaml(Path('/config/config.yml').read_text(encoding='utf-8'))
assert config.cameras['entrance'].detect.width == 640
assert config.cameras['entrance'].detect.height == 480
assert not config.record.enabled
print('Frigate configuration validated; camera detection disabled for initial feed check.')
