# Quy Chuẩn Sản Xuất Phim Tài Liệu Địa Lý (Geographic Documentary Protocol)
========================================================================

> **ĐỊNH VỊ THƯƠNG HIỆU & SỨ MỆNH KÊNH:**
> **Kênh**: BIẾT ĐỊA LÝ TỪ BA TÔI (`@phamtrai-dialy`)  
> **Slogan**: *"Hiểu một vùng đất, để hiểu những người sống trên đó."*  
> **Tông giọng & Linh hồn**: Giọng người cha miền Tây trầm ấm, chiêm nghiệm, bao dung; dẫn dắt người con đi qua từng vùng đất bằng góc nhìn Địa lý Nhân văn (Human Geography) — nơi địa hình, sông núi, khí hậu định hình nên tính cách, số phận và văn hóa của con người.

---

## 1. Cổng Kiểm Soát Chất Lượng Kịch Bản (Script Quality Gate — CHỐNG LAZY CODE)

Mọi kịch bản trong series *Việt Nam — Những Miền Sống* bắt buộc phải vượt qua các tiêu chí sau:

1. **Chuẩn Phim Tài Liệu Dài Tập (Longform Documentary $\ge 25$ Phút)**:
   - **Số phần tối thiểu**: Bắt buộc chia thành **ít nhất 10 phần** ($\ge 10$ Parts/Chapters).
   - **Tổng thời lượng video**: Bắt buộc **trên 25 phút** ($\ge 1,500$ giây, mục tiêu 25 – 28 phút). Tuyệt đối cấm kịch bản rút gọn 8 đoạn ngắn ~4 phút.
   - **Phân rã khối Sub-3-minute**: Mỗi phần dài $120\text{s} - 170\text{s}$ ($\le 180$s). Lời bình voiceover chứa $250 - 350$ từ tiếng Việt (~1.5 – 2.0 phút) kết hợp 40 – 60 giây khoảng thở thiên nhiên và âm nhạc ambient tự kể chuyện. Tổng dung lượng kịch bản đạt $3,000 - 3,500$ từ.
2. **Cấu trúc tự sự 3 lớp (The 3-Layer Narrative)**:
   - *Lớp 1: Bức tranh địa lý tự nhiên* (Sông, núi, phù sa, khí hậu, hướng gió, độ dốc, thủy động lực học).
   - *Lớp 2: Sự thích ứng của con người* (Quy hoạch kinh thành, đắp đê, làm nhà rường, xuồng ghe, công trình giảm sóng, sinh kế).
   - *Lớp 3: Triết lý nhân sinh đọng lại* (Bài học của người cha gửi gắm cho con).
3. **Quy Tắc Đọc Song Ngữ & Động Cơ TTS (Bilingual TTS & Engine Contract)**:
   - **Động cơ mặc định:** **V8 Enhanced VieNeu-TTS** (VieNeu-TTS v3 Turbo 48kHz Streaming kết hợp Chuỗi Master Giọng Đọc 5 Giai Đoạn - Studio Vocal Mastering Chain: High-pass 80Hz, De-mud EQ 300Hz, Presence EQ 3.8kHz, Air Treble 9kHz, EBU R128 Loudnorm -15 LUFS). OmniVoice (F5-TTS) đóng vai trò dự phòng thứ cấp.
   - Các thuật ngữ khoa học, tên tổ chức quốc tế, chuẩn tọa độ hoặc trích dẫn Latinh được đặt trong thẻ `<en>...</en>` tại ranh giới câu hoặc mệnh đề hoàn chỉnh (ví dụ: `<en>GPS 0001</en>`, `<en>UNESCO World Biosphere Reserve</en>`, `<en>Ramsar site 2088</en>`, `<en>offshore breakwater</en>`).
   - Giữ nguyên văn phong tiếng Anh chuẩn, cấm phiên âm tiếng Việt lệch chuẩn (như không viết "Răm-xa" hay "Gờ-pê-ét").
   - Giọng đọc: Zen Miền Tây (`zenpham-zen-meditation-mientay.wav`) với nhịp điệu trầm ấm, điềm tĩnh (1.08x).
   - Quy chuẩn âm vị học: $Q \to$ "Qui" (cấm đọc "Cu"), $D, Đ \to$ "Đê" (cấm đọc "Dê"), $L \to$ "E-lờ", $R \to$ "E-rờ", $V \to$ "Vê".
