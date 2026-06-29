@echo off
REM ============================================================================
REM  RAM Monitor — Windows build script
REM  Produces a single-file, console-less .exe via PyInstaller.
REM
REM  Usage:
REM     build.bat                 # builds dist\RAMMonitor.exe
REM     build.bat clean           # removes build/ dist/ and PyInstaller cache
REM ============================================================================
setlocal EnableDelayedExpansion

set "APP_NAME=RAMMonitor"
set "ENTRY=src\ram_monitor\__main__.py"
set "ICON="

REM -- Resolve repo root (script's directory) --
pushd "%~dp0"
set "ROOT=%CD%"
popd

REM -- 'clean' subcommand --
if /I "%~1"=="clean" (
    echo Cleaning previous build artifacts...
    if exist "build" rmdir /S /Q "build"
    if exist "dist"  rmdir /S /Q "dist"
    if exist "%APP_NAME%.spec" del /Q "%APP_NAME%.spec"
    echo Done.
    exit /b 0
)

REM -- Verify venv / python on PATH --
where python >nul 2>nul
if errorlevel 1 (
    echo ERROR: python not found on PATH. Create a venv and activate it first:
    echo     python -m venv .venv
    echo     .venv\Scripts\activate
    exit /b 1
)

REM -- Ensure PyInstaller is installed --
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo PyInstaller not found, installing...
    python -m pip install --upgrade pyinstaller || exit /b 1
)

REM -- Ensure runtime deps are installed --
python -c "import PySide6, psutil, pyqtgraph, numpy" 2>nul
if errorlevel 1 (
    echo Installing runtime dependencies...
    python -m pip install -r requirements.txt || exit /b 1
)

REM -- Build --
echo.
echo Building %APP_NAME%.exe ...
echo.

set "EXCLUDES=pytest unittest tkinter test tests"
set "EXCLUDE_ARGS="
for %%M in (%EXCLUDES%) do set "EXCLUDE_ARGS=!EXCLUDE_ARGS! --exclude-module %%M"

python -m PyInstaller ^
    --noconfirm ^
    --clean ^
    --onefile ^
    --noconsole ^
    --name "%APP_NAME%" ^
    --collect-submodules psutil ^
    --collect-submodules PySide6 ^
    --collect-submodules pyqtgraph ^
    --hidden-import "PySide6.QtCore" ^
    --hidden-import "PySide6.QtGui" ^
    --hidden-import "PySide6.QtWidgets" ^
    %EXCLUDE_ARGS% ^
    "%ENTRY%"

if errorlevel 1 (
    echo.
    echo BUILD FAILED.
    exit /b 1
)

echo.
echo BUILD OK: dist\%APP_NAME%.exe
echo (You can run it directly or copy it to any Windows machine.)
exit /b 0
