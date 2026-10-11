---
title: "Media Asset Bank — Manage Cyber-Zen footage bank with metadata and AI quota"
sidebar_label: "Media Asset Bank"
description: "Manage Cyber-Zen footage bank with metadata and AI quota"
---

{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */}

# Media Asset Bank

Manage Cyber-Zen footage bank with metadata and AI quota.

## Skill metadata

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/creative/media-asset-bank` |
| Version | `1.0.0` |
| Author | ZENPHAM, Hermes Agent |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `media-bank`, `footage`, `video`, `images`, `metadata`, `cyber-zen`, `free-quota`, `b-roll`, `podcast`, `youtube`, `x`, `facebook` |
| Related skills | [`agnes-ai-video`](/docs/user-guide/skills/bundled/creative/creative-agnes-ai-video), [`media-studio`](/docs/user-guide/skills/bundled/media/media-media-studio), [`youtube-publisher`](/docs/user-guide/skills/bundled/media/media-youtube-publisher), [`facebook-publisher`](/docs/user-guide/skills/bundled/social-media/social-media-facebook-publisher), [`x-publisher`](/docs/user-guide/skills/bundled/social-media/social-media-x-publisher) |

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# Media Asset Bank & Cyber-Zen Footage Hub 🎬🖼️💎

Hệ thống quản lý và làm giàu kho tư liệu hình ảnh & video (**Footage & Image Bank**) chuẩn hóa theo bộ nhận diện phong cách **"Cyber-Zen Tech"** (Obsidian Dark `#0B0C0E`, Electric Cyan `#00F2FE`, Cyber Amethyst `#7F00FF`, Zen Amber `#FFB703`).

Hệ thống lưu trữ đầy đủ **Metadata chi tiết**, hỗ trợ **FTS5 tìm kiếm toàn văn siêu tốc**, và tự động tích hợp với **Agnes AI Free Quota Scheduler** để liên tục sinh footage B-roll phục vụ sản xuất video YouTube, X, Facebook và Podcast trong tương lai.

---

## When to Use

Sử dụng skill này khi:
- Người dùng muốn **tìm kiếm footage hoặc hình ảnh theo chủ đề** để làm video/podcast (ví dụ: *"Tìm footage B-roll về AI brain 16:9"*, *"Tìm ảnh nền studio podcast"*).
- Người dùng muốn **thu hoạch và sinh thêm footage mới từ kho prompt chuẩn hóa bằng Free Quota** (`/footage_harvest`, `--enqueue-seed`).
- Người dùng muốn **kiểm tra danh mục, metadata hoặc số lượng footage hiện có trong kho** (`/media_bank_status`, `--status`).
- Tích hợp tự động vào `media-studio` khi lắp ráp video YouTube Shorts hoặc X Threads.

---

## 🌟 6 Phân Loại Chủ Đề Cốt Lõi:

1. 🧠 `ai_brain`: Neural Network, Quantum Core, AI Agent Swarm, Data Waves.
2. 💻 `dev_workspace`: Bàn làm việc ThinkPad, gõ bàn phím cơ, code OLED dọc, đèn ấm, trà đạo.
3. 🌐 `cloud_infra`: Tủ rack máy chủ, cáp quang phát sáng, microservices container 3D.
4. 📈 `fintech_market`: Biểu đồ nến hologram 3D, radar phân tích thị trường, dòng tiền thông minh.
5. 🎙️ `podcast_studio`: Micro Shure SM7B, phòng thu vách gỗ tiêu âm, sóng âm thanh phát quang.
6. 🏙️ `smart_city`: Drone view TP.HCM / Hà Nội / Cầu Rồng Đà Nẵng lung linh về đêm.

---

## 🛠️ Hướng Dẫn Dòng Lệnh (CLI):

```bash
# 1. Thu hoạch footage mới từ thư viện 30+ prompt chuẩn hóa (dùng Free Quota):
python3 skills/creative/media-asset-bank/harvest_free_quota.py --enqueue-seed --limit 5

# 2. Thu hoạch footage theo chủ đề và tỷ lệ cụ thể:
python3 skills/creative/media-asset-bank/harvest_free_quota.py --enqueue-seed --category ai_brain --aspect-ratio 16:9
python3 skills/creative/media-asset-bank/harvest_free_quota.py --enqueue-seed --category dev_workspace --aspect-ratio 9:16

# 3. Tìm kiếm footage trong kho tư liệu:
python3 skills/creative/media-asset-bank/harvest_free_quota.py --search "neural brain"
python3 skills/creative/media-asset-bank/harvest_free_quota.py --search "server datacenter"

# 4. Xem thống kê toàn bộ kho footage & dung lượng:
python3 skills/creative/media-asset-bank/harvest_free_quota.py --status

# 5. Đồng bộ các video hoàn tất từ hàng đợi vào kho tư liệu:
python3 skills/creative/media-asset-bank/harvest_free_quota.py --ingest
```

---

## 📱 Lệnh Telegram Tích Hợp:

| Mục đích | Lệnh Telegram (Slash Command) | Ví dụ câu lệnh tự nhiên |
|---|---|---|
| 🔍 **Tìm kiếm footage** | `/footage_search [từ khóa]` | `Tìm footage máy chủ data center 16:9` |
| 🌾 **Thu hoạch footage mới** | `/footage_harvest [số lượng]` | `Thu hoạch thêm 5 footage AI brain bằng free quota` |
| 📊 **Trạng thái kho tư liệu** | `/media_bank_status` | `Kiểm tra số lượng video và ảnh trong kho` |
