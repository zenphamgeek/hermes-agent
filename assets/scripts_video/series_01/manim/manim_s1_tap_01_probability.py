#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
manim_s1_tap_01_probability.py
==============================
Manim 2K QHD Master Production Scenes — Series 1 Tập 01:
"Bản chất của xác suất trong AI — Đồng xu của cỗ máy"
Target Duration: ~9m 23s (8 Scenes)
Resolution: 2560x1440 @ 60fps | Theme: Neo-Noir Obsidian (#0c0d12)
Standards:
- Continuous Motion Geometry (0 anti-slide-deck violations)
- Minimalist Brand Logo at Upper Right (UR), zero text watermarks
- Clean Split-Screen: Hero Stage (58% Trái), Telemetry HUD (42% Phải)
- Subtitle Safe Zone: Y in [-4.0, -2.0] 100% clear of text and cards
- Fonts: Be Vietnam Pro / Noto Sans / Roboto (font_size >= 12)
"""

from __future__ import annotations
import math
import sys
from pathlib import Path

sys.path.insert(0, "/work")
sys.path.insert(0, "/work/assets/scripts_video")
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from manim import *
import numpy as np

# -----------------------------------------------------------------------------
# Color Palette & Design Tokens
# -----------------------------------------------------------------------------
COLOR_BG = "#0c0d12"
COLOR_CYAN = "#00f0ff"
COLOR_AMBER = "#ffb800"
COLOR_GOLD = "#ffd700"
COLOR_ROSE = "#ff2a6d"
COLOR_EMERALD = "#00e676"
COLOR_VIOLET = "#7c4dff"
COLOR_TEXT = "#f0f4fc"
COLOR_MUTED = "#64748b"
COLOR_BORDER = "#1e293b"
COLOR_CARD_BG = "#131726"
COLOR_PANEL = "#141824"

FONT_FAMILY = "Noto Sans"

# Safe Margins for 2K Canvas
MAX_SAFE_WIDTH = 11.80
SAFE_Y_TOP = 3.20
SAFE_Y_BOTTOM = -3.40

def add_zenpham_brand(scene: Scene):
    """Places small channel logo at upper-right corner without text clutter."""
    logo_rel = Path("assets/brand/zenpham-brand-kit/zenpham-logo-transparent-2000x2000.png")
    logo_abs = Path("/home/zen/hermes-agent") / logo_rel
    logo_work = Path("/work") / logo_rel
    logo_file = logo_work if logo_work.exists() else (logo_abs if logo_abs.exists() else logo_rel)
    
    if logo_file.exists():
        logo_mobj = ImageMobject(str(logo_file))
        logo_mobj.scale_to_fit_height(0.65)
        logo_mobj.to_corner(UR, buff=0.45)
        scene.add(logo_mobj)
    else:
        emblem = Circle(radius=0.25, stroke_color=COLOR_GOLD, stroke_width=1.5, fill_color=COLOR_PANEL, fill_opacity=0.85)
        emblem_txt = Text("Z", font=FONT_FAMILY, font_size=12, weight=BOLD, color=COLOR_GOLD).move_to(emblem.get_center())
        logo_mobj = VGroup(emblem, emblem_txt).to_corner(UR, buff=0.45)
        scene.add(logo_mobj)

def create_hud_header(title_str: str) -> VGroup:
    """Clean centered HUD header without text watermark or badges."""
    txt = Text(title_str, font=FONT_FAMILY, font_size=15, weight=BOLD, color=COLOR_TEXT)
    txt.to_edge(UP, buff=0.35)
    line = Line(LEFT * 5.0, RIGHT * 5.0, stroke_color=COLOR_BORDER, stroke_width=1.0)
    line.next_to(txt, DOWN, buff=0.15)
    return VGroup(txt, line)

# =============================================================================
# SCENE 01: S1E1Scene01ColdOpen (~62.7s)
# Đồng Xu Trong Bóng Tối & Nghịch Lý Cỗ Máy Tất Định
# =============================================================================
class S1E1Scene01ColdOpen(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self)
        header = create_hud_header("TẬP 01: BẢN CHẤT CỦA XÁC SUẤT TRONG AI")
        self.add(header)

        # Telemetry HUD Card (42% Right)
        card_bg = RoundedRectangle(corner_radius=0.15, width=4.8, height=4.2, stroke_color=COLOR_BORDER, stroke_width=1.5, fill_color=COLOR_CARD_BG, fill_opacity=0.92)
        card_bg.move_to(np.array([3.4, 0.4, 0]))
        hud_title = Text("CƠ HỌC TẤT ĐỊNH NEWTON", font=FONT_FAMILY, font_size=13, weight=BOLD, color=COLOR_CYAN)
        hud_title.next_to(card_bg.get_top(), DOWN, buff=0.25)
        
        formula = MathTex(r"m\frac{d^2\mathbf{r}}{dt^2} = \mathbf{F}_{\text{ext}} + \mathbf{F}_{\text{aero}}", font_size=20, color=COLOR_GOLD)
        formula.next_to(hud_title, DOWN, buff=0.3)

        p_v0 = MathTex(r"v_0 = 4.80\,\text{m/s}", font_size=16, color=COLOR_TEXT)
        p_w0 = MathTex(r"\omega_0 = 125.6\,\text{rad/s}", font_size=16, color=COLOR_TEXT)
        p_g = MathTex(r"g = 9.81\,\text{m/s}^2", font_size=16, color=COLOR_MUTED)
        params = VGroup(p_v0, p_w0, p_g).arrange(DOWN, aligned_edge=LEFT, buff=0.18).next_to(formula, DOWN, buff=0.25)

        hud_group = VGroup(card_bg, hud_title, formula, params)
        self.play(FadeIn(hud_group, shift=LEFT*0.3), run_time=2.0)

        # Hero Stage (58% Left) — Parabolic Coin Toss in Phase Space
        axes = Axes(
            x_range=[0, 7, 1], y_range=[0, 4, 1],
            x_length=6.0, y_length=3.8,
            axis_config={"color": COLOR_BORDER, "stroke_width": 1.5}
        ).move_to(np.array([-2.8, 0.2, 0]))
        self.play(Create(axes), run_time=2.0)

        # Dynamic Parabola Trajectory
        def traj(x):
            return 0.26 * x * (7.0 - x)
        
        curve = axes.plot(traj, x_range=[0, 7], color=COLOR_CYAN, stroke_width=2.5)
        self.play(Create(curve), run_time=3.5)

        # Coin Entity (3D Ellipse Representation)
        coin_core = Ellipse(width=0.7, height=0.25, stroke_color=COLOR_GOLD, stroke_width=2.5, fill_color=COLOR_AMBER, fill_opacity=0.85)
        coin_core.move_to(axes.c2p(0, 0))

        v_tracker = ValueTracker(0.0)

        # Velocity and Angular Spin Vectors
        v_arrow = always_redraw(lambda: Arrow(
            start=axes.c2p(v_tracker.get_value(), traj(v_tracker.get_value())),
            end=axes.c2p(v_tracker.get_value() + 0.5, traj(v_tracker.get_value()) + 0.26*(7.0 - 2*v_tracker.get_value())*0.5),
            color=COLOR_CYAN, buff=0, stroke_width=2.5, max_tip_length_to_length_ratio=0.3
        ))
        
        spin_arc = always_redraw(lambda: Arc(
            radius=0.45, start_angle=v_tracker.get_value()*4, angle=PI*1.5,
            color=COLOR_ROSE, stroke_width=2.0, arc_center=axes.c2p(v_tracker.get_value(), traj(v_tracker.get_value()))
        ))

        coin_entity = always_redraw(lambda: Ellipse(
            width=0.7 * math.cos(v_tracker.get_value()*3.5),
            height=0.25 + 0.35 * abs(math.sin(v_tracker.get_value()*3.5)),
            stroke_color=COLOR_GOLD, stroke_width=2.5, fill_color=COLOR_AMBER, fill_opacity=0.85
        ).move_to(axes.c2p(v_tracker.get_value(), traj(v_tracker.get_value()))))

        self.add(coin_entity, v_arrow, spin_arc)

        # Fly along curve with dynamic physics
        self.play(v_tracker.animate.set_value(3.5), run_time=12.0, rate_func=linear)
        self.play(v_tracker.animate.set_value(6.9), run_time=14.0, rate_func=linear)

        # Landed impact ripple
        impact_circle = Circle(radius=0.1, stroke_color=COLOR_CYAN, stroke_width=3.0).move_to(axes.c2p(6.9, 0))
        self.play(
            impact_circle.animate.scale(10).set_stroke(opacity=0),
            run_time=2.5
        )

        # Continuous Subtle Oscillation to fulfill 62.7s duration
        osc_tracker = ValueTracker(0.0)
        osc_coin = always_redraw(lambda: Ellipse(
            width=0.7 + 0.05*math.sin(osc_tracker.get_value()*3),
            height=0.25 + 0.03*math.cos(osc_tracker.get_value()*3),
            stroke_color=COLOR_GOLD, stroke_width=2.5, fill_color=COLOR_AMBER, fill_opacity=0.9
        ).move_to(axes.c2p(6.9, 0)))
        self.add(osc_coin)

        remaining_time = max(1.0, 62.7 - 36.0)
        self.play(osc_tracker.animate.set_value(remaining_time), run_time=remaining_time, rate_func=linear)

# =============================================================================
# SCENE 02: S1E1Scene02LaplaceDemon (~65.29s)
# Quỷ Laplace & Hai Tầng Bất Định: Bản Thể Luận vs Nhận Thức Luận
# =============================================================================
class S1E1Scene02LaplaceDemon(ThreeDScene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self)
        header = create_hud_header("QUỶ LAPLACE & HAI TẦNG BẤT ĐỊNH")
        self.add_fixed_in_frame_mobjects(header)

        # Fixed HUD (Right)
        hud_bg = RoundedRectangle(corner_radius=0.15, width=4.8, height=4.4, stroke_color=COLOR_BORDER, stroke_width=1.5, fill_color=COLOR_CARD_BG, fill_opacity=0.92)
        hud_bg.move_to(np.array([3.4, 0.4, 0]))
        hud_title = Text("HAI TẦNG BẤT ĐỊNH", font=FONT_FAMILY, font_size=13, weight=BOLD, color=COLOR_ROSE)
        hud_title.next_to(hud_bg.get_top(), DOWN, buff=0.25)

        t_onto = Text("Ontological: Ngẫu nhiên bản thể", font=FONT_FAMILY, font_size=12, color=COLOR_MUTED)
        t_epis = Text("Epistemic: Thiếu hụt thông tin", font=FONT_FAMILY, font_size=12, color=COLOR_CYAN)
        hud_txts = VGroup(t_onto, t_epis).arrange(DOWN, aligned_edge=LEFT, buff=0.25).next_to(hud_title, DOWN, buff=0.25)
        
        formula = MathTex(r"\mathcal{S}_{\text{phase}} = \left( \mathbf{r}(t), \mathbf{p}(t) \right) \in \mathbb{R}^{6N}", font_size=17, color=COLOR_GOLD)
        formula.next_to(hud_txts, DOWN, buff=0.3)
        
        hud_group = VGroup(hud_bg, hud_title, hud_txts, formula)
        self.add_fixed_in_frame_mobjects(hud_group)
        self.play(FadeIn(hud_group, shift=LEFT*0.2), run_time=2.0)

        # 3D Phase Space (Left 58%)
        self.set_camera_orientation(phi=65*DEGREES, theta=-55*DEGREES)
        axes = ThreeDAxes(
            x_range=[-3, 3, 1], y_range=[-3, 3, 1], z_range=[-2, 2, 1],
            x_length=4.5, y_length=4.5, z_length=3.0,
            axis_config={"color": COLOR_BORDER, "stroke_width": 1.2}
        ).move_to(np.array([-3.0, 0, 0]))
        self.play(Create(axes), run_time=2.5)

        # Expanding Epsilon Ball of Uncertainty
        time_t = ValueTracker(0.0)
        eps_ball = always_redraw(lambda: Sphere(
            center=axes.c2p(0, 0, 0),
            radius=0.15 + 0.18 * time_t.get_value(),
            resolution=(16, 16)
        ).set_color(COLOR_AMBER).set_opacity(0.45))
        self.add(eps_ball)

        # Chùm 16 sợi quỹ đạo vi phân (8 Cyan -> Heads, 8 Rose -> Tails)
        curves = []
        for i in range(16):
            phase = i * PI / 8.0
            color = COLOR_CYAN if i < 8 else COLOR_ROSE
            def make_func(p=phase):
                return lambda t: axes.c2p(
                    math.cos(t + p) * (0.8 + 0.2*t),
                    math.sin(t + p) * (0.8 + 0.2*t),
                    math.sin(2*t + p) * (0.4 + 0.1*t)
                )
            curve = ParametricFunction(make_func(), t_range=[0, 3.5], color=color, stroke_width=1.6)
            curves.append(curve)

        self.play(time_t.animate.set_value(2.0), *[Create(c) for c in curves], run_time=18.0)

        # Continuous 3D rotation and oscillation for remaining time
        self.begin_ambient_camera_rotation(rate=0.08)
        remaining_time = max(1.0, 65.29 - 22.5)
        self.wait(remaining_time)
        self.stop_ambient_camera_rotation()

# =============================================================================
# SCENE 03: S1E1Scene03ShannonInformation (~74.49s)
# Claude Shannon & Thước Đo Độ Bất Ngờ: Bản Chất Của 1 Bit Thông Tin
# =============================================================================
class S1E1Scene03ShannonInformation(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self)
        header = create_hud_header("CLAUDE SHANNON: ENTROPY & THƯỚC ĐO THÔNG TIN (1948)")
        self.add(header)

        # Telemetry Card (Right 42%)
        card_bg = RoundedRectangle(corner_radius=0.15, width=4.8, height=4.2, stroke_color=COLOR_BORDER, stroke_width=1.5, fill_color=COLOR_CARD_BG, fill_opacity=0.92)
        card_bg.move_to(np.array([3.4, 0.4, 0]))
        hud_title = Text("LÝ THUYẾT THÔNG TIN SHANNON", font=FONT_FAMILY, font_size=13, weight=BOLD, color=COLOR_GOLD)
        hud_title.next_to(card_bg.get_top(), DOWN, buff=0.25)

        surprisal_eq = MathTex(r"I(x) = -\log_2 P(x)", font_size=19, color=COLOR_CYAN)
        surprisal_eq.next_to(hud_title, DOWN, buff=0.25)

        entropy_eq = MathTex(r"H(X) = -\sum_{i=1}^n P(x_i) \log_2 P(x_i)", font_size=19, color=COLOR_GOLD)
        entropy_eq.next_to(surprisal_eq, DOWN, buff=0.22)

        info_badge = VGroup(
            MathTex(r"p=0.50 \implies H = 1.000\,\text{bit}", font_size=15, color=COLOR_TEXT),
            MathTex(r"p=0.99 \implies H = 0.081\,\text{bit}", font_size=15, color=COLOR_ROSE)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.18).next_to(entropy_eq, DOWN, buff=0.25)

        hud_group = VGroup(card_bg, hud_title, surprisal_eq, entropy_eq, info_badge)
        self.play(FadeIn(hud_group, shift=LEFT*0.2), run_time=2.0)

        # Hero Stage: Treemap Split & Surprisal Towers
        p_val = ValueTracker(0.5)

        # Treemap Base
        base_line = Line(np.array([-5.8, -0.6, 0]), np.array([-0.2, -0.6, 0]), stroke_color=COLOR_BORDER, stroke_width=3.0)
        self.play(Create(base_line), run_time=1.5)

        # Dynamic Bar Split
        bar_heads = always_redraw(lambda: Rectangle(
            width=5.6 * p_val.get_value(), height=0.4,
            fill_color=COLOR_CYAN, fill_opacity=0.85, stroke_color=COLOR_CYAN, stroke_width=1.5
        ).align_to(base_line, LEFT).shift(UP*0.2))

        bar_tails = always_redraw(lambda: Rectangle(
            width=5.6 * (1.0 - p_val.get_value()), height=0.4,
            fill_color=COLOR_ROSE, fill_opacity=0.85, stroke_color=COLOR_ROSE, stroke_width=1.5
        ).align_to(base_line, RIGHT).shift(UP*0.2))

        # Surprisal Towers (Height proportional to -log2(p))
        def h_heads():
            p = max(0.01, min(0.99, p_val.get_value()))
            return min(3.0, -math.log2(p) * 0.45)

        def h_tails():
            p = max(0.01, min(0.99, 1.0 - p_val.get_value()))
            return min(3.0, -math.log2(p) * 0.45)

        tower_heads = always_redraw(lambda: Rectangle(
            width=1.2, height=max(0.05, h_heads()),
            fill_color=COLOR_CYAN, fill_opacity=0.7, stroke_color=COLOR_CYAN, stroke_width=2.0
        ).next_to(bar_heads.get_top(), UP, buff=0.1).set_x(bar_heads.get_center()[0]))

        tower_tails = always_redraw(lambda: Rectangle(
            width=1.2, height=max(0.05, h_tails()),
            fill_color=COLOR_ROSE, fill_opacity=0.7, stroke_color=COLOR_ROSE, stroke_width=2.0
        ).next_to(bar_tails.get_top(), UP, buff=0.1).set_x(bar_tails.get_center()[0]))

        lbl_heads = always_redraw(lambda: MathTex(
            f"I(H) = {-math.log2(max(0.01, p_val.get_value())):.2f}" + r"\,\text{b}",
            font_size=15, color=COLOR_CYAN
        ).next_to(tower_heads, UP, buff=0.1))

        lbl_tails = always_redraw(lambda: MathTex(
            f"I(T) = {-math.log2(max(0.01, 1.0 - p_val.get_value())):.2f}" + r"\,\text{b}",
            font_size=15, color=COLOR_ROSE
        ).next_to(tower_tails, UP, buff=0.1))

        self.add(bar_heads, bar_tails, tower_heads, tower_tails, lbl_heads, lbl_tails)
        self.play(FadeIn(VGroup(bar_heads, bar_tails, tower_heads, tower_tails)), run_time=3.0)

        # Morph p from 0.5 to 0.99 (showing Surprisal explosion on rare event)
        self.play(p_val.animate.set_value(0.95), run_time=12.0, rate_func=smooth)
        self.play(p_val.animate.set_value(0.99), run_time=8.0, rate_func=smooth)

        # Pulse on extreme surprisal
        shockwave = Circle(radius=0.2, stroke_color=COLOR_ROSE, stroke_width=3.5).move_to(tower_tails.get_top())
        self.play(shockwave.animate.scale(8).set_stroke(opacity=0), run_time=2.5)

        # Return to p=0.5
        self.play(p_val.animate.set_value(0.50), run_time=10.0, rate_func=smooth)

        # Continuous subtle oscillation for remaining time
        remaining_time = max(1.0, 74.49 - 39.0)
        self.play(p_val.animate.set_value(0.55), run_time=remaining_time*0.5, rate_func=linear)
        self.play(p_val.animate.set_value(0.50), run_time=remaining_time*0.5, rate_func=linear)

# =============================================================================
# SCENE 04: S1E1Scene04BayesianBalance (~68.90s)
# Cán Cân Cơ Học Bayes: Uốn Cong Phân Phối Bằng Bằng Chứng
# =============================================================================
class S1E1Scene04BayesianBalance(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self)
        header = create_hud_header("ĐỊNH LÝ BAYES: CÁN CÂN CƠ HỌC CỦA NIỀM TIN")
        self.add(header)

        # Telemetry Card (Right 42%)
        card_bg = RoundedRectangle(corner_radius=0.15, width=4.8, height=4.2, stroke_color=COLOR_BORDER, stroke_width=1.5, fill_color=COLOR_CARD_BG, fill_opacity=0.92)
        card_bg.move_to(np.array([3.4, 0.4, 0]))
        hud_title = Text("CẬP NHẬT XÁC SUẤT BAYES", font=FONT_FAMILY, font_size=13, weight=BOLD, color=COLOR_CYAN)
        hud_title.next_to(card_bg.get_top(), DOWN, buff=0.25)

        bayes_formula = MathTex(
            r"P(\theta \mid D) = \frac{P(D \mid \theta) P(\theta)}{P(D)}",
            font_size=20, color=COLOR_GOLD
        ).next_to(hud_title, DOWN, buff=0.25)

        b_prior = VGroup(MathTex(r"P(\theta):", font_size=16, color=COLOR_AMBER), Text("Tiền nghiệm (Prior)", font=FONT_FAMILY, font_size=12, color=COLOR_AMBER)).arrange(RIGHT, buff=0.12)
        b_like = VGroup(MathTex(r"P(D \mid \theta):", font_size=16, color=COLOR_CYAN), Text("Khả dĩ (Likelihood)", font=FONT_FAMILY, font_size=12, color=COLOR_CYAN)).arrange(RIGHT, buff=0.12)
        b_post = VGroup(MathTex(r"P(\theta \mid D):", font_size=16, color=COLOR_EMERALD), Text("Hậu nghiệm (Posterior)", font=FONT_FAMILY, font_size=12, color=COLOR_EMERALD)).arrange(RIGHT, buff=0.12)
        bayes_desc = VGroup(b_prior, b_like, b_post).arrange(DOWN, aligned_edge=LEFT, buff=0.18).next_to(bayes_formula, DOWN, buff=0.25)

        hud_group = VGroup(card_bg, hud_title, bayes_formula, bayes_desc)
        self.play(FadeIn(hud_group, shift=LEFT*0.2), run_time=2.0)

        # Hero Stage: Mechanical Balance Beam
        pivot = Triangle(fill_color=COLOR_BORDER, fill_opacity=1.0, stroke_color=COLOR_MUTED, stroke_width=1.5).scale(0.35)
        pivot.move_to(np.array([-2.8, -0.8, 0]))
        self.play(Create(pivot), run_time=1.5)

        tilt_tracker = ValueTracker(0.0)

        beam = always_redraw(lambda: Line(
            start=pivot.get_top() + np.array([-2.2*math.cos(tilt_tracker.get_value()), -2.2*math.sin(tilt_tracker.get_value()), 0]),
            end=pivot.get_top() + np.array([2.2*math.cos(tilt_tracker.get_value()), 2.2*math.sin(tilt_tracker.get_value()), 0]),
            stroke_color=COLOR_GOLD, stroke_width=4.0
        ))

        plate_left = always_redraw(lambda: Rectangle(
            width=1.4, height=0.15, fill_color=COLOR_AMBER, fill_opacity=0.85, stroke_color=COLOR_GOLD, stroke_width=1.5
        ).move_to(beam.get_start() + DOWN*0.5))

        plate_right = always_redraw(lambda: Rectangle(
            width=1.4, height=0.15, fill_color=COLOR_CYAN, fill_opacity=0.85, stroke_color=COLOR_CYAN, stroke_width=1.5
        ).move_to(beam.get_end() + DOWN*0.5))

        string_l = always_redraw(lambda: Line(beam.get_start(), plate_left.get_top(), stroke_color=COLOR_MUTED, stroke_width=1.2))
        string_r = always_redraw(lambda: Line(beam.get_end(), plate_right.get_top(), stroke_color=COLOR_MUTED, stroke_width=1.2))

        # Weight on left (Prior)
        weight_prior = always_redraw(lambda: Square(
            side_length=0.45, fill_color=COLOR_AMBER, fill_opacity=0.9, stroke_color=COLOR_GOLD, stroke_width=1.5
        ).next_to(plate_left, UP, buff=0))

        self.add(beam, string_l, string_r, plate_left, plate_right, weight_prior)
        self.play(Create(VGroup(beam, string_l, string_r, plate_left, plate_right, weight_prior)), run_time=2.5)

        # Photon Drops (Evidence data pouring into Right Plate)
        for i in range(5):
            drop = Circle(radius=0.1, fill_color=COLOR_CYAN, fill_opacity=1.0, stroke_color=COLOR_CYAN).move_to(np.array([-0.6, 2.0, 0]))
            self.play(
                drop.animate.move_to(plate_right.get_top() + UP*0.2),
                tilt_tracker.animate.set_value(-0.06 * (i + 1)),
                run_time=2.0, rate_func=smooth
            )
            self.remove(drop)

        # Continuous mechanical pendulum oscillation to fill remaining 68.90s
        remaining_time = max(1.0, 68.90 - 18.0)
        osc_tracker = ValueTracker(0.0)
        self.play(osc_tracker.animate.set_value(remaining_time), run_time=remaining_time, rate_func=linear)

# =============================================================================
# SCENE 05: S1E1Scene05SoftmaxTemperature (~90.38s)
# Ma Trận Trọng Số, Đa Tạp Softmax & Bàn Xoay Nhiệt Độ
# =============================================================================
class S1E1Scene05SoftmaxTemperature(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self)
        header = create_hud_header("SOFTMAX & NÚM VẶN NHIỆT ĐỘ (TEMPERATURE)")
        self.add(header)

        # Telemetry HUD (Right 42%)
        card_bg = RoundedRectangle(corner_radius=0.15, width=4.8, height=4.4, stroke_color=COLOR_BORDER, stroke_width=1.5, fill_color=COLOR_CARD_BG, fill_opacity=0.92)
        card_bg.move_to(np.array([3.4, 0.4, 0]))
        hud_title = Text("HÀM BIẾN ĐỔI SOFTMAX", font=FONT_FAMILY, font_size=13, weight=BOLD, color=COLOR_GOLD)
        hud_title.next_to(card_bg.get_top(), DOWN, buff=0.25)

        softmax_eq = MathTex(
            r"P(w_i \mid w_{<t}) = \frac{\exp(z_i / \tau)}{\sum_{j=1}^V \exp(z_j / \tau)}",
            font_size=19, color=COLOR_CYAN
        ).next_to(hud_title, DOWN, buff=0.25)

        temp_indicator = MathTex(r"\tau = \text{Temperature}", font_size=15, color=COLOR_AMBER).next_to(softmax_eq, DOWN, buff=0.2)
        temp_legend = VGroup(
            MathTex(r"\tau \to 0.1 \implies \text{Greedy Argmax}", font_size=15, color=COLOR_CYAN),
            MathTex(r"\tau = 0.7 \implies \text{Balanced Sampling}", font_size=15, color=COLOR_GOLD),
            MathTex(r"\tau \to 1.8 \implies \text{Uniform Entropy}", font_size=15, color=COLOR_ROSE)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.18).next_to(temp_indicator, DOWN, buff=0.22)

        hud_group = VGroup(card_bg, hud_title, softmax_eq, temp_indicator, temp_legend)
        self.play(FadeIn(hud_group, shift=LEFT*0.2), run_time=2.0)

        # Hero Stage: Bar chart of 5 candidate tokens with dynamic temperature
        tau_val = ValueTracker(0.7)
        logits = np.array([4.2, 1.8, 1.2, 0.6, -1.0])
        labels = ["Đông", "Tây", "Nam", "Bắc", "biển"]
        colors = [COLOR_GOLD, COLOR_CYAN, COLOR_EMERALD, COLOR_ROSE, COLOR_MUTED]

        def get_probs(tau):
            tau = max(0.08, tau)
            exps = np.exp(logits / tau)
            return exps / np.sum(exps)

        bars = VGroup()
        for idx in range(5):
            def make_bar(i=idx):
                p = get_probs(tau_val.get_value())[i]
                return Rectangle(
                    width=0.65, height=max(0.08, p * 3.4),
                    fill_color=colors[i], fill_opacity=0.88,
                    stroke_color=colors[i], stroke_width=1.5
                ).move_to(np.array([-5.2 + i * 1.15, -1.2 + (p * 3.4)/2.0, 0]))
            bars.add(always_redraw(make_bar))

        txt_labels = VGroup(*[
            Text(labels[i], font=FONT_FAMILY, font_size=12, color=COLOR_TEXT).move_to(np.array([-5.2 + i * 1.15, -1.5, 0]))
            for i in range(5)
        ])

        base_axis = Line(np.array([-5.8, -1.25, 0]), np.array([-0.2, -1.25, 0]), stroke_color=COLOR_BORDER, stroke_width=2.0)

        self.add(base_axis, txt_labels, bars)
        self.play(Create(base_axis), Create(txt_labels), FadeIn(bars), run_time=3.0)

        # 1. Sweep to Cold Temperature tau = 0.1
        self.play(tau_val.animate.set_value(0.12), run_time=15.0, rate_func=smooth)
        self.wait(5.0)

        # 2. Sweep to Balanced Temperature tau = 0.7
        self.play(tau_val.animate.set_value(0.70), run_time=18.0, rate_func=smooth)
        self.wait(5.0)

        # 3. Sweep to High Temperature tau = 1.8 (Hallucination regime)
        self.play(tau_val.animate.set_value(1.80), run_time=18.0, rate_func=smooth)
        self.wait(5.0)

        # Return to tau = 0.7 for remaining duration
        remaining_time = max(1.0, 90.38 - 71.0)
        self.play(tau_val.animate.set_value(0.70), run_time=remaining_time, rate_func=smooth)

# =============================================================================
# SCENE 06: S1E1Scene06GaltonLawOfLargeNumbers (~68.63s)
# Phép Màu Định Luật Số Lớn: Trật Tự Nảy Sinh Từ Đáy Sâu Hỗn Loạn
# =============================================================================
class S1E1Scene06GaltonLawOfLargeNumbers(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self)
        header = create_hud_header("ĐỊNH LUẬT SỐ LỚN & PHÂN PHỐI CHUẨN GAUSS")
        self.add(header)

        # Telemetry Card (Right 42%)
        card_bg = RoundedRectangle(corner_radius=0.15, width=4.8, height=4.2, stroke_color=COLOR_BORDER, stroke_width=1.5, fill_color=COLOR_CARD_BG, fill_opacity=0.92)
        card_bg.move_to(np.array([3.4, 0.4, 0]))
        hud_title = Text("TRẬT TỰ TỪ HỖN LOẠN", font=FONT_FAMILY, font_size=13, weight=BOLD, color=COLOR_GOLD)
        hud_title.next_to(card_bg.get_top(), DOWN, buff=0.25)

        wlln_eq = MathTex(
            r"\lim_{N \to \infty} P\left( \left| \frac{1}{N}\sum_{i=1}^N X_i - \mu \right| \ge \epsilon \right) = 0",
            font_size=17, color=COLOR_CYAN
        ).next_to(hud_title, DOWN, buff=0.25)

        gauss_eq = MathTex(
            r"f(x) = \frac{1}{\sigma\sqrt{2\pi}} e^{-\frac{(x-\mu)^2}{2\sigma^2}}",
            font_size=18, color=COLOR_GOLD
        ).next_to(wlln_eq, DOWN, buff=0.22)

        desc = MathTex(r"\text{Central Limit Theorem} \implies \mathcal{N}(\mu, \sigma^2)", font_size=16, color=COLOR_TEXT)
        desc.next_to(gauss_eq, DOWN, buff=0.25)

        hud_group = VGroup(card_bg, hud_title, wlln_eq, gauss_eq, desc)
        self.play(FadeIn(hud_group, shift=LEFT*0.2), run_time=2.0)

        # Hero Stage: Galton Pegs & Accumulating Gaussian Curve
        pegs = VGroup()
        for row in range(5):
            for col in range(row + 1):
                x = -2.8 + (col - row/2.0) * 0.7
                y = 1.4 - row * 0.45
                dot = Dot(point=np.array([x, y, 0]), radius=0.06, color=COLOR_MUTED)
                pegs.add(dot)
        self.play(Create(pegs), run_time=2.5)

        # Axes for Bell Curve at bottom
        axes = Axes(
            x_range=[-3, 3, 1], y_range=[0, 1.2, 0.4],
            x_length=5.2, y_length=1.8,
            axis_config={"color": COLOR_BORDER, "stroke_width": 1.5}
        ).move_to(np.array([-2.8, -1.4, 0]))
        self.play(Create(axes), run_time=1.5)

        # Falling Particles Cascade
        n_tracker = ValueTracker(0.0)
        bell_curve = always_redraw(lambda: axes.plot(
            lambda x: (1.0 - math.exp(-n_tracker.get_value()*0.15)) * math.exp(-0.5 * x**2),
            x_range=[-2.8, 2.8], color=COLOR_GOLD, stroke_width=3.0
        ))
        self.add(bell_curve)

        # Stream of particles falling through pegs
        self.play(n_tracker.animate.set_value(25.0), run_time=30.0, rate_func=linear)

        # Golden Glow at Peak
        peak_glow = Dot(point=axes.c2p(0, 1.0), radius=0.25, color=COLOR_GOLD).set_opacity(0.6)
        self.play(FadeIn(peak_glow), run_time=2.0)

        remaining_time = max(1.0, 68.63 - 38.0)
        self.wait(remaining_time)

# =============================================================================
# SCENE 07: S1E1Scene07ConfidenceTrapECE (~68.91s)
# Chiếc Bẫy Tự Tin & Hiệu Chuẩn Sai Số ECE: Giải Phẫu Ảo Giác AI
# =============================================================================
class S1E1Scene07ConfidenceTrapECE(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self)
        header = create_hud_header("HIỆU CHUẨN XÁC SUẤT (ECE) & ẢO GIÁC AI")
        self.add(header)

        # Telemetry Card (Right 42%)
        card_bg = RoundedRectangle(corner_radius=0.15, width=4.8, height=4.2, stroke_color=COLOR_BORDER, stroke_width=1.5, fill_color=COLOR_CARD_BG, fill_opacity=0.92)
        card_bg.move_to(np.array([3.4, 0.4, 0]))
        hud_title = Text("SAI SỐ HIỆU CHUẨN KỲ VỌNG (ECE)", font=FONT_FAMILY, font_size=13, weight=BOLD, color=COLOR_ROSE)
        hud_title.next_to(card_bg.get_top(), DOWN, buff=0.25)

        ece_formula = MathTex(
            r"\text{ECE} = \sum_{m=1}^M \frac{|B_m|}{N} \left| \text{acc}(B_m) - \text{conf}(B_m) \right|",
            font_size=17, color=COLOR_ROSE
        ).next_to(hud_title, DOWN, buff=0.25)

        badge_warn = VGroup(
            Text("Overconfidence Gap", font=FONT_FAMILY, font_size=12, weight=BOLD, color=COLOR_ROSE),
            MathTex(r"\text{Confidence} \approx 99.4\% \gg \text{Accuracy}", font_size=15, color=COLOR_TEXT),
            Text("Out-of-Distribution Shift", font=FONT_FAMILY, font_size=12, weight=BOLD, color=COLOR_AMBER),
            MathTex(r"P_{\text{train}}(x) \neq P_{\text{test}}(x)", font_size=15, color=COLOR_TEXT)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.16).next_to(ece_formula, DOWN, buff=0.25)

        hud_group = VGroup(card_bg, hud_title, ece_formula, badge_warn)
        self.play(FadeIn(hud_group, shift=LEFT*0.2), run_time=2.0)

        # Hero Stage: Reliability Diagram (Accuracy vs Confidence)
        axes = Axes(
            x_range=[0, 1.0, 0.2], y_range=[0, 1.0, 0.2],
            x_length=4.5, y_length=3.5,
            axis_config={"color": COLOR_BORDER, "stroke_width": 1.5}
        ).move_to(np.array([-2.8, 0.2, 0]))

        diag_line = Line(axes.c2p(0, 0), axes.c2p(1, 1), stroke_color=COLOR_EMERALD, stroke_width=2.5)
        ideal_lbl = Text("Hiệu chuẩn lý tưởng (acc = conf)", font=FONT_FAMILY, font_size=10, color=COLOR_EMERALD).next_to(diag_line, UP, buff=0.1).rotate(38*DEGREES)

        self.play(Create(axes), Create(diag_line), FadeIn(ideal_lbl), run_time=2.5)

        # Overconfidence Defect Region
        defect_pts = [
            axes.c2p(0.6, 0.6), axes.c2p(1.0, 1.0),
            axes.c2p(1.0, 0.45), axes.c2p(0.6, 0.35)
        ]
        poly_defect = Polygon(*defect_pts, fill_color=COLOR_ROSE, fill_opacity=0.45, stroke_color=COLOR_ROSE, stroke_width=2.0)
        gap_lbl = Text("Overconfidence Gap", font=FONT_FAMILY, font_size=12, weight=BOLD, color=COLOR_ROSE).move_to(poly_defect.get_center())

        self.play(FadeIn(poly_defect), Write(gap_lbl), run_time=4.0)

        # Flashing Alarm Ripple
        pulse = Circle(radius=0.1, stroke_color=COLOR_ROSE, stroke_width=3.0).move_to(axes.c2p(0.95, 0.5))
        for _ in range(3):
            self.play(pulse.animate.scale(6).set_stroke(opacity=0), run_time=2.0)
            pulse.scale(1/6).set_stroke(opacity=1.0)

        remaining_time = max(1.0, 68.91 - 20.5)
        self.wait(remaining_time)

# =============================================================================
# SCENE 08: S1E1Scene08OceanOfUncertainty (~63.66s)
# Đại Dương Bất Định & Điểm Giao Thoa Nhận Thức Nhân - Máy
# =============================================================================
class S1E1Scene08OceanOfUncertainty(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self)
        header = create_hud_header("ĐẠI DƯƠNG BẤT ĐỊNH & KHÁT VỌNG TRI THỨC")
        self.add(header)

        # Telemetry Card (Right 42%) — Curiosity Bridge to S1E2
        card_bg = RoundedRectangle(corner_radius=0.15, width=4.8, height=4.2, stroke_color=COLOR_GOLD, stroke_width=2.0, fill_color=COLOR_CARD_BG, fill_opacity=0.94)
        card_bg.move_to(np.array([3.4, 0.4, 0]))
        hud_title = Text("HẸN GẶP LẠI Ở TẬP 02", font=FONT_FAMILY, font_size=14, weight=BOLD, color=COLOR_GOLD)
        hud_title.next_to(card_bg.get_top(), DOWN, buff=0.25)

        t_next = Text("GIẢI TÍCH & GRADIENT DESCENT", font=FONT_FAMILY, font_size=12, weight=BOLD, color=COLOR_CYAN)
        t_next.next_to(hud_title, DOWN, buff=0.2)

        eq_grad = MathTex(r"\theta_{t+1} = \theta_t - \eta \nabla_\theta \mathcal{L}(\theta)", font_size=17, color=COLOR_GOLD)
        eq_grad.next_to(t_next, DOWN, buff=0.25)

        desc = Text("La Bàn Toán Học Vạn Chiều", font=FONT_FAMILY, font_size=12, color=COLOR_TEXT).next_to(eq_grad, DOWN, buff=0.2)

        hud_group = VGroup(card_bg, hud_title, t_next, eq_grad, desc)
        self.play(FadeIn(hud_group, shift=LEFT*0.2), run_time=2.0)

        # Hero Stage: Loss Landscape Valley with Vector Compass
        axes = Axes(
            x_range=[-3, 3, 1], y_range=[-2, 2, 1],
            x_length=5.6, y_length=3.5,
            axis_config={"color": COLOR_BORDER, "stroke_width": 1.2}
        ).move_to(np.array([-2.8, 0.2, 0]))
        self.play(Create(axes), run_time=1.5)

        # Contour lines of Loss Landscape
        contours = VGroup()
        for r in [0.6, 1.2, 1.8, 2.4]:
            c = Ellipse(width=r*1.8, height=r*1.1, stroke_color=COLOR_CYAN, stroke_width=1.5).move_to(axes.c2p(0, 0))
            contours.add(c)
        self.play(Create(contours), run_time=3.0)

        # Compass Needle pointing towards Global Minimum (0, 0)
        angle_t = ValueTracker(PI)
        needle = always_redraw(lambda: Arrow(
            start=axes.c2p(1.8*math.cos(angle_t.get_value()), 1.2*math.sin(angle_t.get_value())),
            end=axes.c2p(0, 0),
            color=COLOR_GOLD, stroke_width=3.5, max_tip_length_to_length_ratio=0.3
        ))
        center_star = Dot(point=axes.c2p(0, 0), radius=0.15, color=COLOR_GOLD)

        self.add(needle, center_star)
        self.play(angle_t.animate.set_value(0.0), run_time=15.0, rate_func=smooth)

        # Subtle wave oscillations to fill 63.66s
        remaining_time = max(1.0, 63.66 - 21.5)
        self.wait(remaining_time)
