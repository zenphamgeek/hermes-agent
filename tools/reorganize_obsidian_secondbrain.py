#!/usr/bin/env python3
"""
tools/reorganize_obsidian_secondbrain.py
Reorganizes and unifies the local Obsidian SecondBrain vaults:
  1. Canonical SecondBrain Vault: /home/zen/Obsidian/SecondBrain
  2. Dev Operational Vault:       /home/zen/Downloads/Dev
  3. Live Knowledge Compiler DB:  ~/.hermes/knowledge_compiler.db
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sqlite3
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

DEFAULT_SECONDBRAIN = Path("/home/zen/Obsidian/SecondBrain")
DEFAULT_DEV_VAULT = Path("/home/zen/Downloads/Dev")
DEFAULT_COMPILER_DB = Path.home() / ".hermes" / "knowledge_compiler.db"
DEFAULT_TOMBSTONES = Path("/home/zen/hermes-agent/.agents/skills/memory-curator/resources/l3_tombstones.jsonl")

DEV_ROOT_MOVES: List[tuple[str, str]] = [
    ("Untitled.md", "0-Inbox/Insilos-Website-PDCA-and-Trae-Autopilot.md"),
    ("Untitled 1.md", "0-Inbox/NCSP-SRS-Extension-L3-Notes.md"),
    ("Untitled 2.md", "0-Inbox/JEV-Clef-and-OAuth-Notes.md"),
    ("PROMPT Antigravity.md", "1-Projects/Prompts/PROMPT Antigravity.md"),
    ("AGYROUTER.md", "1-Projects/Architecture/AGYROUTER.md"),
    ("Domain.md", "2-Areas/Account-Vault/Domain.md"),
    ("GPT Plan.md", "2-Areas/Account-Vault/GPT Plan.md"),
    ("Modal New.md", "2-Areas/Account-Vault/Modal New.md"),
    ("Thông tin system eco.md", "2-Areas/Account-Vault/Thông tin system eco.md"),
    ("Pasted image 20261016073636.png", "2-Areas/Account-Vault/Pasted image 20261016073636.png"),
    ("2026-08-18.md", "3-Resources/Personal/2026-08-18.md"),
]

NOISY_SYMLINK_PATTERNS = (
    "_next__static__chunks",
    "flutter__engine__src__flutter__lib__web_ui",
    "website__static__img__docs",
)

PROJECT_REPOS: Dict[str, tuple[str, str, str]] = {
    "hermes-agent": (
        "/home/zen/hermes-agent",
        "Data/Projects/hermes-agent__docs",
        "Autonomous AI Agent & Content Factory with 7-Repo AI Knowledge Compiler, Local JEV (<20ms, 0 output tokens), Clef Cloud, and 273 unified skills.",
    ),
    "zencode": (
        "/home/zen/zencode-ent/router",
        "Data/Projects/arouter__docs",
        "AGY Fleet Router v2.5 (17 Pro Swarm Nodes, Clef 4-Stage Sovereign Lifecycle, Autonomous DAG Worker, and Passive Quota Accounting).",
    ),
    "insilos_ee": (
        "/home/zen/O20",
        "Data/Projects/O20__docs",
        "Insilos Enterprise Platform on Odoo 20 (Native QWeb + Owl Component Architecture, Neo-Noir Obsidian UI tokens).",
    ),
    "VerticalRisk": (
        "/home/zen/VerticalRisk",
        "Data/Projects/VerticalRisk__docs",
        "VerticalRisk GRC, HSE-DPM, and NCSP Enterprise Risk & Compliance Platform.",
    ),
    "workspace": (
        "/home/zen",
        "Data/Projects/hermes-agent__docs",
        "Multi-Repo Sovereign Workstation Environment (ThinkPad P15 Quadro RTX 5000 16GB CUDA).",
    ),
}


def _git_summary(repo_dir: str) -> str:
    p = Path(repo_dir)
    if not (p / ".git").exists():
        return f"Directory `{repo_dir}` (active workspace)"
    try:
        branch = subprocess.run(
            ["git", "-C", repo_dir, "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, check=True, timeout=5
        ).stdout.strip()
        sha = subprocess.run(
            ["git", "-C", repo_dir, "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, check=True, timeout=5
        ).stdout.strip()
        subject = subprocess.run(
            ["git", "-C", repo_dir, "log", "-1", "--format=%s"],
            capture_output=True, text=True, check=True, timeout=5
        ).stdout.strip()
        return f"Branch `{branch}` @ `{sha}` — *{subject}*"
    except Exception:
        return f"Repository `{repo_dir}`"


def reorganize_dev_vault(dev_vault: Path, apply: bool = False) -> Dict[str, Any]:
    moved: List[Dict[str, str]] = []
    cleaned_Scratch: List[str] = []

    if not dev_vault.exists():
        return {"exists": False, "moved": moved}

    # 1. Remove empty Untitled/ folder and empty Untitled.base
    untitled_dir = dev_vault / "Untitled"
    if untitled_dir.exists() and untitled_dir.is_dir() and not any(untitled_dir.iterdir()):
        if apply:
            untitled_dir.rmdir()
        cleaned_Scratch.append("Untitled/")

    untitled_base = dev_vault / "Untitled.base"
    if untitled_base.exists() and untitled_base.stat().st_size <= 64:
        if apply:
            untitled_base.unlink()
        cleaned_Scratch.append("Untitled.base")

    # 2. Move loose root files into structured PARA directories (preserving 100% of content)
    for src_name, dst_rel in DEV_ROOT_MOVES:
        src = dev_vault / src_name
        dst = dev_vault / dst_rel
        if src.exists():
            if apply:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(src), str(dst))
            moved.append({"from": src_name, "to": dst_rel})

    # 3. Write clean Home.md in Dev vault
    home_md = dev_vault / "Home.md"
    home_content = """# Dev Operational Vault — Index & MOC

