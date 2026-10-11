"""Supply Chain Lockfile & Registry Integrity CI Guard.

Guards against supply-chain attacks, rogue npm registries, missing integrity hashes,
and credential leaks in npm configuration files (.npmrc, package-lock.json).
Inspired by adversarial Red Team recommendations from the AGY Fleet Swarm.
"""

import json
import os
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_package_lock_external_registries_strict():
    """Verify 100% of external npm packages resolve strictly to the official npmjs registry."""
    lockfile_path = REPO_ROOT / "package-lock.json"
    assert lockfile_path.is_file(), f"package-lock.json not found at {lockfile_path}"

    with open(lockfile_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    packages = data.get("packages", {})
    assert len(packages) > 0, "package-lock.json packages map must not be empty"

    LOCAL_WORKSPACE_PREFIXES = (
        "apps/",
        "ui-tui",
        "tests-js",
        "web",
    )

    rogue_packages = []
    missing_integrity = []

    for pkg_path, pkg_info in packages.items():
        if not pkg_path:  # root workspace entry
            continue

        resolved = pkg_info.get("resolved")
        integrity = pkg_info.get("integrity")

        # Skip local workspace package links
        if pkg_info.get("link") is True or any(pkg_path.startswith(p) for p in LOCAL_WORKSPACE_PREFIXES):
            continue
        if resolved and any(resolved.startswith(p) for p in LOCAL_WORKSPACE_PREFIXES):
            continue

        if resolved:
            # Must strictly point to official npm registry
            if not resolved.startswith("https://registry.npmjs.org/"):
                rogue_packages.append((pkg_path, resolved))

            # Must have valid integrity hash
            if not integrity or not re.match(r"^sha(512|1)-", integrity):
                missing_integrity.append((pkg_path, integrity))

    assert not rogue_packages, (
        f"Detected {len(rogue_packages)} packages pointing to unauthorized or rogue registries: {rogue_packages[:10]}"
    )
    assert not missing_integrity, (
        f"Detected {len(missing_integrity)} packages missing valid SHA integrity hashes: {missing_integrity[:10]}"
    )


def test_npmrc_security_and_quarantine():
    """Verify .npmrc enforces release age quarantine and contains zero plaintext secrets."""
    npmrc_path = REPO_ROOT / ".npmrc"
    if not npmrc_path.is_file():
        return

    content = npmrc_path.read_text(encoding="utf-8")

    # Verify no raw hardcoded authorization tokens
    token_matches = re.findall(r":_authToken=([^\s$]+)", content)
    for token in token_matches:
        assert token.startswith("${") and token.endswith("}"), (
            f"Found potential hardcoded npm auth token in .npmrc: {token[:6]}..."
        )

    # Verify quarantine policy (min-release-age)
    assert "min-release-age=" in content or "min-release-age = " in content, (
        ".npmrc must enforce supply-chain quarantine via min-release-age"
    )


def test_npmrc_bounded_cooldown_exclusions():
    """Verify min-release-age exclusions are tightly bounded and contain no unauthorized wildcards."""
    npmrc_path = REPO_ROOT / ".npmrc"
    if not npmrc_path.is_file():
        return

    content = npmrc_path.read_text(encoding="utf-8")
    exclusions = re.findall(r"min-release-age-exclude\[\]\s*=\s*([^\s#]+)", content)

    # Trigger.dev is pinned in package.json and must NEVER have blanket cooldown exclusion
    assert "@trigger.dev/*" not in exclusions, "Blanket scope wildcard @trigger.dev/* is forbidden"
    assert "trigger.dev" not in exclusions, "trigger.dev blanket exclusion is forbidden; pin version in package.json"


def test_npmrc_save_exact_enforced():
    """Verify .npmrc enforces exact dependency pinning via save-exact=true."""
    npmrc_path = REPO_ROOT / ".npmrc"
    assert npmrc_path.is_file(), ".npmrc must exist"
    content = npmrc_path.read_text(encoding="utf-8")
    assert "save-exact=true" in content or "save-exact = true" in content, (
        ".npmrc must declare save-exact=true to eliminate range widening on installs"
    )


def test_package_json_dependencies_exact_pins():
    """Verify all top-level root dependencies are pinned to exact versions (no floating wildcards)."""
    pkg_path = REPO_ROOT / "package.json"
    assert pkg_path.is_file()
    with open(pkg_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    deps = data.get("dependencies", {})
    floating_deps = []
    for name, ver in deps.items():
        if ver.startswith("^") or ver.startswith("~") or ver == "*" or "x" in ver:
            floating_deps.append((name, ver))

    assert not floating_deps, f"Found non-exact pinned dependencies in root package.json: {floating_deps}"
