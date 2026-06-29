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
build.bat
```

Produces `dist\RAMMonitor.exe` — a single, console-less executable that runs
on any Windows 11 / 10 x64 machine with no Python pre-installed.

---

## Screens / Layout

```
┌──────────────────────────────────────────────────────────┐
│  RAM Monitor                                  ─  □  ✕    │
├──────────────────────────────────────────────────────────┤
│  ┌────────┐ ┌──────────┐ ┌────────┐ ┌──────────┐         │
│  │ RAM    │ │ RAM Used │ │ CPU    │ │ Processes│         │
│  │ 50.0%  │ │ 4.00 GB  │ │ 12.3%  │ │ 142      │         │
│  │ ▓▓▓▓░░ │ │          │ │ ▓▓░░░░ │ │ up 01:01 │         │
│  └────────┘ └──────────┘ └────────┘ └──────────┘         │
│                                                          │
│  ┌────────────────────┐  ┌────────────────────┐          │
│  │ RAM History        │  │ CPU History        │          │
│  │     ╱╲    ╱╲╱      │  │   ╱╲  ╱╲╲          │          │
│  │  ╱╲╱  ╲╱╲╱  ╲╲╲    │  │ ╱╲╱  ╲╱  ╲╲╲       │          │
│  └────────────────────┘  └────────────────────┘          │
│                                                          │
│  TOP PROCESSES                                           │
│  ┌──────────────────────────────────────────────────┐    │
│  │ chrome.exe      2.15 GB   26.9%   ↑ +550 MB       │    │
│  │ code.exe        850 MB    10.6%   ↓ -128 MB       │    │
│  │ explorer.exe    120 MB     1.5%   — 0 B            │    │
│  └──────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────┘
```

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
├── core/
│   ├── models.py          # SystemMetrics, ProcessInfo (frozen, slotted)
│   ├── metrics.py         # MetricsCollector — pure psutil wrapper
│   └── monitor.py         # MonitorWorker(QThread)
├── ui/
│   ├── styles.py          # Windows 11 dark QSS
│   ├── stats_cards.py     # StatCard (animated meter)
│   ├── charts.py          # HistoryChart (pyqtgraph + bounded ring)
│   ├── process_panel.py   # TopProcessesPanel (QTableWidget)
│   ├── dashboard.py       # DashboardView composition
│   └── main_window.py     # QMainWindow, owns worker
└── utils/
    ├── formatters.py      # bytes / percent / uptime / delta formatters
    └── logger.py          # Rotating-file logger, opt-in via RAM_MONITOR_DEBUG=1
```

---

## Performance Budget

| Resource              | Budget    | Achieved (typical)  |
|-----------------------|-----------|---------------------|
| App RAM (idle, 1 h)   | < 60 MB   | ~35–45 MB           |
| App CPU (idle)        | < 1 %     | ~0.4–0.6 %          |
| UI thread blocking    | 0 ms      | 0 ms                |
| Memory leaks          | 0         | 0                   |

Verified by:
* `pytest tests/` — 49 unit + integration tests, all green.
* `scripts/smoke_test_window.py` — constructs the full MainWindow offscreen,
  pushes two metrics ticks, asserts charts and cards updated, closes cleanly.

---

## Configuration

All tunables live in [`src/ram_monitor/config.py`](./src/ram_monitor/config.py).
Override the `Config` dataclass and pass it to `run(config=...)` to change:

* `poll_interval_seconds` — sampling cadence (default 1.5).
* `history_length` — chart buffer size (default 60 samples ≈ 90 s).
* `top_processes_count` — rows in the process table (default 8).
* `process_state_ceiling` — hard cap on `prev_mem` (default 256).
* All colors — Windows 11 dark palette by default.

### Debug logging

```bash
# Enable rotating-file debug logs at ~/.ram_monitor/logs/ram_monitor.log
RAM_MONITOR_DEBUG=1 python -m ram_monitor
```

Logs are **off by default** in the shipped binary.

---

## Testing

```bash
pytest -v
```

Covers:
* `utils.formatters` — all format functions, edge cases (NaN, negatives, None).
* `core.models` — immutability, slots, delta direction logic.
* `core.metrics.MetricsCollector` — pure logic via a fake psutil (delta math,
  top-N sort, dead-PID eviction, zero-rss filtering, ceiling bounding) plus
  a live smoke test against the host's real psutil.
* `core.monitor.MonitorWorker` — signal delivery end-to-end on a real QThread.

---

## Packaging

```bat
build.bat
```

The script:
1. Verifies Python + PyInstaller + runtime deps are installed.
2. Invokes PyInstaller in `--onefile --noconsole` mode.
3. Excludes dev-only modules (`pytest`, `unittest`, `tkinter`, `tests`) to
   shrink the bundle.
4. Emits `dist\RAMMonitor.exe` — typically 35–50 MB.

To produce a smaller bundle, edit `build.bat` and switch `--onefile` to
`--onedir` (faster startup, smaller per-file overhead).

---

## FAQ

**Q: Why no RAM cleaner?**  
A: Because they don't work. Modern Windows already aggressively pages unused
memory; "cleaners" either force that paging early (slowing the next launch of
every app) or simply allocate-and-free a huge block to make the *available*
number go up briefly. `RAM Monitor` exists to **show** you the truth, not to
lie to you about it.

**Q: Why is the chart only 90 seconds?**  
A: Because that's enough to see the effect of an action (open/close an app)
and short enough to keep the y-axis visually meaningful. Longer history would
compress the curve until individual events disappear. Override
`Config.history_length` if you want more.

**Q: Why does the first `cpu_percent` reading sometimes show 0?**  
A: That's a psutil contract — the very first call after import has no baseline
to compare against, so it returns 0. We prime it once during `MonitorWorker`
construction so the user never sees it.

---

## License

MIT — see `setup.py`.