> **Liên kết đồng bộ**: Vault này được nối trực tiếp vào **[[Second Brain]]** tại `/home/zen/Obsidian/SecondBrain`.

## 🗺️ Maps of Content (MOC)
- [[Maps-of-Content/MOC-Daily-Digest|MOC Daily Digest]] (76 bản tổng hợp hàng ngày)
- [[Maps-of-Content/MOC-Projects|MOC Projects]]
- [[Maps-of-Content/MOC-Cost-Tracking|MOC Cost Tracking]]
- [[Maps-of-Content/MOC-AI-Models|MOC AI Models]]

## 🏗️ 1-Projects & Architecture
- [[1-Projects/Architecture/AGYROUTER|AGYRouter Local ONNX & Clef Decision Architecture]]
- [[1-Projects/Prompts/PROMPT Antigravity|Enterprise Sales & Marketing Playbook Prompts]]

## 🛡️ 2-Areas (Operational & Analytics)
- **AI Coding Sessions**: `2-Areas/AI-Coding-Patterns/` (830+ phiên làm việc tự động)
- **GPU & Cost Telemetry**:
  - [[2-Areas/GPU-Fleet-Analytics/2026-07-17_gpu_fleet_report|GPU Fleet Analytics]]
  - [[2-Areas/Cost-Analytics/2026-07-17_cost_summary|Cost Analytics]]
  - [[2-Areas/TokenSaver/2026-07-17_compression_stats|TokenSaver Compression Metrics]]
- **Account & Infrastructure Reference (`2-Areas/Account-Vault/`)**:
  - [[2-Areas/Account-Vault/Modal New|Modal Multi-Workspace Profiles]]
  - [[2-Areas/Account-Vault/GPT Plan|Account Subscription Schedule]]
  - [[2-Areas/Account-Vault/Domain|Domain & Backup Codes]]
  - [[2-Areas/Account-Vault/Thông tin system eco|System Ecosystem Endpoints]]

## 📥 0-Inbox (Captured Notes)
- [[0-Inbox/Insilos-Website-PDCA-and-Trae-Autopilot|Insilos Website PDCA & Trae Autopilot]]
- [[0-Inbox/NCSP-SRS-Extension-L3-Notes|NCSP SRS Extension L3 & HSE-DPM Reuse]]
- [[0-Inbox/JEV-Clef-and-OAuth-Notes|Local JEV + Clef Cloud & Consolidation Notes]]

