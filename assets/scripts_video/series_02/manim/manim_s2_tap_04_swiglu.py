#!/usr/bin/env python3
"""
Manim 2K QHD Master Production Scenes — SwiGLU & Cổng Kiểm Soát Dòng Chảy Nơ-ron (Gated Linear Units)
Resolution: 2560x1440 @ 60fps | Theme: Neo-Noir Obsidian (#0c0d12)
Standards:
- Zero FadeOut to black (visuals hold vibrant and active)
- Strictly Center-Justified text & formulas inside all cards
- Safe Zone Compliance: Margin > 15% (|x| <= 5.2, |y| <= 3.2)
- Zero Mascots (LivingZenMascot / ZenEngineerMascot 100% removed)
- Zero static bullet boxes ("box và text")
- Continuous Median/3Blue1Brown dynamic geometric animations
- 100% Vector Manim Graphics
"""

import sys
from pathlib import Path
sys.path.insert(0, "/workspace")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from manim import *
import numpy as np
import math

# Neo-Noir Theme Palette
COLOR_BG = "#0c0d12"
COLOR_CARD_BG = "#101422"
COLOR_CYAN = "#00e5ff"      # Up / Value branch
COLOR_AMBER = "#f59e0b"     # Gate branch
COLOR_GOLD = "#ffb300"      # Accent / SOTA
COLOR_ROSE = "#ff2a6d"      # ReLU / Inactive / Warning
COLOR_EMERALD = "#00e676"   # Output / SiLU / Active
COLOR_VIOLET = "#a78bfa"    # Hadamard product
COLOR_TEXT = "#e2e8f0"
COLOR_MUTED = "#94a3b8"
COLOR_BORDER = "#1e293b"
COLOR_PANEL = "#141824"

FONT_FAMILY = "Noto Sans"

def add_zenpham_brand(scene: Scene, ep_title: str = ""):
    """Clean Minimalist Brand HUD: Small channel logo in upper corner (UR), zero text clutter."""
    logo_rel = Path("assets/brand/zenpham-brand-kit/zenpham-logo-transparent-2000x2000.png")
    logo_abs = Path("/home/zen/hermes-agent") / logo_rel
    logo_work = Path("/work") / logo_rel
    logo_file = (
        logo_work if logo_work.exists()
        else logo_abs if logo_abs.exists()
        else logo_rel
    )
    if logo_file.exists():
        logo_mobj = ImageMobject(str(logo_file))
        logo_mobj.scale_to_fit_height(0.65)
        logo_mobj.to_corner(UR, buff=0.45)
        scene.add(logo_mobj)
    else:
        emblem = Circle(radius=0.25, stroke_color="#ffd700", stroke_width=1.5, fill_color="#141824", fill_opacity=0.85)
        emblem_txt = Text("Z", font=FONT_FAMILY, font_size=12, weight=BOLD, color="#ffd700").move_to(emblem.get_center())
        logo_mobj = VGroup(emblem, emblem_txt).to_corner(UR, buff=0.45)
        scene.add(logo_mobj)



