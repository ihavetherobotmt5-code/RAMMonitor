# RAM Monitor

> A lightweight, **observe-only** Windows 11 desktop monitor for RAM and CPU.
> No popups, no dialogs, no RAM cleaning — just quiet, beautiful indicators.

---

## Why

`RAM Monitor` is built for users with low-end hardware (8 GB RAM) who want to
**understand** how their everyday actions — opening Chrome, launching VS Code,
closing an app — affect system memory in real time. It does not modify, clean,
or "optimize" anything. It only shows you the truth.

* 🎯 **Strict observer** — never cleans RAM, never pops up dialogs.
* ⚡ **Tiny footprint** — `< 60 MB RAM`, `< 1% CPU`, zero leaks.
* 🪟 **Windows 11 native** — dark title bar, rounded corners, Fusion palette.
* 📈 **Real-time charts** — 90 s scrolling history at 1.5 s cadence.
* 📊 **Top processes** — live table with per-process **memory delta** since
  the last tick, color-coded (red ↑ grew, green ↓ shrank).

---

## Quick Start

### From source (development)

```bash
# 1. Create a venv (Python 3.11+)
python -m venv .venv
.venv\Scripts\activate            # Windows
# source .venv/bin/activate       # macOS / Linux

# 2. Install in editable mode + dev deps
pip install -e ".[dev]"

# 3. Run the app
python -m ram_monitor

# 4. Run the test suite
pytest -v
```

### From a Windows .exe (end users)

```bat
build\build.bat
```

Produces `dist\RAMMonitor.exe` — a single, console-less executable that runs
on any Windows 11 / 10 x64 machine with no Python pre-installed.

---

## Architecture

`RAM Monitor` follows a strict **core / UI boundary** so the monitoring engine
can be unit-tested headlessly on any platform.

```
┌──────────────────────┐    signal    ┌──────────────────────┐
│  MonitorWorker       │  ─────────>  │  MainWindow          │
│  (QThread)           │              │  ─ DashboardView     │
│   ─ MetricsCollector │              │    ─ StatCard × 4    │
│     (psutil wrapper) │              │    ─ HistoryChart ×2 │
│   ─ bounded state    │              │    ─ TopProcessesPanel│
└──────────────────────┘              └──────────────────────┘
        ▲                                      ▲
        │ imports                              │ imports
        │                                      │
   psutil only                            PySide6 + pyqtgraph only
```

Key design decisions (full rationale in [`ROADMAP.md`](./ROADMAP.md)):

| Decision | Why |
|----------|-----|
| 1.5 s polling interval | Balances "instant" feel with the < 1% CPU budget. |
| `psutil.process_iter(attrs=[...])` | Single batched syscall — one walk of the process table per tick. |
| Bounded ring buffers (`deque(maxlen=60)`) | Memory stays flat over days of uptime. |
| `prev_mem` dict capped at 256 entries | Cannot grow unboundedly as PIDs churn. |
| Frozen, slotted dataclasses | No accidental mutation; ~40% smaller per-instance footprint. |
| `QThread` + `pyqtSignal` | Lock-free cross-thread delivery; Qt marshals for us. |
| `MainWindow.closeEvent` → `request_stop` + `wait(2000)` | Guaranteed clean shutdown; no orphan threads. |

### Module Layout

