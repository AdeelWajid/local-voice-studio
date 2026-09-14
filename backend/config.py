from pathlib import Path
import os
import sys

ROOT = Path(__file__).resolve().parent.parent
VENDOR = ROOT / 'vendor' / 'index-tts'
MAX_UPLOAD = 50 * 1024 * 1024

def default_data_dir(*, platform=None, home=None, localappdata=None, xdg_data_home=None):
    """Platform-native studio data directory, overridable with VOICE_STUDIO_DATA."""
    platform = sys.platform if platform is None else platform
    home = Path.home() if home is None else Path(home)
    if platform == 'darwin':
        return home / 'Library' / 'Application Support' / 'LocalVoiceStudio' / 'data'
    if platform == 'win32':
        root = Path(localappdata or os.environ.get('LOCALAPPDATA') or (home / 'AppData' / 'Local'))
        return root / 'LocalVoiceStudio' / 'data'
    xdg = Path(xdg_data_home or os.environ.get('XDG_DATA_HOME') or (home / '.local' / 'share'))
    return xdg / 'LocalVoiceStudio' / 'data'

def studio_python(*, platform=None):
    platform = sys.platform if platform is None else platform
    if platform == 'win32':
        return VENDOR / '.venv' / 'Scripts' / 'python.exe'
    return VENDOR / '.venv' / 'bin' / 'python'

DATA = Path(os.environ.get('VOICE_STUDIO_DATA', str(default_data_dir()))).resolve()
MODEL = Path(os.environ.get('VOICE_STUDIO_MODEL', str(ROOT / 'checkpoints'))).resolve()

def initialize_storage():
    for folder in ('voices', 'generations', 'temp', 'projects', 'exports'):
        (DATA / folder).mkdir(parents=True, exist_ok=True)
