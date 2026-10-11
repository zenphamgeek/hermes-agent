---
title: "Youtube Channel Srt — Download YouTube channel SRT subtitles, media & WhisperX"
sidebar_label: "Youtube Channel Srt"
description: "Download YouTube channel SRT subtitles, media & WhisperX"
---

{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */}

# Youtube Channel Srt

Download YouTube channel SRT subtitles, media & WhisperX.

## Skill metadata

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/media/youtube-channel-srt` |
| Version | `1.2.0` |
| Author | Hermes Agent |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `YouTube`, `Subtitles`, `SRT`, `Transcripts`, `WhisperX`, `Speech-to-Text`, `Audio`, `Video`, `Media`, `Scheduler`, `Anti-Bot` |
| Related skills | [`youtube-content`](/docs/user-guide/skills/bundled/media/media-youtube-content), [`media-studio`](/docs/user-guide/skills/bundled/media/media-media-studio) |

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# YouTube Channel SRT Extractor (with Media Download & WhisperX Engine)

Extracts and downloads subtitle files (`.srt`), audio streams (`.wav`), and full video files (`.mp4`) from any YouTube channel, playlist, or video URL.
Features smart anti-bot throttling, batch chunking, rest intervals, and mobile client spoofing.
If a video lacks YouTube subtitles (manual captions or auto-generated captions), the tool automatically downloads the audio stream and executes **WhisperX** (with GPU CUDA acceleration, Silero VAD batching, and word-level phoneme alignment) to generate clean, timestamped `.srt` files.

---

## When to Use

Use this skill when:
- The user wants to download **subtitles, clean audio (.wav), or full video (.mp4)** from an entire YouTube channel (e.g. `@channelhandle`, channel URL, playlist).
- The user wants to **keep audio/video files permanently** (`--keep-audio`, `--keep-video`) without deleting them after SRT generation for voice cloning, editing, or future re-processing.
- The user wants to **run WhisperX on existing local audio/video files** (`--process-local`) without downloading again from YouTube (saving bandwidth and avoiding YouTube rate limits).
- The user wants to run a background cron job / scheduled loop (`--loop --interval 3600`) to automatically sync new videos and transcribe pending items.

---

## Setup & Dependencies

Install dependencies into the Hermes environment using `uv`:

```bash
uv pip install yt-dlp whisperx faster-whisper torch torchaudio rich
```

---

## Key Features

1. **Media Retention (`--keep-audio`, `--keep-video`)**:
   - Download and save high-quality 16kHz mono `.wav` into `./audio/` for AI voice training/analysis.
   - Download full `.mp4` video files into `./video/`.
   - Never deletes media files after SRT transcription.
2. **Local Offline Processing (`--process-local`)**:
   - Scans existing `./audio/` and `./video/` directories for files without `.srt` and runs WhisperX GPU directly without network requests.
3. **Anti-Bot & Safe Throttling**:
   - Mobile player clients (`android`, `ios`) bypass web captchas.
   - Jitter delay (`--delay-min`, `--delay-max`) and batch rest pauses (`--rest-seconds`).
4. **Browser Cookies Integration (`--cookies-from-browser chrome`)**:
   - Authenticates requests directly with browser cookies.
5. **Scheduled Cron Mode (`--loop --interval 3600`)**:
   - Runs periodically in the background, checking for new channel uploads.

---

## Usage Examples

### 1. Download Subtitles and Keep Audio (.wav)

```bash
uv run python skills/media/youtube-channel-srt/scripts/extractor.py "https://www.youtube.com/channel/UCOkQcQKRboB0DjSYlrL9sMw" \
  --output-dir "./output_srt/thinh_phap_am" \
  --keep-audio
```

### 2. Download Full Video (.mp4) + Audio (.wav) + Subtitles

```bash
uv run python skills/media/youtube-channel-srt/scripts/extractor.py "URL" \
  --output-dir "./downloads/channel_archive" \
  --keep-video \
  --keep-audio
