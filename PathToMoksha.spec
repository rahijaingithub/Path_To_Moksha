# -*- mode: python ; coding: utf-8 -*-
"""Portable PyInstaller configuration for the Windows executable."""

import os


ROOT = os.path.abspath(SPECPATH)
SRC = os.path.join(ROOT, "src")
ASSETS = os.path.join(ROOT, "assets")
DATA = os.path.join(ROOT, "data")

ICON_PATH = os.path.join(ASSETS, "images", "icon.ico")
ICON = ICON_PATH if os.path.exists(ICON_PATH) else None


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
        "zmq",
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="PathToMoksha",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=ICON,
)
