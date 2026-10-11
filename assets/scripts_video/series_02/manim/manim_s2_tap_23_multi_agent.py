#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Manim 2K Mathematical Engine — Series 2, Episode 23: Multi-Agent Architecture
================================================================================
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

# 2K QHD 60fps Canvas Configuration
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
# SCENE 1: COLD OPEN — SINGLE-AGENT BOTTLENECK VS MULTI-AGENT CONSTELLATION
# ==============================================================================
class Tap23Scene01ColdOpen(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "ĐIỂM NGHẼN ĐƠN TỬ & KIẾN TRÚC ĐA TÁC TỬ")

        scene_title = Text(
            "ĐIỂM NGHẼN NHẬN THỨC: MONOLITH VS CHÒM SAO ĐA TÁC TỬ",
            font=DEFAULT_FONT, font_size=17.5, weight=BOLD, color=COLOR_GOLD
        )
        scene_title.to_edge(UP, buff=0.95)
        self.play(FadeIn(scene_title, shift=DOWN * 0.2), run_time=0.8)

        # Left Container: Single God-Agent Bottleneck (Monolith)
        monolith_card = RoundedRectangle(
            corner_radius=0.16, width=5.0, height=4.3,
            fill_color=COLOR_PANEL, fill_opacity=0.85, stroke_color=COLOR_ROSE, stroke_width=1.5
        ).move_to(LEFT * 3.4 + DOWN * 0.2)

        monolith_header = Text("MONOLITH GOD-AGENT", font=DEFAULT_FONT, font_size=13.0, weight=BOLD, color=COLOR_ROSE)
        monolith_header.next_to(monolith_card.get_top(), DOWN, buff=0.25)
        monolith_subtitle = Text("Quá tải vai trò & sụp đổ ngữ cảnh", font=DEFAULT_FONT, font_size=12.0, color=COLOR_MUTED)
        monolith_subtitle.next_to(monolith_header, DOWN, buff=0.15)

        # Pulsing Memory Stress Ring on Monolith
        monolith_core = Circle(
            radius=0.85, stroke_color=COLOR_ROSE, stroke_width=2.4,
            fill_color=COLOR_ROSE, fill_opacity=0.22
        ).move_to(LEFT * 3.4 + DOWN * 0.2)
        stress_ring = Annulus(
            inner_radius=0.85, outer_radius=1.20,
            stroke_color=COLOR_ROSE, stroke_width=1.4, fill_opacity=0.10
        ).move_to(LEFT * 3.4 + DOWN * 0.2)

        math_stress = fit_math_to_card(
            r"M_{\text{context}} \to \text{OOM} \implies \text{Error} \uparrow",
            monolith_card, font_size=20.0, color=COLOR_ROSE
        ).next_to(monolith_core, DOWN, buff=0.35)

        monolith_grp = VGroup(monolith_card, monolith_header, monolith_subtitle, monolith_core, stress_ring, math_stress)
        self.play(FadeIn(monolith_grp, shift=RIGHT * 0.3), run_time=1.0)

        # Right Container: Multi-Agent Constellation
        const_card = RoundedRectangle(
            corner_radius=0.16, width=5.8, height=4.3,
            fill_color=COLOR_PANEL, fill_opacity=0.85, stroke_color=COLOR_CYAN, stroke_width=1.5
        ).move_to(RIGHT * 3.4 + DOWN * 0.2)

        const_header = Text("CHÒM SAO MULTI-AGENT SWARM", font=DEFAULT_FONT, font_size=13.0, weight=BOLD, color=COLOR_CYAN)
        const_header.next_to(const_card.get_top(), DOWN, buff=0.25)
        const_subtitle = Text("Phân rã vai trò & phản biện độc lập", font=DEFAULT_FONT, font_size=12.0, color=COLOR_MUTED)
        const_subtitle.next_to(const_header, DOWN, buff=0.15)

        # 4 Specialized Nodes in Orbital Topology
        node_orch = Circle(radius=0.38, fill_color=COLOR_PANEL, fill_opacity=0.9, stroke_color=COLOR_VIOLET, stroke_width=2.0).move_to(RIGHT * 3.4 + UP * 0.8)
        orch_header = Text("ORCH", font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_VIOLET).move_to(node_orch.get_center())

        node_arch = Circle(radius=0.38, fill_color=COLOR_PANEL, fill_opacity=0.9, stroke_color=COLOR_CYAN, stroke_width=2.0).move_to(RIGHT * 1.8 + DOWN * 0.2)
        arch_header = Text("ARCH", font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_CYAN).move_to(node_arch.get_center())

        node_code = Circle(radius=0.38, fill_color=COLOR_PANEL, fill_opacity=0.9, stroke_color=COLOR_GOLD, stroke_width=2.0).move_to(RIGHT * 5.0 + DOWN * 0.2)
        code_header = Text("CODE", font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_GOLD).move_to(node_code.get_center())

        node_crit = Circle(radius=0.38, fill_color=COLOR_PANEL, fill_opacity=0.9, stroke_color=COLOR_GREEN, stroke_width=2.0).move_to(RIGHT * 3.4 + DOWN * 1.2)
        crit_header = Text("CRIT", font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_GREEN).move_to(node_crit.get_center())

        nodes_grp = VGroup(
            node_orch, orch_header,
            node_arch, arch_header,
            node_code, code_header,
            node_crit, crit_header,
        )

        # Token Laser Beam Network Connections
        beam_oa = DashedLine(node_orch.get_center(), node_arch.get_center(), color=COLOR_CYAN, stroke_width=1.8, dash_length=0.08)
        beam_oc = DashedLine(node_orch.get_center(), node_code.get_center(), color=COLOR_GOLD, stroke_width=1.8, dash_length=0.08)
        beam_ac = DashedLine(node_arch.get_center(), node_code.get_center(), color=COLOR_CYAN, stroke_width=1.8, dash_length=0.08)
        beam_cc = DashedLine(node_code.get_center(), node_crit.get_center(), color=COLOR_GREEN, stroke_width=1.8, dash_length=0.08)
        beam_co = DashedLine(node_crit.get_center(), node_orch.get_center(), color=COLOR_VIOLET, stroke_width=1.8, dash_length=0.08)
        beams_grp = VGroup(beam_oa, beam_oc, beam_ac, beam_cc, beam_co)

        const_grp = VGroup(const_card, const_header, const_subtitle, beams_grp, nodes_grp)
        self.play(FadeIn(const_grp, shift=LEFT * 0.3), run_time=1.2)

        # Dynamic Token Laser Beams along network
        token1 = Dot(point=node_orch.get_center(), radius=0.09, color=COLOR_CYAN)
        token2 = Dot(point=node_arch.get_center(), radius=0.09, color=COLOR_GOLD)
        token3 = Dot(point=node_code.get_center(), radius=0.09, color=COLOR_GREEN)
        self.add(token1, token2, token3)

        self.play(
            token1.animate.move_to(node_arch.get_center()),
            token2.animate.move_to(node_code.get_center()),
            token3.animate.move_to(node_crit.get_center()),
            run_time=1.5,
        )
        self.play(
            token1.animate.move_to(node_code.get_center()),
            token2.animate.move_to(node_crit.get_center()),
            token3.animate.move_to(node_orch.get_center()),
            run_time=1.5,
        )

        # Dynamic ValueTracker kinetics
        stress_tracker = ValueTracker(1.0)
        self.play(stress_tracker.animate.set_value(1.4), run_time=1.0)

        # Bottom HUD Metric Box
        hud_box = RoundedRectangle(
            corner_radius=0.12, width=10.6, height=0.68,
            fill_color="#101422", fill_opacity=0.95, stroke_color=COLOR_GOLD, stroke_width=1.2
        ).to_edge(DOWN, buff=0.35)
        hud_header = Text(
            "MULTI-AGENT PARADIGM SHIFT // ERROR RATE -78% // CONTEXT PURITY 100%",
            font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_GOLD
        )
        hud_header.move_to(hud_box.get_center())

        self.play(FadeIn(hud_box, shift=UP * 0.2), FadeIn(hud_header), run_time=0.9)
        self.wait(1.5)


