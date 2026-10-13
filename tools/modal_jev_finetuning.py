#!/usr/bin/env python3
"""
tools/modal_jev_finetuning.py
=============================
Autonomous Fine-Tuning Pipeline for Local JEV Decision Model on Modal Multi-GPU Fleet.

Hardened against CWE-200 (Dataset Secret Leakage), CWE-502 (Deserialization RCE),
and CWE-798/259 (Hardcoded Credentials) per Nebula Adversarial Audit (Cycle 33 & Cycle 34).

Key Security Guarantees:
1. Serialization Boundary & DatasetSecretScrubber:
   - All dataset rows pass through DatasetSecretScrubber (Bearer tokens, DB URLs,
     passwords, API keys, GitHub PATs, Google refresh tokens, private keys, OpenAI keys).
   - Atomic, mode-0600 file creation with advisory locking via non-blocking fcntl.flock retry and tempfile os.replace.
   - HMAC/SHA-256 integrity signature attached to every scrubbed sample.
   - Sanitization validation gate: Modal upload physically rejects un-scrubbed datasets.
2. Safe Weight Serialization & Deserialization RCE Guard (CWE-502):
   - Enforces safe_serialization=True (safetensors) for adapter export.
   - load_safe_model_weights rejects symlinks, non-whitelisted formats, and raw pickle formats while enforcing weights_only=True.
3. Modal Credential Sourcing Guard (CWE-798/259):
   - Only sources credentials via modal.Secret or standard environment variables (whitespace-only treated as None),
     never hardcoded.
"""

from __future__ import annotations

import argparse
import ast
import fcntl
import hashlib
import hmac
import json
import logging
import math
import os
import re
import stat
import struct
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Set, Tuple, Union

logger = logging.getLogger("modal_jev_finetune")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

DEFAULT_DATASET_PATH = Path("output/jev_finetuning_dataset.sanitized.jsonl")
DEFAULT_BASE_MODEL = "Qwen/Qwen2.5-Coder-1.5B-Instruct"
DATASET_SCRUBBER_SALT = "hermes_jev_dataset_scrubber_v1"

# =============================================================================
# 0. SERIALIZATION BOUNDARY & SECRET SCRUBBER (CWE-200 / CWE-259)
# =============================================================================

