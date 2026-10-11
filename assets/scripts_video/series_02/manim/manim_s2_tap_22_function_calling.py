#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Manim 2K Mathematical Engine — Series 2, Episode 22: Function Calling & Tool Use
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
# SCENE 1: COLD OPEN — THE PAPER POET PARADOX VS TOOL-AUGMENTED AGENTS
# ==============================================================================
class Tap22Scene01ColdOpen(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "NGHỊCH LÝ NHÀ THƠ BÀN GIẤY & FUNCTION CALLING")

        scene_title = Text(
            "NGHỊCH LÝ NHÀ THƠ BÀN GIẤY: LLM CÔ LẬP VS AGENT CÓ CÔNG CỤ",
            font=DEFAULT_FONT, font_size=17.5, weight=BOLD, color=COLOR_GOLD
        )
        scene_title.to_edge(UP, buff=0.95)
        self.play(FadeIn(scene_title, shift=DOWN * 0.2), run_time=0.8)

        # Left Container: The Isolated LLM Monolith
        monolith_card = RoundedRectangle(
            corner_radius=0.16, width=5.2, height=4.4,
            fill_color=COLOR_PANEL, fill_opacity=0.85, stroke_color=COLOR_ROSE, stroke_width=1.5
        ).move_to(LEFT * 3.3 + DOWN * 0.2)

        monolith_header = Text("LLM CÔ LẬP TRONG KÍNH", font=DEFAULT_FONT, font_size=13.0, weight=BOLD, color=COLOR_ROSE)
        monolith_header.next_to(monolith_card.get_top(), DOWN, buff=0.25)
        monolith_subtitle = Text("Dự đoán token thụ động, không tác động", font=DEFAULT_FONT, font_size=12.0, color=COLOR_MUTED)
        monolith_subtitle.next_to(monolith_header, DOWN, buff=0.12)

        # Central LLM core with stress/barrier ring
        monolith_core = Circle(
            radius=0.80, stroke_color=COLOR_ROSE, stroke_width=2.2,
            fill_color=COLOR_ROSE, fill_opacity=0.22
        ).move_to(LEFT * 3.3 + DOWN * 0.25)
        core_header = Text("LLM CORE", font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_ROSE).move_to(monolith_core.get_center())

        barrier_ring = Annulus(
            inner_radius=0.80, outer_radius=1.15,
            stroke_color=COLOR_ROSE, stroke_width=1.4, fill_opacity=0.10
        ).move_to(LEFT * 3.3 + DOWN * 0.25)

        math_monolith = fit_math_to_card(
            r"P(w_{t+1} \mid w_{1:t}) \implies \text{No Side Effects}",
            monolith_card, font_size=20.0, color=COLOR_ROSE
        ).next_to(barrier_ring, DOWN, buff=0.30)

        left_grp = VGroup(monolith_card, monolith_header, monolith_subtitle, monolith_core, core_header, barrier_ring, math_monolith)
        self.play(FadeIn(left_grp, shift=RIGHT * 0.3), run_time=1.0)

        # Right Container: Tool-Augmented Agent with Function Calling Bridge
        agent_card = RoundedRectangle(
            corner_radius=0.16, width=5.8, height=4.4,
            fill_color=COLOR_PANEL, fill_opacity=0.85, stroke_color=COLOR_CYAN, stroke_width=1.5
        ).move_to(RIGHT * 3.3 + DOWN * 0.2)

        agent_header = Text("AGENT CÔNG CỤ THỰC THI", font=DEFAULT_FONT, font_size=13.0, weight=BOLD, color=COLOR_CYAN)
        agent_header.next_to(agent_card.get_top(), DOWN, buff=0.25)
        agent_subtitle = Text("Giao tiếp API qua JSON Schema chuẩn hóa", font=DEFAULT_FONT, font_size=12.0, color=COLOR_MUTED)
        agent_subtitle.next_to(agent_header, DOWN, buff=0.12)

        # Central Agent Hub
        node_agent = Circle(
            radius=0.48, fill_color=COLOR_PANEL, fill_opacity=0.95,
            stroke_color=COLOR_CYAN, stroke_width=2.2
        ).move_to(RIGHT * 2.1 + DOWN * 0.25)
        agent_node_header = Text("AGENT", font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_CYAN).move_to(node_agent.get_center())

        # 3 External Tool Nodes
        node_calc = Circle(radius=0.34, fill_color=COLOR_PANEL, fill_opacity=0.9, stroke_color=COLOR_GOLD, stroke_width=1.8).move_to(RIGHT * 4.6 + UP * 0.95)
        calc_header = Text("MATH", font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_GOLD).move_to(node_calc.get_center())

        node_sql = Circle(radius=0.34, fill_color=COLOR_PANEL, fill_opacity=0.9, stroke_color=COLOR_GREEN, stroke_width=1.8).move_to(RIGHT * 5.0 + DOWN * 0.25)
        sql_header = Text("SQL", font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_GREEN).move_to(node_sql.get_center())

        node_api = Circle(radius=0.34, fill_color=COLOR_PANEL, fill_opacity=0.9, stroke_color=COLOR_VIOLET, stroke_width=1.8).move_to(RIGHT * 4.6 + DOWN * 1.45)
        api_header = Text("API", font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_VIOLET).move_to(node_api.get_center())

        beam_calc = DashedLine(node_agent.get_center(), node_calc.get_center(), color=COLOR_GOLD, stroke_width=1.8, dash_length=0.08)
        beam_sql = DashedLine(node_agent.get_center(), node_sql.get_center(), color=COLOR_GREEN, stroke_width=1.8, dash_length=0.08)
        beam_api = DashedLine(node_agent.get_center(), node_api.get_center(), color=COLOR_VIOLET, stroke_width=1.8, dash_length=0.08)

        right_grp = VGroup(
            agent_card, agent_header, agent_subtitle,
            beam_calc, beam_sql, beam_api,
            node_agent, agent_node_header,
            node_calc, calc_header,
            node_sql, sql_header,
            node_api, api_header,
        )
        self.play(FadeIn(right_grp, shift=LEFT * 0.3), run_time=1.2)

        # Dynamic Token laser beams pulsing along network
        token_calc = Dot(point=node_agent.get_center(), radius=0.08, color=COLOR_GOLD)
        token_sql = Dot(point=node_agent.get_center(), radius=0.08, color=COLOR_GREEN)
        token_api = Dot(point=node_agent.get_center(), radius=0.08, color=COLOR_VIOLET)
        self.add(token_calc, token_sql, token_api)

        self.play(
            token_calc.animate.move_to(node_calc.get_center()),
            token_sql.animate.move_to(node_sql.get_center()),
            token_api.animate.move_to(node_api.get_center()),
            run_time=1.4,
        )
        self.play(
            token_calc.animate.move_to(node_agent.get_center()),
            token_sql.animate.move_to(node_agent.get_center()),
            token_api.animate.move_to(node_agent.get_center()),
            run_time=1.4,
        )

        # Dynamic ValueTracker kinetics
        bridge_tracker = ValueTracker(1.0)
        self.play(bridge_tracker.animate.set_value(1.5), run_time=1.0)

        # Bottom HUD Metric Box
        hud_box = RoundedRectangle(
            corner_radius=0.12, width=10.6, height=0.68,
            fill_color="#101422", fill_opacity=0.95, stroke_color=COLOR_GOLD, stroke_width=1.2
        ).to_edge(DOWN, buff=0.35)
        hud_header = Text(
            "FUNCTION CALLING // CHUYỂN Ý ĐỊNH THÀNH LỜI GỌI HÀM SẢN XUẤT",
            font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_GOLD
        )
        hud_header.move_to(hud_box.get_center())

        self.play(FadeIn(hud_box, shift=UP * 0.2), FadeIn(hud_header), run_time=0.9)
        self.wait(1.5)


