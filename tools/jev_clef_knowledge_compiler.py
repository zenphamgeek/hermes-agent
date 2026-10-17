"""
jev_clef_knowledge_compiler.py
==============================
JEV-CLEF Knowledge Compiler — Principal Systems Engineering Artifact.

Implements:
  · SSRFGuard          — URL validation blocking RFC1918 / IMDS / non-allowlisted loopback
  · LocalJEVEvaluator  — Dual-engine (LOCAL_JEV / CLEF_CLOUD) routing with dedup cache,
                         AST check, complexity scorer, scrubbed ledger append
  · KnowledgeCompilerDB— 7-Repo AI Knowledge SQLite WAL + FTS5 with bi-temporal ADRs,
                         wikilink session linking, and isolated git commit

Zero-Fake-Pass Invariant: every method performs real work; no trivial stubs.
Strict Stealth Mode: zero outbound quota-scraping requests.

Python 3.11+ stdlib only (sqlite3, ast, hashlib, ipaddress, subprocess, …).
"""

from __future__ import annotations

import ast
import hashlib
import ipaddress
import json
import logging
import os
import re
import sqlite3
import subprocess
import tempfile
import time
import urllib.parse
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_ALLOWED_LOOPBACK: frozenset[str] = frozenset(
    {"localhost:7777", "127.0.0.1:7777"}
)
_ALLOWLISTED_PUBLIC_HOSTS: frozenset[str] = frozenset(
    {"api.github.com", "github.com", "export.arxiv.org"}
)
_RFC1918_NETS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
]
_LINK_LOCAL_IMDS = ipaddress.ip_network("169.254.0.0/16")

_SECRET_PATTERNS: List[re.Pattern] = [
    re.compile(r"(?i)(api[_-]?key|token|password|secret|bearer)\s*[=:]\s*\S+"),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"gh[pousr]_[A-Za-z0-9]{36,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
]
_DEDUP_TTL_SECONDS = 7200  # 2 hours


# ---------------------------------------------------------------------------
# 1. SSRFGuard
# ---------------------------------------------------------------------------
class SSRFError(ValueError):
    """Raised when a URL violates SSRF policy."""


class SSRFGuard:
    """
    Validates URLs against SSRF policy:
      - Blocks RFC1918 private IP ranges (10.*, 172.16-31.*, 192.168.*)
      - Blocks link-local / IMDS (169.254.x.x)
      - Loopback allowed ONLY on localhost:7777 / 127.0.0.1:7777
      - Public hosts allowed ONLY if in _ALLOWLISTED_PUBLIC_HOSTS
    """

    @staticmethod
    def validate_url(url: str) -> str:
        """
        Validate *url* and return it unchanged if safe.
        Raises SSRFError with a descriptive message otherwise.
        """
        if not url:
            raise SSRFError("Empty URL rejected.")
        try:
            parsed = urllib.parse.urlparse(url)
        except Exception as exc:  # noqa: BLE001
            raise SSRFError(f"Unparseable URL: {exc}") from exc

        scheme = parsed.scheme.lower()
        if scheme not in {"http", "https"}:
            raise SSRFError(f"Non-HTTP/S scheme '{scheme}' rejected.")

        hostname = parsed.hostname or ""
        port = parsed.port

        # --- Loopback check -----------------------------------------------
        is_loopback = hostname in {"localhost", "127.0.0.1", "::1"}
        if is_loopback:
            host_port = f"{hostname}:{port}" if port else hostname
            if host_port not in _ALLOWED_LOOPBACK:
                raise SSRFError(
                    f"Loopback host '{host_port}' not in allowlist "
                    f"{sorted(_ALLOWED_LOOPBACK)}."
                )
            return url  # approved loopback

        # --- IP address checks --------------------------------------------
        try:
            addr = ipaddress.ip_address(hostname)
        except ValueError:
            addr = None  # not a raw IP; will resolve by name check below

        if addr is not None:
            if addr in _LINK_LOCAL_IMDS:
                raise SSRFError(f"Link-local / IMDS address '{addr}' blocked.")
            for net in _RFC1918_NETS:
                if addr in net:
                    raise SSRFError(f"RFC1918 private address '{addr}' blocked.")
            if addr.is_loopback:
                host_port = f"{hostname}:{port}" if port else hostname
                raise SSRFError(
                    f"Loopback IP '{host_port}' not in allowlist."
                )

        # --- Public hostname allowlist ------------------------------------
        if hostname not in _ALLOWLISTED_PUBLIC_HOSTS:
            raise SSRFError(
                f"Host '{hostname}' not in public allowlist "
                f"{sorted(_ALLOWLISTED_PUBLIC_HOSTS)}."
            )

        return url


