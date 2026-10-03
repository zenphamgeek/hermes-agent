# Layout Architecture, Collision Prevention & Typography
# ZENPHAM "Tôi Làm Việc" — Manim Production Guide

Tài liệu chuẩn hóa kiến trúc bố cục không gian, thuật toán tránh va chạm Mobject và quy tắc kiểu chữ tiếng Việt (Typography) cho chuỗi video Manim.

---

## 1. Không Gian Tọa Độ Màn Hình 16:9 & Vùng An Toàn (Safe Zones)

Trong Manim Community Edition với tỉ lệ mặc định 16:9:
- **Chiều rộng**: 14.222 Manim units (tọa độ $X$ từ $-7.111$ đến $+7.111$)
- **Chiều cao**: 8.000 Manim units (tọa độ $Y$ từ $-4.000$ đến $+4.000$)
- **Gốc tọa độ $(0, 0)$**: Nằm ngay chính giữa khung hình.

### Vùng An Toàn Đồ Họa (Action-Safe Margin):
Để tránh bị che khuất bởi giao diện YouTube (nút Pause, thanh tiến trình Timeline, Title, Watermark):
- **Margin X (Trái/Phải)**: Tối thiểu $0.6$ unit (Giới hạn thực tế: $X \in [-6.5, 6.5]$)
- **Margin Y (Trên/Dưới)**: Tối thiểu $0.45$ unit (Giới hạn thực tế: $Y \in [-3.55, 3.55]$)

---

## 2. Kiến Trúc Bố Cục Phân Vùng Rõ Ràng (Clear Spatial Partitioning — Chuẩn Toán Thầy Việt & 3B1B)

Mọi cảnh hoạt họa đạt đỉnh cao về sự rõ ràng (Clarity) đều phân tách màn hình thành **3 tầng không gian độc lập**, tuyệt đối không để chữ và hình học tranh chấp sự chú ý của người xem:

```
┌────────────────────────────────────────────────────────────────────────┐
│ ZONE 1: BREADCRUMB STATE TRACKER  [Y: +3.1 đến +3.5]                   │
│ Chuỗi node trạng thái nhận thức: (N) ── (Z) ── (Q) ── (R) ── (?)       │
│ Nút đang học sáng rực (Glow Neon), các nút khác mờ (opacity=0.35)      │
├──────────────────────────────────────────┬─────────────────────────────┤
│                                          │ ZONE 3: COGNITIVE STACK     │
│ ZONE 2: MAIN VISUAL STAGE (60% Width)    │ (40% Width) [X: +1.0 đến +6.0]│
│ [X: -6.0 đến +0.8, Y: -1.7 đến +2.8]     │                             │
│                                          │ 1. [EquationBox] Công thức  │
│ - Đồ thị hình học 2D / 3D, mặt phẳng phức│    trọng tâm viền neon sáng │
│ - Cây nhị phân, vector quay, đường sóng  │                             │
│ - Mũi tên cong PointCallout ("ở ĐÂY")    │ 2. [ConceptBadge] Thẻ tag   │
│ - Đường gióng nét đứt DashedLine         │    in hoa: [MẶT PHẲNG PHỨC]│
│                                          │                             │
│                                          │ 3. Quy tắc suy luận súc tích│
│                                          │    (NHÂN = xoay + co giãn)  │
├──────────────────────────────────────────┴─────────────────────────────┤
│ ZONE 4: BOTTOM EXPLAINER CALLOUT CARD  [Y: -2.4 đến -1.8]              │
│ Thẻ kính mờ đen bo góc chứa 1-2 dòng triết lý tinh túy của phân cảnh   │
├────────────────────────────────────────────────────────────────────────┤
│ ZONE 5: SUBTITLE CC EXCLUSION ZONE  [Y: < -2.6]                        │
│ BẮT BUỘC ĐỂ TRỐNG 100% CHO PHỤ ĐỀ YOUTUBE TỰ ĐỘNG                     │
└────────────────────────────────────────────────────────────────────────┘
```

