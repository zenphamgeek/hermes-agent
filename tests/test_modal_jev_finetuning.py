"""
tests/test_modal_jev_finetuning.py
==================================
Unit tests for the Modal JEV Decision Model fine-tuning pipeline.
Covers Cycle 33 Nebula adversarial security remediation:
- Mandatory Serialization Boundary & SecretScrubber on Dataset Export Path (CWE-200)
- Safe Weight Serialization & Deserialization RCE Guard (CWE-502)
- Modal Credential Sourcing Guard (CWE-798/259)
"""

import ast
import fcntl
import json
import os
import pickle
import stat
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
import pytest
import torch
from safetensors.torch import save_file

from tools.modal_jev_finetuning import (
    JEV_SYSTEM_INSTRUCTION,
    DatasetSecretScrubber,
    ModalCredentialError,
    QuotaBreaker,
    advisory_file_lock,
    generate_dataset_manifest,
    get_modal_credentials,
    harvest_dataset_from_ledgers,
    is_tombstoned,
    load_safe_model_weights,
    train_jev_modal,
    validate_dataset_is_sanitized,
    verify_dataset_manifest,
    write_dataset_manifest,
)


def test_harvest_dataset_generation(tmp_path):
    output_ds = tmp_path / "test_jev_dataset.jsonl"
    fake_ledger = tmp_path / "fake_action_ledger.jsonl"

    # Write a simulated action ledger entry
    fake_ledger.write_text(
        json.dumps({
            "action": "jev_decision_evaluation",
            "domain": "enterprise_erp",
            "payload_sha256": "hash_12345",
            "status": "PERMITTED",
            "details": {
                "complexity": 1.5,
                "tier": "PRO",
                "runner": "odoo.tests.common.TransactionCase (`odoo-bin --test-enable`)",
            },
        }) + "\n",
        encoding="utf-8",
    )

    records = harvest_dataset_from_ledgers(
        action_ledger_path=fake_ledger,
        output_path=output_ds,
    )

    assert len(records) >= 5  # Seed anchors + ledger entry
    assert output_ds.exists()

    # Read back and verify JSONL structure
    lines = [json.loads(l) for l in output_ds.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert len(lines) == len(records)

    for item in lines:
        assert "instruction" in item
        assert "input" in item
        assert "output" in item
        out = item["output"]
        assert "domain" in out
        assert "complexity_score" in out
        assert 0.0 <= out["complexity_score"] <= 4.0
        assert out["target_tier"] in ("PRO", "ULTRA")
        assert "test_runner" in out
        assert isinstance(out["requires_cloud_escalation"], bool)
        assert out["verdict"] in ("PERMITTED", "ESCALATED", "REJECTED_COOLDOWN", "REJECTED_SYNTAX")


def test_seed_anchors_coverage(tmp_path):
    output_ds = tmp_path / "seed_dataset.jsonl"
    records = harvest_dataset_from_ledgers(
        action_ledger_path=tmp_path / "nonexistent.jsonl",
        output_path=output_ds,
    )

    domains = {r["output"]["domain"] for r in records}
    assert "enterprise_erp" in domains
    assert "game_simulation" in domains
    assert "ai_infrastructure" in domains

    # Verify both fast-path and escalated cases exist in seed data
    escalated_flags = {r["output"]["requires_cloud_escalation"] for r in records}
    assert True in escalated_flags
    assert False in escalated_flags


def test_secret_scrubber_on_dataset_export_boundary(tmp_path):
    """
    CWE-200: Raw secrets in action ledger entries (Bearer tokens, DB passwords,
    GitHub PATs, API keys) must be sanitized before dataset export.
    """
    output_ds = tmp_path / "boundary_export.sanitized.jsonl"
    fake_ledger = tmp_path / "sensitive_action_ledger.jsonl"

    raw_bearer = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.super_secret_payload_12345"
    raw_db_pass = "P@ssw0rd_Enterprise_2026!"
    raw_db_url = f"postgresql://odoo_admin:{raw_db_pass}@pg-primary.internal:5432/production_db"
    raw_gh_pat = "ghp_123456789012345678901234567890123456"
    raw_api_key = "AIzaSyD-1234567890123456789012345678901"
    raw_google_refresh = "1//04test_google_refresh_token_very_sensitive_123456789"

    fake_ledger.write_text(
        json.dumps({
            "action": "jev_decision_evaluation",
            "domain": "enterprise_erp",
            "payload_sha256": "secret_payload_digest",
            "status": "PERMITTED",
            "details": {
                "complexity": 1.8,
                "tier": "PRO",
                "runner": f"pytest --db-url={raw_db_url} --auth='{raw_bearer}'",
                "api_access": raw_api_key,
                "vcs_token": raw_gh_pat,
                "oauth_refresh": raw_google_refresh,
            },
        }) + "\n",
        encoding="utf-8",
    )

    records = harvest_dataset_from_ledgers(
        action_ledger_path=fake_ledger,
        output_path=output_ds,
    )

    assert output_ds.exists()
    content = output_ds.read_text(encoding="utf-8")

    # Assert none of the raw secret strings leak into exported dataset
    assert raw_db_pass not in content
    assert raw_gh_pat not in content
    assert raw_api_key not in content
    assert raw_google_refresh not in content
    assert "super_secret_payload_12345" not in content

    # Assert exported dataset passes the strict sanitization gate
    is_valid, violations = validate_dataset_is_sanitized(content)
    assert is_valid is True, f"Sanitization gate failed with violations: {violations}"
    assert len(violations) == 0


def test_unredacted_dataset_rejected_by_sanitization_gate(tmp_path):
    """
    CWE-200 / CWE-259: Un-scrubbed datasets containing raw secret patterns
    or lacking scrubber integrity metadata trigger ValueError at the training gate.
    """
    unredacted_sample = {
        "instruction": JEV_SYSTEM_INSTRUCTION,
        "input": {
            "prompt": "Connect to postgresql://admin:leaked_db_password_123@prod-db:5432/main",
            "domain": "enterprise_erp",
        },
        "output": {
            "domain": "enterprise_erp",
            "complexity_score": 1.2,
            "target_tier": "PRO",
            "test_runner": "pytest",
            "requires_cloud_escalation": False,
            "verdict": "PERMITTED",
            "rationale": "Bearer raw_bearer_token_should_never_pass_gate_12345",
        },
    }
    unredacted_content = json.dumps(unredacted_sample) + "\n"

    # 1. Validation gate returns False and identifies violations
    is_valid, violations = validate_dataset_is_sanitized(unredacted_content)
    assert is_valid is False
    assert len(violations) > 0
    assert any("Database URL" in v for v in violations)
    assert any("Bearer Token" in v for v in violations)

    # 2. train_jev_modal fails closed with ValueError
    with pytest.raises(ValueError, match="Dataset sanitization validation failed"):
        train_jev_modal(dataset_jsonl_content=unredacted_content)


def test_safetensors_and_weights_only_deserialization_guard(tmp_path):
    """
    CWE-502: Safe weight serialization and deserialization.
    Verifies safetensors loading, weights_only=True enforcement,
    and rejection of raw pickle formats (.pkl, .pickle).
    """
    # 1. Safetensors weights load cleanly
    tensors = {"weight": torch.randn(4, 4), "bias": torch.zeros(4)}
    safe_path = tmp_path / "model.safetensors"
    save_file(tensors, str(safe_path))

    loaded_safe = load_safe_model_weights(safe_path)
    assert "weight" in loaded_safe
    assert torch.allclose(loaded_safe["weight"], tensors["weight"])

    # 2. Directory loading finds and loads safetensors
    loaded_dir = load_safe_model_weights(tmp_path)
    assert "weight" in loaded_dir

    # 3. PyTorch weights_only loads safe tensor state dict
    pt_path = tmp_path / "safe_model.pt"
    torch.save(tensors, pt_path)
    loaded_pt = load_safe_model_weights(pt_path)
    assert "weight" in loaded_pt
    assert torch.allclose(loaded_pt["weight"], tensors["weight"])

    # 4. Raw pickle file (.pkl) is strictly rejected
    pkl_path = tmp_path / "malicious.pkl"
    with open(pkl_path, "wb") as f:
        pickle.dump(tensors, f)

    with pytest.raises(ValueError, match="Insecure or unsupported weight file format"):
        load_safe_model_weights(pkl_path)

    # 5. Deserialization of untrusted code payload via .bin is blocked by weights_only=True
    class ArbitraryCodeExecution:
        def __reduce__(self):
            return (eval, ("1+1",))

    exploit_path = tmp_path / "exploit.bin"
    with open(exploit_path, "wb") as f:
        pickle.dump(ArbitraryCodeExecution(), f)

    with pytest.raises(Exception):
        load_safe_model_weights(exploit_path)


def test_dataset_harvesting_atomic_and_locked(tmp_path, monkeypatch):
    """
    Verifies atomic mode-0600 file creation with advisory lock (fcntl.flock).
    """
    output_ds = tmp_path / "atomic_dataset.sanitized.jsonl"
    flock_calls = []

    orig_flock = fcntl.flock

    def mock_flock(fd, op):
        flock_calls.append(op)
        return orig_flock(fd, op)

    monkeypatch.setattr(fcntl, "flock", mock_flock)

    records = harvest_dataset_from_ledgers(
        action_ledger_path=tmp_path / "empty_ledger.jsonl",
        output_path=output_ds,
    )

    # Check that file was created and is non-empty
    assert output_ds.exists()
    assert len(records) > 0

    # Verify mode-0600 permissions
    file_mode = stat.S_IMODE(output_ds.stat().st_mode)
    assert file_mode == 0o600

    # Verify advisory locking was executed (exclusive lock and unlock)
    assert any(op & fcntl.LOCK_EX for op in flock_calls)
    assert fcntl.LOCK_UN in flock_calls

    # Verify no temporary files remain
    tmp_files = list(tmp_path.glob("*.tmp"))
    assert len(tmp_files) == 0


def test_zero_hardcoded_modal_credentials_ast_scan():
    """
    CWE-798/259: AST scan of tools/modal_jev_finetuning.py verifying zero
    hardcoded tokens, passwords, or secret strings.
    """
    target_path = Path("tools/modal_jev_finetuning.py")
    assert target_path.exists()

    source = target_path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    for node in ast.walk(tree):
        # 1. Scan all string literals
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            val = node.value
            assert not val.startswith("ak-"), f"Hardcoded Modal token ID found: {val}"
            assert not val.startswith("as-"), f"Hardcoded Modal token secret found: {val}"
            assert not val.startswith("ghp_"), f"Hardcoded GitHub PAT found: {val}"
            assert not val.startswith("AIza"), f"Hardcoded Google API key found: {val}"
            assert not val.startswith("1//"), f"Hardcoded Google refresh token found: {val}"

        # 2. Check variable assignments for credential targets
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    if target.id in ("MODAL_TOKEN_ID", "MODAL_TOKEN_SECRET", "MODAL_API_KEY"):
                        if isinstance(node.value, ast.Constant) and node.value.value:
                            pytest.fail(f"Hardcoded credential literal assigned to {target.id}: {node.value.value}")


def test_dataset_secret_scrubber_unit_patterns():
    """
    Unit test for DatasetSecretScrubber pattern matching and replacement.
    """
    scrubber = DatasetSecretScrubber(known_secrets=["MyCustomSecretToken123"])

    sample = (
        "Here is Bearer my_super_secret_bearer_token_12345 "
        "and db postgresql://user:mypassword123@localhost:5432/db "
        "and pat ghp_123456789012345678901234567890123456 "
        "and api AIzaSyD-1234567890123456789012345678901 "
        "and custom MyCustomSecretToken123"
    )

    scrubbed = scrubber.scrub_text(sample)

    assert "my_super_secret_bearer_token_12345" not in scrubbed
    assert "mypassword123" not in scrubbed
    assert "ghp_123456789012345678901234567890123456" not in scrubbed
    assert "AIzaSyD-1234567890123456789012345678901" not in scrubbed
    assert "MyCustomSecretToken123" not in scrubbed

    assert "Bearer [REDACTED]" in scrubbed
    assert "[REDACTED_GITHUB_PAT]" in scrubbed
    assert "[REDACTED_GOOGLE_API_KEY]" in scrubbed


def test_metadata_integrity_tamper_detection():
    """
    Verifies that altering record content after scrubber signing breaks HMAC integrity.
    """
    scrubber = DatasetSecretScrubber()
    record = {
        "instruction": JEV_SYSTEM_INSTRUCTION,
        "input": {"prompt": "Run benchmark", "domain": "enterprise_erp"},
        "output": {"domain": "enterprise_erp", "complexity_score": 1.0},
    }

    signed = scrubber.sign_record(record)
    assert DatasetSecretScrubber.verify_record_integrity(signed) is True

    # Tamper with input prompt
    signed["input"]["prompt"] = "Tampered prompt!"
    assert DatasetSecretScrubber.verify_record_integrity(signed) is False


def test_get_modal_credentials_sourcing(monkeypatch):
    """
    Verifies modal credentials helper sources from environment and
    treats empty or whitespace-only variables as None (CWE-798/259).
    """
    monkeypatch.setenv("MODAL_TOKEN_ID", "ak-test-token-id-123")
    monkeypatch.setenv("MODAL_TOKEN_SECRET", "as-test-token-secret-456")

    creds = get_modal_credentials()
    assert creds["MODAL_TOKEN_ID"] == "ak-test-token-id-123"
    assert creds["MODAL_TOKEN_SECRET"] == "as-test-token-secret-456"

    # Whitespace-only must be stripped to None
    monkeypatch.setenv("MODAL_TOKEN_ID", "   ")
    monkeypatch.setenv("MODAL_TOKEN_SECRET", "\t\n")
    creds_ws = get_modal_credentials(require=False)
    assert creds_ws["MODAL_TOKEN_ID"] is None
    assert creds_ws["MODAL_TOKEN_SECRET"] is None


def test_load_safe_model_weights_rejects_renamed_pickle(tmp_path):
    """
    CWE-502: Attempting to bypass safetensors loading by renaming a raw pickle
    file to .safetensors must be intercepted by the magic bytes check.
    """
    tensors = {"weight": torch.randn(2, 2)}
    fake_safetensors = tmp_path / "renamed_model.safetensors"
    with open(fake_safetensors, "wb") as f:
        pickle.dump(tensors, f)

    with pytest.raises(ValueError, match="Refusing to load non-safetensors artifact"):
        load_safe_model_weights(fake_safetensors)

    # Also test zip container disguised as .safetensors
    zip_fake = tmp_path / "zip_disguised.safetensors"
    zip_fake.write_bytes(b"PK\x03\x04" + b"\x00" * 30)
    with pytest.raises(ValueError, match="Refusing to load non-safetensors artifact"):
        load_safe_model_weights(zip_fake)


def test_credentials_absent_fails_closed(monkeypatch, tmp_path):
    """
    CWE-798/259: When credentials are required but absent, fail closed
    with ModalCredentialError and never echo secret values.
    """
    monkeypatch.delenv("MODAL_TOKEN_ID", raising=False)
    monkeypatch.delenv("MODAL_TOKEN_SECRET", raising=False)
    monkeypatch.delenv("MODAL_PROFILE", raising=False)

    # Point home to a temp dir with no .modal.toml
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    with pytest.raises(ModalCredentialError) as exc_info:
        get_modal_credentials(require=True)

    err_msg = str(exc_info.value)
    assert "Missing required Modal credentials" in err_msg
    assert "MODAL_TOKEN_ID" in err_msg
    assert "MODAL_TOKEN_SECRET" in err_msg


def test_scrubber_recurses_into_nested_and_encoded():
    """
    CWE-200: Scrubber must recursively sanitize arbitrarily nested dictionaries,
    lists, tuples, and fine-grained GitHub PAT tokens.
    """
    scrubber = DatasetSecretScrubber()
    nested_payload = {
        "outer": {
            "middle": [
                {
                    "deep_key": "Bearer my_deep_bearer_token_12345",
                    "fine_pat": "github_pat_11ABCD1234_long_token_string_here_567890",
                    "db_info": "postgresql://user:secret_pass_999@localhost:5432/db",
                }
            ]
        }
    }

    scrubbed = scrubber.scrub(nested_payload)
    deep_record = scrubbed["outer"]["middle"][0]

    assert deep_record["deep_key"] == "Bearer [REDACTED]"
    assert deep_record["fine_pat"] == "[REDACTED_GITHUB_PAT]"
    assert "secret_pass_999" not in deep_record["db_info"]
    assert "[REDACTED]" in deep_record["db_info"]


def test_harvest_refuses_write_on_validation_failure(tmp_path, monkeypatch):
    """
    CWE-200 Fail-Closed: If post-harvest validation catches unredacted secrets,
    the pipeline must refuse to write the output file and raise ValueError.
    """
    output_ds = tmp_path / "should_not_exist.jsonl"
    fake_ledger = tmp_path / "bad_ledger.jsonl"
    fake_ledger.write_text("{}", encoding="utf-8")

    # Mock scrubber.sign_record to intentionally bypass redaction and inject a raw secret
    def leaky_sign(rec):
        rec["input"]["prompt"] = "leaked postgresql://admin:unscrubbed_pass@db:5432/x"
        return rec

    monkeypatch.setattr(DatasetSecretScrubber, "sign_record", lambda self, rec: leaky_sign(rec))

    with pytest.raises(ValueError, match="Dataset post-harvest sanitization gate failed"):
        harvest_dataset_from_ledgers(
            action_ledger_path=fake_ledger,
            output_path=output_ds,
        )

    # Output file must NOT exist on disk
    assert not output_ds.exists()


def test_dataset_provenance_manifest_gate(tmp_path):
    """
    Supply-Chain Provenance Gate: Dataset provenance manifest is automatically
    generated, cryptographically signed, and verified before training.
    """
    output_ds = tmp_path / "provenance_dataset.jsonl"
    records = harvest_dataset_from_ledgers(
        action_ledger_path=tmp_path / "empty.jsonl",
        output_path=output_ds,
    )

    manifest_file = output_ds.with_name(f"{output_ds.name}.manifest.json")
    assert manifest_file.exists()

    manifest_data = json.loads(manifest_file.read_text(encoding="utf-8"))
    assert manifest_data["sample_count"] == len(records)
    assert len(manifest_data["content_sha256"]) == 64
    assert "provenance_signature" in manifest_data

    # 1. Verification succeeds on untampered dataset
    is_valid, violations = verify_dataset_manifest(output_ds)
    assert is_valid is True, f"Manifest verification failed: {violations}"
    assert len(violations) == 0

    # 2. Tampering with dataset invalidates manifest verification
    with open(output_ds, "a", encoding="utf-8") as f:
        f.write('{"tampered": true}\n')

    is_valid_tampered, violations_tampered = verify_dataset_manifest(output_ds)
    assert is_valid_tampered is False
    assert any("Provenance hash mismatch" in v for v in violations_tampered)


def test_manifest_write_is_atomic_under_concurrent_writers(tmp_path):
    """
    CWE-362: Concurrent manifest writers must not produce torn writes or interleaved JSON.
    """
    target_ds = tmp_path / "concurrent_dataset.jsonl"
    target_ds.write_text('{"sample": 1}\n', encoding="utf-8")
    errors = []

    def writer(tag: int):
        try:
            m = generate_dataset_manifest(
                dataset_path=target_ds,
                dataset_content=f'{{"sample": {tag}}}\n',
                sample_count=1,
            )
            write_dataset_manifest(target_ds, m)
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=writer, args=(i,)) for i in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, f"Concurrent manifest write errors encountered: {errors}"
    manifest_p = target_ds.with_name(f"{target_ds.name}.manifest.json")
    assert manifest_p.exists()
    # Must parse cleanly without JSON syntax error
    data = json.loads(manifest_p.read_text(encoding="utf-8"))
    assert "content_sha256" in data
    assert "provenance_signature" in data


