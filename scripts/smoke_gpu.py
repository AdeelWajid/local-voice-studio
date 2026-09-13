"""Real HTTP upload -> IndexTTS inference -> playable WAV gate. Run server first."""
from pathlib import Path
import argparse
import io
import time
import httpx
import soundfile as sf

parser = argparse.ArgumentParser()
parser.add_argument('reference', type=Path)
parser.add_argument('--url', default='http://127.0.0.1:8000')
args = parser.parse_args()
with httpx.Client(base_url=args.url, timeout=90) as client:
    with args.reference.open('rb') as reference:
        response = client.post('/api/voices', data={'name': 'Official example · smoke test'},
                               files={'file': ('example.wav', reference, 'audio/wav')})
    response.raise_for_status()
    voice = response.json()
    response = client.post('/api/generate', json={'text': 'Welcome to Local Voice Studio. This speech was generated entirely on this computer.',
                                                 'voice_id': voice['id'], 'language': 'EN'})
    response.raise_for_status()
    job_id = response.json()['id']
    deadline = time.monotonic() + 1200
    previous = None
    while time.monotonic() < deadline:
        response = client.get(f'/api/jobs/{job_id}')
        response.raise_for_status()
        job = response.json()
        if job['status'] != previous:
            print(job['status'], flush=True)
            previous = job['status']
        if job['status'] == 'failed':
            raise RuntimeError(job['error'])
        if job['status'] == 'completed':
            response = client.get(f'/api/jobs/{job_id}/audio')
            response.raise_for_status()
            audio, sample_rate = sf.read(io.BytesIO(response.content))
            assert len(audio) / sample_rate > 1, 'Output too short'
            assert abs(audio).max() > 0.001, 'Output silent'
            print(f"PASS: {len(audio)/sample_rate:.2f}s, {sample_rate}Hz, generation {job['elapsed']:.2f}s, job {job_id}")
            break
        time.sleep(2)
    else:
        raise TimeoutError('Real generation did not finish within 20 minutes.')
