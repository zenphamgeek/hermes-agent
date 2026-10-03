#!/usr/bin/env python3
"""Superseded-concept candidate scanner (memory-curator skill, Clef Mnemosyne P2).

READ-ONLY. Scans L3 normative memory (AGENTS.md, .agents/rules/*.md,
.agents/skills/*/SKILL.md) for mentions of concepts listed in a deprecation
registry and pre-labels each hit:

  * ``mentions_as_deprecated``      -- a deprecation marker appears within
                                       +-N lines (the text likely *describes*
                                       the concept as abandoned/forbidden).
  * ``candidate_live_instruction``  -- no marker nearby; the text may still be
                                       instructing agents to use the concept.

The pre-label is a cheap heuristic for candidate gathering (design section
4.3 step 1). It is NOT a classification verdict; a Judge must review each hit.
This script never opens scanned files for writing.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_REPO = Path(__file__).resolve().parents[4]
DEFAULT_REGISTRY = SCRIPT_DIR.parent / "resources" / "deprecations.json"

LIVE = "candidate_live_instruction"
DEPRECATED = "mentions_as_deprecated"
# The curator's own skill quotes deprecated concepts as teaching examples.
SELF_EXCLUDE = {"memory-curator"}

# Uppercase markers are case-sensitive so ordinary prose "not" does not count.
MARKERS: list[tuple[str, re.Pattern[str]]] = [
    ("ABANDONED", re.compile(r"\bABANDONED\b")),
    ("FORBIDDEN", re.compile(r"\bFORBIDDEN\b")),
    ("NOT", re.compile(r"\bNOT\b")),
    ("KHÔNG", re.compile(r"(?<!\w)KHÔNG(?!\w)")),
    ("deprecated", re.compile(r"deprecat", re.IGNORECASE)),
    ("legacy", re.compile(r"\blegacy\b", re.IGNORECASE)),
    ("bỏ", re.compile(r"(?<!\w)bỏ(?!\w)", re.IGNORECASE)),
    ("cấm", re.compile(r"(?<!\w)cấm(?!\w)", re.IGNORECASE)),
    ("cũ", re.compile(r"(?<!\w)cũ(?!\w)", re.IGNORECASE)),
]


def load_registry(path: Path) -> list[dict]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    concepts = []
    for c in data["concepts"]:
        concepts.append({**c, "_rx": [re.compile(p, re.IGNORECASE) for p in c["patterns"]]})
    return concepts


def iter_target_files(repo: Path) -> list[Path]:
    repo = Path(repo)
    files: list[Path] = []
    if (repo / "AGENTS.md").is_file():
        files.append(repo / "AGENTS.md")
    files += sorted((repo / ".agents" / "rules").glob("*.md"))
    files += sorted(p for p in (repo / ".agents" / "skills").glob("*/SKILL.md")
                    if p.parent.name not in SELF_EXCLUDE)
    return files


def _markers_in(lines: list[str]) -> list[str]:
    found = []
    for name, rx in MARKERS:
        if any(rx.search(ln) for ln in lines):
            found.append(name)
    return found


def scan(repo: Path, concepts: list[dict], context: int = 3) -> list[dict]:
    repo = Path(repo)
    hits: list[dict] = []
    for path in iter_target_files(repo):
        with open(path, "r", encoding="utf-8", errors="replace") as fh:  # read-only
            lines = fh.read().splitlines()
        rel = path.relative_to(repo).as_posix()
        for idx, line in enumerate(lines):
            for c in concepts:
                m = next((mm for rx in c["_rx"] if (mm := rx.search(line))), None)
                if m is None:
                    continue
                window = lines[max(0, idx - context): idx + context + 1]
                markers = _markers_in(window)
                hits.append({
                    "file": rel,
                    "line": idx + 1,
                    "concept_id": c["id"],
                    "matched": m.group(0),
                    "snippet": line.strip()[:240],
                    "pre_label": DEPRECATED if markers else LIVE,
                    "markers_found": markers,
                })
    return hits


def render_markdown(hits: list[dict], repo: Path) -> str:
    by_label = Counter(h["pre_label"] for h in hits)
    by_concept = Counter(h["concept_id"] for h in hits)
    by_file = Counter(h["file"] for h in hits)
    out = [
        "# Superseded-Concept Scan (read-only)",
        "",
        f"- Repo: `{repo}`",
        f"- Generated: {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        f"- Total hits: **{len(hits)}** across **{len(by_file)}** files",
        "",
        "> Pre-labels are heuristic (marker within +-N lines). They are candidates, not verdicts.",
        "",
        "| Pre-label | Count |", "|---|---|",
        *[f"| `{k}` | {v} |" for k, v in sorted(by_label.items())],
        "",
        "| Concept | Count |", "|---|---|",
        *[f"| `{k}` | {v} |" for k, v in sorted(by_concept.items())],
        "",
        "| # | File | Line | Concept | Pre-label | Snippet |",
        "|---|---|---|---|---|---|",
    ]
    for i, h in enumerate(hits, 1):
        snip = h["snippet"].replace("|", "\\|")
        out.append(f"| {i} | `{h['file']}` | {h['line']} | `{h['concept_id']}` | `{h['pre_label']}` | {snip} |")
    return "\n".join(out) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repo", type=Path, default=DEFAULT_REPO)
    ap.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    ap.add_argument("--out", type=Path, default=Path("/tmp"))
    ap.add_argument("--context", type=int, default=3)
    args = ap.parse_args(argv)

    repo = args.repo.resolve()
    hits = scan(repo, load_registry(args.registry), args.context)
    args.out.mkdir(parents=True, exist_ok=True)
    by_label = dict(Counter(h["pre_label"] for h in hits))
    json_path = args.out / "superseded_scan.json"
    md_path = args.out / "superseded_scan.md"
    json_path.write_text(json.dumps({
        "repo": str(repo),
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "total_hits": len(hits),
        "by_label": by_label,
        "hits": hits,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(render_markdown(hits, repo), encoding="utf-8")
    print(f"hits={len(hits)} by_label={by_label}")
    print(f"json: {json_path}\nmarkdown: {md_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
