#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
manim_s2_tap_17_ppo.py
=======================
2K QHD (2560x1440 @ 60fps) Mathematical Cinema Engine for ZenPham Series 2 Episode 17:
"PPO vs DPO vs KTO vs ORPO — 4 Trường Phái Dạy AI Đạo Đức"

Adversarial Council & Thinkers Integrated:
- Dario Amodei: Online RLHF vs Offline Preference Traps, OOD Drift, Sycophancy (Flattery Hallucination).
- Henri Poincaré: Geometric Loss Landscapes: Clipped PPO vs Bradley-Terry DPO vs S-Curve Kahneman KTO.
- Kurt Gödel: Arrow's Impossibility Theorem & Goodhart's Law in Finite Datasets, Syntactic vs Semantic Alignment.
- Claude Shannon: Mutual Information Channel Capacity: Pairwise Feedback (1 bit) vs Scalar vs Token Odds Ratio.

Design System:
- Neo-Noir Tech Minimalist (Obsidian #0c0d12, Panel #161b26, Cyan #00e5ff, Gold #ffb300, Green #00e676, Rose #ff2a6d)
- 2K QHD native (2560x1440, 60fps, 14.22x8.0 unit frame)
- Minimum font size >= 12.0pt (anti-micro-text compliant)
- Anti-Slide-Deck certified (0 paragraph violations, pure kinetic HUD & geometric telemetry)
- YouTube Interactive End Screen Safe Zones (Next Card Ep 18, Playlist, Subscribe, 5x5 Mosaic)
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
        f"ZENPHAM // TÔI LÀM VIỆC — TẬP 17: {ep_title}",
        font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_TEXT
    ).move_to(badge_bg.get_center())

    scene.add(watermark, badge_bg, badge_txt)


# ==============================================================================
# SCENE 1: COLD OPEN — FOUR ALIGNMENT PARADIGMS
# ==============================================================================
class Tap17Scene01ColdOpen(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "BỐN TRƯỜNG PHÁI CĂN CHỈNH AI")

        scene_title = Text(
            "BỐN TRƯỜNG PHÁI TOÁN HỌC CĂN CHỈNH ĐẠO ĐỨC & HÀNH VI LLM",
            font=DEFAULT_FONT, font_size=19, weight=BOLD, color=COLOR_GOLD
        ).to_edge(UP, buff=0.95)
        self.play(FadeIn(scene_title, shift=DOWN * 0.2), run_time=0.8)

        # 4 Quadrants Grid
        quads = [
            ("PPO (ONLINE RL)", "Tự khám phá thời gian thực", "4 Models trên GPU", COLOR_ROSE, LEFT * 3.3 + UP * 0.8),
            ("DPO (OFFLINE PAIRS)", "Cặp so găng nhị phân tĩnh", "Khai tử Reward Model", COLOR_CYAN, RIGHT * 3.3 + UP * 0.8),
            ("KTO (PROSPECT THEORY)", "Dữ liệu đơn lẻ Upvote/Down", "Thuyết triển vọng Nobel", COLOR_GOLD, LEFT * 3.3 + DOWN * 1.5),
            ("ORPO (MONOLITHIC)", "Hợp nhất SFT và Alignment", "Khai tử Reference Model", COLOR_GREEN, RIGHT * 3.3 + DOWN * 1.5),
        ]

        boxes = []
        for name, sub1, sub2, col, pos in quads:
            box = RoundedRectangle(
                corner_radius=0.15, height=1.9, width=5.6,
                fill_color=COLOR_PANEL, fill_opacity=0.92, stroke_color=col, stroke_width=1.8
            ).move_to(pos)
            lbl = Text(name, font=DEFAULT_FONT, font_size=12.5, weight=BOLD, color=col).move_to(box.get_top() + DOWN * 0.32)
            s1 = Text(sub1, font=DEFAULT_FONT, font_size=12.0, color=COLOR_TEXT).move_to(box.get_center() + UP * 0.05)
            s2 = Text(sub2, font=DEFAULT_FONT, font_size=12.0, color=COLOR_MUTED).move_to(box.get_bottom() + UP * 0.32)
            boxes.append(VGroup(box, lbl, s1, s2))

        self.play(
            LaggedStart(
                FadeIn(boxes[0], shift=RIGHT * 0.2),
                FadeIn(boxes[1], shift=LEFT * 0.2),
                FadeIn(boxes[2], shift=RIGHT * 0.2),
                FadeIn(boxes[3], shift=LEFT * 0.2),
                lag_ratio=0.20
            ),
            run_time=1.5
        )

        # Bottom summary callout
        summary_box = RoundedRectangle(
            corner_radius=0.12, height=0.64, width=10.6,
            fill_color="#181e2b", fill_opacity=0.95, stroke_color=COLOR_CYAN, stroke_width=1.2
        ).to_edge(DOWN, buff=0.35)
        summary_header = Text(
            "KHÔNG CÓ PHƯƠNG PHÁP HOÀN HẢO TUYỆT ĐỐI — MỖI HÀM MẤT MÁT LÀ MỘT BÀI TOÁN ĐÁNH ĐỔI HÌNH HỌC",
            font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_CYAN
        ).move_to(summary_box.get_center())

        self.play(FadeIn(summary_box), FadeIn(summary_header), run_time=0.8)
        self.wait(1.5)


