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

def _nvidia_gpu():
    try:
        result = subprocess.run(['nvidia-smi', '--query-gpu=name,memory.total,memory.used,driver_version',
                                 '--format=csv,noheader,nounits'],capture_output=True,text=True,timeout=5)
        if result.returncode == 0:
            name,total,used,driver = result.stdout.strip().splitlines()[0].split(', ')
            return {'backend':'cuda','name':name,'total_mb':int(total),'used_mb':int(used),'driver':driver}
    except (FileNotFoundError,subprocess.TimeoutExpired,ValueError):
        pass
    return None

def _apple_gpu():
    name = 'Apple GPU (Metal)'
    total_mb = None
    try:
        brand = subprocess.run(['sysctl','-n','machdep.cpu.brand_string'],capture_output=True,text=True,timeout=3)
        if brand.returncode == 0 and brand.stdout.strip():
            name = f'Apple Silicon ({brand.stdout.strip()})'
    except (FileNotFoundError,subprocess.TimeoutExpired):
        pass
    try:
        memory = subprocess.run(['sysctl','-n','hw.memsize'],capture_output=True,text=True,timeout=3)
        if memory.returncode == 0:
            total_mb = int(memory.stdout.strip()) // (1024 * 1024)
    except (FileNotFoundError,subprocess.TimeoutExpired,ValueError):
        pass
    return {'backend':'mps','name':name,'total_mb':total_mb,'used_mb':None,'driver':None}

def accelerator():
    gpu = {'backend':None,'name':None,'total_mb':None,'used_mb':None,'driver':None}
    try:
        import torch
    except ImportError:
        nvidia = _nvidia_gpu()
        return nvidia or gpu
    if torch.cuda.is_available():
        nvidia = _nvidia_gpu()
        if nvidia:
            return nvidia
        return {'backend':'cuda','name':torch.cuda.get_device_name(0),
                'total_mb':torch.cuda.get_device_properties(0).total_memory // (1024 * 1024),
                'used_mb':None,'driver':None}
    mps = getattr(torch.backends, 'mps', None)
    if mps is not None and mps.is_available():
        return _apple_gpu()
    gpu['backend'] = 'cpu'
    gpu['name'] = 'CPU'
    return gpu

def diagnostics():
    packages = {}
    for name in ('torch', 'torchaudio', 'transformers', 'numpy', 'soundfile', 'fastapi'):
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = None
    return {'python':sys.version.split()[0], 'packages':packages, 'ffmpeg':bool(shutil.which('ffmpeg')),
            'gpu':accelerator(), 'missing_checkpoints':missing_checkpoints(), 'storage':str(DATA)}
