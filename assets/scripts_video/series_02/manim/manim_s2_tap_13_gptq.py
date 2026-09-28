#!/usr/bin/env python3
"""
Manim 2K QHD Master Scenes — GPTQ & AWQ // Kỹ Thuật Lượng Tử Hóa Nâng Cao Bảo Vệ Trọng Số Cốt Lõi
Resolution: 2560x1440 @ 60fps | Theme: Neo-Noir Obsidian (#0c0d12)
Standards: Pure mathematical visualization, zero mascots, safe padding (|x| <= 5.2, |y| <= 3.2),
           top-right brand badge, continuous visual transitions.
"""

from manim import *
import numpy as np
import math
from pathlib import Path

# Neo-Noir Theme Constants
COLOR_BG = "#0c0d12"
COLOR_PANEL = "#141824"
COLOR_CYAN = "#00e5ff"
COLOR_GOLD = "#ffb300"
COLOR_ROSE = "#ff2a6d"
COLOR_GREEN = "#00e676"
COLOR_TEXT = "#e2e8f0"
COLOR_MUTED = "#64748b"


def add_zenpham_brand(scene, ep_title="GPTQ VS AWQ"):
    header_text = Text(
        f"ZENPHAM // TÔI LÀM VIỆC — {ep_title}",
        font="Noto Sans",
        font_size=15,
        weight=BOLD,
        color=COLOR_TEXT
    )
    box_w = max(8.0, header_text.width + 0.8)
    header_box = RoundedRectangle(
        corner_radius=0.12,
        height=0.55,
        width=box_w,
        fill_color=COLOR_PANEL,
        fill_opacity=0.9,
        stroke_color=COLOR_CYAN,
        stroke_width=1.2
    )
    header_box.to_edge(UP, buff=0.35)
    header_text.move_to(header_box.get_center())
    scene.add(header_box, header_text)


