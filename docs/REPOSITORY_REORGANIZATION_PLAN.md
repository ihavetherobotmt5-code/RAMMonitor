# REPOSITORY_REORGANIZATION_PLAN.md

**RAM Monitor V2 — Authoritative Migration Guide**
**Created:** 2026-07-01
**Author:** GLM-5.2 Agent

---

## SECTION 1: OBJECTIVE

### Why Reorganization Is Necessary

The RAM Monitor V2 project was developed across multiple conversation sessions. During these sessions, the Linux container workspace was partially reset — `src/ram_monitor/` (all 22 Python source modules) and `tests/` (all 15 test files) were lost. Only root-level documentation, build infrastructure, and asset files survived the reset.

Evidence: Current workspace — `find . -type f` shows 14 files present, with `src/` and `tests/` directories entirely absent.

Additionally, the project has never been pushed to GitHub. The intended repository `https://github.com/ihavetherobotmt5-code/RAMMonitor` exists but contains no code.

Evidence: Previous verified output — `git push` failed due to no GITHUB_TOKEN, no SSH keys, no `gh` CLI.

### What Problem It Solves

The reorganization accomplishes two goals:
1. Reconstruct the complete V2 source tree in the local workspace so the project is functional again (146 tests pass).
2. Establish the correct repository structure so that when the code is pushed to GitHub, the layout is correct, clean, and immediately buildable on Windows.

Evidence: Current workspace — missing `src/` and `tests/` prevent any import, test, or build from working.

### Desired End State

A repository at `/home/z/my-project/ram_monitor/` (and eventually `https://github.com/ihavetherobotmt5-code/RAMMonitor`) containing:

- 22 Python source modules under `src/ram_monitor/` (4 core, 11 ui, 3 utils, 4 root)
- 15 test files under `tests/` (146 tests total)
- 3 build files under `build/`
- 2 asset files under `assets/`
- 1 script under `scripts/`
- 7 root-level documentation/config files
- `.gitignore` excluding `.venv/`, `__pycache__/`, `.pyc`, `.pytest_cache/`, `dist/`, `build/RAMMonitor/`, `*.egg-info/`

Evidence: Previously recovered file — the complete file tree was verified multiple times in prior conversation turns with 146 passing tests.

### What Success Looks Like

1. `find . -type f -not -path "./.venv/*" -not -path "./.git/*" | wc -l` returns 50+ files (currently 14)
2. `LD_LIBRARY_PATH=/home/z/.local/lib QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/ -v` shows "146 passed"
3. `scripts/smoke_test_window.py` prints "SMOKE OK"
4. `git diff --stat -- src/ram_monitor/core/` is empty (frozen engine unchanged)
5. `git status` is clean after committing

Evidence: Previous verified output — these exact commands were run successfully in prior sessions with 146 passed and SMOKE OK.

---

## SECTION 2: CURRENT REPOSITORY STATE

### 2.1 Verified Files

| File Path | Last Known State | Verification Method | Evidence |
|---|---|---|---|
| `Architecture.md` | 133 lines, 7,312 bytes — complete architecture doc | `cat` command output | Current workspace |
| `Changelog.md` | 85 lines, 5,736 bytes — full version history | `cat` command output | Current workspace |
| `HANDOVER_DOCUMENT.md` | 1,138 lines, 48 KB — complete handover doc | `Write` tool created it | Current workspace |
| `LICENSE` | 21 lines, MIT license | `cat` command output | Current workspace |
| `README.md` | 216 lines — user documentation with M2 features | `cat` command output | Current workspace |
| `ROADMAP.md` | 212 lines — architecture roadmap | `cat` command output | Current workspace |
| `requirements.txt` | 9 lines — PySide6, psutil, pyqtgraph, numpy, pyinstaller, pytest | `cat` command output | Current workspace |
| `setup.py` | 51 lines — pip install metadata, v2.0.0 | `cat` command output | Current workspace |
| `assets/rammonitor.exe.manifest` | 57 lines, valid XML — PerMonitorV2 DPI, UTF-8, Win10/11 | `cat` + XML parse | Current workspace |
| `assets/rammonitor.ico` | 1,917 bytes, binary — 4 icons (16/32/48/256 RGBA) | `file` command + `generate_icon.py` | Current workspace |
| `build/RAMMonitor.spec` | 85 lines, valid Python — PyInstaller spec with SPECPATH fix | `cat` + `ast.parse` | Current workspace |
| `build/build.bat` | 74 lines — Windows build script | `cat` command output | Current workspace |
| `build/version_info.txt` | 39 lines, valid Python — Win32 version resource v2.0.0.0 | `cat` + `compile()` | Current workspace |
| `scripts/generate_icon.py` | 65 lines — Pillow-based icon generator | `cat` command output | Current workspace |

### 2.2 Missing Files

