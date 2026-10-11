---
name: ai-song-cover
description: Transform any song into an AI song cover using your custom voice sample.
version: 1.0.0
author: hermes-agent
license: MIT
platforms:
- linux
- macos
- windows
metadata:
  hermes:
    tags:
    - music
    - song-cover
    - singing-voice-conversion
    - rvc
    - audio
    - stem-separation
    - voice-cloning
    related_skills:
    - omnivoice-reader
    - media-studio
    - songsee
---

# AI Song Cover & Singing Voice Transformation Skill

Skill này tự động biến bất kỳ bài hát nào thành một bản **AI Song Cover** hoàn chỉnh sử dụng mẫu giọng nói/giọng hát của bạn (ví dụ: `zenpham-mien tay-trung nien.mp3` trong `assets/voices/`).

---

## When to Use

Sử dụng skill này khi:
- Người dùng yêu cầu dùng giọng của họ (hoặc một mẫu voice có sẵn) để cover/hát lại một bài hát input.
- Người dùng muốn tách vocal và beat từ một bài hát để thực hiện chuyển đổi giọng hát (Singing Voice Conversion).
- Cần dịch tone bài hát (pitch shift) cho phù hợp với quãng giọng nam/nữ.
- Cần mix & master tự động giữa vocal AI mới và beat nhạc nền.

---

## Architecture & Pipeline

Pipeline thực hiện qua 4 bước tự động hóa:

1. **Stem Separation (Tách Vocal & Beat)**: Sử dụng mô hình Demucs (`htdemucs_ft`) để tách bài hát gốc thành 2 luồng âm thanh sạch: `vocals.wav` và `instrumental.wav`.
2. **Pitch & Timbre Conversion (RVC v2 + RMVPE)**:
   - Trích xuất đường cao độ (F0 Pitch Contour) bằng thuật toán **RMVPE** (chính xác tuyệt đối nốt nhạc và luyến láy).
   - Chuyển đổi âm sắc từ giọng ca sĩ gốc sang giọng người dùng thông qua mô hình RVC v2 với feature retrieval matching.
   - Hỗ trợ dịch giọng (`--pitch`) theo số bán âm (semitones).
3. **Mastering & Audio Mixing**:
   - Khử chói (De-esser) và EQ vocal.
   - Áp dụng Reverb / Ambience để giọng hát hòa vào không gian bài hát.
   - Cân bằng âm lượng (LuFS matching) và xuất ra file chất lượng cao (MP3 320kbps / WAV).
4. **Hạ tầng thực thi**:
   - **Local GPU**: Chạy trực tiếp trên GPU máy cục bộ (CUDA PyTorch).
   - **Modal Serverless GPU**: Đẩy tác vụ lên 9 profile Modal GPU song song để xử lý siêu tốc mà không tốn tài nguyên máy.

---

## Quick Start Examples

### 1. Cover một bài hát với giọng ZenPham Miền Tây (Mặc định)

```bash
uv run python skills/media/ai-song-cover/scripts/cover.py \
  --song "path/to/song.mp3" \
  --voice "assets/voices/zenpham-mien tay-trung nien.mp3" \
  --output "output/zenpham_cover.mp3"
```

### 2. Cover bài hát từ ca sĩ nữ sang giọng nam (Dịch -12 bán âm / 1 quãng tám)

```bash
uv run python skills/media/ai-song-cover/scripts/cover.py \
  --song "path/to/female_song.mp3" \
  --voice "assets/voices/zenpham-mien tay-trung nien.mp3" \
  --pitch -12 \
  --reverb 0.25 \
  --output "output/zenpham_cover_low.mp3"
```

### 3. Cover bài hát từ ca sĩ nam sang giọng nữ (Dịch +12 bán âm)

```bash
uv run python skills/media/ai-song-cover/scripts/cover.py \
  --song "path/to/male_song.mp3" \
  --voice "assets/voices/mai - natural, bright and authentic.mp3" \
  --pitch 12 \
  --output "output/mai_cover_high.mp3"
```

### 4. Tăng/giảm âm lượng Vocal so với Beat

