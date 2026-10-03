---
name: youtube-to-manim
description: "Phân tích và chuyển hóa kịch bản từ 1 URL YouTube thành kịch bản phân cảnh Manim (2K QHD, Median Math x ZenPham Digital Craftsmanship) sử dụng hoàn toàn cụm mô hình AI chạy local trên ThinkPad P15 (NVIDIA Quadro RTX 5000 16GB VRAM)."
version: 1.0.0
author: ZENPHAM & Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [youtube, manim, video-analysis, local-llm, lm-studio, rtx-5000, splay-tree, toi-lam-viec, manim-production]
    related_skills: [manim-production, toi-lam-viec, manim-video, pexels-visual-search]
---

# YouTube to Manim Production Skill — Local AI Pipeline on P15

Skill này cung cấp quy trình tự động hóa phân tích nội dung từ bất kỳ **URL YouTube** nào (bài giảng thuật toán, toán học, kiến trúc AI/phần mềm) và chuyển thể thành **kịch bản phân cảnh hoạt họa Manim chuẩn 2K QHD** theo triết lý "Tôi Làm Việc" (3Blue1Brown × Median Math × ZenPham Craftsmanship), vận hành 100% bằng **các mô hình AI cục bộ chạy trên ThinkPad P15 (Quadro RTX 5000 16GB VRAM)**.

> **Đặc tả kỹ thuật chính thức**: Xem toàn bộ kiến trúc và hợp đồng kỹ thuật tại [MANIM_SKILLS_MASTER_SPECIFICATION.md](../../../docs/specs/MANIM_SKILLS_MASTER_SPECIFICATION.md).

---

## 1. Bản Đồ Mô Hình AI Local Trên Máy P15 (Quadro RTX 5000 16GB VRAM)

Hệ thống P15 sở hữu GPU **NVIDIA Quadro RTX 5000 (16GB VRAM GDDR6)** kết hợp LM Studio trên bare-metal và các thư viện tăng tốc inference (CTranslate2, PyTorch CUDA, Docker).

### Bảng phân vai cụm mô hình cục bộ (Local Model Roster):

| Công đoạn Pipeline | Mô hình Local | Định dạng / Vị trí | Bộ nhớ VRAM | Nhiệm vụ cụ thể |
| :--- | :--- | :--- | :--- | :--- |
| **1. Audio Transcription & ASR** | `Systran/faster-whisper-small` & `wav2vec2-base-vi-vlsp2020` | CTranslate2 / PyTorch (`~/.cache/huggingface/hub`) | ~1.2 GB (hoặc CPU INT8) | Tách lời thoại tiếng Việt/Anh từ audio YouTube, trích xuất timestamp từng từ (word-level alignment). |
| **2. Audio Stem Isolation** | `adefossez/HTDemucs` | TorchScript (`~/.cache/huggingface/hub`) | ~1.5 GB | Bóc tách giọng nói thuyết minh gốc ra khỏi nhạc nền BGM để nghe rõ ngữ điệu và thuật ngữ. |
| **3. Frame & Slide OCR** | `sahilchachra/unlimited-ocr` (DeepSeek-OCR) | GGUF (`~/.lmstudio/models`) | ~2.6 GB | Bóc tách công thức toán, bảng biểu, mã giả (pseudocode) từ các khung hình slide bài giảng. |
| **4. Visual & Spatial Understanding** | `qwen3-vl-8b-thinking` | GGUF Q4_K_M + mmproj (`~/.lmstudio/models`) | ~6.2 GB | Đọc keyframe video YouTube, phân tích cấu trúc đồ thị, cây nhị phân, hướng mũi tên chuyển động để học hỏi visual pattern. |
| **5. Pedagogical Deconstruction & Scriptwriting** | `lmstudio-community/qwen3.5-9b` | GGUF Q4_K_M (`~/.lmstudio/models`) | ~6.5 GB | Tái cấu trúc nội dung theo cấu trúc 6 phân cảnh "Tôi Làm Việc" (Hook $\rightarrow$ Vấn đề $\rightarrow$ Trực giác hình học $\rightarrow$ Chứng minh toán $\rightarrow$ Ứng dụng thực chiến $\rightarrow$ Đạo làm nghề). |
| **6. Manim Community Code Generation** | `yuxinlu1/gemma-4-12b-coder` | GGUF Q4_K_M (`~/.lmstudio/models`) | ~7.4 GB | Sinh mã nguồn Python Manim hoàn chỉnh, tuân thủ `ZenPalette`, `safe_place()`, không dùng tiếng Việt có dấu trong `MathTex`. |
| **7. Vietnamese Voiceover Synthesis** | `OmniVoice TTS` (Zen Mien Tay) | Container port 8080 (`http://10.123.214.178:8080`) | ~3.5 GB | Tạo file thuyết minh WAV 100% Đơn giọng Zen Miền Tây (TTS V0-Sense, `1.0x` native), giữ nguyên thuật ngữ tiếng Anh gốc, TUYỆT ĐỐI CẤM cắt ghép 2 giọng đọc, không phiên âm thô. |
| **8. 2K QHD Master Rendering** | `manimcommunity/manim:latest` | Docker container | CPU / OpenGL GPU | Render video 2K QHD (2560x1440 @ 60fps). Camera tĩnh 100% (Zero Fake Motion), chống đóng băng bằng `pulse_tracker` & sóng mang hàm số (`noise=-65dB`). |

