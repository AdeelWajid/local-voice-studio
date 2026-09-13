import asyncio
import json
import subprocess
import numpy as np
import soundfile as sf
import shutil
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import uuid4
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.responses import JSONResponse
from backend.config import DATA, ROOT, MAX_UPLOAD, initialize_storage
from backend.database import connection, initialize_database
from backend.audio_io import decode_reference
from backend.engine import engine
from backend.jobs import jobs, now
from backend.audio_edit import trim_audio
from backend.enhancement import enhance
from backend.presets import list_presets, save_preset
from backend.schemas import GenerateRequest
from backend.diagnostics import diagnostics, missing_checkpoints
from backend.logging_setup import configure_logging

@asynccontextmanager
async def lifespan(app):
    initialize_storage()
    initialize_database()
    configure_logging().info('Application started')
    jobs.start()
    yield

app = FastAPI(title='Local Voice Studio', lifespan=lifespan)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=['127.0.0.1', 'localhost', 'testserver'])

@app.middleware('http')
async def local_origin_only(request, call_next):
    origin = request.headers.get('origin')
    if origin and origin not in {'http://127.0.0.1:8000', 'http://localhost:8000',
                                  'http://127.0.0.1:5173', 'http://localhost:5173'}:
        return JSONResponse({'detail': 'Requests must originate from the local studio.'}, status_code=403)
    return await call_next(request)

@app.get('/api/system/model')
def model_status():
    return {'state': engine.state, 'error': engine.error, 'model': 'IndexTTS 2.5',
            'checkpoints_ready': not missing_checkpoints(),
            'languages': {'EN': 'English', 'ZH': 'Chinese', 'JA': 'Japanese', 'ES': 'Spanish', 'AR': 'Arabic'}}

@app.get('/api/system/diagnostics')
def system_diagnostics():
    return diagnostics()

@app.get('/api/voices')
def list_voices():
    with connection() as db:
        return [dict(v) for v in db.execute('SELECT * FROM voices ORDER BY created DESC')]

@app.get('/api/emotion-references')
def list_emotion_references():
    with connection() as db:
        return [dict(v) for v in db.execute('SELECT * FROM emotion_refs ORDER BY created DESC')]

@app.post('/api/emotion-references', status_code=201)
async def upload_emotion_reference(name: str = Form(...), file: UploadFile = File(...)):
    name = name.strip()
    if not name: raise HTTPException(422, 'Enter an emotion reference name.')
    ref_id = str(uuid4()); folder = DATA / 'voices' / 'emotion' / ref_id; folder.mkdir(parents=True)
    original = folder / ('original' + Path(file.filename or 'audio').suffix.lower())
    reference = folder / 'reference.wav'
    try:
        with original.open('wb') as target:
            size = 0
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                if size > MAX_UPLOAD: raise HTTPException(413, 'The maximum recording size is 50 MB.')
                target.write(chunk)
        duration = await run_in_threadpool(decode_reference, original, reference)
        result = {'id':ref_id,'name':name,'reference':str(reference.relative_to(DATA)),'duration':duration,'created':now()}
        with connection() as db: db.execute('INSERT INTO emotion_refs VALUES(:id,:name,:reference,:duration,:created)', result)
        return result
    except Exception:
        shutil.rmtree(folder, ignore_errors=True); raise
    finally: await file.close()

