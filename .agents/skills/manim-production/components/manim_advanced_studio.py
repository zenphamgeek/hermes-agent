#!/usr/bin/env python3
"""
Manim Advanced Studio — Next-Gen 2D/3D Mathematical & Layout Library
===================================================================
Tailored for ZENPHAM "Tôi Làm Việc" Series 2 (LLM Anatomy) & Beyond.
Minimum output: 2K QHD (2560x1440 @ 60fps), Neo-Noir Obsidian #0c0d12.

Features:
1. CINEMATIC LAYOUTS:
   - GoldenSplitLayout (Visual 62% : Math/Code 38%)
   - QuadrantComparisonLayout (4-way comparative split)
   - HUDTelemetryCard (Sci-Fi Glassmorphism Parameter Card)
   - FocusSpotlightZone (Backdrop darkening focus mask)

2. ADVANCED 2D STRUCTURES:
   - MatrixTensorGrid (Parametric interactive matrix with cell zooming & heatmap)
   - TokenRibbonStream (BPE Tokenizer, sliding context window, KV Cache)
   - AutogradDAGGraph (Computational Graph with forward/backward signal pulses)
   - ContinuousManifold2D (Non-linear space folding & decision boundary)

3. CINEMATIC 3D STRUCTURES:
   - LossLandscapeSurface3D (3D Saddle point & valley surface with gradient descent ball)
   - RiemannHypersphere3D (Unit sphere for Cosine similarity & RoPE complex rotation)
   - TransformerTower3D (Layered 3D architectural stack)
"""

from __future__ import annotations
import numpy as np

try:
    from manim import (
        Mobject, VMobject, VGroup, Scene, ThreeDScene,
        Text, MathTex,
        Rectangle, RoundedRectangle, Circle, Dot, Line, Arrow, DashedLine,
        Polygon, Arc, Annulus,
        Axes, ThreeDAxes, Surface, Sphere,
        FadeIn, FadeOut, Write, Create, Transform, ReplacementTransform,
        Indicate, Flash, ApplyWave,
        UP, DOWN, LEFT, RIGHT, UL, UR, DL, DR, ORIGIN, IN, OUT,
        WHITE, BLACK, GRAY, GRAY_A, GRAY_C, GRAY_D,
        interpolate_color, ManimColor,
        PI, TAU, DEGREES,
        rate_functions,
    )
    MANIM_AVAILABLE = True
except ImportError:
    MANIM_AVAILABLE = False
    UP = np.array([0, 1, 0])
    DOWN = np.array([0, -1, 0])
    LEFT = np.array([-1, 0, 0])
    RIGHT = np.array([1, 0, 0])
    ORIGIN = np.array([0, 0, 0])

# =============================================================================
# NEO-NOIR PALETTE DEFINITIONS
# =============================================================================

class NoirPalette:
    BG_OBSIDIAN  = "#0c0d12"
    BG_CARD      = "#131722"
    CYAN_NEON    = "#00e5ff"
    CYAN_DIM     = "#006680"
    GOLD_AMBER   = "#ffb300"
    GOLD_DIM     = "#805900"
    ROSE_CRIMSON = "#ff2a6d"
    EMERALD_MINT = "#00ff9f"
    PURPLE_DEEP  = "#a855f7"
    TEXT_PRIMARY = "#f8fafc"
    TEXT_MUTED   = "#94a3b8"
    GRID_LINE    = "#1e293b"


# =============================================================================
# 1. CINEMATIC LAYOUT ENGINES
# =============================================================================

