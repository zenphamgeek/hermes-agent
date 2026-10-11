#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tts_v0_sense_synthesizer.py
===========================
TTS V0-Sense Engine: The Sole Gold TTS Standard for Workspace hermes-agent.

4 Pillars:
1. Sense-Processing: English tech term wrapping (<en>...</en>), subtle [cười] cues,
   dramatic script punctuation (..., —), and dynamic scene temper (0.52 - 0.60).
2. Direct Raw VieNeu CUDA Synthesis: Local VieNeu-TTS v3 Turbo on Quadro RTX 5000 16GB.
3. Smart Silence Gate: Frame-by-frame 20ms RMS scan compressing dead gaps > 0.35s to 0.20s.
4. 5-Stage Studio Vocal Mastering: Highpass 80Hz, De-mud 300Hz, Presence 3.8kHz, Air Treble 9kHz,
   EBU R128 Loudnorm -14.5 LUFS, 48kHz Stereo.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional, Union, List, Tuple

import numpy as np
import soundfile as sf

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REF_WAV = REPO_ROOT / "assets" / "voices" / "Zen Mien Tay" / "zenpham-zen-meditation-mientay.wav"

try:
    from tts_input_sanitizer import sanitize_tts_input
except ImportError:
    from assets.scripts_video.tts_input_sanitizer import sanitize_tts_input

# Ensure vieneu package can be imported from vieneu_tts_test or /home/zen/vieneu-tts
VIENEU_SRC = REPO_ROOT / "vieneu_tts_test" / "src"
ALT_VIENEU_SRC = Path("/home/zen/vieneu-tts/src")
if str(VIENEU_SRC) not in sys.path:
    sys.path.insert(0, str(VIENEU_SRC))
if ALT_VIENEU_SRC.exists() and str(ALT_VIENEU_SRC) not in sys.path:
    sys.path.insert(0, str(ALT_VIENEU_SRC))

try:
    from vieneu import Vieneu
except ImportError:
    Vieneu = None


# ---------------------------------------------------------------------------
# Pillar 1: Sense-Processing
# ---------------------------------------------------------------------------

KNOWN_TECH_TERMS = [
    r"Innoria(?:\s+Solution)?",
    r"Innoria",
    r"Solution",
    r"Overfitting",
    r"Transformer",
    r"Softmax",
    r"Temperature",
    r"DAG",
    r"LLM",
    r"Vector",
    r"Embedding",
    r"Embeddings",
    r"Loss",
    r"Cross-Entropy",
    r"Entropy",
    r"Bayes",
    r"Bayesian",
    r"Prior",
    r"Likelihood",
    r"Posterior",
    r"Laplace",
    r"Sensor",
    r"Sensors",
    r"Calibration",
    r"Adam",
    r"Gradient",
    r"Descent",
    r"Prompt",
    r"Attention",
    r"Self-Attention",
    r"Multi-Head",
    r"Feedforward",
    r"Backprop",
    r"Backpropagation",
    r"Dropout",
    r"Batch",
    r"Normalization",
    r"LayerNorm",
    r"Residual",
    r"Token",
    r"Tokens",
    r"Tokenizer",
    r"Inference",
    r"Weights",
    r"Biases",
    r"SVD",
    r"PCA",
    r"Autoencoder",
    r"VAE",
    r"Latent",
    r"Diffusion",
    r"Zero-Shot",
    r"Few-Shot",
    r"Fine-Tuning",
    r"RLHF",
    r"DPO",
    r"RoPE",
    r"K-Means",
    r"Manifold",
    r"Eckart-Young",
    r"Frobenius",
    r"LoRA",
    r"Momentum",
    r"RMSprop",
    r"RMSProp",
    r"Nesterov",
    r"NaN",
    r"Warmup",
    r"Cosine",
    r"Annealing",
    r"Scheduling",
    r"Clipping",
    r"Lookahead",
    r"Ravine",
    r"Learning Rate",
    r"Multi-Agent",
    r"Agents?",
    r"AutoGen",
    r"Orchestrator",
    r"Sequential",
    r"Hierarchical",
    r"Blackboard",
    r"Groupthink",
    r"Infinite Loop",
    r"Token Budget",
    r"Self-Healing",
    r"Human-in-the-loop",
    r"Context Window",
    r"Red[- ]Teaming",
    r"Architect",
    r"Coder",
    r"Critic",
    r"Reviewer",
    r"Auditor",
    r"Proposer",
    r"Skeptic",
    r"Swarm Intelligence",
    r"Swarm",
    r"Shared State",
    r"Sandbox",
    r"Smallville",
    r"Distributed Training",
    r"Condorcet",
    r"Pareto",
    r"InfiniBand",
]

