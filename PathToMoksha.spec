# -*- mode: python ; coding: utf-8 -*-
import os

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT   = os.path.abspath(".")
SRC    = os.path.join(ROOT, "src")
ASSETS = os.path.join(ROOT, "assets")
DATA   = os.path.join(ROOT, "data")

# Anaconda DLL paths to prevent pyexpat / DLL load failures
ANACONDA_DIR = r"D:\Installation\Anaconda"
pyexpat_pyd  = os.path.join(ANACONDA_DIR, "DLLs", "pyexpat.pyd")
libexpat_dll = os.path.join(ANACONDA_DIR, "Library", "bin", "libexpat.dll")
ffi_dll      = os.path.join(ANACONDA_DIR, "Library", "bin", "ffi.dll")
libssl_dll   = os.path.join(ANACONDA_DIR, "Library", "bin", "libssl-3-x64.dll")
libcrypto_dll= os.path.join(ANACONDA_DIR, "Library", "bin", "libcrypto-3-x64.dll")

binaries_list = []
for dll_path in [pyexpat_pyd, libexpat_dll, ffi_dll, libssl_dll, libcrypto_dll]:
    if os.path.exists(dll_path):
        binaries_list.append((dll_path, '.'))

# ── Analysis ──────────────────────────────────────────────────────────────────
a = Analysis(
    [os.path.join(SRC, "main.py")],
    pathex=[SRC],
    binaries=binaries_list,
    datas=[
        (ASSETS, "assets"),
        (DATA, "data"),
    ],
    hiddenimports=[
        "pyexpat",
        "_ctypes",
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
        "babel", "docutils", "jinja2", "boto3", "botocore", "skia"
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
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
