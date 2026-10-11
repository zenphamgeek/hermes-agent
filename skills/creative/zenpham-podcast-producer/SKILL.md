---
name: zenpham-podcast-producer
description: End-to-end production skill for ZENPHAM philosophical podcasts & shorts (Neo-noir, 9:16 anti-skew, voice-driven sync, smart-break cover scenes, and audio quality gates).
version: 3.0.0
author: ZENPHAM, Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [zenpham, podcast, shorts, youtube, video-production, neo-noir, cover-engine, kanban, omnivoice]
    related_skills: [zenpham-script-writer, youtube-publisher, omnivoice-reader]
---

# ZENPHAM Podcast & Shorts Producer Skill (v3.0)

Hệ thống sản xuất tự động trọn gói cho kênh **ZENPHAM** — Thể loại: **Triết học ứng dụng, chiêm nghiệm công nghệ, Digital Minimalism và hiện sinh hiện đại**. Phong cách: **Neo-noir tối giản, trầm mặc, suy tư sâu sắc**.

## 1. Thể Loại & Định Dạng Sản Xuất Chuẩn

### A. Shorts / Reels / TikTok (9:16 — 1080x1920)
- **Thời lượng**: 60s – 90s (hoặc micro-shorts 30s–45s).
- **Quy chuẩn Footage & Anti-Skew**:
  - TUYỆT ĐỐI KHÔNG scale trần `scale=1080:1920` làm méo footage 16:9.
  - BẮT BUỘC dùng pipeline: `scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920` để bảo toàn tỉ lệ khung hình gốc và crop trung tâm điện ảnh.
- **Voice-Driven Duration**: Co giãn từng clip theo đúng thời lượng phát âm thực tế của voice (`--voice-driven`).
- **Karaoke Subtitles**: ASS karaoke màu vàng hổ phách `#FFD700`, căn lề dưới MarginV 180–220px, không che mặt nhân vật hay logo.

### B. Video Dài / Podcast (16:9 — 1920x1080)
- **Thời lượng**: 3 – 5 phút.
- **Tone thị giác**: Ánh sáng tương phản cao (low-key lighting), monochrome / desaturated cinematic, hạt phim 35mm grain.
- **Âm thanh**: Piano mộc tối giản, một nốt kéo dài, nhịp thở sâu, không tiếng ồn nhân tạo.

---

## 2. Quy Chuẩn Cover Scene & Thumbnail Engine (`cover_design_engine.py`)

Mọi video sản xuất phải có Cover Scene / Thumbnail đạt chuẩn nhận diện thương hiệu ZENPHAM:

### A. Quy Cách Thiết Kế
- **Brand Badge**: `🔴  ZENPHAM` (Ruby Crimson `#DC2D2D`, bo góc, badge nổi bật).
- **Typography**: `NotoSansDisplay-Bold` cực nét, drop shadow nhiều lớp chống chìm nền.
  - Dòng 1: Trắng tinh thể (`#FFFFFF`).
  - Dòng 2: Đỏ Neon nhấn mạnh (`#FF4B4B`).
- **Curiosity Subtitle Hook**: Màu Slate Soft (`#D2D7E1`), câu hỏi hoặc mệnh đề kích thích tư duy.
- **Hero Image**: Ảnh 4K Pexels (dark moody, cinematic silhouette, high contrast).

### B. Smart Vietnamese Title Breaking Engine
- **Không cắt đôi từ ghép/từ láy**: Tự động nhận diện cụm từ cố định tiếng Việt (áo mưa, đề phòng, thuê bao, đám mây, giá trị, ý nghĩa, sáng tạo, thông minh, bao nhiêu, nguy hiểm, v.v.).
- **Cân bằng 2 dòng**: Chia điểm ngắt sao cho độ dài 2 dòng chữ tương đương, tạo khối thị giác chữ nhật vững chắc.
- **Làm sạch ký tự rác**: Tự động loại bỏ toàn bộ dấu ngoặc kép thừa (`"`, `”`, `“`, `'`) trong title.