def sense_process_text(text: str) -> str:
    """
    Applies Sense-Processing to raw author script:
    1. Preserves [cười] / [chuckle] and maps to clean [cười].
    2. Converts ineffective [thở dài] / [hắng giọng] or other emotional tags into
       dramatic script rhythm punctuation ('... ').
    3. Normalizes dashes and hyphens used as clause separators (—, –, -) to natural comma pauses.
    4. Strips HTML tags (<br>, <span>, etc.) and markdown code formatting (`code`, **, *).
    5. Wraps English tech terms in <en>...</en> with watertight tag hygiene (zero nested tags, zero stray <>).
    6. Normalizes whitespace, punctuation, and dramatic pauses.
    """
    if not text:
        return ""

    processed = text.strip()

    # 0. Zero-Code/LaTeX Leak Guard: Translate math symbols or sanitize raw LaTeX
    GREEK_SPOKEN_MAP = {
        r"\$\s*\\eta\s*\$": "ê-ta",
        r"\$\s*\\kappa\s*\$": "cáp-pa",
        r"\$\s*\\alpha\s*\$": "an-pha",
        r"\$\s*\\beta\s*\$": "bê-ta",
        r"\$\s*\\theta\s*\$": "thê-ta",
        r"\$\s*\\lambda\s*\$": "lam-đa",
        r"\$\s*\\sigma\s*\$": "xích-ma",
        r"\$\s*\\nabla\s*\$": "Gradient",
        r"\$\s*\\mu\s*\$": "muy",
        r"\$\s*\\pi\s*\$": "pi",
        r"\$\s*\\Delta\s*\$": "đen-ta",
    }
    for pat, rep in GREEK_SPOKEN_MAP.items():
        processed = re.sub(pat, rep, processed)

    # Sanitize and strip any remaining raw LaTeX formulas ($...$ or $$...$$)
    def clean_latex_formula(m):
        raw = m.group(0)
        print(f"[!] WARNING: Raw LaTeX formula leaked in script: {raw!r}. Sanitizing to prevent TTS corruption!")
        return ""

    processed = re.sub(r"\$\$[\s\S]*?\$\$", clean_latex_formula, processed)
    processed = re.sub(r"\$[^$]+\$", clean_latex_formula, processed)
    processed = re.sub(r"\\[a-zA-Z]+(?:\{[^}]*\})*", "", processed)

    # 1. Clean HTML line breaks and markup (strip all tags except <en>...</en>)
    processed = re.sub(r"<br\s*/?>", "\n\n", processed, flags=re.IGNORECASE)
    processed = re.sub(r"<(?!/?en\b)[^>]+>", "", processed, flags=re.IGNORECASE)

    # 2. Clean markdown code formatting and leaked symbols
    processed = re.sub(r"`([^`]+)`", r"\1", processed)  # inline code backticks
    processed = re.sub(r"\*\*([^*]+)\*\*", r"\1", processed)  # bold
    processed = re.sub(r"\*([^*]+)\*", r"\1", processed)  # italic
    processed = re.sub(r"^[-*•]\s+", "", processed, flags=re.MULTILINE)  # list bullets

    # 3. Clean bracket tags
    def replace_brackets(match):
        inner = match.group(1).strip().lower()
        if inner in ["cười", "chuckle", "cuoi"]:
            return " [cười] "
        elif inner in ["thở dài", "sigh", "tho dai", "hắng giọng", "clear throat", "hang giong"]:
            return "... "
        elif inner.startswith("<|emotion_") or inner.startswith("en") or inner.startswith("/en"):
            return match.group(0)
        else:
            return " "

    processed = re.sub(r"\[(.*?)\]", replace_brackets, processed)

    # 4. Normalize dashes and hyphens used as clause separators / pauses & clean Vietnamese transliterations
    VN_HYPHEN_MAP = {
        r"\bvéc-tơ\b": "véc tơ",
        r"\bnơ-ron\b": "nơ ron",
        r"\bcô-sin\b": "cô sin",
        r"\bxích-ma\b": "xích ma",
        r"\bê-ta\b": "ê ta",
        r"\ban-pha\b": "an pha",
        r"\bbê-ta\b": "bê ta",
        r"\bcáp-pa\b": "cáp pa",
        r"\blam-đa\b": "lam đa",
        r"\bđen-ta\b": "đen ta",
        r"\bngu-yên\b": "nguyên",
        r"\bphân-phối\b": "phân phối",
        r"\bAugustin-Louis\b": "Augustin Louis",
    }
    for pat, rep in VN_HYPHEN_MAP.items():
        processed = re.sub(pat, rep, processed, flags=re.IGNORECASE)

    processed = re.sub(r"\s*[—–]\s*", ", ", processed)  # em-dashes and en-dashes to comma pause
    processed = re.sub(r"-{2,}", ", ", processed)  # multi-hyphens --, ---
    processed = re.sub(r"\s+-\s+", ", ", processed)  # isolated hyphen between spaces
    processed = re.sub(r"(?<=[.,!?;])\s*-\s*", " ", processed)
    processed = re.sub(r"\s*-\s*(?=[.,!?;])", " ", processed)
    processed = re.sub(r"(?<=[a-zà-ỹ0-9])\s*-\s*(?=[a-zà-ỹ0-9])", " ", processed, flags=re.IGNORECASE)  # hyphens between Vietnamese words
    processed = re.sub(r"\s*-\s*", ", ", processed)  # any remaining dangling hyphen to comma
    processed = re.sub(r",\s*,+", ", ", processed)  # deduplicate commas
    processed = re.sub(r"\s+,", ",", processed)

    # 5. Watertight <en>...</en> Tag Hygiene (Zero Nested Tags, Zero Stray Angle Brackets)
    # Step A: Unnest any existing nested <en> tags
    def unnest_en(m):
        c = re.sub(r"</?en>", "", m.group(1), flags=re.IGNORECASE)
        return f"<en>{c.strip()}</en>"

    for _ in range(5):
        processed = re.sub(r"<en>((?:(?!</en>).)*?<en>.*?</en>.*?)</en>", unnest_en, processed, flags=re.IGNORECASE | re.DOTALL)
        processed = re.sub(r"<en>(.*?)</en>", unnest_en, processed, flags=re.IGNORECASE | re.DOTALL)

    # Step B: Protect existing valid <en>...</en> blocks with placeholders
    placeholders = []
    def save_en(m):
        idx = len(placeholders)
        inner = re.sub(r"</?en>", "", m.group(0), flags=re.IGNORECASE).strip()
        placeholders.append(f"<en>{inner}</en>")
        return f"___EN_PLACEHOLDER_{idx}___"

    processed = re.sub(r"<en>.*?</en>", save_en, processed, flags=re.IGNORECASE | re.DOTALL)

    # Step C: Strip any remaining stray <en> or </en> or stray angle brackets <, >
    processed = re.sub(r"</?en>", "", processed, flags=re.IGNORECASE)
    processed = re.sub(r"[<>]", "", processed)

    # Step D: Wrap known tech terms on the remaining text
    for term in KNOWN_TECH_TERMS:
        pattern = rf"\b({term})\b"
        processed = re.sub(pattern, r"<en>\1</en>", processed, flags=re.IGNORECASE)

    # Step E: Restore placeholders
    for idx, val in enumerate(placeholders):
        processed = processed.replace(f"___EN_PLACEHOLDER_{idx}___", val)

    # 6. Final whitespace, punctuation, and pause normalization
    processed = re.sub(r"[ \t]+", " ", processed)
    processed = re.sub(r",\s*,+", ", ", processed)
    processed = re.sub(r",\s*\.", ".", processed)
    processed = re.sub(r"\.\s*,", ".", processed)
    processed = re.sub(r"\.{4,}", "...", processed)
    processed = re.sub(r"\n\s*\n+", "\n\n", processed)
    processed = re.sub(r"(?<!\n)\n(?!\n)", " ", processed)
    processed = re.sub(r"[ \t]+([.,!?:;])", r"\1", processed)

    return processed.strip()


