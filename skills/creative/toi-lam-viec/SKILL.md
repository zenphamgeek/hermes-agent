---
name: toi-lam-viec
description: Production and publishing skill for ZENPHAM channel's "Tôi làm việc" series (AI Engineering craftsmanship, Manim math animations, Neo-noir tech minimalist 16:9 & 9:16, natural VI-EN TTS voiceover, YouTube publishing).
version: 1.1.0
author: ZENPHAM, Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [zenpham, toi-lam-viec, ai-engineering, software-craftsmanship, manim, video-production, youtube-publisher, omnivoice, gold-tts]
    related_skills: [vietnamese-expressive-tts, manim-production, zenpham-podcast-producer, zenpham-script-writer, toi-doc-sach, youtube-publisher, omnivoice-reader, manim-video, pexels-visual-search]
---

# Tôi Làm Việc — Production & Publishing Skill (v1.0)

Hệ thống sản xuất và xuất bản nội dung tự động cho series **"TÔI LÀM VIỆC"** trên kênh **ZENPHAM**.

---

## Contract production và release gate

**Hiện tại: prototype; chưa audio-approved; chưa visual-approved; chưa golden-approved.** Áp dụng [contract Manim production](../manim-production/SKILL.md#contract-production-và-golden-approval-2026-09-07) trước mọi lệnh batch/re-TTS/render/upload bên dưới. Không tự chạy publish chỉ vì checklist kỹ thuật pass.

- Mascot `assets/brand/zenpham-brand-kit/zenpham-mascot-rig.svg` là **SVG prototype**, chưa artwork/rig-approved; duyệt trong golden scene, không thay hero toán học hay thêm watermark.
- OmniVoice dùng catalog/reference thật và contract async bên mục 5; không phiên âm Việt, không IPA/phoneme/SSML giả. Nghe duyệt sample VI-EN có tên riêng, thuật ngữ, acronym và toán; lint/ASR chỉ hỗ trợ, không phải audio approval.
- Benchmark hình ảnh phải có URL tác phẩm chính chủ, tác giả/video, timestamp, ngày truy cập và tiêu chí so sánh. Nguồn khảo sát: [3Blue1Brown — Linear algebra](https://www.3blue1brown.com/topics/linear-algebra), [Manim configuration](https://docs.manim.community/en/stable/guides/configuration.html). Chưa có đoạn Median được xác minh: **chưa benchmark Median**. Không công bố hệ số tốc độ/dung lượng/retention nếu thiếu log đo hoặc nguồn phù hợp.
- Master 16:9 **2560x1440 @ 60fps**, master Shorts **1440x2560 @ 60fps**; bản 1080p chỉ là derivative, không đạt master 2K60. Đo width/height/r_frame_rate/avg_frame_rate sau mux bằng `ffprobe`; ghi rõ bumper/B-roll upscale hoặc chuyển fps.
- Duyệt golden 20–40s trước cả tập: audio trước, rồi visual không tiếng và bản có narration/SFX. Ghi `audio-approved`, `visual-approved`, `golden-approved` riêng với người duyệt, thời điểm, đường dẫn/hash media. Mặc định `pending`; chỉ người dùng/người duyệt được chỉ định xác nhận. Chặn nhân rộng/re-TTS hàng loạt/publish cho đến khi golden được duyệt; media đổi phải duyệt lại.

### Quy Chuẩn Bất Biến: Phòng Chống Đuối Ngữ Cảnh & Anti-Hallucination Quality Gate
Tham chiếu quy chuẩn chi tiết tại [manim_masterclass_rules.md](../../rules/manim_masterclass_rules.md):
1. **1 Episode = 1 Isolated Task:** CẤM sản xuất hàng loạt nhiều tập trong 1 phiên hội thoại duy nhất. Khi kết thúc Tập N, agent phải báo cáo kết quả và kết thúc lượt để người dùng/hệ thống khởi tạo Task mới cho Tập N+1 với ngữ cảnh sạch 100%.
2. **Cấm Gian Lận Chuyển Động Giả (Zero Fake Camera Drift / Crop Sway):** TUYỆT ĐỐI CẤM dùng các filter FFmpeg như `crop=...sin(t)...cos(t)` hay `zoompan` để làm rung lắc khung hình nhằm lừa thuật toán phát hiện freeze. Camera phải 100% tĩnh cố định.
3. **Ambient Motion Có Chủ Đích (Zero Fake Carrier Wave):** Chuyển động vi mô phải xuất phát từ hero math entity (tracer dot chạy trên curve, vector xoay phase, gradient particles, opacity pulse). TUYỆT ĐỐI CẤM `FunctionGraph` sine wave chạy dọc đáy, `setup_ambient_hologram_environment()`, và vòng lặp `scale()` co giãn vô nghĩa. Tham chiếu Rule #24 [manim_masterclass_rules.md](../../rules/manim_masterclass_rules.md).
4. **Hiệu Chuẩn Ngưỡng Đóng Băng Vector (`noise=-65dB:duration=4.0s`):** Trong hoạt họa vector nền tối (`#0c0d12`), chuyển động tinh tế của vector chỉ chiếm 1-2% diện tích khung hình (mean $\Delta \approx -68\text{dB}$). Do đó, ngưỡng `noise` của FFmpeg `freezedetect` bắt buộc đặt tại `-65dB` (thay vì `-50dB` hay `-60dB`) để phân biệt chính xác giữa chuyển động toán học thực thụ và đóng băng kỹ thuật số (digital zero freeze).
5. **Cấm FadeOut ra màn hình đen:** Không bao giờ gọi `FadeOut()` toàn bộ mobject ở cuối scene nếu lời thoại vẫn tiếp diễn.
6. **Hard Quality Gate Pre-flight 4 Tầng:** Bắt buộc chạy:
   ```bash
   python3 assets/scripts_video/run_all_quality_gates.py --episode XX
   ```
   Phải đạt 0 Critical trên cả 4 tầng (Kỹ thuật, Bố cục/Typography, Sư phạm/Vật lý, Bản sắc kênh).
7. **Tiêu chuẩn Gold TTS Duy Nhất (V8 Expressive Prosody):** 100% audio lời thoại bắt buộc xử lý qua `vietnamese-expressive-tts` (`vietnamese_expressive_prosody.py` + `prosody_dictionary.json`): khóa nguyên khối từ ghép (Zero-split), bảo vệ biên câu, điều biến 24 Wave ngữ điệu, kẹp trần tốc độ $\le 0.98x$ chống méo tiếng. Cấm đọc phẳng một tốc độ (flat monotone). 1 giọng Zen thuần nhất từ đầu tới cuối, cấm cắt ghép 2 giọng đọc.
8. **Chuẩn mực ngôn ngữ:** 100% "thực tế", 0% "thực chiến"; thuật ngữ tiếng Anh tự nhiên theo ngữ cảnh.
9. **Phân Rã 10-12 Phần Modular (Modular Parts Architecture):**
   - **Tuyệt đối cấm xử lý Monolithic (Nguyên khối):** Mỗi tập phim = 10-12 Parts độc lập (45-90s/part), mỗi Part có kịch bản `.md`, Manim `.py`, audio `.wav` và quality gate riêng.
   - **Micro-Task Isolation:** Agent xử lý tối đa 2 Parts liên tiếp trong 1 micro-session. Context truyền qua `PART_XX_CONTEXT.json`, kết quả ghi vào `PART_XX_RESULT.json`.
   - **Mục tiêu tối thượng:** Tập trung cao độ ngữ cảnh (Context Window Focus, loại trừ trôi dạt/ảo giác), trau chuốt thiết kế chuyển động & kịch bản minh họa từng giây (Artisanal Detailing với ambient motion có chủ đích từ hero math entity), kiểm định chất lượng cục bộ (Granular Quality Gate cho từng Part), và tối ưu hóa bộ nhớ đệm kết xuất Docker (Fail-fast Caching, sửa và render từng Part trong ~30s thay vì cả tập 10 phút).
   - **Tham chiếu chi tiết:** [modular_episode_harness.md](../../rules/modular_episode_harness.md)
10. **Quy Chuẩn Phụ Đề Karaoke & Chống Tràn Chữ Vào Khung Hình (Zero Monolithic Paragraph Dump & Whisper Karaoke Sync):**
    - **CẤM TUYỆT ĐỐI NÉM NGUYÊN KHỐI ĐOẠN VĂN (ZERO MONOLITHIC PARAGRAPH DUMP):** Tuyệt đối cấm lấy toàn bộ lời thoại cả phân cảnh (30–70 từ) ném vào một cue duy nhất chạy suốt 15–25 giây. Lỗi này làm phụ đề bung thành 4–6 dòng chữ choán hết 50% màn hình, che kín đồ thị toán học và đè bẹp các vùng chức năng khác.
    - **GIỚI HẠN DÒNG & SỐ TỪ (LINE & WORD LIMITS):**
      * **16:9 Landscape (2K/1080p):** Tối đa 1–2 dòng (ưu tiên 1 dòng), tối đa 7–10 từ/dòng (dưới 55 ký tự). Thời lượng mỗi cue 1.2s – 3.5s (tối đa $\le 4.5$s). Ngắt theo dấu câu tự nhiên (`.`, `,`, `...`, `—`, `?`, `!`) hoặc nhịp thở giọng đọc.
      * **9:16 Portrait (Shorts):** Bắt buộc 1 dòng duy nhất (max 1 line), tối đa 4–7 từ, căn giữa đáy (Alignment 2).
    - **ĐỒNG BỘ KARAOKE TỪNG TỪ FASTER-WHISPER (FRAME-ACCURATE WHISPER SYNC):** BẮT BUỘC dùng Faster-Whisper GPU (`whisper_aligner.py` / `make_karaoke_subs.py`) trích xuất timestamp chính xác từng từ từ file WAV giọng đọc thật (`scene_*.wav`). Phụ đề karaoke phải sáng từng từ (`{\kf...}`) khớp đúng nhịp phát âm của giọng đọc Zen. Tuyệt đối cấm chia đều thời gian tuyến tính giả lập.
    - **VÙNG AN TOÀN ĐÁY (BOTTOM SUBTITLE EXCLUSION ZONE):** Phụ đề bắt buộc neo sát đáy màn hình ($Y \le -2.60$, MarginV 65–75px), tuyệt đối không để trôi lên giữa màn hình ($Y \in [-2.0, +2.0]$).
    - **AUTOMATED QUALITY GATE AUDIT:** Kiểm toán tự động từ chối bất kỳ file `.srt` / `.ass` nào có cue $> 12$ từ, $> 2$ dòng hoặc thời lượng $> 5.0$s.
11. **CẤM TUYỆT ĐỐI HỘI CHỨNG "SLIDE THUYẾT TRÌNH" & BẮT BUỘC ĐỒ HỌA TOÁN HỌC ÁP ĐẢO (ZERO SLIDE-DECK & >= 75% MATH DOMINANCE):**
    - Nghiêm cấm các phân cảnh chỉ gồm 2–3 thẻ bo tròn (`CalloutBoxCard`, `RoundedRectangle`) chứa gạch đầu dòng văn bản mà không có bất kỳ mobject toán học hình học nào.
    - Mọi phân cảnh bắt buộc phải lấy thực thể hình học toán học làm trung tâm: Hệ trục tọa độ (`Axes`), lưới không gian (`NumberPlane`), đồ thị hàm số (`FunctionGraph`), đường cong tham số (`ParametricFunction`), vector độ dốc (`Vector`), ma trận biến hình (`Matrix`), hoặc mô phỏng xác suất/vật lý. Văn bản chỉ đóng vai trò nhãn phụ trợ (Labels/Context).
12. **CẤM GÁN TỌA ĐỘ GROUP RỖNG & CẤM SƠ ĐỒ KÝ TỰ ASCII (ZERO EMPTY VGROUP MOVE_TO & ZERO ASCII ART):**
    - Cấm triệt để lệnh `hero = VGroup().move_to(...)` trên nhóm rỗng. Mọi đối tượng con bắt buộc được định vị tọa độ tường minh (`.move_to(...)`) trước khi thêm vào nhóm, duy trì khoảng hở an toàn Zone 3 và Zone 4 $\Delta X \ge 0.5$.
    - Cấm đưa sơ đồ văn bản ASCII như `[Input] -> [Embedding] -> Residual Stream` hay `|-> ... -> +|` vào Manim; bắt buộc dựng khối hình học vector thật.
13. **CẤM RÒ RỈ TAG QUẢN LÝ / PIPELINE NỘI BỘ VÀO NỘI DUNG (ZERO PIPELINE TAG LEAKAGE):**
    - Tuyệt đối CẤM đưa các thuật ngữ, mã phiên bản kỹ thuật, hoặc tag quản trị nội bộ của pipeline sản xuất (như `V3`, `V4`, `V5`, `V6`, `V7`, `Quality Gate`, `Pre-flight`, `Pipeline`, `Cue`, `Phase`, `Sprint`, `Ticket`, `Task`, `SHA256`...) vào kịch bản dẫn chuyện, phụ đề, tiêu đề, mô tả hay đồ họa video.
    - Khán giả chỉ quan tâm tới tri thức, bản chất toán học và tinh thần làm nghề thực thụ. Mọi tiêu chuẩn kỹ thuật phải được diễn đạt bằng ngôn ngữ đời thường, chuẩn văn nói tự nhiên và gần gũi (ví dụ: *"những tiêu chuẩn kỹ thuật nghiêm cẩn"*, *"hành trình bền bỉ đi từ gốc rễ toán học"* thay vì *"chuẩn mực V6 khắt khe"*).
    - Toàn bộ metadata nội bộ chỉ nằm trong codebase, test suite, log và tài liệu kỹ thuật, TUYỆT ĐỐI KHÔNG BƯỚC VÀO PHÒNG THU HOẶC KHUNG HÌNH VIDEO.
14. **Golden Brand Trust Boundary (Immutable Pre-Rendered Assets):**
    - Opener (5.80s) và Closing CTA (8.00s) là pre-rendered clips không được tái tạo.
    - Mọi assemble script import `golden_brand_constants.py` và gọi `verify_golden_integrity()` trước khi chạy.
    - SHA-256 hash phải khớp. Nếu thay đổi → chỉ qua human approval.
    - Tham chiếu: [modular_episode_harness.md](../../rules/modular_episode_harness.md#8-golden-brand-immutable-assets-trust-boundary)
15. **BẢO CHỨNG BẰNG CHỨNG THỰC TẾ & NGHIÊM CẤM BỊA ĐẶT ẢO GIÁC (ZERO-FABRICATION & EVIDENCE-FIRST MANDATE):**
    - Tuyệt đối CẤM tự tuyên bố "đã xong", "0 lỗi", "chất lượng tuyệt hảo", hay "đã publish" mà không có bằng chứng số liệu đo đạc thực tế từ công cụ kiểm tra (Ground-Truth Evidence) trong phiên làm việc.
    - Mọi tập phim và phân cảnh trước khi xuất bản bắt buộc vượt qua:
      * Gate Q (Manim Element Collision Detection): 0 va chạm hình học (AABB AST analysis).
      * Gate R (Text Overflow Card Boundary): 0 tràn viền card.
      * Gate O (Broadcast Audio EBU R128): $I \in [-15.5, -13.5]\text{ LUFS}$, True Peak $\le -1.0\text{ dBFS}$, 0 clipped samples.
      * YouTube Publishing: Bắt buộc trả về YouTube Video ID 11 ký tự thật và URL thật trả về từ HTTP 200 API response, kèm liên kết hai chiều hoàn chỉnh giữa Video Dài và 5 Shorts.

## 1. Định Vị Thương Hiệu & Ma Trận 3 Series Trên Kênh ZENPHAM

Kênh **ZENPHAM** được định hình với 3 trụ cột nội dung bổ trợ cho nhau:

```
                          KÊNH ZENPHAM
         (Tư Duy — Công Nghệ — Triết Học — Đời Sống)
                              │
     ┌────────────────────────┼────────────────────────┐
     ▼                        ▼                        ▼
📖 TÔI ĐỌC SÁCH          ⚡ 101 SHORTS          💻 TÔI LÀM VIỆC
(Văn học kinh điển,       (Nghịch lý hiện sinh,    (Nhật ký kỹ sư AI,
 Triết học cổ điển,        Digital minimalism,      Toán học thực tế,
 Tiểu luận 5 hồi 16:9)    Micro-shorts 9:16)       Nghề phần mềm & AI)
```

| Tiêu chí | 📖 Tôi Đọc Sách | ⚡ 101 Shorts | 💻 Tôi Làm Việc (Series Mới) |
| :--- | :--- | :--- | :--- |
| **Chủ đề trung tâm** | Triết học Trang Tử, Khắc kỷ, Hiện sinh qua sách kinh điển | Các khoảnh khắc thức tỉnh, bẫy tiện nghi, màn hình | **Kỹ nghệ AI, toán học máy học, văn hóa kỹ sư & tối ưu hóa hệ thống** |
| **Persona người dẫn** | Học giả mộc mạc, tĩnh lặng, đọc và chiêm nghiệm | Người quan sát xã hội sắc sảo, đĩnh đạc | **Zen: Kỹ sư thực thi điềm tĩnh, chia sẻ từ hiện trường phòng lab đêm** |
| **Định dạng chính** | Longform 10–15 phút (16:9) | Shorts 60s–90s (9:16) | **Hybrid: Video phân tích chuyên sâu 3–8 phút (16:9) + Tech Shorts 60s–90s (9:16)** |
| **Visual đặc trưng** | Thư phòng ấm, trang sách cũ, tách trà, ánh nắng | Phố xá mưa đêm, silhouette bóng tối, neon mờ | **Bàn làm việc minimalist, code terminal, máy chủ + Đồ họa toán học Manim (Python)** |
| **Âm thanh** | Tiếng mưa, lật sách, piano mộc acoustic | Piano một nốt kéo dài, low-fi tối giản | **Ambient Synth & Piano sâu lắng, âm thanh bàn phím cơ gõ nhẹ, broadcast -14 LUFS** |
| **Brand Pill Cover** | `📖 TÔI ĐỌC SÁCH` (Sage Green) | `🔴 ZENPHAM` (Ruby Red) | `🔴 ZENPHAM • TÔI LÀM VIỆC` (Ruby Red & Platinum) |

---

## 2. Tinh Thần Cốt Lõi: Tìm Kiếm Sự Thú Vị & Vẻ Đẹp Toán Học (Wonder & System Elegance)

Series **"Tôi Làm Việc"** được xây dựng trên những nguyên tắc bất biến:
- **Hướng tới người xem yêu thích sự thú vị (Sense of Wonder & Fascination)**:
  - Khán giả không phải là những chuyên gia nghiên cứu sâu đi tìm tài liệu học thuật khô cứng, mà là những người yêu khoa học, tò mò về thế giới và đi tìm cảm hứng từ những điều kỳ diệu ẩn sau công nghệ.
  - Cách dẫn dắt phải khơi gợi cảm giác "Aha! Hóa ra tự nhiên và toán học lại vận hành kỳ diệu như vậy!", tương tự phong cách của 3Blue1Brown, Veritasium hay Steve Mould.
- **Văn phong nhẹ nhàng, điềm tĩnh và khách quan (Gentle, Objective & Anti-Melodrama)**:
  - **CẤM TUYỆT ĐỐI các sáo ngữ giật gân, melodrama**: Không dùng các cụm từ sáo rỗng như *"lúc 2 giờ sáng"*, *"3 giờ sáng"*, *"sự thật tàn nhẫn"*, *"cú tát vào mặt"*, *"cỗ máy lạnh lùng"*, *"nhà toán học lạnh lùng"*, *"sự đánh đổi khốc liệt"*, *"thực chiến"*.
  - **CẤM TUYỆT ĐỐI mở đầu sáo rỗng (Blacklist Openings)**: Cấm *"Có bao giờ bạn tự hỏi..."*, *"Bạn có biết rằng..."*, *"Hãy tưởng tượng..."*, *"Trong thế giới ngày nay..."*. Bắt buộc dùng 1 trong 5 Opening Archetypes kỹ thuật (The Glitch, The Counter-Intuitive Truth, The Micro-Mechanism, The Engineering Dilemma, The Quiet Shift).
  - **CẤM TUYỆT ĐỐI kết thúc thuyết giáo (Blacklist Endings)**: Cấm biến đoạn kết thành bài thuyết pháp *"Đạo làm nghề..."*, *"người thợ thủ công số"*, *"bài học triết học sâu sắc"*. Bắt buộc dùng 1 trong 5 Ending Archetypes khoa học (The Quiet Precision, The Open Frontier, The Hard Trade-off, The Codebase Echo, The Invisible Infrastructure).
  - Dùng câu văn trong sáng, thanh thản, gãy gọn, giàu hình ảnh thị giác và ẩn dụ đời thường. Người dẫn chuyện như một người bạn đồng hành cùng ngồi quan sát thế giới, nhẹ nhàng lật mở từng lớp bí mật của cỗ máy.
- **Humble Persona — Không tự đánh bóng, Không nhắc tên cá nhân/công ty**:
  - **CẤM TUYỆT ĐỐI** các câu thoại tự xưng: *"Tôi là Zen, 10 năm làm nghề..."*, *"Tại công ty chúng tôi..."*.
  - Nhập vai người quan sát khách quan ("chúng ta", "khi nhìn sâu vào cỗ máy", "hãy quan sát hiện tượng"). Uy tín của video toát ra từ sự tao nhã của hình ảnh Manim và sự sáng tỏ của tri thức.
- **Trực giác hình học thay vì công thức khô cứng (Geometry-First)**:
  - Không ném một chuỗi phương trình đại số phức tạp vào tai người nghe. Biến mọi khái niệm toán học thành những chuyển động hình học trực quan, thanh thoát, dễ hiểu đối với bất kỳ ai có lòng tò mò.
- **Quy tắc Giãn cách Thuật ngữ TTS (Term Cooldown)**:
  - Thuật ngữ tiếng Anh chỉ xuất hiện tối đa 1 lần/câu và tối đa 2 lần/phân cảnh. Các câu tiếp theo bắt buộc dùng đại từ thay thế tiếng Việt (`thuật toán này`, `hàm số trên`, `bộ lọc đó`).
  - Cấm lặp từ nối giải thích (`tức là`, `nói cách khác` tối đa 1 lần/cảnh). Cấm ngoặc kép `"..."`, cấm gạch ngang đầu dòng hoặc giữa câu.
  - Xem tài liệu quy chuẩn chi tiết tại `assets/scripts_video/MASTER_SCRIPT_PROMPT.md`.

---

## 3. Hai Định Dạng Sản Xuất Chuẩn

### A. Long-Form Essay (16:9 — TỐI THIỂU 2K QHD 2560x1440 — 3 đến 8 phút)

- **Cấu trúc 4 Nhịp Khám Phá (The 4-Quadrant Narrative)**:
  1. **Q1: Điều kỳ diệu & Sự tò mò tự nhiên (The Wonder / Question — 30–45s)**: Mở đầu bằng một câu hỏi trực quan, gợi mở sự tò mò (Ví dụ: *"Tại sao một vòng tròn xoay đều lại vẽ nên những con sóng biển, và giấu trong mình âm hưởng của vạn vật?"*).
  2. **Q2: Giải phẫu Thị giác Manim (The Visual Intuition — 90–150s)**: Dùng đồ họa chuyển động Manim để người xem "nhìn thấy" ý niệm toán học chuyển động tự nhiên trước mắt.
  3. **Q3: Sự kết nối với đời sống & Công nghệ (The Connection — 45–60s)**: Cách quy luật toán học ấy âm thầm vận hành trong những cỗ máy thông minh quanh ta.
  4. **Q4: Lắng đọng & Chiêm nghiệm (The Gentle Reflection — 30–45s)**: Một khoảng lặng nhẹ nhàng về mối liên hệ giữa con người, tự nhiên và công nghệ.
- **Cơ cấu hình ảnh — Manim Áp Đảo & Chuẩn Tối Thiểu 2K QHD (>= 75% Manim Dominant @ 2K QHD)**:
  - `75% - 85%`: **Đồ họa toán học Manim 2K QHD (2560x1440 @ 60fps) thanh thoát, trực quan** (Đường tròn, vector quay, sóng hình sin, lưới không gian biến hình, quang phổ ánh sáng).
  - `10% - 15%`: **B-roll Tech Minimalist tinh tế** (Bàn làm việc gọn gàng, tách trà, phím gõ nhẹ, màn hình hiển thị trang nhã).
  - `5% - 10%`: **Khoảng lặng chuyển cảnh (Negative Space)** (Ánh sáng tự nhiên qua ô cửa, giọt nước rơi nhẹ, nhịp thở thư thái).

### B. Micro-Shorts Phễu Kéo Traffic & Liên Kết Hai Chiều (The 30s–50s Funnel)

- **Thời lượng chuẩn xác: 45s – 55s**:
  - **Nhịp 1: The Curious Hook (0 – 10s)**: Đặt ra một câu hỏi nhẹ nhàng nhưng khơi gợi trí tò mò mạnh mẽ về thế giới số.
  - **Nhịp 2: The Visual Spotlight (10 – 40s)**: Hoạt họa Manim trực quan, dễ hiểu nhất, tạo cảm giác "Aha!" ngay lập tức.
  - **Nhịp 3: High-Impact Call-To-Action (40 – 50s)**: Thẻ CTA nhã nhặn, hướng dẫn người xem bấm vào nút "Video liên quan" để xem bản chứng minh đầy đủ.

> [!CAUTION]
> **QUY TẮC BẤT DI BẤT DỊCH VỀ CẤU TRÚC & FOOTAGE SHORTS 30S:**
> 1. **Thứ tự bắt buộc: Hook (0-7.5s) → Manim Spotlight (7.5-21.5s) → Studio CTA Card (21.5-30s)**:
>    - CTA Card và Voice CTA **TUYỆT ĐỐI LUÔN Ở CUỐI CÙNG (Nhịp 3)**.
>    - Nghiêm cấm mọi lỗi mapping âm thanh khiến giọng CTA (`scene_03.wav`) phát ra từ 0s hoặc đảo clip CTA lên đầu.
> 2. **Footage độc lập cho từng tập — Nghiêm cấm dùng trùng lặp (Zero Reuse)**:
>    - **Tập 1**: Footage đồng xu kim loại xoay chậm (`clips_raw/zenpham_ban_chat_xac_suat_ai/raw_1.mp4`).
>    - **Tập 2**: Footage kỹ sư trực đêm trước màn hình terminal (`clips_raw/zenpham_toi_lam_viec_tap_02_gradient_descent/raw_1.mp4`).
>    - **Tập 3**: Footage bionic hand & CRT monitor matrix độc lập (`assets/footage_pool/clips/pool_7689156_03.mp4`).
>    - **Tập 4**: Footage giọt mưa đêm trên kính cửa sổ độc lập (`assets/footage_pool/clips/pool_14156117_05.mp4`).
>    - **Tập 5**: Footage cyberpunk terminal RANDOMIZE (`assets/footage_pool/clips/pool_5377775_01.mp4`).

- **Hệ Thống Tự Động SEO & Liên Kết Hai Chiều (Bi-Directional Content Flywheel)**:
  1. **Tự Động Tạo SEO (Mobile-First SEO Engine)**:
     - *Shorts Title*: Rút gọn dưới 55 ký tự, giữ trọn Hook cảm xúc + gắn thẻ `#Shorts` (Ví dụ: `CỖ MÁY MÒ MẪM TRONG BÓNG TỐI? #Shorts`).
     - *Shorts Description*: Đặt đường dẫn trực tiếp đến tập 16:9 ngay 3 dòng đầu tiên (`👉 XEM BẢN ĐẦY ĐỦ: https://youtube.com/watch?v={LONG_ID}`).
     - *Longform Description*: Tự động bổ sung backlink xem nhanh (`📱 Xem tóm tắt nhanh 30s của tập này: https://youtube.com/shorts/{SHORT_ID}`).
  2. **Bộ Công Cụ Điều Phối Tự Động (`assets/scripts_video/seo_shorts_linker.py`)**:
     - *Xem trước kết nối SEO*:
       ```bash
       python3 assets/scripts_video/seo_shorts_linker.py preview \
         --long-md assets/scripts_video/zenpham_toi_lam_viec_tap_XX.md \
         --short-md assets/scripts_video/zenpham_toi_lam_viec_tap_XX_short_30s.md \
         --long-id <LONG_ID>
       ```
     - *Upload Short và Tự Động Đồng Bộ Liên Kết Hai Chiều*:
       ```bash
       python3 assets/scripts_video/seo_shorts_linker.py upload-short \
         --short-video assets/scripts_video/zenpham_toi_lam_viec_tap_XX_short_30s_master.mp4 \
         --short-md assets/scripts_video/zenpham_toi_lam_viec_tap_XX_short_30s.md \
         --long-id <LONG_ID> \
         --thumbnail assets/scripts_video/output/short_cta_card.png \
         --channel ZENPHAM
       ```
  3. **YouTube Related Video (Studio Setup)**:
     Sau khi Short được upload, vào YouTube Studio -> Chi tiết Short -> Mục **"Video có liên quan" (Related video)** -> Chọn video dài tương ứng để hiển thị nút xem video dài trực tiếp trên điện thoại.
  4. **Anti-Skew Pipeline**: BẮT BUỘC dùng `scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920`.

---

## 4. Quy Chuẩn Kỹ Thuật Đồ Họa Manim (Median / 3Blue1Brown Style)

> **📦 Premium Component Library**: Xem skill **`manim-production`** để sử dụng hệ thống Manim Production System bao gồm:
> - 10 Premium Components (DiagramCard, ComparisonPanel, TensorDiagram, FlowChart, NeonArrow, EquationBox, ...)
> - Layout Constraint Engine (`safe_place()` — chống đè lấp tự động)
> - Voice-Sync Timeline (đồng bộ animation với audio TTS)
> - SFX/VFX Integration (8 loại sound effects + visual effects)
> - 📚 **References**: [10 Visual Paradigms](file:///home/zen/hermes-agent/.agents/skills/manim-production/references/ai_math_visual_paradigms.md) | [VFX & Choreography](file:///home/zen/hermes-agent/.agents/skills/manim-production/references/visual_effects_and_choreography.md) | [Layout & Typography](file:///home/zen/hermes-agent/.agents/skills/manim-production/references/layout_and_typography.md) | [Scriptwriting & Voice-Sync](file:///home/zen/hermes-agent/.agents/skills/manim-production/references/scriptwriting_workflow.md)
>
> Module: `assets/scripts_video/manim_production.py` — import trực tiếp vào scene files.

Mọi cảnh hoạt họa thuật toán trong "Tôi Làm Việc" phải tuân thủ bảng thiết kế trực quan:
- **Tỷ lệ & Độ phân giải chuẩn:** 16:9 — **TỐI THIỂU 2K QHD (2560x1440 @ 60fps)** cho Video Essay, 9:16 (1440x2560 2K QHD hoặc 1080x1920) cho Shorts.
- **Background**: Tối sâu Neo-noir (`#0c0d12` hoặc `#0f111a`), không dùng màu đen tuyền `#000000` gắt.
- **Bảng màu đồ họa**:
  - Primary Accent: Xanh ngọc Cyan (`#00f0ff` hoặc `#34d399`) — Đại diện cho dữ liệu, luồng tính toán.
  - Secondary Accent: Hổ phách Amber / Cam ấm (`#f59e0b` hoặc `#fbbf24`) — Đại diện cho trọng số, điểm chú ý.
  - Text Label: Dùng `Text(..., font="sans-serif")` qua Pango engine để hỗ trợ tiếng Việt đầy đủ dấu.
  - Math Label: Dùng `MathTex(r"...")` với ký hiệu toán thuần TeX ($\theta, \mathcal{L}, \nabla, W^T x$).

### 💎 QUY CHUẨN BRAND KIT ZENPHAM & OPENER SCENE (BẮT BUỘC)
Để tăng độ nhận diện, xác lập bản quyền tác giả và nâng tầm uy tín như các kênh lớn quốc tế (3Blue1Brown, Median, Veritasium, StatQuest):

1. **5.80s Logo Opener Bumper (Nhận diện thương hiệu mở đầu)**:
   - **Asset chuẩn hóa**: `assets/brand/zenpham-brand-kit/zenpham_opener_clip_1080p30.mp4` (hoặc bản upscale Lanczos 2K, đúng 5.800s).
   - **Vị trí chèn**: Ngay sau **Scene 1 (Cold Open / Hook)** và trước khi bắt đầu **Scene 2 (Nội dung chính)**. Tuyệt đối không đặt ở 0s để tối ưu hóa tỷ lệ giữ chân người xem (Viewer Retention).
   - **Âm thanh Opener**: Sử dụng tiếng chime thương hiệu độc quyền từ `assets/brand/zenpham-brand-kit/zenpham_opener_audio.wav`. BGM tự động ducking sâu xuống `volume=0.02` (-24dB) trong suốt 5.80s Opener.
   - **Bumper sạch**: Trong 5.80s Opener, khung hình phải sạch 100% — **KHÔNG đè watermark, KHÔNG phụ đề**.

2. **Subtle Warm Ivory Watermark (Watermark Ngà Ấm Mờ 28%)**:
   - **Asset**: `assets/brand/zenpham-brand-kit/zenpham_subtle_watermark_150px.png` (bản màu ngà ấm `#F6F0E4`, độ mờ 28% trong suốt tinh tế trên nền dark obsidian `#0c0d12`).
   - **Vị trí**: Góc trên bên phải (**Top-Right**: `overlay=W-w-80:80` cho 2K QHD, hoặc `W-w-60:60` cho 1080p), lùi vào để tuân thủ 15% safe margin.
   - **Phạm vi hiển thị**: Xuất hiện xuyên suốt các phân cảnh B-roll và Manim, **TẮT hoàn toàn trong 5.80s Opener**.

3. **Đồng Bộ Phụ Đề & Chapters (+5.80s Time-Shift)**:
   - Toàn bộ thời gian bắt đầu của Scene 2 trở đi được tịnh tiến chính xác `+5.80s`.
   - Phụ đề `.srt` và YouTube chapters trong `description.txt` được dịch chuyển tự động qua module `brand_integrator.py`:
     ```python
     from brand_integrator import shift_srt_for_opener, calculate_branded_scene_start_times
     ```
   - Chèn chapter chuẩn: `mm:ss - [ZENPHAM] Giới thiệu thương hiệu & Triết lý`.

### 🛡️ QUY CHUẨN AN TOÀN BỐ CỤC MANIM: 15% SAFE MARGIN & ZERO TEXT OVERFLOW
Nhằm đảm bảo 100% không bao giờ bị phụ đề CC, watermark hay thanh điều khiển video che lấp:
1. **Quy tắc Safe Padding 15% ở 4 phía**:
   - **Đáy màn hình (Bottom $Y \ge -2.6$, `buff \ge 1.2`)**: BẮT BUỘC chừa trống tối thiểu 15% chiều cao khung hình cho phụ đề phụ đề (Subtitle CC). Không đặt bất kỳ text, phương trình hay đồ thị nào xuống vùng đáy này.
   - **Đỉnh màn hình (Top $Y \le +2.6$, `buff \ge 1.0`)**: Chừa trống tối thiểu 15% chiều cao để không chạm Watermark góc trên bên phải.
   - **Hai biên trái phải ($-4.8 \le X \le +4.8$)**: Nội dung đồ họa phải cách mép viền tối thiểu 15% chiều rộng (2.13 units).
2. **Quy tắc Zero Text-Out-of-the-Box**:
   - Nghiêm cấm tạo hộp kích thước cố định nhỏ hơn text khiến chữ bị tràn/chòi ra ngoài viền (Out of the box).
   - Mọi hộp code/text BẮT BUỘC dùng `SurroundingRectangle(text_mob, buff=0.30, corner_radius=0.15, ...)` để viền tự động ôm trọn chữ với lề đệm sang trọng.
3. **Compositing Filter trong FFmpeg (Chuẩn 2K QHD)**:
   - Khi ghép clip Manim vào video Master 2K QHD, luôn dùng bộ lọc đệm 15% an toàn với tỷ lệ hoàn hảo:
     `scale=1792:1008:force_original_aspect_ratio=decrease,pad=2560:1440:(2560-iw)/2:(1440-ih)/2:color=#08090e` (hoặc cho canvas 1080p: `scale=1344:756:force_original_aspect_ratio=decrease,pad=1920:1080:(1920-iw)/2:(1080-ih)/2:color=#08090e`)

### 🗄️ KHO LƯU TRỮ & TÁI SỬ DỤNG MANIM FOOTAGE (MANIM FOOTAGE VAULT)
Toàn bộ các phân cảnh hoạt họa Manim sau khi render được tự động lưu trữ, đánh chỉ mục và bảo tồn tập trung tại:
- **Thư mục lưu trữ**: `assets/manim_library/footage/` (phân loại theo `tap_01/`, `tap_02/`, `tap_03/`, `common/`).
- **File chỉ mục metadata**: `assets/manim_library/footage/manim_footage_registry.json`.
- **Nguyên tắc tái sử dụng**:
  - Không bao giờ xóa các file render Manim hoàn chỉnh.
  - Khi làm các tập mới, video tổng hợp (Masterclass), hay video Shorts 30s phễu, hệ thống ưu tiên tìm kiếm và tái sử dụng footage Manim từ kho lưu trữ qua lệnh:
    ```bash
    python3 assets/scripts_video/manim_footage_vault.py index
    ```

### 🎬 KỸ THUẬT GHÉP NHIỀU LỚP MANIM ĐỂ TĂNG VISUAL (MULTI-MANIM LAYERING)
Để tối đa hóa mật độ thông tin thị giác (Visual Density) và giữ chân người xem (High Retention), những phân đoạn giải thích toán học phức tạp cần áp dụng kỹ thuật lồng ghép nhiều hoạt họa Manim trong cùng một cảnh:
1. **Kỹ thuật Split-Screen (Two-Pane Math Canvas)**:
   - Chia đôi khung hình: Bên trái là không gian 3D (3D manifold / Loss surface / Vector Space), bên phải là đồ thị 2D hoặc biểu thức toán học tương ứng, ngăn cách bởi vệt sáng neon phát quang (`#00f0ff` hoặc `#ffd166`).
   - Lệnh thực thi:
     ```bash
     python3 assets/scripts_video/manim_footage_vault.py split \
       --left path/to/scene_3d.mp4 \
       --right path/to/scene_2d.mp4 \
       --out path/to/composite_split.mp4
     ```
2. **Kỹ thuật Picture-in-Picture (PiP / Holographic Inset Card)**:
   - Hoạt họa nền 3D toàn cảnh làm background; góc dưới bên phải hoặc góc trái đặt một thẻ bài hoạt họa bổ trợ (như đồ thị so sánh thuật toán, bảng ma trận Attention) với viền bo góc phát sáng drop-shadow.
   - Lệnh thực thi:
     ```bash
     python3 assets/scripts_video/manim_footage_vault.py pip \
       --bg path/to/main_3d_space.mp4 \
       --pip path/to/inset_formula.mp4 \
       --pos bottom_right \
       --out path/to/composite_pip.mp4
     ```
3. **Kỹ thuật Dynamic Montage (Micro-Cut Sequence)**:
   - Trong một phân đoạn dài 15–25s, không để người xem nhìn một góc máy tĩnh. Ghép 2–3 góc nhìn Manim khác nhau (Toàn cảnh 3D $\to$ Cận cảnh vector $\to$ Biến đổi ma trận) luân phiên nhau với nhịp cắt 4–5 giây/cảnh.
   - Lệnh thực thi:
     ```bash
     python3 assets/scripts_video/manim_footage_vault.py montage \
       --clips clip1.mp4 clip2.mp4 clip3.mp4 \
       --durs 5.0 5.0 6.0 \
       --out path/to/composite_montage.mp4
     ```

### 📐 QUY CHUẨN CHẶT DÒNG THÔNG MINH & CHỐNG MẤT CHỮ (SMART TEXT & SAFE BOUNDS)
> [!IMPORTANT]
> **TRIỆT TIÊU LỖI MẤT CHỮ & TRÀN VIỀN:** Trong Manim, chuỗi Text dài không được tự động xuống dòng và thường bị tràn ra ngoài khung camera (đặc biệt khi cắt Split-Screen hoặc xem trên điện thoại). Mọi tiêu đề và chú thích phải tuân thủ chuẩn chặt dòng thông minh:
1. **Sử dụng bộ công cụ `manim_smart_text.py`**:
   - `smart_wrap_vn(text, max_chars=30)`: Tự động phát hiện dấu ngắt logic (`:`, `—`, `→`, `,`), phân bổ độ dài các dòng cân xứng, triệt tiêu hiện tượng chữ mồ côi (orphan word) lẻ loi ở dòng cuối.
   - `SmartText(text, max_chars=32, max_width=12.0)`: Tự động xuống dòng và tự động co tỉ lệ (`scale_to_fit_width`) nếu vượt quá giới hạn an toàn.
   - `SmartHeader(title, subtitle)`: Tạo cụm tiêu đề + phụ đề chuẩn typography 2 tầng không bao giờ chạm mép màn hình.
2. **Quy chuẩn chiều rộng an toàn (Safe Boundary Units)**:
   - Khung hình 16:9 Full Screen: `max_width = 12.0` (cách mép tối thiểu 1.1 đơn vị Manim).
   - Khung hình Split-Screen (Chia đôi): `max_width = 5.6` đơn vị mỗi bên.
   - Khung hình 9:16 Shorts (Dọc): `max_width = 6.8` đơn vị.

### ⚡ QUY CHUẨN VISUAL FX & SOUND FX CHO MANIM (MANIM VFX & SFX STUDIO)
Để đạt đẳng cấp truyền cảm hứng như 3Blue1Brown, Median và Veritasium, hoạt họa Manim không chỉ có chuyển động hình học câm, mà phải kết hợp hiệu ứng thị giác và âm thanh tương tác:
1. **Bộ Hiệu Ứng Thị Giác (VFX Guidelines)**:
   - **Glowing Neon Stroke**: Mũi tên vector và đường đồng mức quan trọng được render 3 tầng stroke (Lõi trắng sáng `#ffffff` nằm trên hào quang cyan `#00f0ff` bán trong suốt) tạo cảm giác laser viễn tưởng.
   - **Glassmorphism Backdrop**: Đặt công thức phức tạp vào thẻ bài kính mờ bo góc (`GlassCard`) màu đen obsidian `#08090d` viền cyan mỏng.
   - **Eureka Flash**: Khi nghiệm toán học hội tụ hoặc Cosine đạt cực đại, phát xung ánh sáng bùng nổ (`Flash` + `Indicate`) tỏa ra từ tâm điểm.
2. **Bộ Âm Thanh Tương Tác (SFX Studio)**:
   - Tạo sẵn 5 âm thanh toán học đặc trưng tại `assets/scripts_video/sfx/`:
     - `whoosh`: Khi mũi tên vector vươn dài hoặc góc máy 3D xoay lướt.
     - `pop` / `blip`: Khi các điểm dữ liệu rời rạc hoặc nút mạng xuất hiện.
     - `impact`: Âm trầm sub-bass khi đại định lý hoặc công thức xuất hiện.
     - `shimmer`: Tiếng chuông cộng hưởng huyền ảo khi nghiệm hội tụ hoàn hảo.
   - **Lệnh tự động mix SFX vào video Manim**:
     ```bash
     python3 assets/scripts_video/manim_fx_engine.py \
       --video path/to/manim_raw.mp4 \
       --out path/to/manim_with_sfx.mp4 \
       --cues whoosh:0.5 pop:1.8 shimmer:3.5
     ```

Các mẫu Manim có sẵn tại `skills/creative/toi-lam-viec/references/manim_templates.py`:
- `LossLandscapeScene`: Đồ thị gradient descent trượt trên bề mặt hàm mất mát.
- `BayesianBeliefScene`: Phân phối Gauss Prior cập nhật thành Posterior khi nhận dữ liệu mới.
- `SoftmaxTokenBarScene`: Biểu đồ phân phối xác suất từ tiếp theo trong LLM.
- `NeuralAttentionFlowScene`: Ma trận Attention mechanism kết nối các token ngữ cảnh.
- `VectorEmbeddingSpaceScene`: Vũ trụ vector đa chiều 1536 chiều chiếu xuống không gian 3D.
- `VectorArithmeticScene`: Phép toán ý niệm King - Man + Woman = Queen.
- `CosineSimilarityScene`: Tích vô hướng và góc kẹp Cosine đo mức độ đồng điệu ngữ nghĩa.
- `AttentionProjectionScene`: Chiếu không gian Query - Key - Value trong Transformer.

---

## 5. Hệ Thống Giọng Đọc & Âm Thanh

> [!IMPORTANT]
> **CHỐT QUY CHUẨN GIỌNG ĐỌC KÊNH ZENPHAM (MANDATORY INVARIANT):**
> - **Voice Model**: `Zen Mien Tay (Zen Meditation)` (File gốc: `assets/voices/Zen Mien Tay/zenpham-zen-meditation-mientay.wav`, transcript: `zenpham-zen-meditation-mientay.txt`, catalog OmniVoice: `Zen Mien Tay/zenpham-zen-meditation-mientay`).
> - **Định luật Đơn Giọng Thuần Khiết (Monolingual Voice Invariant — 100% 1 Giọng Duy Nhất)**:
>   - **TUYỆT ĐỐI CẤM** việc cắt từ tiếng Anh/thuật ngữ kỹ thuật đưa sang một voice model thứ 2 đọc rồi ghép lại (Bilingual Splitting / Splicing).
>   - *Lý do thực nghiệm*: Việc cắt ghép 2 giọng đọc khác nhau (dù áp dụng carrier prompting, crossfade hay LUFS matching) vẫn tạo ra xung đột âm sắc (timbre clash), làm vấp nhịp thở tự nhiên và phá hủy hoàn toàn cảm xúc tĩnh tại, liền mạch của người nghe.
>   - Toàn bộ nội dung kịch bản (kể cả thuật ngữ kỹ thuật, code-switching tiếng Anh) **BẮT BUỘC do 1 giọng Zen Miền Tây duy nhất đọc xuyên suốt từ đầu tới cuối**.
> - **Tốc độ đọc chuẩn (Calibrated Speed)**: **`0.94x`** (Bắt buộc cho toàn bộ nội dung tiếng Việt của kênh ZENPHAM, bao gồm video phân tích chuyên sâu 16:9 "Tôi Làm Việc" và Tech Shorts 9:16). Nhịp 0.94x đảm bảo sự điềm tĩnh, suy tưởng, đĩnh đạc, rõ nét từng âm vị toán & kỹ thuật, tạo khoảng trống chiêm nghiệm cho người xem.
> - **Engine TTS Mặc Định (Default Synthesizer)**: **V8 Enhanced VieNeu-TTS** (VieNeu-TTS v3 Turbo 48kHz Streaming kết hợp Chuỗi Master Giọng Đọc 5 Giai Đoạn - Studio Vocal Mastering Chain: Highpass 80Hz, De-mud EQ 300Hz, Presence EQ 3.8kHz, Air Treble 9kHz, EBU R128 Loudnorm -15 LUFS). GPU OmniVoice (F5-TTS 24kHz) giữ vai trò dự phòng thứ cấp (Secondary Fallback).
> - **Profile âm thanh**: Tiêu chuẩn âm thanh phòng thu **48000 Hz Stereo**, EBU R128 `loudnorm=I=-14.5:LRA=7:TP=-1.5` kết hợp 5-Stage Studio Vocal Mastering Chain.

### 🎵 QUY TẮC NHẠC NỀN (BGM) — BẮT BUỘC DÙNG NHẠC CHÍNH CHỦ, NGHIÊM CẤM BẢN QUYỀN
> [!CAUTION]
> **NGHIÊM CẤM SỬ DỤNG `soft_piano_ambient.mp3`:**
> Tuyệt đối KHÔNG sử dụng `soft_piano_ambient.mp3` trong bất kỳ scene nào (từ scene đầu, hook, tới toàn bộ video dài hay Shorts) vì file này bị YouTube quét bản quyền (Copyright Strike/Claim).
> 
> **BẮT BUỘC sử dụng kho nhạc nền chính chủ độc quyền tại `assets/background_music/living - lifestyle/`**:
> - `Quiet Room Glow (1).mp3` (hoặc bản gốc 120s): Giai điệu mộc mạc, tĩnh lặng, ấm áp, hoàn hảo cho chiêm nghiệm, triết học AI và các phân đoạn suy tư.
> - `Velvet After Hours.mp3`: Phong cách Neo-noir, đêm muộn, phòng lab công nghệ, thích hợp cho không gian màn hình tối, code terminal, trực quan hóa toán học 3D.
> - `Loop in Glass.mp3`: Ambient tuần hoàn tối giản 60s, hoàn hảo cho định dạng Shorts 9:16 (30s).
> - `Morning After Rain.mp3`: Trong trẻo, thanh bình cho phần mở đầu hoặc lắng đọng kết bài.
> - `Small Steps Bloom.mp3`: Tinh tế, truyền cảm hứng cho khoảnh khắc eureka hoặc đúc kết 10 năm làm nghề.
> 
> **Thông số chuẩn mix nhạc nền**:
> - Gain: `volume=0.10` đến `0.15` (âm lượng nhỏ hơn lời thoại từ `-20dB` đến `-24dB`).
> - Fade in: 1.0s ở đầu video; Fade out: 2.0s đến 3.0s ở cuối video.

### 🎙️ QUY TẮC PHÁT ÂM THƯƠNG HIỆU: ZENPHAM → "ZEN PHẠM" (BẮT BUỘC)
- Trong toàn bộ kịch bản và nội dung đưa vào bộ đọc TTS (Text Content), từ khóa thương hiệu `ZENPHAM` **BẮT BUỘC luôn được chuyển đổi hoặc viết thành `Zen Phạm`** (có dấu cách và thanh nặng).
- Tuyệt đối không để nguyên khối `ZENPHAM` khi đưa vào engine TTS để tránh giọng đọc bị ngọng hoặc đọc thành âm tiếng Anh lướt ("Zen-phăm"). Bộ tiền xử lý `vietnamese_prosody.py` và `tts_zen.py` đã tự động ép chuẩn quy tắc này.

### 🔬 QUY TẮC PHÁT ÂM THUẬT NGỮ KỸ THUẬT & TOÁN HỌC (BẮT BUỘC ĐỌC CHUẨN XÁC)
Đối với video chuyên sâu về AI & Toán học kỹ thuật ("Tôi Làm Việc"), giọng đọc cần toát lên sự chuẩn xác, tự nhiên khi code-switching giữa tiếng Việt và tiếng Anh. **Không** phiên âm các thuật ngữ kỹ thuật sang tiếng Việt — TTS engine hiện đại đọc nguyên bản tiếng Anh tốt hơn bất kỳ bảng phiên âm thủ công nào. Chỉ can thiệp theo 4 nhóm sau:
1. **Acronyms kỹ thuật — giữ spelling, không tự ý chèn khoảng trắng**:
   - Giữ nguyên `NaN`, `SGD`, `GPU`, `CPU`, `TPU`, `LLM`, `API`, `ReLU`, `PCA`, `MSE`, `MAE` trong Vocal Script.
   - Không tự động đổi thành `N a N`, `L L M`, `G P U` hoặc một dạng phiên âm khác. Chỉ thay spoken form sau khi A/B đúng ngữ cảnh đã được người duyệt chấp thuận và ghi vào term registry.
   - Acronym là nhóm rủi ro phát âm cao; bắt buộc chạy `tts_code_switch_risk.py` trước synthesis.
2. **Ký hiệu toán học & đại lượng — Đọc đúng nghĩa, không đọc ký tự**:
   - `∇` (nabla): Đọc là `"nabla"` hoặc `"gradient"`, không đọc thành "tam giác ngược".
   - `θ` (theta): Đọc là `"theta"`, không đọc thành "ô".
   - `σ` (sigma): Đọc là `"sigma"`.
   - `μ` (mu): Đọc là `"mu"`.
   - `ε` (epsilon): Đọc là `"epsilon"`.
   - `∂` (partial): Đọc là `"đạo hàm riêng"` hoặc `"partial"`.
   - `∑` (summation): Đọc là `"tổng"` hoặc `"sigma lớn"`.
   - `∏` (product): Đọc là `"tích"`.
   - `→` / `↦`: Đọc là `"ánh xạ tới"` hoặc `"maps to"`.
   - `∈`: Đọc là `"thuộc"`.
   - `‖x‖`: Đọc là `"norm x"` hoặc `"chuẩn x"`.
   - `log` / `ln`: Đọc là `"logarit"` / `"lô-ga-rít tự nhiên"`.
   - `argmin` / `argmax`: Đọc là `"ác-min"` / `"ác-mác"`.

3. **Tên riêng & thuật ngữ kỹ thuật — Giữ nguyên, KHÔNG phiên âm**:
   - Các tên như Gradient, Transformer, Embedding, Attention, Softmax, PyTorch, TensorFlow, Fine-tuning, Inference, v.v. được **đọc nguyên bản tiếng Anh** bởi TTS engine.
   - **Không** chuyển đổi sang phiên âm tiếng Việt (ví dụ: KHÔNG viết "gờ-ra-đi-ân" cho Gradient, KHÔNG viết "Tran-sơ-pho-mơ" cho Transformer).
   - Khả năng code-switching phụ thuộc model, voice và ngữ cảnh; không mặc định engine sẽ luôn đọc đúng nếu chưa nghe evidence.

4. **Neo ngữ pháp tiếng Việt phải được viết ngay trong Vocal Script**:
   - Không mở câu hoặc mở một mệnh đề mới bằng thuật ngữ tiếng Anh trần nếu có cách diễn đạt tự nhiên hơn.
   - Đặt thuật ngữ trong một khung ngữ pháp Việt có nghĩa: `mô hình LLM`, `phương pháp PCA`, `hàm Softmax`, `độ calibration`, `chỉ số MSE`, `thuật toán Backpropagation`, `quá trình training`.
   - Neo phải đúng nghĩa chuyên môn; không thêm từ đệm chỉ để đánh lừa linter. Giữ nguyên chính tả và casing của thuật ngữ.
   - Mỗi scene là đúng một utterance `lang=vi`; không viết câu dịch tiếng Anh lặp lại, không dùng `<en>`, không tách thuật ngữ sang voice hoặc WAV khác.
   - Sau vòng rewrite cuối, dựng cue sheet và chạy `python3 assets/scripts_video/tts_code_switch_risk.py <cue_sheet.json>`. Risk `high` chặn synthesis; risk `medium` được giữ trong manifest để nghe kiểm tra.

### 🔄 PIPELINE RE-TTS HÀNG LOẠT (BATCH RE-TTS)
Khi cần re-record audio cho nhiều tập (ví dụ: thay đổi quy tắc phát âm, đổi voice, sửa lỗi prosody):
```bash
# Dry-run: xem trước mà không thay đổi gì
python3 assets/scripts_video/re_tts_all.py --all --dry-run

# Re-TTS toàn bộ 24 tập longform (backup tự động trước khi overwrite)
python3 assets/scripts_video/re_tts_all.py --all --force --tts-only

# Re-TTS + Re-assemble video master
python3 assets/scripts_video/re_tts_all.py --all --force

# Re-TTS chỉ 1-2 tập cụ thể
python3 assets/scripts_video/re_tts_all.py --episodes 11,21 --force
```
- **Pipeline**: `.md` gốc → `vietnamese_prosody.py` → `.txt` → `tts_zen.py` (OmniVoice) → `.wav` → `assemble_tap_XX.py` → master `.mp4`
- **Backup**: Audio cũ tự động backup vào `audio/.backup_YYYYMMDD_HHMMSS/` trước khi ghi đè.
- **Preprocessor**: `vn_text_preprocessor.py` chứa bảng TECH_TERMS (chỉ acronyms, không phiên âm).

### 🌟 QUY CHUẨN 100% CLEAN FEED MASTER & YOUTUBE CC EXPORT (TIÊU CHUẨN V8)
- **Zero Burned-in Subtitles (Master MP4 100% Sạch)**: Video master xuất xưởng tuyệt đối **KHÔNG nhúng cứng phụ đề (Zero Hardsub / Zero Karaoke Sub)** lên khung hình để tránh mọi xung đột, đè chữ lên vùng đồ họa toán học Manim (Zone 5 & đáy màn hình).
- **Phụ đề mềm CC độc lập (`.srt`)**: Xuất file `.srt` chuẩn (tối đa 10–12 từ/cue, hiển thị 1.0s–3.5s) để tải lên YouTube Closed Captions (CC), cho phép khán giả tùy chọn bật/tắt tự do.

### 🎙️ TIÊU CHUẨN V8 WAVE EXPRESSION TTS (KẾ THỪA & ĐỒNG BỘ TOÀN WORKSPACE VỚI KÊNH BIẾT ĐỊA LÝ TỪ BA TÔI)
> [!IMPORTANT]
> **ĐỒNG BỘ & DÙNG CHUNG CỐT LÕI (SHARED CORE ACROSS CHANNELS):**
> Tiêu chuẩn **V8 Wave Expression TTS** được nghiên cứu và phát triển chung giữa đội ngũ kỹ nghệ của hai kênh **ZENPHAM** và **BIẾT ĐỊA LÝ TỪ BA TÔI** (`assets/scripts_video/vietnamese_expressive_tts_research.md`). Hai kênh chia sẻ 100% động cơ lõi tại `assets/scripts_video/vietnamese_expressive_prosody.py`, từ điển tự học `prosody_dictionary.json`, và skill toàn cục `vietnamese-expressive-tts`.
>
> **Khác biệt về định vị Persona giữa 2 kênh:**
> - **Kênh Biết Địa Lý Từ Ba Tôi**: Persona "Người cha giải thích cho con", ấm áp, tình cảm gia đình, thuận thiên sông nước, tốc độ tự nhiên 1.05x - 1.08x (phóng sự tài liệu) hoặc 0.96x - 1.02x (đoạn triết lý).
> - **Kênh ZENPHAM ("Tôi Làm Việc" / Reality Decode)**: Persona "Kỹ sư thực thi điềm tĩnh", mộc mạc, suy tư, không melodrama (cấm "phòng lab 2h sáng"), tôn trọng vẻ đẹp toán học và sự tao nhã của hệ thống. Tốc độ chuẩn **0.94x** (kẹp trần $\le 0.98x$), giữ khoảng trống chiêm nghiệm cho người xem theo dõi hoạt họa Manim 2K và các phép biến đổi vi tích phân / ma trận.

- **1. Bảo Toàn Cụm Từ Ghép Nguyên Khối (Zero-Split Invariant — 500+ Lexical Units)**:
  - Khóa chặt mọi từ ghép 2-3 tiếng: bao phủ cả thuật ngữ AI / Toán học (*năng lực tính toán, lan truyền ngược, đạo hàm riêng, hàm mất mát, điểm cực tiểu, ma trận hessian, không gian tiềm ẩn, nút thắt cổ chai, độ phức tạp bậc hai...*) lẫn từ vựng văn hóa Nam Bộ / Thủy văn kế thừa từ kênh Địa Lý (*đồng bằng, phù sa, triều cường, xâm nhập mặn, con nước lớn ròng...*).
  - Tuyệt đối cấm ngắt nhịp hoặc chèn dấu câu giữa các âm tiết của từ ghép.
- **2. Điều Biến Ma Trận 24 Wave Ngữ Điệu & 8 Mood Profiles**:
  - Từng câu thoại mang sắc thái F0 và trường độ riêng biệt, triệt tiêu hoàn toàn lối đọc phẳng đều đều (flat-rate monotone).
  - *Nhóm Triết lý (W01–W06)*: Dành cho khoảnh khắc eureka, đúc kết bản chất toán học (`W01_SubBass_Drift`, `W06_Zen_Equanimity`), F0 hạ sâu -1.0 đến -2.5 semitones.
  - *Nhóm Thủy văn & Động lực học (W07–W12)*: Ứng dụng xuất sắc cho dòng chảy gradient, luồng tensor lan truyền trong mạng nơ-ron (`W07_Tidal_Arch`, `W08_River_Glide`).
  - *Nhóm Luận đề & Phản biện (W19–W24)*: Dành cho tranh luận kỹ thuật, tương phản bias-variance, trade-offs phần cứng (`W20_Axiom_Anchor`, `W21_Data_Staccato`, `W22_Dialectic_Contrast`).
- **3. Bảo Vệ Biểu Cảm Biên Câu (Head Attack & Tail Cadence Release)**:
  - *Head Attack*: Khoảng thở đón đầu 80–120ms (lead-in headroom), khởi động F0 ở dải 110–120Hz mượt mà, triệt tiêu tiếng bụp khởi âm.
  - *Tail Cadence*: Đuôi âm buông dần 280–350ms, kết hợp micro-punctuation (` — ` hoặc `...`) để âm giọng chìm vào sub-bass tự nhiên trước khi BGM nổi lên.
- **4. Nhịp Thở Sinh Học Chính Xác (Biological Micro-Pause)**:
  - Khoảng nghỉ giữa các câu thoại: 340ms – 420ms (dẫn chuyện khoa học), 450ms – 800ms (chuyển cảnh triết lý).
  - Tự động chèn micro-breath (60–80ms) trước liên từ (`và`, `nhưng`, `để`) cho câu dài $> 14$ âm tiết.
- **5. Hybrid Acoustic Guard & Tương Thích Code-Switching AI**:
  - Kẹp trần an toàn `safe_speed <= 0.98x` khi phát hiện mật độ âm tiết dày đặc hoặc cụm phụ âm tắc.
  - Giữ nguyên spelling thuật ngữ tiếng Anh (`Backpropagation`, `Attention`, `Softmax`, `GPU H100`), neo bằng khung ngữ pháp tiếng Việt (`thuật toán Backpropagation`, `mô hình LLM`), phát âm ký hiệu toán chuẩn nghĩa ($\nabla \to$ nabla/gradient, $\theta \to$ theta, $\mathcal{L} \to$ hàm mất mát).
- **Kiểm định bắt buộc**: Vượt qua kiểm toán Prosody Audit ($\ge 85.0/100$ điểm, 0 lỗi ngắt từ ghép, Master EBU R128 $-14.5 \pm 0.5$ LUFS, True Peak $\le -1.5$ dBTP).

### 📱 CƠ CHẾ NÚT BẤM CHUYỂN TIẾP TRÊN SHORTS (NATIVE RELATED VIDEO CTA)
- Kể từ cuối năm 2023, YouTube đã khóa toàn bộ các siêu liên kết (hyperlink) trong phần mô tả và bình luận của Shorts để chống spam. Do đó, người xem **không thể bấm trực tiếp vào link trong mô tả/comment của Shorts**.
- **Cách duy nhất để có nút bấm CTA chuyển tiếp ngay trên video Short**: Sử dụng tính năng chính thức **"Video có liên quan" (Related video)** trong YouTube Studio:
  1. Vào [YouTube Studio](https://studio.youtube.com) -> **Nội dung** -> chọn video Short vừa đăng.
  2. Tại trang chi tiết video, nhấp vào mục **Video có liên quan (Related video)**.
  3. Chọn video dài 16:9 tương ứng -> Nhấn **Lưu (Save)**.
  4. Lúc này, trên giao diện ứng dụng YouTube điện thoại của người xem sẽ xuất hiện một nút bấm viên thuốc nổi bật: `▶️ Tiêu đề video dài` đặt ngay trên tên kênh — khớp hoàn hảo với mũi tên chỉ xuống của thẻ bài CTA cuối video Short!

---

## 6. Quy Chuẩn Cover & Thumbnail Engine — QUY TẮC THUMBNAIL HOÀNG KIM (THUMBNAIL DIVERSITY & HERO-FIRST)

> [!IMPORTANT]
> **QUY TẮC BẤT DI BẤT DỊCH VỀ THUMBNAIL (CHỐNG RẬP KHUÔN 90%):**
> Video thumbnail là touch point quan trọng nhất quyết định tỷ lệ nhấp chuột (CTR). Tuyệt đối **KHÔNG ĐƯỢC PHÉP dùng chung một khuôn mẫu (template) đen xì với vạch đỏ bên trái** khiến người xem lướt qua thấy các tập giống nhau 90%.

- **Cấu trúc 4 Trụ Cột Độc Bản (The 4-Pillar Thumbnail Architecture)**:
  1. **Trụ cột 1 — Hero Subject Khổng Lồ Áp Đảo (>= 50-60% Diện Tích Canvas)**:
     - Trung tâm hoặc phần lớn khung hình phải là một thực thể hình ảnh / biểu tượng 3D phát quang cực kỳ bắt mắt, đại diện cho bản chất toán học của tập đó.
     - *Tập 03 (Vector Space)*: Vũ trụ vector đa chiều 3D, chùm laser tọa độ neon phát sáng.
     - *Tập 04 (Nghịch lý Simpson)*: Hai khối dữ liệu đối kháng cực độ (Ice Blue vs Crimson Coral) với nhát cắt phân cực kịch tính.
     - *Tập 05 (PRNG & Entropy)*: Xúc xắc lượng tử Cyberpunk phát sáng bị bổ đôi để lộ bánh răng cơ học bên trong.
     - *Tập 06 (CLT & Chuông Gauss)*: Đồi chuông Gauss bằng vàng lỏng phát sáng với hàng triệu hạt mưa năng lượng rơi tự do.
  2. **Trụ cột 2 — Đột Phá Bảng Màu (Color Palette Divergence)**:
     - Nghiêm cấm dùng lại tone màu nền đen tím `#08090e` và chữ đỏ neon giữa 2 tập kế cận.
     - Mỗi tập phải có một Color Signature hoàn toàn riêng biệt:
       - Tập 03: Electric Cyan & Deep Violet Cosmos (`#00f0ff`, `#7928ca`).
       - Tập 04: Split Dual-tone Clash (Ice Blue `#38bdf8` vs Crimson Coral `#ef4444`).
       - Tập 05: Synthwave Magenta & Cyber Amber (`#f43f5e`, `#f59e0b`).
       - Tập 06: Luminous Golden Gauss & Deep Obsidian (`#fcd34d`, `#d97706`, `#0b0f19`).
       - Tập 07: Acid Matrix Emerald (`#10b981`, `#059669`).
  3. **Trụ cột 3 — Typography Siêu Tinh Gọn (2–4 Từ Kích Thước Khổng Lồ 130–160px)**:
     - **CẤM TUYỆT ĐỐI**: Viết cả câu học thuật dài 3 dòng rườm rà.
     - **CHỈ DÙNG 2–4 TỪ**: Đánh trúng tâm lý tò mò (Curiosity Hook), font chữ sans-serif cực dày, drop shadow 3D nhiều hướng để đọc rõ mồn một trên màn hình điện thoại 5 inch (150px preview).
       - Ví dụ: `VŨ TRỤ 1536 CHIỀU`, `DỮ LIỆU ĐANG LỪA BẠN!`, `AI KHÔNG HỀ NGẪU NHIÊN!`, `MỌI HỖN LOẠN ĐỀU VỀ ĐÂY!`.
  4. **Trụ cột 4 — Bố Cục Biến Hóa Linh Hoạt (Dynamic Layouts)**:
     - Không cố định text bên trái đè lên nền đen. Linh hoạt sử dụng:
       - *Center Hero*: Hero nằm chính giữa tỏa sáng, text đặt phía trên hoặc phía dưới.
       - *Split A/B Duel*: Chia đôi khung hình tương phản 2 nửa.
       - *Diagonal Tension*: Góc chéo năng động tạo cảm giác chuyển động mạnh.
     - **Brand Badge Chuẩn Hóa**: Tinh giản thành một badge nhỏ tinh tế ở góc, chỉ ghi duy nhất định dạng: `Series {số seri} - Tập {thứ tự hay tên tập}` (ví dụ: `Series 1 - Tập 01`). Tuyệt đối **KHÔNG** ghi thêm bất kỳ tag nào như "2K Masterclass", "QHD Masterclass" hay câu từ tự đánh bóng; tính toán dynamic bounding box với padding tối thiểu 36px ngang để chữ không chạm mép viền.

Lệnh tạo cover đạt chuẩn:
```bash
python3 assets/scripts_video/thumbnail_hero_engine.py \
  --episode 06 \
  --out assets/scripts_video/output/thumb_tap_06_master.jpg
```

---

## 7. Quy Trình Sản Xuất End-to-End & Lệnh Thực Thi

Quy trình sản xuất một tập "Tôi Làm Việc" hoàn chỉnh gồm 5 bước:

### Bước 1: Viết kịch bản chuẩn
Tạo file kịch bản markdown theo mẫu `skills/creative/toi-lam-viec/references/script_template_toi_lam_viec.md`.

### Bước 2: Tạo giọng đọc Zenpham Omnivoice
```bash
python3 assets/scripts_video/tts_zen.py \
  --md assets/scripts_video/zenpham_toi_lam_viec_tap_XX.md \
  --channel zenpham \
  --mood zen_meditation \
  --speed 0.94
```

### Bước 3: Render đồ họa toán học Manim (100% Clean Master, ZERO Baked-in Watermark)
> [!IMPORTANT]
> **Tuyệt đối KHÔNG nhúng Watermark/Logo vào code Manim**. Manim chỉ render hoạt họa toán học thuần khiết. Watermark chính thức duy nhất (`zenpham_subtle_watermark_150px.png` mờ 28%, góc trên phải `W-w-60:60`, TẮT trong 5.80s Opener) được chèn tự động duy nhất 1 lần ở bước hậu kỳ FFmpeg.
> Trước khi render, bắt buộc chạy kiểm định AST:
> ```bash
> python3 assets/scripts_video/ast_manim_deep_auditor.py
> ```
> Sau đó render qua Docker:
```bash
docker run --rm -v $(pwd)/assets/scripts_video:/manim manimcommunity/manim:latest \
  manim -r 2560,1440 --fps 60 /manim/manim_scenes/your_scene.py SceneName -o scene_render_2k.mp4
```

### Bước 4: Assemble video với Anti-Skew & Voice-driven Timing (Xuất Bản Chuẩn Tối Thiểu 2K QHD)
```bash
python3 assets/scripts_video/assemble_podcast.py \
  --md zenpham_toi_lam_viec_tap_XX.md \
  --landscape \
  --channel ZENPHAM \
  --voice-driven \
  --music "assets/background_music/living - lifestyle/Quiet Room Glow (1).mp3" \
  --out assets/scripts_video/output/zenpham_toi_lam_viec_tap_XX_master_2k.mp4
```

### Bước 5: Chạy Pre-Flight QA & Publish lên YouTube
```bash
uv run python skills/media/youtube-publisher/scripts/yt_publish.py upload \
  --video assets/scripts_video/output/zenpham_toi_lam_viec_tap_XX_master_2k.mp4 \
  --md assets/scripts_video/zenpham_toi_lam_viec_tap_XX.md \
  --channel ZENPHAM \
  --privacy public
```

---

## 8. Bảng Kiểm Tra Chất Lượng Trước Khi Đăng (Quality Gate Checklist)

- [ ] **Kịch bản**: Chứa dấu ấn kỹ sư 10+ năm kinh nghiệm tại InnoRia Solution; không có lý thuyết sáo rỗng.
- [ ] **Khung hình**: Tối thiểu chuẩn 16:9 Landscape 2K QHD (2560x1440 @ 60fps) cho Video Essay hoặc 9:16 2K QHD (1440x2560) / 1080x1920 cho Shorts; không bị méo tỉ lệ (anti-skew verified).
- [ ] **Đồ họa Manim**: 100% Clean Master (KHÔNG nhúng watermark/logo vào code Manim). Vượt qua kiểm tra AST Deep Audit (`python3 assets/scripts_video/ast_manim_deep_auditor.py` đạt 0 Critical). Chữ tiếng Việt hiển thị chính xác không lỗi font (`manim_smart_text.py` / `Text(font="sans-serif")`), KHÔNG dùng tiếng Việt có dấu trong `MathTex` (tránh crash LaTeX), có sound fx đồng bộ mili-giây. Zero layout collision. Render ở chuẩn 2K QHD (`-qp`).
- [ ] **Âm lượng**: Max volume `-1.0 dBFS`, Mean loudness `-14` đến `-18 LUFS`, nhạc nền không át tiếng nói.
- [ ] **Thumbnail**: Đạt chuẩn Golden Thumbnail ấn tượng nhất, có Brand Badge chuẩn `Series {số seri} - Tập {thứ tự}` (không ghi masterclass).
- [ ] **SEO Metadata**: Tiêu đề dưới 70 ký tự, có đủ Timestamps 00:00, 3 tầng thẻ tags, pinned comment kích thích bàn luận.
- [ ] **Clean Feed Subtitles & Tạm Dừng Karaoke Subs (BẮT BUỘC - ZERO MANIM COLLISION)**: Master video xuất bản là 100% Clean Feed (cấm tuyệt đối burn-in phụ đề cứng hoặc karaoke `.ass` vào video để không đè lên Manim Zone 5 và hệ trục tọa độ). Phụ đề chỉ phát hành dạng file `.srt` rời cho YouTube CC.
- [ ] **Phễu Shorts 30s & Liên kết CTA Hai Chiều (BẮT BUỘC - QUALITY GATE 7)**:
  - Mỗi tập 16:9 bắt buộc phải có ít nhất 1 video Micro-Short 30s phễu đi kèm.
  - Video Short 30s bắt buộc có thẻ bài CTA Card cuối video (`short_cta_card.png`) nhúng ảnh thumbnail 16:9, viền neon, mũi tên chỉ xuống `⬇️ LIÊN KẾT BÊN DƯỚI VIDEO NÀY`.
  - Giọng đọc kết của Short bắt buộc có câu kêu gọi: *"Xem bản phân tích trọn vẹn tại video đầy đủ trên kênh Zen Phạm. Bấm vào liên kết bên dưới để xem ngay."*
  - Mô tả Short bắt buộc đặt link video dài 16:9 ngay 3 dòng đầu tiên.
  - Mô tả Video 16:9 bắt buộc chứa backlink xem tóm tắt: `📱 Xem tóm tắt nhanh 30s của tập này: https://youtube.com/shorts/{SHORT_ID}`.
  - Thiết lập mục **"Video có liên quan" (Related video)** trong YouTube Studio trỏ về video dài 16:9 tương ứng.
- [ ] **Footage Độc Lập & Không Trùng Lặp (BẮT BUỘC - QUALITY GATE 8 - ZERO FOOTAGE REUSE)**:
  - **Tuyệt đối KHÔNG DÙNG LẶP LẠI B-roll footage giữa các tập khác nhau** (cả Video Shorts 9:16 và Longform 16:9).
  - Mỗi tập phải có kho B-roll footage riêng biệt được lấy từ Footage Pool (`assets/footage_pool/clips/`) hoặc render mới.
  - Nghiêm cấm trỏ cứng vào thư mục `clips_raw` của tập trước làm nguồn B-roll.
  - Hook của Short 30s giữa các tập bắt buộc dùng footage hoàn toàn độc lập (Tập 1: Đồng xu quay chậm, Tập 2: Kỹ sư trực đêm trước màn hình, Tập 3: Mạng nơ-ron phát quang, Tập 4: Giọt mưa trên kính cửa sổ đêm, Tập 5: Bo mạch / server / laser riêng).
  - Toàn bộ clip sử dụng trong từng tập phải được đăng ký và kiểm tra tính duy nhất (Uniqueness Audit) trước khi render.

---

## 9. Kế Hoạch Video Tổng Hợp Toàn Bộ Series (The Full Masterclass Compilation)

Sau khi hoàn thành phát hành toàn bộ các tập đơn lẻ của chuỗi 10 tập:
- **Tên Video**: `TRỌN BỘ TOÁN HỌC & BẢN CHẤT CỦA TRÍ TUỆ NHÂN TẠO — 10 NĂM LÀM NGHỀ ĐÚC KẾT`
- **Thời lượng**: 60 – 90 phút (Định dạng Phim tài liệu kỹ thuật / Masterclass).
- **Cấu trúc**:
  - Lời mở đầu tổng quan về hành trình 10 năm của một kỹ sư AI Việt Nam từ con số 0.
  - Ghép nối 10 chương liền mạch với phần dẫn dắt chuyển tiếp (Bridge Segments).
  - Tích hợp Chapter Timestamps chi tiết từng chủ đề.
  - Đi kèm Repository GitHub mở mã nguồn toàn bộ các file Manim animation và code demo.
- **Mega Thumbnail**: Bức họa toàn cảnh vũ trụ nơ-ron (The Grand AI Computation Cosmos), quả cầu phát quang ở trung tâm, kết nối mạng lưới các thuật toán từ Xác suất đến Transformer.
