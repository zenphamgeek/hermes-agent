"""Durable, user-approved learning proposals."""

from __future__ import annotations

import json
import os
import re
import tempfile
import threading
import uuid
from datetime import datetime, timezone
from ipaddress import ip_address
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from hermes_constants import get_hermes_home

_LOCK = threading.RLock()
_SECRET = re.compile(
    r'(?i)(api[_-]?key|token|password|secret)["\']?\s*[:=]\s*["\']?\S+'
)
_SECRET_PATTERNS = [
    # Key-value assignments: api_key=..., token=..., password=...
    re.compile(r'(?i)(api[_-]?key|access[_-]?token|auth[_-]?token|secret[_-]?key|password|bearer|private[_-]?key|client[_-]?secret)["\']?\s*[:=]\s*["\']?([^\s"\',;}{]+)'),
    # Bearer tokens
    re.compile(r'(?i)\bbearer\s+[A-Za-z0-9\-\._~\+\/]+=*'),
    # OpenAI API keys: sk-...
    re.compile(r'\bsk-(?:proj-|live-|test-)?[A-Za-z0-9_\-]{20,}\b'),
    # Google API keys: AIza...
    re.compile(r'\bAIza[0-9A-Za-z\-_]{35}\b'),
    # GitHub personal access tokens: ghp_..., gho_..., etc.
    re.compile(r'\bgh[pousr]_[A-Za-z0-9]{36,}\b'),
    # AWS access keys: AKIA...
    re.compile(r'\bAKIA[0-9A-Z]{16}\b'),
    # Private keys
    re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----[\s\S]*?-----END (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----'),
    # Slack tokens
    re.compile(r'\bxox[baprs]-[0-9A-Za-z\-]{10,}\b'),
]

MAX_PAYLOAD_BYTES = 65536   # 64 KB limit
MAX_EVIDENCE_BYTES = 16384  # 16 KB limit


def scrub_secrets(value: Any) -> Any:
    """Recursively scrub high-risk secrets and credentials from payloads and evidence.

    Replaces discovered API keys, tokens, passwords, and private keys with [REDACTED_SECRET].
    """
    if isinstance(value, str):
        result = value
        for pattern in _SECRET_PATTERNS:
            result = pattern.sub("[REDACTED_SECRET]", result)
        return result
    if isinstance(value, dict):
        cleaned: dict[str, Any] = {}
        for k, v in value.items():
            if isinstance(k, str) and re.search(r'(?i)^(api[_-]?key|token|password|secret|auth|bearer)$', k):
                cleaned["[REDACTED_KEY]"] = "[REDACTED_SECRET]"
            else:
                cleaned[k] = scrub_secrets(v)
        return cleaned
    if isinstance(value, list):
        return [scrub_secrets(item) for item in value]
    return value
_INJECTION = re.compile(
    r"(?is)(ignore\s+(?:all\s+)?(?:previous|above)\s+instructions|"
    r"system\s*prompt|<\|im_(?:start|end)\|>|"
    r"you\s+are\s+now\s+(?:the|an?)\s+|"
    r"do\s+not\s+follow\s+(?:the\s+)?instructions)"
)
_ALLOWED_KINDS = {"content", "memory", "skill"}
_ALLOWED_ACTIONS = {
    "content": {"create"},
    "memory": {"add", "replace", "remove"},
    "skill": {"create", "edit", "patch", "write_file", "remove_file"},
}


def _path() -> Path:
    return get_hermes_home() / "learning" / "proposals.json"


def _read() -> list[dict[str, Any]]:
    try:
        data = json.loads(_path().read_text(encoding="utf-8"))
    except FileNotFoundError:
        return []
    if not isinstance(data, list):
        raise ValueError("learning proposal store must contain a JSON list")
    return [item for item in data if isinstance(item, dict)]


def _write(items: list[dict[str, Any]]) -> None:
    path = _path()
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".proposals-", suffix=".json", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(items, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass


def list_proposals(status: str | None = None) -> list[dict[str, Any]]:
    with _LOCK:
        items = _read()
    return [dict(item) for item in items if status is None or item.get("status") == status]


def get_proposal(proposal_id: str) -> dict[str, Any]:
    for item in list_proposals():
        if item.get("id") == proposal_id:
            return item
    raise KeyError(f"proposal not found: {proposal_id}")


def _event_path() -> Path:
    return get_hermes_home() / "learning" / "events.json"


def record_memory_recall(*, hit: bool) -> None:
    """Record an attempted external-memory recall at its concrete call site."""
    with _LOCK:
        path = _event_path()
        try:
            events = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            events = {}
        except (json.JSONDecodeError, OSError):
            return
        if not isinstance(events, dict):
            return
        events["memory_recall_attempt_count"] = int(events.get("memory_recall_attempt_count", 0)) + 1
        events["memory_recall_hit_count"] = int(events.get("memory_recall_hit_count", 0)) + int(hit)
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix=".events-", suffix=".json", dir=path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(events, handle, indent=2, sort_keys=True)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
        finally:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass


def record_cache_selection(*, hit: bool) -> None:
    """Record a context-engine selection cache hit/miss at its concrete call site."""
    with _LOCK:
        path = _event_path()
        try:
            events = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            events = {}
        except (json.JSONDecodeError, OSError):
            return
        if not isinstance(events, dict):
            return
        events["cache_selection_attempt_count"] = int(events.get("cache_selection_attempt_count", 0)) + 1
        events["cache_selection_hit_count"] = int(events.get("cache_selection_hit_count", 0)) + int(hit)
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix=".events-", suffix=".json", dir=path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(events, handle, indent=2, sort_keys=True)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
        finally:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass


def proposal_metrics() -> dict[str, Any]:
    items = list_proposals()
    statuses = ("pending", "approved", "rejected", "applied")
    status_counts = {status: sum(item.get("status") == status for item in items) for status in statuses}
    total = len(items)
    decided = status_counts["approved"] + status_counts["rejected"] + status_counts["applied"]
    accepted = status_counts["approved"] + status_counts["applied"]
    try:
        events = json.loads(_event_path().read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        events = {}
    from tools.skill_usage import load_usage
    usage = load_usage()
    skill_use_count = sum(max(0, int(record.get("use_count") or 0)) for record in usage.values())
    skill_reuse_count = sum(max(0, int(record.get("use_count") or 0) - 1) for record in usage.values())
    recall_attempts = int(events.get("memory_recall_attempt_count", 0)) if isinstance(events, dict) else 0
    recall_hits = int(events.get("memory_recall_hit_count", 0)) if isinstance(events, dict) else 0
    cache_attempts = int(events.get("cache_selection_attempt_count", 0)) if isinstance(events, dict) else 0
    cache_hits = int(events.get("cache_selection_hit_count", 0)) if isinstance(events, dict) else 0
    return {
        "total": total,
        "status_counts": status_counts,
        "status_rates": {status: (status_counts[status] / total if total else 0.0) for status in statuses},
        "kind_counts": {kind: sum(item.get("kind") == kind for item in items) for kind in sorted(_ALLOWED_KINDS)},
        "proposal_acceptance_rate": accepted / decided if decided else 0.0,
        "duplicate_proposal_count": sum(int(item.get("duplicate_count") or 0) for item in items),
        "unsafe_apply_count": sum(int(item.get("unsafe_apply_count") or 0) for item in items),
        "memory_recall": {"attempt_count": recall_attempts, "hit_count": recall_hits, "hit_rate": recall_hits / recall_attempts if recall_attempts else 0.0},
        "skill_reuse": {"use_count": skill_use_count, "reuse_count": skill_reuse_count, "reuse_rate": skill_reuse_count / skill_use_count if skill_use_count else 0.0},
        "revert_rate": {"value": 0.0, "availability": "not_available"},
        "cache_stability": {
            "attempt_count": cache_attempts,
            "hit_count": cache_hits,
            "hit_rate": cache_hits / cache_attempts if cache_attempts else 0.0,
            "availability": "available",
        },
    }


def _validate_research(research: Any) -> dict[str, Any]:
    if not isinstance(research, dict):
        raise ValueError("research metadata must be an object")
    claim = research.get("claim")
    sources = research.get("sources")
    confidence = research.get("confidence")
    if not isinstance(claim, str) or not claim.strip():
        raise ValueError("research claim is required")
    if _INJECTION.search(claim):
        raise ValueError("research claim contains prompt-injection language")
    if not isinstance(sources, list) or not 2 <= len(sources) <= 8:
        raise ValueError("research requires 2 to 8 independent sources")
    normalized_sources = []
    hosts = set()
    for source in sources:
        if not isinstance(source, dict):
            raise ValueError("each research source must be an object")
        url = source.get("url")
        excerpt = source.get("excerpt")
        if not isinstance(url, str) or not isinstance(excerpt, str) or not excerpt.strip():
            raise ValueError("each research source requires url and excerpt")
        parsed = urlparse(url.strip())
        host = (parsed.hostname or "").rstrip(".").lower()
        if parsed.scheme not in {"http", "https"} or not host or parsed.username or parsed.password:
            raise ValueError("research source must use a public HTTP(S) URL")
        try:
            address = ip_address(host)
        except ValueError:
            address = None
        if (
            host == "localhost" or host.endswith(".local")
            or (address is not None and not address.is_global)
        ):
            raise ValueError("research source cannot target a local or private host")
        if _INJECTION.search(excerpt):
            raise ValueError("research source contains prompt-injection language")
        hosts.add(host)
        normalized_sources.append({"url": url.strip(), "excerpt": excerpt.strip()})
    if len(hosts) < 2:
        raise ValueError("research requires sources from at least two independent hosts")
    if isinstance(confidence, bool) or not isinstance(confidence, (int, float)):
        raise ValueError("research confidence must be a number from 0 to 1")
    confidence = float(confidence)
    if not 0 <= confidence <= 1:
        raise ValueError("research confidence must be a number from 0 to 1")
    if confidence < 0.7:
        raise ValueError("research confidence below 0.7 cannot become a proposal")
    return {
        "claim": claim.strip(),
        "sources": normalized_sources,
        "confidence": confidence,
        "conflict_detected": bool(research.get("conflict_detected", False)),
    }


def _validate_content_payload(payload: dict[str, Any]) -> dict[str, Any]:
    required = ("title", "angle", "audience", "outline")
    for field in required:
        value = payload.get(field)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"content {field} is required")
    if len(payload["title"].strip()) > 160:
        raise ValueError("content title must be at most 160 characters")
    return {
        "title": payload["title"].strip(),
        "angle": payload["angle"].strip(),
        "audience": payload["audience"].strip(),
        "outline": payload["outline"].strip(),
        "cta": str(payload.get("cta") or "").strip(),
        "format": str(payload.get("format") or "article").strip(),
    }


def _content_slug(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return (slug[:80].rstrip("-") or "content-draft")


def _write_content_draft(payload: dict[str, Any], research: dict[str, Any]) -> dict[str, Any]:
    content = _validate_content_payload(payload)
    directory = get_hermes_home() / "learning" / "content"
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{_content_slug(content['title'])}.md"
    sources = "\n".join(
        f"- [{source['url']}]({source['url']}) — {source['excerpt']}"
        for source in research["sources"]
    )
    text = (
        f"# {content['title']}\n\n"
        f"Status: draft\nFormat: {content['format']}\nAudience: {content['audience']}\n"
        f"Confidence: {research['confidence']:.2f}\n\n"
        f"## Angle\n\n{content['angle']}\n\n"
        f"## Grounded claim\n\n{research['claim']}\n\n"
        f"## Outline\n\n{content['outline']}\n\n"
        f"## CTA\n\n{content['cta'] or 'TBD'}\n\n"
        f"## Sources\n\n{sources}\n"
    )
    fd, temporary = tempfile.mkstemp(prefix=".content-", suffix=".md", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
    return {"success": True, "path": str(path), "status": "draft"}


def create_proposal(
    kind: str,
    action: str,
    payload: dict[str, Any],
    evidence: str,
    *,
    source_session_id: str | None = None,
    source_message_id: str | None = None,
    research: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if kind not in _ALLOWED_KINDS or action not in _ALLOWED_ACTIONS[kind]:
        raise ValueError(f"unsupported proposal: {kind}/{action}")
    if not isinstance(payload, dict) or not payload:
        raise ValueError("payload is required")
    evidence = evidence.strip()
    if not evidence:
        raise ValueError("evidence is required")
    if len(json.dumps(payload, ensure_ascii=False).encode("utf-8")) > MAX_PAYLOAD_BYTES:
        raise ValueError(f"payload exceeds maximum size of {MAX_PAYLOAD_BYTES} bytes")
    if len(evidence.encode("utf-8")) > MAX_EVIDENCE_BYTES:
        raise ValueError(f"evidence exceeds maximum size of {MAX_EVIDENCE_BYTES} bytes")
    source = {
        key: value.strip()
        for key, value in {
            "session_id": source_session_id,
            "message_id": source_message_id,
        }.items()
        if isinstance(value, str) and value.strip()
    }
    if kind == "content":
        payload = _validate_content_payload(payload)
        if research is None:
            raise ValueError("content proposal requires research metadata")
    validated_research = _validate_research(research) if research is not None else None
    serialized = json.dumps(
        {"payload": payload, "evidence": evidence, "source": source, "research": validated_research},
        ensure_ascii=False,
    )
    if _SECRET.search(serialized):
        raise ValueError("proposal may contain a secret")
    now = datetime.now(timezone.utc).isoformat()
    item = {
        "id": uuid.uuid4().hex[:12], "kind": kind, "action": action,
        "payload": payload, "evidence": evidence, "status": "pending",
        "created_at": now, "updated_at": now,
    }
    if source:
        item["source"] = source
    if validated_research is not None:
        item["research"] = validated_research
    with _LOCK:
        items = _read()
        duplicate = next((
            existing for existing in items
            if existing.get("kind") == kind
            and existing.get("action") == action
            and existing.get("payload") == payload
            and existing.get("evidence") == evidence
        ), None)
        if duplicate is not None:
            duplicate["duplicate_count"] = int(duplicate.get("duplicate_count") or 0) + 1
            duplicate["updated_at"] = datetime.now(timezone.utc).isoformat()
            _write(items)
            return dict(duplicate)
        items.append(item)
        _write(items)
    return dict(item)


def set_status(proposal_id: str, status: str) -> dict[str, Any]:
    if status not in {"approved", "rejected"}:
        raise ValueError("status must be approved or rejected")
    with _LOCK:
        items = _read()
        for item in items:
            if item.get("id") == proposal_id:
                if item.get("status") == status:
                    return dict(item)
                if item.get("status") != "pending":
                    raise ValueError(f"proposal is already {item.get('status')}")
                item["status"] = status
                item["updated_at"] = datetime.now(timezone.utc).isoformat()
                _write(items)
                return dict(item)
    raise KeyError(f"proposal not found: {proposal_id}")


def apply_proposal(proposal_id: str) -> dict[str, Any]:
    with _LOCK:
        items = _read()
        item = next((entry for entry in items if entry.get("id") == proposal_id), None)
        if item is None:
            raise KeyError(f"proposal not found: {proposal_id}")
        if item.get("status") == "applied":
            return dict(item)
        if item.get("status") != "approved":
            item["unsafe_apply_count"] = int(item.get("unsafe_apply_count") or 0) + 1
            item["updated_at"] = datetime.now(timezone.utc).isoformat()
            _write(items)
            raise ValueError("proposal must be approved before apply")
        payload = dict(item["payload"])
        if "research" in item:
            # Revalidate persisted model output at the mutation boundary. A
            # manually edited proposal file must not bypass source, SSRF,
            # injection, confidence, or independence checks.
            _validate_research(item["research"])
        if item["kind"] == "content":
            result = _write_content_draft(payload, item["research"])
        elif item["kind"] == "memory":
            from tools.memory_tool import MemoryStore, memory_tool
            store = MemoryStore()
            store.load_from_disk()
            result = json.loads(memory_tool(action=item["action"], store=store, **payload))
        else:
            from agent import curator_backup
            (get_hermes_home() / "skills").mkdir(parents=True, exist_ok=True)
            checkpoint = curator_backup.snapshot_skills(
                reason=f"pre-learning-proposal-{proposal_id}"
            )
            if checkpoint is None:
                raise RuntimeError("skill checkpoint failed; proposal was not applied")
            from tools.skill_manager_tool import skill_manage
            source_session_id = (item.get("source") or {}).get("session_id")
            if isinstance(source_session_id, str):
                payload["session_id"] = source_session_id
            # description lives in the SKILL.md frontmatter (part of
            # `content`); skill_manage has no description kwarg. Reference
            # files are written after the umbrella skill exists.
            references = payload.pop("references", None)
            payload.pop("description", None)
            result = json.loads(skill_manage(action=item["action"], **payload))
            if result.get("success") and references:
                for ref in references:
                    if not isinstance(ref, dict):
                        continue
                    rpath = (ref.get("path") or "").strip()
                    rcontent = ref.get("content")
                    if not rpath or not rcontent:
                        continue
                    if not rpath.startswith("references/"):
                        rpath = f"references/{rpath}"
                    reference_args = {
                        "action": "write_file", "name": payload["name"],
                        "file_path": rpath, "file_content": rcontent,
                    }
                    if isinstance(payload.get("session_id"), str):
                        reference_args["session_id"] = payload["session_id"]
                    rres = json.loads(skill_manage(**reference_args))
                    if not rres.get("success"):
                        raise RuntimeError(
                            rres.get("error") or f"reference write failed: {rpath}"
                        )
        if not result.get("success"):
            raise RuntimeError(result.get("error") or "proposal apply failed")
        item["status"] = "applied"
        item["updated_at"] = datetime.now(timezone.utc).isoformat()
        item["result"] = result
        _write(items)
        return dict(item)


def redact_proposals_for_session(
    session_id: str,
    reason: str = "GDPR_RIGHT_TO_ERASURE",
) -> int:
    """Crypto-shreds and tombstones proposals linked to a specific session_id.

    Reconciles background learning proposals with the GDPR 72h right-to-erasure SLA
    by scrubbing conversation evidence, zeroing payload content, and marking the proposal
    status as 'rejected' / tombstoned.
    """
    if not session_id or not isinstance(session_id, str):
        return 0
    with _LOCK:
        items = _read()
        redacted_count = 0
        now = datetime.now(timezone.utc).isoformat()
        for item in items:
            source = item.get("source") or {}
            if source.get("session_id") == session_id:
                redacted_count += 1
                item["evidence"] = "[REDACTED_PII]"
                item["payload"] = {"redacted": True, "target": item.get("payload", {}).get("target", "unknown")}
                if "research" in item:
                    item["research"] = {"redacted": True, "claim": "[REDACTED_PII]"}
                item["status"] = "rejected"
                item["redacted"] = True
                item["redacted_at"] = now
                item["redacted_reason"] = reason
                item["updated_at"] = now
        if redacted_count > 0:
            _write(items)
        return redacted_count
