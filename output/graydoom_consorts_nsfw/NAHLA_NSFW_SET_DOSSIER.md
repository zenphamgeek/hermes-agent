# Dossier & Thiết Kế Set NSFW: Tần Phi Hoàng Gia Nahla (Sunward Court)

> **Dự án**: Gray Doom Game Art Production  
> **Nhân vật được chọn**: **Nahla (Tần phi Ba Tư / Persian Royal Diplomat)**  
> **Ảnh nguồn phê duyệt**: [`art/candidates/consorts/nahla-identity-v5.png`](file:///home/zen/Downloads/Graydoom-art-atlas/art/candidates/consorts/nahla-identity-v5.png)  
> **Hợp đồng nhân dạng**: [`nahla-approved-v7.json`](file:///home/zen/Downloads/Graydoom-art-atlas/art/production/identity-contracts/consorts/nahla-approved-v7.json)  
> **Mô hình kiến trúc**: **FLUX.1 Fill [dev] (FP8 DiT) + NSFW Anatomy LoRA**

---

## 1. Hồ Sơ Nhân Vật & Ràng Buộc Nhân Dạng Gốc (Identity Contract)

Trong 5 Tần phi của Minh Ước Hướng Dương (**Nahla, Evelyn, Lucía, Mei, Vera**), **Nahla** là nhân vật được cộng đồng và Owner đánh giá cao nhất về độ quý phái và thần thái:
- **Nguồn gốc / Vai trò**: Công chúa con nuôi Vua Nadir, nhà ngoại giao hoàng gia Ba Tư. Đảm nhiệm các hiệp ước giới hạn và bảo lãnh ngoại giao.
- **Ràng buộc thị giác (Visual Locks)**:
  - Gương mặt trẻ trung, làn da màu ô-liu ấm áp (*youthful warm-olive skin*).
  - Mái tóc đen tuyền thẳng dài buông xõa (*long straight raven hair*).
  - Đôi mắt đen sâu thẳm mang nét kiêu sa huyền bí.
  - Hoa tai giọt nước ngọc lam viền vàng hình học (*turquoise-gold geometric drop earrings*).
  - Trang phục gốc: Lụa hoàng gia màu ngọc lam / ngà (*sculpted teal/ivory silk*), cấm tuyệt đối giáp sắt và vũ khí.

---

## 2. Thiết Kế Bộ 4 Phân Cảnh NSFW Set (Cinematic NSFW Progression)

Bộ set được biên soạn theo chuỗi cảm xúc và mức độ quyến rũ tăng dần, bảo toàn 100% DNA khuôn mặt bằng kỹ thuật Inpainting/Edit của FLUX.1 Fill:

### 🎬 Scene 01: Royal Boudoir Silk & Lace (Tease / Nửa Kín Nửa Hở)
- **File Workflow**: [`scene_01_boudoir_lace.json`](file:///home/zen/hermes-agent/output/graydoom_consorts_nsfw/scene_01_boudoir_lace.json)
- **Ý đồ nghệ thuật**: Khởi đầu trong tẩm cung lúc hoàng hôn. Áo choàng lụa ngọc lam quen thuộc buông trễ hẳn khỏi bờ vai trần mảnh dẻ, để lộ nội y ren đen xuyên thấu (*sheer black lace*), tôn lên đường cong vòng 1 và thắt eo thon gọn dưới ánh nến lung linh.
- **Denoise**: `0.88` | **Guidance**: `3.5` | **Steps**: `25`

### 🎬 Scene 02: Imperial Sunward Bath (Wet Onsen / Bể Tắm Hoàng Gia)
- **File Workflow**: [`scene_02_imperial_bath.json`](file:///home/zen/hermes-agent/output/graydoom_consorts_nsfw/scene_02_imperial_bath.json)
- **Ý đồ nghệ thuật**: Nahla ngâm mình trong bể tắm đá cẩm thạch rải đầy cánh sen trắng. Mái tóc đen ướt đẫm bết nhẹ sau lưng và cổ, làn da bóng mướt giọt nước đọng trên xương quai xanh và khuôn ngực trần. Làn khói nước mờ ảo tôn lên nét gợi cảm tinh tế.
- **Denoise**: `0.90` | **Guidance**: `3.5` | **Steps**: `25`

### 🎬 Scene 03: The Unveiled Consort (Reclining Nude / Khỏa Thân Cổ Điển)
- **File Workflow**: [`scene_03_unveiled_reclining.json`](file:///home/zen/hermes-agent/output/graydoom_consorts_nsfw/scene_03_unveiled_reclining.json)
- **Ý đồ nghệ thuật**: Tư thế nàng Vệ Nữ nằm nghiêng trên đệm gấm tơ tằm màu ngà. Toàn bộ trang phục được trút bỏ hoàn toàn, chỉ giữ lại đôi khuyên tai ngọc lam lấp lánh đặc trưng. Ánh sáng vàng chiều xiên (chiaroscuro) khắc họa giải phẫu cơ thể mềm mại, chân thực.
- **Denoise**: `0.92` | **Guidance**: `3.5` | **Steps**: `26`

### 🎬 Scene 04: Morning Desert Sunrise (Sensual Awakening / Ban Công Sớm)
- **File Workflow**: [`scene_04_morning_balcony.json`](file:///home/zen/hermes-agent/output/graydoom_consorts_nsfw/scene_04_morning_balcony.json)
- **Ý đồ nghệ thuật**: Đứng tựa ban công đá ngắm bình minh sa mạc Sunward. Chỉ quấn hờ một dải ga giường tơ tằm che hờ phần trước, khoe trọn lưng trần thon thả và đường cong hông từ góc nhìn trắc diện (silhouette).
- **Denoise**: `0.86` | **Guidance**: `3.5` | **Steps**: `24`

---

## 3. Hướng Dẫn Kích Hoạt & Chạy Set

Bạn có thể kích hoạt toàn bộ 4 scene chỉ bằng 1 lệnh dispatch:

```bash
# Chạy trực tiếp qua ComfyUI (Local hoặc Modal URL):
python3 output/graydoom_consorts_nsfw/dispatch_nahla_set.py --host http://127.0.0.1:8188
```
