#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Manim 2K Mathematical Engine — Series 2, Episode 20: Hallucination & Probing
============================================================================
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

import math
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
        ZenArrow,
        ZenCurvedArrow,
    )
    _MANIM_PRODUCTION_OK = True
except ImportError:
    _MANIM_PRODUCTION_OK = False
    DEFAULT_FONT = "Be Vietnam Pro"

    def create_wrapped_card_text(text, card, font=DEFAULT_FONT, font_size=24.0, color=None, weight=None, **kwargs):
        from manim import Text, NORMAL
        t = Text(text, font=font, font_size=font_size, color=color or "#e2e8f0", weight=weight or NORMAL)
        max_w = getattr(card, "width", 6.0) * 0.86
        if t.width > max_w:
            t.scale_to_fit_width(max_w)
        return t

    def fit_math_to_card(latex, card, font_size=28.0, color=None, **kwargs):
        from manim import MathTex
        m = MathTex(latex, font_size=font_size, color=color or "#e2e8f0")
        max_w = getattr(card, "width", 6.0) * 0.86
        if m.width > max_w:
            m.scale_to_fit_width(max_w)
        return m

    def create_hairline_axes(x_range=(-1, 1, 0.5), y_range=(-1, 1, 0.5),
                             x_length=4.0, y_length=3.0, axis_color="#64748b",
                             stroke_width=1.2, include_ticks=True, **kwargs):
        from manim import Line, VGroup, ORIGIN
        import numpy as _np
        x_min, x_max, x_step = x_range
        y_min, y_max, y_step = y_range
        x_ax = Line(_np.array([0, 0, 0]), _np.array([x_length, 0, 0]), color=axis_color, stroke_width=stroke_width)
        y_ax = Line(_np.array([0, 0, 0]), _np.array([0, y_length, 0]), color=axis_color, stroke_width=stroke_width)
        return VGroup(x_ax, y_ax).move_to(ORIGIN)

    def create_elegant_arrow(start, end, color="#00e5ff", stroke_width=2.0,
                             tip_length=0.18, buff=0.05, **kwargs):
        from manim import Arrow
        import numpy as _np
        return Arrow(
            start=_np.array(start) if not isinstance(start, _np.ndarray) else start,
            end=_np.array(end) if not isinstance(end, _np.ndarray) else end,
            color=color, stroke_width=stroke_width,
            tip_length=min(float(tip_length), 0.20), buff=buff,
        )

    def create_elegant_dot(point=None, radius=0.07, color="#00e5ff",
                           fill_opacity=1.0, stroke_width=0.0, **kwargs):
        from manim import Dot, ORIGIN
        import numpy as _np
        pos = _np.array(point) if point is not None else ORIGIN
        return Dot(point=pos, radius=radius, color=color,
                   fill_opacity=fill_opacity, stroke_width=stroke_width)

    def ZenArrow(start=None, end=None, color="#00e5ff", stroke_width=2.4,
                 buff=0.08, **kwargs):
        from manim import Arrow, LEFT, RIGHT
        import numpy as _np
        s = _np.array(start) if start is not None and not isinstance(start, _np.ndarray) else (start if start is not None else LEFT)
        e = _np.array(end) if end is not None and not isinstance(end, _np.ndarray) else (end if end is not None else RIGHT)
        return Arrow(start=s, end=e, color=color, stroke_width=stroke_width,
                     tip_length=0.18, buff=buff)

    def ZenCurvedArrow(start_point, end_point, color="#00e5ff", stroke_width=2.4,
                       angle=0.3, **kwargs):
        from manim import CurvedArrow
        import numpy as _np
        s = _np.array(start_point) if not isinstance(start_point, _np.ndarray) else start_point
        e = _np.array(end_point) if not isinstance(end_point, _np.ndarray) else end_point
        return CurvedArrow(start_point=s, end_point=e, color=color,
                           stroke_width=stroke_width, angle=angle)


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

# 2K QHD 60FPS STANDARD CANONICAL CANVAS CONFIGURATION
config.background_color = COLOR_BG
config.pixel_width = 2560
config.pixel_height = 1440
config.frame_width = 14.22
config.frame_height = 8.0
config.frame_rate = 60


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


