---
name: automation-backlog
description: 'Khảo sát page RPA, đề xuất backlog, chờ duyệt rồi chạy.'
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
    - Automation
    - RPA
    - Research
    - Backlog
    related_skills:
    - automation-workflow
    - automation-watch
    - automation-data-trigger
    - cron
---
# Automation Backlog Skill

Khảo sát các trang về Automation/RPA để tìm việc lặp lại đáng tự động hoá, viết
đề xuất có cấu trúc, ghi vào backlog bền vững, nhắc chủ nhân phê duyệt, và chỉ
thực thi sau khi được duyệt. Backlog nằm ở một file Markdown duy nhất, nên
không cần hạ tầng mới — chỉ cần `read_file`/`write_file`/`patch` để đọc và cập
nhật trạng thái.

Có hai chế độ:

- **Tương tác** (mặc định): người dùng nhờ khảo sát → nghiên cứu → đề xuất →
  hỏi duyệt ngay trong hội thoại → thực thi nếu được duyệt.
- **Định kỳ** (cron): chạy lướt chỉ để khảo sát + đề xuất + nhắc duyệt, giao kết
  quả qua kênh nhắn tin. Không tự thực thi — chỉ nhắc.

## When to Use

- "Khảo sát các page về automation/RPA và đề xuất việc nên tự động hoá."
- "Có gì mới đáng tự động hoá trong tuần này?"
- "Tôi vừa xem trang X — đưa ý tưởng vào backlog."
- "Chạy định kỳ mỗi sáng: khảo sát + nhắc tôi duyệt backlog."

Don't use for: thực thi một việc tự động đã rõ (dùng `automation-workflow` /
`cronjob`), hay theo dõi thay đổi file/giá trị (dùng `automation-watch` /
`automation-data-trigger`).

## Prerequisites

- Backlog file: `display_hermes_home()/automation-backlog.md` (mặc định
  `~/.hermes/automation-backlog.md`). Tự tạo nếu chưa có. Profile-aware.
- Web tools: `web_search`, `web_extract`, `browser_navigate` (tùy `check_fn`).

## How to Run

1. Mở file backlog: `read_file display_hermes_home()/automation-backlog.md`
   (hoặc tạo mới với header nếu chưa tồn tại).
2. Khảo sát nguồn (xem Procedure).
3. Viết đề xuất + ghi vào backlog.
4. Hỏi duyệt.
5. Nếu duyệt → thực thi → cập nhật trạng thái.

## Quick Reference

Định dạng đề xuất trong backlog (mỗi mục một khối, ID tăng dần):

```markdown
## [RB-007] <Tiêu đề ngắn, một dòng>
- **Trạng thái:** `chờ duyệt`
- **Nguồn:** <url trang đã khảo sát>
- **Task thủ công:** <đang làm gì, thủ công thế nào, tần suất>
- **Tự động hoá:** <cách làm tự động — script, cron, workflow, tool>
- **Công cụ:** <tên tool / cronjob / automation-workflow>
- **Độ khó:** S | M | L
- **Giá trị:** Thấp | TB | Cao
- **Ước lượng:** <giờ hoặc ngày>
```

Vòng đời trạng thái:

```
chờ duyệt → đã duyệt → đang làm → xong
        ↘  từ chối
```

## Procedure

1. **Đọc backlog.** Lấy số ID tiếp theo, đọc mục cũ để tránh đề xuất trùng.
2. **Khảo sát.** Nguồn gợi ý: r/automation, r/RPA, r/selfhosted; blog Make,
   Zapier, n8n; Hacker News; tài liệu RPA (UiPath, n8n, Playwright). Với mỗi
   trang: `web_search` tìm chủ đề, `web_extract` đọc chi tiết, `browser_navigate`
   nếu cần tương tác. Ghi chú **việc thủ công lặp lại** mà trang đề cập — đó là
   nhiệm vụ của skill này, không phải tóm tắt tin tức.
3. **Lọc.** Chỉ đề xuất việc có thể tự động hoá bằng công cụ Hermes hiện có
   (`cronjob`, `automation-workflow`, `terminal`, `delegate_task`, toolsets
   đang bật). Bỏ ý tưởng mơ hồ hoặc cần hạ tầng không tồn tại. Tối đa 3 đề xuất
   mỗi lượt khảo sát — chất lượng hơn số lượng.
4. **Ghi vào backlog.** Dùng `patch` (hoặc `write_file` nếu file mới) để thêm
   mục mới với trạng thái `chờ duyệt`.
5. **Nhắc duyệt.** Trình bày tóm tắt ngắn — mỗi mục 2-3 dòng: ID, tiêu đề, việc
   thủ công, cách tự động hoá, độ khó/giá trị. Hỏi rõ: "Duyệt `RB-007`? Trả lời
   `duyệt <ID>`, `bỏ <ID>`, hoặc `sửa <ID> ...`".
   - Chế độ tương tác: hỏi trong câu trả lời (dùng `clarify` nếu bật và phù
     hợp).
   - Chế độ cron: kết thúc lượt bằng bản nhắc — không chờ câu trả lời trong
     session, không tự thực thi.
6. **Thực thi sau khi duyệt.** Với mục đã duyệt: cập nhật `đã duyệt` → thực
   hiện (tạo `cronjob`, `hermes workflow deploy`, script, ...) → cập nhật
   `đang làm` → khi xong chuyển `xong` kèm ghi chú kết quả. Với `bỏ`: chuyển
   `từ chối` kèm lý do nếu có.

### Chế độ định kỳ

Cài cron chỉ gồm bước khảo sát + đề xuất + nhắc:

```bash
hermes cron add "every 1d" \
  "Chạy skill automation-backlog chế độ cron: khảo sát page RPA, thêm đề xuất vào backlog, nhắc phê duyệt. KHÔNG thực thi gì." \
  --name rpa-scan --skills automation-backlog --deliver telegram
```

Job giao bản nhắc qua kênh; phê duyệt và thực thi vẫn diễn ra trong hội thoại
thường.

## Pitfalls

- **Không tự thực thi khi chưa duyệt.** Trong chế độ cron, tuyệt đối không chạy
  đề xuất mới. Nếu không chắc, giữ trạng thái `chờ duyệt` và nhắc lại.
- **Trùng lặp.** Luôn đối chiếu backlog trước khi thêm; mục trùng thì cập nhật
  "nguồn mới" thay vì tạo bản thứ hai.
- **Không đổi nội dung mục cũ khi thêm mới** — dùng `patch` chèn ở cuối file,
  tránh `write_file` ghi đè toàn bộ làm mất lịch sử.
- **Giữ vai trò hai chiều.** Cả "task thủ công" và "cách tự động hoá" phải rõ
  ràng; mục thiếu một trong hai là đề xuất dở, bỏ.
- **Nguồn phải có URL.** Đề xuất không có nguồn khó đánh giá lại — luôn kèm url.

## Verification

- Mở backlog: mỗi mục có ID duy nhất, trạng thái hợp lệ, có `Nguồn` + `Task
  thủ công` + `Tự động hoá`.
- Sau lượt khảo sát: có ít nhất 1 mục mới ở trạng thái `chờ duyệt` và không có
  trùng ID.
- Sau khi duyệt: trạng thái chuyển qua `đã duyệt` → `xong` (hoặc `từ chối`), và
  việc thực thi đã chạy thật (cron/workflow có lần chạy thành công).
