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
      or optionally adapt to `gemini-4-argon-*` when `adapt_argon_to_flash=True`.
    - Claude 5.5 models dynamically adapt to Claude 4.6 (`claude-opus-4-6-thinking`, `claude-sonnet-4-6`).
    """
    validate_fleet_node_id(node_id.replace(".", "_"))
    if node_id in GROUP_B_PRO_NODES:
        if requested_model in CLAUDE_ADAPTATION_MAP:
            return CLAUDE_ADAPTATION_MAP[requested_model], True
        if adapt_argon_to_flash and requested_model in DIRECT_ARGON_MODELS:
            return requested_model.replace("gemini-4-argon-", "gemini-4-argon-"), True
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


MAX_ALLOWED_DRIFT_MS: int = 5000


class ClockDriftExceededError(RuntimeError, ValueError):
    """Raised when physical clock drift/skew exceeds maximum allowable bounds."""

    def __init__(self, drift_or_msg: Any, threshold_ms: Optional[int] = None) -> None:
        if threshold_ms is not None:
            drift_ms = int(drift_or_msg)
            thresh = int(threshold_ms)
            super().__init__(
                f"Detected physical clock drift of {drift_ms}ms exceeding threshold {thresh}ms"
            )
            self.drift_ms = drift_ms
            self.threshold_ms = thresh
        else:
            super().__init__(str(drift_or_msg))
            self.drift_ms = 0
            self.threshold_ms = 0


@dataclass
class HLCState:
    physical_time_ms: int
    logical_counter: int


@dataclass(frozen=True)
class HLCClock:
    """Immutable HLC clock value (physical_time_ms, logical_counter)."""

    physical_time_ms: int
    logical_counter: int


class HLCClockGuard:
    """
    Thread-safe monotonic Hybrid Logical Clock guard in milliseconds.
    Supports both local `tick(now_physical_ms)` and remote `update(remote_physical_ms, remote_logical)`.
    Fails closed when physical clock skew exceeds allowable threshold.
    """

    def __init__(
        self,
        initial_physical_ms: int = 0,
        max_drift_ms: int = 1500,
    ) -> None:
        import threading
        import time

        self.max_drift_ms = int(max_drift_ms)
        self._lock = threading.Lock()
        init_phys = int(initial_physical_ms) if initial_physical_ms else int(time.time() * 1000)
        self._last_state = HLCState(physical_time_ms=init_phys, logical_counter=0)
        self._latest_physical_ms = init_phys
        self._logical_counter = 0

    def tick(self, now_physical_ms: int) -> Tuple[int, int]:
        with self._lock:
            last_phys = self._last_state.physical_time_ms
            drift = abs(int(now_physical_ms) - last_phys)

            if drift > MAX_ALLOWED_DRIFT_MS and int(now_physical_ms) < last_phys:
                raise ClockDriftExceededError(drift, MAX_ALLOWED_DRIFT_MS)

            if int(now_physical_ms) > last_phys:
                self._last_state = HLCState(physical_time_ms=int(now_physical_ms), logical_counter=0)
            else:
                self._last_state = HLCState(
                    physical_time_ms=last_phys,
                    logical_counter=self._last_state.logical_counter + 1,
                )
            self._latest_physical_ms = self._last_state.physical_time_ms
            self._logical_counter = self._last_state.logical_counter
            return self._last_state.physical_time_ms, self._last_state.logical_counter

    @property
    def current_state(self) -> HLCState:
        return self._last_state

    def update(self, remote_physical_ms: int, remote_logical: int) -> HLCClock:
        import time

        with self._lock:
            local_now = int(time.time() * 1000)
            skew = abs(local_now - int(remote_physical_ms))
            if skew > self.max_drift_ms:
                raise ClockDriftExceededError(
                    f"Clock drift {skew}ms exceeds maximum tolerated threshold of {self.max_drift_ms}ms"
                )

            if remote_physical_ms > self._latest_physical_ms:
                self._latest_physical_ms = int(remote_physical_ms)
                self._logical_counter = int(remote_logical) + 1
            elif remote_physical_ms == self._latest_physical_ms:
                self._logical_counter = max(self._logical_counter, int(remote_logical)) + 1
            else:
                if local_now > self._latest_physical_ms:
                    self._latest_physical_ms = local_now
                    self._logical_counter = 0
                else:
                    self._logical_counter += 1

            self._last_state = HLCState(
                physical_time_ms=self._latest_physical_ms,
                logical_counter=self._logical_counter,
            )
            return HLCClock(self._latest_physical_ms, self._logical_counter)

    def verify_order(self, earlier: HLCClock, later: HLCClock) -> bool:
        if earlier.physical_time_ms < later.physical_time_ms:
            return True
        if earlier.physical_time_ms == later.physical_time_ms:
            return earlier.logical_counter < later.logical_counter
        return False


class HLCReading:
    """Immutable reading of a node's Hybrid Logical Clock."""

    def __init__(self, physical_ms: int, logical_counter: int, node_id: str) -> None:
        self.physical_ms = int(physical_ms)
        self.logical_counter = int(logical_counter)
        self.node_id = str(node_id)


