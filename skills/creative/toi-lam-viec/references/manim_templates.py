#!/usr/bin/env python3
"""
Manim Math & Architecture Animation Templates for 'Tôi Làm Việc' Series
======================================================================
Pre-built 1080p 16:9 minimalist scenes following Median / 3Blue1Brown aesthetics:
- Dark Neo-noir background (#0d0e15)
- Cyan (#00f0ff) & Amber (#f59e0b) vibrant data points
- Pango text for complete Vietnamese Unicode accent support
- MathTex for LaTeX mathematical formulas
"""

from manim import *
import numpy as np

# Palette Constants
BG_COLOR = "#0c0d14"
CYAN = "#00f0ff"
AMBER = "#f59e0b"
EMERALD = "#10b981"
CRIMSON = "#ef4444"
SOFT_WHITE = "#f1f5f9"
MUTED_GRAY = "#64748b"


class LossLandscapeScene(Scene):
    """Visualizes Gradient Descent minimizing a non-convex Loss Function."""

    def construct(self):
        self.camera.background_color = BG_COLOR

        # Title
        title = Text("HÀM MẤT MÁT & GRADIENT DESCENT", font="sans-serif", font_size=36, color=CYAN, weight=BOLD)
        title.to_edge(UP, buff=0.8)
        subtitle = Text("Học tập là hành trình thu hẹp sai số", font="sans-serif", font_size=22, color=MUTED_GRAY)
        subtitle.next_to(title, DOWN, buff=0.2)

        # Coordinate Axes
        axes = Axes(
            x_range=[-4, 4, 1],
            y_range=[0, 8, 2],
            x_length=8,
            y_length=4.5,
            axis_config={"color": "#334155", "stroke_width": 2},
        ).shift(DOWN * 0.5)

        # Loss Function: J(theta) = 0.5 * x^2 + 0.5 * sin(2x) + 2
        loss_curve = axes.plot(
            lambda x: 0.25 * (x - 1) ** 2 + 0.6 * np.sin(2.5 * x) + 2.5,
            x_range=[-3.5, 3.5],
            color=CYAN,
            stroke_width=3.5,
        )

        loss_label = MathTex(r"\mathcal{L}(\theta) = \frac{1}{N}\sum (y - \hat{y})^2", font_size=32, color=SOFT_WHITE)
        loss_label.to_corner(UR, buff=1.0)

        # Gradient Descent Ball
        initial_x = -3.0
        ball = Dot(axes.c2p(initial_x, 0.25 * (initial_x - 1) ** 2 + 0.6 * np.sin(2.5 * initial_x) + 2.5), color=AMBER, radius=0.14)
        ball_label = Text("Điểm khởi tạo", font="sans-serif", font_size=18, color=AMBER).next_to(ball, UP, buff=0.2)

        self.play(Write(title), FadeIn(subtitle), run_time=1.2)
        self.play(Create(axes), Create(loss_curve), Write(loss_label), run_time=1.8)
        self.play(FadeIn(ball), FadeIn(ball_label), run_time=0.8)
        self.wait(0.5)

        # Descent Steps
        steps = [-2.2, -1.4, -0.6, 0.2, 0.9]
        for next_x in steps:
            target_pos = axes.c2p(next_x, 0.25 * (next_x - 1) ** 2 + 0.6 * np.sin(2.5 * next_x) + 2.5)
            self.play(
                ball.animate.move_to(target_pos),
                ball_label.animate.next_to(target_pos, UP, buff=0.2),
                run_time=0.7,
                rate_func=ease_out_sine,
            )

        optimal_label = Text("Cực tiểu tối ưu", font="sans-serif", font_size=20, color=EMERALD)
        optimal_label.next_to(ball, DOWN, buff=0.3)
        self.play(ReplacementTransform(ball_label, optimal_label), run_time=0.8)
        self.wait(2.0)


class OverfittingVsGeneralizationScene(Scene):
    """Demonstrates Overfitting vs Generalization on noisy real-world data."""

    def construct(self):
        self.camera.background_color = BG_COLOR

        title = Text("BẪY QUÁ KHỚP (OVERFITTING)", font="sans-serif", font_size=36, color=CYAN, weight=BOLD)
        title.to_edge(UP, buff=0.8)

        axes = Axes(
            x_range=[0, 10, 2],
            y_range=[0, 10, 2],
            x_length=7.5,
            y_length=4.2,
            axis_config={"color": "#334155"},
        ).shift(DOWN * 0.4)

        # Sample data points
        np.random.seed(42)
        xs = np.linspace(1, 9, 14)
        ys = 0.8 * xs + 1.0 + np.random.normal(0, 0.9, len(xs))

        dots = VGroup(*[Dot(axes.c2p(x, y), color=AMBER, radius=0.09) for x, y in zip(xs, ys)])

        # Good fit line
        clean_fit = axes.plot(lambda x: 0.8 * x + 1.0, color=EMERALD, stroke_width=3.5)
        clean_lbl = Text("Khái quát hóa tốt (Generalization)", font="sans-serif", font_size=20, color=EMERALD)
        clean_lbl.to_corner(UL, buff=1.2)

        # Overfitted crazy polynomial
        poly_coeff = np.polyfit(xs, ys, deg=9)
        poly_fit = axes.plot(lambda x: np.polyval(poly_coeff, x), x_range=[1, 9], color=CRIMSON, stroke_width=3)
        overfit_lbl = Text("Quá khớp (Overfitting)", font="sans-serif", font_size=20, color=CRIMSON)
        overfit_lbl.to_corner(UL, buff=1.2)

        self.play(Write(title))
        self.play(Create(axes), FadeIn(dots), run_time=1.5)
        self.wait(0.5)

        self.play(Create(clean_fit), FadeIn(clean_lbl), run_time=1.5)
        self.wait(1.5)

        self.play(ReplacementTransform(clean_fit, poly_fit), ReplacementTransform(clean_lbl, overfit_lbl), run_time=1.8)
        self.wait(2.5)


class AttentionMatrixScene(Scene):
    """Scaled Dot-Product Attention: Q * K^T / sqrt(d_k)."""

    def construct(self):
        self.camera.background_color = BG_COLOR

        title = Text("CƠ CHẾ CHÚ Ý (ATTENTION MECHANISM)", font="sans-serif", font_size=34, color=CYAN, weight=BOLD)
        title.to_edge(UP, buff=0.8)

        formula = MathTex(
            r"\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{Q K^T}{\sqrt{d_k}}\right) V",
            font_size=34,
            color=SOFT_WHITE,
        )
        formula.next_to(title, DOWN, buff=0.4)

        # Heatmap tokens
        tokens = ["Tôi", "làm", "việc", "với", "AI"]
        n = len(tokens)

        grid = VGroup()
        for i in range(n):
            for j in range(n):
                val = 0.8 if i == j else (0.4 if abs(i - j) == 1 else 0.1)
                rect = Square(side_length=0.7)
                rect.set_fill(CYAN, opacity=val)
                rect.set_stroke(color="#1e293b", width=1.5)
                rect.move_to(np.array([j * 0.75 - 1.5, -i * 0.75 - 0.2, 0]))
                grid.add(rect)

        self.play(Write(title), Write(formula), run_time=1.5)
        self.play(Create(grid), run_time=2.0)
        self.wait(2.0)
