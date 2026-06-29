"""Editable-install + PyInstaller metadata.

Usage:
    pip install -e .            # dev install
    pip install -e .[dev]       # dev install with pytest etc.
"""
from __future__ import annotations

from pathlib import Path
from setuptools import find_packages, setup

ROOT = Path(__file__).parent
README = (ROOT / "README.md").read_text(encoding="utf-8") if (ROOT / "README.md").exists() else ""

setup(
    name="ram-monitor",
    version="1.0.0",
    description="Lightweight Windows 11 RAM/CPU monitor — observe only, never cleans.",
    long_description=README,
    long_description_content_type="text/markdown",
    author="RAM Monitor Project",
    license="MIT",
    python_requires=">=3.11",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    include_package_data=True,
    install_requires=[
        "PySide6>=6.6,<7",
        "psutil>=5.9,<7",
        "pyqtgraph>=0.13",
        "numpy>=1.24",
    ],
    extras_require={
        "dev": ["pytest>=8.0", "pyinstaller>=6.0"],
    },
    entry_points={
        "console_scripts": [
            "ram-monitor=ram_monitor.app:run",
        ],
        "gui_scripts": [
            "RAMMonitor=ram_monitor.app:run",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: X11 Applications :: Qt",
        "Environment :: Win32 (MS Windows)",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows :: Windows 11",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: System :: Monitoring",
    ],
)
