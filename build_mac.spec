# -*- mode: python ; coding: utf-8 -*-
# build_mac.spec — PyInstaller spec for macOS (.app bundle)
# ─────────────────────────────────────────────────────────────
# Run this on a Mac from inside the "version 1" directory:
#   pyinstaller build_mac.spec
#
# Output: dist/PathToMoksha.app
# ─────────────────────────────────────────────────────────────
import os

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT   = os.path.abspath(".")
SRC    = os.path.join(ROOT, "src")
ASSETS = os.path.join(ROOT, "assets")
DATA   = os.path.join(ROOT, "data")

# Icon file — create a .icns from your game icon before building.
# Use "iconutil" on Mac or an online converter.
# Place it at: assets/images/icon.icns
ICON_PATH = os.path.join(ASSETS, "images", "icon.icns")
icon_arg = ICON_PATH if os.path.exists(ICON_PATH) else None

# ── Analysis ──────────────────────────────────────────────────────────────────
a = Analysis(
    [os.path.join(SRC, "main.py")],
    pathex=[SRC],
    binaries=[],              # No Windows DLLs on Mac
    datas=[
        (ASSETS, "assets"),
        (DATA, "data"),
    ],
    hiddenimports=[
        "pygame",
        "pygame.mixer",
        "pygame.font",
        "pygame.image",
        "pygame.joystick",
        "pygame.locals",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "numpy", "scipy", "pandas", "matplotlib", "PIL", "tkinter",
        "notebook", "IPython", "tornado", "zmq", "cv2", "sklearn",
        "cryptography", "lxml", "h5py", "sqlalchemy", "sphinx",
        "babel", "docutils", "jinja2", "boto3", "botocore", "skia",
        # Windows-only exclusions (not present on Mac, but safe to list)
        "winreg", "ctypes.windll",
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure, a.zipped_data)

# ── macOS .app bundle ─────────────────────────────────────────────────────────
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="PathToMoksha",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,         # UPX is unreliable on macOS — keep disabled
    console=False,     # No terminal window
    disable_windowed_traceback=False,
    argv_emulation=True,   # Required for proper macOS .app event handling
    target_arch=None,      # None = build for current arch (arm64 on M1/M2, x86_64 on Intel)
    codesign_identity=None,     # Set to your Apple Developer ID for distribution
    entitlements_file=None,
    icon=icon_arg,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="PathToMoksha",
)

# ── Bundle into .app ──────────────────────────────────────────────────────────
app = BUNDLE(
    coll,
    name="PathToMoksha.app",
    icon=icon_arg,
    bundle_identifier="com.jsot.pathtomoksha",   # Reverse-DNS identifier
    info_plist={
        # App metadata shown in Finder & About
        "CFBundleDisplayName": "Path to Moksha",
        "CFBundleShortVersionString": "1.0.0",
        "CFBundleVersion": "1.0.0",
        "NSHumanReadableCopyright": "© 2026 JSOT Digamber Pathshala. All rights reserved.",

        # Allow windowed mode and fullscreen toggle to work correctly
        "NSHighResolutionCapable": True,
        "LSMinimumSystemVersion": "11.0",   # macOS Big Sur minimum

        # Gamepad / joystick support
        "NSGameControllerUsageDescription": "Path to Moksha supports game controllers for gameplay.",

        # Disable App Transport Security (not needed, just avoids warnings)
        "NSAppTransportSecurity": {"NSAllowsArbitraryLoads": True},
    },
)
