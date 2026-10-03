# Phương Pháp Đọc Tiếng Anh Tự Nhiên — Vietnamese Grammatical Anchoring (Golden Method v4)

> **QUY TẮC BẤT BIẾN (INVARIANT):**
> Mọi kịch bản TTS song ngữ Việt-Anh trên các kênh ZENPHAM, TÔI LÀM VIỆC, REALITY DECODE
> và bất kỳ nội dung kỹ thuật nào qua OmniVoice **BẮT BUỘC** tuân thủ toàn bộ phương pháp
> Vietnamese Grammatical Anchoring bên dưới. Vi phạm bất kỳ quy tắc nào sẽ bị chặn xuất bản
> (synthesis-blocked) bởi `tts_code_switch_risk.py`.
>
> **Skill tham chiếu chi tiết:** `.agents/skills/omnivoice-reader/SKILL.md`

---

## 1. Quy Tắc Neo Ngữ Pháp Tiếng Việt (Grammatical Anchor Invariant)

Khi mô hình TTS tiếng Việt nhìn thấy một từ tiếng Anh trơ trọi (bare English term), nó bị
lúng túng về trọng âm và ngữ điệu → phát âm sai hoặc nuốt âm.

**Quy tắc bắt buộc:** Đặt một từ định danh loại ngữ pháp tiếng Việt ngay trước thuật ngữ
tiếng Anh để "neo" ngữ cảnh cho OmniVoice:

| Loại từ neo | Ví dụ chuẩn |
|---|---|
| `hàm` | hàm Softmax, hàm loss, hàm Sigmoid, hàm ReLU |
| `thuật toán` | thuật toán Backpropagation, thuật toán Gradient Descent |
| `phương pháp` | phương pháp PCA, phương pháp Monte Carlo |
| `phân phối` | phân phối Gaussian, phân phối Bernoulli, phân phối Beta |
| `độ` / `chỉ số` / `giá trị` | độ calibration, chỉ số MSE, chỉ số MAE, giá trị loss |
| `mô hình` / `kiến trúc` | mô hình Transformer, mô hình LLM, kiến trúc Autoencoder |
| `không gian` / `cơ chế` / `tầng` | không gian latent space, cơ chế self-attention, tầng LayerNorm |
| `ma trận` / `phép` | ma trận Hessian, ma trận covariance, phép phân tích SVD |
| `quá trình` / `bước` | quá trình training, bước forward pass |

---

## 2. CẤM Bare English Term Ở Đầu Câu (Zero Bare Start)

Tuyệt đối không để từ tiếng Anh đứng đầu câu hoặc mệnh đề:

- ❌ *Sai:* "Backpropagation là trái tim của mạng nơ-ron."
- ✅ *Đúng:* "Thuật toán Backpropagation là trái tim của mạng nơ-ron."
- ❌ *Sai:* "Softmax biến đổi logits thành xác suất."
- ✅ *Đúng:* "Hàm Softmax biến đổi các giá trị logits thành xác suất."
- ❌ *Sai:* "Loss function đo lường sai số."
- ✅ *Đúng:* "Hàm loss function đo lường sai số."
- ❌ *Sai:* "Training bắt đầu với learning rate nhỏ."
- ✅ *Đúng:* "Quá trình training bắt đầu với tốc độ learning rate nhỏ."

---

## 3. CẤM Phiên Âm Việt Thô Thiển (Zero Fake Transliteration)

Tuyệt đối CẤM viết phiên âm chắp vá:

- ❌ "Gờ-ra-đi-ân", "Rơ-lu", "Tran-sơ-pho-mơ", "Bi-nôm-mi-ơn", "Xốp-mắc", "La-ma", "Béc-nu-li"
- ✅ Giữ nguyên chính tả tiếng Anh chuẩn quốc tế: Gradient, ReLU, Transformer, Binomial, Softmax, LLaMA, Bernoulli

Thuật ngữ toán học và kỹ thuật máy tính **bắt buộc giữ nguyên chính tả tiếng Anh**. OmniVoice với Vietnamese Grammatical Anchor sẽ phát âm đúng khi có neo ngữ pháp.

---

## 3.5 Chuẩn Hóa Ký Hiệu Toán Học Cho TTS (Math Notation TTS-Safe) 🔒

