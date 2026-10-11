---
title: "Vietnam Legal Crawler — Hourly crawl & sync Vietnam legal docs with cron management"
sidebar_label: "Vietnam Legal Crawler"
description: "Hourly crawl & sync Vietnam legal docs with cron management"
---

{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */}

# Vietnam Legal Crawler

Hourly crawl & sync Vietnam legal docs with cron management.

## Skill metadata

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/research/vietnam-legal-crawler` |
| Version | `1.0.0` |
| Author | Hermes Agent |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `Legal`, `Vietnam`, `Documents`, `Decrees`, `Circulars`, `Laws`, `Crawler`, `Cron`, `Hourly`, `Knowledge-Sync` |
| Related skills | [`sync-hs-knowledge`](/docs/user-guide/skills/bundled/sync-hs-knowledge/sync-hs-knowledge-sync-hs-knowledge), [`sync-hse-knowledge`](/docs/user-guide/skills/bundled/sync-hse-knowledge/sync-hse-knowledge-sync-hse-knowledge), [`trae-telegram`](/docs/user-guide/skills/bundled/autonomous-ai-agents/autonomous-ai-agents-trae-telegram) |

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# Vietnam Legal Documents Hourly Crawler & Cron Manager 📜⚖️🇻🇳

Tự động thu thập, trích xuất siêu dữ liệu, tải văn bản đính kèm (PDF/DOCX có chữ ký số) và lập lịch cron chạy hàng giờ (**Hourly Crawl**) từ Cổng Thông tin Văn bản Chính phủ (`vanban.chinhphu.vn`) và Cơ sở Dữ liệu Văn bản Pháp luật Quốc gia (`vbpl.vn`).

---

## When to Use

Sử dụng skill này khi:
- Người dùng yêu cầu **tự động thu thập văn bản quy phạm pháp luật** (Luật, Nghị định, Nghị quyết, Quyết định, Thông tư, Công văn) từ các cổng chính thống.
- Người dùng yêu cầu **thiết lập lịch chạy cron hàng giờ (`hourly crawl`)** để theo dõi và tải ngay văn bản mới ban hành mà không bị bỏ sót.
- Người dùng yêu cầu tra cứu, tìm kiếm văn bản pháp luật, trích yếu, số hiệu và tải file đính kèm PDF đã ký số (`/legal_search`).
- Người dùng yêu cầu nhận thông báo tự động về Telegram khi có Nghị định/Thông tư mới ban hành.

Do NOT use for general unauthorized scraping of personal or confidential government intranets.

---

## 🌟 Chức năng chính:

1. **Thu thập Định kỳ Hàng giờ (Hourly Incremental Crawl)**:
   - Tần suất: `0 * * * *` (Mỗi 60 phút / Chạy hàng giờ).
   - Tự động kiểm tra văn bản mới, đối chiếu mã SHA-256 và SQLite checkpoint để tránh tải trùng lặp.
2. **Tải Toàn văn & File đính kèm ký số (Signed PDF/DOCX)**:
   - Tải file PDF chính thức có chữ ký số về kho tri thức `./output_legal_docs/raw/<doc_id>/`.
   - Trích xuất văn bản thuần phục vụ RAG / tìm kiếm vector tại `./output_legal_docs/clean_text/`.
3. **Quản lý Cron Linh hoạt (Cron Manager)**:
   - Đăng ký vào Hermes Cron Scheduler (`~/.hermes/cron/jobs.json`).
   - Hỗ trợ chế độ daemon độc lập: `python3 crawler.py --loop --interval 3600`.
4. **Thông báo Telegram Tức thì**:
   - Gửi tóm tắt Số hiệu, Cơ quan, Người ký, Trích yếu và đường link file PDF ngay khi phát hiện văn bản mới.
5. **Tra cứu & Tìm kiếm Nhanh**:
   - Tìm kiếm tức thì theo số hiệu (VD: `8631`, `08/2015`), cơ quan ban hành hoặc từ khóa chuyên ngành.

---

## 🚀 Hướng Dẫn Sử Dụng:

### 1. Lập lịch Cron Chạy Hàng Giờ (Hourly Cron Registration):
```bash
# Đăng ký cronjob chạy mỗi giờ và gửi cảnh báo Telegram khi có văn bản mới
python3 skills/research/vietnam-legal-crawler/cron_manager.py install

# Kiểm tra trạng thái lập lịch cron và số lượng văn bản đã lưu
python3 skills/research/vietnam-legal-crawler/cron_manager.py status --telegram

# Hủy đăng ký cronjob
python3 skills/research/vietnam-legal-crawler/cron_manager.py uninstall
```

### 2. Chạy Thu Thập Thủ Công Ngay Lập Tức:
```bash
# Chạy một chu kỳ quét và tải văn bản mới (kèm file PDF)
python3 skills/research/vietnam-legal-crawler/crawler.py --notify

# Chạy ở chế độ tiến trình nền (Hourly Daemon Loop)
python3 skills/research/vietnam-legal-crawler/crawler.py --loop --interval 3600 --notify
```

### 3. Tìm Kiếm Văn Bản Trong Kho Dữ Liệu:
```bash
python3 skills/research/vietnam-legal-crawler/search.py "Hải quan" --telegram
python3 skills/research/vietnam-legal-crawler/search.py "8631/VPCP-PL"
```

---

## 📱 Lệnh Telegram Tích Hợp:

| Mục đích | Lệnh Telegram |
|---|---|
| 🔄 **Thu thập văn bản mới ngay** | `/legal_crawl` |
| ⏱️ **Xem trạng thái lập lịch Hourly Cron** | `/legal_cron_status` |
| 🔍 **Tìm kiếm văn bản pháp luật** | `/legal_search [từ khóa / số hiệu]` |

---

## 📂 Cấu Trúc Thư Mục Lưu Trữ:

<!-- ascii-guard-ignore -->
```
output_legal_docs/
├── raw/                                  # Chứa thư mục từng văn bản và file PDF ký số
│   └── <doc_id>/
│       ├── metadata.json                 # Số hiệu, ngày ban hành, người ký, trích yếu
│       └── <file_name>.signed.pdf        # File PDF đính kèm chính thức
├── clean_text/                           # Văn bản thuần phục vụ RAG / AI Chat
│   └── <doc_id>_<so_hieu>.txt
├── manifest.json                         # Thống kê tổng hợp thời gian thực
└── history.sqlite                        # SQLite DB lưu checkpoint và lịch sử crawl
```
<!-- ascii-guard-ignore-end -->
