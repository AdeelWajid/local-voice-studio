#!/usr/bin/env python3
"""Explicit, resumable model provisioning. No voice or script data is transmitted."""
from pathlib import Path
import os
import sys

ROOT = Path(__file__).resolve().parent.parent
VENDOR = ROOT / 'vendor' / 'index-tts'

def studio_python():
    if sys.platform == 'win32':
        return VENDOR / '.venv' / 'Scripts' / 'python.exe'
    return VENDOR / '.venv' / 'bin' / 'python'

def ensure_studio_python():
    target = studio_python()
    if not target.is_file():
        sys.exit('Run ./scripts/install.sh first, then retry this command.')
    current = Path(sys.executable).resolve()
    if current != target.resolve() and current.parent != target.parent:
        os.execv(str(target), [str(target), str(Path(__file__).resolve()), *sys.argv[1:]])

if __name__ == '__main__':
    ensure_studio_python()
    # Standard HTTP is more reliable on constrained connections. Transfers resume.
    os.environ.setdefault('HF_HUB_DISABLE_XET', '1')
    sys.path.insert(0, str(VENDOR))
    from huggingface_hub import snapshot_download, hf_hub_download
    snapshot_download('IndexTeam/IndexTTS-2.5', local_dir=ROOT / 'checkpoints', max_workers=4)
    cache = ROOT / 'checkpoints' / 'hf_cache'
    snapshot_download('facebook/w2v-bert-2.0', local_dir=cache / 'w2v-bert-2.0',
                      allow_patterns=['*.json', 'model.safetensors'], max_workers=2)
    hf_hub_download('funasr/campplus', 'campplus_cn_common.bin', local_dir=cache)
    snapshot_download('nvidia/bigvgan_v2_22khz_80band_256x', local_dir=cache / 'bigvgan',
                      allow_patterns=['config.json', 'bigvgan_generator.pt'], max_workers=2)
    print('IndexTTS 2.5 and auxiliary checkpoints are available.')
