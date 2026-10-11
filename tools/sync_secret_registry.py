#!/usr/bin/env python3
"""Single Source of Truth (SSOT) Secret Registry Synchronizer.

Derives .gitignore entries programmatically from .security/secret_paths.registry
to guarantee zero divergence between the ECS secret registry, .gitignore,
pre-commit hook, and server-side CI gates.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
REGISTRY_FILE = REPO_ROOT / ".security" / "secret_paths.registry"
GITIGNORE_FILE = REPO_ROOT / ".gitignore"

BLOCK_START = "# --- BEGIN ECS SECRET REGISTRY (SSOT) ---"
BLOCK_END = "# --- END ECS SECRET REGISTRY (SSOT) ---"


def load_registry_paths() -> list[str]:
    if not REGISTRY_FILE.is_file():
        raise FileNotFoundError(f"Missing secret registry: {REGISTRY_FILE}")
    lines = [
        line.strip()
        for line in REGISTRY_FILE.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    return sorted(list(dict.fromkeys(lines)))


def generate_block(paths: list[str]) -> str:
    inner = "\n".join(paths)
    return (
        f"{BLOCK_START}\n"
        f"# Generated automatically from .security/secret_paths.registry — DO NOT EDIT MANUALLY\n"
        f"{inner}\n"
        f"{BLOCK_END}"
    )


def sync_gitignore(check_only: bool = False) -> bool:
    paths = load_registry_paths()
    expected_block = generate_block(paths)

    if not GITIGNORE_FILE.is_file():
        raise FileNotFoundError(f"Missing .gitignore: {GITIGNORE_FILE}")

    content = GITIGNORE_FILE.read_text(encoding="utf-8")

    if BLOCK_START in content and BLOCK_END in content:
        before = content.split(BLOCK_START)[0]
        after = content.split(BLOCK_END)[1]
        new_content = f"{before}{expected_block}{after}"
    else:
        new_content = f"{content.rstrip()}\n\n{expected_block}\n"

    is_synced = (content == new_content)

    # Check if all paths are present anywhere in gitignore if check_only
    all_present = all(p in content for p in paths)

    if check_only:
        if not is_synced or not all_present:
            missing = [p for p in paths if p not in content]
            print(
                f"❌ .gitignore is out of sync with .security/secret_paths.registry!\n"
                f"Missing or misplaced entries: {missing}\n"
                f"Run 'python tools/sync_secret_registry.py' to synchronize.",
                file=sys.stderr,
            )
            return False
        print("✅ .gitignore is in 100% parity with .security/secret_paths.registry.")
        return True

    if not is_synced:
        GITIGNORE_FILE.write_text(new_content, encoding="utf-8")
        print(f"✅ Synchronized {len(paths)} secret patterns into .gitignore.")
    else:
        print("✅ .gitignore already synchronized.")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Synchronize .gitignore from .security/secret_paths.registry")
    parser.add_argument("--check", action="store_true", help="Check parity without modifying .gitignore")
    args = parser.parse_args()

    success = sync_gitignore(check_only=args.check)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