def test_manifest_rejects_future_dated_validity_window(tmp_path):
    """
    CWE-367/613: Skew-tolerant but strictly bounded. A manifest dated 5 minutes
    in the future beyond allowed max_clock_skew_s (120s) must be rejected.
    """
    m = generate_dataset_manifest(
        dataset_path=tmp_path / "skew_dataset.jsonl",
        dataset_content='{"sample": 1}\n',
        sample_count=1,
    )
    # Tamper timestamp to 5 minutes into the future
    m["generated_at"] = (datetime.now(timezone.utc).timestamp() + 300)

    ok, violations = verify_dataset_manifest(m, max_clock_skew_s=120)
    assert ok is False
    assert any("clock skew" in v.lower() for v in violations)


def test_tombstone_not_resurrected_by_lagging_reader_clock():
    """
    Bi-Temporal Invariant: A reader whose wall clock lags the tombstone's
    transaction_time must still treat the record as deleted (Zero-Resurrection).
    """
    tombstone_tx_time = time.time()
    reader_now = tombstone_tx_time - 300  # Reader 5 minutes slow
    assert is_tombstoned(tombstone_tx_time, reader_now=reader_now) is True


def test_validator_catches_unredacted_high_entropy_token():
    """
    CWE-200 Non-Circular Gate: Independent Shannon entropy heuristic catches
    un-enumerated, unknown high-entropy token shapes not in the named pattern set.
    """
    # Raw high-entropy token (32 random base64 chars with entropy > 4.0)
    novel_token = "K9zX4mP7qR2wL8vN5tY1jB6cE0aF3sD="
    leaked_record = {
        "instruction": JEV_SYSTEM_INSTRUCTION,
        "input": {"prompt": f"Debug unknown token: {novel_token}"},
        "output": {"domain": "enterprise_erp", "complexity_score": 1.0},
    }
    content = json.dumps(leaked_record) + "\n"

    is_valid, violations = validate_dataset_is_sanitized(content, enforce_signature=False)
    assert is_valid is False
    assert any("high-entropy" in v.lower() for v in violations)


