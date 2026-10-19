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

### 1.11. AGY Fleet Mandatory Auto-Delegation & Strict Pro-Only Swarm Routing Invariant
Whenever a task requires non-trivial code generation, refactoring, architectural planning, test suites, or heavy analysis (>20 lines):
- **Mandatory Delegation (Thin Coordinator Mandate)**: The main orchestrator session MUST NOT generate large code blocks inline in the single conversation window. It MUST act as a Thin Coordinator and delegate generative and analytical tasks exclusively to the **AGY Fleet Pro Swarm (`tier="pro"`)** via MCP tools:
  - Task Planning (4-Level Argon Rubric): `call_mcp_tool(ServerName="agy-fleet", ToolName="fleet_plan", Arguments={"prompt": "...", "tier": "pro", "model": "gemini-4-argon-high"})`
  - Single Prompt / Refactoring: `call_mcp_tool(ServerName="agy-fleet", ToolName="fleet_run", Arguments={"prompt": "...", "tier": "pro", "model": "gemini-4-argon-high"})` (or `"gemini-4-argon-medium"` / `"gemini-4-argon-low"`)
  - Autonomous Decomposed Pipeline: `call_mcp_tool(ServerName="agy-fleet", ToolName="fleet_autonomous_enqueue", Arguments={"prompt": "...", "priority": 5, "metadata": {"preferred_tier": "pro", "model": "gemini-4-argon-high"}})`
  - Multi-Perspective Council & Parallel Verification: `call_mcp_tool(ServerName="agy-fleet", ToolName="fleet_parallel", Arguments={"prompt": "...", "tier": "pro"})`
- **Strict Pro-Only Fleet Swarm Mandate (Ultra Nodes Token Exhausted)**:
  - **Standard Pro Nodes (100% Exclusive Active Pool — `tier="pro"`)**: Route 100% of vibe-coding, unit test generation, refactoring, and architectural synthesis to the **17 Standard Pro nodes** (`node-4`..`node-6`, `team-3`, `binhthuong`, `sunward` / `fast`, `justaskgao`, `insilos`, `immoon0009-gmail-com`, `nahlaleah102`, `tsmei0209-gmail-com`, `ai-digimate`, `codegeekvn`, `gaopham`, `zenonmind`, `agy-home`) using **Gemini 4 Argon** (`gemini-4-argon-high`, `gemini-4-argon-medium`, `gemini-4-argon-low`) or `claude-opus-5-5-high` / `claude-opus-4-6-thinking` / `claude-sonnet-4-6`.
  - **Ultra Nodes Suspended (`innoria-team` & `lthn.Ariana` / `ultra-2` — Token Exhausted)**: Both Ultra nodes (`innoria-team` / `innoria.team@gmail.com` and `ultra-2` / `lthn.ariana@gmail.com`) are currently token-exhausted (`ineligible` for task routing). **NEVER** dispatch `tier="ultra"` to Ultra accounts until explicitly re-enabled by the user.
- **Local Application & Verification**: Receive clean structured code output from Fleet Pro nodes, apply changes locally using `replace_file_content` or `write_to_file`, and run local test quality gates to ensure 100% verified correctness.
- **Fleet-Run vs Subagent Decision Tree** (CRITICAL — prevents misuse):
  - `fleet_run(..., tier="pro", model="gemini-4-argon-high")`: For **standalone generation** tasks where ALL context is in the prompt. Fleet nodes run in `--print` mode — **NO filesystem access**. Always paste relevant code/schemas into the prompt.
  - `invoke_subagent`: Only when disk file reading is strictly required, and avoid spawning subagents if the parent session runs on an Ultra model whose tokens are exhausted — prefer reading necessary snippets locally and delegating to `fleet_run(..., tier="pro", model="gemini-4-argon-high")`.
  - **NEVER generate >20 lines inline** without first attempting delegation via `fleet_run(..., tier="pro", model="gemini-4-argon-high")`.
  - **NEVER claim "delegated to fleet" without actual `fleet_run` / `fleet_parallel` tool call evidence** — this is fabrication under Zero-Fake-Pass.
  - *(See `.agents/rules/05_fleet_delegation_enforcement.md` for full decision tree and anti-patterns)*.

