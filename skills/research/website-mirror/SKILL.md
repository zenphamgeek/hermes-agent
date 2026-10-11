---
name: website-mirror
description: Mirror a full website to assets/website/<name> on schedule.
version: 0.1.0
author: Hermes Agent
license: MIT
platforms:
- linux
- macos
- windows
metadata:
  hermes:
    tags:
    - Mirror
    - Crawler
    - Website
    - Archive
    - Deploy
    - Cron
    related_skills:
    - blogwatcher
    - vietnam-legal-crawler
---
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

# CDN/asset host cho media parity (khi CSS/img nằm trên CDN khác host — repeatable)
python3 skills/research/website-mirror/scripts/mirror_site.py crawl --url <URL> --name <name> --extra-domain cdn.example.com --extra-domain fonts.googleapis.com

# loại bỏ subdomain SaaS/nhiễu — --domains khớp hậu tố nên *.c3.ai bị quét cả subdomain
# (ir., learn., community., support., mcp., developer.); chặn chúng khi gây treo/rate-limit (repeatable)
python3 skills/research/website-mirror/scripts/mirror_site.py crawl --url https://c3.ai --name c3ai --exclude-domain ir.c3.ai --exclude-domain learn.c3.ai --exclude-domain community.c3.ai --exclude-domain support.c3.ai --exclude-domain mcp.c3.ai --exclude-domain developer.c3.ai

# deploy root khác mặc định
python3 skills/research/website-mirror/scripts/mirror_site.py crawl --url <URL> --name <name> --root /path/to/assets/website

# deploy staging hiện có mà không crawl lại (dùng khi lần crawl trước bị timeout)
python3 skills/research/website-mirror/scripts/mirror_site.py deploy --name <name>

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
`--exclude` / `--exclude-domain` / `--timeout` trước khi tiếp tục. Done when:
lần crawl foreground thành công và thư mục deploy có đủ nội dung.

### 3. Đặt lịch lặp lại

Sau khi crawl thủ công thành công, tạo cronjob (tần suất hợp lý theo quy mô
site và giới hạn rate của site — đừng crawl quá nhanh nếu không cần):

```
cronjob(action="create",
        schedule="every 1d",
        prompt="Load the website-mirror skill and run the tick for the mirror named <name> (URL <URL>) in assets/website/<name>.",
        deliver=<user's destination>)
        ```

```
# Example: c3.ai parity mirror with CDN asset hosts (--extra-domain for each)
# and noisy subdomains blocked (--exclude-domain)
cronjob(action="create",
        schedule="every 1d",
        name="c3ai-mirror",
        skill="website-mirror",
        deliver="origin",
        prompt="Load the website-mirror skill and run the tick for the mirror named c3ai (URL https://c3.ai) in assets/website/c3ai. Use extra-domain docs.c3.ai, cdn.jsdelivr.net, fonts.googleapis.com, fonts.gstatic.com. Use exclude-domain ir.c3.ai, learn.c3.ai, community.c3.ai, support.c3.ai, mcp.c3.ai, developer.c3.ai.")
```

Done when: `hermes cron list` hiển thị job và job trỏ đúng skill + tên mirror.

## Procedure — Tick (each scheduled run)

### 4. Crawl lại và đồng bộ

Chạy lại `mirror_site.py crawl` với cùng `--url`/`--name`/`--exclude`/`--extra-domain`/`--exclude-domain` như lần
setup. `wget --timestamping` chỉ tải lại trang đã đổi (staging được giữ lại giữa các lần chạy); script copy file mới
vào `assets/website/<name>/` (giữ nguyên file không đổi).

Site lớn hiếm khi hoàn tất trong một cửa sổ chạy: khi `wget` bị timeout, script vẫn
**deploy phần đã tải** và ghi state `ok: false` kèm `error` — tick sau tiếp tục bằng
`--timestamping` cho tới khi đủ. Nếu staging đã đầy đủ mà chỉ cần deploy lại (vd tick
trước bị timeout trước khi copy), dùng `mirror_site.py deploy --name <name>`. Done when: `status` có `last_run` mới và `copied` phản ánh thay đổi (có thể là 0).

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
- **`--domains` khớp cả subdomain.** `--domains c3.ai` quét cả `*.c3.ai` (ir.,
  learn., community., support., mcp., developer.) — những host SaaS này dễ treo
  crawl. Chặn bằng `--exclude-domain` khi gặp; còn lại việc quét thêm subdomain
  cũng là parity nếu bạn muốn.
- **Timeout giữa chừng là bình thường với site lớn.** Không phải lỗi; chạy lại
  tick sẽ resume incremental. Kiểm tra `status` để xem `ok: false` + `error` là
  do timeout chứ không phải lỗi cấu hình.
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
