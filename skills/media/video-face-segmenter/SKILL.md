---
name: video-face-segmenter
description: Phân tích video MP4 dài thành các phân đoạn (segments) chứa khuôn mặt chuẩn góc nhìn, kích thước, độ nét, độ che phủ theo giới tính (male/female) và gắn nhãn _OK, _NOT, _NOFACE để chuẩn bị Target Footage cho SwapFace.
---

# Video Face Segmenter & Footage Analyzer Skill

Skill này cho phép Hermes Agent tự động phân tích một video dài (MP4), phát hiện và trích xuất các phân đoạn (segments) có chất lượng khuôn mặt lý tưởng để làm **Target Video cho SwapFace**.

## Khi nào kích hoạt:
- Người dùng yêu cầu phân tích, chia đoạn, lọc góc mặt, chuẩn bị footage từ video dài.
- Người dùng muốn tìm các đoạn video có khuôn mặt đẹp/chuẩn góc để ghép mặt (`_OK`), loại bỏ các đoạn mặt bị méo, ngửa quá cao, nghiêng quá sâu, bị che khuất (`_NOT`), hoặc không có mặt (`_NOFACE`).
- Người dùng chỉ định phân tích theo giới tính: Nữ (`female`) hoặc Nam (`male`).

## Lệnh thực thi:

```bash
python3 ~/.hermes/skills/video-face-segmenter/segmenter.py \
  --input "<đường_dẫn_video_mp4>" \
  --gender "<female|male|any>" \
  --preset "<strict|balanced|relaxed|permissive>" \
  --max-scene-len 30 \
  --output-dir "<thư_mục_xuất_kết_quả>" \
  --json
```

### Các tham số:
- `--input` (`-i`): Đường dẫn file video MP4 cần phân tích.
- `--gender` (`-g`): Giới tính cần phân tích (`female`, `male`, `any`). Mặc định: `female`.
- `--preset` (`-p`): Mức độ khắt khe của tiêu chuẩn đánh giá:
  - `strict`: Góc quay hẹp (|Yaw| ≤ 35°, |Pitch| ≤ 28°), độ nét cao (Sharpness ≥ 40), Pass Ratio 50%.
  - `balanced` (Mặc định): Góc vừa phải (|Yaw| ≤ 45°, |Pitch| ≤ 35°), độ nét vừa (Sharpness ≥ 20), Pass Ratio 30%.
  - `relaxed`: Góc rộng (|Yaw| ≤ 55°, |Pitch| ≤ 42°), độ nét nhẹ (Sharpness ≥ 12), Pass Ratio 20%. Rất thích hợp cho video chuyển động nhiều hoặc góc quay tự do.
  - `permissive`: Rất thoáng (|Yaw| ≤ 65°, |Pitch| ≤ 50°), chấp nhận góc cúi/nghiêng sâu, Pass Ratio 15%. Dùng khi muốn lấy tối đa footage có mặt để ghép.
- `--max-scene-len`: Thời lượng tối đa của mỗi clip footage (mặc định: `30.0` giây, `0` để tắt). Giúp chia các cảnh dài thành các clip ngắn vừa vặn cho SwapFace và tránh việc 1 cảnh dài bị đánh NOT chỉ vì một vài góc khuất.
- `--max-yaw`: Ghi đè góc quay trái/phải tối đa (độ).
- `--max-pitch`: Ghi đè góc cúi/ngửa tối đa (độ).
- `--min-sharpness`: Ghi đè độ sắc nét tối thiểu.
- `--pass-ratio`: Tỷ lệ frames đạt chuẩn tối thiểu trong scene để dán nhãn `_OK` (0.0 - 1.0).
- `--output-dir` (`-o`): Thư mục lưu các video segment và báo cáo (mặc định: `/output/segments/<video_name>/`).
- `--sample-fps`: Tần số lấy mẫu phân tích khung hình (mặc định: `6.0` fps).
- `--json`: Xuất kết quả tổng hợp dạng JSON.

## Định dạng file xuất ra:
Tất cả các đoạn video sau khi cắt không nén (lossless FFmpeg stream copy) được lưu trong 1 thư mục phẳng:
```
segment_0001_00-00-00_00-00-30_female_OK.mp4
segment_0002_00-00-30_00-01-00_female_NOT.mp4
segment_0003_00-01-00_00-01-15_female_NOFACE.mp4
report.json
timeline.csv
```

## Phản hồi người dùng:
1. Báo cáo tổng số cảnh quay (scenes) phát hiện được.
2. Thống kê số lượng đoạn **✅ _OK** (đạt chuẩn hoàn hảo), **⚠️ _NOT** (bị góc nghiêng/che/mờ), **❌ _NOFACE** (không có mặt target).
3. Đưa ra danh sách chi tiết các file `_OK` để người dùng chọn làm target footage cho FaceSwap.
