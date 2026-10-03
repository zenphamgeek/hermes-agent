---
name: youtube-video-rewriter
description: "Nhận đầu vào là 1 URL YouTube, tự động tải/phiên âm phụ đề .srt, mổ xẻ cấu trúc sư phạm, tra cứu Manim Registry (100 scenes), lập kịch bản sản xuất đa luồng 4 track (OmniVoice TTS, Manim 4-Zone, B-roll Footage, SFX), và chạy kiểm toán ảo giác (Hallucination Audit Engine) 5 chiều trên máy trạm ThinkPad P15 (Quadro RTX 5000 16GB)."
version: 1.0.0
author: ZENPHAM & Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [youtube, srt-extraction, script-rewriting, manim, registry-first, omnivoice-tts, hallucination-audit, 4-zone-layout, thinkpad-p15]
    related_skills: [manim-production, youtube-to-manim, toi-lam-viec, youtube-channel-srt, pexels-visual-search]
---

# YouTube Video Rewriter & Hallucination Audit Skill (ThinkPad P15)

Skill này cung cấp quy trình tự động hóa toàn diện nhằm tiếp nhận bất kỳ **URL Video YouTube** nào (bài giảng kỹ thuật, giải thuật, toán học, AI, kiến trúc hệ thống), phân tích phụ đề `.srt`, mổ xẻ cấu trúc sư phạm, tra cứu **Manim Registry (100 Scenes)** để tái sử dụng hoạt họa sẵn có, xây dựng kịch bản đa luồng 4 track (**OmniVoice TTS**, **Manim 4 Phân Vùng**, **Footage B-roll & SFX** kèm **Pexels Visual Matcher >90% Rule**), và thực thi **Động Cơ Kiểm Toán Ảo Giác (Hallucination Audit Engine)** 5 chiều để đảm bảo tính xác thực học thuật và độ tin cậy tuyệt đối trước khi sản xuất.

> **Đặc tả kỹ thuật chính thức**: Xem toàn bộ quy chuẩn tại [MANIM_SKILLS_MASTER_SPECIFICATION.md](../../../docs/specs/MANIM_SKILLS_MASTER_SPECIFICATION.md).

---

## 1. Kiến Trúc Pipeline 5 Tầng (5-Stage Pipeline Architecture)

