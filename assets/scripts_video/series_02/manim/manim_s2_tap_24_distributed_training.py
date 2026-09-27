#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Manim 2K Mathematical Engine — Series 2, Episode 24: Distributed Training
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
    brand_header = Text("ZENPHAM", font=DEFAULT_FONT, font_size=13.0, weight=BOLD, color=COLOR_GOLD)
    sub_header = Text("KỸ NGHỆ LLM TỐI TÂN", font=DEFAULT_FONT, font_size=12.0, color=COLOR_MUTED).next_to(brand_header, DOWN, buff=0.06)
    watermark = VGroup(brand_header, sub_header).to_corner(UR, buff=0.45)

    badge_bg = RoundedRectangle(
        corner_radius=0.12, height=0.46, width=8.5,
        fill_color=COLOR_PANEL, fill_opacity=0.9, stroke_color=COLOR_CYAN, stroke_width=1.0
    )
    badge_bg.to_edge(UP, buff=0.35)
    badge_header = Text(f"ZENPHAM // TÔI LÀM VIỆC — {ep_title}", font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_TEXT)
    badge_header.move_to(badge_bg.get_center())

    scene.add(watermark, badge_bg, badge_header)


# ==============================================================================
# SCENE 1: COLD OPEN — THE MEMORY WALL & DISTRIBUTED COSMIC LATTICE
# ==============================================================================
class Tap24Scene01ColdOpen(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "BỨC TƯỜNG BỘ NHỚ VRAM & DISTRIBUTED TRAINING")

        scene_title = Text(
            "BỨC TƯỜNG VẬT LÝ VRAM: MÔ HÌNH 70B TRÊN GPU ĐƠN LẺ",
            font=DEFAULT_FONT, font_size=17.5, weight=BOLD, color=COLOR_GOLD
        )
        scene_title.to_edge(UP, buff=0.95)
        self.play(FadeIn(scene_title, shift=DOWN * 0.2), run_time=0.8)

        # Single GPU Physical Card Container
        gpu_card = RoundedRectangle(
            corner_radius=0.15, width=3.4, height=2.2,
            fill_color=COLOR_PANEL, fill_opacity=0.9, stroke_color=COLOR_MUTED, stroke_width=1.5
        ).move_to(DOWN * 0.2)
        gpu_header = Text("NVIDIA H100 SXM5", font=DEFAULT_FONT, font_size=12.5, weight=BOLD, color=COLOR_CYAN)
        gpu_header.next_to(gpu_card.get_top(), DOWN, buff=0.25)
        gpu_sub = Text("VRAM: 80 GB HBM3", font=DEFAULT_FONT, font_size=12.0, color=COLOR_TEXT)
        gpu_sub.next_to(gpu_header, DOWN, buff=0.18)
        single_gpu_grp = VGroup(gpu_card, gpu_header, gpu_sub)
        self.play(FadeIn(single_gpu_grp), run_time=1.0)

        # Towering 70B Tensor Footprint Sphere Overwhelming Single GPU
        tensor_core = Circle(
            radius=1.85, stroke_color=COLOR_ROSE, stroke_width=2.5,
            fill_color=COLOR_ROSE, fill_opacity=0.22
        ).move_to(DOWN * 0.2)
        tensor_ring = Annulus(
            inner_radius=1.35, outer_radius=1.85,
            stroke_color=COLOR_ROSE, stroke_width=1.5, fill_opacity=0.12
        ).move_to(DOWN * 0.2)
        math_oom = fit_math_to_card(
            r"M_{\text{total}} = 1{,}120\,\text{GB} \gg 80\,\text{GB}",
            tensor_core, font_size=23.0, color=COLOR_ROSE, padding_x=0.20, padding_y=0.10
        )

        oom_box = RoundedRectangle(
            corner_radius=0.10, width=4.6, height=0.62,
            fill_color="#2b0a14", fill_opacity=0.95, stroke_color=COLOR_ROSE, stroke_width=1.6
        ).next_to(tensor_core, UP, buff=0.25)
        oom_header = create_wrapped_card_text(
            "CUDA OUT OF MEMORY (OOM)",
            oom_box, font=DEFAULT_FONT, font_size=12.5, weight=BOLD, color=COLOR_ROSE, padding_x=0.20, padding_y=0.10
        )

        self.play(
            Create(tensor_core),
            Create(tensor_ring),
            Write(math_oom),
            FadeIn(oom_box),
            Write(oom_header),
            Flash(oom_box, color=COLOR_ROSE),
            run_time=2.0
        )

        # Dynamic Pullback: Shrink Single Overwhelmed GPU & Expand into 4x6 Distributed Lattice
        lattice_tracker = ValueTracker(0.0)
        grid_nodes = VGroup()
        grid_lines = VGroup()

        rows, cols = 3, 6
        dx, dy = 1.8, 1.2
        x_start, y_start = -4.5, 1.0

        for r in range(rows):
            for c in range(cols):
                pos = np.array([x_start + c * dx, y_start - r * dy, 0.0])
                node_box = RoundedRectangle(
                    corner_radius=0.08, width=0.95, height=0.60,
                    fill_color=COLOR_PANEL, fill_opacity=0.85, stroke_color=COLOR_CYAN, stroke_width=1.2
                ).move_to(pos)
                node_dot = Dot(pos, radius=0.06, color=COLOR_GOLD)
                grid_nodes.add(VGroup(node_box, node_dot))

        # Optical Interconnect Links (Horizontal & Vertical Dashed Lines)
        for r in range(rows):
            for c in range(cols - 1):
                p1 = np.array([x_start + c * dx + 0.48, y_start - r * dy, 0.0])
                p2 = np.array([x_start + (c + 1) * dx - 0.48, y_start - r * dy, 0.0])
                grid_lines.add(DashedLine(p1, p2, stroke_color=COLOR_CYAN, stroke_width=1.2, stroke_opacity=0.6))

        for r in range(rows - 1):
            for c in range(cols):
                p1 = np.array([x_start + c * dx, y_start - r * dy - 0.30, 0.0])
                p2 = np.array([x_start + c * dx, y_start - (r + 1) * dy + 0.30, 0.0])
                grid_lines.add(DashedLine(p1, p2, stroke_color=COLOR_CYAN, stroke_width=1.2, stroke_opacity=0.6))

        callout_header = Text(
            "LƯỚI ĐIỀU PHỐI 16,384 GPU: 1.3 PETABYTES BỘ NHỚ THỐNG NHẤT",
            font=DEFAULT_FONT, font_size=12.5, weight=BOLD, color=COLOR_CYAN
        )
        callout_box = SurroundingRectangle(
            callout_header, buff=0.15, stroke_color=COLOR_CYAN, stroke_width=1.2,
            fill_color=COLOR_PANEL, fill_opacity=0.9
        )
        callout_grp = VGroup(callout_box, callout_header).to_edge(DOWN, buff=0.45)

        self.play(
            FadeOut(single_gpu_grp),
            FadeOut(tensor_core),
            FadeOut(tensor_ring),
            FadeOut(math_oom),
            FadeOut(oom_box),
            FadeOut(oom_header),
            LaggedStart(*[FadeIn(n, scale=0.6) for n in grid_nodes], lag_ratio=0.03),
            Create(grid_lines),
            FadeIn(callout_grp, shift=UP * 0.2),
            lattice_tracker.animate.set_value(1.0),
            run_time=2.5
        )
        self.wait(1.5)