@app.post('/api/voices', status_code=201)
async def upload_voice(name: str = Form(...), file: UploadFile = File(...)):
    name = name.strip()
    if not 1 <= len(name) <= 100:
        raise HTTPException(422, 'Enter a voice name between 1 and 100 characters.')
    suffix = Path(file.filename or '').suffix.lower()
    if suffix not in {'.wav', '.mp3', '.flac', '.m4a', '.ogg', '.webm'}:
        raise HTTPException(422, 'Choose WAV, MP3, FLAC, M4A, OGG or WebM audio.')
    if file.content_type and not (file.content_type.startswith('audio/') or file.content_type in {'video/webm','video/mp4','application/octet-stream'}):
        raise HTTPException(422, 'The uploaded file must be audio.')
    voice_id = str(uuid4())
    folder = DATA / 'voices' / voice_id
    folder.mkdir()
    original, reference = folder / f'original{suffix}', folder / 'reference.wav'
    try:
        size = 0
        with original.open('wb') as target:
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                if size > MAX_UPLOAD:
                    raise HTTPException(413, 'The maximum recording size is 50 MB.')
                target.write(chunk)
        duration = await run_in_threadpool(decode_reference, original, reference)
        result = {'id': voice_id, 'name': name, 'original': str(original.relative_to(DATA)),
                  'reference': str(reference.relative_to(DATA)), 'duration': duration, 'created': now()}
        with connection() as db:
            db.execute('INSERT INTO voices VALUES(:id,:name,:original,:reference,:duration,:created)', result)
        return result
    except Exception:
        shutil.rmtree(folder)
        raise
    finally:
        await file.close()

@app.get('/api/voices/{voice_id}/audio')
def voice_audio(voice_id: str):
    with connection() as db:
        row = db.execute('SELECT reference FROM voices WHERE id=?', (voice_id,)).fetchone()
    if not row:
        raise HTTPException(404, 'Voice not found.')
    return FileResponse(DATA / row['reference'], media_type='audio/wav')

@app.post('/api/generate', status_code=202)
def generate(request: GenerateRequest):
    with connection() as db:
        if not db.execute('SELECT id FROM voices WHERE id=?', (request.voice_id,)).fetchone():
            raise HTTPException(422, 'Choose an existing voice profile.')
    try:
        return {'id': jobs.submit(request)}
    except ValueError as exc:
        raise HTTPException(429, str(exc))

@app.post('/api/generate/batch', status_code=202)
def generate_batch(payload: dict):
    requests = payload.get('requests', [])
    if not isinstance(requests, list) or not 1 <= len(requests) <= 10: raise HTTPException(422, 'Batch size must be between 1 and 10.')
    ids=[]
    for item in requests:
        try: ids.append(jobs.submit(GenerateRequest.model_validate(item)))
        except Exception as exc: raise HTTPException(422, str(exc))
    return {'ids':ids}

@app.post('/api/generate/segments', status_code=202)
def generate_segments(payload: dict):
    """Queue timeline segments; each segment may use a different saved speaker."""
    segments = payload.get('segments', [])
    if not isinstance(segments, list) or not 1 <= len(segments) <= 50:
        raise HTTPException(422, 'Timeline must contain between 1 and 50 segments.')
    ids = []
    for index, item in enumerate(segments):
        try:
            request = GenerateRequest.model_validate(item)
            with connection() as db:
                if not db.execute('SELECT id FROM voices WHERE id=?', (request.voice_id,)).fetchone():
                    raise ValueError(f'Segment {index + 1}: choose an existing voice profile.')
            ids.append(jobs.submit(request))
        except Exception as exc:
            raise HTTPException(422, str(exc))
    return {'ids': ids}

@app.get('/api/jobs')
def list_jobs():
    with connection() as db:
        return [dict(row) for row in db.execute('SELECT * FROM jobs ORDER BY created DESC LIMIT 100')]

@app.get('/api/projects')
def list_projects():
    with connection() as db: return [dict(row) for row in db.execute('SELECT * FROM projects ORDER BY updated DESC')]

@app.post('/api/projects', status_code=201)
def create_project(payload: dict):
    name = str(payload.get('name','')).strip()
    if not name: raise HTTPException(422, 'Enter a project name.')
    project = {'id':str(uuid4()),'name':name,'script':str(payload.get('script',''))[:20000], 'settings':json.dumps(payload.get('settings',{})), 'updated':now()}
    with connection() as db: db.execute('INSERT INTO projects VALUES(:id,:name,:script,:settings,:updated)', project)
    return project

