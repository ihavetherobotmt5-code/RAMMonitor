# RAM Monitor V2 — Architecture

**Version:** 2.0.0
**Date:** 2026-06-29

---

## Overview

RAM Monitor is a lightweight, observe-only Windows desktop resource monitor built on PySide6 + pyqtgraph + psutil. The architecture enforces a strict boundary between the **monitoring engine** (frozen since V1) and the **presentation layer** (evolved through M1+M2).

```
┌─────────────────────────────────────────────────────────────┐
│                         app.py                               │
│  QApplication bootstrap, DWM dark title bar, font setup      │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    MainWindow (QMainWindow)                  │
│  Owns: MonitorWorker + DashboardView + CompactModeWindow     │
│  Shortcuts: Ctrl+M (compact), Ctrl+Q (quit)                  │
│  closeEvent → request_stop + wait(2000)                      │
└──────┬──────────────────────┬───────────────────┬───────────┘
       │                      │                   │
       ▼                      ▼                   ▼
┌──────────────┐   ┌──────────────────┐  ┌──────────────────┐
│ MonitorWorker │   │  DashboardView   │  │ CompactModeWindow│
│  (QThread)    │   │  (QWidget)       │  │ (QWidget, AOT)   │
│               │   │                  │  │                  │
│ metrics_ready │──▶│ apply_metrics()  │  │ apply_metrics()  │
│ collection_err│   │  ├─ 4 StatCards  │  │  ├─ RAM value    │
│ request_stop()│   │  ├─ 2 Charts     │  │  └─ CPU value    │
│               │   │  ├─ ProcessPanel │  │                  │
└──────┬────────┘   │  └─ ResponsiveGrid│  └──────────────────┘
       │            └──────────────────┘
       ▼
┌──────────────────────────────┐
│    MetricsCollector           │
│  collect() → SystemMetrics    │
│  (psutil wrapper — ONLY       │
│   place that imports psutil)  │
│  Bounded prev_mem dict (256)  │
└──────────────────────────────┘
```

## Layer Separation

### Core Layer (FROZEN — do not modify)

| Module | Responsibility |
|--------|---------------|
| `core/models.py` | Frozen dataclasses: `SystemMetrics`, `ProcessInfo` |
| `core/metrics.py` | `MetricsCollector` — pure psutil wrapper, no Qt |
| `core/monitor.py` | `MonitorWorker(QThread)` — polling loop, signals |

**Rule:** The core layer has ZERO Qt imports (except `QThread`/`Signal` in monitor.py). It can be unit-tested headlessly on any platform.

### UI Layer (evolved in M1+M2)

| Module | Responsibility |
|--------|---------------|
| `ui/fluent_theme.py` | Design tokens (colors, typography, radii, spacing, breakpoints) — pure data, no Qt |
| `ui/styles.py` | QSS stylesheet generated from tokens |
| `ui/stats_cards.py` | `StatCard` + `_RingMeter` — status-colored ring meter, smart animation |
| `ui/charts.py` | `HistoryChart` — gradient fill, AA, crosshair, tooltip |
| `ui/dashboard.py` | `DashboardView` — composes cards + charts + panel |
| `ui/responsive_grid.py` | `ResponsiveGridLayout` — 5-breakpoint reflow (sm/md/lg/xl/xxl) |
| `ui/main_window.py` | `MainWindow` — owns worker, compact mode, shortcuts |
| `ui/compact_mode.py` | `CompactModeWindow` — always-on-top floating monitor |
| `ui/settings.py` | `SettingsManager` — persistent config via QSettings |
| `ui/process_panel.py` | `TopProcessesPanel` — live process table |

### Utils Layer

| Module | Responsibility |
|--------|---------------|
| `utils/formatters.py` | Pure functions: format_bytes, format_percent, format_uptime, format_delta |
| `utils/logger.py` | Rotating-file logger, platform-aware paths |

## Data Flow

```
MonitorWorker.run()                    [background thread]
  │
  ├─ MetricsCollector.collect()        [psutil syscalls]
  │    └─ returns SystemMetrics (frozen dataclass)
  │
  ├─ emit metrics_ready(metrics)       [Qt signal, QueuedConnection]
  │
  └─ sleep(poll_interval)              [threading.Event.wait]
                    │
                    ▼  [GUI thread, queued]
  MainWindow._on_metrics(metrics)
  │
  ├─ DashboardView.apply_metrics(metrics)
  │    ├─ StatCard.set_value()         [smart animation if delta > 2%]
  │    ├─ HistoryChart.push()          [skip if unchanged]
  │    └─ TopProcessesPanel.update_processes()
  │
  └─ CompactModeWindow.apply_metrics(metrics)
       └─ self.update()                [repaint only this widget]
```

## Signal/Slot Map

| Signal | Emitter | Receiver | Connection |
|--------|---------|----------|------------|
| `metrics_ready(object)` | `MonitorWorker` | `MainWindow._on_metrics` | QueuedConnection |
| `metrics_ready(object)` | `MonitorWorker` | `CompactModeWindow.apply_metrics` | QueuedConnection |
| `collection_error(str)` | `MonitorWorker` | `MainWindow._on_error` | QueuedConnection |
| `valueChanged` | `_RingMeter._anim` | `_RingMeter.update` | Direct (bound method) |
| `sigMouseMoved` | `HistoryChart.scene()` | `HistoryChart._on_mouse_moved` | Direct |

## Threading Model

- **Main thread:** Qt event loop, all UI widgets, paint events
- **Worker thread:** `MonitorWorker.run()` — psutil polling, never touches widgets
- **Communication:** `pyqtSignal` with `Qt.QueuedConnection` — lock-free, thread-safe
- **Shutdown:** `request_stop()` sets `threading.Event` → worker exits → `wait(2000)` → fallback `terminate()`

## Performance Architecture

| Technique | Where | Effect |
|-----------|-------|--------|
| `WA_OpaquePaintEvent` | StatCard, _RingMeter, DashboardView | Eliminates parent repaint cascade |
| Cached QFont/QPen/QGradient | _RingMeter.__init__ | Zero per-paint allocations |
| Single reused QPropertyAnimation | _RingMeter.__init__ | Zero per-tick allocations (93.6% reduction) |
| Smart animation threshold | StatCard.set_value | Skips animation on noise (<2% delta) |
| Skip-if-unchanged | HistoryChart.push | Eliminates ~50% of chart repaints at idle |
| Bounded deque(maxlen=60) | HistoryChart | Memory flat over days of uptime |
| Bounded prev_mem (256) | MetricsCollector | Prevents dict growth over long uptimes |
| Cached ys array | HistoryChart._ys_cached | O(1) tooltip lookup, zero mouse-event allocations |
