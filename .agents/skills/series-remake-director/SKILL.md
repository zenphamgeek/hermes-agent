---
name: series-remake-director
description: Plan and govern a ZenPham series remake when every episode must follow an approved knowledge graph, audiovisual contract, and hash-bound quality gates.
---

# Series Remake Director

Use this skill for a full remake of an existing ZenPham series. It governs the
series as a learning journey; it does not replace the Manim, voice, or Shorts
production skills for the work inside an individual episode.

## Entry gate

Do not start an Episode Contract, TTS, alignment, Manim render, mix, or publish
operation until `SERIES_CONTRACT_V1.json` has a matching human
`SERIES_PLANNER_APPROVAL_V1.json`. Read
[`../../rules/series_remake.md`](../../rules/series_remake.md) before changing
production state. Read-only research and audit remain allowed while blocked.

## Direct the remake in this order

1. Audit the existing plan, scripts, CTA edges, terminology and media evidence.
2. Establish a single Series Contract: thesis, audience, knowledge graph,
   episode promises, prerequisites, misconception, practical payoff, visual
   spine, open loop and CTA target.
3. Resolve scope collisions before writing. A repeated topic needs an explicit
   “foundation → advanced application” boundary, never two equivalent lessons.
4. Produce in topological prerequisite order, not merely episode-number order.
   Treat the first approved 20–40 second scene as a pilot; do not batch render
   a whole series from a speculative design.
5. For each episode, create the Episode Contract, final voice, strict word
   alignment, frame timeline, preview, final render, mix and three approvals.
6. Create its Short only after its longform promise and Related Video target are
   stable. One Short teaches one proof and leaves one truthful open loop.

## S1 editorial invariants

- Audience: working adults 22–40 who want usable AI/ML mental models without a
  presumed advanced-math background.
- Vietnamese is the grammatical base. English technical terms stay in standard
  spelling and are anchored inside the same Vietnamese sentence; do not use
  fake transliteration or a separate English repeat.
- Manim prose uses bundled Roboto Regular through `vi_text`; bold only conveys
  deliberate emphasis. Math stays separate from Vietnamese prose.
- Visual motion must expose a causal, physical or mathematical relationship.
  Omit a shadow or VFX that cannot be made truthful.
- A closing is 12–20 seconds, continues the episode’s visual spine, resolves
  its promise, and points to exactly one valid knowledge-graph successor.
- Internal labels, cue numbers, P0 dates and pipeline metadata never appear on
  screen.

## Required evidence

Automation may report only `PASS`, `ERROR` or `UNKNOWN`; it cannot certify
creative quality. Keep planner, audio, visual and golden approvals separate and
bound to hashes. If source, font, model, audio, alignment or final media changes,
the relevant approval is stale.

Use:

```bash
python3 assets/scripts_video/series_01/remake_pipeline.py status
python3 assets/scripts_video/series_01/remake_pipeline.py queue
python3 assets/scripts_video/series_01/remake_pipeline.py preflight \
  --episode S01E01 --contract EPISODE_CONTRACT_V1.json --media master.mp4 \
  --approvals-dir approvals
```

Read `manim-production`, `vietnamese-expressive-tts`, or `shorts-development` only when
performing that corresponding specialist stage. For audio production, `vietnamese-expressive-tts`
is the sole authorized Gold TTS standard. Where older conventions conflict with the S1 invariants
above or Gold TTS rules, this skill and project rules control.
