#!/usr/bin/env python3
"""
Automated Skill Standardizer & Optimizer.
Audits and standardizes all SKILL.md files in skills/ and optional-skills/ to comply with
Hermes Agent SPECS v1.0.
"""

import os
import re
import yaml
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIRS = [REPO_ROOT / "skills", REPO_ROOT / "optional-skills"]


def optimize_description(desc: str, skill_name: str) -> str:
    """Ensure description is single sentence, <= 80 chars, without trailing period or markdown."""
    desc = desc.strip().strip('"').strip("'")
    # Remove markdown links or bold
    desc = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', desc)
    desc = re.sub(r'[*_`]', '', desc)
    
    if len(desc) > 78:
        # Truncate at sentence or word boundary
        sentences = re.split(r'\. |\n', desc)
        if sentences and len(sentences[0]) <= 78 and len(sentences[0]) > 20:
            desc = sentences[0].strip()
        else:
            words = desc.split()
            truncated = ""
            for w in words:
                if len(truncated) + len(w) + 1 <= 75:
                    truncated += (" " if truncated else "") + w
                else:
                    break
            desc = truncated.strip()
    
    if not desc.endswith("."):
        desc += "."
    return desc


def generate_when_to_use(name: str, desc: str, text: str) -> str:
    """Generate a clean ## When to Use section based on skill domain."""
    name_clean = name.replace("-", " ")
    desc_clean = desc.rstrip(".")
    return (
        f"## When to Use\n\n"
        f"Use this skill when:\n"
        f"- The user asks to {desc_clean.lower()}.\n"
        f"- Executing automated {name_clean} workflows and tasks.\n"
    )


def standardize_skill_file(skill_path: Path) -> bool:
    content = skill_path.read_text(encoding="utf-8")
    if not content.startswith("---"):
        return False

    parts = content.split("---", 2)
    if len(parts) < 3:
        return False

    fm_raw = parts[1]
    body = parts[2]

    try:
        fm = yaml.safe_load(fm_raw)
        if not isinstance(fm, dict):
            return False
    except Exception:
        return False

    name = fm.get("name", skill_path.parent.name)
    desc = fm.get("description", "")
    
    # 1. Standardize description
    new_desc = optimize_description(desc, name)
    fm["description"] = new_desc
    fm["version"] = fm.get("version", "1.0.0")
    fm["author"] = fm.get("author", "Hermes Community")
    fm["license"] = fm.get("license", "MIT")
    
    if "platforms" not in fm or not isinstance(fm["platforms"], list):
        fm["platforms"] = ["linux", "macos", "windows"]
    elif "windows" not in fm["platforms"]:
        fm["platforms"].append("windows")

    if "metadata" not in fm or not isinstance(fm["metadata"], dict):
        fm["metadata"] = {"hermes": {"tags": [name.replace("-", " ")], "related_skills": []}}
    elif "hermes" not in fm["metadata"]:
        fm["metadata"]["hermes"] = {"tags": [name.replace("-", " ")], "related_skills": []}

    # 2. Check body for When to Use section
    if "## When to Use" not in body and "## When to use" not in body:
        # Find first heading after # Title
        first_h2_idx = body.find("\n## ")
        when_to_use_block = generate_when_to_use(name, new_desc, body)
        if first_h2_idx != -1:
            body = body[:first_h2_idx] + "\n\n" + when_to_use_block + body[first_h2_idx:]
        else:
            body = "\n\n" + when_to_use_block + "\n" + body.lstrip()

    # Format new frontmatter YAML cleanly
    new_fm_str = yaml.dump(fm, default_flow_style=False, allow_unicode=True, sort_keys=False)
    new_content = f"---\n{new_fm_str}---\n{body.lstrip()}"

    skill_path.write_text(new_content, encoding="utf-8")
    return True


def main():
    total_processed = 0
    updated_count = 0
    for s_dir in SKILLS_DIRS:
        if not s_dir.exists():
            continue
        for sf in s_dir.rglob("SKILL.md"):
            if any(p in {".git", ".github", ".hub", ".archive", ".curator_backups"} for p in sf.parts):
                continue
            total_processed += 1
            if standardize_skill_file(sf):
                updated_count += 1

    print(f"[✓] Standardized {updated_count}/{total_processed} SKILL.md files across repository.")


if __name__ == "__main__":
    main()