def test_symlink_weight_file_rejected(tmp_path):
    """
    F1 (CWE-502): Symlinks in model weights path must be strictly refused.
    """
    tensors = {"weight": torch.randn(2, 2)}
    valid_file = tmp_path / "valid_model.safetensors"
    save_file(tensors, str(valid_file))

    symlink_file = tmp_path / "symlink_model.safetensors"
    symlink_file.symlink_to(valid_file)

    with pytest.raises(ValueError, match=r"Refusing symlinked weight file.*CWE-502"):
        load_safe_model_weights(symlink_file)


def test_crafted_pickle_sentinel_never_executed(tmp_path):
    """
    F1 (CWE-502): Crafted malicious class with __reduce__ that attempts RCE
    via file write is blocked by weights_only=True and NEVER executed.
    """
    sentinel_path = Path(f"/tmp/sentinel_exploit_{uuid.uuid4().hex}.txt")

    class MaliciousPayload:
        def __reduce__(self):
            return (eval, (f"open('{sentinel_path}', 'w').write('CWE-502-RCE')",))

    exploit_pt = tmp_path / "crafted_exploit.pt"
    with open(exploit_pt, "wb") as f:
        pickle.dump(MaliciousPayload(), f, protocol=2)

    try:
        with pytest.raises(Exception):
            load_safe_model_weights(exploit_pt)
        assert not sentinel_path.exists(), (
            "CWE-502 Critical RCE: Malicious __reduce__ payload executed during load_safe_model_weights (.pt)!"
        )
    finally:
        if sentinel_path.exists():
            sentinel_path.unlink()

    exploit_bin = tmp_path / "crafted_exploit.bin"
    with open(exploit_bin, "wb") as f:
        pickle.dump(MaliciousPayload(), f, protocol=2)

    try:
        with pytest.raises(Exception):
            load_safe_model_weights(exploit_bin)
        assert not sentinel_path.exists(), (
            "CWE-502 Critical RCE: Malicious __reduce__ payload executed during load_safe_model_weights (.bin)!"
        )
    finally:
        if sentinel_path.exists():
            sentinel_path.unlink()


