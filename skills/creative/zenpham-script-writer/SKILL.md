---
name: zenpham-script-writer
description: ZENPHAM channel script writer: noir, philosophical, 8–20 scenes.
version: 2.1.0
author: ZENPHAM, Hermes Agent
license: MIT
platforms:
  - linux
  - macos
  - windows
metadata:
  hermes:
    tags:
      - zenpham
      - script-writing
      - video-production
      - content-creation
      - philosophical
      - noir
    related_skills:
      - pexels-visual-search
      - agnes-ai-video
      - content-factory
      - video-motion-studio
---

# ZENPHAM Script Writer Skill

Produces cinematic noir video scripts for the **ZENPHAM** YouTube/TikTok channel.
Each script runs 8–20 scenes (8–10s per scene), voiced by **Zen** (deep
Southern Vietnamese baritone via OmniVoice TTS, reference `zen-style.wav`), with philosophical grounding
in Stoicism and Existentialism, and a unified opening/closing style.

Output is a `.md` file compatible with `make_karaoke_subs.py` and
`assemble_podcast.py` in the asset pipeline.

## When to Use

Activate this skill when the user asks to:
- Create a new ZENPHAM video script on a current-event or philosophical topic
- Generate a noir-style video outline with 8–20 scenes
- Write script lines with Pexels search keywords, voice acting notes, and
  karaoke-ready dialogue
- Research a topic via web search, then structure it into a scene-by-scene
  storyboard
- Plan a new video for the ZENPHAM pipeline (fetch_stock → tts → post_stock → assemble)

## Prerequisites

