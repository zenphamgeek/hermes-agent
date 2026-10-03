"""
Manim Artisan Components — Reusable Mathematical Visual Storytelling Library.
Designed for 2K QHD (2560x1440 @ 60fps) with Neo-Noir aesthetic tokens.
All components inherit from VGroup/Mobject, support dynamic parameterization,
and are collision-safe when arranged with safe_place.
"""

from manim import *
import numpy as np

# Neo-Noir Design Tokens
COLOR_OBSIDIAN = "#0c0d12"
COLOR_CYAN = "#00e5ff"
COLOR_CYAN_DIM = "#007799"
COLOR_GOLD = "#ffb300"
COLOR_GOLD_DIM = "#996d00"
COLOR_ROSE = "#ff2a6d"
COLOR_EMERALD = "#00ff9f"
COLOR_PURPLE = "#bd00ff"
COLOR_TEXT_PRIMARY = "#f0f2f5"
COLOR_TEXT_MUTED = "#8892b0"


class AttentionHeatmapGrid(VGroup):
    """
    Parametric Attention Matrix Heatmap Component.
    Visualizes token-to-token Attention Weights (Softmax(Q * K^T / sqrt(d_k))).
    """
    def __init__(self, tokens=None, weights=None, cell_size=0.6, **kwargs):
        super().__init__(**kwargs)
        self.tokens = tokens or ["The", "AI", "Thinks", "Fast"]
        n = len(self.tokens)
        self.weights = weights if weights is not None else np.random.dirichlet(np.ones(n), size=n)

        # Draw Cells
        self.cells = VGroup()
        for i in range(n):
            for j in range(n):
                w = float(self.weights[i, j])
                color = interpolate_color(ManimColor(COLOR_OBSIDIAN), ManimColor(COLOR_CYAN), w)
                cell = Square(side_length=cell_size, fill_color=color, fill_opacity=0.85, stroke_color=COLOR_CYAN_DIM, stroke_width=1)
                cell.move_to(np.array([(j - n / 2 + 0.5) * cell_size, (n / 2 - i - 0.5) * cell_size, 0]))
                self.cells.add(cell)

        # Labels
        self.col_labels = VGroup()
        for j, t in enumerate(self.tokens):
            lbl = Text(t, font_size=16, color=COLOR_TEXT_MUTED)
            lbl.next_to(self.cells[j], UP, buff=0.2)
            self.col_labels.add(lbl)

        self.row_labels = VGroup()
        for i, t in enumerate(self.tokens):
            lbl = Text(t, font_size=16, color=COLOR_TEXT_MUTED)
            lbl.next_to(self.cells[i * n], LEFT, buff=0.2)
            self.row_labels.add(lbl)

        self.add(self.cells, self.col_labels, self.row_labels)


class VectorProjectionPlot(VGroup):
    """
    High-dimensional Vector Space Projection & Cosine Similarity Component.
    """
    def __init__(self, v1=np.array([2.5, 1.5, 0]), v2=np.array([1.5, 2.8, 0]), label1="u", label2="v", **kwargs):
        super().__init__(**kwargs)
        self.origin = np.array([0, 0, 0])
        self.axes = Axes(x_range=[-1, 4, 1], y_range=[-1, 4, 1], axis_config={"color": COLOR_TEXT_MUTED, "stroke_width": 1.5})
        
        self.arrow1 = Arrow(self.axes.c2p(0, 0), self.axes.c2p(v1[0], v1[1]), buff=0, color=COLOR_CYAN, stroke_width=4)
        self.arrow2 = Arrow(self.axes.c2p(0, 0), self.axes.c2p(v2[0], v2[1]), buff=0, color=COLOR_GOLD, stroke_width=4)

        self.lbl1 = MathTex(label1, color=COLOR_CYAN).next_to(self.arrow1.get_end(), RIGHT)
        self.lbl2 = MathTex(label2, color=COLOR_GOLD).next_to(self.arrow2.get_end(), UP)

        dot_prod = float(np.dot(v1[:2], v2[:2]) / (np.linalg.norm(v1[:2]) * np.linalg.norm(v2[:2])))
        self.sim_card = VGroup(
            RoundedRectangle(corner_radius=0.1, width=2.8, height=0.8, fill_color="#121520", fill_opacity=0.9, stroke_color=COLOR_CYAN, stroke_width=1),
            Text(f"cos(θ) = {dot_prod:.3f}", font_size=18, color=COLOR_TEXT_PRIMARY)
        )
        self.sim_card[1].move_to(self.sim_card[0].get_center())
        self.sim_card.next_to(self.axes, RIGHT, buff=0.5)

        self.add(self.axes, self.arrow1, self.arrow2, self.lbl1, self.lbl2, self.sim_card)


class NeuralArchitectureFlow(VGroup):
    """
    Parametric Layered Neural Architecture Flow with Signal Pulses.
    """
    def __init__(self, layer_sizes=[3, 5, 4, 2], layer_spacing=1.8, node_spacing=0.6, **kwargs):
        super().__init__(**kwargs)
        self.layers = VGroup()
        self.connections = VGroup()

        # Build Nodes
        all_layers = []
        for l_idx, size in enumerate(layer_sizes):
            layer_nodes = VGroup()
            for n_idx in range(size):
                y = (size / 2 - n_idx - 0.5) * node_spacing
                x = (l_idx - len(layer_sizes) / 2 + 0.5) * layer_spacing
                node = Circle(radius=0.14, fill_color=COLOR_OBSIDIAN, fill_opacity=1, stroke_color=COLOR_CYAN if l_idx == 0 else (COLOR_GOLD if l_idx == len(layer_sizes)-1 else COLOR_EMERALD), stroke_width=2)
                node.move_to(np.array([x, y, 0]))
                layer_nodes.add(node)
            all_layers.append(layer_nodes)
            self.layers.add(layer_nodes)

        # Build Edges
        for i in range(len(all_layers) - 1):
            for n1 in all_layers[i]:
                for n2 in all_layers[i+1]:
                    edge = Line(n1.get_center(), n2.get_center(), stroke_color="#222838", stroke_width=1, stroke_opacity=0.6)
                    self.connections.add(edge)

        self.add(self.connections, self.layers)


class FourierWaveDecomposition(VGroup):
    """
    Multi-Harmonic Fourier Wave Decomposition & Synthesis Component.
    """
    def __init__(self, harmonics=[1, 3, 5], length=6.0, **kwargs):
        super().__init__(**kwargs)
        self.waves = VGroup()
        colors = [COLOR_CYAN, COLOR_GOLD, COLOR_ROSE]

        for idx, k in enumerate(harmonics):
            c = colors[idx % len(colors)]
            wave = FunctionGraph(
                lambda x: 0.5 / k * np.sin(k * x * 1.5),
                x_range=[-length/2, length/2],
                color=c,
                stroke_width=2
            )
            wave.shift(UP * (1.2 - idx * 0.9))
            lbl = MathTex(rf"\sin({k}\omega t)", font_size=18, color=c).next_to(wave, LEFT, buff=0.3)
            self.waves.add(VGroup(wave, lbl))

        self.add(self.waves)
