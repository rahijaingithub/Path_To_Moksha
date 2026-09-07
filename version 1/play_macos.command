#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [[ "$(uname -s)" != "Darwin" ]]; then
    echo "This launcher is for macOS. On Windows, run build_exe.bat or python src/main.py."
    exit 1
fi

PYTHON_BIN="${PYTHON_BIN:-python3}"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
    echo "Python 3.11 or newer is required. Install it from https://www.python.org/downloads/macos/"
    exit 1
fi

if ! "$PYTHON_BIN" -c 'import sys; raise SystemExit(sys.version_info < (3, 11))'; then
    echo "Python 3.11 or newer is required. Current version: $($PYTHON_BIN --version 2>&1)"
    exit 1
fi

VENV_DIR="${PATH_TO_MOKSHA_VENV:-$SCRIPT_DIR/.venv}"
if [[ ! -x "$VENV_DIR/bin/python" ]]; then
    echo "Creating the game environment..."
    "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

echo "Checking game dependencies..."
"$VENV_DIR/bin/python" -m pip install --disable-pip-version-check -r requirements.txt

echo "Starting Path to Moksha..."
exec "$VENV_DIR/bin/python" src/main.py
