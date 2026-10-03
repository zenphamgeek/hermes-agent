# QUY CHUẨN PHỤ ĐỀ VÀNG (GOLD SRT KARAOKE STANDARD)
**Áp dụng:** Toàn bộ hệ thống video Masterclass 16:9 và YouTube Shorts 9:16 thuộc Content Factory (ZENPHAM, Biết Địa Lý Từ Ba Tôi, Tôi Đọc Sách, Reality Decode).

---

## 1. NGUYÊN TẮC CỐT LÕI (CORE PRINCIPLES)

> [!IMPORTANT]
> **CẤM DỒN CẢ ĐOẠN VĂN LÊN MÀN HÌNH (Zero Full-Paragraph Dumps).**
> Phụ đề YouTube không phải là tài liệu in ấn để hiển thị 2–3 dòng văn bản dài 12–15 giây bao phủ toàn bộ màn hình. Phụ đề phải là dòng chảy thị giác động học (Dynamic Karaoke Cadence), dẫn dắt mắt người xem theo từng nhịp thở của người dẫn chuyện.

### 4 Trụ Cột Của Chuẩn Phụ Đề Vàng:
1. **Hiển thị chính xác vài từ (A Few Words Only — 3 đến 5 từ / cue):**
   - Mỗi cue phụ đề chỉ hiển thị từ 2 đến 6 từ (lý tưởng: 3–5 từ).
   - Tuyệt đối không để dồn quá 7 từ trên một khung hình.
2. **Quy tắc 60% chiều ngang màn hình (60% Screen Width Rule):**
   - Chiều dài mỗi cue phụ đề: **18 đến 32 ký tự** (ngưỡng tối đa tuyệt đối: **35 ký tự**).
   - Đảm bảo khi hiển thị ở kích cỡ chữ tiêu chuẩn (Font Size 40–52 trên 16:9, Font Size 55–68 trên 9:16), phụ đề chỉ chiếm tối đa 60% chiều ngang vùng an toàn chính giữa màn hình (chừa lề 20% mỗi bên trái và phải).
   - Tránh xa các vùng HUD telemetry, logo thương hiệu góc phải và thanh công cụ Shorts Right-Rail ($X \le 3.1$).
3. **Nhịp điệu Karaoke động (Dynamic Pacing: 0.8s – 2.2s / cue):**
   - Thời lượng mỗi cue: **0.8 giây đến 2.2 giây** (tối đa tuyệt đối: 2.8 giây).
   - Xuất hiện và biến đổi nhịp nhàng theo tốc độ nói (180–205 WPM).
   - Ngắt câu tự nhiên theo ngữ nghĩa tiếng Việt: theo dấu câu (`.`, `,`, `—`, `...`), khoảng nghỉ hơi thở ($>0.28\text{s}$), hoặc ranh giới chủ ngữ - vị ngữ.
4. **Bảo toàn từ ghép & Cấm tách âm tiết (Zero Broken Compound Words):**
   - Tuyệt đối cấm tách đôi các từ ghép tiếng Việt hoặc danh từ riêng khoa học (ví dụ: cấm ngắt *"ngẫu"* ở cue trước, *"nhiên"* ở cue sau; cấm ngắt *"Claude"* / *"Shannon"*, *"Quỷ"* / *"Laplace"*, *"xác"* / *"suất"*, *"trí"* / *"tuệ"*).

---

## 2. BẢNG THÔNG SỐ KỸ THUẬT ĐỊNH LƯỢNG (QUANTITATIVE METRICS)

| Tiêu Chí Đo Lường | Ngưỡng Lý Tưởng (Gold Target) | Giới Hạn Cứng Cho Phép (Hard Limit) | Vi Phạm (Rejection Trigger) |
| :--- | :---: | :---: | :--- |
| **Số từ mỗi cue (Words / Cue)** | **3 – 5 từ** | 2 – 6 từ | $> 7$ từ hoặc $\le 0$ từ |
| **Số ký tự mỗi dòng (Chars / Line)** | **20 – 30 ký tự** | $\le 34$ ký tự | $> 35$ ký tự (tràn 60% màn hình) |
| **Số dòng trên màn hình (Line Count)** | **1 dòng duy nhất** | 1 dòng | $\ge 2$ dòng |
| **Thời lượng mỗi cue (Duration / Cue)** | **1.0s – 2.2s** | 0.6s – 2.6s | $> 2.8\text{s}$ hoặc $< 0.4\text{s}$ |
| **Độ khớp kịch bản gốc (Script Accuracy)** | **100.0%** | $\ge 99.5\%$ | Có lỗi chính tả / sai thuật ngữ |
| **Từ ghép bị xé đôi (Broken Compounds)** | **0 từ** | 0 từ | $\ge 1$ từ ghép bị cắt đôi |

---

## 3. QUY TRÌNH SẢN XUẤT PHỤ ĐỀ (PIPELINE INTEGRATION)

```
Kịch bản gốc (Canonical Script) + Audio WAV (TTS V0-Sense)
                   │
                   ▼
[Faster-Whisper on CUDA (word_timestamps=True)]
                   │
                   ▼
[Difflib SequenceMatcher (Khớp 100% chữ hoa, dấu câu gốc)]
                   │
                   ▼
[Gold Karaoke 60% Chunker (Nhịp 3-5 từ, ngắt ngữ nghĩa tự nhiên)]
                   │
                   ▼
[Quality Gate Test (test_gold_srt_quality_gate.py)]
                   │
                   ▼
Xuất bản YouTube Captions API (.srt)
```

---

## 4. BỘ KIỂM TOÁN TỰ ĐỘNG (QUALITY GATE HOOK)

Mọi tệp `.srt` trước khi mux vào video hoặc upload lên YouTube bắt buộc phải chạy qua hàm kiểm định:
`audit_gold_srt_quality(srt_path)` tại `tests/test_gold_srt_quality_gate.py`. Bất kỳ tệp phụ đề nào có dòng dài quá 35 ký tự, thời lượng cue $>2.8\text{s}$, hoặc chứa từ ghép bị cắt đôi đều bị **HARD STOP** từ chối nghiệm thu.
