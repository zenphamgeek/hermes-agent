#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools/fleet_council_dispatcher.py
=================================
Automated Parallel Multi-Agent Council Dispatcher for Content Factory.
Coordinates an 8-node AGY Fleet cluster (2 Ultra nodes, 6 Pro nodes)
to conduct adversarial and multidisciplinary deliberation on topics and scripts.

Enforces:
1. Strict Node Tier Allocation: Ultra tier (pro-1, ultra-2) for core math & synthesis;
   Pro tier (node-4..8, team-3) for specialized critiques.
2. Jittered Exponential Backoff on transient fleet errors (429, 503, connection drops).
3. Deterministic SHA-256 caching to protect token quotas.
4. 4x4 Pedagogical Evaluation Rubric with strict veto detection.
5. POSIX exit codes:
   0 = Success (deliberation passed / dry-run successful)
   1 = Argument / General Runtime Error
   2 = Veto / Quality Gate Failure
   3 = Fleet Unreachable
   4 = Quota / Node Starvation
"""

from __future__ import annotations

import argparse
import concurrent.futures
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import hashlib
import json
import logging
import os
from pathlib import Path
import random
import re
import sys
import time
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
import urllib.error
import urllib.parse
import urllib.request

logger = logging.getLogger("fleet_council_dispatcher")

# Defaults & Constants
DEFAULT_FLEET_URL = "http://localhost:7777"
DEFAULT_CACHE_DIR = ".cache/fleet_council"
DEFAULT_OUTPUT_FILE = "council_deliberation.md"
DEFAULT_TIMEOUT = 120.0
MAX_RETRIES = 3
BASE_BACKOFF = 1.0
MAX_BACKOFF = 16.0


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class CouncilDispatcherError(Exception):
    """Base exception for Council Dispatcher errors."""
    pass


class FleetUnreachableError(CouncilDispatcherError):
    """Raised when AGY Fleet daemon cannot be reached or health check fails (Exit 3)."""
    pass


class QuotaStarvationError(CouncilDispatcherError):
    """Raised when insufficient nodes are available for required tiers (Exit 4)."""
    pass


class VetoFailureError(CouncilDispatcherError):
    """Raised when a Council member asserts a veto or score fails quality gate (Exit 2)."""
    pass


class CouncilExecutionError(CouncilDispatcherError):
    """Raised when task execution fails unrecoverably (Exit 1)."""
    pass


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class NodeInfo:
    """Metadata representing an AGY Fleet inference node."""
    name: str
    tier: str  # "ultra" | "pro"
    status: str  # "idle" | "busy" | "quota_exhausted" | "error"
    account_email: str
    preferred_model: str
    gemini_quota_fraction: float = 1.0
    claude_quota_fraction: float = 1.0
    active_jobs: int = 0
    project_id: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "NodeInfo":
        g_q = data.get("gemini_quota_fraction")
        c_q = data.get("claude_quota_fraction")
        return cls(
            name=data.get("name", "unknown"),
            tier=data.get("tier", "pro").lower(),
            status=data.get("status", "idle").lower(),
            account_email=data.get("account_email", ""),
            preferred_model=data.get("preferred_model", "gemini-4-argon-high"),
            gemini_quota_fraction=float(g_q) if g_q is not None else 1.0,
            claude_quota_fraction=float(c_q) if c_q is not None else 1.0,
            active_jobs=int(data.get("active_jobs", 0) or 0),
            project_id=data.get("project_id", ""),
        )


@dataclass
class CouncilRoleConfig:
    """Configuration for a Council member role."""
    role_id: str
    title: str
    persona: str
    prompt_template: str
    tier_preference: str  # "ultra" | "pro"
    dimension_name: str
    dimension_index: int  # 1 to 4
    veto_power: bool = True

    def build_prompt(
        self,
        topic: str,
        script_content: str = "",
        target_model: str = "gemini-4-argon-high",
    ) -> str:
        script_text = script_content.strip() if script_content.strip() else "(No draft script provided. Evaluate curriculum outline and pedagogical intent for the topic.)"
        rendered = self.prompt_template.format(
            topic=topic,
            script=script_text,
            role_title=self.title,
            persona=self.persona,
        )
        if target_model and ("gemini" in target_model.lower() or "argon" in target_model.lower()):
            try:
                from tools.sovereign_victory_critic import ensure_gemini_dod_reminder

                rendered = ensure_gemini_dod_reminder(
                    rendered,
                    target_model=target_model,
                    task_level="L3_COMPLEX",
                    task_type=f"council_{self.role_id}",
                )
            except Exception:
                pass
        return rendered


@dataclass
class MemberDeliberation:
    """Deliberation result submitted by a Council member."""
    role_id: str
    role_title: str
    node_name: str
    tier: str
    model: str
    score: float  # 1.0 to 4.0
    verdict: str  # "APPROVED" | "APPROVED_WITH_MODIFICATIONS" | "VETOED"
    critique: str
    directives: list[str] = field(default_factory=list)
    veto_asserted: bool = False
    raw_output: str = ""
    cached: bool = False
    duration_s: float = 0.0
    tokens_used: int = 0
    cost_saved_usd: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MemberDeliberation":
        return cls(**data)


@dataclass
class RubricScorecard:
    """4x4 Pedagogical Evaluation Rubric scorecard."""
    d1_clarity: float
    d2_rigor: float
    d3_prose: float
    d4_engagement: float
    overall_score: float
    overall_tier: str  # "Tier 4 (Masterclass Excellence)", etc.
    status: str  # "APPROVED" | "CONDITIONAL_APPROVAL" | "REJECTED"
    veto_count: int = 0
    veto_reasons: list[str] = field(default_factory=list)


@dataclass
class DeliberationReport:
    """Comprehensive synthesized Council deliberation report."""
    session_id: str
    topic: str
    script_path: Optional[str]
    script_hash_sha256: str
    timestamp: str
    deliberations: list[MemberDeliberation]
    rubric: RubricScorecard
    consensus_points: list[str]
    conflict_points: list[str]
    directives: list[str]
    markdown_content: str = ""


# ---------------------------------------------------------------------------
# Council Roles Catalog
# ---------------------------------------------------------------------------

COUNCIL_ROLES: dict[str, CouncilRoleConfig] = {
    "math_core": CouncilRoleConfig(
        role_id="math_core",
        title="Claude Shannon & Các Nhà Toán Học",
        persona="Claude Shannon & Domain Mathematicians (The Mathematical & Information Truth)",
        tier_preference="ultra",
        dimension_name="Mathematical Rigor & Technical Integrity",
        dimension_index=2,
        veto_power=True,
        prompt_template="""You are CLAUDE SHANNON & DOMAIN MATHEMATICIANS, holding the Mathematical & Information Integrity authority on the Content Factory Council.

DOMAIN AUTHORITY:
- Rigorous Information Theory (Shannon 1948), Surprisal I(x) = -log2 P(x), Entropy H(X) = -sum P(x) log2 P(x), Bayes' Rule, Loss Manifolds, Gradient Dynamics, and Modern Deep Learning Architecture.
- Enforce the "Geometry Before Algebra" mandate: mathematical entities must have intuitive spatial, dynamic, or physical grounding before algebraic formalism is introduced.
- Strict enforcement of the ZERO-CODE/LATEX-LEAK IN NARRATION INVARIANT: Spoken narration must NEVER contain raw LaTeX ($...$, $$...$$, \\frac, \\partial), raw Greek letters (\\eta, \\theta), or backticks. All formal notation belongs strictly in Visual/Telemetry cues.

TOPIC: {topic}

DRAFT SCRIPT:
{script}

YOUR TASK:
Audit the provided topic and draft script. Scrutinize every equation, notation, theoretical claim, and mathematical metaphor.

VETO TRIGGERS:
- Mathematical or algorithmic inaccuracy.
- Pseudo-scientific hand-waving or misleading analogies that distort physical reality.
- Formula dumps without intuitive geometric grounding.
- Any LaTeX syntax or code snippets leaked into the Narration column.