# ==============================================================================
# SCENE 2: ARCHITECTURE — REACT PROMPTING VS NATIVE TOOL CALLING
# ==============================================================================
class Tap22Scene02Architecture(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "TIẾN HÓA KIẾN TRÚC: REACT VS NATIVE TOOL USE")

        scene_title = Text(
            "TIẾN HÓA KIẾN TRÚC: REACT PROMPTING VS NATIVE TOOL CALLING",
            font=DEFAULT_FONT, font_size=17.0, weight=BOLD, color=COLOR_CYAN
        )
        scene_title.to_edge(UP, buff=0.95)
        self.play(FadeIn(scene_title, shift=DOWN * 0.2), run_time=0.8)

        # Hairline divider
        v_divider = DashedLine(UP * 2.4, DOWN * 3.0, color="#263147", stroke_width=1.2, dash_length=0.10).move_to(ORIGIN)
        self.play(Create(v_divider), run_time=0.6)

        # Left Container: ReAct Text Prompting (Fragile)
        react_card = RoundedRectangle(
            corner_radius=0.15, width=5.6, height=4.5,
            fill_color=COLOR_PANEL, fill_opacity=0.85, stroke_color=COLOR_ROSE, stroke_width=1.5
        ).move_to(LEFT * 3.3 + DOWN * 0.2)

        react_header = Text("1. REACT TEXT PROMPTING", font=DEFAULT_FONT, font_size=13.0, weight=BOLD, color=COLOR_ROSE)
        react_header.next_to(react_card.get_top(), DOWN, buff=0.25)
        react_subtitle = Text("Chuỗi văn bản tự do, phụ thuộc regex thô", font=DEFAULT_FONT, font_size=12.0, color=COLOR_MUTED)
        react_subtitle.next_to(react_header, DOWN, buff=0.12)

        # Flow Nodes: Thought -> Action -> Crash
        n_prompt = RoundedRectangle(corner_radius=0.1, width=3.8, height=0.55, fill_color="#1e1824", fill_opacity=0.9, stroke_color=COLOR_ROSE, stroke_width=1.2).move_to(LEFT * 3.3 + UP * 0.6)
        p_header = Text("Action: Calculator [25 * 40]", font=DEFAULT_FONT, font_size=12.0, color=COLOR_TEXT).move_to(n_prompt.get_center())

        arr_down1 = ZenArrow(n_prompt.get_bottom(), n_prompt.get_bottom() + DOWN * 0.45, color=COLOR_ROSE, stroke_width=1.8)

        n_parser = RoundedRectangle(corner_radius=0.1, width=3.8, height=0.55, fill_color="#1e1824", fill_opacity=0.9, stroke_color=COLOR_ROSE, stroke_width=1.2).next_to(arr_down1, DOWN, buff=0.10)
        parser_header = Text("JSON Regex Parser (Dễ vỡ)", font=DEFAULT_FONT, font_size=12.0, color=COLOR_ROSE).move_to(n_parser.get_center())

        arr_down2 = ZenArrow(n_parser.get_bottom(), n_parser.get_bottom() + DOWN * 0.45, color=COLOR_ROSE, stroke_width=1.8)

        math_react = fit_math_to_card(
            r"P(\text{Syntax Error}) = 14.5\% \implies \text{Crash}",
            react_card, font_size=19.0, color=COLOR_ROSE
        ).next_to(arr_down2, DOWN, buff=0.15)

        left_grp = VGroup(react_card, react_header, react_subtitle, n_prompt, p_header, arr_down1, n_parser, parser_header, arr_down2, math_react)
        self.play(FadeIn(left_grp, shift=RIGHT * 0.3), run_time=1.1)

        # Right Container: Native Tool Calling with JSON Schema
        native_card = RoundedRectangle(
            corner_radius=0.15, width=5.6, height=4.5,
            fill_color=COLOR_PANEL, fill_opacity=0.85, stroke_color=COLOR_GREEN, stroke_width=1.5
        ).move_to(RIGHT * 3.3 + DOWN * 0.2)

        native_header = Text("2. NATIVE TOOL CALLING", font=DEFAULT_FONT, font_size=13.0, weight=BOLD, color=COLOR_GREEN)
        native_header.next_to(native_card.get_top(), DOWN, buff=0.25)
        native_subtitle = Text("JSON Schema tường minh & Special Tokens", font=DEFAULT_FONT, font_size=12.0, color=COLOR_MUTED)
        native_subtitle.next_to(native_header, DOWN, buff=0.12)

        # Flow Nodes: Schema -> Model Token -> Execution
        n_schema = RoundedRectangle(corner_radius=0.1, width=4.2, height=0.55, fill_color="#14261e", fill_opacity=0.9, stroke_color=COLOR_GREEN, stroke_width=1.2).move_to(RIGHT * 3.3 + UP * 0.6)
        schema_header = Text("Schema: {\"name\": \"calc\", ...}", font=DEFAULT_FONT, font_size=12.0, color=COLOR_TEXT).move_to(n_schema.get_center())

        arr_down3 = ZenArrow(n_schema.get_bottom(), n_schema.get_bottom() + DOWN * 0.45, color=COLOR_GREEN, stroke_width=1.8)

        n_native = RoundedRectangle(corner_radius=0.1, width=4.2, height=0.55, fill_color="#14261e", fill_opacity=0.9, stroke_color=COLOR_CYAN, stroke_width=1.2).next_to(arr_down3, DOWN, buff=0.10)
        native_token_header = Text("<tool_call> {\"args\": ...} </tool_call>", font=DEFAULT_FONT, font_size=12.0, color=COLOR_CYAN).move_to(n_native.get_center())

        arr_down4 = ZenArrow(n_native.get_bottom(), n_native.get_bottom() + DOWN * 0.45, color=COLOR_GREEN, stroke_width=1.8)

        math_native = fit_math_to_card(
            r"\text{Payload} \in \mathcal{G}_{\text{JSON}} \implies \text{Error} \to 0\%",
            native_card, font_size=19.0, color=COLOR_GREEN
        ).next_to(arr_down4, DOWN, buff=0.15)

        right_grp = VGroup(native_card, native_header, native_subtitle, n_schema, schema_header, arr_down3, n_native, native_token_header, arr_down4, math_native)
        self.play(FadeIn(right_grp, shift=LEFT * 0.3), run_time=1.1)

        # Dynamic token packet locking into slot
        packet = Dot(point=n_schema.get_center(), radius=0.09, color=COLOR_GREEN)
        self.add(packet)
        self.play(packet.animate.move_to(n_native.get_center()), run_time=1.2)
        self.play(packet.animate.move_to(math_native.get_center()), run_time=1.2)

        # Bottom HUD Metric Box
        hud_box = RoundedRectangle(
            corner_radius=0.12, width=10.6, height=0.68,
            fill_color="#101422", fill_opacity=0.95, stroke_color=COLOR_CYAN, stroke_width=1.2
        ).to_edge(DOWN, buff=0.35)
        hud_header = Text(
            "NATIVE TOOL CALLING // KHÓA CỨNG HỢP ĐỒNG API // TƯƠNG THÍCH DOANH NGHIỆP",
            font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_CYAN
        )
        hud_header.move_to(hud_box.get_center())

        self.play(FadeIn(hud_box, shift=UP * 0.2), FadeIn(hud_header), run_time=0.9)
        self.wait(1.5)


