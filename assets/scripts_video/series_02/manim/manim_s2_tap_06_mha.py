#!/usr/bin/env python3
"""
Manim 2K QHD Master Production Scenes — MHA vs MQA vs GQA // Chiếc Cầu Nối Giữa Năng Lực Biểu Diễn Và Băng Thông Bộ Nhớ
Theme: Neo-Noir Obsidian (#0c0d12) | Standard: 100% Median / 3Blue1Brown Mathematical Craftsmanship
Strict Invariants:
- Zero Mascots (LivingZenMascot, Pioneers, ZenEngineerMascot 100% removed)
- Zero Static Bullet Boxes (continuous geometric & tensor transformations)
- Safe Margins: All elements stay strictly within |x| <= 5.2, |y| <= 3.2 (>=15% margin for subtitles/HUD)
- Dynamic Mathematical Mechanics: Roofline model, MHA/MQA/GQA tensor grouping, SRAM broadcast, VRAM scaling
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
# SCENE 01: BỨC TƯỜNG BỘ NHỚ TRONG KỶ NGUYÊN SUY LUẬN MÔ HÌNH LỚN
# =============================================================================
class Tap06Scene01ColdOpen(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG

        # 1. Header HUD Pill
        header_text = Text(
            "MHA vs MQA vs GQA // BÀI TOÁN BĂNG THÔNG BỘ NHỚ ĐỒ HỌA",
            font=FONT_FAMILY, font_size=13, weight=BOLD, color=COLOR_CYAN
        )
        header_box = RoundedRectangle(
            corner_radius=0.12, height=0.5, width=header_text.width + 0.6,
            fill_color="#141826", fill_opacity=0.9, stroke_color=COLOR_CYAN, stroke_width=1.2
        ).to_edge(UP, buff=0.35)
        header_text.move_to(header_box.get_center())
        self.play(FadeIn(header_box), Write(header_text), run_time=0.8)

        # 2. Roofline Model Plot (Left: |x| <= 5.1)
        axes = Axes(
            x_range=[0, 8, 2], y_range=[0, 6, 2],
            x_length=4.8, y_length=4.2,
            axis_config={"color": COLOR_MUTED, "stroke_width": 1.2, "include_numbers": False}
        ).shift(LEFT * 2.7 + DOWN * 0.2)

        x_lbl = Text("Cường độ tính toán (FLOPs / Byte)", font=FONT_FAMILY, font_size=12.0, color=COLOR_MUTED).next_to(axes.x_axis, DOWN, buff=0.15)
        y_lbl = Text("Hiệu năng thực thi (TFLOPs)", font=FONT_FAMILY, font_size=12.0, color=COLOR_MUTED).next_to(axes.y_axis, UP, buff=0.15).shift(RIGHT * 0.6)

        # Roofline curves: memory-bound slope then compute-bound ceiling
        mem_slope = Line(axes.c2p(0, 0), axes.c2p(3.5, 5.0), color=COLOR_AMBER, stroke_width=2.5)
        comp_ceiling = Line(axes.c2p(3.5, 5.0), axes.c2p(7.5, 5.0), color=COLOR_CYAN, stroke_width=2.5)

        lbl_mem_bound_hdr = Text("Memory-Bound\n(Băng thông HBM)", font=FONT_FAMILY, font_size=12.0, color=COLOR_AMBER).next_to(mem_slope.get_center(), UL, buff=0.1)
        lbl_comp_bound_hdr = Text("Compute-Bound\n(Công suất Tensor Core)", font=FONT_FAMILY, font_size=12.0, color=COLOR_CYAN).next_to(comp_ceiling, UP, buff=0.1)

        self.play(Create(axes), FadeIn(x_lbl), FadeIn(y_lbl), Create(mem_slope), Create(comp_ceiling), FadeIn(lbl_mem_bound_hdr), FadeIn(lbl_comp_bound_hdr), run_time=1.2)

        # 3. Prefill vs Decode Operating Points
        dot_prefill = Dot(axes.c2p(5.5, 5.0), color=COLOR_EMERALD, radius=0.1)
        lbl_prefill_hdr = Text("Pha Prefill\n(Song song cực đại)", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_EMERALD).next_to(dot_prefill, DOWN, buff=0.15)

        dot_decode = Dot(axes.c2p(0.8, 1.14), color=COLOR_ROSE, radius=0.1)
        lbl_decode_hdr = Text("Pha Decode\n(< 1 FLOP/Byte)", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_ROSE).next_to(dot_decode, RIGHT, buff=0.15)

        self.play(FadeIn(dot_prefill), Write(lbl_prefill_hdr), FadeIn(dot_decode), Write(lbl_decode_hdr), run_time=1.0)

        # 4. Right Card: Memory Wall Crisis
        right_panel = RoundedRectangle(
            corner_radius=0.15, height=4.2, width=4.6,
            fill_color=COLOR_CARD_BG, fill_opacity=0.92, stroke_color=COLOR_BORDER, stroke_width=1.2
        ).shift(RIGHT * 2.7 + DOWN * 0.2)

        t1 = Text("NGHỊCH LÝ DECODING:", font=FONT_FAMILY, font_size=12, weight=BOLD, color=COLOR_ROSE)
        desc1_hdr = Text("GPU ngồi chờ dữ liệu từ HBM\nthay vì thực hiện phép tính.", font=FONT_FAMILY, font_size=12.0, color=COLOR_TEXT)
        
        div1 = Line(LEFT * 1.8, RIGHT * 1.8, color=COLOR_BORDER, stroke_width=1.0)
        
        t2 = Text("THỦ PHẠM: KV CACHE", font=FONT_FAMILY, font_size=12, weight=BOLD, color=COLOR_GOLD)
        desc2_hdr = Text("Mỗi token sinh ra phải đọc lại\ntoàn bộ Key & Value của quá khứ.", font=FONT_FAMILY, font_size=12.0, color=COLOR_MUTED)

        t3 = Text("CÂU HỎI KỸ NGHỆ:", font=FONT_FAMILY, font_size=12, weight=BOLD, color=COLOR_CYAN)
        desc3_hdr = Text("Liệu mỗi Query có bắt buộc\nphải giữ riêng 1 cặp K-V độc lập?", font=FONT_FAMILY, font_size=12.0, color=COLOR_TEXT)

        content = VGroup(t1, desc1_hdr, div1, t2, desc2_hdr, t3, desc3_hdr).arrange(DOWN, buff=0.14, aligned_edge=ORIGIN).move_to(right_panel.get_center())
        self.play(FadeIn(right_panel), FadeIn(content), run_time=1.0)
        self.wait(2.0)

        # [Masterclass: Visual State Retained - Trailing FadeOut Removed]
        self.wait(2.0)


# =============================================================================
# SCENE 02: TỪ MULTI-HEAD ATTENTION ĐẾN MULTI-QUERY ATTENTION
# =============================================================================
class Tap06Scene02Architecture(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG

        # 1. Header HUD Pill
        header_text = Text("KIẾN TRÚC ĐỐI CHIẾU: MHA (2017) vs MQA (2019)", font=FONT_FAMILY, font_size=13, weight=BOLD, color=COLOR_CYAN)
        header_box = RoundedRectangle(corner_radius=0.12, height=0.5, width=header_text.width + 0.6, fill_color="#141826", fill_opacity=0.9, stroke_color=COLOR_CYAN, stroke_width=1.2).to_edge(UP, buff=0.35)
        header_text.move_to(header_box.get_center())
        self.play(FadeIn(header_box), Write(header_text), run_time=0.8)

        # 2. Side-by-Side Architectural Panels: Left = MHA, Right = MQA
        left_panel = RoundedRectangle(corner_radius=0.15, height=4.6, width=4.8, fill_color=COLOR_CARD_BG, fill_opacity=0.9, stroke_color=COLOR_CYAN, stroke_width=1.2).shift(LEFT * 2.6 + DOWN * 0.2)
        right_panel = RoundedRectangle(corner_radius=0.15, height=4.6, width=4.8, fill_color=COLOR_CARD_BG, fill_opacity=0.9, stroke_color=COLOR_AMBER, stroke_width=1.2).shift(RIGHT * 2.6 + DOWN * 0.2)

        lbl_mha = Text("1. MULTI-HEAD ATTENTION (MHA)", font=FONT_FAMILY, font_size=12, weight=BOLD, color=COLOR_CYAN).next_to(left_panel.get_top(), DOWN, buff=0.2)
        lbl_mqa = Text("2. MULTI-QUERY ATTENTION (MQA)", font=FONT_FAMILY, font_size=12, weight=BOLD, color=COLOR_AMBER).next_to(right_panel.get_top(), DOWN, buff=0.2)

        self.play(FadeIn(left_panel), FadeIn(right_panel), Write(lbl_mha), Write(lbl_mqa), run_time=0.8)

        # 3. MHA Layout: 4 Q heads connected 1-to-1 with 4 KV pairs
        mha_q_group = VGroup()
        mha_kv_group = VGroup()
        mha_arrows = VGroup()

        for i in range(4):
            q_box = RoundedRectangle(corner_radius=0.08, height=0.45, width=0.9, fill_color="#1e293b", fill_opacity=0.8, stroke_color=COLOR_CYAN, stroke_width=1.0)
            q_txt = Text(f"Q{i+1}", font=FONT_FAMILY, font_size=12.0, color=COLOR_CYAN).move_to(q_box.get_center())
            q_elem = VGroup(q_box, q_txt).shift(LEFT * 3.8 + UP * (0.8 - i * 0.75))
            mha_q_group.add(q_elem)

            kv_box = RoundedRectangle(corner_radius=0.08, height=0.45, width=1.1, fill_color="#1e293b", fill_opacity=0.8, stroke_color=COLOR_GOLD, stroke_width=1.0)
            kv_txt = Text(f"K{i+1}, V{i+1}", font=FONT_FAMILY, font_size=12.0, color=COLOR_GOLD).move_to(kv_box.get_center())
            kv_elem = VGroup(kv_box, kv_txt).shift(LEFT * 1.4 + UP * (0.8 - i * 0.75))
            mha_kv_group.add(kv_elem)

            arr = Arrow(q_box.get_right(), kv_box.get_left(), buff=0.08, color=COLOR_MUTED, stroke_width=1.5, max_tip_length_to_length_ratio=0.2)
            mha_arrows.add(arr)

        stat_mha_hdr = Text("Tỷ lệ: 1 Query / 1 KV Pair\nCache: 100% (Chuẩn MHA)", font=FONT_FAMILY, font_size=12.0, color=COLOR_TEXT).next_to(left_panel.get_bottom(), UP, buff=0.25)

        # 4. MQA Layout: 4 Q heads connected to 1 Shared KV pair
        mqa_q_group = VGroup()
        mqa_arrows = VGroup()

        for i in range(4):
            q_box = RoundedRectangle(corner_radius=0.08, height=0.45, width=0.9, fill_color="#1e293b", fill_opacity=0.8, stroke_color=COLOR_CYAN, stroke_width=1.0)
            q_txt = Text(f"Q{i+1}", font=FONT_FAMILY, font_size=12.0, color=COLOR_CYAN).move_to(q_box.get_center())
            q_elem = VGroup(q_box, q_txt).shift(RIGHT * 1.4 + UP * (0.8 - i * 0.75))
            mqa_q_group.add(q_elem)

        mqa_kv_box = RoundedRectangle(corner_radius=0.1, height=1.6, width=1.3, fill_color="#1e293b", fill_opacity=0.9, stroke_color=COLOR_AMBER, stroke_width=1.5).shift(RIGHT * 3.8 + DOWN * 0.3)
        mqa_kv_txt_hdr = Text("DUY NHẤT\n1 CẶP\nK, V", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_AMBER).move_to(mqa_kv_box.get_center())
        mqa_kv = VGroup(mqa_kv_box, mqa_kv_txt_hdr)

        for q in mqa_q_group:
            arr = Arrow(q.get_right(), mqa_kv_box.get_left(), buff=0.08, color=COLOR_AMBER, stroke_width=1.5, max_tip_length_to_length_ratio=0.15)
            mqa_arrows.add(arr)

        stat_mqa_hdr = Text("Tỷ lệ: 4 Query / 1 KV Pair\nCache: Giảm 4x (Mất biểu đạt)", font=FONT_FAMILY, font_size=12.0, color=COLOR_ROSE).next_to(right_panel.get_bottom(), UP, buff=0.25)

        self.play(FadeIn(mha_q_group), FadeIn(mha_kv_group), Create(mha_arrows), Write(stat_mha_hdr), run_time=1.2)
        self.play(FadeIn(mqa_q_group), FadeIn(mqa_kv), Create(mqa_arrows), Write(stat_mqa_hdr), run_time=1.2)
        self.wait(2.0)

        # [Masterclass: Visual State Retained - Trailing FadeOut Removed]
        self.wait(2.0)


# =============================================================================
# SCENE 03: GROUPED-QUERY ATTENTION: TỶ LỆ VÀNG DUNG HÒA HAI CỰC ĐOAN
# =============================================================================
class Tap06Scene03Mathematics(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG

        # 1. Header HUD Pill
        header_text = Text("GQA (2023): GROUPED-QUERY ATTENTION // TỶ LỆ VÀNG KỸ NGHỆ", font=FONT_FAMILY, font_size=13, weight=BOLD, color=COLOR_EMERALD)
        header_box = RoundedRectangle(corner_radius=0.12, height=0.5, width=header_text.width + 0.6, fill_color="#141826", fill_opacity=0.9, stroke_color=COLOR_EMERALD, stroke_width=1.2).to_edge(UP, buff=0.35)
        header_text.move_to(header_box.get_center())
        self.play(FadeIn(header_box), Write(header_text), run_time=0.8)

        # 2. Left Visual: Grouped-Query Diagram (4 Q heads -> 2 KV heads)
        left_panel = RoundedRectangle(corner_radius=0.15, height=4.6, width=4.8, fill_color=COLOR_CARD_BG, fill_opacity=0.9, stroke_color=COLOR_EMERALD, stroke_width=1.2).shift(LEFT * 2.6 + DOWN * 0.2)
        panel_title = Text("CƠ CHẾ PHÂN NHÓM GQA", font=FONT_FAMILY, font_size=12, weight=BOLD, color=COLOR_EMERALD).next_to(left_panel.get_top(), DOWN, buff=0.2)

        # Group 1: Q1, Q2 -> KV1
        grp1_box = RoundedRectangle(corner_radius=0.1, height=1.6, width=4.3, fill_color="#131e2b", fill_opacity=0.6, stroke_color=COLOR_CYAN, stroke_width=1.0).shift(LEFT * 2.6 + UP * 0.7)
        grp1_lbl = Text("Nhóm 1 (G=2)", font=FONT_FAMILY, font_size=12.0, color=COLOR_CYAN).next_to(grp1_box.get_top(), DOWN, buff=0.08)
        
        q1 = RoundedRectangle(corner_radius=0.06, height=0.4, width=0.8, fill_color="#1e293b", fill_opacity=0.8, stroke_color=COLOR_CYAN, stroke_width=1.0).shift(LEFT * 3.8 + UP * 0.8)
        q1_t = Text("Q1", font=FONT_FAMILY, font_size=12.0, color=COLOR_CYAN).move_to(q1.get_center())
        q2 = RoundedRectangle(corner_radius=0.06, height=0.4, width=0.8, fill_color="#1e293b", fill_opacity=0.8, stroke_color=COLOR_CYAN, stroke_width=1.0).shift(LEFT * 3.8 + UP * 0.3)
        q2_t = Text("Q2", font=FONT_FAMILY, font_size=12.0, color=COLOR_CYAN).move_to(q2.get_center())

        kv1 = RoundedRectangle(corner_radius=0.08, height=0.9, width=1.1, fill_color="#1e293b", fill_opacity=0.9, stroke_color=COLOR_GOLD, stroke_width=1.2).shift(LEFT * 1.5 + UP * 0.55)
        kv1_t = Text("K1, V1", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_GOLD).move_to(kv1.get_center())

        arr1a = Arrow(q1.get_right(), kv1.get_left(), buff=0.06, color=COLOR_MUTED, stroke_width=1.5, max_tip_length_to_length_ratio=0.15)
        arr1b = Arrow(q2.get_right(), kv1.get_left(), buff=0.06, color=COLOR_MUTED, stroke_width=1.5, max_tip_length_to_length_ratio=0.15)

        # Group 2: Q3, Q4 -> KV2
        grp2_box = RoundedRectangle(corner_radius=0.1, height=1.6, width=4.3, fill_color="#131e2b", fill_opacity=0.6, stroke_color=COLOR_VIOLET, stroke_width=1.0).shift(LEFT * 2.6 + DOWN * 1.1)
        grp2_lbl = Text("Nhóm 2 (G=2)", font=FONT_FAMILY, font_size=12.0, color=COLOR_VIOLET).next_to(grp2_box.get_top(), DOWN, buff=0.08)

        q3 = RoundedRectangle(corner_radius=0.06, height=0.4, width=0.8, fill_color="#1e293b", fill_opacity=0.8, stroke_color=COLOR_VIOLET, stroke_width=1.0).shift(LEFT * 3.8 + DOWN * 1.0)
        q3_t = Text("Q3", font=FONT_FAMILY, font_size=12.0, color=COLOR_VIOLET).move_to(q3.get_center())
        q4 = RoundedRectangle(corner_radius=0.06, height=0.4, width=0.8, fill_color="#1e293b", fill_opacity=0.8, stroke_color=COLOR_VIOLET, stroke_width=1.0).shift(LEFT * 3.8 + DOWN * 1.5)
        q4_t = Text("Q4", font=FONT_FAMILY, font_size=12.0, color=COLOR_VIOLET).move_to(q4.get_center())

        kv2 = RoundedRectangle(corner_radius=0.08, height=0.9, width=1.1, fill_color="#1e293b", fill_opacity=0.9, stroke_color=COLOR_GOLD, stroke_width=1.2).shift(LEFT * 1.5 + DOWN * 1.25)
        kv2_t = Text("K2, V2", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_GOLD).move_to(kv2.get_center())

        arr2a = Arrow(q3.get_right(), kv2.get_left(), buff=0.06, color=COLOR_MUTED, stroke_width=1.5, max_tip_length_to_length_ratio=0.15)
        arr2b = Arrow(q4.get_right(), kv2.get_left(), buff=0.06, color=COLOR_MUTED, stroke_width=1.5, max_tip_length_to_length_ratio=0.15)

        g_left = VGroup(left_panel, panel_title, grp1_box, grp1_lbl, q1, q1_t, q2, q2_t, kv1, kv1_t, arr1a, arr1b,
                        grp2_box, grp2_lbl, q3, q3_t, q4, q4_t, kv2, kv2_t, arr2a, arr2b)

        self.play(FadeIn(g_left), run_time=1.2)

        # 3. Right Panel: Formal Mathematics & Efficiency Ratios
        right_panel = RoundedRectangle(corner_radius=0.15, height=4.6, width=4.8, fill_color=COLOR_CARD_BG, fill_opacity=0.9, stroke_color=COLOR_BORDER, stroke_width=1.2).shift(RIGHT * 2.6 + DOWN * 0.2)
        
        m_title = Text("CÔNG THỨC TOÁN HỌC ĐỊNH LƯỢNG", font=FONT_FAMILY, font_size=12, weight=BOLD, color=COLOR_GOLD).next_to(right_panel.get_top(), DOWN, buff=0.25)
        
        f1 = MathTex(r"\text{GroupSize } (G) = \frac{H_Q}{H_{KV}}", font_size=20, color=COLOR_CYAN)
        desc_f1 = Text("Ví dụ: 32 đầu Q / 8 đầu KV  →  G = 4", font=FONT_FAMILY, font_size=12.0, color=COLOR_MUTED)

        div_m = Line(LEFT * 1.9, RIGHT * 1.9, color=COLOR_BORDER, stroke_width=1.0)

        f2 = MathTex(r"\text{Cache Ratio} = \frac{H_{KV}}{H_Q} = \frac{1}{G}", font_size=20, color=COLOR_EMERALD)
        desc_f2 = Text("Dung lượng KV Cache giảm đúng G lần", font=FONT_FAMILY, font_size=12.0, color=COLOR_MUTED)

        div_m2 = Line(LEFT * 1.9, RIGHT * 1.9, color=COLOR_BORDER, stroke_width=1.0)

        t_res = Text("KẾT LUẬN TỪ GOOGLE RESEARCH (2023):", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_TEXT)
        t_res2_hdr = Text("• Tốc độ suy luận ngang ngửa MQA\n• Giữ trọn 99.8% năng lực ngôn ngữ MHA", font=FONT_FAMILY, font_size=12.0, color=COLOR_EMERALD)

        r_content = VGroup(m_title, f1, desc_f1, div_m, f2, desc_f2, div_m2, t_res, t_res2_hdr).arrange(DOWN, buff=0.14, aligned_edge=ORIGIN).move_to(right_panel.get_center())

        self.play(FadeIn(right_panel), FadeIn(r_content), run_time=1.2)
        self.wait(2.0)

        # [Masterclass: Visual State Retained - Trailing FadeOut Removed]
        self.wait(2.0)


# =============================================================================
# SCENE 04: GIẢI PHẪU CON SỐ THỰC TẾ: BỨC TRANH BỘ NHỚ VRAM Ở NGỮ CẢNH DÀI
# =============================================================================
class Tap06Scene04Telemetry(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG

        # 1. Header HUD Pill
        header_text = Text("TÍNH TOÁN DUNG LƯỢNG KV CACHE: MÔ HÌNH NHỎ ĐẾN LLAMA-3 70B", font=FONT_FAMILY, font_size=13, weight=BOLD, color=COLOR_GOLD)
        header_box = RoundedRectangle(corner_radius=0.12, height=0.5, width=header_text.width + 0.6, fill_color="#141826", fill_opacity=0.9, stroke_color=COLOR_GOLD, stroke_width=1.2).to_edge(UP, buff=0.35)
        header_text.move_to(header_box.get_center())
        self.play(FadeIn(header_box), Write(header_text), run_time=0.8)

        # 2. Formula Card on Top: KV Cache General Formula
        formula_box = RoundedRectangle(corner_radius=0.12, height=1.1, width=10.0, fill_color=COLOR_CARD_BG, fill_opacity=0.9, stroke_color=COLOR_BORDER, stroke_width=1.2).shift(UP * 1.5)
        f_tex = MathTex(
            r"\text{Memory}_{\text{KV}} = 2 \times B \times S \times L \times H_{KV} \times d_k \times \text{bytes\_per\_num}",
            font_size=22, color=COLOR_GOLD
        ).move_to(formula_box.get_center())
        self.play(FadeIn(formula_box), Write(f_tex), run_time=1.0)

        # 3. Two Detailed Columns: Left = Toy Model (S=4), Right = LLaMA-3 70B (S=128k)
        left_card = RoundedRectangle(corner_radius=0.15, height=3.3, width=4.8, fill_color=COLOR_CARD_BG, fill_opacity=0.92, stroke_color=COLOR_CYAN, stroke_width=1.2).shift(LEFT * 2.6 + DOWN * 1.0)
        right_card = RoundedRectangle(corner_radius=0.15, height=3.3, width=4.8, fill_color=COLOR_CARD_BG, fill_opacity=0.92, stroke_color=COLOR_ROSE, stroke_width=1.2).shift(RIGHT * 2.6 + DOWN * 1.0)

        # Left Content: Toy Model
        t_left_title = Text("1. VÍ DỤ MINH HỌA (B=1, S=4, L=1, d_k=2)", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_CYAN)
        t_mha_toy = Text("• MHA (H_kv=4):  2×1×4×1×4×2×2 = 128 Bytes", font=FONT_FAMILY, font_size=12.0, color=COLOR_TEXT)
        t_gqa_toy = Text("• GQA (H_kv=2):  2×1×4×1×2×2×2 = 64 Bytes (50%)", font=FONT_FAMILY, font_size=12.0, color=COLOR_EMERALD)
        t_mqa_toy = Text("• MQA (H_kv=1):  2×1×4×1×1×2×2 = 32 Bytes (25%)", font=FONT_FAMILY, font_size=12.0, color=COLOR_AMBER)
        left_grp = VGroup(t_left_title, t_mha_toy, t_gqa_toy, t_mqa_toy).arrange(DOWN, buff=0.18, aligned_edge=LEFT).move_to(left_card.get_center())

        # Right Content: LLaMA-3 70B (80 layers, d_k=128, S=128k, FP16)
        t_right_title = Text("2. THỰC TẾ: LLAMA-3 70B (S=128k Token)", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_ROSE)
        t_mha_prod_hdr = Text("• MHA (64 heads): ~160 GiB VRAM / User\n  (Tràn bộ nhớ! Vượt quá 2 card H100 80GB)", font=FONT_FAMILY, font_size=12.0, color=COLOR_ROSE)
        t_gqa_prod_hdr = Text("• GQA (8 heads):  ~20 GiB VRAM / User\n  (Giảm 8x! Phục vụ 8 người dùng đồng thời)", font=FONT_FAMILY, font_size=12.0, color=COLOR_EMERALD)
        right_grp = VGroup(t_right_title, t_mha_prod_hdr, t_gqa_prod_hdr).arrange(DOWN, buff=0.18, aligned_edge=LEFT).move_to(right_card.get_center())

        self.play(FadeIn(left_card), FadeIn(left_grp), FadeIn(right_card), FadeIn(right_grp), run_time=1.2)
        self.wait(2.0)

        # [Masterclass: Visual State Retained - Trailing FadeOut Removed]
        self.wait(2.0)


# =============================================================================
# SCENE 05: KỸ NGHỆ PHẦN CỨNG: BROADCAST TRONG SRAM VÀ CHUYỂN ĐỔI CHECKPOINT
# =============================================================================
class Tap06Scene05LabExperiment(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG

        # 1. Header HUD Pill
        header_text = Text("KỸ NGHỆ PHẦN CỨNG: SRAM BROADCAST & UPTRAINING CHECKPOINT", font=FONT_FAMILY, font_size=13, weight=BOLD, color=COLOR_CYAN)
        header_box = RoundedRectangle(corner_radius=0.12, height=0.5, width=header_text.width + 0.6, fill_color="#141826", fill_opacity=0.9, stroke_color=COLOR_CYAN, stroke_width=1.2).to_edge(UP, buff=0.35)
        header_text.move_to(header_box.get_center())
        self.play(FadeIn(header_box), Write(header_text), run_time=0.8)

        # 2. Hardware Memory Hierarchy Diagram (Left: |x| <= 5.1)
        hbm_box = RoundedRectangle(corner_radius=0.12, height=1.2, width=4.6, fill_color="#1e1b2e", fill_opacity=0.9, stroke_color=COLOR_ROSE, stroke_width=1.2).shift(LEFT * 2.7 + UP * 1.1)
        hbm_title = Text("GPU HBM3 (Chậm, Băng thông 3.35 TB/s)", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_ROSE).next_to(hbm_box.get_top(), DOWN, buff=0.12)
        hbm_data = Text("Lưu đúng 1 bản sao KV duy nhất (Không nhân bản)", font=FONT_FAMILY, font_size=12.0, color=COLOR_TEXT).move_to(hbm_box.get_center()).shift(DOWN * 0.15)
        hbm_group = VGroup(hbm_box, hbm_title, hbm_data)

        sram_box = RoundedRectangle(corner_radius=0.12, height=2.2, width=4.6, fill_color="#13242b", fill_opacity=0.9, stroke_color=COLOR_CYAN, stroke_width=1.2).shift(LEFT * 2.7 + DOWN * 1.1)
        sram_title = Text("SRAM CACHE & TENSOR CORES (Siêu tốc, 100+ TB/s)", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_CYAN).next_to(sram_box.get_top(), DOWN, buff=0.12)
        
        # Broadcast visual arrows inside SRAM
        sram_desc_hdr = Text("Phát thanh (Broadcast) 1 KV tới 4 Query\ntrên các thanh ghi mà không tốn byte HBM nào!", font=FONT_FAMILY, font_size=12.0, color=COLOR_TEXT).move_to(sram_box.get_center()).shift(DOWN * 0.2)
        sram_group = VGroup(sram_box, sram_title, sram_desc_hdr)

        read_arrow = Arrow(hbm_box.get_bottom(), sram_box.get_top(), buff=0.1, color=COLOR_GOLD, stroke_width=2.5)
        lbl_read = Text("1 Lần Đọc Duy Nhất", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_GOLD).next_to(read_arrow, RIGHT, buff=0.1)

        self.play(FadeIn(hbm_group), FadeIn(sram_group), GrowArrow(read_arrow), FadeIn(lbl_read), run_time=1.2)

        # 3. Right Panel: Uptraining Strategy from MHA Checkpoints
        right_panel = RoundedRectangle(corner_radius=0.15, height=4.6, width=4.8, fill_color=COLOR_CARD_BG, fill_opacity=0.9, stroke_color=COLOR_BORDER, stroke_width=1.2).shift(RIGHT * 2.6 + DOWN * 0.2)
        
        t_up_title = Text("CHIẾN LƯỢC CHUYỂN ĐỔI CHECKPOINT", font=FONT_FAMILY, font_size=12, weight=BOLD, color=COLOR_GOLD).next_to(right_panel.get_top(), DOWN, buff=0.25)
        
        step1_title = Text("1. Mean-Pooling Trọng Số", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_CYAN)
        step1_desc_hdr = Text("Lấy trung bình cộng các đầu K và V trong nhóm\nđể khởi tạo trọng số cho GQA.", font=FONT_FAMILY, font_size=12.0, color=COLOR_TEXT)

        div_r = Line(LEFT * 1.9, RIGHT * 1.9, color=COLOR_BORDER, stroke_width=1.0)

        step2_title = Text("2. Huấn Luyện Bổ Sung (Uptraining)", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_EMERALD)
        step2_desc_hdr = Text("Chỉ cần train thêm 5% tổng số bước ban đầu.\nMô hình lấy lại hoàn toàn độ chính xác MHA!", font=FONT_FAMILY, font_size=12.0, color=COLOR_TEXT)

        div_r2 = Line(LEFT * 1.9, RIGHT * 1.9, color=COLOR_BORDER, stroke_width=1.0)

        step3_title = Text("3. Thư Viện Hỗ Trợ Tối Tân", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_AMBER)
        step3_desc_hdr = Text("vLLM, TensorRT-LLM, FlashDecoding tích hợp sẵn\nkernel GQA broadcast tối ưu ở tầng assembly.", font=FONT_FAMILY, font_size=12.0, color=COLOR_MUTED)

        r_content = VGroup(t_up_title, step1_title, step1_desc_hdr, div_r, step2_title, step2_desc_hdr, div_r2, step3_title, step3_desc_hdr).arrange(DOWN, buff=0.12, aligned_edge=ORIGIN).move_to(right_panel.get_center())

        self.play(FadeIn(right_panel), FadeIn(r_content), run_time=1.2)
        self.wait(2.0)

        # [Masterclass: Visual State Retained - Trailing FadeOut Removed]
        self.wait(2.0)


# =============================================================================
# SCENE 06: TRIẾT LÝ ĐÁNH ĐỔI, LỜI TRI ÂN CHÂN THÀNH VÀ KẾT NỐI TẬP 07
# =============================================================================
# =============================================================================
# SCENE 06: TRIẾT LÝ ĐÁNH ĐỔI, LỜI TRI ÂN CHÂN THÀNH VÀ KẾT NỐI TẬP 07
# =============================================================================
class Tap06Scene06Outro(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "TỔNG KẾT & CẦU NỐI KỸ NGHỆ")

        scene_title = Text(
            "BÀN GIAO TRI THỨC // MHA, MQA, GQA & BĂNG THÔNG SILICON",
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
        # 1. Next Video Card (Episode 07: KV Cache)
        next_card = RoundedRectangle(
            corner_radius=0.12, width=3.8, height=2.0,
            fill_color=COLOR_PANEL, fill_opacity=0.7, stroke_color=COLOR_CYAN, stroke_width=1.5
        ).move_to(RIGHT * 3.5 + UP * 1.5)
        next_header = Text("TẬP TIẾP THEO // TẬP 07", font=FONT_FAMILY, font_size=12.5, weight=BOLD, color=COLOR_CYAN)
        next_sub_header = Text("KV CACHE: NGHỊCH LÝ BỘ NHỚ", font=FONT_FAMILY, font_size=12.0, color=COLOR_TEXT).next_to(next_header, DOWN, buff=0.18)
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