## 📚 3-Resources
- `3-Resources/Model-Comparisons/`
- [[3-Resources/Personal/2026-08-18|Thơ & Ghi chép cá nhân (2026-08-18)]]
"""
    if apply:
        home_md.write_text(home_content, encoding="utf-8")

    return {
        "exists": True,
        "moved_count": len(moved),
        "moved": moved,
        "cleaned_scratch": cleaned_Scratch,
        "home_updated": apply,
    }


def reorganize_secondbrain_vault(
    sb_vault: Path,
    dev_vault: Path,
    compiler_db: Path,
    tombstones_path: Path,
    apply: bool = False,
) -> Dict[str, Any]:
    if not sb_vault.exists():
        return {"exists": False}

    cleaned_scratch: List[str] = []
    pruned_symlinks: List[str] = []
    bridged_links: List[str] = []

    # 1. Remove empty Untitled.base / Untitled 1.base
    for base_name in ("Untitled.base", "Untitled 1.base"):
        bf = sb_vault / base_name
        if bf.exists() and bf.stat().st_size <= 64:
            if apply:
                bf.unlink()
            cleaned_scratch.append(base_name)

    # 2. Prune noisy Next.js / Flutter build chunk symlinks in Data/Projects/
    dp_dir = sb_vault / "Data" / "Projects"
    managed_json_path = dp_dir / ".managed-links.json"
    managed_map: Dict[str, str] = {}
    if managed_json_path.exists():
        try:
            managed_map = json.loads(managed_json_path.read_text(encoding="utf-8"))
        except Exception:
            managed_map = {}

    if dp_dir.exists():
        for item in sorted(dp_dir.iterdir()):
            if item.name.startswith("."):
                continue
            if any(pat in item.name for pat in NOISY_SYMLINK_PATTERNS):
                pruned_symlinks.append(item.name)
                managed_map.pop(item.name, None)
                if apply and (item.is_symlink() or item.exists()):
                    item.unlink()

    if apply and managed_json_path.exists():
        managed_json_path.write_text(
            json.dumps(managed_map, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    # 3. Bridge Dev Vault session logs & analytics into SecondBrain/10-Areas/AI Engineering/
    bridge_targets = [
        ("AI-Coding-Sessions", dev_vault / "2-Areas" / "AI-Coding-Patterns"),
        ("GPU-Fleet-Analytics", dev_vault / "2-Areas" / "GPU-Fleet-Analytics"),
        ("Cost-Analytics", dev_vault / "2-Areas" / "Cost-Analytics"),
        ("TokenSaver-Telemetry", dev_vault / "2-Areas" / "TokenSaver"),
        ("Daily-Digests", dev_vault / "Maps-of-Content" / "Daily"),
        ("Dev-Account-Vault", dev_vault / "2-Areas" / "Account-Vault"),
    ]
    ai_eng_dir = sb_vault / "10-Areas" / "AI Engineering"
    if apply:
        ai_eng_dir.mkdir(parents=True, exist_ok=True)
    for link_name, target_path in bridge_targets:
        dest_link = ai_eng_dir / link_name
        if target_path.exists():
            if apply:
                if dest_link.is_symlink() or dest_link.exists():
                    if dest_link.is_symlink():
                        dest_link.unlink()
                if not dest_link.exists():
                    dest_link.symlink_to(target_path)
            bridged_links.append(f"10-Areas/AI Engineering/{link_name} -> {target_path}")

    # 4. Query live telemetry from ~/.hermes/knowledge_compiler.db
    nodes_total = edges_total = trees_total = files_total = 0
    node_breakdown: List[tuple[str, int]] = []
    edge_breakdown: List[tuple[str, str, int]] = []
    adrs: List[tuple[Any, ...]] = []
    sessions: List[tuple[Any, ...]] = []

    if compiler_db.exists():
        conn = sqlite3.connect(str(compiler_db))
        try:
            nodes_total = conn.execute("SELECT COUNT(*) FROM nodes").fetchone()[0]
            edges_total = conn.execute("SELECT COUNT(*) FROM edges").fetchone()[0]
            trees_total = conn.execute("SELECT COUNT(*) FROM logic_trees").fetchone()[0]
            files_total = conn.execute("SELECT COUNT(*) FROM nodes WHERE node_type='FILE'").fetchone()[0]
            node_breakdown = conn.execute(
                "SELECT node_type, COUNT(*) FROM nodes GROUP BY node_type ORDER BY COUNT(*) DESC"
            ).fetchall()
            edge_breakdown = conn.execute(
                "SELECT edge_type, relation, COUNT(*) FROM edges GROUP BY edge_type, relation ORDER BY COUNT(*) DESC"
            ).fetchall()
            adrs = conn.execute(
                "SELECT adr_id, title, status, rationale, valid_from, valid_to, repo, sha256 "
                "FROM decisions ORDER BY recorded_at ASC"
            ).fetchall()
            sessions = conn.execute(
                "SELECT session_id, adr_id, vault_note, wikilink, created_at FROM session_links ORDER BY id ASC"
            ).fetchall()
        finally:
            conn.close()

    tombstone_count = 0
    if tombstones_path.exists():
        tombstone_count = sum(1 for line in tombstones_path.read_text(encoding="utf-8").splitlines() if line.strip())

    today = "2026-10-17"

    # 5. Compile live 10-Areas/Architecture/Knowledge-Graph-Telemetry.md
    arch_dir = sb_vault / "10-Areas" / "Architecture"
    sec_dir = sb_vault / "10-Areas" / "Security"
    sessions_dir = sb_vault / "10-Areas" / "AI Engineering" / "Sessions"

    kg_md = [
        "---",
        "type: telemetry",
        "status: compiled-live",
        f"reviewed: {today}",
        "source_db: ~/.hermes/knowledge_compiler.db",
        "---",
        "",
        "# 7-Repo AI Knowledge Compiler — Live SQLite Graph Telemetry",
        "",
        "> **Axiom 1 & 7**: *Stop storing static notes; compile them live. Repos are not your brain; they are the compiler!*",
        "",
        "## 1. Real-Time Graph Metrics",
        f"- **SQLite WAL + FTS5 Store**: `/home/zen/.hermes/knowledge_compiler.db`",
        f"- **Python Files Indexed (`FILE`)**: `{files_total:,}`",
        f"- **Total Knowledge Nodes**: `{nodes_total:,}`",
        f"- **Total Provenance Edges**: `{edges_total:,}`",
        f"- **AST Logic Trees (`CONTROL_FLOW` + `CALL_GRAPH`)**: `{trees_total:,}`",
        f"- **Bi-Temporal L3 Tombstones (`Clef Mnemosyne`)**: `{tombstone_count}` entries in `l3_tombstones.jsonl`",
        "",
        "## 2. Node Breakdown",
        "| Node Type | Count |",
        "|---|---|",
    ]
    for nt, cnt in node_breakdown:
        kg_md.append(f"| `{nt}` | `{cnt:,}` |")

    kg_md.extend([
        "",
        "## 3. Edge Breakdown (`EXTRACTED` vs `INFERRED`)",
        "| Edge Type | Relation | Count |",
        "|---|---|---|",
    ])
    for et, rel, cnt in edge_breakdown:
        kg_md.append(f"| `{et}` | `{rel}` | `{cnt:,}` |")

    kg_md.extend([
        "",
        "## 4. Connected Projects & Maps",
        "- [[20-Projects/Active/hermes-agent]]",
        "- [[20-Projects/Active/zencode]]",
        "- [[Maps/Decisions]]",
        "- [[Maps/Patterns]]",
    ])

    # 6. Compile live Maps/Decisions.md and 10-Areas/Architecture/ADR-Ledger.md
    dec_md = [
        "---",
        "type: map",
        f"reviewed: {today}",
        "---",
        "",
        "# Decisions — Bi-Temporal Architecture Decision Ledger",
        "",
        "> Đồng bộ trực tiếp từ bảng `decisions` trong `~/.hermes/knowledge_compiler.db` và `l3_tombstones.jsonl`.",
        "",
        "| ADR ID | Title | Status | Repo | Valid From | SHA-256 |",
        "|---|---|---|---|---|---|",
    ]
    for adr_id, title, status, rationale, valid_from, valid_to, repo, sha in adrs:
        dec_md.append(f"| **`{adr_id}`** | {title} | `{status}` | `{repo or 'hermes-agent'}` | `{valid_from[:10]}` | `{sha[:10]}…` |")

    dec_md.append("\n## Detailed Rationale & Consequences\n")
    for adr_id, title, status, rationale, valid_from, valid_to, repo, sha in adrs:
        dec_md.extend([
            f"### {adr_id}: {title}",
            f"- **Status**: `{status}` | **Valid From**: `{valid_from}` | **Valid To**: `{valid_to or '9999-12-31'}`",
            f"- **Rationale**: {rationale}",
            f"- **Cryptographic Digest**: `{sha}`",
            "",
        ])

    # 7. Compile Session-6c296d29.md in 10-Areas/AI Engineering/Sessions/
    sess_md = [
        "---",
        "type: session",
        "session_id: 6c296d29-cc14-4b02-a1dd-a0274d0fa689",
        f"date: {today}",
        "status: verified",
        "---",
        "",
        "# Session 6c296d29 — 7-Repo AI Knowledge Compiler, JEV/Clef & SecondBrain Rearchitecture",
        "",
        "## Summary",
        "- Built and verified `tools/jev_clef_knowledge_compiler.py` (`SSRFGuard`, `LocalJEVEvaluator`, `KnowledgeCompilerDB`, `isolated_git_commit`).",
        "- Built and executed `tools/rearchitect_skills_and_root.py` across **273 unique `SKILL.md` files** (`0` violations > 60 chars, `0` duplicate skills) and organized **99 root `.py` scripts** into `pipelines/masterclass/*`.",
        "- Hardened `autonomous_worker.py` for strict Pro-First routing (`tier='pro'`, `claude-sonnet-4-6` fallback when Gemini weekly quota is 0%).",
        "- Unified local Obsidian `SecondBrain` (`/home/zen/Obsidian/SecondBrain`) and `Dev` (`/home/zen/Downloads/Dev`).",
        "",
        "## Linked Architectural Decisions",
        "- [[Maps/Decisions#ADR-20261017-001|ADR-20261017-001]]",
        "- [[Maps/Decisions#ADR-20261017-002|ADR-20261017-002]]",
        "- [[Maps/Decisions#ADR-20261017-003|ADR-20261017-003]]",
        "- [[Maps/Decisions#ADR-20261017-004|ADR-20261017-004]]",
        "",
        "## Linked Projects",
        "- [[20-Projects/Active/hermes-agent]]",
        "- [[20-Projects/Active/zencode]]",
    ]

    # 8. Update 5 Active Project notes with live git status & outcomes
    project_notes: Dict[str, str] = {}
    for slug, (repo_path, docs_rel, outcome_desc) in PROJECT_REPOS.items():
        git_line = _git_summary(repo_path)
        project_notes[slug] = f"""---