# ==============================================================================
# SCENE 2: ARCHITECTURE — TOPOLOGY COMPARISON MATRIX (4 QUADRANTS)
# ==============================================================================
class Tap23Scene02Architecture(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "MA TRẬN TÔ-PÔ GIAO TIẾP ĐA TÁC TỬ")

        scene_title = Text(
            "MA TRẬN KIẾN TRÚC GIAO TIẾP: 4 TÔ-PÔ ĐIỀU PHỐI ĐA TÁC TỬ",
            font=DEFAULT_FONT, font_size=17.0, weight=BOLD, color=COLOR_CYAN
        )
        scene_title.to_edge(UP, buff=0.95)
        self.play(FadeIn(scene_title, shift=DOWN * 0.2), run_time=0.8)

        # Subtle hairline quadrant dividers
        h_line = DashedLine(LEFT * 5.8, RIGHT * 5.8, color="#263147", stroke_width=1.2, dash_length=0.10).move_to(DOWN * 0.3)
        v_line = DashedLine(UP * 2.6, DOWN * 3.2, color="#263147", stroke_width=1.2, dash_length=0.10).move_to(ORIGIN)
        self.play(Create(h_line), Create(v_line), run_time=0.8)

        # ---------------------------------------------------------------------
        # Quadrant 1 (Top-Left): Sequential Pipeline (A -> B -> C)
        # ---------------------------------------------------------------------
        q1_card = RoundedRectangle(
            corner_radius=0.14, width=5.4, height=2.4,
            fill_color=COLOR_PANEL, fill_opacity=0.85, stroke_color=COLOR_CYAN, stroke_width=1.2
        ).move_to(LEFT * 3.2 + UP * 1.25)
        seq_header = Text("1. SEQUENTIAL PIPELINE", font=DEFAULT_FONT, font_size=12.5, weight=BOLD, color=COLOR_CYAN)
        seq_header.next_to(q1_card.get_top(), DOWN, buff=0.18)
        seq_subtitle = Text("Dây chuyền xử lý tuần tự tuyến tính", font=DEFAULT_FONT, font_size=12.0, color=COLOR_MUTED)
        seq_subtitle.next_to(seq_header, DOWN, buff=0.10)

        n1_a = Circle(radius=0.28, color=COLOR_CYAN, fill_opacity=0.35, stroke_width=1.6).move_to(LEFT * 4.6 + UP * 0.7)
        n1_b = Circle(radius=0.28, color=COLOR_CYAN, fill_opacity=0.35, stroke_width=1.6).move_to(LEFT * 3.2 + UP * 0.7)
        n1_c = Circle(radius=0.28, color=COLOR_CYAN, fill_opacity=0.35, stroke_width=1.6).move_to(LEFT * 1.8 + UP * 0.7)
        lbl_1a = Text("A", font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_CYAN).move_to(n1_a.get_center())
        lbl_1b = Text("B", font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_CYAN).move_to(n1_b.get_center())
        lbl_1c = Text("C", font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_CYAN).move_to(n1_c.get_center())
        arr_1ab = ZenArrow(n1_a.get_right(), n1_b.get_left(), color=COLOR_CYAN, stroke_width=2.0)
        arr_1bc = ZenArrow(n1_b.get_right(), n1_c.get_left(), color=COLOR_CYAN, stroke_width=2.0)
        q1_grp = VGroup(q1_card, seq_header, seq_subtitle, n1_a, n1_b, n1_c, lbl_1a, lbl_1b, lbl_1c, arr_1ab, arr_1bc)

        # ---------------------------------------------------------------------
        # Quadrant 2 (Top-Right): Hierarchical Tree (Orchestrator -> Workers)
        # ---------------------------------------------------------------------
        q2_card = RoundedRectangle(
            corner_radius=0.14, width=5.4, height=2.4,
            fill_color=COLOR_PANEL, fill_opacity=0.85, stroke_color=COLOR_VIOLET, stroke_width=1.2
        ).move_to(RIGHT * 3.2 + UP * 1.25)
        hier_header = Text("2. HIERARCHICAL TREE", font=DEFAULT_FONT, font_size=12.5, weight=BOLD, color=COLOR_VIOLET)
        hier_header.next_to(q2_card.get_top(), DOWN, buff=0.18)
        hier_subtitle = Text("Mô hình Quản đốc phân cấp ủy quyền", font=DEFAULT_FONT, font_size=12.0, color=COLOR_MUTED)
        hier_subtitle.next_to(hier_header, DOWN, buff=0.10)

        n2_root = Circle(radius=0.28, color=COLOR_VIOLET, fill_opacity=0.35, stroke_width=1.6).move_to(RIGHT * 3.2 + UP * 1.2)
        lbl_root = Text("ORCH", font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_VIOLET).move_to(n2_root.get_center())
        n2_w1 = Circle(radius=0.24, color=COLOR_CYAN, fill_opacity=0.35, stroke_width=1.5).move_to(RIGHT * 1.9 + UP * 0.45)
        n2_w2 = Circle(radius=0.24, color=COLOR_GOLD, fill_opacity=0.35, stroke_width=1.5).move_to(RIGHT * 3.2 + UP * 0.45)
        n2_w3 = Circle(radius=0.24, color=COLOR_GREEN, fill_opacity=0.35, stroke_width=1.5).move_to(RIGHT * 4.5 + UP * 0.45)
        arr_rw1 = ZenArrow(n2_root.get_bottom(), n2_w1.get_top(), color=COLOR_VIOLET, stroke_width=1.8)
        arr_rw2 = ZenArrow(n2_root.get_bottom(), n2_w2.get_top(), color=COLOR_VIOLET, stroke_width=1.8)
        arr_rw3 = ZenArrow(n2_root.get_bottom(), n2_w3.get_top(), color=COLOR_VIOLET, stroke_width=1.8)
        q2_grp = VGroup(q2_card, hier_header, hier_subtitle, n2_root, lbl_root, n2_w1, n2_w2, n2_w3, arr_rw1, arr_rw2, arr_rw3)

        self.play(FadeIn(q1_grp, shift=RIGHT * 0.2), FadeIn(q2_grp, shift=LEFT * 0.2), run_time=1.1)

        # ---------------------------------------------------------------------
        # Quadrant 3 (Bottom-Left): Joint Blackboard (Shared Memory Hub)
        # ---------------------------------------------------------------------
        q3_card = RoundedRectangle(
            corner_radius=0.14, width=5.4, height=2.4,
            fill_color=COLOR_PANEL, fill_opacity=0.85, stroke_color=COLOR_GOLD, stroke_width=1.2
        ).move_to(LEFT * 3.2 + DOWN * 1.85)
        blackboard_header = Text("3. JOINT BLACKBOARD", font=DEFAULT_FONT, font_size=12.5, weight=BOLD, color=COLOR_GOLD)
        blackboard_header.next_to(q3_card.get_top(), DOWN, buff=0.18)
        blackboard_subtitle = Text("Bảng tin bộ nhớ chung bất đồng bộ", font=DEFAULT_FONT, font_size=12.0, color=COLOR_MUTED)
        blackboard_subtitle.next_to(blackboard_header, DOWN, buff=0.10)

        hub_ring = Annulus(inner_radius=0.25, outer_radius=0.45, fill_color=COLOR_GOLD, fill_opacity=0.25, stroke_color=COLOR_GOLD, stroke_width=1.6).move_to(LEFT * 3.2 + DOWN * 2.2)
        hub_header = Text("STATE", font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_GOLD).move_to(hub_ring.get_center())
        b_a1 = Dot(point=LEFT * 4.5 + DOWN * 2.2, radius=0.15, color=COLOR_CYAN)
        b_a2 = Dot(point=LEFT * 1.9 + DOWN * 2.2, radius=0.15, color=COLOR_GREEN)
        b_dash1 = DashedLine(b_a1.get_center(), hub_ring.get_left(), color=COLOR_CYAN, stroke_width=1.6)
        b_dash2 = DashedLine(b_a2.get_center(), hub_ring.get_right(), color=COLOR_GREEN, stroke_width=1.6)
        q3_grp = VGroup(q3_card, blackboard_header, blackboard_subtitle, hub_ring, hub_header, b_a1, b_a2, b_dash1, b_dash2)

        # ---------------------------------------------------------------------
        # Quadrant 4 (Bottom-Right): Multi-Agent Debate Graph
        # ---------------------------------------------------------------------
        q4_card = RoundedRectangle(
            corner_radius=0.14, width=5.4, height=2.4,
            fill_color=COLOR_PANEL, fill_opacity=0.85, stroke_color=COLOR_GREEN, stroke_width=1.2
        ).move_to(RIGHT * 3.2 + DOWN * 1.85)
        debate_header = Text("4. ADVERSARIAL DEBATE", font=DEFAULT_FONT, font_size=12.5, weight=BOLD, color=COLOR_GREEN)
        debate_header.next_to(q4_card.get_top(), DOWN, buff=0.18)
        debate_subtitle = Text("Tranh luận đối kháng triệt tiêu lỗi", font=DEFAULT_FONT, font_size=12.0, color=COLOR_MUTED)
        debate_subtitle.next_to(debate_header, DOWN, buff=0.10)

        deb_p = Circle(radius=0.32, color=COLOR_CYAN, fill_opacity=0.35, stroke_width=1.6).move_to(RIGHT * 2.1 + DOWN * 2.2)
        deb_c = Circle(radius=0.32, color=COLOR_ROSE, fill_opacity=0.35, stroke_width=1.6).move_to(RIGHT * 4.3 + DOWN * 2.2)
        lbl_p = Text("PROP", font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_CYAN).move_to(deb_p.get_center())
        lbl_c = Text("CRIT", font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_ROSE).move_to(deb_c.get_center())
        arr_fwd = ZenCurvedArrow(deb_p.get_top(), deb_c.get_top(), color=COLOR_CYAN, stroke_width=2.2, angle=0.45)
        arr_rev = ZenCurvedArrow(deb_c.get_bottom(), deb_p.get_bottom(), color=COLOR_ROSE, stroke_width=2.2, angle=-0.45)
        q4_grp = VGroup(q4_card, debate_header, debate_subtitle, deb_p, deb_c, lbl_p, lbl_c, arr_fwd, arr_rev)

        self.play(FadeIn(q3_grp, shift=RIGHT * 0.2), FadeIn(q4_grp, shift=LEFT * 0.2), run_time=1.1)

        # Dynamic Token packet animating debate exchange
        deb_token = Dot(point=deb_p.get_center(), radius=0.08, color=COLOR_CYAN)
        self.add(deb_token)
        self.play(MoveAlongPath(deb_token, arr_fwd), run_time=1.2)
        deb_token.set_color(COLOR_ROSE)
        self.play(MoveAlongPath(deb_token, arr_rev), run_time=1.2)

        self.wait(1.5)


