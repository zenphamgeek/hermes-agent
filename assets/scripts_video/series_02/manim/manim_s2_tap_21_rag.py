#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Manim 2K Mathematical Engine — Series 2, Episode 21: Advanced Multi-Tier RAG
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


def add_zenpham_brand(scene: Scene, ep_title: str):
    """Adds ZenPham top-right watermark and top pill header."""
    brand_title = Text("ZENPHAM", font=DEFAULT_FONT, font_size=13, weight=BOLD, color=COLOR_GOLD)
    sub_title = Text("KỸ NGHỆ LLM TỐI TÂN", font=DEFAULT_FONT, font_size=12.0, color=COLOR_MUTED).next_to(brand_title, DOWN, buff=0.06)
    watermark_grp = VGroup(brand_title, sub_title).to_corner(UR, buff=0.45)

    badge_rect = RoundedRectangle(
        corner_radius=0.12, height=0.46, width=8.6,
        fill_color=COLOR_PANEL, fill_opacity=0.9, stroke_color=COLOR_CYAN, stroke_width=1.0
    ).to_edge(UP, buff=0.35)
    badge_header = Text(
        f"ZENPHAM // TÔI LÀM VIỆC — {ep_title}",
        font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_TEXT
    ).move_to(badge_rect.get_center())

    scene.add(watermark_grp, badge_rect, badge_header)


