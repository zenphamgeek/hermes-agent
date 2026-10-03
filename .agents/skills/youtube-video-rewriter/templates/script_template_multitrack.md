# BẢN KỊCH BẢN ĐA LUỒNG SẢN XUẤT VIDEO KỸ THUẬT (MULTI-TRACK PRODUCTION SCRIPT)
## Kênh: ZENPHAM — "Tôi Làm Việc" & Deep Tech Documentary
### Chuẩn: 2K QHD 1440p @ 60fps | Manim 4-Zone | OmniVoice TTS | Neo-Noir

---

## 1. METADATA & BẢN ĐỒ TỔNG QUAN (PRODUCTION METADATA)

- **Tiêu đề video**: {{VIDEO_TITLE}}
- **Độ dài mục tiêu**: {{TARGET_DURATION}} (Dự kiến ~{{WORD_COUNT}} từ, tốc độ 135-145 từ/phút)
- **Chuyên ngành (Domain)**: {{DOMAIN}} *(Physics | Chemistry | AI_ML | CS_ALGO | PURE_MATH)*
- **Phong cách thị giác (Style)**: {{STYLE}} *(neo_noir | architecture | minimal | vibrant)*
- **Tài liệu tham chiếu gốc (Source URL)**: {{SOURCE_URL}}
- **Tiên đề bất biến cốt lõi (Core Invariant)**: {{CORE_INVARIANT}}
- **Bảng màu chủ đạo (ZenPalette)**:
  - Nền: Obsidian `#0c0d12`
  - Điểm nhấn chính: Neon Cyan `#00f5d4` & Amber Gold `#ffd166`
  - Cảnh báo/Lỗi: Coral Red `#ef476f`
  - Văn bản: Pearl White `#e2e8f0` & Slate Muted `#94a3b8`

---

## 2. KỊCH BẢN ĐA LUỒNG CHI TIẾT (MULTI-TRACK SCRIPT TABLE)

### HỒI 1: HOOK & CÚ SỐC NHẬN THỨC (00:00 — 00:45)
*Mục tiêu: Đập tan ngộ nhận thông thường của lập trình viên / kỹ sư trong 15 giây đầu.*

| Phân Luồng | Đặc Tả Chi Tiết |
| :--- | :--- |
| **Track 1: Timeline & Beat** | `00:00 - 00:45` \| **Scene 1: The Illusion of Perfection** |
| **Track 2: Voiceover (OmniVoice)** | [pause 0.5s] Một trong những ảo tưởng ngọt ngào nhất của người làm phần mềm... [emphasis] là tin rằng lý thuyết trên giảng đường luôn đúng trong thực tế. [pause 0.8s] Chúng ta được dạy rằng cấu trúc dữ liệu cây nhị phân có độ phức tạp ô-lốc-en (O(log N)). [pause 0.5s] Nhưng chỉ cần một dòng dữ liệu có thứ tự đổ vào, toàn bộ bảo chứng hiệu năng sụp đổ thành ô-en (O(N)). [pause 0.6s] Một danh sách liên kết thẳng đuột xuất hiện, và hệ thống của bạn nghẽn đứng. |
| **Track 3: Manim Blueprint** | **Class**: `DegenerateAnomalyScene` *(Registry: Reused / New)*<br>- **Zone 1 (Tracker)**: Node tròn highlight `VẤN ĐỀ`<br>- **Zone 2 (Canvas 60%)**: Cây BST chuẩn biến dạng thẳng đuột thành chuỗi dài, tia quét tìm kiếm đỏ rực.<br>- **Zone 3 (Stack 40%)**: `ConceptBadge("THẢM HỌA HIỆU NĂNG")` + `EquationBox("T(N) = \\mathcal{O}(N)")`.<br>- **Zone 4 (Callout)**: `BottomCalloutCard("Lý thuyết sụp đổ trước trật tự dữ liệu thực tế.")`<br>- **Safe Zone**: Đảm bảo $Y \ge -2.6$. |
| **Track 4: Footage & SFX** | - **Footage**: Màn hình Terminal nạp dữ liệu tăng dần, htop CPU 100% đỏ rực.<br>- **SFX**: `sub_bass_drop` tại 00:00, `glitch_low` khi cây gãy, `ambient_dark_drone` nền. |

