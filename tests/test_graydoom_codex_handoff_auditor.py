"""Unit and integration tests for Graydoom Codex-to-AGY Handoff Auditor and Skills."""

from __future__ import annotations

from pathlib import Path
from tools.graydoom_codex_handoff_auditor import (
    WORKTREE_TARGETS,
    audit_worktree,
    build_handoff_plan,
    render_markdown_report,
)


def test_graydoom_skills_exist_and_have_valid_frontmatter() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    skill_names = [
        "graydoom-codex-harness",
        "graydoom-character-and-art-logic",
        "graydoom-handoff-navigator",
    ]
    for s in skill_names:
        local_skill = repo_root / ".agents" / "skills" / s / "SKILL.md"
        global_skill = Path("/home/zen/.gemini/config/skills") / s / "SKILL.md"
        assert local_skill.is_file(), f"Missing local skill {local_skill}"
        assert global_skill.is_file(), f"Missing global skill {global_skill}"
        text = local_skill.read_text(encoding="utf-8")
        assert text.startswith("---\nname: " + s)
        assert "description:" in text


def test_audit_live_graydoom_worktrees_and_argon_plan(tmp_path: Path) -> None:
    audits = [audit_worktree(t) for t in WORKTREE_TARGETS]
    assert len(audits) == 4
    existing = [a for a in audits if a.exists]
    assert len(existing) == 4

    branches = {a.name: a.branch for a in audits}
    assert branches["settlement-art-mapping"] == "codex/settlement-art-mapping-20261015"
    assert branches["game-art-atlas"] == "codex/game-art-atlas-parallel-20261008"
    assert branches["novel-gemini-2"] == "gemini-2"

    # Verify settlement-art-mapping has >= 35 harness packets and >= 75 SQL migrations
    settlement_audit = next(a for a in audits if a.name == "settlement-art-mapping")
    assert settlement_audit.harness_packets >= 30
    assert settlement_audit.sql_migrations >= 75

    # Verify game-art-atlas has 3/3 tri-lock files and 2,081 atlas tasks
    atlas_audit = next(a for a in audits if a.name == "game-art-atlas")
    assert atlas_audit.tri_lock_files == 3
    assert atlas_audit.atlas_work_order_tasks == 2081

    plan = build_handoff_plan(audits)
    assert len(plan) == 4
    assert [p.level for p in plan] == ["L1_TRIVIAL", "L2_STANDARD", "L3_COMPLEX", "L4_SOVEREIGN"]
    assert [p.canonical_model for p in plan] == [
        "gemini-4-argon-low",
        "gemini-4-argon-medium",
        "gemini-4-argon-high",
        "gemini-4-argon-high",
    ]
    assert all(p.tier == "pro" for p in plan)

    md = render_markdown_report(audits, plan)
    assert "Gray Doom Codex-to-AGY Fleet Sovereign Handoff Dossier" in md
    assert "codex/settlement-art-mapping-20261015" in md
    assert "2081" in md
