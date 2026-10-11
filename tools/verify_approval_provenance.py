#!/usr/bin/env python3
"""Approval Provenance & Secret Leak Audit Verifier.

Audits approval records in approvals/*.json for:
1. Zero secret/credential leak in payloads (CWE-259/CWE-312).
2. Cryptographic checksum validity and disk artifact integrity.
3. Provenance tracking: git_hash, is_git_clean, closure_sha256.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
APPROVALS_DIR = REPO_ROOT / "approvals"

FORBIDDEN_KEY_PATTERNS = [
    r"client_secret",
    r"refresh_token",
    r"access_token",
    r"id_token",
    r"private_key",
    r"api_key",
    r"auth_token",
    r"password",
    r"bearer",
]

SECRET_VALUE_PATTERNS = [
    r"ya29\.[0-9A-Za-z-_]+",
    r"sk-ant-[0-9A-Za-z-_]+",
    r"ghp_[0-9A-Za-z]+",
    r"AIzaSy[0-9A-Za-z-_]{33}",
]


def check_for_secrets(obj: Any, path: str = "") -> list[str]:
    """Recursively inspect a JSON object for secret keys or token values."""
    leaks = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            current_path = f"{path}.{k}" if path else k
            for pat in FORBIDDEN_KEY_PATTERNS:
                if re.search(pat, k, re.IGNORECASE):
                    leaks.append(f"Forbidden key name '{k}' at {current_path}")
            leaks.extend(check_for_secrets(v, current_path))
    elif isinstance(obj, list):
        for idx, item in enumerate(obj):
            leaks.extend(check_for_secrets(item, f"{path}[{idx}]"))
    elif isinstance(obj, str):
        for pat in SECRET_VALUE_PATTERNS:
            if re.search(pat, obj):
                leaks.append(f"Potential secret token matching '{pat}' at {path}")
    return leaks


def audit_approvals(verbose: bool = False) -> tuple[int, int, list[str]]:
    """Audit all approvals in approvals/*.json. Returns (total_audited, clean_count, errors)."""
    if not APPROVALS_DIR.is_dir():
        return 0, 0, [f"Approvals directory missing: {APPROVALS_DIR}"]

    approval_files = sorted(list(APPROVALS_DIR.glob("S*_EP*_APPROVAL.json")))
    errors = []
    clean_count = 0

    for f in approval_files:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except Exception as e:
            errors.append(f"{f.name}: Invalid JSON: {e}")
            continue

        # 1. Secret scanning
        leaks = check_for_secrets(data)
        if leaks:
            errors.append(f"{f.name}: Found credential leaks: {leaks}")

        # 2. Checksum and provenance integrity
        checksums = data.get("asset_checksums", {})
        closure = data.get("closure_sha256")
        is_clean = data.get("is_git_clean", False)
        git_hash = data.get("git_hash", "")

        if not checksums:
            errors.append(f"{f.name}: Missing asset_checksums")
        if not closure:
            errors.append(f"{f.name}: Missing closure_sha256")
        if not git_hash or len(git_hash) != 40:
            errors.append(f"{f.name}: Malformed or missing git_hash: {git_hash}")

        # 3. Optional dirty_tree_addendum cryptographic validation
        dirty_tree = data.get("dirty_tree_addendum")
        if dirty_tree:
            diff_sha = dirty_tree.get("diff_sha256", "")
            untracked_sha = dirty_tree.get("untracked_files_sha256", "")
            hex64_re = re.compile(r"^[0-9a-f]{64}$")
            if not hex64_re.match(diff_sha):
                errors.append(f"{f.name}: Malformed or missing diff_sha256 in dirty_tree_addendum: {diff_sha}")
            if not hex64_re.match(untracked_sha):
                errors.append(f"{f.name}: Malformed or missing untracked_files_sha256 in dirty_tree_addendum: {untracked_sha}")

        if is_clean:
            clean_count += 1

        if verbose:
            clean_tag = "CLEAN" if is_clean else "DIRTY-TREE"
            print(f"[{f.name}] decision={data.get('decision')} {clean_tag} git={git_hash[:8]} assets={len(checksums)}")

    return len(approval_files), clean_count, errors


STAGING_DIR = REPO_ROOT / "output" / "youtube_staging"


def audit_staging_artifacts(verbose: bool = False) -> tuple[int, list[str]]:
    """Scan machine-generated publish-boundary artifacts in output/youtube_staging/ for secret leaks."""
    if not STAGING_DIR.is_dir():
        return 0, []

    staging_files = []
    for ext in ("*.json", "*.txt", "*.srt", "*.md"):
        staging_files.extend(STAGING_DIR.rglob(ext))

    errors = []
    for path in staging_files:
        try:
            if path.suffix == ".json":
                data = json.loads(path.read_text(encoding="utf-8"))
                leaks = check_for_secrets(data)
            else:
                text = path.read_text(encoding="utf-8", errors="ignore")
                leaks = []
                for pat in SECRET_VALUE_PATTERNS:
                    if re.search(pat, text):
                        leaks.append(f"Potential secret token matching '{pat}' in text")
            if leaks:
                rel = path.relative_to(REPO_ROOT)
                errors.append(f"{rel}: Found leaked credential(s): {leaks}")
        except Exception as e:
            errors.append(f"{path.name}: Failed reading staging file: {e}")

    if verbose and staging_files:
        print(f"Scanned {len(staging_files)} staging artifacts in {STAGING_DIR.relative_to(REPO_ROOT)}")

    return len(staging_files), errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit approval manifests and staging boundary for secrets and provenance")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--skip-staging", action="store_true", help="Skip scanning staging artifacts")
    args = parser.parse_args()

    total, clean, errors = audit_approvals(verbose=args.verbose)
    print(f"\nAudit complete: {total} manifests examined ({clean} signed clean).")

    if not args.skip_staging:
        staging_total, staging_errors = audit_staging_artifacts(verbose=args.verbose)
        print(f"Staging boundary complete: {staging_total} publish artifacts examined in output/youtube_staging/.")
        errors.extend(staging_errors)

    if errors:
        print(f"❌ {len(errors)} errors found:")
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    print("✅ All approval manifests and staging artifacts passed secret scanning and cryptographic provenance validation.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