# ==============================================================================
# SCENE 1: COLD OPEN — FROZEN PARAMETRIC KNOWLEDGE VS LIVE RETRIEVAL
# ==============================================================================
class Tap21Scene01ColdOpen(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "NGHỊCH LÝ TRI THỨC ĐÓNG BĂNG VÀ RAG ĐA TẦNG")

        scene_title = Text(
            "NGHỊCH LÝ MÔ HÌNH ĐÓNG BĂNG TRONG DOANH NGHIỆP",
            font=DEFAULT_FONT, font_size=19, weight=BOLD, color=COLOR_GOLD
        ).to_edge(UP, buff=0.95)
        self.play(FadeIn(scene_title, shift=DOWN * 0.2), run_time=0.8)

        # ValueTracker for geometric animation
        weight_tracker = ValueTracker(0.0)

        # Left Card: Frozen Parametric Memory
        left_card = RoundedRectangle(
            corner_radius=0.15, width=4.9, height=4.2,
            fill_color=COLOR_PANEL, fill_opacity=0.85, stroke_color=COLOR_ROSE, stroke_width=1.5
        ).move_to(LEFT * 3.0 + DOWN * 0.3)
        l_header = Text("TRI THỨC THAM SỐ (PARAMETRIC)", font=DEFAULT_FONT, font_size=13.0, weight=BOLD, color=COLOR_ROSE)
        l_header.next_to(left_card.get_top(), DOWN, buff=0.25)

        # Frozen Weights Neural Lattice (Geometric Hero)
        lattice_dots = VGroup()
        for rx in np.linspace(-1.8, 1.8, 4):
            for ry in np.linspace(-0.8, 0.8, 3):
                d = Dot(point=left_card.get_center() + np.array([rx, ry, 0]), radius=0.08, color=COLOR_MUTED)
                lattice_dots.add(d)

        lattice_lines = VGroup()
        for idx in range(len(lattice_dots) - 1):
            if idx % 3 != 2:
                l = Line(lattice_dots[idx].get_center(), lattice_dots[idx + 1].get_center(), stroke_width=1.0, color="#334155")
                lattice_lines.add(l)

        frozen_badge = RoundedRectangle(
            corner_radius=0.08, width=3.8, height=0.5,
            fill_color="#23131d", fill_opacity=0.9, stroke_color=COLOR_ROSE, stroke_width=1.2
        ).next_to(left_card.get_bottom(), UP, buff=0.25)
        frozen_header = Text("TRỌNG SỐ ĐÓNG BĂNG // CUTOFF DATE", font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_ROSE)
        frozen_header.move_to(frozen_badge.get_center())

        left_grp = VGroup(left_card, l_header, lattice_lines, lattice_dots, frozen_badge, frozen_header)

        # Right Card: Non-Parametric Dynamic RAG
        right_card = RoundedRectangle(
            corner_radius=0.15, width=4.9, height=4.2,
            fill_color=COLOR_PANEL, fill_opacity=0.85, stroke_color=COLOR_CYAN, stroke_width=1.5
        ).move_to(RIGHT * 3.0 + DOWN * 0.3)
        r_header = Text("TRI THỨC NGOẠI VI (NON-PARAMETRIC)", font=DEFAULT_FONT, font_size=13.0, weight=BOLD, color=COLOR_CYAN)
        r_header.next_to(right_card.get_top(), DOWN, buff=0.25)

        # Dynamic Vector Database Clusters (Geometric Hero)
        axes_rag = create_hairline_axes(
            x_range=(-2, 2, 1), y_range=(-1.5, 1.5, 1),
            x_length=3.4, y_length=2.0, axis_color="#334155"
        ).move_to(right_card.get_center() + UP * 0.1)

        vec_dots = VGroup()
        rng = np.random.default_rng(42)
        for _ in range(12):
            vx = rng.uniform(-1.4, 1.4)
            vy = rng.uniform(-0.8, 0.8)
            col = COLOR_CYAN if vx > 0 else COLOR_GREEN
            dot = Dot(point=axes_rag.get_center() + np.array([vx, vy, 0]), radius=0.07, color=col)
            vec_dots.add(dot)

        rag_badge = RoundedRectangle(
            corner_radius=0.08, width=3.8, height=0.5,
            fill_color="#10252b", fill_opacity=0.9, stroke_color=COLOR_CYAN, stroke_width=1.2
        ).next_to(right_card.get_bottom(), UP, buff=0.25)
        rag_header = Text("TRUY HỒI ĐỘNG // VECTOR DATABASE", font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_CYAN)
        rag_header.move_to(rag_badge.get_center())

        right_grp = VGroup(right_card, r_header, axes_rag, vec_dots, rag_badge, rag_header)

        self.play(FadeIn(left_grp, shift=RIGHT * 0.3), FadeIn(right_grp, shift=LEFT * 0.3), run_time=1.2)

        # Dynamic laser query search connecting both domains
        query_dot = Dot(point=left_card.get_center() + UP * 0.5, radius=0.10, color=COLOR_GOLD)
        laser_arrow = ZenArrow(
            start=left_card.get_right() + UP * 0.2,
            end=right_card.get_left() + UP * 0.2,
            color=COLOR_GOLD, stroke_width=2.5
        )
        laser_header = Text("QUERY VECTOR", font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_GOLD)
        laser_header.next_to(laser_arrow, UP, buff=0.1)

        self.play(FadeIn(query_dot), GrowArrow(laser_arrow), FadeIn(laser_header), run_time=1.0)
        self.play(
            weight_tracker.animate.set_value(1.0),
            query_dot.animate.move_to(right_card.get_center() + UP * 0.3),
            run_time=1.2
        )

        # Bottom Callout Header Box
        callout_box = RoundedRectangle(
            corner_radius=0.12, width=10.6, height=0.72,
            fill_color="#101422", fill_opacity=0.95, stroke_color=COLOR_GOLD, stroke_width=1.2
        ).to_edge(DOWN, buff=0.35)
        callout_header = Text(
            "RAG ĐA TẦNG: GIẢI PHÓNG LLM KHỎI CHIẾC LỒNG TRI THỨC ĐÓNG BĂNG",
            font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_GOLD
        ).move_to(callout_box.get_center())

        self.play(FadeIn(callout_box, shift=UP * 0.2), FadeIn(callout_header), run_time=0.9)
        self.wait(2.0)


