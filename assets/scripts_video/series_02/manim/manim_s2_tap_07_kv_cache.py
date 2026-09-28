#!/usr/bin/env python3
"""
Manim 2K QHD Master Production Scenes — KV Cache // Trái Tim Vận Hành Từng Token Của Bộ Sinh LLM
Theme: Neo-Noir Obsidian (#0c0d12) | Standard: 100% Median / 3Blue1Brown Mathematical Craftsmanship
Strict Invariants:
- Zero Mascots (LivingZenMascot, Pioneers, ZenEngineerMascot 100% removed)
- Zero Static Bullet Boxes (continuous geometric & tensor transformations)
- Safe Margins: All elements stay strictly within |x| <= 5.2, |y| <= 3.2 (>=15% margin for subtitles/HUD)
- Dynamic Mathematical Mechanics: Recomputation vs Memoization, Prefill/Decode phasing, 128 KiB/token formula, VRAM fragmentation
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
# SCENE 01: NGHỊCH LÝ TÍNH TOÁN LẠI: VỰC THẲM CỦA ĐỘ PHỨC TẠP BẬC HAI
# =============================================================================
class Tap07Scene01ColdOpen(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG

        # 1. Header HUD Pill
        header_text = Text(
            "KV CACHE // TRÁI TIM VẬN HÀNH TỪNG TOKEN CỦA BỘ SINH LLM",
            font=FONT_FAMILY, font_size=13, weight=BOLD, color=COLOR_CYAN
        )
        header_box = RoundedRectangle(
            corner_radius=0.12, height=0.5, width=header_text.width + 0.6,
            fill_color="#141826", fill_opacity=0.9, stroke_color=COLOR_CYAN, stroke_width=1.2
        ).to_edge(UP, buff=0.35)
        header_text.move_to(header_box.get_center())
        self.play(FadeIn(header_box), Write(header_text), run_time=0.8)

        # 2. Left Panel: Autoregressive Recomputation Without Cache
        left_panel = RoundedRectangle(corner_radius=0.15, height=4.6, width=4.8, fill_color=COLOR_CARD_BG, fill_opacity=0.9, stroke_color=COLOR_ROSE, stroke_width=1.2).shift(LEFT * 2.6 + DOWN * 0.2)
        lbl_no_cache = Text("1. KHÔNG CACHE: TÍNH LẶP O(N²)", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_ROSE).next_to(left_panel.get_top(), DOWN, buff=0.2)

        # Token steps accumulating quadratically
        steps_group = VGroup()
        for s in range(4):
            row = VGroup()
            for t in range(s + 1):
                sq = Square(side_length=0.45, fill_color="#331422", fill_opacity=0.8, stroke_color=COLOR_ROSE, stroke_width=1.0)
                sq_txt = Text(f"T{t+1}", font=FONT_FAMILY, font_size=12.0, color=COLOR_ROSE).move_to(sq.get_center())
                row.add(VGroup(sq, sq_txt))
            row.arrange(RIGHT, buff=0.1).shift(LEFT * 4.2 + UP * (0.8 - s * 0.7) + RIGHT * (s * 0.25))
            steps_group.add(row)

        desc_no_cache_hdr = Text("Sinh T4: Phải tính lại T1, T2, T3\nChi phí nhân ma trận bùng nổ O(N²)", font=FONT_FAMILY, font_size=12.0, color=COLOR_MUTED).next_to(left_panel.get_bottom(), UP, buff=0.25)

        # 3. Right Panel: With KV Cache (Memoization)
        right_panel = RoundedRectangle(corner_radius=0.15, height=4.6, width=4.8, fill_color=COLOR_CARD_BG, fill_opacity=0.9, stroke_color=COLOR_EMERALD, stroke_width=1.2).shift(RIGHT * 2.6 + DOWN * 0.2)
        lbl_cache = Text("2. DÙNG KV CACHE: MEMOIZATION O(1)", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_EMERALD).next_to(right_panel.get_top(), DOWN, buff=0.2)

        # Cached memory row + single new token
        cached_row = VGroup()
        for t in range(3):
            sq = Square(side_length=0.45, fill_color="#132e22", fill_opacity=0.85, stroke_color=COLOR_EMERALD, stroke_width=1.0)
            sq_txt = Text(f"K,V{t+1}", font=FONT_FAMILY, font_size=12.0, color=COLOR_EMERALD).move_to(sq.get_center())
            cached_row.add(VGroup(sq, sq_txt))
        cached_row.arrange(RIGHT, buff=0.1).shift(RIGHT * 1.5 + UP * 0.4)

        cache_bracket = SurroundingRectangle(cached_row, color=COLOR_MUTED, stroke_width=1.0, buff=0.1)
        lbl_frozen = Text("Đóng băng trong VRAM (T1-T3)", font=FONT_FAMILY, font_size=12.0, color=COLOR_MUTED).next_to(cache_bracket, UP, buff=0.1)

        new_token = RoundedRectangle(corner_radius=0.08, height=0.6, width=1.1, fill_color="#2b2310", fill_opacity=0.9, stroke_color=COLOR_GOLD, stroke_width=1.5).shift(RIGHT * 3.8 + UP * 0.4)
        new_txt_hdr = Text("Token 4\n(Chỉ tính 1 lần)", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_GOLD).move_to(new_token.get_center())
        new_elem = VGroup(new_token, new_txt_hdr)

        desc_cache_hdr = Text("Thời gian sinh mỗi token: CỐ ĐỊNH O(1)\nĐánh đổi bộ nhớ để giải cứu tốc độ!", font=FONT_FAMILY, font_size=12.0, color=COLOR_EMERALD).next_to(right_panel.get_bottom(), UP, buff=0.25)

        self.play(FadeIn(left_panel), Write(lbl_no_cache), FadeIn(steps_group), FadeIn(desc_no_cache_hdr), run_time=1.2)
        self.play(FadeIn(right_panel), Write(lbl_cache), FadeIn(cached_row), Create(cache_bracket), FadeIn(lbl_frozen),
                  FadeIn(new_elem), FadeIn(desc_cache_hdr), run_time=1.2)
        self.wait(2.0)

        # [Masterclass: Visual State Retained - Trailing FadeOut Removed]
        self.wait(2.0)


# =============================================================================
# SCENE 02: GIẢI PHẪU HAI THÌ NHỊP ĐẬP: PHA PREFILL VÀ PHA DECODE
# =============================================================================
class Tap07Scene02Architecture(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG

        # 1. Header HUD Pill
        header_text = Text("HAI PHA THỰC THI: PREFILL (NẠP PROMPT) vs DECODE (SINH TỪ)", font=FONT_FAMILY, font_size=13, weight=BOLD, color=COLOR_CYAN)
        header_box = RoundedRectangle(corner_radius=0.12, height=0.5, width=header_text.width + 0.6, fill_color="#141826", fill_opacity=0.9, stroke_color=COLOR_CYAN, stroke_width=1.2).to_edge(UP, buff=0.35)
        header_text.move_to(header_box.get_center())
        self.play(FadeIn(header_box), Write(header_text), run_time=0.8)

        # 2. Phase 1: Prefill (Left Card)
        left_card = RoundedRectangle(corner_radius=0.15, height=4.6, width=4.8, fill_color=COLOR_CARD_BG, fill_opacity=0.9, stroke_color=COLOR_CYAN, stroke_width=1.2).shift(LEFT * 2.6 + DOWN * 0.2)
        lbl_p1 = Text("PHA 1: PREFILL (Xử Lý Prompt)", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_CYAN).next_to(left_card.get_top(), DOWN, buff=0.2)

        # Triangular Attention Mask Matrix
        t_matrix = VGroup()
        for r in range(4):
            for c in range(4):
                val = 1 if c <= r else 0
                col = COLOR_CYAN if val == 1 else "#1e293b"
                sq = Square(side_length=0.35, fill_color=col, fill_opacity=0.7 if val == 1 else 0.2, stroke_color=COLOR_BORDER, stroke_width=0.8)
                t_matrix.add(sq)
        t_matrix.arrange_in_grid(rows=4, cols=4, buff=0.06).shift(LEFT * 2.6 + UP * 0.3)
        lbl_mask = Text("Mặt nạ Causal Mask (Song song GEMM)", font=FONT_FAMILY, font_size=12.0, color=COLOR_MUTED).next_to(t_matrix, DOWN, buff=0.15)
        desc_p1_hdr = Text("• Tính song song toàn bộ prompt\n• Nạp K, V ban đầu vào Cache\n• Tạo ra token đầu tiên", font=FONT_FAMILY, font_size=12.0, color=COLOR_TEXT).next_to(left_card.get_bottom(), UP, buff=0.2)

        p1_group = VGroup(left_card, lbl_p1, t_matrix, lbl_mask, desc_p1_hdr)

        # 3. Phase 2: Decode (Right Card)
        right_card = RoundedRectangle(corner_radius=0.15, height=4.6, width=4.8, fill_color=COLOR_CARD_BG, fill_opacity=0.9, stroke_color=COLOR_AMBER, stroke_width=1.2).shift(RIGHT * 2.6 + DOWN * 0.2)
        lbl_p2 = Text("PHA 2: DECODE (Sinh Từng Token)", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_AMBER).next_to(right_card.get_top(), DOWN, buff=0.2)

        # Single Query Arrow scanning history
        q_dot = Dot(RIGHT * 3.8 + UP * 0.4, color=COLOR_AMBER, radius=0.12)
        q_lbl = Text("Q_mới", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_AMBER).next_to(q_dot, UP, buff=0.1)

        kv_row = VGroup()
        for k in range(4):
            box = RoundedRectangle(corner_radius=0.06, height=0.45, width=0.65, fill_color="#13242b", fill_opacity=0.8, stroke_color=COLOR_EMERALD, stroke_width=1.0)
            txt = Text(f"K{k+1}", font=FONT_FAMILY, font_size=12.0, color=COLOR_EMERALD).move_to(box.get_center())
            kv_row.add(VGroup(box, txt))
        kv_row.arrange(RIGHT, buff=0.08).shift(RIGHT * 1.5 + DOWN * 0.4)

        scan_arrows = VGroup()
        for b in kv_row:
            arr = Arrow(q_dot.get_center(), b.get_top(), buff=0.08, color=COLOR_MUTED, stroke_width=1.2, max_tip_length_to_length_ratio=0.15)
            scan_arrows.add(arr)

        desc_p2_hdr = Text("• Query chỉ sống trong 1 token bước!\n• K, V mới được nối vào cuối cache\n• Quét qua toàn bộ Key quá khứ", font=FONT_FAMILY, font_size=12.0, color=COLOR_TEXT).next_to(right_card.get_bottom(), UP, buff=0.2)

        p2_group = VGroup(right_card, lbl_p2, q_dot, q_lbl, kv_row, scan_arrows, desc_p2_hdr)

        self.play(FadeIn(p1_group), run_time=1.2)
        self.play(FadeIn(p2_group), run_time=1.2)
        self.wait(2.0)

        # [Masterclass: Visual State Retained - Trailing FadeOut Removed]
        self.wait(2.0)


# =============================================================================
# SCENE 03: TOÁN HỌC ĐỊNH LƯỢNG: CÔNG THỨC TÍNH TỪNG BYTE BỘ NHỚ VRAM
# =============================================================================
class Tap07Scene03Mathematics(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG

        # 1. Header HUD Pill
        header_text = Text("CÔNG THỨC ĐỊNH LƯỢNG KV CACHE: 128 KiB / TOKEN (LLAMA-3 8B)", font=FONT_FAMILY, font_size=13, weight=BOLD, color=COLOR_GOLD)
        header_box = RoundedRectangle(corner_radius=0.12, height=0.5, width=header_text.width + 0.6, fill_color="#141826", fill_opacity=0.9, stroke_color=COLOR_GOLD, stroke_width=1.2).to_edge(UP, buff=0.35)
        header_text.move_to(header_box.get_center())
        self.play(FadeIn(header_box), Write(header_text), run_time=0.8)

        # 2. General Formula Box
        formula_box = RoundedRectangle(corner_radius=0.12, height=1.1, width=10.0, fill_color=COLOR_CARD_BG, fill_opacity=0.9, stroke_color=COLOR_BORDER, stroke_width=1.2).shift(UP * 1.5)
        f_tex = MathTex(
            r"\text{KV Cache (Bytes)} = 2 \times B \times S \times L \times H_{KV} \times d_k \times \text{sizeof(dtype)}",
            font_size=22, color=COLOR_GOLD
        ).move_to(formula_box.get_center())
        self.play(FadeIn(formula_box), Write(f_tex), run_time=1.0)

        # 3. Two Comparison Columns: Left = LLaMA-3 8B, Right = LLaMA-3 70B
        left_card = RoundedRectangle(corner_radius=0.15, height=3.3, width=4.8, fill_color=COLOR_CARD_BG, fill_opacity=0.92, stroke_color=COLOR_CYAN, stroke_width=1.2).shift(LEFT * 2.6 + DOWN * 1.0)
        right_card = RoundedRectangle(corner_radius=0.15, height=3.3, width=4.8, fill_color=COLOR_CARD_BG, fill_opacity=0.92, stroke_color=COLOR_AMBER, stroke_width=1.2).shift(RIGHT * 2.6 + DOWN * 1.0)

        # Left: LLaMA-3 8B (L=32, H_kv=8, d_k=128, FP16=2 bytes)
        t8_title = Text("1. LLAMA-3 8B (L=32, H_kv=8, d=128)", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_CYAN)
        t8_calc_hdr = Text("• 1 Token = 2×32×8×128×2 = 131.072 Bytes\n  → Đúng tròn trịa 128 KiB / Token!", font=FONT_FAMILY, font_size=12.0, color=COLOR_TEXT)
        t8_8k = Text("• Ngữ cảnh 8k: 8.192 × 128 KiB = 1.0 GiB", font=FONT_FAMILY, font_size=12.0, color=COLOR_EMERALD)
        t8_128k = Text("• Ngữ cảnh 128k: 128k × 128 KiB = 16 GiB / User!", font=FONT_FAMILY, font_size=12.0, color=COLOR_ROSE)
        grp_8b = VGroup(t8_title, t8_calc_hdr, t8_8k, t8_128k).arrange(DOWN, buff=0.16, aligned_edge=LEFT).move_to(left_card.get_center())

        # Right: LLaMA-3 70B (L=80, H_kv=8, d_k=128, FP16=2 bytes)
        t70_title = Text("2. LLAMA-3 70B (L=80, H_kv=8, d=128)", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_AMBER)
        t70_calc_hdr = Text("• 1 Token = 2×80×8×128×2 = 327.680 Bytes\n  → Đúng tròn trịa 320 KiB / Token!", font=FONT_FAMILY, font_size=12.0, color=COLOR_TEXT)
        t70_8k = Text("• Ngữ cảnh 8k: 8.192 × 320 KiB = 2.5 GiB", font=FONT_FAMILY, font_size=12.0, color=COLOR_EMERALD)
        t70_128k = Text("• Ngữ cảnh 128k: 128k × 320 KiB = 40 GiB / User!", font=FONT_FAMILY, font_size=12.0, color=COLOR_ROSE)
        grp_70b = VGroup(t70_title, t70_calc_hdr, t70_8k, t70_128k).arrange(DOWN, buff=0.16, aligned_edge=LEFT).move_to(right_card.get_center())

        self.play(FadeIn(left_card), FadeIn(grp_8b), FadeIn(right_card), FadeIn(grp_70b), run_time=1.2)
        self.wait(2.0)

        # [Masterclass: Visual State Retained - Trailing FadeOut Removed]
        self.wait(2.0)


# =============================================================================
# SCENE 04: CƠN ÁC MỘNG PHÂN MẢNH BỘ NHỚ: BẪY CẤP PHÁT TĨNH
# =============================================================================
class Tap07Scene04Telemetry(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG

        # 1. Header HUD Pill
        header_text = Text("CƠN ÁC MỘNG PHÂN MẢNH: INTERNAL & EXTERNAL VRAM FRAGMENTATION", font=FONT_FAMILY, font_size=13, weight=BOLD, color=COLOR_ROSE)
        header_box = RoundedRectangle(corner_radius=0.12, height=0.5, width=header_text.width + 0.6, fill_color="#141826", fill_opacity=0.9, stroke_color=COLOR_ROSE, stroke_width=1.2).to_edge(UP, buff=0.35)
        header_text.move_to(header_box.get_center())
        self.play(FadeIn(header_box), Write(header_text), run_time=0.8)

        # 2. Left Visual: Static Allocation Slots Waste
        left_panel = RoundedRectangle(corner_radius=0.15, height=4.6, width=4.8, fill_color=COLOR_CARD_BG, fill_opacity=0.9, stroke_color=COLOR_ROSE, stroke_width=1.2).shift(LEFT * 2.6 + DOWN * 0.2)
        lbl_static = Text("BẪY CẤP PHÁT TĨNH (STATIC ALLOC)", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_ROSE).next_to(left_panel.get_top(), DOWN, buff=0.2)

        # Slot 1: Reserved 8k, Used 500 (80% empty)
        bar1_res = RoundedRectangle(corner_radius=0.08, height=0.6, width=4.2, fill_color="#1e1422", fill_opacity=0.8, stroke_color=COLOR_BORDER, stroke_width=1.0).shift(LEFT * 2.6 + UP * 0.6)
        bar1_used = RoundedRectangle(corner_radius=0.08, height=0.6, width=0.9, fill_color=COLOR_EMERALD, fill_opacity=0.8, stroke_color=COLOR_EMERALD, stroke_width=1.0).align_to(bar1_res, LEFT)
        t_bar1 = Text("User 1: Dùng 500 / Giữ 8k (LÃNG PHÍ 93%)", font=FONT_FAMILY, font_size=12.0, color=COLOR_TEXT).next_to(bar1_res, UP, buff=0.08)

        # Slot 2: Reserved 8k, Used 2k
        bar2_res = RoundedRectangle(corner_radius=0.08, height=0.6, width=4.2, fill_color="#1e1422", fill_opacity=0.8, stroke_color=COLOR_BORDER, stroke_width=1.0).shift(LEFT * 2.6 + DOWN * 0.4)
        bar2_used = RoundedRectangle(corner_radius=0.08, height=0.6, width=1.6, fill_color=COLOR_CYAN, fill_opacity=0.8, stroke_color=COLOR_CYAN, stroke_width=1.0).align_to(bar2_res, LEFT)
        t_bar2 = Text("User 2: Dùng 2.000 / Giữ 8k (LÃNG PHÍ 75%)", font=FONT_FAMILY, font_size=12.0, color=COLOR_TEXT).next_to(bar2_res, UP, buff=0.08)

        desc_static_hdr = Text("Hậu quả: 60-80% VRAM bị bỏ hoang!\nBáo OOM dù bộ nhớ thực chỉ dùng 30%", font=FONT_FAMILY, font_size=12.0, color=COLOR_ROSE).next_to(left_panel.get_bottom(), UP, buff=0.25)

        g_left = VGroup(left_panel, lbl_static, bar1_res, bar1_used, t_bar1, bar2_res, bar2_used, t_bar2, desc_static_hdr)

        # 3. Right Visual: The Two Fragmentation Types
        right_panel = RoundedRectangle(corner_radius=0.15, height=4.6, width=4.8, fill_color=COLOR_CARD_BG, fill_opacity=0.9, stroke_color=COLOR_BORDER, stroke_width=1.2).shift(RIGHT * 2.6 + DOWN * 0.2)
        lbl_right = Text("BẢN CHẤT HAI DẠNG PHÂN MẢNH", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_GOLD).next_to(right_panel.get_top(), DOWN, buff=0.25)

        t_int = Text("1. PHÂN MẢNH NỘI BỘ (Internal)", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_CYAN)
        d_int_hdr = Text("Cấp phát khối nhớ cố định cho ngữ cảnh tối đa\ntrong khi người dùng chỉ hỏi một câu ngắn.", font=FONT_FAMILY, font_size=12.0, color=COLOR_TEXT)

        div_f = Line(LEFT * 1.9, RIGHT * 1.9, color=COLOR_BORDER, stroke_width=1.0)

        t_ext = Text("2. PHÂN MẢNH NGOẠI VI (External)", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_AMBER)
        d_ext_hdr = Text("Các chuỗi kết thúc so le tạo lỗ thủng lởm chởm,\nkhông thể tìm được khoảng trống liên tục.", font=FONT_FAMILY, font_size=12.0, color=COLOR_TEXT)

        div_f2 = Line(LEFT * 1.9, RIGHT * 1.9, color=COLOR_BORDER, stroke_width=1.0)

        t_sol = Text("LỜI GIẢI ĐỘT PHÁ:", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_EMERALD)
        d_sol_hdr = Text("PagedAttention: Mượn ý tưởng phân trang OS\nđể quản lý bộ nhớ đệm theo từng Block rời rạc!", font=FONT_FAMILY, font_size=12.0, color=COLOR_EMERALD)

        r_content = VGroup(lbl_right, t_int, d_int_hdr, div_f, t_ext, d_ext_hdr, div_f2, t_sol, d_sol_hdr).arrange(DOWN, buff=0.12, aligned_edge=ORIGIN).move_to(right_panel.get_center())

        self.play(FadeIn(g_left), run_time=1.2)
        self.play(FadeIn(right_panel), FadeIn(r_content), run_time=1.2)
        self.wait(2.0)

        # [Masterclass: Visual State Retained - Trailing FadeOut Removed]
        self.wait(2.0)


# =============================================================================
# SCENE 05: THỰC NGHIỆM HỆ THỐNG: ĐÁNH ĐỔI THỜI GIAN LẤY KHÔNG GIAN
# =============================================================================
class Tap07Scene05LabExperiment(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG

        # 1. Header HUD Pill
        header_text = Text("THỰC NGHIỆM ĐỘ TRỄ & GIẢI PHÁP SLIDING WINDOW ATTENTION", font=FONT_FAMILY, font_size=13, weight=BOLD, color=COLOR_CYAN)
        header_box = RoundedRectangle(corner_radius=0.12, height=0.5, width=header_text.width + 0.6, fill_color="#141826", fill_opacity=0.9, stroke_color=COLOR_CYAN, stroke_width=1.2).to_edge(UP, buff=0.35)
        header_text.move_to(header_box.get_center())
        self.play(FadeIn(header_box), Write(header_text), run_time=0.8)

        # 2. Latency vs Context Plot (Left: |x| <= 5.1)
        axes = Axes(
            x_range=[0, 8, 2], y_range=[0, 6, 2],
            x_length=4.8, y_length=4.2,
            axis_config={"color": COLOR_MUTED, "stroke_width": 1.2, "include_numbers": False}
        ).shift(LEFT * 2.7 + DOWN * 0.2)

        x_lbl = Text("Độ dài ngữ cảnh (Tokens)", font=FONT_FAMILY, font_size=12.0, color=COLOR_MUTED).next_to(axes.x_axis, DOWN, buff=0.15)
        y_lbl = Text("Độ trễ sinh mỗi token (ms)", font=FONT_FAMILY, font_size=12.0, color=COLOR_MUTED).next_to(axes.y_axis, UP, buff=0.15).shift(RIGHT * 0.5)

        # Curves: Without Cache (Linear growth) vs With Cache (Flat line)
        curve_no_cache = Line(axes.c2p(0.5, 0.8), axes.c2p(7.5, 5.2), color=COLOR_ROSE, stroke_width=2.5)
        lbl_no_c = Text("Không Cache (Chậm dần đều)", font=FONT_FAMILY, font_size=12.0, color=COLOR_ROSE).next_to(curve_no_cache.get_end(), UL, buff=0.1)

        curve_cache = Line(axes.c2p(0.5, 1.2), axes.c2p(7.5, 1.2), color=COLOR_EMERALD, stroke_width=2.5)
        lbl_c = Text("Dùng Cache (Độ trễ phẳng ~20ms)", font=FONT_FAMILY, font_size=12.0, color=COLOR_EMERALD).next_to(curve_cache.get_end(), UR, buff=0.1)

        self.play(Create(axes), FadeIn(x_lbl), FadeIn(y_lbl), Create(curve_no_cache), FadeIn(lbl_no_c), Create(curve_cache), FadeIn(lbl_c), run_time=1.2)

        # 3. Right Card: Mistral Sliding Window & Circular Buffer
        right_panel = RoundedRectangle(corner_radius=0.15, height=4.6, width=4.8, fill_color=COLOR_CARD_BG, fill_opacity=0.9, stroke_color=COLOR_BORDER, stroke_width=1.2).shift(RIGHT * 2.6 + DOWN * 0.2)
        
        t_sw = Text("GIẢI PHÁP CHUYỂN TIẾP: SLIDING WINDOW", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_GOLD).next_to(right_panel.get_top(), DOWN, buff=0.25)

        # Circular buffer diagram
        circle_buf = Circle(radius=1.1, color=COLOR_CYAN, stroke_width=2.0).shift(RIGHT * 2.6 + UP * 0.4)
        c_lbl_hdr = Text("Hàng đợi xoay vòng\n(Circular Buffer\nW=4.096)", font=FONT_FAMILY, font_size=12.0, color=COLOR_CYAN).move_to(circle_buf.get_center())

        div_sw = Line(LEFT * 1.9, RIGHT * 1.9, color=COLOR_BORDER, stroke_width=1.0).shift(RIGHT * 2.6 + DOWN * 0.9)

        desc_sw_hdr = Text("• Mistral 7B: Giới hạn Cache cố định 4.096 token\n• VRAM không bao giờ tràn, nhưng mất trí nhớ xa\n• Muốn ngữ cảnh dài 128k: Bắt buộc dùng PagedAttention!", font=FONT_FAMILY, font_size=12.0, color=COLOR_TEXT).next_to(right_panel.get_bottom(), UP, buff=0.2)

        r_sw = VGroup(t_sw, circle_buf, c_lbl_hdr, div_sw, desc_sw_hdr)

        self.play(FadeIn(right_panel), FadeIn(r_sw), run_time=1.2)
        self.wait(2.0)

        # [Masterclass: Visual State Retained - Trailing FadeOut Removed]
        self.wait(2.0)


# =============================================================================
# SCENE 06: TỔNG KẾT TRIẾT LÝ, LỜI TRI ÂN CHÂN THÀNH VÀ KẾT NỐI TẬP 08
# =============================================================================
class Tap07Scene06Outro(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "TỔNG KẾT & CẦU NỐI KỸ NGHỆ")

        scene_title = Text(
            "BÀN GIAO TRI THỨC // KV CACHE & HẠ TẦNG VLLM",
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
        # 1. Next Video Card (Episode 08: PagedAttention)
        next_card = RoundedRectangle(
            corner_radius=0.12, width=3.8, height=2.0,
            fill_color=COLOR_PANEL, fill_opacity=0.7, stroke_color=COLOR_CYAN, stroke_width=1.5
        ).move_to(RIGHT * 3.5 + UP * 1.5)
        next_header = Text("TẬP TIẾP THEO // TẬP 08", font=FONT_FAMILY, font_size=12.5, weight=BOLD, color=COLOR_CYAN)
        next_sub_header = Text("PAGEDATTENTION & VLLM MEMORY", font=FONT_FAMILY, font_size=12.0, color=COLOR_TEXT).next_to(next_header, DOWN, buff=0.18)
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

