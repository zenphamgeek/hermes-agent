"""
tests/test_modal_jev_finetuning.py
==================================
Unit tests for the Modal JEV Decision Model fine-tuning pipeline.
"""

import json
from pathlib import Path
import pytest

from tools.modal_jev_finetuning import (
    JEV_SYSTEM_INSTRUCTION,
    harvest_dataset_from_ledgers,
)


def test_harvest_dataset_generation(tmp_path):
    output_ds = tmp_path / "test_jev_dataset.jsonl"
    fake_ledger = tmp_path / "fake_action_ledger.jsonl"

    # Write a simulated action ledger entry
    fake_ledger.write_text(
        json.dumps({
            "action": "jev_decision_evaluation",
            "domain": "enterprise_erp",
            "payload_sha256": "hash_12345",
            "status": "PERMITTED",
            "details": {
                "complexity": 1.5,
                "tier": "PRO",
                "runner": "odoo.tests.common.TransactionCase (`odoo-bin --test-enable`)",
            },
        }) + "\n",
        encoding="utf-8",
    )

    records = harvest_dataset_from_ledgers(
        action_ledger_path=fake_ledger,
        output_path=output_ds,
    )

    assert len(records) >= 5  # Seed anchors + ledger entry
    assert output_ds.exists()

    # Read back and verify JSONL structure
    lines = [json.loads(l) for l in output_ds.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert len(lines) == len(records)

    for item in lines:
        assert "instruction" in item
        assert "input" in item
        assert "output" in item
        out = item["output"]
        assert "domain" in out
        assert "complexity_score" in out
        assert 0.0 <= out["complexity_score"] <= 4.0
        assert out["target_tier"] in ("PRO", "ULTRA")
        assert "test_runner" in out
        assert isinstance(out["requires_cloud_escalation"], bool)
        assert out["verdict"] in ("PERMITTED", "ESCALATED", "REJECTED_COOLDOWN", "REJECTED_SYNTAX")


def test_seed_anchors_coverage(tmp_path):
    output_ds = tmp_path / "seed_dataset.jsonl"
    records = harvest_dataset_from_ledgers(
        action_ledger_path=tmp_path / "nonexistent.jsonl",
        output_path=output_ds,
    )

    domains = {r["output"]["domain"] for r in records}
    assert "enterprise_erp" in domains
    assert "game_simulation" in domains
    assert "ai_infrastructure" in domains

    # Verify both fast-path and escalated cases exist in seed data
    escalated_flags = {r["output"]["requires_cloud_escalation"] for r in records}
    assert True in escalated_flags
    assert False in escalated_flags
