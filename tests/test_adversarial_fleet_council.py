#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_adversarial_fleet_council.py
=======================================
Adversarial Stress Test Suite for AGY Fleet Council Dispatcher (tools/fleet_council_dispatcher.py).
Conducted by Empirical Challenger Subagent (teamwork_preview_challenger_2).

Exhaustively stress tests:
1. Veto Override Boundary:
   - 7 members 4.0/4.0 (Tier 4) + 1 member VETO across all 8 roles -> REJECTED & exit code 2
   - Multiple concurrent vetoes -> REJECTED & exit code 2
   - Implicit veto via score <= 1.0 -> converted to VETOED & REJECTED
   - Syntactic variations of veto
   - Semantic veto evasion defects (e.g. "NOT APPROVED", "REJECTED" defaulting to APPROVED)
2. Score Boundary Testing:
   - Overall score exactly at 3.00 -> CONDITIONAL_APPROVAL & exit code 0
   - Overall score at 2.99 -> REJECTED & exit code 2
   - Overall score at 1.00 -> REJECTED & exit code 2
   - Overall score at 4.00 -> APPROVED & exit code 0
   - Overall score at 3.50 (with min dimension >= 3.0 vs < 3.0)
   - Dimension floor boundary (< 2.0 forces REJECTED even with overall score >= 3.00)
3. Extreme & Malformed Input Handling:
   - Empty script ("")
   - Whitespace-only script
   - Massive 2MB script (2,000,000 chars)
   - Unformatted / hallucinated model outputs (empty, JSON error, binary, code dumps, conversational refusal)
   - Robust fallback parsing without uncaught exceptions
4. Content Integrity & Downstream Parsing:
   - YAML frontmatter validity with yaml.safe_load
   - YAML frontmatter unescaped quote syntax defect
   - Markdown table column count consistency
   - Table column break via pipe character injection
   - Hardcoded "Tier 4" defect in Table 2 dimension rows
