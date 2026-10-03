---
name: omnivoice-reader
description: "Chuyên môn kỹ thuật và quy trình chuẩn sản xuất giọng đọc ZenPham (Zen Miền Tây, TTS V0-Sense 1.0x native) qua OmniVoice: Chuẩn hóa code-switching Việt-Anh (Golden Method v4), chuẩn hóa ký hiệu toán học TTS-safe, quét rủi ro neo ngữ pháp (tts_code_switch_risk), kiểm tra A/B từ điển phát âm (tts_term_registry), nối âm mượt mà chống giật cục (Zero-Jolt Splicing), premium studio mastering, đồng bộ timestamp từng từ qua Faster-Whisper (whisper_aligner), pha nhịp chuyển động Manim (VoiceSyncTimeline), và voice benchmark tiêu chuẩn phòng thu."
version: 2.0.0
author: ZENPHAM, Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [omnivoice, zen-voice, tts, code-switching, whisper-sync, voice-timeline, audio-engineering, golden-gate, math-notation, studio-mastering, voice-benchmark]
    related_skills: [toi-lam-viec, manim-production, youtube-publisher]
---

# OmniVoice Reader — Kỹ Nghệ Giọng Đọc Kỹ Thuật ZenPham (Golden Voice Method v2)

Quy trình sản xuất âm thanh, kiểm soát ngữ âm song ngữ Việt - Anh, chuẩn hóa ký hiệu toán học cho TTS, premium studio mastering, và đồng bộ hóa thời gian tuyệt đối (Time-Sync) cho series **"TÔI LÀM VIỆC"**, **"REALITY DECODE"** và các nội dung chuyên sâu trên kênh **ZENPHAM**.

---

## 1. Bản Sắc & Định Luật Đơn Giọng Bất Biến (Monolingual Voice Invariant)

1. **Giọng Đọc Độc Quyền Duy Nhất**:
   - Thư mục: `assets/voices/Zen Mien Tay/`
   - 6 phiên bản giọng (standard, zen-meditation, warm-radio, intimate, authoritative, storyteller)
   - Giọng mặc định cho kỹ thuật: `zenpham-zen-meditation-mientay` (Baritone F0 ~114-121Hz)
   - Câu chuẩn benchmark: *"Đôi khi, điều khó nhất không phải là tìm câu trả lời đúng, mà là chấp nhận rằng mình đã sai. Nhưng chính những lần vấp ngã ấy, lại dạy ta nhiều hơn bất kỳ thành công nào."*

2. **Tham Số Kỹ Thuật Bắt Buộc (OmniVoice F5-TTS)**:
   - **Tốc độ (Speed)**: Cố định `1.0x` native (mọi scene, bất biến; cấm `atempo < 1.0` theo AGENTS.md §1.4).
   - **Độ phân giải lấy mẫu (Sample Rate)**: 24,000 Hz, 16-bit Mono PCM WAV.
   - **Siêu tham số suy luận**:
     - `num_step`: 48 (độ mịn sóng âm tối đa)
     - `guidance_scale`: 2.2
     - `position_temperature`: 1.0
     - `layer_penalty_factor`: 3.0
     - `no_cache`: True

3. **CẤM TUYỆT ĐỐI Phiên Âm Việt Thô Thiển (Zero Fake Transliteration)**:
   - Tuyệt đối CẤM viết phiên âm chắp vá: *"Gờ-ra-đi-ân"*, *"Rơ-lu"*, *"Tran-sơ-pho-mơ"*, *"Xốp-mắc"*.
   - Thuật ngữ kỹ thuật bắt buộc giữ nguyên chính tả tiếng Anh chuẩn quốc tế.

---

## 2. Kỹ Thuật Neo Ngữ Pháp Tiếng Việt (Vietnamese Grammatical Anchoring)

Khi mô hình TTS tiếng Việt nhìn thấy một từ tiếng Anh trơ trọi (bare English term), nó bị lúng túng về trọng âm và ngữ điệu. Để OmniVoice đọc chuẩn xác:

1. **Quy Tắc Neo Ngữ Pháp (Grammatical Anchor Invariant)**:
   - Bắt buộc đặt một từ định danh loại ngữ pháp tiếng Việt ngay trước thuật ngữ tiếng Anh:
     - `hàm Softmax`, `thuật toán Backpropagation`, `phương pháp PCA`
     - `phân phối Gaussian`, `mô hình Transformer`, `ma trận Hessian`
     - `cơ chế self-attention`, `tầng LayerNorm`, `phép phân tích SVD`

2. **CẤM Bare English Term Ở Đầu Câu**:
   - ❌ "Softmax biến đổi logits thành xác suất."
   - ✅ "Hàm Softmax biến đổi các giá trị logits thành xác suất."

3. **Công Cụ Quét Rủi Ro Code-Switching**:
   ```bash
   python3 assets/scripts_video/tts_code_switch_risk.py <cue_sheet.json>
   ```
   - Cảnh báo `high` → chặn synthesis đến khi bổ sung neo ngữ pháp.

---

## 3. Chuẩn Hóa Ký Hiệu Toán Học Cho TTS (Math Notation TTS-Safe) 🆕

> **BÀI HỌC THỰC CHIẾN:** 146 ký hiệu toán subscript đã gây lỗi đọc dính âm trong 10 tập
> (T10–T20, đặc biệt T11 Attention QKV và T14 Softmax Temperature). Quy tắc này bắt buộc
> cho MỌI kịch bản TTS sinh ra từ đây trở đi.

