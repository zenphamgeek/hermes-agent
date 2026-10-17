"""
tests/test_cognitive_secondbrain_engine.py

Verification suite for the Sovereign Cognitive SecondBrain Engine & Stratified AGI Memory Plugin:
  1. Bloom Taxonomy Cognitive Ladder (B1_REMEMBER .. B6_CREATE)
  2. Ebbinghaus Forgetting Curve & Synaptic Consolidation (L1 -> L2 -> L3)
  3. Hegelian Dialectical Critique (ABANDON false knowledge, SUPERSEDE, REFINE, QUARANTINE)
  4. Obsidian SecondBrain Self-Healing (broken symlinks, orphan recovery index, Ebbinghaus decay)
  5. AGI Harness Stratified Context Assembly (fast, deep_tot, dialectic_audit, creative_synthesis)
  6. SecondBrainMemoryProvider plugin registration & tool execution
"""

from __future__ import annotations

import json
from pathlib import Path
import sqlite3

import pytest

from plugins.memory import discover_memory_providers, load_memory_provider
from plugins.memory.secondbrain import SecondBrainMemoryProvider
from tools.cognitive_secondbrain_engine import (
    BloomLevel,
    CognitiveSecondBrainEngine,
    MemoryTier,
    classify_bloom_level,
    compute_retention_score,
)


def test_bloom_taxonomy_classification_ladder() -> None:
    # B1_REMEMBER: raw episodic log
    assert (
        classify_bloom_level("User executed git status at 10:15 UTC on terminal.", tier="L1")
        == BloomLevel.B1_REMEMBER
    )
    # B2_UNDERSTAND: semantic summary / concept map
    assert (
        classify_bloom_level("Overview and concept map of the SQLite FTS5 indexing module.", tier="L1")
        == BloomLevel.B2_UNDERSTAND
    )
    # B3_APPLY: procedural playbook / SOP
    assert (
        classify_bloom_level("Standard SOP workflow and execution steps for deploying workers.", tier="L2")
        == BloomLevel.B3_APPLY
    )
    # B4_ANALYZE: root-cause analysis / AST diff
    assert (
        classify_bloom_level("Root-cause analysis of the AST graph bottleneck in parser.", tier="L2")
        == BloomLevel.B4_ANALYZE
    )
    # B5_EVALUATE: adversarial critique / Clef JEV security audit
    assert (
        classify_bloom_level("Adversarial security audit and Clef JEV verdict on SSRF guard.", tier="L2")
        == BloomLevel.B5_EVALUATE
    )
    # B6_CREATE: sovereign invariant / ADR paradigm
    assert (
        classify_bloom_level("ADR-20261017-006 establishes the sovereign invariant for memory.", tier="L3")
        == BloomLevel.B6_CREATE
    )


def test_ebbinghaus_retention_and_synaptic_consolidation(tmp_path: Path) -> None:
    db_path = tmp_path / "test_cognitive.db"
    vault_path = tmp_path / "SecondBrain"
    tombstone_path = tmp_path / "l3_tombstones.jsonl"
    engine = CognitiveSecondBrainEngine(
        db_path=db_path, vault_path=vault_path, tombstone_path=tombstone_path
    )

    # Store an initial L1 episodic memory at B2_UNDERSTAND with strength 0.70
    mem = engine.store_memory(
        mem_key="ep:test-consolidation",
        title="SQLite WAL Concurrency Pattern",
        content="Overview and mental model of SQLite WAL mode concurrency.",
        tier=MemoryTier.L1_EPISODIC.value,
        bloom_level=BloomLevel.B2_UNDERSTAND,
        synaptic_strength=0.70,
        evidence_score=0.88,
    )
    assert mem["tier"] == "L1"
    assert mem["bloom_level"] == int(BloomLevel.B2_UNDERSTAND)
    assert mem["recall_count"] == 0

    # Reinforce #1: strength -> 0.82, recall_count -> 1 (not yet promoted)
    r1 = engine.reinforce_memory("ep:test-consolidation", evidence_boost=0.12)
    assert r1["recall_count"] == 1
    assert r1["synaptic_strength"] == pytest.approx(0.82, abs=1e-3)
    assert r1["tier"] == "L1"

    # Reinforce #2: strength -> 0.94 (>= 0.85) and recall_count == 2 -> promotes B2->B3 and L1->L2!
    r2 = engine.reinforce_memory("ep:test-consolidation", evidence_boost=0.12)
    assert r2["recall_count"] == 2
    assert r2["synaptic_strength"] >= 0.85
    assert r2["bloom_level"] == int(BloomLevel.B3_APPLY)
    assert r2["tier"] == "L2"

    # Reinforce further to B5_EVALUATE -> upgrades L2 -> L3_SOVEREIGN (since evidence_score=0.88 >= 0.85)
    engine.reinforce_memory("ep:test-consolidation", evidence_boost=0.05)  # B3 -> B4
    r4 = engine.reinforce_memory("ep:test-consolidation", evidence_boost=0.05)  # B4 -> B5, L2 -> L3
    assert r4["bloom_level"] >= int(BloomLevel.B5_EVALUATE)
    assert r4["tier"] == "L3"