"""

from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
import re
import sys
import time
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import yaml

from tools.fleet_council_dispatcher import (
    COUNCIL_ROLES,
    DEFAULT_CACHE_DIR,
    DEFAULT_FLEET_URL,
    DEFAULT_OUTPUT_FILE,
    CacheManager,
    CouncilExecutionError,
    CouncilRoleConfig,
    DeliberationReport,
    DeliberationSynthesizer,
    DispatcherCLI,
    FleetClient,
    MemberDeliberation,
    NodeInfo,
    QuotaStarvationError,
    RubricScorecard,
)

# Canonical Mock Fleet Nodes (8 nodes)
MOCK_8_NODES = [
    NodeInfo("ultra-2", "ultra", "idle", "ultra2@example.com", "claude-opus-4-6-thinking"),
    NodeInfo("pro-1", "ultra", "idle", "pro1@example.com", "gemini-4-argon-high"),
    NodeInfo("node-4", "pro", "idle", "node4@example.com", "gemini-4-argon-high"),
    NodeInfo("node-5", "pro", "idle", "node5@example.com", "gemini-4-argon-high"),
    NodeInfo("node-6", "pro", "idle", "node6@example.com", "gemini-4-argon-high"),
    NodeInfo("node-7", "pro", "idle", "node7@example.com", "gemini-4-argon-high"),
    NodeInfo("node-8", "pro", "idle", "node8@example.com", "gemini-4-argon-high"),
    NodeInfo("team-3", "pro", "idle", "team3@example.com", "gemini-4-argon-high"),
]


# ===========================================================================
# 1. VETO OVERRIDE BOUNDARY TESTS
# ===========================================================================

class TestVetoOverrideBoundary:
    """Stress tests verifying that ANY veto unconditionally rejects deliberation and exits with code 2."""

    @pytest.mark.parametrize("veto_role_id", list(COUNCIL_ROLES.keys()))
    def test_single_member_veto_overrides_seven_perfect_scores(self, veto_role_id: str, tmp_path: Path):
        """
        Adversarial test: 7 members assign perfect 4.0/4.0 (Tier 4 Masterclass Excellence),
        but exactly 1 member triggers a VETO.
        Tested across each of the 8 council roles individually.
        MUST unconditionally conclude REJECTED, record veto_count == 1, and CLI exit code == 2.
        """
        synth = DeliberationSynthesizer()
        deliberations: list[MemberDeliberation] = []

        for role_id, config in COUNCIL_ROLES.items():
            if role_id == veto_role_id:
                # This member asserts a VETO
                delib = MemberDeliberation(
                    role_id=role_id,
                    role_title=config.title,
                    node_name="test-node",
                    tier=config.tier_preference,
                    model="test-model",
                    score=1.0,
                    verdict="VETOED",
                    critique=f"Fatal defect identified by {config.title}.",
                    directives=["Remediate defect"],
                    veto_asserted=True,
                )
            else:
                # Other 7 members assign 4.0
                delib = MemberDeliberation(
                    role_id=role_id,
                    role_title=config.title,
                    node_name="test-node",
                    tier=config.tier_preference,
                    model="test-model",
                    score=4.0,
                    verdict="APPROVED",
                    critique="Perfect score.",
                    directives=[],
                    veto_asserted=False,
                )
            deliberations.append(delib)

        rubric = synth.compute_rubric(deliberations)

        # Assertions on rubric
        assert rubric.status == "REJECTED", f"Role {veto_role_id} veto failed to force REJECTED status!"
        assert rubric.veto_count == 1
        assert len(rubric.veto_reasons) == 1
        assert COUNCIL_ROLES[veto_role_id].title in rubric.veto_reasons[0]

        # Verify CLI execution exit code 2
        out_file = tmp_path / f"veto_{veto_role_id}.md"
        with patch.object(FleetClient, "get_health", return_value={"status": "ok", "nodes": 8}), \
             patch.object(FleetClient, "get_status", return_value=MOCK_8_NODES), \
             patch.object(FleetClient, "run_parallel") as mock_parallel:

            def mock_exec(tasks, timeout):
                results = []
                for t in tasks:
                    if t["role_id"] == veto_role_id:
                        text = "### 1. Assessment & Veto Status: VETOED\nFatal defect\n### 6. Rubric Score: 1.0"
                    else:
                        text = "### 1. Assessment & Veto Status: APPROVED\nExcellent\n### 6. Rubric Score: 4.0"
                    results.append({
                        "role_id": t["role_id"],
                        "cache_key": t["cache_key"],
                        "job_result": {
                            "status": "completed",
                            "clean_response": text,
                            "total_tokens": 100,
                            "cost_saved_usd": 0.001,
                        }
                    })
                return results

            mock_parallel.side_effect = mock_exec

            exit_code = DispatcherCLI.run([
                "--topic", f"Adversarial Veto Test on {veto_role_id}",
                "-o", str(out_file),
                "--cache-dir", str(tmp_path / "cache"),
                "--no-cache",
            ])

            assert exit_code == 2, f"CLI must exit with code 2 when {veto_role_id} vetoes, but returned {exit_code}!"
            assert out_file.exists()
            content = out_file.read_text(encoding="utf-8")
            assert 'overall_status: "REJECTED"' in content
            assert "veto_count: 1" in content

    def test_multiple_simultaneous_vetoes(self):
        """Verify that when multiple members veto, all reasons are recorded and status is REJECTED."""
        synth = DeliberationSynthesizer()
        deliberations: list[MemberDeliberation] = []

        veto_roles = {"math_core", "visual_architect", "acoustic_qa"}

        for role_id, config in COUNCIL_ROLES.items():
            is_veto = role_id in veto_roles
            delib = MemberDeliberation(
                role_id=role_id,
                role_title=config.title,
                node_name="test-node",
                tier=config.tier_preference,
                model="test-model",
                score=1.0 if is_veto else 4.0,
                verdict="VETOED" if is_veto else "APPROVED",
                critique="Veto critique" if is_veto else "Approval critique",
                directives=[],
                veto_asserted=is_veto,
            )
            deliberations.append(delib)

        rubric = synth.compute_rubric(deliberations)
        assert rubric.status == "REJECTED"
        assert rubric.veto_count == 3
        assert len(rubric.veto_reasons) == 3

    def test_implicit_veto_via_score_one_point_zero(self):
        """
        Adversarial test: Member output does NOT mention the word 'VETO', but assigns Score: 1.0.
        Verify that score <= 1.0 implicitly triggers veto_asserted=True and status=REJECTED.
        """
        synth = DeliberationSynthesizer()
        node = MOCK_8_NODES[0]
        raw_output = """