### Cơ chế Điều Phối VRAM (GPU Time-Sharing):
Do RTX 5000 có 16GB VRAM và OmniVoice giữ ~3.5GB khi rảnh, pipeline áp dụng kỹ thuật **tuần tự hóa GPU**:
1. **Bước 1**: Chạy Faster-Whisper / yt-dlp trích xuất âm thanh và transcript (tốn 1.5GB VRAM, giải phóng ngay).
2. **Bước 2**: Nạp `qwen3.5-9b` vào LM Studio (`lms load qwen/qwen3.5-9b`) để xây dựng kịch bản 6 cảnh (~6.5GB VRAM).
3. **Bước 3**: Chuyển sang `gemma-4-12b-coder` (`lms load gemma-4-12b-coder-...`) để viết code Manim (~7.4GB VRAM).
4. **Bước 4**: Render Manim bằng Docker và tổng hợp audio bằng OmniVoice.

---

## 2. Quy Trình 4 Bước Phân Tích Kịch Bản Từ YouTube URL

```
   [YouTube URL]
         │
   ┌─────┴──────────────────────────────────────────────────────┐
   │ BƯỚC 1: Thu thập đa kênh (Multi-Modal Ingestion)           │
   │ - Public Video: yt-dlp tải audio m4a + Whisper ASR         │
   │ - Members-only Video: Fallback Scraping (Metadata + Blog)  │
   │ - Keyframe Sampler: Trích xuất 1 ảnh mỗi 10 giây           │
   └─────────────────────────────┬──────────────────────────────┘
                                 ▼
   ┌────────────────────────────────────────────────────────────┐
   │ BƯỚC 2: Mổ xẻ sư phạm (Pedagogical Deconstruction)        │
   │ Model: Qwen 3.5 9B (LM Studio)                             │
   │ - Tách Core Invariant (Tiên đề bất biến toán học)          │
   │ - Bóc tách sự suy biến / thảm họa hiệu năng                │
   │ - Định vị ẩn dụ thị giác (Visual Metaphor)                  │
   └─────────────────────────────┬──────────────────────────────┘
                                 ▼
   ┌────────────────────────────────────────────────────────────┐
   │ BƯỚC 3: Dựng kịch bản phân cảnh "Tôi Làm Việc"             │
   │ Model: Qwen 3.5 9B (LM Studio)                             │
   │ - Chuẩn 6 hồi: Hook -> Pain Point -> Visual -> Proof ->    │
   │   Benchmark -> Craftsmanship                               │
   │ - Phân bổ nhịp đọc, Voice-Sync & SFX cues                  │
   │ - Pexels Visual Matcher (>90% Rule):                       │
   │   + Tra cứu Pexels cho cảnh B-roll thực tế (máy chủ, code) │
   │   + Nếu khớp >= 90%: DÙNG TRỰC TIẾP VIDEO FOOTAGE PEXELS   │
   │   + Nếu khớp < 90%: Chuyển giao sang lập trình Manim       │
   └─────────────────────────────┬──────────────────────────────┘
                                 ▼
   ┌────────────────────────────────────────────────────────────┐
   │ BƯỚC 4: Lập trình hoạt họa Manim 2K QHD (Clear Layout)     │
   │ Model: Gemma 4 12B Coder + AST Auditor                     │
   │ - Áp dụng Bố cục 3 tầng Toán Thầy Việt (Dkxhykqz5VE):      │
   │   + Đỉnh: StateTrackerBar dải tiến trình tư duy            │
   │   + Giữa: Bố cục 2 cột 60/40 (Trái: Hình học, Phải: Stack) │
   │   + Đáy: BottomCalloutCard triết lý (cách ly phụ đề Y>=-2.6)│
   │ - Render 2560x1440 @ 60fps, nền Obsidian #0c0d12           │
   │ - Đảm bảo Safe Margin 15% (Y >= -2.6 cho phụ đề)          │
   └────────────────────────────────────────────────────────────┘
```