def test_honeytoken_canary_recall_harness(tmp_path):
    """
    F2 (CWE-200 / CWE-259): Seeds an action ledger entry with 14 distinct synthetic honeytokens.
    Verifies scrubber recall == 1.0 (100% recall) and validate_dataset_is_sanitized passes with 0 violations.
    """
    output_ds = tmp_path / "honeytoken_export.sanitized.jsonl"
    ledger_p = tmp_path / "honeytoken_ledger.jsonl"

    honeytokens = [
        "sk-proj-abc1234567890abcdefghijklmnopqrstuvwxyz",
        "ghp_1234567890abcdefghijklmnopqrstuvwxyz12",
        "github_pat_11AABCDEF0123456789_abcdefghijklmnopqrstuvwxyz1234567890",
        "1//04testGoogleOAuthRefreshToken1234567890",
        "ya29.a0ARrdaM_test_access_token_1234567890",
        "AIzaSyD_TestGoogleApiKey_12345678901",
        "AKIAIOSFODNN7EXAMPLE",
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.doNotLeakThisSecretSignature",
        "Bearer superSecretBearerTokenValue12345678",
        "postgresql://db_admin:UltraSecretPassword2026!@pg-cluster.internal:5432/main",
        "xoxb-" + "1234567890-1234567890123-abcdefghijklmnopqrstuvwx",
        "123456789:ABCdefGhIjkLmNoPqRsTuVwXyZ_1234567890",
        "ak-testModalTokenId1234567890",
        "https://api.internal/data?token=super_secret_query_param_token_12345",
    ]

    ledger_lines = []
    for idx, token in enumerate(honeytokens):
        ledger_lines.append(
            json.dumps({
                "action": "jev_decision_evaluation",
                "domain": "security_canary_domain",
                "payload_sha256": f"Canary {idx}: {token}",
                "status": "PERMITTED",
                "details": {
                    "complexity": 1.2,
                    "tier": "PRO",
                    "canary_secret": token,
                },
            })
        )

    ledger_p.write_text("\n".join(ledger_lines) + "\n", encoding="utf-8")

    records = harvest_dataset_from_ledgers(
        action_ledger_path=ledger_p,
        output_path=output_ds,
    )

    assert output_ds.exists()
    exported_content = output_ds.read_text(encoding="utf-8")

    total_canaries = len(honeytokens)
    leaked_canaries = sum(1 for token in honeytokens if token in exported_content)
    scrubber_recall = (total_canaries - leaked_canaries) / total_canaries

    assert scrubber_recall == 1.0, f"Canary leakage detected! Leaked: {leaked_canaries}/{total_canaries}"

    is_valid, violations = validate_dataset_is_sanitized(exported_content)
    assert is_valid is True, f"Sanitization gate failed with violations: {violations}"
    assert len(violations) == 0


