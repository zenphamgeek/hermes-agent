---
name: video-face-segmenter
description: Segment video into face angles and quality footage.
version: 1.5.0
author: hermes-community
license: MIT
platforms:
- linux
- macos
- windows
tags:
- media
- video
- segmentation
- face-detection
metadata:
  hermes:
    tags:
    - video face segmenter
    related_skills: []
---
# Video Face Segmenter & Footage Analyzer Skill

Skill này phân tích video dài (MP4), phát hiện khuôn mặt theo giới tính, đánh giá góc quay (yaw/pitch/roll), độ nét, che khuất, độ tin cậy detection và tính nhất quán nhân dạng — rồi trích xuất các phân đoạn (segments) chất lượng cao làm **Target Video cho SwapFace**. Chạy trên GPU qua LXC container `facefusion-ai`.

## When to Use

Use this skill when:
- The user asks to segment video into face angles and quality footage.
- Executing automated video face segmenter workflows and tasks.

## Khi nào kích hoạt:
- Người dùng yêu cầu phân tích, chia đoạn, lọc góc mặt, chuẩn bị footage từ video dài.
- Người dùng muốn tìm các đoạn video có khuôn mặt chuẩn góc để ghép mặt (`_OK`), loại bỏ đoạn mặt méo/ngửa cao/nghiêng sâu/bị che (`_NOT`), hoặc không có mặt (`_NOFACE`).
- Người dùng chỉ định phân tích theo giới tính: Nữ (`female`) hoặc Nam (`male`).

## Prerequisites

- LXC container `facefusion-ai` đang chạy (`lxc start facefusion-ai` nếu cần).
- **Idmap container** (chạy 1 lần):
  ```bash
  lxc config set facefusion-ai raw.idmap 'both 1000 1000'
  lxc restart facefusion-ai
  ```
  Đảm bảo container uid 1000 = host uid 1000 (file viết ra host zen-owned).
- Venv `/opt/seg-venv` trong container (insightface + scenedetect + opencv-headless + onnxruntime-gpu + numpy).
- Mount container: `host-data` (video nguồn → `/data/videos/`), `host-out-full` (`/home/zen/workspace/output` → cùng path host), preexisting `host-output` (`/output` → `/home/zen/workspace/output`).
- Path `-o "/output/..."` bị rewrite về `/home/zen/workspace/output/...`; nếu thiếu mount `host-out-full`, output rơi vào filesystem container-local (invisible trên host).

## How to Run

```bash
lxc exec facefusion-ai --user 1000 --group 1000 -- bash -c 'cd /opt/seg-venv && /opt/seg-venv/bin/python segmenter.py \
  -i "/data/videos/<FILE>.mp4" -g female -p strict --contiguous --sample-fps 10 \
  --ok-min-duration 5 --merge-gap 2 \
  -o "/output/segments/<NAME>_hq" --json 2>/tmp/x.err'
```

> **Đoạn dài ≥5s**: contiguous mode gộp các OK-run liền kề thành segment ≥ `--ok-min-duration` (mặc định 5s). Khoảng footage xấu ngắn (≤ `--merge-gap`, mặc định 2s: blink, che, cắt scene) được cầu nối thành 1 segment dài — không còn cắt vụn 1.5-3s.

> **Chạy dưới uid 1000 (`ubuntu`)** — hàng rào idmap container 0→1000000; uid 1000=host 1000 → file ra host-owned, snap VLC mở được.

Đọc kết quả từ `report.json` (stdout có thể in noise model-init ra stderr, rc đôi khi 1 dù thành công — luôn check `report.json`).

> **Lưu trữ Google Drive Filestore (Tiết kiệm SSD & Cloud Storage)**:
> - **Nguyên liệu thô (Base Media)** lưu tại `05_Footage/Raw/base_media`:
>   ```bash
>   python3 assets/scripts_video/filestore_sync_cli.py push-base-media --confirm
>   ```
> - **Phân đoạn & Báo cáo Analytics** lưu tại `05_Footage/Selects/segments`:
>   ```bash
>   python3 assets/scripts_video/filestore_sync_cli.py push-segments /output/segments/<NAME>_hq --confirm --prune-local
>   ```
> - Hoặc đồng bộ toàn bộ pipeline assets:
>   ```bash
>   python3 assets/scripts_video/filestore_sync_cli.py push-pipeline-assets --confirm
>   ```
> - Hoặc qua Python:
>   ```python
>   from video_pipeline_filestore_adapter import VideoPipelineFilestore
>   VideoPipelineFilestore.archive_all_segments("/output/segments", prune_local=False)
>   ```

## Quick Reference


| Preset | Yaw | Pitch | Roll | Occl. | Sharp | Det | Pass ratio |
|--------|-----|-------|------|-------|-------|-----|-----------|
| `strict` | ≤35° | ≤28° | ≤25° | ≤0.25 | ≥40 | ≥0.50 | 50% |
| `balanced` (default) | ≤45° | ≤35° | ≤35° | ≤0.35 | ≥20 | ≥0.40 | 30% |
| `relaxed` | ≤55° | ≤42° | ≤45° | ≤0.45 | ≥12 | ≥0.30 | 20% |
| `permissive` | ≤65° | ≤50° | ≤50° | ≤0.60 | ≥6 | ≥0.20 | 15% |

Các tham số ghi đè: `--max-yaw`, `--max-pitch`, `--min-sharpness`, `--min-face-height`, `--min-det-score`, `--pass-ratio`. Điều chỉnh runtime khác: `--sample-fps` (mặc định 6.0; dùng 10 để bắt sát frame xấu), `--max-scene-len` (mặc định 30s, `0` tắt), `--ok-min-duration` (độ dài segment tối thiểu, mặc định 5.0s), `--merge-gap` (giây footage xấu được cầu nối giữa 2 OK-run, mặc định 2.0), `--no-global-identity` (tắt gate 1-người toàn video).