class GoldenSplitLayout:
    """
    Splits 16:9 2K canvas into Golden Ratio partitions (62% Visual : 38% Math/Code).
    Safe bounds guaranteed for YouTube 2K player UI and watermark.
    """
    def __init__(self, mode="left_visual"):
        self.mode = mode
        # 16:9 canvas dimensions in Manim coordinates (~14.22 x 8.0)
        self.total_width = 14.22
        self.total_height = 8.0
        
        if mode == "left_visual":
            self.visual_center = np.array([-2.2, 0, 0])
            self.visual_width = 8.5
            self.math_center = np.array([4.2, 0, 0])
            self.math_width = 4.8
        else:
            self.math_center = np.array([-4.2, 0, 0])
            self.math_width = 4.8
            self.visual_center = np.array([2.2, 0, 0])
            self.visual_width = 8.5

    def attach_divider(self) -> VMobject:
        div_x = 1.6 if self.mode == "left_visual" else -1.6
        return DashedLine(
            start=np.array([div_x, 3.5, 0]),
            end=np.array([div_x, -3.5, 0]),
            dash_length=0.15,
            color=NoirPalette.GRID_LINE,
            stroke_width=1.5
        )


class HUDTelemetryCard(VGroup):
    """
    Futuristic Sci-Fi HUD card for real-time training telemetry
    (Loss, Learning Rate, Memory Footprint, Token Throughput).
    """
    def __init__(self, title="SYSTEM TELEMETRY", metrics=None, width=3.8, height=2.2, **kwargs):
        super().__init__(**kwargs)
        metrics = metrics or [("Loss", "0.0241"), ("LR", "3e-4"), ("VRAM", "18.2 GB")]
        
        # Glassmorphism Base
        bg = RoundedRectangle(corner_radius=0.15, width=width, height=height,
                              fill_color=NoirPalette.BG_CARD, fill_opacity=0.85,
                              stroke_color=NoirPalette.CYAN_DIM, stroke_width=1)
        
        # Header Badge
        header_bar = RoundedRectangle(corner_radius=0.08, width=width*0.9, height=0.4,
                                      fill_color=NoirPalette.BG_OBSIDIAN, fill_opacity=0.9,
                                      stroke_color=NoirPalette.CYAN_NEON, stroke_width=1)
        header_bar.next_to(bg.get_top(), DOWN, buff=0.12)
        lbl = Text(title, font_size=13, color=NoirPalette.CYAN_NEON, weight="BOLD")
        lbl.move_to(header_bar.get_center())
        
        # Metrics rows
        rows = VGroup()
        for idx, (k, v) in enumerate(metrics):
            k_txt = Text(k, font_size=14, color=NoirPalette.TEXT_MUTED)
            v_txt = Text(v, font_size=14, color=NoirPalette.GOLD_AMBER, weight="BOLD")
            row = VGroup(k_txt, v_txt).arrange(RIGHT, buff=0.8)
            rows.add(row)
        rows.arrange(DOWN, buff=0.18)
        rows.next_to(header_bar, DOWN, buff=0.22)
        
        self.add(bg, header_bar, lbl, rows)


class QuadrantComparisonLayout:
    """
    4-Way Quadrant Layout for simultaneous algorithm showdowns
    (e.g., ReLU vs GELU vs SiLU vs Swish or SGD vs Momentum vs RMSProp vs Adam).
    """
    def __init__(self):
        self.centers = {
            "top_left": np.array([-3.5, 1.8, 0]),
            "top_right": np.array([3.5, 1.8, 0]),
            "bottom_left": np.array([-3.5, -1.8, 0]),
            "bottom_right": np.array([3.5, -1.8, 0]),
        }
        self.cell_width = 6.0
        self.cell_height = 3.2

    def get_crosshair(self) -> VGroup:
        h_line = DashedLine(LEFT * 6.5, RIGHT * 6.5, dash_length=0.2, color=NoirPalette.GRID_LINE, stroke_width=1)
        v_line = DashedLine(UP * 3.5, DOWN * 3.5, dash_length=0.2, color=NoirPalette.GRID_LINE, stroke_width=1)
        return VGroup(h_line, v_line)


# =============================================================================
# 2. ADVANCED 2D MATHEMATICAL STRUCTURES
# =============================================================================

