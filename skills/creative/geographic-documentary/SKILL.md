---
name: geographic-documentary
description: End-to-end documentary video production pipeline for geographic/cultural content using footage-centric approach, TTS voice-over, cinematic grading, and automated YouTube publishing.
version: 1.0.0
author: ZENPHAM, Hermes Agent
license: MIT
platforms:
- linux
metadata:
  hermes:
    tags:
    - Video Production
    - Documentary
    - Geography
    - Content Factory
    - YouTube
    related_skills:
    - youtube-publisher
    - media-studio
    - youtube-content
---
# Geographic Documentary — Production Skill

End-to-end pipeline for producing broadcast-quality geographic & cultural documentary videos.
Built from real production experience on **"Biết Địa Lý Từ Ba Tôi"** (Vietnam Geography Series).

## When to Use

- User wants to create a documentary video about a region, culture, or geographic topic
- User has footage (drone, travel, archival) + a narrative script
- User wants automated TTS voice-over + cinematic grading + YouTube publish
- Producing multi-episode series with consistent quality

## Architecture Overview

```
Script (MD) → TTS Voice-Over → Footage Mapping → Shot Extraction
    → Cinematic Grading → Scene Assembly → Music Mixing → Final Output
    → YouTube Publish
```

## Core Principle: Footage-Centric (CRITICAL)

> **The script serves the footage, not the other way around.**

This is the #1 quality rule. Every scene's narration must describe what the viewer
actually sees. If footage shows rice paddies, the script must talk about rice paddies —
NOT about floating markets (even if the original script says so).

### Visual-Semantic Quality Gate (≥ 90% Match Ratio)

$$\text{Visual-Semantic Score} = \frac{\sum \text{Matched Entity Shots}}{\sum \text{Required Entity Anchors}} \times 100\% \ge 90\%$$

1. **Visual Entity Anchoring & Geographic Purity (CRITICAL MANDATE)**:
   - **Strict Geographic Footprint Binding**: Every documentary episode is strictly bound to its geographical topic. **ALL footage used in an episode MUST be authentically located in that specific geographic region/province/city**.
   - **Zero False B-roll / Zero Geographic Hallucination**:
     - When producing an episode on **Hà Nội**: **STRICTLY FORBIDDEN** to use limestone karst mountains (Ninh Bình / Tam Cốc), terraced rice fields (Tây Bắc / Mù Cang Chải / Sa Pa), southern canals/boats (Mekong Delta), lantern streets (Hội An), skyscrapers of Sài Gòn, or foreign/European urban streets and apartment blocks.
     - Every shot must show genuine, verifiable Hanoi locations: Sông Hồng bãi bồi, Cầu Long Biên, Hoàng thành Thăng Long, Văn Miếu, Phố Cổ 36 phố phường, Nhà tập thể Kim Liên chuồng cọp, Cát Linh - Hà Đông metro, Hồ Tây - Chùa Trấn Quốc.
   - Any specific location, building, river, monument, or historical entity mentioned in voice-over MUST have actual, authentic footage of that exact entity on screen within $\pm 1.5$ seconds.
2. **The Bidirectional Script Rewrite Rule**:
   - If footage is unavailable for a script concept: Rewrite the narration to focus on high-definition footage that *is* available in the vault (e.g., if subterranean excavation is unavailable, pivot narration to Doan Mon and Flag Tower).
   - Script and footage co-evolve; never force mismatched stock video.
3. **Longform Documentary Standard & Shot Breakdown (CHỐNG LAZY CODE)**:
   - **Tối thiểu 10 Phần ($\ge 10$ Parts)**: Mỗi tập phim tài liệu địa lý phải có tối thiểu 10 phần độc lập, tổng thời lượng video $\ge 25$ phút (1,500s – 1,700s).
   - **Phân rã khối Sub-3-minute**: Mỗi phần dài $120\text{s} - 170\text{s}$ ($\le 180$s). Voiceover chứa $250 - 350$ từ tiếng Việt (~1.5 – 2.0 phút) kết hợp 40 – 60s negative space thiên nhiên.
   - **Mật độ cú máy**: Mỗi phần được cắt dựng từ 4–8 shots con (3–8s/shot): Establishing (flycam đại cảnh), Action (nhịp sống sông nước, mưu sinh), Detail (rễ cây, thớ đất, công trình), Transition (cutaway mượt mà).
   - **Bilingual TTS Contract**: Thuật ngữ khoa học, tên tổ chức quốc tế hoặc mã tọa độ chuẩn hóa bằng thẻ `<en>...</en>` tại ranh giới câu/mệnh đề độc lập (ví dụ: `<en>GPS 0001</en>`, `<en>UNESCO World Biosphere Reserve</en>`, `<en>offshore breakwater</en>`).
