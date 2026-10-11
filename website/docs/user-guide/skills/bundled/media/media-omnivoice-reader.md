---
title: "Omnivoice Reader — Convert long documents and transcripts into voiceover audio"
sidebar_label: "Omnivoice Reader"
description: "Convert long documents and transcripts into voiceover audio"
---

{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */}

# Omnivoice Reader

Convert long documents and transcripts into voiceover audio.

## Skill metadata

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/media/omnivoice-reader` |
| Version | `1.0.0` |
| Author | Hermes Agent |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `tts`, `voice-cloning`, `audiobook`, `speech`, `podcast`, `media`, `audio` |
| Related skills | [`youtube-channel-srt`](/docs/user-guide/skills/bundled/media/media-youtube-channel-srt), [`media-studio`](/docs/user-guide/skills/bundled/media/media-media-studio) |

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# OmniVoice Long Text Reader (Smart Chunking & Voice Cloning)

Reads and converts long texts, transcripts, books, lectures, and articles into natural, continuous voiceover audio tracks (MP3/WAV/M4A) using the GPU-accelerated **OmniVoice TTS** engine on the P15 LXC container (`10.123.214.178:80`).

## When to Use

Use this skill when:
- The user asks to convert long text, books, articles, or transcripts into speech / audiobook files.
- The user needs zero-shot voice cloning with custom audio samples.
- The user requests synchronized subtitle generation (`.srt`) along with generated narration.

Do NOT use for short single-sentence notification sounds.

---

## Key Features

- **Smart Semantic Chunking**: Breaks long documents into natural prosodic chunks (250–400 chars) on sentence and paragraph boundaries without cutting words or clauses.
- **Transcript Artifact Cleaning**: Automatically cleans YouTube transcript sound markers (`[âm nhạc]`, `[vỗ tay]`, `[Music]`), unneeded line breaks, and punctuation.
- **Zero-shot Voice Cloning**: Uses local voice samples to narrate with custom emotional tonality.
- **Parallel Synthesis Pipeline**: Accelerates batch synthesis using concurrent threads on the GPU.
- **Studio-Quality Audio Assembly**: Seamlessly stitches audio chunks with natural silence pauses (`--pause-ms 350`) via FFmpeg.
- **Synced SRT Export**: Automatically generates an exact, timestamped `.srt` subtitle file synced with the generated audio.

---

## Setup & Prerequisites

OmniVoice runs as an LXC container on the P15 workstation (`omnivoice-tts` at `http://10.123.214.178:80/tts`).

Ensure FFmpeg and Python dependencies are present:
```bash
uv pip install requests rich boto3
```

---

## Usage Examples

### 1. Read a Long Transcript with Voice Preset

```bash
uv run python skills/media/omnivoice-reader/scripts/reader.py \
  "path/to/transcript.txt" \
  --voice "moon phan - audiobooks & podcast" \
  --output "./output_audio/output.mp3"
```

### 2. Custom Reference Voice Audio & Text

```bash
uv run python skills/media/omnivoice-reader/scripts/reader.py \
  "path/to/document.txt" \
  --ref-audio "path/to/sample.mp3" \
  --ref-text "path/to/sample.txt" \
  --output "output_audiobook.mp3"
```

### 3. Adjust Pacing, Chunks, and Silence Gaps

```bash
uv run python skills/media/omnivoice-reader/scripts/reader.py \
  "path/to/document.txt" \
  --voice "moon phan - audiobooks & podcast" \
  --max-chars 350 \
  --pause-ms 400 \
  --workers 3 \
  --format mp3 \
  --bitrate 192k
```

---

## CLI Reference

| Argument | Description | Default |
|---|---|---|
| `file` | Path to the input text file | *Required* |
| `-o, --output` | Path to destination audio file (`.mp3`, `.wav`, `.m4a`) | `./audiobooks/<filename>_<voice>.mp3` |
| `-v, --voice` | Name of registered OmniVoice voice | `moon phan - audiobooks & podcast` |
| `--ref-audio` | Local reference audio file for custom cloning | `None` |
| `--ref-text` | Local reference text file for custom cloning | `None` |
| `--max-chars` | Maximum characters per chunk | `380` |
| `--pause-ms` | Silence pause between chunks in milliseconds | `350` |
| `--workers` | Concurrent worker threads | `3` |
| `--format` | Output container (`mp3`, `wav`, `m4a`) | `mp3` |
| `--bitrate` | Encoding bitrate | `192k` |
| `--no-srt` | Disable synced `.srt` export | `False` |

---

## Output Files

For each processed document, the tool generates:
1. **Master Voiceover Track (`.mp3`)**: Studio-quality combined narration.
2. **Synchronized Subtitles (`.srt`)**: Timestamps matching the narrated speech.