> **INVARIANT (Rút ra từ 146 lỗi thực tế trong 10 tập T10–T20):**
> Mọi ký hiệu toán dạng subscript (`_`) hoặc superscript (`^`) trong `TTS_INPUT_*.md`
> sẽ gây dính âm, đọc literal, hoặc garbled khi TTS synthesize.
> Script kiểm toán: `assets/scripts_video/series_01/fix_tts_math_notation.py`

**QUY TẮC:** Tách rời từng chữ cái bằng khoảng trắng, viết công thức thành prose mô tả:

| CẤM (trong TTS script) | BẮT BUỘC viết | Lý do |
|---|---|---|
| `W_Q`, `W_K`, `W_V`, `W_O` | `W Q`, `W K`, `W V`, `W O` | Underscore → dính âm |
| `d_k`, `d_v`, `d_model` | `d k`, `d v`, `d model` | Subscript → garbled |
| `p_i`, `z_j`, `x_t`, `A_ij` | `p i`, `z j`, `x t`, `A i j` | Index → merged |
| `delta_ij`, `sigma_i`, `theta_i` | `delta i j`, `sigma i`, `theta i` | Greek+subscript |
| `A^T`, `K^T` | `A chuyển vị`, `K chuyển vị` | Caret → stutter |
| `N²`, `O(N²)` | `N bình phương`, `bậc N bình phương` | Unicode math |
| `1/√d_k` | `một chia căn bậc hai của d k` | Fraction + root |

**KHÔNG fix** (đã xử lý tốt): `Softmax`, `LayerNorm`, `RNN`, `LSTM`, `one-hot`, `dot product` — thuật ngữ EN nguyên vẹn, OmniVoice đọc đúng khi có neo ngữ pháp.

---

## 3.6 CẤM Dấu Ngoặc Kép `"string"` và Dấu Gạch Ngang `-` Trong Lời Thoại (Zero Quotes & Zero Bullet Dashes) 🔒

> **QUY TẮC BẤT BIẾN (USER INVARIANT):**
> Trong kịch bản đọc lời thoại (`TTS_INPUT_*.md`), tuyệt đối CẤM sinh ra các dấu ngoặc kép `"string"` hoặc dấu gạch ngang đầu dòng `- ` hay gạch nối giữa câu ` - `. Chúng gây nhiễu, làm mô hình TTS đọc thành "quote / mở ngoặc", "dấu trừ / gạch ngang", hoặc gây khựng/ngắt giật ngữ điệu (stutter).

1. **CẤM dấu ngoặc kép:** Không bao bọc thuật ngữ hay chuỗi trong `"..."` hoặc `'...'`. Viết thẳng văn bản xuôi tự nhiên:
   - ❌ *Sai:* `thuật ngữ "hàm mất mát"`, `khái niệm "Adam"`, `chế độ "eval"`, `nhãn "1"`
   - ✅ *Đúng:* `thuật ngữ hàm mất mát`, `khái niệm Adam`, `chế độ eval`, `nhãn 1`

2. **CẤM dấu gạch ngang đầu dòng hoặc gạch nối giữa câu:**
   - ❌ *Sai:* `- Mô hình không có lương tri` (dấu gạch đầu dòng làm TTS phát âm "trừ" hoặc ngắt giọng thô bạo)
   - ❌ *Sai:* `bề mặt tối ưu - nơi gradient dẫn đường` (dấu gạch ngang giữa câu gây giật nhịp)
   - ✅ *Đúng:* `Mô hình không có lương tri`
   - ✅ *Đúng:* `bề mặt tối ưu, nơi gradient dẫn đường` (dùng dấu phẩy `,` hoặc liên từ tự nhiên)

---

## 3.7 Quy Tắc Giãn Cách Thuật Ngữ & Chống Lặp Từ Cho TTS (Term Cooldown & Anti-Repetition Invariant) 🔒

> **QUY TẮC BẤT BIẾN (INVARIANT):**
> Khi mô hình TTS phát âm thuật ngữ tiếng Anh trong ngữ cảnh tiếng Việt, việc lặp lại cùng một thuật ngữ trong khoảng cách ngắn gây ra:
> 1. Hiện tượng nhại âm hoặc lúng túng trọng âm giữa 2 lần đọc.
> 2. Cảm giác giật cục, vấp váp cho người nghe và giảm chất lượng chuyên nghiệp của kênh.

