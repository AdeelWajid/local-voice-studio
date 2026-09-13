import io
import os
import tempfile
from pathlib import Path
import numpy as np
import pytest
import soundfile as sf

_temporary = tempfile.TemporaryDirectory(prefix='voice-studio-tests-')
os.environ['VOICE_STUDIO_DATA'] = _temporary.name
from fastapi.testclient import TestClient
from backend.main import app
from backend.config import DATA
from backend.schemas import GenerateRequest

@pytest.fixture(scope='module')
def client():
    with TestClient(app) as value:
        yield value

def recording(seconds=5):
    buffer = io.BytesIO()
    sr = 24000
    signal = .2 * np.sin(2 * np.pi * 220 * np.arange(int(seconds * sr)) / sr)
    sf.write(buffer, signal, sr, format='WAV')
    return buffer.getvalue()

def test_blank_script_and_unsupported_language():
    with pytest.raises(ValueError):
        GenerateRequest(text='  ', voice_id='x')
    with pytest.raises(ValueError):
        GenerateRequest(text='hello', voice_id='x', language='UR')

def test_reference_upload_preserves_original(client):
    original = recording()
    response = client.post('/api/voices', data={'name':'Test Voice'}, files={'file':('../../escape.wav',original,'audio/wav')})
    assert response.status_code == 201, response.text
    voice = response.json()
    assert 4.9 < voice['duration'] < 5.1
    assert (DATA / voice['original']).read_bytes() == original
    assert (DATA / voice['reference']).resolve().is_relative_to(DATA.resolve())
    assert voice['original'] != voice['reference']
    assert client.get('/api/voices').json()[0]['id'] == voice['id']
    preview = client.get(f"/api/voices/{voice['id']}/audio")
    assert preview.status_code == 200
    assert sf.info(io.BytesIO(preview.content)).samplerate == 24000

@pytest.mark.parametrize('filename,content,mime',[
    ('bad.wav',b'not audio','audio/wav'),
    ('bad.exe',b'not audio','application/octet-stream'),
    ('bad.wav',b'not audio','text/html'),
], ids=['decode-error','extension-error','mime-error'])
def test_invalid_upload_cleans_temporary_directory(client,filename,content,mime):
    before = set((DATA/'voices').iterdir())
    response = client.post('/api/voices',data={'name':'Invalid'},files={'file':(filename,content,mime)})
    assert response.status_code == 422
    assert set((DATA/'voices').iterdir()) == before

def test_short_upload_is_rejected(client):
    before = set((DATA/'voices').iterdir())
    response = client.post('/api/voices', data={'name':'Short'}, files={'file':('short.wav',recording(.25),'audio/wav')})
    assert response.status_code == 422
    assert set((DATA/'voices').iterdir()) == before

def test_missing_voice_does_not_queue(client):
    response = client.post('/api/generate',json={'text':'Hello','voice_id':'absent'})
    assert response.status_code == 422
    assert client.get('/api/jobs').json() == []

def test_serialization_keeps_unicode_and_punctuation():
    request = GenerateRequest(text='Hello… “world”!\nこんにちは。',voice_id='v')
    assert GenerateRequest.model_validate_json(request.model_dump_json()) == request

def test_missing_audio_returns_actionable_error(client):
    response = client.get('/api/jobs/missing/audio')
    assert response.status_code == 404
    assert response.json()['detail'] == 'Generation not found.'

def test_external_websites_cannot_read_local_voices(client):
    assert client.get('/api/voices', headers={'origin':'https://example.com'}).status_code == 403
    assert client.get('/api/voices', headers={'host':'example.com'}).status_code == 400
