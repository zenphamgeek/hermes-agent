---
name: documentary-video-biet-dia-ly
description: >
  Footage-Centric Documentary Video Production skill for kênh "Biết Địa Lý Từ Ba Tôi".
  Tạo phóng sự địa lý Việt Nam chất lượng truyền hình/tài liệu điện ảnh từ footage
  Wikimedia Commons (CC BY/CC BY-SA) + Pexels + YouTube Fair-Use micro-clips.
version: 1.0.0
author: ZENPHAM, Hermes Agent
license: MIT
platforms: [linux, cli, telegram]
tags:
  - creative
  - documentary
  - geography
  - vietnam
  - video-production
  - footage-centric
related_skills:
  - content-factory
  - zenpham-podcast-producer
  - toi-doc-sach
metadata:
  hermes:
    tags: [documentary, geography, vietnam, video]
    related_skills: [content-factory]
---

# Documentary Video — Biết Địa Lý Từ Ba Tôi

Skill sản xuất video phóng sự tài liệu địa lý Việt Nam cho kênh **BIẾT ĐỊA LÝ TỪ BA TÔI**
(@phamtrai-dialy). Series: **VIỆT NAM — NHỮNG MIỀN SỐNG**.

Phong cách: National Geographic / BBC Earth documentary cho Việt Nam.

## When to Use

Dùng khi yêu cầu:
- Sản xuất tập phóng sự địa lý Việt Nam (long-form 20–28 phút, 16:9)
- Tìm footage tư liệu cho vùng đất/tỉnh/thành Việt Nam
- Viết kịch bản phóng sự theo phong cách "cha kể con nghe"
- Xử lý footage từ nhiều nguồn thành video đồng nhất cinematic
- Quản lý pipeline sản xuất: script → footage → grade → assemble → publish

KHÔNG dùng cho: Shorts/Reels, AI video, face swap, kênh Tôi Đọc Sách, kênh ZenPham.

## Prerequisites

1. **FFmpeg** cài đặt trên workstation
2. **Python 3.10+** với `.venv` hoạt động
3. **OmniVoice TTS** tại `http://10.123.214.178:80` cho voice-over
4. **Telegram Bot** `@pvt281_bot` (token: see `.env`) cho review/approval
5. **Disk space**: tối thiểu 5GB free cho wikimedia_vault + clips

## Core Principles — Ghi Nhớ TUYỆT ĐỐI

### 1. Footage-Centric Bidirectional (Bài Toán 2 Chiều)

```
Script ←→ Footage: Co giãn và tương hỗ hai chiều
```

- **Chiều 1 (Script → Footage)**: Tìm kiếm tư liệu chân thực, chuẩn xác nhất cho từng thực thể trong kịch bản.
- **Chiều 2 (Footage → Script Rewrite)**: Khi tư liệu trong kho có những cảnh sắc Hà Nội tuyệt đẹp (ví dụ: góc quay Cột cờ Hà Nội, Văn Miếu Quốc Tử Giám, phố tranh Hàng Trống) mà kịch bản đang viết về một thực thể khó tìm hình ảnh (như hố khai quật ngầm mờ ảo), **BẮT BUỘC** viết lại lời thoại neo trực diện vào cảnh đang có trong kho.
- **Quy tắc vàng**: *"Thấy gì nói nấy, nói gì thấy nấy."* Tuyệt đối không để xảy ra tình trạng "tai nghe một đằng, mắt nhìn một nẻo".

### 2. Quality Gate: Khớp Tuyệt Đối Thị Giác & Kịch Bản (Visual-Semantic Gate ≥ 90%)

Mọi tập phim tài liệu địa lý (đặc biệt từ Tập 02 trở đi) bắt buộc phải vượt qua Quality Gate này trước khi render:

1. **Công Thức Tính Visual-Semantic Match Ratio**:
   $$\text{Visual-Semantic Score} = \frac{\sum_{i=1}^{N} \text{Matched Entity Shots}_i}{\sum_{i=1}^{N} \text{Required Entity Anchors}_i} \times 100\% \ge 90\%$$
   - Mỗi câu thoại nhắc đến một thực thể địa danh/lịch sử/văn hóa thì trên khung hình tại thời điểm phát âm ($\pm 1.5s$) **BẮT BUỘC** phải hiển thị đúng thực thể đó.

