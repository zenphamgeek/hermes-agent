"""
tests/test_cognitive_secondbrain_adversarial_challenge.py

Adversarial Counterfactual Challenge & Stress Testing Suite for Milestone M2:
1. classify_bloom_level short keyword strings (< 30 chars, < 5 words) across L1, L2, L3.
2. classify_bloom_level English forward & backward/post-predicate negations.
3. classify_bloom_level Vietnamese compound negations and post-predicate phrasing.
4. _compute_shannon_entropy_bits keyword salads vs structured Python code.
5. featurize_text_256d bigram reordering sensitivity (dims 160..223).
6. featurize_text_256d negation channel activations (dims 248..255) and Vietnamese diacritics gap.
"""

from __future__ import annotations

import math
import numpy as np
import pytest

from tools.cognitive_secondbrain_engine import (
    BloomLevel,
    CognitiveSecondBrainEngine,
    classify_bloom_level,
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
