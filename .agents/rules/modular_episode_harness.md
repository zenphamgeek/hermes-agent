# Quy Chuẩn Sản Xuất Modular Episode (10-12 Parts)

## 0. Triết Lý: Mỗi Part Là 1 Tác Phẩm Nhỏ Hoàn Chỉnh
- Mỗi Part (45-90s) là một micro-scene độc lập với ngữ cảnh riêng
- Viewer comprehension > task completion
- Manim math entity là trung tâm, không phải text

## 0.1. Cấu Trúc Khung Vàng Bất Biến (Gold Macro-Structure)
Mọi tập Masterclass trong toàn bộ series (S1E1 -> S1E25) BẮT BUỘC tuân thủ đúng 5 phân đoạn chuẩn:
1. **Cold Opener (15 – 30s):**
   - Mở màn trực diện bằng nghịch lý nhận thức hoặc bài toán thực tế gây tò mò (Opening Archetypes 1–5).
   - CẤM chào hỏi rườm rà ("Chào các bạn"), CẤM chèn logo kênh ở đầu phân cảnh này.
2. **Logo Scene / Channel Stinger (5.80s):**
   - Clip nhận diện thương hiệu bất biến 2K60 (`assets/brand/zenpham-brand-kit/zenpham_opener_clip_2k60_muxed.mp4`).
   - BẮT BUỘC ghép nối ngay sau khi Cold Opener kết thúc.
3. **Content Scenes (6 – 10 phân cảnh bài học, 60 – 90s/cảnh):**
   - Chuỗi phân cảnh mổ xẻ hình học động học liên tục (Continuous Motion Geometry).
   - Tuyệt đối cấm slide thuyết trình, cấm camera sway xoay toàn cảnh, tuân thủ Rule 27 "Quay tại chỗ".
4. **CTA Beat (15 – 20s):**
   - Kêu gọi thảo luận văn minh, suy ngẫm triết học kỹ nghệ hoặc giải bài toán phòng lab.
5. **Bridge & Closing Screen với Series Thumbnails Mosaic (15 – 25s):**
   - Bắt buộc hiển thị bảng lưới Series Mosaic (chuẩn 5×5 cho Series 1: `series1_25_thumbnails_mosaic.png`).
   - Làm nổi bật tập hiện tại $k$ và tập kế tiếp $k+1$ (`cta_target`).
   - Tuân thủ YouTube End Screen Interactive Safe Zones:
     * Top-Right $[X \in [2.5, 6.5], Y \in [0.5, 3.2]]$: Video kế tiếp (Next Video Card).
     * Bottom-Right $[X \in [2.5, 6.5], Y \in [-3.2, -0.5]]$: Danh sách phát (Playlist Card).
     * Subscribe Avatar $[X \in [-1.0, 1.0], Y \in [-1.0, 1.0]]$.
   - Lời thoại tuân thủ triệt để công thức **ZenPham 3-Step Open Loop Formula** (Gate U trong `series_closing_gate.py`):
     *(1) Core Synthesis (1 câu) -> (2) Open Loop Hook (1 câu) -> (3) Direct Action CTA (1 câu)*.

## 0.2. Nhiệm Vụ Kiểm Toán Hội Đồng: Shorts, Thumbnails, Scenes & Closing Layout Elegant (Chống Bịa Đặt)

Hội đồng Cố vấn (Chuyên gia YouTube 2026, Carl Sagan, Claude Shannon, Cụ Nguyễn Hiến Lê, Bạn học sinh 16 tuổi) trực tiếp giám sát 4 chốt chặn kiểm toán bắt buộc:

### A. Kiểm Toán YouTube Shorts (Chất Lượng Là Ưu Tiên Hàng Đầu):
1. **Shorts là mặt tiền phễu chuyển đổi (Knowledge Funnel):** Tuyệt đối không xem Shorts là sản phẩm phụ làm đối phó. Mỗi Short phải là một tác phẩm điện ảnh dọc 9:16 (1440x2560 @ 60fps) độc lập với đồ họa Manim bản địa.
2. **Diệt sạch lỗi âm thanh bị câm (Zero Audio Silence Holes):**
   - CẤM TUYỆT ĐỐI hiện tượng 2–3s đầu bị câm (mất hook âm thanh) hoặc 2–3s cuối bị câm (cụt lời kêu gọi Related Video).
   - Âm thanh thoại bắt buộc xuất hiện ngay từ mili-giây $0.20\text{s} - 0.40\text{s}$.
   - Toàn bộ thời lượng Short ($45\text{s} - 55\text{s}$) không được có bất kỳ lỗ câm nào $\ge 0.35\text{s}$. Giọng đọc TTS V0-Sense mượt mà, ấm áp, âm lượng đạt chuẩn YouTube Shorts ($-14.0 \pm 0.5\text{ LUFS}$, True Peak $\le -1.0\text{ dBTP}$).
3. **Hooks rõ ràng, kịch tính & đủ thời lượng (Clear & Substantial Paradox Hook):**
   - $0 - 3\text{s}$ đầu tiên là sinh tử của Short: Bắt buộc mở màn bằng một câu hỏi nghịch lý nhận thức sắc bén (Cognitive Dissonance) đi kèm chữ Kinetic Typography nổi bật trên Tầng 1 ($Y \in [3.5, 6.8]$).
   - CẤM Hook mờ nhạt, chung chung, hoặc quá ngắn lướt qua dưới 2.0s khiến người xem chưa kịp tiếp thu đã biến mất. Text Hook phải lưu lại màn hình tối thiểu $2.5\text{s} - 3.5\text{s}$.

### B. Kiểm Toán Video Thumbnail & Thumbnail Mosaic Nhúng:
1. **Video Hero Thumbnail (2560x1440 2K QHD 16:9):**
   - Tương phản thị giác mạnh mẽ (Neo-Noir Obsidian `#0c0d12` kết hợp Cyan/Gold/Rose).
   - Tối đa 3–5 từ khóa kích thích tò mò (Cognitive Tension), không nhồi nhét chữ dài.
   - Vùng an toàn góc dưới bên phải ($X > 85\%, Y < 20\%$) phải 100% không chứa text/logo để tránh bị che bởi nhãn thời lượng video của YouTube (`10:45`).