def test_hegelian_dialectical_critique_abandon_and_supersede(tmp_path: Path) -> None:
    db_path = tmp_path / "test_dialectic.db"
    vault_path = tmp_path / "SecondBrain"
    tombstone_path = tmp_path / "l3_tombstones.jsonl"
    engine = CognitiveSecondBrainEngine(
        db_path=db_path, vault_path=vault_path, tombstone_path=tombstone_path
    )

    # 1. Store a false/flawed hypothesis and test ABANDON (evidence >= 0.80, empty new_content)
    engine.store_memory(
        mem_key="claim:atempo-slowdown-ok",
        title="Use atempo=0.75x to pad Shorts audio",
        content="Workflow suggestion: slow down TTS via atempo=0.75 to fill 50s Shorts.",
        tier="L2",
        synaptic_strength=0.65,
        evidence_score=0.40,
    )
    abandon_res = engine.dialectical_critique(
        thesis_key="claim:atempo-slowdown-ok",
        antithesis_claim="Rule 1.4 strictly forbids atempo < 1.0; speech must run at native 1.0x speed.",
        new_content="",
        evidence_score=0.95,
        evidence_ref="AGENTS.md#1.4",
    )
    assert abandon_res["verdict"] == "ABANDON"
    abandoned_state = engine.get_memory("claim:atempo-slowdown-ok")
    assert abandoned_state is not None
    assert abandoned_state["status"] == "ABANDONED"
    assert abandoned_state["tier"] == "L4"
    assert abandoned_state["valid_to"] is not None

    # 2. Store an outdated thesis and test SUPERSEDE (evidence >= 0.80, non-empty new_content)
    engine.store_memory(
        mem_key="arch:static-markdown-notes",
        title="Store static markdown notes manually",
        content="Legacy workflow: store static notes without live SQLite compilation.",
        tier="L2",
        synaptic_strength=0.75,
        evidence_score=0.60,
    )
    supersede_res = engine.dialectical_critique(
        thesis_key="arch:static-markdown-notes",
        antithesis_claim="7-Repo AI Knowledge Compiler Blueprint proves repos must be compiled live into SQLite WAL + FTS5.",
        new_content="Sovereign Invariant: Compile AST graphs and ADRs live into KnowledgeCompilerDB and project into SecondBrain.",
        evidence_score=0.94,
        evidence_ref="ADR-20261017-004",
    )
    assert supersede_res["verdict"] == "SUPERSEDE"
    synth_key = supersede_res["synthesis_key"]
    assert synth_key is not None

    old_thesis = engine.get_memory("arch:static-markdown-notes")
    assert old_thesis is not None
    assert old_thesis["status"] == "SUPERSEDED"
    assert old_thesis["superseded_by"] == synth_key
    assert old_thesis["tier"] == "L4"

    new_synth = engine.get_memory(synth_key)
    assert new_synth is not None
    assert new_synth["status"] == "ACTIVE"
    assert new_synth["bloom_level"] == int(BloomLevel.B6_CREATE)
    assert new_synth["tier"] == "L3"

    # Verify both tombstones were written to tombstone_path
    tomb_lines = [
        json.loads(line)
        for line in tombstone_path.read_text(encoding="utf-8").strip().splitlines()
    ]
    assert len(tomb_lines) == 2
    assert tomb_lines[0]["verdict"] == "ABANDON"
    assert tomb_lines[1]["verdict"] == "SUPERSEDE"
    assert tomb_lines[1]["superseded_by"] == synth_key

    # 3. Test REFINE (0.55 <= evidence < 0.80) and QUARANTINE (evidence < 0.55)
    engine.store_memory(
        mem_key="note:fts5-query",
        title="FTS5 Query Pattern",
        content="Basic FTS5 query guide.",
        tier="L2",
        bloom_level=BloomLevel.B2_UNDERSTAND,
    )
    refine_res = engine.dialectical_critique(
        thesis_key="note:fts5-query",
        antithesis_claim="Add fallback LIKE scan when FTS5 returns < 5 rows.",
        new_content="Fallback LIKE clause ensures recall on partial stems.",
        evidence_score=0.68,
        evidence_ref="cognitive_secondbrain_engine.py",
    )
    assert refine_res["verdict"] == "REFINE"
    assert refine_res["thesis_state"]["bloom_level"] == int(BloomLevel.B3_APPLY)

    quarantine_res = engine.dialectical_critique(
        thesis_key="note:fts5-query",
        antithesis_claim="Unverified rumor that FTS5 fails on UTF-8.",
        new_content="",
        evidence_score=0.20,
    )
    assert quarantine_res["verdict"] == "QUARANTINE"
    assert quarantine_res["thesis_state"]["contradiction_count"] == 1