## Procedure

1. **Chọn preset.** `strict` cho footage SwapFace chất lượng cao; `balanced` khi cần nhiều footage hơn, chấp nhận lẫn vài frame xấu.
2. **Bật chế độ contiguous** (`--contiguous`) khi mục tiêu là OK segments chất lượng cao. Mode này:
   - **Không** dán nhãn OK cho cả scene chỉ vì ≥50% frame đạt chuẩn (nguyên nhân OK lẫn 30-40% frame xấu trước đây).
   - Gộp mọi OK-run **trên toàn video** (xuyên scene cut) thành segment dài ≥ `--ok-min-duration` (mặc định **5s**); khoảng xấu ngắn ≤ `--merge-gap` giây được cầu nối. Mỗi segment 1 file `_OK` riêng.
   - Không xuất segment `_NOT`/`_NOFACE` (output sạch, sẵn cho swapface-folder).
3. **Gate nhân dạng** (`--min-id-sim`, mặc định 0.30): clustering embedding ArcFace greedy **theo scene** + **toàn video** (gate toàn cục, tắt bằng `--no-global-identity`). Đảm bảo mỗi segment dài chỉ 1 người — frame của identity khác không được cầu nối lẫn vào.
4. **Gate detection** (`min_det_score`): loại detection mờ/nhỏ/sai có độ tin cậy thấp khỏi mọi thống kê.
5. **Chạy** bằng lệnh How to Run, check `report.json` (counts.OK = số segment xuất ra + list `segments` với start/end/duration/file), verify file OK bằng `ffprobe`.
6. Kết quả `_OK` dùng thẳng làm target cho `modal-swapface` (xem skill `modal-swapface`).

## Pitfalls

- **Frame không chính xác với `-c copy`**: `-ss` trước `-i` seek về keyframe trước, segment thừa 0.3-1.3s. Fix: re-encode libx264 (từ v1.3.0) — frame-accurate, duration khớp run input.
- **Snap VLC trên host bị confinement**: không mở được file uid 1000000 (container root). Fix: raw.idmap `both 1000 1000` + chạy container process dưới uid 1000 (`--user 1000 --group 1000`). File ra host uid 1000 → VLC snap mở được. Không cần `sudo snap connect vlc`.
- **Container root không ghi được vào dir host pre-existing của zen** (permission denied). Dùng output dir mới (`*_hq`) hoặc `rmdir` dir rỗng trước khi chạy lại.
- **`lxc file pull -r` không lấy được file nằm trong filesystem container-local** — luôn output qua mount `/output`.
- **CUDA smoke-test ONNX**: dùng `opset 13` + `ir_version=8` (opset 26/IR 13 bị reject).
- `gender_confidence` là config chết (không được code đọc) — đã gỡ; gender lọc bằng `gender` argmax của insightface.
- Giới hạn hiện tại (chưa patch): không có blink/EAR (mắt nhắm vẫn qua), không có motion-blur riêng (sharpness là proxy), sampling rời rạc (6-10fps có thể lọt khoảng xấu ngắn giữa 2 sample).

## Verification

- Test: `scripts/run_tests.sh tests/skills/test_video_face_segmenter_skill.py -q` (test `quality.py`: clustering identity + trích/gộp OK run với `merge_gap`).
- Check output: `report.json` có `thresholds_used` phản ánh đúng preset/override, list `segments` có duration ≥ `--ok-min-duration`, và mọi file OK mở được bằng `ffprobe`.

## SwapFace Pipeline (sau khi Segment xong)

Sau khi segmenter tạo ra OK segments, dùng **Parallel SwapFace Pipeline** để swap face vào tất cả segments song song qua 5 Modal GPU profiles.

### Quick Start

```bash
# Dry-run: xem plan, không chạy GPU
python3 assets/video-pipeline/parallel_swapface.py \
  --scan-root /home/zen/workspace/output/segments \
  --source-face assets/faces/female/002\ Ly.jpeg \
  --dry-run

# Full run: swap tất cả pending segments, 5 profiles song song
python3 assets/video-pipeline/parallel_swapface.py \
  --scan-root /home/zen/workspace/output/segments \
  --source-face assets/faces/female/002\ Ly.jpeg

# Swap + assemble timeline (concat swapped OK + NOFACE)
python3 assets/video-pipeline/parallel_swapface.py \
  --scan-root /home/zen/workspace/output/segments \
  --source-face assets/faces/female/002\ Ly.jpeg \
  --assemble
```

### Cơ chế Timeout-Resilient

| Mechanism | Mô tả |
|---|---|
| **Checkpoint** | `swap_progress.json` per segment dir — resume sau crash |
| **Adaptive timeout** | `max(600, duration × 30)` — scale theo độ dài segment |
| **Profile rotation** | Timeout ở profile X → retry ở profile Y (khác quota) |
| **Idempotent skip** | File đã swap → skip tự động |
| **Modal retries** | `max_retries=1` ở Modal level cho cold-start flake/OOM |

### Deploy Modal App (1 lần / khi cập nhật)

```bash
cd assets/video-pipeline
for p in diatts mojopham mvlm motion vrag; do
  MODAL_PROFILE=$p modal deploy modal_swapface.py
done
```

### Files

- `assets/video-pipeline/parallel_swapface.py` — orchestrator chính
- `assets/video-pipeline/swap_segment_cli.py` — CLI bridge cho 1 segment
- `assets/video-pipeline/modal_swapface.py` — Modal GPU function (FaceFusion)
- `assets/video-pipeline/assemble_timeline.py` — concat timeline cũ (legacy)

