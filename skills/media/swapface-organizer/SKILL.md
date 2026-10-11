---
name: swapface-organizer
description: Scan, reorganize, and deduplicate Swapface assets, Movies Footage (/Ai, /eporner, /erome, etc.), and Vault Images on Google Drive.
version: 1.1.0
author: hermes-community
license: MIT
platforms:
- linux
- macos
- windows
metadata:
  hermes:
    tags:
    - swapface
    - gdrive
    - rclone
    - media-organizer
    - footage
    - vault
    - deduplication
    related_skills:
    - swapface-folder
    - modal-swapface
---

# SwapFace & Media Google Drive Organizer Skill

Skill này giúp Hermes Agent tự động **quét, phân loại, dọn dẹp file trùng lặp/file rác, và tái cấu trúc toàn diện kho Media trên Google Drive** (`phamvuthang@gmail.com:Content Factory` và `phamvuthang@gmail.com:Vault`):

1. **Cấu trúc Review SwapFace Chuẩn Hóa:**
   - Gom video và ảnh theo cấu trúc `<Face_Name>/{img, vid}` tại `06_Exports/Review/swapface/`.
2. **Phân Loại Toàn Bộ Movies / Footage:**
   - Quét video `.mp4`, `.mov`, `.mkv` từ Vault / base_media.
   - Các video mang tiền tố Face (`000 Truc_...`, `020 SM_...`, `025 KhanhChi_...`) được chuyển về `06_Exports/Review/swapface/<Face_Name>/vid/`.
   - Các video raw còn lại được tự động phân loại vào `05_Footage/Raw/{source}/`:
     - `/Ai`: Video sinh từ AI (`wan`, `touching hair`, `comfyui`, `generated`).
     - `/eporner`: Video từ Eporner hoặc mã ID hash `_720p/_480p`.
     - `/erome`: Video tải từ EroMe.
     - `/onlyfans`: Video nguồn OnlyFans.
     - `/web`: Video tải từ nguồn web tổng hợp (`hqporn`, `weliketosuck`, `cammer`, `rphang`).
     - `/general`: Các video clip raw còn lại.
3. **Đồng Bộ & Gom Ảnh Từ `/Vault`:**
   - Đồng bộ ảnh chân dung nguồn `Vault/0 Face/*` vào thư viện tổng `02_Media/Images/Faces/female/` và `<Face_Name>/img/`.
   - Gom toàn bộ ảnh swapface theo từng khuôn mặt `Vault/Photo-sf-img-no-log/<Face_Name>/*` vào `06_Exports/Review/swapface/<Face_Name>/img/`.

---

## Cú Pháp Lệnh Thực Thi (Runner CLI)

### 1. Quét & Kiểm Tra An Toàn (Dry-Run):
```bash
# Kiểm tra phân loại toàn bộ Footage và Kho ảnh Vault
python3 skills/media/swapface-organizer/runner.py --organize-footage --organize-vault-images --dry-run

# Hoặc quét toàn bộ (Swapface + Footage + Vault Images)
python3 skills/media/swapface-organizer/runner.py --all --dry-run
```

### 2. Thực Thi Phân Loại Footage & Đồng Bộ Ảnh Vault (Server-Side Cloud):
```bash
python3 skills/media/swapface-organizer/runner.py --organize-footage --organize-vault-images --execute --workers 8
```

### 3. Tái Cấu Trúc Thư Mục Review SwapFace & Dọn File Rác:
```bash
python3 skills/media/swapface-organizer/runner.py --organize-swapface --clean-stale --execute
```

---

## Cơ Chế Tối Ưu Hóa & An Toàn:
- **Server-Side Operations:** Toàn bộ lệnh `moveto`, `copyto`, `purge` đều chạy trực tiếp trên cloud qua Google Drive API, không tốn băng thông máy trạm.
- **Đa luồng song song (Multi-threading):** Mặc định 8 worker (`--workers 8`) tăng tốc độ xử lý hàng trăm tệp gấp 8 lần.
- **Bảo toàn chất lượng:** Các video swapface đã qua Face Enhancer (GFPGAN 1.4) luôn được bảo toàn và chuyển về đúng thư mục face tương ứng.