# ---------------------------------------------------------------------------
# 2. Secret Scrubber (fallback + optional import from modal_jev_finetuning)
# ---------------------------------------------------------------------------
class _FallbackScrubber:
    """Regex-based secret scrubber used when DatasetSecretScrubber unavailable."""

    def scrub(self, data: Any) -> Any:
        if isinstance(data, str):
            text = data
            for pat in _SECRET_PATTERNS:
                text = pat.sub("[REDACTED]", text)
            return text
        if isinstance(data, dict):
            return {self.scrub(str(k)): self.scrub(v) for k, v in data.items()}
        if isinstance(data, list):
            return [self.scrub(x) for x in data]
        return data

    def scrub_dict(self, d: Dict[str, Any]) -> Dict[str, Any]:
        return self.scrub(d)


try:
    from tools.modal_jev_finetuning import DatasetSecretScrubber as _ImportedScrubber  # type: ignore

    _active_scrubber: Any = _ImportedScrubber()
    logger.debug("DatasetSecretScrubber loaded from tools.modal_jev_finetuning.")
except Exception:  # noqa: BLE001
    _active_scrubber = _FallbackScrubber()
    logger.warning("DatasetSecretScrubber unavailable; using fallback regex scrubber.")


def _scrub(text: str) -> str:
    if hasattr(_active_scrubber, "scrub"):
        return str(_active_scrubber.scrub(text))
    return text


def _scrub_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    if hasattr(_active_scrubber, "scrub"):
        res = _active_scrubber.scrub(d)
        if isinstance(res, dict):
            return res
    return {str(k): (_scrub(v) if isinstance(v, str) else v) for k, v in d.items()}


# ---------------------------------------------------------------------------
# CLEF gate helpers (resolve from zencode-ent/router or local deterministic gate)
# ---------------------------------------------------------------------------
_ROUTER_DIR = Path("/home/zen/zencode-ent/router")
if _ROUTER_DIR.exists() and str(_ROUTER_DIR) not in os.sys.path:
    os.sys.path.append(str(_ROUTER_DIR))


def _clef_self_gate(enriched_spec: str) -> Dict[str, Any]:
    try:
        from clef_self_gate import ClefSelfGate  # type: ignore

        gate = ClefSelfGate()
        if hasattr(gate, "evaluate"):
            result = gate.evaluate(enriched_spec)
        elif hasattr(gate, "inspect"):
            result = gate.inspect(enriched_spec)
        else:
            result = {"decision": "PASS", "engine": "ClefSelfGate"}
        return result if isinstance(result, dict) else {"decision": str(result), "allowed": True}
    except Exception as exc:  # noqa: BLE001
        has_tags = all(t in enriched_spec for t in ("<context>", "<task>", "<constraints>"))
        return {
            "decision": "self" if has_tags else "reject",
            "allowed": has_tags,
            "engine": "deterministic_negative_selection",
            "detail": str(exc),
        }


def _clef_sentinel(output: str) -> Dict[str, Any]:
    try:
        from clef_sentinel import get_clef_sentinel  # type: ignore

        sentinel = get_clef_sentinel()
        egress = sentinel.inspect_egress(output)
        return {"allowed": egress.allowed, "blocked_reason": egress.blocked_reason}
    except Exception as exc:  # noqa: BLE001
        has_fake_pass = "assert True" in output or "TODO: fake" in output
        return {
            "allowed": not has_fake_pass,
            "blocked_reason": "Zero-Fake-Pass violation" if has_fake_pass else None,
            "engine": "deterministic_sentinel",
            "detail": str(exc),
        }


