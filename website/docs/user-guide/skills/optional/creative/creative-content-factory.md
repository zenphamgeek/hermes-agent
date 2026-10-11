---
title: "Content Factory — Autonomous multi-platform AI content production pipeline"
sidebar_label: "Content Factory"
description: "Autonomous multi-platform AI content production pipeline"
---

{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */}

# Content Factory

Autonomous multi-platform AI content production pipeline.

## Skill metadata

| | |
|---|---|
| Source | Optional — install with `hermes skills install official/creative/content-factory` |
| Path | `optional-skills/creative/content-factory` |
| Version | `1.0.0` |
| Author | hermes-community |
| License | MIT |
| Platforms | cli, telegram, windows |
| Tags | `content factory` |

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# Content Factory — Autonomous Media Production Pipeline

The Content Factory skill coordinates the entire end-to-end media creation
and distribution lifecycle using local ThinkPad P15 AI infrastructure
(LM Studio, ComfyUI, FaceFusion, OmniVoice TTS, MinIO S3) and Telegram Mission Control.

## When to Use

Activate this skill when the user asks to:
- Generate complete multi-platform content from a single topic or trend
- Produce AI videos with automated voiceover, subtitles, and face swap
- Batch render social media reels, shorts, or infographic carousels
- Orchestrate publishing across YouTube, Facebook, and X (Twitter)
- Check render job status or manage asset buckets in MinIO S3
- Execute commands starting with `/factory` or `factory:`

Do NOT use for one-off single-image edits or manual coding tasks.

## Prerequisites

1. **LM Studio** active at `http://10.123.214.1:1234/v1` for scripting
2. **ComfyUI** container running at `http://10.123.214.153:8188`
3. **FaceFusion** container running at `http://10.123.214.208:7860`
4. **OmniVoice TTS** container running at `http://10.123.214.178:8080`
5. **MinIO S3** active at `http://10.123.214.249:9000` (bucket: `shared-assets`)
6. **FFmpeg** installed on the workstation

## How to Run

All factory stages are executed via `terminal` tool invocations to local
services, Python runners, or sub-skills.

## Procedure

### Stage 1 — Topic Research & Script Generation

Generate title, outline, storyboard scenes, and narrator voice lines:

```bash
terminal(command="curl -s http://10.123.214.1:1234/v1/chat/completions -H 'Content-Type: application/json' -d '{\"model\":\"default\",\"messages\":[{\"role\":\"user\",\"content\":\"Tạo kịch bản YouTube Shorts 45s về chủ đề: AI Vibe Coding 2026 kèm visual prompts cho ComfyUI và voiceover script.\"}],\"temperature\":0.7}' | python3 -m json.tool")
```

### Stage 2 — Visual Asset & Voice Synthesis

1. **Audio Synthesis (OmniVoice TTS)**:
```bash
terminal(command="curl -s -X POST http://10.123.214.178:8080/synthesize -H 'Content-Type: application/json' -d '{\"text\":\"Chào mừng bạn đến với kỷ nguyên AI Vibe Coding 2026\",\"voice\":\"vi_female_1\",\"output_format\":\"wav\"}' -o ~/workspace/output/factory/audio_01.wav")
```

2. **Image Generation (ComfyUI)**:
```bash
terminal(command="curl -s -X POST http://10.123.214.153:8188/prompt -H 'Content-Type: application/json' -d '{\"prompt\":{...}}'")
```

### Stage 3 — Face Swap & Video Assembly

1. **Segment Footage / Target Video**:
```bash
terminal(command="python3 ~/.hermes/skills/video-face-segmenter/segmenter.py --input '~/workspace/footage/target.mp4' --gender female --output-dir '~/workspace/output/segments/' --json")
```

2. **Batch Face Swap (FaceFusion)**:
```bash
terminal(command="python3 ~/.hermes/skills/swapface-folder/runner.py --source '~/workspace/faces/source.jpg' --target-folder '~/workspace/output/segments/' --filter ok_only --json")
```

3. **Assemble Final Video with FFmpeg**:
```bash
terminal(command="ffmpeg -y -loop 1 -i ~/workspace/output/visual.jpg -i ~/workspace/output/factory/audio_01.wav -c:v libx264 -tune stillimage -c:a aac -b:a 192k -pix_fmt yuv420p -shortest ~/workspace/output/factory/final_short.mp4")
```

### Stage 4 — Multi-Platform Publishing

```bash
# YouTube Shorts
terminal(command="python3 ~/.hermes/skills/youtube-publisher/publisher.py --video ~/workspace/output/factory/final_short.mp4 --title 'AI Vibe Coding 2026 #shorts' --privacy public")

# Facebook Reel / Post
terminal(command="python3 ~/.hermes/skills/facebook-publisher/publisher.py --video ~/workspace/output/factory/final_short.mp4 --caption 'Kỷ nguyên AI Vibe Coding'")

# X Thread
terminal(command="python3 ~/.hermes/skills/x-publisher/publisher.py --text 'AI Vibe Coding 2026: Cách vận hành Content Factory tự hành từ điện thoại 🧵👇' --media ~/workspace/output/factory/final_short.mp4")
```

## Quick Reference

```
/factory plan <topic>        → Tạo kịch bản + storyboard + prompt
/factory produce             → Kích hoạt ComfyUI + TTS render assets
/factory swap <face> <video> → Chạy FaceFusion swap khuôn mặt
/factory assemble            → Ghép audio, video, phụ đề thành phẩm
/factory publish <channel>   → Xuất bản lên YouTube, FB, X
/factory status              → Báo cáo tiến độ các job đang chạy
```

## Common Pitfalls

1. **GPU VRAM Overload**: LM Studio retains ~11GB VRAM. Run only ONE
   GPU-heavy task (ComfyUI render OR FaceFusion swap) at a time.
2. **Missing Storage Bucket**: Ensure target bucket `shared-assets` exists in MinIO.
3. **Invalid Social Tokens**: Validate OAuth credentials via `media-setup` before bulk publishing.

## Verification

1. Verify output file exists and has size > 1MB: `ls -lh ~/workspace/output/factory/`
2. Test playback or inspect metadata with `ffprobe`
3. Check Telegram notification delivered with thumbnail preview
