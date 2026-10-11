---
name: trae-screen-analyst
description: Inspect Trae IDE screen, click controls, and autopilot.
version: 1.0.0
author: zen
license: MIT
platforms:
- linux
- macos
- windows
metadata:
  hermes:
    tags:
    - trae
    - screen-analyst
    - cdp
    - autopilot
    - ide
    related_skills:
    - trae-telegram
    - electron-ide-cdp-automation
---
# Trae Screen Analyst & Autonomous Co-Pilot Bridge 📸🎯🤖

Skill giúp Hermes Agent đồng hành tự hành cùng Trae IDE (hoặc VS Code) qua CDP debug port và vision screencapture.

## When to Use

Sử dụng skill này khi:
- Người dùng yêu cầu chụp ảnh màn hình hoặc phân tích giao diện Trae IDE.
- Cần tự động phát hiện và click các nút bấm `Continue`, `Always Continue`, `Run in Terminal`, `Allow`, `Confirm` khi Trae AI dừng chờ phê duyệt.
- Xem trạng thái Autopilot (`status`). Hermes autopilot bị vô hiệu hóa; Trae Autopilot Extension là controller duy nhất.
- Tạo báo cáo Git Diff và snapshot màn hình Trae IDE.

Do NOT use for generic web browser automation.

---

## 🛠️ Lệnh thực thi chi tiết:

### 1. Chụp và gửi ảnh màn hình Trae về Telegram:
```bash
# Màn hình chính (Dell DP-1 hoặc Auto-detect)
python3 skills/software-development/trae-screen-analyst/runner.py

# Màn hình Samsung (HDMI-1)
python3 skills/software-development/trae-screen-analyst/runner.py --target hdmi

# Màn hình Laptop (eDP-1)
python3 skills/software-development/trae-screen-analyst/runner.py --target laptop
```

### 2. Gửi tin nhắn / Prompt vào khung chat Trae IDE:
```bash
# Project name bắt buộc; phải match đúng một cửa sổ CDP.
python3 skills/software-development/trae-screen-analyst/trae_bridge.py --send "Hãy viết test unit cho module thanh toán" --project insilos_ee

# Bị từ chối, không fallback active project/monitor:
python3 skills/software-development/trae-screen-analyst/trae_bridge.py --send "Hãy sửa code"
```

### 3. Tìm và click nút `Continue` / `Run` / `Confirm`:
```bash
# Tự động quét Vision và click
python3 skills/software-development/trae-screen-analyst/trae_bridge.py --continue-click --target dell

# Click cưỡng bức vào tọa độ nút mặc định
python3 skills/software-development/trae-screen-analyst/trae_bridge.py --force-click --target dell
```

### 4. Trạng thái Autopilot (HERMES BLOCKED):
```bash
# Hermes autopilot bị vô hiệu hóa. Trae Autopilot Extension (trae-controller) là bộ điều khiển duy nhất.
# `--autopilot on` / `--autopilot daemon` bị chặn — không có hiệu lực.

# Xem trạng thái (chỉ đọc, hợp lệ):
python3 skills/software-development/trae-screen-analyst/trae_bridge.py --autopilot status
```

### 5. Báo cáo hoàn tất tác vụ + Thống kê Git Diff:
```bash
python3 skills/software-development/trae-screen-analyst/runner.py --report
```
