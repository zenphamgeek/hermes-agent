---
name: series-closing-cta
description: Direct, generate, and verify video Closing Screens, End Screens, and CTA beats with strict Series Plan, Thumbnails Grid, and Script Bridge integrity.
version: "1.0.0"
author: zenpham-team
license: MIT
platforms:
  - cli
tags:
  - video-production
  - manim
  - youtube
  - quality-gate
related_skills:
  - series-remake-director
  - manim-production
  - shorts-development
---

# Series Closing & CTA Director

Governs the production, design constraints, and automated verification of **Closing Screens, End Screens, and Call-To-Action (CTA) beats** across all ZenPham educational video series.

Ensures zero confusion between series plans, prevents cross-series thumbnail pollution, enforces YouTube End Screen clickable safe zones, and mandates a strict 3-part Open Loop script bridge.

---

## When to Use

Activate this skill whenever:
1. Writing the closing beat (final 12–20 seconds) of any longform episode script.
2. Generating or editing a Manim Closing Scene (e.g. `ZenphamLogoClosingCTA`, `SC12_ClosingCTA`).
3. Generating composite series thumbnail mosaics (e.g., 5×5 for Series 01, 3×3 for Logistics AI).
4. Performing pre-flight quality checks before rendering or publishing to YouTube.

---

## Prerequisites

- Active Series Contract (`SERIES_CONTRACT_V1.json` or `series_profile.json`).
- Python environment with Manim CE, Pillow, and FFmpeg installed.
- Thumbnail assets stored under `assets/scripts_video/output/youtube_staging/<series_id>/` or `assets/brand/zenpham-brand-kit/`.

---

## How to Run

Run the automated Series Closing Gate CLI:

```bash
# Verify closing screen alignment for an episode
python3 assets/scripts_video/series_closing_gate.py \
  --series series_01 \
  --episode 12 \
  --scene assets/scripts_video/hybrid_s1e12/scenes/scene_12_closing.py \
  --script assets/scripts_video/zenpham_toi_lam_viec_tap_12_transformer_architecture.md
```

---

## Procedure: The 3 Core Pillars

### Pillar 1: Series Plan Invariants & Finale Guard

Never assume the number of episodes or declare a "Finale" without consulting the Series Contract.

1. **Query Series Contract:** Look up `SERIES_CONTRACT_V1.json` for the given `series_id`.
   - Extract total episode count $N$ (e.g., $N=25$ for `series_01`, $N=5$ for `industrial_ai`, $N=9$ for `logistics_ai`).
   - Identify current episode index $k$.
2. **Intermediate Episode Rule ($k < N$):**
   - **STRICTLY FORBIDDEN:** Words like "Tập cuối", "Grand Finale", "Khép lại toàn bộ series", "Hồi kết".
   - **MANDATORY:** Must declare and display the successor episode $k+1$ (`cta_target`) along with its core dilemma (`next_open_loop`).
3. **True Finale Rule ($k = N$):**
   - Synthesizes the full $N$-episode journey.
   - Points to the Series Playlist or the next series in the ZenPham curriculum.

---

### Pillar 2: Thumbnails Grid of Series & Namespace Isolation

Every series possesses its own designated gallery mosaic and thumbnail dimensions. Cross-series mixing is a **CRITICAL FAILURE**.

#### Official Series Mosaic Registry

| Series ID | Series Name | Episode Count | Mosaic Asset Path | Grid Layout |
|:---|:---|:---:|:---|:---:|
| `series_01` | Tôi Làm Việc (AI Foundations) | **25 tập** | `assets/brand/zenpham-brand-kit/series1_25_thumbnails_mosaic.png` | 5 × 5 (16:9 cards) |
| `industrial_ai` | Industrial AI Masterclass | **5 tập** | `assets/brand/zenpham-brand-kit/industrial_ai_5_thumbnails_mosaic.png` | 1 × 5 (Horizontal) |
| `logistics_ai` | Logistics AI & Supply Chain | **9 tập** | `assets/brand/zenpham-brand-kit/logistics_ai_9_thumbnails_mosaic.png` | 3 × 3 (16:9 cards) |
| `series_02` | LLM Anatomy & Systems | **25 tập** | `assets/brand/zenpham-brand-kit/series2_25_thumbnails_mosaic.png` | 5 × 5 (16:9 cards) |

