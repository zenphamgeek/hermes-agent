# Visual Effects, Camera Choreography & Micro-Animations
# ZENPHAM "Tôi Làm Việc" — Manim Production Guide

Tài liệu chuyên sâu về kỹ thuật tạo hiệu ứng thị giác đỉnh cao, điều phối chuyển động camera và nhịp điệu hoạt họa điện ảnh (Cinematic Pacing) trong Manim Community Edition.

---

## 1. Triết Lý Thẩm Mỹ Neo-Noir & Hệ Thống Layering

Khán giả hiện đại bị mỏi mắt trước những video nền đen tuyền đơn điệu hoặc nền trắng chói lòa. Phong cách **Neo-Noir Tech Minimalist** của kênh ZENPHAM sử dụng:

### 1.1. Tầng Màu & Độ Tương Phản (Contrast & Opacity Layering)

| Lớp (Layer) | Đối tượng | Màu sắc | Opacity / Độ sáng |
|:------------|:----------|:--------|:-------------------|
| **Lớp Nền (Background)** | Canvas toàn màn hình | `ZenPalette.BG_DEEP` (`#0c0d12`) | 1.0 (Không bao giờ dùng `#000000`) |
| **Lớp Khung (HUD/Card)** | Card chứa nội dung, panel | `ZenPalette.BG_CARD` (`#08090d`) | Fill 0.85 - 0.92, viền `#1e293b` |
| **Lớp Cấu Trúc (Grids/Axes)** | Trục tọa độ, lưới nền, phân cách | `ZenPalette.BORDER_SUBTLE` (`#1e293b`) | 0.15 - 0.30 (chỉ gợi mở không gian) |
| **Lớp Ngữ Cảnh (Context)** | Dữ liệu phụ, nhãn thứ cấp | `ZenPalette.TEXT_SECONDARY` (`#94a3b8`) | 0.45 - 0.60 |
| **Lớp Tiêu Điểm (Hero Object)** | Vector, đồ thị chính, nơ-ron trọng tâm | `ZenPalette.CYAN` / `ZenPalette.AMBER` | 1.0 + Viền phát quang Neon Glow |
| **Lớp Đột Phá (Eureka Moment)** | Khoảnh khắc tìm ra chân lý, tia chớp | `ZenPalette.NEON_CORE` (`#ffffff`) | 1.0 + Radial Energy Shockwave |

---

## 2. Kỹ Thuật Tạo Hiệu Ứng Phát Sáng Neon 3 Tầng (3-Layer Glow)

Manim không có GPU shader bloom mặc định, nhưng ta có thể tạo ảo giác phát sáng quang học chân thực bằng kỹ thuật **3-Layer Concentric Strokes**:

```python
from manim import *
from manim_production import ZenPalette

def make_neon_line(start, end, color=ZenPalette.CYAN):
    """Tạo đường thẳng phát sáng laser 3 lớp."""
    return VGroup(
        # Lớp 1: Hào quang ngoài cùng (Rộng, mờ)
        Line(start, end, stroke_color=color, stroke_width=8, stroke_opacity=0.2),
        # Lớp 2: Hào quang trung tâm (Vừa, bán trong suốt)
        Line(start, end, stroke_color=color, stroke_width=4, stroke_opacity=0.6),
        # Lớp 3: Lõi năng lượng trắng sáng (Mảnh, rực rỡ)
        Line(start, end, stroke_color=ZenPalette.NEON_CORE, stroke_width=1.5, stroke_opacity=1.0),
    )
```

Hoặc sử dụng trực tiếp class `GlowEffect` từ `manim_production`:
```python
from manim_production import GlowEffect

# Bọc bất kỳ Mobject nào để tạo vầng hào quang xung quanh
glow = GlowEffect(target_mob, color=ZenPalette.AMBER, num_layers=4, max_opacity=0.45)
self.play(FadeIn(glow), run_time=0.8)
```

---

## 3. Khoảnh Khắc Bừng Sáng Eureka (Aha! Moments)

Khi người kể chuyện trong video thốt lên: *"Và đây chính là khoảnh khắc thay đổi toàn bộ cuộc chơi..."*, thị giác phải bùng nổ đồng điệu.