### 3.1 Quy Tắc Bất Biến: Zero Subscript/Superscript Trong TTS Script

Ký hiệu toán với underscore (`_`) hoặc caret (`^`) sẽ khiến TTS engine:
- Đọc literal "W underscore Q" hoặc nuốt âm thành "wờ kiu"
- Merge subscript thành âm vô nghĩa
- Stutter/dính âm trên ký tự index

**QUY TẮC: Mọi ký hiệu toán trong `TTS_INPUT_*.md` PHẢI được viết dạng tách rời từng chữ cái, có khoảng trắng.**

### 3.2 Bảng Chuyển Đổi Bắt Buộc Chuẩn V7 (Academic Mathematical Prosody)

| Dạng gốc (CẤM trong TTS) | Dạng cũ (VẪN GÂY LỖI) | Dạng V7 Chuẩn Hóa (BẮT BUỘC) | Ghi chú ngữ âm học thuật |
|---|---|---|---|
| `W_Q`, `W_K`, `W_V`, `W_O` | `W Q`, `W K`, `W V`, `W O` | `W Qui`, `W Ca`, `W Vê`, `W Ô` | Triệt tiêu /wờ kiu/, /nhân vơ/, CẤM đọc /cu/, đọc chuẩn âm học thuật Qui |
| `d_k`, `d_v` | `d k`, `d v` | `đê ca`, `đê vê` | Chống đọc /dê/ (con dê), /đờ ca/, /đực/ — Bắt buộc "đê" (/ɗe/) |
| `d_model` | `d model` | `chiều mô hình đê model` | Có neo định danh |
| `p_i`, `p_j` | `p i`, `p j` | `xác suất p i`, `xác suất p j` | Neo định danh xác suất |
| `z_i`, `z_j` | `z i`, `z j` | `z i`, `z j` (phát âm: dét i, dét giây) | Biến tiềm ẩn |
| `x_i`, `x_j`, `x_t` | `x i`, `x j`, `x t` | `x i`, `x j`, `x thời điểm t` | Tránh dính âm /xì/, /xịt/ |
| `h_t`, `h_{t-1}` | `h t`, `h t - 1` | `trạng thái h thời điểm t`, `h thời điểm t trừ một` | Chống đọc /hút/, /hát tờ/ |
| `w_t`, `w_{t+1}` | `w t`, `w t + 1` | `trọng số w thời điểm t`, `w thời điểm t cộng một` | Trọng số cập nhật |
| `u_i`, `v_i`, `s_i` | `u i`, `v i`, `s i` | `u i`, `v i`, `s i` | Thành phần SVD |
| `A_k`, `A_ij`, `H_ij` | `A k`, `A i j`, `H i j` | `A k`, `A i j`, `H i j` | Ma trận indexed |
| `delta_ij` | `delta i j` | `đen-ta i j` | Kronecker delta |
| `sigma_i`, `lambda_i` | `sigma i`, `lambda i` | `xích-ma i`, `lam-đa i` | Trị riêng & độ lệch |
| `theta_i`, `mu_t` | `theta i`, `mu t` | `thê-ta i`, `muy t` | Tham số & trung bình |
| `P_ij`, `P_ji` | `P i j`, `P j i` | `P i j`, `P j i` | Ma trận chuyển trạng thái |
| `A^T`, `K^T`, `Q^T`, `X^T` | `A chuyển vị`, `K chuyển vị` | `ma trận A chuyển vị`, `ma trận K chuyển vị`, `ma trận Qui chuyển vị`, `ma trận X chuyển vị` | Bảo vệ đại lượng ma trận |
| `A * V`, `* V`, `nhân V` | `A nhân V`, `nhân V` | `ma trận A nhân với ma trận Vê`, `nhân với ma trận Vê` | CẤM TUYỆT ĐỐI — Triệt tiêu 100% bẫy "nhân vơ" |
| `Q K^T / √d_k` | `Q nhân K chuyển vị chia căn d k` | `ma trận Qui nhân với Ca chuyển vị, chia cho căn bậc hai của đê ca` | Chuyển ngữ chuẩn mực học thuật |
| `O(N^2)`, `O(N)`, `O(1)` | `O(N^2)`, `O N` | `ô N bình phương`, `ô N`, `ô một` | Độ phức tạp thuật toán |
| `1/N`, `1/2` | `1/N`, `1/2` | `một phần N`, `một phần hai` | Phân số chuẩn tiếng Việt |

### 3.3 Quy Tắc Viết Đại Lượng Chữ & Công Thức Toán Cho TTS (V7 Academic Standard)