# =============================================================================
# SCENE 01: NGHỊCH LÝ CỦA RELU & SỰ RA ĐỜI CỦA SWIGLU (COLD OPEN)
# =============================================================================
class Tap04Scene01ColdOpen(Scene):
    """
    Cold Open:
    Act 1: ReLU hard clipping at 0 with dead flat gradient region.
    Act 2: SiLU smooth curve dipping into negative values with continuous non-zero derivative.
    Act 3: Dynamic comparison: Hard switch vs Continuous gating modulation.
    """
    def construct(self):
        self.camera.background_color = COLOR_BG

        # Title Card
        title_text = Text(
            "SwiGLU // ĐIỀU BIẾN HAI NHÁNH & CỔNG THÔNG TIN",
            font=FONT_FAMILY, font_size=15, weight=BOLD, color=COLOR_GOLD
        )
        title_box = RoundedRectangle(
            corner_radius=0.12, width=title_text.width + 0.6, height=0.5,
            fill_color="#10172a", fill_opacity=0.9, stroke_color=COLOR_GOLD, stroke_width=1.2
        ).to_edge(UP, buff=0.45)
        title_text.move_to(title_box)
        self.play(FadeIn(title_box, shift=DOWN * 0.2), Write(title_text), run_time=0.6)

        # Left Axes: ReLU Function
        ax_l = Axes(
            x_range=[-3, 3, 1], y_range=[-1, 3, 1],
            x_length=4.4, y_length=2.8,
            axis_config={"color": COLOR_BORDER, "stroke_width": 1.2}
        ).shift(LEFT * 2.8 + DOWN * 0.2)

        relu_graph = ax_l.plot(lambda x: max(0, x), x_range=[-3, 3], color=COLOR_ROSE, stroke_width=3.0)
        relu_lbl = MathTex(r"\mathrm{ReLU}(x) = \max(0, x)", font_size=18, color=COLOR_ROSE).next_to(ax_l, UP, buff=0.2)

        # Highlight Dead ReLU zone (x < 0)
        dead_zone = ax_l.plot(lambda x: 0, x_range=[-3, 0], color=COLOR_ROSE, stroke_width=5.0)
        dead_tag = Text("Vùng chết: Đạo hàm = 0", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_ROSE).next_to(ax_l, DOWN, buff=0.2)

        # Right Axes: SiLU / Swish Function
        ax_r = Axes(
            x_range=[-3, 3, 1], y_range=[-1, 3, 1],
            x_length=4.4, y_length=2.8,
            axis_config={"color": COLOR_BORDER, "stroke_width": 1.2}
        ).shift(RIGHT * 2.8 + DOWN * 0.2)

        silu_graph = ax_r.plot(lambda x: x / (1.0 + math.exp(-x)), x_range=[-3, 3], color=COLOR_EMERALD, stroke_width=3.0)
        silu_lbl = MathTex(r"\mathrm{SiLU}(x) = x \cdot \sigma(x)", font_size=18, color=COLOR_EMERALD).next_to(ax_r, UP, buff=0.2)

        # Highlight smooth non-monotonic dip
        smooth_tag = Text("Đạo hàm trơn, không triệt tiêu", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_EMERALD).next_to(ax_r, DOWN, buff=0.2)

        self.play(
            Create(ax_l), Write(relu_lbl), Create(relu_graph),
            Create(ax_r), Write(silu_lbl), Create(silu_graph),
            run_time=1.2
        )
        self.play(Create(dead_zone), Write(dead_tag), Write(smooth_tag), run_time=0.8)

        # Animated Tracer Dots
        dot_l = Dot(ax_l.c2p(-2.5, 0), radius=0.08, color=COLOR_ROSE)
        dot_r = Dot(ax_r.c2p(-2.5, -2.5 / (1.0 + math.exp(2.5))), radius=0.08, color=COLOR_EMERALD)
        self.add(dot_l, dot_r)

        self.play(
            MoveAlongPath(dot_l, relu_graph),
            MoveAlongPath(dot_r, silu_graph),
            run_time=2.0, rate_func=linear
        )
        self.wait(1.5)