### C. Lệnh Tạo Cover & Sync Kênh YouTube
```bash
# Tạo cover cho 1 script cụ thể (cả 16:9 & 9:16)
python3 assets/scripts_video/cover_design_engine.py --md assets/scripts_video/your_script.md --both-ratios

# Batch generate cover chuẩn nhận diện cho TOÀN BỘ các video trên kênh ZENPHAM:
python3 assets/scripts_video/cover_design_engine.py --batch-channel ZENPHAM --both-ratios

# Đồng bộ cover lên YouTube API (tự động lưu trạng thái nếu gặp 429 rate limit):
/home/zen/hermes-agent/.venv/bin/python3 assets/scripts_video/sync_channel_covers.py
```

---

## 3. Hệ Thống Giọng Đọc Zen Voice (OmniVoice Engine)

> [!IMPORTANT]
> **CHỐT QUY CHUẨN GIỌNG ĐỌC KÊNH ZENPHAM:**
> - **Voice Model**: `Zen Mien Tay (Zen Meditation)` (File gốc: `assets/voices/Zen Mien Tay/zenpham-zen-meditation-mientay.wav`, catalog: `Zen Mien Tay/zenpham-zen-meditation-mientay`).
> - **Tốc độ đọc chuẩn (Calibrated Speed)**: **`0.94x`** (Bắt buộc cho toàn bộ nội dung tiếng Việt của kênh ZENPHAM).
> - **Profiles Tâm Trạng (`assets/voices/zen_voice_profiles.yaml`)**:
>   - `zen_meditation`: Tốc độ 0.94 (đặc trưng kênh ZenPham: suy tưởng, đĩnh đạc, tĩnh tại).
>   - `am_ap_chua_lanh`: Tốc độ 0.94 (cho chủ đề gia đình, bữa cơm, khoảng lặng).
>   - `suy_tu_tram_lang`: Tốc độ 0.93 (cho chủ đề số phận, công nghệ lấn át, mất mát).
>   - `diem_tinh_khoa_hoc`: Tốc độ 0.94 (cho chủ đề kỹ thuật, kiến trúc AI, code).
> - **Lệnh tạo giọng chuẩn**:
> ```bash
> python3 assets/scripts_video/tts_zen.py --md assets/scripts_video/your_script.md --channel zenpham --mood zen_meditation --speed 0.94
> ```

---

## 4. Quy Chuẩn Cách Ly Footage (Footage Isolation Architecture)

Để **TUYỆT ĐỐI KHÔNG** xảy ra lỗi các video khác nhau dùng chung video footage (như lỗi lặp cảnh đám đông qua đường ở Scene 6):
1. **Cô lập thư mục theo Script Stem**:
   - Footage thô: `assets/scripts_video/clips_raw/<script_stem>/raw_<s:02d>.mp4`
   - Clip xử lý màu/filter: `assets/scripts_video/clips/<script_stem>/clip_<s:02d>.mp4`
   - Audio giọng đọc: `assets/scripts_video/audio/<script_stem>/scene_<s:02d>.wav`
2. **Cấm dùng chung Pool / Silent Fallback**:
   - `assemble_podcast.py` bắt buộc nhận cờ `--clips-dir` trỏ tới thư mục riêng của tập.
   - Nếu thiếu footage cho bất kỳ scene nào, pipeline phải báo lỗi `ContentIntegrityError` và dừng lại để fetch bổ sung, tuyệt đối KHÔNG lấy ngẫu nhiên clip của tập khác đắp vào.
3. **Phân biệt chủ đề ngữ nghĩa khi Fetch**:
   - Mỗi kịch bản có bộ từ khóa `subject_map` riêng biệt, tải ảnh/clip 4K trực tiếp từ Pexels theo đúng mạch nội dung triết học của tập đó.

---

## 5. Quy Trình Sản Xuất End-to-End & Lệnh Chạy