4. **Time Compensation & Transition Padding**:
   - Head padding: $0.4s \le T_{head} \le 0.8s$
   - Tail padding: $0.6s \le T_{tail} \le 0.8s$
   - Transition overlap: $D_{trans} = 0.5s$
   - Duration requirement: $T_{video} \ge T_{voice} + T_{head} + T_{tail} + D_{trans} \ge T_{voice} + 1.6s$
   - Breathing gap: $1.5s$ giữa các phân đoạn để tạo chiều sâu chiêm nghiệm của phim tài liệu.

### Episode 02 Blueprint: Hà Nội — Thành Phố Của Những Lớp Thời Gian
- **Scene 1 (Cold Open)**: Lake of the Restored Sword morning mist → Old Quarter clay tiles → Long Bien Bridge → Modern high-rises.
- **Scene 2 (Red River & Delta)**: Muddy red water, agricultural floodplains, ancient dike system.
- **Scene 3 (Imperial Citadel)**: Thang Long Citadel, Doan Mon gate, archaeological layers of Ly-Tran-Le dynasties.
- **Scene 4 (36 Merchant Guild Streets)**: Hang Bac, Hang Ma, silversmith artisans, deep tube houses (nhà hình ống).
- **Scene 5 (French Colonial Layer)**: Hanoi Opera House, rusted Eiffel steel of Long Bien Bridge, Phan Dinh Phung shaded tree avenue.
- **Scene 6 (Subsidy Era & War Memory)**: Kim Lien / Trung Tu collective housing blocks, iron tiger cages (chuồng cọp), weathered cement stairs.
- **Scene 7 (Modern Rebuilding)**: Nhat Tan cable-stayed bridge, Cat Linh - Ha Dong elevated metro, modern skyline.
- **Scene 8 (Philosophical Pause)**: West Lake twilight mist, sidewalk iced tea (trà đá), street elders playing chess — the enduring pace of Hanoi.

### Footage-Centric Checklist
- [ ] Pre-production audit of available footage before finalizing narration
- [ ] Map each part/scene to specific timecodes (file + start + duration)
- [ ] Zero timecode overlap — no footage segment used twice
- [ ] Script rewrites executed when footage doesn't match original narration
- [ ] Video duration ≥ audio duration + padding ($T_{head} 0.8s + T_{tail} 0.8s + D_{trans} 0.5s$)
- [ ] Audio volume gate: `volumedetect` verifies mean_volume > -30 dB across all parts (1 đến N)
- [ ] Master 2K QHD export (2560x1440 Lanczos) kích hoạt VP9/AV01 trên YouTube
- [ ] Normalized stereo 44.1kHz / 48kHz AAC prior to concat (zero silent scene drop)

## Pipeline Scripts

All scripts in `assets/scripts_video/`:

| Script | Purpose |
|:---|:---|
| `footage_centric_engine.py` | Shot mapping, extraction, grading, concatenation |
| `cinematic_filter_engine.py` | Color grading profiles (NatGeo warmth) |
| `assemble_documentary.py` | Final assembly: merge VO + concat + music |
| `run_toi_doc_sach_full_release.py` | Batch runner for full episodes |

## Step-by-Step Workflow

### 1. Prepare Footage Vault

```bash
# Organize source footage in wikimedia_vault/
assets/scripts_video/wikimedia_vault/
├── chau_doc_nga_ba_song.webm    # Drone/aerial
├── mekong_forest_tour.webm      # River tours
├── rach_gia_travel.webm         # City footage
└── ...
```

Create contact sheets to preview what's in each file:
```bash
# Extract frames every 10s for visual review
for f in wikimedia_vault/*.webm; do
  name=$(basename "$f" .webm)
  ffmpeg -i "$f" -vf "fps=0.1,scale=320:-1" -q:v 5 "contact_${name}_%03d.jpg"
done
```

### 2. Create Script Markdown

Write the episode script in markdown with frontmatter:

```markdown
---
channel: PHAMTRAI_DIALY
series: "Việt Nam Những Miền Sống"
episode: 1
title: "Miền Tây Nam Bộ: Sống Cùng Dòng Nước"
---

## Scene 1: Mở đầu — Châu Đốc
Hồi nhỏ, ba hay dắt con ra phố, qua mấy cái đền cũ...

## Scene 2: Ruộng lúa xanh bạt ngàn
Nhìn từ trên cao, ruộng lúa trải dài...
```