# ==============================================================================
# SCENE 3: MATHEMATICS — GRAMMAR-CONSTRAINED LOGIT MASKING & FSM
# ==============================================================================
class Tap22Scene03Mathematics(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "TOÁN HỌC GRAMMAR MASKING & MÁY TRẠNG THÁI FSM")

        scene_title = Text(
            "TOÁN HỌC GRAMMAR-CONSTRAINED LOGIT MASKING & FSM",
            font=DEFAULT_FONT, font_size=17.0, weight=BOLD, color=COLOR_GOLD
        )
        scene_title.to_edge(UP, buff=0.95)
        self.play(FadeIn(scene_title, shift=DOWN * 0.2), run_time=0.8)

        # Left Container: Formulas Card
        math_card = RoundedRectangle(
            corner_radius=0.15, width=5.6, height=4.5,
            fill_color=COLOR_PANEL, fill_opacity=0.85, stroke_color=COLOR_GOLD, stroke_width=1.5
        ).move_to(LEFT * 3.3 + DOWN * 0.2)

        math_header = Text("CAN THIỆP LOGIT TRƯỚC SOFTMAX", font=DEFAULT_FONT, font_size=13.0, weight=BOLD, color=COLOR_GOLD)
        math_header.next_to(math_card.get_top(), DOWN, buff=0.25)
        math_subtitle = Text("Triệt tiêu xác suất lỗi cú pháp bằng 0", font=DEFAULT_FONT, font_size=12.0, color=COLOR_MUTED)
        math_subtitle.next_to(math_header, DOWN, buff=0.12)

        formula_mask = MathTex(
            r"\tilde{z}_i = \begin{cases} z_i & \text{if } i \in \mathcal{V}_{\text{valid}} \\ -\infty & \text{otherwise} \end{cases}",
            font_size=21.0, color=COLOR_CYAN
        )
        if formula_mask.width > math_card.width * 0.86:
            formula_mask.scale_to_fit_width(math_card.width * 0.86)
        formula_mask.next_to(math_subtitle, DOWN, buff=0.30)

        formula_soft = fit_math_to_card(
            r"P(\text{token}_i) = \frac{\exp(\tilde{z}_i)}{\sum_{j} \exp(\tilde{z}_j)}",
            math_card, font_size=22.0, color=COLOR_GOLD
        ).next_to(formula_mask, DOWN, buff=0.25)

        formula_zero = fit_math_to_card(
            r"P(\text{invalid}) = \frac{\exp(-\infty)}{\sum_{j} \exp(\tilde{z}_j)} = 0.0",
            math_card, font_size=21.0, color=COLOR_GREEN
        ).next_to(formula_soft, DOWN, buff=0.25)

        left_grp = VGroup(math_card, math_header, math_subtitle, formula_mask, formula_soft, formula_zero)
        self.play(FadeIn(left_grp, shift=RIGHT * 0.3), run_time=1.1)

        # Right Container: Finite State Machine (FSM) Graph
        fsm_card = RoundedRectangle(
            corner_radius=0.15, width=5.8, height=4.5,
            fill_color=COLOR_PANEL, fill_opacity=0.85, stroke_color=COLOR_CYAN, stroke_width=1.5
        ).move_to(RIGHT * 3.3 + DOWN * 0.2)

        fsm_header = Text("MÁY TRẠNG THÁI FSM BIÊN DỊCH TỪ SCHEMA", font=DEFAULT_FONT, font_size=12.5, weight=BOLD, color=COLOR_CYAN)
        fsm_header.next_to(fsm_card.get_top(), DOWN, buff=0.25)
        fsm_subtitle = Text("Đồ thị chuyển trạng thái token hợp lệ", font=DEFAULT_FONT, font_size=12.0, color=COLOR_MUTED)
        fsm_subtitle.next_to(fsm_header, DOWN, buff=0.10)

        # 4 FSM Nodes along state path
        s0 = Circle(radius=0.35, color=COLOR_CYAN, fill_opacity=0.3, stroke_width=1.8).move_to(RIGHT * 1.5 + UP * 0.6)
        s0_header = Text("'{'", font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_CYAN).move_to(s0.get_center())

        s1 = Circle(radius=0.35, color=COLOR_GOLD, fill_opacity=0.3, stroke_width=1.8).move_to(RIGHT * 3.3 + UP * 0.6)
        s1_header = Text("\"key\"", font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_GOLD).move_to(s1.get_center())

        s2 = Circle(radius=0.35, color=COLOR_GREEN, fill_opacity=0.3, stroke_width=1.8).move_to(RIGHT * 5.1 + UP * 0.6)
        s2_header = Text("\":\"", font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_GREEN).move_to(s2.get_center())

        s3 = Circle(radius=0.35, color=COLOR_VIOLET, fill_opacity=0.3, stroke_width=1.8).move_to(RIGHT * 3.3 + DOWN * 0.8)
        s3_header = Text("VAL", font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_VIOLET).move_to(s3.get_center())

        arr_01 = ZenArrow(s0.get_right(), s1.get_left(), color=COLOR_CYAN, stroke_width=1.8)
        arr_12 = ZenArrow(s1.get_right(), s2.get_left(), color=COLOR_GOLD, stroke_width=1.8)
        arr_23 = ZenCurvedArrow(s2.get_bottom(), s3.get_right(), color=COLOR_GREEN, stroke_width=1.8, angle=-0.4)
        arr_30 = ZenCurvedArrow(s3.get_left(), s0.get_bottom(), color=COLOR_VIOLET, stroke_width=1.8, angle=-0.4)

        fsm_nodes_grp = VGroup(
            s0, s0_header, s1, s1_header, s2, s2_header, s3, s3_header,
            arr_01, arr_12, arr_23, arr_30
        )

        fsm_status = fit_math_to_card(
            r"\text{Invalid Tokens}: z_i \leftarrow -\infty \implies P(\text{err}) = 0",
            fsm_card, font_size=18.0, color=COLOR_GREEN
        ).next_to(s3, DOWN, buff=0.35)

        right_grp = VGroup(fsm_card, fsm_header, fsm_subtitle, fsm_nodes_grp, fsm_status)
        self.play(FadeIn(right_grp, shift=LEFT * 0.3), run_time=1.1)

        # Dynamic State Transition Token
        state_dot = Dot(point=s0.get_center(), radius=0.09, color=COLOR_CYAN)
        self.add(state_dot)
        self.play(state_dot.animate.move_to(s1.get_center()), run_time=1.0)
        state_dot.set_color(COLOR_GOLD)
        self.play(state_dot.animate.move_to(s2.get_center()), run_time=1.0)
        state_dot.set_color(COLOR_GREEN)
        self.play(MoveAlongPath(state_dot, arr_23), run_time=1.1)
        state_dot.set_color(COLOR_VIOLET)
        self.play(MoveAlongPath(state_dot, arr_30), run_time=1.1)

        # ValueTracker kinetics
        prob_tracker = ValueTracker(1.0)
        self.play(prob_tracker.animate.set_value(0.0), run_time=0.8)

        # Bottom HUD Metric Box
        hud_box = RoundedRectangle(
            corner_radius=0.12, width=10.6, height=0.68,
            fill_color="#101422", fill_opacity=0.95, stroke_color=COLOR_GREEN, stroke_width=1.2
        ).to_edge(DOWN, buff=0.35)
        hud_header = Text(
            "MÁY TRẠNG THÁI HỮU HẠN // BẢO HÀNH TOÁN HỌC 100% CÚ PHÁP HỢP LỆ",
            font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_GREEN
        )
        hud_header.move_to(hud_box.get_center())

        self.play(FadeIn(hud_box, shift=UP * 0.2), FadeIn(hud_header), run_time=0.9)
        self.wait(1.5)


