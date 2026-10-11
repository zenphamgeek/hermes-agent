#!/usr/bin/env python3
"""
Manim 2K QHD Master Animation Engine — Mixture of Experts (MoE)
Strict Neo-Noir Minimalist Theme | Pure 3Blue1Brown Geometric Flow
Zero Mascots | Safe Padding |x| <= 5.2, |y| <= 3.2
"""

from manim import *
import numpy as np
import math
from pathlib import Path

# Neo-Noir Theme Constants
COLOR_BG = "#0c0d12"
COLOR_CYAN = "#00e5ff"
COLOR_GOLD = "#ffb300"
COLOR_AMBER = "#ff9100"
COLOR_ROSE = "#ff2a6d"
COLOR_GREEN = "#00ffaa"
COLOR_TEXT = "#e2e8f0"
COLOR_MUTED = "#64748b"
COLOR_PANEL = "#141824"
COLOR_PANEL_STROKE = "#232d42"


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


# -----------------------------------------------------------------------------
# PHÂN CẢNH 1: COLD OPEN — NGHỊCH LÝ DENSE VS SPARSE MOE
# -----------------------------------------------------------------------------
class Tap11Scene01ColdOpen(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "MIXTURE OF EXPERTS")

        # 1. Main Title Card
        title_top = Text("NGHỊCH LÝ CỦA MÔ HÌNH DENSE", font="Noto Sans", font_size=24, weight=BOLD, color=COLOR_GOLD)
        title_sub = Text("KHI 100% NƠ-RON CÙNG BÙNG NỔ CHO MỖI DẤU PHẨY", font="Noto Sans", font_size=13, color=COLOR_TEXT)
        title_grp = VGroup(title_top, title_sub).arrange(DOWN, buff=0.15).to_edge(UP, buff=1.0)
        self.play(FadeIn(title_grp, shift=DOWN*0.3), run_time=0.9)

        # 2. Dense Monolith Architecture vs Sparse MoE
        dense_box = RoundedRectangle(corner_radius=0.15, height=3.0, width=4.4,
                                     fill_color=COLOR_PANEL, fill_opacity=0.85,
                                     stroke_color=COLOR_ROSE, stroke_width=1.5).shift(LEFT * 2.7 + DOWN * 0.4)
        dense_label = Text("DENSE MODEL (100% KÍCH HOẠT)", font="Noto Sans", font_size=12, weight=BOLD, color=COLOR_ROSE)
        dense_label.next_to(dense_box, UP, buff=0.15)
        
        # Grid of firing neurons (Dense)
        dense_dots = VGroup()
        for r in range(4):
            for c in range(6):
                dot = Dot(point=dense_box.get_center() + np.array([(c-2.5)*0.6, (r-1.5)*0.55, 0]),
                          radius=0.08, color=COLOR_ROSE)
                dense_dots.add(dot)
        
        dense_sub = Text("Lãng phí FLOPs cực đại", font="Noto Sans", font_size=12.0, color=COLOR_MUTED).next_to(dense_box, DOWN, buff=0.15)

        self.play(Create(dense_box), Write(dense_label), FadeIn(dense_dots), FadeIn(dense_sub), run_time=1.2)

        # 3. Sparse MoE Council
        sparse_box = RoundedRectangle(corner_radius=0.15, height=3.0, width=4.4,
                                      fill_color=COLOR_PANEL, fill_opacity=0.85,
                                      stroke_color=COLOR_CYAN, stroke_width=1.5).shift(RIGHT * 2.7 + DOWN * 0.4)
        sparse_label = Text("SPARSE MoE (TOP-2 EXPERTS)", font="Noto Sans", font_size=12, weight=BOLD, color=COLOR_CYAN)
        sparse_label.next_to(sparse_box, UP, buff=0.15)

        # 8 Experts blocks in sparse box
        sparse_experts = VGroup()
        for i in range(8):
            row = i // 4
            col = i % 4
            exp_color = COLOR_CYAN if i in [1, 5] else COLOR_MUTED
            op = 0.9 if i in [1, 5] else 0.25
            eb = RoundedRectangle(corner_radius=0.08, height=0.75, width=0.85,
                                  fill_color="#101828", fill_opacity=op, stroke_color=exp_color, stroke_width=1.2)
            eb.move_to(sparse_box.get_center() + np.array([(col-1.5)*0.95, (0.5-row)*1.0, 0]))
            lbl = Text(f"E{i+1}", font="Noto Sans", font_size=12.0, weight=BOLD, color=exp_color)
            lbl.move_to(eb.get_center())
            sparse_experts.add(VGroup(eb, lbl))

        sparse_sub = Text("Chỉ đánh thức chuyên gia cần thiết", font="Noto Sans", font_size=12.0, color=COLOR_GREEN).next_to(sparse_box, DOWN, buff=0.15)

        self.play(Create(sparse_box), Write(sparse_label), FadeIn(sparse_experts), FadeIn(sparse_sub), run_time=1.4)
        self.wait(1.0)

        # Pulse highlight the 2 active experts
        self.play(
            sparse_experts[1].animate.scale(1.1),
            sparse_experts[5].animate.scale(1.1),
            rate_func=there_and_back, run_time=1.2
        )
        self.wait(1.5)