# ==============================================================================
# SCENE 1: COLD OPEN — THE 4-BIT COMPRESSION BARRIER (00:00 - 01:25)
# ==============================================================================
class Tap13Scene01ColdOpen(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "BỨC TƯỜNG NÉN 4-BIT & SỰ SỤP ĐỔ CỦA RTN")

        # 1. Main Title
        title_top = Text("BỨC TƯỜNG NÉN 4-BIT & SỰ SỤP ĐỔ CỦA RTN", font="Noto Sans", font_size=22, weight=BOLD, color=COLOR_GOLD)
        title_sub = Text("KHI LÀM TRÒN SỐ HỌC NGÂY THƠ BIẾN SIÊU MÔ HÌNH THÀNH KẺ MẤT TRÍ", font="Noto Sans", font_size=12, color=COLOR_TEXT)
        title_grp = VGroup(title_top, title_sub).arrange(DOWN, buff=0.15).to_edge(UP, buff=1.0)
        self.play(FadeIn(title_grp, shift=DOWN*0.3), run_time=0.9)

        # 2. Left Box: FP16 Standard vs Right Box: Naive RTN 4-Bit
        fp16_box = RoundedRectangle(corner_radius=0.15, height=3.2, width=4.2, fill_color=COLOR_PANEL, fill_opacity=0.85, stroke_color=COLOR_CYAN, stroke_width=1.5).shift(LEFT * 2.8 + DOWN * 0.4)
        fp16_label = Text("CHUẨN FP16 (GỐC)", font="Noto Sans", font_size=14, weight=BOLD, color=COLOR_CYAN).next_to(fp16_box, UP, buff=0.12)
        fp16_stat1 = Text("LLaMA-3-70B: 140 GB VRAM", font="Noto Sans", font_size=12, color=COLOR_TEXT).move_to(fp16_box.get_center() + UP * 0.8)
        fp16_stat2 = Text("Yêu cầu: 2x GPU A100 (80GB)", font="Noto Sans", font_size=12, color=COLOR_MUTED).move_to(fp16_box.get_center() + UP * 0.3)
        fp16_stat3 = Text("Perplexity: 5.40 (Chuẩn SOTA)", font="Noto Sans", font_size=12, weight=BOLD, color=COLOR_GREEN).move_to(fp16_box.get_center() + DOWN * 0.3)
        fp16_stat4 = Text("Trí tuệ ngôn ngữ: Hoàn hảo", font="Noto Sans", font_size=12.0, color=COLOR_TEXT).move_to(fp16_box.get_center() + DOWN * 0.8)
        fp16_grp = VGroup(fp16_box, fp16_label, fp16_stat1, fp16_stat2, fp16_stat3, fp16_stat4)

        rtn_box = RoundedRectangle(corner_radius=0.15, height=3.2, width=4.2, fill_color=COLOR_PANEL, fill_opacity=0.85, stroke_color=COLOR_ROSE, stroke_width=1.5).shift(RIGHT * 2.8 + DOWN * 0.4)
        rtn_label = Text("ROUND-TO-NEAREST 4-BIT", font="Noto Sans", font_size=14, weight=BOLD, color=COLOR_ROSE).next_to(rtn_box, UP, buff=0.12)
        rtn_stat1 = Text("Dung lượng: 35 GB VRAM (-75%)", font="Noto Sans", font_size=12, color=COLOR_TEXT).move_to(rtn_box.get_center() + UP * 0.8)
        rtn_stat2 = Text("Chạy trên: 1 Card GPU cá nhân", font="Noto Sans", font_size=12, color=COLOR_MUTED).move_to(rtn_box.get_center() + UP * 0.3)
        rtn_stat3 = Text("Perplexity: > 1,000 (Sụp đổ)", font="Noto Sans", font_size=12, weight=BOLD, color=COLOR_ROSE).move_to(rtn_box.get_center() + DOWN * 0.3)
        rtn_stat4 = Text("Hiện tượng: Lặp từ vô nghĩa", font="Noto Sans", font_size=12.0, color=COLOR_ROSE).move_to(rtn_box.get_center() + DOWN * 0.8)
        rtn_grp = VGroup(rtn_box, rtn_label, rtn_stat1, rtn_stat2, rtn_stat3, rtn_stat4)

        self.play(FadeIn(fp16_grp, shift=RIGHT*0.3), FadeIn(rtn_grp, shift=LEFT*0.3), run_time=1.2)

        # 3. Bottom Alert Box
        alert_box = RoundedRectangle(corner_radius=0.12, height=0.9, width=9.6, fill_color="#180e18", fill_opacity=0.95, stroke_color=COLOR_GOLD, stroke_width=1.5).shift(DOWN * 2.5)
        alert_hdr = Text("HỐ SÂU TỬ THẦN: LÀM SAO NÉN 4-BIT MÀ BẢO TOÀN TRÍ THÔNG MINH?", font="Noto Sans", font_size=13, weight=BOLD, color=COLOR_GOLD).move_to(alert_box.get_center())
        self.play(Create(alert_box), Write(alert_hdr), run_time=1.0)
        self.wait(1.5)