2. **Thumbnail Mosaic Nhúng (Series 1 5×5 Mosaic):**
   - Cô lập namespace 100%: Series 1 bắt buộc dùng `series1_25_thumbnails_mosaic.png` (25 tập xếp 5×5). Cấm lẫn lộn với mosaic của Series 2, Logistics AI hay Industrial AI.
   - Hiển thị sắc nét, tỷ lệ chuẩn không méo hình, bọc trong khung kính Frosted Glassmorphism sang trọng.
   - Có đèn viền phát quang (Glow Halo) làm nổi bật tập hiện tại $k$ và tập kế tiếp $k+1$.

### C. Kiểm Toán Scene Visuals:
- Math dominance $\ge 75\%$, tuyệt đối cấm slide thuyết trình hay card chữ rỗng.
- Tuân thủ 100% Rule 27: Camera đứng yên như đá tảng, canvas và logo kênh đứng yên, chỉ xoay đối tượng toán học 3D tại chỗ.

### D. Chuẩn Mực Bố Cục Scene Cuối Cùng (Closing Scene Elegant Aesthetics & Zero Fabrication):
1. **Thiết Kế Đẹp & Elegant (Thẩm Mỹ Điện Ảnh Tinh Tế):**
   - Bố cục 2 cột cân xứng chuẩn tỷ lệ vàng:
     * Cột trái: 25-Thumbnail Mosaic với viền mạ Cyan `#00f0ff` và badge trọn bộ 25 tập.
     * Cột phải: Next Episode Hero Preview Card bọc viền kính phản quang + Hộp CTA YouTube 2026 tinh tế, chữ sắc nét (Be Vietnam Pro / Roboto).
     * Dải Triết Lý Làm Nghề thanh lịch ở đáy màn hình ($Y \ge -2.75$), cách xa vùng YouTube CC.
   - Tuyệt đối cấm các hộp thô cứng, màu sắc lòe loẹt hoặc viền stroke dày cộm làm mất tính thẩm mỹ công nghệ cao.
2. **TUYỆT ĐỐI TRÁNH BỊA ĐẶT (Zero-Fabrication Mandate):**
   - CẤM BỊA TÊN TẬP, CẤM BỊA CHỦ ĐỀ, CẤM BỊA URL HOẶC SỐ TẬP.
   - 100% thông tin về Tập tiếp theo $k+1$ (Tên tập, số thứ tự $k/25$, chủ đề toán học, đường dẫn GitHub `github.com/phamvuthang/hermes-agent`) BẮT BUỘC phải tra cứu và đối chiếu chính xác từ `SERIES_CONTRACT_V1.json` và `master_plan.md`.
   - Lời thoại 3-Step Open Loop Bridge phải dẫn dắt chính xác bài toán của tập $k+1$ theo hợp đồng, không bịa đặt nội dung mơ hồ.

## 1. Kiến Trúc 10-12 Parts Per Episode

Provide a clear table:

| Part | Tên | Thời lượng | Vai trò sư phạm |
|------|-----|-----------|----------------|
| 01 | Hook & Paradox | 45-60s | Opening Archetype 1–5 (CẤM 'Có bao giờ bạn tự hỏi') |
| 02 | Geometric Foundation | 60-90s | Xây nền tảng hình học trực quan |
| 03 | Mathematical Core A | 60-90s | Mổ xẻ concept lõi — visual build-up |
| 04 | Mathematical Core B | 60-90s | Deep-dive phương trình & LaTeX |
| 05 | LaTeX Spine | 60-90s | Equation revelation — khoảnh khắc Aha! |
| 06 | Visual Transformation | 60-90s | Dynamic motion — biến đổi thị giác |
| 07 | Algorithmic Mechanism | 60-90s | Thuật toán & vi cơ chế |
| 08 | Real-World Connection | 60-90s | Kết nối ứng dụng đời sống & hệ thống |
| 09 | Experimental Intuition | 60-90s | Trực giác thực nghiệm & đánh đổi |
| 10 | Architectural Reflection | 45-60s | Chiêm nghiệm kiến trúc hệ thống |
| 11 | Engineering Horizon | 45-60s | Ending Archetype 1–5 (CẤM 'Đạo làm nghề') |
| 12 | Outro & Next Episode Bridge | 30-45s | Cầu nối tập tiếp theo (Thumbnail 2K + MathTex) |

Total target: 8-12 minutes per episode.

## 2. Per-Part Production Protocol (Micro-Task Isolation)

### A. File Structure Per Part:
```
assets/scripts_video/
├── episode_XX/
│   ├── part_01_hook.md          # Script
│   ├── part_01_hook.py          # Manim scene
│   ├── part_01_hook.wav         # TTS audio
│   ├── PART_01_CONTEXT.json     # Input context
│   └── PART_01_RESULT.json      # Output QA result
│   ├── part_02_foundation.md
│   ├── part_02_foundation.py
│   └── ...
```

### B. Context Isolation Protocol:
- Agent processes MAX 2 consecutive Parts per micro-session
- Each Part begins by reading PART_XX_CONTEXT.json (contains: topic, math_entities, color_palette, preceding_part_summary)
- Each Part ends by writing PART_XX_RESULT.json (contains: duration_seconds, freeze_score, visual_qa_status, math_entities_used, scene_class_name)
- ZERO context carryover beyond what's in CONTEXT.json

### C. Quality Gate Per Part (MUST PASS before next Part):
1. **Render Gate**: Manim renders without errors via Docker
2. **Freeze Gate**: `freezedetect=noise=-65dB:duration=4.0s` on raw render — ZERO freeze > 4.0s
3. **Math Dominance Gate**: >= 75% of frame area is math geometry (Axes, FunctionGraph, Vector, etc.)
4. **Duration Gate**: Part duration matches audio ± 2s
5. **Visual QA Gate**: Extract 3 keyframes, agent must `view_file` each