1. **Pipeline assets** at `assets/scripts_video/` with:
   - `footage_manager.py` — Footage Asset Pool (cache-first B-roll search, Pexels fallback, Noir/Old-Time grade)
   - `fetch_stock.py` & `post_stock.py` — legacy fallback stock video search & post-processing
   - `tts_zen.py` — OmniVoice TTS with Zen-Style Mood & Speed profiles (`assets/voices/zen_voice_profiles.yaml`)
   - `make_karaoke_subs.py` — ASS karaoke subtitle generator
   - `assemble_podcast.py` — final video assembly (--md, --out, --music, integrates endcard)
   - `kanban_sync.py` — Hermes Kanban board task synchronizer (http://127.0.0.1:9119/kanban)
   - `content_reporter.py` — Performance analytics & Telegram automated reporter
2. **OmniVoice TTS** running at `http://10.123.214.178:80` (with S3 bucket `omnivoice-audio` at MinIO `10.123.214.249:9000`)
3. **Pexels API keys** in `~/.hermes/.env` (keys for rotation)
4. **FFmpeg** installed on the workstation
5. **`web_search`** tool available for topic research

## How to Run

Validate before producing, then execute the autonomous pipeline:

```bash
cd assets/scripts_video
# 1. Sync script to Kanban board
python3 kanban_sync.py --seed

# 2. Prepare footage from local pool or Pexels
python3 footage_manager.py --prepare your_script.md

# 3. Generate Zen voice with Mood & Speed profiling
python3 tts_zen.py --md your_script.md --mood suy_tu_tram_lang

# 4. Assemble final 9:16 Shorts with karaoke subtitles
python3 assemble_podcast.py --md your_script.md --out your_video_final.mp4

# OR run all steps end-to-end autonomously:
python3 pipeline_zenpham.py --md your_script.md
```

## Quick Reference

```
ZENPHAM script structure:
  Scene 1   — Opening hook (unified intro)
  Scenes 2–7  — Body: 1 core idea per scene, 2–3 philosophers max
  Scenes 8–10 — Climax: personal story leads, stats support
  Scene 11–12 — Close (unified outro)

Per scene:
  • Visual: noir B&W, low-key lighting, film grain
  • Audio: soft piano/ambient, no rain
  • Dialogue: 2–4 sentences, 8–10s voice span, one thesis per scene
  • Tốc độ đọc: 0.82–1.08; per-scene OmniVoice pace
  • [Pexels keywords] for footage search
```

- **Endcard TAGLINE**: "Sống nhẹ thôi, ngay giữa hiện tại."
- **Background music** from `assets/background_music/` (local, copyright-free). Loop with `-stream_loop -1`. Default: Quiet Room Glow.

## Procedure

### Stage 1 — Topic Research

Read `assets/scripts_video/topic_registry.json` first. Use `web_search` to
find 3–5 recent articles (≤6 months old) on a thesis not already produced.
Extract: 1 key statistic, 1 conflicting viewpoint, 1 personal angle. Keep it
tight — the script is poetry, not a white paper. Store in
`references/research.md`.

### Stage 2 — Script Structure & Narrative Flow

Plan 8–10 scenes (8–10s per scene → 70–90s), optimal for modern YouTube Shorts retention.

**Core Narrative Rules (BẮT BUỘC):**
1. **Mạch tự sự liên hoàn (Seamless Storytelling Flow):**
   - Tuyệt đối cấm các câu châm ngôn rời rạc dạng khẩu hiệu. Toàn bộ kịch bản là MỘT MẠCH SUY TƯ THỐNG NHẤT của người đàn ông miền Tây 40 tuổi (ZenPham).
    - Từ đoạn 2 trở đi, lời thoại PHẢI có từ nối chuyển tiếp tự nhiên (`"Thế nhưng...", "Bạn có để ý...", "Người ta cứ ngỡ...", "Để rồi đến một ngày...", "Tôi nhận ra...", "Hóa ra..."`).
2. **Điểm chạm đời sống đa dạng (5 Hook Archetypes — CẤM RẬP KHUÔN):**
   - **Tuyệt đối CẤM lặp lại mô-típ:** `"Giữa đêm khuya..."`, `"Nửa đêm..."`, `"Ánh sáng xanh từ màn hình..."`, `"Màn đêm yên tĩnh..."`, `"khiến tôi giật mình nhận ra"`.
   - **5 hình thức mở đầu đa dạng linh hoạt:**
     1. *Chi tiết đời thường / Giác quan:* Ly cà phê sáng nguội ngắt, tiếng chuông thông báo giữa bữa cơm, hóa đơn mua sắm đồ không dùng...
     2. *Nghịch lý thời sự / Xã hội:* "Càng nhiều công cụ tiết kiệm thời gian, ta lại càng thấy mình không có thời gian..."
     3. *Góc nhìn kỹ sư 20 năm làm nghề:* "Hai mươi năm làm việc với máy tính, tôi nhận ra cỗ máy dễ hiểu hơn con người..."
     4. *Câu hỏi khơi gợi trực diện:* "Đã bao lâu rồi bạn không có một buổi chiều ngồi ngắm mưa mà không rút điện thoại ra xem?"
     5. *Tình huống đối thoại / Quan sát:* "Hôm qua trên xe buýt, tôi thấy một đứa bé cố vuốt ngón tay lên mặt kính cửa sổ..."
3. **B-Roll điện ảnh chống trùng lặp & Quy tắc khớp >90% (Pexels Visual Matcher):**
   - [Pexels keywords] phải gợi tả khung cảnh giàu cảm xúc (`rain on window dark room`, `solitary man sitting coffee morning light`, `blurry city lights night walk`) thay vì các từ chung chung (`technology`, `happy`).
   - **QUY TẮC CỐT LÕI (>90% MATCH RULE)**: Chạy `assets/scripts_video/pexels_visual_matcher.py` để chấm điểm ngữ cảnh của từng phân cảnh.
      - **Nếu tìm được Video Footage khớp $\ge 90\%$ (Score $\ge 0.90$)**: BẮT BUỘC dùng trực tiếp Video Footage của Pexels, gán thẻ `[VISUAL: PEXELS_STOCK #ID (Khớp: XX%)]` và tải clip về `assets/footage_pool/clips/`.
      - **Nếu khớp $< 90\%$**: Chuyển giao sang Manim hoạt họa hoặc custom assets minh họa.
4. **Phân Rã Khối Dưới 3 Phút (Sub-3-Minute Modular Chunking & Act Focus):**
   - **Tuyệt đối cấm kịch bản nguyên khối:** Đối với định dạng video phân tích kỹ thuật 16:9, kịch bản BẮT BUỘC chia thành các phân cảnh ngắn hơn 3 phút (mỗi Scene/Chapter $\le 180$s, tối ưu 60s–95s).
   - **Cấu trúc 3 Hồi:** Hồi A (Khởi nguyên & Ẩn dụ đời thường $\le 180$s) $\to$ Hồi B (Trọng tâm Toán học & Cơ chế $\le 100$s) $\to$ Hồi C (Thực nghiệm phòng lab & Triết lý làm nghề $\le 240$s).
   - Từng phân cảnh bóc tách rõ các phân đoạn nhịp điệu (Parts/Beats: Part 1.1, 1.2,...) để người làm hoạt họa Manim và AI Agent tập trung ngữ cảnh, thiết kế chuyển động chính xác từng giây, tránh loãng ý và chống đóng băng hình ảnh.

**Philosophical framework (lồng ghép tự nhiên, không lên gân):**
- Epictetus / Stoicism — vòng tròn kiểm soát, phân biệt cái ta có thể và không thể can thiệp
- Sartre / Existentialism — tự do hiện sinh, trách nhiệm với lựa chọn của chính mình
- Camus / Absurdism — nhìn thẳng vào thực tại phi lý mà vẫn mỉm cười sống trọn vẹn
- Foucault — nhà tù vô hình (Panopticon), quyền lực của sự theo dõi và kiểm soát ngầm
- Frankl — tìm kiếm ý nghĩa nội tại ngay giữa những trói buộc

**Ending & Organic CTA (Đoạn cuối & Kêu gọi hành động gắn liền nội dung):**
CẤM TUYỆT ĐỐI CTA máy móc kiểu YouTuber ("hãy like, share và đăng ký...") hoặc câu châm ngôn sáo rỗng lặp đi lặp lại ("sống nhẹ thôi giữa hiện tại..."). Đoạn cuối phải kết hợp chiêm nghiệm sâu sắc + lời kêu gọi tương tác/hành động gắn liền với chủ đề:

- **Archetype 1: Gợi mở đàm đạo (Reflective Inquiry):**
  Đặt câu hỏi xoáy vào trăn trở cốt lõi, mời khán giả bình luận góc nhìn cá nhân.
  *Ví dụ:* "Đã bao giờ bạn nhận ra một thông tin mình tin tưởng suốt nhiều năm hóa ra chỉ là một nửa sự thật? Hãy để lại góc nhìn của bạn bên dưới, và đăng ký kênh để cùng tôi chậm lại trước những cơn bão thông tin."
- **Archetype 2: Thách thức hành động nhỏ (Micro-Action Challenge):**
  Kêu gọi làm một việc thực tế ngoài đời để thoát khỏi chiếc bẫy công nghệ vừa phân tích.
  *Ví dụ:* "Hôm nay, bạn có dám thử tắt định vị và tự tìm đường về nhà bằng mắt và trí nhớ của mình không? Hãy chia sẻ trải nghiệm ấy ở bình luận, và theo dõi kênh để cùng tôi làm chủ lại sự chú ý."
- **Archetype 3: Lựa chọn ngã rẽ (The Dichotomy Choice):**
  Đưa ra hai thái độ sống để người xem tự chọn và bình luận.
  *Ví dụ:* "Giữa mười lăm giây hào nhoáng trên mạng và một cuộc đời bình dị nhưng có chiều sâu, bạn chọn điều gì? Bình luận câu trả lời của bạn, và bấm theo dõi để lắng nghe thêm những chiêm nghiệm đời thường."
- **Archetype 4: Giữ gìn giá trị thực tế (Preservation of the Real):**
  Kêu gọi quay về với xúc chạm thật, con người thật, ký ức thật.
  *Ví dụ:* "Đừng để những bức ảnh quý giá nhất của đời bạn mãi nằm sau một gói thuê bao dữ liệu. Hôm nay hãy in một tấm ảnh ra giấy và cất vào ví nhé. Và nếu thấy đồng cảm, hãy theo dõi kênh để cùng gìn giữ những điều chân thật."

### Stage 3 — Write Script `.md`

Use the template at `templates/script_template.md`. Each scene block:

```markdown
Đoạn N: Xs–Ys (Scene Title)
• Hình ảnh: [visual description, noir B&W — mention "mưa" if rain overlay needed]
  [Pexels keywords: ...]
• Âm thanh: [audio description, piano/ambient]
• Lời thoại: (acting note) "Dialogue text..."
```

Rules:
- Dialogue in `"quotes"` — `make_karaoke_subs.py` extracts from these
- Acting notes inside `(parentheses)` — stripped by subtitle parser
- Pexels keywords on a line starting with `[Pexels keywords:`
- Scene 1: unified opening hook
- Final scene: `END_TITLE: "ZENPHAM — [Topic Tag]"` — this feeds the endcard graphic
- 8–10s per scene → total 80–200s
- Voice: `Giọng: Zen (zen-style) — OmniVoice`
- Style: `Phong cách: Cinematic Noir`
- Every scene states `Cảm xúc:` and `Tốc độ đọc:`. Pace guide: grief/confession 0.84–0.90; reflection 0.91–0.96; observation 0.97–1.00; tension/climax 1.01–1.05; release 0.90–0.94. Keep dialogue ≤9.8s after TTS.

### Stage 4 — Pipeline Execution
 
```bash
cd assets/scripts_video
# 1. Quét đối soát kịch bản visual, khớp >=90% thì nạp trực tiếp Pexels footage
python3 pexels_visual_matcher.py --enhance-script script.md --orientation portrait --download

# 2. Tải/chuẩn bị các footage còn lại và hậu kỳ noir
python3 fetch_stock.py --md script.md        # download Pexels clips fallback
python3 post_stock.py --md script.md         # noir-style clips
python3 tts_zen.py --md script.md            # Zen voice (zen-style.wav) WAVs
python3 assemble_podcast.py --md script.md --channel ZENPHAM --music <track.mp3>  # final mp4 with endcard
```

## Pitfalls

1. **Pexels interlacing**: downloaded clips are often 1080i → `assemble.py`
   and `assemble_podcast.py` apply `yadif=1` for deinterlace.
3. **Voice timing**: Zen TTS sometimes runs slow (>60s per scene).
   `tts_zen.py` has 3 retries + 180s timeout.
3. **Scene duration**: Pexels clips < 10s filtered out by `fetch_stock.py`.
   If a scene has no valid clip, re‑search with broader keywords.
4. **Philosophy overload**: max 2–3 philosophical references per **entire script**.
   One per scene is too many. Each philosopher needs room to breathe.
5. **Data freshness**: always `web_search` before writing. Statistics from
   2023 read as stale in a 2026 video.
6. **Depth over breadth**: a single well-told idea beats five scattered references.
   If the script feels crowded, cut the weakest philosopher and double the
   personal story.
7. **Cache collisions**: when switching scripts, `--force` flag on fetch_stock,
   tts, or delete `raw_*.mp4` / `scene_*.wav` to avoid stale artifacts.

## Verification

1. `python3 scripts/zenpham_script.py <script.md>` passes; it checks topic novelty and philosopher cap.
2. Script md has 8–20 `Đoạn N:` blocks, each with `Lời thoại:`
3. Each `Lời thoại:` contains `"quoted dialogue"`
3. `make_karaoke_subs.py` parses the script without errors
4. `assemble_podcast.py` produces a playable mp4 > 10MB
5. Final video: 1080×1920, B&W, karaoke subtitles, piano bed, Zen voice (zen-style),
   TikTok-style endcard with ZENPHAM + title