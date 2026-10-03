# Scriptwriting Workflow, Voice-Sync & SFX Integration
# ZENPHAM "Tôi Làm Việc" — Manim Production Guide

Quy trình chuẩn hóa từ ý tưởng kịch bản (Script Idea) đến kịch bản phân cảnh hoạt họa Manim đồng bộ giọng đọc (Voice-Sync) và âm thanh hiệu ứng (SFX).

---

## 1. Cấu Trúc Kịch Bản 4 Nhịp (The 4-Beat Narrative Arc)

Mọi tập phim trong series "Tôi Làm Việc" kế thừa công thức từ kênh Median kết hợp với góc nhìn thực chiến của Kỹ sư AI 10+ năm kinh nghiệm:

```
┌───────────────────────────┐
│ 1. VA CHẠM THỰC TẾ        │  Mở đầu bằng một bài toán sống còn tại InnoRia Solution
│ (Practical Dilemma)       │  Ví dụ: Mô hình 70B bị nổ loss, hệ thống gợi ý bị nghịch lý dữ liệu.
├───────────────────────────┤
│ 2. MỔ XẺ HÌNH HỌC MANIM   │  Trực quan hóa bản chất toán học bằng Manim (Hình học trước Đại số)
│ (Geometric Dissection)    │  Khán giả "nhìn thấy" cấu trúc không gian trước khi thấy công thức.
├───────────────────────────┤
│ 3. ỨNG DỤNG SỐNG CÒN      │  Liên hệ trực tiếp đến thuật toán AI hiện đại
│ (AI Engineering Survival) │  Tại sao Batch Normalization cứu CNN? Tại sao Softmax cứu Attention?
├───────────────────────────┤
│ 4. ĐẠO LÀM NGHỀ           │  Đúc kết triết lý kỹ thuật (Digital Craftsmanship)
│ (Craftsmanship Insight)   │  "Không cần biết trước cả con đường, chỉ cần mỗi bước đi giảm thiểu sai số."
└───────────────────────────┘
```

---

## 2. Đồng Bộ Giọng Đọc Thời Gian Thực (`VoiceSyncTimeline`)

Lỗi phổ biến nhất khi viết kịch bản hoạt hình là **thời lượng hình ảnh lệch pha với giọng đọc** (hình kết thúc quá sớm hoặc nói xong mà hình vẫn đang chạy).

### Cách sử dụng `VoiceSyncTimeline`:
```python
from manim_production import VoiceSyncTimeline

# Khởi tạo timeline với danh sách file WAV đã thu âm từ TTS
timeline = VoiceSyncTimeline([
    "audio/scene_01.wav",  # Ví dụ thời lượng 32.4 giây
    "audio/scene_02.wav",  # Thời lượng 45.0 giây
])

# Phân bổ thời lượng cho 4 nhịp hoạt họa trong Scene 1 theo tỉ lệ trọng số (weights):
# - Nhịp 1: Xuất hiện đề bài (nhanh)
# - Nhịp 2: Khám phá nghịch lý (trọng tâm)
# - Nhịp 3: Biến đổi hình học (trọng tâm)
# - Nhịp 4: Đúc kết bài học (nghỉ ngơi)
timings = timeline.allocate(scene_index=0, n_animations=4, weights=[1.0, 2.5, 2.5, 1.5])
# timings = [4.32s, 10.80s, 10.80s, 6.48s] -> Khớp tuyệt đối 32.4s!

# Áp dụng vào Scene:
self.play(Create(intro_group), run_time=timings[0])
self.play(Transform(intro_group, puzzle_group), run_time=timings[1])
self.play(Create(eureka_effect), run_time=timings[2])
self.wait(timings[3])  # Khoảng thở để người xem chiêm nghiệm lời kết
```

---

## 3. Hệ Thống Âm Thanh Hiệu Ứng (SFX Cue Integration)

Âm thanh mang lại linh hồn cho đồ họa vector. Manim Module tích hợp sẵn 8 hiệu ứng âm thanh CC0:

| SFX Identifier | Tên hiệu ứng | Sự kiện kích hoạt phù hợp |
|:---------------|:-------------|:--------------------------|
| `whoosh` | Tiếng gió vút | Tia sáng bắn ngang màn hình, camera lia nhanh, đổi góc nhìn |
| `pop` | Bong bóng tách | Một nơ-ron bật sáng, điểm dữ liệu xuất hiện trên đồ thị |
| `impact` | Tiếng va chạm trầm | Khoảnh khắc chân lý Eureka, định lý cốt lõi đóng dấu |
| `shimmer` | Ngân vang lấp lánh | Mô hình đạt độ hội tụ hoàn hảo, triết lý đọng lại |
| `typewriter` | Bàn phím cơ | Các dòng code terminal hiện ra |
| `swoosh` | Chuyển cảnh mềm | Toàn bộ Mobject tan biến để đón cảnh tiếp theo |
| `heartbeat` | Nhịp tim điện tử | Quá trình lặp qua từng Epoch trong vòng lặp huấn luyện |
| `glitch` | Nhiễu sóng kỹ thuật | Lỗi tràn số NaN, sập server, vượt quá giới hạn |

### Xuất Bảng Cue Sheet SFX:
Khi viết kịch bản phân cảnh Manim, ghi chú rõ mốc thời gian chèn SFX:
```python
from manim_production import SFXCue, mix_sfx

# Định nghĩa danh sách âm thanh
cues = [
    SFXCue(sfx_type="whoosh", timestamp=2.5, volume=0.8),
    SFXCue(sfx_type="pop", timestamp=4.2, volume=0.6),
    SFXCue(sfx_type="impact", timestamp=12.0, volume=1.0),
    SFXCue(sfx_type="shimmer", timestamp=28.5, volume=0.7),
]

# Tự động mux SFX vào video sau khi Manim render xong:
mix_sfx(
    video_path="media/videos/manim_scene/1080p60/SceneName.mp4",
    cues=cues,
    output_path="media/videos/final_with_sfx.mp4"
)
```

---

## 4. Prompt Template Chuẩn Cho LLM Khi Viết Kịch Bản Manim

Khi yêu cầu một mô hình LLM viết kịch bản Manim cho một tập phim mới, hãy tuân theo cấu trúc Prompt sau để đạt chất lượng cao nhất:

```markdown
Bạn là Đạo diễn Hoạt họa Manim chuyên nghiệp của series ZENPHAM "Tôi Làm Việc".
Nhiệm vụ của bạn là hiện thực hóa phân cảnh sau bằng Manim CE:

- Chủ đề: [Chủ đề toán/AI, ví dụ: Nghịch lý Simpson trong gợi ý tín dụng]
- Thời lượng âm thanh lồng tiếng: [Thời lượng, ví dụ: 42 giây]
- Giọng đọc: "..."

Yêu cầu thực thi bắt buộc:
1. Áp dụng quy tắc "Hình học trước Đại số": Trực quan hóa bản chất trước khi hiện công thức.
2. Thiết kế bố cục chuẩn 4 vùng, dùng `manim_production.py` và `safe_place()`, tuyệt đối không đè chữ lên hình.
3. Sử dụng bảng màu `ZenPalette` (Nền `#0c0d12`, Cyan `#00f0ff`, Amber `#f59e0b`).
4. Sử dụng `VoiceSyncTimeline` để phân bổ chính xác thời gian các lệnh `play()` và `wait()`.
5. Liệt kê bảng mốc thời gian âm thanh SFX (whoosh, pop, impact, shimmer).
6. Mã nguồn Python phải khép kín, độc lập, có thể render ngay lập tức mà không phát sinh lỗi.
7. Vocal Script dùng một câu tiếng Việt liền mạch có thể chứa thuật ngữ tiếng Anh tại đúng vị trí ngữ nghĩa. Giữ nguyên spelling; không viết phiên âm Việt, không thêm câu dịch Anh, không tách voice.
8. Không mở câu hoặc mệnh đề bằng bare English term. Viết neo ngữ pháp Việt đúng nghĩa, ví dụ: `mô hình LLM`, `phương pháp PCA`, `hàm Softmax`, `độ calibration`, `chỉ số MSE`, `thuật toán Backpropagation`.
9. Sau rewrite, cue sheet phải qua `tts_code_switch_risk.py`; mọi finding mức `high` phải sửa trước khi synthesis.
```
