# Local Voice Studio

Local Voice Studio is a local web application for expressive speech generation with [IndexTTS 2.5](https://github.com/index-tts/index-tts). It provides voice cloning, emotion controls, emotion-reference audio, waveform previews, editing, multi-speaker timelines, projects, presets, batch generation, and WAV/FLAC/MP3 export. Your recordings and generated audio stay on your computer; no cloud TTS account is required.

It runs on **macOS** (Apple Silicon / Metal) and **Windows** (NVIDIA / CUDA). The same browser UI talks to a FastAPI server on your machine.

| Platform | Accelerator | Install | Start |
| --- | --- | --- | --- |
| macOS (Apple Silicon) | Metal / MPS | `./scripts/install.sh --download-models` | `./start.sh` |
| Windows 10/11 | NVIDIA CUDA | `.\scripts\install.ps1 -DownloadModels` | `.\start.ps1` |

## Requirements

Shared tools (must be on `PATH`):

- [Git](https://git-scm.com/), [uv](https://docs.astral.sh/uv/), [Node.js/npm](https://nodejs.org/), and [FFmpeg](https://ffmpeg.org/)
- Internet access during installation for upstream source, dependencies, and model checkpoints

### macOS

- macOS 14 or later
- Apple Silicon (M1 or newer) recommended; 16 GB unified memory or more is more comfortable
- IndexTTS uses PyTorch’s Metal/MPS backend. The first generation is slower than a CUDA GPU
- Intel Macs fall back to CPU and are much slower
- Xcode Command Line Tools: `xcode-select --install`
- Homebrew tools, if they are not already installed:

```bash
brew install git node ffmpeg
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Windows

- Windows 10/11 (Windows 11 recommended)
- NVIDIA GPU with a current driver and enough VRAM for IndexTTS (verified on an RTX 5060 Ti 16 GB)

The installer provisions Python 3.11.9 and creates the model environment at `vendor/index-tts/.venv`. Model weights are downloaded separately and ignored by Git. On macOS the lockfile installs the official PyTorch build with Metal support; on Windows it installs CUDA 12.8 PyTorch.

## Install

### macOS

From the repository root:

```bash
chmod +x scripts/install.sh start.sh
./scripts/install.sh --download-models
```

To install without downloading large checkpoints, omit `--download-models`; download later with:

```bash
vendor/index-tts/.venv/bin/python scripts/download_models.py
```

### Windows

Open PowerShell in this repository and run:

```powershell
.\scripts\install.ps1 -DownloadModels
```

To install without downloading large checkpoints, omit `-DownloadModels`; download later with:

```powershell
vendor\index-tts\.venv\Scripts\python.exe scripts\download_models.py
```

The installer pins the tested upstream IndexTTS revision, installs its locked PyTorch environment for this OS, installs this app's dependencies, and builds the frontend.

## Start

### macOS

```bash
./start.sh
```

For frontend development: `./start.sh --dev`. Add `--no-browser` to start without opening a browser.

### Windows

```powershell
.\start.ps1
```

For frontend development: `.\start.ps1 -Dev`. Add `-NoBrowser` to start without opening a browser.

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in production, or [http://127.0.0.1:5173](http://127.0.0.1:5173) in development. The model stays resident and jobs are processed sequentially; do not run multiple Uvicorn workers.

## Basic workflow

1. Choose **Add a voice** and upload a clean recording that you own or are authorized to use. References must be 3–60 seconds; 5–15 seconds is recommended.
2. Select the voice, enter a script, and choose English, Chinese, Japanese, Spanish, or Arabic. Urdu and Hindi are not supported by the upstream release.
3. Choose an emotion mode. The mixer exposes eight IndexTTS emotion dimensions, strength, and speed. Description mode accepts a natural-language prompt; reference mode accepts separate emotion audio.
4. Select **Generate speech** or press `Ctrl+Enter` (Windows) / `⌘+Enter` (macOS). The first request takes longer while the model loads.
5. Review the waveform and take history, then trim, enhance, save a project, or export WAV, FLAC, or MP3.
6. Use **Advanced timeline** to assign different saved speakers to lines and queue a multi-speaker sequence with configurable silence between segments.

Browser script drafts are autosaved locally. Application data is stored at:

- Windows: `%LOCALAPPDATA%\LocalVoiceStudio\data`
- macOS: `~/Library/Application Support/LocalVoiceStudio/data`
- Linux: `~/.local/share/LocalVoiceStudio/data`

Set `VOICE_STUDIO_DATA` to choose another local directory.

## Verification

### macOS

```bash
cd frontend
npm run build
cd ..
vendor/index-tts/.venv/bin/python -m pytest backend/tests -q
vendor/index-tts/.venv/bin/python scripts/diagnose.py
vendor/index-tts/.venv/bin/python scripts/smoke_gpu.py /path/to/reference.wav
```

### Windows

```powershell
cd frontend
npm.cmd run build
cd ..
vendor\index-tts\.venv\Scripts\python.exe -m pytest backend/tests -q
vendor\index-tts\.venv\Scripts\python.exe scripts\diagnose.py
vendor\index-tts\.venv\Scripts\python.exe scripts\smoke_gpu.py path\to\reference.wav
```

The smoke test performs real local inference and checks that the returned WAV is valid and non-silent. Diagnostics report Python packages, FFmpeg, GPU or Metal status, checkpoint readiness, and storage paths. On a working Apple Silicon install, diagnostics should show `"backend": "mps"` and the studio header should show `mps` after the model loads.

## Repository layout

```text
backend/       FastAPI API, job queue, IndexTTS adapter, audio processing, database
frontend/      React + TypeScript + Vite interface
scripts/       macOS/Windows installers, model download, diagnostics, smoke test
start.sh       macOS/Linux production start
start.ps1      Windows production start
docs/          Specification and implementation progress
vendor/        Upstream IndexTTS checkout (ignored by Git)
```

## Troubleshooting

- **Missing model:** run `scripts/download_models.py` with the vendor Python environment and inspect `/api/system/diagnostics`.
- **CUDA unavailable (Windows):** update the NVIDIA driver and use the upstream CUDA-enabled PyTorch environment; CPU-only wheels are not the tested Windows setup.
- **Slow or Metal errors (macOS):** Apple Silicon uses MPS. Unsupported ops fall back to CPU automatically. Close other GPU-heavy apps, shorten the script, or generate timeline segments separately. CPU-only Intel Macs will be very slow.
- **Out of memory:** shorten scripts, close other GPU applications, or generate timeline segments separately.
- **FFmpeg missing:** install FFmpeg, add it to `PATH`, and open a new terminal. On macOS: `brew install ffmpeg`.
- **Server failure:** ensure port 8000 is free and inspect `logs/server-error.log`.

## Privacy and responsible use

The server binds to localhost by default. Recordings and generated audio remain in the configured local storage directory. Clone only voices you own or have explicit permission to use, and disclose synthetic audio where required by law or context.

## Credits and third-party components

- **IndexTTS 2.5**: speech synthesis and voice cloning. [Source repository](https://github.com/index-tts/index-tts) and [model checkpoints](https://huggingface.co/IndexTeam/IndexTTS-2.5). Review the upstream source and model licenses before redistribution or commercial use.
- **PyTorch and torchaudio**: CUDA (Windows/Linux) and Metal/MPS (macOS) tensor and audio runtime. [pytorch.org](https://pytorch.org/)
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