# -----------------------------------------------------------------------------
# PHÂN CẢNH 2: KIẾN TRÚC — ROUTER & CÁC CHUYÊN GIA FFN
# -----------------------------------------------------------------------------
class Tap11Scene02Architecture(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "KIẾN TRÚC MoE")

        # Header
        hdr = Text("GIẢI PHẪU TẦNG MoE TRANSFORMER", font="Noto Sans", font_size=20, weight=BOLD, color=COLOR_TEXT)
        hdr.to_edge(UP, buff=1.0)
        self.play(FadeIn(hdr), run_time=0.8)

        # Input Token Vector x
        x_card = RoundedRectangle(corner_radius=0.1, height=0.55, width=3.8,
                                  fill_color=COLOR_PANEL, fill_opacity=0.9, stroke_color=COLOR_GOLD, stroke_width=1.5)
        x_card.shift(DOWN * 2.5)
        x_text = Text("Input Token Vector: x", font="Noto Sans", font_size=12, color=COLOR_GOLD).move_to(x_card.get_center())
        self.play(Create(x_card), Write(x_text), run_time=0.8)

        # Attention block above input
        attn_card = RoundedRectangle(corner_radius=0.1, height=0.6, width=4.8,
                                     fill_color=COLOR_PANEL, fill_opacity=0.9, stroke_color=COLOR_MUTED, stroke_width=1.2)
        attn_card.shift(DOWN * 1.4)
        attn_text = Text("Multi-Head Self-Attention (Giữ nguyên)", font="Noto Sans", font_size=12, color=COLOR_TEXT).move_to(attn_card.get_center())
        arr1 = Arrow(start=x_card.get_top(), end=attn_card.get_bottom(), buff=0.1, stroke_width=2.0, color=COLOR_GOLD)
        self.play(Create(arr1), Create(attn_card), Write(attn_text), run_time=0.9)

        # Gating Router in center
        router_card = RoundedRectangle(corner_radius=0.12, height=0.7, width=4.0,
                                       fill_color="#1e1832", fill_opacity=0.95, stroke_color=COLOR_ROSE, stroke_width=1.8)
        router_card.shift(UP * 0.1)
        router_text = Text("Gating Router W_g (Softmax Top-2)", font="Noto Sans", font_size=12, weight=BOLD, color=COLOR_ROSE)
        router_text.move_to(router_card.get_center())
        arr2 = Arrow(start=attn_card.get_top(), end=router_card.get_bottom(), buff=0.1, stroke_width=2.0, color=COLOR_CYAN)
        self.play(Create(arr2), Create(router_card), Write(router_text), run_time=1.0)

        # 4 Representative Experts above
        experts_grp = VGroup()
        arrows_exp = VGroup()
        for i in range(4):
            x_pos = (i - 1.5) * 2.5
            is_active = i in [1, 2]
            c = COLOR_CYAN if is_active else COLOR_MUTED
            op = 0.95 if is_active else 0.3
            ecard = RoundedRectangle(corner_radius=0.1, height=1.0, width=2.1,
                                     fill_color=COLOR_PANEL, fill_opacity=op, stroke_color=c, stroke_width=1.4)
            ecard.shift(UP * 1.8 + RIGHT * x_pos)
            elbl = Text(f"Expert {i+1} (FFN)", font="Noto Sans", font_size=12.0, weight=BOLD, color=c).next_to(ecard.get_top(), DOWN, buff=0.18)
            sublbl = Text("Code & Logic" if i==1 else ("Math & Reasoning" if i==2 else "General"), font="Noto Sans", font_size=12.0, color=COLOR_TEXT if is_active else COLOR_MUTED).next_to(elbl, DOWN, buff=0.1)
            experts_grp.add(VGroup(ecard, elbl, sublbl))

            arr = Arrow(start=router_card.get_top(), end=ecard.get_bottom(), buff=0.12,
                        stroke_width=2.2 if is_active else 1.0, color=c if is_active else COLOR_PANEL_STROKE)
            arrows_exp.add(arr)

        self.play(Create(arrows_exp), Create(experts_grp), run_time=1.5)
        self.wait(1.5)