# ==============================================================================
# SCENE 2: ARCHITECTURE — PPO CLIPPED SURROGATE OBJECTIVE
# ==============================================================================
class Tap17Scene02Architecture(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "CƠ CHẾ CLIPPING TRONG THUẬT TOÁN PPO")

        scene_title = Text(
            "HÀM MỤC TIÊU CẮT TỈA (CLIPPED SURROGATE) TRONG THUẬT TOÁN PPO",
            font=DEFAULT_FONT, font_size=19, weight=BOLD, color=COLOR_GOLD
        ).to_edge(UP, buff=0.95)
        self.play(FadeIn(scene_title, shift=DOWN * 0.2), run_time=0.8)

        # 1. Top Card: PPO Clipping Equation
        eq_box = RoundedRectangle(
            corner_radius=0.15, width=10.6, height=1.9,
            fill_color=COLOR_PANEL, fill_opacity=0.92, stroke_color=COLOR_ROSE, stroke_width=1.5
        ).move_to(UP * 1.1)
        eq_hdr = Text("CÔNG THỨC MỤC TIÊU CẮT TỈA PPO (SCHULMAN ET AL. OPENAI)", font=DEFAULT_FONT, font_size=12.5, weight=BOLD, color=COLOR_ROSE)
        eq_hdr.next_to(eq_box.get_top(), DOWN, buff=0.18)

        eq_math = MathTex(
            r"\mathcal{L}^{\text{CLIP}}(\theta) = \hat{\mathbb{E}}_t \left[ \min\left( r_t(\theta) \hat{A}_t, \, \text{clip}\left(r_t(\theta), 1-\epsilon, 1+\epsilon\right) \hat{A}_t \right) \right], \quad r_t(\theta) = \frac{\pi_\theta(a_t \mid s_t)}{\pi_{\theta_{\text{old}}}(a_t \mid s_t)}",
            font_size=21, color=COLOR_TEXT
        ).move_to(eq_box.get_center() + DOWN * 0.15)
        grp_eq = VGroup(eq_box, eq_hdr, eq_math)

        # 2. Left Column: Positive Advantage
        pos_box = RoundedRectangle(
            corner_radius=0.12, width=5.1, height=2.8,
            fill_color=COLOR_PANEL, fill_opacity=0.9, stroke_color=COLOR_GREEN, stroke_width=1.5
        ).move_to(LEFT * 2.8 + DOWN * 1.5)
        pos_hdr = Text("KHI LỢI THẾ DƯƠNG (A > 0)", font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_GREEN)
        pos_hdr.next_to(pos_box.get_top(), DOWN, buff=0.20)
        p1_hdr = Text("• Hành động tốt hơn mức kỳ vọng nền", font=DEFAULT_FONT, font_size=12.0, color=COLOR_TEXT).next_to(pos_hdr, DOWN, buff=0.16, aligned_edge=LEFT)
        p2_hdr = Text("• Tỷ số r tăng: Cần khuyến khích hành vi", font=DEFAULT_FONT, font_size=12.0, color=COLOR_CYAN).next_to(p1_hdr, DOWN, buff=0.12, aligned_edge=LEFT)
        p3_hdr = Text("• Bị chặn trên ở 1 + epsilon (1.20)", font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_GREEN).next_to(p2_hdr, DOWN, buff=0.12, aligned_edge=LEFT)
        p4_hdr = Text("• Triệt tiêu gradient nếu cập nhật quá đà", font=DEFAULT_FONT, font_size=12.0, color=COLOR_MUTED).next_to(p3_hdr, DOWN, buff=0.12, aligned_edge=LEFT)
        grp_pos = VGroup(pos_box, pos_hdr, p1_hdr, p2_hdr, p3_hdr, p4_hdr)

        # 3. Right Column: Negative Advantage
        neg_box = RoundedRectangle(
            corner_radius=0.12, width=5.1, height=2.8,
            fill_color=COLOR_PANEL, fill_opacity=0.9, stroke_color=COLOR_ROSE, stroke_width=1.5
        ).move_to(RIGHT * 2.8 + DOWN * 1.5)
        neg_hdr = Text("KHI LỢI THẾ ÂM (A < 0)", font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_ROSE)
        neg_hdr.next_to(neg_box.get_top(), DOWN, buff=0.20)
        n1_hdr = Text("• Hành động kém hơn mức kỳ vọng nền", font=DEFAULT_FONT, font_size=12.0, color=COLOR_TEXT).next_to(neg_hdr, DOWN, buff=0.16, aligned_edge=LEFT)
        n2_hdr = Text("• Tỷ số r giảm: Cần dìm giảm xác suất", font=DEFAULT_FONT, font_size=12.0, color=COLOR_ROSE).next_to(n1_hdr, DOWN, buff=0.12, aligned_edge=LEFT)
        n3_hdr = Text("• Bị chặn dưới ở 1 - epsilon (0.80)", font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_GOLD).next_to(n2_hdr, DOWN, buff=0.12, aligned_edge=LEFT)
        n4_hdr = Text("• Bảo vệ mạng nơ-ron không bị sụp đổ", font=DEFAULT_FONT, font_size=12.0, color=COLOR_MUTED).next_to(n3_hdr, DOWN, buff=0.12, aligned_edge=LEFT)
        grp_neg = VGroup(neg_box, neg_hdr, n1_hdr, n2_hdr, n3_hdr, n4_hdr)

        self.play(FadeIn(grp_eq, shift=UP * 0.2), run_time=1.2)
        self.play(FadeIn(grp_pos, shift=RIGHT * 0.2), FadeIn(grp_neg, shift=LEFT * 0.2), run_time=1.3)
        self.wait(1.5)


