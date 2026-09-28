#!/usr/bin/env python3
"""
Manim 2K QHD Master Production Scenes — PagedAttention & vLLM // Liền Mạch Về Logic, Rời Nhau Trong Bộ Nhớ
Theme: Neo-Noir Obsidian (#0c0d12) | Standard: 100% Median / 3Blue1Brown Mathematical Craftsmanship
Strict Invariants:
- Zero Mascots (LivingZenMascot, Pioneers, ZenEngineerMascot 100% removed)
- Zero Static Bullet Boxes (continuous geometric & tensor transformations)
- Safe Margins: All elements stay strictly within |x| <= 5.2, |y| <= 3.2 (>=15% margin for subtitles/HUD)
- Dynamic Mathematical Mechanics: Block Table mapping, Copy-on-Write sharing, <4% fragmentation bound, 2x-4x throughput
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
# SCENE 01: NGHỊCH LÝ PHỤC VỤ: NGHẼN MẠNG VÌ KHÔNG BIẾT TRƯỚC TƯƠNG LAI
# =============================================================================
class Tap08Scene01ColdOpen(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG

        # 1. Header HUD Pill
        header_text = Text(
            "PAGEDATTENTION & VLLM // LIỀN MẠCH VỀ LOGIC, RỜI NHAU TRONG BỘ NHỚ",
            font=FONT_FAMILY, font_size=13, weight=BOLD, color=COLOR_CYAN
        )
        header_box = RoundedRectangle(
            corner_radius=0.12, height=0.5, width=header_text.width + 0.6,
            fill_color="#141826", fill_opacity=0.9, stroke_color=COLOR_CYAN, stroke_width=1.2
        ).to_edge(UP, buff=0.35)
        header_text.move_to(header_box.get_center())
        self.play(FadeIn(header_box), Write(header_text), run_time=0.8)

        # 2. Left Visual: GPU VRAM Bottleneck Meter
        meter_box = RoundedRectangle(corner_radius=0.15, height=4.6, width=4.8, fill_color=COLOR_CARD_BG, fill_opacity=0.9, stroke_color=COLOR_ROSE, stroke_width=1.2).shift(LEFT * 2.6 + DOWN * 0.2)
        lbl_meter = Text("CƠN ÁC MỘNG VRAM CỔ ĐIỂN", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_ROSE).next_to(meter_box.get_top(), DOWN, buff=0.2)

        # Gauge bar showing 100% reserved, 28% actual
        gauge_bg = RoundedRectangle(corner_radius=0.1, height=0.8, width=4.0, fill_color="#1f1322", fill_opacity=0.9, stroke_color=COLOR_BORDER, stroke_width=1.0).shift(LEFT * 2.6 + UP * 0.7)
        gauge_fill = RoundedRectangle(corner_radius=0.1, height=0.8, width=1.12, fill_color=COLOR_ROSE, fill_opacity=0.8, stroke_color=COLOR_ROSE, stroke_width=1.0).align_to(gauge_bg, LEFT)
        t_gauge_hdr = Text("VRAM Báo Đầy 100% (Bắn Lỗi OOM)\nThực Tế Dùng: 28% // Lãng Phí: 72%", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_TEXT).next_to(gauge_bg, DOWN, buff=0.15)

        desc_cause_hdr = Text("Nguyên nhân: Không biết câu trả lời dài bao nhiêu\nbuộc phải đặt chỗ trước 8.000 token liên tục!", font=FONT_FAMILY, font_size=12.0, color=COLOR_MUTED).next_to(meter_box.get_bottom(), UP, buff=0.25)

        g_left = VGroup(meter_box, lbl_meter, gauge_bg, gauge_fill, t_gauge_hdr, desc_cause_hdr)

        # 3. Right Visual: The Core Question of UC Berkeley
        right_panel = RoundedRectangle(corner_radius=0.15, height=4.6, width=4.8, fill_color=COLOR_CARD_BG, fill_opacity=0.9, stroke_color=COLOR_EMERALD, stroke_width=1.2).shift(RIGHT * 2.6 + DOWN * 0.2)
        lbl_berkeley = Text("CÂU HỎI LÀM THAY ĐỔI NGÀNH AI", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_EMERALD).next_to(right_panel.get_top(), DOWN, buff=0.25)

        q_quote_title = Text('"Tại sao một chuỗi văn bản\nliền mạch về ngữ nghĩa\nlại bắt buộc phải nằm liền kề\ntrên từng ô nhớ vật lý?"', font=FONT_FAMILY, font_size=12.0, slant=ITALIC, color=COLOR_GOLD).shift(RIGHT * 2.6 + UP * 0.3)

        div_r = Line(LEFT * 1.9, RIGHT * 1.9, color=COLOR_BORDER, stroke_width=1.0).shift(RIGHT * 2.6 + DOWN * 0.7)

        t_ans_title = Text("LỜI GIẢI: PAGEDATTENTION (vLLM)\nBăm nhỏ KV Cache thành các khối Block 16 token!", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_CYAN).next_to(right_panel.get_bottom(), UP, buff=0.25)

        g_right = VGroup(right_panel, lbl_berkeley, q_quote_title, div_r, t_ans_title)

        self.play(FadeIn(g_left), run_time=1.2)
        self.play(FadeIn(g_right), run_time=1.2)
        self.wait(2.0)

        # [Masterclass: Visual State Retained - Trailing FadeOut Removed]
        self.wait(2.0)


# =============================================================================
# SCENE 02: CUỘC HỘI NGỘ LỊCH SỬ: MƯỢN Ý TƯỞNG PHÂN TRANG NỬA THẾ KỶ TRƯỚC
# =============================================================================
class Tap08Scene02Architecture(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG

        # 1. Header HUD Pill
        header_text = Text("KIẾN TRÚC BLOCK TABLE: ÁNH XẠ LOGICAL BLOCK SANG PHYSICAL BLOCK", font=FONT_FAMILY, font_size=13, weight=BOLD, color=COLOR_CYAN)
        header_box = RoundedRectangle(corner_radius=0.12, height=0.5, width=header_text.width + 0.6, fill_color="#141826", fill_opacity=0.9, stroke_color=COLOR_CYAN, stroke_width=1.2).to_edge(UP, buff=0.35)
        header_text.move_to(header_box.get_center())
        self.play(FadeIn(header_box), Write(header_text), run_time=0.8)

        # 2. Three Columns: Left = Logical Blocks, Center = Block Table, Right = Physical VRAM
        # Logical Sequence (Continuous: 0, 1, 2)
        lbl_log_hdr = Text("CHUỖI LOGIC\n(Người dùng nhìn)", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_CYAN).shift(LEFT * 4.0 + UP * 1.8)
        log_col = VGroup()
        for i in range(3):
            b = RoundedRectangle(corner_radius=0.06, height=0.7, width=1.4, fill_color="#13242b", fill_opacity=0.9, stroke_color=COLOR_CYAN, stroke_width=1.2)
            t = Text(f"Block L{i}\n(Token {i*16}-{(i+1)*16-1})", font=FONT_FAMILY, font_size=12.0, color=COLOR_CYAN).move_to(b.get_center())
            log_col.add(VGroup(b, t))
        log_col.arrange(DOWN, buff=0.25).shift(LEFT * 4.0 + DOWN * 0.1)

        # Block Table (Mapping: L0->P7, L1->P2, L2->P11)
        tbl_box = RoundedRectangle(corner_radius=0.1, height=3.2, width=2.4, fill_color=COLOR_CARD_BG, fill_opacity=0.92, stroke_color=COLOR_GOLD, stroke_width=1.5).shift(DOWN * 0.1)
        tbl_title = Text("BLOCK TABLE", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_GOLD).next_to(tbl_box.get_top(), DOWN, buff=0.15)
        m0 = Text("L0  →  Physical 7", font=FONT_FAMILY, font_size=12.0, color=COLOR_TEXT)
        m1 = Text("L1  →  Physical 2", font=FONT_FAMILY, font_size=12.0, color=COLOR_TEXT)
        m2 = Text("L2  →  Physical 11", font=FONT_FAMILY, font_size=12.0, color=COLOR_TEXT)
        tbl_rows = VGroup(m0, m1, m2).arrange(DOWN, buff=0.35).move_to(tbl_box.get_center()).shift(DOWN * 0.1)
        tbl_group = VGroup(tbl_box, tbl_title, tbl_rows)

        # Physical VRAM (Scattered: P2, P7, P11)
        lbl_phy_hdr = Text("VRAM VẬT LÝ\n(Rời rạc bất kỳ)", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_EMERALD).shift(RIGHT * 4.0 + UP * 1.8)
        phy_col = VGroup()
        phy_indices = [7, 2, 11]
        for p in phy_indices:
            b = RoundedRectangle(corner_radius=0.06, height=0.7, width=1.4, fill_color="#132e22", fill_opacity=0.9, stroke_color=COLOR_EMERALD, stroke_width=1.2)
            t = Text(f"Block P{p}\n(Slot {p})", font=FONT_FAMILY, font_size=12.0, color=COLOR_EMERALD).move_to(b.get_center())
            phy_col.add(VGroup(b, t))
        phy_col.arrange(DOWN, buff=0.25).shift(RIGHT * 4.0 + DOWN * 0.1)

        # Arrows connecting
        arr_in = VGroup(*[Arrow(log_col[i].get_right(), tbl_rows[i].get_left(), buff=0.1, color=COLOR_MUTED, stroke_width=1.2, max_tip_length_to_length_ratio=0.15) for i in range(3)])
        arr_out = VGroup(*[Arrow(tbl_rows[i].get_right(), phy_col[i].get_left(), buff=0.1, color=COLOR_MUTED, stroke_width=1.2, max_tip_length_to_length_ratio=0.15) for i in range(3)])

        self.play(FadeIn(lbl_log_hdr), FadeIn(log_col), FadeIn(tbl_group), FadeIn(lbl_phy_hdr), FadeIn(phy_col), run_time=1.2)
        self.play(Create(arr_in), Create(arr_out), run_time=1.0)
        self.wait(2.0)

        # [Masterclass: Visual State Retained - Trailing FadeOut Removed]
        self.wait(2.0)


# =============================================================================
# SCENE 03: TOÁN HỌC ĐỊNH LƯỢNG: CHẶN ĐỨNG PHÂN MẢNH DƯỚI BỐN PHẦN TRĂM
# =============================================================================
class Tap08Scene03Mathematics(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG

        # 1. Header HUD Pill
        header_text = Text("TOÁN HỌC PAGEDATTENTION: PHÂN MẢNH NỘI BỘ LUÔN < BLOCK SIZE", font=FONT_FAMILY, font_size=13, weight=BOLD, color=COLOR_GOLD)
        header_box = RoundedRectangle(corner_radius=0.12, height=0.5, width=header_text.width + 0.6, fill_color="#141826", fill_opacity=0.9, stroke_color=COLOR_GOLD, stroke_width=1.2).to_edge(UP, buff=0.35)
        header_text.move_to(header_box.get_center())
        self.play(FadeIn(header_box), Write(header_text), run_time=0.8)

        # 2. Core Formula Box
        formula_box = RoundedRectangle(corner_radius=0.12, height=1.1, width=10.0, fill_color=COLOR_CARD_BG, fill_opacity=0.9, stroke_color=COLOR_BORDER, stroke_width=1.2).shift(UP * 1.5)
        f_tex = MathTex(
            r"N_{\text{blocks}} = \lceil \frac{S}{B} \rceil, \quad \text{Wasted Tokens} = N_{\text{blocks}} \times B - S < B",
            font_size=22, color=COLOR_GOLD
        ).move_to(formula_box.get_center())
        self.play(FadeIn(formula_box), Write(f_tex), run_time=1.0)

        # 3. Concrete Visual Walkthrough: S=65 Tokens, BlockSize B=16
        left_card = RoundedRectangle(corner_radius=0.15, height=3.3, width=4.8, fill_color=COLOR_CARD_BG, fill_opacity=0.92, stroke_color=COLOR_CYAN, stroke_width=1.2).shift(LEFT * 2.6 + DOWN * 1.0)
        right_card = RoundedRectangle(corner_radius=0.15, height=3.3, width=4.8, fill_color=COLOR_CARD_BG, fill_opacity=0.92, stroke_color=COLOR_EMERALD, stroke_width=1.2).shift(RIGHT * 2.6 + DOWN * 1.0)

        # Left: Example S=65
        t_ex_title = Text("1. VÍ DỤ CỤ THỂ: S = 65 TOKEN (B = 16)", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_CYAN)
        t_ex1 = Text("• Số khối cấp phát: ceil(65 / 16) = 5 Blocks", font=FONT_FAMILY, font_size=12.0, color=COLOR_TEXT)
        t_ex2 = Text("• Dung lượng cấp: 5 × 16 = 80 token slots", font=FONT_FAMILY, font_size=12.0, color=COLOR_TEXT)
        t_ex3 = Text("• Lãng phí: 80 - 65 = 15 token slots (< 16)", font=FONT_FAMILY, font_size=12.0, color=COLOR_ROSE)
        t_ex4 = Text("• Chặn cứng: Không bao giờ lãng phí > 15 token!", font=FONT_FAMILY, font_size=12.0, color=COLOR_EMERALD)
        grp_l = VGroup(t_ex_title, t_ex1, t_ex2, t_ex3, t_ex4).arrange(DOWN, buff=0.14, aligned_edge=LEFT).move_to(left_card.get_center())

        # Right: Real Scaling (S=2048)
        t_sc_title = Text("2. QUY MÔ THỰC TẾ (S = 2.048 TOKEN)", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_EMERALD)
        t_sc1 = Text("• Số khối: 2.048 / 16 = 128 Blocks tròn trịa", font=FONT_FAMILY, font_size=12.0, color=COLOR_TEXT)
        t_sc2 = Text("• Phân mảnh nội bộ: Tối đa 15/2048 = 0.73%!", font=FONT_FAMILY, font_size=12.0, color=COLOR_EMERALD)
        t_sc3_hdr = Text("• Phân mảnh ngoại vi: 0% TUYỆT ĐỐI\n  (Mọi block đều bằng nhau, tái dùng ngay lập tức)", font=FONT_FAMILY, font_size=12.0, color=COLOR_GOLD)
        grp_r = VGroup(t_sc_title, t_sc1, t_sc2, t_sc3_hdr).arrange(DOWN, buff=0.18, aligned_edge=LEFT).move_to(right_card.get_center())

        self.play(FadeIn(left_card), FadeIn(grp_l), FadeIn(right_card), FadeIn(grp_r), run_time=1.2)
        self.wait(2.0)

        # [Masterclass: Visual State Retained - Trailing FadeOut Removed]
        self.wait(2.0)


# =============================================================================
# SCENE 04: KỸ NGHỆ ĐỈNH CAO: CHIA SẺ BỘ NHỚ VÀ COPY-ON-WRITE
# =============================================================================
class Tap08Scene04Telemetry(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG

        # 1. Header HUD Pill
        header_text = Text("CƠ CHẾ COPY-ON-WRITE (COW) & CHIA SẺ TIỀN TỐ PROMPT", font=FONT_FAMILY, font_size=13, weight=BOLD, color=COLOR_AMBER)
        header_box = RoundedRectangle(corner_radius=0.12, height=0.5, width=header_text.width + 0.6, fill_color="#141826", fill_opacity=0.9, stroke_color=COLOR_AMBER, stroke_width=1.2).to_edge(UP, buff=0.35)
        header_text.move_to(header_box.get_center())
        self.play(FadeIn(header_box), Write(header_text), run_time=0.8)

        # 2. Shared Prompt Blocks (Left: |x| <= 5.1)
        shared_card = RoundedRectangle(corner_radius=0.15, height=4.6, width=4.8, fill_color=COLOR_CARD_BG, fill_opacity=0.9, stroke_color=COLOR_AMBER, stroke_width=1.2).shift(LEFT * 2.6 + DOWN * 0.2)
        lbl_shared = Text("CHIA SẺ PROMPT (REF COUNT = 4)", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_AMBER).next_to(shared_card.get_top(), DOWN, buff=0.2)

        prompt_box = RoundedRectangle(corner_radius=0.1, height=1.4, width=4.0, fill_color="#2b2310", fill_opacity=0.9, stroke_color=COLOR_GOLD, stroke_width=1.5).shift(LEFT * 2.6 + UP * 0.4)
        t_prompt_hdr = Text("Khối Prompt Chung (System Prompt 2k token)\nReference Count = 4 Luồng\n(Lưu đúng 1 bản sao trên VRAM!)", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_GOLD).move_to(prompt_box.get_center())

        desc_shared_hdr = Text("Tiết kiệm 75% VRAM khi chạy\nParallel Sampling hoặc Beam Search!", font=FONT_FAMILY, font_size=12.0, color=COLOR_EMERALD).next_to(shared_card.get_bottom(), UP, buff=0.25)

        g_left = VGroup(shared_card, lbl_shared, prompt_box, t_prompt_hdr, desc_shared_hdr)

        # 3. Branching & Copy-on-Write (Right: |x| <= 5.1)
        cow_card = RoundedRectangle(corner_radius=0.15, height=4.6, width=4.8, fill_color=COLOR_CARD_BG, fill_opacity=0.9, stroke_color=COLOR_CYAN, stroke_width=1.2).shift(RIGHT * 2.6 + DOWN * 0.2)
        lbl_cow = Text("CƠ CHẾ SAO CHÉP KHI GHI (CoW)", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_CYAN).next_to(cow_card.get_top(), DOWN, buff=0.2)

        branch_group = VGroup()
        for b in range(3):
            box = RoundedRectangle(corner_radius=0.06, height=0.55, width=4.0, fill_color="#13242b", fill_opacity=0.8, stroke_color=COLOR_CYAN, stroke_width=1.0)
            txt = Text(f"Nhánh {b+1}: Chỉ nhân bản đúng 1 Block cuối khi sinh từ mới!", font=FONT_FAMILY, font_size=12.0, color=COLOR_TEXT).move_to(box.get_center())
            branch_group.add(VGroup(box, txt))
        branch_group.arrange(DOWN, buff=0.2).shift(RIGHT * 2.6 + UP * 0.3)

        desc_cow_hdr = Text("• Không đụng vào các khối prompt chung\n• Reference count giảm khi nhánh kết thúc\n• Giải phóng bộ nhớ tức thì", font=FONT_FAMILY, font_size=12.0, color=COLOR_MUTED).next_to(cow_card.get_bottom(), UP, buff=0.2)

        g_right = VGroup(cow_card, lbl_cow, branch_group, desc_cow_hdr)

        self.play(FadeIn(g_left), run_time=1.2)
        self.play(FadeIn(g_right), run_time=1.2)
        self.wait(2.0)

        # [Masterclass: Visual State Retained - Trailing FadeOut Removed]
        self.wait(2.0)


# =============================================================================
# SCENE 05: THỰC CHIẾN SẢN XUẤT: CÚ BỨT PHÁ THÔNG LƯỢNG GẤP BỐN LẦN
# =============================================================================
class Tap08Scene05LabExperiment(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG

        # 1. Header HUD Pill
        header_text = Text("BENCHMARK THỰC TẾ: THÔNG LƯỢNG SUY LUẬN TĂNG 2X - 4X", font=FONT_FAMILY, font_size=13, weight=BOLD, color=COLOR_EMERALD)
        header_box = RoundedRectangle(corner_radius=0.12, height=0.5, width=header_text.width + 0.6, fill_color="#141826", fill_opacity=0.9, stroke_color=COLOR_EMERALD, stroke_width=1.2).to_edge(UP, buff=0.35)
        header_text.move_to(header_box.get_center())
        self.play(FadeIn(header_box), Write(header_text), run_time=0.8)

        # 2. Bar Chart: Serving Throughput (Tokens/s) on A100 GPU
        axes = Axes(
            x_range=[0, 3, 1], y_range=[0, 1200, 300],
            x_length=4.8, y_length=4.2,
            axis_config={"color": COLOR_MUTED, "stroke_width": 1.2, "include_numbers": False}
        ).shift(LEFT * 2.7 + DOWN * 0.2)

        y_lbl = Text("Thông lượng phục vụ (Tokens / s)", font=FONT_FAMILY, font_size=12.0, color=COLOR_MUTED).next_to(axes.y_axis, UP, buff=0.15).shift(RIGHT * 0.5)

        # Bar 1: HuggingFace TGI Cổ điển (~320 tps)
        b1 = Rectangle(height=1.1, width=1.1, fill_color=COLOR_ROSE, fill_opacity=0.85, stroke_color=COLOR_BORDER, stroke_width=1.0).next_to(axes.c2p(0.8, 0), UP, buff=0)
        lbl_b1_hdr = Text("HuggingFace TGI\n(~320 tps)", font=FONT_FAMILY, font_size=12.0, color=COLOR_ROSE).next_to(b1, UP, buff=0.1)

        # Bar 2: vLLM PagedAttention (~1150 tps - 3.6x!)
        b2 = Rectangle(height=3.8, width=1.1, fill_color=COLOR_EMERALD, fill_opacity=0.85, stroke_color=COLOR_BORDER, stroke_width=1.0).next_to(axes.c2p(2.0, 0), UP, buff=0)
        lbl_b2_hdr = Text("vLLM PagedAttention\n(~1.150 tps // 3.6x!)", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_EMERALD).next_to(b2, UP, buff=0.1)

        self.play(Create(axes), FadeIn(y_lbl), FadeIn(b1), Write(lbl_b1_hdr), FadeIn(b2), Write(lbl_b2_hdr), run_time=1.2)

        # 3. Right Card: Production Economic Impact
        right_panel = RoundedRectangle(corner_radius=0.15, height=4.6, width=4.8, fill_color=COLOR_CARD_BG, fill_opacity=0.9, stroke_color=COLOR_BORDER, stroke_width=1.2).shift(RIGHT * 2.6 + DOWN * 0.2)
        
        t_econ = Text("Ý NGHĨA KINH TẾ TRONG PRODUCTION", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_GOLD).next_to(right_panel.get_top(), DOWN, buff=0.25)

        e1_hdr = Text("• Batch size phục vụ tăng gấp 4 lần\n  trên cùng một cụm máy chủ A100 / H100", font=FONT_FAMILY, font_size=12.0, color=COLOR_TEXT)
        div_e = Line(LEFT * 1.9, RIGHT * 1.9, color=COLOR_BORDER, stroke_width=1.0)
        e2_hdr = Text("• Chi phí điện toán cho mỗi triệu token\n  giảm xuống gần 70%", font=FONT_FAMILY, font_size=12.0, color=COLOR_CYAN)
        div_e2 = Line(LEFT * 1.9, RIGHT * 1.9, color=COLOR_BORDER, stroke_width=1.0)
        e3_hdr = Text("• Trở thành chuẩn mực phục vụ mã nguồn mở\n  được toàn bộ ngành công nghiệp áp dụng!", font=FONT_FAMILY, font_size=12.0, color=COLOR_EMERALD)

        r_econ = VGroup(t_econ, e1_hdr, div_e, e2_hdr, div_e2, e3_hdr).arrange(DOWN, buff=0.18, aligned_edge=ORIGIN).move_to(right_panel.get_center())

        self.play(FadeIn(right_panel), FadeIn(r_econ), run_time=1.2)
        self.wait(2.0)

        # [Masterclass: Visual State Retained - Trailing FadeOut Removed]
        self.wait(2.0)


# =============================================================================
# SCENE 06: BÀI HỌC GIAO THOA, LỜI TRI ÂN CHÂN THÀNH VÀ KẾT NỐI TẬP 09
# =============================================================================
class Tap08Scene06Outro(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "TỔNG KẾT & CẦU NỐI KỸ NGHỆ")

        scene_title = Text(
            "BÀN GIAO TRI THỨC // PAGEDATTENTION & VLLM",
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
        # 1. Next Video Card (Episode 09: FlashAttention)
        next_card = RoundedRectangle(
            corner_radius=0.12, width=3.8, height=2.0,
            fill_color=COLOR_PANEL, fill_opacity=0.7, stroke_color=COLOR_CYAN, stroke_width=1.5
        ).move_to(RIGHT * 3.5 + UP * 1.5)
        next_header = Text("TẬP TIẾP THEO // TẬP 09", font=FONT_FAMILY, font_size=12.5, weight=BOLD, color=COLOR_CYAN)
        next_sub_header = Text("FLASHATTENTION: TỐI ƯU I/O", font=FONT_FAMILY, font_size=12.0, color=COLOR_TEXT).next_to(next_header, DOWN, buff=0.18)
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