# -----------------------------------------------------------------------------
# PHÂN CẢNH 3: TOÁN HỌC — NOISY TOP-K & AUXILIARY BALANCING LOSS
# -----------------------------------------------------------------------------
class Tap11Scene03Mathematics(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "TOÁN HỌC MoE")

        # Header
        hdr = Text("PHƯƠNG TRÌNH ĐỊNH TUYẾN & CÂN BẰNG TẢI", font="Noto Sans", font_size=19, weight=BOLD, color=COLOR_GOLD)
        hdr.to_edge(UP, buff=0.95)
        self.play(FadeIn(hdr), run_time=0.8)

        # 1. Formula 1: Router Output
        f1_card = RoundedRectangle(corner_radius=0.15, height=1.5, width=9.6,
                                   fill_color=COLOR_PANEL, fill_opacity=0.9, stroke_color=COLOR_CYAN, stroke_width=1.5)
        f1_card.shift(UP * 1.3)
        f1_title = Text("1. Noisy Top-k Gating Function (Noam Shazeer et al.)", font="Noto Sans", font_size=12, weight=BOLD, color=COLOR_CYAN)
        f1_title.next_to(f1_card.get_top(), DOWN, buff=0.14)
        f1_math = MathTex(
            r"H(x)_i = (x W_g)_i + \epsilon \cdot \text{Softplus}((x W_{\text{noise}})_i), \quad G(x) = \text{Softmax}(\text{KeepTopK}(H(x), k))",
            font_size=27, color=COLOR_TEXT
        ).next_to(f1_title, DOWN, buff=0.15)
        self.play(Create(f1_card), Write(f1_title), Write(f1_math), run_time=1.4)

        # 2. Formula 2: Output Weighted Sum
        f2_card = RoundedRectangle(corner_radius=0.15, height=1.3, width=9.6,
                                   fill_color=COLOR_PANEL, fill_opacity=0.9, stroke_color=COLOR_AMBER, stroke_width=1.5)
        f2_card.shift(DOWN * 0.3)
        f2_title = Text("2. Kết Hợp Đầu Ra Tuyến Tính Của Các Chuyên Gia", font="Noto Sans", font_size=12, weight=BOLD, color=COLOR_AMBER)
        f2_title.next_to(f2_card.get_top(), DOWN, buff=0.14)
        f2_math = MathTex(
            r"y = \sum_{i \in \text{TopK}} G(x)_i \cdot E_i(x)",
            font_size=32, color=COLOR_TEXT
        ).next_to(f2_title, DOWN, buff=0.14)
        self.play(Create(f2_card), Write(f2_title), Write(f2_math), run_time=1.2)

        # 3. Formula 3: Auxiliary Load Balancing Loss
        f3_card = RoundedRectangle(corner_radius=0.15, height=1.4, width=9.6,
                                   fill_color=COLOR_PANEL, fill_opacity=0.9, stroke_color=COLOR_ROSE, stroke_width=1.5)
        f3_card.shift(DOWN * 1.85)
        f3_title = Text("3. Hàm Mất Mát Cân Bằng Tải Triệt Tiêu Expert Collapse", font="Noto Sans", font_size=12, weight=BOLD, color=COLOR_ROSE)
        f3_title.next_to(f3_card.get_top(), DOWN, buff=0.14)
        f3_math = MathTex(
            r"\mathcal{L}_{\text{balance}} = \alpha \cdot N \sum_{i=1}^N f_i \cdot P_i, \quad f_i = \frac{\text{Tokens}_i}{T}, \quad P_i = \frac{1}{T} \sum_t G(x_t)_i",
            font_size=25, color=COLOR_TEXT
        ).next_to(f3_title, DOWN, buff=0.15)
        self.play(Create(f3_card), Write(f3_title), Write(f3_math), run_time=1.4)
        self.wait(1.5)