2. **Quy Tắc Zero False B-Roll & Ràng Buộc Địa Lý Tuyệt Đối Theo Chủ Đề (Geographic Purity)**:
   - **Nguyên tắc cốt lõi**: Mỗi tập phóng sự tài liệu địa lý bị ràng buộc tuyệt đối vào phạm vi địa lý của tập đó. **100% hình ảnh trên khung hình phải thuộc đúng địa danh/tỉnh thành/vùng đất đang nói đến**.
   - Khi kịch bản nói về **Hà Nội**:
     - **NGHIÊM CẤM 100%**:
       + Tuyệt đối không dùng núi đá vôi karst Ninh Bình (Tam Cốc, Tràng An) hay chùa Bái Đính để minh họa Thăng Long.
       + Tuyệt đối không dùng ruộng bậc thang vùng cao Tây Bắc (Mù Cang Chải, Sa Pa) hay thợ dệt thổ cẩm vùng cao để minh họa đồng bằng sông Hồng hay Kẻ Chợ.
       + Tuyệt đối không dùng sông nước, xuồng ghe, cầu bê tông kênh rạch của Miền Tây Nam Bộ.
       + Tuyệt đối không dùng đường phố Châu Âu (nhà gạch đỏ, xe biển nước ngoài) hay khu tập thể Liên Xô/Đông Âu.
       + Tuyệt đối không dùng hình ảnh Sài Gòn (Bitexco, Landmark 81, Chợ Bến Thành, sông Sài Gòn), Đà Nẵng, Hội An.
     - **Yêu cầu bắt buộc**: Mọi khung hình thành phố phải nhận diện rõ nét và xác thực chất Hà Nội: dòng nước đỏ phù sa Sông Hồng & Cầu Long Biên, Hoàng thành Thăng Long Đoan Môn, Văn Miếu Quốc Tử Giám rồng đá, ngói vảy rêu phong phố cổ & cấu trúc nhà hình ống 36 phố phường, khu tập thể Kim Liên/Trung Tự chuồng cọp cơi nới, đường sắt trên cao Cát Linh - Hà Đông, Hồ Tây - Chùa Trấn Quốc - đường Thanh Niên, bàn cờ tướng và quán trà đá vỉa hè.

3. **Mật Độ Phóng Sự & Phân Đoạn Shot (3–8s/shot)**:
   - Mỗi scene voice-over dài 25–35 giây phải được cắt dựng từ **4–6 shots con**, không để một cú máy tĩnh trôi quá 8s:
     - **Establishing (5–8s)**: Flycam/drone đại cảnh định vị không gian địa lý.
     - **Action (4–6s)**: Nhịp sống con người, thợ thủ công, xe cộ, sinh hoạt phố thị.
     - **Detail (3–5s)**: Cận cảnh vân gỗ, gạch rêu, đinh tán thép hoen gỉ, cốc trà đá, bàn cờ tướng.
     - **Transition (2–3s)**: Cutaway, lia máy chuyển động mượt mà.

4. **Bù Trừ Thời Gian & Bảo Vệ Lời Thoại (Time Compensation & Padding)**:
   - **Head Padding ($T_{head}$)**: $0.4s - 0.5s$ hình ảnh chạy trước khi câu thoại cất lên, cho mắt người xem bắt nhịp cảnh mới sau chuyển cảnh.
   - **Tail Padding ($T_{tail}$)**: $0.6s - 0.8s$ hình ảnh duy trì sau khi dứt câu thoại cuối cùng của scene, chống bị transition chém cụt đuôi âm thanh.
   - **Overlap Offset ($D_{trans}$)**: Khi dùng crossfade/dissolve ($D_{trans} = 0.5s$), thời lượng video bắt buộc phải bù thêm:
     $$T_{video} \ge T_{voice} + T_{head} + T_{tail} + D_{trans} \ge T_{voice} + 1.6s$$
   - **Breathing Gap**: Giữa các chương (scenes) luôn chèn $1.5s$ khoảng thở để tạo chiều sâu chiêm nghiệm của phim tài liệu.

### 3. Blueprint Chuẩn Hóa Cho Tập 02: Hà Nội — Thành Phố Của Những Lớp Thời Gian

Tập 02 áp dụng trọn vẹn mô hình 8 Lớp Không Gian & Lịch Sử của Thăng Long - Hà Nội:

| Scene | Lớp Không Gian / Lịch Sử | Thực Thể Thị Giác Bắt Buộc (Visual Anchors) | Cú Máy & Nhịp Dựng |
|:---:|:---|:---|:---|
| **S1** | **Cold Open**: Thành phố bao nhiêu tuổi? | Flycam sương sớm Hồ Gươm, ngói phố cổ, cầu Long Biên, skyline mới | Establishing $\rightarrow$ Detail $\rightarrow$ Contrast |
| **S2** | **Lớp Sông & Đồng Bằng**: Nôi sinh thái châu thổ | Dòng sông Hồng đỏ phù sa, bãi bồi xanh mướt ngô khoai, dải đê sông Hồng | Flycam bãi bồi $\rightarrow$ Cận phù sa $\rightarrow$ Mặt đê |
| **S3** | **Lớp Kinh Thành**: Trái tim quyền lực 13 thế kỷ | Hoàng thành Thăng Long, Đoan Môn, Kỳ Đài Thăng Long, gạch rêu cổ kính | Toàn cảnh Đoan Môn $\rightarrow$ Cận gạch $\rightarrow$ Kỳ Đài |
| **S4** | **Lớp Kẻ Chợ**: 36 Phố Phường thủ công | Phố Hàng Bạc/Hàng Mã, nghệ nhân kim hoàn gõ búa, cấu trúc nhà hình ống | Action thợ bạc $\rightarrow$ Cận chi tiết $\rightarrow$ Ngõ hẹp |
| **S5** | **Lớp Thuộc Địa Pháp**: Giao thoa Á - Âu | Nhà hát Lớn Hà Nội, Cầu Long Biên Eiffel hoen gỉ, hàng xà cừ Phan Đình Phùng | Flycam Long Biên $\rightarrow$ Cận đinh tán gỉ $\rightarrow$ Biệt thự |
| **S6** | **Lớp Bao Cấp & Tái Thiết**: Ký ức bền bỉ | Khu tập thể Kim Liên/Trung Tự, lồng cọp cơi nới, cầu thang xi măng, sân chung | Cận chuồng cọp $\rightarrow$ Sân chung $\rightarrow$ Cầu thang cũ |
| **S7** | **Lớp Đô Thị Hiện Đại**: Vươn mình tái thiết | Cầu Nhật Tân dây văng, đường sắt trên cao Cát Linh - Hà Đông, cao ốc mới | Action tàu Cát Linh $\rightarrow$ Cầu Nhật Tân $\rightarrow$ Cổng làng |
| **S8** | **Khoảng Lặng Triết Lý**: Chiều tà lắng đọng | Hoàng hôn Hồ Tây sương mờ, quán trà đá vỉa hè góc phố, bàn cờ tướng cụ già | Cận cốc trà đá $\rightarrow$ Bàn cờ $\rightarrow$ Hoàng hôn mặt hồ |


### 4. Blueprint Chuẩn Hóa Cho Tập 07: Cà Mau — Nơi Đường Biên Đất Và Biển Không Đứng Yên

Tập 07 thiết lập quy chuẩn phim tài liệu địa lý dài tập ($\ge 25$ phút, 11 phần hoàn chỉnh) với bài toán động lực học bờ biển và sinh thái ngập mặn:

| Part | Chủ Đề & Luận Điểm Địa Lý | Thực Thể Thị Giác Bắt Buộc (Visual Anchors) | Cú Máy & Nhịp Dựng |
|:---:|:---|:---|:---|
| **P1** | **Đường Biên Bất Định**: Biên đất & biển không đứng yên | Mũi Cà Mau flycam 4K, bãi bùn phù sa non, sóng đập mép bùn, rễ đước bám đất, vỏ lãi lướt sóng | Establishing $\rightarrow$ Action $\rightarrow$ Contrast |
| **P2** | **Hai Mặt Giáp Biển**: Hải lưu & xung đột nhật/bán nhật triều | Sông Cửa Lớn, sông Gành Hào rẽ nước, dòng chảy hai chiều, bến sông ngập mặn | Map động lực học $\rightarrow$ Flycam dòng chảy $\rightarrow$ Nhịp triều |
| **P3** | **Cuộc Viễn Chinh Phù Sa**: Hạt bùn từ Himalaya về Đất Mũi | Cửa sông Cửu Long đỏ quạch, dòng hải lưu ven bờ mùa gió chướng, bãi triều bồi tụ | Macro phù sa $\rightarrow$ Vệ tinh bồi tụ $\rightarrow$ Bãi bồi non |
| **P4** | **Cây Tiên Phong**: Rễ thở mắm & rễ đước chân nơm | Rễ mắm đâm ngược lên bùn nhão, mầm mắm trôi dạt, rễ đước đan lưới bẫy trầm tích | Cận cảnh rễ thở $\rightarrow$ Rễ chân nơm $\rightarrow$ Rừng lấn biển |
| **P5** | **Vỏ Lãi & Sông Ngòi**: Giao thông trên mặt nước | Vỏ lãi đuôi tôm xé nước bọt trắng xóa, ngã ba sông, chợ nổi, bến đò, mạng lưới kênh | Action vỏ lãi $\rightarrow$ Toàn cảnh ngã ba sông $\rightarrow$ Sinh hoạt |
| **P6** | **Rừng Tràm U Minh Hạ**: Lớp than bùn & túi nước ngọt | Rừng tràm hoa trắng ngát hương, thảm lá mục, nước đỏ màu cánh gián, thợ gác kèo ong | Flycam tán tràm $\rightarrow$ Cận kèo ong $\rightarrow$ Dòng nước sẫm |
| **P7** | **Đất Lạt Hóa**: Đê ngăn mặn & cuộc chiến ngọt - mặn | Tuyến đê biển Tây, cống ngăn mặn, cánh đồng lúa một vụ xen lẫn vuông tôm | Contrast cống ngăn $\rightarrow$ Đồng lúa $\rightarrow$ Mương mặn |
| **P8** | **Mặt Trái Tôm Công Nghiệp**: Sụt lún đất & mất rừng | Vuông tôm thâm canh, giàn quạt nước sủi bọt, giếng khoan nước ngầm, cây đước khô chết | Action quạt nước $\rightarrow$ Cận đất nứt $\rightarrow$ Rừng suy thoái |
| **P9** | **Xói Lở Bờ Biển**: Khi biển ngoạm đất | Sóng dữ đập sạt lở bờ biển Đông, rễ cây trơ trọi đổ sụp, nhà dân mép nước xiêu vẹo | Cận cảnh sạt lở $\rightarrow$ Gốc cây đổ $\rightarrow$ Dấu vết đất mất |
| **P10**| **Kè Cọc Ly Tâm & Đê Chắn Sóng**: Giữ đất & bẫy phù sa | Tuyến kè ngầm cọc bê tông ly tâm giảm sóng, thảm phù sa bồi đắp sau kè, mầm cây mọc lại | Flycam kè ngầm $\rightarrow$ Cận cọc ly tâm $\rightarrow$ Mầm non hồi sinh |
| **P11**| **Cột Mốc GPS 0001**: Triết lý sống nương vào tự nhiên | Cột mốc tọa độ quốc gia GPS 0001, tượng con tàu hướng ra biển, hoàng hôn Đất Mũi | Chậm rãi, chiêm nghiệm $\rightarrow$ Outro motif signature |

### 5. Bộ Cổng Kiểm Toán Chất Lượng Kênh (Channel Quality Gates)

Mọi tập phim trong series "Việt Nam — Những Miền Sống" phải vượt qua 2 tầng gate trước khi phát hành:

1. **Cổng Nghiệm Thu Từng Phần (`part_by_part_gate.py`)**:
   - Thời lượng từng phần: $T_{part} \ge 120.0$s ($\le 180.0$s).
   - Âm lượng trung bình: $-35.0\text{ dB} \le \text{Mean Volume} \le -20.0\text{ dB}$ (EBU R128 broadcast norm).
   - Âm lượng đỉnh: $\text{Max Volume} \le 0.0\text{ dB}$ (chống méo tiếng/clipping).
   - Chuẩn kỹ thuật video: $1920\times 1080$, 30fps, YUV420p, audio AAC Stereo 44.1kHz.
   - Bắt buộc ghi nhận vào sổ cái `assets/scripts_video/acceptance_tap_XX.json`.

2. **Cổng Phim Tài Liệu Toàn Thể (`geographic_quality_gate.py`)**:
   - Cấu trúc trường đoạn: $\ge 10$ phần/chương.
   - Thời lượng bản Master: $\ge 1.500$ giây ($\ge 25.0$ phút).
   - Dung lượng kịch bản: $\ge 3.000$ từ.
   - Khiêm nhường học thuật: 0% từ ngữ thương mại/bán khóa học ("thực chiến" $\to$ "thực tế").
   - Nhãn ngữ âm song ngữ: Khớp 100% cặp thẻ `<en>...</en>`.
   - Chữ ký kết thúc (Outro Motif): *"Địa lý không chỉ nằm trên bản đồ. Nó nằm trong cách con người sống."*

