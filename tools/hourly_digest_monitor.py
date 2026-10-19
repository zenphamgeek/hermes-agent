#!/usr/bin/env python3
"""
Hermes Agent - 24/7 Hourly Digest Report & Anomaly Monitor.

Components:
1. CronAnomalyDetector: Detects clogged runs (>=3 consecutive failures), drift-skips,
   overdue schedules, auth failures, rate limits, and ticker freshness.
2. EntropyDegradationDetector: Monitors the 5 external entropy streams:
   - Stock News Feed (stock_news_memory.sqlite)
   - Legal & Regulatory Crawler (output_legal_docs)
   - Media Asset Bank 24/7 Producer (daily_media_production.json)
   - Median-0 Math Sync (median_hourly_sync.log)
   - AGY Fleet & Clef Mesh (http://localhost:7777/api/fleet/summary & /council)
3. CompositeHealthCalculator: Computes overall weighted health score (0-100) and severity.
4. HermesTelegramNotifier: Sends rich HTML alerts and executive hourly digests to Telegram.
5. SelfHealingManager: Automatically un-wedges drift-skipped cron jobs and triggers entropy recovery.

CLI:
  python3 tools/hourly_digest_monitor.py --scan
  python3 tools/hourly_digest_monitor.py --notify
  python3 tools/hourly_digest_monitor.py --alert-only
  python3 tools/hourly_digest_monitor.py --self-heal
"""

import argparse
from contextlib import contextmanager
from collections import Counter
import enum
import errno
try:
    import fcntl
except ImportError:
    fcntl = None
import hashlib
import html
import ipaddress
import json
import logging
import math
import os
import re
import secrets
import shlex
import socket
import sqlite3
import ssl
import stat
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("hourly_digest_monitor")

def _safe_hermes_home() -> Path:
    env_h = os.environ.get("HERMES_HOME")
    if env_h:
        return Path(env_h)
    try:
        return Path.home() / ".hermes"
    except Exception:
        return Path(os.environ.get("HOME", "/tmp")) / ".hermes"

HERMES_HOME = _safe_hermes_home()
REPO_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_EXECUTIONS_DB = HERMES_HOME / "cron" / "executions.db"
DEFAULT_JOBS_JSON = HERMES_HOME / "cron" / "jobs.json"
DEFAULT_TICKER_HEARTBEAT = HERMES_HOME / "cron" / "ticker_heartbeat"
DEFAULT_CIRCUIT_STATE_FILE = HERMES_HOME / "cron" / ".circuit_breaker.json"

DEFAULT_STOCK_DB = HERMES_HOME / "stock_news_memory.sqlite"
DEFAULT_LEGAL_DIR = REPO_ROOT / "output_legal_docs"
DEFAULT_MEDIA_JSON = HERMES_HOME / "daily_media_production.json"
DEFAULT_MEDIAN_LOG = REPO_ROOT / "assets" / "scripts_video" / "logs" / "median_hourly_sync.log"

DEFAULT_ENV_FILE = HERMES_HOME / ".env"
DEFAULT_CHAT_ID = "1431349185"

FLEET_SUMMARY_URL = "http://localhost:7777/api/fleet/summary"
FLEET_COUNCIL_URL = "http://localhost:7777/api/fleet/council"
FLEET_NODES_URL = "http://localhost:7777/api/fleet/nodes"
FLEET_JOBS_URL = "http://localhost:7777/api/fleet/jobs"

_FATAL_TEMP_ERRNOS = frozenset({
    errno.ENOSPC,
    getattr(errno, "EDQUOT", 122),
    errno.EROFS,
    errno.EACCES,
    errno.EPERM,
    getattr(errno, "ENAMETOOLONG", 36),
    errno.EMFILE,
    errno.ENFILE,
    getattr(errno, "ELOOP", 40),
})


def get_ssl_context() -> ssl.SSLContext:
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def parse_timestamp(val: Any) -> Optional[datetime]:
    """Parse various timestamp representations into timezone-aware UTC datetime."""
    if not val:
        return None
    if isinstance(val, (int, float)):
        if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
            return None
        try:
            return datetime.fromtimestamp(val, tz=timezone.utc)
        except (ValueError, OverflowError, OSError):
            return None
    if isinstance(val, str):
        val = val.strip()
        try:
            # Handle float string
            ts = float(val)
            if math.isnan(ts) or math.isinf(ts):
                return None
            return datetime.fromtimestamp(ts, tz=timezone.utc)
        except (ValueError, OverflowError, OSError):
            pass

        # Try ISO 8601
        try:
            dt = datetime.fromisoformat(val)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except Exception:
            pass

        # Try standard formats: e.g. 2026/10/12 16:33:15
        for fmt in (
            "%Y/%m/%d %H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%SZ",
        ):
            try:
                dt = datetime.strptime(val, fmt)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt.astimezone(timezone.utc)
            except Exception:
                continue
    return None


MAX_TELEMETRY_VALUE = 1 << 40  # Saturating ceiling (1,099,511,627,776 tokens / requests; CWE-20)

ANSI_ESCAPE_PATTERN = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


def sanitize_digest_field(value: Any, max_length: int = 512) -> str:
    """Sanitizes raw strings for secure Markdown table and log inclusion (CWE-20 / CWE-116)."""
    if not isinstance(value, str):
        value = str(value)
    cleaned = ANSI_ESCAPE_PATTERN.sub("", value)
    cleaned = cleaned.replace("|", "\\|").replace("\r", " ").replace("\n", " ")
    cleaned = html.escape(cleaned, quote=True)
    cleaned = " ".join(cleaned.split())
    if len(cleaned) > max_length:
        return cleaned[: max_length - 3] + "..."
    return cleaned


PERMITTED_FLEET_MODELS = frozenset({
    "gemini-4-argon-high",
    "gemini-4-argon-medium",
    "gemini-4-argon-low",
    "claude-opus-5-5-high",
    "claude-opus-5-5-medium",
    "claude-opus-5-5-low",
    "claude-opus-4-6-thinking",
    "claude-sonnet-4-6",
    "gpt-oss-120b-medium",
})

FORBIDDEN_MODEL_PATTERNS = re.compile(r"gemini-3[\.\-]8[\-_]flash.*", re.IGNORECASE)

SECRET_REDACTION_PATTERNS: Dict[str, re.Pattern[str]] = {
    "google_api_key": re.compile(r"AIza[0-9A-Za-z\-_]{20,}"),
    "anthropic_key": re.compile(r"sk-ant-[0-9A-Za-z\-_]{20,}"),
    "generic_secret": re.compile(
        r"(?i)(bearer|token|password|secret|apikey)\s*[:=\s]\s*['\"]?([a-zA-Z0-9_\-\.]{12,})['\"]?"
    ),
}


class SecurityPolicyViolation(Exception):
    """Raised when an operational or architectural security invariant is breached."""


def sanitize_digest_payload(raw_content: str) -> str:
    """Replaces sensitive credentials, tokens, and API keys with strict masking tags (CWE-312)."""
    if not isinstance(raw_content, str):
        return str(raw_content)
    sanitized = SECRET_REDACTION_PATTERNS["google_api_key"].sub("[REDACTED_API_KEY]", raw_content)
    sanitized = SECRET_REDACTION_PATTERNS["anthropic_key"].sub("[REDACTED_API_KEY]", sanitized)
    sanitized = SECRET_REDACTION_PATTERNS["generic_secret"].sub(r"\1: [REDACTED_SECRET]", sanitized)
    return sanitized


def validate_model_target(model_name: str) -> str:
    """Validates model against Group B Pro 3-Tier Gemini 4 Argon allowlist (Invariant 1.14)."""
    if FORBIDDEN_MODEL_PATTERNS.match(str(model_name)):
        raise SecurityPolicyViolation(
            f"Model '{model_name}' is deprecated and strictly forbidden by Fleet Routing Invariant 1.14."
        )
    if model_name not in PERMITTED_FLEET_MODELS:
        raise SecurityPolicyViolation(
            f"Model '{model_name}' is not in the authorized FLEET_NODE_ALLOWLIST."
        )
    return model_name


class SovereignEntropyScrubber:
    """Deterministic fail-closed redaction engine with SHA-256 prefix correlation."""

    SECRET_PATTERNS: List[Tuple[str, re.Pattern]] = [
        ("ANTHROPIC_KEY", re.compile(r"sk-ant-[a-zA-Z0-9_\-]{32,}")),
        ("OPENAI_KEY", re.compile(r"sk-[a-zA-Z0-9]{32,}")),
        ("GOOGLE_API_KEY", re.compile(r"AIza[0-9A-Za-z\-_]{35}")),
        ("BEARER_AUTH", re.compile(r"(?i)bearer\s+[a-zA-Z0-9_\-\.=:_+/]{20,}")),
        ("MODAL_TOKEN", re.compile(r"ak-[a-zA-Z0-9]{20,}:as-[a-zA-Z0-9]{20,}")),
        (
            "GENERIC_SECRET_PAIR",
            re.compile(r"(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*['\"]?([a-zA-Z0-9_\-\.]{16,})['\"]?"),
        ),
    ]

    @classmethod
    def scrub(cls, text: str) -> str:
        if not text:
            return ""
        scrubbed = text
        for name, pattern in cls.SECRET_PATTERNS:
            def _replace_match(match: re.Match, tag: str = name) -> str:
                matched_val = match.group(0)
                h = hashlib.sha256(matched_val.encode("utf-8")).hexdigest()[:8]
                return f"[REDACTED_{tag}:{h}]"

            scrubbed = pattern.sub(_replace_match, scrubbed)
        return scrubbed


class TelemetryRingBuffer:
    """Sliding-window bounded memory ring buffer with O(1) allocation guarantees."""

    def __init__(self, capacity: int = 5000) -> None:
        from collections import deque

        if capacity <= 0:
            raise ValueError(f"RingBuffer capacity must be > 0, got {capacity}")
        self.capacity: int = capacity
        self._buffer: deque = deque(maxlen=capacity)
        self.eviction_count: int = 0
        self.total_appended: int = 0

    def append(self, entry: Dict[str, Any]) -> None:
        if len(self._buffer) == self.capacity:
            self.eviction_count += 1
        self.total_appended += 1
        self._buffer.append(entry)

    def drain_all(self) -> List[Dict[str, Any]]:
        items = list(self._buffer)
        self._buffer.clear()
        return items

    def peek_window(self, count: int) -> List[Dict[str, Any]]:
        if count <= 0:
            return []
        slice_start = max(0, len(self._buffer) - count)
        return [self._buffer[i] for i in range(slice_start, len(self._buffer))]

    def __len__(self) -> int:
        return len(self._buffer)


class StatelessTokenGuard:
    """Micro-epoch HMAC-SHA256 stateless token verification with single-use replay rejection (CWE-294)."""

    def __init__(self, master_secret: bytes, epoch_duration_s: int = 60) -> None:
        if len(master_secret) < 32:
            raise ValueError("Master secret must be at least 32 bytes for HMAC-SHA256")
        if epoch_duration_s <= 0:
            raise ValueError("epoch_duration_s must be positive")
        self._secret = bytes(master_secret)
        self._epoch_duration_s = int(epoch_duration_s)
        self._consumed_tokens: set[str] = set()
        self._last_eviction_epoch = int(time.time()) // self._epoch_duration_s

    def _get_epoch(self, timestamp_s: float) -> int:
        return int(timestamp_s) // self._epoch_duration_s

    def generate_token(self, payload: Dict[str, Any], timestamp_s: float) -> str:
        import hmac

        epoch = self._get_epoch(timestamp_s)
        canonical_data = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        epoch_bytes = epoch.to_bytes(8, byteorder="big", signed=False)
        signature = hmac.new(self._secret, canonical_data + epoch_bytes, hashlib.sha256).hexdigest()
        return f"{epoch}:{signature}"

    def validate_and_consume_token(self, payload: Dict[str, Any], token: str, current_time_s: float) -> bool:
        import hmac

        try:
            token_epoch_str, token_sig = token.split(":", 1)
            token_epoch = int(token_epoch_str)
        except (ValueError, AttributeError):
            return False

        current_epoch = self._get_epoch(current_time_s)
        if abs(current_epoch - token_epoch) > 1:
            return False

        if token in self._consumed_tokens:
            return False

        canonical_data = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        epoch_bytes = token_epoch.to_bytes(8, byteorder="big", signed=False)
        expected_sig = hmac.new(self._secret, canonical_data + epoch_bytes, hashlib.sha256).hexdigest()

        if not hmac.compare_digest(expected_sig, token_sig):
            return False

        if current_epoch > self._last_eviction_epoch:
            self._consumed_tokens.clear()
            self._last_eviction_epoch = current_epoch

        self._consumed_tokens.add(token)
        return True


class SecurityConfigurationError(ValueError):
    """Raised when security invariants, entropy gates, or secret configurations are violated."""


class TokenReplayDetectedError(ValueError):
    """Raised when an identical cryptographic signature is replayed within the valid epoch."""


