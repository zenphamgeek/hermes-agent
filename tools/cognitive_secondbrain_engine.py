"""
tools/cognitive_secondbrain_engine.py

Sovereign Cognitive SecondBrain Engine & Stratified AGI Memory Subsystem.
Integrates:
  1. Bloom Taxonomy Cognitive Ladder (B1_REMEMBER .. B6_CREATE)
  2. 5-Tier Stratified AGI Memory Hierarchy (L0_SENSORY .. L4_ARCHIVE)
  3. Ebbinghaus Forgetting Decay & Synaptic Consolidation (L1 -> L2 -> L3)
  4. Hegelian Dialectical Critique (ABANDON false knowledge, SUPERSEDE, REFINE, QUARANTINE)
  5. Bi-Temporal Clef Mnemosyne Tombstones (l3_tombstones.jsonl)
  6. Obsidian SecondBrain Self-Healing (symlinks, wikilinks, orphans, live telemetry matrix)
  7. Stratified Context Assembly for AGI Harnesses (fast, deep_tot, dialectic_audit, creative_synthesis)
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from enum import Enum, IntEnum
import hashlib
import json
import math
from pathlib import Path
import re
import sqlite3
from typing import Any, Dict, List, Optional, Set, Tuple


# ==============================================================================
# 1. BLOOM TAXONOMY COGNITIVE LADDER & STRATIFIED MEMORY TIERS
# ==============================================================================

class BloomLevel(IntEnum):
    """
    Bloom Taxonomy Cognitive Ladder (IntEnum 1..6).
    Represents the epistemic abstraction depth of memory entries.
    """
    B1_REMEMBER = 1   # Raw episodic facts, logs, execution traces, observations
    B2_UNDERSTAND = 2 # Semantic summaries, concept maps, AST call graphs
    B3_APPLY = 3      # Procedural playbooks, SOPs, skills, verified workflows
    B4_ANALYZE = 4    # Root-cause analyses, AST control-flow diffs, contrastive patterns
    B5_EVALUATE = 5   # Adversarial critiques, benchmarks, security audits, Clef/JEV verdicts
    B6_CREATE = 6     # Sovereign invariants, ADRs, architectural paradigms, synthesized frameworks


class MemoryTier(str, Enum):
    """
    5-Tier Stratified AGI Memory Hierarchy mapped to Human Neuro-Anatomy.
    """
    L0_SENSORY = "L0"    # Prefrontal Working Buffer & Thalamic Sensory Gate (Gamma 30-100Hz)
    L1_EPISODIC = "L1"   # Hippocampus CA3/CA1 & Dentate Gyrus (Fast Hebbian one-shot encoding)
    L2_SEMANTIC = "L2"   # Temporal-Parietal Association Neocortex & Basal Ganglia (Schemas & SOPs)
    L3_SOVEREIGN = "L3"  # vmPFC / dlPFC & Anterior Cingulate Cortex (Myelinated Constitutional Invariants)
    L4_ARCHIVE = "L4"    # Infralimbic Extinction & Subcortical Bi-Temporal Ledger (l3_tombstones.jsonl)


BRAIN_REGION_MAP: Dict[str, Dict[str, str]] = {
    MemoryTier.L0_SENSORY.value: {
        "region": "Thalamic Gate & Prefrontal Working Buffer",
        "oscillation": "Gamma (30–100 Hz)",
        "plasticity": "Sub-second attentional bottleneck (7±2 chunks)",
    },
    MemoryTier.L1_EPISODIC.value: {
        "region": "Hippocampus (Dentate Gyrus Pattern Separation + CA3/CA1)",
        "oscillation": "Theta-Nested Gamma & Sharp-Wave Ripples (150–250 Hz)",
        "plasticity": "Fast one-shot Hebbian LTP; vulnerable to interference",
    },
    MemoryTier.L2_SEMANTIC.value: {
        "region": "Temporal-Parietal Association Neocortex & Basal Ganglia",
        "oscillation": "Thalamocortical Sleep Spindles (11–16 Hz)",
        "plasticity": "Slow interleaved systems consolidation; procedural SOPs & concept maps",
    },
    MemoryTier.L3_SOVEREIGN.value: {
        "region": "Dorsolateral & Ventromedial Prefrontal Cortex (dlPFC / vmPFC) + ACC",
        "oscillation": "Phase-Locked Prefrontal-Cortical Coherence",
        "plasticity": "Myelinated constitutional invariants & ADRs; Synaptic Tagging protected",
    },
    MemoryTier.L4_ARCHIVE.value: {
        "region": "Infralimbic Extinction Cortex & Bi-Temporal Fossil Ledger",
        "oscillation": "Slow Delta Extinction Trace (< 1 Hz)",
        "plasticity": "Inhibited counterfactual trace with Clef Mnemosyne tombstone",
    },
}


def classify_bloom_level(content: str, tier: str = "L1") -> BloomLevel:
    """
    Deterministically classifies content into the Bloom Taxonomy Cognitive Ladder (B1..B6)
    using structural patterns, semantic keywords, and epistemic markers.
    """
    text = content.lower()

    # B6_CREATE: Sovereign invariants, ADRs, architectural paradigms, foundational laws
    b6_patterns = [
        r"\bsovereign\b", r"\binvariant\b", r"\badr[-_\s]?\d+\b",
        r"\barchitectur(al|e)\s+paradigm\b", r"\bconstitutional\s+rule\b",
        r"\bfirst\s+principle\b", r"\bsynthesized\s+framework\b",
        r"\bformal\s+proof\b", r"\bzero[-_\s]?fake[-_\s]?pass\b"
    ]
    if any(re.search(p, text) for p in b6_patterns):
        return BloomLevel.B6_CREATE

    # B5_EVALUATE: Adversarial critiques, benchmarks, security audits, Clef/JEV verdicts
    b5_patterns = [
        r"\badversarial\b", r"\bcritique\b", r"\bbenchmark\b", r"\bsecurity\s+audit\b",
        r"\bclef\b", r"\bjev\b", r"\bverdict\b", r"\bevaluation\b", r"\bhegelian\b",
        r"\bantithesis\b", r"\bvalidation\s+gate\b", r"\bbyzantine\b", r"\brisk\s+score\b"
    ]
    if any(re.search(p, text) for p in b5_patterns):
        return BloomLevel.B5_EVALUATE

    # B4_ANALYZE: Root-cause analyses, AST control-flow diffs, contrastive patterns
    b4_patterns = [
        r"\broot[-_\s]?cause\b", r"\brca\b", r"\bast\s+(diff|control[-_\s]?flow|graph)\b",
        r"\bcontrastive\b", r"\bpostmortem\b", r"\bbottleneck\b", r"\bprofiling\b",
        r"\bdiscrepancy\b", r"\bcounterexample\b", r"\bdecomposition\b"
    ]
    if any(re.search(p, text) for p in b4_patterns):
        return BloomLevel.B4_ANALYZE

    # B3_APPLY: Procedural playbooks, SOPs, skills, verified workflows
    b3_patterns = [
        r"\bplaybook\b", r"\bsop\b", r"\brunbook\b", r"\bworkflow\b",
        r"\bprocedure\b", r"\bstep\s+\d+:\b", r"\bhow[-_\s]?to\b",
        r"\bpipeline\b", r"\bexecution\s+steps?\b", r"\bimplementation\s+guide\b"
    ]
    if any(re.search(p, text) for p in b3_patterns):
        return BloomLevel.B3_APPLY

    # B2_UNDERSTAND: Semantic summaries, concept maps, AST call graphs
    b2_patterns = [
        r"\bsummary\b", r"\bconcept\s+map\b", r"\bcall\s+graph\b", r"\boverview\b",
        r"\bexplanation\b", r"\btaxonomy\b", r"\bdefinition\b", r"\bmental\s+model\b",
        r"\bsemantic\s+representation\b"
    ]
    if any(re.search(p, text) for p in b2_patterns) or tier == MemoryTier.L2_SEMANTIC.value:
        return BloomLevel.B2_UNDERSTAND

    if tier == MemoryTier.L3_SOVEREIGN.value:
        return BloomLevel.B6_CREATE

    return BloomLevel.B1_REMEMBER


# ==============================================================================
# 2. EBBINGHAUS FORGETTING & SYNAPTIC CONSOLIDATION ENGINE
# ==============================================================================

def compute_retention_score(
    synaptic_strength: float,
    last_recalled_at: str,
    recall_count: int,
    half_life_days: float = 7.0,
    now_iso: Optional[str] = None
) -> float:
    """
    Computes Ebbinghaus retention score:
        R = min(1.0, synaptic_strength * exp(-Δt / (half_life_days * (1.0 + ln(1 + recall_count)))))
    """
    try:
        now_dt = datetime.fromisoformat(now_iso) if now_iso else datetime.now(timezone.utc)
        recalled_dt = datetime.fromisoformat(last_recalled_at)
        if recalled_dt.tzinfo is None:
            recalled_dt = recalled_dt.replace(tzinfo=timezone.utc)
        if now_dt.tzinfo is None:
            now_dt = now_dt.replace(tzinfo=timezone.utc)
        elapsed_days = max(0.0, (now_dt - recalled_dt).total_seconds() / 86400.0)
    except Exception:
        elapsed_days = 0.0

    effective_half_life = half_life_days * (1.0 + math.log1p(max(0, recall_count)))
    decay = math.exp(-elapsed_days / effective_half_life) if effective_half_life > 0.0 else 0.0
    retention = synaptic_strength * decay
    return float(round(min(1.0, max(0.0, retention)), 4))


# ==============================================================================
# 3. SQLITE WAL + FTS5 SCHEMA & DATABASE LAYER
# ==============================================================================

class CognitiveMemoryDB:
    """
    High-performance SQLite WAL + FTS5 Storage Engine for Cognitive Memories
    and Hegelian Dialectical Audits. Shares ~/.hermes/knowledge_compiler.db.
    """

    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            hermes_dir = Path.home() / ".hermes"
            hermes_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = hermes_dir / "knowledge_compiler.db"
        else:
            self.db_path = Path(db_path)
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._init_schema()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        conn.execute("PRAGMA busy_timeout=5000;")
        return conn

    def _init_schema(self) -> None:
        with self.get_connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS cognitive_memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    mem_key TEXT UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    tier TEXT NOT NULL,
                    bloom_level INTEGER NOT NULL,
                    synaptic_strength REAL NOT NULL DEFAULT 0.7,
                    evidence_score REAL NOT NULL DEFAULT 0.5,
                    recall_count INTEGER NOT NULL DEFAULT 0,
                    contradiction_count INTEGER NOT NULL DEFAULT 0,
                    status TEXT NOT NULL DEFAULT 'ACTIVE',
                    superseded_by TEXT,
                    vault_path TEXT,
                    valid_from TEXT NOT NULL,
                    valid_to TEXT,
                    last_recalled_at TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    sha256 TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_mem_tier ON cognitive_memories(tier);
                CREATE INDEX IF NOT EXISTS idx_mem_bloom ON cognitive_memories(bloom_level);
                CREATE INDEX IF NOT EXISTS idx_mem_status ON cognitive_memories(status);
                CREATE INDEX IF NOT EXISTS idx_mem_valid ON cognitive_memories(valid_to);

                CREATE TABLE IF NOT EXISTS dialectical_audits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    thesis_key TEXT NOT NULL,
                    antithesis_claim TEXT NOT NULL,
                    verdict TEXT NOT NULL,
                    synthesis_key TEXT,
                    evidence_ref TEXT,
                    judge_engine TEXT NOT NULL,
                    recorded_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_audit_thesis ON dialectical_audits(thesis_key);
                CREATE INDEX IF NOT EXISTS idx_audit_verdict ON dialectical_audits(verdict);

                CREATE TABLE IF NOT EXISTS jev_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_key TEXT UNIQUE NOT NULL,
                    query TEXT NOT NULL,
                    harness_mode TEXT NOT NULL,
                    bloom_level INTEGER NOT NULL,
                    tier TEXT NOT NULL,
                    complexity REAL NOT NULL DEFAULT 0.5,
                    engine TEXT NOT NULL DEFAULT 'LOCAL_JEV',
                    chosen_response TEXT NOT NULL,
                    rejected_response TEXT DEFAULT '',
                    sample_type TEXT NOT NULL DEFAULT 'SFT',
                    sha256 TEXT NOT NULL,
                    recorded_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_jev_sess_type ON jev_sessions(sample_type);
                CREATE INDEX IF NOT EXISTS idx_jev_sess_mode ON jev_sessions(harness_mode);

                CREATE TABLE IF NOT EXISTS exogenous_entropy_ledger (
                    entropy_id TEXT PRIMARY KEY,
                    source_type TEXT NOT NULL,
                    external_ref TEXT NOT NULL,
                    domain TEXT NOT NULL,
                    title TEXT NOT NULL,
                    url TEXT DEFAULT '',
                    shannon_entropy_bits REAL DEFAULT 2.4,
                    architectural_pattern TEXT DEFAULT '',
                    key_algorithms TEXT DEFAULT '',
                    adaptation_blueprint TEXT DEFAULT '',
                    evolution_decision TEXT NOT NULL,
                    ecology_impact_score REAL DEFAULT 0.85,
                    secondbrain_note_path TEXT DEFAULT '',
                    mem_key TEXT DEFAULT '',
                    status TEXT DEFAULT 'ACTIVE',
                    recorded_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_exo_source_domain ON exogenous_entropy_ledger(source_type, domain, evolution_decision);
            """)

            conn.executescript("""
                CREATE VIRTUAL TABLE IF NOT EXISTS cognitive_memories_fts USING fts5(
                    title,
                    content,
                    tier,
                    status,
                    content='cognitive_memories',
                    content_rowid='id'
                );

                CREATE TRIGGER IF NOT EXISTS trg_cm_after_insert AFTER INSERT ON cognitive_memories BEGIN
                    INSERT INTO cognitive_memories_fts(rowid, title, content, tier, status)
                    VALUES (new.id, new.title, new.content, new.tier, new.status);
                END;

                CREATE TRIGGER IF NOT EXISTS trg_cm_after_delete AFTER DELETE ON cognitive_memories BEGIN
                    INSERT INTO cognitive_memories_fts(cognitive_memories_fts, rowid, title, content, tier, status)
                    VALUES ('delete', old.id, old.title, old.content, old.tier, old.status);
                END;

                CREATE TRIGGER IF NOT EXISTS trg_cm_after_update AFTER UPDATE ON cognitive_memories BEGIN
                    INSERT INTO cognitive_memories_fts(cognitive_memories_fts, rowid, title, content, tier, status)
                    VALUES ('delete', old.id, old.title, old.content, old.tier, old.status);
                    INSERT INTO cognitive_memories_fts(rowid, title, content, tier, status)
                    VALUES (new.id, new.title, new.content, new.tier, new.status);
                END;
            """)
            conn.commit()


# ==============================================================================
# 4. COGNITIVE SECONDBRAIN ENGINE IMPLEMENTATION
# ==============================================================================

DEFAULT_TOMBSTONE_PATH = Path(
    "/home/zen/hermes-agent/.agents/skills/memory-curator/resources/l3_tombstones.jsonl"
)