1. **Định luật Âm vị học học thuật (Academic Pronunciation Invariant)**:
   - CẤM TUYỆT ĐỐI đọc theo kiểu đánh vần chữ cái tiểu học: `/bờ, cờ, dờ, gờ, hờ, ca/kờ, pê/pờ, quờ, vờ, xờ, rờ, sờ, mờ, nờ, tê/tờ/`.
   - **Bảng phiên âm học thuật chữ cái La-tinh (Chữ thường đại diện cho vô hướng/vector/biến)**:
     - $x \to$ `"ích"` (CẤM `/xờ/`)
     - $y \to$ `"i"` (CẤM `/y-cờ-rét/`)
     - $z \to$ `"dét"` (CẤM `/dờ/`)
     - $w \to$ `"đắp-liu"` (CẤM `/quờ/`, `/vờ/`, `/u/`)
     - $b \to$ `"bê"` (CẤM `/bờ/`)
     - $p \to$ `"pê"` (CẤM `/pờ/`)
     - $q \to$ `"qui"` (CẤM `/quờ/`, CẤM `/cu/`)
     - $k \to$ `"ca"` (CẤM `/kờ/`)
     - $v \to$ `"vê"` (CẤM `/vờ/`)
     - $u \to$ `"u"`
     - $t \to$ `"tê"` (CẤM `/tờ/`)
     - $d, \text{đ} \to$ `"đê"` (CẤM đọc `/dê/` như con dê, CẤM `/dờ/`, `/đờ/`)
     - $h \to$ `"hát"` (CẤM `/hờ/`)
     - $r \to$ `"e-rờ"` (CẤM `/rờ/`)
     - $s \to$ `"ét"` (CẤM `/sờ/`)
     - $m \to$ `"em-mờ"` (CẤM `/mờ/`)
     - $n \to$ `"en-nờ"` (CẤM `/nờ/`)
     - $c \to$ `"xê"` (CẤM `/cờ/`)
     - $l \to$ `"e-lờ"` (CẤM `/lờ/`)
     - $f \to$ `"ép"` (CẤM `/phờ/`)
     - $g \to$ `"giê"` (CẤM `/gờ/`)
   - **Bảng phiên âm học thuật chữ cái in hoa (Đại diện cho Ma trận / Tập hợp / Biến ngẫu nhiên / Hàm)**:
     - $X \to$ `"Ích"`
     - $Y \to$ `"I"`
     - $Z \to$ `"Dét"`
     - $W \to$ `"Đắp-liu"`
     - $L \to$ `"E-lờ"`
     - $H \to$ `"Hát"`
     - $C \to$ `"Xê"`
     - $K \to$ `"Ca"`
     - $Q \to$ `"Qui"` (CẤM `/cu/`, CẤM `/quờ/`)
     - $V \to$ `"Vê"`
     - $A \to$ `"A"`
     - $B \to$ `"Bê"`
     - $D, \text{Đ} \to$ `"Đê"` (CẤM đọc `/Dê/` con dê, CẤM `/đờ/`)
     - $P \to$ `"Pê"`
     - $S \to$ `"Ét"`
     - $M \to$ `"Em-mờ"`
     - $N \to$ `"En-nờ"`
     - $T \to$ `"Tê"`
     - $U \to$ `"U"`

2. **Triệt tiêu bẫy dính âm & tiếng lóng (Phonic Binding Elimination)**:
   - Các từ nối, giới từ, toán tử kết hợp với chữ cái đơn độc thường bị neural TTS gộp thành từ lóng tiếng Việt nguy hại. Bắt buộc chuyển hóa:
     - `* V` hoặc `nhân V` $\to$ `"nhân với ma trận Vê"` (Triệt tiêu 100% bẫy *"nhân vơ"*)
     - `* X` hoặc `nhân X` $\to$ `"nhân với ma trận Ích"` (Triệt tiêu 100% bẫy *"nhân xơ"*)
     - `* Y` hoặc `nhân Y` $\to$ `"nhân với ma trận I"`
     - `* W` hoặc `nhân W` $\to$ `"nhân với ma trận Đắp-liu"`
     - `* C` hoặc `nhân C` $\to$ `"nhân với ma trận Xê"`
     - `* H` hoặc `nhân H` $\to$ `"nhân với ma trận Hát"`
     - `* K` hoặc `nhân K` $\to$ `"nhân với ma trận Ca"`
     - `* Q` hoặc `nhân Q` $\to$ `"nhân với ma trận Qui"` (CẤM đọc `/cu/`)
     - `* x` hoặc `nhân x` $\to$ `"nhân với vector ích"` / `"nhân với ích"`
     - `* y` hoặc `nhân y` $\to$ `"nhân với i"`
     - `* z` hoặc `nhân z` $\to$ `"nhân với dét"`
     - `* w` hoặc `nhân w` $\to$ `"nhân với vector đắp-liu"`
     - `* r` hoặc `nhân r` $\to$ `"nhân với e-rờ"`
     - `* b` hoặc `nhân b` $\to$ `"nhân với bê"`
     - `* p` hoặc `nhân p` $\to$ `"nhân với pê"`
     - `* q` hoặc `nhân q` $\to$ `"nhân với qui"` (CẤM đọc `/cu/`)
     - `* t` hoặc `nhân t` $\to$ `"nhân với tê"`
     - `tại t` $\to$ `"tại thời điểm tê"` (Chống đọc dính âm `/tại tờ/`)
     - `cho x` $\to$ `"cho biến ích"` (Chống đọc `/cho xờ/`)
     - `của z` $\to$ `"của dét"` (Chống đọc `/của dờ/`)
     - `xác suất p` $\to$ `"xác suất pê"` (Chống đọc `/xác suất pờ/`)
     - `phân phối q` $\to$ `"phân phối qui"` (Chống đọc `/cu/`, `/phân phối quờ/`)
     - `p và q` $\to$ `"pê và qui"` (Chống đọc `/pờ và quờ/`)
     - `x và y` $\to$ `"ích và i"` (Chống đọc `/xờ và y/`)
     - `x_t` $\to$ `"đầu vào ích thời điểm tê"`
     - `h_t` $\to$ `"trạng thái hát thời điểm tê"`
     - `w_t` $\to$ `"trọng số đắp-liu thời điểm tê"`