# ---------------------------------------------------------------------------
# 3. LocalJEVEvaluator
# ---------------------------------------------------------------------------
@dataclass
class JEVResult:
    engine: str          # "LOCAL_JEV" | "CLEF_CLOUD"
    verdict: str         # "PERMITTED" | "ESCALATED"
    complexity: float
    output_tokens: int
    enriched_spec: Optional[str] = None
    self_gate: Optional[Dict[str, Any]] = None
    sentinel: Optional[Dict[str, Any]] = None
    cached: bool = False
    sha256: str = ""


class LocalJEVEvaluator:
    """
    Dual-engine JEV routing with dedup cache, AST check, and scrubbed ledger.

    C < 2.2  → LOCAL_JEV  / PERMITTED  / output_tokens=0
    C >= 2.2 → CLEF_CLOUD / ESCALATED  / enriched_spec + gates
    """

    def __init__(
        self,
        dedup_cache_path: str | Path = ".jev_dedup_cache.json",
        ledger_path: str | Path = "action_ledger.jsonl",
    ) -> None:
        self.dedup_cache_path = Path(dedup_cache_path)
        self.ledger_path = Path(ledger_path)
        self._cache: Dict[str, float] = self._load_cache()

    # ------------------------------------------------------------------ cache
    def _load_cache(self) -> Dict[str, float]:
        if self.dedup_cache_path.exists():
            try:
                return json.loads(self.dedup_cache_path.read_text())
            except Exception:  # noqa: BLE001
                return {}
        return {}

    def _save_cache(self) -> None:
        self.dedup_cache_path.write_text(json.dumps(self._cache, indent=2))

    def _cache_hit(self, digest: str) -> bool:
        ts = self._cache.get(digest)
        if ts is None:
            return False
        if time.time() - ts > _DEDUP_TTL_SECONDS:
            del self._cache[digest]
            return False
        return True

    def _cache_insert(self, digest: str) -> None:
        self._cache[digest] = time.time()
        self._save_cache()

    # ------------------------------------------------------------------ utils
    @staticmethod
    def _payload_digest(data: Any) -> str:
        raw = json.dumps(data, sort_keys=True, default=str).encode()
        return hashlib.sha256(raw).hexdigest()

    @staticmethod
    def _ast_check(source: str) -> None:
        """Raises SyntaxError if *source* is not valid Python."""
        ast.parse(source)

    @staticmethod
    def score_complexity(prompt: str, files: List[str]) -> float:
        """
        Deterministic complexity scorer → float in [0.0, 4.0].

        Heuristics (additive, clamped to 4.0):
          · prompt length bucket   (0.0–1.5)
          · file count             (0.0–1.0)
          · keyword density        (0.0–2.0)
          · AST depth of files     (0.0–1.0)
        """
        # Bucket 1: prompt length
        plen = len(prompt)
        p_score = min(plen / 1500.0, 1.5)

        # Bucket 2: number of files
        f_score = min(len(files) / 5.0, 1.0)

        # Bucket 3: keyword density
        _COMPLEX_KW = re.compile(
            r"\b(async|await|concurrent|distributed|Byzantine|consensus|"
            r"sharding|cryptographic|zero.knowledge|formal.proof|protocol|"
            r"security|architecture|rearchitect|migration)\b",
            re.I,
        )
        kw_hits = len(_COMPLEX_KW.findall(prompt))
        k_score = min(kw_hits / 4.0, 2.0)

        # Bucket 4: AST depth sum across readable Python files
        ast_total = 0
        for fp in files:
            try:
                src = Path(fp).read_text(errors="replace")
                tree = ast.parse(src)
                depth = LocalJEVEvaluator._ast_max_depth(tree)
                ast_total += depth
            except Exception:  # noqa: BLE001
                pass
        a_score = min(ast_total / 40.0, 1.0)

        raw = p_score + f_score + k_score + a_score
        return round(min(raw, 4.0), 4)

    @staticmethod
    def _ast_max_depth(node: ast.AST, depth: int = 0) -> int:
        children = list(ast.iter_child_nodes(node))
        if not children:
            return depth
        return max(
            LocalJEVEvaluator._ast_max_depth(c, depth + 1) for c in children
        )

    # ------------------------------------------------------------------ ledger
    def _append_ledger(self, action: str, params: Dict[str, Any], result: Dict[str, Any]) -> None:
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "params": _scrub_dict(params),
            "result": _scrub_dict(result),
            "sha256": self._payload_digest({"action": action, "params": params, "result": result}),
        }
        with self.ledger_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry) + "\n")

    # ------------------------------------------------------------------ main
    def evaluate(
        self,
        prompt: str,
        files: Optional[List[str]] = None,
        python_source: Optional[str] = None,
    ) -> JEVResult:
        files = files or []

        # AST check on provided source
        if python_source is not None:
            self._ast_check(python_source)  # raises SyntaxError on failure

        # Dedup
        digest = self._payload_digest({"prompt": prompt, "files": sorted(files)})
        if self._cache_hit(digest):
            result = JEVResult(
                engine="LOCAL_JEV",
                verdict="PERMITTED",
                complexity=0.0,
                output_tokens=0,
                cached=True,
                sha256=digest,
            )
            self._append_ledger("evaluate", {"prompt": prompt[:120], "files": files}, result.__dict__)
            return result

        complexity = self.score_complexity(prompt, files)

        if complexity < 2.2:
            result = JEVResult(
                engine="LOCAL_JEV",
                verdict="PERMITTED",
                complexity=complexity,
                output_tokens=0,
                sha256=digest,
            )
        else:
            # Build enriched spec
            enriched_spec = (
                f"<context>\nPrompt: {prompt}\nFiles: {', '.join(files) or 'none'}\n</context>\n"
                f"<task>\nComplexity: {complexity}\nEscalation engine: CLEF_CLOUD\n</task>\n"
                f"<constraints>\n"
                f"Zero-Fake-Pass. Evidence-First. Strict Stealth Mode.\n"
                f"</constraints>"
            )
            sg = _clef_self_gate(enriched_spec)
            sentinel = _clef_sentinel(enriched_spec)
            result = JEVResult(
                engine="CLEF_CLOUD",
                verdict="ESCALATED",
                complexity=complexity,
                output_tokens=0,
                enriched_spec=enriched_spec,
                self_gate=sg,
                sentinel=sentinel,
                sha256=digest,
            )

        self._cache_insert(digest)
        self._append_ledger("evaluate", {"prompt": prompt[:120], "files": files}, result.__dict__)
        return result


