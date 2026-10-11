---
title: "Media Studio — Pipeline from 1 topic to Shorts, Facebook, and X"
sidebar_label: "Media Studio"
description: "Pipeline from 1 topic to Shorts, Facebook, and X"
---

{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */}

# Media Studio

Pipeline from 1 topic to Shorts, Facebook, and X.

## Skill metadata

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/media/media-studio` |
| Version | `1.0.0` |
| Author | ZENPHAM, Hermes Agent |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `media`, `content`, `production`, `pipeline`, `shorts`, `reels`, `video` |
| Related skills | [`youtube-publisher`](/docs/user-guide/skills/bundled/media/media-youtube-publisher), [`facebook-publisher`](/docs/user-guide/skills/bundled/social-media/social-media-facebook-publisher), [`xurl`](/docs/user-guide/skills/bundled/social-media/social-media-xurl), [`youtube-content`](/docs/user-guide/skills/bundled/media/media-youtube-content), [`media-setup`](/docs/user-guide/skills/bundled/media/media-media-setup) |

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# Media Studio — Content Production Pipeline

Orchestrator skill that transforms **one topic** into a complete content pack for
**3 platforms** (YouTube Shorts, Facebook Post, X Thread). Combines research,
writing, visual generation, voiceover, and video assembly.

## When to Use

Use when the user wants to:
- Create content about a topic for multiple platforms
- Run the daily content pipeline
- Produce a YouTube Shorts video from a script
- Generate thumbnail + voiceover + subtitles automatically

## Prerequisites

- `ffmpeg` installed (static binary at `~/.local/bin/ffmpeg`)
- Publishing skills configured: `youtube-publisher`, `facebook-publisher`, `xurl`
- `image_generation_tool` available (for thumbnail generation)
- **OmniVoice TTS** (primary): LXC container `omnivoice-tts` at `10.123.214.178:80`
  - Voice: "dũng - poetic, deep and resonant" (default for ZENPHAM)
  - Engine: `omnivoice` (local GPU on P15 Quadro RTX 5000)
- **Edge-TTS** (fallback): `vi-VN-NamMinhNeural` voice (when OmniVoice is unavailable)

## Content Templates

Load the appropriate template from `SKILL_DIR/templates/` based on content type:

- `templates/shorts_script.md` — YouTube Shorts script structure
- `templates/fb_post.md` — Facebook long-form post structure
- `templates/x_thread.md` — X/Twitter thread structure
- `templates/thumbnail_prompt.md` — Prompt template for thumbnail generation
- `templates/persona.md` — ZENPHAM brand voice and style guide

## Full Pipeline (1 Topic → 3 Platforms)

### Step 1: Research

```
1. Web search for the topic — latest news, key developments
2. xurl search for trending discussions on X about the topic
3. Summarize key points, interesting angles, potential hooks
```

### Step 2: Write Content (load templates)

Generate 3 versions simultaneously:

1. **YouTube Shorts Script** (load `templates/shorts_script.md`):
   - Hook (0-3s): Câu hỏi gây tò mò hoặc fact giật
   - Content (3-50s): Giải thích cốt lõi, ví dụ cụ thể
   - CTA (50-60s): Like + Subscribe + Comment prompt

2. **Facebook Post** (load `templates/fb_post.md`):
   - Hook line 1: Câu đầu tiên trước nút "Xem thêm" — phải giật
   - Body: Phân tích sâu hơn, bullet points, ví dụ
   - CTA: Câu hỏi mời tương tác

3. **X Thread** (load `templates/x_thread.md`):
   - Tweet 1: Hook giật + emoji + ảnh thumbnail
   - Tweets 2-5: Nội dung cốt lõi (mỗi tweet &lt; 280 ký tự)
   - Tweet 6: CTA + "Repost nếu hữu ích" + hashtag

### Step 3: Generate Thumbnail

```
1. Load templates/thumbnail_prompt.md
2. Generate hero image with image_generation_tool (Flux/DALL-E)
3. Run make_thumbnail.py to overlay text + brand watermark
4. Resize for each platform:
   - YouTube: 1280x720 (16:9)
   - Facebook: 1200x630 (1.91:1)
   - X: 1600x900 (16:9)
```

### Step 4: Generate Voiceover

**Primary: OmniVoice (local GPU voice clone)**
```bash
OVTTS="python SKILL_DIR/scripts/omnivoice_tts.py"

# Check health first
$OVTTS --health

# Generate voiceover with "dũng" voice clone
$OVTTS --file /tmp/media-studio/YYYY-MM-DD/tts_input.txt \
  --voice "dũng - poetic, deep and resonant" \
  --output /tmp/media-studio/YYYY-MM-DD/voiceover.wav

# List available voices
$OVTTS --list-voices
```

**Fallback: Edge-TTS (when OmniVoice is unavailable)**
```bash
edge-tts --voice "vi-VN-NamMinhNeural" \
  --file /tmp/media-studio/YYYY-MM-DD/tts_input.txt \
  --write-media /tmp/media-studio/YYYY-MM-DD/voiceover.mp3 \
  --write-subtitles /tmp/media-studio/YYYY-MM-DD/subtitles.vtt