type: project
status: active
repository: {repo_path}
docs: {docs_rel}
reviewed: {today}
---

# {slug}

## Outcome

{outcome_desc}

## Current State

- **Live Git State (`{today}`)**: {git_line}
- **Knowledge Graph Telemetry**: [[10-Areas/Architecture/Knowledge-Graph-Telemetry]]

## Next Action

- [x] Đồng bộ Knowledge Graph (`~/.hermes/knowledge_compiler.db`) & ADR Ledger (`[[Maps/Decisions]]`).
- [ ] Chạy kiểm định tự động định kỳ qua `python3 tools/jev_clef_knowledge_compiler.py --delta --upstream-audit`.

## Constraints

- Không lưu plaintext secrets chưa kiểm soát; ưu tiên redaction qua `DatasetSecretScrubber`.
- Mọi thay đổi kiến trúc phải ghi nhận Bi-Temporal Tombstone (`l3_tombstones.jsonl`) và ADR.

## Decisions

- [[Maps/Decisions]]
"""

    # 9. Regenerate Maps/Projects.md cleanly categorized
    valid_project_links = sorted(
        [p.name for p in dp_dir.iterdir() if not p.name.startswith(".") and p.exists()]
    ) if dp_dir.exists() else []
    proj_map_lines = [
        "---",
        "type: map",
        f"reviewed: {today}",
        "---",
        "",
        f"# Projects — {len(valid_project_links)} Linked Documentation Roots",
        "",
        "## Active Core Repositories",
        "- [[20-Projects/Active/hermes-agent|hermes-agent]] — AI Knowledge Compiler, Content Factory & 273 Skills",
        "- [[20-Projects/Active/zencode|zencode]] — AGY Fleet Router v2.5 & Clef/JEV Swarm",
        "- [[20-Projects/Active/insilos_ee|insilos_ee]] — Odoo 20 Enterprise Platform",
        "- [[20-Projects/Active/VerticalRisk|VerticalRisk]] — GRC, HSE-DPM & NCSP",
        "- [[20-Projects/Active/workspace|workspace]] — Sovereign Workstation Root",
        "",
        "## Linked Documentation Directories (`Data/Projects/`)",
    ]
    for link_name in valid_project_links:
        human_label = link_name.replace("__", "/")
        proj_map_lines.append(f"- [{human_label}](../Data/Projects/{link_name}/)")

    # 10. Update Maps/Concepts.md, Maps/Patterns.md, Maps/Problems.md
    concepts_md = f"""---
