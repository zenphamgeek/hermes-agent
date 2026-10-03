---
name: infographic-director
description: "Đạo diễn Đồ họa Thông tin Địa lý & Khoa học (Geographic & Scientific Infographic Director) cho series 'Việt Nam — Những Miền Sống' và kênh BIẾT ĐỊA LÝ TỪ BA TÔI. Triết lý tối thượng: FOOTAGE-CENTRIC (100% cảnh quay thực tế làm nền tảng điện ảnh, Infographics là HUD telemetry bán trong suốt Frosted Glassmorphism bổ trợ dữ liệu, tuyệt đối cấm biến phim thành slide thuyết trình). Quản trị bản đồ động GeoJSON/DEM, biểu đồ thủy văn, kinetic typography tọa độ GPS, và quy chuẩn màu sắc nhận diện kênh đồng bộ cùng giọng đọc V8 Expressive Prosody."
version: 1.0.0
author: ZENPHAM, Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [infographic-director, footage-centric, geo-infographics, map-animation, hud-telemetry, glassmorphism, geographic-documentary, biet-dia-ly-tu-ba-toi, manim-2k]
    related_skills: [manim-director, manim-production, vietnamese-expressive-tts, dual-engine-cinematics]
---

# Infographic Director — Đạo Diễn Đồ Họa Thông Tin Địa Lý & Khoa Học (v1.0)

> **TRIẾT LÝ TỐI THƯỢNG (CORE DIRECTIVE): FOOTAGE-CENTRIC LÀ QUAN TRỌNG NHẤT.**  
> Trong phim tài liệu địa lý, thiên nhiên và con người Việt Nam là nhân vật chính. Khung hình thực địa 2K QHD (flycam đại cảnh, cận cảnh lao động, sông ngòi, rừng tràm, chợ nổi) **chiếm trọn 100% không gian thị giác**.
> 
> Đồ họa thông tin (Infographics), Bản đồ (Maps) và Khung đo đạc (Telemetry HUD) **CHỈ ĐÓNG VAI TRÒ LÀ LỚP KÍNH THÔNG MINH (INTELLIGENT VIEWFINDER OVERLAY)** tăng cường tri thức cho người xem. **TUYỆT ĐỐI KHÔNG BAO GIỜ** biến cảnh phim thành một slide thuyết trình thô cứng hay che khuất vẻ đẹp của cảnh quan thực tế.

---

## 1. Bản Sắc Thị Giác & Bảng Màu Nhận Diện (Neo-Noir Geography Palette)

Đồ họa thông tin của kênh **BIẾT ĐỊA LÝ TỪ BA TÔI** mang phong cách tối giản công nghệ cao (Cyber-Minimalist Geographic HUD):

| Mã màu Hex | Tên màu | Ứng dụng trong Infographics | Ý nghĩa biểu tượng |
| :---: | :--- | :--- | :--- |
| `#E6A822` | **Sunset Gold** (Vàng Hoàng Hôn) | Tiêu đề phân đoạn, điểm nhấn dữ liệu, số liệu kỷ lục, huy hiệu kênh | Phù sa màu mỡ, nắng ấm phương Nam, giá trị tri thức bền vững |
| `#3B82F6` | **River Hydro Blue** (Xanh Dòng Nước) | Vector dòng chảy sông ngòi, đường ranh giới thủy triều, biểu đồ lưu lượng | Dòng sông Tiền, sông Hậu, Biển Đông, sức sống đại ngàn |
| `#10B981` | **Melaleuca Green** (Xanh Rừng Tràm) | Khu bảo tồn sinh quyển, rừng ngập mặn, vùng nông nghiệp thích ứng | Rừng tràm Trà Sư, hệ sinh thái thuận thiên |
| `#F8FAFC` | **Pure Cloud White** (Trắng Mây Trời) | Nhãn text, số liệu tọa độ GPS, chú thích địa danh | Rõ ràng, tương phản cao trên mọi footage |
| `rgba(15,23,42,0.45)` | **Frosted Slate Glass** (Phiến Đá Mờ) | Nền hộp HUD telemetry, thanh đo đạc | Bán trong suốt, làm nổi bật chữ mà không che cảnh |

---

## 2. Quy Chuẩn Khung HUD Telemetry Bán Trong Suốt (Frosted Glassmorphism HUD)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 100% KHUNG HÌNH FOOTAGE THỰC ĐỊA 2K QHD (Sông Tiền, Chợ Nổi, Rừng Tràm...)  │
│                                                                             │
│                                            ┌──────────────────────────────┐ │
│                                            │ 📍 TỌA ĐỘ THỦY VĂN: CẦN THƠ  │ │
│                                            │ 10°02' N — 105°47' E         │ │
│                                            │ Lưu lượng: 14.000 m³/s       │ │
│                                            │ Mực nước: +1.8m (Triều lớn) │ │
│                                            └──────────────────────────────┘ │
│                                                (HUD Bán Trong Suốt 45%)     │
│                                                                             │
│  [ PHỤ ĐỀ MOBILE-FIRST CĂN ĐÁY Y <= -2.60 ]                                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

