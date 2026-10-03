"""
Template Manim: Hóa Học & Cấu Trúc Phân Tử (Chemistry Template)
Chuẩn Bố Cục 4 Phân Vùng (Zone 1-4) & Neo-Noir Aesthetic
"""
from manim import *
import numpy as np

BG_OBSIDIAN = "#0c0d12"
AMBER = "#f59e0b"
GOLD = "#fbbf24"
CYAN = "#06b6d4"
RED_ATOM = "#ef4444"
WHITE_ATOM = "#f8fafc"
TEXT_PRIMARY = "#f8fafc"
TEXT_MUTED = "#94a3b8"
BG_CARD = "#14161f"
BORDER_SUBTLE = "#2d3345"

class ChemistryWaterMoleculeScene(Scene):
    def construct(self):
        self.camera.background_color = BG_OBSIDIAN

        # =====================================================================
        # ZONE 1: STATE TRACKER BAR (Đỉnh màn hình Y = +3.3)
        # =====================================================================
        states = ["NGUYEN TU", "LIEN KET", "GOC HOA TRI", "PHAN CUC"]
        tracker = VGroup()
        for idx, st in enumerate(states):
            is_active = (idx == 2)
            c = GOLD if is_active else TEXT_MUTED
            circ = Circle(radius=0.28, stroke_color=c, stroke_width=2.0 if is_active else 1.0,
                          fill_color=BG_CARD if is_active else BG_OBSIDIAN, fill_opacity=0.9)
            txt = Text(st, font="sans-serif", font_size=9, color=c, weight="BOLD" if is_active else "NORMAL")
            txt.move_to(circ.get_center())
            node = VGroup(circ, txt).shift(RIGHT * (idx * 2.5 - 3.75) + UP * 3.3)
            tracker.add(node)
        self.play(FadeIn(tracker), run_time=0.6)

        # =====================================================================
        # ZONE 2: VISUAL CANVAS (Cột trái X in [-6, 0]) - Phân tử H2O góc 104.5 độ
        # =====================================================================
        oxygen_pos = np.array([-2.8, 0.8, 0])
        dist = 1.8
        angle = 104.5 * DEGREES
        h1_pos = oxygen_pos + np.array([-dist * np.sin(angle/2), -dist * np.cos(angle/2), 0])
        h2_pos = oxygen_pos + np.array([dist * np.sin(angle/2), -dist * np.cos(angle/2), 0])

        # Liên kết cộng hóa trị (Bonds)
        bond1 = Line(oxygen_pos, h1_pos, stroke_color=BORDER_SUBTLE, stroke_width=4)
        bond2 = Line(oxygen_pos, h2_pos, stroke_color=BORDER_SUBTLE, stroke_width=4)

        # Nguyên tử Oxy (Lớn, Đỏ)
        oxygen = Circle(radius=0.55, fill_color=RED_ATOM, fill_opacity=1.0, stroke_color=WHITE, stroke_width=2).move_to(oxygen_pos)
        o_lbl = Text("O", font="sans-serif", font_size=18, color=WHITE, weight="BOLD").move_to(oxygen_pos)

        # 2 Nguyên tử Hydro (Nhỏ, Trắng)
        h1 = Circle(radius=0.35, fill_color=WHITE_ATOM, fill_opacity=1.0, stroke_color=CYAN, stroke_width=2).move_to(h1_pos)
        h1_lbl = Text("H", font="sans-serif", font_size=14, color=BG_OBSIDIAN, weight="BOLD").move_to(h1_pos)

        h2 = Circle(radius=0.35, fill_color=WHITE_ATOM, fill_opacity=1.0, stroke_color=CYAN, stroke_width=2).move_to(h2_pos)
        h2_lbl = Text("H", font="sans-serif", font_size=14, color=BG_OBSIDIAN, weight="BOLD").move_to(h2_pos)

        # Cung đo góc 104.5 độ
        arc = Arc(start_angle=-PI/2 - angle/2, angle=angle, radius=0.75, arc_center=oxygen_pos, color=AMBER, stroke_width=2.5)
        angle_lbl = Text("104.5°", font="sans-serif", font_size=11, color=AMBER, weight="BOLD").next_to(arc, DOWN, buff=0.1)

        molecule = VGroup(bond1, bond2, oxygen, o_lbl, h1, h1_lbl, h2, h2_lbl, arc, angle_lbl)

        self.play(Create(bond1), Create(bond2), run_time=0.8)
        self.play(FadeIn(oxygen), FadeIn(o_lbl), FadeIn(h1), FadeIn(h1_lbl), FadeIn(h2), FadeIn(h2_lbl), run_time=1.0)
        self.play(Create(arc), FadeIn(angle_lbl), run_time=0.8)

        # =====================================================================
        # ZONE 3: COGNITIVE STACK (Cột phải X in [1.0, 6.0])
        # =====================================================================
        badge_bg = RoundedRectangle(corner_radius=0.12, width=3.8, height=0.45,
                                    stroke_color=GOLD, stroke_width=1.2, fill_color=BG_CARD, fill_opacity=0.9)
        badge_txt = Text("Cấu Trúc Không Gian H2O", font="sans-serif", font_size=12, color=GOLD, weight="BOLD")
        badge = VGroup(badge_bg, badge_txt).move_to(np.array([3.6, 2.1, 0]))

        eq_card = RoundedRectangle(corner_radius=0.15, width=4.5, height=1.6,
                                   stroke_color=BORDER_SUBTLE, stroke_width=1.5, fill_color=BG_CARD, fill_opacity=0.92)
        eq_card.move_to(np.array([3.6, 0.8, 0]))
        eq_tex = MathTex(r"2\text{H}_2 + \text{O}_2 \xrightarrow{t^\circ} 2\text{H}_2\text{O}", color=CYAN, font_size=24)
        eq_tex.move_to(eq_card.get_center())
        eq_box = VGroup(eq_card, eq_tex)

        rule1 = Text("• Lai hóa sp3 với 2 cặp electron tự do", font="sans-serif", font_size=12, color=TEXT_PRIMARY)
        rule2 = Text("• Lực đẩy cặp electron ép góc từ 109.5° về 104.5°", font="sans-serif", font_size=12, color=AMBER)
        rule3 = Text("• Độ âm điện: Oxy (3.44) >> Hydro (2.20) -> Phân cực", font="sans-serif", font_size=12, color=TEXT_MUTED)
        rules = VGroup(rule1, rule2, rule3).arrange(DOWN, aligned_edge=LEFT, buff=0.25).next_to(eq_box, DOWN, buff=0.35)

        self.play(FadeIn(badge), Create(eq_box), FadeIn(rules), run_time=1.0)

        # =====================================================================
        # ZONE 4: BOTTOM CALLOUT CARD (Đáy Y in [-2.4, -1.8])
        # =====================================================================
        callout_bg = RoundedRectangle(corner_radius=0.15, width=10.5, height=0.8,
                                      stroke_color=BORDER_SUBTLE, stroke_width=1.5, fill_color=BG_CARD, fill_opacity=0.92)
        callout_bg.shift(UP * -2.1)
        callout_txt = Text("Bản chất: Góc gấp khúc và độ âm điện lệch tạo moment lưỡng cực vĩnh cửu cho nước.",
                           font="sans-serif", font_size=13, color=TEXT_PRIMARY)
        callout_txt.move_to(callout_bg.get_center())
        callout_card = VGroup(callout_bg, callout_txt)

        self.play(FadeIn(callout_card), run_time=0.6)
        self.wait(2.0)
