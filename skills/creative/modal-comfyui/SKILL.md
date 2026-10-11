---
name: modal-comfyui
description: Khởi chạy và điều hành ComfyUI Serverless trên Modal GPU (A100-80GB / T4), hỗ trợ thực thi trực tiếp các template JSON cho Wan 2.2 S2V, LTX 2.5 và Qwen Image 2.1.
---

# Modal ComfyUI Serverless Engine & Template JSON Workflows

Hạ tầng điều phối **ComfyUI Serverless** trên GPU đám mây Modal kết hợp trạm làm việc cục bộ ThinkPad P15, cho phép Vibe Agent nạp trực tiếp các **Template JSON Workflows** để đạt chất lượng tạo hình ảnh và video điện ảnh tối ưu nhất.

---

## 1. Ba Template JSON Chuẩn Hóa Sẵn Có

Toàn bộ các template đã được chuyển đổi sang định dạng **ComfyUI API Format** tại thư mục [`skills/creative/comfyui/workflows/`](file:///home/zen/hermes-agent/skills/creative/comfyui/workflows/):

| Mô Hình | File Template JSON | Năng Lực & Nodes Cốt Lõi | Phần Cứng Khuyến Nghị |
| :--- | :--- | :--- | :---: |
| **Wan 2.2 S2V (14B)** | [`wan22_s2v_14b_api.json`](file:///home/zen/hermes-agent/skills/creative/comfyui/workflows/wan22_s2v_14b_api.json) | Điều khiển khẩu hình từ file âm thanh TTS V0-Sense 48kHz qua `WanSoundImageToVideo` + `AudioEncoderEncode` | **NVIDIA A100-80GB** |
| **LTX-Video 2.5 (22B)**| [`ltx_video_25_api.json`](file:///home/zen/hermes-agent/skills/creative/comfyui/workflows/ltx_video_25_api.json) | Tạo video điện ảnh 10–15s qua `ModelSamplingLTXV` + `LTXVScheduler` + `VAEDecodeTiled` chống OOM | **NVIDIA A100-80GB** |
| **Qwen-Image 2.1 (7B)**| [`qwen_image_21_api.json`](file:///home/zen/hermes-agent/skills/creative/comfyui/workflows/qwen_image_21_api.json) | Tạo và chỉnh sửa ảnh Single-Stream DiT qua `EmptyQwenImageLayeredLatentImage` + `TextEncodeQwenImageEdit` | **NVIDIA T4 / A10G** |

---

## 2. Triển Khai ComfyUI Serverless Lên Modal

### Lệnh Triển Khai (Deploy)
```bash
# Triển khai lên workspace có A100-80GB (ví dụ: mojopham, zenonmind, motion)
MODAL_PROFILE=mojopham modal deploy skills/creative/modal-comfyui/modal_app.py
```

### Các Endpoint Được Khởi Tạo Tự Động:
1. **ComfyUI Web GUI & REST/WS**: `https://<workspace>--hermes-comfyui-engine-comfyuirunner-web-ui.modal.run`
   - Mở trực tiếp trên trình duyệt để kéo thả node hoặc import template JSON.
   - Nhận request chuẩn ComfyUI: `POST /prompt`, `GET /history`, `GET /view`, WebSocket `/ws`.
2. **Template Execution Endpoint**: `POST https://<workspace>--hermes-comfyui-engine-comfyuirunner-run-template.modal.run`
   - Nhận payload JSON đơn giản, tự động inject vào template và chạy trên GPU.

---

## 3. Cách Vibe Agent Thực Thi Template JSON

### Cách 1: Sử dụng Dispatcher Script (Khuyến nghị cho Agent)
Agent có thể thực thi nhanh chóng thông qua lệnh CLI:
```bash
# 1. Chạy Wan 2.2 S2V với âm thanh và ảnh chân dung
python3 skills/creative/modal-comfyui/dispatch_template.py \
    --template wan22_s2v_14b \
    --prompt "A wise teacher explaining complex mathematics with expressive eye contact" \
    --audio assets/audio/speech.wav \
    --image assets/portraits/avatar.png \
    --output output/wan_s2v_result.mp4

# 2. Chạy LTX 2.5 sinh video 10-15s trên Modal
python3 skills/creative/modal-comfyui/dispatch_template.py \
    --host https://mojopham--hermes-comfyui-engine-comfyuirunner-web-ui.modal.run \
    --template ltx_video_25 \
    --prompt "An ultra-detailed cinematic drone shot over misty rice terraces at dawn, 8k photorealistic" \
    --width 1280 --height 720 \
    --output output/ltx_cinema.mp4

# 3. Chạy Qwen-Image 2.1 tạo ảnh chân dung 1024x1024
python3 skills/creative/modal-comfyui/dispatch_template.py \
    --template qwen_image_21 \
    --prompt "Editorial portrait of a Vietnamese cyber-engineer, Neo-noir obsidian and cyan lighting" \
    --output output/qwen_portrait.png
```

### Cách 2: Gọi Trực Tiếp Qua REST API (`POST /prompt`)
```bash
curl -X POST http://127.0.0.1:8188/prompt \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "vibe_agent_01",
    "prompt": '"$(cat skills/creative/comfyui/workflows/wan22_s2v_14b_api.json)"'
  }'
```

---

## 4. Kiểm Soát Tài Nguyên & Scale-To-Zero
- Worker tự động giải phóng tài nguyên GPU (scale-to-zero) sau **300 giây (5 phút)** nhàn rỗi để tránh phát sinh chi phí.
- Checkpoints được mount vào **Modal Volume (`hermes-comfyui-cache`)** để không phải tải lại các file weights 14B/22B giữa các lần khởi động container.
