#!/usr/bin/env python3
"""
Hybrid Logical Clocks (HLC), Monotonic Lamport Epoch Fencing, and RFC 7519 Clock-Skew Guard.
Remediates 5-minute (+/-300s) cross-node clock drift split-brain and CWE-20/CWE-78 node ID validation.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, Tuple

FLEET_NODE_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")

GROUP_B_PRO_NODES = {
    "insilos", "node-4", "node-5", "node-6", "team-3", "binhthuong",
    "justaskgao", "sunward", "ai-digimate", "codegeekvn", "gaopham",
    "zenonmind", "immoon0009-gmail-com", "nahlaleah102",
    "tsmei0209-gmail-com", "fast", "agy-home", "coderedgen", "zenphamgeek", "zeninallgeek", "just.ask.mr.zen",
}

DIRECT_ARGON_MODELS = {
    "gemini-4-argon-high",
    "gemini-4-argon-medium",
    "gemini-4-argon-low",
}

CLAUDE_ADAPTATION_MAP = {
    "claude-opus-5-5-high": "claude-opus-4-6-thinking",
    "claude-opus-5-5-medium": "claude-opus-4.6",
    "claude-sonnet-5-5-high": "claude-sonnet-4-6",
}


def resolve_model_for_node(
    node_id: str,
    requested_model: str,
    adapt_argon_to_flash: bool = False,
) -> Tuple[str, bool]:
    """
    Resolve requested model for Group B Pro nodes:
    - Group B Pro nodes natively support 4-Level Gemini 4 Argon (`gemini-4-argon-high/medium/low`),
      or optionally adapt to `gemini-3.8-flash-*` when `adapt_argon_to_flash=True`.
    - Claude 5.5 models dynamically adapt to Claude 4.6 (`claude-opus-4-6-thinking`, `claude-sonnet-4-6`).
    """
    validate_fleet_node_id(node_id.replace(".", "_"))
    if node_id in GROUP_B_PRO_NODES:
        if requested_model in CLAUDE_ADAPTATION_MAP:
            return CLAUDE_ADAPTATION_MAP[requested_model], True
        if adapt_argon_to_flash and requested_model in DIRECT_ARGON_MODELS:
            return requested_model.replace("gemini-4-argon-", "gemini-3.8-flash-"), True
    return requested_model, False


def validate_fleet_node_id(node_id: str) -> str:
    """Enforce strict CWE-20 / CWE-78 alphanumeric validation for Fleet & Modal identifiers."""
    if not isinstance(node_id, str) or not node_id or not FLEET_NODE_ID_PATTERN.match(node_id):
        raise ValueError(f"CWE-20 Invalid fleet/workspace identifier: {node_id!r}")
    return node_id


@dataclass(frozen=True, order=True)
class HLCTimestamp:
    """Immutable Hybrid Logical Clock tuple (physical_time, logical_counter)."""

    physical_time: float
    logical_counter: int


class HybridLogicalClock:
    """
    Maintains causal monotonicity across distributed Fleet nodes even when
    physical wall clocks skew by +/-300 seconds.
    """

    def __init__(self, initial_physical: float = 0.0, initial_logical: int = 0) -> None:
        self._last = HLCTimestamp(float(initial_physical), int(initial_logical))

    @property
    def current(self) -> HLCTimestamp:
        return self._last

    def now(self, wall_time: float) -> HLCTimestamp:
        wall = float(wall_time)
        if wall > self._last.physical_time:
            self._last = HLCTimestamp(wall, 0)
        else:
            self._last = HLCTimestamp(self._last.physical_time, self._last.logical_counter + 1)
        return self._last

    def receive(self, remote_hlc: HLCTimestamp, wall_time: float) -> HLCTimestamp:
        wall = float(wall_time)
        max_phys = max(self._last.physical_time, remote_hlc.physical_time, wall)
        if max_phys == self._last.physical_time == remote_hlc.physical_time:
            next_logical = max(self._last.logical_counter, remote_hlc.logical_counter) + 1
        elif max_phys == self._last.physical_time:
            next_logical = self._last.logical_counter + 1
        elif max_phys == remote_hlc.physical_time:
            next_logical = remote_hlc.logical_counter + 1
        else:
            next_logical = 0
        self._last = HLCTimestamp(max_phys, next_logical)
        return self._last


class AuthTokenValidator:
    """
    RFC 7519 section 4.1.4 compliant token validator with a 300-second clock-skew
    leeway envelope to prevent false TokenNotYetValid / TokenExpired errors under 5-min drift.
    """

    def __init__(self, clock_skew_leeway: int = 300) -> None:
        if clock_skew_leeway < 0:
            raise ValueError("clock_skew_leeway must be non-negative")
        self.leeway = float(clock_skew_leeway)

    def validate_token(self, token: Dict[str, Any], current_time: float) -> Tuple[bool, str]:
        now = float(current_time)
        if "nbf" in token:
            nbf = float(token["nbf"])
            if now < (nbf - self.leeway):
                return False, f"TokenNotYetValid: current_time({now}) < nbf({nbf}) - leeway({self.leeway})"
        if "exp" in token:
            exp = float(token["exp"])
            if now >= (exp + self.leeway):
                return False, f"TokenExpired: current_time({now}) >= exp({exp}) + leeway({self.leeway})"
        return True, "Valid"


class DistributedLeaseGuard:
    """
    Monotonic Lamport Epoch Fencing guard preventing dual-primary split-brain lease theft
    when peer node wall clocks drift by 5 minutes.
    """

    def is_valid(
        self,
        grant_epoch_seq: int,
        current_epoch_seq: int,
        monotonic_elapsed: float,
        ttl: float,
    ) -> bool:
        if grant_epoch_seq != current_epoch_seq:
            return False
        if monotonic_elapsed < 0 or ttl <= 0:
            return False
        return float(monotonic_elapsed) < float(ttl)