type: map
reviewed: {today}
---

# Concepts

- [[30-Resources/Concepts/Knowledge States|Knowledge States]] — Phân tách trạng thái tri thức (`EXTRACTED` vs `INFERRED`, `draft` vs `verified`).
- [[10-Areas/Architecture/Knowledge-Graph-Telemetry|7-Repo AI Knowledge Compiler]] — Biên dịch trực tiếp AST/SQL thay vì ghi chú tĩnh.
"""

    patterns_md = f"""---
type: map
reviewed: {today}
---

# Patterns

Giải pháp kiến trúc đã chứng minh thực nghiệm và tái sử dụng xuyên suốt các dự án:

## Agent & Compiler Design
- [[30-Resources/Patterns/Hermes Learning Loop - Design Breakthroughs|Hermes Learning Loop - Design Breakthroughs]] — Propose don't mutate, audit-first, deterministic retry, kill process-globals.
- [[10-Areas/Architecture/Knowledge-Graph-Telemetry|Local JEV + Clef Cloud Dual-Engine Routing]] — Fast-path `<20ms` (`output_tokens=0`) cho $C < 2.2$, leo thang Clef Cloud + SelfGate/Sentinel cho $C \\ge 2.2$.
- **Isolated Git Index Memory Compiler (`GIT_INDEX_FILE`)** — Commit nguyên tử các file chỉ định mà không làm xáo trộn working tree đang dirty.
"""

    problems_md = f"""---