## 3. Manim Quality Standards Per Part

### A. Hero Math Entity Rule:
- Every Part MUST have exactly 1 hero math entity (Axes, NumberPlane, ParametricFunction, Matrix, etc.)
- The hero entity is the visual anchor — all other elements support it
- Hero entity must undergo at least 1 meaningful transformation (Create → Transform → Eureka)

### B. Staged Animation Beats (Minimum 3 per Part):
```
Beat 1 (0-15s): Foundation — Hero entity appears
Beat 2 (15-40s): Transformation — Math operation visualized
Beat 3 (40-60s): Convergence/Eureka — Result crystallizes
Beat 4 (60s+): Ambient Hold — Hero entity with purposeful micro-motion
```

### C. Ambient Motion Rule (REPLACES carrier_wave):
- Ambient motion MUST originate from the hero math entity itself:
  * TracerDot running along a FunctionGraph curve
  * Vector rotating phase continuously on unit circle
  * Eigenvalue pulsing on matrix diagonal
  * Gradient particles flowing along descent direction
  * Opacity pulse on key LaTeX terms
- ABSOLUTELY BANNED:
  * FunctionGraph sine wave running along bottom of screen (old carrier_wave)
  * Fake hologram environment (setup_ambient_hologram_environment)
  * Scale breathing (animate.scale loops)
  * Random decorative motion unrelated to the math being taught

### D. LaTeX Standards:
- LaTeX must serve pedagogical purpose — reveal understanding, not decorate
- Use `MathTex` for pure math, `Text(font="Be Vietnam Pro")` for Vietnamese labels
- Equation revelation should be staged: show components first, then assemble
- ZERO raw LaTeX in Text() — separate text and math renderers

## 4. Anti-Context-Loss Firewall

### A. The Problem:
AI models lose context when producing long episodes (8+ minutes), causing:
- Lazy coding (200 lines instead of 800)
- 5-second scenes for 90-second voiceover
- FadeOut to black, frame cloning via tpad
- Loosening freezedetect thresholds to pass

### B. The Solution: Modular Parts
Each Part is a self-contained unit that:
- Fits entirely within model context window
- Has clear input (CONTEXT.json) and output (RESULT.json)
- Can be iterated independently without touching other Parts
- Renders in ~30s via Docker cache (fail-fast)

### C. Assembly Protocol:
1. All Parts rendered independently → 10-12 video clips
2. Assembly script (`assemble_modular_episode.py`) reads all PART_RESULT.json files
3. Concatenates clips with smooth transitions (0.3s crossfade, NOT hard cut)
4. Brand opener inserted after Part 01 (5.80s bumper)
5. SRT generated per-part then merged with timestamp offsets
6. Audio mastering: voice conditioning → BGM pocketing → amix normalize=0 → alimiter
7. Final master: 2560x1440 @ 60fps, EBU R128 -14.5 LUFS

## 5. Integration with Content Factory Harness

The modular episode harness extends (does not replace) the existing Content Factory 6-gate system:
- Gate 0: Director Approval (verify_director_approval)
- Gate 1: Contract Validation (per-part CONTEXT.json)
- Gate 2: Timeline Compilation (per-part audio alignment)
- Gate 3: Evidence Hash (SHA-256 per-part closure)
- Gate 4: Media Probe (2560x1440, 60fps)
- Gate 5: Freeze Detect (per-part, then master)
- Gate 6: Human Approval (audio, visual, golden)

## 6. Naming Conventions

### Files:
- Script: `part_XX_<slug>.md` (e.g., `part_01_hook_fourier.md`)
- Manim: `part_XX_<slug>.py` (one Scene class per file)
- Audio: `part_XX_<slug>.wav`
- Context: `PART_XX_CONTEXT.json`
- Result: `PART_XX_RESULT.json`

### Scene Classes:
- `TapXX_PartYY_<DescriptiveName>(Scene)`
- Example: `Tap03_Part05_FourierSpectralReveal(Scene)`

## 7. Banned Patterns (Absolute Prohibitions)

1. **carrier_wave**: `FunctionGraph(lambda x: -3.3 + 0.15 * sin(...))` at bottom of screen
2. **setup_ambient_hologram_environment**: Fake hologram bars
3. **Scale breathing**: `target.animate.scale(1.025)` loops
4. **Monolithic production**: Processing entire episode (8+ min) in one context
5. **Black fadeout**: `FadeOut()` all mobjects while voiceover continues
6. **Slide-deck**: RoundedRectangle boxes with bullet-point text, no math
7. **ASCII art**: Text-based diagrams (`[Input] -> [Embedding] -> [Output]`)
8. **Camera drift**: FFmpeg crop/zoompan/rotate filters on Manim output
9. **Sáo ngữ giật gân**: "2 giờ sáng", "sự thật tàn nhẫn", "lạnh lùng", etc.
10. **Pipeline tag leakage**: "V3", "Quality Gate", "Pipeline", "Sprint" in video content

## 8. Golden Brand Immutable Assets (Trust Boundary)

Agent KHÔNG ĐƯỢC render lại các clip sau. Chỉ concat vào master video qua `golden_brand_constants.py`.

| Asset | File | Duration | Khi nào dùng |
|-------|------|----------|-------------|
| Logo Opener | `zenpham_opener_clip_2k60_muxed.mp4` | 5.80s | Sau Part 01 (Hook) |
| Closing CTA | `zenpham_closing_cta_2k60_muxed.mp4` | 8.00s | Cuối master, sau Part cuối cùng |
| Watermark | `zenpham_subtle_watermark_150px.png` | — | Góc phải dưới (tùy chọn) |

### Integrity Verification:
- SHA-256 hash của mỗi asset phải khớp `golden_brand_constants.py`
- Nếu agent sửa đổi file brand → Gold Pipeline Gate CRITICAL FAIL
- Nếu cần thay đổi nội dung brand → yêu cầu human approval → render lại bằng scripts trong `assets/brand/zenpham-brand-kit/` → update SHA-256