# ==============================================================================
# SCENE 2: ARCHITECTURE — 3D MEMORY PARTITIONING & ZeRO-1/2/3 DYNAMIC COLLAPSE
# ==============================================================================
class Tap24Scene02Architecture(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "GIẢI PHẪU 16Phi BỘ NHỚ & ZeRO-1/2/3")

        scene_title = Text(
            "GIẢI PHẪU 16Phi BỘ NHỚ ADAMW & CƠ CHẾ NÉN ZeRO-1/2/3",
            font=DEFAULT_FONT, font_size=17.0, weight=BOLD, color=COLOR_GOLD
        )
        scene_title.to_edge(UP, buff=0.95)
        self.play(FadeIn(scene_title, shift=DOWN * 0.2), run_time=0.8)

        # Mathematical Decomposition of Mixed-Precision Training
        math_decomp = MathTex(
            r"M_{\text{total}} = \underbrace{2\Phi}_{\text{Weights}} + \underbrace{2\Phi}_{\text{Gradients}} + \underbrace{12\Phi}_{\text{AdamW}} = 16\Phi",
            font_size=23.0, color=COLOR_GOLD
        ).move_to(UP * 1.8)
        self.play(Write(math_decomp), run_time=1.2)

        # Left Side: Memory Stack Tower (Total = 16Phi = 1120 GB)
        stack_x = -3.8
        base_y = -1.9

        weight_rect = Rectangle(
            width=2.8, height=0.65,
            fill_color=COLOR_CYAN, fill_opacity=0.85, stroke_color=COLOR_TEXT, stroke_width=1.0
        ).move_to(np.array([stack_x, base_y + 0.325, 0.0]))
        weight_header = fit_math_to_card(
            r"\text{Weights } 2\Phi \ (140\,\text{GB})",
            weight_rect, font_size=16.0, color="#0c0d12", padding_x=0.15, padding_y=0.10
        )

        grad_rect = Rectangle(
            width=2.8, height=0.65,
            fill_color=COLOR_VIOLET, fill_opacity=0.85, stroke_color=COLOR_TEXT, stroke_width=1.0
        ).move_to(np.array([stack_x, base_y + 0.65 + 0.325, 0.0]))
        grad_header = fit_math_to_card(
            r"\text{Gradients } 2\Phi \ (140\,\text{GB})",
            grad_rect, font_size=16.0, color="#0c0d12", padding_x=0.15, padding_y=0.10
        )

        adam_rect = Rectangle(
            width=2.8, height=2.20,
            fill_color=COLOR_GOLD, fill_opacity=0.85, stroke_color=COLOR_TEXT, stroke_width=1.0
        ).move_to(np.array([stack_x, base_y + 1.30 + 1.10, 0.0]))
        adam_header = fit_math_to_card(
            r"\text{AdamW } 12\Phi \ (840\,\text{GB})",
            adam_rect, font_size=17.0, color="#0c0d12", padding_x=0.15, padding_y=0.15
        )

        stack_label_header = Text("BỘ NHỚ TĨNH 1 GPU: 1,120 GB", font=DEFAULT_FONT, font_size=12.5, weight=BOLD, color=COLOR_ROSE)
        stack_label_header.next_to(adam_rect, UP, buff=0.18)

        left_stack_grp = VGroup(
            weight_rect, weight_header, grad_rect, grad_header, adam_rect, adam_header, stack_label_header
        )
        self.play(FadeIn(left_stack_grp, shift=RIGHT * 0.3), run_time=1.2)

        # Right Side: ZeRO-1/2/3 Staged Collapsing HUD
        zero1_box = RoundedRectangle(
            corner_radius=0.12, width=5.8, height=0.85,
            fill_color=COLOR_PANEL, fill_opacity=0.9, stroke_color=COLOR_GOLD, stroke_width=1.4
        ).move_to(RIGHT * 2.8 + UP * 0.9)
        math_zero1 = fit_math_to_card(
            r"\text{ZeRO-1 } (P_{\text{os}}): \ M = 4\Phi + \frac{12\Phi}{N} \implies 293\,\text{GB} \ (4\times)",
            zero1_box, font_size=18.0, color=COLOR_GOLD, padding_x=0.20, padding_y=0.10
        )

        zero2_box = RoundedRectangle(
            corner_radius=0.12, width=5.8, height=0.85,
            fill_color=COLOR_PANEL, fill_opacity=0.9, stroke_color=COLOR_VIOLET, stroke_width=1.4
        ).move_to(RIGHT * 2.8 + DOWN * 0.05)
        math_zero2 = fit_math_to_card(
            r"\text{ZeRO-2 } (P_{\text{os+g}}): \ M = 2\Phi + \frac{14\Phi}{N} \implies 155\,\text{GB} \ (8\times)",
            zero2_box, font_size=18.0, color=COLOR_VIOLET, padding_x=0.20, padding_y=0.10
        )

        zero3_box = RoundedRectangle(
            corner_radius=0.12, width=5.8, height=0.85,
            fill_color=COLOR_PANEL, fill_opacity=0.9, stroke_color=COLOR_GREEN, stroke_width=1.5
        ).move_to(RIGHT * 2.8 + DOWN * 1.0)
        math_zero3 = fit_math_to_card(
            r"\text{ZeRO-3 / FSDP}: \ M = \frac{16\Phi}{N} \implies 17.5\,\text{GB} < 80\,\text{GB} \ (16\times)",
            zero3_box, font_size=18.0, color=COLOR_GREEN, padding_x=0.20, padding_y=0.10
        )

        # Stage 1 Collapse Animation: ZeRO-1
        arrow_z1 = Arrow(start=adam_rect.get_right(), end=zero1_box.get_left(), buff=0.15, color=COLOR_GOLD, tip_length=0.16)
        self.play(FadeIn(zero1_box), Write(math_zero1), GrowArrow(arrow_z1), run_time=1.0)

        # Stage 2 Collapse Animation: ZeRO-2
        arrow_z2 = Arrow(start=grad_rect.get_right(), end=zero2_box.get_left(), buff=0.15, color=COLOR_VIOLET, tip_length=0.16)
        self.play(FadeIn(zero2_box), Write(math_zero2), GrowArrow(arrow_z2), run_time=1.0)

        # Stage 3 Collapse Animation: ZeRO-3
        arrow_z3 = Arrow(start=weight_rect.get_right(), end=zero3_box.get_left(), buff=0.15, color=COLOR_GREEN, tip_length=0.16)
        self.play(FadeIn(zero3_box), Write(math_zero3), GrowArrow(arrow_z3), Flash(zero3_box, color=COLOR_GREEN), run_time=1.2)

        # Bottom Conclusion Badge
        callout_header = Text(
            "FSDP & ZeRO-3: NÉN 16 LẦN BỘ NHỚ — HUẤN LUYỆN 70B MƯỢT MÀ TRÊN GPU 80GB",
            font=DEFAULT_FONT, font_size=12.5, weight=BOLD, color=COLOR_GREEN
        )
        callout_box = SurroundingRectangle(
            callout_header, buff=0.15, stroke_color=COLOR_GREEN, stroke_width=1.2,
            fill_color=COLOR_PANEL, fill_opacity=0.9
        )
        callout_grp = VGroup(callout_box, callout_header).to_edge(DOWN, buff=0.45)
        self.play(FadeIn(callout_grp, shift=UP * 0.2), run_time=0.8)
        self.wait(1.5)


