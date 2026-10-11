---
name: vietnam-stock-watchlist
description: Manage Vietnam stock watchlist for morning daily briefs.
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
    - finance
    - stock
    - vietnam
    - watchlist
    - telegram
    related_skills:
    - vietnam-stock-daily-brief
    - trae-telegram
---
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