### Master Duration Invariant:
$$D_{\text{master}} = \sum_{i=1}^{N} \text{dur}(\text{Part}_i) + 5.80\text{s} + 8.00\text{s} \pm 1.0\text{s}$$

### Subtitle Timing:
- 0 cues during opener (5.80s gap after Part 01)
- All Part 02+ subtitle cues shift forward by +5.80s
- 0 cues during Closing CTA (last 8.00s)

## 9. Gold Pipeline Verification (Post-Assembly)

Sau khi assemble master video, chạy Gold Pipeline gate:
```bash
python3 assets/scripts_video/gold_pipeline_gate.py --master path/to/master.mp4
```

7 Gates kiểm tra trên video THỰC (không phải AST code):
- **Gate A**: Opener Presence (SSIM keyframe matching)
- **Gate B**: Closing CTA Presence (SSIM keyframe matching)
- **Gate C**: ColdOpen Quality (math mobjects, no logo at start)
- **Gate D**: Script ↔ Visual LaTeX Match (Jaccard ≥ 0.70)
- **Gate E**: Thumbnail Validity (> 50KB, ≥ 1280x720)
- **Gate F**: Master Structural Integrity (2560x1440, 60fps, freeze < 4s)
- **Gate G**: Brand Hash Integrity (SHA-256 match)

Mọi CRITICAL gate FAIL → chặn xuất bản.

---

## 10. Per-Scene Quality Harness Protocol (`scene_harness.py` & `produce_scene.py`)

Quy trình sản xuất bắt buộc chạy tuần tự theo **Per-Scene Quality Harness**.
**BẤT BIẾN: FAIL = STOP** — Nếu phân cảnh $N$ thất bại bất kỳ gate nào, pipeline DỪNG LẬP TỨC để sửa, tuyệt đối không render tiếp để tránh rework dây chuyền.

Mỗi phân cảnh bắt buộc có tệp hợp đồng JSON tương ứng (`contracts/scene_XX_contract.json`) và trải qua **4 Quality Gates**:

```
┌────────────────────────────────────────────────────────────┐
│ GATE 1: SCRIPT QUALITY (part_XX.md & scene_XX.txt)         │
│   • Banned words scan: 0 vi phạm                           │
│   • Sentence count: Nằm trong khoảng hợp đồng [min, max]   │
│   • LaTeX Cues: Khớp 100% các ký hiệu trong HTML comments  │
│   • No Raw LaTeX in Spoken Text: Văn bản đọc thuần Việt    │
├────────────────────────────────────────────────────────────┤
│ GATE 2: CODE AST QUALITY (part_XX.py)                      │
│   • Cú pháp Python AST hợp lệ                              │
│   • Zero hardcoded font_size (Bắt buộc dùng FS_... tokens) │
│   • Background: add_deep_space_background(self)           │
│   • Required Mobjects: Đầy đủ hình học theo hợp đồng       │
│   • SVG Badge: Tích hợp DuotoneIcon từ assets/duotone/     │
│   • Animation count: Tối thiểu >= 3 staged animations      │
├────────────────────────────────────────────────────────────┤
│ GATE 3: RENDER QUALITY (part_XX_*.mp4)                     │
│   • Resolution: 2560x1440 (2K QHD), FPS: 60.0              │
│   • Duration: Nằm trong khoảng hợp đồng duration_target_s  │
│   • File size: > 100KB, không lỗi khung đen                │
├────────────────────────────────────────────────────────────┤
│ GATE 4: AUDIO QUALITY (scene_XX.wav)                       │
│   • Format: 48,000 Hz, Stereo (2 channels)                 │
│   • Duration: Khớp kịch bản (> 5.0s)                       │
│   • Loudness: EBU R128 -14.5 LUFS (khoảng: -18.0 đến -12.0)│
│   • True Peak: <= -1.5 dBTP (chuẩn studio <= -4.0 dBFS)    │
└────────────────────────────────────────────────────────────┘
```

---

## 11. Chuẩn Hóa TTS & Ngữ Pháp Song Ngữ Việt - Anh (Golden Method v4)

### A. Quy Tắc Neo Ngữ Pháp Tiếng Việt (Grammatical Anchoring Invariant):
OmniVoice khi gặp thuật ngữ tiếng Anh trơ trọi sẽ bị ngập ngừng hoặc phát âm sai.
**BẮT BUỘC:** Đặt từ định danh ngữ pháp tiếng Việt ngay trước thuật ngữ tiếng Anh:
- `hàm`: hàm Softmax, hàm loss, hàm Sigmoid, hàm ReLU
- `thuật toán`: thuật toán Levenberg-Marquardt, thuật toán Gradient Descent, thuật toán Backpropagation
- `phương pháp`: phương pháp Gauss-Newton, phương pháp Monte Carlo, phương pháp PCA
- `mô hình` / `kiến trúc`: mô hình Brown-Conrady, mô hình Transformer, kiến trúc CNN
- `ma trận`: ma trận K, ma trận Hessian, ma trận covariance
- `hệ số`: hệ số k1, hệ số tiếp tuyến p1, hệ số méo quang học
- `bản đồ`: bản đồ remap, bản đồ ánh xạ điểm ảnh
- `tốc độ`: tốc độ 120 FPS, tốc độ learning rate

### B. CẤM Bare English Term Ở Đầu Câu (Zero Bare Start):
Tuyệt đối không để thuật ngữ tiếng Anh đứng đầu câu:
- ❌ *Sai:* "Levenberg-Marquardt là thuật toán tối ưu phi tuyến tính."
- ✅ *Đúng:* "Thuật toán Levenberg-Marquardt là phương pháp tối ưu phi tuyến tính."
- ❌ *Sai:* "Fisheye lens làm cong không gian."
- ✅ *Đúng:* "Ống kính mắt cá fisheye làm cong không gian."

### C. CẤM Phiên Âm Chắp Vá (Zero Fake Transliteration):
- ❌ "Phi-sơ-ai", "Gờ-ra-đi-ân", "Li-ven-bớt Mác-quát", "Gau-xơ Niu-tơn", "Tên-xơ-Rờ-Tê"
- ✅ Giữ nguyên chính tả tiếng Anh: `Fisheye`, `Gradient`, `Levenberg-Marquardt`, `Gauss-Newton`, `TensorRT`.