### 6. Tối Ưu Hóa Phân Luồng & Mã Hóa Video (Hardware-Aware Vibe Coding)

- **Chống CPU Thrashing**: Khi xử lý song song với Python `ThreadPoolExecutor`, FFmpeg mặc định sẽ chiếm dụng toàn bộ số luồng của CPU trên mỗi tiến trình con. Ví dụ: chạy 8 workers trên CPU 16 threads sẽ tạo ra $8 \times 16 = 128$ luồng $\to$ load average vọt lên 143, hệ thống bị nghẽn context-switching, tốc độ render chậm gấp 10 lần.
  - **Quy tắc**: BẮT BUỘC gán cờ `-threads 2` (hoặc số thread cố định $\le 2$) cho mỗi lệnh gọi FFmpeg trong worker.
- **Tính Toàn Vẹn Nguyên Tử (Atomic MP4 Writing)**: Khi tiến trình bị ngắt giữa chừng, FFmpeg để lại file MP4 rỗng/thiếu `moov` atom làm hỏng toàn bộ bước nối `concat`.
  - **Quy tắc**: Luôn render ra file tạm `tmp_*.mp4`, kiểm tra tính toàn vẹn bằng `ffprobe -v error -show_entries format=duration <file>`, rồi mới `os.rename()` sang tên file đích.

### 7. Thiết Kế Thumbnail Đồng Bộ (`cover_design_engine.py`)

- **Kích thước**: $1920 \times 1080$ (16:9 Landscape).
- **Hero Frame**: Trích xuất trực tiếp khung cảnh đại cảnh đẹp nhất (4K Flycam) từ footage thực tế của tập đó.
- **Gold Brand Pill (`#E6A822`)**: `BIẾT ĐỊA LÝ TỪ BA TÔI • VIỆT NAM – NHỮNG MIỀN SỐNG • TẬP XX`.
- **Typography 3D Nổi Khối**:
  - Tầng 1: Tên địa danh (chữ trắng in hoa, font NotoSansDisplay-Bold, đổ bóng sâu 3D).
  - Tầng 2: Câu định vị cảm xúc/đặc trưng địa lý (màu vàng mật ong `#FFE65A`).
- **Phụ đề**: `Khám phá câu chuyện đằng sau [Địa danh].`

### 8. Unified Cinematic Grade

TOÀN BỘ footage phải qua pipeline 5 tầng:

1. **Geometry Lock**: 1920x1080, 30fps progressive, yuv420p (Anti-skew, crop chuẩn tỉ lệ).
2. **Alluvial Clay Tone**: Warm shadows, teal highlights, saturation 1.12.
3. **35mm Film Grain**: `noise=alls=6:allf=t` — xóa chênh lệch độ nét giữa các nguồn camera.
4. **Cinematic Vignette**: `vignette=PI/4.5` — hút mắt vào trung tâm chủ thể.
5. **Unified Foley**: Ambiance tự nhiên xuyên suốt (tiếng còi tàu xa, tiếng xào xạc lá cây, tiếng phố xá êm).

### 5. Những Điều Tuyệt Đối Cấm

- Ghép stock footage bừa bãi (MC nói Hà Nội nhưng dùng video Sài Gòn, Hội An hoặc nước ngoài).
- Dùng clip nguồn liên tục >15 giây không có lý do.
- Bỏ qua attribution cho footage CC BY.
- Dùng footage có watermark lớn hoặc logo choán giữa khung hình.
- Tạo "stock compilation" không có luận điểm và không có neo thực thể chính xác.
- Bỏ qua việc kiểm tra âm lượng bằng `volumedetect` dẫn đến mất tiếng sau khi ghép nối.

## Footage Sourcing — Hệ Phân Loại

### GREEN — Ưu Tiên
- **Wikimedia Commons**: CC0, CC BY, CC BY-SA — TƯ LIỆU SỐ 1
- **Pexels Video**: Pexels License — Flycam 4K, phong cảnh và con người
- **Pixabay**: Content License — B-roll bổ sung
- **Footage tự quay** hoặc được cấp phép trực tiếp

