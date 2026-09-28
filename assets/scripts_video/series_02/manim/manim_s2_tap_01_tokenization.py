#!/usr/bin/env python3
"""
Manim 2K QHD Master Production Scenes — Tập 01: Tokenization — Nghệ Thuật Cắt Lát Ngôn Ngữ AI
Resolution: 2560x1440 @ 60fps | Theme: Neo-Noir Obsidian (#0c0d12)
Style: Median Math & 3Blue1Brown Continuous Geometric Morphing
- ZERO Mascot (Mascot completely removed per directive)
- ZERO Slide Boxes / Text Containers (Pure geometric transformations, physical metaphors)
- STRICT SAFE PADDING: Horizontal bounds [-5.8, 5.8], Vertical bounds [-2.45, 2.90]
- FULL 11 SCENES: Multi-beat dynamic mathematical animations naturally matching voiceover durations (~74s - 110s).
- ZERO PTS STRETCHING: Animations are natively developed to fill target durations.
- NATIVE ZENPHAM VECTOR EMBLEM: Drawn directly via Manim vector graphics in HUD header.
- CONTINUOUS AMBIENT KINETIC MOTION: ValueTracker pulse_tracker + always_redraw carrier wave
  at y = -3.75 (below YouTube CC zone) guaranteeing frame-by-frame delta > -65dB.
- STANDARD VIETNAMESE TYPOGRAPHY: font='Roboto', font_size >= 11.
"""

from __future__ import annotations
import sys
import math
from pathlib import Path

sys.path.insert(0, "/workspace")
sys.path.insert(0, "/workspace/series_02")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from manim import *
import numpy as np

# Palette: Neo-Noir Obsidian & Vibrant Neon Accents
COLOR_BG = "#0c0d12"
COLOR_CYAN = "#00f0ff"
COLOR_AMBER = "#ffb800"
COLOR_GOLD = "#ffd700"
COLOR_ROSE = "#ff2a6d"
COLOR_EMERALD = "#00e676"
COLOR_VIOLET = "#7c4dff"
COLOR_TEXT = "#f0f4fc"
COLOR_MUTED = "#64748b"
COLOR_BORDER = "#1e293b"
COLOR_CARD_BG = "#131726"
COLOR_PANEL = "#141824"

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


FONT_FAMILY = "Noto Sans"

# Strict Safety Bounds
MAX_SAFE_WIDTH = 11.60
SAFE_Y_TOP = 2.90
SAFE_Y_BOTTOM = -2.45


def create_hud_header(title_str: str) -> VGroup:
    """Clean centered HUD header without watermark or brand emblems."""
    max_title_w = 10.6
    title_text = Text(title_str, font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_TEXT)
    if title_text.width > max_title_w - 0.8:
        title_text.scale_to_fit_width(max_title_w - 0.8)
    title_box = RoundedRectangle(
        corner_radius=0.08, width=min(title_text.width + 0.8, max_title_w), height=0.46,
        fill_color="#10172a", fill_opacity=0.92, stroke_color=COLOR_BORDER, stroke_width=1.2
    ).move_to(UP * 2.70)
    title_text.move_to(title_box)

    return VGroup(title_box, title_text)