# ==============================================================================
# SCENE 3: MATHEMATICS — RING ALL-REDUCE BUCKET TOKEN CIRCULATION
# ==============================================================================
class Tap24Scene03Mathematics(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "RING ALL-REDUCE BĂNG THÔNG TỐI ƯU")

        scene_title = Text(
            "RING ALL-REDUCE: VÒNG TRÒN GIAO TIẾP TỐI ƯU BĂNG THÔNG",
            font=DEFAULT_FONT, font_size=17.0, weight=BOLD, color=COLOR_GOLD
        )
        scene_title.to_edge(UP, buff=0.95)
        self.play(FadeIn(scene_title, shift=DOWN * 0.2), run_time=0.8)

        # Ring All-Reduce Invariant Communication Volume Formula
        math_vol = MathTex(
            r"\text{Data Volume} = 2 \times \frac{N-1}{N} \times \Phi \approx 2\Phi",
            font_size=24.0, color=COLOR_GOLD
        ).move_to(UP * 2.45)
        self.play(Write(math_vol), run_time=1.0)

        # 6 GPU Nodes in Circular Topology (Radius = 2.1, Center = [0.0, -0.7, 0.0])
        ring_center = np.array([0.0, -0.7, 0.0])
        ring_radius = 2.1
        num_gpus = 6
        node_colors = [COLOR_CYAN, COLOR_GOLD, COLOR_VIOLET, COLOR_ROSE, COLOR_GREEN, "#38bdf8"]

        gpu_nodes = VGroup()
        node_centers = []

        for i in range(num_gpus):
            theta = i * TAU / num_gpus
            pos = ring_center + np.array([ring_radius * np.cos(theta), ring_radius * np.sin(theta), 0.0])
            node_centers.append(pos)

            outer_circle = Circle(
                radius=0.48, stroke_color=node_colors[i], stroke_width=2.0,
                fill_color=COLOR_PANEL, fill_opacity=0.9
            ).move_to(pos)
            inner_dot = Dot(pos, radius=0.08, color=node_colors[i])
            node_header = Text(f"GPU {i}", font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=node_colors[i])
            node_header.next_to(outer_circle.get_top(), DOWN, buff=0.12)
            gpu_nodes.add(VGroup(outer_circle, inner_dot, node_header))

        self.play(LaggedStart(*[FadeIn(n, scale=0.7) for n in gpu_nodes], lag_ratio=0.08), run_time=1.2)

        # Curved Ring Interconnect Arrows (tip_length=0.15 <= 0.20)
        ring_arrows = VGroup()
        for i in range(num_gpus):
            start_p = node_centers[i]
            end_p = node_centers[(i + 1) % num_gpus]
            # Tangent direction on circle
            t_mid = (i + 0.5) * TAU / num_gpus
            curved_arr = CurvedArrow(
                start_point=start_p + 0.50 * np.array([np.cos(i * TAU / num_gpus + 0.3), np.sin(i * TAU / num_gpus + 0.3), 0.0]),
                end_point=end_p + 0.50 * np.array([np.cos((i + 1) * TAU / num_gpus - 0.3), np.sin((i + 1) * TAU / num_gpus - 0.3), 0.0]),
                angle=-TAU / 12,
                color=COLOR_CYAN,
                stroke_width=2.0,
                tip_length=0.15
            )
            ring_arrows.add(curved_arr)

        self.play(Create(ring_arrows), run_time=1.2)

        # Two-Phase Bucket Circulation Animation
        # Phase 1: Scatter-Reduce token packets rotating around the ring
        phase1_header = Text(
            "GIAI ĐOẠN 1: SCATTER-REDUCE — TÍCH LŨY PHÂN MẢNH ĐẠO HÀM (N-1 BƯỚC)",
            font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_CYAN
        ).move_to(UP * 2.05)
        self.play(FadeIn(phase1_header), run_time=0.6)

        token_dots = VGroup(*[
            Dot(node_centers[i], radius=0.12, color=node_colors[i]) for i in range(num_gpus)
        ])
        self.play(FadeIn(token_dots), run_time=0.5)

        # Rotate tokens to adjacent nodes (Step 1 of Scatter-Reduce)
        self.play(
            *[token_dots[i].animate.move_to(node_centers[(i + 1) % num_gpus]) for i in range(num_gpus)],
            run_time=1.5
        )

        # Phase 2: All-Gather broadcast
        phase2_header = Text(
            "GIAI ĐOẠN 2: ALL-GATHER — ĐỒNG BỘ TOÀN BỘ TRỌNG SỐ TOÀN CỤC (N-1 BƯỚC)",
            font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_GREEN
        ).move_to(UP * 2.05)
        self.play(
            FadeOut(phase1_header),
            FadeIn(phase2_header),
            *[Flash(gpu_nodes[i][0], color=COLOR_GOLD) for i in range(num_gpus)],
            run_time=1.0
        )

        callout_header = Text(
            "NCCL RING: TẬN DỤNG 100% BĂNG THÔNG DÂY CÁP — KHÔNG CÓ GPU NGHẼN",
            font=DEFAULT_FONT, font_size=12.5, weight=BOLD, color=COLOR_CYAN
        )
        callout_box = SurroundingRectangle(
            callout_header, buff=0.15, stroke_color=COLOR_CYAN, stroke_width=1.2,
            fill_color=COLOR_PANEL, fill_opacity=0.9
        )
        callout_grp = VGroup(callout_box, callout_header).to_edge(DOWN, buff=0.20)
        self.play(FadeIn(callout_grp, shift=UP * 0.2), run_time=0.8)
        self.wait(1.5)


