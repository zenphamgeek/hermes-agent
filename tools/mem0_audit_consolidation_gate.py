#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools/mem0_audit_consolidation_gate.py
======================================
Mem0-Inspired Episodic-to-Semantic Memory Consolidation Gate for Swarm Security Audits.

Architecture:
- Episodic Tier: Raw audit observations (WARN, INFO, CRITICAL) per cron/step cycle.
- Semantic Tier: Codified invariants, durable security policies (.agents/rules/).
- Procedural Tier: Reusable audit playbooks & test gates (tests/test_*.py).

Consolidation Mechanics:
1. One-off noise suppression: A WARN finding must recur >= N times (default: 2)
   across audit cycles before graduating to a codified rule, preventing rule bloat.
2. Severity Fast-Track: CRITICAL findings bypass the recurrence counter and
   graduate immediately.
3. Expiration: Unrepeated episodic warnings decay after max_age_steps.
"""

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple


class FindingSeverity(str, Enum):
    CRITICAL = "CRITICAL"
    WARN = "WARN"
    INFO = "INFO"


@dataclass
class AuditObservation:
    finding_id: str
    category: str
    severity: FindingSeverity
    description: str
    step_index: int
    timestamp: float = field(default_factory=time.time)


@dataclass
class ConsolidatedRuleCandidate:
    category: str
    severity: FindingSeverity
    first_seen_step: int
    last_seen_step: int
    occurrences: int
    graduated: bool
    summary: str


class Mem0ConsolidationGate:
    def __init__(self, graduation_threshold: int = 2, max_age_steps: int = 5):
        self.graduation_threshold = graduation_threshold
        self.max_age_steps = max_age_steps
        self.episodic_log: List[AuditObservation] = []
        self.recurrent_tracker: Dict[str, List[AuditObservation]] = {}
        self.graduated_rules: Dict[str, ConsolidatedRuleCandidate] = {}

    def record_observation(
        self,
        finding_id: str,
        category: str,
        severity: FindingSeverity,
        description: str,
        step_index: int,
    ) -> Tuple[bool, Optional[ConsolidatedRuleCandidate]]:
        """
        Records an episodic observation and checks if it graduates to semantic tier.
        Returns: (did_graduate_now, ConsolidatedRuleCandidate)
        """
        obs = AuditObservation(
            finding_id=finding_id,
            category=category,
            severity=severity,
            description=description,
            step_index=step_index,
        )
        self.episodic_log.append(obs)

        if category not in self.recurrent_tracker:
            self.recurrent_tracker[category] = []
        self.recurrent_tracker[category].append(obs)

        # Prune expired observations outside the rolling window
        current_history = [
            o for o in self.recurrent_tracker[category]
            if step_index - o.step_index <= self.max_age_steps
        ]
        self.recurrent_tracker[category] = current_history

        # Fast-track critical findings immediately
        if severity == FindingSeverity.CRITICAL:
            candidate = ConsolidatedRuleCandidate(
                category=category,
                severity=severity,
                first_seen_step=current_history[0].step_index,
                last_seen_step=step_index,
                occurrences=len(current_history),
                graduated=True,
                summary=f"CRITICAL FAST-TRACK: {description}",
            )
            self.graduated_rules[category] = candidate
            return True, candidate

        # Standard consolidation for WARN: requires >= graduation_threshold recurrences
        if len(current_history) >= self.graduation_threshold:
            candidate = ConsolidatedRuleCandidate(
                category=category,
                severity=severity,
                first_seen_step=current_history[0].step_index,
                last_seen_step=step_index,
                occurrences=len(current_history),
                graduated=True,
                summary=f"GRADUATED INVARIANT (recurs {len(current_history)}x): {description}",
            )
            self.graduated_rules[category] = candidate
            return True, candidate

        return False, None

    def get_graduated_rules(self) -> List[ConsolidatedRuleCandidate]:
        return list(self.graduated_rules.values())

    def get_pending_warnings(self) -> List[Dict[str, any]]:
        pending = []
        for cat, history in self.recurrent_tracker.items():
            if cat not in self.graduated_rules and history:
                pending.append({
                    "category": cat,
                    "occurrences": len(history),
                    "threshold": self.graduation_threshold,
                    "latest_description": history[-1].description,
                })
        return pending