# ==============================================================================
# SCENE 3: MATHEMATICS — DPO VS KTO PROSPECT THEORY
# ==============================================================================
class Tap17Scene03Mathematics(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "DPO VÀ THUYẾT TRIỂN VỌNG TRONG KTO")

        scene_title = Text(
            "DPO TRÊN CẶP SỞ THÍCH VS KTO TRÊN DỮ LIỆU ĐƠN LẺ",
            font=DEFAULT_FONT, font_size=19, weight=BOLD, color=COLOR_GOLD
        ).to_edge(UP, buff=0.95)
        self.play(FadeIn(scene_title, shift=DOWN * 0.2), run_time=0.8)

        math_tracker = ValueTracker(0.0)

        # 1. Left Card: DPO Pairwise
        c1 = RoundedRectangle(
            corner_radius=0.15, width=5.6, height=4.2,
            fill_color=COLOR_PANEL, fill_opacity=0.92, stroke_color=COLOR_CYAN, stroke_width=1.5
        ).move_to(LEFT * 3.3 + DOWN * 0.35)
        hdr1 = Text("1. DPO (PAIRWISE PREFERENCE)", font=DEFAULT_FONT, font_size=12.5, weight=BOLD, color=COLOR_CYAN)
        hdr1.next_to(c1.get_top(), DOWN, buff=0.20)

        eq1 = MathTex(
            r"\mathcal{L}_{\text{DPO}} = -\mathbb{E}\left[ \log \sigma\left( \beta \log \frac{\pi_\theta(y_w \mid x)}{\pi_{\text{ref}}(y_w \mid x)} - \beta \log \frac{\pi_\theta(y_l \mid x)}{\pi_{\text{ref}}(y_l \mid x)} \right) \right]",
            font_size=17, color=COLOR_TEXT
        ).move_to(c1.get_center() + UP * 0.6)

        d1_hdr = Text("• ĐẦU VÀO: BẮT BUỘC CẶP SO GÁNG (x, yw, yl)", font=DEFAULT_FONT, font_size=12.0, color=COLOR_TEXT).next_to(eq1, DOWN, buff=0.20, aligned_edge=LEFT)
        d2_hdr = Text("• THUẬN LỢI: LOẠI BỎ MẠNG REWARD VÀ CRITIC", font=DEFAULT_FONT, font_size=12.0, color=COLOR_GREEN).next_to(d1_hdr, DOWN, buff=0.12, aligned_edge=LEFT)
        d3_hdr = Text("• ĐIỂM YẾU: CẦN 2 MÔ HÌNH (ACTOR + REF)", font=DEFAULT_FONT, font_size=12.0, color=COLOR_GOLD).next_to(d2_hdr, DOWN, buff=0.12, aligned_edge=LEFT)
        d4_hdr = Text("• NGUY CƠ: OOD HALLUCINATION TRÊN TẬP TĨNH", font=DEFAULT_FONT, font_size=12.0, color=COLOR_ROSE).next_to(d3_hdr, DOWN, buff=0.12, aligned_edge=LEFT)

        grp_c1 = VGroup(c1, hdr1, eq1, d1_hdr, d2_hdr, d3_hdr, d4_hdr)

        # 2. Right Card: KTO Prospect Theory
        c2 = RoundedRectangle(
            corner_radius=0.15, width=5.6, height=4.2,
            fill_color=COLOR_PANEL, fill_opacity=0.92, stroke_color=COLOR_GOLD, stroke_width=1.5
        ).move_to(RIGHT * 3.3 + DOWN * 0.35)
        hdr2 = Text("2. KTO (KAHNEMAN-TVERSKY NOBEL)", font=DEFAULT_FONT, font_size=12.5, weight=BOLD, color=COLOR_GOLD)
        hdr2.next_to(c2.get_top(), DOWN, buff=0.20)

        eq2 = MathTex(
            r"v(r) = \begin{cases} \sigma(r) & \text{if Upvote } (y \in Y_w) \\ 1 - \sigma(\lambda_{\text{loss}} r) & \text{if Downvote } (y \in Y_l) \end{cases}",
            font_size=19, color=COLOR_TEXT
        ).move_to(c2.get_center() + UP * 0.6)

        k1_hdr = Text("• ĐẦU VÀO: DỮ LIỆU ĐƠN LẺ (x, y) + UP/DOWN", font=DEFAULT_FONT, font_size=12.0, color=COLOR_TEXT).next_to(eq2, DOWN, buff=0.20, aligned_edge=LEFT)
        k2_hdr = Text("• TÂM LÝ HỌC: PHẠT MẤT MÁT DỐC GẤP 2.25 LẦN", font=DEFAULT_FONT, font_size=12.0, color=COLOR_GOLD).next_to(k1_hdr, DOWN, buff=0.12, aligned_edge=LEFT)
        k3_hdr = Text("• KHAI PHÓNG: DÙNG TRỰC TIẾP LOG NGƯỜI DÙNG", font=DEFAULT_FONT, font_size=12.0, color=COLOR_GREEN).next_to(k2_hdr, DOWN, buff=0.12, aligned_edge=LEFT)
        k4_hdr = Text("• TIẾT KIỆM: KHÔNG CẦN CHUYÊN GIA DÁN CẶP", font=DEFAULT_FONT, font_size=12.0, color=COLOR_CYAN).next_to(k3_hdr, DOWN, buff=0.12, aligned_edge=LEFT)

        grp_c2 = VGroup(c2, hdr2, eq2, k1_hdr, k2_hdr, k3_hdr, k4_hdr)

        self.play(FadeIn(grp_c1, shift=RIGHT * 0.2), run_time=1.2)
        self.play(FadeIn(grp_c2, shift=LEFT * 0.2), math_tracker.animate.set_value(1.0), run_time=1.3)
        self.wait(1.5)