# ==============================================================================
# SCENE 2: ARCHITECTURE — NAIVE RAG VS LOST IN THE MIDDLE
# ==============================================================================
class Tap21Scene02Architecture(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "TỬ HUYỆT CỦA NAIVE RAG VÀ LOST IN THE MIDDLE")

        scene_title = Text(
            "TẠI SAO NAIVE RAG THẤT BẠI: ĐỨT GÃY NGỮ CẢNH & ATTENTION CHÌM",
            font=DEFAULT_FONT, font_size=18, weight=BOLD, color=COLOR_CYAN
        ).to_edge(UP, buff=0.95)
        self.play(FadeIn(scene_title, shift=DOWN * 0.2), run_time=0.8)

        tracker = ValueTracker(0.0)

        # Naive Pipeline flow (Top)
        flow_panel = RoundedRectangle(
            corner_radius=0.12, width=10.6, height=1.6,
            fill_color=COLOR_PANEL, fill_opacity=0.8, stroke_color=COLOR_MUTED, stroke_width=1.0
        ).move_to(UP * 1.5)

        stages_data = [
            ("Raw Doc", "Chunk 500t", COLOR_CYAN),
            ("Bi-Encoder", "Embedding", COLOR_CYAN),
            ("Cosine Sim", "Top-K Scan", COLOR_GOLD),
            ("LLM Prompt", "Stuffing", COLOR_ROSE),
        ]

        pipe_boxes = VGroup()
        for idx, (top_t, btm_t, st_c) in enumerate(stages_data):
            bx = RoundedRectangle(
                corner_radius=0.08, width=2.0, height=1.0,
                fill_color="#1a202c", fill_opacity=0.9, stroke_color=st_c, stroke_width=1.2
            )
            t_top = Text(top_t, font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=st_c)
            t_btm = Text(btm_t, font=DEFAULT_FONT, font_size=12.0, color=COLOR_TEXT).next_to(t_top, DOWN, buff=0.08)
            g_box = VGroup(bx, t_top, t_btm)
            g_box.move_to(flow_panel.get_left() + RIGHT * (1.3 + idx * 2.6))
            pipe_boxes.add(g_box)

        arrows_grp = VGroup()
        for idx in range(3):
            ar = ZenArrow(
                start=pipe_boxes[idx].get_right() + RIGHT * 0.05,
                end=pipe_boxes[idx + 1].get_left() + LEFT * 0.05,
                color=COLOR_MUTED, stroke_width=2.0
            )
            arrows_grp.add(ar)

        pipeline_grp = VGroup(flow_panel, pipe_boxes, arrows_grp)
        self.play(FadeIn(pipeline_grp, shift=DOWN * 0.2), run_time=1.0)

        # Bottom Graph: Lost in the Middle U-Curve
        u_box = RoundedRectangle(
            corner_radius=0.15, width=10.6, height=3.0,
            fill_color=COLOR_PANEL, fill_opacity=0.9, stroke_color=COLOR_GOLD, stroke_width=1.2
        ).move_to(DOWN * 1.5)

        u_header = Text(
            "HIỆN TƯỢNG 'LOST IN THE MIDDLE' (PERCY LIANG ET AL., STANFORD 2024)",
            font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_GOLD
        ).next_to(u_box.get_top(), DOWN, buff=0.25)

        axes = Axes(
            x_range=[0, 10, 2],
            y_range=[0, 1, 0.2],
            x_length=7.6,
            y_length=1.6,
            axis_config={"color": COLOR_MUTED, "stroke_width": 1.5},
        ).move_to(u_box.get_center() + DOWN * 0.15)

        # U-curve function
        u_curve = axes.plot(
            lambda x: 0.85 - 0.55 * np.sin(np.pi * x / 10.0),
            x_range=[0, 10], color=COLOR_ROSE, stroke_width=3.0
        )

        x_lbl1 = Text("Đầu Context (Top)", font=DEFAULT_FONT, font_size=12.0, color=COLOR_CYAN).next_to(axes.c2p(0.5, 0), DOWN, buff=0.15)
        x_lbl2 = Text("Giữa Context (VÙNG MÙ)", font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_ROSE).next_to(axes.c2p(5.0, 0), DOWN, buff=0.15)
        x_lbl3 = Text("Cuối Context (Prompt)", font=DEFAULT_FONT, font_size=12.0, color=COLOR_CYAN).next_to(axes.c2p(9.5, 0), DOWN, buff=0.15)
        y_lbl = Text("Attention", font=DEFAULT_FONT, font_size=12.0, color=COLOR_MUTED).next_to(axes.c2p(0, 0.9), LEFT, buff=0.15)

        # Scanning Dot along U-curve
        scan_dot = Dot(point=axes.c2p(0, 0.85), radius=0.08, color=COLOR_GOLD)

        self.play(
            FadeIn(u_box), FadeIn(u_header), Create(axes), Create(u_curve),
            FadeIn(x_lbl1), FadeIn(x_lbl2), FadeIn(x_lbl3), FadeIn(y_lbl),
            FadeIn(scan_dot), run_time=1.5
        )

        self.play(
            tracker.animate.set_value(10.0),
            MoveAlongPath(scan_dot, u_curve),
            run_time=2.0
        )
        self.wait(1.5)


