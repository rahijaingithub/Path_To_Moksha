# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller configuration for a distributable macOS .app bundle."""

import os


ROOT = os.path.abspath(SPECPATH)
SRC = os.path.join(ROOT, "src")
ASSETS = os.path.join(ROOT, "assets")
DATA = os.path.join(ROOT, "data")

ICON_PATH = os.path.join(ASSETS, "images", "icon.icns")
ICON = ICON_PATH if os.path.exists(ICON_PATH) else None

# Native builds are the most reliable default. A python.org universal2 Python
# plus universal dependencies can opt in with PYINSTALLER_TARGET_ARCH=universal2.
TARGET_ARCH = os.environ.get("PYINSTALLER_TARGET_ARCH") or None
CODESIGN_IDENTITY = os.environ.get("MACOS_CODESIGN_IDENTITY") or None
APP_VERSION = os.environ.get("PATH_TO_MOKSHA_VERSION", "1.0.0")
MINIMUM_MACOS = os.environ.get("MACOSX_DEPLOYMENT_TARGET", "11.0")
BUNDLE_IDENTIFIER = os.environ.get(
    "MACOS_BUNDLE_IDENTIFIER", "com.jsot.pathtomoksha"
)


a = Analysis(
    [os.path.join(SRC, "main.py")],
    pathex=[SRC],
    binaries=[],
    datas=[
        (ASSETS, "assets"),
        (DATA, "data"),
    ],
    hiddenimports=[
        "pygame",
        "pygame.font",
        "pygame.image",
        "pygame.joystick",
        "pygame.locals",
        "pygame.mixer",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "IPython",
        "PIL",
        "babel",
        "boto3",
        "botocore",
        "cryptography",
        "cv2",
        "docutils",
        "h5py",
        "jinja2",
        "lxml",
        "matplotlib",
        "notebook",
        "numpy",
        "pandas",
        "scipy",
        "skia",
        "sklearn",
        "sphinx",
        "sqlalchemy",
        "tkinter",
        "tornado",
        "winreg",
        "zmq",
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="PathToMoksha",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=TARGET_ARCH,
    codesign_identity=CODESIGN_IDENTITY,
    entitlements_file=None,
    icon=ICON,
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

app = BUNDLE(
    coll,
    name="PathToMoksha.app",
    icon=ICON,
    bundle_identifier=BUNDLE_IDENTIFIER,
    info_plist={
        "CFBundleDisplayName": "Path to Moksha",
        "CFBundleShortVersionString": APP_VERSION,
        "CFBundleVersion": APP_VERSION,
        "LSMinimumSystemVersion": MINIMUM_MACOS,
        "NSHighResolutionCapable": True,
        "NSHumanReadableCopyright": (
            "© 2026 JSOT Digamber Pathshala. All rights reserved."
        ),
    },
)
