# Skill Development Standards

## Skill Structure Requirements

Every skill in `optional-skills/` and `skills/` MUST follow this structure:

```
skill-name/
├── SKILL.md              # Required — main instruction file
└── references/           # Optional — supporting docs
    └── *.md              # Reference files
```

## SKILL.md Frontmatter (Required)

```yaml
---
name: skill-name              # lowercase-hyphenated, matches directory name
description: One line.        # ≤256 chars, ends with period, no marketing terms
version: "1.0.0"              # Semantic versioning
author: hermes-community      # Or specific author
license: MIT                  # License identifier
platforms:                    # Where this skill works
  - telegram
  - cli
tags:                         # Searchable tags
  - coding
  - automation
related_skills:               # Cross-references
  - other-skill-name
---
```

### Frontmatter Validation Rules
- `name`: lowercase letters, digits, hyphens only; must start with letter
- `description`: ≤256 chars; ends with `.`; no marketing buzzwords ("revolutionary", "cutting-edge", "game-changing")
- `version`: present and valid
- `author`: present
- `license`: present
- `platforms`: list containing at least one platform
- `tags`: list with relevant tags

## SKILL.md Body Structure (Required Sections)

### Must Have:
1. `## When to Use` — trigger conditions (what messages activate this skill)
2. `## Prerequisites` — required software, services, credentials
3. `## How to Run` — brief execution method (terminal tool, browser, etc.)
4. `## Procedure` — step-by-step instructions with code blocks
5. `## Quick Reference` — command cheatsheet
6. `## Common Pitfalls` or `## Pitfalls` — known issues and workarounds
7. `## Verification` — how to confirm the skill worked

### Body Rules:
- **No machine-local paths**: Use `~/.hermes/` not `/home/zen/.hermes/`
- **Use terminal tool**: Reference `terminal(command=...)` for execution
- **Size limits**: 500 bytes ≤ SKILL.md ≤ 50KB
- **No lazy-reading pagination**: No `offset`/`limit` — models must read fully

## Reference Files

- Located in `references/` subdirectory
- No machine-local paths (`/home/<user>/`)
- Should contain dispatch tables, format specs, or technical details
- Agent reads these for implementation details, not for user display

## Test Files

Every skill MUST have a corresponding test at:
```
tests/skills/test_<skill_name_underscored>_skill.py
```

### Required Test Classes:
1. `TestFrontmatter` — validates YAML frontmatter fields
2. `TestBodyStructure` — validates required sections and content rules
3. `TestReferences` — validates reference files exist and are clean

### Running Skill Tests:
```bash
source .venv/bin/activate
python -m pytest tests/skills/test_<name>_skill.py -v
```

## Skill Categories

| Directory | Purpose |
|---|---|
| `skills/` | Built-in, active by default |
| `optional-skills/autonomous-ai-agents/` | IDE automation, vibe coding |
| `optional-skills/infrastructure/` | Server, container, database ops |
| `optional-skills/development/` | Dev tooling, testing, deployment |
| `~/.hermes/skills/` | User-local skills (not in repo) |

## Skill Loading

- Built-in skills: auto-loaded from `skills/` directory
- Optional skills: loaded on-demand when triggered
- User skills: loaded from `~/.hermes/skills/` on-demand
- **Never modify system prompt to load skills** — inject as user message to preserve prompt caching