# ==============================================================================
# SCENE 3: MATHEMATICS — CONDORCET'S JURY THEOREM DYNAMIC CONVERGENCE CURVE
# ==============================================================================
class Tap23Scene03Mathematics(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "TOÁN HỌC TRANH LUẬN & ĐỊNH LÝ CONDORCET")

        scene_title = Text(
            "TOÁN HỌC ĐỘNG LỰC TRANH LUẬN: ĐỊNH LÝ BỒI THẨM ĐOÀN CONDORCET",
            font=DEFAULT_FONT, font_size=17.0, weight=BOLD, color=COLOR_GOLD
        )
        scene_title.to_edge(UP, buff=0.95)
        self.play(FadeIn(scene_title, shift=DOWN * 0.2), run_time=0.8)

        # Left Container: Formulas and Bound Card
        math_card = RoundedRectangle(
            corner_radius=0.15, width=5.6, height=4.5,
            fill_color=COLOR_PANEL, fill_opacity=0.85, stroke_color=COLOR_GOLD, stroke_width=1.5
        ).move_to(LEFT * 3.3 + DOWN * 0.2)

        math_header = Text("ĐỊNH LÝ CONDORCET // HỘI TỤ ĐA SỐ", font=DEFAULT_FONT, font_size=13.0, weight=BOLD, color=COLOR_GOLD)
        math_header.next_to(math_card.get_top(), DOWN, buff=0.25)
        cond_subtitle = Text("Khuếch đại xác suất cá nhân thành chân lý", font=DEFAULT_FONT, font_size=12.0, color=COLOR_MUTED)
        cond_subtitle.next_to(math_header, DOWN, buff=0.12)

        formula_cond = fit_math_to_card(
            r"\mu(N) = \sum_{k=\lceil N/2 \rceil}^N \binom{N}{k} p^k (1-p)^{N-k}",
            math_card, font_size=23.0, color=COLOR_CYAN
        ).next_to(cond_subtitle, DOWN, buff=0.32)

        formula_lim = fit_math_to_card(
            r"\lim_{N \to \infty} \mu(N) = 1.0 \quad (\text{khi } p > 0.5)",
            math_card, font_size=22.0, color=COLOR_GREEN
        ).next_to(formula_cond, DOWN, buff=0.28)

        formula_err = fit_math_to_card(
            r"P_{\text{error}} \le \exp\left(-2N(p - 0.5)^2\right)",
            math_card, font_size=21.0, color=COLOR_ROSE
        ).next_to(formula_lim, DOWN, buff=0.28)

        left_grp = VGroup(math_card, math_header, cond_subtitle, formula_cond, formula_lim, formula_err)
        self.play(FadeIn(left_grp, shift=RIGHT * 0.3), run_time=1.1)

        # Right Container: Plotted Dynamic Convergence Curve
        plot_card = RoundedRectangle(
            corner_radius=0.15, width=5.8, height=4.5,
            fill_color=COLOR_PANEL, fill_opacity=0.85, stroke_color=COLOR_CYAN, stroke_width=1.5
        ).move_to(RIGHT * 3.3 + DOWN * 0.2)

        plot_header = Text("ĐƯỜNG CONG HỘI TỤ CONDORCET (p = 0.65)", font=DEFAULT_FONT, font_size=13.0, weight=BOLD, color=COLOR_CYAN)
        plot_header.next_to(plot_card.get_top(), DOWN, buff=0.25)

        axes = Axes(
            x_range=[1, 21, 5],
            y_range=[0.5, 1.05, 0.1],
            x_length=4.6,
            y_length=2.8,
            axis_config={"color": COLOR_MUTED, "stroke_width": 1.2, "include_ticks": True},
            tips=False,
        ).move_to(RIGHT * 3.3 + DOWN * 0.45)

        x_header = Text("N (Số tác tử)", font=DEFAULT_FONT, font_size=12.0, color=COLOR_TEXT).next_to(axes.x_axis, DOWN, buff=0.15)
        y_header = Text("mu(N)", font=DEFAULT_FONT, font_size=12.0, color=COLOR_TEXT).next_to(axes.y_axis, LEFT, buff=0.15)
        axes_grp = VGroup(plot_card, plot_header, axes, x_header, y_header)
        self.play(FadeIn(axes_grp, shift=LEFT * 0.3), run_time=1.0)

        # Continuous smooth convergence curve function for p = 0.65
        def condorcet_curve_fn(x):
            # Normal cumulative approximation for majority voting
            z = (0.65 - 0.5) * math.sqrt(max(1.0, x)) / math.sqrt(0.65 * 0.35)
            # erf based approximation
            prob = 0.5 + 0.5 * math.erf(z / math.sqrt(2.0))
            return min(0.999, max(0.65, prob))

        curve = axes.plot(condorcet_curve_fn, x_range=[1, 21], color=COLOR_GREEN, stroke_width=2.5)
        self.play(Create(curve), run_time=1.5)

        # Dynamic ValueTracker dot and tracker readout
        n_tracker = ValueTracker(1.0)

        tracker_dot = always_redraw(
            lambda: Dot(
                axes.c2p(n_tracker.get_value(), condorcet_curve_fn(n_tracker.get_value())),
                radius=0.09, color=COLOR_GOLD
            )
        )
        readout_header = Text("ĐỘ CHÍNH XÁC:", font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_GOLD)
        readout_header.next_to(axes, UP, buff=0.15).align_to(axes, LEFT)

        readout_num = DecimalNumber(65.0, num_decimal_places=1, unit="%", font_size=18, color=COLOR_GOLD)
        readout_num.next_to(readout_header, RIGHT, buff=0.15)
        readout_num.add_updater(
            lambda d: d.set_value(condorcet_curve_fn(n_tracker.get_value()) * 100.0)
        )

        self.add(tracker_dot, readout_header, readout_num)

        # Animate tracker converging from N=1 to N=21
        self.play(n_tracker.animate.set_value(21.0), run_time=4.5, rate_func=linear)
        self.wait(1.5)


