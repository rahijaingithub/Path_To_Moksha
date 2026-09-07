# Developer Reference

## File & Folder Inventory

| File / Folder | Responsibility |
|---------------|----------------|
| `assets/` | Contains all read-only game media (`audio`, `fonts`, `images`, and JSON files for questions/goals). |
| `data/` | Stores writable user data (profiles, high scores, custom controller mappings). |
| `src/main.py` | Application entry point; handles window scaling, Pygame init, and the master game loop. |
| `src/settings.py` | Global constants, color definitions, gameplay variables, and cross-platform path resolution. |
| `src/scene_manager.py` | State machine orchestrator for transitioning between game screens. |
| `src/asset_manager.py` | Robust caching loader for images, audio, and fonts with missing-file fallbacks. |
| `src/input_manager.py` | Unified input handler for keyboard, controllers, and on-screen touch buttons. |
| `src/profile_manager.py` | Handles JSON serialization for player save data and global leaderboards. |
| `src/level_scene.py` | Core gameplay scene; orchestrates player movement, collision, boxes, and the Monk. |
| `src/level_layouts.py` | Defines the specific `pygame.Rect` platform layouts for all 4 levels. |
| `src/box_system.py` | Handles Box Roulette logic, placement, and time penalty/bonus application. |
| `src/monk_system.py` | Manages the Monk NPC, proximity interaction, and typewriter dialogue overlay. |
| `src/test.py` | Standalone rendering benchmark comparing Pygame, Cairo, and Skia drawing APIs. |
| `generate_audio.py` | Utility script to procedurally synthesize 16-bit retro `.wav` sound effects. |
| `requirements.txt` | Runtime dependencies used when playing from source. |
| `requirements-build.txt` | Runtime and packaging dependencies used to create distributable builds. |
| `PathToMoksha.spec` | PyInstaller build specification tailored for Windows (.exe). |
| `build_mac.spec` | PyInstaller build specification tailored for macOS (.app bundle). |
| `play_macos.command` | Finder-friendly macOS source launcher. |
| `build_macos.sh` | Reproducible macOS app build, validation, signing, and archive entry point. |

## Build, Run, and Test Instructions

### Run from source

Python 3.11 or newer is recommended. Create an isolated environment from the
repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python src/main.py
```

On macOS, `play_macos.command` is the Finder-friendly equivalent. It can also be
started from Terminal:

```bash
chmod +x play_macos.command
./play_macos.command
```

### Build for Windows

```bash
python -m pip install -r requirements-build.txt
python -m PyInstaller PathToMoksha.spec --noconfirm
```

The executable is written to `dist/PathToMoksha.exe`.

### Build for macOS

macOS bundles must be built on macOS. The build script installs the build
dependencies, invokes PyInstaller, validates the app, and creates the archive:

```bash
chmod +x build_macos.sh
./build_macos.sh
```

Outputs:

- `dist/PathToMoksha.app`
- `dist/PathToMoksha-mac.zip`

By default, PyInstaller creates a native build for the current Mac's
architecture. To request a universal2 app:

```bash
PYINSTALLER_TARGET_ARCH=universal2 ./build_macos.sh
```

Universal2 succeeds only when Python and every bundled binary dependency are
also universal. If they are not, produce and label separate native Intel and
Apple Silicon archives instead. Inspect a finished executable with:

```bash
file dist/PathToMoksha.app/Contents/MacOS/PathToMoksha
```

To sign with an installed Apple Developer identity:

```bash
MACOS_CODESIGN_IDENTITY="Developer ID Application: Your Name (TEAMID)" ./build_macos.sh
```

Without `MACOS_CODESIGN_IDENTITY`, the script applies an ad-hoc development
signature and players may need Finder's right-click **Open** flow on first
launch. Developer ID signing and Apple notarization are separate steps; a
public, frictionless download should be both signed and notarized. If a
`notarytool` keychain profile is configured, set `MACOS_NOTARY_PROFILE` to have
the build script submit and staple the finished app.

The packaged app treats bundled assets as read-only. Both source and packaged
macOS runs store profiles, high scores, and writable configuration in:

```text
~/Library/Application Support/PathToMoksha
```

For portable or test installs, `PATH_TO_MOKSHA_DATA_DIR` overrides that writable
location without changing the bundled asset path. `DIST_DIR` and
`BUILD_WORK_DIR` can similarly redirect macOS build output and temporary files.
The bundle metadata is configurable with `PATH_TO_MOKSHA_VERSION`,
`MACOS_BUNDLE_IDENTIFIER`, and `MACOSX_DEPLOYMENT_TARGET`.

The build archive should be distributed intact rather than copying files out of
the `.app` bundle.

## Asset Pipeline

* **Audio:** Placeholder sound effects are generated procedurally using the `generate_audio.py` script.
* **Graphics:** Several sprites and background images were authored via AI generation. The specific prompts used for these generations are documented in `image_generation_prompts.md` in the root directory.
* **Dependencies:** Install the tested runtime set from `requirements.txt` and
  the packaging set from `requirements-build.txt`. The `skia` and `cairo`
  dependencies referenced in `test.py` are strictly for R&D/benchmarking and
  are excluded from final builds via the `.spec` files.
