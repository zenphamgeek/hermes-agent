#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_tts_input_sanitizer.py
=================================
Automated Unit Tests & AST Security Gate for TTS Input Sanitization & Subprocess Safety.

Verifies:
1. Null bytes, control characters, and ANSI escapes are neutralized.
2. Trojan Source bidirectional overrides (CVE-2021-42574) are stripped.
3. Natural Vietnamese diacritics, punctuation, and <en> markup are preserved.
4. Input length limits enforce denial-of-service / memory exhaustion defense.
5. AST audit confirms ZERO `shell=True` subprocess calls exist in TTS synthesizers.
"""

import ast
from pathlib import Path
import pytest

from assets.scripts_video.tts_input_sanitizer import (
    sanitize_tts_input,
    MAX_TTS_TEXT_LENGTH,
)

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_sanitize_null_and_control_chars():
    """Verify null bytes and non-printable control characters are stripped."""
    payload = "Xin chào\x00 các bạn\x07\x08, hôm nay\x1f chúng ta học toán."
    cleaned = sanitize_tts_input(payload)
    assert "\x00" not in cleaned
    assert "\x07" not in cleaned
    assert "\x08" not in cleaned
    assert "\x1f" not in cleaned
    assert cleaned == "Xin chào các bạn, hôm nay chúng ta học toán."


def test_sanitize_trojan_source_bidi_characters():
    """Verify Trojan Source bidirectional control characters (CVE-2021-42574) are stripped."""
    # \u202e is Right-to-Left Override (RLO)
    payload = "Đoạn văn \u202Ereversed text\u202C bình thường."
    cleaned = sanitize_tts_input(payload)
    assert "\u202e" not in cleaned
    assert "\u202c" not in cleaned
    assert cleaned == "Đoạn văn reversed text bình thường."


def test_sanitize_ansi_escape_sequences():
    """Verify ANSI escape codes are stripped."""
    payload = "\x1b[31;1mCảnh báo\x1b[0m hệ thống mạng."
    cleaned = sanitize_tts_input(payload)
    assert "\x1b" not in cleaned
    assert "[31;1m" not in cleaned
    assert cleaned == "Cảnh báo hệ thống mạng."


def test_sanitize_preserves_vietnamese_and_tech_markup():
    """Verify natural Vietnamese diacritics, math terms, and <en> tags are 100% preserved."""
    canonical_text = "Hệ thống <en>Transformer</en> với cơ chế <en>Self-Attention</en>, tối ưu hóa qua Adam."
    cleaned = sanitize_tts_input(canonical_text)
    assert cleaned == canonical_text


def test_sanitize_length_boundary_limit():
    """Verify unbounded payloads exceeding MAX_TTS_TEXT_LENGTH raise ValueError."""
    huge_payload = "a" * (MAX_TTS_TEXT_LENGTH + 1)
    with pytest.raises(ValueError, match="exceeds maximum allowable length"):
        sanitize_tts_input(huge_payload)


def test_ast_zero_shell_true_in_synthesizers():
    """AST Security Gate: Prohibit shell=True in all TTS synthesizer subprocess calls."""
    synthesizer_paths = [
        REPO_ROOT / "assets" / "scripts_video" / "tts_v0_synthesizer.py",
        REPO_ROOT / "assets" / "scripts_video" / "tts_v0_sense_synthesizer.py",
    ]

    for p in synthesizer_paths:
        assert p.exists(), f"Synthesizer path must exist: {p}"
        tree = ast.parse(p.read_text(encoding="utf-8"), filename=str(p))

        shell_true_violations = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                for keyword in node.keywords:
                    if keyword.arg == "shell" and isinstance(keyword.value, ast.Constant):
                        if keyword.value.value is True:
                            shell_true_violations.append((p.name, node.lineno))

        assert not shell_true_violations, (
            f"Detected forbidden `shell=True` subprocess invocation in {p.name}: {shell_true_violations}"
        )