3. **Quy tắc Neo Danh Định (The Grammatical Anchor Rule)**:
   - Đặt từ loại chỉ thực thể toán học trước chữ cái:
     - "ma trận W", "ma trận X", "ma trận Q", "ma trận K", "ma trận V"
     - "vector x", "vector y", "vector q", "vector k", "vector v", "vector bias b"
     - "hàm kích hoạt Sigmoid của z", "hàm ReLU", "hàm tanh"
     - "hệ số an-pha", "hệ số lam-đa", "tốc độ học ê-ta", "độ lệch chuẩn xích-ma"

4. **Công thức toán phức hợp**: Viết thành văn xuôi chuẩn mực, KHÔNG để ký hiệu thô:
   - ❌ `Attention(Q, K, V) = softmax(Q * K^T / sqrt(d_k)) * V`
   - ✅ `"hàm Attention của Q, K, V bằng hàm Softmax của ma trận Q nhân với K chuyển vị chia cho căn bậc hai của dê ca, tất cả nhân với ma trận Vê"`
   - ❌ `y = W * x + b`
   - ✅ `"đầu ra i bằng ma trận Đắp-liu nhân với vector ích, cộng với bias bê"`
   - ❌ `C = 1/N * X^T * X`
   - ✅ `"ma trận hiệp phương sai Xê bằng một phần En-nờ nhân với ma trận Ích chuyển vị nhân Ích"`
   - ❌ `z = (x - mu) / sigma`
   - ✅ `"dét bằng (ích trừ muy) chia cho xích-ma"`
   - ❌ `H(X) = - sum p(x) log p(x)`
   - ✅ `"Entropy Hát của biến ngẫu nhiên Ích bằng trừ tổng pê của ích nhân logarit pê của ích"`
   - ❌ `đạo hàm L theo w`
   - ✅ `"đạo hàm hàm mất mát E-lờ theo trọng số đắp-liu"`
   - ❌ `r = y_hat - y`
   - ✅ `"phần dư sai số e-rờ bằng i mũ trừ i"`

5. **Số mũ, lũy thừa, căn thức, phân số**:
   - ❌ `N²`, `O(N²)`, `sigma^2`, `e^-z`
   - ✅ `"En-nờ bình phương"`, `"ô En-nờ bình phương"`, `"xích-ma bình phương"`, `"e mũ trừ dét"`
   - ❌ `1/√d_k`, `1/N`, `1/2`
   - ✅ `"một chia cho căn bậc hai của dê ca"`, `"một phần En-nờ"`, `"một phần hai"`

6. **Canonical Engine**:
   - Thư viện quy chuẩn: `assets/scripts_video/vietnamese_math_prosody.py` (`normalize_math_prosody`). Mọi pipeline chuẩn hóa kịch bản TTS bắt buộc import và sử dụng hàm này.

### 3.4 Script Kiểm Toán Tự Động

Chạy trước khi synthesis để bắt mọi ký hiệu toán còn sót:
```bash
cd assets/scripts_video/series_01
python3 fix_tts_math_notation.py --dry-run --verbose
```
- `--dry-run`: Chỉ report, không sửa file.
- Không có flag: Tự động fix tất cả.

### 3.5 Phân Biệt: Cái GÌ Cần Fix vs Cái GÌ Giữ Nguyên

| Giữ nguyên (đã xử lý tốt) | Lý do |
|---|---|
| `Softmax`, `LayerNorm`, `FlashAttention` | Thuật ngữ EN nguyên vẹn, OmniVoice + neo ngữ pháp đọc tốt |
| `one-hot`, `dot product` | Cụm EN chuẩn, không có subscript |
| `RNN`, `LSTM`, `GPT`, `BERT` | Viết tắt EN đọc từng chữ cái tự nhiên |
| `backpropagation` | Từ EN dài, OmniVoice phát âm đúng |

| PHẢI fix (gây lỗi TTS) | Lý do |
|---|---|
| `W_Q`, `d_k`, `p_i` | Underscore → dính âm hoặc đọc literal |
| `A^T` | Caret → stutter |
| `delta_ij`, `sigma_i` | Greek + subscript → garbled |

---

## 4. Tiêu Chuẩn V7 — Vietnamese Prosody Script Intelligent & Phonic Binding Cụm Danh Từ Kỹ Thuật 🆕

> **BÀI HỌC CỐT LÕI V7:** Khi đọc văn bản kỹ thuật AI & Khoa học máy tính, giọng đọc TTS rất dễ mắc lỗi ngắt nhịp vô lý giữa chừng các cụm danh từ ghép (compound nouns) như *"năng lực | tính toán"*, *"lan truyền | ngược"*, *"đạo hàm | riêng"*, *"quy tắc | dây chuyền"*, *"hàm | mất mát"*, *"bộ nhớ | đệm"*. 
> Tiêu chuẩn V7 xác lập giải pháp công nghệ và quy chuẩn biên soạn kịch bản triệt tiêu 100% lỗi ngắt nhịp này.

