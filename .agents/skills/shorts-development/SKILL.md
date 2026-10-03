---
name: shorts-development
description: Quy chuẩn sản xuất YouTube Shorts 9:16 (2K QHD 1440x2560 @ 60fps) cho kênh ZENPHAM. Tự động chuyển hóa các phân đoạn của video dài thành bộ Shorts độc lập tương ứng, tái sử dụng động học toán học Manim 3Blue1Brown, áp dụng NLP Open Loop để chuyển đổi người xem sang Long-form Video qua tính năng YouTube Related Video, tích hợp bộ kiểm toán kép SQG (Structural Quality Gate) và AQG (Audio Quality Gate).
---

# Kỹ Năng Sản Xuất YouTube Shorts Kỹ Nghệ AI (Shorts Development Skill)

Tài liệu đặc tả toàn diện quy trình sản xuất **YouTube Shorts Kỹ Nghệ Cao (9:16 Vertical 2K QHD)** cho các series "Tôi Làm Việc" và "Reality Decode" của kênh ZENPHAM.

---

## 1. Triết Lý Cốt Lõi & Nguyên Tắc 1 Phần = 1 Short

- **Ánh Xạ Nội Dung 1:1 (Section-to-Short Mapping)**:
  Mỗi tập video dài gồm $N$ phân đoạn kiến thức (Thematic Sections). Pipeline tự động sản xuất đúng $N$ Shorts độc lập. Mỗi Short đại diện cho một mâu thuẫn nhận thức (cognitive dissonance) hoặc một lát cắt toán học sâu sắc của phân đoạn đó.
- **Tái Sử Dụng Visual Đỉnh Cao (3Blue1Brown Reframing & Native 9:16 Render)**:
  Không dùng video kho (stock footage) rẻ tiền hay hoạt ảnh nhảm nhí. Tái sử dụng trực tiếp các mô hình Manim toán học đỉnh cao từ bản dài, nhưng được **lập trình và render độc lập 100% trong khung dọc 9:16 (1440x2560)**.
  **CẤM TUYỆT ĐỐI NHÚNG VIDEO (Zero Video-in-Video Embedding)**: Không tạo card nền tĩnh bằng PIL rồi dùng FFmpeg overlay video 16:9 ngang vào cửa sổ ở giữa (thủ phạm gây lỗi sọc tím/xanh, hỏng pixel format và làm co rúm diện tích hiển thị). Toàn bộ khung dọc phải là sân khấu điện ảnh của Manim!
- **NLP Open Loop & Chuyển Đổi Về Video Dài (Related Video Link)**:
  Shorts không phải là sản phẩm phụ tách rời, mà là **Phễu Chuyển Đổi Tri Thức (Knowledge Funnel)**. Trong 5–7 giây cuối, áp dụng kỹ thuật NLP Open Loop để neo sự tò mò chưa có lời giải đáp và hướng dẫn người xem bấm vào nút **"Video liên quan" (Related Video)** bên dưới tiêu đề.

---

## 2. Kiến Trúc Thị Giác 3 Tầng Điện Ảnh (3-Zone Vertical Cinema Stage)

Độ phân giải chuẩn: **$1440 \times 2560$ (9:16 Vertical 2K QHD @ 60fps)**.

```
┌─────────────────────────────────────────────────────────────┐  Y = +8.0
│  TẦNG 1: HOOK QUESTION & HEADLINE BANNER (25%)              │
│  - Y từ +3.5 đến +6.8                                       │
│  - Tag series: [TÔI LÀM VIỆC · TẬP 01]                     │
│  - Câu hỏi Hook giật gân, chữ Title Case, viền phát sáng    │
│  - Tuyệt đối an toàn: Y <= 6.8 (tránh icon camera/search)   │  Y = +3.5
├─────────────────────────────────────────────────────────────┤
│  TẦNG 2: HERO MATHEMATICAL ANIMATION (50%)                  │
│  - Y từ -3.0 đến +3.0                                       │
│  - Vùng trung tâm thị giác, không gian tối Obsidian #080a0f │
│  - Động học Manim 3Blue1Brown chuyển động mượt mà 60fps    │
│  - Tọa độ căn giữa tuyệt đối theo trục X = 0                │  Y = -3.0
├─────────────────────────────────────────────────────────────┤
│  TẦNG 3: SUBTITLE & NLP CURIOSITY BRIDGE (25%)              │
│  - Y từ -6.2 đến -3.2                                       │
│  - Phụ đề Kinetic Karaoke hiển thị theo từng từ             │
│  - Thẻ điều hướng: "Xem chứng minh ở video liên kết 👇"     │
│  - VÙNG CẤM: Y < -6.2 (nơi YouTube đặt Avatar/Title/Sound) │  Y = -8.0
└─────────────────────────────────────────────────────────────┘
```