---

### HỒI 2: NỖI ĐAU KỸ THUẬT & THẢM HỌA HIỆU NĂNG (00:45 — 02:15)
*Mục tiêu: Đào sâu vào nguyên nhân gốc rễ (Root Cause) và chi phí thực tế phải trả.*

| Phân Luồng | Đặc Tả Chi Tiết |
| :--- | :--- |
| **Track 1: Timeline & Beat** | `00:45 - 02:15` \| **Scene 2: The Latency Catastrophe** |
| **Track 2: Voiceover (OmniVoice)** | {{ACT_2_VOICEOVER}} |
| **Track 3: Manim Blueprint** | **Class**: `{{ACT_2_MANIM_CLASS}}`<br>- **Zone 1**: `StateTrackerBar` highlight bước 2.<br>- **Zone 2**: Đồ thị so sánh độ trễ hoặc mô phỏng dòng dữ liệu.<br>- **Zone 3**: Bảng thông số kỹ thuật (`SafeMetricCard`) & Công thức toán.<br>- **Zone 4**: `BottomCalloutCard` câu đúc kết hồi 2. |
| **Track 4: Footage & SFX** | - **Footage**: IDE VS Code zoom cận cảnh đoạn mã gây thảm họa bộ nhớ.<br>- **SFX**: `keyboard_mechanical_click`, `data_stream_hum`. |

---

### HỒI 3: TRỰC GIÁC HÌNH HỌC & MÔ HÌNH TƯ DUY (02:15 — 04:45)
*Mục tiêu: Khai mở giải pháp bằng trực quan không gian / hình học (3Blue1Brown style).*

| Phân Luồng | Đặc Tả Chi Tiết |
| :--- | :--- |
| **Track 1: Timeline & Beat** | `02:15 - 04:45` \| **Scene 3: The Geometric Intuition** |
| **Track 2: Voiceover (OmniVoice)** | {{ACT_3_VOICEOVER}} |
| **Track 3: Manim Blueprint** | **Class**: `{{ACT_3_MANIM_CLASS}}`<br>- **Zone 1**: `StateTrackerBar` highlight bước 3.<br>- **Zone 2**: Phép biến hình hình học (`Transform`, `ReplacementTransform`, quay vector, xoay nhánh cây).<br>- **Zone 3**: Nguyên lý hoạt động ngắn gọn dạng gạch đầu dòng (`Bullet Rules`).<br>- **Zone 4**: `BottomCalloutCard` trực giác cốt lõi. |
| **Track 4: Footage & SFX** | - **Footage**: Mô phỏng sơ đồ kiến trúc động với Phosphor Duotone Icons.<br>- **SFX**: `whoosh_subtle`, `energy_chime`. |

---

### HỒI 4: CHỨNG MINH TOÁN HỌC & TIÊN ĐỀ BẤT BIẾN (04:45 — 07:15)
*Mục tiêu: Đặt nền móng học thuật vững chắc, không nói suông bằng công thức toán chặt chẽ.*

| Phân Luồng | Đặc Tả Chi Tiết |
| :--- | :--- |
| **Track 1: Timeline & Beat** | `04:45 - 07:15` \| **Scene 4: The Mathematical Invariant** |
| **Track 2: Voiceover (OmniVoice)** | {{ACT_4_VOICEOVER}} |
| **Track 3: Manim Blueprint** | **Class**: `{{ACT_4_MANIM_CLASS}}`<br>- **Zone 1**: `StateTrackerBar` highlight bước 4.<br>- **Zone 2**: Biểu đồ thế năng hoặc chuyển dịch không gian trạng thái.<br>- **Zone 3**: `SafeFormulaCard` chứa chuỗi phương trình LaTeX chuẩn ASCII: ${{ACT_4_FORMULA}}$<br>- **Zone 4**: `BottomCalloutCard` định lý bảo toàn. |
| **Track 4: Footage & SFX** | - **Footage**: Trang tài liệu nghiên cứu gốc (ArXiv paper) highlight đoạn công thức then chốt.<br>- **SFX**: `chalk_board_soft`, `low_resonance`. |

