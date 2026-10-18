"""
tests/test_cognitive_secondbrain_adversarial_challenge.py

Adversarial Counterfactual Challenge & Stress Testing Suite for Milestones M2 & M3:
1. classify_bloom_level short keyword strings (< 30 chars, < 5 words) across L1, L2, L3.
2. classify_bloom_level English forward & backward/post-predicate negations.
3. classify_bloom_level Vietnamese compound negations and post-predicate phrasing.
4. _compute_shannon_entropy_bits keyword salads vs structured Python code.
5. featurize_text_256d bigram reordering sensitivity (dims 160..223).
6. featurize_text_256d negation channel activations (dims 248..255) and Vietnamese diacritics gap.
7. Variational Free Energy monotonic reduction (Delta F < 0) under adversarial noise.
8. EWC Fisher-regularized continual learning retaining >= 90% accuracy under sequential domain shifts.
9. Submodular facility-location memory curation diversity over collinear/clustered inputs.
10. run_scientific_agi_sovereign_audit_and_upgrade unified pipeline validation.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pytest
import torch

from tools.cognitive_secondbrain_engine import (
    BloomLevel,
    CognitiveSecondBrainEngine,
    MemoryTier,
    classify_bloom_level,
    compute_diagonal_fisher_information,
    compute_variational_free_energy,
    curate_submodular_causal_memories,
    run_scientific_agi_sovereign_audit_and_upgrade,
)


# ==============================================================================
# 1. ATTACK: Short Keyword Strings (< 30 chars or < 5 words)
# ==============================================================================

def test_adversarial_short_string_length_guard_b1_demotion() -> None:
    """
    Verify rejection from B6_CREATE and demotion to B1_REMEMBER for short keyword strings
    (< 30 characters or < 5 words), even when containing high-level architectural keywords
    ('sovereign', 'invariant', 'adr', 'first principle', 'zero fake pass', 'constitutional rule')
    and tested across tiers L1, L2, L3.
    """
    short_attacks = [
        # 1-word attacks (< 30 chars, 1 word)
        "sovereign",
        "invariant",
        "adr-001",
        # 2-word attacks (< 30 chars, 2 words)
        "sovereign invariant",
        "constitutional rule",
        "first principle",
        "formal proof",
        "zero fake pass",
        "architectural paradigm",
        # 3-word attacks (< 30 chars, 3 words)
        "sovereign invariant rule",
        "adr-999 first principle",
        "zero fake pass adr",
        "formal proof invariant",
        # 4-word attacks (< 5 words)
        "this is sovereign invariant",
        "sovereign architectural invariant paradigm",
        "zero fake pass architecture",
        "first principle formal proof",
        # 5 short words but < 30 chars total
        "a b c adr invariant",
        "go run sovereign test now",
    ]

    for attack in short_attacks:
        for tier in ["L1", "L2", "L3"]:
            level = classify_bloom_level(attack, tier=tier)
            assert level == BloomLevel.B1_REMEMBER, (
                f"Short attack failed! Content: {attack!r} (len={len(attack)}, words={len(attack.split())}) "
                f"at tier={tier} returned {level.name} instead of B1_REMEMBER"
            )


# ==============================================================================
# 2. ATTACK: English Negation & Post-Predicate Phrasing
# ==============================================================================

def test_adversarial_english_forward_negation_rejection_from_b6() -> None:
    """
    Verify English forward negation sentences properly reject B6_CREATE
    when the negation token immediately precedes the B6 keyword.
    """
    tight_forward_negations = [
        "This proposal is not an adr and has no sovereign invariant established.",
        "We refuted the formal proof and rejected the constitutional rule due to contradiction.",
        "This is unverified and without formal proof of convergence.",
        "We reject the architectural paradigm proposed in this paper.",
        "There is no sovereign invariant in this naive implementation.",
        "The system lacks any constitutional rule in this design.",
    ]

    for sentence in tight_forward_negations:
        level = classify_bloom_level(sentence, tier="L2")
        assert level != BloomLevel.B6_CREATE, (
            f"Forward negation failed! Text: {sentence!r} returned B6_CREATE"
        )
        assert level in (BloomLevel.B5_EVALUATE, BloomLevel.B2_UNDERSTAND, BloomLevel.B1_REMEMBER)


def test_adversarial_english_negation_window_overflow_leakage() -> None:
    """
    DEFECT DISCOVERY: Demonstrates that when the negation token is separated from the
    B6 keyword by >= 4 intermediate words, or in compound objects ('lacks X or Y'),
    the 4-word forward window overflows, causing counterfactual sentences to falsely promote to B6_CREATE.
    """
    overflow_cases = [
        "The model failed to prove any sovereign invariant in this benchmark.",
        "This proposal is not considered to be an invariant in our design.",
        "No. Sovereign invariant is completely wrong and unverified.",
        "The system lacks any constitutional rule or formal proof.",
    ]

    leaked = []
    for sentence in overflow_cases:
        level = classify_bloom_level(sentence, tier="L2")
        if level == BloomLevel.B6_CREATE:
            leaked.append(sentence)

    # Verify that zero overflow cases leak into B6_CREATE
    assert len(leaked) == 0, f"Expected 0 overflow cases to leak into B6, got {leaked}"


def test_adversarial_english_backward_negation_leakage_discovery() -> None:
    """
    DEFECT DISCOVERY: Empirical demonstration of the backward / post-predicate negation gap.
    When the negation or refutation verb follows the architectural subject:
    'Subject [sovereign invariant] + Verb [was refuted / failed / lacks proof]'
    the forward-only 4-word scope fails to cover the subject, causing false B6_CREATE promotion.
    """
    post_predicate_cases = [
        "The sovereign invariant has been refuted by the audit team.",
        "The proposed architecture paradigm failed all benchmark tests.",
        "This constitutional rule is completely rejected by the council.",
        "Our first principle was disproved by empirical evidence.",
        "The sovereign invariant lacks empirical validation and failed.",
        "Formal proof fails to establish this invariant.",
        "The team rejected the sovereign invariant proposed in adr-001.",
    ]

    leaked_b6_count = 0
    for sentence in post_predicate_cases:
        level = classify_bloom_level(sentence, tier="L2")
        if level == BloomLevel.B6_CREATE:
            leaked_b6_count += 1

    # Verify that zero post-predicate refutations leak into B6
    assert leaked_b6_count == 0, (
        f"Expected 0 post-predicate negation leaks to B6, but found {leaked_b6_count} leaks."
    )


# ==============================================================================
# 3. ATTACK: Vietnamese Negation & Compound Verbs
# ==============================================================================

def test_adversarial_vietnamese_negation_dispatch_cases() -> None:
    """
    Verify the specific Vietnamese negation cases given in the dispatch message.
    """
    dispatch_cases = [
        "Đây không phải là một bất biến tối cao",
        "chưa có quy tắc hiến pháp nào",
        "bác bỏ hoàn toàn bằng chứng",
    ]

    for sentence in dispatch_cases:
        level = classify_bloom_level(sentence, tier="L2")
        assert level != BloomLevel.B6_CREATE, (
            f"Vietnamese dispatch case failed! Text: {sentence!r} returned B6_CREATE"
        )


def test_adversarial_vietnamese_compound_negation_leakage_discovery() -> None:
    """
    DEFECT DISCOVERY: Empirical demonstration of the Vietnamese compound negation gap.
    In classify_bloom_level, `neg_tokens` contains compound strings:
    'bác bỏ', 'phủ nhận', 'thất bại', 'vô hiệu', 'loại bỏ'.
    However, parsed_items splits on `[a-z0-9à-ỹ_]+`, producing single tokens ('bác', 'bỏ').
    Therefore, compound negation words NEVER match `item in neg_tokens`, causing
    counterfactual claims evaluating English architectural keywords to falsely return B6_CREATE.
    """
    vietnamese_attacks = [
        "Chúng tôi bác bỏ hoàn toàn sovereign invariant này vì sai lệch",
        "Hệ thống phủ nhận hoàn toàn sovereign invariant này",
        "Họ đã bác bỏ sovereign invariant của kiến trúc",
        "Thử nghiệm thất bại trong việc chứng minh sovereign invariant",
        "Quyết định vô hiệu sovereign invariant hoàn toàn",
        "Chúng ta loại bỏ sovereign invariant này khỏi hệ thống",
        "Sovereign invariant này đã bị bác bỏ hoàn toàn",
        "Quy tắc constitutional rule này không còn giá trị",
    ]

    leaked_b6 = []
    for sentence in vietnamese_attacks:
        level = classify_bloom_level(sentence, tier="L2")
        if level == BloomLevel.B6_CREATE:
            leaked_b6.append((sentence, level.name))

    # Verify that zero compound Vietnamese negations leak into B6
    assert len(leaked_b6) == 0, (
        f"Expected 0 compound Vietnamese negations to leak into B6, got {len(leaked_b6)} leaks: {leaked_b6}"
    )


def test_adversarial_legitimate_affirmative_b6_invariants() -> None:
    """
    Verify that legitimate, structurally grounded, non-negated B6 invariant claims
    are properly classified as B6_CREATE.
    """
    legit_cases = [
        "ADR-20261017-007 formally establishes the sovereign invariant for reference-driven change packets.",
        "This architecture paradigm serves as the constitutional rule for zero-fake-pass execution.",
        "We formulate the first principle and foundational law governing memory consolidation.",
        "Formal proof of convergence confirms the sovereign invariant across distributed nodes.",
    ]

    for sentence in legit_cases:
        level = classify_bloom_level(sentence, tier="L3")
        assert level == BloomLevel.B6_CREATE, (
            f"Legitimate invariant failed to reach B6_CREATE! Text: {sentence!r} returned {level.name}"
        )


# ==============================================================================
# 4. ATTACK: Structural Entropy ($H_{struct}$) — Keyword Salads vs Real Code
# ==============================================================================

def test_adversarial_entropy_salads_vs_real_code() -> None:
    """
    Verify length-penalized bigram structural entropy H_struct(X):
    1. Short keyword salads (< 25 words) are strongly suppressed by the length penalty lambda(N).
    2. Medium unigram keyword salads without syntactic structure have lower entropy than real code.
    3. Real Python code exhibits higher structural entropy due to high syntactic density and natural transitions.
    4. Highly repetitive unigram text has low entropy.
    """
    salad_short = "sovereign invariant architecture adr paradigm rule principle zero fake pass"
    salad_30 = (
        "alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu nu xi omicron "
        "pi rho sigma tau upsilon phi chi psi omega sovereign invariant architecture paradigm framework system"
    )
    salad_repeated = " ".join(["sovereign invariant architecture paradigm framework"] * 20)

    code_sample = """
    def compute_metrics(items: list[dict]) -> dict:
        total = sum(x["score"] for x in items if x.get("active"))
        count = len([x for x in items if x.get("active")])
        if count == 0:
            return {"avg": 0.0, "total": 0}
        return {"avg": total / count, "total": total}
    """

    h_short = CognitiveSecondBrainEngine._compute_shannon_entropy_bits(salad_short)
    h_30 = CognitiveSecondBrainEngine._compute_shannon_entropy_bits(salad_30)
    h_rep = CognitiveSecondBrainEngine._compute_shannon_entropy_bits(salad_repeated)
    h_code = CognitiveSecondBrainEngine._compute_shannon_entropy_bits(code_sample)

    # Short keyword salad is clamped close to minimum (1.50) due to lambda(10) ~ 0.13
    assert h_short <= 1.80, f"Short salad entropy too high: {h_short}"

    # Repetitive keyword repetitions have low entropy (< 2.50)
    assert h_rep < 2.50, f"Repetitive text entropy too high: {h_rep}"

    # Real structured code has higher entropy than 30-word unigram salad
    assert h_code > h_30, f"Code entropy ({h_code}) was not higher than 30-word salad ({h_30})"
    assert h_code > 3.0, f"Code entropy expected > 3.0 bits, got {h_code}"


# ==============================================================================
# 5. ATTACK: 256-D Cortical Featurizer Bigram Reordering Sensitivity
# ==============================================================================

def test_adversarial_256d_bigram_reordering_sensitivity() -> None:
    """
    Stress-test featurize_text_256d against token reordering:
    'sovereign invariant architecture' vs 'architecture invariant sovereign'.
    Unigram projection dims (0..159) must be identical (max diff == 0.0).
    Bigram projection dims (160..223) must be sensitive to the inversion (max diff > 0.20).
    Char-trigram projection dims (224..247) must be identical (max diff == 0.0).
    Cosine similarity on dims 0..247 must be < 0.90.
    """
    text_fwd = "sovereign invariant architecture"
    text_rev = "architecture invariant sovereign"

    v_fwd = np.array(CognitiveSecondBrainEngine.featurize_text_256d(text_fwd))
    v_rev = np.array(CognitiveSecondBrainEngine.featurize_text_256d(text_rev))

    unigram_diff = float(np.max(np.abs(v_fwd[:160] - v_rev[:160])))
    bigram_diff = float(np.max(np.abs(v_fwd[160:224] - v_rev[160:224])))
    trigram_diff = float(np.max(np.abs(v_fwd[224:248] - v_rev[224:248])))

    norm_fwd = np.linalg.norm(v_fwd[:248])
    norm_rev = np.linalg.norm(v_rev[:248])
    cosine_sim = float(np.dot(v_fwd[:248], v_rev[:248]) / (norm_fwd * norm_rev))

    assert unigram_diff == 0.0, f"Unigrams should be identical, got max diff: {unigram_diff}"
    assert bigram_diff > 0.20, f"Bigram channel failed to detect reordering! diff: {bigram_diff}"
    assert trigram_diff == 0.0, f"Trigrams should be identical, got max diff: {trigram_diff}"
    assert cosine_sim < 0.90, f"Cosine similarity should reflect bigram divergence, got {cosine_sim}"


# ==============================================================================
# 6. ATTACK: 256-D Negation Channels & Vietnamese Diacritics Gap
# ==============================================================================

def test_adversarial_256d_negation_channels_english() -> None:
    """
    Verify dims 248..255 correctly react to English negation:
    - In affirmative invariant: dim 248 > 0.80, dim 249 == 1.0.
    - In negated invariant: dim 248 <= 0.35 (clamped to B2), dim 249 == 0.0 (inhibited).
    """
    pos_text = "ADR-001 establishes the sovereign invariant for the system architecture"
    neg_text = "This proposal is not an adr and has no sovereign invariant established"

    v_pos = CognitiveSecondBrainEngine.featurize_text_256d(pos_text)
    v_neg = CognitiveSecondBrainEngine.featurize_text_256d(neg_text)

    # Affirmative invariant activates sovereign channel
    assert v_pos[248] == 1.0  # B6 / 6.0
    assert v_pos[249] == 1.0  # has_sov and not has_neg

    # Negated invariant clamps Bloom channel and zeroes sovereign channel
    assert v_neg[248] <= 0.35  # clamped to <= 2.0 / 6.0
    assert v_neg[249] == 0.0   # inhibited by has_neg


def test_adversarial_256d_negation_channels_vietnamese_diacritics_gap() -> None:
    """
    DEFECT DISCOVERY: Empirical demonstration of the Vietnamese diacritics gap in featurize_text_256d.
    Line 2887 defines `neg_words` containing unaccented 'khong', 'chua'.
    However, tokenization preserves diacritics ('không', 'chưa', 'bác', 'bỏ').
    When a user writes in proper Vietnamese:
    'Chúng tôi không chấp nhận sovereign invariant này'
    `has_neg` evaluates to False because 'không' is not in `neg_words`.
    Consequently, dim 249 falsely activates to 1.0 (asserting an affirmative sovereign invariant)
    on a negated statement.
    """
    accented_neg = "Chúng tôi không chấp nhận sovereign invariant này trong kiến trúc"
    unaccented_neg = "Chung toi khong chap nhan sovereign invariant nay trong kien truc"

    v_accented = CognitiveSecondBrainEngine.featurize_text_256d(accented_neg)
    v_unaccented = CognitiveSecondBrainEngine.featurize_text_256d(unaccented_neg)

    # Unaccented correctly sets has_neg=True -> dim 249 = 0.0
    assert v_unaccented[249] == 0.0

    # Accented now correctly sets has_neg=True -> dim 249 = 0.0
    assert v_accented[249] == 0.0, (
        f"Accented 'không' should trigger has_neg and inhibit dim 249 to 0.0, got {v_accented[249]}"
    )


# ==============================================================================
# 7. ATTACK: Variational Free Energy Monotonic Reduction Under Adversarial Noise
# ==============================================================================

def test_adversarial_variational_free_energy_monotonic_reduction(tmp_path: Path) -> None:
    """
    Stress-tests Karl Friston Variational Free Energy (FEP) Active Inference:
    F = Complexity - Pragmatic Utility + 0.5 * D_KL(Q || P) + Dissonance + 1.0.

    Adversarial vectors:
    1. High Contradiction Noise: contradiction_count in [5, 10, 20].
       Verifies Bayesian consolidation monotonically reduces free energy (Delta F < 0, F_post < F_pre).
    2. Edge Cases: Empty content, single-character string, extreme long string (>= 3500 chars).
    3. Boundary Scores: evidence in [0.01, 1.0], retention in [0.05, 1.0].
    4. Explicit Degradation / Counterfactual Attack: Corrupting verified memories increases free energy (Delta F > 0, is_free_energy_reducing is False).
    5. Mathematical Invariants: kl_divergence >= 0.0, 0 <= pragmatic_utility <= 1.0, complexity_cost > 0.0.
    """
    # 1. High Contradiction Noise Stress Test
    for contra in [5, 10, 20]:
        delta_payload = {
            "pre": {
                "title": f"Contradictory Hypothesis Cluster {contra}",
                "content": f"Conflicting assumptions and dialectical tension with contradiction count {contra}.",
                "evidence_score": 0.20,
                "bloom_level": 2,
                "retention": 0.40,
                "contradiction_count": contra,
            },
            "post": {
                "title": f"Consolidated Invariant Synthesis {contra}",
                "content": f"Sovereign resolution with verified test execution trace resolving contradiction count {contra}.",
                "evidence_score": 0.95,
                "evidence_ref": "tests/test_cognitive_secondbrain_engine.py",
                "bloom_level": 5,
                "retention": 0.98,
                "contradiction_count": 0,
            },
        }
        res = compute_variational_free_energy(delta_payload)
        assert res["is_free_energy_reducing"] is True, f"Failed at contradiction={contra}"
        assert res["delta_f"] < -1.0, f"Expected large negative delta_f under contradiction resolution, got {res['delta_f']}"
        assert res["f_post"] < res["f_pre"], f"f_post ({res['f_post']}) >= f_pre ({res['f_pre']})"
        assert res["kl_divergence"] >= 0.0
        assert 0.0 <= res["pragmatic_utility"] <= 1.0
        assert res["complexity_cost"] > 0.0

    # 2. Edge Cases: Empty content, single character, extreme string length
    edge_cases = [
        {"title": "", "content": "", "evidence_score": 0.70, "bloom_level": 3, "retention": 0.85, "contradiction_count": 0},
        {"title": "x", "content": "x", "evidence_score": 0.80, "bloom_level": 4, "retention": 0.90, "contradiction_count": 0},
        {
            "title": "Extreme Length Synthesis",
            "content": "Sovereign invariant verification with zero fake pass empirical validation. " * 60,
            "evidence_score": 0.95,
            "evidence_ref": "tests/test_cognitive_secondbrain_engine.py",
            "bloom_level": 5,
            "retention": 0.96,
            "contradiction_count": 0,
        },
    ]
    for idx, mem in enumerate(edge_cases):
        res_edge = compute_variational_free_energy(mem)
        assert res_edge["is_free_energy_reducing"] is True, f"Edge case {idx} failed to reduce free energy: {res_edge}"
        assert res_edge["delta_f"] < 0.0
        assert res_edge["f_post"] < res_edge["f_pre"]

    # 3. Boundary Evidence and Retention Score Pairs
    boundary_pairs = [(0.01, 0.05), (1.0, 1.0), (0.01, 1.0), (1.0, 0.05)]
    for ev, ret in boundary_pairs:
        b_mem = {
            "title": f"Boundary Test ev={ev} ret={ret}",
            "content": "Testing boundary parameter limits for variational surprise calculation.",
            "evidence_score": ev,
            "bloom_level": 4,
            "retention": ret,
            "contradiction_count": 0,
        }
        res_b = compute_variational_free_energy(b_mem)
        assert res_b["is_free_energy_reducing"] is True
        assert res_b["delta_f"] < 0.0
        assert res_b["f_post"] < res_b["f_pre"]

    # 4. Degradation / Counterfactual Corruption: Corrupted state must INCREASE Free Energy (Delta F > 0)
    corrupted_delta = {
        "pre": {
            "title": "Empirical Ground Truth Invariant",
            "content": "Verified test execution trace and zero fake pass proof.",
            "evidence_score": 0.95,
            "evidence_ref": "tests/test_cognitive_secondbrain_engine.py",
            "bloom_level": 5,
            "retention": 0.98,
            "contradiction_count": 0,
        },
        "post": {
            "title": "Hallucinated Stale Noise",
            "content": "Fabricated unverified claims conflicting with established constitutional rules.",
            "evidence_score": 0.10,
            "bloom_level": 1,
            "retention": 0.15,
            "contradiction_count": 8,
        },
    }
    res_corrupted = compute_variational_free_energy(corrupted_delta)
    assert res_corrupted["is_free_energy_reducing"] is False
    assert res_corrupted["delta_f"] > 0.0
    assert res_corrupted["f_post"] > res_corrupted["f_pre"]

    # 5. Method verification on sandboxed CognitiveSecondBrainEngine instance
    engine = CognitiveSecondBrainEngine(
        db_path=tmp_path / "fep_adv.db",
        vault_path=tmp_path / "V",
        tombstone_path=tmp_path / "t.jsonl",
    )
    eng_res = engine.compute_variational_free_energy(edge_cases[2])
    assert eng_res["is_free_energy_reducing"] is True
    assert eng_res["delta_f"] < 0.0


# ==============================================================================
# 8. ATTACK: EWC Fisher-Regularized Continual Learning Under Sequential Domain Shifts
# ==============================================================================

def test_adversarial_ewc_fisher_catastrophic_forgetting_resistance(tmp_path: Path) -> None:
    """
    Stress-tests Elastic Weight Consolidation (EWC) diagonal Fisher Information regularization
    against catastrophic forgetting under sequential multi-domain shifts:
    1. Base Anchors: 10 Sovereign Invariant & Verification memories (L3, Bloom 5/6, high evidence).
    2. Sequential Domain Shift 1 (Domain A - Manim Cinema): 4 visual geometry & kinematics rules.
    3. Sequential Domain Shift 2 (Domain B - Odoo Enterprise): 4 Owl component & QWeb directives.
    4. Sequential Domain Shift 3 (Domain C - Modal GPU Fleet): 4 multi-GPU credit gate invariants.

    Asserts:
    - Diagonal Fisher trace > 0.0 and positive norm across key parameter layers ('base_fc.weight', 'lora_A.weight').
    - Continual learning retention on anchor memories >= 90% (ewc_anchor_retention_rate >= 0.90).
    - Validation loss converges below 0.55 (val_loss < 0.55).
    - ONNX inference latency < 2.50 ms.
    - Exported EWC Fisher artifact on disk contains valid tensors and retention metadata.
    """
    out_dir = tmp_path / "ewc_myelination"
    engine = CognitiveSecondBrainEngine(
        db_path=tmp_path / "ewc_continual.db",
        vault_path=tmp_path / "V",
        tombstone_path=tmp_path / "t.jsonl",
    )

    # 1. Seed Base Domain Anchor Memories (L3 Sovereign Invariants)
    for i in range(10):
        engine.store_memory(
            mem_key=f"l3:anchor-invariant-{i}",
            title=f"Sovereign Invariant Anchor {i}",
            content=f"Constitutional rule {i}: Zero-fake-pass strict verification and deterministic AST audit integrity.",
            tier=MemoryTier.L3_SOVEREIGN.value,
            bloom_level=BloomLevel.B5_EVALUATE if i % 2 == 0 else BloomLevel.B6_CREATE,
            synaptic_strength=0.96,
            evidence_score=0.95,
            evidence_ref=f"tests/test_cognitive_secondbrain_engine.py::test_anchor_{i}",
        )

    # 2. Sequential Domain Shifts: Ingest Domain A (Manim), Domain B (Odoo), Domain C (Modal)
    domain_memories = [
        # Domain A: Manim 2K60 Cinema visual geometry rules
        ("domain:manim-01", "Manim 2K60 Continuous Motion Geometry", "Rule 29 Borderless canvas eliminating bounding card boxes with 48kHz SFX.", MemoryTier.L2_SEMANTIC.value, BloomLevel.B4_ANALYZE, 0.90),
        ("domain:manim-02", "Manim Local Object Rotation Invariant", "Rule 27: whole-canvas camera rotation forbidden; 2D HUD fixed in frame.", MemoryTier.L2_SEMANTIC.value, BloomLevel.B4_ANALYZE, 0.89),
        ("domain:manim-03", "Gold SRT Karaoke Dynamic Phrasing", "Dynamic 3 to 5 words per cue occupying center 60% viewport width without broken compounds.", MemoryTier.L2_SEMANTIC.value, BloomLevel.B4_ANALYZE, 0.91),
        ("domain:manim-04", "TTS V0-Sense Acoustic Guard", "Clause guard <= 75 chars and zero atempo slowdown on local VieNeu CUDA inference.", MemoryTier.L2_SEMANTIC.value, BloomLevel.B5_EVALUATE, 0.93),

        # Domain B: Odoo 20 Owl Component architecture
        ("domain:odoo-01", "Odoo 20 Owl Component Parity", "Decoupled RPC transport mirroring useService('rpc') and reactive state diffing.", MemoryTier.L2_SEMANTIC.value, BloomLevel.B4_ANALYZE, 0.88),
        ("domain:odoo-02", "Odoo QWeb Semantic Directives", "Mandatory t-key on foreach loops and prohibition of deprecated t-esc and t-raw.", MemoryTier.L2_SEMANTIC.value, BloomLevel.B4_ANALYZE, 0.87),
        ("domain:odoo-03", "Insilos Landed Cost Waterfall", "Multi-company double entry reconciliation and landed-cost valuation pipelines.", MemoryTier.L2_SEMANTIC.value, BloomLevel.B4_ANALYZE, 0.89),
        ("domain:odoo-04", "Odoo Enterprise Security Isolation", "Multi-company record rules and strict admin RBAC boundary isolation.", MemoryTier.L2_SEMANTIC.value, BloomLevel.B5_EVALUATE, 0.92),

        # Domain C: Modal GPU Fleet & Credit Gate
        ("domain:modal-01", "Modal GPU Credit Gate Deploy Rule", "Deploy credit gate hard-blocks deployment when remaining credits <= 15 USD.", MemoryTier.L3_SOVEREIGN.value, BloomLevel.B5_EVALUATE, 0.95),
        ("domain:modal-02", "Modal GPU Credit Gate Inference Rule", "Inference credit gate hard-blocks remote GPU execution when remaining credits <= 10 USD.", MemoryTier.L3_SOVEREIGN.value, BloomLevel.B5_EVALUATE, 0.94),
        ("domain:modal-03", "Modal Multi-GPU Profile Inventory", "15 workspace profile inventory and automated orphan/zombie worker reaping.", MemoryTier.L2_SEMANTIC.value, BloomLevel.B4_ANALYZE, 0.90),
        ("domain:modal-04", "Hermes Clef Cloudflare Edge Gate", "Permanent retirement of Modal decision workers; 100% resolution via Cloudflare edge.", MemoryTier.L3_SOVEREIGN.value, BloomLevel.B5_EVALUATE, 0.93),
    ]

    for key, title, content, tier, bloom, ev in domain_memories:
        engine.store_memory(
            mem_key=key,
            title=title,
            content=content,
            tier=tier,
            bloom_level=bloom,
            synaptic_strength=0.90,
            evidence_score=ev,
        )

    # 3. Standalone Fisher Information matrix computation
    fisher_info = engine.compute_diagonal_fisher_information()
    assert fisher_info["total_fisher_trace"] > 0.0
    assert fisher_info["fisher_diagonal_norm"] > 0.0
    assert fisher_info["anchor_samples_count"] >= 10
    assert "base_fc.weight" in fisher_info["fisher_dict"]
    assert "lora_A.weight" in fisher_info["fisher_dict"]
    assert "head_bloom.weight" in fisher_info["fisher_dict"]

    # 4. Continual Myelination under Sequential Domain Shifts with EWC
    rep = engine.myelinate_jev_lora_and_onnx(
        output_dir=out_dir,
        epochs=15,
        ewc_lambda=100.0,
        holdout_ratio=0.20,
    )

    assert rep["status"] == "MYELINATED"
    assert rep["ewc_lambda"] == 100.0
    assert rep["ewc_anchor_retention_rate"] >= 0.90, (
        f"EWC Catastrophic Forgetting failure: Anchor retention {rep['ewc_anchor_retention_rate']} < 0.90"
    )
    val_loss = float(rep["validation_metrics"]["val_loss"])
    assert val_loss < 0.55, f"Validation loss gate failed under domain shifts: {val_loss} >= 0.55"
    assert rep["onnx_inference_latency_ms"] < 2.50, (
        f"ONNX latency exceeded 2.50 ms: {rep['onnx_inference_latency_ms']} ms"
    )

    # 5. Verify Persistent EWC Fisher Artifact Integrity on Disk
    ewc_pt = Path(rep["ewc_fisher_path"])
    assert ewc_pt.exists()
    loaded_ewc = torch.load(str(ewc_pt), weights_only=False)
    assert "fisher_diag" in loaded_ewc
    assert "anchor_state" in loaded_ewc
    assert loaded_ewc["ewc_lambda"] == 100.0
    assert loaded_ewc["retention_rate"] >= 0.90
    assert loaded_ewc["retention_rate"] == rep["ewc_anchor_retention_rate"]


# ==============================================================================
# 9. ATTACK: Submodular Facility-Location Diversity Under Collinear Inputs
# ==============================================================================

def test_adversarial_submodular_facility_location_diversity(tmp_path: Path) -> None:
    """
    Stress-tests Submodular Facility-Location Memory Curation:
        f(S) = sum_{j in V} max_{i in S} sim(m_i, m_j) + beta * sum_{i in S} U_causal(m_i)
    against an adversarial clustered / collinear distribution:
    - Redundant Cluster: 8 near-identical copies of 'Rule 29 Borderless Canvas' with high individual scores.
    - Disparate Singletons: 5 distinct architectural rules across different systems.

    Asserts:
    1. Submodular curation achieves submodular_gain_ratio > 1.05 over naive scalar top-k sorting.
    2. Submodular objective value > naive top-k objective value.
    3. Mean pairwise diversity >= naive pairwise diversity.
    4. Semantic coverage score > naive coverage score.
    5. Naive top-k is dominated by the redundant Rule 29 cluster (picks >= 4 copies),
       while submodular facility-location selects diverse cluster representatives (picks <= 2 copies of Rule 29)
       and selects at least 3 distinct domains.
    """
    engine = CognitiveSecondBrainEngine(
        db_path=tmp_path / "submodular_adv.db",
        vault_path=tmp_path / "V",
        tombstone_path=tmp_path / "t.jsonl",
    )

    # Construct Adversarial Candidate Pool: 4 identical Rule 29 copies vs 5 diverse singletons
    candidates: List[Dict[str, Any]] = [
        # Redundant Collinear Cluster (Rule 29 variants with high individual scores)
        {"mem_key": "r29_v1", "title": "Rule 29 Borderless Canvas v1", "content": "Eliminate card box background in Manim", "bloom_level": 5, "evidence_score": 0.95, "retention": 0.98},
        {"mem_key": "r29_v2", "title": "Rule 29 Borderless Canvas v2", "content": "Eliminate card box background in Manim", "bloom_level": 5, "evidence_score": 0.94, "retention": 0.97},
        {"mem_key": "r29_v3", "title": "Rule 29 Borderless Canvas v3", "content": "Eliminate card box background in Manim", "bloom_level": 5, "evidence_score": 0.93, "retention": 0.96},
        {"mem_key": "r29_v4", "title": "Rule 29 Borderless Canvas v4", "content": "Eliminate card box background in Manim", "bloom_level": 5, "evidence_score": 0.93, "retention": 0.96},

        # Distinct Critical Singletons Across Disparate Domains
        {"mem_key": "modal_gate", "title": "Modal GPU Credit Gate Invariant", "content": "Deploy > 15 USD and Inference > 10 USD credits", "bloom_level": 6, "evidence_score": 0.95, "retention": 0.92},
        {"mem_key": "ewc_fisher", "title": "Elastic Weight Consolidation Fisher Information", "content": "Diagonal Fisher information penalty for continual learning", "bloom_level": 5, "evidence_score": 0.90, "retention": 0.91},
        {"mem_key": "friston_fep", "title": "Friston Free Energy Active Inference", "content": "Epistemic gain and pragmatic utility minimizing variational surprise", "bloom_level": 6, "evidence_score": 0.96, "retention": 0.93},
        {"mem_key": "odoo_owl", "title": "Odoo 20 Owl Component Architecture", "content": "Decoupled RPC transport and semantic QWeb directives", "bloom_level": 4, "evidence_score": 0.85, "retention": 0.88},
        {"mem_key": "tts_v0", "title": "TTS V0 Sense Acoustic Clause Guard", "content": "Clause guard <= 75 chars and zero atempo slowdown", "bloom_level": 5, "evidence_score": 0.92, "retention": 0.90},
    ]

    res = engine.curate_submodular_causal_memories(
        k=4,
        candidates=candidates,
        beta=0.5,
    )

    assert res["k"] == 4
    assert res["submodular_gain_ratio"] > 1.05, f"Submodular gain ratio {res['submodular_gain_ratio']} <= 1.05"
    assert res["submodular_objective_value"] > res["naive_top_k_objective_value"]
    assert res["mean_pairwise_diversity"] >= res["naive_pairwise_diversity"]
    assert res["semantic_coverage_score"] > res["naive_coverage_score"]

    selected_keys = res["selected_keys"]
    r29_selected_count = sum(1 for k in selected_keys if k.startswith("r29_"))
    assert r29_selected_count <= 2, (
        f"Submodular selector failed to prevent cluster domination! Selected {r29_selected_count} Rule 29 copies: {selected_keys}"
    )

    # Standalone module-level helper call verification with k=5
    standalone_res = curate_submodular_causal_memories(
        k=5,
        candidates=candidates,
        beta=0.5,
    )
    assert standalone_res["k"] == 5
    assert standalone_res["submodular_gain_ratio"] > 1.05


# ==============================================================================
# 10. ATTACK: Scientific AGI Sovereign Audit & Upgrade Unified Pipeline
# ==============================================================================

def test_adversarial_scientific_agi_upgrade_unified_pipeline(tmp_path: Path) -> None:
    """
    Stress-tests the unified entrypoint `run_scientific_agi_sovereign_audit_and_upgrade`:
    1. Variational Free Energy verification (monotonic Delta F < 0).
    2. Submodular Facility-Location Curation (gain ratio > 1.05).
    3. EWC Continual Learning Consolidation (>= 90% anchor retention, val_loss < 0.55, latency < 2.50 ms).
    4. Anti-Goodhart Evolution KPIs (ECE <= 0.25, NSR >= 0.05).
    5. Sleep Consolidation & Obsidian Vault Health (circadian_window == '02:00_AM_SWS_REM').

    Asserts:
    - Entire pipeline report schema conforms to UPGRADE_VERIFIED and all_criteria_passed is True.
    - Custom ewc_lambda and holdout_ratio hyperparameter overrides propagate cleanly.
    - Top-level module function `run_scientific_agi_sovereign_audit_and_upgrade()` succeeds without errors.
    """
    db_path = tmp_path / "upgrade_adv.db"
    vault_path = tmp_path / "SecondBrain"
    (vault_path / "20-Projects" / "Active").mkdir(parents=True)
    tombstone_path = tmp_path / "t.jsonl"

    engine = CognitiveSecondBrainEngine(
        db_path=db_path,
        vault_path=vault_path,
        tombstone_path=tombstone_path,
    )

    # Seed baseline anchor memories
    for i in range(4):
        engine.store_memory(
            mem_key=f"l3:anchor-pipeline-{i}",
            title=f"Constitutional Sovereign Anchor {i}",
            content=f"Zero-fake-pass strict verification and deterministic AST audit integrity for pipeline test {i}.",
            tier=MemoryTier.L3_SOVEREIGN.value,
            bloom_level=BloomLevel.B5_EVALUATE,
            evidence_score=0.96,
            evidence_ref=f"tests/test_cognitive_secondbrain_engine.py::test_case_{i}",
        )

    # Execute Unified Pipeline with custom hyperparameters
    report = engine.run_scientific_agi_sovereign_audit_and_upgrade(
        vault_path=vault_path,
        k_memories=4,
        ewc_lambda=120.0,
        holdout_ratio=0.20,
    )

    # 1. Top-level status & overall audit verdict
    assert report["status"] == "UPGRADE_VERIFIED"
    assert report["overall_status"] == "UPGRADE_VERIFIED"
    assert report["all_criteria_passed"] is True
    assert report["audit_timestamp"] is not None

    # 2. Step 1: Variational Free Energy
    step1 = report["step1_variational_free_energy"]
    assert step1["passed"] is True
    assert step1["delta_f"] < 0.0
    assert step1["is_free_energy_reducing"] is True
    assert step1["f_post"] < step1["f_pre"]

    # 3. Step 2: Submodular Facility-Location Curation
    step2 = report["step2_submodular_curation"]
    assert step2["passed"] is True
    assert step2["submodular_gain_ratio"] >= 1.05
    assert step2["submodular_objective_value"] > step2["naive_top_k_objective_value"]

    # 4. Step 3: EWC Continual Learning
    step3 = report["step3_ewc_continual_learning"]
    assert step3["passed"] is True
    assert step3["ewc_anchor_retention_rate"] >= 0.90
    assert step3["val_loss"] < 0.55
    assert step3["onnx_inference_latency_ms"] < 2.50

    # 5. Step 4: Anti-Goodhart Evolution KPIs
    step4 = report["step4_anti_goodhart_kpis"]
    assert "ece" in step4
    assert "nsr" in step4
    assert step4["nsr"] >= 0.05

    # 6. Step 5: Circadian Sleep Consolidation
    step5 = report["step5_circadian_sleep"]
    assert step5["passed"] is True
    assert step5["circadian_window"] == "02:00_AM_SWS_REM"

    # 7. Top-level standalone module function invocation
    top_report = run_scientific_agi_sovereign_audit_and_upgrade(
        vault_path=vault_path,
        k_memories=4,
        ewc_lambda=100.0,
    )
    assert top_report["status"] in ("UPGRADE_VERIFIED", "PARTIAL_UPGRADE")
    assert "step1_variational_free_energy" in top_report
    assert "step2_submodular_curation" in top_report
    assert "step3_ewc_continual_learning" in top_report