type: map
reviewed: {today}
---

# Problems & Adversarial Remediations

- **CWE-918 SSRF trên Modal/Webhook Dispatchers**: Đã chặn bằng `SSRFGuard` và `validate_target_host()` (chặn RFC1918, IMDS `169.254.169.254`, chỉ cho phép domain whitelist).
- **72h GDPR Art. 17 Erasure vs. Immutable Merkle Audit Trail**: Giải quyết bằng Dual-Plane Cryptographic Shredding (`ESEE-AMEC`).
- **Context Bloating do mô tả Skill > 60 ký tự & Skill trùng lặp**: Đã chuẩn hoá toàn bộ 273 `SKILL.md` (`0` vi phạm, `0` trùng lặp).
"""

    # 11. Update SecondBrain/Home.md
    sb_home_md = f"""---
type: home
reviewed: {today}
---

# 🧠 Second Brain — Sovereign Knowledge Compiler Hub

> **Triết lý vận hành (7-Repo Blueprint)**: *Stop storing static notes; compile them live. Repos are not your brain; they are the compiler!*

---

## 🚀 1. Active Projects (`20-Projects/Active/`)
- [[20-Projects/Active/hermes-agent|hermes-agent]] — Hermes Agent, Content Factory & 273 Unified Skills
- [[20-Projects/Active/zencode|zencode]] — AGY Fleet Router v2.5, Pro-First Swarm & Clef/JEV
- [[20-Projects/Active/insilos_ee|insilos_ee]] — Insilos Enterprise Odoo 20 (QWeb & Owl)
- [[20-Projects/Active/VerticalRisk|VerticalRisk]] — VerticalRisk GRC, HSE-DPM & NCSP
- [[20-Projects/Active/workspace|workspace]] — ThinkPad P15 Sovereign Workstation

## ⚡ 2. Live Compiled Knowledge Graph (`10-Areas/`)
- [[10-Areas/Architecture/Knowledge-Graph-Telemetry|📊 Knowledge Graph Telemetry]] — **`{files_total:,}` files**, **`{nodes_total:,}` AST nodes**, **`{edges_total:,}` edges**, **`{trees_total:,}` logic trees**
- [[10-Areas/Architecture/ADR-Ledger|📜 Bi-Temporal ADR Ledger]] — `{len(adrs)}` Active ADRs & `{tombstone_count}` Clef Mnemosyne L3 Tombstones
- [[10-Areas/AI Engineering/Sessions/Session-6c296d29|🔗 Latest Session: 6c296d29 (Knowledge Compiler & Rearchitecture)]]
- **Bridged Operational Archives (`10-Areas/AI Engineering/`)**:
  - `10-Areas/AI Engineering/AI-Coding-Sessions/` (830+ automated coding sessions)
  - `10-Areas/AI Engineering/Daily-Digests/` (76 daily digests)
  - `10-Areas/AI Engineering/GPU-Fleet-Analytics/` & `Cost-Analytics/` & `TokenSaver-Telemetry/`

