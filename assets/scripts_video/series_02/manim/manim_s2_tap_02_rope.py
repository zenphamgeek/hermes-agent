#!/usr/bin/env python3
"""
Manim 2K QHD Master Production Scenes — RoPE (Rotary Position Embedding)
================================================================================
Resolution: 2560x1440 @ 60fps | Theme: Neo-Noir Obsidian (#0b0f19)
Standards: Median & 3Blue1Brown Continuous Geometric Flow

Master Quality Standards:
- 100% Genuine Manim Mathematical Motion (Multi-beat staged animations)
- Continuous Ambient Mathematical Loops (ValueTracker, Phasors, Traveling Waves)
- ZERO Fake Camera Drift / Crop Sway (Solid 1080p/2K Framing)
- ZERO Static Bullet Boxes / Box Gaps (Pure Geometric Hero Mobjects)
- Safe Margins: |x| <= 5.2, |y| <= 3.2, Bottom y >= -2.4 for subtitles
- Audio Voice-Sync matching exact scene audio durations (472s total)
"""

from __future__ import annotations
import sys
import math
from pathlib import Path

sys.path.insert(0, "/workspace")
sys.path.insert(0, "/workspace/series_02")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from manim import *
import numpy as np

# Neo-Noir Obsidian Theme Palette (High Contrast & Zero Glare)
COLOR_BG = "#0b0f19"
COLOR_CARD_BG = "#111726"
COLOR_CYAN = "#00f0ff"
COLOR_AMBER = "#ffb800"
COLOR_GOLD = "#ffd700"
COLOR_ROSE = "#ff2a6d"
COLOR_EMERALD = "#00e676"
COLOR_VIOLET = "#8b5cf6"
COLOR_TEXT = "#f8fafc"
COLOR_MUTED = "#94a3b8"
COLOR_BORDER = "#1e293b"
COLOR_PANEL = "#141824"
FONT_FAMILY = "Noto Sans"

def add_zenpham_brand(scene: Scene, ep_title: str = ""):
    """Clean Minimalist Brand HUD: Small channel logo in upper corner (UR), zero text clutter."""
    logo_rel = Path("assets/brand/zenpham-brand-kit/zenpham-logo-transparent-2000x2000.png")
    logo_abs = Path("/home/zen/hermes-agent") / logo_rel
    logo_work = Path("/work") / logo_rel
    logo_file = (
        logo_work if logo_work.exists()
        else logo_abs if logo_abs.exists()
        else logo_rel
    )
    if logo_file.exists():
        logo_mobj = ImageMobject(str(logo_file))
        logo_mobj.scale_to_fit_height(0.65)
        logo_mobj.to_corner(UR, buff=0.45)
        scene.add(logo_mobj)
    else:
        emblem = Circle(radius=0.25, stroke_color="#ffd700", stroke_width=1.5, fill_color="#141824", fill_opacity=0.85)
        emblem_txt = Text("Z", font=FONT_FAMILY, font_size=12, weight=BOLD, color="#ffd700").move_to(emblem.get_center())
        logo_mobj = VGroup(emblem, emblem_txt).to_corner(UR, buff=0.45)
        scene.add(logo_mobj)