---

### HỒI 5: THỰC CHIẾN KỸ NGHỆ & ĐIỂM NGHẼN HỆ THỐNG (07:15 — 09:30)
*Mục tiêu: Đưa toán học vào hạ tầng thực tế (Linux kernel, Database, GPU, Cache).*

| Phân Luồng | Đặc Tả Chi Tiết |
| :--- | :--- |
| **Track 1: Timeline & Beat** | `07:15 - 09:30` \| **Scene 5: Production Engineering Benchmark** |
| **Track 2: Voiceover (OmniVoice)** | {{ACT_5_VOICEOVER}} |
| **Track 3: Manim Blueprint** | **Class**: `{{ACT_5_MANIM_CLASS}}`<br>- **Zone 1**: `StateTrackerBar` highlight bước 5.<br>- **Zone 2**: Cột bar chart so sánh Throughput (req/s) và P99 Latency (ms).<br>- **Zone 3**: Architecture Diagram các tầng bộ nhớ (L1/L2/L3 Cache, RAM, NVMe).<br>- **Zone 4**: `BottomCalloutCard` bài học đánh đổi (Trade-off). |
| **Track 4: Footage & SFX** | - **Footage**: Benchmark chạy thật trên terminal Linux P15, biểu đồ Grafana nhảy số.<br>- **SFX**: `digital_process_beeps`, `riser_transition`. |

---

### HỒI 6: TỔNG HỢP KIẾN TRÚC & ĐƯỜNG CHÂN TRỜI KỸ NGHỆ (09:30 — 11:00)
*Mục tiêu: Đúc kết vẻ đẹp kiến trúc hệ thống, mở ra đường chân trời bài toán mới (Ending Archetype 1–5, CẤM 'Đạo làm nghề').*

| Phân Luồng | Đặc Tả Chi Tiết |
| :--- | :--- |
| **Track 1: Timeline & Beat** | `09:30 - 11:00` \| **Scene 6: Architecture Synthesis & System Horizon** |
| **Track 2: Voiceover (OmniVoice)** | {{ACT_6_VOICEOVER}} |
| **Track 3: Manim Blueprint** | **Class**: `{{ACT_6_MANIM_CLASS}}`<br>- **Zone 1**: `StateTrackerBar` hoàn tất toàn bộ chuỗi.<br>- **Zone 2**: Biểu tượng tối giản phát sáng tĩnh lặng trung tâm.<br>- **Zone 3**: Thẻ tổng kết kiến trúc & Cầu nối tập kế tiếp.<br>- **Zone 4**: `BottomCalloutCard` thông điệp đĩnh đạc sau cùng. |
| **Track 4: Footage & SFX** | - **Footage**: Màn hình hệ thống vận hành ổn định, dòng dữ liệu chảy mượt mà.<br>- **SFX**: `ambient_pad_warm`, `fade_to_black`. |

---

## 3. CHECKLIST KIỂM TOÁN ẢO GIÁC TRƯỚC KHI RENDER (HALLUCINATION AUDIT)

- [ ] **Toán học & Big-O**: Công thức toán đã được đối chứng bằng SymPy / Sách giáo khoa chuẩn.
- [ ] **Cú pháp Python Manim**: 100% Clean AST, không dùng hàm tự chế không có trong Manim CE.
- [ ] **Quy chuẩn vùng hiển thị**: Tuyệt đối không có Mobject nào cố định tại $Y < -2.6$.
- [ ] **Ngữ âm OmniVoice & Term Cooldown**: Toàn bộ từ tiếng Anh kỹ thuật tuân thủ Golden Method v4 & Term Cooldown (neo ngữ pháp tiếng Việt, không kẹp phiên âm đôi, không lặp từ trong câu/cảnh).
- [ ] **Tương thích Registry**: Đã ưu tiên tái sử dụng các Scene đã có trong `manim_registry.json`.
