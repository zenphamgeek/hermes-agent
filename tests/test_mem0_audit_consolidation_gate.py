#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_mem0_audit_consolidation_gate.py
===========================================
Unit tests for Mem0-Inspired Audit Consolidation Gate.
"""

from tools.mem0_audit_consolidation_gate import (
    Mem0ConsolidationGate,
    FindingSeverity,
)


def test_one_off_warn_stays_in_episodic_tier():
    gate = Mem0ConsolidationGate(graduation_threshold=2, max_age_steps=5)
    did_grad, cand = gate.record_observation(
        finding_id="obs-1",
        category="lockfile_range",
        severity=FindingSeverity.WARN,
        description="Possible range widening",
        step_index=1,
    )
    assert not did_grad
    assert cand is None
    assert len(gate.get_graduated_rules()) == 0
    assert len(gate.get_pending_warnings()) == 1


def test_recurrent_warn_graduates_to_semantic_tier():
    gate = Mem0ConsolidationGate(graduation_threshold=2, max_age_steps=5)
    gate.record_observation(
        finding_id="obs-1",
        category="tts_sanitizer_boundary",
        severity=FindingSeverity.WARN,
        description="Verify boundary sanitizer",
        step_index=1,
    )
    did_grad, cand = gate.record_observation(
        finding_id="obs-2",
        category="tts_sanitizer_boundary",
        severity=FindingSeverity.WARN,
        description="Verify boundary sanitizer",
        step_index=2,
    )
    assert did_grad
    assert cand is not None
    assert cand.occurrences == 2
    assert "GRADUATED INVARIANT" in cand.summary
    assert len(gate.get_graduated_rules()) == 1


def test_critical_finding_bypasses_threshold():
    gate = Mem0ConsolidationGate(graduation_threshold=3, max_age_steps=5)
    did_grad, cand = gate.record_observation(
        finding_id="obs-crit",
        category="shell_injection_vulnerability",
        severity=FindingSeverity.CRITICAL,
        description="shell=True detected in audio command",
        step_index=1,
    )
    assert did_grad
    assert cand is not None
    assert "CRITICAL FAST-TRACK" in cand.summary
    assert len(gate.get_graduated_rules()) == 1


def test_stale_findings_decay_without_graduation():
    gate = Mem0ConsolidationGate(graduation_threshold=2, max_age_steps=3)
    gate.record_observation(
        finding_id="obs-old",
        category="transient_lint",
        severity=FindingSeverity.WARN,
        description="Missing docstring",
        step_index=1,
    )
    # Step 6 is beyond max_age_steps (6 - 1 = 5 > 3)
    did_grad, cand = gate.record_observation(
        finding_id="obs-new",
        category="transient_lint",
        severity=FindingSeverity.WARN,
        description="Missing docstring",
        step_index=6,
    )
    assert not did_grad
    assert cand is None
    assert len(gate.get_graduated_rules()) == 0