# ==============================================================================
# SCENE 3: MATHEMATICS — CROSS-ENCODER & HYDE MATHEMATICAL FORMULATION
# ==============================================================================
class Tap21Scene03Mathematics(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "TOÁN HỌC CROSS-ENCODER & TÀI LIỆU GIẢ ĐỊNH HYDE")

        scene_title = Text(
            "TOÁN HỌC TÁI XẾP HẠNG & BIẾN ĐỔI KHÔNG GIAN HYDE",
            font=DEFAULT_FONT, font_size=19, weight=BOLD, color=COLOR_GOLD
        ).to_edge(UP, buff=0.95)
        self.play(FadeIn(scene_title, shift=DOWN * 0.2), run_time=0.8)

        math_tracker = ValueTracker(0.0)

        # Card 1: Bi-Encoder vs Cross-Encoder Formulation
        card_ce = RoundedRectangle(
            corner_radius=0.15, width=10.6, height=2.4,
            fill_color=COLOR_PANEL, fill_opacity=0.95, stroke_color=COLOR_CYAN, stroke_width=1.5
        ).move_to(UP * 1.3)

        lbl_ce_header = Text(
            "1. TƯƠNG TÁC TẬP TRUNG TOÀN PHẦN CROSS-ENCODER RE-RANKING",
            font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_CYAN
        ).next_to(card_ce.get_top(), DOWN, buff=0.20)

        f_bi = MathTex(
            r"\text{Bi-Encoder:}\quad s_{\text{bi}}(q, d) = \cos(\mathbf{e}_q, \mathbf{e}_d) = \frac{\mathbf{e}_q^\top \mathbf{e}_d}{\|\mathbf{e}_q\| \|\mathbf{e}_d\|}",
            font_size=23, color=COLOR_MUTED
        ).next_to(lbl_ce_header, DOWN, buff=0.18)

        f_cross = MathTex(
            r"\text{Cross-Encoder:}\quad s_{\text{cross}}(q, d) = \text{Transformer}([q \oplus [\text{SEP}] \oplus d])_{[\text{CLS}]}",
            font_size=24, color=COLOR_GOLD
        ).next_to(f_bi, DOWN, buff=0.18)

        if f_bi.width > card_ce.width * 0.88:
            f_bi.scale_to_fit_width(card_ce.width * 0.88)
        if f_cross.width > card_ce.width * 0.88:
            f_cross.scale_to_fit_width(card_ce.width * 0.88)

        grp_ce = VGroup(card_ce, lbl_ce_header, f_bi, f_cross)
        self.play(FadeIn(grp_ce, shift=UP * 0.2), run_time=1.2)

        # Card 2: HyDE Transformation
        card_hyde = RoundedRectangle(
            corner_radius=0.15, width=10.6, height=2.4,
            fill_color=COLOR_PANEL, fill_opacity=0.95, stroke_color=COLOR_GOLD, stroke_width=1.5
        ).move_to(DOWN * 1.5)

        lbl_hyde_header = Text(
            "2. ĐỘT PHÁ TÀI LIỆU GIẢ ĐỊNH HyDE (GAO ET AL., ACL 2023)",
            font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_GOLD
        ).next_to(card_hyde.get_top(), DOWN, buff=0.20)

        f_hyde = MathTex(
            r"d_{\text{hyp}} \sim p_{\text{LM}}(d \mid q), \quad \mathbf{v}_{\text{query}} = \mathcal{E}(d_{\text{hyp}}) \in \mathbb{R}^D",
            font_size=25, color=COLOR_CYAN
        ).next_to(lbl_hyde_header, DOWN, buff=0.20)

        if f_hyde.width > card_hyde.width * 0.88:
            f_hyde.scale_to_fit_width(card_hyde.width * 0.88)

        desc_hyde_header = Text(
            "CHUYỂN DỊCH CÂU HỎI MƠ HỒ SANG KHÔNG GIAN ĐỒNG DẠNG VỚI TÀI LIỆU ĐÍCH",
            font=DEFAULT_FONT, font_size=12.0, color=COLOR_TEXT
        ).next_to(f_hyde, DOWN, buff=0.18)

        # Vector Alignment Geometry
        q_dot = Dot(point=card_hyde.get_left() + RIGHT * 1.5 + DOWN * 0.2, radius=0.08, color=COLOR_CYAN)
        d_dot = Dot(point=card_hyde.get_right() + LEFT * 1.5 + DOWN * 0.2, radius=0.08, color=COLOR_GOLD)
        align_arrow = ZenArrow(start=q_dot.get_center(), end=d_dot.get_center(), color=COLOR_GREEN, stroke_width=2.0)

        grp_hyde = VGroup(card_hyde, lbl_hyde_header, f_hyde, desc_hyde_header, q_dot, d_dot, align_arrow)
        self.play(FadeIn(grp_hyde, shift=UP * 0.2), run_time=1.2)

        self.play(
            math_tracker.animate.set_value(1.0),
            q_dot.animate.move_to(card_hyde.get_center() + LEFT * 0.8 + DOWN * 0.2),
            d_dot.animate.move_to(card_hyde.get_center() + RIGHT * 0.8 + DOWN * 0.2),
            run_time=1.5
        )
        self.wait(1.5)


