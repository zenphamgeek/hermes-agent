# Hermes Agent & Content Factory — Master Sovereign Development Guide

> **Core Philosophy**: Never give up on the right solution. Keep the core waist narrow; harness optimization; enforce evidence-first verification.

---

## 1. Sovereign Quality Invariants (Immutable & Adversarial)

The Multidisciplinary Council (Hội đồng Cố vấn & Kiểm định Đa ngành) enforces these non-negotiable invariants across all pipelines (ZENPHAM, Biết Địa Lý Từ Ba Tôi, Tôi Đọc Sách, Reality Decode, Longform Masterclass, Shorts):

### 1.1. Council Integrity, Zero-Fake-Pass & Canonical Fidelity Invariant
The Council exists as an adversarial truth-seeking body, NOT a rubber stamp or placation device:
- **Zero-Fake-Pass**: Never claim tests or audits passed without executing real tools on real assets in the current session (no trivial mocks, no `assert True` cheats).
- **Zero-Fabricated-Audit**: Never invent numbers, timestamps, LUFS levels, True Peak levels, or Whisper probabilities without actual measurement.
- **Script Canonical Fidelity (Anti-Dodging)**: When a TTS model distorts or slurs a word (e.g., *"chính thức"*), NEVER alter or dodge the author's canonical script text to circumvent the defect — diagnose the mathematical, tokenization, or acoustic root cause and resolve it on the ground.
- **Anti-Context-Drift**: When context compacts or turns advance, never guess or assume previous tasks succeeded — anchor against disk state (`git status`, `.wav`, `.mp4`, `.json`) as the single source of truth.
*(See detailed legal charter in `.agents/rules/01_council_integrity_and_macro_structure.md` and `.agents/rules/council_integrity_and_anti_fabrication_rules.md`)*.

### 1.2. Evidence-First Verification
Any assertion regarding code correctness, visual layout compliance, audio mastering, or video publishing MUST be accompanied by real, measured tool execution evidence in the current session (e.g. AST collision count = 0 via `visual_quality_gate.py`, EBU R128 integrated loudness via `ffmpeg ebur128`, 2K frame artifacts, real YouTube Video ID returned via API). Never claim "Done", "Zero defects", or "Published" without verifiable proof.

### 1.3. Gold Macro-Structure (5 Sections / 10-Clip Assembly)
Every Longform Masterclass episode MUST assemble exactly 10 clips across 5 structured sections:
1. **Cold Opener** (Scene 01, 15–30s): Cognitive paradox, 0% channel logo at start.
2. **Logo Stinger** (5.80s, `assets/brand/zenpham-brand-kit/zenpham_opener_clip_2k60_muxed.mp4`): Invariant brand intro.
3. **Content Scenes** (Scenes 02 to 07): Continuous Motion Geometry, borderless canvas (Rule 29).
4. **CTA Beat & Bridge** (Scene 08, 15–20s): Philosophical synthesis, open community debate, bridge to Ep $k+1$.
5. **Closing Screen with 5x5 Mosaic** (8.00s, `zenpham_closing_cta_2k60_muxed.mp4`): 5x5 Series 1 Mosaic, Next Episode Preview, YouTube End Screen Safe Zones.
- **Subtitle Offset Rule**: Subtitle cues for Scenes 02–08 must carry the `+5.800s` offset and never bleed into Stinger or Closing Mosaic windows.