### 2.1. Code Recipe: Bố Cục 2 Cột Bất Đối Xứng (Two-Column Asymmetric Canvas)
```python
from manim import *
from manim_production import (
    ZenPalette, StateTrackerBar, ConceptBadge,
    BottomCalloutCard, PointCallout, EquationBox
)

class ClearLayoutScene(Scene):
    def construct(self):
        self.camera.background_color = ZenPalette.BG_DEEP

        # 1. Dải chỉ mục tư duy đỉnh màn hình
        tracker = StateTrackerBar(
            states=["N", "Z", "Q", "R", "?"],
            active_index=4,  # Highlight dấu hỏi số phức '?'
            y_pos=3.3,
            spacing=1.6,
            active_color=ZenPalette.GOLD
        )
        self.play(FadeIn(tracker, shift=DOWN*0.2), run_time=0.6)

        # 2. Cột Phải: Cognitive Stack (Công thức + Concept Badge)
        eq_box = EquationBox(r"i^2 = -1", width=3.8, font_size=28, accent_color=ZenPalette.CYAN)
        eq_box.shift(RIGHT * 3.6 + UP * 1.6)

        badge = ConceptBadge("Mặt Phẳng Phức", color=ZenPalette.CYAN)
        badge.shift(RIGHT * 3.6 + UP * 0.4)

        rule = Text("NHÂN = xoay 90° + co giãn", font="sans-serif", font_size=13, color=ZenPalette.GOLD)
        rule.shift(RIGHT * 3.6 + DOWN * 0.4)

        self.play(Create(eq_box), FadeIn(badge), FadeIn(rule), run_time=0.8)

        # 3. Cột Trái: Visual Stage (Sân khấu hình học thuần khiết)
        plane = NumberPlane(
            x_range=[-3, 3, 1], y_range=[-2, 2, 1],
            x_length=5.4, y_length=3.6,
            background_line_style={"stroke_color": ZenPalette.BORDER_SUBTLE, "stroke_opacity": 0.4}
        ).shift(LEFT * 2.8 + DOWN * 0.1)

        arc = Arc(radius=1.2, start_angle=0, angle=PI/2, color=ZenPalette.CYAN, stroke_width=3.0)
        arc.shift(plane.c2p(0, 0))

        callout = PointCallout(plane.c2p(0, 1.2), label="ở ĐÂY (i)", direction=UR)

        self.play(Create(plane), Create(arc), FadeIn(callout), run_time=1.2)

        # 4. Thẻ chú giải triết lý đáy màn hình (cách ly phụ đề Y >= -2.4)
        callout_card = BottomCalloutCard(
            "Khoảnh khắc đó, trục số 1 chiều tung ra thành MẶT PHẲNG SỐ 2 chiều.",
            width=10.5, y_pos=-2.1
        )
        self.play(FadeIn(callout_card, shift=UP*0.2), run_time=0.7)
        self.wait(2.0)
```

---

## 3. Động Cơ Tránh Va Chạm `safe_place()` (Collision Engine)

### 3.1. Vấn Đề Kinh Điển Của Manim:
Hàm `.next_to(target, DIRECTION, buff=...)` thuần túy chỉ tính khoảng cách với một đối tượng duy nhất. Nếu xung quanh có vật thể thứ 3, văn bản sẽ bị đè chồng lên hình vẽ (Audit 25 tập cho thấy 55/88 cảnh gặp lỗi này!).

### 3.2. Giải Pháp: `safe_place()`
Hàm `safe_place()` tự động tính toán Hộp bao (Bounding Box) và dịch chuyển thông minh:

```python
from manim_production import safe_place, ZenPalette

# Đặt nhãn label cạnh mũi tên, đồng thời tự tránh 3 hình chữ nhật đã vẽ trước
safe_place(
    mob = label,
    anchor = arrow,
    direction = RIGHT,
    buff = 0.35,
    avoid = [rect_a, rect_b, rect_c],
    strategy = "shift_then_scale",  # Ưu tiên dịch chuyển, nếu chật quá tự thu nhỏ
    min_scale = 0.75               # Không thu nhỏ quá 75% kích thước gốc
)
```