| Expected Path | Original Purpose | Last Known Location | Might Exist on GitHub? | Evidence |
|---|---|---|---|---|
| `src/ram_monitor/__init__.py` | Package marker, `__version__ = "2.0.0"` | Written in conversation, lost on reset | No — never pushed | Current workspace (directory absent) |
| `src/ram_monitor/__main__.py` | Entry point: `python -m ram_monitor` | Written in conversation, lost on reset | No | Current workspace |
| `src/ram_monitor/app.py` | QApplication bootstrap, DWM dark title bar | Written in conversation, lost on reset | No | Current workspace |
| `src/ram_monitor/config.py` | Frozen Config dataclass with all tunables | Written in conversation, lost on reset | No | Current workspace |
| `src/ram_monitor/core/__init__.py` | Exports ProcessInfo, SystemMetrics | Written in conversation, lost on reset | No | Current workspace |
| `src/ram_monitor/core/models.py` | Frozen slotted dataclasses (FROZEN engine) | Written in conversation, lost on reset | No | Current workspace |
| `src/ram_monitor/core/metrics.py` | MetricsCollector — psutil wrapper (FROZEN engine) | Written in conversation, lost on reset | No | Current workspace |
| `src/ram_monitor/core/monitor.py` | MonitorWorker(QThread) (FROZEN engine) | Written in conversation, lost on reset | No | Current workspace |
| `src/ram_monitor/ui/__init__.py` | UI package marker | Written in conversation, lost on reset | No | Current workspace |
| `src/ram_monitor/ui/fluent_theme.py` | Fluent Design tokens (pure data, no Qt) | Written in conversation, lost on reset | No | Current workspace |
| `src/ram_monitor/ui/styles.py` | QSS stylesheet from tokens | Written in conversation, lost on reset | No | Current workspace |
| `src/ram_monitor/ui/stats_cards.py` | StatCard + _RingMeter with status colors | Written in conversation, lost on reset | No | Current workspace |
| `src/ram_monitor/ui/charts.py` | HistoryChart with gradient, AA, crosshair, tooltip | Written in conversation, lost on reset | No | Current workspace |
| `src/ram_monitor/ui/dashboard.py` | DashboardView with section headers | Written in conversation, lost on reset | No | Current workspace |
| `src/ram_monitor/ui/responsive_grid.py` | 5-breakpoint responsive layout | Written in conversation, lost on reset | No | Current workspace |
| `src/ram_monitor/ui/main_window.py` | MainWindow with compact mode + shortcuts | Written in conversation, lost on reset | No | Current workspace |
| `src/ram_monitor/ui/compact_mode.py` | Always-on-top floating monitor | Written in conversation, lost on reset | No | Current workspace |
| `src/ram_monitor/ui/settings.py` | SettingsManager (QSettings) | Written in conversation, lost on reset | No | Current workspace |
| `src/ram_monitor/ui/process_panel.py` | TopProcessesPanel (QTableWidget) | Written in conversation, lost on reset | No | Current workspace |
| `src/ram_monitor/utils/__init__.py` | Utils package marker | Written in conversation, lost on reset | No | Current workspace |
| `src/ram_monitor/utils/formatters.py` | Pure format functions | Written in conversation, lost on reset | No | Current workspace |
| `src/ram_monitor/utils/logger.py` | Rotating-file logger, platform-aware paths | Written in conversation, lost on reset | No | Current workspace |
| `tests/__init__.py` | Tests package marker | Written in conversation, lost on reset | No | Current workspace |
| `tests/conftest.py` | sys.path setup for src/ | Written in conversation, lost on reset | No | Current workspace |
| `tests/test_fluent_theme.py` | 18 tests — token consistency | Written in conversation, lost on reset | No | Current workspace |
| `tests/test_formatters.py` | 25 tests — format functions | Written in conversation, lost on reset | No | Current workspace |
| `tests/test_logger.py` | 6 tests — platform-aware log paths | Written in conversation, lost on reset | No | Current workspace |
| `tests/test_m2_animation_audit.py` | 6 tests — animation audit | Written in conversation, lost on reset | No | Current workspace |
| `tests/test_m2_compact_mode.py` | 7 tests — compact mode | Written in conversation, lost on reset | No | Current workspace |
| `tests/test_m2_interactive_charts.py` | 11 tests — crosshair + tooltip | Written in conversation, lost on reset | No | Current workspace |
| `tests/test_m2_settings.py` | 6 tests — settings roundtrip | Written in conversation, lost on reset | No | Current workspace |
| `tests/test_m2_status_colors.py` | 6 tests — status ring colors | Written in conversation, lost on reset | No | Current workspace |
| `tests/test_metrics.py` | 13 tests — MetricsCollector with fake psutil | Written in conversation, lost on reset | No | Current workspace |
| `tests/test_models.py` | 11 tests — frozen dataclasses | Written in conversation, lost on reset | No | Current workspace |
| `tests/test_monitor.py` | 2 tests — signal plumbing | Written in conversation, lost on reset | No | Current workspace |
| `tests/test_responsive_grid.py` | 17 tests — reflow behavior | Written in conversation, lost on reset | No | Current workspace |
| `tests/test_stats_cards.py` | 20 tests — StatCard API + animation | Written in conversation, lost on reset | No | Current workspace |
| `.gitignore` | Excludes .venv, __pycache__, .pyc, etc. | Written in conversation, may have been lost | No | Current workspace (not present in file listing) |

### 2.3 Unknown Files

| File | Why Unknown | Evidence |
|---|---|---|
| `.gitignore` | Not visible in current `find` output. May have existed in a prior git commit but lost during workspace reset. | Evidence: None — Needs verification |
| Any files in GitHub repository `ihavetherobotmt5-code/RAMMonitor` | The GitHub repository was created but never populated with code. Contents unknown. | Evidence: None — Needs GitHub verification |

### 2.4 Files Requiring GitHub Verification

| File Name | Expected Location | Verification Needed | Evidence |
|---|---|---|---|
| Any file in `https://github.com/ihavetherobotmt5-code/RAMMonitor` | Repository root | Clone the repository and inspect contents. The repo may be empty or may contain an initial README. | Evidence: None — Needs GitHub verification |
| `.gitignore` | Repository root | Check if `.gitignore` was committed in a prior session. | Evidence: None — Needs GitHub verification |

**Explicitly stated:** All items above **Needs GitHub verification.**

---

## SECTION 3: TARGET REPOSITORY LAYOUT