### 1.4. TTS V0-Sense as Sole Gold TTS Standard (Clause Guard $\le 75$ Chars & Zero-Atempo-Slowdown)
All Vietnamese voiceover generation MUST strictly adhere to the **TTS V0-Sense standard** (`assets/scripts_video/tts_v0_sense_synthesizer.py`). TTS V8 and all intermediate text manipulation, prosody dictionaries (`prosody_dictionary.json`), 24 Wave matrices, compound locks, and phonetic preprocessors remain **COMPLETELY ABANDONED**.
- **Engine**: 100% natural inference on Local VieNeu-TTS v3 Turbo on CUDA (ThinkPad P15 Quadro RTX 5000 16GB).
- **Zero-Atempo-Slowdown Mandate**: Speech MUST run at 100% native 1.0x neural inference speed. Any artificial time-stretching or speed reduction (`atempo < 1.0`, e.g. 0.73x, 0.94x) and mechanical zero-silence padding between clauses are **STRICTLY AND ABSOLUTELY FORBIDDEN**. Voice and Shorts duration are decoupled: speech ends naturally (~36–42s), remaining time to 50.0s is filled by ambient music/SFX and visual conversion CTA, NEVER by dragging or stretching speech.
- **Acoustic Clause Guard**: All synthesis units must be split into fine-grained clauses $\le 75$ characters. Unsegmented sentences $> 80$ chars and ellipsis `...` are **COMPLETELY FORBIDDEN** (replace `...` with `, ` to generate stable 120–220ms pauses).
- **Closed-Loop ASR Verification**: Transcribe every synthesized unit via Faster-Whisper, enforce repetition checks, verify $\ge 75\%$ word coverage, and auto-retry if distorted.
- **Smart Silence Gate**: Frame-by-frame 20ms RMS scan compressing dead gaps $> 0.35$s down to $0.20 – 0.25$s.
- **5-Stage Studio Vocal Mastering Chain**: Highpass 75Hz, De-mud EQ 300Hz (-1.5dB), Presence EQ 3.4kHz (+1.8dB), Air Treble 8.5kHz (+2.0dB), EBU R128 Loudnorm **$-14.5 \pm 0.5$ LUFS**, True Peak **$\le -1.5$ dBTP**, 48kHz Stereo. *(See `.agents/rules/02_acoustic_tts_and_subtitles_gold_standards.md`)*.

### 1.5. Gold SRT Karaoke Rule (Dynamic Phrase Cadence, 60% Screen Width)
All subtitle generation (`.srt`) across Masterclass 16:9 and Shorts 9:16 MUST strictly adhere to the **Gold SRT Karaoke standard** (`assets/scripts_video/gold_srt_karaoke_aligner.py`). Full paragraph or long sentence dumps (10-15s static blocks) covering the screen are **COMPLETELY FORBIDDEN**:
1. **A Few Words Only**: Exactly 3 to 5 words per cue (hard limit 2–6 words).
2. **60% Screen Width Constraint**: Max 34 characters per line (hard limit 35 chars) occupying only the center 60% horizontal viewport, single line only.
3. **Dynamic Karaoke Pacing**: Duration 0.8s to 2.2s per cue (hard max 2.5s), pacing in lockstep with spoken speech.
4. **Zero Broken Compounds**: Compound terms and scientific names (*ngẫu nhiên*, *xác suất*, *Claude Shannon*, *Quỷ Laplace*, *điểm yên ngựa*) must never be split across cue boundaries.
5. **Canonical Script Fidelity**: 100% of subtitle text must derive from canonical author script (0 ASR phonetic typos) with word-level timestamps extracted via Faster-Whisper.

### 1.6. Zero-Code/LaTeX-Leak in Narration Invariant
The Narration Script column (and any text fed to TTS synthesis) MUST NEVER contain raw LaTeX formulas, dollar math delimiters (`$...$`, `$$...$$`), partial derivatives (`\frac{\partial...}`), Greek letters as raw symbols (`\eta`, `\kappa`), markdown code blocks, backticks, or variable subscripts/superscripts. Mathematical formulas and technical notations belong **exclusively in the Visual Action Cues / Telemetry columns**. The spoken script must express all mathematical concepts in 100% natural, elegant spoken Vietnamese. Enforced automatically via `test_zero_latex_or_code_leaks_in_narration`.