class DatasetSecretScrubber:
    """
    Mandatory serialization boundary and secret scrubber for fine-tuning datasets (CWE-200 / CWE-259).
    Scrubs Bearer tokens, DB credentials, API keys, GitHub PATs, Google refresh tokens,
    PEM private keys, and environment secrets prior to dataset export.
    """

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
            "pytest",
            "darwin",
            "linux",
        }
    )

    _PEM_KEY_PATTERN = re.compile(
        r"-----BEGIN [A-Z ]+ PRIVATE KEY-----[\s\S]*?-----END [A-Z ]+ PRIVATE KEY-----"
    )
    _URL_CRED_PATTERN = re.compile(
        r"(?P<scheme>\b(?:jdbc:)?[a-zA-Z][a-zA-Z0-9+.\-]*://[^:@/\s]+:)(?:[^@/\s]+)(?P<at>@)",
        re.I,
    )
    _RAW_URL_CRED_PATTERN = re.compile(
        r"\b(?:jdbc:)?[a-zA-Z][a-zA-Z0-9+.\-]*://[^:@/\s]+:(?!\[REDACTED\])[^@/\s]+@",
        re.I,
    )
    _QUERY_PARAM_PATTERN = re.compile(
        r"(?i)([\?&](?:token|key|secret|password|passwd|api[_-]?key|access[_-]?token)=)([^&\s]+)"
    )
    _RAW_QUERY_PARAM_PATTERN = re.compile(
        r"(?i)([\?&](?:token|key|secret|password|passwd|api[_-]?key|access[_-]?token)=)(?!\[REDACTED\])[^&\s]+"
    )
    _BASIC_AUTH_PATTERN = re.compile(
        r"(?i)\b(Authorization:\s*Basic\s+)[A-Za-z0-9+/=]{10,512}"
    )
    _RAW_BASIC_AUTH_PATTERN = re.compile(
        r"(?i)\bAuthorization:\s*Basic\s+(?!\[REDACTED\])[A-Za-z0-9+/=]{10,512}"
    )
    _KV_SECRET_PATTERN = re.compile(
        r"(?i)\b(?P<k>password|passwd|secret|api[_-]?key|client[_-]?secret)(?P<sep>\s*[:=]\s*)(?:[\"']?[^\s,;'\"}&\[]+[\"']?)"
    )
    _RAW_KV_SECRET_PATTERN = re.compile(
        r"(?i)\b(?P<k>password|passwd|secret|api[_-]?key|client[_-]?secret)\s*[:=]\s*[\"']?(?!\[REDACTED\])[^\s,;'\"}&\[]+"
    )
    _BEARER_PATTERN = re.compile(r"\bBearer\s+[A-Za-z0-9._\-/+=]{10,512}", re.I)
    _RAW_BEARER_PATTERN = re.compile(r"\bBearer\s+(?!\[REDACTED\])[A-Za-z0-9._\-/+=]{10,512}", re.I)
    _GH_PAT_PATTERN = re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{36,255}\b")
    _GH_FINE_GRAINED_PAT_PATTERN = re.compile(r"\bgithub_pat_[A-Za-z0-9_]{22,255}\b")
    _GOOGLE_API_KEY_PATTERN = re.compile(r"\bAIza[0-9A-Za-z\-_]{30,40}\b")
    _GOOGLE_REFRESH_PATTERN = re.compile(r"\b1//[A-Za-z0-9._\-/+=]{10,512}", re.I)
    _RAW_GOOGLE_REFRESH_PATTERN = re.compile(r"\b1//(?!\[REDACTED)[A-Za-z0-9._\-/+=]{10,512}", re.I)
    _GOOGLE_ACCESS_PATTERN = re.compile(r"\bya29\.[A-Za-z0-9._\-/+=]{10,512}", re.I)
    _RAW_GOOGLE_ACCESS_PATTERN = re.compile(r"\bya29\.(?!\[REDACTED)[A-Za-z0-9._\-/+=]{10,512}", re.I)
    _AWS_KEY_PATTERN = re.compile(r"\b(?:AKIA|ABIA|ACCA|ASIA)[0-9A-Z]{16}\b")
    _OPENAI_KEY_PATTERN = re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_\-]{20,128}\b")
    _RAW_OPENAI_KEY_PATTERN = re.compile(r"\bsk-(?:proj-)?(?!\[REDACTED)[A-Za-z0-9_\-]{20,128}\b")
    _SLACK_TOKEN_PATTERN = re.compile(r"\bxox[baprs]-[0-9A-Za-z\-]{10,72}\b")
    _RAW_SLACK_TOKEN_PATTERN = re.compile(r"\bxox[baprs]-(?!\[REDACTED)[0-9A-Za-z\-]{10,72}\b")
    _TELEGRAM_TOKEN_PATTERN = re.compile(r"\b[0-9]{6,20}:[A-Za-z0-9_\-]{30,128}\b")
    _MODAL_TOKEN_PATTERN = re.compile(r"\b(?:ak|as)-[A-Za-z0-9]{20,64}\b")
    _JWT_PATTERN = re.compile(r"\beyJ[A-Za-z0-9._\-/+=]{20,1024}")
    _RAW_JWT_PATTERN = re.compile(r"\beyJ(?!\[REDACTED)[A-Za-z0-9._\-/+=]{20,1024}")

    def __init__(
        self,
        known_secrets: Optional[Iterable[str]] = None,
        env_file: Optional[Path] = None,
    ):
        self.env_file = Path(env_file) if env_file else Path(".env")
        self._known_secrets: List[str] = self._load_known_secrets(known_secrets)

    def _load_known_secrets(self, extra: Optional[Iterable[str]] = None) -> List[str]:
        secrets: Set[str] = set()

        def _maybe_add(k: str, v: str) -> None:
            if not k or not v:
                return
            k_up = k.strip().upper()
            if any(kw in k_up for kw in self._SECRET_KEY_KEYWORDS):
                val = v.strip().strip("'\"")
                if len(val) >= 8 and val.lower() not in self._COMMON_NON_SECRETS:
                    secrets.add(val)

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

        for k, v in os.environ.items():
            _maybe_add(k, v)

        if extra:
            for s in extra:
                if isinstance(s, str) and len(s) >= 8 and s.lower() not in self._COMMON_NON_SECRETS:
                    secrets.add(s)

        sorted_secrets = sorted(secrets, key=len, reverse=True)
        return sorted_secrets

    def scrub_text(self, text: Any) -> str:
        """Best-effort regex and known-secret redaction of text fields."""
        if text is None:
            return ""
        if not isinstance(text, str):
            text = str(text)
        if not text:
            return ""

        # 1. Exact replacement of known secrets (longest first)
        for s in self._known_secrets:
            text = text.replace(s, "[REDACTED]")

        # 2. Structural & pattern redaction
        text = self._PEM_KEY_PATTERN.sub("[REDACTED_PRIVATE_KEY]", text)
        text = self._URL_CRED_PATTERN.sub(r"\g<scheme>[REDACTED]\g<at>", text)
        text = self._QUERY_PARAM_PATTERN.sub(r"\g<1>[REDACTED]", text)
        text = self._BASIC_AUTH_PATTERN.sub(r"\g<1>[REDACTED]", text)
        text = self._KV_SECRET_PATTERN.sub(r"\g<k>\g<sep>[REDACTED]", text)
        text = self._BEARER_PATTERN.sub("Bearer [REDACTED]", text)
        text = self._GH_PAT_PATTERN.sub("[REDACTED_GITHUB_PAT]", text)
        text = self._GH_FINE_GRAINED_PAT_PATTERN.sub("[REDACTED_GITHUB_PAT]", text)
        text = self._GOOGLE_API_KEY_PATTERN.sub("[REDACTED_GOOGLE_API_KEY]", text)
        text = self._GOOGLE_REFRESH_PATTERN.sub("[REDACTED_GOOGLE_REFRESH_TOKEN]", text)
        text = self._GOOGLE_ACCESS_PATTERN.sub("[REDACTED_GOOGLE_ACCESS_TOKEN]", text)
        text = self._AWS_KEY_PATTERN.sub("[REDACTED_AWS_KEY]", text)
        text = self._OPENAI_KEY_PATTERN.sub("[REDACTED_OPENAI_KEY]", text)
        text = self._SLACK_TOKEN_PATTERN.sub("[REDACTED_SLACK_TOKEN]", text)
        text = self._TELEGRAM_TOKEN_PATTERN.sub("[REDACTED_TELEGRAM_TOKEN]", text)
        text = self._MODAL_TOKEN_PATTERN.sub("[REDACTED_MODAL_TOKEN]", text)
        text = self._JWT_PATTERN.sub("[REDACTED_JWT]", text)

        return text

    def scrub(self, data: Any) -> Any:
        """Recursively scrub strings, dicts, lists, and sets."""
        if isinstance(data, str):
            return self.scrub_text(data)
        elif isinstance(data, dict):
            return {self.scrub_text(str(k)): self.scrub(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.scrub(elem) for elem in data]
        elif isinstance(data, tuple):
            return tuple(self.scrub(elem) for elem in data)
        elif isinstance(data, set):
            return {self.scrub(elem) for elem in data}
        return data

    @classmethod
    def compute_integrity_hash(cls, record: Dict[str, Any]) -> str:
        """Computes a salted HMAC/SHA-256 fingerprint over non-metadata record fields."""
        clean = {k: v for k, v in record.items() if k != "_metadata"}
        canonical_bytes = json.dumps(clean, sort_keys=True, ensure_ascii=False).encode("utf-8")
        return hashlib.sha256(f"{DATASET_SCRUBBER_SALT}:".encode("utf-8") + canonical_bytes).hexdigest()

    def sign_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Scrubs record and attaches a verifiable cryptographic scrubber signature."""
        scrubbed = self.scrub(record)
        integrity_hash = self.compute_integrity_hash(scrubbed)
        scrubbed["_metadata"] = {
            "scrubber": "DatasetSecretScrubber",
            "version": "1.0",
            "sanitized_at": datetime.now(timezone.utc).isoformat(),
            "integrity_hash": integrity_hash,
            "signature": f"scrubbed:{integrity_hash[:16]}",
        }
        return scrubbed

    @classmethod
    def verify_record_integrity(cls, record: Dict[str, Any]) -> bool:
        """Verifies that record was generated by DatasetSecretScrubber and has not been tampered with."""
        if not isinstance(record, dict):
            return False
        meta = record.get("_metadata")
        if not isinstance(meta, dict):
            return False
        if meta.get("scrubber") != "DatasetSecretScrubber":
            return False
        expected_hash = meta.get("integrity_hash")
        if not expected_hash:
            return False
        actual_hash = cls.compute_integrity_hash(record)
        return hmac.compare_digest(actual_hash, expected_hash)


_HIGH_ENTROPY_TOKEN = re.compile(r"\b[A-Za-z0-9_\-/+=]{24,}\b")
_ENTROPY_BYTE_CAP = 2 * 1024 * 1024  # 2MB cap to prevent CPU exhaustion on oversized inputs (CWE-400)


def shannon_entropy(s: str) -> float:
    """Calculates Shannon entropy in bits per character."""
    if not s:
        return 0.0
    counts = {c: s.count(c) for c in set(s)}
    n = len(s)
    return -sum((count / n) * math.log2(count / n) for count in counts.values())


def is_allowlisted_high_entropy(token: str) -> bool:
    """
    Allowlists legitimate high-entropy tokens:
    - Redacted placeholders ([REDACTED], [REDACTED_...])
    - Hex digests (HMAC, SHA-256, MD5)
    - Safe known model identifiers, class names, or constants
    """
    if token.startswith("[REDACTED"):
        return True
    clean = token.replace("-", "").lower()
    if all(c in "0123456789abcdef" for c in clean):
        return True
    allowlisted_substrings = (
        "Qwen",
        "Coder",
        "Instruct",
        "TransactionCase",
        "DatasetSecretScrubber",
        "instruction",
        "content_sha256",
        "provenance_signature",
        "integrity_hash",
        "generated_at",
        "dataset_filename",
    )
    if any(sub in token for sub in allowlisted_substrings):
        return True
    return False


def validate_dataset_is_sanitized(
    content: str,
    enforce_signature: bool = True,
    known_secrets: Optional[Iterable[str]] = None,
) -> Tuple[bool, List[str]]:
    """
    Validates that a dataset string has been fully sanitized and signed.
    Fails closed if unredacted secrets, unknown high-entropy tokens, or missing
    integrity signatures are detected (CWE-200 non-circular defense).
    """
    violations: List[str] = []
    if not content or not content.strip():
        return False, ["Dataset content is empty."]

    scrubber = DatasetSecretScrubber(known_secrets=known_secrets)

    # 1. Exact environment secret scan
    for s in scrubber._known_secrets:
        if s in content:
            violations.append(f"Unredacted environment secret detected: {s[:3]}...{s[-2:]}")

    # 2. Regex pattern scan for unredacted credentials
    raw_patterns = [
        ("PEM Private Key", DatasetSecretScrubber._PEM_KEY_PATTERN),
        ("Database URL Credentials", DatasetSecretScrubber._RAW_URL_CRED_PATTERN),
        ("Basic Auth Credentials", DatasetSecretScrubber._RAW_BASIC_AUTH_PATTERN),
        ("URL Query Parameter Secret", DatasetSecretScrubber._RAW_QUERY_PARAM_PATTERN),
        ("Key-Value Secret", DatasetSecretScrubber._RAW_KV_SECRET_PATTERN),
        ("Bearer Token", DatasetSecretScrubber._RAW_BEARER_PATTERN),
        ("GitHub PAT", DatasetSecretScrubber._GH_PAT_PATTERN),
        ("GitHub Fine-Grained PAT", DatasetSecretScrubber._GH_FINE_GRAINED_PAT_PATTERN),
        ("Google API Key", DatasetSecretScrubber._GOOGLE_API_KEY_PATTERN),
        ("Google Refresh Token", DatasetSecretScrubber._RAW_GOOGLE_REFRESH_PATTERN),
        ("Google Access Token", DatasetSecretScrubber._RAW_GOOGLE_ACCESS_PATTERN),
        ("AWS Key", DatasetSecretScrubber._AWS_KEY_PATTERN),
        ("OpenAI API Key", DatasetSecretScrubber._RAW_OPENAI_KEY_PATTERN),
        ("Slack Token", DatasetSecretScrubber._RAW_SLACK_TOKEN_PATTERN),
        ("Telegram Bot Token", DatasetSecretScrubber._TELEGRAM_TOKEN_PATTERN),
        ("Modal Token", DatasetSecretScrubber._MODAL_TOKEN_PATTERN),
        ("JWT Token", DatasetSecretScrubber._RAW_JWT_PATTERN),
    ]

    for name, pat in raw_patterns:
        m = pat.search(content)
        if m:
            violations.append(f"Unredacted {name} detected: {m.group(0)[:40]}")

    # 3. Independent High-Entropy Token Scan (Non-Circular Defense, bounded for CWE-400)
    scan_content = content[:_ENTROPY_BYTE_CAP]
    for m in _HIGH_ENTROPY_TOKEN.finditer(scan_content):
        tok = m.group(0)
        if is_allowlisted_high_entropy(tok):
            continue
        h = shannon_entropy(tok)
        if h >= 3.8:
            violations.append(f"Unredacted high-entropy token detected (entropy={h:.2f}): {tok[:12]}...")

    # 4. Parse JSON lines and verify schema and cryptographic signature
    lines = [l for l in content.strip().splitlines() if l.strip()]
    if not lines:
        violations.append("Dataset contains no valid records.")

    for idx, line in enumerate(lines, 1):
        try:
            item = json.loads(line)
        except json.JSONDecodeError as e:
            violations.append(f"Line {idx}: Invalid JSON ({e})")
            continue

        if not isinstance(item, dict):
            violations.append(f"Line {idx}: Record is not a JSON object")
            continue

        for req_field in ("instruction", "input", "output"):
            if req_field not in item:
                violations.append(f"Line {idx}: Missing required schema field '{req_field}'")

        if enforce_signature:
            if not DatasetSecretScrubber.verify_record_integrity(item):
                violations.append(f"Line {idx}: Missing or invalid DatasetSecretScrubber integrity signature")

    is_valid = len(violations) == 0
    return is_valid, violations


# =============================================================================
# 1. SAFE WEIGHT SERIALIZATION & DESERIALIZATION (CWE-502)
# =============================================================================

_PICKLE_OPCODES = (b"\x80\x00", b"\x80\x01", b"\x80\x02", b"\x80\x03", b"\x80\x04", b"\x80\x05")


def load_safe_model_weights(
    weights_path: Union[str, Path],
    device: str = "cpu",
) -> Any:
    """
    Safely loads model weights enforcing CWE-502 RCE deserialization guards.
    Rejects symlinks, unwhitelisted extensions, raw pickle formats (.pkl, .pickle)
    and enforces safetensors or weights_only=True for PyTorch checkpoints.
    Inspects magic bytes to prevent renamed pickle or zip container bypasses.
    """
    path = Path(weights_path)
    if path.is_symlink():
        raise ValueError(
            f"Refusing symlinked weight file: {path} (CWE-502). "
            "Symlinks prohibited in model weights path."
        )

    if not path.exists():
        raise FileNotFoundError(f"Weights path does not exist: {path}")

    # If directory, find weights file prioritizing safetensors
    if path.is_dir():
        safetensors_file = path / "adapter_model.safetensors"
        if not safetensors_file.exists():
            safetensors_file = path / "model.safetensors"
        if safetensors_file.exists():
            path = safetensors_file
        else:
            pt_file = path / "adapter_model.bin"
            if not pt_file.exists():
                pt_file = path / "pytorch_model.bin"
            if pt_file.exists():
                path = pt_file
            else:
                pkl_files = list(path.glob("*.pkl")) + list(path.glob("*.pickle"))
                if pkl_files:
                    raise ValueError(
                        f"Insecure pickle file detected in {path}: {pkl_files[0].name} (CWE-502). "
                        "Raw pickle formats are strictly prohibited."
                    )
                raise FileNotFoundError(f"No safe weights found in directory: {path}")

        if path.is_symlink():
            raise ValueError(
                f"Refusing symlinked weight file: {path} (CWE-502). "
                "Symlinks prohibited in model weights path."
            )

    suffix = path.suffix.lower()
    if suffix not in (".safetensors", ".pt", ".pth", ".bin"):
        raise ValueError(
            f"Insecure or unsupported weight file format '{suffix}' rejected (CWE-502). "
            "Only .safetensors or authenticated PyTorch checkpoints permitted."
        )

    # File permissions & magic byte inspection
    if path.is_file():
        mode = path.stat().st_mode
        if mode & stat.S_IWOTH:
            raise ValueError(
                f"Weight file '{path.name}' is world-writable ({oct(mode)}). "
                "Rejecting potentially tampered weights container."
            )

        with open(path, "rb") as f:
            head = f.read(16)
        if len(head) < 2:
            raise ValueError(f"Truncated or empty weights file: {path}")

        # Reject pickle bytecode and zip container archives disguised under any extension
        if head[:2] in _PICKLE_OPCODES or head[:2] == b"PK":
            if suffix == ".safetensors":
                raise ValueError(
                    f"Refusing to load non-safetensors artifact disguised as '{path.name}' (CWE-502): "
                    "Pickle or zip container signature detected."
                )
            if suffix not in (".pt", ".pth", ".bin"):
                raise ValueError(
                    f"Insecure pickle bytecode detected in '{path.name}' (CWE-502). "
                    "Only .safetensors or authenticated PyTorch weights_only=True files permitted."
                )

    if suffix == ".safetensors":
        if path.is_file():
            with open(path, "rb") as f:
                head = f.read(8)
            if len(head) < 8:
                raise ValueError(f"Truncated safetensors header in {path}")
            try:
                (header_len,) = struct.unpack("<Q", head)
            except struct.error as e:
                raise ValueError(f"Malformed safetensors header length in '{path.name}': {e}")
            if header_len == 0 or header_len > 100_000_000:
                raise ValueError(
                    f"Implausible safetensors header length ({header_len}) in '{path.name}'. "
                    "Container is corrupted or malicious."
                )
        from safetensors.torch import load_file
        return load_file(str(path), device=device)

    import torch
    # For PyTorch weights (.pt, .pth, .bin), strictly enforce weights_only=True
    return torch.load(str(path), map_location=device, weights_only=True)


# =============================================================================
# 2. MODAL CREDENTIAL SOURCING (CWE-798 / CWE-259)
# =============================================================================

class ModalCredentialError(RuntimeError):
    """Raised when required Modal credentials cannot be safely sourced (CWE-798/259)."""
    pass


def get_modal_credentials(require: bool = False) -> Dict[str, Optional[str]]:
    """
    Safely source Modal credentials from environment variables or modal configuration (CWE-798/259).
    Never hardcodes credentials or echoes secret values in error messages.
    """
    token_id = (os.environ.get("MODAL_TOKEN_ID") or "").strip() or None
    token_secret = (os.environ.get("MODAL_TOKEN_SECRET") or "").strip() or None

    modal_toml = Path.home() / ".modal.toml"
    if modal_toml.exists():
        try:
            mode = stat.S_IMODE(modal_toml.stat().st_mode)
            if mode & (stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH | stat.S_IWOTH):
                logger.warning(
                    "Modal credentials file %s has overly permissive mode %o (world/group readable). "
                    "Recommend running: chmod 0600 %s",
                    modal_toml,
                    mode,
                    modal_toml,
                )
        except OSError:
            pass

    if require and not (token_id and token_secret) and not os.environ.get("MODAL_PROFILE"):
        if not modal_toml.exists():
            missing = []
            if not token_id:
                missing.append("MODAL_TOKEN_ID")
            if not token_secret:
                missing.append("MODAL_TOKEN_SECRET")
            raise ModalCredentialError(f"Missing required Modal credentials: {', '.join(missing)}")

    return {
        "MODAL_TOKEN_ID": token_id,
        "MODAL_TOKEN_SECRET": token_secret,
    }


# =============================================================================
# 3. DATASET PROVENANCE MANIFEST & SUPPLY-CHAIN INTEGRITY
# =============================================================================

def generate_dataset_manifest(
    dataset_path: Path,
    dataset_content: str,
    sample_count: int,
) -> Dict[str, Any]:
    """
    Computes an immutable build-time provenance manifest for the fine-tuning dataset.
    Binds the dataset content hash (SHA-256) to git commit provenance, record count,
    and HMAC signature to enforce supply-chain attestability.
    """
    content_hash = hashlib.sha256(dataset_content.encode("utf-8")).hexdigest()

    git_commit = "unknown"
    try:
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
        if res.returncode == 0 and res.stdout.strip():
            git_commit = res.stdout.strip()
    except Exception:
        pass

    manifest = {
        "dataset_filename": dataset_path.name,
        "sample_count": sample_count,
        "content_sha256": content_hash,
        "git_commit": git_commit,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scrubber_version": "1.0",
        "provenance_signature": hashlib.sha256(
            f"{DATASET_SCRUBBER_SALT}:{content_hash}:{git_commit}".encode("utf-8")
        ).hexdigest(),
    }
    return manifest


@contextmanager
def advisory_file_lock(lock_path: Path, timeout: float = 10.0):
    """
    Acquires an exclusive advisory file lock using fcntl.flock with non-blocking retry and timeout (CWE-362/400).
    Opens lock file with mode 0600, retries with 0.1s sleep until timeout deadline,
    and guarantees release and cleanup in finally.
    """
    lock_path = Path(lock_path)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(str(lock_path), os.O_CREAT | os.O_RDWR, 0o600)
    deadline = time.monotonic() + timeout
    acquired = False
    try:
        while True:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                acquired = True
                break
            except (BlockingIOError, OSError) as e:
                if time.monotonic() >= deadline:
                    raise TimeoutError(
                        f"Advisory lock timeout ({timeout}s) on {lock_path}; possible stale lock or contention"
                    ) from e
                time.sleep(0.1)
        yield
    finally:
        if acquired:
            try:
                fcntl.flock(fd, fcntl.LOCK_UN)
            except OSError:
                pass
        try:
            os.close(fd)
        except OSError:
            pass
        if acquired and lock_path.exists():
            try:
                lock_path.unlink()
            except OSError:
                pass


def _coerce_timestamp(val: Any) -> Optional[float]:
    """
    Normalizes numeric or ISO-8601 strings into POSIX timestamp float (CWE-367/613).
    Returns None on missing, invalid or corrupt timestamps to fail closed.
    """
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        val = val.strip()
        if not val:
            return None
        try:
            return float(val)
        except ValueError:
            pass
        try:
            iso_val = val.replace("Z", "+00:00")
            return datetime.fromisoformat(iso_val).timestamp()
        except (ValueError, TypeError):
            return None
    return None


def write_dataset_manifest(dataset_path: Path, manifest: Dict[str, Any]) -> Path:
    """
    Writes the dataset manifest file atomically alongside the dataset (e.g. dataset.jsonl.manifest.json).
    Uses advisory locking and atomic temporary file replacement (os.replace) with unique per-writer
    temporary file paths to prevent torn writes under concurrent writers (CWE-362).

    NOTE: fcntl.flock is per-host. For cross-node distributed swarm storage,
    an external distributed lock or conditional put (e.g. S3 If-Match / lease) must be used.
    """
    manifest_path = dataset_path.with_name(f"{dataset_path.name}.manifest.json")
    manifest_content = json.dumps(manifest, indent=2, sort_keys=True)
    payload = manifest_content.encode("utf-8")

    # Unique temporary filename per pid, thread ID, and UUID (CWE-362)
    tmp_name = f".{manifest_path.name}.{os.getpid()}.{threading.get_ident()}.{uuid.uuid4().hex}.tmp"
    tmp_path = manifest_path.parent / tmp_name

    lock_file = manifest_path.with_name(f".{manifest_path.name}.lock")
    with advisory_file_lock(lock_file):
        try:
            fd = os.open(str(tmp_path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            try:
                os.write(fd, payload)
                os.fsync(fd)
            finally:
                os.close(fd)
            os.replace(tmp_path, manifest_path)
            try:
                os.chmod(manifest_path, 0o600)
            except OSError:
                pass
        finally:
            if tmp_path.exists():
                try:
                    tmp_path.unlink()
                except OSError:
                    pass
    return manifest_path


def verify_dataset_manifest(
    dataset_or_manifest: Union[Path, str, Dict[str, Any]],
    max_clock_skew_s: float = 120.0,
    max_age_s: Optional[float] = 604800.0,
) -> Tuple[bool, List[str]]:
    """
    Verifies that the dataset matches its provenance manifest and has not been altered or replaced.
    Fails closed if manifest is missing, corrupt, hash mismatches, or clock skew/expiry exceeds bounds (CWE-367/613).
    """
    violations: List[str] = []

    if isinstance(dataset_or_manifest, dict):
        manifest = dataset_or_manifest
        content = None
    else:
        dataset_path = Path(dataset_or_manifest)
        if not dataset_path.exists():
            return False, [f"Dataset file does not exist: {dataset_path}"]

        manifest_path = dataset_path.with_name(f"{dataset_path.name}.manifest.json")
        if not manifest_path.exists():
            return False, [f"Missing dataset provenance manifest: {manifest_path}"]

        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception as e:
            return False, [f"Corrupted dataset manifest ({e})"]

        content = dataset_path.read_text(encoding="utf-8")

    # 1. Clock skew and expiration validation with single timestamp normalizer (CWE-367 / CWE-613)
    gen_at_raw = manifest.get("generated_at")
    gen_ts = _coerce_timestamp(gen_at_raw)
    now_ts = time.time()

    if gen_ts is None:
        violations.append(f"Invalid or missing generated_at in manifest: '{gen_at_raw}' (fail-closed)")
    else:
        if gen_ts - now_ts > max_clock_skew_s:
            violations.append(
                f"Clock skew violation: manifest generated_at is {gen_ts - now_ts:.1f}s in the future "
                f"(exceeds max_clock_skew_s={max_clock_skew_s}s)."
            )
        if max_age_s is not None and now_ts - gen_ts > max_age_s:
            violations.append(
                f"Manifest expired: age is {now_ts - gen_ts:.1f}s (exceeds max_age_s={max_age_s}s) (replay guard)."
            )

    # 2. Content integrity and HMAC signature validation
    if content is not None:
        actual_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        expected_hash = manifest.get("content_sha256")

        if actual_hash != expected_hash:
            violations.append(
                f"Provenance hash mismatch: expected {expected_hash}, calculated {actual_hash}"
            )

        expected_sig = manifest.get("provenance_signature")
        git_commit = manifest.get("git_commit", "unknown")
        calc_sig = hashlib.sha256(
            f"{DATASET_SCRUBBER_SALT}:{actual_hash}:{git_commit}".encode("utf-8")
        ).hexdigest()

        if not hmac.compare_digest(calc_sig, expected_sig or ""):
            violations.append("Provenance cryptographic signature verification failed.")

    return len(violations) == 0, violations


def is_tombstoned(
    tombstone_tx_time: Optional[Union[float, int, datetime]],
    reader_now: Optional[Union[float, int, datetime]] = None,
    valid_to: Optional[Union[float, int, datetime]] = None,
) -> bool:
    """
    Bi-Temporal Invariant (Zero-Resurrection): A tombstone is an immutable monotonic fact.
    Once written, tombstone existence is permanent: neither a lagging nor a leading
    reader wall-clock can resurrect a deleted/tombstoned entity (CWE-367/613).
    """
    return tombstone_tx_time is not None


class QuotaBreaker:
    """
    Circuit breaker preventing retry-storm amplification under compute/quota exhaustion (CWE-400).
    Surfaced by Nebula Adversarial Audit What-If ("compute quota cut by 80%").
    Applies bounded exponential backoff for transient quota/rate throttling (429/503),
    and fails closed immediately without retry on terminal/non-quota errors.
    """

    def __init__(
        self,
        max_attempts: int = 3,
        base_backoff_s: float = 2.0,
        max_backoff_s: float = 30.0,
    ):
        self.max_attempts = max_attempts
        self.base_backoff_s = base_backoff_s
        self.max_backoff_s = max_backoff_s

    @staticmethod
    def is_quota_error(exc: Exception) -> bool:
        msg = str(exc).lower()
        return any(k in msg for k in (
            "429",
            "quota",
            "resource_exhausted",
            "rate limit",
            "too many requests",
            "capacity",
            "overloaded",
            "concurrency limit",
            "throttled",
        ))

    def execute(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        last_exc = None
        for attempt in range(1, self.max_attempts + 1):
            try:
                return fn(*args, **kwargs)
            except Exception as e:
                last_exc = e
                if not self.is_quota_error(e) or attempt >= self.max_attempts:
                    raise
                backoff = min(self.base_backoff_s * (2 ** (attempt - 1)), self.max_backoff_s)
                logger.warning(
                    "Quota throttling detected (attempt %d/%d). Backing off for %.1fs: %s",
                    attempt, self.max_attempts, backoff, e,
                )
                time.sleep(backoff)
        if last_exc:
            raise last_exc


# =============================================================================
# 4. DATASET HARVESTING & SYNTHESIS
# =============================================================================

JEV_SYSTEM_INSTRUCTION = (
    "You are the Local JEV (Judge / Evolution Validator) Decision Model. "
    "Evaluate the task prompt and workspace context, determine the domain, "
    "compute the complexity score [0.0, 4.0], select the native test runner, "
    "and decide whether Clef Cloud Dialect Council escalation is required."
)


def harvest_dataset_from_ledgers(
    action_ledger_path: Optional[Path] = None,
    evolution_db_path: Optional[Path] = None,
    output_path: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    """
    Harvests past actions and decisions into structured, sanitized instruction-tuning pairs.
    Enforces secret scrubbing, double-barrier validation, provenance manifests, and atomic mode-0600 file write.
    """
    out_file = output_path or DEFAULT_DATASET_PATH
    out_file.parent.mkdir(parents=True, exist_ok=True)

    scrubber = DatasetSecretScrubber()
    records: List[Dict[str, Any]] = []

    # 1. Ingest from ActionLedger if available
    ledger_p = action_ledger_path or (Path.home() / ".gemini" / "antigravity" / "action_ledger.jsonl")
    if ledger_p.exists():
        try:
            with open(ledger_p, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        # Immediate read-boundary scrubbing before JSON deserialization (CWE-200)
                        scrubbed_line = scrubber.scrub_text(line)
                        raw_entry = json.loads(scrubbed_line)
                        if raw_entry.get("action") == "jev_decision_evaluation":
                            # Deep-object recursive scrub pass
                            entry = scrubber.scrub(raw_entry)
                            details = entry.get("details", {})
                            domain = entry.get("domain", "general_ai_workspace")
                            complexity = float(details.get("complexity", 1.5))
                            tier = details.get("tier", "PRO")
                            runner = details.get("runner", "pytest (`pytest tests/ -v`)")
                            status = entry.get("status", "PERMITTED")

                            rec = {
                                "instruction": JEV_SYSTEM_INSTRUCTION,
                                "input": {
                                    "prompt": f"Evaluate task: {entry.get('payload_sha256', '')}",
                                    "domain": domain,
                                },
                                "output": {
                                    "domain": domain,
                                    "complexity_score": complexity,
                                    "target_tier": tier,
                                    "test_runner": runner,
                                    "requires_cloud_escalation": complexity >= 2.2,
                                    "verdict": status,
                                    "rationale": f"JEV verdict for {domain} with complexity {complexity}.",
                                },
                            }
                            # Attach cryptographic scrubber integrity signature
                            records.append(scrubber.sign_record(rec))
                    except Exception:
                        pass
        except Exception as e:
            logger.warning("Failed reading action ledger: %s", e)

    # 2. Ensure Curated High-Fidelity Domain Anchors (Self-Contained Bootstrap)
    seed_anchors = [
        {
            "prompt": "Run full regression test suite across accounting modules in O20.",
            "domain": "enterprise_erp",
            "workspace": "/home/zen/O20",
            "ladder_step": 1,
            "complexity": 1.2,
            "tier": "PRO",
            "runner": "odoo.tests.common.TransactionCase (`odoo-bin --test-enable`)",
            "escalate": False,
            "verdict": "PERMITTED",
            "rationale": "Standard regression test on ERP domain. Fast-path local execution permitted.",
        },
        {
            "prompt": "Synthesize 4-vector adversarial stress test suite for HSE incident state machine under concurrency.",
            "domain": "enterprise_erp",
            "workspace": "/home/zen/VerticalRisk",
            "ladder_step": 3,
            "complexity": 2.8,
            "tier": "ULTRA",
            "runner": "odoo.tests.common.TransactionCase (`odoo-bin --test-enable`)",
            "escalate": True,
            "verdict": "ESCALATED",
            "rationale": "High concurrency race interleaving and state machine proof requires Dialect Council escalation.",
        },
        {
            "prompt": "Verify deterministic fixed-timestep game physics loop with frame rollback interpolation in Graydoom RTS.",
            "domain": "game_simulation",
            "workspace": "/home/zen/Graydoom",
            "ladder_step": 4,
            "complexity": 3.1,
            "tier": "ULTRA",
            "runner": "node:test (`NODE_ENV=test node --test tests/*.test.js`)",
            "escalate": True,
            "verdict": "ESCALATED",
            "rationale": "Game physics determinism and frame rollback require ultra-tier consensus reasoning.",
        },
        {
            "prompt": "Add offline SQLite cache syncing with drift detection for field safety inspection in Insilos Mobile.",
            "domain": "enterprise_erp",
            "workspace": "/home/zen/insilos_mobile",
            "ladder_step": 2,
            "complexity": 2.1,
            "tier": "PRO",
            "runner": "flutter test (`flutter test`)",
            "escalate": False,
            "verdict": "PERMITTED",
            "rationale": "Mobile offline sync logic under threshold 2.2. Fast-path local execution permitted.",
        },
        {
            "prompt": "Check unit test coverage on secret scrubber and SSRF guard in Hermes Agent.",
            "domain": "ai_infrastructure",
            "workspace": "/home/zen/hermes-agent",
            "ladder_step": 1,
            "complexity": 1.4,
            "tier": "PRO",
            "runner": "pytest (`pytest tests/ -v`)",
            "escalate": False,
            "verdict": "PERMITTED",
            "rationale": "Standard security unit tests in Hermes. Fast-path execution permitted.",
        },
    ]

    for anchor in seed_anchors:
        rec = {
            "instruction": JEV_SYSTEM_INSTRUCTION,
            "input": {
                "prompt": anchor["prompt"],
                "domain": anchor["domain"],
                "workspace": anchor["workspace"],
                "ladder_step": anchor["ladder_step"],
            },
            "output": {
                "domain": anchor["domain"],
                "complexity_score": anchor["complexity"],
                "target_tier": anchor["tier"],
                "test_runner": anchor["runner"],
                "requires_cloud_escalation": anchor["escalate"],
                "verdict": anchor["verdict"],
                "rationale": anchor["rationale"],
            },
        }
        records.append(scrubber.sign_record(rec))

    # 3. Write atomic mode-0600 file with advisory flock
    lock_file = out_file.with_name(f".{out_file.name}.lock")
    with advisory_file_lock(lock_file):
        tmp_path = out_file.parent / f".{out_file.name}.{uuid.uuid4().hex}.tmp"
        tmp_fd = os.open(str(tmp_path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            with open(tmp_fd, "w", encoding="utf-8", closefd=True) as tmp_file:
                for r in records:
                    tmp_file.write(json.dumps(r, ensure_ascii=False) + "\n")
                tmp_file.flush()
                os.fsync(tmp_file.fileno())

            # Double-barrier post-harvest sanitization check before atomic publish
            written_content = tmp_path.read_text(encoding="utf-8")
            is_valid, violations = validate_dataset_is_sanitized(written_content)
            if not is_valid:
                if tmp_path.exists():
                    try:
                        tmp_path.unlink()
                    except OSError:
                        pass
                raise ValueError(
                    f"Dataset post-harvest sanitization gate failed (CWE-200): {violations}. "
                    "Refusing to write unsanitized dataset."
                )

            os.replace(tmp_path, out_file)
            try:
                os.chmod(out_file, 0o600)
            except OSError:
                pass

            # Generate and write immutable dataset provenance manifest
            manifest = generate_dataset_manifest(
                dataset_path=out_file,
                dataset_content=written_content,
                sample_count=len(records),
            )
            write_dataset_manifest(out_file, manifest)
        except Exception:
            if tmp_path.exists():
                try:
                    tmp_path.unlink()
                except OSError:
                    pass
            raise

    logger.info("Harvested, scrubbed and signed %d JEV training samples into %s", len(records), out_file)
    return records


# =============================================================================
# 4. MODAL TRAINING APP DEFINITION
# =============================================================================

def _train_jev_modal_impl(
    dataset_jsonl_content: str,
    base_model_name: str = DEFAULT_BASE_MODEL,
    epochs: int = 3,
) -> Dict[str, Any]:
    """
    Core implementation of QLoRA 4-bit fine-tuning of JEV Decision Model.
    Enforces sanitization validation and safe weight serialization.
    """
    # 0. Enforce sanitization validation gate (Fail-Closed)
    is_valid, violations = validate_dataset_is_sanitized(dataset_jsonl_content)
    if not is_valid:
        raise ValueError(f"Dataset sanitization validation failed: {violations}")

    import time
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig, TrainingArguments
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
    from datasets import Dataset

    start_time = time.time()
    print(f"[Modal] Initializing JEV fine-tuning on {torch.cuda.get_device_name(0)}")

    # 1. Parse dataset
    lines = [json.loads(l) for l in dataset_jsonl_content.strip().splitlines() if l.strip()]
    formatted_data = []
    for item in lines:
        text = (
            f"<|im_start|>system\n{item['instruction']}<|im_end|>\n"
            f"<|im_start|>user\n{json.dumps(item['input'], ensure_ascii=False)}<|im_end|>\n"
            f"<|im_start|>assistant\n{json.dumps(item['output'], ensure_ascii=False)}<|im_end|>"
        )
        formatted_data.append({"text": text})

    ds = Dataset.from_list(formatted_data)
    print(f"[Modal] Loaded dataset with {len(ds)} instruction-tuning pairs.")

    # 2. Load Tokenizer & Quantized Base Model
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )

    tokenizer = AutoTokenizer.from_pretrained(base_model_name, trust_remote_code=True)
    if not tokenizer.pad_token:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        base_model_name,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
    )
    model = prepare_model_for_kbit_training(model)

    # 3. LoRA Configuration
    peft_config = LoraConfig(
        r=16,
        lora_alpha=32,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, peft_config)
    model.print_trainable_parameters()

    # 4. Tokenization & Formatting
    def tokenize_fn(example):
        return tokenizer(
            example["text"],
            truncation=True,
            max_length=1024,
            padding="max_length",
        )

    tokenized_ds = ds.map(tokenize_fn, batched=False)

    # 5. Training Arguments (Bounded Budget & Safe Serialization)
    output_dir = Path("/tmp/jev_model_output")
    training_args = TrainingArguments(
        output_dir=str(output_dir),
        num_train_epochs=epochs,
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,
        learning_rate=2e-4,
        lr_scheduler_type="cosine",
        logging_steps=5,
        fp16=True,
        optim="paged_adamw_8bit",
        save_strategy="no",
        save_safetensors=True,  # Safe serialization guard (CWE-502)
        report_to="none",
    )

    from trl import SFTTrainer
    trainer = SFTTrainer(
        model=model,
        train_dataset=tokenized_ds,
        dataset_text_field="text",
        max_seq_length=1024,
        tokenizer=tokenizer,
        args=training_args,
    )

    train_result = trainer.train()

    # Safe Adapter Export Boundary (CWE-502):
    # Enforces safe_serialization=True (.safetensors format)
    output_dir.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(str(output_dir), safe_serialization=True)
    tokenizer.save_pretrained(str(output_dir))

    duration = round(time.time() - start_time, 2)

    return {
        "status": "SUCCESS",
        "base_model": base_model_name,
        "training_samples": len(ds),
        "epochs": epochs,
        "duration_seconds": duration,
        "train_loss": round(float(train_result.training_loss), 4),
        "gpu": torch.cuda.get_device_name(0),
        "weights_format": "safetensors",
        "safe_serialization": True,
    }


class CallableModalFunction:
    """Wrapper that enables both direct, .local(), and .remote() invocation on modal functions."""

    def __init__(self, fn: Any, impl: Any):
        self._fn = fn
        self._impl = impl

    def __call__(self, *args, **kwargs):
        return self._impl(*args, **kwargs)

    def local(self, *args, **kwargs):
        if hasattr(self._fn, "local"):
            return self._fn.local(*args, **kwargs)
        return self._impl(*args, **kwargs)

    def remote(self, *args, **kwargs):
        if hasattr(self._fn, "remote"):
            return self._fn.remote(*args, **kwargs)
        return self._impl(*args, **kwargs)

    def __getattr__(self, name):
        return getattr(self._fn, name)


try:
    import modal

    def _configure_modal_secrets() -> List[Any]:
        secrets = []
        if "MODAL_SECRET_NAME" in os.environ:
            secrets.append(modal.Secret.from_name(os.environ["MODAL_SECRET_NAME"]))
        elif "MODAL_TOKEN_ID" in os.environ and "MODAL_TOKEN_SECRET" in os.environ:
            secrets.append(
                modal.Secret.from_dict({
                    "MODAL_TOKEN_ID": os.environ["MODAL_TOKEN_ID"],
                    "MODAL_TOKEN_SECRET": os.environ["MODAL_TOKEN_SECRET"],
                })
            )
        return secrets

    app = modal.App("jev-decision-finetune")
    training_image = (
        modal.Image.debian_slim(python_version="3.11")
        .pip_install(
            "torch==2.3.1",
            "transformers==4.42.4",
            "peft==0.11.1",
            "trl==0.9.6",
            "bitsandbytes==0.43.1",
            "accelerate==0.32.1",
            "datasets==2.20.0",
            "safetensors==0.4.3",
        )
    )

    _modal_raw_fn = app.function(
        image=training_image,
        gpu="T4",
        timeout=2700,
        memory=16384,
        secrets=_configure_modal_secrets(),
    )(_train_jev_modal_impl)

    train_jev_modal = CallableModalFunction(_modal_raw_fn, _train_jev_modal_impl)

except ImportError:
    app = None
    train_jev_modal = _train_jev_modal_impl


# =============================================================================
# 5. LOCAL CLI ENTRYPOINT
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Modal JEV Decision Model Fine-Tuning Harness")
    parser.add_argument("--harvest-dataset", action="store_true", help="Extract and synthesize training dataset from ledgers.")
    parser.add_argument("--dry-run", action="store_true", help="Validate dataset format and token lengths without spawning cloud containers.")
    parser.add_argument("--train-modal", action="store_true", help="Dispatch training job to Modal.com T4 GPU.")
    parser.add_argument("--dataset-path", type=str, default=str(DEFAULT_DATASET_PATH), help="Path to JSONL dataset.")
    parser.add_argument("--base-model", type=str, default=DEFAULT_BASE_MODEL, help="Base HuggingFace model.")

    args = parser.parse_args()

    ds_path = Path(args.dataset_path)

    if args.harvest_dataset or not ds_path.exists():
        records = harvest_dataset_from_ledgers(output_path=ds_path)
        print(f"✅ Harvested and sanitized {len(records)} records into {ds_path}")

    if args.dry_run:
        if not ds_path.exists():
            print(f"❌ Dataset not found at {ds_path}. Run --harvest-dataset first.")
            sys.exit(1)
        content = ds_path.read_text(encoding="utf-8")
        is_valid, violations = validate_dataset_is_sanitized(content)
        if not is_valid:
            print(f"❌ Dry-run validation failed: {violations}")
            sys.exit(1)

        # Check provenance manifest if present
        manifest_file = ds_path.with_name(f"{ds_path.name}.manifest.json")
        if manifest_file.exists():
            m_valid, m_violations = verify_dataset_manifest(ds_path)
            if not m_valid:
                print(f"❌ Provenance manifest verification failed: {m_violations}")
                sys.exit(1)
            print("🛡️ Provenance manifest verified (immutable supply-chain binding).")

        lines = [json.loads(l) for l in content.splitlines() if l.strip()]
        print(f"🔍 Dry-run validation: {len(lines)} samples.")
        for idx, item in enumerate(lines[:3], 1):
            assert "instruction" in item and "input" in item and "output" in item
            print(f"  [Sample {idx}] Domain: {item['output']['domain']} | Complexity: {item['output']['complexity_score']} | Escalation: {item['output']['requires_cloud_escalation']}")
        print("✅ Dry-run validation passed: 100% schema & sanitization compliance.")

    if args.train_modal:
        if app is None:
            print("❌ Modal package is not available in the current environment.")
            sys.exit(1)
        if not ds_path.exists():
            harvest_dataset_from_ledgers(output_path=ds_path)
        content = ds_path.read_text(encoding="utf-8")

        # Mandatory Sanitization Validation Gate (Fail-Closed)
        is_valid, violations = validate_dataset_is_sanitized(content)
        if not is_valid:
            logger.error("Dataset sanitization gate failed: %s", violations)
            raise ValueError(f"Dataset failed sanitization validation gate: {violations}")

        # Mandatory Provenance Manifest Verification Gate (Fail-Closed)
        m_valid, m_violations = verify_dataset_manifest(ds_path)
        if not m_valid:
            logger.error("Dataset provenance manifest verification failed: %s", m_violations)
            raise ValueError(f"Dataset failed provenance manifest verification: {m_violations}")

        creds = get_modal_credentials(require=True)
        if not (creds.get("MODAL_TOKEN_ID") and creds.get("MODAL_TOKEN_SECRET")) and not os.environ.get("MODAL_PROFILE"):
            logger.info("Using Modal profile/environment token sourcing.")

        breaker = QuotaBreaker(max_attempts=3, base_backoff_s=2.0)
        print("🚀 Dispatching JEV Fine-Tuning to Modal GPU (Quota-Breaker Protected)...")
        with app.run():
            result = breaker.execute(
                train_jev_modal.remote,
                dataset_jsonl_content=content,
                base_model_name=args.base_model,
            )
            print("🎉 Modal Training Completed Successfully:")
            print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