# ==============================================================================
# SCENE 1: COLD OPEN — THE CONFIDENT HALLUCINATION PARADOX
# ==============================================================================
class Tap20Scene01ColdOpen(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "NGHỊCH LÝ ẢO GIÁC TRONG MẠNG NƠ-RON")

        scene_title = Text(
            "NGHỊCH LÝ ẢO GIÁC: TỰ TIN TUYỆT ĐỐI NHƯNG SAI LẦM",
            font=DEFAULT_FONT, font_size=19, weight=BOLD, color=COLOR_GOLD
        ).to_edge(UP, buff=0.95)
        self.play(FadeIn(scene_title, shift=DOWN * 0.2), run_time=0.8)

        tracker = ValueTracker(0.0)

        # Left Card: Fluency & Surface Rhetoric
        left_card = RoundedRectangle(
            corner_radius=0.15, width=4.9, height=4.2,
            fill_color=COLOR_PANEL, fill_opacity=0.85, stroke_color=COLOR_CYAN, stroke_width=1.5
        ).move_to(LEFT * 3.0 + DOWN * 0.3)
        l_header = Text("HÌNH THÁI VĂN BẢN (FLUENCY)", font=DEFAULT_FONT, font_size=13.0, weight=BOLD, color=COLOR_CYAN)
        l_header.next_to(left_card.get_top(), DOWN, buff=0.25)

        # Probability Softmax Distribution (Hero Geometry)
        axes_fluency = Axes(
            x_range=[0, 4, 1], y_range=[0, 1, 0.5],
            x_length=3.4, y_length=1.8,
            axis_config={"color": "#334155", "stroke_width": 1.2},
            tips=False
        ).move_to(left_card.get_center() + UP * 0.1)

        bar_peak = Rectangle(width=0.45, height=1.6, fill_color=COLOR_CYAN, fill_opacity=0.9, stroke_width=1.0)
        bar_peak.move_to(axes_fluency.c2p(1.5, 0.45))
        p_header = Text("P(token) = 0.998", font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_CYAN)
        p_header.next_to(bar_peak, UP, buff=0.1)

        fluency_badge = RoundedRectangle(
            corner_radius=0.08, width=3.8, height=0.5,
            fill_color="#10252b", fill_opacity=0.9, stroke_color=COLOR_CYAN, stroke_width=1.2
        ).next_to(left_card.get_bottom(), UP, buff=0.25)
        fluency_header = Text("NGỮ PHÁP HOÀN HẢO // ĐỘ TỰ TIN CAO", font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_CYAN)
        fluency_header.move_to(fluency_badge.get_center())

        left_grp = VGroup(left_card, l_header, axes_fluency, bar_peak, p_header, fluency_badge, fluency_header)

        # Right Card: Factuality & Truth Collapse
        right_card = RoundedRectangle(
            corner_radius=0.15, width=4.9, height=4.2,
            fill_color=COLOR_PANEL, fill_opacity=0.85, stroke_color=COLOR_ROSE, stroke_width=1.5
        ).move_to(RIGHT * 3.0 + DOWN * 0.3)
        r_header = Text("BẢN CHẤT SỰ THỰC (FACTUALITY)", font=DEFAULT_FONT, font_size=13.0, weight=BOLD, color=COLOR_ROSE)
        r_header.next_to(right_card.get_top(), DOWN, buff=0.25)

        # Fake Citations Radar (Hero Geometry)
        circle_truth = Circle(radius=0.9, color="#334155", stroke_width=1.2).move_to(right_card.get_center() + UP * 0.1)
        alert_dot = Dot(point=circle_truth.get_center(), radius=0.12, color=COLOR_ROSE)
        radar_line = Line(circle_truth.get_center(), circle_truth.get_top(), color=COLOR_ROSE, stroke_width=2.0)

        fact_badge = RoundedRectangle(
            corner_radius=0.08, width=3.8, height=0.5,
            fill_color="#28131e", fill_opacity=0.9, stroke_color=COLOR_ROSE, stroke_width=1.2
        ).next_to(right_card.get_bottom(), UP, buff=0.25)
        fact_header = Text("ÁN LỆ BỊA ĐẶT // ZERO FACTUALITY", font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_ROSE)
        fact_header.move_to(fact_badge.get_center())

        right_grp = VGroup(right_card, r_header, circle_truth, alert_dot, radar_line, fact_badge, fact_header)

        self.play(FadeIn(left_grp, shift=RIGHT * 0.3), FadeIn(right_grp, shift=LEFT * 0.3), run_time=1.2)

        # Contradiction Bridge Arrow
        clash_arrow = ZenArrow(
            start=left_card.get_right() + UP * 0.2,
            end=right_card.get_left() + UP * 0.2,
            color=COLOR_GOLD, stroke_width=2.5
        )
        clash_header = Text("PARADOX GAP", font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_GOLD)
        clash_header.next_to(clash_arrow, UP, buff=0.1)

        self.play(GrowArrow(clash_arrow), FadeIn(clash_header), tracker.animate.set_value(1.0), run_time=1.0)

        # Bottom Callout Box
        callout_box = RoundedRectangle(
            corner_radius=0.12, width=10.6, height=0.72,
            fill_color="#181528", fill_opacity=0.95, stroke_color=COLOR_GOLD, stroke_width=1.2
        ).to_edge(DOWN, buff=0.35)
        callout_header = Text(
            "CỐT LÕI: LLM TỐI ĐA HÓA XÁC SUẤT CHUỖI, KHÔNG PHẢI CHÂN LÝ KHÁCH QUAN",
            font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_GOLD
        ).move_to(callout_box.get_center())

        self.play(FadeIn(callout_box, shift=UP * 0.2), FadeIn(callout_header), run_time=0.9)
        self.wait(2.0)


