---
name: memory-curator
description: "Clef Mnemosyne memory curator: detects superseded knowledge across episodic (L1), semantic (L2) and normative (L3: AGENTS.md, .agents/rules, skills) memory. Classifies each candidate as supersedes/refines/contradicts/mentions_as_deprecated/unrelated, requires evidence before SUPERSEDE, archives with tombstones instead of deleting, and only PROPOSES L3 changes on a fleet/judge/memory-curation-YYYYWW branch that is never auto-merged."
version: 0.1.0
author: ZENPHAM & Antigravity
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [memory, curation, forgetting, supersession, quality-gate, judge, clef-mnemosyne]
    related_skills: [zenpham-series-auditor, vietnamese-expressive-tts]
---

# Memory Curator — Clef Mnemosyne (P2)

> Forgetting ≠ deleting. Forgetting removes stale knowledge from the *active context*;
> the original evidence always survives in an archive (tombstone + git).

Design reference: `clef_memory_curator_design.md` §2, §4.1, §4.3, §5.

## 1. When to run

| Trigger | Scope | Action |
|---|---|---|
| Every 6h while fleet admission = `NORMAL` | L1 → L2 | COMPRESS / ARCHIVE episodes |
| Weekly | L3 | Run scanner, Judge-classify, open proposal branch + report |
| Event: user declares "X is abandoned" (e.g. TTS V8) | All tiers | Add X to `resources/deprecations.json`, scan immediately |

Run the curator on a **Judge/Auditor** fleet node, never on the Builder node that produced the knowledge.

## 2. The seven operations

| Op | When | Tier | Automatic? |
|---|---|---|---|
| `KEEP` | Still used and still true | all | yes |
| `MERGE` | ≥2 entries say the same thing | L1, L2 | yes |
| `COMPRESS` | N episodes share a pattern → 1 lesson + stats + source episode ids | L1→L2 | yes |
| `SUPERSEDE` | Newer knowledge, same scope, **with evidence** | L2 | yes (logged) |
| `SUPERSEDE` | same | L3 | **no — proposal branch only** |
| `ARCHIVE` | TTL expired, low retention score | L1, L2 | yes |
| `QUARANTINE` | Contradiction not yet adjudicable | all | flag, wait for Council |
| `DELETE` | Only leaked secrets or fabricated data (Zero-Fake-Pass breach) | all | **no — needs user confirmation** |

## 3. Supersession pipeline (§4.3)

1. **Gather candidates (local, cheap, read-only)**
   ```bash
   python3 .agents/skills/memory-curator/scripts/scan_superseded.py --out /tmp
   ```
   Emits `superseded_scan.md` + `superseded_scan.json` with heuristic pre-labels
   `mentions_as_deprecated` / `candidate_live_instruction`. Pre-labels are **not verdicts**.
2. **Classify (Judge node)** each hit, quoting the source text verbatim, into exactly one of:

   | Label | Meaning | Consequence |
   |---|---|---|
   | `supersedes` | New knowledge replaces old, same scope | SUPERSEDE (L3: propose only) |
   | `refines` | New narrows/extends old; old remains partly valid | edit proposal, keep history |
   | `contradicts` | Conflict, no evidence for either side | QUARANTINE |
   | `mentions_as_deprecated` | Text *describes* old concept as abandoned/forbidden | **KEEP** — it is a guard rail |
   | `unrelated` | Pattern collision (e.g. "cấm" about another topic) | KEEP |
3. **Verify (deterministic)**: accept `supersedes` **only** if the newer side cites at least one
   checkable artifact — a passing test, a commit, an on-disk measurement, or an explicit user
   decision recorded in AGENTS.md / a rule. No artifact → downgrade to `QUARANTINE`.
   Newer-but-unproven is never enough.

## 4. L3 is propose-only

- L3 = `AGENTS.md`, `.agents/rules/*.md`, `.agents/skills/*/SKILL.md`.
- The curator **never edits L3 on the working branch**. It creates a branch
  `fleet/judge/memory-curation-YYYYWW` (ISO year + week, e.g. `fleet/judge/memory-curation-202640`)
  containing the proposed diff plus the report, and stops.
- The branch is **never merged by an agent** (Clef R6: never merge to main). The user decides.
- Each proposed hunk must cite: the stale line (file:line + quote), the source of truth
  (e.g. AGENTS.md §1.4), and the evidence artifact.

## 5. Tombstone / archive principle

Every ARCHIVE or SUPERSEDE writes a tombstone:

```json
{"id": "...", "op": "SUPERSEDE", "tier": "L2", "superseded_by": "...",
 "reason": "...", "evidence": ["tests/test_x.py::test_y PASSED", "commit abc123"],
 "valid_from": "...", "valid_to": "...", "recorded_at": "...", "original_ref": "path or git sha"}
```

- Bi-temporal: `valid_from`/`valid_to` (true in the world) vs `recorded_at` (when we learned it),
  so "what did we use for X in September?" stays answerable (Gate G5).
- Gate G1: count before = count after + archived. Nothing vanishes without a tombstone.

## 6. Quality gates (§5)

| Gate | Check |
|---|---|
| G1 | No evidence loss (tombstone reconciliation) |
| G2 | Existing pytest suite still green after curation |
| G3 | Precision ≥ 0.95 on `supersedes` against frozen `resources/g3_fixture.json` |
| G4 | Context size (rules + memory tokens) decreases with G2 green |
| G5 | Fixed recall questions answerable from archive |

The scanner heuristic alone does **not** meet G3 (see `tests/test_memory_curator_scanner.py`
for the measured number). A Judge pass is mandatory before any SUPERSEDE proposal.

## 7. Anti-patterns

- **Deleting on mere recency.** "Newer" is not "true". Without an evidence artifact → QUARANTINE.
- **Treating a deprecation notice as a live instruction.** Lines like
  "BÃI BỎ HOÀN TOÀN TTS V8" or "atempo < 1.0 ... FORBIDDEN" are guard rails. Removing them
  re-opens the door to the abandoned practice. Label them `mentions_as_deprecated` and KEEP.
- **Trusting nearby markers blindly.** A "CẤM"/"KHÔNG" within ±3 lines often refers to a
  different topic (afftdn, splicing, hardsubs) and hides a stale live instruction. Read the sentence.
- **Rewriting canonical author scripts.** Narration scripts are author canon (AGENTS.md §1.1);
  the curator never edits script text, only rules/skills/memory.
- **Self-certifying.** The node that wrote a rule may not be the node that retires it.
- **Merging the proposal branch.** Never. Report and stop.
- **Silent DELETE.** Only for leaked secrets / fabricated data, and only with user confirmation.

## 8. Files

| Path | Purpose |
|---|---|
| `scripts/scan_superseded.py` | Read-only candidate scanner (stdlib only) |
| `resources/deprecations.json` | Registry: deprecated concept → patterns, replacement, source of truth |
| `resources/g3_fixture.json` | Frozen manual ground truth for Gate G3 |
| `tests/test_memory_curator_scanner.py` (repo root) | Behaviour + read-only + precision report |