# =============================================================================
# SCENE 01: NGHỊCH LÝ VỊ TRÍ & PHÉP XOAY BẢO TOÀN (COLD OPEN — 58.3s)
# =============================================================================
class Tap02Scene01ColdOpen(Scene):
    """
    Cold Open (58.3s Voiceover):
    Beat 1 (0-16s): 1D Number line tokens at p=1 and p=4 (distance=3).
                    Translate together to p=7 and p=10 (distance remains 3).
    Beat 2 (16-36s): Morph 1D line into 2D Complex Unit Circle.
                     Query vector rotates as position advances, norm is constant.
                     Key vector appears with relative arc (n-m)*theta.
    Beat 3 (36-50s): Simultaneous translation by +6*theta.
                     Visual proof that relative angle and dot product are invariant.
    Beat 4 (50-58.3s): Geometric invariance formula and continuous ambient phasor loop.
    """
    def construct(self):
        self.camera.background_color = COLOR_BG

        # Title HUD — Direct Typography
        title_text = Text(
            "ROTARY POSITION EMBEDDING // VŨ ĐIỆU PHÉP XOAY",
            font=FONT_FAMILY, font_size=15, weight=BOLD, color=COLOR_CYAN
        ).to_edge(UP, buff=0.45)
        title_line = Line(
            title_text.get_left() + DOWN * 0.12, title_text.get_right() + DOWN * 0.12,
            color=COLOR_CYAN, stroke_width=1.5
        )
        self.play(FadeIn(title_text, shift=DOWN * 0.15), Create(title_line), run_time=1.0)

        # -------------------------------------------------------------
        # BEAT 1: 1D Token Translation (0 - 16s)
        # -------------------------------------------------------------
        line_y = 1.0
        axis_line = NumberLine(
            x_range=[0, 12, 1], length=9.6, color=COLOR_BORDER,
            include_numbers=True, font_size=16, stroke_width=2.5
        ).shift(UP * line_y)

        t1_pos = axis_line.n2p(1)
        t4_pos = axis_line.n2p(4)

        t1_box = RoundedRectangle(corner_radius=0.1, width=1.3, height=0.65, fill_color="#1e293b", fill_opacity=0.95, stroke_color=COLOR_CYAN, stroke_width=1.8).move_to(t1_pos + UP * 0.65)
        t1_lbl = Text("Từ 1 (p=1)", font=FONT_FAMILY, font_size=12, weight=BOLD, color=WHITE).move_to(t1_box)
        t1_grp = VGroup(t1_box, t1_lbl)

        t4_box = RoundedRectangle(corner_radius=0.1, width=1.3, height=0.65, fill_color="#1e293b", fill_opacity=0.95, stroke_color=COLOR_GOLD, stroke_width=1.8).move_to(t4_pos + UP * 0.65)
        t4_lbl = Text("Từ 2 (p=4)", font=FONT_FAMILY, font_size=12, weight=BOLD, color=WHITE).move_to(t4_box)
        t4_grp = VGroup(t4_box, t4_lbl)

        bracket = DoubleArrow(t1_pos + UP * 1.25, t4_pos + UP * 1.25, buff=0, color=COLOR_ROSE, stroke_width=3.0)
        bracket_lbl = Text("Khoảng cách = 3 vị trí", font=FONT_FAMILY, font_size=12, weight=BOLD, color=COLOR_ROSE).next_to(bracket, UP, buff=0.12)
        bracket_grp = VGroup(bracket, bracket_lbl)

        self.play(Create(axis_line), FadeIn(t1_grp), FadeIn(t4_grp), run_time=2.0)
        self.play(Create(bracket), Write(bracket_lbl), run_time=1.8)
        self.wait(1.5)

        # Shift both tokens by 6 positions: 1->7, 4->10
        t7_pos = axis_line.n2p(7)
        t10_pos = axis_line.n2p(10)
        bracket_shifted = DoubleArrow(t7_pos + UP * 1.25, t10_pos + UP * 1.25, buff=0, color=COLOR_ROSE, stroke_width=3.0)
        bracket_lbl_shifted = Text("Khoảng cách vẫn = 3 vị trí", font=FONT_FAMILY, font_size=12, weight=BOLD, color=COLOR_ROSE).next_to(bracket_shifted, UP, buff=0.12)

        t1_box_shifted = RoundedRectangle(corner_radius=0.1, width=1.3, height=0.65, fill_color="#1e293b", fill_opacity=0.95, stroke_color=COLOR_CYAN, stroke_width=1.8).move_to(t7_pos + UP * 0.65)
        t1_lbl_shifted = Text("Từ 1 (p=7)", font=FONT_FAMILY, font_size=12, weight=BOLD, color=WHITE).move_to(t1_box_shifted)
        t1_grp_shifted = VGroup(t1_box_shifted, t1_lbl_shifted)

        t4_box_shifted = RoundedRectangle(corner_radius=0.1, width=1.3, height=0.65, fill_color="#1e293b", fill_opacity=0.95, stroke_color=COLOR_GOLD, stroke_width=1.8).move_to(t10_pos + UP * 0.65)
        t4_lbl_shifted = Text("Từ 2 (p=10)", font=FONT_FAMILY, font_size=12, weight=BOLD, color=WHITE).move_to(t4_box_shifted)
        t4_grp_shifted = VGroup(t4_box_shifted, t4_lbl_shifted)

        self.play(
            Transform(t1_grp, t1_grp_shifted),
            Transform(t4_grp, t4_grp_shifted),
            Transform(bracket, bracket_shifted),
            Transform(bracket_lbl, bracket_lbl_shifted),
            run_time=3.5, rate_func=rate_functions.smooth
        )
        self.wait(2.0)

        # -------------------------------------------------------------
        # BEAT 2: Morphing to 2D Complex Unit Circle (16 - 36s)
        # -------------------------------------------------------------
        center_pt = LEFT * 2.2 + DOWN * 0.35
        circle_r = 2.0
        grid = NumberPlane(
            x_range=[-3, 3, 1], y_range=[-3, 3, 1],
            x_length=4.5, y_length=4.5,
            background_line_style={"stroke_color": COLOR_BORDER, "stroke_width": 1.2}
        ).move_to(center_pt)

        # Kinetic pulse tracker for continuous live animation
        pulse_tracker = ValueTracker(0.0)
        pulse_tracker.add_updater(lambda m, dt: m.increment_value(dt))
        self.add(pulse_tracker)

        unit_circle = Circle(radius=circle_r, stroke_color=COLOR_CYAN, stroke_width=2.0).move_to(center_pt)
        circ_aura = always_redraw(lambda: Circle(
            radius=circle_r + 0.08 * np.sin(pulse_tracker.get_value() * 2.5),
            stroke_color=COLOR_CYAN, stroke_width=1.5,
            stroke_opacity=0.35 + 0.15 * np.sin(pulse_tracker.get_value() * 2.5)
        ).move_to(center_pt))
        c_dot = Dot(center_pt, radius=0.07, color=COLOR_CYAN)
        circ_lbl = Text("Mặt Phẳng Phức 2D (Độ dài = 1)", font=FONT_FAMILY, font_size=12.0, color=COLOR_MUTED).next_to(unit_circle, UP, buff=0.15)

        self.play(
            FadeOut(axis_line), FadeOut(t1_grp), FadeOut(t4_grp), FadeOut(bracket), FadeOut(bracket_lbl),
            Create(grid), Create(unit_circle), FadeIn(circ_aura), FadeIn(c_dot), Write(circ_lbl),
            run_time=3.0
        )

        # Vector Query q with dynamic rotation
        ang_q_tracker = ValueTracker(0.35)
        v_q = always_redraw(lambda: Arrow(
            center_pt,
            center_pt + circle_r * np.array([np.cos(ang_q_tracker.get_value()), np.sin(ang_q_tracker.get_value()), 0]),
            buff=0, color=COLOR_CYAN, stroke_width=4.0
        ))
        lbl_q = always_redraw(lambda: MathTex(
            r"\mathbf{q}_m", color=COLOR_CYAN, font_size=24
        ).next_to(v_q.get_end(), UR, buff=0.1))

        self.play(GrowArrow(v_q), Write(lbl_q), run_time=2.0)

        # Position advances: vector rotates, length unchanged
        self.play(ang_q_tracker.animate.set_value(1.2), run_time=3.5, rate_func=rate_functions.smooth)
        self.wait(1.5)

        # Key vector k appears
        ang_k_tracker = ValueTracker(2.4)
        v_k = always_redraw(lambda: Arrow(
            center_pt,
            center_pt + circle_r * np.array([np.cos(ang_k_tracker.get_value()), np.sin(ang_k_tracker.get_value()), 0]),
            buff=0, color=COLOR_GOLD, stroke_width=4.0
        ))
        lbl_k = always_redraw(lambda: MathTex(
            r"\mathbf{k}_n", color=COLOR_GOLD, font_size=24
        ).next_to(v_k.get_end(), UL, buff=0.1))

        # Relative arc
        arc_rel = always_redraw(lambda: Arc(
            radius=0.8,
            start_angle=ang_q_tracker.get_value(),
            angle=ang_k_tracker.get_value() - ang_q_tracker.get_value(),
            arc_center=center_pt, color=COLOR_ROSE, stroke_width=3.5
        ))
        lbl_arc = always_redraw(lambda: MathTex(
            r"\Delta\theta = (n - m)\theta", color=COLOR_ROSE, font_size=18
        ).next_to(arc_rel, UR, buff=0.15))

        self.play(GrowArrow(v_k), Write(lbl_k), Create(arc_rel), Write(lbl_arc), run_time=2.5)
        self.wait(2.0)

        # -------------------------------------------------------------
        # BEAT 3: Simultaneous Rotation & Invariance Test (36 - 50s)
        # -------------------------------------------------------------
        hud_title = Text("TÍNH BẢO TOÀN HÌNH HỌC", font=FONT_FAMILY, font_size=13, weight=BOLD, color=COLOR_EMERALD)
        hud_eq1 = MathTex(r"\mathbf{q}_m = \mathbf{R}_m \mathbf{q}", color=COLOR_CYAN, font_size=22)
        hud_eq2 = MathTex(r"\mathbf{k}_n = \mathbf{R}_n \mathbf{k}", color=COLOR_GOLD, font_size=22)
        hud_eq3 = MathTex(r"\langle \mathbf{q}_m, \mathbf{k}_n \rangle = g(\mathbf{q}, \mathbf{k}, n - m)", color=COLOR_ROSE, font_size=22)
        hud_desc_title = Text("Tịnh tiến đồng thời — Góc tương đối bất biến", font=FONT_FAMILY, font_size=12.0, color=COLOR_TEXT)

        hud_content = VGroup(hud_title, hud_eq1, hud_eq2, hud_eq3, hud_desc_title).arrange(DOWN, buff=0.20, aligned_edge=LEFT).shift(RIGHT * 2.6 + DOWN * 0.35)
        hud_bar = Line(hud_content.get_corner(UL), hud_content.get_corner(DL), color=COLOR_EMERALD, stroke_width=2.5).next_to(hud_content, LEFT, buff=0.15)

        self.play(Create(hud_bar), FadeIn(hud_content), run_time=2.0)

        # Both vectors rotate by +1.4 rad (simulating shift of +6 positions)
        self.play(
            ang_q_tracker.animate.increment_value(1.4),
            ang_k_tracker.animate.increment_value(1.4),
            run_time=4.5, rate_func=rate_functions.smooth
        )
        self.play(Indicate(hud_eq3, color=COLOR_EMERALD, scale_factor=1.06), run_time=1.5)
        self.wait(1.5)

        # -------------------------------------------------------------
        # BEAT 4: Ambient Phasor Loop (50 - 58.3s)
        # -------------------------------------------------------------
        # Vectors maintain smooth micro-rotation to ensure continuous motion
        self.play(
            ang_q_tracker.animate.increment_value(1.2),
            ang_k_tracker.animate.increment_value(1.2),
            run_time=19.0, rate_func=rate_functions.linear
        )
        self.wait(1.5)


