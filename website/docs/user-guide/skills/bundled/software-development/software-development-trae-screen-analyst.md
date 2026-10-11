---
title: "Trae Screen Analyst — Inspect Trae IDE screen, click controls, and autopilot"
sidebar_label: "Trae Screen Analyst"
description: "Inspect Trae IDE screen, click controls, and autopilot"
---

{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */}

# Trae Screen Analyst

Inspect Trae IDE screen, click controls, and autopilot.

## Skill metadata

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/software-development/trae-screen-analyst` |
| Version | `1.0.0` |
| Author | zen |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `trae`, `screen-analyst`, `cdp`, `autopilot`, `ide` |
| Related skills | [`trae-telegram`](/docs/user-guide/skills/bundled/autonomous-ai-agents/autonomous-ai-agents-trae-telegram), [`electron-ide-cdp-automation`](/docs/user-guide/skills/bundled/software-development/software-development-electron-ide-cdp-automation) |

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

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
python3 skills/software-development/trae-screen-analyst/trae_bridge.py --send "Hãy viết test unit cho module thanh toán" --target dell
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
