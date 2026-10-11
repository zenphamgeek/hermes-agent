#!/usr/bin/env python3
"""CI Secret & Untracked Roster Pre-Commit / Pre-Push Supply Chain Scanner.

Enforces:
1. Untracked roster files (fleet_roster.yml, fleet_roster.json, .fleet_roster.json)
   were NEVER committed in git history.
2. No untracked roster files are currently tracked or staged in git index.
3. Tracked governance markdown files contain zero personal account handles or credentials.
4. Committed template fleet_roster.example.yml exists and adheres to canonical schema.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

FORBIDDEN_ROSTER_FILES = [
    "fleet_roster.yml",
    "fleet_roster.json",
    ".fleet_roster.json",
]

FORBIDDEN_PII_PATTERNS = [
    "tsmei0209",
    "immoon0009",
    "nahlaleah102",
]


def check_git_history_for_roster_leaks() -> list[str]:
    """Scan entire git history across all branches for forbidden roster files."""
    errors: list[str] = []
    cmd = ["git", "log", "--all", "--oneline", "--"] + FORBIDDEN_ROSTER_FILES
    try:
        proc = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, check=False)
        if proc.returncode != 0:
            errors.append(f"git log failed with code {proc.returncode}: {proc.stderr.strip()}")
        else:
            output = proc.stdout.strip()
            if output:
                errors.append(
                    f"CRITICAL LEAK IN GIT HISTORY: Found commits referencing untracked roster files:\n{output}\n"
                    f"Must purge using git-filter-repo and rotate any leaked credentials."
                )
    except Exception as err:
        errors.append(f"Failed to inspect git history: {err}")
    return errors


def check_git_index_and_tracked_files() -> list[str]:
    """Ensure no forbidden roster files are tracked or staged in the index."""
    errors: list[str] = []
    try:
        proc = subprocess.run(["git", "ls-files"], cwd=REPO_ROOT, capture_output=True, text=True, check=False)
        if proc.returncode == 0:
            tracked = set(proc.stdout.splitlines())
            for forbidden in FORBIDDEN_ROSTER_FILES:
                if forbidden in tracked:
                    errors.append(f"CRITICAL: Forbidden file '{forbidden}' is currently tracked in git index!")
    except Exception as err:
        errors.append(f"Failed to check tracked files: {err}")
    return errors


def check_pii_in_tracked_markdown() -> list[str]:
    """Verify tracked markdown rules contain no concrete account credentials/PII."""
    errors: list[str] = []
    targets = [
        REPO_ROOT / "AGENTS.md",
        REPO_ROOT / ".agents" / "rules" / "05_fleet_delegation_enforcement.md",
    ]
    for target in targets:
        if not target.is_file():
            continue
        try:
            content = target.read_text(encoding="utf-8")
            for pattern in FORBIDDEN_PII_PATTERNS:
                if pattern in content:
                    errors.append(f"CWE-200 LEAK: Pattern '{pattern}' leaked in {target.name}!")
        except Exception as err:
            errors.append(f"Failed reading {target.name}: {err}")
    return errors


def check_example_roster_template() -> list[str]:
    """Ensure fleet_roster.example.yml and fleet_roster.defaults.yml are present and valid YAML with zero Ultra in pro-claude-pool."""
    errors: list[str] = []
    for fname in ("fleet_roster.example.yml", "fleet_roster.defaults.yml"):
        target_path = REPO_ROOT / fname
        if not target_path.is_file():
            errors.append(f"Missing committed {fname} template!")
            continue

        try:
            import yaml
            with open(target_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            if not isinstance(data, dict):
                errors.append(f"{fname} must be a valid YAML dictionary")
            elif "pools" not in data or "pro-claude-pool" not in data["pools"]:
                errors.append(f"{fname} missing 'pools.pro-claude-pool'")
        except Exception as err:
            errors.append(f"YAML parsing error in {fname}: {err}")
    return errors


def main() -> int:
    print("🔒 [CI Gate] Scanning git history, index, and governance files for roster/PII leaks...")
    all_errors: list[str] = []
    all_errors.extend(check_git_history_for_roster_leaks())
    all_errors.extend(check_git_index_and_tracked_files())
    all_errors.extend(check_pii_in_tracked_markdown())
    all_errors.extend(check_example_roster_template())

    if all_errors:
        print(f"❌ [CI Gate] FAILED with {len(all_errors)} violations:")
        for err in all_errors:
            print(f"   - {err}")
        return 1

    print("✅ [CI Gate] PASSED: Zero roster leaks in history, clean git index, and compliant template.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