```
[ YouTube URL / ID ]
        │
        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ TẦNG 1: SRT & METADATA INGESTION (scripts/srt_extractor.py)                 │
│ - Tải .srt chính thức / auto-sub qua yt-dlp hoặc youtube_transcript_api     │
│ - Fallback: Tải audio 16kHz mono -> Faster-Whisper ASR (GPU P15) tạo .srt   │
│ - Phân tích mật độ lời thoại, tốc độ WPM, trích xuất metadata và chapters   │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ TẦNG 2: GIẢI PHẪU SƯ PHẠM (scripts/script_deconstructor.py)                │
│ - Mô hình: Qwen 3.5 9B (LM Studio http://10.123.214.1:1234) hoặc Heuristic │
│ - Bóc tách Core Invariant (Tiên đề bất biến) & Pain Point (Thảm họa)       │
│ - Bản đồ hóa 6 hồi kinh điển: Hook -> Nỗi đau -> Trực giác -> Chứng minh -> │
│   Thực chiến -> Đạo làm nghề                                                │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ TẦNG 3: MANIM SRS & REGISTRY-FIRST (scripts/manim_srs_planner.py)           │
│ - Tra cứu Manim Registry (`manim_registry.json`) đối chiếu 100 Scene đã có  │
│ - Áp dụng Bố cục 4 phân vùng chuẩn:                                         │
│   + Zone 1: StateTrackerBar (Y ≈ +3.3)                                      │
│   + Zone 2: Visual Canvas 60% (X ∈ [-6, 0])                                 │
│   + Zone 3: Cognitive Stack 40% (X ∈ [1, 6])                                │
│   + Zone 4: BottomCalloutCard (Y ∈ [-2.4, -1.8])                            │
│   + Vùng cấm phụ đề: Tuyệt đối không đặt phần tử cố định tại Y < -2.6       │
│ - Chọn Duotone Icon (assets/duotone/ 1,512 SVG) & Preset YouTube Style      │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ TẦNG 4: MULTI-TRACK SCRIPTWRITING (scripts/script_writer.py)                │
│ - Track 1: Timeline & Phân cảnh 6 hồi                                       │
│ - Track 2: Thuyết minh TTS OmniVoice (100% Đơn giọng Zen Miền Tây, 0.94x)   │
│ - Track 3: Manim Animation Blueprint (Class name, Zone 1-4, ASCII MathTex)  │
│ - Track 4: Footage B-roll & SFX (Tự động tra cứu PexelsVisualMatcher:       │
│   * Nếu khớp >= 90%: DÙNG TRỰC TIẾP VIDEO FOOTAGE PEXELS [VISUAL: PEXELS]   │
│   * Nếu khớp < 90%: Fallback về hoạt họa Manim / Terminal screen capture)   │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ TẦNG 5: KIỂM TOÁN ẢO GIÁC & QUALITY GATE (scripts/hallucination_auditor.py) │
│ - Chiều 1: Toán học & Big-O (SymPy, kiểm tra đẳng thức, chặn trên)          │
│ - Chiều 2: Cú pháp mã nguồn & AST (Loại bỏ API Manim ảo hoặc deprecated)    │
│ - Chiều 3: Sự kiện & Lịch sử khoa học (Đối soát tác giả, năm phát minh)     │
│ - Chiều 4: Bố cục Manim SRS (Bảo vệ vùng an toàn phụ đề Y >= -2.6)         │
│ - Chiều 5: Đồng bộ Lời thoại - Thị giác (Visual-Verbal Consistency)         │
│ - Chiều 6: Zero Fake Motion (100% Camera tĩnh, cấm filter crop/sway/zoom)   │
│ - Chiều 7: Vi động lực học Manim (Ambient motion từ hero math entity, chống freeze -65dB)│
│ => Xuất Hallucination Risk Score (0-100) & Báo cáo hướng dẫn đính chính     │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Hướng Dẫn Vận Hành Master CLI (Quick Start)

Chạy toàn bộ quy trình từ 1 lệnh duy nhất thông qua môi trường ảo của Hermes Agent:

```bash
# Cú pháp đầy đủ:
/home/zen/hermes-agent/.venv/bin/python \
  skills/creative/youtube-video-rewriter/scripts/rewrite_youtube_pipeline.py \
  "https://www.youtube.com/watch?v=vWnG7R6fvTw" \
  --output-dir "./workspace/rewrite_splay_tree" \
  --style "neo_noir"
```

### Các tùy chọn tham số:
- `--style`: Lựa chọn 1 trong 4 phong cách thị giác YouTube:
  - `neo_noir` *(Mặc định cho ZenPham "Tôi Làm Việc")*: Nền tối Obsidian `#0c0d12`, viền phát sáng Neon Cyan/Gold.
  - `architecture` *(Phong cách ByteByteGo / System Design)*: Dùng `ArchitectureNode`, Duotone icon đại diện cho DB, Cache, Worker.
  - `minimal` *(Phong cách 3Blue1Brown / Toán Thầy Việt)*: Tinh giản tối đa, tập trung vào công thức LaTeX và đồ thị.
  - `vibrant` *(Phong cách Kurzgesagt / Primer)*: Đậm đà, 2 mảng màu tương phản rực rỡ.
- `--force-whisper`: Bỏ qua phụ đề YouTube có sẵn và ép chạy Faster-Whisper ASR trên GPU Quadro RTX 5000.
- `--skip-audit`: Bỏ qua bước kiểm toán ảo giác (không khuyến nghị).

---

## 3. Quy Chuẩn Vận Hành Chi Tiết Từng Module

### 3.1. Thu Thập Phụ Đề & Xử Lý Âm Thanh (`srt_extractor.py`)
- **Tải Subtitle**: Sử dụng `yt-dlp` với các cờ tối ưu anti-bot (`--sub-lang vi,en --convert-subs srt`).
- **Whisper ASR Fallback**: Khi video là livestream, bài giảng không có phụ đề, hoặc video tiếng nước ngoài cần dịch, hệ thống tự nạp `faster-whisper` (`device="cuda"`, `compute_type="float16"`), bóc tách từng phân đoạn kèm timestamp chính xác đến mili-giây.
- **Tính toán WPM**: Đo đếm chính xác tốc độ nói gốc của giảng viên để chuẩn bị biên dịch sang tốc độ 140 WPM chuẩn cho OmniVoice.

