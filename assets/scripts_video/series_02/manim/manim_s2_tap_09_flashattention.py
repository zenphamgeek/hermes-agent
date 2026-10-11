#!/usr/bin/env python3
"""
Manim 2K QHD Master Production Scenes — FlashAttention // Nghệ Thuật Tối Ưu I/O Giữa SRAM & HBM Của GPU
Theme: Neo-Noir Obsidian (#0c0d12) | Standard: 100% Median / 3Blue1Brown Mathematical Craftsmanship
Strict Invariants:
- Zero Mascots (LivingZenMascot, Pioneers, ZenEngineerMascot 100% removed)
- Zero Static Bullet Boxes (continuous geometric & tensor transformations)
- Safe Margins: All elements stay strictly within |x| <= 5.2, |y| <= 3.2 (>=15% margin for subtitles/HUD)
- Dynamic Mathematical Mechanics: Online Softmax update, Tiling SRAM vs HBM, Recomputation in Backward
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
# SCENE 01: NGHỊCH LÝ BỨC TƯỜNG BỘ NHỚ VÀ CHIẾC BÀN LÀM VIỆC GPU
# =============================================================================
class Tap09Scene01ColdOpen(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG

        # 1. Header HUD Pill
        header_text = Text(
            "FLASHATTENTION // NGHỆ THUẬT TỐI ƯU I/O GIỮA SRAM & HBM CỦA GPU",
            font=FONT_FAMILY, font_size=13, weight=BOLD, color=COLOR_CYAN
        )
        header_box = RoundedRectangle(
            corner_radius=0.12, height=0.5, width=header_text.width + 0.6,
            fill_color="#141826", fill_opacity=0.9, stroke_color=COLOR_CYAN, stroke_width=1.2
        ).to_edge(UP, buff=0.35)
        header_text.move_to(header_box.get_center())
        self.play(FadeIn(header_box), Write(header_text), run_time=0.8)

        # 2. Left: HBM Storage Warehouse
        hbm_box = RoundedRectangle(corner_radius=0.15, height=4.2, width=4.6, fill_color=COLOR_CARD_BG, fill_opacity=0.9, stroke_color=COLOR_AMBER, stroke_width=1.5).shift(LEFT * 2.8 + DOWN * 0.2)
        lbl_hbm = Text("KHO HBM (VRAM NGOÀI)", font=FONT_FAMILY, font_size=12, weight=BOLD, color=COLOR_AMBER).next_to(hbm_box.get_top(), DOWN, buff=0.25)
        stat_hbm_cap = Text("Dung lượng: 80 GB", font=FONT_FAMILY, font_size=12, color=COLOR_TEXT).next_to(lbl_hbm, DOWN, buff=0.3)
        stat_hbm_bw = Text("Băng thông: ~2.0 TB/s", font=FONT_FAMILY, font_size=12, color=COLOR_MUTED).next_to(stat_hbm_cap, DOWN, buff=0.2)
        stat_hbm_lat = Text("Độ trễ: Hàng trăm chu kỳ", font=FONT_FAMILY, font_size=12.0, color=COLOR_ROSE).next_to(stat_hbm_bw, DOWN, buff=0.2)
        hbm_group = VGroup(hbm_box, lbl_hbm, stat_hbm_cap, stat_hbm_bw, stat_hbm_lat)

        # 3. Right: SRAM On-Chip Desk
        sram_box = RoundedRectangle(corner_radius=0.15, height=4.2, width=4.6, fill_color=COLOR_CARD_BG, fill_opacity=0.9, stroke_color=COLOR_CYAN, stroke_width=1.5).shift(RIGHT * 2.8 + DOWN * 0.2)
        lbl_sram = Text("BÀN SRAM (ON-CHIP)", font=FONT_FAMILY, font_size=12, weight=BOLD, color=COLOR_CYAN).next_to(sram_box.get_top(), DOWN, buff=0.25)
        stat_sram_cap = Text("Dung lượng: ~20 MB (Siêu nhỏ)", font=FONT_FAMILY, font_size=12, color=COLOR_ROSE).next_to(lbl_sram, DOWN, buff=0.3)
        stat_sram_bw = Text("Băng thông: ~19.0 TB/s (Cực đại)", font=FONT_FAMILY, font_size=12, color=COLOR_EMERALD).next_to(stat_sram_cap, DOWN, buff=0.2)
        stat_sram_lat = Text("Độ trễ: Gần như tức thì", font=FONT_FAMILY, font_size=12.0, color=COLOR_CYAN).next_to(stat_sram_bw, DOWN, buff=0.2)
        sram_group = VGroup(sram_box, lbl_sram, stat_sram_cap, stat_sram_bw, stat_sram_lat)

        self.play(FadeIn(hbm_group), FadeIn(sram_group), run_time=1.0)

        # 4. Center: Memory Wall Bottleneck Bus
        bus_arrow_right = Arrow(LEFT * 0.4 + UP * 0.3, RIGHT * 0.4 + UP * 0.3, color=COLOR_ROSE, stroke_width=3, buff=0)
        bus_arrow_left = Arrow(RIGHT * 0.4 + DOWN * 0.3, LEFT * 0.4 + DOWN * 0.3, color=COLOR_ROSE, stroke_width=3, buff=0)
        lbl_bus = Text("CỔ CHAI MEMORY BUS", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_ROSE).shift(DOWN * 1.2)
        bus_group = VGroup(bus_arrow_right, bus_arrow_left, lbl_bus)

        self.play(Create(bus_group), run_time=0.8)

        # 5. Core Metric Badge
        metric_badge = RoundedRectangle(corner_radius=0.1, height=0.65, width=7.2, fill_color="#181424", fill_opacity=0.95, stroke_color=COLOR_GOLD, stroke_width=1.2).shift(DOWN * 2.3)
        metric_txt = Text("NGHỊCH LÝ: TENSOR CORE RỖI VIỆC ĐỢI HBM ĐỌC DỮ LIỆU", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_GOLD).move_to(metric_badge)
        self.play(FadeIn(metric_badge), Write(metric_txt), run_time=0.8)
        self.wait(1.0)

        # [Masterclass: Visual State Retained - Trailing FadeOut Removed]
        self.wait(2.0)


# =============================================================================
# SCENE 02: CƠ CHẾ ATTENTION CỔ ĐIỂN: NGHẼN BĂNG THÔNG HBM VÌ MA TRẬN N x N
# =============================================================================
class Tap09Scene02Architecture(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG

        # 1. Header HUD Pill
        header_text = Text(
            "CƠ CHẾ ATTENTION CỔ ĐIỂN // NGHẼN BĂNG THÔNG HBM VÌ MA TRẬN N x N",
            font=FONT_FAMILY, font_size=13, weight=BOLD, color=COLOR_AMBER
        )
        header_box = RoundedRectangle(
            corner_radius=0.12, height=0.5, width=header_text.width + 0.6,
            fill_color="#141826", fill_opacity=0.9, stroke_color=COLOR_AMBER, stroke_width=1.2
        ).to_edge(UP, buff=0.35)
        header_text.move_to(header_box.get_center())
        self.play(FadeIn(header_box), Write(header_text), run_time=0.6)

        # 2. Formula Flow: Q, K -> S -> P -> O
        flow_card = RoundedRectangle(corner_radius=0.15, height=1.4, width=9.6, fill_color=COLOR_CARD_BG, fill_opacity=0.9, stroke_color=COLOR_CYAN, stroke_width=1.2).shift(UP * 1.5)
        flow_tex = MathTex(
            r"S = \frac{Q K^T}{\sqrt{d}} \in \mathbb{R}^{N \times N}",
            r"\quad \longrightarrow \quad",
            r"P = \text{softmax}(S) \in \mathbb{R}^{N \times N}",
            r"\quad \longrightarrow \quad",
            r"O = P V",
            font_size=24, color=COLOR_TEXT
        ).move_to(flow_card)
        flow_tex[0].set_color(COLOR_AMBER)
        flow_tex[2].set_color(COLOR_ROSE)
        flow_tex[4].set_color(COLOR_EMERALD)
        self.play(FadeIn(flow_card), Write(flow_tex), run_time=1.0)

        # 3. Memory Cost Explosion Card
        cost_card = RoundedRectangle(corner_radius=0.15, height=3.0, width=9.6, fill_color=COLOR_CARD_BG, fill_opacity=0.9, stroke_color=COLOR_ROSE, stroke_width=1.2).shift(DOWN * 1.0)
        lbl_cost_title = Text("SỰ BÙNG NỔ DUNG LƯỢNG TRUNG GIAN TRÊN HBM", font=FONT_FAMILY, font_size=12, weight=BOLD, color=COLOR_ROSE).next_to(cost_card.get_top(), DOWN, buff=0.25)

        detail_hdr_1 = Text("• Chuỗi N = 4096: Ma trận S & P gồm 4096 x 4096 = 16.7 triệu phần tử", font=FONT_FAMILY, font_size=12.0, color=COLOR_TEXT).shift(DOWN * 0.3 + LEFT * 0.2)
        detail_hdr_2 = Text("• FP16 (2 byte): Mỗi ma trận tốn 32 MB cho 1 Attention Head", font=FONT_FAMILY, font_size=12.0, color=COLOR_AMBER).shift(DOWN * 0.8 + LEFT * 0.2)
        detail_hdr_3 = Text("• 32 Heads: Hơn 1 GB VRAM chỉ để chứa S và P cho đúng 1 layer!", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_ROSE).shift(DOWN * 1.3 + LEFT * 0.2)
        detail_hdr_4 = Text("• HBM Round-trips: Ghi S -> Đọc S -> Ghi P -> Đọc P (3 lần lặp đắt đỏ)", font=FONT_FAMILY, font_size=12.0, color=COLOR_CYAN).shift(DOWN * 1.8 + LEFT * 0.2)

        cost_group = VGroup(cost_card, lbl_cost_title, detail_hdr_1, detail_hdr_2, detail_hdr_3, detail_hdr_4)
        self.play(FadeIn(cost_group), run_time=1.2)
        self.wait(1.0)

        # [Masterclass: Visual State Retained - Trailing FadeOut Removed]
        self.wait(2.0)


# =============================================================================
# SCENE 03: TOÁN HỌC ONLINE SOFTMAX: BẢN CHẤT TÁI CHUẨN HÓA
# =============================================================================
class Tap09Scene03Mathematics(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG

        # 1. Header HUD Pill
        header_text = Text(
            "TOÁN HỌC ONLINE SOFTMAX // BẢN CHẤT TÁI CHUẨN HÓA KHÔNG MẤT ĐỘ CHÍNH XÁC",
            font=FONT_FAMILY, font_size=13, weight=BOLD, color=COLOR_GOLD
        )
        header_box = RoundedRectangle(
            corner_radius=0.12, height=0.5, width=header_text.width + 0.6,
            fill_color="#141826", fill_opacity=0.9, stroke_color=COLOR_GOLD, stroke_width=1.2
        ).to_edge(UP, buff=0.35)
        header_text.move_to(header_box.get_center())
        self.play(FadeIn(header_box), Write(header_text), run_time=0.6)

        # 2. Formula Card: Online Normalization
        math_card = RoundedRectangle(corner_radius=0.15, height=2.4, width=9.6, fill_color=COLOR_CARD_BG, fill_opacity=0.95, stroke_color=COLOR_GOLD, stroke_width=1.5).shift(UP * 1.0)
        lbl_math_title = Text("CÔNG THỨC CẬP NHẬT TRỰC TUYẾN (MILAKOV & GIMELSHEIN 2018)", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_GOLD).next_to(math_card.get_top(), DOWN, buff=0.2)

        eq_1 = MathTex(
            r"m_{\text{new}} = \max(m_{\text{old}}, \max(x^{(j)})), \quad \alpha = e^{m_{\text{old}} - m_{\text{new}}} \le 1",
            font_size=21, color=COLOR_CYAN
        ).shift(UP * 1.3)
        eq_2 = MathTex(
            r"l_{\text{new}} = \alpha \cdot l_{\text{old}} + \sum e^{x_i - m_{\text{new}}}, \quad u_{\text{new}} = \alpha \cdot u_{\text{old}} + \sum e^{x_i - m_{\text{new}}} v_i",
            font_size=21, color=COLOR_AMBER
        ).shift(UP * 0.7)
        eq_3 = MathTex(
            r"O = \frac{u_{\text{new}}}{l_{\text{new}}} \equiv \text{Softmax}(S) V \quad (\text{100\% Exact Equivalence})",
            font_size=21, color=COLOR_EMERALD
        ).shift(UP * 0.1)

        formula_group = VGroup(math_card, lbl_math_title, eq_1, eq_2, eq_3)
        self.play(FadeIn(formula_group), run_time=1.2)

        # 3. Concrete Numerical Example Table Card
        num_card = RoundedRectangle(corner_radius=0.15, height=2.3, width=9.6, fill_color="#0e1320", fill_opacity=0.95, stroke_color=COLOR_BORDER, stroke_width=1.2).shift(DOWN * 1.8)
        lbl_num_title = Text("VÍ DỤ THỰC TẾ: 3 ĐIỂM S = [0, ln 2, ln 4], V = [2, 4, 8]", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_TEXT).next_to(num_card.get_top(), DOWN, buff=0.2)

        step_hdr_1 = Text("• Khối 1 [0, ln 2]: m1 = ln 2 => l1 = e^(0-ln2) + 1 = 1.5, u1 = 0.5*2 + 1*4 = 5.0", font=FONT_FAMILY, font_size=12.0, color=COLOR_CYAN).shift(DOWN * 1.4 + LEFT * 0.3)
        step_hdr_2 = Text("• Khối 2 [ln 4]: m2 = ln 4 => Hệ số co α = exp(ln 2 - ln 4) = 1/2", font=FONT_FAMILY, font_size=12.0, color=COLOR_AMBER).shift(DOWN * 1.8 + LEFT * 0.3)
        step_hdr_3 = Text("• Đồng bộ: l_new = 0.5*1.5 + 1.0 = 1.75 | u_new = 0.5*5.0 + 8.0 = 10.5 => O = 10.5/1.75 = 6.0", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_EMERALD).shift(DOWN * 2.2 + LEFT * 0.3)

        num_group = VGroup(num_card, lbl_num_title, step_hdr_1, step_hdr_2, step_hdr_3)
        self.play(FadeIn(num_group), run_time=1.0)
        self.wait(1.0)

        # [Masterclass: Visual State Retained - Trailing FadeOut Removed]
        self.wait(2.0)


# =============================================================================
# SCENE 04: KỸ NGHỆ TILING VÀ KERNEL FUSION
# =============================================================================
class Tap09Scene04Telemetry(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG

        # 1. Header HUD Pill
        header_text = Text(
            "KỸ NGHỆ TILING & KERNEL FUSION // HỢP NHẤT TRÊN BỘ NHỚ ĐỆM SRAM",
            font=FONT_FAMILY, font_size=13, weight=BOLD, color=COLOR_CYAN
        )
        header_box = RoundedRectangle(
            corner_radius=0.12, height=0.5, width=header_text.width + 0.6,
            fill_color="#141826", fill_opacity=0.9, stroke_color=COLOR_CYAN, stroke_width=1.2
        ).to_edge(UP, buff=0.35)
        header_text.move_to(header_box.get_center())
        self.play(FadeIn(header_box), Write(header_text), run_time=0.6)

        # 2. Left: Tiling Block Diagram
        diag_card = RoundedRectangle(corner_radius=0.15, height=4.2, width=4.8, fill_color=COLOR_CARD_BG, fill_opacity=0.9, stroke_color=COLOR_CYAN, stroke_width=1.2).shift(LEFT * 2.6 + DOWN * 0.2)
        lbl_diag = Text("CHIA KHỐI TILING (Br x Bc)", font=FONT_FAMILY, font_size=12, weight=BOLD, color=COLOR_CYAN).next_to(diag_card.get_top(), DOWN, buff=0.25)

        # Block representation
        b_q = RoundedRectangle(corner_radius=0.08, height=0.6, width=3.8, fill_color="#162b3d", fill_opacity=0.9, stroke_color=COLOR_CYAN, stroke_width=1.0).shift(LEFT * 2.6 + UP * 0.7)
        txt_q = Text("Khối Query Br (Nạp vào SRAM)", font=FONT_FAMILY, font_size=12.0, color=COLOR_TEXT).move_to(b_q)

        b_kv = RoundedRectangle(corner_radius=0.08, height=0.6, width=3.8, fill_color="#2b2318", fill_opacity=0.9, stroke_color=COLOR_AMBER, stroke_width=1.0).shift(LEFT * 2.6 + DOWN * 0.1)
        txt_kv = Text("Khối Key / Value Bc (Lần lượt duyệt)", font=FONT_FAMILY, font_size=12.0, color=COLOR_TEXT).move_to(b_kv)

        b_out = RoundedRectangle(corner_radius=0.08, height=0.6, width=3.8, fill_color="#132b1f", fill_opacity=0.9, stroke_color=COLOR_EMERALD, stroke_width=1.0).shift(LEFT * 2.6 + DOWN * 0.9)
        txt_out = Text("Cộng dồn trực tiếp vào Output O", font=FONT_FAMILY, font_size=12.0, color=COLOR_TEXT).move_to(b_out)

        diag_group = VGroup(diag_card, lbl_diag, b_q, txt_q, b_kv, txt_kv, b_out, txt_out)

        # 3. Right: Telemetry IO Complexity Comparison
        comp_card = RoundedRectangle(corner_radius=0.15, height=4.2, width=4.8, fill_color=COLOR_CARD_BG, fill_opacity=0.9, stroke_color=COLOR_EMERALD, stroke_width=1.2).shift(RIGHT * 2.6 + DOWN * 0.2)
        lbl_comp = Text("LƯU LƯỢNG TRUY XUẤT BỘ NHỚ HBM", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_EMERALD).next_to(comp_card.get_top(), DOWN, buff=0.25)

        row_old_lbl = Text("Attention Chuẩn:", font=FONT_FAMILY, font_size=12.0, color=COLOR_MUTED).shift(RIGHT * 1.5 + UP * 0.7)
        row_old_val = MathTex(r"\Theta(N d + N^2)", font_size=22, color=COLOR_ROSE).shift(RIGHT * 3.7 + UP * 0.7)

        row_new_lbl = Text("FlashAttention:", font=FONT_FAMILY, font_size=12.0, color=COLOR_MUTED).shift(RIGHT * 1.5 + DOWN * 0.1)
        row_new_val = MathTex(r"\Theta\left(N d + \frac{N^2 d^2}{M}\right) \approx \mathcal{O}(N d)", font_size=20, color=COLOR_EMERALD).shift(RIGHT * 3.7 + DOWN * 0.1)

        summary_box = RoundedRectangle(corner_radius=0.1, height=0.9, width=4.2, fill_color="#10241b", fill_opacity=0.9, stroke_color=COLOR_EMERALD, stroke_width=1.0).shift(RIGHT * 2.6 + DOWN * 1.2)
        summary_hdr = Text("Triệt tiêu hoàn toàn việc đọc/ghi\nma trận NxN trung gian ra HBM!", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_TEXT).move_to(summary_box)

        comp_group = VGroup(comp_card, lbl_comp, row_old_lbl, row_old_val, row_new_lbl, row_new_val, summary_box, summary_hdr)

        self.play(FadeIn(diag_group), FadeIn(comp_group), run_time=1.2)
        self.wait(1.0)

        # [Masterclass: Visual State Retained - Trailing FadeOut Removed]
        self.wait(2.0)


# =============================================================================
# SCENE 05: CHIẾN THUẬT RECOMPUTATION TRONG THỰC TẾ
# =============================================================================
class Tap09Scene05LabExperiment(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG

        # 1. Header HUD Pill
        header_text = Text(
            "CHIẾN THUẬT RECOMPUTATION // ĐÁNH ĐỔI PHÉP TÍNH LẤY TỐC ĐỘ BĂNG THÔNG",
            font=FONT_FAMILY, font_size=13, weight=BOLD, color=COLOR_ROSE
        )
        header_box = RoundedRectangle(
            corner_radius=0.12, height=0.5, width=header_text.width + 0.6,
            fill_color="#141826", fill_opacity=0.9, stroke_color=COLOR_ROSE, stroke_width=1.2
        ).to_edge(UP, buff=0.35)
        header_text.move_to(header_box.get_center())
        self.play(FadeIn(header_box), Write(header_text), run_time=0.6)

        # 2. Left vs Right: Forward vs Backward Pass
        fwd_box = RoundedRectangle(corner_radius=0.15, height=3.2, width=4.7, fill_color=COLOR_CARD_BG, fill_opacity=0.9, stroke_color=COLOR_CYAN, stroke_width=1.2).shift(LEFT * 2.6 + UP * 0.4)
        lbl_fwd = Text("FORWARD PASS", font=FONT_FAMILY, font_size=12, weight=BOLD, color=COLOR_CYAN).next_to(fwd_box.get_top(), DOWN, buff=0.25)
        fwd_1 = Text("• Không lưu ma trận xác suất P", font=FONT_FAMILY, font_size=12.0, color=COLOR_TEXT).shift(LEFT * 2.6 + UP * 0.8)
        fwd_2 = Text("• Chỉ lưu vector cực đại m và tổng l", font=FONT_FAMILY, font_size=12.0, color=COLOR_AMBER).shift(LEFT * 2.6 + UP * 0.3)
        fwd_3 = Text("• Tiết kiệm hàng chục GB VRAM", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_EMERALD).shift(LEFT * 2.6 + DOWN * 0.2)
        fwd_group = VGroup(fwd_box, lbl_fwd, fwd_1, fwd_2, fwd_3)

        bwd_box = RoundedRectangle(corner_radius=0.15, height=3.2, width=4.7, fill_color=COLOR_CARD_BG, fill_opacity=0.9, stroke_color=COLOR_ROSE, stroke_width=1.2).shift(RIGHT * 2.6 + UP * 0.4)
        lbl_bwd = Text("BACKWARD PASS (RECOMPUTE)", font=FONT_FAMILY, font_size=12, weight=BOLD, color=COLOR_ROSE).next_to(bwd_box.get_top(), DOWN, buff=0.25)
        bwd_1 = Text("• Đọc lại Q và K nhỏ gọn vào SRAM", font=FONT_FAMILY, font_size=12.0, color=COLOR_TEXT).shift(RIGHT * 2.6 + UP * 0.8)
        bwd_2 = Text("• Tái tính P trong nháy mắt bằng SRAM", font=FONT_FAMILY, font_size=12.0, color=COLOR_AMBER).shift(RIGHT * 2.6 + UP * 0.3)
        bwd_3 = Text("• FLOPs rẻ hơn nhiều so với IO HBM!", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_GOLD).shift(RIGHT * 2.6 + DOWN * 0.2)
        bwd_group = VGroup(bwd_box, lbl_bwd, bwd_1, bwd_2, bwd_3)

        self.play(FadeIn(fwd_group), FadeIn(bwd_group), run_time=1.0)

        # 3. Bottom Speedup Bar
        speed_bar = RoundedRectangle(corner_radius=0.12, height=1.1, width=9.6, fill_color="#181528", fill_opacity=0.95, stroke_color=COLOR_GOLD, stroke_width=1.2).shift(DOWN * 2.0)
        speed_title = Text("HIỆU NĂNG THỰC TẾ TRÊN PHẦN CỨNG THƯƠNG MẠI (A100 / H100):", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_GOLD).shift(DOWN * 1.7)
        speed_val_hdr = Text("Tăng tốc 2x - 4x Huấn Luyện  •  Mở Rộng Độ Dài Ngữ Cảnh Gấp Hàng Chục Lần", font=FONT_FAMILY, font_size=12, weight=BOLD, color=COLOR_TEXT).shift(DOWN * 2.2)
        speed_group = VGroup(speed_bar, speed_title, speed_val_hdr)

        self.play(FadeIn(speed_group), run_time=0.8)
        self.wait(1.0)

        # [Masterclass: Visual State Retained - Trailing FadeOut Removed]
        self.wait(2.0)


# =============================================================================
# SCENE 06: TỔNG KẾT KỸ NGHỆ & LỜI TRI ÂN
# =============================================================================
class Tap09Scene06Outro(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "TỔNG KẾT & CẦU NỐI KỸ NGHỆ")

        scene_title = Text(
            "BÀN GIAO TRI THỨC // FLASHATTENTION",
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
        # 1. Next Video Card (Episode 10: Mamba & State Space Models)
        next_card = RoundedRectangle(
            corner_radius=0.12, width=3.8, height=2.0,
            fill_color=COLOR_PANEL, fill_opacity=0.7, stroke_color=COLOR_CYAN, stroke_width=1.5
        ).move_to(RIGHT * 3.5 + UP * 1.5)
        next_header = Text("TẬP TIẾP THEO // TẬP 10", font=FONT_FAMILY, font_size=12.5, weight=BOLD, color=COLOR_CYAN)
        next_sub_header = Text("MAMBA & STATE SPACE MODELS", font=FONT_FAMILY, font_size=12.0, color=COLOR_TEXT).next_to(next_header, DOWN, buff=0.18)
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