# ---------------------------------------------------------------------------
# Pillar 3: Smart Silence Gate
# ---------------------------------------------------------------------------

def clean_silence_gaps(
    data: np.ndarray,
    sr: int = 48000,
    threshold_rms: float = 0.0008,
    max_gap_s: float = 0.60,
    target_gap_s: float = 0.28,
    safety_pad_s: float = 0.04
) -> np.ndarray:
    """
    Scans audio frame-by-frame (20ms) for true dead silence (RMS < threshold_rms).
    Preserves subtle human micro-breaths (RMS 0.0008 - 0.004) and trailing word sounds
    while compressing unnatural dead air gaps > max_gap_s down to target_gap_s with a
    smooth raised-cosine crossfade. Eliminates GPU EOS delays while keeping speech continuous.
    Uses 40ms safety padding before/after gaps to guarantee zero phoneme clipping.
    """
    is_stereo = (data.ndim == 2)
    mono = data.mean(axis=1) if is_stereo else data

    frame_len = int(0.02 * sr)  # 20ms
    n_frames = len(mono) // frame_len
    energies = [np.sqrt(np.mean(mono[i*frame_len : (i+1)*frame_len]**2)) for i in range(n_frames)]

    is_silent = np.array(energies) < threshold_rms

    segments_to_keep = []
    in_gap = False
    gap_start = 0
    seg_start = 0

    target_gap_samples = int(target_gap_s * sr)
    fade_len = int(0.02 * sr)  # 20ms crossfade
    safety_pad = int(safety_pad_s * sr) # default 40ms safety padding to preserve phoneme tails

    for i, s in enumerate(is_silent):
        if s and not in_gap:
            in_gap = True
            gap_start = i * frame_len
        elif not s and in_gap:
            in_gap = False
            gap_end = i * frame_len
            gap_dur = (gap_end - gap_start) / sr
            if gap_dur > max_gap_s:
                # Add audio up to gap_start + safety_pad
                seg_end = min(len(data), gap_start + safety_pad)
                segments_to_keep.append(data[seg_start:seg_end])
                # Insert controlled natural room silence
                silence_shape = (target_gap_samples, 2) if is_stereo else (target_gap_samples,)
                segments_to_keep.append(np.zeros(silence_shape, dtype=data.dtype))
                # Resume with safety padding before gap_end
                seg_start = max(0, gap_end - safety_pad)

    # Handle trailing silence at end of audio stream
    if in_gap:
        gap_end = len(mono)
        gap_dur = (gap_end - gap_start) / sr
        if gap_dur > max_gap_s:
            seg_end = min(len(data), gap_start + safety_pad)
            segments_to_keep.append(data[seg_start:seg_end])
            silence_shape = (target_gap_samples, 2) if is_stereo else (target_gap_samples,)
            segments_to_keep.append(np.zeros(silence_shape, dtype=data.dtype))
            seg_start = len(data)

    if seg_start < len(data):
        segments_to_keep.append(data[seg_start:])
    return np.concatenate(segments_to_keep, axis=0)


