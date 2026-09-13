import importlib.metadata
import shutil
import subprocess
import sys
from backend.config import MODEL, DATA

REQUIRED_CHECKPOINTS = (
    'config.yaml', 'gpt.pth', 's2mel.pth', 'codec.pth', 'feat1.pt', 'feat2.pt',
    'wav2vec2bert_stats.pt', 'qwen0.6bemo4-merge/config.json',
    'hf_cache/w2v-bert-2.0/config.json', 'hf_cache/w2v-bert-2.0/model.safetensors',
    'hf_cache/w2v-bert-2.0/preprocessor_config.json', 'hf_cache/campplus_cn_common.bin',
    'hf_cache/bigvgan/config.json', 'hf_cache/bigvgan/bigvgan_generator.pt',
)

def missing_checkpoints():
    return [name for name in REQUIRED_CHECKPOINTS if not (MODEL / name).is_file()]

def diagnostics():
    packages = {}
    for name in ('torch', 'torchaudio', 'transformers', 'numpy', 'soundfile', 'fastapi'):
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = None
    gpu = None
    try:
        result = subprocess.run(['nvidia-smi', '--query-gpu=name,memory.total,memory.used,driver_version',
                                 '--format=csv,noheader,nounits'],capture_output=True,text=True,timeout=5)
        if result.returncode == 0:
            name,total,used,driver = result.stdout.strip().splitlines()[0].split(', ')
            gpu = {'name':name,'total_mb':int(total),'used_mb':int(used),'driver':driver}
    except (FileNotFoundError,subprocess.TimeoutExpired,ValueError):
        pass
    return {'python':sys.version.split()[0], 'packages':packages, 'ffmpeg':bool(shutil.which('ffmpeg')),
            'gpu':gpu, 'missing_checkpoints':missing_checkpoints(), 'storage':str(DATA)}
