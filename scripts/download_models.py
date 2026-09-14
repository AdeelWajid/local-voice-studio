"""Explicit, resumable model provisioning. No voice or script data is transmitted."""
from pathlib import Path
import sys
import os
# Standard HTTP is more reliable on constrained connections. Transfers resume.
os.environ.setdefault('HF_HUB_DISABLE_XET', '1')
from huggingface_hub import snapshot_download
from huggingface_hub import hf_hub_download

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'vendor' / 'index-tts'))

if __name__ == '__main__':
    snapshot_download('IndexTeam/IndexTTS-2.5', local_dir=ROOT / 'checkpoints', max_workers=4)
    cache = ROOT / 'checkpoints' / 'hf_cache'
    snapshot_download('facebook/w2v-bert-2.0', local_dir=cache / 'w2v-bert-2.0',
                      allow_patterns=['*.json', 'model.safetensors'], max_workers=2)
    hf_hub_download('funasr/campplus', 'campplus_cn_common.bin', local_dir=cache)
    snapshot_download('nvidia/bigvgan_v2_22khz_80band_256x', local_dir=cache / 'bigvgan',
                      allow_patterns=['config.json', 'bigvgan_generator.pt'], max_workers=2)
    print('IndexTTS 2.5 and auxiliary checkpoints are available.')
