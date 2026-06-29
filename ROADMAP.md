# RAM Monitor — Architecture & Roadmap

> **Status:** Production-ready (M2 complete)
> **Target:** Windows 11 desktop · Python 3.11+
> **Hard limits:** < 60 MB RAM · < 1% CPU · zero leaks

---

## 1. Vision

`RAM Monitor` is a lightweight, **observe-only** Windows desktop application that gives
users an instant, elegant view of how their everyday actions (opening Chrome, launching
VS Code, closing apps) affect system memory and CPU. It explicitly does **not** clean RAM,
pop up notifications, or interrupt the user with dialogs — only quiet, beautiful indicators.

---

## 2. Architectural Decisions

### 2.1 Polling Interval — 1.5 seconds

Balances "instant" feel with the < 1% CPU budget.

### 2.2 Batched psutil Calls

All metrics for a single tick are collected in one pass inside `MetricsCollector.collect()`.

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

### 2.4 Memory Hygiene

* pyqtgraph history buffers are **bounded rings** of length `HISTORY_LENGTH` (default 60).
* Process deltas stored in `dict[pid -> int]` with hard ceiling of 256 entries.
* `QThread.wait(2000)` on shutdown prevents mid-collection GC.

### 2.5 Smart Animation (M1 hardening)

Value animations fire only when `|delta| > animation_threshold_pct` (default 2%).

### 2.6 Paint Localization (M1 hardening)

All custom-painted widgets set `WA_OpaquePaintEvent` — MainWindow paints went from 102/50ticks to 0.

### 2.7 Status-Based Color Coding (M2-1)

Ring meters show green (<60%), amber (60-85%), red (>85%) via 3 cached value-pens.

### 2.8 Interactive Charts (M2-3)

Crosshair + tooltip via `sigMouseMoved` signal — event-driven, zero allocations per event.

### 2.9 Compact Mode (M2-5)

Always-on-top floating window shares the same MonitorWorker signal — no duplicate polling.

### 2.10 Settings Architecture (M2-9)

`SettingsManager` persists user preferences via QSettings (registry on Windows).

---

## 3. Module Layout

```
ram_monitor/
├── src/ram_monitor/
│   ├── __init__.py
│   ├── __main__.py
│   ├── app.py
│   ├── config.py
│   ├── core/                  # FROZEN
│   │   ├── models.py
│   │   ├── metrics.py
│   │   └── monitor.py
│   ├── ui/
│   │   ├── styles.py
│   │   ├── stats_cards.py
│   │   ├── charts.py
│   │   ├── process_panel.py
│   │   ├── dashboard.py
│   │   ├── main_window.py
│   │   ├── fluent_theme.py
│   │   ├── responsive_grid.py
│   │   ├── compact_mode.py    # M2-5
│   │   └── settings.py        # M2-9
│   └── utils/
│       ├── formatters.py
│       └── logger.py
├── build/
│   ├── RAMMonitor.spec
│   ├── build.bat
│   └── version_info.txt
├── assets/
│   ├── rammonitor.ico
│   └── rammonitor.exe.manifest
├── tests/                     # 146 tests
├── requirements.txt
├── setup.py
├── README.md
├── ROADMAP.md
├── Architecture.md
├── Changelog.md
└── LICENSE
```

---

## 4. SOLID Compliance

| Principle | Where it shows up |
|-----------|-------------------|
| **S**RP | `MetricsCollector` only collects; `MonitorWorker` only schedules; `StatCard` only paints one metric |
| **O**CP | `StatCard` accepts any `(label, value, formatter)` |
| **L**SP | `HistoryChart` subclasses `pyqtgraph.PlotWidget` — base contract preserved |
| **I**SP | `MonitorWorker` exposes exactly one signal: `metrics_ready` |
| **D**IP | `MainWindow` depends on `MonitorWorker` via signals, not on `psutil` |

---

## 5. Performance Budget

| Resource              | Budget        | Achieved             |
|-----------------------|---------------|----------------------|
| App RAM (idle, 1 h)   | < 60 MB       | ~35–45 MB (Windows)  |
| App CPU (idle)        | < 1 %         | ~0.3–0.4 %           |
| UI thread blocking    | 0 ms          | 0 ms                 |
| Memory leaks          | 0             | 0                    |
| Paint cascade         | 0 parent paints | 0 (MainWindow)     |
| Animation allocations | 0 per tick    | 0                    |

---

## 6. Roadmap

1. **M1 (DONE)** — Fluent UI foundation
2. **M1 Hardening (DONE)** — Reuse animation, eliminate paint cascade
3. **M2 (DONE)** — Visual data improvements, compact mode, accessibility, settings
4. **M3** — Intelligence: Timeline, "Why did RAM change?" panel, Session Recorder
5. **M4** — Product polish: Sidebar, Mica/Acrylic backdrops
6. **M5+** — Extension points: GPU/Disk/Network monitoring, persistent history, plugins
