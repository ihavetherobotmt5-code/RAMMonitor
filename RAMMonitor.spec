# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for RAM Monitor.

Builds a single-file, console-less Windows executable with:
* Custom application icon (multi-resolution)
* Embedded application manifest (Per-Monitor V2 DPI awareness)
* Win32 version resources (visible in File -> Properties -> Details)
* All M1+M2 modules collected (fluent_theme, responsive_grid, compact_mode, settings)
* Dev-only modules excluded (pytest, tkinter, tests)

Build command (run from project root):
    pyinstaller --noconfirm --clean build/RAMMonitor.spec
"""
import os
from PyInstaller.utils.hooks import collect_submodules

# Resolve paths relative to the project root.
# PyInstaller sets SPECPATH to the directory containing the .spec file.
# So _PROJECT_ROOT = parent of that directory = the project root.
_SPEC_DIR = SPECPATH  # PyInstaller sets this to the spec file's directory
_PROJECT_ROOT = os.path.dirname(_SPEC_DIR)

block_cipher = None

hidden_imports = [
    # Explicit Qt modules (defensive -- pyqtgraph pulls these but be explicit)
    "PySide6.QtCore",
    "PySide6.QtGui",
    "PySide6.QtWidgets",
    # M1+M2 modules -- must be explicit to avoid PyInstaller missing them
    "ram_monitor.ui.fluent_theme",
    "ram_monitor.ui.responsive_grid",
    "ram_monitor.ui.compact_mode",    # M2-5
    "ram_monitor.ui.settings",        # M2-9
]
# Batch-collect submodules for the heavy third-party packages.
hidden_imports += collect_submodules("psutil")
hidden_imports += collect_submodules("PySide6")
hidden_imports += collect_submodules("pyqtgraph")

a = Analysis(
    [os.path.join(_PROJECT_ROOT, "src", "ram_monitor", "__main__.py")],
    pathex=[os.path.join(_PROJECT_ROOT, "src")],
    binaries=[],
    datas=[
        (os.path.join(_PROJECT_ROOT, "assets", "rammonitor.ico"), "assets"),
    ],
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "pytest", "unittest", "tkinter", "test", "tests",
        "pdb", "ipython", "matplotlib", "PIL",
    ],
    noarchive=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="RAMMonitor",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=["vcruntime140.dll", "msvcp140.dll"],
    runtime_tmpdir=None,
    console=False,                    # GUI app -- no console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,                 # Build on the host's native arch
    codesign_identity=None,           # Set via environment during signed builds
    entitlements_file=None,
    icon=os.path.join(_PROJECT_ROOT, "assets", "rammonitor.ico"),
    manifest=os.path.join(_PROJECT_ROOT, "assets", "rammonitor.exe.manifest"),
    version_file=os.path.join(_PROJECT_ROOT, "build", "version_info.txt"),
)