```bash
python3 skills/creative/youtube-video-rewriter/scripts/srt_extractor.py \
  "URL_YOUTUBE" --output-dir "./workspace/my_ingest"
```

### 3.2. Mổ Xẻ Sư Phạm & Bản Đồ 6 Hồi (`script_deconstructor.py`)
- Trích xuất 3 trụ cột nhận thức:
  1. **Core Thesis**: Thông điệp trung tâm bài giảng.
  2. **Core Invariant**: Tiên đề bất biến toán học / kỹ thuật bảo đảm hệ thống vận hành.
  3. **Pain Point**: Điểm nghẽn hiệu năng khiến lý thuyết sụp đổ trong thực tế.
- Phân đoạn thành **6 Hồi chuẩn điện ảnh**:
  - *Hồi 1: Hook & Cú sốc nhận thức* (00:00 - 00:45)
  - *Hồi 2: Nỗi đau kỹ thuật & Thảm họa hiệu năng* (00:45 - 02:15)
  - *Hồi 3: Trực giác hình học & Mô hình tư duy* (02:15 - 04:45)
  - *Hồi 4: Chứng minh toán học & Tiên đề bất biến* (04:45 - 07:15)
  - *Hồi 5: Thực chiến kỹ nghệ & Điểm nghẽn hệ thống* (07:15 - 09:30)
  - *Hồi 6: Đạo làm nghề & Triết lý kiến trúc* (09:30 - 11:00)

### 3.3. Tra Cứu Manim Registry-First & Bố Cục 4 Phân Vùng (`manim_srs_planner.py`)
- **Nguyên tắc Registry-First**: Luôn tra cứu cơ sở dữ liệu `assets/scripts_video/manim_registry.json` (chứa 100 Scene đã xây dựng từ 25 tập "Tôi Làm Việc", Splay Tree, Science Templates) trước khi viết mã mới.
- **Phân bổ không gian 4-Zone**:
  - `Zone 1 (Tracker)`: $Y \approx +3.3$
  - `Zone 2 (Visual Canvas 60%)`: $X \in [-6.0, 0.0]$
  - `Zone 3 (Cognitive Stack 40%)`: $X \in [1.0, 6.0]$
  - `Zone 4 (Callout Card)`: $Y \in [-2.4, -1.8]$
  - **Vùng cấm phụ đề (Subtitle Exclusion Zone)**: Tuyệt đối không đặt Mobject tại $Y < -2.6$.
- **Gán Phosphor Duotone Icon**: Lựa chọn tự động từ kho 1,512 icon SVG tại `assets/duotone/`.

### 3.4. Biên Soạn Kịch Bản Đa Luồng (`script_writer.py`)
- Kết hợp dữ liệu phân tích và kế hoạch Manim để tạo file `production_script_multitrack.md` gồm 4 luồng song song:
  - **Track 1**: Timeline & Tên phân cảnh.
  - **Track 2**: Lời thoại thuyết minh tiếng Việt chuẩn OmniVoice (100% Đơn giọng Zen Miền Tây):
    - **Định luật Đơn Giọng Thuần Khiết (Monolingual Invariant)**: 1 giọng Zen duy nhất từ đầu tới cuối (`0.94x`), tuyệt đối KHÔNG cắt ghép 2 giọng đọc.
    - **Thuật ngữ kỹ thuật**: Giữ nguyên tiếng Anh gốc (`Splay Tree`, `Transformer`, `Softmax`, `Cache`, `Attention`), không phiên âm thô.
    - **Acronyms**: Đọc tách từng chữ cái (`N a N`, `L L M`, `G P U`). Thương hiệu: `Zen Phạm`.
    - Chèn thẻ ngắt nhịp thở `[pause 0.5s]`, `[emphasis]`.
  - **Track 3**: Đặc tả Manim 4 vùng kèm công thức LaTeX thuần ASCII (không dùng tiếng Việt có dấu trong `MathTex`).
  - **Track 4**: Kế hoạch B-Roll (Quay màn hình IDE, terminal Linux, đồ thị Grafana) và SFX Cues (`whoosh_subtle`, `sub_bass_drop`, `digital_beep`).

