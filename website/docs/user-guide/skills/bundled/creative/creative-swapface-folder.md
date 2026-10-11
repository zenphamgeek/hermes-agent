---
title: "Swapface Folder — Batch face swap into all videos in target directory"
sidebar_label: "Swapface Folder"
description: "Batch face swap into all videos in target directory"
---

{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */}

# Swapface Folder

Batch face swap into all videos in target directory.

## Skill metadata

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/creative/swapface-folder` |
| Version | `1.0.0` |
| Author | hermes-community |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `face-swap`, `batch`, `video`, `media`, `facefusion` |
| Related skills | [`video-face-segmenter`](/docs/user-guide/skills/bundled/media/media-video-face-segmenter), [`modal-swapface`](/docs/user-guide/skills/bundled/creative/creative-modal-swapface) |

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# SwapFace to Target Folder Skill

Skill này giúp Hermes Agent tự động thực hiện **hoán đổi khuôn mặt hàng loạt (Batch Face Swap)** từ một ảnh khuôn mặt nguồn vào **toàn bộ các video/ảnh trong một thư mục đích** (đặc biệt là các thư mục segments do `video-face-segmenter` xuất ra).

## When to Use

Sử dụng skill này khi:
- Người dùng yêu cầu ghép mặt / swap face vào toàn bộ video trong một folder hoặc thư mục segment (ví dụ: *"Ghép mặt ảnh Truc.jpg vào tất cả các đoạn _OK trong thư mục segments"*).
- Người dùng cung cấp 1 ảnh khuôn mặt + 1 đường dẫn thư mục đích (target folder).
- Người dùng muốn batch swap tự động nhiều video cùng lúc mà không phải gọi từng lệnh đơn lẻ.

Do NOT use for single image swap where `image_generation` or modal tool is requested.

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
- `--source` (`-s`): Resolve asset ID/relative path qua `tools.media_asset_catalog.resolve_asset` (category `face`) trước khi gọi runner; URL vẫn truyền trực tiếp.
- `--target-folder` / `--target-dir` (`-t`): Đường dẫn thư mục chứa các video/ảnh đích; media catalog được scan đệ quy.
- Face/video `local_only` không được gửi lên Modal/Remote; cloud cần consent/policy tường minh. Group `female`/`male` chỉ dùng lọc catalog.
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
<!-- ascii-guard-ignore -->
```
/output/swapface_batches/<tên_thư_mục_gốc>_<timestamp>/
├── swapped_segment_0002_00-00-17_00-00-22_female_OK.mp4
├── swapped_segment_0005_00-01-06_00-01-15_female_OK.mp4
├── swapped_segment_0007_00-01-26_00-01-34_female_OK.mp4
└── batch_summary.json
```
<!-- ascii-guard-ignore-end -->
