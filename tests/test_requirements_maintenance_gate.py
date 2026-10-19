"""Sovereign Multi-Repo requirements.txt Maintenance & PEP 508 Verification Gate.

Enforces that all core repositories maintain valid, non-conflicting, PEP 508-compliant
`requirements.txt` manifests synchronized with `pyproject.toml` for deterministic
fresh installation (`pip install -r requirements.txt`) and smooth test execution.
"""

from __future__ import annotations

from pathlib import Path
import tomllib
from typing import Dict, List, Set, Tuple

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name
import pytest


REPOSITORIES: Dict[str, Path] = {
    "hermes-agent": Path("/home/zen/hermes-agent"),
    "zencode-ent-router": Path("/home/zen/zencode-ent/router"),
    "zencode-ent-root": Path("/home/zen/zencode-ent"),
    "agy-pinned-monitor": Path("/home/zen/workspace/agy-pinned-monitor"),
    "VerticalRisk": Path("/home/zen/VerticalRisk"),
    "O20": Path("/home/zen/O20"),
}

EXPECTED_CORE_PACKAGES: Dict[str, Set[str]] = {
    "hermes-agent": {
        "openai",
        "httpx",
        "pydantic",
        "fastapi",
        "uvicorn",
        "mcp",
        "starlette",
        "cryptography",
        "psutil",
        "pillow",
        "numpy",
        "onnxruntime",
        "faster-whisper",
        "modal",
        "pytest",
        "pytest-asyncio",
    },
    "zencode-ent-router": {
        "fastapi",
        "uvicorn",
        "pydantic",
        "starlette",
        "python-multipart",
        "httpx",
        "requests",
        "anyio",
        "pyyaml",
        "orjson",
        "packaging",
        "numpy",
        "onnxruntime",
        "huggingface-hub",
        "safetensors",
        "cryptography",
        "psutil",
        "modal",
        "pillow",
        "mcp",
        "pytest",
        "pytest-asyncio",
    },
    "zencode-ent-root": {
        "fastapi",
        "pydantic",
        "httpx",
        "onnxruntime",
        "mcp",
        "pytest",
    },
    "agy-pinned-monitor": {
        "typer",
        "rich",
        "pydantic",
        "httpx",
        "fastapi",
        "uvicorn",
        "pytest",
        "pytest-asyncio",
    },
    "VerticalRisk": {
        "cryptography",
        "pydantic",
        "pydantic-settings",
        "fastapi",
        "uvicorn",
        "httpx",
        "sqlalchemy",
        "psycopg2-binary",
        "asyncpg",
        "aiosqlite",
        "lxml",
        "reportlab",
        "pypdf",
        "jsonschema",
        "pytest",
        "pytest-asyncio",
    },
    "O20": {
        "babel",
        "cryptography",
        "gevent",
        "greenlet",
        "jinja2",
        "lxml",
        "pillow",
        "psutil",
        "psycopg2",
        "reportlab",
        "requests",
        "werkzeug",
    },
}


def parse_requirements_file(req_file: Path, visited: Set[Path] | None = None) -> List[ Tuple[Requirement, Path, int] ]:
    """Recursively parse a requirements.txt file into PEP 508 Requirement objects."""
    if visited is None:
        visited = set()
    resolved = req_file.resolve()
    if resolved in visited:
        return []
    visited.add(resolved)

    parsed: List[Tuple[Requirement, Path, int]] = []
    lines = req_file.read_text(encoding="utf-8").splitlines()
    for idx, raw_line in enumerate(lines, start=1):
        # Strip inline comments (unless inside quotes, handled safely via split on ' #')
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if " #" in line:
            line = line.split(" #", 1)[0].strip()
        elif "\t#" in line:
            line = line.split("\t#", 1)[0].strip()

        if line.startswith("-r ") or line.startswith("--requirement "):
            target_rel = line.split(maxsplit=1)[1].strip()
            target_path = (req_file.parent / target_rel).resolve()
            assert target_path.is_file(), (
                f"Broken -r include in {req_file}:{idx} -> {target_path} does not exist"
            )
            parsed.extend(parse_requirements_file(target_path, visited))
            continue

        req = Requirement(line)
        parsed.append((req, req_file, idx))
    return parsed


@pytest.mark.parametrize("repo_name,repo_path", list(REPOSITORIES.items()))
def test_requirements_txt_exists_and_parses_valid_pep508(repo_name: str, repo_path: Path) -> None:
    """Verify every target repository has a non-empty, 100% PEP 508-valid requirements.txt."""
    if not repo_path.exists():
        pytest.skip(f"Repository path {repo_path} not mounted in this environment")

    req_file = repo_path / "requirements.txt"
    assert req_file.is_file(), f"[{repo_name}] Missing {req_file}"
    reqs = parse_requirements_file(req_file)
    assert len(reqs) >= 5, f"[{repo_name}] {req_file} has too few requirements ({len(reqs)})"