# -----------------------------------------------------------------------------
# PHÂN CẢNH 4: TRỰC GIÁC KỸ SƯ — BĂNG THÔNG VRAM & TOKEN DROPPING
# -----------------------------------------------------------------------------
class Tap11Scene04Telemetry(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "TELEMETRY VÀ PHẦN CỨNG")

        hdr = Text("NGHỊCH LÝ BĂNG THÔNG: ACTIVE VS STORED PARAMS", font="Noto Sans", font_size=19, weight=BOLD, color=COLOR_TEXT)
        hdr.to_edge(UP, buff=1.0)
        self.play(FadeIn(hdr), run_time=0.8)

        # Telemetry Card 1: Active vs Total
        c1 = RoundedRectangle(corner_radius=0.15, height=3.3, width=4.8,
                              fill_color=COLOR_PANEL, fill_opacity=0.9, stroke_color=COLOR_CYAN, stroke_width=1.5)
        c1.shift(LEFT * 2.7 + DOWN * 0.4)
        t1 = Text("MIXTRAL 8x7B METRICS", font="Noto Sans", font_size=13, weight=BOLD, color=COLOR_CYAN).next_to(c1.get_top(), DOWN, buff=0.2)
        
        row1 = Text("• Total Params: 46.7B (Store)", font="Noto Sans", font_size=12.0, color=COLOR_TEXT).next_to(t1, DOWN, buff=0.25, aligned_edge=LEFT)
        row2 = Text("• Active per Token: 12.9B (Compute)", font="Noto Sans", font_size=12.0, color=COLOR_GREEN).next_to(row1, DOWN, buff=0.18, aligned_edge=LEFT)
        row3 = Text("• VRAM yêu cầu: ~90 GB (FP16)", font="Noto Sans", font_size=12.0, color=COLOR_AMBER).next_to(row2, DOWN, buff=0.18, aligned_edge=LEFT)
        row4 = Text("• FLOPs tiết kiệm: ~73%", font="Noto Sans", font_size=12.0, weight=BOLD, color=COLOR_GOLD).next_to(row3, DOWN, buff=0.18, aligned_edge=LEFT)
        
        self.play(Create(c1), Write(t1), FadeIn(VGroup(row1, row2, row3, row4)), run_time=1.3)

        # Telemetry Card 2: Token Dropping & Capacity Factor
        c2 = RoundedRectangle(corner_radius=0.15, height=3.3, width=4.8,
                              fill_color=COLOR_PANEL, fill_opacity=0.9, stroke_color=COLOR_ROSE, stroke_width=1.5)
        c2.shift(RIGHT * 2.7 + DOWN * 0.4)
        t2 = Text("CAPACITY FACTOR & TOKEN DROP", font="Noto Sans", font_size=13, weight=BOLD, color=COLOR_ROSE).next_to(c2.get_top(), DOWN, buff=0.2)
        
        b1 = Text("• Expert Capacity Limit:", font="Noto Sans", font_size=12.0, color=COLOR_TEXT).next_to(t2, DOWN, buff=0.25, aligned_edge=LEFT)
        f_cap = MathTex(r"C = \text{Factor} \times \frac{T \cdot k}{N}", font_size=24, color=COLOR_CYAN).next_to(b1, DOWN, buff=0.12, aligned_edge=LEFT)
        b2 = Text("• Tràn hàng đợi: Drop Token", font="Noto Sans", font_size=12.0, color=COLOR_ROSE).next_to(f_cap, DOWN, buff=0.18, aligned_edge=LEFT)
        b3 = Text("• Token tràn đi qua Residual bypass", font="Noto Sans", font_size=12.0, color=COLOR_MUTED).next_to(b2, DOWN, buff=0.14, aligned_edge=LEFT)

        self.play(Create(c2), Write(t2), FadeIn(VGroup(b1, f_cap, b2, b3)), run_time=1.3)
        self.wait(1.5)