def test_advisory_lock_timeout_on_contention(tmp_path):
    """
    F5 (CWE-362/400): Non-blocking fcntl retry with timeout.
    Acquires lock in thread; second attempt with timeout=0.2s raises TimeoutError.
    """
    lock_file = tmp_path / "contention_test.lock"
    holder_acquired = threading.Event()
    release_holder = threading.Event()

    def lock_holder():
        with advisory_file_lock(lock_file, timeout=5.0):
            holder_acquired.set()
            release_holder.wait(timeout=5.0)

    t = threading.Thread(target=lock_holder)
    t.start()
    try:
        assert holder_acquired.wait(timeout=2.0), "Holder failed to acquire lock"

        t0 = time.monotonic()
        with pytest.raises(TimeoutError, match=r"Advisory lock timeout \(0.2s\)"):
            with advisory_file_lock(lock_file, timeout=0.2):
                pass
        elapsed = time.monotonic() - t0
        assert 0.15 <= elapsed <= 1.0, f"Timeout took unexpected duration: {elapsed:.3f}s"
    finally:
        release_holder.set()
        t.join(timeout=2.0)


def test_kill_between_tmp_and_rename_leaves_no_torn_manifest(tmp_path, monkeypatch):
    """
    CWE-362: If a crash, kill, or filesystem error occurs between writing the temp file
    and os.replace, the target manifest is never left in a torn or corrupted state,
    and temporary files are cleaned up.
    """
    target_ds = tmp_path / "crash_test.jsonl"
    target_ds.write_text('{"sample": 1}\n', encoding="utf-8")
    m = generate_dataset_manifest(target_ds, '{"sample": 1}\n', 1)

    def failing_replace(src, dst):
        raise OSError("Simulated crash/power-loss before rename")

    monkeypatch.setattr(os, "replace", failing_replace)

    with pytest.raises(OSError, match="Simulated crash"):
        write_dataset_manifest(target_ds, m)

    manifest_p = target_ds.with_name(f"{target_ds.name}.manifest.json")
    assert not manifest_p.exists(), "Torn manifest appeared after simulated crash!"

    # Ensure no lingering .tmp files
    tmp_files = list(tmp_path.glob(".*.tmp"))
    assert len(tmp_files) == 0, f"Lingering temporary files found: {tmp_files}"