### 1. Assessment & Veto Status: APPROVED
I like the topic, but the script is missing almost everything.
### 6. 4x4 Rubric Score on Dimension 2: 1.0 / 4
        """
        delib = synth.parse_member_response("math_core", COUNCIL_ROLES["math_core"], node, raw_output)
        assert delib.score == 1.0
        assert delib.verdict == "VETOED"
        assert delib.veto_asserted is True

    @pytest.mark.parametrize("veto_snippet", [
        "### 1. Assessment & Veto Status: [VETOED]",
        "### 1. Assessment & Veto Status: VETO",
        "VETOED by reviewer.",
        "Quyền Phủ Quyết được kích hoạt do vi phạm bất biến",
        "Tôi kích hoạt quyền phủ quyết đối với bản thảo này",
        "### 1. Assessment & Veto Status: [VETO]",
    ])
    def test_syntactic_veto_patterns_detected(self, veto_snippet: str):
        """Verify that known syntactic veto patterns are correctly caught."""
        synth = DeliberationSynthesizer()
        node = MOCK_8_NODES[0]
        output = f"{veto_snippet}\n### 6. Rubric Score: 4.0"
        delib = synth.parse_member_response("math_core", COUNCIL_ROLES["math_core"], node, output)
        assert delib.veto_asserted is True
        assert delib.verdict == "VETOED"
        assert delib.score <= 1.0

    def test_semantic_veto_missed_defect_demonstration(self):
        """
        REMEDIATION VERIFICATION: Model outputs clear semantic rejection phrases like:
        - 'Assessment & Veto Status: NOT APPROVED'
        - 'Assessment & Veto Status: REJECTED'
        - 'Quyết định: Phủ quyết kịch bản'
        - 'VETO: Script contains fatal math error.'
        Verify that all are properly parsed as VETOED with score <= 1.0 and veto_asserted=True.
        """
        synth = DeliberationSynthesizer()
        node = MOCK_8_NODES[0]

        failing_outputs = [
            ("### 1. Assessment & Veto Status: NOT APPROVED\nScore: 2.0", "NOT APPROVED"),
            ("### 1. Assessment & Veto Status: REJECTED\nScore: 2.0", "REJECTED"),
            ("Tôi phủ quyết kịch bản này do vi phạm nghiêm trọng.\nScore: 2.0", "Phủ quyết"),
            ("VETO: Script contains fatal math error.\nScore: 2.0", "VETO: without leading colon"),
        ]

        for raw, label in failing_outputs:
            delib = synth.parse_member_response("math_core", COUNCIL_ROLES["math_core"], node, raw)
            assert delib.verdict == "VETOED", f"Expected VETOED for {label}, got {delib.verdict}"
            assert delib.veto_asserted is True, f"Expected veto_asserted=True for {label}"
            assert delib.score <= 1.0, f"Expected score <= 1.0 for {label}, got {delib.score}"


# ===========================================================================
# 2. SCORE BOUNDARY TESTING
# ===========================================================================

class TestScoreBoundaryConditions:
    """Stress tests probing exact boundary values of the 4x4 rubric engine."""

    def _build_deliberations_with_scores(self, scores: dict[str, float]) -> list[MemberDeliberation]:
        delibs = []
        for role_id, config in COUNCIL_ROLES.items():
            sc = scores.get(role_id, 3.5)
            delibs.append(MemberDeliberation(
                role_id=role_id,
                role_title=config.title,
                node_name="test-node",
                tier=config.tier_preference,
                model="test-model",
                score=sc,
                verdict="APPROVED" if sc >= 3.0 else "APPROVED_WITH_MODIFICATIONS",
                critique="Score test",
                directives=[],
                veto_asserted=False,
            ))
        return delibs

    def test_overall_score_exactly_3_00(self, tmp_path: Path):
        """
        Boundary condition: overall_score == 3.00 (the exact boundary between REJECTED and CONDITIONAL_APPROVAL).
        Formula: 0.30*D1 + 0.30*D2 + 0.20*D3 + 0.20*D4.
        If all members assign 3.0:
        D1=3.0, D2=3.0, D3=3.0, D4=3.0 -> overall = 3.00.
        Status MUST BE 'CONDITIONAL_APPROVAL' (not REJECTED), Tier MUST BE 'Tier 3 (Standard Pass)',
        and CLI MUST exit with code 0.
        """
        synth = DeliberationSynthesizer()
        delibs = self._build_deliberations_with_scores({r: 3.0 for r in COUNCIL_ROLES})
        rubric = synth.compute_rubric(delibs)

        assert rubric.overall_score == 3.00
        assert rubric.status == "CONDITIONAL_APPROVAL"
        assert rubric.overall_tier == "Tier 3 (Standard Pass)"
        assert rubric.veto_count == 0

        # Verify CLI exit code 0
        out_file = tmp_path / "boundary_300.md"
        with patch.object(FleetClient, "get_health", return_value={"status": "ok", "nodes": 8}), \
             patch.object(FleetClient, "get_status", return_value=MOCK_8_NODES), \
             patch.object(FleetClient, "run_parallel") as mock_parallel:

            mock_parallel.return_value = [
                {
                    "role_id": r,
                    "cache_key": f"key_{r}",
                    "job_result": {
                        "status": "completed",
                        "clean_response": "### 1. Assessment: APPROVED_WITH_MODIFICATIONS\nPassable.\n### 6. Rubric Score: 3.0",
                        "total_tokens": 100,
                        "cost_saved_usd": 0.0,
                    }
                }
                for r in COUNCIL_ROLES
            ]

            exit_code = DispatcherCLI.run([
                "--topic", "Score 3.00 Boundary Test",
                "-o", str(out_file),
                "--cache-dir", str(tmp_path / "cache"),
                "--no-cache",
            ])

            assert exit_code == 0
            content = out_file.read_text(encoding="utf-8")
            assert 'overall_status: "CONDITIONAL_APPROVAL"' in content
            assert "overall_score: 3.00" in content

    def test_overall_score_boundary_2_99(self, tmp_path: Path):
        """
        Boundary condition: overall_score == 2.99 (< 3.00).
        MUST conclude REJECTED, Tier MUST BE 'Tier 2 (Deficient / Remediation)',
        and CLI MUST exit with code 2.
        """
        synth = DeliberationSynthesizer()
        # To get 2.99:
        # D1 = (3.0 + 3.0 + 3.0)/3 = 3.0 (weight 0.30 -> 0.90)
        # D2 = 3.0 (weight 0.30 -> 0.90)
        # D3 = (2.95 + 3.0)/2 = 2.975 (weight 0.20 -> 0.595)
        # D4 = 2.95 (weight 0.20 -> 0.59)
        # 0.90 + 0.90 + 0.595 + 0.59 = 2.985 -> round to 2.99.
        scores = {
            "synthesis": 3.0,
            "sagan": 3.0,
            "student_16": 3.0,
            "math_core": 3.0,
            "hien_le": 2.95,
            "acoustic_qa": 3.0,
            "youtube_expert": 2.95,
            "visual_architect": 2.95,
        }
        delibs = self._build_deliberations_with_scores(scores)
        rubric = synth.compute_rubric(delibs)

        assert rubric.overall_score == 2.99
        assert rubric.status == "REJECTED"
        assert rubric.overall_tier == "Tier 2 (Deficient / Remediation)"

        # Verify CLI exit code 2
        out_file = tmp_path / "boundary_299.md"
        with patch.object(FleetClient, "get_health", return_value={"status": "ok", "nodes": 8}), \
             patch.object(FleetClient, "get_status", return_value=MOCK_8_NODES), \
             patch.object(FleetClient, "run_parallel") as mock_parallel:

            mock_parallel.return_value = [
                {
                    "role_id": r,
                    "cache_key": f"key_{r}",
                    "job_result": {
                        "status": "completed",
                        "clean_response": f"### 1. Assessment: APPROVED_WITH_MODIFICATIONS\nNotes.\n### 6. Rubric Score: {scores[r]}",
                        "total_tokens": 100,
                        "cost_saved_usd": 0.0,
                    }
                }
                for r in COUNCIL_ROLES
            ]

            exit_code = DispatcherCLI.run([
                "--topic", "Score 2.99 Boundary Test",
                "-o", str(out_file),
                "--cache-dir", str(tmp_path / "cache"),
                "--no-cache",
            ])

            assert exit_code == 2
            content = out_file.read_text(encoding="utf-8")
            assert 'overall_status: "REJECTED"' in content

    def test_overall_score_boundary_1_00(self):
        """
        Boundary condition: minimum possible score 1.00.
        All members assign 1.00.
        Status MUST BE 'REJECTED', overall_tier MUST BE 'Tier 1 (Critical Rejection / Veto)',
        veto_count MUST BE 8.
        """
        synth = DeliberationSynthesizer()
        delibs = self._build_deliberations_with_scores({r: 1.0 for r in COUNCIL_ROLES})
        rubric = synth.compute_rubric(delibs)

        assert rubric.overall_score == 1.00
        assert rubric.status == "REJECTED"
        assert rubric.overall_tier == "Tier 1 (Critical Rejection / Veto)"
        assert rubric.veto_count == 8

    def test_overall_score_boundary_4_00(self):
        """
        Boundary condition: maximum possible score 4.00.
        All members assign 4.00.
        Status MUST BE 'APPROVED', overall_tier MUST BE 'Tier 4 (Masterclass Excellence)'.
        """
        synth = DeliberationSynthesizer()
        delibs = self._build_deliberations_with_scores({r: 4.0 for r in COUNCIL_ROLES})
        rubric = synth.compute_rubric(delibs)

        assert rubric.overall_score == 4.00
        assert rubric.status == "APPROVED"
        assert rubric.overall_tier == "Tier 4 (Masterclass Excellence)"
        assert rubric.veto_count == 0

    def test_overall_score_3_50_with_dimension_constraints(self):
        """
        Boundary condition: overall_score >= 3.50, but testing the sub-condition min(D1..D4) >= 3.0.
        Case A: overall == 3.50 and all D_i >= 3.0 -> APPROVED
        Case B: overall == 3.50 but one D_i < 3.0 -> CONDITIONAL_APPROVAL
        """
        synth = DeliberationSynthesizer()

        # Case A: D1=3.5, D2=3.5, D3=3.5, D4=3.5 -> overall=3.50, min=3.5 >= 3.0 -> APPROVED
        delibs_a = self._build_deliberations_with_scores({r: 3.5 for r in COUNCIL_ROLES})
        rubric_a = synth.compute_rubric(delibs_a)
        assert rubric_a.overall_score == 3.50
        assert rubric_a.status == "APPROVED"

        # Case B: D1=4.0, D2=4.0, D3=4.0, D4=2.25
        # 0.3*4 + 0.3*4 + 0.2*4 + 0.2*2.25 = 1.2 + 1.2 + 0.8 + 0.45 = 3.65 (>= 3.50!)
        # But D4 = 2.25 < 3.0!
        scores_b = {
            "synthesis": 4.0,
            "sagan": 4.0,
            "student_16": 4.0,
            "math_core": 4.0,
            "hien_le": 4.0,
            "acoustic_qa": 4.0,
            "youtube_expert": 2.25,
            "visual_architect": 2.25,
        }
        delibs_b = self._build_deliberations_with_scores(scores_b)
        rubric_b = synth.compute_rubric(delibs_b)
        assert rubric_b.overall_score >= 3.50
        assert rubric_b.d4_engagement < 3.0
        # MUST BE CONDITIONAL_APPROVAL despite high overall score!
        assert rubric_b.status == "CONDITIONAL_APPROVAL"

    def test_dimension_floor_boundary_rejects_sub_2_0(self):
        """
        Boundary condition: min(D1, D2, D3, D4) < 2.0 triggers REJECTED,
        even when overall score is comfortably above 3.00!
        """
        synth = DeliberationSynthesizer()
        # D1 = 1.90, D2 = 4.0, D3 = 4.0, D4 = 4.0
        # overall = 0.30*1.9 + 0.30*4 + 0.20*4 + 0.20*4 = 0.57 + 1.20 + 0.80 + 0.80 = 3.37
        scores = {
            "synthesis": 1.9,
            "sagan": 1.9,
            "student_16": 1.9,
            "math_core": 4.0,
            "hien_le": 4.0,
            "acoustic_qa": 4.0,
            "youtube_expert": 4.0,
            "visual_architect": 4.0,
        }
        delibs = self._build_deliberations_with_scores(scores)
        rubric = synth.compute_rubric(delibs)

        assert rubric.overall_score == 3.37
        assert rubric.d1_clarity == 1.90
        assert rubric.status == "REJECTED", "Dimension < 2.0 must trigger REJECTED status!"


# ===========================================================================
# 3. EXTREME & MALFORMED INPUT HANDLING
# ===========================================================================

class TestExtremeAndMalformedInputs:
    """Stress tests verifying system resilience against empty, massive, and chaotic inputs."""

    def test_empty_and_whitespace_script(self, tmp_path: Path):
        """Verify handling of completely empty string and whitespace-only script."""
        cache_mgr = CacheManager(cache_dir=tmp_path, enabled=True)

        for empty_script in ["", "   ", "\n\t\n  \r\n"]:
            # 1. build_prompt handles empty script with fallback text
            prompt = COUNCIL_ROLES["math_core"].build_prompt("Test Topic", empty_script)
            assert "(No draft script provided" in prompt

            # 2. SHA-256 hash is deterministic and succeeds
            h = cache_mgr.compute_hash("math_core", "Test Topic", empty_script, "opus")
            assert len(h) == 64

            # 3. DeliberationSynthesizer synthesizes without error
            synth = DeliberationSynthesizer()
            delib = MemberDeliberation("math_core", "Shannon", "u2", "ultra", "opus", 4.0, "APPROVED", "ok")
            report = synth.synthesize("Test Topic", empty_script, None, [delib])
            assert report.script_hash_sha256 != ""
            assert len(report.markdown_content) > 100

    def test_massive_2mb_script_handling(self, tmp_path: Path):
        """Verify handling of massive 2MB script without memory exhaustion, ReDoS, or crash."""
        massive_script = "# Long Section\n" + ("Nội dung kịch bản thực tế dài 2MB. " * 80_000)
        assert len(massive_script) > 2_000_000
        assert len(massive_script.encode("utf-8")) > 2_000_000

        start_time = time.time()

        # 1. Prompt generation
        prompt = COUNCIL_ROLES["math_core"].build_prompt("Big Topic", massive_script)
        assert len(prompt) > 2_000_000

        # 2. SHA-256 computation
        cache_mgr = CacheManager(cache_dir=tmp_path, enabled=True)
        h = cache_mgr.compute_hash("math_core", "Big Topic", massive_script, "opus")
        assert len(h) == 64

        # 3. Synthesizer
        synth = DeliberationSynthesizer()
        delib = MemberDeliberation("math_core", "Shannon", "u2", "ultra", "opus", 4.0, "APPROVED", "Good")
        report = synth.synthesize("Big Topic", massive_script, None, [delib])
        expected_script_hash = hashlib.sha256(massive_script.strip().encode("utf-8")).hexdigest()
        assert report.script_hash_sha256 == expected_script_hash

        duration = time.time() - start_time
        assert duration < 3.0, f"Processing 2MB script took too long: {duration:.2f}s"

    @pytest.mark.parametrize("malformed_output, expected_fallback_directive", [
        ("", True),
        (None, True),
        ('{"error": "node internal failure", "code": 500}', True),
        ("Plain conversational text without any rubric headers or scores.", True),
        ("```python\nprint('hello world')\n```", True),
        ("\x00\x01\x02\xff\xfeGarbage binary data", True),
        ("A" * 500_000, False),  # 500KB unstructured text
    ])
    def test_unformatted_hallucinated_model_outputs_robust_fallback(
        self, malformed_output: Any, expected_fallback_directive: bool
    ):
        """
        Verify that completely malformed, unexpected, or hallucinated outputs
        do NOT raise any uncaught exceptions (TypeError, AttributeError, IndexError, etc.)
        and safely populate fallbacks.
        """
        synth = DeliberationSynthesizer()
        node = MOCK_8_NODES[0]

        delib = synth.parse_member_response(
            role_id="math_core",
            role_config=COUNCIL_ROLES["math_core"],
            node_info=node,
            raw_output=malformed_output,
        )

        assert isinstance(delib, MemberDeliberation)
        assert 1.0 <= delib.score <= 4.0
        assert delib.verdict in ("APPROVED", "APPROVED_WITH_MODIFICATIONS", "VETOED", "FAILED_EXECUTION")
        assert len(delib.directives) >= 1
        # Critique must be bounded to ~803 characters (800 + '...')
        assert len(delib.critique) <= 803

        if expected_fallback_directive:
            assert any("Tuân thủ các yêu cầu chuyên môn" in d for d in delib.directives)


# ===========================================================================
# 4. CONTENT INTEGRITY & DOWNSTREAM PARSING
# ===========================================================================

class TestContentIntegrityAndDownstreamParsing:
    """Stress tests verifying the syntactical and structural integrity of council_deliberation.md."""

    def test_yaml_frontmatter_validity_standard(self):
        """Verify that council_deliberation.md generated from standard inputs has 100% valid YAML frontmatter."""
        synth = DeliberationSynthesizer()
        delibs = [
            MemberDeliberation(r, COUNCIL_ROLES[r].title, f"node-{i}", "pro", "flash", 4.0, "APPROVED", "Good")
            for i, r in enumerate(COUNCIL_ROLES)
        ]
        report = synth.synthesize("Bản chất của xác suất trong AI", "Script", None, delibs)
        md = report.markdown_content

        assert md.startswith("---\n")
        parts = md.split("---\n")
        assert len(parts) >= 3
        fm_text = parts[1]

        data = yaml.safe_load(fm_text)
        assert isinstance(data, dict)
        assert data["topic"] == "Bản chất của xác suất trong AI"
        assert data["overall_status"] == "APPROVED"
        assert data["overall_score"] == 4.0
        assert data["veto_count"] == 0
        assert data["fleet_cluster"]["total_nodes"] == 8

    def test_yaml_frontmatter_unescaped_quotes_defect(self):
        """
        REMEDIATION VERIFICATION: When a topic contains quotation marks (e.g. S1E1: "Đồng xu của cỗ máy"),
        quotes in YAML frontmatter are properly escaped so that yaml.safe_load parses cleanly without ParserError.
        """
        synth = DeliberationSynthesizer()
        delib = MemberDeliberation("math_core", "Shannon", "u2", "ultra", "opus", 4.0, "APPROVED", "Good")

        topic_with_quotes = 'S1E1: Bản chất của xác suất trong AI — "Đồng xu của cỗ máy"'
        report = synth.synthesize(topic_with_quotes, "Script", None, [delib])

        parts = report.markdown_content.split("---\n")
        fm_text = parts[1]

        parsed = yaml.safe_load(fm_text)
        assert isinstance(parsed, dict)
        assert parsed["topic"] == 'S1E1: Bản chất của xác suất trong AI — "Đồng xu của cỗ máy"'

    def test_markdown_tables_column_consistency(self):
        """Verify that Table 1.2 (Roster) and Table 2 (Scorecard) have consistent column counts across all rows."""
        synth = DeliberationSynthesizer()
        delibs = [
            MemberDeliberation(r, COUNCIL_ROLES[r].title, f"node-{i}", "pro", "flash", 3.5, "APPROVED", "Critique")
            for i, r in enumerate(COUNCIL_ROLES)
        ]
        report = synth.synthesize("Topic", "Script", None, delibs)
        lines = report.markdown_content.splitlines()

        # Check Table 1.2: Roster Table (7 columns)
        roster_table_rows = [
            line for line in lines
            if line.startswith("|") and ("Thành Viên Hội Đồng" in line or "| 1 |" in line or "| 8 |" in line)
        ]
        for row in roster_table_rows:
            # Split by | and strip empty edge tokens
            cols = [c.strip() for c in row.split("|")[1:-1]]
            assert len(cols) == 7, f"Roster table row column count mismatch: expected 7, got {len(cols)} in: {row}"

        # Check Table 2: Scorecard Table (5 columns)
        scorecard_rows = [
            line for line in lines
            if line.startswith("|") and ("Trọng Số" in line or "$D_" in line or "ĐIỂM TỔNG HỢP" in line)
        ]
        for row in scorecard_rows:
            cols = [c.strip() for c in row.split("|")[1:-1]]
            assert len(cols) == 5, f"Scorecard table row column count mismatch: expected 5, got {len(cols)} in: {row}"

    def test_markdown_table_pipe_injection_defect(self):
        """
        REMEDIATION VERIFICATION: When a member verdict or critique contains pipe characters (|),
        they are properly escaped as &#124;, maintaining 7 columns in Table 1.2 without corruption.
        """
        synth = DeliberationSynthesizer()
        delib = MemberDeliberation(
            role_id="math_core",
            role_title="Claude Shannon",
            node_name="ultra-2",
            tier="ultra",
            model="claude-opus",
            score=3.5,
            verdict="APPROVED | WITH CONDITIONS",  # contains pipe!
            critique="Critique",
            directives=[],
        )
        report = synth.synthesize("Topic", "Script", None, [delib])

        # Find row in Table 1.2
        target_row = [l for l in report.markdown_content.splitlines() if "| 1 |" in l][0]
        cols = [c.strip() for c in target_row.split("|")[1:-1]]
        # Column count is preserved at 7 and pipe is escaped!
        assert len(cols) == 7
        assert "&#124;" in cols[5]

    def test_table2_scorecard_dimension_tier_hardcoding_defect(self):
        """
        REMEDIATION VERIFICATION: In Section 2 (Table 2), dimension tiers are computed dynamically:
        scores < 2.0 evaluate to Tier 1, rather than hardcoding Tier 4.
        """
        synth = DeliberationSynthesizer()
        delibs = [
            MemberDeliberation(r, COUNCIL_ROLES[r].title, "node", "pro", "flash", 1.0, "VETOED", "Bad", veto_asserted=True)
            for r in COUNCIL_ROLES
        ]
        report = synth.synthesize("Topic", "Script", None, delibs)

        # Look at D1 row in Table 2
        d1_row = [l for l in report.markdown_content.splitlines() if "$D_1$:" in l][0]
        assert "Tier 1" in d1_row


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
