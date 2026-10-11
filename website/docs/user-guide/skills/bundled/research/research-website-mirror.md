---
title: "Website Mirror — Mirror a full website to assets/website/<name> on schedule"
sidebar_label: "Website Mirror"
description: "Mirror a full website to assets/website/<name> on schedule"
---

{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */}

# Website Mirror

Mirror a full website to assets/website/&lt;name> on schedule.

## Skill metadata

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/research/website-mirror` |
| Version | `0.1.0` |
| Author | Hermes Agent |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `Mirror`, `Crawler`, `Website`, `Archive`, `Deploy`, `Cron` |
| Related skills | [`blogwatcher`](/docs/user-guide/skills/bundled/research/research-blogwatcher), [`vietnam-legal-crawler`](/docs/user-guide/skills/bundled/research/research-vietnam-legal-crawler) |

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# Website Mirror Skill

Tải toàn bộ website (`wget --mirror`) về máy và đồng bộ vào thư mục deploy
`assets/website/<name>/`. Chạy một lần để thiết lập; lịch lặp lại chạy qua
`cronjob`. Kết quả là bản mirror offline duyệt được (liên kết đã được
convert-links), phù hợp để lưu trữ hoặc phục vụ tĩnh.

## When to Use

- "Crawl toàn bộ website X về máy."
- "Mirror site Y để xem offline / phục vụ tĩnh."
- "Lập lịch đồng bộ lại website định kỳ."
- Một cron tick bắn cho mirror đã tồn tại (bước 3-4).

Don't use for: crawl có chọn lọc theo nội dung (dùng `web_extract` /
`web_search`), giám sát tin mới (dùng `blogwatcher`), hoặc website cần login /
phía sau JavaScript SPA nặng mà `wget` không lấy được nội dung thực.

## Prerequisites

- `wget` cài trên máy (`apt install wget`, `brew install wget`, hoặc bản
  Windows từ winget/Git Bash).
- Thư mục `assets/website/` nằm trong thư mục làm việc (có thể đổi bằng
  `--root`).
- Tôn trọng `robots.txt` của site đích; chỉ mirror site bạn có quyền.

## How to Run

Chạy crawl thủ công trước khi đặt lịch:

```
terminal(command="python3 skills/research/website-mirror/scripts/mirror_site.py crawl --url https://example.com --name example", timeout=3600)
```

Xem trạng thái mirror:

```
terminal(command="python3 skills/research/website-mirror/scripts/mirror_site.py status --name example")
```

## Quick Reference

```bash
# crawl + deploy vào assets/website/<name>/
python3 skills/research/website-mirror/scripts/mirror_site.py crawl --url <URL> --name <name>

# loại trừ file/đuôi (repeatable)
python3 skills/research/website-mirror/scripts/mirror_site.py crawl --url <URL> --name <name> --exclude '*.pdf' --exclude '*.zip'

# deploy root khác mặc định
python3 skills/research/website-mirror/scripts/mirror_site.py crawl --url <URL> --name <name> --root /path/to/assets/website

# trạng thái lần chạy cuối
python3 skills/research/website-mirror/scripts/mirror_site.py status --name <name>
```

## Procedure — Setup (foreground, once)

### 1. Chốt URL và tên site

Xác định URL gốc (homepage), `name` ngắn gọn dùng làm tên thư mục (vd
`example`), và danh sách `--exclude` cho nội dung không cần (file nặng, trang
admin, PDF). Done when: `name` duy nhất và danh sách exclude không còn nghi
ngờ.

### 2. Crawl thủ công một lần

Chạy `mirror_site.py crawl` với `terminal`. Kiểm tra thư mục
`assets/website/<name>/` có nội dung và `status` trả về `ok: true`, ghi nhận
`file_count`. Nếu `wget` báo lỗi (404 tràn lan, timeout), điều chỉnh
`--exclude` / `--timeout` trước khi tiếp tục. Done when: lần crawl foreground
thành công và thư mục deploy có đủ nội dung.

### 3. Đặt lịch lặp lại

Sau khi crawl thủ công thành công, tạo cronjob (tần suất hợp lý theo quy mô
site và giới hạn rate của site — đừng crawl quá nhanh nếu không cần):

```
cronjob(action="create",
        schedule="every 1d",
        prompt="Load the website-mirror skill and run the tick for the mirror named <name> (URL <URL>) in assets/website/<name>.",
        deliver=<user's destination>)
```

Done when: `hermes cron list` hiển thị job và job trỏ đúng skill + tên mirror.

## Procedure — Tick (each scheduled run)

### 4. Crawl lại và đồng bộ

Chạy lại `mirror_site.py crawl` với cùng `--url`/`--name`/`--exclude` như lần
setup. `wget --timestamping` chỉ tải lại trang đã đổi; script copy file mới
vào `assets/website/<name>/` (giữ nguyên file không đổi). Done when: `status`
có `last_run` mới và `copied` phản ánh thay đổi (có thể là 0).

### 5. Báo kết quả

Báo gọn: tên site, `file_count`, số file `copied` lần này, thời điểm `last_run`,
và đường dẫn deploy. Nếu `copied == 0`, chỉ xác nhận đồng bộ xong — không cần
chi tiết. Done when: người dùng biết mirror đã cập nhật hay không thay đổi.

## Pitfalls

- **Quên crawl thủ công trước khi đặt lịch.** Cron tick không phải nơi để phát
  hiện lỗi URL/exclude; chạy foreground một lần cho chắc.
- **Site nặng / động.** `wget` không render JavaScript. Site SPA lấy nội dung
  qua JS sẽ ra bản mirror rỗng; cân nhắc `web_extract` theo trang hoặc kiểm tra
  lại output.
- **Quét cả site lạ.** Tôn trọng `robots.txt` và chỉ mirror site bạn được phép.
- **`--exclude` đặt sai.** File bị loại sẽ không có trong bản deploy — kiểm tra
  `file_count` so với kỳ vọng.
- **Tần suất quá dày.** Crawl toàn site mỗi giờ dễ bị site chặn IP. Mặc định
  nên từ `every 1d` trở lên trừ khi site nhỏ.

## Verification

- [ ] `mirror_site.py status --name <name>` trả về `ok: true` với `file_count` > 0.
- [ ] Mở `assets/website/<name>/index.html` bằng trình duyệt thấy trang chủ và
      link nội bộ hoạt động (offline).
- [ ] `hermes cron list` hiển thị job mirror và tick chạy xong cập nhật
      `last_run`.
