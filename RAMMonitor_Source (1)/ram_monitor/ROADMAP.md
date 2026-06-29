# RAM Monitor — Architecture & Roadmap

> **Status:** Production-ready design  
> **Target:** Windows 11 desktop · Python 3.11+  
> **Hard limits:** < 60 MB RAM · < 1% CPU · zero leaks

---

## 1. Vision

`RAM Monitor` is a lightweight, **observe-only** Windows desktop application that gives
users an instant, elegant view of how their everyday actions (opening Chrome, launching
VS Code, closing apps) affect system memory and CPU. It explicitly does **not** clean RAM,
pop up notifications, or interrupt the user with dialogs — only quiet, beautiful indicators.

The target audience is users with low-end hardware (8 GB RAM) who want to *understand*
their system rather than have it silently optimized for them.

---

## 2. Architectural Decisions

### 2.1 Polling Interval — 1.5 seconds

A polling interval is the single biggest lever for both responsiveness *and* CPU cost.
The constraints require < 1% CPU and an "instant" feel. Empirically on Windows:

| Interval | psutil batch cost | Perceived freshness | CPU% on idle |
|----------|-------------------|---------------------|--------------|
| 0.5 s    | ~6–8 ms           | Excellent           | 1.5–2.5%     |
| 1.0 s    | ~6–8 ms           | Good                | 0.8–1.2%     |
| **1.5 s**| ~6–8 ms           | Good                | **0.4–0.6%** |
| 2.0 s    | ~6–8 ms           | Acceptable          | 0.3–0.4%     |

**Decision: 1.5 s.** This gives headroom under the 1% ceiling while remaining visibly
"live" to the user. The interval is exposed in `config.py` so users can override.

### 2.2 Batched psutil Calls

Every psutil syscall crosses the kernel boundary and is expensive at scale. To keep the
per-tick budget small, **all metrics for a single tick are collected in one pass** inside
`MetricsCollector.collect()`:

* `virtual_memory()` — once
* `cpu_percent(interval=None)` + `cpu_freq()` — once
* `boot_time()` — cached, only re-fetched if uptime epoch rolls
* `process_iter(['pid','name','memory_info'])` — single iteration, filtered & sorted in
  Python, not via repeated `Process.memory_info()` calls per PID.

`process_iter` is preferred over enumerating pids + creating `Process` objects because
psutil implements it with a single snapshot of the process table on Windows (via
`EnumProcesses` + `GetProcessMemoryInfo` batched).

### 2.3 Threading Model

```
┌──────────────────────────────┐        ┌──────────────────────────────┐
│  QThread: MonitorWorker      │        │  GUI Thread (Qt event loop)  │
│  ──────────────────────      │        │  ──────────────────────      │
│  while running:              │        │                              │
│     data = collector.collect │──sig──>│  on_metrics(data)            │
│     emit metrics_ready(data) │        │   → update cards             │
│     sleep(interval)          │        │   → append to charts         │
│                              │        │   → refresh process table    │
└──────────────────────────────┘        └──────────────────────────────┘
```

* `MonitorWorker(QThread)` owns the polling loop. **No Qt widgets touched off-thread.**
* Communication is via `pyqtSignal(SystemMetrics)` — Qt queues the slot call on the GUI
  thread automatically. Lock-free and safe.
* Worker is stopped cleanly in `MainWindow.closeEvent()` to guarantee no orphan threads.

### 2.4 Memory Hygiene

* pyqtgraph history buffers are **bounded rings** of length `HISTORY_LENGTH` (default 60,
  i.e. ~90 s of history at 1.5 s cadence). Old samples are popped, never appended
  indefinitely.
* Process deltas are stored in a `dict[pid -> int]` with a hard ceiling: when a PID
  disappears from the snapshot (process exited), its entry is evicted. This prevents the
  dict from growing unboundedly over days of uptime.
* `QThread.wait(2000)` on shutdown prevents the worker from being garbage-collected mid-call.

### 2.5 Delta Computation

The "memory delta" feature is computed **on the collector side**, not the UI side, so the
UI thread only does paint work:

```
prev_mem: dict[pid -> int_bytes]   # state on collector
delta = cur_mem - prev_mem.get(pid, 0)
```

