# The Path to Moksha

*The Path to Moksha* is a spiritual 2D platform game built with Python and
Pygame. It supports keyboard, gamepad, and on-screen controls.

## Play the game

### macOS

1. Download `PathToMoksha-mac.zip` from the project's
   [Releases page](https://github.com/rahijaingithub/Path_To_Moksha/releases)
   and open the zip.
2. Move `PathToMoksha.app` to `Applications` if desired.
3. Open the app. For an ad-hoc-signed or unnotarized local build, right-click
   the app in Finder, choose **Open**, then confirm **Open** on the first launch.

The automated release contains the native architecture of its macOS build
runner. If macOS reports that it is incompatible with your Mac, use the source
launcher below or create a native local build with `build_macos.sh`.

### Windows

Download `PathToMoksha.exe` from the Releases page and double-click it.

## Run from source

Python 3.11 or newer is recommended.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python src/main.py
```

On macOS, `play_macos.command` provides a convenient launcher. If necessary,
make it executable once with `chmod +x play_macos.command`.

## Build for macOS

Run the build on a Mac:

```bash
chmod +x build_macos.sh
./build_macos.sh
```

The build produces `dist/PathToMoksha.app` and
`dist/PathToMoksha-mac.zip`. See [the developer reference](docs/DEV_REFERENCE.md)
for architecture and code-signing options.

Player profiles and high scores on macOS are stored in
`~/Library/Application Support/PathToMoksha`.

More gameplay and installation information is available in
[the game guide](docs/README.md).
