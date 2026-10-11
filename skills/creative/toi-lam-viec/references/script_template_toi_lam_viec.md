# Kịch bản video ZENPHAM — [Tiêu Đề Tập Video: Ngắn Gọn, Kích Thích Tò Mò]

**KÊNH**: ZENPHAM  
**SERIES**: TÔI LÀM VIỆC  
**NGƯỜI DẪN**: Zen (Kỹ sư AI thực thi điềm tĩnh, chia sẻ từ hiện trường)  
**ĐỊNH DẠNG**: 16:9 Landscape (2560x1440 2K QHD) / Hoặc 9:16 Portrait (1440x2560)  
**THỜI LƯỢNG MỤC TIÊU**: ~8–12 phút (8–12 scenes)  
**NHẠC NỀN**: `quiet_room_glow.mp3` hoặc `velvet_after_hours.mp3` (kho nhạc chính chủ tại `assets/background_music/living - lifestyle/`, gain -22dB)

---

## TỔNG QUAN NỘI DUNG (THE 4 QUADRANTS)
- **Câu hỏi trung tâm**: [Câu hỏi kỹ thuật / toán học cốt lõi]
- **Tình huống thực tế (The Bug/Context)**: [Một ca debug, nghẽn tải, hoặc sự cố kiến trúc thực tế ngoài hiện trường]
- **Lớp bản chất toán học (The Manim Layer)**: [Công thức, thuật toán hoặc phân phối xác suất cần trực quan hóa 2K]
- **Chiêm nghiệm kỹ nghệ (The System Insight)**: [Bài học đánh đổi khách quan, không rao giảng đạo đức]

## VOCAL SCRIPT CONTRACT — VI–EN TRONG MỘT UTTERANCE & TERM COOLDOWN

- Mỗi lời thoại là một câu/mạch tiếng Việt tự nhiên; thuật ngữ tiếng Anh nằm tại đúng vị trí ngữ nghĩa và giữ nguyên spelling chuyên nghiệp.
- **Quy tắc Giãn cách Thuật ngữ (Term Cooldown)**: Mỗi thuật ngữ tiếng Anh xuất hiện tối đa 1 lần/câu và tối đa 2 lần/cảnh. Lần 2 trở đi bắt buộc dùng đại từ thay thế tiếng Việt (`thuật toán này`, `mô hình trên`, `bộ lọc đó`).
- **Đa dạng hóa cầu nối**: Cấm lặp `tức là`, `nói cách khác` (tối đa 1 lần/cảnh).
- **Cấm Bare English Term đầu câu**: Dùng neo ngữ pháp Việt đúng nghĩa: `mô hình LLM`, `phương pháp PCA`, `hàm Softmax`, `độ calibration`, `chỉ số MSE`, `thuật toán Backpropagation`, `quá trình training`.
- **Cấm dấu ngoặc kép `"string"` và dấu gạch ngang `- `**: Viết văn bản xuôi tự nhiên để TTS không đọc thành "quote" hay "dấu trừ".
- **Cấm mở đầu cliché**: Tuyệt đối không dùng *"Có bao giờ bạn tự hỏi..."*, *"Bạn có biết rằng..."*. Chọn 1 trong 5 Opening Archetypes.
- **Cấm kết thúc sáo rỗng**: Tuyệt đối không dùng *"Đạo làm nghề..."*, *"người thợ thủ công số"*. Chọn 1 trong 5 Ending Archetypes + cầu nối tập kế.
- Sau rewrite cuối, dựng cue sheet và chạy `tts_code_switch_risk.py` và `script_audience_gate.py`.

---

## CHI TIẾT CÁC PHÂN CẢNH (SCENES)

### Đoạn 1: Mở đầu kỹ thuật (Opening Archetype 1–5, CẤM 'Có bao giờ bạn tự hỏi')
- **Hình ảnh**: [Đồ họa Manim 2K hoặc màn hình terminal hiện trường, biểu diễn trực diện sự cố/nghịch lý kỹ thuật]
- **Manim Blueprint**: Hero Geometry rõ ràng (Axes, Vector, Matrix), tone Obsidian `#0c0d12` + Neon Cyan/Amber.
- **Lời thoại**: "..."
- **Ghi chú âm thanh**: Ambient Synth & Piano sâu lắng, âm thanh bàn phím cơ nhẹ 2 giây đầu.

