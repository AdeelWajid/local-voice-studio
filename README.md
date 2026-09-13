# Local Voice Studio

A local Windows speech studio using React, TypeScript, FastAPI and the official IndexTTS 2.5 engine. No cloud TTS service or account is required.

**Development status:** Phase 1 is under construction. Real GPU inference has not yet passed its verification gate. Later emotion, editor, enhancement, project and batch features are not implemented yet. See [the specification](docs/SPECIFICATION.md) and [progress](docs/PROGRESS.md).

## Requirements

- Windows 11, NVIDIA GPU (target: RTX 5060 Ti 16 GB), current driver and sufficient free disk space for model weights and CUDA dependencies.
- Git, uv, Node.js/npm and FFmpeg on PATH.
- Python 3.11.9 is installed separately by the installer.

## Install and start

```powershell
.\scripts\install.ps1 -DownloadModels
.\start.ps1
```

The installer uses official upstream revision `ee40fa7d6c6b8a2c7f06105f9f1e65775b74868c` and its frozen dependency lock, including PyTorch 2.8/CUDA 12.8, Transformers 4.52.1 and NumPy 2.2.6. It does not install unrelated system software. Model downloads require internet access and resume on subsequent runs. Voice files and scripts are never sent to a model service.

The production interface is served at http://127.0.0.1:8000. For development use `start.ps1 -Dev` (Vite at localhost:5173). Backend and model run in one process; do not use multiple Uvicorn workers or reload while generating.

## Basic workflow

1. Choose **Add a voice**, name it and upload a clean recording. Use only voices you own or have permission to use.
2. Select the voice and enter your script. The original recording remains separate from the mono 24 kHz inference reference.
3. Choose the script language: English, Chinese, Japanese, Spanish or Arabic. Urdu and Hindi are not supported by the official 2.5 release.
4. Set the eight IndexTTS emotion dimensions, emotion strength, and speaking speed. The values are sent to the model as `emo_vector`, `emo_alpha`, and `duration_factor`; they are not decorative controls.
5. Select **Generate speech** or press Ctrl+Enter. The first request loads the model; later requests reuse it.
5. Play the output or download the original WAV.

The script autosaves in this browser. Voice and generation metadata are stored in SQLite under `%LOCALAPPDATA%/LocalVoiceStudio/data`, with audio in separate UUID directories. This keeps private recordings outside this project's OneDrive-synced workspace. Set `VOICE_STUDIO_DATA` to override storage. The current first-phase limit is 2,000 characters and references of 3–60 seconds (5–15 recommended).

Cancellation prevents queued work and discards output from an active model call after it finishes. It does not forcibly interrupt a CUDA kernel.

## Checks

```powershell
cd frontend
npm.cmd run build
cd ..
vendor/index-tts/.venv/Scripts/python.exe -m pytest backend/tests
vendor/index-tts/.venv/Scripts/python.exe scripts/smoke_gpu.py path/to/reference.wav
```

The GPU smoke test requires the server and complete checkpoints, uploads the reference, generates actual speech and validates a non-silent WAV. Unit tests do not require model weights.

## Troubleshooting

- **Missing model:** run `scripts/download_models.py` with the vendor environment’s Python.
- **CUDA unavailable:** use upstream’s CUDA 12.8 PyTorch packages, not a CPU-only wheel.
- **Out of memory:** shorten the script or close other GPU applications. Generation is sequential and BF16 is used when supported. Custom CUDA compilation and DeepSpeed are disabled initially for Windows reliability.
- **FFmpeg missing:** install FFmpeg and add its executable directory to PATH.
- **Server failed:** inspect `logs/server-error.log`.

## Planned phases

Emotion controls, waveform editing, enhancement, WAV/MP3/FLAC export options, projects, multi-character timelines and batch generation follow the real basic-generation gate. Model generation controls will be kept separate from audio post-processing. No UI control will pretend to expose an unsupported model feature.

Screenshot documentation will be added after browser verification.

Upstream code and checkpoints retain their respective licenses: [IndexTTS](https://github.com/index-tts/index-tts), [model repository](https://huggingface.co/IndexTeam/IndexTTS-2.5).
