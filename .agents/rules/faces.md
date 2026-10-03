# Quy Chuẩn Quản Lý Tài Nguyên Khuôn Mặt (Faces Rules & SwapFace Discipline)

> **Mã quy tắc:** `@rules:faces`  
> **Áp dụng cho:** Tất cả các tác vụ và pipeline hoán đổi khuôn mặt (SwapFace), bao gồm `modal-swapface`, `swapface-folder`, `video-face-segmenter`, và Content Factory pipeline.

---

## 1. Cấu Trúc Lưu Trữ Khuôn Mặt Chuẩn Hóa

Toàn bộ tài nguyên khuôn mặt nguồn (Reference Face Assets) dùng cho hoán đổi khuôn mặt (FaceSwap) bắt buộc phải nằm trong đúng thư mục phân loại:

### 1.1 Thư mục Cục bộ (Local Assets)
* **Khuôn mặt nữ (Female Faces):**
  `assets/faces/female/`
  *(Ví dụ: `000 Truc.jpg`, `001 Tam.jpeg`, `002 Ly.jpeg`, `020 SM.jpeg`,...)*
* **Khuôn mặt nam (Male Faces):**
  `assets/faces/male/`

### 1.2 Thư mục Điện toán Đám mây (Google Drive Remote)
Đồng bộ tương ứng qua rclone remote `phamvuthang@gmail.com:Content Factory`:
* `02_Media/Images/Faces/female/`
* `02_Media/Images/Faces/male/`

---

## 2. Quy Tắc Tự Động Định Danh (Automatic Face Resolution)

Khi người dùng hoặc agent gọi lệnh SwapFace với tham số `--source`, hệ thống hỗ trợ cơ chế phân giải tên thông minh (Fuzzy & Stem Resolution):
1. **Tên ngắn gọn / Stem Name:**
   - Chỉ cần truyền `--source "Truc"` $\rightarrow$ Tự động khớp và nạp `assets/faces/female/000 Truc.jpg`.
   - Truyền `--source "020 SM"` $\rightarrow$ Tự động khớp và nạp `assets/faces/female/020 SM.jpeg`.
2. **Thứ tự ưu tiên tìm nạp:**
   - 1. Đường dẫn tệp trực tiếp / tuyệt đối (`expanduser()`).
   - 2. Đường dẫn tương đối từ gốc repository (`REPO_ROOT`).
   - 3. Tra cứu nhanh trong `assets/faces/female/`, `assets/faces/male/`, `assets/faces/`.
   - 4. Tra cứu trên Google Drive Cloud FUSE mount (`02_Media/Images/Faces/female`, v.v.).
   - 5. Fallback qua `media_asset_catalog.py`.

---

## 3. Quy Chuẩn Xử Lý SwapFace (Execution Discipline)

1. **Chế độ Face Enhancer:**
   - Mặc định **LUÔN BẬT** `--face-enhancer-model codeformer` để phục hồi chi tiết mắt, miệng, răng và cấu trúc da sắc nét chuẩn điện ảnh.
   - Khi xử lý video dài (> 3 phút) hoặc cần tốc độ cao, có thể tắt bằng cờ `--no-face-enhancer` hoặc `--face-enhancer-model none`.
2. **Tối ưu hóa GPU & Hardware:**
   - Model SwapFace: `inswapper_128_fp16` (nhanh, tiết kiệm VRAM).
   - Pixel Boost: `--face-swapper-pixel-boost 128x128` (tránh nghẽn over-sampling tiling).
   - Face Detector: `yolo_face` (YOLO Face 8n trên CUDA, tốc độ ~2-3ms).
   - Temp Frame Format: `bmp` (Zero-overhead NVMe I/O).
   - Video Encoder: `libx264` preset `fast`.
3. **Đồng bộ hóa Cloud:**
   - Sau khi hoàn thành xuất video vào `/home/zen/workspace/output/swapface/`, chạy:
     ```bash
     python3 assets/scripts_video/filestore_sync_cli.py push-swapface --confirm
     ```
