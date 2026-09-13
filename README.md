# Local Voice Studio

Local Voice Studio is a local Windows web application for expressive speech generation with [IndexTTS 2.5](https://github.com/index-tts/index-tts). It provides voice cloning, emotion controls, emotion-reference audio, waveform previews, editing, multi-speaker timelines, projects, presets, batch generation, and WAV/FLAC/MP3 export. Your recordings and generated audio stay on your computer; no cloud TTS account is required.

## Requirements

- Windows 10/11 (Windows 11 recommended)
- NVIDIA GPU with a current driver and enough VRAM for IndexTTS (verified on an RTX 5060 Ti 16 GB)
- [Git](https://git-scm.com/), [uv](https://docs.astral.sh/uv/), [Node.js/npm](https://nodejs.org/), and [FFmpeg](https://ffmpeg.org/) on `PATH`
- Internet access during installation for upstream source, dependencies, and model checkpoints

The installer provisions Python 3.11.9 and creates the model environment at `vendor/index-tts/.venv`. Model weights are downloaded separately and ignored by Git.

## Install

Open PowerShell in this repository and run:

```powershell
.\scripts\install.ps1 -DownloadModels
```

To install without downloading large checkpoints, omit `-DownloadModels`; download later with:

```powershell
vendor\index-tts\.venv\Scripts\python.exe scripts\download_models.py
```

The installer pins the tested upstream IndexTTS revision, installs its locked CUDA/PyTorch environment, installs this app's dependencies, and builds the frontend.

## Start

Production build:

```powershell
.\start.ps1
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000). For frontend development:

```powershell
.\start.ps1 -Dev
```

Then open [http://127.0.0.1:5173](http://127.0.0.1:5173). Add `-NoBrowser` to start without opening a browser. The model stays resident and jobs are processed sequentially; do not run multiple Uvicorn workers.

## Basic workflow

1. Choose **Add a voice** and upload a clean recording that you own or are authorized to use. References must be 3–60 seconds; 5–15 seconds is recommended.
2. Select the voice, enter a script, and choose English, Chinese, Japanese, Spanish, or Arabic. Urdu and Hindi are not supported by the upstream release.
3. Choose an emotion mode. The mixer exposes eight IndexTTS emotion dimensions, strength, and speed. Description mode accepts a natural-language prompt; reference mode accepts separate emotion audio.
4. Select **Generate speech** or press `Ctrl+Enter`. The first request takes longer while the model loads.
5. Review the waveform and take history, then trim, enhance, save a project, or export WAV, FLAC, or MP3.
6. Use **Advanced timeline** to assign different saved speakers to lines and queue a multi-speaker sequence with configurable silence between segments.

Browser script drafts are autosaved locally. Application data is stored at `%LOCALAPPDATA%\LocalVoiceStudio\data` by default. Set `VOICE_STUDIO_DATA` to choose another local directory.

## Verification

```powershell
cd frontend
npm.cmd run build
cd ..
vendor\index-tts\.venv\Scripts\python.exe -m pytest backend/tests -q
vendor\index-tts\.venv\Scripts\python.exe scripts\diagnose.py
vendor\index-tts\.venv\Scripts\python.exe scripts\smoke_gpu.py path\to\reference.wav
```

The smoke test performs real local GPU inference and checks that the returned WAV is valid and non-silent. Diagnostics report Python packages, FFmpeg, GPU memory, checkpoint readiness, and storage paths.

## Repository layout

```text
backend/       FastAPI API, job queue, IndexTTS adapter, audio processing, database
frontend/      React + TypeScript + Vite interface
scripts/       Installation, model download, startup, diagnostics, smoke test
docs/          Specification and implementation progress
vendor/        Upstream IndexTTS checkout (ignored by Git)
```

## Troubleshooting

- **Missing model:** run `scripts\download_models.py` with the vendor Python environment and inspect `/api/system/diagnostics`.
- **CUDA unavailable:** update the NVIDIA driver and use the upstream CUDA-enabled PyTorch environment; CPU-only wheels are not the tested setup.
- **Out of memory:** shorten scripts, close other GPU applications, or generate timeline segments separately.
- **FFmpeg missing:** install FFmpeg, add its `bin` directory to `PATH`, and reopen PowerShell.
- **Server failure:** ensure port 8000 is free and inspect `logs/server-error.log`.

## Privacy and responsible use

The server binds to localhost by default. Recordings and generated audio remain in the configured local storage directory. Clone only voices you own or have explicit permission to use, and disclose synthetic audio where required by law or context.

## Credits and third-party components

- **IndexTTS 2.5**: speech synthesis and voice cloning. [Source repository](https://github.com/index-tts/index-tts) and [model checkpoints](https://huggingface.co/IndexTeam/IndexTTS-2.5). Review the upstream source and model licenses before redistribution or commercial use.
- **PyTorch and torchaudio**: CUDA tensor and audio runtime. [pytorch.org](https://pytorch.org/)
- **Hugging Face Hub**: checkpoint download tooling. [Documentation](https://huggingface.co/docs/huggingface_hub)
- **FastAPI, Uvicorn, Pydantic, NumPy, SoundFile, pytest**: backend, validation, numerical/audio I/O, and tests. Each package retains its own license.
- **React, TypeScript, Vite, lucide-react**: frontend runtime, build tooling, and icons. [React](https://react.dev/) · [TypeScript](https://www.typescriptlang.org/) · [Vite](https://vite.dev/) · [Lucide](https://lucide.dev/)
- **FFmpeg**: decoding, enhancement, trimming, concatenation, and export. [ffmpeg.org](https://ffmpeg.org/). Check the binary's license and enabled codecs when distributing it.
- **uv**: Python version and environment management. [Documentation](https://docs.astral.sh/uv/)

This repository does not include upstream model weights or the upstream source checkout. The installer downloads them locally and `.gitignore` excludes them.

## License

No project-level license has been selected yet. Third-party software, upstream source, model checkpoints, and downloaded binaries remain subject to their own licenses and terms. Add a project license before accepting outside contributions or publishing a redistributed package.

## Documentation

- [Full specification](docs/SPECIFICATION.md)
- [Implementation progress](docs/PROGRESS.md)