```bash
cd /home/zen/hermes-agent/assets/scripts_video

# Bước 1: Chuẩn bị footage cô lập theo tập (Isolated Stock Fetch)
python3 fetch_stock.py --md your_script.md --raw-dir clips_raw/your_script_stem
python3 post_stock.py --md your_script.md --raw-dir clips_raw/your_script_stem --clips-dir clips/your_script_stem

# Bước 2: Tạo Zen Voice OmniVoice
python3 tts_zen.py --md your_script.md

# Bước 3: Tạo Cover Scene chuẩn Smart Title Break (Cả 16:9 & 9:16)
python3 cover_design_engine.py --md your_script.md --both-ratios

# Bước 4: Assemble video với Anti-Skew, Voice-Driven & Isolated Clips
python3 assemble_podcast.py \
  --md your_script.md \
  --out output/your_video_final.mp4 \
  --audio-dir audio/your_script_stem \
  --clips-dir clips/your_script_stem \
  --voice-driven
```

## 6. Quy Chuẩn Transition Effects & Bù Trừ Thời Gian (Time Offset & Padding)

Chuyển cảnh (transition) giữa các scene bắt buộc tuân thủ nguyên tắc **"Không chém vào lời thoại, bảo toàn trọn vẹn ngữ âm"**:

### A. Quy Tắc Bù Trừ Thời Gian (Padding & Safe Zones)
1. **Head Padding (Đệm đầu cảnh: 0.3s – 0.5s)**:
   - Giọng đọc tuyệt đối không cất lên ở giây `0.0s` khi cảnh mới còn đang fade-in hoặc vừa chuyển cảnh.
   - Bắt buộc có khoảng lặng `0.3s – 0.5s` để cảnh hình ảnh ổn định hoàn toàn rồi giọng đọc mới bắt đầu.
2. **Tail Padding (Đệm cuối cảnh: 0.5s – 0.8s)**:
   - Sau khi âm tiết cuối cùng của câu thoại dứt, bắt buộc giữ khoảng hình ảnh tự nhiên `0.5s – 0.8s` trước khi kích hoạt transition sang cảnh tiếp theo.
   - Tránh hiện tượng chữ cuối cùng bị giật cụt hoặc bị hiệu ứng chuyển cảnh đè lên.
3. **Bù Trừ Overlap (`xfade` / Crossfade / Dissolve)**:
   - Khi dùng hiệu ứng chồng mờ với thời lượng $D_{trans}$ (thường `0.5s`), hai clip sẽ gối lên nhau, làm tổng độ dài video bị hụt đi $D_{trans}$.
   - Độ dài video clip của từng cảnh bắt buộc phải cộng bù thêm:
     $$T_{video\_clip} \ge T_{voice} + T_{head} + T_{tail} + D_{trans}$$
   - Lời thoại và phụ đề Karaoke ASS phải được đặt trong vùng an toàn (`T_safe = [T_head, T_video_clip - T_tail - D_{trans}]`).

### B. Quy Tắc Dip to Black / Breathing Gap
- Khi dùng khoảng thở (Breathing Gap 1.0s – 1.5s) hoặc Dip to Black:
  - Fade-out của cảnh trước diễn ra sau khi voice đã dứt hoàn toàn.
  - Fade-in của cảnh sau hoàn tất trước khi voice mới cất lên.
  - Phụ đề karaoke/SRT phải tịnh tiến (offset) đúng bằng tổng thời lượng các gap tích lũy trước đó, tuyệt đối không bị lệch pha tiếng.

---

## 7. Bắt Buộc Kiểm Định Chất Lượng (Quality Gate Checklist)

Trước khi bàn giao hoặc xuất bản:
- [ ] **Footage Isolation Check**: Mỗi video sử dụng footage từ thư mục `clips/<script_stem>/`, không dùng chung flat clips pool.
- [ ] **Anti-Skew Check**: Xác nhận video 9:16 không bị méo ngang (dùng `scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920`).
- [ ] **Transition Voice Safety**: Kiểm tra điểm nối giữa mọi scene — không có âm tiết nào bị chém cụt hoặc bị transition đè lên.
- [ ] **Audio Volume Integrity**: Chạy `volumedetect` kiểm tra âm lượng ở Scene 1, Scene 3, Scene cuối — đảm bảo `mean_volume > -30 dB` và `max_volume > -12 dB`.
- [ ] **Cover Text Legibility**: Title ngắt câu thông minh, không đứt từ ghép, không chứa dấu ngoặc kép thừa.
- [ ] **Subtitle Alignment**: Karaoke ASS chữ hiển thị khớp từng âm tiết, không lệch pha tiếng do chèn gap/transition.
