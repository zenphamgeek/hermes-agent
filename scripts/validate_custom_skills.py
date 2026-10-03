#!/usr/bin/env python3
"""Custom Skills Validator & Sync Tool for Hermes Agent.

Audits custom skills against Hermes Hardline Standards & SKILL_SPECS.md.
Validates frontmatter, description length, mandatory sections, native tool conventions,
and ensures synchronization between repository skills/ and ~/.hermes/skills/.

Usage:
    python3 scripts/validate_custom_skills.py [--fix] [--sync] [--all]
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple

# Ensure hermes-agent root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.skill_linter import lint_skill, ERROR, WARNING, LintFinding
from hermes_constants import get_hermes_home

USER_SKILLS_DIR = get_hermes_home() / "skills"
REPO_SKILLS_DIR = REPO_ROOT / "skills"

# Targeted custom skills
KNOWN_CUSTOM_SKILLS: Set[str] = {
    "sync-hs-knowledge",
    "sync-hse-knowledge",
    "youtube-channel-srt",
    "vietnam-stock-daily-brief",
    "vietnam-stock-watchlist",
    "vietnam-legal-crawler",
    "swapface-folder",
    "trae-telegram",
    "trae-screen-analyst",
    "electron-ide-cdp-automation",
    "omnivoice-reader",
    "agnes-ai-video",
    "media-asset-bank",
    "cloakbrowser",
}




def find_skills_in_dir(base_dir: Path, target_names: Set[str] | None = None) -> Dict[str, Path]:
    """Find all SKILL.md files mapped by skill name."""
    found: Dict[str, Path] = {}
    if not base_dir.exists():
        return found

    for skill_md in base_dir.rglob("SKILL.md"):
        if any(p in {".git", ".github", ".hub", ".archive", ".curator_backups"} for p in skill_md.parts):
            continue
        skill_name = skill_md.parent.name
        if target_names is None or skill_name in target_names or skill_name.startswith("sync-"):
            found[skill_name] = skill_md
    return found


def audit_skills(skills_map: Dict[str, Path]) -> Tuple[int, int, Dict[str, List[LintFinding]]]:
    """Audit found skills using Hermes skill_linter."""
    total_errors = 0
    total_warnings = 0
    results: Dict[str, List[LintFinding]] = {}

    for name, skill_md in sorted(skills_map.items()):
        findings = lint_skill(skill_md)
        results[name] = findings
        for f in findings:
            if f.severity == ERROR:
                total_errors += 1
            else:
                total_warnings += 1

    return total_errors, total_warnings, results


def sync_skill(source_dir: Path, target_dir: Path) -> None:
    """Sync a skill directory recursively, excluding __pycache__ and git."""
    target_dir.mkdir(parents=True, exist_ok=True)
    for root, dirs, files in os.walk(source_dir):
        # Filter out hidden or build dirs
        dirs[:] = [d for d in dirs if d not in {"__pycache__", ".git", ".pytest_cache"}]
        rel_root = Path(root).relative_to(source_dir)
        dest_root = target_dir / rel_root
        dest_root.mkdir(parents=True, exist_ok=True)
        for f in files:
            src_file = Path(root) / f
            dest_file = dest_root / f
            shutil.copy2(src_file, dest_file)


def sync_all_custom_skills() -> None:
    """Synchronize custom skills between repo skills/ and ~/.hermes/skills/."""
    print("🔄 Synchronizing custom skills between workspace and ~/.hermes/skills/...")
    
    # 1. Sync from repo to user dir
    for name in KNOWN_CUSTOM_SKILLS:
        # Find in repo
        repo_matches = list(REPO_SKILLS_DIR.rglob(f"**/{name}"))
        if repo_matches:
            repo_skill_dir = repo_matches[0]
            rel_path = repo_skill_dir.relative_to(REPO_SKILLS_DIR)
            target_user_dir = USER_SKILLS_DIR / rel_path
            sync_skill(repo_skill_dir, target_user_dir)
            print(f"  ✓ Synced {name} -> {target_user_dir}")

    # 2. Sync from user dir to repo for user-only custom skills
    for name in KNOWN_CUSTOM_SKILLS:
        repo_matches = list(REPO_SKILLS_DIR.rglob(f"**/{name}"))
        if not repo_matches:
            user_matches = list(USER_SKILLS_DIR.rglob(f"**/{name}"))
            if user_matches:
                user_skill_dir = user_matches[0]
                rel_path = user_skill_dir.relative_to(USER_SKILLS_DIR)
                target_repo_dir = REPO_SKILLS_DIR / rel_path
                sync_skill(user_skill_dir, target_repo_dir)
                print(f"  ✓ Imported {name} into repo -> {target_repo_dir}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit and validate custom skills.")
    parser.add_argument("--all", action="store_true", help="Audit all skills, not just custom skills.")
    parser.add_argument("--sync", action="store_true", help="Sync custom skills between repo and user directory.")
    args = parser.parse_args()

    if args.sync:
        sync_all_custom_skills()

    targets = None if args.all else KNOWN_CUSTOM_SKILLS

    print("================================================================")
    print("         HERMES CUSTOM SKILLS AUDIT & SPECS VALIDATOR           ")
    print("================================================================")

    # 1. Check Repo Skills
    repo_skills = find_skills_in_dir(REPO_SKILLS_DIR, targets)
    print(f"\n📂 Workspace Skills Directory: {REPO_SKILLS_DIR}")
    print(f"   Found {len(repo_skills)} targeted custom skills.")
    repo_err, repo_warn, repo_results = audit_skills(repo_skills)

    for name, findings in repo_results.items():
        path = repo_skills[name]
        rel_path = path.relative_to(REPO_SKILLS_DIR)
        if not findings:
            print(f"  ✅ \033[92m[PASS]\033[0m {name} ({rel_path})")
        else:
            print(f"  ⚠️  \033[93m[FINDINGS]\033[0m {name} ({rel_path}):")
            for f in findings:
                print(f"      {f.format()}")

    # 2. Check User Profile Skills
    user_skills = find_skills_in_dir(USER_SKILLS_DIR, targets)
    print(f"\n📂 Runtime User Skills Directory: {USER_SKILLS_DIR}")
    print(f"   Found {len(user_skills)} targeted custom skills.")
    user_err, user_warn, user_results = audit_skills(user_skills)

    for name, findings in user_results.items():
        path = user_skills[name]
        rel_path = path.relative_to(USER_SKILLS_DIR)
        if not findings:
            print(f"  ✅ \033[92m[PASS]\033[0m {name} ({rel_path})")
        else:
            print(f"  ⚠️  \033[93m[FINDINGS]\033[0m {name} ({rel_path}):")
            for f in findings:
                print(f"      {f.format()}")

    total_err = repo_err + user_err
    total_warn = repo_warn + user_warn

    print("\n----------------------------------------------------------------")
    print(f"Audit Summary: {total_err} errors, {total_warn} warnings.")
    if total_err == 0 and total_warn == 0:
        print("\033[92m🎉 ALL CUSTOM SKILLS COMPLY 100% WITH HERMES SPECS!\033[0m")
        return 0
    elif total_err == 0:
        print("\033[93m⚠️  Passed with advisory warnings. Please standardize to zero warnings.\033[0m")
        return 1
    else:
        print("\033[91m❌ FAILED: Critical errors detected in custom skills.\033[0m")
        return 1


if __name__ == "__main__":
    sys.exit(main())