# ==============================================================================
# SCENE 2: ARCHITECTURE — LEXICAL ENTROPY VS SEMANTIC ENTROPY
# ==============================================================================
class Tap20Scene02Architecture(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "TỪ VỰNG RỜI RẠC VS NGỮ NGHĨA HỘI TỤ")

        scene_title = Text(
            "PHÂN TÁCH: LEXICAL ENTROPY VS SEMANTIC ENTROPY",
            font=DEFAULT_FONT, font_size=18, weight=BOLD, color=COLOR_CYAN
        ).to_edge(UP, buff=0.95)
        self.play(FadeIn(scene_title, shift=DOWN * 0.2), run_time=0.8)

        entropy_tracker = ValueTracker(0.0)

        # Top Model Query Box
        q_box = RoundedRectangle(
            corner_radius=0.12, width=8.6, height=0.8,
            fill_color=COLOR_PANEL, fill_opacity=0.9, stroke_color=COLOR_GOLD, stroke_width=1.2
        ).move_to(UP * 1.8)
        q_header = Text(
            "TRUY VẤN: 'THỦ ĐÔ NƯỚC PHÁP LÀ THÀNH PHỐ NÀO?'",
            font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_GOLD
        ).move_to(q_box.get_center())
        self.play(FadeIn(q_box), FadeIn(q_header), run_time=0.8)

        # Branch Left: Lexical Variation, Same Semantic Meaning (Entropy = 0)
        b1_card = RoundedRectangle(
            corner_radius=0.15, width=4.9, height=3.3,
            fill_color=COLOR_PANEL, fill_opacity=0.85, stroke_color=COLOR_GREEN, stroke_width=1.5
        ).move_to(LEFT * 3.0 + DOWN * 0.6)
        b1_header = Text("TRƯỜNG HỢP 1: TỪ VỰNG PHONG PHÚ", font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_GREEN)
        b1_header.next_to(b1_card.get_top(), DOWN, buff=0.25)

        # Clustered geometric dots for semantic agreement
        b1_cluster = Circle(radius=0.6, color=COLOR_GREEN, stroke_width=1.2).next_to(b1_header, DOWN, buff=0.25)
        d1 = Dot(point=b1_cluster.get_center() + LEFT * 0.2, radius=0.07, color=COLOR_GREEN)
        d2 = Dot(point=b1_cluster.get_center() + RIGHT * 0.2, radius=0.07, color=COLOR_GREEN)
        d3 = Dot(point=b1_cluster.get_center() + UP * 0.2, radius=0.07, color=COLOR_GREEN)

        b1_res_header = Text("CÙNG 1 CỤM Ý NGHĨA // H_SEMANTIC = 0", font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_GREEN)
        b1_res_header.next_to(b1_card.get_bottom(), UP, buff=0.25)
        grp1 = VGroup(b1_card, b1_header, b1_cluster, d1, d2, d3, b1_res_header)

        # Branch Right: Semantic Hallucination / Conflicting Clusters (Entropy >> 0)
        b2_card = RoundedRectangle(
            corner_radius=0.15, width=4.9, height=3.3,
            fill_color=COLOR_PANEL, fill_opacity=0.85, stroke_color=COLOR_ROSE, stroke_width=1.5
        ).move_to(RIGHT * 3.0 + DOWN * 0.6)
        b2_header = Text("TRƯỜNG HỢP 2: ẢO GIÁC PHÂN MẢNH", font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_ROSE)
        b2_header.next_to(b2_card.get_top(), DOWN, buff=0.25)

        # Fragmented conflicting dots
        c_a = Circle(radius=0.35, color=COLOR_ROSE, stroke_width=1.2).move_to(b2_card.get_center() + LEFT * 1.0 + UP * 0.1)
        c_b = Circle(radius=0.35, color=COLOR_GOLD, stroke_width=1.2).move_to(b2_card.get_center() + RIGHT * 1.0 + UP * 0.1)
        da = Dot(point=c_a.get_center(), radius=0.07, color=COLOR_ROSE)
        db = Dot(point=c_b.get_center(), radius=0.07, color=COLOR_GOLD)

        b2_res_header = Text("ĐA CỤM MÂU THUẪN // H_SEMANTIC >> 0", font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_ROSE)
        b2_res_header.next_to(b2_card.get_bottom(), UP, buff=0.25)
        grp2 = VGroup(b2_card, b2_header, c_a, c_b, da, db, b2_res_header)

        arr1 = ZenArrow(start=q_box.get_bottom() + LEFT * 1.5, end=b1_card.get_top(), color=COLOR_GREEN, stroke_width=2.0)
        arr2 = ZenArrow(start=q_box.get_bottom() + RIGHT * 1.5, end=b2_card.get_top(), color=COLOR_ROSE, stroke_width=2.0)

        self.play(Create(arr1), Create(arr2), FadeIn(grp1, shift=UP * 0.2), FadeIn(grp2, shift=UP * 0.2), run_time=1.2)

        # Dynamic scan indicator
        self.play(
            entropy_tracker.animate.set_value(1.0),
            c_a.animate.scale(1.1),
            c_b.animate.scale(1.1),
            run_time=1.2
        )

        bot_box = RoundedRectangle(
            corner_radius=0.12, width=10.6, height=0.64,
            fill_color="#181e2b", fill_opacity=0.95, stroke_color=COLOR_CYAN, stroke_width=1.2
        ).to_edge(DOWN, buff=0.35)
        bot_header = Text(
            "GOM CỤM Ý NGHĨA NLI ĐO LƯỜNG SỰ THỰC, KHÔNG ĐO LƯỜNG TỪ VỰNG",
            font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_CYAN
        ).move_to(bot_box.get_center())

        self.play(FadeIn(bot_box, shift=UP * 0.2), FadeIn(bot_header), run_time=0.8)
        self.wait(1.5)