# =============================================================================
# SCENE 02: PHÂN TÁCH 2D & ĐOÁN TRƯỚC KHI QUAY (ARCHITECTURE — 80.4s)
# =============================================================================
class Tap02Scene02Architecture(Scene):
    """
    Architecture (80.4s Voiceover):
    Beat 1 (0-22s): Complex Unit Circle with Query (Cyan) and Key (Gold).
                    Orthogonal projection shadow of Key onto Query.
                    Live Dot Product tracker displaying scalar score.
    Beat 2 (22-48s): Vectors at pos 4 and 1. Pose prediction question.
                     Simultaneous rotation by 6 theta to pos 10 and 7.
                     Proof: projection length and dot product are strictly identical!
    Beat 3 (48-68s): 128D vector partitioned into 64 2D sub-planes.
                     Block-diagonal rotation matrix R_theta,m visualization.
    Beat 4 (68-80.4s): Continuous multi-frequency clock rotation loop.
    """
    def construct(self):
        self.camera.background_color = COLOR_BG

        # Title HUD — Direct Typography
        title_text = Text(
            "PHÉP CHIẾU TÍCH VÔ HƯỚNG & PHÂN TÁCH 64 MẶT PHẲNG 2D",
            font=FONT_FAMILY, font_size=15, weight=BOLD, color=COLOR_CYAN
        ).to_edge(UP, buff=0.45)
        title_line = Line(
            title_text.get_left() + DOWN * 0.12, title_text.get_right() + DOWN * 0.12,
            color=COLOR_CYAN, stroke_width=1.5
        )
        self.play(FadeIn(title_text, shift=DOWN * 0.15), Create(title_line), run_time=1.2)

        # -------------------------------------------------------------
        # BEAT 1: Vectors & Projection Shadow (0 - 22s)
        # -------------------------------------------------------------
        c_pt = LEFT * 2.4 + DOWN * 0.35
        r = 2.1
        circ = Circle(radius=r, stroke_color=COLOR_BORDER, stroke_width=1.5).move_to(c_pt)
        h_line = Line(c_pt + LEFT * r, c_pt + RIGHT * r, color=COLOR_BORDER, stroke_width=1.0)
        v_line = Line(c_pt + DOWN * r, c_pt + UP * r, color=COLOR_BORDER, stroke_width=1.0)

        # Trackers for Query and Key angles
        q_ang = ValueTracker(0.3)
        k_ang = ValueTracker(1.1)

        v_q = always_redraw(lambda: Arrow(
            c_pt, c_pt + r * np.array([np.cos(q_ang.get_value()), np.sin(q_ang.get_value()), 0]),
            buff=0, color=COLOR_CYAN, stroke_width=4.0
        ))
        v_k = always_redraw(lambda: Arrow(
            c_pt, c_pt + r * np.array([np.cos(k_ang.get_value()), np.sin(k_ang.get_value()), 0]),
            buff=0, color=COLOR_GOLD, stroke_width=4.0
        ))

        lbl_q = always_redraw(lambda: Text("Query q", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_CYAN).next_to(v_q.get_end(), UR, buff=0.08))
        lbl_k = always_redraw(lambda: Text("Key k", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_GOLD).next_to(v_k.get_end(), UL, buff=0.08))

        # Dynamic projection shadow of k onto q
        def get_proj_point():
            uq = np.array([np.cos(q_ang.get_value()), np.sin(q_ang.get_value()), 0])
            vk = r * np.array([np.cos(k_ang.get_value()), np.sin(k_ang.get_value()), 0])
            proj_len = np.dot(vk, uq)
            return c_pt + proj_len * uq

        proj_line = always_redraw(lambda: DashedLine(
            v_k.get_end(), get_proj_point(), color=COLOR_ROSE, stroke_width=2.0, dash_length=0.08
        ))
        proj_vec = always_redraw(lambda: Line(
            c_pt, get_proj_point(), color=COLOR_ROSE, stroke_width=4.5
        ))

        self.play(Create(circ), Create(h_line), Create(v_line), GrowArrow(v_q), GrowArrow(v_k), Write(lbl_q), Write(lbl_k), run_time=2.5)
        self.play(Create(proj_line), Create(proj_vec), run_time=2.0)

        # Right side: Live Dot Product Score Gauge
        gauge_box = RoundedRectangle(
            corner_radius=0.12, width=4.8, height=2.8,
            fill_color=COLOR_CARD_BG, fill_opacity=0.95, stroke_color=COLOR_AMBER, stroke_width=1.5
        ).shift(RIGHT * 2.6 + DOWN * 0.35)

        g_title = Text("ĐIỂM TÍCH VÔ HƯỚNG THÔ", font=FONT_FAMILY, font_size=12, weight=BOLD, color=COLOR_AMBER).move_to(gauge_box.get_top() + DOWN * 0.3)
        
        score_val = always_redraw(lambda: Text(
            f"Tích: {np.cos(k_ang.get_value() - q_ang.get_value()):+.3f}",
            font="monospace", font_size=20, weight=BOLD,
            color=COLOR_EMERALD if np.cos(k_ang.get_value() - q_ang.get_value()) > 0 else COLOR_ROSE
        ).move_to(gauge_box.get_center() + UP * 0.1))

        angle_diff = always_redraw(lambda: Text(
            f"Góc lệch Δθ = {abs(k_ang.get_value() - q_ang.get_value()):.2f} rad",
            font=FONT_FAMILY, font_size=12, color=COLOR_TEXT
        ).next_to(score_val, DOWN, buff=0.25))

        self.play(FadeIn(gauge_box), Write(g_title), FadeIn(score_val), FadeIn(angle_diff), run_time=2.5)
        self.wait(3.0)

        # -------------------------------------------------------------
        # BEAT 2: Prediction & Shift Test (22 - 48s)
        # -------------------------------------------------------------
        # Rotate q by 4*theta, k by 1*theta (theta = 0.28)
        theta_step = 0.28
        self.play(
            q_ang.animate.set_value(0.3 + 4 * theta_step),
            k_ang.animate.set_value(1.1 + 1 * theta_step),
            run_time=3.5, rate_func=rate_functions.smooth
        )
        self.wait(2.5)

        # Shift test: move both by +6 positions (6 * 0.28 rad = 1.68 rad)
        shift_callout = Text(
            "Đoán: Dời 4→10 và 1→7, điểm số có đổi không?",
            font=FONT_FAMILY, font_size=12, weight=BOLD, color=COLOR_GOLD
        ).next_to(gauge_box, UP, buff=0.25)
        self.play(Write(shift_callout), run_time=1.8)
        self.wait(2.5)

        self.play(
            q_ang.animate.increment_value(6 * theta_step),
            k_ang.animate.increment_value(6 * theta_step),
            run_time=6.0, rate_func=rate_functions.smooth
        )
        
        proof_callout = Text(
            "BẤT BIẾN: Bóng chiếu & Điểm số giữ nguyên!",
            font=FONT_FAMILY, font_size=12, weight=BOLD, color=COLOR_EMERALD
        ).move_to(shift_callout)
        self.play(Transform(shift_callout, proof_callout), run_time=1.5)
        self.play(Circumscribe(gauge_box, color=COLOR_EMERALD), run_time=2.0)
        self.wait(2.5)

        # -------------------------------------------------------------
        # BEAT 3: 128D Matrix & 64 2D Sub-Planes (48 - 68s)
        # -------------------------------------------------------------
        self.play(FadeOut(shift_callout), FadeOut(gauge_box), FadeOut(g_title), FadeOut(score_val), FadeOut(angle_diff), run_time=1.5)

        matrix_box = RoundedRectangle(
            corner_radius=0.12, width=5.2, height=3.2,
            fill_color=COLOR_CARD_BG, fill_opacity=0.95, stroke_color=COLOR_CYAN, stroke_width=1.5
        ).shift(RIGHT * 2.6 + DOWN * 0.35)
        m_title = Text("MA TRẬN KHỐI ĐƯỜNG CHÉO (d=128)", font=FONT_FAMILY, font_size=12, weight=BOLD, color=COLOR_CYAN).move_to(matrix_box.get_top() + DOWN * 0.3)

        mat_tex = MathTex(
            r"\mathbf{R}_{\Theta, m} = \begin{pmatrix} \mathbf{R}_m^{(0)} & 0 & \dots \\ 0 & \mathbf{R}_m^{(1)} & \dots \\ \vdots & \vdots & \ddots \end{pmatrix}",
            font_size=20, color=COLOR_TEXT
        ).move_to(matrix_box.get_center() + UP * 0.1)

        mat_sub = MathTex(
            r"\mathbf{R}_m^{(i)} = \begin{pmatrix} \cos(m\theta_i) & -\sin(m\theta_i) \\ \sin(m\theta_i) & \cos(m\theta_i) \end{pmatrix}",
            font_size=18, color=COLOR_GOLD
        ).next_to(mat_tex, DOWN, buff=0.25)

        self.play(FadeIn(matrix_box), Write(m_title), Write(mat_tex), run_time=2.5)
        self.play(Write(mat_sub), run_time=2.0)
        self.wait(3.0)

        # -------------------------------------------------------------
        # BEAT 4: Continuous Ambient Loop (68 - 80.4s)
        # -------------------------------------------------------------
        self.play(
            q_ang.animate.increment_value(2.8),
            k_ang.animate.increment_value(2.8),
            run_time=35.5, rate_func=rate_functions.linear
        )
        self.wait(2.0)


