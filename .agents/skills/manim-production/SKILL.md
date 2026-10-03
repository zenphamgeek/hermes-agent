---
name: manim-production
description: "Comprehensive production Manim system for ZENPHAM video productions. Minimum output standard: 2K QHD (2560x1440). Empowered with 3Blue1Brown and Median mathematical visual storytelling, Neo-Noir aesthetic design tokens, 10 reusable visual components, collision-safe layout constraint engine (safe_place), voice-sync timeline synchronization, and SFX/VFX cue choreography for educational cinema."
version: 2.1.0
author: ZENPHAM & Antigravity
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [manim, video-production, animation, layout-engine, visual-components, zenpham, 3blue1brown, median-math, 2k-qhd]
    related_skills: [toi-lam-viec, manim-video]
---

# Manim Production System — Master Creative & Technical Guide (v2.1 - 2K QHD Standard)

> *"Đây là điện ảnh giáo dục (Educational Cinema). Mỗi khung hình đều phải mang tính giảng dạy. Mọi chuyển động đều phải bóc tách cấu trúc sâu kín của toán học và kỹ thuật AI. Chuẩn hình ảnh tối thiểu toàn hệ thống: **2K QHD (2560x1440 @ 60fps)**."*

**Resolution Standard**: Tối thiểu 2K QHD (2560x1440 @ 60fps)  
**Style**: 3Blue1Brown × Median (Nền Obsidian `#0c0d12`, Pastel Neon Glow, Geometric Intuition First)  
**Core Module**: `assets/scripts_video/manim_production.py` — Thư viện thành phần và thuật toán tránh va chạm  
**Tài liệu tham khảo chuyên sâu**:
- 📜 [Master Engineering Specification](file:///home/zen/hermes-agent/docs/specs/MANIM_SKILLS_MASTER_SPECIFICATION.md) — Toàn bộ đặc tả kỹ thuật hệ sinh thái Manim Skills
- 📖 [Manim Master Dictionary (Source of Truth)](references/manim_dictionary.md) — Bộ từ điển tra cứu 100 Scenes Manim (Động/Tĩnh, Căn cứ khoa học)
- 🧪 [Science Pattern Catalog](references/science_catalog.md) — Cẩm nang thư viện khoa học & template 5 chuyên ngành
- 📚 [10 Visual Paradigms Code Recipes](references/ai_math_visual_paradigms.md)
- 🎨 [VFX, Camera Choreography & Micro-Animations](references/visual_effects_and_choreography.md)
- 📐 [Layout Architecture & Typography](references/layout_and_typography.md)
- 🌐 [Advanced 2D/3D Structures & Cinematic Layouts](references/advanced_2d_3d_and_layouts.md)
- 🎙️ [Scriptwriting Workflow & Voice-Sync](references/scriptwriting_workflow.md)
- 🌐 [Curated Manim Ecosystem & External Sources](references/manim_curated_ecosystem_sources.md) — 7 nguồn tài nguyên toàn cầu, ma trận bản quyền và thư viện thành phần STEM
- 🎨 [ZenManim CSS Design System (Tailwind CSS v3 + Material Design 3)](file:///home/zen/hermes-agent/assets/scripts_video/MANIM_CSS_DESIGN_SYSTEM.md) — Bảng quy chuẩn Design Tokens, Spacing Scale, Type Scale và Vùng an toàn Subtitle CC

---

## 0. ZenManim CSS Design System (Tailwind CSS v3 + Google Material 3)

Mọi cảnh Manim trong kênh BẮT BUỘC phải tuân thủ chuẩn **ZenManim CSS (ZM-CSS)** thông qua thư viện [manim_css.py](file:///home/zen/hermes-agent/assets/scripts_video/manim_css.py) và bộ Tokens [tokens.json](file:///home/zen/hermes-agent/assets/manim_css/tokens.json):

1. **Design Tokens:**
   - **Màu nền:** `Material3.SURFACE_0` (`#0b0f19` Obsidian Deep Black, không dùng `#000000`).
   - **Card & Stage:** `Tailwind.SLATE_900` (`#10172a`), viền `Tailwind.SLATE_800` (`#1e293b`).
   - **Accent Colors:** `Tailwind.CYAN_400` (`#00f0ff`), `Tailwind.AMBER_400` (`#fbbf24`), `Tailwind.EMERALD_400` (`#34d399`), `Tailwind.ROSE_500` (`#fb7185`).
   - **Thang khoảng cách:** `Tailwind.GAP_1` (0.08), `GAP_2` (0.16), `GAP_4` (0.32), `GAP_6` (0.48).
2. **Typography Scale & Phông chữ:**
   - Bắt buộc dùng phông `Be Vietnam Pro` để triệt tiêu 100% lỗi khoảng trống ký tự (kerning gap) trong tiếng Việt.
   - **Tiêu đề H1 (`Typography.h1`):** Size 22pt, Single-line clamp tối đa 52 ký tự. Tuyệt đối không tự ý ngắt dòng sau dấu hai chấm `:` và không bao giờ để khoảng trắng trước dấu câu.
   - **Tiêu đề H2 (`Typography.h2`):** Size 17pt, tối đa 36 ký tự.
   - **Nội dung (`Typography.body`):** Size 12pt, line-spacing 1.35.
3. **Bảo vệ vùng phụ đề (YouTube Subtitle CC Safe Zone):**
   - Vùng đáy màn hình $Y \in [-4.00, -2.00]$ (chiếm 22% khung hình) được **bảo vệ tuyệt đối cho phụ đề YouTube**.
   - Mọi layout (`SplitScreenLayout`, `ComparisonLayout`, `FullCanvasLayout`) tự động kiểm tra và đẩy nội dung lên trên nếu $Y < -2.00$, triệt tiêu hoàn toàn lỗi che khuất chữ phụ đề.
4. **Bố cục Flexbox & Grid:**
   - Sử dụng `VStack` (FlexCol), `HStack` (FlexRow), `Card`, `MetricBadge`.
   - Cấm dùng các tọa độ ma thuật `shift(UP * 2.3 + LEFT * 1.5)` gây lệch tâm và va chạm khi nội dung thay đổi.

### 0.1. Quy Chuẩn Vòng Đời Bố Cục & Kỷ Luật Chống Thoái Lui (Layout Lifecycle & Regression Invariants)

1. **Vòng đời Component Layout Container (`SplitScreenLayout`, `ComparisonLayout`):**
   - Khi truyền `hero` vào `SplitScreenLayout(hero=left_hero, sidebar=sidebar, header=header)`:
     - `SafeViewport.clamp_mobject(hero)` và `hero.move_to(...)` sẽ dịch chuyển toàn bộ hệ trục và hình vẽ sang vị trí mới.
     - **BẮT BUỘC:** Mọi phần tử phụ thuộc toạ độ đồ thị `axes.c2p(...)` (ví dụ `tangent_arrow`, `tag_step`, nhãn phụ trợ) phải được khởi tạo **SAU KHI** container layout đã được gán, HOẶC phải được nhóm trực tiếp vào `hero` *trước* khi truyền vào layout. Khởi tạo mobject ngoài layout từ `axes` trước khi gọi layout sẽ gây lỗi lệch toạ độ nghiêm trọng (trôi dạt véc-tơ, đè chữ vào sidebar card).
2. **Neo tiêu đề màn hình tự do (Standalone Header Anchoring):**
   - `Typography.h1` mặc định xuất phát tại tâm màn hình `(0, 0, 0)`.
   - Các cảnh tự do không bọc qua `SplitScreenLayout` bắt buộc phải gọi `.move_to([0, 3.30, 0])` ngay khi khai báo để đảm bảo tiêu đề nằm vững chãi trên đỉnh an toàn ($Y \approx 3.30$).
3. **Phân tách rạch ròi Text thường và Công thức LaTeX:**
   - Trường `value` trong `MetricBadge` và các nhãn `caption` được tạo bằng Manim `Text` (Pango/Cairo).
   - Tuyệt đối cấm truyền ký tự LaTeX thô chứa `{` `}` như `{t-1}` vào `value`. Phải dùng ký tự unicode toán học: `s_t = β·s_(t-1) + (1-β)·g_t²`.
   - Chỉ dùng LaTeX với `Typography.formula(r"...")` hoặc `MathTex`.
4. **Đồng bộ nhịp thở kỹ thuật Voice-Sync ($2.4\text{s}$ Technical Pauses):**
   - Giữa các đại ý toán học, kịch bản âm thanh chèn khoảng nghỉ $2.0\text{s} - 3.0\text{s}$ (chuẩn $2.4\text{s}$).
   - Trong Manim, các cảnh tương ứng phải phân bố `self.wait(14.0)` đến `self.wait(22.0)` tương thích với từng beat âm thanh, kết hợp `play_eureka_flash` tại các mốc hội tụ để tạo nhịp thở điện ảnh trầm tĩnh, đĩnh đạc.

---

## Contract production và golden approval (2026-09-07)

**Trạng thái hiện tại: prototype; chưa audio-approved; chưa visual-approved; chưa golden-approved.** Đọc code, AST pass, render thành công hoặc điểm rubric không thay thế người nghe/xem phê duyệt.

- **Mascot SVG prototype**: `assets/brand/zenpham-brand-kit/zenpham-mascot-rig.svg`, `viewBox="0 0 600 640"`; có parts `eye-left`, `eye-right`, `pupil-left`, `pupil-right`, `arm`, `hand`. Đây là prototype, không phải artwork/rig đã duyệt. Kiểm tra mapping parts sau import SVG; không mặc định Manim giữ ID thành API. Duyệt silhouette, kính, mắt, pointing và tỷ lệ trên nền thật; mascot dẫn hướng target, không thay hero toán học, không thành watermark thứ hai.
- **OmniVoice contract theo code hiện hành**, nguồn `assets/scripts_video/tts_zen.py:get_ref_audio` và `_call_single_omnivoice_api` (chưa xác minh runtime trong lần cập nhật skill này): lấy `GET /voices`, chọn `omnivoice.voices` với `name="Zen Mien Tay/zenpham-zen-meditation-mientay"`; dùng `ref_audio` HTTP(S) mới và `ref_text` không rỗng từ catalog. Không hardcode signed URL, không ghi URL có token vào log.
- Gửi JSON `POST /api/tts/start`: `text`, `engine="omnivoice"`, `lang="vi"`, `speed`, `normalize_vi=false`, `expand_numbers=false`, `ref_audio`, `ref_text`. Nhận `job_id`, poll `GET /api/tts/progress/{job_id}`: `queued/loading/generating`, `done` kèm `audio_url`, hoặc `error`. Client hiện poll 3s, deadline 600s; chỉ tải HTTP(S) cùng host portal, kiểm tra WAV có frames/sample rate hợp lệ. Không gọi `/tts` như endpoint đồng bộ; không tự resubmit khi lỗi mạng khiến trạng thái job chưa rõ.
- Portal chỉ gửi tuning `speed`; `num_step`, `guidance_scale`, `position_temperature`, `layer_penalty_factor` là tham số legacy của wrapper, không phải field request đã chứng minh. Không bịa field IPA, phoneme, SSML hoặc pronunciation dictionary. Nếu contract server đổi, đọc schema/runtime evidence trước khi cập nhật.
- **Không phiên âm/IPA giả**: giữ nguyên thuật ngữ và tên riêng VI-EN; không chèn cách đọc kiểu Việt, chuỗi IPA tự chế hoặc markup chưa được hỗ trợ vào narration. Viết toán thành nghĩa tự nhiên; acronym chỉ đổi cách đọc sau A/B listening. Sample phải chứa tên riêng, thuật ngữ, acronym, số, ký hiệu; lint/ASR không chứng minh phát âm tự nhiên.
- **Benchmark có nguồn**: mỗi so sánh ghi URL tác phẩm gốc, tên tác giả/video, timestamp đoạn tham chiếu, ngày truy cập, tiêu chí quan sát và điểm hạn chế. Không có đoạn đã xem thì ghi `chưa benchmark`, không tự chấm như kết quả thực nghiệm. Nguồn kỹ thuật: [Manim output settings](https://docs.manim.community/en/stable/guides/configuration.html); nguồn tham chiếu trực giác: [3Blue1Brown — Linear algebra](https://www.3blue1brown.com/topics/linear-algebra). Đây là nguồn để khảo sát, không phải chứng cứ đã đạt chất lượng tương đương. Median cần URL video chính chủ và timestamp được xác minh; không suy đoán công cụ tác giả dùng. Benchmark tốc độ/dung lượng phải có lệnh, phiên bản, phần cứng, scene, log và số đo cùng điều kiện; không dùng hệ số không nguồn.
- **2K60 thật**: production `manim -r 2560,1440 --fps 60 ...`; Shorts master dọc `1440x2560 @ 60fps`. Kiểm tra file sau mux bằng `ffprobe` (width, height, r_frame_rate, avg_frame_rate). `-qp`, tên file, upscale hoặc lặp frame 30→60 không chứng minh render gốc 2K60; ghi rõ nguồn upscale/converted. Nháp thấp chỉ dùng kiểm tra blocking.
- **Golden approval**: prototype 20–40s, duyệt audio VI-EN trước; render golden 2K60, xem không tiếng rồi xem kèm narration/SFX. Ghi riêng `audio-approved`, `visual-approved`, `golden-approved` cùng người duyệt, thời điểm, đường dẫn/hash đúng phiên bản media và lỗi còn lại. Mặc định tất cả `pending`; chỉ người dùng/người duyệt được chỉ định xác nhận. Chỉ nhân rộng episode hoặc publish khi cả ba được duyệt; sửa audio/visual phải duyệt lại phần bị ảnh hưởng.

## 1. Triết Lý Sáng Tạo: Median Math ➜ Zenpham AI Craftsmanship

```
     CÔNG THỨC MEDIAN                      CÔNG THỨC "TÔI LÀM VIỆC" (ZENPHAM)
┌──────────────────────────┐          ┌──────────────────────────────────────────────┐
│  1. Câu hỏi toán học     │   ──►    │  1. Va chạm thực tế tại InnoRia Solution     │
│  2. Lịch sử khoa học     │   ──►    │  2. Mổ xẻ toán học bằng Manim (Hình học hóa) │
│  3. Nghịch lý nhận thức  │   ──►    │  3. Ứng dụng sống còn trong AI & Phần mềm    │
│  4. Kết luận trừu tượng  │   ──►    │  4. Đạo làm nghề (Digital Craftsmanship)     │
└──────────────────────────┘          └──────────────────────────────────────────────┘
```

### 5 Nguyên Tắc Bất Di Bất Dịch Cho Mọi Cảnh Manim:
1. **Hình học trước Đại số (Geometry before Algebra)**: Luôn hiển thị hình ảnh trực quan, không gian 3D, sự co giãn vector trước khi viết phương trình. Khi người xem nhìn thấy hình học trước, công thức toán học sẽ trở nên tự nhiên và dễ hiểu.
2. **Ẩn dụ trực quan sống động (Intuitive Metaphors)**:
   - Gradient Descent: Người leo núi mù dò dẫm trong đêm tối trên rặng Andes bằng độ nghiêng bàn chân.
   - Attention: Ngọn đèn pin soi rọi vào các từ khóa trong đêm tối ngữ cảnh.
   - Vector Embedding: Đổ bóng hình chiếu vuông góc giữa hai mũi tên trong không gian ngữ nghĩa.
   - Normalization: Lát cắt ngang/dọc qua khối Rubik tensor 3 chiều.
3. **Phân tầng thị giác & Độ tương phản (Visual Layering)**:
   - Nền Obsidian: `ZenPalette.BG_DEEP` (`#0c0d12`), không bao giờ dùng đen tuyền thô ráp `#000000`.
   - Lớp Tiêu điểm (Hero): Neon rực rỡ (`#00f0ff`, `#f59e0b`, `#34d399`) độ sáng 1.0 + Hào quang (Glow).
   - Lớp Ngữ cảnh: Màu thứ cấp (`#94a3b8`) độ sáng 0.5.
   - Lớp Cấu trúc: Lưới trục mờ (`#1e293b`) độ sáng 0.15 - 0.25.
0. **Cấm Tuyệt Đối Chuyển Động Giả Hậu Kỳ (Zero Fake Camera Drift / Crop Sway Cheat)**:
   - Tuyệt đối CẤM dùng bất kỳ filter FFmpeg nào (`crop=...sin/cos...`, `zoompan`, `rotate`) để làm camera rung lắc/trôi dạt giả tạo nhằm lách qua kiểm định freeze.
   - Toàn bộ khung hình Manim trong hậu kỳ BẮT BUỘC dùng scale tĩnh cố định (`scale=1920:1080:force_original_aspect_ratio=decrease,pad=...`). Camera phải vững như bàn thạch. Chuyển động PHẢI đến từ bản chất toán học thuần khiết trong Manim.
4. **Ambient Motion Từ Hero Math Entity (Purposeful Micro-Kinetics):**
   - Chuyển động vi mô giữ nhịp PHẢI xuất phát từ thực thể toán học trung tâm (Hero Math Entity) của phân cảnh:
     * Tracer dot (`Dot`) chạy trên đường cong hàm số (`FunctionGraph`, `ParametricFunction`)
     * Vector xoay góc pha liên tục trên vòng tròn đơn vị
     * Điểm cực trị dao động nhẹ trên bề mặt hàm mất mát
     * Gradient particles chảy theo hướng descent
     * Opacity pulse nhẹ trên key LaTeX terms (`Indicate`, `Flash`)
   - **TUYỆT ĐỐI CẤM:**
     * `FunctionGraph` sine wave trang trí chạy dọc đáy màn hình (old `carrier_wave` pattern)
     * `setup_ambient_hologram_environment()` hoặc fake hologram bars
     * Vòng lặp `target.animate.scale(...)` co giãn vô nghĩa (scale breathing)
     * Bất kỳ chuyển động trang trí nào không liên quan đến nội dung toán học đang giảng dạy
   - Tham chiếu: Rule #24 trong [manim_masterclass_rules.md](../../rules/manim_masterclass_rules.md)
5. **Hiệu Chuẩn Ngưỡng Đóng Băng Vector (`noise=-65dB:duration=4.0s`)**:
   - Hoạt họa vector nền tối `#0c0d12` có delta trung bình $\approx -68\text{dB}$. Ngưỡng FFmpeg `freezedetect` bắt buộc đặt tại `-65dB`. Ngưỡng này phát hiện tức thì các đoạn frame bị clone/đứng hình tuyệt đối ($-\infty$) mà không bao giờ báo lỗi sai (false positive) trên các vector đang xoay hay sóng đang dao động.
6. **Không bao giờ đè chữ lên hình**: Mọi phần tử đều phải tuân thủ hệ thống phân vùng an toàn 4 vùng thông qua `safe_place()`.
7. **Tiêu Trừ Hộp Rỗng & Gạch Đầu Dòng (Anti-Box Gap & Hero Geometry)**:
   - Nghiêm cấm tạo 3–4 khối chữ nhật rỗng `RoundedRectangle` chứa văn bản gạch đầu dòng (Slide-Deck Laziness).
   - Mọi Scene bắt buộc phải lấy thực thể hình học toán học làm trung tâm (Trục số, Mặt phẳng phức, Vòng tròn lượng giác, Ma trận heatmap, Cây dữ liệu, Đồ thị sóng lan truyền, Dải token ribbon). Text chỉ đóng vai trò nhãn phụ / Badge / HUD.
8. **Bảo Toàn Thời Lượng Hoạt Họa Thực Chất (Animation Coverage >= 70%)**:
   - Tuyệt đối CẤM viết scene 5–15 giây cho voiceover 60–90 giây rồi nhân bản khung hình tĩnh bằng FFmpeg.
   - Manim phải có dòng chảy chuyển động đa giai đoạn (3–4 staged beats) bám sát lời thoại.
9. **Cấm FadeOut Ra Màn Hình Đen (Zero Black FadeOut)**:
   - Tuyệt đối KHÔNG gọi `self.play(FadeOut(...))` toàn bộ phần tử ở cuối scene nếu video sau đó tiếp tục giữ hình. Khung hình cuối cùng phải giữ trọn vẹn biểu đồ toán học sắc nét.
10. **Đơn Giọng Zen Thuần Nhất (100% Monolingual Voice)**:
    - 1 giọng Zen duy nhất đọc toàn bộ kịch bản. Tuyệt đối cấm cắt ghép 2 giọng đọc riêng rẽ cho tiếng Anh.
11. **Kỷ Luật Tách Biệt Ngữ Cảnh (1 Episode = 1 Isolated Task)**:
    - Không gộp nhiều tập vào 1 phiên làm việc. Mỗi tập phim là một Task độc lập.
12. **Pre-flight Quality Gate 4 Tầng Tự Động (`run_all_quality_gates.py`)**:
    - Mọi kịch bản và mã nguồn Manim trước khi dựng master BẮT BUỘC phải vượt qua kiểm định:
      ```bash
      python3 assets/scripts_video/run_all_quality_gates.py --episode XX
      ```
      Phải đạt 0 Critical trên cả 4 tầng (Kỹ thuật, Bố cục/Typography, Sư phạm/Vật lý, Bản sắc kênh).
13. **Phân Rã Khối Dưới 3 Phút (Sub-3-Minute Modular Chunking & 3-Act Structure)**:
    - **Tuyệt đối cấm xử lý Monolithic (Khối nguyên khối)**: Không bao giờ viết kịch bản, thiết kế đồ họa chuyển động hay lập trình Manim như một khối 8–10 phút liền tù tì không phân rã.
    - **Quy tắc cấu trúc 3 Hồi (3 Acts / Part Groups A, B, C)**: Mỗi tập phim bắt buộc được phân bổ theo 3 Hồi rõ ràng:
      - **Hồi A (Khởi nguyên & Triệu chứng — Scenes 1 & 2)**: $\le 180$s. Đập tan ngộ nhận, xây dựng trực giác đời thực bằng mô hình đồ chơi vật lý.
      - **Hồi B (Trọng tâm Cơ chế Toán học — Scene 3)**: $\le 100$s. Mổ xẻ sâu thuật toán lõi, phương trình và mô hình cơ học.
      - **Hồi C (Thực nghiệm, Đánh đổi & Đạo làm nghề — Scenes 4, 5, 6)**: $\le 240$s. Đo lường thực nghiệm, phân tích đánh đổi phần cứng (VRAM/Speed) và đúc kết triết lý người thợ thủ công số.
    - **Giới hạn thời lượng từng phân cảnh (Scene Limit $\le 180$s)**: Mọi phân cảnh thành phần (Scene / Chapter) bắt buộc có thời lượng $\le 3$ phút (180 giây), tối ưu nhất trong khoảng **60s – 95s**.
    - **Mục đích chiến lược sống còn**:
      - **Tập trung ngữ cảnh (Context Focus)**: Agent khi viết kịch bản minh họa và code Manim chỉ tập trung vào một phạm vi hẹp, loại trừ hoàn toàn ảo giác (hallucination) và trôi dạt (drift).
      - **Gia công mỹ thuật cao cấp (Artisanal Detailing)**: Đảm bảo từng giây hoạt ảnh đều có nhịp phách rõ ràng (Parts/Beats: Part 1.1, 1.2,...), không bị loãng nội dung hay thiếu hoạt ảnh dẫn đến đứng hình.
      - **Kiểm định cục bộ (Granular Quality Gate)**: Kiểm tra `freezedetect <= 4.0s`, safe padding và typography độc lập cho từng Scene trước khi ráp nối.
      - **Tiết kiệm tài nguyên (Caching & Fail-fast)**: Render từng Scene độc lập qua Docker; nếu phát hiện lỗi ở Scene nào, chỉ cần sửa và render lại đúng Scene đó trong vài chục giây thay vì kết xuất lại toàn bộ video 8–10 phút.

---

## 2. Quick Start: Sử Dụng Thư Viện `manim_production.py`

Mọi file kịch bản Manim của series đều chỉ cần import một module duy nhất:

```python
from manim import *
from manim_production import (
    # Bảng màu thiết kế chuẩn
    ZenPalette,
    # Layout an toàn chống va chạm
    safe_place, check_collisions, auto_resolve_overlap, SafeZone,
    # 10 Thành phần đồ họa cao cấp
    DiagramCard, ComparisonPanel, TensorDiagram, FlowChart,
    NeuralNetworkDiagram, TimelineDiagram, ProbabilityDistribution,
    NeonArrow, EquationBox, AnimatedCounter,
    # Đồng bộ giọng đọc
    VoiceSyncTimeline,
    # Hiệu ứng VFX & Âm thanh SFX
    SFXCue, mix_sfx, GlowEffect, EurekaFlash, GlassmorphismRect,
    # Tiện ích thương hiệu
    add_zenpham_watermark,
)
```

**Bắt Buộc Import Golden Brand Constants:**
Mọi assemble script PHẢI import và sử dụng:
```python
from golden_brand_constants import (
    OPENER_CLIP_2K60, CLOSING_CTA_CLIP,
    OPENER_DURATION, CLOSING_CTA_DURATION,
    verify_golden_integrity,
)
```
- Opener insert sau Part 01 (Hook)
- Closing CTA insert sau Part cuối cùng
- Gọi `verify_golden_integrity()` trước khi bắt đầu assemble

---

## 3. Trụ Cột 1: Động Cơ Bố Cục & Tránh Va Chạm (`safe_place()`)

### 3.1. Tiêu Chuẩn Safe Margin 15% - 20% & Zero Baked-in Watermark
> [!IMPORTANT]
> **Quy Tắc Vàng 1: ZERO Baked-in Watermark trong Code Manim**
> - **Tuyệt đối không nhúng Watermark / Logo / Text thương hiệu vào code Manim**. Manim chỉ tập trung 100% vào hoạt họa toán học và kỹ thuật thuần khiết.
> - Hàm `add_watermark()` / `add_zenpham_watermark()` bắt buộc là `pass` (No-op).
> - Watermark chính thức duy nhất (`zenpham_subtle_watermark_150px.png`, độ mờ 28%, tọa độ `W-w-60:60`, TẮT trong 5.80s Opener) được áp tự động DUY NHẤT 1 LẦN trong bước hậu kỳ FFmpeg (`batch_apply_brand_all_episodes.py`). Điều này loại trừ hoàn toàn lỗi 2 watermark đè nhau (như Tập 23) hoặc watermark mờ theo text logo cũ (như Tập 12).

> [!IMPORTANT]
> **Quy Tắc Vàng 2: Safe Padding 15% - 20% (Chống Đè Phụ Đề & Mép Màn Hình)**:
> - **Top Safe Zone ($Y \le +2.95$, `buff \ge 0.45`)**: Tiêu đề phân cảnh cách mép trên tối thiểu 0.45 units (chừa vùng Top HUD $Y \in [3.1, 3.5]$).
> - **Bottom Safe Zone ($Y \ge -2.50$, `buff \ge 0.45`)**: **BẮT BUỘC DÀNH RIÊNG 20% ĐÁY CHO PHỤ ĐỀ (SUBTITLE CC) VÀ THANH SCRUBBER**. Không đặt bất kỳ text, công thức, đồ thị nào vào vùng $Y < -2.50$. Cấm gọi `to_edge(DOWN, buff=0.35)` (sẽ rơi vào $Y = -3.30$ nguy hiểm).
> - **Horizontal Safe Zone ($-5.69 \le X \le +5.69$)**: Toàn bộ nội dung chính nằm gọn trong chiều ngang an toàn 20% lề.

### 3.2. Quy Tắc Bắt Buộc: Zero Text-Out-of-the-Box & Spatial Isolation (Chống Đè Chữ)
> [!CAUTION]
> **Lỗi Layout & Va Chạm Chữ (Kinh nghiệm xương máu từ Tập 21 & Tập 03)**:
> 1. **CẤM ĐÈ MŨI TÊN LÊN CHỮ**: Không bao giờ đặt mũi tên chỉ trục (Dimension Arrow) cắt ngang qua chữ của các thẻ (Card/Rect). Mũi tên trục Batch $N$ phải đặt hoàn toàn ở mép ngoài bên trái; mũi tên trục Feature $D$ phải đặt hoàn toàn ở phía trên hoặc bên ngoài khối thẻ.
> 2. **CẤM GỌI `.next_to()` MÙ QUÁNG**: Khi gán nhãn cho mũi tên bằng `.next_to(arrow, DOWN/LEFT)`, phải tính toán tọa độ để nhãn KHÔNG chiếm vùng không gian của các Card lân cận.
> 3. **BẮT BUỘC FONT ROBOTO CHO TIẾNG VIỆT**: LaTeX engine của Manim crash với tiếng Việt có dấu. Toàn bộ chú thích tiếng Việt bắt buộc phải dùng `Text("...", font="Roboto")` (được mount tự động vào `/usr/share/fonts/truetype/custom:ro`). Cấm dùng fallback generic `font="sans-serif"` gây topple dấu.
> 4. **MANDATORY PRE-FLIGHT AUDIT TRƯỚC KHI RENDER**: Mọi file kịch bản Manim trước khi xuất xưởng PHẢI vượt qua kiểm định tự động bằng lệnh:
>    ```bash
>    python3 assets/scripts_video/run_all_quality_gates.py --episode XX
>    ```
### 3.3. Tiêu Chuẩn Bố Cục Phân Vùng Rõ Ràng (Toán Thầy Việt & 3Blue1Brown Standard)
> [!TIP]
> **Kinh nghiệm thị giác từ các kênh toán trực quan hàng đầu (như Toán Thầy Việt `Dkxhykqz5VE` & 3Blue1Brown)**:
> Video đạt độ rõ ràng (clarity) tuyệt đối khi người xem không bao giờ phải phân vân *"Mắt mình nên nhìn vào đâu trước?"*. Cấu trúc không gian luôn tuân theo **3 tầng phân lập**:
>
> 1. **Dải chỉ mục trạng thái đỉnh màn hình (`StateTrackerBar`, $Y \approx +3.3$)**:
>    - Biểu diễn tiến trình tư duy dạng chuỗi node tròn/pill: $\mathbb{N} \rightarrow \mathbb{Z} \rightarrow \mathbb{Q} \rightarrow \mathbb{R} \rightarrow \mathbb{C}$ hoặc `[BST] -> [O(N)] -> [Splay] -> [O(log N)]`.
>    - Nút đang học phát sáng Neon (`ZenPalette.GOLD` / `ZenPalette.CYAN`), các nút còn lại mờ (`opacity=0.35`). Người xem luôn định vị được mình đang ở đâu trong hành trình nhận thức.
>
> 2. **Sân khấu 2 cột bất đối xứng 60–40 (Two-Column Asymmetric Stage)**:
>    - **Cột Trái (Visual Stage — 60% Width, $X \in [-5.5, +0.5]$)**: Sân khấu hình học thuần khiết (trục số, mặt phẳng phức, vector quay, cây dữ liệu, đồ thị Fourier). Tuyệt đối không nhét chữ dài vào đây. Dùng `PointCallout` (mũi tên cong + nhãn `"ở ĐÂY"`) để chỉ đích danh điểm nút.
>    - **Cột Phải (Cognitive Stack — 40% Width, $X \in [+0.8, +5.5]$)**:
>      - Trên cùng: Khung công thức tiêu điểm (`EquationBox`) viền neon nổi bật.
>      - Ở giữa: Thẻ định danh khái niệm (`ConceptBadge`) chữ in hoa bo góc (ví dụ: `[ MẶT PHẲNG PHỨC ]`, `[ ZIG-ZIG ROTATION ]`).
>      - Ở dưới: Quy tắc suy luận súc tích (ví dụ: `NHÂN = xoay + co giãn`).
>
> 3. **Thẻ chú giải triết lý đáy màn hình (`BottomCalloutCard`, $Y \in [-2.4, -1.8]$)**:
>    - Thẻ kính mờ bo góc (`BG_CARD`, opacity 0.92) chứa lời giải thích tinh túy nhất của phân cảnh.
>
### 3.4. Quy Tắc Bất Biến: Đầu Mũi Tên Nhỏ Gọn & Cân Đối (Sleek Proportional Arrowheads)
> [!IMPORTANT]
> **TIÊU CHUẨN ĐẦU MŨI TÊN 3BLUE1BROWN NEO-NOIR**:
> - **CẤM DÙNG `Arrow()` MẶC ĐỊNH CỦA MANIM MÀ KHÔNG GÁN THAM SỐ**: Default `Arrow` của Manim có `tip_length = 0.35` và `max_tip_length_to_length_ratio = 0.25`. Trên các bước nhảy ngắn ($\Delta \le 2.0$), đầu mũi tên biến thành khối tam giác khổng lồ nuốt chửng thân mũi tên, che khuất đồ thị và va chạm với chữ xung quanh.
> - **THAM SỐ CHUẨN BẮT BUỘC**:
>   - `tip_length = 0.15 - 0.16` (thanh mảnh, tinh tế, sắc nét).
>   - `max_tip_length_to_length_ratio = 0.15 - 0.16` (không vượt quá 16% tổng chiều dài).
>   - `stroke_width = 2.2 - 2.8` (cân xứng hoàn hảo với đầu mũi tên).
>   - `buff = 0.0` (tiếp xúc chính xác điểm tọa độ, không hở khoảng trống kỳ quặc).
> - **CÁCH DÙNG KHUYÊN DÙNG**:
>   - Sử dụng `CleanArrow` / `SleekArrow` từ `manim_css` hoặc `visual_kit`:
>     ```python
>     from manim_css import CleanArrow, CleanCurvedArrow
>     arr = CleanArrow(start_pt, end_pt, color=COLOR_ROSE)
>     ```
>   - Hoặc khi gọi `Arrow()` gốc:
>     ```python
>     arr = Arrow(start_pt, end_pt, buff=0, color=COLOR_CYAN, stroke_width=2.4, tip_length=0.16, max_tip_length_to_length_ratio=0.16)
>     ```

### 3.5. Hệ Sinh Thái Thư Viện Manim Khoa Học & Mẫu Dựng Sẵn (Science Ecosystem & Pattern Catalog)

Hệ thống Manim Production áp dụng kiến trúc **Hub-and-Spoke**: Core giữ vững chuẩn layout 4 phân vùng và bảng màu Neo-Noir, còn các thư viện khoa học chuyên ngành được mở rộng qua các reference modules:

- **Cẩm nang tra cứu**: [references/science_catalog.md](references/science_catalog.md) (Tổng hợp API, cách kết hợp và các mẫu kinh điển từ `3b1b/videos`, `Theorem-of-Beethoven/AnimationsWithManim`, `manim-physics`, `manim-Chemistry`, `manim-ml`, `networkx`, `sympy`).
- **Kho mẫu code dựng sẵn (Ready-to-run Templates)**: Nằm tại thư mục `references/templates/`:
  1. `template_physics.py`: Cơ học con lắc / mô phỏng vật lý 2D / điện từ / quang học.
  2. `template_chemistry.py`: Cấu trúc phân tử 2D/3D (file `.mol`, PubChem), góc liên kết, orbital Bohr.
  3. `template_ml.py`: Ma trận Attention, lớp CNN (Feature maps), mạng nơ-ron sâu.
  4. `template_cs_algo.py`: Đồ thị trọng số Dijkstra (NetworkX), cây nhị phân, quy hoạch động.
  5. `template_math_3b1b.py`: Biến đổi ma trận không gian 2D, giải tích vi phân tích phân, Fourier.

> [!TIP]
> Khi tạo kịch bản cho video thuộc các lĩnh vực trên, AI tự động tra cứu [references/science_catalog.md](references/science_catalog.md) và áp dụng mẫu template tương ứng từ `references/templates/`, giữ nguyên 100% chuẩn bố cục 4 phân vùng.

### 3.5. Quy Tắc Registry-First & Bộ Từ Điển Manim (Single Source of Truth)

Hệ thống sở hữu bộ từ điển **[references/manim_dictionary.md](references/manim_dictionary.md)** và cơ sở dữ liệu `assets/scripts_video/manim_registry.json` lập chỉ mục **100+ phân cảnh Manim đã xây dựng**.

> [!IMPORTANT]
> **QUY TẮC BẮT BUỘC (REGISTRY-FIRST)**:
> Trước khi viết bất kỳ Scene Manim mới nào, AI **PHẢI tra cứu Manim Dictionary** hoặc chạy lệnh:
> ```bash
> python3 assets/scripts_video/manim_registry_scanner.py --query "<từ khóa thuật toán/công thức>"
> ```
> - Nếu phân cảnh hoặc hình ảnh tương tự đã có (ví dụ: Splay Tree, Gradient Descent, Transformer Attention, Matrix Eigenvalues): **Tái sử dụng ngay cấu trúc Scene có sẵn** thay vì viết lại từ đầu.
> - Mỗi phân cảnh trong Dictionary đều được định danh rõ:
>   - **Tính chất**: `DYNAMIC_ANIMATION` (chuyển động mượt mà) vs `STATIC_FRAME` (khung hình tĩnh).
>   - **Căn cứ khoa học**: Tiên đề toán học, định lý, tác giả và năm công bố.
>   - **Kịch bản phân cảnh**: Lời thoại tương ứng và vị trí trong video.
>   - **Lệnh Render Docker 1 dòng**: Sẵn sàng chạy kiểm chứng.

---

## 4. Trụ Cột 2: Danh Mục Các Thành Phần Đồ Họa Cao Cấp

| Thành phần | Công dụng | Ví dụ trực quan |
|:-----------|:----------|:----------------|
| **1. `StateTrackerBar`** | Dải chỉ mục tư duy đỉnh màn hình, highlight trạng thái hiện tại | `StateTrackerBar(states=["N", "Z", "Q", "R", "?"], active_index=4)` |
| **2. `ConceptBadge`** | Thẻ định danh khái niệm bo góc chữ in hoa chuẩn broadcast | `ConceptBadge("Mặt Phẳng Phức", color=ZenPalette.CYAN)` |
| **3. `BottomCalloutCard`** | Thẻ kính mờ chú giải triết lý đáy màn hình (cách ly phụ đề) | `BottomCalloutCard("Nhân với i tương đương phép quay 90 độ")` |
| **4. `PointCallout`** | Mũi tên cong laser chỉ định điểm Eureka kèm nhãn "ở ĐÂY" | `PointCallout(target_point, label="ở ĐÂY", direction=UR)` |
| **5. `DiagramCard`** | Thẻ kính mờ Glassmorphism chứa tiêu đề và nội dung nổi bật | `DiagramCard(content, title="Update Rule", accent_color=ZenPalette.CYAN)` |
| **6. `ComparisonPanel`** | Bảng so sánh 2 nửa đối xứng A/B (CNN vs Transformer, BN vs LN) | `ComparisonPanel(left_title="A", left_content=..., right_title="B", right_content=...)` |
| **7. `TensorDiagram`** | Biểu diễn ma trận/tensor kèm mũi tên chiều kích thước bên ngoài | `TensorDiagram(shape=(4, 6), dim_labels=["Batch", "Features"], highlight_slice="col")` |
| **8. `FlowChart`** | Sơ đồ luồng đường ống dữ liệu, pipeline tuần tự hoặc song song | `FlowChart(nodes=[{"label": "Input"}, {"label": "Process"}], layout="horizontal")` |
| **9. `NeuralNetworkDiagram`** | Mạng nơ-ron nhiều tầng với luồng tín hiệu phát quang liên kết | `NeuralNetworkDiagram(layers=[3, 5, 5, 2], accent_color=ZenPalette.CYAN)` |
| **10. `TimelineDiagram`** | Dòng thời gian lịch sử phát triển hoặc các cột mốc thuật toán | `TimelineDiagram(events=[{"year": "1687", "label": "Newton"}, ...])` |
| **11. `ProbabilityDistribution`** | Đồ thị hàm mật độ xác suất với vùng tô bóng phân vị $\pm 1\sigma$ | `ProbabilityDistribution(func=gaussian_pdf, shade_region=(-1, 1))` |
| **12. `NeonArrow`** | Mũi tên laser phát quang 3 tầng (Lõi trắng, hào quang neon) | `NeonArrow(start, end, glow_color=ZenPalette.AMBER)` |
| **13. `EquationBox`** | Khung hiển thị công thức viền neon, tiêu đề trên và chân lý toán học | `EquationBox(r"P(A|B) = \frac{P(B|A)P(A)}{P(B)}", title="Bayes Theorem")` |
| **14. `AnimatedCounter`** | Đồng hồ đếm số thực động lực (Epochs, Accuracy %, Loss, Req/s) | `AnimatedCounter(start=0, end=99.4, suffix="%", font_size=32)` |
| **15. `DuotoneIcon`** | Icon vector Phosphor 2 lớp (1,512 SVG) hỗ trợ 4 phong cách YouTube | `DuotoneIcon("tree-structure", style="neo_noir")` |
| **16. `DuotoneBadge`** | Thẻ khái niệm kết hợp icon vector sắc nét | `DuotoneBadge("brain", "Cơ Chế Attention", color=ZenPalette.CYAN)` |
| **17. `ArchitectureNode`** | Khối kiến trúc hệ thống (ByteByteGo style) cho CS/Phần mềm | `ArchitectureNode("database", "PostgreSQL", "Cold Storage")` |
| **18. `DuotoneTrackerBar`** | Thanh StateTrackerBar đỉnh màn hình dùng icon vector | `DuotoneTrackerBar([("tree-structure", "BST"), ("cpu", "SPLAY")])` |

*(Xem mã nguồn mẫu chi tiết trong [ai_math_visual_paradigms.md](references/ai_math_visual_paradigms.md))*

### 4.1. Khai Thác Kho Icon Phosphor Duotone (1,512 SVG) & 4 Phong Cách Thị Giác YouTube

Hệ thống sở hữu kho **1,512 icon SVG Phosphor Duotone** tại `assets/duotone/`. Mỗi icon gồm 2 path (`sub[0]` mảng nền opacity 0.2-0.5 và `sub[1]` nét vẽ chính). Component `DuotoneIcon` cung cấp 4 bộ phong cách thích ứng theo từng định dạng kênh YouTube:

1. **`neo_noir` (ZenPham "Tôi Làm Việc" - Signature)**:
   - Viền Neon rực rỡ (`CYAN`, `AMBER`, `GOLD`), nền kính tối bán trong suốt (opacity 0.28).
   - Ứng dụng: Nhấn mạnh các tiên đề thuật toán, chip xử lý, cấu trúc cây, GPU inference.
2. **`architecture` (ByteByteGo / System Design / Fireship)**:
   - Dạng thẻ hộp kiến trúc vuông vức bo góc với icon ở trên, tên component và nhiệm vụ ở dưới.
   - Ứng dụng: Sơ đồ vi dịch vụ, luồng dữ liệu phân tán (Kafka, Redis, PostgreSQL, Worker Thread).
3. **`minimal` (3Blue1Brown / Toán Thầy Việt)**:
   - Đơn sắc thanh nhã (`TEXT_PRIMARY` / `TEXT_MUTED`), không làm phân tán sự chú ý khỏi công thức toán LaTeX.
   - Ứng dụng: Gắn nhỏ bên trong `ConceptBadge` hoặc `StateTrackerBar`.
4. **`vibrant` (Kurzgesagt / Primer Explainer)**:
   - Hai mảng màu tương phản rực rỡ (Đỏ Neon + Vàng Gold, Xanh Lục + Cyan), độ đậm fill 0.5.
   - Ứng dụng: Video giải thích khoa học đại chúng, hoạt họa sinh động.

> [!TIP]
> Để tránh lỗi phân quyền trong Docker (`PermissionError: cpu-duotone_.svg`), `DuotoneIcon` tự động sao chép SVG vào bộ đệm ghi an toàn `/tmp/manim_svg_cache/` trước khi nạp vào Manim.

---

## 5. Trụ Cột 3: Kỹ Thuật Voice-Sync (Khớp Chuẩn Giọng Đọc)

Không đoán mò thời gian `self.wait(2.0)`! Sử dụng `VoiceSyncTimeline` để đo trực tiếp file WAV của TTS:

```python
timeline = VoiceSyncTimeline(["audio/scene_01.wav"])

# Nếu file thu âm dài 38.5 giây, chia cho 4 chuyển động chính theo trọng số:
timings = timeline.allocate(scene_index=0, n_animations=4, weights=[1.0, 2.0, 3.0, 1.5])
# -> Tự động tính toán chính xác số giây cho từng lệnh self.play()
```

### Quy Chuẩn Phát Âm Tự Nhiên VI-EN (Zero Transliteration Artifacts):
Để giọng đọc kỹ thuật giữ trọn sự sang trọng và tự nhiên khi code-switching giữa tiếng Việt và tiếng Anh:
1. **Thuật ngữ & Tên riêng giữ nguyên tiếng Anh chuẩn**:
   - `Gradient`, `Transformer`, `Attention`, `Embedding`, `Softmax`, `Loss Function`, `Backpropagation`, `Learning Rate`, `PyTorch`, `TensorFlow`...
   - **Tuyệt đối KHÔNG viết phiên âm thô** (ví dụ: cấm viết "Gờ-ra-đi-ân", "Tran-sơ-pho-mơ", "E-ti-en-sân", "Rơ-lu").
2. **Acronyms kỹ thuật giữ nguyên mặc định**:
   - `NaN`, `SGD`, `GPU`, `LLM`, `ReLU`: nghe sample trước; chỉ tách chữ khi A/B listening được duyệt. Không ép `ReLU` thành từng chữ hoặc giả định mọi acronym cùng quy tắc.
3. **Ký hiệu toán học đọc chuẩn nghĩa**:
   - $\nabla$ đọc là `"nabla"` hoặc `"gradient"`, $\theta$ đọc là `"theta"`, $\sigma$ đọc là `"sigma"`, $\partial$ đọc là `"đạo hàm riêng"`.


---

## 6. Trụ Cột 4: Hệ Thống SFX/VFX (Âm Thanh & Hiệu Ứng Ánh Sáng)

### 8 Mẫu SFX Chuẩn (Freesound CC0):
- `whoosh`: Lia camera, mũi tên bay vút.
- `pop`: Nơ-ron hoặc điểm dữ liệu lóe sáng.
- `impact`: Khoảnh khắc Eureka, kết quả định lý giáng xuống.
- `shimmer`: Mô hình hội tụ, kết luận triết lý nghề nghiệp.
- `typewriter`: Dòng code hoặc lệnh terminal gõ tự động.
- `swoosh`: Chuyển đổi cảnh quay mềm mại.
- `heartbeat`: Vòng lặp epoch luyện mô hình.
- `glitch`: Lỗi tràn số NaN, sập worker pool.

### Mux âm thanh tự động:
```python
from manim_production import SFXCue, mix_sfx

cues = [
    SFXCue("whoosh", timestamp=1.5),
    SFXCue("impact", timestamp=8.4),
    SFXCue("shimmer", timestamp=22.0, volume=0.8),
]
mix_sfx("render/raw_scene.mp4", cues, "output/scene_sfx.mp4")
```

---

## 7. Bảng Màu `ZenPalette` — Design Tokens Chuẩn

```python
ZenPalette.BG_DEEP       = "#0c0d12"   # Nền Canvas chính (Obsidian huyền bí)
ZenPalette.BG_CARD       = "#08090d"   # Nền các thẻ Card Glassmorphism
ZenPalette.BG_CARD_ALT   = "#0f1118"   # Nền phụ cho mặt cong 3D
ZenPalette.CYAN          = "#00f0ff"   # Dữ liệu, tensor, Forward pass, tính toán
ZenPalette.AMBER         = "#f59e0b"   # Trọng số model, tham số, chú ý
ZenPalette.GOLD          = "#fbbf24"   # Điểm nhấn Eureka, góc tương quan
ZenPalette.EMERALD       = "#34d399"   # Hội tụ thành công, dữ liệu chuẩn hóa
ZenPalette.CORAL         = "#f87171"   # Hàm mất mát (Loss), lỗi sai số
ZenPalette.RUBY_RED      = "#ef4444"   # Cảnh báo tràn số NaN, sập hệ thống
ZenPalette.VIOLET        = "#a78bfa"   # Không gian tiềm ẩn (Latent space), embeddings
ZenPalette.TEXT_PRIMARY  = "#e2e8f0"   # Chữ chính, công thức cốt lõi
ZenPalette.TEXT_SECONDARY= "#94a3b8"   # Chữ diễn giải, chú thích
ZenPalette.TEXT_DIM      = "#64748b"   # Đơn vị trục, nhãn mờ
ZenPalette.BORDER_SUBTLE = "#1e293b"   # Viền card mờ, đường lưới tọa độ
ZenPalette.NEON_CORE     = "#ffffff"   # Lõi trắng của tia laser phát sáng
```

---

## 8. Lệnh Render Trong Môi Trường Production (Docker / Native)

```bash
# Render nháp nhanh (Low Quality 480p15 - Draft):
docker run --rm -v $(pwd)/assets/scripts_video:/manim \
  manimcommunity/manim:latest \
  manim -ql /manim/manim_tap_XX_topic.py SceneName

# Render chất lượng cao xuất bản (2K QHD 2560x1440 @ 60fps - Production Master TỐI THIỂU 2K):
docker run --rm -v $(pwd)/assets/scripts_video:/manim \
  manimcommunity/manim:latest \
  manim -qp /manim/manim_tap_XX_topic.py SceneName

# Hoặc tùy biến độ phân giải pixel gốc 2K QHD:
docker run --rm -v $(pwd)/assets/scripts_video:/manim \
  manimcommunity/manim:latest \
  manim -r 2560,1440 --fps 60 /manim/manim_tap_XX_topic.py SceneName

# Render xem trước một khung hình tĩnh (Still Image 2K):
docker run --rm -v $(pwd)/assets/scripts_video:/manim \
  manimcommunity/manim:latest \
  manim -s -qp /manim/manim_tap_XX_topic.py SceneName
```

---

## 9. Pre-Flight Checklist: 7 Bước Kiểm Duyệt Trước Khi Xuất Bản

1. [ ] **Độ phân giải chuẩn tối thiểu 2K QHD (2560x1440 @ 60fps)**: Đã render `-r 2560,1440 --fps 60` và xác nhận metadata file sau mux bằng `ffprobe` chưa?
2. [ ] **Nền chuẩn Obsidian `#0c0d12`**: Đã đặt `self.camera.background_color = ZenPalette.BG_DEEP` chưa? (Không để đen `#000000`).
3. [ ] **Safe Margin 15% (Chống đè Subtitle/Watermark)**: Đáy màn hình có chừa đủ $Y \ge -2.6$ (`buff \ge 1.2`) cho phụ đề CC và đỉnh $Y \le +2.6$ cho watermark không?
4. [ ] **Zero Text-Out-of-the-Box**: Các khối text, code, công thức có được bọc bằng `SurroundingRectangle` hoặc tính kích thước động không? (Tuyệt đối không tràn ra ngoài viền hộp).
5. [ ] **Kiểm tra va chạm (Zero-Collision)**: Đã dùng `safe_place()` cho các nhãn cạnh mũi tên và khối vẽ chưa?
6. [ ] **Tiếng Việt Unicode**: Đã dùng `Text(..., font="sans-serif")` cho chữ tiếng Việt chưa? (Không dùng `MathTex` cho chữ có dấu tiếng Việt).
7. [ ] **Nhịp thở (Breathing Room)**: Sau khoảnh khắc cao trào có `self.wait(1.5-2.5)` không?
8. [ ] **Voice-Sync**: Tổng thời lượng các nhịp hoạt họa có khớp tuyệt đối thời lượng file audio không?
9. [ ] **Âm thanh SFX**: Đã gắn nhãn các mốc `whoosh`, `pop`, `impact` tương ứng với biến chuyển trên màn hình chưa?
10. [ ] **Subtitle & Karaoke Sync QA**: Phụ đề BẮT BUỘC dùng Faster-Whisper trích xuất mốc thời gian từng từ. Tối đa 1–2 dòng, tối đa 10–12 từ/cue, thời lượng cue $\le 4.5$s. CẤM TUYỆT ĐỐI ném nguyên cả đoạn văn 50–70 từ vào 1 cue duy nhất khiến chữ bung 5–6 dòng đè nát visual và tràn ra giữa màn hình.

---

## 10. Quy Chuẩn Brand Kit Zenpham & Opener Scene (Bắt Buộc Cho Series)

Để tạo bản sắc nhận diện thương hiệu điện ảnh cao cấp, toàn bộ các tập video series "Tôi Làm Việc" bắt buộc tuân thủ:

1. **5.80s Logo Opener Bumper**:
   - Chèn clip `assets/brand/zenpham-brand-kit/zenpham_opener_clip_1080p30.mp4` (hoặc bản upscale Lanczos 2K) ngay sau **Scene 1 (Hook)** và trước **Scene 2**.
   - Âm thanh: Mix tiếng chime thương hiệu từ `assets/brand/zenpham-brand-kit/zenpham_opener_audio.wav`.
   - BGM: Tự động ducking sâu xuống `volume=0.02` (-24dB) trong suốt 5.80s Opener.
   - Không đè watermark hay phụ đề trong 5.80s này (khung hình 100% sạch).
2. **Subtle Warm Ivory Watermark (Góc trên bên phải)**:
   - Asset: `assets/brand/zenpham-brand-kit/zenpham_subtle_watermark_150px.png` (ngà ấm `#F6F0E4`, độ mờ 28%).
   - Tọa độ: `W-w-80:80` (cho 2K QHD) hoặc `W-w-60:60` (cho 1080p) để giữ 15% safe margin.
   - Tắt hoàn toàn trong 5.80s Opener bumper.
3. **Sub-frame Audio-Video Parity & Time Shift**:
   - Độ lệch thời lượng Master: `abs(video_dur - audio_dur) < 0.05s` (chuẩn EBU R128 `loudnorm=I=-14:TP=-1.5:LRA=11,apad=whole_dur`).
   - Mốc thời gian phụ đề `.srt` và YouTube chapters từ Scene 2 trở đi tịnh tiến chính xác `+5.80s`.

