"""
test_jev_clef_knowledge_compiler.py
====================================
Adversarial pytest suite for:
  · tools/jev_clef_knowledge_compiler.py  (SSRFGuard, LocalJEVEvaluator, KnowledgeCompilerDB)
  · tools/rearchitect_skills_and_root.py  (REMEDIATION_DESCRIPTIONS, audit_skills,
                                           apply_skill_description_fixes, classify_root_python_scripts)

Adversarial ToT applied:
  Branch A — catastrophic failure modes (SSRF bypass, cache poisoning, git dirty-tree clobber,
             tombstone data loss, secret leakage in ledger)
  Branch B — defensive assertions (exact error types, file existence, ledger scrubbing, git SHA format)
  Branch C — merged into the tests below with real subprocess / SQLite / filesystem execution.

Zero-Fake-Pass Invariant: no trivial mocks, no assert True stubs.
All assertions are against real file I/O, real SQLite rows, and real git object SHAs.
"""

from __future__ import annotations

import json
import re
import subprocess
import textwrap
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Module imports (fail-fast if the source files are missing or broken)
# ---------------------------------------------------------------------------
from tools.jev_clef_knowledge_compiler import (
    KnowledgeCompilerDB,
    LocalJEVEvaluator,
    SSRFError,
    SSRFGuard,
)
from tools.rearchitect_skills_and_root import (
    MAX_DESC_LEN,
    REMEDIATION_DESCRIPTIONS,
    apply_skill_description_fixes,
    audit_skills,
    classify_root_python_scripts,
)


# ===========================================================================
# 1. SSRFGuard
# ===========================================================================

class TestSSRFGuard:
    """Verify SSRF policy: allowlist, loopback, RFC1918, IMDS."""

    # --- ALLOWED -----------------------------------------------------------

    def test_allows_localhost_7777(self):
        url = "http://localhost:7777/api"
        result = SSRFGuard.validate_url(url)
        assert result == url, "Approved loopback URL must be returned unchanged."

    def test_allows_github_api(self):
        url = "https://api.github.com/repos"
        result = SSRFGuard.validate_url(url)
        assert result == url, "Allow-listed public host must pass through."

    def test_allows_export_arxiv(self):
        url = "https://export.arxiv.org/abs/2301.00001"
        result = SSRFGuard.validate_url(url)
        assert result == url

    # --- BLOCKED -----------------------------------------------------------

    def test_blocks_imds(self):
        """169.254.169.254 is the AWS/GCP IMDS; must be hard-blocked."""
        with pytest.raises(SSRFError, match="169.254.169.254"):
            SSRFGuard.validate_url("http://169.254.169.254/latest")

    def test_blocks_rfc1918_192_168(self):
        """192.168.x.x is RFC1918 private range."""
        with pytest.raises(SSRFError, match="192.168"):
            SSRFGuard.validate_url("http://192.168.1.1/")

    def test_blocks_localhost_non_7777(self):
        """localhost:8080 is not in the loopback allowlist."""
        with pytest.raises(SSRFError):
            SSRFGuard.validate_url("http://localhost:8080/")

    def test_blocks_rfc1918_10_net(self):
        with pytest.raises(SSRFError):
            SSRFGuard.validate_url("http://10.0.0.1/internal")

    def test_blocks_rfc1918_172_16(self):
        with pytest.raises(SSRFError):
            SSRFGuard.validate_url("http://172.16.0.1/")

    def test_blocks_non_allowlisted_public(self):
        with pytest.raises(SSRFError):
            SSRFGuard.validate_url("https://evil.com/steal")

    def test_blocks_non_http_scheme(self):
        with pytest.raises(SSRFError, match="scheme"):
            SSRFGuard.validate_url("ftp://api.github.com/repos")

    def test_blocks_empty_url(self):
        with pytest.raises(SSRFError, match="Empty"):
            SSRFGuard.validate_url("")


# ===========================================================================
# 2. LocalJEVEvaluator
# ===========================================================================