### 3.3. Tự Động Kẹp Trong Khung Hình (`SafeZone.clamp` & 15% Safe Padding)
```python
from manim_production import SafeZone

# Chuẩn Safe Margin 15%: 2.13 units chiều ngang, 1.20 units chiều dọc
safe_zone = SafeZone(margin_x=2.13, margin_y=1.20)
# Đảm bảo khối văn bản không bao giờ bị văng ra khỏi rìa màn hình, không chạm Subtitle
safe_zone.clamp(large_diagram_group)
```

### 3.4. Chuẩn Tránh Tràn Viền Hộp (Zero Text-Out-of-the-Box)
> [!CAUTION]
> Tuyệt đối không bao giờ khởi tạo hộp chữ nhật `RoundedRectangle` với chiều rộng/chiều cao cố định nhỏ hơn nội dung text bên trong, khiến chữ bị chòi ra ngoài viền lố lăng.
>
> **Giải pháp chuẩn:**
> ```python
> # Luôn dùng SurroundingRectangle để hộp bao bọc hoàn hảo nội dung
> code_text = Text(code_str, font="monospace", font_size=13, color=ZenPalette.CYAN)
> code_box = SurroundingRectangle(
>     code_text,
>     buff=0.30,
>     corner_radius=0.15,
>     color=ZenPalette.MUTED,
>     fill_color="#0a0c10",
>     fill_opacity=0.95,
>     stroke_width=2.0
> )
> code_group = VGroup(code_box, code_text)
> ```

---

## 4. Chuẩn Kiểu Chữ Tiếng Việt (Vietnamese Typography)

### 4.1. Sự Cố Diacritics Trong LaTeX
Trong Manim CE, `MathTex` và `Tex` chạy qua hệ thống phân tích cú pháp LaTeX. Khi gặp tiếng Việt có dấu (`ế, ệ, ơ, ư, ặ`), LaTeX rất dễ phát sinh lỗi font hoặc rơi rụng dấu.

### 4.2. Quy Tắc Bắt Buộc:
1. **Đối với công thức Toán học thuần túy**: Dùng `MathTex(r"...")` với cú pháp LaTeX chuẩn.
2. **Đối với văn bản tiếng Việt**: Dùng `Text(..., font="Be Vietnam Pro")` hoặc font Sans-serif hệ thống hỗ trợ đầy đủ Unicode (`font="Arial"` hoặc `"sans-serif"`).

```python
from manim import Text
from manim_production import ZenPalette

# Văn bản tiếng Việt sắc nét, chuẩn dấu:
vn_label = Text(
    "Đạo hàm không phải là công thức khô khan,\nmà là chiếc la bàn trong bóng tối.",
    font="sans-serif",
    font_size=18,
    color=ZenPalette.TEXT_PRIMARY,
    line_spacing=1.35
)
```

### 4.3. Bảng Phân Cấp Kích Thước Chữ (Typography Ladder)

| Phân cấp | Kích thước (`font_size`) | Sử dụng cho |
|:---------|:------------------------|:------------|
| **Display Title** | $32 - 36$ | Tựa đề chính mở đầu phân cảnh |
| **Section Header** | $22 - 26$ | Tiêu đề các Card HUD, tên định lý |
| **Body Text** | $16 - 18$ | Câu diễn giải, lời bình sư phạm |
| **Subtext / Footnote** | $12 - 14$ | Đơn vị đo, chú thích trục, công thức phụ |
| **Hero Equation** | $32 - 40$ | Công thức trung tâm của khoảnh khắc Eureka |

---

## 5. Tự Động Xuống Dòng & Giới Hạn Chiều Rộng (Auto-Wrapping)

Không bao giờ để một dòng chữ dài quá $6.0$ Manim units mà không ngắt dòng. Khán giả xem trên điện thoại hoặc máy tính bảng sẽ không thể đọc kịp nếu mắt phải quét quá dài.

```python
def make_wrapped_text(text_str, max_width=5.5, font_size=16, color=ZenPalette.TEXT_PRIMARY):
    """Tự động co giãn để văn bản không bao giờ tràn khung."""
    txt = Text(text_str, font_size=font_size, color=color, line_spacing=1.3)
    if txt.width > max_width:
        txt.scale_to_fit_width(max_width)
    return txt
```
