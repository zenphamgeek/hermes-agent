"""
Template Manim: Toán Cao Cấp & Biến Đổi Tuyến Tính 3Blue1Brown (Math 3B1B Template)
Chuẩn Bố Cục 4 Phân Vùng (Zone 1-4) & Neo-Noir Aesthetic
"""
from manim import *
import numpy as np

BG_OBSIDIAN = "#0c0d12"
AMBER = "#f59e0b"
GOLD = "#fbbf24"
CYAN = "#06b6d4"
EMERALD = "#10b981"
TEXT_PRIMARY = "#f8fafc"
TEXT_MUTED = "#94a3b8"
BG_CARD = "#14161f"
BORDER_SUBTLE = "#2d3345"

class Math3B1BMatrixScene(Scene):
    def construct(self):
        self.camera.background_color = BG_OBSIDIAN

        # =====================================================================
        # ZONE 1: STATE TRACKER BAR (Đỉnh màn hình Y = +3.3)
        # =====================================================================
        states = ["KHONG GIAN", "VECTOR CO SO", "BIEN DOI", "DINH THUC"]
        tracker = VGroup()
        for idx, st in enumerate(states):
            is_active = (idx == 2)
            c = GOLD if is_active else TEXT_MUTED
            circ = Circle(radius=0.28, stroke_color=c, stroke_width=2.0 if is_active else 1.0,
                          fill_color=BG_CARD if is_active else BG_OBSIDIAN, fill_opacity=0.9)
            txt = Text(st, font="sans-serif", font_size=8, color=c, weight="BOLD" if is_active else "NORMAL")
            txt.move_to(circ.get_center())
            node = VGroup(circ, txt).shift(RIGHT * (idx * 2.5 - 3.75) + UP * 3.3)
            tracker.add(node)
        self.play(FadeIn(tracker), run_time=0.6)

        # =====================================================================
        # ZONE 2: VISUAL CANVAS (Cột trái X in [-6, 0]) - Mặt phẳng tọa độ 2D
        # =====================================================================
        plane_origin = np.array([-2.8, 0.6, 0])
        axes = Axes(
            x_range=[-2.5, 2.5, 1],
            y_range=[-2, 2, 1],
            x_length=4.5,
            y_length=3.5,
            axis_config={"color": BORDER_SUBTLE, "stroke_width": 1.5}
        ).move_to(plane_origin)

        # Vector cơ sở i_hat và j_hat
        i_hat_orig = Vector([1, 0], color=EMERALD).shift(plane_origin)
        j_hat_orig = Vector([0, 1], color=CYAN).shift(plane_origin)

        # Ma trận biến đổi: A = [[1, 1], [0, 1.5]] (Shear + Stretch)
        i_hat_trans = Vector([1, 0], color=EMERALD).shift(plane_origin)
        j_hat_trans = Vector([1, 1.5], color=CYAN).shift(plane_origin)

        # Hình bình hành diện tích định thức det(A)
        polygon = Polygon(
            plane_origin,
            plane_origin + np.array([1, 0, 0]),
            plane_origin + np.array([2, 1.5, 0]),
            plane_origin + np.array([1, 1.5, 0]),
            fill_color=GOLD,
            fill_opacity=0.35,
            stroke_color=GOLD,
            stroke_width=2
        )

        self.play(Create(axes), run_time=0.8)
        self.play(Create(i_hat_orig), Create(j_hat_orig), run_time=0.8)
        self.play(Transform(i_hat_orig, i_hat_trans), Transform(j_hat_orig, j_hat_trans), FadeIn(polygon), run_time=2.0)

        # =====================================================================
        # ZONE 3: COGNITIVE STACK (Cột phải X in [1.0, 6.0])
        # =====================================================================
        badge_bg = RoundedRectangle(corner_radius=0.12, width=3.8, height=0.45,
                                    stroke_color=GOLD, stroke_width=1.2, fill_color=BG_CARD, fill_opacity=0.9)
        badge_txt = Text("Biến Đổi Tuyến Tính & det(A)", font="sans-serif", font_size=12, color=GOLD, weight="BOLD")
        badge = VGroup(badge_bg, badge_txt).move_to(np.array([3.6, 2.1, 0]))

        eq_card = RoundedRectangle(corner_radius=0.15, width=4.5, height=1.6,
                                   stroke_color=BORDER_SUBTLE, stroke_width=1.5, fill_color=BG_CARD, fill_opacity=0.92)
        eq_card.move_to(np.array([3.6, 0.8, 0]))
        eq_tex = MathTex(r"A = \begin{bmatrix} 1 & 1 \\ 0 & 1.5 \end{bmatrix}, \quad \det(A) = 1.5",
                         color=CYAN, font_size=22)
        eq_tex.move_to(eq_card.get_center())
        eq_box = VGroup(eq_card, eq_tex)

        rule1 = Text("• Các đường lưới song song và cách đều sau biến đổi", font="sans-serif", font_size=12, color=TEXT_PRIMARY)
        rule2 = Text("• Gốc tọa độ (0, 0) luôn giữ cố định bất biến", font="sans-serif", font_size=12, color=AMBER)
        rule3 = Text("• det(A) là hệ số co giãn diện tích của không gian", font="sans-serif", font_size=12, color=EMERALD)
        rules = VGroup(rule1, rule2, rule3).arrange(DOWN, aligned_edge=LEFT, buff=0.25).next_to(eq_box, DOWN, buff=0.35)

        self.play(FadeIn(badge), Create(eq_box), FadeIn(rules), run_time=1.0)

        # =====================================================================
        # ZONE 4: BOTTOM CALLOUT CARD (Đáy Y in [-2.4, -1.8])
        # =====================================================================
        callout_bg = RoundedRectangle(corner_radius=0.15, width=10.5, height=0.8,
                                      stroke_color=BORDER_SUBTLE, stroke_width=1.5, fill_color=BG_CARD, fill_opacity=0.92)
        callout_bg.shift(UP * -2.1)
        callout_txt = Text("Bản chất 3B1B: Ma trận chỉ là tọa độ mới của các vector cơ sở sau khi không gian biến dạng.",
                           font="sans-serif", font_size=12, color=TEXT_PRIMARY)
        callout_txt.move_to(callout_bg.get_center())
        callout_card = VGroup(callout_bg, callout_txt)

        self.play(FadeIn(callout_card), run_time=0.6)
        self.wait(2.0)