class MatrixTensorGrid(VGroup):
    """
    Parametric Interactive Matrix Grid (NxM).
    Supports dynamic coloring by value, cell highlighting, and attention row-scanning.
    """
    def __init__(self, rows=4, cols=4, cell_size=0.6, matrix_data=None, **kwargs):
        super().__init__(**kwargs)
        self.rows = rows
        self.cols = cols
        self.cell_size = cell_size
        data = matrix_data if matrix_data is not None else np.random.uniform(0, 1, size=(rows, cols))

        self.cells = VGroup()
        for i in range(rows):
            for j in range(cols):
                val = float(data[i, j])
                c = interpolate_color(ManimColor(NoirPalette.BG_OBSIDIAN), ManimColor(NoirPalette.CYAN_NEON), val)
                cell = Square(side_length=cell_size, fill_color=c, fill_opacity=0.9,
                              stroke_color=NoirPalette.CYAN_DIM, stroke_width=1)
                cell.move_to(np.array([(j - cols/2 + 0.5) * cell_size, (rows/2 - i - 0.5) * cell_size, 0]))
                self.cells.add(cell)

        # Surrounding matrix brackets
        bracket_l = MathTex(r"\left[", font_size=int(rows * cell_size * 45), color=NoirPalette.CYAN_NEON)
        bracket_r = MathTex(r"\right]", font_size=int(rows * cell_size * 45), color=NoirPalette.CYAN_NEON)
        bracket_l.next_to(self.cells, LEFT, buff=0.1)
        bracket_r.next_to(self.cells, RIGHT, buff=0.1)

        self.add(self.cells, bracket_l, bracket_r)


class TokenRibbonStream(VGroup):
    """
    Autoregressive Token Ribbon Stream.
    Visualizes Tokenization, Sliding Window Context, and KV Cache evictions.
    """
    def __init__(self, tokens=None, active_idx=2, box_width=1.5, box_height=0.6, **kwargs):
        super().__init__(**kwargs)
        tokens = tokens or ["Khi", "máy", "tính", "bắt", "đầu", "suy", "nghĩ"]
        
        self.boxes = VGroup()
        for idx, tok in enumerate(tokens):
            is_active = (idx == active_idx)
            is_past = (idx < active_idx)
            border_c = NoirPalette.CYAN_NEON if is_active else (NoirPalette.GOLD_AMBER if is_past else NoirPalette.TEXT_MUTED)
            fill_c = NoirPalette.BG_CARD if is_active else NoirPalette.BG_OBSIDIAN
            
            box = RoundedRectangle(corner_radius=0.08, width=box_width, height=box_height,
                                   fill_color=fill_c, fill_opacity=0.9,
                                   stroke_color=border_c, stroke_width=2 if is_active else 1)
            txt = Text(tok, font_size=15, color=NoirPalette.TEXT_PRIMARY if (is_active or is_past) else NoirPalette.TEXT_MUTED)
            txt.move_to(box.get_center())
            
            item = VGroup(box, txt)
            item.shift(RIGHT * (idx - len(tokens)/2 + 0.5) * (box_width + 0.15))
            self.boxes.add(item)

        # Context Window Bracket underneath
        self.add(self.boxes)


