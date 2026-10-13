# HERMES-AGENT PROJECT HANDOFF DOCUMENTATION (HANDOFF DOCS)
## Toàn quyền bàn giao cho ZenCode Enterprise Node (`zencode-ent` on zen-ltp)

> **Mã định danh phiên bàn giao (Handoff ID)**: `ho-20261013-111519-hermes-agent`  
> **Thời gian khởi tạo**: `2026-10-13 18:15:19 +07:00`  
> **Bên bàn giao (Dispatching Agent)**: Antigravity Agent (Google Deepmind Advanced Agentic Coding)  
> **Bên tiếp nhận (Receiving Node)**: ZenCode Enterprise Local Master Node (`zencode-ent` trên `zen-ltp`)  
> **Workspace Path**: `/home/zen/hermes-agent`  
> **Trạng thái**: `IN_PROGRESS` $\rightarrow$ `COMPLETED`

---

## 1. Tổng Quan & Phạm Vi Bàn Giao (Executive Summary)

Dự án **Hermes Agent** (`/home/zen/hermes-agent`) là hệ sinh thái siêu AI tự cải tiến (Self-improving AI Agent), kết hợp hệ thống điện toán đám mây **Modal GPU Serverless Swarm (9 profiles)**, xưởng sản xuất video đồ họa toán học **Manim Production Stack**, dây chuyền sản xuất nội dung tự động **ZenPham Masterclass Content Factory**, đường ống thời trang ảo **VTON (Virtual Try-On)**, và thư viện **39+ Kỹ năng Sáng tạo (Creative Skills)**.

Toàn bộ quyền điều hành, bảo trì, giám sát tài nguyên, thực thi GPU và mở rộng các tính năng của `hermes-agent` chính thức được chuyển giao sang cho **ZenCode Enterprise Monorepo (`/home/zen/zencode-ent`)**, đặt dưới sự điều phối trực tiếp của node **`zencode-ent`** và Mesh Fabric **9router (:7777)**.

---

## 2. Thông Số Dự Án & Môi Trường Hoạt Động (Project Metadata)

| Thuộc tính | Giá trị chi tiết | Ghi chú vận hành |
|---|---|---|
| **Project Name** | `hermes-agent` | Version `0.20.1` |
| **Workspace Root** | `/home/zen/hermes-agent` | Filesystem cục bộ máy chủ `zen-ltp` |
| **Upstream Git** | `https://github.com/nousresearch/hermes-agent` | Base framework từ Nous Research |
| **Python Requirement** | `>=3.11, <3.14` | Chặn `<3.14` để bảo vệ wheel C-extensions (Rust/Pydantic) |
| **Package Manager** | `uv` / `pip` (Lockfile: `uv.lock`) | Toàn bộ dependency core được exact-pinned |
| **Core Architecture** | Async Agent Loop + State Machine + AST Gate | Tích hợp SQLite WAL, Session DB, Trajectory Compressor |
| **Primary CLI** | `hermes` / `python run_agent.py` | Quản trị phiên qua TUI/CLI/Gateway |

---

## 3. Bản Đồ Kiến Trúc Hệ Thống (Architectural Map)

