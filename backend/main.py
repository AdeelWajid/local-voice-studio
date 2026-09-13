import asyncio
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

@app.get('/api/jobs')
def list_jobs():
    with connection() as db:
        return [dict(row) for row in db.execute('SELECT * FROM jobs ORDER BY created DESC LIMIT 100')]

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
