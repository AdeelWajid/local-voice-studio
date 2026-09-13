from pathlib import Path
import os

ROOT = Path(__file__).resolve().parent.parent
_local_root = Path(os.environ.get('LOCALAPPDATA', str(ROOT))) / 'LocalVoiceStudio'
DATA = Path(os.environ.get('VOICE_STUDIO_DATA', str(_local_root / 'data'))).resolve()
MODEL = Path(os.environ.get('VOICE_STUDIO_MODEL', str(ROOT / 'checkpoints'))).resolve()
VENDOR = ROOT / 'vendor' / 'index-tts'
MAX_UPLOAD = 50 * 1024 * 1024

def initialize_storage():
    for folder in ('voices', 'generations', 'temp', 'projects', 'exports'):
        (DATA / folder).mkdir(parents=True, exist_ok=True)