# ==============================================================================
# SCENE 4: TELEMETRY — SWE-BENCH & HUMANEVAL COMPARISON BENCHMARK
# ==============================================================================
class Tap23Scene04Telemetry(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "ĐO KIỂM TELEMETRY MULTI-AGENT")

        scene_title = Text(
            "BẢNG ĐO KIỂM HIỆU NĂNG THỰC TẾ: SWE-BENCH RESOLVE RATE (%)",
            font=DEFAULT_FONT, font_size=17.5, weight=BOLD, color=COLOR_CYAN
        )
        scene_title.to_edge(UP, buff=0.95)
        self.play(FadeIn(scene_title, shift=DOWN * 0.2), run_time=0.8)

        # Telemetry Main Card
        telemetry_card = RoundedRectangle(
            corner_radius=0.16, width=10.8, height=4.6,
            fill_color=COLOR_PANEL, fill_opacity=0.9, stroke_color=COLOR_CYAN, stroke_width=1.5
        ).move_to(DOWN * 0.25)
        self.play(FadeIn(telemetry_card), run_time=0.6)

        benchmarks = [
            ("Single Model (Zero-Shot)", 13.4, COLOR_ROSE),
            ("Single Model + CoT", 21.2, COLOR_GOLD),
            ("AutoGen Multi-Agent (3 Roles)", 48.6, COLOR_GREEN),
        ]

        bars_grp = VGroup()
        for i, (name, val, col) in enumerate(benchmarks):
            item_header = Text(name, font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_TEXT)
            item_header.move_to(LEFT * 4.3 + UP * (0.9 - i * 1.05), aligned_edge=LEFT)

            bar_bg = RoundedRectangle(
                corner_radius=0.08, width=5.6, height=0.38,
                fill_color="#0d111a", fill_opacity=0.9, stroke_color=COLOR_MUTED, stroke_width=0.8
            ).next_to(item_header, RIGHT, buff=0.4)

            fill_width = (val / 60.0) * 5.6
            bar_fill = RoundedRectangle(
                corner_radius=0.08, width=fill_width, height=0.38,
                fill_color=col, fill_opacity=0.9, stroke_color=col, stroke_width=1.0
            ).align_to(bar_bg, LEFT)

            val_header = Text(f"{val}%", font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=col)
            val_header.next_to(bar_fill, RIGHT, buff=0.2)

            bars_grp.add(item_header, bar_bg, bar_fill, val_header)

        self.play(FadeIn(bars_grp), run_time=1.2)

        # Metric Banner inside card
        metric_card = RoundedRectangle(
            corner_radius=0.10, width=9.8, height=0.68,
            fill_color="#101422", fill_opacity=0.95, stroke_color=COLOR_GOLD, stroke_width=1.2
        ).next_to(telemetry_card.get_bottom(), UP, buff=0.25)

        metric_header = Text(
            "TỶ LỆ GIẢI QUYẾT TĂNG GẦN 4 LẦN NHỜ VÒNG LẶP PHẢN BIỆN TỰ ĐỘNG",
            font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_GOLD
        )
        metric_header.move_to(metric_card.get_center())

        self.play(FadeIn(metric_card, shift=UP * 0.2), FadeIn(metric_header), run_time=0.9)
        self.wait(1.5)


