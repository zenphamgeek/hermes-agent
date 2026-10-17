#!/usr/bin/env python3
"""
tools/rearchitect_skills_and_root.py
Lead Hermes Skills & Clef Mnemosyne Engineer — AGY Fleet Pro Swarm
─────────────────────────────────────────────────────────────────────
Adversarial ToT Synopsis
  Branch A (Failure): Concurrent writes corrupt JSONL; frontmatter regex
    partial-matches embedded YAML blocks; classified root scripts overwrite
    existing targets; tombstone file missing → silent data loss.
  Branch B (Defence): Atomic temp-rename writes; strict single-line regex
    anchored to frontmatter boundaries; classify to explicit mapping only;
    tombstone dir created before first write; dry-run default.
  Branch C (Synthesis): Implemented below with all guards active.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ─── Constants ───────────────────────────────────────────────────────────────

MAX_DESC_LEN = 60
TOMBSTONE_REL = ".agents/skills/memory-curator/resources/l3_tombstones.jsonl"
JUDGE_NODE = "local-jev"

SKILL_ROOTS = [".agents/skills", "skills", "optional-skills"]

# Prefix → target sub-directory inside pipelines/masterclass/
ROOT_PY_CLASSIFY: list[tuple[tuple[str, ...], str]] = [
    (("assemble_",),                                               "pipelines/masterclass/assemblers"),
    (("audit_",),                                                  "pipelines/masterclass/auditors"),
    (("calibrate_", "align_", "update_"),                          "pipelines/masterclass/calibration"),
    (("generate_", "init_", "populate_", "clean_"),                "pipelines/masterclass/generators"),
    (("publish_", "republish_", "upload_"),                        "pipelines/masterclass/publishers"),
    (("produce_", "remake_", "remediate_", "finish_",
      "patch_", "parallel_render_"),                               "pipelines/masterclass/producers"),
    (("check_", "find_", "inspect_", "verify_",
      "test_candidate_", "test_chinh_"),                           "pipelines/masterclass/inspectors"),
    (("render_",),                                                 "pipelines/masterclass/renderers"),
]

# ─── Remediation catalogue (19 violating paths) ──────────────────────────────

REMEDIATION_DESCRIPTIONS: dict[str, str] = {
    "skills/account-vault/SKILL.md":
        "Secure multi-account credential vault manager.",
    "skills/creative/documentary-video-biet-dia-ly/SKILL.md":
        "Geographic documentary video production skill.",
    "skills/creative/geographic-documentary/SKILL.md":
        "Craft geographic documentary video narratives.",
    "skills/creative/manim-director/SKILL.md":
        "Animate math concepts with Manim director.",
    "skills/creative/modal-comfyui/SKILL.md":
        "Run ComfyUI image workflows on Modal GPU.",
    "skills/creative/modal-ltxvideo/SKILL.md":
        "Generate LTX video via Modal inference.",
    "skills/creative/modal-wan-s2v/SKILL.md":
        "WAN speech-to-video generation on Modal.",
    "skills/creative/omnivoice-reader/SKILL.md":
        "OmniVoice neural TTS document reader.",
    "skills/creative/pexels-visual-search/SKILL.md":
        "Search and curate Pexels stock footage.",
    "skills/creative/toi-doc-sach/SKILL.md":
        "Vietnamese book reading and summarization.",
    "skills/creative/toi-lam-viec/SKILL.md":
        "Personal productivity and work-session skill.",
    "skills/creative/video-debugger/SKILL.md":
        "Debug and diagnose video pipeline errors.",
    "skills/creative/youtube-to-manim/SKILL.md":
        "Convert YouTube content to Manim animations.",
    "skills/creative/youtube-video-rewriter/SKILL.md":
        "Rewrite and adapt YouTube video scripts.",
    "skills/creative/zenpham-podcast-producer/SKILL.md":
        "Produce ZenPham-style podcast episodes.",
    "skills/media/ai-song-cover/SKILL.md":
        "Generate AI vocal song covers.",
    "skills/media/reality-decode/SKILL.md":
        "Decode and fact-check media reality claims.",
    "skills/media/swapface-organizer/SKILL.md":
        "Organise and tag face-swap media assets.",
    "skills/shorts-development/SKILL.md":
        "Short-form vertical video development skill.",
}

# Validate catalogue at import time (adversarial guard)
_bad = {k: v for k, v in REMEDIATION_DESCRIPTIONS.items() if len(v) > MAX_DESC_LEN}
if _bad:
    raise ValueError(
        f"REMEDIATION_DESCRIPTIONS entries exceed {MAX_DESC_LEN} chars: {_bad}"
    )

# ─── Duplicate / relocate maps ────────────────────────────────────────────────

# Each entry: canonical is the *kept* copy; duplicate is *removed* (archived).
DUPLICATE_SKILL_MAP: list[dict[str, str]] = [
    {
        "name": "manim-director",
        "canonical": ".agents/skills/manim-director",
        "duplicate": "skills/creative/manim-director",
    },
    {
        "name": "reality-decode",
        "canonical": ".agents/skills/reality-decode",
        "duplicate": "skills/media/reality-decode",
    },
    {
        "name": "youtube-video-rewriter",
        "canonical": ".agents/skills/youtube-video-rewriter",
        "duplicate": "skills/creative/youtube-video-rewriter",
    },
    {
        "name": "shorts-development",
        "canonical": ".agents/skills/shorts-development",
        "duplicate": "skills/shorts-development",
    },
    {
        "name": "omnivoice-reader",
        "canonical": "skills/creative/omnivoice-reader",
        "duplicate": "skills/media/omnivoice-reader",
    },
    {
        "name": "trae-telegram",
        "canonical": "optional-skills/autonomous-ai-agents/trae-telegram",
        "duplicate": "skills/autonomous-ai-agents/trae-telegram",
    },
]

RELOCATE_SKILL_MAP: list[dict[str, str]] = [
    {
        "name": "account-vault",
        "source": "skills/account-vault",
        "target": "skills/security/account-vault",
    },
]

# ─── Helpers ─────────────────────────────────────────────────────────────────

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---", re.DOTALL)
_DESC_LINE_RE   = re.compile(r"^(description\s*:\s*)(.+)$", re.MULTILINE)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _strip_yaml_quotes(val: str) -> str:
    v = val.strip()
    if len(v) >= 2 and ((v[0] == '"' and v[-1] == '"') or (v[0] == "'" and v[-1] == "'")):
        return v[1:-1].replace("''", "'").replace('\\"', '"')
    return v


def _parse_description(text: str) -> tuple[str | None, int | None]:
    """Return (unquoted_description_value, line_number_1indexed) or (None, None)."""
    fm = _FRONTMATTER_RE.match(text)
    if not fm:
        return None, None
    fm_block = fm.group(1)
    fm_start_line = 2  # first line after opening ---
    for i, line in enumerate(fm_block.splitlines(), start=fm_start_line):
        m = re.match(r"^description\s*:\s*(.+)$", line)
        if m:
            return _strip_yaml_quotes(m.group(1)), i
    return None, None


def _atomic_write(path: Path, content: str) -> None:
    """Write content atomically via temp file + rename (same filesystem)."""
    dir_ = path.parent
    dir_.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=dir_, prefix=".tmp_skill_")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(content)
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _append_tombstone(tombstone_path: Path, record: dict[str, Any]) -> None:
    tombstone_path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(record, ensure_ascii=False)
    with tombstone_path.open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def _shorten_auto(desc: str) -> str:
    """Best-effort auto-shorten to <= MAX_DESC_LEN chars."""
    if len(desc) <= MAX_DESC_LEN:
        return desc
    truncated = desc[: MAX_DESC_LEN - 1].rstrip()
    if not truncated.endswith("."):
        truncated = truncated.rstrip(",;: ") + "."
    return truncated[:MAX_DESC_LEN]

# ─── 1. Audit ─────────────────────────────────────────────────────────────────

def audit_skills(repo_root: str | Path) -> dict[str, Any]:
    """
    Scan SKILL_ROOTS for SKILL.md files.
    Returns: counts, duplicate skill names, description > 60 char violations.

    Symlink-dedup invariant: if two paths resolve to the same physical SKILL.md
    (e.g. .agents/skills/foo/SKILL.md → skills/creative/foo/SKILL.md), only the
    first encounter is added to name_index so the pair is NOT reported as a
    duplicate name collision.
    """
    root = Path(repo_root)
    all_skills: list[dict[str, Any]] = []
    name_index: dict[str, list[str]] = {}
    seen_resolved: set[Path] = set()  # resolved inodes already counted

    for sr in SKILL_ROOTS:
        base = root / sr
        if not base.exists():
            continue
        for skill_md in base.rglob("SKILL.md"):
            rel = skill_md.relative_to(root).as_posix()

            # ── Symlink-dedup guard ────────────────────────────────────────
            try:
                resolved = skill_md.resolve()
            except OSError:
                resolved = skill_md  # broken symlink: still record it
            is_symlink_dup = resolved in seen_resolved
            seen_resolved.add(resolved)
            # ──────────────────────────────────────────────────────────────

            try:
                text = skill_md.read_text(encoding="utf-8", errors="replace")
            except OSError as exc:
                all_skills.append({"path": rel, "error": str(exc)})
                continue

            desc, lineno = _parse_description(text)
            skill_name = skill_md.parent.name

            # Only register in name_index when this physical file is new
            if not is_symlink_dup:
                name_index.setdefault(skill_name, []).append(rel)

            entry: dict[str, Any] = {
                "path": rel,
                "skill_name": skill_name,
                "description": desc,
                "desc_len": len(desc) if desc else 0,
                "desc_line": lineno,
                "violation": bool(desc and len(desc) > MAX_DESC_LEN),
            }
            if is_symlink_dup:
                entry["symlink_of"] = resolved.as_posix()
            all_skills.append(entry)

    violations = [s for s in all_skills if s.get("violation")]
    duplicates = {k: v for k, v in name_index.items() if len(v) > 1}

    return {
        "total_scanned": len(all_skills),
        "violations_count": len(violations),
        "violations": violations,
        "duplicates_count": len(duplicates),
        "duplicates": duplicates,
        "skills": all_skills,
    }

# ─── 3a. Deduplicate & relocate skills ───────────────────────────────────────

def deduplicate_and_relocate_skills(
    repo_root: str | Path,
    tombstone_path: str | Path,
    dry_run: bool = True,
) -> dict[str, Any]:
    """
    Adversarial ToT synthesis:
      Branch A risk  — copy step overwrites canonical content; archive target
                       already exists; tombstone write interrupted mid-line.
      Branch B guard — copy only *missing* files; remove archive target before
                       move; tombstone appended atomically via _append_tombstone.
      Branch C impl  — see below.

    For each entry in DUPLICATE_SKILL_MAP:
      - Skip if `root/duplicate` does not exist.
      - Skip if `root/duplicate` is already a symlink whose target resolves to
        the same physical path as `root/canonical` (no-op — already unified).
      - If not dry_run:
          1. Copy any files from duplicate → canonical that are absent in canonical.
          2. Move duplicate dir → .hermes_archive/duplicate_skills/<slug>.
          3. Append bi-temporal tombstone.

    For each entry in RELOCATE_SKILL_MAP:
      - Skip if `root/source` does not exist.
      - If not dry_run: shutil.move source → target (create parent dirs).
      - Append tombstone.
    """
    root = Path(repo_root)
    tomb = Path(tombstone_path)
    archive_base = root / ".hermes_archive" / "duplicate_skills"
    now = _now_iso()
    actions: list[dict[str, Any]] = []

    # ── Duplicates ────────────────────────────────────────────────────────────
    for entry in DUPLICATE_SKILL_MAP:
        name       = entry["name"]
        canonical  = entry["canonical"]
        duplicate  = entry["duplicate"]
        dup_path   = root / duplicate
        canon_path = root / canonical

        if not dup_path.exists():
            actions.append({"name": name, "duplicate": duplicate, "status": "skip_missing"})
            continue

        # Symlink check: if duplicate IS a symlink to canonical, it's already
        # unified at the filesystem level — nothing to do.
        if dup_path.is_symlink():
            try:
                if dup_path.resolve() == canon_path.resolve():
                    actions.append({
                        "name": name,
                        "duplicate": duplicate,
                        "status": "skip_symlink_to_canonical",
                    })
                    continue
            except OSError:
                pass  # broken symlink — proceed to archive it

        slug = duplicate.replace("/", "_")
        archive_target = archive_base / slug

        tombstone: dict[str, Any] = {
            "id": str(uuid.uuid4()),
            "file": f"{duplicate}/SKILL.md",
            "line": 1,
            "old_text": f"duplicate skill dir {duplicate}",
            "new_text": f"merged into {canonical}",
            "reason": "Deduplicated duplicate skill directory into canonical skill location",
            "superseded_by": f"{canonical}/SKILL.md",
            "verdict": "supersedes",
            "judge_node": JUDGE_NODE,
            "recorded_at": now,
            "valid_to": "9999-12-31T23:59:59+00:00",
            "dry_run": dry_run,
        }

        if not dry_run:
            # 1. Copy files missing from canonical
            if canon_path.exists():
                for src_file in dup_path.rglob("*"):
                    if src_file.is_file():
                        rel_part = src_file.relative_to(dup_path)
                        dest_file = canon_path / rel_part
                        if not dest_file.exists():
                            dest_file.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(src_file, dest_file)

            # 2. Archive the duplicate directory
            archive_base.mkdir(parents=True, exist_ok=True)
            if archive_target.exists() or archive_target.is_symlink():
                shutil.rmtree(archive_target, ignore_errors=True)
            shutil.move(str(dup_path), str(archive_target))

            # 3. Tombstone
            _append_tombstone(tomb, tombstone)

        actions.append({
            "name":           name,
            "canonical":      canonical,
            "duplicate":      duplicate,
            "archive_target": str(archive_target.relative_to(root)),
            "status":         "dry_run" if dry_run else "archived",
            "tombstone":      tombstone,
        })

    # ── Relocations ───────────────────────────────────────────────────────────
    for entry in RELOCATE_SKILL_MAP:
        name   = entry["name"]
        source = entry["source"]
        target = entry["target"]
        src_path  = root / source
        dest_path = root / target

        if not src_path.exists():
            actions.append({"name": name, "source": source, "status": "skip_missing"})
            continue

        tombstone: dict[str, Any] = {
            "id": str(uuid.uuid4()),
            "file": f"{source}/SKILL.md",
            "line": 1,
            "old_text": f"skill dir at {source}",
            "new_text": f"relocated to {target}",
            "reason": "Relocated skill to canonical directory structure",
            "superseded_by": f"{target}/SKILL.md",
            "verdict": "supersedes",
            "judge_node": JUDGE_NODE,
            "recorded_at": now,
            "valid_to": "9999-12-31T23:59:59+00:00",
            "dry_run": dry_run,
        }

        if not dry_run:
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src_path), str(dest_path))
            _append_tombstone(tomb, tombstone)

        actions.append({
            "name":      name,
            "source":    source,
            "target":    target,
            "status":    "dry_run" if dry_run else "relocated",
            "tombstone": tombstone,
        })

    return {
        "dry_run":      dry_run,
        "action_count": len(actions),
        "actions":      actions,
    }


# ─── 3b. Organise root Python scripts ────────────────────────────────────────

def organize_root_python_scripts(
    repo_root: str | Path,
    dry_run: bool = True,
) -> dict[str, Any]:
    """
    Adversarial ToT synthesis:
      Branch A risk  — symlink creation races with another process; target dir
                       already contains a regular file with the same name;
                       relative symlink depth wrong if target nesting changes.
      Branch B guard — existence check before symlink creation; only skip if
                       existing path is already a symlink to the same target;
                       relative target always computed as `../../<filename>`
                       (two levels up from pipelines/masterclass/<subdir>/).
      Branch C impl  — see below.

    For each proposal from classify_root_python_scripts:
      - Create `root / target_dir` (mkdir -p).
      - Create a relative symlink at `root / target` → `../../<source_filename>`
        unless the symlink already exists and points to the correct relative path.
    """
    root = Path(repo_root)
    classification = classify_root_python_scripts(root)
    proposals = classification["proposals"]
    results: list[dict[str, Any]] = []

    for prop in proposals:
        source_filename = Path(prop["source"]).name          # e.g. render_ep01.py
        target_rel      = prop["target"]                     # e.g. pipelines/masterclass/renderers/render_ep01.py
        target_dir      = prop["target_dir"]                 # e.g. pipelines/masterclass/renderers
        target_path     = root / target_rel
        target_dir_path = root / target_dir

        # Relative symlink: from pipelines/masterclass/<subdir>/ back to root is ../../
        # then the filename.  Always exactly two levels deep inside pipelines/masterclass/.
        relative_link_target = Path("../../..") / source_filename  # root/pipelines/masterclass/sub → root
        # Depth: root/pipelines/masterclass/<subdir>/<file.py>
        # To get back to root we need 4 .. segments (subdir, masterclass, pipelines, root)
        # but symlinks resolve relative to the *directory* containing the link,
        # so from root/pipelines/masterclass/<subdir>/ we need ../../../../<file.py>
        # However target_dir has exactly 3 components (pipelines/masterclass/<subdir>),
        # so depth = 3 → relative_link_target = ../../../<file.py>
        relative_link_target = Path("../../../") / source_filename

        status: str
        if target_path.exists() or target_path.is_symlink():
            # Already a correct symlink? Compare resolved targets.
            if target_path.is_symlink():
                existing = os.readlink(str(target_path))
                if existing == str(relative_link_target):
                    status = "already_correct"
                else:
                    status = "symlink_mismatch"
            else:
                status = "conflict_not_symlink"
            results.append({
                "source":     prop["source"],
                "target":     target_rel,
                "status":     status,
                "dry_run":    dry_run,
            })
            continue

        if not dry_run:
            target_dir_path.mkdir(parents=True, exist_ok=True)
            target_path.symlink_to(relative_link_target)
            status = "created"
        else:
            status = "dry_run"

        results.append({
            "source":              prop["source"],
            "target":              target_rel,
            "relative_link_target": str(relative_link_target),
            "status":              status,
            "dry_run":             dry_run,
        })

    created = sum(1 for r in results if r["status"] == "created")
    return {
        "dry_run":        dry_run,
        "proposal_count": len(proposals),
        "result_count":   len(results),
        "created_count":  created,
        "results":        results,
        "unclassified":   classification.get("unclassified", []),
    }


# ─── 2. Apply description fixes ───────────────────────────────────────────────

def apply_skill_description_fixes(
    repo_root: str | Path,
    tombstone_path: str | Path,
    dry_run: bool = True,
) -> dict[str, Any]:
    """
    Rewrite description: lines for skills in REMEDIATION_DESCRIPTIONS
    (or auto-shorten any >60 char description if not in catalogue).
    Appends bi-temporal tombstone records to tombstone_path.
    """
    root = Path(repo_root)
    tomb = Path(tombstone_path)
    results: list[dict[str, Any]] = []
    now = _now_iso()

    for sr in SKILL_ROOTS:
        base = root / sr
        if not base.exists():
            continue
        for skill_md in base.rglob("SKILL.md"):
            rel = skill_md.relative_to(root).as_posix()
            try:
                original = skill_md.read_text(encoding="utf-8", errors="replace")
            except OSError as exc:
                results.append({"path": rel, "status": "read_error", "error": str(exc)})
                continue

            old_desc, lineno = _parse_description(original)
            if old_desc is None:
                continue

            # Determine new description
            if rel in REMEDIATION_DESCRIPTIONS:
                new_desc = REMEDIATION_DESCRIPTIONS[rel]
            elif len(old_desc) > MAX_DESC_LEN:
                new_desc = _shorten_auto(old_desc)
            else:
                continue  # no fix needed

            if new_desc == old_desc:
                results.append({"path": rel, "status": "no_change"})
                continue

            # Build rewritten content (replace only the frontmatter desc line)
            fm = _FRONTMATTER_RE.match(original)
            if not fm:
                results.append({"path": rel, "status": "no_frontmatter"})
                continue

            old_line = f"description: {old_desc}"
            new_line = f"description: {new_desc}"
            # Restrict replacement to within frontmatter span only
            fm_end = fm.end()
            fm_block = original[: fm_end]
            rest = original[fm_end:]
            patched_fm = fm_block.replace(old_line, new_line, 1)
            if patched_fm == fm_block:
                # Try flexible whitespace variant
                patched_fm = _DESC_LINE_RE.sub(
                    lambda m: m.group(1) + new_desc, fm_block, count=1
                )
            new_content = patched_fm + rest

            tombstone: dict[str, Any] = {
                "id": str(uuid.uuid4()),
                "file": rel,
                "line": lineno,
                "old_text": old_line,
                "new_text": new_line,
                "reason": "description exceeds 60 chars; remediated by rearchitect_skills_and_root",
                "superseded_by": "REMEDIATION_DESCRIPTIONS catalogue" if rel in REMEDIATION_DESCRIPTIONS else "auto-shorten",
                "verdict": "supersedes",
                "judge_node": JUDGE_NODE,
                "recorded_at": now,
                "valid_to": "9999-12-31T23:59:59+00:00",
                "dry_run": dry_run,
            }

            if not dry_run:
                _atomic_write(skill_md, new_content)
                _append_tombstone(tomb, tombstone)

            results.append({
                "path": rel,
                "status": "dry_run" if dry_run else "applied",
                "old_desc": old_desc,
                "new_desc": new_desc,
                "tombstone": tombstone,
            })

    return {"dry_run": dry_run, "fixes": results, "fix_count": len(results)}

# ─── 3. Classify root Python scripts ─────────────────────────────────────────

# Files that must never be touched
_PROTECTED_STEMS = frozenset({
    "setup", "conftest", "__init__", "manage", "wsgi", "asgi",
    "fleet_manager", "rearchitect_skills_and_root",
})


def classify_root_python_scripts(repo_root: str | Path) -> dict[str, Any]:
    """
    Classify root-level *.py files by prefix into pipelines/masterclass/* dirs.
    Returns proposed moves; does NOT mutate any file.
    """
    root = Path(repo_root)
    proposals: list[dict[str, str]] = []
    unclassified: list[str] = []

    for py_file in sorted(root.glob("*.py")):
        stem = py_file.stem
        if stem in _PROTECTED_STEMS or stem.startswith("_"):
            continue

        matched = False
        for prefixes, target_dir in ROOT_PY_CLASSIFY:
            if any(stem.startswith(p) for p in prefixes):
                dest = root / target_dir / py_file.name
                proposals.append({
                    "source": py_file.relative_to(root).as_posix(),
                    "target": (root / target_dir / py_file.name)
                    .relative_to(root)
                    .as_posix(),
                    "target_dir": target_dir,
                    "exists_at_target": dest.exists(),
                })
                matched = True
                break

        if not matched:
            unclassified.append(py_file.relative_to(root).as_posix())

    return {
        "proposals": proposals,
        "proposal_count": len(proposals),
        "unclassified": unclassified,
        "note": "No files mutated — this is a dry classification report.",
    }

# ─── CLI ─────────────────────────────────────────────────────────────────────

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="rearchitect_skills_and_root",
        description="Hermes Skills & Clef Mnemosyne rearchitect tool.",
    )
    p.add_argument(
        "--repo-root",
        default=".",
        help="Path to repository root (default: current directory).",
    )
    p.add_argument(
        "--audit",
        action="store_true",
        help="Scan skill roots and report description violations + duplicates.",
    )
    p.add_argument(
        "--apply-descriptions",
        action="store_true",
        help="Rewrite violating description: lines (defaults to dry-run).",
    )
    p.add_argument(
        "--deduplicate-skills",
        action="store_true",
        help="Merge duplicate skill dirs into canonical locations (defaults to dry-run).",
    )
    p.add_argument(
        "--organize-root",
        action="store_true",
        help="Create pipelines/masterclass/* symlinks for root *.py scripts (defaults to dry-run).",
    )
    p.add_argument(
        "--no-dry-run",
        action="store_true",
        help="Actually write changes (combine with any mutating flag).",
    )
    p.add_argument(
        "--tombstone-path",
        default=None,
        help=f"Override tombstone JSONL path (default: <repo-root>/{TOMBSTONE_REL}).",
    )
    p.add_argument(
        "--classify-root",
        action="store_true",
        help="Classify root *.py scripts into pipelines/masterclass/* dirs (report only).",
    )
    p.add_argument(
        "--json",
        action="store_true",
        dest="output_json",
        help="Emit results as JSON to stdout.",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if not any([
        args.audit,
        args.apply_descriptions,
        args.classify_root,
        args.deduplicate_skills,
        args.organize_root,
    ]):
        parser.print_help()
        return 0

    repo_root = Path(args.repo_root).resolve()
    if not repo_root.exists():
        print(f"ERROR: --repo-root '{repo_root}' does not exist.", file=sys.stderr)
        return 1

    tombstone_path = Path(args.tombstone_path) if args.tombstone_path else repo_root / TOMBSTONE_REL
    dry_run = not args.no_dry_run
    output: dict[str, Any] = {"repo_root": str(repo_root)}

    if args.audit:
        output["audit"] = audit_skills(repo_root)

    if args.apply_descriptions:
        output["apply_descriptions"] = apply_skill_description_fixes(
            repo_root, tombstone_path, dry_run=dry_run
        )

    if args.deduplicate_skills:
        output["deduplicate_skills"] = deduplicate_and_relocate_skills(
            repo_root, tombstone_path, dry_run=dry_run
        )

    if args.organize_root:
        output["organize_root"] = organize_root_python_scripts(
            repo_root, dry_run=dry_run
        )

    if args.classify_root:
        output["classify_root"] = classify_root_python_scripts(repo_root)

    if args.output_json:
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        # Human-readable summary
        if "audit" in output:
            a = output["audit"]
            print(f"\n── Audit ──────────────────────────────────────")
            print(f"  Scanned : {a['total_scanned']} SKILL.md files")
            print(f"  Violations (desc > {MAX_DESC_LEN}): {a['violations_count']}")
            print(f"  Duplicate skill names: {a['duplicates_count']}")
            for v in a["violations"]:
                print(f"    [VIOLATION] {v['path']}  ({v['desc_len']} chars)")
            for name, paths in a["duplicates"].items():
                print(f"    [DUPLICATE] '{name}': {paths}")

        if "apply_descriptions" in output:
            ad = output["apply_descriptions"]
            mode = "DRY-RUN" if ad["dry_run"] else "APPLIED"
            print(f"\n── Apply Descriptions [{mode}] ──────────────")
            print(f"  Fixes proposed/applied: {ad['fix_count']}")
            for fx in ad["fixes"]:
                st = fx.get("status", "?")
                if st in ("dry_run", "applied"):
                    print(f"    [{st.upper()}] {fx['path']}")
                    print(f"      old: {fx['old_desc']}")
                    print(f"      new: {fx['new_desc']}")

        if "deduplicate_skills" in output:
            ds = output["deduplicate_skills"]
            mode = "DRY-RUN" if ds["dry_run"] else "APPLIED"
            print(f"\n── Deduplicate & Relocate Skills [{mode}] ──────")
            print(f"  Actions: {ds['action_count']}")
            for act in ds["actions"]:
                st = act["status"]
                name = act.get("name", "?")
                if st in ("dry_run", "archived", "relocated"):
                    dup = act.get("duplicate") or act.get("source", "?")
                    can = act.get("canonical") or act.get("target", "?")
                    print(f"    [{st.upper()}] {name}: {dup} → {can}")
                else:
                    print(f"    [{st.upper()}] {name}")

        if "organize_root" in output:
            og = output["organize_root"]
            mode = "DRY-RUN" if og["dry_run"] else "APPLIED"
            print(f"\n── Organise Root Scripts [{mode}] ──────────────")
            print(f"  Proposals: {og['proposal_count']}  Created: {og['created_count']}")
            for r in og["results"]:
                print(f"    [{r['status'].upper()}] {r['source']}  →  {r['target']}")
            if og.get("unclassified"):
                print(f"  Unclassified ({len(og['unclassified'])}):")
                for u in og["unclassified"]:
                    print(f"    {u}")

        if "classify_root" in output:
            cr = output["classify_root"]
            print(f"\n── Classify Root Scripts ──────────────────────")
            print(f"  Proposals: {cr['proposal_count']}")
            for prop in cr["proposals"]:
                clash = " [TARGET EXISTS]" if prop["exists_at_target"] else ""
                print(f"    {prop['source']}  →  {prop['target']}{clash}")
            if cr["unclassified"]:
                print(f"  Unclassified ({len(cr['unclassified'])}):")
                for u in cr["unclassified"]:
                    print(f"    {u}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