### 4.1 Nguyên Nhân Ngữ Âm & Cú Pháp Học
Trong tiếng Việt kỹ thuật, đa số cụm thuật ngữ là từ ghép chính phụ hoặc ghép đẳng lập có cấu trúc:
- **Danh từ + Động từ:** *"năng lực"* (N) + *"tính toán"* (V), *"quá trình"* (N) + *"huấn luyện"* (V), *"chi phí"* (N) + *"tính toán"* (V).
- **Danh từ + Tính từ:** *"mạng nơ-ron"* (N) + *"sâu"* (Adj), *"đạo hàm"* (N) + *"riêng"* (Adj), *"điểm cực tiểu"* (N) + *"cục bộ"* (Adj).
- **Động từ + Hướng/Trạng từ:** *"lan truyền"* (V) + *"ngược"* (Dir), *"quá"* (Adv) + *"khớp"* (V) $\to$ *"quá khớp"*.

Khi văn bản thiếu các điểm neo cú pháp rõ ràng, tokenizer hoặc bộ dự đoán ngữ điệu (prosody predictor) của TTS thường hiểu nhầm âm tiết cuối là vị ngữ độc lập của câu, tự động hạ cao độ ($F_0$ drop) và chèn khoảng lặng ngắt nhịp (caesura) ở giữa cụm từ.

### 4.2 Bộ Tứ Quy Chuẩn V7 Bắt Buộc (The 4-Pillar V7 Prosody Invariant)

1. **Khóa Nguyên Khối Từ Vựng (Zero-Split Lexical Binding Invariant):**
   - Từ điển `VN_COMPOUND_NOUNS_V7` trong `assets/scripts_video/vietnamese_prosody_v7.py` chứa 150+ cụm danh từ then chốt.
   - **CẤM TUYỆT ĐỐI** bất kỳ dấu câu nào (phẩy `,`, chấm `.`, gạch ngang `-`, hai chấm `:`, chấm phẩy `;`) xuất hiện ở bất kỳ vị trí nào bên trong cụm từ ghép:
     - ❌ *"năng lực, tính toán"* $\to$ ✅ *"năng lực tính toán"*
     - ❌ *"lan truyền - ngược"* $\to$ ✅ *"lan truyền ngược"*
     - ❌ *"hàm, mất mát"* $\to$ ✅ *"hàm mất mát"*
     - ❌ *"đạo hàm, riêng"* $\to$ ✅ *"đạo hàm riêng"*

2. **Kỹ Thuật Neo Ngữ Pháp Thời Thể (Syntactic Prosodic Anchoring):**
   - Khi viết kịch bản, nếu cụm danh từ ghép kỹ thuật đứng làm chủ ngữ trực tiếp trước một động từ vị ngữ, **BẮT BUỘC** bổ sung một trợ từ thời thể (*"đã"*, *"đang"*, *"sẽ"*, *"được"*) hoặc từ định lượng (*"toàn bộ"*, *"các"*, *"nguồn"*) hoặc từ liên kết (*"chính là"*):
     - ❌ *"Năng lực tính toán tăng vọt khiến mô hình..."* (TTS dễ ngắt sau 'năng lực')
     - ✅ *"Năng lực tính toán đã tăng vọt, khiến mô hình..."* (Neo 'đã' bảo vệ trọn vẹn cụm 'năng lực tính toán')
     - ❌ *"Quá trình huấn luyện đòi hỏi dung lượng lớn."*
     - ✅ *"Toàn bộ quá trình huấn luyện đòi hỏi dung lượng bộ nhớ rất lớn."*

3. **Phân Cụm Hơi Thở Sinh Học (Biological Breath Groups 8–16 Từ):**
   - Tốc độ đọc 1.0x tự nhiên (TTS V0-Sense) của Zen yêu cầu nhịp thở trầm tĩnh, đĩnh đạc.
   - Mỗi vế câu (giữa 2 dấu phẩy/chấm) phải chứa từ **8 đến 16 từ**.
   - Cấm các vế câu vượt quá **22 từ** không có dấu phẩy lấy hơi. Điểm lấy hơi chỉ được đặt tại các liên từ tự nhiên (*"và"*, *"nhưng"*, *"mà"*, *"khi"*, *"để"*, *"do đó"*, *"vì vậy"*), tuyệt đối không ngắt ngang cụm từ ghép.

4. **Kiểm Toán Tự Động Trước Khi Synthesis (Gate 9 Quality Gate):**
   - Chạy kiểm toán prosody tự động trên kịch bản:
   ```bash
   python3 -c "from assets.scripts_video.vietnamese_prosody_v7 import audit_prosody_script_v7; res = audit_prosody_script_v7(open('TTS_INPUT_V6.md').read()); print('Score:', res.score); exit(0 if res.is_valid else 1)"
   ```
   - Chặn synthesis nếu điểm số $< 80.0$ hoặc có bất kỳ lỗi `split_defects` nào.

---

## 5. Kỹ Thuật Ghép Âm Nghệ Thuật Không Giật Cục (Zero-Jolt Artisan Splicing)

Đối với cụm thuật ngữ tiếng Anh dài, sử dụng giọng Anh đối ứng kết hợp 5 kỹ thuật:

1. **Contextual Carrier Sentence Prompting**: Bổ sung `... Term ...` để tránh pitch-drop.
2. **Noun-Phrase Semantic Chunking**: Tách theo cụm danh từ trọn nghĩa.
3. **Phonetic Boundary Stop-Gap**: Chèn 35–45ms lặng tại ranh giới chuyển ngữ.
4. **Equal-Power Cosine Crossfade**: Nối sóng bằng cosine đẳng năng lượng 25ms.
5. **EBU R128 Normalization & Room-Tone Injection**: Chuẩn -16.0 LUFS + room-tone -52.0 dBFS.

---

## 5. Premium Studio Mastering Chain 🆕