def test_self_heal_secondbrain_symlinks_orphans_and_decay(tmp_path: Path) -> None:
    db_path = tmp_path / "test_self_heal.db"
    vault_path = tmp_path / "SecondBrain"
    (vault_path / "Data" / "Projects").mkdir(parents=True)
    (vault_path / "20-Projects" / "Active").mkdir(parents=True)
    (vault_path / "00-Inbox").mkdir(parents=True)

    # Create a broken symlink
    broken_link = vault_path / "Data" / "Projects" / "dead_symlink"
    broken_link.symlink_to(tmp_path / "non_existent_target_dir")

    # Create a connected note and an unlinked orphan note
    (vault_path / "Home.md").write_text("# Home\nLinks to [[Connected-Project]].\n", encoding="utf-8")
    (vault_path / "20-Projects" / "Active" / "Connected-Project.md").write_text(
        "# Connected Project\nActive project note.\n", encoding="utf-8"
    )
    (vault_path / "20-Projects" / "Active" / "Isolated-Orphan-Note.md").write_text(
        "# Isolated Orphan Note\nNo incoming wikilinks point here.\n", encoding="utf-8"
    )

    engine = CognitiveSecondBrainEngine(
        db_path=db_path,
        vault_path=vault_path,
        tombstone_path=tmp_path / "tombstones.jsonl",
    )

    # Insert a stale memory and force its last_recalled_at to 120 days ago with low strength
    engine.store_memory(
        mem_key="stale:ephemeral-log",
        title="Old unverified log from 2020",
        content="Raw ephemeral trace from years ago.",
        tier="L1",
        synaptic_strength=0.30,
    )
    with engine.db.get_connection() as conn:
        conn.execute(
            "UPDATE cognitive_memories SET last_recalled_at = '2020-01-01T00:00:00+00:00' WHERE mem_key = 'stale:ephemeral-log';"
        )
        conn.commit()

    report = engine.self_heal_secondbrain(vault_path=vault_path)
    assert report["broken_symlinks_count"] == 1
    assert not broken_link.is_symlink()
    assert report["orphan_notes_count"] >= 1
    assert "stale:ephemeral-log" in report["decayed_memories"]

    orphan_index = vault_path / "00-Inbox" / "Orphan-Recovery-Index.md"
    assert orphan_index.exists()
    assert "[[Isolated-Orphan-Note]]" in orphan_index.read_text(encoding="utf-8")

    matrix_file = Path(report["matrix_path"])
    assert matrix_file.exists()
    assert "Stratified Cognitive Memory Matrix" in matrix_file.read_text(encoding="utf-8")

    archived_mem = engine.get_memory("stale:ephemeral-log")
    assert archived_mem is not None
    assert archived_mem["status"] == "ARCHIVED"
    assert archived_mem["tier"] == "L4"


