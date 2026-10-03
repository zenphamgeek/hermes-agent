# Quy Chuẩn Bắt Buộc Về Giọng Đọc: ZENPHAM & TÔI ĐỌC SÁCH

> **QUY TẮC BẤT BIẾN (INVARIANT):**
> Tất cả các tác vụ sinh âm thanh (TTS), dựng video và vận hành nội dung cho hai kênh **ZENPHAM** và **TÔI ĐỌC SÁCH** bắt buộc **100% LUÔN LUÔN** sử dụng bộ giọng mẫu độc quyền tại thư mục:
> `/home/zen/hermes-agent/assets/voices/Zen Mien Tay/`
> Tuyệt đối không sử dụng bất kỳ giọng nào ngoài thư mục này (không dùng giọng Bắc, giọng nữ, giọng mặc định của mô hình hay tệp âm thanh trôi nổi).

---

## 1. Danh Mục Giọng Chuẩn Trong `Zen Mien Tay`

Thư mục `/home/zen/hermes-agent/assets/voices/Zen Mien Tay/` bao gồm 6 phiên bản giọng mẫu (được tinh chỉnh trực tiếp từ bản thu mic chất lượng cao của Zen, triệt tiêu 63.4% jitter, khử noise floor và diffusion hiss):

| Tệp Âm Thanh (.wav) | Tệp Tham Chiếu (.txt) | Tốc độ | Đặc trưng âm sắc & Phong cách |
|---|---|:---:|---|
| `zenpham-standard-mientay.wav` | `zenpham-standard-mientay.txt` | 120% (Chuẩn) | Đĩnh đạc, rõ ràng, dứt khoát, âm sắc Nam Bộ trung niên trí thức. |
| `zenpham-zen-meditation-mientay.wav` | `zenpham-zen-meditation-mientay.txt` | 114% | Trầm ấm (F0 ~114-121Hz), thong dong, nhịp thở sâu, tĩnh lặng. |
| `zenpham-warm-radio-mientay.wav` | `zenpham-warm-radio-mientay.txt` | 118% | Ấm áp, gần gũi, chia sẻ tâm sự như người dẫn radio đêm muộn. |
| `zenpham-intimate-mientay.wav` | `zenpham-intimate-mientay.txt` | 115% | Thủ thỉ, tâm tình, chữa lành, đồng cảm với những bối rối đời thường. |
| `zenpham-authoritative-mientay.wav` | `zenpham-authoritative-mientay.txt` | 122% | Chắc chắn, uy lực, sắc bén khi phân tích luận đề triết học/quản trị. |
| `zenpham-storyteller-mientay.wav` | `zenpham-storyteller-mientay.txt` | 120% | Biểu cảm dẫn chuyện sinh động, đưa người nghe vào mạch tích xưa. |

---

## 2. Quy Chuẩn Phân Bổ Theo Kênh

### A. Kênh ZENPHAM (Shorts, Triết Học Đời Thường, Podcast Mini)
- **Định dạng:** 9:16 Vertical Shorts (hoặc 16:9 Podcast mini ngắn).
- **Giọng chính:** `zenpham-standard-mientay.wav` (Tốc độ chuẩn 120%).
- **Giọng bổ trợ:** 
  - `zenpham-warm-radio-mientay.wav` (cho các chủ đề thói quen sống, gia đình, công sở).
  - `zenpham-authoritative-mientay.wav` (cho các chủ đề quản lý vs quản trị, công nghệ, AI, nghịch lý tư duy).
  - `zenpham-storyteller-mientay.wav` (cho các câu chuyện ngụ ngôn, nhân vật).
- **Nhạc nền:** Lo-fi Noir, Ambient chậm nhẹ.

### B. Kênh TÔI ĐỌC SÁCH (Long-form Video Essay 16:9 > 10 phút)
- **Định dạng:** **100% Landscape 16:9 Widescreen (1920x1080)**.
- **Giọng chính:** **`zenpham-zen-meditation-mientay.wav`** (Bắt buộc cho Hồi 1, Hồi 2 và Hồi 5 kết đọng).
- **Giọng bổ trợ:** **`zenpham-intimate-mientay.wav`** (cho Hồi 3 va chạm đời thực và chia sẻ vấp ngã cá nhân).
- **Nhịp độ:** Chế độ `--voice-driven` (kéo giãn visual theo giọng đọc, giữ khoảng thở 1.6s ở mỗi đoạn chuyển).
- **Nhạc nền:** `Quiet Room Glow` (Neo-classical piano và cello ấm áp).