```
ram_monitor/
├── src/                                    # Source code (src/ layout)
│   └── ram_monitor/                        # Python package
│       ├── __init__.py                     # Package marker, __version__="2.0.0"
│       │   Evidence: Previously recovered file
│       ├── __main__.py                     # Entry point: python -m ram_monitor
│       │   Evidence: Previously recovered file
│       ├── app.py                          # QApplication bootstrap, DWM dark title bar
│       │   Evidence: Previously recovered file
│       ├── config.py                       # Frozen Config dataclass
│       │   Evidence: Previously recovered file
│       ├── core/                           # FROZEN monitoring engine — never modify
│       │   ├── __init__.py                 # Exports ProcessInfo, SystemMetrics
│       │   │   Evidence: Previously recovered file
│       │   ├── models.py                   # Frozen slotted dataclasses
│       │   │   Evidence: Previously recovered file
│       │   ├── metrics.py                  # MetricsCollector (psutil wrapper)
│       │   │   Evidence: Previously recovered file
│       │   └── monitor.py                  # MonitorWorker(QThread)
│       │       Evidence: Previously recovered file
│       ├── ui/                             # Presentation layer (PySide6)
│       │   ├── __init__.py                 # Package marker
│       │   │   Evidence: Previously recovered file
│       │   ├── fluent_theme.py             # Design tokens (pure data, no Qt)
│       │   │   Evidence: Previously recovered file
│       │   ├── styles.py                   # QSS from tokens
│       │   │   Evidence: Previously recovered file
│       │   ├── stats_cards.py              # StatCard + _RingMeter
│       │   │   Evidence: Previously recovered file
│       │   ├── charts.py                   # HistoryChart with crosshair
│       │   │   Evidence: Previously recovered file
│       │   ├── process_panel.py            # TopProcessesPanel
│       │   │   Evidence: Previously recovered file
│       │   ├── dashboard.py               # DashboardView
│       │   │   Evidence: Previously recovered file
│       │   ├── responsive_grid.py          # 5-breakpoint layout
│       │   │   Evidence: Previously recovered file
│       │   ├── main_window.py              # MainWindow with compact mode
│       │   │   Evidence: Previously recovered file
│       │   ├── compact_mode.py             # Always-on-top floating monitor
│       │   │   Evidence: Previously recovered file
│       │   └── settings.py                 # SettingsManager (QSettings)
│       │       Evidence: Previously recovered file
│       └── utils/                          # Pure Python helpers
│           ├── __init__.py                 # Package marker
│           │   Evidence: Previously recovered file
│           ├── formatters.py               # format_bytes, format_percent, etc.
│           │   Evidence: Previously recovered file
│           └── logger.py                   # Rotating-file logger, platform-aware
│               Evidence: Previously recovered file
├── tests/                                  # 146 tests
│   ├── __init__.py                         # Package marker
│   │   Evidence: Previously recovered file
│   ├── conftest.py                         # sys.path setup
│   │   Evidence: Previously recovered file
│   ├── test_fluent_theme.py                # 18 tests
│   │   Evidence: Previously recovered file
│   ├── test_formatters.py                  # 25 tests
│   │   Evidence: Previously recovered file
│   ├── test_logger.py                      # 6 tests
│   │   Evidence: Previously recovered file
│   ├── test_m2_animation_audit.py          # 6 tests
│   │   Evidence: Previously recovered file
│   ├── test_m2_compact_mode.py             # 7 tests
│   │   Evidence: Previously recovered file
│   ├── test_m2_interactive_charts.py       # 11 tests
│   │   Evidence: Previously recovered file
│   ├── test_m2_settings.py                 # 6 tests
│   │   Evidence: Previously recovered file
│   ├── test_m2_status_colors.py            # 6 tests
│   │   Evidence: Previously recovered file
│   ├── test_metrics.py                     # 13 tests
│   │   Evidence: Previously recovered file
│   ├── test_models.py                      # 11 tests
│   │   Evidence: Previously recovered file
│   ├── test_monitor.py                     # 2 tests
│   │   Evidence: Previously recovered file
│   ├── test_responsive_grid.py             # 17 tests
│   │   Evidence: Previously recovered file
│   └── test_stats_cards.py                 # 20 tests
│       Evidence: Previously recovered file
├── build/                                  # Build infrastructure
│   ├── RAMMonitor.spec                     # PyInstaller spec
│   │   Evidence: Current workspace
│   ├── build.bat                           # Windows build script
│   │   Evidence: Current workspace
│   └── version_info.txt                    # Win32 version resources
│       Evidence: Current workspace
├── assets/                                 # Binary resources
│   ├── rammonitor.ico                      # Multi-resolution icon
│   │   Evidence: Current workspace
│   └── rammonitor.exe.manifest             # PerMonitorV2 DPI manifest
│       Evidence: Current workspace
├── scripts/                                # Developer tools
│   └── generate_icon.py                    # Icon generator (Pillow)
│       Evidence: Current workspace
├── .gitignore                              # Git exclusions
│   Evidence: None — Needs GitHub verification
├── requirements.txt                        # Python dependencies
│   Evidence: Current workspace
├── setup.py                                # pip install metadata
│   Evidence: Current workspace
├── README.md                               # User documentation
│   Evidence: Current workspace
├── ROADMAP.md                              # Architecture roadmap
│   Evidence: Current workspace
├── Architecture.md                         # Detailed architecture
│   Evidence: Current workspace
├── Changelog.md                            # Version history
│   Evidence: Current workspace
├── HANDOVER_DOCUMENT.md                    # Technical handover
│   Evidence: Current workspace
├── REPOSITORY_REORGANIZATION_PLAN.md       # This document
│   Evidence: Current workspace
└── LICENSE                                 # MIT license
    Evidence: Current workspace
```

---

## SECTION 4: FILE CLASSIFICATION

### 4.1 Files That Should Remain Unchanged

| File Path | Current Location | Target Location | Confidence | Evidence | Notes |
|---|---|---|---|---|---|
| `Architecture.md` | Root | Root | Verified | Current workspace | Do not modify |
| `Changelog.md` | Root | Root | Verified | Current workspace | Do not modify |
| `HANDOVER_DOCUMENT.md` | Root | Root | Verified | Current workspace | Do not modify |
| `LICENSE` | Root | Root | Verified | Current workspace | Legal file, never modify |
| `README.md` | Root | Root | Verified | Current workspace | Do not modify |
| `ROADMAP.md` | Root | Root | Verified | Current workspace | Do not modify |
| `requirements.txt` | Root | Root | Verified | Current workspace | Do not modify |
| `setup.py` | Root | Root | Verified | Current workspace | Do not modify |
| `assets/rammonitor.exe.manifest` | `assets/` | `assets/` | Verified | Current workspace | Do not modify |
| `assets/rammonitor.ico` | `assets/` | `assets/` | Verified | Current workspace | Binary, do not modify |
| `build/RAMMonitor.spec` | `build/` | `build/` | Verified | Current workspace | Do not modify |
| `build/build.bat` | `build/` | `build/` | Verified | Current workspace | Do not modify |
| `build/version_info.txt` | `build/` | `build/` | Verified | Current workspace | Do not modify |
| `scripts/generate_icon.py` | `scripts/` | `scripts/` | Verified | Current workspace | Do not modify |

### 4.2 Files That Should Be Moved

No files need to be moved. All verified files are already in their correct target locations.

Evidence: Current workspace — file listing shows all present files in correct directories.

### 4.3 Files That Should Be Renamed

No files need to be renamed.

Evidence: Current workspace — all filenames match the target layout.

### 4.4 Files That Should Be Compared Before Replacement