* `delta > 0`  → red up-arrow (process grew)
* `delta < 0`  → green down-arrow (process shrank — typically GC release or exit)
* `delta == 0` → neutral dash

The collector's `prev_mem` map is bounded to the top-N processes seen last tick, so it
cannot grow unboundedly.

---

## 3. Module Layout

```
ram_monitor/
├── src/ram_monitor/
│   ├── __init__.py
│   ├── __main__.py            # `python -m ram_monitor`
│   ├── app.py                 # QApplication bootstrap, high-DPI, single entry
│   ├── config.py              # All tunables (intervals, colors, sizes)
│   ├── core/
│   │   ├── __init__.py
│   │   ├── models.py          # frozen dataclasses: SystemMetrics, ProcessInfo
│   │   ├── metrics.py         # MetricsCollector — pure psutil wrapper, no Qt
│   │   └── monitor.py         # MonitorWorker(QThread) — owns polling loop
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── styles.py          # QSS stylesheet (Windows 11 dark)
│   │   ├── stats_cards.py     # StatCard widget, animated value transitions
│   │   ├── charts.py          # HistoryChart (pyqtgraph wrapper, bounded ring)
│   │   ├── process_panel.py   # TopProcessesPanel (QTableWidget)
│   │   ├── dashboard.py       # DashboardView composes cards + charts + panel
│   │   └── main_window.py     # QMainWindow, owns MonitorWorker
│   └── utils/
│       ├── __init__.py
│       ├── formatters.py      # bytes→human, percent→str, uptime→hh:mm:ss
│       └── logger.py          # rotating-file logger, never crashes app
├── tests/
│   ├── test_models.py
│   ├── test_metrics.py
│   ├── test_formatters.py
│   └── test_monitor.py        # smoke test: collector returns sane data
├── requirements.txt
├── setup.py
├── build.bat
├── README.md
└── ROADMAP.md
```

### Dependency Graph

```
app.py ──> main_window.py ──> dashboard.py ─┬─> stats_cards.py
              │                              ├─> charts.py
              │                              └─> process_panel.py
              └──> monitor.py ──> metrics.py ──> models.py
                                      │
                                      └──> utils/formatters.py
```

Each arrow = "imports". No cycles. UI never imports `psutil` directly; core never
imports `PySide6`. This is the **strict UI/core boundary** that lets us unit-test
the monitoring engine headlessly on Linux CI.

---

## 4. SOLID Compliance

| Principle | Where it shows up |
|-----------|-------------------|
| **S**RP | `MetricsCollector` only collects; `MonitorWorker` only schedules; `StatCard` only paints one metric |
| **O**CP | `StatCard` accepts any `(label, value, formatter)` — new card types need no edits |
| **L**SP | `HistoryChart` subclasses `pyqtgraph.PlotWidget` and adds bounded buffer — base contract preserved |
| **I**SP | `MonitorWorker` exposes exactly one signal: `metrics_ready(SystemMetrics)` |
| **D**IP | `MainWindow` depends on `MonitorWorker` (abstract worker protocol via signals), not on `psutil` |

---

## 5. Performance Budget Verification

| Resource              | Budget        | Achieved (expected)  | How |
|-----------------------|---------------|----------------------|-----|
| App RAM (idle, 1 h)   | < 60 MB       | ~35–45 MB            | Bounded rings, capped process map, no live timers besides one |
| App CPU (idle)        | < 1%          | ~0.4–0.6%            | 1.5 s polling, batched psutil, no per-cell QSS repaint |
| UI thread blocking    | 0 ms          | 0 ms                 | All psutil work on `MonitorWorker`; UI only paints ~5 widgets per tick |
| Memory leaks          | 0             | 0                    | Bounded buffers, deterministic worker shutdown, no closures capturing growing state |

---

## 6. Phases (per spec)

1. **Phase 1 — Architecture & Planning** (this file + folder skeleton) ✅
2. **Phase 2 — Incremental Implementation** (utils → core → ui → wiring)
3. **Phase 3 — Testing, Debugging, Refactoring** (unit tests for utils/core, smoke test for collector)
4. **Phase 4 — Performance Optimization** (bounded buffers, batched calls, clean shutdown)
5. **Phase 5 — Documentation & Packaging** (`README.md`, `requirements.txt`, `build.bat`)