@app.put('/api/projects/{project_id}')
def update_project(project_id: str, payload: dict):
    with connection() as db:
        if not db.execute('SELECT id FROM projects WHERE id=?',(project_id,)).fetchone(): raise HTTPException(404,'Project not found.')
        db.execute('UPDATE projects SET name=?,script=?,settings=?,updated=? WHERE id=?',(str(payload.get('name','Untitled'))[:100],str(payload.get('script',''))[:20000],json.dumps(payload.get('settings',{})),now(),project_id))
        return dict(db.execute('SELECT * FROM projects WHERE id=?',(project_id,)).fetchone())

@app.post('/api/audio/trim')
def trim_endpoint(payload: dict):
    job = get_job(str(payload.get('job_id','')))
    if job['status'] != 'completed': raise HTTPException(409,'Audio is not ready yet.')
    target = DATA / 'generations' / f"{job['id']}-trim.wav"
    trim_audio(DATA / job['audio'], target, float(payload.get('start',0)), float(payload.get('end',0)))
    return {'audio':str(target.relative_to(DATA)),'url':f"/api/audio/file/{target.name}"}

@app.post('/api/audio/enhance')
def enhance_endpoint(payload: dict):
    job=get_job(str(payload.get('job_id','')))
    if job['status']!='completed': raise HTTPException(409,'Audio is not ready yet.')
    target=DATA/'generations'/f"{job['id']}-enhanced.wav"; enhance(DATA/job['audio'],target,payload.get('settings',{}))
    return {'audio':str(target.relative_to(DATA)),'url':f"/api/audio/file/{target.name}"}

@app.post('/api/audio/concat')
def concat_audio(payload: dict):
    """Join completed segment jobs with a configurable silence gap."""
    ids = payload.get('job_ids', []); gap = float(payload.get('gap', 0.25))
    if not isinstance(ids, list) or not 1 <= len(ids) <= 50 or not 0 <= gap <= 10:
        raise HTTPException(422, 'Choose 1–50 jobs and a gap from 0 to 10 seconds.')
    sources = []
    for job_id in ids:
        row = get_job(str(job_id))
        if row['status'] != 'completed' or not row['audio']: raise HTTPException(409, 'All segments must be completed.')
        sources.append(DATA / row['audio'])
    target = DATA / 'generations' / f"timeline-{uuid4()}.wav"
    inputs = []
    for source in sources: inputs += ['-i', str(source)]
    filters = ''.join(f'[{i}:a]' for i in range(len(sources)))
    if gap:
        filters += f"aevalsrc=0:d={gap}:s=22050:c=mono[sil];[0:a]"
        # Build a concat filter with silence pads between each segment.
        parts = []
        for i in range(len(sources)):
            parts.append(f'[{i}:a]')
            if i < len(sources)-1: parts.append(f'silence{i}')
        silence = ''.join(f'anullsrc=r=22050:cl=mono:d={gap}[silence{i}];' for i in range(len(sources)-1))
        graph = silence + ''.join(parts) + f'concat=n={len(sources)*2-1}:v=0:a=1[out]'
    else:
        graph = ''.join(f'[{i}:a]' for i in range(len(sources))) + f'concat=n={len(sources)}:v=0:a=1[out]'
    result = subprocess.run(['ffmpeg','-nostdin','-v','error','-y',*inputs,'-filter_complex',graph,'-map','[out]','-ar','22050','-ac','1',str(target)],capture_output=True,timeout=300)
    if result.returncode: raise HTTPException(422, 'The timeline could not be assembled.')
    return {'audio': str(target.relative_to(DATA)), 'url': f'/api/audio/file/{target.name}'}

@app.get('/api/presets')
def get_presets(): return list_presets()

@app.post('/api/presets',status_code=201)
def create_preset(payload: dict): return save_preset(payload)