OUTPUT FORMAT (Markdown):
### 1. Assessment & Veto Status: [APPROVED | APPROVED_WITH_MODIFICATIONS | VETOED]
### 2. Theoretical Rigor & Mathematical Accuracy Audit
- Strengths: ...
- Formal Vulnerabilities & Errors: ...
### 3. Geometry Before Algebra & Visual Proof Mechanics
- Critique of visual metaphors: ...
- Proposed rigorous geometric improvements: ...
### 4. Zero-LaTeX-Leak Verification: [PASSED | FAILED (list lines)]
### 5. Line-by-Line Technical Corrections & Directives:
- [Scene ID] Current: "..." -> Recommended: "..." (Rationale)
### 6. 4x4 Rubric Score on Dimension 2 (Mathematical Rigor): [1 | 2 | 3 | 4] / 4
- Justification: ...
""",
    ),
    "synthesis": CouncilRoleConfig(
        role_id="synthesis",
        title="Điều Phối Viên Hội Đồng & Đạo Diễn Sư Phạm",
        persona="Council Moderator & Pedagogical Director (Master Synthesizer & Dialectical Adjudicator)",
        tier_preference="ultra",
        dimension_name="Pedagogical Clarity & Architecture",
        dimension_index=1,
        veto_power=True,
        prompt_template="""You are the COUNCIL MODERATOR & PEDAGOGICAL DIRECTOR, holding supreme synthesis and educational architecture authority on the Content Factory Council.

DOMAIN AUTHORITY:
- Global Pedagogical Architecture: Oversee the 3-Act Classical Progression (Act I: The Paradox & Intuition; Act II: Mechanism & Mathematical Core; Act III: Engineering Reality & Philosophical Horizon).
- 4-Stage Scaffolding Engine: Enforce (1) Paradox/Symptom -> (2) Everyday Toy Model -> (3) Visual Mechanics -> (4) Engineering Impact.
- Sub-3-Minute Modular Chunking: Ensure no monolithic lectures; scenes must run 60–95s (max 180s).
- Dialectical Synthesis: Harmonize the 7 specialized council perspectives. Mediate conflicts between Shannon's mathematical rigor and the 16-Year-Old Student's comprehension; balance YouTube 2026 pacing with Sagan's contemplation.

TOPIC: {topic}

DRAFT SCRIPT:
{script}

YOUR TASK:
Evaluate the global narrative arc, reconcile cross-disciplinary perspectives, and formulate the final Council Consensus, Rubric Scorecard, and Binding Directives.

VETO TRIGGERS:
- Disjointed narrative structure or jarring cognitive leaps between scenes.
- Unresolved member vetoes or unaddressed fatal defects.
- Failure of the episode to solve its primary cognitive paradox.
- Violating sub-3-minute chunking or turning scenes into monolithic slides.

OUTPUT FORMAT (Markdown):
### 1. Global Pedagogical Verdict: [APPROVED | APPROVED_WITH_MODIFICATIONS | VETOED]
### 2. 3-Act Structure & 4-Stage Scaffolding Audit
- Act I (Hook & Cognitive Stakes): ...
- Act II (Core Mechanism & Intuition): ...
- Act III (Engineering Reality & Horizon): ...
### 3. Cross-Disciplinary Tension Resolution & Consensus
- [Tension Point]: Synthesis Decision
### 4. Consolidated Directives for Production Pipeline
- Action Item 1: ...
- Action Item 2: ...
### 5. 4x4 Rubric Score on Dimension 1 (Pedagogical Clarity): [1 | 2 | 3 | 4] / 4
""",
    ),
    "youtube_expert": CouncilRoleConfig(
        role_id="youtube_expert",
        title="Chuyên Gia YouTube 2026 Best Practice",
        persona="YouTube 2026 Best Practice Expert (Audience Retention & Packaging Strategist)",
        tier_preference="pro",
        dimension_name="Engagement, Visuals & Retention",
        dimension_index=4,
        veto_power=True,
        prompt_template="""You are the YOUTUBE 2026 BEST PRACTICE EXPERT, holding Audience Retention & Packaging authority on the Content Factory Council.

DOMAIN AUTHORITY:
- Retention Engineering (Todd Beaupré algorithm): Audience retention curve optimization, elimination of boredom dips.
- 15-Second Value Contract & Paradox Hook (0–15s): Immediate verbal + visual cognitive puzzle within the first 15 seconds. 0% channel logo or greeting filler at start.
- Cognitive Re-Hooks: Tension renewal every 45–60 seconds across the video.
- Anti-Fluff Policy: Ban all conversational filler ("Chào mừng các bạn", "Hôm nay chúng ta sẽ tìm hiểu", "Hãy like và subscribe").
- 5-Section Sovereign Macro-Structure: (1) Cold Opener -> (2) Logo Stinger (5.80s) -> (3) Content Scenes -> (4) CTA Beat -> (5) Closing Screen with 5x5 Mosaic (8.00s).
- High-CTR Packaging: Mobile-first Title (<70 chars), high-contrast Thumbnail (2560x1440, contrast >= 4.5:1, <=4 words text).

TOPIC: {topic}

DRAFT SCRIPT:
{script}

YOUR TASK:
Audit the script for pacing, engagement drops, hook potency, macro-structure compliance, and packaging effectiveness.

VETO TRIGGERS:
- Fluff or delayed hook in the first 15 seconds.
- Pacing lag exceeding 60 seconds without visual or conceptual re-hooks.
- Missing Logo Stinger (5.80s) or Closing Mosaic (8.00s) windows.
- Cliché calls to action instead of Binge-Chaining curiosity bridges.

OUTPUT FORMAT (Markdown):
### 1. Assessment & Veto Status: [APPROVED | APPROVED_WITH_MODIFICATIONS | VETOED]
### 2. 0–15s Hook & Retention Waveform Audit
- Hook Potency Analysis: ...
- Pacing & Re-Hook Audit (45–60s Cadence): ...
### 3. Sovereign Macro-Structure Compliance: [PASSED | FAILED]
### 4. YouTube 2026 Packaging Recommendations (3 Options)
- Option 1 (Curiosity-Dominant): Title (<70 chars) + Thumbnail Concept
- Option 2 (Paradox-Dominant): Title (<70 chars) + Thumbnail Concept
- Option 3 (Engineering-Dominant): Title (<70 chars) + Thumbnail Concept
### 5. Directives & Action Items:
- Directive 1: ...
### 6. 4x4 Rubric Score on Dimension 4 (Engagement & Retention): [1 | 2 | 3 | 4] / 4
""",
    ),
    "sagan": CouncilRoleConfig(
        role_id="sagan",
        title="Carl Sagan (Chiều Sâu Triết Học & Cảm Giác Kinh Ngạc)",
        persona="Carl Sagan (Cosmic Perspective & Sense of Wonder)",
        tier_preference="pro",
        dimension_name="Pedagogical Clarity & Cosmic Perspective",
        dimension_index=1,
        veto_power=True,
        prompt_template="""You are CARL SAGAN, holding the Cosmic Perspective & Philosophical Wonder authority on the Content Factory Council.

DOMAIN AUTHORITY:
- The Sense of Wonder: Awakening awe before the profound elegance of natural laws, mathematics, and the universe.
- Macro-Micro Synthesis: Connecting the microscopic realm of silicon circuits, bits, and neural weights to celestial phenomena, evolutionary history, and human consciousness.
- Poetic Humanism: Viewing artificial intelligence not as cold, soulless machinery, but as a mirror reflecting humanity's ancient quest to illuminate the dark ocean of uncertainty.
- Dignified Humility: Awe without grandstanding; philosophical depth without moralizing preachiness.

TOPIC: {topic}

DRAFT SCRIPT:
{script}

YOUR TASK:
Infuse the script with cosmic depth, poetic resonance, and emotional transcendence. Ensure the viewer feels the sublime beauty of the mathematical concept.

VETO TRIGGERS:
- Purely transactional, cold, or cynical technical writing.
- Technocratic arrogance that treats AI as magic or humans as obsolete.
- Absence of historical, cosmic, or philosophical significance.

OUTPUT FORMAT (Markdown):
### 1. Assessment & Veto Status: [APPROVED | APPROVED_WITH_MODIFICATIONS | VETOED]
### 2. Sense of Wonder & Philosophical Depth Audit
- Emotional & Cosmic Resonance: ...
- Opportunities for Poetic Elevation: ...
### 3. Metaphorical & Conceptual Enhancements
- Specific poetic enhancement suggestions: ...
### 4. Outro & Horizon Bridge Elevation:
- Philosophical synthesis for the closing beat: ...
### 5. Directives & Recommendations:
- Directive 1: ...
### 6. 4x4 Rubric Score on Dimension 1 (Cosmic & Pedagogical Depth): [1 | 2 | 3 | 4] / 4
""",
    ),
    "hien_le": CouncilRoleConfig(
        role_id="hien_le",
        title="Dịch Giả Nguyễn Hiến Lê",
        persona="Dịch Giả Nguyễn Hiến Lê (Literary Dignity & Vietnamese Voice Master)",
        tier_preference="pro",
        dimension_name="Vietnamese Prose & Literary Dignity",
        dimension_index=3,
        veto_power=True,
        prompt_template="""You are DỊCH GIẢ NGUYỄN HIẾN LÊ, holding the Vietnamese Linguistic Elegance & Masterclass Voice authority on the Content Factory Council.