### 1.7. Zero-Card-Box-Background & Borderless-Canvas Invariant (Rule 29)
All Manim scripts and visual pipelines across all Content Factory channels and series MUST COMPLETELY ELIMINATE colored card box background containers (no `RoundedRectangle` or `Rectangle` with `fill_color=COLOR_CARD_BG`, `fill_opacity > 0` behind text, tables, or telemetry HUDs). Because Manim lacks an automated flexbox/layout bounding engine, static-sized card boxes inevitably cause element overflow, border collisions, and severe clipping defects. All text, tables, and mathematical formulas must float directly on the pristine Neo-Noir Obsidian canvas (`#080a0f` / `#0c0d12`), structured cleanly via typography hierarchy (Title Cyan `#38bdf8`, Gold `#ffd700`), open grid coordinates, and delicate hairlines/whitespace rather than clunky bounding cards. *(See `.agents/rules/03_visual_geometry_and_manim_standards.md`)*.

### 1.8. Local Object Rotation Invariant (Rule 27)
In all 3D scenes (such as `ThreeDScene`), whole-canvas camera rotation (`begin_ambient_camera_rotation`) is **STRICTLY FORBIDDEN**. The 2D canvas, channel logo, and header HUD must stand completely still (`self.add_fixed_in_frame_mobjects(...)`). All rotation must be executed locally on geometric objects (`Rotate(curves_group, axis=OUT)`).

### 1.9. 5-Shorts Funnel & 4-Beat NLP Open Loop Standard
Every Masterclass episode is accompanied by a suite of 5 dedicated standalone Shorts (9:16, 2K60, exactly 50.00s duration):
- **4-Beat NLP Open Loop Formula**: Paradox Hook (0–10s) $\to$ Cognitive Stake (10–20s) $\to$ Mathematical Proof (20–42s) $\to$ Related Video Conversion CTA (42–50s).
- **Audio Continuity**: Voiceover starts at $0.20 – 0.40$s at 100% native 1.0x neural speed, finishes naturally around $36 – 43$s; zero internal gaps $\ge 0.35$s. Ambient lo-fi pad/SFX carries the bed through to $50.00$s without any artificial speech stretching.
- **Safe Boundaries**: $X \le 3.1$, $Y \ge -6.2$. *(See `.agents/rules/04_shorts_funnel_and_publishing_standards.md`)*.

### 1.10. Manim Gold Standard: Voice-Sync Full-Duration Animation & Zero-Static-Hold Invariant
All Manim animation scenes across Masterclass and Shorts MUST strictly adhere to the **Manim Gold Standard**:
- **Full-Duration Convergence**: Total animation runtime $T_{\text{anim}} = \sum (\text{run\_time} + \text{wait})$ of each scene must closely match the spoken voiceover duration $T_{\text{audio}}$ ($T_{\text{audio}} - T_{\text{anim}} \in [0.5\text{s}, 2.0\text{s}]$). The visual scene stays alive and actively transforms throughout the spoken segment, ending with only a gentle $0.5\text{s} - 1.5\text{s}$ pause before the scene transition.
- **Zero-Static-Hold Invariant**: Generating short 5–10s animations and freezing the frame for 30–60s via video assembler padding (`tpad > 3.0s`) or long dead `self.wait(> 3.0s)` is **STRICTLY AND ABSOLUTELY FORBIDDEN**.
- **Multi-Beat Kinetic Progression**: Each scene must be choreographed into 4 to 6 continuous staged narrative beats in lockstep with the sentences of the spoken script. *(See `.agents/rules/03_visual_geometry_and_manim_standards.md`)*.

### 1.11. AGY Fleet Mandatory Auto-Delegation & Parallel Vibe-Coding Invariant
Whenever a task requires non-trivial code generation, refactoring, architectural planning, test suites, or heavy analysis (>20 lines):
- **Mandatory Delegation (Thin Coordinator Mandate)**: The main orchestrator session MUST NOT generate large code blocks inline in the single conversation window. It MUST act as a Thin Coordinator and delegate generative and analytical tasks to the **AGY Fleet** swarm via MCP tools:
  - Single Prompt / Refactoring: `call_mcp_tool(ServerName="agy-fleet", ToolName="fleet_run", Arguments={"prompt": "...", "model": "gemini-3.8-flash-high"})`
  - Autonomous Decomposed Pipeline: `call_mcp_tool(ServerName="agy-fleet", ToolName="fleet_autonomous_enqueue", Arguments={"prompt": "...", "priority": 5, "metadata": {"preferred_node": "lthn.Ariana"}})`
  - Multi-Perspective Council & Parallel Verification: `call_mcp_tool(ServerName="agy-fleet", ToolName="fleet_parallel", Arguments={"prompt": "..."})`