### Đoạn 2: Sự cố thực tế từ hiện trường hệ thống
- **Hình ảnh**: [Màn hình dòng lệnh Linux terminal, log chạy cuộn nhanh, thông báo nghẽn tài nguyên hoặc deadlock]
- **Lời thoại**: "..."

### Đoạn 3: Đồ họa toán học Manim (The Mechanism — Vi cơ chế)
- **Hình ảnh**: [Hoạt họa Manim 2K hiển thị công thức LaTeX và trực quan hóa vi cơ chế toán học]
- **Manim Class**: `YourSceneName` (Xem mẫu tại `references/manim_templates.py`)
- **Mô tả đồ họa**: Đường cong hàm mất mát, trường vector hoặc phân phối xác suất chuyển động mượt mà.
- **Lời thoại**: "..."

### Đoạn 4: Phản trực giác giữa con người và máy móc
- **Hình ảnh**: [Manim mô phỏng không gian trạng thái hoặc luồng dữ liệu biến đổi]
- **Lời thoại**: "..."

### Đoạn 5: Đồ họa phân tích chuyên sâu (The Geometric Insight)
- **Hình ảnh**: [Manim hoạt họa đa vùng (4-Zone Staging), biến đổi hình học chứng minh tính chất bất biến]
- **Lời thoại**: "..."

### Đoạn 6: Đánh đổi kỹ nghệ & Thử nghiệm thực tế (Production Benchmark & Trade-offs)
- **Hình ảnh**: [Biểu đồ đo lường Throughput / Latency P99 hoặc kiến trúc bộ nhớ phần cứng GPU/RAM]
- **Lời thoại**: "..."

### Đoạn 7: Kiến trúc hệ thống & Giới hạn thực nghiệm (System Architecture & Bounds)
- **Hình ảnh**: [Sơ đồ khối tinh giản, các vector luồng dữ liệu được nén lại gọn gàng trong không gian tối ưu]
- **Lời thoại**: "..."

### Đoạn 8: Chiêm nghiệm kỹ nghệ (The Quiet Insight)
- **Hình ảnh**: [Mô hình hình học ổn định, các hạt dữ liệu chuyển động trơn tru không còn xung đột]
- **Lời thoại**: "..."

### Đoạn 9: Kết luận đĩnh đạc (Ending Archetype 1–5, CẤM 'Đạo làm nghề')
- **Hình ảnh**: [Cỗ máy toán học hoàn tất chu kỳ, trạng thái cân bằng tuyệt đối phát sáng nhẹ nhàng]
- **Lời thoại**: "..."

### Đoạn 10: Outro & Cầu nối tập kế tiếp (Next Episode Bridge)
- **Hình ảnh**: [Thẻ cầu nối tập kế: Hero 2K Thumbnail tập tiếp theo + Header Badge 'TẬP TIẾP THEO' + Capsule Công thức Toán]
- **Lời thoại**: "..."

---

## THÔNG TIN XUẤT BẢN YOUTUBE (SEO & METADATA)

- **Tiêu đề YouTube (< 60 ký tự)**:  
  `[Hook Kích Thích Tò Mò] — [Chủ đề] | Zenpham`
- **Tags**:  
  `Zenpham, Tôi Làm Việc, AI Engineering, Machine Learning, Deep Learning, Lập Trình, Khoa Học Máy Tính, Python, Manim`
- **Pinned Comment**:  
  > *"Khi đối mặt với bài toán tối ưu này trong thực tế... [câu hỏi kích thích thảo luận kỹ thuật]. Hãy để lại góc nhìn của bạn nhé."*

END_TITLE: "ZENPHAM — Tôi Làm Việc: [Tên Tập]"