```
src/ram_monitor/
├── __init__.py
├── __main__.py            # `python -m ram_monitor`
├── app.py                 # QApplication bootstrap, Windows 11 dark title bar
├── config.py              # All tunables
├── core/                  # FROZEN — monitoring engine
│   ├── models.py          # SystemMetrics, ProcessInfo (frozen, slotted)
│   ├── metrics.py         # MetricsCollector — pure psutil wrapper
│   └── monitor.py         # MonitorWorker(QThread)
├── ui/
│   ├── styles.py          # Windows 11 dark QSS (token-driven)
│   ├── stats_cards.py     # StatCard (ring meter + smart animation)
│   ├── charts.py          # HistoryChart (pyqtgraph + bounded ring)
│   ├── process_panel.py   # TopProcessesPanel (QTableWidget)
│   ├── dashboard.py       # DashboardView composition
│   ├── main_window.py     # QMainWindow, owns worker
│   ├── fluent_theme.py    # Fluent Design tokens (pure data)
│   ├── responsive_grid.py # 4-breakpoint reflow layout
│   ├── compact_mode.py    # Always-on-top floating monitor (M2-5)
│   └── settings.py        # Persistent config via QSettings (M2-9)
└── utils/
    ├── formatters.py      # bytes / percent / uptime / delta formatters
    └── logger.py          # Rotating-file logger, opt-in via RAM_MONITOR_DEBUG=1
```

---

## M2 Features (Version 2.0)

1. **Status ring colors** — Green (<60%), Amber (60-85%), Red (>85%)
2. **Gradient charts** — Anti-aliased lines with gradient area fills
3. **Interactive charts** — Crosshair + tooltip on hover
4. **Dashboard layout** — Section headers, 5 breakpoints (720→3440px)
5. **Compact mode** — Ctrl+M toggles always-on-top floating monitor
6. **Theme refinement** — Hover/pressed/disabled states, improved contrast
7. **Animation audit** — Zero per-tick allocations verified
8. **Accessibility** — Keyboard nav (Tab, Ctrl+M, Ctrl+Q), focus indicators
9. **Settings architecture** — Persistent config via QSettings
10. **Packaging** — PyInstaller spec with M2 hidden imports, manifest, icon

---

## Performance Budget

| Resource              | Budget    | Achieved (typical)  |
|-----------------------|-----------|---------------------|
| App RAM (idle, 1 h)   | < 60 MB   | ~35–45 MB (Windows) |
| App CPU (idle)        | < 1 %     | ~0.3–0.4 %          |
| UI thread blocking    | 0 ms      | 0 ms                |
| Memory leaks          | 0         | 0                   |

---

## Configuration

All tunables live in [`src/ram_monitor/config.py`](./src/ram_monitor/config.py).
Override the `Config` dataclass and pass it to `run(config=...)` to change:

* `poll_interval_seconds` — sampling cadence (default 1.5).
* `history_length` — chart buffer size (default 60 samples ≈ 90 s).
* `top_processes_count` — rows in the process table (default 8).
* `animation_threshold_pct` — animate only when |delta| > this % (default 2.0).
* All colors — Windows 11 dark palette by default.

### Debug logging

```bash
# Enable rotating-file debug logs
RAM_MONITOR_DEBUG=1 python -m ram_monitor
```

On Windows, logs go to `%LOCALAPPDATA%\RAMMonitor\logs\ram_monitor.log`.
On Linux/macOS, logs go to `~/.ram_monitor/logs/ram_monitor.log`.

---

## Testing

```bash
pytest -v
```

146 tests covering formatters, models, metrics (with fake psutil), monitor
signal plumbing, fluent theme tokens, stat cards, responsive grid, compact
mode, interactive charts, animation audit, and settings.

---

## Packaging

```bat
build\build.bat
```

The script:
1. Verifies Python + PyInstaller + runtime deps are installed.
2. Invokes PyInstaller via `build\RAMMonitor.spec`.
3. Bundles:
   * Custom application icon (`assets\rammonitor.ico`)
   * Application manifest (`assets\rammonitor.exe.manifest` — PerMonitor V2 DPI)
   * Win32 version resources (`build\version_info.txt`)
   * All M1+M2 modules via hidden imports
4. Emits `dist\RAMMonitor.exe` — typically 35–50 MB.

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+M` | Toggle compact mode (floating mini-monitor) |
| `Ctrl+Q` | Quit application |

---

## License

MIT — see [LICENSE](./LICENSE).
