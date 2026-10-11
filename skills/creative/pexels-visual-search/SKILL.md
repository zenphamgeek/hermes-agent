---
name: pexels-visual-search
description: "Tìm kiếm, chấm điểm ngữ cảnh (Contextual Matching Score) và tự động tích hợp Video Footage Pexels vào kịch bản Visual (16:9 Longform & 9:16 Shorts). Tự động quyết định: nếu khớp trên 90% ngữ cảnh cần minh họa thì dùng trực tiếp Video Footage của Pexels; nếu dưới 90% thì fallback sang Manim hoạt họa hoặc custom assets."
version: 1.0.0
author: ZENPHAM, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [pexels, video-footage, stock-search, visual-scripting, contextual-matching, zero-fake-motion, zenpham, reality-decode, toi-lam-viec]
    related_skills: [zenpham-script-writer, toi-lam-viec, youtube-to-manim, youtube-video-rewriter, reality-decode]
---

# Pexels Visual Search & Contextual Matcher Skill

Skill chuyên biệt cung cấp công cụ tìm kiếm thông minh, đối soát ngữ cảnh 4 chiều và tự động tích hợp video footage từ Pexels API vào kịch bản hình ảnh (Visual Track / Kịch bản phân cảnh).

> **QUY TẮC CỐT LÕI (CORE DIRECTIVE):**  
> **"Nếu tìm được Video Footage khớp trên 90% (Score $\ge 0.90$) ngữ cảnh cần minh họa, hệ thống BẮT BUỘC dùng trực tiếp Video Footage của Pexels."**  
> Khi độ khớp $< 90\%$, hệ thống tự động fallback sang đồ họa Manim (cho các khái niệm toán học, cây nhị phân, giải thuật) hoặc custom visual assets.

---

## 1. Kiến Trúc Thuật Toán Chấm Điểm Ngữ Cảnh 4 Chiều (Score 0.00 – 1.00)

Độ khớp ngữ cảnh được tính toán tự động dựa trên 4 trọng số:

$$\text{Score} = 0.40 \cdot S_{\text{semantic}} + 0.30 \cdot S_{\text{action}} + 0.15 \cdot S_{\text{aesthetic}} + 0.15 \cdot S_{\text{tech}}$$

| Trọng số | Thành phần | Tiêu chí đánh giá |
| :--- | :--- | :--- |
| **40%** | **Semantic & Subject ($S_{\text{semantic}}$)** | Khớp thực thể cốt lõi (bàn tay, bàn phím, màn hình, máy chủ, ly cà phê, cửa sổ mưa, sách cổ). Hỗ trợ từ điển ngữ nghĩa song ngữ VI-EN. |
| **30%** | **Action & Dynamics ($S_{\text{action}}$)** | Khớp hành động cụ thể đang diễn ra (gõ code, nhìn qua cửa sổ, nước mưa rơi, lật trang sách, đèn chớp nháy). |
| **15%** | **Aesthetic & Tone ($S_{\text{aesthetic}}$)** | Khớp ánh sáng và tông màu (low-key, dark, cinematic, neon, warm, minimalist, moody). |
| **15%** | **Technical & Aspect Ratio ($S_{\text{tech}}$)** | Độ phân giải $\ge 1080p$ (ưu tiên 4K), thời lượng $\ge 8.0s$, đúng tỷ lệ khung hình 16:9 hoặc 9:16, không trùng lặp lịch sử sử dụng (`used_history.json`). |

### Tiêu chuẩn Zero Fake Motion:
- Video Pexels khi tải về được transcode nguyên bản tĩnh 100% (`scale=...:force_original_aspect_ratio=increase,crop=...`).
- **TUYỆT ĐỐI CẤM** dùng `zoompan` hoặc hiệu ứng rung lắc `crop sway` giả chuyển động camera.

---

## 2. Hướng Dẫn Sử Dụng Master CLI

Engine chính được tích hợp tại: `assets/scripts_video/pexels_visual_matcher.py` (hoặc qua symlink `scripts/pexels_visual_matcher.py`).

### 2.1. Tra cứu ngữ cảnh độc lập (Prompt tiếng Việt hoặc tiếng Anh):
```bash
# Định dạng 16:9 Landscape (Video phân tích chuyên sâu / YouTube 2K)
/home/zen/hermes-agent/.venv/bin/python assets/scripts_video/pexels_visual_matcher.py \
  --context "bàn tay gõ bàn phím trong phòng tối" \
  --orientation landscape

# Định dạng 9:16 Portrait (YouTube Shorts / TikTok)
/home/zen/hermes-agent/.venv/bin/python assets/scripts_video/pexels_visual_matcher.py \
  --context "mưa rơi trên cửa sổ nhìn ra ánh đèn thành phố ban đêm" \
  --orientation portrait
```

### 2.2. Tra cứu và tự động tải về Footage Pool nếu khớp $\ge 90\%$:
```bash
/home/zen/hermes-agent/.venv/bin/python assets/scripts_video/pexels_visual_matcher.py \
  --context "bàn tay gõ bàn phím trong phòng tối" \
  --orientation landscape \
  --download
```
*Clip sẽ được lưu tại `assets/footage_pool/clips/` và tự động cập nhật vào `assets/footage_pool/index.json`.*

### 2.3. Tự động quét và nâng cấp toàn bộ file kịch bản markdown (`--enhance-script`):
```bash
/home/zen/hermes-agent/.venv/bin/python assets/scripts_video/pexels_visual_matcher.py \
  --enhance-script path/to/script.md \
  --orientation portrait \
  --download
```
*Hệ thống sẽ duyệt qua từng `Đoạn N:`, đối soát `• Hình ảnh:`. Phân cảnh nào đạt khớp $\ge 90\%$ sẽ được tự động đổi sang thẻ `[VISUAL: PEXELS_STOCK #ID...]`, tải clip sẵn sàng đưa vào render.*

---

## 3. Quy Ước Định Dạng Kịch Bản Visual

Khi video Pexels đạt điều kiện $\ge 90\%$, thẻ visual trong kịch bản `.md` có cấu trúc:

```markdown
Đoạn N: Xs–Ys (Tiêu đề cảnh)
• Hình ảnh: [VISUAL: PEXELS_STOCK #33414561 (Khớp: 90.0%) — Illuminated In Low Light]
  File: assets/footage_pool/clips/pexels_33414561_landscape.mp4
  URL: https://www.pexels.com/video/typing-on-illuminated-keyboard-in-low-light-33414561/
  Lý do khớp >90%: Semantic: 0.75, Action: 1.00, Aesthetic: 1.00, Tech: 1.00 (1920x1080, 12.0s) | Matches: typing, keyboard, low
• Lời thoại: "..."
```

Khi video Pexels $< 90\%$:
```markdown
Đoạn N: Xs–Ys (Tiêu đề cảnh)
• Hình ảnh: [VISUAL: MANIM_ANIMATION — SplayTreeRotationScene]
  Lý do: Không có stock footage khớp >90% với thuật toán xoay cây nhị phân trừu tượng.
• Lời thoại: "..."
```

---

## 4. Danh Sách 5 Khóa API Xoay Vòng
Hệ thống tự động nạp 5 khóa Pexels từ `~/.hermes/.env`:
- `PEXELS_API_KEY`
- `PEXELS_API_KEY_2`
- `PEXELS_API_KEY_3`
- `PEXELS_API_KEY_4`
- `PEXELS_API_KEY_5`

Tự động chuyển key ngay khi gặp giới hạn tần suất HTTP 429 mà không làm gián đoạn pipeline sản xuất.