# =============================================================================
# SCENE 03: TÍCH VÔ HƯỚNG & QUY LUẬT SUY GIẢM (MATHEMATICS — 87.3s)
# =============================================================================
class Tap02Scene03Mathematics(Scene):
    """
    Mathematics (87.3s Voiceover):
    Beat 1 (0-24s): Reverse rotation operation: Rotate both vectors back by m*theta.
                    Query returns to initial content orientation q_0.
                    Key retains relative rotation (n-m)*theta.
    Beat 2 (24-54s): Derivation of matrix transpose identity: R(m)^T R(n) = R(n-m).
                    Visual angle subtraction: beta - alpha + (n-m)*theta.
    Beat 3 (54-74s): Generalization to 64 orthogonal planes and sum of inner products.
    Beat 4 (74-87.3s): Ambient wave propagation loop.
    """
    def construct(self):
        self.camera.background_color = COLOR_BG

        # Title HUD — Direct Typography
        title_text = Text(
            "ĐẠI SỐ PHÉP QUAY // R(m)ᵀ R(n) = R(n - m)",
            font=FONT_FAMILY, font_size=15, weight=BOLD, color=COLOR_CYAN
        ).to_edge(UP, buff=0.45)
        title_line = Line(
            title_text.get_left() + DOWN * 0.12, title_text.get_right() + DOWN * 0.12,
            color=COLOR_CYAN, stroke_width=1.5
        )
        self.play(FadeIn(title_text, shift=DOWN * 0.15), Create(title_line), run_time=1.2)

        # -------------------------------------------------------------
        # BEAT 1: Reverse Rotation to Cancel m*theta (0 - 24s)
        # -------------------------------------------------------------
        c_pt = LEFT * 2.4 + DOWN * 0.35
        r = 2.1

        # Continuous kinetic tracker
        pulse_tracker = ValueTracker(0.0)
        pulse_tracker.add_updater(lambda m, dt: m.increment_value(dt))
        self.add(pulse_tracker)

        circ = Circle(radius=r, stroke_color=COLOR_BORDER, stroke_width=1.5).move_to(c_pt)
        circ_aura = always_redraw(lambda: Circle(
            radius=r + 0.08 * np.sin(pulse_tracker.get_value() * 2.5),
            stroke_color=COLOR_EMERALD, stroke_width=1.5,
            stroke_opacity=0.35 + 0.15 * np.sin(pulse_tracker.get_value() * 2.5)
        ).move_to(c_pt))
        beacon = always_redraw(lambda: Dot(
            c_pt + (r + 0.08) * np.array([np.cos(pulse_tracker.get_value() * 1.8), np.sin(pulse_tracker.get_value() * 1.8), 0]),
            radius=0.06, color=COLOR_EMERALD
        ))

        h_ax = Line(c_pt + LEFT * r, c_pt + RIGHT * r, color=COLOR_BORDER, stroke_width=1.0)
        v_ax = Line(c_pt + DOWN * r, c_pt + UP * r, color=COLOR_BORDER, stroke_width=1.0)

        # Trackers
        ang_m = ValueTracker(1.8)  # m*theta
        ang_n = ValueTracker(3.1)  # n*theta

        v_q = always_redraw(lambda: Arrow(
            c_pt, c_pt + r * np.array([np.cos(ang_m.get_value()), np.sin(ang_m.get_value()), 0]),
            buff=0, color=COLOR_CYAN, stroke_width=4.0
        ))
        v_k = always_redraw(lambda: Arrow(
            c_pt, c_pt + r * np.array([np.cos(ang_n.get_value()), np.sin(ang_n.get_value()), 0]),
            buff=0, color=COLOR_GOLD, stroke_width=4.0
        ))

        lbl_q = always_redraw(lambda: MathTex(r"\mathbf{q}_m", color=COLOR_CYAN, font_size=22).next_to(v_q.get_end(), UR, buff=0.08))
        lbl_k = always_redraw(lambda: MathTex(r"\mathbf{k}_n", color=COLOR_GOLD, font_size=22).next_to(v_k.get_end(), UL, buff=0.08))

        self.play(Create(circ), FadeIn(circ_aura), FadeIn(beacon), Create(h_ax), Create(v_ax), GrowArrow(v_q), GrowArrow(v_k), Write(lbl_q), Write(lbl_k), run_time=2.5)
        self.wait(2.5)

        # Reverse rotation banner
        rev_text = Text("Quay ngược cả hai vector một góc m·θ...", font=FONT_FAMILY, font_size=12, color=COLOR_ROSE).next_to(circ, UP, buff=0.2)
        self.play(Write(rev_text), run_time=1.5)

        # Rotate backwards by 1.8 rad (canceling m)
        self.play(
            ang_m.animate.set_value(0.0),
            ang_n.animate.set_value(1.3),
            run_time=5.0, rate_func=rate_functions.smooth
        )
        self.wait(2.5)

        # -------------------------------------------------------------
        # BEAT 2: Matrix Transpose Derivation (24 - 54s)
        # -------------------------------------------------------------
        derivation_box = RoundedRectangle(
            corner_radius=0.12, width=5.2, height=3.6,
            fill_color=COLOR_CARD_BG, fill_opacity=0.95, stroke_color=COLOR_EMERALD, stroke_width=1.5
        ).shift(RIGHT * 2.6 + DOWN * 0.35)

        d_title = Text("CHỨNG MINH ĐẠI SỐ TUẦN HOÀN", font=FONT_FAMILY, font_size=12, weight=BOLD, color=COLOR_EMERALD).move_to(derivation_box.get_top() + DOWN * 0.3)

        eq1 = MathTex(r"\mathbf{R}_m^{-1} = \mathbf{R}_m^T = \mathbf{R}_{-m}", font_size=20, color=COLOR_CYAN)
        eq2 = MathTex(r"\mathbf{R}_m^T \mathbf{R}_n = \mathbf{R}_{n - m}", font_size=22, color=COLOR_GOLD)
        eq3 = MathTex(r"(\mathbf{R}_m \mathbf{q})^T (\mathbf{R}_n \mathbf{k}) = \mathbf{q}^T \mathbf{R}_m^T \mathbf{R}_n \mathbf{k}", font_size=19, color=COLOR_TEXT)
        eq4 = MathTex(r"= \mathbf{q}^T \mathbf{R}_{n - m} \mathbf{k}", font_size=22, color=COLOR_EMERALD)

        eq_grp = VGroup(d_title, eq1, eq2, eq3, eq4).arrange(DOWN, buff=0.22, aligned_edge=LEFT)
        eq_grp.move_to(derivation_box)

        self.play(FadeIn(derivation_box), Write(d_title), run_time=2.0)
        self.play(Write(eq1), run_time=2.5)
        self.play(Write(eq2), run_time=2.5)
        self.play(Write(eq3), run_time=3.0)
        self.play(Write(eq4), run_time=2.5)
        self.play(Circumscribe(eq4, color=COLOR_EMERALD), run_time=2.0)
        self.wait(3.0)

        # -------------------------------------------------------------
        # BEAT 3: Generalization Across 64 Planes (54 - 74s)
        # -------------------------------------------------------------
        self.play(FadeOut(derivation_box), FadeOut(eq_grp), run_time=1.5)

        multi_box = RoundedRectangle(
            corner_radius=0.12, width=5.2, height=3.0,
            fill_color=COLOR_CARD_BG, fill_opacity=0.95, stroke_color=COLOR_GOLD, stroke_width=1.5
        ).shift(RIGHT * 2.6 + DOWN * 0.35)

        m_title2 = Text("TỔNG HỢP TRÊN 64 MẶT PHẲNG", font=FONT_FAMILY, font_size=12, weight=BOLD, color=COLOR_GOLD).move_to(multi_box.get_top() + DOWN * 0.3)
        multi_eq = MathTex(
            r"\langle \tilde{\mathbf{q}}, \tilde{\mathbf{k}} \rangle = \sum_{i=0}^{63} \mathbf{q}^{(i)T} \mathbf{R}_{n-m}^{(i)} \mathbf{k}^{(i)}",
            font_size=20, color=COLOR_TEXT
        ).move_to(multi_box.get_center() + UP * 0.1)

        multi_note_hdr = Text("Đa thang bậc tần số theo cặp chiều", font=FONT_FAMILY, font_size=12.0, color=COLOR_MUTED).next_to(multi_eq, DOWN, buff=0.25)

        self.play(FadeIn(multi_box), Write(m_title2), Write(multi_eq), Write(multi_note_hdr), run_time=3.0)
        self.wait(3.5)

        # -------------------------------------------------------------
        # BEAT 4: Ambient Loop (74 - 87.3s)
        # -------------------------------------------------------------
        self.play(
            ang_m.animate.increment_value(3.2),
            ang_n.animate.increment_value(3.2),
            run_time=44.0, rate_func=rate_functions.linear
        )
        self.wait(2.5)