# ==============================================================================
# SCENE 4: TELEMETRY — CONTEXT PRECISION & FAITHFULNESS METRICS
# ==============================================================================
class Tap21Scene04Telemetry(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "ĐO KIỂM THỰC NGHIỆM CONTEXT PRECISION & FAITHFULNESS")

        scene_title = Text(
            "ĐO KIỂM TELEMETRY: FINANCIAL-QA DATASET BENCHMARK",
            font=DEFAULT_FONT, font_size=19, weight=BOLD, color=COLOR_CYAN
        ).to_edge(UP, buff=0.95)
        self.play(FadeIn(scene_title, shift=DOWN * 0.2), run_time=0.8)

        telem_tracker = ValueTracker(0.0)

        # 3 Benchmark Columns
        col_w, col_h = 3.3, 4.4
        cols_data = [
            ("NAIVE RAG (BASELINE)", COLOR_ROSE, [
                ("Context Precision", "42%", COLOR_ROSE),
                ("Context Recall", "45%", COLOR_ROSE),
                ("Faithfulness", "51%", COLOR_ROSE),
                ("Latency (p95)", "110 ms", COLOR_GREEN),
                ("Hallucination Risk", "49% (RẤT CAO)", COLOR_ROSE),
            ]),
            ("PARENT-CHILD CHUNK", COLOR_CYAN, [
                ("Context Precision", "71%", COLOR_CYAN),
                ("Context Recall", "78%", COLOR_GREEN),
                ("Faithfulness", "74%", COLOR_CYAN),
                ("Latency (p95)", "125 ms", COLOR_GREEN),
                ("Hallucination Risk", "26% (TRUNG BÌNH)", COLOR_GOLD),
            ]),
            ("MULTI-TIER + RE-RANK", COLOR_GOLD, [
                ("Context Precision", "91%", COLOR_GOLD),
                ("Context Recall", "88%", COLOR_GOLD),
                ("Faithfulness", "96%", COLOR_GREEN),
                ("Latency (p95)", "145 ms", COLOR_GOLD),
                ("Hallucination Risk", "< 4% (AN TOÀN)", COLOR_GREEN),
            ]),
        ]

        col_group = VGroup()
        for idx, (head_title, stroke_c, metrics) in enumerate(cols_data):
            c_box = RoundedRectangle(
                corner_radius=0.15, width=col_w, height=col_h,
                fill_color=COLOR_PANEL, fill_opacity=0.9, stroke_color=stroke_c, stroke_width=1.5
            )
            c_header = Text(head_title, font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=stroke_c)
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

        # Highlight Faithfulness Jump with SurroundingRectangle
        highlight_box = SurroundingRectangle(col_group[2], stroke_color=COLOR_GREEN, stroke_width=2.0, corner_radius=0.15)
        self.play(Create(highlight_box), telem_tracker.animate.set_value(1.0), run_time=1.0)

        # Bottom Conclusion Pill
        pill_box = RoundedRectangle(
            corner_radius=0.12, width=10.6, height=0.64,
            fill_color="#101824", fill_opacity=0.95, stroke_color=COLOR_GREEN, stroke_width=1.2
        ).to_edge(DOWN, buff=0.35)
        pill_header = Text(
            "KẾT LUẬN: THÊM 35ms CHO CROSS-ENCODER ĐỔI LẤY ĐỘ TRUNG THỰC 96% — ĐÁNH ĐỔI XỨNG ĐÁNG",
            font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_GREEN
        ).move_to(pill_box.get_center())

        self.play(FadeIn(pill_box, shift=UP * 0.2), FadeIn(pill_header), run_time=0.8)
        self.wait(1.5)