---

## 2.5. Quy Chuẩn Bắt Buộc: Nghiêm Cấm Hoàn Toàn Card Text (Zero Card Text Policy)

**TUYỆT ĐỐI NGHIÊM CẤM DÙNG CARD TEXT (RoundedRectangle, Bounding Box, Hộp Chứa Chữ)** trong toàn bộ các phân cảnh Manim 9:16 và kịch bản Shorts.

### Lý do kỹ thuật đào thải Card Text:
1. **Lỗi Tràn Viền & Vỡ Bố Cục (Layout & Overflow Defects)**: Khi độ dài từ, nội dung dịch thuật hoặc cỡ chữ biến thiên, text tràn ra ngoài viền hộp hoặc để lại khoảng đệm mất cân đối nghiêm trọng.
2. **Lỗi Ràng Buộc Cứng Nhắc (Rigid Geometry vs Cinematic Fluidity)**: Khung hộp tĩnh biến hoạt cảnh toán học điện ảnh 3Blue1Brown thành các "slide thuyết trình" thô cứng, phá hủy hoàn toàn nhịp điệu chuyển động liên tục.
3. **Lỗi Cắt Xén Font (Ascender/Descender Glyph Clipping)**: Pango/FreeType khi render font trong khung hình học kín dễ bị cắt chân chữ hoặc va chạm viền (stroke).
4. **Nhiễu Thị Giác (Visual Noise)**: Đường viền stroke và màu nền hộp cạnh tranh trực tiếp với các đường cong hàm số, vector và không gian hình học.

### 5 Kiến Trúc Thay Thế Khi Layout Text Lên Manim:
1. **Floating Kinetic Typography (Chữ Động Không Gian Tự Do)**:
   - Text đặt trực tiếp trong không gian tối Obsidian (`#080A0F`), không có bất kỳ hình chữ nhật hay đường viền đóng kín nào.
   - Xuất hiện mượt mà bằng vector chuyển dịch (`FadeIn(..., shift=UP * 0.25)`) hoặc hiển thị theo từng từ (`vi_text_words`).
2. **Geometric Relative Anchoring (Điểm Neo Hình Học)**:
   - Định vị tương đối với đối tượng toán học qua các toán tử không gian `.next_to()`, `.align_to()`.
   - Sử dụng điểm neo tinh tế (`Dot(radius=0.04)`) và đường chỉ dẫn mảnh (`Line(stroke_width=1.0, stroke_opacity=0.4)`) nối trực tiếp nhãn vào tọa độ cực trị, vector tiếp tuyến hay trị riêng.
3. **Dynamic Text Wrapping & Safe Zone Clamping**:
   - Tự động ngắt dòng theo ký tự (`vi_text(..., max_width=...)`) thay vì ép vào hộp.
   - Bắt buộc tuân thủ tọa độ an toàn: $X \in [-3.8, +3.1]$ (loại trừ 15% mép phải YouTube action buttons), $Y \in [-6.2, +6.8]$.
4. **Minimalist Duotone Title + Formula Hierarchy (Phân Cấp Thị Giác Hai Tông Màu)**:
   - Tạo phân cấp thị giác bằng kích thước và nhiệt độ màu thay vì vẽ khung: Tag Series (Gold `#F59E0B`, chữ hoa, tracking rộng); Tiêu đề Hook (Cyan `#00F0FF` / White `#F8FAFC`, Bold); Công thức LaTeX (`MathTex`) đồng bộ màu với đường cong toán học tương ứng.
5. **Soft Ambient Falloff (Bóng Mờ Mịn, Tuyệt Đối Không Viền Cứng)**:
   - Nếu bắt buộc tạo độ tương phản trên nền chuyển động phức tạp, chỉ dùng bóng mờ tỏa mịn (Gaussian radial blur) hòa tan tự nhiên vào nền `#080A0F`, không có viền stroke hay góc bo cứng.

---

Mọi video Short trước khi kết xuất thành phẩm bắt buộc phải vượt qua kiểm toán kép:

### A. SQG (Structural Quality Gate for Shorts 9:16)
1. **Right-Rail Safe Zone (Loại trừ 15% lề phải)**:
   - Trong tọa độ Manim 9:16 ($X \in [-4.5, +4.5]$), mép phải $X > +3.1$ là nơi YouTube đặt các nút tương tác: Like, Dislike, Comment, Share, Sound Remix.
   - **Quy tắc**: Không có bất kỳ text, công thức LaTeX, hay điểm neo chính nào được vi phạm $X > 3.1$.
