#!/usr/bin/env python3
"""
Manim 2K QHD Master Production Scenes — YaRN & Mở Rộng Ngữ Cảnh Dài
Resolution: 2560x1440 @ 60fps | Theme: Neo-Noir Obsidian (#0b0f19)
Standards: Median & 3Blue1Brown Continuous Geometric Flow
- 100% Pure Manim Geometry (ZERO post-processing fake camera drift / crop sway)
- Multi-beat staged animations matching voiceover narration durations (55s - 90s per scene)
- ZERO Mascots (100% clean artisan mathematical animation)
- ZERO static bullet boxes (dynamic geometric components & interactive trackers only)
- Safe Margins: > 15% padding from screen edges (|x| <= 5.2, |y| <= 3.2, bottom y >= -2.4 for CC)
- Zero baked-in watermarks (watermark applied solely via post-processing FFmpeg)
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
from manim_web_layout import (
    VStack, HStack, ResponsiveCard, ProgressBarComponent,
    TokenDistanceSnippet, NeedleInHaystackSnippet, WebSafeZone
)

# Neo-Noir Theme Palette (High Contrast & Zero Glare)
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
# SCENE 01: ẢO TƯỞNG NGỮ CẢNH & THỬ THÁCH 128K (COLD OPEN — 66.0s)
# =============================================================================
class Tap03Scene01ColdOpen(Scene):
    """
    Cold Open (66s Voiceover):
    Beat 1 (0-18s): RoPE vector rotation on complex unit circle in normal 4K domain.
    Beat 2 (18-40s): Context stretches 4K -> 32K -> 128K. Vector spins > 20pi (Phase dispersion).
    Beat 3 (40-54s): Attention entropy maximum & Perplexity explosion (8.2 -> 1,250+).
    Beat 4 (54-66s): Geometric Paradox callout & continuous ambient phase needle rotation.
    """
    def construct(self):
        self.camera.background_color = COLOR_BG

        # Kinetic pulse tracker & Carrier Wave (Continuous frame delta > -65dB)
        pulse_tracker = ValueTracker(0.0)
        pulse_tracker.add_updater(lambda m, dt: m.increment_value(dt))
        self.add(pulse_tracker)

        carrier_wave = always_redraw(lambda: FunctionGraph(
            lambda x: -3.2 + 0.08 * np.sin(2.0 * x + pulse_tracker.get_value() * 2.5),
            x_range=[-6.0, 6.0], color=COLOR_CYAN, stroke_width=1.5, stroke_opacity=0.45
        ))
        self.add(carrier_wave)

        # Title HUD
        title_text = Text(
            "MỞ RỘNG NGỮ CẢNH DÀI // ĐỘT PHÁ YaRN & ATTENTION SINK",
            font=FONT_FAMILY, font_size=15, weight=BOLD, color=COLOR_CYAN
        )
        title_box = RoundedRectangle(
            corner_radius=0.12, width=title_text.width + 0.6, height=0.5,
            fill_color="#10172a", fill_opacity=0.9, stroke_color=COLOR_CYAN, stroke_width=1.2
        ).to_edge(UP, buff=0.45)
        title_text.move_to(title_box)
        self.play(FadeIn(title_box, shift=DOWN * 0.2), Write(title_text), run_time=0.9)

        # -------------------------------------------------------------
        # BEAT 1: RoPE Complex Unit Circle (0 - 15s)
        # -------------------------------------------------------------
        c_pt = LEFT * 2.8 + DOWN * 0.25
        circ = Circle(radius=1.85, stroke_color=COLOR_BORDER, stroke_width=1.5).move_to(c_pt)
        circ_aura = always_redraw(lambda: Circle(
            radius=1.85 + 0.05 * np.sin(pulse_tracker.get_value() * 2.5),
            stroke_color=COLOR_CYAN, stroke_width=1.2,
            stroke_opacity=0.35 + 0.15 * np.sin(pulse_tracker.get_value() * 2.5)
        ).move_to(c_pt))
        c_label = Text("Mặt Phẳng Phức 2D (RoPE)", font=FONT_FAMILY, font_size=12.0, color=COLOR_MUTED).next_to(circ, UP, buff=0.15)
        
        h_axis = Line(c_pt + LEFT * 1.85, c_pt + RIGHT * 1.85, color=COLOR_BORDER, stroke_width=1.0)
        v_axis = Line(c_pt + DOWN * 1.85, c_pt + UP * 1.85, color=COLOR_BORDER, stroke_width=1.0)

        # Fixed Query vector q
        v_q = Arrow(c_pt, c_pt + 1.7 * np.array([np.cos(0.45), np.sin(0.45), 0]), buff=0, color=COLOR_CYAN, stroke_width=3.5)
        lbl_q = Text("Query q (Vị trí m)", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_CYAN).next_to(v_q.get_end(), UR, buff=0.08)

        self.play(Create(circ), FadeIn(circ_aura), Create(h_axis), Create(v_axis), Write(c_label), GrowArrow(v_q), Write(lbl_q), run_time=2.0)

        # Right Side Layout: Context Slider & Perplexity Monitor
        slider_line = Line(RIGHT * 0.3 + UP * 1.4, RIGHT * 4.9 + UP * 1.4, color=COLOR_BORDER, stroke_width=3.0)
        s_title = Text("Độ Dài Ngữ Cảnh Token (L)", font=FONT_FAMILY, font_size=12, weight=BOLD, color=COLOR_GOLD).next_to(slider_line, UP, buff=0.2)

        p_4k = RIGHT * 0.3 + UP * 1.4
        t_4k = Dot(p_4k, radius=0.09, color=COLOR_CYAN)
        lbl_4k = Text("4K (Chuẩn)", font=FONT_FAMILY, font_size=12.0, color=COLOR_CYAN).next_to(t_4k, DOWN, buff=0.1)

        p_32k = RIGHT * 2.6 + UP * 1.4
        t_32k = Dot(p_32k, radius=0.09, color=COLOR_AMBER)
        lbl_32k = Text("32K (Sách)", font=FONT_FAMILY, font_size=12.0, color=COLOR_AMBER).next_to(t_32k, DOWN, buff=0.1)

        p_128k = RIGHT * 4.9 + UP * 1.4
        t_128k = Dot(p_128k, radius=0.09, color=COLOR_ROSE)
        lbl_128k = Text("128K (Kho tài liệu)", font=FONT_FAMILY, font_size=12.0, color=COLOR_ROSE).next_to(t_128k, DOWN, buff=0.1)

        self.play(
            Create(slider_line), Write(s_title),
            FadeIn(t_4k), Write(lbl_4k),
            FadeIn(t_32k), Write(lbl_32k),
            FadeIn(t_128k), Write(lbl_128k),
            run_time=2.0
        )

        # Dynamic Slider Cursor linked to ValueTracker
        token_tracker = ValueTracker(4000)
        cursor_dot = always_redraw(lambda: Dot(
            RIGHT * (0.3 + (token_tracker.get_value() - 4000) / (128000 - 4000) * 4.6) + UP * 1.4,
            radius=0.13,
            color=COLOR_CYAN if token_tracker.get_value() < 20000 else (COLOR_AMBER if token_tracker.get_value() < 80000 else COLOR_ROSE)
        ))
        token_val_text = always_redraw(lambda: Text(
            f"{int(token_tracker.get_value()):,} tokens", font=FONT_FAMILY, font_size=13, weight=BOLD,
            color=COLOR_CYAN if token_tracker.get_value() < 20000 else (COLOR_AMBER if token_tracker.get_value() < 80000 else COLOR_ROSE)
        ).next_to(slider_line, DOWN, buff=0.45))

        self.add(cursor_dot, token_val_text)

        # Key vector k with dynamic angle
        angle_tracker = ValueTracker(0.9)
        v_k = always_redraw(lambda: Arrow(
            c_pt, c_pt + 1.7 * np.array([np.cos(angle_tracker.get_value()), np.sin(angle_tracker.get_value()), 0]),
            buff=0, color=COLOR_ROSE, stroke_width=3.5
        ))
        lbl_k = always_redraw(lambda: Text(
            f"Key k (Δθ = {angle_tracker.get_value():.1f} rad)", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_ROSE
        ).next_to(circ, DOWN, buff=0.2))

        self.add(v_k, lbl_k)

        # Normal 4K rotation demo: vector k rotates by 2.0 rad
        self.play(angle_tracker.animate.set_value(2.9), run_time=5.0, rate_func=rate_functions.smooth)
        self.wait(2.0)

        # -------------------------------------------------------------
        # BEAT 2: Context Stretch to 32K & Phase Dispersion (15 - 41s)
        # -------------------------------------------------------------
        ppl_tracker = ValueTracker(8.2)
        gauge_rect = RoundedRectangle(
            corner_radius=0.12, width=4.8, height=1.6,
            fill_color="#10172a", fill_opacity=0.92, stroke_color=COLOR_BORDER, stroke_width=1.2
        ).shift(RIGHT * 2.6 + DOWN * 0.9)
        gauge_title = Text("CHỈ SỐ PERPLEXITY (ĐỘ RỐI LOẠN):", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_MUTED).move_to(gauge_rect.get_top() + DOWN * 0.25)
        gauge_val = always_redraw(lambda: Text(
            f"{ppl_tracker.get_value():.1f}" if ppl_tracker.get_value() < 999 else "> 1,000 (MÔ HÌNH NÓI NHẢM)",
            font=FONT_FAMILY, font_size=16, weight=BOLD,
            color=COLOR_EMERALD if ppl_tracker.get_value() < 12 else (COLOR_AMBER if ppl_tracker.get_value() < 60 else COLOR_ROSE)
        ).move_to(gauge_rect.get_center() + DOWN * 0.15))

        self.play(FadeIn(gauge_rect), Write(gauge_title), FadeIn(gauge_val), run_time=1.4)

        # Staged expansion: 4K -> 32K (Vector rotates 8pi = 4 full revolutions)
        self.play(
            token_tracker.animate.set_value(32000),
            angle_tracker.animate.set_value(2.9 + 8 * PI),
            ppl_tracker.animate.set_value(24.5),
            gauge_rect.animate.set_stroke(color=COLOR_AMBER, width=1.5),
            run_time=9.0, rate_func=rate_functions.ease_in_out_quad
        )
        self.wait(2.5)

        # Staged expansion: 32K -> 128K (Vector spins furiously 24pi = 12 revolutions)
        self.play(
            token_tracker.animate.set_value(128000),
            angle_tracker.animate.set_value(angle_tracker.get_value() + 24 * PI),
            ppl_tracker.animate.set_value(1280.0),
            gauge_rect.animate.set_stroke(color=COLOR_ROSE, width=2.0),
            run_time=12.0, rate_func=rate_functions.ease_in_out_cubic
        )
        self.play(Circumscribe(gauge_rect, color=COLOR_ROSE, time_width=0.8), run_time=1.5)
        self.wait(3.0)

        # -------------------------------------------------------------
        # BEAT 3: Geometric Paradox Insight Callout (41 - 52s)
        # -------------------------------------------------------------
        insight_rect = RoundedRectangle(
            corner_radius=0.12, width=10.2, height=1.0,
            fill_color="#140f1c", fill_opacity=0.95, stroke_color=COLOR_ROSE, stroke_width=1.5
        ).shift(DOWN * 2.5)
        insight_txt_hdr = Text(
            "NGHỊCH LÝ: Phép xoay không hề hỏng số học, nhưng phá vỡ phân bố pha cỗ máy từng học!",
            font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_ROSE
        ).move_to(insight_rect)

        self.play(FadeIn(insight_rect, shift=UP * 0.2), Write(insight_txt_hdr), run_time=2.0)
        self.play(Circumscribe(insight_rect, color=COLOR_CYAN, time_width=0.8), run_time=1.5)
        self.wait(3.0)

        # -------------------------------------------------------------
        # BEAT 4: Smooth Continuous Phase Rotation to Finish (52 - 67.6s)
        # -------------------------------------------------------------
        # The vector continues a graceful ambient rotation so there is zero static freeze
        self.play(
            angle_tracker.animate.set_value(angle_tracker.get_value() + 6 * PI),
            insight_rect.animate.set_stroke(color=COLOR_CYAN, width=1.5),
            run_time=17.0, rate_func=rate_functions.linear
        )
        self.wait(2.8)


# =============================================================================
# SCENE 02: BẢN GIAO HƯỞNG TẦN SỐ & BƯỚC SÓNG (ARCHITECTURE — 91.4s)
# =============================================================================
class Tap03Scene02Architecture(Scene):
    """
    Architecture (91.4s Voiceover):
    Beat 1 (0-25s): 64 frequency pairs RoPE. 3 dynamic frequency clocks rotating exponentially.
    Beat 2 (25-52s): 3 Traveling Waves y = sin(kx - wt) propagating across token sequence.
    Beat 3 (52-74s): LLaMA 3 Base scaling experiment (10,000 -> 500,000) phase perturbation.
    Beat 4 (74-91.4s): The Asymmetry Principle & Wavelength Ratio r_i = L_train / lambda_i.
    """
    def construct(self):
        self.camera.background_color = COLOR_BG

        # Kinetic pulse tracker & Carrier Wave (Continuous frame delta > -65dB)
        pulse_tracker = ValueTracker(0.0)
        pulse_tracker.add_updater(lambda m, dt: m.increment_value(dt))
        self.add(pulse_tracker)

        carrier_wave = always_redraw(lambda: FunctionGraph(
            lambda x: -3.2 + 0.08 * np.sin(1.8 * x - pulse_tracker.get_value() * 2.5),
            x_range=[-6.0, 6.0], color=COLOR_AMBER, stroke_width=1.5, stroke_opacity=0.45
        ))
        self.add(carrier_wave)

        # Title HUD
        title_text = Text(
            "PHỔ BƯỚC SÓNG: BẢN GIAO HƯỞNG ĐA TẦN SỐ TRONG RoPE",
            font=FONT_FAMILY, font_size=15, weight=BOLD, color=COLOR_CYAN
        )
        title_box = RoundedRectangle(
            corner_radius=0.12, width=title_text.width + 0.6, height=0.5,
            fill_color="#10172a", fill_opacity=0.9, stroke_color=COLOR_CYAN, stroke_width=1.2
        ).to_edge(UP, buff=0.45)
        title_text.move_to(title_box)
        self.play(FadeIn(title_box, shift=DOWN * 0.2), Write(title_text), run_time=0.9)

        # -------------------------------------------------------------
        # BEAT 1: 3 Representative Frequency Clocks (0 - 24s)
        # -------------------------------------------------------------
        time_tracker = ValueTracker(0.0)

        # Clock 1: High frequency (i=0, lambda = 3 tokens)
        c1_pt = LEFT * 3.6 + UP * 1.55
        c1_circ = Circle(radius=0.95, stroke_color=COLOR_BORDER, stroke_width=1.2).move_to(c1_pt)
        c1_needle = always_redraw(lambda: Arrow(
            c1_pt, c1_pt + 0.85 * np.array([np.cos(time_tracker.get_value() * 6.0), np.sin(time_tracker.get_value() * 6.0), 0]),
            buff=0, color=COLOR_ROSE, stroke_width=2.5
        ))
        c1_lbl = Text("i = 0 (Tần số cao)", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_ROSE).next_to(c1_circ, UP, buff=0.12)
        c1_sub = Text("λ ≈ 3 token (Cú pháp kề)", font=FONT_FAMILY, font_size=12.0, color=COLOR_MUTED).next_to(c1_circ, DOWN, buff=0.1)

        # Clock 2: Mid frequency (i=32, lambda = 500 tokens)
        c2_pt = ORIGIN + UP * 1.55
        c2_circ = Circle(radius=0.95, stroke_color=COLOR_BORDER, stroke_width=1.2).move_to(c2_pt)
        c2_needle = always_redraw(lambda: Arrow(
            c2_pt, c2_pt + 0.85 * np.array([np.cos(time_tracker.get_value() * 1.5), np.sin(time_tracker.get_value() * 1.5), 0]),
            buff=0, color=COLOR_AMBER, stroke_width=2.5
        ))
        c2_lbl = Text("i = 32 (Tần số trung)", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_AMBER).next_to(c2_circ, UP, buff=0.12)
        c2_sub = Text("λ ≈ 500 token (Đoạn văn)", font=FONT_FAMILY, font_size=12.0, color=COLOR_MUTED).next_to(c2_circ, DOWN, buff=0.1)

        # Clock 3: Low frequency (i=63, lambda > 10,000 tokens)
        c3_pt = RIGHT * 3.6 + UP * 1.55
        c3_circ = Circle(radius=0.95, stroke_color=COLOR_BORDER, stroke_width=1.2).move_to(c3_pt)
        c3_needle = always_redraw(lambda: Arrow(
            c3_pt, c3_pt + 0.85 * np.array([np.cos(time_tracker.get_value() * 0.2), np.sin(time_tracker.get_value() * 0.2), 0]),
            buff=0, color=COLOR_EMERALD, stroke_width=2.5
        ))
        c3_lbl = Text("i = 63 (Tần số thấp)", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_EMERALD).next_to(c3_circ, UP, buff=0.12)
        c3_sub = Text("λ > 10,000 token (Vĩ mô)", font=FONT_FAMILY, font_size=12.0, color=COLOR_MUTED).next_to(c3_circ, DOWN, buff=0.1)

        self.play(
            Create(c1_circ), Write(c1_lbl), Write(c1_sub),
            Create(c2_circ), Write(c2_lbl), Write(c2_sub),
            Create(c3_circ), Write(c3_lbl), Write(c3_sub),
            run_time=2.5
        )
        self.add(c1_needle, c2_needle, c3_needle)

        # Clocks spin simultaneously for 16.5s
        self.play(time_tracker.animate.set_value(16.5), run_time=16.5, rate_func=rate_functions.linear)
        self.wait(4.0)

        # -------------------------------------------------------------
        # BEAT 2: 3 Traveling Waves across Token Stream (24 - 50s)
        # -------------------------------------------------------------
        # Clean up sub-labels from Beat 1 so that wave box and experiment badge have full breathing room
        self.play(FadeOut(c1_sub), FadeOut(c2_sub), FadeOut(c3_sub), run_time=0.8)

        wave_box = RoundedRectangle(
            corner_radius=0.14, width=10.4, height=2.8,
            fill_color=COLOR_CARD_BG, fill_opacity=0.94, stroke_color=COLOR_BORDER, stroke_width=1.2
        ).shift(DOWN * 1.55)
        self.play(FadeIn(wave_box), run_time=1.0)

        # Common Axes for Waves
        ax = Axes(
            x_range=[0, 10, 1], y_range=[-1.2, 1.2, 1],
            x_length=9.4, y_length=2.2,
            axis_config={"color": COLOR_BORDER, "stroke_width": 1.0}
        ).move_to(wave_box.get_center())

        base_tracker = ValueTracker(10000.0)

        # Dynamic Traveling Waves: y = sin(k*x - omega*t)
        wave_high = always_redraw(lambda: ax.plot(
            lambda x: 0.35 * math.sin(x * 6.0 - time_tracker.get_value() * 4.0) + 0.6,
            color=COLOR_ROSE, stroke_width=2.2
        ))
        wave_mid = always_redraw(lambda: ax.plot(
            lambda x: 0.40 * math.sin(x * 1.8 - time_tracker.get_value() * 1.2),
            color=COLOR_AMBER, stroke_width=2.2
        ))
        wave_low = always_redraw(lambda: ax.plot(
            lambda x: 0.35 * math.sin(x * (0.4 * 10000.0 / base_tracker.get_value()) - time_tracker.get_value() * 0.3) - 0.6,
            color=COLOR_EMERALD, stroke_width=2.5
        ))

        self.play(Create(ax), run_time=1.0)
        self.add(wave_high, wave_mid, wave_low)

        # Propagate traveling waves
        self.play(time_tracker.animate.set_value(34.5), run_time=18.0, rate_func=rate_functions.linear)
        self.wait(4.0)

        # -------------------------------------------------------------
        # BEAT 3: LLaMA 3 Base Scaling Experiment (50 - 74s)
        # -------------------------------------------------------------
        exp_badge = RoundedRectangle(
            corner_radius=0.08, width=5.6, height=0.6,
            fill_color="#181324", fill_opacity=0.95, stroke_color=COLOR_GOLD, stroke_width=1.2
        ).move_to(wave_box.get_top() + UP * 0.35)
        exp_txt = always_redraw(lambda: Text(
            f"Thử nghiệm Base: 10,000 → {int(base_tracker.get_value()):,} (LLaMA 3)",
            font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_GOLD
        ).move_to(exp_badge))

        self.play(FadeIn(exp_badge), FadeIn(exp_txt), run_time=1.2)

        # Scale base up to 500,000 -> Watch low frequency wave stretch flat
        self.play(
            base_tracker.animate.set_value(500000.0),
            time_tracker.animate.set_value(51.5),
            run_time=16.0, rate_func=rate_functions.ease_in_out_quad
        )
        self.play(Circumscribe(exp_badge, color=COLOR_GOLD, time_width=0.8), run_time=1.5)
        self.wait(4.0)

        # -------------------------------------------------------------
        # BEAT 4: The Asymmetry Principle Formula & Continuous Life (74 - 93.0s)
        # -------------------------------------------------------------
        f_card = RoundedRectangle(
            corner_radius=0.1, width=8.8, height=0.7,
            fill_color="#10172a", fill_opacity=0.95, stroke_color=COLOR_CYAN, stroke_width=1.5
        ).shift(DOWN * 1.85)
        f_formula = MathTex(
            r"\lambda_i = \frac{2\pi}{\theta_i} = 2\pi \cdot b^{\frac{2i}{d}}, \quad r_i = \frac{L_{\mathrm{train}}}{\lambda_i}",
            font_size=19, color=COLOR_CYAN
        ).move_to(f_card)

        self.play(FadeIn(f_card, shift=UP * 0.2), Write(f_formula), run_time=1.5)
        self.play(Indicate(f_card, color=COLOR_GOLD, scale_factor=1.02), run_time=1.2)

        # Ambient continuous wave propagation to complete the 93.0s scene smoothly
        self.play(
            time_tracker.animate.set_value(66.0),
            run_time=14.0, rate_func=rate_functions.linear
        )
        self.wait(2.3)


# =============================================================================
# SCENE 03: TỪ NÉN THẲNG ĐẾN NỘI SUY ĐA DẢI YARN (MATHEMATICS — 77.4s)
# =============================================================================
class Tap03Scene03Mathematics(Scene):
    """
    Mathematics (77.4s Voiceover):
    Beat 1 (0-25s): The Fatal Flaw of Position Interpolation (PI) -> Local Myopia.
    Beat 2 (25-50s): YaRN 3-Band Continuous Spectrum Ribbon (High/Mid/Low partitions).
    Beat 3 (50-77.4s): Mathematical Formulation theta_i' & Connecting energy rays.
    """
    def construct(self):
        self.camera.background_color = COLOR_BG

        # Kinetic pulse tracker & Carrier Wave (Ensures continuous frame delta > -65dB)
        pulse_tracker = ValueTracker(0.0)
        pulse_tracker.add_updater(lambda m, dt: m.increment_value(dt))
        self.add(pulse_tracker)

        carrier_wave = always_redraw(lambda: FunctionGraph(
            lambda x: -3.2 + 0.08 * np.sin(2.0 * x + pulse_tracker.get_value() * 3.0),
            x_range=[-6.0, 6.0], color=COLOR_GOLD, stroke_width=1.5, stroke_opacity=0.45
        ))
        self.add(carrier_wave)

        # Title HUD
        title_text = Text(
            "ĐỘT PHÁ YaRN: NỘI SUY TẦN SỐ PHÂN TẦNG (NTK-BY-PARTS)",
            font=FONT_FAMILY, font_size=15, weight=BOLD, color=COLOR_GOLD
        )
        title_box = RoundedRectangle(
            corner_radius=0.12, width=title_text.width + 0.6, height=0.5,
            fill_color="#10172a", fill_opacity=0.9, stroke_color=COLOR_GOLD, stroke_width=1.2
        ).to_edge(UP, buff=0.45)
        title_text.move_to(title_box)
        self.play(FadeIn(title_box, shift=DOWN * 0.2), Write(title_text), run_time=0.9)

        # -------------------------------------------------------------
        # BEAT 1: The Fatal Flaw of Position Interpolation (0 - 21s)
        # -------------------------------------------------------------
        top_axis = Line(LEFT * 4.8 + UP * 1.5, RIGHT * 4.8 + UP * 1.5, color=COLOR_BORDER, stroke_width=2.5)
        axis_lbl = Text("Khoảng cách góc giữa 2 token kề nhau trong câu:", font=FONT_FAMILY, font_size=12.0, color=COLOR_MUTED).next_to(top_axis, UP, buff=0.15)
        self.play(Create(top_axis), Write(axis_lbl), run_time=1.5)

        # Word tokens: "Chú" and "Mèo"
        dot_w1 = Dot(LEFT * 1.2 + UP * 1.5, radius=0.12, color=COLOR_CYAN)
        lbl_w1 = Text("'Chú'", font=FONT_FAMILY, font_size=12, weight=BOLD, color=COLOR_CYAN).next_to(dot_w1, UP, buff=0.1)

        dot_w2 = Dot(RIGHT * 1.2 + UP * 1.5, radius=0.12, color=COLOR_CYAN)
        lbl_w2 = Text("'Mèo'", font=FONT_FAMILY, font_size=12, weight=BOLD, color=COLOR_CYAN).next_to(dot_w2, UP, buff=0.1)

        angle_dist_brace = BraceBetweenPoints(dot_w1.get_center(), dot_w2.get_center(), direction=DOWN)
        lbl_dist_orig = Text("Góc ban đầu Δθ (Rõ ràng)", font=FONT_FAMILY, font_size=12.0, color=COLOR_EMERALD).next_to(angle_dist_brace, DOWN, buff=0.08)

        self.play(FadeIn(dot_w1), Write(lbl_w1), FadeIn(dot_w2), Write(lbl_w2), Create(angle_dist_brace), Write(lbl_dist_orig), run_time=3.0)
        self.wait(2.0)

        # Position Interpolation compress by s=8
        lbl_pi_warning_hdr = Text("Position Interpolation: Chia đều tọa độ cho s=8 → Nén tất cả kim 8 lần!", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_ROSE).shift(UP * 0.5)
        self.play(Write(lbl_pi_warning_hdr), run_time=2.0)

        # Shrink distance between words by 8x — Stagger labels to prevent collision
        dot_w2_compressed = Dot(LEFT * 1.2 + RIGHT * 0.45 + UP * 1.5, radius=0.12, color=COLOR_ROSE)
        brace_compressed = BraceBetweenPoints(dot_w1.get_center(), dot_w2_compressed.get_center(), direction=DOWN)
        lbl_dist_comp = Text("Δθ / 8 (Cận thị cục bộ!) 💥", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_ROSE).next_to(brace_compressed, DOWN, buff=0.15)

        self.play(
            Transform(dot_w2, dot_w2_compressed),
            lbl_w2.animate.next_to(dot_w2_compressed, UR, buff=0.12),
            Transform(angle_dist_brace, brace_compressed),
            Transform(lbl_dist_orig, lbl_dist_comp),
            run_time=5.0
        )
        self.play(Circumscribe(lbl_dist_comp, color=COLOR_ROSE, time_width=0.8), run_time=2.5)
        self.play(Wiggle(lbl_dist_comp), run_time=2.0)
        self.wait(1.5)

        # Clean up top demonstration to open space for YaRN Masterpiece Ribbon
        self.play(
            FadeOut(top_axis), FadeOut(axis_lbl), FadeOut(dot_w1), FadeOut(lbl_w1),
            FadeOut(dot_w2), FadeOut(lbl_w2), FadeOut(angle_dist_brace), FadeOut(lbl_dist_orig),
            FadeOut(lbl_pi_warning_hdr),
            run_time=1.5
        )

        # -------------------------------------------------------------
        # BEAT 2: YaRN 3-Band Continuous Spectrum Ribbon (21 - 42s)
        # -------------------------------------------------------------
        ribbon_y = 1.1
        
        # Continuous Spectrum Base
        r_high = Rectangle(width=3.2, height=1.0, fill_color=COLOR_ROSE, fill_opacity=0.85, stroke_color=COLOR_BORDER, stroke_width=1.0).shift(LEFT * 3.3 + UP * ribbon_y)
        r_mid = Rectangle(width=3.4, height=1.0, fill_color=COLOR_AMBER, fill_opacity=0.85, stroke_color=COLOR_BORDER, stroke_width=1.0).shift(ORIGIN + UP * ribbon_y)
        r_low = Rectangle(width=3.2, height=1.0, fill_color=COLOR_EMERALD, fill_opacity=0.85, stroke_color=COLOR_BORDER, stroke_width=1.0).shift(RIGHT * 3.3 + UP * ribbon_y)

        t_high_hdr = Text("1. SÓNG NGẮN (r_i > β)\nGiữ nguyên 100% (γ = 1)", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=WHITE).move_to(r_high)
        t_mid_hdr = Text("2. SÓNG TRUNG (α ≤ r_i ≤ β)\nHàm dốc hòa trộn (Ramp)", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=WHITE).move_to(r_mid)
        t_low_hdr = Text("3. SÓNG DÀI (r_i < α)\nNội suy s lần (γ = 0)", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=WHITE).move_to(r_low)

        spec_group = VGroup(r_high, t_high_hdr, r_mid, t_mid_hdr, r_low, t_low_hdr)
        spec_title = Text("PHỔ TẦN SỐ YaRN: PHÂN TẦNG THEO BƯỚC SÓNG (NTK-BY-PARTS)", font=FONT_FAMILY, font_size=12, weight=BOLD, color=COLOR_GOLD).next_to(r_mid, UP, buff=0.25)

        self.play(Write(spec_title), FadeIn(spec_group), run_time=2.5)
        self.play(Circumscribe(r_high, color=COLOR_ROSE, time_width=0.7), run_time=1.5)
        self.play(Circumscribe(r_low, color=COLOR_EMERALD, time_width=0.7), run_time=1.5)

        # Dynamic frequency wavelength wave indicators under each band
        wave_h = always_redraw(lambda: FunctionGraph(
            lambda x: 0.35 + 0.09 * np.sin(10.0 * x + pulse_tracker.get_value() * 8.0),
            x_range=[-4.8, -1.8], color=COLOR_ROSE, stroke_width=2.0
        ))
        wave_m = always_redraw(lambda: FunctionGraph(
            lambda x: 0.35 + 0.09 * np.sin(4.0 * x + pulse_tracker.get_value() * 4.0),
            x_range=[-1.6, 1.6], color=COLOR_AMBER, stroke_width=2.0
        ))
        wave_l = always_redraw(lambda: FunctionGraph(
            lambda x: 0.35 + 0.09 * np.sin(1.5 * x + pulse_tracker.get_value() * 1.8),
            x_range=[1.8, 4.8], color=COLOR_EMERALD, stroke_width=2.0
        ))
        waves_group = VGroup(wave_h, wave_m, wave_l)
        lbl_waves_hdr = Text("Tần số cao: Xoay tít           Tần số trung: Chuyển tiếp           Tần số thấp: Chu kỳ dài", font=FONT_FAMILY, font_size=12.0, color=COLOR_MUTED).shift(DOWN * 0.05)

        self.play(Create(waves_group), Write(lbl_waves_hdr), run_time=3.0)
        self.play(r_high.animate.set_fill(opacity=1.0), r_low.animate.set_fill(opacity=1.0), run_time=2.0, rate_func=rate_functions.there_and_back)
        self.play(Circumscribe(r_mid, color=COLOR_AMBER, time_width=0.8), run_time=2.0)
        self.wait(2.0)

        # Clean up wavelength waves to open space for mathematical formulation
        self.play(FadeOut(waves_group), FadeOut(lbl_waves_hdr), run_time=1.5)

        # -------------------------------------------------------------
        # BEAT 3: Mathematical Formulation & Smooth Ramp (42 - 79.0s)
        # -------------------------------------------------------------
        formula_box = RoundedRectangle(
            corner_radius=0.14, width=9.8, height=2.2,
            fill_color=COLOR_CARD_BG, fill_opacity=0.95, stroke_color=COLOR_GOLD, stroke_width=1.5
        ).shift(DOWN * 1.3)

        eq_main = MathTex(
            r"\theta_i' = (1 - \gamma_i)\frac{\theta_i}{s} + \gamma_i \theta_i",
            font_size=24, color=COLOR_GOLD
        ).move_to(formula_box.get_top() + DOWN * 0.45)

        eq_ramp = MathTex(
            r"\gamma_i = \frac{r_i - \alpha}{\beta - \alpha}, \quad r_i = \frac{L_{\mathrm{train}}}{\lambda_i}",
            font_size=19, color=COLOR_AMBER
        ).next_to(eq_main, DOWN, buff=0.25)

        ppl_badge_hdr = Text(
            "✓ Bảo toàn 100% khả năng suy luận ngữ pháp ngắn • Mở rộng 128K hoàn hảo!",
            font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_EMERALD
        ).move_to(formula_box.get_bottom() + UP * 0.3)

        self.play(FadeIn(formula_box), Write(eq_main), run_time=2.5)
        self.play(Write(eq_ramp), FadeIn(ppl_badge_hdr), run_time=2.5)
        
        # Step-by-step interactive focus on the 3 bands
        # Focus 1: High freq band -> gamma_i = 1
        ind_high = Arrow(r_high.get_bottom(), eq_main.get_left() + UP * 0.2, color=COLOR_ROSE, stroke_width=2.5, buff=0.1)
        lbl_h_focus = Text("γ = 1: Giữ nguyên θ_i", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_ROSE).next_to(ind_high, LEFT, buff=0.1)
        self.play(GrowArrow(ind_high), Write(lbl_h_focus), r_high.animate.set_stroke(color=WHITE, width=2.5), run_time=3.5)

        # Focus 2: Low freq band -> gamma_i = 0
        ind_low = Arrow(r_low.get_bottom(), eq_main.get_right() + UP * 0.2, color=COLOR_EMERALD, stroke_width=2.5, buff=0.1)
        lbl_l_focus = Text("γ = 0: Nội suy θ_i / s", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_EMERALD).next_to(ind_low, RIGHT, buff=0.1)
        self.play(
            FadeOut(ind_high), FadeOut(lbl_h_focus), r_high.animate.set_stroke(color=COLOR_BORDER, width=1.0),
            GrowArrow(ind_low), Write(lbl_l_focus), r_low.animate.set_stroke(color=WHITE, width=2.5),
            run_time=3.5
        )

        # Clean focus arrows & run continuous harmonized pulse
        self.play(
            FadeOut(ind_low), FadeOut(lbl_l_focus), r_low.animate.set_stroke(color=COLOR_BORDER, width=1.0),
            r_high.animate.set_fill(opacity=1.0),
            r_mid.animate.set_fill(opacity=1.0),
            r_low.animate.set_fill(opacity=1.0),
            formula_box.animate.set_stroke(color=COLOR_CYAN, width=2.0),
            run_time=12.0, rate_func=rate_functions.there_and_back
        )
        self.play(
            Circumscribe(ppl_badge_hdr, color=COLOR_EMERALD, time_width=0.8),
            run_time=3.0
        )
        self.play(formula_box.animate.set_stroke(color=COLOR_GOLD, width=2.2), run_time=2.5, rate_func=rate_functions.there_and_back)
        self.play(Circumscribe(eq_main, color=COLOR_GOLD, time_width=0.8), run_time=3.0)
        self.play(Wiggle(ppl_badge_hdr), run_time=2.5)
        self.wait(2.0)


# =============================================================================
# SCENE 04: BỒN TRŨNG ATTENTION SINK & STREAMINGLLM (TELEMETRY — 89.2s)
# =============================================================================
class Tap03Scene04Telemetry(Scene):
    """
    Telemetry (89.2s Voiceover):
    Beat 1 (0-24s): KV Cache VRAM linear explosion (60+ GB for 1 user at 128K).
    Beat 2 (24-50s): Naive sliding window eviction causes immediate perplexity explosion.
    Beat 3 (50-70s): MIT Attention Sink discovery in Softmax Attention Heatmap.
    Beat 4 (70-89.2s): StreamingLLM 4 Sink anchors + sliding window = 4M tokens at 4.2 GB.
    """
    def construct(self):
        self.camera.background_color = COLOR_BG

        # Kinetic pulse tracker & Carrier Wave (Continuous frame delta > -65dB)
        pulse_tracker = ValueTracker(0.0)
        pulse_tracker.add_updater(lambda m, dt: m.increment_value(dt))
        self.add(pulse_tracker)

        carrier_wave = always_redraw(lambda: FunctionGraph(
            lambda x: -3.2 + 0.08 * np.sin(1.8 * x - pulse_tracker.get_value() * 2.5),
            x_range=[-6.0, 6.0], color=COLOR_ROSE, stroke_width=1.5, stroke_opacity=0.45
        ))
        self.add(carrier_wave)

        # Title HUD
        title_text = Text(
            "BÍ ẨN ATTENTION SINK & ĐỘT PHÁ StreamingLLM",
            font=FONT_FAMILY, font_size=15, weight=BOLD, color=COLOR_CYAN
        )
        title_box = RoundedRectangle(
            corner_radius=0.12, width=title_text.width + 0.6, height=0.5,
            fill_color="#10172a", fill_opacity=0.9, stroke_color=COLOR_CYAN, stroke_width=1.2
        ).to_edge(UP, buff=0.45)
        title_text.move_to(title_box)
        self.play(FadeIn(title_box, shift=DOWN * 0.2), Write(title_text), run_time=0.9)

        # -------------------------------------------------------------
        # BEAT 1: KV Cache VRAM Linear Wall (0 - 24s) [Web Component]
        # -------------------------------------------------------------
        vram_tracker = ValueTracker(2.0)
        vram_comp = ProgressBarComponent(
            title="BỨC TƯỜNG VRAM: BỘ NHỚ KV CACHE TĂNG TUYẾN TÍNH THEO CONTEXT",
            tracker=vram_tracker,
            max_val=64.0,
            width=9.6,
            height=0.45,
        ).shift(UP * 1.5)

        self.play(FadeIn(vram_comp), run_time=2.0)

        # Explode VRAM from 2GB to 64GB
        self.play(
            vram_tracker.animate.set_value(64.0),
            run_time=12.0, rate_func=rate_functions.ease_in_out_cubic
        )
        self.play(Circumscribe(vram_comp.val_label, color=COLOR_ROSE, time_width=0.8), run_time=2.0)
        self.play(Wiggle(vram_comp.val_label), run_time=2.5)
        self.play(vram_comp.fill_bar.animate.set_fill(opacity=0.6), run_time=2.5, rate_func=rate_functions.there_and_back)
        self.wait(2.0)

        # -------------------------------------------------------------
        # BEAT 2: Naive Sliding Window & PPL Explosion (24 - 50s)
        # -------------------------------------------------------------
        conveyor_y = -0.3
        conveyor_label = Text("Thử nghiệm Cửa Sổ Trượt (Sliding Window W = 4):", font=FONT_FAMILY, font_size=12.0, color=COLOR_MUTED).shift(UP * 0.4 + LEFT * 1.8)
        self.play(Write(conveyor_label), run_time=1.5)

        # Token sequence on conveyor
        tokens_grp = VGroup()
        for i in range(8):
            c = RoundedRectangle(corner_radius=0.06, width=0.85, height=0.75, fill_color="#1e293b", fill_opacity=0.9, stroke_color=COLOR_CYAN if i < 4 else COLOR_AMBER, stroke_width=1.2)
            t = Text(f"T_{i}", font=FONT_FAMILY, font_size=12.0, color=WHITE).move_to(c)
            tokens_grp.add(VGroup(c, t))
        tokens_grp.arrange(RIGHT, buff=0.15).shift(UP * conveyor_y)

        self.play(FadeIn(tokens_grp), run_time=1.5)

        # Evict Token 0 into trash -> PPL explodes
        t0 = tokens_grp[0]
        evict_arrow = CurvedArrow(t0.get_bottom(), t0.get_bottom() + DOWN * 1.0 + LEFT * 0.8, color=COLOR_ROSE)
        evict_lbl = Text("Xóa T_0 khỏi đệm đạn!", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_ROSE).next_to(evict_arrow, DOWN, buff=0.05)

        self.play(Create(evict_arrow), Write(evict_lbl), t0.animate.set_stroke(color=COLOR_ROSE, width=2.5), run_time=3.0)

        ppl_spike_card = RoundedRectangle(
            corner_radius=0.1, width=4.5, height=1.1,
            fill_color="#180b12", fill_opacity=0.95, stroke_color=COLOR_ROSE, stroke_width=1.8
        ).shift(DOWN * 1.8 + RIGHT * 2.2)
        ppl_spike_txt_hdr = Text("PERPLEXITY VỌT LÊN VÔ CỰC 💥\nMô hình sụp đổ hoàn toàn!", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_ROSE, line_spacing=1.2).move_to(ppl_spike_card)

        self.play(FadeIn(ppl_spike_card, shift=UP * 0.2), Write(ppl_spike_txt_hdr), run_time=3.0)
        self.play(Circumscribe(ppl_spike_card, color=COLOR_ROSE, time_width=0.8), run_time=2.0)
        self.play(Wiggle(ppl_spike_card), run_time=3.0)
        self.play(ppl_spike_card.animate.set_stroke(color=WHITE, width=2.5), run_time=2.0, rate_func=rate_functions.there_and_back)
        self.play(Circumscribe(t0, color=COLOR_ROSE, time_width=0.8), run_time=2.0)
        self.wait(2.0)

        # Clean up middle to reveal Attention Sink Matrix
        self.play(
            FadeOut(evict_arrow), FadeOut(evict_lbl), FadeOut(ppl_spike_card), FadeOut(ppl_spike_txt_hdr),
            FadeOut(tokens_grp), FadeOut(conveyor_label),
            FadeOut(vram_comp),
            run_time=2.0
        )

        # -------------------------------------------------------------
        # BEAT 3: MIT Attention Sink Discovery (50 - 70s) [Zero Overlap Safe Zone]
        # -------------------------------------------------------------
        sink_title = Text(
            "PHÁT HIỆN BỒN TRŨNG CHÚ Ý (ATTENTION SINK - MIT 2024)",
            font=FONT_FAMILY, font_size=12, weight=BOLD, color=COLOR_GOLD
        ).shift(UP * 2.3)
        self.play(Write(sink_title), run_time=2.0)

        # Visual Attention Heatmap: 5 rows x 8 columns, first 4 columns intensely glowing
        grid_group = VGroup()
        for r in range(5):
            row = VGroup()
            for c in range(8):
                is_sink = (c < 4)
                color = COLOR_CYAN if is_sink else COLOR_BORDER
                op = 0.95 if is_sink else 0.25
                cell = Rectangle(width=0.55, height=0.38, fill_color=color, fill_opacity=op, stroke_color=COLOR_BORDER, stroke_width=0.8)
                row.add(cell)
            row.arrange(RIGHT, buff=0.06)
            grid_group.add(row)
        grid_group.arrange(DOWN, buff=0.06).shift(LEFT * 2.5 + DOWN * 0.45)

        # Bracket ONLY the 4 cyan sink columns (not the whole grid) to prevent label collision
        sink_cols = VGroup(*[row[:4] for row in grid_group])
        sink_bracket = Brace(sink_cols, direction=UP)
        sink_brace_lbl = Text(
            "4 Attention Sinks: Hút 40%+ Softmax",
            font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_CYAN
        ).next_to(sink_bracket, UP, buff=0.12)

        self.play(Create(grid_group), Create(sink_bracket), Write(sink_brace_lbl), run_time=3.5)

        # Attention energy pulses into sink columns
        self.play(
            grid_group.animate.set_stroke(color=COLOR_GOLD, width=1.5),
            sink_brace_lbl.animate.set_color(COLOR_GOLD),
            run_time=8.0, rate_func=rate_functions.there_and_back
        )
        self.play(Circumscribe(sink_brace_lbl, color=COLOR_GOLD, time_width=0.8), run_time=2.5)
        self.wait(2.0)

        # -------------------------------------------------------------
        # BEAT 4: StreamingLLM Pinning Solution (70 - 90.8s) [15%-20% Safe Zone]
        # -------------------------------------------------------------
        sol_panel = RoundedRectangle(
            corner_radius=0.12, width=4.8, height=2.8,
            fill_color=COLOR_CARD_BG, fill_opacity=0.95, stroke_color=COLOR_EMERALD, stroke_width=1.5
        ).shift(RIGHT * 2.5 + DOWN * 0.45)
        sol_title = Text("GIẢI PHÁP StreamingLLM:", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_EMERALD).move_to(sol_panel.get_top() + DOWN * 0.35)
        sol_desc_hdr = Text(
            "• Ghim chặt 4 token đầu (Sinks)\n• Trượt mượt cửa sổ gần nhất W\n• VRAM cố định 4.2 GB vĩnh viễn\n• Xử lý 4,000,000+ token không đổi!",
            font=FONT_FAMILY, font_size=12.0, color=COLOR_TEXT, line_spacing=1.3
        ).next_to(sol_title, DOWN, buff=0.20)

        self.play(FadeIn(sol_panel, shift=LEFT * 0.3), Write(sol_title), FadeIn(sol_desc_hdr), run_time=3.5)
        
        # Soft glowing pulses on the 4 sink columns and streaming panel
        self.play(
            grid_group.animate.set_stroke(color=COLOR_CYAN, width=1.5),
            sol_panel.animate.set_stroke(color=COLOR_GOLD, width=1.8),
            run_time=8.0, rate_func=rate_functions.there_and_back
        )
        self.play(Circumscribe(sol_panel, color=COLOR_EMERALD, time_width=0.8), run_time=2.0)
        self.play(sol_panel.animate.set_fill(opacity=0.7), run_time=2.5, rate_func=rate_functions.there_and_back)
        self.play(Wiggle(sol_title), run_time=2.5)
        self.wait(2.4)


# =============================================================================
# SCENE 05: THỬ NGHIỆM ĐỐI CHỨNG: STREAMING KHÁC VỚI TRUY XUẤT (LAB — 84.3s)
# =============================================================================
class Tap03Scene05LabExperiment(Scene):
    """
    Lab Experiment (84.3s Voiceover):
    Beat 1 (0-25s): Dual-track lab bench: StreamingLLM (Track A) vs YaRN+RAG (Track B).
    Beat 2 (25-55s): Needle-in-a-Haystack at token 10,000 queried at token 100,000.
                     StreamingLLM returns empty (X); YaRN+RAG pinpoints needle (V).
    Beat 3 (55-84.3s): Production 2-Tier Architecture: Outer Streaming, Inner Retrieval.
    """
    def construct(self):
        self.camera.background_color = COLOR_BG

        # Kinetic pulse tracker & Carrier Wave (Continuous frame delta > -65dB)
        pulse_tracker = ValueTracker(0.0)
        pulse_tracker.add_updater(lambda m, dt: m.increment_value(dt))
        self.add(pulse_tracker)

        carrier_wave = always_redraw(lambda: FunctionGraph(
            lambda x: -3.2 + 0.08 * np.sin(1.8 * x - pulse_tracker.get_value() * 2.5),
            x_range=[-6.0, 6.0], color=COLOR_CYAN, stroke_width=1.5, stroke_opacity=0.45
        ))
        self.add(carrier_wave)

        # Title HUD
        title_text = Text(
            "THỬ NGHIỆM ĐỐI CHỨNG: STREAMING KHÔNG PHẢI LÀ TRUY XUẤT",
            font=FONT_FAMILY, font_size=15, weight=BOLD, color=COLOR_ROSE
        )
        title_box = RoundedRectangle(
            corner_radius=0.12, width=title_text.width + 0.6, height=0.5,
            fill_color="#10172a", fill_opacity=0.9, stroke_color=COLOR_ROSE, stroke_width=1.2
        ).to_edge(UP, buff=0.45)
        title_text.move_to(title_box)
        self.play(FadeIn(title_box, shift=DOWN * 0.2), Write(title_text), run_time=0.9)

        # -------------------------------------------------------------
        # BEAT 1: Dual-Track Interactive Test Bench (0 - 25s)
        # -------------------------------------------------------------
        # Track A: StreamingLLM (Top Track)
        track_a_line = Line(LEFT * 4.8 + UP * 1.5, RIGHT * 4.8 + UP * 1.5, color=COLOR_BORDER, stroke_width=3.0)
        lbl_track_a = Text("NHÁNH 1: StreamingLLM (Cửa sổ trượt cố định W = 2K)", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_AMBER).next_to(track_a_line, UP, buff=0.15)
        
        # Track B: Long Context YaRN + RAG (Bottom Track)
        track_b_line = Line(LEFT * 4.8 + DOWN * 0.6, RIGHT * 4.8 + DOWN * 0.6, color=COLOR_BORDER, stroke_width=3.0)
        lbl_track_b = Text("NHÁNH 2: YaRN 128K + RAG (Truy xuất sự thật quá khứ)", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_CYAN).next_to(track_b_line, UP, buff=0.15)

        self.play(
            Create(track_a_line), Write(lbl_track_a),
            Create(track_b_line), Write(lbl_track_b),
            run_time=2.2
        )

        # Token Timeline Markers: 10K (Needle) and 100K (Query)
        needle_pt_a = LEFT * 3.0 + UP * 1.5
        needle_pt_b = LEFT * 3.0 + DOWN * 0.6
        needle_dot_a = Dot(needle_pt_a, radius=0.12, color=COLOR_GOLD)
        needle_dot_b = Dot(needle_pt_b, radius=0.12, color=COLOR_GOLD)
        needle_lbl = Text("Kim: 'Mã bí mật = 8492' (Token 10,000)", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_GOLD).next_to(needle_dot_a, UP, buff=0.25)

        query_pt_a = RIGHT * 3.8 + UP * 1.5
        query_pt_b = RIGHT * 3.8 + DOWN * 0.6
        query_dot_a = Dot(query_pt_a, radius=0.12, color=COLOR_ROSE)
        query_dot_b = Dot(query_pt_b, radius=0.12, color=COLOR_CYAN)
        query_lbl = Text("Truy vấn: 'Mã bí mật là gì?' (Token 100,000)", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=WHITE).next_to(query_dot_a, UP, buff=0.25)

        self.play(
            FadeIn(needle_dot_a), FadeIn(needle_dot_b), Write(needle_lbl),
            FadeIn(query_dot_a), FadeIn(query_dot_b), Write(query_lbl),
            run_time=2.2
        )
        self.wait(2.0)

        # -------------------------------------------------------------
        # BEAT 2: Needle-in-a-Haystack Search Contrast (25 - 55s)
        # -------------------------------------------------------------
        # Track A: Window has moved to [98K - 100K], Token 10K was evicted 90K tokens ago
        window_a = RoundedRectangle(corner_radius=0.08, width=1.6, height=0.6, fill_color=COLOR_AMBER, fill_opacity=0.3, stroke_color=COLOR_AMBER, stroke_width=1.5).move_to(query_pt_a)
        res_a_badge = RoundedRectangle(corner_radius=0.1, width=3.8, height=0.8, fill_color="#180b12", fill_opacity=0.9, stroke_color=COLOR_ROSE, stroke_width=1.5).shift(UP * 0.5 + LEFT * 1.0)
        res_a_txt = Text("Streaming: BẤT LỰC ✗ (Dữ liệu đã trôi)", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_ROSE).move_to(res_a_badge)

        self.play(Create(window_a), FadeIn(res_a_badge), Write(res_a_txt), run_time=2.0)
        self.wait(1.5)

        # Track B: RAG Searchlight scans from 100K back to 10K and retrieves needle
        search_ray = Arrow(query_pt_b, needle_pt_b, buff=0.15, color=COLOR_CYAN, stroke_width=3.5)
        res_b_badge = RoundedRectangle(corner_radius=0.1, width=3.8, height=0.8, fill_color="#0b1814", fill_opacity=0.9, stroke_color=COLOR_EMERALD, stroke_width=1.5).shift(DOWN * 1.6 + LEFT * 1.0)
        res_b_txt = Text("YaRN + RAG: CHÍNH XÁC 100% ✓ ('8492')", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_EMERALD).move_to(res_b_badge)

        self.play(GrowArrow(search_ray), FadeIn(res_b_badge), Write(res_b_txt), run_time=2.2)
        self.play(Circumscribe(needle_dot_b, color=COLOR_EMERALD, time_width=0.8), run_time=1.2)
        
        # Interactive pulse scanning along search_ray
        scan_dot = Dot(query_pt_b, radius=0.15, color=COLOR_CYAN)
        self.play(FadeIn(scan_dot), run_time=0.5)
        self.play(scan_dot.animate.move_to(needle_pt_b), run_time=2.0, rate_func=rate_functions.ease_in_out_quad)
        self.play(Flash(needle_pt_b, color=COLOR_EMERALD, flash_radius=0.4), FadeOut(scan_dot), run_time=1.0)
        self.wait(2.0)

        # Clean up tracks to reveal the final production architecture banner
        self.play(
            FadeOut(track_a_line), FadeOut(lbl_track_a), FadeOut(track_b_line), FadeOut(lbl_track_b),
            FadeOut(needle_dot_a), FadeOut(needle_dot_b), FadeOut(needle_lbl),
            FadeOut(query_dot_a), FadeOut(query_dot_b), FadeOut(query_lbl),
            FadeOut(window_a), FadeOut(res_a_badge), FadeOut(res_a_txt),
            FadeOut(search_ray), FadeOut(res_b_badge), FadeOut(res_b_txt),
            run_time=1.2
        )

        # -------------------------------------------------------------
        # BEAT 3: Production 2-Tier Architecture Blueprint (55 - 84.3s)
        # -------------------------------------------------------------
        arch_box = RoundedRectangle(
            corner_radius=0.14, width=10.2, height=2.5,
            fill_color=COLOR_CARD_BG, fill_opacity=0.95, stroke_color=COLOR_GOLD, stroke_width=1.5
        ).shift(DOWN * 0.4)
        arch_title = Text("KIẾN TRÚC HYBRID 2 TẦNG CHUẨN THỰC TẾ TRONG DOANH NGHIỆP:", font=FONT_FAMILY, font_size=12, weight=BOLD, color=COLOR_GOLD).move_to(arch_box.get_top() + DOWN * 0.35)

        t1_box = RoundedRectangle(corner_radius=0.08, width=4.5, height=1.3, fill_color="#1e1828", fill_opacity=0.9, stroke_color=COLOR_AMBER, stroke_width=1.2).shift(DOWN * 0.6 + LEFT * 2.4)
        t1_lbl_hdr = Text("TẦNG NGOÀI: StreamingLLM\nHội thoại liên tục • Độ trễ < 15ms\nVRAM cố định 4.2 GB", font=FONT_FAMILY, font_size=12.0, color=COLOR_TEXT, line_spacing=1.2).move_to(t1_box)

        t2_box = RoundedRectangle(corner_radius=0.08, width=4.5, height=1.3, fill_color="#122424", fill_opacity=0.9, stroke_color=COLOR_CYAN, stroke_width=1.2).shift(DOWN * 0.6 + RIGHT * 2.4)
        t2_lbl_hdr = Text("TẦNG TRONG: YaRN 128K + RAG\nTruy hồi sự thật • Soi xét hợp đồng\nĐộ chính xác 99.8% • 0% Hallucination", font=FONT_FAMILY, font_size=12.0, color=COLOR_TEXT, line_spacing=1.2).move_to(t2_box)

        conn_arrow = DoubleArrow(t1_box.get_right(), t2_box.get_left(), color=COLOR_GOLD, stroke_width=2.5)

        self.play(FadeIn(arch_box), Write(arch_title), run_time=1.2)
        self.play(FadeIn(t1_box), Write(t1_lbl_hdr), Create(conn_arrow), FadeIn(t2_box), Write(t2_lbl_hdr), run_time=2.0)
        
        # Continuous token flow packets between Tier 1 and Tier 2
        p_q = Dot(t1_box.get_right(), radius=0.1, color=COLOR_AMBER)
        p_a = Dot(t2_box.get_left(), radius=0.1, color=COLOR_CYAN)

        self.play(FadeIn(p_q), run_time=0.4)
        self.play(p_q.animate.move_to(t2_box.get_left()), run_time=2.2, rate_func=rate_functions.ease_in_out_sine)
        self.play(FadeOut(p_q), FadeIn(p_a), run_time=0.4)
        self.play(p_a.animate.move_to(t1_box.get_right()), run_time=2.2, rate_func=rate_functions.ease_in_out_sine)
        self.play(FadeOut(p_a), run_time=0.4)

        # Second cycle of token flow & pulse
        self.play(
            arch_box.animate.set_stroke(color=COLOR_CYAN, width=1.8),
            conn_arrow.animate.set_color(COLOR_EMERALD),
            t1_box.animate.set_stroke(color=COLOR_GOLD, width=1.8),
            t2_box.animate.set_stroke(color=COLOR_EMERALD, width=1.8),
            run_time=6.0, rate_func=rate_functions.there_and_back
        )
        self.wait(3.0)


# =============================================================================
# SCENE 06: TỔNG KẾT KỸ NGHỆ & TEASER TẬP 04 (OUTRO — 74.4s)
# =============================================================================
class Tap03Scene06Outro(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "TỔNG KẾT & CẦU NỐI KỸ NGHỆ")

        scene_title = Text(
            "BÀN GIAO TRI THỨC // YARN & MỞ RỘNG NGỮ CẢNH DÀI",
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
        # 1. Next Video Card (Episode 04: SwiGLU)
        next_card = RoundedRectangle(
            corner_radius=0.12, width=3.8, height=2.0,
            fill_color=COLOR_PANEL, fill_opacity=0.7, stroke_color=COLOR_CYAN, stroke_width=1.5
        ).move_to(RIGHT * 3.5 + UP * 1.5)
        next_header = Text("TẬP TIẾP THEO // TẬP 04", font=FONT_FAMILY, font_size=12.5, weight=BOLD, color=COLOR_CYAN)
        next_sub_header = Text("SWIGLU & DÒNG CHẢY GRADIENT", font=FONT_FAMILY, font_size=12.0, color=COLOR_TEXT).next_to(next_header, DOWN, buff=0.18)
        next_grp = VGroup(next_header, next_sub_header).move_to(next_card.get_center())

        # 2. Playlist Card
        pl_card = RoundedRectangle(
            corner_radius=0.12, width=3.8, height=1.3,
            fill_color=COLOR_PANEL, fill_opacity=0.7, stroke_color=COLOR_GOLD, stroke_width=1.5
        ).move_to(RIGHT * 3.5 + DOWN * 0.35)
        pl_header = Text("DANH SÁCH PHÁT SERIES 2", font=FONT_FAMILY, font_size=12.5, weight=BOLD, color=COLOR_GOLD)
        pl_sub_header = Text("THE ANATOMY OF MODERN LLMS", font=FONT_FAMILY, font_size=12.0, color=COLOR_MUTED).next_to(pl_header, DOWN, buff=0.15)
        pl_grp = VGroup(pl_header, pl_sub_header).move_to(pl_card.get_center())

        # 3. Subscribe Card
        sub_card = RoundedRectangle(
            corner_radius=0.12, width=3.8, height=1.1,
            fill_color=COLOR_PANEL, fill_opacity=0.7, stroke_color=COLOR_ROSE, stroke_width=1.5
        ).move_to(RIGHT * 3.5 + DOWN * 1.85)
        sub_header = Text("ĐĂNG KÝ KÊNH // ZENPHAM", font=FONT_FAMILY, font_size=12.5, weight=BOLD, color=COLOR_ROSE)
        sub_sub_header = Text("AI CRAFTSMANSHIP & ENGINEERING", font=FONT_FAMILY, font_size=12.0, color=COLOR_TEXT).next_to(sub_header, DOWN, buff=0.12)
        sub_grp = VGroup(sub_header, sub_sub_header).move_to(sub_card.get_center())

        right_grp = VGroup(next_card, next_grp, pl_card, pl_grp, sub_card, sub_grp)
        self.play(FadeIn(right_grp, shift=LEFT * 0.3), run_time=1.2)

        # Kinetic Pulse & Glow
        self.play(
            mosaic_frame.animate.set_stroke(COLOR_GOLD, width=2.2),
            next_card.animate.set_stroke(COLOR_GOLD, width=2.2),
            run_time=1.5
        )
        self.wait(2.0)

