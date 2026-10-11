#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
manim_s2_tap_19_grpo.py
=======================
2K QHD (2560x1440 @ 60fps) Mathematical Cinema Engine for ZenPham Series 2 Episode 19:
"Giải Thuật GRPO & Reasoning Models — Huấn Luyện AI Biết Tự Suy Nghĩ (DeepSeek-R1)"

Adversarial Council & Thinkers Integrated:
- Dario Amodei: Reasoning Tokens vs Hidden States, Test-time Compute Scaling, Zero-Critic RL.
- Henri Poincaré: Dynamical Phase Space of Reasoning Trajectories, Saddle-node Bifurcation of "Aha Moment".
- Kurt Gödel: Rule-based External Verification (Tarski Oracle) vs Self-Referential Hallucination.
- Claude Shannon: Policy Information Entropy, Group Advantage Whitening Filter, KL Divergence Regularization.

Design System:
- Neo-Noir Tech Minimalist (Obsidian #0c0d12, Panel #161b26, Cyan #00e5ff, Gold #ffb300, Green #00e676, Rose #ff2a6d)
- 2K QHD native (2560x1440, 60fps, 14.22x8.0 unit frame)
- Minimum font size >= 12.0pt (anti-micro-text compliant)
- Anti-Slide-Deck certified (0 paragraph violations, pure kinetic HUD & geometric telemetry)
- YouTube Interactive End Screen Safe Zones (Next Card Ep 20, Playlist, Subscribe, 5x5 Mosaic)
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
# SCENE 1: COLD OPEN — THE PPO BOTTLENECK & CRITIC ELIMINATION
# ==============================================================================
class Tap19Scene01ColdOpen(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "NGHỊCH LÝ PPO VÀ GÁNH NẶNG MẠNG CRITIC")

        scene_title = Text(
            "NGHỊCH LÝ HỌC TĂNG CƯỜNG (PPO): KHỦNG HOẢNG BỘ NHỚ CRITIC 70B",
            font=DEFAULT_FONT, font_size=19, weight=BOLD, color=COLOR_ROSE
        ).to_edge(UP, buff=0.95)
        self.play(FadeIn(scene_title, shift=DOWN * 0.2), run_time=0.8)

        # 1. Left Card: PPO Architecture Overhead
        card_ppo = RoundedRectangle(
            corner_radius=0.15, width=5.6, height=4.2,
            fill_color=COLOR_PANEL, fill_opacity=0.9, stroke_color=COLOR_ROSE, stroke_width=1.5
        ).move_to(LEFT * 3.3 + DOWN * 0.35)
        ppo_hdr = Text("KIẾN TRÚC PPO: 4 MẠNG NƠ-RON", font=DEFAULT_FONT, font_size=12.5, weight=BOLD, color=COLOR_ROSE)
        ppo_hdr.next_to(card_ppo.get_top(), DOWN, buff=0.22)
        sep_ppo = Line(start=LEFT * 2.5, end=RIGHT * 2.5, color=COLOR_MUTED, stroke_width=1.0).next_to(ppo_hdr, DOWN, buff=0.14)

        ppo_items = [
            ("1. Policy / Actor Model (70B)", "Chiếm 80 GB VRAM", COLOR_CYAN),
            ("2. Reference Model (70B Đóng băng)", "Chiếm 80 GB VRAM", COLOR_MUTED),
            ("3. Reward Model (Chấm điểm)", "Chiếm 40 GB VRAM", COLOR_GOLD),
            ("4. Critic / Value Network (70B)", "Chiếm 80 GB VRAM", COLOR_ROSE),
            ("TỔNG TIÊU TỐN VRAM", "280 GB GPU MEMORY", COLOR_ROSE),
        ]
        grp_ppo = VGroup()
        curr_y = sep_ppo
        for lbl, val, c in ppo_items:
            t_lbl = Text(lbl, font=DEFAULT_FONT, font_size=12.0, color=COLOR_TEXT)
            t_val = Text(val, font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=c)
            row = VGroup(t_lbl, t_val).arrange(DOWN, buff=0.04, aligned_edge=ORIGIN)
            row.next_to(curr_y, DOWN, buff=0.14)
            grp_ppo.add(row)
            curr_y = row

        col_ppo = VGroup(card_ppo, ppo_hdr, sep_ppo, grp_ppo)

        # 2. Right Card: GRPO Paradigm Shift
        card_grpo = RoundedRectangle(
            corner_radius=0.15, width=5.6, height=4.2,
            fill_color=COLOR_PANEL, fill_opacity=0.9, stroke_color=COLOR_GREEN, stroke_width=1.5
        ).move_to(RIGHT * 3.3 + DOWN * 0.35)
        grpo_hdr = Text("ĐỘT PHÁ GRPO: XÓA SỔ CRITIC", font=DEFAULT_FONT, font_size=12.5, weight=BOLD, color=COLOR_GREEN)
        grpo_hdr.next_to(card_grpo.get_top(), DOWN, buff=0.22)
        sep_grpo = Line(start=LEFT * 2.5, end=RIGHT * 2.5, color=COLOR_MUTED, stroke_width=1.0).next_to(grpo_hdr, DOWN, buff=0.14)

        grpo_items = [
            ("1. Policy / Actor Model (70B)", "Tập trung suy luận", COLOR_CYAN),
            ("2. Reference Model (70B Tham chiếu)", "Neo ngữ nghĩa", COLOR_MUTED),
            ("3. Zero Critic Network", "Tiết kiệm 100% Critic", COLOR_GREEN),
            ("4. Group Baseline Evaluation", "So sánh nội bộ nhóm", COLOR_GOLD),
            ("TỔNG TIÊU TỐN VRAM", "140 GB (GIẢM 50%)", COLOR_GREEN),
        ]
        grp_grpo = VGroup()
        curr_y = sep_grpo
        for lbl, val, c in grpo_items:
            t_lbl = Text(lbl, font=DEFAULT_FONT, font_size=12.0, color=COLOR_TEXT)
            t_val = Text(val, font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=c)
            row = VGroup(t_lbl, t_val).arrange(DOWN, buff=0.04, aligned_edge=ORIGIN)
            row.next_to(curr_y, DOWN, buff=0.14)
            grp_grpo.add(row)
            curr_y = row

        col_grpo = VGroup(card_grpo, grpo_hdr, sep_grpo, grp_grpo)

        self.play(FadeIn(col_ppo, shift=RIGHT * 0.3), FadeIn(col_grpo, shift=LEFT * 0.3), run_time=1.4)

        # Pulse comparison
        pulse_box = SurroundingRectangle(card_grpo, stroke_color=COLOR_GREEN, stroke_width=2.0, corner_radius=0.15)
        self.play(Create(pulse_box), run_time=0.8)
        self.wait(1.5)


# ==============================================================================
# SCENE 2: ARCHITECTURE — GROUP RELATIVE ROLLOUT IN POINCARÉ PHASE SPACE
# ==============================================================================
class Tap19Scene02Architecture(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "ĐẤU TRƯỜNG SUY LUẬN NHÓM VÀ KHÔNG GIAN PHA")

        scene_title = Text(
            "GROUP SAMPLING: ĐẤU TRƯỜNG SUY LUẬN ĐA TUYẾN SONG SONG",
            font=DEFAULT_FONT, font_size=19, weight=BOLD, color=COLOR_CYAN
        ).to_edge(UP, buff=0.95)
        self.play(FadeIn(scene_title, shift=DOWN * 0.2), run_time=0.8)

        # Left Query Node
        q_box = RoundedRectangle(
            corner_radius=0.12, width=2.8, height=1.6,
            fill_color=COLOR_PANEL, fill_opacity=0.95, stroke_color=COLOR_CYAN, stroke_width=1.5
        ).move_to(LEFT * 4.4 + UP * 0.2)
        q_hdr = Text("CÂU HỎI q", font=DEFAULT_FONT, font_size=12.5, weight=BOLD, color=COLOR_CYAN)
        q_sub = Text("ĐỀ BÀI TOÁN HỌC", font=DEFAULT_FONT, font_size=12.0, color=COLOR_TEXT).next_to(q_hdr, DOWN, buff=0.12)
        grp_q = VGroup(q_box, q_hdr, q_sub)
        q_hdr.move_to(q_box.get_center() + UP * 0.2)
        q_sub.move_to(q_box.get_center() + DOWN * 0.2)

        self.play(FadeIn(grp_q, shift=RIGHT * 0.3), run_time=0.8)

        # 4 Parallel Rollout Trajectories (representing G=8)
        rollouts = [
            ("Luồng 1 (Đại số)", "r_1 = 1.0 (ĐÚNG)", COLOR_GREEN),
            ("Luồng 2 (Hình học)", "r_2 = 1.0 (ĐÚNG)", COLOR_GREEN),
            ("Luồng 3 (Tự sửa sai)", "r_3 = 1.0 (ĐÚNG)", COLOR_GOLD),
            ("Luồng 4 (Tính cẩu thả)", "r_4 = 0.0 (SAI)", COLOR_ROSE),
        ]
        grp_branches = VGroup()
        grp_arrows = VGroup()

        for idx, (name, score, col) in enumerate(rollouts):
            y_coord = 1.6 - idx * 0.95
            r_box = RoundedRectangle(
                corner_radius=0.10, width=4.6, height=0.72,
                fill_color=COLOR_PANEL, fill_opacity=0.92, stroke_color=col, stroke_width=1.2
            ).move_to(RIGHT * 1.5 + UP * y_coord)
            r_name = Text(name, font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=col)
            r_score = Text(score, font=DEFAULT_FONT, font_size=12.0, color=COLOR_TEXT).next_to(r_name, RIGHT, buff=0.25)
            r_line = VGroup(r_name, r_score).move_to(r_box.get_center())

            arr = ZenArrow(start=q_box.get_right(), end=r_box.get_left(), color=col, stroke_width=1.8)
            grp_arrows.add(arr)
            grp_branches.add(VGroup(r_box, r_line))

        self.play(
            LaggedStart(*[GrowArrow(a) for a in grp_arrows], lag_ratio=0.15),
            LaggedStart(*[FadeIn(b, shift=LEFT * 0.2) for b in grp_branches], lag_ratio=0.15),
            run_time=1.5
        )

        # Bottom Baseline Box
        base_box = RoundedRectangle(
            corner_radius=0.12, width=10.6, height=0.9,
            fill_color="#181e2b", fill_opacity=0.95, stroke_color=COLOR_GOLD, stroke_width=1.5
        ).to_edge(DOWN, buff=0.45)
        base_hdr = Text("BASELINE TỰ THÂN: TRUNG BÌNH CỘNG CỦA NHÓM G", font=DEFAULT_FONT, font_size=12.5, weight=BOLD, color=COLOR_GOLD)
        base_sub_hdr = Text("MỨC KỲ VỌNG = MEAN(R_1..R_G) · LỢI THẾ A_i = (R_i - MEAN) / STD", font=DEFAULT_FONT, font_size=12.0, color=COLOR_TEXT)
        grp_base = VGroup(base_hdr, base_sub_hdr).arrange(DOWN, buff=0.08).move_to(base_box.get_center())

        self.play(FadeIn(base_box, shift=UP * 0.2), FadeIn(grp_base), run_time=1.0)
        self.wait(1.5)


# ==============================================================================
# SCENE 3: MATHEMATICS — GROUP ADVANTAGE & CLIPPED OBJECTIVE
# ==============================================================================
class Tap19Scene03Mathematics(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "GIẢI PHẪU TOÁN HỌC CÔNG THỨC GRPO")

        scene_title = Text(
            "CÔNG THỨC TOÁN HỌC: GROUP ADVANTAGE VÀ LOSS CLIPPED",
            font=DEFAULT_FONT, font_size=19, weight=BOLD, color=COLOR_GOLD
        ).to_edge(UP, buff=0.95)
        self.play(FadeIn(scene_title, shift=DOWN * 0.2), run_time=0.8)

        math_tracker = ValueTracker(0.0)

        # 1. Top Card: Group Relative Advantage (Z-Score)
        c1 = RoundedRectangle(
            corner_radius=0.15, width=10.6, height=1.9,
            fill_color=COLOR_PANEL, fill_opacity=0.92, stroke_color=COLOR_CYAN, stroke_width=1.5
        ).move_to(UP * 1.05)
        hdr1 = Text("1. CHUẨN HÓA LỢI THẾ Z-SCORE THEO NHÓM (GROUP ADVANTAGE)", font=DEFAULT_FONT, font_size=12.5, weight=BOLD, color=COLOR_CYAN)
        hdr1.next_to(c1.get_top(), DOWN, buff=0.18)

        eq1 = MathTex(
            r"\hat{A}_i = \frac{r_i - \bar{r}}{\sigma_r + \epsilon}, \quad \bar{r} = \frac{1}{G}\sum_{j=1}^G r_j, \quad \sigma_r = \sqrt{\frac{1}{G}\sum_{j=1}^G (r_j - \bar{r})^2}",
            font_size=23, color=COLOR_TEXT
        ).move_to(c1.get_center() + DOWN * 0.15)
        grp_c1 = VGroup(c1, hdr1, eq1)

        # 2. Bottom Card: GRPO Clipped Objective with KL Penalty
        c2 = RoundedRectangle(
            corner_radius=0.15, width=10.6, height=2.4,
            fill_color=COLOR_PANEL, fill_opacity=0.92, stroke_color=COLOR_GOLD, stroke_width=1.5
        ).move_to(DOWN * 1.45)
        hdr2 = Text("2. HÀM MỤC TIÊU TỐI ƯU HÓA CHÍNH SÁCH VÀ HÌNH PHẠT KL", font=DEFAULT_FONT, font_size=12.5, weight=BOLD, color=COLOR_GOLD)
        hdr2.next_to(c2.get_top(), DOWN, buff=0.18)

        eq2 = MathTex(
            r"\mathcal{J}_{\text{GRPO}}(\theta) = \mathbb{E}\left[ \frac{1}{G}\sum_{i=1}^G \min\left( \frac{\pi_\theta}{\pi_{\text{old}}}\hat{A}_i, \text{clip}\left(\frac{\pi_\theta}{\pi_{\text{old}}}, 1-\epsilon, 1+\epsilon\right)\hat{A}_i \right) - \beta \mathbb{D}_{\text{KL}}(\pi_\theta \parallel \pi_{\text{ref}}) \right]",
            font_size=21, color=COLOR_TEXT
        ).move_to(c2.get_center() + UP * 0.05)

        sub_hdr2 = Text(
            "CẮT XÉN [1-EPS, 1+EPS] CHỐNG BÙNG NỔ GRADIENT · PHẠT KL GIỮ NEO NGỮ NGHĨA",
            font=DEFAULT_FONT, font_size=12.0, color=COLOR_MUTED
        ).next_to(eq2, DOWN, buff=0.22)
        grp_c2 = VGroup(c2, hdr2, eq2, sub_hdr2)

        self.play(FadeIn(grp_c1, shift=UP * 0.2), run_time=1.2)
        self.play(FadeIn(grp_c2, shift=UP * 0.2), math_tracker.animate.set_value(1.0), run_time=1.3)
        self.wait(1.5)


# ==============================================================================
# SCENE 4: TELEMETRY — BENCHMARK EVALUATION
# ==============================================================================
class Tap19Scene04Telemetry(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "SO SÁNH CÁC PHƯƠNG PHÁP HỌC TĂNG CƯỜNG")

        scene_title = Text(
            "BENCHMARK KỸ NGHỆ: PPO VS DPO VS GRPO TRÊN DEEPSEEK MATH",
            font=DEFAULT_FONT, font_size=19, weight=BOLD, color=COLOR_GREEN
        ).to_edge(UP, buff=0.95)
        self.play(FadeIn(scene_title, shift=DOWN * 0.2), run_time=0.8)

        telem_tracker = ValueTracker(0.0)

        # 3 Benchmark Telemetry Cards
        cards_data = [
            ("PPO (CLASSIC RL)", COLOR_ROSE, [
                ("Tiêu tốn VRAM", "280 GB (4 Models)", COLOR_ROSE),
                ("Độ ổn định huấn luyện", "KÉM (Value Drift)", COLOR_ROSE),
                ("Phụ thuộc Critic", "BẮT BUỘC 100%", COLOR_ROSE),
                ("Chi phí hạ tầng", "CỰC KỲ ĐẮT ĐỎ", COLOR_ROSE),
            ]),
            ("DPO (OFFLINE PAIRS)", COLOR_CYAN, [
                ("Tiêu tốn VRAM", "160 GB (2 Models)", COLOR_CYAN),
                ("Độ ổn định huấn luyện", "CAO (Học tĩnh)", COLOR_CYAN),
                ("Khả năng tự suy luận", "KHÔNG (Chỉ bắt chước)", COLOR_GOLD),
                ("Aha Moment", "KHÔNG XUẤT HIỆN", COLOR_ROSE),
            ]),
            ("GRPO (GROUP RELATIVE)", COLOR_GREEN, [
                ("Tiêu tốn VRAM", "140 GB (GIẢM 50%)", COLOR_GREEN),
                ("Độ ổn định huấn luyện", "XUẤT SẮC (Rule-based)", COLOR_GREEN),
                ("Khả năng tự suy luận", "BÙNG NỔ (Emergent CoT)", COLOR_GREEN),
                ("Aha Moment", "TỰ PHÁT MINH TỰ SỬA", COLOR_GREEN),
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

        # Highlight GRPO column
        highlight_box = SurroundingRectangle(col_group[2], stroke_color=COLOR_GREEN, stroke_width=2.0, corner_radius=0.15)
        self.play(Create(highlight_box), telem_tracker.animate.set_value(1.0), run_time=1.0)

        # Bottom Conclusion Box
        bot_box = RoundedRectangle(
            corner_radius=0.12, width=10.6, height=0.64,
            fill_color="#181e2b", fill_opacity=0.95, stroke_color=COLOR_GREEN, stroke_width=1.2
        ).to_edge(DOWN, buff=0.35)
        bot_header = Text(
            "KẾT LUẬN: THƯỞNG QUY TẮC KHÁCH QUAN LOẠI BỎ THIÊN KIẾN, MỞ ĐƯỜNG CHO TỰ DUY BẬC CAO",
            font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_GREEN
        ).move_to(bot_box.get_center())

        self.play(FadeIn(bot_box, shift=UP * 0.2), FadeIn(bot_header), run_time=0.8)
        self.wait(1.5)


# ==============================================================================
# SCENE 5: LAB EXPERIMENT — THE AHA MOMENT IN DEEPSEEK-R1
# ==============================================================================
class Tap19Scene05LabExperiment(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "KHOẢNH KHẮC AHA VÀ TIẾN HÓA SUY LUẬN")

        scene_title = Text(
            "LAB DEEPSEEK: SỰ XUẤT HIỆN CỦA NĂNG LỰC TỰ SỬA LỖI (AHA MOMENT)",
            font=DEFAULT_FONT, font_size=19, weight=BOLD, color=COLOR_GOLD
        ).to_edge(UP, buff=0.95)
        self.play(FadeIn(scene_title, shift=DOWN * 0.2), run_time=0.8)

        aha_tracker = ValueTracker(0.0)

        # 3 Multi-step Nodes: Step 1 (Sai lầm) -> Step 2 (Wait rethinking) -> Step 3 (Khắc phục hoàn hảo)
        node_s1 = RoundedRectangle(
            corner_radius=0.12, width=3.0, height=1.6,
            fill_color=COLOR_PANEL, fill_opacity=0.9, stroke_color=COLOR_ROSE, stroke_width=1.5
        ).move_to(LEFT * 4.0 + UP * 0.6)
        s1_hdr = Text("BƯỚC 1: TÍNH NHẦM DẤU", font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_ROSE)
        s1_sub = Text("x + 5 = 12 -> x = 17 (SAI)", font=DEFAULT_FONT, font_size=12.0, color=COLOR_TEXT).next_to(s1_hdr, DOWN, buff=0.12)
        g_s1 = VGroup(node_s1, s1_hdr, s1_sub)
        s1_hdr.move_to(node_s1.get_center() + UP * 0.2)
        s1_sub.move_to(node_s1.get_center() + DOWN * 0.2)

        node_s2 = RoundedRectangle(
            corner_radius=0.12, width=3.6, height=1.8,
            fill_color="#231d34", fill_opacity=0.95, stroke_color=COLOR_GOLD, stroke_width=2.0
        ).move_to(ORIGIN + UP * 0.6)
        s2_hdr = Text("BƯỚC 2: KHOẢNH KHẮC AHA", font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_GOLD)
        s2_quote = Text("\"Wait, let me rethink this...\"", font=DEFAULT_FONT, font_size=12.0, color=COLOR_GOLD).next_to(s2_hdr, DOWN, buff=0.12)
        g_s2 = VGroup(node_s2, s2_hdr, s2_quote)
        s2_hdr.move_to(node_s2.get_center() + UP * 0.22)
        s2_quote.move_to(node_s2.get_center() + DOWN * 0.22)

        node_s3 = RoundedRectangle(
            corner_radius=0.12, width=3.0, height=1.6,
            fill_color=COLOR_PANEL, fill_opacity=0.9, stroke_color=COLOR_GREEN, stroke_width=1.5
        ).move_to(RIGHT * 4.0 + UP * 0.6)
        s3_hdr = Text("BƯỚC 3: QUAY LUI TÌM ĐÁP SỐ", font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_GREEN)
        s3_sub = Text("x = 12 - 5 = 7 (CHÍNH XÁC)", font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_GREEN).next_to(s3_hdr, DOWN, buff=0.12)
        g_s3 = VGroup(node_s3, s3_hdr, s3_sub)
        s3_hdr.move_to(node_s3.get_center() + UP * 0.2)
        s3_sub.move_to(node_s3.get_center() + DOWN * 0.2)

        arr1 = ZenArrow(start=node_s1.get_right(), end=node_s2.get_left(), color=COLOR_GOLD, stroke_width=2.4)
        arr2 = ZenArrow(start=node_s2.get_right(), end=node_s3.get_left(), color=COLOR_GREEN, stroke_width=2.4)

        self.play(
            FadeIn(g_s1), GrowArrow(arr1),
            FadeIn(g_s2), GrowArrow(arr2),
            FadeIn(g_s3), run_time=1.4
        )

        # Pulse Aha Dot
        pulse_dot = Dot(point=node_s2.get_center(), radius=0.12, color=COLOR_GOLD)
        self.play(FadeIn(pulse_dot), aha_tracker.animate.set_value(1.0), run_time=0.8)

        # Bottom Deployment Pillars Card
        spec_box = RoundedRectangle(
            corner_radius=0.15, width=10.6, height=2.0,
            fill_color=COLOR_PANEL, fill_opacity=0.9, stroke_color=COLOR_CYAN, stroke_width=1.2
        ).to_edge(DOWN, buff=0.45)
        spec_header = Text("Ý NGHĨA KỸ NGHỆ CỦA HIỆN TƯỢNG AHA (DEEPSEEK-R1-ZERO)", font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_CYAN)
        spec_header.next_to(spec_box.get_top(), DOWN, buff=0.20)

        line1_header = Text("• ZERO SFT DATA: KHÔNG CẦN BẤT KỲ BÀI MẪU SUY NGHĨ NÀO CỦA CON NGƯỜI", font=DEFAULT_FONT, font_size=12.0, color=COLOR_TEXT).next_to(spec_header, DOWN, buff=0.18, aligned_edge=LEFT)
        line2_header = Text("• TỰ PHÁT MINH TỰ KIỂM TRA: CHUỖI TOKEN DÀI RA ĐỂ TỐI ĐA HÓA XÁC SUẤT ĐÚNG", font=DEFAULT_FONT, font_size=12.0, color=COLOR_GREEN).next_to(line1_header, DOWN, buff=0.15, aligned_edge=LEFT)
        line3_header = Text("• TEST-TIME COMPUTE: DỊCH CHUYỂN NĂNG LƯỢNG TÍNH TOÁN SANG THỜI GIAN SUY LUẬN", font=DEFAULT_FONT, font_size=12.0, color=COLOR_GOLD).next_to(line2_header, DOWN, buff=0.15, aligned_edge=LEFT)

        grp_spec = VGroup(spec_box, spec_header, line1_header, line2_header, line3_header)
        self.play(FadeIn(grp_spec, shift=UP * 0.2), run_time=1.1)
        self.wait(1.5)


# ==============================================================================
# SCENE 6: OUTRO — SUMMARY, CRAFTSMANSHIP & EPISODE 20 TEASER
# ==============================================================================
class Tap19Scene06Outro(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "TỔNG KẾT & CẦU NỐI KỸ NGHỆ")

        scene_title = Text(
            "BÀN GIAO TRI THỨC // GRPO & REASONING MODELS",
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
        # 1. Next Video Card (Episode 20: Hallucination Anatomy): X in [+1.6, +5.4], Y in [+0.5, +2.5]
        # Clearance to mosaic right edge (-0.30): +1.60 - (-0.30) = 1.90 units = 342px >= 300px!
        next_card = RoundedRectangle(
            corner_radius=0.12, width=3.8, height=2.0,
            fill_color=COLOR_PANEL, fill_opacity=0.7, stroke_color=COLOR_CYAN, stroke_width=1.5
        ).move_to(RIGHT * 3.5 + UP * 1.5)
        next_header = Text("TẬP TIẾP THEO // TẬP 20", font=DEFAULT_FONT, font_size=12.5, weight=BOLD, color=COLOR_CYAN)
        next_sub_header = Text("ẢO GIÁC AI: GIẢI PHẪU NGUỒN CỘI", font=DEFAULT_FONT, font_size=12.0, color=COLOR_TEXT).next_to(next_header, DOWN, buff=0.18)
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
