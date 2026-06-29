"""Rotating-file logger that never crashes the host application.

Logging is **off by default** in the released binary (PyInstaller bundle) to
keep the app's footprint minimal and avoid writing to user disk without
consent. It is enabled via the `RAM_MONITOR_DEBUG=1` environment variable.

Design notes:
* A single module-level `get_logger()` call returns a configured logger.
* File handler rotates at 1 MB with 1 backup — small enough that even a
  week-long debug session stays under 2 MB on disk.
* All handler-attachment code is wrapped in try/except so a read-only
  filesystem (e.g. corporate kiosk) cannot bring the app down.
"""
from __future__ import annotations

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

_LOGGER_NAME = "ram_monitor"
_LOGGER_INITIALIZED = False
_LOGGER: Optional[logging.Logger] = None


def get_logger() -> logging.Logger:
    """Return the shared logger. Initializes on first call.

    Debug verbosity is enabled when `RAM_MONITOR_DEBUG=1` is set in the
    environment. Otherwise only WARNING+ messages reach stdout, and no
    file is written.
    """
    global _LOGGER_INITIALIZED, _LOGGER
    if _LOGGER_INITIALIZED and _LOGGER is not None:
        return _LOGGER

    logger = logging.getLogger(_LOGGER_NAME)
    debug = os.environ.get("RAM_MONITOR_DEBUG", "").lower() in ("1", "true", "yes")
    logger.setLevel(logging.DEBUG if debug else logging.WARNING)

    # Always log to stderr — useful when launched from a console.
    try:
        stderr_handler = logging.StreamHandler(stream=sys.stderr)
        stderr_handler.setLevel(logging.DEBUG if debug else logging.WARNING)
        stderr_handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        )
        logger.addHandler(stderr_handler)
    except Exception:  # pragma: no cover — defensive
        pass

    # Optional rotating file handler — only in debug mode.
    if debug:
        try:
            log_dir = Path(os.environ.get(
                "RAM_MONITOR_LOG_DIR",
                Path.home() / ".ram_monitor" / "logs",
            ))
            log_dir.mkdir(parents=True, exist_ok=True)
            file_handler = RotatingFileHandler(
                log_dir / "ram_monitor.log",
                maxBytes=1_000_000,
                backupCount=1,
                encoding="utf-8",
            )
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(
                logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
            )
            logger.addHandler(file_handler)
        except Exception:  # pragma: no cover — defensive
            pass

    logger.propagate = False
    _LOGGER = logger
    _LOGGER_INITIALIZED = True
    return logger