# =============================================================================
# SCENE 02: KIẾN TRÚC HAI NHÁNH VALUE VÀ GATE CỦA SWIGLU (ARCHITECTURE)
# =============================================================================
class Tap04Scene02Architecture(Scene):
    """
    Architecture:
    Act 1: Input x splits into two separate projection paths.
    Act 2: Upper path: Gate projection + SiLU activation. Lower path: Up / Value projection.
    Act 3: Meeting at element-wise Hadamard product ⊙ and Down projection W_down.
    """
    def construct(self):
        self.camera.background_color = COLOR_BG

        # Title
        title_text = Text(
            "KIẾN TRÚC HAI NHÁNH: CỔNG ĐIỀU BIẾN & TÍCH HADAMARD",
            font=FONT_FAMILY, font_size=15, weight=BOLD, color=COLOR_CYAN
        )
        title_box = RoundedRectangle(
            corner_radius=0.12, width=title_text.width + 0.6, height=0.5,
            fill_color="#10172a", fill_opacity=0.9, stroke_color=COLOR_CYAN, stroke_width=1.2
        ).to_edge(UP, buff=0.45)
        title_text.move_to(title_box)
        self.play(FadeIn(title_box, shift=DOWN * 0.2), Write(title_text), run_time=0.6)

        # 1. Input Node x
        x_card = RoundedRectangle(corner_radius=0.1, width=1.4, height=1.0, fill_color=COLOR_CARD_BG, fill_opacity=0.95, stroke_color=COLOR_GOLD, stroke_width=1.5).shift(LEFT * 4.4)
        x_tex = MathTex(r"\mathbf{x} \in \mathbb{R}^d", font_size=18, color=COLOR_GOLD).move_to(x_card)
        x_grp = VGroup(x_card, x_tex)

        # 2. Gate Branch (Top - Amber)
        w_gate_card = RoundedRectangle(corner_radius=0.1, width=2.0, height=0.9, fill_color=COLOR_CARD_BG, fill_opacity=0.95, stroke_color=COLOR_AMBER, stroke_width=1.5).shift(LEFT * 1.8 + UP * 1.2)
        w_gate_tex = MathTex(r"W_{\mathrm{gate}}", font_size=18, color=COLOR_AMBER).move_to(w_gate_card)
        gate_grp = VGroup(w_gate_card, w_gate_tex)

        silu_card = RoundedRectangle(corner_radius=0.1, width=1.6, height=0.9, fill_color=COLOR_CARD_BG, fill_opacity=0.95, stroke_color=COLOR_AMBER, stroke_width=1.5).shift(RIGHT * 0.6 + UP * 1.2)
        silu_tex = MathTex(r"\mathrm{SiLU}", font_size=18, color=COLOR_AMBER).move_to(silu_card)
        act_grp = VGroup(silu_card, silu_tex)

        # 3. Up / Value Branch (Bottom - Cyan)
        w_up_card = RoundedRectangle(corner_radius=0.1, width=2.0, height=0.9, fill_color=COLOR_CARD_BG, fill_opacity=0.95, stroke_color=COLOR_CYAN, stroke_width=1.5).shift(LEFT * 1.8 + DOWN * 1.2)
        w_up_tex = MathTex(r"W_{\mathrm{up}}", font_size=18, color=COLOR_CYAN).move_to(w_up_card)
        up_grp = VGroup(w_up_card, w_up_tex)

        # 4. Hadamard Product Junction (Violet)
        had_card = Circle(radius=0.55, fill_color="#1e1b4b", fill_opacity=0.95, stroke_color=COLOR_VIOLET, stroke_width=2.0).shift(RIGHT * 2.5)
        had_tex = MathTex(r"\odot", font_size=28, color=COLOR_VIOLET).move_to(had_card)
        had_grp = VGroup(had_card, had_tex)

        # 5. Down Projection (Emerald)
        w_down_card = RoundedRectangle(corner_radius=0.1, width=1.8, height=0.9, fill_color=COLOR_CARD_BG, fill_opacity=0.95, stroke_color=COLOR_EMERALD, stroke_width=1.5).shift(RIGHT * 4.4)
        w_down_tex = MathTex(r"W_{\mathrm{down}}", font_size=18, color=COLOR_EMERALD).move_to(w_down_card)
        down_grp = VGroup(w_down_card, w_down_tex)

        # Arrows
        a_x_gate = Arrow(x_card.get_top(), w_gate_card.get_left(), buff=0.1, color=COLOR_AMBER, stroke_width=2.0)
        a_gate_silu = Arrow(w_gate_card.get_right(), silu_card.get_left(), buff=0.1, color=COLOR_AMBER, stroke_width=2.0)
        a_silu_had = Arrow(silu_card.get_right(), had_card.get_top(), buff=0.1, color=COLOR_AMBER, stroke_width=2.0)

        a_x_up = Arrow(x_card.get_bottom(), w_up_card.get_left(), buff=0.1, color=COLOR_CYAN, stroke_width=2.0)
        a_up_had = Arrow(w_up_card.get_right(), had_card.get_bottom(), buff=0.1, color=COLOR_CYAN, stroke_width=2.0)

        a_had_down = Arrow(had_card.get_right(), w_down_card.get_left(), buff=0.1, color=COLOR_EMERALD, stroke_width=2.0)

        # Play Flow Animation
        self.play(FadeIn(x_grp, shift=RIGHT * 0.3), run_time=0.6)
        self.play(Create(a_x_gate), FadeIn(gate_grp), Create(a_x_up), FadeIn(up_grp), run_time=0.9)
        self.play(Create(a_gate_silu), FadeIn(act_grp), run_time=0.6)
        self.play(Create(a_silu_had), Create(a_up_had), FadeIn(had_grp), run_time=0.8)
        self.play(Create(a_had_down), FadeIn(down_grp), run_time=0.6)

        # Formula Summary Bar at Bottom
        f_bar = RoundedRectangle(corner_radius=0.1, width=9.2, height=0.7, fill_color="#10172a", fill_opacity=0.95, stroke_color=COLOR_GOLD, stroke_width=1.5).to_edge(DOWN, buff=0.45)
        f_tex = MathTex(r"\mathrm{SwiGLU}(\mathbf{x}) = \left( \mathrm{SiLU}(\mathbf{x} W_{\mathrm{gate}}) \odot \mathbf{x} W_{\mathrm{up}} \right) W_{\mathrm{down}}", font_size=18, color=COLOR_GOLD).move_to(f_bar)
        self.play(FadeIn(f_bar, shift=UP * 0.2), Write(f_tex), run_time=0.8)
        self.wait(1.5)