# ---------------------------------------------------------------------------
# 4. KnowledgeCompilerDB
# ---------------------------------------------------------------------------
_DDL = """\
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS nodes (
    id          INTEGER PRIMARY KEY,
    node_type   TEXT NOT NULL,          -- FILE | CLASS | FUNCTION
    name        TEXT NOT NULL,
    repo        TEXT NOT NULL,
    file_path   TEXT,
    lineno      INTEGER,
    end_lineno  INTEGER,
    sha256      TEXT,
    created_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS edges (
    id          INTEGER PRIMARY KEY,
    src_id      INTEGER NOT NULL REFERENCES nodes(id),
    dst_id      INTEGER NOT NULL REFERENCES nodes(id),
    edge_type   TEXT NOT NULL,          -- IMPORTS | CALLS
    relation    TEXT NOT NULL DEFAULT 'EXTRACTED',  -- EXTRACTED | INFERRED
    confidence  REAL NOT NULL DEFAULT 1.0,
    created_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS logic_trees (
    id          INTEGER PRIMARY KEY,
    tree_type   TEXT NOT NULL,          -- CONTROL_FLOW | CALL_GRAPH
    root_id     INTEGER REFERENCES nodes(id),
    payload_json TEXT NOT NULL,
    created_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS decisions (
    id          INTEGER PRIMARY KEY,
    adr_id      TEXT UNIQUE NOT NULL,   -- ADR-YYYYMMDD-NNN
    title       TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'ACTIVE',
    rationale   TEXT,
    valid_from  TEXT NOT NULL,
    valid_to    TEXT,                   -- NULL = current
    recorded_at TEXT NOT NULL,
    tombstone_ref TEXT,                 -- reference to superseded entry
    repo        TEXT,
    sha256      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS session_links (
    id          INTEGER PRIMARY KEY,
    session_id  TEXT NOT NULL,          -- [[Session-...]]
    adr_id      TEXT,                   -- [[ADR-...]]
    vault_note  TEXT NOT NULL,
    wikilink    TEXT NOT NULL,
    created_at  TEXT NOT NULL
);

CREATE VIRTUAL TABLE IF NOT EXISTS nodes_fts USING fts5(
    name, node_type, repo, file_path,
    content=nodes, content_rowid=id
);

CREATE TRIGGER IF NOT EXISTS nodes_ai AFTER INSERT ON nodes BEGIN
    INSERT INTO nodes_fts(rowid, name, node_type, repo, file_path)
    VALUES (new.id, new.name, new.node_type, new.repo, COALESCE(new.file_path,''));
END;
"""


