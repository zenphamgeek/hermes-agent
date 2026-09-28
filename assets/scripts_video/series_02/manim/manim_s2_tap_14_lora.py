#!/usr/bin/env python3
"""
Manim 2K QHD Master Scenes — LoRA & QLoRA // Tinh Chỉnh Mô Hình Hàng Tỷ Tham Số Trên GPU Cá Nhân
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


def add_zenpham_brand(scene, ep_title="LORA & QLORA"):
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
# SCENE 1: COLD OPEN — FULL FINE-TUNING MEMORY WALL (00:00 - 01:25)
# ==============================================================================
class Tap14Scene01ColdOpen(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "BỨC TƯỜNG BỘ NHỚ HUẤN LUYỆN TOÀN PHẦN")

        # 1. Main Title
        title_top = Text("BỨC TƯỜNG BỘ NHỚ HUẤN LUYỆN TOÀN PHẦN", font="Noto Sans", font_size=22, weight=BOLD, color=COLOR_GOLD)
        title_sub = Text("TẠI SAO MÔ HÌNH 70B CẦN HƠN 1.1 TERABYTE VRAM TRONG FULL FINE-TUNING?", font="Noto Sans", font_size=12, color=COLOR_TEXT)
        title_grp = VGroup(title_top, title_sub).arrange(DOWN, buff=0.15).to_edge(UP, buff=1.0)
        self.play(FadeIn(title_grp, shift=DOWN*0.3), run_time=0.9)

        # 2. Left Box: Full Fine-Tuning Memory Breakdown
        full_box = RoundedRectangle(corner_radius=0.15, height=3.2, width=4.5, fill_color=COLOR_PANEL, fill_opacity=0.85, stroke_color=COLOR_ROSE, stroke_width=1.5).shift(LEFT * 2.8 + DOWN * 0.4)
        full_label = Text("FULL FINE-TUNING (70B MODEL)", font="Noto Sans", font_size=13, weight=BOLD, color=COLOR_ROSE).next_to(full_box, UP, buff=0.12)
        full_stat1 = Text("Trọng số gốc FP16: 140 GB", font="Noto Sans", font_size=12.0, color=COLOR_TEXT).move_to(full_box.get_center() + UP * 0.9)
        full_stat2 = Text("Gradients (FP16): 140 GB", font="Noto Sans", font_size=12.0, color=COLOR_TEXT).move_to(full_box.get_center() + UP * 0.4)
        full_stat3 = Text("AdamW States (FP32 m & v): 560 GB", font="Noto Sans", font_size=12.0, color=COLOR_ROSE).move_to(full_box.get_center() + DOWN * 0.1)
        full_stat4 = Text("Master Weights (FP32): 280 GB", font="Noto Sans", font_size=12.0, color=COLOR_MUTED).move_to(full_box.get_center() + DOWN * 0.6)
        full_stat5 = Text("Tổng cộng: 1,120 GB (> 1.1 TB VRAM!)", font="Noto Sans", font_size=12, weight=BOLD, color=COLOR_ROSE).move_to(full_box.get_center() + DOWN * 1.1)
        full_grp = VGroup(full_box, full_label, full_stat1, full_stat2, full_stat3, full_stat4, full_stat5)

        # Right Box: The LoRA / QLoRA Breakthrough
        lora_box = RoundedRectangle(corner_radius=0.15, height=3.2, width=4.5, fill_color=COLOR_PANEL, fill_opacity=0.85, stroke_color=COLOR_GREEN, stroke_width=1.5).shift(RIGHT * 2.8 + DOWN * 0.4)
        lora_label = Text("LORA & QLORA BREAKTHROUGH", font="Noto Sans", font_size=13, weight=BOLD, color=COLOR_GREEN).next_to(lora_box, UP, buff=0.12)
        lora_stat1 = Text("Đóng băng 100% trọng số gốc W0", font="Noto Sans", font_size=12.0, color=COLOR_TEXT).move_to(lora_box.get_center() + UP * 0.9)
        lora_stat2 = Text("Chỉ huấn luyện adapter hạng thấp BxA", font="Noto Sans", font_size=12.0, color=COLOR_CYAN).move_to(lora_box.get_center() + UP * 0.4)
        lora_stat3 = Text("Zero optimizer state cho W0", font="Noto Sans", font_size=12.0, weight=BOLD, color=COLOR_GREEN).move_to(lora_box.get_center() + DOWN * 0.1)
        lora_stat4 = Text("QLoRA 4-bit: 70B chạy gọn trong 37GB!", font="Noto Sans", font_size=12.0, color=COLOR_GOLD).move_to(lora_box.get_center() + DOWN * 0.6)
        lora_stat5 = Text("Khả thi trên 1-2 GPU cá nhân", font="Noto Sans", font_size=12, weight=BOLD, color=COLOR_GREEN).move_to(lora_box.get_center() + DOWN * 1.1)
        lora_grp = VGroup(lora_box, lora_label, lora_stat1, lora_stat2, lora_stat3, lora_stat4, lora_stat5)

        self.play(FadeIn(full_grp, shift=RIGHT*0.3), FadeIn(lora_grp, shift=LEFT*0.3), run_time=1.2)

        # 3. Bottom Alert Box
        alert_box = RoundedRectangle(corner_radius=0.12, height=0.9, width=9.8, fill_color="#180e18", fill_opacity=0.95, stroke_color=COLOR_GOLD, stroke_width=1.5).shift(DOWN * 2.5)
        alert_header = Text("NGHỊCH LÝ ĐƯỢC GIẢI MÃ: HUẤN LUYỆN < 1% THAM SỐ NHƯNG ĐẠT 100% HIỆU NĂNG", font="Noto Sans", font_size=13, weight=BOLD, color=COLOR_GOLD).move_to(alert_box.get_center())
        self.play(Create(alert_box), Write(alert_header), run_time=1.0)
        self.wait(1.5)


# ==============================================================================
# SCENE 2: ARCHITECTURE — INTRINSIC RANK & MATRIX DECOMPOSITION (01:25 - 02:55)
# ==============================================================================
class Tap14Scene02Architecture(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "GIẢI PHẪU ĐẠI SỐ TUYẾN TÍNH CỦA LORA")

        # 1. Title
        title = Text("GIẢI THUYẾT HẠNG NỘI TẠI & PHÂN RÃ MA TRẬN HẠNG THẤP", font="Noto Sans", font_size=19, weight=BOLD, color=COLOR_CYAN).to_edge(UP, buff=1.0)
        subtitle = Text("INTRINSIC RANK: BIẾN THIÊN KHI HỌC TÁC VỤ MỚI NẰM TRONG KHÔNG GIAN CON RẤT NHỎ", font="Noto Sans", font_size=12, color=COLOR_TEXT).next_to(title, DOWN, buff=0.12)
        self.play(FadeIn(title, shift=DOWN*0.2), FadeIn(subtitle), run_time=0.9)

        # 2. Main Decomposition Card
        decomp_box = RoundedRectangle(corner_radius=0.15, height=2.2, width=9.8, fill_color=COLOR_PANEL, fill_opacity=0.9, stroke_color=COLOR_GOLD, stroke_width=1.5).shift(UP * 0.5)
        decomp_tex = MathTex(
            r"W = W_0 + \Delta W = W_0 + B \times A, \quad W_0 \in \mathbb{R}^{d \times k}, \ B \in \mathbb{R}^{d \times r}, \ A \in \mathbb{R}^{r \times k} \quad (r \ll d, k)",
            font_size=30, color=COLOR_GOLD
        ).move_to(decomp_box.get_center() + UP * 0.35)
        decomp_header = Text("W0 bị đóng băng (Freeze). Chỉ có A và B được cập nhật gradient với hạng rank r = 8 hoặc 16.", font="Noto Sans", font_size=12.0, color=COLOR_TEXT).move_to(decomp_box.get_center() + DOWN * 0.45)
        self.play(Create(decomp_box), Write(decomp_tex), FadeIn(decomp_header), run_time=1.3)

        # 3. Parameter Reduction Comparison Card
        param_box = RoundedRectangle(corner_radius=0.15, height=2.0, width=9.8, fill_color=COLOR_PANEL, fill_opacity=0.9, stroke_color=COLOR_GREEN, stroke_width=1.5).shift(DOWN * 1.8)
        param_title = Text("SO SÁNH THAM SỐ (VỚI d = 4096, k = 4096, r = 16):", font="Noto Sans", font_size=12, weight=BOLD, color=COLOR_GREEN).move_to(param_box.get_center() + UP * 0.6)
        param_tex = MathTex(
            r"W_0: 4096 \times 4096 = 16,777,216 \text{ params} \quad \longleftrightarrow \quad \text{LoRA } (A + B): 2 \times 4096 \times 16 = 131,072 \text{ params}",
            font_size=28, color=COLOR_GREEN
        ).move_to(param_box.get_center())
        param_hdr = Text("CẮT GIẢM HƠN 128 LẦN THAM SỐ TRÊN MỖI MA TRẬN TUYẾN TÍNH!", font="Noto Sans", font_size=12, weight=BOLD, color=COLOR_CYAN).move_to(param_box.get_center() + DOWN * 0.6)
        self.play(Create(param_box), FadeIn(param_title), Write(param_tex), FadeIn(param_hdr), run_time=1.3)
        self.wait(1.5)


# ==============================================================================
# SCENE 3: MATHEMATICS — ASYMMETRIC INITIALIZATION & ALPHA SCALING (02:55 - 04:25)
# ==============================================================================
class Tap14Scene03Mathematics(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "TOÁN HỌC KHỞI TẠO BẤT ĐỐI XỨNG & ALPHA")

        # 1. Title
        title = Text("TOÁN HỌC KHỞI TẠO BẤT ĐỐI XỨNG & HỆ SỐ TỶ LỆ ALPHA", font="Noto Sans", font_size=19, weight=BOLD, color=COLOR_GOLD).to_edge(UP, buff=1.0)
        subtitle = Text("CƠ CHẾ BẢO VỆ TRI THỨC BAN ĐẦU VÀ ĐIỀU HÒA GRADIENT KHI THAY ĐỔI RANK", font="Noto Sans", font_size=12, color=COLOR_TEXT).next_to(title, DOWN, buff=0.12)
        self.play(FadeIn(title, shift=DOWN*0.2), FadeIn(subtitle), run_time=0.9)

        # 2. Master Forward Equation Card
        f_box = RoundedRectangle(corner_radius=0.15, height=1.9, width=9.8, fill_color=COLOR_PANEL, fill_opacity=0.9, stroke_color=COLOR_CYAN, stroke_width=1.5).shift(UP * 0.7)
        f_tex = MathTex(
            r"h = W_0 x + \Delta W x = W_0 x + \frac{\alpha}{r} (B \times A) x",
            font_size=36, color=COLOR_CYAN
        ).move_to(f_box.get_center() + UP * 0.25)
        f_hdr = Text("alpha: Hằng số khuếch đại (Scaling factor). r: Hạng nén rank của adapter.", font="Noto Sans", font_size=12.0, color=COLOR_TEXT).move_to(f_box.get_center() + DOWN * 0.45)
        self.play(Create(f_box), Write(f_tex), FadeIn(f_hdr), run_time=1.3)

        # 3. Two Pillars: Zero-Gaussian Init & Alpha/r Tuning
        init_box = RoundedRectangle(corner_radius=0.15, height=2.3, width=4.7, fill_color=COLOR_PANEL, fill_opacity=0.85, stroke_color=COLOR_ROSE, stroke_width=1.5).shift(LEFT * 2.5 + DOWN * 1.6)
        init_label = Text("KHỞI TẠO BẤT ĐỐI XỨNG", font="Noto Sans", font_size=12, weight=BOLD, color=COLOR_ROSE).next_to(init_box, UP, buff=0.1)
        init_tex = MathTex(r"A \sim \mathcal{N}(0, \sigma^2), \quad B = 0", font_size=28, color=COLOR_ROSE).move_to(init_box.get_center() + UP * 0.4)
        init_desc1 = Text("Tại t = 0: Delta W = B x A = 0", font="Noto Sans", font_size=12.0, weight=BOLD, color=COLOR_TEXT).move_to(init_box.get_center() + DOWN * 0.2)
        init_desc2 = Text("Đầu ra giữ nguyên 100% gốc!", font="Noto Sans", font_size=12.0, color=COLOR_MUTED).move_to(init_box.get_center() + DOWN * 0.6)
        init_grp = VGroup(init_box, init_label, init_tex, init_desc1, init_desc2)

        scale_box = RoundedRectangle(corner_radius=0.15, height=2.3, width=4.7, fill_color=COLOR_PANEL, fill_opacity=0.85, stroke_color=COLOR_GREEN, stroke_width=1.5).shift(RIGHT * 2.5 + DOWN * 1.6)
        scale_label = Text("HỆ SỐ ĐIỀU HÒA ALPHA / R", font="Noto Sans", font_size=12, weight=BOLD, color=COLOR_GREEN).next_to(scale_box, UP, buff=0.1)
        scale_tex = MathTex(r"\text{Scale} = \frac{\alpha}{r}, \quad \alpha = 2 \times r", font_size=26, color=COLOR_GREEN).move_to(scale_box.get_center() + UP * 0.4)
        scale_hdr1 = Text("Giữ độ lớn gradient ổn định khi đổi r", font="Noto Sans", font_size=12.0, weight=BOLD, color=COLOR_TEXT).move_to(scale_box.get_center() + DOWN * 0.2)
        scale_desc2 = Text("Không cần tune lại Learning Rate!", font="Noto Sans", font_size=12.0, color=COLOR_MUTED).move_to(scale_box.get_center() + DOWN * 0.6)
        scale_grp = VGroup(scale_box, scale_label, scale_tex, scale_hdr1, scale_desc2)

        self.play(FadeIn(init_grp, shift=RIGHT*0.2), FadeIn(scale_grp, shift=LEFT*0.2), run_time=1.3)
        self.wait(1.5)


# ==============================================================================
# SCENE 4: TELEMETRY — QLORA & THE THREE PILLARS (04:25 - 05:55)
# ==============================================================================
class Tap14Scene04Telemetry(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "BỘ BA ĐỘT PHÁ CỦA QLORA")

        # 1. Title
        title = Text("QLORA: ĐỘT PHÁ NF4, LƯỢNG TỬ HÓA KÉP & PAGED OPTIMIZERS", font="Noto Sans", font_size=18, weight=BOLD, color=COLOR_CYAN).to_edge(UP, buff=1.0)
        subtitle = Text("CÔNG TRÌNH CỦA TIM DETTMERS (2023) ĐƯA MÔ HÌNH 70B VỀ CHẠY TRÊN 1 GPU CÁ NHÂN", font="Noto Sans", font_size=12.0, color=COLOR_TEXT).next_to(title, DOWN, buff=0.12)
        self.play(FadeIn(title, shift=DOWN*0.2), FadeIn(subtitle), run_time=0.9)

        # 2. Three Pillars Cards
        p1 = RoundedRectangle(corner_radius=0.12, height=3.0, width=3.1, fill_color=COLOR_PANEL, fill_opacity=0.85, stroke_color=COLOR_CYAN, stroke_width=1.5).shift(LEFT * 3.4 + DOWN * 0.4)
        p1_title = Text("1. NORMALFLOAT 4 (NF4)", font="Noto Sans", font_size=12.0, weight=BOLD, color=COLOR_CYAN).next_to(p1, UP, buff=0.1)
        p1_tex = MathTex(r"q_i = Q_X\left(\frac{2i + 1}{2^{k+1}}\right)", font_size=24, color=COLOR_CYAN).move_to(p1.get_center() + UP * 0.7)
        p1_t1 = Text("Tối ưu theo đường cong", font="Noto Sans", font_size=12.0, color=COLOR_TEXT).move_to(p1.get_center() + UP * 0.1)
        p1_t2 = Text("phân phối chuẩn Gauss.", font="Noto Sans", font_size=12.0, color=COLOR_TEXT).move_to(p1.get_center() - UP * 0.2)
        p1_t3 = Text("Bảo toàn thông tin tối đa.", font="Noto Sans", font_size=12.0, weight=BOLD, color=COLOR_GREEN).move_to(p1.get_center() - UP * 0.6)
        grp_p1 = VGroup(p1, p1_title, p1_tex, p1_t1, p1_t2, p1_t3)

        p2 = RoundedRectangle(corner_radius=0.12, height=3.0, width=3.1, fill_color=COLOR_PANEL, fill_opacity=0.85, stroke_color=COLOR_GOLD, stroke_width=1.5).shift(DOWN * 0.4)
        p2_title = Text("2. DOUBLE QUANT (DQ)", font="Noto Sans", font_size=12.0, weight=BOLD, color=COLOR_GOLD).next_to(p2, UP, buff=0.1)
        p2_tex = MathTex(r"c_2 = \text{quant8}(c_1)", font_size=24, color=COLOR_GOLD).move_to(p2.get_center() + UP * 0.7)
        p2_t1 = Text("Lượng tử hóa chính các", font="Noto Sans", font_size=12.0, color=COLOR_TEXT).move_to(p2.get_center() + UP * 0.1)
        p2_t2 = Text("hằng số tỷ lệ quantization.", font="Noto Sans", font_size=12.0, color=COLOR_TEXT).move_to(p2.get_center() - UP * 0.2)
        p2_t3 = Text("Tiết kiệm 0.37 bit/param!", font="Noto Sans", font_size=12.0, weight=BOLD, color=COLOR_GOLD).move_to(p2.get_center() - UP * 0.6)
        grp_p2 = VGroup(p2, p2_title, p2_tex, p2_t1, p2_t2, p2_t3)

        p3 = RoundedRectangle(corner_radius=0.12, height=3.0, width=3.1, fill_color=COLOR_PANEL, fill_opacity=0.85, stroke_color=COLOR_ROSE, stroke_width=1.5).shift(RIGHT * 3.4 + DOWN * 0.4)
        p3_title = Text("3. PAGED OPTIMIZERS", font="Noto Sans", font_size=12.0, weight=BOLD, color=COLOR_ROSE).next_to(p3, UP, buff=0.1)
        p3_tex = MathTex(r"\text{VRAM} \xrightarrow{\text{PCIe}} \text{RAM}", font_size=24, color=COLOR_ROSE).move_to(p3.get_center() + UP * 0.7)
        p3_t1 = Text("Mượn cơ chế phân trang", font="Noto Sans", font_size=12.0, color=COLOR_TEXT).move_to(p3.get_center() + UP * 0.1)
        p3_t2 = Text("đẩy state sang RAM CPU", font="Noto Sans", font_size=12.0, color=COLOR_TEXT).move_to(p3.get_center() - UP * 0.2)
        p3_t3 = Text("Triệt tiêu hoàn toàn OOM!", font="Noto Sans", font_size=12.0, weight=BOLD, color=COLOR_ROSE).move_to(p3.get_center() - UP * 0.6)
        grp_p3 = VGroup(p3, p3_title, p3_tex, p3_t1, p3_t2, p3_t3)

        self.play(FadeIn(grp_p1, shift=UP*0.3), FadeIn(grp_p2, shift=UP*0.3), FadeIn(grp_p3, shift=UP*0.3), run_time=1.3)

        # 3. Bottom Summary Banner
        banner = RoundedRectangle(corner_radius=0.1, height=0.75, width=9.9, fill_color="#101820", fill_opacity=0.9, stroke_color=COLOR_GREEN, stroke_width=1.5).shift(DOWN * 2.5)
        banner_hdr = Text("KẾT QUẢ: MÔ HÌNH 70B GIẢM TỪ 1,120 GB XUỐNG CHỈ CÒN 37 GB VRAM!", font="Noto Sans", font_size=12, weight=BOLD, color=COLOR_GREEN).move_to(banner.get_center())
        self.play(Create(banner), Write(banner_hdr), run_time=0.9)
        self.wait(1.5)


# ==============================================================================
# SCENE 5: LAB EXPERIMENT — ALL-MODULE ADAPTERS & WEIGHT MERGING (05:55 - 07:25)
# ==============================================================================
class Tap14Scene05LabExperiment(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "KỸ NGHỆ TRIỂN KHAI THỰC TẾ")

        # 1. Title
        title = Text("KỸ NGHỆ TRIỂN KHAI: GẮN ADAPTER TOÀN DIỆN & HỢP NHẤT TRỌNG SỐ", font="Noto Sans", font_size=18, weight=BOLD, color=COLOR_GOLD).to_edge(UP, buff=1.0)
        subtitle = Text("CHIẾN LƯỢC VÀNG TRONG SẢN XUẤT VÀ NGHỆ THUẬT SUY LUẬN VỚI ĐỘ TRỄ BẰNG KHÔNG", font="Noto Sans", font_size=12.0, color=COLOR_TEXT).next_to(title, DOWN, buff=0.12)
        self.play(FadeIn(title, shift=DOWN*0.2), FadeIn(subtitle), run_time=0.9)

        # 2. Module Target Strategy Card
        mod_box = RoundedRectangle(corner_radius=0.15, height=2.0, width=9.8, fill_color=COLOR_PANEL, fill_opacity=0.9, stroke_color=COLOR_CYAN, stroke_width=1.5).shift(UP * 0.7)
        mod_title = Text("1. CHIẾN LƯỢC VỊ TRÍ GẮN ADAPTER (TARGET MODULES):", font="Noto Sans", font_size=12, weight=BOLD, color=COLOR_CYAN).move_to(mod_box.get_center() + UP * 0.6)
        mod_tex = MathTex(
            r"\text{Target: } \{W_q, W_k, W_v, W_o\} \ \cup \ \{W_{gate}, W_{up}, W_{down}\}",
            font_size=28, color=COLOR_CYAN
        ).move_to(mod_box.get_center() + UP * 0.05)
        mod_hdr = Text("Gắn toàn diện vào cả Attention lẫn MLP với rank nhỏ (r=16) tốt hơn nhiều so với chỉ gắn Wq, Wv!", font="Noto Sans", font_size=12.0, color=COLOR_TEXT).move_to(mod_box.get_center() + DOWN * 0.55)
        self.play(Create(mod_box), FadeIn(mod_title), Write(mod_tex), FadeIn(mod_hdr), run_time=1.3)

        # 3. Weight Merging Card
        merge_box = RoundedRectangle(corner_radius=0.15, height=2.1, width=9.8, fill_color=COLOR_PANEL, fill_opacity=0.9, stroke_color=COLOR_GREEN, stroke_width=1.5).shift(DOWN * 1.6)
        merge_title = Text("2. HỢP NHẤT TRỌNG SỐ SUY LUẬN (WEIGHT MERGE — ZERO LATENCY):", font="Noto Sans", font_size=12, weight=BOLD, color=COLOR_GREEN).move_to(merge_box.get_center() + UP * 0.65)
        merge_tex = MathTex(
            r"W_{\text{final}} = W_0 + \frac{\alpha}{r} (B \times A), \quad y = W_{\text{final}} x",
            font_size=32, color=COLOR_GREEN
        ).move_to(merge_box.get_center() + UP * 0.05)
        merge_hdr = Text("Cộng trực tiếp delta W vào ma trận gốc -> Bỏ nhánh phụ -> Độ trễ suy luận = 0 ms!", font="Noto Sans", font_size=12.0, weight=BOLD, color=COLOR_TEXT).move_to(merge_box.get_center() + DOWN * 0.55)
        self.play(Create(merge_box), FadeIn(merge_title), Write(merge_tex), FadeIn(merge_hdr), run_time=1.3)
        self.wait(1.5)


# ==============================================================================
# SCENE 6: OUTRO — 5x5 MOSAIC & EPISODE 15 TEASER (07:25 - 08:35)
# ==============================================================================
class Tap14Scene06Outro(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "TỔNG KẾT & CẦU NỐI KỸ NGHỆ")

        scene_title = Text(
            "BÀN GIAO TRI THỨC // LORA & QLORA",
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
        # 1. Next Video Card (Episode 15: Speculative Decoding)
        next_card = RoundedRectangle(
            corner_radius=0.12, width=3.8, height=2.0,
            fill_color=COLOR_PANEL, fill_opacity=0.7, stroke_color=COLOR_CYAN, stroke_width=1.5
        ).move_to(RIGHT * 3.5 + UP * 1.5)
        next_header = Text("TẬP TIẾP THEO // TẬP 15", font="Noto Sans", font_size=12.5, weight=BOLD, color=COLOR_CYAN)
        next_sub_header = Text("SPECULATIVE DECODING: ĐOÁN TOKEN", font="Noto Sans", font_size=12.0, color=COLOR_TEXT).next_to(next_header, DOWN, buff=0.18)
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