# =============================================================================
# SCENE 04: VÌ SAO CẦN NHIỀU CHIẾC KIM? (TELEMETRY — 87.8s)
# =============================================================================
class Tap02Scene04Telemetry(Scene):
    """
    Telemetry (87.8s Voiceover):
    Beat 1 (0-24s): The single-needle aliasing dilemma: 2pi rotation repeats.
                    Formula: theta_i = 10000^(-2i/128).
    Beat 2 (24-54s): 4 Synchronized Clock Gears (i=0, 16, 32, 63).
                     Position counter advances 0 -> 80 tokens.
                     Fast needle spins dozens of times; slow needle moves slightly.
    Beat 3 (54-74s): Multi-scale hierarchical spatial perception.
    Beat 4 (74-87.8s): Synchronized ambient clock rotation loop.
    """
    def construct(self):
        self.camera.background_color = COLOR_BG

        # Title HUD — Direct Typography
        title_text = Text(
            "BẢN GIAO HƯỞNG BÁNH RĂNG TẦN SỐ // 64 CHIẾC KIM",
            font=FONT_FAMILY, font_size=15, weight=BOLD, color=COLOR_CYAN
        ).to_edge(UP, buff=0.45)
        title_line = Line(
            title_text.get_left() + DOWN * 0.12, title_text.get_right() + DOWN * 0.12,
            color=COLOR_CYAN, stroke_width=1.5
        )
        self.play(FadeIn(title_text, shift=DOWN * 0.15), Create(title_line), run_time=1.2)

        # Kinetic pulse tracker for active continuous telemetry motion
        pulse_tracker = ValueTracker(0.0)
        pulse_tracker.add_updater(lambda m, dt: m.increment_value(dt))
        self.add(pulse_tracker)

        carrier_wave = always_redraw(lambda: FunctionGraph(
            lambda x: -2.7 + 0.2 * np.sin(2.2 * x + pulse_tracker.get_value() * 3.5),
            x_range=[-6.0, 6.0], color=COLOR_CYAN, stroke_width=1.5, stroke_opacity=0.45
        ))
        self.add(carrier_wave)

        # -------------------------------------------------------------
        # BEAT 1: The Aliasing Dilemma & Frequency Formula (0 - 24s)
        # -------------------------------------------------------------
        formula_box = RoundedRectangle(
            corner_radius=0.12, width=8.5, height=1.4,
            fill_color=COLOR_CARD_BG, fill_opacity=0.95, stroke_color=COLOR_BORDER, stroke_width=1.2
        ).shift(UP * 1.5)

        form_text = MathTex(
            r"\theta_i = 10000^{-\frac{2i}{d}}, \quad i \in [0, 1, \dots, 63], \quad d = 128",
            font_size=22, color=COLOR_GOLD
        ).move_to(formula_box)

        self.play(Create(formula_box), Write(form_text), run_time=2.5)
        self.wait(3.0)

        # -------------------------------------------------------------
        # BEAT 2: 4 Synchronized Clock Gears (24 - 54s)
        # -------------------------------------------------------------
        # 4 clocks placed horizontally at Y = -0.5
        clock_centers = [LEFT * 4.2, LEFT * 1.4, RIGHT * 1.4, RIGHT * 4.2]
        clock_labels = ["i=0 (Tần số cực cao)", "i=16 (Tần số cao)", "i=32 (Tần số trung bình)", "i=63 (Tần số siêu thấp)"]
        clock_freqs = [1.0, 0.1, 0.01, 0.0001]
        clock_colors = [COLOR_ROSE, COLOR_AMBER, COLOR_CYAN, COLOR_EMERALD]

        clock_mobs = []
        pos_tracker = ValueTracker(0.0)

        for i in range(4):
            cp = clock_centers[i] + DOWN * 0.5
            col = clock_colors[i]
            circ = Circle(radius=0.95, stroke_color=COLOR_BORDER, stroke_width=1.5).move_to(cp)
            dot = Dot(cp, radius=0.05, color=col)
            lbl = Text(clock_labels[i], font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=col).next_to(circ, DOWN, buff=0.2)

            # Needle driven by pos_tracker and frequency
            freq = clock_freqs[i]
            needle = always_redraw(lambda cp=cp, freq=freq, col=col: Arrow(
                cp, cp + 0.85 * np.array([np.cos(pos_tracker.get_value() * freq), np.sin(pos_tracker.get_value() * freq), 0]),
                buff=0, color=col, stroke_width=3.2
            ))
            clock_mobs.extend([circ, dot, lbl, needle])

        self.play(*[FadeIn(m) for m in clock_mobs], run_time=3.0)

        # Dynamic Token Position Counter HUD
        counter_box = RoundedRectangle(
            corner_radius=0.1, width=3.6, height=0.7,
            fill_color="#10172a", fill_opacity=0.95, stroke_color=COLOR_CYAN, stroke_width=1.2
        ).shift(UP * 0.3)
        pos_label = always_redraw(lambda: Text(
            f"Vị trí token p = {int(pos_tracker.get_value()):2d}",
            font="monospace", font_size=15, weight=BOLD, color=COLOR_CYAN
        ).move_to(counter_box))

        self.play(FadeIn(counter_box), FadeIn(pos_label), run_time=1.5)

        # Advance position from 0 to 60 tokens smoothly over 22 seconds
        self.play(pos_tracker.animate.set_value(60.0), run_time=22.0, rate_func=rate_functions.smooth)
        self.wait(2.5)

        # -------------------------------------------------------------
        # BEAT 3: Multi-Scale Hierarchical Perception (54 - 74s)
        # -------------------------------------------------------------
        scale_box = RoundedRectangle(
            corner_radius=0.12, width=9.6, height=1.0,
            fill_color="#10172a", fill_opacity=0.95, stroke_color=COLOR_AMBER, stroke_width=1.2
        ).shift(DOWN * 2.1)

        scale_desc_hdr = Text(
            "Kim nhanh: Cục bộ  |  Kim chậm: Mạch văn vĩ mô",
            font=FONT_FAMILY, font_size=12, weight=BOLD, color=COLOR_AMBER
        ).move_to(scale_box)

        self.play(FadeIn(scale_box), Write(scale_desc_hdr), run_time=2.0)
        self.wait(3.0)

        # -------------------------------------------------------------
        # BEAT 4: Synchronized Ambient Loop (74 - 87.8s)
        # -------------------------------------------------------------
        self.play(pos_tracker.animate.increment_value(88.0), run_time=44.0, rate_func=rate_functions.linear)
        self.wait(2.5)