# ==============================================================================
# SCENE 5: LAB EXPERIMENT — HYBRID SEARCH, CONTEXTUAL COMPRESSION & SELF-RAG
# ==============================================================================
class Tap21Scene05LabExperiment(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "BỘ BA PHÒNG THỦ: HYBRID SEARCH, NÉN & SELF-RAG")

        scene_title = Text(
            "KIẾN TRÚC THỰC TẾ: BỘ BA PHÒNG THỦ ĐA TẦNG INNORIA",
            font=DEFAULT_FONT, font_size=19, weight=BOLD, color=COLOR_GOLD
        ).to_edge(UP, buff=0.95)
        self.play(FadeIn(scene_title, shift=DOWN * 0.2), run_time=0.8)

        pillar_tracker = ValueTracker(0.0)

        # 3 Defense Pillars
        pillar_w, pillar_h = 3.3, 4.3
        pillars = [
            ("TẦNG 1: HYBRID SEARCH", COLOR_CYAN, [
                "Kết hợp BM25 & HNSW Vector",
                "RRF: Reciprocal Rank Fusion",
                "Chống sót từ khóa chuyên ngành",
                "RRF(d) = sum(1 / (k + rank_i))"
            ]),
            ("TẦNG 2: CONTEXT COMPRESSION", COLOR_GOLD, [
                "Quét bằng nơ-ron chuyên biệt",
                "Loại bỏ 75% token rác/nhiễu",
                "Tiết kiệm chi phí cửa sổ ngữ cảnh",
                "Tập trung thông tin quyết định"
            ]),
            ("TẦNG 3: SELF-RAG CRITIQUE", COLOR_GREEN, [
                "Bộ phân loại tự kiểm chứng",
                "Kiểm toán nguồn trích dẫn",
                "Phát hiện khẳng định vô căn cứ",
                "Tự động kích hoạt truy xuất lại"
            ]),
        ]

        p_group = VGroup()
        for i, (p_title, p_color, p_items) in enumerate(pillars):
            p_box = RoundedRectangle(
                corner_radius=0.15, width=pillar_w, height=pillar_h,
                fill_color=COLOR_PANEL, fill_opacity=0.9, stroke_color=p_color, stroke_width=1.5
            )
            p_header = Text(p_title, font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=p_color)
            p_header.next_to(p_box.get_top(), DOWN, buff=0.25)
            p_line = Line(start=LEFT * 1.3, end=RIGHT * 1.3, color=COLOR_MUTED, stroke_width=1.0).next_to(p_header, DOWN, buff=0.15)

            items_v = VGroup()
            for itm in p_items:
                dot = Dot(radius=0.04, color=p_color)
                it_hdr = Text(itm, font=DEFAULT_FONT, font_size=12.0, color=COLOR_TEXT)
                row = VGroup(dot, it_hdr).arrange(RIGHT, buff=0.12)
                items_v.add(row)
            items_v.arrange(DOWN, buff=0.28, aligned_edge=LEFT)
            items_v.next_to(p_line, DOWN, buff=0.28)

            single_p = VGroup(p_box, p_header, p_line, items_v)
            single_p.move_to(LEFT * 3.6 + RIGHT * (i * 3.6) + DOWN * 0.4)
            p_group.add(single_p)

        self.play(LaggedStart(*[FadeIn(p, shift=UP * 0.3) for p in p_group], lag_ratio=0.2), run_time=1.5)

        # Dynamic Query Packet Flow across Pillars
        flow_packet = Dot(point=p_group[0].get_center() + UP * 0.5, radius=0.09, color=COLOR_CYAN)
        flow_arrow1 = ZenArrow(start=p_group[0].get_right() + UP * 0.5, end=p_group[1].get_left() + UP * 0.5, color=COLOR_GOLD, stroke_width=2.0)
        flow_arrow2 = ZenArrow(start=p_group[1].get_right() + UP * 0.5, end=p_group[2].get_left() + UP * 0.5, color=COLOR_GREEN, stroke_width=2.0)

        self.play(FadeIn(flow_packet), GrowArrow(flow_arrow1), GrowArrow(flow_arrow2), run_time=1.0)
        self.play(
            pillar_tracker.animate.set_value(1.0),
            flow_packet.animate.move_to(p_group[2].get_center() + UP * 0.5),
            run_time=1.5
        )

        # Bottom Callout Box
        callout = RoundedRectangle(
            corner_radius=0.12, width=10.6, height=0.64,
            fill_color="#181e2b", fill_opacity=0.95, stroke_color=COLOR_CYAN, stroke_width=1.2
        ).to_edge(DOWN, buff=0.35)
        callout_header = Text(
            "HỆ THỐNG VẬN HÀNH BỀN BỈ HÀNG TRIỆU QUERY MỖI NGÀY MÀ KHÔNG RÒ RỈ DỮ LIỆU",
            font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_CYAN
        ).move_to(callout.get_center())

        self.play(FadeIn(callout, shift=UP * 0.2), FadeIn(callout_header), run_time=0.8)
        self.wait(1.5)


