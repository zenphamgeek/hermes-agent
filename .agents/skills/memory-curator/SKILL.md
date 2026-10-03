---
name: memory-curator
description: "Clef Mnemosyne memory curator: detects superseded knowledge across episodic (L1), semantic (L2) and normative (L3: AGENTS.md, .agents/rules, skills) memory. Classifies each candidate as supersedes/refines/contradicts/mentions_as_deprecated/unrelated via a Judge/Auditor fleet node, requires evidence before SUPERSEDE, archives with tombstones instead of deleting, and (P3) auto-removes stale L3 lines only when a strict auto-apply gate holds, committing on fleet/judge/memory-curation-YYYYWW and fast-forwarding main; everything else is quarantined for the Council."
version: 0.2.0
author: ZENPHAM & Antigravity
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [memory, curation, forgetting, supersession, quality-gate, judge, clef-mnemosyne]
    related_skills: [zenpham-series-auditor, vietnamese-expressive-tts]
---

# Memory Curator — Clef Mnemosyne (P3)

> Forgetting ≠ deleting. Forgetting removes stale knowledge from the *active context*;
> the original evidence always survives in an archive (tombstone + git).

Design reference: `clef_memory_curator_design.md` §2, §4.1, §4.3, §5.

## 1. When to run

| Trigger | Scope | Action |
|---|---|---|
| Every 6h while fleet admission = `NORMAL` | L1 → L2 | COMPRESS / ARCHIVE episodes |
| Weekly (Sun 03:00, cron) | L3 | `curate_l3.py --apply`: Judge-classify, gated auto-apply, quarantine rest, report |
| Event: user declares "X is abandoned" (e.g. TTS V8) | All tiers | Add X to `resources/deprecations.json`, scan immediately |

Run the curator on a **Judge/Auditor** fleet node, never on the Builder node that produced the knowledge.

## 2. The seven operations

| Op | When | Tier | Automatic? |
|---|---|---|---|
| `KEEP` | Still used and still true | all | yes |
| `MERGE` | ≥2 entries say the same thing | L1, L2 | yes |
| `COMPRESS` | N episodes share a pattern → 1 lesson + stats + source episode ids | L1→L2 | yes |
| `SUPERSEDE` | Newer knowledge, same scope, **with evidence** | L2 | yes (logged) |
| `SUPERSEDE` | same | L3 | **only through the §4.1 auto-apply gate**, tombstoned |
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
   | `supersedes` | New knowledge replaces old, same scope | SUPERSEDE (L3: only if §4.1 gate holds, else QUARANTINE) |
   | `refines` | New narrows/extends old; old remains partly valid | edit proposal, keep history |
   | `contradicts` | Conflict, no evidence for either side | QUARANTINE |
   | `mentions_as_deprecated` | Text *describes* old concept as abandoned/forbidden | **KEEP** — it is a guard rail |
   | `unrelated` | Pattern collision (e.g. "cấm" about another topic) | KEEP |
3. **Verify (deterministic)**: accept `supersedes` **only** if the newer side cites at least one
   checkable artifact — a passing test, a commit, an on-disk measurement, or an explicit user
   decision recorded in AGENTS.md / a rule. No artifact → downgrade to `QUARANTINE`.
   Newer-but-unproven is never enough.

## 4. L3 curation (P3): gated auto-removal

Auto-removal on L3 was explicitly authorized by the user (design §8 question 2). It is
**gated**: anything that fails a single clause is QUARANTINED, never applied.

- L3 = `AGENTS.md`, `.agents/rules/*.md`, `.agents/skills/*/SKILL.md` (this skill excluded).
- Runner: `scripts/curate_l3.py` — scan → judge → gate → rewrite + tombstone → commit → ff-merge.
  ```bash
  python3 .agents/skills/memory-curator/scripts/curate_l3.py            # --dry-run (default), writes nothing in repo
  python3 .agents/skills/memory-curator/scripts/curate_l3.py --apply    # weekly scheduled mode
  python3 .agents/skills/memory-curator/scripts/curate_l3.py --judge offline --offline-verdicts v.json
  ```
- **Judge backend**: arouter `POST http://localhost:7777/api/fleet/run-sync`
  (`{"prompt", "node_name", "timeout"}`), routed to a node labelled `Judge`/`Auditor`
  (prefers `ultra-2`). Fleet nodes have no filesystem, so each prompt carries ±6 lines of
  context and the registry entry. Transport error, non-`completed` job, rerouting to a
  non-Judge node, or unparsable JSON → **QUARANTINE**.

### 4.1 Auto-apply gate (all must hold)

1. Judge verdict is `supersedes` (`mentions_as_deprecated`/`unrelated` → KEEP; `refines`/`contradicts` → QUARANTINE).
2. Heuristic pre-label is `candidate_live_instruction` **or** the judge quote is verbatim in the line
   (a non-verbatim quote always quarantines).
3. The registry entry has an explicit `replacement`.
4. Target is **not** `AGENTS.md` and **not** `.agents/rules/05_modal_gpu_fleet_and_token_invariants.md`.
5. The line is not inside a dated benchmark/history block (date on the line, or nearest heading
   has a date / benchmark / history / changelog / lịch sử / nhật ký).
6. The judge's single-line replacement differs from the original and, when re-scanned, matches
   **no** deprecated pattern.
7. The line is identical at `HEAD` (no concurrent uncommitted edit by another agent).

### 4.2 Apply, tombstone, commit

- Minimal one-line rewrite in place (indentation and line endings preserved).
- Tombstone appended to `resources/l3_tombstones.jsonl`: `file, line, old_text` (full line),
  `new_text, reason, superseded_by, verdict, judge_node, recorded_at, valid_to` (+ `concept_id,
  quote, source_of_truth, op, tier`).
- Report: `resources/runs/YYYYWW.md` (applied / quarantined / skipped). Dry-run reports go to
  `/tmp/memory-curator-runs/YYYYWW.dry-run.md`.
- Commit uses a temporary git index containing **only** the curated paths (other agents'
  uncommitted work is never swept in) on `fleet/judge/memory-curation-YYYYWW`, then
  fast-forwards `main` with a compare-and-swap `update-ref`. **Never pushes.**
- Schedule: user crontab, Sunday 03:00 local, `--apply`, log `~/.hermes/logs/memory_curator_l3.log`.
  Disable by deleting the line tagged `# memory-curator-l3-weekly` (`crontab -e`).
- Rollback: `git revert <sha>` or restore `old_text` from the tombstone.

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
