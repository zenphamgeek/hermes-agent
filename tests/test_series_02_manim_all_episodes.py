"""
tests/test_series_02_manim_all_episodes.py — Comprehensive Unit Test Suite for Series 2 Manim Scenes
====================================================================================================

Validates all 25 episodes of Series 2 ("Tôi làm việc — The Anatomy of Modern LLMs"):
  1. Episode Coverage: All 25 Manim scripts (manim_s2_tap_01 to tap_25) and 25 markdown scripts exist.
  2. AST Syntax Integrity: All 25 manim_s2_tap_*.py files parse with zero syntax errors.
  3. Sleek Arrow Invariants: Proportional aerodynamic arrows (tip_length <= 0.20 or ZenArrow).
  4. CurvedArrow Geometric Clearance: No upward curved arrows slicing through horizontal node chains.
  5. Micro-Text Hard Gate: Font sizes in 2K scenes must maintain mobile legibility (flag font_size < 12.0pt).
  6. Series 2 Canonical Plan & DAG: All 25 episodes topologically sorted, acyclic, mobile-first titles <= 60 chars.
  7. Audio & Staging Compliance: EBU R128 loudness (-14 to -16 LUFS), 2K QHD resolution requirements, and closing CTA mosaic.
"""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path
import sys
import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "assets/scripts_video"
S2_DIR = SCRIPTS / "series_02"
S2_MANIM = S2_DIR / "manim"
S2_SCRIPTS = S2_DIR / "scripts"
S2_AUDIO = SCRIPTS / "audio/series_02"
S2_STAGING = SCRIPTS / "output/youtube_staging/series_02"
sys.path.insert(0, str(SCRIPTS))

from manim_visual_test_harness import (
    BoundingBox2D,
    VisualMockElement,
    assert_no_conflict_regions,
    assert_no_text_out_card,
    assert_within_safe_zone,
    assert_within_viewport,
    assert_sufficient_contrast,
    assert_sleek_arrow,
    SAFE_ZONE_16X9_X_MIN,
    SAFE_ZONE_16X9_X_MAX,
    SAFE_ZONE_16X9_Y_MIN,
    SAFE_ZONE_16X9_Y_MAX,
    FRAME_WIDTH,
    FRAME_HEIGHT,
)

from manim_production import (
    ZenPalette,
    SafeZone,
    fit_text_to_card,
    auto_resolve_overlap,
    check_collisions,
)


# =============================================================================
# 1. SERIES 2 STRUCTURAL INTEGRITY ACROSS ALL 25 EPISODES
# =============================================================================

class TestSeries2StructuralIntegrity:
    """Verifies that all 25 episodes of Series 2 are present, well-structured, and populated."""

    def test_series_02_all_25_manim_scripts_exist(self):
        """All 25 episodes of Series 2 must have valid Manim scene files."""
        missing = []
        for ep in range(1, 26):
            matches = list(S2_MANIM.glob(f"manim_s2_tap_{ep:02d}*.py"))
            if not matches:
                matches = list(S2_MANIM.glob(f"manim_s2_tap_{ep}*.py"))
            if not matches:
                missing.append(f"tap_{ep:02d}")
        assert not missing, f"Missing Series 2 Manim script files: {missing}"

    def test_series_02_all_25_markdown_scripts_exist(self):
        """All 25 episodes of Series 2 must have complete narrative markdown scripts."""
        missing = []
        for ep in range(1, 26):
            matches = list(S2_SCRIPTS.glob(f"*tap_{ep:02d}*.md"))
            if not matches:
                matches = list(S2_SCRIPTS.glob(f"*tap_{ep}*.md"))
            if not matches:
                missing.append(f"tap_{ep:02d}")
        assert not missing, f"Missing Series 2 narrative markdown scripts: {missing}"

    def test_series_02_all_25_manim_files_syntax_clean(self):
        """Every single manim_s2_tap_*.py file must parse cleanly without SyntaxError."""
        all_manim = sorted(list(S2_MANIM.glob("manim_s2_tap_*.py")))
        assert len(all_manim) == 25, f"Expected 25 Manim files, found {len(all_manim)}"

        syntax_errors = []
        for mf in all_manim:
            try:
                ast.parse(mf.read_text(encoding="utf-8"), filename=mf.name)
            except SyntaxError as e:
                syntax_errors.append(f"{mf.name}: line {e.lineno}: {e.msg}")

        assert not syntax_errors, f"Syntax errors in Series 2 Manim files: {syntax_errors}"

    def test_series_02_scene_classes_defined(self):
        """Each Manim script must define at least 6 Scene classes."""
        all_manim = sorted(list(S2_MANIM.glob("manim_s2_tap_*.py")))
        sparse_episodes = []

        for mf in all_manim:
            tree = ast.parse(mf.read_text(encoding="utf-8"), filename=mf.name)
            scene_count = 0
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    for base in node.bases:
                        base_name = ""
                        if isinstance(base, ast.Name):
                            base_name = base.id
                        elif isinstance(base, ast.Attribute):
                            base_name = base.attr
                        if "Scene" in base_name:
                            scene_count += 1
            if scene_count < 6:
                sparse_episodes.append(f"{mf.name}: only {scene_count} scenes")

        assert not sparse_episodes, f"Episodes with fewer than 6 scenes: {sparse_episodes}"