Chuỗi xử lý hậu kỳ phòng thu chuyên nghiệp cho giọng đọc kỹ thuật ZenPham, áp dụng **sau** khi synthesis và splicing hoàn tất:

### 5.1 Signal Chain (Thứ Tự Bắt Buộc)

```
Raw OmniVoice WAV (24kHz/16-bit)
  │
  ├─ 1. De-Noise Gate ─────── Noise floor suppression ≤ -60 dBFS
  │                           RNNoise hoặc noisereduce (stationary)
  │
  ├─ 2. De-Ess ────────────── Sibilance control cho âm "s", "x", "xác"
  │                           Threshold: -28 dB, Ratio 4:1, Band 4–9 kHz
  │
  ├─ 3. EQ Parametric ─────── Cắt rumble < 80 Hz (HPF 24dB/oct)
  │                           Boost presence 2.5–4 kHz (+2 dB, Q=1.2)
  │                           Boost air 10–12 kHz (+1.5 dB, Q=0.7, shelf)
  │                           Notch room resonance nếu có (analyze per-room)
  │
  ├─ 4. Compression ────────── Ratio 3:1, Threshold -20 dBFS
  │                           Attack 10ms, Release 80ms
  │                           Makeup gain: auto to target -16 LUFS
  │                           ⚠ CẤM ratio > 6:1 (phá hủy dynamic range tự nhiên)
  │
  ├─ 5. Warmth Saturation ──── Analog tape saturation nhẹ (2nd harmonic)
  │                           Drive: 10-15% (subtle warmth, không distort)
  │                           ⚠ Chỉ áp dụng cho zen-meditation & warm-radio
  │
  ├─ 6. Stereo Width ────────── Mid-Side processing (mono voice center)
  │                           Subtle stereo spread cho room ambience
  │                           Width: 15–20% (giữ mono compatibility)
  │
  ├─ 7. Limiter ─────────────── True peak: -1.0 dBTP
  │                           Lookahead: 5ms
  │
  └─ 8. Final Loudness ─────── EBU R128 normalize: -16.0 LUFS (YouTube)
                               Room-tone underlay: -52.0 dBFS
```

### 5.2 FFmpeg Implementation

```bash
# Premium mastering chain cho 1 scene
ffmpeg -i scene_raw.wav \
  -af "highpass=f=80:p=2, \
       equalizer=f=3000:t=q:w=1.2:g=2, \
       equalizer=f=11000:t=q:w=0.7:g=1.5, \
       acompressor=threshold=-20dB:ratio=3:attack=10:release=80, \
       alimiter=limit=-1dBTP:level=disabled, \
       loudnorm=I=-16:TP=-1:LRA=11" \
  -ar 24000 -ac 1 -sample_fmt s16 \
  scene_mastered.wav
```

### 5.3 Tiêu Chí Chất Lượng Studio

| Metric | Target | Tool đo |
|---|---|---|
| Integrated Loudness | -14.5 ± 0.5 LUFS (S1 Masterclass) / -16.0 LUFS | `ffmpeg -i file -af loudnorm=print_format=json -f null -` |
| True Peak | ≤ -1.45 dBFS (S1 Masterclass) / ≤ -1.0 dBTP | `ffmpeg -i file -af astats -f null -` |
| Noise Floor | ≤ -60 dBFS | `sox file -n stats` |
| Dynamic Range (LRA) | 8–14 LU | `loudnorm` output |
| Clipping | 0.00% (0 clipped samples) | `audio_join_quality.py` |

### 5.4 Kỷ Luật Phòng Chống Rè & Khoảng Nghỉ Kỹ Thuật (Zero-Rè & 2.4s Technical Pause Invariant) 🆕

1. **Khoảng Nghỉ Kỹ Thuật & Nghệ Thuật (Technical & Artistic Contemplation Pauses):**
   - Giữa các khối ý niệm toán học lớn, bắt buộc chèn một khoảng lặng kỹ thuật **$2.0\text{s} - 3.0\text{s}$ (chuẩn thực thi $2.4\text{s}$)**.
   - Khoảng nghỉ này vừa phục vụ việc tiêu hóa nhận thức cho người học, vừa giải phóng bộ đệm âm thanh và đồng bộ hoàn hảo với các micro-kinetic animations của Manim.
2. **Triệt Tiêu Hoàn Toàn Lỗi Rè / Click / Bụp (Zero-Jolt Waveform Continuity):**
   - Mọi thao tác cắt (trim) hoặc ghép (splice) câu thoại BẮT BUỘC phải diễn ra tại các điểm giao cắt số 0 (zero-crossing points) của sóng âm.
   - Tuyệt đối cấm cắt audio ngang đỉnh biên độ sóng (amplitude peak), gây ra tiếng click/pop/rè rất khó chịu trong tai nghe người nghe.
   - Sử dụng crossfade tối thiểu $15\text{ms} - 30\text{ms}$ tại các khớp nối để giữ tính liền mạch, đầm ấm của giọng Baritone F0.
| Sibilance peak | ≤ -12 dB at 6 kHz | Spectral analysis |

---

## 6. Hậu Kỳ Sóng Âm & Kiểm Soát Khoảng Lặng (Post-Synthesis QA)

1. **Giới Hạn Khoảng Lặng Nội Bộ (Internal Silence Capping)**:
   - Khoảng cách giữa các câu trong 1 scene: max `350ms – 450ms`.
   - `cap_internal_silence(input_wav, output_wav, max_silence_s=0.35)`

