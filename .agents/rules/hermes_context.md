# Hermes Workspace Context & Automation Rules

## 1. Hermes Alias Definition
- Khi người dùng nhắc đến **"Hermes"**, luôn hiểu là **Hermes Agent Web Dashboard** tại **`http://127.0.0.1:9119/`** (hoặc `http://10.123.214.1:9119/` trên mạng LXD bridge).
- Mọi rà soát, cấu hình, quản lý sessions, skills, cron, và biến môi trường đều được quy chiếu trực tiếp về giao diện và API của Hermes Web Dashboard (`http://127.0.0.1:9119/`).

## 2. Automated Env & API Key Management Protocol
- Trang cấu hình biến môi trường và API keys nằm tại **`http://127.0.0.1:9119/env`** (quản lý file `~/.hermes/.env`).
- Khi người dùng yêu cầu lấy/cập nhật API keys cho các nhà cung cấp (OpenAI, Anthropic, OpenRouter, Google Gemini, Groq, Fal.ai, Tavily, Telegram,...):
  1. Tự động hóa tối đa quy trình: Điều hướng trình duyệt (Browser Automation) đến trang quản lý API Key của dịch vụ tương ứng.
  2. Người dùng chỉ cần thao tác đăng nhập / xác thực (click & auth).
  3. Agent sẽ tự động trích xuất key, gọi API `PUT /api/env` (với `X-Hermes-Session-Token`) hoặc ghi trực tiếp vào `~/.hermes/.env` và kiểm chứng trạng thái kết nối.

## 3. Antigravity-Telegram Coding Bridge
- Khi nhận tin nhắn Telegram liên quan đến coding/development qua `agy` hoặc Antigravity, tự động load skill `antigravity-telegram` (optional-skills/autonomous-ai-agents/antigravity-telegram).
- Các command pattern từ Telegram: `agy: <prompt>`, `agy status`, `agy diff`, `agy stop`, `agy switch <dir>`.
- **Bảo mật**: Chỉ thực thi coding commands từ users trong `TELEGRAM_ALLOWED_USERS`. Không bao giờ chạy shell commands từ user chưa xác thực.
- **Autopilot**: Sử dụng `/goal` cho long-running coding tasks, `/heartbeat` để giữ agent hoạt động, `/background` cho background execution.
- **Project context**: Khi chưa có working directory, hỏi user chọn project trước khi thực thi `agy`.

## 4. Trae IDE ↔ Telegram Bridge
- Khi nhận tin nhắn Telegram bắt đầu bằng `trae:`, `trae screenshot`, `trae continue`, `trae autopilot`, hoặc `trae project`, tự động load skill `trae-telegram` (optional-skills/autonomous-ai-agents/trae-telegram).
- **Project Selection**: Hỗ trợ chọn project trước khi gửi prompt. Dùng `trae project list` để xem danh sách, `trae project select <name>` để chọn.
- **Project Registry**: Lưu tại `~/.hermes/trae_projects.json`. Auto-discover bằng `trae project discover`.
- **Autopilot State**: Lưu tại `~/.hermes/autopilot.json`. Bật/tắt bằng `trae autopilot on/off`.
- **Scripts**:
  - `~/.hermes/skills/software-development/trae-screen-analyst/trae_bridge.py` — CDP injection, autopilot, project management
  - `~/.hermes/skills/software-development/trae-screen-analyst/runner.py` — screenshot capture, Telegram send

## 5. Project Registry Integration
- Khi user hỏi "chọn project" hoặc "project nào", hiển thị danh sách từ `~/.hermes/trae_projects.json`.
- Active project được sử dụng cho: git diff, prompt injection, completion reports.
- Prefix `[Project: <name> @ <path>]` được thêm vào mọi prompt gửi đến Trae IDE.