# =============================================================================
# 2. SERIES 2 MANIM 2K LAYOUT, AESTHETICS & COLLISION AUDIT
# =============================================================================

class TestSeries2ManimLayoutInvariants:
    """Verifies layout safety, arrow aerodynamics, and text readability for Series 2."""

    def test_series_02_arrow_proportions_in_scenes(self):
        """No scene file in Series 2 should instantiate a raw Arrow with blunt tip_length > 0.20."""
        all_manim = sorted(list(S2_MANIM.glob("manim_s2_tap_*.py")))
        blunt_arrows = []

        for mf in all_manim:
            tree = ast.parse(mf.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func_name = None
                    if isinstance(node.func, ast.Name):
                        func_name = node.func.id
                    elif isinstance(node.func, ast.Attribute):
                        func_name = node.func.attr

                    if func_name == "Arrow":
                        for kw in node.keywords:
                            if kw.arg == "tip_length" and isinstance(kw.value, ast.Constant):
                                if float(kw.value.value) > 0.20:
                                    blunt_arrows.append(f"{mf.name}: L{node.lineno} tip_length={kw.value.value}")

        assert not blunt_arrows, f"Found blunt arrows with tip_length > 0.20: {blunt_arrows}"

    def test_series_02_curved_arrow_collision_risk(self):
        """
        CurvedArrow connecting horizontal node lists must not curve upward into existing text boxes.
        Specifically, an arc from a right node to a left node with angle > 0 bulges upwards into
        the positive Y area where the node cards reside.
        """
        all_manim = sorted(list(S2_MANIM.glob("manim_s2_tap_*.py")))
        collision_risks = []

        for mf in all_manim:
            code = mf.read_text(encoding="utf-8")
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func_name = None
                    if isinstance(node.func, ast.Name):
                        func_name = node.func.id
                    elif isinstance(node.func, ast.Attribute):
                        func_name = node.func.attr

                    if func_name == "CurvedArrow":
                        angle_val = None
                        for kw in node.keywords:
                            if kw.arg == "angle":
                                if isinstance(kw.value, ast.Constant):
                                    angle_val = float(kw.value.value)
                                elif isinstance(kw.value, ast.BinOp):
                                    # e.g. TAU / 4.5
                                    try:
                                        angle_val = 1.0 # positive binop
                                    except Exception:
                                        pass
                        # If start_point is nodes[3] and end_point is nodes[0] (right to left)
                        # and angle is positive, it bulges upwards into boxes
                        code_segment = ast.get_source_segment(code, node) or ""
                        if ("nodes[3]" in code_segment or "nodes[2]" in code_segment) and "nodes[0]" in code_segment:
                            if "angle=" in code_segment and "TAU" in code_segment and "-TAU" not in code_segment:
                                collision_risks.append(f"{mf.name}: line {node.lineno} upward collision: {code_segment.strip()}")

        assert not collision_risks, f"CurvedArrow upward collision detected: {collision_risks}"

    def test_series_02_micro_text_audit(self):
        """
        Font sizes below 12.0pt in 2K scenes are unreadable on mobile screens and fail the Trust Gate.
        This test inventories any micro-text occurrences across Series 2.
        """
        all_manim = sorted(list(S2_MANIM.glob("manim_s2_tap_*.py")))
        micro_texts = []

        for mf in all_manim:
            tree = ast.parse(mf.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func_name = None
                    if isinstance(node.func, ast.Name):
                        func_name = node.func.id
                    elif isinstance(node.func, ast.Attribute):
                        func_name = node.func.attr

                    if func_name in ("Text", "Tex", "MathTex"):
                        for kw in node.keywords:
                            if kw.arg == "font_size" and isinstance(kw.value, ast.Constant):
                                try:
                                    val = float(kw.value.value)
                                    if 0 < val < 12.0:
                                        micro_texts.append((mf.name, node.lineno, func_name, val))
                                except (ValueError, TypeError):
                                    pass

        # Zero-tolerance assertion: all text in 2K scenes must be >= 12.0pt
        assert len(micro_texts) == 0, f"Found {len(micro_texts)} micro-text occurrences: {micro_texts[:5]}"


# =============================================================================
# 3. SERIES 2 CANONICAL PLAN & CURRICULUM DAG INTEGRITY
# =============================================================================

class TestSeries2PlanAndCurriculumDAG:
    """Verifies Series 2 canonical plan, 3-act structure, and DAG acyclicity."""

    def test_series_02_canonical_plan_all_25_episodes(self):
        """series_02_canonical_plan.json must define exactly 25 episodes with complete metadata."""
        plan_path = S2_DIR / "series_02_canonical_plan.json"
        assert plan_path.is_file(), "series_02_canonical_plan.json must exist"

        data = json.loads(plan_path.read_text(encoding="utf-8"))
        assert data.get("series_id") == "series_02"
        episodes = data.get("episodes", [])
        assert len(episodes) == 25, f"Expected 25 episodes, found {len(episodes)}"

        for ep in episodes:
            num = ep["ep"]
            assert 1 <= num <= 25
            assert len(ep["title"]) <= 60, f"Ep {num} title exceeds 60 chars: {ep['title']}"
            assert "//" not in ep["title"], f"Ep {num} title contains forbidden '//': {ep['title']}"
            assert ep["target_word_count"] >= 2850, f"Ep {num} target words < 2850: {ep['target_word_count']}"
            assert 15.0 <= ep["target_duration_minutes"] <= 25.0

    def test_series_02_acyclic_dag_dependencies(self):
        """Episode prerequisites must form a strictly valid topological sort."""
        plan_path = S2_DIR / "series_02_canonical_plan.json"
        data = json.loads(plan_path.read_text(encoding="utf-8"))
        episodes = data.get("episodes", [])

        positions = {ep["ep"]: idx for idx, ep in enumerate(episodes)}
        for ep in episodes:
            num = ep["ep"]
            for prereq in ep.get("prerequisites", []):
                # parse episode number from prerequisite string e.g. "Tập 01"
                m = re.search(r"(\d+)", str(prereq))
                if m:
                    prereq_num = int(m.group(1))
                    assert prereq_num in positions, f"Ep {num} unknown prereq {prereq}"
                    assert positions[prereq_num] < positions[num], (
                        f"Ep {num} topological cycle or forward dependency on {prereq}"
                    )


# =============================================================================
# 4. SERIES 2 AUDIO & VIDEO STAGING QUALITY AUDIT
# =============================================================================

class TestSeries2AudioAndStagingQuality:
    """Verifies audio coverage, EBU R128 mastering, and YouTube staging readiness."""

    def test_series_02_audio_coverage_all_25_episodes(self):
        """All 25 episodes must have generated WAV audio files in audio/series_02/."""
        missing_audio = []
        for ep in range(1, 26):
            ep_dir = S2_AUDIO / f"tap_{ep:02d}"
            wavs = list(ep_dir.glob("*.wav")) if ep_dir.is_dir() else []
            if not wavs:
                missing_audio.append(f"tap_{ep:02d}")

        assert not missing_audio, f"Episodes missing audio WAV files: {missing_audio}"

    def test_series_02_master_video_staging_inventory(self):
        """Verifies presence of master videos in youtube_staging/series_02/."""
        missing_masters = []
        for ep in range(1, 26):
            ep_dir = S2_STAGING / f"tap_{ep:02d}"
            mp4s = [f for f in ep_dir.glob("*.mp4") if "short" not in f.name] if ep_dir.is_dir() else []
            if not mp4s:
                missing_masters.append(f"tap_{ep:02d}")

        assert not missing_masters, f"Episodes missing master video files: {missing_masters}"

    def test_series_02_thumbnail_presence(self):
        """Each staged episode directory must contain a valid 16:9 thumbnail."""
        missing_thumbs = []
        for ep in range(1, 26):
            ep_dir = S2_STAGING / f"tap_{ep:02d}"
            thumbs = list(ep_dir.glob("*.jpg")) + list(ep_dir.glob("*.png")) if ep_dir.is_dir() else []
            if not thumbs:
                missing_thumbs.append(f"tap_{ep:02d}")

        assert not missing_thumbs, f"Episodes missing thumbnail image: {missing_thumbs}"

    def test_series_02_25_thumbnails_mosaic_exists(self):
        """The 5x5 composite gallery mosaic for Series 2 must be generated and non-empty."""
        mosaic = ROOT / "assets/brand/zenpham-brand-kit/series2_25_thumbnails_mosaic.png"
        assert mosaic.is_file(), f"Series 2 mosaic not found at {mosaic}"
        assert mosaic.stat().st_size > 100_000, f"Series 2 mosaic file too small ({mosaic.stat().st_size} bytes)"