# ==============================================================================
# SCENE 5: LAB EXPERIMENT — SELF-HEALING RED-TEAMING FEEDBACK LOOP
# ==============================================================================
class Tap23Scene05LabExperiment(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "THỰC NGHIỆM TỰ CHỮA LÀNH (SELF-HEALING)")

        scene_title = Text(
            "KIẾN TRÚC TỰ CHỮA LÀNH: VÒNG LẶP PHẢN BIỆN ĐỐI KHÁNG (SELF-HEALING)",
            font=DEFAULT_FONT, font_size=16.5, weight=BOLD, color=COLOR_GOLD
        )
        scene_title.to_edge(UP, buff=0.95)
        self.play(FadeIn(scene_title, shift=DOWN * 0.2), run_time=0.8)

        # 3 Nodes in Cyclic State Machine at Y = +0.7
        box_coder = RoundedRectangle(
            corner_radius=0.14, width=2.8, height=1.9,
            fill_color=COLOR_PANEL, fill_opacity=0.9, stroke_color=COLOR_CYAN, stroke_width=1.8
        ).move_to(LEFT * 3.8 + UP * 0.7)
        coder_header = Text("CODER AGENT (S0)", font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_CYAN)
        coder_header.next_to(box_coder.get_top(), DOWN, buff=0.25)
        coder_subtitle = Text("Sinh mã & hiệu chỉnh", font=DEFAULT_FONT, font_size=12.0, color=COLOR_MUTED)
        coder_subtitle.next_to(coder_header, DOWN, buff=0.18)
        coder_grp = VGroup(box_coder, coder_header, coder_subtitle)

        box_sandbox = RoundedRectangle(
            corner_radius=0.14, width=2.8, height=1.9,
            fill_color=COLOR_PANEL, fill_opacity=0.9, stroke_color=COLOR_GOLD, stroke_width=1.8
        ).move_to(ORIGIN + UP * 0.7)
        sandbox_header = Text("CI SANDBOX (S1)", font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_GOLD)
        sandbox_header.next_to(box_sandbox.get_top(), DOWN, buff=0.25)
        sandbox_subtitle = Text("Biên dịch & kiểm thử", font=DEFAULT_FONT, font_size=12.0, color=COLOR_MUTED)
        sandbox_subtitle.next_to(sandbox_header, DOWN, buff=0.18)
        sandbox_grp = VGroup(box_sandbox, sandbox_header, sandbox_subtitle)

        box_critic = RoundedRectangle(
            corner_radius=0.14, width=2.8, height=1.9,
            fill_color=COLOR_PANEL, fill_opacity=0.9, stroke_color=COLOR_ROSE, stroke_width=1.8
        ).move_to(RIGHT * 3.8 + UP * 0.7)
        critic_header = Text("CRITIC AUDITOR (S2)", font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_ROSE)
        critic_header.next_to(box_critic.get_top(), DOWN, buff=0.25)
        critic_subtitle = Text("Soi lỗi biên & bảo mật", font=DEFAULT_FONT, font_size=12.0, color=COLOR_MUTED)
        critic_subtitle.next_to(critic_header, DOWN, buff=0.18)
        critic_grp = VGroup(box_critic, critic_header, critic_subtitle)

        self.play(FadeIn(coder_grp), FadeIn(sandbox_grp), FadeIn(critic_grp), run_time=1.0)

        # Forward transition arrows
        arr_01 = ZenArrow(box_coder.get_right(), box_sandbox.get_left(), color=COLOR_CYAN, stroke_width=2.2)
        arr_12 = ZenArrow(box_sandbox.get_right(), box_critic.get_left(), color=COLOR_GOLD, stroke_width=2.2)
        self.play(GrowArrow(arr_01), GrowArrow(arr_12), run_time=0.8)

        # Reverse negative feedback arc (theta <= 0 down into empty lower space)
        feedback_arc = ZenCurvedArrow(
            box_critic.get_bottom() + DOWN * 0.08,
            box_coder.get_bottom() + DOWN * 0.08,
            color=COLOR_ROSE, stroke_width=2.5, angle=-0.55
        )
        feedback_header = Text("PHẢN HỒI LỖI (FEEDBACK ARC theta <= 0)", font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_ROSE)
        feedback_header.next_to(feedback_arc, DOWN, buff=0.12)

        self.play(Create(feedback_arc), FadeIn(feedback_header), run_time=1.0)

        # Self-Healing Iteration Pulse
        pulse_dot = Dot(point=box_critic.get_bottom(), radius=0.09, color=COLOR_ROSE)
        self.add(pulse_dot)
        self.play(MoveAlongPath(pulse_dot, feedback_arc), run_time=1.4)
        self.remove(pulse_dot)

        # Human-in-the-loop Approval Gate
        gate_box = RoundedRectangle(
            corner_radius=0.12, width=8.6, height=1.1,
            fill_color="#0a1f14", fill_opacity=0.95, stroke_color=COLOR_GREEN, stroke_width=1.6
        ).move_to(DOWN * 2.2)
        gate_header = Text("HUMAN-IN-THE-LOOP APPROVAL GATE [VERIFIED]", font=DEFAULT_FONT, font_size=12.5, weight=BOLD, color=COLOR_GREEN)
        gate_header.next_to(gate_box.get_top(), DOWN, buff=0.20)
        gate_subtitle = Text("Con người giữ quyền phê duyệt tối cao & kiểm soát chất lượng", font=DEFAULT_FONT, font_size=12.0, color=COLOR_TEXT)
        gate_subtitle.next_to(gate_header, DOWN, buff=0.14)
        gate_grp = VGroup(gate_box, gate_header, gate_subtitle)

        arr_gate = ZenArrow(box_sandbox.get_bottom(), gate_box.get_top(), color=COLOR_GREEN, stroke_width=2.2)
        self.play(GrowArrow(arr_gate), FadeIn(gate_grp, shift=UP * 0.2), run_time=1.0)
        self.wait(1.5)