class TestLocalJEVEvaluator:
    """
    Verify dual-engine routing, dedup cache, secret scrubbing, and CLEF escalation.
    """

    def test_simple_prompt_routes_to_local_jev(self, tmp_path):
        """C < 2.2 → LOCAL_JEV, output_tokens == 0."""
        evaluator = LocalJEVEvaluator(
            dedup_cache_path=tmp_path / "cache.json",
            ledger_path=tmp_path / "ledger.jsonl",
        )
        result = evaluator.evaluate("fix the typo", files=[])
        assert result.engine == "LOCAL_JEV", f"Expected LOCAL_JEV, got {result.engine}"
        assert result.output_tokens == 0
        assert result.complexity < 2.2
        assert result.verdict == "PERMITTED"
        assert not result.cached, "First call must not be cached."

    def test_repeat_call_is_cached(self, tmp_path):
        """Second identical call must return cached=True."""
        evaluator = LocalJEVEvaluator(
            dedup_cache_path=tmp_path / "cache.json",
            ledger_path=tmp_path / "ledger.jsonl",
        )
        evaluator.evaluate("fix the typo", files=[])
        result2 = evaluator.evaluate("fix the typo", files=[])
        assert result2.cached is True, "Repeat call within TTL must hit dedup cache."
        assert result2.engine == "LOCAL_JEV"
        assert result2.output_tokens == 0

    def test_ledger_scrubs_secrets(self, tmp_path):
        """Secrets embedded in prompt must be redacted in action_ledger.jsonl."""
        evaluator = LocalJEVEvaluator(
            dedup_cache_path=tmp_path / "cache.json",
            ledger_path=tmp_path / "ledger.jsonl",
        )
        secret_prompt = "Update config: api_key=sk-abc123XYZXYZXYZXYZXYZ"
        evaluator.evaluate(secret_prompt, files=[])

        ledger_text = (tmp_path / "ledger.jsonl").read_text()
        assert "sk-abc123XYZXYZXYZXYZXYZ" not in ledger_text, (
            "Raw secret must not appear in the ledger — scrubber failed."
        )
        assert "[REDACTED]" in ledger_text or "REDACTED" in ledger_text, (
            "Scrubber must write a redaction placeholder."
        )

    def test_high_complexity_routes_to_clef_cloud(self, tmp_path):
        """
        C >= 2.2 → CLEF_CLOUD with <context>/<task>/<constraints> in enriched_spec.
        Force high complexity via keyword density.
        """
        evaluator = LocalJEVEvaluator(
            dedup_cache_path=tmp_path / "cache.json",
            ledger_path=tmp_path / "ledger.jsonl",
        )
        # 5 complex keywords saturate k_score=1.0; long prompt → p_score>0; total > 2.2
        long_prefix = "x " * 800  # ~1600 chars → p_score~0.4
        prompt = (
            long_prefix
            + "async await concurrent distributed Byzantine consensus "
            + "sharding cryptographic zero-knowledge formal-proof protocol "
            * 4
        )
        result = evaluator.evaluate(prompt, files=[])
        assert result.engine == "CLEF_CLOUD", (
            f"Expected CLEF_CLOUD for high-complexity prompt, got {result.engine} "
            f"(complexity={result.complexity})"
        )
        assert result.verdict == "ESCALATED"
        assert result.enriched_spec is not None
        assert "<context>" in result.enriched_spec
        assert "<task>" in result.enriched_spec
        assert "<constraints>" in result.enriched_spec

    def test_sha256_digest_is_hex(self, tmp_path):
        evaluator = LocalJEVEvaluator(
            dedup_cache_path=tmp_path / "cache.json",
            ledger_path=tmp_path / "ledger.jsonl",
        )
        result = evaluator.evaluate("hello world", files=[])
        assert re.fullmatch(r"[0-9a-f]{64}", result.sha256), (
            "sha256 must be a 64-char lowercase hex string."
        )

    def test_ast_check_raises_on_syntax_error(self, tmp_path):
        evaluator = LocalJEVEvaluator(
            dedup_cache_path=tmp_path / "cache.json",
            ledger_path=tmp_path / "ledger.jsonl",
        )
        with pytest.raises(SyntaxError):
            evaluator.evaluate("noop", python_source="def broken(:\n    pass")


# ===========================================================================
# 3. KnowledgeCompilerDB
# ===========================================================================