# ==============================================================================
# SCENE 4: TELEMETRY — MEGATRON-LM TENSOR PARALLELISM (XA -> YB)
# ==============================================================================
class Tap24Scene04Telemetry(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "TENSOR PARALLELISM & MEGATRON-LM")

        scene_title = Text(
            "MEGATRON-LM TENSOR PARALLELISM: TÁCH MA TRẬN 2 CHIỀU",
            font=DEFAULT_FONT, font_size=17.0, weight=BOLD, color=COLOR_GOLD
        )
        scene_title.to_edge(UP, buff=0.95)
        self.play(FadeIn(scene_title, shift=DOWN * 0.2), run_time=0.8)

        # Mathematical Formulation of Column + Row Parallel Megatron Block
        math_tp = MathTex(
            r"XA = [XA_1 \mid XA_2] \implies YB = Y_1 B_1 + Y_2 B_2 = XAB",
            font_size=23.0, color=COLOR_GOLD
        ).move_to(UP * 1.8)
        self.play(Write(math_tp), run_time=1.0)

        # Dual Rail Rails: Top Rail (GPU 0) and Bottom Rail (GPU 1)
        rail_y_top = 0.55
        rail_y_bot = -1.25

        gpu0_tag = Text("GPU 0 (Cột A1 // Hàng B1)", font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_CYAN).move_to(LEFT * 5.2 + UP * rail_y_top)
        gpu1_tag = Text("GPU 1 (Cột A2 // Hàng B2)", font=DEFAULT_FONT, font_size=12.0, weight=BOLD, color=COLOR_VIOLET).move_to(LEFT * 5.2 + UP * rail_y_bot)
        self.play(FadeIn(gpu0_tag), FadeIn(gpu1_tag), run_time=0.8)

        # Input Matrix X duplicated to both rails
        x0_box = RoundedRectangle(corner_radius=0.08, width=1.1, height=1.0, fill_color=COLOR_PANEL, fill_opacity=0.9, stroke_color=COLOR_CYAN, stroke_width=1.4).move_to(LEFT * 3.3 + UP * rail_y_top)
        x0_header = MathTex(r"X", font_size=20.0, color=COLOR_CYAN).move_to(x0_box.get_center())
        x1_box = RoundedRectangle(corner_radius=0.08, width=1.1, height=1.0, fill_color=COLOR_PANEL, fill_opacity=0.9, stroke_color=COLOR_VIOLET, stroke_width=1.4).move_to(LEFT * 3.3 + UP * rail_y_bot)
        x1_header = MathTex(r"X", font_size=20.0, color=COLOR_VIOLET).move_to(x1_box.get_center())

        # Column Parallel Weights A1, A2
        a0_box = RoundedRectangle(corner_radius=0.08, width=1.1, height=1.0, fill_color=COLOR_PANEL, fill_opacity=0.9, stroke_color=COLOR_GOLD, stroke_width=1.4).move_to(LEFT * 1.5 + UP * rail_y_top)
        a0_header = MathTex(r"A_1", font_size=20.0, color=COLOR_GOLD).move_to(a0_box.get_center())
        a1_box = RoundedRectangle(corner_radius=0.08, width=1.1, height=1.0, fill_color=COLOR_PANEL, fill_opacity=0.9, stroke_color=COLOR_GOLD, stroke_width=1.4).move_to(LEFT * 1.5 + UP * rail_y_bot)
        a1_header = MathTex(r"A_2", font_size=20.0, color=COLOR_GOLD).move_to(a1_box.get_center())

        # Row Parallel Weights B1, B2
        b0_box = RoundedRectangle(corner_radius=0.08, width=1.1, height=1.0, fill_color=COLOR_PANEL, fill_opacity=0.9, stroke_color=COLOR_ROSE, stroke_width=1.4).move_to(RIGHT * 0.3 + UP * rail_y_top)
        b0_header = MathTex(r"B_1", font_size=20.0, color=COLOR_ROSE).move_to(b0_box.get_center())
        b1_box = RoundedRectangle(corner_radius=0.08, width=1.1, height=1.0, fill_color=COLOR_PANEL, fill_opacity=0.9, stroke_color=COLOR_ROSE, stroke_width=1.4).move_to(RIGHT * 0.3 + UP * rail_y_bot)
        b1_header = MathTex(r"B_2", font_size=20.0, color=COLOR_ROSE).move_to(b1_box.get_center())

        # Forward arrows between blocks
        arr_x_a0 = Arrow(start=x0_box.get_right(), end=a0_box.get_left(), buff=0.1, color=COLOR_TEXT, tip_length=0.15)
        arr_x_a1 = Arrow(start=x1_box.get_right(), end=a1_box.get_left(), buff=0.1, color=COLOR_TEXT, tip_length=0.15)
        arr_a_b0 = Arrow(start=a0_box.get_right(), end=b0_box.get_left(), buff=0.1, color=COLOR_TEXT, tip_length=0.15)
        arr_a_b1 = Arrow(start=a1_box.get_right(), end=b1_box.get_left(), buff=0.1, color=COLOR_TEXT, tip_length=0.15)

        rail_blocks = VGroup(
            x0_box, x0_header, x1_box, x1_header,
            a0_box, a0_header, a1_box, a1_header,
            b0_box, b0_header, b1_box, b1_header,
            arr_x_a0, arr_x_a1, arr_a_b0, arr_a_b1
        )
        self.play(FadeIn(rail_blocks), run_time=1.5)

        # Single All-Reduce Summation Node Convergence
        sum_node = Circle(
            radius=0.55, stroke_color=COLOR_GOLD, stroke_width=2.0,
            fill_color=COLOR_PANEL, fill_opacity=0.9
        ).move_to(RIGHT * 2.5 + DOWN * 0.35)
        sum_math = MathTex(r"\sum", font_size=28.0, color=COLOR_GOLD).move_to(sum_node.get_center())

        conv_arr0 = Arrow(start=b0_box.get_right(), end=sum_node.get_left() + UP * 0.2, buff=0.12, color=COLOR_GOLD, tip_length=0.15)
        conv_arr1 = Arrow(start=b1_box.get_right(), end=sum_node.get_left() + DOWN * 0.2, buff=0.12, color=COLOR_GOLD, tip_length=0.15)

        # Final Reconstructed Output Matrix Z
        z_box = RoundedRectangle(
            corner_radius=0.08, width=1.5, height=1.1,
            fill_color=COLOR_PANEL, fill_opacity=0.9, stroke_color=COLOR_GREEN, stroke_width=1.6
        ).move_to(RIGHT * 4.6 + DOWN * 0.35)
        z_header = fit_math_to_card(r"Z = XAB", z_box, font_size=19.0, color=COLOR_GREEN, padding_x=0.15, padding_y=0.15)
        arr_sum_z = Arrow(start=sum_node.get_right(), end=z_box.get_left(), buff=0.12, color=COLOR_GREEN, tip_length=0.15)

        self.play(
            GrowArrow(conv_arr0), GrowArrow(conv_arr1),
            FadeIn(sum_node), Write(sum_math),
            run_time=1.0
        )
        self.play(
            GrowArrow(arr_sum_z), FadeIn(z_box), Write(z_header),
            Flash(z_box, color=COLOR_GREEN),
            run_time=1.0
        )

        callout_header = Text(
            "1 LẦN ALL-REDUCE DUY NHẤT CHO MỖI KHỐI TRANSFORMER MLP",
            font=DEFAULT_FONT, font_size=12.5, weight=BOLD, color=COLOR_CYAN
        )
        callout_box = SurroundingRectangle(
            callout_header, buff=0.15, stroke_color=COLOR_CYAN, stroke_width=1.2,
            fill_color=COLOR_PANEL, fill_opacity=0.9
        )
        callout_grp = VGroup(callout_box, callout_header).to_edge(DOWN, buff=0.45)
        self.play(FadeIn(callout_grp, shift=UP * 0.2), run_time=0.8)
        self.wait(1.5)


