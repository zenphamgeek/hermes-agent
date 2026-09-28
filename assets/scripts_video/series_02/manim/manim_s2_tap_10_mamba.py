#!/usr/bin/env python3
"""
Manim 2K QHD Master Production Scenes — Linear Attention & Mamba (State Space Models - SSM)
Theme: Neo-Noir Obsidian (#0c0d12) | Standard: 100% Median / 3Blue1Brown Mathematical Craftsmanship
Strict Invariants:
- Zero Mascots (LivingZenMascot, Pioneers, ZenEngineerMascot 100% removed)
- Zero Static Bullet Boxes (continuous geometric & tensor transformations)
- Safe Margins: All elements stay strictly within |x| <= 5.2, |y| <= 3.2 (>=15% margin for subtitles/HUD)
- Dynamic Mathematical Mechanics: Continuous to Discrete SSM (ZOH), Selective Scan Gating, Parallel Associative Scan
"""

import sys
from pathlib import Path

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


def add_zenpham_brand(scene: Scene, ep_title: str):
    """Clean Neo-Noir HUD Header strictly within safe screen padding."""
    watermark = Text("ZENPHAM // TÔI LÀM VIỆC", font="Noto Sans", font_size=13, weight=BOLD, color=COLOR_MUTED)
    watermark.to_corner(UR, buff=0.45)
    
    ep_badge = Text(ep_title, font="Noto Sans", font_size=12, weight=BOLD, color=COLOR_CYAN)
    badge_bg = RoundedRectangle(corner_radius=0.1, height=0.36, width=ep_badge.width + 0.35,
                                fill_color=COLOR_PANEL, fill_opacity=0.9, stroke_color=COLOR_CYAN, stroke_width=1.0)
    badge_bg.to_corner(UL, buff=0.45)
    ep_badge.move_to(badge_bg.get_center())
    
    scene.add(watermark, badge_bg, ep_badge)