# ==============================================================================
# SCENE 2: MATHEMATICS — OPTIMAL BRAIN SURGEON & HESSIAN (01:25 - 02:55)
# ==============================================================================
class Tap13Scene02Architecture(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "TOÁN HỌC OPTIMAL BRAIN SURGEON")

        # 1. Title
        title = Text("GIẢI PHẪU TOÁN HỌC: KHAI TRIỂN TAYLOR BẬC HAI", font="Noto Sans", font_size=20, weight=BOLD, color=COLOR_CYAN).to_edge(UP, buff=1.0)
        subtitle = Text("BÙ TRỪ SAI SỐ BẰNG MA TRẬN ĐẠO HÀM BẬC HAI HESSIAN", font="Noto Sans", font_size=12, color=COLOR_TEXT).next_to(title, DOWN, buff=0.12)
        self.play(FadeIn(title, shift=DOWN*0.2), FadeIn(subtitle), run_time=0.9)

        # 2. Formula Card: Taylor Expansion at Optimum
        f_box = RoundedRectangle(corner_radius=0.15, height=1.7, width=9.8, fill_color=COLOR_PANEL, fill_opacity=0.9, stroke_color=COLOR_GOLD, stroke_width=1.5).shift(UP * 0.8)
        f_tex = MathTex(
            r"L(w + \delta w) \approx L(w) + g^T \delta w + \frac{1}{2} \delta w^T H \delta w, \quad g = \nabla_w L = 0",
            font_size=32, color=COLOR_GOLD
        ).move_to(f_box.get_center() + UP * 0.25)
        f_hdr = Text("Tại điểm cực tiểu tối ưu: Gradient triệt tiêu. Độ cong bề mặt do Hessian H = 2 X X^T quyết định.", font="Noto Sans", font_size=12.0, color=COLOR_TEXT).move_to(f_box.get_center() + DOWN * 0.4)
        self.play(Create(f_box), Write(f_tex), FadeIn(f_hdr), run_time=1.3)

        # 3. Error Compensation Formula
        comp_box = RoundedRectangle(corner_radius=0.15, height=2.3, width=9.8, fill_color=COLOR_PANEL, fill_opacity=0.9, stroke_color=COLOR_GREEN, stroke_width=1.5).shift(DOWN * 1.5)
        comp_title = Text("CÔNG THỨC BÙ TRỪ SAI SỐ CỦA OPTIMAL BRAIN SURGEON (OBS):", font="Noto Sans", font_size=12, weight=BOLD, color=COLOR_GREEN).move_to(comp_box.get_center() + UP * 0.75)
        comp_tex = MathTex(
            r"\delta w = - \frac{w_i - \text{quant}(w_i)}{[H^{-1}]_{ii}} \cdot H^{-1}_{:, i}",
            font_size=32, color=COLOR_GREEN
        ).move_to(comp_box.get_center() + UP * 0.1)
        comp_hdr = Text("Lệch một trọng số -> Tự động xoay các trọng số chưa nén để giữ nguyên đầu ra mạng nơ-ron!", font="Noto Sans", font_size=12.0, color=COLOR_TEXT).move_to(comp_box.get_center() + DOWN * 0.65)
        self.play(Create(comp_box), FadeIn(comp_title), Write(comp_tex), FadeIn(comp_hdr), run_time=1.4)
        self.wait(1.5)


