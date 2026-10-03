#!/usr/bin/env python3
"""Weekly L3 curation loop with gated auto-removal (memory-curator skill, Clef Mnemosyne P3).

Pipeline: scan -> judge -> auto-apply gate -> minimal line rewrite + tombstone
-> commit on ``fleet/judge/memory-curation-YYYYWW`` -> fast-forward ``main``.

* ``--dry-run`` (default) never writes inside the repo; the report goes to
  ``--report-dir`` (default ``/tmp/memory-curator-runs``).
* ``--apply`` edits L3 files, appends tombstones, writes
  ``resources/runs/YYYYWW.md`` and commits ONLY those paths using git plumbing
  (a temporary index), so other agents' uncommitted work is never swept in.
  It never pushes.

Any judge failure / unparsable verdict -> QUARANTINE. Nothing is auto-applied
unless every clause of the auto-apply gate holds (see ``gate``).
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_REL = Path(".agents/skills/memory-curator")
DEFAULT_REPO = Path(__file__).resolve().parents[4]
DEFAULT_FLEET_URL = os.environ.get("AROUTER_URL", "http://localhost:7777")
PREFERRED_JUDGE = "ultra-2"
JUDGE_ROLES = {"Judge", "Auditor"}
CONTEXT = 6

LABELS = {"supersedes", "refines", "contradicts", "mentions_as_deprecated", "unrelated"}
KEEP_LABELS = {"mentions_as_deprecated", "unrelated"}
PROTECTED_FILES = {"AGENTS.md", ".agents/rules/05_modal_gpu_fleet_and_token_invariants.md"}
MIN_QUOTE = 8

DATE_RX = re.compile(r"\b(?:19|20)\d{2}-\d{2}(?:-\d{2})?\b|\b\d{1,2}/\d{1,2}/(?:19|20)\d{2}\b")
HISTORY_RX = re.compile(
    r"benchmark|history|changelog|lịch sử|nhật ký|kết quả đo|measurement|post-?mortem|incident|\blog\b",
    re.IGNORECASE)

TOMBSTONE_KEYS = ("file", "line", "old_text", "new_text", "reason", "superseded_by",
                  "verdict", "judge_node", "recorded_at", "valid_to")
BOT_ENV = {
    "GIT_AUTHOR_NAME": "memory-curator (Clef Mnemosyne)",
    "GIT_AUTHOR_EMAIL": "memory-curator@localhost",
    "GIT_COMMITTER_NAME": "memory-curator (Clef Mnemosyne)",
    "GIT_COMMITTER_EMAIL": "memory-curator@localhost",
}


def _load_scanner():
    spec = importlib.util.spec_from_file_location("scan_superseded", SCRIPT_DIR / "scan_superseded.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


scanner = _load_scanner()


# --------------------------------------------------------------------------- judges
@dataclass
class Verdict:
    verdict: str
    quote: str
    replacement: str = ""
    rationale: str = ""
    judge_node: str = ""


class JudgeError(Exception):
    pass


def candidate_key(c: dict) -> str:
    return f"{c['file']}:{c['line']}:{c['concept_id']}"


def _validate(raw: dict, node: str) -> Verdict:
    if not isinstance(raw, dict):
        raise JudgeError("verdict is not an object")
    v = str(raw.get("verdict", "")).strip().lower()
    if v not in LABELS:
        raise JudgeError(f"invalid verdict label {v!r}")
    quote = raw.get("quote")
    if not isinstance(quote, str) or not quote.strip():
        raise JudgeError("missing verbatim quote")
    repl = raw.get("replacement") or ""
    if not isinstance(repl, str):
        raise JudgeError("replacement is not a string")
    return Verdict(v, quote, repl, str(raw.get("rationale", "")), node)


class OfflineJudge:
    """Deterministic backend for tests/offline runs.

    ``verdicts`` maps ``file:line:concept_id`` -> {verdict, quote, replacement}
    or {"fail": True}. Missing keys are judge failures (-> QUARANTINE).
    """

    name = "offline"

    def __init__(self, verdicts: dict | None = None):
        self.verdicts = verdicts or {}

    def judge(self, candidates: list[dict]) -> dict[str, Verdict | JudgeError]:
        out: dict[str, Verdict | JudgeError] = {}
        for c in candidates:
            raw = self.verdicts.get(candidate_key(c))
            if raw is None:
                out[candidate_key(c)] = JudgeError("offline judge: no verdict for candidate")
            elif raw.get("fail"):
                out[candidate_key(c)] = JudgeError("offline judge: simulated backend failure")
            else:
                try:
                    out[candidate_key(c)] = _validate(raw, "offline")
                except JudgeError as e:
                    out[candidate_key(c)] = e
        return out


JUDGE_INSTRUCTIONS = """You are the Judge/Auditor of the Clef Mnemosyne memory curator.
You have NO filesystem access; everything you need is below.
For each candidate, classify the TARGET line (marked '>>') against its deprecation
registry entry into exactly one label:
- supersedes: the line still instructs agents to USE the deprecated concept; the registry
  replacement fully replaces it within the same scope.