# =============================================================================
# SCENE 01: BỨC TƯỜNG BẬC HAI CỦA TRANSFORMER VÀ GIẤC MƠ TUYẾN TÍNH
# =============================================================================
class Tap10Scene01ColdOpen(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG

        # 1. Header HUD Pill
        header_text = Text(
            "LINEAR ATTENTION & MAMBA // KHI ĐỘ PHỨC TẠP TUYẾN TÍNH O(N) LÊN NGÔI",
            font=FONT_FAMILY, font_size=13, weight=BOLD, color=COLOR_CYAN
        )
        header_box = RoundedRectangle(
            corner_radius=0.12, height=0.5, width=header_text.width + 0.6,
            fill_color="#141826", fill_opacity=0.9, stroke_color=COLOR_CYAN, stroke_width=1.2
        ).to_edge(UP, buff=0.35)
        header_text.move_to(header_box.get_center())
        self.play(FadeIn(header_box), Write(header_text), run_time=0.8)

        # 2. Scaling Graph: O(N^2) vs O(N)
        axes = Axes(
            x_range=[0, 10, 2],
            y_range=[0, 10, 2],
            x_length=8.4,
            y_length=4.2,
            axis_config={"color": COLOR_BORDER, "stroke_width": 1.5},
            tips=False
        ).shift(DOWN * 0.3)

        # Curves
        quad_curve = axes.plot(lambda x: 0.1 * (x ** 2), x_range=[0, 9.8], color=COLOR_ROSE, stroke_width=3.5)
        lin_curve = axes.plot(lambda x: 0.5 * x, x_range=[0, 9.8], color=COLOR_EMERALD, stroke_width=3.5)

        lbl_quad = Text("Transformer: O(N^2) VRAM & FLOPs", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_ROSE).next_to(axes.c2p(7.5, 7.5), UP)
        lbl_lin = Text("Mamba / SSM: O(N) Tuyến Tính", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_EMERALD).next_to(axes.c2p(7.5, 3.8), DOWN)

        lbl_x = Text("Độ dài chuỗi ngữ cảnh N (4K -> 128K -> 1M)", font=FONT_FAMILY, font_size=12.0, color=COLOR_MUTED).next_to(axes, DOWN, buff=0.15)

        self.play(Create(axes), Write(lbl_x), run_time=0.8)
        self.play(Create(quad_curve), FadeIn(lbl_quad), run_time=1.2)
        self.play(Create(lin_curve), FadeIn(lbl_lin), run_time=1.0)

        # 3. Bottom Callout Pill
        callout = RoundedRectangle(corner_radius=0.1, height=0.6, width=8.8, fill_color="#181424", fill_opacity=0.95, stroke_color=COLOR_GOLD, stroke_width=1.2).shift(DOWN * 2.6)
        callout_hdr = Text("ĐẬP TAN BỨC TƯỜNG BỘ NHỚ KHI XỬ LÝ VĂN BẢN SIÊU DÀI", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_GOLD).move_to(callout)
        self.play(FadeIn(callout), Write(callout_hdr), run_time=0.6)
        self.wait(2.0)


# =============================================================================
# SCENE 02: CỘI NGUỒN LÝ THUYẾT ĐIỀU KHIỂN & KHÔNG GIAN TRẠNG THÁI
# =============================================================================
class Tap10Scene02Architecture(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG

        # 1. Header HUD Pill
        header_text = Text(
            "CỘI NGUỒN TOÁN HỌC // TỪ PHƯƠNG TRÌNH VI PHÂN ĐẾN TRUY HỒI RỜI RẠC",
            font=FONT_FAMILY, font_size=13, weight=BOLD, color=COLOR_AMBER
        )
        header_box = RoundedRectangle(
            corner_radius=0.12, height=0.5, width=header_text.width + 0.6,
            fill_color="#141826", fill_opacity=0.9, stroke_color=COLOR_AMBER, stroke_width=1.2
        ).to_edge(UP, buff=0.35)
        header_text.move_to(header_box.get_center())
        self.play(FadeIn(header_box), Write(header_text), run_time=0.6)

        # 2. Continuous State Space Card (Left)
        cont_card = RoundedRectangle(corner_radius=0.15, height=4.2, width=4.8, fill_color=COLOR_CARD_BG, fill_opacity=0.9, stroke_color=COLOR_CYAN, stroke_width=1.2).shift(LEFT * 2.6 + DOWN * 0.2)
        lbl_cont = Text("HỆ LIÊN TỤC (VẬT LÝ & ĐIỀU KHIỂN)", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_CYAN).next_to(cont_card.get_top(), DOWN, buff=0.25)

        eq_diff = MathTex(
            r"h'(t) = A h(t) + B x(t)",
            font_size=23, color=COLOR_TEXT
        ).shift(LEFT * 2.6 + UP * 0.7)
        eq_diff[0][0:5].set_color(COLOR_AMBER)

        eq_out = MathTex(
            r"y(t) = C h(t)",
            font_size=23, color=COLOR_TEXT
        ).shift(LEFT * 2.6 + DOWN * 0.1)
        eq_out[0][0:4].set_color(COLOR_EMERALD)

        note_cont_header = Text("Vector trạng thái h(t) chứa trọn vẹn lịch sử tín hiệu", font=FONT_FAMILY, font_size=12.0, color=COLOR_MUTED).shift(LEFT * 2.6 + DOWN * 1.1)

        cont_group = VGroup(cont_card, lbl_cont, eq_diff, eq_out, note_cont_header)

        # 3. Discrete Recurrence Card (Right)
        disc_card = RoundedRectangle(corner_radius=0.15, height=4.2, width=4.8, fill_color=COLOR_CARD_BG, fill_opacity=0.9, stroke_color=COLOR_GOLD, stroke_width=1.2).shift(RIGHT * 2.6 + DOWN * 0.2)
        lbl_disc = Text("HỆ RỜI RẠC (ZERO-ORDER HOLD)", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_GOLD).next_to(disc_card.get_top(), DOWN, buff=0.25)

        eq_zoh = MathTex(
            r"\bar{A} = \exp(\Delta A), \quad \bar{B} = (\Delta A)^{-1}(\bar{A} - I)\Delta B",
            font_size=19, color=COLOR_GOLD
        ).shift(RIGHT * 2.6 + UP * 0.8)

        eq_rec = MathTex(
            r"h_t = \bar{A} h_{t-1} + \bar{B} x_t",
            font_size=24, color=COLOR_CYAN
        ).shift(RIGHT * 2.6 + UP * 0.0)

        eq_rec_out = MathTex(
            r"y_t = C h_t",
            font_size=24, color=COLOR_EMERALD
        ).shift(RIGHT * 2.6 + DOWN * 0.7)

        note_disc_header = Text("Truy hồi RNN: Chỉ cần nhớ h_t hiện tại, không lưu lịch sử!", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_TEXT).shift(RIGHT * 2.6 + DOWN * 1.4)

        disc_group = VGroup(disc_card, lbl_disc, eq_zoh, eq_rec, eq_rec_out, note_disc_header)

        self.play(FadeIn(cont_group), FadeIn(disc_group), run_time=1.2)
        self.wait(2.0)


# =============================================================================
# SCENE 03: ĐỘT PHÁ LỚN: CƠ CHẾ SELECTIVE SCAN
# =============================================================================
class Tap10Scene03Mathematics(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG

        # 1. Header HUD Pill
        header_text = Text(
            "ĐỘT PHÁ CỐT LÕI // CƠ CHẾ QUÉT CHỌN LỌC SELECTIVE SCAN CỦA MAMBA",
            font=FONT_FAMILY, font_size=13, weight=BOLD, color=COLOR_GOLD
        )
        header_box = RoundedRectangle(
            corner_radius=0.12, height=0.5, width=header_text.width + 0.6,
            fill_color="#141826", fill_opacity=0.9, stroke_color=COLOR_GOLD, stroke_width=1.2
        ).to_edge(UP, buff=0.35)
        header_text.move_to(header_box.get_center())
        self.play(FadeIn(header_box), Write(header_text), run_time=0.6)

        # 2. Formula Card: Input-Dependent Selection
        math_card = RoundedRectangle(corner_radius=0.15, height=2.4, width=9.6, fill_color=COLOR_CARD_BG, fill_opacity=0.95, stroke_color=COLOR_GOLD, stroke_width=1.5).shift(UP * 1.0)
        lbl_math = Text("BIẾN ĐỔI THAM SỐ PHỤ THUỘC TRỰC TIẾP VÀO INPUT x_t", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_GOLD).next_to(math_card.get_top(), DOWN, buff=0.2)

        eq_params = MathTex(
            r"\Delta_t = \text{softplus}(W_\Delta x_t), \quad B_t = W_B x_t, \quad C_t = W_C x_t",
            font_size=23, color=COLOR_CYAN
        ).shift(UP * 1.0)

        eq_dyn = MathTex(
            r"\bar{A}_t = \exp(\Delta_t A), \quad \bar{B}_t \approx \Delta_t B_t",
            font_size=23, color=COLOR_AMBER
        ).shift(UP * 0.3)

        formula_group = VGroup(math_card, lbl_math, eq_params, eq_dyn)
        self.play(FadeIn(formula_group), run_time=1.0)

        # 3. Dynamic Filtering Demo (Left vs Right)
        flt_box = RoundedRectangle(corner_radius=0.15, height=2.3, width=9.6, fill_color="#0e1320", fill_opacity=0.95, stroke_color=COLOR_BORDER, stroke_width=1.2).shift(DOWN * 1.8)
        lbl_flt = Text("TRỰC QUAN HÓA CƠ CHẾ NÉN VÀ XÓA KÝ ỨC CÓ CHỌN LỌC", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_TEXT).next_to(flt_box.get_top(), DOWN, buff=0.2)

        case_1_header = Text("• Từ dừng / Dấu câu vô nghĩa: Delta -> 0 => Giữ nguyên trạng thái cũ", font=FONT_FAMILY, font_size=12.0, color=COLOR_ROSE).shift(DOWN * 1.5 + LEFT * 0.2)
        case_2_header = Text("• Khái niệm / Từ khóa trọng tâm: Delta mở lớn => Hấp thụ sâu thông tin mới", font=FONT_FAMILY, font_size=12.0, color=COLOR_EMERALD).shift(DOWN * 2.0 + LEFT * 0.2)

        flt_group = VGroup(flt_box, lbl_flt, case_1_header, case_2_header)
        self.play(FadeIn(flt_group), run_time=1.0)
        self.wait(2.0)


# =============================================================================
# SCENE 04: KỸ NGHỆ TẦNG SILICON: HARDWARE-AWARE PARALLEL SCAN
# =============================================================================
class Tap10Scene04Telemetry(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG

        # 1. Header HUD Pill
        header_text = Text(
            "KỸ NGHỆ TẦNG SILICON // HARDWARE-AWARE PARALLEL ASSOCIATIVE SCAN",
            font=FONT_FAMILY, font_size=13, weight=BOLD, color=COLOR_CYAN
        )
        header_box = RoundedRectangle(
            corner_radius=0.12, height=0.5, width=header_text.width + 0.6,
            fill_color="#141826", fill_opacity=0.9, stroke_color=COLOR_CYAN, stroke_width=1.2
        ).to_edge(UP, buff=0.35)
        header_text.move_to(header_box.get_center())
        self.play(FadeIn(header_box), Write(header_text), run_time=0.6)

        # 2. Binary Tree Parallel Prefix Sum Card
        tree_card = RoundedRectangle(corner_radius=0.15, height=4.2, width=4.8, fill_color=COLOR_CARD_BG, fill_opacity=0.9, stroke_color=COLOR_CYAN, stroke_width=1.2).shift(LEFT * 2.6 + DOWN * 0.2)
        lbl_tree = Text("CÂY TIỀN TỐ SONG SONG (PREFIX SUM)", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_CYAN).next_to(tree_card.get_top(), DOWN, buff=0.25)

        t_nodes = VGroup()
        for lvl in range(3):
            n_items = 4 // (2 ** lvl)
            for j in range(n_items):
                cx = -3.8 + (j + 0.5) * (2.4 / n_items) * 2
                cy = 0.8 - lvl * 0.9
                node = Circle(radius=0.22, fill_color="#182c40", fill_opacity=0.9, stroke_color=COLOR_CYAN, stroke_width=1.2).move_to([cx, cy, 0])
                t_nodes.add(node)

        tree_note_header = Text("Độ sâu O(log N): Tính toán song song hàng nghìn token cùng lúc", font=FONT_FAMILY, font_size=12.0, color=COLOR_TEXT).shift(LEFT * 2.6 + DOWN * 1.4)
        tree_group = VGroup(tree_card, lbl_tree, t_nodes, tree_note_header)

        # 3. Kernel Fusion Card
        fuse_card = RoundedRectangle(corner_radius=0.15, height=4.2, width=4.8, fill_color=COLOR_CARD_BG, fill_opacity=0.9, stroke_color=COLOR_EMERALD, stroke_width=1.2).shift(RIGHT * 2.6 + DOWN * 0.2)
        lbl_fuse = Text("HỢP NHẤT KERNEL TRÊN BỘ NHỚ SRAM", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_EMERALD).next_to(fuse_card.get_top(), DOWN, buff=0.25)

        fuse_1 = Text("• Nạp trực tiếp x_t từ HBM vào SRAM", font=FONT_FAMILY, font_size=12.0, color=COLOR_TEXT).shift(RIGHT * 2.6 + UP * 0.8)
        fuse_2 = Text("• Tính rời rạc hóa & Parallel Scan trên SRAM", font=FONT_FAMILY, font_size=12.0, color=COLOR_AMBER).shift(RIGHT * 2.6 + UP * 0.2)
        fuse_3 = Text("• KHÔNG ghi trạng thái ẩn h_t khổng lồ ra HBM", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_ROSE).shift(RIGHT * 2.6 + DOWN * 0.4)
        fuse_4 = Text("• Triệt tiêu hoàn toàn tắc nghẽn Bus bộ nhớ", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_EMERALD).shift(RIGHT * 2.6 + DOWN * 1.0)

        fuse_group = VGroup(fuse_card, lbl_fuse, fuse_1, fuse_2, fuse_3, fuse_4)

        self.play(FadeIn(tree_group), FadeIn(fuse_group), run_time=1.2)
        self.wait(2.0)


# =============================================================================
# SCENE 05: THỰC TẾ VẬN HÀNH & ƯU THẾ INFERENCE
# =============================================================================
class Tap10Scene05LabExperiment(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG

        # 1. Header HUD Pill
        header_text = Text(
            "THỰC TẾ VẬN HÀNH // ƯU THẾ INFERENCE O(1) VÀ GIỚI HẠN CỦA MAMBA",
            font=FONT_FAMILY, font_size=13, weight=BOLD, color=COLOR_ROSE
        )
        header_box = RoundedRectangle(
            corner_radius=0.12, height=0.5, width=header_text.width + 0.6,
            fill_color="#141826", fill_opacity=0.9, stroke_color=COLOR_ROSE, stroke_width=1.2
        ).to_edge(UP, buff=0.35)
        header_text.move_to(header_box.get_center())
        self.play(FadeIn(header_box), Write(header_text), run_time=0.6)

        # 2. Left vs Right: Inference Comparison
        inf_card = RoundedRectangle(corner_radius=0.15, height=3.2, width=4.7, fill_color=COLOR_CARD_BG, fill_opacity=0.9, stroke_color=COLOR_EMERALD, stroke_width=1.2).shift(LEFT * 2.6 + UP * 0.4)
        lbl_inf = Text("ƯU THẾ SUY LUẬN VƯỢT TRỘI", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_EMERALD).next_to(inf_card.get_top(), DOWN, buff=0.25)
        inf_1 = Text("• Bộ nhớ VRAM: O(1) cố định hoàn hảo", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_TEXT).shift(LEFT * 2.6 + UP * 0.7)
        inf_2 = Text("• Không có K-V Cache phình to theo chuỗi", font=FONT_FAMILY, font_size=12.0, color=COLOR_CYAN).shift(LEFT * 2.6 + UP * 0.2)
        inf_3 = Text("• Thông lượng sinh token tăng 4x - 5x", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_EMERALD).shift(LEFT * 2.6 + DOWN * 0.3)
        inf_group = VGroup(inf_card, lbl_inf, inf_1, inf_2, inf_3)

        lim_card = RoundedRectangle(corner_radius=0.15, height=3.2, width=4.7, fill_color=COLOR_CARD_BG, fill_opacity=0.9, stroke_color=COLOR_AMBER, stroke_width=1.2).shift(RIGHT * 2.6 + UP * 0.4)
        lbl_lim = Text("GIỚI HẠN THỰC TẾ & ĐÁNH ĐỔI", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_AMBER).next_to(lim_card.get_top(), DOWN, buff=0.25)
        lim_1 = Text("• Nén thông tin vào trạng thái hữu hạn", font=FONT_FAMILY, font_size=12.0, color=COLOR_TEXT).shift(RIGHT * 2.6 + UP * 0.7)
        lim_2 = Text("• Trí nhớ liên tưởng (Recall) kém hơn Attention", font=FONT_FAMILY, font_size=12.0, color=COLOR_ROSE).shift(RIGHT * 2.6 + UP * 0.2)
        lim_3 = Text("• Xu hướng SOTA: Kiến trúc lai ghép (Hybrid)", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_GOLD).shift(RIGHT * 2.6 + DOWN * 0.3)
        lim_group = VGroup(lim_card, lbl_lim, lim_1, lim_2, lim_3)

        self.play(FadeIn(inf_group), FadeIn(lim_group), run_time=1.0)

        # 3. Bottom Architecture Insight Pill
        insight_bar = RoundedRectangle(corner_radius=0.12, height=1.1, width=9.6, fill_color="#181528", fill_opacity=0.95, stroke_color=COLOR_GOLD, stroke_width=1.2).shift(DOWN * 2.0)
        insight_title = Text("TƯ DUY KỸ NGHỆ HIỆN ĐẠI (JAMBA, SAMBA):", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_GOLD).shift(DOWN * 1.7)
        insight_val_header = Text("Kết Hợp Tầng Mamba Tuyến Tính Tốc Độ Cao Với Attention Truyền Thống", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_TEXT).shift(DOWN * 2.2)
        insight_group = VGroup(insight_bar, insight_title, insight_val_header)

        self.play(FadeIn(insight_group), run_time=0.8)
        self.wait(2.0)


# =============================================================================
# SCENE 06: OUTRO — 5x5 MOSAIC & EPISODE 11 TEASER
# =============================================================================
class Tap10Scene06Outro(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "TỔNG KẾT & CẦU NỐI KỸ NGHỆ")

        scene_title = Text(
            "BÀN GIAO TRI THỨC // MAMBA & STATE SPACE MODELS",
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
        # 1. Next Video Card (Episode 11: Mixture of Experts - MoE)
        next_card = RoundedRectangle(
            corner_radius=0.12, width=3.8, height=2.0,
            fill_color=COLOR_PANEL, fill_opacity=0.7, stroke_color=COLOR_CYAN, stroke_width=1.5
        ).move_to(RIGHT * 3.5 + UP * 1.5)
        next_header = Text("TẬP TIẾP THEO // TẬP 11", font="Noto Sans", font_size=12.5, weight=BOLD, color=COLOR_CYAN)
        next_sub_header = Text("MẠNG CHUYÊN GIA MoE: MIXTRAL", font="Noto Sans", font_size=12.0, color=COLOR_TEXT).next_to(next_header, DOWN, buff=0.18)
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