---

## 3. Quy Chuẩn Tiền Xử Lý Văn Bản (Text Normalization)

Trước khi gửi bất kỳ văn bản nào sang OmniVoice TTS:
1. **Lọc sạch dấu ngoặc kép:** Bắt buộc loại bỏ toàn bộ `""`, `“”`, `«»` quanh từ ngữ tiếng Việt để ngăn tokenizer nuốt phụ âm đầu (ví dụ biến `"đúng"` thành `"dúng"`).
2. **Chuẩn hóa danh từ riêng ngoại ngữ:**
   - *Epictetus* $\rightarrow$ `Ê-pích-tê-tớt`
   - *Albert Camus* $\rightarrow$ `An-be Ca-muy`
   - *Stoicism* $\rightarrow$ `Chủ nghĩa Khắc kỷ`
   - *Existentialism* $\rightarrow$ `Chủ nghĩa hiện sinh`
3. **Chuẩn hóa số & thời gian theo chuẩn phương Nam:**
   - `2300 năm trước` $\rightarrow$ `hai ngàn ba trăm năm trước` (dùng "ngàn", không dùng "nghìn")
   - `thế kỷ IV` $\rightarrow$ `thế kỷ bốn`
   - `15/8/1945` $\rightarrow$ `ngày mười lăm tháng tám năm một ngàn chín trăm bốn mươi lăm`
4. **Sử dụng Engine:** Mọi pipeline phải import và gọi `transform_for_tts()` từ `vietnamese_prosody.py` (tích hợp `vn_text_preprocessor.py` và `vietnamese_expressive_prosody.py`).

---

## 4. Tiêu Chuẩn Gold TTS Duy Nhất: TTS V0 (Direct Raw Script Synthesis)

> **BẮT BUỘC 100% CHO MỌI KÊNH & MỌI VIDEO:**
> Kể từ phiên bản hiện tại, mọi tác vụ sinh giọng đọc TTS cho **ZENPHAM**, **TÔI ĐỌC SÁCH**, **BIẾT ĐỊA LÝ TỪ BA TÔI**, **REALITY DECODE** và toàn bộ Shorts/Longform đều phải tuân thủ chuẩn **TTS V0 (Direct Raw Script Synthesis)**:
> 1. **Động cơ mặc định (Default Engine):** **Local VieNeu-TTS v3 Turbo** chạy trực tiếp trên GPU NVIDIA Quadro RTX 5000 16GB (CUDA). Môi trường thực thi: `/home/zen/hermes-agent/vieneu_tts_test/.venv/bin/python`.
> 2. **Đọc thẳng 100% từ kịch bản (Zero Text Preprocessing):** Bỏ hoàn toàn TTS V8, không sử dụng `prosody_dictionary.json`, không gán 24 Wave ngữ điệu, không băm câu hay chèn dấu câu giả lập. VieNeu-TTS v3 Turbo đọc liền mạch tự nhiên từ chính văn bản tác giả.
> 3. **Giọng mẫu nhận diện thương hiệu (Voice Reference):**
>    - ZENPHAM & BIẾT ĐỊA LÝ: `assets/voices/Zen Mien Tay/zenpham-zen-meditation-mientay.wav`.
> 4. **Chuỗi Master Phòng Thu 5 Giai Đoạn (Studio Vocal Mastering Chain):** Mọi audio VieNeu raw bắt buộc phải lọc qua chuỗi FFmpeg: `highpass=f=80, equalizer=f=300:t=q:w=1.5:g=-2.0, equalizer=f=3800:t=q:w=1.2:g=3.0, treble=g=3.5:f=9000:t=s, loudnorm=I=-14.5:TP=-1.5:LRA=7.0` (-ar 48000 -ac 2) để đạt chuẩn phát thanh quốc tế EBU R128 trong trẻo, sang trọng.
> 5. **Mã nguồn thực thi chuẩn:** `assets/scripts_video/tts_v0_synthesizer.py`.
> 6. **Tham chiếu quy chuẩn:** `.agents/rules/vietnamese_gold_tts_rules.md`.