# ==============================================================================
# SCENE 4: TELEMETRY — BENCHMARK ACCURACY & SYNTAX ZERO-ERROR
# ==============================================================================
class Tap22Scene04Telemetry(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "ĐO KIỂM HIỆU NĂNG BERKELEY FUNCTION-CALLING")

        scene_title = Text(
            "ĐO KIỂM TELEMETRY: BERKELEY FUNCTION-CALLING BENCHMARK",
            font=DEFAULT_FONT, font_size=17.0, weight=BOLD, color=COLOR_CYAN
        )
        scene_title.to_edge(UP, buff=0.95)
        self.play(FadeIn(scene_title, shift=DOWN * 0.2), run_time=0.8)

        # 3 Benchmark Columns
        col_w, col_h = 3.6, 4.4
        cols_config = [
            ("PROMPT (REACT)", COLOR_ROSE, LEFT * 3.8, [
                ("Syntax Error", "14.5%"),
                ("Function Acc", "72.0%"),
                ("Argument Acc", "64.2%"),
                ("Production", "RỦI RO CAO"),
            ]),
            ("FINE-TUNED", COLOR_CYAN, ORIGIN, [
                ("Syntax Error", "2.8%"),
                ("Function Acc", "91.4%"),
                ("Argument Acc", "88.6%"),
                ("Production", "RỦI RO THẤP"),
            ]),
            ("GRAMMAR MASKED", COLOR_GREEN, RIGHT * 3.8, [
                ("Syntax Error", "0.0%"),
                ("Function Acc", "98.5%"),
                ("Argument Acc", "97.8%"),
                ("Production", "100% AN TOÀN"),
            ]),
        ]

        col_group = VGroup()
        for head_text, col_color, col_pos, rows in cols_config:
            c_card = RoundedRectangle(
                corner_radius=0.15, width=col_w, height=col_h,
                fill_color=COLOR_PANEL, fill_opacity=0.88, stroke_color=col_color, stroke_width=1.5
            ).move_to(col_pos + DOWN * 0.2)

            c_header = Text(head_text, font=DEFAULT_FONT, font_size=12.5, weight=BOLD, color=col_color)
            c_header.next_to(c_card.get_top(), DOWN, buff=0.22)
            c_div = Line(start=LEFT * 1.4, end=RIGHT * 1.4, color=COLOR_MUTED, stroke_width=1.0).next_to(c_header, DOWN, buff=0.14)

            row_vgroup = VGroup()
            for lbl_str, val_str in rows:
                lbl_obj = Text(lbl_str, font=DEFAULT_FONT, font_size=12.0, color=COLOR_MUTED)
                val_obj = Text(val_str, font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=col_color)
                pair = VGroup(lbl_obj, val_obj).arrange(RIGHT, buff=0.25)
                row_vgroup.add(pair)

            row_vgroup.arrange(DOWN, buff=0.30, aligned_edge=ORIGIN)
            row_vgroup.next_to(c_div, DOWN, buff=0.25)

            col_v = VGroup(c_card, c_header, c_div, row_vgroup)
            col_group.add(col_v)

        self.play(LaggedStart(*[FadeIn(c, shift=UP * 0.3) for c in col_group], lag_ratio=0.2), run_time=1.4)

        # Dynamic comparison tracker bar
        tracker = ValueTracker(14.5)
        self.play(tracker.animate.set_value(0.0), run_time=1.2)

        # Bottom Conclusion Pill
        pill_box = RoundedRectangle(
            corner_radius=0.12, width=10.6, height=0.68,
            fill_color="#101824", fill_opacity=0.95, stroke_color=COLOR_GREEN, stroke_width=1.2
        ).to_edge(DOWN, buff=0.35)
        pill_header = Text(
            "KẾT LUẬN: MASKING FSM ĐƯA TỶ LỆ LỖI CÚ PHÁP VỀ 0% — TIÊU CHUẨN DOANH NGHIỆP",
            font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_GREEN
        )
        pill_header.move_to(pill_box.get_center())

        self.play(FadeIn(pill_box, shift=UP * 0.2), FadeIn(pill_header), run_time=0.8)
        self.wait(1.5)