### D. Phân Tách Tuyệt Đối Giữa Lời Thoại & Ký Hiệu LaTeX (Spoken vs LaTeX Separation):
- **Văn bản nói (`scene_XX.txt`):** 100% viết bằng từ ngữ đọc tự nhiên. Tuyệt đối không chứa mã `\frac`, `\begin`, `\theta`, `^2`.
  - $\theta \to$ `góc tới theta` hoặc `góc tới tê-ta`
  - $r = 2f \cdot \sin(\theta/2) \to$ `bán kính r bằng hai lần tiêu cự nhân sin của một nửa góc tới`
  - $K \to$ `ma trận K`
  - $\pi \to$ `số Pi`
- **Tệp kịch bản (`part_XX.md`):** Các công thức LaTeX dùng cho hoạt họa Manim **BẮT BUỘC** nằm gọn trong HTML comment ở đầu tệp để Gate D khớp Jaccard mà không làm rò rỉ vào bộ đọc:
  ```markdown
  # Part 01: Chiếc Bụng Tròn Của Không Gian

  <!--
  LaTeX Visual Cues:
  $C = 2\pi r \quad \longleftrightarrow \quad 2\theta$
  $(x, y)$
  $r' = r(1 + k r^2)$
  -->

  Đã bao giờ bạn chụp một bức ảnh góc rộng...
  ```

### E. Phong Cách Lời Thoại (3Blue1Brown × Median Wonder-Driven):
- Điềm tĩnh, nhẹ nhàng, khơi gợi tò mò từ hiện thực đời thường.
- **Banned Sensation Words:** "2 giờ sáng", "lạnh lùng", "tàn nhẫn", "thực chiến", "thảm họa", "tuyệt đối", "phi thường", "bí mật vật lý".
- **Banned Repetitive Crutches:** "đóng vai trò", "không... mà...", "khi... khi...".

### F. Thông Số Âm Thanh Studio:
- Giọng mẫu: `zenpham-zen-meditation-mientay`
- Tốc độ: **0.94x** (khoảng dừng thở tự nhiên giữa các câu)
- Chuẩn xuất xưởng: **48,000 Hz, Stereo, EBU R128 -14.5 LUFS**, True Peak $\le$ **-1.5 dBTP**.
- **Banned Audio Filters:**
  - `afftdn`: Gây biến dạng pha kim loại (phase warble) $\to$ **CẤM**.
  - `lowpass=11000`: Bóp nghẹt dải cao và làm hỏng âm hưởng nhạc hiệu $\to$ **CẤM**.

---

## 12. Hệ Thống Thiết Kế ZenManim CSS & Chuẩn Mực Hoạt Họa

### A. Bảng Token Thiết Kế Bắt Buộc (ZenManim CSS):
Mọi tệp cảnh Manim (`part_XX.py`) bắt buộc import và sử dụng thống nhất hệ token:
```python
# ZenManim CSS Design Tokens
COLOR_CYAN = "#00f0ff"
COLOR_AMBER = "#fbbf24"
COLOR_EMERALD = "#34d399"
COLOR_ROSE = "#fb7185"
COLOR_TEXT = "#f8fafc"
COLOR_MUTED = "#94a3b8"
COLOR_GRID = "#1e293b"
COLOR_CARD_BG = "#090d16"
FONT_FAMILY = "Roboto"

# Typography Scale (BẮT BUỘC dùng, CẤM hardcode font_size=\d+)
FS_TITLE = 24
FS_SUBTITLE = 13
FS_FORMULA_LG = 32
FS_FORMULA_MD = 28
FS_FORMULA_SM = 24
FS_LABEL = 12
FS_BODY = 14

# Card System
CARD_RADIUS = 0.15
CARD_OPACITY = 0.92
CARD_STROKE_W = 1.5
```

### B. Nền Không Gian Đa Chiều (Deep Space Gradient Background):
- **CẤM** đặt nền phẳng đơn sắc `self.camera.background_color = COLOR_BG`.
- **BẮT BUỘC** gọi `add_deep_space_background(self)` từ module `zen_deep_space_bg.py`.
- Sử dụng dithered radial gradient 2K kết xuất bằng NumPy + Pillow (tâm `#0a1329` Deep Cosmic Navy $\to$ rìa `#040508` Obsidian Void), triệt tiêu hoàn toàn hiện tượng color banding.

### C. Tích Hợp Biểu Tượng Phosphor Duotone SVG:
- Mỗi phân cảnh tích hợp 1 biểu tượng Duotone SVG tương ứng với chủ đề sư phạm từ kho 1,512 icon trong `/assets/duotone/`.
- Cú pháp chuẩn: `badge = DuotoneIcon("<tên_icon>", size=0.5, primary_color=COLOR_CYAN, style="minimal")`.
- CẤM truyền tham số `color=` vào `DuotoneIcon` (bắt buộc dùng `primary_color=`).

### D. Đồng Bộ Thời Lượng & Chuyển Động Thực Tế:
- Thời lượng chuyển động Manim (`sum(run_time) + sum(wait)`) **BẮT BUỘC** khớp với thời lượng thoại của từng cảnh ($\pm 2.0$s).
- **CẤM** dựng cảnh ngắn 15s rồi dùng lệnh giãn thời gian `setpts` hay chèn freeze frames giữ ảnh tĩnh $> 4.0$s.
- Chia nhỏ hoạt họa thành 3-5 phân đoạn (staged animation beats) chuyển động tịnh tiến theo từng câu thoại.

---

## 13. Chuẩn Mực Thiết Kế Thumbnail 2K (High-CTR, Zero Overlap, Visual Depth)

Tệp tạo thumbnail: `generate_thumbnail_industrial_ai_tap_XX_2k.py`.
Độ phân giải chuẩn: **2560×1440 @ 2K QHD (16:9)**.