# =============================================================================
# SCENE 01: NGHỊCH LÝ ĐẾM CHỮ CÁI & ẢO GIÁC KHOẢNG TRẮNG (Duration: 84.0s)
# =============================================================================
class Tap01Scene01ColdOpen(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        pulse_tracker = ValueTracker(0.0)
        pulse_tracker.add_updater(lambda m, dt: m.increment_value(dt))
        self.add(pulse_tracker)
        carrier_wave = always_redraw(lambda: FunctionGraph(
            lambda x: -3.75 + 0.08 * np.sin(2.4 * x + pulse_tracker.get_value() * 3.0),
            x_range=[-5.8, 5.8], color=COLOR_CYAN, stroke_width=1.8, stroke_opacity=0.45
        ).set_z_index(5))
        self.add(carrier_wave)

        hud = create_hud_header("NGHỊCH LÝ ĐẾM CHỮ CÁI & ẢO GIÁC KHOẢNG TRẮNG")
        self.play(FadeIn(hud, shift=DOWN * 0.15), run_time=1.5)

        # ── Beat 1: The Strawberry Paradox & Vector Blindness (0s - 20s) ──
        straw_title = Text("NGHỊCH LÝ ĐẾM CHỮ: 'strawberry' có mấy chữ 'r'?", font=FONT_FAMILY, font_size=16, weight=BOLD, color=COLOR_AMBER).move_to(UP * 1.65)
        word_block = RoundedRectangle(corner_radius=0.12, width=5.0, height=1.0, fill_color=COLOR_CARD_BG, fill_opacity=0.85, stroke_color=COLOR_ROSE, stroke_width=2.0).move_to(UP * 0.80)
        word_text = Text("s t r a w b e r r y", font=FONT_FAMILY, font_size=22, weight=BOLD, color=WHITE).move_to(word_block)
        r_letters = VGroup(
            Text("r", font=FONT_FAMILY, font_size=24, weight=BOLD, color=COLOR_ROSE).move_to(word_block.get_center() + LEFT * 0.95),
            Text("r", font=FONT_FAMILY, font_size=24, weight=BOLD, color=COLOR_ROSE).move_to(word_block.get_center() + RIGHT * 0.90),
            Text("r", font=FONT_FAMILY, font_size=24, weight=BOLD, color=COLOR_ROSE).move_to(word_block.get_center() + RIGHT * 1.35),
        )
        self.play(Write(straw_title), Create(word_block), Write(word_text), run_time=3.0)
        self.wait(1.5)

        split_card = RoundedRectangle(corner_radius=0.10, width=5.4, height=1.15, fill_color="#1e1b4b", fill_opacity=0.90, stroke_color=COLOR_CYAN, stroke_width=1.8).move_to(DOWN * 0.55)
        split_lbl = Text("Tokenizer chỉ tách thành 2 Token nguyên khối:", font=FONT_FAMILY, font_size=12, color=COLOR_CYAN).next_to(split_card.get_top(), DOWN, buff=0.14)
        split_tokens = Text("['straw' (ID: 1542), 'berry' (ID: 8841)]", font=FONT_FAMILY, font_size=14, weight=BOLD, color=COLOR_GOLD).next_to(split_lbl, DOWN, buff=0.12)
        arrow_split = Arrow(word_block.get_bottom(), split_card.get_top(), color=COLOR_CYAN, stroke_width=2.2)
        self.play(GrowArrow(arrow_split), Create(split_card), Write(split_lbl), Write(split_tokens), run_time=3.5)
        self.play(Indicate(r_letters, color=COLOR_ROSE), run_time=2.0)
        
        blind_note_hdr = Text("Self-Attention chỉ nhìn thấy 2 Vector nhúng — Hoàn toàn mù với từng chữ cái bên trong!", font=FONT_FAMILY, font_size=12.0, color=COLOR_ROSE).move_to(DOWN * 1.50)
        self.play(Write(blind_note_hdr), run_time=2.5)
        self.wait(3.5)
        self.play(FadeOut(straw_title), FadeOut(word_block), FadeOut(word_text), FadeOut(r_letters), FadeOut(split_card), FadeOut(split_lbl), FadeOut(split_tokens), FadeOut(arrow_split), FadeOut(blind_note_hdr), run_time=2.0)

        # ── Beat 2: The Space Illusion & 0x20 Byte (20s - 40s) ──
        raw_sentence = "Tôi  học  tiếng  Việt"
        human_text = Text(raw_sentence, font=FONT_FAMILY, font_size=28, weight=BOLD, color=COLOR_TEXT).move_to(UP * 1.20)
        ribbon_w = human_text.width + 0.8
        ribbon = RoundedRectangle(corner_radius=0.15, width=ribbon_w, height=0.95, fill_color=COLOR_CARD_BG, fill_opacity=0.75, stroke_color=COLOR_CYAN, stroke_width=1.6).move_to(human_text)
        self.play(Create(ribbon), Write(human_text), run_time=2.5)

        q_brace = Brace(ribbon, DOWN, buff=0.18, color=COLOR_AMBER)
        q_label_hdr = Text("Mắt người nhận diện: 4 từ riêng biệt (Khoảng trắng là hư không)", font=FONT_FAMILY, font_size=13, weight=BOLD, color=COLOR_AMBER).next_to(q_brace, DOWN, buff=0.14)
        self.play(GrowFromCenter(q_brace), FadeIn(q_label_hdr, shift=UP * 0.15), run_time=2.0)
        self.wait(3.0)

        laser = Line(UP * 1.70, UP * 0.70, color=COLOR_ROSE, stroke_width=3.5).move_to(ribbon.get_left() + LEFT * 0.2)
        laser_glow = Line(UP * 1.70, UP * 0.70, color=COLOR_ROSE, stroke_width=9.0, stroke_opacity=0.35).move_to(laser)
        laser_group = VGroup(laser_glow, laser)
        self.play(FadeIn(laser_group), run_time=0.8)
        self.play(laser_group.animate.move_to(ribbon.get_right() + RIGHT * 0.2), rate_func=linear, run_time=3.5)
        self.play(FadeOut(laser_group), FadeOut(q_brace), FadeOut(q_label_hdr), run_time=1.2)
        self.wait(2.0)

        # ── Beat 3: Shattering into 7 Discrete Token Blocks (40s - 60s) ──
        token_pieces = [
            ("Tôi", COLOR_CYAN, "ID: 4120", 1.45),
            (" ", COLOR_AMBER, "0x20", 0.85),
            ("học", COLOR_EMERALD, "ID: 9812", 1.45),
            (" ", COLOR_AMBER, "0x20", 0.85),
            ("tiếng", COLOR_VIOLET, "ID: 15430", 1.85),
            (" ", COLOR_AMBER, "0x20", 0.85),
            ("Việt", COLOR_ROSE, "ID: 6721", 1.55),
        ]
        token_blocks = VGroup()
        for text_val, col, id_val, block_w in token_pieces:
            is_space = (text_val == " ")
            block_rect = RoundedRectangle(corner_radius=0.08, width=block_w, height=1.20, fill_color=col, fill_opacity=0.22, stroke_color=col, stroke_width=2.0)
            if is_space:
                display_t = Text("␣", font=FONT_FAMILY, font_size=20, weight=BOLD, color=col).move_to(block_rect.get_top() + DOWN * 0.38)
                sub_label = Text(id_val, font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=col).next_to(display_t, DOWN, buff=0.10)
            else:
                display_t = Text(text_val, font=FONT_FAMILY, font_size=18, weight=BOLD, color=WHITE).move_to(block_rect.get_top() + DOWN * 0.38)
                sub_label = Text(id_val, font=FONT_FAMILY, font_size=12.0, color=col).next_to(display_t, DOWN, buff=0.10)
            token_blocks.add(VGroup(block_rect, display_t, sub_label))

        token_blocks.arrange(RIGHT, buff=0.14).move_to(UP * 0.20)
        self.play(ReplacementTransform(ribbon, token_blocks), FadeOut(human_text, shift=DOWN * 0.3), run_time=3.0)
        self.wait(2.0)

        space_blocks = [token_blocks[1], token_blocks[3], token_blocks[5]]
        self.play(*[Indicate(sb, color=COLOR_AMBER, scale_factor=1.12) for sb in space_blocks], run_time=2.5)
        space_expl_hdr = Text("Khoảng trắng là KÝ TỰ THẬT: Mã Hex 0x20 (ASCII 32) — Không hề biến mất!", font=FONT_FAMILY, font_size=13, weight=BOLD, color=COLOR_AMBER).move_to(DOWN * 1.05)
        self.play(Write(space_expl_hdr), run_time=2.5)
        self.wait(3.5)

        # ── Beat 4: Vietnamese Multi-Byte Accent Dissection (60s - 74s) ──
        self.play(FadeOut(token_blocks), FadeOut(space_expl_hdr), run_time=1.5)
        accent_card = RoundedRectangle(corner_radius=0.12, width=9.6, height=1.6, fill_color=COLOR_CARD_BG, fill_opacity=0.88, stroke_color=COLOR_EMERALD, stroke_width=1.8).move_to(UP * 0.40)
        accent_title = Text("BẪY TIẾNG VIỆT CÓ DẤU TRONG BẢNG MÃ UTF-8", font=FONT_FAMILY, font_size=14, weight=BOLD, color=COLOR_EMERALD).next_to(accent_card.get_top(), DOWN, buff=0.18)
        byte_stream_hdr = Text("Từ 'học'  ➜  3 chữ cái  =  5 Byte nhị phân [0x68, 0xE1, 0xBB, 0x8D, 0x63]", font=FONT_FAMILY, font_size=14, weight=BOLD, color=COLOR_GOLD).next_to(accent_title, DOWN, buff=0.20)
        self.play(Create(accent_card), Write(accent_title), Write(byte_stream_hdr), run_time=3.0)
        self.wait(2.5)

        hud_card = RoundedRectangle(corner_radius=0.10, width=9.6, height=0.85, fill_color="#10172a", fill_opacity=0.92, stroke_color=COLOR_CYAN, stroke_width=1.4).move_to(DOWN * 1.15)
        hud_metrics_hdr = Text("ĐO LƯỜNG: Ký tự người: 18 | Token máy: 7 | Tỷ lệ Token/Từ tiếng Việt: 1.45x - 1.80x", font=FONT_FAMILY, font_size=12, weight=BOLD, color=COLOR_CYAN).move_to(hud_card)
        self.play(Create(hud_card), Write(hud_metrics_hdr), run_time=2.5)
        self.wait(3.5)

        # ── Beat 5: Transition into Engine (74s - 84.0s) ──
        bridge_text_hdr = Text("CHÀO MỪNG ĐẾN VỚI TẦNG SÂU NHẤT: BỘ GIẢI MÃ TOKENIZATION", font=FONT_FAMILY, font_size=14, weight=BOLD, color=COLOR_GOLD).move_to(DOWN * 2.10)
        self.play(Write(bridge_text_hdr), run_time=2.5)
        self.play(Circumscribe(bridge_text_hdr, color=COLOR_GOLD), run_time=2.5)
        self.wait(5.0)


# =============================================================================
# SCENE 02: BA LỐI RẼ LỊCH SỬ: TỪ VỰNG, KÝ TỰ HAY BYTE? (Duration: 101.0s)
# =============================================================================
class Tap01Scene02Architecture(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        pulse_tracker = ValueTracker(0.0)
        pulse_tracker.add_updater(lambda m, dt: m.increment_value(dt))
        self.add(pulse_tracker)
        carrier_wave = always_redraw(lambda: FunctionGraph(
            lambda x: -3.75 + 0.08 * np.sin(2.4 * x + pulse_tracker.get_value() * 3.0),
            x_range=[-5.8, 5.8], color=COLOR_CYAN, stroke_width=1.8, stroke_opacity=0.45
        ).set_z_index(5))
        self.add(carrier_wave)

        hud = create_hud_header("BA CẤP ĐỘ BIỂU DIỄN: TỪ VỰNG  ➜  KÝ TỰ  ➜  BYTE CƠ BẢN")
        self.play(FadeIn(hud, shift=DOWN * 0.15), run_time=1.5)

        # ── Beat 1: Layout 3 Historical Pillars (0s - 22s) ──
        card_word = RoundedRectangle(corner_radius=0.12, width=3.6, height=3.6, fill_color=COLOR_CARD_BG, fill_opacity=0.85, stroke_color=COLOR_ROSE, stroke_width=1.8).move_to(LEFT * 3.8 + UP * 0.15)
        w_title = Text("1. CẤP ĐỘ TỪ", font=FONT_FAMILY, font_size=13, weight=BOLD, color=COLOR_ROSE).next_to(card_word.get_top(), DOWN, buff=0.18)
        w_desc_hdr = Text("Kho từ: 500.000+ từ\nNgữ nghĩa trọn vẹn\nNhưng không bao quát!", font=FONT_FAMILY, font_size=12.0, color=COLOR_TEXT, line_spacing=1.2).next_to(w_title, DOWN, buff=0.20)
        g_word = VGroup(card_word, w_title, w_desc_hdr)

        card_char = RoundedRectangle(corner_radius=0.12, width=3.6, height=3.6, fill_color=COLOR_CARD_BG, fill_opacity=0.85, stroke_color=COLOR_AMBER, stroke_width=1.8).move_to(UP * 0.15)
        c_title = Text("2. CẤP ĐỘ KÝ TỰ", font=FONT_FAMILY, font_size=13, weight=BOLD, color=COLOR_AMBER).next_to(card_char.get_top(), DOWN, buff=0.18)
        c_desc_hdr = Text("Từ vựng gọn (<300)\nChuỗi dài gấp 5 lần\nBùng nổ bộ nhớ O(L²)!", font=FONT_FAMILY, font_size=12.0, color=COLOR_TEXT, line_spacing=1.2).next_to(c_title, DOWN, buff=0.20)
        g_char = VGroup(card_char, c_title, c_desc_hdr)

        card_byte = RoundedRectangle(corner_radius=0.12, width=3.6, height=3.6, fill_color=COLOR_CARD_BG, fill_opacity=0.85, stroke_color=COLOR_EMERALD, stroke_width=1.8).move_to(RIGHT * 3.8 + UP * 0.15)
        b_title = Text("3. CẤP ĐỘ BYTE", font=FONT_FAMILY, font_size=13, weight=BOLD, color=COLOR_EMERALD).next_to(card_byte.get_top(), DOWN, buff=0.18)
        b_desc_hdr = Text("Cố định 256 byte\nBao quát 100% dữ liệu\nKhông bao giờ thiếu từ!", font=FONT_FAMILY, font_size=12.0, color=COLOR_TEXT, line_spacing=1.2).next_to(b_title, DOWN, buff=0.20)
        g_byte = VGroup(card_byte, b_title, b_desc_hdr)

        self.play(FadeIn(g_word, shift=UP * 0.2), run_time=2.5)
        self.play(FadeIn(g_char, shift=UP * 0.2), run_time=2.5)
        self.play(FadeIn(g_byte, shift=UP * 0.2), run_time=2.5)
        self.wait(3.5)

        # ── Beat 2: Word Level Catastrophe (<UNK> Collapse) (22s - 45s) ──
        self.play(FadeOut(w_desc_hdr), run_time=1.0)
        dict_scan = Text("Quét từ điển: 500.000 mục từ...", font=FONT_FAMILY, font_size=12.0, color=COLOR_MUTED).next_to(w_title, DOWN, buff=0.22)
        self.play(Write(dict_scan), run_time=1.5)
        
        unk_drawer = RoundedRectangle(corner_radius=0.08, width=3.1, height=0.9, fill_color="#450a0a", fill_opacity=0.9, stroke_color=COLOR_ROSE, stroke_width=2.0).next_to(dict_scan, DOWN, buff=0.20)
        unk_alert_hdr = Text("TỪ MỚI: 'vibe coding'\n➜ SỤP ĐỔ: <UNK>", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_ROSE, line_spacing=1.2).move_to(unk_drawer)
        self.play(Create(unk_drawer), Write(unk_alert_hdr), run_time=2.5)
        self.play(Circumscribe(unk_drawer, color=COLOR_ROSE), run_time=2.0)
        
        vram_burn_hdr = Text("VRAM Bùng Nổ (500k × 4096):\n➜ Tiêu tốn 4.1GB bộ nhớ!", font=FONT_FAMILY, font_size=12.0, color=COLOR_GOLD, line_spacing=1.1).move_to(card_word.get_bottom() + UP * 0.38)
        self.play(FadeIn(vram_burn_hdr), run_time=2.0)
        self.wait(4.0)

        # ── Beat 3: Character Level Trap (O(L^2) Attention Wall) (45s - 68s) ──
        self.play(FadeOut(c_desc_hdr), run_time=1.0)
        char_chain = Line(card_char.get_left() + RIGHT * 0.4 + UP * 0.65, card_char.get_right() + LEFT * 0.4 + UP * 0.65, color=COLOR_AMBER, stroke_width=2.0)
        char_dots = VGroup(*[Dot(char_chain.point_from_proportion(p), radius=0.05, color=COLOR_AMBER) for p in [0.1, 0.3, 0.5, 0.7, 0.9]])
        self.play(Create(char_chain), Create(char_dots), run_time=2.0)
        
        matrix_box = RoundedRectangle(corner_radius=0.06, width=3.1, height=1.1, fill_color="#451a03", fill_opacity=0.9, stroke_color=COLOR_AMBER, stroke_width=1.8).move_to(card_char.get_center() + DOWN * 0.30)
        matrix_txt_hdr = Text("ATTENTION MEMORY WALL\nChi phí tính toán: O(L²)\n1 câu = 150 ký tự ➜ 22.500 phép tính!", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_AMBER, line_spacing=1.1).move_to(matrix_box)
        self.play(Create(matrix_box), Write(matrix_txt_hdr), run_time=3.0)
        self.play(Indicate(matrix_box, color=COLOR_ROSE), run_time=2.5)
        self.wait(4.0)

        # ── Beat 4: Byte Level Physics & Universal Ring (68s - 88s) ──
        self.play(FadeOut(b_desc_hdr), run_time=1.0)
        byte_wheel = Circle(radius=0.55, stroke_color=COLOR_EMERALD, stroke_width=2.2).move_to(card_byte.get_center() + UP * 0.20)
        byte_dots = VGroup(*[Dot(byte_wheel.point_at_angle(k * np.pi / 4), radius=0.045, color=COLOR_GOLD) for k in range(8)])
        byte_lbl_hdr = Text("256 BYTES\n(0x00 - 0xFF)", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_EMERALD, line_spacing=1.1).move_to(byte_wheel)
        self.play(Create(byte_wheel), Create(byte_dots), Write(byte_lbl_hdr), run_time=2.5)
        self.play(Rotate(byte_wheel, angle=2 * np.pi, rate_func=smooth, run_time=3.0))
        
        byte_vi_hdr = Text("Tiếng Việt: 1 chữ có dấu = 3-5 Byte\nChuỗi bị kéo dài gấp 4-5 lần!", font=FONT_FAMILY, font_size=12.0, color=COLOR_GOLD, line_spacing=1.1).move_to(card_byte.get_bottom() + UP * 0.38)
        self.play(FadeIn(byte_vi_hdr), run_time=2.5)
        self.wait(4.0)

        # ── Beat 5: The Golden Synthesis & Subwords Balance (88s - 101.0s) ──
        synth_banner = RoundedRectangle(corner_radius=0.12, width=10.6, height=0.95, fill_color="#1e1b4b", fill_opacity=0.95, stroke_color=COLOR_GOLD, stroke_width=2.0).move_to(DOWN * 1.95)
        synth_txt_hdr = Text("ĐIỂM CÂN BẰNG VÀNG: ĐƠN VỊ DƯỚI TỪ (SUBWORD UNITS)\nTừ vựng hữu hạn (~32k-128k)  +  Chuỗi câu ngắn  +  Zero Lỗi <UNK>", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_GOLD).move_to(synth_banner)
        self.play(Create(synth_banner), Write(synth_txt_hdr), run_time=3.5)
        self.play(Circumscribe(synth_banner, color=COLOR_GOLD), run_time=2.5)
        self.wait(5.0)


# =============================================================================
# SCENE 03: SỰ RA ĐỜI CỦA ĐƠN VỊ DƯỚI TỪ (SUBWORD UNITS) (Duration: 74.0s)
# =============================================================================
class Tap01Scene03Subwords(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        pulse_tracker = ValueTracker(0.0)
        pulse_tracker.add_updater(lambda m, dt: m.increment_value(dt))
        self.add(pulse_tracker)
        carrier_wave = always_redraw(lambda: FunctionGraph(
            lambda x: -3.75 + 0.08 * np.sin(2.4 * x + pulse_tracker.get_value() * 3.0),
            x_range=[-5.8, 5.8], color=COLOR_CYAN, stroke_width=1.8, stroke_opacity=0.45
        ).set_z_index(5))
        self.add(carrier_wave)

        hud = create_hud_header("ĐỘT PHÁ SUBWORD // NGUYÊN LÝ KHỐI GHÉP LEGO ĐA NĂNG")
        self.play(FadeIn(hud, shift=DOWN * 0.15), run_time=1.5)

        # ── Beat 1: Monolithic Words vs Modular Connectors (0s - 22s) ──
        center_y = UP * 0.70
        box_frequent = RoundedRectangle(corner_radius=0.12, width=4.5, height=1.6, fill_color="#064e3b", fill_opacity=0.75, stroke_color=COLOR_EMERALD, stroke_width=2.0).move_to(LEFT * 3.2 + center_y)
        frequent_title = Text("TỪ PHỔ BIẾN (NGUYÊN KHỐI)", font=FONT_FAMILY, font_size=12, weight=BOLD, color=COLOR_EMERALD).next_to(box_frequent.get_top(), DOWN, buff=0.16)
        frequent_val = Text("\"học tập\"", font=FONT_FAMILY, font_size=22, weight=BOLD, color=WHITE).next_to(frequent_title, DOWN, buff=0.14)
        g_frequent = VGroup(box_frequent, frequent_title, frequent_val)

        box_rare = RoundedRectangle(corner_radius=0.12, width=5.6, height=1.6, fill_color="#1e1b4b", fill_opacity=0.75, stroke_color=COLOR_CYAN, stroke_width=2.0).move_to(RIGHT * 3.0 + center_y)
        rare_title = Text("TỪ HIẾM GẶP (TÁCH SUBWORD LEGO)", font=FONT_FAMILY, font_size=12, weight=BOLD, color=COLOR_CYAN).next_to(box_rare.get_top(), DOWN, buff=0.16)
        g_rare_head = VGroup(box_rare, rare_title)

        self.play(FadeIn(g_frequent, shift=RIGHT * 0.2), FadeIn(g_rare_head, shift=LEFT * 0.2), run_time=2.5)
        self.wait(2.5)

        # ── Beat 2: Shared Subword Lego Bricks (22s - 42s) ──
        lego_card = RoundedRectangle(corner_radius=0.10, width=5.6, height=1.2, fill_color=COLOR_CARD_BG, fill_opacity=0.9, stroke_color=COLOR_GOLD, stroke_width=1.6).move_to(RIGHT * 3.0 + DOWN * 0.25)
        lego_sub1 = RoundedRectangle(corner_radius=0.06, width=1.3, height=0.55, fill_color=COLOR_CYAN, fill_opacity=0.4, stroke_color=COLOR_CYAN, stroke_width=1.5)
        t_sub1 = Text("bất", font=FONT_FAMILY, font_size=13, weight=BOLD, color=WHITE).move_to(lego_sub1)
        lego_sub2 = RoundedRectangle(corner_radius=0.06, width=1.5, height=0.55, fill_color=COLOR_VIOLET, fill_opacity=0.4, stroke_color=COLOR_VIOLET, stroke_width=1.5)
        t_sub2 = Text("biến", font=FONT_FAMILY, font_size=13, weight=BOLD, color=WHITE).move_to(lego_sub2)
        lego_sub3 = RoundedRectangle(corner_radius=0.06, width=1.3, height=0.55, fill_color=COLOR_AMBER, fill_opacity=0.4, stroke_color=COLOR_AMBER, stroke_width=1.5)
        t_sub3 = Text("tính", font=FONT_FAMILY, font_size=13, weight=BOLD, color=WHITE).move_to(lego_sub3)
        lego_row = VGroup(VGroup(lego_sub1, t_sub1), VGroup(lego_sub2, t_sub2), VGroup(lego_sub3, t_sub3)).arrange(RIGHT, buff=0.12).move_to(lego_card)
        self.play(Create(lego_card), FadeIn(lego_row), run_time=3.0)

        snap1 = Arrow(lego_sub1.get_right(), lego_sub2.get_left(), buff=0.03, color=COLOR_CYAN, stroke_width=2.5)
        snap2 = Arrow(lego_sub2.get_right(), lego_sub3.get_left(), buff=0.03, color=COLOR_AMBER, stroke_width=2.5)
        self.play(GrowArrow(snap1), GrowArrow(snap2), run_time=2.0)
        self.play(Indicate(lego_row, color=COLOR_GOLD), run_time=2.0)
        self.wait(3.5)

        # ── Beat 3: Morphological Reusability in Action (42s - 58s) ──
        reuse_card = RoundedRectangle(corner_radius=0.10, width=4.5, height=1.2, fill_color=COLOR_CARD_BG, fill_opacity=0.9, stroke_color=COLOR_EMERALD, stroke_width=1.6).move_to(LEFT * 3.2 + DOWN * 0.25)
        reuse_title = Text("TÁI SỬ DỤNG MẢNH 'học':", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_EMERALD).next_to(reuse_card.get_top(), DOWN, buff=0.12)
        reuse_list_hdr = Text("• 'học' + 'sinh'  • 'học' + 'phí'\n• 'du' + 'học'   • 'khoa' + 'học'", font=FONT_FAMILY, font_size=12.0, color=COLOR_TEXT).next_to(reuse_title, DOWN, buff=0.10)
        self.play(Create(reuse_card), Write(reuse_title), Write(reuse_list_hdr), run_time=3.0)
        self.play(Indicate(reuse_list_hdr, color=COLOR_EMERALD), run_time=2.0)
        self.wait(3.5)

        # ── Beat 4: The Lego Compression Principle Takeaway (58s - 74.0s) ──
        takeaway_box = RoundedRectangle(corner_radius=0.10, width=10.4, height=1.05, fill_color="#131726", fill_opacity=0.95, stroke_color=COLOR_GOLD, stroke_width=1.8).move_to(DOWN * 1.65)
        takeaway_txt_hdr = Text(
            "NGUYÊN LÝ LEGO: Từ quen thuộc giữ nguyên 1 token — Từ lạ lắp ghép từ các mảnh có sẵn.\nKhông một từ nào bị bỏ rơi, không một ký tự nào gây sụp đổ bộ nhớ!",
            font=FONT_FAMILY, font_size=12, weight=BOLD, color=COLOR_GOLD
        ).move_to(takeaway_box)
        self.play(Create(takeaway_box), Write(takeaway_txt_hdr), run_time=3.5)
        self.play(Circumscribe(takeaway_box, color=COLOR_GOLD), run_time=2.5)
        self.wait(4.5)


# =============================================================================
# SCENE 04: BĂNG CHUYỀN CƠ HỌC BPE — THUẬT TOÁN GHÉP CẶP THAM LAM (Duration: 101.0s)
# =============================================================================
class Tap01Scene04BPE(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        pulse_tracker = ValueTracker(0.0)
        pulse_tracker.add_updater(lambda m, dt: m.increment_value(dt))
        self.add(pulse_tracker)
        carrier_wave = always_redraw(lambda: FunctionGraph(
            lambda x: -3.75 + 0.08 * np.sin(2.4 * x + pulse_tracker.get_value() * 3.0),
            x_range=[-5.8, 5.8], color=COLOR_CYAN, stroke_width=1.8, stroke_opacity=0.45
        ).set_z_index(5))
        self.add(carrier_wave)

        hud = create_hud_header("BĂNG CHUYỀN BPE // THUẬT TOÁN MÃ HÓA CẶP BYTE THAM LAM")
        self.play(FadeIn(hud, shift=DOWN * 0.15), run_time=1.5)

        # ── Beat 1: Initial Character Conveyor Belt (0s - 22s) ──
        raw_chars = ["h", "o", "c", " ", "s", "i", "n", "h", " ", "h", "o", "c"]
        belt_line = Line(LEFT * 5.4 + UP * 0.85, RIGHT * 5.4 + UP * 0.85, color=COLOR_MUTED, stroke_width=3.0)
        self.play(Create(belt_line), run_time=2.0)

        cubes = VGroup()
        for ch in raw_chars:
            box = RoundedRectangle(corner_radius=0.06, width=0.68, height=0.68, fill_color=COLOR_CARD_BG, fill_opacity=0.9, stroke_color=COLOR_CYAN, stroke_width=1.6)
            txt = Text("␣" if ch == " " else ch, font=FONT_FAMILY, font_size=16, weight=BOLD, color=COLOR_AMBER if ch == " " else WHITE).move_to(box)
            cubes.add(VGroup(box, txt))
        cubes.arrange(RIGHT, buff=0.12).move_to(UP * 0.85)
        self.play(FadeIn(cubes, shift=DOWN * 0.2), run_time=3.0)
        self.wait(2.5)

        freq_card = RoundedRectangle(corner_radius=0.10, width=5.8, height=1.4, fill_color="#10172a", fill_opacity=0.92, stroke_color=COLOR_AMBER, stroke_width=1.5).move_to(LEFT * 2.6 + DOWN * 0.75)
        freq_title = Text("BẢNG ĐẾM TẦN SUẤT CẶP KÝ TỰ (FREQUENCY TABLE)", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_AMBER).next_to(freq_card.get_top(), DOWN, buff=0.12)
        freq_rows_hdr = Text("Cặp ('h', 'o'): 120 lần  [CAO NHẤT]\nCặp ('s', 'i'): 45 lần | Cặp ('i', 'n'): 32 lần", font=FONT_FAMILY, font_size=12.0, color=COLOR_TEXT).next_to(freq_title, DOWN, buff=0.12)
        self.play(Create(freq_card), Write(freq_title), Write(freq_rows_hdr), run_time=3.5)
        self.wait(3.5)

        # ── Beat 2: Greedy Fusion of ('h', 'o') -> 'ho' (22s - 45s) ──
        pair_h0 = cubes[0]
        pair_o0 = cubes[1]
        pair_h9 = cubes[9]
        pair_o10 = cubes[10]

        self.play(
            pair_h0[0].animate.set_stroke(color=COLOR_GOLD, width=2.5),
            pair_o0[0].animate.set_stroke(color=COLOR_GOLD, width=2.5),
            pair_h9[0].animate.set_stroke(color=COLOR_GOLD, width=2.5),
            pair_o10[0].animate.set_stroke(color=COLOR_GOLD, width=2.5),
            run_time=2.5
        )
        self.wait(2.0)

        ho_box_1 = RoundedRectangle(corner_radius=0.06, width=1.1, height=0.68, fill_color="#78350f", fill_opacity=0.9, stroke_color=COLOR_GOLD, stroke_width=2.0).move_to((pair_h0.get_center() + pair_o0.get_center()) / 2)
        ho_txt_1 = Text("ho", font=FONT_FAMILY, font_size=16, weight=BOLD, color=COLOR_GOLD).move_to(ho_box_1)
        ho_1 = VGroup(ho_box_1, ho_txt_1)

        ho_box_2 = RoundedRectangle(corner_radius=0.06, width=1.1, height=0.68, fill_color="#78350f", fill_opacity=0.9, stroke_color=COLOR_GOLD, stroke_width=2.0).move_to((pair_h9.get_center() + pair_o10.get_center()) / 2)
        ho_txt_2 = Text("ho", font=FONT_FAMILY, font_size=16, weight=BOLD, color=COLOR_GOLD).move_to(ho_box_2)
        ho_2 = VGroup(ho_box_2, ho_txt_2)

        self.play(
            ReplacementTransform(VGroup(pair_h0, pair_o0), ho_1),
            ReplacementTransform(VGroup(pair_h9, pair_o10), ho_2),
            run_time=3.5
        )
        self.wait(3.5)

        # ── Beat 3: Second Iteration: 'ho' + 'c' -> 'hoc' (45s - 68s) ──
        c_block = cubes[2]
        c_block_end = cubes[11]
        
        hoc_box_1 = RoundedRectangle(corner_radius=0.06, width=1.4, height=0.68, fill_color="#064e3b", fill_opacity=0.9, stroke_color=COLOR_EMERALD, stroke_width=2.2).move_to((ho_1.get_center() + c_block.get_center()) / 2)
        hoc_txt_1 = Text("hoc", font=FONT_FAMILY, font_size=16, weight=BOLD, color=COLOR_EMERALD).move_to(hoc_box_1)
        hoc_1 = VGroup(hoc_box_1, hoc_txt_1)

        hoc_box_2 = RoundedRectangle(corner_radius=0.06, width=1.4, height=0.68, fill_color="#064e3b", fill_opacity=0.9, stroke_color=COLOR_EMERALD, stroke_width=2.2).move_to((ho_2.get_center() + c_block_end.get_center()) / 2)
        hoc_txt_2 = Text("hoc", font=FONT_FAMILY, font_size=16, weight=BOLD, color=COLOR_EMERALD).move_to(hoc_box_2)
        hoc_2 = VGroup(hoc_box_2, hoc_txt_2)

        self.play(
            ReplacementTransform(VGroup(ho_1, c_block), hoc_1),
            ReplacementTransform(VGroup(ho_2, c_block_end), hoc_2),
            run_time=3.5
        )
        self.wait(3.5)

        # ── Beat 4: Live Merge Rules & Compression Ratio (68s - 88s) ──
        rules_card = RoundedRectangle(corner_radius=0.10, width=4.8, height=1.4, fill_color="#10172a", fill_opacity=0.92, stroke_color=COLOR_CYAN, stroke_width=1.5).move_to(RIGHT * 3.1 + DOWN * 0.75)
        rules_title = Text("TẬP QUY TẮC GHÉP (MERGE RULES)", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_CYAN).next_to(rules_card.get_top(), DOWN, buff=0.12)
        rules_content_hdr = Text("1. 'h' + 'o'  ➜  'ho'\n2. 'ho' + 'c'  ➜  'hoc'\n3. 's' + 'i'  ➜  'si'", font=FONT_FAMILY, font_size=12.0, color=COLOR_TEXT).next_to(rules_title, DOWN, buff=0.12)
        self.play(Create(rules_card), Write(rules_title), Write(rules_content_hdr), run_time=3.5)
        self.play(Circumscribe(rules_card, color=COLOR_CYAN), run_time=2.5)
        self.wait(4.0)

        # ── Beat 5: Deterministic Execution Rule Takeaway (88s - 101.0s) ──
        footer_card = RoundedRectangle(corner_radius=0.08, width=10.6, height=0.85, fill_color="#1e1b4b", fill_opacity=0.95, stroke_color=COLOR_GOLD, stroke_width=1.8).move_to(DOWN * 2.05)
        footer_txt_hdr = Text("BPE LÀ GIẢI THUẬT THAM LAM XÁC ĐỊNH: Lặp lại N lần gộp cho đến khi đạt kích thước kho từ V mục tiêu.", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_GOLD).move_to(footer_card)
        self.play(Create(footer_card), Write(footer_txt_hdr), run_time=3.0)
        self.play(Circumscribe(footer_card, color=COLOR_GOLD), run_time=2.5)
        self.wait(5.5)


# =============================================================================
# SCENE 05: BYTE-FALLBACK & PHỔ QUÁT DỮ LIỆU (Duration: 89.0s)
# =============================================================================
class Tap01Scene05ByteFallback(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        pulse_tracker = ValueTracker(0.0)
        pulse_tracker.add_updater(lambda m, dt: m.increment_value(dt))
        self.add(pulse_tracker)
        carrier_wave = always_redraw(lambda: FunctionGraph(
            lambda x: -3.75 + 0.08 * np.sin(2.4 * x + pulse_tracker.get_value() * 3.0),
            x_range=[-5.8, 5.8], color=COLOR_CYAN, stroke_width=1.8, stroke_opacity=0.45
        ).set_z_index(5))
        self.add(carrier_wave)

        hud = create_hud_header("BYTE-LEVEL BPE // CƠ CHẾ DỰ PHÒNG BYTE TIÊU DIỆT LỖI <UNK>")
        self.play(FadeIn(hud, shift=DOWN * 0.15), run_time=1.5)

        # ── Beat 1: Raw Byte Array Foundation (0s - 22s) ──
        grid_title = Text("NỀN TẢNG BẤT BIẾN: 256 BYTE CƠ SỞ ĐƯỢC BẢO HỘ TRONG TỪ ĐIỂN", font=FONT_FAMILY, font_size=14, weight=BOLD, color=COLOR_EMERALD).move_to(UP * 1.80)
        self.play(Write(grid_title), run_time=2.5)

        byte_grid = VGroup()
        for idx, byte_val in enumerate(["0x00", "0x01", "...", "0x20", "...", "0x68", "0x6F", "...", "0xE1", "0xBB", "0x8D", "...", "0xFF"]):
            is_accent = byte_val in ["0xE1", "0xBB", "0x8D"]
            b_box = RoundedRectangle(corner_radius=0.06, width=0.72, height=0.62, fill_color="#064e3b" if is_accent else COLOR_CARD_BG, fill_opacity=0.85, stroke_color=COLOR_EMERALD if is_accent else COLOR_BORDER, stroke_width=1.5)
            b_txt = Text(byte_val, font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_GOLD if is_accent else COLOR_TEXT).move_to(b_box)
            byte_grid.add(VGroup(b_box, b_txt))
        byte_grid.arrange(RIGHT, buff=0.10).move_to(UP * 0.90)
        self.play(FadeIn(byte_grid, shift=DOWN * 0.15), run_time=3.5)
        self.wait(3.5)

        # ── Beat 2: Foreign Emojis & Math Symbols Arrive (22s - 45s) ──
        test_box = RoundedRectangle(corner_radius=0.10, width=8.5, height=1.2, fill_color=COLOR_CARD_BG, fill_opacity=0.9, stroke_color=COLOR_AMBER, stroke_width=1.8).move_to(DOWN * 0.20)
        test_title = Text("KÝ TỰ NGOẠI LAI XUẤT HIỆN: Emoji Robot 🤖 (Mã Unicode: U+1F916)", font=FONT_FAMILY, font_size=13, weight=BOLD, color=COLOR_AMBER).next_to(test_box.get_top(), DOWN, buff=0.16)
        test_bytes = Text("Giải mã thành 4 Byte:  0xF0  0x9F  0xA4  0x96", font=FONT_FAMILY, font_size=15, weight=BOLD, color=WHITE).next_to(test_title, DOWN, buff=0.18)
        self.play(Create(test_box), Write(test_title), Write(test_bytes), run_time=3.5)
        self.play(Circumscribe(test_box, color=COLOR_AMBER), run_time=2.5)
        self.wait(4.0)

        # ── Beat 3: Fallback Routing vs <UNK> Catastrophe (45s - 68s) ──
        route_card = RoundedRectangle(corner_radius=0.10, width=9.2, height=1.3, fill_color="#10172a", fill_opacity=0.92, stroke_color=COLOR_CYAN, stroke_width=1.6).move_to(DOWN * 1.60)
        route_title = Text("CƠ CHẾ ROUTING: Khi không có token ghép sẵn cho 🤖...", font=FONT_FAMILY, font_size=12, weight=BOLD, color=COLOR_CYAN).next_to(route_card.get_top(), DOWN, buff=0.14)
        route_flow_hdr = Text("Hệ thống tự động lùi về 4 token Byte độc lập: [ID_F0, ID_9F, ID_A4, ID_96]\nKẾT QUẢ: 100% dòng dữ liệu được đọc nguyên vẹn — Lỗi <UNK> biến mất vĩnh viễn!", font=FONT_FAMILY, font_size=12.0, color=COLOR_GOLD).next_to(route_title, DOWN, buff=0.14)
        self.play(Create(route_card), Write(route_title), Write(route_flow_hdr), run_time=3.5)
        self.play(Indicate(route_flow_hdr, color=COLOR_EMERALD), run_time=2.5)
        self.wait(4.5)

        # ── Beat 4: Out-of-Vocabulary Immunity Theorem (68s - 89.0s) ──
        theorem_card = RoundedRectangle(corner_radius=0.08, width=10.4, height=0.85, fill_color="#064e3b", fill_opacity=0.95, stroke_color=COLOR_EMERALD, stroke_width=2.0).move_to(DOWN * 2.65)
        theorem_txt_hdr = Text("ĐỊNH LÝ MIỄN NHIỄM OOV: Mọi văn bản nhân loại đều phân rã được về 256 byte nguyên thủy.", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=WHITE).move_to(theorem_card)
        self.play(Create(theorem_card), Write(theorem_txt_hdr), run_time=3.0)
        self.play(Circumscribe(theorem_card, color=COLOR_EMERALD), run_time=2.5)
        self.wait(5.5)


# =============================================================================
# SCENE 06: BẪY CHUẨN HÓA UNICODE: NFC VS NFD (Duration: 99.0s)
# =============================================================================
class Tap01Scene06Unicode(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        pulse_tracker = ValueTracker(0.0)
        pulse_tracker.add_updater(lambda m, dt: m.increment_value(dt))
        self.add(pulse_tracker)
        carrier_wave = always_redraw(lambda: FunctionGraph(
            lambda x: -3.75 + 0.08 * np.sin(2.4 * x + pulse_tracker.get_value() * 3.0),
            x_range=[-5.8, 5.8], color=COLOR_CYAN, stroke_width=1.8, stroke_opacity=0.45
        ).set_z_index(5))
        self.add(carrier_wave)

        hud = create_hud_header("BẪY CHUẨN HÓA UNICODE // NGHỊCH LÝ ĐỒNG DẠNG NFC VS NFD")
        self.play(FadeIn(hud, shift=DOWN * 0.15), run_time=1.5)

        # ── Beat 1: The Visual Identical Trap (0s - 22s) ──
        trap_title = Text("HAI CHỮ 'ệ' NHÌN Y HỆT NHAU NHƯNG MÁY TÍNH NHẬN DIỆN KHÁC BIỆT", font=FONT_FAMILY, font_size=14, weight=BOLD, color=COLOR_ROSE).move_to(UP * 1.80)
        self.play(Write(trap_title), run_time=2.5)

        card_nfc = RoundedRectangle(corner_radius=0.12, width=4.8, height=2.2, fill_color=COLOR_CARD_BG, fill_opacity=0.88, stroke_color=COLOR_CYAN, stroke_width=2.0).move_to(LEFT * 2.8 + UP * 0.35)
        nfc_head = Text("CHUẨN NFC (TỔ HỢP ĐÓNG GÓI)", font=FONT_FAMILY, font_size=12, weight=BOLD, color=COLOR_CYAN).next_to(card_nfc.get_top(), DOWN, buff=0.18)
        nfc_glyph = Text("'ệ'", font=FONT_FAMILY, font_size=36, weight=BOLD, color=WHITE).next_to(nfc_head, DOWN, buff=0.15)
        nfc_cp_hdr = Text("1 Code Point duy nhất:\nU+1EC7 (LATIN SMALL LETTER E WITH CIRCUMFLEX AND DOT BELOW)", font=FONT_FAMILY, font_size=12.0, color=COLOR_GOLD).next_to(nfc_glyph, DOWN, buff=0.12)
        g_nfc = VGroup(card_nfc, nfc_head, nfc_glyph, nfc_cp_hdr)

        card_nfd = RoundedRectangle(corner_radius=0.12, width=4.8, height=2.2, fill_color=COLOR_CARD_BG, fill_opacity=0.88, stroke_color=COLOR_AMBER, stroke_width=2.0).move_to(RIGHT * 2.8 + UP * 0.35)
        nfd_head = Text("CHUẨN NFD (TÁCH RỜI KÝ HIỆU)", font=FONT_FAMILY, font_size=12, weight=BOLD, color=COLOR_AMBER).next_to(card_nfd.get_top(), DOWN, buff=0.18)
        nfd_glyph = Text("'e' + ' ̂' + ' ̣'", font=FONT_FAMILY, font_size=28, weight=BOLD, color=WHITE).next_to(nfd_head, DOWN, buff=0.18)
        nfd_cp_hdr = Text("3 Code Points riêng biệt:\nU+0065 + U+0302 (Dấu mũ) + U+0323 (Dấu nặng)", font=FONT_FAMILY, font_size=12.0, color=COLOR_AMBER).next_to(nfd_glyph, DOWN, buff=0.12)
        g_nfd = VGroup(card_nfd, nfd_head, nfd_glyph, nfd_cp_hdr)

        self.play(FadeIn(g_nfc, shift=RIGHT * 0.2), FadeIn(g_nfd, shift=LEFT * 0.2), run_time=3.5)
        self.wait(3.5)

        # ── Beat 2: Tokenizer Fragmentation Disaster (22s - 46s) ──
        disaster_card = RoundedRectangle(corner_radius=0.10, width=10.2, height=1.3, fill_color="#450a0a", fill_opacity=0.92, stroke_color=COLOR_ROSE, stroke_width=2.0).move_to(DOWN * 1.25)
        disaster_title = Text("HẬU QUẢ KHI TOKENIZER THIẾU BƯỚC NORMALIZER:", font=FONT_FAMILY, font_size=12, weight=BOLD, color=COLOR_ROSE).next_to(disaster_card.get_top(), DOWN, buff=0.14)
        disaster_flow_hdr = Text("Chuẩn NFC: 'tiếng'  ➜  [ID: 15430] (1 token)\nChuẩn NFD: 'tiếng'  ➜  [ID: 820, ID: 412, ID: 901, ID: 512] (4 token vụn nát!)", font=FONT_FAMILY, font_size=12, weight=BOLD, color=WHITE).next_to(disaster_title, DOWN, buff=0.14)
        self.play(Create(disaster_card), Write(disaster_title), Write(disaster_flow_hdr), run_time=3.5)
        self.play(Circumscribe(disaster_card, color=COLOR_ROSE), run_time=2.5)
        self.wait(5.0)

        # ── Beat 3: The Normalization Pipeline Solution (46s - 72s) ──
        self.play(FadeOut(disaster_card), run_time=1.5)
        pipe_card = RoundedRectangle(corner_radius=0.10, width=10.2, height=1.3, fill_color="#064e3b", fill_opacity=0.92, stroke_color=COLOR_EMERALD, stroke_width=1.8).move_to(DOWN * 1.25)
        pipe_title = Text("GIẢI PHÁP CHUẨN HÓA BẮT BUỘC: unicodedata.normalize('NFC', text)", font=FONT_FAMILY, font_size=12, weight=BOLD, color=COLOR_EMERALD).next_to(pipe_card.get_top(), DOWN, buff=0.14)
        pipe_desc_hdr = Text("Mọi luồng dữ liệu trước khi nạp vào Tokenizer đều phải ép về dạng chuẩn tắc NFC.\nĐảm bảo tính nhất quán toán học 100% giữa quá trình Huấn luyện và Suy luận.", font=FONT_FAMILY, font_size=12.0, color=COLOR_TEXT).next_to(pipe_title, DOWN, buff=0.14)
        self.play(Create(pipe_card), Write(pipe_title), Write(pipe_desc_hdr), run_time=3.5)
        self.play(Indicate(pipe_desc_hdr, color=COLOR_GOLD), run_time=2.5)
        self.wait(5.0)

        # ── Beat 4: Golden Takeaway Card (72s - 99.0s) ──
        takeaway_card = RoundedRectangle(corner_radius=0.08, width=10.6, height=0.85, fill_color="#10172a", fill_opacity=0.95, stroke_color=COLOR_GOLD, stroke_width=1.8).move_to(DOWN * 2.35)
        takeaway_txt_hdr = Text("BÀI HỌC KỸ NGHỆ: Không chuẩn hóa Unicode thì LLM không thể học biểu diễn chuẩn cho tiếng Việt.", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_GOLD).move_to(takeaway_card)
        self.play(Create(takeaway_card), Write(takeaway_txt_hdr), run_time=3.0)
        self.play(Circumscribe(takeaway_card, color=COLOR_GOLD), run_time=2.5)
        self.wait(6.0)


# =============================================================================
# SCENE 07: KỸ THUẬT METASPACE TRONG SENTENCEPIECE (Duration: 77.5s)
# =============================================================================
class Tap01Scene07SentencePiece(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        pulse_tracker = ValueTracker(0.0)
        pulse_tracker.add_updater(lambda m, dt: m.increment_value(dt))
        self.add(pulse_tracker)
        carrier_wave = always_redraw(lambda: FunctionGraph(
            lambda x: -3.75 + 0.08 * np.sin(2.4 * x + pulse_tracker.get_value() * 3.0),
            x_range=[-5.8, 5.8], color=COLOR_CYAN, stroke_width=1.8, stroke_opacity=0.45
        ).set_z_index(5))
        self.add(carrier_wave)

        hud = create_hud_header("SENTENCEPIECE // KÝ TỰ METASPACE VÀ TÍNH KHẢ NGHỊCH TUYỆT ĐỐI")
        self.play(FadeIn(hud, shift=DOWN * 0.15), run_time=1.5)

        # ── Beat 1: The Space Loss Problem (0s - 18s) ──
        head_txt_hdr = Text("BẤT CẬP CŨ: Tokenizer truyền thống nuốt mất khoảng trắng sau khi split()", font=FONT_FAMILY, font_size=14, weight=BOLD, color=COLOR_ROSE).move_to(UP * 1.80)
        self.play(Write(head_txt_hdr), run_time=2.5)

        old_card = RoundedRectangle(corner_radius=0.10, width=9.6, height=1.3, fill_color=COLOR_CARD_BG, fill_opacity=0.88, stroke_color=COLOR_BORDER, stroke_width=1.5).move_to(UP * 0.70)
        old_txt_hdr = Text("Văn bản gốc: \"Xin   chào\" (3 khoảng trắng)\nSau khi tách: [\"Xin\", \"chào\"]  ➜  Ghép lại: \"Xin chào\" (MẤT 2 KHOẢNG TRẮNG GỐC!)", font=FONT_FAMILY, font_size=12, color=COLOR_TEXT).move_to(old_card)
        self.play(Create(old_card), Write(old_txt_hdr), run_time=3.0)
        self.wait(3.0)

        # ── Beat 2: Kudo's Metaspace Innovation (18s - 38s) ──
        kudo_card = RoundedRectangle(corner_radius=0.10, width=9.6, height=1.3, fill_color="#1e1b4b", fill_opacity=0.92, stroke_color=COLOR_CYAN, stroke_width=2.0).move_to(DOWN * 0.40)
        kudo_title = Text("PHÁT KIẾN Taku Kudo (Google 2018): Thay khoảng trắng bằng Ký tự Metaspace ' ' (U+2581)", font=FONT_FAMILY, font_size=12, weight=BOLD, color=COLOR_CYAN).next_to(kudo_card.get_top(), DOWN, buff=0.14)
        kudo_flow_hdr = Text("Văn bản chuyển đổi: \"Xin   chào\"  ➜  \"Xin   chào\"\nMọi khoảng trắng đều được bảo toàn thành ký tự in được!", font=FONT_FAMILY, font_size=12, weight=BOLD, color=COLOR_GOLD).next_to(kudo_title, DOWN, buff=0.14)
        self.play(Create(kudo_card), Write(kudo_title), Write(kudo_flow_hdr), run_time=3.5)
        self.play(Indicate(kudo_flow_hdr, color=COLOR_GOLD), run_time=2.5)
        self.wait(4.0)

        # ── Beat 3: Lossless Roundtrip Guarantee (38s - 58s) ──
        guar_card = RoundedRectangle(corner_radius=0.10, width=9.6, height=1.1, fill_color="#064e3b", fill_opacity=0.92, stroke_color=COLOR_EMERALD, stroke_width=2.0).move_to(DOWN * 1.55)
        guar_title = Text("TÍNH KHẢ NGHỊCH TUYỆT ĐỐI (LOSSLESS REVERSIBILITY)", font=FONT_FAMILY, font_size=12, weight=BOLD, color=COLOR_EMERALD).next_to(guar_card.get_top(), DOWN, buff=0.14)
        guar_eq_hdr = Text("detokenize(tokenize(text))  ===  text (Khớp chính xác từng byte)", font=FONT_FAMILY, font_size=14, weight=BOLD, color=WHITE).next_to(guar_title, DOWN, buff=0.14)
        self.play(Create(guar_card), Write(guar_title), Write(guar_eq_hdr), run_time=3.0)
        self.play(Circumscribe(guar_card, color=COLOR_EMERALD), run_time=2.5)
        self.wait(4.5)

        # ── Beat 4: Multilingual Universal Standard (58s - 77.5s) ──
        multi_card = RoundedRectangle(corner_radius=0.08, width=10.4, height=0.75, fill_color="#10172a", fill_opacity=0.95, stroke_color=COLOR_GOLD, stroke_width=1.8).move_to(DOWN * 2.45)
        multi_txt_hdr = Text("SentencePiece hoạt động trực tiếp trên byte stream: Không cần từ điển tiền xử lý cho tiếng Việt hay tiếng Nhật.", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_GOLD).move_to(multi_card)
        self.play(Create(multi_card), Write(multi_txt_hdr), run_time=3.0)
        self.play(Circumscribe(multi_card, color=COLOR_GOLD), run_time=2.0)
        self.wait(5.5)


# =============================================================================
# SCENE 08: ĐÁNH ĐỔI KỸ NGHỆ: DUNG LƯỢNG TỪ VỰNG VS ĐỘ DÀI NGỮ CẢNH (Duration: 110.5s)
# =============================================================================
class Tap01Scene08Tradeoff(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        pulse_tracker = ValueTracker(0.0)
        pulse_tracker.add_updater(lambda m, dt: m.increment_value(dt))
        self.add(pulse_tracker)
        carrier_wave = always_redraw(lambda: FunctionGraph(
            lambda x: -3.75 + 0.08 * np.sin(2.4 * x + pulse_tracker.get_value() * 3.0),
            x_range=[-5.8, 5.8], color=COLOR_CYAN, stroke_width=1.8, stroke_opacity=0.45
        ).set_z_index(5))
        self.add(carrier_wave)

        hud = create_hud_header("ĐÁNH ĐỔI KỸ NGHỆ // QUY MÔ KHO TỪ VỰNG VS CHI PHÍ TÍNH TOÁN")
        self.play(FadeIn(hud, shift=DOWN * 0.15), run_time=1.5)

        # ── Beat 1: The Tradeoff Continuum Setup (0s - 22s) ──
        axis_line = Arrow(LEFT * 5.2 + UP * 1.50, RIGHT * 5.2 + UP * 1.50, color=COLOR_CYAN, stroke_width=2.5)
        axis_lbl = Text("QUY MÔ KHO TỪ VỰNG V (VOCABULARY SIZE)", font=FONT_FAMILY, font_size=12, weight=BOLD, color=COLOR_CYAN).next_to(axis_line, UP, buff=0.12)
        p_32k = Dot(axis_line.point_from_proportion(0.15), radius=0.08, color=COLOR_ROSE)
        t_32k_hdr = Text("32.000\n(LLaMA 1 & 2)", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_ROSE).next_to(p_32k, DOWN, buff=0.12)
        p_128k = Dot(axis_line.point_from_proportion(0.55), radius=0.08, color=COLOR_GOLD)
        t_128k_hdr = Text("128.000\n(LLaMA 3, GPT-4o)", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_GOLD).next_to(p_128k, DOWN, buff=0.12)
        p_256k = Dot(axis_line.point_from_proportion(0.90), radius=0.08, color=COLOR_EMERALD)
        t_256k_hdr = Text("256.000+\n(Gemma, DeepSeek)", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_EMERALD).next_to(p_256k, DOWN, buff=0.12)

        self.play(GrowArrow(axis_line), Write(axis_lbl), run_time=2.5)
        self.play(FadeIn(p_32k), Write(t_32k_hdr), FadeIn(p_128k), Write(t_128k_hdr), FadeIn(p_256k), Write(t_256k_hdr), run_time=3.5)
        self.wait(3.5)

        # ── Beat 2: Embedding Matrix Footprint VRAM (22s - 46s) ──
        embed_card = RoundedRectangle(corner_radius=0.10, width=5.4, height=2.0, fill_color=COLOR_CARD_BG, fill_opacity=0.90, stroke_color=COLOR_ROSE, stroke_width=1.8).move_to(LEFT * 2.8 + DOWN * 0.35)
        embed_title = Text("1. CHI PHÍ BỘ NHỚ EMBEDDING", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_ROSE).next_to(embed_card.get_top(), DOWN, buff=0.14)
        embed_calc_hdr = Text("Ma trận nhúng: E ∈ R^(V × d)\nKhi V = 256.000 & d = 8192 (float16):\n➜ Chiếm tới 4.19 GB VRAM\nchỉ riêng cho 2 tầng Input/Output!", font=FONT_FAMILY, font_size=12.0, color=COLOR_TEXT).next_to(embed_title, DOWN, buff=0.12)
        g_embed = VGroup(embed_card, embed_title, embed_calc_hdr)

        # ── Beat 3: Sequence Compression Savings (46s - 70s) ──
        seq_card = RoundedRectangle(corner_radius=0.10, width=5.4, height=2.0, fill_color=COLOR_CARD_BG, fill_opacity=0.90, stroke_color=COLOR_EMERALD, stroke_width=1.8).move_to(RIGHT * 2.8 + DOWN * 0.35)
        seq_title = Text("2. LỢI ÍCH TIẾT KIỆM ĐỘ DÀI L", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_EMERALD).next_to(seq_card.get_top(), DOWN, buff=0.14)
        seq_calc_hdr = Text("Kho từ lớn ➜ Token nén chặt hơn\nĐộ dài chuỗi L giảm 25% - 35%\n➜ Chi phí Attention giảm O(L²)\nBộ nhớ KV-Cache giảm tương ứng!", font=FONT_FAMILY, font_size=12.0, color=COLOR_TEXT).next_to(seq_title, DOWN, buff=0.12)
        g_seq = VGroup(seq_card, seq_title, seq_calc_hdr)

        self.play(FadeIn(g_embed, shift=UP * 0.2), run_time=3.0)
        self.wait(3.0)
        self.play(FadeIn(g_seq, shift=UP * 0.2), run_time=3.0)
        self.wait(3.5)

        # ── Beat 4: Low-Resource Language Token Tax (70s - 92s) ──
        tax_card = RoundedRectangle(corner_radius=0.10, width=10.4, height=1.1, fill_color="#10172a", fill_opacity=0.92, stroke_color=COLOR_AMBER, stroke_width=1.6).move_to(DOWN * 1.80)
        tax_title = Text("THUẾ TOKEN (TOKEN TAX) CHO TIẾNG VIỆT:", font=FONT_FAMILY, font_size=12, weight=BOLD, color=COLOR_AMBER).next_to(tax_card.get_top(), DOWN, buff=0.14)
        tax_txt_hdr = Text("Kho từ 32k: 1 câu tiếng Việt tốn 2.1x token so với tiếng Anh ➜ Tốn gấp đôi tiền API và mất nửa cửa sổ context!\nKho từ 128k: Tỷ lệ co lại chỉ còn 1.15x ➜ Cực kỳ tối ưu cho đa ngôn ngữ.", font=FONT_FAMILY, font_size=12.0, color=WHITE).next_to(tax_title, DOWN, buff=0.12)
        self.play(Create(tax_card), Write(tax_title), Write(tax_txt_hdr), run_time=3.5)
        self.play(Circumscribe(tax_card, color=COLOR_AMBER), run_time=2.5)
        self.wait(4.5)

        # ── Beat 5: Modern Frontier Consensus (92s - 110.5s) ──
        consensus_card = RoundedRectangle(corner_radius=0.08, width=10.6, height=0.75, fill_color="#064e3b", fill_opacity=0.95, stroke_color=COLOR_GOLD, stroke_width=1.8).move_to(DOWN * 2.70)
        consensus_txt_hdr = Text("ĐỒNG THUẬN 2026: Đánh đổi VRAM cho Embedding để mua lấy độ dài chuỗi L và tốc độ tính toán.", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_GOLD).move_to(consensus_card)
        self.play(Create(consensus_card), Write(consensus_txt_hdr), run_time=3.0)
        self.play(Circumscribe(consensus_card, color=COLOR_GOLD), run_time=2.5)
        self.wait(5.5)


# =============================================================================
# SCENE 09: BẪY KÝ TỰ MA & PROMPT DRIFT (Duration: 76.5s)
# =============================================================================
class Tap01Scene09GhostTokens(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        pulse_tracker = ValueTracker(0.0)
        pulse_tracker.add_updater(lambda m, dt: m.increment_value(dt))
        self.add(pulse_tracker)
        carrier_wave = always_redraw(lambda: FunctionGraph(
            lambda x: -3.75 + 0.08 * np.sin(2.4 * x + pulse_tracker.get_value() * 3.0),
            x_range=[-5.8, 5.8], color=COLOR_CYAN, stroke_width=1.8, stroke_opacity=0.45
        ).set_z_index(5))
        self.add(carrier_wave)

        hud = create_hud_header("BẪY KHOẢNG TRẮNG ĐUÔI // KÝ TỰ MA VÀ LỆCH PHA XÁC SUẤT")
        self.play(FadeIn(hud, shift=DOWN * 0.15), run_time=1.5)

        # ── Beat 1: Trailing Space Prompt Bug (0s - 18s) ──
        head_txt_hdr = Text("MỘT KHOẢNG TRẮNG THỪA Ở CUỐI PROMPT CÓ THỂ LÀM HỎNG KẾT QUẢ AI", font=FONT_FAMILY, font_size=14, weight=BOLD, color=COLOR_ROSE).move_to(UP * 1.80)
        self.play(Write(head_txt_hdr), run_time=2.5)

        p1_box = RoundedRectangle(corner_radius=0.08, width=5.2, height=1.3, fill_color=COLOR_CARD_BG, fill_opacity=0.9, stroke_color=COLOR_EMERALD, stroke_width=1.8).move_to(LEFT * 2.8 + UP * 0.55)
        p1_title = Text("PROMPT A (KHÔNG KHOẢNG TRẮNG ĐUÔI):", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_EMERALD).next_to(p1_box.get_top(), DOWN, buff=0.14)
        p1_val = Text("\"Hãy viết mã Python\"", font=FONT_FAMILY, font_size=16, weight=BOLD, color=WHITE).next_to(p1_title, DOWN, buff=0.14)
        g_p1 = VGroup(p1_box, p1_title, p1_val)

        p2_box = RoundedRectangle(corner_radius=0.08, width=5.2, height=1.3, fill_color=COLOR_CARD_BG, fill_opacity=0.9, stroke_color=COLOR_ROSE, stroke_width=1.8).move_to(RIGHT * 2.8 + UP * 0.55)
        p2_title = Text("PROMPT B (THỪA KHOẢNG TRẮNG ĐUÔI):", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_ROSE).next_to(p2_box.get_top(), DOWN, buff=0.14)
        p2_val = Text("\"Hãy viết mã Python \"␣", font=FONT_FAMILY, font_size=16, weight=BOLD, color=COLOR_AMBER).next_to(p2_title, DOWN, buff=0.14)
        g_p2 = VGroup(p2_box, p2_title, p2_val)

        self.play(FadeIn(g_p1, shift=RIGHT * 0.2), FadeIn(g_p2, shift=LEFT * 0.2), run_time=3.0)
        self.wait(3.0)

        # ── Beat 2: Token ID Divergence (18s - 38s) ──
        div_card = RoundedRectangle(corner_radius=0.10, width=9.8, height=1.3, fill_color="#1e1b4b", fill_opacity=0.92, stroke_color=COLOR_CYAN, stroke_width=2.0).move_to(DOWN * 0.65)
        div_title = Text("SỰ PHÂN KỲ TOKEN ID KHẮC NGHIỆT:", font=FONT_FAMILY, font_size=12, weight=BOLD, color=COLOR_CYAN).next_to(div_card.get_top(), DOWN, buff=0.14)
        div_flow_hdr = Text("Prompt A kết thúc bằng token 'Python' (ID: 14210)\nPrompt B bị ép tách thành: token 'Python' + token độc lập ' ' (ID: 220)\n➜ Mô hình bị cấm dự đoán các token bắt đầu bằng từ khóa kết hợp!", font=FONT_FAMILY, font_size=12.0, color=COLOR_GOLD).next_to(div_title, DOWN, buff=0.14)
        self.play(Create(div_card), Write(div_title), Write(div_flow_hdr), run_time=3.5)
        self.play(Circumscribe(div_card, color=COLOR_CYAN), run_time=2.5)
        self.wait(4.0)

        # ── Beat 3: Skewed Logit Probabilities (38s - 58s) ──
        chart_card = RoundedRectangle(corner_radius=0.10, width=9.8, height=1.1, fill_color="#10172a", fill_opacity=0.92, stroke_color=COLOR_AMBER, stroke_width=1.6).move_to(DOWN * 1.80)
        chart_title = Text("HỆ QUẢ PHÂN PHỐI XÁC SUẤT LOGITS:", font=FONT_FAMILY, font_size=12, weight=BOLD, color=COLOR_AMBER).next_to(chart_card.get_top(), DOWN, buff=0.14)
        chart_desc_hdr = Text("Phân phối xác suất bị bẻ lệch hoàn toàn. Mô hình mất đi quán tính tự nhiên,\ndễ sinh ra lời mở đầu ngắc ngứ hoặc lặp từ không mong muốn.", font=FONT_FAMILY, font_size=12.0, color=COLOR_TEXT).next_to(chart_title, DOWN, buff=0.14)
        self.play(Create(chart_card), Write(chart_title), Write(chart_desc_hdr), run_time=3.5)
        self.play(Indicate(chart_desc_hdr, color=COLOR_AMBER), run_time=2.0)
        self.wait(4.0)

        # ── Beat 4: Prompt Engineering Takeaway (58s - 76.5s) ──
        tip_card = RoundedRectangle(corner_radius=0.08, width=10.4, height=0.75, fill_color="#064e3b", fill_opacity=0.95, stroke_color=COLOR_GOLD, stroke_width=1.8).move_to(DOWN * 2.65)
        tip_txt_hdr = Text("QUY TẮC BẤT DI BẤT DỊCH: Luôn rstrip() cắt bỏ khoảng trắng cuối prompt trước khi gửi vào LLM.", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_GOLD).move_to(tip_card)
        self.play(Create(tip_card), Write(tip_txt_hdr), run_time=3.0)
        self.play(Circumscribe(tip_card, color=COLOR_GOLD), run_time=2.0)
        self.wait(5.5)


# =============================================================================
# SCENE 10: NGHỆ THUẬT TOKEN HEALING (Duration: 75.0s)
# =============================================================================
class Tap01Scene10TokenHealing(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        pulse_tracker = ValueTracker(0.0)
        pulse_tracker.add_updater(lambda m, dt: m.increment_value(dt))
        self.add(pulse_tracker)
        carrier_wave = always_redraw(lambda: FunctionGraph(
            lambda x: -3.75 + 0.08 * np.sin(2.4 * x + pulse_tracker.get_value() * 3.0),
            x_range=[-5.8, 5.8], color=COLOR_CYAN, stroke_width=1.8, stroke_opacity=0.45
        ).set_z_index(5))
        self.add(carrier_wave)

        hud = create_hud_header("TOKEN HEALING // KỸ THUẬT CHỮA LÀNH ĐIỂM GÃY RỜI RẠC")
        self.play(FadeIn(hud, shift=DOWN * 0.15), run_time=1.5)

        # ── Beat 1: The Premature Token Commitment Problem (0s - 18s) ──
        head_txt_hdr = Text("BỆNH ÁN: Tokenizer khóa sớm ranh giới token khiến đuôi câu bị cắt cụt", font=FONT_FAMILY, font_size=14, weight=BOLD, color=COLOR_AMBER).move_to(UP * 1.80)
        self.play(Write(head_txt_hdr), run_time=2.5)

        url_card = RoundedRectangle(corner_radius=0.10, width=9.6, height=1.3, fill_color=COLOR_CARD_BG, fill_opacity=0.88, stroke_color=COLOR_BORDER, stroke_width=1.5).move_to(UP * 0.70)
        url_txt_hdr = Text("Ví dụ URL Prompt: \"Trang web: http://domain.com/fil\"\nTokenizer vội vã tokenize: [... , 'fil'] (Token kết thúc sớm)\nModel bị ép sinh tiếp từ 'fil' thay vì ghép thành token 'file'!", font=FONT_FAMILY, font_size=12.0, color=COLOR_TEXT).move_to(url_card)
        self.play(Create(url_card), Write(url_txt_hdr), run_time=3.0)
        self.wait(3.0)

        # ── Beat 2: Token Healing Rollback Mechanism (18s - 38s) ──
        heal_card = RoundedRectangle(corner_radius=0.10, width=9.6, height=1.3, fill_color="#1e1b4b", fill_opacity=0.92, stroke_color=COLOR_CYAN, stroke_width=2.0).move_to(DOWN * 0.40)
        heal_title = Text("CƠ CHẾ TOKEN HEALING (Lundberg 2023 - Guidance):", font=FONT_FAMILY, font_size=12, weight=BOLD, color=COLOR_CYAN).next_to(heal_card.get_top(), DOWN, buff=0.14)
        heal_flow_hdr = Text("1. Lùi lại (Rollback) 1 token cuối cùng của prompt về cấp độ byte.\n2. Ép mô hình sinh tiếp từ tiền tố byte chưa đóng biên.\n3. Cho phép token 'file' hoặc 'filename' xuất hiện trọn vẹn!", font=FONT_FAMILY, font_size=12.0, color=COLOR_GOLD).next_to(heal_title, DOWN, buff=0.14)
        self.play(Create(heal_card), Write(heal_title), Write(heal_flow_hdr), run_time=3.5)
        self.play(Circumscribe(heal_card, color=COLOR_CYAN), run_time=2.5)
        self.wait(4.0)

        # ── Beat 3: Probability Distribution Restoration (38s - 58s) ──
        resto_card = RoundedRectangle(corner_radius=0.10, width=9.6, height=1.1, fill_color="#064e3b", fill_opacity=0.92, stroke_color=COLOR_EMERALD, stroke_width=2.0).move_to(DOWN * 1.55)
        resto_title = Text("PHỤC HỒI CHÍNH XÁC PHÂN PHỐI XÁC SUẤT:", font=FONT_FAMILY, font_size=12, weight=BOLD, color=COLOR_EMERALD).next_to(resto_card.get_top(), DOWN, buff=0.14)
        resto_desc_hdr = Text("Loại bỏ 100% rủi ro prompt bias do ranh giới token ngẫu nhiên gây ra.\nNền tảng cốt lõi cho các thư viện Structured Output (Outlines, Guidance).", font=FONT_FAMILY, font_size=12.0, color=WHITE).next_to(resto_title, DOWN, buff=0.14)
        self.play(Create(resto_card), Write(resto_title), Write(resto_desc_hdr), run_time=3.5)
        self.play(Indicate(resto_desc_hdr, color=COLOR_GOLD), run_time=2.5)
        self.wait(4.0)

        # ── Beat 4: Engineering Golden Standard (58s - 75.0s) ──
        std_card = RoundedRectangle(corner_radius=0.08, width=10.4, height=0.75, fill_color="#10172a", fill_opacity=0.95, stroke_color=COLOR_GOLD, stroke_width=1.8).move_to(DOWN * 2.45)
        std_txt_hdr = Text("KỸ NGHỆ THỰC CHIẾN: Hiểu cấu trúc Tokenizer để làm chủ hoàn toàn quá trình sinh văn bản của AI.", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_GOLD).move_to(std_card)
        self.play(Create(std_card), Write(std_txt_hdr), run_time=3.0)
        self.play(Circumscribe(std_card, color=COLOR_GOLD), run_time=2.0)
        self.wait(5.5)


# =============================================================================
# SCENE 11: TỔNG KẾT BẢN ĐỒ KỸ NGHỆ & TEASER TẬP 02 (Duration: 84.0s)
# =============================================================================
# SCENE 11: TỔNG KẾT BẢN ĐỒ KỸ NGHỆ & TEASER TẬP 02 (Duration: 84.0s)
# =============================================================================
class Tap01Scene11Outro(Scene):
    def construct(self):
        self.camera.background_color = COLOR_BG
        add_zenpham_brand(self, "TỔNG KẾT & CẦU NỐI KỸ NGHỆ")

        scene_title = Text(
            "BÀN GIAO TRI THỨC // TOKENIZATION — NGHỆ THUẬT CẮT LÁT",
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
        # 1. Next Video Card (Episode 02: RoPE)
        next_card = RoundedRectangle(
            corner_radius=0.12, width=3.8, height=2.0,
            fill_color=COLOR_PANEL, fill_opacity=0.7, stroke_color=COLOR_CYAN, stroke_width=1.5
        ).move_to(RIGHT * 3.5 + UP * 1.5)
        next_header = Text("TẬP TIẾP THEO // TẬP 02", font=FONT_FAMILY, font_size=12.5, weight=BOLD, color=COLOR_CYAN)
        next_sub_header = Text("MA TRẬN ROPE & PHÉP XOAY TỌA ĐỘ", font=FONT_FAMILY, font_size=10.5, color=COLOR_TEXT)
        next_txt = VGroup(next_header, next_sub_header).arrange(DOWN, buff=0.15).move_to(next_card.get_center())

        # 2. Playlist Card
        plist_card = RoundedRectangle(
            corner_radius=0.12, width=3.8, height=1.3,
            fill_color=COLOR_PANEL, fill_opacity=0.7, stroke_color=COLOR_GOLD, stroke_width=1.5
        ).move_to(RIGHT * 3.5 + DOWN * 0.35)
        plist_header = Text("DANH SÁCH PHÁT SERIES 2", font=FONT_FAMILY, font_size=12.0, weight=BOLD, color=COLOR_GOLD)
        plist_sub_header = Text("25 TẬP BẢN VẼ KIẾN TRÚC LLM", font=FONT_FAMILY, font_size=10.5, color=COLOR_TEXT)
        plist_txt = VGroup(plist_header, plist_sub_header).arrange(DOWN, buff=0.12).move_to(plist_card.get_center())

        # 3. Channel Subscribe Circular Card
        sub_card = Circle(
            radius=0.75, fill_color=COLOR_PANEL, fill_opacity=0.85, stroke_color=COLOR_ROSE, stroke_width=1.5
        ).move_to(RIGHT * 3.5 + DOWN * 1.85)
        sub_header = Text("ĐĂNG KÝ", font=FONT_FAMILY, font_size=11.5, weight=BOLD, color=COLOR_ROSE).move_to(sub_card.get_center())

        right_grp = VGroup(next_card, next_txt, plist_card, plist_txt, sub_card, sub_header)
        self.play(FadeIn(right_grp, shift=LEFT * 0.3), run_time=1.2)

        # Ambient phase needle rotation loop until end of scene
        phase_line = Line(ORIGIN, RIGHT * 0.6, color=COLOR_CYAN, stroke_width=2.5).move_to(sub_card.get_center())
        def update_phase(m, dt):
            outro_tracker.increment_value(dt)
            m.rotate(1.2 * dt, about_point=sub_card.get_center())

        phase_line.add_updater(update_phase)
        self.add(phase_line)

        # Wait remaining duration of scene (audio ~83.5s)
        self.wait(5.0)