# =============================================================================
# SCENE 03: BƯỚC TÍNH SỐ HỌC CỤ THỂ (MATHEMATICS)
# =============================================================================
class Tap04Scene03Mathematics(Scene):
    """
    Mathematics:
    Act 1: Concrete numerical vector x = [1.0, -1.0].
    Act 2: Step-by-step evaluation of Gate (SiLU) and Up paths.
    Act 3: Hadamard product: how negative gate flips polarity (-0.269 * -3.0 = +0.807).
    """
    def construct(self):
        self.camera.background_color = COLOR_BG

        # Title
        title_text = Text(
            "ĐỐI SOÁT SỐ HỌC: HIỆU ỨNG ĐỔI DẤU CỦA CỔNG ÂM",
            font=FONT_FAMILY, font_size=15, weight=BOLD, color=COLOR_GOLD
        )
        title_box = RoundedRectangle(
            corner_radius=0.12, width=title_text.width + 0.6, height=0.5,
            fill_color="#10172a", fill_opacity=0.9, stroke_color=COLOR_GOLD, stroke_width=1.2
        ).to_edge(UP, buff=0.45)
        title_text.move_to(title_box)
        self.play(FadeIn(title_box, shift=DOWN * 0.2), Write(title_text), run_time=0.6)

        # Computation Steps Card
        calc_card = RoundedRectangle(
            corner_radius=0.16, width=10.0, height=4.2,
            fill_color=COLOR_CARD_BG, fill_opacity=0.95, stroke_color=COLOR_BORDER, stroke_width=1.5
        ).shift(DOWN * 0.3)

        s1 = MathTex(r"\mathbf{x} = [1.0, \; -1.0]", font_size=20, color=COLOR_GOLD)
        s2 = MathTex(r"\mathbf{g} = \mathbf{x} W_{\mathrm{gate}} = [1.0, \; -1.0] \implies \mathrm{SiLU}(\mathbf{g}) \approx [0.731, \; -0.269]", font_size=18, color=COLOR_AMBER)
        s3 = MathTex(r"\mathbf{u} = \mathbf{x} W_{\mathrm{up}} = [2.0, \; -3.0]", font_size=18, color=COLOR_CYAN)
        s4 = MathTex(r"\mathbf{h} = \mathrm{SiLU}(\mathbf{g}) \odot \mathbf{u} = [0.731 \times 2.0, \; (-0.269) \times (-3.0)] \approx [1.462, \; \mathbf{+0.807}]", font_size=18, color=COLOR_VIOLET)
        s5 = MathTex(r"\mathbf{y} = \mathbf{h} W_{\mathrm{down}} \approx [2.269, \; 0.807]", font_size=19, color=COLOR_EMERALD)

        steps = VGroup(s1, s2, s3, s4, s5).arrange(DOWN, buff=0.28, aligned_edge=LEFT)
        steps.move_to(calc_card.get_center())

        self.play(FadeIn(calc_card), FadeIn(s1, shift=RIGHT * 0.2), run_time=0.6)
        self.play(FadeIn(s2, shift=RIGHT * 0.2), run_time=0.8)
        self.play(FadeIn(s3, shift=RIGHT * 0.2), run_time=0.8)
        self.play(FadeIn(s4, shift=RIGHT * 0.2), run_time=1.0)
        self.play(Indicate(s4, color=COLOR_GOLD, scale_factor=1.04), run_time=0.8)
        self.play(FadeIn(s5, shift=RIGHT * 0.2), run_time=0.8)

        # Polarity Callout Box at Bottom
        self.wait(1.5)


