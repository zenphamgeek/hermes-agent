---
name: zenpham-series-auditor
description: Comprehensive multi-engine quality auditor for ZenPham masterclass video series. Audits EBU R128 audio fidelity, True Peak clipping, acoustic silence holes, 25-Thumbnail Mosaic Closing CTA uniformity, and Gold Standard structural sequence compliance.
version: "1.0.0"
author: zenpham-team
license: MIT
platforms:
  - cli
tags:
  - video-audit
  - audio-mastering
  - manim
  - youtube
  - quality-gate
  - ebu-r128
related_skills:
  - series-remake-director
  - series-closing-cta
  - vietnamese-expressive-tts
  - manim-production
---

# ZenPham Series Master Quality Auditor

Governs the multimodal quality inspection, automated regression detection, and compliance auditing for all **ZenPham Educational Cinema & Masterclass video productions** (Series 01 "Tôi Làm Việc", Series 02, etc.).

Ensures zero tolerance for audio distortion, acoustic silence holes, missing/non-uniform thumbnail mosaics, and inverted structural sequences.

---

## 1. When to Use

Activate this skill whenever:
1. **Pre-Flight Video Audit**: Auditing an episode or an entire series before publishing to YouTube.
2. **Audio Quality Inspection**: Checking for distorted audio (harmonic clipping, true peak > -4.0 dBFS), dead silence holes (> 0.35s in speech, > 3.5s in transitions), or unexpressive prosody.
3. **Closing Scene & Mosaic Verification**: Verifying whether the Closing CTA correctly displays the uniform 25-Thumbnail Mosaic (`series1_25_thumbnails_mosaic.png`) in 2K60 QHD with correct branding.
4. **Structural Sequence Gate**: Enforcing the strict Gold Standard scene order:
   `[1. Cold Open (Hook)] -> [2. Logo Opener (5.80s)] -> [3. Technical Scenes] -> [4. CTA & Mosaic Thumbnail] -> [5. Script Bridge Closing]`.

---

## 2. Three Pillars of the ZenPham Gold Standard

```
+-----------------------------------------------------------------------------------+
|                           ZENPHAM MASTER QUALITY GATE                             |
+-------------------------+-------------------------+-------------------------------+
|  1. AUDIO FIDELITY      |  2. MOSAIC UNIFORMITY   |  3. STRUCTURAL ORDER          |
|  - Integrated: -15.1 LUFS| - 5x5 Card Matrix (2K)  |  - Step 1: Cold Open (t=0)    |
|  - Peak: < -4.0 dBFS    |  - Episode Badges T.01  |  - Step 2: Opener (5.80s)     |
|  - 0 Digital Clipping   |  - Cyan/Amber Glows     |  - Step 3: Technical Scenes   |
|  - Holes: <= 3.5s       |  - Master Logo + CTA    |  - Step 4: CTA & Mosaic 25    |
|  - Local VieNeu CUDA    |  - Exact 8.00s Duration |  - Step 5: Script Bridge End  |
+-------------------------+-------------------------+-------------------------------+
```

### Pillar A: Audio Fidelity & Silence Gate
- **Integrated Loudness**: Must be strictly within **-15.1 ± 0.3 LUFS** (EBU R128 standard).
- **True Peak**: Maximum **-4.0 dBFS** ceiling (minimum 4.0 dB headroom). Any True Peak > -0.1 dBFS is an automatic hard rejection (Clipping Defect).
- **Loudness Range (LRA)**: Typical range 1.5 to 2.2 LU for clear, mastered speech.
- **Silence Gate**:
  * Intra-speech gaps: Frame-by-frame 20ms RMS scan compresses dead silence > 0.35s down to 0.20s (eliminating acoustic EOS-delay holes).
  * Inter-scene transition pauses: 0.35s to 3.0s is normal cinematic pacing.
  * **Critical Defect**: Any gap > 3.5s in speech or scene tails (e.g. untrimmed video plates) is an acoustic dead hole and MUST be trimmed.

### Pillar B: Closing Scene 25-Thumbnail Mosaic Uniformity
- **Master Image Asset**: `assets/brand/zenpham-brand-kit/series1_25_thumbnails_mosaic.png` (2560x1440 QHD).
  * 5x5 card layout (Cols=5, Rows=5, Card: 320x180, Padding: 14px, Radius: 10px).
  * Episode badges: `T.01` to `T.24` (cyan border `#38bdf8`) and `FINALE` for Ep 25 (amber border `#fbbf24`).
- **Master Video Asset**: `assets/brand/zenpham-brand-kit/zenpham_closing_cta_2k60_muxed.mp4` (8.00s @ 60fps, 2560x1440).
- **Uniformity Invariant**: Every episode in the series MUST append this exact 8.00s clip at the end. Ending abruptly without the Closing CTA or using a mismatched mosaic (e.g. 5-card or 9-card) is a visual defect.