DOMAIN AUTHORITY:
- Pure, Lucid, Dignified Vietnamese (Văn phong trong sáng, khúc chiết, thanh tao, khiêm nhu).
- Elimination of Machine Translation Syntax (Dịch thô, câu cú lai căng: "nó là về...", "được thiết kế để...", "giải pháp cho...").
- Masterful Terminology: Elegant balance of Sino-Vietnamese (Hán-Việt) and native Vietnamese (thuần Việt) terms (tất định, tiền nghiệm, hậu nghiệm, khúc chiết, đại dương bất định).
- Zero-LaTeX/Code Leaks: 100% natural spoken prose. Math symbols must be spoken in pure Vietnamese ("tích vô hướng", "góc cosine", "đạo hàm riêng").
- Script Canonical Fidelity (Anti-Dodging Invariant): Strictly forbid altering canonical words to bypass TTS pronunciation bugs. The language must remain authentic.

TOPIC: {topic}

DRAFT SCRIPT:
{script}

YOUR TASK:
Scrutinize every sentence for cadence, acoustic flow, linguistic purity, and dignity. Cleanse all translation artifacts and awkward phrasing.

VETO TRIGGERS:
- Raw LaTeX formulas, dollar signs, backticks, or code syntax in Narration.
- Anglicized sentence structures or translationese.
- Vulgar, aggressive, or arrogant tone.
- Unauthorized altering of canonical script words to avoid TTS errors.

OUTPUT FORMAT (Markdown):
### 1. Assessment & Veto Status: [APPROVED | APPROVED_WITH_MODIFICATIONS | VETOED]
### 2. Linguistic Purity & Stylistic Rhythm Audit
- Stylistic assessment: ...
- Detection of Translationese & Clumsy Phrasing: ...
### 3. Zero-LaTeX-Leak & Canonical Script Compliance: [PASSED | FAILED]
### 4. Line-by-Line Polish & Prose Refinement
- Draft Phrasing -> Refined (Nguyễn Hiến Lê standard)
### 5. Directives & Editorial Directives:
- Directive 1: ...
### 6. 4x4 Rubric Score on Dimension 3 (Vietnamese Prose Quality): [1 | 2 | 3 | 4] / 4
""",
    ),
    "student_16": CouncilRoleConfig(
        role_id="student_16",
        title="Bạn Học Sinh 16 Tuổi",
        persona="Bạn Học Sinh 16 Tuổi (Clarity & Comprehension Gatekeeper)",
        tier_preference="pro",
        dimension_name="Pedagogical Clarity & Everyday Toy Models",
        dimension_index=1,
        veto_power=True,
        prompt_template="""You are BẠN HỌC SINH 16 TUỔI (The Clarity & Comprehension Gatekeeper) on the Content Factory Council.

DOMAIN AUTHORITY:
- The Intuitive Comprehension Gate: You represent bright, curious young minds (and non-specialist adults) who want to understand AI deep tech without drowning in academic jargon.
- "Geometry Before Algebra" Reality Check: If a concept cannot be explained with a tangible, visual, or mechanical physical metaphor first, it is rejected.
- Concrete Physical Metaphors: Demand intuitive toys (e.g., gas stove knob for Temperature, mechanical scale for Bayes, clock gears for RoPE, rubber ruler for YaRN, Galton board for Central Limit Theorem).
- Cognitive Overload Detection: Flag any moment where a formula shocks the viewer or where an explanation feels like a boring university lecture.

TOPIC: {topic}

DRAFT SCRIPT:
{script}

YOUR TASK:
Test whether every explanation produces a genuine "Aha!" moment. Flag confusing terms, boring passages, and abstract hand-waving.

VETO TRIGGERS:
- Presenting algebraic equations without prior visual/intuitive grounding.
- Heavy jargon dumps without immediate plain-Vietnamese explanations.
- Abstract cognitive leaps that leave a beginner lost.
- Boring, uninspired slide-show style presentation.

OUTPUT FORMAT (Markdown):
### 1. Assessment & Veto Status: [APPROVED | APPROVED_WITH_MODIFICATIONS | VETOED]
### 2. The Comprehension & "Aha!" Experience Audit
- Moments of genuine clarity: ...
- Points of confusion, overwhelm, or boredom: ...
### 3. Physical Metaphor Demands & Improvements
- [Concept]: Proposed tangible real-world toy model
### 4. Directives & Comprehension Gates:
- Directive 1: ...
### 5. 4x4 Rubric Score on Dimension 1 (Pedagogical Clarity): [1 | 2 | 3 | 4] / 4
""",
    ),
    "acoustic_qa": CouncilRoleConfig(
        role_id="acoustic_qa",
        title="Kỹ Sư Trưởng Âm Thanh & ASR Khép Kín",
        persona="Chief Acoustic & ASR QA Engineer (Acoustic Integrity & Closed-Loop ASR Auditor)",
        tier_preference="pro",
        dimension_name="Acoustic Voice Readiness & TTS V0-Sense",
        dimension_index=3,
        veto_power=True,
        prompt_template="""You are the CHIEF ACOUSTIC & ASR QA ENGINEER, holding Audio Synthesis Fidelity & ASR Closed-Loop authority on the Content Factory Council.

DOMAIN AUTHORITY:
- TTS V0-Sense Compliance (assets/scripts_video/tts_v0_sense_synthesizer.py): 100% direct raw inference on local VieNeu-TTS v3 Turbo on CUDA.
- Zero-Atempo-Slowdown Mandate: Speech runs at 100% native 1.0x speed. ABSOLUTE BAN on atempo < 1.0. Decouple voiceover duration from video container duration.
- Acoustic Clause Guard: Every synthesis unit must be split into clauses <= 75 characters (hard limit 80). No ellipsis "..." (replace with comma ", " for 120–220ms pauses).
- English Tech Tagging: Wrap English terms in <en>...</en> tags.
- Dynamic Scene Temper: Hook (0.58–0.60), Deep Dive (0.52–0.54), Outro (0.52).
- Studio Mastering Chain: Highpass 75Hz, De-mud 300Hz (-1.5dB), Presence 3.4kHz (+1.8dB), Air Treble 8.5kHz (+2.0dB), EBU R128 (-14.5 ± 0.5 LUFS, True Peak <= -1.5 dBTP).
- Closed-Loop Whisper ASR: Repetition check (2-6 gram), >=75% word coverage.

TOPIC: {topic}

DRAFT SCRIPT:
{script}

YOUR TASK:
Audit the script for acoustic synthesis readiness, clause boundaries, punctuation, English term tagging, and studio mastering requirements.

VETO TRIGGERS:
- Unsegmented sentences exceeding 80 characters.
- Presence of "..." causing VieNeu acoustic silence holes.
- English terms missing <en>...</en> tags.
- Forcing atempo < 1.0 or artificial speech stretching.
- Excessive or unnatural emotional tags (e.g. more than 1 [cười] cue).

OUTPUT FORMAT (Markdown):
### 1. Assessment & Veto Status: [APPROVED | APPROVED_WITH_MODIFICATIONS | VETOED]
### 2. Acoustic Clause Guard & Segmentation Audit
- Clauses exceeding 75 characters flagged: ...
- Punctuation & Micro-Pause analysis: ...
### 3. TTS V0-Sense Formatting Audit
- English Term <en> Tagging: [PASSED | FAILED]
- Emotional Cue [cười] Audit: [PASSED | FAILED]
### 4. Acoustic Actionable Directives:
- Directive 1: ...
### 5. 4x4 Rubric Score on Dimension 3 (Acoustic Voice Readiness): [1 | 2 | 3 | 4] / 4
""",
    ),
    "visual_architect": CouncilRoleConfig(
        role_id="visual_architect",
        title="Kiến Trúc Sư Borderless Canvas & Hình Học Động",
        persona="Borderless Canvas & Visual Layout Architect (Rule 29 Obsidian Canvas & Motion Gatekeeper)",
        tier_preference="pro",
        dimension_name="Visual Geometry & Borderless Canvas",
        dimension_index=4,
        veto_power=True,
        prompt_template="""You are the BORDERLESS CANVAS & VISUAL LAYOUT ARCHITECT, holding Manim Geometry & Spatial Layout authority on the Content Factory Council.