| File Path | Location A | Location B | Comparison Method | Confidence | Evidence | Notes |
|---|---|---|---|---|---|---|
| `.gitignore` | Current workspace (missing) | Conversation history (content known) | Recreate from conversation, compare with any GitHub version | Needs GitHub verification | Current workspace | If `.gitignore` exists on GitHub, compare before overwriting |

### 4.5 New V2 Files (Must Be Recreated)

| File Path | Purpose | Source | Confidence | Evidence | Notes |
|---|---|---|---|---|---|
| `src/ram_monitor/__init__.py` | Package marker | Conversation history | Verified | Previously recovered file | Recreate from conversation |
| `src/ram_monitor/__main__.py` | Entry point | Conversation history | Verified | Previously recovered file | Recreate from conversation |
| `src/ram_monitor/app.py` | QApplication bootstrap | Conversation history | Verified | Previously recovered file | Recreate from conversation |
| `src/ram_monitor/config.py` | Config dataclass | Conversation history | Verified | Previously recovered file | Recreate from conversation |
| `src/ram_monitor/core/__init__.py` | Core package marker | Conversation history | Verified | Previously recovered file | Recreate from conversation |
| `src/ram_monitor/core/models.py` | Frozen dataclasses (FROZEN) | Conversation history | Verified | Previously recovered file | Recreate from conversation, NEVER modify |
| `src/ram_monitor/core/metrics.py` | MetricsCollector (FROZEN) | Conversation history | Verified | Previously recovered file | Recreate from conversation, NEVER modify |
| `src/ram_monitor/core/monitor.py` | MonitorWorker (FROZEN) | Conversation history | Verified | Previously recovered file | Recreate from conversation, NEVER modify |
| `src/ram_monitor/ui/__init__.py` | UI package marker | Conversation history | Verified | Previously recovered file | Recreate from conversation |
| `src/ram_monitor/ui/fluent_theme.py` | Design tokens | Conversation history | Verified | Previously recovered file | Recreate from conversation |
| `src/ram_monitor/ui/styles.py` | QSS from tokens | Conversation history | Verified | Previously recovered file | Recreate from conversation |
| `src/ram_monitor/ui/stats_cards.py` | StatCard + _RingMeter | Conversation history | Verified | Previously recovered file | Recreate from conversation |
| `src/ram_monitor/ui/charts.py` | HistoryChart | Conversation history | Verified | Previously recovered file | Recreate from conversation |
| `src/ram_monitor/ui/dashboard.py` | DashboardView | Conversation history | Verified | Previously recovered file | Recreate from conversation |
| `src/ram_monitor/ui/responsive_grid.py` | Responsive layout | Conversation history | Verified | Previously recovered file | Recreate from conversation |
| `src/ram_monitor/ui/main_window.py` | MainWindow | Conversation history | Verified | Previously recovered file | Recreate from conversation |
| `src/ram_monitor/ui/compact_mode.py` | Compact mode window | Conversation history | Verified | Previously recovered file | Recreate from conversation |
| `src/ram_monitor/ui/settings.py` | SettingsManager | Conversation history | Verified | Previously recovered file | Recreate from conversation |
| `src/ram_monitor/ui/process_panel.py` | TopProcessesPanel | Conversation history | Verified | Previously recovered file | Recreate from conversation |
| `src/ram_monitor/utils/__init__.py` | Utils package marker | Conversation history | Verified | Previously recovered file | Recreate from conversation |
| `src/ram_monitor/utils/formatters.py` | Format functions | Conversation history | Verified | Previously recovered file | Recreate from conversation |
| `src/ram_monitor/utils/logger.py` | Logger | Conversation history | Verified | Previously recovered file | Recreate from conversation |
| `tests/__init__.py` | Tests package marker | Conversation history | Verified | Previously recovered file | Recreate from conversation |
| `tests/conftest.py` | sys.path setup | Conversation history | Verified | Previously recovered file | Recreate from conversation |
| `tests/test_fluent_theme.py` | 18 tests | Conversation history | Verified | Previously recovered file | Recreate from conversation |
| `tests/test_formatters.py` | 25 tests | Conversation history | Verified | Previously recovered file | Recreate from conversation |
| `tests/test_logger.py` | 6 tests | Conversation history | Verified | Previously recovered file | Recreate from conversation |
| `tests/test_m2_animation_audit.py` | 6 tests | Conversation history | Verified | Previously recovered file | Recreate from conversation |
| `tests/test_m2_compact_mode.py` | 7 tests | Conversation history | Verified | Previously recovered file | Recreate from conversation |
| `tests/test_m2_interactive_charts.py` | 11 tests | Conversation history | Verified | Previously recovered file | Recreate from conversation |
| `tests/test_m2_settings.py` | 6 tests | Conversation history | Verified | Previously recovered file | Recreate from conversation |
| `tests/test_m2_status_colors.py` | 6 tests | Conversation history | Verified | Previously recovered file | Recreate from conversation |
| `tests/test_metrics.py` | 13 tests | Conversation history | Verified | Previously recovered file | Recreate from conversation |
| `tests/test_models.py` | 11 tests | Conversation history | Verified | Previously recovered file | Recreate from conversation |
| `tests/test_monitor.py` | 2 tests | Conversation history | Verified | Previously recovered file | Recreate from conversation |
| `tests/test_responsive_grid.py` | 17 tests | Conversation history | Verified | Previously recovered file | Recreate from conversation |
| `tests/test_stats_cards.py` | 20 tests | Conversation history | Verified | Previously recovered file | Recreate from conversation |

### 4.6 Generated Files

| File Pattern | Generated By | Should Be Versioned? | Evidence | Notes |
|---|---|---|---|---|
| `.venv/` | `python -m venv .venv` | No | Current workspace | Python virtual environment |
| `__pycache__/` | Python interpreter | No | Current workspace | Bytecode cache |
| `*.pyc` | Python interpreter | No | Current workspace | Compiled bytecode |
| `.pytest_cache/` | pytest | No | Current workspace | Test cache |
| `dist/` | PyInstaller | No | Previous verified output | Build output |
| `build/RAMMonitor/` | PyInstaller | No | Previous verified output | Work directory |
| `src/ram_monitor.egg-info/` | `pip install -e .` | No | Previous verified output | Package metadata |
| `assets/rammonitor.ico` | `scripts/generate_icon.py` | Yes (binary asset) | Current workspace | Generated but should be versioned |

### 4.7 Binary Files