4. **Motif Kết Thúc Bất Biến**:
   - Mỗi tập phải kết lại bằng một câu đúc kết triết lý của người cha:
     * *“Địa lý không chỉ nằm trên bản đồ. Nó nằm trong cách con người sống.”*

---

## 2. Cổng Kiểm Soát Độ Chân Thực Địa Lý (Geographic Purity & Footage-Centric Gate)

> **QUY TẮC TỐI THƯỢNG: FOOTAGE-CENTRIC LÀ QUAN TRỌNG NHẤT**  
> 100% không gian thị giác của video tài liệu phải lấy cảnh quay thực địa (flycam, cận cảnh đời sống, thiên nhiên sông nước) làm trung tâm điện ảnh. Đồ họa thông tin và bản đồ chỉ là HUD bán trong suốt bổ trợ dữ liệu theo chuẩn của skill `infographic-director`. Tuyệt đối cấm hội chứng slide thuyết trình và cấm che lấp cảnh quan thực tế.
>
> **THƯỚC ĐO CHUẨN MỰC (GOLDEN BASELINE):**  
> Toàn bộ các tập phim của series *Việt Nam — Những Miền Sống* bắt buộc phải kế thừa và đáp ứng các chỉ số kỹ thuật và nghệ thuật đã được chuẩn hóa tại [`BASELINE_EP01_SPEC.md`](file:///home/zen/hermes-agent/production_hub/channels/ch_biet_dia_ly/BASELINE_EP01_SPEC.md).

1. **Bắt Buộc File LLM Meta (.meta.json) Đi Kèm & Matching $\ge 95\%$**:
   - **Tất cả Footage đưa vào sản xuất bắt buộc phải có File LLM Meta (`<clip_name>.meta.json`) đi kèm.**
   - File `.meta.json` phải định nghĩa: Vùng địa lý, địa mạo (`canal_network`, `floating_market`, `melaleuca_forest`, v.v.), tọa độ, góc máy, thực thể thị giác, và điểm đánh giá khớp kịch bản (`script_evaluation.score >= 95.0`).
   - Cấm sử dụng các clip có điểm Semantic Matching $< 95\%$ hoặc có dấu hiệu không ăn khớp với câu thoại đang đọc.

2. **Đúng địa danh 100% (Absolute Locality — Zero False B-Roll)**:
   - Tập về **Hà Nội**: Chỉ sử dụng footage Hồ Gươm, Tháp Rùa, phố cổ, Cầu Long Biên, bãi bồi Sông Hồng, chùa Trấn Quốc, đường sắt Cát Linh. Tuyệt đối không dùng skyline Thượng Hải hay đường phố Bangkok.
   - Tập về **Huế**: Bắt buộc chỉ dùng Sông Hương, Núi Ngự Bình, Kỳ Đài Ngọ Môn, hồ sen Đại Nội, Lăng Tự Đức/Khải Định/Minh Mạng, nhà vườn Kim Long/Vỹ Dạ, cầu Trường Tiền, phá Tam Giang. Cấm dùng chùa chiền Trung Quốc hay phong cảnh miền núi phía Bắc thay thế.
   - Tập về **Miền Tây**: Chỉ dùng chợ nổi Cái Răng, sông Tiền/sông Hậu, bến phà, rừng tràm Trà Sư, cánh đồng sen Tháp Mười, ghe xuồng Châu Đốc.

3. **Đa dạng góc máy (Multi-Shot Diversity)**:
   - Mỗi phân cảnh 30 giây bắt buộc ghép từ **3 đến 4 shot quay thực tế khác nhau** (tối thiểu 7 - 8 giây/shot): kết hợp giữa flycam toàn cảnh (aerial wide), cận cảnh đời sống (ground detail), và đại cảnh kiến trúc văn hóa.

4. **Quy tắc Khử Sạch Watermark (Zero Watermark Rule)**:
   - Tuyệt đối không để lọt logo, watermark nguồn (ví dụ: `Footage by 1.61 MEDIA`, watermark Pexels/Storyblocks, timestamp camera). Mọi footage flycam phải qua bộ lọc crop/delogo trước khi scale về 2K Master.

5. **Cổng Phân Biệt Địa Hình Địa Lý (Smart Landform Detector Gate)**:
   - **Phân biệt tuyệt đối giữa Ruộng Nước Bằng Phẳng (Miền Tây / Đồng Bằng) và Ruộng Bậc Thang (Tây Bắc / Miền Núi)**:
     * *Vùng trũng / Đồng bằng sông Cửu Long / Cửa sông (Tập 01, 02, 03, 04, 07)*: Chỉ sử dụng ruộng nước phẳng lặng, kênh rạch thẳng tắp, bờ ruộng bằng, ghe xuồng, dừa nước, rừng ngập mặn. **Tuyệt đối cấm** hình ảnh ruộng bậc thang, sườn núi dốc, thung lũng đá tai mèo Tây Bắc (Hà Giang, Mù Cang Chải, Sa Pa).
     * *Vùng núi cao đồi dốc (Tập 08 Sa Pa / Hoàng Liên Sơn)*: Bắt buộc sử dụng ruộng bậc thang uốn lượn theo đường đồng mức, đèo dốc hiểm trở, thung lũng mây, đỉnh núi cao. **Tuyệt đối cấm** ruộng nước trũng phẳng lỳ hoặc rừng ngập mặn.
   - Mọi ứng viên B-roll trước khi render đều phải qua kiểm duyệt tự động bởi `assets/scripts_video/geographic_landform_detector.py`.


---

## 3. Cổng Kiểm Soát Thumbnail / Cover Scene (Thumbnail & Human CC Portrait Gate)

> **QUY TẮC BẤT BIẾN:**
> **Tiêu đề Text trên Thumbnail TUYỆT ĐỐI KHÔNG LẤY TÊN FILE SLUG** (Ví dụ cấm lấy `vietnam_nhung_mien_song_tap_03` hay `tap_03`).
> **BẮT BUỘC PHẢI DÙNG TIÊU ĐỀ NGHỆ THUẬT ĐÃ DUYỆT CỦA TẬP**.

### 3.1. Quy tắc Chân Dung Con Người Bản Địa (Human CC Portrait Focus Rule)
1. **Nguồn ảnh Wikimedia Commons / Wikipedia Creative Commons (CC)**:
   - Ưu tiên tìm kiếm và sử dụng hình ảnh chân dung con người bản địa của chính vùng địa lý đó từ Wikimedia Commons / Wikipedia với giấy phép mở (CC-BY, CC-BY-SA, Public Domain, CC0).
   - **Ưu tiên chân dung cô gái trẻ trên 18 tuổi hoặc phụ nữ bản địa trong trang phục truyền thống / sinh kế gắn liền với vùng đất**:
     * Tập 01 (Miền Tây): Cô gái nón lá, áo bà ba đi ghe chợ nổi Phong Điền Cần Thơ.
     * Tập 02 (Đồng Tháp Mười): Nụ cười thiếu nữ cấy lúa / thu hoạch sen, súng trên đồng nước nổi phản chiếu.
     * Tập 03 (Tứ Giác Long Xuyên): Thiếu nữ Chăm Islam / Khmer An Giang với khăn trùm Mat'ra và làng dệt Châu Đốc.
     * Tập 04 (Mũi Cà Mau): Người phụ nữ bơi xuồng giữa dòng sông phù sa và rừng ngập mặn.
     * Tập 05 (Tây Nguyên): Cô gái trẻ Kon Tum / Đắk Lắk trong trang phục thổ cẩm buôn làng cao nguyên Bazan.
     * Tập 06 (Duyên Hải Nam Trung Bộ): Thiếu nữ Chăm Ninh Thuận rạng rỡ trong lễ hội Katê tháp Chàm.
     * Tập 07 (Rạch Giá - Kiên Giang): Mẹ con người phụ nữ vá lưới trên cầu cảng Hàm Ninh, Phú Quốc.
     * Tập 08 (Sa Pa): Cô gái H'Mông trẻ tuổi thổi Đàn Môi trong trang phục thổ cẩm trên nương ruộng bậc thang.
2. **Bố cục Thumbnail Focus Chân Dung**:
   - Nhân vật chiếm vị trí chủ đạo phía bên phải khung hình (**45% – 55% diện tích canvas**), khuôn mặt rõ nét, ánh nhìn giàu cảm xúc, trang phục văn hóa nổi bật.
   - Chân dung được cắt tỉa, cân chỉnh màu sắc ấm áp và hòa quyện mượt mà (soft gradient feathering) vào background địa hình đặc trưng của tập.
   - Góc dưới bên phải ghi Attribution Credit chuẩn mực (tác giả, giấy phép CC, Wikimedia Commons).

### 3.2. Cấu trúc thị giác bắt buộc trên Thumbnail
1. **Brand Signature Pill**:
   - Vị trí: Góc trên bên trái khối chữ.
   - Màu nền: Vàng Gold hoàng gia `#E6A822` (`rgba(230, 168, 34, 0.94)`), chữ đen đậm.
   - Nội dung: `🌏  BIẾT ĐỊA LÝ TỪ BA TÔI  •  TẬP XX` (Ví dụ: `TẬP 03`).
2. **Tiêu đề chính (Punchy Title - Tối đa 2 dòng)**:
   - Dòng 1 (Trắng sáng `#FFFFFF`): Tên địa danh / Thực thể trung tâm (Ví dụ: `HUẾ`, `HÀ NỘI`, `MIỀN TÂY NAM BỘ`).
   - Dòng 2 (Vàng ấm `#FFE65A`): Mệnh đề linh hồn / Câu chuyện cốt lõi (Ví dụ: `MỘT KINH ĐÔ ĐẶT VÀO PHONG CẢNH`, `THÀNH PHỐ CỦA NHỮNG LỚP THỜI GIAN`).
   - **Quy tắc Typography**: Font `NotoSansDisplay-Bold` hoặc `NotoSerif-Bold`, đổ bóng drop shadow sắc nét, bảo toàn 100% từ ghép tiếng Việt (không ngắt đôi từ).
3. **Hero Visual & Khổ Phân Giải**:
   - Xuất bản chuẩn **2K QHD (2560x1440)** cho master và **HD (1920x1080)** cho thumbnail YouTube.
   - Có lớp gradient đen mờ (dark vignette overlay) từ cạnh dưới và bên trái để làm nổi bật typography mà không che khuất chân dung con người.

---

## 4. Cổng Kiểm Soát Xuất Bản YouTube (YouTube Packaging Gate)

1. **Tiêu đề Video (Title)**:
   - Chuẩn Mobile-First: Dưới 70 ký tự.
   - Cấu trúc: `[Tên Tập: Phụ Đề Cảm Xúc] | Biết Địa lý từ Ba tôi`
   - Ví dụ: `Huế: Một Kinh Đô Được Đặt Vào Phong Cảnh | Biết Địa lý từ Ba tôi` (62 ký tự).
2. **Mô tả (Description)**:
   - Đầy đủ 4 phần: Hook mở đầu, Mục lục Chapters bắt đầu bằng `00:00` qua đầy đủ các phần ($\ge 10$ chapters), Lời kêu gọi hành động CTA, Footer thương hiệu & hashtags `#BietDiaLyTuBaToi #DiaLyVietNam #NhungMienSong`.
3. **Phụ đề (Captions)**:
   - Đồng bộ file `.srt` với toàn bộ các mốc thời gian của $\ge 10$ phần.
   - Master video giữ ở định dạng Clean Footage để người xem trải nghiệm điện ảnh trọn vẹn.
4. **Tiêu Chuẩn Video Master 2K QHD (2560x1440)**:
   - File xuất bản tại `output/...master_2k.mp4`.
   - Độ phân giải chuẩn 2K QHD (2560x1440 @ 30fps) nội suy Lanczos, bitrate 16–24 Mbps để kích hoạt codec cao cấp `vp09` hoặc `av01` trên YouTube.

---

## 5. Quy Trình Nghiệm Thu Từng Phần (Part-by-Part Acceptance Gate)

Để tránh hiện tượng cẩu thả và dồn tải hệ thống, mọi tập phim dài $\ge 25$ phút phải tuân thủ nghiêm ngặt:
1. **Sản xuất cuốn chiếu**: Hoàn thiện kịch bản, âm thanh và footage của từng phần theo thứ tự `Part 01 -> Part 02 -> ... -> Part N`.
2. **Nghiệm thu độc lập từng phần**:
   - Mỗi phần phải có file video con `merged_part_XX.mp4` với thời lượng $\ge 120$s.
   - Âm lượng `volumedetect` đạt `mean_volume > -30 dB` và `max_volume > -12 dB`.
   - Visual-semantic match đạt $\ge 90\%$ (đúng thực thể địa danh trên khung hình).
3. **Tổng hợp Master**: Chỉ khi 100% các phần đều đạt Quality Gate mới tiến hành nối master, mix nhạc nền ambient, trích xuất phụ đề và xuất bản.

---

## 6. Hệ Thống Dual Quality Gate & Footage Metadata Signature (Chống False B-Roll & Chuẩn Hóa Nhịp Thở)

Để bảo đảm 100% video xuất bản không bao giờ bị lệch nội dung (như vụ việc dùng nhầm slide AI, máy gặt phương Tây hay xa lộ ban đêm), toàn bộ quy trình sản xuất kênh bắt buộc vận hành qua hệ thống **Dual Quality Gate**:

### 6.1. Script Quality Gate (Pre-Flight — Tiền Kỳ Trước Khi TTS & Dựng Video)
- **Công cụ thực thi**: `python3 -m production_hub.channels.ch_biet_dia_ly.quality_gates.channel_qg_cli script <path_to_script.md>`
- **6 Trục Kiểm Toán Bắt Buộc**:
  1. *Cấu trúc & Nhịp điệu*: $\ge 10$ phần, sub-3-minute, WPM ~155.
  2. *Dữ liệu địa lý*: Đầy đủ cao trình có đơn vị (`1.500m`, `450m`), cấu trúc 3 lớp (Tự nhiên - Thích ứng - Nhân sinh).
  3. *Chuẩn hóa TTS*: 100% số thô viết thành chữ, thẻ `<en>...</en>` cho tiếng Anh, tông giọng Cha - Con (`Ba ơi`, `con nhìn`).
  4. *Từ khóa Footage-Centric*: Từng phân cảnh phải có danh sách từ khóa tìm kiếm Pexels/Thư viện cụ thể.
  5. *Đặc tả Manim HUD*: Quy chuẩn Safe Zone Title Safe ($X \in [-5.4, 5.4], Y \in [-2.9, 3.1]$), kiến trúc 2-zone card.
  6. *Signature Outro*: Đúng nguyên văn *"Địa lý không chỉ nằm trên bản đồ. Nó nằm trong cách con người sống."*

### 6.2. Footage Metadata Signature Protocol (Hồ Sơ Nhận Diện Tư Liệu)
- Mọi video footage trong kho `selects/` hoặc `shots/` bắt buộc phải có hồ sơ Metadata Signature (`.meta.json` hoặc đăng ký catalog):
  * **Vùng miền (`region`)**: Xác định rõ 1 trong 8 vùng địa lý Việt Nam.
  * **Địa mạo (`landform_type`)**: `karst_mountain`, `mountain_pass`, `canyon_river`, `terraced_rice`, `valley_basin`, `tea_hills`, `alluvial_delta`.
  * **Thực thể thị giác (`visual_elements`)**: Ghi rõ các đối tượng xuất hiện trên khung hình.
  * **Quy tắc cấm kỵ (`forbidden_contexts`)**: Cấm tuyệt đối ghép video sông nước miền Tây vào kịch bản miền núi, cấm máy gặt phương Tây vào thung lũng lúa, cấm phố xá châu Âu vào cao nguyên.
- **Tính toán Semantic Matching Score**:
  * So khớp trực tiếp nội dung phân cảnh TTS với Metadata Signature của clip tương ứng.
  * Ngưỡng yêu cầu: Điểm khớp ngữ nghĩa trung bình $\ge 75\%$. Bất kỳ clip nào vi phạm B-roll cấm sẽ bị **VETO REJECTED** (Điểm = 0%).

### 6.3. Tiêu Chuẩn Phân Bổ Thời Lượng & Khoảng Nghỉ Khoa Học (Scientific Pause Distribution)
- **Tỷ Lệ Vàng Âm Thanh Tài Liệu**:
  * **$65\% - 75\%$ Lời Thoại (Voiceover Speech)**.
  * **$25\% - 35\%$ Khoảng Thở Thiên Nhiên & Nhạc Nền Ambient (Breathing/Music)**.
  * Tuyệt đối cấm kịch bản nói liên tục không ngừng nghỉ (Wall-to-wall speech $> 82\%$), gây mệt mỏi thính giác cho khán giả.
- **Tỷ Lệ Riêng Từng Phân Cảnh (Scene-Level Pause Budget)**:
  * Mỗi phân cảnh dài $45\text{s} - 150\text{s}$ phải phân bổ từ $15\text{s} - 40\text{s}$ cho cảnh quay flycam tự kể chuyện kết hợp nhạc nền nổi lên.
  * Cuối mỗi phân cảnh bắt buộc có khoảng đệm chuyển cảnh từ $2.5\text{s} - 4.5\text{s}$ để nhạc BGM un-duck (tăng từ -22dB lên -14dB) tạo khoảng lắng chiêm nghiệm.
- **Mật Độ Dấu Ngắt Nhịp Vi Mô**:
  * Trung bình 1 dấu phẩy ngắt nhịp sau mỗi $6 - 10$ từ.
  * Có từ 1 - 2 dấu chấm lửng (`...`) hoặc gạch nối dài (`—`) trong mỗi cảnh để định hướng giọng đọc trầm ngâm, từ tốn của người cha.

### 6.4. Audience Quality Gate (Post-Flight — Hậu Kỳ Trải Nghiệm Khán Giả)
- **Công cụ thực thi**: `python3 -m production_hub.channels.ch_biet_dia_ly.quality_gates.channel_qg_cli audience <video.mp4> --script <script.md> --srt <srt> --footage <footage_dir>`
- **6 Trục Kiểm Toán Trải Nghiệm Khán Giả (Thang điểm 100)**:
  1. *Khử lỗi màu & sọc tím (20 điểm)*: 0.00% purple scanlines, 0 frame lỗi.
  2. *Tính động của khung hình (15 điểm)*: 0 đoạn đứng hình tĩnh $> 3.0$ giây.
  3. *Khớp ngữ nghĩa tư liệu (25 điểm)*: Điểm trung bình $\ge 75\%$, 0 vi phạm Veto.
  4. *Chuẩn âm học EBU R128 (15 điểm)*: Integrated Loudness $-15.0 \pm 1.5$ LUFS, True Peak $\le -1.0$ dBTP.
  5. *Đồng bộ phụ đề Mobile (10 điểm)*: $\le 42$ ký tự/dòng, tốc độ đọc 12 - 22 CPS.
  6. *Phân bổ nhịp thở thực tế (15 điểm)*: Tỷ lệ thoại đo đạc $60\% - 78\%$, có đủ khoảng ngắt chuyển cảnh $1.5\text{s} - 5.0\text{s}$.
- **Phán quyết xuất bản**:
  * $\ge 85$ điểm & 0 blocker $\rightarrow$ **APPROVED FOR RELEASE**.
  * Dưới 85 điểm hoặc có lỗi cứng $\rightarrow$ **REJECTED (NEEDS REMAKE)**.

---

## 7. Cổng Kiểm Soát Chuyển Cảnh Phần (Section Title Card — TikTok-Inspired Chapter Breaks)

> **NGUYÊN TẮC: KHÔNG BAO GIỜ sử dụng text trắng trên nền đen (Plain White Text on Black) cho scene chuyển phần.**
> Mọi transition giữa các phần trong 1 tập PHẢI sử dụng `GeoSectionTitleCard` — component Manim premium với glassmorphism layout.

### 7.1. Kiến Trúc Thị Giác Section Title Card

Component render dưới dạng **transparent overlay** (.mov ProRes 4444), composit lên footage drone/flycam bên dưới.

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│    ┌──────────────────────────────────────────┐      │
│    │ ▐ PHẦN 03                               │      │
│    │ ▐                                       │      │
│    │ ▐ TỨ GIÁC LONG XUYÊN                   │      │
│    │ ▐ ──────────────────────                │      │
│    │ ▐ Vùng trũng tận cùng — nơi nước       │      │
│    │ ▐ không có đường chảy ra biển           │      │
│    └──────────────────────────────────────────┘      │
│              ▲ Drone / Flycam Footage Background     │
└─────────────────────────────────────────────────────┘
  ▲ Gold accent bar    ▲ Glassmorphism panel (opacity 82%)
```

### 7.2. Thành Phần Bắt Buộc Trên Mỗi Section Title Card
1. **Glassmorphism Panel**: Nền bán trong suốt (`fill_opacity >= 0.82`), viền bo góc (`corner_radius = 0.18`), nằm trọn trong Safe Zone.
2. **Gold Accent Bar**: Thanh dọc bên trái (`#E6A822`), chiều cao nhỏ hơn panel 0.5 đơn vị.
3. **Part Badge (Pill)**: Nhãn `PHẦN XX` trong nền gold bo tròn, font Bold, chữ tối.
4. **Main Title**: Font Bold, trắng sáng (`#F0F4F8`), tối đa 45 ký tự, không tràn viền.
5. **Cyan Divider**: Đường phân cách ngang (`#38BDF8`, `stroke_opacity = 0.6`), chiều dài 70% chiều rộng title.
6. **Subtitle**: Font thường, màu xám nhạt (`#94A3B8`), tối đa 100 ký tự, 1-2 dòng.

### 7.3. Animation Sequence (4.0s tổng)
| Thời điểm | Hành động                                 |
|-----------|-------------------------------------------|
| 0.0s      | Panel trượt lên từ dưới + accent bar mọc  |
| 0.6s      | Badge "PHẦN XX" fade in                   |
| 0.8s      | Title fade in + shift phải                |
| 1.2s      | Divider tạo từ trái → phải               |
| 1.5s      | Subtitle fade in                          |
| 2.0s      | Giữ nguyên (hold 1.5s)                   |
| 3.5s      | Toàn bộ fade out                          |
| 4.0s      | Kết thúc                                  |

### 7.4. Công Cụ Thực Thi
- **Component**: `manim_production_stack/packages/visual_kit/section_title_card.py`
- **Import**: `from manim_production_stack.packages.visual_kit.section_title_card import GeoSectionTitleCard, generate_section_scenes`
- **Render**: `python3 manim_production_stack/packages/visual_kit/render_section_titles.py --demo`
- **Docker Manim**: `manim -t --format mov -r 2560,1440 --fps 60 section_title_card.py DemoSectionCard`

### 7.5. Quy Tắc Cấm Kỵ
- ❌ Text trắng trên nền đen hoàn toàn (amateur, không phù hợp documentary premium).
- ❌ Font mặc định của hệ thống (phải dùng Be Vietnam Pro hoặc sans-serif).
- ❌ Section title tràn ngoài Safe Zone (kiểm tra bằng `is_within_safe_area()`).
- ❌ Composit không có footage bên dưới (luôn phải overlay lên cảnh drone/flycam transition).