### A. Quy Tắc Anti-Slide / Anti-Card (Bất Biến):
- **TUYỆT ĐỐI CẤM** dùng các khối thẻ Card to đùng chứa nhiều gạch đầu dòng dày đặc như slide bài giảng.
- Không dùng hộp văn bản tù túng gây lỗi tràn chữ hoặc cắt cụt từ ngữ trên giao diện di động.
- Sử dụng bố cục **3 Cột Chỉ Số Kỹ Thuật (HUD Metrics)** thanh lịch, thoáng đãng:
  - Giá trị lớn (Font Black ~42pt): `120 FPS` | `±0.038px` | `BẬC 5`
  - Nhãn kỹ thuật nhỏ phía dưới (Font Bold ~22pt): `TỐC ĐỘ GPU REALTIME` | `ĐỘ CHUẨN XÁC SUB-PIXEL` | `ĐA THỨC BROWN-CONRADY`
  - Vạch gạch màu điểm nhấn trên đỉnh mỗi cột.

### B. Quy Tắc Bounding Box Tự Động (Zero Overlap Invariant):
- Mọi huy hiệu, khung viền (pill badge, formula capsule) **BẮT BUỘC** tính toán kích thước động dựa trên văn bản thực tế:
  ```python
  bbox = font.getbbox(text)
  box_w = bbox[2] - bbox[0] + padding_x * 2
  box_h = bbox[3] - bbox[1] + padding_y * 2
  ```
- **CẤM** sử dụng emoji thô trong chuỗi văn bản (`🔴`, `⚡`, `🎯`) nếu font không có bảng mã màu emoji (ngăn chặn lỗi ô vuông `▯`). Thay bằng hình vẽ vector (chấm tròn LED, hình thoi) vẽ trực tiếp bằng `ImageDraw`.

### C. Chiều Sâu Thị Giác Quang Học (Volumetric Optical Depth):
- Ánh sáng thể tích tỏa tia (radial volumetric glow) phía sau chủ thể chính.
- Thấu kính mắt cá hoặc mô hình 3D phải có:
  - Khối cầu kính trong suốt có bóng chuyển sắc (translucent glass shading).
  - Lưới không gian bên trong bị uốn cong theo đúng vật lý quang học (curved barrel distortion mesh).
  - Ánh sáng ven vành trăng khuyết (Fresnel rim sheen).
  - Hệ trục đo lường laser và các điểm neo sub-pixel phát sáng nhẹ.
- Capsule công thức toán học nổi bên dưới chủ thể với viền phát sáng mờ.

---

## 14. Quy Chuẩn Sản Xuất YouTube Shorts 9:16 — Cấm Tuyệt Đối Video-in-Video Embedding

Độ phân giải chuẩn: **$1440 \times 2560$ (9:16 Vertical 2K QHD @ 60fps)**.  
Cấu hình Manim: `config.frame_width = 9.0`, `config.frame_height = 16.0`.  
Mã nguồn: `episode_industrial_ai_tap_XX/manim_short_tap_XX.py`.

### A. Nguyên Tắc Bất Biến: Render Độc Lập 100% Bằng Manim (Zero Video-in-Video Embedding):
- **TUYỆT ĐỐI CẤM** dùng các kỹ thuật chắp vá:
  - CẤM tạo ảnh nền tĩnh bằng PIL rồi dùng bộ lọc FFmpeg `overlay` để nhúng video 16:9 vào khung giữa (gây lỗi sọc tím/xanh interlaced, biến dạng pixel và co rúm diện tích hiển thị).
  - CẤM co kéo video ngang 16:9 nhét vào khung dọc (letterboxing/pillarboxing).
- **BẮT BUỘC**: Toàn bộ các phân cảnh của Short phải được lập trình và render độc lập trực tiếp bằng Manim 9:16 bám sát kịch bản.
- Mọi thành phần hiển thị (Badge, Header Title, Terminal HUD, Lưới PCB/Chip BGA, Động học méo thấu kính, Ma trận biến đổi, Mũi tên điều hướng CTA) đều là vector Mobject gốc của Manim.

### B. Vùng An Toàn Giao Diện YouTube Shorts (UI Safe Zones):
- **Right-Rail Safe Zone ($X \le +3.1$)**:
  Mép phải $X > +3.1$ là nơi YouTube đặt cụm nút tương tác (Like, Dislike, Comment, Share, Sound Remix). Bắt buộc toàn bộ text, mobject, công thức LaTeX phải nằm trong $X \le +3.1$ (giới hạn chiều rộng $\le 6.8$, căn giữa hoặc lệch nhẹ về bên trái).
- **Bottom UI Safe Zone ($Y \ge -6.0$)**:
  Vùng $Y < -6.2$ bị che lấp bởi thanh tiến trình video, Avatar kênh, Tiêu đề Short và nút bấm "Video liên quan" (Related Video). Tuyệt đối không để text hay chi tiết quan trọng rơi xuống dưới $Y = -6.0$.
- **Top Header Safe Zone ($Y \le +6.6$)**:
  Tránh thanh tìm kiếm và icon camera ở mép trên cùng màn hình điện thoại.

### C. Âm Thanh Chuẩn YouTube Shorts (AQG Compliance):
- Giọng đọc Zen Miền Tây (0.94x – 0.96x) ấm áp, rõ nét.
- Chuẩn EBU R128: **$-14.0 \pm 0.5$ LUFS**, True Peak $\le -1.0$ dBTP (chống méo khi YouTube nén lại qua Opus).
- Nhạc nền Ambient Lo-Fi ducking sâu $-18$dB đến $-22$dB khi có giọng nói; fade-in 1.5s, fade-out 2.0s.
- **TUYỆT ĐỐI CẤM** dùng các bộ lọc phá hoại âm thanh: CẤM `afftdn=nf=-28`, CẤM `lowpass=11000`.

---

## 15. Quy Chuẩn Phân Cảnh Cầu Nối Tập Kế Tiếp (Next-Episode Bridge) & Cô Lập Tài Nguyên Series Tuyệt Đối

