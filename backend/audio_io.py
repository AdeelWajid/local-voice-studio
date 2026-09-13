import subprocess
from pathlib import Path
import soundfile as sf
from fastapi import HTTPException

def decode_reference(source: Path, target: Path):
    try:
        result = subprocess.run([
            'ffmpeg', '-nostdin', '-v', 'error', '-y', '-i', str(source),
            '-t', '61', '-ac', '1', '-ar', '24000', '-c:a', 'pcm_s16le', str(target)
        ], capture_output=True, timeout=60)
    except FileNotFoundError:
        raise HTTPException(503, 'FFmpeg was not found. Install it and add it to PATH.')
    except subprocess.TimeoutExpired:
        raise HTTPException(422, 'The recording took too long to decode.')
    if result.returncode:
        raise HTTPException(422, 'The recording could not be decoded. Choose a valid audio file.')
    info = sf.info(target)
    if not 3 <= info.duration <= 60:
        raise HTTPException(422, 'Use a recording between 3 and 60 seconds; 5–15 seconds is recommended.')
    return info.duration