2. **Kiểm Toán Sóng Âm Tự Động (`audio_join_quality.py`)**:
   ```bash
   python3 assets/scripts_video/audio_join_quality.py <scene.wav>
   ```
   Tiêu chí đạt:
   - `clipped_samples_percent`: 0.00%
   - `peak_dbfs`: ≤ -0.5 dBFS
   - `longest_silence_ms`: ≤ 450 ms
   - `click_ratio_to_p99_delta`: ≤ 2.5

---

## 7. Quy Trình Đồng Bộ Thời Gian (Time-Sync Architecture)

### 7.1. Đồng Bộ Phụ Đề Từng Từ Qua Faster-Whisper (`whisper_aligner.py`)
1. GPU ThinkPad P15 (`device="cuda"`, `compute_type="float16"`).
2. Căn khớp lời thoại gốc qua `SequenceMatcher`.
3. Mỗi cue phụ đề: 1.2s – 4.2s, tối đa 8–10 từ/dòng.

### 7.2. Pha Nhịp Hoạt Họa Manim (`VoiceSyncTimeline`)
- CẤM `self.wait(50)`. Phân bổ nhịp theo trọng số âm thanh:
```python
from assets.scripts_video.manim_production import VoiceSyncTimeline

timeline = VoiceSyncTimeline(["audio/series_01/tap_XX_v6/scene_01.wav"])
timings = timeline.allocate(scene_index=0, n_animations=4, weights=[1.0, 2.5, 3.0, 1.5])
```

---

## 8. Voice Benchmark — Tiêu Chuẩn Phòng Thu ZenPham 🆕

Benchmark đánh giá chất lượng giọng đọc cho mỗi tập phim, chạy **trước** Golden Approval Gate.

### 8.1 Bộ Câu Benchmark Chuẩn (Chạy Mỗi Lần Thay Đổi Voice Config)

Mỗi khi thay đổi tham số OmniVoice, voice reference, hoặc mastering chain, **BẮT BUỘC** sinh audio từ 5 câu benchmark sau và so sánh A/B với bản reference:

```
[BM-01] Prose thuần Việt:
"Đôi khi, điều khó nhất không phải là tìm câu trả lời đúng, mà là chấp nhận rằng mình đã sai."

[BM-02] Code-switching kỹ thuật (neo ngữ pháp):
"Thuật toán Backpropagation lan truyền ngược vector gradient qua từng tầng ẩn của mạng nơ-ron, cập nhật trọng số bằng phương pháp Gradient Descent."

[BM-03] Đại lượng toán TTS-safe:
"Ba ma trận W Q, W K và W V được chiếu từ cùng vector x có kích thước d k bằng sáu mươi tư chiều."

[BM-04] Dấu tiếng Việt phức hợp (NFC stress test):
"Xác suất có điều kiện, Độ lệch chuẩn, Phép biến đổi tuyến tính, trọng số chú ý Attention. Ắ Ằ Ẳ Ẵ Ặ; Ấ Ầ Ẩ Ẫ Ậ; Ế Ề Ể Ễ Ệ."

[BM-05] Số & đơn vị (phương Nam):
"Năm hai ngàn không trăm mười bảy, chiều sâu vector tăng lên đến một trăm hai mươi tám, phương sai tăng tuyến tính theo d k, đẩy giá trị logit lên ba mươi hoặc bốn mươi."
```

### 8.2 Metrics Đánh Giá Tự Động

| Metric | Mô tả | Target | Tool |
|---|---|---|---|
| **MOS-LQO** | Mean Opinion Score ước lượng | ≥ 3.8 / 5.0 | PESQ hoặc ViSQOL |
| **Intelligibility** | Tỷ lệ từ nhận dạng đúng qua Whisper | ≥ 97% | Faster-Whisper → diff script gốc |
| **F0 Stability** | Jitter (biến thiên tần số cơ bản) | ≤ 1.5% | `parselmouth` (Praat) |
| **HNR** | Harmonics-to-Noise Ratio | ≥ 15 dB | `parselmouth` |
| **Formant Consistency** | F1/F2 drift giữa các câu | ≤ 8% CV | `parselmouth` |
| **Speaking Rate** | Tốc độ nói (âm tiết/giây) | 3.2 – 3.8 syl/s | Whisper timestamps |
| **Pause Pattern** | Ratio pause/speech | 0.15 – 0.25 | VAD analysis |
| **SNR** | Signal-to-Noise Ratio | ≥ 40 dB | `sox stats` |

### 8.3 Quy Trình Benchmark

```bash
# 1. Sinh 5 câu benchmark
python3 assets/scripts_video/voice_benchmark.py --synthesize

# 2. Chạy đo metrics tự động
python3 assets/scripts_video/voice_benchmark.py --evaluate

# 3. So sánh A/B với bản reference (lưu kết quả vào registry)
python3 assets/scripts_video/voice_benchmark.py --compare --baseline latest
```

### 8.4 Scorecard Mẫu