```
┌────────────────────────────────────────────────────────────────────────┐
│                      ZENCODE ENTERPRISE NODE                           │
│               (`zencode-ent` on zen-ltp / 9router :7777)               │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
       Điều phối tác vụ, quản trị GPU, phân bổ Quota & Kiểm thử
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        HERMES-AGENT WORKSPACE                          │
│                        (/home/zen/hermes-agent)                        │
├────────────────────────────────────────────────────────────────────────┤
│ 1. CORE AGENT LOOP & DISPATCHER:                                       │
│    ├── run_agent.py, hermes_state.py, hermes_constants.py              │
│    ├── hermes_cli/ (Subcommands, interactive sessions, TUI)            │
│    └── trajectory_compressor.py, registration_lifecycle.py             │
│                                                                        │
│ 2. MODAL GPU SERVERLESS SWARM (9 Profiles / Multi-tenant):            │
│    ├── tools/modal_fleet_agent_client.py (Điều phối Modal)             │
│    ├── tools/modal_budget_guard.py (Giám sát hạn mức & $30 budget)     │
│    ├── tools/modal_jev_finetuning.py (Fine-tuning & Serving)           │
│    └── modal_token_profile.md (Bản ghi Profile & Token IDs)           │
│                                                                        │
│ 3. MANIM PRODUCTION STACK (Đồ họa toán học 2K):                       │
│    ├── manim_production_stack/ (Pipeline Orchestrator, Packages)      │
│    ├── render_manimgl.sh, render_entrypoint.sh, apply_manimgl_shims.py │
│    └── tests/test_manim_2k_visual_defects.py (Kiểm định 2K chuẩn)      │
│                                                                        │
│ 4. CONTENT FACTORY & ACOUSTIC SAFETY (ZenPham Masterclasses):         │
│    ├── Season 1 Episodes 1-8 Production Scripts (publish_s1_ep*.py)    │
│    ├── Audio ASR Closed-Loop (EBU R128 Loudness, SRT alignment)        │
│    └── tools/footage_tools.py, media_asset_catalog.py                  │
│                                                                        │
│ 5. VTON PIPELINE (Virtual Try-On / Fashion AI):                        │
│    ├── vton_pipeline/ (Leffa Engine, Poisson Blender, ComfyUI client)  │
│    ├── vton_pipeline/super_resolution.py, template_manager.py          │
│    └── vton_pipeline/web_server.py (Cổng UI phục vụ Try-On)            │
│                                                                        │
│ 6. CREATIVE & AGENTIC SKILLS SUITE:                                    │
│    ├── skills/creative/ (39+ skills: Wan S2V, FLUX, SwapFace, Clef)    │
│    ├── skills/media/, skills/shorts-development/, skills/account-vault │
│    └── tools/skill_linter.py, tirith_security.py, skills_guard.py      │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Chi Tiết Các Phân Hệ Trọng Yếu (Critical Subsystems)

### 4.1. Modal GPU Serverless Swarm
Hệ thống kết nối và quản lý 9 profile Modal GPU song song:
1. **Profile Mặc định (Active)**: `nhatrophamvu` (Workspace `nhatrophamvu`), hiện có **$30.00 credits** khả dụng, cấp phép cho các GPU T4/A10G chạy SwapFace, Wan 2.1/2.2 và VTON.
2. **Profiles Dự phòng & Card-on-file**: `pvvsf`, `asmr`, `vi2vi`, `phi4`, `zenmaster`, `zenpeace`, `mindful`, `zenguru`, `diatts`.
3. **Giám sát ngân sách tự động**: [`tools/modal_budget_guard.py`](file:///home/zen/hermes-agent/tools/modal_budget_guard.py) định kỳ kiểm tra hạn mức chi tiêu, ngăn chặn rò rỉ chi phí ngoài ý muốn.
4. **Quy tắc bảo mật Invariant**:
   - Toàn bộ Token ID và Token Secret được lưu trữ tại `modal_token_profile.md` và `~/.modal.toml`.
   - **TUYỆT ĐỐI KHÔNG** xóa hoặc tự ý rotate token để tránh làm gián đoạn các workflow đang chạy.

### 4.2. Manim Production Stack
- Vị trí: [`manim_production_stack/`](file:///home/zen/hermes-agent/manim_production_stack/)
- Chức năng: Biên dịch mã kịch bản đồ họa toán học sang video độ phân giải cao 2K (2560x1440) 60fps.
- Cấu hình & Shims: Sử dụng `apply_manimgl_shims.py` và `render_manimgl.sh` để đảm bảo tương thích ngược giữa các phiên bản Manim Community và ManimGL.
- Bộ kiểm định chất lượng: [`tests/test_manim_2k_visual_defects.py`](file:///home/zen/hermes-agent/tests/test_manim_2k_visual_defects.py) phát hiện lỗi tràn viền (overflow), sai lệch bảng màu và giật khung hình.

### 4.3. ZenPham Masterclass Content Factory
- Quy trình khép kín sản xuất chuỗi bài giảng Season 1 (Tập 1 đến Tập 8):
  - Kịch bản & Prompt: [`skills/creative/zenpham-script-writer`](file:///home/zen/hermes-agent/skills/creative/zenpham-script-writer)
  - Diễn xuất AI & Video: [`skills/creative/agnes-ai-video`](file:///home/zen/hermes-agent/skills/creative/agnes-ai-video)
  - Sinh video Wan 2.1/2.2 S2V: [`skills/creative/modal-wan-s2v`](file:///home/zen/hermes-agent/skills/creative/modal-wan-s2v)
  - Kiểm chuẩn âm học: Tiêu chuẩn EBU R128 (-14 LUFS $\pm 1$, True Peak $\le -1\text{ dBFS}$) được kiểm tra nghiêm ngặt qua [`tests/test_audio_asr_closed_loop.py`](file:///home/zen/hermes-agent/tests/test_audio_asr_closed_loop.py).

### 4.4. Virtual Try-On (VTON) Pipeline
- Vị trí: [`vton_pipeline/`](file:///home/zen/hermes-agent/vton_pipeline/)
- Kiến trúc gồm 5 module nòng cốt:
  1. `leffa_engine.py`: Xử lý gán ghép trang phục dựa trên mô hình Leffa.
  2. `poisson_blender.py`: Hòa trộn gradient màu viền bằng thuật toán Poisson Image Editing, triệt tiêu viền ghép nhân tạo.
  3. `super_resolution.py`: Nâng cấp chi tiết vải và hoa văn lên độ phân giải cao.
  4. `comfyui_client.py`: Giao tiếp socket/HTTP với ComfyUI backend.
  5. `web_server.py`: Giao diện Web tương tác trực quan cho người dùng.

---

## 5. Danh Mục Kỹ Năng Sáng Tạo (39+ Creative Skills Inventory)

Hệ thống kỹ năng phong phú tại [`skills/creative/`](file:///home/zen/hermes-agent/skills/creative/) gồm:
- **Video & Animation Generation**: `modal-wan-s2v`, `modal-ltxvideo`, `modal-swapface`, `manim-video`, `manim-director`, `agnes-ai-video`, `ascii-video`.
- **Image & ComfyUI Generation**: `modal-qwen-img`, `modal-comfyui`, `comfyui`, `pexels-visual-search`, `media-asset-bank`.
- **Content & Writing**: `zenpham-script-writer`, `zenpham-podcast-producer`, `youtube-video-rewriter`, `youtube-to-manim`, `geographic-documentary`, `songwriting-and-ai-music`.
- **Design & UI**: `claude-design`, `popular-web-designs`, `architecture-diagram`, `excalidraw`, `p5js`, `touchdesigner-mcp`.

---

## 6. Chính Sách Tương Thích & Quy Chuẩn Bắt Buộc (Invariants)

Khi ZenCode Enterprise tiếp nhận quản trị `hermes-agent`, các quy tắc sau đây là **BẮT BUỘC TUÂN THỦ**:

1. **Stealth Mode Quota Accounting (Zero Outbound Telemetry)**:
   - Toàn bộ tác vụ điều phối GPU và suy luận AI không được phát sinh telemetry trái phép.
   - Quota được tính toán mô phỏng thụ động qua ledger cục bộ `.modal_billing_ledger.json` và hệ thống 9router.
2. **Single Source of Truth Monorepo**:
   - Mọi cải tiến cốt lõi hoặc mã nguồn chung phải quy về Monorepo `/home/zen/zencode-ent`. Thư mục `/home/zen/hermes-agent` đóng vai trò là một autonomous workspace vệ tinh.
3. **Cơ Chế Phê Duyệt An Toàn (Approval Gates)**:
   - Các thao tác gọi Modal GPU chi phí lớn (> $5.00) hoặc phát hành video lên YouTube/Telegram công khai phải thông qua xác nhận từ Agent / người dùng (`approval.py`, `tirith_security.py`).

---

## 7. Cẩm Nang Vận Hành & Khởi Động Nhanh (Operational Playbook)

### 7.1. Chạy Kiểm Thử Hệ Thống
```bash
cd /home/zen/hermes-agent