### A. Bất Biến Bố Cục Hero Thumbnail (Next-Episode Bridge Invariant):
Trong phân cảnh kết thúc (Outro / Part cuối, cụ thể là Beat 3 của Outro), khi người dẫn chuyện giới thiệu tập kế tiếp:
1. **BẮT BUỘC hiển thị Hero 2K Thumbnail (16:9)** của tập kế tiếp làm chủ thể trung tâm trong layout.
2. **CẤM TUYỆT ĐỐI fallback về thẻ chữ rỗng (Empty Text Card):** Không được hiển thị một khung chữ rỗng không có ảnh đại diện của tập kế tiếp. Mã nguồn Manim bắt buộc phải tìm và nhúng tệp ảnh `thumb_{series}_tap_{next}_hero_2k.jpg` qua `ImageMobject`. Nếu không tìm thấy file, pipeline bắt buộc phải báo lỗi dừng ngay lập tức (FAIL = STOP) thay vì âm thầm nhảy sang nhánh fallback chữ.
3. **Cấu trúc 4 Tầng Bố Cục Chuẩn (4-Layer Bridge Layout):**
   - **Tầng 1 - Next Episode Header (Y in [+2.6, +3.25]):**
     - Icon điều hướng: `DuotoneIcon("arrow-circle-right", size=0.50)` hoặc `DuotoneIcon("play-circle")`.
     - Huy hiệu phân kỳ: `TẬP TIẾP THEO: TẬP XX` (Màu Hổ phách / Cyan, Font Bold).
     - Tiêu đề tập kế tiếp: Tiêu đề tiếng Việt chuẩn Title Case (Font Bold ~18-20pt, màu Cyan/Trắng sáng).
     - Phụ đề phương pháp: Danh sách từ khóa thuật toán / công nghệ cốt lõi của tập kế tiếp (Font Regular ~12pt, màu Muted).
   - **Tầng 2 - Hero 2K Thumbnail Mobject (Y in [+0.4, +0.65]):**
     - Kích thước hiển thị: `set_width(6.8)` (chuẩn 16:9, chiều rộng 6.8 đơn vị Manim, chiều cao ~3.82 đơn vị).
     - Viền Neon kép phát sáng: Khung `RoundedRectangle` bọc ngoài có `corner_radius=0.16`, viền vàng hổ phách (`COLOR_AMBER`) và hiệu ứng thở viền cyan/ngọc lục bảo (`rate_func=there_and_back`).
     - Tag nhận diện: Huy hiệu `EPISODE PREVIEW` hoặc `2K QHD` đặt góc ảnh.
   - **Tầng 3 - Mathematical Spine Formula Capsule (Y in [-0.95, -0.75]):**
     - Viên nang tối màu chứa công thức toán học đỉnh cao của tập tiếp theo (`MathTex`).
     - Nhãn định danh thuật toán / phương trình (ví dụ: `\min \sum \text{Cost}`, `\max \sum v_i x_i`, `Kalman Filter`).
   - **Tầng 4 - Brand HUD (Safe Zone Y in [-1.65, -1.35]):**
     - Dải nhận diện thương hiệu ZenPham, chấm đèn LED phát sáng và lời kêu gọi theo dõi trọn bộ series.

### B. Bất Biến Cô Lập Tài Nguyên Series Tuyệt Đối (Strict Series Asset Isolation Invariant):
1. **Một Series = Một Hệ Sinh Thái Tài Nguyên Khép Kín:**
   - Series **Logistics AI** (`logistics_ai`):
     * Chỉ dùng Mosaic 9 tập Logistics: `logistics_ai_9_thumbnails_mosaic.png`.
     * Chỉ dùng Closing CTA Bumper của Logistics AI: `zenpham_closing_cta_logistics_ai_2k60_muxed.mp4`.
     * Chỉ dùng Thumbnail tập kế tiếp của Logistics AI: `thumb_logistics_tap_XX_hero_2k.jpg`.
   - Series **Industrial AI** (`industrial_ai`):
     * Chỉ dùng Mosaic 5 tập Industrial: `industrial_ai_5_thumbnails_mosaic.png`.
     * Chỉ dùng Closing CTA Bumper của Industrial AI: `zenpham_closing_cta_industrial_ai_2k60_muxed.mp4`.
     * Chỉ dùng Thumbnail của Industrial AI: `thumb_industrial_tap_XX_hero_2k.jpg`.
2. **CẤM Rò Rỉ Chéo (Zero Cross-Series Leakage):**
   - **TUYỆT ĐỐI CẤM** dùng chung biến mặc định có cơ chế ngầm fallback sang series khác (ví dụ: `CLOSING_CTA_CLIP` nếu không tìm thấy clip của series hiện tại lại tự động lấy clip của series khác).
   - Mọi script dựng master (`assemble_*.py`) và script Manim Outro (`part_10_outro.py`) **bắt buộc** gọi hàm định danh series rõ ràng: `get_series_closing_cta(series_name)`.
   - Cổng kiểm định `gold_pipeline_gate.py` sẽ quét và đánh dấu **HARD FAIL** nếu phát hiện bất kỳ tài nguyên hoặc từ khóa của series khác rò rỉ vào tập đang kiểm tra.

---

## 16. Pre-Production Asset Hard Gate (Gate M) & Zero-Tolerance Readiness Policy

### A. Nguyên Tắc Tiền Kiểm Tài Nguyên Tuyệt Đối (Pre-Production Hard Gate):
Trước khi khởi động bất kỳ tiến trình render Manim (Docker) hay lắp ráp video master (FFmpeg) nào:
1. **BẮT BUỘC thực thi tiền kiểm tài nguyên (Preflight Asset Gate)** thông qua module `preflight_asset_gate.py`.
2. **Nguyên lý Zero-Tolerance (Chặn Đứng Tức Thì):** Nếu phát hiện thiếu BẤT KỲ tài nguyên nào hoặc tài nguyên không đạt chuẩn kỹ thuật, toàn bộ pipeline bắt buộc phải **HARD FAIL** (dừng ngay lập tức với Exit Code 1), in bảng chẩn đoán lỗi chi tiết và ngăn chặn hoàn toàn việc tiêu tốn chu kỳ tính toán GPU/CPU.