class TestKnowledgeCompilerDB:
    """
    Verify compile_python_file, record_decision, supersede_decision (tombstone),
    link_session_to_vault, and isolated_git_commit (preserving dirty working tree).
    """

    _SAMPLE_PY = textwrap.dedent("""\
        import os
        import hashlib

        class Foo:
            def bar(self):
                return hashlib.md5(b"x").hexdigest()

        def baz(x):
            return os.path.join(x, "y")
    """)

    def test_compile_python_file(self, tmp_path):
        """compile_python_file must insert FILE/CLASS/FUNCTION nodes and return correct counts."""
        src = tmp_path / "sample.py"
        src.write_text(self._SAMPLE_PY)
        db = KnowledgeCompilerDB(db_path=tmp_path / "kg.db")
        try:
            summary = db.compile_python_file(src, repo_name="test-repo")
        finally:
            db.close()

        assert summary["classes"] >= 1, "Must find at least 1 class (Foo)."
        assert summary["functions"] >= 2, "Must find at least 2 functions (bar, baz)."
        assert summary["imports"] >= 2, "Must record at least 2 imports (os, hashlib)."
        assert re.fullmatch(r"[0-9a-f]{64}", summary["sha256"])

    def test_compile_nonexistent_file_raises(self, tmp_path):
        db = KnowledgeCompilerDB(db_path=tmp_path / "kg.db")
        try:
            with pytest.raises(FileNotFoundError):
                db.compile_python_file(tmp_path / "ghost.py")
        finally:
            db.close()

    def test_record_and_supersede_decision(self, tmp_path):
        """record_decision inserts ACTIVE ADR; supersede_decision writes tombstone JSONL."""
        db = KnowledgeCompilerDB(db_path=tmp_path / "kg.db")
        tomb = tmp_path / "tombstones.jsonl"
        try:
            db.record_decision(
                adr_id="ADR-20260101-001",
                title="Use SQLite WAL",
                rationale="Concurrent read performance.",
                repo="hermes-agent",
            )
            # Verify it's ACTIVE in DB
            row = db.conn.execute(
                "SELECT status FROM decisions WHERE adr_id=?",
                ("ADR-20260101-001",),
            ).fetchone()
            assert row is not None
            assert row[0] == "ACTIVE"

            db.supersede_decision(
                old_adr_id="ADR-20260101-001",
                new_adr_id="ADR-20260601-002",
                new_title="Use PostgreSQL for HA",
                new_rationale="Need replication.",
                tombstone_file=tomb,
                repo="hermes-agent",
            )

            # Old ADR must be SUPERSEDED
            old = db.conn.execute(
                "SELECT status, tombstone_ref FROM decisions WHERE adr_id=?",
                ("ADR-20260101-001",),
            ).fetchone()
            assert old[0] == "SUPERSEDED"
            assert old[1] == "ADR-20260601-002"

            # New ADR must be ACTIVE
            new = db.conn.execute(
                "SELECT status FROM decisions WHERE adr_id=?",
                ("ADR-20260601-002",),
            ).fetchone()
            assert new[0] == "ACTIVE"

            # Tombstone file must exist and contain valid JSON
            assert tomb.exists(), "Tombstone JSONL must be written."
            lines = [l for l in tomb.read_text().splitlines() if l.strip()]
            assert len(lines) >= 1
            record = json.loads(lines[0])
            assert record["superseded_adr"] == "ADR-20260101-001"
            assert record["superseded_by"] == "ADR-20260601-002"
        finally:
            db.close()

    def test_link_session_to_vault(self, tmp_path):
        """link_session_to_vault must write wikilink with [[Session-...]] syntax."""
        db = KnowledgeCompilerDB(db_path=tmp_path / "kg.db")
        try:
            db.link_session_to_vault(
                session_id="sess-abc123",
                vault_note_path="/vault/notes/2026-10-17.md",
                adr_id="ADR-20260101-001",
            )
            row = db.conn.execute(
                "SELECT wikilink FROM session_links WHERE session_id=?",
                ("sess-abc123",),
            ).fetchone()
            assert row is not None
            wikilink = row[0]
            assert "[[Session-sess-abc123]]" in wikilink
            assert "[[ADR-ADR-20260101-001]]" in wikilink
        finally:
            db.close()

    def test_isolated_git_commit_preserves_dirty_tree(self, tmp_path):
        """
        isolated_git_commit must:
          · produce a valid 40-char hex commit SHA
          · NOT modify the working-tree dirty files (files NOT in target_files)
        """
        # Bootstrap a minimal git repo in tmp_path
        def git(*args):
            return subprocess.run(
                ["git", "-C", str(tmp_path), *args],
                capture_output=True, text=True, check=True,
            ).stdout.strip()

        git("init", "-b", "main")
        git("config", "user.email", "test@test.com")
        git("config", "user.name", "Test")

        # Create an initial commit so HEAD exists
        initial = tmp_path / "initial.py"
        initial.write_text("# initial\n")
        git("add", "initial.py")
        git("commit", "-m", "init")

        # File to commit via isolated path
        target = tmp_path / "target.py"
        target.write_text("print('hello')\n")

        # Dirty (unstaged) file that must NOT be disturbed
        dirty = tmp_path / "dirty.py"
        dirty.write_text("# UNSTAGED DIRTY CONTENT\n")

        sha = KnowledgeCompilerDB.isolated_git_commit(
            repo_path=tmp_path,
            target_files=[str(target)],
            message="isolated: add target.py",
        )

        # SHA must be a valid git object hash (40 hex chars)
        assert re.fullmatch(r"[0-9a-f]{40}", sha), (
            f"Commit SHA must be 40 lowercase hex chars, got: {sha!r}"
        )

        # dirty.py content must be untouched on disk
        assert dirty.read_text() == "# UNSTAGED DIRTY CONTENT\n", (
            "isolated_git_commit must NOT modify dirty working-tree files."
        )

        # HEAD now points to the new commit
        head_sha = git("rev-parse", "HEAD")
        assert head_sha == sha, "HEAD must be advanced to the isolated commit SHA."

        # The new commit must include target.py
        tree_files = git("ls-tree", "--name-only", sha)
        assert "target.py" in tree_files


