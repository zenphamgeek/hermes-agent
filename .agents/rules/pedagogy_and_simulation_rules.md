# Quy Chuẩn Sư Phạm & Mô Phỏng Vật Lý Trong Kịch Bản Manim (Pedagogy & Simulation Rules)

> **TRIẾT LÝ SỐNG CÒN (CORE AXIOM):**
> *"Nếu không thể giải thích cho một người bình thường hiểu bằng trực giác hình học và vật lý đời thường, điều đó chứng tỏ chúng ta chưa thực sự hiểu bản chất kỹ nghệ."*
> Mọi chủ đề AI Deep-tech (dù khó đến đâu: RoPE, YaRN, KV Cache, Mamba SSM, FlashAttention, SwiGLU, Quantization) đều **BẮT BUỘC PHẢI ĐƯỢC HÌNH TƯỢNG HÓA** bằng mô hình trực quan trước khi viết công thức đại số.

---

## 1. Nguyên Tắc 1: Hình Học Trước Đại Số (Geometry Before Algebra)

1. **Tuyệt đối không đưa công thức LaTeX trước khi đưa mô hình trực quan**: Người xem phải nhìn thấy sự quay của vector, sự lan truyền của sóng, hay sự co giãn của không gian trước khi phương trình xuất hiện.
2. **Tiêu trừ Slide-Deck Laziness (Bệnh lười vẽ hộp văn bản)**:
   - Cấm tạo 3–4 khối chữ nhật `RoundedRectangle` chứa văn bản gạch đầu dòng như bài thuyết trình PowerPoint.
   - Phân cảnh kỹ thuật phải lấy thực thể toán học/vật lý động làm trung tâm:
     - Trục tọa độ, mặt phẳng phức (`Axes`, `ComplexPlane`)
     - Sóng tuần hoàn, đồ thị hàm số động (`FunctionGraph`, `sin`, `cos`)
     - Vòng tròn lượng giác, kim quay, góc pha (`Circle`, `Angle`, `Vector`, `Arrow`)
     - Ma trận / Tensor heatmap đổi màu theo thời gian thực (`Matrix`, `Square` grid)
     - Bộ theo dõi chuyển động vật lý (`ValueTracker`, `always_redraw`, `add_updater`)

---

## 2. Nguyên Tắc 2: Ẩn Dụ Đời Thực Neo Giữ Tư Duy (Metaphor Anchoring)

Mỗi phân cảnh kỹ thuật phức tạp bắt buộc phải gắn liền với ít nhất 1 hình tượng vật lý đời sống:

| Khái niệm AI Trừu Tượng | Ẩn Dụ Vật Lý / Đời Thường Bắt Buộc | Trực Quan Hóa Manim |
| :--- | :--- | :--- |
| **RoPE (Rotary Position Embedding)** | Bản giao hưởng 64 cặp bánh răng; Mặt đồng hồ đo bước sóng $\lambda$ (kim phút quay nhanh, kim giờ quay chậm). | 3 mặt đồng hồ kim quay tốc độ góc khác nhau + đồ thị sóng $y = \sin(kx - \omega t)$. |
| **YaRN (Context Extension)** | Chiếc thước kẻ cao su co giãn đàn hồi; Giữ nguyên vạch milimet vi mô, kéo dài bước sóng vĩ mô. | Thước đo phân tầng 3 dải màu (Hồng: giữ nguyên, Vàng: hòa trộn, Xanh: nội suy). |
| **Position Interpolation** | Nén thô bạo cả cuốn sách dày vào chiếc thước kẻ cũ $\to$ Gây chứng "cận thị cục bộ". | Các vạch chia dính chặt vào nhau, chữ mờ nhòe. |
| **Attention Sink** | Bồn trũng nước hút phần áp suất dư thừa; Chiếc phao neo giữ thăng bằng cho hàm Softmax. | 4 cột đầu tiên phát sáng cyan hút trọn 40%+ trọng số, ghìm phẳng đường cong VRAM. |
| **KV Cache & Eviction** | Cuốn sổ tay ghi chép trí nhớ tạm; Bức tường bộ nhớ VRAM 64GB; Chiếc xô nước tràn. | Đồng hồ đo VRAM tăng vọt chạm ngưỡng trần đỏ, sau đó gạn lọc cửa sổ trượt. |
| **Attention Mechanism** | Ngọn đèn pin soi rọi vào các từ khóa trong đêm tối ngữ cảnh; Chiếu vuông góc giữa 2 vector. | Chùm sáng quét qua chuỗi token, tia sáng hội tụ. |
| **Gradient Descent** | Người leo núi mù dò dẫm trong đêm tối sương mù trên rặng Andes bằng độ dốc bàn chân. | Quả cầu lăn trên mặt cong paraboloid 3D tìm điểm cực tiểu. |
| **LayerNorm / RMSNorm** | Lát cắt ngang qua khối Rubik tensor; Con lắc điều hòa cân bằng biên độ. | Vector co giãn chuẩn hóa biên độ về mặt cầu đơn vị. |