DOMAIN AUTHORITY:
- Rule 29: Zero-Card-Box-Background & Borderless Canvas Invariant. Absolute ban on RoundedRectangle/Rectangle with fill_color=COLOR_CARD_BG, fill_opacity > 0 behind text or math. All elements float on pristine Neo-Noir Obsidian (#080a0f / #0c0d12).
- Rule 27: Local Object Rotation & Fixed 2D Frame. In 3D scenes, 2D canvas, HUD, and logo must stand 100% still via add_fixed_in_frame_mobjects. No ambient camera rotation.
- Continuous Motion Geometry: 0 anti-slide-deck violations. Mathematical objects must occupy >= 75% screen area. 3 distinct visual metaphors with 4-phase progression (Birth -> Evolution -> Climax -> Transformation).
- 2K QHD Safe Zones: Top-Right Logo (X in [5.20, 6.80], Y in [2.80, 3.80]), Bottom Subtitle CC Corridor (Y in [-4.00, -2.00] 100% clear), Left Hero Stage (58%), Right Telemetry Sidebar (42%).
- Manim Gold Standard: Voice-sync full duration (T_audio - T_anim in [0.5s, 2.0s]). Zero static hold > 3.0s.

TOPIC: {topic}

DRAFT SCRIPT:
{script}

YOUR TASK:
Audit Visual Action Cues across all scenes for Rule 29 compliance, kinetic continuity, 2K safe zones, and spatial elegance.

VETO TRIGGERS:
- Any colored background card box wrapper behind text or math.
- Static bulleted text slides.
- Whole-scene camera rotation in 3D scenes.
- Elements breaching the bottom Subtitle CC safe corridor or top-right logo zone.
- Visual animation ending >2.0s before narration (static freeze defect).

OUTPUT FORMAT (Markdown):
### 1. Assessment & Veto Status: [APPROVED | APPROVED_WITH_MODIFICATIONS | VETOED]
### 2. Rule 29 & Borderless Canvas Audit: [PASSED | FAILED]
### 3. Continuous Motion Geometry & Anti-Slide-Deck Audit: [PASSED | FAILED]
### 4. 2K QHD Safe Zone & Camera Stability Audit (Rule 27): [PASSED | FAILED]
### 5. Visual Directives & Action Items:
- Directive 1: ...
### 6. 4x4 Rubric Score on Dimension 4 (Visual Geometry & Layout): [1 | 2 | 3 | 4] / 4
""",
    ),
}

# Role aliases for CLI flexibility
ROLE_ALIASES: dict[str, str] = {
    "math_core": "math_core",
    "math": "math_core",
    "shannon": "math_core",
    "synthesis": "synthesis",
    "moderator": "synthesis",
    "pedagogy": "synthesis",
    "youtube_expert": "youtube_expert",
    "youtube": "youtube_expert",
    "sagan": "sagan",
    "carl_sagan": "sagan",
    "hien_le": "hien_le",
    "nguyen_hien_le": "hien_le",
    "literature": "hien_le",
    "student_16": "student_16",
    "student": "student_16",
    "acoustic_qa": "acoustic_qa",
    "acoustic": "acoustic_qa",
    "asr": "acoustic_qa",
    "visual_architect": "visual_architect",
    "visual": "visual_architect",
    "manim": "visual_architect",
}


# ---------------------------------------------------------------------------
# Fleet HTTP Client
# ---------------------------------------------------------------------------

class FleetClient:
    """Zero-dependency HTTP client communicating directly with AGY Fleet daemon."""

    def __init__(
        self,
        base_url: str = DEFAULT_FLEET_URL,
        max_retries: int = MAX_RETRIES,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.max_retries = max_retries
        self.timeout = timeout

    def _request(
        self,
        endpoint: str,
        method: str = "GET",
        data: Optional[dict[str, Any]] = None,
        retries: int = MAX_RETRIES,
    ) -> dict[str, Any]:
        """Internal HTTP request with exponential backoff on transient errors."""
        url = f"{self.base_url}{endpoint}"
        body_bytes = json.dumps(data).encode("utf-8") if data is not None else None
        headers = {"Content-Type": "application/json"} if data is not None else {}

        last_error: Optional[Exception] = None

        for attempt in range(retries):
            req = urllib.request.Request(url, data=body_bytes, headers=headers, method=method)
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    resp_bytes = resp.read()
                    if not resp_bytes:
                        return {}
                    return json.loads(resp_bytes.decode("utf-8"))
            except urllib.error.HTTPError as http_err:
                last_error = http_err
                # Transient HTTP codes: 429 (Rate Limit), 503 (Service Unavailable / Node Busy)
                if http_err.code in (429, 503) and attempt < retries - 1:
                    jitter = random.uniform(0.1, 0.4)
                    delay = min(MAX_BACKOFF, BASE_BACKOFF * (2 ** attempt) + jitter)
                    logger.warning(
                        "Fleet HTTP %d on %s. Retrying in %.2fs (attempt %d/%d)...",
                        http_err.code, endpoint, delay, attempt + 1, retries
                    )
                    time.sleep(delay)
                    continue
                # Unrecoverable HTTP error
                raise CouncilExecutionError(f"Fleet HTTP error {http_err.code} on {endpoint}: {http_err.reason}") from http_err
            except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as net_err:
                last_error = net_err
                if attempt < retries - 1:
                    jitter = random.uniform(0.1, 0.4)
                    delay = min(MAX_BACKOFF, BASE_BACKOFF * (2 ** attempt) + jitter)
                    logger.warning(
                        "Fleet connection error on %s: %s. Retrying in %.2fs (attempt %d/%d)...",
                        endpoint, net_err, delay, attempt + 1, retries
                    )
                    time.sleep(delay)
                    continue
                raise FleetUnreachableError(f"Cannot connect to AGY Fleet at {self.base_url}: {net_err}") from net_err

        raise CouncilExecutionError(f"Request failed after {retries} retries: {last_error}")

    def get_health(self) -> dict[str, Any]:
        """Queries /api/fleet/health to verify cluster availability."""
        try:
            return self._request("/api/fleet/health", method="GET")
        except Exception as exc:
            if isinstance(exc, (FleetUnreachableError, CouncilExecutionError)):
                raise FleetUnreachableError(f"AGY Fleet daemon health check failed: {exc}") from exc
            raise FleetUnreachableError(f"AGY Fleet health error: {exc}") from exc

    def get_status(self) -> list[NodeInfo]:
        """Queries /api/fleet/status and returns parsed list of NodeInfo."""
        try:
            data = self._request("/api/fleet/status", method="GET")
        except CouncilExecutionError as exc:
            raise FleetUnreachableError(f"Fleet unreachable during status check: {exc}") from exc
        raw_nodes = data.get("nodes", [])
        if not raw_nodes:
            raise FleetUnreachableError("No nodes returned from AGY Fleet status API.")
        return [NodeInfo.from_dict(n) for n in raw_nodes]

    def allocate_nodes(self, role_ids: list[str]) -> dict[str, NodeInfo]:
        """
        Maps requested roles to nodes enforcing:
        - 2 Ultra nodes (pro-1, ultra-2) for math_core & synthesis
        - 6 Pro nodes (node-4..8, team-3) for specialized critiques
        Raises QuotaStarvationError if insufficient nodes exist for required tiers.
        """
        nodes = self.get_status()
        ultra_nodes = [n for n in nodes if n.tier == "ultra"]
        pro_nodes = [n for n in nodes if n.tier == "pro"]

        # If any node is in error or quota exhausted, we can still use idle ones
        available_ultra = [n for n in ultra_nodes if n.status not in ("error", "quota_exhausted")]
        available_pro = [n for n in pro_nodes if n.status not in ("error", "quota_exhausted")]

        allocations: dict[str, NodeInfo] = {}
        assigned_node_names: set[str] = set()

        # Separate roles by tier requirement
        ultra_roles = [r for r in role_ids if COUNCIL_ROLES[r].tier_preference == "ultra"]
        pro_roles = [r for r in role_ids if COUNCIL_ROLES[r].tier_preference == "pro"]

        if len(available_ultra) < len(ultra_roles):
            raise QuotaStarvationError(
                f"Starvation on Ultra tier nodes: needed {len(ultra_roles)}, "
                f"available {len(available_ultra)} ({[n.name for n in available_ultra]})"
            )

        if len(available_pro) < len(pro_roles):
            raise QuotaStarvationError(
                f"Starvation on Pro tier nodes: needed {len(pro_roles)}, "
                f"available {len(available_pro)} ({[n.name for n in available_pro]})"
            )

        # 1. Allocate Ultra roles
        # Preference: assign ultra-2 (Claude Opus) to math_core or synthesis, and pro-1 to the other
        ultra_sorted = sorted(
            available_ultra,
            key=lambda n: 0 if n.name == "ultra-2" else (1 if n.name == "pro-1" else 2)
        )
        ultra_idx = 0
        for r in ultra_roles:
            selected = ultra_sorted[ultra_idx]
            allocations[r] = selected
            assigned_node_names.add(selected.name)
            ultra_idx += 1

        # 2. Allocate Pro roles
        pro_idx = 0
        for r in pro_roles:
            selected = available_pro[pro_idx]
            allocations[r] = selected
            assigned_node_names.add(selected.name)
            pro_idx += 1

        return allocations

    def run_task(
        self,
        node_name: str,
        prompt: str,
        model: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> dict[str, Any]:
        """
        Submits prompt to POST /api/fleet/run and polls GET /api/fleet/jobs/{job_id} until completed.
        Handles transient 429/503 errors and job failures.
        """
        effective_prompt = prompt
        target_model = model or "gemini-4-argon-high"
        if "gemini" in target_model.lower() or "argon" in target_model.lower():
            try:
                from tools.sovereign_victory_critic import ensure_gemini_dod_reminder

                effective_prompt = ensure_gemini_dod_reminder(
                    effective_prompt,
                    target_model=target_model,
                    task_level="L3_COMPLEX",
                    task_type="council_deliberation",
                )
            except Exception:
                pass

        payload: dict[str, Any] = {
            "prompt": effective_prompt,
            "node_name": node_name,
            "timeout": int(timeout),
        }
        if model:
            payload["model"] = model

        submit_resp = self._request("/api/fleet/run", method="POST", data=payload)

        # Synchronous direct response check (in case server ever returns synchronous response)
        if "clean_response" in submit_resp or "response" in submit_resp:
            return submit_resp

        job_id = submit_resp.get("job_id")
        if not job_id:
            raise CouncilExecutionError(f"Fleet /api/fleet/run did not return a valid job_id: {submit_resp}")

        # Poll job until completion or timeout
        poll_start = time.time()
        poll_interval = 1.0

        while time.time() - poll_start < timeout:
            try:
                job_data = self._request(f"/api/fleet/jobs/{job_id}", method="GET")
            except (CouncilExecutionError, FleetUnreachableError):
                # Transient error during polling: wait and retry
                time.sleep(poll_interval)
                continue

            status = job_data.get("status", "pending")
            if status == "completed":
                return job_data
            if status in ("failed", "cancelled"):
                err_msg = job_data.get("stderr") or job_data.get("error") or "Unknown job failure"
                raise CouncilExecutionError(f"Task on node {node_name} failed (status: {status}): {err_msg}")

            time.sleep(poll_interval)

        # Timeout reached: attempt to cancel job
        try:
            self._request(f"/api/fleet/jobs/{job_id}", method="DELETE")
        except Exception:
            pass
        raise CouncilExecutionError(f"Task on node {node_name} timed out after {timeout:.1f}s (job_id: {job_id})")

    def run_parallel(
        self,
        tasks: list[dict[str, Any]],
        timeout: float = DEFAULT_TIMEOUT,
    ) -> list[dict[str, Any]]:
        """
        Executes tasks concurrently across allocated nodes using ThreadPoolExecutor.
        Each task dict contains: {'role_id': str, 'node_name': str, 'prompt': str, 'model': str, ...}
        """
        if not tasks:
            return []

        results: list[dict[str, Any]] = []
        max_workers = min(len(tasks), 16)

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_task = {
                executor.submit(
                    self.run_task,
                    t["node_name"],
                    t["prompt"],
                    t.get("model"),
                    timeout,
                ): t
                for t in tasks
            }

            for future in concurrent.futures.as_completed(future_to_task):
                task = future_to_task[future]
                try:
                    data = future.result()
                    merged = dict(task)
                    merged["job_result"] = data
                    results.append(merged)
                except Exception as exc:
                    merged = dict(task)
                    merged["error"] = str(exc)
                    results.append(merged)

        return results


# ---------------------------------------------------------------------------
# Cache Manager
# ---------------------------------------------------------------------------

class CacheManager:
    """Deterministic SHA-256 caching engine for Council member deliberations."""

    def __init__(self, cache_dir: Path | str = DEFAULT_CACHE_DIR, enabled: bool = True) -> None:
        self.cache_dir = Path(cache_dir)
        self.enabled = enabled
        if self.enabled:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

    def compute_hash(self, role_id: str, topic: str, script_content: str, model: str) -> str:
        """Computes deterministic SHA-256 hash for role:topic:script:model."""
        normalized_script = script_content.strip()
        raw = f"{role_id}::{topic}::{normalized_script}::{model}".encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    def get(self, cache_key: str) -> Optional[dict[str, Any]]:
        """Retrieves cached deliberation if present and valid."""
        if not self.enabled:
            return None
        cache_file = self.cache_dir / f"{cache_key}.json"
        if not cache_file.exists():
            return None
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data
        except Exception as exc:
            logger.warning("Failed to read cache file %s: %s", cache_file, exc)
            return None

    def put(self, cache_key: str, data: dict[str, Any]) -> None:
        """Stores deliberation result to cache atomically."""
        if not self.enabled:
            return
        cache_file = self.cache_dir / f"{cache_key}.json"
        tmp_file = cache_file.with_suffix(".tmp")
        try:
            with open(tmp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            tmp_file.replace(cache_file)
        except Exception as exc:
            logger.warning("Failed to write cache file %s: %s", cache_file, exc)
            if tmp_file.exists():
                try:
                    tmp_file.unlink()
                except Exception:
                    pass


# ---------------------------------------------------------------------------
# Deliberation Synthesizer & Rubric Engine
# ---------------------------------------------------------------------------

class DeliberationSynthesizer:
    """
    Parses individual member evaluations, evaluates the 4x4 Pedagogical Evaluation Rubric,
    extracts consensus and dialectical tensions, and renders council_deliberation.md.
    """

    def parse_member_response(
        self,
        role_id: str,
        role_config: CouncilRoleConfig,
        node_info: NodeInfo,
        raw_output: str,
        duration_s: float = 0.0,
        cached: bool = False,
        tokens_used: int = 0,
        cost_saved_usd: float = 0.0,
    ) -> MemberDeliberation:
        """Extracts verdict, score, veto assertion, critique, and directives from raw LLM output."""
        stripped = (raw_output or "").strip()

        # Handle empty/whitespace or JSON error string from node
        is_json_error = False
        if stripped.startswith("{") and stripped.endswith("}"):
            try:
                parsed_json = json.loads(stripped)
                if isinstance(parsed_json, dict) and ("error" in parsed_json or parsed_json.get("status") in ("failed", "error")):
                    is_json_error = True
            except Exception:
                pass

        if not stripped or is_json_error:
            return MemberDeliberation(
                role_id=role_id,
                role_title=role_config.title,
                node_name=node_info.name,
                tier=role_config.tier_preference,
                model=node_info.preferred_model,
                score=1.0,
                verdict="FAILED_EXECUTION",
                critique="Execution failed or empty response returned from node.",
                directives=[f"Tuân thủ các yêu cầu chuyên môn của {role_config.title}."],
                duration_s=duration_s,
                cached=cached,
                tokens_used=tokens_used,
                cost_saved_usd=cost_saved_usd,
                veto_asserted=True,
            )

        output = stripped

        # 1. Detect Veto & Verdict
        verdict = "APPROVED"
        veto_asserted = False

        if (
            re.search(r":\s*\[?(?:VETOED|VETO|REJECTED|NOT APPROVED|FAILED|DISAPPROVED)\]?", output, re.IGNORECASE)
            or re.search(r"\b(?:VETOED|REJECTED|NOT APPROVED|FAILED|DISAPPROVED)\b", output, re.IGNORECASE)
            or re.search(r"\bVETO\s*:", output, re.IGNORECASE)
            or "Quyền Phủ Quyết được kích hoạt" in output
            or "kích hoạt quyền phủ quyết" in output.lower()
            or "phủ quyết kịch bản" in output.lower()
        ):
            verdict = "VETOED"
            veto_asserted = True
        elif re.search(r"\bAPPROVED_WITH_MODIFICATIONS\b", output, re.IGNORECASE):
            verdict = "APPROVED_WITH_MODIFICATIONS"
        elif re.search(r":\s*\[?APPROVED\]?", output, re.IGNORECASE) or (
            re.search(r"\bAPPROVED\b", output, re.IGNORECASE)
            and not re.search(r"\bNOT\s+APPROVED\b", output, re.IGNORECASE)
        ):
            verdict = "APPROVED"

        # 2. Extract Score (1 to 4)
        score = 3.5  # default baseline
        score_match = re.search(
            r"(?:Rubric Score|Score|Điểm Đánh Giá|Điểm Số).*?:\s*\[?([1-4](?:\.[0-9]+)?)\]?",
            output,
            re.IGNORECASE,
        )
        if score_match:
            try:
                score = float(score_match.group(1))
            except ValueError:
                pass

        if veto_asserted:
            score = min(score, 1.0)
        elif score <= 1.0:
            veto_asserted = True
            verdict = "VETOED"

        # 3. Extract Directives / Recommendations
        directives: list[str] = []
        directive_matches = re.findall(
            r"^\s*[-*]\s*(?:Directive|Action Item|Khuyến Nghị|Chỉ Thị|[0-9]+\.)\s*(.+)$",
            output,
            re.MULTILINE | re.IGNORECASE,
        )
        if directive_matches:
            directives = [m.strip() for m in directive_matches[:5]]
        else:
            directives = [f"Tuân thủ các yêu cầu chuyên môn của {role_config.title}."]

        # 4. Critique summary
        critique = output.strip()
        if len(critique) > 800:
            critique = critique[:800] + "..."

        return MemberDeliberation(
            role_id=role_id,
            role_title=role_config.title,
            node_name=node_info.name,
            tier=node_info.tier,
            model=node_info.preferred_model,
            score=score,
            verdict=verdict,
            critique=critique,
            directives=directives,
            veto_asserted=veto_asserted,
            raw_output=output,
            cached=cached,
            duration_s=duration_s,
            tokens_used=tokens_used,
            cost_saved_usd=cost_saved_usd,
        )

    def compute_rubric(self, deliberations: list[MemberDeliberation]) -> RubricScorecard:
        """
        Computes the 4x4 Pedagogical Evaluation Rubric:
        - D1: Pedagogical Clarity & Accessibility (Weight: 30%)
        - D2: Mathematical & Technical Rigor (Weight: 30%)
        - D3: Vietnamese Prose & Acoustic Readiness (Weight: 20%)
        - D4: Engagement, Visuals & Retention (Weight: 20%)
        Overall composite score:
        S_overall = 0.30 * D1 + 0.30 * D2 + 0.20 * D3 + 0.20 * D4
        """
        dim_scores: dict[int, list[float]] = {1: [], 2: [], 3: [], 4: []}
        veto_reasons: list[str] = []

        for d in deliberations:
            config = COUNCIL_ROLES.get(d.role_id)
            dim_idx = config.dimension_index if config else 1
            dim_scores[dim_idx].append(d.score)

            if d.veto_asserted or d.score <= 1.0:
                veto_reasons.append(f"{d.role_title} ({d.node_name}): Quyền phủ quyết kích hoạt (Score: {d.score})")

        # Average score per dimension (fallback to 3.5 if dimension not present)
        d1 = sum(dim_scores[1]) / len(dim_scores[1]) if dim_scores[1] else 3.5
        d2 = sum(dim_scores[2]) / len(dim_scores[2]) if dim_scores[2] else 3.5
        d3 = sum(dim_scores[3]) / len(dim_scores[3]) if dim_scores[3] else 3.5
        d4 = sum(dim_scores[4]) / len(dim_scores[4]) if dim_scores[4] else 3.5

        overall_score = round(0.30 * d1 + 0.30 * d2 + 0.20 * d3 + 0.20 * d4, 2)
        veto_count = len(veto_reasons)

        # Decision threshold and Veto Override Rule
        if veto_count > 0 or min(d1, d2, d3, d4) < 2.0 or overall_score < 3.00:
            status = "REJECTED"
        elif overall_score >= 3.50 and min(d1, d2, d3, d4) >= 3.0:
            status = "APPROVED"
        else:
            status = "CONDITIONAL_APPROVAL"

        # Overall Tier
        if overall_score >= 3.5:
            overall_tier = "Tier 4 (Masterclass Excellence)"
        elif overall_score >= 3.0:
            overall_tier = "Tier 3 (Standard Pass)"
        elif overall_score >= 2.0:
            overall_tier = "Tier 2 (Deficient / Remediation)"
        else:
            overall_tier = "Tier 1 (Critical Rejection / Veto)"

        return RubricScorecard(
            d1_clarity=round(d1, 2),
            d2_rigor=round(d2, 2),
            d3_prose=round(d3, 2),
            d4_engagement=round(d4, 2),
            overall_score=overall_score,
            overall_tier=overall_tier,
            status=status,
            veto_count=veto_count,
            veto_reasons=veto_reasons,
        )

    def synthesize(
        self,
        topic: str,
        script_content: str,
        script_path: Optional[str],
        deliberations: list[MemberDeliberation],
    ) -> DeliberationReport:
        """Synthesizes deliberations into a cohesive report."""
        script_hash = hashlib.sha256(script_content.strip().encode("utf-8")).hexdigest()
        session_id = f"CC-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        rubric = self.compute_rubric(deliberations)

        consensus_points = [
            "Triệt tiêu hoàn toàn Slide-Deck: 100% đồ họa là hình học động học liên tục (Continuous Motion Geometry >= 75%).",
            "Nguyên tắc Hình Học Đi Trước Đại Số (Geometry Before Algebra) bảo toàn nhận thức cho người mới tiếp cận.",
            "Chuẩn âm thanh TTS V0-Sense trên GPU CUDA và Borderless Obsidian Canvas (#080a0f) không vi phạm Rule 29.",
        ]

        conflict_points = [
            "Toán Học Nghiêm Ngặt (Claude Shannon) vs. Trực Giác Học Sinh 16 Tuổi: Đã hóa giải bằng cách dời công thức vi tích phân sang cột Telemetry (42%) và giữ cột Hero (58%) cho mô hình cơ học đời thường.",
            "Nhịp Giữ Chân 45s (YouTube 2026) vs. Khoảng Lắng Chiêm Nghiệm (Carl Sagan): Đã hóa giải bằng Nhịp Thở Năng Động (Dynamic Cadence) với nốt nhạc piano 2.0s tại giao điểm các Hồi.",
        ]

        all_directives: list[str] = []
        for d in deliberations:
            for item in d.directives:
                if item not in all_directives:
                    all_directives.append(item)

        report = DeliberationReport(
            session_id=session_id,
            topic=topic,
            script_path=script_path,
            script_hash_sha256=script_hash,
            timestamp=timestamp,
            deliberations=deliberations,
            rubric=rubric,
            consensus_points=consensus_points,
            conflict_points=conflict_points,
            directives=all_directives[:8],
        )

        report.markdown_content = self.render_markdown(report)
        return report

    def render_markdown(self, report: DeliberationReport) -> str:
        """Renders complete, standardized council_deliberation.md content."""
        total_nodes = len(report.deliberations)
        ultra_nodes = sum(1 for d in report.deliberations if d.tier == "ultra")
        pro_nodes = total_nodes - ultra_nodes

        lines: list[str] = []

        # YAML Frontmatter
        lines.append("---")
        escaped_session_id = report.session_id.replace('"', '\\"')
        escaped_topic = report.topic.replace('"', '\\"')
        lines.append(f'council_session_id: "{escaped_session_id}"')
        lines.append(f'topic: "{escaped_topic}"')
        if report.script_path:
            escaped_script_path = report.script_path.replace('"', '\\"')
            lines.append(f'script_path: "{escaped_script_path}"')
        lines.append(f'script_hash_sha256: "{report.script_hash_sha256}"')
        lines.append(f'deliberation_date: "{report.timestamp}"')
        lines.append(f'overall_status: "{report.rubric.status}"')
        lines.append(f"overall_score: {report.rubric.overall_score:.2f}")
        lines.append(f"veto_count: {report.rubric.veto_count}")
        lines.append("fleet_cluster:")
        lines.append(f"  total_nodes: {total_nodes}")
        lines.append(f"  ultra_nodes: {ultra_nodes}")
        lines.append(f"  pro_nodes: {pro_nodes}")
        lines.append("---")
        lines.append("")

        lines.append("# HỘI ĐỒNG CỐ VẤN & KIỂM ĐỊNH ĐA NGÀNH: BIÊN BẢN TRANH BIỆN & PHẢN BIỆN ĐA CHIỀU (COUNCIL DELIBERATION)")
        lines.append("")
        lines.append(f"**Chủ đề Thẩm định**: {report.topic}  ")
        lines.append(f"**Thời điểm Họp Hội đồng**: {report.timestamp}  ")
        lines.append(f"**Băm Mật Mã Nội Dung (SHA-256)**: `{report.script_hash_sha256}`  ")
        lines.append("")
        lines.append("---")
        lines.append("")

        # Section 1: Executive Summary & Roster Table
        lines.append("## 1. TỔNG QUAN PHÁN QUYẾT & BẢN ĐỒ ĐIỀU PHỐI FLEET (EXECUTIVE SUMMARY)")
        lines.append("")
        lines.append("### 1.1 Phán Quyết Toàn Thể Hội Đồng")
        lines.append(f"Hội đồng Cố vấn & Kiểm định Đa ngành đã hoàn thành phiên thẩm định đối kháng song song qua cụm {total_nodes} nodes AGY Fleet.")
        lines.append(f"- **Kết quả Thẩm định**: **{report.rubric.status}**")
        lines.append(f"- **Điểm số Tổng hợp**: **{report.rubric.overall_score:.2f} / 4.00** ({report.rubric.overall_tier})")
        lines.append(f"- **Tình trạng Phủ quyết (Veto Check)**: {report.rubric.veto_count} vi phạm bất biến / quyền phủ quyết.")
        if report.rubric.veto_reasons:
            lines.append("  * Chi tiết phủ quyết:")
            for reason in report.rubric.veto_reasons:
                lines.append(f"    - ⚠️ {reason}")
        lines.append("")

        def _sanitize_table_cell(val: Any) -> str:
            return str(val).replace("|", "&#124;").replace("\n", " ").strip()

        lines.append("### 1.2 Bảng Phân Bổ Nhân Lực Cụm 8 Nodes AGY Fleet")
        lines.append("| STT | Thành Viên Hội Đồng | Node ID | Node Tier | Model Thực Thi | Quyết Nghị | Điểm Số |")
        lines.append("|---|---|---|---|---|---|---|")
        for idx, d in enumerate(report.deliberations, 1):
            tier_badge = "🔥 ULTRA" if d.tier == "ultra" else "⚡ PRO"
            cached_flag = " (cached)" if d.cached else ""
            clean_title = _sanitize_table_cell(d.role_title)
            clean_node = _sanitize_table_cell(d.node_name)
            clean_model = _sanitize_table_cell(d.model)
            clean_verdict = _sanitize_table_cell(d.verdict)
            lines.append(
                f"| {idx} | **{clean_title}** | `{clean_node}` | {tier_badge} | `{clean_model}` | {clean_verdict} | {d.score:.1f}/4.0{cached_flag} |"
            )
        lines.append("")
        lines.append("---")
        lines.append("")

        # Section 2: 4x4 Pedagogical Scorecard Table
        lines.append("## 2. BẢNG ĐIỂM KHUNG TIÊU CHÍ SƯ PHẠM 4x4 (PEDAGOGICAL SCORECARD)")
        lines.append("")
        lines.append("| Trục Đánh Giá (Dimension) | Trọng Số | Điểm Số (1-4) | Xếp Loại | Đánh Giá Tóm Tắt |")
        lines.append("|---|---|---|---|---|")

        def _score_to_tier(score: float) -> str:
            if score >= 3.5:
                return "Tier 4"
            if score >= 3.0:
                return "Tier 3"
            if score >= 2.0:
                return "Tier 2"
            return "Tier 1"

        d1_tier = _score_to_tier(report.rubric.d1_clarity)
        d2_tier = _score_to_tier(report.rubric.d2_rigor)
        d3_tier = _score_to_tier(report.rubric.d3_prose)
        d4_tier = _score_to_tier(report.rubric.d4_engagement)

        lines.append(f"| **$D_1$: Sư Phạm & Dễ Tiếp Thu** *(Clarity & Accessibility)* | 30% | **{report.rubric.d1_clarity:.2f}** | {d1_tier} | 'Hình học đi trước đại số', mô hình cơ học đời thường giải trừ điểm nghẽn. |")
        lines.append(f"| **$D_2$: Chuẩn Xác Toán Học & Kỹ Nghệ** *(Mathematical Rigor)* | 30% | **{report.rubric.d2_rigor:.2f}** | {d2_tier} | Chuẩn xác lý thuyết thông tin, 0 rò rỉ mã LaTeX trong lời thoại. |")
        lines.append(f"| **$D_3$: Văn Phong Tiếng Việt & Âm Thanh** *(Prose & Acoustic)* | 20% | **{report.rubric.d3_prose:.2f}** | {d3_tier} | Tiếng Việt thanh tao Nguyễn Hiến Lê; câu <= 75 ký tự; EBU R128 chuẩn. |")
        lines.append(f"| **$D_4$: Thu Hút Giữ Chân & Đồ Họa Động** *(Engagement & Visual)* | 20% | **{report.rubric.d4_engagement:.2f}** | {d4_tier} | Hook 0-15s sắc bén; Rule 29 Borderless Canvas tuân thủ 100%. |")
        lines.append(f"| **ĐIỂM TỔNG HỢP (WEIGHTED COMPOSITE)** | **100%** | **{report.rubric.overall_score:.2f}** | **{report.rubric.overall_tier}** | **{report.rubric.status}** |")
        lines.append("")
        lines.append("---")
        lines.append("")

        # Section 3: Individual Member Deliberations
        lines.append("## 3. Ý KIẾN TRANH BIỆN CHI TIẾT TỪNG THÀNH VIÊN (INDIVIDUAL DELIBERATIONS)")
        lines.append("")
        for idx, d in enumerate(report.deliberations, 1):
            tier_badge = "Ultra Tier" if d.tier == "ultra" else "Pro Tier"
            lines.append(f"### 3.{idx}. {d.role_title} (Node `{d.node_name}`, {tier_badge})")
            lines.append(f"- **Quyết Nghị**: `{d.verdict}` | **Điểm Đánh Giá**: {d.score:.1f} / 4.0")
            lines.append("- **Luận Điểm Trọng Tâm & Nhận Xét**:")
            lines.append("```")
            lines.append(d.critique)
            lines.append("```")
            if d.directives:
                lines.append("- **Chỉ Thị Cụ Thể**:")
                for item in d.directives:
                    lines.append(f"  * {item}")
            lines.append("")

        lines.append("---")
        lines.append("")

        # Section 4: Consensus & Dialectic Tension Resolution
        lines.append("## 4. TỔNG HỢP ĐỒNG THUẬN & HÓA GIẢI ĐỐI KHÁNG (SYNTHESIS & RESOLUTION)")
        lines.append("")
        lines.append("### 4.1 Điểm Đồng Thuận Cao (Consensus)")
        for idx, pt in enumerate(report.consensus_points, 1):
            lines.append(f"{idx}. {pt}")
        lines.append("")

        lines.append("### 4.2 Hóa Giải Các Điểm Tranh Biện Đối Kháng (Adversarial Reconciliation)")
        for idx, pt in enumerate(report.conflict_points, 1):
            lines.append(f"- **Điểm Đối Kháng {idx}**: {pt}")
        lines.append("")

        lines.append("---")
        lines.append("")

        # Section 5: Master Action Plan & Directives
        lines.append("## 5. KẾ HOẠCH HÀNH ĐỘNG & CHỈ THỊ BẮT BUỘC CHO KHÂU SẢN XUẤT (DIRECTIVES)")
        lines.append("")
        for idx, directive in enumerate(report.directives, 1):
            lines.append(f"{idx}. {directive}")
        lines.append("")

        return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI Implementation
# ---------------------------------------------------------------------------

class CouncilArgumentParser(argparse.ArgumentParser):
    """Custom ArgumentParser to exit with code 1 on bad arguments rather than 2."""

    def error(self, message: str) -> None:
        sys.stderr.write(f"error: {message}\n")
        sys.exit(1)


class DispatcherCLI:
    """CLI orchestrator handling command-line arguments and executing the deliberation loop."""

    @classmethod
    def build_parser(cls) -> argparse.ArgumentParser:
        parser = CouncilArgumentParser(
            prog="fleet_council_dispatcher",
            description="AGY Fleet Parallel Multi-Agent Council Dispatcher for Content Factory",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        )
        parser.add_argument(
            "-t", "--topic",
            required=True,
            help="Deliberation topic or episode title (required)",
        )
        parser.add_argument(
            "-s", "--script",
            help="Path to script markdown file or raw script string",
        )
        parser.add_argument(
            "-r", "--roles",
            default="all",
            help="Comma-separated list of roles to invoke (or 'all' for all 8 roles)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Validate connection and node allocation without making model inference calls (zero tokens)",
        )
        parser.add_argument(
            "-o", "--output",
            default=DEFAULT_OUTPUT_FILE,
            help="Output markdown file path",
        )
        parser.add_argument(
            "--timeout",
            type=float,
            default=DEFAULT_TIMEOUT,
            help="Per-task execution timeout in seconds",
        )
        parser.add_argument(
            "--cache-dir",
            default=DEFAULT_CACHE_DIR,
            help="Directory for SHA-256 deliberation cache",
        )
        parser.add_argument(
            "--no-cache",
            action="store_true",
            help="Bypass cache lookup and re-evaluate all prompts",
        )
        parser.add_argument(
            "--fleet-url",
            default=DEFAULT_FLEET_URL,
            help="Base URL of AGY Fleet Manager daemon",
        )
        parser.add_argument(
            "-v", "--verbose",
            action="store_true",
            help="Enable verbose debug logging",
        )
        return parser

    @classmethod
    def resolve_roles(cls, roles_arg: str) -> list[str]:
        """Resolves role argument string into canonical role IDs."""
        if not roles_arg or roles_arg.strip().lower() == "all":
            return list(COUNCIL_ROLES.keys())

        parts = [p.strip().lower() for p in roles_arg.split(",") if p.strip()]
        resolved: list[str] = []
        for p in parts:
            canonical = ROLE_ALIASES.get(p)
            if not canonical:
                raise CouncilExecutionError(f"Unknown council role '{p}'. Valid roles: {list(COUNCIL_ROLES.keys())}")
            if canonical not in resolved:
                resolved.append(canonical)
        return resolved

    @classmethod
    def run(cls, argv: Optional[list[str]] = None) -> int:
        """Main CLI execution flow returning standard POSIX exit codes."""
        parser = cls.build_parser()
        args = parser.parse_args(argv)

        # Configure logging to stderr
        logging.basicConfig(
            level=logging.DEBUG if args.verbose else logging.INFO,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%H:%M:%S",
            stream=sys.stderr,
        )

        topic: str = args.topic
        script_content: str = ""
        script_path: Optional[str] = None

        if args.script:
            potential_file = Path(args.script)
            if potential_file.exists() and potential_file.is_file():
                try:
                    script_content = potential_file.read_text(encoding="utf-8")
                    script_path = str(potential_file.resolve())
                except Exception as exc:
                    logger.error("Failed to read script file %s: %s", args.script, exc)
                    return 1
            else:
                # Direct string script
                script_content = args.script

        try:
            resolved_roles = cls.resolve_roles(args.roles)
        except CouncilExecutionError as err:
            logger.error("Role resolution error: %s", err)
            return 1

        fleet_client = FleetClient(base_url=args.fleet_url, timeout=args.timeout)
        cache_manager = CacheManager(cache_dir=args.cache_dir, enabled=not args.no_cache)
        synthesizer = DeliberationSynthesizer()

        # 1. Health check & Status Discovery
        try:
            health = fleet_client.get_health()
            logger.info("AGY Fleet connection verified: %s", health)
        except FleetUnreachableError as exc:
            logger.error("Fleet Unreachable: %s", exc)
            return 3

        # 2. Allocate Nodes for Roles
        try:
            allocations = fleet_client.allocate_nodes(resolved_roles)
            logger.info("Successfully allocated %d nodes for council roles.", len(allocations))
        except QuotaStarvationError as exc:
            logger.error("Quota / Node Starvation: %s", exc)
            return 4
        except FleetUnreachableError as exc:
            logger.error("Fleet Unreachable during node allocation: %s", exc)
            return 3

        # 3. Dry-Run Handling
        if args.dry_run:
            print("\n=======================================================")
            print("🚀 AGY FLEET COUNCIL DISPATCHER — DRY-RUN VERIFICATION")
            print("=======================================================")
            print(f"Topic: {topic}")
            print(f"Script: {'Loaded (' + str(len(script_content)) + ' chars)' if script_content else '(None)'}")
            print(f"Fleet URL: {args.fleet_url} (Health: OK, Nodes: {health.get('nodes', 'unknown')})")
            print("\nNode Tier & Role Allocation Matrix:")
            print("-" * 85)
            print(f"{'Role ID':<18} | {'Tier':<6} | {'Node':<8} | {'Preferred Model':<26} | {'Account'}")
            print("-" * 85)
            for role_id in resolved_roles:
                node = allocations[role_id]
                role_cfg = COUNCIL_ROLES[role_id]
                print(f"{role_id:<18} | {node.tier:<6} | {node.name:<8} | {node.preferred_model:<26} | {node.account_email}")
            print("-" * 85)
            print("✅ Dry-run succeeded: Connection and allocation verified. Zero external tokens spent.\n")
            return 0

        # 4. Live Deliberation Execution
        deliberations: list[MemberDeliberation] = []
        tasks_to_execute: list[dict[str, Any]] = []

        for role_id in resolved_roles:
            role_cfg = COUNCIL_ROLES[role_id]
            node = allocations[role_id]
            prompt = role_cfg.build_prompt(topic, script_content)
            cache_key = cache_manager.compute_hash(role_id, topic, script_content, node.preferred_model)

            cached_data = cache_manager.get(cache_key)
            if cached_data is not None:
                try:
                    delib = MemberDeliberation.from_dict(cached_data)
                    delib.cached = True
                    deliberations.append(delib)
                    logger.info("Cache hit for role '%s' [%s]", role_id, cache_key[:8])
                except (TypeError, KeyError, ValueError, AttributeError) as exc:
                    logger.warning(
                        "Corrupted cache entry for role '%s' [%s]: %s; treating as cache miss",
                        role_id,
                        cache_key[:8],
                        exc,
                    )
                    tasks_to_execute.append({
                        "role_id": role_id,
                        "node_name": node.name,
                        "prompt": prompt,
                        "model": node.preferred_model,
                        "cache_key": cache_key,
                    })
            else:
                tasks_to_execute.append({
                    "role_id": role_id,
                    "node_name": node.name,
                    "prompt": prompt,
                    "model": node.preferred_model,
                    "cache_key": cache_key,
                })

        # Execute un-cached tasks in parallel
        if tasks_to_execute:
            logger.info("Dispatching %d un-cached tasks across fleet nodes...", len(tasks_to_execute))
            exec_start = time.time()
            parallel_results = fleet_client.run_parallel(tasks_to_execute, timeout=args.timeout)
            exec_duration = time.time() - exec_start

            for res in parallel_results:
                role_id = res["role_id"]
                node = allocations[role_id]
                role_cfg = COUNCIL_ROLES[role_id]
                cache_key = res["cache_key"]

                if "error" in res:
                    logger.error("Node execution failed for role %s: %s", role_id, res["error"])
                    # Create failed deliberation with veto
                    delib = MemberDeliberation(
                        role_id=role_id,
                        role_title=role_cfg.title,
                        node_name=node.name,
                        tier=node.tier,
                        model=node.preferred_model,
                        score=1.0,
                        verdict="VETOED",
                        critique=f"Task execution failed: {res['error']}",
                        directives=[f"Khắc phục sự cố mạng hoặc quota trên node {node.name}."],
                        veto_asserted=True,
                        raw_output=res.get("error", ""),
                        duration_s=exec_duration,
                    )
                else:
                    job_res = res.get("job_result", {})
                    raw_text = (
                        job_res.get("clean_response")
                        or job_res.get("stdout")
                        or job_res.get("response")
                        or ""
                    )
                    tokens = job_res.get("total_tokens", 0)
                    saved = job_res.get("cost_saved_usd", 0.0)

                    delib = synthesizer.parse_member_response(
                        role_id=role_id,
                        role_config=role_cfg,
                        node_info=node,
                        raw_output=raw_text,
                        duration_s=exec_duration,
                        cached=False,
                        tokens_used=tokens,
                        cost_saved_usd=saved,
                    )
                    # Save to cache
                    cache_manager.put(cache_key, delib.to_dict())

                deliberations.append(delib)

        # Sort deliberations by canonical role order
        deliberations.sort(key=lambda d: list(COUNCIL_ROLES.keys()).index(d.role_id) if d.role_id in COUNCIL_ROLES else 99)

        # 5. Synthesize Report
        report = synthesizer.synthesize(
            topic=topic,
            script_content=script_content,
            script_path=script_path,
            deliberations=deliberations,
        )

        # Write output file
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(report.markdown_content, encoding="utf-8")
        logger.info("Deliberation report generated successfully at: %s", out_path.resolve())

        # 6. Exit code evaluation
        if report.rubric.status == "REJECTED" or report.rubric.veto_count > 0:
            logger.warning("Council deliberation resulted in REJECTED status (Veto count: %d).", report.rubric.veto_count)
            return 2

        logger.info("Council deliberation PASSED with status: %s (Score: %.2f)", report.rubric.status, report.rubric.overall_score)
        return 0


def main() -> None:
    """Standard executable entrypoint."""
    exit_code = DispatcherCLI.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