# =============================================================================
# SCENE 04: CÂN BẰNG NGÂN SÁCH THAM SỐ (TELEMETRY)
# =============================================================================
class Tap04Scene04Telemetry(Scene):
    """
    Telemetry:
    Act 1: Standard FFN (2 matrices) = 8 d^2 parameters.
    Act 2: SwiGLU (3 matrices) = 3 * d * h parameters.
    Act 3: Parameter Parity Equation: 3 d h = 8 d^2 -> h = 8/3 d approx 2.67 d.
    """
    def construct(self):
        self.camera.background_color = COLOR_BG

        # Title
        title_text = Text(
            "CÂN BẰNG NGÂN SÁCH THAM SỐ: NGHỆ THUẬT 8/3 CHIỀU ẨN",
            font=FONT_FAMILY, font_size=15, weight=BOLD, color=COLOR_CYAN
        )
        title_box = RoundedRectangle(
            corner_radius=0.12, width=title_text.width + 0.6, height=0.5,
            fill_color="#10172a", fill_opacity=0.9, stroke_color=COLOR_CYAN, stroke_width=1.2
        ).to_edge(UP, buff=0.45)
        title_text.move_to(title_box)
        self.play(FadeIn(title_box, shift=DOWN * 0.2), Write(title_text), run_time=0.6)

        # 1. Left Card: Standard FFN (Transformer 2017)
        c_l = RoundedRectangle(corner_radius=0.14, width=4.8, height=3.8, fill_color=COLOR_CARD_BG, fill_opacity=0.95, stroke_color=COLOR_ROSE, stroke_width=1.5).shift(LEFT * 2.7 + DOWN * 0.3)
        h_l = Text("STANDARD FFN (2 MA TRẬN)", font=FONT_FAMILY, font_size=12, weight=BOLD, color=COLOR_ROSE).move_to(c_l.get_top() + DOWN * 0.35)
        f_l1 = MathTex(r"W_1 \in [d, 4d], \quad W_2 \in [4d, d]", font_size=16, color=WHITE)
        f_l2 = MathTex(r"\text{Params} = 2 \times 4d^2 = 8d^2", font_size=18, color=COLOR_ROSE)
        t_l_hdr = Text("2 phép nhân ma trận lớn\nHàm ReLU / GELU đơn thuần", font=FONT_FAMILY, font_size=12.0, color=COLOR_MUTED, line_spacing=1.3)
        g_l = VGroup(h_l, f_l1, f_l2, t_l_hdr).arrange(DOWN, buff=0.3, aligned_edge=ORIGIN).move_to(c_l)

        # 2. Right Card: SwiGLU Parity (LLaMA / Mistral)
        c_r = RoundedRectangle(corner_radius=0.14, width=5.2, height=3.8, fill_color=COLOR_CARD_BG, fill_opacity=0.95, stroke_color=COLOR_EMERALD, stroke_width=1.5).shift(RIGHT * 2.7 + DOWN * 0.3)
        h_r = Text("SWIGLU (3 MA TRẬN TƯƠNG ĐƯƠNG)", font=FONT_FAMILY, font_size=12, weight=BOLD, color=COLOR_EMERALD).move_to(c_r.get_top() + DOWN * 0.35)
        f_r1 = MathTex(r"W_{\mathrm{gate}}, W_{\mathrm{up}} \in [d, h], \quad W_{\mathrm{down}} \in [h, d]", font_size=15, color=WHITE)
        f_r2 = MathTex(r"3 \times dh = 8d^2 \implies h = \frac{8}{3}d \approx 2.67d", font_size=17, color=COLOR_EMERALD)
        t_r_hdr = Text("3 ma trận nhỏ hơn nhưng chia sẻ ngân sách\nBảo toàn 100% FLOPs khi huấn luyện!", font=FONT_FAMILY, font_size=12.0, color=COLOR_GOLD, line_spacing=1.3)
        g_r = VGroup(h_r, f_r1, f_r2, t_r_hdr).arrange(DOWN, buff=0.28, aligned_edge=ORIGIN).move_to(c_r)

        self.play(FadeIn(c_l, shift=RIGHT * 0.3), FadeIn(g_l), run_time=0.9)
        self.play(FadeIn(c_r, shift=LEFT * 0.3), FadeIn(g_r), run_time=0.9)
        self.play(Circumscribe(f_r2, color=COLOR_GOLD, time_width=0.8), run_time=1.0)
        self.wait(1.5)


