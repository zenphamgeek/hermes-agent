#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools/audit_diff_classifier.py
==============================
Asset-vs-Code Diff Router & Classifier for Swarm Security Audits.

Retires audit budget exhaustion and signal dilution on inert assets
(subtitles, audio, declarative Manim geometry, documentation) while strictly
escalating code files, invariant rule changes, AST dynamic execution, and
tampered assets containing high-entropy secrets or Trojan Source BiDi unicode.

Complies with Sovereign Invariants:
- 1.1 Council Integrity & Zero-Fake-Pass
- 1.2 Evidence-First Verification
"""

from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import re
import subprocess
import sys
from typing import Dict, List, Optional, Set, Tuple

try:
    from tools.mem0_audit_consolidation_gate import (
        Mem0ConsolidationGate,
        FindingSeverity,
        ConsolidatedRuleCandidate,
    )
except ImportError:
    # Fallback if executed with different PYTHONPATH
    from mem0_audit_consolidation_gate import (  # type: ignore
        Mem0ConsolidationGate,
        FindingSeverity,
        ConsolidatedRuleCandidate,
    )


class DiffCategory(str, Enum):
    SECURITY_RELEVANT = "security-relevant"
    INERT_ASSET = "inert-asset"
    REVIEW_MANUALLY = "review-manually"


@dataclass
class ClassificationResult:
    path: str
    category: DiffCategory
    reasons: List[str]
    escalated_from_inert: bool = False
    sanity_issues: List[str] = field(default_factory=list)


SECURITY_KEYWORDS: Tuple[str, ...] = (
    "auth",
    "token",
    "secret",
    "credential",
    "session",
    "route",
    "handler",
    "endpoint",
    "client",
    "api",
    "rpc",
    "db",
    "query",
    "subprocess",
    "exec",
    "crypto",
    "permission",
    "sanitiz",
)

SECURITY_CODE_EXTENSIONS: Set[str] = {
    ".py",
    ".ts",
    ".js",
    ".tsx",
    ".jsx",
    ".sh",
    ".sql",
}

BINARY_MEDIA_EXTENSIONS: Set[str] = {
    ".wav",
    ".mp3",
    ".mp4",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".svg",
    ".webp",
    ".ico",
    ".ttf",
    ".otf",
    ".woff",
    ".woff2",
}


def scan_inert_sanity(path_str: str, content: str) -> List[str]:
    """
    Scans content of an inert asset candidate for hidden security hazards:
    - High-entropy secrets (OpenAI sk-, GitHub ghp_, Bearer tokens)
    - Embedded credentials or secret query parameters in URLs
    - Null bytes in text assets (\x00)
    - Trojan Source Unicode BiDi direction-override characters
    """
    issues: List[str] = []
    if not content:
        return issues

    # 1. High-entropy secrets
    if re.search(r"sk-[a-zA-Z0-9]{20,}", content):
        issues.append("Detected high-entropy secret (pattern: sk-[...])")
    if re.search(r"ghp_[a-zA-Z0-9]{20,}", content):
        issues.append("Detected high-entropy secret (pattern: ghp_[...])")
    if re.search(r"Bearer\s+[a-zA-Z0-9._-]{25,}", content, re.IGNORECASE):
        issues.append("Detected high-entropy secret (pattern: Bearer token)")

    # 2. Embedded credentials in URLs
    if re.search(r"https?://[^:\s]+:[^@\s]+@", content):
        issues.append("Detected embedded credentials in URL")
    if re.search(r"[\?&](?:token|key|secret|api_key)=[a-zA-Z0-9_-]{16,}", content, re.IGNORECASE):
        issues.append("Detected sensitive token/key query parameter in URL")

    # 3. Null byte check (only for non-binary assets)
    ext = Path(path_str).suffix.lower()
    if ext not in BINARY_MEDIA_EXTENSIONS:
        if "\x00" in content:
            issues.append(r"Detected null byte (\x00) in text asset")

    # 4. Trojan Source BiDi unicode check
    bidi_match = re.search(r"[\u202a-\u202e\u2066-\u2069]", content)
    if bidi_match:
        char_hex = f"U+{ord(bidi_match.group(0)):04X}"
        issues.append(f"Detected Trojan Source BiDi Unicode character ({char_hex})")

    return issues


class _ManimASTInspector(ast.NodeVisitor):
    """
    Inspects Manim scene AST for dynamic execution, subprocess invocation, or network calls.
    Declarative geometry and mathematical animations are pure; dynamic system calls trigger escalation.
    """

    def __init__(self) -> None:
        self.suspicious: List[str] = []

    def _resolve_call_name(self, node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            parent = self._resolve_call_name(node.value)
            return f"{parent}.{node.attr}" if parent else node.attr
        return ""

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            name = alias.name
            if name in ("subprocess", "socket", "urllib", "requests") or name.startswith(
                ("subprocess.", "socket.", "urllib.", "requests.")
            ):
                self.suspicious.append(f"import {name}")
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        mod = node.module or ""
        if mod in ("subprocess", "socket", "urllib", "requests") or mod.startswith(
            ("subprocess.", "socket.", "urllib.", "requests.")
        ):
            self.suspicious.append(f"from {mod} import ...")
        elif mod == "os":
            for alias in node.names:
                if alias.name in ("system", "popen", "spawn", "execl", "execv", "execle", "execlp"):
                    self.suspicious.append(f"from os import {alias.name}")
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        name = self._resolve_call_name(node.func)
        if name in ("eval", "exec", "system", "popen", "Popen", "spawn"):
            self.suspicious.append(f"call to {name}()")
        elif name.startswith((
            "subprocess.",
            "os.system",
            "os.popen",
            "os.spawn",
            "os.exec",
            "urllib.",
            "requests.",
            "socket.",
        )):
            self.suspicious.append(f"call to {name}()")
        self.generic_visit(node)


def is_manim_animation_pattern(norm_path: str) -> bool:
    """
    Checks if path matches declarative Manim scene geometry conventions:
    - assets/manim/*.py
    - manim_*.py
    - tests/test_manim_*.py
    """
    if not norm_path.endswith(".py"):
        return False
    parts = norm_path.split("/")
    filename = parts[-1]
    if "assets/manim/" in norm_path or norm_path.startswith("assets/manim/"):
        return True
    if filename.startswith("manim_"):
        return True
    if filename.startswith("test_manim_"):
        return True
    return False


def _check_manim_ast(content: str) -> List[str]:
    """Parses Python AST and returns list of suspicious calls/imports."""
    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        return [f"AST parse syntax error: {e}"]
    except Exception as e:
        return [f"AST analysis error: {e}"]

    inspector = _ManimASTInspector()
    inspector.visit(tree)
    return inspector.suspicious


def classify_path(path_str: str, file_content: Optional[str] = None) -> ClassificationResult:
    """
    Core Classifier: Evaluates a file path and optional content into DiffCategory.

    Classification Flow:
    1. Security Invariants (.agents/rules/) -> SECURITY_RELEVANT
    2. Declarative Manim Scripts -> AST Gate (clean -> INERT_ASSET, suspicious -> SECURITY_RELEVANT)
    3. Inert Asset Candidates (youtube_staging/, assets/audio, assets/brand, .srt, .md, media)
       -> Sanity Scan (clean -> INERT_ASSET, tainted -> SECURITY_RELEVANT)
    4. Code Files (.py, .ts, .js, .tsx, .jsx, .sh, .sql) -> SECURITY_RELEVANT
    5. Security Keyword Matches -> SECURITY_RELEVANT
    6. Others -> REVIEW_MANUALLY
    """
    norm_path = path_str.replace("\\", "/").lower()
    ext = Path(norm_path).suffix

    # Attempt to load content from disk if not provided and file exists
    content = file_content
    if content is None:
        p = Path(path_str)
        if p.is_file() and ext not in BINARY_MEDIA_EXTENSIONS:
            try:
                content = p.read_text(encoding="utf-8", errors="replace")
            except Exception:
                content = None

    # 1. Sovereign Invariants Gate: Rules in .agents/rules/ define security boundaries
    if ".agents/rules/" in norm_path or norm_path.startswith(".agents/rules/"):
        return ClassificationResult(
            path=path_str,
            category=DiffCategory.SECURITY_RELEVANT,
            reasons=["Security rule definition in .agents/rules/ defines sovereign invariants"],
        )

    # 2. Declarative Manim Animation Gate
    if is_manim_animation_pattern(norm_path):
        if content is not None:
            suspicious = _check_manim_ast(content)
            if suspicious:
                return ClassificationResult(
                    path=path_str,
                    category=DiffCategory.SECURITY_RELEVANT,
                    reasons=[
                        f"AST escalation: contains dynamic execution / subprocess / network call ({', '.join(suspicious)})"
                    ],
                    escalated_from_inert=True,
                )
            # AST is clean; perform inert sanity scan
            sanity = scan_inert_sanity(path_str, content)
            if sanity:
                return ClassificationResult(
                    path=path_str,
                    category=DiffCategory.SECURITY_RELEVANT,
                    reasons=[f"Inert asset sanity violation: {s}" for s in sanity],
                    escalated_from_inert=True,
                    sanity_issues=sanity,
                )
            return ClassificationResult(
                path=path_str,
                category=DiffCategory.INERT_ASSET,
                reasons=["Declarative Manim animation script with clean AST"],
            )
        else:
            # File content not accessible (e.g. deleted or virtual test path)
            return ClassificationResult(
                path=path_str,
                category=DiffCategory.INERT_ASSET,
                reasons=["Declarative Manim animation pattern (uninspected)"],
            )

    # 3. Inert Asset Candidates
    is_inert_candidate = False
    inert_reason = ""

    if ext == ".srt":
        is_inert_candidate = True
        inert_reason = "Subtitles asset (.srt)"
    elif "youtube_staging/" in norm_path or norm_path.startswith("youtube_staging/"):
        if ext in (".srt", ".txt", ".json"):
            is_inert_candidate = True
            inert_reason = f"YouTube staging asset ({ext})"
    elif "assets/audio/" in norm_path or norm_path.startswith("assets/audio/"):
        is_inert_candidate = True
        inert_reason = "Audio asset directory"
    elif "assets/brand/" in norm_path or norm_path.startswith("assets/brand/"):
        is_inert_candidate = True
        inert_reason = "Brand asset directory"
    elif ext in BINARY_MEDIA_EXTENSIONS:
        is_inert_candidate = True
        inert_reason = f"Binary media asset ({ext})"
    elif ext == ".md":
        is_inert_candidate = True
        inert_reason = "Markdown documentation (.md)"

    if is_inert_candidate:
        if content is not None:
            sanity = scan_inert_sanity(path_str, content)
            if sanity:
                return ClassificationResult(
                    path=path_str,
                    category=DiffCategory.SECURITY_RELEVANT,
                    reasons=[f"Inert asset sanity violation: {s}" for s in sanity],
                    escalated_from_inert=True,
                    sanity_issues=sanity,
                )
        return ClassificationResult(
            path=path_str,
            category=DiffCategory.INERT_ASSET,
            reasons=[inert_reason],
        )

    # 4. Code Extensions Gate
    matched_keywords = [kw for kw in SECURITY_KEYWORDS if kw in norm_path]

    if ext in SECURITY_CODE_EXTENSIONS:
        reasons = [f"Code file ({ext}) requires security audit"]
        if matched_keywords:
            reasons.append(f"Path matches security keywords: {', '.join(matched_keywords)}")
        return ClassificationResult(
            path=path_str,
            category=DiffCategory.SECURITY_RELEVANT,
            reasons=reasons,
        )

    # 5. Security Keywords in non-code path
    if matched_keywords:
        return ClassificationResult(
            path=path_str,
            category=DiffCategory.SECURITY_RELEVANT,
            reasons=[f"Path matches security keywords: {', '.join(matched_keywords)}"],
        )

    # 6. Unrecognized paths -> REVIEW_MANUALLY
    return ClassificationResult(
        path=path_str,
        category=DiffCategory.REVIEW_MANUALLY,
        reasons=["Unrecognized file type or path pattern: manual review required"],
    )


def get_git_diff_names(
    repo_root: Path,
    base: str = "HEAD~1",
    target: str = "HEAD",
    staged: bool = False,
) -> List[str]:
    """Retrieves list of changed file paths from Git."""
    cmd = ["git", "-C", str(repo_root), "diff", "--name-only"]
    if staged:
        cmd.append("--cached")
    else:
        cmd.extend([base, target])

    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            return []
        return [line.strip() for line in proc.stdout.splitlines() if line.strip()]
    except Exception:
        return []


def classify_git_diff(
    repo_root: Path,
    base: str = "HEAD~1",
    target: str = "HEAD",
    staged: bool = False,
) -> Dict[DiffCategory, List[ClassificationResult]]:
    """Classifies all files changed in the git diff."""
    names = get_git_diff_names(repo_root, base=base, target=target, staged=staged)
    grouped: Dict[DiffCategory, List[ClassificationResult]] = {
        DiffCategory.SECURITY_RELEVANT: [],
        DiffCategory.INERT_ASSET: [],
        DiffCategory.REVIEW_MANUALLY: [],
    }

    for rel_path in names:
        file_path = repo_root / rel_path
        content = None
        if staged:
            try:
                proc = subprocess.run(
                    ["git", "-C", str(repo_root), "show", f":{rel_path}"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=False,
                )
                if proc.returncode == 0:
                    content = proc.stdout
            except Exception:
                pass
        if content is None and file_path.is_file():
            try:
                content = file_path.read_text(encoding="utf-8", errors="replace")
            except Exception:
                content = None

        res = classify_path(rel_path, file_content=content)
        grouped[res.category].append(res)

    return grouped


def record_diff_audit_to_mem0(
    classified_results: List[ClassificationResult],
    mem0_gate: Optional[Mem0ConsolidationGate] = None,
    step_index: int = 1,
) -> Optional[Tuple[bool, Optional[ConsolidatedRuleCandidate]]]:
    """
    Hooks into Mem0ConsolidationGate:
    When >= 80% of files in a diff are INERT_ASSET, records an episodic observation
    'AUDIT_DIFF_ROUTED_INERT' to suppress full CWE heavy scanning.
    """
    if not classified_results:
        return None

    if mem0_gate is None:
        mem0_gate = Mem0ConsolidationGate()

    total = len(classified_results)
    inert_count = sum(1 for r in classified_results if r.category == DiffCategory.INERT_ASSET)
    ratio = inert_count / total

    if ratio >= 0.80:
        desc = (
            f"Diff classified as predominantly inert ({inert_count}/{total} files, "
            f"{ratio * 100:.1f}% inert); suppressing full CWE heavy scanning."
        )
        return mem0_gate.record_observation(
            finding_id=f"audit-diff-inert-step-{step_index}",
            category="AUDIT_DIFF_ROUTED_INERT",
            severity=FindingSeverity.INFO,
            description=desc,
            step_index=step_index,
        )
    return None


def main(argv: Optional[List[str]] = None) -> int:
    """
    CLI Interface for Asset-vs-Code Diff Router & Classifier.
    Returns:
      1 if any SECURITY_RELEVANT files exist.
      0 if 100% inert or clean.
    """
    parser = argparse.ArgumentParser(
        description="Asset-vs-Code Diff Router & Classifier for Swarm Security Audits"
    )
    parser.add_argument(
        "--file",
        type=str,
        help="Classify a single file path",
    )
    parser.add_argument(
        "--staged",
        action="store_true",
        help="Inspect staged git changes",
    )
    parser.add_argument(
        "--base",
        type=str,
        default="HEAD~1",
        help="Git diff base commit/ref (default: HEAD~1)",
    )
    parser.add_argument(
        "--target",
        type=str,
        default="HEAD",
        help="Git diff target commit/ref (default: HEAD)",
    )
    parser.add_argument(
        "--repo-root",
        type=str,
        default=".",
        help="Path to repository root (default: current directory)",
    )
    parser.add_argument(
        "--hook-mem0",
        action="store_true",
        help="Record observation to Mem0 consolidation gate if >= 80%% inert",
    )

    args = parser.parse_args(argv)
    repo_root = Path(args.repo_root).resolve()
    results: List[ClassificationResult] = []

    if args.file:
        file_path = Path(args.file)
        content = None
        if file_path.is_file():
            try:
                content = file_path.read_text(encoding="utf-8", errors="replace")
            except Exception:
                content = None
        results.append(classify_path(args.file, file_content=content))
    elif args.staged:
        grouped = classify_git_diff(repo_root, base=args.base, target=args.target, staged=True)
        for items in grouped.values():
            results.extend(items)
    elif not sys.stdin.isatty():
        stdin_lines = [line.strip() for line in sys.stdin.readlines() if line.strip()]
        for p in stdin_lines:
            fpath = repo_root / p
            content = None
            if fpath.is_file():
                try:
                    content = fpath.read_text(encoding="utf-8", errors="replace")
                except Exception:
                    content = None
            results.append(classify_path(p, file_content=content))
    else:
        grouped = classify_git_diff(repo_root, base=args.base, target=args.target, staged=args.staged)
        for items in grouped.values():
            results.extend(items)

    security_count = sum(1 for r in results if r.category == DiffCategory.SECURITY_RELEVANT)
    inert_count = sum(1 for r in results if r.category == DiffCategory.INERT_ASSET)
    review_count = sum(1 for r in results if r.category == DiffCategory.REVIEW_MANUALLY)

    for r in results:
        status_tag = f"[{r.category.value.upper()}]"
        escalated_tag = " (ESCALATED)" if r.escalated_from_inert else ""
        print(f"{status_tag}{escalated_tag} {r.path}: {'; '.join(r.reasons)}")
        if r.sanity_issues:
            for issue in r.sanity_issues:
                print(f"  - SANITY VIOLATION: {issue}")

    if args.hook_mem0 and results:
        mem0_res = record_diff_audit_to_mem0(results)
        if mem0_res:
            print("\n[MEM0] Recorded AUDIT_DIFF_ROUTED_INERT observation to Mem0 gate.")

    print(
        f"\nSummary: {len(results)} files classified | "
        f"{security_count} security-relevant, {inert_count} inert, {review_count} review-manually."
    )

    if security_count > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