# -----------------------------------------------------------------------------
# PHÂN CẢNH 5: THỰC NGHIỆM LAB — BƯỚC TIẾN DEEPSEEK FINE-GRAINED MoE
# -----------------------------------------------------------------------------
class Tap11Scene05LabExperiment(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "THỰC NGHIỆM LAB")

        hdr = Text("TIẾN HÓA: MIXTRAL 8x7B VS DEEPSEEK-V3 FINE-GRAINED", font="Noto Sans", font_size=18, weight=BOLD, color=COLOR_GOLD)
        hdr.to_edge(UP, buff=1.0)
        self.play(FadeIn(hdr), run_time=0.8)

        # Left: Traditional Coarse MoE
        p_left = RoundedRectangle(corner_radius=0.15, height=3.4, width=4.6,
                                  fill_color=COLOR_PANEL, fill_opacity=0.85, stroke_color=COLOR_MUTED, stroke_width=1.2)
        p_left.shift(LEFT * 2.7 + DOWN * 0.4)
        t_left = Text("Coarse MoE (Mixtral)", font="Noto Sans", font_size=13, weight=BOLD, color=COLOR_TEXT).next_to(p_left.get_top(), DOWN, buff=0.18)
        
        # 8 coarse blocks
        coarse_blocks = VGroup()
        for i in range(8):
            r, c = i // 4, i % 4
            b = Rectangle(height=0.6, width=0.85, fill_color="#1e293b", fill_opacity=0.8, stroke_color=COLOR_CYAN, stroke_width=1.0)
            b.move_to(p_left.get_center() + np.array([(c-1.5)*0.95, (0.4-r)*0.9, 0]))
            coarse_blocks.add(b)
        sub_left = Text("8 Chuyên gia lớn // Chọn 2", font="Noto Sans", font_size=12.0, color=COLOR_MUTED).next_to(p_left.get_bottom(), UP, buff=0.2)

        self.play(Create(p_left), Write(t_left), FadeIn(coarse_blocks), Write(sub_left), run_time=1.2)

        # Right: DeepSeek-V3 Fine-Grained + Shared Experts
        p_right = RoundedRectangle(corner_radius=0.15, height=3.4, width=4.6,
                                   fill_color=COLOR_PANEL, fill_opacity=0.85, stroke_color=COLOR_GREEN, stroke_width=1.5)
        p_right.shift(RIGHT * 2.7 + DOWN * 0.4)
        t_right = Text("Fine-Grained MoE (DeepSeek-V3)", font="Noto Sans", font_size=13, weight=BOLD, color=COLOR_GREEN).next_to(p_right.get_top(), DOWN, buff=0.18)

        # Shared Expert Banner
        shared_exp = RoundedRectangle(corner_radius=0.08, height=0.55, width=3.8,
                                      fill_color="#064e3b", fill_opacity=0.9, stroke_color=COLOR_GREEN, stroke_width=1.5)
        shared_exp.next_to(t_right, DOWN, buff=0.15)
        shared_txt = Text("Shared Expert: 100% Cố định mọi token", font="Noto Sans", font_size=12.0, weight=BOLD, color=COLOR_GREEN).move_to(shared_exp.get_center())

        # Micro dots for 256 fine-grained
        micro_grid = VGroup()
        for r in range(4):
            for c in range(8):
                d = Dot(radius=0.05, color=COLOR_AMBER if (r*8+c) in [3, 7, 12, 19] else COLOR_MUTED)
                d.move_to(p_right.get_center() + np.array([(c-3.5)*0.45, -0.2 + (1.5-r)*0.35, 0]))
                micro_grid.add(d)
        
        sub_right = Text("256 Chuyên gia vi mô // Top-8", font="Noto Sans", font_size=12.0, color=COLOR_GOLD).next_to(p_right.get_bottom(), UP, buff=0.2)

        self.play(Create(p_right), Write(t_right), Create(shared_exp), Write(shared_txt), FadeIn(micro_grid), Write(sub_right), run_time=1.5)
        self.wait(1.5)