# ==============================================================================
# SCENE 5: LAB EXPERIMENT — DISPATCHER, DOCKER SANDBOX & HUMAN-IN-THE-LOOP
# ==============================================================================
class Tap22Scene05LabExperiment(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "KIẾN TRÚC DISPATCHER & SANDBOX THỰC TẾ")

        scene_title = Text(
            "KIẾN TRÚC AN TOÀN 3 LỚP: VÒNG LẶP TOOL DISPATCHER",
            font=DEFAULT_FONT, font_size=17.0, weight=BOLD, color=COLOR_GOLD
        )
        scene_title.to_edge(UP, buff=0.95)
        self.play(FadeIn(scene_title, shift=DOWN * 0.2), run_time=0.8)

        # 3 Defense Pillars in Horizontal Flow
        pillar_w, pillar_h = 3.6, 4.4
        pillars_config = [
            ("LỚP 1: SANDBOX", COLOR_CYAN, LEFT * 3.8, [
                ("Cách ly Host OS", COLOR_TEXT),
                ("Chống Injection", COLOR_CYAN),
                ("Giới hạn RAM/CPU", COLOR_TEXT),
                ("Tự hủy Container", COLOR_CYAN),
            ]),
            ("LỚP 2: APPROVAL", COLOR_GOLD, ORIGIN, [
                ("Thao tác Đọc: Auto", COLOR_TEXT),
                ("Ghi/Giao dịch: Khóa", COLOR_GOLD),
                ("Xác thực quản trị", COLOR_TEXT),
                ("Chữ ký số an toàn", COLOR_GOLD),
            ]),
            ("LỚP 3: RESPONSE", COLOR_GREEN, RIGHT * 3.8, [
                ("Đóng gói Tool Msg", COLOR_TEXT),
                ("Tiêm ngược Context", COLOR_GREEN),
                ("Tổng hợp lời giải", COLOR_TEXT),
                ("Hội tụ đa lượt", COLOR_GREEN),
            ]),
        ]

        p_group = VGroup()
        for p_title, p_color, p_pos, p_items in pillars_config:
            p_card = RoundedRectangle(
                corner_radius=0.15, width=pillar_w, height=pillar_h,
                fill_color=COLOR_PANEL, fill_opacity=0.88, stroke_color=p_color, stroke_width=1.5
            ).move_to(p_pos + DOWN * 0.2)

            p_header = Text(p_title, font=DEFAULT_FONT, font_size=12.5, weight=BOLD, color=p_color)
            p_header.next_to(p_card.get_top(), DOWN, buff=0.22)
            p_div = Line(start=LEFT * 1.4, end=RIGHT * 1.4, color=COLOR_MUTED, stroke_width=1.0).next_to(p_header, DOWN, buff=0.14)

            items_vgroup = VGroup()
            for itm_text, itm_color in p_items:
                d = Dot(radius=0.05, color=p_color)
                t = Text(itm_text, font=DEFAULT_FONT, font_size=12.0, color=itm_color)
                row = VGroup(d, t).arrange(RIGHT, buff=0.18)
                items_vgroup.add(row)

            items_vgroup.arrange(DOWN, buff=0.28, aligned_edge=LEFT)
            items_vgroup.next_to(p_div, DOWN, buff=0.25)

            p_v = VGroup(p_card, p_header, p_div, items_vgroup)
            p_group.add(p_v)

        self.play(LaggedStart(*[FadeIn(p, shift=UP * 0.3) for p in p_group], lag_ratio=0.2), run_time=1.4)

        # Closed Loop Connecting Arrows between pillars
        arr_12 = ZenArrow(p_group[0].get_right(), p_group[1].get_left(), color=COLOR_CYAN, stroke_width=2.0)
        arr_23 = ZenArrow(p_group[1].get_right(), p_group[2].get_left(), color=COLOR_GOLD, stroke_width=2.0)
        loop_back = ZenCurvedArrow(p_group[2].get_bottom(), p_group[0].get_bottom(), color=COLOR_GREEN, stroke_width=2.0, angle=-0.35)

        self.play(Create(arr_12), Create(arr_23), Create(loop_back), run_time=1.2)

        # Dynamic loop token circulating
        loop_dot = Dot(point=p_group[0].get_center(), radius=0.08, color=COLOR_CYAN)
        self.add(loop_dot)
        self.play(loop_dot.animate.move_to(p_group[1].get_center()), run_time=1.0)
        loop_dot.set_color(COLOR_GOLD)
        self.play(loop_dot.animate.move_to(p_group[2].get_center()), run_time=1.0)
        loop_dot.set_color(COLOR_GREEN)
        self.play(MoveAlongPath(loop_dot, loop_back), run_time=1.4)

        # Bottom Callout Box
        callout_box = RoundedRectangle(
            corner_radius=0.12, width=10.6, height=0.68,
            fill_color="#181e2b", fill_opacity=0.95, stroke_color=COLOR_CYAN, stroke_width=1.2
        ).to_edge(DOWN, buff=0.35)
        callout_header = Text(
            "CỘNG SỰ THÔNG MINH // TUYỆT ĐỐI NẰM TRONG TẦM KIỂM SOÁT CỦA CON NGƯỜI",
            font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_CYAN
        )
        callout_header.move_to(callout_box.get_center())

        self.play(FadeIn(callout_box, shift=UP * 0.2), FadeIn(callout_header), run_time=0.8)
        self.wait(1.5)