def test_agi_harness_stratified_context_assembly(tmp_path: Path) -> None:
    db_path = tmp_path / "test_harness.db"
    engine = CognitiveSecondBrainEngine(
        db_path=db_path,
        vault_path=tmp_path / "SecondBrain",
        tombstone_path=tmp_path / "tombstones.jsonl",
    )

    # Seed B1 (L1), B3 (L2), B6 (L3)
    engine.store_memory(
        mem_key="m:b1",
        title="Raw Terminal Ping Log",
        content="Pinged compiler server once.",
        tier="L1",
        bloom_level=BloomLevel.B1_REMEMBER,
    )
    engine.store_memory(
        mem_key="m:b3",
        title="Compiler Execution Playbook",
        content="Standard SOP workflow for running the compiler pipeline.",
        tier="L2",
        bloom_level=BloomLevel.B3_APPLY,
        synaptic_strength=0.85,
    )
    engine.store_memory(
        mem_key="m:b6",
        title="Sovereign Compiler Invariant ADR",
        content="ADR-20261017-004 sovereign invariant for compiler graph integrity.",
        tier="L3",
        bloom_level=BloomLevel.B6_CREATE,
        synaptic_strength=0.95,
        evidence_score=0.95,
    )

    fast_ctx = engine.assemble_harness_context("compiler invariant playbook", harness_mode="fast")
    assert "[L3-B6] Sovereign Compiler Invariant ADR" in fast_ctx
    assert "[L2-B3] Compiler Execution Playbook" in fast_ctx
    assert "Raw Terminal Ping Log" not in fast_ctx

    audit_ctx = engine.assemble_harness_context("compiler invariant", harness_mode="dialectic_audit")
    assert "[L3-B6] Sovereign Compiler Invariant ADR" in audit_ctx
    assert "[L2-B3]" not in audit_ctx  # dialectic_audit requires B >= 5


def test_secondbrain_memory_provider_plugin_lifecycle(tmp_path: Path) -> None:
    # Verify plugin discovery finds 'secondbrain'
    discovered = {name: avail for name, _desc, avail in discover_memory_providers()}
    assert "secondbrain" in discovered
    assert discovered["secondbrain"] is True

    provider = SecondBrainMemoryProvider(
        config={
            "db_path": str(tmp_path / "provider_test.db"),
            "vault_path": str(tmp_path / "Vault"),
            "tombstone_path": str(tmp_path / "tombstones.jsonl"),
        }
    )
    provider.initialize(session_id="test-sess-001", hermes_home=str(tmp_path))

    schemas = provider.get_tool_schemas()
    assert len(schemas) == 1
    assert schemas[0]["name"] == "secondbrain_cognitive"

    # Store via tool call
    store_raw = provider.handle_tool_call(
        "secondbrain_cognitive",
        {
            "action": "store",
            "mem_key": "plugin:test-rule",
            "title": "Sovereign Bloom Memory Rule",
            "content": "Sovereign invariant for Bloom taxonomy stratification in Hermes Agent.",
            "tier": "L3",
            "synaptic_strength": 0.92,
            "evidence_score": 0.95,
        },
    )
    store_data = json.loads(store_raw)
    assert store_data["status"] == "stored"
    assert store_data["memory"]["bloom_level"] == int(BloomLevel.B6_CREATE)

    # Prefetch & RecallStatus
    prefetched = provider.prefetch("architecture invariant Bloom taxonomy")
    assert "Sovereign Bloom Memory Rule" in prefetched
    status = provider.recall_status()
    assert status is not None
    assert status.provider_label == "secondbrain"
    assert status.count >= 1

    # Mirror built-in memory write
    provider.on_memory_write("add", "memory", "Always run pytest verification before committing.")
    stats_raw = provider.handle_tool_call("secondbrain_cognitive", {"action": "matrix_stats"})
    stats_data = json.loads(stats_raw)
    assert stats_data["status_counts"].get("ACTIVE", 0) >= 2

    provider.shutdown()
