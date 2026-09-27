#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Manim 2K Mathematical Engine — Series 2, Episode 25: The Future of AGI (Grand Finale)
======================================================================================
Pedagogical Identity:
- 3Blue1Brown/Median continuous mathematical flow
- Zero mascots, zero static bullet lists, zero slide-deck paragraph boxes
- Clean ASCII MathTex (zero non-ASCII in LaTeX math mode)
- Safe padding: |x| <= 5.2, |y| <= 3.2 (Outro mosaic safe in [-6.20, +6.20], [-2.00, +3.30])
- Top-right ZenPham brand watermark intact
- No FadeOut at end of scenes (preserves cloned visual state for FFmpeg tpad)
- 2K QHD 60fps standard canvas (2560x1440 @ 60fps)
"""

from __future__ import annotations

import os
from pathlib import Path
import sys
from manim import *
import numpy as np

# Ensure assets/scripts_video is in sys.path
SCRIPTS_DIR = Path(__file__).resolve().parents[2]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

try:
    from manim_production import (
        DEFAULT_FONT,
        create_wrapped_card_text,
        fit_math_to_card,
        create_hairline_axes,
        create_elegant_arrow,
        create_elegant_dot,
    )
except ImportError:
    DEFAULT_FONT = "Be Vietnam Pro"
    create_wrapped_card_text = None
    fit_math_to_card = None

if create_wrapped_card_text is None:
    def create_wrapped_card_text(text, card, font=DEFAULT_FONT, font_size=12.0, color=None, weight=None, **kwargs):
        return Text(text, font=font, font_size=font_size, color=color, weight=weight or NORMAL)

if fit_math_to_card is None:
    def fit_math_to_card(latex, card, font_size=24.0, color=None, **kwargs):
        return MathTex(latex, font_size=font_size, color=color)

# -----------------------------------------------------------------------------
# DESIGN SYSTEM TOKENS — NEO-NOIR TECH MINIMALIST
# -----------------------------------------------------------------------------
COLOR_BG = "#0c0d12"
COLOR_PANEL = "#161b26"
COLOR_TEXT = "#e2e8f0"
COLOR_MUTED = "#64748b"
COLOR_CYAN = "#00e5ff"
COLOR_GOLD = "#ffb300"
COLOR_GREEN = "#00e676"
COLOR_ROSE = "#ff2a6d"
COLOR_VIOLET = "#a78bfa"

# 2K QHD 60fps Canvas Configuration
config.background_color = COLOR_BG
config.pixel_width = 2560
config.pixel_height = 1440
config.frame_width = 14.22
config.frame_height = 8.0
config.frame_rate = 60


def add_zenpham_brand(scene: Scene, ep_title: str):
    """Adds ZenPham top-right watermark and top pill header."""
    brand = Text("ZENPHAM", font=DEFAULT_FONT, font_size=13.0, weight=BOLD, color=COLOR_GOLD)
    sub = Text("KỸ NGHỆ LLM TỐI TÂN", font=DEFAULT_FONT, font_size=12.0, color=COLOR_MUTED).next_to(brand, DOWN, buff=0.06)
    watermark = VGroup(brand, sub).to_corner(UR, buff=0.45)

    badge_bg = RoundedRectangle(
        corner_radius=0.12, height=0.46, width=8.5,
        fill_color=COLOR_PANEL, fill_opacity=0.9, stroke_color=COLOR_CYAN, stroke_width=1.0
    )
    badge_bg.to_edge(UP, buff=0.35)
    badge_header = Text(f"ZENPHAM // TÔI LÀM VIỆC — {ep_title}", font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_TEXT)
    badge_header.move_to(badge_bg.get_center())

    scene.add(watermark, badge_bg, badge_header)


# ==============================================================================
# SCENE 1: COLD OPEN — RETROSPECTIVE 25 EPISODES & 24-FACET CRYSTAL ASSEMBLY
# ==============================================================================
class Tap25Scene01ColdOpen(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "ĐẠI KẾT SERIES 2 & CHÂN TRỜI AGI")

        scene_title = Text(
            "HÀNH TRÌNH 25 TẬP KỸ NGHỆ LLM & BƯỚC NGOẶT AGI",
            font=DEFAULT_FONT, font_size=18.0, weight=BOLD, color=COLOR_GOLD
        )
        scene_title.to_edge(UP, buff=0.95)
        self.play(FadeIn(scene_title, shift=DOWN * 0.2), run_time=0.8)

        # 24-Facet Crystal Assembly converging into a radiant unified core
        colors = [COLOR_CYAN, COLOR_GOLD, COLOR_VIOLET, COLOR_GREEN]
        facets = VGroup()
        radial_lines = VGroup()

        # Center radiant core representing the grand synthesis
        core_glow = Circle(
            radius=0.6, stroke_color=COLOR_GOLD, stroke_width=2.0,
            fill_color=COLOR_PANEL, fill_opacity=0.85
        )
        core_inner = Circle(
            radius=0.38, stroke_color=COLOR_CYAN, stroke_width=1.5,
            fill_color=COLOR_BG, fill_opacity=0.95
        )
        core_dot = Dot(radius=0.12, color=COLOR_GOLD)
        core_math = MathTex(
            r"\mathcal{S}_{\text{AGI}} = \bigoplus_{i=1}^{24} \mathcal{M}_i",
            font_size=24.0, color=COLOR_GOLD
        )
        core_group = VGroup(core_glow, core_inner, core_dot, core_math).move_to(ORIGIN + DOWN * 0.3)

        # 24 facets in 2 concentric rings representing the 24 prior episodes
        radii = [3.2] * 16 + [2.0] * 8
        angles = [i * TAU / 16 for i in range(16)] + [j * TAU / 8 + TAU / 16 for j in range(8)]

        for idx in range(24):
            r = radii[idx]
            ang = angles[idx]
            pos = core_group.get_center() + np.array([r * np.cos(ang), r * np.sin(ang), 0.0])
            col = colors[idx % len(colors)]
            poly = RegularPolygon(
                n=6, radius=0.14, color=col, stroke_width=1.5,
                fill_color=col, fill_opacity=0.35
            )
            poly.move_to(pos)
            line = DashedLine(
                start=pos, end=core_group.get_center(),
                stroke_color=col, stroke_width=1.0, stroke_opacity=0.45
            )
            facets.add(poly)
            radial_lines.add(line)

        self.play(
            LaggedStart(*[FadeIn(f, scale=0.5) for f in facets], lag_ratio=0.04),
            Create(radial_lines),
            run_time=2.0,
        )

        tracker = ValueTracker(1.0)
        self.play(FadeIn(core_group), run_time=1.0)

        # Dynamic contraction of 24 facets into radiant unified core
        converge_targets = []
        for idx in range(24):
            ang = angles[idx]
            target_pos = core_group.get_center() + np.array([0.75 * np.cos(ang), 0.75 * np.sin(ang), 0.0])
            t_poly = RegularPolygon(
                n=6, radius=0.08, color=colors[idx % len(colors)],
                stroke_width=1.2, fill_opacity=0.85
            )
            t_poly.move_to(target_pos)
            converge_targets.append(t_poly)

        self.play(
            *[Transform(facets[i], converge_targets[i]) for i in range(24)],
            FadeOut(radial_lines),
            tracker.animate.set_value(2.0),
            run_time=2.5,
        )

        pulse = Annulus(
            inner_radius=0.6, outer_radius=1.8,
            stroke_color=COLOR_CYAN, stroke_width=2.0, fill_opacity=0.15
        )
        pulse.move_to(core_group.get_center())

        callout_header = Text(
            "24 MẮT XÍCH KỸ NGHỆ HỘI TỤ THÀNH KHỐI AGI ĐẠI KẾT",
            font=DEFAULT_FONT, font_size=13.0, weight=BOLD, color=COLOR_CYAN
        )
        callout_header.to_edge(DOWN, buff=0.45)

        self.play(
            Create(pulse),
            FadeIn(callout_header, shift=UP * 0.2),
            Flash(core_group, color=COLOR_GOLD, line_length=0.35),
            run_time=1.5,
        )
        self.wait(1.5)


# ==============================================================================
# SCENE 2: ARCHITECTURE — RECURSIVE OODA & RUNAWAY SINGULARITY LOOP
# ==============================================================================
class Tap25Scene02Architecture(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "VÒNG LẶP TỰ CẢI TIẾN ĐỆ QUY")

        scene_title = Text(
            "VÒNG LẶP TỰ HOÀN THIỆN ĐỆ QUY: TỪ PHÂN TÍCH ĐẾN TỰ BIÊN DỊCH KERNEL",
            font=DEFAULT_FONT, font_size=16.5, weight=BOLD, color=COLOR_CYAN
        )
        scene_title.to_edge(UP, buff=0.95)
        self.play(FadeIn(scene_title, shift=DOWN * 0.2), run_time=0.8)

        # Exponential Singularity Differential Equation
        math_singularity = MathTex(
            r"\frac{dI}{dt} = k \cdot I^\alpha, \quad \alpha > 1",
            font_size=28.0, color=COLOR_GOLD
        )
        math_singularity.move_to(UP * 1.7)
        self.play(Write(math_singularity), run_time=1.0)

        # 4 Cyclic Nodes: Profiling -> NAS Search -> Kernel Gen -> Deployment
        steps = [
            ("1. PROFILING", COLOR_ROSE, LEFT * 4.5),
            ("2. NAS SEARCH", COLOR_GOLD, LEFT * 1.5),
            ("3. KERNEL GEN", COLOR_CYAN, RIGHT * 1.5),
            ("4. DEPLOYMENT", COLOR_GREEN, RIGHT * 4.5),
        ]

        nodes = []
        for header, col, x_pos in steps:
            outer_ring = Circle(
                radius=0.82, stroke_color=col, stroke_width=2.0,
                fill_color=COLOR_PANEL, fill_opacity=0.9
            )
            inner_ring = Circle(
                radius=0.68, stroke_color=col, stroke_width=1.0, stroke_opacity=0.6
            )
            node_header = Text(header, font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=col)
            node_header.move_to(outer_ring.get_center())
            node_grp = VGroup(outer_ring, inner_ring, node_header).move_to(x_pos + DOWN * 0.2)
            nodes.append(node_grp)

        self.play(*[FadeIn(n, shift=UP * 0.3) for n in nodes], run_time=1.0)

        # Forward Aerodynamic Arrows (tip_length=0.16 <= 0.20)
        arrows = []
        for i in range(len(nodes) - 1):
            arr = Arrow(
                start=nodes[i][0].get_right(),
                end=nodes[i + 1][0].get_left(),
                buff=0.12,
                color=COLOR_GOLD,
                stroke_width=2.5,
                tip_length=0.16,
            )
            arrows.append(arr)
        self.play(*[GrowArrow(a) for a in arrows], run_time=0.8)

        # Reverse Feedback Curved Arrow (angle <= 0 to avoid collision with nodes)
        rec_arrow = CurvedArrow(
            start_point=nodes[3][0].get_bottom() + DOWN * 0.15,
            end_point=nodes[0][0].get_bottom() + DOWN * 0.15,
            angle=-TAU / 4.5,
            color=COLOR_CYAN,
            stroke_width=2.5,
            tip_length=0.16,
        )
        rec_header = Text("Vòng lặp tự hoàn thiện đệ quy: Gia tốc trí tuệ", font=DEFAULT_FONT, font_size=12.0, color=COLOR_CYAN)
        rec_header.next_to(rec_arrow, DOWN, buff=0.12)
        self.play(Create(rec_arrow), FadeIn(rec_header), run_time=1.0)

        # Accelerating Parameter Tracker pulse along the loop
        speed_tracker = ValueTracker(0.0)
        pulse_dot = Dot(color=COLOR_GOLD, radius=0.1)
        pulse_dot.move_to(nodes[0].get_center())
        self.play(FadeIn(pulse_dot), speed_tracker.animate.set_value(1.0), run_time=1.0)

        loop_header = Text(
            "CHU TRÌNH TỰ ĐỘNG KHÉP KÍN: TỐC ĐỘ TIẾN HÓA BÙNG NỔ HÀM MŨ",
            font=DEFAULT_FONT, font_size=13.0, weight=BOLD, color=COLOR_GREEN
        )
        loop_header.to_edge(DOWN, buff=0.45)
        self.play(FadeIn(loop_header, shift=UP * 0.2), run_time=0.8)
        self.wait(1.5)


# ==============================================================================
# SCENE 3: MATHEMATICS — EXPONENTIAL SINGULARITY CURVE & TANGENT VECTORS
# ==============================================================================
class Tap25Scene03Mathematics(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "TOÁN HỌC CĂN CHỈNH GIÁ TRỊ")

        scene_title = Text(
            "TOÁN HỌC AN TOÀN AGI: HỘI TỤ VỀ TẬP GIÁ TRỊ CON NGƯỜI",
            font=DEFAULT_FONT, font_size=17.0, weight=BOLD, color=COLOR_GOLD
        )
        scene_title.to_edge(UP, buff=0.95)
        self.play(FadeIn(scene_title, shift=DOWN * 0.2), run_time=0.8)

        # Left Side: Exponential Singularity Curve on Axes
        axes = Axes(
            x_range=[0, 5, 1],
            y_range=[0, 10, 2],
            x_length=5.6,
            y_length=3.8,
            axis_config={"color": COLOR_MUTED, "stroke_width": 1.5},
        ).move_to(LEFT * 3.0 + DOWN * 0.35)

        x_header = Text("Thời gian t", font=DEFAULT_FONT, font_size=12.0, color=COLOR_TEXT).next_to(axes.x_axis.get_end(), DOWN, buff=0.15)
        y_header = Text("Trí tuệ I(t)", font=DEFAULT_FONT, font_size=12.0, color=COLOR_TEXT).next_to(axes.y_axis.get_end(), LEFT, buff=0.15)
        self.play(Create(axes), FadeIn(x_header), FadeIn(y_header), run_time=1.0)

        # Plot Singularity Curve: I(t) = 0.18 * exp(0.82 * t)
        singularity_curve = axes.plot(
            lambda t: 0.18 * np.exp(0.82 * t),
            x_range=[0, 4.8],
            color=COLOR_CYAN,
            stroke_width=3.0,
        )
        self.play(Create(singularity_curve), run_time=1.2)

        # Dynamic Tangent Vector & ValueTracker
        t_tracker = ValueTracker(2.0)
        curve_dot = always_redraw(
            lambda: Dot(
                axes.c2p(t_tracker.get_value(), 0.18 * np.exp(0.82 * t_tracker.get_value())),
                color=COLOR_GOLD,
                radius=0.1,
            )
        )
        tangent_arrow = always_redraw(
            lambda: Arrow(
                start=curve_dot.get_center(),
                end=curve_dot.get_center() + RIGHT * 0.9 + UP * (0.9 * 0.82 * 0.18 * np.exp(0.82 * t_tracker.get_value()) / 2.2),
                buff=0,
                color=COLOR_ROSE,
                stroke_width=2.5,
                tip_length=0.16,
            )
        )
        self.add(curve_dot, tangent_arrow)
        self.play(t_tracker.animate.set_value(4.2), run_time=2.0)

        # Right Side: Alignment Mathematical Constraints
        right_box = RoundedRectangle(
            corner_radius=0.15, width=5.0, height=4.0,
            fill_color=COLOR_PANEL, fill_opacity=0.85, stroke_color=COLOR_CYAN, stroke_width=1.5
        ).move_to(RIGHT * 3.0 + DOWN * 0.35)

        card_header = create_wrapped_card_text(
            "ĐIỀU KIỆN HỘI TỤ AN TOÀN TUYỆT ĐỐI",
            right_box,
            font=DEFAULT_FONT,
            font_size=12.0,
            color=COLOR_CYAN,
            weight=BOLD,
        )
        card_header.next_to(right_box.get_top(), DOWN, buff=0.25)

        math1 = fit_math_to_card(
            r"\frac{dI}{dt} = k \cdot I^\alpha, \quad \alpha > 1",
            right_box,
            font_size=26.0,
            color=COLOR_GOLD,
        )
        math1.next_to(card_header, DOWN, buff=0.35)

        math2 = fit_math_to_card(
            r"\lim_{t \to \infty} D_{\text{KL}}(\pi_t \parallel \pi^*) = 0",
            right_box,
            font_size=26.0,
            color=COLOR_CYAN,
        )
        math2.next_to(math1, DOWN, buff=0.35)

        math3 = fit_math_to_card(
            r"\max_{\pi} \mathbb{E}[R] - \beta \cdot \text{Risk}(\pi)",
            right_box,
            font_size=24.0,
            color=COLOR_GREEN,
        )
        math3.next_to(math2, DOWN, buff=0.35)

        r_grp = VGroup(right_box, card_header, math1, math2, math3)
        self.play(FadeIn(r_grp, shift=LEFT * 0.3), run_time=1.0)

        math_header = Text(
            "BẢO TOÀN GIÁ TRỊ NHÂN BẢN: ĐIỀU KIỆN TIÊN QUYẾT CHO AGI",
            font=DEFAULT_FONT, font_size=13.0, weight=BOLD, color=COLOR_CYAN
        )
        math_header.to_edge(DOWN, buff=0.45)
        self.play(FadeIn(math_header, shift=UP * 0.2), run_time=0.8)
        self.wait(1.5)


# ==============================================================================
# SCENE 4: TELEMETRY — STATE-SPACE CONTINUOUS FLOW & TEST-TIME COMPUTE
# ==============================================================================
class Tap25Scene04Telemetry(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "ĐO KIỂM TEST-TIME COMPUTE")

        scene_title = Text(
            "CHUYỂN TRỤC KIẾN TRÚC: PRE-TRAINING SANG TEST-TIME COMPUTE",
            font=DEFAULT_FONT, font_size=16.5, weight=BOLD, color=COLOR_CYAN
        )
        scene_title.to_edge(UP, buff=0.95)
        self.play(FadeIn(scene_title, shift=DOWN * 0.2), run_time=0.8)

        # Left Side: Continuous State-Space Vector Field Flow
        axes = Axes(
            x_range=[-3, 3, 1],
            y_range=[-2, 2, 1],
            x_length=5.6,
            y_length=3.8,
            axis_config={"color": COLOR_MUTED, "stroke_width": 1.2},
        ).move_to(LEFT * 3.0 + DOWN * 0.35)

        def flow_func(pos):
            return np.array([-pos[1] - 0.35 * pos[0], pos[0] - 0.35 * pos[1], 0.0])

        flow_field = ArrowVectorField(
            flow_func,
            x_range=[-2.6, 2.6, 0.65],
            y_range=[-1.6, 1.6, 0.65],
            length_func=lambda norm: 0.22,
            colors=[COLOR_CYAN, COLOR_VIOLET, COLOR_GOLD],
        )
        flow_field.move_to(axes.get_center())

        field_header = Text("Trường vector không gian trạng thái", font=DEFAULT_FONT, font_size=12.0, color=COLOR_MUTED)
        field_header.next_to(axes, DOWN, buff=0.15)
        self.play(Create(axes), Create(flow_field), FadeIn(field_header), run_time=1.8)

        # Right Side: Test-Time Compute Scaling Metrics
        right_panel = RoundedRectangle(
            corner_radius=0.15, width=5.0, height=4.0,
            fill_color=COLOR_PANEL, fill_opacity=0.85, stroke_color=COLOR_GOLD, stroke_width=1.5
        ).move_to(RIGHT * 3.0 + DOWN * 0.35)

        card_header = create_wrapped_card_text(
            "QUY LUẬT TỶ LỆ TÍNH TOÁN SUY LUẬN",
            right_panel,
            font=DEFAULT_FONT,
            font_size=12.0,
            color=COLOR_GOLD,
            weight=BOLD,
        )
        card_header.next_to(right_panel.get_top(), DOWN, buff=0.25)

        math_scaling = fit_math_to_card(
            r"\text{Accuracy}(C_{\text{test}}) \propto \log(C_{\text{test}})",
            right_panel,
            font_size=24.0,
            color=COLOR_GOLD,
        )
        math_scaling.next_to(card_header, DOWN, buff=0.35)

        # Live Accuracy Counter via ValueTracker
        acc_tracker = ValueTracker(32.0)
        acc_label = Text("Frontier Reasoning Benchmark:", font=DEFAULT_FONT, font_size=12.0, color=COLOR_TEXT)
        acc_label.next_to(math_scaling, DOWN, buff=0.45)

        acc_val = always_redraw(
            lambda: DecimalNumber(
                acc_tracker.get_value(),
                num_decimal_places=1,
                unit="\\%",
                font_size=32.0,
                color=COLOR_GREEN,
            ).next_to(acc_label, DOWN, buff=0.2)
        )

        r_grp = VGroup(right_panel, card_header, math_scaling, acc_label, acc_val)
        self.play(FadeIn(r_grp), run_time=1.0)
        self.play(acc_tracker.animate.set_value(92.4), run_time=2.2)

        telemetry_header = Text(
            "CHIẾN THẮNG CỦA THUẬT TOÁN TINH GỌN: SUY NGHĨ SÂU ĐÁNH BẠI QUY MÔ",
            font=DEFAULT_FONT, font_size=13.0, weight=BOLD, color=COLOR_GOLD
        )
        telemetry_header.to_edge(DOWN, buff=0.45)
        self.play(FadeIn(telemetry_header, shift=UP * 0.2), run_time=0.8)
        self.wait(1.5)


# ==============================================================================
# SCENE 5: LAB EXPERIMENT — DIGITAL CRAFTSMANSHIP & 3 GEOMETRIC PILLARS
# ==============================================================================
class Tap25Scene05LabExperiment(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "THỰC NGHIỆM LAB INNORIA")

        scene_title = Text(
            "TRIẾT LÝ INNORIA: TÂM THẾ NGƯỜI THỦ CÔNG SỐ TRONG KỶ NGUYÊN AGI",
            font=DEFAULT_FONT, font_size=16.5, weight=BOLD, color=COLOR_GOLD
        )
        scene_title.to_edge(UP, buff=0.95)
        self.play(FadeIn(scene_title, shift=DOWN * 0.2), run_time=0.8)

        # 3 Triad Vertices representing the 3 Foundations of Digital Craftsmanship
        p1 = UP * 1.5 + LEFT * 3.6
        p2 = UP * 1.5 + RIGHT * 3.6
        p3 = DOWN * 1.1 + ORIGIN

        triad_lines = Polygon(p1, p2, p3, stroke_color=COLOR_GOLD, stroke_width=2.0, stroke_opacity=0.6)
        self.play(Create(triad_lines), run_time=1.0)

        pillars = [
            ("TRỤ CỘT 1: TOÁN HỌC", r"\mathcal{H}_{\text{math}}", COLOR_CYAN, p1),
            ("TRỤ CỘT 2: SẢN PHẨM", r"\mathcal{P}_{\text{prod}}", COLOR_VIOLET, p2),
            ("TRỤ CỘT 3: TÂM NGHỀ", r"\mathcal{C}_{\text{craft}}", COLOR_GREEN, p3),
        ]

        nodes = []
        for header, formula, col, pos in pillars:
            c_outer = Circle(radius=0.72, stroke_color=col, stroke_width=2.0, fill_color=COLOR_PANEL, fill_opacity=0.9)
            c_outer.move_to(pos)
            c_math = MathTex(formula, font_size=28.0, color=col)
            c_math.move_to(pos)
            c_header = Text(header, font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=col)
            c_header.next_to(c_outer, UP if pos[1] > 0 else DOWN, buff=0.15)
            nodes.append(VGroup(c_outer, c_math, c_header))

        self.play(*[FadeIn(n, scale=0.8) for n in nodes], run_time=1.2)

        # Center Diamond Core: Craftsmanship Optimum
        center_core = RegularPolygon(
            n=4, radius=0.65, stroke_color=COLOR_GOLD, stroke_width=2.0,
            fill_color=COLOR_BG, fill_opacity=0.95
        )
        center_core.move_to(UP * 0.4)
        center_math = MathTex(r"\nabla_{\theta} \mathcal{L} = 0", font_size=26.0, color=COLOR_GOLD)
        center_math.move_to(center_core.get_center())
        center_grp = VGroup(center_core, center_math)

        glow_tracker = ValueTracker(1.0)
        self.play(FadeIn(center_grp), Flash(center_grp, color=COLOR_GOLD), run_time=1.0)

        craft_header = Text(
            "ĐẠO LÀM NGHỀ: GIỮ TRỌN TÂM THẾ NGƯỜI THỦ CÔNG ĐỂ TẠO GIÁ TRỊ BẤT BIẾN",
            font=DEFAULT_FONT, font_size=13.0, weight=BOLD, color=COLOR_GOLD
        )
        craft_header.to_edge(DOWN, buff=0.45)
        self.play(FadeIn(craft_header, shift=UP * 0.2), glow_tracker.animate.set_value(2.0), run_time=0.8)
        self.wait(1.5)


# ==============================================================================
# SCENE 6: OUTRO — 5x5 THUMBNAIL MOSAIC & YOUTUBE SAFE ZONE CLOSING CTA
# ==============================================================================
class Tap25Scene06Outro(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "KHÉP LẠI SERIES 2 & CHÀO ĐÓN SERIES 3")

        scene_title = Text(
            "ĐẠI KẾT SERIES 2 // 25 TẬP KỸ NGHỆ LLM TỐI TÂN",
            font=DEFAULT_FONT, font_size=17.0, weight=BOLD, color=COLOR_GOLD
        )
        scene_title.to_edge(UP, buff=0.95)
        self.play(FadeIn(scene_title, shift=DOWN * 0.2), run_time=0.8)

        # Left Side: Ingest 5x5 Closing Thumbnail Mosaic
        # Relative and absolute paths for host and container environments
        mosaic_rel = Path("assets/brand/zenpham-brand-kit/series2_25_thumbnails_mosaic.png")
        mosaic_abs = Path("/home/zen/hermes-agent") / mosaic_rel
        mosaic_work = Path("/work") / mosaic_rel
        mosaic_file = (
            mosaic_work if mosaic_work.exists()
            else mosaic_abs if mosaic_abs.exists()
            else mosaic_rel
        )

        # YouTube safe zone compliance:
        # Constrained strictly to X in [-6.20, +6.20], Y in [-2.00, +3.30]
        # Mosaic width=5.8 centered at X=-3.2 -> X in [-6.10, -0.30] (safe)
        # Height=3.38 centered at Y=0.55 -> Y in [-1.14, +2.24] (safe)
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
            font=DEFAULT_FONT, font_size=12.5, weight=BOLD, color=COLOR_GOLD
        )
        gallery_header.next_to(mosaic_frame, UP, buff=0.18)

        left_grp = Group(mosaic_mobj, mosaic_frame, gallery_header)
        self.play(FadeIn(left_grp, shift=RIGHT * 0.3), run_time=1.2)

        # Right Side: YouTube End Screen Interactive Safe Zones
        # 1. Next Video Card: X in [+1.6, +5.4], Y in [+0.5, +2.5]
        next_card = RoundedRectangle(
            corner_radius=0.12, width=3.8, height=2.0,
            fill_color=COLOR_PANEL, fill_opacity=0.7, stroke_color=COLOR_CYAN, stroke_width=1.5
        ).move_to(RIGHT * 3.5 + UP * 1.5)
        next_header = Text("VIDEO TIẾP THEO // SERIES 3", font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_CYAN)
        next_header.move_to(next_card.get_center())

        # 2. Playlist Card: X in [+1.6, +5.4], Y in [-1.0, +0.3]
        pl_card = RoundedRectangle(
            corner_radius=0.12, width=3.8, height=1.3,
            fill_color=COLOR_PANEL, fill_opacity=0.7, stroke_color=COLOR_GOLD, stroke_width=1.5
        ).move_to(RIGHT * 3.5 + DOWN * 0.35)
        pl_header = Text("PLAYLIST TRỌN BỘ 25 TẬP", font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_GOLD)
        pl_header.move_to(pl_card.get_center())

        # 3. Channel Subscribe Avatar: Circle at X=+3.5, Y=-1.65
        sub_circle = Circle(
            radius=0.52, fill_color=COLOR_BG, fill_opacity=0.9, stroke_color=COLOR_GOLD, stroke_width=1.5
        ).move_to(RIGHT * 3.5 + DOWN * 1.65)
        sub_header = Text("ZEN", font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_GOLD)
        sub_header.move_to(sub_circle.get_center())

        right_grp = VGroup(next_card, next_header, pl_card, pl_header, sub_circle, sub_header)
        self.play(FadeIn(right_grp, shift=LEFT * 0.3), run_time=1.0)

        # Bottom Series 3 Teaser Announcement
        series3_header = Text(
            "HẸN GẶP LẠI TRONG SERIES 3: KỸ NGHỆ AUTONOMOUS AGENT TỰ HÀNH",
            font=DEFAULT_FONT, font_size=12.5, weight=BOLD, color=COLOR_CYAN
        )
        series3_header.to_edge(DOWN, buff=0.45)
        self.play(FadeIn(series3_header, shift=UP * 0.2), run_time=0.8)
        self.wait(2.0)