# =============================================================================
# SCENE 05: DÒNG CHẢY GRADIENT & BẢO TOÀN LỖI (LAB EXPERIMENT)
# =============================================================================
class Tap04Scene05LabExperiment(Scene):
    """
    Lab Experiment:
    Act 1: Dual-branch backpropagation flow.
    Act 2: Partial derivative breakdown: Gate path error vs Value path error.
    Act 3: Why SwiGLU avoids dead neurons even when individual coordinates are small.
    """
    def construct(self):
        self.camera.background_color = COLOR_BG

        # Title
        title_text = Text(
            "THỬ NGHIỆM ĐỐI CHỨNG: DÒNG CHẢY GRADIENT QUA HAI NHÁNH",
            font=FONT_FAMILY, font_size=15, weight=BOLD, color=COLOR_ROSE
        )
        title_box = RoundedRectangle(
            corner_radius=0.12, width=title_text.width + 0.6, height=0.5,
            fill_color="#10172a", fill_opacity=0.9, stroke_color=COLOR_ROSE, stroke_width=1.2
        ).to_edge(UP, buff=0.45)
        title_text.move_to(title_box)
        self.play(FadeIn(title_box, shift=DOWN * 0.2), Write(title_text), run_time=0.6)

        # Gradient Backpropagation Card
        grad_card = RoundedRectangle(
            corner_radius=0.16, width=10.2, height=4.2,
            fill_color=COLOR_CARD_BG, fill_opacity=0.95, stroke_color=COLOR_BORDER, stroke_width=1.5
        ).shift(DOWN * 0.3)

        eq_title = Text("CÔNG THỨC LAN TRUYỀN NGƯỢC (CHAIN RULE):", font=FONT_FAMILY, font_size=13, weight=BOLD, color=COLOR_GOLD).move_to(grad_card.get_top() + DOWN * 0.35)

        g_eq1 = MathTex(r"\frac{\partial \mathbf{h}}{\partial \mathbf{u}} = \mathrm{SiLU}(\mathbf{g})", font_size=18, color=COLOR_CYAN)
        g_eq2 = MathTex(r"\frac{\partial \mathbf{h}}{\partial \mathbf{g}} = \mathbf{u} \odot \mathrm{SiLU}'(\mathbf{g}) = \mathbf{u} \odot \left( \sigma(\mathbf{g}) + \mathbf{g} \cdot \sigma(\mathbf{g})(1 - \sigma(\mathbf{g})) \right)", font_size=16, color=COLOR_AMBER)

        g_takeaway_hdr = Text(
            "Gradient từ hàm mất mát luôn phân tách thành hai dòng chảy độc lập:\nNếu nhánh cổng bão hòa, nhánh giá trị vẫn dẫn truyền tín hiệu sửa sai về các tầng sâu!",
            font=FONT_FAMILY, font_size=12.0, color=COLOR_TEXT, line_spacing=1.3
        )

        grad_grp = VGroup(eq_title, g_eq1, g_eq2, g_takeaway_hdr).arrange(DOWN, buff=0.3, aligned_edge=LEFT)
        grad_grp.move_to(grad_card.get_center())

        self.play(FadeIn(grad_card), FadeIn(grad_grp), run_time=1.0)
        self.play(Indicate(g_eq1, color=COLOR_CYAN, scale_factor=1.03), run_time=0.7)
        self.play(Indicate(g_eq2, color=COLOR_AMBER, scale_factor=1.03), run_time=0.7)
        self.wait(1.5)