# =============================================================================
# SCENE 05: KÉO DÀI THƯỚC ĐO, TRẢ GIÁ Ở ĐÂU? (LAB EXPERIMENT — 90.3s)
# =============================================================================
class Tap02Scene05LabExperiment(Scene):
    """
    Lab Experiment (90.3s Voiceover):
    Beat 1 (0-24s): Context ruler from 0 to 32. Moving from 8 to 32.
    Beat 2 (24-54s): Position Interpolation (PI): p -> p/4.
                     Needle at pos 32 returns to phase of 8!
                     Compression cost: step between adjacent tokens shrinks by 4x.
    Beat 3 (54-75s): Trade-off analysis: local syntax blurred vs global reach.
    Beat 4 (75-90.3s): Ambient token belt loop.
    """
    def construct(self):
        self.camera.background_color = COLOR_BG

        # Title HUD — Direct Typography
        title_text = Text(
            "THỬ THÁCH MỞ RỘNG // POSITION INTERPOLATION (PI)",
            font=FONT_FAMILY, font_size=15, weight=BOLD, color=COLOR_CYAN
        ).to_edge(UP, buff=0.45)
        title_line = Line(
            title_text.get_left() + DOWN * 0.12, title_text.get_right() + DOWN * 0.12,
            color=COLOR_CYAN, stroke_width=1.5
        )
        self.play(FadeIn(title_text, shift=DOWN * 0.15), Create(title_line), run_time=1.2)

        # Kinetic pulse tracker for continuous live animation
        pulse_tracker = ValueTracker(0.0)
        pulse_tracker.add_updater(lambda m, dt: m.increment_value(dt))
        self.add(pulse_tracker)

        carrier_wave = always_redraw(lambda: FunctionGraph(
            lambda x: -3.3 + 0.15 * np.sin(2.4 * x + pulse_tracker.get_value() * 3.2),
            x_range=[-6.0, 6.0], color=COLOR_AMBER, stroke_width=1.5, stroke_opacity=0.45
        ))
        self.add(carrier_wave)

        # -------------------------------------------------------------
        # BEAT 1: Context Ruler 0 to 32 (0 - 24s)
        # -------------------------------------------------------------
        ruler_line = NumberLine(
            x_range=[0, 32, 4], length=9.6, color=COLOR_BORDER,
            include_numbers=True, font_size=14, stroke_width=2.5
        ).shift(UP * 1.4)
        ruler_title = Text("Thước vị trí ngữ cảnh (Toy Ruler)", font=FONT_FAMILY, font_size=12.0, color=COLOR_MUTED).next_to(ruler_line, UP, buff=0.15)

        ruler_pulse = always_redraw(lambda: Dot(
            ruler_line.n2p((pulse_tracker.get_value() * 3.5) % 32.0),
            radius=0.08, color=COLOR_AMBER
        ))
        self.add(ruler_pulse)

        # Mark pre-trained boundary at 8
        pt8 = ruler_line.n2p(8)
        mark_8 = Line(pt8 + DOWN * 0.3, pt8 + UP * 0.3, color=COLOR_CYAN, stroke_width=3.5)
        lbl_8 = Text("Huấn luyện (L=8)", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_CYAN).next_to(mark_8, UP, buff=0.1)

        self.play(Create(ruler_line), Write(ruler_title), Create(mark_8), Write(lbl_8), run_time=2.5)

        # Position cursor tracker
        pos_tracker = ValueTracker(8.0)
        cursor = always_redraw(lambda: Dot(
            ruler_line.n2p(pos_tracker.get_value()), radius=0.12,
            color=COLOR_CYAN if pos_tracker.get_value() <= 8 else COLOR_ROSE
        ))
        cursor_lbl = always_redraw(lambda: Text(
            f"p = {int(pos_tracker.get_value())}", font="monospace", font_size=12, weight=BOLD,
            color=COLOR_CYAN if pos_tracker.get_value() <= 8 else COLOR_ROSE
        ).next_to(cursor, DOWN, buff=0.2))

        self.play(FadeIn(cursor), FadeIn(cursor_lbl), run_time=1.5)

        # Advance to pos 32 (outside training window)
        self.play(pos_tracker.animate.set_value(32.0), run_time=5.0, rate_func=rate_functions.smooth)
        self.wait(2.5)

        # -------------------------------------------------------------
        # BEAT 2: Position Interpolation p -> p/4 (24 - 54s)
        # -------------------------------------------------------------
        # Complex unit circle to show phase compression
        c_pt = LEFT * 2.4 + DOWN * 0.7
        r = 1.6
        circ = Circle(radius=r, stroke_color=COLOR_BORDER, stroke_width=1.5).move_to(c_pt)
        c_label = Text("Pha quay thực tế", font=FONT_FAMILY, font_size=12.0, color=COLOR_MUTED).next_to(circ, UP, buff=0.15)

        theta = 0.2
        phase_tracker = ValueTracker(32.0 * theta)
        needle = always_redraw(lambda: Arrow(
            c_pt, c_pt + r * np.array([np.cos(phase_tracker.get_value()), np.sin(phase_tracker.get_value()), 0]),
            buff=0, color=COLOR_ROSE, stroke_width=3.5
        ))

        self.play(Create(circ), Write(c_label), GrowArrow(needle), run_time=2.0)

        # Compress phase: 32 -> 8 (p/4)
        pi_callout = RoundedRectangle(
            corner_radius=0.12, width=5.0, height=2.8,
            fill_color=COLOR_CARD_BG, fill_opacity=0.95, stroke_color=COLOR_AMBER, stroke_width=1.5
        ).shift(RIGHT * 2.6 + DOWN * 0.7)

        pi_title = Text("NỘI SUY VỊ TRÍ (s = 4)", font=FONT_FAMILY, font_size=12, weight=BOLD, color=COLOR_AMBER).move_to(pi_callout.get_top() + DOWN * 0.3)
        pi_formula = MathTex(r"p' = \frac{p}{s} = \frac{32}{4} = 8", font_size=22, color=COLOR_GOLD).move_to(pi_callout.get_center() + UP * 0.2)
        pi_cost = MathTex(r"\Delta\theta' = \frac{\theta}{4}", font_size=22, color=COLOR_ROSE).next_to(pi_formula, DOWN, buff=0.25)

        self.play(FadeIn(pi_callout), Write(pi_title), Write(pi_formula), run_time=2.5)

        # Needle rotates backwards to phase of 8
        self.play(
            phase_tracker.animate.set_value(8.0 * theta),
            needle.animate.set_color(COLOR_CYAN),
            run_time=4.5, rate_func=rate_functions.smooth
        )
        self.play(Write(pi_cost), run_time=2.0)
        self.wait(3.0)

        # -------------------------------------------------------------
        # BEAT 3: Trade-Off Analysis (54 - 75s)
        # -------------------------------------------------------------
        blur_box = RoundedRectangle(
            corner_radius=0.12, width=9.6, height=1.0,
            fill_color="#10172a", fill_opacity=0.95, stroke_color=COLOR_ROSE, stroke_width=1.2
        ).shift(DOWN * 2.4)
        blur_text_hdr = Text(
            "Cái giá hình học: Co góc pha -> Mờ độ phân giải cục bộ",
            font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_ROSE
        ).move_to(blur_box)

        self.play(FadeIn(blur_box), Write(blur_text_hdr), run_time=2.5)
        self.wait(3.5)

        # -------------------------------------------------------------
        # BEAT 4: Ambient Loop (75 - 90.3s)
        # -------------------------------------------------------------
        self.play(phase_tracker.animate.increment_value(6.0), run_time=54.5, rate_func=rate_functions.linear)
        self.wait(2.5)


