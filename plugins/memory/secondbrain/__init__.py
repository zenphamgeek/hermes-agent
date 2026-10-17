"""SecondBrain Cognitive Memory Provider Plugin for Hermes Agent.

Integrates the local Obsidian SecondBrain (`/home/zen/Obsidian/SecondBrain`) and
`KnowledgeCompilerDB` (`~/.hermes/knowledge_compiler.db`) into Hermes Agent's
`MemoryManager` lifecycle using human-like cognitive architectures:
  - Bloom Taxonomy Cognitive Ladder (`B1_REMEMBER` .. `B6_CREATE`)
  - 5-Tier Stratified AGI Memory (`L0_SENSORY` .. `L4_ARCHIVE`)
  - Ebbinghaus Forgetting Curve & Synaptic Consolidation (`L1 -> L2 -> L3`)
  - Hegelian Dialectical Critique (`ABANDON` false knowledge, `SUPERSEDE`, `REFINE`, `QUARANTINE`)
  - Autonomous Vault Self-Healing (broken symlinks, orphan recovery, live matrix)
"""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path
import re
from typing import Any, Dict, List, Optional

from agent.memory_provider import MemoryProvider, RecallStatus
from hermes_cli.config import cfg_get
from tools.cognitive_secondbrain_engine import (
    BloomLevel,
    CognitiveSecondBrainEngine,
    MemoryTier,
)
from tools.registry import tool_error
from utils import is_truthy_value

logger = logging.getLogger(__name__)


SECONDBRAIN_COGNITIVE_SCHEMA: Dict[str, Any] = {
    "name": "secondbrain_cognitive",
    "description": (
        "Stratified AGI Cognitive Memory & Obsidian SecondBrain maintenance tool.\n"
        "Operates across Bloom Taxonomy levels (B1_REMEMBER .. B6_CREATE) and "
        "5 memory tiers (L0..L4) with Ebbinghaus retention, synaptic consolidation, "
        "Hegelian dialectical critique (abandoning or superseding false knowledge), "
        "and autonomous Obsidian vault self-healing.\n\n"
        "ACTIONS:\n"
        "• recall_harness — Stratified retrieval tailored to AGI harness mode "
        "('fast', 'deep_tot', 'dialectic_audit', 'creative_synthesis').\n"
        "• store — Store or upsert a memory with automatic Bloom classification.\n"
        "• reinforce — Consolidate a verified memory (boosts synaptic strength, "
        "promotes B1->B6 and L1->L2->L3).\n"
        "• critique — Hegelian dialectical critique of an existing thesis against "
        "empirical antithesis evidence ('ABANDON' false knowledge, 'SUPERSEDE' with "
        "new synthesis + Clef tombstone, 'REFINE', or 'QUARANTINE').\n"
        "• self_heal — Repair broken vault symlinks, index orphan notes, decay stale "
        "episodes via Ebbinghaus curve, and update Cognitive-Memory-Matrix.md.\n"
        "• matrix_stats — Return the 5x6 Tier x Bloom epistemic matrix and recent audits."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": [
                    "recall_harness",
                    "store",
                    "reinforce",
                    "critique",
                    "self_heal",
                    "sleep_cycle",
                    "matrix_stats",
                ],
                "description": "Cognitive operation to execute.",
            },
            "query": {
                "type": "string",
                "description": "Search query for 'recall_harness'.",
            },
            "harness_mode": {
                "type": "string",
                "enum": ["fast", "deep_tot", "dialectic_audit", "creative_synthesis"],
                "description": "AGI harness retrieval profile for 'recall_harness'.",
            },
            "token_budget": {
                "type": "integer",
                "description": "Token budget for 'recall_harness' (default: 1200).",
            },
            "mem_key": {
                "type": "string",
                "description": "Unique memory key for 'store' or 'reinforce'.",
            },
            "title": {
                "type": "string",
                "description": "Human-readable title for 'store'.",
            },
            "content": {
                "type": "string",
                "description": "Knowledge content for 'store'.",
            },
            "tier": {
                "type": "string",
                "enum": ["L1", "L2", "L3"],
                "description": "Memory tier for 'store' (default: 'L2').",
            },
            "synaptic_strength": {
                "type": "number",
                "description": "Initial synaptic strength [0.0..1.0] for 'store' (default: 0.75).",
            },
            "evidence_score": {
                "type": "number",
                "description": "Empirical evidence score [0.0..1.0] for 'store' or 'critique'.",
            },
            "evidence_boost": {
                "type": "number",
                "description": "Synaptic boost delta for 'reinforce' (default: 0.12).",
            },
            "promote_bloom": {
                "type": "boolean",
                "description": "Whether 'reinforce' should promote Bloom level when consolidated (default: true).",
            },
            "thesis_key": {
                "type": "string",
                "description": "Target memory key to challenge in 'critique'.",
            },
            "antithesis_claim": {
                "type": "string",
                "description": "Counter-evidence or refutation claim for 'critique'.",
            },
            "new_content": {
                "type": "string",
                "description": "Synthesized replacement knowledge for 'critique' (leave empty to ABANDON false knowledge).",
            },
            "evidence_ref": {
                "type": "string",
                "description": "Citation, test log, or ADR reference backing 'critique'.",
            },
        },
        "required": ["action"],
    },
}


