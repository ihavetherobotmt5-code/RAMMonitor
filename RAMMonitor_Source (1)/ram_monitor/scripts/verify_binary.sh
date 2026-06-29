#!/usr/bin/env bash
# Verify the PyInstaller-bundled binary launches and reaches the Qt event loop.
# Strategy: launch the binary, sleep 3 seconds, then kill it. If the process
# exits with a non-zero code BEFORE we kill it, the bundle is broken.
set -u

BIN=/home/z/my-project/ram_monitor/dist/RAMMonitor
cd /home/z/my-project/ram_monitor

# Provide a display via offscreen platform — bundled Qt respects the same
# env var as the dev install.
export QT_QPA_PLATFORM=offscreen
export LD_LIBRARY_PATH=/home/z/.local/lib:${LD_LIBRARY_PATH:-}
export RAM_MONITOR_DEBUG=1
export RAM_MONITOR_LOG_DIR=/tmp/ram_monitor_verify_logs

mkdir -p "$RAM_MONITOR_LOG_DIR"
rm -f "$RAM_MONITOR_LOG_DIR"/ram_monitor.log

# Launch in background.
"$BIN" &
APP_PID=$!
echo "Launched PID=$APP_PID"

# Give it 4 seconds to either crash or sit in the event loop.
sleep 4

# Check if the process is still alive.
if kill -0 "$APP_PID" 2>/dev/null; then
    echo "STATUS: ALIVE after 4 s — bundle starts cleanly."
    # Send SIGTERM, then SIGKILL if needed.
    kill -TERM "$APP_PID" 2>/dev/null
    sleep 1
    kill -KILL "$APP_PID" 2>/dev/null
    EXIT_STATUS=0
else
    wait "$APP_PID"
    CODE=$?
    echo "STATUS: EXITED EARLY with code $CODE — bundle is broken."
    EXIT_STATUS=1
fi

# Dump any logs the binary wrote.
echo "=== LOG OUTPUT ==="
cat "$RAM_MONITOR_LOG_DIR"/ram_monitor.log 2>/dev/null || echo "(no log file)"
echo "=== END LOG ==="

exit $EXIT_STATUS
