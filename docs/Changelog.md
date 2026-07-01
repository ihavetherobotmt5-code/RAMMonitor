# Changelog

All notable changes to RAM Monitor are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [2.0.0] — 2026-06-29

### Milestone 2 — Visual Data Improvements

#### Added
- **Status-aware stat cards** — Ring meters now show green (<60%), amber (60-85%), red (>85%) based on usage tier. Three cached value-pens per ring, zero paint-event allocations.
- **Gradient charts** — History charts feature anti-aliased lines with gradient area fills (accent color fading to transparent). Cached QLinearGradient, no per-push allocations.
- **Interactive charts** — Hover crosshair (dashed vertical line) + tooltip showing relative time and value (e.g., "−45s: 62.4%"). Event-driven via `sigMouseMoved`, zero allocations per mouse event. Auto-hides on mouse leave.
- **Section headers** — Dashboard now has "Overview", "Performance History", and "Top Processes" section titles for visual hierarchy.
- **Ultra-wide support** — New `xxl` breakpoint (≥2560px) with `content_max_width=1600` token prevents cards from stretching on 3440px monitors.
- **Compact Mode** — `Ctrl+M` toggles a 180×80px always-on-top floating window showing RAM% and CPU%. Draggable, remembers position via QSettings, shares the same MonitorWorker signal (no duplicate polling).
- **Hover/pressed/disabled states** — Cards visually respond to mouse interaction with elevation changes (`surface_elevated` on hover, `surface_alt` on pressed).
- **Keyboard shortcuts** — `Ctrl+M` (compact mode), `Ctrl+Q` (quit).
- **Focus indicators** — Cards show 2px accent border when focused via Tab key.
- **Accessible names** — All QLabels have `setAccessibleName()` for screen reader support.
- **Settings architecture** — `SettingsManager` class persists user preferences (poll interval, animation threshold, history length, window size) via QSettings. Windows: registry; Linux: ~/.config/RAMMonitor.conf.
- **5-breakpoint responsive grid** — sm (<700), md (700-899), lg (900-1279), xl (1280-2559), xxl (≥2560).

#### Changed
- **Card value font** — Increased from 20px to 28px (weight 700 bold) for commercial-grade hierarchy.
- **CPU color** — Changed from `#9CDCFE` (light blue, too similar to RAM) to `#FFB85C` (amber) for instant visual distinction.
- **Background contrast** — Darkened bg from `#1F1F1F` to `#1A1A1A`, lightened surface from `#2B2B2B` to `#2D2D2D` for clearer elevation.
- **Stroke opacity** — Increased from 0.06 to 0.08 (border) and 0.12 to 0.18 (top highlight) for visible card outlines.
- **Card height** — Reduced from 110px to 90px (charts are more important).
- **Chart height** — Increased from 180px to 240px (charts are the visual centerpiece).
- **Layout spacing** — Replaced hardcoded 20px/14px with theme tokens (`spacing.xl=24`, `spacing.lg=16`).
- **Log path** — Now uses `%LOCALAPPDATA%\RAMMonitor\logs` on Windows (was `~/.ram_monitor/logs`).

#### Removed
- **Ring center text** — Removed redundant percentage text inside the ring (the card value label already shows it).
- **"INSIGHTS — coming in Milestone 3" placeholder** — Removed debug placeholder text. The reserved cell is now empty (None) until M3.
- **Dead code** — Removed `_build_shadow_pixmap` stub, unused `FillBetweenItem`, unused `QIcon` import.

#### Fixed
- **Law of Demeter** — `DashboardView` no longer accesses `StatCard._ring` / `StatCard._meter` directly. Added `set_ring_visible(bool)` and `set_meter_visible(bool)` public methods.
- **QPropertyAnimation accumulation** — Single animation instance reused per `_RingMeter` (was creating new ones per tick). 93.6% allocation reduction.
- **Paint cascade** — `WA_OpaquePaintEvent` set on all custom-painted widgets. MainWindow paints went from 102/50ticks to 0.
- **PyInstaller spec paths** — Fixed SPECPATH resolution so spec works from any working directory.

---

## [1.0.0] — 2026-06-28

### Milestone 1 — Fluent UI Foundation

#### Added
- **Fluent Design token system** — 7 token groups (Colors, Typography, Radii, Spacing, Elevation, Animation, Breakpoints). Pure data, no Qt imports.
- **StatCard with ring meter** — Circular gradient ring meter + horizontal progress bar + label/value/sub-text. Smart animation (only animates when |delta| > 2%).
- **ResponsiveGridLayout** — 4-breakpoint reflow (sm/md/lg/xl) with single persistent QGridLayout.
- **MainWindow with QSplitter** — Reserved 0-width sidebar slot for M4.
- **18 theme tests, 20 stats_cards tests, 17 responsive_grid tests** — 55 new tests total.

#### Changed
- All QSS generated from FluentTheme tokens — zero magic numbers in widget code.
- Card radii increased from 8px to 12px (WinUI 3 spec).
- 1px top highlight on cards (Windows 11 "light from above" cue).

#### Fixed
- Layout teardown segfault — switched from layout-tree rebuild to single persistent QGridLayout.
- EventFilter crash on stale `_host` — added `getattr` guard.

---

## [0.9.0] — 2026-06-28

### Initial Release (V1)

#### Added
- `MetricsCollector` — pure psutil wrapper, batched process_iter, bounded prev_mem (256 entries).
- `MonitorWorker(QThread)` — polling loop with threading.Event stop signal.
- `SystemMetrics` / `ProcessInfo` — frozen, slotted dataclasses.
- `HistoryChart` — pyqtgraph wrapper with bounded deque(maxlen=60).
- `TopProcessesPanel` — live process table with color-coded delta arrows.
- `DashboardView` — composes 4 cards + 2 charts + process table.
- `MainWindow` — owns worker, clean closeEvent.
- 49 tests covering formatters, models, metrics (with fake psutil), monitor signal plumbing.
