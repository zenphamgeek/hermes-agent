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
    """AST Security Gate: Prohibit shell=True in all TTS synthesizer and driver subprocess calls."""
    scripts_video_dir = REPO_ROOT / "assets" / "scripts_video"
    synthesizer_paths = list(scripts_video_dir.glob("tts_*.py")) + list(scripts_video_dir.glob("synthesize_*.py"))
    assert len(synthesizer_paths) > 0, "Synthesizer scripts must be found"

    shell_true_violations = []
    for p in synthesizer_paths:
        tree = ast.parse(p.read_text(encoding="utf-8"), filename=str(p))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                for keyword in node.keywords:
                    if keyword.arg == "shell" and isinstance(keyword.value, ast.Constant):
                        if keyword.value.value is True:
                            shell_true_violations.append((p.name, node.lineno))

    assert not shell_true_violations, (
        f"Detected forbidden `shell=True` subprocess invocation in synthesizers: {shell_true_violations}"
    )


def test_synthesis_drivers_zero_hardcoded_secrets_and_network_isolation():
    """
    Security Audit Gate (CWE-259 & Stealth Invariant):
    Synthesizer drivers must operate 100% locally on CUDA:
    1. Zero hardcoded secrets, API tokens, or Bearer auth (CWE-259).
    2. Zero remote HTTP/network client imports (pure local inference, zero quota scraping).
    3. All subprocess calls must use list/array arguments, never string commands (CWE-78).
    """
    import re
    scripts_video_dir = REPO_ROOT / "assets" / "scripts_video"
    synthesizer_paths = list(scripts_video_dir.glob("synthesize_series_*.py")) + list(scripts_video_dir.glob("tts_v0*.py"))
    assert len(synthesizer_paths) > 0, "No production series synthesis drivers found"

    secret_pattern = re.compile(
        r"(?:api_key|secret|token|password|bearer)\s*=\s*['\"][a-zA-Z0-9_\-\.]{16,}['\"]",
        re.IGNORECASE
    )
    network_modules = {"requests", "httpx", "urllib.request", "aiohttp", "socket"}

    for p in synthesizer_paths:
        content = p.read_text(encoding="utf-8")
        
        # 1. Secret scan
        secret_matches = secret_pattern.findall(content)
        assert not secret_matches, f"CWE-259 Violation: Potential hardcoded secret in {p.name}: {secret_matches}"

        # 2. AST Module & Subprocess Argument Scan
        tree = ast.parse(content, filename=str(p))
        for node in ast.walk(tree):
            # Check imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name not in network_modules, (
                        f"Network Isolation Violation: {p.name} imports remote client '{alias.name}'"
                    )
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                assert not any(mod == nm or mod.startswith(nm + ".") for nm in network_modules), (
                    f"Network Isolation Violation: {p.name} imports from remote client '{mod}'"
                )

            # Check subprocess invocations use list/array argument
            if isinstance(node, ast.Call):
                func = node.func
                is_subp = False
                if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
                    if func.value.id == "subprocess" and func.attr in ("run", "Popen", "check_output", "call"):
                        is_subp = True
                if is_subp and node.args:
                    first_arg = node.args[0]
                    # Disallow raw string literal as command (must be list, variable, or Call)
                    assert not isinstance(first_arg, (ast.Constant, ast.JoinedStr)), (
                        f"CWE-78 Risk: Subprocess in {p.name} at line {node.lineno} passes string literal instead of list"
                    )