### 3. Generate TTS Voice-Over

```bash
# Using Google TTS or ElevenLabs
# Output: audio/vietnam_nhung_mien_song_tap_01/scene_01.wav ... scene_08.wav
```

### 4. Build Footage Map (footage_centric_engine.py)

The `build_footage_centric_map()` function returns a list of `SceneFootageMap` objects,
each containing:
- `scene_num`: Scene number (1-8)
- `audio_duration`: Duration from TTS wav file
- `shots`: List of `Shot(source_file, start_time, duration, description, shot_type, quality)`
- `script_rewrite`: Optional rewritten narration matching footage

#### Critical Rules:
1. **No timecode overlap**: Each `(file, start_time)` pair appears exactly once
2. **Video ≥ Audio**: `sum(shot.duration) >= audio_duration` for every scene
3. **Content match**: Shot descriptions must match what's visually on screen
4. **Shot quality ≥ 4**: Use `quality` field (1-5) to prefer best footage

### 5. Extract & Grade Shots

```python
from footage_centric_engine import build_footage_centric_map, extract_shot, apply_cinematic_grade

scenes = build_footage_centric_map()
for scene in scenes:
    for i, shot in enumerate(scene.shots):
        raw = shots_dir / f"s{scene.scene_num}_shot{i+1}.mp4"
        extract_shot(shot, raw)        # → 1080p 30fps h264
        graded = graded_dir / raw.name
        apply_cinematic_grade(raw, graded)  # → warm documentary tone
```

### 6. Assemble Final Video

```bash
python3 assemble_documentary.py --episode 01
```

This runs:
1. **Merge** each scene clip + voice-over (audio is master duration)
2. **Generate** 1.5s black breathing gaps between scenes
3. **Concatenate** all scenes with gaps
4. **Mix** ambient music at -35dB under voice-over

### 7. Publish to YouTube

```bash
YTP=".venv/bin/python3 skills/media/youtube-publisher/scripts/yt_publish.py"

# Dry-run first
$YTP upload --video output/final.mp4 --md script.md --channel PHAMTRAI_DIALY --dry-run

# Publish
$YTP upload --video output/final.mp4 --md script.md --channel PHAMTRAI_DIALY --privacy public
```

## Quality Control — Lessons Learned (CRITICAL)

These are bugs encountered in real production and their fixes:

### QC1: Vocal Cut at Scene Transitions
**Symptom**: Voice-over gets cut mid-sentence at scene boundaries.
**Root Cause**: Video duration < audio duration. FFmpeg's `-shortest` trims to shorter stream.
**Fix**: Ensure every scene's total video footage ≥ TTS audio duration.
```python
# In footage_centric_engine.py — validate before assembly
for scene in scenes:
    video_dur = sum(shot.duration for shot in scene.shots)
    assert video_dur >= scene.audio_duration, \
        f"S{scene.scene_num}: video={video_dur}s < audio={scene.audio_duration}s"
```

### QC2: Footage Appearing Multiple Times
**Symptom**: Same aerial shot repeats across different scenes.
**Root Cause**: Multiple scenes referencing same (file, timecode) segment.
**Fix**: Zero-overlap constraint — each timecode window used exactly once.
```python
# Validate in build_footage_centric_map()
usage = {}
for scene in scenes:
    for shot in scene.shots:
        key = (shot.source_file, shot.start_time)
        assert key not in usage, f"Overlap: {key} in S{scene.scene_num} and S{usage[key]}"
        usage[key] = scene.scene_num
```

### QC3: Content-Footage Mismatch
**Symptom**: Narrator says "floating market" but footage shows rice paddies.
**Root Cause**: Script written before footage review.
**Fix**: Write `script_rewrite` on the SceneFootageMap to match actual footage content.

### QC4: Concat Duration Mismatch
**Symptom**: Final video reports 384s when actual content is 234s.
**Root Cause**: `ffmpeg -c copy` concat can produce wrong container metadata when
source clips have different audio stream lengths.
**Fix**: Use video stream duration (not format duration) for downstream calculations:
```python
# Get accurate duration from video stream, not format container
vstream_dur = float(subprocess.run(
    ["ffprobe", "-v", "error", "-select_streams", "v:0",
     "-show_entries", "stream=duration", "-of", "csv=p=0", str(concat_out)],
    capture_output=True, text=True).stdout.strip())
```

