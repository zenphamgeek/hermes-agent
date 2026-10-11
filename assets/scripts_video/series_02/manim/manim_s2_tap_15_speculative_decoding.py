#!/usr/bin/env python3
"""
Manim 2K QHD Master Scenes — Speculative Decoding // Cơ Chế Đoán Trước Tương Lai Để Tăng Tốc Sinh Token
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


# ==============================================================================
# SCENE 1: COLD OPEN — AUTOREGRESSIVE MEMORY BOTTLENECK (00:00 - 01:25)
# ==============================================================================
class Tap15Scene01ColdOpen(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "NÚT THẮT BĂNG THÔNG BỘ NHỚ HBM")

        # 1. Main Title
        title_top = Text("NÚT THẮT SINH TỪNG TỪ TỰ HỒI QUY", font="Noto Sans", font_size=22, weight=BOLD, color=COLOR_GOLD)
        title_sub = Text("TẠI SAO GPU HÀNG TRĂM TFLOPS LẠI BỊ KẸT CỨNG TRONG PHA GIẢI MÃ TỰ HỒI QUY?", font="Noto Sans", font_size=12, color=COLOR_TEXT)
        title_grp = VGroup(title_top, title_sub).arrange(DOWN, buff=0.15).to_edge(UP, buff=1.0)
        self.play(FadeIn(title_grp, shift=DOWN*0.3), run_time=0.9)

        # 2. Left Box: Standard Autoregressive Generation
        ar_box = RoundedRectangle(corner_radius=0.15, height=3.2, width=4.5, fill_color=COLOR_PANEL, fill_opacity=0.85, stroke_color=COLOR_ROSE, stroke_width=1.5).shift(LEFT * 2.8 + DOWN * 0.4)
        ar_label = Text("GIẢI MÃ TỰ HỒI QUY TRUYỀN THỐNG", font="Noto Sans", font_size=12, weight=BOLD, color=COLOR_ROSE).next_to(ar_box, UP, buff=0.12)
        ar_stat1 = Text("LLaMA-70B: Nạp 140 GB / 1 token", font="Noto Sans", font_size=12.0, color=COLOR_TEXT).move_to(ar_box.get_center() + UP * 0.9)
        ar_stat2 = Text("Băng thông HBM: 100% Saturation", font="Noto Sans", font_size=12.0, color=COLOR_ROSE).move_to(ar_box.get_center() + UP * 0.4)
        ar_stat3 = Text("Tensor Core: Chỉ chạy ~3% năng lực", font="Noto Sans", font_size=12.0, color=COLOR_MUTED).move_to(ar_box.get_center() + DOWN * 0.1)
        ar_stat4 = Text("97% thời gian: GPU ngồi chờ dữ liệu", font="Noto Sans", font_size=12.0, weight=BOLD, color=COLOR_ROSE).move_to(ar_box.get_center() + DOWN * 0.6)
        ar_stat5 = Text("Nghiêm trọng: Memory-Bound Regime", font="Noto Sans", font_size=12.0, color=COLOR_GOLD).move_to(ar_box.get_center() + DOWN * 1.1)
        ar_grp = VGroup(ar_box, ar_label, ar_stat1, ar_stat2, ar_stat3, ar_stat4, ar_stat5)

        # Right Box: Speculative Decoding Paradigm
        spec_box = RoundedRectangle(corner_radius=0.15, height=3.2, width=4.5, fill_color=COLOR_PANEL, fill_opacity=0.85, stroke_color=COLOR_GREEN, stroke_width=1.5).shift(RIGHT * 2.8 + DOWN * 0.4)
        spec_label = Text("SPECULATIVE DECODING", font="Noto Sans", font_size=13, weight=BOLD, color=COLOR_GREEN).next_to(spec_box, UP, buff=0.12)
        spec_stat1 = Text("Mô hình Draft (1B): Đoán nhanh k token", font="Noto Sans", font_size=12.0, color=COLOR_TEXT).move_to(spec_box.get_center() + UP * 0.9)
        spec_stat2 = Text("Mô hình Target (70B): Duyệt 1 nhịp duy nhất", font="Noto Sans", font_size=12.0, color=COLOR_CYAN).move_to(spec_box.get_center() + UP * 0.4)
        spec_stat3 = Text("Tận dụng Tensor Core tính song song", font="Noto Sans", font_size=12.0, color=COLOR_GREEN).move_to(spec_box.get_center() + DOWN * 0.1)
        spec_stat4 = Text("Tăng tốc 2.5x - 3.5x thời gian thực!", font="Noto Sans", font_size=12.0, weight=BOLD, color=COLOR_GREEN).move_to(spec_box.get_center() + DOWN * 0.6)
        spec_stat5 = Text("Bảo toàn 100% phân phối Target", font="Noto Sans", font_size=12.0, color=COLOR_GOLD).move_to(spec_box.get_center() + DOWN * 1.1)
        spec_grp = VGroup(spec_box, spec_label, spec_stat1, spec_stat2, spec_stat3, spec_stat4, spec_stat5)

        self.play(FadeIn(ar_grp, shift=RIGHT*0.3), FadeIn(spec_grp, shift=LEFT*0.3), run_time=1.2)

        # 3. Bottom Alert Box
        alert_box = RoundedRectangle(corner_radius=0.12, height=0.9, width=9.8, fill_color="#180e18", fill_opacity=0.95, stroke_color=COLOR_GOLD, stroke_width=1.5).shift(DOWN * 2.5)
        alert_header = Text("ĐOÁN NHANH BẢN NHÁP — KIỂM CHỨNG CHÍNH XÁC TRONG MỘT FORWARD PASS", font="Noto Sans", font_size=13, weight=BOLD, color=COLOR_GOLD).move_to(alert_box.get_center())
        self.play(Create(alert_box), Write(alert_header), run_time=1.0)
        self.wait(1.5)


# ==============================================================================
# SCENE 2: ARCHITECTURE — DRAFT & TARGET DUAL PIPELINE (01:25 - 02:55)
# ==============================================================================
class Tap15Scene02Architecture(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "KIẾN TRÚC DRAFT VÀ TARGET")

        # 1. Title
        title = Text("SỰ PHÂN CÔNG GIỮA MÔ HÌNH DRAFT VÀ TARGET", font="Noto Sans", font_size=19, weight=BOLD, color=COLOR_CYAN).to_edge(UP, buff=1.0)
        sub_header = Text("CAUSAL MASKING CHO PHÉP TARGET KIỂM CHỨNG SONG SONG K TOKEN ĐỀ XUẤT TRONG 1 LƯỢT", font="Noto Sans", font_size=12, color=COLOR_TEXT).next_to(title, DOWN, buff=0.12)
        self.play(FadeIn(title, shift=DOWN*0.2), FadeIn(sub_header), run_time=0.9)

        # 2. Main Dual Architecture Card
        card_box = RoundedRectangle(corner_radius=0.15, height=2.2, width=9.8, fill_color=COLOR_PANEL, fill_opacity=0.9, stroke_color=COLOR_GOLD, stroke_width=1.5).shift(UP * 0.5)
        step1_tex = MathTex(
            r"\text{Draft } M_q: \quad x \xrightarrow{\text{k steps}} (\tilde{x}_1, \tilde{x}_2, \dots, \tilde{x}_k) \sim q(x)",
            font_size=28, color=COLOR_GOLD
        ).move_to(card_box.get_center() + UP * 0.45)
        step2_tex = MathTex(
            r"\text{Target } M_p: \quad \text{Forward}(x, \tilde{x}_1, \dots, \tilde{x}_k) \xrightarrow{\text{1 pass}} (p_1, p_2, \dots, p_k, p_{k+1})",
            font_size=28, color=COLOR_CYAN
        ).move_to(card_box.get_center() - UP * 0.35)
        self.play(Create(card_box), Write(step1_tex), Write(step2_tex), run_time=1.4)

        # 3. Benefits & Synchronization Card
        sync_box = RoundedRectangle(corner_radius=0.15, height=2.0, width=9.8, fill_color=COLOR_PANEL, fill_opacity=0.9, stroke_color=COLOR_GREEN, stroke_width=1.5).shift(DOWN * 1.8)
        sync_title = Text("TỐI ƯU HÓA BĂNG THÔNG BỘ NHỚ VÀ PHẦN CỨNG:", font="Noto Sans", font_size=12, weight=BOLD, color=COLOR_GREEN).move_to(sync_box.get_center() + UP * 0.6)
        sync_desc1_hdr = Text("• Draft model siêu nhỏ (1B-3B) chạy hoàn toàn trong SRAM và bộ nhớ đệm tốc độ cao.", font="Noto Sans", font_size=12.0, color=COLOR_TEXT).move_to(sync_box.get_center() + UP * 0.1)
        sync_desc2_hdr = Text("• Target model (70B) chỉ nạp trọng số qua HBM đúng 1 lần cho k vị trí thay vì k lần tuần tự!", font="Noto Sans", font_size=12.0, color=COLOR_GREEN).move_to(sync_box.get_center() - UP * 0.4)
        self.play(Create(sync_box), FadeIn(sync_title), FadeIn(sync_desc1_hdr), FadeIn(sync_desc2_hdr), run_time=1.3)
        self.wait(1.5)


# ==============================================================================
# SCENE 3: MATHEMATICS — MODIFIED REJECTION SAMPLING (02:55 - 04:25)
# ==============================================================================
class Tap15Scene03Mathematics(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "TOÁN HỌC MODIFIED REJECTION SAMPLING")

        # 1. Title
        title = Text("TOÁN HỌC LẤY MẪU BÁC BỎ CẢI TIẾN (LEVIATHAN ET AL., ICML 2023)", font="Noto Sans", font_size=18, weight=BOLD, color=COLOR_GOLD).to_edge(UP, buff=1.0)
        sub_header = Text("CHỨNG MINH ĐẦU RA CUỐI CÙNG TUÂN THEO PHÂN PHỐI TARGET VỚI ĐỘ CHÍNH XÁC 100%", font="Noto Sans", font_size=12, color=COLOR_TEXT).next_to(title, DOWN, buff=0.12)
        self.play(FadeIn(title, shift=DOWN*0.2), FadeIn(sub_header), run_time=0.9)

        # 2. Acceptance Probability Card
        acc_box = RoundedRectangle(corner_radius=0.15, height=2.0, width=9.8, fill_color=COLOR_PANEL, fill_opacity=0.9, stroke_color=COLOR_CYAN, stroke_width=1.5).shift(UP * 0.6)
        acc_tex = MathTex(
            r"\alpha(x) = \min\left(1, \frac{p(x)}{q(x)}\right), \quad u \sim \mathcal{U}[0, 1) \implies \text{Accept if } u < \alpha(x)",
            font_size=32, color=COLOR_CYAN
        ).move_to(acc_box.get_center() + UP * 0.3)
        acc_desc_hdr = Text("Nếu token nháp x thỏa mãn: Giữ lại x và tiếp tục xét token nháp kế tiếp.", font="Noto Sans", font_size=12.0, color=COLOR_TEXT).move_to(acc_box.get_center() - UP * 0.45)
        self.play(Create(acc_box), Write(acc_tex), FadeIn(acc_desc_hdr), run_time=1.3)

        # 3. Recovery Distribution on Rejection Card
        rec_box = RoundedRectangle(corner_radius=0.15, height=2.3, width=9.8, fill_color=COLOR_PANEL, fill_opacity=0.9, stroke_color=COLOR_ROSE, stroke_width=1.5).shift(DOWN * 1.7)
        rec_title = Text("KHI BỊ BÁC BỎ (REJECT): HỦY TOÀN BỘ PHẦN ĐUÔI VÀ LẤY MẪU HIỆU CHỈNH:", font="Noto Sans", font_size=12, weight=BOLD, color=COLOR_ROSE).move_to(rec_box.get_center() + UP * 0.75)
        rec_tex = MathTex(
            r"r(y) = \frac{\max(0, p(y) - q(y))}{\sum_{z} \max(0, p(z) - q(z))}, \quad y \sim r(y)",
            font_size=30, color=COLOR_ROSE
        ).move_to(rec_box.get_center() + UP * 0.1)
        rec_exp_hdr = Text("Định lý toán học: p_spec(x) = q(x)*alpha(x) + (1-beta)*r(x) == p(x) (BẢO TOÀN HOÀN TOÀN!)", font="Noto Sans", font_size=12.0, weight=BOLD, color=COLOR_GREEN).move_to(rec_box.get_center() - UP * 0.65)
        self.play(Create(rec_box), FadeIn(rec_title), Write(rec_tex), FadeIn(rec_exp_hdr), run_time=1.4)
        self.wait(1.5)


# ==============================================================================
# SCENE 4: TELEMETRY — INFERENCE ECONOMICS & ACCEPTANCE RATE (04:25 - 05:55)
# ==============================================================================
class Tap15Scene04Telemetry(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "KINH TẾ HỌC SUY LUẬN & ĐỘ TĂNG TỐC")

        # 1. Title
        title = Text("KINH TẾ HỌC SUY LUẬN: TỶ LỆ CHẤP NHẬN & SPEEDUP", font="Noto Sans", font_size=19, weight=BOLD, color=COLOR_CYAN).to_edge(UP, buff=1.0)
        sub_header = Text("PHƯƠNG TRÌNH ĐÁNH ĐỔI GIỮA CHI PHÍ DRAFT VÀ THỜI GIAN TIẾT KIỆM ĐƯỢC", font="Noto Sans", font_size=12, color=COLOR_TEXT).next_to(title, DOWN, buff=0.12)
        self.play(FadeIn(title, shift=DOWN*0.2), FadeIn(sub_header), run_time=0.9)

        # 2. Formula Card: Expected Tokens per Round
        f_box = RoundedRectangle(corner_radius=0.15, height=2.1, width=9.8, fill_color=COLOR_PANEL, fill_opacity=0.9, stroke_color=COLOR_GOLD, stroke_width=1.5).shift(UP * 0.6)
        f_tex = MathTex(
            r"\mathbb{E}[L] = \frac{1 - \beta^{k+1}}{1 - \beta}, \quad \text{Speedup} = \frac{\mathbb{E}[L] \cdot T_{\text{target}}}{k \cdot T_{\text{draft}} + T_{\text{verify}} + T_{\text{overhead}}}",
            font_size=28, color=COLOR_GOLD
        ).move_to(f_box.get_center() + UP * 0.25)
        f_sub_hdr = Text("beta: Tỷ lệ chấp nhận trung bình (Acceptance rate). k: Độ dài chuỗi nháp suy đoán.", font="Noto Sans", font_size=12.0, color=COLOR_TEXT).move_to(f_box.get_center() - UP * 0.5)
        self.play(Create(f_box), Write(f_tex), FadeIn(f_sub_hdr), run_time=1.3)

        # 3. Two Comparison Cases (High beta vs Low beta)
        box_hi = RoundedRectangle(corner_radius=0.15, height=2.2, width=4.7, fill_color=COLOR_PANEL, fill_opacity=0.85, stroke_color=COLOR_GREEN, stroke_width=1.5).shift(LEFT * 2.5 + DOWN * 1.7)
        hi_lbl = Text("KỊCH BẢN TỐI ƯU (BETA >= 80%)", font="Noto Sans", font_size=12, weight=BOLD, color=COLOR_GREEN).next_to(box_hi, UP, buff=0.1)
        hi_t1 = Text("Văn bản hội thoại, tin tức, văn phong chung", font="Noto Sans", font_size=12.0, color=COLOR_TEXT).move_to(box_hi.get_center() + UP * 0.5)
        hi_t2 = Text("Thu hoạch 3-4 token / 1 vòng lặp", font="Noto Sans", font_size=12.0, weight=BOLD, color=COLOR_CYAN).move_to(box_hi.get_center() + UP * 0.05)
        hi_t3 = Text("Tăng tốc 2.5x - 3.5x thời gian thực!", font="Noto Sans", font_size=12.0, weight=BOLD, color=COLOR_GREEN).move_to(box_hi.get_center() - UP * 0.45)
        grp_hi = VGroup(box_hi, hi_lbl, hi_t1, hi_t2, hi_t3)

        box_lo = RoundedRectangle(corner_radius=0.15, height=2.2, width=4.7, fill_color=COLOR_PANEL, fill_opacity=0.85, stroke_color=COLOR_ROSE, stroke_width=1.5).shift(RIGHT * 2.5 + DOWN * 1.7)
        lo_lbl = Text("KỊCH BẢN KÉM (BETA < 50%)", font="Noto Sans", font_size=12, weight=BOLD, color=COLOR_ROSE).next_to(box_lo, UP, buff=0.1)
        lo_t1 = Text("Toán học phức tạp, mã nguồn hiếm gặp", font="Noto Sans", font_size=12.0, color=COLOR_TEXT).move_to(box_lo.get_center() + UP * 0.5)
        lo_t2 = Text("Draft model liên tục bị bác bỏ", font="Noto Sans", font_size=12.0, color=COLOR_ROSE).move_to(box_lo.get_center() + UP * 0.05)
        lo_t3 = Text("Hệ thống có thể chậm hơn chạy gốc!", font="Noto Sans", font_size=12.0, weight=BOLD, color=COLOR_ROSE).move_to(box_lo.get_center() - UP * 0.45)
        grp_lo = VGroup(box_lo, lo_lbl, lo_t1, lo_t2, lo_t3)

        self.play(FadeIn(grp_hi, shift=RIGHT*0.2), FadeIn(grp_lo, shift=LEFT*0.2), run_time=1.3)
        self.wait(1.5)


# ==============================================================================
# SCENE 5: LAB EXPERIMENT — MEDUSA & EAGLE (05:55 - 07:25)
# ==============================================================================
class Tap15Scene05LabExperiment(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "MEDUSA & EAGLE — TIẾN HÓA KỸ NGHỆ")

        # 1. Title
        title = Text("TIẾN HÓA KỸ NGHỆ: KHAI TỬ MÔ HÌNH DRAFT ĐỘC LẬP", font="Noto Sans", font_size=18, weight=BOLD, color=COLOR_GOLD).to_edge(UP, buff=1.0)
        sub_header = Text("MEDUSA & EAGLE: GẮN NHIỀU ĐẦU GIẢI MÃ TUYẾN TÍNH TRỰC TIẾP LÊN MÔ HÌNH TARGET", font="Noto Sans", font_size=12.0, color=COLOR_TEXT).next_to(title, DOWN, buff=0.12)
        self.play(FadeIn(title, shift=DOWN*0.2), FadeIn(sub_header), run_time=0.9)

        # 2. Medusa Architecture Card
        med_box = RoundedRectangle(corner_radius=0.15, height=2.0, width=9.8, fill_color=COLOR_PANEL, fill_opacity=0.9, stroke_color=COLOR_CYAN, stroke_width=1.5).shift(UP * 0.7)
        med_title = Text("1. KIẾN TRÚC MEDUSA (MULTIPLE DECODING HEADS):", font="Noto Sans", font_size=12, weight=BOLD, color=COLOR_CYAN).move_to(med_box.get_center() + UP * 0.6)
        med_tex = MathTex(
            r"\text{Head}_1 \to \tilde{x}_{t+1}, \quad \text{Head}_2 \to \tilde{x}_{t+2}, \quad \text{Head}_3 \to \tilde{x}_{t+3} \quad \text{(Parallel Heads)}",
            font_size=28, color=COLOR_CYAN
        ).move_to(med_box.get_center() + UP * 0.05)
        med_desc_hdr = Text("Không cần nạp thêm mô hình Draft! Không phân mảnh VRAM hay rắc rối Tokenizer.", font="Noto Sans", font_size=12.0, color=COLOR_TEXT).move_to(med_box.get_center() - UP * 0.55)
        self.play(Create(med_box), FadeIn(med_title), Write(med_tex), FadeIn(med_desc_hdr), run_time=1.3)

        # 3. Tree Attention & EAGLE Card
        tree_box = RoundedRectangle(corner_radius=0.15, height=2.1, width=9.8, fill_color=COLOR_PANEL, fill_opacity=0.9, stroke_color=COLOR_GREEN, stroke_width=1.5).shift(DOWN * 1.6)
        tree_title = Text("2. TREE ATTENTION & THUẬT TOÁN EAGLE:", font="Noto Sans", font_size=12, weight=BOLD, color=COLOR_GREEN).move_to(tree_box.get_center() + UP * 0.65)
        tree_tex = MathTex(
            r"\text{Tree Attention: Parallel Multi-Branch Verification Graph}",
            font_size=28, color=COLOR_GREEN
        ).move_to(tree_box.get_center() + UP * 0.05)
        tree_desc_hdr = Text("Tỷ lệ chấp thuận beta vọt lên > 90% -> Tích hợp hoàn hảo trên engine vLLM & SGLang!", font="Noto Sans", font_size=12.0, weight=BOLD, color=COLOR_TEXT).move_to(tree_box.get_center() - UP * 0.55)
        self.play(Create(tree_box), FadeIn(tree_title), Write(tree_tex), FadeIn(tree_desc_hdr), run_time=1.3)
        self.wait(1.5)


# ==============================================================================
# SCENE 6: OUTRO — ACKNOWLEDGMENT & EPISODE 16 TEASER (07:25 - 08:35)
# ==============================================================================
class Tap15Scene06Outro(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "TỔNG KẾT & CẦU NỐI KỸ NGHỆ")

        scene_title = Text(
            "BÀN GIAO TRI THỨC // SPECULATIVE DECODING",
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
        # 1. Next Video Card (Episode 16: Direct Preference Optimization)
        next_card = RoundedRectangle(
            corner_radius=0.12, width=3.8, height=2.0,
            fill_color=COLOR_PANEL, fill_opacity=0.7, stroke_color=COLOR_CYAN, stroke_width=1.5
        ).move_to(RIGHT * 3.5 + UP * 1.5)
        next_header = Text("TẬP TIẾP THEO // TẬP 16", font="Noto Sans", font_size=12.5, weight=BOLD, color=COLOR_CYAN)
        next_sub_header = Text("DPO: CĂN CHỈNH KHÔNG CẦN THƯỞNG", font="Noto Sans", font_size=12.0, color=COLOR_TEXT).next_to(next_header, DOWN, buff=0.18)
        next_grp = VGroup(next_header, next_sub_header).move_to(next_card.get_center())

        # 2. Playlist Card
        pl_card = RoundedRectangle(
            corner_radius=0.12, width=3.8, height=1.3,
            fill_color=COLOR_PANEL, fill_opacity=0.7, stroke_color=COLOR_GOLD, stroke_width=1.5
        ).move_to(RIGHT * 3.5 + DOWN * 0.35)
        pl_header = Text("PLAYLIST TRỌN BỘ 25 TẬP", font="Noto Sans", font_size=12.0, weight=BOLD, color=COLOR_GOLD).move_to(pl_card.get_center())

        # 3. Channel Subscribe Avatar Circle
        sub_circle = Circle(
            radius=0.52, fill_color=COLOR_BG, fill_opacity=0.9, stroke_color=COLOR_GOLD, stroke_width=1.5
        ).move_to(RIGHT * 3.5 + DOWN * 1.65)
        sub_header = Text("ZEN", font="Noto Sans", font_size=12.0, weight=BOLD, color=COLOR_GOLD).move_to(sub_circle.get_center())

        self.play(
            FadeIn(next_card), FadeIn(next_grp),
            run_time=0.9
        )
        self.play(
            FadeIn(pl_card), FadeIn(pl_header),
            FadeIn(sub_circle), FadeIn(sub_header),
            outro_tracker.animate.set_value(1.0),
            run_time=1.0
        )
        self.wait(2.0)