| File Path | Type | Purpose | Confidence | Evidence | Notes |
|---|---|---|---|---|---|
| `assets/rammonitor.ico` | MS Windows icon resource | Application icon (16/32/48/256 RGBA) | Verified | Current workspace | Generated by `scripts/generate_icon.py` using Pillow. Can be regenerated if lost. |

### 4.8 Files That Must Not Be Modified During Repository Reorganization

| File Path | Reason | Evidence |
|---|---|---|
| `src/ram_monitor/core/models.py` | FROZEN monitoring engine — byte-identical to V1 | Previously verified output — git diff showed 0 changes across all M2 commits |
| `src/ram_monitor/core/metrics.py` | FROZEN monitoring engine | Previously verified output — git diff showed 0 changes |
| `src/ram_monitor/core/monitor.py` | FROZEN monitoring engine | Previously verified output — git diff showed 0 changes |
| `src/ram_monitor/core/__init__.py` | FROZEN monitoring engine | Previously verified output |
| `LICENSE` | Legal file | Current workspace |
| `README.md` | Project documentation | Current workspace |
| `ROADMAP.md` | Architecture documentation | Current workspace |
| `requirements.txt` | Dependency list | Current workspace |
| `setup.py` | Package configuration | Current workspace |
| `build/RAMMonitor.spec` | PyInstaller spec — contains SPECPATH fix | Current workspace |
| `build/build.bat` | Windows build script | Current workspace |
| `build/version_info.txt` | Win32 version resources | Current workspace |
| `assets/rammonitor.exe.manifest` | Windows manifest — PerMonitorV2 DPI | Current workspace |
| `assets/rammonitor.ico` | Binary icon asset | Current workspace |
| `scripts/generate_icon.py` | Icon generation script | Current workspace |

---

## SECTION 5: MIGRATION STRATEGY

### Step-by-Step Sequence

**Step 1: Create directory structure**
```
mkdir -p src/ram_monitor/core src/ram_monitor/ui src/ram_monitor/utils tests
```
Rationale: All source and test directories are missing. Must create before writing files.
Dependencies: None.
Safety check: `ls -d src/ram_monitor/core src/ram_monitor/ui src/ram_monitor/utils tests` — all 4 directories must exist.
Evidence: Current workspace — directories confirmed absent.

**Step 2: Write core/ files (4 files)**
Write `__init__.py`, `models.py`, `metrics.py`, `monitor.py` to `src/ram_monitor/core/`.
Rationale: Core engine is the foundation — all other modules depend on it. Must exist first.
Dependencies: Step 1 (directories must exist).
Safety check: `python -c "from ram_monitor.core.models import SystemMetrics; print('OK')"` — must print OK.
Evidence: Previously recovered file — all 4 files were verified functional.

**Step 3: Write utils/ files (3 files)**
Write `__init__.py`, `formatters.py`, `logger.py` to `src/ram_monitor/utils/`.
Rationale: Utils have no Qt imports and can be tested immediately after writing.
Dependencies: Step 1.
Safety check: `python -c "from ram_monitor.utils.formatters import format_bytes; print(format_bytes(1024))"` — must print "1.00 KiB".
Evidence: Previously recovered file.

**Step 4: Write root source files (4 files)**
Write `__init__.py`, `__main__.py`, `app.py`, `config.py` to `src/ram_monitor/`.
Rationale: These are the package marker, entry point, bootstrap, and config.
Dependencies: Steps 2, 3 (app.py imports from core and utils).
Safety check: `python -c "from ram_monitor.config import CONFIG; print(CONFIG.poll_interval_seconds)"` — must print 1.5.
Evidence: Previously recovered file.

**Step 5: Write ui/ files (11 files)**
Write all 11 UI modules to `src/ram_monitor/ui/`.
Rationale: UI layer depends on core, config, utils, and fluent_theme (which is in ui/).
Dependencies: Steps 2, 3, 4.
Safety check: `python -c "from ram_monitor.ui.fluent_theme import FluentTheme; print(FluentTheme.default().colors.accent)"` — must print #60CDFF.
Evidence: Previously recovered file.

**Step 6: Write test files (15 files)**
Write all 15 test files to `tests/`.
Rationale: Tests verify all source files are correct.
Dependencies: Steps 2-5 (all source must exist).
Safety check: `pytest tests/test_formatters.py -v` — must show 25 passed.
Evidence: Previously recovered file.

**Step 7: Write .gitignore**
Create `.gitignore` with exclusions for `.venv/`, `__pycache__/`, `*.pyc`, `.pytest_cache/`, `dist/`, `build/RAMMonitor/`, `*.egg-info/`.
Rationale: Prevents generated files from being committed.
Dependencies: None.
Safety check: `cat .gitignore` — must contain `.venv/`.
Evidence: Previously recovered file — .gitignore was written in a prior session.

**Step 8: Create venv and install dependencies**
```
python -m venv .venv
.venv/bin/pip install -e ".[dev]"
```
Rationale: Required to run tests.
Dependencies: Steps 2-6 (source must exist for `pip install -e .`).
Safety check: `.venv/bin/python -c "import psutil, PySide6, pyqtgraph, numpy; print('OK')"` — must print OK.
Evidence: Previous verified output — this exact sequence was run successfully before.

**Step 9: Set up Qt environment (Linux only)**
```
mkdir -p /home/z/.local/lib
ln -sf /home/z/.cache/ms-playwright/chromium-1228/chrome-linux64/libEGL.so /home/z/.local/lib/libEGL.so.1
ln -sf /home/z/.cache/ms-playwright/chromium-1228/chrome-linux64/libGLESv2.so /home/z/.local/lib/libGLESv2.so.1
```
Rationale: PySide6 requires libEGL.so.1 which is not installed on the container.
Dependencies: None.
Safety check: `LD_LIBRARY_PATH=/home/z/.local/lib python -c "import PySide6.QtWidgets; print('OK')"` — must print OK.
Evidence: Previous verified output — this symlink was required every session.

**Step 10: Run full test suite**
```
LD_LIBRARY_PATH=/home/z/.local/lib QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/ -v
```
Rationale: Verifies all 146 tests pass after reconstruction.
Dependencies: Steps 2-9.
Safety check: Output must show "146 passed".
Evidence: Previous verified output — 146 passed was confirmed multiple times.

