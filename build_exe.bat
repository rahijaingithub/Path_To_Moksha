@echo off
SETLOCAL
cd /d "%~dp0"

REM Set PYTHON to a specific python.exe before running this script if needed.
IF NOT DEFINED PYTHON SET "PYTHON=python"

echo.
echo ==============================================
echo   PATH TO MOKSHA - WINDOWS BUILD
echo ==============================================
echo.

"%PYTHON%" --version >NUL 2>&1
IF ERRORLEVEL 1 (
    echo ERROR: Python 3.11 or newer was not found on PATH.
    echo Install Python from https://www.python.org/downloads/windows/
    pause
    exit /b 1
)
"%PYTHON%" -c "import sys; raise SystemExit(sys.version_info ^< (3, 11))"
IF ERRORLEVEL 1 (
    echo ERROR: Python 3.11 or newer is required.
    pause
    exit /b 1
)

echo [1/2] Installing build dependencies...
"%PYTHON%" -m pip install --disable-pip-version-check -r requirements-build.txt
IF ERRORLEVEL 1 (
    echo ERROR: Could not install build dependencies.
    pause
    exit /b 1
)

echo [2/2] Building the standalone executable...
"%PYTHON%" -m PyInstaller PathToMoksha.spec --noconfirm --clean
IF ERRORLEVEL 1 (
    echo ERROR: PyInstaller build failed. Check the output above.
    pause
    exit /b 1
)

IF EXIST "dist\PathToMoksha.exe" (
    echo.
    echo BUILD SUCCESSFUL: dist\PathToMoksha.exe
) ELSE (
    echo ERROR: dist\PathToMoksha.exe was not created.
    pause
    exit /b 1
)

echo.
pause
