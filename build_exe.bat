@echo off
SETLOCAL

REM ═══════════════════════════════════════════════════════════════
REM  build_exe.bat — Builds single standalone PathToMoksha.exe
REM  Run this from "version 1" folder by double-clicking it,
REM  or from cmd: cd /d "d:\Jain_game_workspace\Path to Moksha\version 1"
REM                build_exe.bat
REM ═══════════════════════════════════════════════════════════════

SET PYTHON=D:\Installation\Anaconda\python.exe
SET SPECFILE=PathToMoksha.spec
SET ANACONDA_DIR=D:\Installation\Anaconda

echo.
echo ══════════════════════════════════════════════
echo   PATH TO MOKSHA — SINGLE EXE BUILD SCRIPT
echo ══════════════════════════════════════════════
echo.

REM ── Step 1: Install / upgrade PyInstaller ─────────────────────
echo [1/3] Checking PyInstaller...
"%PYTHON%" -m pip install pyinstaller --quiet --upgrade
IF ERRORLEVEL 1 (
    echo ERROR: Could not verify PyInstaller. Check Python installation.
    pause
    exit /b 1
)
echo       Done.

REM ── Step 2: Clean previous build ─────────────────────────────
echo [2/3] Cleaning previous build files...
IF EXIST build     RMDIR /S /Q build
IF EXIST dist      RMDIR /S /Q dist
echo       Done.

REM ── Step 3: Run PyInstaller with Spec ─────────────────────────
echo [3/3] Building single-file EXE (this takes ~1-3 minutes)...
"%PYTHON%" -m PyInstaller %SPECFILE% --noconfirm
IF ERRORLEVEL 1 (
    echo ERROR: PyInstaller build failed. Check output above.
    pause
    exit /b 1
)

echo.
echo ══════════════════════════════════════════════
IF EXIST "dist\PathToMoksha.exe" (
    echo   BUILD SUCCESSFUL!
    echo.
    echo   Single File Executable Created:
    echo   dist\PathToMoksha.exe
    echo.
    echo   You can share dist\PathToMoksha.exe DIRECTLY!
    echo   No zipping or extra asset folders needed.
) ELSE (
    echo   BUILD FAILED — Check PyInstaller logs above.
)
echo ══════════════════════════════════════════════
echo.
pause
