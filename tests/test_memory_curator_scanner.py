"""Tests for the memory-curator superseded-concept scanner (Clef Mnemosyne P2).

(a) pre-label behaviour on a synthetic mini-repo,
(b) read-only guarantee (hashes unchanged),
(c) G3 fixture integrity + measured heuristic precision (reported, not gated).
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SKILL = REPO / ".agents" / "skills" / "memory-curator"
SCRIPT = SKILL / "scripts" / "scan_superseded.py"
REGISTRY = SKILL / "resources" / "deprecations.json"
FIXTURE = SKILL / "resources" / "g3_fixture.json"


def _load_scanner():
    spec = importlib.util.spec_from_file_location("scan_superseded", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


scanner = _load_scanner()

# The G3 fixture quotes are frozen against this commit. The working tree drifts by
# design (curation rewrites stale L3 lines), so drift is checked against the baseline.
# Symlinked skills (.agents/skills/X -> skills/creative/X) have their targets' pre-fix
# baseline tracked one commit later, in f943c79.
BASELINE_COMMIT = "ceb7861"
SYMLINK_BASELINE_COMMIT = "f943c79"


def _baseline_lines(rel: str) -> list[str]:
    tracked = (REPO / rel).resolve().relative_to(REPO.resolve()).as_posix()
    for commit in (BASELINE_COMMIT, SYMLINK_BASELINE_COMMIT):
        out = subprocess.run(["git", "show", f"{commit}:{tracked}"], cwd=REPO, capture_output=True)
        if out.returncode == 0:
            return out.stdout.decode("utf-8").splitlines()
    raise AssertionError(f"{rel} ({tracked}) not found in baseline commits")

FILLER = "\n".join(f"Filler line {i} about subtitles." for i in range(8))


@pytest.fixture
def mini_repo(tmp_path: Path) -> Path:
    (tmp_path / ".agents" / "rules").mkdir(parents=True)
    (tmp_path / ".agents" / "skills" / "voice").mkdir(parents=True)
    (tmp_path / "AGENTS.md").write_text(
        "# Agents\n" + FILLER + "\nTTS V8 is COMPLETELY ABANDONED.\n" + FILLER + "\n", encoding="utf-8")
    (tmp_path / ".agents" / "rules" / "tts.md").write_text(
        FILLER + "\nBÃI BỎ HOÀN TOÀN TTS V8.\n" + FILLER +
        "\nAlways run speech at speed 0.94x for calm tone.\n" + FILLER + "\n", encoding="utf-8")
    (tmp_path / ".agents" / "skills" / "voice" / "SKILL.md").write_text(
        "---\nname: voice\n---\n" + FILLER +
        "\nEngine: load prosody_dictionary.json before synthesis.\n" + FILLER + "\n", encoding="utf-8")
    return tmp_path


def _tree_hashes(root: Path) -> dict[str, str]:
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob("*")) if p.is_file()}


def test_prelabels_on_mini_repo(mini_repo: Path):
    hits = scanner.scan(mini_repo, scanner.load_registry(REGISTRY))
    got = {(h["file"], h["concept_id"]): h["pre_label"] for h in hits}
    assert got == {
        ("AGENTS.md", "tts_v8"): scanner.DEPRECATED,
        (".agents/rules/tts.md", "tts_v8"): scanner.DEPRECATED,
        (".agents/rules/tts.md", "atempo_slowdown"): scanner.LIVE,
        (".agents/skills/voice/SKILL.md", "prosody_dictionary"): scanner.LIVE,
    }


def test_scanner_is_read_only(mini_repo: Path, tmp_path_factory):
    before = _tree_hashes(mini_repo)
    out = tmp_path_factory.mktemp("out")
    assert scanner.main(["--repo", str(mini_repo), "--registry", str(REGISTRY), "--out", str(out)]) == 0
    assert _tree_hashes(mini_repo) == before
    report = json.loads((out / "superseded_scan.json").read_text(encoding="utf-8"))
    assert report["total_hits"] == 4
    assert (out / "superseded_scan.md").read_text(encoding="utf-8").startswith("# Superseded-Concept Scan")


def test_real_repo_scan_is_read_only(tmp_path: Path):
    targets = scanner.iter_target_files(REPO)
    before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in targets}
    scanner.main(["--repo", str(REPO), "--out", str(tmp_path)])
    assert {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in targets} == before


def test_g3_fixture_integrity_and_precision_report():
    fx = json.loads(FIXTURE.read_text(encoding="utf-8"))
    entries = fx["entries"]
    assert entries, "fixture must not be empty"
    allowed = {"supersedes_candidate", "mentions_as_deprecated", "ambiguous"}
    for e in entries:
        assert e["label"] in allowed
        lines = _baseline_lines(e["file"])
        assert 1 <= e["line"] <= len(lines), e
        assert lines[e["line"] - 1].strip()[:200] == e["quote"], f"fixture drifted: {e['file']}:{e['line']}"

    truth = {(e["file"], e["line"], e["concept_id"]): e["label"] for e in entries}
    hits = scanner.scan(REPO, scanner.load_registry(REGISTRY))
    pred = {(h["file"], h["line"], h["concept_id"]): h["pre_label"] for h in hits}

    live = [k for k, v in pred.items() if v == scanner.LIVE]
    tp = sum(truth.get(k) == "supersedes_candidate" for k in live)
    amb = sum(truth.get(k) == "ambiguous" for k in live)
    unlabeled = [k for k in pred if k not in truth]
    n_true = sum(v == "supersedes_candidate" for v in truth.values())
    precision = tp / len(live) if live else float("nan")
    precision_ex_amb = tp / (len(live) - amb) if len(live) - amb else float("nan")
    recall = tp / n_true if n_true else float("nan")
    print(f"\n[G3 heuristic] hits={len(pred)} candidate_live={len(live)} tp={tp} ambiguous={amb} "
          f"precision={precision:.3f} precision_excl_ambiguous={precision_ex_amb:.3f} "
          f"recall={recall:.3f} (G3 target for Judge output: >=0.95) unlabeled_hits={len(unlabeled)}")
    for k in unlabeled:
        print(f"  UNLABELED hit (fixture needs review): {k}")