1. **Quy tắc Cooldown trong câu (Zero Within-Sentence Repeat):**
   - Tuyệt đối **CẤM** một thuật ngữ tiếng Anh chuyên sâu xuất hiện $\ge 2$ lần trong cùng một câu hoặc cùng một mệnh đề.
   - ❌ *Sai:* "Khi thuật toán Levenberg-Marquardt cập nhật ma trận, Levenberg-Marquardt sẽ giảm hệ số suy giảm."
   - ✅ *Đúng:* "Khi thuật toán Levenberg-Marquardt cập nhật ma trận, giải thuật này sẽ giảm hệ số suy giảm."

2. **Quy tắc Cooldown trong phân cảnh (Max 2 per Scene):**
   - Trong mỗi phân cảnh (60–90 giây), một thuật ngữ tiếng Anh chỉ được xuất hiện **tối đa 2 lần**.
   - Từ lần thứ 2 trở đi, **BẮT BUỘC** thay thế bằng đại từ hoặc danh từ tiếng Việt tự nhiên:
     - `thuật toán A*` $\to$ `giải thuật này` / `thuật toán trên` / `cơ chế tìm kiếm đường đi`
     - `hàm Softmax` $\to$ `hàm số này` / `phép chuẩn hóa xác suất`
     - `mô hình Transformer` $\to$ `kiến trúc này` / `mạng nơ-ron này`
     - `bộ lọc Kalman Filter` $\to$ `bộ lọc này` / `bộ ước lượng trạng thái`
     - `độ trễ P99` $\to$ `chỉ số trễ phân vị` / `chỉ số này`

3. **CẤM kẹp song song kiểu phiên âm thừa thãi:**
   - ❌ *Sai:* `thuật toán Splay Tree (x-plây tri)` hoặc `bộ lọc Kalman, tức là bộ lọc Kalman`
   - ✅ *Đúng:* `thuật toán Splay Tree`, `bộ lọc Kalman`

---

## 3.8 Đa Dạng Hóa Cầu Nối Ngữ Nghĩa & Chống Rập Khuôn (Bridge Phrase Diversity Invariant) 🔒

> **QUY TẮC BẤT BIẾN (ANTI-CRUTCH INVARIANT):**
> Tuyệt đối CẤM lạm dụng một từ nối duy nhất để "đỡ" các thuật ngữ tiếng Anh.

1. **Giới hạn tần suất từ nối:**
   - Các cụm từ nối giải thích: `tức là`, `nói cách khác`, `có thể hiểu là`, `bản chất là` **CHỈ ĐƯỢC XUẤT HIỆN TỐI ĐA 1 LẦN MỖI TỪ TRONG MỘT PHÂN CẢNH**.
   - CẤM phân cảnh nào cũng lặp lại 3–4 lần `tức là` hoặc `nói cách khác`.
2. **Ưu tiên bắc cầu bằng thị giác Manim:**
   - Thay vì dùng lời nói để giải thích định nghĩa hàn lâm, để hoạt họa Manim 2K biểu diễn trực tiếp cơ chế hình học, lời thoại chỉ cần dẫn dắt mắt nhìn tự nhiên.

---

## 4. Gate Bắt Buộc Trước Synthesis (Pre-TTS Gate)

Trước mỗi lần synthesize audio, pipeline PHẢI chạy tuần tự:

### Bước 1: Quét rủi ro code-switching
```bash
python3 assets/scripts_video/tts_code_switch_risk.py <cue_sheet.json>
```
- Nếu phát hiện cảnh báo `high` → **CHẶN synthesis** cho đến khi thêm neo ngữ pháp.
- Nếu phát hiện cảnh báo `medium` → cần A/B test trước khi synthesis cả tập.

### Bước 2: Kiểm tra từ điển phát âm
- Tra cứu `omnivoice_pronunciation_lexicon.json` cho spoken form đã duyệt.
- Chỉ entry `status: "approved"` hoặc đã qua `human_listening: approved` mới được dùng.
- Từ mới chưa có trong registry → phải A/B test riêng trước.

### Bước 3: A/B Test cho term rủi ro
- Với mỗi HIGH risk: tạo clip 8–15 giây cùng voice, cùng speed, cùng câu xung quanh.
- Không tự chèn IPA, phoneme hoặc transliteration.
- Lưu verdict người nghe trong `tts_term_registry_v4.json`.

