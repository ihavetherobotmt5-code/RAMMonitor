"""Entry point so `python -m ram_monitor` works.

This file is intentionally tiny — all logic lives in `app.py:run()`.
"""
from __future__ import annotations

import sys

from ram_monitor.app import run

if __name__ == "__main__":
    sys.exit(run())
