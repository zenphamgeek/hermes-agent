"""Tests for memory-curator P3: weekly L3 curation with gated auto-removal.

All tests use the deterministic OfflineJudge on a throwaway git repo (tmp_path).
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SKILL = REPO / ".agents" / "skills" / "memory-curator"
SCRIPT = SKILL / "scripts" / "curate_l3.py"
REGISTRY = SKILL / "resources" / "deprecations.json"


def _load():
    spec = importlib.util.spec_from_file_location("curate_l3", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["curate_l3"] = mod  # dataclasses resolve annotations via sys.modules
    spec.loader.exec_module(mod)
    return mod


cur = _load()

FILLER = "".join(f"Filler line {i} about subtitles.\n" for i in range(8))
LIVE_LINE = "Always run speech at speed 0.94x for calm tone."
AGENTS_LINE = "Use TTS V8 for everything."
GOOD_REPL = "Always run speech at native 1.0x speed for calm tone."
RULE = ".agents/rules/tts.md"
TOMB = ".agents/skills/memory-curator/resources/l3_tombstones.jsonl"
TOMB_KEYS = {"file", "line", "old_text", "new_text", "reason", "superseded_by",
             "verdict", "judge_node", "recorded_at", "valid_to"}


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True,
                          text=True).stdout.strip()


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    r = tmp_path / "repo"
    (r / ".agents" / "rules").mkdir(parents=True)
    (r / ".agents" / "skills" / "memory-curator" / "resources").mkdir(parents=True)
    (r / "AGENTS.md").write_text(FILLER + AGENTS_LINE + "\n" + FILLER, encoding="utf-8")
    (r / RULE).write_text(FILLER + LIVE_LINE + "\n" + FILLER, encoding="utf-8")
    (r / ".agents" / "skills" / "memory-curator" / "resources" / ".gitkeep").write_text("")
    git(r, "init", "-q", "-b", "main")
    git(r, "config", "user.name", "t")
    git(r, "config", "user.email", "t@t")
    git(r, "add", "-A")
    git(r, "commit", "-q", "-m", "base")
    return r


def line_no(path: Path, text: str) -> int:
    return path.read_text(encoding="utf-8").splitlines().index(text) + 1


def key(repo: Path, rel: str, text: str, concept: str) -> str:
    return f"{rel}:{line_no(repo / rel, text)}:{concept}"


def tree_hashes(root: Path) -> dict[str, str]:
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob("*")) if p.is_file() and ".git" not in p.relative_to(root).parts}


def supersede(repo: Path, replacement: str = GOOD_REPL) -> dict:
    return {key(repo, RULE, LIVE_LINE, "atempo_slowdown"):
            {"verdict": "supersedes", "quote": LIVE_LINE, "replacement": replacement}}


def run(repo, verdicts, apply=True, report_dir=None):
    return cur.run(repo, cur.OfflineJudge(verdicts), apply=apply, registry=REGISTRY, report_dir=report_dir)


def test_applies_true_supersedes(repo: Path):
    n = line_no(repo / RULE, LIVE_LINE)
    res = run(repo, supersede(repo))
    assert [(a["file"], a["line"]) for a in res["applied"]] == [(RULE, n)]
    assert (repo / RULE).read_text(encoding="utf-8").splitlines()[n - 1] == GOOD_REPL
    assert res["commit"] and res["merged"] is True
    assert git(repo, "rev-parse", "main") == res["commit"]
    assert git(repo, "status", "--porcelain", "--", RULE) == ""


def test_quarantines_on_judge_failure(repo: Path):
    before = (repo / RULE).read_bytes()
    res = run(repo, {key(repo, RULE, LIVE_LINE, "atempo_slowdown"): {"fail": True}})
    q = [e for e in res["quarantined"] if e["file"] == RULE]
    assert q and "judge failure" in q[0]["reason"]
    assert res["applied"] == []
    assert (repo / RULE).read_bytes() == before
    tomb = repo / TOMB
    assert not tomb.exists() or tomb.read_text(encoding="utf-8").strip() == ""


def test_quarantines_when_replacement_still_deprecated(repo: Path):
    before = (repo / RULE).read_bytes()
    res = run(repo, supersede(repo, "Always run speech at 0.94x speed."))
    q = [e for e in res["quarantined"] if e["file"] == RULE]
    assert q and "still matches deprecated" in q[0]["reason"]
    assert res["applied"] == []
    assert (repo / RULE).read_bytes() == before


def test_never_edits_agents_md(repo: Path):
    before = (repo / "AGENTS.md").read_bytes()
    res = run(repo, {key(repo, "AGENTS.md", AGENTS_LINE, "tts_v8"):
                     {"verdict": "supersedes", "quote": AGENTS_LINE,
                      "replacement": "Use TTS V0-Sense for everything."}})
    assert (repo / "AGENTS.md").read_bytes() == before
    q = [e for e in res["quarantined"] if e["file"] == "AGENTS.md"]
    assert q and "protected" in q[0]["reason"]
    assert all(a["file"] != "AGENTS.md" for a in res["applied"])


def test_tombstone_full_old_text(repo: Path):
    run(repo, supersede(repo))
    recs = [json.loads(ln) for ln in (repo / TOMB).read_text(encoding="utf-8").splitlines() if ln.strip()]
    assert len(recs) == 1
    r = recs[0]
    assert TOMB_KEYS <= set(r)
    assert r["old_text"] == LIVE_LINE
    assert r["new_text"] == GOOD_REPL
    assert r["verdict"] == "supersedes"
    assert r["file"] == RULE and r["judge_node"] == "offline"


def test_commit_on_curation_branch_and_merged(repo: Path):
    base = git(repo, "rev-parse", "HEAD")
    res = run(repo, supersede(repo))
    assert re.fullmatch(r"fleet/judge/memory-curation-\d{6}", res["branch"])
    assert git(repo, "rev-parse", res["branch"]) == res["commit"] == git(repo, "rev-parse", "main")
    assert git(repo, "rev-parse", "HEAD~1") == base  # fast-forward, single commit
    assert "memory-curator" in git(repo, "log", "-1", "--format=%s", "main")
    changed = git(repo, "diff", "--name-only", "HEAD~1", "HEAD").splitlines()
    assert RULE in changed and TOMB in changed and "AGENTS.md" not in changed
    assert any(p.startswith(".agents/skills/memory-curator/resources/runs/") for p in changed)


def test_commit_excludes_unrelated_dirty_work(repo: Path):
    (repo / "notes.txt").write_text("other agent WIP\n", encoding="utf-8")
    res = run(repo, supersede(repo))
    assert "notes.txt" not in git(repo, "diff", "--name-only", "HEAD~1", "HEAD").splitlines()
    assert res["merged"] and (repo / "notes.txt").exists()


def test_dry_run_changes_nothing(repo: Path, tmp_path_factory):
    before, head = tree_hashes(repo), git(repo, "rev-parse", "HEAD")
    res = run(repo, supersede(repo), apply=False, report_dir=tmp_path_factory.mktemp("rep"))
    assert res["applied"], "dry-run should still report would-apply candidates"
    assert res["commit"] is None
    assert tree_hashes(repo) == before
    assert git(repo, "rev-parse", "HEAD") == head
    assert git(repo, "branch", "--list", "fleet/*") == ""
    assert Path(res["report_path"]).is_file()


def test_fleet_backend_unreachable_quarantines(repo: Path):
    before = (repo / RULE).read_bytes()
    judge = cur.FleetJudge(base_url="http://127.0.0.1:9", timeout=5)
    res = cur.run(repo, judge, apply=True, registry=REGISTRY)
    assert res["applied"] == [] and len(res["quarantined"]) == res["candidates"] >= 1
    assert all("judge failure" in e["reason"] for e in res["quarantined"])
    assert (repo / RULE).read_bytes() == before


def test_parse_verdict_array_rejects_prose():
    with pytest.raises(cur.JudgeError):
        cur.parse_verdict_array("I think it supersedes.")
    assert cur.parse_verdict_array('```json\n[{"id": "0", "verdict": "unrelated"}]\n```')[0]["id"] == "0"