def test_tombstone_resurrection_with_leading_reader_clock():
    """
    Bi-Temporal Invariant: A reader whose wall clock leads the tombstone transaction time
    (clock ahead by 5 minutes) must also treat the record as tombstoned.
    Neither lagging nor leading reader clocks can resurrect deleted data.
    """
    tombstone_tx_time = time.time()
    reader_now = tombstone_tx_time + 300  # Reader 5 minutes ahead
    assert is_tombstoned(tombstone_tx_time, reader_now=reader_now) is True
    assert is_tombstoned(None) is False


def test_skew_gate_rejects_ancient_manifest_replay(tmp_path):
    """
    CWE-367/613 Replay Guard: A manifest with a generated_at timestamp older than
    max_age_s (7 days / 604800s) must be rejected to prevent replay attacks.
    """
    m = generate_dataset_manifest(
        dataset_path=tmp_path / "replay_dataset.jsonl",
        dataset_content='{"sample": 1}\n',
        sample_count=1,
    )
    # Set timestamp to 8 days in the past
    m["generated_at"] = time.time() - (8 * 86400)

    ok, violations = verify_dataset_manifest(m, max_age_s=604800.0)
    assert ok is False
    assert any("expired" in v.lower() for v in violations)


def test_skew_gate_fails_closed_on_unparseable_timestamp(tmp_path):
    """
    CWE-367/613 Fail-Closed: Manifests with non-numeric, corrupt or unparseable
    generated_at values must fail validation gracefully without unhandled exceptions.
    """
    m = generate_dataset_manifest(
        dataset_path=tmp_path / "corrupt_ts_dataset.jsonl",
        dataset_content='{"sample": 1}\n',
        sample_count=1,
    )
    m["generated_at"] = "invalid_not_a_timestamp_2026-99-99"

    ok, violations = verify_dataset_manifest(m)
    assert ok is False
    assert any("invalid or missing generated_at" in v.lower() for v in violations)