@pytest.mark.parametrize("repo_name,repo_path", list(REPOSITORIES.items()))
def test_no_unguarded_duplicate_packages_in_requirements(repo_name: str, repo_path: Path) -> None:
    """Ensure no package is declared twice without environment markers (e.g. python_version)."""
    if not repo_path.exists():
        pytest.skip(f"Repository path {repo_path} not mounted in this environment")

    req_file = repo_path / "requirements.txt"
    reqs = parse_requirements_file(req_file)
    seen_entries: Dict[str, List[Tuple[Requirement, Path, int]]] = {}
    for req, src_path, line_no in reqs:
        pkg_name = canonicalize_name(req.name)
        seen_entries.setdefault(pkg_name, []).append((req, src_path, line_no))

    for pkg_name, entries in seen_entries.items():
        if len(entries) > 1:
            # Every duplicate entry MUST be guarded by an environment marker
            unguarded = [
                f"{src.name}:{ln} ({r})"
                for r, src, ln in entries
                if r.marker is None
            ]
            assert not unguarded, (
                f"[{repo_name}] Unguarded duplicate package '{pkg_name}' in {req_file}: {unguarded}"
            )


@pytest.mark.parametrize("repo_name,repo_path", list(REPOSITORIES.items()))
def test_essential_runtime_and_test_packages_covered(repo_name: str, repo_path: Path) -> None:
    """Verify all essential runtime, inference, and test packages are present for fresh install."""
    if not repo_path.exists():
        pytest.skip(f"Repository path {repo_path} not mounted in this environment")

    req_file = repo_path / "requirements.txt"
    reqs = parse_requirements_file(req_file)
    present_packages = {canonicalize_name(req.name) for req, _, _ in reqs}
    expected = {canonicalize_name(pkg) for pkg in EXPECTED_CORE_PACKAGES[repo_name]}
    missing = sorted(expected - present_packages)
    assert not missing, (
        f"[{repo_name}] Missing critical packages in {req_file}: {missing}"
    )


def test_hermes_agent_requirements_synced_with_pyproject_core_dependencies() -> None:
    """Verify hermes-agent/requirements.txt includes 100% of pyproject.toml [project].dependencies."""
    repo_path = REPOSITORIES["hermes-agent"]
    if not repo_path.exists():
        pytest.skip("hermes-agent repository not present")

    pyproject_data = tomllib.loads((repo_path / "pyproject.toml").read_text(encoding="utf-8"))
    pyproject_deps = [Requirement(d) for d in pyproject_data["project"]["dependencies"]]
    req_deps = {
        canonicalize_name(r.name): r
        for r, _, _ in parse_requirements_file(repo_path / "requirements.txt")
    }

    for py_req in pyproject_deps:
        canon = canonicalize_name(py_req.name)
        assert canon in req_deps, (
            f"Core dependency '{py_req}' from hermes-agent/pyproject.toml is missing in requirements.txt"
        )
        assert req_deps[canon].specifier == py_req.specifier, (
            f"Version specifier drift for '{canon}': pyproject.toml has '{py_req.specifier}' "
            f"but requirements.txt has '{req_deps[canon].specifier}'"
        )


@pytest.mark.parametrize("repo_key", ["zencode-ent-router", "agy-pinned-monitor"])
def test_pyproject_and_requirements_parity(repo_key: str) -> None:
    """Verify pyproject.toml [project].dependencies are 100% represented in requirements.txt."""
    repo_path = REPOSITORIES[repo_key]
    if not repo_path.exists():
        pytest.skip(f"{repo_key} not present")

    pyproject_data = tomllib.loads((repo_path / "pyproject.toml").read_text(encoding="utf-8"))
    pyproject_deps = [Requirement(d) for d in pyproject_data["project"]["dependencies"]]
    req_deps = {
        canonicalize_name(r.name): r
        for r, _, _ in parse_requirements_file(repo_path / "requirements.txt")
    }

    for py_req in pyproject_deps:
        canon = canonicalize_name(py_req.name)
        assert canon in req_deps, (
            f"[{repo_key}] Dependency '{py_req}' in pyproject.toml is missing from requirements.txt"
        )
        assert req_deps[canon].specifier == py_req.specifier, (
            f"[{repo_key}] Specifier mismatch for '{canon}': pyproject.toml={py_req.specifier} "
            f"vs requirements.txt={req_deps[canon].specifier}"
        )