# ---------------------------------------------------------------------------
# Pillar 2 & 4: Engine + Mastering
# ---------------------------------------------------------------------------

class TtsV0SenseEngine:
    def __init__(self, ref_wav: Optional[Path] = None, device: str = "cuda"):
        if Vieneu is None:
            raise ImportError(
                "Vieneu package not found. Run with: "
                f"{REPO_ROOT}/vieneu_tts_test/.venv/bin/python"
            )
        self.ref_wav = Path(ref_wav) if ref_wav else DEFAULT_REF_WAV
        if not self.ref_wav.exists():
            raise FileNotFoundError(f"Reference audio not found: {self.ref_wav}")

        print(f"[*] Initializing TTS V0-Sense Engine on {device.upper()}...")
        t0 = time.time()
        self.engine = Vieneu()
        print(f"✓ TTS V0-Sense Engine ready in {time.time() - t0:.2f}s")
        print(f"  Voice Reference: {self.ref_wav.name}")

    def synthesize(
        self,
        raw_text: str,
        output_wav: Union[str, Path],
        temper: Optional[float] = None,
        scene_index: int = 2,
        target_lufs: float = -14.5,
        target_tp: float = -1.5,
        target_wpm: Optional[float] = None,
        tempo: Optional[float] = None,
        pause_between_paragraphs_s: float = 0.35
    ) -> dict:
        """
        Executes full 4-pillar TTS V0-Sense pipeline (VieNeu V0-Expression Standard):
        1. Sense-Processing (English terms, [cười], punctuation)
        2. Direct Raw VieNeu CUDA Synthesis with Dynamic Temper and natural paragraph pauses
        3. Smart Silence Gate (zero dead gaps, preserves micro-breaths)
        4. 5-Stage Studio Vocal Mastering (Highpass, De-mud, Presence, Treble, EBU R128)
        """
        output_wav = Path(output_wav)
        output_wav.parent.mkdir(parents=True, exist_ok=True)
        raw_wav = output_wav.with_suffix(".raw.wav")
        gated_wav = output_wav.with_suffix(".gated.wav")

        # Security Control: Sanitize input against control chars, ANSI escapes, Trojan Source
        raw_text = sanitize_tts_input(raw_text)

        # 1. Sense-Processing
        processed_text = sense_process_text(raw_text)

        # Dynamic Temper selection (Golden ZenPham tuning):
        # 0.58 for Hook (Scene 1), 0.54 for Math/Tech (Scenes 2-10), 0.52 for Outro (Scene 11+)
        if temper is None:
            if scene_index == 1:
                temper = 0.58
            elif scene_index >= 11:
                temper = 0.52
            else:
                temper = 0.54

        words_count = len(processed_text.split())
        print(f"\n[TTS V0-Sense] Synthesizing Scene {scene_index:02d} (temper={temper:.2f}, {words_count} words)...")
        t0 = time.time()

        # 2. Direct Raw CUDA Inference with Paragraph-Level Natural Pacing
        # Preserve natural sentence flow within each thought block.
        # Between major paragraphs (\n\n), allow a light natural pause (0.35s).
        paragraphs = [p.strip() for p in processed_text.split("\n\n") if p.strip()]
        if not paragraphs:
            paragraphs = [processed_text]

        print(f"  -> VieNeu V0-Expression: {len(paragraphs)} paragraph block(s)")
        wav_chunks = []
        para_pause = np.zeros(int(pause_between_paragraphs_s * 48000), dtype=np.float32)

        for idx, para in enumerate(paragraphs):
            para_audio = self.engine.infer(
                para,
                ref_audio=str(self.ref_wav),
                denoise=True,
                temperature=temper,
                repetition_penalty=1.12,
                top_k=20,
                top_p=0.92,
                max_chars=180
            )
            wav_chunks.append(para_audio)
            if idx < len(paragraphs) - 1:
                wav_chunks.append(para_pause)

        audio = np.concatenate(wav_chunks) if len(wav_chunks) > 1 else wav_chunks[0]
        t_infer = time.time() - t0
        sf.write(str(raw_wav), audio, 48000)

        # 3. Smart Silence Gate (Safe Margin: threshold=0.0008, safety_pad=40ms, max_gap_s=0.60s, target_gap_s=0.28s)
        raw_data, sr = sf.read(str(raw_wav))
        gated_data = clean_silence_gaps(
            raw_data,
            sr=sr,
            threshold_rms=0.0008,
            max_gap_s=0.60,
            target_gap_s=0.28,
            safety_pad_s=0.04
        )
        sf.write(str(gated_wav), gated_data, sr)

        raw_dur = len(raw_data) / sr
        gated_dur = len(gated_data) / sr
        saved_s = raw_dur - gated_dur
        print(f"✓ Smart Silence Gate: {raw_dur:.2f}s -> {gated_dur:.2f}s (reclaimed {saved_s:.2f}s dead air)")

        natural_wpm = (words_count / gated_dur) * 60.0 if gated_dur > 0 else 0
        print(f"  -> Natural VieNeu V0-Expression Cadence: {natural_wpm:.1f} WPM")

        # 4. 5-Stage Studio Vocal Mastering Chain (Smooth, warm, resonant, 48kHz Stereo)
        filters = [
            "highpass=f=75",
            "equalizer=f=300:t=q:w=1.2:g=-1.5",
            "equalizer=f=3400:t=q:w=1.0:g=1.8",
            "treble=g=2.0:f=8500:t=s",
        ]
        if tempo is not None and abs(tempo - 1.0) > 0.005:
            filters.append(f"atempo={tempo:.4f}")
        elif target_wpm is not None and natural_wpm > 0:
            effective_tempo = target_wpm / natural_wpm
            if abs(effective_tempo - 1.0) > 0.02:
                filters.append(f"atempo={effective_tempo:.4f}")
        filters.append(f"loudnorm=I={target_lufs}:TP={target_tp}:LRA=7.0")
        af_chain = ", ".join(filters)

        cmd = [
            "ffmpeg", "-y",
            "-i", str(gated_wav),
            "-af", af_chain,
            "-ar", "48000",
            "-ac", "2",
            str(output_wav)
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Cleanup intermediate files
        for tmp_f in [raw_wav, gated_wav]:
            if tmp_f.exists():
                tmp_f.unlink()

        # Audit with ffprobe (safe array-based call, zero shell=True)
        probe_cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(output_wav)
        ]
        dur = float(subprocess.check_output(probe_cmd).decode().strip())

        measured_wpm = (words_count / dur) * 60.0 if dur > 0 else 0

        print(f"✓ Mastered Output ({dur:.2f}s, {measured_wpm:.1f} WPM, EBU {target_lufs} LUFS): {output_wav.name} (TTS took {t_infer:.1f}s)")
        return {
            "output_wav": str(output_wav),
            "duration": dur,
            "raw_duration": raw_dur,
            "saved_silence": saved_s,
            "temper": temper,
            "words": words_count,
            "natural_wpm": natural_wpm,
            "measured_wpm": measured_wpm,
            "tempo": tempo if tempo else 1.0,
            "infer_time_s": t_infer
        }