1. **Độ Mờ & Xuyên Sáng (Transparency Standard)**:
   - Nền HUD: Bắt buộc dùng `rgba(15, 23, 42, 0.40 - 0.50)` kết hợp `backdrop-filter: blur(12px)`.
   - Viền khung: 1px hairline viền sáng nhẹ `rgba(255, 255, 255, 0.12)`.
   - Bo góc: $R = 8\text{px} - 12\text{px}$.
   - **CẤM TUYỆT ĐỐI**: Nền đen kịt (opaque black `#000000`) hay hộp chữ đặc che mất dòng sông bên dưới.
2. **Vị Trí Đặt HUD An Toàn**:
   - Vùng ưu tiên: Góc trên bên phải ($X \in [+3.0, +6.0]$, $Y \in [+1.5, +3.2]$ trong tọa độ Manim).
   - Tuyệt đối không đặt HUD chính giữa màn hình làm chắn tầm nhìn của máy bay flycam hay mặt tiền ghe thuyền.

---

## 3. Quy Chuẩn Bản Đồ Động (Animated Geographic Maps)

Khi cần mô phỏng địa mạo hoặc cấu trúc không gian (ví dụ: Mạng lưới 9 cửa sông Cửu Long, sơ đồ xâm nhập mặn):

1. **Hiển Thị Trên Nền Footage (Footage-Underlay Mapping)**:
   - Bản đồ vector (đường ranh giới, sông ngòi) vẽ bằng nét neon mảnh (stroke width 2–3px) nổi ngay trên nền footage flycam đã được làm tối nhẹ vignette (-15% exposure), không đưa người xem vào một màn hình đồ họa trống rỗng.
2. **Động Học Tinh Tế (Physical Motion)**:
   - Các đường dòng chảy (`vector river branches`) xuất hiện bằng hiệu ứng `Create()` hoặc `ShowPassingFlash()` với tốc độ mô phỏng vận tốc thực tế của con nước (0.8s – 1.5s).
   - Tọa độ GPS nhảy số theo kiểu cơ học (digital ticker countdown) từ 0 đến tọa độ thực trong 0.8s.

---

## 4. Đồng Bộ Nhịp Điệu Giọng Đọc V8 Expressive Prosody

1. **Thời Điểm Xuất Hiện (In-Point Lead)**:
   - HUD hoặc Bản đồ chỉ xuất hiện **sau 0.6s – 1.0s** kể từ khi giọng đọc cất lên câu thoại liên quan (để tai người xem đón nhận khái niệm trước, sau đó mắt mới đối chiếu dữ liệu trên màn hình).
2. **Thời Lượng Tồn Tại (Linger Duration)**:
   - Tối thiểu: **4.0 giây** (đủ để mắt người đọc hết 3 dòng thông số).
   - Tối đa: **8.0 giây** (phải tự động biến mất bằng `FadeOut(run_time=0.6)` để trả lại sự thoáng đãng thuần khiết cho footage).
3. **Phản Hồi Theo Mood**:
   - Khi giọng đọc chuyển sang Wave triết lý (`W01_SubBass_Drift`, `W24_Grand_Outro`), **toàn bộ HUD biến mất 100%**, chỉ để lại cảnh quay thiên nhiên thuần túy cùng giọng người cha và tiếng nhạc nền lắng đọng.

---

## 5. Danh Mục Kiểm Toán Infographic (Infographic Quality Gate Checklist)

Trước khi duyệt bất kỳ cảnh overlay nào vào bản Master:
- [ ] **Footage Dominance**: Cảnh quay thực địa có chiếm trọn màn hình và rõ ràng dưới lớp HUD không?
- [ ] **Transparency Check**: Nền HUD có đủ độ trong suốt ($\ge 50\%$) không?
- [ ] **Color Brand Integrity**: Đúng bảng màu Sunset Gold `#E6A822` và River Blue `#3B82F6` chưa?
- [ ] **Typography**: Font không chân hiện đại (Inter, Montserrat, SF Pro Display), kích thước nhãn $\ge 24\text{pt}$ ở 2K.
- [ ] **Zero Overlap**: HUD có va chạm với Section Title Card hoặc Phụ đề đáy không?