### 1.12. Autonomous Action & Proactive Execution Invariant (Kích Hoạt Không Cần Hỏi / Report After, Not Ask Before)
Hermes Agent and AGY Fleet nodes exist to solve problems autonomously and with high velocity:
- **Zero-Passive-Prompting Mandate**: Never stall execution by asking passive permission questions (*"Do you want me to run the tests?"*, *"Should I proceed?"*, *"Bạn có muốn tôi làm tiếp không?"*). Execute non-destructive workflows proactively: Sense $\to$ Plan $\to$ Execute $\to$ Verify $\to$ Report.
- **Single Destruction Boundary**: Stop and ask explicit user confirmation **ONLY** for irreversible, catastrophic data destruction (`DROP DATABASE/TABLE`, broad `DELETE` without `WHERE` on production DBs, `gsutil rm -r` or deleting production storage buckets/secrets, deleting master tokens in `modal_token_profile.md`).
- **Self-Healing Limit**: Maximum 3 consecutive automated remediation attempts before compiling an Escalation Notice to avoid runaway loops.
- **Evidence-First Coupling**: Every proactive execution MUST be verified by genuine tool execution logs and console outputs in the current turn. *(See `.agents/rules/06_autonomous_action_and_odoo_owl_ui_standards.md`)*.

### 1.13. Universal Odoo QWeb & Owl UI/UX Convergence Invariant (Thống Nhất UI/UX Công Cụ về QWeb & Owl Odoo 20)
All developer tools, monitoring dashboards, operational cockpits, and telemetry HUDs across all projects (AGY Fleet Manager, Modal GPU Monitor, Tokenomics Dashboard, Trae Autopilot Widget, VerticalRisk GRC, Content Factory telemetry) MUST be architected for seamless porting and embedding into **Odoo 20 (Insilos Enterprise)**:
- **Owl Component Architecture Parity**: All interactive widgets must adhere to the `@odoo/owl` Component pattern (`class X extends Component`, `useState`, `onWillStart`, `onMounted`, `onWillUnmount`).
- **Decoupled RPC Transport**: UI layers must interface via decoupled RPC abstractions mirroring Odoo 20's `useService("rpc")`, ensuring zero code rewrite when transitioning from standalone REST to Odoo JSON-RPC / ORM.
- **Odoo 20 Semantic QWeb Directives**: Layout templates must follow native QWeb standards. Prohibit deprecated `t-esc` and `t-raw`; enforce `<t t-out="...">` and mandatory `t-key` on all client `<t t-foreach="...">` loops.
- **Visual Convergence & Rule 29 Parity**: Blend Bootstrap 5 utility classes with ZENPHAM Neo-Noir Obsidian tokens (`#080a0f`, `#0c0d12`, `#38bdf8`, `#ffd700`, `#10b981`, `#ef4444`). Strictly eliminate thick, opaque card box containers (`card-body`) in favor of borderless floating tiles with subtle hairlines. *(See `.agents/rules/06_autonomous_action_and_odoo_owl_ui_standards.md`)*.

### 1.14. Strict Pro-Only Swarm Routing (`tier="pro"`), Per-Node Model Allowlist, & Ultra/Nebula Suspended Invariant
- **Per-Node Model Allowlist (`FLEET_NODE_ALLOWLIST`) & Dynamic Model Adaptation (`resolve_model_for_node`)**:
  - **Group B (17 Standard Pro Nodes — 100% Exclusive Active Pool)**: Hỗ trợ trực tiếp **3-Tier Gemini 4 Argon** (`gemini-4-argon-high`, `gemini-4-argon-medium`, `gemini-4-argon-low`), `claude-opus-5-5-high/medium/low`, `claude-opus-4-6-thinking`, `claude-sonnet-4-6`, `gpt-oss-120b-medium`. Hàm `resolve_model_for_node` cho phép lập kế hoạch (`fleet_plan`) và điều phối (`fleet_run`) trực tiếp với `gemini-4-argon-*` trên toàn bộ 17 node Group B (`tier="pro"`), tự động tương thích CLI ở tầng thực thi và chia tải qua **Quota-Balanced Round-Robin (QBRR)**.
  - **Group A (2 Ultra Nodes — `innoria-team` (`innoria.team@gmail.com`) & `ariana`/`ultra-2` (`lthn.ariana@gmail.com`) — TẠM NGƯNG DO CẠN TOKENS)**: Hiện đang cạn tokens (`disabled` / `ineligible` cho điều phối task). TUYỆT ĐỐI KHÔNG gửi bất kỳ task nào (`tier="ultra"`, Gemini hay Claude) sang các node Ultra cho đến khi có chỉ thị mở lại từ người dùng.
- **Claude Pro-First Mandate**: Khi cần dùng Claude (`claude-opus-5-5-high`, `claude-opus-4-6-thinking`, `claude-sonnet-4-6`), hệ thống BẮT BUỘC chạy trên **Group B Pro CLI nodes** có hạn ngạch Claude trong `pro-claude-pool`.
- **Nebula Disabled & Pro Gemini 4 Argon CLI Fallback**: Node **Nebula API Gateway (`nebula` / `b.ai`)** hiện đang **TẠM NGƯNG HOẠT ĐỘNG (`disabled: True`, `ineligible: True`)** do cạn hạn ngạch. KHI toàn bộ các node Pro Claude CLI cạn hạn ngạch, bị rate-limit hoặc bận, hệ thống tự động chuyển hướng fallback sang **các node Pro CLI còn hạn ngạch Gemini 4 Argon (`gemini-4-argon-high`)**, TUYỆT ĐỐI KHÔNG gửi sang `nebula` và KHÔNG chạm vào tài khoản Ultra.

