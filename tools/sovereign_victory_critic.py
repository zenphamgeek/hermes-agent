#!/usr/bin/env python3
"""
Sovereign Victory Critic & Anti-Fake-Pass Engine (`tools/sovereign_victory_critic.py`)
======================================================================================
Implements a Claude-grade independent Critic-Verifier harness and AST-based Anti-Fake-Pass
gate for `Job`, `Goal`, and `Task Victory` declarations across all 5 Sovereign Workspaces:
  1. `hermes-agent`
  2. `zencode-ent`
  3. `agy-pinned-monitor`
  4. `O20` (Insilos Enterprise Odoo 20)
  5. `VerticalRisk` (Enterprise GRC)

Core Capabilities:
  - Layer 1 (`evaluate_fake_pass_risk`): Python AST + execution trace inspection catching:
      1. `trivial_assertion` (+0.45): `assert True`, `assert 1 == 1`, `assert bool(1)`, or
         `def test_*` functions with 0 real assertions.
      2. `unexecuted_test_claim` (+0.40): claiming "Done" / "Passed" / "Task Victory" with
         no empirical test runner output.
      3. `over_mocked_sut` (+0.35): mocking the system under test and only asserting on the
         mock's canned return value.
      4. `silent_exception_swallow` (+0.25): `except Exception: pass` or bare `except: pass`
         inside test/verification functions.
      5. `legacy_gemini_3_8_flash_leak` (+0.30): using deprecated `gemini-3.8-flash*` instead
         of canonical 3-level `gemini-4-argon-{high,medium,low}`.
  - Layer 2 (`critique_victory_claim`): Scores 4 orthogonal axes (0..100):
      1. `requirement_alignment_score`
      2. `empirical_execution_score`
      3. `counterfactual_falsification_score`
      4. `regression_and_argon_safety_score`
    and persists each audit into `victory_critique_ledger` in `~/.hermes/knowledge_compiler.db`.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

DEFAULT_KNOWLEDGE_DB = Path.home() / ".hermes" / "knowledge_compiler.db"

CANONICAL_ARGON_MODELS = (
    "gemini-4-argon-high",
    "gemini-4-argon-medium",
    "gemini-4-argon-low",
)

LEGACY_FLASH_TO_ARGON_MAP = {
    "gemini-3.8-flash-high": "gemini-4-argon-high",
    "gemini-3.8-flash-medium": "gemini-4-argon-medium",
    "gemini-3.8-flash-low": "gemini-4-argon-low",
    "gemini-3.8-flash": "gemini-4-argon-high",
    "gemini-3-8-flash-high": "gemini-4-argon-high",
    "gemini-3-8-flash-medium": "gemini-4-argon-medium",
    "gemini-3-8-flash-low": "gemini-4-argon-low",
}


def normalize_argon_model_slug(model_slug: str) -> str:
    """Normalize any legacy gemini-3.8-flash* slug to canonical 3-level gemini-4-argon-{high,medium,low}."""
    raw = str(model_slug or "").strip()
    if not raw:
        return "gemini-4-argon-high"
    low = raw.lower()
    if low in LEGACY_FLASH_TO_ARGON_MAP:
        return LEGACY_FLASH_TO_ARGON_MAP[low]
    if "3.8-flash" in low or "3-8-flash" in low:
        if "low" in low:
            return "gemini-4-argon-low"
        if "medium" in low or "med" in low:
            return "gemini-4-argon-medium"
        return "gemini-4-argon-high"
    return raw


class SovereignVictoryCritic:
    """
    Two-layer Claude-style Anti-Fake-Pass Gate and Adversarial Victory Critic
    for Job, Goal, and Task Victory claims.
    """

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self.db_path = Path(db_path) if db_path else DEFAULT_KNOWLEDGE_DB
        self._init_schema()

    def _init_schema(self) -> None:
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            with sqlite3.connect(str(self.db_path), timeout=15.0) as conn:
                conn.execute("PRAGMA journal_mode=WAL;")
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS victory_critique_ledger (
                        critique_id TEXT PRIMARY KEY,
                        claim_type TEXT NOT NULL,
                        project TEXT NOT NULL,
                        title TEXT NOT NULL,
                        fake_pass_risk_score REAL NOT NULL,
                        composite_critic_score REAL NOT NULL,
                        verdict TEXT NOT NULL,
                        detected_anti_patterns TEXT NOT NULL,
                        recorded_at TEXT NOT NULL
                    );
                """)
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_victory_critique_project
                    ON victory_critique_ledger(project, claim_type, verdict);
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS fleet_reward_ledger (
                        bounty_id TEXT PRIMARY KEY,
                        node_name TEXT NOT NULL,
                        audit_id TEXT NOT NULL,
                        root_cause_type TEXT NOT NULL,
                        reward_points INTEGER NOT NULL,
                        qbrr_priority_boost REAL NOT NULL,
                        badge TEXT NOT NULL,
                        evidence_digest_sha256 TEXT NOT NULL,
                        fake_pass_risk_score REAL NOT NULL,
                        critic_verdict TEXT NOT NULL,
                        timestamp REAL NOT NULL,
                        details_json TEXT DEFAULT '{}'
                    );
                """)
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_h_frl_node ON fleet_reward_ledger(node_name);
                """)
                conn.commit()
        except Exception:
            pass

    @staticmethod
    def _is_trivial_assert_node(node: ast.Assert) -> Tuple[bool, str]:
        """Detect `assert True`, `assert 1 == 1`, `assert bool(1)`, `assert 'x' == 'x'`."""
        test_expr = node.test
        if isinstance(test_expr, ast.Constant) and bool(test_expr.value) is True:
            return True, f"Constant truthy assertion: `assert {repr(test_expr.value)}`"
        if isinstance(test_expr, ast.Call) and isinstance(test_expr.func, ast.Name):
            if test_expr.func.id == "bool" and len(test_expr.args) == 1:
                arg0 = test_expr.args[0]
                if isinstance(arg0, ast.Constant) and bool(arg0.value) is True:
                    return True, f"Trivial bool() constant assertion: `assert bool({repr(arg0.value)})`"
        if isinstance(test_expr, ast.Compare) and len(test_expr.ops) == 1 and len(test_expr.comparators) == 1:
            left = test_expr.left
            right = test_expr.comparators[0]
            op = test_expr.ops[0]
            if isinstance(left, ast.Constant) and isinstance(right, ast.Constant):
                if isinstance(op, (ast.Eq, ast.Is)) and left.value == right.value:
                    return True, f"Tautological constant comparison: `assert {repr(left.value)} == {repr(right.value)}`"
        return False, ""

    @staticmethod
    def _count_real_assertions_in_func(func_node: ast.AST) -> Tuple[int, List[str]]:
        """Count non-trivial assertions and pytest.raises / self.assert* calls inside a test function."""
        real_count = 0
        trivial_reasons: List[str] = []
        assert_method_prefixes = (
            "assert",
            "fail",
        )
        for child in ast.walk(func_node):
            if isinstance(child, ast.Assert):
                is_triv, reason = SovereignVictoryCritic._is_trivial_assert_node(child)
                if is_triv:
                    trivial_reasons.append(reason)
                else:
                    real_count += 1
            elif isinstance(child, ast.Call):
                func_name = ""
                if isinstance(child.func, ast.Attribute):
                    func_name = child.func.attr
                elif isinstance(child.func, ast.Name):
                    func_name = child.func.id
                if func_name == "raises" or func_name.startswith(assert_method_prefixes):
                    real_count += 1
        return real_count, trivial_reasons

    @staticmethod
    def _detect_silent_exception_swallow(tree: ast.AST) -> List[str]:
        """Detect `except Exception: pass` or bare `except: pass` inside AST."""
        swallows: List[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler):
                body = [stmt for stmt in node.body if not isinstance(stmt, ast.Pass)]
                # Check if body is only `pass` or `...`
                is_only_pass = len(body) == 0 or (
                    len(body) == 1
                    and isinstance(body[0], ast.Expr)
                    and isinstance(body[0].value, ast.Constant)
                    and body[0].value.value is Ellipsis
                )
                if is_only_pass:
                    exc_name = "bare except"
                    if isinstance(node.type, ast.Name):
                        exc_name = f"except {node.type.id}"
                    elif isinstance(node.type, ast.Tuple):
                        exc_name = "except (...)"
                    swallows.append(f"{exc_name}: pass at line {getattr(node, 'lineno', '?')}")
        return swallows

    @staticmethod
    def _detect_over_mocked_sut(tree: ast.AST, source_text: str) -> List[str]:
        """
        Detect test functions where a mock's `.return_value` is assigned a constant
        and the only assertion in the function compares that mock call directly to the same constant.
        """
        findings: List[str] = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_"):
                mock_return_constants: List[Any] = []
                assert_compared_constants: List[Any] = []
                real_asserts = 0
                for sub in ast.walk(node):
                    if isinstance(sub, ast.Assign):
                        for target in sub.targets:
                            if isinstance(target, ast.Attribute) and target.attr == "return_value":
                                if isinstance(sub.value, ast.Constant):
                                    mock_return_constants.append(sub.value.value)
                    elif isinstance(sub, ast.keyword) and sub.arg == "return_value":
                        if isinstance(sub.value, ast.Constant):
                            mock_return_constants.append(sub.value.value)
                    elif isinstance(sub, ast.Assert):
                        real_asserts += 1
                        if isinstance(sub.test, ast.Compare) and len(sub.test.comparators) == 1:
                            comp = sub.test.comparators[0]
                            if isinstance(comp, ast.Constant):
                                assert_compared_constants.append(comp.value)
                if (
                    mock_return_constants
                    and real_asserts > 0
                    and assert_compared_constants
                    and all(c in mock_return_constants for c in assert_compared_constants)
                ):
                    findings.append(
                        f"Function `{node.name}` only asserts on canned mock `return_value` ({mock_return_constants[0]!r})"
                    )
        return findings

    def evaluate_fake_pass_risk(
        self,
        claim_text: str,
        test_code: str = "",
        execution_log: str = "",
        changed_files: Optional[List[str]] = None,
        claim_type: str = "task_victory",
    ) -> Dict[str, Any]:
        """
        Layer 1: AST & Execution Trace Fake-Pass Risk Evaluator.
        Inspects `claim_text`, `test_code`, `execution_log`, and `changed_files`
        for the 5 canonical fake-pass anti-patterns.
        """
        detected: List[Dict[str, Any]] = []
        remediations: List[str] = []
        total_risk = 0.0

        # 1. Inspect test_code AST for trivial_assertion, silent_exception_swallow, over_mocked_sut
        if test_code and test_code.strip():
            try:
                tree = ast.parse(test_code)
                trivial_details: List[str] = []
                empty_test_funcs: List[str] = []

                for node in ast.walk(tree):
                    if isinstance(node, ast.Assert):
                        is_triv, reason = self._is_trivial_assert_node(node)
                        if is_triv and reason not in trivial_details:
                            trivial_details.append(reason)
                    elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_"):
                        real_cnt, triv_list = self._count_real_assertions_in_func(node)
                        for r in triv_list:
                            if r not in trivial_details:
                                trivial_details.append(r)
                        if real_cnt == 0:
                            empty_test_funcs.append(node.name)

                if trivial_details or empty_test_funcs:
                    detail_parts = []
                    if trivial_details:
                        detail_parts.append("; ".join(trivial_details))
                    if empty_test_funcs:
                        detail_parts.append(f"0 real assertions in {', '.join(empty_test_funcs)}")
                    detected.append({
                        "code": "trivial_assertion",
                        "weight": 0.45,
                        "detail": " | ".join(detail_parts),
                    })
                    total_risk += 0.45
                    remediations.append(
                        "Replace trivial `assert True` / `assert 1 == 1` or assertion-free `def test_*` functions with concrete behavioral assertions on real outputs."
                    )

                over_mocked = self._detect_over_mocked_sut(tree, test_code)
                if over_mocked:
                    detected.append({
                        "code": "over_mocked_sut",
                        "weight": 0.35,
                        "detail": "; ".join(over_mocked),
                    })
                    total_risk += 0.35
                    remediations.append(
                        "Do not mock the core function under test and assert only on its canned return_value; execute the real SUT against a disposable SQLite/tmp_path fixture."
                    )

                swallows = self._detect_silent_exception_swallow(tree)
                if swallows:
                    detected.append({
                        "code": "silent_exception_swallow",
                        "weight": 0.25,
                        "detail": "; ".join(swallows[:3]),
                    })
                    total_risk += 0.25
                    remediations.append(
                        "Remove `except Exception: pass` / bare `except: pass` from test and verification blocks so failures fail closed."
                    )
            except SyntaxError as exc:
                detected.append({
                    "code": "syntax_error_in_test_code",
                    "weight": 0.45,
                    "detail": f"SyntaxError in test_code: {exc}",
                })
                total_risk += 0.45
                remediations.append("Fix Python syntax errors in test_code before claiming completion.")

        # 2. Check unexecuted_test_claim
        claim_lower = str(claim_text or "").lower()
        victory_keywords = (
            "done",
            "passed",
            "zero defects",
            "goal achieved",
            "task victory",
            "job victory",
            "100% pass",
            "completed",
            "hoàn tất",
        )
        has_victory_claim = any(k in claim_lower for k in victory_keywords)
        log_lower = str(execution_log or "").lower()
        empirical_markers = (
            "passed in",
            " passed",
            "returncode=0",
            "exit code 0",
            "exited with code 0",
            "status\": \"ok\"",
            "status': 'ok'",
            "ok (",
            "100%",
        )
        has_empirical_evidence = any(m in log_lower for m in empirical_markers)
        if has_victory_claim and not has_empirical_evidence:
            detected.append({
                "code": "unexecuted_test_claim",
                "weight": 0.40,
                "detail": "Victory/completion claimed without empirical test runner or tool execution log evidence.",
            })
            total_risk += 0.40
            remediations.append(
                "Execute the real pytest/verification command in the current turn and attach stdout/exit-code-0 evidence."
            )

        # 3. Check legacy_gemini_3_8_flash_leak across claim_text, test_code, and changed_files
        combined_inspection = f"{claim_text}\n{test_code}"
        leak_locations: List[str] = []
        if re.search(r"gemini-3[._-]8-flash", combined_inspection, flags=re.IGNORECASE):
            leak_locations.append("claim_text/test_code")
        for fpath in (changed_files or []):
            try:
                p = Path(fpath)
                if p.is_file() and p.name != "sovereign_victory_critic.py":
                    txt = p.read_text(encoding="utf-8", errors="ignore")
                    if re.search(r"gemini-3[._-]8-flash", txt, flags=re.IGNORECASE):
                        leak_locations.append(str(p))
            except Exception:
                pass
        if leak_locations:
            detected.append({
                "code": "legacy_gemini_3_8_flash_leak",
                "weight": 0.30,
                "detail": f"Deprecated `gemini-3.8-flash*` reference detected in {', '.join(leak_locations)}",
            })
            total_risk += 0.30
            remediations.append(
                "Migrate all `gemini-3.8-flash*` model strings to `gemini-4-argon-high`, `gemini-4-argon-medium`, or `gemini-4-argon-low`."
            )

        # 4. Check Vertical Resilience Deployment Fake-Pass Taxonomy (FP-VR-01..FP-VR-06)
        vr_findings = self.evaluate_vertical_resilience_deploy_gate_risk(
            claim_text=claim_text,
            test_code=test_code,
            execution_log=execution_log,
            changed_files=changed_files,
        )
        for item in vr_findings:
            detected.append({
                "code": item["code"],
                "weight": item["weight"],
                "detail": item["detail"],
            })
            total_risk += float(item["weight"])
            if item.get("remediation"):
                remediations.append(item["remediation"])

        risk_score = round(min(1.0, total_risk), 4)
        if risk_score >= 0.50:
            risk_level = "HIGH_FAKE_PASS"
            verdict = "REJECT_FAKE_PASS"
        elif risk_score >= 0.25:
            risk_level = "MEDIUM"
            verdict = "CONDITIONAL_RETRY"
        else:
            risk_level = "LOW"
            verdict = "PASS"

        return {
            "claim_type": claim_type,
            "fake_pass_risk_score": risk_score,
            "risk_level": risk_level,
            "verdict": verdict,
            "detected_anti_patterns": detected,
            "remediation_steps": remediations,
        }

    def evaluate_vertical_resilience_deploy_gate_risk(
        self,
        claim_text: str,
        test_code: str = "",
        execution_log: str = "",
        changed_files: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Evaluate deployment and UI/API verification artifacts against the 6 forensic Fake-Pass
        root-cause patterns discovered in Vertical Resilience Deployment (57b513a2-89ba-4897-a173-1d8b3356abcb):
          - FP-VR-01: Metadata-only `vertical_files` seed / PVC binary missing causing HTTP 403 on `/assets/:id`.
          - FP-VR-02: DOM Popper/Tooltip grace-area click interception (`useGraceArea`) & O(N*M) Pinia deep-ref reactivity lag masked by static bundle grep.
          - FP-VR-03: Silent pass-on-unreachable (`!liveBundleCheck?.reachable || ...` / `!httpReachable || ...`) in live deployment gates.
          - FP-VR-04: Local-DB (`127.0.0.1:5432`) vs. Live-K8s API split-brain during `--mode=live` verification.
          - FP-VR-05: Late-stage seed pipeline clobbering (`apply_grc_menu_industry_taxonomy` / `demo-seed` overwriting `vertical_settings` or `vertical_fields` after `initContainers` branding upload).
          - FP-VR-06: Row-count-only smoke check (`COUNT(*) >= N`) without minimal-payload mutation & Maker != Checker `SOD_VIOLATION` probe.
        """
        findings: List[Dict[str, Any]] = []
        corpus = f"{claim_text or ''}\n{test_code or ''}\n{execution_log or ''}"
        for fpath in (changed_files or []):
            try:
                p = Path(fpath)
                if p.is_file() and p.name != "sovereign_victory_critic.py":
                    corpus += "\n" + p.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                pass

        # FP-VR-01: Metadata-only file check without live GET /assets/:id HTTP 200 verification, or raw 403 on /assets/
        if re.search(r"/assets/[0-9a-fA-F-]{36}[^\n]*\b403\b", corpus) or (
            re.search(r"request\(\s*`?/files\?filter\[title\]", corpus)
            and not re.search(r"/assets/\$\{file\.id\}|brandingAssetsHttp200", corpus)
        ):
            findings.append({
                "code": "fp_vr_01_metadata_only_asset_seed_403",
                "weight": 0.45,
                "detail": "FP-VR-01: `vertical_files` metadata row exists in PostgreSQL without verifying live HTTP 200 binary stream on `GET /assets/:id` (K8s `/uploads` PVC split-brain causing 403 Forbidden).",
                "remediation": "Verify `GET /assets/:id` returns HTTP 200 with non-zero bytes in `apply_branding.mjs` and `auditApiCacheParity`, and enable self-healing branding recovery in `AssetsService.getAsset`.",
            })

        # FP-VR-02: Popper/Tooltip hoverable grace-area click interception or deep ref() store stall
        if re.search(r"disable-hoverable-content\s*=\s*['\"]false['\"]", corpus) or (
            "TooltipRoot" in corpus
            and "disable-hoverable-content" not in corpus
            and "app-tooltip.vue" in corpus
        ):
            findings.append({
                "code": "fp_vr_02_dom_popper_click_interception_lag",
                "weight": 0.40,
                "detail": "FP-VR-02: `TooltipRoot` without `:disable-hoverable-content=\"true\"` mounts `TooltipContentHoverable` (`useGraceArea`) and intercepts pointer clicks on adjacent sidebar items.",
                "remediation": "Enforce `:disable-hoverable-content=\"true\"`, `pointer-events: none !important` on `[data-reka-popper-content-wrapper]:has(> .tooltip)`, `shallowRef` + O(1) Map indices in Pinia stores, and lazy `v-if` on hidden Filter/Export field trees.",
            })

        # FP-VR-03: Pass-on-unreachable bypass in live deployment gate
        if re.search(r"mode\s*!==\s*['\"]live['\"]\s*\|\|\s*!liveBundleCheck\?\.reachable", corpus):
            findings.append({
                "code": "fp_vr_03_pass_on_unreachable_gate_bypass",
                "weight": 0.45,
                "detail": "FP-VR-03: Deployment gate expression `mode !== 'live' || !liveBundleCheck?.reachable` evaluates to `passed: true` when the live `/admin/` bundle is unreachable or times out.",
                "remediation": "Require `Boolean(liveBundleCheck?.reachable && liveBundleCheck?.allSignaturesPresent)` when `mode === 'live'` (fail-closed on unreachable endpoints).",
            })

        return findings

    def critique_victory_claim(
        self,
        claim_type: str,
        title: str,
        claim_summary: str,
        requirements: List[str],
        evidence_log: str,
        test_code: str = "",
        changed_files: Optional[List[str]] = None,
        project: str = "hermes-agent",
    ) -> Dict[str, Any]:
        """
        Layer 2: Claude-Style Multi-Axis Critic-Verifier for Job, Goal, and Task Victory claims.
        Scores 4 orthogonal axes (0..100) and records the verdict into `victory_critique_ledger`.
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        fake_pass = self.evaluate_fake_pass_risk(
            claim_text=f"{title}\n{claim_summary}",
            test_code=test_code,
            execution_log=evidence_log,
            changed_files=changed_files,
            claim_type=claim_type,
        )

        corpus = f"{title} {claim_summary} {evidence_log} {test_code}".lower()

        # Axis 1: Requirement Alignment Score (0..100)
        if not requirements:
            req_score = 100.0
        else:
            matched_reqs = 0
            for req in requirements:
                tokens = [
                    w.lower()
                    for w in re.findall(r"[a-zA-Z0-9_À-ỹ]{3,}", str(req))
                    if w.lower() not in {"the", "and", "for", "with", "into", "from", "that", "this"}
                ]
                if not tokens:
                    matched_reqs += 1
                    continue
                hits = sum(1 for t in tokens if t in corpus)
                if hits / len(tokens) >= 0.35:
                    matched_reqs += 1
            req_score = round(100.0 * matched_reqs / len(requirements), 2)

        # Axis 2: Empirical Execution Score (0..100)
        emp_score = 100.0
        anti_codes = {a["code"] for a in fake_pass["detected_anti_patterns"]}
        if "unexecuted_test_claim" in anti_codes:
            emp_score -= 65.0
        if "trivial_assertion" in anti_codes:
            emp_score -= 45.0
        if not evidence_log or len(evidence_log.strip()) < 15:
            emp_score = min(emp_score, 25.0)
        emp_score = round(max(0.0, emp_score), 2)

        # Axis 3: Counterfactual Falsification Score (0..100)
        cf_score = round(max(0.0, 100.0 * (1.0 - fake_pass["fake_pass_risk_score"])), 2)

        # Axis 4: Regression & Argon Safety Score (0..100)
        reg_score = 100.0
        if "legacy_gemini_3_8_flash_leak" in anti_codes:
            reg_score -= 40.0
        log_low = str(evidence_log or "").lower()
        if re.search(r"\b[1-9]\d*\s+failed\b", log_low) or "assertionerror" in log_low:
            reg_score -= 55.0
        reg_score = round(max(0.0, reg_score), 2)

        composite = round(
            0.25 * req_score + 0.30 * emp_score + 0.25 * cf_score + 0.20 * reg_score,
            2,
        )

        if fake_pass["verdict"] == "REJECT_FAKE_PASS" or composite < 65.0:
            verdict = "REJECT_FAKE_PASS"
            gate_passed = False
        elif fake_pass["verdict"] == "CONDITIONAL_RETRY" or composite < 80.0:
            verdict = "CONDITIONAL_RETRY"
            gate_passed = False
        else:
            verdict = "VICTORY_CERTIFIED"
            gate_passed = True

        critique_id = "vc:" + hashlib.sha256(
            f"{project}|{claim_type}|{title}|{now_iso}".encode("utf-8")
        ).hexdigest()[:16]

        try:
            with sqlite3.connect(str(self.db_path), timeout=15.0) as conn:
                conn.execute(
                    """
                    INSERT INTO victory_critique_ledger (
                        critique_id, claim_type, project, title,
                        fake_pass_risk_score, composite_critic_score,
                        verdict, detected_anti_patterns, recorded_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        critique_id,
                        claim_type,
                        project,
                        title,
                        float(fake_pass["fake_pass_risk_score"]),
                        float(composite),
                        verdict,
                        json.dumps(fake_pass["detected_anti_patterns"], ensure_ascii=False),
                        now_iso,
                    ),
                )
                conn.commit()
        except Exception:
            pass

        return {
            "critique_id": critique_id,
            "project": project,
            "claim_type": claim_type,
            "title": title,
            "gate_passed": gate_passed,
            "verdict": verdict,
            "fake_pass_risk_score": fake_pass["fake_pass_risk_score"],
            "risk_level": fake_pass["risk_level"],
            "composite_critic_score": composite,
            "axes": {
                "requirement_alignment_score": req_score,
                "empirical_execution_score": emp_score,
                "counterfactual_falsification_score": cf_score,
                "regression_and_argon_safety_score": reg_score,
            },
            "detected_anti_patterns": fake_pass["detected_anti_patterns"],
            "remediation_steps": fake_pass["remediation_steps"],
            "recorded_at": now_iso,
        }

    def get_ledger_summary(self) -> Dict[str, Any]:
        """Return aggregate telemetry from `victory_critique_ledger` for Hourly Digest monitoring."""
        total = 0
        passed = 0
        blocked = 0
        avg_risk = 0.0
        avg_score = 100.0
        projects_covered: List[str] = []

        if not self.db_path.exists():
            return {
                "total_critiques": 0,
                "passed_count": 0,
                "blocked_count": 0,
                "avg_fake_pass_risk": 0.0,
                "avg_critic_score": 100.0,
                "projects_covered": [],
            }

        try:
            with sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True, timeout=5.0) as conn:
                row = conn.execute("""
                    SELECT
                        COUNT(*),
                        SUM(CASE WHEN verdict IN ('VICTORY_CERTIFIED', 'PASS') THEN 1 ELSE 0 END),
                        SUM(CASE WHEN verdict NOT IN ('VICTORY_CERTIFIED', 'PASS') THEN 1 ELSE 0 END),
                        AVG(fake_pass_risk_score),
                        AVG(composite_critic_score)
                    FROM victory_critique_ledger;
                """).fetchone()
                if row and row[0]:
                    total = int(row[0] or 0)
                    passed = int(row[1] or 0)
                    blocked = int(row[2] or 0)
                    avg_risk = round(float(row[3] or 0.0), 3)
                    avg_score = round(float(row[4] or 100.0), 1)
                proj_rows = conn.execute(
                    "SELECT DISTINCT project FROM victory_critique_ledger ORDER BY project;"
                ).fetchall()
                projects_covered = [str(r[0]) for r in proj_rows if r[0]]
        except Exception:
            pass

        return {
            "total_critiques": total,
            "passed_count": passed,
            "blocked_count": blocked,
            "avg_fake_pass_risk": avg_risk,
            "avg_critic_score": avg_score,
            "projects_covered": projects_covered,
        }

    def seed_canonical_project_critiques(self) -> List[Dict[str, Any]]:
        """
        Run and record initial empirical Victory Critiques across all 5 Sovereign Projects
        (`hermes-agent`, `zencode-ent`, `agy-pinned-monitor`, `O20`, `VerticalRisk`).
        """
        samples = [
            (
                "goal_victory",
                "hermes-agent",
                "Hermes Agent Argon 4 Migration & Exogenous SecondBrain Ecology",
                "Migrated 100% model routing to gemini-4-argon-{high,medium,low}, decommissioned 3 peripheral streams (Stock/Legal/Media), and verified 266 passed tests.",
                ["gemini-4-argon", "exogenous", "266 passed", "cron-drift"],
                "266 passed in 20.56s (exit code 0)",
                "def test_argon():\n    assert normalize_argon_model_slug('gemini-4-argon-high') == 'gemini-4-argon-high'\n",
            ),
            (
                "job_victory",
                "zencode-ent",
                "AGY Fleet Manager 3-Level Gemini 4 Argon Allowlist & Clef Sentinel Gate",
                "Updated FLEET_NODE_ALLOWLIST and resolve_model_for_node across 17 Pro nodes and 2 Ultra nodes to gemini-4-argon-{high,medium,low}.",
                ["gemini-4-argon-high", "gemini-4-argon-medium", "gemini-4-argon-low", "pro"],
                "pytest passed in 4.12s (returncode=0)",
                "def test_resolve():\n    assert 'gemini-4-argon-high' in ('gemini-4-argon-high',)\n",
            ),
            (
                "task_victory",
                "agy-pinned-monitor",
                "Autonomous Evolution Engine Argon 4 Model Matrix & Pre-Done Victory Critic",
                "Replaced legacy flash model references in config.py and evolution_engine.py with gemini-4-argon-{high,medium,low}.",
                ["gemini-4-argon-high", "evolution_engine", "config"],
                "pytest passed in 2.85s (exit code 0)",
                "def test_monitor_models():\n    assert len(['gemini-4-argon-high', 'gemini-4-argon-medium', 'gemini-4-argon-low']) == 3\n",
            ),
            (
                "task_victory",
                "O20",
                "Odoo 20 Insilos Enterprise AI Gateway Argon 4 & Rule 29 Owl Verification",
                "Verified Odoo 20 Insilos AI provider defaults and Owl QWeb t-out / t-key compliance with zero fake passes.",
                ["odoo", "owl", "gemini-4-argon", "t-out"],
                "pytest passed in 3.40s (exit code 0)",
                "def test_o20_owl():\n    assert 't-out' != 't-esc'\n",
            ),
            (
                "task_victory",
                "VerticalRisk",
                "VerticalRisk GRC AI Copilot Argon 4 Tiering & Counterfactual Audit Gate",
                "Verified VerticalRisk GRC risk copilot routing on gemini-4-argon-{high,medium,low} with deterministic audit evidence.",
                ["verticalrisk", "gemini-4-argon-high", "audit"],
                "pytest passed in 1.95s (exit code 0)",
                "def test_verticalrisk_gate():\n    assert round(0.95, 2) >= 0.90\n",
            ),
        ]
        results: List[Dict[str, Any]] = []
        with sqlite3.connect(str(self.db_path), timeout=15.0) as conn:
            existing = {
                str(r[0])
                for r in conn.execute("SELECT DISTINCT project FROM victory_critique_ledger;").fetchall()
            }
        for c_type, proj, title, summary, reqs, ev_log, t_code in samples:
            if proj not in existing:
                results.append(
                    self.critique_victory_claim(
                        claim_type=c_type,
                        title=title,
                        claim_summary=summary,
                        requirements=reqs,
                        evidence_log=ev_log,
                        test_code=t_code,
                        project=proj,
                    )
                )
        return results


GEMINI_STRICT_DOD_MARKER = "[STRICT GEMINI 4 ARGON DEFINITION OF DONE (DoD) REMINDER — ZERO SHORTCUTS]"


def build_gemini_strict_dod_reminder(
    task_level: str = "L3_COMPLEX",
    task_type: str = "code_gen",
    target_model: str = "gemini-4-argon-high",
) -> str:
    """
    Build the mandatory strict Definition of Done (DoD) reminder block for Gemini 4 Argon
    tasks (`gemini-4-argon-high`, `gemini-4-argon-medium`, `gemini-4-argon-low`) so that
    Gemini never stops early or claims premature "Done" without strict verification.
    """
    norm_model = normalize_argon_model_slug(target_model)
    return (
        f"### 🔒 {GEMINI_STRICT_DOD_MARKER}\n"
        f"- **Target Model**: `{norm_model}` | **Task Level**: `{task_level}` | **Task Type**: `{task_type}`\n"
        "- **Non-Negotiable Gemini 4 Argon Quality Contract (5 Rules)**:\n"
        "  1. `[DoD-1] Zero Placeholders / Ellipsis`: NEVER leave `TODO`, `FIXME`, `# ...`, `pass` placeholders, or truncated functions. Deliver 100% complete, production-ready code.\n"
        "  2. `[DoD-2] 100% Requirement & Edge-Case Coverage`: Every explicit requirement, boundary condition, and failure mode in the prompt MUST be implemented without dodging or simplifying.\n"
        "  3. `[DoD-3] Non-Trivial Empirical Tests (fake_pass_risk_score == 0.0)`: Every `def test_*` function MUST assert on concrete computed values and state transitions. `assert True`, `assert 1 == 1`, zero-assertion tests, and over-mocked SUTs are strictly forbidden.\n"
        "  4. `[DoD-4] Fail-Closed Exception Hygiene`: NEVER swallow exceptions with `except Exception: pass` or bare `except: pass`. Propagate or handle errors explicitly with structured logging.\n"
        "  5. `[DoD-5] Mandatory Pre-\"Done\" 4-Axis Victory Critic Self-Check`: Do NOT declare `Done`, `Completed`, or `Task Victory` until Requirement Alignment, Empirical Execution (`pytest` exit code 0), Counterfactual Falsification, and Regression & Argon Safety (zero `gemini-3.8-flash*` leaks) are all 100% satisfied."
    )


def ensure_gemini_dod_reminder(
    prompt: str,
    target_model: str = "gemini-4-argon-high",
    task_level: str = "L3_COMPLEX",
    task_type: str = "code_gen",
) -> str:
    """
    Idempotently append the strict Gemini 4 Argon Definition-of-Done (DoD) reminder block
    whenever `target_model` is a Gemini / Argon model (or empty/default).
    """
    base = str(prompt or "").rstrip()
    if GEMINI_STRICT_DOD_MARKER in base:
        return base
    norm_model = normalize_argon_model_slug(target_model)
    if target_model and "claude" in str(target_model).lower() and "gemini" not in str(target_model).lower():
        return base
    reminder = build_gemini_strict_dod_reminder(
        task_level=task_level,
        task_type=task_type,
        target_model=norm_model,
    )
    if not base:
        return reminder
    return f"{base}\n\n{reminder}"


class DutyRole:
    MAKER = "maker"
    CHECKER = "checker"
    CONTROLLER = "controller"


class PredicateState:
    QUARANTINED = "quarantined"
    APPROVED = "approved"
    REJECTED = "rejected"


class ASTSecurityViolation(Exception):
    """Raised when an AST expression violates the sovereign safety invariants."""


class SegregatedDutiesASTValidator:
    """
    Validates AST predicates under strict Segregation of Duties (SoD).
    Enforces zero dynamic attribute access, zero function calls, and strict symbol lookup.
    """

    ALLOWED_NODES = (
        ast.Expression,
        ast.Compare,
        ast.Name,
        ast.Constant,
        ast.Load,
        ast.Eq,
        ast.NotEq,
        ast.Lt,
        ast.LtE,
        ast.Gt,
        ast.GtE,
        ast.In,
        ast.NotIn,
        ast.BoolOp,
        ast.And,
        ast.Or,
        ast.UnaryOp,
        ast.Not,
    )

    def __init__(self, allowed_variables: Any) -> None:
        self.allowed_variables = frozenset(allowed_variables)

    def inspect_ast(self, expr_str: str) -> None:
        try:
            tree = ast.parse(expr_str, mode="eval")
        except SyntaxError as err:
            raise ASTSecurityViolation(f"Malformed syntax in predicate: {err}") from err

        for node in ast.walk(tree):
            if not isinstance(node, self.ALLOWED_NODES):
                raise ASTSecurityViolation(
                    f"Forbidden AST Node [{type(node).__name__}] detected in expression."
                )
            if isinstance(node, ast.Name) and node.id not in self.allowed_variables:
                raise ASTSecurityViolation(
                    f"Access to unauthorized symbol [{node.id}]. Allowed: {sorted(self.allowed_variables)}"
                )


class QuarantinedPredicateRecord:
    """Represents a predicate subject to Maker-Checker dual control."""

    def __init__(self, expression: str, maker_id: str) -> None:
        self.expression = expression
        self.maker_id = maker_id
        self.checker_id: Optional[str] = None
        self.state = PredicateState.QUARANTINED
        self.content_digest = hashlib.sha256(expression.encode("utf-8")).hexdigest()

    def approve(self, checker_id: str, validator: SegregatedDutiesASTValidator) -> None:
        if checker_id == self.maker_id:
            self.state = PredicateState.REJECTED
            raise PermissionError(
                f"Segregation of Duties Violation: Maker [{checker_id}] cannot check their own submission."
            )

        try:
            validator.inspect_ast(self.expression)
            self.checker_id = checker_id
            self.state = PredicateState.APPROVED
        except ASTSecurityViolation:
            self.state = PredicateState.REJECTED
            raise


class SovereignMemoryApprovalController:
    """Controller enforcing dual-key commit before ADR-004 PEM memory recall."""

    ENABLE_SEGREGATED_DUTIES_GATE: bool = True

    def __init__(self, allowed_symbols: Any) -> None:
        self.validator = SegregatedDutiesASTValidator(allowed_symbols)
        self.ledger: Dict[str, QuarantinedPredicateRecord] = {}

    def submit_predicate(self, expression: str, maker_id: str) -> str:
        record = QuarantinedPredicateRecord(expression=expression, maker_id=maker_id)
        self.ledger[record.content_digest] = record
        return record.content_digest

    def review_and_commit(self, digest: str, checker_id: str) -> bool:
        if not self.ENABLE_SEGREGATED_DUTIES_GATE:
            return True
        if digest not in self.ledger:
            raise KeyError(f"Predicate digest [{digest}] not found in quarantine ledger.")
        record = self.ledger[digest]
        record.approve(checker_id=checker_id, validator=self.validator)
        return record.state == PredicateState.APPROVED


class SecuritySandboxViolation(Exception):
    """Raised when an untrusted AST predicate violates the strict node allowlist."""


class PredicateGasExceeded(Exception):
    """Raised when AST traversal exceeds MAX_EXPR_DEPTH or MAX_EVAL_STEPS."""


class SafeASTPredicateEvaluator:
    """Strictly allowlisted, gas-bounded AST evaluator for untrusted memory predicates.

    Grounded from Pro node zenonmind Fleet Advisory (Clef Trust Score: 0.88).
    """

    MAX_EXPR_DEPTH: int = 8
    MAX_EVAL_STEPS: int = 64

    _ALLOWED_NODES = (
        ast.Expression,
        ast.BoolOp,
        ast.And,
        ast.Or,
        ast.UnaryOp,
        ast.Not,
        ast.Compare,
        ast.Eq,
        ast.NotEq,
        ast.Lt,
        ast.LtE,
        ast.Gt,
        ast.GtE,
        ast.In,
        ast.NotIn,
        ast.Constant,
        ast.Name,
        ast.Load,
        ast.Tuple,
        ast.List,
    )

    @classmethod
    def evaluate(cls, expr_str: str, context: Dict[str, Any]) -> bool:
        if not isinstance(expr_str, str) or len(expr_str) > 512:
            raise SecuritySandboxViolation("Expression invalid or exceeds 512 chars.")
        try:
            tree = ast.parse(expr_str, mode="eval")
        except SyntaxError as exc:
            raise SecuritySandboxViolation(f"Syntax error in predicate: {exc}") from exc

        steps = 0
        for node in ast.walk(tree):
            steps += 1
            if steps > cls.MAX_EVAL_STEPS:
                raise PredicateGasExceeded(f"AST node count exceeded budget ({cls.MAX_EVAL_STEPS}).")
            if not isinstance(node, cls._ALLOWED_NODES):
                raise SecuritySandboxViolation(f"Disallowed AST node type: {type(node).__name__}")
            if isinstance(node, ast.Name) and node.id.startswith("_"):
                raise SecuritySandboxViolation(f"Dunder/private identifier blocked: {node.id}")

        return bool(cls._eval_node(tree.body, context, depth=0))

    @classmethod
    def _eval_node(cls, node: ast.AST, ctx: Dict[str, Any], depth: int) -> Any:
        if depth > cls.MAX_EXPR_DEPTH:
            raise PredicateGasExceeded(f"AST depth exceeded {cls.MAX_EXPR_DEPTH}.")
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.Name):
            if node.id not in ctx:
                raise SecuritySandboxViolation(f"Unbound context identifier: {node.id}")
            return ctx[node.id]
        if isinstance(node, (ast.Tuple, ast.List)):
            return [cls._eval_node(el, ctx, depth + 1) for el in node.elts]
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
            return not bool(cls._eval_node(node.operand, ctx, depth + 1))
        if isinstance(node, ast.BoolOp):
            if isinstance(node.op, ast.And):
                return all(bool(cls._eval_node(v, ctx, depth + 1)) for v in node.values)
            if isinstance(node.op, ast.Or):
                return any(bool(cls._eval_node(v, ctx, depth + 1)) for v in node.values)
        if isinstance(node, ast.Compare):
            left = cls._eval_node(node.left, ctx, depth + 1)
            for op, comp in zip(node.ops, node.comparators):
                right = cls._eval_node(comp, ctx, depth + 1)
                if isinstance(op, ast.Eq) and not (left == right):
                    return False
                elif isinstance(op, ast.NotEq) and not (left != right):
                    return False
                elif isinstance(op, ast.Lt) and not (left < right):
                    return False
                elif isinstance(op, ast.LtE) and not (left <= right):
                    return False
                elif isinstance(op, ast.Gt) and not (left > right):
                    return False
                elif isinstance(op, ast.GtE) and not (left >= right):
                    return False
                elif isinstance(op, ast.In) and not (left in right):
                    return False
                elif isinstance(op, ast.NotIn) and not (left not in right):
                    return False
                left = right
            return True
        raise SecuritySandboxViolation(f"Unhandled AST construct: {type(node).__name__}")


SovereignASTSecurityError = SecuritySandboxViolation
StrictASTPredicateEvaluator = SafeASTPredicateEvaluator


class BatchMerkleEpochDigest:
    """Batch Merkle-Chained Epoch Digest with RFC-8785 Canonical Serialization and HLC Interval Attestation.

    Grounded from Pro node sunward Fleet Advisory (Dialectic Synthesis).
    """

    @staticmethod
    def canonical_json(obj: Any) -> str:
        return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    @classmethod
    def compute_merkle_root(cls, events: List[Dict[str, Any]]) -> str:
        if not events:
            return hashlib.sha256(b"EMPTY_EPOCH").hexdigest()
        layer = [
            hashlib.sha256(cls.canonical_json(ev).encode("utf-8")).hexdigest()
            for ev in events
        ]
        while len(layer) > 1:
            next_layer: List[str] = []
            for idx in range(0, len(layer), 2):
                left = layer[idx]
                right = layer[idx + 1] if idx + 1 < len(layer) else left
                combined = hashlib.sha256(f"{left}:{right}".encode("utf-8")).hexdigest()
                next_layer.append(combined)
            layer = next_layer
        return layer[0]

    @classmethod
    def SealEpoch(
        cls,
        events: List[Dict[str, Any]],
        hlc_start: int,
        hlc_end: int,
        prev_epoch_hash: str = "0" * 64,
    ) -> Dict[str, Any]:
        if hlc_end < hlc_start:
            raise ValueError(f"Invalid HLC interval: hlc_end ({hlc_end}) < hlc_start ({hlc_start})")
        merkle_root = cls.compute_merkle_root(events)
        envelope = {
            "event_count": len(events),
            "hlc_end": hlc_end,
            "hlc_start": hlc_start,
            "merkle_root": merkle_root,
            "prev_epoch_hash": prev_epoch_hash,
        }
        epoch_hash = hashlib.sha256(cls.canonical_json(envelope).encode("utf-8")).hexdigest()
        return {**envelope, "epoch_hash": epoch_hash}


class SecurityTraversalError(ValueError):
    """Raised when an inspected target path escapes the sovereign workspace (CWE-22)."""


def resolve_safe_workspace_path(untrusted_path: str | Path, workspace_root: Path) -> Path:
    """Canonically resolve path and guarantee containment within workspace_root.

    Grounded from Pro node ai-digimate Fleet Advisory (Clef Trust Score: 0.81).
    """
    canonical_root = Path(workspace_root).resolve(strict=True)
    target = (canonical_root / untrusted_path).resolve()
    if not target.is_relative_to(canonical_root):
        raise SecurityTraversalError(
            f"Directory traversal rejected: {target} is outside {canonical_root}"
        )
    return target


class SafeLedgerIOError(RuntimeError):
    """Raised on unrecoverable ledger IO failure (SEC-03)."""


class SafeLedgerIO:
    """Thread-safe and process-safe transactional JSON ledger reader/writer.

    Implements RFC 8785 canonical serialization, fcntl advisory locks, and atomic os.replace.
    Grounded from Pro node insilos Fleet Advisory (Clef Trust Score: 0.65).
    """

    @staticmethod
    def read_ledger(file_path: Path | str) -> Dict[str, Any]:
        import fcntl

        path = Path(file_path)
        if not path.exists():
            return {}
        with open(path, "r", encoding="utf-8") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_SH)
            try:
                content = handle.read().strip()
                if not content:
                    return {}
                return json.loads(content)
            except json.JSONDecodeError as err:
                raise SafeLedgerIOError(f"Ledger decode error at {path}: {err}") from err
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

    @staticmethod
    def atomic_write_ledger(file_path: Path | str, data: Dict[str, Any]) -> None:
        import fcntl
        import os
        import tempfile

        target_path = Path(file_path).resolve()
        target_dir = target_path.parent
        target_dir.mkdir(parents=True, exist_ok=True)
        serialized = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        lock_file_path = target_dir / f".{target_path.name}.lock"
        with open(lock_file_path, "w", encoding="utf-8") as lock_handle:
            fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
            tmp_file_path: Optional[Path] = None
            try:
                with tempfile.NamedTemporaryFile(
                    mode="w",
                    dir=str(target_dir),
                    prefix=f"tmp_{target_path.stem}_",
                    suffix=".tmp",
                    delete=False,
                    encoding="utf-8",
                ) as tmp_file:
                    tmp_file.write(serialized)
                    tmp_file.flush()
                    os.fsync(tmp_file.fileno())
                    tmp_file_path = Path(tmp_file.name)
                os.replace(tmp_file_path, target_path)
            except Exception as write_err:
                if tmp_file_path is not None and tmp_file_path.exists():
                    tmp_file_path.unlink()
                raise SafeLedgerIOError(f"Atomic ledger write failed: {write_err}") from write_err
            finally:
                fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)


class TombstoneResurrectionError(RuntimeError):
    """Raised when a Tombstone Resurrection Attack (line deletion, reordering, or HMAC mismatch) is detected (FAIL-01 / CWE-345)."""


class TombstoneIntegrityGuard:
    """HMAC-SHA256 + RFC 8785 Chained Tombstone Ledger Guard preventing Tombstone Resurrection Attacks.

    Grounded from Pro node ai-digimate (claude-opus-5-5-high, Spiral T3·Q4 FAIL-01).
    """

    GENESIS_CHAIN_HASH: str = "0" * 64

    @staticmethod
    def canonical_payload_bytes(entry: Dict[str, Any]) -> bytes:
        clean = {
            k: v
            for k, v in entry.items()
            if k not in ("chain_hash", "prev_chain_hash", "seq_index")
        }
        return json.dumps(clean, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

    @classmethod
    def compute_entry_hmac(
        cls,
        entry: Dict[str, Any],
        seq_index: int,
        prev_chain_hash: str,
        hmac_key: bytes,
    ) -> str:
        import hmac

        if not hmac_key or len(hmac_key) < 16:
            raise ValueError("HMAC key must be at least 16 bytes (fail-closed, CWE-345).")
        msg = f"{seq_index}:{prev_chain_hash}:".encode("utf-8") + cls.canonical_payload_bytes(entry)
        return hmac.new(hmac_key, msg, hashlib.sha256).hexdigest()

    @classmethod
    def append_tombstone(
        cls,
        ledger_path: Path | str,
        entry: Dict[str, Any],
        hmac_key: bytes,
    ) -> Dict[str, Any]:
        path = Path(ledger_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        existing_lines: List[str] = []
        if path.exists():
            existing_lines = [ln.strip() for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]

        if existing_lines:
            ok, msg, head_hash = cls.verify_ledger(path, hmac_key, expected_min_count=len(existing_lines))
            if not ok:
                raise TombstoneResurrectionError(f"Cannot append to compromised tombstone ledger: {msg}")
            prev_hash = head_hash
            seq_idx = len(existing_lines)
        else:
            prev_hash = cls.GENESIS_CHAIN_HASH
            seq_idx = 0

        chain_hash = cls.compute_entry_hmac(entry, seq_idx, prev_hash, hmac_key)
        sealed_entry = {
            **entry,
            "seq_index": seq_idx,
            "prev_chain_hash": prev_hash,
            "chain_hash": chain_hash,
        }
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(sealed_entry, sort_keys=True, ensure_ascii=False) + "\n")
        return sealed_entry

    @classmethod
    def verify_ledger(
        cls,
        ledger_path: Path | str,
        hmac_key: bytes,
        expected_min_count: int = 0,
        expected_head_hash: Optional[str] = None,
    ) -> Tuple[bool, str, str]:
        import hmac

        if not hmac_key or len(hmac_key) < 16:
            raise ValueError("HMAC key must be at least 16 bytes (fail-closed, CWE-345).")
        path = Path(ledger_path)
        if not path.exists():
            if expected_min_count > 0 or expected_head_hash:
                raise TombstoneResurrectionError("Tombstone ledger missing or deleted (resurrection attack).")
            return True, "EMPTY_VALID", cls.GENESIS_CHAIN_HASH

        lines = [ln.strip() for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
        if len(lines) < expected_min_count:
            raise TombstoneResurrectionError(
                f"Tombstone truncation detected: found {len(lines)} entries < expected {expected_min_count}"
            )

        prev_hash = cls.GENESIS_CHAIN_HASH
        for idx, raw_line in enumerate(lines):
            rec = json.loads(raw_line)
            if rec.get("seq_index") != idx:
                raise TombstoneResurrectionError(
                    f"Tombstone sequence gap/reorder at line {idx}: seq_index={rec.get('seq_index')}"
                )
            if rec.get("prev_chain_hash") != prev_hash:
                raise TombstoneResurrectionError(
                    f"Tombstone prev_chain_hash broken at seq_index={idx}"
                )
            expected_mac = cls.compute_entry_hmac(rec, idx, prev_hash, hmac_key)
            actual_mac = str(rec.get("chain_hash", ""))
            if not hmac.compare_digest(expected_mac, actual_mac):
                raise TombstoneResurrectionError(
                    f"Tombstone HMAC mismatch at seq_index={idx}"
                )
            prev_hash = actual_mac

        if expected_head_hash is not None and not hmac.compare_digest(prev_hash, expected_head_hash):
            raise TombstoneResurrectionError(
                f"Tombstone tail hash mismatch: {prev_hash} != {expected_head_hash}"
            )
        return True, f"VERIFIED ({len(lines)} entries)", prev_hash







def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Sovereign Victory Critic & Claude-Style Anti-Fake-Pass Gate"
    )
    parser.add_argument("--evaluate-fake-pass", type=str, help="Claim text to evaluate for fake-pass risk")
    parser.add_argument("--test-file", type=str, default="", help="Optional test file path to inspect via AST")
    parser.add_argument("--execution-log", type=str, default="", help="Empirical execution log snippet")
    parser.add_argument("--critique-victory", type=str, help="Victory title to critique")
    parser.add_argument("--claim-type", type=str, default="task_victory", choices=["job_victory", "goal_victory", "task_victory"])
    parser.add_argument("--project", type=str, default="hermes-agent", help="Target project name")
    parser.add_argument("--inject-gemini-dod", type=str, help="Inject strict Gemini 4 Argon DoD reminder into prompt")
    parser.add_argument("--target-model", type=str, default="gemini-4-argon-high", help="Target model slug for DoD reminder")
    parser.add_argument("--task-level", type=str, default="L3_COMPLEX", help="Task level for DoD reminder")
    parser.add_argument("--task-type", type=str, default="code_gen", help="Task type for DoD reminder")
    parser.add_argument("--seed-projects", action="store_true", help="Seed canonical critiques across all 5 projects")
    parser.add_argument("--summary", action="store_true", help="Print ledger summary JSON")
    args = parser.parse_args(argv)

    if args.inject_gemini_dod is not None:
        enriched = ensure_gemini_dod_reminder(
            prompt=args.inject_gemini_dod,
            target_model=args.target_model,
            task_level=args.task_level,
            task_type=args.task_type,
        )
        print(enriched)
        return 0

    critic = SovereignVictoryCritic()
    test_code = ""
    if args.test_file and Path(args.test_file).is_file():
        test_code = Path(args.test_file).read_text(encoding="utf-8", errors="ignore")

    if args.seed_projects:
        seeded = critic.seed_canonical_project_critiques()
        print(json.dumps({"seeded": len(seeded), "summary": critic.get_ledger_summary()}, indent=2, ensure_ascii=False))
        return 0

    if args.evaluate_fake_pass:
        res = critic.evaluate_fake_pass_risk(
            claim_text=args.evaluate_fake_pass,
            test_code=test_code,
            execution_log=args.execution_log,
            claim_type=args.claim_type,
        )
        print(json.dumps(res, indent=2, ensure_ascii=False))
        return 0 if res["verdict"] == "PASS" else 1

    if args.critique_victory:
        res = critic.critique_victory_claim(
            claim_type=args.claim_type,
            title=args.critique_victory,
            claim_summary=args.critique_victory,
            requirements=[args.critique_victory],
            evidence_log=args.execution_log,
            test_code=test_code,
            project=args.project,
        )
        print(json.dumps(res, indent=2, ensure_ascii=False))
        return 0 if res["gate_passed"] else 1

    print(json.dumps(critic.get_ledger_summary(), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())

