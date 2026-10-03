#!/usr/bin/env bash
set -euo pipefail

# ==============================================================================
# Hermes Agent - Hourly Median-0 Channel Sync & Manim Ingestion Job
# ==============================================================================

REPO_DIR="/home/zen/hermes-agent"
cd "$REPO_DIR"

# Ensure PATH includes local binaries (rclone, uv, ffmpeg, etc.)
export PATH="/home/zen/.local/bin:$PATH"

# Log file setup
LOG_DIR="$REPO_DIR/assets/scripts_video/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/median_hourly_sync.log"

# Keep log file bounded (max ~5MB, rotate if larger)
if [ -f "$LOG_FILE" ] && [ "$(stat -c%s "$LOG_FILE" 2>/dev/null || stat -f%z "$LOG_FILE" 2>/dev/null || echo 0)" -gt 5242880 ]; then
    mv "$LOG_FILE" "${LOG_FILE}.old"
fi

echo "======================================================================" >> "$LOG_FILE"
echo "⏰ [Hermes Cron] Triggering Hourly Sync at $(date -u '+%Y-%m-%dT%H:%M:%SZ')" >> "$LOG_FILE"
echo "======================================================================" >> "$LOG_FILE"

# Prefer .venv python if available
PYTHON_BIN="python3"
if [ -f "$REPO_DIR/.venv/bin/python" ]; then
    PYTHON_BIN="$REPO_DIR/.venv/bin/python"
fi

# Run the sync pipeline with local pruning enabled to protect disk space
"$PYTHON_BIN" "$REPO_DIR/assets/scripts_video/median_channel_sync_pipeline.py" \
    --prune-local-videos \
    >> "$LOG_FILE" 2>&1

EXIT_CODE=$?
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ [Hermes Cron] Hourly Sync completed successfully." >> "$LOG_FILE"
else
    echo "❌ [Hermes Cron] Hourly Sync failed with exit code $EXIT_CODE." >> "$LOG_FILE"
fi

exit $EXIT_CODE
