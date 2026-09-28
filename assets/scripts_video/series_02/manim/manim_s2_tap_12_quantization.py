#!/usr/bin/env python3
"""
Manim 2K QHD Master Scenes — Lượng Tử Hóa INT8 & FP8 // Nén Trọng Số Mà Không Làm Mất Trí Tuệ
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


def add_zenpham_brand(scene, ep_title="QUANTIZATION INT8 & FP8"):
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
# SCENE 1: COLD OPEN — THE MEMORY WALL PARADOX (00:00 - 01:20)
# ==============================================================================
class Tap12Scene01ColdOpen(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "BỨC TƯỜNG BỘ NHỚ & LƯỢNG TỬ HÓA")

        # 1. Main Title
        title_top = Text("NGHỊCH LÝ BỨC TƯỜNG BỘ NHỚ", font="Noto Sans", font_size=24, weight=BOLD, color=COLOR_GOLD)
        title_sub = Text("KHI DI CHUYỂN DỮ LIỆU ĐẮT GẤP 100 LẦN TÍNH TOÁN SỐ HỌC", font="Noto Sans", font_size=13, color=COLOR_TEXT)
        title_grp = VGroup(title_top, title_sub).arrange(DOWN, buff=0.15).to_edge(UP, buff=1.0)
        self.play(FadeIn(title_grp, shift=DOWN*0.3), run_time=0.9)

        # 2. Left Box: HBM Memory Stick vs Right Box: SRAM Compute Engine
        hbm_box = RoundedRectangle(corner_radius=0.15, height=3.2, width=4.0, fill_color=COLOR_PANEL, fill_opacity=0.85, stroke_color=COLOR_ROSE, stroke_width=1.5).shift(LEFT * 3.0 + DOWN * 0.4)
        hbm_label = Text("HBM3 VRAM (140 GB)", font="Noto Sans", font_size=14, weight=BOLD, color=COLOR_ROSE).next_to(hbm_box, UP, buff=0.12)
        hbm_stat1 = Text("Trọng số FP16: 16-bit", font="Noto Sans", font_size=12, color=COLOR_TEXT).move_to(hbm_box.get_center() + UP * 0.7)
        hbm_stat2 = Text("Dung lượng: 140,000 MB", font="Noto Sans", font_size=12, color=COLOR_MUTED).move_to(hbm_box.get_center() + UP * 0.2)
        hbm_stat3 = Text("Băng thông: 3.35 TB/s (Nghẽn)", font="Noto Sans", font_size=12, weight=BOLD, color=COLOR_ROSE).move_to(hbm_box.get_center() + DOWN * 0.5)
        hbm_grp = VGroup(hbm_box, hbm_label, hbm_stat1, hbm_stat2, hbm_stat3)

        sram_box = RoundedRectangle(corner_radius=0.15, height=3.2, width=4.0, fill_color=COLOR_PANEL, fill_opacity=0.85, stroke_color=COLOR_CYAN, stroke_width=1.5).shift(RIGHT * 3.0 + DOWN * 0.4)
        sram_label = Text("SRAM ON-CHIP (50 MB)", font="Noto Sans", font_size=14, weight=BOLD, color=COLOR_CYAN).next_to(sram_box, UP, buff=0.12)
        sram_stat1 = Text("Tensor Core: 2,000 TFLOPS", font="Noto Sans", font_size=12, color=COLOR_TEXT).move_to(sram_box.get_center() + UP * 0.7)
        sram_stat2 = Text("Tốc độ: 33 TB/s nội bộ", font="Noto Sans", font_size=12, color=COLOR_MUTED).move_to(sram_box.get_center() + UP * 0.2)
        sram_stat3 = Text("Trạng thái: Đói dữ liệu (Starving)", font="Noto Sans", font_size=12, weight=BOLD, color=COLOR_GOLD).move_to(sram_box.get_center() + DOWN * 0.5)
        sram_grp = VGroup(sram_box, sram_label, sram_stat1, sram_stat2, sram_stat3)

        self.play(Create(hbm_box), FadeIn(hbm_label), FadeIn(hbm_stat1), FadeIn(hbm_stat2), FadeIn(hbm_stat3),
                  Create(sram_box), FadeIn(sram_label), FadeIn(sram_stat1), FadeIn(sram_stat2), FadeIn(sram_stat3), run_time=1.2)

        # 3. Data Flow Pipe with amber pulsing dots
        pipe_arrow = Arrow(hbm_box.get_right(), sram_box.get_left(), buff=0.2, stroke_width=4, color=COLOR_GOLD)
        pipe_label = Text("PCIe / NVLink Bus (64 GB/s)", font="Noto Sans", font_size=12, color=COLOR_GOLD).next_to(pipe_arrow, UP, buff=0.1)
        self.play(GrowArrow(pipe_arrow), FadeIn(pipe_label), run_time=0.8)

        # 4. Solution Banner: Compression 16-bit to 8-bit
        sol_banner = RoundedRectangle(corner_radius=0.12, height=0.9, width=9.2, fill_color="#101826", fill_opacity=0.95, stroke_color=COLOR_GREEN, stroke_width=1.5).shift(DOWN * 2.6)
        sol_hdr = Text("GIẢI PHÁP LƯỢNG TỬ HÓA: 16-BIT FP16 (140GB)  →  8-BIT INT8/FP8 (70GB)", font="Noto Sans", font_size=13, weight=BOLD, color=COLOR_GREEN)
        sol_sub_hdr = Text("Vừa vặn trên 1x GPU 80GB đơn lẻ // Cắt giảm 50% băng thông truyền dẫn", font="Noto Sans", font_size=12.0, color=COLOR_TEXT)
        sol_grp = VGroup(sol_hdr, sol_sub_hdr).arrange(DOWN, buff=0.08).move_to(sol_banner.get_center())

        self.play(Create(sol_banner), Write(sol_grp), run_time=1.0)
        self.wait(2.0)


# ==============================================================================
# SCENE 2: ARCHITECTURE & INTUITION — CONTINUOUS TO DISCRETE (01:20 - 02:45)
# ==============================================================================
class Tap12Scene02Architecture(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "BẢN CHẤT HÌNH HỌC LƯỢNG TỬ HÓA")

        title_top = Text("ÁNH XẠ MIỀN LIÊN TỤC VÀO LƯỚI SỐ NGUYÊN 8-BIT", font="Noto Sans", font_size=20, weight=BOLD, color=COLOR_GOLD)
        title_sub = Text("TỪ KHÔNG GIAN THỰC R VÔ HẠN SANG 256 MỨC NGUYÊN [-128, 127]", font="Noto Sans", font_size=13, color=COLOR_TEXT)
        title_grp = VGroup(title_top, title_sub).arrange(DOWN, buff=0.15).to_edge(UP, buff=1.0)
        self.play(FadeIn(title_grp, shift=DOWN*0.3), run_time=0.8)

        # 1. Number Line for Real Numbers
        num_line_real = NumberLine(x_range=[-2.0, 2.0, 0.5], length=8.8, color=COLOR_MUTED, include_numbers=True, font_size=14).shift(UP * 0.8)
        real_label = Text("Miền số thực liên tục x in R (FP16)", font="Noto Sans", font_size=13, color=COLOR_CYAN).next_to(num_line_real, UP, buff=0.2)
        self.play(Create(num_line_real), FadeIn(real_label), run_time=1.0)

        # 2. Number Line for INT8 Grid
        num_line_int8 = NumberLine(x_range=[-128, 128, 32], length=8.8, color=COLOR_GOLD, include_numbers=True, font_size=14).shift(DOWN * 1.0)
        int8_label = Text("Lưới số nguyên rời rạc q in [-128, 127] (INT8)", font="Noto Sans", font_size=13, color=COLOR_GOLD).next_to(num_line_int8, UP, buff=0.2)
        self.play(Create(num_line_int8), FadeIn(int8_label), run_time=1.0)

        # 3. Scale Factor S mapping arrows
        arrow_left = Arrow(num_line_real.n2p(-1.5), num_line_int8.n2p(-128), color=COLOR_ROSE, stroke_width=2.5, buff=0.1)
        arrow_zero = Arrow(num_line_real.n2p(0.0), num_line_int8.n2p(0), color=COLOR_GREEN, stroke_width=2.5, buff=0.1)
        arrow_right = Arrow(num_line_real.n2p(1.5), num_line_int8.n2p(127), color=COLOR_ROSE, stroke_width=2.5, buff=0.1)
        scale_tag = Text("Hệ số co giãn Scale: S = max(|X|) / 127", font="Noto Sans", font_size=13, weight=BOLD, color=COLOR_CYAN).move_to(DOWN * 0.1)

        self.play(GrowArrow(arrow_left), GrowArrow(arrow_zero), GrowArrow(arrow_right), FadeIn(scale_tag), run_time=1.2)

        # 4. Symmetric vs Asymmetric Comparison Card
        sym_box = RoundedRectangle(corner_radius=0.12, height=1.0, width=8.8, fill_color=COLOR_PANEL, fill_opacity=0.9, stroke_color=COLOR_CYAN, stroke_width=1.5).shift(DOWN * 2.5)
        sym_hdr1 = Text("LƯỢNG TỬ HÓA ĐỐI XỨNG (SYMMETRIC): Gán cứng Zero-point Z = 0", font="Noto Sans", font_size=12, weight=BOLD, color=COLOR_CYAN)
        sym_hdr2 = Text("Triệt tiêu toàn bộ số hạng chéo trong phép nhân ma trận GEMM -> Tăng tốc tối đa", font="Noto Sans", font_size=12.0, color=COLOR_TEXT)
        sym_content = VGroup(sym_hdr1, sym_hdr2).arrange(DOWN, buff=0.08).move_to(sym_box.get_center())

        self.play(Create(sym_box), Write(sym_content), run_time=1.0)
        self.wait(2.0)


# ==============================================================================
# SCENE 3: MATHEMATICS — THE OUTLIER PARADOX IN LLM.INT8() (02:45 - 04:15)
# ==============================================================================
class Tap12Scene03Mathematics(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "TOÁN HỌC & CẠM BẪY PHẦN TỬ NGOẠI LỆ")

        title_top = Text("TOÁN HỌC ĐỊNH LƯỢNG & GIẢI PHÁP LLM.INT8()", font="Noto Sans", font_size=20, weight=BOLD, color=COLOR_GOLD)
        title_sub = Text("CƠ CHẾ PHÂN TÁCH HỖN HỢP ĐỘ CHÍNH XÁC (MIXED-PRECISION DECOMPOSITION)", font="Noto Sans", font_size=13, color=COLOR_TEXT)
        title_grp = VGroup(title_top, title_sub).arrange(DOWN, buff=0.15).to_edge(UP, buff=1.0)
        self.play(FadeIn(title_grp, shift=DOWN*0.3), run_time=0.8)

        # 1. Main Formulas Card
        form_box = RoundedRectangle(corner_radius=0.15, height=1.6, width=9.2, fill_color=COLOR_PANEL, fill_opacity=0.9, stroke_color=COLOR_CYAN, stroke_width=1.5).shift(UP * 1.1)
        f1 = MathTex(r"X_{\text{quant}} = \text{clip}\left(\left\lfloor \frac{X}{S} \right\rceil, -128, 127\right)", font_size=26, color=COLOR_CYAN)
        f2 = MathTex(r"\hat{X} = S \times X_{\text{quant}}, \quad S = \frac{\max(|X|)}{127}", font_size=26, color=COLOR_GOLD)
        f_grp = VGroup(f1, f2).arrange(DOWN, buff=0.2).move_to(form_box.get_center())
        self.play(Create(form_box), Write(f_grp), run_time=1.2)

        # 2. Left: The Outlier Explosion Diagram
        out_box = RoundedRectangle(corner_radius=0.15, height=2.6, width=4.4, fill_color=COLOR_PANEL, fill_opacity=0.85, stroke_color=COLOR_ROSE, stroke_width=1.5).shift(LEFT * 2.5 + DOWN * 1.3)
        out_title = Text("BÙNG NỔ PHẦN TỬ NGOẠI LỆ (> 6.7B)", font="Noto Sans", font_size=12, weight=BOLD, color=COLOR_ROSE).next_to(out_box, UP, buff=0.1)
        out_text1 = Text("0.1% số chiều có độ lớn gấp 20x", font="Noto Sans", font_size=12.0, color=COLOR_TEXT).move_to(out_box.get_center() + UP * 0.5)
        out_text2 = Text("Scale S bị kéo giãn quá lớn", font="Noto Sans", font_size=12.0, color=COLOR_ROSE).move_to(out_box.get_center())
        out_text3 = Text("-> 99.9% giá trị bị làm tròn về 0", font="Noto Sans", font_size=12.0, weight=BOLD, color=COLOR_MUTED).move_to(out_box.get_center() + DOWN * 0.5)
        out_grp = VGroup(out_box, out_title, out_text1, out_text2, out_text3)

        # 3. Right: LLM.int8() Mixed Precision Decomposition
        dec_box = RoundedRectangle(corner_radius=0.15, height=2.6, width=4.4, fill_color=COLOR_PANEL, fill_opacity=0.85, stroke_color=COLOR_GREEN, stroke_width=1.5).shift(RIGHT * 2.5 + DOWN * 1.3)
        dec_title = Text("CƠ CHẾ PHÂN TÁCH LLM.INT8()", font="Noto Sans", font_size=12, weight=BOLD, color=COLOR_GREEN).next_to(dec_box, UP, buff=0.1)
        dec_text1 = Text("99.9% Chiều thường -> INT8 MatMul", font="Noto Sans", font_size=12.0, color=COLOR_CYAN).move_to(dec_box.get_center() + UP * 0.5)
        dec_text2 = Text("0.1% Chiều ngoại lệ -> FP16 MatMul", font="Noto Sans", font_size=12.0, color=COLOR_GOLD).move_to(dec_box.get_center())
        dec_text3 = Text("Tổng hợp: Y = S_X S_W (X_q W_q) + X_fp W_fp", font="Noto Sans", font_size=12.0, weight=BOLD, color=COLOR_GREEN).move_to(dec_box.get_center() + DOWN * 0.5)
        dec_grp = VGroup(dec_box, dec_title, dec_text1, dec_text2, dec_text3)

        self.play(Create(out_box), FadeIn(out_title), FadeIn(out_text1), FadeIn(out_text2), FadeIn(out_text3),
                  Create(dec_box), FadeIn(dec_title), FadeIn(dec_text1), FadeIn(dec_text2), FadeIn(dec_text3), run_time=1.4)
        self.wait(2.0)


# ==============================================================================
# SCENE 4: TELEMETRY — THE FP8 REVOLUTION (E4M3 VS E5M2) (04:15 - 05:40)
# ==============================================================================
class Tap12Scene04Telemetry(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "CUỘC CÁCH MẠNG SỐ THỰC FP8")

        title_top = Text("ĐỊNH DẠNG FP8: E4M3 VÀ E5M2 TRÊN HOPPER H100", font="Noto Sans", font_size=20, weight=BOLD, color=COLOR_GOLD)
        title_sub = Text("SỰ ĐÁNH ĐỔI GIỮA ĐỘ CHÍNH XÁC (PRECISION) VÀ MIỀN ĐỘNG (DYNAMIC RANGE)", font="Noto Sans", font_size=13, color=COLOR_TEXT)
        title_grp = VGroup(title_top, title_sub).arrange(DOWN, buff=0.15).to_edge(UP, buff=1.0)
        self.play(FadeIn(title_grp, shift=DOWN*0.3), run_time=0.8)

        # 1. Left: E4M3 Architecture Card
        e4m3_box = RoundedRectangle(corner_radius=0.15, height=3.6, width=4.3, fill_color=COLOR_PANEL, fill_opacity=0.85, stroke_color=COLOR_CYAN, stroke_width=1.5).shift(LEFT * 2.6 + DOWN * 0.6)
        e4m3_title = Text("FP8 — ĐỊNH DẠNG E4M3", font="Noto Sans", font_size=14, weight=BOLD, color=COLOR_CYAN).next_to(e4m3_box, UP, buff=0.12)
        e4m3_bits = Text("1 Bit Dấu | 4 Bit Mũ | 3 Bit Trị", font="Noto Sans", font_size=12, color=COLOR_TEXT).move_to(e4m3_box.get_center() + UP * 1.1)
        e4m3_prop1 = Text("Độ chính xác cao // Sai số thấp", font="Noto Sans", font_size=12.0, color=COLOR_GREEN).move_to(e4m3_box.get_center() + UP * 0.5)
        e4m3_prop2 = Text("Giá trị cực đại: +/- 448", font="Noto Sans", font_size=12.0, color=COLOR_MUTED).move_to(e4m3_box.get_center())
        e4m3_prop3 = Text("ỨNG DỤNG CHỦ LỰC:", font="Noto Sans", font_size=12.0, weight=BOLD, color=COLOR_GOLD).move_to(e4m3_box.get_center() + DOWN * 0.5)
        e4m3_prop4 = Text("Inference Trọng Số & Activation", font="Noto Sans", font_size=12.0, weight=BOLD, color=COLOR_CYAN).move_to(e4m3_box.get_center() + DOWN * 0.9)
        e4m3_grp = VGroup(e4m3_box, e4m3_title, e4m3_bits, e4m3_prop1, e4m3_prop2, e4m3_prop3, e4m3_prop4)

        # 2. Right: E5M2 Architecture Card
        e5m2_box = RoundedRectangle(corner_radius=0.15, height=3.6, width=4.3, fill_color=COLOR_PANEL, fill_opacity=0.85, stroke_color=COLOR_ROSE, stroke_width=1.5).shift(RIGHT * 2.6 + DOWN * 0.6)
        e5m2_title = Text("FP8 — ĐỊNH DẠNG E5M2", font="Noto Sans", font_size=14, weight=BOLD, color=COLOR_ROSE).next_to(e5m2_box, UP, buff=0.12)
        e5m2_bits = Text("1 Bit Dấu | 5 Bit Mũ | 2 Bit Trị", font="Noto Sans", font_size=12, color=COLOR_TEXT).move_to(e5m2_box.get_center() + UP * 1.1)
        e5m2_prop1 = Text("Miền động khổng lồ // Chống tràn số", font="Noto Sans", font_size=12.0, color=COLOR_ROSE).move_to(e5m2_box.get_center() + UP * 0.5)
        e5m2_prop2 = Text("Giá trị cực đại: +/- 57,344", font="Noto Sans", font_size=12.0, color=COLOR_MUTED).move_to(e5m2_box.get_center())
        e5m2_prop3 = Text("ỨNG DỤNG CHỦ LỰC:", font="Noto Sans", font_size=12.0, weight=BOLD, color=COLOR_GOLD).move_to(e5m2_box.get_center() + DOWN * 0.5)
        e5m2_prop4 = Text("Gradients & Backward Pass", font="Noto Sans", font_size=12.0, weight=BOLD, color=COLOR_ROSE).move_to(e5m2_box.get_center() + DOWN * 0.9)
        e5m2_grp = VGroup(e5m2_box, e5m2_title, e5m2_bits, e5m2_prop1, e5m2_prop2, e5m2_prop3, e5m2_prop4)

        self.play(Create(e4m3_box), FadeIn(e4m3_title), FadeIn(e4m3_bits), FadeIn(e4m3_prop1), FadeIn(e4m3_prop2), FadeIn(e4m3_prop3), FadeIn(e4m3_prop4),
                  Create(e5m2_box), FadeIn(e5m2_title), FadeIn(e5m2_bits), FadeIn(e5m2_prop1), FadeIn(e5m2_prop2), FadeIn(e5m2_prop3), FadeIn(e5m2_prop4), run_time=1.5)
        self.wait(2.0)


# ==============================================================================
# SCENE 5: LAB EXPERIMENT — BENCHMARK & VRAM REDUCTION (05:40 - 07:05)
# ==============================================================================
class Tap12Scene05LabExperiment(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "ĐỐI CHIẾU THỰC ĐỊA & HIỆU NĂNG")

        title_top = Text("THỰC TẾ SẢN XUẤT: VRAM & TỐC ĐỘ SINH TOKEN", font="Noto Sans", font_size=20, weight=BOLD, color=COLOR_GOLD)
        title_sub = Text("BENCHMARK TRÊN CỤM GPU NVIDIA H100 80GB — MÔ HÌNH LLAMA-70B", font="Noto Sans", font_size=13, color=COLOR_TEXT)
        title_grp = VGroup(title_top, title_sub).arrange(DOWN, buff=0.15).to_edge(UP, buff=1.0)
        self.play(FadeIn(title_grp, shift=DOWN*0.3), run_time=0.8)

        # 3 Comparison Columns: FP16 vs INT8 vs FP8
        col_w, col_h = 2.6, 3.4
        c1_box = RoundedRectangle(corner_radius=0.12, height=col_h, width=col_w, fill_color=COLOR_PANEL, fill_opacity=0.85, stroke_color=COLOR_MUTED, stroke_width=1.5).shift(LEFT * 3.0 + DOWN * 0.5)
        c1_title = Text("GỐC: FP16", font="Noto Sans", font_size=13, weight=BOLD, color=COLOR_TEXT).next_to(c1_box, UP, buff=0.1)
        c1_vram = Text("140 GB VRAM", font="Noto Sans", font_size=13, weight=BOLD, color=COLOR_ROSE).move_to(c1_box.get_center() + UP * 0.9)
        c1_req = Text("Cần 2x H100 80GB", font="Noto Sans", font_size=12.0, color=COLOR_MUTED).move_to(c1_box.get_center() + UP * 0.3)
        c1_speed = Text("Tốc độ: 1.0x (Gốc)", font="Noto Sans", font_size=12.0, color=COLOR_TEXT).move_to(c1_box.get_center() + DOWN * 0.3)
        c1_ppl = Text("PPL: 3.12 (Chuẩn)", font="Noto Sans", font_size=12.0, color=COLOR_GREEN).move_to(c1_box.get_center() + DOWN * 0.9)
        c1_grp = VGroup(c1_box, c1_title, c1_vram, c1_req, c1_speed, c1_ppl)

        c2_box = RoundedRectangle(corner_radius=0.12, height=col_h, width=col_w, fill_color=COLOR_PANEL, fill_opacity=0.85, stroke_color=COLOR_CYAN, stroke_width=1.5).shift(DOWN * 0.5)
        c2_title = Text("NÉN: INT8", font="Noto Sans", font_size=13, weight=BOLD, color=COLOR_CYAN).next_to(c2_box, UP, buff=0.1)
        c2_vram = Text("70 GB VRAM", font="Noto Sans", font_size=13, weight=BOLD, color=COLOR_CYAN).move_to(c2_box.get_center() + UP * 0.9)
        c2_req = Text("Vừa 1x H100 80GB", font="Noto Sans", font_size=12.0, color=COLOR_GREEN).move_to(c2_box.get_center() + UP * 0.3)
        c2_speed = Text("Tốc độ: 1.85x", font="Noto Sans", font_size=12.0, weight=BOLD, color=COLOR_GOLD).move_to(c2_box.get_center() + DOWN * 0.3)
        c2_ppl = Text("PPL: 3.14 (+0.02)", font="Noto Sans", font_size=12.0, color=COLOR_TEXT).move_to(c2_box.get_center() + DOWN * 0.9)
        c2_grp = VGroup(c2_box, c2_title, c2_vram, c2_req, c2_speed, c2_ppl)

        c3_box = RoundedRectangle(corner_radius=0.12, height=col_h, width=col_w, fill_color=COLOR_PANEL, fill_opacity=0.85, stroke_color=COLOR_GOLD, stroke_width=1.5).shift(RIGHT * 3.0 + DOWN * 0.5)
        c3_title = Text("TỐI ƯU: FP8", font="Noto Sans", font_size=13, weight=BOLD, color=COLOR_GOLD).next_to(c3_box, UP, buff=0.1)
        c3_vram = Text("70 GB VRAM", font="Noto Sans", font_size=13, weight=BOLD, color=COLOR_GOLD).move_to(c3_box.get_center() + UP * 0.9)
        c3_req = Text("Vừa 1x H100 80GB", font="Noto Sans", font_size=12.0, color=COLOR_GREEN).move_to(c3_box.get_center() + UP * 0.3)
        c3_speed = Text("Tốc độ: 2.20x", font="Noto Sans", font_size=12.0, weight=BOLD, color=COLOR_GREEN).move_to(c3_box.get_center() + DOWN * 0.3)
        c3_ppl = Text("PPL: 3.12 (Bảo toàn)", font="Noto Sans", font_size=12.0, color=COLOR_GREEN).move_to(c3_box.get_center() + DOWN * 0.9)
        c3_grp = VGroup(c3_box, c3_title, c3_vram, c3_req, c3_speed, c3_ppl)

        self.play(FadeIn(c1_grp), FadeIn(c2_grp), FadeIn(c3_grp), run_time=1.4)

        # Bottom Callout Banner
        bot_banner = RoundedRectangle(corner_radius=0.12, height=0.7, width=8.8, fill_color="#101826", fill_opacity=0.9, stroke_color=COLOR_GREEN, stroke_width=1.5).shift(DOWN * 2.7)
        bot_hdr = Text("KẾT LUẬN: GIẢM 50% CHI PHÍ HẠ TẦNG // TĂNG GẤP ĐÔI THÔNG LƯỢNG PHỤC VỤ", font="Noto Sans", font_size=12, weight=BOLD, color=COLOR_GREEN).move_to(bot_banner.get_center())
        self.play(Create(bot_banner), Write(bot_hdr), run_time=0.9)

        self.wait(2.0)


# ==============================================================================
# SCENE 6: OUTRO — 5x5 MOSAIC & EPISODE 13 TEASER (07:05 - 08:30)
# ==============================================================================
class Tap12Scene06Outro(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "TỔNG KẾT & CẦU NỐI KỸ NGHỆ")

        scene_title = Text(
            "BÀN GIAO TRI THỨC // LƯỢNG TỬ HÓA INT8 & FP8",
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
        # 1. Next Video Card (Episode 13: GPTQ & AWQ)
        next_card = RoundedRectangle(
            corner_radius=0.12, width=3.8, height=2.0,
            fill_color=COLOR_PANEL, fill_opacity=0.7, stroke_color=COLOR_CYAN, stroke_width=1.5
        ).move_to(RIGHT * 3.5 + UP * 1.5)
        next_header = Text("TẬP TIẾP THEO // TẬP 13", font="Noto Sans", font_size=12.5, weight=BOLD, color=COLOR_CYAN)
        next_sub_header = Text("GPTQ & AWQ: LƯỢNG TỬ HÓA LÕI", font="Noto Sans", font_size=12.0, color=COLOR_TEXT).next_to(next_header, DOWN, buff=0.18)
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