# ==============================================================================
# SCENE 3: MATHEMATICS — GPTQ: CHOLESKY & LAZY BATCH UPDATES (02:55 - 04:25)
# ==============================================================================
class Tap13Scene03Mathematics(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "ĐỘT PHÁ CỦA THUẬT TOÁN GPTQ")

        # 1. Header
        title = Text("CHOLESKY INVERSION & LAZY BATCH UPDATES", font="Noto Sans", font_size=20, weight=BOLD, color=COLOR_GOLD).to_edge(UP, buff=1.0)
        subtitle = Text("GIẢM THỜI GIAN NÉN TỪ HÀNG THÁNG XUỐNG 4 GIỜ TRÊN 1 GPU", font="Noto Sans", font_size=12, color=COLOR_TEXT).next_to(title, DOWN, buff=0.12)
        self.play(FadeIn(title, shift=DOWN*0.2), FadeIn(subtitle), run_time=0.9)

        # 2. Left vs Right comparison
        left_box = RoundedRectangle(corner_radius=0.15, height=3.0, width=4.6, fill_color=COLOR_PANEL, fill_opacity=0.85, stroke_color=COLOR_ROSE, stroke_width=1.5).shift(LEFT * 2.7 + DOWN * 0.4)
        l_title = Text("THÁCH THỨC OBS CỔ ĐIỂN", font="Noto Sans", font_size=13, weight=BOLD, color=COLOR_ROSE).next_to(left_box, UP, buff=0.1)
        l_pt1 = Text("• Ma trận Hessian 4096 x 4096", font="Noto Sans", font_size=12.0, color=COLOR_TEXT).move_to(left_box.get_center() + UP * 0.8)
        l_pt2 = Text("• Nghịch đảo từng phần tử: O(d^3)", font="Noto Sans", font_size=12.0, color=COLOR_MUTED).move_to(left_box.get_center() + UP * 0.25)
        l_pt3 = Text("• Thời gian nén 70B: ~45 ngày", font="Noto Sans", font_size=12.0, weight=BOLD, color=COLOR_ROSE).move_to(left_box.get_center() + DOWN * 0.3)
        l_pt4 = Text("• Bất khả thi trong thực tế", font="Noto Sans", font_size=12.0, color=COLOR_ROSE).move_to(left_box.get_center() + DOWN * 0.8)
        l_grp = VGroup(left_box, l_title, l_pt1, l_pt2, l_pt3, l_pt4)

        right_box = RoundedRectangle(corner_radius=0.15, height=3.0, width=4.6, fill_color=COLOR_PANEL, fill_opacity=0.85, stroke_color=COLOR_CYAN, stroke_width=1.5).shift(RIGHT * 2.7 + DOWN * 0.4)
        r_title = Text("ĐỘT PHÁ GPTQ (FRANTAR 2022)", font="Noto Sans", font_size=13, weight=BOLD, color=COLOR_CYAN).next_to(right_box, UP, buff=0.1)
        r_pt1 = Text("• Phân rã Cholesky H^-1 đúng 1 lần", font="Noto Sans", font_size=12.0, color=COLOR_TEXT).move_to(right_box.get_center() + UP * 0.8)
        r_pt2 = Text("• Gom khối 128 cột (Block Updates)", font="Noto Sans", font_size=12.0, color=COLOR_MUTED).move_to(right_box.get_center() + UP * 0.25)
        r_pt3 = Text("• Cập nhật lười bằng GEMM trên SRAM", font="Noto Sans", font_size=12.0, weight=BOLD, color=COLOR_GREEN).move_to(right_box.get_center() + DOWN * 0.3)
        r_pt4 = Text("• Hoàn thành nén 70B trong 4 giờ", font="Noto Sans", font_size=12.0, color=COLOR_CYAN).move_to(right_box.get_center() + DOWN * 0.8)
        r_grp = VGroup(right_box, r_title, r_pt1, r_pt2, r_pt3, r_pt4)

        self.play(FadeIn(l_grp, shift=RIGHT*0.3), FadeIn(r_grp, shift=LEFT*0.3), run_time=1.2)

        # 3. Bottom Badge
        b_badge = RoundedRectangle(corner_radius=0.12, height=0.7, width=9.6, fill_color="#0e1e24", fill_opacity=0.9, stroke_color=COLOR_CYAN, stroke_width=1.2).shift(DOWN * 2.4)
        b_hdr = Text("KẾT HỢP ĐẠI SỐ TUYẾN TÍNH SÂU SẮC VỚI KỸ NGHỆ PHẦN CỨNG GPU HIỆN ĐẠI", font="Noto Sans", font_size=12, weight=BOLD, color=COLOR_CYAN).move_to(b_badge.get_center())
        self.play(Create(b_badge), FadeIn(b_hdr), run_time=0.9)
        self.wait(1.5)