### Kỹ thuật Eureka Shockwave:
```python
from manim import *
from manim_production import EurekaFlash, ZenPalette

class EurekaDemo(Scene):
    def construct(self):
        self.camera.background_color = ZenPalette.BG_DEEP

        center_pt = ORIGIN
        # 1. Tia chớp tỏa tròn từ trung tâm
        flash = EurekaFlash(center=center_pt, color=ZenPalette.AMBER, radius=3.2, num_lines=24)

        # 2. Vòng tròn sóng xung kích (Shockwave Ring)
        ring = Circle(radius=0.1, color=ZenPalette.GOLD, stroke_width=6).move_to(center_pt)

        # 3. Chân lý xuất hiện
        truth_formula = MathTex(r"E = mc^2", font_size=48, color=ZenPalette.CYAN).move_to(center_pt)

        self.play(
            Create(flash),
            ring.animate.scale(35).set_stroke(width=0, opacity=0),
            FadeIn(truth_formula, scale=1.5),
            run_time=1.4,
            rate_func=rate_functions.ease_out_quad
        )
        self.wait(1.5)
```

---

## 4. Điều Phối Camera Điện Ảnh (Camera Choreography)

Một video giáo dục chất lượng cao không bao giờ để khung hình tĩnh như một slide thuyết trình PowerPoint.

### 4.1. Kỹ Thuật Zoom Cận Cảnh Tiêu Điểm (2D Dynamic Framing)
Sử dụng `MovingCameraScene` để di chuyển ống kính vào vùng chi tiết khi giải thích công thức phức tạp:

```python
from manim import *
from manim_production import ZenPalette

class CinematicZoomScene(MovingCameraScene):
    def construct(self):
        self.camera.background_color = ZenPalette.BG_DEEP

        formula = MathTex(r"\nabla_\theta \mathcal{L} = \mathbb{E} \left[ \nabla_\theta \log \pi_\theta(a|s) Q^\pi(s, a) \right]", font_size=36)
        self.add(formula)

        # Zoom sát vào thành phần log policy
        log_term = formula[0][12:23]  # Chọn phân đoạn con

        self.play(
            self.camera.frame.animate.set(width=log_term.width * 3.5).move_to(log_term.get_center()),
            run_time=2.0,
            rate_func=rate_functions.ease_in_out_cubic
        )
        self.wait(1.0)

        # Trả lại góc rộng toàn cảnh
        self.play(
            self.camera.frame.animate.to_default_state(),
            run_time=1.8,
            rate_func=rate_functions.ease_in_out_quad
        )
```

### 4.2. Góc Nhìn 3D Cinematic Orbit (Không gian Đa Chiều)
Khi biểu diễn hàm mất mát, mặt cong manifold, hoặc cụm vector 3D:
- Giữ góc nhìn nghiêng ban đầu: `phi=65*DEGREES, theta=-45*DEGREES`.
- Bật quay chậm xung quanh trục: `self.begin_ambient_camera_rotation(rate=0.08)`.
- Khi có sự kiện quan trọng, lia nhanh camera để nhấn mạnh độ dốc.

---

## 5. Nhịp Điệu Hoạt Họa & Rate Functions (Emotional Pacing)

Tốc độ chuyển động quyết định cảm xúc của người xem:

| Rate Function | Đặc tính | Ứng dụng phù hợp |
|:--------------|:---------|:-----------------|
| `linear` | Đều đặn, máy móc | Đồng hồ cát chạy, luồng data truyền tải không ngừng |
| `smooth` (mặc định) | Tăng tốc ➜ Giảm tốc | Di chuyển card, chuyển đổi Mobject thông thường |
| `rush_into` | Bắt đầu chậm ➜ Lao vút vào đích | Hạt vật chất bị hút vào lỗ đen, điểm rơi cực tiểu |
| `rush_from` | Phóng vọt ra từ điểm xuất phát ➜ Hãm dần | Phóng tên lửa, tia sáng bùng nổ sau cú nhấp chuột |
| `ease_out_elastic` | Nảy nhẹ khi dừng lại | Nút bấm giao diện, popup card xuất hiện vui mắt |
| `wiggle` | Rung lắc nhẹ | Cảnh báo lỗi, bất định, dao động sóng |

