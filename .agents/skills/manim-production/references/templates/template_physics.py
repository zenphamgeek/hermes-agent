"""
Template Manim: Vật Lý & Dao Động / Điện Từ (Physics Template)
Chuẩn Bố Cục 4 Phân Vùng (Zone 1-4) & Neo-Noir Aesthetic
"""
from manim import *
import numpy as np

# Palette Neo-Noir ZenPalette
BG_OBSIDIAN = "#0c0d12"
AMBER = "#f59e0b"
GOLD = "#fbbf24"
CYAN = "#06b6d4"
EMERALD = "#10b981"
TEXT_PRIMARY = "#f8fafc"
TEXT_MUTED = "#94a3b8"
BG_CARD = "#14161f"
BORDER_SUBTLE = "#2d3345"

class PhysicsPendulumScene(Scene):
    def construct(self):
        self.camera.background_color = BG_OBSIDIAN

        # =====================================================================
        # ZONE 1: STATE TRACKER BAR (Đỉnh màn hình Y = +3.3)
        # =====================================================================
        states = ["CO HOC", "DAO DONG", "PHUONG TRINH", "THE NANG"]
        tracker = VGroup()
        for idx, st in enumerate(states):
            is_active = (idx == 1)
            c = GOLD if is_active else TEXT_MUTED
            circ = Circle(radius=0.28, stroke_color=c, stroke_width=2.0 if is_active else 1.0,
                          fill_color=BG_CARD if is_active else BG_OBSIDIAN, fill_opacity=0.9)
            txt = Text(st, font="sans-serif", font_size=9, color=c, weight="BOLD" if is_active else "NORMAL")
            txt.move_to(circ.get_center())
            node = VGroup(circ, txt).shift(RIGHT * (idx * 2.5 - 3.75) + UP * 3.3)
            tracker.add(node)
        self.play(FadeIn(tracker), run_time=0.6)

        # =====================================================================
        # ZONE 2: VISUAL CANVAS (Cột trái X in [-6, 0]) - Con lắc vật lý
        # =====================================================================
        pivot = np.array([-2.8, 2.2, 0])
        rod_length = 2.8
        theta_0 = PI / 5
        omega = 2.0
        time_tracker = ValueTracker(0)

        pivot_dot = Dot(pivot, color=WHITE, radius=0.08)
        
        # Dây con lắc động
        rod = always_redraw(lambda: Line(
            pivot,
            pivot + np.array([
                rod_length * np.sin(theta_0 * np.cos(omega * time_tracker.get_value())),
                -rod_length * np.cos(theta_0 * np.cos(omega * time_tracker.get_value())),
                0
            ]),
            stroke_color=CYAN,
            stroke_width=3
        ))

        # Quả cầu kim loại
        bob = always_redraw(lambda: Circle(
            radius=0.28,
            fill_color=AMBER,
            fill_opacity=1.0,
            stroke_color=GOLD,
            stroke_width=2
        ).move_to(rod.get_end()))

        # Cung góc dao động theta
        arc_ref = DashedLine(pivot, pivot + DOWN * 1.5, stroke_color=TEXT_MUTED, stroke_width=1.5)

        self.play(FadeIn(pivot_dot), Create(arc_ref), Create(rod), FadeIn(bob), run_time=1.0)

        # =====================================================================
        # ZONE 3: COGNITIVE STACK (Cột phải X in [1.0, 6.0])
        # =====================================================================
        # 1. ConceptBadge
        badge_bg = RoundedRectangle(corner_radius=0.12, width=3.8, height=0.45,
                                    stroke_color=GOLD, stroke_width=1.2, fill_color=BG_CARD, fill_opacity=0.9)
        badge_txt = Text("Con Lắc Đơn: Dao Động Nhỏ", font="sans-serif", font_size=12, color=GOLD, weight="BOLD")
        badge = VGroup(badge_bg, badge_txt).move_to(np.array([3.6, 2.1, 0]))

        # 2. EquationBox
        eq_card = RoundedRectangle(corner_radius=0.15, width=4.5, height=1.6,
                                   stroke_color=BORDER_SUBTLE, stroke_width=1.5, fill_color=BG_CARD, fill_opacity=0.92)
        eq_card.move_to(np.array([3.6, 0.8, 0]))
        eq_tex = MathTex(r"\frac{d^2\theta}{dt^2} + \frac{g}{L}\sin\theta = 0", color=CYAN, font_size=28)
        eq_tex.move_to(eq_card.get_center())
        eq_box = VGroup(eq_card, eq_tex)

        # 3. Bullet Rules
        rule1 = Text("• Khi góc theta << 1: sin(theta) ~ theta", font="sans-serif", font_size=12, color=TEXT_PRIMARY)
        rule2 = Text("• Chu kỳ dao động riêng: T = 2pi*sqrt(L/g)", font="sans-serif", font_size=12, color=EMERALD)
        rule3 = Text("• Bảo toàn cơ năng: E = Wd + Wt = const", font="sans-serif", font_size=12, color=TEXT_MUTED)
        rules = VGroup(rule1, rule2, rule3).arrange(DOWN, aligned_edge=LEFT, buff=0.25).next_to(eq_box, DOWN, buff=0.35)

        self.play(FadeIn(badge), Create(eq_box), FadeIn(rules), run_time=1.0)

        # =====================================================================
        # ZONE 4: BOTTOM CALLOUT CARD (Đáy Y in [-2.4, -1.8])
        # =====================================================================
        callout_bg = RoundedRectangle(corner_radius=0.15, width=10.5, height=0.8,
                                      stroke_color=BORDER_SUBTLE, stroke_width=1.5, fill_color=BG_CARD, fill_opacity=0.92)
        callout_bg.shift(UP * -2.1)
        callout_txt = Text("Bản chất: Lực phục hồi tỷ lệ thuận với ly độ góc tạo nên chuyển động điều hòa.",
                           font="sans-serif", font_size=13, color=TEXT_PRIMARY)
        callout_txt.move_to(callout_bg.get_center())
        callout_card = VGroup(callout_bg, callout_txt)

        self.play(FadeIn(callout_card), run_time=0.6)

        # Diễn hoạt dao động thực tế
        self.play(time_tracker.animate.set_value(4 * PI), run_time=4.0, rate_func=linear)
        self.wait(1.0)