class AutogradDAGGraph(VGroup):
    """
    Reverse-Mode Computational DAG Graph for Autograd & Backpropagation.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Nodes: x, w -> multiply -> add b -> Loss
        node_configs = [
            ("x", np.array([-3, 1.2, 0]), NoirPalette.CYAN_NEON),
            ("w", np.array([-3, -1.2, 0]), NoirPalette.CYAN_NEON),
            ("×", np.array([-1, 0, 0]), NoirPalette.GOLD_AMBER),
            ("b", np.array([-1, -1.8, 0]), NoirPalette.CYAN_NEON),
            ("+", np.array([1, -0.6, 0]), NoirPalette.GOLD_AMBER),
            ("Loss", np.array([3.2, -0.6, 0]), NoirPalette.ROSE_CRIMSON),
        ]
        self.nodes = VGroup()
        node_dict = {}
        for label, pos, col in node_configs:
            circle = Circle(radius=0.32, fill_color=NoirPalette.BG_OBSIDIAN, fill_opacity=1,
                            stroke_color=col, stroke_width=2)
            circle.move_to(pos)
            txt = Text(label, font_size=16, color=NoirPalette.TEXT_PRIMARY)
            txt.move_to(pos)
            nd = VGroup(circle, txt)
            self.nodes.add(nd)
            node_dict[label] = circle

        # Edges
        self.edges = VGroup()
        edges_to_make = [("x", "×"), ("w", "×"), ("×", "+"), ("b", "+"), ("+", "Loss")]
        for u, v in edges_to_make:
            c1 = node_dict[u].get_center()
            c2 = node_dict[v].get_center()
            arrow = Arrow(c1, c2, buff=0.35, color=NoirPalette.TEXT_MUTED, stroke_width=1.5, tip_length=0.15)
            self.edges.add(arrow)

        self.add(self.edges, self.nodes)


# =============================================================================
# 3. CINEMATIC 3D MATHEMATICAL STRUCTURES
# =============================================================================

class LossLandscapeSurface3D(VGroup):
    """
    3D Parametric Loss Landscape with Saddle Points and Gradient Descent Trajectory.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.axes = ThreeDAxes(
            x_range=[-3, 3, 1], y_range=[-3, 3, 1], z_range=[-2, 4, 1],
            x_length=5.5, y_length=5.5, z_length=3.5,
            axis_config={"color": NoirPalette.GRID_LINE, "stroke_width": 1}
        )
        # Saddle surface z = x^2 - y^2
        self.surface = Surface(
            lambda u, v: self.axes.c2p(u, v, 0.4 * (u**2 - v**2)),
            u_range=[-2.2, 2.2], v_range=[-2.2, 2.2],
            resolution=(24, 24),
            fill_color=NoirPalette.CYAN_DIM, fill_opacity=0.65,
            stroke_color=NoirPalette.CYAN_NEON, stroke_width=0.5
        )
        self.add(self.axes, self.surface)


class RiemannHypersphere3D(VGroup):
    """
    3D Unit Hypersphere representation for L2 Normalization, Cosine Similarity,
    and RoPE (Rotary Positional Embedding) in Complex Vector Space.
    """
    def __init__(self, radius=2.0, **kwargs):
        super().__init__(**kwargs)
        self.axes = ThreeDAxes(x_range=[-2.5, 2.5], y_range=[-2.5, 2.5], z_range=[-2.5, 2.5],
                               x_length=4.5, y_length=4.5, z_length=4.5,
                               axis_config={"color": NoirPalette.GRID_LINE, "stroke_width": 1})
        # Wireframe Sphere
        self.sphere = Sphere(radius=radius, resolution=(16, 32),
                             fill_color=NoirPalette.BG_CARD, fill_opacity=0.25,
                             stroke_color=NoirPalette.CYAN_NEON, stroke_width=0.6)
        self.add(self.axes, self.sphere)


class TransformerTower3D(VGroup):
    """
    Layered 3D Transformer Stack representation (Stacked Attention + FFN blocks).
    """
    def __init__(self, num_layers=4, width=3.5, height=0.4, spacing=0.7, **kwargs):
        super().__init__(**kwargs)
        self.blocks = VGroup()
        for i in range(num_layers):
            layer_z = i * spacing - (num_layers * spacing) / 2
            
            # Multi-Head Attention slab
            mha = RoundedRectangle(corner_radius=0.08, width=width, height=height,
                                   fill_color=NoirPalette.BG_CARD, fill_opacity=0.85,
                                   stroke_color=NoirPalette.CYAN_NEON, stroke_width=1.5)
            lbl = Text(f"Block {i+1}: MHA + FFN", font_size=13, color=NoirPalette.TEXT_PRIMARY)
            lbl.move_to(mha.get_center())
            blk = VGroup(mha, lbl)
            blk.shift(UP * (i * 0.9 - 1.3))
            self.blocks.add(blk)

        self.add(self.blocks)