# ===========================================================================
# 4. rearchitect_skills_and_root
# ===========================================================================

class TestRearchitectSkillsAndRoot:
    """
    Verify REMEDIATION_DESCRIPTIONS catalogue, audit_skills, apply_skill_description_fixes
    (tombstone write), and classify_root_python_scripts.
    """

    def test_remediation_descriptions_count_and_length(self):
        """Must have exactly 19 entries, each description <= 60 chars."""
        assert len(REMEDIATION_DESCRIPTIONS) == 19, (
            f"Expected 19 entries in REMEDIATION_DESCRIPTIONS, got {len(REMEDIATION_DESCRIPTIONS)}."
        )
        violations = {k: v for k, v in REMEDIATION_DESCRIPTIONS.items() if len(v) > MAX_DESC_LEN}
        assert not violations, (
            f"Descriptions exceed {MAX_DESC_LEN} chars: {violations}"
        )

    def test_audit_skills_on_empty_repo(self, tmp_path):
        """audit_skills on a repo with no SKILL.md files must return zero counts."""
        result = audit_skills(tmp_path)
        assert result["total_scanned"] == 0
        assert result["violations_count"] == 0
        assert result["duplicates_count"] == 0

    def test_audit_skills_detects_violation(self, tmp_path):
        """A SKILL.md with description > 60 chars must be flagged as a violation."""
        skill_dir = tmp_path / "skills" / "my-tool"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(
            "---\n"
            "name: my-tool\n"
            "description: This is a very long description that definitely exceeds the sixty character limit set by policy.\n"
            "---\n\n# My Tool\nDoes stuff.\n"
        )
        result = audit_skills(tmp_path)
        assert result["violations_count"] >= 1
        assert any("my-tool" in v["path"] for v in result["violations"])

    def test_apply_skill_description_fixes_writes_tombstone(self, tmp_path):
        """
        apply_skill_description_fixes with dry_run=False must:
          · rewrite description in SKILL.md
          · append a valid tombstone record to the JSONL
        """
        skill_dir = tmp_path / "skills" / "demo-skill"
        skill_dir.mkdir(parents=True)
        long_desc = "A" * 80  # clearly over 60
        (skill_dir / "SKILL.md").write_text(
            f"---\nname: demo-skill\ndescription: {long_desc}\n---\n\n# Demo\n"
        )
        tomb = tmp_path / "tombstones.jsonl"

        result = apply_skill_description_fixes(tmp_path, tomb, dry_run=False)

        assert result["fix_count"] >= 1
        applied = [f for f in result["fixes"] if f.get("status") == "applied"]
        assert len(applied) >= 1, "At least one fix must be applied in non-dry-run mode."

        # Tombstone file must exist and be valid JSONL
        assert tomb.exists(), "Tombstone JSONL must be written after non-dry-run apply."
        lines = [l for l in tomb.read_text().splitlines() if l.strip()]
        assert len(lines) >= 1
        record = json.loads(lines[0])
        assert record["verdict"] == "supersedes"
        assert record["dry_run"] is False

        # SKILL.md must have been rewritten with shorter description
        new_text = (skill_dir / "SKILL.md").read_text()
        new_desc_match = re.search(r"description:\s*(.+)", new_text)
        assert new_desc_match, "description: line must still be present after rewrite."
        assert len(new_desc_match.group(1).strip()) <= MAX_DESC_LEN, (
            "Rewritten description must be <= 60 chars."
        )

    def test_classify_root_python_scripts_proposes_moves(self, tmp_path):
        """Scripts with known prefixes must appear in proposals; protected stems excluded."""
        # Create classifiable scripts
        (tmp_path / "assemble_clips.py").write_text("# assembler\n")
        (tmp_path / "audit_quality.py").write_text("# auditor\n")
        (tmp_path / "render_output.py").write_text("# renderer\n")
        # Protected — must be excluded
        (tmp_path / "conftest.py").write_text("# protected\n")
        (tmp_path / "fleet_manager.py").write_text("# protected\n")

        result = classify_root_python_scripts(tmp_path)

        sources = [p["source"] for p in result["proposals"]]
        assert "assemble_clips.py" in sources
        assert "audit_quality.py" in sources
        assert "render_output.py" in sources
        # Protected stems must not appear in proposals
        assert "conftest.py" not in sources
        assert "fleet_manager.py" not in sources
        # No files are mutated
        assert result["note"] and "No files mutated" in result["note"]

    def test_compile_delta_skips_unchanged_and_recompiles_modified(self, tmp_path):
        """compile_delta must compile on first run, skip unchanged on second, and recompile modified."""
        db = KnowledgeCompilerDB(db_path=tmp_path / "kg.db")
        try:
            tools_dir = tmp_path / "tools"
            tools_dir.mkdir(parents=True)
            f1 = tools_dir / "mod_a.py"
            f1.write_text("def alpha():\n    return 1\n")

            res1 = db.compile_delta(repo_root=tmp_path, subdirs=["tools"])
            assert res1["scanned"] == 1
            assert res1["recompiled"] == 1
            assert res1["skipped_unchanged"] == 0

            res2 = db.compile_delta(repo_root=tmp_path, subdirs=["tools"])
            assert res2["scanned"] == 1
            assert res2["recompiled"] == 0
            assert res2["skipped_unchanged"] == 1

            f1.write_text("def alpha():\n    return 2\n")
            res3 = db.compile_delta(repo_root=tmp_path, subdirs=["tools"])
            assert res3["scanned"] == 1
            assert res3["recompiled"] == 1
            assert res3["skipped_unchanged"] == 0
        finally:
            db.close()

    def test_deduplicate_and_relocate_skills_archives_and_writes_tombstone(self, tmp_path):
        """deduplicate_and_relocate_skills must merge missing files, archive duplicate, and write tombstone."""
        from tools.rearchitect_skills_and_root import deduplicate_and_relocate_skills

        canon = tmp_path / ".agents" / "skills" / "manim-director"
        dup = tmp_path / "skills" / "creative" / "manim-director"
        canon.mkdir(parents=True)
        dup.mkdir(parents=True)
        (canon / "SKILL.md").write_text("---\nname: manim-director\ndescription: Canonical skill.\n---\n")
        (dup / "SKILL.md").write_text("---\nname: manim-director\ndescription: Duplicate skill.\n---\n")
        (dup / "extra_helper.py").write_text("# extra\n")

        tomb = tmp_path / "tombstones.jsonl"
        res = deduplicate_and_relocate_skills(tmp_path, tomb, dry_run=False)
        assert res["action_count"] >= 1
        assert not dup.exists(), "Duplicate skill directory must be archived/removed."
        assert (canon / "extra_helper.py").exists(), "Missing helper file from duplicate must be merged into canonical."
        assert tomb.exists(), "Tombstone JSONL must be written."