---

## 2.1. Chuẩn Bố Cục Rõ Ràng (Tham Chiếu "Toán Thầy Việt" `Dkxhykqz5VE`)

Kênh **Toán Thầy Việt** (`Dkxhykqz5VE`) đạt được mức độ rõ ràng thị giác vượt trội nhờ nguyên tắc **Spatial Division (Phân lập không gian tuyệt đối)**:
1. **Dải chỉ mục trạng thái đỉnh màn hình (`StateTrackerBar`)**: Dãy node tròn ở đỉnh màn hình $\mathbb{N} \rightarrow \mathbb{Z} \rightarrow \mathbb{Q} \rightarrow \mathbb{R} \rightarrow \mathbb{C}$ giúp người xem không bao giờ bị lạc lối trong bài giảng dài.
2. **Sân khấu 2 cột bất đối xứng (Asymmetric Two-Column)**:
   - **Cột Trái (60% Width)**: Dành riêng cho trực quan hình học động (Mặt phẳng phức, phép quay vector, cây nhị phân).
   - **Cột Phải (40% Width)**: Xếp tầng công thức (`EquationBox`), thẻ định danh (`ConceptBadge`), quy tắc suy luận ngắn (`NHÂN = xoay + co giãn`).
3. **Thẻ chú giải dưới đáy (`BottomCalloutCard`)**: Hộp thoại kính mờ ở đáy màn hình ($Y \in [-2.4, -1.8]$) chứa 1 câu đúc kết cốt lõi, hoàn toàn nằm trên vùng an toàn của phụ đề tự động YouTube ($Y \ge -2.6$).
4. **Mũi tên chỉ điểm trực quan (`PointCallout`)**: Mũi tên cong kèm nhãn `"ở ĐÂY"` chỉ đích danh điểm xoay/nút trọng tâm.

---

## 2.2. Nhận Diện Chuyên Ngành Khoa Học Tự Động & Nạp Template (Auto-Domain Science Detection)

Khi phân tích bất kỳ URL YouTube nào, mô hình `qwen3.5-9b` tự động phân loại chủ đề và nạp bộ quy tắc/mẫu code tương ứng từ `manim-production/references/templates/`:

| Chuyên Ngành | Dấu Hiệu Từ Khóa (Keywords) | Thư Viện Manim Chuyên Dụng | Template Mẫu Áp Dụng |
| :--- | :--- | :--- | :--- |
| **Vật Lý (Physics)** | *lực, gia tốc, con lắc, điện trường, từ trường Lorentz, khúc xạ, thấu kính, sóng* | `manim-physics` (Pymunk 2D, Electromagnetism, Ray Optics) | `references/templates/template_physics.py` |
| **Hóa Học (Chemistry)** | *phân tử, liên kết cộng hóa trị, orbital, bảng tuần hoàn, lai hóa, phản ứng* | `manim-Chemistry` (MMoleculeObject, BohrAtom, PubChem) | `references/templates/template_chemistry.py` |
| **Trí Tuệ Nhân Tạo (AI/ML)**| *attention, transformer, CNN, backprop, neural network, loss landscape, latent* | `manim-ml` (FeedForward, Conv2D, Attention Matrix) | `references/templates/template_ml.py` |
| **Giải Thuật / CS (DSA)** | *cây nhị phân, đồ thị, dijkstra, dynamic programming, sorting, complexity O(N)* | `networkx` + `Manim Graph`, Tree Layouts | `references/templates/template_cs_algo.py` |
| **Toán Cao Cấp (Pure Math)** | *ma trận, định thức det, không gian vector, vi tích phân, Fourier, Riemann* | Kho mẫu `3b1b/videos` + `sympy` | `references/templates/template_math_3b1b.py` |

Khi sinh mã Manim (Bước 4), `gemma-4-12b-coder` sẽ kết hợp bố cục 4 phân vùng từ `layout_and_typography.md` cùng cấu trúc hình học từ template chuyên ngành đã chọn, đảm bảo video vừa đẹp mắt vừa chính xác tuyệt đối về mặt học thuật.

---

## 2.3. Tự Động Đối Chiếu Manim Registry Để Tái Sử Dụng Scene Có Sẵn (Registry Matching)