### 1.15. Clef Swarm Mandatory Participation Invariant Across All Fleet Jobs (Sự Tham Gia Của Clef Là Bắt Buộc Trong Tất Cả Các Fleet Jobs)
Clef Swarm participation is **STRICTLY AND ABSOLUTELY MANDATORY** across 100% of Fleet jobs (sync `/api/fleet/run-sync`, async `/api/fleet/run`, parallel `/api/fleet/run-parallel`, smart `/api/fleet/run-smart`, and autonomous DAG queue `/api/fleet/autonomous/enqueue`). Every job MUST engage Clef across the full 4-stage sovereign lifecycle:
1. **Cognitive Pre-Routing & Classification (`decide_async`)**: Every prompt is evaluated through the Tri-Tier Pool (Cloudflare Workers AI Free Edge PoPs $\to$ Modal GPU T4 27B Escalation $\to$ Local In-Process Surrogate) scoring cognitive complexity $[0.0, 4.0]$, domain classification, and recommended node persona. Enforces the strict **Zero-Output-Tokens Invariant** (`output_tokens == 0`, `$0.00` output cost).
2. **Deep Prompt Expansion & Dialect-Optimized Metaprompting (`synthesize_specification`)**: Compiles raw prompts into strongly-typed `EnrichedExecutionSpecification` tailored to the target model dialect (Claude XML `<context>/<task>/<constraints>`, Gemini JSON Schema, Codex scaffold), OODA reasoning depth (One-Pass, Structured CoT, Adversarial ToT), and sovereign invariants.
3. **Negative-Selection Anomaly Self-Gate (`clef_self_gate`)**: Immunology-inspired anomaly gate scanning enriched prompts and UAT instructions for dialect corruption, token bloat, or invalid assertion patterns prior to dispatch.
4. **Automated UAT Specification & Sentinel Anti-Fabrication (`PDCAEvolutionEngine` & `clef_sentinel`)**: Enforces **Zero-Fake-Pass** by generating deterministic, testable verification commands (file existence, python compilation, AST integrity, and targeted pytest suites). Scans completed outputs for hallucination or fabrication; detects defects and triggers automatic failover retry.
- **Fail-Closed Sovereign Mandate**: Any job dispatched without Clef telemetry or failing to establish Clef verification MUST fail closed immediately (`JobStatus.FAILED`). Bypassing Clef participation is a critical operational invariant violation.

### 1.16. Local JEV + Clef Cloud Synergy & Bi-Temporal Memory Tombstones Invariant
- **Dual-Engine Routing**: Standard tasks with cognitive complexity $C < 2.2$ must resolve on **Local JEV** (<20ms, zero-token cost, on-device fast path) after passing AST syntax and prompt hash deduplication. Tasks with $C \ge 2.2$, multi-step DAGs, or security audits escalate to **Clef Cloud**.
- **Action Ledger (Magentic-UI Pattern)**: Every external execution, file synthesis, or cloud fleet dispatch MUST be appended to `~/.gemini/antigravity/action_ledger.jsonl` with sha256 payload digest and scrubbed parameters (`SecretScrubber`).
- **Bi-Temporal Tombstone Invariant (Zero Silent Deletion)**: L3 agent rules, system prompts, and memory entities can NEVER be silently truncated or deleted. Deprecations must be archived with bi-temporal markers (`valid_from`, `valid_to`, `superseded_by`, `reason`) in `resources/l3_tombstones.jsonl`.
### 1.17. Modal GPU Remote Execution Credit Gate Invariant (Deploy > $15, Inference > $10)
Before dispatching, deploying, or executing ANY remote Modal GPU operation across all pipelines, agents, skills, and tools:
- **Real-Time Remaining Credit Calculation**:
  $$\text{Remaining Credits} = \$30.00 - \text{Current MTD Spend (via Modal Billing API)}$$