def test_entropy_scan_is_bounded_on_large_input():
    """
    CWE-400 CPU Exhaustion Guard: Entropy evaluation on 4MB of benign content
    must execute within bounded time (< 4.0s) using the _ENTROPY_BYTE_CAP limit.
    """
    sample_line = json.dumps({
        "instruction": JEV_SYSTEM_INSTRUCTION,
        "input": {"prompt": "Routine enterprise ERP evaluation" * 10},
        "output": {"domain": "enterprise_erp", "complexity_score": 1.0, "requires_cloud_escalation": False, "verdict": "PERMITTED", "target_tier": "PRO", "test_runner": "pytest"},
    }) + "\n"
    # Create ~4MB of payload
    multiplier = (4 * 1024 * 1024) // len(sample_line)
    large_content = sample_line * multiplier

    t0 = time.monotonic()
    is_valid, violations = validate_dataset_is_sanitized(large_content, enforce_signature=False)
    elapsed = time.monotonic() - t0

    assert is_valid is True, f"Valid large content failed: {violations}"
    assert elapsed < 4.0, f"Entropy scan took too long on large input: {elapsed:.2f}s (CWE-400 risk)"


def test_entropy_whitelist_does_not_flag_manifest_sha256():
    """
    CWE-200/400 False-Positive Guard: Legitimate hex digests (64-char SHA-256,
    32-char HMAC) and manifest structural tags must NOT be flagged as secret leaks.
    """
    legit_record = {
        "instruction": JEV_SYSTEM_INSTRUCTION,
        "input": {"prompt": "Task hash: a1b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7e8f90"},
        "output": {
            "domain": "enterprise_erp",
            "complexity_score": 1.2,
            "requires_cloud_escalation": False,
            "verdict": "PERMITTED",
            "target_tier": "PRO",
            "test_runner": "pytest",
            "content_sha256": "46b42b4229cd7a39c564e780bb665a8bde4fdf722007e8473f167fe53ed4b995",
        },
    }
    content = json.dumps(legit_record) + "\n"
    is_valid, violations = validate_dataset_is_sanitized(content, enforce_signature=False)
    assert is_valid is True, f"Legitimate SHA-256 hash was falsely flagged: {violations}"