# ==============================================================================
# SCENE 4: ARCHITECTURE — AWQ: ACTIVATION-AWARE QUANTIZATION (04:25 - 05:55)
# ==============================================================================
class Tap13Scene04Telemetry(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "AWQ & KÊNH KÍCH HOẠT NHẠY CẢM")

        # 1. Title
        title = Text("BẢO VỆ 1% TRỌNG SỐ CỐT LÕI (MIT SONG HAN)", font="Noto Sans", font_size=20, weight=BOLD, color=COLOR_GREEN).to_edge(UP, buff=1.0)
        subtitle = Text("BIẾN ĐỔI TỶ LỆ CÂN BẰNG: KHÔNG TỐN THÊM MỘT BYTE BỘ NHỚ", font="Noto Sans", font_size=12, color=COLOR_TEXT).next_to(title, DOWN, buff=0.12)
        self.play(FadeIn(title, shift=DOWN*0.2), FadeIn(subtitle), run_time=0.9)

        # 2. Key Discovery Card
        card1 = RoundedRectangle(corner_radius=0.15, height=1.7, width=9.8, fill_color=COLOR_PANEL, fill_opacity=0.9, stroke_color=COLOR_GOLD, stroke_width=1.5).shift(UP * 0.8)
        c1_title = Text("PHÁT HIỆN ĐỘT PHÁ TẠI MIT: KHÔNG PHẢI MỌI TRỌNG SỐ ĐỀU QUAN TRỌNG NHƯ NHAU", font="Noto Sans", font_size=12, weight=BOLD, color=COLOR_GOLD).move_to(card1.get_center() + UP * 0.45)
        c1_hdr1 = Text("• Trọng số chỉ sống còn khi nhân với các kênh kích hoạt biên độ lớn (|X| >= 6.0).", font="Noto Sans", font_size=12.0, color=COLOR_TEXT).move_to(card1.get_center())
        c1_hdr2 = Text("• Nhóm 1% trọng số này nắm giữ 99% trí thông minh và khả năng suy luận của mô hình.", font="Noto Sans", font_size=12.0, color=COLOR_MUTED).move_to(card1.get_center() + DOWN * 0.45)
        self.play(Create(card1), FadeIn(c1_title), FadeIn(c1_hdr1), FadeIn(c1_hdr2), run_time=1.2)

        # 3. Invariant Scaling Formula Card
        card2 = RoundedRectangle(corner_radius=0.15, height=2.2, width=9.8, fill_color=COLOR_PANEL, fill_opacity=0.9, stroke_color=COLOR_CYAN, stroke_width=1.5).shift(DOWN * 1.5)
        c2_title = Text("CƠ CHẾ BẢO VỆ BẰNG HỆ SỐ TỶ LỆ CÂN BẰNG (PER-CHANNEL SCALING):", font="Noto Sans", font_size=12, weight=BOLD, color=COLOR_CYAN).move_to(card2.get_center() + UP * 0.7)
        c2_tex = MathTex(
            r"W' = W \cdot s, \quad X' = X / s \implies X' W' = (X / s)(W \cdot s) = X W",
            font_size=32, color=COLOR_CYAN
        ).move_to(card2.get_center() + UP * 0.1)
        c2_hdr = Text("Biên độ trọng số nhạy cảm được khuếch đại -> Sai số lượng tử giảm s lần mà không đổi đầu ra!", font="Noto Sans", font_size=12.0, color=COLOR_GREEN).move_to(card2.get_center() + DOWN * 0.6)
        self.play(Create(card2), FadeIn(c2_title), Write(c2_tex), FadeIn(c2_hdr), run_time=1.3)
        self.wait(1.5)


