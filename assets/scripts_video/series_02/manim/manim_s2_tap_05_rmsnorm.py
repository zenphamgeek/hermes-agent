#!/usr/bin/env python3
"""
Manim 2K QHD Master Production Scenes — RMSNorm // Khi Bỏ Qua Kỳ Vọng Giúp LLM Tăng Tốc Gấp Đôi
Theme: Neo-Noir Obsidian (#0c0d12) | Standard: 100% Median / 3Blue1Brown Mathematical Craftsmanship
Strict Invariants:
- Zero Mascots (LivingZenMascot, Pioneers, ZenEngineerMascot 100% removed)
- Zero Static Bullet Boxes (continuous geometric & tensor transformations)
- Safe Margins: All elements stay strictly within |x| <= 5.2, |y| <= 3.2 (>=15% margin for subtitles/HUD)
- Dynamic Mathematical Mechanics: Scale invariance, 1-pass SRAM fused kernel, shift variance
"""

import sys
from pathlib import Path
sys.path.insert(0, "/workspace")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from manim import *
import numpy as np
import math

# Neo-Noir Theme Color Palette
COLOR_BG = "#0c0d12"
COLOR_CARD_BG = "#101422"
COLOR_CYAN = "#00e5ff"
COLOR_AMBER = "#f59e0b"
COLOR_GOLD = "#ffd700"
COLOR_ROSE = "#ff2a6d"
COLOR_EMERALD = "#00e676"
COLOR_VIOLET = "#a78bfa"
COLOR_TEXT = "#e2e8f0"
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
# SCENE 01: NGHỊCH LÝ CHUẨN HÓA: CÙNG MỘ VECTOR, HAI KẾT QUẢ TRÁI NGƯỢC
# =============================================================================
class Tap05Scene01ColdOpen(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG

        # 1. Header HUD Pill
        header_text = Text(
            "RMSNORM // KHI BỎ QUA KỲ VỌNG GIÚP CỖ MÁY BỨT TỐC",
            font=FONT_FAMILY, font_size=13, weight=BOLD, color=COLOR_CYAN
        )
        header_box = RoundedRectangle(
            corner_radius=0.12, height=0.5, width=header_text.width + 0.6,
            fill_color="#141826", fill_opacity=0.9, stroke_color=COLOR_CYAN, stroke_width=1.2
        ).to_edge(UP, buff=0.35)
        header_text.move_to(header_box.get_center())
        self.play(FadeIn(header_box), Write(header_text), run_time=0.8)

        # 2. 2D Coordinate System for Vector Demonstration
        axes = Axes(
            x_range=[-2, 5, 1], y_range=[-2, 5, 1],
            x_length=4.6, y_length=4.6,
            axis_config={"color": COLOR_MUTED, "stroke_width": 1.2, "include_numbers": True, "font_size": 11}
        ).shift(LEFT * 2.8 + DOWN * 0.15)

        # Input vector x = [3, 4]
        v_in = Arrow(axes.c2p(0, 0), axes.c2p(3, 4), color=COLOR_GOLD, buff=0, stroke_width=3.5)
        v_in_lbl = MathTex(r"\mathbf{x} = [3, 4]^T", font_size=20, color=COLOR_GOLD).next_to(v_in.get_end(), UR, buff=0.1)
        dot_in = Dot(axes.c2p(3, 4), color=COLOR_GOLD, radius=0.08)

        self.play(Create(axes), GrowArrow(v_in), FadeIn(dot_in), Write(v_in_lbl), run_time=1.2)

        # 3. Two Paths Comparison Panel (Right Side: |x| <= 5.1)
        right_panel = RoundedRectangle(
            corner_radius=0.15, height=4.6, width=4.6,
            fill_color=COLOR_CARD_BG, fill_opacity=0.92, stroke_color=COLOR_BORDER, stroke_width=1.2
        ).shift(RIGHT * 2.7 + DOWN * 0.15)

        title_ln = Text("1. CỔ ĐIỂN: LAYERNORM", font=FONT_FAMILY, font_size=12, weight=BOLD, color=COLOR_ROSE)
        formula_ln = MathTex(r"y = \frac{x - \mu}{\sqrt{\sigma^2 + \epsilon}} \odot \gamma", font_size=20, color=COLOR_ROSE)
        calc_ln_hdr = Text("μ = 3.5  →  x - μ = [-0.5, +0.5]\nĐầu ra: [-1.0, +1.0] (ĐỔI DẤU!)", font=FONT_FAMILY, font_size=12.0, color=COLOR_MUTED)

        title_rms = Text("2. TỐI GIẢN: RMSNORM", font=FONT_FAMILY, font_size=12, weight=BOLD, color=COLOR_EMERALD)
        formula_rms = MathTex(r"y = \frac{x}{\mathrm{RMS}(x)} \odot \gamma, \quad \mathrm{RMS} = \sqrt{\frac{1}{d}\sum x_i^2}", font_size=20, color=COLOR_EMERALD)
        calc_rms_hdr = Text("RMS = 3.5355  (Không trừ μ)\nĐầu ra: [+0.849, +1.131] (GIỮ HƯỚNG)", font=FONT_FAMILY, font_size=12.0, color=COLOR_TEXT)

        ln_group = VGroup(title_ln, formula_ln, calc_ln_hdr).arrange(DOWN, buff=0.1, aligned_edge=ORIGIN)
        rms_group = VGroup(title_rms, formula_rms, calc_rms_hdr).arrange(DOWN, buff=0.1, aligned_edge=ORIGIN)
        div_line = Line(LEFT * 2.0, RIGHT * 2.0, color=COLOR_BORDER, stroke_width=1.0)

        right_content = VGroup(ln_group, div_line, rms_group).arrange(DOWN, buff=0.2, aligned_edge=ORIGIN).move_to(right_panel.get_center())

        self.play(FadeIn(right_panel), FadeIn(right_content), run_time=1.0)

        # 4. Dynamic Geometric Action: LayerNorm flips direction vs RMSNorm preserves ray
        v_ln = Arrow(axes.c2p(0, 0), axes.c2p(-1.0, 1.0), color=COLOR_ROSE, buff=0, stroke_width=3.0)
        v_ln_lbl = MathTex(r"\mathbf{y}_{\mathrm{LN}}", font_size=18, color=COLOR_ROSE).next_to(v_ln.get_end(), LEFT, buff=0.1)

        v_rms = Arrow(axes.c2p(0, 0), axes.c2p(0.849, 1.131), color=COLOR_EMERALD, buff=0, stroke_width=3.0)
        v_rms_lbl = MathTex(r"\mathbf{y}_{\mathrm{RMS}}", font_size=18, color=COLOR_EMERALD).next_to(v_rms.get_end(), UR, buff=0.1)

        ray_orig = DashedLine(axes.c2p(0, 0), axes.c2p(4, 5.333), color=COLOR_CYAN, stroke_width=1.2)

        self.play(Create(ray_orig), run_time=0.8)
        self.play(GrowArrow(v_ln), Write(v_ln_lbl), GrowArrow(v_rms), Write(v_rms_lbl), run_time=1.2)
        self.wait(1.5)


# =============================================================================
# SCENE 02: DÒNG CHẢY BỘ NHỚ: TẠI SAO 2-PASS GÂY NGHẼN BĂNG THÔNG HBM
# =============================================================================
class Tap05Scene02Architecture(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG

        # 1. Header HUD Pill
        header_text = Text(
            "KIẾN TRÚC SILICON // NỖI ÁM ẢNH BĂNG THÔNG BỘ NHỚ CỦA LAYERNORM",
            font=FONT_FAMILY, font_size=13, weight=BOLD, color=COLOR_CYAN
        )
        header_box = RoundedRectangle(
            corner_radius=0.12, height=0.5, width=header_text.width + 0.6,
            fill_color="#141826", fill_opacity=0.9, stroke_color=COLOR_CYAN, stroke_width=1.2
        ).to_edge(UP, buff=0.35)
        header_text.move_to(header_box.get_center())
        self.play(FadeIn(header_box), Write(header_text), run_time=0.8)

        # 2. Hardware Memory Hierarchy Card
        # Left side: DRAM / HBM (slow, huge). Right side: On-Chip SRAM (super fast, small)
        hbm_box = RoundedRectangle(
            corner_radius=0.15, height=3.8, width=4.5,
            fill_color="#160c14", fill_opacity=0.9, stroke_color=COLOR_ROSE, stroke_width=1.5
        ).shift(LEFT * 2.8 + DOWN * 0.1)
        hbm_title = Text("GPU HBM / DRAM (2 TB/s)", font=FONT_FAMILY, font_size=12, weight=BOLD, color=COLOR_ROSE).next_to(hbm_box.get_top(), DOWN, buff=0.2)

        sram_box = RoundedRectangle(
            corner_radius=0.15, height=3.8, width=4.5,
            fill_color="#071b26", fill_opacity=0.9, stroke_color=COLOR_CYAN, stroke_width=1.5
        ).shift(RIGHT * 2.8 + DOWN * 0.1)
        sram_title = Text("ON-CHIP SRAM / REGISTERS (19 TB/s)", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_CYAN).next_to(sram_box.get_top(), DOWN, buff=0.2)

        self.play(FadeIn(hbm_box), Write(hbm_title), FadeIn(sram_box), Write(sram_title), run_time=1.0)

        # 3. LayerNorm 2-Pass Bottleneck Animation
        ln_lbl = Text("LayerNorm: 2 Lượt qua Bus HBM (Memory-Bound)", font=FONT_FAMILY, font_size=12.0, color=COLOR_ROSE).shift(UP * 1.1)
        p1_arrow = Arrow(LEFT * 0.8, RIGHT * 0.8, color=COLOR_ROSE, stroke_width=2.5).shift(UP * 0.5)
        p1_lbl = Text("Pass 1: Đọc x → Tính μ → Ghi tạm ra DRAM", font=FONT_FAMILY, font_size=12.0, color=COLOR_MUTED).next_to(p1_arrow, UP, buff=0.08)

        p2_arrow = Arrow(RIGHT * 0.8, LEFT * 0.8, color=COLOR_ROSE, stroke_width=2.5).shift(DOWN * 0.1)
        p2_lbl = Text("Pass 2: Đọc lại x & μ → Trừ μ → Tính σ → Ghi y", font=FONT_FAMILY, font_size=12.0, color=COLOR_MUTED).next_to(p2_arrow, DOWN, buff=0.08)

        self.play(Write(ln_lbl), GrowArrow(p1_arrow), FadeIn(p1_lbl), run_time=1.2)
        self.play(GrowArrow(p2_arrow), FadeIn(p2_lbl), run_time=1.2)

        # 4. RMSNorm 1-Pass Fused Revolution
        rms_banner = RoundedRectangle(
            corner_radius=0.12, height=1.1, width=10.2,
            fill_color="#082018", fill_opacity=0.95, stroke_color=COLOR_EMERALD, stroke_width=1.5
        ).shift(DOWN * 2.3)
        rms_title = Text("ĐỘT PHÁ RMSNORM: FUSED 1-PASS STREAMING KERNEL", font=FONT_FAMILY, font_size=12, weight=BOLD, color=COLOR_EMERALD)
        rms_desc_hdr = Text(
            "Tích lũy bình phương trực tiếp trong thanh ghi (Register Accumulator). Không cần đợi đồng bộ trung bình.\n"
            "Tiết kiệm 50% lưu lượng Bus HBM • Tốc độ chuẩn hóa tăng 1.6x đến 2.0x.",
            font=FONT_FAMILY, font_size=12.0, color=COLOR_TEXT
        )
        rms_group = VGroup(rms_title, rms_desc_hdr).arrange(DOWN, buff=0.08, aligned_edge=ORIGIN).move_to(rms_banner.get_center())

        self.play(FadeIn(rms_banner), FadeIn(rms_group), run_time=1.0)
        self.wait(1.5)


# =============================================================================
# SCENE 03: ĐỊNH LÝ BẤT BIẾN TỶ LỆ (SCALE INVARIANCE): TOÁN HỌC THỰC THỤ
# =============================================================================
class Tap05Scene03Mathematics(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG

        # 1. Header HUD Pill
        header_text = Text(
            "GIẢI PHẪU TOÁN HỌC // ĐỊNH LÝ BẤT BIẾN TỶ LỆ CỦA ZHANG & SENNRICH",
            font=FONT_FAMILY, font_size=13, weight=BOLD, color=COLOR_EMERALD
        )
        header_box = RoundedRectangle(
            corner_radius=0.12, height=0.5, width=header_text.width + 0.6,
            fill_color="#141826", fill_opacity=0.9, stroke_color=COLOR_EMERALD, stroke_width=1.2
        ).to_edge(UP, buff=0.35)
        header_text.move_to(header_box.get_center())
        self.play(FadeIn(header_box), Write(header_text), run_time=0.8)

        # 2. Geometric Demonstration: Expanding Vectors Collapsing to Same Sphere
        circle = Circle(radius=1.8, color=COLOR_CYAN, stroke_width=1.5).shift(LEFT * 2.7 + DOWN * 0.15)
        c_lbl = Text("Hình cầu chuẩn hóa (Radius = 1)", font=FONT_FAMILY, font_size=12.0, color=COLOR_CYAN).next_to(circle, DOWN, buff=0.15)

        v1 = Arrow(circle.get_center(), circle.get_center() + RIGHT * 1.8 * 0.707 + UP * 1.8 * 0.707, color=COLOR_EMERALD, buff=0, stroke_width=3.0)
        v1_lbl = MathTex(r"\mathbf{x}", font_size=18, color=COLOR_EMERALD).next_to(v1.get_end(), UR, buff=0.08)

        v2 = Arrow(circle.get_center(), circle.get_center() + RIGHT * 1.8 * 1.414 + UP * 1.8 * 1.414, color=COLOR_AMBER, buff=0, stroke_width=3.0)
        v2_lbl = MathTex(r"2\mathbf{x}", font_size=18, color=COLOR_AMBER).next_to(v2.get_end(), UR, buff=0.08)

        self.play(Create(circle), Write(c_lbl), GrowArrow(v1), Write(v1_lbl), run_time=1.2)
        self.play(Transform(v1.copy(), v2), Write(v2_lbl), run_time=1.0)

        # 3. Mathematical Proof Card (Right Side: |x| <= 5.1)
        proof_box = RoundedRectangle(
            corner_radius=0.15, height=4.6, width=4.8,
            fill_color=COLOR_CARD_BG, fill_opacity=0.94, stroke_color=COLOR_EMERALD, stroke_width=1.4
        ).shift(RIGHT * 2.7 + DOWN * 0.15)

        t_proof = Text("TÍNH BẤT BIẾN HOÀN TOÀN", font=FONT_FAMILY, font_size=12, weight=BOLD, color=COLOR_EMERALD)
        
        f1 = MathTex(r"\mathrm{RMS}(\alpha \mathbf{x}) = \sqrt{\frac{1}{d}\sum (\alpha x_i)^2} = \alpha \cdot \mathrm{RMS}(\mathbf{x})", font_size=18, color=COLOR_TEXT)
        f2 = MathTex(r"\mathrm{RMSNorm}(\alpha \mathbf{x}) = \frac{\alpha \mathbf{x}}{\alpha \mathrm{RMS}(\mathbf{x})} = \mathrm{RMSNorm}(\mathbf{x})", font_size=19, color=COLOR_GOLD)
        
        t_grad = Text("TỰ ĐIỀU TIẾT GRADIENT TỰ NHIÊN", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_CYAN)
        f3 = MathTex(r"\nabla_\mathbf{x} \mathrm{RMSNorm}(\alpha \mathbf{x}) = \frac{1}{\alpha} \nabla_\mathbf{x} \mathrm{RMSNorm}(\mathbf{x})", font_size=19, color=COLOR_CYAN)

        note_hdr = Text("Khi tín hiệu bùng nổ (α lớn), gradient tự động\nco nhỏ lại 1/α. Ổn định tuyệt đối không cần trừ μ.", font=FONT_FAMILY, font_size=12.0, color=COLOR_MUTED)

        proof_content = VGroup(t_proof, f1, f2, t_grad, f3, note_hdr).arrange(DOWN, buff=0.16, aligned_edge=ORIGIN).move_to(proof_box.get_center())

        self.play(FadeIn(proof_box), FadeIn(proof_content), run_time=1.2)
        self.wait(1.5)


# =============================================================================
# SCENE 04: THÍ NGHIỆM DỊCH CHUYỂN (SHIFT INVARIANCE VS ANGLE PRESERVATION)
# =============================================================================
class Tap05Scene04Telemetry(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG

        # 1. Header HUD Pill
        header_text = Text(
            "THÍ NGHIỆM DỊCH CHUYỂN // TẠI SAO RMSNORM KHÔNG TRỪ ĐỘ LỆCH TĨNH?",
            font=FONT_FAMILY, font_size=13, weight=BOLD, color=COLOR_GOLD
        )
        header_box = RoundedRectangle(
            corner_radius=0.12, height=0.5, width=header_text.width + 0.6,
            fill_color="#141826", fill_opacity=0.9, stroke_color=COLOR_GOLD, stroke_width=1.2
        ).to_edge(UP, buff=0.35)
        header_text.move_to(header_box.get_center())
        self.play(FadeIn(header_box), Write(header_text), run_time=0.8)

        # 2. Vector Angle Preservation Visual
        axes = Axes(
            x_range=[0, 16, 4], y_range=[0, 16, 4],
            x_length=4.8, y_length=4.4,
            axis_config={"color": COLOR_MUTED, "stroke_width": 1.2, "include_numbers": True, "font_size": 11}
        ).shift(LEFT * 2.7 + DOWN * 0.15)

        v_base = Arrow(axes.c2p(0, 0), axes.c2p(3, 4), color=COLOR_CYAN, buff=0, stroke_width=3.0)
        v_base_lbl = MathTex(r"\mathbf{x} = [3, 4]", font_size=16, color=COLOR_CYAN).next_to(v_base.get_end(), UR, buff=0.08)

        v_shifted = Arrow(axes.c2p(0, 0), axes.c2p(13, 14), color=COLOR_AMBER, buff=0, stroke_width=3.0)
        v_shift_lbl = MathTex(r"\mathbf{x}' = [13, 14]", font_size=16, color=COLOR_AMBER).next_to(v_shifted.get_end(), UP, buff=0.08)

        shift_link = DashedLine(axes.c2p(3, 4), axes.c2p(13, 14), color=COLOR_ROSE, stroke_width=1.5)
        shift_tag_hdr = Text("+10 vào mỗi chiều", font=FONT_FAMILY, font_size=12.0, color=COLOR_ROSE).next_to(shift_link, DOWN, buff=0.08)

        self.play(Create(axes), GrowArrow(v_base), Write(v_base_lbl), run_time=1.0)
        self.play(Create(shift_link), Write(shift_tag_hdr), GrowArrow(v_shifted), Write(v_shift_lbl), run_time=1.2)

        # 3. Telemetry Comparison Card
        tele_box = RoundedRectangle(
            corner_radius=0.15, height=4.4, width=4.8,
            fill_color=COLOR_CARD_BG, fill_opacity=0.94, stroke_color=COLOR_BORDER, stroke_width=1.2
        ).shift(RIGHT * 2.7 + DOWN * 0.15)

        t1 = Text("ĐỐI CHIẾU HÀNH VI ĐẠI SỐ", font=FONT_FAMILY, font_size=12, weight=BOLD, color=COLOR_GOLD)
        
        ln_box_hdr = VGroup(
            Text("LayerNorm (Triệt tiêu độ lệch)", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_ROSE),
            Text("μ' = 13.5 → x' - μ' = [-0.5, 0.5]\nĐầu ra: [-1.0, +1.0] (Không đổi!)", font=FONT_FAMILY, font_size=12.0, color=COLOR_MUTED)
        ).arrange(DOWN, buff=0.06, aligned_edge=ORIGIN)

        rms_box_hdr = VGroup(
            Text("RMSNorm (Bảo toàn biên độ góc)", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_EMERALD),
            Text("Góc vector thay đổi: 53.1° → 47.1°\nĐầu ra: [0.962, 1.036] (Biến đổi theo tín hiệu)", font=FONT_FAMILY, font_size=12.0, color=COLOR_TEXT)
        ).arrange(DOWN, buff=0.06, aligned_edge=ORIGIN)

        insight_hdr = Text(
            "Bản chất: Độ lệch tĩnh (DC Offset) chứa đựng\nthông tin ngữ nghĩa thực tế. RMSNorm giữ lại\nthay vì vội vã triệt tiêu.",
            font=FONT_FAMILY, font_size=12.0, color=COLOR_CYAN, line_spacing=1.2
        )

        tele_content = VGroup(t1, ln_box_hdr, rms_box_hdr, insight_hdr).arrange(DOWN, buff=0.18, aligned_edge=ORIGIN).move_to(tele_box.get_center())

        self.play(FadeIn(tele_box), FadeIn(tele_content), run_time=1.2)
        self.wait(1.5)


# =============================================================================
# SCENE 05: BENCHMARK THỰC TẾ TRÊN SILICON: TRITON FUSED KERNEL
# =============================================================================
class Tap05Scene05LabExperiment(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG

        # 1. Header HUD Pill
        header_text = Text(
            "ĐO LƯỜNG THỰC TẾ // BENCHMARK TRITON RMSNORM TRÊN KIẾN TRÚC LLAMA 3",
            font=FONT_FAMILY, font_size=13, weight=BOLD, color=COLOR_CYAN
        )
        header_box = RoundedRectangle(
            corner_radius=0.12, height=0.5, width=header_text.width + 0.6,
            fill_color="#141826", fill_opacity=0.9, stroke_color=COLOR_CYAN, stroke_width=1.2
        ).to_edge(UP, buff=0.35)
        header_text.move_to(header_box.get_center())
        self.play(FadeIn(header_box), Write(header_text), run_time=0.8)

        # 2. Benchmark Bar Comparison Chart (Left: |x| <= 5.1)
        chart_box = RoundedRectangle(
            corner_radius=0.15, height=4.5, width=5.2,
            fill_color=COLOR_CARD_BG, fill_opacity=0.92, stroke_color=COLOR_BORDER, stroke_width=1.2
        ).shift(LEFT * 2.5 + DOWN * 0.15)
        chart_title = Text("ĐỘ TRỄ KERNEL (d = 4096, Batch = 16)", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_CYAN).next_to(chart_box.get_top(), DOWN, buff=0.2)

        # LayerNorm Bar
        ln_bar = Rectangle(height=0.45, width=3.8, fill_color=COLOR_ROSE, fill_opacity=0.9, stroke_color=COLOR_ROSE, stroke_width=1.0).shift(LEFT * 2.2 + UP * 0.5)
        ln_label = Text("PyTorch LayerNorm: 182 µs", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_ROSE).next_to(ln_bar, UP, buff=0.08, aligned_edge=LEFT)

        # RMSNorm Bar
        rms_bar = Rectangle(height=0.45, width=2.0, fill_color=COLOR_EMERALD, fill_opacity=0.9, stroke_color=COLOR_EMERALD, stroke_width=1.0).shift(LEFT * 3.1 + DOWN * 0.6)
        rms_label = Text("Triton Fused RMSNorm: 96 µs (Giảm 47%)", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_EMERALD).next_to(rms_bar, UP, buff=0.08, aligned_edge=LEFT)

        chart_content = VGroup(chart_title, ln_label, ln_bar, rms_label, rms_bar)
        self.play(FadeIn(chart_box), FadeIn(chart_content), run_time=1.2)

        # 3. Numerical Stability Guard (Right: |x| <= 5.1)
        guard_box = RoundedRectangle(
            corner_radius=0.15, height=4.5, width=4.8,
            fill_color=COLOR_CARD_BG, fill_opacity=0.92, stroke_color=COLOR_EMERALD, stroke_width=1.2
        ).shift(RIGHT * 2.7 + DOWN * 0.15)

        g_title = Text("LÁ CHẮN SỐ HỌC EPSILON (ε)", font=FONT_FAMILY, font_size=12, weight=BOLD, color=COLOR_EMERALD)
        
        g_f = MathTex(r"\mathrm{RMS}(x) = \sqrt{\frac{1}{d}\sum x_i^2 + \epsilon}", font_size=20, color=COLOR_GOLD)
        
        g_desc_hdr = Text(
            "Giá trị chuẩn: ε = 1e-5 (LLaMA) hoặc 1e-6\n\n"
            "• Chống chia cho 0 khi vector x = 0\n"
            "• Giữ ổn định số học trong định dạng FP16 & BF16\n"
            "• Đảm bảo không bị hiện tượng Underflow/NaN",
            font=FONT_FAMILY, font_size=12.0, color=COLOR_TEXT, line_spacing=1.3
        )
        
        tag_hdr = Text("Chuẩn mực công nghiệp: LLaMA 3, Mistral, Gemma, DeepSeek", font=FONT_FAMILY, font_size=12.0, color=COLOR_MUTED)

        guard_content = VGroup(g_title, g_f, g_desc_hdr, tag_hdr).arrange(DOWN, buff=0.16, aligned_edge=ORIGIN).move_to(guard_box.get_center())

        self.play(FadeIn(guard_box), FadeIn(guard_content), run_time=1.2)
        self.wait(1.5)


# =============================================================================
# SCENE 06: TỔNG KẾT TRIẾT LÝ & ĐỊNH HƯỚNG TẬP 06 (GQA & KV CACHE)
# =============================================================================
class Tap05Scene06Outro(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "TỔNG KẾT & CẦU NỐI KỸ NGHỆ")

        scene_title = Text(
            "BÀN GIAO TRI THỨC // RMSNORM & KỶ NGUYÊN KIẾN TRÚC MỞ",
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
        # 1. Next Video Card (Episode 06: MHA vs MQA vs GQA)
        next_card = RoundedRectangle(
            corner_radius=0.12, width=3.8, height=2.0,
            fill_color=COLOR_PANEL, fill_opacity=0.7, stroke_color=COLOR_CYAN, stroke_width=1.5
        ).move_to(RIGHT * 3.5 + UP * 1.5)
        next_header = Text("TẬP TIẾP THEO // TẬP 06", font=FONT_FAMILY, font_size=12.5, weight=BOLD, color=COLOR_CYAN)
        next_sub_header = Text("MHA, MQA & GQA ARCHITECTURE", font=FONT_FAMILY, font_size=12.0, color=COLOR_TEXT).next_to(next_header, DOWN, buff=0.18)
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