## 🗺️ 3. Knowledge Maps (`Maps/`)
- [[Maps/Decisions|Decisions (ADR Ledger)]]
- [[Maps/Patterns|Patterns (Verified Engineering Patterns)]]
- [[Maps/Problems|Problems & Security Remediations]]
- [[Maps/Concepts|Concepts (Knowledge States & Compiler Axioms)]]
- [[Maps/Projects|Projects ({len(valid_project_links)} Linked Docs Roots)]]

## 🛠️ 4. Playbooks, Templates & Capture
- **Inbox**: [[00-Inbox/Research Topics|Research Topics]]
- **Playbooks**:
  - [[30-Resources/Playbooks/Vibe Coding Session|Vibe Coding Session]]
  - [[30-Resources/Playbooks/Agent Context Pack|Agent Context Pack]]
- **Templates (`20-Projects/Templates/`)**:
  - [[20-Projects/Templates/Decision|Decision]] · [[20-Projects/Templates/Project|Project]] · [[20-Projects/Templates/Problem|Problem]] · [[20-Projects/Templates/Pattern|Pattern]] · [[20-Projects/Templates/Handoff|Handoff]] · [[20-Projects/Templates/Weekly Review|Weekly Review]]
"""

    if apply:
        arch_dir.mkdir(parents=True, exist_ok=True)
        sec_dir.mkdir(parents=True, exist_ok=True)
        sessions_dir.mkdir(parents=True, exist_ok=True)
        (arch_dir / "Knowledge-Graph-Telemetry.md").write_text("\n".join(kg_md) + "\n", encoding="utf-8")
        (arch_dir / "ADR-Ledger.md").write_text("\n".join(dec_md) + "\n", encoding="utf-8")
        (sb_vault / "Maps" / "Decisions.md").write_text("\n".join(dec_md) + "\n", encoding="utf-8")
        (sb_vault / "Maps" / "Projects.md").write_text("\n".join(proj_map_lines) + "\n", encoding="utf-8")
        (sb_vault / "Maps" / "Concepts.md").write_text(concepts_md, encoding="utf-8")
        (sb_vault / "Maps" / "Patterns.md").write_text(patterns_md, encoding="utf-8")
        (sb_vault / "Maps" / "Problems.md").write_text(problems_md, encoding="utf-8")
        (sessions_dir / "Session-6c296d29.md").write_text("\n".join(sess_md) + "\n", encoding="utf-8")
        for slug, content in project_notes.items():
            (sb_vault / "20-Projects" / "Active" / f"{slug}.md").write_text(content, encoding="utf-8")
        (sb_vault / "Home.md").write_text(sb_home_md, encoding="utf-8")

    return {
        "exists": True,
        "cleaned_scratch": cleaned_scratch,
        "pruned_noisy_symlinks_count": len(pruned_symlinks),
        "pruned_noisy_symlinks": pruned_symlinks,
        "bridged_links": bridged_links,
        "valid_project_links_count": len(valid_project_links),
        "compiled_metrics": {
            "files": files_total,
            "nodes": nodes_total,
            "edges": edges_total,
            "logic_trees": trees_total,
            "adrs": len(adrs),
            "tombstones": tombstone_count,
        },
        "updated_active_projects": list(project_notes.keys()),
    }


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Reorganize and unify local Obsidian SecondBrain vaults.")
    parser.add_argument("--secondbrain", type=Path, default=DEFAULT_SECONDBRAIN)
    parser.add_argument("--dev-vault", type=Path, default=DEFAULT_DEV_VAULT)
    parser.add_argument("--db-path", type=Path, default=DEFAULT_COMPILER_DB)
    parser.add_argument("--tombstones", type=Path, default=DEFAULT_TOMBSTONES)
    parser.add_argument("--apply", action="store_true", help="Apply changes on disk (default is dry-run)")
    args = parser.parse_args(argv)

    dev_res = reorganize_dev_vault(args.dev_vault, apply=args.apply)
    sb_res = reorganize_secondbrain_vault(
        args.secondbrain, args.dev_vault, args.db_path, args.tombstones, apply=args.apply
    )

    summary = {
        "mode": "APPLIED" if args.apply else "DRY_RUN",
        "dev_vault": dev_res,
        "secondbrain_vault": sb_res,
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
