"""
Template Manim: Cấu Trúc Dữ Liệu & Đồ Thị Giải Thuật (CS & DSA Template)
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

class CSGraphDijkstraScene(Scene):
    def construct(self):
        self.camera.background_color = BG_OBSIDIAN

        # =====================================================================
        # ZONE 1: STATE TRACKER BAR (Đỉnh màn hình Y = +3.3)
        # =====================================================================
        states = ["KHOI TAO", "RELAX CANH", "MIN-HEAP", "DUONG DI"]
        tracker = VGroup()
        for idx, st in enumerate(states):
            is_active = (idx == 1)
            c = GOLD if is_active else TEXT_MUTED
            circ = Circle(radius=0.28, stroke_color=c, stroke_width=2.0 if is_active else 1.0,
                          fill_color=BG_CARD if is_active else BG_OBSIDIAN, fill_opacity=0.9)
            txt = Text(st, font="sans-serif", font_size=8, color=c, weight="BOLD" if is_active else "NORMAL")
            txt.move_to(circ.get_center())
            node = VGroup(circ, txt).shift(RIGHT * (idx * 2.5 - 3.75) + UP * 3.3)
            tracker.add(node)
        self.play(FadeIn(tracker), run_time=0.6)

        # =====================================================================
        # ZONE 2: VISUAL CANVAS (Cột trái X in [-6, 0]) - Đồ thị trọng số
        # =====================================================================
        nodes_pos = {
            "S": np.array([-4.8, 0.6, 0]),
            "A": np.array([-3.2, 1.8, 0]),
            "B": np.array([-3.2, -0.6, 0]),
            "T": np.array([-1.4, 0.6, 0]),
        }

        # Tạo vertices
        vertices = VGroup()
        for k, pt in nodes_pos.items():
            circ = Circle(radius=0.35, fill_color=BG_CARD, fill_opacity=1.0, stroke_color=CYAN, stroke_width=2).move_to(pt)
            lbl = Text(k, font="sans-serif", font_size=14, color=WHITE, weight="BOLD").move_to(pt)
            vertices.add(VGroup(circ, lbl))

        # Tạo edges
        edges_data = [
            ("S", "A", "4"),
            ("S", "B", "2"),
            ("B", "A", "1"),
            ("A", "T", "3"),
            ("B", "T", "5")
        ]
        edges_group = VGroup()
        for u, v, w in edges_data:
            p1 = nodes_pos[u]
            p2 = nodes_pos[v]
            line = Line(p1, p2, stroke_color=BORDER_SUBTLE, stroke_width=2.5)
            mid = (p1 + p2) / 2 + UP * 0.15
            w_txt = Text(w, font="sans-serif", font_size=11, color=AMBER).move_to(mid)
            edges_group.add(line, w_txt)

        self.play(Create(edges_group), run_time=1.0)
        self.play(FadeIn(vertices), run_time=0.8)

        # Highlight đường đi ngắn nhất: S -> B -> A -> T (Chi phí: 2 + 1 + 3 = 6)
        path_edges = [
            Line(nodes_pos["S"], nodes_pos["B"], stroke_color=EMERALD, stroke_width=4),
            Line(nodes_pos["B"], nodes_pos["A"], stroke_color=EMERALD, stroke_width=4),
            Line(nodes_pos["A"], nodes_pos["T"], stroke_color=EMERALD, stroke_width=4)
        ]
        self.play(*[Create(e) for e in path_edges], run_time=1.5)

        # =====================================================================
        # ZONE 3: COGNITIVE STACK (Cột phải X in [1.0, 6.0])
        # =====================================================================
        badge_bg = RoundedRectangle(corner_radius=0.12, width=3.8, height=0.45,
                                    stroke_color=GOLD, stroke_width=1.2, fill_color=BG_CARD, fill_opacity=0.9)
        badge_txt = Text("Dijkstra Shortest Path", font="sans-serif", font_size=12, color=GOLD, weight="BOLD")
        badge = VGroup(badge_bg, badge_txt).move_to(np.array([3.6, 2.1, 0]))

        eq_card = RoundedRectangle(corner_radius=0.15, width=4.5, height=1.6,
                                   stroke_color=BORDER_SUBTLE, stroke_width=1.5, fill_color=BG_CARD, fill_opacity=0.92)
        eq_card.move_to(np.array([3.6, 0.8, 0]))
        eq_tex = MathTex(r"d[v] = \min(d[v], d[u] + w(u, v))", color=CYAN, font_size=24)
        eq_tex.move_to(eq_card.get_center())
        eq_box = VGroup(eq_card, eq_tex)

        rule1 = Text("• Kỹ thuật 'Relaxing' cập nhật khoảng cách tạm", font="sans-serif", font_size=12, color=TEXT_PRIMARY)
        rule2 = Text("• Dùng Min-Heap chọn node gần nhất trong O(log V)", font="sans-serif", font_size=12, color=EMERALD)
        rule3 = Text("• Độ phức tạp toàn phần: O((V + E) log V)", font="sans-serif", font_size=12, color=AMBER)
        rules = VGroup(rule1, rule2, rule3).arrange(DOWN, aligned_edge=LEFT, buff=0.25).next_to(eq_box, DOWN, buff=0.35)

        self.play(FadeIn(badge), Create(eq_box), FadeIn(rules), run_time=1.0)

        # =====================================================================
        # ZONE 4: BOTTOM CALLOUT CARD (Đáy Y in [-2.4, -1.8])
        # =====================================================================
        callout_bg = RoundedRectangle(corner_radius=0.15, width=10.5, height=0.8,
                                      stroke_color=BORDER_SUBTLE, stroke_width=1.5, fill_color=BG_CARD, fill_opacity=0.92)
        callout_bg.shift(UP * -2.1)
        callout_txt = Text("Bản chất: Chiến lược tham lam (Greedy) đảm bảo đường đi tối ưu cho đồ thị trọng số không âm.",
                           font="sans-serif", font_size=12, color=TEXT_PRIMARY)
        callout_txt.move_to(callout_bg.get_center())
        callout_card = VGroup(callout_bg, callout_txt)

        self.play(FadeIn(callout_card), run_time=0.6)
        self.wait(2.0)