**Step 11: Run smoke test**
```
LD_LIBRARY_PATH=/home/z/.local/lib QT_QPA_PLATFORM=offscreen .venv/bin/python scripts/smoke_test_window.py
```
Rationale: Verifies the application constructs and runs.
Dependencies: Steps 2-10.
Safety check: Output must show "SMOKE OK".
Evidence: Previous verified output.

**Step 12: Verify core/ is unchanged**
```
git diff --stat -- src/ram_monitor/core/
```
Rationale: Confirms the frozen monitoring engine was not accidentally modified.
Dependencies: Step 10.
Safety check: Output must be empty.
Evidence: Previous verified output — git diff was empty across all M2 commits.

**Step 13: Git commit**
```
git add -A
git commit -m "Reconstruct RAM Monitor V2 — all source + tests"
```
Rationale: Creates a checkpoint.
Dependencies: Steps 2-12.
Safety check: `git status` must show "nothing to commit, working tree clean".
Evidence: Current workspace — git repo exists on branch main.

### Rollback Strategy

If any step fails:
1. `git checkout -- .` — reverts all uncommitted changes
2. `git clean -fd` — removes untracked files (recreated source)
3. Re-examine the error, fix the specific file, re-run from the failed step

If git has no commits yet (fresh repo):
1. Delete the specific file that caused the error
2. Rewrite it from the conversation history
3. Re-run the validation step

Evidence: Standard git operations — `git checkout` and `git clean` are safe rollback commands.

---

## SECTION 6: GIT COMMIT PLAN

```
Commit 1: Create directory structure + .gitignore
Evidence: Current workspace — directories are missing, .gitignore may be missing
- mkdir -p src/ram_monitor/core src/ram_monitor/ui src/ram_monitor/utils tests
- Write .gitignore with .venv/, __pycache__/, *.pyc, .pytest_cache/, dist/, build/RAMMonitor/, *.egg-info/
- git add -A
- git commit -m "Create directory structure and .gitignore"

Commit 2: Restore core/ monitoring engine (FROZEN)
Evidence: Previously recovered file — core/ is frozen since V1
- Write src/ram_monitor/core/__init__.py
- Write src/ram_monitor/core/models.py
- Write src/ram_monitor/core/metrics.py
- Write src/ram_monitor/core/monitor.py
- git add src/ram_monitor/core/
- git commit -m "Restore frozen core/ monitoring engine (models, metrics, monitor)"

Commit 3: Restore utils/ helpers
Evidence: Previously recovered file — utils are pure Python, no Qt
- Write src/ram_monitor/utils/__init__.py
- Write src/ram_monitor/utils/formatters.py
- Write src/ram_monitor/utils/logger.py
- git add src/ram_monitor/utils/
- git commit -m "Restore utils/ (formatters, logger with platform-aware paths)"

Commit 4: Restore root source files
Evidence: Previously recovered file
- Write src/ram_monitor/__init__.py
- Write src/ram_monitor/__main__.py
- Write src/ram_monitor/app.py
- Write src/ram_monitor/config.py
- git add src/ram_monitor/__init__.py src/ram_monitor/__main__.py src/ram_monitor/app.py src/ram_monitor/config.py
- git commit -m "Restore root source (package marker, entry point, app bootstrap, config)"

Commit 5: Restore ui/ layer (11 modules)
Evidence: Previously recovered file — all 11 UI modules were verified
- Write src/ram_monitor/ui/__init__.py
- Write src/ram_monitor/ui/fluent_theme.py
- Write src/ram_monitor/ui/styles.py
- Write src/ram_monitor/ui/stats_cards.py
- Write src/ram_monitor/ui/charts.py
- Write src/ram_monitor/ui/process_panel.py
- Write src/ram_monitor/ui/dashboard.py
- Write src/ram_monitor/ui/responsive_grid.py
- Write src/ram_monitor/ui/main_window.py
- Write src/ram_monitor/ui/compact_mode.py
- Write src/ram_monitor/ui/settings.py
- git add src/ram_monitor/ui/
- git commit -m "Restore ui/ layer (fluent_theme, styles, stats_cards, charts, dashboard, responsive_grid, main_window, compact_mode, settings, process_panel)"

Commit 6: Restore tests/ (15 files, 146 tests)
Evidence: Previously recovered file — 146 tests verified passing
- Write all 15 test files to tests/
- git add tests/
- git commit -m "Restore tests/ (146 tests — formatters, models, metrics, monitor, fluent_theme, logger, stats_cards, responsive_grid, M2 features)"

Commit 7: Final verification commit
Evidence: Previous verified output — 146 passed + SMOKE OK
- Run pytest tests/ -v → expect 146 passed
- Run smoke_test_window.py → expect SMOKE OK
- Run git diff --stat -- src/ram_monitor/core/ → expect empty
- git add -A (if any .gitignore or minor changes)
- git commit -m "Verified: 146 tests pass, smoke OK, core/ unchanged"
```

---

## SECTION 7: IMPORT VERIFICATION