- **Node Routing Persona Standards**:
  - **Standard Pro Nodes (Default)**: Route high-throughput vibe-coding and unit test generation to Pro nodes (`pro-1` / `innoria.team`, `node-4`..`node-8`, `team-3` / `coderedgen`) using `gemini-3.8-flash-high` or `gemini-3.1-pro-high`.
  - **Ultra Offload Persona (`lthn.Ariana`)**: When the user requests "chuyển tải sang lthn.Ariana", or for complex architectural proofs, deep debugging, and high-complexity tasks ($\ge 2.5$), route directly to **`lthn.Ariana`** (`ultra-2` / `claude-opus-4-6-thinking` or `claude-sonnet-4-6`).
- **Local Application & Verification**: Receive clean structured code output from Fleet nodes, apply changes locally using `replace_file_content` or `write_to_file`, and run local test quality gates to ensure 100% verified correctness.

---

## 2. Hermes Agent Core Principles

1. **Per-conversation prompt caching is sacred**: Never mutate past context, swap toolsets, or rebuild the system prompt mid-conversation.
2. **The core is a narrow waist; capability lives at the edges**: Model tools are sent on every API call. The bar for a new core tool is high.
3. **The Footprint Ladder** (lowest footprint first):
   - Extend existing code $\to$ CLI command + skill $\to$ Service-gated tool (`check_fn`) $\to$ Plugin $\to$ MCP server in catalog $\to$ New core tool (last resort).
4. **Behavior contracts over snapshots**: Invariant tests over change-detector tests.
5. **No speculative infrastructure**: Only ship hooks and extension points with concrete consumers.
6. **Config vs Secrets**: `.env` is for secrets only (API keys, tokens). All behavioral settings belong in `config.yaml`.

---

## 3. Development Environment & Testing

```bash
# Workstation environment: ThinkPad P15 (Quadro RTX 5000 16GB, CUDA)
source .venv/bin/activate              # Core Hermes / Pytest environment (Python 3.11)
source vieneu_tts_test/.venv/bin/activate  # VieNeu-TTS v3 Turbo & Faster-Whisper environment (Python 3.12)
```

Run test quality gates:
```bash
.venv/bin/pytest tests/test_council_integrity_gate.py tests/test_zero_card_box_invariant.py tests/test_gold_srt_quality_gate.py tests/test_shorts_and_closing_quality_gate.py -v
```

---

## 4. Master Rules Directory

For comprehensive operational guidelines, consult the 4 Master Pillars in `.agents/rules/`:
- [**MASTER_RULES.md**](file:///home/zen/hermes-agent/.agents/rules/MASTER_RULES.md) — Unified Index
- [**01_council_integrity_and_macro_structure.md**](file:///home/zen/hermes-agent/.agents/rules/01_council_integrity_and_macro_structure.md) — Council Charter & 5-Section Assembly
- [**02_acoustic_tts_and_subtitles_gold_standards.md**](file:///home/zen/hermes-agent/.agents/rules/02_acoustic_tts_and_subtitles_gold_standards.md) — TTS V0-Sense on CUDA & Gold SRT
- [**03_visual_geometry_and_manim_standards.md**](file:///home/zen/hermes-agent/.agents/rules/03_visual_geometry_and_manim_standards.md) — Rule 29 Borderless Canvas & Manim Rules
- [**04_shorts_funnel_and_publishing_standards.md**](file:///home/zen/hermes-agent/.agents/rules/04_shorts_funnel_and_publishing_standards.md) — 5-Shorts Funnel & Packaging
