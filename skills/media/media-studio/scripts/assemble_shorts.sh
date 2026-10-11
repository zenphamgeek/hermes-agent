#!/bin/bash
# assemble_shorts.sh — Assemble YouTube Shorts video from components
#
# Usage:
#   bash assemble_shorts.sh \
#     --audio voiceover.mp3 \
#     --srt subtitles.srt \
#     [--bg background.mp4] \
#     --out output.mp4
#
# If --bg is not provided, generates a dark gradient background.
# Output is always 1080x1920 (9:16) suitable for Shorts/Reels.

set -euo pipefail

FFMPEG="${FFMPEG:-ffmpeg}"
if ! command -v "$FFMPEG" &>/dev/null; then
    # Try common locations
    for loc in ~/.local/bin/ffmpeg /usr/local/bin/ffmpeg /usr/bin/ffmpeg; do
        if [ -x "$loc" ]; then
            FFMPEG="$loc"
            break
        fi
    done
fi

if ! command -v "$FFMPEG" &>/dev/null && [ ! -x "$FFMPEG" ]; then
    echo '{"status": "error", "error": "ffmpeg not found. Install with: curl -sL https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz | tar -xJ --strip-components=1 -C ~/.local/bin"}' >&2
    exit 1
fi

# Parse arguments
AUDIO=""
SRT=""
BG=""
OUT=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --audio) AUDIO="$2"; shift 2;;
        --srt) SRT="$2"; shift 2;;
        --bg) BG="$2"; shift 2;;
        --out) OUT="$2"; shift 2;;
        *) echo "Unknown option: $1" >&2; exit 1;;
    esac
done

if [ -z "$AUDIO" ] || [ -z "$OUT" ]; then
    echo "Usage: assemble_shorts.sh --audio FILE --srt FILE [--bg FILE] --out FILE" >&2
    exit 1
fi

if [ ! -f "$AUDIO" ]; then
    echo "Audio file not found: $AUDIO" >&2
    exit 1
fi

# Get audio duration (ffmpeg -i exits non-zero as it's a probe, hence || true)
DURATION=$("$FFMPEG" -i "$AUDIO" 2>&1 | grep "Duration" | head -1 | sed 's/.*Duration: //' | sed 's/,.*//' || true)
DURATION_SECS=$(echo "$DURATION" | awk -F: '{ printf "%.0f", ($1 * 3600) + ($2 * 60) + $3 }')
# Add 2 seconds buffer to ensure background covers the full audio
DURATION_SECS_BG=$((DURATION_SECS + 2))

echo "Audio duration: ${DURATION} (${DURATION_SECS}s, bg: ${DURATION_SECS_BG}s)" >&2

# Generate background if not provided
if [ -z "$BG" ] || [ ! -f "$BG" ]; then
    BG_TMP=$(mktemp /tmp/media-studio-bg-XXXXX.mp4)
    echo "Generating gradient background (${DURATION_SECS_BG}s)..." >&2

    "$FFMPEG" -y -loglevel warning \
        -f lavfi -i "color=c=#0d1117:s=1080x1920:d=${DURATION_SECS_BG},format=yuv420p" \
        -vf "
            drawbox=x=0:y=0:w=1080:h=640:color=#1a1a2e@0.8:t=fill,
            drawbox=x=0:y=640:w=1080:h=640:color=#16213e@0.6:t=fill,
            drawbox=x=0:y=1280:w=1080:h=640:color=#0f3460@0.4:t=fill
        " \
        -c:v libx264 -preset ultrafast -crf 28 \
        -t "$DURATION_SECS_BG" \
        "$BG_TMP"

    BG="$BG_TMP"
    CLEANUP_BG=1
else
    CLEANUP_BG=0
fi

# Build FFmpeg filter
VFILTER="scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=#0d1117"

if [ -n "$SRT" ] && [ -f "$SRT" ]; then
    # Escape the SRT path for FFmpeg subtitle filter
    SRT_ESCAPED=$(echo "$SRT" | sed "s/'/\\\\'/g" | sed 's/:/\\:/g')
    VFILTER="${VFILTER},subtitles='${SRT_ESCAPED}':force_style='FontName=Arial,FontSize=24,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BackColour=&H80000000,Outline=2,Shadow=1,Alignment=2,MarginV=120,Bold=1'"
fi

echo "Assembling video..." >&2

"$FFMPEG" -y -loglevel warning \
    -i "$BG" \
    -i "$AUDIO" \
    -vf "$VFILTER" \
    -c:v libx264 -preset fast -crf 23 -pix_fmt yuv420p \
    -c:a aac -b:a 128k -ar 44100 \
    -shortest \
    -movflags +faststart \
    "$OUT"

# Cleanup
if [ "$CLEANUP_BG" -eq 1 ] && [ -f "$BG_TMP" ]; then
    rm -f "$BG_TMP"
fi

# Output result
FILE_SIZE=$(stat --printf="%s" "$OUT" 2>/dev/null || stat -f%z "$OUT" 2>/dev/null || echo "0")
echo "{\"status\": \"ok\", \"output\": \"$OUT\", \"duration\": \"${DURATION_SECS}s\", \"size_bytes\": $FILE_SIZE}" >&2
echo "Done: $OUT" >&2