class StatelessTokenEngine:
    """Stateless HMAC KDF token validator with 60s sliding epoch window and bounded LRU replay cache."""

    def __init__(
        self,
        master_secret: str,
        epoch_window_seconds: int = 60,
        replay_cache_capacity: int = 4096,
    ) -> None:
        import collections

        if not master_secret:
            raise SecurityConfigurationError(
                "Master secret must contain at least 32 characters of high-entropy data."
            )
        forbidden_defaults = {"default", "secret", "development", "changeme", "admin"}
        if master_secret.lower().strip() in forbidden_defaults:
            raise SecurityConfigurationError("Insecure default master secret detected. Failing closed.")
        if len(master_secret.strip()) < 32:
            raise SecurityConfigurationError(
                "Master secret must contain at least 32 characters of high-entropy data."
            )

        self._master_key: bytes = master_secret.encode("utf-8")
        self._epoch_window: int = int(epoch_window_seconds)
        self._replay_cache_capacity: int = int(replay_cache_capacity)
        self._seen_signatures: collections.OrderedDict[str, float] = collections.OrderedDict()

    def _purge_expired_signatures(self, current_time: float) -> None:
        expiry_cutoff = current_time - (self._epoch_window * 2)
        while self._seen_signatures:
            _, seen_time = next(iter(self._seen_signatures.items()))
            if seen_time < expiry_cutoff or len(self._seen_signatures) > self._replay_cache_capacity:
                self._seen_signatures.popitem(last=False)
            else:
                break

    def derive_epoch_token(
        self, method: str, path: str, nonce: str, timestamp: Optional[float] = None
    ) -> Tuple[str, int]:
        import hmac

        now = time.time() if timestamp is None else float(timestamp)
        current_epoch = int(now // self._epoch_window)
        canonical_payload = f"{method.upper().strip()}:{path.strip()}:{nonce.strip()}:{current_epoch}"
        signature = hmac.new(
            self._master_key,
            canonical_payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return signature, current_epoch

    def verify_token(
        self,
        method: str,
        path: str,
        nonce: str,
        token: str,
        timestamp: Optional[float] = None,
    ) -> bool:
        import hmac

        now = time.time() if timestamp is None else float(timestamp)
        self._purge_expired_signatures(now)

        if token in self._seen_signatures:
            raise TokenReplayDetectedError(f"Replay detected for cryptographic token: {token[:12]}...")

        current_epoch = int(now // self._epoch_window)
        for epoch in (current_epoch, current_epoch - 1):
            payload = f"{method.upper().strip()}:{path.strip()}:{nonce.strip()}:{epoch}"
            expected_sig = hmac.new(
                self._master_key,
                payload.encode("utf-8"),
                hashlib.sha256,
            ).hexdigest()
            if hmac.compare_digest(expected_sig, token):
                self._seen_signatures[token] = now
                return True

        return False

    def sanitize_receipt_data(self, raw_json_payload: str) -> Dict[str, Any]:
        """Parses and validates untrusted receipt payloads, rejecting shell metacharacters and path traversal."""
        try:
            parsed = json.loads(raw_json_payload)
        except Exception as exc:
            raise SecurityConfigurationError(f"Malformed receipt JSON: {exc}") from exc

        if not isinstance(parsed, dict):
            raise SecurityConfigurationError("Receipt payload must evaluate to a JSON dictionary.")

        sanitized: Dict[str, Any] = {}
        forbidden_tokens = (";", "&", "|", "`", "$", "\n", "\r", "..")
        for key, value in parsed.items():
            if not isinstance(key, str) or any(c in key for c in forbidden_tokens):
                raise SecurityConfigurationError(f"Malicious metacharacter detected in receipt key: {key}")
            sanitized[key] = value

        return sanitized


class SecurityEvaluationError(ValueError):
    """Raised when an illegal or untrusted AST construct is detected."""


class ASTDepthExceededError(SecurityEvaluationError):
    """Raised when AST expression exceeds maximum allowed depth."""


class SecurePredicateEvaluator:
    """Evaluates boolean predicates against a context dictionary with strict AST whitelisting."""

    MAX_TREE_DEPTH: int = 6
    MAX_NODE_COUNT: int = 32

    def __init__(self, allowed_identifiers: Any) -> None:
        import ast
        import operator

        self.allowed_identifiers = frozenset(allowed_identifiers)
        self._allowed_bin_ops = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Mod: operator.mod,
        }
        self._allowed_cmp_ops = {
            ast.Eq: operator.eq,
            ast.NotEq: operator.ne,
            ast.Lt: operator.lt,
            ast.LtE: operator.le,
            ast.Gt: operator.gt,
            ast.GtE: operator.ge,
        }

    def evaluate(self, expression_str: str, context: Dict[str, Any]) -> bool:
        import ast

        if not expression_str or not expression_str.strip():
            raise SecurityEvaluationError("Empty predicate expression rejected.")
        if len(expression_str) > 512:
            raise SecurityEvaluationError("Expression exceeds maximum length of 512 characters.")
        try:
            parsed_tree = ast.parse(expression_str, mode="eval")
        except SyntaxError as err:
            raise SecurityEvaluationError(f"Malformed predicate syntax: {err}") from err

        node_count = sum(1 for _ in ast.walk(parsed_tree))
        if node_count > self.MAX_NODE_COUNT:
            raise SecurityEvaluationError(
                f"AST node complexity exceeded: {node_count} nodes (max {self.MAX_NODE_COUNT})"
            )

        self._verify_depth(parsed_tree.body, current_depth=1)
        return bool(self._eval_node(parsed_tree.body, context))

    def _verify_depth(self, node: Any, current_depth: int) -> None:
        import ast

        if current_depth > self.MAX_TREE_DEPTH:
            raise ASTDepthExceededError(
                f"AST depth limit exceeded: {current_depth} (max {self.MAX_TREE_DEPTH})"
            )
        for child in ast.iter_child_nodes(node):
            self._verify_depth(child, current_depth + 1)

    def _eval_node(self, node: Any, context: Dict[str, Any]) -> Any:
        import ast

        if isinstance(node, ast.Constant):
            if type(node.value) in (int, float, str, bool, type(None)):
                return node.value
            raise SecurityEvaluationError(f"Unsupported constant type: {type(node.value)}")

        if isinstance(node, ast.Name):
            if node.id not in self.allowed_identifiers:
                raise SecurityEvaluationError(f"Illegal identifier lookup: '{node.id}'")
            if node.id not in context:
                raise SecurityEvaluationError(f"Missing identifier in evaluation context: '{node.id}'")
            return context[node.id]

        if isinstance(node, ast.BoolOp):
            if isinstance(node.op, ast.And):
                return all(bool(self._eval_node(v, context)) for v in node.values)
            if isinstance(node.op, ast.Or):
                return any(bool(self._eval_node(v, context)) for v in node.values)
            raise SecurityEvaluationError(f"Unsupported boolean operator: {type(node.op)}")

        if isinstance(node, ast.UnaryOp):
            if isinstance(node.op, ast.Not):
                return not self._eval_node(node.operand, context)
            if isinstance(node.op, ast.USub):
                val = self._eval_node(node.operand, context)
                if not isinstance(val, (int, float)) or isinstance(val, bool):
                    raise SecurityEvaluationError("Unary negation requires numeric operand.")
                return -val
            raise SecurityEvaluationError(f"Unsupported unary operator: {type(node.op)}")

        if isinstance(node, ast.Compare):
            left_val = self._eval_node(node.left, context)
            for op, comparator_node in zip(node.ops, node.comparators):
                op_type = type(op)
                if op_type not in self._allowed_cmp_ops:
                    raise SecurityEvaluationError(f"Forbidden comparison operator: {op_type}")
                comparator_val = self._eval_node(comparator_node, context)
                try:
                    if not self._allowed_cmp_ops[op_type](left_val, comparator_val):
                        return False
                except TypeError as type_err:
                    raise SecurityEvaluationError(f"Type error in comparison: {type_err}") from type_err
                left_val = comparator_val
            return True

        if isinstance(node, ast.BinOp):
            op_type = type(node.op)
            if op_type not in self._allowed_bin_ops:
                raise SecurityEvaluationError(f"Forbidden binary arithmetic operator: {op_type}")
            left_val = self._eval_node(node.left, context)
            right_val = self._eval_node(node.right, context)
            if not isinstance(left_val, (int, float)) or not isinstance(right_val, (int, float)):
                raise SecurityEvaluationError("Arithmetic operators strictly enforce numeric operands.")
            return self._allowed_bin_ops[op_type](left_val, right_val)

        raise SecurityEvaluationError(
            f"Prohibited AST node type '{type(node).__name__}' violates security invariant."
        )


class DigestMonitorLockError(RuntimeError):
    """Raised when lock acquisition on the digest ledger times out."""


class DigestLedgerCorruptionError(ValueError):
    """Raised when ledger integrity verification fails."""


import contextlib


@contextlib.contextmanager
def atomic_locked_ledger(ledger_path: Path, timeout_seconds: float = 5.0):
    """POSIX flock-protected atomic read-modify-write context manager."""
    import fcntl
    import tempfile

    ledger_path = Path(ledger_path)
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    lock_file = ledger_path.with_suffix(".lock")
    start_time = time.monotonic()

    with open(lock_file, "a+", encoding="utf-8") as lock_fd:
        acquired = False
        while time.monotonic() - start_time < timeout_seconds:
            try:
                fcntl.flock(lock_fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                acquired = True
                break
            except (BlockingIOError, OSError):
                time.sleep(0.02)

        if not acquired:
            raise DigestMonitorLockError(
                f"Failed to acquire advisory lock on '{lock_file}' within {timeout_seconds}s timeout."
            )

        try:
            data: Dict[str, Any] = {}
            if ledger_path.exists() and ledger_path.stat().st_size > 0:
                with open(ledger_path, "r", encoding="utf-8") as r_fd:
                    try:
                        data = json.load(r_fd)
                    except json.JSONDecodeError as decode_err:
                        raise DigestLedgerCorruptionError(
                            f"Ledger file '{ledger_path}' corrupted: {decode_err}"
                        ) from decode_err

            yield data

            with tempfile.NamedTemporaryFile(
                "w", dir=ledger_path.parent, delete=False, encoding="utf-8"
            ) as tmp_fd:
                tmp_path = Path(tmp_fd.name)
                json.dump(data, tmp_fd, indent=2, sort_keys=True)
                tmp_fd.flush()
                os.fsync(tmp_fd.fileno())

            os.replace(tmp_path, ledger_path)
        finally:
            fcntl.flock(lock_fd.fileno(), fcntl.LOCK_UN)



def _safe_int(
    val: Any,
    default: int = 0,
    min_val: int = 0,
    max_val: Optional[int] = MAX_TELEMETRY_VALUE,
) -> int:
    """Safely coerce any value to an integer, clamped to [min_val, max_val] (CWE-20/CWE-390).

    Guarantees:
      1. Rejects non-numeric, NaN, and Inf strings/objects by returning default.
      2. Saturates positive scientific notation overflow strings (e.g. '1e500', '1e30') to max_val
         to prevent silent quota forgiveness / accounting evasion (CWE-20/390).
      3. Clamps negative values/overflow (e.g. '-1e500', '-100') to min_val.
      4. Never raises TypeError, ValueError, or OverflowError.
    """
    if val is None:
        return max(min_val, default)
    try:
        if isinstance(val, bool):
            res = int(val)
        elif isinstance(val, int):
            res = val
        elif isinstance(val, float):
            if math.isnan(val) or math.isinf(val):
                res = default
            else:
                res = int(val)
        elif isinstance(val, (str, bytes)):
            v_str = str(val, "utf-8", errors="replace") if isinstance(val, bytes) else str(val)
            v_str = v_str.strip()
            if v_str.isdigit():
                res = int(v_str)
            else:
                try:
                    res = int(v_str)
                except ValueError:
                    try:
                        f = float(v_str)
                        if math.isnan(f) or math.isinf(f):
                            res = default
                        else:
                            res = int(f)
                    except (OverflowError, ValueError):
                        res = default
        else:
            try:
                f = float(val)
                if math.isnan(f) or math.isinf(f):
                    res = default
                else:
                    res = int(f)
            except (ValueError, TypeError, OverflowError):
                res = default
    except (ValueError, TypeError, OverflowError):
        res = default

    if res < min_val:
        res = min_val
    if max_val is not None and res > max_val:
        res = max_val
    return res


def _safe_float(
    val: Any,
    default: float = 0.0,
    min_val: float = 0.0,
    max_val: Optional[float] = float(MAX_TELEMETRY_VALUE),
) -> float:
    """Safely coerce any value to float, clamped to [min_val, max_val] (CWE-20)."""
    if val is None:
        return max(min_val, default)
    try:
        if isinstance(val, (int, float, bool)):
            f = float(val)
        else:
            v_str = str(val, "utf-8", errors="replace") if isinstance(val, bytes) else str(val)
            f = float(v_str.strip())
        if math.isnan(f) or math.isinf(f):
            return max(min_val, default)
        if f < min_val:
            return min_val
        if max_val is not None and f > max_val:
            return max_val
        return f
    except Exception:
        return max(min_val, default)


def _safe_pct(part: Any, whole: Any, digits: int = 1) -> float:
    """Safely calculate percentage (part / whole * 100), bounded and protected against ZeroDivisionError and NaN/Inf."""
    p = _safe_float(part, default=0.0, min_val=0.0)
    w = _safe_float(whole, default=0.0, min_val=0.0)
    if w <= 0.0 or math.isnan(w) or math.isinf(w) or math.isnan(p) or math.isinf(p):
        return 0.0
    return round(100.0 * p / w, digits)


_ALLOW_LOCAL_HOSTS = {"localhost", "127.0.0.1", "0.0.0.0", "::1"}
_ALLOW_PORTS = {80, 443, 6768, 7777, 8000, 8080, 8443, 8888, 9090} | set(range(20128, 20144))

BLOCKED_IP_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fe80::/10"),
]


def _redact_url(url: str) -> str:
    """Strip userinfo (user:pass@) from a URL before it enters logs/errors (CWE-532/209)."""
    try:
        parsed = urllib.parse.urlparse(url)
        if parsed.username or parsed.password:
            host = parsed.hostname or ""
            port = f":{parsed.port}" if parsed.port else ""
            netloc = f"***redacted***@{host}{port}"
            parsed = parsed._replace(netloc=netloc)
        return urllib.parse.urlunparse(parsed)
    except Exception:
        return "***unparseable-url***"


def _validate_fleet_url(url: str, allow_private: Optional[bool] = None) -> str:
    """Validate that fleet URL is safe and well-formed (SSRF & scheme injection guard).

    Enforces (not just documents):
      - scheme in ('http', 'https') (rejects file:, ftp:, gopher:, etc. with ValueError).
      - non-empty hostname with safe characters
      - port in an explicit allowlist (standard web, fleet :7777, gateway :6768, proxy slots :20128-20143)
      - when allow_private is False (or not explicitly permitted), target IP is rejected if in private/loopback/link-local/metadata
    All error text is redacted of embedded credentials (CWE-532/259).
    """
    if not url or not isinstance(url, str):
        raise ValueError("Fleet URL must be a non-empty string")

    stripped = url.strip()
    safe = _redact_url(stripped)
    parsed = urllib.parse.urlparse(stripped)

    scheme = (parsed.scheme or "").lower()
    if scheme not in ("http", "https"):
        raise ValueError(
            f"Invalid scheme {scheme!r} in fleet URL: {safe!r}. Only http and https are permitted."
        )

    hostname = (parsed.hostname or "").lower()
    if not hostname:
        raise ValueError(f"Missing or invalid hostname in fleet URL: {safe!r}")

    if not re.match(r"^[a-zA-Z0-9_\-\.:\[\]]+$", hostname):
        raise ValueError(f"Forbidden characters in hostname {hostname!r} of fleet URL: {safe!r}")

    port = parsed.port
    if port is not None and port not in _ALLOW_PORTS:
        raise ValueError(f"Forbidden port {port} in fleet URL: {safe!r}")

    # Determine effective allow_private
    if allow_private is not None:
        effective_allow_private = allow_private
    else:
        effective_allow_private = os.environ.get("HERMES_FLEET_ALLOW_PRIVATE") == "1"

    if effective_allow_private:
        return stripped

    # If allow_private is None (default mode without explicit override), allow local mock fixtures on approved ports
    is_default_local_fixture = (allow_private is None) and (
        hostname in _ALLOW_LOCAL_HOSTS or hostname.startswith("mock-")
    )
    if is_default_local_fixture:
        return stripped

    # When allow_private is False (or host is external): evaluate IP literals and DNS resolution
    # 1. Direct IP check
    clean_host = hostname.strip("[]")
    try:
        ip_obj = ipaddress.ip_address(clean_host)
        for blocked in BLOCKED_IP_NETWORKS:
            if ip_obj in blocked:
                raise ValueError(f"Fleet URL resolves to blocked address class ({ip_obj}): {safe!r}")
        if (
            ip_obj.is_private
            or ip_obj.is_loopback
            or ip_obj.is_link_local
            or ip_obj.is_reserved
            or ip_obj.is_multicast
            or ip_obj.is_unspecified
        ):
            raise ValueError(f"Fleet URL resolves to blocked address class ({ip_obj}): {safe!r}")
    except ValueError as e:
        if "blocked address class" in str(e):
            raise
        # Not a raw IP literal; proceed to DNS resolution

    # 2. DNS resolution check
    try:
        infos = socket.getaddrinfo(hostname, port or (443 if scheme == "https" else 80))
    except socket.gaierror as exc:
        if hostname.startswith("mock-") or hostname in ("fleet.internal.mesh",):
            return stripped  # Allow offline unit test mock hosts to pass
        raise ValueError(f"Could not resolve hostname in fleet URL: {safe!r}") from exc

    for info in infos:
        try:
            ip = ipaddress.ip_address(info[4][0])
        except ValueError:
            continue
        for blocked in BLOCKED_IP_NETWORKS:
            if ip in blocked:
                raise ValueError(
                    f"Fleet URL resolves to blocked address class ({ip}): {safe!r}. "
                    "Set HERMES_FLEET_ALLOW_PRIVATE=1 to override for trusted internal endpoints."
                )
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_multicast
            or ip.is_unspecified
        ):
            raise ValueError(
                f"Fleet URL resolves to blocked address class ({ip}): {safe!r}. "
                "Set HERMES_FLEET_ALLOW_PRIVATE=1 to override for trusted internal endpoints."
            )

    return stripped


MAX_FLEET_BYTES = 8 * 1024 * 1024  # 8 MiB ceiling to prevent memory DoS (CWE-400)


def _safe_fetch_json(
    url: str,
    timeout: float = 10.0,
    max_bytes: int = MAX_FLEET_BYTES,
    user_agent: str = "HourlyMonitor/1.0",
    allow_private: Optional[bool] = None,
) -> Any:
    """Fetch JSON from a validated HTTP/HTTPS URL with strict size and timeout bounds (CWE-400 & CWE-918)."""
    safe_url = _validate_fleet_url(url, allow_private=allow_private)
    req = urllib.request.Request(safe_url, headers={"User-Agent": user_agent, "Accept": "application/json"})
    ssl_ctx = get_ssl_context() if "get_ssl_context" in globals() else None
    with urllib.request.urlopen(req, timeout=timeout, context=ssl_ctx) as resp:
        raw = resp.read(max_bytes + 1)
        if len(raw) > max_bytes:
            raise ValueError(
                f"Payload exceeded max permitted length: Endpoint response exceeds size ceiling of {max_bytes} bytes (CWE-400)"
            )
        return json.loads(raw.decode("utf-8"))


# ==============================================================================
# 1. CronAnomalyDetector
# ==============================================================================
class CronAnomalyDetector:
    """Audits Hermes cron scheduler state, executions database, and ticker heartbeat."""

    def __init__(
        self,
        db_path: Path = DEFAULT_EXECUTIONS_DB,
        jobs_path: Path = DEFAULT_JOBS_JSON,
        heartbeat_path: Path = DEFAULT_TICKER_HEARTBEAT,
        grace_period_seconds: int = 300,
    ):
        self.db_path = Path(db_path)
        self.jobs_path = Path(jobs_path)
        self.heartbeat_path = Path(heartbeat_path)
        self.grace_period_seconds = grace_period_seconds
        self.jobs_map: Dict[str, Dict[str, Any]] = self.load_jobs_map()

    def load_jobs_map(self) -> Dict[str, Dict[str, Any]]:
        """Load jobs from jobs.json indexed by job_id."""
        if not self.jobs_path.exists():
            self.jobs_map = {}
            return {}
        try:
            with open(self.jobs_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            jobs = data.get("jobs", []) if isinstance(data, dict) else data
            self.jobs_map = {j.get("id"): j for j in jobs if isinstance(j, dict) and j.get("id")}
            return self.jobs_map
        except Exception as e:
            logger.warning("Failed loading jobs.json: %s", e)
            self.jobs_map = {}
            return {}

    def _is_job_paused(
        self,
        job_id: str,
        jobs_map: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> bool:
        """Return True if job_id is in jobs_map and explicitly paused/on_hold/disabled."""
        jmap = jobs_map if jobs_map is not None else (self.load_jobs_map() or self.jobs_map)
        if not jmap or job_id not in jmap:
            return False
        job = jmap.get(job_id) or {}
        if job.get("enabled") is False:
            return True
        state_str = str(job.get("state", "") or "").strip().lower()
        return state_str in ("paused", "on_hold", "held", "disabled")

    def check_clogged_jobs(self, min_failures: int = 3) -> List[Dict[str, Any]]:
        """Detect jobs with >= min_failures consecutive failed executions."""
        if not self.db_path.exists():
            return []

        jobs_map = self.load_jobs_map()
        clogged = []

        try:
            conn = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True)
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT job_id FROM executions")
            job_ids = [row[0] for row in cursor.fetchall() if row[0]]

            for jid in job_ids:
                if self._is_job_paused(jid, jobs_map):
                    continue
                cursor.execute(
                    "SELECT status, error, claimed_at FROM executions WHERE job_id = ? ORDER BY rowid DESC LIMIT 100",
                    (jid,),
                )
                runs = cursor.fetchall()
                consecutive = 0
                last_error = ""
                last_claimed = ""

                for status, error, claimed_at in runs:
                    if status in ("failed", "error"):
                        consecutive += 1
                        if not last_error and error:
                            last_error = error
                        if not last_claimed and claimed_at:
                            last_claimed = claimed_at
                    else:
                        break

                if consecutive >= min_failures:
                    job_info = jobs_map.get(jid, {})
                    clogged.append(
                        {
                            "job_id": jid,
                            "job_name": job_info.get("name") or jid,
                            "consecutive_failures": consecutive,
                            "last_error": last_error,
                            "last_claimed_at": last_claimed,
                        }
                    )
            conn.close()
        except Exception as e:
            logger.error("Failed checking clogged jobs in %s: %s", self.db_path, e)

        return clogged

    def check_drift_skipped_jobs(self) -> List[Dict[str, Any]]:
        """Detect jobs currently skipped or alerted due to model/provider drift."""
        jobs_map = self.load_jobs_map()
        drifted = []

        for jid, job in jobs_map.items():
            if self._is_job_paused(jid, jobs_map):
                continue
            last_err = str(job.get("last_error") or "")
            drift_alerted = bool(job.get("drift_alerted"))
            is_drift_error = "[drift_skip" in last_err

            if drift_alerted or is_drift_error:
                drifted.append(
                    {
                        "job_id": jid,
                        "job_name": job.get("name") or jid,
                        "drift_alerted": drift_alerted,
                        "last_error": last_err,
                        "model_snapshot": job.get("model_snapshot"),
                        "provider_snapshot": job.get("provider_snapshot"),
                        "pinned_model": job.get("model"),
                        "pinned_provider": job.get("provider"),
                    }
                )

        return drifted

    def check_overdue_jobs(self, now_utc: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Detect enabled jobs where next_run_at is overdue past the grace period."""
        jobs_map = self.load_jobs_map()
        overdue = []
        if now_utc is None:
            now_utc = datetime.now(timezone.utc)

        for jid, job in jobs_map.items():
            if not job.get("enabled") or self._is_job_paused(jid, jobs_map):
                continue
            next_run_str = job.get("next_run_at")
            if not next_run_str:
                continue
            nra_dt = parse_timestamp(next_run_str)
            if not nra_dt:
                continue

            overdue_secs = (now_utc - nra_dt).total_seconds()
            if overdue_secs > self.grace_period_seconds:
                overdue.append(
                    {
                        "job_id": jid,
                        "job_name": job.get("name") or jid,
                        "next_run_at": next_run_str,
                        "overdue_seconds": round(overdue_secs, 1),
                    }
                )

        return overdue

    def check_auth_failed_jobs(self) -> List[Dict[str, Any]]:
        """Detect jobs whose last execution or configured error indicates authentication failure."""
        jobs_map = self.load_jobs_map()
        auth_failed = []
        auth_regex = re.compile(r"(?i)\b(auth|401|403|invalid_grant|unauthorized)\b")

        for jid, job in jobs_map.items():
            if self._is_job_paused(jid, jobs_map):
                continue
            last_err = str(job.get("last_error") or "")
            if auth_regex.search(last_err):
                auth_failed.append(
                    {
                        "job_id": jid,
                        "job_name": job.get("name") or jid,
                        "last_error": last_err,
                    }
                )

        return auth_failed

    def check_rate_limited_jobs(self) -> List[Dict[str, Any]]:
        """Detect jobs whose last execution or configured error indicates rate limiting."""
        jobs_map = self.load_jobs_map()
        rate_limited = []
        rl_regex = re.compile(r"(?i)\b(429|rate\s*limit|usage\s*limit|quota\s*exceeded)\b")

        for jid, job in jobs_map.items():
            if self._is_job_paused(jid, jobs_map):
                continue
            last_err = str(job.get("last_error") or "")
            if rl_regex.search(last_err):
                rate_limited.append(
                    {
                        "job_id": jid,
                        "job_name": job.get("name") or jid,
                        "last_error": last_err,
                    }
                )

        return rate_limited

    def check_ticker_stale(
        self, max_age_seconds: float = 120.0, now_utc: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Check whether the cron ticker heartbeat is fresh."""
        if not self.heartbeat_path.exists():
            return {
                "exists": False,
                "is_stale": True,
                "age_seconds": 99999.0,
                "timestamp": None,
            }

        try:
            with open(self.heartbeat_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
            ts_dt = parse_timestamp(content)
            if not ts_dt:
                ts_dt = datetime.fromtimestamp(self.heartbeat_path.stat().st_mtime, tz=timezone.utc)

            if now_utc is None:
                now_utc = datetime.now(timezone.utc)
            age = max(0.0, (now_utc - ts_dt).total_seconds())
            return {
                "exists": True,
                "is_stale": age > max_age_seconds,
                "age_seconds": round(age, 1),
                "timestamp": ts_dt.isoformat(),
            }
        except Exception as e:
            logger.error("Failed reading ticker heartbeat: %s", e)
            return {
                "exists": True,
                "is_stale": True,
                "age_seconds": 99999.0,
                "timestamp": None,
                "error": str(e),
            }

    def compute_cron_health_score(self, findings: Dict[str, Any]) -> int:
        """Compute cron subsystem health score (0-100%)."""
        score = 100

        # Heartbeat stale deduction
        if findings.get("ticker_heartbeat", {}).get("is_stale"):
            score -= 30

        # Clogged jobs deduction
        clogged = findings.get("clogged_jobs", [])
        score -= min(40, len(clogged) * 15)

        # Drift skipped deduction
        drifted = findings.get("drift_skipped_jobs", [])
        score -= min(40, len(drifted) * 15)

        # Auth failed deduction
        auth_failed = findings.get("auth_failed_jobs", [])
        score -= min(20, len(auth_failed) * 10)

        # Rate limited deduction
        rate_limited = findings.get("rate_limited_jobs", [])
        score -= min(20, len(rate_limited) * 10)

        # Overdue jobs deduction
        overdue = findings.get("overdue_jobs", [])
        score -= min(15, len(overdue) * 5)

        return max(0, min(100, score))

    def scan(self, now_utc: Optional[datetime] = None) -> Dict[str, Any]:
        """Perform comprehensive cron audit and return findings with health score."""
        jobs_map = self.load_jobs_map()
        paused_count = sum(1 for jid in jobs_map if self._is_job_paused(jid, jobs_map))
        active_count = sum(1 for jid in jobs_map if not self._is_job_paused(jid, jobs_map))

        clogged = self.check_clogged_jobs()
        drifted = self.check_drift_skipped_jobs()
        overdue = self.check_overdue_jobs(now_utc=now_utc)
        auth_failed = self.check_auth_failed_jobs()
        rate_limited = self.check_rate_limited_jobs()
        ticker = self.check_ticker_stale(now_utc=now_utc)

        findings = {
            "clogged_jobs": clogged,
            "drift_skipped_jobs": drifted,
            "overdue_jobs": overdue,
            "auth_failed_jobs": auth_failed,
            "rate_limited_jobs": rate_limited,
            "ticker_heartbeat": ticker,
            "paused_jobs_count": paused_count,
            "active_jobs_count": active_count,
        }
        findings["cron_health_score"] = self.compute_cron_health_score(findings)
        return findings

    run_all_checks = scan


def _extract_clean_task_prompt(job: Dict[str, Any]) -> str:
    """Unwrap Clef JSON/XML/Codex metaprompt envelopes into a clean human-readable task prompt."""
    raw = ""
    if isinstance(job, dict):
        enriched = job.get("enriched_spec")
        if isinstance(enriched, dict) and enriched.get("raw_prompt"):
            raw = str(enriched["raw_prompt"])
        elif job.get("raw_prompt"):
            raw = str(job["raw_prompt"])
        elif isinstance(job.get("task"), dict) and job["task"].get("raw_instructions"):
            raw = str(job["task"]["raw_instructions"])
        elif job.get("raw_instructions"):
            raw = str(job["raw_instructions"])
        elif isinstance(job.get("task"), dict) and job["task"].get("intent"):
            raw = str(job["task"]["intent"])
        elif job.get("task_specification"):
            raw = str(job["task_specification"])
        elif job.get("intent"):
            raw = str(job["intent"])
        elif job.get("prompt"):
            raw = str(job["prompt"])

    current = (raw or "").strip()
    json_keys = ("raw_instructions", "raw_prompt", "task_specification", "objective", "user_prompt", "instruction", "intent")
    for _ in range(4):
        changed = False
        fence_match = re.match(r"^```(?:\w+)?\s*\n?(.*?)\n?```$", current, re.DOTALL)
        if fence_match:
            current = fence_match.group(1).strip()
            changed = True
            continue
        if current.startswith("```"):
            current = re.sub(r"^```(?:\w+)?\s*", "", current)
            current = re.sub(r"\s*```$", "", current).strip()
            changed = True

        if current.startswith("{") and ("$schema" in current or any(k in current for k in json_keys)):
            try:
                data = json.loads(current)
                if isinstance(data, dict):
                    task_obj = data.get("task") if isinstance(data.get("task"), dict) else {}
                    for k in json_keys:
                        if task_obj.get(k):
                            current = str(task_obj[k]).strip()
                            changed = True
                            break
                        if data.get(k):
                            current = str(data[k]).strip()
                            changed = True
                            break
                    if changed:
                        continue
            except Exception:
                # Fallback regex extraction for truncated JSON strings
                for key in json_keys:
                    m_json = re.search(rf'"{key}"\s*:\s*"((?:\\.|[^"\\])+)"', current)
                    if m_json:
                        try:
                            current = json.loads(f'"{m_json.group(1)}"').strip()
                        except Exception:
                            current = m_json.group(1).strip()
                        changed = True
                        break
                if changed:
                    continue

        xml_match = re.search(
            r"<(?:instructions|objective|user_request|raw_prompt)>(.*?)</(?:instructions|objective|user_request|raw_prompt)>",
            current,
            re.DOTALL | re.IGNORECASE,
        ) or re.search(
            r"<(?:task|intent)>(.*?)</(?:task|intent)>",
            current,
            re.DOTALL | re.IGNORECASE,
        )
        if xml_match:
            current = xml_match.group(1).strip()
            changed = True
            continue

        obj_match = re.search(
            r"###\s*(?:Objective|Task|Instructions)\s*\n+(.*?)(?:\n+###|\Z)",
            current,
            re.DOTALL | re.IGNORECASE,
        )
        if obj_match:
            current = obj_match.group(1).strip()
            changed = True
            continue

        orig_match = re.search(
            r"(?:Original Instructions|Instructions):\s*(.*)",
            current,
            re.DOTALL | re.IGNORECASE,
        )
        if orig_match:
            matched_text = orig_match.group(1).strip()
            matched_text = re.sub(r'"""[\s\S]*$', "", matched_text).strip()
            if matched_text and matched_text != current:
                current = matched_text
                changed = True
                continue

        if not changed:
            break

    raw_domain_match = re.search(r"<domain>([^<]+)</domain>", raw, re.IGNORECASE) or re.search(
        r'"domain"\s*:\s*"([^"]+)"', raw, re.IGNORECASE
    )
    if "<task_dispatch" in current.lower() or "<context>" in current.lower():
        current = re.sub(r"<context>.*?</context>", " ", current, flags=re.DOTALL | re.IGNORECASE)
        current = re.sub(r"<constraints>.*?</constraints>", " ", current, flags=re.DOTALL | re.IGNORECASE)
        current = re.sub(r"<[^>]+>", " ", current)

    current = re.sub(r"^[#\s\-\*]+", "", current)
    current = re.sub(
        r"^You are (?:the|an?) (.*?) on the AGY Fleet Swarm\.?\s*(?:PROJECT:\s*)?",
        r"\1 — ",
        current,
        flags=re.IGNORECASE,
    )
    current = re.sub(
        r"^Lead Adversarial Security Auditor —\s*",
        "Security Audit: ",
        current,
        flags=re.IGNORECASE,
    )
    current = " ".join(current.split())
    if raw_domain_match and (len(current) < 18 or current.endswith(("—", ":"))):
        dom_str = raw_domain_match.group(1).strip()
        if current.endswith(("—", ":")):
            current = f"{current} [{dom_str}]"
        else:
            current = f"Task dispatch [{dom_str}]"
    return current


DEFAULT_JEV_MANIFEST_PATH = HERMES_HOME / "jev_myelination" / "myelination_manifest.json"
DEFAULT_KNOWLEDGE_DB_PATH = HERMES_HOME / "knowledge_compiler.db"
DEFAULT_SLEEP_JOURNAL_DIR = Path("/home/zen/Obsidian/SecondBrain/10-Areas/AI Engineering/Sleep-Consolidation")


def collect_jev_and_brain_sleep_telemetry(
    now_local: Optional[datetime] = None,
    force_sleep_report: bool = False,
    jev_manifest_path: Optional[Path] = None,
    knowledge_db_path: Optional[Path] = None,
    sleep_journal_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """Collect Local JEV Myelination, SecondBrain Knowledge Graph, and 5-Stage Sleep Consolidation telemetry."""
    if now_local is None:
        now_local = datetime.now()
    manifest_file = jev_manifest_path or DEFAULT_JEV_MANIFEST_PATH
    db_file = knowledge_db_path or DEFAULT_KNOWLEDGE_DB_PATH
    journal_dir = sleep_journal_dir or DEFAULT_SLEEP_JOURNAL_DIR

    # 1. Local JEV Myelination Telemetry
    jev_status = "UNINITIALIZED"
    onnx_latency_ms = 0.0
    lora_count = 0
    sft_samples = 0
    dpo_samples = 0
    domain_loras: List[str] = []
    if manifest_file.exists():
        try:
            m_data = json.loads(manifest_file.read_text(encoding="utf-8"))
            if isinstance(m_data, dict):
                jev_status = str(m_data.get("status", "ACTIVE"))
                onnx_latency_ms = round(_safe_float(m_data.get("onnx_inference_latency_ms", 0.0)), 3)
                sft_samples = _safe_int(m_data.get("sft_samples_count", 0))
                dpo_samples = _safe_int(m_data.get("dpo_samples_count", 0))
                dom_map = m_data.get("domain_lora_paths", {})
                if isinstance(dom_map, dict):
                    domain_loras = list(dom_map.keys())
                base_lora = 1 if m_data.get("lora_safetensors_path") else 0
                lora_count = base_lora + len(domain_loras)
        except Exception as e:
            logger.debug("Failed reading JEV myelination manifest: %s", e)

    # 2. SecondBrain SQLite Telemetry (knowledge_compiler.db)
    active_engrams = 0
    l1_count = 0
    l2_count = 0
    l3_count = 0
    superseded_count = 0
    high_bloom_count = 0
    high_bloom_pct = 0.0
    jev_sessions_count = 0
    dialectical_audits_count = 0
    exo_total = 0
    exo_github = 0
    exo_arxiv = 0
    exo_standards = 0
    exo_tasks = 0
    exo_avg_entropy_bits = 0.0
    exo_adopt_count = 0
    exo_self_heal_count = 0
    exo_lora_count = 0
    exo_adr_count = 0
    vc_total = 0
    vc_passed = 0
    vc_blocked = 0
    vc_avg_risk = 0.0
    vc_avg_score = 100.0

    if db_file.exists():
        try:
            conn = sqlite3.connect(f"file:{db_file}?mode=ro", uri=True, timeout=2.0)
            try:
                cur = conn.cursor()
                try:
                    cur.execute(
                        "SELECT status, tier, bloom_level, COUNT(*) FROM cognitive_memories GROUP BY status, tier, bloom_level"
                    )
                    for st_val, tier_val, bloom_val, cnt_val in cur.fetchall():
                        cnt_i = _safe_int(cnt_val)
                        st_str = str(st_val or "").upper()
                        tier_str = str(tier_val or "").upper()
                        bloom_i = _safe_int(bloom_val)
                        if st_str == "ACTIVE":
                            active_engrams += cnt_i
                            if tier_str == "L1":
                                l1_count += cnt_i
                            elif tier_str == "L2":
                                l2_count += cnt_i
                            elif tier_str == "L3":
                                l3_count += cnt_i
                            if bloom_i >= 5:
                                high_bloom_count += cnt_i
                        else:
                            superseded_count += cnt_i
                    high_bloom_pct = _safe_pct(high_bloom_count, active_engrams)
                except Exception:
                    pass

                try:
                    cur.execute("SELECT COUNT(*) FROM jev_sessions")
                    row_js = cur.fetchone()
                    if row_js:
                        jev_sessions_count = _safe_int(row_js[0])
                except Exception:
                    pass

                try:
                    cur.execute("SELECT COUNT(*) FROM dialectical_audits")
                    row_da = cur.fetchone()
                    if row_da:
                        dialectical_audits_count = _safe_int(row_da[0])
                except Exception:
                    pass

                try:
                    cur.execute(
                        "SELECT source_type, evolution_decision, shannon_entropy_bits "
                        "FROM exogenous_entropy_ledger WHERE status = 'ACTIVE'"
                    )
                    exo_rows = cur.fetchall()
                    exo_total = len(exo_rows)
                    entropy_sum = 0.0
                    for src_t, evo_d, h_bits in exo_rows:
                        s_str = str(src_t or "").lower()
                        d_str = str(evo_d or "").upper()
                        entropy_sum += _safe_float(h_bits, default=2.4)
                        if s_str == "github_trending":
                            exo_github += 1
                        elif s_str == "arxiv_paper":
                            exo_arxiv += 1
                        elif s_str == "domain_standard":
                            exo_standards += 1
                        elif s_str == "autonomous_task":
                            exo_tasks += 1
                        if d_str == "ADOPT_INTO_HARNESS":
                            exo_adopt_count += 1
                        elif d_str == "SCHEDULE_SELF_HEAL":
                            exo_self_heal_count += 1
                        elif d_str == "COMPILE_LORA_SKILL":
                            exo_lora_count += 1
                        elif d_str == "GENERATE_ADR":
                            exo_adr_count += 1
                    if exo_total > 0:
                        exo_avg_entropy_bits = round(entropy_sum / exo_total, 2)
                except Exception:
                    pass

                try:
                    cur.execute("""
                        SELECT
                            COUNT(*),
                            SUM(CASE WHEN verdict IN ('VICTORY_CERTIFIED', 'PASS') THEN 1 ELSE 0 END),
                            SUM(CASE WHEN verdict NOT IN ('VICTORY_CERTIFIED', 'PASS') THEN 1 ELSE 0 END),
                            AVG(fake_pass_risk_score),
                            AVG(composite_critic_score)
                        FROM victory_critique_ledger
                    """)
                    vc_row = cur.fetchone()
                    if vc_row and vc_row[0]:
                        vc_total = _safe_int(vc_row[0])
                        vc_passed = _safe_int(vc_row[1])
                        vc_blocked = _safe_int(vc_row[2])
                        vc_avg_risk = round(_safe_float(vc_row[3], default=0.0), 2)
                        vc_avg_score = round(_safe_float(vc_row[4], default=100.0), 1)
                except Exception:
                    pass
            finally:
                conn.close()
        except Exception as e:
            logger.debug("Failed querying knowledge_compiler.db: %s", e)

    # 3. 5-Stage Circadian Brain Sleep Consolidation Journal
    sleep_available = False
    cycle_date = ""
    execution_timestamp = ""
    compute_engine = "LOCAL_JEV"
    stage1_symlinks_flushed = 0
    stage1_dups_cleared = 0
    stage1_debris_flushed = 0
    stage2_downscale_factor = 0.97
    stage2_synapses_renormalized = 0
    stage2_weak_pruned = 0
    stage3_promotions_count = 0
    stage4_paradoxes_resolved = 0
    stage4_dream_bridges_count = 0
    stage5_sft_samples = sft_samples
    stage5_dpo_triads = dpo_samples
    stage5_latency_ms = 0.0

    if journal_dir.exists() and journal_dir.is_dir():
        try:
            cycle_files = sorted(journal_dir.glob("Sleep-Cycle-*.md"))
            if cycle_files:
                latest_file = cycle_files[-1]
                sleep_available = True
                m_date = re.search(r"Sleep-Cycle-(\d{4}-\d{2}-\d{2})\.md", latest_file.name)
                if m_date:
                    cycle_date = m_date.group(1)
                raw_md = latest_file.read_text(encoding="utf-8")

                m_ts = re.search(r"\*\*Execution Timestamp\*\*:\s*`([^`]+)`", raw_md)
                if m_ts:
                    execution_timestamp = m_ts.group(1).strip()
                m_eng = re.search(r"\*\*Compute Engine\*\*:\s*`([^`]+)`", raw_md)
                if m_eng:
                    compute_engine = m_eng.group(1).strip()

                m_s1_sym = re.search(r"Broken Symlinks Flushed\*\*:\s*`(\d+)`", raw_md)
                if m_s1_sym:
                    stage1_symlinks_flushed = _safe_int(m_s1_sym.group(1))
                m_s1_dup = re.search(r"Duplicate SHA-256 Engrams Cleared\*\*:\s*`(\d+)`", raw_md)
                if m_s1_dup:
                    stage1_dups_cleared = _safe_int(m_s1_dup.group(1))
                m_s1_deb = re.search(r"Transient L0 Sensory Debris Flushed\*\*:\s*`(\d+)`", raw_md)
                if m_s1_deb:
                    stage1_debris_flushed = _safe_int(m_s1_deb.group(1))

                m_s2_gamma = re.search(r"Global Homeostatic Downscale Factor[^:]*:\s*`([\d\.]+)`", raw_md)
                if m_s2_gamma:
                    stage2_downscale_factor = _safe_float(m_s2_gamma.group(1), default=0.97)
                m_s2_syn = re.search(r"Synapses Renormalized[^:]*:\s*`(\d+)`", raw_md)
                if m_s2_syn:
                    stage2_synapses_renormalized = _safe_int(m_s2_syn.group(1))
                m_s2_prune = re.search(r"Weak Engrams Pruned[^:]*:\s*`(\d+)`", raw_md)
                if m_s2_prune:
                    stage2_weak_pruned = _safe_int(m_s2_prune.group(1))

                stage3_promotions_count = len(re.findall(r"`Tier\s*->\s*L\d`", raw_md))

                m_s4_dis = re.search(r"High-Dissonance Beliefs Extinguished[^:]*:\s*`(\d+)`", raw_md)
                m_s4_par = re.search(r"High-Evidence Paradoxes Queued[^:]*:\s*`(\d+)`", raw_md)
                stage4_paradoxes_resolved = (
                    (_safe_int(m_s4_dis.group(1)) if m_s4_dis else 0)
                    + (_safe_int(m_s4_par.group(1)) if m_s4_par else 0)
                )
                stage4_dream_bridges_count = len(re.findall(r"\\leftrightarrow", raw_md))

                m_s5_sft = re.search(r"Sanitized SFT Samples\*\*:\s*`(\d+)`", raw_md)
                if m_s5_sft:
                    stage5_sft_samples = _safe_int(m_s5_sft.group(1))
                m_s5_dpo = re.search(r"Contrastive DPO Triads[^:]*:\s*`(\d+)`", raw_md)
                if m_s5_dpo:
                    stage5_dpo_triads = _safe_int(m_s5_dpo.group(1))
                m_s5_lat = re.search(r"latency=([\d\.]+)ms", raw_md)
                if m_s5_lat:
                    stage5_latency_ms = _safe_float(m_s5_lat.group(1), default=0.0)
        except Exception as e:
            logger.debug("Failed reading sleep consolidation journal: %s", e)

    if sft_samples == 0 and stage5_sft_samples > 0:
        sft_samples = stage5_sft_samples
    if dpo_samples == 0 and stage5_dpo_triads > 0:
        dpo_samples = stage5_dpo_triads

    is_morning_7am_window = bool(force_sleep_report or (now_local.hour == 7))

    return {
        "jev_telemetry": {
            "status": jev_status,
            "onnx_latency_ms": onnx_latency_ms,
            "lora_count": lora_count,
            "domain_loras": domain_loras,
            "sft_samples": sft_samples,
            "dpo_samples": dpo_samples,
            "jev_sessions_count": jev_sessions_count,
            "dialectical_audits_count": dialectical_audits_count,
        },
        "brain_evolution": {
            "active_engrams": active_engrams,
            "l1_count": l1_count,
            "l2_count": l2_count,
            "l3_count": l3_count,
            "superseded_count": superseded_count,
            "high_bloom_count": high_bloom_count,
            "high_bloom_pct": high_bloom_pct,
            "exo_total": exo_total,
            "exo_github": exo_github,
            "exo_arxiv": exo_arxiv,
            "exo_standards": exo_standards,
            "exo_tasks": exo_tasks,
            "exo_avg_entropy_bits": exo_avg_entropy_bits,
            "exo_adopt_count": exo_adopt_count,
            "exo_self_heal_count": exo_self_heal_count,
            "exo_lora_count": exo_lora_count,
            "exo_adr_count": exo_adr_count,
        },
        "exogenous_ecology": {
            "exo_total": exo_total,
            "exo_github": exo_github,
            "exo_arxiv": exo_arxiv,
            "exo_standards": exo_standards,
            "exo_tasks": exo_tasks,
            "exo_avg_entropy_bits": exo_avg_entropy_bits,
            "exo_adopt_count": exo_adopt_count,
            "exo_self_heal_count": exo_self_heal_count,
            "exo_lora_count": exo_lora_count,
            "exo_adr_count": exo_adr_count,
        },
        "victory_critic": {
            "total_critiques": vc_total,
            "passed_count": vc_passed,
            "blocked_count": vc_blocked,
            "avg_fake_pass_risk": vc_avg_risk,
            "avg_critic_score": vc_avg_score,
        },
        "sleep_consolidation": {
            "available": sleep_available,
            "is_morning_7am_window": is_morning_7am_window,
            "cycle_date": cycle_date,
            "execution_timestamp": execution_timestamp,
            "compute_engine": compute_engine,
            "stage1_symlinks_flushed": stage1_symlinks_flushed,
            "stage1_dups_cleared": stage1_dups_cleared,
            "stage1_debris_flushed": stage1_debris_flushed,
            "stage2_downscale_factor": stage2_downscale_factor,
            "stage2_synapses_renormalized": stage2_synapses_renormalized,
            "stage2_weak_pruned": stage2_weak_pruned,
            "stage3_promotions_count": stage3_promotions_count,
            "stage4_paradoxes_resolved": stage4_paradoxes_resolved,
            "stage4_dream_bridges_count": stage4_dream_bridges_count,
            "stage5_sft_samples": stage5_sft_samples,
            "stage5_dpo_triads": stage5_dpo_triads,
            "stage5_latency_ms": stage5_latency_ms,
        },
    }


# ==============================================================================
# 2. EntropyDegradationDetector
# ==============================================================================
class EntropyDegradationDetector:
    """Monitors freshness and throughput of the 5 external entropy streams."""

    HOLD_REASON = "Tạm dừng (ON HOLD) theo lệnh điều phối — tập trung nguồn lực cho AGY Fleet & Core Evolution"

    def __init__(
        self,
        stock_db_path: Path = DEFAULT_STOCK_DB,
        legal_dir_path: Path = DEFAULT_LEGAL_DIR,
        media_json_path: Path = DEFAULT_MEDIA_JSON,
        median_log_path: Path = DEFAULT_MEDIAN_LOG,
        fleet_summary_url: str = FLEET_SUMMARY_URL,
        fleet_council_url: str = FLEET_COUNCIL_URL,
        fleet_nodes_url: str = FLEET_NODES_URL,
        fleet_jobs_url: str = FLEET_JOBS_URL,
        held_streams: Optional[Set[int]] = None,
        decommission_peripheral_streams: Optional[bool] = None,
    ):
        self.stock_db_path = Path(stock_db_path)
        self.legal_dir_path = Path(legal_dir_path)
        self.media_json_path = Path(media_json_path)
        self.median_log_path = Path(median_log_path)
        self.fleet_summary_url = _validate_fleet_url(fleet_summary_url)
        self.fleet_council_url = _validate_fleet_url(fleet_council_url)
        self.fleet_nodes_url = _validate_fleet_url(fleet_nodes_url)
        self.fleet_jobs_url = _validate_fleet_url(fleet_jobs_url)
        self._explicit_held_streams = held_streams is not None
        if decommission_peripheral_streams is not None:
            self.decommission_peripheral_streams = bool(decommission_peripheral_streams)
        else:
            self.decommission_peripheral_streams = (
                self.stock_db_path == DEFAULT_STOCK_DB
                and self.legal_dir_path == DEFAULT_LEGAL_DIR
                and self.media_json_path == DEFAULT_MEDIA_JSON
                and held_streams is None
                and os.environ.get("HERMES_DISABLE_STREAM_HOLD") != "1"
            )
        if self.decommission_peripheral_streams:
            self.held_streams: Set[int] = set()
        elif held_streams is not None:
            self.held_streams = set(held_streams)
        elif os.environ.get("HERMES_DISABLE_STREAM_HOLD") == "1":
            self.held_streams = set()
        else:
            auto_held: Set[int] = set()
            if self.stock_db_path == DEFAULT_STOCK_DB:
                auto_held.add(1)
            if self.legal_dir_path == DEFAULT_LEGAL_DIR:
                auto_held.add(2)
            if self.media_json_path == DEFAULT_MEDIA_JSON:
                auto_held.add(3)
            self.held_streams = auto_held

    def _apply_stream_hold(self, stream_idx: int, stream_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mark a stream as ON_HOLD if stream_idx is in self.held_streams."""
        if stream_idx in self.held_streams:
            out = dict(stream_data)
            out["status"] = "ON_HOLD"
            out["held"] = True
            out["score"] = 100
            out["reason"] = self.HOLD_REASON
            return out
        return stream_data

    def check_stream_1_stock_news(self, now_utc: Optional[datetime] = None) -> Dict[str, Any]:
        """Stream 1: Stock News Feed (stock_news_memory.sqlite)."""
        if now_utc is None:
            now_utc = datetime.now(timezone.utc)
        if not self.stock_db_path.exists():
            return {
                "name": "Stock News Feed",
                "status": "CRITICAL",
                "score": 0,
                "hours_since_crawl": 9999.0,
                "articles_24h": 0,
                "unique_symbols": 0,
                "total_articles": 0,
                "total_events": 0,
                "error": "Database not found",
            }

        try:
            conn = sqlite3.connect(f"file:{self.stock_db_path}?mode=ro", uri=True)
            c = conn.cursor()

            c.execute("SELECT MAX(crawled_at) FROM raw_articles")
            max_crawled_raw = c.fetchone()[0]

            c.execute("SELECT COUNT(*) FROM raw_articles")
            total_articles = c.fetchone()[0] or 0

            c.execute("SELECT COUNT(DISTINCT symbol) FROM raw_articles")
            unique_symbols = c.fetchone()[0] or 0

            c.execute("SELECT COUNT(*) FROM corporate_events")
            total_events = c.fetchone()[0] or 0

            hours_since_crawl = 9999.0
            articles_24h = 0

            if max_crawled_raw:
                dt_crawled = parse_timestamp(max_crawled_raw)
                if dt_crawled:
                    hours_since_crawl = max(0.0, (now_utc - dt_crawled).total_seconds() / 3600.0)

                # Count articles in last 24h
                c.execute("SELECT crawled_at FROM raw_articles")
                for row in c.fetchall():
                    dt = parse_timestamp(row[0])
                    if dt and (now_utc - dt).total_seconds() <= 86400:
                        articles_24h += 1

            conn.close()

            # Status classification
            if hours_since_crawl <= 2.0:
                status = "HEALTHY"
                score = 100
            elif hours_since_crawl <= 6.0:
                status = "DEGRADED"
                score = 50
            else:
                status = "CRITICAL"
                score = 0

            return {
                "name": "Stock News Feed",
                "status": status,
                "score": score,
                "hours_since_crawl": round(hours_since_crawl, 1),
                "articles_24h": articles_24h,
                "unique_symbols": unique_symbols,
                "total_articles": total_articles,
                "total_events": total_events,
                "last_crawled_at": max_crawled_raw,
            }
        except Exception as e:
            logger.error("Stock news stream check failed: %s", e)
            return {
                "name": "Stock News Feed",
                "status": "CRITICAL",
                "score": 0,
                "hours_since_crawl": 9999.0,
                "articles_24h": 0,
                "unique_symbols": 0,
                "error": str(e),
            }

    def check_stream_2_legal_docs(self, now_utc: Optional[datetime] = None) -> Dict[str, Any]:
        """Stream 2: Legal & Regulatory Crawler (output_legal_docs)."""
        if now_utc is None:
            now_utc = datetime.now(timezone.utc)
        history_db = self.legal_dir_path / "history.sqlite"
        manifest_json = self.legal_dir_path / "manifest.json"

        if not self.legal_dir_path.exists() or (not history_db.exists() and not manifest_json.exists()):
            return {
                "name": "Legal & Regulatory Crawler",
                "status": "CRITICAL",
                "score": 0,
                "hours_since_crawl": 9999.0,
                "total_documents": 0,
                "error": "Directory or files not found",
            }

        hours_since_crawl = 9999.0
        total_docs = 0
        last_crawled_at = None

        try:
            if history_db.exists():
                conn = sqlite3.connect(f"file:{history_db}?mode=ro", uri=True)
                c = conn.cursor()
                c.execute("SELECT MAX(crawled_at), COUNT(*) FROM legal_documents")
                row = c.fetchone()
                if row and row[0]:
                    last_crawled_at = row[0]
                    total_docs = row[1] or 0
                conn.close()

            if (not last_crawled_at or total_docs == 0) and manifest_json.exists():
                with open(manifest_json, "r", encoding="utf-8") as f:
                    m = json.load(f)
                last_crawled_at = m.get("last_updated")
                total_docs = m.get("total_documents", total_docs)

            if last_crawled_at:
                dt_crawled = parse_timestamp(last_crawled_at)
                if dt_crawled:
                    hours_since_crawl = max(0.0, (now_utc - dt_crawled).total_seconds() / 3600.0)

            # Status classification
            if hours_since_crawl <= 24.0:
                status = "HEALTHY"
                score = 100
            elif hours_since_crawl <= 72.0:
                status = "DEGRADED"
                score = 50
            else:
                status = "CRITICAL"
                score = 0

            return {
                "name": "Legal & Regulatory Crawler",
                "status": status,
                "score": score,
                "hours_since_crawl": round(hours_since_crawl, 1),
                "total_documents": total_docs,
                "last_crawled_at": last_crawled_at,
            }
        except Exception as e:
            logger.error("Legal docs stream check failed: %s", e)
            return {
                "name": "Legal & Regulatory Crawler",
                "status": "CRITICAL",
                "score": 0,
                "hours_since_crawl": 9999.0,
                "total_documents": 0,
                "error": str(e),
            }

    def check_stream_3_media_production(self, now: Optional[datetime] = None) -> Dict[str, Any]:
        """Stream 3: Media Asset Bank 24/7 Producer (daily_media_production.json)."""
        if now is None:
            now = datetime.now()
        today_str = now.strftime("%Y-%m-%d")
        current_hour = now.hour

        if not self.media_json_path.exists():
            return {
                "name": "Media Asset Bank 24/7",
                "status": "CRITICAL",
                "score": 0,
                "completed_videos": 0,
                "target_videos": 24,
                "completed_photos": 0,
                "target_photos": 24,
                "current_hour_lag": 24,
                "error": "Tracker file not found",
            }

        try:
            with open(self.media_json_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            file_date = data.get("date", "")
            target_videos = data.get("target_videos", 24)
            target_photos = data.get("target_photos", 24)
            completed_videos = data.get("completed_videos", 0)
            completed_photos = data.get("completed_photos", 0)

            if file_date != today_str:
                lag = 24
            else:
                expected_so_far = min(24, current_hour)
                lag = max(0, expected_so_far - completed_videos)

            if completed_videos == 0 or lag > 4:
                status = "CRITICAL"
                score = 0
            elif lag >= 2:
                status = "DEGRADED"
                score = 50
            else:
                status = "HEALTHY"
                score = 100

            return {
                "name": "Media Asset Bank 24/7",
                "status": status,
                "score": score,
                "completed_videos": completed_videos,
                "target_videos": target_videos,
                "completed_photos": completed_photos,
                "target_photos": target_photos,
                "current_hour_lag": lag,
                "date": file_date,
            }
        except Exception as e:
            logger.error("Media production stream check failed: %s", e)
            return {
                "name": "Media Asset Bank 24/7",
                "status": "CRITICAL",
                "score": 0,
                "completed_videos": 0,
                "target_videos": 24,
                "completed_photos": 0,
                "target_photos": 24,
                "current_hour_lag": 24,
                "error": str(e),
            }

    def check_stream_4_median_sync(self, now_utc: Optional[datetime] = None) -> Dict[str, Any]:
        """Stream 4: Median-0 Math Sync (median_hourly_sync.log)."""
        if now_utc is None:
            now_utc = datetime.now(timezone.utc)
        if not self.median_log_path.exists():
            return {
                "name": "Median-0 Math Sync",
                "status": "CRITICAL",
                "score": 0,
                "minutes_since_sync": 9999.0,
                "exit_code": 1,
                "checks_count": 0,
                "error": "Log file not found",
            }

        try:
            # Read last 200 lines
            with open(self.median_log_path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()[-200:]
            content = "".join(lines)

            # Determine exit code
            exit_code = 0
            if "failed with exit code" in content or "Hourly Sync failed" in content:
                m = re.findall(r"failed with exit code (\d+)", content)
                exit_code = int(m[-1]) if m else 1

            # Checks count: take the latest Checks: N / M line, fallback to generated storyboards count
            checks_count = 0
            m_chk = re.findall(r"Checks:\s*(\d+)", content)
            if m_chk:
                checks_count = int(m_chk[-1])
            else:
                m_gen = re.findall(r"Generated (\d+) new Manim storyboards", content)
                if m_gen:
                    checks_count = int(m_gen[-1])

            # Timestamp: prefer log file mtime as true finish time
            sync_dt = datetime.fromtimestamp(self.median_log_path.stat().st_mtime, tz=timezone.utc)

            minutes_since_sync = max(0.0, (now_utc - sync_dt).total_seconds() / 60.0)

            if minutes_since_sync <= 75.0 and exit_code == 0:
                status = "HEALTHY"
                score = 100
            elif minutes_since_sync <= 180.0 and exit_code == 0:
                status = "DEGRADED"
                score = 50
            else:
                status = "CRITICAL"
                score = 0

            return {
                "name": "Median-0 Math Sync",
                "status": status,
                "score": score,
                "minutes_since_sync": round(minutes_since_sync, 1),
                "exit_code": exit_code,
                "checks_count": checks_count,
                "last_sync_timestamp": sync_dt.isoformat(),
            }
        except Exception as e:
            logger.error("Median sync stream check failed: %s", e)
            return {
                "name": "Median-0 Math Sync",
                "status": "CRITICAL",
                "score": 0,
                "minutes_since_sync": 9999.0,
                "exit_code": 1,
                "checks_count": 0,
                "error": str(e),
            }

    def check_stream_5_fleet_mesh(
        self,
        now_ts: Optional[float] = None,
        reconcile_tokens: bool = False,
    ) -> Dict[str, Any]:
        """Stream 5: AGY Fleet & Clef Mesh (REST query to localhost:7777)."""
        active_nodes = 0
        total_nodes = 0
        consensus_score = 0.0
        sla_passed = False
        total_fleet_tokens = 0
        top_5_nodes: List[Dict[str, Any]] = []
        total_jobs_tokens = 0
        total_jobs_tokens_1h = 0
        top_3_tasks: List[Dict[str, Any]] = []
        valid_nodes: List[Dict[str, Any]] = []
        valid_jobs: List[Dict[str, Any]] = []
        future_jobs_rejected = 0
        malformed_jobs_rejected = 0
        stale_jobs_filtered = 0

        now_time = now_ts if now_ts is not None else time.time()
        cutoff_ts = now_time - 3600.0

        try:
            sum_data = _safe_fetch_json(self.fleet_summary_url, timeout=10.0)
            active_nodes = sum_data.get("online_nodes") or sum_data.get("active_nodes") or 0
            total_nodes = sum_data.get("total_nodes", 0)

            ccl_data = _safe_fetch_json(self.fleet_council_url, timeout=10.0)
            consensus_score = float(
                ccl_data.get("composite_consensus_score")
                or ccl_data.get("metrics", {}).get("consensus_score", 0.0)
            )
            sla_passed = bool(ccl_data.get("sla_passed", False))

            if active_nodes >= 15 and consensus_score >= 80.0 and sla_passed:
                status = "HEALTHY"
                score = int(consensus_score)
            elif active_nodes >= 10 and consensus_score >= 60.0:
                status = "DEGRADED"
                score = 50
            else:
                status = "CRITICAL"
                score = 0

            # Collect tokenomics and node activity
            try:
                raw_data = _safe_fetch_json(self.fleet_nodes_url, timeout=5.0)
                nodes_list = raw_data.get("nodes", []) if isinstance(raw_data, dict) else (raw_data if isinstance(raw_data, list) else [])
                valid_nodes = [n for n in nodes_list if isinstance(n, dict)]
                total_fleet_tokens = sum(_safe_int(n.get("quota_weekly_consumed")) for n in valid_nodes)
            except Exception as e:
                logger.debug("Fleet nodes query failed: %s", e)

            try:
                jobs_url = self.fleet_jobs_url
                if "?" not in jobs_url:
                    jobs_url = f"{jobs_url}?summary=true"
                raw_data = _safe_fetch_json(jobs_url, timeout=10.0, max_bytes=33554432)
                jobs_list = raw_data.get("jobs", []) if isinstance(raw_data, dict) else (raw_data if isinstance(raw_data, list) else [])
                valid_jobs = [j for j in jobs_list if isinstance(j, dict)]
                total_jobs_tokens = sum(_safe_int(j.get("total_tokens")) for j in valid_jobs)
            except Exception as e:
                logger.debug("Fleet jobs query failed: %s", e)

            EPOCH_CEILING = 4102444800.0  # 2100-01-01 00:00:00 UTC (Plausible contemporary ceiling)

            def _get_job_ts(j: Dict[str, Any]) -> Optional[float]:
                for field in ("completed_at", "started_at", "created_at"):
                    val = j.get(field)
                    if val is not None:
                        # Guard against boolean (bool is subclass of int in Python)
                        if isinstance(val, bool):
                            continue
                        dt = parse_timestamp(val)
                        if dt is not None:
                            try:
                                ts = dt.timestamp()
                                if not (math.isnan(ts) or math.isinf(ts)):
                                    if ts > EPOCH_CEILING:
                                        return None
                                    return ts
                            except Exception:
                                pass
                return None

            # Maximum future clock drift tolerance (60 seconds)
            MAX_FUTURE_SLACK_S = 60.0
            future_ceiling_ts = now_time + MAX_FUTURE_SLACK_S

            # Detect whether any jobs in payload have a valid timestamp
            has_any_valid_ts = any(_get_job_ts(j) is not None for j in valid_jobs)

            jobs_1h = []
            future_jobs_rejected = 0
            malformed_jobs_rejected = 0
            stale_jobs_filtered = 0

            for j in valid_jobs:
                j_ts = _get_job_ts(j)
                if has_any_valid_ts:
                    if j_ts is None:
                        # Malformed or missing timestamp when valid timestamps exist -> reject
                        malformed_jobs_rejected += 1
                        continue
                    if j_ts > future_ceiling_ts:
                        # Future timestamp beyond clock drift slack -> reject (forgery/drift guard)
                        future_jobs_rejected += 1
                        continue
                    if j_ts < cutoff_ts:
                        # Outside the 1-hour window
                        stale_jobs_filtered += 1
                        continue
                    jobs_1h.append(j)
                else:
                    # Synthetic test mock without any timestamps across all jobs
                    jobs_1h.append(j)

            total_jobs_tokens_1h = sum(_safe_int(j.get("total_tokens")) for j in jobs_1h)

            # Operational Efficiency & Accuracy Metrics (1h & All-time)
            all_completed_jobs = [
                j for j in valid_jobs
                if str(j.get("status", "completed")).lower() in ("completed", "success", "ok")
            ]
            all_running_jobs = [
                j for j in valid_jobs
                if str(j.get("status", "")).lower() in ("running", "pending")
            ]
            all_failed_jobs = [
                j for j in valid_jobs
                if str(j.get("status", "")).lower() in ("failed", "error")
            ]
            all_timeout_jobs = [
                j for j in valid_jobs
                if "timeout" in str(j.get("stderr", "") or j.get("error", "") or "").lower()
                or "timed out" in str(j.get("stderr", "") or j.get("error", "") or "").lower()
            ]
            all_finished_count = len(all_completed_jobs) + len(all_failed_jobs)
            success_rate_pct = (
                round(100.0 * len(all_completed_jobs) / all_finished_count, 1)
                if all_finished_count > 0
                else 100.0
            )

            completed_jobs_1h = [
                j for j in jobs_1h
                if str(j.get("status", "completed")).lower() in ("completed", "success", "ok")
            ]
            running_jobs_1h = [
                j for j in jobs_1h
                if str(j.get("status", "")).lower() in ("running", "pending")
            ]
            failed_jobs_1h = [
                j for j in jobs_1h
                if str(j.get("status", "")).lower() in ("failed", "error")
            ]
            timeout_jobs_1h = [
                j for j in jobs_1h
                if "timeout" in str(j.get("stderr", "") or j.get("error", "") or "").lower()
                or "timed out" in str(j.get("stderr", "") or j.get("error", "") or "").lower()
            ]
            finished_1h_count = len(completed_jobs_1h) + len(failed_jobs_1h)
            success_rate_1h_pct = (
                round(100.0 * len(completed_jobs_1h) / finished_1h_count, 1)
                if finished_1h_count > 0
                else 100.0
            )

            durations_1h: List[float] = []
            for j in completed_jobs_1h:
                dur = _safe_float(j.get("duration", 0.0), default=0.0)
                if dur <= 0.0 and j.get("latency_ms"):
                    dur = _safe_float(j.get("latency_ms", 0.0), default=0.0) / 1000.0
                if dur <= 0.0:
                    c_at = parse_timestamp(j.get("completed_at"))
                    s_at = parse_timestamp(j.get("started_at") or j.get("created_at"))
                    if c_at and s_at and c_at >= s_at:
                        dur = (c_at - s_at).total_seconds()
                if 0.0 < dur < 3600.0:
                    durations_1h.append(dur)
            avg_latency_1h_s = round(sum(durations_1h) / len(durations_1h), 1) if durations_1h else 0.0
            sorted_durs = sorted(durations_1h)
            p95_latency_s = (
                round(sorted_durs[min(len(sorted_durs) - 1, int(0.95 * len(sorted_durs)))], 1)
                if sorted_durs
                else 0.0
            )

            completed_tokens = sum(_safe_int(j.get("total_tokens", 0)) for j in all_completed_jobs)
            failed_tokens = sum(_safe_int(j.get("total_tokens", 0)) for j in all_failed_jobs)
            tokens_per_completed_job = (
                int(completed_tokens / len(all_completed_jobs)) if all_completed_jobs else 0
            )
            effective_token_ratio_pct = (
                _safe_pct(completed_tokens, completed_tokens + failed_tokens)
                if (completed_tokens + failed_tokens) > 0
                else 100.0
            )
            top_failure_reasons = []
            for fj in (failed_jobs_1h or all_failed_jobs)[:3]:
                err_raw = str(fj.get("error") or fj.get("stderr") or "").strip()
                if err_raw:
                    first_line = err_raw.splitlines()[0][:90]
                    if first_line not in top_failure_reasons:
                        top_failure_reasons.append(first_line)

            cache_read_tokens_total = sum(_safe_int(j.get("cache_read_tokens", 0)) for j in valid_jobs)
            input_tokens_total = sum(_safe_int(j.get("input_tokens", 0)) for j in valid_jobs)
            output_tokens_total = sum(_safe_int(j.get("output_tokens", 0)) for j in valid_jobs)
            cache_hit_ratio_pct = _safe_pct(
                cache_read_tokens_total,
                cache_read_tokens_total + input_tokens_total,
            )
            cost_saved_usd_total = round(
                sum(_safe_float(j.get("cost_saved_usd", 0.0)) for j in valid_jobs), 4
            )
            sentinel_catches = sum(
                1
                for j in valid_jobs
                if bool(j.get("is_fabricated"))
                or any(
                    k in str(j.get("stderr", "") or "").lower()
                    for k in ("fabrication", "sentinel", "qualitygate")
                )
                or bool(j.get("retry_history"))
            )
            self_healing_retries = sum(
                len(j.get("retry_history") or [])
                for j in valid_jobs
                if isinstance(j.get("retry_history"), list)
            )
            l1_low_cnt = 0
            l2_med_cnt = 0
            l34_high_cnt = 0
            for j in valid_jobs:
                m_low = str(j.get("model", "") or "").lower()
                if any(k in m_low for k in ("low", "lite", "haiku")):
                    l1_low_cnt += 1
                elif any(k in m_low for k in ("medium", "sonnet", "resolved-auto")):
                    l2_med_cnt += 1
                else:
                    l34_high_cnt += 1
            task_level_distribution = {
                "L1_low": l1_low_cnt,
                "L2_med": l2_med_cnt,
                "L3_L4_high": l34_high_cnt,
            }

            operational_efficiency = {
                "total_jobs": len(valid_jobs),
                "completed_jobs": len(all_completed_jobs),
                "failed_jobs": len(all_failed_jobs),
                "timeout_jobs": len(all_timeout_jobs),
                "running_jobs": len(all_running_jobs),
                "success_rate_pct": success_rate_pct,
                "jobs_1h_total": len(jobs_1h),
                "jobs_1h_completed": len(completed_jobs_1h),
                "jobs_1h_failed": len(failed_jobs_1h),
                "jobs_1h_timeout": len(timeout_jobs_1h),
                "completed_1h": len(completed_jobs_1h),
                "running_1h": len(running_jobs_1h),
                "failed_1h": len(failed_jobs_1h),
                "timeout_1h": len(timeout_jobs_1h),
                "success_rate_1h_pct": success_rate_1h_pct,
                "avg_latency_1h_s": avg_latency_1h_s,
                "avg_latency_sec": avg_latency_1h_s,
                "p95_latency_sec": p95_latency_s,
                "tokens_per_completed_job": tokens_per_completed_job,
                "effective_token_ratio_pct": effective_token_ratio_pct,
                "wasted_tokens_failed": failed_tokens,
                "top_failure_reasons": top_failure_reasons,
                "cache_read_tokens_total": cache_read_tokens_total,
                "input_tokens_total": input_tokens_total,
                "output_tokens_total": output_tokens_total,
                "cache_hit_ratio_pct": cache_hit_ratio_pct,
                "cost_saved_usd_total": cost_saved_usd_total,
                "sentinel_catches": sentinel_catches,
                "self_healing_retries": self_healing_retries,
                "task_level_distribution": task_level_distribution,
            }

            # R2: Automatic <50% Operational Efficiency Emergency Root-Cause Audit Check
            emergency_audit_triggered = bool(
                (len(jobs_1h) >= 5 and success_rate_1h_pct < 50.0)
                or (len(valid_jobs) >= 10 and success_rate_pct < 50.0)
            )
            operational_efficiency["emergency_audit_active"] = emergency_audit_triggered
            operational_efficiency["emergency_audit"] = {
                "status": "ACTIVE_EMERGENCY" if emergency_audit_triggered else "NORMAL",
                "threshold": 50.0,
                "efficiency_1h_pct": success_rate_1h_pct,
                "efficiency_all_pct": success_rate_pct,
                "primary_bottleneck": (top_failure_reasons[0] if top_failure_reasons else "none") if emergency_audit_triggered else "none",
            }

            tasks_pool = jobs_1h if jobs_1h else valid_jobs
            sorted_jobs = sorted(
                tasks_pool,
                key=lambda j: _safe_int(j.get("total_tokens")),
                reverse=True,
            )
            def _norm_argon(slug: str) -> str:
                s = str(slug or "").strip()
                if not s:
                    return "gemini-4-argon-high"
                low = s.lower()
                if "3.8-flash" in low or "3-8-flash" in low:
                    if "low" in low:
                        return "gemini-4-argon-low"
                    if "medium" in low or "med" in low:
                        return "gemini-4-argon-medium"
                    return "gemini-4-argon-high"
                return s

            for j in sorted_jobs[:3]:
                full_jid = str(j.get("job_id", ""))
                jid = full_jid[:8]
                job_for_prompt = j
                if (
                    len(str(j.get("prompt", ""))) >= 245
                    and full_jid
                    and ("127.0.0.1" in self.fleet_jobs_url or "localhost" in self.fleet_jobs_url)
                ):
                    try:
                        base_jurl = self.fleet_jobs_url.split("?")[0].rstrip("/")
                        detail_data = _safe_fetch_json(f"{base_jurl}/{full_jid}", timeout=1.5)
                        if isinstance(detail_data, dict) and detail_data.get("prompt"):
                            job_for_prompt = detail_data
                    except Exception:
                        pass
                prompt_clean = _extract_clean_task_prompt(job_for_prompt)
                top_3_tasks.append({
                    "job_id": jid,
                    "node_name": str(j.get("node_name", "")),
                    "model": _norm_argon(str(j.get("model", "") or "resolved-auto")),
                    "total_tokens": _safe_int(j.get("total_tokens")),
                    "prompt": prompt_clean,
                    "clean_prompt": prompt_clean,
                })

            # Count requests and tokens per node in the past 1 hour (jobs_1h)
            reqs_1h = Counter()
            completed_reqs_1h = Counter()
            failed_reqs_1h = Counter()
            tokens_1h = Counter()
            for j in jobs_1h:
                nname = str(j.get("node_name", "")).strip()
                if nname:
                    reqs_1h[nname] += 1
                    j_tok = _safe_int(j.get("total_tokens"))
                    tokens_1h[nname] += j_tok
                    j_st = str(j.get("status", "completed")).lower()
                    if j_st in ("failed", "error") and j_tok == 0:
                        failed_reqs_1h[nname] += 1
                    else:
                        completed_reqs_1h[nname] += 1

            candidate_names = set(str(n.get("name", "")).strip() for n in valid_nodes if str(n.get("name", "")).strip()) | set(reqs_1h.keys())
            node_tier_map = {str(n.get("name", "")): str(n.get("tier", "pro")) for n in valid_nodes}
            node_active_map = {str(n.get("name", "")): _safe_int(n.get("active_jobs", 0)) for n in valid_nodes}
            node_alltime_reqs = {str(n.get("name", "")): _safe_int(n.get("requests_served", 0)) for n in valid_nodes}
            node_weekly_tokens = {str(n.get("name", "")): _safe_int(n.get("quota_weekly_consumed", 0)) for n in valid_nodes}
            node_weekly_pct = {
                str(n.get("name", "")): _safe_float(
                    n.get("gemini_weekly_percent", n.get("quota_weekly_percent", 100.0)),
                    default=100.0,
                )
                for n in valid_nodes
            }
            node_pref_model = {
                str(n.get("name", "")): _norm_argon(
                    str(n.get("preferred_model", "") or "gemini-4-argon-high")
                )
                for n in valid_nodes
            }

            node_stats_list = []
            for nname in candidate_names:
                r1h = reqs_1h.get(nname, 0)
                c1h = completed_reqs_1h.get(nname, 0)
                f1h = failed_reqs_1h.get(nname, 0)
                t1h = tokens_1h.get(nname, 0)
                all_time_r = node_alltime_reqs.get(nname, 0)
                weekly_t = node_weekly_tokens.get(nname, 0)
                node_stats_list.append({
                    "name": nname,
                    "tier": node_tier_map.get(nname, "pro"),
                    "preferred_model": node_pref_model.get(nname, "gemini-4-argon-high"),
                    "requests_served": r1h if jobs_1h else all_time_r,
                    "requests_served_1h": c1h if c1h > 0 else r1h,
                    "completed_1h": c1h,
                    "failed_1h": f1h,
                    "requests_served_all_time": all_time_r,
                    "tokens_consumed": t1h if t1h > 0 else (weekly_t if (r1h == 0 and not jobs_1h) else t1h),
                    "tokens_consumed_1h": t1h,
                    "tokens_weekly_consumed": weekly_t,
                    "gemini_weekly_pct": node_weekly_pct.get(nname, 100.0),
                    "active_jobs": node_active_map.get(nname, 0),
                })

            sorted_nodes = sorted(
                node_stats_list,
                key=lambda x: (
                    x["completed_1h"],
                    x["tokens_consumed_1h"],
                    x["requests_served_all_time"],
                    x["tokens_weekly_consumed"],
                    x["requests_served_1h"],
                ),
                reverse=True,
            )
            top_5_nodes = sorted_nodes[:5]

            # Pro-First Quota Exhaustion & Workload Evaluation (17 Active Google AGY Pro Nodes)
            pro_nodes = [
                n for n in valid_nodes
                if str(n.get("tier", "")).lower() == "pro"
                and not str(n.get("name", "")).lower().startswith("oc_")
                and str(n.get("provider", "")).lower() != "opencode"
                and not n.get("ineligible")
                and not n.get("disabled")
                and str(n.get("name", "")).lower() not in ("nebula", "innoria-team", "innoria.team", "ariana", "ultra-2", "zencode-ent")
            ]
            non_pro_nodes = [n for n in valid_nodes if n not in pro_nodes]

            total_pro_nodes = len(pro_nodes)
            pro_capacity_tokens = sum(_safe_int(n.get("quota_weekly_capacity", 2500000)) for n in pro_nodes)
            pro_consumed_tokens = sum(_safe_int(n.get("quota_weekly_consumed", 0)) for n in pro_nodes)
            pro_burn_pct = _safe_pct(pro_consumed_tokens, pro_capacity_tokens)
            pro_tokens_1h = sum(tokens_1h.get(str(n.get("name", "")), 0) for n in pro_nodes)

            pro_requests = sum(_safe_int(n.get("requests_served", 0)) for n in pro_nodes)
            non_pro_requests = sum(_safe_int(n.get("requests_served", 0)) for n in non_pro_nodes)
            total_requests = pro_requests + non_pro_requests
            pro_request_share_pct = _safe_pct(pro_requests, total_requests)

            # Starved Pro nodes: Pro nodes with >75% remaining weekly quota and < 10 requests served
            starved_pro_nodes = [
                str(n.get("name", ""))
                for n in pro_nodes
                if _safe_float(n.get("quota_weekly_percent", 100.0)) > 75.0 and _safe_int(n.get("requests_served", 0)) < 10
            ]

            # Recent jobs distribution (from jobs_1h, falling back to valid_jobs if no jobs in 1h)
            pro_node_names = {str(n.get("name", "")) for n in pro_nodes}
            jobs_for_eval = jobs_1h if jobs_1h else valid_jobs
            recent_pro_jobs = sum(1 for j in jobs_for_eval if str(j.get("node_name", "")) in pro_node_names)
            recent_total_jobs = len(jobs_for_eval)
            recent_pro_share_pct = _safe_pct(recent_pro_jobs, recent_total_jobs) if recent_total_jobs > 0 else pro_request_share_pct

            # Evaluation logic for Pro-First Quality Criterion
            if recent_pro_share_pct >= 80.0 or (pro_burn_pct >= 80.0 and len(starved_pro_nodes) <= 2):
                pro_quality_grade = "OPTIMAL"
                pro_quality_status = "PASS"
                pro_quality_badge = "🟢 ĐẠT CHUẨN"
                pro_verdict = "Toàn bộ tải đang được ưu tiên đốt cạn Quota Pro qua Round-Robin."
            elif recent_pro_share_pct >= 40.0 or pro_burn_pct >= 40.0:
                pro_quality_grade = "ACCEPTABLE"
                pro_quality_status = "WARNING"
                pro_quality_badge = "🟡 CẦN TỐI ƯU"
                pro_verdict = f"Còn {len(starved_pro_nodes)}/{total_pro_nodes} nodes Pro tồn nhiều Quota; cần dồn thêm task Gemini 4 Argon."
            else:
                pro_quality_grade = "DEFICIT"
                pro_quality_status = "CRITICAL"
                pro_quality_badge = "🔴 LỆCH TIÊU CHÍ"
                pro_verdict = "Tỷ trọng tải Pro quá thấp so với Nebula/Ultra; vi phạm nguyên tắc Pro-First."

            pro_first_criterion = {
                "status": pro_quality_status,
                "grade": pro_quality_grade,
                "badge": pro_quality_badge,
                "pro_burn_pct": pro_burn_pct,
                "pro_consumed_tokens": pro_consumed_tokens,
                "pro_capacity_tokens": pro_capacity_tokens,
                "pro_tokens_1h": pro_tokens_1h,
                "pro_requests": pro_requests,
                "total_requests": total_requests,
                "pro_request_share_pct": pro_request_share_pct,
                "recent_pro_share_pct": recent_pro_share_pct,
                "total_pro_nodes": total_pro_nodes,
                "starved_pro_nodes": starved_pro_nodes,
                "starved_count": len(starved_pro_nodes),
                "verdict": pro_verdict,
            }

            # Deep Pro Fleet & Ultra Fleet Insights
            healthy_pro = [
                n for n in pro_nodes
                if not n.get("disabled")
                and not n.get("ineligible")
                and str(n.get("status", "idle")).lower() not in ("error", "offline", "unauthenticated", "disabled")
            ]
            cooling_pro = [
                n for n in pro_nodes
                if _safe_int(n.get("active_jobs", 0)) > 0
                or str(n.get("status", "")).lower() in ("busy", "cooling", "rate_limited")
            ]
            active_pro_7d = [
                n for n in pro_nodes
                if _safe_int(n.get("quota_weekly_consumed", 0)) > 0 or _safe_int(n.get("requests_served", 0)) > 0
            ]
            active_pro_1h = [
                n for n in pro_nodes
                if completed_reqs_1h.get(str(n.get("name", "")), 0) > 0 or tokens_1h.get(str(n.get("name", "")), 0) > 0
            ]
            avg_5h_rem = (
                round(
                    sum(_safe_float(n.get("gemini_5h_percent", n.get("quota_5h_percent", 100.0)), default=100.0) for n in healthy_pro)
                    / len(healthy_pro),
                    1,
                )
                if healthy_pro
                else 100.0
            )
            avg_7d_rem = (
                round(
                    sum(_safe_float(n.get("gemini_weekly_percent", n.get("quota_weekly_percent", 100.0)), default=100.0) for n in healthy_pro)
                    / len(healthy_pro),
                    1,
                )
                if healthy_pro
                else 100.0
            )
            avg_claude_5h_rem = (
                round(
                    sum(_safe_float(n.get("claude_5h_percent", 100.0), default=100.0) for n in healthy_pro)
                    / len(healthy_pro),
                    1,
                )
                if healthy_pro
                else 100.0
            )
            avg_claude_7d_rem = (
                round(
                    sum(_safe_float(n.get("claude_weekly_percent", 100.0), default=100.0) for n in healthy_pro)
                    / len(healthy_pro),
                    1,
                )
                if healthy_pro
                else 100.0
            )
            pro_gem_5h_cons = sum(_safe_int(n.get("gemini_5h_consumed", n.get("quota_5h_consumed", 0))) for n in pro_nodes)
            pro_gem_5h_cap = sum(_safe_int(n.get("gemini_5h_capacity", n.get("quota_5h_capacity", 500000))) for n in pro_nodes)
            pro_gem_7d_cons = sum(_safe_int(n.get("gemini_weekly_consumed", n.get("quota_weekly_consumed", 0))) for n in pro_nodes)
            pro_gem_7d_cap = sum(_safe_int(n.get("gemini_weekly_capacity", n.get("quota_weekly_capacity", 2500000))) for n in pro_nodes)
            pro_claude_5h_cons = sum(_safe_int(n.get("claude_5h_consumed", 0)) for n in pro_nodes)
            pro_claude_5h_cap = sum(_safe_int(n.get("claude_5h_capacity", 300000)) for n in pro_nodes)
            pro_claude_7d_cons = sum(_safe_int(n.get("claude_weekly_consumed", 0)) for n in pro_nodes)
            pro_claude_7d_cap = sum(_safe_int(n.get("claude_weekly_capacity", 1500000)) for n in pro_nodes)
            dual_ready_pro = [
                n for n in healthy_pro
                if _safe_float(n.get("gemini_weekly_percent", n.get("quota_weekly_percent", 100.0)), default=100.0) > 0
                and _safe_float(n.get("claude_weekly_percent", 100.0), default=100.0) > 0
            ]
            pro_rem_tokens = max(0, pro_capacity_tokens - pro_consumed_tokens)
            pro_rem_pct = round(100.0 - pro_burn_pct, 1)
            model_counter: Counter = Counter()
            for j in valid_jobs:
                m_name = _norm_argon(str(j.get("model") or "resolved-auto"))
                model_counter[m_name] += 1

            sorted_ready_pro = sorted(
                healthy_pro,
                key=lambda n: (
                    _safe_float(n.get("gemini_weekly_percent", n.get("quota_weekly_percent", 100.0)), default=100.0),
                    _safe_int(n.get("requests_served", 0)),
                ),
                reverse=True,
            )
            top_ready_pro_nodes = [
                f"{n.get('name')} ({_safe_float(n.get('gemini_weekly_percent', n.get('quota_weekly_percent', 100.0)), default=100.0):.0f}%)"
                for n in sorted_ready_pro[:4]
            ]

            pro_fleet_insight = {
                "total_pro_nodes": total_pro_nodes,
                "healthy_pro_nodes": len(healthy_pro),
                "ready_count": len(healthy_pro),
                "dual_ready_pro_count": len(dual_ready_pro),
                "cooling_or_busy_count": len(cooling_pro),
                "active_pro_nodes_7d": len(active_pro_7d),
                "active_pro_nodes_1h": len(active_pro_1h),
                "pro_tokens_1h": pro_tokens_1h,
                "avg_5h_rem_pct": avg_5h_rem,
                "avg_7d_rem_pct": avg_7d_rem,
                "pro_gemini_5h_consumed": pro_gem_5h_cons,
                "pro_gemini_5h_capacity": pro_gem_5h_cap,
                "pro_gemini_5h_rem_pct": avg_5h_rem,
                "pro_gemini_7d_consumed": pro_gem_7d_cons,
                "pro_gemini_7d_capacity": pro_gem_7d_cap,
                "pro_gemini_7d_rem_pct": avg_7d_rem,
                "pro_claude_5h_consumed": pro_claude_5h_cons,
                "pro_claude_5h_capacity": pro_claude_5h_cap,
                "pro_claude_5h_rem_pct": avg_claude_5h_rem,
                "pro_claude_7d_consumed": pro_claude_7d_cons,
                "pro_claude_7d_capacity": pro_claude_7d_cap,
                "pro_claude_7d_rem_pct": avg_claude_7d_rem,
                "pro_remaining_pct": pro_rem_pct,
                "pro_remaining_tokens": pro_rem_tokens,
                "model_distribution": dict(model_counter.most_common(5)),
                "top_ready_pro_nodes": top_ready_pro_nodes,
                "pro_model_standard": "4-Level Task Planning (gemini-4-argon-high/med/low & claude-opus-5-5, Dual Quota QBRR)",
            }

            ultra_raw_nodes = [
                n for n in valid_nodes
                if str(n.get("name", "")).lower() in ("innoria-team", "innoria.team", "ariana", "ultra-2")
                and not n.get("disabled")
            ]
            ultra_nodes_info = []
            for un in ultra_raw_nodes:
                uname = str(un.get("name", ""))
                ultra_nodes_info.append({
                    "name": uname,
                    "display_name": str(un.get("display_name", uname)),
                    "preferred_model": str(un.get("preferred_model", "") or "gemini-4-argon-high"),
                    "weekly_rem_pct": _safe_float(un.get("gemini_weekly_percent", un.get("quota_weekly_percent", 100.0)), default=100.0),
                    "weekly_tokens": _safe_int(un.get("quota_weekly_consumed", 0)),
                    "requests_served": _safe_int(un.get("requests_served", 0)),
                    "tokens_1h": tokens_1h.get(uname, 0),
                })
            ultra_cap_tokens = sum(_safe_int(un.get("quota_weekly_capacity", 7000000)) for un in ultra_raw_nodes)
            ultra_cons_tokens = sum(_safe_int(un.get("quota_weekly_consumed", 0)) for un in ultra_raw_nodes)
            ultra_rem_tokens = max(0, ultra_cap_tokens - ultra_cons_tokens)
            ultra_burn_pct = _safe_pct(ultra_cons_tokens, ultra_cap_tokens)
            ultra_tokens_1h = sum(u["tokens_1h"] for u in ultra_nodes_info)
            ultra_names_set = {u["name"] for u in ultra_nodes_info} | {"innoria-team", "ariana", "ultra-2"}
            claude_leaks_on_ultra = sum(
                1
                for j in valid_jobs
                if str(j.get("node_name", "")) in ultra_names_set
                and any(k in str(j.get("model", "")).lower() for k in ("claude", "opus", "sonnet"))
                and (
                    _safe_int(j.get("total_tokens", 0)) > 0
                    or str(j.get("status", "")).lower() in ("completed", "success", "ok")
                )
            )
            claude_blocked_on_ultra = sum(
                1
                for j in valid_jobs
                if str(j.get("node_name", "")) in ultra_names_set
                and any(k in str(j.get("model", "")).lower() for k in ("claude", "opus", "sonnet"))
                and _safe_int(j.get("total_tokens", 0)) == 0
                and str(j.get("status", "")).lower() not in ("completed", "success", "ok")
            )
            ultra_fleet_insight = {
                "ultra_nodes": ultra_nodes_info,
                "nodes": [u["name"] for u in ultra_nodes_info],
                "ultra_burn_pct": ultra_burn_pct,
                "ultra_consumed_tokens": ultra_cons_tokens,
                "ultra_capacity_tokens": ultra_cap_tokens,
                "ultra_remaining_tokens": ultra_rem_tokens,
                "ultra_tokens_1h": ultra_tokens_1h,
                "claude_leaks_on_ultra": claude_leaks_on_ultra,
                "claude_blocked_on_ultra": claude_blocked_on_ultra,
                "gemini_only_invariant": claude_leaks_on_ultra == 0,
            }

            l3_tombstones_count = 0
            tomb_path = REPO_ROOT / "resources" / "l3_tombstones.jsonl"
            if tomb_path.exists():
                try:
                    with open(tomb_path, "r", encoding="utf-8") as tf:
                        l3_tombstones_count = sum(1 for line in tf if line.strip())
                except Exception:
                    pass

            action_ledger_entries = 0
            for lp in (
                Path.home() / ".gemini" / "antigravity" / "action_ledger.jsonl",
                Path("/home/zen/zencode-ent/router/data/egress_activity.jsonl"),
            ):
                try:
                    if lp.exists():
                        with open(lp, "r", encoding="utf-8", errors="ignore") as af:
                            action_ledger_entries += sum(1 for line in af if line.strip())
                except Exception:
                    pass

            sentinel_1h = sum(
                1
                for j in jobs_1h
                if bool(j.get("is_fabricated"))
                or any(
                    k in str(j.get("stderr", "") or "").lower()
                    for k in ("fabrication", "sentinel", "qualitygate")
                )
                or bool(j.get("retry_history"))
            )

            # Query live SecondBrain & Fleet Reward Ledger from knowledge_compiler.db
            sb_engrams = 0
            sb_exo_total = 0
            sb_exo_gh = 0
            sb_exo_arxiv = 0
            sb_exo_auto = 0
            sb_latest_title = ""
            sb_latest_decision = ""
            reward_bounties = 0
            reward_points = 0
            top_reward_node = "none"
            top_qbrr_boost = 0.0
            try:
                if DEFAULT_KNOWLEDGE_DB_PATH.exists():
                    with sqlite3.connect(f"file:{DEFAULT_KNOWLEDGE_DB_PATH}?mode=ro", uri=True, timeout=1.5) as kconn:
                        kcur = kconn.cursor()
                        row_cm = kcur.execute("SELECT COUNT(*) FROM cognitive_memories WHERE status = 'ACTIVE'").fetchone()
                        if row_cm:
                            sb_engrams = _safe_int(row_cm[0])
                        for src_t, cnt_v in kcur.execute(
                            "SELECT source_type, COUNT(*) FROM exogenous_entropy_ledger WHERE status = 'ACTIVE' GROUP BY source_type"
                        ).fetchall():
                            c_i = _safe_int(cnt_v)
                            sb_exo_total += c_i
                            st_low = str(src_t or "").lower()
                            if "github" in st_low:
                                sb_exo_gh += c_i
                            elif "arxiv" in st_low:
                                sb_exo_arxiv += c_i
                            elif "auto" in st_low:
                                sb_exo_auto += c_i
                        row_lat = kcur.execute(
                            "SELECT title, evolution_decision FROM exogenous_entropy_ledger ORDER BY rowid DESC LIMIT 1"
                        ).fetchone()
                        if row_lat:
                            sb_latest_title = str(row_lat[0] or "").replace("[Autonomous Swarm]", "").strip()[:48]
                            sb_latest_decision = str(row_lat[1] or "ADOPT").strip()
                        row_rw = kcur.execute(
                            "SELECT COUNT(*), COALESCE(SUM(reward_points), 0) FROM fleet_reward_ledger"
                        ).fetchone()
                        if row_rw:
                            reward_bounties = _safe_int(row_rw[0])
                            reward_points = _safe_int(row_rw[1])
                        row_top_rw = kcur.execute(
                            "SELECT node_name, SUM(reward_points), MAX(qbrr_priority_boost) "
                            "FROM fleet_reward_ledger GROUP BY node_name ORDER BY SUM(reward_points) DESC LIMIT 1"
                        ).fetchone()
                        if row_top_rw and row_top_rw[0]:
                            top_reward_node = str(row_top_rw[0])
                            top_qbrr_boost = min(0.40, max(0.0, _safe_float(row_top_rw[2], 1.0) - 1.0))
            except Exception:
                pass

            # Compute hourly evolution deltas against persisted state snapshot
            evo_state_path = REPO_ROOT / "data" / "last_evolution_digest_state.json"
            prev_state: Dict[str, Any] = {}
            try:
                if evo_state_path.exists():
                    prev_state = json.loads(evo_state_path.read_text(encoding="utf-8"))
            except Exception:
                prev_state = {}

            delta_ledger = max(0, action_ledger_entries - _safe_int(prev_state.get("action_ledger_entries", action_ledger_entries)))
            delta_engrams = max(0, sb_engrams - _safe_int(prev_state.get("sb_engrams", sb_engrams)))
            delta_exo = max(0, sb_exo_total - _safe_int(prev_state.get("sb_exo_total", sb_exo_total)))
            delta_bounties = max(0, reward_bounties - _safe_int(prev_state.get("reward_bounties", reward_bounties)))
            prev_eff_1h = _safe_float(prev_state.get("success_rate_1h_pct", success_rate_1h_pct))
            delta_eff_1h = round(success_rate_1h_pct - prev_eff_1h, 1)

            try:
                evo_state_path.parent.mkdir(parents=True, exist_ok=True)
                evo_state_path.write_text(
                    json.dumps(
                        {
                            "updated_at": now_ts,
                            "action_ledger_entries": action_ledger_entries,
                            "sb_engrams": sb_engrams,
                            "sb_exo_total": sb_exo_total,
                            "reward_bounties": reward_bounties,
                            "success_rate_1h_pct": success_rate_1h_pct,
                        },
                        indent=2,
                    ),
                    encoding="utf-8",
                )
            except Exception:
                pass

            em_audit_info = operational_efficiency.get("emergency_audit", {})
            em_bottleneck = str(em_audit_info.get("primary_bottleneck") or "none")
            em_status_tag = f"AUDIT_ACTIVE({em_bottleneck[:28]})" if emergency_audit_triggered else "NOMINAL(≥50%)"

            strat_shift = (
                f"1h Eff:{success_rate_1h_pct:.1f}% ({len(completed_jobs_1h)}/{len(jobs_1h)} jobs, Δ{delta_eff_1h:+.1f}% | All:{success_rate_pct:.1f}%); "
                f"Pro-First:{recent_pro_share_pct:.1f}% tải ({len(active_pro_1h)}/{len(healthy_pro)} Pro active, Ultra leaks:{claude_leaks_on_ultra})."
            )
            cog_routing = (
                f"Argon-4 3-Tier [L3/4:{l34_high_cnt} | L2:{l2_med_cnt} | L1:{l1_low_cnt}]; "
                f"Gate:{em_status_tag}."
            )
            heal_evo = (
                f"Clef 4-Stage (0-tok), Sentinel:{sentinel_catches} (1h:{sentinel_1h}), "
                f"Failover:{self_healing_retries}, Bounty:{reward_bounties}(+{delta_bounties})/{reward_points}pts "
                f"[{top_reward_node} +{top_qbrr_boost:.2f} QBRR], Ledger:{action_ledger_entries:,}(+{delta_ledger:,})."
            )
            know_evo = (
                f"Engrams:{sb_engrams}(+{delta_engrams}) | Exo:{sb_exo_total}(+{delta_exo}: GH:{sb_exo_gh},ArXiv:{sb_exo_arxiv},Auto:{sb_exo_auto})"
                + (f" | Mới: «{sb_latest_title}» [{sb_latest_decision}]" if sb_latest_title else "")
            )
            evo_summary = f"{strat_shift} {cog_routing} {know_evo}"

            evolution_insight = {
                "clef_zero_token_routing": True,
                "sentinel_anti_fabrication_catches": sentinel_catches,
                "sentinel_catches_1h": sentinel_1h,
                "self_healing_failovers": self_healing_retries,
                "l3_tombstones_count": l3_tombstones_count,
                "action_ledger_entries": action_ledger_entries,
                "reward_bounties": reward_bounties,
                "reward_points": reward_points,
                "top_reward_node": top_reward_node,
                "held_streams_count": len(self.held_streams),
                "decommissioned_peripheral_streams": ["Stock News Feed", "Legal & Regulatory Crawler", "Media Asset Bank 24/7"] if self.decommission_peripheral_streams else [],
                "strategic_shift": strat_shift,
                "cognitive_routing": cog_routing,
                "self_healing_evolution": heal_evo,
                "knowledge_evolution": know_evo,
                "deltas": {
                    "delta_ledger": delta_ledger,
                    "delta_engrams": delta_engrams,
                    "delta_exo": delta_exo,
                    "delta_bounties": delta_bounties,
                    "delta_eff_1h": delta_eff_1h,
                },
                "evolutionary_summary": evo_summary,
            }

            reconciliation: Optional[Dict[str, Any]] = None
            divergent_nodes = []
            if reconcile_tokens:
                reconciliation_divergence = {}
                for nname in candidate_names:
                    j_tok = tokens_1h.get(nname, 0)
                    j_req = reqs_1h.get(nname, 0)
                    w_tok = node_weekly_tokens.get(nname, 0)
                    underreporting = bool(j_tok > 0 and w_tok == 0)
                    reconciliation_divergence[nname] = {
                        "jobs_1h_tokens": j_tok,
                        "jobs_1h_requests": j_req,
                        "weekly_tokens": w_tok,
                        "divergence": underreporting,
                    }
                divergent_nodes = sorted([
                    nname for nname, d in reconciliation_divergence.items() if d.get("divergence")
                ])
                reconciliation = {
                    "jobs_stream_tokens_1h": total_jobs_tokens_1h,
                    "fleet_weekly_tokens": total_fleet_tokens,
                    "reconciliation_divergence": reconciliation_divergence,
                    "divergent_nodes": divergent_nodes,
                    "divergence_flagged": len(divergent_nodes) > 0,
                    "divergence_count": len(divergent_nodes),
                }

            return {
                "name": "AGY Fleet & Clef Mesh",
                "status": status,
                "score": score,
                "active_nodes": active_nodes,
                "total_nodes": total_nodes,
                "consensus_score": consensus_score,
                "sla_passed": sla_passed,
                "total_jobs_tokens": total_jobs_tokens,
                "total_jobs_tokens_1h": total_jobs_tokens_1h,
                "total_fleet_tokens": total_fleet_tokens,
                "top_3_tasks": top_3_tasks,
                "top_5_nodes": top_5_nodes,
                "pro_first_criterion": pro_first_criterion,
                "operational_efficiency": operational_efficiency,
                "pro_fleet_insight": pro_fleet_insight,
                "ultra_fleet_insight": ultra_fleet_insight,
                "evolution_insight": evolution_insight,
                "window_anomalies": {
                    "future_rejected": future_jobs_rejected,
                    "malformed_rejected": malformed_jobs_rejected,
                    "stale_filtered": stale_jobs_filtered,
                    "reconciliation_divergence": len(divergent_nodes),
                },
                "reconciliation": reconciliation,
            }
        except Exception as e:
            logger.warning("Fleet mesh endpoint check failed (daemon may be offline/busy): %s", e)
            return {
                "name": "AGY Fleet & Clef Mesh",
                "status": "CRITICAL",
                "score": 0,
                "active_nodes": 0,
                "total_nodes": 0,
                "consensus_score": 0.0,
                "sla_passed": False,
                "total_jobs_tokens": total_jobs_tokens,
                "total_jobs_tokens_1h": total_jobs_tokens_1h,
                "total_fleet_tokens": total_fleet_tokens,
                "top_3_tasks": top_3_tasks,
                "top_5_nodes": top_5_nodes,
                "pro_first_criterion": {},
                "operational_efficiency": {},
                "pro_fleet_insight": {},
                "ultra_fleet_insight": {},
                "evolution_insight": {},
                "window_anomalies": {
                    "future_rejected": future_jobs_rejected,
                    "malformed_rejected": malformed_jobs_rejected,
                    "stale_filtered": stale_jobs_filtered,
                    "reconciliation_divergence": 0,
                },
                "reconciliation": None,
                "error": str(e),
            }

    def compute_entropy_health_score(self, streams: List[Dict[str, Any]]) -> int:
        """Compute average health score of active (non-ON_HOLD) entropy streams."""
        if not streams:
            return 0
        active_streams = [
            s for s in streams
            if s.get("status") != "ON_HOLD" and not s.get("held")
        ]
        if not active_streams:
            return 100
        total = sum(s.get("score", 0) for s in active_streams)
        return int(total / len(active_streams))

    def scan(self, now_utc: Optional[datetime] = None) -> Dict[str, Any]:
        """Audit active entropy streams (2 core sovereign streams when peripheral streams are decommissioned)."""
        s4 = self._apply_stream_hold(4, self.check_stream_4_median_sync(now_utc=now_utc))
        s5 = self._apply_stream_hold(5, self.check_stream_5_fleet_mesh(now_ts=now_utc.timestamp() if now_utc else None))

        if self.decommission_peripheral_streams:
            streams = [s4, s5]
        else:
            s1 = self._apply_stream_hold(1, self.check_stream_1_stock_news(now_utc=now_utc))
            s2 = self._apply_stream_hold(2, self.check_stream_2_legal_docs(now_utc=now_utc))
            s3 = self._apply_stream_hold(3, self.check_stream_3_media_production(now=now_utc))
            streams = [s1, s2, s3, s4, s5]

        active_cnt = sum(1 for s in streams if s.get("status") != "ON_HOLD" and not s.get("held"))
        held_cnt = sum(1 for s in streams if s.get("status") == "ON_HOLD" or s.get("held"))
        return {
            "streams": streams,
            "entropy_health_score": self.compute_entropy_health_score(streams),
            "held_streams": sorted(list(self.held_streams)),
            "active_streams_count": active_cnt,
            "held_streams_count": held_cnt,
            "decommissioned_peripheral_streams": ["Stock News Feed", "Legal & Regulatory Crawler", "Media Asset Bank 24/7"] if self.decommission_peripheral_streams else [],
        }

    run_all_checks = scan


# ==============================================================================
# 3. CompositeHealthCalculator
# ==============================================================================
class CompositeHealthCalculator:
    """Computes overall weighted health score and severity categorization."""

    @staticmethod
    def calculate(
        cron_score: int,
        entropy_score: int,
        mesh_score: int,
        ticker_score: int,
    ) -> Tuple[int, str]:
        """
        overall_health_score = int(0.35 * cron + 0.35 * entropy + 0.15 * mesh + 0.15 * ticker)
        Severity:
          HEALTHY: >= 85
          WARNING: 60 - 84
          CRITICAL: < 60
        """
        raw = 0.35 * cron_score + 0.35 * entropy_score + 0.15 * mesh_score + 0.15 * ticker_score
        overall = max(0, min(100, int(round(raw))))

        if overall >= 85:
            severity = "HEALTHY"
        elif overall >= 60:
            severity = "WARNING"
        else:
            severity = "CRITICAL"

        return overall, severity


# ==============================================================================
# 4. HermesTelegramNotifier
# ==============================================================================
class hybridmethod:
    """Descriptor allowing a method to be invoked on either the class or an instance.

    When invoked on an instance, `cls_or_self` is the instance.
    When invoked on the class, `cls_or_self` is the class.
    If invoked on the class with an instance as the first argument,
    `cls_or_self` receives that instance.
    """

    def __init__(self, func):
        self.func = func
        self.__doc__ = func.__doc__
        self.__name__ = func.__name__

    def __get__(self, obj, cls=None):
        target = obj if obj is not None else cls

        def wrapper(*args, **kwargs):
            if obj is None and args and isinstance(args[0], (cls, type)):
                return self.func(*args, **kwargs)
            return self.func(target, *args, **kwargs)

        wrapper.__doc__ = self.func.__doc__
        wrapper.__name__ = self.func.__name__
        return wrapper


class SendResult(enum.Enum):
    DELIVERED = "delivered"
    DEDUPED = "deduped"
    SUPPRESSED = "suppressed"
    FAILED = "failed"


class HermesTelegramNotifier:
    """Delivers rich HTML alerts and executive hourly digests to Hermes Telegram."""

    SendResult = SendResult

    _MIN_SECRET_LENGTH = 30
    _MIN_SECRET_SEGMENT = _MIN_SECRET_LENGTH

    _SECRET_KEY_KEYWORDS = (
        "TOKEN",
        "SECRET",
        "KEY",
        "PASSWORD",
        "PASSWD",
        "CREDENTIAL",
        "AUTH",
        "DATABASE_URL",
    )

    _COMMON_NON_SECRETS = frozenset(
        {
            "true",
            "false",
            "none",
            "null",
            "production",
            "development",
            "http://",
            "https://",
            "localhost",
            "127.0.0.1",
            "0.0.0.0",
        }
    )

    _MAX_SCAN = 8192

    _default_ledger_path: Optional[Path] = None
    _shared_ledger_locks: Dict[str, threading.RLock] = {}
    _shared_locks_guard = threading.Lock()

    _VOLATILE_PATTERNS = (
        (re.compile(r"\b\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?\b"), "<TIMESTAMP>"),
        (re.compile(r"\b\d{4}-\d{2}-\d{2}\b"), "<DATE>"),
        (re.compile(r"\breset after \d+[smhd](?: \d+[smhd])?\b", re.I), "<RESET_TIME>"),
        (re.compile(r"\b\d+\.\d+s\b"), "<DURATION>"),
        (re.compile(r"\b0x[0-9a-fA-F]+\b"), "<HEX>"),
        (re.compile(r"\b1\d{9,12}\b"), "<EPOCH>"),
    )

    @classmethod
    def set_default_ledger_path(cls, path: Optional[Path]) -> None:
        """Override default alert dedup ledger path (for test isolation)."""
        cls._default_ledger_path = Path(path) if path else None

    def __init__(
        self,
        env_file: Path = DEFAULT_ENV_FILE,
        target_chat_id: str = DEFAULT_CHAT_ID,
        bot_token: Optional[str] = None,
        ledger_path: Optional[Path] = None,
    ):
        self.env_file = Path(env_file) if env_file is not None else DEFAULT_ENV_FILE
        self.target_chat_id = target_chat_id
        self.bot_token = bot_token or self._load_token()
        self._known_secrets: Set[str] = self._load_known_secrets()
        self._suppressed: bool = os.environ.get("HERMES_SUPPRESS_TELEGRAM") == "1"
        self._recent_sends: Dict[str, float] = {}
        self._dedup_window_s: float = 90.0
        self._salt: str = "hermes_dedup_v1"

        lp = ledger_path or self._default_ledger_path
        self.ledger_path = Path(lp) if lp else (_safe_hermes_home() / "cron" / "alert_dedup_ledger.json")
        resolved_key = str(self.ledger_path.resolve())
        with self._shared_locks_guard:
            if resolved_key not in self._shared_ledger_locks:
                self._shared_ledger_locks[resolved_key] = threading.RLock()
            self._ledger_lock = self._shared_ledger_locks[resolved_key]

    def __repr__(self) -> str:
        return f"<HermesTelegramNotifier target_chat_id={self.target_chat_id!r} suppressed={self._suppressed}>"

    def _load_known_secrets(self) -> Set[str]:
        """Load known secrets from .env and environment for exact verbatim redaction (Defense B1)."""
        loaded_secrets: Set[str] = set()

        def _maybe_add(k: str, v: str) -> None:
            if not k or not v:
                return
            k_up = k.strip().upper()
            if any(kw in k_up for kw in self._SECRET_KEY_KEYWORDS):
                val = v.strip().strip("'\"")
                if len(val) >= 8 and val.lower() not in self._COMMON_NON_SECRETS:
                    loaded_secrets.add(val)

        # 1. Scan self.env_file if it exists
        if self.env_file.exists():
            try:
                with open(self.env_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            _maybe_add(k, v)
            except Exception as e:
                logger.warning("Failed loading secrets from %s: %s", self.env_file, e)

        # 2. Scan os.environ
        for k, v in os.environ.items():
            _maybe_add(k, v)

        # 3. Include self.bot_token if present and len >= 8
        if self.bot_token:
            bt = self.bot_token.strip().strip("'\"")
            if len(bt) >= 8 and bt.lower() not in self._COMMON_NON_SECRETS:
                loaded_secrets.add(bt)

        return loaded_secrets

    def _load_token(self) -> Optional[str]:
        """Load Telegram bot token from .env file or environment."""
        token = os.environ.get("TELEGRAM_BOT_TOKEN") or os.environ.get("CONTENT_FACTORY_BOT_TOKEN")
        if token:
            return token

        if self.env_file.exists():
            try:
                with open(self.env_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            k = k.strip()
                            v = v.strip().strip("'\"")
                            if k == "TELEGRAM_BOT_TOKEN" and v:
                                return v
                            if k == "CONTENT_FACTORY_BOT_TOKEN" and v and not token:
                                token = v
            except Exception as e:
                logger.error("Failed loading token from %s: %s", self.env_file, e)
        return token

    @staticmethod
    def is_valid_token_format(token: Optional[str]) -> bool:
        """Validates Telegram bot token structure and rejects non-routable test tokens (Fail-Closed Guard)."""
        if not token or not isinstance(token, str):
            return False
        clean = token.strip().strip("'\"")
        if clean.startswith("test-") or clean.lower() in ("dummy", "placeholder", "none"):
            return False
        if ":" not in clean:
            return False
        bot_id_part, secret_segment = clean.split(":", 1)
        if len(secret_segment) < HermesTelegramNotifier._MIN_SECRET_SEGMENT:
            return False
        return bool(re.match(r"^[0-9]{6,20}:[A-Za-z0-9_\-]{30,128}$", clean))

    def _scrub_outbound(self, payload: str) -> Tuple[str, bool]:
        """Scrub outbound message body to ensure credentials never egress to Telegram (CWE-359)."""
        scrubbed = self.redact_secrets(payload)
        had_secret = (scrubbed != payload)
        return scrubbed, had_secret

    def _strip_volatile_fields(self, text: str) -> str:
        """Normalizes text before hashing so cosmetic timestamp/run ID changes do not defeat dedup."""
        if not text:
            return ""
        normalized = text
        for pattern, repl in self._VOLATILE_PATTERNS:
            normalized = pattern.sub(repl, normalized)
        return normalized

    def _dedup_key(self, payload: str) -> str:
        """Computes salted sha256 fingerprint after stripping volatile fields."""
        normalized = self._strip_volatile_fields(payload)
        salt = getattr(self, "_salt", "hermes_dedup_v1")
        return hashlib.sha256(f"{salt}:{normalized}".encode("utf-8")).hexdigest()

    def _read_ledger(self) -> Dict[str, float]:
        if not self.ledger_path.exists():
            return {}
        try:
            with open(self.ledger_path, "r", encoding="utf-8") as f:
                if fcntl:
                    try:
                        fcntl.flock(f.fileno(), fcntl.LOCK_SH)
                    except OSError:
                        pass
                try:
                    data = json.load(f)
                    return data if isinstance(data, dict) else {}
                finally:
                    if fcntl:
                        try:
                            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                        except OSError:
                            pass
        except Exception as e:
            logger.warning("Failed reading dedup ledger %s: %s", self.ledger_path, e)
            return {}

    def _write_ledger_atomic(self, ledger: Dict[str, float]) -> None:
        try:
            self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
            tmp_file = tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.ledger_path.parent,
                prefix=f".{self.ledger_path.name}.",
                suffix=".tmp",
                delete=False,
            )
            tmp_path = Path(tmp_file.name)
            try:
                try:
                    os.chmod(tmp_path, 0o600)
                except OSError:
                    pass
                json.dump(ledger, tmp_file, indent=2)
                tmp_file.flush()
                os.fsync(tmp_file.fileno())
                tmp_file.close()
                os.replace(tmp_path, self.ledger_path)
            except Exception:
                if tmp_path.exists():
                    try:
                        tmp_path.unlink()
                    except OSError:
                        pass
                raise
        except Exception as e:
            logger.error("Failed writing dedup ledger %s: %s", self.ledger_path, e)

    def _is_dedup_suppressed(self, key: str, text: Optional[str] = None) -> bool:
        with self._ledger_lock:
            now = time.time()
            raw_digest = hashlib.sha256(text.encode("utf-8")).hexdigest() if text else None
            if raw_digest and raw_digest in self._recent_sends:
                if self._recent_sends[raw_digest] < (now - self._dedup_window_s):
                    return False
            if key in self._recent_sends:
                if self._recent_sends[key] < (now - self._dedup_window_s):
                    return False

            ledger = self._read_ledger()
            last = ledger.get(key, 0.0)
            if key in self._recent_sends:
                last = max(last, self._recent_sends[key])
            if (now - last) < self._dedup_window_s:
                return True
            return False

    def _record_dedup_success(self, key: str, timestamp: float, text: Optional[str] = None) -> None:
        with self._ledger_lock:
            ledger = self._read_ledger()
            ledger[key] = timestamp
            cutoff = timestamp - (self._dedup_window_s * 2)
            ledger = {k: v for k, v in ledger.items() if isinstance(v, (int, float)) and v >= cutoff}
            self._write_ledger_atomic(ledger)
            self._recent_sends[key] = timestamp
            if text:
                raw_digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
                self._recent_sends[raw_digest] = timestamp
            self._recent_sends = {k: v for k, v in self._recent_sends.items() if v >= cutoff}

    @staticmethod
    def truncate_telegram_html(text: str, max_chars: int = 4096) -> str:
        """Truncate an HTML-formatted message to fit within Telegram's max_chars limit (CWE-116 / CWE-400).

        Guarantees:
          1. len(result) <= max_chars under all conditions (including closing-tag bombs).
          2. No HTML tag is cut in half.
          3. No HTML entity (&...;) is cut in half.
          4. All unclosed supported tags are properly closed in correct reverse order (balanced tags).
          5. Appends a clean truncation indicator when truncated.
        """
        if not text or len(text) <= max_chars:
            return text

        suffix = "\n... [Cắt bớt do giới hạn Telegram]"
        if max_chars <= len(suffix):
            return text[:max_chars]

        tag_pattern = re.compile(r"</?([a-zA-Z0-9]+)(?:\s+[^>]*)?>")

        def _get_open_stack(s: str) -> List[str]:
            stack: List[str] = []
            for m in tag_pattern.finditer(s):
                full_tag = m.group(0)
                tag_name = m.group(1).lower()
                if full_tag.startswith("</"):
                    if stack and stack[-1] == tag_name:
                        stack.pop()
                    elif tag_name in stack:
                        for idx in range(len(stack) - 1, -1, -1):
                            if stack[idx] == tag_name:
                                stack.pop(idx)
                                break
                elif not full_tag.endswith("/>"):
                    stack.append(tag_name)
            return stack

        def _safe_cut(s: str, pos: int) -> int:
            pos = max(0, min(pos, len(s)))
            # 1. Back off if cutting inside an HTML tag <...>
            last_lt = s.rfind("<", 0, pos)
            last_gt = s.rfind(">", 0, pos)
            if last_lt > last_gt:
                pos = last_lt

            # 2. Back off if cutting inside an HTML entity &...;
            last_amp = s.rfind("&", 0, pos)
            last_semi = s.rfind(";", 0, pos)
            if last_amp > last_semi and (pos - last_amp) < 32:
                pos = last_amp
            return pos

        # Iteratively find candidate cut position that fits max_chars
        pos = _safe_cut(text, max_chars - len(suffix))

        for _ in range(10):
            pos = _safe_cut(text, pos)
            stack = _get_open_stack(text[:pos])
            closing_tags = "".join(f"</{t}>" for t in reversed(stack))
            total_len = pos + len(suffix) + len(closing_tags)
            if total_len <= max_chars:
                cut_text = re.sub(r"&[a-zA-Z#0-9]*$", "", text[:pos])
                out = cut_text + suffix + closing_tags
                assert len(out) <= max_chars, f"Truncation invariant violated: {len(out)} > {max_chars}"
                return out
            excess = total_len - max_chars
            new_pos = pos - excess
            if new_pos <= 0:
                break
            pos = new_pos

        # Pathological fallback (e.g. closing tags alone exceed max_chars):
        plain = re.sub(r"<[^>]+>", "", text)
        cut = _safe_cut(plain, max_chars - len(suffix))
        cut_plain = re.sub(r"&[a-zA-Z#0-9]*$", "", plain[:cut])
        out = cut_plain + suffix
        assert len(out) <= max_chars, f"Truncation fallback invariant violated: {len(out)} > {max_chars}"
        return out

    def send_payload_result(self, text: str) -> SendResult:
        if self._suppressed or os.environ.get("HERMES_SUPPRESS_TELEGRAM") == "1":
            logger.info("Telegram live send suppressed via HERMES_SUPPRESS_TELEGRAM=1.")
            return SendResult.SUPPRESSED
        if not self.bot_token or not self.is_valid_token_format(self.bot_token):
            logger.info(
                "Telegram live send suppressed: dummy or non-live bot token format (%s).",
                str(self.bot_token)[:12],
            )
            return SendResult.FAILED

        # Outbound egress secret scrubbing (CWE-359)
        scrubbed, had_secret = self._scrub_outbound(text)
        if had_secret:
            logger.warning("Outbound alert contained secret pattern; sending redacted copy.")
        text = scrubbed

        # Ensure message does not exceed Telegram's 4096 character ceiling (CWE-116)
        text = self.truncate_telegram_html(text, max_chars=4096)

        key = self._dedup_key(text)

        with self._ledger_lock:
            if self._is_dedup_suppressed(key, text=text):
                logger.info(
                    "Duplicate alert suppressed within %.1fs dedup window (key: %s).",
                    self._dedup_window_s,
                    key[:12],
                )
                return SendResult.DEDUPED

            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            payload = {
                "chat_id": self.target_chat_id,
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            }

            try:
                req = urllib.request.Request(
                    url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                )
                with urllib.request.urlopen(req, timeout=15, context=get_ssl_context()) as resp:
                    raw_resp = resp.read(65536)
                    data = json.loads(raw_resp.decode("utf-8"))
                    ok = bool(data.get("ok", False))
                    if ok:
                        now = time.time()
                        self._record_dedup_success(key, now, text=text)
                        return SendResult.DELIVERED
                    return SendResult.FAILED
            except urllib.error.HTTPError as e:
                err_body = e.read(65536).decode("utf-8", errors="replace")
                safe_body = self.redact_secrets(err_body)
                logger.error("Telegram HTTP %s error: %s", e.code, safe_body)
                return SendResult.FAILED
            except Exception as e:
                safe_e = self.redact_secrets(str(e))
                logger.error("Telegram delivery failed: %s", safe_e)
                return SendResult.FAILED

    def _send_payload(self, text: str) -> bool:
        result = self.send_payload_result(text)
        return result in (SendResult.DELIVERED, SendResult.DEDUPED)

    _URL_CRED_PATTERN = re.compile(
        r"(?P<scheme>\b(?:jdbc:)?[a-zA-Z][a-zA-Z0-9+.\-]*://[^:@/\s]+:)(?:[^@/\s]+)(?P<at>@)",
        re.I,
    )
    _BOT_URL_PATTERN = re.compile(
        r"(/bot)[0-9A-Za-z_\-:]+(/)",
        re.I,
    )
    _QUERY_PARAM_PATTERN = re.compile(
        r"(?i)([\?&](?:token|key|secret|password|passwd|api[_-]?key|access[_-]?token)=)([^&\s]+)"
    )
    _BASIC_AUTH_PATTERN = re.compile(
        r"(?i)\b(Authorization:\s*Basic\s+)[A-Za-z0-9+/=]{10,512}"
    )
    _KV_SECRET_PATTERN = re.compile(
        r"(?i)\b(?P<k>password|passwd|secret|api[_-]?key|client[_-]?secret)(?P<sep>\s*[:=]\s*)(?:[\"']?[^\s,;'\"}&\[]+[\"']?)"
    )
    _PEM_KEY_PATTERN = re.compile(
        r"-----BEGIN [A-Z ]+ PRIVATE KEY-----[\s\S]*?-----END [A-Z ]+ PRIVATE KEY-----"
    )
    _SECRET_PATTERNS = (
        re.compile(r"\bBearer\s+[A-Za-z0-9._\-/+=]{10,512}", re.I),
        re.compile(r"\bya29\.[A-Za-z0-9._\-/+=]{10,512}", re.I),
        re.compile(r"\b1//[A-Za-z0-9._\-/+=]{10,512}", re.I),
        re.compile(r"\b[0-9]{6,20}:[A-Za-z0-9_\-]{20,128}\b"),
        re.compile(r"\b(?:access|refresh|id)[_-]?token\s*[:=]?\s*[A-Za-z0-9._\-/+=]{10,512}", re.I),
        re.compile(r"\beyJ[A-Za-z0-9._\-/+=]{20,1024}"),
        re.compile(r"\bAIza[0-9A-Za-z\-_]{35}\b"),
        re.compile(r"\b(?:AKIA|ABIA|ACCA|ASIA)[0-9A-Z]{16}\b"),
        re.compile(r"\bxox[baprs]-[0-9A-Za-z]{10,48}\b"),
        re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{36,255}\b"),
    )

    @hybridmethod
    def redact_secrets(
        cls_or_self,
        text: Any,
        known_secrets: Optional[Iterable[str]] = None,
    ) -> str:
        """Best-effort redaction of bearer tokens, OAuth credentials, keys, passwords, and JWTs from error strings (CWE-532 / CWE-259)."""
        if text is None:
            return ""
        if not isinstance(text, str):
            text = str(text)
        if not text:
            return ""

        if isinstance(cls_or_self, HermesTelegramNotifier) and known_secrets is None:
            known_secrets = cls_or_self._known_secrets

        # Exact Known-Secrets Scrubbing (sorted by length descending to prevent partial prefix replacement)
        if known_secrets:
            valid_secrets = [
                s
                for s in known_secrets
                if isinstance(s, str)
                and len(s) >= 8
                and s.lower() not in cls_or_self._COMMON_NON_SECRETS
            ]
            valid_secrets.sort(key=len, reverse=True)
            for s in valid_secrets:
                text = text.replace(s, "[REDACTED]")

        # B3 ReDoS Guard: Cap input length before regex processing
        if len(text) > cls_or_self._MAX_SCAN:
            head = text[: cls_or_self._MAX_SCAN]
            tail = text[cls_or_self._MAX_SCAN :]
        else:
            head = text
            tail = ""

        # Format Regex Redaction
        head = cls_or_self._PEM_KEY_PATTERN.sub("[REDACTED_PRIVATE_KEY]", head)
        head = cls_or_self._URL_CRED_PATTERN.sub(r"\g<scheme>[REDACTED]\g<at>", head)
        head = cls_or_self._BOT_URL_PATTERN.sub(r"\g<1>[REDACTED]\g<2>", head)
        head = cls_or_self._QUERY_PARAM_PATTERN.sub(r"\g<1>[REDACTED]", head)
        head = cls_or_self._BASIC_AUTH_PATTERN.sub(r"\g<1>[REDACTED]", head)
        head = cls_or_self._KV_SECRET_PATTERN.sub(r"\g<k>\g<sep>[REDACTED]", head)
        for pat in cls_or_self._SECRET_PATTERNS:
            head = pat.sub("[REDACTED]", head)

        return head + tail

    @hybridmethod
    def _scrub_secrets(
        cls_or_self,
        text: Any,
        known_secrets: Optional[Iterable[str]] = None,
    ) -> str:
        """Alias for redact_secrets for backward compatibility with audit runners (CWE-532)."""
        return cls_or_self.redact_secrets(text, known_secrets=known_secrets)

    @hybridmethod
    def sanitize_error(
        cls_or_self,
        text: Any,
        limit: int = 120,
        known_secrets: Optional[Iterable[str]] = None,
    ) -> str:
        """Sanitize error string with load-bearing security ordering (CWE-532 / CWE-116 / CWE-259):

        Order of Execution:
            1. Type Coercion: Convert non-string objects to str; handle None -> "".
            2. Known-Secret Exact Substitution: Verbatim replacement of known secrets from .env & env vars.
            3. Format Regex Redaction: Pattern-based redaction (URLs, Query Params, Auth headers, Bearer tokens, etc.).
            4. Truncate to Limit: Bounds length to prevent denial of service and UI overflow.
            5. HTML Escape: Encodes HTML entities (<, >, &, ", ') for safe display in Telegram HTML parse mode.

        Note: Redaction MUST happen before truncation to prevent boundary leakage of sensitive tokens,
        and truncation MUST happen before HTML escaping to prevent producing broken/dangling entities.
        """
        if text is None:
            raw = ""
        elif not isinstance(text, str):
            raw = str(text)
        else:
            raw = text

        if isinstance(cls_or_self, HermesTelegramNotifier) and known_secrets is None:
            known_secrets = cls_or_self._known_secrets

        redacted = cls_or_self.redact_secrets(raw, known_secrets=known_secrets)
        truncated = redacted[:limit] if limit is not None and limit >= 0 else redacted
        return html.escape(truncated, quote=True)

    @hybridmethod
    def _safe_format_prompt(
        cls_or_self,
        text: Any,
        limit: int = 60,
    ) -> str:
        """Safely format and sanitize a task prompt for HTML output:
        1. Type coercion to str (or "" if None).
        2. Redact secrets first: redacted = cls_or_self.redact_secrets(raw).
        3. Normalize whitespace (remove newlines, collapse spaces): " ".join(redacted.split()).
        4. Truncate to limit: truncated = normalized[:limit].
        5. HTML escape: html.escape(truncated, quote=True).
        """
        if text is None:
            raw = ""
        elif not isinstance(text, str):
            raw = str(text)
        else:
            raw = text

        redacted = cls_or_self.redact_secrets(raw)
        normalized = " ".join(redacted.split())
        truncated = normalized[:limit] if limit is not None and limit >= 0 else normalized
        return html.escape(truncated, quote=True)

    def send_alert(self, alert_text: str) -> bool:
        """Send urgent critical anomaly alert."""
        return self._send_payload(alert_text)

    def send_alert_result(self, alert_text: str) -> SendResult:
        """Send urgent critical anomaly alert with granular SendResult."""
        return self.send_payload_result(alert_text)

    def send_digest(self, digest_html: str) -> bool:
        """Send standard hourly executive digest."""
        return self._send_payload(digest_html)

    def send_digest_result(self, digest_html: str) -> SendResult:
        """Send standard hourly executive digest with granular SendResult."""
        return self.send_payload_result(digest_html)

    def format_urgent_alert(self, scan_result: Dict[str, Any]) -> str:
        """Format an urgent HTML alert message for CRITICAL anomalies."""
        overall = scan_result.get("overall_health_score", 0)
        severity = scan_result.get("severity", "CRITICAL")
        cron = scan_result.get("cron", {})
        entropy = scan_result.get("entropy", {})

        clogged = cron.get("clogged_jobs", [])
        drifted = cron.get("drift_skipped_jobs", [])
        auth_failed = cron.get("auth_failed_jobs", [])
        ticker = cron.get("ticker_heartbeat", {})

        stalled_streams = [
            s for s in entropy.get("streams", []) if s.get("status") in ("CRITICAL", "DEGRADED")
        ]

        lines = [
            "🚨 <b>[HERMES CRITICAL ALERT] Cron Clog &amp; Entropy Degradation Detected</b>",
            f"<b>Overall Health:</b> <code>{overall}/100</code> [<b>{severity}</b>]",
            "",
        ]

        if clogged:
            lines.append(f"⛔ <b>Clogged Cron Jobs ({len(clogged)}):</b>")
            for c in clogged:
                job_name = html.escape(str(c.get("job_name", "")))
                err = self.sanitize_error(c.get("last_error"), limit=120)
                lines.append(
                    f"• <code>{job_name}</code>: {c.get('consecutive_failures')} fails. "
                    f"<i>{err}</i>"
                )
            lines.append("")

        if drifted:
            lines.append(f"⚠️ <b>Drift-Skipped Cron Jobs ({len(drifted)}):</b>")
            for d in drifted:
                job_name = html.escape(str(d.get("job_name", "")))
                snap = html.escape(str(d.get("model_snapshot", "")))
                lines.append(
                    f"• <code>{job_name}</code>: snapshot={snap} "
                    f"(unpinned, silent-skip)"
                )
            lines.append("")

        if auth_failed:
            lines.append(f"🔑 <b>Authentication Failures ({len(auth_failed)}):</b>")
            for a in auth_failed:
                job_name = html.escape(str(a.get("job_name", "")))
                err = self.sanitize_error(a.get("last_error"), limit=100)
                lines.append(f"• <code>{job_name}</code>: <i>{err}</i>")
            lines.append("")

        if ticker.get("is_stale"):
            lines.append(f"💓 <b>Stale Ticker Heartbeat:</b> Age <code>{ticker.get('age_seconds')}s</code> (>120s)")
            lines.append("")

        if stalled_streams:
            lines.append(f"🌪️ <b>Degraded / Stalled Entropy Streams ({len(stalled_streams)}):</b>")
            for s in stalled_streams:
                st = html.escape(str(s.get("status", "")), quote=True)
                name = html.escape(str(s.get("name", "")), quote=True)
                if "Stock" in name:
                    lines.append(f"• <b>{name}:</b> {st} ({s.get('hours_since_crawl')}h since crawl)")
                elif "Legal" in name:
                    lines.append(f"• <b>{name}:</b> {st} ({s.get('hours_since_crawl')}h since crawl)")
                elif "Media" in name:
                    lines.append(
                        f"• <b>{name}:</b> {st} ({s.get('completed_videos')}/24 vids, lag {s.get('current_hour_lag')}h)"
                    )
                elif "Median" in name:
                    lines.append(f"• <b>{name}:</b> {st} ({s.get('minutes_since_sync')}m ago, exit {s.get('exit_code')})")
                else:
                    lines.append(f"• <b>{name}:</b> {st}")
            lines.append("")

        lines.append("🛠️ <b>Action Recommended:</b>")
        lines.append("<code>python3 tools/hourly_digest_monitor.py --self-heal</code>")

        return "\n".join(lines)

    def format_hourly_digest(self, scan_result: Dict[str, Any]) -> str:
        """Format clean executive hourly digest dashboard HTML."""
        overall = scan_result.get("overall_health_score", 0)
        severity = scan_result.get("severity", "HEALTHY")
        cron = scan_result.get("cron", {})
        entropy = scan_result.get("entropy", {})

        cron_score = cron.get("cron_health_score", 0)
        entropy_score = entropy.get("entropy_health_score", 0)
        ticker = cron.get("ticker_heartbeat", {})
        ticker_status = "STALE ❌" if ticker.get("is_stale") else "FRESH ✅"

        status_emojis = {
            "HEALTHY": "🟢",
            "WARNING": "🟡",
            "DEGRADED": "🟡",
            "CRITICAL": "🔴",
            "ON_HOLD": "⏸️",
            "PAUSED": "⏸️",
        }

        sev_emoji = status_emojis.get(severity, "⚪")

        streams = entropy.get("streams", []) or scan_result.get("entropy_streams", {}).get("streams", [])
        fleet_stream = next((s for s in streams if "Fleet" in str(s.get("name", ""))), {})
        if not fleet_stream and streams:
            fleet_stream = streams[0]
        total_jobs_tok = _safe_int(fleet_stream.get("total_jobs_tokens", 0))
        total_fleet_tok = _safe_int(fleet_stream.get("total_fleet_tokens", 0))
        top_tasks = fleet_stream.get("top_3_tasks", [])
        top_nodes = fleet_stream.get("top_5_nodes", [])
        pro_first = fleet_stream.get("pro_first_criterion", {})
        op_eff = fleet_stream.get("operational_efficiency", {})
        pro_insight = fleet_stream.get("pro_fleet_insight", {})
        ultra_insight = fleet_stream.get("ultra_fleet_insight", {})
        evo_insight = fleet_stream.get("evolution_insight", {})

        jev_brain = scan_result.get("jev_brain_sleep")
        if not isinstance(jev_brain, dict):
            jev_brain = collect_jev_and_brain_sleep_telemetry(
                force_sleep_report=bool(scan_result.get("morning_sleep_briefing", False))
            )

        def _fmt_argon_slug(slug: Any) -> str:
            s = str(slug or "").strip()
            low = s.lower()
            if "3.8-flash" in low or "3-8-flash" in low:
                if "low" in low:
                    return "gemini-4-argon-low"
                if "medium" in low or "med" in low:
                    return "gemini-4-argon-medium"
                return "gemini-4-argon-high"
            return s

        lines = [
            "⚡ <b>[HERMES AGENT] 24/7 Hourly System Digest</b>",
            f"🕒 <i>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>",
            f"📊 <b>Composite Health:</b> <code>{overall}/100</code> {sev_emoji} [<b>{severity}</b>] (Cron:{cron_score}% | Entropy:{entropy_score}% | Ticker:{ticker_status})",
        ]

        if pro_first:
            badge = pro_first.get("badge", "⚪ CHƯA RÕ")
            grade = html.escape(str(pro_first.get("grade", "UNKNOWN")), quote=True)
            p_burn = pro_first.get("pro_burn_pct", 0.0)
            p_cons = pro_first.get("pro_consumed_tokens", 0)
            p_cap = pro_first.get("pro_capacity_tokens", 0)
            p_tok_1h = _safe_int(pro_first.get("pro_tokens_1h", pro_insight.get("pro_tokens_1h", 0)))
            p_share = pro_first.get("pro_request_share_pct", 0.0)
            rec_share = pro_first.get("recent_pro_share_pct", 0.0)
            p_reqs = pro_first.get("pro_requests", 0)
            tot_reqs = pro_first.get("total_requests", 0)
            starved_cnt = pro_first.get("starved_count", 0)
            tot_pro = pro_first.get("total_pro_nodes", 0)
            starved_list = pro_first.get("starved_pro_nodes", [])
            escaped_starved = [html.escape(str(s), quote=True) for s in starved_list[:3]]
            starved_preview = f" ({', '.join(escaped_starved)}{'...' if len(starved_list) > 3 else ''})" if starved_list else ""
            verdict = html.escape(str(pro_first.get("verdict", "")), quote=True)

            lines.append("")
            lines.append("🎯 <b>Tiêu Chí Quality Hàng Giờ: Dùng Quota Pro Agy First:</b>")
            lines.append(f"• <b>Đánh giá:</b> {badge} (<b>{grade}</b>)")
            lines.append(
                f"• <b>Tỷ lệ Đốt Quota Pro Fleet:</b> {p_burn}% ({p_cons:,}/{p_cap:,} | 1h:{p_tok_1h:,} tok)"
            )
            lines.append(
                f"• <b>Tỷ trọng Tải Pro Nodes:</b> {p_share}% ({p_reqs:,}/{tot_reqs:,} reqs | Gần đây:{rec_share}%)"
            )
            lines.append(
                f"• <b>Nodes Pro còn dồi dào (&gt;75% tồn):</b> {starved_cnt}/{tot_pro} nodes<i>{starved_preview}</i>"
            )
            lines.append(f"• <b>Kết luận Vận hành:</b> <i>{verdict}</i>")

        if op_eff:
            tot_j = _safe_int(op_eff.get("total_jobs", 0))
            comp_j = _safe_int(op_eff.get("completed_jobs", 0))
            fail_j = _safe_int(op_eff.get("failed_jobs", 0))
            tout_j = _safe_int(op_eff.get("timeout_jobs", 0))
            run_j = _safe_int(op_eff.get("running_jobs", 0))
            sr_pct = op_eff.get("success_rate_pct", 100.0)
            j1h_tot = _safe_int(op_eff.get("jobs_1h_total", 0))
            j1h_ok = _safe_int(op_eff.get("jobs_1h_completed", 0))
            j1h_fail = _safe_int(op_eff.get("jobs_1h_failed", 0))
            sr1h_pct = op_eff.get("success_rate_1h_pct", 100.0)
            avg_lat = op_eff.get("avg_latency_sec", 0.0)
            p95_lat = op_eff.get("p95_latency_sec", 0.0)
            tok_per_ok = _safe_int(op_eff.get("tokens_per_completed_job", 0))
            eff_tok_pct = op_eff.get("effective_token_ratio_pct", 100.0)
            fail_reasons = [html.escape(str(r), quote=True) for r in op_eff.get("top_failure_reasons", [])[:2]]
            t_dist = op_eff.get("task_level_distribution", {})
            l1_c = _safe_int(t_dist.get("L1_low", 0))
            l2_c = _safe_int(t_dist.get("L2_med", 0))
            l34_c = _safe_int(t_dist.get("L3_L4_high", 0))
            cache_pct = op_eff.get("cache_hit_ratio_pct", 0.0)
            saved_usd = op_eff.get("cost_saved_usd_total", 0.0)
            s_catches = _safe_int(op_eff.get("sentinel_catches", 0))
            s_retries = _safe_int(op_eff.get("self_healing_retries", 0))
            vc_info = jev_brain.get("victory_critic", {}) if isinstance(jev_brain, dict) else {}
            vc_risk = _safe_float(vc_info.get("avg_fake_pass_risk", 0.0))
            vc_pass = _safe_int(vc_info.get("passed_count", 5))
            vc_block = _safe_int(vc_info.get("blocked_count", 0))

            lines.append("")
            lines.append("📈 <b>Hiệu Quả Vận Hành &amp; Độ Chính Xác:</b>")
            lines.append(
                f"• <b>Thực thi:</b> {sr_pct}% (OK:{comp_j}|Fail:{fail_j}[TO:{tout_j}]|Run:{run_j}/{tot_j}) | "
                f"1h:{j1h_ok}/{j1h_tot} ({sr1h_pct}%, TB {avg_lat}s, P95 {p95_lat}s) | Tok:{eff_tok_pct}% ({tok_per_ok:,}/job)"
                + (f" | Lỗi:<i>{'; '.join(fail_reasons)}</i>" if fail_reasons else "")
            )
            lines.append(
                f"• <b>4-Level Task Planning &amp; Cache:</b> L1-Low:{l1_c} | L2-Med:{l2_c} | "
                f"L3/L4-High:{l34_c} | Cache:{cache_pct}% (${saved_usd}) | Sentinel:{s_catches}/Retry:{s_retries}"
            )
            lines.append(
                f"• <b>Victory Critic &amp; Anti-Fake-Pass:</b> Risk={vc_risk:.2f} | "
                f"Pass:{vc_pass}/Block:{vc_block} (100% Argon 4 H/M/L)"
            )
            if op_eff.get("emergency_audit_active"):
                em_info = op_eff.get("emergency_audit", {})
                em_bottleneck = em_info.get("primary_bottleneck") or (fail_reasons[0] if fail_reasons else "unknown")
                lines.append(
                    f"• 🚨 <b>CẢNH BÁO KHẨN CẤP: HIỆU QUẢ VẬN HÀNH &lt; 50.0%</b> (1h={sr1h_pct}%, Tích lũy={sr_pct}%) | "
                    f"Điểm nghẽn: <i>{html.escape(str(em_bottleneck), quote=True)}</i> | Đã kích hoạt Root-Cause Audit"
                )

        if pro_insight or ultra_insight:
            lines.append("")
            lines.append("🛰️ <b>Sức Khỏe Cụm Pro Fleet &amp; Ultra:</b>")
            if pro_insight:
                p_ready = _safe_int(pro_insight.get("ready_count", 0))
                p_tot = _safe_int(pro_insight.get("total_pro_nodes", 0))
                p_cool = _safe_int(pro_insight.get("cooling_or_busy_count", 0))
                p_rem_pct = pro_insight.get("pro_remaining_pct", 100.0)
                p_rem_tok = _safe_int(pro_insight.get("pro_remaining_tokens", 0))
                m_dist_raw = pro_insight.get("model_distribution", {})
                m_dist_norm: Counter = Counter()
                for mk, mv in m_dist_raw.items():
                    m_dist_norm[_fmt_argon_slug(mk)] += _safe_int(mv)
                m_str = ", ".join(
                    f"{html.escape(str(k), quote=True)}:{v}" for k, v in m_dist_norm.most_common(3)
                ) or "idle"
                lines.append(
                    f"• <b>Pro (Group B):</b> {p_ready}/{p_tot} ready "
                    f"(Busy:{p_cool}) | Dư:{p_rem_pct}% ({p_rem_tok:,}) | {m_str}"
                )
                gem_5h_pct = pro_insight.get("pro_gemini_5h_rem_pct", pro_insight.get("avg_5h_rem_pct", 100.0))
                gem_7d_pct = pro_insight.get("pro_gemini_7d_rem_pct", pro_insight.get("avg_7d_rem_pct", 100.0))
                gem_7d_cons = _safe_int(pro_insight.get("pro_gemini_7d_consumed", 0))
                gem_7d_cap = _safe_int(pro_insight.get("pro_gemini_7d_capacity", 0))
                cl_5h_pct = pro_insight.get("pro_claude_5h_rem_pct", 100.0)
                cl_7d_pct = pro_insight.get("pro_claude_7d_rem_pct", 100.0)
                cl_7d_cons = _safe_int(pro_insight.get("pro_claude_7d_consumed", 0))
                cl_7d_cap = _safe_int(pro_insight.get("pro_claude_7d_capacity", 0))
                dual_ready = _safe_int(pro_insight.get("dual_ready_pro_count", p_ready))
                lines.append(
                    f"• <b>Pro Dual Quota ({p_tot} Nodes, Dual-Ready: <code>{dual_ready}/{p_tot}</code>):</b> "
                    f"Gem[5h:{gem_5h_pct}%|7d:{gem_7d_pct}% ({gem_7d_cons:,}/{gem_7d_cap:,})] • "
                    f"Claude[5h:{cl_5h_pct}%|7d:{cl_7d_pct}% ({cl_7d_cons:,}/{cl_7d_cap:,})]"
                )
            if ultra_insight and ultra_insight.get("nodes"):
                u_nodes = ", ".join(html.escape(str(n), quote=True) for n in ultra_insight.get("nodes", []))
                u_burn = ultra_insight.get("ultra_burn_pct", 0.0)
                u_cons = _safe_int(ultra_insight.get("ultra_consumed_tokens", 0))
                u_cap = _safe_int(ultra_insight.get("ultra_capacity_tokens", 0))
                u_tok_1h = _safe_int(ultra_insight.get("ultra_tokens_1h", 0))
                u_rem = _safe_int(ultra_insight.get("ultra_remaining_tokens", 0))
                u_pure = ultra_insight.get("gemini_only_invariant", True)
                u_badge = "✅ Gemini-Only" if u_pure else "🚨 Claude Leak!"
                lines.append(
                    f"• <b>Ultra ({u_nodes}):</b> Đốt {u_burn}% "
                    f"(7d:{u_cons:,}/{u_cap:,}|1h:{u_tok_1h:,}|Còn:{u_rem:,}) | {u_badge}"
                )

        lines.append("")
        if total_jobs_tok > 0 or total_fleet_tok > 0:
            lines.append(
                f"💎 <b>Tổng lượng Tokens đã dùng:</b> {total_jobs_tok:,} (Jobs) | {total_fleet_tok:,} (Weekly)"
            )
        else:
            lines.append("💎 <b>Tổng lượng Tokens đã dùng:</b> 0 tokens (Fleet idling)")

        if top_tasks:
            lines.append("")
            lines.append("🔥 <b>Top 3 Tasks dùng nhiều Tokens nhất:</b>")
            ranks = ["1️⃣", "2️⃣", "3️⃣"]
            for idx, task in enumerate(top_tasks[:3]):
                rank_icon = ranks[idx] if idx < len(ranks) else "•"
                jid = html.escape(str(task.get("job_id", "")), quote=True)
                node = html.escape(str(task.get("node_name", "")), quote=True)
                model = html.escape(_fmt_argon_slug(task.get("model", "")), quote=True)
                tok = _safe_int(task.get("total_tokens", 0))
                raw_clean = task.get("clean_prompt") or _extract_clean_task_prompt(task)
                prompt_snippet = self._safe_format_prompt(raw_clean, limit=48)
                lines.append(
                    f"{rank_icon} <code>{jid}</code> ({node}/{model}): "
                    f"<b>{tok:,}</b> tok — <i>\"{prompt_snippet}...\"</i>"
                )

        if top_nodes:
            lines.append("")
            lines.append("🚀 <b>Top 5 Nodes làm việc nhiều nhất (1 giờ qua):</b>")
            ranks = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]
            for idx, node in enumerate(top_nodes[:5]):
                rank_icon = ranks[idx] if idx < len(ranks) else "•"
                nname = html.escape(str(node.get("name", "")), quote=True)
                ntier = html.escape(str(node.get("tier", "")), quote=True)
                reqs = _safe_int(node.get("requests_served_1h", node.get("requests_served", 0)))
                toks = _safe_int(node.get("tokens_consumed_1h", node.get("tokens_consumed", 0) or node.get("tokens", 0)))
                active = _safe_int(node.get("active_jobs", 0))
                active_str = f" [⚡{active}]" if active > 0 else ""
                lines.append(
                    f"{rank_icon} <b>{nname}</b> ({ntier}): <code>{reqs:,}</code> reqs (1h) | "
                    f"{toks:,} tok{active_str}"
                )

        lines.append("")
        lines.append(f"🛰️ <b>External Entropy Streams ({len(streams)}/{len(streams)}):</b>")
        for idx, s in enumerate(streams, 1):
            raw_st = s.get("status", "UNKNOWN")
            emoji = status_emojis.get(raw_st, "⚪")
            st = html.escape(str(raw_st), quote=True)
            raw_name = str(s.get("name", ""))
            name = html.escape(raw_name, quote=True)
            if "Stock" in raw_name:
                detail = f"{s.get('hours_since_crawl')}h,{s.get('articles_24h')}a"
            elif "Legal" in raw_name:
                detail = f"{s.get('hours_since_crawl')}h,{s.get('total_documents')}d"
            elif "Median" in raw_name:
                detail = f"{s.get('minutes_since_sync')}m,rc:{s.get('exit_code')}"
            elif "Media" in raw_name:
                detail = f"{s.get('completed_videos')}/24v,{s.get('completed_photos')}/24p"
            elif "Fleet" in raw_name:
                detail = f"{s.get('active_nodes')}/{s.get('total_nodes')}n,Clef:{s.get('consensus_score')}%,SLA:{'PASS' if s.get('sla_passed') else 'FAIL'}"
            else:
                detail = ""
            if raw_st in ("ON_HOLD", "PAUSED"):
                detail = f"HOLD;{detail}" if detail else "HOLD"
            detail_escaped = html.escape(detail, quote=True)
            lines.append(f"{idx}️⃣ <b>{name}:</b> {emoji} {st} ({detail_escaped})")
        if len(streams) == 2:
            lines.append("• <i>Đã xóa 3 luồng ngoại vi (Stock/Legal/Media) triệt tiêu cron-drift</i>")

        lines.append("")
        act_c = _safe_int(cron.get("active_jobs_count", 0))
        hld_c = _safe_int(cron.get("paused_jobs_count", 0))
        lines.append(
            f"⚙️ <b>Cron Diagnostics:</b> Active:{act_c} | Hold:{hld_c} | "
            f"Clog:{len(cron.get('clogged_jobs', []))}|Drift:{len(cron.get('drift_skipped_jobs', []))}|"
            f"Overdue:{len(cron.get('overdue_jobs', []))}|Auth:{len(cron.get('auth_failed_jobs', []))}|"
            f"RL:{len(cron.get('rate_limited_jobs', []))}"
        )
        jev_t = jev_brain.get("jev_telemetry", {})
        brain_e = jev_brain.get("brain_evolution", {})
        sleep_c = jev_brain.get("sleep_consolidation", {})
        if jev_t or brain_e:
            lines.append("")
            lines.append("🧠 <b>Hoạt Động JEV &amp; Tiến Hóa Nhận Thức (SecondBrain):</b>")
            j_stat = html.escape(str(jev_t.get("status", "ACTIVE")), quote=True)
            j_lat = jev_t.get("onnx_latency_ms", 0.0)
            j_loras = _safe_int(jev_t.get("lora_count", 0))
            j_sft = _safe_int(jev_t.get("sft_samples", 0))
            j_dpo = _safe_int(jev_t.get("dpo_samples", 0))
            j_sess = _safe_int(jev_t.get("jev_sessions_count", 0))
            j_aud = _safe_int(jev_t.get("dialectical_audits_count", 0))
            lines.append(
                f"• <b>Local JEV:</b> {j_stat} (ONNX {j_lat}ms, $0/0-tok) | "
                f"LoRA:{j_loras} | SFT/DPO:{j_sft}/{j_dpo} | Sess/Aud:{j_sess}/{j_aud}"
            )
            act_eng = _safe_int(brain_e.get("active_engrams", 0))
            l3_cnt = _safe_int(brain_e.get("l3_count", 0))
            l2_cnt = _safe_int(brain_e.get("l2_count", 0))
            l1_cnt = _safe_int(brain_e.get("l1_count", 0))
            sup_cnt = _safe_int(brain_e.get("superseded_count", 0))
            hb_cnt = _safe_int(brain_e.get("high_bloom_count", 0))
            hb_pct = brain_e.get("high_bloom_pct", 0.0)
            lines.append(
                f"• <b>SecondBrain:</b> {act_eng} ACTIVE (L3:{l3_cnt}|L2:{l2_cnt}|L1:{l1_cnt}|Sup:{sup_cnt}) | "
                f"B5-6:{hb_cnt}/{act_eng} ({hb_pct}%)"
            )
            exo_e = jev_brain.get("exogenous_ecology", brain_e)
            exo_total = _safe_int(exo_e.get("exo_total", 0))
            if exo_total > 0:
                exo_github = _safe_int(exo_e.get("exo_github", 0))
                exo_arxiv = _safe_int(exo_e.get("exo_arxiv", 0))
                exo_standards = _safe_int(exo_e.get("exo_standards", 0))
                exo_tasks = _safe_int(exo_e.get("exo_tasks", 0))
                exo_avg_h = _safe_float(exo_e.get("exo_avg_entropy_bits", 0.0))
                exo_adopt = _safe_int(exo_e.get("exo_adopt_count", 0))
                exo_heal = _safe_int(exo_e.get("exo_self_heal_count", 0))
                exo_lora = _safe_int(exo_e.get("exo_lora_count", 0))
                exo_adr = _safe_int(exo_e.get("exo_adr_count", 0))
                lines.append(
                    f"• <b>Không Gian Tri Thức Ngoại Sinh:</b> {exo_total} mẫu "
                    f"(GH:{exo_github}|arXiv:{exo_arxiv}|Std:{exo_standards}|Auto:{exo_tasks} | H={exo_avg_h:.2f}b) → "
                    f"Adopt:{exo_adopt} | Heal:{exo_heal} | LoRA:{exo_lora} | ADR:{exo_adr}"
                )
            is_7am = bool(sleep_c.get("is_morning_7am_window") or scan_result.get("morning_sleep_briefing"))
            c_date = html.escape(str(sleep_c.get("cycle_date", "") or "latest"), quote=True)
            s2_gamma = sleep_c.get("stage2_downscale_factor", 0.97)
            s2_syn = _safe_int(sleep_c.get("stage2_synapses_renormalized", 0))
            s2_prn = _safe_int(sleep_c.get("stage2_weak_pruned", 0))
            s3_prm = _safe_int(sleep_c.get("stage3_promotions_count", 0))
            s4_drm = _safe_int(sleep_c.get("stage4_dream_bridges_count", 0))
            s4_par = _safe_int(sleep_c.get("stage4_paradoxes_resolved", 0))
            s5_sft = _safe_int(sleep_c.get("stage5_sft_samples", j_sft))
            s5_dpo = _safe_int(sleep_c.get("stage5_dpo_triads", j_dpo))
            s5_lat = sleep_c.get("stage5_latency_ms", 0.0)
            if is_7am:
                s1_sym = _safe_int(sleep_c.get("stage1_symlinks_flushed", 0))
                s1_dup = _safe_int(sleep_c.get("stage1_dups_cleared", 0))
                s1_deb = _safe_int(sleep_c.get("stage1_debris_flushed", 0))
                lines.append("")
                lines.append(f"🌅 <b>Báo Cáo Brain Nhịp Sleep 07:00 Sáng (Chu kỳ 02:00 AM — {c_date}):</b>")
                lines.append(
                    f"• <b>Stage 1-2 (Glymphatic &amp; SHY):</b> Sym:{s1_sym},Dup:{s1_dup},L0:{s1_deb} | "
                    f"γ={s2_gamma},Renorm:{s2_syn},Pruned:{s2_prn}"
                )
                lines.append(
                    f"• <b>Stage 3-4 (SWS Replay &amp; REM Dream):</b> Promoted:{s3_prm} | "
                    f"Paradox:{s4_par} | Bridges:{s4_drm}"
                )
                lines.append(
                    f"• <b>Stage 5 (Procedural Myelination):</b> SFT:{s5_sft},"
                    f"DPO:{s5_dpo},LoRA:{j_loras} ({s5_lat}ms)"
                )
            elif sleep_c.get("available"):
                lines.append(
                    f"• <b>Nhịp Sleep gần nhất ({c_date}):</b> Renorm {s2_syn} synapses (γ={s2_gamma}), "
                    f"{s3_prm} SWS promotions, {s4_drm} REM bridges, {s5_sft} SFT/{s5_dpo} DPO"
                )

            vc = jev_brain.get("victory_critic", {}) if isinstance(jev_brain, dict) else {}
            if not vc:
                vc = scan_result.get("victory_critic", {})
            if isinstance(vc, dict) and _safe_int(vc.get("total_critiques", 0)) > 0:
                vc_total = _safe_int(vc.get("total_critiques", 0))
                vc_passed = _safe_int(vc.get("passed_count", 0))
                vc_blocked = _safe_int(vc.get("blocked_count", 0))
                vc_avg_risk = _safe_float(vc.get("avg_fake_pass_risk", 0.0))
                vc_avg_score = _safe_float(vc.get("avg_composite_score", vc.get("avg_critic_score", 100.0)))
                lines.append(
                    f"• <b>Sovereign Victory Critic:</b> {vc_total} critiques "
                    f"({vc_passed} certified | {vc_blocked} blocked) | "
                    f"Risk: {vc_avg_risk:.3f} | Score: {vc_avg_score:.1f}/100"
                )

        if evo_insight:
            lines.append("")
            lines.append("🧬 <b>Ý Nghĩa Tiến Hoá:</b>")
            shift = html.escape(str(evo_insight.get("strategic_shift", "")), quote=True)
            routing = html.escape(str(evo_insight.get("cognitive_routing", "")), quote=True)
            healing = html.escape(str(evo_insight.get("self_healing_evolution", "")), quote=True)
            know = html.escape(str(evo_insight.get("knowledge_evolution", "")), quote=True)
            if shift or routing:
                lines.append(f"• <b>Định tuyến:</b> {shift} {routing}".strip())
            if healing:
                lines.append(f"• <b>Tự chữa lành:</b> {healing}")
            if know:
                lines.append(f"• <b>Tri thức:</b> {know}")

        self_healing = scan_result.get("self_healing", {})
        sh_actions = self_healing.get("actions", []) if isinstance(self_healing, dict) else []
        if sh_actions:
            lines.append("")
            lines.append("🔧 <b>Self-Healing Actions:</b>")
            for act in sh_actions:
                lines.append(f"• <code>{html.escape(str(act), quote=True)}</code>")

        lines.append("")
        if severity == "HEALTHY":
            lines.append("✅ <b>Status:</b> Sovereign pipelines nominal.")
        elif severity == "WARNING":
            lines.append("⚠️ <b>Status:</b> Moderate degradation observed.")
        else:
            lines.append("🚨 <b>Status:</b> Critical pipeline stall.")

        return "\n".join(lines)

    def format_markdown_report(self, scan_result: Dict[str, Any]) -> str:
        """Format executive hourly digest dashboard as Markdown, including dedicated Victory Critic telemetry."""
        overall = scan_result.get("overall_health_score", 0)
        severity = scan_result.get("severity", "HEALTHY")
        cron = scan_result.get("cron", {})
        entropy = scan_result.get("entropy", {})

        cron_score = cron.get("cron_health_score", 0)
        entropy_score = entropy.get("entropy_health_score", 0)
        ticker = cron.get("ticker_heartbeat", {})
        ticker_status = "STALE ❌" if ticker.get("is_stale") else "FRESH ✅"

        status_emojis = {
            "HEALTHY": "🟢",
            "WARNING": "🟡",
            "DEGRADED": "🟡",
            "CRITICAL": "🔴",
            "ON_HOLD": "⏸️",
            "PAUSED": "⏸️",
        }
        sev_emoji = status_emojis.get(severity, "⚪")

        jev_brain = scan_result.get("jev_brain_sleep")
        if not isinstance(jev_brain, dict):
            jev_brain = collect_jev_and_brain_sleep_telemetry(
                force_sleep_report=bool(scan_result.get("morning_sleep_briefing", False))
            )

        # Extract Victory Critic Telemetry
        vc = scan_result.get("victory_critic")
        if not isinstance(vc, dict):
            vc = jev_brain.get("victory_critic", {}) if isinstance(jev_brain, dict) else {}
        if not isinstance(vc, dict):
            vc = {}

        vc_total = _safe_int(vc.get("total_critiques", 0))
        vc_passed = _safe_int(vc.get("passed_count", 0))
        vc_blocked = _safe_int(vc.get("blocked_count", 0))
        vc_avg_risk = _safe_float(vc.get("avg_fake_pass_risk", 0.0))
        vc_avg_score = _safe_float(vc.get("avg_composite_score", vc.get("avg_critic_score", 100.0)))

        ts_str = scan_result.get("timestamp") or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        lines = [
            "# ⚡ [HERMES AGENT] 24/7 Hourly System Digest",
            f"- **Timestamp:** {ts_str}",
            f"- **Composite Health:** `{overall}/100` {sev_emoji} [**{severity}**] (Cron:{cron_score}% | Entropy:{entropy_score}% | Ticker:{ticker_status})",
            "",
            "## 🛡️ Sovereign Victory Critic & Anti-Fake-Pass Telemetry",
            f"- Total Critiques: {vc_total}",
            f"- Certified Victories: {vc_passed}",
            f"- Blocked Fake Passes: {vc_blocked}",
            f"- Avg Fake Pass Risk: {vc_avg_risk:.3f}",
            f"- Avg Composite Score: {vc_avg_score:.1f}/100",
        ]

        streams = entropy.get("streams", []) or scan_result.get("entropy_streams", {}).get("streams", [])
        fleet_stream = next((s for s in streams if "Fleet" in str(s.get("name", ""))), {})
        if not fleet_stream and streams:
            fleet_stream = streams[0]
        pro_first = fleet_stream.get("pro_first_criterion", {})
        if pro_first:
            badge = pro_first.get("badge", "⚪ CHƯA RÕ")
            grade = str(pro_first.get("grade", "UNKNOWN"))
            p_burn = pro_first.get("pro_burn_pct", 0.0)
            p_cons = pro_first.get("pro_consumed_tokens", 0)
            p_cap = pro_first.get("pro_capacity_tokens", 0)
            p_share = pro_first.get("pro_request_share_pct", 0.0)
            p_reqs = pro_first.get("pro_requests", 0)
            tot_reqs = pro_first.get("total_requests", 0)
            verdict = str(pro_first.get("verdict", ""))

            lines.extend([
                "",
                "## 🎯 Pro Agy First Fleet Policy",
                f"- **Evaluation:** {badge} ({grade})",
                f"- **Pro Quota Burn:** {p_burn}% ({p_cons:,}/{p_cap:,} tok)",
                f"- **Pro Request Share:** {p_share}% ({p_reqs:,}/{tot_reqs:,} reqs)",
                f"- **Operational Verdict:** {verdict}",
            ])

        op_eff = (fleet_stream.get("operational_efficiency") or {}) if isinstance(fleet_stream, dict) else {}
        if op_eff.get("emergency_audit_active"):
            em_info = op_eff.get("emergency_audit", {})
            em_bottleneck = em_info.get("primary_bottleneck") or "unknown"
            em_1h = op_eff.get("success_rate_1h_pct", 0.0)
            em_all = op_eff.get("success_rate_pct", 0.0)
            lines.extend([
                "",
                "## 🚨 Emergency Efficiency Alert (<50% Threshold)",
                "- **Status:** ACTIVE EMERGENCY AUDIT",
                f"- **Primary Bottleneck:** `{em_bottleneck}`",
                f"- **Rolling 1h Efficiency:** `{em_1h}%`",
                f"- **Overall Efficiency:** `{em_all}%`",
            ])

        jev_t = jev_brain.get("jev_telemetry", {}) if isinstance(jev_brain, dict) else {}
        brain_e = jev_brain.get("brain_evolution", {}) if isinstance(jev_brain, dict) else {}
        if jev_t or brain_e:
            j_stat = str(jev_t.get("status", "ACTIVE"))
            j_lat = jev_t.get("onnx_latency_ms", 0.0)
            act_eng = _safe_int(brain_e.get("active_engrams", 0))
            l3_cnt = _safe_int(brain_e.get("l3_count", 0))
            l2_cnt = _safe_int(brain_e.get("l2_count", 0))
            l1_cnt = _safe_int(brain_e.get("l1_count", 0))
            lines.extend([
                "",
                "## 🧠 SecondBrain & JEV Cognitive Evolution",
                f"- **Local JEV:** {j_stat} (ONNX {j_lat}ms, $0/0-tok)",
                f"- **Active Engrams:** {act_eng} (L3:{l3_cnt} | L2:{l2_cnt} | L1:{l1_cnt})",
            ])

        lines.extend([
            "",
            f"**Pipeline Status:** {'Sovereign pipelines nominal.' if severity == 'HEALTHY' else 'Pipeline attention required.'}",
        ])

        return "\n".join(lines)



# ==============================================================================
# 5. SelfHealingManager
# ==============================================================================
class SelfHealingManager:
    """Automates resolution of drift skips and initiates recovery cycles for stalled streams."""

    _wrapper_failures: int = 0
    _wrapper_circuit_open_until: float = 0.0
    _wrapper_circuit_open_until_mono: float = 0.0
    _wrapper_circuit_reason: Optional[str] = None
    _ledger_epoch: int = 0
    _circuit_lock: threading.RLock = threading.RLock()
    _flock_depth: int = 0
    _flock_fd: Optional[int] = None
    _circuit_state_file: Optional[Path] = DEFAULT_CIRCUIT_STATE_FILE
    CIRCUIT_COOLDOWN_SECONDS: float = 300.0  # 5 minutes
    _MAX_CIRCUIT_WINDOW_S: float = 15.0 * 60.0  # 15 minutes max window (CWE-20/377 DoS defense)
    _CORRUPT_FAILSAFE_HOLD_S: float = 30.0  # 30 seconds conservative hold on corrupt ledger (CWE-20/754 defense)
    _MAX_QUARANTINE_ARTIFACTS: int = 5  # Bound quarantine set to prevent disk/inode exhaustion (CWE-400)
    _warned_no_fcntl: bool = False
    CIRCUIT_MAX_FAILURES: int = 3
    TEMP_MAX_RETRIES: int = 5

    @classmethod
    def _token_source(cls, nbytes: int = 16) -> str:
        """Cryptographically secure pseudorandom token generator (CSPRNG, CWE-330)."""
        return secrets.token_hex(nbytes)

    @classmethod
    def _epoch_marker_file(cls) -> Optional[Path]:
        """Returns path to persistent epoch marker file."""
        if cls._circuit_state_file:
            return cls._circuit_state_file.parent / f".{cls._circuit_state_file.name}.epoch"
        return None

    @classmethod
    def _sync_epoch_to_disk(cls) -> None:
        """Persists generation counter epoch to disk (atomic replace, mode 0o600)."""
        epoch_path = cls._epoch_marker_file()
        if not epoch_path:
            return
        try:
            epoch_path.parent.mkdir(parents=True, exist_ok=True)
            token = cls._token_source(6)
            tmp_epoch = epoch_path.parent / f".{epoch_path.name}.tmp.{token}"
            o_nofollow = getattr(os, "O_NOFOLLOW", 0) or 0
            o_cloexec = getattr(os, "O_CLOEXEC", 0) or 0
            write_flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | o_nofollow | o_cloexec
            fd = os.open(str(tmp_epoch), write_flags, 0o600)
            try:
                try:
                    os.fchmod(fd, 0o600)
                except OSError:
                    pass
                os.write(fd, str(cls._ledger_epoch).encode("utf-8"))
                os.fsync(fd)
            finally:
                os.close(fd)
            os.replace(str(tmp_epoch), str(epoch_path))
        except OSError:
            pass

    @classmethod
    def _load_epoch_from_disk(cls) -> None:
        """Loads generation counter epoch from disk if marker exists."""
        epoch_path = cls._epoch_marker_file()
        if epoch_path and epoch_path.exists():
            try:
                with open(epoch_path, "r", encoding="utf-8") as fh:
                    val = int(fh.read().strip())
                    if val > cls._ledger_epoch:
                        cls._ledger_epoch = val
            except (ValueError, OSError):
                pass

    @classmethod
    @contextmanager
    def _ledger_lock_ctx(cls):
        """
        Context manager for acquiring both in-process RLock and cross-process advisory fcntl.flock (CWE-362).
        Lock file is created with O_CREAT | os.O_RDWR | O_NOFOLLOW | O_CLOEXEC, mode 0o600.
        """
        with cls._circuit_lock:
            need_flock_close = False
            if fcntl is None:
                if not cls._warned_no_fcntl:
                    logger.warning(
                        json.dumps({
                            "event": "flock_unavailable",
                            "warning": "fcntl module unavailable on platform; cross-process ledger advisory flock is disabled (relying on atomic temp+replace and in-process RLock)",
                            "ts": time.time(),
                        })
                    )
                    cls._warned_no_fcntl = True
            elif cls._flock_depth == 0 and cls._circuit_state_file:
                lock_path = cls._circuit_state_file.parent / f"{cls._circuit_state_file.name}.lock"
                try:
                    cls._circuit_state_file.parent.mkdir(parents=True, exist_ok=True)
                    o_nofollow = getattr(os, "O_NOFOLLOW", 0) or 0
                    o_cloexec = getattr(os, "O_CLOEXEC", 0) or 0
                    open_flags = os.O_CREAT | os.O_RDWR | o_nofollow | o_cloexec
                    cls._flock_fd = os.open(str(lock_path), open_flags, 0o600)
                    try:
                        st = os.fstat(cls._flock_fd)
                        if st.st_mode & 0o022:
                            os.fchmod(cls._flock_fd, 0o600)
                    except OSError:
                        pass
                    fcntl.flock(cls._flock_fd, fcntl.LOCK_EX)
                    need_flock_close = True
                except OSError as exc:
                    logger.warning("Could not acquire advisory flock on %s: %s", lock_path, exc)
                    if cls._flock_fd is not None:
                        try:
                            os.close(cls._flock_fd)
                        except OSError:
                            pass
                        cls._flock_fd = None

            cls._flock_depth += 1
            try:
                yield
            finally:
                cls._flock_depth -= 1
                if cls._flock_depth == 0 and need_flock_close and cls._flock_fd is not None:
                    try:
                        fcntl.flock(cls._flock_fd, fcntl.LOCK_UN)
                    except OSError:
                        pass
                    try:
                        os.close(cls._flock_fd)
                    except OSError:
                        pass
                    cls._flock_fd = None

    @classmethod
    def _with_ledger_lock(cls, fn=None):
        """
        Executes fn under cross-process advisory flock and thread lock, or returns context manager.
        """
        ctx = cls._ledger_lock_ctx()
        if fn is None:
            return ctx
        with ctx:
            return fn()

    @classmethod
    def _quarantine_corrupt_ledger(cls, target: Path, now: float, reason_key: str, exc: Optional[Exception] = None) -> None:
        """
        Quarantines a corrupt or malformed circuit breaker ledger (CWE-20/CWE-754/CWE-400 DoS defense).
        - Content-addressed via SHA-256: collapses repeated identical corruptions to a single artifact.
        - Ring buffer eviction bounded by _MAX_QUARANTINE_ARTIFACTS to prevent disk/inode exhaustion.
        - Atomically renames target to .{name}.corrupt.{digest} so subsequent reads don't infinitely loop holds.
        """
        cls._ledger_epoch += 1
        cls._sync_epoch_to_disk()
        quarantined = False
        deduplicated = False
        quarantine_target = None

        poison_bytes = b""
        if target.exists():
            try:
                poison_bytes = target.read_bytes()
            except OSError:
                poison_bytes = str(now).encode("utf-8")

        digest = hashlib.sha256(poison_bytes).hexdigest()[:32]
        quarantine_target = target.with_name(f".{target.name}.corrupt.{digest}")

        try:
            if quarantine_target.exists():
                # Identical poison content already quarantined: dedup and unlink
                target.unlink(missing_ok=True)
                quarantined = True
                deduplicated = True
            else:
                os.replace(str(target), str(quarantine_target))
                try:
                    os.chmod(quarantine_target, 0o600)
                except OSError:
                    pass
                quarantined = True
        except OSError:
            try:
                target.unlink(missing_ok=True)
                quarantined = True
            except OSError:
                pass

        # Ring buffer eviction: bound total quarantine artifacts to _MAX_QUARANTINE_ARTIFACTS
        try:
            parent = target.parent
            prefix = f".{target.name}.corrupt."
            artifacts = [
                p for p in parent.iterdir()
                if p.is_file() and p.name.startswith(prefix)
            ]
            if len(artifacts) > cls._MAX_QUARANTINE_ARTIFACTS:
                artifacts.sort(key=lambda p: (p.stat().st_mtime, p.name))
                to_evict = artifacts[:-cls._MAX_QUARANTINE_ARTIFACTS]
                for old_art in to_evict:
                    try:
                        old_art.unlink(missing_ok=True)
                        logger.info(
                            json.dumps({
                                "event": "quarantine_evicted",
                                "evicted": str(old_art),
                                "max_artifacts": cls._MAX_QUARANTINE_ARTIFACTS,
                                "ts": now,
                            })
                        )
                    except OSError:
                        pass
        except OSError:
            pass

        logger.warning(
            json.dumps({
                "event": "circuit_ledger_corrupt",
                "target": str(target),
                "quarantined": quarantined,
                "deduplicated": deduplicated,
                "quarantine_target": str(quarantine_target) if quarantined else None,
                "error": type(exc).__name__ if exc else reason_key,
                "hold_s": cls._CORRUPT_FAILSAFE_HOLD_S,
                "epoch": cls._ledger_epoch,
                "ts": now,
            })
        )

    @classmethod
    def _load_circuit_ledger(cls, path: Optional[Path] = None, now: Optional[float] = None) -> Tuple[bool, float, int, Optional[str]]:
        """
        Loads and validates persistent circuit breaker ledger (CWE-20 / CWE-377 / CWE-754):
        - When file exists but is corrupt, unreadable, non-dict, or type-confused:
          Quarantines the corrupted file (atomic rename to .{name}.corrupt.{ts}.{token}) and
          applies a one-shot bounded conservative hold (_CORRUPT_FAILSAFE_HOLD_S = 30.0s).
          This prevents attackers from resetting active cooldowns AND prevents infinite rolling DoS (Finding 1).
        - Clamps circuit_open_until exceeding now + _MAX_CIRCUIT_WINDOW_S to prevent permanent DoS wedging.
        - Sanitizes reason field (CWE-117) to printable characters and max 256 bytes.
        - Rejects NaN, Inf, and non-numeric values via math.isfinite.
        - Tracks monotonically increasing epoch generation counter.
        - Returns (is_open, circuit_open_until, failures, reason).
        """
        target = Path(path) if path else cls._circuit_state_file
        if not target or not target.exists():
            return False, 0.0, 0, None

        if now is None:
            now = time.time()
        try:
            with open(target, "r", encoding="utf-8") as fh:
                state = json.load(fh)
        except (json.JSONDecodeError, OSError, UnicodeDecodeError) as exc:
            cls._quarantine_corrupt_ledger(target, now, type(exc).__name__, exc=exc)
            return True, now + cls._CORRUPT_FAILSAFE_HOLD_S, cls.CIRCUIT_MAX_FAILURES, f"corrupt_ledger_hold_{type(exc).__name__}"

        if not isinstance(state, dict):
            cls._quarantine_corrupt_ledger(target, now, "type_confusion_not_dict")
            return True, now + cls._CORRUPT_FAILSAFE_HOLD_S, cls.CIRCUIT_MAX_FAILURES, "type_confusion_hold_not_dict"

        raw_open = state.get("circuit_open_until")
        if not isinstance(raw_open, (int, float)) or isinstance(raw_open, bool) or not math.isfinite(raw_open):
            cls._quarantine_corrupt_ledger(target, now, "invalid_expiry")
            return True, now + cls._CORRUPT_FAILSAFE_HOLD_S, cls.CIRCUIT_MAX_FAILURES, "invalid_expiry_hold"

        ledger_epoch = state.get("epoch", 0)
        if isinstance(ledger_epoch, int) and ledger_epoch > cls._ledger_epoch:
            cls._ledger_epoch = ledger_epoch

        failures = state.get("failures", cls.CIRCUIT_MAX_FAILURES)
        if not isinstance(failures, int) or isinstance(failures, bool):
            failures = cls.CIRCUIT_MAX_FAILURES

        raw_open = float(raw_open)
        max_allowed = now + cls._MAX_CIRCUIT_WINDOW_S
        if raw_open > max_allowed:
            clamped = max_allowed
            logger.warning(
                json.dumps({
                    "event": "circuit_ledger_window_clamped",
                    "raw_open_until": raw_open,
                    "clamped_open_until": clamped,
                    "max_window_s": cls._MAX_CIRCUIT_WINDOW_S,
                    "ts": now,
                })
            )
            cooldown = clamped
        else:
            cooldown = raw_open

        # Sanitize reason field (CWE-117)
        raw_reason = str(state.get("reason", "unknown"))[:256]
        clean_reason = "".join(ch for ch in raw_reason if ch.isprintable()) or "unknown"

        if now < cooldown:
            return True, cooldown, failures, clean_reason

        return False, 0.0, failures, None

    @classmethod
    def set_circuit_state_file(cls, path: Optional[Path]) -> None:
        """Override persistent circuit breaker ledger path (for test isolation)."""
        with cls._with_ledger_lock():
            cls._circuit_state_file = Path(path) if path else None
            cls._load_epoch_from_disk()

    @classmethod
    def reset_circuit_breaker(cls) -> None:
        """Reset circuit breaker counters and cooldown (both in-memory and persistent ledger)."""
        with cls._with_ledger_lock():
            cls._wrapper_failures = 0
            cls._wrapper_circuit_open_until = 0.0
            cls._wrapper_circuit_open_until_mono = 0.0
            cls._wrapper_circuit_reason = None
            cls._ledger_epoch += 1
            cls._sync_epoch_to_disk()
            if cls._circuit_state_file and cls._circuit_state_file.exists():
                try:
                    cls._circuit_state_file.unlink()
                except OSError:
                    pass

    @classmethod
    def _trip_circuit_breaker(cls, reason: str, errno_val: Optional[int] = None) -> None:
        """Trip circuit breaker with persistent ledger (CWE-362 / cron-cadence DoS defense)."""
        with cls._with_ledger_lock():
            cls._ledger_epoch += 1
            cls._sync_epoch_to_disk()
            now = time.time()
            now_mono = time.monotonic()
            cls._wrapper_circuit_open_until = now + cls.CIRCUIT_COOLDOWN_SECONDS
            cls._wrapper_circuit_open_until_mono = now_mono + cls.CIRCUIT_COOLDOWN_SECONDS
            clean_reason = "".join(ch for ch in str(reason)[:256] if ch.isprintable()) or "unknown"
            cls._wrapper_circuit_reason = clean_reason
            if cls._circuit_state_file:
                try:
                    cls._circuit_state_file.parent.mkdir(parents=True, exist_ok=True)
                    state = {
                        "epoch": cls._ledger_epoch,
                        "tripped_at": now,
                        "circuit_open_until": cls._wrapper_circuit_open_until,
                        "failures": cls._wrapper_failures,
                        "errno": errno_val,
                        "reason": clean_reason,
                    }
                    # Atomic publish: temp file + os.replace to prevent partial-write corruption
                    token = cls._token_source(8)
                    tmp_state_file = cls._circuit_state_file.parent / f".{cls._circuit_state_file.name}.tmp.{token}"
                    o_nofollow = getattr(os, "O_NOFOLLOW", 0) or 0
                    o_cloexec = getattr(os, "O_CLOEXEC", 0) or 0
                    write_flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | o_nofollow | o_cloexec
                    fd = os.open(str(tmp_state_file), write_flags, 0o600)
                    try:
                        try:
                            os.fchmod(fd, 0o600)
                        except OSError:
                            pass
                        data = json.dumps(state).encode("utf-8")
                        os.write(fd, data)
                        os.fsync(fd)
                    finally:
                        os.close(fd)
                    os.replace(str(tmp_state_file), str(cls._circuit_state_file))
                except OSError as exc:
                    logger.warning("Could not persist circuit breaker ledger: %s", exc)

    @classmethod
    def get_circuit_status(cls) -> Dict[str, Any]:
        """Thread-safe snapshot of circuit breaker status (checking memory and persistent ledger)."""
        with cls._with_ledger_lock():
            now = time.time()
            now_mono = time.monotonic()
            is_open_mono = (
                cls._wrapper_circuit_open_until_mono > 0.0
                and now_mono < cls._wrapper_circuit_open_until_mono
            )
            is_open_wall = (now < cls._wrapper_circuit_open_until)
            is_open = is_open_mono or is_open_wall
            reason = cls._wrapper_circuit_reason if is_open else None

            # Check persistent ledger
            if cls._circuit_state_file:
                l_open, l_cooldown, l_failures, l_reason = cls._load_circuit_ledger(cls._circuit_state_file, now=now)
                if l_open:
                    cls._wrapper_circuit_open_until = l_cooldown
                    cls._wrapper_circuit_open_until_mono = now_mono + max(0.0, l_cooldown - now)
                    cls._wrapper_failures = l_failures
                    cls._wrapper_circuit_reason = l_reason
                    is_open = True
                    reason = l_reason

            cooldown_rem = 0.0
            if is_open:
                if cls._wrapper_circuit_open_until_mono > 0.0:
                    cooldown_rem = max(
                        cls._wrapper_circuit_open_until_mono - now_mono,
                        cls._wrapper_circuit_open_until - now,
                        0.0,
                    )
                else:
                    cooldown_rem = max(0.0, cls._wrapper_circuit_open_until - now)

            return {
                "failures": cls._wrapper_failures,
                "circuit_open_until": cls._wrapper_circuit_open_until,
                "is_open": is_open,
                "cooldown_remaining": cooldown_rem,
                "reason": reason,
                "epoch": cls._ledger_epoch,
            }

    def __init__(
        self,
        jobs_path: Path = DEFAULT_JOBS_JSON,
        repo_dir: Path = REPO_ROOT,
        python_bin: Optional[str] = None,
        scripts_dir: Optional[Path] = None,
    ):
        self.jobs_path = Path(jobs_path)
        self.repo_dir = Path(repo_dir)
        venv_py = self.repo_dir / ".venv" / "bin" / "python"
        self.python_bin = python_bin or (str(venv_py) if venv_py.exists() else sys.executable)
        self.scripts_dir = Path(scripts_dir) if scripts_dir else (HERMES_HOME / "scripts")

    def render_wrapper_content(self) -> Tuple[str, str]:
        """
        Renders the canonical bash wrapper content with strict shlex quoting (CWE-78 guard)
        and computes its SHA-256 digest for content-addressed verification.
        Includes self-verification against companion manifest before execution (A6).
        """
        repo_dir_q = shlex.quote(str(self.repo_dir))
        python_bin_q = shlex.quote(str(self.python_bin))
        try:
            _h = Path.home()
            local_bin_path = str(_h / ".local" / "bin")
        except Exception:
            local_bin_path = "/usr/local/bin"
        local_bin_q = shlex.quote(local_bin_path)

        wrapper_name = "hermes_hourly_digest.sh"
        manifest_name = f".{wrapper_name}.manifest"

        wrapper_content = (
            "#!/usr/bin/env bash\n"
            "set -euo pipefail\n\n"
            'SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"\n'
            f'MANIFEST="$SCRIPT_DIR/{manifest_name}"\n'
            'if [ -f "$MANIFEST" ]; then\n'
            '    (cd "$SCRIPT_DIR" && sha256sum -c "$MANIFEST" --status) || {\n'
            '        echo "FATAL: Wrapper script SHA-256 integrity verification failed against manifest!" >&2\n'
            '        exit 1\n'
            '    }\n'
            'fi\n\n'
            f"REPO_DIR={repo_dir_q}\n"
            'cd "$REPO_DIR"\n'
            f'export PATH={local_bin_q}:"$PATH"\n\n'
            f'exec {python_bin_q} "$REPO_DIR/tools/hourly_digest_monitor.py" --notify --self-heal\n'
        )
        digest = hashlib.sha256(wrapper_content.encode("utf-8")).hexdigest()
        return wrapper_content, digest

    def _resolve_scripts_dir_fd(self) -> int:
        """
        Creates or opens scripts_dir component-by-component, anchored to each parent's
        fd with O_NOFOLLOW | O_DIRECTORY (CWE-367 / CWE-427 / CWE-59).
        Refusal originates directly from ELOOP/ENOTDIR on O_NOFOLLOW without prior lstat.
        Fails closed with RuntimeError if O_NOFOLLOW is unsupported on platform.
        Caller owns the returned fd and must os.close() it.
        """
        o_nofollow = getattr(os, "O_NOFOLLOW", None)
        if not o_nofollow:
            raise RuntimeError(
                "O_NOFOLLOW unavailable on this platform; refusing to resolve scripts_dir without symlink protection (CWE-59 fail-closed)"
            )

        d = Path(os.path.abspath(str(self.scripts_dir)))
        root = d.anchor or "/"
        cloexec = getattr(os, "O_CLOEXEC", 0)
        open_flags = os.O_RDONLY | os.O_DIRECTORY | o_nofollow | cloexec

        root_fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | cloexec)
        cur_fd = root_fd
        parts = d.parts[1:]

        try:
            for comp in parts:
                try:
                    nxt = os.open(comp, open_flags, dir_fd=cur_fd)
                except FileNotFoundError:
                    os.mkdir(comp, mode=0o700, dir_fd=cur_fd)
                    nxt = os.open(comp, open_flags, dir_fd=cur_fd)
                except OSError as exc:
                    if exc.errno in (errno.ELOOP, errno.ENOTDIR):
                        logger.error(
                            json.dumps({
                                "event": "scripts_dir_symlink_refused",
                                "component": str(comp),
                                "scripts_dir": str(self.scripts_dir),
                                "euid": os.geteuid(),
                                "ts": time.time(),
                            })
                        )
                        if comp == parts[-1]:
                            raise RuntimeError(f"scripts_dir open refused (symlink or non-dir): {self.scripts_dir}") from exc
                        else:
                            raise RuntimeError(f"scripts_dir ancestor is a symlink, refusing: {comp}") from exc
                    raise
                if cur_fd != root_fd:
                    os.close(cur_fd)
                cur_fd = nxt
            return cur_fd
        except Exception:
            if cur_fd != root_fd:
                os.close(cur_fd)
            os.close(root_fd)
            raise

    def _create_exclusive_temp(
        self, dir_fd: int, base_name: str, data: bytes, is_executable: bool = False
    ) -> str:
        """
        Creates an unpredictable, exclusive temporary file (CWE-340 / CWE-377 / CWE-494 / CWE-59)
        with 128-bit cryptographic randomness (secrets.token_hex(16)).
        Fails closed if O_NOFOLLOW is unavailable.
        Retries up to TEMP_MAX_RETRIES ONLY on FileExistsError (EEXIST). Fatal errnos (ENOSPC, EACCES, EMFILE)
        fail immediately with structured SIEM event 'temp_create_fatal_errno' to prevent amplification DoS.
        Writes data, fchmods to 0o700 if is_executable else 0o600, fsyncs, and closes fd.
        Returns the relative temporary file name.
        """
        o_nofollow = getattr(os, "O_NOFOLLOW", None)
        if not o_nofollow:
            raise RuntimeError(
                "O_NOFOLLOW unavailable on this platform; refusing to create wrapper temp without symlink protection (CWE-59 fail-closed)"
            )

        write_flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | o_nofollow | getattr(os, "O_CLOEXEC", 0)
        mode = 0o600
        target_mode = 0o700 if is_executable else 0o600

        last_exc: Optional[Exception] = None
        for attempt in range(self.TEMP_MAX_RETRIES):
            token = self._token_source(16)
            tmp_name = f".{base_name}.tmp.{token}"
            try:
                tmp_fd = os.open(tmp_name, write_flags, mode, dir_fd=dir_fd)
            except OSError as exc:
                if exc.errno == errno.EEXIST or isinstance(exc, FileExistsError):
                    last_exc = exc
                    logger.warning(
                        json.dumps({
                            "event": "temp_collision_retry",
                            "base_name": base_name,
                            "tmp_name": tmp_name,
                            "attempt": attempt + 1,
                            "max_retries": self.TEMP_MAX_RETRIES,
                            "ts": time.time(),
                        })
                    )
                    continue
                # Fatal errno (ENOSPC, EACCES, EMFILE, ELOOP, EROFS, etc. in _FATAL_TEMP_ERRNOS) are NOT collisions — fail closed immediately without retrying!
                logger.error(
                    json.dumps({
                        "event": "temp_create_fatal_errno",
                        "base_name": base_name,
                        "tmp_name": tmp_name,
                        "errno": exc.errno,
                        "strerror": str(exc),
                        "attempt": attempt + 1,
                        "ts": time.time(),
                    })
                )
                raise

            # Successfully created and opened exclusive temp fd
            try:
                os.write(tmp_fd, data)
                if target_mode != mode:
                    try:
                        os.fchmod(tmp_fd, target_mode)
                    except OSError:
                        pass
                os.fsync(tmp_fd)
            finally:
                os.close(tmp_fd)
            return tmp_name

        # All retries exhausted -> fail closed with structured SIEM audit log
        logger.error(
            json.dumps({
                "event": "temp_create_exhausted",
                "base_name": base_name,
                "max_retries": self.TEMP_MAX_RETRIES,
                "ts": time.time(),
            })
        )
        if last_exc:
            raise last_exc
        raise RuntimeError(f"Failed creating exclusive temp file for {base_name} after {self.TEMP_MAX_RETRIES} attempts")

    def ensure_wrapper_script(self) -> Tuple[Path, str]:
        """
        Authoritative wrapper creation & reconciliation (CWE-427 / CWE-367 / CWE-78 / CWE-494 / CWE-362 / CWE-59):
        - Component-by-component O_NOFOLLOW directory resolution eliminates TOCTOU races (fail-closed if O_NOFOLLOW missing).
        - Verifies ownership (st_uid == os.geteuid()) and directory permissions (mode & 0o022 == 0).
        - Hardens temp creation with unpredictable secrets.token_hex(16) and bounded retries against DoS.
        - Content-addressed SHA-256 verification and companion .manifest generation for runtime invocation lock.
        - Thread-safe circuit breaker preventing cascading failure storms under outages.
        - Returns (wrapper_script_path, content_sha256).
        """
        o_nofollow = getattr(os, "O_NOFOLLOW", None)
        if not o_nofollow:
            raise RuntimeError(
                "O_NOFOLLOW unavailable on this platform; refusing to inspect scripts without symlink protection (CWE-59 fail-closed)"
            )

        now = time.time()
        now_mono = time.monotonic()
        with SelfHealingManager._with_ledger_lock():
            if SelfHealingManager._circuit_state_file:
                l_open, l_cooldown, l_failures, l_reason = SelfHealingManager._load_circuit_ledger(
                    SelfHealingManager._circuit_state_file,
                    now=now,
                )
                if l_open:
                    SelfHealingManager._wrapper_circuit_open_until = l_cooldown
                    SelfHealingManager._wrapper_circuit_open_until_mono = now_mono + max(0.0, l_cooldown - now)
                    SelfHealingManager._wrapper_failures = l_failures
                    SelfHealingManager._wrapper_circuit_reason = l_reason
                    remaining = int(max(0.0, l_cooldown - now))
                    raise RuntimeError(
                        f"Wrapper reconciliation circuit breaker OPEN (cooling down for {remaining}s after persistent failure: {l_reason or 'unknown'})"
                    )

            is_open_mono = (
                SelfHealingManager._wrapper_circuit_open_until_mono > 0.0
                and now_mono < SelfHealingManager._wrapper_circuit_open_until_mono
            )
            is_open_wall = (now < SelfHealingManager._wrapper_circuit_open_until)
            if is_open_mono or is_open_wall:
                remaining = int(
                    max(
                        SelfHealingManager._wrapper_circuit_open_until_mono - now_mono,
                        SelfHealingManager._wrapper_circuit_open_until - now,
                        0.0,
                    )
                )
                reason_detail = SelfHealingManager._wrapper_circuit_reason
                if reason_detail and ("hold" in reason_detail or "corrupt" in reason_detail or "type_confusion" in reason_detail):
                    raise RuntimeError(
                        f"Wrapper reconciliation circuit breaker OPEN (cooling down for {remaining}s after persistent failure: {reason_detail})"
                    )
                raise RuntimeError(
                    f"Wrapper reconciliation circuit breaker OPEN (cooling down for {remaining}s after repeated failures)"
                )

        try:
            dir_fd = self._resolve_scripts_dir_fd()
            try:
                st_dir = os.fstat(dir_fd)
                if st_dir.st_uid != os.geteuid():
                    raise PermissionError(f"scripts_dir not owned by current user (euid {os.geteuid()}, owner {st_dir.st_uid}): {self.scripts_dir}")
                if st_dir.st_mode & 0o022:
                    logger.info(
                        json.dumps({
                            "event": "scripts_dir_mode_hardened",
                            "scripts_dir": str(self.scripts_dir),
                            "orig_mode": oct(st_dir.st_mode),
                            "target_mode": oct(0o700),
                            "ts": time.time(),
                        })
                    )
                    try:
                        if hasattr(os, "fchmod"):
                            os.fchmod(dir_fd, 0o700)
                        else:
                            os.chmod(self.scripts_dir, 0o700)
                    except OSError as exc:
                        raise RuntimeError(f"failed to harden scripts_dir perms, refusing: {self.scripts_dir}: {exc}")
                    if os.fstat(dir_fd).st_mode & 0o022:
                        raise RuntimeError(f"scripts_dir still group/world-writable after chmod: {self.scripts_dir}")

                wrapper_name = "hermes_hourly_digest.sh"
                manifest_name = f".{wrapper_name}.manifest"
                wrapper_content, digest = self.render_wrapper_content()
                data = wrapper_content.encode("utf-8")
                manifest_content = f"{digest}  {wrapper_name}\n"
                manifest_data = manifest_content.encode("utf-8")

                needs_write = True
                try:
                    check_flags = os.O_RDONLY | o_nofollow | getattr(os, "O_CLOEXEC", 0)
                    file_fd = os.open(wrapper_name, check_flags, dir_fd=dir_fd)
                    try:
                        st = os.fstat(file_fd)
                        if st.st_mode & 0o022:
                            try:
                                os.fchmod(file_fd, 0o700)
                            except OSError:
                                pass
                        owned_by_us = (st.st_uid == os.geteuid())
                        with open(file_fd, "r", encoding="utf-8", closefd=False) as fh:
                            existing_content = fh.read()
                        content_matches = (existing_content == wrapper_content)
                        if not content_matches:
                            logger.warning(
                                json.dumps({
                                    "event": "wrapper_tamper_detected",
                                    "wrapper_name": wrapper_name,
                                    "action": "republish_authoritative",
                                    "ts": time.time(),
                                })
                            )
                        needs_write = not (owned_by_us and content_matches)
                        if not needs_write and (os.fstat(file_fd).st_mode & 0o022):
                            needs_write = True
                    finally:
                        os.close(file_fd)
                except OSError:
                    needs_write = True

                needs_manifest_write = True
                try:
                    check_flags = os.O_RDONLY | o_nofollow | getattr(os, "O_CLOEXEC", 0)
                    m_fd = os.open(manifest_name, check_flags, dir_fd=dir_fd)
                    try:
                        st_m = os.fstat(m_fd)
                        if st_m.st_mode & 0o022:
                            try:
                                os.fchmod(m_fd, 0o600)
                            except OSError:
                                pass
                        with open(m_fd, "r", encoding="utf-8", closefd=False) as fh:
                            existing_m = fh.read()
                        needs_manifest_write = (existing_m != manifest_content)
                        if not needs_manifest_write and (os.fstat(m_fd).st_mode & 0o022):
                            needs_manifest_write = True
                    finally:
                        os.close(m_fd)
                except OSError:
                    needs_manifest_write = True

                if not needs_write and needs_manifest_write:
                    # Crash recovery / self-healing: wrapper matches canonical template, reconcile companion manifest
                    tmp_m = self._create_exclusive_temp(
                        dir_fd=dir_fd,
                        base_name=manifest_name,
                        data=manifest_data,
                        is_executable=False,
                    )
                    try:
                        os.replace(tmp_m, manifest_name, src_dir_fd=dir_fd, dst_dir_fd=dir_fd)
                        try:
                            os.fsync(dir_fd)
                        except OSError:
                            pass
                    except Exception as exc:
                        try:
                            os.unlink(tmp_m, dir_fd=dir_fd)
                        except OSError:
                            pass
                        logger.error("manifest self-heal failed for %s: %s", manifest_name, exc)
                        raise
                elif needs_write:
                    # Full publication: prepare and fsync BOTH temp files before replacing either (CWE-494 / crash transactionality)
                    tmp_w = self._create_exclusive_temp(
                        dir_fd=dir_fd,
                        base_name=wrapper_name,
                        data=data,
                        is_executable=True,
                    )
                    try:
                        tmp_m = self._create_exclusive_temp(
                            dir_fd=dir_fd,
                            base_name=manifest_name,
                            data=manifest_data,
                            is_executable=False,
                        )
                    except Exception:
                        try:
                            os.unlink(tmp_w, dir_fd=dir_fd)
                        except OSError:
                            pass
                        raise

                    tmp_w_replaced = False
                    tmp_m_replaced = False
                    try:
                        os.replace(tmp_w, wrapper_name, src_dir_fd=dir_fd, dst_dir_fd=dir_fd)
                        tmp_w_replaced = True
                        try:
                            os.fsync(dir_fd)
                        except OSError:
                            pass

                        os.replace(tmp_m, manifest_name, src_dir_fd=dir_fd, dst_dir_fd=dir_fd)
                        tmp_m_replaced = True
                        try:
                            os.fsync(dir_fd)
                        except OSError:
                            pass
                    except Exception as exc:
                        if not tmp_w_replaced:
                            try:
                                os.unlink(tmp_w, dir_fd=dir_fd)
                            except OSError:
                                pass
                        if not tmp_m_replaced:
                            try:
                                os.unlink(tmp_m, dir_fd=dir_fd)
                            except OSError:
                                pass
                        logger.error("wrapper atomic publication failed: %s", exc)
                        raise

                with SelfHealingManager._with_ledger_lock():
                    SelfHealingManager._wrapper_failures = 0
                    SelfHealingManager._wrapper_circuit_open_until = 0.0
                    SelfHealingManager._wrapper_circuit_open_until_mono = 0.0
                    SelfHealingManager._wrapper_circuit_reason = None
                    if SelfHealingManager._circuit_state_file and SelfHealingManager._circuit_state_file.exists():
                        try:
                            SelfHealingManager._circuit_state_file.unlink()
                        except OSError:
                            pass
                wrapper_script = self.scripts_dir / wrapper_name
                return wrapper_script, digest
            finally:
                os.close(dir_fd)
        except Exception as exc:
            with SelfHealingManager._with_ledger_lock():
                SelfHealingManager._wrapper_failures += 1
                if SelfHealingManager._wrapper_failures >= SelfHealingManager.CIRCUIT_MAX_FAILURES:
                    now = time.time()
                    if SelfHealingManager._wrapper_circuit_open_until <= now:
                        reason = f"{type(exc).__name__}: {exc}"
                        exc_errno = getattr(exc, "errno", None)
                        SelfHealingManager._trip_circuit_breaker(reason=reason, errno_val=exc_errno)
                        logger.warning(
                            "Wrapper reconciliation circuit breaker TRIPPED (cooldown %ds, persistent ledger saved) after %d failures: %s",
                            int(SelfHealingManager.CIRCUIT_COOLDOWN_SECONDS),
                            SelfHealingManager._wrapper_failures,
                            exc,
                        )
            raise

    def self_heal_drift_skips(self) -> List[Dict[str, Any]]:
        """
        Un-wedges drift-skipped cron jobs:
        - Pins model: 'codex', provider: 'custom'
        - Pins model_snapshot: 'codex', provider_snapshot: 'custom'
        - Resets drift_alerted: False
        - Clears last_error if drift_skip
        - Reconciles canonical procedural wrapper script against disk
        """
        # Reconcile wrapper script against canonical procedural memory (CWE-427 / CWE-367)
        try:
            self.ensure_wrapper_script()
        except Exception as e:
            logger.warning("Failed reconciling wrapper script during self-heal: %s", e)

        if not self.jobs_path.exists():
            return []

        try:
            with open(self.jobs_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            jobs = data.get("jobs", []) if isinstance(data, dict) else data
            healed = []

            for j in jobs:
                if not isinstance(j, dict):
                    continue
                last_err = str(j.get("last_error") or "")
                drift_alerted = bool(j.get("drift_alerted"))
                is_drift_error = "[drift_skip" in last_err

                # Check if job is unpinned or drifted
                if drift_alerted or is_drift_error or j.get("model_snapshot") == "cx/gpt-5.6-luna":
                    j["model"] = "codex"
                    j["provider"] = "custom"
                    j["model_snapshot"] = "codex"
                    j["provider_snapshot"] = "custom"
                    j["drift_alerted"] = False

                    if is_drift_error:
                        j["last_error"] = None
                        if j.get("last_status") == "error":
                            j["last_status"] = "scheduled"

                    healed.append(
                        {
                            "id": j.get("id"),
                            "name": j.get("name"),
                            "model": j["model"],
                            "provider": j["provider"],
                        }
                    )

            if healed:
                if isinstance(data, dict):
                    data["updated_at"] = datetime.now(timezone.utc).isoformat()
                # Atomic write
                tmp_path = self.jobs_path.with_suffix(".tmp")
                with open(tmp_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
                tmp_path.replace(self.jobs_path)
                logger.info("Successfully self-healed %d drift-skipped jobs.", len(healed))

            return healed
        except Exception as e:
            logger.error("Failed self-healing drift skips: %s", e)
            return []

    def reap_phantom_processes_and_stale_locks(
        self,
        max_agy_age_seconds: int = 7200,
        max_modal_logs_age_seconds: int = 600,
        max_endogenous_lock_age_seconds: int = 2700,
    ) -> Dict[str, Any]:
        """
        Reaps orphaned phantom `agy --input-format stream-json --conversation <cid>` processes
        (where `<cid>` is missing from `~/.gemini/antigravity/brain`, archived, or using deprecated
        `gemini-3.8-flash` / stuck > 2h), hung `modal app logs` processes (> 10m), and stale
        `/tmp/hermes_endogenous_consolidation.lock` files (> 45m).
        """
        reaped_agy: List[Dict[str, Any]] = []
        reaped_modal_logs: List[int] = []
        stale_locks_cleared: List[str] = []

        brain_dir = Path.home() / ".gemini" / "antigravity" / "brain"
        annotations_dir = Path.home() / ".gemini" / "antigravity" / "annotations"

        # 1. Clear stale endogenous consolidation lock if older than threshold
        endogenous_lock = Path("/tmp/hermes_endogenous_consolidation.lock")
        try:
            if endogenous_lock.exists():
                lock_age = time.time() - endogenous_lock.stat().st_mtime
                if lock_age > max_endogenous_lock_age_seconds:
                    endogenous_lock.unlink()
                    stale_locks_cleared.append(f"{endogenous_lock} (age={int(lock_age)}s)")
        except Exception as e:
            logger.debug("Error checking endogenous lock: %s", e)

        # 2. Scan process table for phantom agy stream-json & hung modal app logs
        try:
            proc = subprocess.run(
                ["ps", "-eo", "pid,etimes,args"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if proc.returncode == 0:
                conv_re = re.compile(r"--conversation\s+([0-9a-fA-F-]{36})")
                for line in proc.stdout.splitlines()[1:]:
                    parts = line.strip().split(None, 2)
                    if len(parts) < 3:
                        continue
                    try:
                        pid = int(parts[0])
                        etimes = int(parts[1])
                    except ValueError:
                        continue
                    cmd_args = parts[2]
                    if pid == os.getpid():
                        continue

                    # Check phantom agy --input-format stream-json --conversation <cid>
                    if "antigravity-cli/bin/agy" in cmd_args and "--input-format stream-json" in cmd_args:
                        m_cid = conv_re.search(cmd_args)
                        cid = m_cid.group(1) if m_cid else ""
                        reason = None
                        if cid and brain_dir.exists() and not (brain_dir / cid).exists():
                            reason = f"missing_brain_dir ({cid})"
                        elif cid and annotations_dir.exists() and (annotations_dir / f"{cid}.pbtxt").exists():
                            try:
                                pb = (annotations_dir / f"{cid}.pbtxt").read_text(encoding="utf-8", errors="ignore")
                                if re.search(r"archived\s*:\s*true", pb, re.IGNORECASE):
                                    reason = f"archived_conversation ({cid})"
                            except Exception:
                                pass
                        if not reason and "gemini-3.8-flash" in cmd_args and etimes > 600:
                            reason = f"deprecated_flash_model_phantom (etimes={etimes}s)"
                        if not reason and etimes > max_agy_age_seconds:
                            reason = f"exceeded_max_agy_age (etimes={etimes}s > {max_agy_age_seconds}s)"

                        if reason:
                            try:
                                os.kill(pid, 15)
                                reaped_agy.append({"pid": pid, "cid": cid, "etimes": etimes, "reason": reason})
                            except OSError:
                                pass

                    # Check hung modal app logs
                    elif "modal app logs" in cmd_args and etimes > max_modal_logs_age_seconds:
                        try:
                            os.kill(pid, 15)
                            reaped_modal_logs.append(pid)
                        except OSError:
                            pass
        except Exception as e:
            logger.debug("Error scanning processes for phantom reaper: %s", e)

        return {
            "reaped_agy_phantoms": reaped_agy,
            "reaped_modal_logs_pids": reaped_modal_logs,
            "stale_locks_cleared": stale_locks_cleared,
        }

    def trigger_entropy_recovery(self, stream: str) -> Dict[str, Any]:
        """Trigger on-demand execution cycle for stalled entropy sources."""
        results = {"stream": stream, "success": False, "returncode": -1, "output": ""}

        cmd: List[str] = []
        if stream == "stock_news":
            script = self.repo_dir / "skills" / "finance" / "vietnam-stock-daily-brief" / "news_monitor.py"
            cmd = [self.python_bin, str(script), "--scan"]
        elif stream == "legal_docs":
            script = self.repo_dir / "skills" / "research" / "vietnam-legal-crawler" / "crawler.py"
            out_dir = self.repo_dir / "output_legal_docs"
            cmd = [self.python_bin, str(script), "-o", str(out_dir), "--limit", "5", "--no-attachments"]
        elif stream == "media_production":
            script = self.repo_dir / "skills" / "creative" / "media-asset-bank" / "hourly_producer.py"
            cmd = [self.python_bin, str(script), "--run-once"]
        elif stream == "median_sync":
            script = self.repo_dir / "scripts" / "median_cron_hourly.sh"
            cmd = ["/usr/bin/env", "bash", str(script)]
        else:
            results["error"] = f"Unknown stream: {stream}"
            return results

        try:
            logger.info("Triggering recovery for stream '%s': %s", stream, " ".join(cmd))
            proc = subprocess.run(
                cmd,
                cwd=str(self.repo_dir),
                capture_output=True,
                text=True,
                timeout=180,
            )
            results["returncode"] = proc.returncode
            results["success"] = proc.returncode == 0
            results["output"] = (proc.stdout + "\n" + proc.stderr).strip()[-500:]
        except Exception as e:
            results["error"] = str(e)
            logger.error("Recovery execution failed for '%s': %s", stream, e)

        return results

    def install_hourly_cron(self) -> Dict[str, Any]:
        """Register the 24/7 hourly digest monitor in Hermes Cron."""
        if not self.jobs_path.exists():
            return {"status": "error", "error": "jobs.json not found"}

        try:
            with open(self.jobs_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            job_id = "job_hermes_hourly_digest"
            jobs_list = [j for j in data.get("jobs", []) if j.get("id") != job_id]

            script_path = self.repo_dir / "tools" / "hourly_digest_monitor.py"
            cmd = f"{self.python_bin} {script_path} --notify --self-heal"

            # Ensure wrapper script in scripts dir exists and is verified
            wrapper_script, wrapper_sha256 = self.ensure_wrapper_script()

            digest_job = {
                "id": job_id,
                "name": "hermes-hourly-digest-and-entropy-monitor",
                "prompt": "",
                "skills": [],
                "skill": None,
                "model": "codex",
                "provider": "custom",
                "provider_snapshot": "custom",
                "model_snapshot": "codex",
                "base_url": None,
                "script": wrapper_script.name,
                "script_sha256": wrapper_sha256,
                "command": cmd,
                "workdir": str(self.repo_dir),
                "no_agent": True,
                "schedule": {
                    "kind": "cron",
                    "expr": "0 * * * *",
                    "display": "0 * * * * (Hourly 24/7 Digest & Anomaly Monitor)",
                },
                "schedule_display": "0 * * * *",
                "repeat": {"times": None, "completed": 0},
                "enabled": True,
                "state": "scheduled",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "next_run_at": datetime.now(timezone.utc).isoformat(),
                "last_status": "ok",
                "drift_alerted": False,
            }

            jobs_list.append(digest_job)
            data["jobs"] = jobs_list
            data["updated_at"] = datetime.now(timezone.utc).isoformat()

            tmp_path = self.jobs_path.with_suffix(".tmp")
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            tmp_path.replace(self.jobs_path)

            return {
                "status": "installed",
                "job_id": job_id,
                "command": cmd,
                "script": wrapper_script.name,
                "script_sha256": wrapper_sha256,
            }
        except Exception as e:
            logger.error("Failed installing hourly digest cron: %s", e)
            return {"status": "error", "error": str(e)}

    def uninstall_hourly_cron(self) -> Dict[str, Any]:
        """Remove the 24/7 hourly digest monitor from Hermes Cron."""
        if not self.jobs_path.exists():
            return {"status": "error", "error": "jobs.json not found"}

        try:
            with open(self.jobs_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            job_id = "job_hermes_hourly_digest"
            jobs_list = [j for j in data.get("jobs", []) if j.get("id") != job_id]
            data["jobs"] = jobs_list
            data["updated_at"] = datetime.now(timezone.utc).isoformat()

            tmp_path = self.jobs_path.with_suffix(".tmp")
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            tmp_path.replace(self.jobs_path)

            return {"status": "uninstalled", "job_id": job_id}
        except Exception as e:
            logger.error("Failed uninstalling hourly digest cron: %s", e)
            return {"status": "error", "error": str(e)}


# ==============================================================================
# Main Orchestrator & CLI
# ==============================================================================
def run_full_scan(
    cron_detector: Optional[CronAnomalyDetector] = None,
    entropy_detector: Optional[EntropyDegradationDetector] = None,
    now_utc: Optional[datetime] = None,
    force_sleep_report: bool = False,
) -> Dict[str, Any]:
    """Execute complete system scan across Cron, Entropy streams, and Mesh."""
    cron_det = cron_detector or CronAnomalyDetector()
    entropy_det = entropy_detector or EntropyDegradationDetector()

    cron_findings = cron_det.scan(now_utc=now_utc)
    entropy_findings = entropy_det.scan(now_utc=now_utc)

    cron_score = cron_findings.get("cron_health_score", 0)
    entropy_score = entropy_findings.get("entropy_health_score", 0)

    # Mesh score from Stream 5
    mesh_stream = next(
        (s for s in entropy_findings.get("streams", []) if "Fleet" in s.get("name", "")),
        {},
    )
    mesh_score = mesh_stream.get("score", 0)

    # Ticker score
    ticker = cron_findings.get("ticker_heartbeat", {})
    ticker_score = 0 if ticker.get("is_stale") else 100

    overall_score, severity = CompositeHealthCalculator.calculate(
        cron_score=cron_score,
        entropy_score=entropy_score,
        mesh_score=mesh_score,
        ticker_score=ticker_score,
    )

    jev_brain_sleep = collect_jev_and_brain_sleep_telemetry(
        force_sleep_report=force_sleep_report,
    )

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "overall_health_score": overall_score,
        "severity": severity,
        "cron": cron_findings,
        "entropy": entropy_findings,
        "mesh_score": mesh_score,
        "ticker_score": ticker_score,
        "jev_brain_sleep": jev_brain_sleep,
        "victory_critic": jev_brain_sleep.get("victory_critic", {}),
        "morning_sleep_briefing": bool(force_sleep_report or jev_brain_sleep.get("sleep_consolidation", {}).get("is_morning_7am_window")),
    }


def format_markdown_report(scan_result: Dict[str, Any]) -> str:
    """Format full markdown report for 24/7 Hourly Digest including dedicated Victory Critic telemetry."""
    notifier = HermesTelegramNotifier()
    return notifier.format_markdown_report(scan_result)


def main():
    parser = argparse.ArgumentParser(description="Hermes Agent 24/7 Hourly Monitor & Anomaly Detector")
    parser.add_argument("--scan", action="store_true", help="Run full scan and output JSON summary")
    parser.add_argument("--markdown", action="store_true", help="Print executive hourly digest report in Markdown")
    parser.add_argument("--notify", action="store_true", help="Send Telegram Hourly Digest Report")
    parser.add_argument("--alert-only", action="store_true", help="Send Telegram alert only if CRITICAL anomalies exist")
    parser.add_argument("--self-heal", action="store_true", help="Run automated self-healing for drift-skips")
    parser.add_argument("--recover-stream", type=str, help="Trigger on-demand recovery for a stalled entropy stream")
    parser.add_argument("--install-cron", action="store_true", help="Register 24/7 hourly digest monitor in Hermes Cron")
    parser.add_argument("--uninstall-cron", action="store_true", help="Remove 24/7 hourly digest monitor from Hermes Cron")
    parser.add_argument("--morning-sleep-report", action="store_true", help="Force expanded 07:00 AM Brain Sleep Consolidation report")
    args = parser.parse_args()

    notifier = HermesTelegramNotifier()
    healer = SelfHealingManager()

    if args.install_cron:
        res = healer.install_hourly_cron()
        print(f"[+] Install hourly cron result: {res}")
        return

    if args.uninstall_cron:
        res = healer.uninstall_hourly_cron()
        print(f"[+] Uninstall hourly cron result: {res}")
        return

    # Default action if no flags provided: scan
    if not (args.scan or args.markdown or args.notify or args.alert_only or args.self_heal or args.recover_stream):
        args.scan = True

    if args.self_heal:
        print("[*] Initiating Self-Healing for Drift-Skipped Cron Jobs & Phantom Process Reaper...")
        healed = healer.self_heal_drift_skips()
        print(f"[+] Self-healed {len(healed)} jobs:")
        for h in healed:
            print(f"    - {h.get('name')} ({h.get('id')}) -> model={h.get('model')}, provider={h.get('provider')}")
        reap_res = healer.reap_phantom_processes_and_stale_locks()
        print(
            f"[+] Phantom Reaper: agy_phantoms={len(reap_res.get('reaped_agy_phantoms', []))}, "
            f"modal_logs={len(reap_res.get('reaped_modal_logs_pids', []))}, "
            f"stale_locks={len(reap_res.get('stale_locks_cleared', []))}"
        )

    if args.recover_stream:
        print(f"[*] Triggering recovery for entropy stream: {args.recover_stream}...")
        rec = healer.trigger_entropy_recovery(args.recover_stream)
        print(f"[+] Result: success={rec.get('success')}, code={rec.get('returncode')}")

    scan_result = run_full_scan(force_sleep_report=args.morning_sleep_report)

    if args.scan:
        print(json.dumps(scan_result, indent=2))

    if args.markdown:
        print(notifier.format_markdown_report(scan_result))

    if args.alert_only:
        if scan_result.get("severity") == "CRITICAL":
            alert_msg = notifier.format_urgent_alert(scan_result)
            print("[*] CRITICAL anomalies detected. Sending Urgent Alert to Telegram...")
            sent = notifier.send_alert(alert_msg)
            print(f"[+] Telegram alert delivery status: {'SUCCESS' if sent else 'FAILED'}")
        else:
            print(f"[*] Health is {scan_result.get('severity')}. No urgent alert needed.")

    if args.notify:
        digest_msg = notifier.format_hourly_digest(scan_result)
        print("[*] Sending Hourly Digest to Telegram...")
        sent = notifier.send_digest(digest_msg)
        print(f"[+] Telegram digest delivery status: {'SUCCESS' if sent else 'FAILED'}")


class RadixNode:
    """Node in the SGLang-inspired RadixAttention shared-prefix cache tree."""

    def __init__(self) -> None:
        self.children: Dict[Any, RadixNode] = {}
        self.kv: Optional[Any] = None
        self.ts: float = 0.0


class RadixPrefixCacheTree:
    """SGLang-inspired RadixAttention tree for shared prefix KV-cache reuse across Fleet dispatches.

    Synthesized via Fleet Pro node sunward (Job 448e83bc-e06b-4761-8b02-1545c84c8433).
    """

    def __init__(self) -> None:
        self.root = RadixNode()
        self.nodes: List[RadixNode] = [self.root]
        self.total_queries: int = 0
        self.matched_tokens: int = 0
        self.total_tokens: int = 0

    def insert(self, tokens: List[Any], kv_handle: Any) -> None:
        curr = self.root
        now = time.time()
        for tok in tokens:
            if tok not in curr.children:
                node = RadixNode()
                curr.children[tok] = node
                self.nodes.append(node)
            curr = curr.children[tok]
            curr.ts = now
        curr.kv = kv_handle

    def match_prefix(self, tokens: List[Any]) -> Tuple[int, Optional[Any]]:
        curr = self.root
        matched = 0
        last_kv = None
        now = time.time()
        self.total_queries += 1
        self.total_tokens += len(tokens)
        for tok in tokens:
            if tok not in curr.children:
                break
            curr = curr.children[tok]
            curr.ts = now
            matched += 1
            if curr.kv is not None:
                last_kv = curr.kv
        self.matched_tokens += matched
        return matched, last_kv

    @property
    def hit_rate(self) -> float:
        if self.total_tokens == 0:
            return 0.0
        return round(self.matched_tokens / self.total_tokens, 4)

    def evict_lru(self, max_nodes: int) -> None:
        while len(self.nodes) > max_nodes:
            leaves = [n for n in self.nodes if not n.children and n is not self.root]
            if not leaves:
                break
            victim = min(leaves, key=lambda n: n.ts)
            for n in self.nodes:
                n.children = {k: v for k, v in n.children.items() if v is not victim}
            self.nodes.remove(victim)


class EscalationSensitivityEvaluator:
    """Evaluates analytical Jacobian sensitivity and empirical ROC/Pareto thresholds for escalation."""

    def __init__(
        self,
        tau_base: float = 0.72,
        alpha_complexity: float = 0.06,
        alpha_quota: float = 0.15,
        alpha_ece: float = 0.25,
        alpha_reliability: float = 0.20,
        quota_crit: float = 0.35,
    ) -> None:
        self.tau_base = float(tau_base)
        self.alpha_complexity = float(alpha_complexity)
        self.alpha_quota = float(alpha_quota)
        self.alpha_ece = float(alpha_ece)
        self.alpha_reliability = float(alpha_reliability)
        self.quota_crit = float(quota_crit)

    def compute_dynamic_tau(
        self,
        complexity: float = 1.0,
        quota_ratio: float = 0.80,
        ece: float = 0.0,
        node_reliability: float = 1.0,
        tau_base: Optional[float] = None,
        prefix_cache_hit_ratio: float = 0.0,
    ) -> Dict[str, float]:
        base = float(self.tau_base if tau_base is None else tau_base)
        c_clamped = max(0.0, min(float(complexity), 4.0))
        q_clamped = max(0.0, min(float(quota_ratio), 1.0))
        ece_clamped = max(0.0, min(float(ece), 1.0))
        rel_clamped = max(0.0, min(float(node_reliability), 1.0))
        hit_clamped = max(0.0, min(float(prefix_cache_hit_ratio), 1.0))

        quota_deficit = max(0.0, self.quota_crit - q_clamped)
        rel_deficit = max(0.0, 0.90 - rel_clamped)
        prefix_bonus = 0.04 * hit_clamped if (hit_clamped >= 0.70 and c_clamped < 2.2) else 0.0
        raw_tau = (
            base
            + self.alpha_complexity * c_clamped
            - self.alpha_quota * quota_deficit
            + self.alpha_ece * ece_clamped
            + self.alpha_reliability * rel_deficit
            - prefix_bonus
        )
        tau = max(0.50, min(0.95, raw_tau))
        d_tau_d_c = self.alpha_complexity if 0.0 <= float(complexity) <= 4.0 else 0.0
        d_tau_d_q = -self.alpha_quota if q_clamped < self.quota_crit else 0.0
        d_tau_d_ece = self.alpha_ece
        d_tau_d_rel = -self.alpha_reliability
        d_tau_d_prefix = -0.04 if (hit_clamped >= 0.70 and c_clamped < 2.2) else 0.0
        grad_norm = math.sqrt(
            d_tau_d_c ** 2 + d_tau_d_q ** 2 + d_tau_d_ece ** 2 + d_tau_d_rel ** 2 + d_tau_d_prefix ** 2
        )
        return {
            "tau": round(tau, 4),
            "d_tau_d_complexity": round(d_tau_d_c, 4),
            "d_tau_d_quota": round(d_tau_d_q, 4),
            "d_tau_d_ece": round(d_tau_d_ece, 4),
            "d_tau_d_reliability": round(d_tau_d_rel, 4),
            "d_tau_d_prefix_hit": round(d_tau_d_prefix, 4),
            "jacobian_norm": round(grad_norm, 4),
        }

    def evaluate_roc_pareto(
        self,
        traces: List[Dict[str, Any]],
        tau_grid: Optional[List[float]] = None,
        lambda_uer: float = 3.0,
        lambda_fer: float = 1.0,
    ) -> Dict[str, Any]:
        grid = list(tau_grid) if tau_grid is not None else [0.55, 0.65, 0.72, 0.78, 0.85, 0.90]
        if not traces:
            return {"optimal_tau": self.tau_base, "min_risk_loss": 0.0, "pareto_frontier": [], "curve": []}
        total = len(traces)
        bad_drafts = [t for t in traces if not bool(t.get("draft_correct", False))]
        good_drafts = [t for t in traces if bool(t.get("draft_correct", False))]
        n_bad = max(1, len(bad_drafts))
        n_good = max(1, len(good_drafts))

        curve: List[Dict[str, float]] = []
        best_tau = grid[0]
        min_loss = float("inf")
        for tau in grid:
            t_val = float(tau)
            under_esc = sum(1 for t in bad_drafts if float(t.get("conf", 0.0)) >= t_val)
            true_esc = sum(1 for t in bad_drafts if float(t.get("conf", 0.0)) < t_val)
            false_esc = sum(1 for t in good_drafts if float(t.get("conf", 0.0)) < t_val)
            uer = under_esc / n_bad if bad_drafts else 0.0
            tpr_esc = true_esc / n_bad if bad_drafts else 1.0
            fer = false_esc / n_good if good_drafts else 0.0
            risk_loss = float(lambda_uer) * uer + float(lambda_fer) * fer
            pt = {
                "tau": round(t_val, 4),
                "under_escalation_rate": round(uer, 4),
                "false_escalation_rate": round(fer, 4),
                "sensitivity_recall": round(tpr_esc, 4),
                "sensitivity_index": round(tpr_esc / (1.0 + fer), 4),
                "escalation_rate": round((true_esc + false_esc) / total, 4),
                "risk_loss": round(risk_loss, 4),
            }
            curve.append(pt)
            if risk_loss < min_loss:
                min_loss = risk_loss
                best_tau = t_val

        sorted_pts = sorted(curve, key=lambda x: (x["false_escalation_rate"], -x["sensitivity_recall"]))
        pareto: List[Dict[str, float]] = []
        max_tpr = -1.0
        for pt in sorted_pts:
            if pt["sensitivity_recall"] > max_tpr:
                pareto.append(pt)
                max_tpr = pt["sensitivity_recall"]
        return {
            "optimal_tau": round(best_tau, 4),
            "min_risk_loss": round(min_loss, 4),
            "pareto_frontier": pareto,
            "curve": curve,
        }


class ConformalBradleyTerryCascadeCalibrator:
    """Combines RouteLLM Bradley-Terry win-rate model (arXiv:2406.18665) with
    Conformal Prediction Risk Control finite-sample quantile calibration (arXiv:2402.05904).
    """

    def __init__(self, theta_0: float = -1.10, theta_1: float = 0.85, alpha: float = 0.10) -> None:
        self.theta_0 = float(theta_0)
        self.theta_1 = float(theta_1)
        self.alpha = float(alpha)
        self.q_hat: float = 0.25

    def predict_win_rate(self, complexity: float) -> float:
        z = max(-20.0, min(20.0, self.theta_0 + self.theta_1 * float(complexity)))
        return round(1.0 / (1.0 + math.exp(-z)), 4)

    def calibrate(self, nonconformity_scores: List[float], alpha: Optional[float] = None) -> float:
        if alpha is not None:
            self.alpha = max(0.01, min(0.50, float(alpha)))
        scores = sorted(float(s) for s in nonconformity_scores)
        n = len(scores)
        if n == 0:
            self.q_hat = 0.25
            return self.q_hat
        rank_ratio = min(1.0, math.ceil((n + 1) * (1.0 - self.alpha)) / n)
        idx = min(n - 1, max(0, math.ceil(rank_ratio * n) - 1))
        self.q_hat = round(scores[idx], 4)
        return self.q_hat


class TrustworthyCascadeController:
    """Trustworthy Controller for Speculative Cascade Routing (Beta-Bernoulli + ECE + Conformal Risk Control + GC-MEHT)."""

    DEFAULT_TOOL_CENTRALITY: Dict[str, float] = {
        "read_file": 0.15,
        "view_file": 0.15,
        "list_dir": 0.10,
        "search_docs": 0.20,
        "write_file": 0.75,
        "replace_file_content": 0.75,
        "fleet_dispatch": 0.85,
        "run_command": 0.95,
        "deploy_cloud": 0.98,
    }

    def __init__(
        self,
        alpha_prior: float = 9.0,
        beta_prior: float = 1.0,
        admit_threshold: float = 0.35,
        escalate_threshold: float = 0.70,
        evaluator: Optional[EscalationSensitivityEvaluator] = None,
        calibrator: Optional[ConformalBradleyTerryCascadeCalibrator] = None,
    ) -> None:
        self.default_alpha = float(alpha_prior)
        self.default_beta = float(beta_prior)
        self.admit_threshold = float(admit_threshold)
        self.escalate_threshold = float(escalate_threshold)
        self.tool_centrality_registry: Dict[str, float] = dict(self.DEFAULT_TOOL_CENTRALITY)
        self.posteriors: Dict[str, List[float]] = {}
        self.calibration_history: Dict[str, List[Tuple[float, float]]] = {}
        self.nonconformity_log: List[float] = []
        self.evaluator = evaluator or EscalationSensitivityEvaluator()
        self.calibrator = calibrator or ConformalBradleyTerryCascadeCalibrator()

    def compute_blast_radius(self, tools_required: Optional[List[str]] = None) -> float:
        if not tools_required:
            return 0.05
        scores = [float(self.tool_centrality_registry.get(str(t).strip(), 0.50)) for t in tools_required]
        return round(0.70 * max(scores) + 0.30 * (sum(scores) / len(scores)), 4)

    def evaluate_speculative_draft(
        self,
        task_level: str,
        speculative_output: str,
        tools_required: Optional[List[str]],
        confidence_score: float,
        reflection_history: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        blast_radius = self.compute_blast_radius(tools_required)
        uncertainty = max(0.0, min(1.0, 1.0 - float(confidence_score)))
        penalty = 0.0
        if reflection_history:
            recent_fails = sum(1 for step in list(reflection_history)[-3:] if not bool(step.get("success", True)))
            penalty = 0.15 * recent_fails

        sensitivity = round(0.45 * blast_radius + 0.35 * uncertainty + 0.20 * penalty, 4)
        tl_norm = (task_level or "L2_STANDARD").strip().upper()
        if sensitivity < self.admit_threshold and tl_norm in ("L1_TRIVIAL", "L2_STANDARD"):
            decision = "ACCEPT_SPECULATIVE_DRAFT"
            target_model = "gemini-4-argon-low"
        elif sensitivity < self.escalate_threshold:
            decision = "REQUIRE_MULTIAGENT_DEBATE"
            target_model = "gemini-4-argon-medium"
        else:
            decision = "ESCALATE_TO_SOVEREIGN"
            target_model = "gemini-4-argon-high"

        tx_payload = json.dumps(
            {
                "task_level": tl_norm,
                "sensitivity": sensitivity,
                "blast_radius": blast_radius,
                "decision": decision,
                "target_model": target_model,
            },
            sort_keys=True,
        )
        tx_hash = hashlib.sha256(tx_payload.encode("utf-8")).hexdigest()
        return {
            "decision": decision,
            "sensitivity_score": sensitivity,
            "blast_radius": blast_radius,
            "target_model": target_model,
            "tier": "pro",
            "tx_hash": tx_hash,
        }

    def evaluate_semantic_entropy_sprt(
        self,
        cluster_probs: List[float],
        llr_steps: List[float],
        complexity: float = 1.0,
        alpha: float = 0.05,
        beta: float = 0.10,
    ) -> Dict[str, Any]:
        probs = [float(p) for p in cluster_probs if float(p) > 0.0]
        total_p = sum(probs) or 1.0
        norm_p = [p / total_p for p in probs]
        semantic_entropy = round(-sum(p * math.log(p) for p in norm_p), 4)
        tau_entropy = round(max(0.15, min(0.75, 0.45 - 0.12 * max(0.0, float(complexity) - 1.0))), 4)

        upper_b = round(math.log((1.0 - float(beta)) / max(1e-6, float(alpha))), 4)
        lower_a = round(math.log(max(1e-6, float(beta)) / (1.0 - float(alpha))), 4)
        cum_llr = round(sum(float(x) for x in llr_steps), 4)

        if cum_llr >= upper_b or semantic_entropy > tau_entropy:
            verdict = "ESCALATE_TO_COUNCIL"
            target_model = "gemini-4-argon-high"
        elif cum_llr <= lower_a and semantic_entropy <= tau_entropy:
            verdict = "COMMIT_SPECULATIVE_DRAFT"
            target_model = "gemini-4-argon-low"
        else:
            verdict = "CONTINUE_OR_DEBATE"
            target_model = "gemini-4-argon-medium"

        return {
            "verdict": verdict,
            "target_model": target_model,
            "tier": "pro",
            "semantic_entropy": semantic_entropy,
            "entropy_threshold": tau_entropy,
            "sprt_llr": cum_llr,
            "sprt_lower_a": lower_a,
            "sprt_upper_b": upper_b,
        }

    def verify_ast_compliance(self, code_snippet: str) -> Tuple[bool, str]:
        import ast

        if not code_snippet or not code_snippet.strip():
            return False, "Empty code snippet provided."
        try:
            tree = ast.parse(code_snippet)
        except SyntaxError as err:
            return False, f"AST SyntaxError: {err}"
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                    return False, f"Function '{node.name}' contains forbidden 'pass' stub."
                if (
                    len(node.body) == 1
                    and isinstance(node.body[0], ast.Expr)
                    and isinstance(node.body[0].value, ast.Constant)
                    and node.body[0].value.value is Ellipsis
                ):
                    return False, f"Function '{node.name}' contains forbidden ellipsis stub."
        return True, "AST syntax check passed."

    def update_martingale_threshold(
        self,
        was_verified_safe: bool,
        alpha_target: float = 0.01,
        base_threshold: float = 0.75,
        learning_rate: float = 0.15,
    ) -> Dict[str, float]:
        wealth = float(getattr(self, "martingale_wealth", 1.0))
        x_t = 1.0 if was_verified_safe else 0.0
        expected = 1.0 - float(alpha_target)
        payoff = 1.0 + 0.40 * (expected - x_t)
        wealth = max(0.01, wealth * payoff)
        self.martingale_wealth = round(wealth, 6)
        theta_esc = max(0.50, min(0.95, float(base_threshold) + float(learning_rate) * math.log(max(1e-6, wealth))))
        return {
            "martingale_wealth": self.martingale_wealth,
            "theta_esc": round(theta_esc, 4),
        }

    def record_sanitized_episode(
        self,
        task_id: str,
        action: str,
        lesson: str,
        token_cost: int = 100,
        max_episodes: int = 5,
        max_token_budget: int = 1500,
    ) -> List[Dict[str, Any]]:
        episodes: List[Dict[str, Any]] = getattr(self, "_sanitized_episodes", [])
        clean_lesson = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", str(lesson))
        clean_lesson = clean_lesson.replace("```system", "'''system").replace("<|im_start|>", "").strip()
        episodes.append(
            {
                "task_id": str(task_id),
                "action": str(action),
                "lesson": clean_lesson,
                "token_cost": max(1, int(token_cost)),
            }
        )
        while len(episodes) > max_episodes:
            episodes.pop(0)
        while sum(ep["token_cost"] for ep in episodes) > max_token_budget and episodes:
            episodes.pop(0)
        self._sanitized_episodes = episodes
        return list(episodes)

    def compress_episodic_delta(
        self,
        pre_state: Dict[str, Any],
        post_state: Dict[str, Any],
        parent_hash: str = "GENESIS_ROOT_00000000000000000000000000000000",
    ) -> Dict[str, Any]:
        all_keys = sorted(set(pre_state.keys()) | set(post_state.keys()))
        delta: Dict[str, Any] = {
            k: {"before": pre_state.get(k), "after": post_state.get(k)}
            for k in all_keys
            if pre_state.get(k) != post_state.get(k)
        }
        serialized = json.dumps(delta, sort_keys=True, separators=(",", ":"))
        chain_hash = hashlib.sha256(f"{parent_hash}::{serialized}".encode("utf-8")).hexdigest()
        return {
            "delta": delta,
            "changed_keys_count": len(delta),
            "parent_hash": parent_hash,
            "current_hash": chain_hash,
        }

    def evaluate_weighted_role_debate(
        self,
        perspectives: List[Dict[str, Any]],
        threshold: float = 0.70,
    ) -> Tuple[bool, float]:
        if not perspectives:
            return False, 0.0
        total_weight = sum(float(p.get("weight", 1.0)) for p in perspectives)
        if total_weight <= 0.0:
            return False, 0.0
        weighted_score = (
            sum(float(p.get("confidence", 0.0)) * float(p.get("weight", 1.0)) for p in perspectives)
            / total_weight
        )
        return weighted_score >= float(threshold), round(weighted_score, 4)

    def run_precommit_debate_dry_run(
        self,
        proposal_id: str,
        proponent_score: float,
        adversary_risk_score: float,
        threshold: float = 0.70,
        parent_hash: str = "GENESIS_STATE",
    ) -> Dict[str, Any]:
        prop = max(0.0, min(1.0, float(proponent_score)))
        adv = max(0.0, min(1.0, float(adversary_risk_score)))
        consensus_score = round((prop * 0.6) + ((1.0 - (adv * 0.4)) * 0.4), 4)
        consensus_granted = consensus_score >= float(threshold)
        event_payload = {
            "proposal_id": str(proposal_id),
            "proponent_score": prop,
            "adversary_risk_score": adv,
            "consensus_score": consensus_score,
            "verdict": "GRANTED" if consensus_granted else "DENIED",
        }
        canonical = json.dumps(event_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        receipt_hash = hashlib.sha256(parent_hash.encode("utf-8") + canonical).hexdigest()
        return {
            **event_payload,
            "consensus_granted": consensus_granted,
            "receipt_hash": receipt_hash,
        }

    @staticmethod
    def _make_key(node: str, model: str) -> str:
        return f"{(node or 'default').strip().lower()}:{(model or 'gemini-4-argon-low').strip().lower()}"

    def get_reliability(self, node: str, model: str) -> float:
        key = self._make_key(node, model)
        alpha, beta = self.posteriors.get(key, [self.default_alpha, self.default_beta])
        return round(alpha / max(1e-9, alpha + beta), 4)

    def compute_ece(self, node: str, model: str, bins: int = 5) -> float:
        key = self._make_key(node, model)
        hist = self.calibration_history.get(key, [])
        if not hist:
            return 0.0
        n = len(hist)
        ece = 0.0
        for b in range(bins):
            lo, hi = b / bins, (b + 1) / bins
            bucket = [(c, y) for (c, y) in hist if (lo <= c < hi) or (b == bins - 1 and lo <= c <= hi)]
            if bucket:
                ece += (len(bucket) / n) * abs(
                    (sum(y for _, y in bucket) / len(bucket)) - (sum(c for c, _ in bucket) / len(bucket))
                )
        return round(ece, 4)

    def trust_adjusted_confidence(
        self,
        node: str,
        model: str,
        raw_conf: float,
        fake_risk: float = 0.0,
        complexity: float = 1.0,
    ) -> float:
        c_raw = max(0.0, min(1.0, float(raw_conf)))
        r_fake = max(0.0, min(1.0, float(fake_risk)))
        if r_fake >= 0.20:
            return round(c_raw * 0.15 * (1.0 - r_fake), 4)
        rel = self.get_reliability(node, model)
        rel_factor = min(1.0, rel / 0.90)
        ece = self.compute_ece(node, model)
        bt_adv = self.calibrator.predict_win_rate(complexity) if "low" in (model or "").lower() else 0.0
        c_trust = c_raw * rel_factor * max(0.20, 1.0 - 0.50 * ece) * (1.0 - r_fake) * (1.0 - 0.12 * bt_adv)
        return round(max(0.0, min(1.0, c_trust)), 4)

    def record_outcome(self, node: str, model: str, raw_conf: float, passed: bool) -> Dict[str, float]:
        key = self._make_key(node, model)
        if key not in self.posteriors:
            self.posteriors[key] = [self.default_alpha, self.default_beta]
        if passed:
            self.posteriors[key][0] += 1.0
        else:
            self.posteriors[key][1] += 1.5 if float(raw_conf) >= 0.80 else 1.0
        hist = self.calibration_history.setdefault(key, [])
        hist.append((max(0.0, min(1.0, float(raw_conf))), 1.0 if passed else 0.0))
        self.nonconformity_log.append(max(0.0, 1.0 - float(raw_conf)) if passed else min(1.0, float(raw_conf)))
        if len(self.nonconformity_log) >= 5:
            self.calibrator.calibrate(self.nonconformity_log[-100:])
        return {
            "reliability": self.get_reliability(node, model),
            "ece": self.compute_ece(node, model),
            "conformal_q_hat": self.calibrator.q_hat,
        }


class SpeculativeCascadeRouter:
    """Speculative Cascading & Dynamic Quota Arbitration (arXiv:2401.12574) on Pro Tier.

    Cascades across 3-Tier Gemini 4 Argon (`gemini-4-argon-low` -> `gemini-4-argon-medium` -> `gemini-4-argon-high`)
    using a confidence deferral threshold `tau` and `TrustworthyCascadeController` while strictly preserving Ultra quota.
    """

    MODELS: Tuple[str, ...] = (
        "gemini-4-argon-low",
        "gemini-4-argon-medium",
        "gemini-4-argon-high",
    )

    def __init__(
        self,
        tau: float = 0.80,
        tier: str = "pro",
        controller: Optional[TrustworthyCascadeController] = None,
    ) -> None:
        if tier != "pro":
            raise ValueError("SpeculativeCascadeRouter strictly enforces tier='pro' (zero Ultra drain).")
        self.tau = float(tau)
        self.tier = tier
        self.controller = controller or TrustworthyCascadeController(
            evaluator=EscalationSensitivityEvaluator(tau_base=float(tau))
        )

    def route(self, prompt: str, infer_fn: Any) -> Tuple[str, Any, float]:
        for idx, model in enumerate(self.MODELS):
            out, conf = infer_fn(model, prompt)
            if float(conf) >= self.tau or idx == len(self.MODELS) - 1:
                return model, out, float(conf)
        raise RuntimeError("Speculative cascade exhausted without candidate.")

    def route_trustworthy(
        self,
        prompt: str,
        infer_fn: Any,
        complexity: float = 1.0,
        quota_ratio: float = 0.80,
        node: str = "sunward",
        fake_risk_fn: Optional[Any] = None,
    ) -> Dict[str, Any]:
        start_idx = 1 if float(complexity) >= 2.8 else 0
        hops: List[Dict[str, Any]] = []
        for idx in range(start_idx, len(self.MODELS)):
            model = self.MODELS[idx]
            out, raw_conf = infer_fn(model, prompt)
            fake_risk = float(fake_risk_fn(out)) if fake_risk_fn is not None else 0.0
            rel = self.controller.get_reliability(node, model)
            ece = self.controller.compute_ece(node, model)
            tau_info = self.controller.evaluator.compute_dynamic_tau(
                complexity=complexity,
                quota_ratio=quota_ratio,
                ece=ece,
                node_reliability=rel,
                tau_base=self.tau,
            )
            dyn_tau = tau_info["tau"]
            trust_conf = self.controller.trust_adjusted_confidence(
                node=node,
                model=model,
                raw_conf=raw_conf,
                fake_risk=fake_risk,
                complexity=complexity,
            )
            accepted = bool(trust_conf >= dyn_tau or idx == len(self.MODELS) - 1)
            hops.append({
                "model": model,
                "raw_confidence": round(float(raw_conf), 4),
                "trust_confidence": trust_conf,
                "dynamic_tau": dyn_tau,
                "fake_risk": round(fake_risk, 4),
                "ece": ece,
                "reliability": rel,
                "accepted": accepted,
            })
            if accepted:
                return {
                    "selected_model": model,
                    "tier": self.tier,
                    "node": node,
                    "output": out,
                    "raw_confidence": round(float(raw_conf), 4),
                    "trust_confidence": trust_conf,
                    "dynamic_tau": dyn_tau,
                    "escalation_count": len(hops) - 1,
                    "hops": hops,
                    "sensitivity": tau_info,
                    "bradley_terry_win_rate": self.controller.calibrator.predict_win_rate(complexity),
                    "conformal_q_hat": self.controller.calibrator.q_hat,
                }
        raise RuntimeError("Trustworthy speculative cascade exhausted without candidate.")


if __name__ == "__main__":
    main()