### Pillar C: Gold Standard Structural Order
- **Sequence Contract**:
  1. `[1. Cold Open (Hook / Paradox)]`: Starts at **$t = 00:00.00$**. Captures viewer retention immediately.
  2. `[2. Logo Opener (Brand Ident 5.80s)]`: Placed at **index 1** (immediately following Cold Open). **TUYỆT ĐỐI KHÔNG đặt ở $t = 00:00$**.
  3. `[3. Core Technical Scenes]`: Scenes 02 through $N-1$ containing procedural Manim geometry, intuitive proof, and physical analogies.
  4. `[4. CTA & 25-Thumbnail Mosaic]`: 8.00s outro showcasing the monumental scope of the series.
  5. `[5. Script Bridge Closing]`: Final cliffhanger sentence or closing dedication bridging to the next episode/series.

---

## 3. CLI Audit Tool & Execution

The canonical multi-threaded audit engine is located at:
`assets/scripts_video/audit_series_master.py`

### Basic Commands

```bash
# 1. Audit a single episode (e.g. Episode 01)
python3 assets/scripts_video/audit_series_master.py --episode 1

# 2. Audit all 25 episodes in parallel (6 worker threads)
python3 assets/scripts_video/audit_series_master.py --all --workers 6

# 3. Audit staging directory instead of scripts_video directory
python3 assets/scripts_video/audit_series_master.py --all --use-output-dir

# 4. Generate custom JSON manifest and Markdown report
python3 assets/scripts_video/audit_series_master.py --all \
  --output-json output/youtube_staging/audit_manifest.json \
  --output-md output/youtube_staging/audit_report.md
```

---

## 4. Reusable Prompt Templates for Future Audits

Copy and paste these prompt templates directly into Antigravity or your AI coding assistant:

### Template 1: Comprehensive Series Full Audit (All Episodes)
```text
/goal Chạy full multimodal quality audit cho toàn bộ 25 tập Series 01 bằng script assets/scripts_video/audit_series_master.py --all --workers 6.
Kiểm tra chi tiết 3 trụ cột Gold Standard:
1. Audio: Loudness (-15.1 ± 0.3 LUFS), True Peak (< -4.0 dBFS), 0 clipping, kiểm tra khoảng im lặng chết (> 3.5s).
2. Mosaic Thumbnail: Đảm bảo 100% các tập có Closing CTA 8.00s hiển thị đầy đủ 25-Thumbnail Mosaic đồng nhất.
3. Cấu trúc thứ tự: Kiểm tra đúng chuẩn [Cold Open -> Logo Opener 5.80s -> Scenes -> CTA Mosaic -> Bridge Closing]. Logo opener phải ở vị trí thứ 2, tuyệt đối cấm ở giây 00:00.
Xuất bảng tổng hợp kết quả chi tiết kèm mã lỗi và hướng dẫn khắc phục.
```

### Template 2: Single Episode Deep Audio & Video Inspection
```text
Chạy audit kiểm tra chất lượng master 2K cho Tập [N] Series [S]:
- File: output/youtube_staging/series_[S]/tap_[N]/zenpham_series_[S]_tap_[N]_master_2k.mp4
- Kiểm tra méo tiếng (harmonic distortion, True Peak > -4.0 dBFS, clipping).
- Quét toàn bộ các đoạn im lặng > 0.35s bằng ffmpeg silencedetect, đối chiếu xem có đoạn im lặng chết nào > 3.5s do video dài hơn audio không.
- Trích xuất frame tại giây cuối (duration - 4.0s) để kiểm tra Closing Scene Mosaic Thumbnail.
- Kiểm tra file concat để xác nhận vị trí Opener Bumper (sau Cold Open) và Closing CTA.
```

### Template 3: Audio Silence Gap & Desync Remediation
```text
Phát hiện đoạn im lặng chết [D] giây tại thời điểm [T] trong Tập [N].
Hãy:
1. Xác định scene cụ thể gây ra khoảng câm (so sánh video plate duration vs audio duration).
2. Mux lại scene đó với cờ `-shortest` hoặc `-t [audio_dur]` để cắt bỏ phần video thừa.
3. Cập nhật concat list và re-assemble full master 2K mà không re-render lại từ đầu.
4. Chạy lại audit_series_master.py --episode [N] để xác nhận Pass Ticket.
```

---

## 5. Remediation Playbook for Common Defects

| Defect Code | Root Cause | Automated Remediation Command |
|:---|:---|:---|
| `ACOUSTIC_HOLE_GT_35S` | Video plate was longer than newly synthesized audio track, leaving trailing silence. | Remux scene master with `-t [audio_dur]` or `-shortest`, then re-concatenate. |
| `INVERTED_OPENER` | Opener bumper was placed at `index 0` ($t=0$s) instead of after Scene 01. | Edit `concat_list.txt` to place Scene 01 at index 0 and Opener at index 1, then re-concatenate. |
| `MISSING_OPENER` | Opener bumper omitted during batch assembly. | Insert `file '.../zenpham_opener_clip_2k60_muxed.mp4'` at line 2 of `concat_list.txt`. |
| `MISSING_CLOSING_CTA` | Closing CTA omitted at the tail of concat list. | Append `file '.../zenpham_closing_cta_2k60_muxed.mp4'` at the final line of `concat_list.txt`. |
| `LOUDNORM_DEVIATION` | Audio outside -15.1 ± 0.3 LUFS. | Re-run 5-Stage Studio Vocal Mastering Chain with `-af loudnorm=I=-15.1:TP=-4.5:LRA=1.8`. |