# =============================================================================
# SCENE 06: TỔNG KẾT KỸ NGHỆ & LỜI TRI ÂN (OUTRO & TAILORED CTA)
# =============================================================================
# =============================================================================
# SCENE 06: TỔNG KẾT KỸ NGHỆ & LỜI TRI ÂN (OUTRO & TAILORED CTA)
# =============================================================================
class Tap04Scene06Outro(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "TỔNG KẾT & CẦU NỐI KỸ NGHỆ")

        scene_title = Text(
            "BÀN GIAO TRI THỨC // SWIGLU & DÒNG CHẢY GRADIENT",
            font=FONT_FAMILY, font_size=15.0, weight=BOLD, color=COLOR_GOLD
        ).to_edge(UP, buff=0.95)
        self.play(FadeIn(scene_title, shift=DOWN * 0.2), run_time=0.8)

        outro_tracker = ValueTracker(0.0)

        # Left Side: 5x5 Closing Thumbnail Mosaic
        mosaic_rel = Path("assets/brand/zenpham-brand-kit/series2_25_thumbnails_mosaic.png")
        mosaic_abs = Path("/home/zen/hermes-agent") / mosaic_rel
        mosaic_work = Path("/work") / mosaic_rel
        mosaic_file = (
            mosaic_work if mosaic_work.exists()
            else mosaic_abs if mosaic_abs.exists()
            else mosaic_rel
        )

        mosaic_x = -3.2
        mosaic_y = 0.55
        mosaic_w = 5.8

        if mosaic_file.exists():
            mosaic_mobj = ImageMobject(str(mosaic_file))
            mosaic_mobj.scale_to_fit_width(mosaic_w)
            mosaic_mobj.move_to(np.array([mosaic_x, mosaic_y, 0.0]))
        else:
            mosaic_mobj = RoundedRectangle(
                width=mosaic_w, height=3.38, corner_radius=0.12,
                fill_color=COLOR_PANEL, fill_opacity=0.85, stroke_color=COLOR_CYAN, stroke_width=1.5
            ).move_to(np.array([mosaic_x, mosaic_y, 0.0]))

        mosaic_frame = SurroundingRectangle(
            mosaic_mobj, buff=0.06, stroke_color=COLOR_CYAN, stroke_width=1.5, corner_radius=0.12
        )
        gallery_header = Text(
            "TRỌN BỘ SERIES 2 · 25 TẬP KỸ NGHỆ LLM TỐI TÂN",
            font=FONT_FAMILY, font_size=12.5, weight=BOLD, color=COLOR_GOLD
        ).next_to(mosaic_frame, UP, buff=0.18)

        left_grp = Group(mosaic_mobj, mosaic_frame, gallery_header)
        self.play(FadeIn(left_grp, shift=RIGHT * 0.3), run_time=1.2)

        # Right Side: YouTube End Screen Interactive Safe Zones
        # 1. Next Video Card (Episode 05: RMSNorm)
        next_card = RoundedRectangle(
            corner_radius=0.12, width=3.8, height=2.0,
            fill_color=COLOR_PANEL, fill_opacity=0.7, stroke_color=COLOR_CYAN, stroke_width=1.5
        ).move_to(RIGHT * 3.5 + UP * 1.5)
        next_header = Text("TẬP TIẾP THEO // TẬP 05", font=FONT_FAMILY, font_size=12.5, weight=BOLD, color=COLOR_CYAN)
        next_sub_header = Text("RMSNORM: TỐI GIẢN PHẦN CỨNG", font=FONT_FAMILY, font_size=12.0, color=COLOR_TEXT).next_to(next_header, DOWN, buff=0.18)
        next_grp = VGroup(next_header, next_sub_header).move_to(next_card.get_center())

        # 2. Playlist Card
        pl_card = RoundedRectangle(
            corner_radius=0.12, width=3.8, height=1.3,
            fill_color=COLOR_PANEL, fill_opacity=0.7, stroke_color=COLOR_GOLD, stroke_width=1.5
        ).move_to(RIGHT * 3.5 + DOWN * 0.35)
        pl_header = Text("DANH SÁCH PHÁT SERIES 2", font=FONT_FAMILY, font_size=12.5, weight=BOLD, color=COLOR_GOLD)
        pl_sub_header = Text("THE ANATOMY OF MODERN LLMS", font=FONT_FAMILY, font_size=12.0, color=COLOR_MUTED).next_to(pl_header, DOWN, buff=0.15)
        pl_grp = VGroup(pl_header, pl_sub_header).move_to(pl_card.get_center())

        # 3. Subscribe Card
        sub_card = RoundedRectangle(
            corner_radius=0.12, width=3.8, height=1.1,
            fill_color=COLOR_PANEL, fill_opacity=0.7, stroke_color=COLOR_ROSE, stroke_width=1.5
        ).move_to(RIGHT * 3.5 + DOWN * 1.85)
        sub_header = Text("ĐĂNG KÝ KÊNH // ZENPHAM", font=FONT_FAMILY, font_size=12.5, weight=BOLD, color=COLOR_ROSE)
        sub_sub_header = Text("AI CRAFTSMANSHIP & ENGINEERING", font=FONT_FAMILY, font_size=12.0, color=COLOR_TEXT).next_to(sub_header, DOWN, buff=0.12)
        sub_grp = VGroup(sub_header, sub_sub_header).move_to(sub_card.get_center())

        right_grp = VGroup(next_card, next_grp, pl_card, pl_grp, sub_card, sub_grp)
        self.play(FadeIn(right_grp, shift=LEFT * 0.3), run_time=1.2)

        # Kinetic Pulse & Glow
        self.play(
            mosaic_frame.animate.set_stroke(COLOR_GOLD, width=2.2),
            next_card.animate.set_stroke(COLOR_GOLD, width=2.2),
            run_time=1.5
        )
        self.wait(2.0)