- refines: partially valid, needs nuanced human edit.
- contradicts: conflict you cannot adjudicate from the given text.
- mentions_as_deprecated: the line DESCRIBES the concept as abandoned/forbidden (a guard
  rail). Guard rails must be kept.
- unrelated: pattern collision, not about the concept.
Rules:
- "quote" MUST be a verbatim substring copied from the TARGET line (>= 8 chars).
- For supersedes only, "replacement" = the FULL rewritten TARGET line: minimal edit,
  same language and markdown structure, aligned with the registry replacement, and it
  must NOT contain any deprecated pattern. Otherwise "replacement" = "".
- Never turn a guard rail into a live instruction. When unsure, use contradicts.
Return ONLY a JSON array, no prose:
[{"id": "<id>", "verdict": "<label>", "quote": "<verbatim>", "replacement": "<line or empty>", "rationale": "<one sentence>"}]
"""


def build_prompt(candidates: list[dict], concepts: dict[str, dict]) -> str:
    parts = [JUDGE_INSTRUCTIONS]
    for i, c in enumerate(candidates):
        reg = {k: v for k, v in concepts[c["concept_id"]].items() if not k.startswith("_")}
        parts.append(f"\n### Candidate id={i}\nfile: {c['file']}  line: {c['line']}  "
                     f"heuristic_pre_label: {c['pre_label']}\nregistry_entry: "
                     f"{json.dumps(reg, ensure_ascii=False)}\ncontext:\n{c['context_text']}\n")
    return "".join(parts)


def parse_verdict_array(text: str) -> list:
    text = text or ""
    m = re.search(r"```(?:json)?\s*(\[.*?\])\s*```", text, re.DOTALL)
    blob = m.group(1) if m else None
    if blob is None:
        s, e = text.find("["), text.rfind("]")
        if s == -1 or e <= s:
            raise JudgeError("no JSON array in judge response")
        blob = text[s:e + 1]
    try:
        data = json.loads(blob)
    except json.JSONDecodeError as exc:
        raise JudgeError(f"unparsable judge JSON: {exc}") from exc
    if not isinstance(data, list):
        raise JudgeError("judge JSON is not an array")
    return data


class FleetJudge:
    """AGY fleet judge via arouter ``POST /api/fleet/run-sync`` (JobRequest payload)."""

    name = "fleet"

    def __init__(self, base_url: str = DEFAULT_FLEET_URL, preferred: str = PREFERRED_JUDGE,
                 timeout: int = 600, batch_size: int = 6, concepts: dict | None = None):
        self.base_url = base_url.rstrip("/")
        self.preferred = preferred
        self.timeout = timeout
        self.batch_size = batch_size
        self.concepts = concepts or {}
        self.endpoint = f"{self.base_url}/api/fleet/run-sync"
        self.errors: list[str] = []

    def _http(self, method: str, path: str, payload: dict | None = None, timeout: int = 15):
        data = json.dumps(payload).encode() if payload is not None else None
        req = urllib.request.Request(f"{self.base_url}{path}", data=data, method=method,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def judge_nodes(self) -> list[str]:
        nodes = self._http("GET", "/api/fleet/nodes")
        nodes = nodes.get("nodes", nodes) if isinstance(nodes, dict) else nodes
        items = nodes.values() if isinstance(nodes, dict) else nodes
        ok = [n["name"] for n in items
              if n.get("label") in JUDGE_ROLES
              and str(n.get("status", "")).lower() not in {"error", "unauthenticated"}]
        return sorted(ok, key=lambda n: (n != self.preferred, n))

    def _run_batch(self, batch: list[dict], allowed: list[str]) -> tuple[list, str]:
        last = "no Judge/Auditor node available"
        for node in allowed[:2]:
            try:
                job = self._http("POST", "/api/fleet/run-sync",
                                 {"prompt": build_prompt(batch, self.concepts),
                                  "node_name": node, "timeout": self.timeout},
                                 timeout=self.timeout + 60)
            except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
                last = f"{node}: transport error {exc}"
                continue
            ran_on = job.get("node_name", "")
            if ran_on not in allowed:
                last = f"{node}: rerouted to non-judge node {ran_on!r}"
                continue
            if job.get("status") != "completed":
                last = f"{ran_on}: job status {job.get('status')!r} {str(job.get('stderr', ''))[:200]}"
                continue
            try:
                return parse_verdict_array(job.get("clean_response") or job.get("stdout") or ""), ran_on
            except JudgeError as exc:
                last = f"{ran_on}: {exc}"
        raise JudgeError(last)

    def judge(self, candidates: list[dict]) -> dict[str, Verdict | JudgeError]:
        out: dict[str, Verdict | JudgeError] = {}
        try:
            allowed = self.judge_nodes()
        except Exception as exc:  # noqa: BLE001 - any failure quarantines
            err = JudgeError(f"fleet node discovery failed at {self.base_url}: {exc}")
            self.errors.append(str(err))
            return {candidate_key(c): err for c in candidates}
        for s in range(0, len(candidates), self.batch_size):
            batch = candidates[s:s + self.batch_size]
            try:
                raw, node = self._run_batch(batch, allowed)
            except JudgeError as exc:
                self.errors.append(str(exc))
                for c in batch:
                    out[candidate_key(c)] = exc
                continue
            by_id = {str(r.get("id")): r for r in raw if isinstance(r, dict)}
            for i, c in enumerate(batch):
                r = by_id.get(str(i))
                try:
                    if r is None:
                        raise JudgeError("judge returned no verdict for this id")
                    out[candidate_key(c)] = _validate(r, node)
                except JudgeError as exc:
                    out[candidate_key(c)] = exc
        return out


# --------------------------------------------------------------------------- git helpers
def git(repo: Path, *args: str, env: dict | None = None, input_: str | None = None,
        check: bool = True, retries: int = 8) -> str:
    full_env = {**os.environ, **(env or {})}
    for attempt in range(retries):
        p = subprocess.run(["git", *args], cwd=repo, env=full_env, input=input_,
                           capture_output=True, text=True, encoding="utf-8")
        if p.returncode == 0 or not check:
            return p.stdout.strip()
        if "index.lock" in p.stderr or ".lock" in p.stderr and "File exists" in p.stderr:
            time.sleep(0.5 * (attempt + 1))
            continue
        raise RuntimeError(f"git {' '.join(args)} failed: {p.stderr.strip()}")
    raise RuntimeError(f"git {' '.join(args)}: lock contention persisted")


def head_text(repo: Path, rel: str, rev: str = "HEAD") -> str | None:
    p = subprocess.run(["git", "show", f"{rev}:{rel}"], cwd=repo, capture_output=True)
    return p.stdout.decode("utf-8") if p.returncode == 0 else None


def tracked_rel(repo: Path, rel: str) -> str | None:
    """Resolve symlinks (e.g. .agents/skills/X -> skills/creative/X) to the git-tracked path."""
    try:
        return (repo / rel).resolve().relative_to(repo.resolve()).as_posix()
    except ValueError:
        return None


def iso_week(now: datetime) -> str:
    y, w, _ = now.isocalendar()
    return f"{y}{w:02d}"


# --------------------------------------------------------------------------- gate
def in_history_block(lines: list[str], idx: int) -> bool:
    if DATE_RX.search(lines[idx]):
        return True
    for j in range(idx - 1, -1, -1):
        s = lines[j].lstrip()
        if s.startswith("#"):
            return bool(DATE_RX.search(s) or HISTORY_RX.search(s))
    return False


def matches_any(line: str, concepts: list[dict]) -> list[str]:
    return [c["id"] for c in concepts if any(rx.search(line) for rx in c["_rx"])]


def _split_eol(line: str) -> tuple[str, str]:
    body = line.rstrip("\r\n")
    return body, line[len(body):]


def gate(c: dict, v: Verdict, concepts: list[dict], by_id: dict[str, dict],
         lines: list[str]) -> tuple[str, str, str]:
    """Return (decision, reason, new_line). decision in applied|quarantined|skipped."""
    if v.verdict in KEEP_LABELS:
        return "skipped", f"KEEP ({v.verdict})", ""
    if v.verdict != "supersedes":
        return "quarantined", f"verdict {v.verdict} needs Council review", ""
    if c["file"] in PROTECTED_FILES:
        return "quarantined", "protected file (never auto-edited)", ""
    old = lines[c["line"] - 1]
    quote_ok = len(v.quote.strip()) >= MIN_QUOTE and v.quote.strip() in old
    if not (c["pre_label"] == scanner.LIVE or quote_ok):
        return "quarantined", "pre-label is not live and judge quote is not verbatim", ""
    if not quote_ok and v.quote.strip() and v.quote.strip() not in old:
        return "quarantined", "judge quote not found verbatim in line", ""
    if not str(by_id[c["concept_id"]].get("replacement", "")).strip():
        return "quarantined", "registry entry has no explicit replacement", ""
    if in_history_block(lines, c["line"] - 1):
        return "quarantined", "line is inside a dated benchmark/history block", ""
    new = v.replacement.rstrip("\r\n")
    if not new.strip() or "\n" in new or "\r" in new:
        return "quarantined", "judge replacement empty or multi-line", ""
    indent = old[: len(old) - len(old.lstrip())]
    if indent and not new.startswith(indent):
        new = indent + new.lstrip()
    if new == old:
        return "quarantined", "replacement identical to original", ""
    still = matches_any(new, concepts)
    if still:
        return "quarantined", f"replacement still matches deprecated pattern(s): {still}", ""
    return "applied", f"supersedes: {by_id[c['concept_id']]['replacement']}", new


# --------------------------------------------------------------------------- run
@dataclass
class Result:
    applied: list = field(default_factory=list)
    quarantined: list = field(default_factory=list)
    skipped: list = field(default_factory=list)


def _entry(c: dict, reason: str, v: Verdict | None = None, new: str = "") -> dict:
    e = {"file": c["file"], "line": c["line"], "concept_id": c["concept_id"],
         "pre_label": c["pre_label"], "old_text": c["full_line"], "reason": reason}
    if v is not None:
        e.update(verdict=v.verdict, quote=v.quote, judge_node=v.judge_node)
    if new:
        e["new_text"] = new
    return e


def collect(repo: Path, concepts: list[dict]) -> list[dict]:
    hits = scanner.scan(repo, concepts)
    cache: dict[str, list[str]] = {}
    for h in hits:
        lines = cache.setdefault(h["file"], (repo / h["file"]).read_text(encoding="utf-8").splitlines())
        idx = h["line"] - 1
        h["full_line"] = lines[idx]
        lo, hi = max(0, idx - CONTEXT), min(len(lines), idx + CONTEXT + 1)
        h["context_text"] = "\n".join(
            f"{'>>' if j == idx else '  '} {j + 1:4d}: {lines[j]}" for j in range(lo, hi))
    return hits


def render_report(res: Result, meta: dict) -> str:
    out = [f"# Memory-curator L3 run {meta['week']} ({meta['mode']})", "",
           f"- Recorded: {meta['recorded_at']}", f"- Repo: `{meta['repo']}`",
           f"- Judge backend: `{meta['judge']}` endpoint: `{meta.get('endpoint', '-')}`",
           f"- Candidates: {meta['candidates']} | applied: **{len(res.applied)}** | "
           f"quarantined: **{len(res.quarantined)}** | skipped (KEEP): **{len(res.skipped)}**", ""]
    if meta.get("judge_errors"):
        out += ["## Judge errors", "", *[f"- {e}" for e in meta["judge_errors"]], ""]
    for title, rows in (("Applied", res.applied), ("Quarantined", res.quarantined),
                        ("Skipped (KEEP)", res.skipped)):
        out += [f"## {title}", "", "| File | Line | Concept | Verdict | Reason |", "|---|---|---|---|---|"]
        for r in rows:
            reason = str(r["reason"]).replace("|", "\\|")
            out.append(f"| `{r['file']}` | {r['line']} | `{r['concept_id']}` | "
                       f"`{r.get('verdict', '-')}` | {reason} |")
        if title == "Applied":
            for r in rows:
                out += ["", f"- `{r['file']}:{r['line']}`", f"  - old: `{r['old_text'].strip()}`",
                        f"  - new: `{r['new_text'].strip()}`"]
        out.append("")
    return "\n".join(out)


def _rewrite(text: str, idx: int, old: str, new: str) -> str | None:
    lines = text.splitlines(keepends=True)
    if idx >= len(lines):
        return None
    body, eol = _split_eol(lines[idx])
    if body != old:
        return None
    lines[idx] = new + eol
    return "".join(lines)


def _commit_and_merge(repo: Path, edits: dict[str, list[tuple[int, str, str]]],
                      extra_paths: list[str], week: str, summary: str) -> dict:
    info = {"commit": None, "branch": None, "merged": False, "merge_error": None}
    for attempt in range(3):
        head = git(repo, "rev-parse", "HEAD")
        with tempfile.TemporaryDirectory() as td:
            env = {"GIT_INDEX_FILE": str(Path(td) / "index"), **BOT_ENV}
            git(repo, "read-tree", head, env=env)
            for rel, items in edits.items():
                text = head_text(repo, rel, head)
                if text is None:
                    raise RuntimeError(f"{rel} not tracked at HEAD")
                for idx, old, new in items:
                    text = _rewrite(text, idx, old, new)
                    if text is None:
                        raise RuntimeError(f"{rel}:{idx + 1} differs from HEAD; refusing to commit")
                blob = git(repo, "hash-object", "-w", "--stdin", input_=text)
                git(repo, "update-index", "--add", "--cacheinfo", f"100644,{blob},{rel}", env=env)
            for rel in extra_paths:
                blob = git(repo, "hash-object", "-w", "--", rel)
                git(repo, "update-index", "--add", "--cacheinfo", f"100644,{blob},{rel}", env=env)
            tree = git(repo, "write-tree", env=env)
        if tree == git(repo, "rev-parse", f"{head}^{{tree}}"):
            return info
        msg = f"chore(memory-curator): L3 curation {week}\n\n{summary}\n"
        commit = git(repo, "commit-tree", tree, "-p", head, "-m", msg, env=BOT_ENV)
        branch = f"fleet/judge/memory-curation-{week}"
        n = 1
        while git(repo, "rev-parse", "--verify", "-q", f"refs/heads/{branch}", check=False):
            existing = git(repo, "rev-parse", f"refs/heads/{branch}")
            if subprocess.run(["git", "merge-base", "--is-ancestor", existing, head], cwd=repo).returncode == 0:
                break  # previous run already merged; safe to move the branch forward
            n += 1
            branch = f"fleet/judge/memory-curation-{week}-{n}"
        git(repo, "update-ref", f"refs/heads/{branch}", commit)
        info.update(commit=commit, branch=branch)
        current = git(repo, "symbolic-ref", "-q", "HEAD", check=False)
        if current != "refs/heads/main":
            info["merge_error"] = f"HEAD is {current or 'detached'}, not main; branch left unmerged"
            return info
        p = subprocess.run(["git", "update-ref", "-m", f"memory-curator: ff-merge {branch}",
                            "refs/heads/main", commit, head], cwd=repo, capture_output=True, text=True)
        if p.returncode != 0:
            info["merge_error"] = p.stderr.strip()
            continue  # main moved concurrently; rebuild on the new HEAD
        # Sync the real index for exactly our paths (other staged work untouched).
        git(repo, "reset", "-q", commit, "--", *edits.keys(), *extra_paths)
        info.update(merged=True, merge_error=None)
        return info
    return info


def run(repo: Path, judge, apply: bool = False, registry: Path | None = None,
        report_dir: Path | None = None, now: datetime | None = None) -> dict:
    repo = Path(repo).resolve()
    now = now or datetime.now(timezone.utc)
    week = iso_week(now.astimezone())
    registry = Path(registry) if registry else (
        repo / SKILL_REL / "resources" / "deprecations.json"
        if (repo / SKILL_REL / "resources" / "deprecations.json").is_file()
        else SCRIPT_DIR.parent / "resources" / "deprecations.json")
    concepts = scanner.load_registry(registry)
    by_id = {c["id"]: c for c in concepts}
    if hasattr(judge, "concepts") and not judge.concepts:
        judge.concepts = by_id

    candidates = collect(repo, concepts)
    verdicts = judge.judge(candidates) if candidates else {}
    res = Result()
    file_lines: dict[str, list[str]] = {}
    edits: dict[str, list[tuple[int, str, str]]] = {}
    rewritten: set[tuple[str, int]] = set()
    recorded = now.isoformat(timespec="seconds")

    for c in candidates:
        v = verdicts.get(candidate_key(c))
        if v is None or isinstance(v, JudgeError):
            res.quarantined.append(_entry(c, f"judge failure: {v or 'no verdict'}"))
            continue
        if (c["file"], c["line"]) in rewritten:
            res.skipped.append(_entry(c, "line already rewritten by another candidate this run", v))
            continue
        lines = file_lines.setdefault(c["file"], (repo / c["file"]).read_text(encoding="utf-8").splitlines())
        decision, reason, new = gate(c, v, concepts, by_id, lines)
        trk = tracked_rel(repo, c["file"])
        if decision == "applied" and (trk is None or trk in PROTECTED_FILES):
            decision, reason = "quarantined", f"path resolves outside repo or to a protected file ({trk})"
        if decision == "applied":
            head = head_text(repo, trk)
            head_lines = head.splitlines() if head is not None else []
            if len(head_lines) < c["line"] or head_lines[c["line"] - 1] != c["full_line"]:
                decision, reason = "quarantined", "line has uncommitted changes vs HEAD (concurrent edit)"
        if decision == "applied":
            rewritten.add((c["file"], c["line"]))
            edits.setdefault(trk, []).append((c["line"] - 1, c["full_line"], new))
            res.applied.append(_entry(c, reason, v, new))
        elif decision == "quarantined":
            res.quarantined.append(_entry(c, reason, v))
        else:
            res.skipped.append(_entry(c, reason, v))

    meta = {"week": week, "mode": "apply" if apply else "dry-run", "recorded_at": recorded,
            "repo": str(repo), "judge": getattr(judge, "name", type(judge).__name__),
            "endpoint": getattr(judge, "endpoint", "-"), "candidates": len(candidates),
            "judge_errors": sorted(set(getattr(judge, "errors", [])))}
    out = {"applied": res.applied, "quarantined": res.quarantined, "skipped": res.skipped,
           "commit": None, "branch": None, "merged": False, "merge_error": None,
           "week": week, "candidates": len(candidates), "judge_errors": meta["judge_errors"]}

    if not apply:
        rd = Path(report_dir) if report_dir else Path("/tmp/memory-curator-runs")
        if rd.resolve().is_relative_to(repo):
            raise ValueError("dry-run report_dir must be outside the repo")
        rd.mkdir(parents=True, exist_ok=True)
        rp = rd / f"{week}.dry-run.md"
        rp.write_text(render_report(res, meta), encoding="utf-8")
        out["report_path"] = str(rp)
        return out

    # ---- apply: working tree edits
    for rel, items in edits.items():
        p = repo / rel
        text = p.read_bytes().decode("utf-8")
        for idx, old, new in items:
            text = _rewrite(text, idx, old, new)
            if text is None:
                raise RuntimeError(f"{rel}:{idx + 1} changed during run; aborting before write")
        p.write_bytes(text.encode("utf-8"))
    extra: list[str] = []
    res_dir = repo / SKILL_REL / "resources"
    if res.applied:
        tomb = res_dir / "l3_tombstones.jsonl"
        tomb.parent.mkdir(parents=True, exist_ok=True)
        with open(tomb, "a", encoding="utf-8") as fh:
            for a in res.applied:
                rec = {"file": a["file"], "line": a["line"], "old_text": a["old_text"],
                       "new_text": a["new_text"], "reason": a["reason"],
                       "superseded_by": by_id[a["concept_id"]]["replacement"],
                       "verdict": a["verdict"], "judge_node": a["judge_node"],
                       "recorded_at": recorded, "valid_to": recorded,
                       "concept_id": a["concept_id"], "quote": a["quote"],
                       "source_of_truth": by_id[a["concept_id"]].get("source_of_truth", ""),
                       "op": "SUPERSEDE", "tier": "L3"}
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        extra.append(tomb.relative_to(repo).as_posix())
    rd = Path(report_dir) if report_dir else res_dir / "runs"
    rd.mkdir(parents=True, exist_ok=True)
    rp = rd / f"{week}.md"
    rp.write_text(render_report(res, meta), encoding="utf-8")
    out["report_path"] = str(rp)
    if rp.resolve().is_relative_to(repo):
        extra.append(rp.resolve().relative_to(repo).as_posix())
    summary = (f"applied={len(res.applied)} quarantined={len(res.quarantined)} "
               f"skipped={len(res.skipped)} judge={meta['judge']}\n" +
               "\n".join(f"- {a['file']}:{a['line']} {a['concept_id']}" for a in res.applied))
    out.update(_commit_and_merge(repo, edits, extra, week, summary))
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repo", type=Path, default=DEFAULT_REPO)
    ap.add_argument("--registry", type=Path, default=None)
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", dest="apply", action="store_false", default=False)
    mode.add_argument("--apply", dest="apply", action="store_true")
    ap.add_argument("--judge", choices=["fleet", "offline"], default="fleet")
    ap.add_argument("--offline-verdicts", type=Path, default=None)
    ap.add_argument("--fleet-url", default=DEFAULT_FLEET_URL)
    ap.add_argument("--judge-node", default=PREFERRED_JUDGE)
    ap.add_argument("--timeout", type=int, default=600)
    ap.add_argument("--batch-size", type=int, default=6)
    ap.add_argument("--report-dir", type=Path, default=None)
    ap.add_argument("--json", action="store_true", help="print full JSON result")
    args = ap.parse_args(argv)

    if args.judge == "offline":
        vd = json.loads(args.offline_verdicts.read_text(encoding="utf-8")) if args.offline_verdicts else {}
        judge = OfflineJudge(vd)
    else:
        judge = FleetJudge(args.fleet_url, args.judge_node, args.timeout, args.batch_size)
    out = run(args.repo, judge, apply=args.apply, registry=args.registry, report_dir=args.report_dir)
    if args.json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
    print(f"mode={'apply' if args.apply else 'dry-run'} week={out['week']} candidates={out['candidates']} "
          f"applied={len(out['applied'])} quarantined={len(out['quarantined'])} skipped={len(out['skipped'])} "
          f"commit={out['commit']} branch={out['branch']} merged={out['merged']}")
    for e in out["judge_errors"]:
        print(f"judge_error: {e}")
    print(f"report: {out['report_path']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
