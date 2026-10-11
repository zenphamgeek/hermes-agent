---
name: modal-ltxvideo
description: Khởi chạy và điều hành mô hình tạo video điện ảnh LTX 2.5 (22B) trên hạ tầng Modal NVIDIA A100-80GB, hỗ trợ sinh video dài 10-15s chuẩn (F-1)%8==0, 3D VAE Tiling, và API endpoint.
---

# Modal LTX-2.5 Video Generation Skill (A100-80GB)

Kỹ năng điều phối mô hình tạo video điện ảnh mã nguồn mở cao cấp **Lightricks LTX-2.5 (22B Multimodal Foundation)** trên cụm GPU đám mây **NVIDIA A100-80GB** thông qua Modal.com.

## 1. Năng Lực Cốt Lõi

- **Sinh video dài 10s – 15s**: Khác với thế hệ 1 (2B) bị giới hạn ở 4–5 giây, bản LTX 2.5 trên A100-80GB mở rộng ngữ cảnh thời gian lên tới 361 frames (15 giây @ 24fps).
- **VRAM 80GB HBM2e**: Giải phóng hoàn toàn nguy cơ OOM do Self-Attention activations và 3D VAE temporal convolution decoding.
- **Tiling & Slicing VAE Causal**: Bật cơ chế chia nhỏ ma trận VAE latents trong không gian và thời gian để chống tràn RAM khi xuất video $1280 \times 720$ hoặc $1920 \times 1080$.
- **Quy chuẩn Temporal Latent**: Luôn đảm bảo tổng số frame tuân thủ công thức nén của Lightricks:
  $$(F - 1) \pmod 8 == 0$$
  * 10.0s $\to$ 241 frames
  * 12.0s $\to$ 289 frames
  * 15.0s $\to$ 361 frames

---

## 2. Hướng Dẫn Vận Hành & Lệnh Triển Khai

### A. Triển khai (Deploy) lên Workspace Modal
Ứng dụng đã được triển khai chính thức trên workspace **mojopham** (Pro tier với NVIDIA A100-80GB):
- **Dashboard URL**: [modal.com/apps/mojopham/main/deployed/hermes-neural-ltxvideo](https://modal.com/apps/mojopham/main/deployed/hermes-neural-ltxvideo)
- **Live FastAPI Endpoint**: `https://mojopham--hermes-neural-ltxvideo-api-generate.modal.run`

Lệnh tái triển khai hoặc triển khai sang workspace khác:
```bash
# Triển khai vào workspace mojopham (đã xác thực Pro A100-80GB)
MODAL_PROFILE=mojopham modal deploy skills/creative/modal-ltxvideo/modal_app.py

# Hoặc triển khai vào workspace khác khi có Payment Method
MODAL_PROFILE=motion modal deploy skills/creative/modal-ltxvideo/modal_app.py
```

### B. Chạy trực tiếp từ dòng lệnh (Local Entrypoint)
Tạo video 12–15 giây thử nghiệm trực tiếp qua terminal máy trạm:
```bash
MODAL_PROFILE=mojopham modal run skills/creative/modal-ltxvideo/modal_app.py \
  --prompt "A dramatic cinematic tracking shot of an AI robotics research lab, Neo-Noir cyberpunk, 4k photorealistic" \
  --duration 12.0 \
  --output output/ltx_test_12s.mp4
```

### C. Gọi qua Web API Endpoint
Sau khi deploy, endpoint sẵn sàng nhận request POST:
```bash
curl -X POST https://mojopham--hermes-neural-ltxvideo-api-generate.modal.run \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Cinematic aerial view of Ho Chi Minh City skyline at sunset, 8k, photorealistic",
    "duration_sec": 15,
    "width": 1280,
    "height": 720
  }' \
  --output output/saigon_15s.mp4
```

---

## 3. Bảng Tham Chiếu Hiệu Năng & Chi Phí

| Thời Lượng | Frame Count | VRAM Peak | Tốc Độ Sinh (A100-80GB) | Chi Phí Ước Tính / Clip |
|:---:|:---:|:---:|:---:|:---:|
| **5.0s** | 121 frames | ~42 GB | ~20 – 30s | ~$0.02 USD |
| **10.0s** | 241 frames | ~62 GB | ~45 – 55s | ~$0.04 USD |
| **15.0s** | 361 frames | ~74 GB | ~70 – 90s | ~$0.06 USD |

---

## 4. Tài Liệu Toàn Diện Cho Vibe Agent
Xem hướng dẫn chi tiết toàn bộ tham số, cách nạp ảnh tham chiếu (Referral Assets Collection), cấu trúc prompt thời gian, và các giao thức gọi đa GPU song song tại:
👉 [**LTX_API_Call.md**](file:///home/zen/hermes-agent/LTX_API_Call.md)
