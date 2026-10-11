---
name: agnes-ai-video
description: Generate AI videos via Agnes AI with free quota scheduling.
version: 1.0.0
author: ZENPHAM, Hermes Agent
license: MIT
platforms:
  - linux
  - macos
  - windows
metadata:
  hermes:
    tags:
      - video
      - ai-video
      - agnes-ai
      - free-quota
      - scheduler
      - text-to-video
      - image-to-video
      - media
    related_skills:
      - media-studio
      - traer-telegram
---

# Agnes AI Video Generation & Free Quota Scheduler 🎬✨🤖

Skill kết nối với nền tảng Agnes AI API (`https://apihub.agnes-ai.com/v1`) để tạo video AI chất lượng cao (`agnes-video-2.5`, `agnes-video-2.5-flash`), hỗ trợ Text-to-Video, Image-to-Video và **hệ thống hàng đợi lập lịch tự động tận dụng tối đa hạn mức Free Quota hàng ngày/hàng tuần**.

---

## When to Use

Sử dụng skill này khi:
- Người dùng yêu cầu **tạo video AI từ văn bản hoặc hình ảnh** bằng Agnes AI (ví dụ: *"Tạo video cảnh hoàng hôn trên biển 16:9 bằng Agnes AI"*, *"Lập lịch tạo video shorts 9:16"*).
- Người dùng yêu cầu **lập lịch tự động chạy tạo video khi có hạn mức Free Quota** (`/agnes_schedule`, `/agnes_queue`).
- Người dùng yêu cầu kiểm tra trạng thái kết nối và số lượng model hỗ trợ của Agnes AI (`/agnes_quota`, `/agnes_status`).

Do NOT use for high-frequency real-time video streaming without dedicated bandwidth.

---

## 🌟 Chức năng chính:

1. **Sinh Video AI Đa Tỷ Lệ (Text/Image-to-Video)**:
   - Hỗ trợ các model: `agnes-video-2.5`, `agnes-video-2.5-flash`, `agnes-video-v2.0`.
   - Độ phân giải: `720P`, `1080P`.
   - Tỷ lệ khung hình: `16:9` (Ngang Youtube), `9:16` (Dọc TikTok/Shorts), `1:1` (Vuông Instagram), `21:9` (Cinematic).
2. **Lập Lịch & Hàng Đợi Tự Động Free Quota (Smart Queue Scheduler)**:
   - Lưu trữ các prompt chờ tạo video tại `~/.hermes/agnes_video_queue.json`.
   - Tự động kiểm tra hạn mức miễn phí (Free Quota) và điều phối công việc tạo video khi hạn mức được cấp mới.
   - Tránh lãng phí lượt tạo miễn phí và không bị gián đoạn công việc.
3. **Tự Động Tải & Lưu Trữ Video**:
   - Tự động thăm dò trạng thái (Polling) và tải file video `.mp4` hoàn chỉnh về `./output_videos/`.
4. **Cảnh Báo & Gửi Video Qua Telegram**:
   - Tự động gửi thông báo kèm thông tin video về Telegram ngay khi render hoàn tất.

---

## 🚀 Hướng Dẫn Dòng Lệnh (CLI):

```bash
# 1. Thêm prompt vào hàng đợi tạo video:
python3 skills/creative/agnes-ai-video/scheduler.py --enqueue "cinematic drone shot of ho chi minh city at night, 4k" --aspect-ratio 16:9

# 2. Xử lý hàng đợi tạo video (tự động tải file MP4 & gửi Telegram):
python3 skills/creative/agnes-ai-video/scheduler.py --process-queue --notify

# 3. Xem danh sách các video đang chờ / đã hoàn thành trong hàng đợi:
python3 skills/creative/agnes-ai-video/scheduler.py --list-queue

# 4. Kiểm tra trạng thái kết nối & API Key:
python3 skills/creative/agnes-ai-video/scheduler.py --status

# 5. Đăng ký lịch chạy tự động kiểm tra Free Quota (08:00 & 20:00 hàng ngày):
python3 skills/creative/agnes-ai-video/scheduler.py --install-cron
```

---

## 📱 Lệnh Telegram Tích Hợp:

| Mục đích | Lệnh Telegram (Slash Command) | Ví dụ câu lệnh tự nhiên |
|---|---|---|
| 🎬 **Tạo video ngay** | `/agnes_video [prompt]` | `Tạo video cảnh bình minh Sa Pa bằng Agnes AI` |
| 📋 **Xem hàng đợi video** | `/agnes_queue` | `Xem danh sách video đang đợi tạo` |
| ⏱️ **Lập lịch tạo video free quota** | `/agnes_schedule` | `Lập lịch chạy tạo video khi có free quota` |
| 🔑 **Kiểm tra trạng thái tài khoản** | `/agnes_quota` | `Kiểm tra kết nối Agnes AI` |
