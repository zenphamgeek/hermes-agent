# Giao thức đợt nghiên cứu song song

Áp dụng khi người dùng đã yêu cầu nhiều agent làm song song. Dùng chung filesystem nhưng chia phạm vi ghi; không để nhiều browser worker điều khiển cùng tab.

## Phân công và khóa đợt

Coordinator là người duy nhất ghi `catalog.json`, `catalog.csv`, `coverage.json`, `REPORT.md`, backlog tổng và hồ sơ chính thức. Worker ghi dưới `work/batch-NNN/<worker-id>/`; không sửa `research.py` hoặc các file tổng. Coordinator lập manifest đợt tối đa 10 Reel, gồm ID/URL, hash SHA-256 hồ sơ gốc, worker được giao và thư mục output. Mỗi ID xuất hiện trong đúng một đợt đang hoạt động.

Khóa bằng thao tác `mkdir` nguyên tử trên filesystem chung, không dùng kiểm tra “exists rồi ghi”:

```bash
mkdir -p assets/research/mathoholic_ch/work/claims
mkdir assets/research/mathoholic_ch/work/claims/batch-001
```

Coordinator chạy trước khi dispatch worker. Nếu `mkdir` thứ hai thất bại vì tồn tại, không nhận/giao đợt đó. Sau khi tạo thành công, ghi `owner.json` trong thư mục claim: `batch`, `worker_id`, `assigned_at_utc`, `reel_ids`, `output_dir`, `state=assigned`. Đây là lock giữ tới khi bàn giao, không tự hết hạn theo đồng hồ.

Claim thiếu `owner.json` cũng được coi là đã khóa. Khi agent chết, coordinator kiểm tra trạng thái task và file đang ghi, xác nhận worker đã dừng rồi mới thu hồi. Không xóa claim chỉ vì lâu không cập nhật. Nếu không xác minh được worker đã dừng, giữ khóa và giao việc độc lập khác.

Worker bắt đầu bằng đối chiếu owner/ID; có sai khác thì báo coordinator, không ghi. Coordinator không chỉnh output khi worker đang chạy. Mỗi worker có tab riêng do coordinator xác định; nếu tool dùng một browser session chung không hỗ trợ điều khiển đồng thời an toàn, coordinator độc quyền browser và cung cấp gói evidence. Worker còn lại làm fact-check, thiết kế hoặc audit engine từ evidence; không coi gói frame là video đầy đủ.

## Đầu ra worker

Trong thư mục được giao:

- `manifest.json`: phạm vi, worker, hashes hồ sơ gốc, trạng thái và thời gian checkpoint.
- `reels/<id>.json`: bản sao hồ sơ gốc được bổ sung, giữ nguyên ID/URL.
- `evidence/`: nguồn, timecode và giới hạn truy cập, không credentials.
- `HANDOFF.md`: đã làm/chưa làm, lỗi, bước tiếp theo, URL mới phát hiện và component đề xuất.

Checkpoint sau mỗi Reel hoặc trước khi đổi nhiệm vụ. Không bật trạng thái hoàn tất cho cả đợt từ việc có đủ 10 file. Thông báo coordinator khi kết quả sẵn sàng và dừng ghi trước khi merge.

## Tích hợp duy nhất bởi coordinator

1. Xác nhận worker đã dừng ghi và đúng chủ claim. So sánh hash hồ sơ chính thức hiện tại với manifest; nếu khác, reconcile theo từng evidence thay vì ghi đè.
2. Kiểm tra ID, URL, timecode, provenance transcript, claim checks và mọi trạng thái bật true. Giữ false với lý do khi bằng chứng thiếu. Gộp URL mới vào catalog bằng `research.py add` sau khử trùng.
3. Copy hồ sơ được chấp nhận và evidence vào ledger; cập nhật đường dẫn evidence nếu thư mục thay đổi. Chạy `research.py validate`; chỉ sau khi nhất quán mới chạy `research.py report`. Không gọi PASS này là review chất lượng.
4. Ghi trạng thái accepted hoặc needs_revision trong handoff. Giữ claim khi cần worker sửa tiếp. Khi accepted và worker đã dừng, lưu owner vào lịch sử đợt rồi xóa `owner.json`, dùng `rmdir` thư mục claim rỗng. Không xóa output để giải phóng lock.

Không sử dụng `git reset`, dọn working tree hoặc sửa file của worker khác để giải quyết xung đột. Nếu ledger đã có giao thức khóa khác, coordinator dùng một giao thức thống nhất cho cả đợt; không trộn hai cơ chế quản lý quyền ghi.
