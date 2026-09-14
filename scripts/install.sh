#!/usr/bin/env bash
set -euo pipefail

download_models=0
for argument in "$@"; do
    case "$argument" in
        --download-models) download_models=1 ;;
        *) echo "Unknown option: $argument" >&2; echo "Usage: ./scripts/install.sh [--download-models]" >&2; exit 1 ;;
    esac
done

studio_root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$studio_root"

for dependency in uv git node npm ffmpeg; do
    if ! command -v "$dependency" >/dev/null 2>&1; then
        echo "Missing prerequisite: $dependency" >&2
        exit 1
    fi
done

if [[ ! -f vendor/index-tts/pyproject.toml ]]; then
    git clone https://github.com/index-tts/index-tts.git vendor/index-tts
    git -C vendor/index-tts checkout ee40fa7d6c6b8a2c7f06105f9f1e65775b74868c
fi

uv python install 3.11.9
(
    cd vendor/index-tts
    uv sync --frozen --python 3.11.9
)

studio_python="$studio_root/vendor/index-tts/.venv/bin/python"
uv pip install --python "$studio_python" --index-url https://pypi.org/simple -r requirements.txt

(
    cd frontend
    npm ci
    npm run build
)

if [[ "$download_models" -eq 1 ]]; then
    "$studio_python" scripts/download_models.py
fi

echo 'Start with ./start.sh. Model provisioning: ./scripts/install.sh --download-models'