### B. Danh Mục Tài Nguyên Giám Sát Bắt Buộc:
1. **Bridge Scene Assets (Cầu Nối Tập Kế Tiếp):**
   - Hero 2K Thumbnail tập tiếp theo (`thumb_{series}_tap_{next_ep:02d}_hero_2k.jpg`): Phải tồn tại trên đĩa.
   - Dung lượng $\ge 50\text{ KB}$, tỉ lệ 16:9, độ phân giải tối thiểu $\ge 1280\times 720$ (chuẩn $2560\times 1440$).
   - Tuân thủ nghiêm ngặt Strict Series Isolation (không trỏ nhầm sang thumbnail của series khác).
2. **CTA Scene Assets (Lưới Mosaic Outro Beat 2):**
   - Tệp ảnh Mosaic series (`{series}_mosaic.png`): Phải tồn tại vật lý.
   - Dung lượng $\ge 100\text{ KB}$, tỉ lệ 16:9, độ phân giải $\ge 1280\times 720$.
   - Đúng series quy định (`logistics_ai_9_thumbnails_mosaic.png` cho Logistics AI, `industrial_ai_5_thumbnails_mosaic.png` cho Industrial AI).
3. **Closing Bumper Assets (Màn Hình Kết Thúc 8.00s):**
   - Tệp video `zenpham_closing_cta_{series}_2k60_muxed.mp4`: Phải tồn tại vật lý.
   - Dung lượng $\ge 1.0\text{ MB}$, thời lượng chính xác $8.00 \pm 0.15\text{s}$, độ phân giải $2560\times 1440 @ 60.00\text{ fps}$.
   - Âm thanh stereo ($2$ kênh), tần số lấy mẫu $48000\text{ Hz}$.
   - Khớp mã băm SHA-256 đã đăng ký trong `golden_brand_constants.py`.
4. **Brand Opener & Audio Assets:**
   - Tệp video `zenpham_opener_clip_2k60_muxed.mp4` ($5.80 \pm 0.15\text{s}$, $2560\times 1440 @ 60\text{ fps}$).
   - Nhạc nền BGM và toàn bộ các tệp voiceover (`scene_01.wav` đến `scene_10.wav`) phải đầy đủ, dung lượng hợp lệ (>10KB).

### C. Tích Hợp Bắt Buộc Vào Mọi Runner & Pipeline:
- Mọi render runner (ví dụ: `render_logistics_outros.py`) bắt buộc gọi `verify_preflight_assets()` trước khi khởi tạo luồng worker.
- Mọi assembly script (ví dụ: `assemble_logistics_ai_tap_XX.py`) bắt buộc gọi `verify_preflight_assets()` ở bước 0 trước khi encode clip.
- Bộ kiểm toán `gold_pipeline_gate.py` tích hợp kiểm tra tự động qua **Gate M: PRE-PRODUCTION ASSET READINESS GATE**.

---

## 17. Quy Chuẩn Anti-Slide-Deck & Hero Geometric Kinetics (Gate N) — Nghiêm Cấm Hội Chứng Slide Thuyết Trình

### A. Triết Lý Điện Ảnh Toán Học (Educational Cinema vs. Slide-Deck):
Manim trong ZenPham Video Productions là phương tiện điện ảnh hóa trực giác toán học (3Blue1Brown × Median). Khán giả đến với video để **nhìn thấy cấu trúc động học sâu kín** của thuật toán, không phải để đọc các slide thuyết trình PowerPoint tóm tắt nội dung.

### B. Các Trọng Tội Bị Cấm Tuyệt Đối (Zero-Tolerance Banned Patterns):
1. **CẤM Hộp Văn Bản Đoạn Văn (Paragraph Boxes):** Tuyệt đối không tạo các thẻ `RoundedRectangle` lớn rồi nhét 2-4 dòng văn bản giải thích vào bên trong. Lời giải thích thuộc về voiceover của người dẫn chuyện.
2. **CẤM Gạch Đầu Dòng (Bullet Points):** Không biến màn hình thành slide bài giảng với các danh sách gạch đầu dòng.
3. **CẤM Hoạt Họa Lười Biếng (Lazy Wait Pattern):** Chuỗi lệnh `FadeIn(card)` theo sau bởi `self.wait(1.5)` mà không có bất kỳ tương tác hình học nào là hành vi bị cấm.
4. **CẤM Thiếu Hụt Chuyển Động (Kinetic Undercoverage):** Thời lượng chuyển động thực chất trong phân cảnh (`sum(run_time)`) phải đạt tối thiểu $50\%$ thời lượng audio của phân cảnh đó.

### C. Định Luật Hero Geometry First (Quy Tắc 70/30):
- **70% Diện Tích Trung Tâm (Hero Stage):** Thuộc về các mobject toán học/vật lý động (Mạng đồ thị luồng, Hạt chuyển động, Sóng lan truyền, Bề mặt thế năng, Trường vector, Ma trận biến đổi, Cây phân cấp).
- **30% Diện Tích Phụ Trợ (Telemetry & Brand):** Chỉ dành cho Tiêu đề H1 một dòng ở đỉnh ($Y \approx 3.25$), Metric Badges nhỏ gọn, và Formula Capsule toán học tinh tế.

### D. Kiểm Toán Bắt Buộc Tại Gate N (Anti-Slide-Deck & Geometric Kinetics Gate):
Tích hợp module kiểm định tự động `anti_slide_deck_gate.py` vào `gold_pipeline_gate.py` để quét cây cú pháp (AST) của toàn bộ các file `.py` Manim:
- Đếm số lượng hộp văn bản vs. thực thể hình học động.
- Tính toán tổng thời lượng chuyển động so với thời lượng audio.
- Bất kỳ phân cảnh nào vi phạm sẽ lập tức nhận trạng thái **REJECT**, chặn đứng tiến trình dựng master video.