```
╔══════════════════════════════════════════════════════╗
║          ZENPHAM VOICE BENCHMARK v2.0                ║
╠══════════════════════════════════════════════════════╣
║ Voice: zen-meditation-mientay | Speed: 0.94x         ║
║ Date: 2026-09-12 | Config: num_step=48, gs=2.2      ║
╠═══════════════╦═══════╦═══════╦══════════════════════╣
║ Metric        ║ Score ║ Target║ Status               ║
╠═══════════════╬═══════╬═══════╬══════════════════════╣
║ Intelligibility║ 98.2% ║ ≥97%  ║ ✅ PASS              ║
║ F0 Stability  ║ 1.1%  ║ ≤1.5% ║ ✅ PASS              ║
║ HNR           ║ 18 dB ║ ≥15dB ║ ✅ PASS              ║
║ SNR           ║ 44 dB ║ ≥40dB ║ ✅ PASS              ║
║ Speaking Rate  ║ 3.4   ║ 3.2-3.8║ ✅ PASS             ║
║ Loudness      ║ -16.1 ║ -16±.5║ ✅ PASS              ║
║ True Peak     ║ -1.2  ║ ≤-1.0 ║ ✅ PASS              ║
║ Math Notation ║ 0 raw ║ 0     ║ ✅ PASS              ║
╠═══════════════╬═══════╬═══════╬══════════════════════╣
║ OVERALL       ║       ║       ║ ✅ STUDIO READY      ║
╚═══════════════╩═══════╩═══════╩══════════════════════╝
```

---

## 9. Bộ Ba Trạng Thái Phê Duyệt (The Golden Approval Gate)

Không bao giờ công bố tập phim nếu thiếu 3 chứng thực:

| Gate | Kiểm tra | Xác nhận |
|---|---|---|
| `audio-approved` | Nghe listening reel | Không vấp từ Anh, phát âm đúng, không giật rè, ngắt nghỉ đúng nhịp |
| `visual-approved` | Xem bản 2K60 mute | Đồ thị chính xác, căn giữa, chuyển động liên tục |
| `golden-approved` | Xem master hoàn chỉnh | Lệch âm-hình < 16.7ms, phụ đề sáng đúng nhịp, -14 LUFS broadcast |

---

## 10. Pipeline Tổng Hợp Đầy Đủ (v7)

```
Soạn vocal script (prose tiếng Việt, thuật ngữ EN giữ nguyên)
  ↓
Áp dụng Vietnamese Grammatical Anchoring (neo ngữ pháp)
  ↓
Chuẩn hóa Math Notation TTS-Safe (fix_tts_math_notation.py)
  ↓
Khóa Phonic Binding Cụm Danh Từ Kỹ Thuật (vietnamese_prosody_v7.py)  ← 🆕 V7
  ↓
Kiểm toán Prosody Gate 9 (audit_prosody_script_v7) → BLOCK nếu lỗi  ← 🆕 V7
  ↓
Chạy tts_code_switch_risk.py → BLOCK nếu HIGH
  ↓
A/B test term rủi ro → Lưu tts_term_registry_v4.json
  ↓
Synthesize audio (TTS V0-Sense tts_v0_sense_synthesizer.py, 1.0x native, 48kHz)
  ↓
cap_internal_silence.py (≤ 350ms)
  ↓
Premium Studio Mastering Chain (de-noise → EQ → compress → limit)
  ↓
audio_join_quality.py → BLOCK nếu fail
  ↓
Voice Benchmark Scorecard (≥97% intelligibility)
  ↓
whisper_aligner.py (timestamp từng từ)
  ↓
VoiceSyncTimeline → Manim animation timing (100% Clean Feed, zero hardsub)
  ↓
audio-approved → visual-approved → golden-approved
  ↓
XUẤT BẢN
```

---

## 11. Tiêu Chuẩn V8 — Vietnamese Expressive TTS: Gold TTS Tiêu Chuẩn Duy Nhất 🌟

Toàn bộ quy trình sản xuất giọng đọc bắt buộc sử dụng tiêu chuẩn **TTS V0-Sense** (`assets/scripts_video/tts_v0_sense_synthesizer.py`, AGENTS.md §1.4) thông qua skill độc quyền **`vietnamese-expressive-tts`**:
- **Khóa từ ghép nguyên khối (Zero-Split Lexical Invariant):** 500+ từ ghép 2-3 tiếng không bao giờ bị ngắt hơi sai giữa chừng.
- **Biểu cảm biên câu:** Head Attack (80-120ms headroom) và Tail Cadence Release (280-350ms decay tail).
- **Ma trận 24 Wave ngữ điệu:** Điều biến tốc độ và F0 theo từng câu, chấm dứt giọng đọc flat-rate đơn điệu.
- **Acoustic Clause Guard (TTS V0-Sense):** Tách mỗi đơn vị tổng hợp thành vế ≤ 75 ký tự (thay `...` bằng `, `), tốc độ 1.0x native (cấm `atempo < 1.0`), xác minh ASR vòng kín Faster-Whisper (≥ 75% độ phủ từ, tự động thử lại nếu méo).
- **Tài liệu & Skill chi tiết:** [.agents/skills/vietnamese-expressive-tts/SKILL.md](file:///home/zen/hermes-agent/.agents/skills/vietnamese-expressive-tts/SKILL.md)
- **Động cơ thực thi:** `assets/scripts_video/tts_v0_sense_synthesizer.py` (đọc trực tiếp kịch bản gốc, không tiền xử lý văn bản).

### Lệnh Kiểm Toán Kịch Bản V8:
```bash
python3 assets/scripts_video/vietnamese_expressive_prosody.py <script_file.txt> --verbose --out-json <cue_sheet.json> --out-txt <safe_tts.txt>
```
Triệt tiêu 100% lỗi ngắt nhịp giữa từ ghép, bảo vệ F0 contour mượt mà cho toàn bộ hệ sinh thái video.


