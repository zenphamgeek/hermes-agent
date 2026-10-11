---
name: modal-swapface
description: Face swap from source image to target via FaceFusion.
version: 1.0.0
author: hermes-community
license: MIT
platforms:
- linux
- macos
- windows
tags:
- creative
- face-swap
- facefusion
- ai-video
metadata:
  hermes:
    tags:
    - modal swapface
    related_skills: []
---
# FaceFusion SwapFace Skill

Skill này giúp Hermes Agent tự động thực hiện hoán đổi khuôn mặt (Face Swap) chất lượng cao khi người dùng yêu cầu (qua Terminal, Web Dashboard, hoặc Telegram Bot).


## When to Use

Use this skill when:
- The user asks to face swap from source image to target via facefusion.
- Executing automated modal swapface workflows and tasks.

## Khi nào kích hoạt:
- Người dùng yêu cầu ghép mặt, hoán đổi mặt, swap face từ ảnh A vào video/ảnh B.
- Người dùng gửi 2 file/URL (ảnh khuôn mặt + video/ảnh đích) kèm lệnh "ghép mặt", "swap mặt", "chuyển mặt", "face swap".
- Người dùng muốn nâng chất lượng mặt sau swap (enhancer) hoặc nâng cấp video (upscaler).

## Lệnh thực thi:

```bash
python3 ~/.hermes/skills/modal-swapface/runner.py \
  --source "<đường_dẫn_hoặc_URL_ảnh_mặt_nguồn>" \
  --target "<đường_dẫn_hoặc_URL_video_đích>" \
  --face-swapper-model inswapper_128 \
  --face-enhancer-model codeformer \
  --json
```

### Tham số chính:
- `--source` (`-s`): Resolve asset ID/relative path qua `tools.media_asset_catalog.resolve_asset` (category `face`) trước khi gọi runner; URL vẫn truyền trực tiếp.
- `--target` (`-t`): Resolve asset ID/relative path qua catalog chung trước khi gọi runner; URL vẫn truyền trực tiếp.
- Face/video `local_only` không được gửi lên Modal/Remote; cloud cần consent/policy tường minh. Group `female`/`male` chỉ dùng lọc catalog.
- `--output` (`-o`): Đường dẫn lưu file kết quả (mặc định: `/output/swapface/` → `~/workspace/output/swapface/`).
- `--face-swapper-model`: Model hoán đổi mặt. Mặc định: `inswapper_128_fp16`.
- `--face-swapper-pixel-boost`: Độ phân giải tiling oversampling. Mặc định: `128x128`.
- `--face-enhancer-model`: Model nâng chất lượng mặt. Mặc định: `codeformer` (Luôn Bật). Dùng `none` hoặc `--no-face-enhancer` để tắt.
- `--no-face-enhancer`: Tắt chế độ Face Enhancer khi cần tốc độ tối đa cho video dài hoặc độ phân giải thấp.
- `--frame-enhancer-model`: Model nâng chất lượng toàn khung hình (tùy chọn).
- `--face-detector-model`: Model phát hiện mặt. Mặc định: `yolo_face` (nhanh nhất trên GPU).
- `--json`: Xuất kết quả dạng JSON.

### Danh sách Model có sẵn:

#### Face Swappers:
- `inswapper_128` (Mặc định, tốt nhất tổng thể)
- `inswapper_128_fp16` (Nhanh hơn, tiết kiệm VRAM)
- `simswap_256`, `simswap_unofficial_512`
- `uniface_256`
- `ghost_1_256`, `ghost_2_256`, `ghost_3_256`
- `hififace_unofficial_256`
- `hyperswap_1a_256`, `hyperswap_1b_256`, `hyperswap_1c_256`

#### Face Enhancers:
- `codeformer` (Mặc định, tốt nhất phục hồi chi tiết mặt)
- `gfpgan_1.2`, `gfpgan_1.3`, `gfpgan_1.4`
- `gpen_bfr_256`, `gpen_bfr_512`, `gpen_bfr_1024`, `gpen_bfr_2048`
- `restoreformer_plus_plus`

#### Frame Enhancers (Upscale):
- `real_esrgan_x2`, `real_esrgan_x4`, `real_esrgan_x8`
- `real_hatgan_x4`
- `nomos8k_sc_x4`
- `ultra_sharp_x4`, `ultra_sharp_2_x4`
- `remacri_x4`, `siax_x4`
- `span_kendata_x4`, `swin2_sr_x4`

#### Face Detectors:
- `retinaface` (Mặc định, chính xác nhất)
- `scrfd` (Nhanh hơn)
- `yolo_face`, `yunet`

## Đường dẫn đầu ra:
Tất cả kết quả mặc định lưu vào `/output/swapface/` (→ `~/workspace/output/swapface/`), thư mục dùng chung giữa Host và LXC Container qua mount.

## Phản hồi người dùng:
1. Thông báo trạng thái đang xử lý trên GPU CUDA.
2. Khi hoàn tất, trả về đường dẫn file, dung lượng, engine và danh sách model đã dùng.
3. Nếu người dùng đang nhắn tin qua **Telegram**, gửi kèm file video/ảnh thành phẩm vào chat/channel.