### Quy tắc "Thở" (Breathing Room Rule):
- **Tuyệt đối không chạy 2 hoạt họa phức tạp liên tiếp mà không có `self.wait()`!**
- Sau mỗi biểu đồ lớn hoặc công thức cốt lõi: **bắt buộc `self.wait(1.5)` đến `self.wait(2.5)`** để người xem kịp ngấm kiến thức theo giọng đọc.

---

## 6. Dynamic Updaters & Traced Paths (Đồ Thị Tự Biến Thiên)

Làm đồ thị sống động bằng cách để các phần tử tự cập nhật theo biến số:

```python
from manim import *
from manim_production import ZenPalette

class DynamicUpdaterScene(Scene):
    def construct(self):
        self.camera.background_color = ZenPalette.BG_DEEP

        axes = Axes(x_range=[0, 6, 1], y_range=[0, 10, 2], x_length=6, y_length=4).shift(LEFT * 2)
        curve = axes.plot(lambda x: 0.3 * x**2 + 1, color=ZenPalette.CYAN)

        # Biến theo dõi x
        x_tracker = ValueTracker(1.0)

        # Điểm di chuyển trên đường cong (Tự cập nhật theo x_tracker)
        dot = always_redraw(lambda: Dot(
            axes.c2p(x_tracker.get_value(), 0.3 * x_tracker.get_value()**2 + 1),
            radius=0.1, color=ZenPalette.AMBER
        ))

        # Tiếp tuyến (Tangent Line) tự quay theo độ dốc đạo hàm f'(x) = 0.6x
        tangent = always_redraw(lambda: axes.get_secant_slope_group(
            x = x_tracker.get_value(),
            graph = curve,
            dx = 0.01,
            secant_line_length = 3,
            secant_line_color = ZenPalette.GOLD
        ))

        # Hiển thị số đo độ dốc theo thời gian thực
        slope_val = DecimalNumber(
            0.6 * x_tracker.get_value(),
            num_decimal_places=2,
            font_size=24, color=ZenPalette.GOLD
        )
        slope_val.add_updater(lambda d: d.set_value(0.6 * x_tracker.get_value()))
        slope_group = VGroup(Text("Độ dốc (Đạo hàm): ", font_size=18, color=ZenPalette.TEXT_SECONDARY), slope_val).arrange(RIGHT).to_edge(RIGHT, buff=1.0)

        self.add(axes, curve, dot, tangent, slope_group)
        self.play(x_tracker.animate.set_value(5.0), run_time=3.5, rate_func=rate_functions.ease_in_out_sine)
        self.wait(1.5)
```

---

## 7. Tia Laser Quét Ma Trận (Scanning Laser Beam)

Sử dụng `ShowPassingFlash` để tạo hiệu ứng quét tia laser qua ma trận dữ liệu hoặc dòng mã:

```python
from manim import *
from manim_production import ZenPalette

class LaserScanScene(Scene):
    def construct(self):
        self.camera.background_color = ZenPalette.BG_DEEP

        code_box = RoundedRectangle(width=6, height=3.5, corner_radius=0.15,
                                    stroke_color=ZenPalette.BORDER_SUBTLE, fill_color=ZenPalette.BG_CARD, fill_opacity=0.9)
        code_lines = VGroup(*[
            Text(f"Line {i+1}: self.attention_weights = softmax(Q @ K.T / sqrt(d))", font_size=13, color=ZenPalette.TEXT_DIM)
            for i in range(5)
        ]).arrange(DOWN, aligned_edge=LEFT, buff=0.25).move_to(code_box)

        self.add(code_box, code_lines)

        # Tia laser quét từ trên xuống dưới
        scan_line = Line(code_box.get_left() + UP * 1.5, code_box.get_right() + UP * 1.5,
                         color=ZenPalette.CYAN, stroke_width=4)

        self.play(
            scan_line.animate.shift(DOWN * 3.0),
            *[line.animate.set_color(ZenPalette.TEXT_PRIMARY) for line in code_lines],
            run_time=2.0,
            rate_func=rate_functions.ease_in_out_quad
        )
        self.play(FadeOut(scan_line))
        self.wait(1.0)
```