# -----------------------------------------------------------------------------
# PHÂN CẢNH 6: OUTRO — 5x5 MOSAIC & EPISODE 12 TEASER
# -----------------------------------------------------------------------------
class Tap11Scene06Outro(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "TỔNG KẾT & CẦU NỐI KỸ NGHỆ")

        scene_title = Text(
            "BÀN GIAO TRI THỨC // MIXTURE OF EXPERTS",
            font="Noto Sans", font_size=15.0, weight=BOLD, color=COLOR_GOLD
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
            font="Noto Sans", font_size=12.5, weight=BOLD, color=COLOR_GOLD
        ).next_to(mosaic_frame, UP, buff=0.18)

        left_grp = Group(mosaic_mobj, mosaic_frame, gallery_header)
        self.play(FadeIn(left_grp, shift=RIGHT * 0.3), run_time=1.2)

        # Right Side: YouTube End Screen Interactive Safe Zones
        # 1. Next Video Card (Episode 12: Quantization INT8 & FP8)
        next_card = RoundedRectangle(
            corner_radius=0.12, width=3.8, height=2.0,
            fill_color=COLOR_PANEL, fill_opacity=0.7, stroke_color=COLOR_CYAN, stroke_width=1.5
        ).move_to(RIGHT * 3.5 + UP * 1.5)
        next_header = Text("TẬP TIẾP THEO // TẬP 12", font="Noto Sans", font_size=12.5, weight=BOLD, color=COLOR_CYAN)
        next_sub_header = Text("LƯỢNG TỬ HÓA INT8 & FP8", font="Noto Sans", font_size=12.0, color=COLOR_TEXT).next_to(next_header, DOWN, buff=0.18)
        next_grp = VGroup(next_header, next_sub_header).move_to(next_card.get_center())

        # 2. Playlist Card
        pl_card = RoundedRectangle(
            corner_radius=0.12, width=3.8, height=1.3,
            fill_color=COLOR_PANEL, fill_opacity=0.7, stroke_color=COLOR_GOLD, stroke_width=1.5
        ).move_to(RIGHT * 3.5 + DOWN * 0.35)
        pl_header = Text("DANH SÁCH PHÁT SERIES 2", font="Noto Sans", font_size=12.5, weight=BOLD, color=COLOR_GOLD)
        pl_sub_header = Text("THE ANATOMY OF MODERN LLMS", font="Noto Sans", font_size=12.0, color=COLOR_MUTED).next_to(pl_header, DOWN, buff=0.15)
        pl_grp = VGroup(pl_header, pl_sub_header).move_to(pl_card.get_center())

        # 3. Subscribe Card
        sub_card = RoundedRectangle(
            corner_radius=0.12, width=3.8, height=1.1,
            fill_color=COLOR_PANEL, fill_opacity=0.7, stroke_color=COLOR_ROSE, stroke_width=1.5
        ).move_to(RIGHT * 3.5 + DOWN * 1.85)
        sub_header = Text("ĐĂNG KÝ KÊNH // ZENPHAM", font="Noto Sans", font_size=12.5, weight=BOLD, color=COLOR_ROSE)
        sub_sub_header = Text("AI CRAFTSMANSHIP & ENGINEERING", font="Noto Sans", font_size=12.0, color=COLOR_TEXT).next_to(sub_header, DOWN, buff=0.12)
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