@app.get('/api/audio/file/{filename}')
def edited_audio(filename: str):
    if '/' in filename or '\\' in filename or not filename.endswith('.wav'): raise HTTPException(404,'Audio not found.')
    target = DATA / 'generations' / filename
    if not target.is_file(): raise HTTPException(404,'Audio not found.')
    return FileResponse(target, media_type='audio/wav')

@app.get('/api/jobs/{job_id}/export/{format}')
def export_audio(job_id: str, format: str):
    job=get_job(job_id)
    if job['status']!='completed': raise HTTPException(409,'Audio is not ready yet.')
    if format not in {'wav','flac','mp3'}: raise HTTPException(422,'Supported exports are WAV, FLAC and MP3.')
    source=DATA/job['audio']; target=DATA/'exports'/f'{job_id}.{format}'; target.parent.mkdir(parents=True,exist_ok=True)
    codec={'wav':['-c:a','pcm_s16le'],'flac':['-c:a','flac'],'mp3':['-c:a','libmp3lame','-b:a','192k']}[format]
    result=subprocess.run(['ffmpeg','-nostdin','-v','error','-y','-i',str(source),*codec,str(target)],capture_output=True,timeout=180)
    if result.returncode: raise HTTPException(422,'Audio export failed.')
    return FileResponse(target,media_type={'wav':'audio/wav','flac':'audio/flac','mp3':'audio/mpeg'}[format],filename=target.name)

@app.get('/api/jobs/{job_id}')
def get_job(job_id: str):
    with connection() as db:
        row = db.execute('SELECT * FROM jobs WHERE id=?', (job_id,)).fetchone()
    if not row:
        raise HTTPException(404, 'Generation not found.')
    return dict(row)

@app.post('/api/jobs/{job_id}/cancel')
def cancel_job(job_id: str):
    get_job(job_id)
    jobs.cancel(job_id)
    return {'status': 'cancelled', 'message': 'A running model call finishes before its output is discarded.'}

@app.get('/api/jobs/{job_id}/audio')
def job_audio(job_id: str):
    row = get_job(job_id)
    if row['status'] != 'completed' or not row['audio']:
        raise HTTPException(409, 'Audio is not ready yet.')
    return FileResponse(DATA / row['audio'], media_type='audio/wav', filename=f'take-{job_id[:8]}.wav')

@app.get('/api/jobs/{job_id}/waveform')
def job_waveform(job_id: str, bins: int = 160):
    row=get_job(job_id)
    if row['status']!='completed' or not row['audio']: raise HTTPException(409,'Audio is not ready yet.')
    bins=max(16,min(800,bins)); audio,sr=sf.read(DATA/row['audio'],always_2d=True); mono=np.max(np.abs(audio),axis=1)
    edges=np.linspace(0,len(mono),bins+1,dtype=int); peaks=[float(mono[edges[i]:edges[i+1]].max()) if edges[i]<edges[i+1] else 0.0 for i in range(bins)]
    return {'peaks':peaks,'duration':len(mono)/sr,'sample_rate':sr}

@app.websocket('/ws/jobs')
async def websocket_jobs(socket: WebSocket):
    origin = socket.headers.get('origin')
    if origin and origin not in {'http://127.0.0.1:8000', 'http://localhost:8000',
                                  'http://127.0.0.1:5173', 'http://localhost:5173'}:
        await socket.close(code=1008)
        return
    await socket.accept()
    try:
        previous = None
        while True:
            payload = {'jobs': await run_in_threadpool(list_jobs), 'model': model_status()}
            if payload != previous:
                await socket.send_json(payload)
                previous = payload
            await asyncio.sleep(1)
    except (WebSocketDisconnect, RuntimeError):
        pass

if (ROOT / 'frontend' / 'dist').is_dir():
    app.mount('/', StaticFiles(directory=ROOT / 'frontend' / 'dist', html=True), name='frontend')