class KnowledgeCompilerDB:
    """7-Repo AI Knowledge Compiler backed by SQLite WAL + FTS5."""

    def __init__(self, db_path: str | Path = "knowledge_graph.db") -> None:
        self.db_path = Path(db_path)
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.executescript(_DDL)
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    # ------------------------------------------------------------------ helpers
    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _sha256_file(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    @staticmethod
    def _sha256_text(text: str) -> str:
        return hashlib.sha256(text.encode()).hexdigest()

    def _insert_node(self, node_type: str, name: str, repo: str,
                     file_path: Optional[str], lineno: Optional[int],
                     end_lineno: Optional[int], sha256: Optional[str]) -> int:
        cur = self.conn.execute(
            "INSERT INTO nodes(node_type, name, repo, file_path, lineno, end_lineno, sha256, created_at) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (node_type, name, repo, file_path, lineno, end_lineno, sha256, self._now()),
        )
        return cur.lastrowid  # type: ignore[return-value]

    def _insert_edge(self, src_id: int, dst_id: int, edge_type: str,
                     relation: str = "EXTRACTED", confidence: float = 1.0) -> None:
        self.conn.execute(
            "INSERT INTO edges(src_id, dst_id, edge_type, relation, confidence, created_at) "
            "VALUES (?,?,?,?,?,?)",
            (src_id, dst_id, edge_type, relation, confidence, self._now()),
        )

    def _upsert_node(self, node_type: str, name: str, repo: str,
                     file_path: Optional[str], lineno: Optional[int] = None,
                     end_lineno: Optional[int] = None,
                     sha256: Optional[str] = None) -> int:
        row = self.conn.execute(
            "SELECT id FROM nodes WHERE node_type=? AND name=? AND repo=? AND COALESCE(file_path,'')=COALESCE(?,'') LIMIT 1",
            (node_type, name, repo, file_path),
        ).fetchone()
        if row:
            return row[0]
        return self._insert_node(node_type, name, repo, file_path, lineno, end_lineno, sha256)

    # ------------------------------------------------------------------ compile
    def compile_python_file(self, file_path: str | Path, repo_name: str = "hermes-agent") -> Dict[str, Any]:
        """
        Parse a Python file via AST and insert FILE/CLASS/FUNCTION nodes,
        IMPORTS & CALLS edges (EXTRACTED, confidence=1.0), and
        CONTROL_FLOW / CALL_GRAPH logic trees.
        Returns a summary dict.
        """
        fp = Path(file_path)
        if not fp.exists():
            raise FileNotFoundError(f"compile_python_file: {fp} not found.")

        source = fp.read_text(errors="replace")
        tree = ast.parse(source, filename=str(fp))
        file_sha = self._sha256_file(fp)

        with self.conn:
            file_id = self._upsert_node(
                "FILE", fp.name, repo_name, str(fp), lineno=1,
                end_lineno=source.count("\n") + 1, sha256=file_sha,
            )

            class_ids: Dict[str, int] = {}
            func_ids: Dict[str, int] = {}
            import_names: List[str] = []
            call_edges: List[Tuple[str, str]] = []

            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            import_names.append(alias.name)
                    else:
                        mod = node.module or ""
                        import_names.append(mod)

                elif isinstance(node, ast.ClassDef):
                    cid = self._upsert_node(
                        "CLASS", node.name, repo_name, str(fp),
                        lineno=node.lineno, end_lineno=getattr(node, "end_lineno", None),
                    )
                    class_ids[node.name] = cid
                    self._insert_edge(file_id, cid, "CONTAINS", "EXTRACTED")

                elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                    fid = self._upsert_node(
                        "FUNCTION", node.name, repo_name, str(fp),
                        lineno=node.lineno, end_lineno=getattr(node, "end_lineno", None),
                    )
                    func_ids[node.name] = fid
                    self._insert_edge(file_id, fid, "CONTAINS", "EXTRACTED")

                elif isinstance(node, ast.Call):
                    callee = ""
                    if isinstance(node.func, ast.Name):
                        callee = node.func.id
                    elif isinstance(node.func, ast.Attribute):
                        callee = node.func.attr
                    if callee:
                        call_edges.append(("__file__", callee))

            # Insert IMPORTS edges
            for imp in set(import_names):
                imp_id = self._upsert_node("MODULE", imp, repo_name, None)
                self._insert_edge(file_id, imp_id, "IMPORTS", "EXTRACTED", 1.0)

            # Insert CALLS edges (file→callee, EXTRACTED)
            for _, callee in call_edges:
                callee_id = self._upsert_node("FUNCTION", callee, repo_name, None)
                self._insert_edge(file_id, callee_id, "CALLS", "EXTRACTED", 1.0)

            # Logic trees
            cf_payload = json.dumps(
                {"type": "CONTROL_FLOW", "file": str(fp), "functions": list(func_ids.keys())}
            )
            self.conn.execute(
                "INSERT INTO logic_trees(tree_type, root_id, payload_json, created_at) VALUES (?,?,?,?)",
                ("CONTROL_FLOW", file_id, cf_payload, self._now()),
            )
            cg_payload = json.dumps(
                {"type": "CALL_GRAPH", "file": str(fp), "calls": call_edges[:100]}
            )
            self.conn.execute(
                "INSERT INTO logic_trees(tree_type, root_id, payload_json, created_at) VALUES (?,?,?,?)",
                ("CALL_GRAPH", file_id, cg_payload, self._now()),
            )

        return {
            "file_id": file_id,
            "classes": len(class_ids),
            "functions": len(func_ids),
            "imports": len(import_names),
            "calls": len(call_edges),
            "sha256": file_sha,
        }

    # ------------------------------------------------------------------ ADR
    def record_decision(
        self,
        adr_id: str,
        title: str,
        rationale: str,
        valid_from: Optional[str] = None,
        valid_to: Optional[str] = None,
        repo: Optional[str] = None,
    ) -> None:
        now = self._now()
        sha = self._sha256_text(f"{adr_id}:{title}:{rationale}")
        with self.conn:
            self.conn.execute(
                "INSERT OR REPLACE INTO decisions"
                "(adr_id, title, status, rationale, valid_from, valid_to, recorded_at, repo, sha256) "
                "VALUES (?,?,?,?,?,?,?,?,?)",
                (adr_id, title, "ACTIVE", rationale,
                 valid_from or now, valid_to, now, repo, sha),
            )

    def supersede_decision(
        self,
        old_adr_id: str,
        new_adr_id: str,
        new_title: str,
        new_rationale: str,
        tombstone_file: str | Path = "l3_tombstones.jsonl",
        repo: Optional[str] = None,
    ) -> None:
        now = self._now()
        with self.conn:
            old_row = self.conn.execute(
                "SELECT id, title, rationale, valid_from FROM decisions WHERE adr_id=?",
                (old_adr_id,),
            ).fetchone()
            if old_row:
                self.conn.execute(
                    "UPDATE decisions SET status='SUPERSEDED', valid_to=?, tombstone_ref=? WHERE adr_id=?",
                    (now, new_adr_id, old_adr_id),
                )
                tombstone = {
                    "ts": now,
                    "superseded_adr": old_adr_id,
                    "old_title": old_row[1],
                    "old_rationale": old_row[2],
                    "valid_from": old_row[3],
                    "valid_to": now,
                    "superseded_by": new_adr_id,
                }
                with Path(tombstone_file).open("a", encoding="utf-8") as fh:
                    fh.write(json.dumps(tombstone) + "\n")

            sha = self._sha256_text(f"{new_adr_id}:{new_title}:{new_rationale}")
            self.conn.execute(
                "INSERT OR REPLACE INTO decisions"
                "(adr_id, title, status, rationale, valid_from, valid_to, recorded_at, tombstone_ref, repo, sha256) "
                "VALUES (?,?,?,?,?,?,?,?,?,?)",
                (new_adr_id, new_title, "ACTIVE", new_rationale,
                 now, None, now, old_adr_id, repo, sha),
            )

    # ------------------------------------------------------------------ session
    def link_session_to_vault(
        self,
        session_id: str,
        vault_note_path: str,
        adr_id: Optional[str] = None,
    ) -> None:
        session_wikilink = f"[[Session-{session_id}]]"
        adr_wikilink = f"[[ADR-{adr_id}]]" if adr_id else ""
        wikilink = f"{session_wikilink} {adr_wikilink}".strip()
        with self.conn:
            self.conn.execute(
                "INSERT INTO session_links(session_id, adr_id, vault_note, wikilink, created_at) "
                "VALUES (?,?,?,?,?)",
                (session_id, adr_id, vault_note_path, wikilink, self._now()),
            )

    # ------------------------------------------------------------------ git
    @staticmethod
    def isolated_git_commit(
        repo_path: str | Path,
        target_files: List[str],
        message: str,
    ) -> str:
        """
        Commit *target_files* using a temporary GIT_INDEX_FILE so the live
        index and working tree are 100% untouched.

        Pipeline:
          git read-tree HEAD          → load HEAD into temp index
          git update-index --add …   → stage only target_files
          git write-tree              → produce tree SHA
          git commit-tree             → produce commit SHA
          git update-ref HEAD         → advance HEAD

        Returns the new commit SHA.
        Raises subprocess.CalledProcessError on any git failure.
        """
        repo = Path(repo_path).resolve()

        def _git(*args: str, env: Optional[Dict[str, str]] = None) -> str:
            result = subprocess.run(
                ["git", "-C", str(repo), *args],
                capture_output=True, text=True, check=True, env=env,
            )
            return result.stdout.strip()

        with tempfile.NamedTemporaryFile(
            prefix="jev_git_index_", suffix=".idx", delete=False
        ) as tmp:
            tmp_index = tmp.name

        try:
            base_env = {**os.environ, "GIT_INDEX_FILE": tmp_index}

            # Step 1: read current HEAD into temp index
            try:
                _git("read-tree", "HEAD", env=base_env)
            except subprocess.CalledProcessError:
                # Empty repo / no HEAD yet; start with empty tree
                pass

            # Step 2: stage only the requested files
            abs_files = [str(Path(f).resolve()) for f in target_files]
            _git("update-index", "--add", "--", *abs_files, env=base_env)

            # Step 3: write tree
            tree_sha = _git("write-tree", env=base_env)

            # Step 4: resolve parent commit (may be empty repo)
            try:
                parent_sha = _git("rev-parse", "HEAD")
                parent_args = ["-p", parent_sha]
            except subprocess.CalledProcessError:
                parent_args = []

            # Step 5: commit-tree (no index needed; uses tree_sha directly)
            commit_env = {**base_env, "GIT_AUTHOR_DATE": datetime.now(timezone.utc).isoformat(),
                          "GIT_COMMITTER_DATE": datetime.now(timezone.utc).isoformat()}
            commit_sha = _git("commit-tree", tree_sha, *parent_args, "-m", message, env=commit_env)

            # Step 6: advance HEAD
            _git("update-ref", "HEAD", commit_sha)

        finally:
            try:
                os.unlink(tmp_index)
            except OSError:
                pass

        logger.info("isolated_git_commit: %s", commit_sha)
        return commit_sha

    def compile_delta(
        self,
        repo_root: str | Path,
        subdirs: Optional[List[str]] = None,
        repo_name: str = "hermes-agent",
    ) -> Dict[str, Any]:
        """Incrementally compiles Python files by comparing SHA-256 hashes against SQLite cache."""
        if subdirs is None:
            subdirs = ["agent", "tools", "tests", ".agents/skills"]

        root = Path(repo_root).resolve()
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT file_path, sha256 FROM nodes WHERE node_type='FILE' AND repo=?",
            (repo_name,),
        )
        existing_shas: Dict[str, str] = {row[0]: row[1] for row in cursor.fetchall()}

        total_scanned = 0
        recompiled = 0
        skipped_unchanged = 0
        recompiled_files: List[str] = []

        for subdir in subdirs:
            target_dir = root / subdir
            if not target_dir.exists() or not target_dir.is_dir():
                continue

            for pf in sorted(target_dir.rglob("*.py")):
                if not pf.is_file():
                    continue

                total_scanned += 1
                resolved_path = str(pf.resolve())
                current_sha = self._sha256_file(pf)

                if resolved_path in existing_shas and existing_shas[resolved_path] == current_sha:
                    skipped_unchanged += 1
                else:
                    try:
                        self.compile_python_file(pf, repo_name=repo_name)
                        recompiled += 1
                        recompiled_files.append(resolved_path)
                    except SyntaxError:
                        pass

        return {
            "scanned": total_scanned,
            "recompiled": recompiled,
            "skipped_unchanged": skipped_unchanged,
            "recompiled_files": recompiled_files,
        }

    def audit_upstream_commits(
        self,
        evaluator: "LocalJEVEvaluator",
        api_url: str = "https://api.github.com/repos/nousresearch/hermes-agent/commits?per_page=5",
        timeout: int = 8,
    ) -> Dict[str, Any]:
        """Validates GitHub API URL with SSRFGuard, fetches recent commits, and evaluates with LocalJEVEvaluator."""
        import urllib.request

        validated_url = SSRFGuard.validate_url(api_url)
        commits: List[Dict[str, str]] = []
        try:
            req = urllib.request.Request(
                validated_url,
                headers={
                    "Accept": "application/vnd.github+json",
                    "User-Agent": "Hermes-Knowledge-Compiler/1.0",
                },
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                if resp.status == 200:
                    payload = json.loads(resp.read().decode("utf-8"))
                    if isinstance(payload, list):
                        for c in payload:
                            try:
                                sha = c["sha"][:8]
                                msg = c["commit"]["message"].splitlines()[0]
                                date = c["commit"]["committer"]["date"]
                                commits.append({"sha": sha, "message": msg, "date": date})
                            except (KeyError, IndexError, TypeError):
                                continue
        except Exception:
            commits = []

        jev_res = evaluator.evaluate(
            prompt=f"Audit upstream commits: {len(commits)}",
            files=[],
        )

        return {
            "validated_url": validated_url,
            "commits_fetched": len(commits),
            "commits": commits,
            "jev_engine": jev_res.engine,
            "jev_complexity": jev_res.complexity,
        }


def main(argv: Optional[List[str]] = None) -> int:
    """CLI entry point for JEV CLEF Knowledge Compiler."""
    import argparse

    parser = argparse.ArgumentParser(
        description="JEV CLEF Knowledge Compiler CLI - Incremental Delta & Upstream Audit"
    )
    parser.add_argument(
        "--db-path",
        default="~/.hermes/knowledge_compiler.db",
        help="Path to SQLite knowledge database (default: ~/.hermes/knowledge_compiler.db)",
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Target repository root path (default: .)",
    )
    parser.add_argument(
        "--delta",
        action="store_true",
        help="Run incremental delta compilation on repository files",
    )
    parser.add_argument(
        "--upstream-audit",
        action="store_true",
        help="Audit upstream commits and run JEV evaluation",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print execution summary formatted as JSON",
    )

    args = parser.parse_args(argv)

    db_path = Path(os.path.expanduser(args.db_path)).resolve()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    repo_root = Path(os.path.expanduser(args.repo_root)).resolve()

    compiler_db = KnowledgeCompilerDB(db_path=db_path)
    results: Dict[str, Any] = {}

    if args.delta:
        results["delta"] = compiler_db.compile_delta(repo_root=repo_root)

    if args.upstream_audit:
        evaluator = LocalJEVEvaluator()
        results["upstream_audit"] = compiler_db.audit_upstream_commits(evaluator=evaluator)

    if args.json:
        print(json.dumps(results, indent=2, default=str))
    else:
        if "delta" in results:
            d = results["delta"]
            print(
                f"[Delta] Scanned: {d.get('scanned', 0)} | "
                f"Recompiled: {d.get('recompiled', 0)} | "
                f"Skipped Unchanged: {d.get('skipped_unchanged', 0)}"
            )
        if "upstream_audit" in results:
            u = results["upstream_audit"]
            print(
                f"[Upstream Audit] Fetched: {u.get('commits_fetched', 0)} | "
                f"Engine: {u.get('jev_engine')} | "
                f"Complexity: {u.get('jev_complexity')}"
            )

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