### 3.5. Động Cơ Kiểm Toán Ảo Giác 5 Chiều (`hallucination_auditor.py`)
Chạy kiểm toán tự động trên kịch bản vừa tạo:
1. **Toán học & Big-O**: Phát hiện các tuyên bố sai về độ phức tạp thuật toán (ví dụ: gán nhầm $O(1)$ cho thao tác đơn lẻ tồi nhất thay vì $O(\log N)$ Amortized).
2. **Cú pháp mã nguồn & AST**: Bắt lỗi cú pháp trong các đoạn code Python, phát hiện các hàm Manim CE lỗi thời (như `ShowCreation`, `FadeInFrom`, `TextMobject`).
3. **Sự kiện & Trích dẫn khoa học**: Bắt lỗi sai lệch năm phát minh hoặc tên tác giả (ví dụ: Tarjan & Sleator 1985, Vaswani 2017).
4. **Bố cục Manim**: Bắt lỗi đè vùng cấm phụ đề ($Y < -2.6$) hoặc lỗi tiếng Việt trong `MathTex`.
5. **Đồng bộ Lời thoại - Thị giác**: Bắt lỗi kịch bản khi thuyết minh nói một đằng nhưng hình ảnh mô tả một nẻo.

**Thang điểm rủi ro ảo giác (Risk Score)**:
- `0 - 10`: **PRISTINE** (Hoàn hảo, không có bất kỳ ảo giác nào).
- `11 - 25`: **LOW RISK** (Đạt chuẩn xuất xưởng).
- `26 - 50`: **MEDIUM RISK** (Cần áp dụng khuyến nghị đính chính).
- `> 50`: **HIGH RISK** (Bắt buộc chạy lại kịch bản).

---

## 4. Bảng Tra Cứu Tệp & Tài Nguyên (Skill Resources)

| Đường Dẫn | Loại Tệp | Nhiệm Vụ |
| :--- | :--- | :--- |
| `scripts/srt_extractor.py` | Python Script | Tải phụ đề YouTube `.srt`, chạy Faster-Whisper ASR, phân tích WPM. |
| `scripts/script_deconstructor.py` | Python Script | Giải phẫu sư phạm, bóc tách Core Invariant & bản đồ 6 hồi. |
| `scripts/manim_srs_planner.py` | Python Script | Tra cứu Manim Registry 100 scenes, thiết lập bố cục 4 phân vùng. |
| `scripts/script_writer.py` | Python Script | Biên soạn kịch bản đa luồng 4 track, nhúng phiên âm OmniVoice. |
| `scripts/hallucination_auditor.py` | Python Script | Động cơ kiểm toán ảo giác 7 chiều, tính điểm Risk Score. |
| `scripts/rewrite_youtube_pipeline.py`| Python Script | Master CLI điều phối toàn bộ pipeline 5 tầng. |
| `references/tech_terms_glossary.json` | JSON Ref | Bảng đối soát từ khóa công nghệ & quy tắc tách âm acronyms (không phiên âm thô). |
| `templates/script_template_multitrack.md` | Markdown Template| Mẫu kịch bản đa luồng 4 track chuẩn 6 hồi cho ZenPham. |

---

## 5. Quy Chuẩn VRAM Trên Máy Trạm P15 (Workstation Constraints)
1. **Chỉ dùng LM Studio**: Endpoint chuẩn là `http://10.123.214.1:1234/v1` (hoặc `127.0.0.1:1234/v1`). **Tuyệt đối không dùng Ollama**.
2. **Luân chuyển VRAM**:
   - Giai đoạn 1 (Faster-Whisper): ~1.2 GB VRAM (chạy xong giải phóng).
   - Giai đoạn 2 & 4 (Qwen 3.5 9B): ~6.5 GB VRAM trên LM Studio.
   - Giai đoạn 3 (Tra cứu Registry): CPU + Memory (0 GB VRAM).
   - Giai đoạn 5 (Kiểm toán AST & SymPy): Chạy trên CPU, xử lý tức thì (<1 giây).