```

**Asset selection:**
- Scan recursively with `tools.media_asset_catalog.scan_assets`; resolve asset ID/relative path with `resolve_asset`.
- Voice references come from category `voice`; face references from category `face`.
- `female`/`male` are catalog filters only; never control articulation.
- Face, voice, and video default to `local_only`; cloud upload requires explicit consent/policy.
- Assets directly supplied by the user default to `owner_authorized` unless the user says otherwise; this does not apply to third-party assets.
- Unicode, spaces, and case-insensitive extensions are supported.

### Step 5: Generate Subtitles

**Option A: Edge-TTS VTT** (if using Edge-TTS with `--write-subtitles`)
```
Already generated in Step 4 fallback as subtitles.vtt
```

**Option B: From text** (if using OmniVoice — no built-in subtitle support)
```bash
# Get audio duration first
DURATION=$(ffmpeg -i voiceover.wav 2>&1 | grep Duration | sed 's/.*Duration: //' | sed 's/,.*//')
DURATION_SECS=$(echo "$DURATION" | awk -F: '{ printf "%.0f", ($1*3600)+($2*60)+$3 }')

python SKILL_DIR/scripts/gen_subtitles.py \
  --file /tmp/media-studio/YYYY-MM-DD/tts_input.txt \
  --duration $DURATION_SECS \
  --output /tmp/media-studio/YYYY-MM-DD/subtitles.srt
```

### Step 6: Assemble Video

```bash
# Use the assembly script (supports both MP3 and WAV audio)
bash SKILL_DIR/scripts/assemble_shorts.sh \
  --audio /tmp/media-studio/YYYY-MM-DD/voiceover.wav \
  --srt /tmp/media-studio/YYYY-MM-DD/subtitles.srt \
  --out /tmp/media-studio/YYYY-MM-DD/shorts_final.mp4

# If no --bg, the script auto-generates a dark gradient background.
# Background duration auto-matches audio length + 2s buffer.
```

### Step 7: Preview & Approval

Send to user via Telegram/current platform:
1. Thumbnail image
2. Video preview (Shorts .mp4)
3. Full text of all 3 content pieces
4. Ask: "OK đăng ngay / Sửa lại / Hẹn giờ [thời gian]"

### Step 8: Publish (after user approval)

Based on user response:
- **"OK đăng ngay"**: Publish all 3 immediately
- **"Hẹn giờ 19h"**: Schedule publish at specified time
- **"Sửa lại [feedback]"**: Revise content and re-preview

Publishing commands:
```bash
# X Thread (via x-publisher skill / xurl CLI)
xurl thread \
  --media /tmp/media-studio/YYYY-MM-DD/thumb_x.jpg \
  "Tweet 1 (hook)" \
  "Tweet 2" "Tweet 3" "Tweet 4" \
  "Final CTA tweet"

# YouTube (via youtube-publisher skill)
python youtube-publisher/scripts/yt_publish.py upload \
  --video /tmp/media-studio/YYYY-MM-DD/shorts_final.mp4 \
  --title "TITLE #shorts" \
  --thumbnail /tmp/media-studio/YYYY-MM-DD/thumb_yt.jpg \
  --privacy private

# Facebook (via facebook-publisher skill)
python facebook-publisher/scripts/fb_publish.py post \
  --message "FB_POST_TEXT" \
  --first-comment "Source links..."
```

## Working Directory

All intermediate files are stored in `/tmp/media-studio/YYYY-MM-DD/`:
<!-- ascii-guard-ignore -->
```
/tmp/media-studio/2026-08-22/
├── topic.md              # Research notes
├── tts_input.txt         # Clean text for TTS
├── script_shorts.md      # YouTube Shorts script
├── script_fb.md          # Facebook post text
├── script_x.md           # X Thread tweets
├── hero_image.jpg        # AI-generated image
├── thumb_yt.jpg          # YouTube thumbnail (1280x720)
├── thumb_fb.jpg          # Facebook thumbnail (1200x630)
├── thumb_x.jpg           # X thumbnail (1600x900)
├── voiceover.wav         # OmniVoice clone audio (primary)
├── voiceover.mp3         # Edge-TTS audio (fallback)
├── subtitles.srt         # Generated subtitles
├── subtitles.vtt         # Edge-TTS word-level timestamps
└── shorts_final.mp4      # Final assembled Shorts video (1080x1920)
```
<!-- ascii-guard-ignore-end -->

## Error Handling

- **OmniVoice fails**: Fallback to Edge-TTS `vi-VN-NamMinhNeural` voice
- **TTS fails completely**: Retry with shorter script. If both fail, create text-only video
- **Image generation fails**: Use a solid color gradient with text overlay as fallback
- **FFmpeg error**: Check that all input files exist. `assemble_shorts.sh` auto-generates background if missing
- **Publishing fails**: Save content to `~/.hermes/media/failed_queue.json` for retry
- **OmniVoice container stopped**: Auto-start with `lxc start omnivoice-tts`, wait 3s, then retry
