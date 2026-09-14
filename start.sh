#!/usr/bin/env bash
set -euo pipefail

dev=0
no_browser=0
for argument in "$@"; do
    case "$argument" in
        --dev|-Dev) dev=1 ;;
        --no-browser|-NoBrowser) no_browser=1 ;;
        *) echo "Unknown option: $argument" >&2; echo "Usage: ./start.sh [--dev] [--no-browser]" >&2; exit 1 ;;
    esac
done

studio_root="$(cd "$(dirname "$0")" && pwd)"
cd "$studio_root"

studio_python="$studio_root/vendor/index-tts/.venv/bin/python"
if [[ ! -x "$studio_python" ]]; then
    echo 'Run ./scripts/install.sh first.' >&2
    exit 1
fi
if [[ "$dev" -eq 0 && ! -f frontend/dist/index.html ]]; then
    echo 'Build the frontend with npm run build in frontend, or use --dev.' >&2
    exit 1
fi

mkdir -p logs
if command -v lsof >/dev/null 2>&1; then
    existing_pids="$(lsof -nP -iTCP:8000 -sTCP:LISTEN -t 2>/dev/null || true)"
    if [[ -n "$existing_pids" ]]; then
        echo "Stopping the existing process on port 8000: $(echo "$existing_pids" | xargs)"
        # shellcheck disable=SC2086
        kill $existing_pids 2>/dev/null || true
        for _ in $(seq 1 20); do
            if ! lsof -nP -iTCP:8000 -sTCP:LISTEN >/dev/null 2>&1; then
                break
            fi
            sleep 0.25
        done
        if lsof -nP -iTCP:8000 -sTCP:LISTEN >/dev/null 2>&1; then
            # shellcheck disable=SC2086
            kill -9 $existing_pids 2>/dev/null || true
            sleep 0.25
        fi
        if lsof -nP -iTCP:8000 -sTCP:LISTEN >/dev/null 2>&1; then
            echo 'Could not free port 8000.' >&2
            exit 1
        fi
    fi
fi

export PYTORCH_ENABLE_MPS_FALLBACK=1
"$studio_python" -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 \
    >logs/server.log 2>logs/server-error.log &
studio_pid=$!

studio_url='http://127.0.0.1:8000'
if [[ "$dev" -eq 1 ]]; then
    (cd frontend && npm run dev >../logs/frontend.log 2>&1) &
    studio_url='http://localhost:5173'
fi

ready=0
for _ in $(seq 1 60); do
    if ! kill -0 "$studio_pid" 2>/dev/null; then
        echo 'Server failed. See logs/server-error.log.' >&2
        exit 1
    fi
    if "$studio_python" -c 'import urllib.request; urllib.request.urlopen("http://127.0.0.1:8000/api/system/model")' >/dev/null 2>&1; then
        ready=1
        break
    fi
    sleep 0.5
done
if [[ "$ready" -eq 0 ]]; then
    echo 'Server did not become ready. See logs/server-error.log.' >&2
    exit 1
fi

if [[ "$no_browser" -eq 0 ]]; then
    if [[ "$(uname -s)" == Darwin ]]; then
        open "$studio_url"
    elif command -v xdg-open >/dev/null 2>&1; then
        xdg-open "$studio_url" >/dev/null 2>&1 || true
    fi
fi

echo "Local Voice Studio: $studio_url (server process $studio_pid)"
