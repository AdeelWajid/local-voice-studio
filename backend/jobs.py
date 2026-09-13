import json
import queue
import threading
import time
import logging
from datetime import datetime, timezone
from uuid import uuid4
import soundfile as sf
from backend.config import DATA
from backend.database import connection
from backend.engine import engine
from backend.schemas import GenerateRequest

def now():
    return datetime.now(timezone.utc).isoformat()

class GenerationQueue:
    def __init__(self):
        self.pending = queue.Queue(maxsize=100)
        self.worker = None

    def start(self):
        self.worker = threading.Thread(target=self.run, name='gpu-worker', daemon=True)
        self.worker.start()

    def submit(self, request):
        job_id = str(uuid4())
        with connection() as db:
            db.execute('INSERT INTO jobs(id,status,request,created) VALUES(?,?,?,?)',
                       (job_id, 'queued', request.model_dump_json(), now()))
        try:
            self.pending.put_nowait(job_id)
        except queue.Full:
            with connection() as db:
                db.execute('DELETE FROM jobs WHERE id=?', (job_id,))
            raise ValueError('The generation queue is full. Wait for an existing job to finish.')
        return job_id

    def run(self):
        while True:
            job_id = self.pending.get()
            output = DATA / 'generations' / f'{job_id}.wav'
            try:
                with connection() as db:
                    row = db.execute('SELECT * FROM jobs WHERE id=?', (job_id,)).fetchone()
                    if not row or row['status'] != 'queued':
                        continue
                    request = GenerateRequest.model_validate_json(row['request'])
                    voice = db.execute('SELECT * FROM voices WHERE id=?', (request.voice_id,)).fetchone()
                    changed = db.execute("UPDATE jobs SET status='generating' WHERE id=? AND status='queued'", (job_id,))
                    if not changed.rowcount:
                        continue
                started = time.monotonic()
                logging.getLogger('voice_studio').info('Generation started %s',job_id)
                engine.generate(request, DATA / voice['reference'], output)
                info = sf.info(output)
                with connection() as db:
                    changed = db.execute("UPDATE jobs SET status='completed',audio=?,elapsed=?,duration=? WHERE id=? AND status='generating'",
                               (str(output.relative_to(DATA)), time.monotonic()-started, info.duration, job_id))
                    if not changed.rowcount:
                        output.unlink(missing_ok=True)
                logging.getLogger('voice_studio').info('Generation finished %s',job_id)
            except Exception as exc:
                logging.getLogger('voice_studio').error('Generation failed %s %s',job_id,type(exc).__name__)
                output.unlink(missing_ok=True)
                with connection() as db:
                    db.execute("UPDATE jobs SET status='failed',error=? WHERE id=? AND status!='cancelled'", (str(exc), job_id))
            finally:
                self.pending.task_done()

    def cancel(self, job_id):
        with connection() as db:
            db.execute("UPDATE jobs SET status='cancelled' WHERE id=? AND status IN ('queued','generating')", (job_id,))

jobs = GenerationQueue()