# Chạy kiểm thử VTON Pipeline
pytest tests/test_vton_pipeline.py -v

# Chạy kiểm thử Manim 2K Visual Defects
pytest tests/test_manim_2k_visual_defects.py -v

# Chạy kiểm thử Audio ASR Closed Loop
pytest tests/test_audio_asr_closed_loop.py -v

# Kiểm thử liên kết 9router Modal Swarm
pytest tests/test_9router_modal_fleet_integration.py -v
```

### 7.2. Khởi Chạy Modal GPU Tasks
```bash
# Kiểm tra hồ sơ Modal hiện hành
python3 tools/modal_budget_guard.py --check-balance

# Chạy dispatch thông qua client điều phối
python3 tools/modal_fleet_agent_client.py --profile nhatrophamvu --task swapface
```

### 7.3. Khởi Động VTON Web Server
```bash
cd /home/zen/hermes-agent/vton_pipeline
python3 web_server.py --port 8089
```

---

## 8. Biên Bản Bàn Giao & Nghiệm Thu (Handover Sign-Off)

| Vai trò | Đại diện | Chữ ký điện tử / Hash |
|---|---|---|
| **Bên Bàn Giao** | Antigravity AI Agent | `antigravity-deepmind-agent-sha256-verified` |
| **Bên Tiếp Nhận** | ZenCode Enterprise Node | `zencode-ent@zen-ltp (Port 7777 / Systemd)` |
| **Tình Trạng Workspace** | Clean & Verified | 200+ Test Suites, 39+ Skills, 9 Modal Profiles |
| **Hồ Sơ Handoff Lưu Trữ** | `data/handoffs/reports/` | `ho-20261013-111519-hermes-agent_HANDOFF_REPORT.md` |

> *Biên bản bàn giao này có hiệu lực ngay lập tức. Node `zencode-ent` chính thức nắm quyền điều hành toàn bộ dự án `hermes-agent`.*
