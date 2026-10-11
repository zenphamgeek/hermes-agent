#!/usr/bin/env python3
"""Full-site mirror: crawl a website and deploy it to assets/website/<name>/.

Wraps `wget --mirror` (full-site mirror, converts links for offline browsing)
and syncs the result into a deploy directory. Safe to re-run: files are
timestamped so only changed pages are re-fetched.

Usage:
  mirror_site.py crawl --url https://example.com --name example
  mirror_site.py crawl --url https://example.com --name example --exclude '*.pdf'
  mirror_site.py deploy --name example     # deploy existing staging without re-crawling
  mirror_site.py status --name example
"""

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

STATE_FILE = ".mirror-state.json"
STAGING_DIR = ".staging"


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _domain(url: str) -> str:
    return url.split("://", 1)[1].split("/")[0].split(":")[0]


def _deploy(staging: Path, target: Path) -> int:
    """Copy staging into the deploy tree; returns number of files copied.

    wget nests everything under staging/<host>/... — flatten the host dir.
    """
    host_dirs = [p for p in staging.iterdir() if p.is_dir()]
    source = host_dirs[0] if len(host_dirs) == 1 else staging
    copied = 0
    for p in source.rglob("*"):
        if p.is_dir():
            continue
        rel = p.relative_to(source)
        out = target / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        if not out.exists() or out.stat().st_mtime < p.stat().st_mtime:
            shutil.copy2(p, out)
            copied += 1
    return copied


def _file_count(target: Path) -> int:
    """Count deployed files, excluding the state file and staging tree."""
    return sum(
        1 for p in target.rglob("*")
        if p.is_file() and p.name != STATE_FILE and STAGING_DIR not in p.parts
    )


def mirror(url: str, deploy_root: Path, name: str, excludes: list[str], timeout: int, extra_domains: list[str], exclude_domains: list[str]) -> dict:
    target = deploy_root / name
    target.mkdir(parents=True, exist_ok=True)
    staging = target / STAGING_DIR
    staging.mkdir(parents=True, exist_ok=True)  # persist across runs: wget --timestamping resumes incrementally

    domains = [_domain(url)] + extra_domains
    # --domains suffix-matches all subdomains (c3.ai => *.c3.ai). Allow
    # excluding noisy SaaS subdomains (ir., learn., community., ...) that
    # hang or rate-limit the crawl.
    exclude_domains = [d for d in exclude_domains if d not in domains]
    cmd = [
        "wget",
        "--mirror",
        "--convert-links",
        "--adjust-extension",
        "--page-requisites",
        "--no-parent",
        "--span-hosts",
        "--domains", ",".join(domains),
        "--timestamping",
        "--directory-prefix",
        str(staging),
    ]
    for ex in excludes:
        cmd += ["--reject", ex]
    if exclude_domains:
        cmd += ["--exclude-domains", ",".join(exclude_domains)]
    cmd.append(url)

    try:
        subprocess.run(cmd, check=True, timeout=timeout)
        ok, error = True, None
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        # Large sites rarely finish in one window. Deploy what we have as a
        # partial mirror; the next tick resumes via wget --timestamping.
        ok, error = False, str(e)

    # wget nests everything under staging/<host>/... — flatten the host dir.
    host_dirs = [p for p in staging.iterdir() if p.is_dir()]
    source = host_dirs[0] if len(host_dirs) == 1 else staging

    copied = 0
    for p in source.rglob("*"):
        if p.is_dir():
            continue
        rel = p.relative_to(source)
        out = target / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        if not out.exists() or out.stat().st_mtime < p.stat().st_mtime:
            shutil.copy2(p, out)
            copied += 1

    # keep staging: next run resumes via wget --timestamping
    copied = _deploy(staging, target)
    file_count = _file_count(target)
    state = {
        "ok": ok,
        "error": error,
        "url": url,
        "name": name,
        "deploy_dir": str(target),
        "copied": copied,
        "file_count": file_count,
        "last_run": _utcnow(),
    }
    (target / STATE_FILE).write_text(json.dumps(state, indent=2), encoding="utf-8")
    return state


def deploy(deploy_root: Path, name: str, url: str | None = None) -> dict:
    """Deploy the existing staging tree without re-crawling."""
    target = deploy_root / name
    if not target.exists():
        return {"ok": False, "error": f"no mirror at {target}; crawl first"}
    staging = target / STAGING_DIR
    if not staging.exists() or not any(staging.iterdir()):
        return {"ok": False, "error": f"empty staging at {staging}; crawl first"}
    copied = _deploy(staging, target)
    state = {
        "ok": True,
        "error": None,
        "url": url or "",
        "name": name,
        "deploy_dir": str(target),
        "copied": copied,
        "file_count": _file_count(target),
        "last_run": _utcnow(),
        "mode": "deploy",
    }
    (target / STATE_FILE).write_text(json.dumps(state, indent=2), encoding="utf-8")
    return state


def status(deploy_root: Path, name: str) -> dict:
    state_path = deploy_root / name / STATE_FILE
    if not state_path.exists():
        return {"ok": False, "error": f"no state for {name}; crawl first"}
    return json.loads(state_path.read_text(encoding="utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("crawl")
    c.add_argument("--root", default="assets/website", help="deploy root (default: assets/website)")
    c.add_argument("--url", required=True)
    c.add_argument("--name", required=True)
    c.add_argument("--exclude", action="append", default=[], help="wget --reject glob; repeatable")
    c.add_argument("--extra-domain", action="append", default=[], help="CDN/asset host to include in --domains (media parity); repeatable")
    c.add_argument("--exclude-domain", action="append", default=[], help="host suffix to exclude from --domains (e.g. ir.c3.ai); repeatable")
    c.add_argument("--timeout", type=int, default=3600)

    s = sub.add_parser("status")
    s.add_argument("--root", default="assets/website", help="deploy root (default: assets/website)")
    s.add_argument("--name", required=True)

    d = sub.add_parser("deploy")
    d.add_argument("--root", default="assets/website", help="deploy root (default: assets/website)")
    d.add_argument("--name", required=True)
    d.add_argument("--url", default=None, help="source URL to record in state (optional)")

    args = ap.parse_args()
    root = Path(args.root)
    if args.cmd == "crawl":
        result = mirror(args.url, root, args.name, args.exclude, args.timeout, args.extra_domain, args.exclude_domain)
    elif args.cmd == "deploy":
        result = deploy(root, args.name, args.url)
    else:
        result = status(root, args.name)

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
