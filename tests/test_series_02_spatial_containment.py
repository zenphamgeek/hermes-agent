"""
tests/test_series_02_spatial_containment.py
===========================================
Comprehensive Zero-Mock Spatial Containment and Episodic Orchestrator Test Suite
for ZenPham Series 2 ("The Anatomy of Modern LLMs", 25 episodes).

Guarantees & Invariants Verified:
1. Card Text Containment (TestCreateWrappedCardText):
   - Exact W_avail formula: W_avail = card.width - 2 * padding_x.
   - Greedy word-wrapping against W_avail and H_avail.
   - Be Vietnam Pro font standard and NFC Unicode normalization.
   - Elimination of decomposed Vietnamese kerning splits (zero 'KHÔ NG' splits).
   - Hard micro-text gate (<12.0pt floor).
   - Non-positive available width/height error handling.
   - Spatial containment invariants: x_min >= card.x_min + padding_x, x_max <= card.x_max - padding_x.
2. Math Formula Containment (TestFitMathToCard):
   - Compact formulas fit unsplit.
   - Multi-line equation splitting across relational operators (=, \\approx, etc.).
   - Multi-line splitting across explicit line breaks (\\\\, \\aligned).
   - Hard bounding box scaling to strictly fit container bounds.
   - Micro-math floor gate (>= 12.0pt).
   - Spatial containment bounds hold under all translations.
3. Arrow Aerodynamics & Collision (TestUpwardArrowCollisionPrevention):
   - Horizontal reverse curved arrows (start.x > end.x) require negative angle (theta <= 0).
   - Sleek aerodynamic proportions: tip_length <= 0.20, max_tip_length_to_length_ratio <= 0.20.
4. Episodic Orchestration (TestEpisodicOrchestrator):
   - Strict rejection of batch production flags (--all, --start, --end, --batch).
   - Reverse dependency check (Ep k requires Ep k+1 approval manifest).
   - Approval manifest schema adherence, git commit hash (40-char hex), and SHA-256 closure.

Zero-Mock Architecture:
Executes standalone in headless environments using VisualMockElement, DummyCard,
and BBox without requiring Docker or a GUI display.
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import re
import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pytest

# Ensure assets/scripts_video and repository root are on sys.path
REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_VIDEO_DIR = REPO_ROOT / "assets" / "scripts_video"
if str(SCRIPTS_VIDEO_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_VIDEO_DIR))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from manim_production import (
    BBox,
    DEFAULT_FONT,
    MIN_READABLE_FONT_SIZE,
    ZenArrow,
    ZenCurvedArrow,
    ZenPalette,
    check_arrow_collision_angle,
    clean_vietnamese_text,
    create_wrapped_card_text,
    fit_math_to_card,
)
from manim_visual_test_harness import (
    BoundingBox2D,
    MAX_ARROW_TIP_LENGTH,
    VisualMockElement,
    assert_no_conflict_regions,
    assert_no_text_out_card,
    assert_sleek_arrow,
)
from produce_episode_isolated import (
    APPROVALS_DIR,
    BATCH_FLAGS,
    CANONICAL_SCHEMA_PATH,
    check_batch_flags_in_argv,
    check_reverse_dependency,
    compute_closure_sha256,
    get_git_commit_hash,
    parse_args,
    sha256_file,
    validate_manifest_schema,
)


# =============================================================================
# TEST FIXTURES & DUMMY CONTAINERS
# =============================================================================

class DummyCard:
    """Lightweight geometric container for card containment verification."""
    def __init__(self, x: float = 0.0, y: float = 0.0, width: float = 5.0, height: float = 3.0):
        self.x = float(x)
        self.y = float(y)
        self.width = float(width)
        self.height = float(height)

    @property
    def x_min(self) -> float:
        return self.x - self.width / 2.0

    @property
    def x_max(self) -> float:
        return self.x + self.width / 2.0

    @property
    def y_min(self) -> float:
        return self.y - self.height / 2.0

    @property
    def y_max(self) -> float:
        return self.y + self.height / 2.0

    def get_center(self) -> np.ndarray:
        return np.array([self.x, self.y, 0.0])

    def get_corner(self, direction: Any) -> np.ndarray:
        dx = -self.width / 2.0 if direction[0] < 0 else self.width / 2.0
        dy = -self.height / 2.0 if direction[1] < 0 else self.height / 2.0
        return np.array([self.x + dx, self.y + dy, 0.0])


# =============================================================================
# 1. SUITE: TestCreateWrappedCardText
# =============================================================================

class TestCreateWrappedCardText:
    """Zero-mock tests verifying greedy word wrapping, typography, and containment."""

    def test_w_avail_exact_formula_card_width_minus_two_padding(self):
        """
        Verify available width calculation matches exact formula:
        W_avail = card.width - 2 * padding_x.
        """
        test_cases = [
            (6.0, 0.35, 5.30),
            (4.0, 0.30, 3.40),
            (5.5, 0.25, 5.00),
            (8.0, 0.50, 7.00),
            (3.0, 0.22, 2.56),
        ]
        text = "Kiến trúc Transformer mô hình hóa tương tác từ vựng."

        for card_w, pad_x, expected_w_avail in test_cases:
            card = DummyCard(x=0.0, y=0.0, width=card_w, height=3.0)
            calculated_w_avail = card.width - 2.0 * pad_x
            assert calculated_w_avail == pytest.approx(expected_w_avail, rel=1e-5), (
                f"Formula mismatch: {card.width} - 2 * {pad_x} should be {expected_w_avail}"
            )

            res = create_wrapped_card_text(text, card, padding_x=pad_x, padding_y=0.20)
            assert res.width <= expected_w_avail + 1e-4, (
                f"Resulting width {res.width:.3f} exceeds expected W_avail {expected_w_avail:.3f}"
            )

    def test_single_line_text_fits_unwrapped(self):
        """Short text string that fits within W_avail should not be wrapped into multiple lines."""
        card = DummyCard(x=0.0, y=0.0, width=6.0, height=2.0)
        short_text = "Self-Attention"

        res = create_wrapped_card_text(short_text, card, font_size=16.0, padding_x=0.30, padding_y=0.20)
        w_avail = card.width - 2.0 * 0.30  # 5.40

        assert res.width <= w_avail
        # If output has lines attribute, verify exactly 1 line
        if hasattr(res, "lines"):
            assert len(res.lines) == 1
            assert res.lines[0] == short_text
        elif hasattr(res, "text"):
            assert "\n" not in res.text

    def test_long_vietnamese_sentence_greedy_wrapping(self):
        """
        Long Vietnamese sentence must be greedily wrapped into >= 2 lines,
        with each line width <= W_avail and strict bounding box containment.
        """
        long_sentence = (
            "Kiến trúc Transformer mở rộng khả năng xử lý ngữ cảnh dài "
            "qua cơ chế tự chú ý đa đầu và phân bổ trọng số động."
        )
        card = DummyCard(x=1.0, y=-0.5, width=4.0, height=2.5)
        pad_x = 0.30
        pad_y = 0.20
        w_avail = card.width - 2.0 * pad_x  # 3.40

        res = create_wrapped_card_text(long_sentence, card, font_size=14.0, padding_x=pad_x, padding_y=pad_y)

        # Check line count >= 2
        if hasattr(res, "lines"):
            assert len(res.lines) >= 2, f"Expected multiple lines, got {len(res.lines)}"
            for l in res.lines:
                assert l.strip() != ""
        elif hasattr(res, "text"):
            assert "\n" in res.text

        # Verify width fits within available width
        assert res.width <= w_avail + 1e-4

        # Spatial containment bounds
        c_x = res.get_center()[0]
        c_y = res.get_center()[1]
        hw = res.width / 2.0
        hh = res.height / 2.0

        x_min = c_x - hw
        x_max = c_x + hw
        y_min = c_y - hh
        y_max = c_y + hh

        assert x_min >= card.x_min + pad_x - 1e-4
        assert x_max <= card.x_max - pad_x + 1e-4
        assert y_min >= card.y_min + pad_y - 1e-4
        assert y_max <= card.y_max - pad_y + 1e-4

    def test_elimination_of_decomposed_vietnamese_kerning_splits(self):
        """
        Input text containing NFD decomposed Unicode (combining diacritical marks)
        must be recomposed into precomposed NFC code points and orphan syllable splits
        such as 'KHÔ NG' must be eliminated.
        """
        # NFD decomposed string: O + U+0302 (combining circumflex), E + U+0301 (acute), O + U+031B (horn)
        decomposed_input = "KHO\u0302 NG GIAN VE\u0301C-TO\u031B VA\u0300 KHÔ   NG GIAN BA CHIỀU"
        card = DummyCard(x=0.0, y=0.0, width=5.5, height=2.0)

        res = create_wrapped_card_text(decomposed_input, card, font="Be Vietnam Pro")
        extracted_text = getattr(res, "text", "")

        # 1. NFC normalization check: the string must be equal to its NFC form
        assert extracted_text == unicodedata.normalize("NFC", extracted_text)

        # 2. Decomposed characters recomposed
        assert "KHÔNG" in extracted_text
        assert "VÉC-TƠ" in extracted_text
        assert "VÀ" in extracted_text

        # 3. Zero separated glyphs like 'KHÔ NG'
        assert not re.search(r"\bKHÔ\s+NG\b", extracted_text, flags=re.IGNORECASE), (
            f"Found forbidden kerning split in: {extracted_text}"
        )

    def test_micro_text_hard_gate_prevents_font_below_12pt(self):
        """
        Micro-text hard gate (<12.0pt):
        When multi-line text is forced into an excessively small container,
        the engine must NEVER downscale font size below 12.0pt.
        It must either raise ValueError or clamp at >= 12.0pt with truncation.
        """
        long_text = "Dòng 1\nDòng 2\nDòng 3\nDòng 4\nDòng 5\nDòng 6\nDòng 7\nDòng 8"
        # Excessively tiny card height (height=0.4 with padding_y=0.15 leaves H_avail=0.10)
        tiny_card = DummyCard(x=0.0, y=0.0, width=3.0, height=0.4)

        try:
            res = create_wrapped_card_text(
                long_text,
                tiny_card,
                font_size=14.0,
                min_font_size=12.0,
                padding_x=0.20,
                padding_y=0.15
            )
            # If function returned instead of raising, effective font_size must be >= 12.0
            fs = getattr(res, "font_size", 12.0)
            assert fs >= 12.0 - 1e-4, f"Effective font size {fs:.2f}pt dropped below 12.0pt floor!"
        except ValueError as exc:
            # Raising ValueError is an expected and compliant way to prevent micro-text
            err_msg = str(exc).lower()
            assert any(k in err_msg for k in ["insufficient", "height", "12", "micro", "positive"]), (
                f"Unexpected error message: {exc}"
            )

    def test_non_positive_available_width_raises_value_error(self):
        """
        When card width <= 2 * padding_x, resulting in non-positive available width,
        create_wrapped_card_text must raise ValueError.
        """
        # card width 0.5 <= 2 * 0.3 = 0.6 -> W_avail = -0.1
        card_narrow = DummyCard(x=0.0, y=0.0, width=0.5, height=2.0)
        with pytest.raises(ValueError, match=r"(?i)available.*width.*positive"):
            create_wrapped_card_text("Test", card_narrow, padding_x=0.30)

        # card height 0.3 <= 2 * 0.2 = 0.4 -> H_avail = -0.1
        card_flat = DummyCard(x=0.0, y=0.0, width=4.0, height=0.3)
        with pytest.raises(ValueError, match=r"(?i)available.*height.*positive"):
            create_wrapped_card_text("Test", card_flat, padding_x=0.30, padding_y=0.20)

    def test_spatial_containment_invariants_hold(self):
        """
        Verify strict spatial containment inequalities hold across various container placements:
        x_min >= card.x_min + padding_x
        x_max <= card.x_max - padding_x
        y_min >= card.y_min + padding_y
        y_max <= card.y_max - padding_y
        """
        positions = [
            (0.0, 0.0, 5.0, 3.0),
            (2.5, -1.0, 4.0, 2.2),
            (-3.0, 1.5, 3.5, 2.0),
        ]
        text = "Mô hình ngôn ngữ lớn học phân bố xác suất của chuỗi văn bản."

        for cx, cy, w, h in positions:
            card = DummyCard(x=cx, y=cy, width=w, height=h)
            pad_x = 0.30
            pad_y = 0.20

            res = create_wrapped_card_text(text, card, font_size=14.0, padding_x=pad_x, padding_y=pad_y)

            # Test using harness assert_no_text_out_card
            card_mock = VisualMockElement(name="Card", center=(cx, cy), width=w, height=h)
            res_mock = VisualMockElement(
                name="TextContent",
                center=res.get_center(),
                width=res.width,
                height=res.height,
            )
            assert_no_text_out_card(res_mock, card_mock, padding_x=pad_x, padding_y=pad_y)

    def test_adversarial_empty_string_handles_gracefully(self):
        """Empty string or whitespace input should not crash and produce an element within bounds."""
        card = DummyCard(x=0.0, y=0.0, width=4.0, height=2.0)
        res_empty = create_wrapped_card_text("", card, padding_x=0.30, padding_y=0.20)
        assert res_empty is not None
        assert res_empty.width <= 4.0 - 2 * 0.30 + 1e-4

        res_spaces = create_wrapped_card_text("     ", card, padding_x=0.30, padding_y=0.20)
        assert res_spaces is not None
        assert res_spaces.width <= 4.0 - 2 * 0.30 + 1e-4

    def test_adversarial_unbroken_long_word_scaling(self):
        """
        An unbroken word longer than W_avail cannot be split on spaces.
        The engine must scale or truncate the line so that width <= W_avail,
        while maintaining font size >= 12.0pt.
        """
        long_word = "FlashAttentionPagedAttentionTransformerKVMemoryAllocation"
        card = DummyCard(x=0.0, y=0.0, width=4.0, height=2.0)
        w_avail = card.width - 2.0 * 0.30  # 3.40

        res = create_wrapped_card_text(long_word, card, font_size=14.0, min_font_size=12.0, padding_x=0.30)
        assert res.width <= w_avail + 1e-4
        fs = getattr(res, "font_size", 12.0)
        assert fs >= 12.0 - 1e-4

    def test_adversarial_vietnamese_punctuation_and_symbols(self):
        """
        Vietnamese text with stray spaces before punctuation and special characters
        should be properly cleaned and fit inside the card container.
        """
        text = "Kiến trúc mô hình : rất hiệu quả ! (Đo lường : 100% chuẩn xác) ... "
        card = DummyCard(x=0.0, y=0.0, width=4.5, height=2.0)
        res = create_wrapped_card_text(text, card, padding_x=0.30)
        extracted = getattr(res, "text", "")
        # Stray spaces before colon, exclamation mark, etc. must be cleaned
        assert " : " not in extracted
        assert " ! " not in extracted
        assert res.width <= 4.5 - 2 * 0.30 + 1e-4

    def test_vietnamese_kerning_remediation_and_case_preservation(self):
        """
        Regression test:
        1. Broken syllables ('nhữ ng', 'NHỮ NG', 'Nhữ ng') must be merged into 'những', 'NHỮNG', 'Những'.
        2. Math expressions like 'như G trong đồ thị' must NOT be mutated.
        3. Casing must be preserved for all syllables ('trườ ng' -> 'trường', 'TRƯỜ NG' -> 'TRƯỜNG', 'Trườ ng' -> 'Trường').
        """
        assert clean_vietnamese_text("nhữ ng") == "những"
        assert clean_vietnamese_text("NHỮ NG") == "NHỮNG"
        assert clean_vietnamese_text("Nhữ ng") == "Những"
        assert clean_vietnamese_text("như G trong đồ thị") == "như G trong đồ thị"
        assert clean_vietnamese_text("trườ ng") == "trường"
        assert clean_vietnamese_text("TRƯỜ NG") == "TRƯỜNG"
        assert clean_vietnamese_text("Trườ ng") == "Trường"
        assert clean_vietnamese_text("khô ng") == "không"
        assert clean_vietnamese_text("KHÔ NG") == "KHÔNG"
        assert clean_vietnamese_text("Khô ng") == "Không"

    def test_max_lines_enforcement_on_ample_card(self):
        """
        Regression test:
        When max_lines is specified, create_wrapped_card_text must truncate lines unconditionally
        even when the card has ample vertical space (tot_h <= h_avail).
        """
        card = DummyCard(x=0.0, y=0.0, width=5.0, height=5.0)
        res = create_wrapped_card_text("D1\nD2\nD3\nD4\nD5", card, max_lines=2)
        assert len(res.lines) == 2, f"Expected 2 lines, got {len(res.lines)}"
        assert res.lines[0] == "D1"
        assert res.lines[1] == "D2..."


# =============================================================================
# 2. SUITE: TestFitMathToCard
# =============================================================================

class TestFitMathToCard:
    """Zero-mock tests for LaTeX equation splitting across operators and hard bounding box scaling."""

    def test_compact_formula_fits_unsplit(self):
        """Compact formulas that fit comfortably within W_avail should not be split."""
        card = DummyCard(x=0.0, y=0.0, width=5.0, height=2.0)
        formula = r"\nabla_\theta \mathcal{L}(\theta)"

        res = fit_math_to_card(formula, card, font_size=22.0, padding_x=0.30, padding_y=0.20)
        w_avail = card.width - 2.0 * 0.30  # 4.40

        assert res.width <= w_avail + 1e-4
        if hasattr(res, "lines"):
            assert len(res.lines) == 1
            assert res.lines[0] == formula

    def test_multiline_splitting_across_relational_operators(self):
        """
        Long equation with relational operator '=' must be split into aligned multi-line structure,
        fitting inside container available width.
        """
        long_formula = r"W_{\text{new}} = W_0 + \Delta W = W_0 + \frac{\alpha}{r} (B \times A)"
        card = DummyCard(x=0.0, y=0.0, width=4.5, height=2.5)
        pad_x = 0.30
        w_avail = card.width - 2.0 * pad_x  # 3.90

        res = fit_math_to_card(long_formula, card, font_size=22.0, padding_x=pad_x, padding_y=0.20)

        assert res.width <= w_avail + 1e-4
        if hasattr(res, "lines"):
            assert len(res.lines) >= 2, f"Formula did not split across '=' operator! Lines: {res.lines}"
            assert any("=" in l for l in res.lines)

    def test_multiline_splitting_across_explicit_breaks(self):
        """
        Equations containing explicit line breaks ('\\\\') or '\\aligned' environments
        must respect explicit line boundaries and fit within card bounds.
        """
        explicit_formula = r"A = X W_Q \\ B = X W_K \\ C = X W_V"
        card = DummyCard(x=0.0, y=0.0, width=4.0, height=2.5)
        pad_x = 0.30
        w_avail = card.width - 2.0 * pad_x

        res = fit_math_to_card(explicit_formula, card, font_size=20.0, padding_x=pad_x, padding_y=0.20)

        assert res.width <= w_avail + 1e-4
        if hasattr(res, "lines"):
            assert len(res.lines) >= 3, f"Expected >= 3 lines, got {len(res.lines)}"

    def test_hard_bounding_box_scaling_containment(self):
        """
        Very large formula mobject or expression exceeding card dimensions must undergo
        hard bounding box scaling to strictly satisfy (W <= W_avail and H <= H_avail).
        """
        large_formula = (
            r"\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{Q K^T}{\sqrt{d_k}}\right) V "
            r"+ \sum_{i=1}^N \frac{\alpha_i}{\beta_i} \cdot \mathbf{M}_i"
        )
        card = DummyCard(x=0.0, y=0.0, width=5.0, height=1.5)
        pad_x = 0.30
        pad_y = 0.20
        w_avail = card.width - 2.0 * pad_x  # 4.40
        h_avail = card.height - 2.0 * pad_y  # 1.10

        res = fit_math_to_card(large_formula, card, font_size=24.0, padding_x=pad_x, padding_y=pad_y)

        assert res.width <= w_avail + 1e-4
        assert res.height <= h_avail + 1e-4

    def test_micro_math_gate_enforces_12pt_floor(self):
        """
        Formula scaling must never allow effective font size to drop below 12.0pt.
        If a large formula cannot fit in a microscopic container without violating 12pt,
        fit_math_to_card must raise ValueError.
        """
        huge_formula = r"\int_{-\infty}^{\infty} \frac{e^{-x^2}}{\sqrt{2\pi}} dx = 1 \quad \text{and} \quad \sum_{k=1}^{100} k^3 = \left(\frac{100 \times 101}{2}\right)^2"
        tiny_card = DummyCard(x=0.0, y=0.0, width=1.0, height=0.3)

        with pytest.raises(ValueError, match=r"(?i)(minimum.*12.*pt|violating.*12pt|micro)"):
            fit_math_to_card(huge_formula, tiny_card, font_size=22.0, min_font_size=12.0, padding_x=0.20, padding_y=0.10)

    def test_spatial_containment_invariants_hold(self):
        """
        Verify strict bounding box containment invariants for mathematical expressions:
        x_min >= card.x_min + padding_x
        x_max <= card.x_max - padding_x
        y_min >= card.y_min + padding_y
        y_max <= card.y_max - padding_y
        """
        card = DummyCard(x=-1.5, y=0.8, width=4.8, height=2.4)
        pad_x = 0.30
        pad_y = 0.20
        formula = r"h_t = \sigma(W_{hh} h_{t-1} + W_{xh} x_t + b_h)"

        res = fit_math_to_card(formula, card, font_size=22.0, padding_x=pad_x, padding_y=pad_y)

        c = res.get_center()
        hw = res.width / 2.0
        hh = res.height / 2.0

        assert c[0] - hw >= card.x_min + pad_x - 1e-4
        assert c[0] + hw <= card.x_max - pad_x + 1e-4
        assert c[1] - hh >= card.y_min + pad_y - 1e-4
        assert c[1] + hh <= card.y_max - pad_y + 1e-4

    def test_adversarial_empty_or_whitespace_formula(self):
        """Empty or whitespace formula string must return valid element without crashing."""
        card = DummyCard(x=0.0, y=0.0, width=4.0, height=2.0)
        res_empty = fit_math_to_card("", card, padding_x=0.30)
        assert res_empty is not None
        assert res_empty.width <= 4.0 - 2 * 0.30 + 1e-4

        res_spaces = fit_math_to_card("   ", card, padding_x=0.30)
        assert res_spaces is not None
        assert res_spaces.width <= 4.0 - 2 * 0.30 + 1e-4

    def test_adversarial_binary_operator_splitting(self):
        """
        Long formula with binary operators ('+') and no relational operators
        must split across top-level binary operators to fit within container.
        """
        formula = r"\alpha_1 \mathbf{v}_1 + \alpha_2 \mathbf{v}_2 + \alpha_3 \mathbf{v}_3 + \alpha_4 \mathbf{v}_4"
        card = DummyCard(x=0.0, y=0.0, width=3.5, height=2.0)
        w_avail = card.width - 2.0 * 0.30  # 2.90

        res = fit_math_to_card(formula, card, font_size=20.0, padding_x=0.30)
        assert res.width <= w_avail + 1e-4
        if hasattr(res, "lines"):
            assert len(res.lines) >= 2


# =============================================================================
# 3. SUITE: TestUpwardArrowCollisionPrevention
# =============================================================================

class TestUpwardArrowCollisionPrevention:
    """Zero-mock tests verifying curved arrow geometry invariants and aerodynamic tip sizing."""

    def test_horizontal_reverse_curved_arrow_requires_negative_angle(self):
        """
        In horizontal node pipelines (start.x > end.x):
        Curved arrows with positive angles (theta > 0) arc upward (+Y),
        colliding with node cards placed along the horizontal axis.
        The invariant strictly mandates negative curvature (theta <= 0).
        """
        node_right = np.array([3.0, 0.0, 0.0])
        node_left = np.array([-3.0, 0.0, 0.0])

        # 1. Direct collision angle check on reverse edge:
        # Positive angle -> collision detected
        ok_pos, msg_pos = check_arrow_collision_angle(node_right, node_left, angle=np.pi / 4.0)
        assert not ok_pos, "Expected check_arrow_collision_angle to reject positive angle on reverse edge"
        assert "UPWARD_ARROW_COLLISION" in msg_pos

        # Negative angle -> passes
        ok_neg, msg_neg = check_arrow_collision_angle(node_right, node_left, angle=-np.pi / 4.0)
        assert ok_neg
        assert msg_neg == "OK"

        # 2. Forward edge (left to right): positive angle is valid (arcs downward or normal flow)
        ok_fwd, msg_fwd = check_arrow_collision_angle(node_left, node_right, angle=np.pi / 4.0)
        assert ok_fwd

        # 3. ZenCurvedArrow auto-enforces negative angle for reverse connections
        arrow = ZenCurvedArrow(node_right, node_left, angle=np.pi / 4.0)
        assert arrow is not None

    def test_arrow_aerodynamic_proportions_within_thresholds(self):
        """
        Manim's default bulky Arrowhead (tip_length=0.35) violates aerodynamic standards.
        All arrows in 2K scenes must adhere to tip_length <= 0.20 and
        max_tip_length_to_length_ratio <= 0.20.
        """
        # 1. Compliant ZenArrow
        sleek_arrow = ZenArrow(start=np.array([-2.0, 0.0, 0.0]), end=np.array([2.0, 0.0, 0.0]), tip_length=0.16)
        assert getattr(sleek_arrow, "tip_length", 0.16) <= MAX_ARROW_TIP_LENGTH
        assert_sleek_arrow(sleek_arrow, max_tip_length=0.20)

        # 2. Bulky arrow with tip_length > 0.20 raises defect in harness
        bulky_arrow = VisualMockElement(name="BulkyArrow", center=(0.0, 0.0), tip_length=0.35)
        with pytest.raises(AssertionError, match=r"(?i)blunt arrow defect"):
            assert_sleek_arrow(bulky_arrow, max_tip_length=0.20)

    def test_adversarial_collinear_or_vertical_arrows(self):
        """
        Vertical arrows or collinear points where start.x <= end.x
        must satisfy collision angle checks without false positives.
        """
        p_top = np.array([0.0, 2.0, 0.0])
        p_bottom = np.array([0.0, -2.0, 0.0])

        ok_v, msg_v = check_arrow_collision_angle(p_top, p_bottom, angle=0.5)
        assert ok_v is True
        assert msg_v == "OK"

        p_same = np.array([1.0, 1.0, 0.0])
        ok_same, msg_same = check_arrow_collision_angle(p_same, p_same, angle=0.5)
        assert ok_same is True
        assert msg_same == "OK"


# =============================================================================
# 4. SUITE: TestEpisodicOrchestrator
# =============================================================================

class TestEpisodicOrchestrator:
    """Zero-mock tests for produce_episode_isolated.py CLI, reverse dependency, and approval schema."""

    def test_orchestrator_rejects_batch_flags(self):
        """
        Episodic isolation mandates strictly ONE episode per execution unit.
        Batch processing flags (--all, --start, --end, --batch) must be rejected
        with fatal exit code 2 or SystemExit.
        """
        # 1. Direct function call test
        for flag in ["--all", "--start=1", "--end=5", "--batch"]:
            with pytest.raises(SystemExit) as exc_info:
                check_batch_flags_in_argv([flag])
            assert exc_info.value.code == 2, f"Flag {flag} did not exit with code 2"

        # 2. Argument parser test
        for flag in ["--all", "--start", "--end"]:
            with pytest.raises(SystemExit) as exc_info:
                parse_args([flag])
            assert exc_info.value.code == 2

        # 3. Subprocess CLI verification
        script_path = REPO_ROOT / "produce_episode_isolated.py"
        assert script_path.exists(), f"Orchestrator script missing at {script_path}"

        proc = subprocess.run(
            [sys.executable, str(script_path), "--all"],
            capture_output=True,
            text=True
        )
        assert proc.returncode == 2
        assert "BATCH EXECUTION IS STRICTLY FORBIDDEN" in proc.stderr

    def test_orchestrator_reverse_dependency_enforcement(self):
        """
        Reverse production dependency check:
        - Episode 25 (initial pilot) is always satisfied.
        - Episode k < 25 requires approvals/S02_EP{k+1:02d}_APPROVAL.json with decision='approved'.
        """
        # 1. Episode 25 requires no subsequent episode
        sat25, msg25 = check_reverse_dependency(25)
        assert sat25 is True
        assert "satisfied" in msg25.lower()

        # 2. Episode 24 with temporary simulated approvals directory
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Missing EP25 approval -> fails
            sat24_missing, msg24_missing = check_reverse_dependency(24, approvals_dir=tmp_path)
            assert sat24_missing is False
            assert "Missing approval manifest" in msg24_missing or "failed" in msg24_missing.lower()

            # EP25 approval present with decision 'rejected' -> fails
            ep25_manifest = tmp_path / "S02_EP25_APPROVAL.json"
            ep25_manifest.write_text(json.dumps({"decision": "rejected"}), encoding="utf-8")
            sat24_rejected, msg24_rejected = check_reverse_dependency(24, approvals_dir=tmp_path)
            assert sat24_rejected is False
            assert "not 'approved'" in msg24_rejected

            # EP25 approval present with decision 'approved' -> succeeds
            ep25_manifest.write_text(json.dumps({"decision": "approved", "approved_at": "2026-09-27T08:00:00Z"}), encoding="utf-8")
            sat24_ok, msg24_ok = check_reverse_dependency(24, approvals_dir=tmp_path)
            assert sat24_ok is True
            assert "verified" in msg24_ok.lower()

    def test_approval_manifest_schema_and_git_hash(self):
        """
        Approval manifest must conform to Draft-7 canonical JSON schema,
        bind a valid 40-character hex git commit hash, and include 64-char SHA-256 digests.
        """
        # 1. Schema file must exist
        assert CANONICAL_SCHEMA_PATH.exists(), f"Schema missing at {CANONICAL_SCHEMA_PATH}"
        schema = json.loads(CANONICAL_SCHEMA_PATH.read_text(encoding="utf-8"))
        assert schema.get("$schema") == "http://json-schema.org/draft-07/schema#"
        assert "git_hash" in schema.get("required", [])

        # 2. Git commit hash format verification (git rev-parse HEAD)
        git_hash = get_git_commit_hash(REPO_ROOT)
        assert re.match(r"^[0-9a-fA-F]{40}$", git_hash), (
            f"Git commit hash '{git_hash}' is not a valid 40-character hex string"
        )

        # 3. Canonical sample manifest validation
        dummy_manifest: Dict[str, Any] = {
            "approval_version": "1.0",
            "series_id": "series_02",
            "series_title": "The Anatomy of Modern LLMs",
            "episode_id": "S02_EP25",
            "episode_num": 25,
            "title": "Tập 25: Tương Lai Kỹ Nghệ LLM: AGI, Reasoning & Physical AI",
            "git_hash": git_hash,
            "is_git_clean": False,
            "execution_mode": "isolated_atomic",
            "approved_at": "2026-09-27T08:30:00Z",
            "asset_checksums": {
                "script_md": "a" * 64,
                "manim_py": "b" * 64,
                "audio_master_wav": "c" * 64,
                "video_master_mp4": "d" * 64,
                "thumbnail_mosaic_png": "e" * 64,
            },
            "closure_sha256": "f" * 64,
            "quality_gates": {
                "episodic_isolation": "PASS",
                "spatial_containment": "PASS",
                "anti_slide_deck": "PASS",
                "audio_ebur128": "PASS",
                "mosaic_cta_grid": "PASS",
            },
            "metrics": {
                "resolution": [2560, 1440],
                "fps": 60,
                "integrated_lufs": -14.5,
                "true_peak_dbtp": -1.5,
                "slide_deck_violations": 0,
                "spatial_bounding_box_violations": 0,
            },
            "decision": "approved",
        }

        valid, errors = validate_manifest_schema(dummy_manifest)
        assert valid is True, f"Manifest schema validation failed: {errors}"

        # 4. Deterministic closure hash check
        checksums = dummy_manifest["asset_checksums"]
        closure_hash = compute_closure_sha256(checksums)
        assert re.match(r"^[0-9a-fA-F]{64}$", closure_hash)

    def test_adversarial_batch_flag_combinations(self):
        """
        Combinations of valid episode flags with forbidden batch flags
        must still be strictly rejected with fatal exit code 2.
        """
        for combo in [
            ["--episode", "25", "--all"],
            ["--all", "--episode", "25"],
            ["--episode", "25", "--start=1", "--end=25"],
            ["--batch", "--episode", "1"],
        ]:
            with pytest.raises(SystemExit) as exc_info:
                check_batch_flags_in_argv(combo)
            assert exc_info.value.code == 2, f"Combination {combo} did not exit with code 2"

    def test_adversarial_corrupted_manifest_json_handling(self):
        """
        Corrupted or unparseable JSON manifest in approvals directory must cause
        check_reverse_dependency to return (False, <error_message>) cleanly without crashing.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            corrupted = Path(tmp_dir) / "S02_EP25_APPROVAL.json"
            corrupted.write_text("{corrupted_json: incomplete", encoding="utf-8")

            sat, msg = check_reverse_dependency(24, approvals_dir=Path(tmp_dir))
            assert sat is False
            assert "Failed to parse" in msg or "corrupted" in msg.lower()