---

## 3. Nguyên Tắc 3: Khung Dắt Tay Chỉ Lối 4 Tầng Nhận Thức (4-Stage Scaffolding)

Mọi phân cảnh trong kịch bản phải được tổ chức theo cấu trúc sư phạm 4 bước:

1. **Bước 1: Nghịch lý / Triệu chứng thực tế (The Paradox / Symptom)**:
   - Mở đầu bằng một câu hỏi hóc búa, một hiện tượng đổ vỡ bất ngờ mà người bình thường cũng tò mò.
   - *Ví dụ*: *"Phép xoay toán học vẫn đúng ở mọi con số, tại sao đưa một cuốn tiểu thuyết 32K token vào thì mô hình lại bắt đầu nói nhảm?"*
2. **Bước 2: Ẩn dụ đời thường (The Toy Physical Model)**:
   - Dùng hình tượng bình dân để não bộ người xem lập tức có "điểm tựa" tư duy.
   - *Ví dụ*: *"Hãy nhìn vào các kim đồng hồ: kim giây quay tít bắt nhịp từng giây, kim giờ quay chậm chạp đếm dòng chảy thời gian."*
3. **Bước 3: Mổ xẻ cơ chế Manim (Visual Mechanics)**:
   - Manim hiển thị chính xác các vector, sóng, góc quay và sự chuyển dịch tham số.
   - Lời thoại đồng bộ từng chuyển động, không nói nhanh hơn hình ảnh.
4. **Bước 4: Tác động kỹ nghệ thực tế (Engineering Reality & Impact)**:
   - Chốt lại bằng con số cụ thể và giá trị thực tế: tiết kiệm từ 60GB xuống 4.2GB VRAM, xử lý 4 triệu token không suy chuyển.

---

## 4. Nguyên Tắc 4: Khử Thuật Ngữ Rỗng (Jargon-to-Metaphor Bridging)

1. **Cấm dùng thuật ngữ chuyên môn cộc lốc**: Mọi thuật ngữ trừu tượng cao khi xuất hiện phải có **lời giải nghĩa trực quan bằng tiếng Việt giản dị đi kèm ngay bên cạnh**.
   - *Sai*: "Sliding window eviction làm perplexity vọt lên vô cực."
   - *Đúng*: "Khi xóa token đầu tiên khỏi bộ nhớ đệm, điểm perplexity — tức độ bối rối, hoang mang khi đoán từ tiếp theo của mô hình — lập tức vọt lên vô cực."
2. **Ngưỡng kiểm định**: Nếu trong một phân cảnh có từ 2 thuật ngữ chuyên môn trở lên không có lời bắc cầu trực quan $\to$ **Quality Gate đánh lỗi HIGH DEFECT**.

---

## 5. Nguyên Tắc 5: Dẫn Hướng Mắt Nhìn Chủ Động (Dynamic Eye Guidance)