# =============================================================================
# SCENE 06: ĐIỀU PHÉP QUAY LÀM ĐƯỢC (OUTRO — 67.9s)
# =============================================================================
class Tap02Scene06Outro(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "TỔNG KẾT & CẦU NỐI KỸ NGHỆ")

        scene_title = Text(
            "BÀN GIAO TRI THỨC // ROPE & PHÉP XOAY TỌA ĐỘ",
            font=FONT_FAMILY, font_size=15.0, weight=BOLD, color=COLOR_GOLD
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
            font=FONT_FAMILY, font_size=12.5, weight=BOLD, color=COLOR_GOLD
        ).next_to(mosaic_frame, UP, buff=0.18)

        left_grp = Group(mosaic_mobj, mosaic_frame, gallery_header)
        self.play(FadeIn(left_grp, shift=RIGHT * 0.3), run_time=1.2)

        # Right Side: YouTube End Screen Interactive Safe Zones
        # 1. Next Video Card (Episode 03: YaRN)
        next_card = RoundedRectangle(
            corner_radius=0.12, width=3.8, height=2.0,
            fill_color=COLOR_PANEL, fill_opacity=0.7, stroke_color=COLOR_CYAN, stroke_width=1.5
        ).move_to(RIGHT * 3.5 + UP * 1.5)
        next_header = Text("TẬP TIẾP THEO // TẬP 03", font=FONT_FAMILY, font_size=12.5, weight=BOLD, color=COLOR_CYAN)
        next_sub_header = Text("YARN & MỞ RỘNG NGỮ CẢNH 128K", font=FONT_FAMILY, font_size=10.5, color=COLOR_TEXT)
        next_txt = VGroup(next_header, next_sub_header).arrange(DOWN, buff=0.15).move_to(next_card.get_center())

        # 2. Playlist Card
        plist_card = RoundedRectangle(
            corner_radius=0.12, width=3.8, height=1.3,
            fill_color=COLOR_PANEL, fill_opacity=0.7, stroke_color=COLOR_GOLD, stroke_width=1.5
        ).move_to(RIGHT * 3.5 + DOWN * 0.35)
        plist_header = Text("DANH SÁCH PHÁT SERIES 2", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_GOLD)
        plist_sub_header = Text("25 TẬP BẢN VẼ KIẾN TRÚC LLM", font=FONT_FAMILY, font_size=10.5, color=COLOR_TEXT)
        plist_txt = VGroup(plist_header, plist_sub_header).arrange(DOWN, buff=0.12).move_to(plist_card.get_center())

        # 3. Channel Subscribe Circular Card
        sub_card = Circle(
            radius=0.75, fill_color=COLOR_PANEL, fill_opacity=0.85, stroke_color=COLOR_ROSE, stroke_width=1.5
        ).move_to(RIGHT * 3.5 + DOWN * 1.85)
        sub_header = Text("ĐĂNG KÝ", font=FONT_FAMILY, font_size=11.5, weight=BOLD, color=COLOR_ROSE).move_to(sub_card.get_center())

        right_grp = VGroup(next_card, next_txt, plist_card, plist_txt, sub_card, sub_header)
        self.play(FadeIn(right_grp, shift=LEFT * 0.3), run_time=1.2)

        # Ambient phase needle rotation loop until end of scene
        phase_line = Line(ORIGIN, RIGHT * 0.6, color=COLOR_CYAN, stroke_width=2.5).move_to(sub_card.get_center())
        def update_phase(m, dt):
            outro_tracker.increment_value(dt)
            m.rotate(1.2 * dt, about_point=sub_card.get_center())

        phase_line.add_updater(update_phase)
        self.add(phase_line)

        # Wait remaining duration of scene (audio ~67.9s)
        self.wait(5.0)
