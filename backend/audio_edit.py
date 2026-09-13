import subprocess
from pathlib import Path
from fastapi import HTTPException

def trim_audio(source: Path, target: Path, start: float, end: float):
    if start < 0 or end <= start or end - start > 3600: raise HTTPException(422, 'Choose a valid trim range.')
    result = subprocess.run(['ffmpeg','-nostdin','-v','error','-y','-ss',str(start),'-i',str(source),'-t',str(end-start),'-c','copy',str(target)],capture_output=True,timeout=120)
    if result.returncode: raise HTTPException(422, 'The audio could not be trimmed.')