def test_retry_storm_is_bounded_under_quota_exhaustion():
    """
    CWE-400 Quota Retry-Storm Guard (What-If: Compute Quota Cut by 80%):
    QuotaBreaker strictly caps retries under 429/quota exhaustion, uses exponential backoff,
    and fails closed immediately without retries for terminal non-quota exceptions.
    """
    breaker = QuotaBreaker(max_attempts=3, base_backoff_s=0.01, max_backoff_s=0.05)
    call_count = 0

    def quota_failing_fn():
        nonlocal call_count
        call_count += 1
        raise RuntimeError("HTTP 429: Resource exhausted: quota exceeded")

    with pytest.raises(RuntimeError, match="quota exceeded"):
        breaker.execute(quota_failing_fn)

    # Must be called exactly max_attempts times, never unbounded
    assert call_count == 3, f"Expected 3 attempts, got {call_count}"

    # Non-quota error must fail immediately on attempt 1
    call_count_fatal = 0

    def fatal_fn():
        nonlocal call_count_fatal
        call_count_fatal += 1
        raise ValueError("Fatal syntax error in prompt")

    with pytest.raises(ValueError, match="Fatal syntax error"):
        breaker.execute(fatal_fn)

    assert call_count_fatal == 1, f"Fatal error retried unexpectedly! count={call_count_fatal}"


def test_no_manifest_for_incomplete_artifact(tmp_path):
    """
    Manifest-After-Artifact Ordering: Verifies that verify_dataset_manifest fails closed
    if the underlying artifact is missing, and that incomplete artifacts cannot produce
    a valid provenance manifest.
    """
    missing_ds = tmp_path / "nonexistent_dataset.jsonl"
    ok, violations = verify_dataset_manifest(missing_ds)
    assert ok is False
    assert any("does not exist" in v.lower() for v in violations)