# ==============================================================================
# SCENE 6: OUTRO — HUMANITY, CRAFTSMANSHIP & EPISODE 22 TEASER
# ==============================================================================
class Tap21Scene06Outro(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "TÔI LÀM VIỆC // SỰ KHIÊM NHƯỜNG TRONG KỸ NGHỆ")

        scene_title = Text(
            "BÀN GIAO TRI THỨC // KIẾN TRÚC RAG ĐA TẦNG TOÀN DIỆN",
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
        # 1. Next Video Card (Episode 22: Function Calling): X in [+1.6, +5.4], Y in [+0.5, +2.5]
        # Clearance to mosaic right edge (-0.30): +1.60 - (-0.30) = 1.90 units = 342px >= 300px!
        next_card = RoundedRectangle(
            corner_radius=0.12, width=3.8, height=2.0,
            fill_color=COLOR_PANEL, fill_opacity=0.7, stroke_color=COLOR_CYAN, stroke_width=1.5
        ).move_to(RIGHT * 3.5 + UP * 1.5)
        next_header = Text("TẬP TIẾP THEO // TẬP 22", font=DEFAULT_FONT, font_size=12.5, weight=BOLD, color=COLOR_CYAN)
        next_sub_header = Text("FUNCTION CALLING: CÔNG CỤ HÀNH ĐỘNG", font=DEFAULT_FONT, font_size=12.0, color=COLOR_TEXT).next_to(next_header, DOWN, buff=0.18)
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

        # Bottom Bridge Announcement to Episode 22
        bridge_banner = RoundedRectangle(
            corner_radius=0.12, width=10.6, height=0.70,
            fill_color="#181524", fill_opacity=0.95, stroke_color=COLOR_GOLD, stroke_width=1.5
        ).to_edge(DOWN, buff=0.35)
        bridge_header = Text(
            "ĐÓN XEM TẬP 22 // FUNCTION CALLING: BIẾN AI TỪ NÓI SUÔNG THÀNH KỸ SƯ HÀNH ĐỘNG",
            font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_GOLD
        ).move_to(bridge_banner.get_center())

        self.play(FadeIn(bridge_banner, shift=UP * 0.2), FadeIn(bridge_header), run_time=0.9)
        self.wait(2.0)