---

## 5. Gate Sau Synthesis (Post-TTS QA)

### Bước 1: Kiểm toán sóng âm
```bash
python3 assets/scripts_video/audio_join_quality.py <scene.wav>
```
Tiêu chí:
- `clipped_samples_percent`: 0.00%
- `peak_dbfs`: ≤ -0.5 dBFS
- `longest_silence_ms`: ≤ 450 ms
- `click_ratio_to_p99_delta`: ≤ 2.5

### Bước 2: Giới hạn khoảng lặng nội bộ
```bash
python3 assets/scripts_video/cap_internal_silence.py <input.wav> <output.wav> --max-silence 0.35
```

### Bước 3: Đồng bộ timestamp Faster-Whisper
```bash
python3 assets/scripts_video/whisper_aligner.py <scene.wav>
```
- Trích xuất mốc thời gian từng từ (word.start, word.end).
- Căn khớp với kịch bản gốc qua SequenceMatcher.

---

## 6. Kỹ Thuật Ghép Âm Song Ngữ Không Giật (Zero-Jolt Splicing)

Khi cần phát âm tiếng Anh bản ngữ (thuật ngữ phức tạp, cụm dài):

1. **Contextual Carrier Sentence**: Bổ sung `... Term ...` khi sinh âm Anh riêng.
2. **Noun-Phrase Semantic Chunking**: Tách theo cụm danh từ trọn nghĩa, không xé vụn âm tiết.
3. **Phonetic Boundary Stop-Gap**: Chèn 35–45ms lặng tại ranh giới chuyển ngữ.
4. **Equal-Power Cosine Crossfade**: Nối sóng bằng hàm cosine 25ms (w_out² + w_in² = 1.0).
5. **EBU R128 Normalization**: Chuẩn hóa -16.0 LUFS + room-tone -52.0 dBFS.

---

## 7. Pha Nhịp Hoạt Họa Manim (VoiceSyncTimeline)

CẤM animation đứng hình thụ động (`self.wait(50)`). Bắt buộc phân bổ nhịp theo trọng số âm thanh:

```python
from assets.scripts_video.manim_production import VoiceSyncTimeline

timeline = VoiceSyncTimeline(["audio/series_01/tap_XX_v6/scene_01.wav"])
timings = timeline.allocate(scene_index=0, n_animations=4, weights=[1.0, 2.5, 3.0, 1.5])

self.play(FadeIn(hero), run_time=timings[0])
self.play(Transform(curve_a, curve_b), run_time=timings[1])
self.play(Create(cloud), run_time=timings[2])
self.play(Indicate(eureka_box), run_time=timings[3])
```

---

## 8. Ba Trạng Thái Phê Duyệt Bắt Buộc (Golden Approval Gate)

Không xuất bản tập phim nếu thiếu bất kỳ trạng thái nào:

| Gate | Ai kiểm tra | Xác nhận |
|---|---|---|
| `audio-approved` | Người nghe | Không có từ Anh bị vấp, phát âm đúng, không giật rè, ngắt nghỉ đúng nhịp |
| `visual-approved` | Người xem | Đồ thị chính xác, căn giữa chuẩn, chuyển động liên tục |
| `golden-approved` | Người thẩm định | Lệch âm-hình < 16.7ms, phụ đề sáng đúng nhịp, -14 LUFS |

---

## Tóm Tắt Pipeline Đầy Đủ

```
Soạn vocal script
  ↓
Áp dụng Vietnamese Grammatical Anchoring (neo ngữ pháp)
  ↓
Chạy tts_code_switch_risk.py → BLOCK nếu HIGH
  ↓
A/B test term rủi ro → Lưu tts_term_registry_v4.json
  ↓
Synthesize audio (TTS V0-Sense tts_v0_sense_synthesizer.py, 1.0x native, 48kHz)
  ↓
cap_internal_silence.py (≤ 350ms)
  ↓
audio_join_quality.py → BLOCK nếu fail
  ↓
whisper_aligner.py (timestamp từng từ)
  ↓
VoiceSyncTimeline → Manim animation timing
  ↓
audio-approved → visual-approved → golden-approved
  ↓
XUẤT BẢN
```
