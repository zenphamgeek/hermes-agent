#!/usr/bin/env python3
"""Graydoom Codex-to-AGY Handoff Auditor & 4-Level Gemini 4 Argon Pro Dispatch Planner.

Synthesized via AGY-Fleet Pro Swarm (gemini-4-argon-high / gemini-4-argon-medium).
Inspects all 4 Graydoom git worktrees and branches:
  1. /home/zen/Downloads/Graydoom (codex/game-art-checkpoints-20260926 & main)
  2. /home/zen/.codex/worktrees/1ec4/Graydoom (codex/settlement-art-mapping-20261015)
  3. /home/zen/Downloads/Graydoom-art-atlas (codex/game-art-atlas-parallel-20261008)
  4. /home/zen/Downloads/Graydoom-novel (gemini-2)
Collects git branch/HEAD/dirty status, counts development-harness packets (gd-*.json),
SQL migrations, 26-character tri-lock catalogs, 2,081-slot atlas work orders, and
gemini-2 review verdicts, producing a structured handoff manifest and Obsidian
SecondBrain architecture report.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, field
import datetime
import json
from pathlib import Path
import subprocess
import sys
from typing import Any, Dict, List, Optional

WORKTREE_TARGETS: List[Dict[str, Any]] = [
    {
        "name": "main-and-security-checkpoints",
        "path": Path("/home/zen/Downloads/Graydoom"),
        "role": "Canonical Main & 8-Round Security / Source-Index Hardening",
    },
    {
        "name": "settlement-art-mapping",
        "path": Path("/home/zen/.codex/worktrees/1ec4/Graydoom"),
        "role": "Codex Live Gameplay, GM Controls & 40-Slot 2.5D/WebGL Settlement Mapping",
    },
    {
        "name": "game-art-atlas",
        "path": Path("/home/zen/Downloads/Graydoom-art-atlas"),
        "role": "Codex 2,081-Slot Game Art Atlas, Character Turnarounds & Spatial Maps",
    },
    {
        "name": "novel-gemini-2",
        "path": Path("/home/zen/Downloads/Graydoom-novel"),
        "role": "Novel 176 Chapters, 352 Scene Plates, 26 Multi-Card Dossiers & 6-Axis VLM QA",
    },
]

TRI_LOCK_REL_PATHS = [
    "content/canonical-characters-v1.json",
    "art/production/character-face-consistency-dna-v1.json",
    "art/production/character-face-expression-dossiers-v1.json",
]

OBSIDIAN_DEFAULT_VAULT = Path("/home/zen/Obsidian/SecondBrain")
OBSIDIAN_REL_PATH = Path("10-Areas/Architecture/Graydoom-Codex-to-AGY-Handoff.md")


@dataclass
class WorktreeAudit:
    name: str
    path: str
    exists: bool
    role: str = ""
    branch: Optional[str] = None
    head_sha: Optional[str] = None
    head_msg: Optional[str] = None
    is_dirty: bool = False
    uncommitted_count: int = 0
    dirty_files: List[str] = field(default_factory=list)
    harness_packets: int = 0
    sql_migrations: int = 0
    tri_lock_files: int = 0
    atlas_work_order_tasks: int = 0
    review_verdicts: Dict[str, int] = field(default_factory=dict)


@dataclass
class HandoffPlanTier:
    level: str
    complexity_range: str
    canonical_model: str
    tier: str
    dialectical_synthesis: bool
    target_tasks: List[str]


def _run_git(cwd: Path, args: List[str]) -> Optional[str]:
    try:
        res = subprocess.run(
            ["git"] + args,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
        if res.returncode == 0:
            return res.stdout.strip()
    except Exception:
        pass
    return None


def audit_worktree(target: Dict[str, Any]) -> WorktreeAudit:
    name = target["name"]
    p: Path = Path(target["path"])
    role = str(target.get("role", ""))

    if not p.exists() or not p.is_dir():
        return WorktreeAudit(name=name, path=str(p), exists=False, role=role)

    branch = _run_git(p, ["rev-parse", "--abbrev-ref", "HEAD"])
    head_sha = _run_git(p, ["rev-parse", "--short", "HEAD"])
    head_msg = _run_git(p, ["log", "-1", "--format=%s"])
    status_porcelain = _run_git(p, ["status", "--porcelain"])

    uncommitted_lines = [
        line.strip() for line in (status_porcelain or "").splitlines() if line.strip()
    ]
    is_dirty = len(uncommitted_lines) > 0
    uncommitted_count = len(uncommitted_lines)

    harness_packets = len(list(p.glob("config/development-harness/changes/gd-*.json")))
    sql_migrations = len(list((p / "migrations").glob("*.sql"))) if (p / "migrations").exists() else 0

    tri_lock_files = sum(1 for rel in TRI_LOCK_REL_PATHS if (p / rel).is_file())
    if (p / "art/production/character-master-dossiers-v2.json").is_file() and tri_lock_files == 0:
        tri_lock_files = 1

    atlas_tasks = 0
    atlas_file = p / "art/production/game-art-atlas-work-orders-v1.json"
    if atlas_file.is_file():
        try:
            atlas_data = json.loads(atlas_file.read_text(encoding="utf-8"))
            atlas_tasks = sum(int(v) for v in atlas_data.get("counts", {}).get("tasks", {}).values())
        except Exception:
            atlas_tasks = 0

    review_file = p / "art/production/review-decisions-v1.json"
    verdicts: Dict[str, int] = {}
    if review_file.is_file():
        try:
            data = json.loads(review_file.read_text(encoding="utf-8"))
            decisions = data.get("decisions", data) if isinstance(data, dict) else data
            if isinstance(decisions, dict):
                for item in decisions.values():
                    status = str(item.get("status") or item.get("verdict") or "UNKNOWN") if isinstance(item, dict) else str(item)
                    verdicts[status] = verdicts.get(status, 0) + 1
        except Exception:
            pass

    return WorktreeAudit(
        name=name,
        path=str(p),
        exists=True,
        role=role,
        branch=branch,
        head_sha=head_sha,
        head_msg=head_msg,
        is_dirty=is_dirty,
        uncommitted_count=uncommitted_count,
        dirty_files=uncommitted_lines[:25],
        harness_packets=harness_packets,
        sql_migrations=sql_migrations,
        tri_lock_files=tri_lock_files,
        atlas_work_order_tasks=atlas_tasks,
        review_verdicts=verdicts,
    )


def build_handoff_plan(audits: List[WorktreeAudit]) -> List[HandoffPlanTier]:
    total_dirty = sum(a.uncommitted_count for a in audits if a.exists)
    max_packets = max((a.harness_packets for a in audits if a.exists), default=0)
    max_migrations = max((a.sql_migrations for a in audits if a.exists), default=0)
    max_atlas = max((a.atlas_work_order_tasks for a in audits if a.exists), default=0)

    return [
        HandoffPlanTier(
            level="L1_TRIVIAL",
            complexity_range="0.0 <= C < 1.2",
            canonical_model="gemini-4-argon-low",
            tier="pro",
            dialectical_synthesis=False,
            target_tasks=[
                f"Package {total_dirty} in-flight uncommitted changes across worktrees into atomic commits",
                "Run build-content-source-index.py --write and verify SHA-256 manifest pins",
                "Sync 4-doc headers (product-spec, technical-spec, implementation-tracker, travianz-parity-register)",
            ],
        ),
        HandoffPlanTier(
            level="L2_STANDARD",
            complexity_range="1.2 <= C < 2.2",
            canonical_model="gemini-4-argon-medium",
            tier="pro",
            dialectical_synthesis=False,
            target_tasks=[
                f"Validate {max_packets} gd-<slug>.json development-harness packets and {max_migrations} SQL migrations",
                "Verify 26-Character Tri-Lock consistency (verify-character-dossiers.js & verify:consort-identities)",
                "Execute 11% alpha margin, alpha 1-7 fringe derivative, and 72px Lanczos building readability checks",
            ],
        ),
        HandoffPlanTier(
            level="L3_COMPLEX",
            complexity_range="2.2 <= C < 3.0",
            canonical_model="gemini-4-argon-high",
            tier="pro",
            dialectical_synthesis=False,
            target_tasks=[
                f"Coordinate 40-slot 2.5D/WebGL settlement lot mapping & {max_atlas}-slot Game Art Atlas work orders",
                "Complete migration 078_world_gm_gold_adjustments.sql + gd-registered-gm-gold-adjustment-v1.json packet",
                "Verify 390x844 disposable PostgreSQL world mobile browser QA with zero horizontal overflow",
            ],
        ),
        HandoffPlanTier(
            level="L4_SOVEREIGN",
            complexity_range="C >= 3.0",
            canonical_model="gemini-4-argon-high",
            tier="pro",
            dialectical_synthesis=True,
            target_tasks=[
                "Multi-worktree convergence across main, codex/settlement-art-mapping-20261015, and codex/game-art-atlas-parallel-20261008",
                "Cross-track identity lock synchronization between main/codex Engine track and gemini-2 Novel (352 plates / 26 dossiers)",
                "Full TravianZ 3dbe9c71 gameplay parity certification and release-readiness gate verification",
            ],
        ),
    ]


def render_markdown_report(audits: List[WorktreeAudit], plan: List[HandoffPlanTier]) -> str:
    now_iso = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines: List[str] = [
        "# Gray Doom Codex-to-AGY Fleet Sovereign Handoff Dossier",
        "",
        f"> [!IMPORTANT]",
        f"> **Generated**: `{now_iso}`  ",
        f"> **Target Swarm**: `17 Standard Pro Nodes (tier='pro', 4-Level Gemini 4 Argon)`  ",
        f"> **Installed Skills**: `graydoom-codex-harness`, `graydoom-character-and-art-logic`, `graydoom-handoff-navigator`, `graydoom_art`  ",
        f"> **Navigation**: [[Home]] | [[Cognitive-Memory-Matrix]] | [[Decisions]]",
        "",
        "## 1. Multi-Worktree & Multi-Branch Inspection Matrix",
        "",
        "| Worktree | Branch | HEAD | Dirty Files | Harness Packets | SQL Migrations | Tri-Lock | Atlas Tasks | Review Verdicts |",
        "| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |",
    ]

    for a in audits:
        if not a.exists:
            lines.append(f"| **{a.name}** | *N/A* | *N/A* | - | - | - | - | - | *Missing* |")
            continue
        dirty_str = f"⚠️ `{a.uncommitted_count}`" if a.is_dirty else "✅ `0`"
        verdicts_str = ", ".join(f"{k}:{v}" for k, v in sorted(a.review_verdicts.items())) or "-"
        lines.append(
            f"| **{a.name}**<br>`{a.path}` | `{a.branch}` | `{a.head_sha}` | {dirty_str} | `{a.harness_packets}` | `{a.sql_migrations}` | `{a.tri_lock_files}/3` | `{a.atlas_work_order_tasks}` | {verdicts_str} |"
        )

    lines.extend(["", "## 2. In-Flight Uncommitted Work Detected Across Codex Worktrees", ""])
    for a in audits:
        if a.exists and a.dirty_files:
            lines.append(f"### `{a.name}` (`{a.branch}` @ `{a.head_sha}` — *{a.head_msg}*)")
            for df in a.dirty_files:
                lines.append(f"- `{df}`")
            lines.append("")

    lines.extend(["## 3. 4-Level Gemini 4 Argon (`tier=\"pro\"`) Handoff Execution Plan", ""])
    for tier in plan:
        synth_badge = " + Dialectical Council" if tier.dialectical_synthesis else ""
        lines.append(f"### {tier.level} (`{tier.complexity_range}`) — `{tier.canonical_model}` (`tier=\"{tier.tier}\"`{synth_badge})")
        for t in tier.target_tasks:
            lines.append(f"- [ ] {t}")
        lines.append("")

    lines.extend([
        "---",
        "*Generated by `tools/graydoom_codex_handoff_auditor.py`.*",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Graydoom Codex-to-AGY Handoff Auditor")
    parser.add_argument("--json", action="store_true", help="Output JSON report")
    parser.add_argument("--write-report", "--write-obsidian", dest="write_obsidian", action="store_true", help="Write report to Obsidian SecondBrain")
    parser.add_argument("--obsidian-vault", type=Path, default=OBSIDIAN_DEFAULT_VAULT, help="Obsidian SecondBrain vault path")
    parser.add_argument("--output", type=Path, default=None, help="Optional custom Markdown output path")
    args = parser.parse_args()

    audits = [audit_worktree(t) for t in WORKTREE_TARGETS]
    plan = build_handoff_plan(audits)
    md = render_markdown_report(audits, plan)

    if args.write_obsidian and args.obsidian_vault.exists():
        out_path = args.obsidian_vault / OBSIDIAN_REL_PATH
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(md, encoding="utf-8")

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(md, encoding="utf-8")

    if args.json:
        print(json.dumps({
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "worktrees": [asdict(a) for a in audits],
            "handoff_plan": [asdict(p) for p in plan],
        }, indent=2, ensure_ascii=False))
    else:
        print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
