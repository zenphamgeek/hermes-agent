#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_tts_phonetic_linter.py
=================================
Automated Adversarial Unit Tests for OmniVoice TTS Phonetic Linter:
1. Subscript & caret traps detection.
2. Raw LaTeX math symbols detection.
3. Approved technical acronyms pass-through.
4. CWE-22 Path Traversal & Repository Confinement Guards (--episode & --dir).
5. Fail-Closed normalization contract enforcement.
"""

import subprocess
import sys
from pathlib import Path
import pytest

import assets.scripts_video.tts_phonetic_linter as linter_mod
from assets.scripts_video.tts_phonetic_linter import lint_text, APPROVED_ACRONYMS

REPO_ROOT = Path(__file__).resolve().parent.parent
LINTER_SCRIPT = REPO_ROOT / "assets" / "scripts_video" / "tts_phonetic_linter.py"


def test_phonetic_linter_subscript_and_caret_traps():
    """Verify that underscore (subscript) and caret (superscript) traps are detected."""
    res_us = lint_text("Biến số x_t đại diện cho thời gian.")
    assert any("Chứa ký tự gạch dưới" in err for err in res_us)

    res_caret = lint_text("Lũy thừa e^x rất nguy hiểm cho TTS.")
    assert any("Chứa ký tự caret" in err for err in res_caret)


def test_phonetic_linter_raw_latex_math_traps():
    """Verify that raw LaTeX formulas are rejected in narration text."""
    res_latex = lint_text("Công thức tính xác suất là $\\frac{1}{2}$ trong không gian mẫu.")
    assert any("Chứa ký tự LaTeX toán học" in err for err in res_latex)


def test_phonetic_linter_approved_acronyms_permitted():
    """Verify approved technical acronyms (AI, GPU, CUDA, ECE) do not trigger false positives."""
    text = "Mô hình AI trên GPU với kiến trúc CUDA và chỉ số ECE đạt chuẩn."
    res = lint_text(text)
    for err in res:
        assert not any(f"'{acr}'" in err for acr in ("AI", "GPU", "CUDA", "ECE"))


@pytest.mark.parametrize("bad_episode", [
    "../../etc/passwd",
    "..",
    "a/b",
    "",
    "tap_01;rm -rf",
    "tap.01",
])
def test_phonetic_linter_episode_cwe22_rejections(bad_episode):
    """Verify CLI rejects invalid or traversing episode names with exit code 2."""
    cmd = [sys.executable, str(LINTER_SCRIPT), "--episode", bad_episode]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 2, f"Expected exit code 2 for bad episode '{bad_episode}', got {result.returncode}"
    assert "CWE-22 path traversal guard" in result.stdout or "CWE-22 path traversal guard" in result.stderr


@pytest.mark.parametrize("bad_dir", [
    "../../etc",
    "/etc",
    "/tmp",
    "../..",
])
def test_phonetic_linter_dir_cwe22_confinement_rejections(bad_dir):
    """Verify CLI rejects directories outside the repository root with exit code 2."""
    cmd = [sys.executable, str(LINTER_SCRIPT), "--dir", bad_dir]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 2, f"Expected exit code 2 for bad dir '{bad_dir}', got {result.returncode}"
    assert "CWE-22 guard" in result.stdout or "CWE-22 guard" in result.stderr


def test_phonetic_linter_dir_valid_confinement():
    """Verify CLI accepts a valid directory inside the repository."""
    valid_dir = REPO_ROOT / "assets" / "scripts_video"
    cmd = [sys.executable, str(LINTER_SCRIPT), "--dir", str(valid_dir)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode in (0, 1), f"Unexpected return code {result.returncode} for valid dir"
    assert "CWE-22 guard" not in result.stdout


def test_phonetic_linter_fail_closed_on_broken_report(monkeypatch):
    """Verify fail-closed behavior when normalize_for_omnivoice returns a malformed non-dict report."""
    monkeypatch.setattr(linter_mod, "normalize_for_omnivoice", lambda text: ("cleaned", None))
    violations = lint_text("Câu văn kiểm tra hợp đồng.")
    assert any("Lỗi hợp đồng normalize_for_omnivoice" in v for v in violations), (
        f"Expected contract violation error on None report, got: {violations}"
    )

    monkeypatch.setattr(linter_mod, "normalize_for_omnivoice", lambda text: ("cleaned", "not a dict"))
    violations_str = lint_text("Câu văn kiểm tra hợp đồng.")
    assert any("Lỗi hợp đồng normalize_for_omnivoice" in v for v in violations_str), (
        f"Expected contract violation error on string report, got: {violations_str}"
    )