# ==============================================================================
# SCENE 3: MATHEMATICS — SEMANTIC ENTROPY & PROBING CLASSIFIERS
# ==============================================================================
class Tap20Scene03Mathematics(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "GIẢI PHẪU TOÁN HỌC SEMANTIC ENTROPY")

        scene_title = Text(
            "TOÁN HỌC SEMANTIC ENTROPY & PROBING CLASSIFIERS",
            font=DEFAULT_FONT, font_size=19, weight=BOLD, color=COLOR_GOLD
        ).to_edge(UP, buff=0.95)
        self.play(FadeIn(scene_title, shift=DOWN * 0.2), run_time=0.8)

        math_tracker = ValueTracker(0.0)

        # Formula 1 Box: Semantic Entropy (Farquhar et al., Nature 2024)
        f1_card = RoundedRectangle(
            corner_radius=0.15, width=10.6, height=2.4,
            fill_color=COLOR_PANEL, fill_opacity=0.95, stroke_color=COLOR_CYAN, stroke_width=1.5
        ).move_to(UP * 1.3)

        f1_header = Text(
            "1. CÔNG THỨC SEMANTIC ENTROPY (FARQUHAR ET AL., NATURE 2024)",
            font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_CYAN
        ).next_to(f1_card.get_top(), DOWN, buff=0.20)

        math_f1 = MathTex(
            r"H_{\text{semantic}}(x) = - \sum_{c \in \mathcal{C}} P(c \mid x) \log P(c \mid x)",
            font_size=26, color=COLOR_GOLD
        ).next_to(f1_header, DOWN, buff=0.20)

        sub_f1_header = Text(
            "TRONG ĐÓ C LÀ TẬP CÁC CỤM NGỮ NGHĨA PHÂN TÁCH QUA PHÉP CHIẾU NLI",
            font=DEFAULT_FONT, font_size=12.0, color=COLOR_TEXT
        ).next_to(math_f1, DOWN, buff=0.18)

        grp_f1 = VGroup(f1_card, f1_header, math_f1, sub_f1_header)
        self.play(FadeIn(grp_f1, shift=UP * 0.2), run_time=1.2)

        # Formula 2 Box: Linear Probe on Hidden Activations (Anthropic 2024)
        f2_card = RoundedRectangle(
            corner_radius=0.15, width=10.6, height=2.4,
            fill_color=COLOR_PANEL, fill_opacity=0.95, stroke_color=COLOR_GOLD, stroke_width=1.5
        ).move_to(DOWN * 1.5)

        f2_header = Text(
            "2. MÁY DÒ TUYẾN TÍNH TRẠNG THÁI ẨN (LINEAR PROBE — ANTHROPIC 2024)",
            font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_GOLD
        ).next_to(f2_card.get_top(), DOWN, buff=0.20)

        math_f2 = MathTex(
            r"P(\text{Truthful} \mid h_l) = \sigma\left(\mathbf{w}^\top \mathbf{h}_l + b\right), \quad \mathbf{h}_l \in \mathbb{R}^{d_{\text{model}}}",
            font_size=26, color=COLOR_CYAN
        ).next_to(f2_header, DOWN, buff=0.20)

        sub_f2_header = Text(
            "TRÍCH XUẤT VECTOR KÍCH HOẠT ẨN: MÔ HÌNH NHẬN THỨC CHÂN LÝ TẠI TẦNG SÂU",
            font=DEFAULT_FONT, font_size=12.0, color=COLOR_GREEN
        ).next_to(math_f2, DOWN, buff=0.18)

        # Geometric probe indicator arrow
        probe_dot = Dot(point=f2_card.get_left() + RIGHT * 1.5 + DOWN * 0.2, radius=0.08, color=COLOR_CYAN)
        truth_dot = Dot(point=f2_card.get_right() + LEFT * 1.5 + DOWN * 0.2, radius=0.08, color=COLOR_GREEN)
        probe_arrow = ZenArrow(start=probe_dot.get_center(), end=truth_dot.get_center(), color=COLOR_GOLD, stroke_width=2.0)

        grp_f2 = VGroup(f2_card, f2_header, math_f2, sub_f2_header, probe_dot, truth_dot, probe_arrow)
        self.play(FadeIn(grp_f2, shift=UP * 0.2), run_time=1.2)

        self.play(
            math_tracker.animate.set_value(1.0),
            probe_dot.animate.move_to(f2_card.get_center() + LEFT * 0.8 + DOWN * 0.2),
            truth_dot.animate.move_to(f2_card.get_center() + RIGHT * 0.8 + DOWN * 0.2),
            run_time=1.5
        )
        self.wait(1.5)


