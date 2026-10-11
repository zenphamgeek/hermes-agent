---
name: toi-doc-sach
description: Production and script-writing skill for "Tôi Đọc Sách" channel (Literary & philosophical essays, 5-Act long-form 16:9, contemplative shorts 9:16, smart-break cover scenes, and scholar aesthetics).
version: 2.0.0
author: ZENPHAM, Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [books, philosophy, literature, video-essay, shorts, toi-doc-sach, cover-engine]
    related_skills: [zenpham-podcast-producer, omnivoice-reader]
---

# Tôi Đọc Sách — Production Skill (v2.0)

Hệ thống sản xuất nội dung chuẩn xác cho kênh **TÔI ĐỌC SÁCH** — Thể loại: **Tiểu luận triết học, trích dẫn văn học kinh điển (Lão Trang, Nam Hoa Kinh, Khắc kỷ, Hiện sinh, văn học tinh hoa)**. Phong cách: **Học giả mộc mạc, chiêm nghiệm đời thường, sâu sắc, không tóm tắt hời hợt, không lên lớp**.

## 1. Hai Thể Loại Nội Dung Thiết Kế Chuẩn

### A. Long-Form Video Essay (10–15 phút — 16:9 — 1920x1080)
- **Cấu trúc 5 Hồi (5-Act Essay Model)**:
  1. **Hồi 1: Cửa vào & Nghịch lý (120–180s)**: Một va chạm thực tế đời sống hiện đại dẫn vào nghịch lý triết học.
  2. **Hồi 2: Bối cảnh & Luận điểm gốc (180–240s)**: Đặt tư tưởng vào đúng bối cảnh lịch sử của tác giả, dẫn nguồn văn bản chính xác.
  3. **Hồi 3: Va chạm đời thường (240–300s)**: 2 tình huống thực tế để người xem tự soi chiếu bản thân.
  4. **Hồi 4: Khắc kỷ vs Hiện sinh (180–240s)**: Đối thoại lăng kính triết học đa chiều, chỉ ra ranh giới và giới hạn của quan điểm.
  5. **Hồi 5: Lắng đọng & Câu hỏi mở (60–120s)**: Không kết luận giáo điều, kết thúc bằng một câu hỏi sống để lại cho người xem.
- **Quy chuẩn kỹ thuật**:
  - Độ dài: ~1.400 – 1.900 từ tiếng Việt.
  - Nhịp đọc: 115 – 125 WPM (từ/phút), thong dong, có điểm ngưng thở.
  - Phụ đề: Documentary subtitle nhã nhặn dưới đáy (không dùng karaoke nhảy nhót cho long-form).
- **Cơ cấu hình ảnh Hybrid Visual (16:9)**:
  - `50%`: B-roll đời sống mộc mạc, tĩnh lặng (ngõ nhỏ, góc phố, mưa rơi, bàn làm việc, tàu xe).
  - `25%`: Typographic Quote Cards (thẻ chữ trích dẫn sách trang nhã, font Serif cổ điển).
  - `15%`: Archival Book Covers & Artwork (bản scan bìa sách cổ, tranh khắc gỗ, tư liệu tác giả).
  - `10%`: Transition Pauses (khoảng lặng 2–3s chỉ có cảnh vật và tiếng thở/nhạc nền để ngấm ý).

### B. Shorts / Reels Triết Lý (90s–120s — 9:16 — 1080x1920)
- **Cấu trúc**: 8–12 scenes, 8–10s/scene. 1 hook nghịch lý -> 1 câu trích dẫn khai sáng -> 1 câu hỏi mở.
- **Anti-Skew**: Bắt buộc xử lý scale + crop (`scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920`) để footage không bị méo.
- **Phụ đề**: Karaoke ASS màu vàng ấm hoặc kem ngà, canh lề dưới vừa mắt.

---

## 2. Quy Chuẩn Cover Scene & Thumbnail Engine (`cover_design_engine.py`)

- **Brand Badge**: `📖  TÔI ĐỌC SÁCH` (Deep Forest Sage `#46825A`, bo góc trang nhã).
- **Typography**: `NotoSerif-Bold` (font chữ có chân kinh điển của giới học giả, sách báo).
  - Dòng 1: Kem ngà ấm áp (`#FFFAF0`).
  - Dòng 2: Hổ phách Amber (`#E6C382`).
- **Hero Background**: Thư phòng cổ điển, trang sách mở, tách trà, ánh nắng chiều rọi qua ô cửa sổ, hạt bụi nắng lơ lửng.
- **Smart Title Breaking**: Tự động nhận diện cụm từ sách và triết học ("Nam Hoa Kinh", "Bình thường", "Thấu hiểu", v.v.), không bẻ gãy danh từ hoặc câu trích dẫn.

### Lệnh tạo Cover:
```bash
# Thumbnail 16:9 cho Video Essay
python3 assets/scripts_video/cover_design_engine.py --md assets/scripts_video/toi_doc_sach_your_script.md

# Cover 9:16 cho Shorts
python3 assets/scripts_video/cover_design_engine.py --md assets/scripts_video/toi_doc_sach_your_script.md --portrait
```

---

## 3. Quy Trình Sản Xuất & Lệnh Chạy

```bash
cd /home/zen/hermes-agent/assets/scripts_video

# 1. Tạo Zen Voice (chậm, trải nghiệm, miền Tây ấm áp)
python3 tts_zen.py --md toi_doc_sach_your_script.md --mood chiem_nghiem_tinh_lang --speed 0.94

# 2. Tạo Cover Scene chuẩn Smart Title Break
python3 cover_design_engine.py --md toi_doc_sach_your_script.md

# 3. Chạy Pipeline sản xuất hoàn chỉnh (hỗ trợ cả batch release)
python3 run_toi_doc_sach_full_release.py
```

---

## 4. Bắt Buộc Kiểm Định Chất Lượng (Quality Gate)

- [ ] **Nguồn gốc chính xác**: Mọi trích dẫn phải kiểm chứng trang sách thật (dùng `web_search`), không bịa đặt nguồn.
- [ ] **Âm lượng xuyên suốt**: Dùng `volumedetect` kiểm tra âm thanh giữa các hồi — đảm bảo không bị drop audio hoặc silence sau Hồi 1.
- [ ] **Cân đối thị giác**: Đảm bảo đủ tỉ lệ 50% B-roll + 25% Quote cards + 15% Book covers + 10% Pauses.
- [ ] **Footage Độc Lập Giữa Các Tập (BẮT BUỘC - ZERO FOOTAGE REUSE)**:
  - Tuyệt đối không dùng lặp lại B-roll footage, hình ảnh minh họa giữa các tập khác nhau trong series "Tôi Đọc Sách" (cả Video 16:9 Longform và 9:16 Shorts).
  - Mỗi tập phải có kho B-roll và tranh khắc gỗ/tư liệu riêng biệt, cấp phát từ kho lưu trữ độc lập.
  - Chạy `python3 assets/scripts_video/audit_series_footage.py --series toi_doc_sach --audit` đạt 0% trùng lặp trước khi render/publish.
  - **Âm nhạc bản quyền sạch:** Nghiêm cấm dùng nhạc có bản quyền (ví dụ `soft_piano_ambient.mp3`), chỉ dùng nhạc trong `assets/background_music/`.