class ByzantineBoundedHLC:
    """Hardened Hybrid Logical Clock with Byzantine Drift Rejection and 16-bit counter ceiling."""

    MAX_DRIFT_MS: int = 3000
    MAX_LOGICAL_COUNTER: int = 65535

    def __init__(self, node_id: str, clock_func: Any = None) -> None:
        import threading
        import time

        if not node_id:
            raise ValueError("node_id must be non-empty string")
        self.node_id = node_id
        self._clock_func = clock_func or (lambda: int(time.time() * 1000))
        self._lock = threading.Lock()
        self._physical_ms: int = int(self._clock_func())
        self._logical_counter: int = 0

    def read(self) -> HLCReading:
        with self._lock:
            return HLCReading(self._physical_ms, self._logical_counter, self.node_id)

    def tick(self) -> HLCReading:
        with self._lock:
            pt = int(self._clock_func())
            if pt > self._physical_ms:
                self._physical_ms = pt
                self._logical_counter = 0
            else:
                if self._logical_counter >= self.MAX_LOGICAL_COUNTER:
                    self._physical_ms += 1
                    self._logical_counter = 0
                else:
                    self._logical_counter += 1
            return HLCReading(self._physical_ms, self._logical_counter, self.node_id)

    def update(self, remote_hlc: HLCReading) -> Tuple[bool, HLCReading, str]:
        with self._lock:
            local_wall_ms = int(self._clock_func())
            skew = abs(remote_hlc.physical_ms - local_wall_ms)
            if skew > self.MAX_DRIFT_MS:
                reason = (
                    f"Byzantine drift detected: remote physical {remote_hlc.physical_ms}ms "
                    f"deviates {skew}ms from local wall {local_wall_ms}ms "
                    f"(tolerance: {self.MAX_DRIFT_MS}ms)"
                )
                return False, HLCReading(self._physical_ms, self._logical_counter, self.node_id), reason

            new_physical = max(local_wall_ms, self._physical_ms, remote_hlc.physical_ms)
            if new_physical == self._physical_ms and new_physical == remote_hlc.physical_ms:
                self._logical_counter = max(self._logical_counter, remote_hlc.logical_counter) + 1
            elif new_physical == self._physical_ms:
                self._logical_counter += 1
            elif new_physical == remote_hlc.physical_ms:
                self._logical_counter = remote_hlc.logical_counter + 1
            else:
                self._logical_counter = 0

            if self._logical_counter > self.MAX_LOGICAL_COUNTER:
                new_physical += 1
                self._logical_counter = 0

            self._physical_ms = new_physical
            return True, HLCReading(self._physical_ms, self._logical_counter, self.node_id), "OK"


class SovereignHLCGuard:
    """Thread-safe Hybrid Logical Clock implementing non-blocking clock stepping and backward drift clamping."""

    def __init__(self, max_drift_ms: float = 250.0) -> None:
        import threading

        self._max_drift_ms: float = float(max_drift_ms)
        self._lock = threading.Lock()
        self._last_physical_ms: float = 0.0
        self._logical_counter: int = 0

    def get_timestamp(self, physical_now_ms: Optional[float] = None) -> Tuple[float, int]:
        import time

        current_phys = time.time() * 1000.0 if physical_now_ms is None else float(physical_now_ms)
        with self._lock:
            drift = self._last_physical_ms - current_phys
            if drift > self._max_drift_ms:
                raise ClockDriftExceededError(
                    f"Physical clock backwards drift ({drift:.2f}ms) exceeds "
                    f"safety threshold ({self._max_drift_ms:.2f}ms)."
                )
            if current_phys > self._last_physical_ms:
                self._last_physical_ms = current_phys
                self._logical_counter = 0
            else:
                self._logical_counter += 1
            return self._last_physical_ms, self._logical_counter


class HLCShrinkingCounterexampleEngine:
    """Delta-debugging binary shrinker for isolating minimal HLC monotonicity violations."""

    def __init__(self, max_trials: int = 100) -> None:
        self.max_trials = int(max_trials)

    def run_monotonicity_property(
        self,
        clock_fn: Any,
        event_sequence: List[Tuple[int, int, int]],
    ) -> bool:
        prev_p, prev_l = -1, -1
        for wall_time, rem_p, rem_l in event_sequence:
            curr_p, curr_l = clock_fn(wall_time, rem_p, rem_l)
            if prev_p != -1:
                if curr_p < prev_p or (curr_p == prev_p and curr_l <= prev_l):
                    return False
            prev_p, prev_l = curr_p, curr_l
        return True

    def shrink_counterexample(
        self,
        clock_fn: Any,
        failing_sequence: List[Tuple[int, int, int]],
    ) -> List[Tuple[int, int, int]]:
        current_failing = list(failing_sequence)
        step_size = len(current_failing) // 2

        while step_size > 0:
            shrunk_in_pass = False
            for i in range(0, len(current_failing) - step_size + 1, step_size):
                candidate = current_failing[:i] + current_failing[i + step_size :]
                if len(candidate) >= 2 and not self.run_monotonicity_property(clock_fn, candidate):
                    current_failing = candidate
                    shrunk_in_pass = True
                    break
            if not shrunk_in_pass:
                step_size //= 2
            else:
                step_size = min(step_size, len(current_failing) // 2)

        return current_failing

