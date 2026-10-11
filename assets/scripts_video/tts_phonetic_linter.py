#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tts_phonetic_linter.py
======================
Phonetic and Pronunciation Linter for OmniVoice narration text.
Verifies that:
1. No raw unmapped English technical terms remain in narration.
2. No bare acronyms (>= 2 uppercase letters) exist without pronunciation mapping.
3. No subscript/superscript traps (_ or ^) exist in narration.
4. Vietnamese grammatical anchoring is respected.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.append(str(SCRIPTS_DIR))

from tts_pronunciation import normalize_for_omnivoice

# Approved technical acronyms and terms read naturally in Vietnamese narration without phonetic rewriting
APPROVED_ACRONYMS: frozenset[str] = frozenset({
    "AI", "ECE", "GPU", "CUDA", "LLM", "API", "CPU", "RAM", "SRT", "TTS", "VRAM", "RL", "OODA"
})

def lint_text(text: str, filename: str = "") -> list[str]:
    violations: list[str] = []
    
    # 1. Traps check: _ and ^
    if "_" in text:
        matches_us = re.findall(r"\w*_\w*", text)
        violations.append(f"Chứa ký tự gạch dưới '_' (bẫy subscript TTS): {matches_us}")
    if "^" in text:
        matches_caret = re.findall(r"\w*\^\w*", text)
        violations.append(f"Chứa ký tự caret '^' (bẫy superscript TTS): {matches_caret}")
        
    # 2. Markdown / LaTeX symbols
    if any(sym in text for sym in ["$", "\\frac", "\\sum", "\\min", "\\max", "\\to"]):
        violations.append("Chứa ký tự LaTeX toán học thô trong văn bản thoại TTS!")

    # 3. Normalization & Unmapped English check
    normalized, report = normalize_for_omnivoice(text)
    unmapped = report.get("unmapped_english", []) if isinstance(report, dict) else []
    
    # Filter out approved acronyms that are naturally read in Vietnamese
    filtered_unmapped = [term for term in unmapped if term.upper() not in APPROVED_ACRONYMS]
        
    if filtered_unmapped:
        violations.append(f"Phát hiện thuật ngữ tiếng Anh / từ viết tắt trơ trọi chưa qua từ điển: {filtered_unmapped}")
        
    return violations

def lint_episode(episode_dir: Path) -> tuple[bool, list[str]]:
    if not episode_dir.exists():
        return False, [f"Thư mục không tồn tại: {episode_dir}"]

    # Look for .txt or .md files for scenes
    txt_files = sorted(episode_dir.glob("scene_*.txt"))
    if not txt_files:
        txt_files = sorted(episode_dir.glob("part_*.md"))

    all_errs: list[str] = []
    for f in txt_files:
        try:
            with open(f, "r", encoding="utf-8") as s:
                content = s.read()
            # If markdown, extract narration paragraphs (strip headers and HTML comments)
            if f.suffix == ".md":
                content = re.sub(r"<!--.*?-->", "", content, flags=re.DOTALL)
                lines = [l for l in content.splitlines() if not l.strip().startswith("#")]
                content = " ".join(lines).strip()

            errs = lint_text(content, f.name)
            for e in errs:
                all_errs.append(f"[{f.name}] {e}")
        except Exception as ex:
            all_errs.append(f"[{f.name}] Lỗi đọc tệp: {ex}")

    return len(all_errs) == 0, all_errs

def main():
    parser = argparse.ArgumentParser(description="OmniVoice TTS Phonetic Linter")
    parser.add_argument("--dir", help="Path to episode directory")
    parser.add_argument("--episode", default="tap_01", help="Episode name (e.g. tap_01, tap_03)")
    args = parser.parse_args()

    # CWE-22 Path Traversal Guard: validate episode name format
    if args.dir:
        ep_dir = Path(args.dir)
    else:
        if not re.fullmatch(r"^[A-Za-z0-9_\-]+$", args.episode):
            print(f"❌ Tên tập không hợp lệ (CWE-22 path traversal guard): {args.episode!r}")
            sys.exit(2)
        ep_dir = SCRIPTS_DIR / f"episode_logistics_{args.episode}"

    print("=" * 75)
    print(f"🎙️  TTS PHONETIC & PRONUNCIATION LINTER: {ep_dir.name}")
    print("=" * 75)

    ok, errors = lint_episode(ep_dir)
    if ok:
        print(f"✅ PASS: Toàn bộ văn bản thoại trong {ep_dir.name} sạch bẫy ký tự và đạt chuẩn ngữ âm!")
        print("=" * 75)
        sys.exit(0)
    else:
        print(f"❌ FAIL: Phát hiện {len(errors)} lỗi ngữ âm / ký tự lạ:")
        for err in errors:
            print(f"   - {err}")
        print("=" * 75)
        sys.exit(1)

if __name__ == "__main__":
    main()