### YELLOW — Kiểm Tra Kỹ  
- CC BY-SA (phải share-alike)
- Footage có người nhận diện rõ
- Media từ YouTube CC (verify trang file)

### RED — Không Dùng
- YouTube standard license (trừ micro-clip 3–6s fair-use)
- TikTok/Facebook/Reels tải lại
- Phim điện ảnh, chương trình TV, documentary đài khác

### Fair-Use Micro-Clip (YouTube)

Chỉ khi không tìm được footage GREEN/YELLOW:

```bash
# Cắt đúng 6 giây từ YouTube video
yt-dlp --download-sections "*01:25-01:31" \
  -f "bestvideo[height<=1080][ext=mp4]+bestaudio/best" \
  --force-keyframes-at-cuts -o "clips_raw/scene_N.mp4" \
  "https://www.youtube.com/watch?v=VIDEO_ID"
```

Quy tắc:
1. Micro-clip 3–6 giây MAX, không quá 8s liên tục
2. Luôn `-an` (xóa audio gốc), chỉ dùng hình minh họa
3. Attribution on-screen 2–3 giây: `Tư liệu: [Kênh YouTube]`
4. Tránh logo/watermark lớn

## Procedure — Quy Trình Sản Xuất 1 Tập

### Stage 0: Đọc Master Plan & Dossier

```
Luôn đọc trước khi bắt đầu tập mới:
assets/scripts_video/vietnam_nhung_mien_song_agent_master_plan.md
assets/scripts_video/INDEX_E01_E08_Biet_Dia_ly_tu_Ba_toi.md
assets/scripts_video/BILINGUAL_TTS_QA_VI.md
```

### Stage 1: Kịch Bản 10+ Phần & Phân Khối Sub-3-Minute (CHỐNG LAZY CODE)

> **QUY TẮC BẮT BUỘC:** Tuyệt đối cấm viết kịch bản 8 đoạn ngắn tóm tắt (~4 phút). Mỗi tập phim tài liệu địa lý bắt buộc phải là một tác phẩm điện ảnh hoàn chỉnh:
> - **Số phần tối thiểu**: $\ge 10$ phần (Chapters/Parts).
> - **Tổng thời lượng video**: $\ge 25$ phút (1,500 giây – 1,700 giây).
> - **Phân rã khối Sub-3-minute**: Mỗi phần dài $120\text{s} - 170\text{s}$ ($\le 180$s), vừa vặn nhịp tiếp nhận của người xem và khả năng xử lý của GPU/CPU.
> - **Dung lượng voiceover**: Mỗi phần chứa $250 - 350$ từ tiếng Việt chuẩn mực, giàu hàm lượng khoa học và chiều sâu cảm xúc (~1.5 – 2.0 phút giọng nói) + 40 – 60 giây khoảng thở thiên nhiên (negative space). Tổng kịch bản đạt $3,000 - 3,500$ từ.
> - **Quy tắc đọc song ngữ (Bilingual TTS Contract)**:
>   - Các thuật ngữ khoa học, địa danh quốc tế, mã tọa độ được đặt trong thẻ `<en>...</en>` tại ranh giới câu hoặc mệnh đề hoàn chỉnh (ví dụ: `<en>GPS 0001</en>`, `<en>UNESCO World Biosphere Reserve</en>`, `<en>Ramsar site</en>`, `<en>offshore breakwater</en>`).
>   - Không thay đổi spelling thuật ngữ thành phiên âm Việt ở luồng mặc định.
>   - Đảm bảo voice cùng sử dụng reference Zen Miền Tây (`zenpham-zen-meditation-mientay.wav`) tốc độ 1.08x.

### Stage 2: Footage Sourcing (Bidirectional & Absolute Locality)

1. Tìm footage trên Wikimedia Commons & Pexels theo danh mục thực thể Cà Mau:
   - 100% hình ảnh phải thuộc đúng địa danh Cà Mau (Mũi Cà Mau, Rừng Đước Năm Căn, Ngọc Hiển, U Minh Hạ, Sông Cửa Lớn, Gành Hào, Kè cọc ly tâm, Vuông tôm sinh thái).
   - Tuyệt đối cấm False B-Roll (không lấy cảnh núi đá vôi miền Bắc, ruộng bậc thang Tây Bắc, kênh rạch Sài Gòn).