# ==============================================================================
# SCENE 6: OUTRO — HUMANITY, CRAFTSMANSHIP & EPISODE 23 TEASER
# ==============================================================================
class Tap22Scene06Outro(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "BÀN GIAO TRI THỨC VÀ CẦU NỐI KỸ NGHỆ")

        scene_title = Text(
            "BÀN GIAO TRI THỨC // FUNCTION CALLING & TOOL DISPATCHER",
            font=DEFAULT_FONT, font_size=15.0, weight=BOLD, color=COLOR_GOLD
        )
        scene_title.to_edge(UP, buff=0.95)
        self.play(FadeIn(scene_title, shift=DOWN * 0.2), run_time=0.8)

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
        )
        gallery_header.next_to(mosaic_frame, UP, buff=0.18)

        left_grp = Group(mosaic_mobj, mosaic_frame, gallery_header)
        self.play(FadeIn(left_grp, shift=RIGHT * 0.3), run_time=1.2)

        # Right Side: YouTube End Screen Interactive Safe Zones
        # 1. Next Video Card (Episode 23): X in [+1.6, +5.4], Y in [+0.5, +2.5]
        # Clearance to mosaic right edge (-0.30): +1.60 - (-0.30) = 1.90 units = 342px >= 300px!
        next_card = RoundedRectangle(
            corner_radius=0.12, width=3.8, height=2.0,
            fill_color=COLOR_PANEL, fill_opacity=0.7, stroke_color=COLOR_CYAN, stroke_width=1.5
        ).move_to(RIGHT * 3.5 + UP * 1.5)
        next_header = Text("TẬP TIẾP THEO // TẬP 23", font=DEFAULT_FONT, font_size=12.5, weight=BOLD, color=COLOR_CYAN)
        next_sub_header = Text("MULTI-AGENT: KHI CÁC SIÊU AI CỘNG TÁC", font=DEFAULT_FONT, font_size=12.0, color=COLOR_TEXT).next_to(next_header, DOWN, buff=0.18)
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

        # Bottom Bridge Announcement to Episode 23
        bridge_banner = RoundedRectangle(
            corner_radius=0.12, width=10.6, height=0.70,
            fill_color="#181524", fill_opacity=0.95, stroke_color=COLOR_GOLD, stroke_width=1.5
        ).to_edge(DOWN, buff=0.35)
        bridge_header = Text(
            "ĐÓN XEM TẬP 23 // KIẾN TRÚC MULTI-AGENT: KHI CÁC SIÊU AI TRANH LUẬN & CỘNG TÁC",
            font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_GOLD
        )
        bridge_header.move_to(bridge_banner.get_center())

        self.play(FadeIn(bridge_banner, shift=UP * 0.2), FadeIn(bridge_header), run_time=0.9)
        self.wait(2.0)
