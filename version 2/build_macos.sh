#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

if [[ "$(uname -s)" != "Darwin" ]]; then
    echo "macOS app bundles must be built on macOS."
    exit 1
fi

PYTHON_BIN="${PYTHON_BIN:-python3}"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
    echo "Python 3.11 or newer is required."
    exit 1
fi

if ! "$PYTHON_BIN" -c 'import sys; raise SystemExit(sys.version_info < (3, 11))'; then
    echo "Python 3.11 or newer is required. Current version: $($PYTHON_BIN --version 2>&1)"
    exit 1
fi

BUILD_VENV="${BUILD_VENV:-$ROOT_DIR/.venv-build}"
if [[ ! -x "$BUILD_VENV/bin/python" ]]; then
    "$PYTHON_BIN" -m venv "$BUILD_VENV"
fi

"$BUILD_VENV/bin/python" -m pip install --disable-pip-version-check -r requirements-build.txt

export MACOSX_DEPLOYMENT_TARGET="${MACOSX_DEPLOYMENT_TARGET:-11.0}"
DIST_DIR="${DIST_DIR:-$ROOT_DIR/dist}"
BUILD_WORK_DIR="${BUILD_WORK_DIR:-$ROOT_DIR/build/macos}"
SIGNING_IDENTITY="${MACOS_CODESIGN_IDENTITY:--}"
if [[ -n "${MACOS_NOTARY_PROFILE:-}" && "$SIGNING_IDENTITY" == "-" ]]; then
    echo "MACOS_NOTARY_PROFILE requires a Developer ID in MACOS_CODESIGN_IDENTITY."
    exit 1
fi

"$BUILD_VENV/bin/python" -m PyInstaller \
    --noconfirm \
    --clean \
    --distpath "$DIST_DIR" \
    --workpath "$BUILD_WORK_DIR" \
    "$ROOT_DIR/build_mac.spec"

APP_PATH="$DIST_DIR/PathToMoksha.app"
ARCHIVE_PATH="$DIST_DIR/PathToMoksha-mac.zip"
APP_BINARY="$APP_PATH/Contents/MacOS/PathToMoksha"

if [[ ! -x "$APP_BINARY" ]]; then
    echo "Build failed: $APP_BINARY was not created."
    exit 1
fi

if [[ "$SIGNING_IDENTITY" == "-" ]]; then
    codesign --force --deep --sign - "$APP_PATH"
else
    codesign --force --deep --options runtime --timestamp \
        --sign "$SIGNING_IDENTITY" "$APP_PATH"
fi

plutil -lint "$APP_PATH/Contents/Info.plist"
codesign --verify --deep --strict "$APP_PATH"
test -d "$APP_PATH/Contents/Resources/assets"
test -d "$APP_PATH/Contents/Resources/data"

if [[ "${SKIP_SMOKE_TEST:-0}" != "1" ]]; then
    SMOKE_DATA_DIR="$(mktemp -d "${TMPDIR:-/tmp}/path-to-moksha-smoke.XXXXXX")"
    PATH_TO_MOKSHA_DATA_DIR="$SMOKE_DATA_DIR" \
        SDL_VIDEODRIVER=dummy \
        SDL_AUDIODRIVER=dummy \
        "$APP_BINARY" --smoke-test
    rm -rf "$SMOKE_DATA_DIR"
fi

rm -f "$ARCHIVE_PATH"
ditto -c -k --sequesterRsrc --keepParent "$APP_PATH" "$ARCHIVE_PATH"
unzip -t "$ARCHIVE_PATH" >/dev/null

if [[ -n "${MACOS_NOTARY_PROFILE:-}" ]]; then
    xcrun notarytool submit "$ARCHIVE_PATH" \
        --keychain-profile "$MACOS_NOTARY_PROFILE" --wait
    xcrun stapler staple "$APP_PATH"
    rm -f "$ARCHIVE_PATH"
    ditto -c -k --sequesterRsrc --keepParent "$APP_PATH" "$ARCHIVE_PATH"
    unzip -t "$ARCHIVE_PATH" >/dev/null
fi

echo "Built: $APP_PATH"
echo "Share: $ARCHIVE_PATH"
file "$APP_BINARY"