2. **Bottom UI Safe Zone (Tránh che lấp phía dưới)**:
   - Phía dưới $Y < -6.2$ bị che bởi thanh tiến trình, tiêu đề Short, Avatar kênh và nút bấm "Video liên quan".
   - **Quy tắc**: Mọi phần tử thị giác phải kết thúc ở $Y \ge -6.2$.
3. **Pacing & Hook Validation (Quy Chuẩn Hook Hội Đồng Thẩm Định)**:
   - **00:00 – 03.00s**: Bắt buộc xuất hiện Paradox Hook Banner và hình ảnh gây tò mò thị giác ngay từ frame đầu tiên (0% màn hình đen mờ dần).
   - **CẤM HOOK QUÁ NGẮN / MỜ NHẠT**: Hook text bắt buộc hiển thị trên Tầng 1 tối thiểu **$2.5\text{s} - 3.5\text{s}$**, câu từ sắc bén gieo nghịch lý nhận thức, cấm lướt qua dưới 2s làm khán giả không kịp đọc.
   - **Thời lượng tổng**: Nằm nghiêm ngặt trong khoảng $45.0\text{s} - 55.0\text{s}$.

### B. AQG (Audio Quality Gate for Shorts — Diệt Sạch Lỗ Câm & Chuẩn V0-Sense)
1. **Integrated Loudness**: Chuẩn YouTube Shorts là **$-14.0 \pm 0.5\text{ LUFS}$** (năng động hơn bản dài $-14.5\text{ LUFS}$).
2. **True Peak**: Nghiêm ngặt $\le -1.0\text{ dBFS}$ để chống vỡ tiếng khi YouTube nén lại qua codec Opus.
3. **DIỆT SẠCH LỖ HỔNG CÂM (Zero Audio Silence Holes)**:
   - **CẤM CÂM ĐẦU VÀ CUỐI**: CẤM TUYỆT ĐỐI hiện tượng 2–3s đầu bị câm tiếng (mất hook âm thanh) hoặc 2–3s cuối bị câm (cụt câu kêu gọi Related Video). Lời thoại bắt buộc bắt đầu từ $0.20\text{s} - 0.40\text{s}$ và kết thúc sát frame cuối.
   - **KHÔNG KHOẢNG CÂM CHẾT**: Tuyệt đối không có bất kỳ khoảng lặng chết nào $\ge 0.35\text{s}$ trong suốt video Short.
4. **Tiêu chuẩn Gold TTS Duy Nhất (TTS V0-Sense trên GPU CUDA)**: 100% kịch bản Shorts bắt buộc xử lý qua `tts_v0_sense_synthesizer.py`. Giữ nguyên 100% kịch bản thuần Việt tự nhiên, bọc `<en>` cho thuật ngữ kỹ thuật, điều biến temper $0.58$ cho Hook và $0.54$ cho toán học, hậu kỳ 5-Stage Studio Vocal Mastering Chain (48kHz Stereo). Nhạc nền ambient lo-fi được tự động nén ducking $-18\text{ dB}$ khi có giọng nói.

---

## 4. Quy Chuẩn Kịch Bản NLP Open Loop

Mỗi kịch bản Short phải cấu trúc thành 3 đoạn chuẩn mực:
- **Đoạn 1 (0–10s): The Paradox Hook**  
  Tạo ra một mâu thuẫn trực giác (ví dụ: *"Tung đồng xu 1 tỷ lần toàn ra sấp, bạn tin đồng xu lệch hay vũ trụ sắp đặt?"*).
- **Đoạn 2 (10–42s): The Mathematical Spotlight**  
  Giải thích bản chất kỹ thuật/toán học qua Manim 3Blue1Brown (Laplace, Bayes, Softmax). Khẳng định cỗ máy không hành động ngẫu nhiên mà tính toán niềm tin số học.
- **Đoạn 3 (42–50s): The NLP Open Loop & Conversion**  
  Mở ra một câu hỏi lớn hơn và kêu gọi hành động:  
  *"Khám phá toàn bộ phép chứng minh toán học trong video dài liên kết ngay bên dưới tiêu đề nhé."*

---

## 5. Danh Mục Đầu Ra Chuẩn Của Một Short

Mỗi Short khi sản xuất xong bao gồm 4 tệp:
1. `script.md`: Kịch bản phân cảnh chi tiết có mốc thời gian và lời thoại TTS.
2. `scene_short.py`: Mã nguồn ManimCE 9:16 ($1440 \times 2560$).
3. `short_master_2k60.mp4`: Video hoàn thiện đã mixdown âm thanh chuẩn $-14.0\text{ LUFS}$.
4. `metadata_seo.json`: Tiêu đề (< 70 ký tự), mô tả, tags, và ID video dài liên kết (`related_video_id`).