# ==============================================================================
# SCENE 6: OUTRO & 5X5 THUMBNAIL MOSAIC (YOUTUBE SAFE ZONE COMPLIANT)
# ==============================================================================
class Tap23Scene06Outro(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "BÀN GIAO TRI THỨC VÀ CẦU NỐI KỸ NGHỆ")

        scene_title = Text(
            "BÀN GIAO TRI THỨC // MA TRẬN MULTI-AGENT ARCHITECTURE",
            font=DEFAULT_FONT, font_size=15.0, weight=BOLD, color=COLOR_GOLD
        )
        scene_title.to_edge(UP, buff=0.95)
        self.play(FadeIn(scene_title, shift=DOWN * 0.2), run_time=0.8)

        # Left Side: 5x5 Closing Thumbnail Mosaic
        # Relative & absolute path resolution for Docker / host environments
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
        # 1. Next Video Card (Episode 24): X in [+1.6, +5.4], Y in [+0.5, +2.5]
        # Clearance to mosaic right edge (-0.30): +1.60 - (-0.30) = 1.90 units = 342px >= 300px!
        next_card = RoundedRectangle(
            corner_radius=0.12, width=3.8, height=2.0,
            fill_color=COLOR_PANEL, fill_opacity=0.7, stroke_color=COLOR_CYAN, stroke_width=1.5
        ).move_to(RIGHT * 3.5 + UP * 1.5)
        next_header = Text("TẬP TIẾP THEO // TẬP 24", font=DEFAULT_FONT, font_size=12.5, weight=BOLD, color=COLOR_CYAN)
        next_sub_header = Text("DISTRIBUTED TRAINING: HUẤN LUYỆN AI PHÂN TÁN", font=DEFAULT_FONT, font_size=12.0, color=COLOR_TEXT).next_to(next_header, DOWN, buff=0.18)
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
        self.play(FadeIn(right_grp, shift=LEFT * 0.3), run_time=1.0)

        # Bottom Bridge Announcement to Episode 24
        teaser_header = Text(
            "HƯỚNG TỚI TẬP 24: DISTRIBUTED TRAINING — ĐIỀU PHỐI HÀNG VẠN GPU HUẤN LUYỆN SONG SONG",
            font=DEFAULT_FONT, font_size=12.5, weight=BOLD, color=COLOR_CYAN
        )
        teaser_header.to_edge(DOWN, buff=0.45)
        self.play(FadeIn(teaser_header, shift=UP * 0.2), run_time=0.8)
        self.wait(2.0)