# ==============================================================================
# SCENE 4: TELEMETRY — BENCHMARK EVALUATION
# ==============================================================================
class Tap20Scene04Telemetry(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "BENCHMARK PHÁT HIỆN ẢO GIÁC TRÊN TRUTHFULQA")

        scene_title = Text(
            "BENCHMARK THỰC TẾ: SELF-REFLECTION VS LINEAR PROBE",
            font=DEFAULT_FONT, font_size=19, weight=BOLD, color=COLOR_GREEN
        ).to_edge(UP, buff=0.95)
        self.play(FadeIn(scene_title, shift=DOWN * 0.2), run_time=0.8)

        telem_tracker = ValueTracker(0.0)

        # 3 Benchmark Telemetry Cards
        cards_data = [
            ("TỰ PHẢN BIỆN (PROMPT)", COLOR_ROSE, [
                ("ROC-AUC", "0.56 (KÉM)", COLOR_ROSE),
                ("Độ trễ (Latency)", "450 ms", COLOR_ROSE),
                ("Chi phí suy luận", "+100% token", COLOR_ROSE),
                ("Hiệu quả", "THẤT BẠI", COLOR_ROSE),
            ]),
            ("SEMANTIC ENTROPY", COLOR_CYAN, [
                ("ROC-AUC", "0.84 (RẤT TỐT)", COLOR_CYAN),
                ("Độ trễ (Latency)", "620 ms", COLOR_GOLD),
                ("Chi phí suy luận", "K-samples", COLOR_GOLD),
                ("Hiệu quả", "CHÍNH XÁC CAO", COLOR_CYAN),
            ]),
            ("LINEAR PROBE (PROBING)", COLOR_GREEN, [
                ("ROC-AUC", "0.89 (XUẤT SẮC)", COLOR_GREEN),
                ("Độ trễ (Latency)", "2.1 ms", COLOR_GREEN),
                ("Chi phí suy luận", "0% token phụ", COLOR_GREEN),
                ("Hiệu quả", "TỐI ƯU SẢN XUẤT", COLOR_GREEN),
            ]),
        ]

        col_group = VGroup()
        for idx, (title, col, metrics) in enumerate(cards_data):
            c_box = RoundedRectangle(
                corner_radius=0.15, width=3.3, height=4.4,
                fill_color=COLOR_PANEL, fill_opacity=0.9, stroke_color=col, stroke_width=1.5
            )
            c_header = Text(title, font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=col)
            c_header.next_to(c_box.get_top(), DOWN, buff=0.25)
            sep_line = Line(start=LEFT * 1.4, end=RIGHT * 1.4, color=COLOR_MUTED, stroke_width=1.0).next_to(c_header, DOWN, buff=0.15)

            m_grp = VGroup()
            curr_y = sep_line
            for label, val, val_c in metrics:
                l_hdr = Text(label, font=DEFAULT_FONT, font_size=12.0, color=COLOR_TEXT)
                v_hdr = Text(val, font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=val_c)
                row = VGroup(l_hdr, v_hdr).arrange(DOWN, buff=0.06, aligned_edge=ORIGIN)
                row.next_to(curr_y, DOWN, buff=0.15)
                m_grp.add(row)
                curr_y = row

            single_col = VGroup(c_box, c_header, sep_line, m_grp)
            single_col.move_to(LEFT * 3.6 + RIGHT * (idx * 3.6) + DOWN * 0.4)
            col_group.add(single_col)

        self.play(LaggedStart(*[FadeIn(c, shift=UP * 0.3) for c in col_group], lag_ratio=0.2), run_time=1.5)

        # Highlight Probe column
        highlight_box = SurroundingRectangle(col_group[2], stroke_color=COLOR_GREEN, stroke_width=2.0, corner_radius=0.15)
        self.play(Create(highlight_box), telem_tracker.animate.set_value(1.0), run_time=1.0)

        # Bottom Conclusion Box
        bot_box = RoundedRectangle(
            corner_radius=0.12, width=10.6, height=0.64,
            fill_color="#181e2b", fill_opacity=0.95, stroke_color=COLOR_GREEN, stroke_width=1.2
        ).to_edge(DOWN, buff=0.35)
        bot_header = Text(
            "KẾT LUẬN: ĐẦU DÒ TRẠNG THÁI ẨN ĐẠT HIỆU QUẢ CAO NHẤT VỚI ĐỘ TRỄ CHỈ 2.1ms",
            font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_GREEN
        ).move_to(bot_box.get_center())

        self.play(FadeIn(bot_box, shift=UP * 0.2), FadeIn(bot_header), run_time=0.8)
        self.wait(1.5)