2. Kiểm tra bản quyền: Ưu tiên GREEN (CC0, CC BY, Pexels, Pixabay). Không dùng RED.
3. Không để lọt watermark hoặc logo nguồn.
4. Quản lý trùng lặp: Đăng ký toàn bộ clip vào `assets/footage_pool/footage_usage_registry.json`, đảm bảo 0% trùng lặp với các tập khác trong series.

### Stage 3: Voice-Over Generation (OmniVoice Zen Miền Tây)

Dùng OmniVoice TTS (`http://10.123.214.178:80`) với voice profile "zenpham-zen-meditation-mientay":

```bash
# Generate VO tuần tự cho toàn bộ N phần (N >= 10)
python3 assets/scripts_video/tts_zen.py --script assets/scripts_video/vietnam_nhung_mien_song_tap_XX.md
```

### Stage 4: Footage Extraction + Cinematic Grade

Tất cả các shots tư liệu qua bộ lọc cinematic 5 tầng:
1. Geometry: Scale & Crop chuẩn 1920x1080 / 2560x1440, 30fps progressive, YUV420p.
2. Tone curve: Alluvial Clay Tone (Ấm áp phù sa, teal bóng râm).
3. 35mm film grain nhẹ (`noise=alls=6:allf=t`) hòa trộn các nguồn máy quay khác nhau.
4. Cinematic vignette hút mắt chủ thể.

### Stage 5: Assembly & Nghiệm Thu Từng Phần (Part-by-Part Acceptance)

Mọi tập phim được dựng và nghiệm thu theo 2 cấp độ:
1. **Nghiệm thu từng phần độc lập (Sub-part Acceptance)**:
   ```bash
   python3 assets/scripts_video/assemble_documentary.py --episode XX --part 1
   python3 assets/scripts_video/assemble_documentary.py --episode XX --part 2
   # ... lần lượt đến part N
   ```
   - Mỗi phần phải đạt: thời lượng $\ge 120$s, âm thanh `volumedetect` mean volume $> -30$dB, visual match $\ge 90\%$.
2. **Nối Master Video 2K QHD Toàn Tập**:
   ```bash
   python3 assets/scripts_video/assemble_documentary.py --episode XX --master-2k
   ```
   - Xuất bản tại `output/vietnam_nhung_mien_song_tap_XX_master_2k.mp4`.
   - Độ phân giải: 2K QHD (2560x1440 @ 30fps) nội suy Lanczos, bitrate 16-24 Mbps để kích hoạt codec `vp09`/`av01` trên YouTube.
   - Tổng thời lượng: $\ge 1,500$ giây ($> 25$ phút).

### Stage 6: Cover Scene & Thumbnail Độc Bản (Hero-First)

1. **Quy tắc Thumbnail Content Factory**:
   - **Hero Visual $\ge 50 - 60\%$ diện tích**: Hình tượng Cà Mau đại cảnh hùng vĩ (Mũi Cà Mau chia đôi hai màu nước, cột mốc tọa độ, mầm mắm non vươn lên giữa bãi phù sa).
   - **Cấm rập khuôn template**: Tuyệt đối không dùng lại một kiểu nền đen tối góc trái. Mỗi tập có chữ ký màu riêng (Tập 07: Acid Matrix Emerald `#10B981` & Alluvial Gold `#F59E0B`).
   - **Typography Auto-Punch (2–4 từ cực đại)**: Ví dụ `ĐẤT NỞ RA BIỂN` hoặc `BỜ BIỂN KHÔNG ĐỨNG YÊN`, cỡ chữ lớn đọc rõ trên màn hình điện thoại.
   - **Brand Pill**: `🌏  BIẾT ĐỊA LÝ TỪ BA TÔI  •  TẬP 07`. Không lấy tên slug file.

2. Gửi preview qua Telegram `@pvt281_bot`:
```bash
python3 assets/scripts_video/video_review_bot.py --send-preview \
  --video output/vietnam_nhung_mien_song_tap_XX.mp4
```

4. Upload YouTube (pending user approval)

## File Structure

```
assets/scripts_video/
├── vietnam_nhung_mien_song_agent_master_plan.md   # Master production rules
├── vietnam_nhung_mien_song_tap_XX.md              # Episode scripts
├── footage_centric_engine.py                       # Bidirectional footage↔script engine
├── cinematic_filter_engine.py                      # 5-layer cinematic grading
├── wikimedia_footage_manager.py                    # Wikimedia download & cut
├── assemble_podcast.py                            # Final video assembly
├── cover_design_engine.py                          # Thumbnail generator
├── video_review_bot.py                            # Telegram review daemon
├── wikimedia_vault/                               # Downloaded source footage
├── clips/                                         # Processed scene clips
│   ├── shots/                                     # Individual shot extracts
│   └── shots_graded/                              # Graded shot files
├── audio/vietnam_nhung_mien_song_tap_XX/          # Voice-over WAV files
└── output/                                        # Final rendered videos
```

