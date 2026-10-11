---
name: vietnam-stock-daily-brief
description: Vietnam stock daily brief, VN-Index & watchlist forecast.
version: 1.3.0
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
    - vnindex
    - forecast
    - watchlist
    - news-monitor
    - deduplication
    - telegram
    related_skills:
    - vietnam-stock-watchlist
    - trae-telegram
---
# Vietnam Stock Daily Brief, Watchlist & Hourly News Monitor 📈🇻🇳📊

Skill phân tích và tổng hợp thông tin chứng khoán đầu ngày, dự báo VN-Index, phân tích chuyên sâu danh mục cổ phiếu theo dõi (Watchlist: FPT, HPG, SSI, MWG, TCB, CII, HBC, REE...) và **giám sát tin tức doanh nghiệp hàng giờ với cơ chế ghi nhớ thông minh lọc bỏ tin trùng lặp**.

## When to Use

Sử dụng skill này khi:
- Người dùng yêu cầu phân tích, điểm tin chứng khoán đầu ngày (08:00 AM).
- Người dùng yêu cầu **thêm/xóa mã cổ phiếu theo dõi** (ví dụ: `/stock_add CII HBC REE`).
- Người dùng yêu cầu **tìm kiếm tin tức hàng giờ, phát hiện tin mới, phân tích chuyên sâu và lọc bỏ tin trùng lặp giữa các báo** (`/stock_news_scan`, `/stock_news_status`).

Do NOT use for individual order placement or trading execution.

---

## 🌟 Chức năng chính:

1. **Giám Sát Tin Tức Doanh Nghiệp Hàng Giờ (Hourly News Monitor & Alert)**:
   - Tần suất: `0 * * * *` (Mỗi 60 phút).
   - Quét tin tức liên tục cho toàn bộ mã trong Watchlist (CII, HBC, REE, FPT, HPG...).
   - **Cơ chế Ghi nhớ Thông minh & Khử Trùng Lặp (Intelligent Semantic Deduplication)**: Phân tích chữ ký sự kiện, đối chiếu mức độ tương đồng tiêu đề/nội dung qua SQLite memory (`~/.hermes/stock_news_memory.sqlite`). Khi nhiều báo cùng đưa tin một sự kiện, hệ thống tự động gộp nguồn và **không bao giờ phân tích hay gửi cảnh báo trùng lặp**!
   - Phân tích chuyên sâu (Bản chất sự kiện, Tác động tài chính/dòng tiền, Tác động giá T+ và Khuyến nghị hành động) và gửi cảnh báo ngay về Telegram.
2. **Quản lý Danh mục Cổ phiếu Theo Dõi (Watchlist)**:
   - Thao tác trực tiếp từ Telegram: `/stock_add`, `/stock_remove`, `/stock_list`.
   - Lưu trữ bền vững tại `~/.hermes/stock_watchlist.json`.
3. **Bản tin Đầu ngày 08:00 AM & Dự báo VN-Index**:
   - Liên thị trường quốc tế (Mỹ, Châu Á, Dầu, Vàng, USD/VND).
   - 3 Kịch bản VN-Index và phân tích kỹ thuật chi tiết từng mã trong Watchlist.

---

## 🚀 Cách chạy dòng lệnh:

```bash
# 1. Giám sát tin tức hàng giờ & lọc tin trùng lặp:
python3 skills/finance/vietnam-stock-daily-brief/news_monitor.py --scan --notify
python3 skills/finance/vietnam-stock-daily-brief/news_monitor.py --symbol CII
python3 skills/finance/vietnam-stock-daily-brief/news_monitor.py --status
python3 skills/finance/vietnam-stock-daily-brief/news_monitor.py --install-cron

# 2. Quản lý danh mục cổ phiếu theo dõi:
python3 skills/finance/vietnam-stock-daily-brief/watchlist_manager.py add CII HBC REE --notify
python3 skills/finance/vietnam-stock-daily-brief/watchlist_manager.py list

# 3. Chạy bản tin buổi sáng (08:00 AM) gửi Telegram:
python3 skills/finance/vietnam-stock-daily-brief/reporter.py
```