| Import Statement | Original File | Expected New Location | Verification Method | Evidence |
|---|---|---|---|---|
| `from ram_monitor.app import run` | `__main__.py` | `src/ram_monitor/app.py` | `python -c "from ram_monitor.app import run"` | Previously recovered file |
| `from ram_monitor.config import CONFIG, Config` | Multiple files | `src/ram_monitor/config.py` | `python -c "from ram_monitor.config import CONFIG"` | Previously recovered file |
| `from ram_monitor.core.models import ProcessInfo, SystemMetrics` | Multiple files | `src/ram_monitor/core/models.py` | `python -c "from ram_monitor.core.models import SystemMetrics"` | Previously recovered file |
| `from ram_monitor.core.metrics import MetricsCollector` | `monitor.py`, `main_window.py` | `src/ram_monitor/core/metrics.py` | `python -c "from ram_monitor.core.metrics import MetricsCollector"` | Previously recovered file |
| `from ram_monitor.core.monitor import MonitorWorker` | `main_window.py` | `src/ram_monitor/core/monitor.py` | `python -c "from ram_monitor.core.monitor import MonitorWorker"` | Previously recovered file |
| `from ram_monitor.ui.fluent_theme import FluentTheme` | Multiple files | `src/ram_monitor/ui/fluent_theme.py` | `python -c "from ram_monitor.ui.fluent_theme import FluentTheme"` | Previously recovered file |
| `from ram_monitor.ui.styles import build_stylesheet` | `app.py` | `src/ram_monitor/ui/styles.py` | `python -c "from ram_monitor.ui.styles import build_stylesheet"` | Previously recovered file |
| `from ram_monitor.ui.stats_cards import StatCard` | `dashboard.py` | `src/ram_monitor/ui/stats_cards.py` | `python -c "from ram_monitor.ui.stats_cards import StatCard"` | Previously recovered file |
| `from ram_monitor.ui.charts import HistoryChart` | `dashboard.py` | `src/ram_monitor/ui/charts.py` | `python -c "from ram_monitor.ui.charts import HistoryChart"` | Previously recovered file |
| `from ram_monitor.ui.dashboard import DashboardView` | `main_window.py` | `src/ram_monitor/ui/dashboard.py` | `python -c "from ram_monitor.ui.dashboard import DashboardView"` | Previously recovered file |
| `from ram_monitor.ui.responsive_grid import ResponsiveGridLayout` | `dashboard.py` | `src/ram_monitor/ui/responsive_grid.py` | `python -c "from ram_monitor.ui.responsive_grid import ResponsiveGridLayout"` | Previously recovered file |
| `from ram_monitor.ui.main_window import MainWindow` | `app.py` | `src/ram_monitor/ui/main_window.py` | `python -c "from ram_monitor.ui.main_window import MainWindow"` | Previously recovered file |
| `from ram_monitor.ui.compact_mode import CompactModeWindow` | `main_window.py` | `src/ram_monitor/ui/compact_mode.py` | `python -c "from ram_monitor.ui.compact_mode import CompactModeWindow"` | Previously recovered file |
| `from ram_monitor.ui.settings import SettingsManager` | Test files | `src/ram_monitor/ui/settings.py` | `python -c "from ram_monitor.ui.settings import SettingsManager"` | Previously recovered file |
| `from ram_monitor.ui.process_panel import TopProcessesPanel` | `dashboard.py` | `src/ram_monitor/ui/process_panel.py` | `python -c "from ram_monitor.ui.process_panel import TopProcessesPanel"` | Previously recovered file |
| `from ram_monitor.utils.formatters import format_bytes, format_percent` | Multiple files | `src/ram_monitor/utils/formatters.py` | `python -c "from ram_monitor.utils.formatters import format_bytes"` | Previously recovered file |
| `from ram_monitor.utils.logger import get_logger` | Multiple files | `src/ram_monitor/utils/logger.py` | `python -c "from ram_monitor.utils.logger import get_logger"` | Previously recovered file |
| `import psutil` | `metrics.py` | Third-party package | `python -c "import psutil; print(psutil.__version__)"` | Previously recovered file |
| `import pyqtgraph as pg` | `charts.py` | Third-party package | `python -c "import pyqtgraph; print(pyqtgraph.__version__)"` | Previously recovered file |
| `import numpy as np` | `charts.py` | Third-party package | `python -c "import numpy; print(numpy.__version__)"` | Previously recovered file |
| `from PySide6.QtCore import Qt, QThread, Signal` | Multiple files | Third-party package | `python -c "from PySide6.QtCore import Qt"` | Previously recovered file |
| `from PySide6.QtGui import QShortcut` | `main_window.py` | Third-party — NOTE: QShortcut is in QtGui, NOT QtCore | `python -c "from PySide6.QtGui import QShortcut"` | Previously recovered file — this import caused a bug in M2-8 |
| `from PySide6.QtCore import QSettings` | `compact_mode.py`, `settings.py` | Third-party package | `python -c "from PySide6.QtCore import QSettings"` | Previously recovered file |

### Circular Dependencies to Watch For

**None.** The import graph is acyclic. The layering is:
```
app → main_window → dashboard → {stats_cards, charts, responsive_grid, process_panel}
                                     ↓                ↓
                               fluent_theme      fluent_theme
```

Evidence: Previously recovered file — import graph was verified in the handover document.

---

## SECTION 8: VALIDATION CHECKLIST

### 8.1 Per-Commit Validation

After each commit, verify:

- [ ] All files are in expected locations (`find . -type f -not -path "./.venv/*" -not -path "./.git/*" | sort`)
- [ ] No files were accidentally deleted (`git diff --stat HEAD~1` — check for deletions)
- [ ] No duplicate files exist (`find . -name "*.py" -not -path "./.venv/*" | sort | uniq -d`)
- [ ] All imports resolve correctly (`python -c "import ram_monitor"`)
- [ ] No generated files were committed (`git ls-files | grep -E "__pycache__|\.pyc|\.pytest_cache|\.venv|dist/|egg-info"`)
- [ ] Binary files are properly tracked (`git ls-files assets/rammonitor.ico`)
- [ ] Directory structure matches target layout (`ls src/ram_monitor/core/ src/ram_monitor/ui/ src/ram_monitor/utils/ tests/`)

### 8.2 Final Validation

- [ ] Repository matches target layout exactly (compare with Section 3 tree)
- [ ] All verified files are preserved (compare with Section 2.1 table)
- [ ] No unintended changes to file contents (`git diff` should show only additions)
- [ ] Git history is clean and logical (`git log --oneline` — 7 commits as described in Section 6)
- [ ] All "Needs GitHub verification" items have been resolved (clone GitHub repo and compare)
- [ ] `LD_LIBRARY_PATH=/home/z/.local/lib QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/ -v` shows "146 passed"
- [ ] `scripts/smoke_test_window.py` prints "SMOKE OK"
- [ ] `git diff --stat -- src/ram_monitor/core/` is empty
- [ ] `git status` shows "nothing to commit, working tree clean"
- [ ] UI module count: 11 files in `src/ram_monitor/ui/`
- [ ] Test file count: 15 files in `tests/`
- [ ] Test count: 146 tests total

### 8.3 Git Verification Commands