```bash
uv run python skills/media/ai-song-cover/scripts/cover.py \
  --song "path/to/song.mp3" \
  --voice "assets/voices/zenpham-mien tay-trung nien.mp3" \
  --vocal-vol 1.2 \
  --inst-vol 0.9 \
  --reverb 0.3 \
  --output "output/zenpham_bolero_cover.mp3"
```

### 5. Chạy qua Modal GPU Cloud (Siêu tốc độ)

```bash
uv run python skills/media/ai-song-cover/scripts/cover.py \
  --song "path/to/song.mp3" \
  --voice "assets/voices/zenpham-mien tay-trung nien.mp3" \
  --engine modal \
  --modal-profile r2rgraph \
  --output "output/modal_cover.mp3"
```

---

## CLI Options & Reference

| Tham số | Ý nghĩa | Mặc định | Ghi chú |
|---|---|---|---|
| `-s, --song` | Đường dẫn file bài hát gốc (`.mp3`, `.wav`, `.m4a`, `.mp4`) | *Bắt buộc* | Bài hát cần cover |
| `-v, --voice` | Đường dẫn file giọng mẫu (`.mp3`, `.wav`) hoặc tên voice trong `assets/voices/` | `zenpham-mien tay-trung nien` | Mẫu giọng dùng để hát |
| `-o, --output` | Đường dẫn lưu file cover hoàn chỉnh | `./output/covers/<song>_<voice>.mp3` | File kết quả |
| `-p, --pitch` | Số bán âm (semitones) cần dịch tone | `0` | `-12` (nữ $\rightarrow$ nam), `+12` (nam $\rightarrow$ nữ) |
| `--reverb` | Mức độ hiệu ứng Reverb không gian phòng (0.0 đến 1.0) | `0.2` | Tăng cho bolero/dân ca (0.3), giảm cho rap (0.1) |
| `--vocal-vol` | Hệ số khuếch đại âm lượng giọng hát (0.1 - 2.0) | `1.0` | 1.1 - 1.2 nếu muốn vocal nổi trội |
| `--inst-vol` | Hệ số khuếch đại âm lượng nhạc beat (0.1 - 2.0) | `1.0` | Giảm 0.85 - 0.9 nếu beat lấn át vocal |
| `--pitch-algo` | Thuật toán trích xuất cao độ (`rmvpe`, `crepe`, `harvest`, `pm`) | `rmvpe` | `rmvpe` cho độ mượt mà và chính xác cao nhất |
| `--engine` | Nơi thực thi (`local` hoặc `modal`) | `local` | `local` dùng GPU cục bộ, `modal` dùng cloud GPU |
| `--modal-profile` | Modal profile workspace (`r2rgraph`, `diatts`, `mojopham`, ...) | `r2rgraph` | Tận dụng token profile có sẵn |
| `--keep-stems` | Giữ lại các file `vocals.wav` và `instrumental.wav` sau khi mix | `False` | Hữu ích khi muốn tự mix lại bằng DAW |

---

## Tips & Best Practices

1. **Dịch Tone (`--pitch`)**:
   - Nếu bài hát gốc do ca sĩ **nữ** hát, nhưng giọng mẫu là **nam** (ZenPham): nên đặt `--pitch -12` hoặc `-10` để giọng trầm ấm tự nhiên, không bị gằn/cháy giọng.
   - Nếu cả bài hát gốc và giọng mẫu đều là **nam**: giữ nguyên `--pitch 0`.
2. **Chọn mẫu giọng (Voice Sample)**:
   - File giọng mẫu nên là âm thanh giọng nói hoặc hát rõ ràng, không lẫn tạp âm, tiếng ồn hay nhạc nền.
   - Các file có sẵn trong `assets/voices/` (như `zenpham-mien tay-trung nien.mp3`) đều đã qua xử lý lọc ồn đạt chuẩn.
3. **Hiệu ứng Reverb cho từng thể loại nhạc**:
   - **Bolero / Dân ca Tây Nam Bộ**: `--reverb 0.35 --vocal-vol 1.1` (tạo độ vang truyền cảm, ngọt ngào).
   - **Acoustic / Ballad**: `--reverb 0.2` (mộc mạc, gần gũi).
   - **Pop / EDM**: `--reverb 0.15` (giọng rõ, sắc nét, bám chặt nhịp).
