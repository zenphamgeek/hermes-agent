---
name: video-motion-studio
description: Create animated video scenes, SVG motion and infographics.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms:
- linux
- macos
- windows
metadata:
  hermes:
    tags:
    - video
    - motion-graphics
    - infographic
    - svg-animation
    - creative
---
# Video Motion Studio Skill

Generate rich visual storyboards, SVG vector animations, high-tech infographics, and kinetic motion graphics for autonomous AI video production.

## When to Use

- When transforming text scripts into animated video scenes.
- When generating technical infographics, system architecture maps, or data dashboards.
- When creating SVG animations, pulsing circuit nodes, or HUD telemetry graphics.
- When applying dynamic camera motion (Ken Burns pan/zoom) and kinetic typography to video scenes.

## Prerequisites

- Python 3.10+
- `ffmpeg` installed for video compositing and transition effects.
- Pillow (`PIL`) for high-resolution graphics rendering.
- `cairosvg` or native vector rasterizer for SVG animation rendering.

## How to Run

Run the standalone CLI runner:

```bash
# 1. Generate high-tech infographic image
python optional-skills/creative/video-motion-studio/motion_studio.py infographic \
  --title "Personal AI Agent Architecture" \
  --subtitle "Zero-Trust & Autonomous Execution" \
  --nodes "LLM Core,Terminal Sandbox,Secret Vault,Telegram Gateway" \
  --output ~/workspace/output/factory/infographic_sample.png

# 2. Render animated scene with Ken Burns motion effect and voiceover
python optional-skills/creative/video-motion-studio/motion_studio.py render-scene \
  --image ~/workspace/output/factory/infographic_sample.png \
  --audio ~/workspace/output/factory/scene_audio.wav \
  --effect pan-zoom \
  --output ~/workspace/output/factory/animated_scene.mp4

# 3. Generate SVG vector motion clip
python optional-skills/creative/video-motion-studio/motion_studio.py svg-anim \
  --type pulsing-network \
  --duration 5 \
  --output ~/workspace/output/factory/svg_network_anim.mp4
```

## Step-by-Step Procedure

1. **Scene Scripting & Storyboarding**: Deconstruct raw topic into structured scenes with visual prompts, layout schemes, and key metric badges.
2. **Infographic Generation**: Compose glassmorphism cards, metric gauges, and connected node graphs with modern cybernetic palettes.
3. **SVG Animation Rasterization**: Animate vector elements (rotating dials, flowing neural links, pulsing security shields).
4. **Camera FX & Kinetic Text**: Apply smooth easing zooms, motion blurs, and animated subtitle overlays.
5. **Quality Gate Verification**: Run Content Quality Gate to ensure broadcast standard (1080p, 30/60 fps, crisp contrast).

## Quick Reference

| Command | Purpose | Key Options |
|---|---|---|
| `infographic` | Create tech diagrams & HUD cards | `--title`, `--nodes`, `--style`, `--output` |
| `svg-anim` | Render vector motion animations | `--type`, `--duration`, `--fps`, `--output` |
| `render-scene` | Assemble image + audio + camera FX | `--image`, `--audio`, `--effect`, `--output` |
| `storyboard` | Plan multi-scene visual storyboard | `--topic`, `--scenes-count`, `--output` |

## Pitfalls to Avoid

- Do not use low-resolution canvas (always generate 1920x1080 for 16:9 or 1080x1920 for 9:16).
- Avoid static images without motion (always apply subtle pan, zoom, or particle overlay).
- Keep text overlays concise (max 2 lines of prominent text per frame).
- Ensure high contrast between text and background for mobile readability.

## Verification

Validate generated visual and video artifacts:

```bash
python optional-skills/creative/content-factory/content_quality_gate.py \
  --video ~/workspace/output/factory/animated_scene.mp4 \
  --aspect 16:9
```
