"""Declarative configuration schema for the SecondBrain cognitive memory provider."""

from __future__ import annotations

from plugins.memory.config_schema import (
    KIND_BOOL,
    KIND_SELECT,
    KIND_TEXT,
    ProviderConfigSchema,
    ProviderField,
    ProviderFieldOption,
    STORAGE_FLAT_JSON,
)

CONFIG_SCHEMA = ProviderConfigSchema(
    name="secondbrain",
    label="Cognitive SecondBrain (Bloom + Hegelian Critique)",
    storage=STORAGE_FLAT_JSON,
    fields=(
        ProviderField(
            key="vault_path",
            label="Obsidian SecondBrain Vault Path",
            kind=KIND_TEXT,
            default="/home/zen/Obsidian/SecondBrain",
            description="Canonical local Obsidian SecondBrain vault path.",
            inline=True,
        ),
        ProviderField(
            key="db_path",
            label="Knowledge Compiler SQLite DB",
            kind=KIND_TEXT,
            default="$HERMES_HOME/knowledge_compiler.db",
            description="SQLite WAL + FTS5 database storing cognitive_memories and dialectical_audits.",
            inline=True,
        ),
        ProviderField(
            key="default_harness_mode",
            label="Default AGI Harness Mode",
            kind=KIND_SELECT,
            default="fast",
            description="Default stratified recall mode when prefetching context.",
            options=(
                ProviderFieldOption("fast", "Fast (L2/L3, B3+)"),
                ProviderFieldOption("deep_tot", "Deep Tree-of-Thought (L1..L3, B4+)"),
                ProviderFieldOption("dialectic_audit", "Dialectical Audit (L2..L4, B5+)"),
                ProviderFieldOption("creative_synthesis", "Creative Synthesis (L2/L3, B2+)"),
            ),
            inline=True,
        ),
        ProviderField(
            key="auto_self_heal_on_exit",
            label="Auto Self-Heal on Session End",
            kind=KIND_BOOL,
            default="true",
            description="Run Ebbinghaus forgetting decay, orphan indexing, and live matrix export when session ends.",
            inline=True,
        ),
    ),
)