#### Rules for Closing Visual Layout
1. **Gallery Header Badge:** Must explicitly match the series title and total episode count (e.g., `"TRỌN BỘ SERIES 1 · 25 TẬP TOÁN HỌC & AI TỪ GỐC"`).
2. **Successor Thumbnail Check:**
   - File `thumb_tap_{k+1}_hero.jpg` or `thumbnail_16x9.png` for episode $k+1$ must exist on disk at 2560×1440 resolution.
3. **YouTube End Screen Interactive Safe Zones:**
   - YouTube allows interactive cards during the last 20 seconds of video.
   - Keep the following screen regions free of critical text or centered logos:
     - **Top-Right Rect [X: +2.5 to +6.5, Y: +0.5 to +3.2]:** Reserved for Next Video card (16:9).
     - **Bottom-Right Rect [X: +2.5 to +6.5, Y: -3.2 to -0.5]:** Reserved for Playlist card (16:9).
     - **Center/Left Circle [X: -1.0 to +1.0, Y: -1.0 to +1.0]:** Reserved for Channel Subscribe Avatar.

---

### Pillar 3: Script Bridge & 3-Step Open Loop Formula

The voiceover for the closing 12–20 seconds must never degrade into generic boilerplate ("Cảm ơn các bạn đã xem, nhớ like và subscribe"). It must follow the **ZenPham 3-Step Open Loop Formula**:

```
[Step 1: Core Synthesis (1 câu)]
Đúc kết ngắn gọn nguyên lý cốt lõi vừa học được trong tập này.

[Step 2: Open Loop Hook (1 câu)]
Chỉ ra nghịch lý, ranh giới lỗi hoặc bài toán thực nghiệm mà nguyên lý trên chưa giải quyết được, 
dẫn dắt trực tiếp vào chủ đề của tập tiếp theo.

[Step 3: Direct Action CTA (1 câu)]
Kêu gọi bấm vào video/thẻ bài hiển thị trên màn hình để giải mã bài toán đó.
```

#### Example Bridge (From S1E12 to S1E13):
> *"Khối Transformer đã liên kết trọn vẹn sự chú ý và tri thức thành một cỗ máy dự đoán ngôn ngữ phi thường. Nhưng làm sao chúng ta đo lường chính xác lượng thông tin bị mất mát hay độ bất định của toàn bộ chuỗi dữ liệu này? Đó là bài toán nén thông tin kỳ vĩ của Shannon Entropy. Hãy bấm vào video tiếp theo trên màn hình để cùng tôi giải mã."*

---

## Quick Reference

```python
# In any closing scene generator:
from series_closing_gate import check_series_plan_alignment, check_thumbnail_grid_isolation

# 1. Validate plan alignment before rendering
result = check_series_plan_alignment(series_id="series_01", ep_num=12, script_text=closing_script)
assert result.status == "PASS", result.detail

# 2. Validate scene code uses correct series assets
result = check_thumbnail_grid_isolation(series_id="series_01", scene_code=scene_source)
assert result.status == "PASS", result.detail
```

---

## Common Pitfalls

- **Hallucinating Finale:** Declaring S1E12 as "Finale" because it covers Transformers. (Series 01 has 25 episodes; Transformer is the anchor of Part 1, not the end of the series).
- **Wrong Mosaic Image:** Using `series1_25_thumbnails_mosaic.png` inside an `industrial_ai` video or vice-versa.
- **Missing Successor Thumbnail:** Rendering an End Screen with a black or placeholder box because the next episode's thumbnail hasn't been generated yet.
- **Overlapping YouTube End Screen Cards:** Placing animated text cards on the right side of the screen where YouTube's clickable video cards will overlay and obscure them.

---

## Verification

Run the test suite to verify closing CTA integrity across all series:

```bash
source .venv/bin/activate
pytest tests/test_series_closing_gate.py -v
```