### QC5: Dark/Black Frame Extraction
**Symptom**: Extracted shot is nearly black (<200KB for 5s clip).
**Root Cause**: Source video has dark intro/outro segments.
**Fix**: Check file size after extraction (minimum 200KB for valid clip):
```python
success = res.returncode == 0 and output_path.exists() and output_path.stat().st_size > 200_000
```

### QC6: WebM Seek Accuracy
**Symptom**: Shot starts at wrong point in WebM files.
**Root Cause**: WebM VP9 has sparse keyframes; input-level seek (`-ss` before `-i`) can miss.
**Fix**: For WebM files with start_time < 10s, use demuxer-level seek (`-ss` after `-i`).

### QC7: Breathing Room Between Scenes
**Symptom**: Scenes cut abruptly into each other, feels rushed.
**Fix**: Insert 1.5s black+silent gap clips between scenes during concatenation.
```bash
gap_dur = 1.5
# Generate black gap — MUST match VO audio params (mono/24kHz)
ffmpeg -f lavfi -i "color=c=black:s=1920x1080:d=1.5:r=30" \
       -f lavfi -i "anullsrc=channel_layout=mono:sample_rate=24000" \
       -t 1.5 -c:v libx264 -c:a aac scene_gap.mp4
```

### QC8: Concat Audio Dropout (CRITICAL)
**Symptom**: Voice-over plays for Scene 1 only, then silence for all remaining scenes.
**Root Cause**: `ffmpeg -f concat -c copy` silently drops audio from subsequent segments
when audio codec params differ (e.g., gap clip = stereo/44.1kHz vs merged clips = mono/24kHz).
**Fix**: ALL clips in the concat list MUST share identical audio params (channels and sample rate) before concatenation, and an automated `volumedetect` check must verify mean_volume > -30 dB across all 8 scenes.

### QC9: Cover Scene Design & Smart Title Breaking
**Requirement**: Every episode must have a broadcast-standard cover generated via `cover_design_engine.py`.
**Rules**:
1. **Preserve Geographical Entities**: The Smart Title Break algorithm must preserve names like "Hà Nội", "Huế", "Hội An", "Tây Nguyên", "Sài Gòn", "Cà Mau", "Sa Pa", "Miền Tây Nam Bộ" without splitting compound words or single words across lines.
2. **Brand Style**: Gold badge `🌏  BIẾT ĐỊA LÝ TỪ BA TÔI`, Crisp White + Golden Yellow title, 4K aerial landscape background.
3. **Command**:
```bash
python3 assets/scripts_video/cover_design_engine.py --md assets/scripts_video/vietnam_nhung_mien_song_tap_XX.md
```


## Cinematic Grade Profile

The PHAMTRAI_DIALY grade creates a warm, National Geographic documentary feel:

```
eq=contrast=1.08:brightness=-0.015:saturation=1.12
colorbalance=rs=0.03:gs=-0.01:bs=-0.04:rm=0.04:gm=0.02:bm=-0.03:rh=-0.02:gh=0.01:bh=-0.02
noise=alls=6:allf=t         # Organic 35mm grain
vignette=PI/4.5             # Subtle edge darkening
```

## Directory Structure

```
assets/scripts_video/
├── wikimedia_vault/          # Source footage (WebM, MP4)
├── audio/                    # TTS voice-over per episode
│   └── vietnam_nhung_mien_song_tap_01/
│       ├── scene_01.wav
│       └── ...
├── clips/                    # Intermediate (auto-cleaned)
│   ├── shots/                # Raw extracted shots
│   ├── shots_graded/         # After cinematic grade
│   ├── clip_1.mp4            # Concatenated scene clips
│   └── scene_gap.mp4         # Breathing gap
├── output/                   # Final deliverables
│   ├── *_final.mp4           # 1080p master
│   └── *_telegram.mp4        # 720p preview
├── footage_centric_engine.py
├── cinematic_filter_engine.py
├── assemble_documentary.py
└── vietnam_nhung_mien_song_tap_01.md  # Script
```

## Multi-Episode Workflow

For episodes 2-8, repeat:
1. Review footage vault for unused timecodes
2. Write script matching available footage
3. Generate TTS audio
4. Update `build_footage_centric_map()` with new scene mappings
5. Run: `python3 assemble_documentary.py --episode 02`
6. QC: Check vocal integrity + footage match + duration accuracy
7. Publish: `$YTP upload --video ... --md ... --channel PHAMTRAI_DIALY`