Để tiết kiệm thời gian sinh mã và đảm bảo chất lượng hình ảnh đồng nhất giữa các tập, trong quá trình lập trình (Bước 4), AI tự động tra cứu bộ từ điển **`references/manim_dictionary.md`** hoặc chạy lệnh:
```bash
python3 assets/scripts_video/manim_registry_scanner.py --query "<khái niệm video cần vẽ>"
```
- **Nếu đã có Scene phù hợp** (ví dụ: đã có 10 Scene về Attention/Transformer trong Tập 03, 11, 12, hoặc Splay Tree trong Tập 100): Ưu tiên tái sử dụng ngay class và logic animation có sẵn, chỉ điều chỉnh thông số hoặc nhãn chữ.
- **Nếu là khái niệm mới hoàn toàn**: Tham khảo template tương ứng trong `references/templates/` để viết mới theo chuẩn 4 phân vùng rõ ràng.

---

## 3. Case Study Thực Tế: Phân Tích URL `vWnG7R6fvTw` (Splay Tree)

- **URL mục tiêu**: `https://www.youtube.com/watch?v=vWnG7R6fvTw`
- **Tiêu đề gốc**: *Splay Tree: Cấu Trúc Dữ Liệu Tự Tối Ưu Hóa*
- **Kênh**: *Học Giải Thuật Cùng HPN*
- **Đặc điểm video**: Đây là video độc quyền hội viên (Members-only). Hệ thống tự kích hoạt chế độ **Fallback Ingestion**:
  1. Trích xuất metadata, video description và các tài liệu liên kết (`penalgo.io.vn/algorithms/data-structures/balanced-bst`).
  2. Dùng `qwen3.5-9b` tái hiện toàn bộ hệ tiên đề toán học của Robert Tarjan & Daniel Sleator (1985).
  3. Xây dựng kịch bản chuẩn điện ảnh giáo dục cho kênh ZENPHAM.

### Kịch bản phân cảnh mẫu "Tôi Làm Việc":