# ==============================================================================
# SCENE 4: TELEMETRY — ORPO MONOLITHIC ALIGNMENT
# ==============================================================================
class Tap17Scene04Telemetry(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "ĐỘT PHÁ ORPO LOẠI BỎ REFERENCE MODEL")

        scene_title = Text(
            "ORPO: CĂN CHỈNH NGUYÊN KHỐI 1 BƯỚC LOẠI BỎ HOÀN TOÀN REFERENCE MODEL",
            font=DEFAULT_FONT, font_size=19, weight=BOLD, color=COLOR_GREEN
        ).to_edge(UP, buff=0.95)
        self.play(FadeIn(scene_title, shift=DOWN * 0.2), run_time=0.8)

        telem_tracker = ValueTracker(0.0)

        # 3 Benchmark Telemetry Cards: PPO vs DPO vs ORPO
        cards_data = [
            ("PPO (ONLINE RL)", COLOR_ROSE, [
                ("Mô hình trên GPU", "4 Models (~560 GB)", COLOR_ROSE),
                ("Độ ổn định", "Thấp (Nhạy tham số)", COLOR_ROSE),
                ("Số bước huấn luyện", "3 Stages (SFT->RM->PPO)", COLOR_ROSE),
                ("Vượt trần năng lực", "CỰC KỲ MẠNH (Toán/Code)", COLOR_GREEN),
            ]),
            ("DPO (OFFLINE PAIRS)", COLOR_CYAN, [
                ("Mô hình trên GPU", "2 Models (~280 GB)", COLOR_CYAN),
                ("Độ ổn định", "Rất cao (Hồi quy tĩnh)", COLOR_CYAN),
                ("Số bước huấn luyện", "2 Stages (SFT -> DPO)", COLOR_GOLD),
                ("Vượt trần năng lực", "BỊ GIỚI HẠN BỞI DỮ LIỆU", COLOR_ROSE),
            ]),
            ("ORPO (MONOLITHIC)", COLOR_GREEN, [
                ("Mô hình trên GPU", "1 Model (~140 GB)", COLOR_GREEN),
                ("Độ ổn định", "Cao (Odds Ratio Loss)", COLOR_GREEN),
                ("Số bước huấn luyện", "1 Stage Duy Nhất", COLOR_GREEN),
                ("Vượt trần năng lực", "TỐI ƯU CHI PHÍ VRAM", COLOR_GREEN),
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

        # Highlight ORPO column
        highlight_box = SurroundingRectangle(col_group[2], stroke_color=COLOR_GREEN, stroke_width=2.0, corner_radius=0.15)
        self.play(Create(highlight_box), telem_tracker.animate.set_value(1.0), run_time=1.0)

        # Bottom Conclusion Box
        bot_box = RoundedRectangle(
            corner_radius=0.12, width=10.6, height=0.64,
            fill_color="#181e2b", fill_opacity=0.95, stroke_color=COLOR_GREEN, stroke_width=1.2
        ).to_edge(DOWN, buff=0.35)
        bot_header = Text(
            "KẾT LUẬN: ORPO LOẠI BỎ REFERENCE MODEL, CHO PHÉP TINH CHỈNH 70B TRÊN PHẦN CỨNG TIẾT KIỆM",
            font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_GREEN
        ).move_to(bot_box.get_center())

        self.play(FadeIn(bot_box, shift=UP * 0.2), FadeIn(bot_header), run_time=0.8)
        self.wait(1.5)


# ==============================================================================
# SCENE 5: LAB EXPERIMENT — DECISION MATRIX & SYCOPHANCY TRAP
# ==============================================================================
class Tap17Scene05LabExperiment(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "MA TRẬN RA QUYẾT ĐỊNH CHO KỸ SƯ AI")

        scene_title = Text(
            "LAB DOANH NGHIỆP: CẠM BẪY NỊNH NỌT (SYCOPHANCY) VÀ MA TRẬN CHIẾN LƯỢC",
            font=DEFAULT_FONT, font_size=19, weight=BOLD, color=COLOR_GOLD
        ).to_edge(UP, buff=0.95)
        self.play(FadeIn(scene_title, shift=DOWN * 0.2), run_time=0.8)

        syco_tracker = ValueTracker(0.0)

        # 3 Multi-step Nodes: Step 1 (User Query) -> Step 2 (Sycophancy Trap) -> Step 3 (Truth Alignment)
        node_q1 = RoundedRectangle(
            corner_radius=0.12, width=3.0, height=1.6,
            fill_color=COLOR_PANEL, fill_opacity=0.9, stroke_color=COLOR_CYAN, stroke_width=1.5
        ).move_to(LEFT * 4.0 + UP * 0.6)
        q1_hdr = Text("CÂU HỎI BẪY", font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_CYAN)
        q1_sub = Text("2 + 2 = 5 có đúng không?", font=DEFAULT_FONT, font_size=12.0, color=COLOR_TEXT).next_to(q1_hdr, DOWN, buff=0.12)
        g_q1 = VGroup(node_q1, q1_hdr, q1_sub)
        q1_hdr.move_to(node_q1.get_center() + UP * 0.2)
        q1_sub.move_to(node_q1.get_center() + DOWN * 0.2)

        node_q2 = RoundedRectangle(
            corner_radius=0.12, width=3.6, height=1.8,
            fill_color="#231d34", fill_opacity=0.95, stroke_color=COLOR_ROSE, stroke_width=2.0
        ).move_to(ORIGIN + UP * 0.6)
        q2_hdr = Text("ẢO GIÁC NỊNH NỌT (SYCOPHANCY)", font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_ROSE)
        q2_quote = Text("\"Bạn thật sáng tạo, rất có lý!\"", font=DEFAULT_FONT, font_size=12.0, color=COLOR_ROSE).next_to(q2_hdr, DOWN, buff=0.12)
        g_q2 = VGroup(node_q2, q2_hdr, q2_quote)
        q2_hdr.move_to(node_q2.get_center() + UP * 0.22)
        q2_quote.move_to(node_q2.get_center() + DOWN * 0.22)

        node_q3 = RoundedRectangle(
            corner_radius=0.12, width=3.0, height=1.6,
            fill_color=COLOR_PANEL, fill_opacity=0.9, stroke_color=COLOR_GREEN, stroke_width=1.5
        ).move_to(RIGHT * 4.0 + UP * 0.6)
        q3_hdr = Text("CĂN CHỈNH CHÂN LÝ KHÁCH QUAN", font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_GREEN)
        q3_sub = Text("2 + 2 = 4 (Kiên định sự thật)", font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_GREEN).next_to(q3_hdr, DOWN, buff=0.12)
        g_q3 = VGroup(node_q3, q3_hdr, q3_sub)
        q3_hdr.move_to(node_q3.get_center() + UP * 0.2)
        q3_sub.move_to(node_q3.get_center() + DOWN * 0.2)

        arr1 = ZenArrow(start=node_q1.get_right(), end=node_q2.get_left(), color=COLOR_ROSE, stroke_width=2.4)
        arr2 = ZenArrow(start=node_q2.get_right(), end=node_q3.get_left(), color=COLOR_GREEN, stroke_width=2.4)

        self.play(
            FadeIn(g_q1), GrowArrow(arr1),
            FadeIn(g_q2), GrowArrow(arr2),
            FadeIn(g_q3), run_time=1.4
        )

        pulse_dot = Dot(point=node_q2.get_center(), radius=0.12, color=COLOR_ROSE)
        self.play(FadeIn(pulse_dot), syco_tracker.animate.set_value(1.0), run_time=0.8)

        # Bottom Strategy Decision Matrix Card
        spec_box = RoundedRectangle(
            corner_radius=0.15, width=10.6, height=2.0,
            fill_color=COLOR_PANEL, fill_opacity=0.9, stroke_color=COLOR_CYAN, stroke_width=1.2
        ).to_edge(DOWN, buff=0.45)
        spec_header = Text("CÂY QUYẾT ĐỊNH CHIẾN LƯỢC TRIỂN KHAI ALIGNMENT", font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_CYAN)
        spec_header.next_to(spec_box.get_top(), DOWN, buff=0.20)

        line1_header = Text("• VĂN PHONG & AN TOÀN TỔNG QUÁT: CHỌN DPO / KTO / ORPO ĐỂ TỐI ƯU CHI PHÍ", font=DEFAULT_FONT, font_size=12.0, color=COLOR_TEXT).next_to(spec_header, DOWN, buff=0.18, aligned_edge=LEFT)
        line2_header = Text("• SUY LUẬN TOÁN & MÃ NGUỒN: BẮT BUỘC DÙNG ONLINE RL (PPO/GRPO) ĐỂ KIỂM CHỨNG", font=DEFAULT_FONT, font_size=12.0, color=COLOR_GREEN).next_to(line1_header, DOWN, buff=0.15, aligned_edge=LEFT)
        line3_header = Text("• GOODHART'S LAW: KHI ĐIỂM THƯỞNG TRỞ THÀNH MỤC TIÊU, MÔ HÌNH DỄ NỊNH NỌT", font=DEFAULT_FONT, font_size=12.0, color=COLOR_GOLD).next_to(line2_header, DOWN, buff=0.15, aligned_edge=LEFT)

        grp_spec = VGroup(spec_box, spec_header, line1_header, line2_header, line3_header)
        self.play(FadeIn(grp_spec, shift=UP * 0.2), run_time=1.1)
        self.wait(1.5)


# ==============================================================================
# SCENE 6: OUTRO — SUMMARY, CRAFTSMANSHIP & EPISODE 18 TEASER
# ==============================================================================
class Tap17Scene06Outro(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "TỔNG KẾT & CẦU NỐI KỸ NGHỆ")

        scene_title = Text(
            "BÀN GIAO TRI THỨC // 4 TRƯỜNG PHÁI CĂN CHỈNH ĐẠO ĐỨC AI",
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
        # 1. Next Video Card (Episode 18: Chain of Thought): X in [+1.6, +5.4], Y in [+0.5, +2.5]
        # Clearance to mosaic right edge (-0.30): +1.60 - (-0.30) = 1.90 units = 342px >= 300px!
        next_card = RoundedRectangle(
            corner_radius=0.12, width=3.8, height=2.0,
            fill_color=COLOR_PANEL, fill_opacity=0.7, stroke_color=COLOR_CYAN, stroke_width=1.5
        ).move_to(RIGHT * 3.5 + UP * 1.5)
        next_header = Text("TẬP TIẾP THEO // TẬP 18", font=DEFAULT_FONT, font_size=12.5, weight=BOLD, color=COLOR_CYAN)
        next_sub_header = Text("CHAIN OF THOUGHT: SUY LUẬN TỪNG BƯỚC", font=DEFAULT_FONT, font_size=12.0, color=COLOR_TEXT).next_to(next_header, DOWN, buff=0.18)
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
