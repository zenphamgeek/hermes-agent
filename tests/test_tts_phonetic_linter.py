#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_tts_phonetic_linter.py
=================================
Automated Unit Tests for OmniVoice TTS Phonetic Linter and CWE-22 Path Traversal Guard.
"""

import subprocess
import sys
from pathlib import Path
import pytest

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
    # None of the approved acronyms should be flagged as unmapped
    for err in res:
        assert not any(f"'{acr}'" in err for acr in ("AI", "GPU", "CUDA", "ECE"))


def test_phonetic_linter_cwe22_path_traversal_guard():
    """Verify CLI rejects path traversal attempts with exit code 2."""
    cmd = [sys.executable, str(LINTER_SCRIPT), "--episode", "../../etc/passwd"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 2, f"Expected exit code 2, got {result.returncode}"
    assert "CWE-22 path traversal guard" in result.stdout or "CWE-22 path traversal guard" in result.stderr


def test_phonetic_linter_valid_episode_arg():
    """Verify valid alphanumeric episode names pass CLI validation."""
    cmd = [sys.executable, str(LINTER_SCRIPT), "--episode", "tap_01"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    # If folder doesn't exist, it returns exit code 1 with "Thư mục không tồn tại", NOT exit code 2
    assert result.returncode in (0, 1), f"Unexpected return code {result.returncode}"
    assert "CWE-22 path traversal guard" not in result.stdout