# ==============================================================================
# SCENE 5: LAB EXPERIMENT — HARDWARE BENCHMARK ON VLLM (05:55 - 07:25)
# ==============================================================================
class Tap13Scene05LabExperiment(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "HIỆU NĂNG THỰC TẾ TRÊN VLLM")

        # 1. Header
        title = Text("BENCHMARK THỰC TẾ: THÔNG LƯỢNG & BỘ NHỚ VRAM", font="Noto Sans", font_size=20, weight=BOLD, color=COLOR_CYAN).to_edge(UP, buff=1.0)
        subtitle = Text("SO SÁNH LLaMA-3-70B GIỮA FP16, GPTQ 4-BIT VÀ AWQ 4-BIT TRÊN VLLM", font="Noto Sans", font_size=12, color=COLOR_TEXT).next_to(title, DOWN, buff=0.12)
        self.play(FadeIn(title, shift=DOWN*0.2), FadeIn(subtitle), run_time=0.9)

        # 2. Benchmark Table (3 Cards)
        cards_data = [
            ("FP16 (CHUẨN GỐC)", "140 GB VRAM", "22.4 tps", "5.40", COLOR_MUTED, LEFT * 3.4),
            ("GPTQ (INT4)", "35 GB (-75%)", "58.6 tps (2.6X)", "5.62", COLOR_ROSE, ORIGIN),
            ("AWQ (INT4)", "35 GB (-75%)", "68.2 tps (3.0X)", "5.49", COLOR_GREEN, RIGHT * 3.4),
        ]
        cards_grp = VGroup()
        for name, vram, tps, ppl, col, pos in cards_data:
            c_box = RoundedRectangle(corner_radius=0.15, height=3.0, width=3.2, fill_color=COLOR_PANEL, fill_opacity=0.9, stroke_color=col, stroke_width=1.8).shift(pos + DOWN * 0.4)
            c_name = Text(name, font="Noto Sans", font_size=13, weight=BOLD, color=col).move_to(c_box.get_center() + UP * 1.0)
            c_vram = Text(f"VRAM: {vram}", font="Noto Sans", font_size=12.0, color=COLOR_TEXT).move_to(c_box.get_center() + UP * 0.4)
            c_tps = Text(f"Tốc độ: {tps}", font="Noto Sans", font_size=12.0, weight=BOLD, color=COLOR_GOLD).move_to(c_box.get_center() + DOWN * 0.1)
            c_ppl = Text(f"Perplexity: {ppl}", font="Noto Sans", font_size=12.0, color=COLOR_TEXT).move_to(c_box.get_center() + DOWN * 0.6)
            c_eval = Text("Logic: " + ("Tối ưu" if "AWQ" in name else ("SOTA" if "FP16" in name else "Khá")), font="Noto Sans", font_size=12.0, color=col).move_to(c_box.get_center() + DOWN * 1.0)
            cards_grp.add(VGroup(c_box, c_name, c_vram, c_tps, c_ppl, c_eval))

        self.play(LaggedStart(*[FadeIn(c, shift=UP*0.3) for c in cards_grp], lag_ratio=0.2), run_time=1.2)

        # 3. Kernel Optimization Note
        k_box = RoundedRectangle(corner_radius=0.12, height=0.75, width=9.8, fill_color="#0e1e24", fill_opacity=0.95, stroke_color=COLOR_GREEN, stroke_width=1.2).shift(DOWN * 2.45)
        k_hdr = Text("KERNEL AWQ GEMM: GIẢI NÉN TRỰC TIẾP TRÊN THANH GHI GPU TĂNG GẤP 3 TỐC ĐỘ PHỤC VỤ", font="Noto Sans", font_size=12.0, weight=BOLD, color=COLOR_GREEN).move_to(k_box.get_center())
        self.play(Create(k_box), FadeIn(k_hdr), run_time=0.9)
        self.wait(1.5)


# ==============================================================================
# SCENE 6: OUTRO — 5x5 MOSAIC & EPISODE 14 TEASER (07:25 - 08:35)
# ==============================================================================
class Tap13Scene06Outro(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "TỔNG KẾT & CẦU NỐI KỸ NGHỆ")

        scene_title = Text(
            "BÀN GIAO TRI THỨC // GPTQ & AWQ",
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
        # 1. Next Video Card (Episode 14: LoRA & QLoRA)
        next_card = RoundedRectangle(
            corner_radius=0.12, width=3.8, height=2.0,
            fill_color=COLOR_PANEL, fill_opacity=0.7, stroke_color=COLOR_CYAN, stroke_width=1.5
        ).move_to(RIGHT * 3.5 + UP * 1.5)
        next_header = Text("TẬP TIẾP THEO // TẬP 14", font="Noto Sans", font_size=12.5, weight=BOLD, color=COLOR_CYAN)
        next_sub_header = Text("LORA & QLORA: TINH CHỈNH SIÊU NHẸ", font="Noto Sans", font_size=12.0, color=COLOR_TEXT).next_to(next_header, DOWN, buff=0.18)
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
