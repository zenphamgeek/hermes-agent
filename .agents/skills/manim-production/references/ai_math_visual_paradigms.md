# AI & Math Visual Paradigms — Production Manim Code Recipes
# ZENPHAM "Tôi Làm Việc" Series — 3Blue1Brown & Median Style

Tài liệu cung cấp 10 kịch bản mẫu Manim hoàn chỉnh, sẵn sàng render, được thiết kế theo chuẩn thẩm mỹ đỉnh cao (Neo-Noir, Obsidian `#0c0d12`, Pastel Neon Glow) nhằm trực quan hóa các khái niệm trừu tượng trong Toán học và Trí tuệ Nhân tạo.

---

## Mục Lục 10 Visual Paradigms

1. [Paradigm 1: 3D Loss Landscape & Gradient Descent Trajectory](#paradigm-1-3d-loss-landscape--gradient-descent-trajectory)
2. [Paradigm 2: Vector Embeddings & Geometric Cosine Projection](#paradigm-2-vector-embeddings--geometric-cosine-projection)
3. [Paradigm 3: Transformer Self-Attention Spotlight & Matrix Alignment](#paradigm-3-transformer-self-attention-spotlight--matrix-alignment)
4. [Paradigm 4: Deep Neural Network Forward Pulse & Backprop Lightning](#paradigm-4-deep-neural-network-forward-pulse--backprop-lightning)
5. [Paradigm 5: 3D Tensor Slicing & Normalization (BatchNorm vs LayerNorm)](#paradigm-5-3d-tensor-slicing--normalization-batchnorm-vs-layernorm)
6. [Paradigm 6: Galton Board & Central Limit Theorem (Hỗn loạn ➜ Chuông Gauss)](#paradigm-6-galton-board--central-limit-theorem-hỗn-loạn--chuông-gauss)
7. [Paradigm 7: Simpson's Paradox (Nghịch lý dữ liệu & Biến số ẩn)](#paradigm-7-simpsons-paradox-nghịch-lý-dữ-liệu--biến-số-ẩn)
8. [Paradigm 8: Shannon Entropy & Latent Information Compression](#paradigm-8-shannon-entropy--latent-information-compression)
9. [Paradigm 9: Step-by-Step TransformMatchingTex Proof with Invariant Glow](#paradigm-9-step-by-step-transformmatchingtex-proof-with-invariant-glow)
10. [Paradigm 10: Event-Driven Agentic Pipeline & Self-Healing Queue](#paradigm-10-event-driven-agentic-pipeline--self-healing-queue)

---

## Paradigm 1: 3D Loss Landscape & Gradient Descent Trajectory

### Ý tưởng trực quan:
Không chỉ vẽ công thức $\theta_{t+1} = \theta_t - \eta \nabla L$. Hãy đưa người xem vào một không gian 3D uốn lượn hiểm trở. Một quả cầu neon phát sáng lăn từ đỉnh núi hiểm trở, vượt qua các điểm yên ngựa (saddle point) nhờ động lượng (momentum), để lại vệt sáng neon phát quang trước khi đáp xuống thung lũng cực tiểu toàn cục.

```python
from manim import *
import numpy as np
from manim_production import ZenPalette, NeonArrow, DiagramCard, GlowEffect

class LossLandscapeScene(ThreeDScene):
    def construct(self):
        # 1. Thiết lập background và camera
        self.camera.background_color = ZenPalette.BG_DEEP
        self.set_camera_orientation(phi=65 * DEGREES, theta=-45 * DEGREES)

        # 2. Định nghĩa hàm mất mát phi lồi (non-convex surface)
        def loss_func(u, v):
            # Hàm tạo bề mặt gồm nhiều thung lũng và điểm yên ngựa
            z = 0.5 * (u**2 + v**2) + 0.8 * np.sin(2.5 * u) * np.cos(2.5 * v)
            return np.array([u, v, z])

        axes = ThreeDAxes(
            x_range=[-3, 3, 1],
            y_range=[-3, 3, 1],
            z_range=[-1, 5, 1],
            x_length=6, y_length=6, z_length=4,
        ).set_color(ZenPalette.TEXT_DIM)

        surface = Surface(
            loss_func,
            u_range=[-2.5, 2.5],
            v_range=[-2.5, 2.5],
            resolution=(40, 40),
            should_make_jagged=False,
        )
        surface.set_style(
            fill_opacity=0.65,
            fill_color=ZenPalette.BG_CARD_ALT,
            stroke_color=ZenPalette.CYAN,
            stroke_width=0.8,
            stroke_opacity=0.7,
        )

        # 3. HUD Title (2D Overlay)
        self.add_fixed_in_frame_mobjects()
        title = Text("3D Loss Landscape: Gradient Descent with Momentum", 
                     font_size=24, color=ZenPalette.CYAN).to_corner(UL)
        card = DiagramCard(
            content=MathTex(r"\theta_{t+1} = \theta_t - \eta \nabla_\theta \mathcal{L} + \beta v_t", font_size=28),
            title="Update Rule",
            accent_color=ZenPalette.AMBER,
            width=4.5, height=1.5
        ).to_corner(UR)
        self.add(title, card)
        self.remove_fixed_in_frame_mobjects()

        # 4. Hiệu ứng xuất hiện bề mặt
        self.play(Create(axes), run_time=1.5)
        self.play(Create(surface), run_time=2.5)
        self.wait(0.5)

        # 5. Khởi tạo quả cầu Gradient Descent (Ball) với vệt sáng
        start_pt = np.array([-2.0, 1.8, loss_func(-2.0, 1.8)[2]])
        ball = Sphere(center=start_pt, radius=0.15).set_color(ZenPalette.AMBER)
        glow = GlowEffect(ball, color=ZenPalette.AMBER, num_layers=4, max_opacity=0.4)
        ball_group = VGroup(glow, ball)

        self.play(FadeIn(ball_group, scale=0.5))

        # Đường đi mô phỏng Gradient Descent với Momentum
        path_points = [
            start_pt,
            np.array([-1.5, 1.2, loss_func(-1.5, 1.2)[2]]),
            np.array([-0.8, 0.9, loss_func(-0.8, 0.9)[2]]),
            np.array([-0.2, 0.4, loss_func(-0.2, 0.4)[2]]),
            np.array([0.0, -0.1, loss_func(0.0, -0.1)[2]]),
        ]

        # Camera quay nhẹ tạo cảm giác không gian đa chiều (Cinematic Orbit)
        self.begin_ambient_camera_rotation(rate=0.12)

        # Di chuyển bóng qua từng điểm và vẽ vệt sáng (Trajectory)
        for i in range(len(path_points) - 1):
            p1, p2 = path_points[i], path_points[i+1]
            segment = Line(p1, p2, color=ZenPalette.AMBER, stroke_width=3)
            self.play(
                ball_group.animate.move_to(p2),
                Create(segment),
                run_time=1.0,
                rate_func=rate_functions.ease_in_out_quad
            )

        self.stop_ambient_camera_rotation()
        self.wait(1.5)
```

---

## Paradigm 2: Vector Embeddings & Geometric Cosine Projection

### Ý tưởng trực quan:
Làm sao từ ngữ biến thành toán học? Hiển thị không gian ngữ nghĩa (Semantic Space). Hai vector từ `"Vua"` và `"Nữ Hoàng"` cùng vector `"Đàn Ông"` và `"Phụ Nữ"`. Phép chiếu vuông góc (Projection shadow) đổ bóng xuống đường chuẩn, cho thấy tích vô hướng chính là hình chiếu trực giác của sự tương đồng.

```python
from manim import *
from manim_production import ZenPalette, NeonArrow, DiagramCard, EquationBox

class VectorEmbeddingScene(Scene):
    def construct(self):
        self.camera.background_color = ZenPalette.BG_DEEP

        # 1. Tiêu đề và Khung công thức
        title = Text("Vector Embeddings: Hình Học của Sự Tương Đồng", 
                     font_size=28, color=ZenPalette.TEXT_PRIMARY).to_edge(UP, buff=0.4)
        self.play(Write(title))

        plane = NumberPlane(
            x_range=[-1, 6, 1], y_range=[-1, 5, 1],
            x_length=8, y_length=5.5,
            background_line_style={"stroke_color": ZenPalette.BORDER_SUBTLE, "stroke_width": 1}
        ).shift(LEFT * 1.5 + DOWN * 0.3)
        self.play(Create(plane), run_time=1.5)

        # 2. Hai vector ngữ nghĩa
        origin = plane.c2p(0, 0)
        v_king_pt = plane.c2p(4.5, 3.5)
        v_queen_pt = plane.c2p(3.5, 4.2)

        arrow_king = NeonArrow(origin, v_king_pt, glow_color=ZenPalette.CYAN, stroke_width=3)
        arrow_queen = NeonArrow(origin, v_queen_pt, glow_color=ZenPalette.AMBER, stroke_width=3)

        label_king = Text("u (Vua)", font_size=20, color=ZenPalette.CYAN).next_to(v_king_pt, RIGHT)
        label_queen = Text("v (Nữ Hoàng)", font_size=20, color=ZenPalette.AMBER).next_to(v_queen_pt, UP)

        self.play(Create(arrow_king), Write(label_king), run_time=1.2)
        self.play(Create(arrow_queen), Write(label_queen), run_time=1.2)

        # 3. Góc kẹp và Phép chiếu (Projection Shadow)
        angle_arc = Angle(arrow_king, arrow_queen, radius=1.2, color=ZenPalette.GOLD)
        theta_label = MathTex(r"\theta", font_size=22, color=ZenPalette.GOLD).next_to(angle_arc, UR, buff=0.1)
        self.play(Create(angle_arc), Write(theta_label))

        # Hạ đường vuông góc từ v_queen xuống v_king (Hình chiếu)
        # Vector đơn vị king
        u_vec = np.array([4.5, 3.5, 0])
        v_vec = np.array([3.5, 4.2, 0])
        proj_val = np.dot(v_vec, u_vec) / np.dot(u_vec, u_vec)
        proj_coord = proj_val * u_vec
        proj_pt = plane.c2p(proj_coord[0], proj_coord[1])

        drop_line = DashedLine(v_queen_pt, proj_pt, color=ZenPalette.TEXT_DIM, stroke_width=2)
        proj_arrow = Arrow(origin, proj_pt, buff=0, color=ZenPalette.EMERALD, stroke_width=4)
        proj_label = Text("Hình chiếu: |v| cos θ", font_size=16, color=ZenPalette.EMERALD).next_to(proj_pt, DR, buff=0.15)

        self.play(Create(drop_line), GrowArrow(proj_arrow), Write(proj_label), run_time=1.5)

        # 4. Insight Card bên phải
        info_box = EquationBox(
            r"\cos(\theta) = \frac{\mathbf{u} \cdot \mathbf{v}}{\|\mathbf{u}\| \|\mathbf{v}\|}",
            title="Cosine Similarity",
            accent_color=ZenPalette.EMERALD,
        ).to_edge(RIGHT, buff=0.5).shift(UP * 0.5)

        sub_text = Text(
            "Khi hai vector cùng hướng:\ncos θ = 1 (Tương đồng tối đa)\nKhoảng cách góc biểu đạt ngữ nghĩa.",
            font_size=15, color=ZenPalette.TEXT_SECONDARY, line_spacing=1.3
        ).next_to(info_box, DOWN, buff=0.4)

        self.play(FadeIn(info_box), Write(sub_text), run_time=1.5)
        self.wait(2.0)
```

---

## Paradigm 3: Transformer Self-Attention Spotlight & Matrix Alignment

### Ý tưởng trực quan:
Giải mã bí mật trung tâm của LLM: Cơ chế Attention. Hiển thị các Token thành hàng chữ. Từ token Query `"ngân hàng"`, phát ra các chùm tia sáng (spotlight beams) quét qua các Token Key còn lại (`"sông"`, `"tiền"`, `"rút"`). Độ đậm nhạt của tia sáng thể hiện ma trận Softmax Attention Weight!

```python
from manim import *
from manim_production import ZenPalette, DiagramCard, GlowEffect

class SelfAttentionSpotlightScene(Scene):
    def construct(self):
        self.camera.background_color = ZenPalette.BG_DEEP

        title = Text("Cơ Chế Self-Attention: Ngọn Đèn Soi Rọi Ngữ Cảnh", 
                     font_size=26, color=ZenPalette.CYAN).to_edge(UP, buff=0.5)
        self.play(Write(title))

        # 1. Danh sách token đầu vào
        words = ["Tôi", "rút", "tiền", "ở", "ngân", "hàng", "bờ", "sông"]
        token_boxes = VGroup()
        for w in words:
            bg = RoundedRectangle(corner_radius=0.1, width=1.3, height=0.6,
                                  fill_color=ZenPalette.BG_CARD, fill_opacity=0.9,
                                  stroke_color=ZenPalette.BORDER_SUBTLE, stroke_width=1.5)
            t = Text(w, font_size=18, color=ZenPalette.TEXT_PRIMARY)
            t.move_to(bg.get_center())
            box = VGroup(bg, t)
            token_boxes.add(box)

        token_boxes.arrange(RIGHT, buff=0.25).shift(UP * 1.5)
        self.play(LaggedStart(*[FadeIn(b, shift=DOWN*0.3) for b in token_boxes], lag_ratio=0.1))

        # 2. Query Token đang xét: "ngân hàng" (Token 4 & 5)
        query_idx = 4
        target_token = token_boxes[query_idx]
        highlight_rect = RoundedRectangle(
            corner_radius=0.1, width=1.35, height=0.65,
            stroke_color=ZenPalette.AMBER, stroke_width=3
        ).move_to(target_token.get_center())

        q_label = Text("Query (Q)", font_size=15, color=ZenPalette.AMBER).next_to(highlight_rect, UP, buff=0.2)
        self.play(Create(highlight_rect), Write(q_label))

        # 3. Chùm tia Attention (Beams) tỏa ra với trọng số Softmax
        # "ngân hàng" gắn với "tiền" (cao), "rút" (cao), "sông" (ngữ cảnh disambiguation)
        weights = [0.05, 0.35, 0.40, 0.05, 0.0, 0.15, 0.05, 0.02]
        beams = VGroup()

        q_center = target_token.get_bottom()

        for idx, (box, w) in enumerate(zip(token_boxes, weights)):
            if idx == query_idx: continue
            k_center = box.get_bottom() + DOWN * 2.0
            line = Line(q_center, k_center, color=ZenPalette.CYAN, stroke_width=w * 15, stroke_opacity=max(0.15, w * 1.2))
            score = Text(f"{int(w*100)}%", font_size=13, color=ZenPalette.CYAN if w > 0.1 else ZenPalette.TEXT_DIM)
            score.next_to(k_center, DOWN, buff=0.15)
            beams.add(VGroup(line, score))

        self.play(LaggedStart(*[Create(b[0]) for b in beams], lag_ratio=0.08),
                  LaggedStart(*[Write(b[1]) for b in beams], lag_ratio=0.08), run_time=2.0)

        # 4. Công thức Attention Formula Card
        formula_card = DiagramCard(
            content=MathTex(r"\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right)V", font_size=24),
            title="Scaled Dot-Product Attention",
            accent_color=ZenPalette.CYAN,
            width=6.8, height=1.8
        ).to_edge(DOWN, buff=0.4)

        self.play(FadeIn(formula_card, shift=UP*0.3))
        self.wait(2.0)
```

---

## Paradigm 4: Deep Neural Network Forward Pulse & Backprop Lightning

### Ý tưởng trực quan:
Mạng Neural không phải là các vòng tròn tĩnh!
- **Forward Pass**: Luồng xung điện (light pulse) màu xanh Cyan chạy từ Input qua các tầng Hidden Layer đến Output.
- **Loss Computation**: Đèn đỏ báo động tại nút Output.
- **Backward Pass**: Tia chớp sét màu Coral/Đỏ giật lùi từ Output về các tầng trước, cập nhật trọng số và làm các nút rung nhẹ (Indicate).

```python
from manim import *
from manim_production import ZenPalette, NeuralNetworkDiagram, EurekaFlash

class NeuralNetworkFlowScene(Scene):
    def construct(self):
        self.camera.background_color = ZenPalette.BG_DEEP

        title = Text("Deep Learning: Nhịp Đập Forward & Tia Sét Backpropagation",
                     font_size=24, color=ZenPalette.TEXT_PRIMARY).to_edge(UP, buff=0.4)
        self.play(Write(title))

        # 1. Vẽ mạng Nơ-ron 4 tầng
        nn = NeuralNetworkDiagram(
            layers=[3, 5, 5, 2],
            layer_spacing=2.5,
            node_radius=0.18,
            accent_color=ZenPalette.CYAN,
            edge_opacity=0.25
        ).shift(DOWN * 0.2)

        self.play(Create(nn), run_time=2.0)
        self.wait(0.5)

        # 2. Forward Pulse (Tia sáng chạy xuôi)
        forward_tag = Text("FORWARD PASS: Lan truyền tín hiệu", font_size=18, color=ZenPalette.CYAN).to_corner(UL)
        self.play(Write(forward_tag))

        # Hiệu ứng sáng lần lượt các tầng
        for l_idx, layer in enumerate(nn.nodes):
            self.play(
                *[node.animate.set_fill(ZenPalette.CYAN, opacity=0.9).set_stroke(ZenPalette.NEON_CORE, width=3) for node in layer],
                run_time=0.4
            )
            # Reset nhẹ opacity
            self.play(
                *[node.animate.set_fill(ZenPalette.BG_CARD, opacity=0.9).set_stroke(ZenPalette.CYAN, width=1.5) for node in layer],
                run_time=0.2
            )

        # 3. Tính Loss tại Output
        loss_text = MathTex(r"\mathcal{L}_{\text{BCE}} = -\sum y \log(\hat{y})", font_size=22, color=ZenPalette.CORAL)
        loss_text.next_to(nn.nodes[-1], RIGHT, buff=0.4)
        flash_output = EurekaFlash(center=nn.nodes[-1].get_center(), color=ZenPalette.CORAL, radius=1.2)

        self.play(Create(flash_output), Write(loss_text), run_time=0.8)
        self.wait(0.5)

        # 4. Backward Pass (Tia sét giật ngược)
        self.play(FadeOut(forward_tag))
        backward_tag = Text("BACKPROPAGATION: Dẫn truyền sai số dL/dw", font_size=18, color=ZenPalette.CORAL).to_corner(UL)
        self.play(Write(backward_tag))

        for l_idx in reversed(range(len(nn.nodes))):
            layer = nn.nodes[l_idx]
            self.play(
                *[node.animate.set_stroke(ZenPalette.CORAL, width=3.5).set_fill(ZenPalette.CORAL, opacity=0.5) for node in layer],
                run_time=0.35
            )
            self.play(
                *[node.animate.set_stroke(ZenPalette.BORDER_SUBTLE, width=1.5).set_fill(ZenPalette.BG_CARD, opacity=0.9) for node in layer],
                run_time=0.15
            )

        self.wait(1.5)
```

---

## Paradigm 5: 3D Tensor Slicing & Normalization (BatchNorm vs LayerNorm)

### Ý tưởng trực quan:
Vấn đề kinh điển của Kỹ sư AI: Khối Tensor 3D kích thước $(N, C, L)$ (Batch, Channels, Length).
- **Batch Normalization**: Cắt lát dọc xuyên qua chiều Batch $N$ (tính $\mu, \sigma$ cho từng Feature).
- **Layer Normalization**: Cắt lát ngang qua các Channels và Length cho từng mẫu riêng biệt.
So sánh trực diện trên 2 tấm Card A/B bằng `ComparisonPanel`.

```python
from manim import *
from manim_production import ZenPalette, ComparisonPanel, TensorDiagram

class NormalizationComparisonScene(Scene):
    def construct(self):
        self.camera.background_color = ZenPalette.BG_DEEP

        title = Text("BatchNorm vs LayerNorm: Bản Chất Hình Học Của Sự Chuẩn Hóa",
                     font_size=26, color=ZenPalette.TEXT_PRIMARY).to_edge(UP, buff=0.4)
        self.play(Write(title))

        # Mô phỏng lát cắt bằng TensorDiagram
        bn_tensor = TensorDiagram(
            shape=(4, 5),
            dim_labels=["Batch (N)", "Feature (D)"],
            highlight_slice="col",  # Chuẩn hóa dọc theo cột
            highlight_index=2,
            accent_color=ZenPalette.CYAN
        ).scale(0.8)

        ln_tensor = TensorDiagram(
            shape=(4, 5),
            dim_labels=["Batch (N)", "Feature (D)"],
            highlight_slice="row",  # Chuẩn hóa ngang theo hàng
            highlight_index=1,
            accent_color=ZenPalette.AMBER
        ).scale(0.8)

        # Ghép vào ComparisonPanel
        panel = ComparisonPanel(
            left_title="Batch Normalization (CNN / Vision)",
            left_content=bn_tensor,
            right_title="Layer Normalization (Transformer / LLM)",
            right_content=ln_tensor,
            panel_width=6.4, panel_height=4.6,
            left_color=ZenPalette.CYAN, right_color=ZenPalette.AMBER
        ).shift(DOWN * 0.3)

        self.play(FadeIn(panel, shift=UP*0.3), run_time=1.5)

        # Chú thích sâu sắc cho Kỹ sư
        bn_note = Text("Tính thống kê trên toàn Batch\nPhụ thuộc Batch Size (Không hợp với Sequence dài)",
                       font_size=13, color=ZenPalette.TEXT_SECONDARY, line_spacing=1.3).next_to(bn_tensor, DOWN, buff=0.3)
        ln_note = Text("Tính thống kê độc lập cho từng Sample\nBất biến với Batch Size (Cứu tinh của Attention)",
                       font_size=13, color=ZenPalette.TEXT_SECONDARY, line_spacing=1.3).next_to(ln_tensor, DOWN, buff=0.3)

        self.play(Write(bn_note), Write(ln_note), run_time=1.2)
        self.wait(2.5)
```

---

## Paradigm 6: Galton Board & Central Limit Theorem (Hỗn loạn ➜ Chuông Gauss)

### Ý tưởng trực quan:
Hàng trăm hạt bi rơi ngẫu nhiên qua các chốt chông hình tam giác. Mỗi hạt rẽ trái/phải ngẫu nhiên với xác suất $50\%$. Nhưng khi tích lũy xuống đáy, chúng xếp thành một đường cong hình chuông hoàn hảo $\mathcal{N}(0, 1)$. Một bài học triết lý sâu sắc: *Sự hỗn loạn ở cấp độ vi mô tạo nên trật tự tuyệt đối ở cấp độ vĩ mô.*

```python
from manim import *
import numpy as np
from manim_production import ZenPalette, ProbabilityDistribution, EquationBox

class GaltonBoardCLTScene(Scene):
    def construct(self):
        self.camera.background_color = ZenPalette.BG_DEEP

        title = Text("Định Lý Giới Hạn Trung Tâm (CLT): Trật Tự Từ Hỗn Loạn",
                     font_size=26, color=ZenPalette.TEXT_PRIMARY).to_edge(UP, buff=0.4)
        self.play(Write(title))

        # 1. Vẽ các chốt chông (Pegs)
        pegs = VGroup()
        rows = 6
        for r in range(rows):
            for c in range(r + 1):
                x = (c - r / 2.0) * 0.7
                y = 1.8 - r * 0.5
                dot = Dot(point=np.array([x - 2.5, y, 0]), radius=0.06, color=ZenPalette.TEXT_DIM)
                pegs.add(dot)

        self.play(LaggedStart(*[FadeIn(p, scale=0.5) for p in pegs], lag_ratio=0.02), run_time=1.0)

        # 2. Histogram tích lũy ở đáy
        bins = [1, 5, 10, 10, 5, 1]  # Tần số nhị thức
        bars = VGroup()
        for i, count in enumerate(bins):
            x = (i - len(bins)/2.0 + 0.5) * 0.7 - 2.5
            h = count * 0.18
            rect = Rectangle(width=0.55, height=h, fill_color=ZenPalette.AMBER,
                             fill_opacity=0.8, stroke_color=ZenPalette.GOLD, stroke_width=1.5)
            rect.move_to(np.array([x, -1.8 + h/2.0, 0]))
            bars.add(rect)

        self.play(LaggedStart(*[GrowFromEdge(b, DOWN) for b in bars], lag_ratio=0.1), run_time=1.5)

        # 3. Đường cong Gauss mềm mại bao bọc lấy các cột
        def gaussian_pdf(x):
            return 2.2 * np.exp(-0.5 * (x / 1.1)**2)

        axes = Axes(
            x_range=[-3, 3, 1], y_range=[0, 2.5, 1],
            x_length=4.5, y_length=2.8,
            axis_config={"stroke_opacity": 0}
        ).move_to(bars.get_center() + UP * 0.3)

        curve = axes.plot(gaussian_pdf, color=ZenPalette.CYAN, stroke_width=3.5)
        self.play(Create(curve), run_time=1.5)

        # 4. Thẻ phương trình bên phải
        eq_card = EquationBox(
            r"\frac{\bar{X}_n - \mu}{\sigma / \sqrt{n}} \xrightarrow{d} \mathcal{N}(0, 1)",
            title="Central Limit Theorem",
            accent_color=ZenPalette.CYAN,
        ).to_edge(RIGHT, buff=0.8).shift(UP * 0.2)

        lesson = Text(
            "Bất kể phân phối gốc là gì,\ntổng của vô số biến cố ngẫu nhiên\nđều hội tụ về chiếc chuông Gauss.",
            font_size=15, color=ZenPalette.TEXT_SECONDARY, line_spacing=1.3
        ).next_to(eq_card, DOWN, buff=0.4)

        self.play(FadeIn(eq_card), Write(lesson), run_time=1.5)
        self.wait(2.5)
```

---

## Paradigm 7: Simpson's Paradox (Nghịch lý dữ liệu & Biến số ẩn)

### Ý tưởng trực quan:
Khi vẽ một đường hồi quy tuyến tính trên toàn bộ dữ liệu, đường dốc lao xuống (xu hướng tiêu cực). Nhưng khi phân tách dữ liệu thành 2 cụm (Cluster A và Cluster B do có biến số ẩn), từng cụm riêng lẻ lại có đường hồi quy dốc đi lên!

```python
from manim import *
import numpy as np
from manim_production import ZenPalette, DiagramCard, NeonArrow

class SimpsonsParadoxScene(Scene):
    def construct(self):
        self.camera.background_color = ZenPalette.BG_DEEP

        title = Text("Nghịch Lý Simpson: Khi Số Liệu Nói Dối Hợp Pháp",
                     font_size=26, color=ZenPalette.CORAL).to_edge(UP, buff=0.4)
        self.play(Write(title))

        # Trục tọa độ
        axes = Axes(
            x_range=[0, 10, 2], y_range=[0, 10, 2],
            x_length=6, y_length=4.5,
            axis_config={"color": ZenPalette.BORDER_SUBTLE}
        ).shift(LEFT * 2 + DOWN * 0.4)
        x_lbl = Text("Liều lượng", font_size=14, color=ZenPalette.TEXT_DIM).next_to(axes.x_axis, DOWN)
        y_lbl = Text("Tỷ lệ hồi phục", font_size=14, color=ZenPalette.TEXT_DIM).next_to(axes.y_axis, LEFT).rotate(PI/2)

        self.play(Create(axes), Write(x_lbl), Write(y_lbl))

        # Cụm 1 (Bệnh nhẹ, liều thấp, hồi phục cao)
        c1_pts = np.array([[2, 6], [2.5, 6.8], [3, 7.2], [3.5, 8.0], [4, 8.5]])
        # Cụm 2 (Bệnh nặng, liều cao, hồi phục thấp hơn)
        c2_pts = np.array([[6, 2], [6.5, 2.8], [7, 3.2], [7.5, 4.0], [8, 4.5]])

        # Ban đầu vẽ các điểm cùng màu xám (chưa phân loại)
        dots = VGroup()
        for pt in np.vstack([c1_pts, c2_pts]):
            dots.add(Dot(axes.c2p(pt[0], pt[1]), radius=0.09, color=ZenPalette.TEXT_SECONDARY))

        self.play(LaggedStart(*[FadeIn(d, scale=0.5) for d in dots], lag_ratio=0.05))

        # Đường xu hướng chung: DỐC XUỐNG
        global_line = Line(axes.c2p(1.5, 7.8), axes.c2p(8.5, 2.5), color=ZenPalette.CORAL, stroke_width=4)
        global_lbl = Text("Toàn thể: Dốc xuống (-)", font_size=16, color=ZenPalette.CORAL).next_to(global_line, UR, buff=-0.5)

        self.play(Create(global_line), Write(global_lbl), run_time=1.5)
        self.wait(1.0)

        # TIẾT LỘ BIẾN SỐ ẨN (BÓC TÁCH NHÓM)
        dots_c1 = [dots[i] for i in range(len(c1_pts))]
        dots_c2 = [dots[i] for i in range(len(c1_pts), len(dots))]

        self.play(
            *[d.animate.set_color(ZenPalette.CYAN) for d in dots_c1],
            *[d.animate.set_color(ZenPalette.AMBER) for d in dots_c2],
            FadeOut(global_line), FadeOut(global_lbl),
            run_time=1.2
        )

        # Hai đường xu hướng riêng rẽ: CÙNG DỐC LÊN (+)
        line_c1 = Line(axes.c2p(1.8, 5.8), axes.c2p(4.2, 8.8), color=ZenPalette.CYAN, stroke_width=3.5)
        line_c2 = Line(axes.c2p(5.8, 1.8), axes.c2p(8.2, 4.8), color=ZenPalette.AMBER, stroke_width=3.5)

        c1_lbl = Text("Nhóm Nhẹ (+)", font_size=14, color=ZenPalette.CYAN).next_to(line_c1, LEFT, buff=0.1)
        c2_lbl = Text("Nhóm Nặng (+)", font_size=14, color=ZenPalette.AMBER).next_to(line_c2, RIGHT, buff=0.1)

        self.play(Create(line_c1), Create(line_c2), Write(c1_lbl), Write(c2_lbl), run_time=1.5)

        # Card kết luận bài học nghề
        card = DiagramCard(
            content=Text(
                "Biến số ẩn (Confounder):\n'Mức độ bệnh ban đầu'\nNgười bệnh nặng dùng liều cao hơn\nnhưng tự nhiên có tỷ lệ khỏi thấp hơn.",
                font_size=14, color=ZenPalette.TEXT_PRIMARY, line_spacing=1.3
            ),
            title="Cảnh Giác Kỹ Sư Dữ Liệu",
            accent_color=ZenPalette.AMBER,
            width=4.8, height=2.2
        ).to_edge(RIGHT, buff=0.4).shift(DOWN * 0.2)

        self.play(FadeIn(card, shift=LEFT*0.3))
        self.wait(2.5)
```

---

## Paradigm 8: Shannon Entropy & Latent Information Compression

### Ý tưởng trực quan:
Thông tin đo bằng độ bất ngờ!
- Một sự kiện chắc chắn xảy ra ($P=1$) ➜ Bất ngờ bằng $0$ ➜ Entropy bằng $0$.
- Một sự kiện cực kỳ khó đoán ➜ Bất ngờ cực đại ➜ Lượng thông tin bùng nổ.
Mô phỏng đồ thị hàm $- \log_2(P)$ cùng phễu nén Autoencoder (Latent Space Bottleneck).

```python
from manim import *
import numpy as np
from manim_production import ZenPalette, EquationBox, DiagramCard

class ShannonEntropyScene(Scene):
    def construct(self):
        self.camera.background_color = ZenPalette.BG_DEEP

        title = Text("Lý Thuyết Thông Tin Shannon & Sự Nén Tri Thức Của AI",
                     font_size=24, color=ZenPalette.CYAN).to_edge(UP, buff=0.4)
        self.play(Write(title))

        # Đồ thị Hàm Bất Ngờ I(P) = -log2(p)
        axes = Axes(
            x_range=[0, 1, 0.2], y_range=[0, 5, 1],
            x_length=5.5, y_length=4.0,
            axis_config={"color": ZenPalette.BORDER_SUBTLE}
        ).shift(LEFT * 2.5 + DOWN * 0.3)

        x_lbl = Text("Xác suất P(x)", font_size=14, color=ZenPalette.TEXT_DIM).next_to(axes.x_axis, DOWN)
        y_lbl = Text("Lượng tin I(x) [Bits]", font_size=14, color=ZenPalette.TEXT_DIM).next_to(axes.y_axis, LEFT).rotate(PI/2)

        def info_func(p):
            p_safe = max(0.03, p)
            return -np.log2(p_safe)

        curve = axes.plot(info_func, x_range=[0.04, 1.0], color=ZenPalette.AMBER, stroke_width=3.5)

        self.play(Create(axes), Write(x_lbl), Write(y_lbl))
        self.play(Create(curve), run_time=1.5)

        # Hai ví dụ trực giác
        dot_sure = Dot(axes.c2p(1.0, 0), radius=0.1, color=ZenPalette.EMERALD)
        lbl_sure = Text("P=1: 'Mặt trời mọc ở hướng Đông'\n(Entropy = 0 bit)", font_size=13, color=ZenPalette.EMERALD).next_to(dot_sure, UR, buff=0.1)

        dot_rare = Dot(axes.c2p(0.06, info_func(0.06)), radius=0.1, color=ZenPalette.CORAL)
        lbl_rare = Text("P=0.06: 'Hệ thống Production sập!'\n(Entropy cực đại)", font_size=13, color=ZenPalette.CORAL).next_to(dot_rare, UR, buff=0.1)

        self.play(FadeIn(dot_sure), Write(lbl_sure))
        self.play(FadeIn(dot_rare), Write(lbl_rare))

        # Formula Card
        card = EquationBox(
            r"H(X) = -\sum_{x} P(x) \log_2 P(x)",
            title="Shannon Entropy",
            accent_color=ZenPalette.CYAN,
        ).to_edge(RIGHT, buff=0.6).shift(UP * 0.5)

        ai_takeaway = DiagramCard(
            content=Text(
                "Mục tiêu huấn luyện LLM:\nTối ưu hàm Cross-Entropy để cỗ máy\nkhông còn bị bất ngờ trước ngôn ngữ con người.",
                font_size=14, color=ZenPalette.TEXT_SECONDARY, line_spacing=1.3
            ),
            title="Ứng Dụng Trong LLM",
            accent_color=ZenPalette.VIOLET,
            width=5.0, height=2.0
        ).next_to(card, DOWN, buff=0.4)

        self.play(FadeIn(card), FadeIn(ai_takeaway), run_time=1.5)
        self.wait(2.5)
```

---

## Paradigm 9: Step-by-Step TransformMatchingTex Proof with Invariant Glow

### Ý tưởng trực quan:
Chuyển hóa toán học từng bước không gây sốc cho mắt người xem! Từng thành phần của biểu thức di chuyển mượt mà sang vị trí mới (`TransformMatchingTex`). Khi chạm đến kết quả bất biến, một khung chữ nhật sáng rực viền neon bao bọc kèm hiệu ứng hào quang.

```python
from manim import *
from manim_production import ZenPalette, EquationBox, GlowEffect

class StepByStepProofScene(Scene):
    def construct(self):
        self.camera.background_color = ZenPalette.BG_DEEP

        title = Text("Chứng Minh Bước-Từng-Bước: Tinh Hoa Biến Đổi Đại Số",
                     font_size=24, color=ZenPalette.TEXT_PRIMARY).to_edge(UP, buff=0.5)
        self.play(Write(title))

        # Bước 1: Công thức Bayes khởi nguồn
        eq1 = MathTex(
            r"P(A \cap B)", r"=", r"P(A|B)", r"P(B)",
            font_size=36, color=ZenPalette.TEXT_PRIMARY
        ).shift(UP * 1.5)

        # Bước 2: Hoán vị đối xứng
        eq2 = MathTex(
            r"P(B \cap A)", r"=", r"P(B|A)", r"P(A)",
            font_size=36, color=ZenPalette.TEXT_PRIMARY
        ).shift(UP * 0.3)

        self.play(Write(eq1), run_time=1.2)
        self.play(Write(eq2), run_time=1.2)
        self.wait(0.5)

        note = Text("Vì P(A ∩ B) = P(B ∩ A), ta đồng nhất hai vế phải:",
                    font_size=16, color=ZenPalette.TEXT_SECONDARY).next_to(eq2, DOWN, buff=0.4)
        self.play(Write(note))

        # Bước 3: Đồng nhất hai vế
        eq3 = MathTex(
            r"P(A|B)", r"P(B)", r"=", r"P(B|A)", r"P(A)",
            font_size=36, color=ZenPalette.AMBER
        ).shift(DOWN * 1.0)

        self.play(Write(eq3), run_time=1.5)
        self.wait(0.8)

        # Bước 4: Chia hai vế cho P(B) để ra Định Lý Bayes (Biến đổi mượt)
        final_eq = MathTex(
            r"P(A|B)", r"=", r"\frac{P(B|A) P(A)}{P(B)}",
            font_size=40, color=ZenPalette.CYAN
        ).shift(DOWN * 2.2)

        self.play(
            FadeOut(note),
            TransformMatchingTex(eq3.copy(), final_eq),
            run_time=1.8
        )

        # Đóng khung phát sáng cho chân lý bất biến
        box = SurroundingRectangle(final_eq, color=ZenPalette.CYAN, buff=0.25, corner_radius=0.1)
        glow = GlowEffect(box, color=ZenPalette.CYAN, num_layers=4, max_opacity=0.5)

        self.play(Create(box), FadeIn(glow), run_time=1.2)
        self.wait(2.5)
```

---

## Paradigm 10: Event-Driven Agentic Pipeline & Self-Healing Queue

### Ý tưởng trực quan:
Dành cho các chủ đề Kỹ thuật Hệ thống & AI Agents:
Hàng đợi tin nhắn (Message Queue / Kafka / Redis) nhận task từ User. Các Worker pods màu Cyan bốc task xử lý. Khi một worker bị lỗi quá tải (đổi màu Đỏ Ruby), hệ thống Retry & Circuit Breaker tự động chuyển giao task sang Fallback Node kèm tia sáng hồi phục.

```python
from manim import *
from manim_production import ZenPalette, FlowChart, AnimatedCounter, EurekaFlash

class AgenticPipelineScene(Scene):
    def construct(self):
        self.camera.background_color = ZenPalette.BG_DEEP

        title = Text("Kiến Trúc AI Agent: Event-Driven & Khả Năng Tự Phục Hồi",
                     font_size=24, color=ZenPalette.TEXT_PRIMARY).to_edge(UP, buff=0.4)
        self.play(Write(title))

        # 1. Pipeline FlowChart
        flow = FlowChart(
            nodes=[
                {"label": "User Task", "color": ZenPalette.TEXT_PRIMARY},
                {"label": "Queue (Redis)", "color": ZenPalette.AMBER},
                {"label": "Router Agent", "color": ZenPalette.CYAN},
                {"label": "Worker Pool", "color": ZenPalette.EMERALD},
            ],
            layout="horizontal",
            box_width=2.2, box_height=1.0,
            spacing=1.0
        ).shift(UP * 0.5)

        self.play(Create(flow), run_time=2.0)

        # 2. Counter trạng thái thông lượng (Throughput)
        tracker, counter_grp, anim_counter = AnimatedCounter(
            start=0, end=1420, suffix=" req/s",
            font_size=24, color=ZenPalette.CYAN, label="Throughput"
        )
        counter_grp.to_corner(DL, buff=0.8)
        self.add(counter_grp)
        self.play(anim_counter(duration=2.0))

        # 3. Sự cố mô phỏng: Worker Pool quá tải
        worker_box = flow.boxes[3]
        self.play(
            worker_box.animate.set_fill(ZenPalette.CORAL, opacity=0.8).set_stroke(ZenPalette.RUBY_RED, width=3),
            run_time=0.8
        )
        err_msg = Text("RATE LIMIT 429 EXCEEDED", font_size=14, color=ZenPalette.RUBY_RED).next_to(worker_box, DOWN, buff=0.2)
        self.play(Write(err_msg))
        self.wait(0.5)

        # 4. Tự phục hồi: Circuit Breaker kích hoạt Fallback Pod
        fallback_box = RoundedRectangle(
            corner_radius=0.15, width=2.2, height=1.0,
            fill_color=ZenPalette.BG_CARD, fill_opacity=0.9,
            stroke_color=ZenPalette.AMBER, stroke_width=2
        ).next_to(worker_box, DOWN, buff=0.8)
        fallback_lbl = Text("Fallback Model", font_size=15, color=ZenPalette.AMBER).move_to(fallback_box)
        fb_grp = VGroup(fallback_box, fallback_lbl)

        flash = EurekaFlash(center=fallback_box.get_center(), color=ZenPalette.AMBER, radius=1.5)

        self.play(
            FadeOut(err_msg),
            FadeIn(fb_grp, shift=UP*0.3),
            Create(flash),
            worker_box.animate.set_fill(ZenPalette.BG_CARD, opacity=0.8).set_stroke(ZenPalette.EMERALD, width=2),
            run_time=1.5
        )

        resolved_msg = Text("Tự động định tuyến sang Fallback Model thành công", font_size=15, color=ZenPalette.EMERALD).to_edge(DOWN, buff=0.5)
        self.play(Write(resolved_msg))
        self.wait(2.0)
```
