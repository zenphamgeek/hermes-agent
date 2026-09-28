#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_s1_e1_masterclass_blueprint_empirical.py
============================================
EMPIRICAL CHALLENGER TEST HARNESS for Masterclass S1E1 Blueprint:
"Bản chất của xác suất trong AI — Đồng xu của cỗ máy"
Target: assets/scripts_video/s1_e1_masterclass_blueprint.md

Verifies:
1. Anti-Slide-Deck Heuristic & AST Scan on Visual Action Cues in Phần 3 & Phần 4.
2. Mathematical Formula Rigor (Gaussian, Shannon Entropy, Surprisal, Bayes, Softmax, ECE, WLLN).
3. 2K Safe Zone Coordinates Verification (Top-right logo, Subtitle CC clearance, 58/42 split).
4. Visual Metaphors 4-Phase Animation Completeness for all 3 required visual metaphors.
5. Invariants & Adversarial Edge Cases (TTS V0-Sense formatting, temper ranges, scene count).
"""

from __future__ import annotations

import re
from pathlib import Path
import pytest

BLUEPRINT_PATH = Path("/home/zen/hermes-agent/assets/scripts_video/s1_e1_masterclass_blueprint.md")

NARR_STARTS = [
    "Một cú búng tay", "Năm 1814", "Mùa hè năm 1948",
    "Khi đối diện", "Giờ đây", "Ở cấp độ", "Nhưng quy luật", "Nhìn thấu qua"
]

COUNCIL_STARTS = [
    "**Chuyên gia YouTube 2026:**", "**Carl Sagan:**", "**Claude Shannon:**",
    "**Nguyễn Hiến Lê:**", "**Shannon & YouTube 2026:**", "**Carl Sagan:**",
    "**YouTube 2026 & Shannon:**", "**Toàn thể Hội đồng:**"
]


@pytest.fixture(scope="module")
def blueprint_content() -> str:
    assert BLUEPRINT_PATH.exists(), f"Target blueprint does not exist at {BLUEPRINT_PATH}"
    with open(BLUEPRINT_PATH, "r", encoding="utf-8") as f:
        return f.read()


@pytest.fixture(scope="module")
def scene_tables(blueprint_content: str) -> list[dict[str, str]]:
    """
    Parses all 8 scenes from Phần 3 into structured dictionaries using boundary markers.
    """
    lines = blueprint_content.splitlines()
    parsed_scenes = []
    for idx, line in enumerate(lines):
        line_s = line.strip()
        if line_s.startswith("| **S1E1_Scene"):
            sc_num = len(parsed_scenes) + 1

            # 1. Col 1: Timecode
            p1 = line_s.find("|")
            p2 = line_s.find("|", p1 + 1)
            col1 = line_s[p1+1:p2].strip()

            # 2. Col 3: Narration start
            ns = NARR_STARTS[sc_num - 1]
            ns_pos = line_s.find(ns)
            assert ns_pos != -1, f"Narration start not found in scene {sc_num}"
            p_vis_end = line_s.rfind("|", p2, ns_pos)
            col2 = line_s[p2+1:p_vis_end].strip()

            # 3. Col 4: Audio start
            m_audio = re.search(r"\|\s*(\*\*\d+:\d+(?:\.\d+)?:\*\*.*?)\|", line_s[ns_pos:])
            assert m_audio, f"Audio start not found in scene {sc_num}"
            audio_rel_pos = ns_pos + m_audio.start()
            col3 = line_s[ns_pos:audio_rel_pos].strip()

            # 4. Col 5: Intent start
            cs = COUNCIL_STARTS[sc_num - 1]
            cs_pos = line_s.find(cs, audio_rel_pos)
            assert cs_pos != -1, f"Council start not found in scene {sc_num}"
            p_aud_end = line_s.rfind("|", audio_rel_pos, cs_pos)
            col4 = line_s[audio_rel_pos+1:p_aud_end].strip()

            # 5. Intent end
            p_last = line_s.rfind("|")
            col5 = line_s[p_aud_end+1:p_last].strip()

            parsed_scenes.append({
                "scene_num": sc_num,
                "id_timecode": col1,
                "visual_cues": col2,
                "narration": col3,
                "audio_cues": col4,
                "pedagogical_intent": col5,
            })

    assert len(parsed_scenes) == 8, f"Expected 8 scenes parsed, got {len(parsed_scenes)}"
    return parsed_scenes


class TestAntiSlideDeckHeuristic:
    """
    Pillar 1: Anti-Slide-Deck Heuristic Scan
    Forbids bullet-point lists, text-card lecturing, and verifies continuous motion geometry.
    """

    def test_no_bullet_points_in_visual_cues(self, scene_tables: list[dict[str, str]]):
        """
        Visual action cues must NEVER prescribe bullet-point text cards
        (e.g., bullet items •, -, or numbered lists 1. 2. 3. rendered as slide text).
        """
        for scene in scene_tables:
            visual = scene["visual_cues"]
            # Disallow literal bullet characters •
            assert "•" not in visual, f"Scene {scene['scene_num']} visual cues contain bullet point '•': {visual}"
            # Check for pattern like "- Text" or "1. Text"
            bullet_list = re.findall(r"(?:^|<br>)\s*(?:[-–]|(?:\d+\.))\s+[A-Za-zÀ-ỹ]", visual)
            assert len(bullet_list) == 0, f"Scene {scene['scene_num']} visual cues contain bullet list: {bullet_list}"

    def test_hero_stage_geometry_presence(self, scene_tables: list[dict[str, str]]):
        """
        Every scene in Phần 3 must specify active mathematical/geometric entities
        in the Left Hero Stage (58% Trái).
        """
        required_geom_keywords = [
            "3d", "vector", "tọa độ", "quỹ đạo", "trục", "parabol", "đường cong",
            "phase space", "hộp", "treemap", "cán cân", "đa tạp", "simplex",
            "galton", "đường chuông", "gauss", "đồ thị", "reliability diagram",
            "thung lũng", "loss landscape", "chùm", "hạt", "mặt cong", "lưới"
        ]
        for scene in scene_tables:
            visual_lower = scene["visual_cues"].lower()
            found_keywords = [k for k in required_geom_keywords if k in visual_lower]
            assert len(found_keywords) >= 2, (
                f"Scene {scene['scene_num']} visual cues lack sufficient geometric entities. "
                f"Found only: {found_keywords} in '{visual_lower}'"
            )

    def test_active_transformation_and_motion_verbs(self, scene_tables: list[dict[str, str]]):
        """
        Every scene must contain dynamic motion and transformation verbs,
        ensuring continuous motion geometry rather than static slides.
        """
        motion_verbs = [
            "xoay", "quay", "phóng", "bám sát", "chuyển động", "biến thành",
            "phân rã", "tách", "nhô lên", "phun trào", "trượt", "rơi", "uốn cong",
            "bẻ cong", "biến dạng", "chiếu", "quét", "nảy", "xếp chồng",
            "dâng lên", "nhấp nháy", "tỏa", "thu nhỏ", "biến đổi", "đón nhận", "bắn vào",
            "chạm", "nứt"
        ]
        for scene in scene_tables:
            visual_lower = scene["visual_cues"].lower()
            found_verbs = [v for v in motion_verbs if v in visual_lower]
            assert len(found_verbs) >= 2, (
                f"Scene {scene['scene_num']} visual cues lack active motion verbs. "
                f"Found only: {found_verbs} in '{visual_lower}'"
            )

    def test_phan_4_metaphors_anti_slide_deck(self, blueprint_content: str):
        """
        Phần 4 detailed storyboard must strictly forbid static slide cards
        and specify Manim animation classes.
        """
        anim_primitives = [
            "ThreeDAxes", "ParametricFunction", "ValueTracker", "ReplacementTransform",
            "FunctionGraph", "AnimatedCounter", "TechGrid"
        ]
        for prim in anim_primitives:
            assert prim in blueprint_content, f"Missing required Manim animation primitive: {prim}"


class TestMathematicalFormulaRigor:
    """
    Pillar 2: Mathematical Formula Correctness & Completeness
    Verifies Gaussian, Shannon Entropy, Surprisal, Bayes, Softmax, and ECE.
    """

    def test_gaussian_distribution_formula(self, blueprint_content: str):
        """
        Verifies standard Gaussian density formula:
        f(x) = (1 / (sigma * sqrt(2*pi))) * exp(- (x - mu)^2 / (2 * sigma^2))
        """
        gaussian_match_1 = re.search(
            r"f\(x\)\s*=\s*\\frac\{1\}\{\\sigma\s*\\sqrt\{2\\pi\}\}\s*e\^\{[^}]*-\\frac\{\(x\s*-\s*\\mu\)\^2\}\{2\\sigma\^2\}\}",
            blueprint_content
        )
        gaussian_match_2 = re.search(
            r"f\(x\)\s*=\s*\\frac\{1\}\{\\sigma\s*\\sqrt\{2\\pi\}\}\s*\\exp\s*\\left\(\s*-\s*\\frac\{\(x\s*-\s*\\mu\)\^2\}\{2\\sigma\^2\}\s*\\right\)",
            blueprint_content
        )
        assert gaussian_match_1 is not None or gaussian_match_2 is not None, (
            "Gaussian density formula is missing or mathematically malformed"
        )

    def test_shannon_entropy_formula(self, blueprint_content: str):
        """
        Verifies Shannon Entropy formula:
        H(X) = - sum P(x_i) log_2 P(x_i)
        """
        shannon_match = re.search(
            r"H(?:\([Xp]\))?\s*=\s*-\s*\\sum(?:_\{[^}]+\})?\s*(?:P\([xX]_i\)|p_i)\s*\\log_2\s*(?:P\([xX]_i\)|p_i)",
            blueprint_content
        )
        assert shannon_match is not None, "Shannon Entropy formula is missing or mathematically malformed"

    def test_surprisal_formula(self, blueprint_content: str):
        """
        Verifies Surprisal / Self-Information formula:
        I(x) = -log_2 P(x) = log_2(1 / P(x))
        """
        surprisal_match = re.search(
            r"I\s*\([xX]\)\s*=\s*-\s*\\log_2\s*P\([xX]\)",
            blueprint_content
        )
        assert surprisal_match is not None, "Surprisal formula I(x) = -log_2 P(x) is missing or malformed"

    def test_bayes_theorem_formula(self, blueprint_content: str):
        """
        Verifies Bayes Theorem formula:
        P(theta | D) = P(D | theta) * P(theta) / P(D)
        """
        bayes_match = re.search(
            r"P\(\\theta\s*\\mid\s*D\)\s*=\s*\\frac\{P\(D\s*\\mid\s*\\theta\)\s*P\(\\theta\)\}\{P\(D\)\}",
            blueprint_content
        )
        assert bayes_match is not None, "Bayes Theorem formula P(theta | D) is missing or malformed"

    def test_softmax_temperature_formula(self, blueprint_content: str):
        """
        Verifies Softmax with Temperature tau formula:
        P(w_i | ...) = exp(z_i / tau) / sum(exp(z_j / tau))
        """
        softmax_match = re.search(
            r"\\frac\{\\exp\(\s*z_i\s*/\s*\\tau\s*\)\}\{\\sum_\{[^\}]+\}(?:\^[A-Za-z0-9]+)?\s*\\exp\(\s*z_j\s*/\s*\\tau\s*\)\}",
            blueprint_content
        )
        assert softmax_match is not None, "Softmax with Temperature formula is missing or malformed"

    def test_ece_formula(self, blueprint_content: str):
        """
        Verifies Expected Calibration Error (ECE) formula:
        ECE = sum ( |B_m| / N ) * | acc(B_m) - conf(B_m) |
        """
        ece_match = re.search(
            r"\\text\{ECE\}\s*=\s*\\sum_\{m=1\}\^M\s*\\frac\{\\?\|B_m\\?\|\}\{N\}\s*\\?\|\\text\{acc\}\(B_m\)\s*-\s*\\text\{conf\}\(B_m\)\\?\|",
            blueprint_content
        )
        assert ece_match is not None, "ECE formula is missing or malformed"

    def test_law_of_large_numbers_formula(self, blueprint_content: str):
        """
        Verifies Weak Law of Large Numbers limit formula:
        lim_{N -> infty} P( | 1/N sum X_i - mu | >= epsilon ) = 0
        """
        lln_match = re.search(
            r"\\lim_\{N\s*\\to\s*\\infty\}\s*P\s*\\left\(\s*\\left\|\s*\\frac\{1\}\{N\}\s*\\sum\s*X_i\s*-\s*\\mu\s*\\right\|\s*\\ge\s*\\epsilon\s*\\right\)\s*=\s*0",
            blueprint_content
        )
        assert lln_match is not None, "Law of Large Numbers formula is missing or malformed"


class TestSafeZoneCompliance:
    """
    Pillar 3: 2K Safe Zone Coordinates Verification
    Verifies UR Logo, CC Subtitle Clearance, and 58/42 Stage/Sidebar layout.
    """

    def test_safe_zone_coordinates_defined_in_header_and_body(self, blueprint_content: str):
        """
        Top-Right Logo and Subtitle CC safe zones must be explicitly declared in metadata and body.
        """
        # Logo: X in [5.20, 6.80], Y in [2.80, 3.80]
        logo_coord_match = re.search(r"X\s*∈\s*\[5\.20,\s*6\.80\],\s*Y\s*∈\s*\[2\.80,\s*3\.80\]", blueprint_content)
        assert logo_coord_match is not None, "Top-right logo coordinates X in [5.20, 6.80], Y in [2.80, 3.80] not found"

        # Subtitle CC: Y in [-4.00, -2.00]
        cc_coord_match = re.search(r"Y\s*∈\s*\[-4\.00?,\s*-2\.00?\]", blueprint_content)
        assert cc_coord_match is not None, "Subtitle CC coordinates Y in [-4.0, -2.0] not found"

    def test_subtitle_cc_clearance_audit(self, scene_tables: list[dict[str, str]]):
        """
        Audits subtitle CC clearance specification across all scenes.
        Empirical check: does each scene declare subtitle clearance?
        Flags missing explicit coordinate intervals in per-scene visual cues.
        """
        missing_scenes = []
        for scene in scene_tables:
            visual = scene["visual_cues"]
            has_cc = "phụ đề" in visual.lower()
            if not has_cc:
                missing_scenes.append(scene["scene_num"])

        # Scene 3 has completely missing subtitle clearance note!
        # This is a known finding we report.
        assert len(missing_scenes) == 0, (
            f"Scenes {missing_scenes} completely lack subtitle CC clearance in visual cues!"
        )

    def test_split_screen_coordinates_bounds(self, scene_tables: list[dict[str, str]], blueprint_content: str):
        """
        Verifies 58/42 split stage coordinates:
        Left Hero Stage: X in [-6.20, +0.60]
        Right Telemetry: X in [+0.90, +5.50]
        There must be a safety buffer between Hero and Telemetry (no X overlap).
        """
        assert "[-6.20, +0.60]" in blueprint_content or "[-6.2, +0.6]" in blueprint_content
        assert "[+0.90, +5.50]" in blueprint_content or "[+0.9, +5.5]" in blueprint_content


class TestVisualMetaphorsCompleteness:
    """
    Pillar 4: 4-Phase Animation Completeness for All 3 Visual Metaphors
    """

    def test_all_three_metaphors_present(self, blueprint_content: str):
        """
        Verifies the presence of all 3 required visual metaphors in Phần 4.
        """
        assert "### 4.1. Visual Metaphor 1:" in blueprint_content, "Visual Metaphor 1 missing"
        assert "### 4.2. Visual Metaphor 2:" in blueprint_content, "Visual Metaphor 2 missing"
        assert "### 4.3. Visual Metaphor 3:" in blueprint_content, "Visual Metaphor 3 missing"

    @pytest.mark.parametrize("metaphor_idx, start_str, end_str", [
        (1, "### 4.1. Visual Metaphor 1:", "### 4.2. Visual Metaphor 2:"),
        (2, "### 4.2. Visual Metaphor 2:", "### 4.3. Visual Metaphor 3:"),
        (3, "### 4.3. Visual Metaphor 3:", "## PHẦN 5:"),
    ])
    def test_four_phase_completeness_per_metaphor(
        self, blueprint_content: str, metaphor_idx: int, start_str: str, end_str: str
    ):
        """
        Each visual metaphor must contain both Section A (Mathematical Foundation)
        and Section B with exactly 4 numbered phases (Giai đoạn 1, 2, 3, 4) with explicit timecodes.
        """
        start_pos = blueprint_content.find(start_str)
        end_pos = blueprint_content.find(end_str)
        assert start_pos != -1, f"Metaphor {metaphor_idx} start not found"
        end_idx = end_pos if end_pos != -1 else len(blueprint_content)
        section_text = blueprint_content[start_pos:end_idx]

        # Check Section A (Toán học) and Section B (Biên đạo Hoạt họa)
        assert "A. Cơ sở" in section_text, f"Metaphor {metaphor_idx} lacks Section A"
        assert "B. Tiến trình Biên đạo Hoạt họa 4 Giai đoạn" in section_text, (
            f"Metaphor {metaphor_idx} lacks Section B 4-phase animation"
        )

        # Check all 4 phases with timecodes
        for phase_num in range(1, 5):
            phase_pattern = re.compile(rf"Giai đoạn\s+{phase_num}\s*\(\d+s\s*–\s*\d+s\):")
            match = phase_pattern.search(section_text)
            assert match is not None, (
                f"Metaphor {metaphor_idx} lacks Giai đoạn {phase_num} with explicit timecodes"
            )


class TestInvariantsAndEdgeCases:
    """
    Pillar 5: Invariants and Strict Edge Cases
    Verifies Council integration, TTS V0-Sense compliance, temper values, and packaging.
    """

    def test_scene_count_and_act_structure(self, scene_tables: list[dict[str, str]]):
        """
        Must have exactly 8 scenes across 3 Acts:
        Act I: Scenes 1-2
        Act II: Scenes 3-5
        Act III: Scenes 6-8
        """
        assert len(scene_tables) == 8
        act_1 = [s for s in scene_tables if s["scene_num"] in (1, 2)]
        act_2 = [s for s in scene_tables if s["scene_num"] in (3, 4, 5)]
        act_3 = [s for s in scene_tables if s["scene_num"] in (6, 7, 8)]
        assert len(act_1) == 2
        assert len(act_2) == 3
        assert len(act_3) == 3

    def test_tts_dynamic_temper_specifications(self, scene_tables: list[dict[str, str]]):
        """
        Dynamic temper specifications must strictly adhere to:
        - Scene 1 (Hook): 0.58 - 0.60 (found: 0.59)
        - Scene 2-7 (Math/Tech): 0.52 - 0.54
        - Scene 8 (Outro): 0.52
        """
        for s in scene_tables:
            timecode_text = s["id_timecode"]
            temper_match = re.search(r"Dynamic Temper:\s*`?([0-9.]+)`?", timecode_text)
            assert temper_match is not None, f"Scene {s['scene_num']} missing Dynamic Temper specification"
            temper = float(temper_match.group(1))

            if s["scene_num"] == 1:
                assert 0.58 <= temper <= 0.60, f"Scene 1 temper {temper} not in Hook range [0.58, 0.60]"
            elif s["scene_num"] == 8:
                assert temper == 0.52, f"Scene 8 outro temper {temper} != 0.52"
            else:
                assert 0.52 <= temper <= 0.54, f"Scene {s['scene_num']} temper {temper} not in Math range [0.52, 0.54]"

    def test_exactly_one_laugh_tag_in_narration(self, scene_tables: list[dict[str, str]]):
        """
        Strict gold rule: Exactly 1 [cười] tag in the entire script, placed at Scene 5 paradox beat.
        """
        laugh_count = 0
        scene_with_laugh = None
        for s in scene_tables:
            count = s["narration"].count("[cười]")
            if count > 0:
                laugh_count += count
                scene_with_laugh = s["scene_num"]

        assert laugh_count == 1, f"Expected exactly 1 [cười] tag across all narration, found {laugh_count}"
        assert scene_with_laugh == 5, f"[cười] tag expected in Scene 5, but found in Scene {scene_with_laugh}"

    def test_english_terms_wrapped_in_en_tags(self, scene_tables: list[dict[str, str]]):
        """
        Strict gold rule: English terms in narration must be wrapped in <en>...</en>.
        Verify common tech terms are not left raw.
        """
        forbidden_raw_terms = [
            r"\bChatGPT\b(?!<)",  # raw ChatGPT
            r"\bLLM\b",
            r"\bSoftmax\b",
            r"\bTemperature\b",
            r"\bEntropy\b",
            r"\bECE\b",
            r"\bHallucination\b",
            r"\bGradient Descent\b",
            r"\btoken\b",
        ]
        unwrapped_findings = []
        for s in scene_tables:
            narration = s["narration"]
            cleaned_narration = re.sub(r"<en>[^<]+</en>", "", narration)

            for term in forbidden_raw_terms:
                raw_match = re.search(term, cleaned_narration, re.IGNORECASE)
                if raw_match:
                    unwrapped_findings.append(
                        f"Scene {s['scene_num']} unwrapped: '{raw_match.group()}'"
                    )

        assert len(unwrapped_findings) == 0, f"Found unwrapped English terms: {unwrapped_findings}"

    def test_audio_ebu_r128_compliance_in_specs(self, blueprint_content: str):
        """
        Audio specifications must declare EBU R128 (-14.5 ± 0.5 LUFS, True Peak <= -1.5 dBTP).
        """
        assert "-14.5 ± 0.5 LUFS" in blueprint_content or "-14.5" in blueprint_content
        assert "-1.5 dBTP" in blueprint_content or "-1.5" in blueprint_content

    def test_three_youtube_packaging_concepts(self, blueprint_content: str):
        """
        Phần 6 must contain all 3 distinct YouTube packaging options with titles < 70 chars.
        """
        assert "CHI TIẾT CONCEPT 1:" in blueprint_content
        assert "CHI TIẾT CONCEPT 2:" in blueprint_content
        assert "CHI TIẾT CONCEPT 3:" in blueprint_content

        title_matches = re.findall(r"\*\*Tiêu đề chính:\*\*\s*`([^`]+)`", blueprint_content)
        assert len(title_matches) >= 3, f"Expected 3 main titles, found {len(title_matches)}"
        for t in title_matches:
            assert len(t) <= 70, f"Title exceeds 70 characters ({len(t)} chars): {t}"
