---
name: swapface-folder
description: Hoán đổi khuôn mặt (Face Swap) hàng loạt từ ảnh Face nguồn vào toàn bộ video/ảnh trong một thư mục đích (Target Folder hoặc thư mục Segments) sử dụng GPU FaceFusion (LXC Container hoặc Modal Cloud). Tự động lọc các đoạn _OK, tối ưu VRAM và xuất báo cáo batch_summary.json.
---

# SwapFace to Target Folder Skill

Skill này giúp Hermes Agent tự động thực hiện **hoán đổi khuôn mặt hàng loạt (Batch Face Swap)** từ một ảnh khuôn mặt nguồn vào **toàn bộ các video/ảnh trong một thư mục đích** (đặc biệt là các thư mục segments do `video-face-segmenter` xuất ra).

## Khi nào kích hoạt:
- Người dùng yêu cầu ghép mặt / swap face vào toàn bộ video trong một folder hoặc thư mục segment (ví dụ: *"Ghép mặt ảnh Truc.jpg vào tất cả các đoạn _OK trong thư mục segments của Jody"*).
- Người dùng cung cấp 1 ảnh khuôn mặt + 1 đường dẫn thư mục đích (target folder).
- Người dùng muốn batch swap tự động nhiều video cùng lúc mà không phải gọi từng lệnh đơn lẻ.

## Lệnh thực thi:

```bash
python3 ~/.hermes/skills/swapface-folder/runner.py \
  --source "<đường_dẫn_hoặc_URL_ảnh_mặt_nguồn>" \
  --target-folder "<đường_dẫn_thư_mục_chứa_video_đích>" \
  --filter "ok_only" \
  --face-swapper-model inswapper_128 \
  --face-enhancer-model codeformer \
  --json
```

### Các tham số chính:
- `--source` (`-s`): Đường dẫn file ảnh hoặc URL ảnh khuôn mặt nguồn (JPG/PNG).
- `--target-folder` / `--target-dir` (`-t`): Đường dẫn thư mục chứa các video/ảnh đích.
- `--filter` (`-f`): Chế độ lọc các file trong thư mục:
  - `ok_only` (Mặc định): Chỉ ghép vào các file có hậu tố `_OK.mp4` / `_OK.*` (thích hợp nhất khi dùng sau bước `video-face-segmenter`). Nếu thư mục không có file `_OK`, tự động xử lý tất cả media files.
  - `all`: Ghép vào toàn bộ file media (.mp4, .mov, .mkv, .jpg, .png, ...) có trong thư mục.
  - `not_only`: Chỉ ghép vào các file có hậu tố `_NOT.mp4`.
- `--output-dir` (`-o`): Thư mục lưu kết quả (mặc định: `/output/swapface_batches/<tên_folder>_<timestamp>/`).
- `--face-swapper-model`: Model swap mặt (`inswapper_128`, `simswap_256`, `uniface_256`, `ghost_2_256`). Mặc định: `inswapper_128`.
- `--face-enhancer-model`: Model làm nét / phục hồi mặt (`codeformer`, `gfpgan_1.4`, `gpen_bfr_512`).
- `--frame-enhancer-model`: Model upscale toàn khung hình (`real_esrgan_x4`, `nomos8k_sc_x4`).
- `--face-detector-model`: Model nhận diện mặt (`retinaface`, `scrfd`). Mặc định: `retinaface`.
- `--json`: Xuất kết quả chi tiết dạng JSON.

## Tối ưu hóa GPU & Quản lý tiến trình:
- **Tự động giải phóng VRAM**: Trước khi bắt đầu batch, runner tự động dừng tạm thời FaceFusion Gradio service để giải phóng 100% VRAM (16GB) cho headless batch execution, tránh xung đột CUDA.
- **Tự động khôi phục**: Sau khi hoàn thành toàn bộ batch (hoặc kể cả khi gặp lỗi), service Gradio Web UI sẽ được tự động bật lại.

## Kết quả xuất ra:
Tất cả các video sau khi swap được lưu trong thư mục:
```
/output/swapface_batches/<tên_thư_mục_gốc>_<timestamp>/
├── swapped_segment_0002_00-00-17_00-00-22_female_OK.mp4
├── swapped_segment_0005_00-01-06_00-01-15_female_OK.mp4
├── swapped_segment_0007_00-01-26_00-01-34_female_OK.mp4
└── batch_summary.json
```

## Phản hồi người dùng:
1. Báo cáo tổng số file tìm thấy và số file thỏa mãn bộ lọc (`_OK`).
2. Tiến độ xử lý từng file và thời gian thực thi.
3. Khi hoàn tất, trả về danh sách các file kết quả và đường dẫn file báo cáo tổng hợp `batch_summary.json`.