def _load_plugin_config() -> Dict[str, Any]:
    try:
        from hermes_cli.config import load_config_readonly
        all_config = load_config_readonly()
        return cfg_get(all_config, "plugins", "secondbrain", default={}) or {}
    except Exception:
        return {}


def _infer_harness_mode(query: str, default_mode: str = "fast") -> str:
    """Selects the optimal AGI harness mode based on query cognitive intent."""
    q = query.lower()
    if any(k in q for k in ("audit", "critique", "phản biện", "contradict", "security", "tombstone", "false", "sai")):
        return "dialectic_audit"
    if any(k in q for k in ("architecture", "kiến trúc", "root cause", "why", "analyze", "tot", "adr", "invariant")):
        return "deep_tot"
    if any(k in q for k in ("brainstorm", "synthesize", "idea", "creative", "design")):
        return "creative_synthesis"
    return default_mode


class SecondBrainMemoryProvider(MemoryProvider):
    """Stratified Cognitive SecondBrain memory provider (Bloom B1..B6, Tiers L0..L4)."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self._config = config or _load_plugin_config()
        self._engine: Optional[CognitiveSecondBrainEngine] = None
        self._session_id: str = ""
        self._last_recall_count: int = 0

    @property
    def name(self) -> str:
        return "secondbrain"

    def is_available(self) -> bool:
        return True

    def initialize(self, session_id: str, **kwargs) -> None:
        hermes_home = kwargs.get("hermes_home")
        if not hermes_home:
            try:
                from hermes_constants import get_hermes_home
                hermes_home = str(get_hermes_home())
            except Exception:
                hermes_home = str(Path.home() / ".hermes")

        raw_db = self._config.get("db_path", f"{hermes_home}/knowledge_compiler.db")
        if isinstance(raw_db, str):
            raw_db = raw_db.replace("$HERMES_HOME", str(hermes_home)).replace("${HERMES_HOME}", str(hermes_home))

        vault_path = Path(self._config.get("vault_path", "/home/zen/Obsidian/SecondBrain"))
        tombstone_path = self._config.get("tombstone_path")

        self._engine = CognitiveSecondBrainEngine(
            db_path=Path(raw_db),
            vault_path=vault_path,
            tombstone_path=Path(tombstone_path) if tombstone_path else None,
        )
        self._session_id = session_id
        self._last_recall_count = 0

    def system_prompt_block(self) -> str:
        if not self._engine:
            return ""
        try:
            stats = self._engine.get_matrix_stats()
            active = stats["status_counts"].get("ACTIVE", 0)
            superseded = stats["status_counts"].get("SUPERSEDED", 0)
            abandoned = stats["status_counts"].get("ABANDONED", 0)
        except Exception:
            active, superseded, abandoned = 0, 0, 0

        return (
            "# Cognitive SecondBrain (Bloom B1..B6 × Stratified Tiers L0..L4)\n"
            f"Active Memories: {active} | Superseded: {superseded} | Abandoned False Knowledge: {abandoned}.\n"
            "Use `secondbrain_cognitive` to:\n"
            "- `recall_harness`: Retrieve stratified memories by harness ('fast', 'deep_tot', 'dialectic_audit', 'creative_synthesis').\n"
            "- `reinforce`: Consolidate verified knowledge (boosts Ebbinghaus retention & promotes B1->B6, L1->L2->L3).\n"
            "- `critique`: Run Hegelian dialectical critique to ABANDON false knowledge or SUPERSEDE outdated theses with Clef tombstones.\n"
            "- `self_heal`: Repair Obsidian vault links, index orphans, and decay stale unverified episodes."
        )

    def prefetch(self, query: str, *, session_id: str = "") -> str:
        self._last_recall_count = 0
        if not self._engine or not query or not query.strip():
            return ""
        try:
            default_mode = str(self._config.get("default_harness_mode", "fast"))
            mode = _infer_harness_mode(query, default_mode=default_mode)
            context = self._engine.assemble_harness_context(query, harness_mode=mode, token_budget=800)
            if "No matching memories" in context:
                return ""
            # Count recalled headers (`### [L`)
            self._last_recall_count = len(re.findall(r"^### \[L\d-B\d\]", context, flags=re.MULTILINE))
            return context
        except Exception as exc:
            logger.debug("SecondBrain prefetch failed: %s", exc)
            return ""

    def recall_status(self) -> Optional[RecallStatus]:
        if self._last_recall_count > 0:
            return RecallStatus(
                provider_label="secondbrain",
                count=self._last_recall_count,
                glyph="🧠",
            )
        return None

    def on_memory_write(
        self,
        action: str,
        target: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Mirror built-in memory writes into SecondBrain L2 Semantic tier."""
        if not self._engine or not content or action not in ("add", "replace"):
            return
        try:
            digest = hashlib.sha256(content.strip().encode("utf-8")).hexdigest()[:10]
            mem_key = f"builtin:{target}:{digest}"
            title = content.strip().splitlines()[0][:72]
            self._engine.store_memory(
                mem_key=mem_key,
                title=title,
                content=content,
                tier=MemoryTier.L2_SEMANTIC.value,
                synaptic_strength=0.78,
                evidence_score=0.70,
            )
        except Exception as exc:
            logger.debug("SecondBrain memory_write mirror failed: %s", exc)

    def on_session_end(self, messages: List[Dict[str, Any]]) -> None:
        if not self._engine:
            return
        if not is_truthy_value(self._config.get("auto_self_heal_on_exit", True)):
            return
        try:
            self._engine.self_heal_secondbrain()
        except Exception as exc:
            logger.debug("SecondBrain on_session_end self-heal failed: %s", exc)

    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        return [SECONDBRAIN_COGNITIVE_SCHEMA]

    def handle_tool_call(self, tool_name: str, args: Dict[str, Any], **kwargs) -> str:
        if tool_name != "secondbrain_cognitive":
            return tool_error(f"Unknown tool: {tool_name}")
        if not self._engine:
            return tool_error("SecondBrainMemoryProvider is not initialized.")

        action = args.get("action", "")
        try:
            if action == "recall_harness":
                query = str(args.get("query", "")).strip()
                if not query:
                    return tool_error("recall_harness requires 'query'.")
                mode = str(args.get("harness_mode") or _infer_harness_mode(query))
                budget = int(args.get("token_budget", 1200))
                context = self._engine.assemble_harness_context(
                    query=query, harness_mode=mode, token_budget=budget
                )
                return json.dumps({
                    "harness_mode": mode,
                    "token_budget": budget,
                    "context": context,
                }, ensure_ascii=False)

            elif action == "store":
                mem_key = str(args.get("mem_key", "")).strip()
                title = str(args.get("title", "")).strip()
                content = str(args.get("content", "")).strip()
                if not mem_key or not title or not content:
                    return tool_error("store requires 'mem_key', 'title', and 'content'.")
                tier = str(args.get("tier", MemoryTier.L2_SEMANTIC.value))
                strength = float(args.get("synaptic_strength", 0.75))
                evidence = float(args.get("evidence_score", 0.65))
                record = self._engine.store_memory(
                    mem_key=mem_key,
                    title=title,
                    content=content,
                    tier=tier,
                    synaptic_strength=strength,
                    evidence_score=evidence,
                )
                return json.dumps({"status": "stored", "memory": record}, ensure_ascii=False)

            elif action == "reinforce":
                mem_key = str(args.get("mem_key", "")).strip()
                if not mem_key:
                    return tool_error("reinforce requires 'mem_key'.")
                boost = float(args.get("evidence_boost", 0.12))
                promote = bool(args.get("promote_bloom", True))
                record = self._engine.reinforce_memory(
                    mem_key=mem_key,
                    evidence_boost=boost,
                    promote_bloom=promote,
                )
                return json.dumps({"status": "reinforced", "memory": record}, ensure_ascii=False)

            elif action == "critique":
                thesis_key = str(args.get("thesis_key", "")).strip()
                antithesis_claim = str(args.get("antithesis_claim", "")).strip()
                if not thesis_key or not antithesis_claim:
                    return tool_error("critique requires 'thesis_key' and 'antithesis_claim'.")
                new_content = str(args.get("new_content", ""))
                evidence_score = float(args.get("evidence_score", 0.85))
                evidence_ref = str(args.get("evidence_ref", ""))
                result = self._engine.dialectical_critique(
                    thesis_key=thesis_key,
                    antithesis_claim=antithesis_claim,
                    new_content=new_content,
                    evidence_score=evidence_score,
                    evidence_ref=evidence_ref,
                )
                return json.dumps(result, ensure_ascii=False)

            elif action == "self_heal":
                report = self._engine.self_heal_secondbrain()
                return json.dumps(report, ensure_ascii=False)

            elif action == "sleep_cycle":
                report = self._engine.run_circadian_sleep_cycle()
                return json.dumps(report, ensure_ascii=False)

            elif action == "matrix_stats":
                stats = self._engine.get_matrix_stats()
                serializable_grid = {
                    f"{t}_B{b}": cnt for (t, b), cnt in stats["grid"].items()
                }
                return json.dumps({
                    "grid": serializable_grid,
                    "status_counts": stats["status_counts"],
                    "recent_audits": stats["recent_audits"],
                }, ensure_ascii=False)

            else:
                return tool_error(f"Unknown action: {action}")
        except KeyError as exc:
            return tool_error(f"Key not found: {exc}")
        except Exception as exc:
            return tool_error(str(exc))

    def backup_paths(self) -> List[str]:
        vault_path = str(self._config.get("vault_path", "/home/zen/Obsidian/SecondBrain"))
        return [vault_path]

    def shutdown(self) -> None:
        self._engine = None


def register(ctx) -> None:
    """Register the SecondBrain cognitive memory provider with the plugin system."""
    provider = SecondBrainMemoryProvider()
    ctx.register_memory_provider(provider)