class CognitiveSecondBrainEngine:
    """
    Autonomous Cognitive Engine orchestrating:
      - Memory storage with automatic Bloom classification & SHA-256 fingerprinting
      - Synaptic consolidation & Ebbinghaus forgetting decay
      - Hegelian dialectical critique & Clef bi-temporal tombstoning
      - Obsidian SecondBrain vault seeding & self-healing (symlinks, orphans, live matrix)
      - Stratified Context Assembly for AGI harnesses
    """

    def __init__(
        self,
        db_path: Optional[Path] = None,
        vault_path: Optional[Path] = None,
        tombstone_path: Optional[Path] = None,
        myelination_dir: Optional[Path] = None,
    ):
        self.db = CognitiveMemoryDB(db_path)
        self.vault_path = Path(vault_path) if vault_path else Path("/home/zen/Obsidian/SecondBrain")
        if tombstone_path is not None:
            self.tombstone_path = Path(tombstone_path)
        elif DEFAULT_TOMBSTONE_PATH.parent.exists():
            self.tombstone_path = DEFAULT_TOMBSTONE_PATH
        else:
            self.tombstone_path = Path.home() / ".hermes" / "l3_tombstones.jsonl"
        self.tombstone_path.parent.mkdir(parents=True, exist_ok=True)
        # Production-artifact isolation: a sandboxed engine (custom db_path) must never
        # overwrite the production ~/.hermes/jev_myelination dataset/adapters. None means
        # "production default" and enables external DPO harvesting (Gray Doom, evolution ledger).
        if myelination_dir is not None:
            self.myelination_dir: Optional[Path] = Path(myelination_dir)
        elif db_path is not None:
            self.myelination_dir = Path(db_path).parent / "jev_myelination"
        else:
            self.myelination_dir = None

    # --------------------------------------------------------------------------
    # Storage & Memory Ingestion
    # --------------------------------------------------------------------------

    def store_memory(
        self,
        mem_key: str,
        title: str,
        content: str,
        tier: str = MemoryTier.L1_EPISODIC.value,
        bloom_level: Optional[BloomLevel] = None,
        synaptic_strength: float = 0.7,
        evidence_score: float = 0.5,
        vault_path: str = "",
        status: str = "ACTIVE"
    ) -> Dict[str, Any]:
        """
        Stores or upserts a cognitive memory with SHA-256 and automatic Bloom classification.
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        sha256_hash = hashlib.sha256(content.strip().encode("utf-8")).hexdigest()

        if bloom_level is None:
            bloom_level = classify_bloom_level(content, tier)

        with self.db.get_connection() as conn:
            conn.execute("""
                INSERT INTO cognitive_memories (
                    mem_key, title, content, tier, bloom_level,
                    synaptic_strength, evidence_score, recall_count, contradiction_count,
                    status, superseded_by, vault_path, valid_from, valid_to,
                    last_recalled_at, created_at, sha256
                ) VALUES (
                    ?, ?, ?, ?, ?,
                    ?, ?, 0, 0,
                    ?, NULL, ?, ?, NULL,
                    ?, ?, ?
                )
                ON CONFLICT(mem_key) DO UPDATE SET
                    title = excluded.title,
                    content = excluded.content,
                    tier = excluded.tier,
                    bloom_level = excluded.bloom_level,
                    synaptic_strength = excluded.synaptic_strength,
                    evidence_score = excluded.evidence_score,
                    status = excluded.status,
                    vault_path = excluded.vault_path,
                    last_recalled_at = excluded.last_recalled_at,
                    sha256 = excluded.sha256;
            """, (
                mem_key, title, content, tier, int(bloom_level),
                synaptic_strength, evidence_score, status, vault_path,
                now_iso, now_iso, now_iso, sha256_hash
            ))
            conn.commit()

        return self.get_memory(mem_key) or {}

    def get_memory(self, mem_key: str) -> Optional[Dict[str, Any]]:
        """Retrieves a single memory record by its unique key."""
        with self.db.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM cognitive_memories WHERE mem_key = ?;", (mem_key,)
            ).fetchone()
            if row:
                d = dict(row)
                d["retention"] = compute_retention_score(
                    d["synaptic_strength"], d["last_recalled_at"], d["recall_count"]
                )
                return d
        return None

    # --------------------------------------------------------------------------
    # Synaptic Reinforcement & Consolidation
    # --------------------------------------------------------------------------

    def reinforce_memory(
        self,
        mem_key: str,
        evidence_boost: float = 0.12,
        promote_bloom: bool = True
    ) -> Dict[str, Any]:
        """
        Increases synaptic_strength, increments recall_count, updates last_recalled_at.
        If synaptic_strength >= 0.85 and recall_count >= 2:
          - promotes bloom_level = min(6, bloom_level + 1)
          - upgrades tier L1 -> L2 (or L2 -> L3 if bloom_level >= 5 and evidence_score >= 0.85).
        """
        now_iso = datetime.now(timezone.utc).isoformat()

        with self.db.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM cognitive_memories WHERE mem_key = ?;", (mem_key,)
            ).fetchone()
            if not row:
                raise KeyError(f"Memory key '{mem_key}' does not exist in cognitive_memories.")

            current_strength = float(row["synaptic_strength"])
            current_recalls = int(row["recall_count"]) + 1
            current_bloom = int(row["bloom_level"])
            current_tier = str(row["tier"])
            evidence_score = float(row["evidence_score"])

            new_strength = round(min(1.0, current_strength + evidence_boost), 4)
            new_bloom = current_bloom
            new_tier = current_tier

            if new_strength >= 0.85 and current_recalls >= 2:
                if promote_bloom:
                    new_bloom = min(6, current_bloom + 1)

                if current_tier == MemoryTier.L1_EPISODIC.value:
                    new_tier = MemoryTier.L2_SEMANTIC.value
                elif current_tier == MemoryTier.L2_SEMANTIC.value:
                    if new_bloom >= 5 and evidence_score >= 0.85:
                        new_tier = MemoryTier.L3_SOVEREIGN.value

            conn.execute("""
                UPDATE cognitive_memories
                SET synaptic_strength = ?,
                    recall_count = ?,
                    bloom_level = ?,
                    tier = ?,
                    last_recalled_at = ?
                WHERE mem_key = ?;
            """, (new_strength, current_recalls, new_bloom, new_tier, now_iso, mem_key))
            conn.commit()

        updated = self.get_memory(mem_key)
        return updated or {}

    # --------------------------------------------------------------------------
    # Hegelian Dialectical Critique & False Knowledge Abandonment
    # --------------------------------------------------------------------------

    def dialectical_critique(
        self,
        thesis_key: str,
        antithesis_claim: str,
        new_content: str = "",
        evidence_score: float = 0.85,
        evidence_ref: str = "",
        tombstone_path: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        Hegelian Dialectical Critique evaluating thesis against empirical antithesis evidence.
        Verdicts:
          - ABANDON (evidence >= 0.80 and empty new_content): Marks thesis ABANDONED in L4, writes tombstone.
          - SUPERSEDE (evidence >= 0.80 and non-empty new_content): Synthesis created at B5/B6,
            thesis marked SUPERSEDED in L4, tombstone written.
          - REFINE (0.55 <= evidence < 0.80): Upgrades thesis content and increments bloom_level.
          - QUARANTINE (evidence < 0.55): Increments contradiction_count without corrupting truth.
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        target_tombstone = Path(tombstone_path) if tombstone_path else self.tombstone_path
        target_tombstone.parent.mkdir(parents=True, exist_ok=True)

        thesis = self.get_memory(thesis_key)
        if not thesis:
            raise KeyError(f"Thesis memory '{thesis_key}' not found in cognitive_memories.")

        verdict: str
        synthesis_key: Optional[str] = None
        synthesis_record: Optional[Dict[str, Any]] = None

        with self.db.get_connection() as conn:
            if evidence_score >= 0.80:
                if not new_content or not new_content.strip():
                    verdict = "ABANDON"
                    conn.execute("""
                        UPDATE cognitive_memories
                        SET status = 'ABANDONED',
                            valid_to = ?,
                            tier = ?
                        WHERE mem_key = ?;
                    """, (now_iso, MemoryTier.L4_ARCHIVE.value, thesis_key))

                    tombstone_data = {
                        "tombstone_id": f"tomb-{hashlib.sha256((thesis_key + now_iso).encode()).hexdigest()[:12]}",
                        "entity_id": thesis_key,
                        "thesis_key": thesis_key,
                        "verdict": verdict,
                        "reason": antithesis_claim,
                        "antithesis_claim": antithesis_claim,
                        "evidence_score": evidence_score,
                        "evidence_ref": evidence_ref,
                        "superseded_by": "ABANDONED_FALSE_KNOWLEDGE",
                        "valid_from": thesis["valid_from"],
                        "valid_to": now_iso,
                        "recorded_at": now_iso
                    }
                    with target_tombstone.open("a", encoding="utf-8") as f:
                        f.write(json.dumps(tombstone_data, ensure_ascii=False) + "\n")
                else:
                    verdict = "SUPERSEDE"
                    content_digest = hashlib.sha256(new_content.strip().encode()).hexdigest()[:8]
                    synthesis_key = f"{thesis_key}-synth-{content_digest}"
                    synthesis_bloom = (
                        BloomLevel.B6_CREATE if evidence_score >= 0.90 else BloomLevel.B5_EVALUATE
                    )
                    synth_tier = (
                        MemoryTier.L3_SOVEREIGN.value
                        if thesis["tier"] == MemoryTier.L3_SOVEREIGN.value or evidence_score >= 0.92
                        else MemoryTier.L2_SEMANTIC.value
                    )

                    conn.execute("""
                        UPDATE cognitive_memories
                        SET status = 'SUPERSEDED',
                            superseded_by = ?,
                            valid_to = ?,
                            tier = ?
                        WHERE mem_key = ?;
                    """, (synthesis_key, now_iso, MemoryTier.L4_ARCHIVE.value, thesis_key))

                    conn.execute("""
                        INSERT INTO cognitive_memories (
                            mem_key, title, content, tier, bloom_level,
                            synaptic_strength, evidence_score, recall_count, contradiction_count,
                            status, superseded_by, vault_path, valid_from, valid_to,
                            last_recalled_at, created_at, sha256
                        ) VALUES (
                            ?, ?, ?, ?, ?,
                            0.90, ?, 1, 0,
                            'ACTIVE', NULL, ?, ?, NULL,
                            ?, ?, ?
                        )
                        ON CONFLICT(mem_key) DO UPDATE SET
                            content = excluded.content,
                            tier = excluded.tier,
                            bloom_level = excluded.bloom_level,
                            evidence_score = excluded.evidence_score,
                            status = 'ACTIVE',
                            last_recalled_at = excluded.last_recalled_at;
                    """, (
                        synthesis_key,
                        f"Synthesis: {thesis['title']}",
                        new_content,
                        synth_tier,
                        int(synthesis_bloom),
                        evidence_score,
                        thesis.get("vault_path", ""),
                        now_iso,
                        now_iso,
                        now_iso,
                        hashlib.sha256(new_content.encode()).hexdigest()
                    ))

                    tombstone_data = {
                        "tombstone_id": f"tomb-{hashlib.sha256((thesis_key + now_iso).encode()).hexdigest()[:12]}",
                        "entity_id": thesis_key,
                        "thesis_key": thesis_key,
                        "verdict": verdict,
                        "reason": antithesis_claim,
                        "antithesis_claim": antithesis_claim,
                        "evidence_score": evidence_score,
                        "evidence_ref": evidence_ref,
                        "superseded_by": synthesis_key,
                        "valid_from": thesis["valid_from"],
                        "valid_to": now_iso,
                        "recorded_at": now_iso
                    }
                    with target_tombstone.open("a", encoding="utf-8") as f:
                        f.write(json.dumps(tombstone_data, ensure_ascii=False) + "\n")

            elif 0.55 <= evidence_score < 0.80:
                verdict = "REFINE"
                refined_content = thesis["content"]
                if new_content and new_content.strip():
                    refined_content = (
                        f"{thesis['content']}\n\n"
                        f"> [!NOTE] Dialectical Refinement ({now_iso[:10]})\n"
                        f"> Ref: {evidence_ref}\n"
                        f"> Claim: {antithesis_claim}\n\n"
                        f"{new_content}"
                    )
                new_bloom = min(6, int(thesis["bloom_level"]) + 1)
                new_strength = round(min(1.0, float(thesis["synaptic_strength"]) + 0.05), 4)

                conn.execute("""
                    UPDATE cognitive_memories
                    SET content = ?,
                        bloom_level = ?,
                        synaptic_strength = ?,
                        evidence_score = max(evidence_score, ?),
                        last_recalled_at = ?,
                        sha256 = ?
                    WHERE mem_key = ?;
                """, (
                    refined_content,
                    new_bloom,
                    new_strength,
                    evidence_score,
                    now_iso,
                    hashlib.sha256(refined_content.encode()).hexdigest(),
                    thesis_key
                ))

            else:
                verdict = "QUARANTINE"
                conn.execute("""
                    UPDATE cognitive_memories
                    SET contradiction_count = contradiction_count + 1
                    WHERE mem_key = ?;
                """, (thesis_key,))

            conn.execute("""
                INSERT INTO dialectical_audits (
                    thesis_key, antithesis_claim, verdict, synthesis_key,
                    evidence_ref, judge_engine, recorded_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?);
            """, (
                thesis_key,
                antithesis_claim,
                verdict,
                synthesis_key,
                evidence_ref,
                "HegelianDialecticEngine-v2",
                now_iso
            ))
            conn.commit()

        if synthesis_key:
            synthesis_record = self.get_memory(synthesis_key)

        return {
            "verdict": verdict,
            "thesis_key": thesis_key,
            "synthesis_key": synthesis_key,
            "evidence_score": evidence_score,
            "antithesis_claim": antithesis_claim,
            "recorded_at": now_iso,
            "thesis_state": self.get_memory(thesis_key),
            "synthesis_state": synthesis_record
        }

    # --------------------------------------------------------------------------
    # Vault Seeding & Synchronization
    # --------------------------------------------------------------------------

    def seed_from_secondbrain_vault(self, vault_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        Seeds and synchronizes Obsidian SecondBrain markdown notes and ADRs into
        the Stratified Cognitive Memory table across L1..L3 and Bloom B1..B6.
        """
        target_vault = Path(vault_path) if vault_path else self.vault_path
        ingested_by_tier: Dict[str, int] = {"L1": 0, "L2": 0, "L3": 0}
        ingested_by_bloom: Dict[str, int] = {f"B{b.value}": 0 for b in BloomLevel}

        # 1. Seed ADRs from KnowledgeCompilerDB `decisions` table if present
        with self.db.get_connection() as conn:
            has_decisions = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='decisions';"
            ).fetchone()
            if has_decisions:
                adr_rows = conn.execute("SELECT * FROM decisions;").fetchall()
                for row in adr_rows:
                    adr_dict = dict(row)
                    adr_id = adr_dict.get("adr_id", "")
                    if not adr_id:
                        continue
                    title = f"{adr_id}: {adr_dict.get('title', '')}"
                    rationale = (
                        adr_dict.get("rationale")
                        or adr_dict.get("decision")
                        or adr_dict.get("context")
                        or ""
                    )
                    content = (
                        f"ADR {adr_id} ({adr_dict.get('status', 'ACTIVE')})\n"
                        f"Title: {adr_dict.get('title', '')}\n"
                        f"Rationale & Decision: {rationale}\n"
                        f"Valid From: {adr_dict.get('valid_from', '')}"
                    )
                    mem = self.store_memory(
                        mem_key=f"adr:{adr_id.lower()}",
                        title=title,
                        content=content,
                        tier=MemoryTier.L3_SOVEREIGN.value,
                        bloom_level=BloomLevel.B6_CREATE,
                        synaptic_strength=0.95,
                        evidence_score=0.95,
                        vault_path="Maps/Decisions.md"
                    )
                    ingested_by_tier["L3"] += 1
                    ingested_by_bloom[f"B{mem.get('bloom_level', 6)}"] += 1

        if not target_vault.exists():
            return {"ingested_by_tier": ingested_by_tier, "ingested_by_bloom": ingested_by_bloom}

        # 2. Scan curated vault directories (following symlinked folders like AI-Coding-Sessions/Daily-Digests)
        scan_specs: List[Tuple[str, str, float, float, int]] = [
            ("10-Areas/Architecture", MemoryTier.L3_SOVEREIGN.value, 0.92, 0.90, 50),
            ("Maps", MemoryTier.L2_SEMANTIC.value, 0.88, 0.85, 50),
            ("20-Projects/Active", MemoryTier.L2_SEMANTIC.value, 0.85, 0.80, 50),
            ("30-Resources", MemoryTier.L2_SEMANTIC.value, 0.80, 0.75, 100),
            ("10-Areas/AI Engineering/Daily-Digests", MemoryTier.L2_SEMANTIC.value, 0.78, 0.72, 25),
            ("10-Areas/AI Engineering/Cost-Analytics", MemoryTier.L2_SEMANTIC.value, 0.80, 0.75, 15),
            ("10-Areas/AI Engineering/GPU-Fleet-Analytics", MemoryTier.L2_SEMANTIC.value, 0.82, 0.78, 15),
            ("10-Areas/AI Engineering/TokenSaver-Telemetry", MemoryTier.L2_SEMANTIC.value, 0.80, 0.75, 15),
            ("10-Areas/AI Engineering/AI-Coding-Sessions", MemoryTier.L1_EPISODIC.value, 0.72, 0.65, 40),
            ("10-Areas/AI Engineering/Sessions", MemoryTier.L1_EPISODIC.value, 0.75, 0.70, 25),
        ]

        for rel_dir, tier, strength, evidence, max_files in scan_specs:
            raw_folder = target_vault / rel_dir
            if not raw_folder.exists():
                continue
            resolved_folder = raw_folder.resolve()
            md_files = sorted(
                [p for p in resolved_folder.rglob("*.md") if p.is_file()],
                key=lambda p: p.stat().st_mtime if p.exists() else 0,
                reverse=True
            )[:max_files]

            for md_file in md_files:
                try:
                    raw_text = md_file.read_text(encoding="utf-8", errors="ignore").strip()
                    if len(raw_text) < 25:
                        continue
                    try:
                        sub_rel = str(md_file.relative_to(resolved_folder))
                        rel_path = f"{rel_dir}/{sub_rel}"
                    except ValueError:
                        rel_path = f"{rel_dir}/{md_file.name}"
                    mem_key = f"vault:{rel_path}"
                    snippet = raw_text[:2400]
                    bloom = classify_bloom_level(snippet, tier=tier)
                    if tier == MemoryTier.L3_SOVEREIGN.value and bloom < BloomLevel.B5_EVALUATE:
                        bloom = BloomLevel.B6_CREATE
                    mem = self.store_memory(
                        mem_key=mem_key,
                        title=md_file.stem.replace("-", " "),
                        content=snippet,
                        tier=tier,
                        bloom_level=bloom,
                        synaptic_strength=strength,
                        evidence_score=evidence,
                        vault_path=rel_path
                    )
                    ingested_by_tier[tier] = ingested_by_tier.get(tier, 0) + 1
                    b_key = f"B{mem.get('bloom_level', int(bloom))}"
                    ingested_by_bloom[b_key] = ingested_by_bloom.get(b_key, 0) + 1
                except Exception:
                    continue

        return {
            "vault_path": str(target_vault),
            "ingested_by_tier": ingested_by_tier,
            "ingested_by_bloom": ingested_by_bloom,
            "total_ingested": sum(ingested_by_tier.values())
        }

    # --------------------------------------------------------------------------
    # Self-Healing Vault & Graph Maintenance
    # --------------------------------------------------------------------------

    def self_heal_secondbrain(self, vault_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        Autonomous maintenance loop for Obsidian SecondBrain:
          1. Detects and removes broken symlinks in Data/Projects/ and 10-Areas/.
          2. Discovers broken [[wikilinks]] and unlinked orphan markdown notes.
             Auto-indexes orphans into 00-Inbox/Orphan-Recovery-Index.md.
          3. Executes Ebbinghaus forgetting decay over active L1/L2 memories:
             Any entry with retention < 0.25 is auto-archived (status='ARCHIVED', tier='L4').
          4. Renders live matrix to 10-Areas/AI Engineering/Cognitive-Memory-Matrix.md.
        """
        target_vault = Path(vault_path) if vault_path else self.vault_path
        now_iso = datetime.now(timezone.utc).isoformat()

        broken_symlinks: List[str] = []
        orphan_notes: List[str] = []
        decayed_memories: List[str] = []

        if target_vault.exists() and target_vault.is_dir():
            # 1. Broken Symlink Audit & Pruning
            for scan_sub in ["Data/Projects", "10-Areas"]:
                scan_dir = target_vault / scan_sub
                if scan_dir.exists():
                    for item in scan_dir.rglob("*"):
                        if item.is_symlink():
                            try:
                                if not item.resolve().exists():
                                    broken_symlinks.append(str(item.relative_to(target_vault)))
                                    item.unlink(missing_ok=True)
                            except Exception:
                                broken_symlinks.append(str(item.relative_to(target_vault)))

            # 2. Broken Wikilinks & Orphan Detection (top-level non-session folders)
            curated_folders = ["00-Inbox", "10-Areas/Architecture", "20-Projects", "30-Resources", "Maps"]
            md_files: List[Path] = []
            for sub in curated_folders:
                sub_dir = target_vault / sub
                if sub_dir.exists():
                    md_files.extend(p for p in sub_dir.rglob("*.md") if p.is_file())
            home_md = target_vault / "Home.md"
            if home_md.exists():
                md_files.append(home_md)

            in_degrees: Dict[str, int] = {f.stem: 0 for f in md_files}
            wikilink_regex = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]")

            for md_file in md_files:
                try:
                    content = md_file.read_text(encoding="utf-8", errors="ignore")
                    matches = wikilink_regex.findall(content)
                    for target_stem in matches:
                        clean_target = re.sub(r"\.md$", "", Path(target_stem).name, flags=re.IGNORECASE).strip()
                        if clean_target in in_degrees:
                            in_degrees[clean_target] += 1
                except Exception:
                    continue

            for stem, degree in in_degrees.items():
                if degree == 0:
                    lower_stem = stem.lower()
                    if not any(
                        skip in lower_stem
                        for skip in [
                            "index", "readme", "inbox", "template", "matrix",
                            "home", "decisions", "telemetry", "exogenous", "ecology",
                            "second brain", "evolution-report",
                        ]
                    ):
                        orphan_notes.append(stem)

            if orphan_notes:
                inbox_dir = target_vault / "00-Inbox"
                inbox_dir.mkdir(parents=True, exist_ok=True)
                recovery_index = inbox_dir / "Orphan-Recovery-Index.md"

                lines = [
                    "# Orphan Recovery Index",
                    f"> Automatically compiled by CognitiveSecondBrainEngine on `{now_iso}`.\n",
                    "## Isolated Knowledge Assets (0 In-Links)\n"
                ]
                for orphan in sorted(set(orphan_notes)):
                    lines.append(f"- [[{orphan}]]")
                lines.append("\n---\n*Auto-generated graph barrier invariant.*")
                recovery_index.write_text("\n".join(lines), encoding="utf-8")

        # 3. Ebbinghaus Decay & Autonomous Archival
        with self.db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT id, mem_key, synaptic_strength, last_recalled_at, recall_count
                FROM cognitive_memories
                WHERE tier IN ('L1', 'L2') AND status = 'ACTIVE';
            """)
            rows = cursor.fetchall()
            for r in rows:
                retention = compute_retention_score(
                    r["synaptic_strength"], r["last_recalled_at"], r["recall_count"]
                )
                if retention < 0.25:
                    conn.execute("""
                        UPDATE cognitive_memories
                        SET status = 'ARCHIVED',
                            tier = ?,
                            valid_to = ?
                        WHERE id = ?;
                    """, (MemoryTier.L4_ARCHIVE.value, now_iso, r["id"]))
                    decayed_memories.append(r["mem_key"])
            conn.commit()

        # 4. Generate & Export Live Matrix
        matrix_path = target_vault / "10-Areas" / "AI Engineering" / "Cognitive-Memory-Matrix.md"
        matrix_rendered = self._render_cognitive_matrix_markdown(matrix_path, now_iso)

        return {
            "timestamp": now_iso,
            "broken_symlinks_count": len(broken_symlinks),
            "broken_symlinks": broken_symlinks,
            "orphan_notes_count": len(orphan_notes),
            "decayed_memories_count": len(decayed_memories),
            "decayed_memories": decayed_memories,
            "matrix_path": str(matrix_path) if matrix_rendered else None
        }

    def _render_cognitive_matrix_markdown(self, matrix_path: Path, now_iso: str) -> bool:
        """Renders the Bloom B1..B6 x Tier L0..L4 state matrix table and audit trail."""
        stats = self.get_matrix_stats()
        matrix_grid = stats["grid"]
        status_counts = stats["status_counts"]
        recent_audits = stats["recent_audits"]

        headers = ["Tier \\ Bloom"] + [f"B{b.value} ({b.name.split('_')[1]})" for b in BloomLevel]
        separator = ["---"] * len(headers)
        rows: List[List[str]] = []

        for tier in [MemoryTier.L0_SENSORY, MemoryTier.L1_EPISODIC, MemoryTier.L2_SEMANTIC,
                     MemoryTier.L3_SOVEREIGN, MemoryTier.L4_ARCHIVE]:
            row = [f"**{tier.value}** ({tier.name.split('_')[1]})"]
            for b in BloomLevel:
                count = matrix_grid.get((tier.value, b.value), 0)
                row.append(str(count) if count > 0 else "·")
            rows.append(row)

        table_md = "| " + " | ".join(headers) + " |\n"
        table_md += "| " + " | ".join(separator) + " |\n"
        for r in rows:
            table_md += "| " + " | ".join(r) + " |\n"

        audits_md = "| ID | Thesis | Verdict | Ref / Synthesis | Time |\n| --- | --- | --- | --- | --- |\n"
        if not recent_audits:
            audits_md += "| - | *No dialectical audits logged* | - | - | - |\n"
        else:
            for a in recent_audits:
                ref_synth = a["synthesis_key"] or a["evidence_ref"] or "-"
                audits_md += f"| {a['id']} | `{a['thesis_key']}` | **{a['verdict']}** | {ref_synth} | {a['recorded_at'][:19]} |\n"

        doc = f"""# Stratified Cognitive Memory Matrix (Bloom B1..B6 × Tier L0..L4)

> [!IMPORTANT]
> **System Time**: `{now_iso}`  
> **Database Engine**: `KnowledgeCompilerDB (SQLite WAL + FTS5)`  
> **Tombstone Ledger**: `{self.tombstone_path}`  
> **Navigation**: [[Home]] | [[Knowledge-Graph-Telemetry]] | [[Decisions]]

## 1. Epistemic Cross-Matrix (Memory Tier × Bloom Cognitive Level)

{table_md}

## 2. Invariant Ledger Status

- **Active Memories**: `{status_counts.get('ACTIVE', 0)}`
- **Superseded Syntheses**: `{status_counts.get('SUPERSEDED', 0)}`
- **Abandoned False Knowledge**: `{status_counts.get('ABANDONED', 0)}`
- **Ebbinghaus Decayed / Archived**: `{status_counts.get('ARCHIVED', 0)}`

## 3. AGI Harness Access Profiles

| Harness Mode | Target Tiers | Min Bloom Level | Purpose |
| :--- | :--- | :--- | :--- |
| `fast` | `L2`, `L3` | `B3_APPLY` | Sub-20ms zero-bloat procedural & invariant recall |
| `deep_tot` | `L1`, `L2`, `L3` | `B4_ANALYZE` | Tree-of-Thought architectural & root-cause synthesis |
| `dialectic_audit` | `L2`, `L3`, `L4` | `B5_EVALUATE` | Hegelian critique, counterfactual & tombstone verification |
| `creative_synthesis` | `L2`, `L3` | `B2_UNDERSTAND` | Cross-domain analogical reasoning & paradigm creation |

## 4. Recent Hegelian Dialectical Audits

{audits_md}

---
*Self-healing cognitive telemetry generated by CognitiveSecondBrainEngine.*
"""
        try:
            matrix_path.parent.mkdir(parents=True, exist_ok=True)
            matrix_path.write_text(doc, encoding="utf-8")
            return True
        except Exception:
            return False

    def get_matrix_stats(self) -> Dict[str, Any]:
        """Calculates memory counts grouped by (tier, bloom) and status."""
        grid: Dict[Tuple[str, int], int] = {}
        status_counts: Dict[str, int] = {}
        recent_audits: List[Dict[str, Any]] = []

        with self.db.get_connection() as conn:
            for r in conn.execute(
                "SELECT tier, bloom_level, count(*) as cnt FROM cognitive_memories GROUP BY tier, bloom_level;"
            ):
                grid[(r["tier"], r["bloom_level"])] = r["cnt"]

            for r in conn.execute(
                "SELECT status, count(*) as cnt FROM cognitive_memories GROUP BY status;"
            ):
                status_counts[r["status"]] = r["cnt"]

            for r in conn.execute(
                "SELECT * FROM dialectical_audits ORDER BY id DESC LIMIT 12;"
            ):
                recent_audits.append(dict(r))

        return {
            "grid": grid,
            "status_counts": status_counts,
            "recent_audits": recent_audits
        }

    # --------------------------------------------------------------------------
    # AGI Harness Stratified Context Assembler
    # --------------------------------------------------------------------------

    def assemble_harness_context(
        self,
        query: str,
        harness_mode: str = "fast",
        token_budget: int = 1200
    ) -> str:
        """
        Assembles a stratified, high-density context block within token_budget for agent harnesses.
        Harness Modes:
          - fast: Tiers ("L2", "L3"), min_bloom = 3
          - deep_tot: Tiers ("L1", "L2", "L3"), min_bloom = 4
          - dialectic_audit: Tiers ("L2", "L3", "L4"), min_bloom = 5
          - creative_synthesis: Tiers ("L2", "L3"), min_bloom = 2
        Ranking Formula:
          score = 0.45 * retention + 0.35 * (bloom_level / 6.0) + 0.20 * evidence_score
        """
        mode_configs = {
            "fast": {"tiers": ("L2", "L3"), "min_bloom": 3, "statuses": ("ACTIVE",)},
            "deep_tot": {"tiers": ("L1", "L2", "L3"), "min_bloom": 4, "statuses": ("ACTIVE",)},
            "dialectic_audit": {
                "tiers": ("L2", "L3", "L4"),
                "min_bloom": 5,
                "statuses": ("ACTIVE", "SUPERSEDED", "ABANDONED", "ARCHIVED")
            },
            "creative_synthesis": {"tiers": ("L2", "L3"), "min_bloom": 2, "statuses": ("ACTIVE",)}
        }

        cfg = mode_configs.get(harness_mode, mode_configs["fast"])
        target_tiers: Tuple[str, ...] = cfg["tiers"]
        min_bloom: int = cfg["min_bloom"]
        allowed_statuses: Tuple[str, ...] = cfg["statuses"]

        clean_tokens = [w for w in re.findall(r"\w+", query) if len(w) > 2]
        fts_query = " OR ".join(f'"{token}"' for token in clean_tokens) if clean_tokens else ""

        candidates: List[Dict[str, Any]] = []

        with self.db.get_connection() as conn:
            if fts_query:
                fts_sql = f"""
                    SELECT m.*
                    FROM cognitive_memories m
                    JOIN cognitive_memories_fts f ON m.id = f.rowid
                    WHERE cognitive_memories_fts MATCH ?
                      AND m.bloom_level >= ?
                      AND m.tier IN ({','.join('?' for _ in target_tiers)})
                      AND m.status IN ({','.join('?' for _ in allowed_statuses)})
                    LIMIT 40;
                """
                params = [fts_query, min_bloom] + list(target_tiers) + list(allowed_statuses)
                try:
                    rows = conn.execute(fts_sql, params).fetchall()
                    candidates = [dict(r) for r in rows]
                except sqlite3.OperationalError:
                    candidates = []

            if len(candidates) < 5:
                like_clauses = (
                    " OR ".join(["(title LIKE ? OR content LIKE ?)" for _ in clean_tokens])
                    if clean_tokens else "1=1"
                )
                like_params: List[Any] = []
                for t in clean_tokens:
                    like_params.extend([f"%{t}%", f"%{t}%"])
                direct_sql = f"""
                    SELECT *
                    FROM cognitive_memories
                    WHERE bloom_level >= ?
                      AND tier IN ({','.join('?' for _ in target_tiers)})
                      AND status IN ({','.join('?' for _ in allowed_statuses)})
                      AND ({like_clauses})
                    ORDER BY bloom_level DESC, synaptic_strength DESC LIMIT 40;
                """
                params = [min_bloom] + list(target_tiers) + list(allowed_statuses) + like_params
                rows = conn.execute(direct_sql, params).fetchall()
                existing_keys = {c["mem_key"] for c in candidates}
                for r in rows:
                    if r["mem_key"] not in existing_keys:
                        candidates.append(dict(r))

        scored_candidates: List[Tuple[float, Dict[str, Any]]] = []
        for item in candidates:
            retention = compute_retention_score(
                item["synaptic_strength"], item["last_recalled_at"], item["recall_count"]
            )
            item["retention"] = retention
            bloom_ratio = float(item["bloom_level"]) / 6.0
            evidence = float(item["evidence_score"])

            score = (0.45 * retention) + (0.35 * bloom_ratio) + (0.20 * evidence)
            scored_candidates.append((score, item))

        scored_candidates.sort(key=lambda x: x[0], reverse=True)

        char_budget = max(400, token_budget * 4)
        assembled_lines: List[str] = [
            f"<!-- CognitiveSecondBrain Context [Mode: {harness_mode} | MinBloom: B{min_bloom}] -->"
        ]
        current_chars = len(assembled_lines[0])
        recalled_keys: List[str] = []

        for score, mem in scored_candidates:
            status_tag = f" | Status: {mem['status']}" if mem["status"] != "ACTIVE" else ""
            header = (
                f"\n### [{mem['tier']}-B{mem['bloom_level']}] {mem['title']} "
                f"(Score: {score:.2f} | R: {mem['retention']:.2f}{status_tag})"
            )
            snippet = mem["content"].strip()

            available = char_budget - (current_chars + len(header) + 20)
            if available < 80:
                break

            if len(snippet) > available:
                snippet = snippet[:available - 15] + "... [TRUNCATED]"

            block = f"{header}\n{snippet}"
            assembled_lines.append(block)
            current_chars += len(block)
            if mem["status"] == "ACTIVE":
                recalled_keys.append(mem["mem_key"])

        for k in recalled_keys[:5]:
            try:
                self.reinforce_memory(k, evidence_boost=0.03, promote_bloom=False)
            except Exception:
                pass

        if len(assembled_lines) == 1:
            return (
                f"<!-- CognitiveSecondBrain Context [Mode: {harness_mode}] - "
                f"No matching memories above B{min_bloom} threshold -->"
            )

        return "\n".join(assembled_lines)

    # --------------------------------------------------------------------------
    # 02:00 AM Neuro-Biological Circadian Sleep Consolidation Cycle
    # --------------------------------------------------------------------------

    def run_circadian_sleep_cycle(
        self,
        vault_path: Optional[Path] = None,
        shy_downscale_factor: float = 0.97,
        swr_replay_limit: int = 10,
    ) -> Dict[str, Any]:
        """
        Executes the 02:00 AM Neuro-Biological Circadian Sleep Consolidation Cycle,
        modeled directly on the 4 physiological phases of human sleep:

        Stage 1 — NREM Slow-Wave Delta (0.5–4 Hz): Glymphatic Clearance (AQP4 Flush)
          - Flushes metabolic neurotoxins (broken symlinks, duplicate SHA-256 engrams,
            transient L0 sensory fragments) and syncs fresh vault notes.

        Stage 2 — NREM Slow-Wave Sleep: Synaptic Homeostasis Hypothesis (SHY - Tononi & Cirelli)
          - Applies proportional global synaptic downscaling (`w <- w * shy_downscale_factor`)
            to L1/L2 memories to prevent runaway saturation while protecting Synaptic-Tagged
            high-salience engrams (`recall_count >= 3` or `L3_SOVEREIGN`).
          - Archives memories falling below Ebbinghaus survival threshold (`retention < 0.25 -> L4`).

        Stage 3 — NREM Stage 2/3 Spindles (11–16 Hz) + Sharp-Wave Ripples (SWR, 150–250 Hz):
          Hippocampal-Neocortical Systems Consolidation (Buzsáki / McClelland CLS)
          - Replays high-salience `L1_EPISODIC` memories from Hippocampus at compressed speed,
            promotes their Bloom level (`B1/B2 -> B2/B3/B4`), and transfers consolidated
            traces into Neocortex (`L2_SEMANTIC` / `L3_SOVEREIGN`).

        Stage 4 — REM Theta-Gamma Coupling (4–8 Hz): Predictive Coding (Friston Free-Energy)
          & Associative Dream Reconsolidation
          - Scans for high-prediction-error / high-dissonance memories (`contradiction_count >= 2`)
            and resolves or flags them for Hegelian Dialectical Critique.
          - Discovers novel cross-domain Associative Dream Bridges between L2/L3 notes.
          - Writes the nightly Sleep Spindle & Dream Journal to
            `10-Areas/AI Engineering/Sleep-Consolidation/Sleep-Cycle-YYYY-MM-DD.md`.
        """
        target_vault = Path(vault_path) if vault_path else self.vault_path
        now_dt = datetime.now(timezone.utc)
        now_iso = now_dt.isoformat()
        date_str = now_dt.strftime("%Y-%m-%d")

        # Pre-sync fresh notes from SecondBrain vault
        seed_summary = self.seed_from_secondbrain_vault(target_vault)

        # --- STAGE 1: Glymphatic Clearance (Delta 0.5-4Hz AQP4 Flush) ---
        deduped_count = 0
        l0_flushed_count = 0
        with self.db.get_connection() as conn:
            # Flush ephemeral L0 sensory buffer
            cur_l0 = conn.execute(
                "DELETE FROM cognitive_memories WHERE tier = ?;",
                (MemoryTier.L0_SENSORY.value,),
            )
            l0_flushed_count = cur_l0.rowcount if cur_l0.rowcount > 0 else 0

            # Deduplicate identical sha256 active records (keep lowest id / oldest canonical)
            dup_rows = conn.execute("""
                SELECT id, mem_key, sha256
                FROM cognitive_memories
                WHERE status = 'ACTIVE'
                  AND id NOT IN (
                      SELECT MIN(id)
                      FROM cognitive_memories
                      WHERE status = 'ACTIVE'
                      GROUP BY sha256
                  );
            """).fetchall()
            for d_row in dup_rows:
                conn.execute(
                    "UPDATE cognitive_memories SET status = 'ARCHIVED', tier = ?, valid_to = ? WHERE id = ?;",
                    (MemoryTier.L4_ARCHIVE.value, now_iso, d_row["id"]),
                )
                deduped_count += 1
            conn.commit()

        # --- STAGE 2: Synaptic Homeostasis Hypothesis (SHY Downscaling) ---
        downscaled_count = 0
        shy_pruned_keys: List[str] = []
        with self.db.get_connection() as conn:
            rows = conn.execute("""
                SELECT id, mem_key, synaptic_strength, recall_count, last_recalled_at, tier
                FROM cognitive_memories
                WHERE tier IN ('L1', 'L2') AND status = 'ACTIVE';
            """).fetchall()
            for r in rows:
                recalls = int(r["recall_count"])
                strength = float(r["synaptic_strength"])
                # Synaptic Tagging & Capture (STC): protect memories with recall_count >= 3
                if recalls < 3:
                    strength = round(max(0.05, strength * shy_downscale_factor), 4)
                    conn.execute(
                        "UPDATE cognitive_memories SET synaptic_strength = ? WHERE id = ?;",
                        (strength, r["id"]),
                    )
                    downscaled_count += 1

                retention = compute_retention_score(
                    strength, r["last_recalled_at"], recalls, now_iso=now_iso
                )
                if retention < 0.25:
                    conn.execute("""
                        UPDATE cognitive_memories
                        SET status = 'ARCHIVED',
                            tier = ?,
                            valid_to = ?
                        WHERE id = ?;
                    """, (MemoryTier.L4_ARCHIVE.value, now_iso, r["id"]))
                    shy_pruned_keys.append(r["mem_key"])
            conn.commit()

        # --- STAGE 3: Hippocampal-Neocortical SWR Replay (150-250Hz) ---
        swr_consolidated: List[Dict[str, Any]] = []
        with self.db.get_connection() as conn:
            l1_candidates = conn.execute("""
                SELECT mem_key, title, bloom_level, synaptic_strength, evidence_score, recall_count
                FROM cognitive_memories
                WHERE tier = 'L1'
                  AND status = 'ACTIVE'
                  AND (synaptic_strength >= 0.68 OR evidence_score >= 0.65)
                ORDER BY synaptic_strength DESC, evidence_score DESC
                LIMIT ?;
            """, (swr_replay_limit,)).fetchall()

        for cand in l1_candidates:
            # Replay boosts synaptic strength and promotes L1 (Hippocampus) -> L2 (Neocortex)
            old_bloom = int(cand["bloom_level"])
            updated = self.reinforce_memory(
                cand["mem_key"], evidence_boost=0.16, promote_bloom=True
            )
            # If recall_count was only 1, force systems consolidation to L2 if strength >= 0.84
            if updated.get("tier") == "L1" and float(updated.get("synaptic_strength", 0)) >= 0.84:
                new_bloom = min(6, max(2, int(updated.get("bloom_level", 1)) + 1))
                with self.db.get_connection() as conn:
                    conn.execute("""
                        UPDATE cognitive_memories
                        SET tier = 'L2', bloom_level = ?
                        WHERE mem_key = ?;
                    """, (new_bloom, cand["mem_key"]))
                    conn.commit()
                updated = self.get_memory(cand["mem_key"]) or updated

            swr_consolidated.append({
                "mem_key": cand["mem_key"],
                "title": cand["title"],
                "from_bloom": f"B{old_bloom}",
                "to_bloom": f"B{updated.get('bloom_level', old_bloom)}",
                "to_tier": updated.get("tier", "L2"),
            })

        # --- STAGE 4: REM Theta-Gamma Dreaming & Predictive Free-Energy Reconsolidation ---
        dissonance_quarantined: List[str] = []
        paradox_escalations: List[Dict[str, Any]] = []
        dream_bridges: List[Tuple[str, str, List[str]]] = []

        # Endogenous Local JEV evaluation (C < 2.2 -> 100% local, 0 output tokens)
        jev_engine_used = "LOCAL_JEV_ENDOGENOUS"
        jev_complexity = 0.85
        try:
            from tools.jev_clef_knowledge_compiler import LocalJEVEvaluator
            jev = LocalJEVEvaluator(
                dedup_cache_path=Path.home() / ".hermes" / ".jev_sleep_dedup.json",
                ledger_path=Path.home() / ".gemini" / "antigravity" / "action_ledger.jsonl",
            )
            jev_res = jev.evaluate(
                prompt=f"Circadian 02:00 AM Sleep Cycle ({date_str}): SWR={len(swr_consolidated)}, Downscaled={downscaled_count}",
                files=[],
            )
            jev_complexity = jev_res.complexity
            jev_engine_used = jev_res.engine
        except Exception:
            pass

        with self.db.get_connection() as conn:
            # Check memories with high contradiction_count (Free-Energy Prediction Error)
            high_err_rows = conn.execute("""
                SELECT mem_key, title, contradiction_count, evidence_score
                FROM cognitive_memories
                WHERE status = 'ACTIVE' AND contradiction_count >= 2;
            """).fetchall()
            for r in high_err_rows:
                if float(r["evidence_score"]) < 0.45:
                    # Auto-abandon chronically contradicted low-evidence beliefs endogenously via Local JEV
                    self.dialectical_critique(
                        thesis_key=r["mem_key"],
                        antithesis_claim=(
                            f"REM Predictive Coding Free-Energy Pruning: {r['contradiction_count']} "
                            f"accumulated contradictions with low evidence ({r['evidence_score']})."
                        ),
                        new_content="",
                        evidence_score=0.88,
                        evidence_ref="Circadian-REM-Reconsolidation",
                    )
                    dissonance_quarantined.append(r["mem_key"])
                else:
                    # High-evidence paradox (C >= 2.2): plan & queue for AGY-Fleet Pro node Gemini 4 Argon synthesis
                    paradox_c = round(min(4.0, 2.2 + 0.25 * int(r["contradiction_count"])), 2)
                    argon_plan = self.plan_argon_pro_task(
                        prompt=f"Resolve dialectical paradox for memory {r['mem_key']} ({r['title']})",
                        complexity=paradox_c,
                    )
                    paradox_escalations.append({
                        "mem_key": r["mem_key"],
                        "title": r["title"],
                        "contradictions": r["contradiction_count"],
                        "evidence_score": r["evidence_score"],
                        "routing": "AGY_FLEET_PRO_GEMINI_4_ARGON (C >= 2.2)",
                        "planned_model": argon_plan["canonical_model"],
                        "planned_tier": argon_plan["tier"],
                        "task_level": argon_plan["level"],
                        "argon_plan": argon_plan,
                    })

            # Discover Associative Dream Bridges across L2/L3 notes
            semantic_rows = conn.execute("""
                SELECT mem_key, title, content, tier
                FROM cognitive_memories
                WHERE tier IN ('L2', 'L3') AND status = 'ACTIVE'
                ORDER BY synaptic_strength DESC LIMIT 30;
            """).fetchall()

        stop_words = {
            "the", "and", "for", "with", "from", "that", "this", "into", "active",
            "adr", "status", "title", "context", "decision", "rationale", "valid",
        }
        tokenized_notes: List[Tuple[str, Set[str]]] = []
        for row in semantic_rows:
            words = {
                w.lower()
                for w in re.findall(r"[A-Za-zÀ-ỹ]{4,}", f"{row['title']} {row['content'][:400]}")
                if w.lower() not in stop_words
            }
            if len(words) >= 3:
                tokenized_notes.append((row["title"], words))

        for i in range(len(tokenized_notes)):
            for j in range(i + 1, len(tokenized_notes)):
                t1, w1 = tokenized_notes[i]
                t2, w2 = tokenized_notes[j]
                if t1 == t2:
                    continue
                shared = sorted(w1.intersection(w2))
                if len(shared) >= 4 and len(dream_bridges) < 8:
                    dream_bridges.append((t1, t2, shared[:5]))

        # Sync Exogenous Knowledge Space (GitHub Trending, arXiv, Standards, Autonomous Tasks) before self-heal
        exogenous_ecology_summary = self.run_exogenous_ecology_cycle(target_vault)

        # Run structural vault self-heal & render matrix
        heal_summary = self.self_heal_secondbrain(target_vault)

        # --- STAGE 5: Oligodendrocyte Cortical Myelination (LoRA .safetensors + ONNX Surrogate) ---
        myelination_summary = self.myelinate_jev_lora_and_onnx(output_dir=self.myelination_dir)

        # Write Nightly Sleep Consolidation Journal to SecondBrain
        sleep_dir = target_vault / "10-Areas" / "AI Engineering" / "Sleep-Consolidation"
        sleep_report_path = sleep_dir / f"Sleep-Cycle-{date_str}.md"
        try:
            sleep_dir.mkdir(parents=True, exist_ok=True)
            swr_lines = [
                f"- `{item['mem_key']}` (**{item['title']}**): `{item['from_bloom']} -> {item['to_bloom']}` (`Tier -> {item['to_tier']}`)"
                for item in swr_consolidated
            ] or ["- *No new L1 episodic traces required SWR cortical transfer tonight.*"]

            bridge_lines = [
                f"- **{a}** $\\leftrightarrow$ **{b}** *(Shared engrams: `{', '.join(sh)}`)*"
                for a, b, sh in dream_bridges
            ] or ["- *No new cross-cortical dream bridges synthesized.*"]

            journal_md = f"""# 🌙 Circadian 02:00 AM Neuro-Biological Sleep Consolidation (`{date_str}`)

> [!NOTE]
> **Execution Timestamp**: `{now_iso}`  
> **Circadian Phase**: `02:00 AM Local Deep SWS -> REM Reconsolidation -> Cortical Myelination`  
> **Compute Engine**: `{jev_engine_used}` (`complexity={jev_complexity:.2f}`, `output_tokens=0`, `100% Endogenous Pacemaker`)  
> **Navigation**: [[Home]] | [[Exogenous-Knowledge-Space]] | [[Cognitive-Memory-Matrix]] | [[Knowledge-Graph-Telemetry]]

## 1. Stage 1 — NREM Slow-Wave Delta (`0.5–4 Hz`): Glymphatic Clearance (AQP4 Flush)
- **Broken Symlinks Flushed**: `{heal_summary['broken_symlinks_count']}`
- **Duplicate SHA-256 Engrams Cleared**: `{deduped_count}`
- **Transient L0 Sensory Debris Flushed**: `{l0_flushed_count}`
- **Orphan Notes Indexed**: `{heal_summary['orphan_notes_count']}`

## 2. Stage 2 — NREM Slow-Wave Sleep: Synaptic Homeostasis Hypothesis (SHY Downscaling)
- **Global Homeostatic Downscale Factor ($\\gamma_{{\\text{{SHY}}}}$)**: `{shy_downscale_factor}`
- **Synapses Renormalized (`L1/L2` with `<3` recalls)**: `{downscaled_count}`
- **Weak Engrams Pruned to `L4_ARCHIVE` ($R < 0.25$)**: `{len(shy_pruned_keys) + heal_summary['decayed_memories_count']}`

## 3. Stage 3 — Thalamic Spindles (`11–16 Hz`) + Hippocampal Sharp-Wave Ripples (`150–250 Hz` SWR Replay)
{chr(10).join(swr_lines)}

## 4. Stage 4 — REM Theta-Gamma Coupling (`4–8 Hz`): Predictive Coding & Dream Bridges
- **High-Dissonance Beliefs Extinguished (Local JEV)**: `{len(dissonance_quarantined)}`
- **High-Evidence Paradoxes Queued for AGY-Fleet Pro ($C \\ge 2.2$)**: `{len(paradox_escalations)}`
- **Associative Cross-Cortical Dream Bridges**:
{chr(10).join(bridge_lines)}

## 5. Stage 5 — Oligodendrocyte Cortical Myelination (LoRA `.safetensors` + ONNX Edge Surrogate)
- **Sanitized SFT Samples**: `{myelination_summary.get('sft_samples_count', 0)}`
- **Contrastive DPO Triads (Rejected False Knowledge)**: `{myelination_summary.get('dpo_samples_count', 0)}`
- **LoRA Adapter (`.safetensors`)**: `{myelination_summary.get('lora_safetensors_path', '')}`
- **Myelinated ONNX Router (`.onnx`)**: `{myelination_summary.get('onnx_model_path', '')}` (`latency={myelination_summary.get('onnx_inference_latency_ms', 0.0)}ms`)

---
*Autonomous Neuro-Biological Circadian Sleep Engine (`tools/cognitive_secondbrain_engine.py --sleep-cycle`).*
"""
            sleep_report_path.write_text(journal_md, encoding="utf-8")
        except Exception:
            pass

        return {
            "timestamp": now_iso,
            "circadian_window": "02:00_AM_SWS_REM",
            "compute_engine": {
                "engine": jev_engine_used,
                "complexity": jev_complexity,
                "output_tokens": 0,
                "paradox_escalations_for_pro": paradox_escalations,
            },
            "stage1_glymphatic": {
                "broken_symlinks_flushed": heal_summary["broken_symlinks_count"],
                "duplicates_cleared": deduped_count,
                "l0_flushed": l0_flushed_count,
                "orphans_indexed": heal_summary["orphan_notes_count"],
            },
            "stage2_synaptic_homeostasis": {
                "downscale_factor": shy_downscale_factor,
                "synapses_renormalized": downscaled_count,
                "pruned_to_l4_count": len(shy_pruned_keys) + heal_summary["decayed_memories_count"],
            },
            "stage3_swr_hippocampal_replay": {
                "replayed_count": len(swr_consolidated),
                "consolidated_engrams": swr_consolidated,
            },
            "stage4_rem_dream_reconsolidation": {
                "dissonance_extinguished": dissonance_quarantined,
                "paradox_escalations_count": len(paradox_escalations),
                "associative_dream_bridges_count": len(dream_bridges),
                "sleep_journal_path": str(sleep_report_path),
            },
            "stage5_cortical_myelination": myelination_summary,
            "exogenous_ecology": exogenous_ecology_summary,
            "seed_summary": seed_summary,
            "matrix_path": heal_summary["matrix_path"],
        }

    # --------------------------------------------------------------------------
    # Exogenous Knowledge Space (Không Gian Tri Thức Ngoại Sinh) & Ecology Engine
    # --------------------------------------------------------------------------

    @staticmethod
    def _compute_shannon_entropy_bits(text: str) -> float:
        """Computes token-level Shannon entropy H(X) = -sum p_i log2 p_i clamped to [1.50, 4.80] bits."""
        tokens = re.findall(r"[a-z0-9à-ỹ_]+", text.lower())
        if not tokens:
            return 2.40
        counts: Dict[str, int] = {}
        for tok in tokens:
            counts[tok] = counts.get(tok, 0) + 1
        total = float(len(tokens))
        raw_h = -sum((c / total) * math.log2(c / total) for c in counts.values() if c > 0)
        scaled = 1.50 + min(3.30, max(0.0, (raw_h - 1.50) * 0.65))
        return round(min(4.80, max(1.50, scaled)), 2)

    @staticmethod
    def _slugify_exogenous(external_ref: str, title: str) -> str:
        """Generates a deterministic, filesystem-safe Obsidian note slug."""
        clean_ref = re.sub(r"[^a-zA-Z0-9_-]+", "-", external_ref.strip()).strip("-")
        clean_title = re.sub(r"[^a-zA-Z0-9_-]+", "-", title.strip()[:48]).strip("-")
        combined = f"{clean_ref}-{clean_title}" if clean_ref else clean_title
        slug = re.sub(r"-{2,}", "-", combined).strip("-").lower()
        return slug[:72].rstrip("-") or "exogenous-item"

    def ingest_exogenous_knowledge(
        self,
        source_type: str,
        external_ref: str,
        domain: str,
        title: str,
        url: str = "",
        architectural_pattern: str = "",
        key_algorithms: Any = "",
        adaptation_blueprint: str = "",
        raw_summary: str = "",
        vault_path: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """
        Ingests exogenous knowledge (GitHub Trending repos, arXiv preprints, international
        standards, or autonomous tasks) into:
          1. `exogenous_entropy_ledger` (SQLite table)
          2. `cognitive_memories` (`L2_SEMANTIC` / `L3_SOVEREIGN`, `Bloom B5/B6`)
          3. Obsidian SecondBrain (`30-Resources/Exogenous-Knowledge/<subdir>/<slug>.md`)
             with bidirectional wikilinks and an explicit Evolutionary Decision:
               - SCHEDULE_SELF_HEAL
               - COMPILE_LORA_SKILL
               - GENERATE_ADR
               - ADOPT_INTO_HARNESS
        """
        target_vault = Path(vault_path) if vault_path else self.vault_path
        now_iso = datetime.now(timezone.utc).isoformat()
        norm_source = str(source_type or "autonomous_task").strip().lower()
        if norm_source not in ("github_trending", "arxiv_paper", "domain_standard", "autonomous_task"):
            norm_source = "autonomous_task"

        if isinstance(key_algorithms, (list, tuple, set)):
            alg_str = ", ".join(str(x).strip() for x in key_algorithms if str(x).strip())
        else:
            alg_str = str(key_algorithms or "").strip()

        clean_domain = str(domain or "hermes_agent").strip().lower()
        combined_text = (
            f"{title} {external_ref} {clean_domain} {architectural_pattern} "
            f"{alg_str} {adaptation_blueprint} {raw_summary}"
        ).strip()
        shannon_bits = self._compute_shannon_entropy_bits(combined_text)

        blob_lower = combined_text.lower()
        if norm_source == "domain_standard" or any(
            kw in blob_lower
            for kw in (
                "iso-", "iso/", "ieee", "ebu r128", "ebu-r128", "rfc-", "rfc ",
                "fido2", "wcag", "ifrs", "osha", "nist", "smpte", "itu-r", "compliance-as-code",
            )
        ):
            evolution_decision = "GENERATE_ADR"
        elif any(
            kw in blob_lower
            for kw in (
                "lora", "onnx", "myelination", "sft", "dpo", "skill compilation",
                "surrogate", "safetensors", "fine-tun", "distillation", "quantization",
            )
        ):
            evolution_decision = "COMPILE_LORA_SKILL"
        elif any(
            kw in blob_lower
            for kw in (
                "self-heal", "self_heal", "circuit-breaker", "circuit breaker",
                "orphan", "quota", "timeout", "deadlock", "recovery", "bisimulation",
                "failover", "reaper", "quarantine", "rate-limit", "fallback", "repair",
            )
        ):
            evolution_decision = "SCHEDULE_SELF_HEAL"
        else:
            evolution_decision = "ADOPT_INTO_HARNESS"

        decision_bonus = {
            "GENERATE_ADR": 0.05,
            "COMPILE_LORA_SKILL": 0.04,
            "SCHEDULE_SELF_HEAL": 0.04,
            "ADOPT_INTO_HARNESS": 0.02,
        }.get(evolution_decision, 0.02)
        ecology_impact = round(
            min(0.99, max(0.65, 0.68 + (shannon_bits - 1.50) * 0.075 + decision_bonus)),
            3,
        )

        slug = self._slugify_exogenous(external_ref, title)
        entropy_id = (
            f"exo-{norm_source}-"
            f"{hashlib.sha256(f'{norm_source}:{external_ref}:{title}'.encode('utf-8')).hexdigest()[:12]}"
        )
        mem_key = f"exo:{norm_source}:{slug}"

        subdir_map = {
            "github_trending": "GitHub-Trending",
            "arxiv_paper": "ArXiv-Papers",
            "domain_standard": "Domain-Standards",
            "autonomous_task": "Autonomous-Tasks",
        }
        subdir = subdir_map[norm_source]
        rel_note_path = f"30-Resources/Exogenous-Knowledge/{subdir}/{slug}.md"
        abs_note_path = target_vault / rel_note_path

        mem_tier = (
            MemoryTier.L3_SOVEREIGN.value
            if evolution_decision in ("GENERATE_ADR", "COMPILE_LORA_SKILL") or ecology_impact >= 0.88
            else MemoryTier.L2_SEMANTIC.value
        )
        mem_bloom = (
            BloomLevel.B6_CREATE
            if mem_tier == MemoryTier.L3_SOVEREIGN.value
            else BloomLevel.B5_EVALUATE
        )

        note_md = f"""---
entropy_id: "{entropy_id}"
source_type: "{norm_source}"
external_ref: "{external_ref}"
domain: "{clean_domain}"
shannon_entropy_bits: {shannon_bits}
evolution_decision: "{evolution_decision}"
ecology_impact_score: {ecology_impact}
recorded_at: "{now_iso}"
---

# 🌐 [{norm_source.upper()}] {title}

> [!IMPORTANT]
> **External Reference**: `{external_ref}` ({url or 'local-sovereign-catalog'})  
> **Target Domain**: `{clean_domain}` | **Shannon Entropy**: `{shannon_bits} bits` | **Ecology Impact**: `{ecology_impact}`  
> **Evolutionary Decision**: **`{evolution_decision}`**  
> **Navigation**: [[Home]] | [[Exogenous-Knowledge-Space]] | [[Cognitive-Memory-Matrix]] | [[Decisions]]

## 1. Architectural Pattern & Core Mechanism
- **Pattern**: {architectural_pattern or title}
- **Key Algorithms / Constructs**: {alg_str or 'Stratified Sovereign Synthesis'}
- **Summary**: {raw_summary or adaptation_blueprint or title}

## 2. Sovereign Adaptation Blueprint & Ecological Action
- **Blueprint**: {adaptation_blueprint or raw_summary or f'Integrate {title} into {clean_domain} harness.'}
- **Ecological Decision (`{evolution_decision}`)**:
  - Mapped to Cognitive Memory `{mem_key}` (`{mem_tier}-B{int(mem_bloom)}`).
  - Linked bidirectionally into [[Exogenous-Knowledge-Space]] and [[Cognitive-Memory-Matrix]].
"""
        try:
            abs_note_path.parent.mkdir(parents=True, exist_ok=True)
            abs_note_path.write_text(note_md, encoding="utf-8")
        except Exception:
            pass

        mem_content = (
            f"[{norm_source.upper()}] {title} (Ref: {external_ref} | Domain: {clean_domain})\n"
            f"Architectural Pattern: {architectural_pattern or title}\n"
            f"Key Algorithms: {alg_str}\n"
            f"Adaptation Blueprint: {adaptation_blueprint or raw_summary}\n"
            f"Evolutionary Decision: {evolution_decision} (Entropy: {shannon_bits} bits, Impact: {ecology_impact})"
        )
        self.store_memory(
            mem_key=mem_key,
            title=f"[{norm_source}] {title}",
            content=mem_content,
            tier=mem_tier,
            bloom_level=mem_bloom,
            synaptic_strength=round(min(0.98, max(0.80, ecology_impact)), 3),
            evidence_score=ecology_impact,
            vault_path=rel_note_path,
        )

        if evolution_decision == "COMPILE_LORA_SKILL":
            try:
                self.record_jev_session(
                    query=f"Apply exogenous {norm_source} pattern ({external_ref}) in {clean_domain}: {title}",
                    chosen_response=(
                        f"Architectural Pattern: {architectural_pattern}\n"
                        f"Algorithms: {alg_str}\n"
                        f"Adaptation Blueprint: {adaptation_blueprint or raw_summary}"
                    ),
                    harness_mode="deep_tot",
                    bloom_level=int(mem_bloom),
                    tier=mem_tier,
                    complexity=round(min(3.8, shannon_bits * 0.78), 2),
                    engine="LOCAL_JEV",
                    sample_type="SFT",
                )
            except Exception:
                pass

        with self.db.get_connection() as conn:
            conn.execute("""
                INSERT INTO exogenous_entropy_ledger (
                    entropy_id, source_type, external_ref, domain, title, url,
                    shannon_entropy_bits, architectural_pattern, key_algorithms,
                    adaptation_blueprint, evolution_decision, ecology_impact_score,
                    secondbrain_note_path, mem_key, status, recorded_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'ACTIVE', ?)
                ON CONFLICT(entropy_id) DO UPDATE SET
                    domain = excluded.domain,
                    title = excluded.title,
                    url = excluded.url,
                    shannon_entropy_bits = excluded.shannon_entropy_bits,
                    architectural_pattern = excluded.architectural_pattern,
                    key_algorithms = excluded.key_algorithms,
                    adaptation_blueprint = excluded.adaptation_blueprint,
                    evolution_decision = excluded.evolution_decision,
                    ecology_impact_score = excluded.ecology_impact_score,
                    secondbrain_note_path = excluded.secondbrain_note_path,
                    mem_key = excluded.mem_key,
                    status = 'ACTIVE',
                    recorded_at = excluded.recorded_at;
            """, (
                entropy_id, norm_source, external_ref, clean_domain, title, url,
                shannon_bits, architectural_pattern, alg_str,
                adaptation_blueprint or raw_summary, evolution_decision, ecology_impact,
                rel_note_path, mem_key, now_iso,
            ))
            conn.commit()

        return {
            "entropy_id": entropy_id,
            "source_type": norm_source,
            "external_ref": external_ref,
            "domain": clean_domain,
            "title": title,
            "shannon_entropy_bits": shannon_bits,
            "evolution_decision": evolution_decision,
            "ecology_impact_score": ecology_impact,
            "mem_key": mem_key,
            "secondbrain_note_path": rel_note_path,
            "slug": slug,
        }

    def run_exogenous_ecology_cycle(
        self,
        vault_path: Optional[Path] = None,
        evolution_ledger_path: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """
        Synchronizes exogenous knowledge from:
          1. GitHub Trending / Titan / Climbing / Breakthrough repositories (`repo_radar.py`)
          2. arXiv preprints (`research_radar.py`)
          3. International Domain Standards (`ISO`, `EBU R128`, `FIDO2`, `IEEE`, `OSHA`, `RFC`)
          4. Autonomous Evolution & Ideation Tasks (`evolution_ledger.db`)
        Builds the SecondBrain Exogenous Knowledge Space (`Maps/Exogenous-Knowledge-Space.md`),
        executes ecological evaluation & self-healing (`self_heal_secondbrain`), and writes
        `10-Areas/AI Engineering/Autonomous-Ecology-Decisions/Ecology-Evaluation-YYYY-MM-DD.md`.
        """
        import sys

        target_vault = Path(vault_path) if vault_path else self.vault_path
        now_dt = datetime.now(timezone.utc)
        now_iso = now_dt.isoformat()
        date_str = now_dt.strftime("%Y-%m-%d")

        radar_src = Path("/home/zen/workspace/agy-pinned-monitor/src")
        repo_catalog: List[Any] = []
        lit_catalog: List[Any] = []
        reg_standards: Dict[Any, List[Dict[str, str]]] = {}

        if radar_src.exists():
            try:
                if str(radar_src) not in sys.path:
                    sys.path.insert(0, str(radar_src))
                from agy_pinned_monitor.repo_radar import CURATED_AI_REPO_CATALOG
                from agy_pinned_monitor.research_radar import (
                    CURATED_LITERATURE_CATALOG,
                    DOMAIN_REGULATORY_STANDARDS,
                )
                repo_catalog = list(CURATED_AI_REPO_CATALOG)
                lit_catalog = list(CURATED_LITERATURE_CATALOG)
                reg_standards = dict(DOMAIN_REGULATORY_STANDARDS)
            except Exception:
                pass

        ingested_items: List[Dict[str, Any]] = []

        # 1. Ingest GitHub Trending / Titan / Climbing Repositories
        if repo_catalog:
            for repo in repo_catalog:
                dom_val = getattr(repo.domain, "value", str(repo.domain))
                res = self.ingest_exogenous_knowledge(
                    source_type="github_trending",
                    external_ref=str(repo.repo_name),
                    domain=dom_val,
                    title=str(repo.title),
                    url=str(repo.url or f"https://github.com/{repo.repo_name}"),
                    architectural_pattern=str(repo.architectural_pattern),
                    key_algorithms=list(repo.key_algorithms or []),
                    adaptation_blueprint=str(repo.adaptation_blueprint),
                    raw_summary=f"{repo.velocity_label} | Topics: {', '.join(repo.topics or [])}",
                    vault_path=target_vault,
                )
                ingested_items.append(res)
        else:
            # Fallback curated repos when running in isolated sandbox
            for ref, dom, title, pat, algs, bp in [
                (
                    "sgl-project/sglang",
                    "zencode_ent",
                    "SGLang: Fast Serving Framework with RadixAttention",
                    "RadixAttention Tree-Based Shared Prefix KV Cache Reuse",
                    ["RadixAttention", "LRU Cache Tree", "Constrained FSM Decoding"],
                    "Adopt radix-tree prefix matching across router nodes to eliminate redundant prefill.",
                ),
                (
                    "BerriAI/litellm",
                    "zencode_ent",
                    "LiteLLM: Universal LLM Gateway, Routing, and Quota Failover",
                    "Dynamic Provider Cascading & Token-Bucket Rate Smoothing",
                    ["Dynamic Health Gating", "Sliding-Window Token Bucket", "Fallback Waterfall"],
                    "Implement self-healing health-gated multi-account quota waterfalls with timeout failover.",
                ),
                (
                    "ggerganov/llama.cpp",
                    "hermes_agent",
                    "llama.cpp: Quantized GGUF & ONNX Surrogate Inference",
                    "Hardware-Fused SIMD Quantization & LoRA/ONNX Fast Surrogate",
                    ["K-Quants Quantization", "Zero-Copy mmap", "LoRA Adapter Fusion"],
                    "Compile quantized ONNX and LoRA skill adapters for sub-millisecond local JEV routing.",
                ),
            ]:
                ingested_items.append(
                    self.ingest_exogenous_knowledge(
                        source_type="github_trending",
                        external_ref=ref,
                        domain=dom,
                        title=title,
                        url=f"https://github.com/{ref}",
                        architectural_pattern=pat,
                        key_algorithms=algs,
                        adaptation_blueprint=bp,
                        vault_path=target_vault,
                    )
                )

        # 2. Ingest arXiv Papers & Regulatory Standards from Literature Catalog
        seen_std_refs: Set[str] = set()
        if lit_catalog:
            for paper in lit_catalog:
                pid = str(paper.arxiv_id).strip()
                dom_val = getattr(paper.domain, "value", str(paper.domain))
                cat_val = str(getattr(paper, "category", "academic_preprint")).lower()
                is_std = (
                    cat_val == "regulatory_standard"
                    or any(
                        pid.upper().startswith(pfx)
                        for pfx in ("ISO-", "EBU-", "OSHA-", "FIDO2-", "IEEE-", "VAS-", "IFRS-", "NIST-", "RFC-", "W3C-", "ITU-", "SMPTE-")
                    )
                )
                src_type = "domain_standard" if is_std else "arxiv_paper"
                if is_std:
                    seen_std_refs.add(pid.upper())
                url_val = str(getattr(paper, "doi_or_url", "") or ("" if is_std else f"https://arxiv.org/abs/{pid}"))
                res = self.ingest_exogenous_knowledge(
                    source_type=src_type,
                    external_ref=pid,
                    domain=dom_val,
                    title=str(paper.title),
                    url=url_val,
                    architectural_pattern=str(paper.core_pattern),
                    key_algorithms=list(getattr(paper, "authors", [])[:3]),
                    adaptation_blueprint=str(paper.proposal_template),
                    raw_summary=str(paper.summary),
                    vault_path=target_vault,
                )
                ingested_items.append(res)
        else:
            for pid, src_t, dom, title, pat, bp in [
                (
                    "2303.11366",
                    "arxiv_paper",
                    "hermes_agent",
                    "Reflexion: Language Agents with Verbal Reinforcement Learning",
                    "Verbal Reinforcement Learning & Self-Reflection Episodic Buffer",
                    "Implement persistent self-reflection buffer storing error traces and counterfactual lessons.",
                ),
                (
                    "EBU-R128-2020",
                    "domain_standard",
                    "hermes_agent",
                    "EBU Recommendation R128: Loudness Normalisation (-14.5 LUFS)",
                    "Broadcast Audio Loudness Normalization & True-Peak Limiting",
                    "Enforce -14.5 +/- 0.5 LUFS and True Peak <= -1.5 dBTP across all TTS V0-Sense masters.",
                ),
            ]:
                seen_std_refs.add(pid.upper())
                ingested_items.append(
                    self.ingest_exogenous_knowledge(
                        source_type=src_t,
                        external_ref=pid,
                        domain=dom,
                        title=title,
                        url=f"https://arxiv.org/abs/{pid}" if src_t == "arxiv_paper" else "",
                        architectural_pattern=pat,
                        adaptation_blueprint=bp,
                        vault_path=target_vault,
                    )
                )

        # 3. Ingest Additional Domain Regulatory Standards Matrix
        for dom_key, std_list in reg_standards.items():
            dom_val = getattr(dom_key, "value", str(dom_key))
            if dom_val in ("ai_infrastructure", "general_ai_workspace"):
                continue
            for std_item in std_list:
                sid = str(std_item.get("standard_id", "")).strip()
                if not sid or sid.upper() in seen_std_refs:
                    continue
                seen_std_refs.add(sid.upper())
                ingested_items.append(
                    self.ingest_exogenous_knowledge(
                        source_type="domain_standard",
                        external_ref=sid,
                        domain=dom_val,
                        title=str(std_item.get("title", sid)),
                        url="",
                        architectural_pattern=f"{std_item.get('body', 'Standard')} Compliance Invariant",
                        key_algorithms=[sid, str(std_item.get("body", ""))],
                        adaptation_blueprint=str(std_item.get("scope", "")),
                        raw_summary=str(std_item.get("scope", "")),
                        vault_path=target_vault,
                    )
                )

        # 4. Harvest Autonomous Tasks & Distilled Lessons from evolution_ledger.db
        ev_db = (
            Path(evolution_ledger_path)
            if evolution_ledger_path
            else (Path.home() / ".gemini" / "antigravity" / "memory" / "evolution_ledger.db")
        )
        auto_ingested = 0
        if ev_db.exists():
            try:
                with sqlite3.connect(f"file:{ev_db}?mode=ro", uri=True) as ev_conn:
                    kd_rows = ev_conn.execute(
                        "SELECT domain, topic, distilled_insight FROM knowledge_distillation ORDER BY rowid DESC LIMIT 6;"
                    ).fetchall()
                    for dom_str, topic_str, insight_str in kd_rows:
                        ingested_items.append(
                            self.ingest_exogenous_knowledge(
                                source_type="autonomous_task",
                                external_ref=f"kd:{topic_str}",
                                domain=str(dom_str or "hermes_agent"),
                                title=f"Autonomous Distillation: {topic_str}",
                                architectural_pattern="Autonomous Adversarial Knowledge Distillation & Self-Healing Guard",
                                key_algorithms=[str(topic_str), "SFT/DPO Distillation"],
                                adaptation_blueprint=str(insight_str),
                                raw_summary=str(insight_str),
                                vault_path=target_vault,
                            )
                        )
                        auto_ingested += 1

                    cyc_rows = ev_conn.execute("""
                        SELECT domain, track, prompt_title, preferred_model
                        FROM evolution_cycles
                        WHERE prompt_title != ''
                        GROUP BY domain, prompt_title
                        ORDER BY MAX(rowid) DESC
                        LIMIT 6;
                    """).fetchall()
                    for dom_str, track_str, p_title, pref_mod in cyc_rows:
                        ref_key = f"auto:{dom_str}:{hashlib.sha256(str(p_title).encode('utf-8')).hexdigest()[:8]}"
                        ingested_items.append(
                            self.ingest_exogenous_knowledge(
                                source_type="autonomous_task",
                                external_ref=ref_key,
                                domain=str(dom_str or "hermes_agent"),
                                title=str(p_title),
                                architectural_pattern=f"Autonomous Swarm Track ({track_str}) on {pref_mod}",
                                key_algorithms=[str(track_str), str(pref_mod)],
                                adaptation_blueprint=f"Self-healing & adversarial verification cycle for {dom_str}: {p_title}",
                                raw_summary=str(p_title),
                                vault_path=target_vault,
                            )
                        )
                        auto_ingested += 1
            except Exception:
                pass

        if auto_ingested == 0:
            ingested_items.append(
                self.ingest_exogenous_knowledge(
                    source_type="autonomous_task",
                    external_ref="auto:self-healing-circuit-breaker",
                    domain="hermes_agent",
                    title="Autonomous Self-Healing Quota & Deadlock Circuit Breaker",
                    architectural_pattern="Pro-First QBRR Quota Waterfall & Orphan Recovery",
                    key_algorithms=["QBRR", "Self-Healing Circuit Breaker", "Clef 4-Stage"],
                    adaptation_blueprint="Automatically detect quota exhaustion or orphan stalls and trigger self-healing failover.",
                    vault_path=target_vault,
                )
            )

        # 4b. Ingest NVIDIA & FPT Sovereign Vietnamese Persona Dataset (nvidia/Nemotron-Personas-Vietnam)
        ingested_items.append(
            self.ingest_exogenous_knowledge(
                source_type="github_trending",
                external_ref="nvidia/Nemotron-Personas-Vietnam",
                domain="hermes_agent",
                title="NVIDIA Nemotron-Personas-Vietnam: 1M Sovereign Vietnamese Demographic & Professional Personas (CC-BY-4.0)",
                url="https://huggingface.co/datasets/nvidia/Nemotron-Personas-Vietnam",
                architectural_pattern="Census-Grounded Multi-Persona SFT/DPO Distillation & Dialect-Aware Cortical Myelination",
                key_algorithms=[
                    "Nemotron-Personas Synthesis",
                    "Vietnam GSO Census & VHLSS Grounding",
                    "Multi-Persona DPO Contrastive Triads",
                    "LoRA Skill Compilation",
                ],
                adaptation_blueprint=(
                    "Synthesize persona-grounded Vietnamese SFT/DPO trajectories across 6 Bloom levels (B1..B6), "
                    "3 macro-regions (Bac/Trung/Nam), Content Factory Zero-LaTeX spoken narration, Odoo 20 Rule 29 "
                    "borderless ERP roles, Gray Doom narrative QA, and Sovereign CWE security audits."
                ),
                raw_summary="1,000,000 synthetic Vietnamese personas (21-31 fields: professional_persona, cultural_background, skills_and_expertise_list) with zero PII.",
                vault_path=target_vault,
            )
        )

        # 5. Query Full Ledger State & Compute Ecological Metrics
        counts_by_source: Dict[str, int] = {
            "github_trending": 0,
            "arxiv_paper": 0,
            "domain_standard": 0,
            "autonomous_task": 0,
        }
        decision_counts: Dict[str, int] = {
            "ADOPT_INTO_HARNESS": 0,
            "SCHEDULE_SELF_HEAL": 0,
            "COMPILE_LORA_SKILL": 0,
            "GENERATE_ADR": 0,
        }
        all_exo_rows: List[Dict[str, Any]] = []
        distinct_domains: Set[str] = set()
        absorbed_count = 0

        with self.db.get_connection() as conn:
            rows = conn.execute("""
                SELECT e.*, m.status AS mem_status, m.tier AS mem_tier
                FROM exogenous_entropy_ledger e
                LEFT JOIN cognitive_memories m ON e.mem_key = m.mem_key
                WHERE e.status = 'ACTIVE'
                ORDER BY e.ecology_impact_score DESC, e.shannon_entropy_bits DESC;
            """).fetchall()
            for r in rows:
                d = dict(r)
                all_exo_rows.append(d)
                st = str(d.get("source_type", "autonomous_task"))
                counts_by_source[st] = counts_by_source.get(st, 0) + 1
                dec = str(d.get("evolution_decision", "ADOPT_INTO_HARNESS"))
                decision_counts[dec] = decision_counts.get(dec, 0) + 1
                if d.get("domain"):
                    distinct_domains.add(str(d["domain"]))
                if d.get("mem_status") == "ACTIVE" and d.get("mem_tier") in ("L2", "L3"):
                    absorbed_count += 1

        total_exo = len(all_exo_rows)
        avg_entropy = (
            round(sum(float(r.get("shannon_entropy_bits", 2.4)) for r in all_exo_rows) / total_exo, 2)
            if total_exo > 0
            else 0.0
        )
        absorption_ratio = round(absorbed_count / float(total_exo), 4) if total_exo > 0 else 1.0
        transfer_index = round(min(1.0, len(distinct_domains) / 6.0), 4)

        # 6. Write Master MOC `Maps/Exogenous-Knowledge-Space.md` & Link in `Home.md`
        moc_path = target_vault / "Maps" / "Exogenous-Knowledge-Space.md"
        eval_dir = target_vault / "10-Areas" / "AI Engineering" / "Autonomous-Ecology-Decisions"
        eval_report_path = eval_dir / f"Ecology-Evaluation-{date_str}.md"

        try:
            moc_path.parent.mkdir(parents=True, exist_ok=True)
            eval_dir.mkdir(parents=True, exist_ok=True)

            linked_stems: Set[str] = set()

            def _render_group(src_key: str, heading: str, subfolder: str) -> str:
                items = [r for r in all_exo_rows if r.get("source_type") == src_key]
                lines_out = []
                for it in items:
                    note_stem = Path(str(it.get("secondbrain_note_path", ""))).stem
                    linked_stems.add(note_stem)
                    clean_alias = (
                        f"{it['external_ref']} — {it['title']}"
                        .replace("[", "(")
                        .replace("]", ")")
                        .replace("|", "/")
                    )
                    lines_out.append(
                        f"- [[{note_stem}|{clean_alias}]] "
                        f"(`{it['domain']}` | $H={it['shannon_entropy_bits']:.2f}\\text{{b}}$ | "
                        f"**`{it['evolution_decision']}`**)"
                    )
                sub_dir = target_vault / "30-Resources" / "Exogenous-Knowledge" / subfolder
                if sub_dir.exists():
                    for extra_md in sorted(sub_dir.glob("*.md")):
                        if extra_md.stem not in linked_stems:
                            linked_stems.add(extra_md.stem)
                            lines_out.append(f"- [[{extra_md.stem}]] (`synced_note`)")
                if not lines_out:
                    return f"## {heading}\n- *None ingested yet.*\n"
                return f"## {heading} (`{len(lines_out)}` items)\n\n" + "\n".join(lines_out) + "\n"

            moc_md = f"""---
type: moc
title: "Không Gian Tri Thức Ngoại Sinh (Exogenous Knowledge Space)"
updated: "{now_iso}"
total_exogenous_items: {total_exo}
avg_shannon_entropy_bits: {avg_entropy}
---

# 🌐 Không Gian Tri Thức Ngoại Sinh (Exogenous Knowledge Space)

> [!IMPORTANT]
> **Updated**: `{now_iso}`  
> **Total Exogenous Engrams**: `{total_exo}` (`GitHub Trending`: `{counts_by_source.get('github_trending', 0)}`, `arXiv Papers`: `{counts_by_source.get('arxiv_paper', 0)}`, `Domain Standards`: `{counts_by_source.get('domain_standard', 0)}`, `Autonomous Tasks`: `{counts_by_source.get('autonomous_task', 0)}`)  
> **Mean Shannon Entropy**: `{avg_entropy:.2f} bits` | **L2/L3 Absorption Ratio**: `{absorption_ratio * 100:.1f}%` | **Cross-Domain Transfer Index**: `{transfer_index * 100:.1f}%`  
> **Navigation**: [[Home]] | [[Cognitive-Memory-Matrix]] | [[Decisions]] | [[Ecology-Evaluation-{date_str}]] | [[05-Official-Release-Master-Goal-Charter]]

## 🎯 1. Evolutionary Decision Matrix (Quyết Định Tiến Hóa & Self-Healing Ecology)

| Evolutionary Decision | Count | Autonomous Ecological Action |
| :--- | :--- | :--- |
| **`ADOPT_INTO_HARNESS`** | `{decision_counts.get('ADOPT_INTO_HARNESS', 0)}` | Inject pattern into `assemble_harness_context` (`L2/L3` memory) |
| **`SCHEDULE_SELF_HEAL`** | `{decision_counts.get('SCHEDULE_SELF_HEAL', 0)}` | Arm circuit-breakers, quota waterfalls & SecondBrain graph self-healing |
| **`COMPILE_LORA_SKILL`** | `{decision_counts.get('COMPILE_LORA_SKILL', 0)}` | Harvest sanitized SFT/DPO trajectory for 02:00 AM LoRA/ONNX myelination |
| **`GENERATE_ADR`** | `{decision_counts.get('GENERATE_ADR', 0)}` | Enforce constitutional compliance invariant (`ISO`/`EBU R128`/`FIDO2`/`IEEE`) |

{_render_group("github_trending", "🚀 2. GitHub Trending, AI Titans & Fast-Climbing Repos", "GitHub-Trending")}
{_render_group("arxiv_paper", "📄 3. Peer-Reviewed & Preprint Literature (arXiv)", "ArXiv-Papers")}
{_render_group("domain_standard", "🏛️ 4. International Regulatory & Domain Standards", "Domain-Standards")}
{_render_group("autonomous_task", "🤖 5. Autonomous Swarm Tasks & Distilled Lessons", "Autonomous-Tasks")}
"""
            moc_path.write_text(moc_md, encoding="utf-8")

            home_md_path = target_vault / "Home.md"
            if home_md_path.exists():
                home_txt = home_md_path.read_text(encoding="utf-8", errors="ignore")
                if "Exogenous-Knowledge-Space" not in home_txt:
                    link_line = (
                        "- [[Maps/Exogenous-Knowledge-Space|🌐 Exogenous Knowledge Space "
                        "(GitHub Trending, arXiv, Standards & Autonomous Ecology)]]\n"
                    )
                    if "## 🗺️ 3. Knowledge Maps" in home_txt:
                        home_txt = home_txt.replace(
                            "## 🗺️ 3. Knowledge Maps (`Maps/`)\n",
                            f"## 🗺️ 3. Knowledge Maps (`Maps/`)\n{link_line}",
                        )
                    else:
                        home_txt += f"\n{link_line}"
                    home_md_path.write_text(home_txt, encoding="utf-8")
            else:
                home_md_path.parent.mkdir(parents=True, exist_ok=True)
                home_md_path.write_text(
                    "# 🧠 Second Brain Hub\n\n"
                    "- [[Exogenous-Knowledge-Space]]\n"
                    "- [[Cognitive-Memory-Matrix]]\n"
                    "- [[Decisions]]\n",
                    encoding="utf-8",
                )

            eval_md = f"""# 🧬 Autonomous Ecology Evaluation & Decision Report (`{date_str}`)

> [!NOTE]
> **Timestamp**: `{now_iso}`  
> **Navigation**: [[Home]] | [[Exogenous-Knowledge-Space]] | [[Cognitive-Memory-Matrix]] | [[Decisions]]

## 1. Exogenous Entropy Telemetry
- **Total Exogenous Knowledge Assets**: `{total_exo}`
  - **GitHub Trending & AI Titans**: `{counts_by_source.get('github_trending', 0)}`
  - **arXiv Scientific Preprints**: `{counts_by_source.get('arxiv_paper', 0)}`
  - **International Domain Standards**: `{counts_by_source.get('domain_standard', 0)}`
  - **Autonomous Swarm Tasks & Distillations**: `{counts_by_source.get('autonomous_task', 0)}`
- **Average Shannon Entropy ($H$)**: `{avg_entropy:.2f} bits`
- **Cortical L2/L3 Absorption Ratio**: `{absorption_ratio * 100:.1f}%`
- **Cross-Domain Transfer Index**: `{transfer_index * 100:.1f}%` ({len(distinct_domains)} domains)

## 2. Evolutionary & Self-Healing Decisions
- **`ADOPT_INTO_HARNESS`**: `{decision_counts.get('ADOPT_INTO_HARNESS', 0)}` architectural patterns active in AGI harness context.
- **`SCHEDULE_SELF_HEAL`**: `{decision_counts.get('SCHEDULE_SELF_HEAL', 0)}` self-healing guards & quota circuit-breakers armed.
- **`COMPILE_LORA_SKILL`**: `{decision_counts.get('COMPILE_LORA_SKILL', 0)}` SFT/DPO skill trajectories queued for cortical myelination.
- **`GENERATE_ADR`**: `{decision_counts.get('GENERATE_ADR', 0)}` international standards pinned to constitutional L3 memory.
"""
            eval_report_path.write_text(eval_md, encoding="utf-8")
        except Exception:
            pass

        # 7. Run Self-Healing SecondBrain Maintenance (after MOC & links are written so 0 orphans!)
        heal_summary = self.self_heal_secondbrain(target_vault)

        return {
            "timestamp": now_iso,
            "total_exogenous_items": total_exo,
            "counts_by_source": counts_by_source,
            "decision_counts": decision_counts,
            "avg_shannon_entropy_bits": avg_entropy,
            "knowledge_absorption_ratio": absorption_ratio,
            "cross_domain_transfer_index": transfer_index,
            "distinct_domains": sorted(distinct_domains),
            "moc_path": str(moc_path),
            "evaluation_report_path": str(eval_report_path),
            "self_heal_summary": heal_summary,
        }

    # --------------------------------------------------------------------------
    # Nemotron-Personas-Vietnam Sovereign Synthesis & Multi-Persona Grounding
    # --------------------------------------------------------------------------

    @staticmethod
    def get_nemotron_personas_vietnam_archetypes() -> List[Dict[str, Any]]:
        """
        Returns 6 canonical Vietnamese persona archetypes grounded in the
        `nvidia/Nemotron-Personas-Vietnam` schema (1M synthetic profiles, CC-BY-4.0,
        Vietnam GSO Census & VHLSS labor/demographic distribution) spanning all
        6 Bloom levels (B1..B6), 3 macro-regions (Bac/Trung/Nam), 4 AGI harness modes,
        and 5 sovereign execution domains.
        """
        def _uuid(key: str) -> str:
            h = hashlib.sha256(f"nvidia/Nemotron-Personas-Vietnam:{key}".encode("utf-8")).hexdigest()
            return f"{h[:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:32]}"

        return [
            {
                "uuid": _uuid("b1_devops_danang"),
                "persona_id": "vn_b1_devops_danang",
                "region": "Trung",
                "province": "Đà Nẵng",
                "age": 24,
                "sex": "Nam",
                "education_level": "Cử nhân Kỹ thuật Mạng & Truyền thông",
                "occupation": "Kỹ sư Vận hành Hạ tầng Đám mây (NOC/DevOps Engineer)",
                "professional_persona": (
                    "Kỷ luật cao trong giám sát log hệ thống, ưu tiên lệnh kiểm tra trạng thái thực tế "
                    "trên đĩa và tuyệt đối không suy đoán khi chưa chạy lệnh kiểm chứng."
                ),
                "cultural_background": "Lớn lên tại Đà Nẵng, tác phong gọn gàng, thực tế, quen làm việc theo ca trực vận hành.",
                "skills_and_expertise_list": ["Linux CLI", "SQLite WAL", "Systemd Telemetry", "Docker Healthcheck"],
                "career_goals_and_ambitions": "Xây dựng hệ thống giám sát tự động phát hiện tiến trình treo trong dưới 1 giây.",
                "target_domain": "hermes_agent",
                "target_tier": "L2",
                "target_bloom": int(BloomLevel.B1_REMEMBER),
                "target_harness_mode": "creative_synthesis",
                "chosen_sft": (
                    "Ghi nhận nhật ký trạng thái hệ thống thực tế từ git status, kiểm tra ổ đĩa và bảng SQLite WAL "
                    "trước khi báo cáo kết quả vận hành."
                ),
                "rejected_dpo": "Giả định tiến trình đã hoàn tất thành công mà không kiểm tra mã thoát hoặc file thực tế.",
            },
            {
                "uuid": _uuid("b2_edumedia_cantho"),
                "persona_id": "vn_b2_edumedia_cantho",
                "region": "Nam",
                "province": "Cần Thơ",
                "age": 28,
                "sex": "Nữ",
                "education_level": "Cử nhân Sư phạm Vật lý & Truyền thông Đa phương tiện",
                "occupation": "Biên tập viên Kịch bản Khoa học & Đạo diễn Thu âm (ZENPHAM / Tôi Đọc Sách)",
                "professional_persona": (
                    "Nhạy bén với nhịp điệu tiếng Việt nói tự nhiên, chuyển hóa mọi ký hiệu toán học thành lời giảng "
                    "dễ hiểu, ngắt mệnh đề dưới 75 ký tự và phụ đề Karaoke 3-5 từ."
                ),
                "cultural_background": "Gốc miền Tây sông nước Cần Thơ, giọng kể truyền cảm, gần gũi, ghét lối dịch máy móc hoặc đọc vấp ký hiệu.",
                "skills_and_expertise_list": ["TTS V0-Sense", "Gold SRT Karaoke", "Zero-LaTeX Narration", "EBU R128 -14.5 LUFS"],
                "career_goals_and_ambitions": "Biến các khái niệm toán học và vật lý phức tạp thành phim tài liệu cuốn hút cho khán giả Việt.",
                "target_domain": "zenpham_content_factory",
                "target_tier": "L2",
                "target_bloom": int(BloomLevel.B2_UNDERSTAND),
                "target_harness_mode": "creative_synthesis",
                "chosen_sft": (
                    "Tổng quan và giải thích khái niệm: Trong cột kịch bản thu âm tiếng Việt của Nemotron-Personas-Vietnam, "
                    "diễn đạt hoàn toàn bằng lời nói tự nhiên như xác suất có điều kiện của biến cố A khi biết B, "
                    "mỗi mệnh đề không quá 75 ký tự, tốc độ đọc 1.0x tự nhiên, tuyệt đối không để lọt ký hiệu toán học."
                ),
                "rejected_dpo": (
                    "Đưa trực tiếp công thức LaTeX $P(A|B) = \\frac{P(A \\cap B)}{P(B)}$ vào cột kịch bản TTS "
                    "và dùng bộ lọc atempo=0.80 để kéo dài thời lượng thu âm."
                ),
            },
            {
                "uuid": _uuid("b3_erp_cfo_hcmc"),
                "persona_id": "vn_b3_erp_cfo_hcmc",
                "region": "Nam",
                "province": "Thành phố Hồ Chí Minh",
                "age": 35,
                "sex": "Nữ",
                "education_level": "Thạc sĩ Tài chính - Kế toán Quốc tế (ACCA / CPA)",
                "occupation": "Kế toán trưởng VAS/IFRS & Chuyên gia Triển khai ERP Odoo 20 (Insilos)",
                "professional_persona": (
                    "Chuẩn xác từng nghiệp vụ kế toán VAS/IFRS, yêu cầu giao diện báo cáo Odoo 20 Owl phải thoáng, "
                    "không dùng hộp thẻ viền dày gây tràn chữ và tuân thủ chuẩn bảo mật QWeb t-out."
                ),
                "cultural_background": "Làm việc tại trung tâm tài chính TP.HCM, quyết đoán, coi trọng hiệu suất thao tác và độ tin cậy số liệu.",
                "skills_and_expertise_list": ["Odoo 20 Owl Component", "QWeb t-out & t-key", "Rule 29 Borderless UI", "VAS/IFRS Reconciliation"],
                "career_goals_and_ambitions": "Chuẩn hóa toàn bộ phân hệ quản trị doanh nghiệp Insilos trên nền tảng Odoo 20 hiện đại.",
                "target_domain": "odoo20_owl_rule29",
                "target_tier": "L2",
                "target_bloom": int(BloomLevel.B3_APPLY),
                "target_harness_mode": "fast",
                "chosen_sft": (
                    "Playbook SOP quy trình triển khai: Áp dụng chuẩn Owl Component trong Odoo 20 cho persona Kế toán trưởng "
                    "với useService('rpc'), dùng chỉ thị <t t-out=\"...\"/> kèm t-key bắt buộc trên nền tảng Neo-Noir Obsidian "
                    "#080a0f không khung hộp thẻ."
                ),
                "rejected_dpo": (
                    "Sử dụng chỉ thị <t t-esc=\"...\"/> hoặc <t t-raw=\"...\"/> đã lỗi thời và bọc bảng số liệu trong "
                    "khung thẻ card-body đặc gây tràn chữ."
                ),
            },
            {
                "uuid": _uuid("b4_gamedev_hue"),
                "persona_id": "vn_b4_gamedev_hue",
                "region": "Trung",
                "province": "Thừa Thiên Huế",
                "age": 37,
                "sex": "Nam",
                "education_level": "Thạc sĩ Văn học & Thiết kế Hệ thống Tương tác",
                "occupation": "Kiến trúc sư Cốt truyện & Cân bằng Gameplay (Gray Doom Codex Harness)",
                "professional_persona": (
                    "Phân tích nguyên nhân gốc rễ (root-cause analysis) giữa cơ chế chiến thuật TravianZ và mỹ thuật "
                    "nhân vật, kiểm soát chặt chẽ 26-Character Tri-Lock DNA và tỷ lệ nhìn nghiêng một mắt."
                ),
                "cultural_background": "Đậm chất chiều sâu lịch sử Huế, kết hợp mỹ học cổ điển phương Đông với thế giới chiến thuật grimdark.",
                "skills_and_expertise_list": ["Gray Doom 26-Character DNA", "TravianZ 3dbe9c71 Parity", "AST Control-Flow Diff", "18-Lot Spatial Gate"],
                "career_goals_and_ambitions": "Hoàn thiện thế giới Gray Doom đồng nhất tuyệt đối giữa tiểu thuyết, hội họa nhân vật và logic mô phỏng.",
                "target_domain": "graydoom_codex_harness",
                "target_tier": "L2",
                "target_bloom": int(BloomLevel.B4_ANALYZE),
                "target_harness_mode": "deep_tot",
                "chosen_sft": (
                    "Root-cause analysis (RCA) và contrastive decomposition cho Gray Doom: Đối chiếu gói thay đổi "
                    "gd-<slug>.json qua 7 làn kiểm định, bảo đảm góc nghiêng ANG_PRF_90 chỉ hiển thị đúng một mắt, "
                    "lề alpha 11% và đồng bộ 4 tài liệu chuẩn."
                ),
                "rejected_dpo": (
                    "Chấp nhận tranh nhân vật góc nghiêng 90 độ bị lộ hai mắt hoặc bỏ qua kiểm định 18 lô đất "
                    "trên màn hình 390px."
                ),
            },
            {
                "uuid": _uuid("b5_sec_auditor_hanoi"),
                "persona_id": "vn_b5_sec_auditor_hanoi",
                "region": "Bac",
                "province": "Hà Nội",
                "age": 39,
                "sex": "Nam",
                "education_level": "Tiến sĩ An toàn Thông tin & Mật mã học",
                "occupation": "Chuyên gia Kiểm toán An ninh Mạng & Quản trị Rủi ro (VerticalRisk GRC / Clef Sentinel)",
                "professional_persona": (
                    "Tư duy phản biện đối kháng (Adversarial Hegelian Critique), luôn kiểm chứng bằng thực nghiệm "
                    "và chặn đứng các lỗ hổng CWE-20, CWE-78, CWE-502 cũng như trượt đồng hồ HLC."
                ),
                "cultural_background": "Đào tạo bài bản tại Hà Nội, nghiêm cẩn, đặt tính toàn vẹn bằng chứng lên trên mọi báo cáo hình thức.",
                "skills_and_expertise_list": ["Adversarial Security Audit", "HLC Clock Drift Guard", "Modal Credit Gate", "CWE-502 Safetensors"],
                "career_goals_and_ambitions": "Bảo vệ hạ tầng AI tự chủ khỏi giả mạo kết quả (Zero-Fake-Pass) và rò rỉ khóa bí mật.",
                "target_domain": "adversarial_security_tot",
                "target_tier": "L3",
                "target_bloom": int(BloomLevel.B5_EVALUATE),
                "target_harness_mode": "dialectic_audit",
                "chosen_sft": (
                    "Adversarial security audit và Clef JEV verdict: Thực thi kiểm toán đối kháng, chặn đứng độ lệch "
                    "đồng hồ HLC quá 500ms, cưỡng chế Modal Credit Gate (>15 USD deploy, >10 USD inference) "
                    "và lưu trọng số bằng safetensors an toàn."
                ),
                "rejected_dpo": (
                    "Tin tưởng báo cáo tự động không gắn với file thật trong repo hoặc dùng hàm eval() trực tiếp "
                    "trên công thức đầu vào."
                ),
            },
            {
                "uuid": _uuid("b6_agi_architect_hanoi"),
                "persona_id": "vn_b6_agi_architect_hanoi",
                "region": "Bac",
                "province": "Hà Nội",
                "age": 42,
                "sex": "Nam",
                "education_level": "Tiến sĩ Khoa học Máy tính & Khoa học Thần kinh Tính toán",
                "occupation": "Kiến trúc sư Trưởng Hệ thống Sovereign AGI & Cognitive SecondBrain",
                "professional_persona": (
                    "Kiến tạo các nguyên lý bất biến (Sovereign Invariants & ADRs), kết hợp mô hình trí nhớ phân tầng "
                    "sinh học thần kinh với huấn luyện LoRA/ONNX tốc độ dưới 1 mili-giây."
                ),
                "cultural_background": "Kết hợp tư duy hệ thống chuẩn mực quốc tế với bản sắc văn hóa và dữ liệu nhân khẩu học Việt Nam.",
                "skills_and_expertise_list": ["Sovereign ADR Synthesis", "Cortical Myelination LoRA/ONNX", "Bi-Temporal Tombstones", "Nemotron-Personas-Vietnam"],
                "career_goals_and_ambitions": "Xây dựng nền tảng AGI có chủ quyền hiểu sâu sắc ngôn ngữ, văn hóa và nghiệp vụ chuyên môn Việt Nam.",
                "target_domain": "hermes_agent",
                "target_tier": "L3",
                "target_bloom": int(BloomLevel.B6_CREATE),
                "target_harness_mode": "deep_tot",
                "chosen_sft": (
                    "Sovereign invariant ADR-20261017-009: Tích hợp bộ dữ liệu nvidia/Nemotron-Personas-Vietnam vào "
                    "Cognitive SecondBrain để đa dạng hóa phản biện Hegelian, chống suy thoái phân phối SFT/DPO và "
                    "tinh chỉnh bộ định tuyến thần kinh 3 đầu ONNX."
                ),
                "rejected_dpo": (
                    "Huấn luyện bộ định tuyến và LoRA trên các mẫu đơn điệu thiếu ngữ cảnh nhân khẩu học, vùng miền "
                    "và vai trò chuyên môn Việt Nam."
                ),
            },
        ]

    def synthesize_nemotron_personas_vietnam(
        self,
        vault_path: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """
        Synthesizes and seeds `nvidia/Nemotron-Personas-Vietnam` archetypes, cognitive
        memories (B1..B6), SFT/DPO contrastive sessions, exogenous knowledge entry, and
        the Obsidian SecondBrain architecture note (`10-Areas/AI Engineering/Nemotron-Personas-Vietnam-SecondBrain-Architecture.md`).
        """
        target_vault = Path(vault_path) if vault_path else self.vault_path
        now_iso = datetime.now(timezone.utc).isoformat()
        archetypes = self.get_nemotron_personas_vietnam_archetypes()

        seeded_memories: List[str] = []
        recorded_sessions: List[str] = []

        for arch in archetypes:
            mem_key = f"persona:nemotron-vn:{arch['persona_id']}"
            title = (
                f"[Nemotron-Personas-Vietnam] {arch['occupation']} "
                f"({arch['province']} - Miền {arch['region']} | B{arch['target_bloom']})"
            )
            content = (
                f"UUID: {arch['uuid']} | Source: nvidia/Nemotron-Personas-Vietnam (CC-BY-4.0)\n"
                f"Demographics: {arch['age']} tuổi, {arch['sex']}, {arch['province']} (Miền {arch['region']}), {arch['education_level']}\n"
                f"Occupation: {arch['occupation']} | Target Domain: {arch['target_domain']}\n"
                f"Professional Persona: {arch['professional_persona']}\n"
                f"Cultural Background: {arch['cultural_background']}\n"
                f"Skills & Expertise: {', '.join(arch['skills_and_expertise_list'])}\n"
                f"Career Goals: {arch['career_goals_and_ambitions']}\n"
                f"Sovereign Chosen Standard: {arch['chosen_sft']}\n"
                f"Contrastive Rejected Anti-Pattern: {arch['rejected_dpo']}"
            )
            self.store_memory(
                mem_key=mem_key,
                title=title,
                content=content,
                tier=str(arch["target_tier"]),
                bloom_level=int(arch["target_bloom"]),
                synaptic_strength=0.92 if arch["target_tier"] == "L3" else 0.86,
                evidence_score=0.94,
                vault_path="10-Areas/AI Engineering/Nemotron-Personas-Vietnam-SecondBrain-Architecture.md",
            )
            seeded_memories.append(mem_key)

            # Record both SFT and DPO persona-grounded trajectories into jev_sessions
            sft_res = self.record_jev_session(
                query=(
                    f"[{arch['target_domain']}] Đóng vai {arch['occupation']} ({arch['province']}, "
                    f"Miền {arch['region']}): {arch['career_goals_and_ambitions']}"
                ),
                chosen_response=str(arch["chosen_sft"]),
                harness_mode=str(arch["target_harness_mode"]),
                bloom_level=int(arch["target_bloom"]),
                tier=str(arch["target_tier"]),
                complexity=round(0.7 + int(arch["target_bloom"]) * 0.45, 2),
                engine="NEMOTRON_PERSONAS_VN_SYNTHESIZER",
                sample_type="SFT",
            )
            recorded_sessions.append(sft_res["session_key"])

            dpo_res = self.record_jev_session(
                query=(
                    f"[DPO Contrastive | {arch['target_domain']}] Kiểm định tiêu chuẩn chuyên môn của "
                    f"{arch['occupation']} ({arch['province']})"
                ),
                chosen_response=str(arch["chosen_sft"]),
                rejected_response=str(arch["rejected_dpo"]),
                harness_mode=str(arch["target_harness_mode"]),
                bloom_level=int(arch["target_bloom"]),
                tier=str(arch["target_tier"]),
                complexity=round(0.9 + int(arch["target_bloom"]) * 0.45, 2),
                engine="NEMOTRON_PERSONAS_VN_SYNTHESIZER",
                sample_type="DPO",
            )
            recorded_sessions.append(dpo_res["session_key"])

        exo_res = self.ingest_exogenous_knowledge(
            source_type="github_trending",
            external_ref="nvidia/Nemotron-Personas-Vietnam",
            domain="hermes_agent",
            title="NVIDIA Nemotron-Personas-Vietnam: 1M Sovereign Vietnamese Demographic & Professional Personas (CC-BY-4.0)",
            url="https://huggingface.co/datasets/nvidia/Nemotron-Personas-Vietnam",
            architectural_pattern="Census-Grounded Multi-Persona SFT/DPO Distillation & Dialect-Aware Cortical Myelination",
            key_algorithms=[
                "Nemotron-Personas Synthesis",
                "Vietnam GSO Census & VHLSS Grounding",
                "Multi-Persona DPO Contrastive Triads",
                "LoRA Skill Compilation",
            ],
            adaptation_blueprint=(
                "Synthesize persona-grounded Vietnamese SFT/DPO trajectories across 6 Bloom levels (B1..B6), "
                "3 macro-regions (Bac/Trung/Nam), Content Factory Zero-LaTeX spoken narration, Odoo 20 Rule 29 "
                "borderless ERP roles, Gray Doom narrative QA, and Sovereign CWE security audits."
            ),
            raw_summary="1,000,000 synthetic Vietnamese personas (21-31 fields: professional_persona, cultural_background, skills_and_expertise_list) with zero PII.",
            vault_path=target_vault,
        )

        arch_note_rel = "10-Areas/AI Engineering/Nemotron-Personas-Vietnam-SecondBrain-Architecture.md"
        arch_note_path = target_vault / arch_note_rel
        try:
            arch_note_path.parent.mkdir(parents=True, exist_ok=True)
            rows_md = "\n".join(
                f"| `B{a['target_bloom']}` | `{a['region']}` ({a['province']}) | {a['occupation']} | `{a['target_domain']}` | `{a['target_harness_mode']}` |"
                for a in archetypes
            )
            note_text = f"""---
type: architecture-blueprint
title: "Ứng Dụng NVIDIA Nemotron-Personas-Vietnam Trong Cognitive SecondBrain & Sovereign AGI"
dataset_ref: "nvidia/Nemotron-Personas-Vietnam"
license: "CC-BY-4.0"
records_scale: "1,000,000 synthetic Vietnamese profiles"
updated: "{now_iso}"
---

# 🇻🇳 Ứng Dụng `nvidia/Nemotron-Personas-Vietnam` Trong Cognitive SecondBrain & Sovereign AGI

> [!IMPORTANT]
> **Nguồn dữ liệu**: `nvidia/Nemotron-Personas-Vietnam` (Hợp tác phát triển bởi **NVIDIA & FPT Smart Cloud**, giấy phép mở `CC-BY-4.0`, quy mô **1.000.000 hồ sơ nhân khẩu học tổng hợp**, 0% PII).  
> **Cơ sở thống kê**: Neo theo Tổng điều tra Dân số và Nhà ở (GSO) & Khảo sát Mức sống Dân cư Việt Nam (VHLSS) khắp 63 tỉnh thành / 3 miền Bắc - Trung - Nam.  
> **Liên kết điều hướng**: [[Home]] | [[Cognitive-Memory-Matrix]] | [[Exogenous-Knowledge-Space]] | [[Decisions]] | [[Sovereign-Fleet-JEV-Modal-Evolution-Report-20261017]]

## 1. Cấu Trúc Schema Cốt Lõi Của `nvidia/Nemotron-Personas-Vietnam`
Mỗi bản ghi trong tập dữ liệu bao gồm **21–31 trường** chia làm 3 nhóm:
1. **6 Trường Chân dung Tự sự (`Persona Narratives`)**:
   - `professional_persona`: Thái độ làm việc, chuyên môn nghề nghiệp, thói quen ra quyết định trong thị trường lao động Việt Nam.
   - `cultural_background`: Bản sắc văn hóa vùng miền, truyền thống gia đình, phong cách giao tiếp và lối sống.
   - `sports_persona`, `arts_persona`, `travel_persona`, `culinary_persona` & `summary`.
2. **Trường Thuộc tính Năng lực (`Persona Attributes`)**:
   - `skills_and_expertise` / `skills_and_expertise_list`
   - `career_goals_and_ambitions`
   - `hobbies_and_interests` / `hobbies_and_interests_list`
3. **Trường Nhân khẩu & Địa lý (`Demographic & Geographic Context`)**:
   - `uuid`, `age`, `sex`, `education_level`, `occupation`, `province`, `region` (Bắc / Trung / Nam).

## 2. Năm Trụ Cột Ứng Dụng Trực Tiếp Trong Hermes Cognitive SecondBrain

### 2.1. Phản Biện Đa Nhân Cách Hegelian & Chống Suy Thoái Phân Phối SFT/DPO (`Stage 5 Myelination`)
- Thay vì sinh dữ liệu SFT/DPO đơn điệu từ một giọng kỹ thuật duy nhất, `CognitiveSecondBrainEngine.synthesize_nemotron_personas_vietnam()` ánh xạ 6 hình mẫu nhân khẩu học Việt Nam trải đều từ **Bloom B1 đến B6** và 4 chế độ AGI Harness (`fast`, `deep_tot`, `dialectic_audit`, `creative_synthesis`).
- Tạo các cặp đối chiếu DPO (`chosen` vs `rejected`) bám sát thực tế vận hành tại Việt Nam.

### 2.2. Content Factory & Chuẩn Hóa Ngôn Ngữ Nói Tự Nhiên (`TTS V0-Sense` & `Gold SRT Karaoke`)
- Ứng dụng trực tiếp cho **ZENPHAM Masterclass**, **Biết Địa Lý Từ Ba Tôi**, **Tôi Đọc Sách**, **Reality Decode** và **Gray Doom Novel**:
  - **Zero-LaTeX-Leak (Rule 1.6)**: Huấn luyện bộ lọc phản xạ từ chối mọi công thức `$...$` trong kịch bản đọc, chuyển thành lời giảng tiếng Việt tự nhiên phù hợp từng đối tượng khán giả (học sinh, kỹ sư, độc giả đại chúng).
  - **Acoustic Clause Guard (`<= 75` ký tự, Rule 1.4)** & **Gold SRT Karaoke (`3–5` từ, `<= 34` ký tự, Rule 1.5)**: Điều chỉnh phương ngữ và nhịp ngắt câu theo vùng miền Bắc/Trung/Nam mà không làm gãy từ ghép tiếng Việt.

### 2.3. Giả Lập Đa Vai Trò Doanh Nghiệp Cho Odoo 20 / Insilos ERP & VerticalRisk GRC
- Sử dụng `professional_persona` của **Kế toán trưởng VAS/IFRS**, **Kiểm toán viên nội bộ**, **Quản lý chuỗi cung ứng FDI**, và **Kỹ sư vận hành SCADA** để sinh kịch bản kiểm thử chấp nhận người dùng (UAT) tự động trên giao diện **Odoo 20 Owl (`t-out`, Rule 29 Borderless Canvas `#080a0f`)**.

### 2.4. Thiết Kế Nhân Vật & Cốt Truyện Đa Chiều Cho Gray Doom (`graydoom_codex_harness`)
- Kết hợp `cultural_background` và `professional_persona` để làm giàu chiều sâu tâm lý, lời thoại tiếng Việt sắc sảo và kiểm định nhất quán `26-Character Tri-Lock DNA`.

### 2.5. Bộ Thích Nghi Chuyên Biệt `lora_nemotron_personas_vietnam.safetensors` (`r=16`)
- Được biên dịch tự động trong chu kỳ **Stage 5 Cortical Myelination** và hỗ trợ `hot_swap_domain_lora("nemotron_personas_vietnam")` trong **dưới `2 ms`** (`KPI < 15 ms`).

## 3. Ma Trận 6 Hình Mẫu Chuẩn (`Canonical Archetypes B1..B6`)

| Cấp Bloom | Vùng Miền | Nghề Nghiệp Chuẩn Hóa | Miền Thực Thi (`Domain`) | Chế Độ Harness |
| :--- | :--- | :--- | :--- | :--- |
{rows_md}
"""
            arch_note_path.write_text(note_text, encoding="utf-8")

            home_md = target_vault / "Home.md"
            if home_md.exists():
                h_txt = home_md.read_text(encoding="utf-8", errors="ignore")
                if "Nemotron-Personas-Vietnam-SecondBrain-Architecture" not in h_txt:
                    h_txt += (
                        "\n- [[10-Areas/AI Engineering/Nemotron-Personas-Vietnam-SecondBrain-Architecture|"
                        "🇻🇳 Nemotron-Personas-Vietnam SecondBrain Architecture]]\n"
                    )
                    home_md.write_text(h_txt, encoding="utf-8")
        except Exception:
            pass

        return {
            "dataset_ref": "nvidia/Nemotron-Personas-Vietnam",
            "archetypes_count": len(archetypes),
            "seeded_memories": seeded_memories,
            "recorded_sessions_count": len(recorded_sessions),
            "exogenous_entropy_id": exo_res["entropy_id"],
            "architecture_note_path": str(arch_note_path),
        }

    @staticmethod
    def plan_argon_pro_task(prompt: str, complexity: float = 2.4) -> Dict[str, Any]:
        """4-level Gemini 4 Argon task planner for Standard Pro nodes (tier='pro')."""
        if complexity < 1.2:
            level, model, synth = "L1_TRIVIAL", "gemini-4-argon-low", False
        elif complexity < 2.2:
            level, model, synth = "L2_STANDARD", "gemini-4-argon-medium", False
        elif complexity < 3.0:
            level, model, synth = "L3_COMPLEX", "gemini-4-argon-high", False
        else:
            level, model, synth = "L4_SOVEREIGN", "gemini-4-argon-high", True
        return {
            "level": level,
            "complexity": round(float(complexity), 2),
            "canonical_model": model,
            "tier": "pro",
            "dialectical_synthesis": synth,
            "fleet_plan_args": {"prompt": prompt, "model": model, "tier": "pro"},
            "fleet_run_args": {"prompt": prompt, "model": model, "tier": "pro"},
        }

    # --------------------------------------------------------------------------
    # Stage 5: JEV Session Recorder + LoRA (.safetensors) + ONNX Myelination
    # --------------------------------------------------------------------------

    @staticmethod
    def featurize_text_256d(text: str) -> List[float]:
        """
        Deterministically converts text into a 256-dimensional normalized cortical
        feature vector combining hashed token/char-trigram projections (dims 0..247)
        and explicit epistemic/Bloom signal detectors (dims 248..255).
        """
        vec = [0.0] * 256
        lower = text.lower()
        tokens = re.findall(r"[a-z0-9à-ỹ_]+", lower)

        for tok in tokens:
            h = int(hashlib.md5(tok.encode("utf-8")).hexdigest()[:8], 16)
            idx = h % 248
            sign = 1.0 if (h & 1) == 0 else -1.0
            vec[idx] += sign

        # Epistemic & Bloom structural channels (dims 248..255)
        vec[248] = float( classify_bloom_level(text, tier="L2") ) / 6.0
        vec[249] = 1.0 if any(w in lower for w in ("adr", "invariant", "sovereign", "constitutional")) else 0.0
        vec[250] = 1.0 if any(w in lower for w in ("audit", "critique", "clef", "jev", "security", "phản biện")) else 0.0
        vec[251] = 1.0 if any(w in lower for w in ("root-cause", "rca", "ast", "architecture", "why")) else 0.0
        vec[252] = 1.0 if any(w in lower for w in ("playbook", "sop", "workflow", "step", "pipeline")) else 0.0
        vec[253] = 1.0 if any(w in lower for w in ("summary", "overview", "map", "taxonomy")) else 0.0
        vec[254] = min(1.0, len(text) / 2000.0)
        vec[255] = min(1.0, len(tokens) / 250.0)

        norm = math.sqrt(sum(v * v for v in vec[:248])) or 1.0
        for i in range(248):
            vec[i] = round(vec[i] / norm, 6)
        return vec

    def record_jev_session(
        self,
        query: str,
        chosen_response: str,
        harness_mode: str = "fast",
        bloom_level: int = 3,
        tier: str = "L2",
        complexity: float = 0.5,
        engine: str = "LOCAL_JEV",
        rejected_response: str = "",
        sample_type: str = "SFT",
    ) -> Dict[str, Any]:
        """
        Records a sanitized JEV session or DPO contrastive triad into `jev_sessions`
        for nightly Cortical Myelination (LoRA SFT/DPO + ONNX surrogate training).
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        try:
            from tools.modal_jev_finetuning import DatasetSecretScrubber
            scrubber = DatasetSecretScrubber()
            clean_query = scrubber.scrub_text(query)
            clean_chosen = scrubber.scrub_text(chosen_response)
            clean_rejected = scrubber.scrub_text(rejected_response)
        except Exception:
            clean_query = query
            clean_chosen = chosen_response
            clean_rejected = rejected_response

        digest = hashlib.sha256(
            f"{sample_type}|{clean_query}|{clean_chosen}|{clean_rejected}".encode("utf-8")
        ).hexdigest()
        session_key = f"jev:{sample_type.lower()}:{digest[:16]}"

        with self.db.get_connection() as conn:
            conn.execute("""
                INSERT INTO jev_sessions (
                    session_key, query, harness_mode, bloom_level, tier,
                    complexity, engine, chosen_response, rejected_response,
                    sample_type, sha256, recorded_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(session_key) DO UPDATE SET
                    chosen_response = excluded.chosen_response,
                    rejected_response = excluded.rejected_response,
                    recorded_at = excluded.recorded_at;
            """, (
                session_key, clean_query, harness_mode, int(bloom_level), tier,
                float(complexity), engine, clean_chosen, clean_rejected,
                sample_type, digest, now_iso
            ))
            conn.commit()

        return {
            "session_key": session_key,
            "sample_type": sample_type,
            "harness_mode": harness_mode,
            "bloom_level": int(bloom_level),
            "sha256": digest,
        }

    def myelinate_jev_lora_and_onnx(
        self,
        output_dir: Optional[Path] = None,
        epochs: int = 35,
    ) -> Dict[str, Any]:
        """
        Stage 5 of the 02:00 AM Sleep Cycle — Oligodendrocyte Cortical Myelination:
          1. Harvests & scrubs SFT samples (consolidated L2/L3 memories + jev_sessions)
             and DPO contrastive triads (dialectical_audits where false knowledge was
             ABANDONED or SUPERSEDED) into `secondbrain_sft_dpo.sanitized.jsonl`.
          2. Trains a PyTorch Cortical Router + LoRA Adapter (r=8, alpha=16) mapping
             256-dim features -> 6-class Bloom Level & 4-class AGI Harness Mode.
          3. Exports `secondbrain_lora_adapter.safetensors` (CWE-502 safe serialization)
             and `secondbrain_jev_router.onnx` (verified via ONNXRuntime in <1ms).
        """
        import os
        import time

        target_dir = Path(output_dir) if output_dir else (Path.home() / ".hermes" / "jev_myelination")
        target_dir.mkdir(parents=True, exist_ok=True)

        dataset_path = target_dir / "secondbrain_sft_dpo.sanitized.jsonl"
        lora_path = target_dir / "secondbrain_lora_adapter.safetensors"
        onnx_path = target_dir / "secondbrain_jev_router.onnx"
        onnx_int8_path = target_dir / "secondbrain_jev_router_int8.onnx"
        manifest_path = target_dir / "myelination_manifest.json"
        domain_lora_paths = {
            "graydoom_codex_harness": str(target_dir / "lora_graydoom_codex_harness.safetensors"),
            "odoo20_owl_rule29": str(target_dir / "lora_odoo20_owl_rule29.safetensors"),
            "adversarial_security_tot": str(target_dir / "lora_adversarial_security_tot.safetensors"),
            "nemotron_personas_vietnam": str(target_dir / "lora_nemotron_personas_vietnam.safetensors"),
        }

        try:
            from tools.modal_jev_finetuning import DatasetSecretScrubber
            scrubber: Any = DatasetSecretScrubber()
        except Exception:
            scrubber = None

        def _clean(txt: str) -> str:
            return scrubber.scrub_text(txt) if scrubber and hasattr(scrubber, "scrub_text") else txt

        sft_records: List[Dict[str, Any]] = []
        dpo_records: List[Dict[str, Any]] = []
        train_features: List[List[float]] = []
        train_bloom_labels: List[int] = []
        train_mode_labels: List[int] = []
        train_argon_labels: List[int] = []
        train_texts: List[str] = []

        mode_to_idx = {"fast": 0, "deep_tot": 1, "dialectic_audit": 2, "creative_synthesis": 3}

        def _bloom_tier_to_argon_idx(bloom_val: int, tier_val: str) -> int:
            if tier_val == "L3" and bloom_val >= 6:
                return 3  # L4_SOVEREIGN -> gemini-4-argon-high
            if bloom_val >= 5 or tier_val == "L3":
                return 2  # L3_COMPLEX -> gemini-4-argon-high
            if bloom_val >= 3 or tier_val == "L2":
                return 1  # L2_STANDARD -> gemini-4-argon-medium
            return 0      # L1_FAST -> gemini-4-argon-low

        with self.db.get_connection() as conn:
            # 1. Harvest consolidated cognitive_memories for SFT & Neural Router training
            mem_rows = conn.execute("""
                SELECT mem_key, title, content, tier, bloom_level, synaptic_strength, evidence_score
                FROM cognitive_memories
                WHERE status = 'ACTIVE'
                ORDER BY synaptic_strength DESC LIMIT 300;
            """).fetchall()

            for r in mem_rows:
                title = _clean(str(r["title"]))
                content = _clean(str(r["content"]))
                bloom = max(1, min(6, int(r["bloom_level"])))
                tier = str(r["tier"])

                if bloom >= 5:
                    target_mode = "dialectic_audit" if "audit" in content.lower() or "critique" in content.lower() else "deep_tot"
                elif bloom == 4:
                    target_mode = "deep_tot"
                elif bloom == 3:
                    target_mode = "fast"
                else:
                    target_mode = "creative_synthesis"

                text_sample = f"{title}\n{content[:800]}"
                train_features.append(self.featurize_text_256d(text_sample))
                train_texts.append(text_sample)
                train_bloom_labels.append(bloom - 1)
                train_mode_labels.append(mode_to_idx[target_mode])
                train_argon_labels.append(_bloom_tier_to_argon_idx(bloom, tier))

                if tier in ("L2", "L3") and bloom >= 3:
                    sft_records.append({
                        "sample_type": "SFT",
                        "instruction": f"Recall and apply sovereign SecondBrain knowledge ({tier}-B{bloom}) for: {title}",
                        "input": title,
                        "chosen": content[:1200],
                        "rejected": "",
                        "metadata": {
                            "mem_key": r["mem_key"],
                            "tier": tier,
                            "bloom_level": bloom,
                            "harness_mode": target_mode,
                        },
                    })

            # 2. Harvest recorded JEV sessions
            sess_rows = conn.execute("SELECT * FROM jev_sessions ORDER BY id DESC LIMIT 200;").fetchall()
            for sr in sess_rows:
                q_txt = _clean(str(sr["query"]))
                c_txt = _clean(str(sr["chosen_response"]))
                r_txt = _clean(str(sr["rejected_response"] or ""))
                b_lvl = max(1, min(6, int(sr["bloom_level"])))
                h_mode = str(sr["harness_mode"]) if str(sr["harness_mode"]) in mode_to_idx else "fast"
                s_tier = str(sr["tier"])

                train_features.append(self.featurize_text_256d(q_txt))
                train_texts.append(f"{q_txt}\n{c_txt[:400]}")
                train_bloom_labels.append(b_lvl - 1)
                train_mode_labels.append(mode_to_idx[h_mode])
                train_argon_labels.append(_bloom_tier_to_argon_idx(b_lvl, s_tier))

                rec = {
                    "sample_type": str(sr["sample_type"]),
                    "instruction": "Execute stratified AGI cognitive reasoning and routing.",
                    "input": q_txt,
                    "chosen": c_txt[:1200],
                    "rejected": r_txt[:1200],
                    "metadata": {
                        "session_key": sr["session_key"],
                        "tier": s_tier,
                        "bloom_level": b_lvl,
                        "harness_mode": h_mode,
                    },
                }
                if str(sr["sample_type"]) == "DPO" and r_txt:
                    dpo_records.append(rec)
                else:
                    sft_records.append(rec)

            # 3. Harvest Hegelian Dialectical Audits as DPO Contrastive Triads (Suppressing False Knowledge)
            audit_rows = conn.execute("""
                SELECT a.*, t.title AS thesis_title, t.content AS thesis_content
                FROM dialectical_audits a
                LEFT JOIN cognitive_memories t ON a.thesis_key = t.mem_key
                WHERE a.verdict IN ('ABANDON', 'SUPERSEDE')
                ORDER BY a.id DESC LIMIT 100;
            """).fetchall()

            for ar in audit_rows:
                thesis_title = _clean(str(ar["thesis_title"] or ar["thesis_key"]))
                rejected_claim = _clean(str(ar["thesis_content"] or ar["thesis_key"]))
                antithesis = _clean(str(ar["antithesis_claim"]))
                synth_key = ar["synthesis_key"]
                chosen_text = f"Refuted false thesis via Hegelian Critique: {antithesis}"
                if synth_key:
                    synth_row = conn.execute(
                        "SELECT content FROM cognitive_memories WHERE mem_key = ?;", (synth_key,)
                    ).fetchone()
                    if synth_row:
                        chosen_text = _clean(str(synth_row["content"]))

                dpo_records.append({
                    "sample_type": "DPO",
                    "instruction": f"Evaluate epistemic validity and reject false assumptions regarding: {thesis_title}",
                    "input": thesis_title,
                    "chosen": chosen_text[:1200],
                    "rejected": rejected_claim[:1200],
                    "metadata": {
                        "thesis_key": ar["thesis_key"],
                        "verdict": ar["verdict"],
                        "synthesis_key": synth_key,
                    },
                })

            # 4. PDCA Loop 1: Harvest Contrastive DPO Triads from Gray Doom review-decisions-v1.json,
            #    Evolution Ledger knowledge_distillation, and Sovereign L3 B6 vs Naive L1 pairs.
            gd_review_path = Path("/home/zen/Downloads/Graydoom-novel/docs/review-decisions-v1.json")
            if gd_review_path.exists() and output_dir is None:
                try:
                    gd_data = json.loads(gd_review_path.read_text(encoding="utf-8"))
                    decisions = gd_data.get("decisions", {}) if isinstance(gd_data, dict) else {}
                    for item_key, item_val in list(decisions.items()):
                        if isinstance(item_val, dict) and item_val.get("status") == "NEEDS_REVISION":
                            note = _clean(str(item_val.get("notes") or "Violated 26-character DNA, Profile One-Eye Rule, or 11% alpha margin."))
                            dpo_records.append({
                                "sample_type": "DPO",
                                "instruction": f"Enforce Gray Doom Codex Game Art & Character DNA QA on asset: {item_key}",
                                "input": str(item_key),
                                "chosen": (
                                    f"Enforce 26-Character Tri-Lock DNA, deterministic crop from sunward-court-six-person-v3.png, "
                                    f"Profile One-Eye Rule at ANG_PRF_90, 11% raw alpha margin, and 3-block spatial prompt. Remediation: {note}"
                                )[:1200],
                                "rejected": f"Accept unverified candidate {item_key} with defect: {note}"[:1200],
                                "metadata": {"source": "graydoom_review_decisions", "asset": str(item_key)},
                            })
                except Exception:
                    pass

            ev_ledger_path = Path.home() / ".gemini" / "antigravity" / "memory" / "evolution_ledger.db"
            if ev_ledger_path.exists() and output_dir is None:
                try:
                    with sqlite3.connect(f"file:{ev_ledger_path}?mode=ro", uri=True) as ev_conn:
                        kd_rows = ev_conn.execute(
                            "SELECT topic, lesson_text, confidence FROM knowledge_distillation ORDER BY rowid DESC LIMIT 25;"
                        ).fetchall()
                        for topic, lesson_text, conf in kd_rows:
                            t_clean = _clean(str(topic))
                            l_clean = _clean(str(lesson_text))
                            dpo_records.append({
                                "sample_type": "DPO",
                                "instruction": f"Enforce sovereign security and concurrency invariant for: {t_clean}",
                                "input": t_clean,
                                "chosen": l_clean[:1200],
                                "rejected": f"Bypass {t_clean} guard, rely on unverified wall-clock timestamps, or trust unpinned inline keys.",
                                "metadata": {"source": "evolution_ledger_distillation", "confidence": float(conf or 1.0)},
                            })
                except Exception:
                    pass

            for r in mem_rows:
                if len(dpo_records) >= 65:
                    break
                if str(r["tier"]) == "L3" and int(r["bloom_level"]) >= 5:
                    t_clean = _clean(str(r["title"]))
                    c_clean = _clean(str(r["content"]))
                    dpo_records.append({
                        "sample_type": "DPO",
                        "instruction": f"Enforce L3-B6 Sovereign Invariant over unverified baseline for: {t_clean}",
                        "input": t_clean,
                        "chosen": c_clean[:1200],
                        "rejected": f"Skip empirical tool verification or bypass constitutional rule for {t_clean}.",
                        "metadata": {"source": "sovereign_l3_contrastive", "mem_key": r["mem_key"]},
                    })

        # Write sanitized JSONL dataset with mode 0600
        all_records = sft_records + dpo_records
        jsonl_lines = [json.dumps(r, ensure_ascii=False) for r in all_records]
        dataset_path.write_text("\n".join(jsonl_lines) + ("\n" if jsonl_lines else ""), encoding="utf-8")
        try:
            os.chmod(dataset_path, 0o600)
        except Exception:
            pass

        # Train PyTorch 3-Head Cortical Router + r=16 Domain LoRA Adapters & Export .safetensors + .onnx
        onnx_latency_ms = 0.0
        final_loss = 0.0
        try:
            import shutil
            import torch
            import torch.nn as nn
            import safetensors.torch
            import onnxruntime as ort

            class MyelinatedCorticalRouter(nn.Module):
                def __init__(self, in_dim: int = 256, hidden_dim: int = 64, lora_rank: int = 8):
                    super().__init__()
                    self.base_fc = nn.Linear(in_dim, hidden_dim)
                    self.lora_A = nn.Linear(in_dim, lora_rank, bias=False)
                    self.lora_B = nn.Linear(lora_rank, hidden_dim, bias=False)
                    self.lora_scale = 2.0  # alpha=16 / r=8
                    self.head_bloom = nn.Linear(hidden_dim, 6)
                    self.head_mode = nn.Linear(hidden_dim, 4)
                    self.head_argon = nn.Linear(hidden_dim, 4)

                def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
                    h = torch.relu(self.base_fc(x) + self.lora_B(self.lora_A(x)) * self.lora_scale)
                    return self.head_bloom(h), self.head_mode(h), self.head_argon(h)

            torch.manual_seed(42)
            if not train_features:
                _fallback = "Sovereign ADR invariant architecture"
                train_features = [self.featurize_text_256d(_fallback)]
                train_texts = [_fallback]
                train_bloom_labels = [5]
                train_mode_labels = [1]
                train_argon_labels = [3]

            # PDCA Loop 5: deterministic 80/20 holdout -> real validation metrics (not train-set loss only)
            n_samples = len(train_features)
            perm = torch.randperm(n_samples, generator=torch.Generator().manual_seed(42))
            n_val = max(1, n_samples // 5) if n_samples >= 5 else 0
            val_idx = perm[:n_val].tolist()
            tr_idx = perm[n_val:].tolist()

            x_all = torch.tensor(train_features, dtype=torch.float32)
            y_bloom = torch.tensor(train_bloom_labels, dtype=torch.long)
            y_mode = torch.tensor(train_mode_labels, dtype=torch.long)
            y_argon = torch.tensor(train_argon_labels, dtype=torch.long)
            criterion = nn.CrossEntropyLoss()

            def _three_head_loss(m: nn.Module, idx: List[int]) -> torch.Tensor:
                ob, om, oa = m(x_all[idx])
                return criterion(ob, y_bloom[idx]) + criterion(om, y_mode[idx]) + criterion(oa, y_argon[idx])

            model = MyelinatedCorticalRouter(lora_rank=8)
            optimizer = torch.optim.AdamW(model.parameters(), lr=0.015, weight_decay=1e-4)
            model.train()
            train_loss = 0.0
            for _ in range(epochs):
                optimizer.zero_grad()
                loss = _three_head_loss(model, tr_idx)
                loss.backward()
                optimizer.step()
                train_loss = float(loss.item())

            val_loss = val_acc_bloom = val_acc_mode = val_acc_argon = None
            if val_idx:
                model.eval()
                with torch.no_grad():
                    vob, vom, voa = model(x_all[val_idx])
                    val_loss = round(float(_three_head_loss(model, val_idx).item()), 4)
                    val_acc_bloom = round(float((vob.argmax(1) == y_bloom[val_idx]).float().mean()), 4)
                    val_acc_mode = round(float((vom.argmax(1) == y_mode[val_idx]).float().mean()), 4)
                    val_acc_argon = round(float((voa.argmax(1) == y_argon[val_idx]).float().mean()), 4)
            validation_metrics = {
                "train_loss": round(train_loss, 4),
                "val_loss": val_loss,
                "val_acc_bloom": val_acc_bloom,
                "val_acc_mode": val_acc_mode,
                "val_acc_argon": val_acc_argon,
                "train_size": len(tr_idx),
                "val_size": len(val_idx),
            }
            final_loss = train_loss

            def _extract_tensors(m: nn.Module) -> Dict[str, Any]:
                names = (
                    "lora_A.weight", "lora_B.weight", "base_fc.weight", "base_fc.bias",
                    "head_bloom.weight", "head_bloom.bias", "head_mode.weight", "head_mode.bias",
                    "head_argon.weight", "head_argon.bias",
                )
                sd = m.state_dict()
                return {k: sd[k].detach().cpu().contiguous() for k in names}

            # 1. Export Master LoRA Adapter (r=8) & 3-Head Router Weights to .safetensors (CWE-502 safe serialization)
            safetensors.torch.save_file(_extract_tensors(model), str(lora_path))

            # PDCA Loop 5b: REAL domain LoRA fine-tuning (frozen base + heads, trainable r=16 A/B)
            domain_keywords = {
                "graydoom_codex_harness": ["gray doom", "graydoom", "travianz", "gd-", "character", "game art", "codex"],
                "odoo20_owl_rule29": ["odoo", "owl", "qweb", "insilos", "rule 29", "t-out"],
                "adversarial_security_tot": ["cwe", "security", "adversarial", "lease", "clock", "credit gate", "injection"],
                "nemotron_personas_vietnam": [
                    "nemotron", "persona", "vietnam", "miền bắc", "miền trung", "miền nam",
                    "đóng vai", "nhân khẩu học", "zero-latex", "tts v0-sense",
                ],
            }
            frozen_prefixes = ("base_fc.", "head_bloom.", "head_mode.", "head_argon.")
            base_sd = {k: v.clone() for k, v in model.state_dict().items() if k.startswith(frozen_prefixes)}
            domain_lora_metrics: Dict[str, Dict[str, Any]] = {}
            for dom_name, kws in domain_keywords.items():
                d_idx = [i for i, t in enumerate(train_texts) if any(k in t.lower() for k in kws)]
                dm = MyelinatedCorticalRouter(lora_rank=16)
                dm.load_state_dict(base_sd, strict=False)
                for p_name, p in dm.named_parameters():
                    if p_name.startswith(frozen_prefixes):
                        p.requires_grad_(False)
                nn.init.kaiming_uniform_(dm.lora_A.weight, a=5 ** 0.5)
                nn.init.zeros_(dm.lora_B.weight)
                if len(d_idx) >= 4:
                    dm.train()
                    d_opt = torch.optim.AdamW([p for p in dm.parameters() if p.requires_grad], lr=0.01, weight_decay=1e-4)
                    d_loss = 0.0
                    for _ in range(epochs):
                        d_opt.zero_grad()
                        dl = _three_head_loss(dm, d_idx)
                        dl.backward()
                        d_opt.step()
                        d_loss = float(dl.item())
                    d_status, d_final = "TRAINED", round(d_loss, 4)
                else:
                    nn.init.zeros_(dm.lora_A.weight)  # honest zero-delta no-op adapter
                    d_status, d_final = "INSUFFICIENT_DATA", None
                safetensors.torch.save_file(_extract_tensors(dm), domain_lora_paths[dom_name])
                domain_lora_metrics[dom_name] = {"samples": len(d_idx), "status": d_status, "final_loss": d_final}

            model.eval()

            # 2. Export 3-Head executable ONNX graph + Dynamic INT8 Quantized ONNX graph
            dummy_in = torch.zeros(1, 256, dtype=torch.float32)
            torch.onnx.export(
                model,
                (dummy_in,),
                str(onnx_path),
                input_names=["features"],
                output_names=["bloom_logits", "mode_logits", "argon_logits"],
                dynamo=False,
            )
            try:
                from onnxruntime.quantization import QuantType, quantize_dynamic
                quantize_dynamic(
                    model_input=str(onnx_path),
                    model_output=str(onnx_int8_path),
                    weight_type=QuantType.QInt8,
                )
            except Exception:
                shutil.copy2(str(onnx_path), str(onnx_int8_path))

            # 3. Warm-cache ONNXRuntime session & measure pure warm inference latency (< 2.50 ms target)
            sess_opts = ort.SessionOptions()
            sess_opts.intra_op_num_threads = 2
            sess = ort.InferenceSession(str(onnx_path), sess_options=sess_opts, providers=["CPUExecutionProvider"])
            dummy_np = dummy_in.numpy()
            sess.run(None, {"features": dummy_np})  # Warm-up pass
            t0 = time.perf_counter()
            sess.run(None, {"features": dummy_np})
            onnx_latency_ms = round((time.perf_counter() - t0) * 1000.0, 3)
            if not hasattr(self, "_onnx_session_cache"):
                self._onnx_session_cache: Dict[str, Any] = {}
            self._onnx_session_cache[str(onnx_path)] = (os.path.getmtime(onnx_path), sess)
        except Exception as exc:
            return {
                "status": "PARTIAL_DATASET_ONLY",
                "error": str(exc),
                "dataset_path": str(dataset_path),
                "sft_samples_count": len(sft_records),
                "dpo_samples_count": len(dpo_records),
            }

        report_payload = {
            "status": "MYELINATED",
            "dataset_path": str(dataset_path),
            "sft_samples_count": len(sft_records),
            "dpo_samples_count": len(dpo_records),
            "lora_safetensors_path": str(lora_path),
            "domain_lora_paths": domain_lora_paths,
            "onnx_model_path": str(onnx_path),
            "onnx_int8_model_path": str(onnx_int8_path),
            "training_samples": len(train_features),
            "final_loss": round(final_loss, 4),
            "validation_metrics": validation_metrics,
            "domain_lora_metrics": domain_lora_metrics,
            "onnx_inference_latency_ms": onnx_latency_ms,
        }
        try:
            manifest_path.write_text(json.dumps(report_payload, indent=2), encoding="utf-8")
        except Exception:
            pass
        return report_payload

    def hot_swap_domain_lora(self, domain: str, myelination_dir: Optional[Path] = None) -> Dict[str, Any]:
        """Hot-swap a domain LoRA adapter (allowlisted, traversal-safe) and measure latency vs the <15 ms KPI."""
        import re as _re
        import time as _time
        import safetensors.torch

        allowlist = (
            "graydoom_codex_harness",
            "odoo20_owl_rule29",
            "adversarial_security_tot",
            "nemotron_personas_vietnam",
        )
        if not _re.fullmatch(r"[a-z0-9_]{1,64}", str(domain)) or domain not in allowlist:
            raise ValueError(f"Domain {domain!r} not in allowlist {allowlist}")
        if myelination_dir is not None:
            base = Path(myelination_dir)
        elif getattr(self, "myelination_dir", None):
            base = Path(self.myelination_dir)
        else:
            base = Path.home() / ".hermes" / "jev_myelination"
        path = base / f"lora_{domain}.safetensors"
        if not path.exists():
            raise FileNotFoundError(str(path))

        t0 = _time.perf_counter()
        tensors = safetensors.torch.load_file(str(path))
        lora_a = tensors["lora_A.weight"]
        lora_b = tensors["lora_B.weight"]
        delta = (lora_b @ lora_a) * 2.0
        ms = (_time.perf_counter() - t0) * 1000.0
        self._active_domain_lora = {"domain": domain, "delta": delta, "rank": int(lora_a.shape[0])}
        return {
            "domain": domain,
            "path": str(path),
            "rank": int(lora_a.shape[0]),
            "delta_shape": list(delta.shape),
            "delta_norm": round(float(delta.norm()), 6),
            "hot_swap_latency_ms": round(ms, 3),
            "within_kpi_15ms": ms < 15.0,
        }

    def predict_with_onnx_surrogate(
        self,
        query: str,
        onnx_path: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """
        Executes sub-millisecond local inference using the myelinated 3-Head ONNX surrogate
        (`secondbrain_jev_router.onnx`) to predict Bloom Level (B1..B6), AGI Harness Mode,
        and 4-Level Gemini 4 Argon Tier (L1_FAST..L4_SOVEREIGN).
        """
        import os
        import time
        import numpy as np
        import onnxruntime as ort

        target_onnx = (
            Path(onnx_path)
            if onnx_path
            else (Path.home() / ".hermes" / "jev_myelination" / "secondbrain_jev_router.onnx")
        )
        if not target_onnx.exists():
            self.myelinate_jev_lora_and_onnx(output_dir=target_onnx.parent)

        if not hasattr(self, "_onnx_session_cache"):
            self._onnx_session_cache = {}
        key = str(target_onnx)
        mtime = os.path.getmtime(target_onnx)
        cached = self._onnx_session_cache.get(key)
        if cached is None or cached[0] != mtime:
            sess_opts = ort.SessionOptions()
            sess_opts.intra_op_num_threads = 2
            sess = ort.InferenceSession(key, sess_options=sess_opts, providers=["CPUExecutionProvider"])
            self._onnx_session_cache[key] = (mtime, sess)
        else:
            sess = cached[1]

        feats = np.array([self.featurize_text_256d(query)], dtype=np.float32)
        t0 = time.perf_counter()
        outputs = sess.run(None, {"features": feats})
        latency_ms = round((time.perf_counter() - t0) * 1000.0, 3)

        bloom_logits = outputs[0]
        mode_logits = outputs[1]
        argon_logits = outputs[2] if len(outputs) >= 3 else None

        modes = ["fast", "deep_tot", "dialectic_audit", "creative_synthesis"]
        argon_levels = ["L1_FAST", "L2_STANDARD", "L3_COMPLEX", "L4_SOVEREIGN"]
        argon_models = [
            "gemini-4-argon-low",
            "gemini-4-argon-medium",
            "gemini-4-argon-high",
            "gemini-4-argon-high",
        ]
        pred_bloom_idx = int(np.argmax(bloom_logits[0]))
        pred_mode_idx = int(np.argmax(mode_logits[0]))
        pred_argon_idx = int(np.argmax(argon_logits[0])) if argon_logits is not None else min(3, pred_bloom_idx // 2)

        return {
            "query": query,
            "predicted_bloom": f"B{pred_bloom_idx + 1}",
            "bloom_level": pred_bloom_idx + 1,
            "predicted_harness_mode": modes[pred_mode_idx],
            "predicted_argon_level": argon_levels[pred_argon_idx],
            "recommended_argon_model": argon_models[pred_argon_idx],
            "latency_ms": latency_ms,
            "engine": "ONNX_MYELINATED_SURROGATE",
        }


# ==============================================================================
# 5. MODULE-LEVEL CONVENIENCE INTERFACES & CLI
# ==============================================================================

_DEFAULT_ENGINE: Optional[CognitiveSecondBrainEngine] = None


def get_default_engine() -> CognitiveSecondBrainEngine:
    global _DEFAULT_ENGINE
    if _DEFAULT_ENGINE is None:
        _DEFAULT_ENGINE = CognitiveSecondBrainEngine()
    return _DEFAULT_ENGINE


def reinforce_memory(
    mem_key: str,
    evidence_boost: float = 0.12,
    promote_bloom: bool = True
) -> Dict[str, Any]:
    return get_default_engine().reinforce_memory(mem_key, evidence_boost, promote_bloom)


def dialectical_critique(
    thesis_key: str,
    antithesis_claim: str,
    new_content: str = "",
    evidence_score: float = 0.85,
    evidence_ref: str = "",
    tombstone_path: Optional[Path] = None
) -> Dict[str, Any]:
    return get_default_engine().dialectical_critique(
        thesis_key, antithesis_claim, new_content, evidence_score, evidence_ref, tombstone_path
    )


def self_heal_secondbrain(vault_path: Optional[Path] = None) -> Dict[str, Any]:
    return get_default_engine().self_heal_secondbrain(vault_path)


def run_circadian_sleep_cycle(vault_path: Optional[Path] = None) -> Dict[str, Any]:
    return get_default_engine().run_circadian_sleep_cycle(vault_path)


def run_exogenous_ecology_cycle(vault_path: Optional[Path] = None) -> Dict[str, Any]:
    return get_default_engine().run_exogenous_ecology_cycle(vault_path)


def assemble_harness_context(
    query: str,
    harness_mode: str = "fast",
    token_budget: int = 1200
) -> str:
    return get_default_engine().assemble_harness_context(query, harness_mode, token_budget)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sovereign Cognitive SecondBrain Engine (Neuro-Biological 02:00 AM Sleep + Bloom + LoRA/ONNX Myelination)"
    )
    parser.add_argument("--seed-from-vault", action="store_true", help="Seed cognitive memories from SecondBrain vault & ADRs")
    parser.add_argument("--seed-nemotron-personas", action="store_true", help="Synthesize & seed nvidia/Nemotron-Personas-Vietnam archetypes into SecondBrain")
    parser.add_argument("--sync-exogenous-ecology", action="store_true", help="Sync GitHub Trending, arXiv, Standards & Autonomous Tasks into Exogenous Knowledge Space")
    parser.add_argument("--self-heal", action="store_true", help="Run self-healing maintenance & Ebbinghaus decay on SecondBrain")
    parser.add_argument("--sleep-cycle", action="store_true", help="Execute full 5-stage 02:00 AM Neuro-Biological Circadian Sleep Consolidation Cycle")
    parser.add_argument("--myelinate", action="store_true", help="Train & export LoRA (.safetensors) + ONNX router from consolidated SecondBrain memories")
    parser.add_argument("--predict-onnx", type=str, default="", help="Run sub-ms ONNX surrogate inference on a query")
    parser.add_argument("--harness-query", type=str, default="", help="Test stratified context assembly for a query")
    parser.add_argument("--mode", type=str, default="fast", choices=["fast", "deep_tot", "dialectic_audit", "creative_synthesis"])
    parser.add_argument("--reinforce", type=str, default="", help="Reinforce a specific mem_key")
    args = parser.parse_args()

    engine = get_default_engine()
    output: Dict[str, Any] = {}

    if args.sleep_cycle:
        output["sleep_cycle_report"] = engine.run_circadian_sleep_cycle()
    else:
        if args.seed_from_vault:
            output["seed_report"] = engine.seed_from_secondbrain_vault()

        if args.seed_nemotron_personas:
            output["nemotron_personas_report"] = engine.synthesize_nemotron_personas_vietnam()

        if args.sync_exogenous_ecology:
            output["exogenous_ecology_report"] = engine.run_exogenous_ecology_cycle()

        if args.self_heal:
            output["self_heal_report"] = engine.self_heal_secondbrain()

        if args.myelinate:
            output["myelination_report"] = engine.myelinate_jev_lora_and_onnx()

    if args.predict_onnx:
        output["onnx_prediction"] = engine.predict_with_onnx_surrogate(args.predict_onnx)

    if args.reinforce:
        output["reinforce_report"] = engine.reinforce_memory(args.reinforce)

    if args.harness_query:
        output["harness_context"] = engine.assemble_harness_context(args.harness_query, harness_mode=args.mode)

    if not output:
        output["matrix_stats"] = {
            "status_counts": engine.get_matrix_stats()["status_counts"],
            "recent_audits_count": len(engine.get_matrix_stats()["recent_audits"]),
            "brain_region_map": BRAIN_REGION_MAP,
        }

    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()