# ==============================================================================
# SCENE 5: LAB EXPERIMENT — ACTIVATION ADDITION & STEERING
# ==============================================================================
class Tap20Scene05LabExperiment(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "KỸ NGHỆ HIỆU CHỈNH ACTIVATION ADDITION")

        scene_title = Text(
            "LAB INNORIA: CAN THIỆP VECTOR KÍCH HOẠT (REPRESENTATION ENG)",
            font=DEFAULT_FONT, font_size=19, weight=BOLD, color=COLOR_GOLD
        ).to_edge(UP, buff=0.95)
        self.play(FadeIn(scene_title, shift=DOWN * 0.2), run_time=0.8)

        steer_tracker = ValueTracker(0.0)

        # 3 Architecture Nodes: Layer 1 -> Layer 16 Steering -> Layer 32 True Output
        node_l1 = RoundedRectangle(
            corner_radius=0.12, width=2.8, height=1.6,
            fill_color=COLOR_PANEL, fill_opacity=0.9, stroke_color=COLOR_CYAN, stroke_width=1.5
        ).move_to(LEFT * 4.0 + UP * 0.6)
        l1_header = Text("LAYER 1..15", font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_CYAN)
        l1_sub_header = Text("ĐỌC VÀ MÃ HÓA NGỮ CẢNH", font=DEFAULT_FONT, font_size=12.0, color=COLOR_TEXT).next_to(l1_header, DOWN, buff=0.12)
        g_l1 = VGroup(node_l1, l1_header, l1_sub_header)
        l1_header.move_to(node_l1.get_center() + UP * 0.2)
        l1_sub_header.move_to(node_l1.get_center() + DOWN * 0.2)

        node_l16 = RoundedRectangle(
            corner_radius=0.12, width=3.4, height=1.8,
            fill_color="#231d34", fill_opacity=0.95, stroke_color=COLOR_GOLD, stroke_width=2.0
        ).move_to(ORIGIN + UP * 0.6)
        l16_header = Text("LAYER 16 CAN THIỆP", font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_GOLD)
        l16_math = MathTex(r"\mathbf{h}' = \mathbf{h} + \alpha \mathbf{v}_{\text{truth}}", font_size=23, color=COLOR_GOLD)
        l16_header.move_to(node_l16.get_center() + UP * 0.28)
        l16_math.move_to(node_l16.get_center() + DOWN * 0.25)
        g_l16 = VGroup(node_l16, l16_header, l16_math)

        node_l32 = RoundedRectangle(
            corner_radius=0.12, width=2.8, height=1.6,
            fill_color=COLOR_PANEL, fill_opacity=0.9, stroke_color=COLOR_GREEN, stroke_width=1.5
        ).move_to(RIGHT * 4.0 + UP * 0.6)
        l32_header = Text("LAYER 32 OUTPUT", font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_GREEN)
        l32_sub_header = Text("TRUNG THỰC 100%", font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_GREEN).next_to(l32_header, DOWN, buff=0.12)
        g_l32 = VGroup(node_l32, l32_header, l32_sub_header)
        l32_header.move_to(node_l32.get_center() + UP * 0.2)
        l32_sub_header.move_to(node_l32.get_center() + DOWN * 0.2)

        arr1 = ZenArrow(start=node_l1.get_right(), end=node_l16.get_left(), color=COLOR_CYAN, stroke_width=2.4)
        arr2 = ZenArrow(start=node_l16.get_right(), end=node_l32.get_left(), color=COLOR_GREEN, stroke_width=2.4)

        self.play(
            FadeIn(g_l1), GrowArrow(arr1),
            FadeIn(g_l16), GrowArrow(arr2),
            FadeIn(g_l32), run_time=1.4
        )

        # Pulse Steering Dot
        pulse_dot = Dot(point=node_l16.get_center(), radius=0.12, color=COLOR_GOLD)
        self.play(FadeIn(pulse_dot), steer_tracker.animate.set_value(1.0), run_time=0.8)

        # Bottom Deployment Pillars Card
        spec_box = RoundedRectangle(
            corner_radius=0.15, width=10.6, height=2.0,
            fill_color=COLOR_PANEL, fill_opacity=0.9, stroke_color=COLOR_CYAN, stroke_width=1.2
        ).to_edge(DOWN, buff=0.45)
        spec_header = Text("KỸ THUẬT ACTIVATION STEERING (INNORIA DEPLOYMENT)", font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_CYAN)
        spec_header.next_to(spec_box.get_top(), DOWN, buff=0.20)

        line1_header = Text("• TIẾT KIỆM CHI PHÍ: KHÔNG CẦN RETRAIN TOÀN BỘ MÔ HÌNH 70B", font=DEFAULT_FONT, font_size=12.0, color=COLOR_TEXT).next_to(spec_header, DOWN, buff=0.18, aligned_edge=LEFT)
        line2_header = Text("• HIỆU QUẢ CAO: DẬP TẮT 88% CÂU TRẢ LỜI BỊA ĐẶT QUA VECTOR HƯỚNG", font=DEFAULT_FONT, font_size=12.0, color=COLOR_GREEN).next_to(line1_header, DOWN, buff=0.15, aligned_edge=LEFT)
        line3_header = Text("• TÍCH HỢP RAG: KHI ENTROPY CAO, CHỦ ĐỘNG TRUY VẤN NGUỒN NGOẠI VI", font=DEFAULT_FONT, font_size=12.0, color=COLOR_GOLD).next_to(line2_header, DOWN, buff=0.15, aligned_edge=LEFT)

        grp_spec = VGroup(spec_box, spec_header, line1_header, line2_header, line3_header)
        self.play(FadeIn(grp_spec, shift=UP * 0.2), run_time=1.1)
        self.wait(1.5)