# ==============================================================================
# SCENE 5: LAB EXPERIMENT — PIPELINE PARALLELISM & 1F1B SCHEDULE TIMELINE
# ==============================================================================
class Tap24Scene05LabExperiment(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "PIPELINE PARALLELISM & 1F1B")

        scene_title = Text(
            "PIPELINE PARALLELISM: ĐIỀU PHỐI 1F1B TRIỆT TIÊU BONG BÓNG TRỄ",
            font=DEFAULT_FONT, font_size=16.5, weight=BOLD, color=COLOR_GOLD
        )
        scene_title.to_edge(UP, buff=0.95)
        self.play(FadeIn(scene_title, shift=DOWN * 0.2), run_time=0.8)

        # Bubble Fraction Formula
        math_bubble = MathTex(
            r"\text{Bubble Fraction} = \frac{p - 1}{m + p - 1} \xrightarrow{m \gg p} 0 \quad (p=\text{Stages}, \ m=\text{Micro-batches})",
            font_size=20.0, color=COLOR_GOLD
        ).move_to(UP * 1.8)
        self.play(Write(math_bubble), run_time=1.0)

        # 4 Pipeline Stages on Vertical Axis
        stages_y = [1.0, 0.3, -0.4, -1.1]
        stage_names = ["Stage 0 (GPU 0)", "Stage 1 (GPU 1)", "Stage 2 (GPU 2)", "Stage 3 (GPU 3)"]
        stage_labels = VGroup()

        for idx, (y_val, name) in enumerate(zip(stages_y, stage_names)):
            lbl_header = Text(name, font=DEFAULT_FONT, font_size=12.0, color=COLOR_TEXT).move_to(LEFT * 4.6 + UP * y_val)
            stage_labels.add(lbl_header)

        self.play(FadeIn(stage_labels), run_time=0.8)

        # 1F1B Schedule Gantt Blocks (Forward in Cyan, Backward in Rose)
        schedule_blocks = VGroup()
        time_origin_x = -2.8
        block_w = 0.85
        block_h = 0.52

        # 1F1B Interlocking sequence coordinates: (stage_idx, time_step, is_forward, step_id)
        f_and_b = [
            # Stage 0: F1, F2, F3, F4, then B1, B2, B3, B4
            (0, 0, True, 1), (0, 1, True, 2), (0, 2, True, 3), (0, 3, True, 4),
            (0, 5, False, 1), (0, 6, False, 2), (0, 7, False, 3), (0, 8, False, 4),
            # Stage 1: F1, F2, F3, F4, then B1, B2, B3, B4
            (1, 1, True, 1), (1, 2, True, 2), (1, 3, True, 3), (1, 4, True, 4),
            (1, 6, False, 1), (1, 7, False, 2), (1, 8, False, 3), (1, 9, False, 4),
            # Stage 2:
            (2, 2, True, 1), (2, 3, True, 2), (2, 4, True, 3), (2, 5, True, 4),
            (2, 7, False, 1), (2, 8, False, 2), (2, 9, False, 3), (2, 10, False, 4),
            # Stage 3: Immediate 1F1B turnaround
            (3, 3, True, 1), (3, 4, False, 1), (3, 5, True, 2), (3, 6, False, 2),
            (3, 7, True, 3), (3, 8, False, 3), (3, 9, True, 4), (3, 10, False, 4)
        ]

        for stg, t_slot, is_fwd, micro_id in f_and_b:
            pos_x = time_origin_x + t_slot * 0.72
            pos_y = stages_y[stg]
            b_col = COLOR_CYAN if is_fwd else COLOR_ROSE
            lbl_str = f"F{micro_id}" if is_fwd else f"B{micro_id}"

            r_block = RoundedRectangle(
                corner_radius=0.06, width=block_w * 0.76, height=block_h,
                fill_color=COLOR_PANEL, fill_opacity=0.9, stroke_color=b_col, stroke_width=1.2
            ).move_to(np.array([pos_x, pos_y, 0.0]))
            t_math = fit_math_to_card(lbl_str, r_block, font_size=15.0, color=b_col, padding_x=0.06, padding_y=0.06)
            schedule_blocks.add(VGroup(r_block, t_math))

        self.play(LaggedStart(*[FadeIn(b, scale=0.8) for b in schedule_blocks], lag_ratio=0.03), run_time=2.2)

        # Bubble Overhead Comparison Callout
        callout_header = Text(
            "1F1B INTERLOCKING: BỘ NHỚ ACTIVATIONS GIẢM TỪ O(m) VỀ O(p) — BUBBLE < 10%",
            font=DEFAULT_FONT, font_size=12.5, weight=BOLD, color=COLOR_GREEN
        )
        callout_box = SurroundingRectangle(
            callout_header, buff=0.15, stroke_color=COLOR_GREEN, stroke_width=1.2,
            fill_color=COLOR_PANEL, fill_opacity=0.9
        )
        callout_grp = VGroup(callout_box, callout_header).to_edge(DOWN, buff=0.45)
        self.play(FadeIn(callout_grp, shift=UP * 0.2), run_time=0.8)
        self.wait(1.5)


