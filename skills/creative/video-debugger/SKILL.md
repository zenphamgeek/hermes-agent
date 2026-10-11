---
name: video-debugger
description: "Intelligent Video Debugger for YouTube productions. Accepts a YouTube video URL and issue description, locates corresponding script/Manim source/staging files, determines whether fix can be applied in-place (Metadata, Thumbnail, Captions, YouTube Studio Trim) or requires a Seamless Master Replacement (re-rendering flawed Manim scenes, re-compiling 2K master, swapping playlist position, and updating Shorts)."
version: 1.0.0
author: ZENPHAM & Antigravity
platforms: [linux, macos]
metadata:
  hermes:
    tags: [video-debugging, youtube, manim, hotfix, content-factory]
    related_skills: [manim-production, toi-lam-viec, youtube-publisher]
---

# Video Debugger — Master Workflow Guide

> *"Chất lượng không bao giờ là sự ngẫu nhiên. Khi một lỗi xuất hiện, hệ thống phải xác định chính xác tầng lỗi (Metadata, Phụ đề, Âm thanh hay Hoạt cảnh Manim) và đưa ra phương án xử lý nhanh nhất, bảo toàn dữ liệu người xem tối đa."*

## 1. Bản Chất Kỹ Thuật Nền Tảng YouTube
- **Bất biến của YouTube (Anti-Bait-and-Switch Invariant):** YouTube **tuyệt đối không cho phép upload đè file video mới lên cùng một Video ID / URL**. Đây là chính sách chống lừa đảo toàn cầu của Google nhằm ngăn chặn việc thay thế nội dung sau khi đã gom hàng triệu view.
- **Những gì sửa được trực tiếp trên URL cũ (In-Place Fixes):**
  1. `Tiêu đề (Title)`, `Mô tả (Description)`, `Chapters (Timestamps)`, `Tags`.
  2. `Ảnh bìa (Thumbnail 16:9)`.
  3. `Phụ đề (Captions / Softsub SRT)`.
  4. `Cắt bỏ đoạn lỗi ngắn (Trim / Cut)` qua YouTube Studio Video Editor.
- **Khi nào bắt buộc phải thực hiện Seamless Master Replacement:**
  Khi lỗi sai nằm ở **công thức toán học Manim, visual glitch lớn, hoặc âm thanh giọng đọc**, bắt buộc phải biên dịch lại scene Manim và xuất bản video mới thay thế.

## 2. Quy Trình Khắc Phục Tự Động (Execution Flow)

```mermaid
graph TD
    A["Nhận URL YouTube & Mô tả lỗi"] --> B["Trích xuất Video ID & Tra cứu Tập"]
    B --> C{"Phân loại lỗi"}
    C -->|"Text / Meta / Chapters"| D["Cập nhật In-Place qua YouTube API (Giữ nguyên URL)"]
    C -->|"Ảnh bìa / Thumbnail"| E["Tải ảnh mới qua thumbnails().set (Giữ nguyên URL)"]
    C -->|"Phụ đề SRT"| F["Cập nhật softsub.srt qua captions() (Giữ nguyên URL)"]
    C -->|"Visual Manim / Audio"| G["Quy trình Seamless Master Replacement"]
    G --> G1["Sửa mã nguồn Manim / Kịch bản scene bị lỗi"]
    G1 --> G2["Biên dịch lại duy nhất scene đó chuẩn 2K QHD 60fps"]
    G2 --> G3["Ghép lại Master sạch trong youtube_staging/tap_XX/"]
    G3 --> G4["Upload video mới lên YouTube"]
    G4 --> G5["Hoán đổi vị trí video mới trong Official Playlist (PLPJRpJBBHEOY)"]
    G5 --> G6["Ghim comment ở video cũ & chuyển sang Private/Unlisted"]
    G6 --> G7["Cập nhật Short 30s trỏ về video mới"]
```

## 3. Lệnh Vận Hành

```bash
# 1. Chẩn đoán và lập kế hoạch sửa lỗi
python3 skills/creative/video-debugger/scripts/video_debugger.py \
  --url "https://youtu.be/HmFA2JUmjKg" \
  --issue "phút 02:15 công thức ma trận bị thiếu chỉ số dưới"

# 2. Định vị tài sản tự động:
#    - assets_located: script.md, manim.py, metadata.json, softsub.srt, video.mp4
```