def main():
    parser = argparse.ArgumentParser(description="TTS V0-Sense Synthesizer")
    parser.add_argument("--text-file", type=Path, help="Input raw text file")
    parser.add_argument("--text", type=str, help="Direct input text")
    parser.add_argument("--output", type=Path, required=True, help="Output master wav path")
    parser.add_argument("--temper", type=float, default=None, help="Sampling temperature")
    parser.add_argument("--scene-index", type=int, default=2, help="Scene index for dynamic temper")
    parser.add_argument("--ref-wav", type=Path, default=None, help="Reference voice wav")
    parser.add_argument("--target-wpm", type=float, default=None, help="Target cadence WPM (default: None for natural VieNeu speed)")
    parser.add_argument("--tempo", type=float, default=None, help="Direct tempo scaling factor (default: None)")
    parser.add_argument("--target-lufs", type=float, default=-14.5, help="EBU R128 target LUFS (default: -14.5)")
    parser.add_argument("--target-tp", type=float, default=-1.5, help="EBU R128 True Peak limit (default: -1.5)")
    args = parser.parse_args()

    if args.text_file:
        raw_text = args.text_file.read_text(encoding="utf-8")
    elif args.text:
        raw_text = args.text
    else:
        print("Error: must provide either --text-file or --text")
        sys.exit(1)

    engine = TtsV0SenseEngine(ref_wav=args.ref_wav)
    engine.synthesize(
        raw_text=raw_text,
        output_wav=args.output,
        temper=args.temper,
        scene_index=args.scene_index,
        target_lufs=args.target_lufs,
        target_tp=args.target_tp,
        target_wpm=args.target_wpm,
        tempo=args.tempo
    )

if __name__ == "__main__":
    main()