# ==============================================================================
# SCENE 6: OUTRO — HUMANITY, CRAFTSMANSHIP & EPISODE 21 TEASER
# ==============================================================================
class Tap20Scene06Outro(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "TỔNG KẾT & CẦU NỐI KỸ NGHỆ")

        scene_title = Text(
            "BÀN GIAO TRI THỨC // GIẢI PHẪU NGUỒN CỘI ẢO GIÁC AI",
            font=DEFAULT_FONT, font_size=15.0, weight=BOLD, color=COLOR_GOLD
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
            font=DEFAULT_FONT, font_size=12.5, weight=BOLD, color=COLOR_GOLD
        ).next_to(mosaic_frame, UP, buff=0.18)

        left_grp = Group(mosaic_mobj, mosaic_frame, gallery_header)
        self.play(FadeIn(left_grp, shift=RIGHT * 0.3), run_time=1.2)

        # Right Side: YouTube End Screen Interactive Safe Zones
        # 1. Next Video Card (Episode 21: Multi-Tier RAG): X in [+1.6, +5.4], Y in [+0.5, +2.5]
        # Clearance to mosaic right edge (-0.30): +1.60 - (-0.30) = 1.90 units = 342px >= 300px!
        next_card = RoundedRectangle(
            corner_radius=0.12, width=3.8, height=2.0,
            fill_color=COLOR_PANEL, fill_opacity=0.7, stroke_color=COLOR_CYAN, stroke_width=1.5
        ).move_to(RIGHT * 3.5 + UP * 1.5)
        next_header = Text("TẬP TIẾP THEO // TẬP 21", font=DEFAULT_FONT, font_size=12.5, weight=BOLD, color=COLOR_CYAN)
        next_sub_header = Text("RAG ĐA TẦNG: NẠP TRI THỨC SỐNG", font=DEFAULT_FONT, font_size=12.0, color=COLOR_TEXT).next_to(next_header, DOWN, buff=0.18)
        next_grp = VGroup(next_header, next_sub_header).move_to(next_card.get_center())

        # 2. Playlist Card: X in [+1.6, +5.4], Y in [-1.0, +0.3]
        pl_card = RoundedRectangle(
            corner_radius=0.12, width=3.8, height=1.3,
            fill_color=COLOR_PANEL, fill_opacity=0.7, stroke_color=COLOR_GOLD, stroke_width=1.5
        ).move_to(RIGHT * 3.5 + DOWN * 0.35)
        pl_header = create_wrapped_card_text(
            "PLAYLIST TRỌN BỘ 25 TẬP", pl_card,
            font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_GOLD, padding_x=0.20, padding_y=0.15
        )

        # 3. Channel Subscribe Avatar: Circle at X=+3.5, Y=-1.65
        sub_circle = Circle(
            radius=0.52, fill_color=COLOR_BG, fill_opacity=0.9, stroke_color=COLOR_GOLD, stroke_width=1.5
        ).move_to(RIGHT * 3.5 + DOWN * 1.65)
        sub_header = Text("ZEN", font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_GOLD)
        sub_header.move_to(sub_circle.get_center())

        right_grp = VGroup(next_card, next_grp, pl_card, pl_header, sub_circle, sub_header)
        self.play(FadeIn(right_grp, shift=LEFT * 0.3), outro_tracker.animate.set_value(1.0), run_time=1.0)

        # Bottom Bridge Announcement to Episode 21
        bridge_banner = RoundedRectangle(
            corner_radius=0.12, width=10.6, height=0.70,
            fill_color="#181524", fill_opacity=0.95, stroke_color=COLOR_GOLD, stroke_width=1.5
        ).to_edge(DOWN, buff=0.35)
        bridge_header = Text(
            "ĐÓN XEM TẬP 21 // HỆ THỐNG RAG ĐA TẦNG: GIẢI PHÓNG LLM KHỎI TRI THỨC TĨNH",
            font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_GOLD
        ).move_to(bridge_banner.get_center())

        self.play(FadeIn(bridge_banner, shift=UP * 0.2), FadeIn(bridge_header), run_time=0.9)
        self.wait(2.0)
