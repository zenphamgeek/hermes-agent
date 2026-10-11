---
name: modal-wan-s2v
description: Autonomous Speech-to-Video (S2V) generation engine using Alibaba Wan2.2-S2V-14B on Modal Serverless (A100-80GB) and ComfyUI. Supports 16:9 Talking Avatar, 9:16 Shorts Funnel, Infinite Chained Speech, and Cinematic Motion templates.
---

# Modal Wan2.2-S2V-14B Engine Skill

Kỹ năng chuyên trách sản xuất video từ giọng nói (Speech-to-Video) cho hệ thống **Hermes Agent** và **ZENPHAM Content Factory** sử dụng nền tảng mô hình **Alibaba Wan2.2-S2V-14B** trên hạ tầng Modal Serverless (NVIDIA A100-80GB) và ComfyUI.

---

## 1. Năng lực & Kiến trúc cốt lõi

- **Mô hình**: Alibaba Wan2.2-S2V-14B (Flow Matching DiT Speech-to-Video).
- **Hạ tầng tính toán**: NVIDIA A100-80GB (80GB HBM2e VRAM) chạy trên Modal Serverless (`mojopham`, `zenonmind`, `mvlm`).
- **Nguồn âm thanh chuẩn**: 100% đồng bộ với giọng đọc chuẩn phòng thu **TTS V0-Sense** (48kHz Stereo, EBU R128 $-14.5 \pm 0.5$ LUFS, True Peak $\le -1.5$ dBTP, Clause Guard $\le 75$ ký tự).
- **Xuất video chuẩn rạp**: Tự động muxing âm thanh gốc và upscale Full HD 1080p bằng bộ lọc chất lượng cao Lanczos (`scale=1920:1080` hoặc `scale=1080:1920`).

---

## 2. Danh mục 4 Template Production Đã Tích Hợp

Các workflow JSON được lưu trữ và tối ưu hóa tại `skills/creative/comfyui/workflows/`:

1. **`talking_avatar` (`wan22_s2v_talking_avatar_production.json`)**:
   - Tỷ lệ: 16:9 (1024x704 base $\to$ 1080p Lanczos).
   - Mục đích: Người dẫn chuyện Masterclass, giải thích hệ thống (Reality Decode, Tôi Làm Việc).
   - Cấu hình: 35 steps, CFG 5.0, Flow Shift 3.0, Sampler `uni_pc`.

2. **`shorts_vertical` (`wan22_s2v_shorts_vertical_production.json`)**:
   - Tỷ lệ: 9:16 (704x1024 base $\to$ 1080x1920 Full HD).
   - Mục đích: YouTube Shorts Funnel 50.00s, TikTok, Reels.
   - Vùng an toàn: Mắt chủ thể nằm ở độ cao 40% ($Y \approx +1.5$), tránh che bởi UI YouTube.

3. **`infinite_speech` (`wan22_s2v_infinite_speech_production.json`)**:
   - Tỷ lệ: 16:9 Chained Multi-Chunk.
   - Mục đích: Nối các vế câu dài liên tục không bị giật khung hình hoặc đổi nhân vật nhờ `WanSoundImageToVideoExtend`.
   - Chuẩn khớp: Đi kèm với Clause Guard $\le 75$ ký tự của TTS V0-Sense.

4. **`cinematic_motion` (`wan22_s2v_cinematic_motion_production.json`)**:
   - Tỷ lệ: 16:9 Dramatic Masterclass.
   - Mục đích: Đoạn mở đầu cao trào, camera push-in dolly zoom, ánh sáng Neo-Noir tương phản cao.
   - Cấu hình: 40 steps, CFG 5.5, Flow Shift 3.5.

---

## 3. Cách vận hành & Dispatch cho Vibe Agent

### Cách 1: Gọi qua FastAPI REST Endpoint
```python
import base64, requests

with open("speech.wav", "rb") as f:
    audio_b64 = "data:audio/wav;base64," + base64.b64encode(f.read()).decode()
with open("avatar.png", "rb") as f:
    img_b64 = "data:image/png;base64," + base64.b64encode(f.read()).decode()

payload = {
    "image": img_b64,
    "audio": audio_b64,
    "template": "shorts_vertical",  # 'talking_avatar', 'infinite_speech', 'cinematic_motion'
    "prompt": "A charismatic Vietnamese tech host explaining AI scaling laws",
    "upscale_1080p": True
}

res = requests.post("https://zenonmind--hermes-wan-s2v-api.modal.run/generate", json=payload, timeout=600)
with open("output/shorts_s2v.mp4", "wb") as f:
    f.write(res.content)
```

### Cách 2: Gọi qua Template Dispatcher (ComfyUI Engine)
```bash
# Kiểm tra danh mục template hiện có
python3 skills/creative/modal-comfyui/dispatch_template.py --list-templates

# Chạy template Shorts 9:16 trên Modal ComfyUI Engine
python3 skills/creative/modal-comfyui/dispatch_template.py \
    --host https://mojopham--hermes-comfyui-engine-comfyuirunner-web-ui.modal.run \
    --template wan22_s2v_shorts_vertical \
    --image assets/avatar.png \
    --audio assets/audio.wav \
    --output output/s2v_output.mp4
```

---

## 4. Tài liệu chi tiết & Quy chuẩn kiểm toán

Xem toàn văn hướng dẫn kỹ thuật, công thức câu lệnh prompt, và bảng thông số tại:
👉 [**WAN 2.2 S2V PRODUCTION SERVICE GUIDE**](file:///home/zen/hermes-agent/skills/creative/modal-wan-s2v/SERVICE_GUIDE.md)
