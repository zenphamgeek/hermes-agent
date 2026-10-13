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
from pathlib import Path
import pytest
import torch
from safetensors.torch import save_file

from tools.modal_jev_finetuning import (
    JEV_SYSTEM_INSTRUCTION,
    DatasetSecretScrubber,
    ModalCredentialError,
    generate_dataset_manifest,
    get_modal_credentials,
    harvest_dataset_from_ledgers,
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

    with pytest.raises(ValueError, match="Insecure pickle serialization format"):
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
    assert fcntl.LOCK_EX in flock_calls
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
    Verifies modal credentials helper sources from environment.
    """
    monkeypatch.setenv("MODAL_TOKEN_ID", "ak-test-token-id-123")
    monkeypatch.setenv("MODAL_TOKEN_SECRET", "as-test-token-secret-456")

    creds = get_modal_credentials()
    assert creds["MODAL_TOKEN_ID"] == "ak-test-token-id-123"
    assert creds["MODAL_TOKEN_SECRET"] == "as-test-token-secret-456"


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