```markdown
# TÔI LÀM VIỆC — SPLAY TREE: CÂY NHỊ PHÂN TỰ TIẾN HÓA VÀ NGHỆ THUẬT QUẢN TRỊ BỘ NHỚ

Đoạn 1: 00s–25s (Thảm họa cây thoái hóa — The Degenerate Tree)
• Hình ảnh: Cây tìm kiếm nhị phân thông thường (BST) khi chèn dữ liệu có thứ tự 1, 2, 3, 4, 5... biến dạng thành một danh sách liên kết thẳng đuột dài ngoằng. Tia tìm kiếm quét từng nút mất O(N), thanh CPU nhấp nháy đỏ rực.
• Lời thoại: "Một trong những bi kịch kinh điển nhất của người làm phần mềm là đặt niềm tin mù quáng vào lý thuyết. Trên giảng đường, chúng ta được học cây tìm kiếm nhị phân có độ phức tạp logarit. Nhưng khi dữ liệu thực tế đổ vào theo một trật tự có sẵn, cái cây ấy tự thoái hóa thành một danh sách liên kết thẳng đuột. Mọi bảo chứng hiệu năng O(log N) sụp đổ thành O(N). Để sinh tồn trong môi trường dữ liệu khắc nghiệt, chúng ta không cần một cái cây hoàn hảo tĩnh lặng — chúng ta cần một cái cây biết tự tái cấu trúc theo từng nhịp tìm kiếm."

Đoạn 2: 25s–55s (Triết lý Splay: Đẩy phần tử nóng lên gốc)
• Hình ảnh: [MANIM 2K: SplayAccessScene] Node giá trị 42 nằm sâu ở đáy cây được truy vấn. Thay vì giữ nguyên vị trí, node 42 phát sáng hào quang Cyan (ZenPalette.CYAN) và thực hiện chuỗi xoay liên hoàn, bay thẳng lên đỉnh làm Root. Các nhánh cây khác tự động thu hẹp độ sâu còn một nửa.
• Lời thoại: "Ý tưởng thiên tài của Robert Tarjan và Daniel Sleator năm 1985 mang tên Splay Tree. Thay vì lưu trữ cồng kềnh chiều cao hay màu sắc như AVL hay Red-Black Tree, Splay Tree tuân theo một bản năng sinh học thuần túy: hễ phần tử nào vừa được chạm vào, nó lập tức được đưa lên làm gốc. Trong thực tế, 80% truy vấn chỉ tập trung vào 20% dữ liệu. Splay Tree biến chính nhược điểm truy vấn thành động lực tái cân bằng cây."

Đoạn 3: 55s–90s (Vũ điệu 3 phép xoay: Zig, Zig-Zig, Zig-Zag)
• Hình ảnh: [MANIM 2K: ThreeRotationsComparisonScene] Màn hình chia làm 3 cột Glassmorphism:
  - Cột 1: Zig (Node là con trực tiếp của Root) -> Xoay đơn 1 nhịp.
  - Cột 2: Zig-Zig (Cả con và cha cùng lệch một hướng) -> Xoay cha trước, xoay con sau (Kỹ thuật then chốt bẻ gãy nhánh cây sâu).
  - Cột 3: Zig-Zag (Con và cha lệch hướng đối xứng) -> Xoay kép như AVL.
• Lời thoại: "Cơ chế đưa một nút lên đỉnh được thực hiện qua ba vũ điệu hình học. Nếu nút là con trực tiếp của gốc, một phép xoay ZIG đơn giản là xong. Nếu nút và cha cùng lệch về một phía, điều kỳ diệu xảy ra ở phép ZIG-ZIG: ta bắt buộc phải xoay ông nội trước, rồi mới xoay cha. Thứ tự này không hề ngẫu nhiên — nó bẻ gãy một nửa độ sâu của toàn bộ nhánh cây. Và cuối cùng là ZIG-ZAG, phép xoay kép đưa nút lên giữa hai tầng."

Đoạn 4: 90s–125s (Toán học sâu sắc: Phân tích khấu hao & Hàm thế năng Tarjan)
• Hình ảnh: [MANIM 2K: PotentialFunctionScene] Phương trình thế năng Phi(T) = sum log(size(x)) hiện lên trong EquationBox viền vàng ZenPalette.GOLD. Đồng hồ AnimatedCounter đếm chi phí khấu hao Amortized Cost luôn ổn định <= 3(r'(x) - r(x)) + 1, hội tụ về O(log N).
• Lời thoại: "Splay Tree có thể tốn O(N) cho một lần tìm kiếm xui xẻo. Vậy tại sao Linux Kernel và các router mạng tỷ đô vẫn dùng nó? Câu trả lời nằm ở Phân tích khấu hao. Bằng việc định nghĩa một hàm thế năng đo độ cồng kềnh của cây, Tarjan chứng minh rằng: chi phí đắt đỏ của một lần xoay thực chất là một khoản đầu tư sinh lời. Nó dọn dẹp và nén phẳng toàn bộ cây, giúp hàng nghìn truy vấn tiếp theo diễn ra với tốc độ ánh sáng."

Đoạn 5: 125s–150s (Ứng dụng thực chiến: High-Speed Cache & Network Routing)
• Hình ảnh: Sơ đồ dòng dữ liệu gói tin IP Router. Các địa chỉ IP phổ biến luôn nằm ở 3 tầng đầu tiên của cây, thời gian định tuyến giảm 70% so với Hash Table khi bộ nhớ đệm L3 bị giới hạn.
• Lời thoại: "Trong kiến trúc bộ nhớ vi xử lý hiện đại, mỗi bit bộ nhớ đều quý giá. Splay Tree không tốn thêm dù chỉ 1 byte để lưu siêu dữ liệu cân bằng. Nó là hiện thân hoàn hảo của thuật toán tự thích nghi, tối ưu hóa phần cứng bằng chính hành vi của người dùng."

Đoạn 6: 150s–170s (Đạo làm nghề — Sự linh hoạt đánh bại sự cứng nhắc)
• Hình ảnh: Cây Splay Tree co giãn mềm mại như một sinh thể sống trong đêm Obsidian. Logo ZENPHAM hiện mờ ở góc trên.
• Lời thoại: "Cấu trúc dữ liệu dạy chúng ta một bài học sâu sắc: Sự cứng nhắc cố duy trì một trạng thái hoàn hảo tĩnh lặng thường phải trả giá bằng sự phức tạp vô tận. Đôi khi, bí quyết của sự bền vững lại nằm ở năng lực biết thích nghi linh hoạt sau mỗi lần va chạm. Hẹn gặp lại bạn ở tập tiếp theo."
```

---

## 4. Lệnh Thực Thi Mẫu Trên Máy P15

```bash
# Phân tích URL và tự sinh kịch bản + code Manim:
python3 assets/scripts_video/youtube_to_manim_pipeline.py \
  --url "https://www.youtube.com/watch?v=vWnG7R6fvTw" \
  --output-dir assets/scripts_video/splay_tree_production

# Kiểm định an toàn layout & Anti-Hallucination Quality Gate (0 Critical, 0 Warning):
python3 assets/scripts_video/manim_quality_gate.py --episode 02

# Render 2K QHD 60fps qua Docker:
docker run --rm -v $(pwd)/assets/scripts_video:/manim \
  manimcommunity/manim:latest \
  manim -r 2560,1440 --fps 60 /manim/manim_splay_tree.py SplayTreeMainScene
```
