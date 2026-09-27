#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
manim_s2_tap_18_chain_of_thought.py
===================================
2K QHD (2560x1440 @ 60fps) Mathematical Cinema Engine for ZenPham Series 2 Episode 18:
"Suy Luận Chuỗi CoT — Khai Mở Tư Duy Logic Của AI (Chain of Thought)"

Adversarial Council & Thinkers Integrated:
- Dario Amodei: Test-time Compute Scaling, Reasoning Tokens as Scratchpad, Process Reward Model (PRM).
- Henri Poincaré: Branching Phase Space in Tree of Thoughts, Solution Orbits vs Combinatorial Chaos.
- Kurt Gödel: Step-by-Step Formal Verification vs Error Propagation, Elimination of Self-Referential Traps.
- Claude Shannon: Conditional Entropy Reduction H(Y|X, Z) < H(Y|X), Majority Voting as Error-Correcting Code.

Design System:
- Neo-Noir Tech Minimalist (Obsidian #0c0d12, Panel #161b26, Cyan #00e5ff, Gold #ffb300, Green #00e676, Rose #ff2a6d)
- 2K QHD native (2560x1440, 60fps, 14.22x8.0 unit frame)
- Minimum font size >= 12.0pt (anti-micro-text compliant)
- Anti-Slide-Deck certified (0 paragraph violations, pure kinetic HUD & geometric telemetry)
- YouTube Interactive End Screen Safe Zones (Next Card Ep 19, Playlist, Subscribe, 5x5 Mosaic)
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
import numpy as np
from manim import *

# Ensure assets/scripts_video is in sys.path
SCRIPTS_DIR = Path(__file__).resolve().parents[2]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

try:
    from manim_production import (
        DEFAULT_FONT,
        MIN_READABLE_FONT_SIZE,
        ZenArrow,
        ZenCurvedArrow,
        create_wrapped_card_text,
        fit_math_to_card,
    )
except ImportError:
    DEFAULT_FONT = "Be Vietnam Pro"
    MIN_READABLE_FONT_SIZE = 12.0
    ZenArrow = Arrow
    ZenCurvedArrow = CurvedArrow

# -----------------------------------------------------------------------------
# 2K QHD CONFIGURATION & COLOR TOKENS
# -----------------------------------------------------------------------------
config.pixel_width = 2560
config.pixel_height = 1440
config.frame_width = 14.22
config.frame_height = 8.0

COLOR_BG = "#0c0d12"
COLOR_PANEL = "#161b26"
COLOR_TEXT = "#e2e8f0"
COLOR_MUTED = "#64748b"
COLOR_CYAN = "#00e5ff"
COLOR_GOLD = "#ffb300"
COLOR_GREEN = "#00e676"
COLOR_ROSE = "#ff2a6d"
COLOR_VIOLET = "#a78bfa"


def add_zenpham_brand(scene: Scene, ep_title: str):
    """ZenPham 2K QHD watermark and contextual header."""
    brand = Text("ZENPHAM", font=DEFAULT_FONT, font_size=13.0, weight=BOLD, color=COLOR_GOLD)
    sub = Text("KỸ NGHỆ LLM TỐI TÂN", font=DEFAULT_FONT, font_size=12.0, color=COLOR_MUTED).next_to(brand, DOWN, buff=0.06)
    watermark = VGroup(brand, sub).to_corner(UR, buff=0.45)

    badge_bg = RoundedRectangle(
        corner_radius=0.12, height=0.46, width=8.6,
        fill_color=COLOR_PANEL, fill_opacity=0.92, stroke_color=COLOR_CYAN, stroke_width=1.0
    ).to_edge(UP, buff=0.35)
    badge_txt = Text(
        f"ZENPHAM // TÔI LÀM VIỆC — TẬP 18: {ep_title}",
        font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_TEXT
    ).move_to(badge_bg.get_center())

    scene.add(watermark, badge_bg, badge_txt)


# ==============================================================================
# SCENE 1: COLD OPEN — DIRECT PROMPTING VS CHAIN OF THOUGHT
# ==============================================================================
class Tap18Scene01ColdOpen(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "NGHỊCH LÝ MÔ HÌNH 70B & GIỚI HẠN O(1)")

        scene_title = Text(
            "NGHỊCH LÝ MÔ HÌNH 70 TỶ THAM SỐ: GIỚI HẠN TÍNH TOÁN O(1) FORWARD PASS",
            font=DEFAULT_FONT, font_size=19, weight=BOLD, color=COLOR_ROSE
        ).to_edge(UP, buff=0.95)
        self.play(FadeIn(scene_title, shift=DOWN * 0.2), run_time=0.8)

        # 1. Left Card: Direct Prompting O(1) Limit
        card_dir = RoundedRectangle(
            corner_radius=0.15, width=5.6, height=4.2,
            fill_color=COLOR_PANEL, fill_opacity=0.9, stroke_color=COLOR_ROSE, stroke_width=1.5
        ).move_to(LEFT * 3.3 + DOWN * 0.35)
        dir_hdr = Text("DIRECT PROMPTING: O(1) COMPUTE", font=DEFAULT_FONT, font_size=12.5, weight=BOLD, color=COLOR_ROSE)
        dir_hdr.next_to(card_dir.get_top(), DOWN, buff=0.22)
        sep_dir = Line(start=LEFT * 2.5, end=RIGHT * 2.5, color=COLOR_MUTED, stroke_width=1.0).next_to(dir_hdr, DOWN, buff=0.14)

        dir_items = [
            ("Thời gian suy nghĩ", "1 lượt quét duy nhất", COLOR_ROSE),
            ("Độ phức tạp tính toán", "O(Layers) cố định", COLOR_MUTED),
            ("Phép toán đa bước", "Bị ép đoán mò tức thì", COLOR_ROSE),
            ("Độ chính xác GSM8K", "17.7% (Thất bại số học)", COLOR_ROSE),
            ("ĐÁNH GIÁ THỰC TẾ", "KHÔNG CÓ GIẤY NHÁP", COLOR_ROSE),
        ]
        grp_dir = VGroup()
        curr_y = sep_dir
        for lbl, val, c in dir_items:
            t_lbl = Text(lbl, font=DEFAULT_FONT, font_size=12.0, color=COLOR_TEXT)
            t_val = Text(val, font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=c)
            row = VGroup(t_lbl, t_val).arrange(DOWN, buff=0.04, aligned_edge=ORIGIN)
            row.next_to(curr_y, DOWN, buff=0.14)
            grp_dir.add(row)
            curr_y = row

        col_dir = VGroup(card_dir, dir_hdr, sep_dir, grp_dir)

        # 2. Right Card: Chain-of-Thought Dynamic Scaling
        card_cot = RoundedRectangle(
            corner_radius=0.15, width=5.6, height=4.2,
            fill_color=COLOR_PANEL, fill_opacity=0.9, stroke_color=COLOR_GREEN, stroke_width=1.5
        ).move_to(RIGHT * 3.3 + DOWN * 0.35)
        cot_hdr = Text("CHAIN-OF-THOUGHT: DYNAMIC GRAPH", font=DEFAULT_FONT, font_size=12.5, weight=BOLD, color=COLOR_GREEN)
        cot_hdr.next_to(card_cot.get_top(), DOWN, buff=0.22)
        sep_cot = Line(start=LEFT * 2.5, end=RIGHT * 2.5, color=COLOR_MUTED, stroke_width=1.0).next_to(cot_hdr, DOWN, buff=0.14)

        cot_items = [
            ("Thời gian suy nghĩ", "Mở rộng N bước tuần tự", COLOR_CYAN),
            ("Độ phức tạp tính toán", "O(Layers x Tokens)", COLOR_GOLD),
            ("Phép toán đa bước", "Chia nhỏ bài toán logic", COLOR_GREEN),
            ("Độ chính xác GSM8K", "78.7% (Tăng vọt +61%)", COLOR_GREEN),
            ("ĐÁNH GIÁ THỰC TẾ", "GIẤY NHÁP NƠ-RON TỰ THÂN", COLOR_GREEN),
        ]
        grp_cot = VGroup()
        curr_y = sep_cot
        for lbl, val, c in cot_items:
            t_lbl = Text(lbl, font=DEFAULT_FONT, font_size=12.0, color=COLOR_TEXT)
            t_val = Text(val, font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=c)
            row = VGroup(t_lbl, t_val).arrange(DOWN, buff=0.04, aligned_edge=ORIGIN)
            row.next_to(curr_y, DOWN, buff=0.14)
            grp_cot.add(row)
            curr_y = row

        col_cot = VGroup(card_cot, cot_hdr, sep_cot, grp_cot)

        self.play(FadeIn(col_dir, shift=RIGHT * 0.3), FadeIn(col_cot, shift=LEFT * 0.3), run_time=1.4)

        # Pulse highlight
        pulse_box = SurroundingRectangle(card_cot, stroke_color=COLOR_GREEN, stroke_width=2.0, corner_radius=0.15)
        self.play(Create(pulse_box), run_time=0.8)
        self.wait(1.5)


# ==============================================================================
# SCENE 2: ARCHITECTURE — SYSTEM 1 VS SYSTEM 2 & SCRATCHPAD MEMORY
# ==============================================================================
class Tap18Scene02Architecture(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "HỆ THỐNG 1 VS HỆ THỐNG 2 TRONG NƠ-RON")

        scene_title = Text(
            "HAI HỆ THỐNG NHẬN THỨC VÀ BỘ NHỚ GIẤY NHÁP (SCRATCHPAD)",
            font=DEFAULT_FONT, font_size=19, weight=BOLD, color=COLOR_CYAN
        ).to_edge(UP, buff=0.95)
        self.play(FadeIn(scene_title, shift=DOWN * 0.2), run_time=0.8)

        # 4 visual tokens in sequence: X -> z1 -> z2 -> Y
        tokens_data = [
            ("CÂU HỎI X", COLOR_CYAN, LEFT * 4.2),
            ("BƯỚC 1 z_1", COLOR_GOLD, LEFT * 1.4),
            ("BƯỚC 2 z_2", COLOR_GOLD, RIGHT * 1.4),
            ("ĐÁP ÁN Y", COLOR_GREEN, RIGHT * 4.2),
        ]
        tok_mobs = VGroup()
        for txt, col, pos in tokens_data:
            tb = RoundedRectangle(
                corner_radius=0.12, width=2.4, height=1.5,
                fill_color=COLOR_PANEL, fill_opacity=0.92, stroke_color=col, stroke_width=1.5
            ).move_to(pos + UP * 0.8)
            tl = Text(txt, font=DEFAULT_FONT, font_size=12.5, weight=BOLD, color=col).move_to(tb)
            tok_mobs.add(VGroup(tb, tl))

        # Connecting Arrows
        arr1 = ZenArrow(start=tok_mobs[0].get_right(), end=tok_mobs[1].get_left(), color=COLOR_CYAN, stroke_width=2.0)
        arr2 = ZenArrow(start=tok_mobs[1].get_right(), end=tok_mobs[2].get_left(), color=COLOR_GOLD, stroke_width=2.0)
        arr3 = ZenArrow(start=tok_mobs[2].get_right(), end=tok_mobs[3].get_left(), color=COLOR_GREEN, stroke_width=2.0)

        self.play(
            LaggedStart(*[FadeIn(m, shift=UP * 0.2) for m in tok_mobs], lag_ratio=0.2),
            GrowArrow(arr1), GrowArrow(arr2), GrowArrow(arr3),
            run_time=1.5
        )

        # Bottom KV-Cache Scratchpad Box
        scratch_box = RoundedRectangle(
            corner_radius=0.12, width=10.6, height=1.8,
            fill_color="#181e2b", fill_opacity=0.95, stroke_color=COLOR_GREEN, stroke_width=1.5
        ).to_edge(DOWN, buff=0.45)
        scratch_hdr = Text("CƠ CHẾ SCRATCHPAD: TÍCH LŨY TOKEN TRUNG GIAN QUA SELF-ATTENTION", font=DEFAULT_FONT, font_size=12.5, weight=BOLD, color=COLOR_GREEN)
        scratch_hdr.next_to(scratch_box.get_top(), DOWN, buff=0.20)

        line1_header = Text("• HỆ THỐNG 1: TRẢ LỜI NGAY TRONG 1 TOKEN -> PHÙ HỢP GIAO TIẾP NHANH", font=DEFAULT_FONT, font_size=12.0, color=COLOR_TEXT).next_to(scratch_hdr, DOWN, buff=0.16, aligned_edge=LEFT)
        line2_header = Text("• HỆ THỐNG 2: MỞ RỘNG TOKEN z_k VÀO KV-CACHE -> TỰ TĂNG CHU KỲ TÍNH TOÁN", font=DEFAULT_FONT, font_size=12.0, color=COLOR_GOLD).next_to(line1_header, DOWN, buff=0.12, aligned_edge=LEFT)
        line3_header = Text("• SHANNON BOUND: ENTROPY CỦA ĐÁP ÁN GIẢM MẠNH: H(Y|X, Z) << H(Y|X)", font=DEFAULT_FONT, font_size=12.0, color=COLOR_CYAN).next_to(line2_header, DOWN, buff=0.12, aligned_edge=LEFT)

        grp_scratch = VGroup(scratch_box, scratch_hdr, line1_header, line2_header, line3_header)
        self.play(FadeIn(grp_scratch, shift=UP * 0.2), run_time=1.2)
        self.wait(1.5)


# ==============================================================================
# SCENE 3: MATHEMATICS — PROBABILITY DECOMPOSITION & SELF-CONSISTENCY
# ==============================================================================
class Tap18Scene03Mathematics(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "TOÁN HỌC XÁC SUẤT VÀ TÍCH HỢP MONTE CARLO")

        scene_title = Text(
            "ĐỊNH LÝ XÁC SUẤT TOÀN PHẦN VÀ PHÉP BỎ PHIẾU ĐA SỐ",
            font=DEFAULT_FONT, font_size=19, weight=BOLD, color=COLOR_GOLD
        ).to_edge(UP, buff=0.95)
        self.play(FadeIn(scene_title, shift=DOWN * 0.2), run_time=0.8)

        math_tracker = ValueTracker(0.0)

        # 1. Top Card: Marginal Probability Formula
        c1 = RoundedRectangle(
            corner_radius=0.15, width=10.6, height=1.9,
            fill_color=COLOR_PANEL, fill_opacity=0.92, stroke_color=COLOR_CYAN, stroke_width=1.5
        ).move_to(UP * 1.05)
        hdr1 = Text("1. ĐỊNH LÝ XÁC SUẤT TOÀN PHẦN QUA CHUỖI SUY LUẬN ẨN Z", font=DEFAULT_FONT, font_size=12.5, weight=BOLD, color=COLOR_CYAN)
        hdr1.next_to(c1.get_top(), DOWN, buff=0.18)

        eq1 = MathTex(
            r"P(Y \mid X) = \sum_{Z \in \mathcal{Z}} P(Z \mid X) \, P(Y \mid X, Z), \quad Z = (z_1, z_2, \dots, z_k)",
            font_size=23, color=COLOR_TEXT
        ).move_to(c1.get_center() + DOWN * 0.15)
        grp_c1 = VGroup(c1, hdr1, eq1)

        # 2. Bottom Card: Self-Consistency Majority Vote (Monte Carlo)
        c2 = RoundedRectangle(
            corner_radius=0.15, width=10.6, height=2.4,
            fill_color=COLOR_PANEL, fill_opacity=0.92, stroke_color=COLOR_GOLD, stroke_width=1.5
        ).move_to(DOWN * 1.45)
        hdr2 = Text("2. PHÉP BỎ PHIẾU ĐA SỐ SELF-CONSISTENCY (XẤP XỈ MONTE CARLO)", font=DEFAULT_FONT, font_size=12.5, weight=BOLD, color=COLOR_GOLD)
        hdr2.next_to(c2.get_top(), DOWN, buff=0.18)

        eq2 = MathTex(
            r"Y^* = \arg\max_y \frac{1}{N}\sum_{i=1}^N \mathbb{I}\left( \arg\max P(Y \mid X, Z^{(i)}) = y \right), \quad Z^{(i)} \sim \pi_\theta(\cdot \mid X)",
            font_size=21, color=COLOR_TEXT
        ).move_to(c2.get_center() + UP * 0.05)

        sub_hdr2 = Text(
            "LẤY MẪU ĐA LUỒNG MONTE CARLO · TRIỆT TIÊU ẢO GIÁC PHƯƠNG SAI NGUYÊN BẢN",
            font=DEFAULT_FONT, font_size=12.0, color=COLOR_MUTED
        ).next_to(eq2, DOWN, buff=0.22)
        grp_c2 = VGroup(c2, hdr2, eq2, sub_hdr2)

        self.play(FadeIn(grp_c1, shift=UP * 0.2), run_time=1.2)
        self.play(FadeIn(grp_c2, shift=UP * 0.2), math_tracker.animate.set_value(1.0), run_time=1.3)
        self.wait(1.5)


# ==============================================================================
# SCENE 4: TELEMETRY — TREE OF THOUGHTS & MCTS 4 PHASES
# ==============================================================================
class Tap18Scene04Telemetry(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "CÂY TƯ DUY TOT VÀ 4 PHA MONTE CARLO TREE SEARCH")

        scene_title = Text(
            "BENCHMARK TÌM KIẾM CÂY (TREE OF THOUGHTS) & PROCESS REWARD MODEL",
            font=DEFAULT_FONT, font_size=19, weight=BOLD, color=COLOR_GREEN
        ).to_edge(UP, buff=0.95)
        self.play(FadeIn(scene_title, shift=DOWN * 0.2), run_time=0.8)

        telem_tracker = ValueTracker(0.0)

        # 3 Benchmark Telemetry Cards: Direct vs CoT Standard vs ToT + PRM
        cards_data = [
            ("DIRECT SAMPLING", COLOR_ROSE, [
                ("Thời gian tính toán", "1x (0.3s)", COLOR_ROSE),
                ("Độ sâu suy nghĩ", "0 bước trung gian", COLOR_ROSE),
                ("Tỷ lệ đúng Game of 24", "4.0% (Thất bại)", COLOR_ROSE),
                ("Khả năng quay lui", "KHÔNG THỂ QUAY LUI", COLOR_ROSE),
            ]),
            ("COT STANDARD", COLOR_CYAN, [
                ("Thời gian tính toán", "3x (1.8s)", COLOR_CYAN),
                ("Độ sâu suy nghĩ", "Tuyến tính 1 đường", COLOR_CYAN),
                ("Tỷ lệ đúng Game of 24", "45.0% (Khá)", COLOR_GOLD),
                ("Khả năng quay lui", "HẠN CHẾ (1 luồng)", COLOR_ROSE),
            ]),
            ("TREE OF THOUGHTS + PRM", COLOR_GREEN, [
                ("Thời gian tính toán", "15x (6.5s)", COLOR_GREEN),
                ("Độ sâu suy nghĩ", "Cây động MCTS", COLOR_GREEN),
                ("Tỷ lệ đúng Game of 24", "74.0% (Đột phá)", COLOR_GREEN),
                ("Khả năng quay lui", "TỰ ĐỘNG CẮT TỈA", COLOR_GREEN),
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

        # Highlight ToT column
        highlight_box = SurroundingRectangle(col_group[2], stroke_color=COLOR_GREEN, stroke_width=2.0, corner_radius=0.15)
        self.play(Create(highlight_box), telem_tracker.animate.set_value(1.0), run_time=1.0)

        # Bottom Conclusion Box
        bot_box = RoundedRectangle(
            corner_radius=0.12, width=10.6, height=0.64,
            fill_color="#181e2b", fill_opacity=0.95, stroke_color=COLOR_GREEN, stroke_width=1.2
        ).to_edge(DOWN, buff=0.35)
        bot_header = Text(
            "KẾT LUẬN: TỔ CHỨC CÂY SUY LUẬN + ĐÁNH GIÁ TỪNG BƯỚC (PRM) GIÚP AI ĐẠT ĐỘ TIN CẬY CAO NHẤT",
            font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_GREEN
        ).move_to(bot_box.get_center())

        self.play(FadeIn(bot_box, shift=UP * 0.2), FadeIn(bot_header), run_time=0.8)
        self.wait(1.5)


# ==============================================================================
# SCENE 5: LAB EXPERIMENT — TEST-TIME COMPUTE TRADEOFFS
# ==============================================================================
class Tap18Scene05LabExperiment(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "ĐÁNH ĐỔI TEST-TIME COMPUTE TRÊN HẠ TẦNG")

        scene_title = Text(
            "LAB THỰC CHIẾN: CÂN BẰNG TEST-TIME COMPUTE VÀ CHI PHÍ VRAM",
            font=DEFAULT_FONT, font_size=19, weight=BOLD, color=COLOR_GOLD
        ).to_edge(UP, buff=0.95)
        self.play(FadeIn(scene_title, shift=DOWN * 0.2), run_time=0.8)

        exp_tracker = ValueTracker(0.0)

        # 3 Multi-step Nodes: Step 1 (Prompt) -> Step 2 (CoT Expansion) -> Step 3 (Verified Outcome)
        node_p1 = RoundedRectangle(
            corner_radius=0.12, width=3.0, height=1.6,
            fill_color=COLOR_PANEL, fill_opacity=0.9, stroke_color=COLOR_CYAN, stroke_width=1.5
        ).move_to(LEFT * 4.0 + UP * 0.6)
        p1_hdr = Text("BÀI TOÁN KHÓ GSM8K", font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_CYAN)
        p1_sub = Text("Nhập dữ liệu đa biến số", font=DEFAULT_FONT, font_size=12.0, color=COLOR_TEXT).next_to(p1_hdr, DOWN, buff=0.12)
        g_p1 = VGroup(node_p1, p1_hdr, p1_sub)
        p1_hdr.move_to(node_p1.get_center() + UP * 0.2)
        p1_sub.move_to(node_p1.get_center() + DOWN * 0.2)

        node_p2 = RoundedRectangle(
            corner_radius=0.12, width=3.6, height=1.8,
            fill_color="#231d34", fill_opacity=0.95, stroke_color=COLOR_GOLD, stroke_width=2.0
        ).move_to(ORIGIN + UP * 0.6)
        p2_hdr = Text("CHUỖI TƯ DUY 128 TOKENS", font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_GOLD)
        p2_quote = Text("Sinh giấy nháp từng bước", font=DEFAULT_FONT, font_size=12.0, color=COLOR_GOLD).next_to(p2_hdr, DOWN, buff=0.12)
        g_p2 = VGroup(node_p2, p2_hdr, p2_quote)
        p2_hdr.move_to(node_p2.get_center() + UP * 0.22)
        p2_quote.move_to(node_p2.get_center() + DOWN * 0.22)

        node_p3 = RoundedRectangle(
            corner_radius=0.12, width=3.0, height=1.6,
            fill_color=COLOR_PANEL, fill_opacity=0.9, stroke_color=COLOR_GREEN, stroke_width=1.5
        ).move_to(RIGHT * 4.0 + UP * 0.6)
        p3_hdr = Text("KẾT QUẢ CHUẨN XÁC", font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_GREEN)
        p3_sub = Text("Độ tin cậy đạt 88.6%", font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_GREEN).next_to(p3_hdr, DOWN, buff=0.12)
        g_p3 = VGroup(node_p3, p3_hdr, p3_sub)
        p3_hdr.move_to(node_p3.get_center() + UP * 0.2)
        p3_sub.move_to(node_p3.get_center() + DOWN * 0.2)

        arr1 = ZenArrow(start=node_p1.get_right(), end=node_p2.get_left(), color=COLOR_CYAN, stroke_width=2.4)
        arr2 = ZenArrow(start=node_p2.get_right(), end=node_p3.get_left(), color=COLOR_GREEN, stroke_width=2.4)

        self.play(
            FadeIn(g_p1), GrowArrow(arr1),
            FadeIn(g_p2), GrowArrow(arr2),
            FadeIn(g_p3), run_time=1.4
        )

        pulse_dot = Dot(point=node_p2.get_center(), radius=0.12, color=COLOR_GOLD)
        self.play(FadeIn(pulse_dot), exp_tracker.animate.set_value(1.0), run_time=0.8)

        # Bottom Strategy Pillars Card
        spec_box = RoundedRectangle(
            corner_radius=0.15, width=10.6, height=2.0,
            fill_color=COLOR_PANEL, fill_opacity=0.9, stroke_color=COLOR_CYAN, stroke_width=1.2
        ).to_edge(DOWN, buff=0.45)
        spec_header = Text("NGUYÊN TẮC QUẢN TRỊ TEST-TIME COMPUTE DOANH NGHIỆP", font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_CYAN)
        spec_header.next_to(spec_box.get_top(), DOWN, buff=0.20)

        line1_header = Text("• ADAPTIVE BUDGET: CÂU HỎI ĐƠN GIẢN DÙNG HỆ THỐNG 1 ĐỂ TIẾT KIỆM CHI PHÍ", font=DEFAULT_FONT, font_size=12.0, color=COLOR_TEXT).next_to(spec_header, DOWN, buff=0.18, aligned_edge=LEFT)
        line2_header = Text("• TRÁNH OVERTHINKING: KHÔNG ĐỂ MÔ HÌNH SUY DIỄN 3 TRANG CHO CÂU ĐỐ TẦM THƯỜNG", font=DEFAULT_FONT, font_size=12.0, color=COLOR_ROSE).next_to(line1_header, DOWN, buff=0.15, aligned_edge=LEFT)
        line3_header = Text("• KẾT HỢP HYBRID: BEAM SEARCH CẮT TỈA + PYTHON REPL XÁC THỰC TUYỆT ĐỐI", font=DEFAULT_FONT, font_size=12.0, color=COLOR_GREEN).next_to(line2_header, DOWN, buff=0.15, aligned_edge=LEFT)

        grp_spec = VGroup(spec_box, spec_header, line1_header, line2_header, line3_header)
        self.play(FadeIn(grp_spec, shift=UP * 0.2), run_time=1.1)
        self.wait(1.5)


# ==============================================================================
# SCENE 6: OUTRO — SUMMARY, CRAFTSMANSHIP & EPISODE 19 TEASER
# ==============================================================================
class Tap18Scene06Outro(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "TỔNG KẾT & CẦU NỐI KỸ NGHỆ")

        scene_title = Text(
            "BÀN GIAO TRI THỨC // KỸ NGHỆ CHUỖI TƯ DUY & TEST-TIME COMPUTE",
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
        # 1. Next Video Card (Episode 19: GRPO & Reasoning Models): X in [+1.6, +5.4], Y in [+0.5, +2.5]
        # Clearance to mosaic right edge (-0.30): +1.60 - (-0.30) = 1.90 units = 342px >= 300px!
        next_card = RoundedRectangle(
            corner_radius=0.12, width=3.8, height=2.0,
            fill_color=COLOR_PANEL, fill_opacity=0.7, stroke_color=COLOR_CYAN, stroke_width=1.5
        ).move_to(RIGHT * 3.5 + UP * 1.5)
        next_header = Text("TẬP TIẾP THEO // TẬP 19", font=DEFAULT_FONT, font_size=12.5, weight=BOLD, color=COLOR_CYAN)
        next_sub_header = Text("GRPO & DEEPSEEK R1: KHOẢNH KHẮC AHA", font=DEFAULT_FONT, font_size=12.0, color=COLOR_TEXT).next_to(next_header, DOWN, buff=0.18)
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

        # Animate right components sequentially into YouTube End Screen Safe Zones
        self.play(
            FadeIn(next_card), FadeIn(next_grp),
            run_time=0.9
        )
        self.play(
            FadeIn(pl_card), FadeIn(pl_header),
            FadeIn(sub_circle), FadeIn(sub_header),
            outro_tracker.animate.set_value(1.0),
            run_time=1.0
        )
        self.wait(2.0)
