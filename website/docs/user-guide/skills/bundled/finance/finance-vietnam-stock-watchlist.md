---
title: "Vietnam Stock Watchlist — Manage Vietnam stock watchlist for morning daily briefs"
sidebar_label: "Vietnam Stock Watchlist"
description: "Manage Vietnam stock watchlist for morning daily briefs"
---

{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */}

# Vietnam Stock Watchlist

Manage Vietnam stock watchlist for morning daily briefs.

## Skill metadata

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/finance/vietnam-stock-watchlist` |
| Version | `1.0.0` |
| Author | zen |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `finance`, `stock`, `vietnam`, `watchlist`, `telegram` |
| Related skills | [`vietnam-stock-daily-brief`](/docs/user-guide/skills/bundled/finance/finance-vietnam-stock-daily-brief), [`trae-telegram`](/docs/user-guide/skills/bundled/autonomous-ai-agents/autonomous-ai-agents-trae-telegram) |

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# Vietnam Stock Watchlist Manager 📌🇻🇳

Skill quản lý danh mục cổ phiếu quan tâm để nhận báo cáo phân tích chuyên sâu (Technical, Vùng cản/Hỗ trợ, Điểm mua/bán) tự động vào 08:00 AM mỗi sáng.

## When to Use

Sử dụng skill này khi:
- Người dùng yêu cầu **thêm mã cổ phiếu** vào danh mục theo dõi mỗi sáng (ví dụ: `/stock_add FPT HPG`, `/vietnam_stock_watchlist add SSI`, *"Thêm mã FPT vào danh mục theo dõi"*).
- Người dùng yêu cầu **xóa mã cổ phiếu** khỏi danh mục theo dõi (ví dụ: `/stock_remove VNM`, `/vietnam_stock_watchlist remove VNM`, *"Bỏ theo dõi mã VNM"*).
- Người dùng yêu cầu **xem danh sách các mã đang theo dõi** (ví dụ: `/stock_list`, `/vietnam_stock_watchlist list`, *"Xem danh mục cổ phiếu hiện tại"*).

Do NOT use for automated order execution or broker trading.

---

## 🌟 Chức năng & Lệnh Thao Tác:

1. **Thêm mã vào danh mục**:
   - Lệnh Telegram: `/stock_add [MÃ...]` hoặc `/vietnam_stock_watchlist add [MÃ...]`
   - Dòng lệnh shell:
     ```bash
     python3 skills/finance/vietnam-stock-daily-brief/watchlist_manager.py add FPT HPG SSI --notify
     ```

2. **Xóa mã khỏi danh mục**:
   - Lệnh Telegram: `/stock_remove [MÃ...]` hoặc `/vietnam_stock_watchlist remove [MÃ...]`
   - Dòng lệnh shell:
     ```bash
     python3 skills/finance/vietnam-stock-daily-brief/watchlist_manager.py remove VNM --notify
     ```

3. **Xem danh mục cổ phiếu đang theo dõi**:
   - Lệnh Telegram: `/stock_list` hoặc `/vietnam_stock_watchlist list`
   - Dòng lệnh shell:
     ```bash
     python3 skills/finance/vietnam-stock-daily-brief/watchlist_manager.py list
     ```
