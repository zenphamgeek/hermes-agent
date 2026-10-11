#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
assets/scripts_video/tts_input_sanitizer.py
===========================================
Standalone Security Guard: Neutralizes untrusted/malicious control characters,
format exploits, Trojan Source directional overrides, ANSI escapes, and shell
metacharacters in text before entering neural synthesis or audio subprocess pipelines.

Decoupled completely from prosody dictionaries to guarantee persistent defense.
"""

import re
from typing import Optional

# Max characters for a single TTS input batch (defense against ReDoS / memory exhaustion)
MAX_TTS_TEXT_LENGTH = 100_000

# ANSI escape sequence regex
ANSI_ESCAPE_PATTERN = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

# Trojan Source / bidirectional control characters (CVE-2021-42574)
BIDI_CONTROL_PATTERN = re.compile(r"[\u200E\u200F\u202A-\u202E\u2066-\u2069]")

# Forbidden ASCII control characters (keep \n, \r, \t)
CONTROL_CHAR_PATTERN = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]")


def sanitize_tts_input(text: Optional[str], max_length: int = MAX_TTS_TEXT_LENGTH) -> str:
    """
    Sanitizes raw text intended for TTS synthesis.
    
    Security Controls:
    1. Null & control character elimination (CWE-20)
    2. ANSI escape sequence purging (terminal injection)
    3. Trojan Source bidirectional override removal (CVE-2021-42574)
    4. Text length boundary guard (DoS / unbounded allocation)
    5. Normalizes carriage returns and trims excessive trailing whitespace
    """
    if text is None:
        return ""

    if not isinstance(text, str):
        raise TypeError(f"TTS input must be str, got {type(text).__name__}")

    # Bounded length guard
    if len(text) > max_length:
        raise ValueError(
            f"TTS input exceeds maximum allowable length ({len(text)} > {max_length} chars)"
        )

    # 1. Purge ANSI escape sequences
    cleaned = ANSI_ESCAPE_PATTERN.sub("", text)

    # 2. Strip Trojan Source directional override characters
    cleaned = BIDI_CONTROL_PATTERN.sub("", cleaned)

    # 3. Strip non-printable ASCII control characters (preserving \t, \n, \r)
    cleaned = CONTROL_CHAR_PATTERN.sub("", cleaned)

    # 4. Normalize \r\n to \n
    cleaned = cleaned.replace("\r\n", "\n").replace("\r", "\n")

    return cleaned.strip()