1. Người xem không chuyên rất dễ mất phương hướng khi nhìn vào một màn hình có nhiều đối tượng toán học.
2. **Quy tắc đồng bộ mắt nhìn**:
   - Khi giọng đọc nhắc tới đại lượng nào, đại lượng đó trên Manim **BẮT BUỘC PHẢI ĐƯỢC CHỈ DẪN**:
     - Khoanh tròn viền sáng: `Circumscribe(mobject, color=ZenPalette.GOLD)`
     - Nhấp nháy phát quang: `Indicate(mobject)` hoặc `Flash(mobject)`
     - Mũi tên chỉ điểm: `GrowArrow(arrow)` hoặc `PointCallout`
     - Chuyển màu tiêu điểm: `Transform` từ màu phụ sang màu Neon Hero (`ZenPalette.CYAN` hoặc `ZenPalette.GOLD`).
   - Cấm tuyệt đối để một biểu đồ đứng yên thụ động suốt 40 giây khi giọng đọc đang phân tích các thành phần con của nó.

---

## 6. Nguyên Tắc 6: Phân Rã Khối Dưới 3 Phút (Sub-3-Minute Modular Chunking)

1. **Tuyệt đối cấm xử lý Monolithic (Khối nguyên khối)**:
   - Một tập Masterclass kéo dài 8–10 phút không bao giờ được viết kịch bản, lập trình Manim, hoặc kiểm định như một tệp duy nhất không phân rã.
2. **Quy tắc cấu trúc 3 Phần (3 Acts / Part Groups A, B, C)**:
   - Mỗi tập phim bắt buộc được phân bổ theo 3 Hồi rõ ràng:
     - **Phần 1 (Part Group A — Khởi nguyên & Triệu chứng)**: Thường gồm Scenes 1 & 2 (~120s – 180s). Đập tan ngộ nhận ban đầu, xây dựng trực giác đời thực.
     - **Phần 2 (Part Group B — Trọng tâm Cơ chế Toán học)**: Scene 3 (~80s – 100s). Mổ xẻ sâu thuật toán lõi, phương trình và mô hình cơ học.
     - **Phần 3 (Part Group C — Thực nghiệm, Đánh đổi Kỹ nghệ & Tổng hợp Kiến trúc)**: Scenes 4, 5, 6 (~180s – 240s). Đo lường thực nghiệm, phân tích đánh đổi phần cứng (VRAM/Speed), tổng hợp kiến trúc hệ thống và mở ra đường chân trời bài toán tiếp theo (Ending Archetypes, CẤM 'Đạo làm nghề').
3. **Giới hạn thời lượng từng phân cảnh (Scene Limit $\le 180$s)**:
   - Mọi phân cảnh (Scene / Chapter) thành phần **bắt buộc có thời lượng $\le 3$ phút (180 giây)**, tối ưu nhất trong khoảng **60s – 95s**.
4. **Mục đích chiến lược**:
   - **Tập trung ngữ cảnh (Context Focus)**: Agent khi viết kịch bản minh họa và code Manim chỉ tập trung vào một phạm vi hẹp, loại trừ hoàn toàn ảo giác (hallucination) và trôi dạt (drift).
   - **Gia công mỹ thuật cao cấp (Artisanal Detailing)**: Đảm bảo từng giây hoạt ảnh đều có nhịp phách rõ ràng (Parts/Beats), không bị loãng nội dung hay thiếu hoạt ảnh dẫn đến đứng hình.
   - **Kiểm định cục bộ (Granular Quality Gate)**: Kiểm tra freezedetect $\le 4.0$s, safe padding và typography độc lập cho từng Scene trước khi ráp nối.
   - **Tiết kiệm tài nguyên (Caching & Fail-fast)**: Render từng Scene độc lập qua Docker; nếu phát hiện lỗi ở Scene nào, chỉ cần sửa và render lại đúng Scene đó trong vài chục giây thay vì kết xuất lại toàn bộ video 8–10 phút.