```

### 3. Run WhisperX on Existing Local Files (No YouTube Download)

```bash
uv run python skills/media/youtube-channel-srt/scripts/extractor.py \
  --output-dir "./output_srt/thinh_phap_am" \
  --process-local \
  --whisper-model large-v2
```

### 4. Background Scheduled Daemon (Lập lịch tự động)

Run continuously in the background, checking the channel every 2 hours:
```bash
uv run python skills/media/youtube-channel-srt/scripts/extractor.py "https://www.youtube.com/channel/UCOkQcQKRboB0DjSYlrL9sMw" \
  --output-dir "./output_srt/thinh_phap_am" \
  --keep-audio \
  --loop \
  --interval 7200
```

### 5. Force WhisperX AI Transcription on GPU

```bash
uv run python skills/media/youtube-channel-srt/scripts/extractor.py "URL" \
  --force-whisper \
  --whisper-model large-v2 \
  --batch-size 16
```

---

## CLI Options Reference

| Argument | Description | Default |
|---|---|---|
| `url` | Channel URL, handle (`@name`), playlist, or empty for local mode | `""` |
| `-o, --output-dir` | Output folder for `.srt`, `.txt`, `.json`, `audio/`, `video/` | `./output_srt/<name>` |
| `-l, --languages` | Subtitle language priority (comma-separated, e.g. `vi,en,auto`) | `vi,en,auto` |
| `--keep-audio`, `--download-audio` | Save 16kHz `.wav` audio permanently in `output_dir/audio/` | `False` |
| `--keep-video`, `--download-video` | Save full `.mp4` video permanently in `output_dir/video/` | `False` |
| `--process-local` | Scan local files and run WhisperX without connecting to YouTube | `False` |
| `--chunk-size` | Number of videos per batch | `20` |
| `--rest-seconds` | Rest interval in seconds between batches | `10.0` |
| `--delay-min` | Minimum randomized delay (seconds) between video requests | `1.0` |
| `--delay-max` | Maximum randomized delay (seconds) between video requests | `3.0` |
| `--max-workers` | Concurrent network workers (default 2 for safe anti-bot) | `2` |
| `--cookies-from-browser` | Extract cookies from browser (`chrome`, `firefox`, `brave`, etc.) | `None` |
| `--loop` | Run continuously in background scheduler mode | `False` |
| `--interval` | Seconds between check cycles when `--loop` is enabled | `3600` (1 hour) |
| `--no-auto-subs` | Do NOT use YouTube auto-captions; use WhisperX instead | `False` |
| `--force-whisper` | Ignore all YouTube subtitles; transcribe everything with WhisperX | `False` |
| `--whisper-model` | Whisper model (`tiny`, `base`, `small`, `medium`, `large-v2`, `large-v3`) | `large-v2` |
| `--device` | Device for WhisperX (`cuda`, `cpu`, `auto`) | `auto` |
| `--batch-size` | Batch size for WhisperX VAD inference | `16` |
| `--no-txt` | Do not export plain text transcripts alongside `.srt` | `False` |
| `--no-jsonl` | Do not export unified `channel_transcripts.jsonl` | `False` |

---

## Output Structure

<!-- ascii-guard-ignore -->
```
output_srt/<channel_name>/
├── audio/                         # Clean 16kHz WAV audio files (--keep-audio)
│   └── <video_id>_<title>.wav
├── video/                         # Full MP4 video files (--keep-video)
│   └── <video_id>_<title>.mp4
├── manifest.json                  # Real-time state & execution statistics
├── history.sqlite                 # SQLite checkpoint store for instant resume
├── channel_transcripts.jsonl      # Combined dataset for RAG / LLM fine-tuning
├── <video_id>_<title>.vi.srt      # Standard SubRip subtitle file (UTF-8)
├── <video_id>_<title>.vi.txt      # Clean reading text (timestamps removed)
└── <video_id>_<title>.json        # Sidecar metadata (video_id, audio/video paths, duration)
```
<!-- ascii-guard-ignore-end -->