# ==============================================================================
# SCENE 6: OUTRO — 5x5 THUMBNAIL MOSAIC & YOUTUBE SAFE ZONE CLOSING CTA
# ==============================================================================
class Tap24Scene06Outro(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "KHÉP LẠI TẬP 24 // CHÀO ĐÓN ĐẠI KẾT AGI")

        scene_title = Text(
            "TẬP 24 // DISTRIBUTED TRAINING: NỀN TẢNG ĐỘT PHÁ SIÊU MÔ HÌNH",
            font=DEFAULT_FONT, font_size=16.5, weight=BOLD, color=COLOR_GOLD
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
        # 1. Next Video Card (Episode 25): X in [+1.6, +5.4], Y in [+0.5, +2.5]
        next_card = RoundedRectangle(
            corner_radius=0.12, width=3.8, height=2.0,
            fill_color=COLOR_PANEL, fill_opacity=0.7, stroke_color=COLOR_CYAN, stroke_width=1.5
        ).move_to(RIGHT * 3.5 + UP * 1.5)
        next_header = Text("TẬP TIẾP THEO // TẬP 25", font=DEFAULT_FONT, font_size=12.5, weight=BOLD, color=COLOR_CYAN)
        next_sub_header = Text("TƯƠNG LAI KỸ NGHỆ LLM: AGI & PHYSICAL AI", font=DEFAULT_FONT, font_size=12.0, color=COLOR_TEXT).next_to(next_header, DOWN, buff=0.18)
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

        # Bottom Bridge Announcement to Episode 25 Grand Finale
        teaser_header = Text(
            "HƯỚNG TỚI TẬP 25: ĐẠI KẾT SERIES 2 — BỨC TRANH TOÀN CẢNH AGI 2030",
            font=DEFAULT_FONT, font_size=12.5, weight=BOLD, color=COLOR_CYAN
        )
        teaser_header.to_edge(DOWN, buff=0.45)
        self.play(FadeIn(teaser_header, shift=UP * 0.2), run_time=0.8)
        self.wait(2.0)
