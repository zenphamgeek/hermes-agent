#!/usr/bin/env python3
"""
Manim 2K QHD Master Scenes — Direct Preference Optimization (DPO) // Khai Tử Mô Hình Thưởng Phức Tạp Của RLHF
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


def add_zenpham_brand(scene, ep_title="DIRECT PREFERENCE OPTIMIZATION"):
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
# SCENE 1: COLD OPEN — SFT LIMITATIONS & ALIGNMENT (00:00 - 01:25)
# ==============================================================================
class Tap16Scene01ColdOpen(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "GIỚI HẠN CỦA HỌC CÓ GIÁM SÁT SFT")

        # 1. Main Title
        title_top = Text("BÀI TOÁN CĂN CHỈNH HÀNH VI (ALIGNMENT)", font="Noto Sans", font_size=22, weight=BOLD, color=COLOR_GOLD)
        title_sub = Text("TẠI SAO HỌC CÓ GIÁM SÁT SFT KHÔNG ĐỦ ĐỂ DẠY MÔ HÌNH VỀ SỰ ƯA THÍCH CỦA CON NGƯỜI?", font="Noto Sans", font_size=12, color=COLOR_TEXT)
        title_grp = VGroup(title_top, title_sub).arrange(DOWN, buff=0.15).to_edge(UP, buff=1.0)
        self.play(FadeIn(title_grp, shift=DOWN*0.3), run_time=0.9)

        # 2. Left Box: Raw SFT Output
        sft_box = RoundedRectangle(corner_radius=0.15, height=3.2, width=4.5, fill_color=COLOR_PANEL, fill_opacity=0.85, stroke_color=COLOR_ROSE, stroke_width=1.5).shift(LEFT * 2.8 + DOWN * 0.4)
        sft_label = Text("MÔ HÌNH CHỈ QUA SFT", font="Noto Sans", font_size=13, weight=BOLD, color=COLOR_ROSE).next_to(sft_box, UP, buff=0.12)
        sft_stat1 = Text("Tối đa hóa xác suất token tiếp theo", font="Noto Sans", font_size=12.0, color=COLOR_TEXT).move_to(sft_box.get_center() + UP * 0.9)
        sft_stat2 = Text("Dễ sinh văn bản dài dòng, sáo rỗng", font="Noto Sans", font_size=12.0, color=COLOR_ROSE).move_to(sft_box.get_center() + UP * 0.4)
        sft_stat3 = Text("Hội chứng nịnh bợ (Sycophancy)", font="Noto Sans", font_size=12.0, color=COLOR_MUTED).move_to(sft_box.get_center() + DOWN * 0.1)
        sft_stat4 = Text("Tự tin bịa đặt sai sự thật (Ảo giác)", font="Noto Sans", font_size=12.0, weight=BOLD, color=COLOR_ROSE).move_to(sft_box.get_center() + DOWN * 0.6)
        sft_stat5 = Text("Không có khái niệm xếp hạng hơn / kém", font="Noto Sans", font_size=12.0, color=COLOR_GOLD).move_to(sft_box.get_center() + DOWN * 1.1)
        sft_grp = VGroup(sft_box, sft_label, sft_stat1, sft_stat2, sft_stat3, sft_stat4, sft_stat5)

        # Right Box: Human Preference Alignment
        pref_box = RoundedRectangle(corner_radius=0.15, height=3.2, width=4.5, fill_color=COLOR_PANEL, fill_opacity=0.85, stroke_color=COLOR_GREEN, stroke_width=1.5).shift(RIGHT * 2.8 + DOWN * 0.4)
        pref_label = Text("CĂN CHỈNH ƯA THÍCH (PREFERENCE)", font="Noto Sans", font_size=13, weight=BOLD, color=COLOR_GREEN).next_to(pref_box, UP, buff=0.12)
        pref_stat1 = Text("Cặp dữ liệu: Câu thắng (yw) vs Câu thua (yl)", font="Noto Sans", font_size=12.0, color=COLOR_TEXT).move_to(pref_box.get_center() + UP * 0.9)
        pref_stat2 = Text("Tính hữu ích: Trả lời trúng trọng tâm", font="Noto Sans", font_size=12.0, color=COLOR_CYAN).move_to(pref_box.get_center() + UP * 0.4)
        pref_stat3 = Text("Tính trung thực: Không bịa đặt tri thức", font="Noto Sans", font_size=12.0, color=COLOR_GREEN).move_to(pref_box.get_center() + DOWN * 0.1)
        pref_stat4 = Text("Tính an toàn: Khước từ yêu cầu độc hại", font="Noto Sans", font_size=12.0, color=COLOR_TEXT).move_to(pref_box.get_center() + DOWN * 0.6)
        pref_stat5 = Text("Mục tiêu: Đưa LLM tiệm cận giá trị con người", font="Noto Sans", font_size=12.0, weight=BOLD, color=COLOR_GOLD).move_to(pref_box.get_center() + DOWN * 1.1)
        pref_grp = VGroup(pref_box, pref_label, pref_stat1, pref_stat2, pref_stat3, pref_stat4, pref_stat5)

        self.play(FadeIn(sft_grp, shift=RIGHT*0.2), FadeIn(pref_grp, shift=LEFT*0.2), run_time=1.2)

        # Bottom summary callout
        summary_box = RoundedRectangle(corner_radius=0.1, height=0.7, width=9.2, fill_color="#1e293b", fill_opacity=0.8, stroke_color=COLOR_CYAN, stroke_width=1.0).to_edge(DOWN, buff=0.4)
        summary_header = Text("Học tăng cường RLHF từng là lời giải duy nhất, nhưng lại mang một gánh nặng khổng lồ trên GPU.", font="Noto Sans", font_size=12, color=COLOR_CYAN).move_to(summary_box)
        self.play(FadeIn(summary_box), Write(summary_header), run_time=0.9)
        self.wait(2.0)


# ==============================================================================
# SCENE 2: RLHF ARCHITECTURE — THE 4-MODEL DANCE (01:25 - 02:55)
# ==============================================================================
class Tap16Scene02Architecture(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "BẢN GIAO HƯỞNG BỐN MÔ HÌNH RLHF")

        title = Text("CẤU TRÚC BỐN MÔ HÌNH TRONG RLHF & PPO TRUYỀN THỐNG", font="Noto Sans", font_size=20, weight=BOLD, color=COLOR_GOLD).to_edge(UP, buff=1.0)
        self.play(FadeIn(title, shift=DOWN*0.2), run_time=0.8)

        # 4 Model Cards arranged in a 2x2 Grid
        cards_data = [
            ("POLICY / ACTOR", "pi_theta(y|x)", "Sinh token tự hồi quy, cập nhật PPO", COLOR_CYAN, LEFT*2.7 + UP*0.8),
            ("REFERENCE MODEL", "pi_ref(y|x)", "Mô hình SFT cố định, rào chắn KL", COLOR_MUTED, RIGHT*2.7 + UP*0.8),
            ("REWARD MODEL", "r_psi(x, y)", "Giám khảo chấm điểm thưởng", COLOR_GOLD, LEFT*2.7 + DOWN*1.5),
            ("VALUE / CRITIC", "V_phi(x)", "Ước lượng kỳ vọng, giảm phương sai", COLOR_ROSE, RIGHT*2.7 + DOWN*1.5),
        ]

        card_vgroups = []
        for name, math_sym, desc, col, pos in cards_data:
            box = RoundedRectangle(corner_radius=0.15, height=1.9, width=4.8, fill_color=COLOR_PANEL, fill_opacity=0.9, stroke_color=col, stroke_width=2.0).move_to(pos)
            lbl = Text(name, font="Noto Sans", font_size=13, weight=BOLD, color=col).move_to(box.get_top() + DOWN * 0.28)
            math_t = MathTex(math_sym, font_size=24, color=WHITE).move_to(box.get_center() + UP * 0.05)
            d_txt = Text(desc, font="Noto Sans", font_size=12.0, color=COLOR_TEXT).move_to(box.get_bottom() + UP * 0.28)
            card_vgroups.append(VGroup(box, lbl, math_t, d_txt))

        self.play(
            LaggedStart(
                FadeIn(card_vgroups[0], shift=RIGHT*0.2),
                FadeIn(card_vgroups[1], shift=LEFT*0.2),
                FadeIn(card_vgroups[2], shift=RIGHT*0.2),
                FadeIn(card_vgroups[3], shift=LEFT*0.2),
                lag_ratio=0.25
            ),
            run_time=1.6
        )

        # Arrows showing complex data flow
        arr1 = Arrow(card_vgroups[0].get_bottom(), card_vgroups[2].get_top(), buff=0.1, color=COLOR_CYAN, stroke_width=2)
        arr2 = Arrow(card_vgroups[0].get_right(), card_vgroups[1].get_left(), buff=0.1, color=COLOR_MUTED, stroke_width=2)
        arr3 = Arrow(card_vgroups[2].get_right(), card_vgroups[3].get_left(), buff=0.1, color=COLOR_GOLD, stroke_width=2)
        self.play(Create(arr1), Create(arr2), Create(arr3), run_time=1.0)

        # Hardware Bottleneck Warning Banner
        vram_banner = RoundedRectangle(corner_radius=0.1, height=0.65, width=9.2, fill_color="#331018", fill_opacity=0.9, stroke_color=COLOR_ROSE, stroke_width=1.5).to_edge(DOWN, buff=0.35)
        vram_header = Text("Gánh nặng phần cứng: Mô hình 70B cần hơn 500GB VRAM để chạy đồng thời 4 mô hình!", font="Noto Sans", font_size=12, weight=BOLD, color=COLOR_ROSE).move_to(vram_banner)
        self.play(FadeIn(vram_banner), Write(vram_header), run_time=0.9)
        self.wait(2.0)


# ==============================================================================
# SCENE 3: REWARD HACKING & KL PENALTY (02:55 - 04:25)
# ==============================================================================
class Tap16Scene03Mathematics(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "HIỆN TƯỢNG REWARD HACKING & RÀO CẢN KL")

        title = Text("CẠM BẪY REWARD HACKING VÀ HÌNH PHẠT KULLBACK-LEIBLER", font="Noto Sans", font_size=19, weight=BOLD, color=COLOR_GOLD).to_edge(UP, buff=1.0)
        self.play(FadeIn(title, shift=DOWN*0.2), run_time=0.8)

        # Mathematical objective of RLHF with KL
        eq_box = RoundedRectangle(corner_radius=0.15, height=1.3, width=9.2, fill_color=COLOR_PANEL, fill_opacity=0.9, stroke_color=COLOR_CYAN, stroke_width=1.5).shift(UP * 1.5)
        eq_label = Text("MỤC TIÊU TỐI ƯU HÓA PHẦN THƯỞNG CÓ PHẠT KL TRONG RLHF", font="Noto Sans", font_size=12.0, weight=BOLD, color=COLOR_CYAN).next_to(eq_box, UP, buff=0.1)
        eq_math = MathTex(
            r"\max_{\pi_\theta} \mathbb{E}_{x \sim \mathcal{D}, y \sim \pi_\theta} \left[ r_\psi(x, y) \right] - \beta \, \mathbb{D}_{\text{KL}}\left(\pi_\theta(y \mid x) \parallel \pi_{\text{ref}}(y \mid x)\right)",
            font_size=24,
            color=WHITE
        ).move_to(eq_box)
        self.play(FadeIn(eq_box), FadeIn(eq_label), Write(eq_math), run_time=1.2)

        # Left Column: Reward Hacking pathology
        hack_box = RoundedRectangle(corner_radius=0.12, height=2.8, width=4.5, fill_color=COLOR_PANEL, fill_opacity=0.85, stroke_color=COLOR_ROSE, stroke_width=1.5).shift(LEFT * 2.8 + DOWN * 1.0)
        hack_title = Text("HIỆN TƯỢNG REWARD HACKING", font="Noto Sans", font_size=12, weight=BOLD, color=COLOR_ROSE).next_to(hack_box, UP, buff=0.1)
        h1 = Text("• Mô hình khai thác lỗ hổng của Reward Model", font="Noto Sans", font_size=12.0, color=COLOR_TEXT).move_to(hack_box.get_center() + UP * 0.8)
        h2 = Text("• Viết dài dòng bất thường để lừa điểm", font="Noto Sans", font_size=12.0, color=COLOR_ROSE).move_to(hack_box.get_center() + UP * 0.3)
        h3 = Text("• Điểm thưởng vọt lên đỉnh cao giả tạo", font="Noto Sans", font_size=12.0, color=COLOR_GOLD).move_to(hack_box.get_center() + DOWN * 0.2)
        h4 = Text("• Chất lượng tư duy logic thực tế sụp đổ", font="Noto Sans", font_size=12.0, color=COLOR_ROSE).move_to(hack_box.get_center() + DOWN * 0.7)
        hack_grp = VGroup(hack_box, hack_title, h1, h2, h3, h4)

        # Right Column: Role of KL Divergence
        kl_box = RoundedRectangle(corner_radius=0.12, height=2.8, width=4.5, fill_color=COLOR_PANEL, fill_opacity=0.85, stroke_color=COLOR_GREEN, stroke_width=1.5).shift(RIGHT * 2.8 + DOWN * 1.0)
        kl_title = Text("VAI TRÒ HÌNH HỌC CỦA D_KL", font="Noto Sans", font_size=12, weight=BOLD, color=COLOR_GREEN).next_to(kl_box, UP, buff=0.1)
        k1 = Text("• Sợi dây thun co giãn giữ chân mô hình", font="Noto Sans", font_size=12.0, color=COLOR_TEXT).move_to(kl_box.get_center() + UP * 0.8)
        k2 = Text("• Phạt nặng khi trôi xa phân phối ban đầu", font="Noto Sans", font_size=12.0, color=COLOR_GREEN).move_to(kl_box.get_center() + UP * 0.3)
        k3 = Text("• Hệ số beta cân bằng giữa thưởng và trôi dạt", font="Noto Sans", font_size=12.0, color=COLOR_CYAN).move_to(kl_box.get_center() + DOWN * 0.2)
        k4 = Text("• Bảo tồn năng lực ngôn ngữ tự nhiên", font="Noto Sans", font_size=12.0, color=COLOR_GOLD).move_to(kl_box.get_center() + DOWN * 0.7)
        kl_grp = VGroup(kl_box, kl_title, k1, k2, k3, k4)

        self.play(FadeIn(hack_grp, shift=RIGHT*0.2), FadeIn(kl_grp, shift=LEFT*0.2), run_time=1.2)
        self.wait(2.0)


# ==============================================================================
# SCENE 4: DPO MATHEMATICAL DERIVATION (04:25 - 05:55)
# ==============================================================================
class Tap16Scene04Telemetry(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "PHÉP BIẾN ĐỔI ĐẠI SỐ KỲ DIỆU CỦA DPO")

        title = Text("ĐỘT PHÁ CỦA DPO: TIÊU BIẾN HÀM PHÂN HOẠCH Z(X)", font="Noto Sans", font_size=20, weight=BOLD, color=COLOR_GOLD).to_edge(UP, buff=1.0)
        self.play(FadeIn(title, shift=DOWN*0.2), run_time=0.8)

        # Step 1: Closed-form optimal policy
        box1 = RoundedRectangle(corner_radius=0.12, height=1.3, width=9.2, fill_color=COLOR_PANEL, fill_opacity=0.9, stroke_color=COLOR_CYAN, stroke_width=1.5).shift(UP * 1.5)
        lbl1_hdr = Text("1. Nghiệm giải tích của bài toán tối ưu có phạt KL", font="Noto Sans", font_size=12.0, color=COLOR_CYAN).next_to(box1, UP, buff=0.08)
        math1 = MathTex(
            r"\pi^*(y \mid x) = \frac{1}{Z(x)} \pi_{\text{ref}}(y \mid x) \exp\left(\frac{1}{\beta} r(x, y)\right)",
            font_size=24, color=WHITE
        ).move_to(box1)
        self.play(FadeIn(box1), FadeIn(lbl1_hdr), Write(math1), run_time=1.0)

        # Step 2: Implicit Reward Expression
        box2 = RoundedRectangle(corner_radius=0.12, height=1.3, width=9.2, fill_color=COLOR_PANEL, fill_opacity=0.9, stroke_color=COLOR_GOLD, stroke_width=1.5).shift(DOWN * 0.1)
        lbl2_hdr = Text("2. Rút ngược phần thưởng tiềm ẩn theo tỷ số xác suất (Implicit Reward)", font="Noto Sans", font_size=12.0, color=COLOR_GOLD).next_to(box2, UP, buff=0.08)
        math2 = MathTex(
            r"r(x, y) = \beta \log \frac{\pi^*(y \mid x)}{\pi_{\text{ref}}(y \mid x)} + \beta \log Z(x)",
            font_size=24, color=WHITE
        ).move_to(box2)
        self.play(FadeIn(box2), FadeIn(lbl2_hdr), Write(math2), run_time=1.0)

        # Step 3: Bradley-Terry Cancellation
        box3 = RoundedRectangle(corner_radius=0.12, height=1.3, width=9.2, fill_color=COLOR_PANEL, fill_opacity=0.9, stroke_color=COLOR_GREEN, stroke_width=1.5).shift(DOWN * 1.7)
        lbl3_hdr = Text("3. Thế vào mô hình Bradley-Terry: Hàm phân hoạch Z(x) triệt tiêu hoàn toàn!", font="Noto Sans", font_size=12.0, weight=BOLD, color=COLOR_GREEN).next_to(box3, UP, buff=0.08)
        math3 = MathTex(
            r"P(y_w \succ y_l \mid x) = \sigma\left(r(x, y_w) - r(x, y_l)\right) = \sigma\left(\beta \log \frac{\pi_\theta(y_w \mid x)}{\pi_{\text{ref}}(y_w \mid x)} - \beta \log \frac{\pi_\theta(y_l \mid x)}{\pi_{\text{ref}}(y_l \mid x)}\right)",
            font_size=21, color=WHITE
        ).move_to(box3)
        self.play(FadeIn(box3), FadeIn(lbl3_hdr), Write(math3), run_time=1.2)
        self.wait(2.0)


# ==============================================================================
# SCENE 5: LOSS FUNCTION & GRADIENT DYNAMICS (05:55 - 07:25)
# ==============================================================================
class Tap16Scene05LabExperiment(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "GIẢI PHẪU HÀM MẤT MÁT DPO VÀ GRADIENT ĐỘNG")

        title = Text("HÀM TỔN THẤT DPO VÀ CƠ CHẾ GRADIENT ĐỘNG TỰ ĐIỀU CHỈNH", font="Noto Sans", font_size=19, weight=BOLD, color=COLOR_GOLD).to_edge(UP, buff=1.0)
        self.play(FadeIn(title, shift=DOWN*0.2), run_time=0.8)

        # Master DPO Loss Equation
        loss_box = RoundedRectangle(corner_radius=0.15, height=1.4, width=9.2, fill_color=COLOR_PANEL, fill_opacity=0.9, stroke_color=COLOR_CYAN, stroke_width=1.5).shift(UP * 1.5)
        loss_lbl = Text("CÔNG THỨC HÀM TỔN THẤT DPO (LOSS FUNCTION)", font="Noto Sans", font_size=12.0, weight=BOLD, color=COLOR_CYAN).next_to(loss_box, UP, buff=0.08)
        loss_math = MathTex(
            r"\mathcal{L}_{\text{DPO}}(\pi_\theta; \pi_{\text{ref}}) = - \mathbb{E}_{(x, y_w, y_l) \sim \mathcal{D}} \left[ \log \sigma \left( \beta \log \frac{\pi_\theta(y_w \mid x)}{\pi_{\text{ref}}(y_w \mid x)} - \beta \log \frac{\pi_\theta(y_l \mid x)}{\pi_{\text{ref}}(y_l \mid x)} \right) \right]",
            font_size=21, color=WHITE
        ).move_to(loss_box)
        self.play(FadeIn(loss_box), FadeIn(loss_lbl), Write(loss_math), run_time=1.2)

        # Gradient breakdown
        grad_box = RoundedRectangle(corner_radius=0.15, height=2.8, width=9.2, fill_color=COLOR_PANEL, fill_opacity=0.85, stroke_color=COLOR_GREEN, stroke_width=1.5).shift(DOWN * 1.0)
        grad_header = Text("GIẢI PHẪU ĐẠO HÀM GRADIENT: HAI LỰC ĐẨY KÉO VÀ TRỌNG SỐ ĐỘNG", font="Noto Sans", font_size=12, weight=BOLD, color=COLOR_GREEN).next_to(grad_box, UP, buff=0.08)
        
        grad_math = MathTex(
            r"\nabla_\theta \mathcal{L}_{\text{DPO}} = - \beta \, \underbrace{\sigma\left(\hat{r}_\theta(x, y_l) - \hat{r}_\theta(x, y_w)\right)}_{\text{Dynamic Weight: Higher for Hard Pairs}} \left[ \underbrace{\nabla_\theta \log \pi_\theta(y_w \mid x)}_{\text{Push Up Chosen } y_w} - \underbrace{\nabla_\theta \log \pi_\theta(y_l \mid x)}_{\text{Push Down Rejected } y_l} \right]",
            font_size=19, color=WHITE
        ).move_to(grad_box.get_center() + UP * 0.4)

        desc1_hdr = Text("• Khi mô hình đoán đúng chắc chắn: Hệ số sigma tiến về 0, không lãng phí gradient.", font="Noto Sans", font_size=12.0, color=COLOR_TEXT).move_to(grad_box.get_center() + DOWN * 0.45)
        desc2_hdr = Text("• Khi mô hình phân vân hoặc đoán sai: Hệ số sigma vọt lên 1, dồn toàn lực uốn nắn mô hình!", font="Noto Sans", font_size=12.0, weight=BOLD, color=COLOR_ROSE).move_to(grad_box.get_center() + DOWN * 0.95)

        self.play(FadeIn(grad_box), FadeIn(grad_header), Write(grad_math), run_time=1.4)
        self.play(FadeIn(desc1_hdr), FadeIn(desc2_hdr), run_time=0.9)
        self.wait(2.0)


# ==============================================================================
# SCENE 6: OUTRO & CTA — BRIDGING TO EPISODE 17 (07:25 - 08:35)
# ==============================================================================
class Tap16Scene06Outro(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "TỔNG KẾT & CẦU NỐI KỸ NGHỆ")

        scene_title = Text(
            "BÀN GIAO TRI THỨC // DIRECT PREFERENCE OPTIMIZATION",
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
        # 1. Next Video Card (Episode 17: PPO vs DPO vs KTO vs ORPO)
        next_card = RoundedRectangle(
            corner_radius=0.12, width=3.8, height=2.0,
            fill_color=COLOR_PANEL, fill_opacity=0.7, stroke_color=COLOR_CYAN, stroke_width=1.5
        ).move_to(RIGHT * 3.5 + UP * 1.5)
        next_header = Text("TẬP TIẾP THEO // TẬP 17", font="Noto Sans", font_size=12.5, weight=BOLD, color=COLOR_CYAN)
        next_sub_header = Text("PPO VS DPO VS KTO VS ORPO: 4 TRƯỜNG PHÁI", font="Noto Sans", font_size=12.0, color=COLOR_TEXT).next_to(next_header, DOWN, buff=0.18)
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
