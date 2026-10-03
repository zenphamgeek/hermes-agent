"""
Template Manim: Trí Tuệ Nhân Tạo & Deep Learning (ML Template)
Chuẩn Bố Cục 4 Phân Vùng (Zone 1-4) & Neo-Noir Aesthetic
"""
from manim import *
import numpy as np

BG_OBSIDIAN = "#0c0d12"
AMBER = "#f59e0b"
GOLD = "#fbbf24"
CYAN = "#06b6d4"
EMERALD = "#10b981"
VIOLET = "#8b5cf6"
TEXT_PRIMARY = "#f8fafc"
TEXT_MUTED = "#94a3b8"
BG_CARD = "#14161f"
BORDER_SUBTLE = "#2d3345"

class MLAttentionMechanismScene(Scene):
    def construct(self):
        self.camera.background_color = BG_OBSIDIAN

        # =====================================================================
        # ZONE 1: STATE TRACKER BAR (Đỉnh màn hình Y = +3.3)
        # =====================================================================
        states = ["EMBEDDING", "Q K V", "DOT PRODUCT", "SOFTMAX"]
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
        # ZONE 2: VISUAL CANVAS (Cột trái X in [-6, 0]) - Ma trận Attention Score
        # =====================================================================
        canvas_center = np.array([-2.8, 0.6, 0])
        grid_size = 4
        cell_w = 0.75
        heatmap = VGroup()
        scores = [
            [0.85, 0.10, 0.03, 0.02],
            [0.15, 0.70, 0.10, 0.05],
            [0.05, 0.20, 0.65, 0.10],
            [0.02, 0.08, 0.15, 0.75]
        ]
        tokens = ["The", "animal", "didn't", "cross"]

        for r in range(grid_size):
            # Row label
            lbl_r = Text(tokens[r], font="sans-serif", font_size=10, color=TEXT_MUTED)
            lbl_r.move_to(canvas_center + np.array([-2.0, (1.5 - r) * cell_w, 0]))
            heatmap.add(lbl_r)

            # Col label
            lbl_c = Text(tokens[r], font="sans-serif", font_size=10, color=TEXT_MUTED)
            lbl_c.move_to(canvas_center + np.array([(r - 1.5) * cell_w, 2.0, 0]))
            heatmap.add(lbl_c)

            for c_idx in range(grid_size):
                val = scores[r][c_idx]
                col = interpolate_color(ManimColor(BG_CARD), ManimColor(CYAN), val)
                sq = Square(side_length=cell_w, stroke_color=BORDER_SUBTLE, stroke_width=1.0,
                            fill_color=col, fill_opacity=0.85)
                sq.move_to(canvas_center + np.array([(c_idx - 1.5) * cell_w, (1.5 - r) * cell_w, 0]))
                val_txt = Text(f"{val:.2f}", font="sans-serif", font_size=9, color=TEXT_PRIMARY)
                val_txt.move_to(sq.get_center())
                heatmap.add(sq, val_txt)

        self.play(FadeIn(heatmap), run_time=1.5)

        # =====================================================================
        # ZONE 3: COGNITIVE STACK (Cột phải X in [1.0, 6.0])
        # =====================================================================
        badge_bg = RoundedRectangle(corner_radius=0.12, width=3.8, height=0.45,
                                    stroke_color=GOLD, stroke_width=1.2, fill_color=BG_CARD, fill_opacity=0.9)
        badge_txt = Text("Scaled Dot-Product Attention", font="sans-serif", font_size=12, color=GOLD, weight="BOLD")
        badge = VGroup(badge_bg, badge_txt).move_to(np.array([3.6, 2.1, 0]))

        eq_card = RoundedRectangle(corner_radius=0.15, width=4.5, height=1.6,
                                   stroke_color=BORDER_SUBTLE, stroke_width=1.5, fill_color=BG_CARD, fill_opacity=0.92)
        eq_card.move_to(np.array([3.6, 0.8, 0]))
        eq_tex = MathTex(r"\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right)V",
                         color=CYAN, font_size=20)
        eq_tex.move_to(eq_card.get_center())
        eq_box = VGroup(eq_card, eq_tex)

        rule1 = Text("• Q (Query) so khớp K (Key) qua tích vô hướng", font="sans-serif", font_size=12, color=TEXT_PRIMARY)
        rule2 = Text("• Chia cho sqrt(d_k) để chống triệt tiêu đạo hàm", font="sans-serif", font_size=12, color=AMBER)
        rule3 = Text("• Softmax chuẩn hóa xác suất phân phối trọng số", font="sans-serif", font_size=12, color=EMERALD)
        rules = VGroup(rule1, rule2, rule3).arrange(DOWN, aligned_edge=LEFT, buff=0.25).next_to(eq_box, DOWN, buff=0.35)

        self.play(FadeIn(badge), Create(eq_box), FadeIn(rules), run_time=1.0)

        # =====================================================================
        # ZONE 4: BOTTOM CALLOUT CARD (Đáy Y in [-2.4, -1.8])
        # =====================================================================
        callout_bg = RoundedRectangle(corner_radius=0.15, width=10.5, height=0.8,
                                      stroke_color=BORDER_SUBTLE, stroke_width=1.5, fill_color=BG_CARD, fill_opacity=0.92)
        callout_bg.shift(UP * -2.1)
        callout_txt = Text("Bản chất: Cơ chế Attention tính toán mức độ tương quan động giữa mọi cặp từ trong ngữ cảnh.",
                           font="sans-serif", font_size=12, color=TEXT_PRIMARY)
        callout_txt.move_to(callout_bg.get_center())
        callout_card = VGroup(callout_bg, callout_txt)

        self.play(FadeIn(callout_card), run_time=0.6)
        self.wait(2.0)