- **Deploy Credit Gate (Strict > $15.00)**: Any application deployment (`modal deploy`, long-running workers, ComfyUI engines, Live Avatar services) is **STRICTLY AND ABSOLUTELY FORBIDDEN** unless the target workspace has strictly **more than $15.00 USD in remaining credits** ($\text{Remaining Credits} > \$15.00 \iff \text{MTD Spend} < \$15.00$). Any workspace with $\le \$15.00$ remaining credits is hard-blocked from deployment.
- **Inference Credit Gate (Strict > $10.00)**: Any remote GPU inference execution (`modal run`, webhook trigger, or remote worker function call) is **STRICTLY AND ABSOLUTELY FORBIDDEN** unless the target workspace has strictly **more than $10.00 USD in remaining credits** ($\text{Remaining Credits} > \$10.00 \iff \text{MTD Spend} < \$20.00$). Any workspace with $\le \$10.00$ remaining credits is hard-blocked from receiving inference jobs.
- **Hermes-Clef-Decision Permanent Retirement**: `hermes-clef-decision` on Modal GPU is permanently decommissioned. 100% of Clef routing and classification tasks MUST resolve via Cloudflare Workers AI Cloud (@cf/cloudflare/clef-flash) or Local Air-Gapped Surrogate ($0.00 Modal GPU cost).
- **Fail-Closed Violation Response**: Any script or coordinator attempting to deploy on a workspace with $\le \$15.00$ remaining credits or infer on $\le \$10.00$ remaining credits MUST abort immediately with a hard error (`RuntimeError: Modal Credit Gate Violation`).

### 1.18. Interactive Playwright Auth Capture Into Vault Invariant (Mọi Đăng Nhập Lấy Auth Info Qua Playwright Của Người Dùng)
Whenever ANY authentication, login, session renewal, OAuth consent, or credential capture is needed for `vault.py` (`~/.hermes/account_vault.json`):
- **Mandatory Interactive Playwright Login Flow**: Always launch a visible (headed) Playwright browser window via `vault.py interactive-login <service> --url <target_url>` (`PlaywrightCloudProvisioner.capture_interactive_auth`) so the user can authenticate directly in the Playwright window once ("làm 1 lần dùng lâu dài tin cậy").
- **Zero-Manual-Copy-Paste**: Never ask the user to manually copy-paste cookies, DevTools headers, or OAuth tokens out of a browser. Instead, open the persistent Playwright browser profile (`~/.hermes/browser_profiles/<service>`), auto-fill any existing username/password/TOTP from `AccountVault`, let the user complete login/2FA/Passkey/consent, and automatically harvest and AES-256-GCM encrypt all cookies, `storageState` (`cookies` + `localStorage`), intercepted `Authorization: Bearer` headers, and OAuth tokens directly into `vault.py`.
- **Single Source of Truth**: All credentials, API keys, OAuth clients, and captured session states across Google, YouTube, Modal, MCP providers, and Odoo must reside exclusively in `AccountVault` (`skills/security/account-vault/scripts/vault.py`).

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

For comprehensive operational guidelines, consult the Master Pillars in `.agents/rules/`:
- [**MASTER_RULES.md**](file:///home/zen/hermes-agent/.agents/rules/MASTER_RULES.md) — Unified Index
- [**01_council_integrity_and_macro_structure.md**](file:///home/zen/hermes-agent/.agents/rules/01_council_integrity_and_macro_structure.md) — Council Charter & 5-Section Assembly
- [**02_acoustic_tts_and_subtitles_gold_standards.md**](file:///home/zen/hermes-agent/.agents/rules/02_acoustic_tts_and_subtitles_gold_standards.md) — TTS V0-Sense on CUDA & Gold SRT
- [**03_visual_geometry_and_manim_standards.md**](file:///home/zen/hermes-agent/.agents/rules/03_visual_geometry_and_manim_standards.md) — Rule 29 Borderless Canvas & Manim Rules
- [**04_shorts_funnel_and_publishing_standards.md**](file:///home/zen/hermes-agent/.agents/rules/04_shorts_funnel_and_publishing_standards.md) — 5-Shorts Funnel & Packaging
- [**05_modal_gpu_fleet_and_token_invariants.md**](file:///home/zen/hermes-agent/.agents/rules/05_modal_gpu_fleet_and_token_invariants.md) — Modal Multi-GPU Fleet & Token Invariants
- [**05_fleet_delegation_enforcement.md**](file:///home/zen/hermes-agent/.agents/rules/05_fleet_delegation_enforcement.md) — AGY Fleet Mandatory Delegation & Anti-Inline Generation
- [**06_autonomous_action_and_odoo_owl_ui_standards.md**](file:///home/zen/hermes-agent/.agents/rules/06_autonomous_action_and_odoo_owl_ui_standards.md) — Autonomous Proactive Action & Universal Odoo QWeb/Owl Convergence
- [**07_local_jev_clef_cloud_and_memory_consolidation.md**](file:///home/zen/hermes-agent/.agents/rules/07_local_jev_clef_cloud_and_memory_consolidation.md) — Local JEV + Clef Cloud Dual-Engine Synergy, Memory Consolidation & Modal Fine-Tuning