## Script Format

Mỗi tập kịch bản cần đúng format sau (xem `vietnam_nhung_mien_song_tap_01.md`):

```markdown
Đoạn N:
Cảm xúc: phong_su_diem_tinh
Hình ảnh: [Shot-by-shot sequence dùng → arrows]
Từ khóa: search keywords for footage
Footage: source_file.webm @start_time1,@start_time2,...
Lời thoại: "Voice-over text here"
```

**Footage line** là REQUIRED — trace rõ nguồn footage cho mỗi scene.

## Channel Branding

- **Tên kênh**: BIẾT ĐỊA LÝ TỪ BA TÔI
- **Tagline**: "Hiểu một vùng đất, để hiểu những người sống trên đó."
- **Motif kết phim**: "Địa lý không chỉ nằm trên bản đồ. Nó nằm trong cách con người sống."
- **Persona**: Người cha giải thích cho con — trầm ấm, điềm tĩnh, gần gũi
- **Voice**: zenpham-zen-meditation-mientay, speed 1.08x
- **Color grade**: PHAMTRAI_DIALY (Alluvial Clay + Teal Shadow)
- **Thumbnail**: High contrast, warm earth tones, bold Vietnamese typography

## Guardrails

1. **Không mô tả thứ người xem đang thấy** — VO giải thích WHY/HOW/SO WHAT
2. **70% factual** — không biến thành văn xuôi mơ hồ
3. **Mỗi 60–90s phải chuyển**: địa điểm, scale, câu hỏi, nhân vật, dữ kiện
4. **Không dùng clip >15s liên tục** từ cùng một nguồn
5. **Attribution bắt buộc** cho CC BY footage (trong YouTube description)
6. **Verify premise** — không "fix" design đã có ý đồ (xem AGENTS.md)
8. **Footage Độc Lập Giữa Các Tập Trong Series (ZERO FOOTAGE REUSE - QUALITY GATE BẮT BUỘC)**:
   - Nghiêm cấm dùng lặp lại bất kỳ B-roll hay drone shot nào giữa các tập khác nhau trong series "Việt Nam — Những Miền Sống" (cả 16:9 Longform và Shorts 9:16).
   - Mỗi tập phải có manifest footage độc lập hoàn toàn. Chạy `audit_series_footage.py --series biet_dia_ly --audit` đạt 0% trùng lặp trước khi render.
   - Không sử dụng nhạc bản quyền (ví dụ `soft_piano_ambient.mp3`), chỉ dùng nhạc bản quyền sạch trong `assets/background_music/`.

## Quick Reference

```
/documentary plan <vùng_đất>     → Research + outline + shot list
/documentary footage <keywords>  → Search Wikimedia/Pexels footage
/documentary script <tập>        → Write VO script + footage mapping
/documentary process <tập>       → Extract, grade, concatenate footage
/documentary assemble <tập>      → Sync VO + video + music → final
/documentary review <tập>        → Send preview to Telegram for approval
/documentary publish <tập>       → Upload to YouTube (after approval)
/documentary status              → Report pipeline progress
```

## Verification

1. Coverage report: tất cả scenes ✅ OK (video ≥ audio duration + padding)
2. Cinematic grade: tất cả clips đồng nhất tông màu PHAMTRAI_DIALY
3. Visual-Semantic Gate: 100% Visual Anchors (Cầu Long Biên, Hoàng Thành Thăng Long, Đê Sông Hồng, Phố Hàng Bạc, KTT Kim Liên, Cát Linh - Hà Đông, Hồ Tây) khớp đúng footage thật
4. Zero Footage Reuse Gate: `audit_series_footage.py` xác nhận 0% footage trùng lặp với các tập trước trong cùng series
5. Attribution: tất cả CC BY footage có credit trong description
6. Audio volume integrity: `volumedetect` xác nhận `mean_volume > -30 dB` xuyên suốt mọi scene, không bao giờ mất tiếng
7. Final render: 1080p 30fps h264, CRF 18, file size < 2GB