| Command | What It Verifies | When To Use |
|---------|-----------------|-------------|
| `git status` | Shows modified, staged, and untracked files | After every file operation |
| `git diff` | Shows exact content changes | Before committing |
| `git diff --stat` | Shows summary of changes (file-level) | Quick overview before commit |
| `git ls-files` | Lists all tracked files | To verify nothing is missing |
| `git ls-files \| wc -l` | Count of tracked files | Should be 50+ after reconstruction |
| `git log --oneline` | Shows commit history | To review commit sequence |
| `git log --stat` | Shows commit history with file changes | To review what each commit changed |
| `git mv old new` | Safely moves/renames files while preserving history | For all file moves (not needed in this plan — no moves required) |
| `git restore <file>` | Reverts unintended changes to a specific file | If something goes wrong |
| `git checkout -- .` | Reverts all uncommitted changes | Emergency rollback |
| `git clean -fd` | Removes untracked files and directories | Emergency cleanup |
| `git show HEAD` | Shows the latest commit details | After committing to verify |

---

## SECTION 9: RISK ANALYSIS

| Risk | Likelihood | Impact | Detection Method | Mitigation | Evidence |
|---|---|---|---|---|---|
| Duplicate files — same file in multiple locations | Low | Medium | `find . -name "*.py" -not -path "./.venv/*" \| sort \| uniq -d` | Write each file exactly once to its target path | Current workspace — no duplicates currently exist |
| Stale versions — older version overwriting newer version | Medium | High | `git diff` before committing | Always write from conversation history (latest verified version) | Previously recovered file — workspace reset means any existing file is stale |
| Broken imports — file moves breaking import statements | Low | High | `python -c "import ram_monitor"` after writing each module | No files are being moved — all are new creations in correct locations | Current workspace — no moves needed, only creation |
| Misplaced modules — files in wrong directories | Medium | High | `ls src/ram_monitor/ui/*.py \| wc -l` (must be 11) | Follow the target layout in Section 3 exactly | Previously recovered file — 11 UI modules expected |
| Generated files accidentally committed | Medium | Low | `git ls-files \| grep -E "__pycache__\|\.pyc\|\.pytest_cache\|\.venv\|dist/\|egg-info"` | `.gitignore` must be written and committed first | Current workspace — `.gitignore` may be missing |
| Lost files — files deleted during move operations | Low | Critical | `git ls-files \| wc -l` (must be 50+) | No moves are happening — only new file creation | Current workspace — no existing files need to be moved |
| Incorrect replacements — wrong file replacing another | Low | High | `git diff` before committing | No replacements needed — all missing files are new | Current workspace — all existing files stay in place |
| Unauthorized modifications — files changed during reorganization that should remain untouched | Medium | Critical | `git diff -- src/ram_monitor/core/` (must be empty) | Never edit core/ files. Write them exactly from conversation history. | Previously verified output — core/ was verified unchanged across all M2 commits |
| Workspace reset during reconstruction | High | Critical | `find . -type f \| wc -l` drops suddenly | Commit immediately after writing each group of files | Current workspace — workspace has reset multiple times during this project |
| Conversation context limit — earlier file contents truncated | Medium | Critical | File contents not available in conversation | Use HANDOVER_DOCUMENT.md as backup reference | Conversation memory — this conversation is extremely long |
| libEGL.so.1 symlink lost | High | Medium | `python -c "import PySide6.QtWidgets"` fails with ImportError | Recreate symlink: `ln -sf /home/z/.cache/ms-playwright/chromium-1228/chrome-linux64/libEGL.so /home/z/.local/lib/libEGL.so.1` | Previous verified output — symlink was required every session |

---

## SECTION 10: FINAL ACCEPTANCE CRITERIA

| Criterion | Verification Method | Evidence Required |
|-----------|--------------------|--------------------|
| Directory structure matches target layout | `find . -type f -not -path "./.venv/*" -not -path "./.git/*" \| sort` — compare with Section 3 tree | File listing matches exactly |
| `src/ram_monitor/` contains 22 Python files | `find src/ -name "*.py" \| wc -l` — must be 22 | Output shows 22 |
| `src/ram_monitor/ui/` contains 11 Python files | `ls src/ram_monitor/ui/*.py \| wc -l` — must be 11 | Output shows 11 |
| `src/ram_monitor/core/` contains 4 Python files | `ls src/ram_monitor/core/*.py \| wc -l` — must be 4 | Output shows 4 |
| `src/ram_monitor/utils/` contains 3 Python files | `ls src/ram_monitor/utils/*.py \| wc -l` — must be 3 | Output shows 3 |
| `tests/` contains 15 Python files | `ls tests/*.py \| wc -l` — must be 15 | Output shows 15 |
| Total test count is 146 | `grep -c "def test_" tests/*.py \| awk -F: '{sum += $2} END {print sum}'` — must be 146 | Output shows 146 |
| All tests pass | `LD_LIBRARY_PATH=/home/z/.local/lib QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/ -v` | Output shows "146 passed" |
| Smoke test passes | `.venv/bin/python scripts/smoke_test_window.py` | Output shows "SMOKE OK" |
| Core engine unchanged | `git diff --stat -- src/ram_monitor/core/` | Output is empty |
| All imports resolve | `python -c "import ram_monitor; from ram_monitor.app import run; print('OK')"` | Output shows "OK" |
| No generated files committed | `git ls-files \| grep -E "__pycache__\|\.pyc\|\.pytest_cache\|\.venv\|dist/\|egg-info"` | Output is empty |
| `.gitignore` exists and contains `.venv/` | `cat .gitignore \| grep ".venv/"` | Output shows `.venv/` |
| Git status is clean | `git status` | Output shows "nothing to commit, working tree clean" |
| All "Needs GitHub verification" items resolved | Clone `https://github.com/ihavetherobotmt5-code/RAMMonitor` and compare contents | Explicit confirmation for each item from Section 2.4 |
| No regressions from verified V2 state | Compare file count, test count, and test output with previous verified runs | File count: 50+, Tests: 146 passed, Smoke: OK |
| `assets/rammonitor.ico` is a valid icon | `file assets/rammonitor.ico` | Output shows "MS Windows icon resource - 4 icons" |
| `assets/rammonitor.exe.manifest` is valid XML | `python -c "import xml.etree.ElementTree as ET; ET.parse('assets/rammonitor.exe.manifest')"` | No exception raised |
| `build/RAMMonitor.spec` is valid Python | `python -c "import ast; ast.parse(open('build/RAMMonitor.spec').read())"` | No exception raised |
| `build/version_info.txt` is valid Python | `python -c "content = open('build/version_info.txt').read(); lines = [l for l in content.split(chr(10)) if not l.strip().startswith('#')]; compile(chr(10).join(lines), 'v', 'exec')"` | No exception raised |
