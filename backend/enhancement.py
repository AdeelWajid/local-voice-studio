from pathlib import Path
import subprocess
from fastapi import HTTPException

def enhance(source: Path, target: Path, settings: dict):
    filters=[]
    if settings.get('highpass'): filters.append(f"highpass=f={float(settings['highpass'])}")
    if settings.get('denoise'): filters.append('afftdn=nf=-25')
    if settings.get('normalize'): filters.append('loudnorm=I=-16:TP=-1.5:LRA=11')
    if settings.get('compressor'): filters.append('acompressor=threshold=-18dB:ratio=3:attack=20:release=150')
    args=['ffmpeg','-nostdin','-v','error','-y','-i',str(source)]
    if filters: args += ['-af',','.join(filters)]
    args += ['-c:a','pcm_s16le',str(target)]
    result=subprocess.run(args,capture_output=True,timeout=180)
    if result.returncode: raise HTTPException(422,'Audio enhancement failed.')
