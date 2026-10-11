#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
synthesize_series_01_tap_05.py
==============================
Synthesizes, verifies, and masters studio-grade audio for Series 1 Episode 5 (S1E5):
"Phân Phối Chuẩn & Định Lý Giới Hạn Trung Tâm — Trật Tự Từ Hỗn Loạn"
from assets/scripts_video/s1_e5_masterclass_blueprint.md using TTS V0-Sense on CUDA.

Produces:
- assets/scripts_video/audio/series_01/tap_05/scene_01.wav .. scene_08.wav
- assets/scripts_video/audio/series_01/tap_05/master_audio_series_01_tap_05.wav
- assets/scripts_video/audio/series_01/tap_05/scene_timings.json
- assets/scripts_video/audio/series_01/tap_05/asr_verification_report.json
"""

import argparse
import difflib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

import numpy as np
import soundfile as sf

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Ensure vieneu package can be imported
VIENEU_SRC = REPO_ROOT / "vieneu_tts_test" / "src"
if str(VIENEU_SRC) not in sys.path:
    sys.path.insert(0, str(VIENEU_SRC))

from assets.scripts_video.asr_closed_loop_gate import (
    COMPOUND_TERMS, CONJUNCTIONS, get_compound_spans, is_space_in_compound,
    sense_process_text, clean_for_repetition, count_phrase_occurrences,
    find_all_text_repetitions, clean_silence_gaps, audit_audio_silence_holes,
    preload_cuda_cublas
)

BLUEPRINT_PATH = REPO_ROOT / "assets" / "scripts_video" / "s1_e5_masterclass_blueprint.md"
OUTPUT_DIR = REPO_ROOT / "assets" / "scripts_video" / "audio" / "series_01" / "tap_05"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
DEFAULT_REF_WAV = REPO_ROOT / "assets" / "voices" / "Zen Mien Tay" / "zenpham-zen-meditation-mientay.wav"

# Common Vietnamese function words and phonetic homophones for ASR auditing
VN_COMMON_WORDS = {
    "và", "là", "của", "cho", "trong", "với", "được", "có", "các", "những",
    "này", "đó", "ra", "vào", "lại", "thì", "mà", "từ", "ở", "về", "đến",
    "để", "như", "một", "hai", "ba", "bốn", "năm", "sẽ", "đã", "đang", "khi",
    "cũng", "rất", "quá", "lắm", "thế", "vậy", "ấy", "họ", "ông", "ta", "bạn",
    "hàng", "chi", "trung", "tâm", "định", "phần", "mặt", "hình", "chiều",
    "điểm", "giá", "trị", "số", "biến", "ngẫu", "nhiên", "chuẩn", "hóa",
    "nào", "gì", "ai", "đâu", "sao", "làm", "nay", "qua", "lên", "xuống"
}


def audit_asr_repetition(canonical_text: str, asr_segments: Any) -> Tuple[bool, str, List[Dict[str, Any]]]:
    """
    Closed-Loop Faster-Whisper ASR Repetition & Defect Auditor:
    1. Zero consecutive word stutter (w_i == w_{i+1}) not in canonical text.
    2. Zero n-gram repetition loops (2 to 6 gram) not in canonical text.
    3. Zero complete omission (empty ASR transcript).
    4. Word-frequency excess check with tolerance for ASR homophone transcription.
    """
    if isinstance(asr_segments, str):
        asr_text = asr_segments
    elif isinstance(asr_segments, list):
        text_parts = []
        for s in asr_segments:
            if hasattr(s, "text"):
                text_parts.append(s.text)
            elif isinstance(s, dict) and "text" in s:
                text_parts.append(s["text"])
            else:
                text_parts.append(str(s))
        asr_text = " ".join(text_parts)
    else:
        asr_text = str(asr_segments)

    issues: List[Dict[str, Any]] = []
    c_words = clean_for_repetition(canonical_text)
    a_words = clean_for_repetition(asr_text)

    if canonical_text.strip() and not asr_text.strip():
        return True, "Complete omission: ASR transcript is empty", [{"type": "empty_asr"}]
    if not c_words or not a_words:
        return False, "Clean", []

    # 1. Check phrase and n-gram repetitions
    candidate_reps = find_all_text_repetitions(asr_text)
    for rep_phrase in candidate_reps:
        rep_words = rep_phrase.split()
        c_count = count_phrase_occurrences(c_words, rep_words)
        a_count = count_phrase_occurrences(a_words, rep_words)
        if a_count > c_count:
            issues.append({"type": "repetition", "phrase": rep_phrase})
            return True, f"Repetition detected: '{rep_phrase}'", issues

    # 2. Check single-word consecutive stutter not in canonical text
    for i in range(len(a_words) - 1):
        w1 = a_words[i]
        w2 = a_words[i + 1]
        if w1 == w2 and len(w1) >= 1:
            c_pair_found = any(
                c_words[k] == w1 and c_words[k + 1] == w1
                for k in range(len(c_words) - 1)
            )
            if not c_pair_found:
                issues.append({"type": "consecutive_repeat", "word": w1, "index": i})
                return True, f"Single-word stutter detected: '{w1} {w2}'", issues

    # 3. Bag-of-Words repetition audit (with tolerance for homophone transcription)
    checked_words = set()
    for w in a_words:
        if w in checked_words or not w.isalpha() or len(w) < 2:
            continue
        checked_words.add(w)
        a_cnt = a_words.count(w)
        c_cnt = c_words.count(w)
        # Content words not in common list: flag if excess >= 2 (allows 1 homophone slip)
        if w not in VN_COMMON_WORDS and c_cnt > 0 and a_cnt >= c_cnt + 2:
            issues.append({"type": "word_repetition", "word": w, "canonical_count": c_cnt, "asr_count": a_cnt})
            return True, f"Word repetition detected: '{w}' appeared {a_cnt} times (expected {c_cnt})", issues
        elif w in VN_COMMON_WORDS and c_cnt > 0 and a_cnt >= c_cnt + 4:
            issues.append({"type": "stopword_excess", "word": w, "canonical_count": c_cnt, "asr_count": a_cnt})
            return True, f"Severe stopword repetition: '{w}' appeared {a_cnt} times (expected {c_cnt})", issues

    return False, "Clean", []


def safe_split_clause(clause: str, max_chars: int = 75) -> List[str]:
    clause = clause.strip()
    if len(clause) <= max_chars:
        return [clause]
    spans = get_compound_spans(clause)
    spaces = [m.start() for m in re.finditer(r"\s+", clause)]
    valid_spaces = [idx for idx in spaces if not is_space_in_compound(idx, spans)]
    if not valid_spaces:
        return [clause]

    valid_splits = [s for s in valid_spaces if s <= max_chars and len(clause) - s >= 5]
    if not valid_splits:
        chosen_idx = valid_spaces[0]
    else:
        conj_splits = []
        for s in valid_splits:
            first_w = clause[s:].strip().split()[0].lower().strip(".,:;!?—")
            if first_w in CONJUNCTIONS or first_w in ["nơi", "cho", "với", "trong", "về", "giúp"]:
                conj_splits.append(s)
        if conj_splits:
            chosen_idx = conj_splits[-1]
        else:
            chosen_idx = max(valid_splits)

    left = clause[:chosen_idx].strip()
    right = clause[chosen_idx:].strip()
    return safe_split_clause(left, max_chars) + safe_split_clause(right, max_chars)


def segment_scene_narration(raw_text: str, max_chars: int = 75) -> List[str]:
    text = re.sub(r"\.{3,}", ", ", raw_text)
    text = re.sub(r"…", ", ", text)
    processed = sense_process_text(text)

    paragraphs = [p.strip() for p in re.split(r"\n\s*\n+", processed) if p.strip()]
    all_clauses = []
    for p in paragraphs:
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", p) if s.strip()]
        for s in sentences:
            parts = [pt.strip() for pt in re.split(r"(?<=[,;:—])\s+", s) if pt.strip()]
            for pt in parts:
                if len(pt) <= max_chars:
                    all_clauses.append(pt)
                else:
                    all_clauses.extend(safe_split_clause(pt, max_chars=max_chars))
    return all_clauses


def parse_blueprint_scenes() -> List[Dict[str, Any]]:
    assert BLUEPRINT_PATH.exists(), f"Blueprint not found at {BLUEPRINT_PATH}"
    content = BLUEPRINT_PATH.read_text(encoding="utf-8")

    parsed_scenes = []
    lines = content.splitlines()
    for line in lines:
        line_s = line.strip()
        if line_s.startswith("| **S1E5_Scene"):
            sc_num = len(parsed_scenes) + 1
            m_col1 = re.match(r"^\|\s*(\*\*S1E5_Scene\d+\*\*.*?)\s*\|", line_s)
            col1 = m_col1.group(1).strip()

            m_col5 = re.search(
                r"\|\s*(\*\*(?:Chuyên gia|Carl|Claude|Shannon|Gauss|Laplace|Nguyễn|Bạn học sinh|Toàn thể).*?)\s*\|\s*$",
                line_s,
            )
            col5_start = m_col5.start()

            m_col4 = re.search(
                r"\|\s*(\*\*\d+:\d+(?:\.\d+)?:\*\*.*?)\s*$", line_s[:col5_start]
            )
            col4_start = m_col4.start()

            middle = line_s[m_col1.end() : col4_start].strip()
            m_split = re.search(
                r"((?:Vùng\s+(?:an\s+toàn\s+)?phụ\s+đề(?:\s+CC)?|\$Y|\bY)\s*(?:∈|\\in)\s*\[-4\.00?,\s*-2\.00?\].*?)\|\s*(.*)$",
                middle,
                re.IGNORECASE | re.DOTALL,
            )
            if not m_split:
                m_split = re.search(
                    r"(\*\*(?:Vùng an toàn phụ đề(?:\s+CC)?|Subtitle CC Safe Zone).*?\*\*.*?)\|\s*(.*)$",
                    middle,
                    re.IGNORECASE | re.DOTALL,
                )
            if not m_split:
                m_split = re.search(
                    r"^(.*?)\|\s*([A-ZÀ-Ỹ][a-zà-ỹ].*)$", middle, re.DOTALL
                )

            col3 = m_split.group(2).strip()
            m_temp = re.search(r"Dynamic Temper:\s*`([0-9.]+)`", col1)
            temper = float(m_temp.group(1)) if m_temp else 0.53

            clean_narr = col3.replace("<br><br>", "\n\n").replace("<br>", " ").strip()
            clauses = segment_scene_narration(clean_narr, max_chars=75)

            for c in clauses:
                assert len(c) <= 75, f"Clause exceeded 75 chars ({len(c)}): {c}"

            parsed_scenes.append({
                "scene_num": sc_num,
                "scene_id": f"S1E5_Scene{sc_num:02d}",
                "temper": temper,
                "raw_narration": clean_narr,
                "clauses": clauses,
                "word_count": len(clean_for_repetition(clean_narr))
            })

    assert len(parsed_scenes) == 8, f"Expected 8 scenes, got {len(parsed_scenes)}"
    return parsed_scenes


def measure_audio_ebur128(wav_path: Path) -> Dict[str, float]:
    cmd = [
        "ffmpeg", "-nostats", "-i", str(wav_path),
        "-filter_complex", "ebur128=peak=true",
        "-f", "null", "-"
    ]
    proc = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.DEVNULL, text=True, check=True)
    stderr = proc.stderr
    i_matches = re.findall(r"I:\s+([-\d\.]+)\s+LUFS", stderr)
    tp_matches = re.findall(r"Peak:\s+([-\d\.]+)\s+dBFS", stderr)
    integrated_lufs = float(i_matches[-1]) if i_matches else -99.0
    true_peak_dbtp = float(tp_matches[-1]) if tp_matches else 0.0

    dur_cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(wav_path)
    ]
    duration = float(subprocess.check_output(dur_cmd).decode().strip())

    return {
        "duration": duration,
        "integrated_lufs": integrated_lufs,
        "true_peak_dbtp": true_peak_dbtp
    }


def main():
    parser = argparse.ArgumentParser(description="S1E5 Audio Synthesis & Mastering")
    parser.add_argument("--scenes", nargs="+", type=int, default=list(range(1, 9)),
                        help="Scene numbers to synthesize (default: 1..8)")
    parser.add_argument("--cadence", type=float, default=1.0,
                        help="Cadence factor (strictly 1.0x native)")
    parser.add_argument("--skip-existing", action="store_true",
                        help="Skip scenes where verified WAV already exists")
    args = parser.parse_args()

    print("=" * 70)
    print("🎙️ S1E5 AUDIO SYNTHESIS & MASTERING — VIENEU V0-SENSE ON CUDA")
    print("Topic: Phân Phối Chuẩn & Định Lý Giới Hạn Trung Tâm — Trật Tự Từ Hỗn Loạn")
    print(f"Reference Voice: {DEFAULT_REF_WAV.name}")
    print(f"Output Directory: {OUTPUT_DIR}")
    print(f"Cadence: {args.cadence:.2f}x (Zen Miền Tây: 135-150 WPM)")
    print("=" * 70)

    preload_cuda_cublas()
    from vieneu import Vieneu
    from faster_whisper import WhisperModel

    print("\n[*] Initializing VieNeu-TTS v3 Turbo engine on CUDA...")
    t0_engine = time.time()
    tts_engine = Vieneu()
    print(f"✓ VieNeu engine initialized in {time.time() - t0_engine:.2f}s")

    print("[*] Initializing Faster-Whisper (small, float16) on CUDA...")
    t0_whisper = time.time()
    whisper_model = WhisperModel("small", device="cuda", compute_type="float16")
    print(f"✓ Faster-Whisper initialized in {time.time() - t0_whisper:.2f}s")

    scenes = parse_blueprint_scenes()
    total_words = sum(s["word_count"] for s in scenes)
    print(f"\n✓ Parsed {len(scenes)} scenes ({total_words} words total)")

    scene_timings = []
    asr_reports = []
    scene_files = []
    t0_all = time.time()

    for sc in scenes:
        sc_num = sc["scene_num"]
        out_wav = OUTPUT_DIR / f"scene_{sc_num:02d}.wav"
        scene_files.append(out_wav)

        if sc_num not in args.scenes:
            if out_wav.exists():
                m = measure_audio_ebur128(out_wav)
                wpm = (sc["word_count"] / m["duration"]) * 60.0 if m["duration"] > 0 else 0
                scene_timings.append({
                    "scene_num": sc_num,
                    "scene_id": sc["scene_id"],
                    "duration": round(m["duration"], 3),
                    "words": sc["word_count"],
                    "wpm": round(wpm, 1),
                    "temper": sc["temper"],
                    "integrated_lufs": m["integrated_lufs"],
                    "true_peak_dbtp": m["true_peak_dbtp"],
                    "wav_file": str(out_wav.relative_to(REPO_ROOT))
                })
            continue

        if args.skip_existing and out_wav.exists():
            holes = audit_audio_silence_holes(out_wav, max_silence_sec=0.35)
            m = measure_audio_ebur128(out_wav)
            if len(holes) == 0 and abs(m["integrated_lufs"] - (-14.5)) <= 0.6:
                print(f"\n[✓] Scene {sc_num:02d} already exists and is fully compliant ({m['duration']:.2f}s, {m['integrated_lufs']:.1f} LUFS, 0 holes). Skipping re-synthesis.")
                wpm = (sc["word_count"] / m["duration"]) * 60.0 if m["duration"] > 0 else 0
                scene_timings.append({
                    "scene_num": sc_num,
                    "scene_id": sc["scene_id"],
                    "duration": round(m["duration"], 3),
                    "words": sc["word_count"],
                    "wpm": round(wpm, 1),
                    "temper": sc["temper"],
                    "integrated_lufs": m["integrated_lufs"],
                    "true_peak_dbtp": m["true_peak_dbtp"],
                    "wav_file": str(out_wav.relative_to(REPO_ROOT))
                })
                continue

        raw_wav = OUTPUT_DIR / f"scene_{sc_num:02d}.raw.wav"
        gated_wav = OUTPUT_DIR / f"scene_{sc_num:02d}.gated.wav"
        tmp_master_wav = OUTPUT_DIR / f"scene_{sc_num:02d}.tmp_master.wav"

        print(f"\n{'='*70}")
        print(f"▶ SYNTHESIZING SCENE {sc_num:02d}: {sc['scene_id']}")
        print(f"  Clauses: {len(sc['clauses'])} (all <= 75 chars) | Words: {sc['word_count']} | Temper: {sc['temper']}")
        print(f"{'='*70}")

        best_audio = None
        best_asr_text = ""
        verification_passed = False
        attempts_used = 0
        word_coverage = 0.0

        canonical_words = set(clean_for_repetition(sc["raw_narration"]))

        for attempt in range(3):
            attempts_used = attempt + 1
            if attempt == 0:
                temper = sc["temper"]
                rep_penalty = 1.15
            elif attempt == 1:
                temper = sc["temper"] - 0.02
                rep_penalty = 1.20
            else:
                temper = sc["temper"] + 0.02
                rep_penalty = 1.25

            print(f"  [Attempt {attempts_used}/3] temper={temper:.2f}, rep_penalty={rep_penalty:.2f}...")
            t_att_start = time.time()

            clause_audios = []
            for c_idx, clause in enumerate(sc["clauses"]):
                c_audio = tts_engine.infer(
                    clause,
                    ref_audio=str(DEFAULT_REF_WAV),
                    denoise=True,
                    temperature=temper,
                    repetition_penalty=rep_penalty,
                    top_k=20,
                    top_p=0.92,
                    max_chars=90
                )
                clause_audios.append(c_audio)
                # ZERO-MECHANICAL-SILENCE-PADDING:
                # Do NOT insert artificial zero silence inside sentences.
                # Only insert a subtle micro-pause (0.08s) at explicit sentence ends (. ! ?) if needed.
                is_sent_end = any(clause.rstrip().endswith(end) for end in [".", "!", "?", "…"])
                if is_sent_end:
                    clause_audios.append(np.zeros(int(0.08 * 48000), dtype=np.float32))

            attempt_audio = np.concatenate(clause_audios)
            sf.write(str(raw_wav), attempt_audio, 48000)
            t_infer = time.time() - t_att_start
            print(f"    -> Inferred {len(sc['clauses'])} clauses in {t_infer:.1f}s")

            # Faster-Whisper ASR audit
            segments, info = whisper_model.transcribe(str(raw_wav), language="vi", beam_size=5)
            seg_list = list(segments)
            asr_text = " ".join(s.text for s in seg_list).strip()
            asr_words = set(clean_for_repetition(asr_text))

            cov = len(canonical_words.intersection(asr_words)) / len(canonical_words) if canonical_words else 1.0
            word_coverage = round(cov * 100.0, 2)

            has_defect, defect_msg, issues = audit_asr_repetition(
                canonical_text=sc["raw_narration"],
                asr_segments=seg_list
            )

            print(f"    -> ASR Transcription: {len(asr_words)} unique words | Coverage: {word_coverage:.1f}%")
            if not has_defect and word_coverage >= 75.0:
                print(f"    ✓ ASR Closed-Loop Verification PASSED (Coverage: {word_coverage}%, 0 repetition)")
                verification_passed = True
                best_audio = attempt_audio
                best_asr_text = asr_text
                break
            else:
                reason = defect_msg if has_defect else f"Low word coverage ({word_coverage}% < 75%)"
                print(f"    [!] ASR Defect on Attempt {attempts_used}: {reason}")
                best_audio = attempt_audio
                best_asr_text = asr_text

        # Smart Silence Gate (compress gaps > 0.28s down to 0.20s for native 1.0x neural pacing)
        gated_data = clean_silence_gaps(
            best_audio,
            sr=48000,
            threshold_rms=0.0008,
            max_gap_s=0.28,
            target_gap_s=0.20,
            safety_pad_s=0.04
        )
        sf.write(str(gated_wav), gated_data, 48000)
        raw_dur = len(best_audio) / 48000
        gated_dur = len(gated_data) / 48000
        saved_silence = raw_dur - gated_dur
        print(f"  ✓ Smart Silence Gate: {raw_dur:.2f}s -> {gated_dur:.2f}s (reclaimed {saved_silence:.2f}s)")

        # 5-Stage Studio Vocal Mastering Chain:
        # Highpass 75Hz, De-mud 300Hz (-1.5dB), Presence 3.4kHz (+1.8dB), Air 8.5kHz (+2.0dB), EBU R128 (-14.5 LUFS, True Peak <= -1.5 dBTP)
        filters = [
            "highpass=f=75",
            "equalizer=f=300:t=q:w=1.2:g=-1.5",
            "equalizer=f=3400:t=q:w=1.0:g=1.8",
            "treble=g=2.0:f=8500:t=s"
        ]

        # ZERO-ATEMPO-SLOWDOWN MANDATE: Strictly forbid atempo < 1.0
        if args.cadence is not None and args.cadence < 0.999:
            print(f"  [!] Zero-Atempo-Slowdown Mandate: atempo={args.cadence} < 1.0 is strictly forbidden and ignored!")
        elif args.cadence is not None and args.cadence > 1.001:
            filters.append(f"atempo={args.cadence:.4f}")
            print(f"  -> Applied cadence filter: atempo={args.cadence:.4f}")

        filters.append("loudnorm=I=-14.5:TP=-1.5:LRA=7.0")
        af_chain = ", ".join(filters)

        master_cmd = [
            "ffmpeg", "-y",
            "-i", str(gated_wav),
            "-af", af_chain,
            "-ar", "48000",
            "-ac", "2",
            "-c:a", "pcm_s24le",
            str(out_wav)
        ]
        subprocess.run(master_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Silence audit on output: if any gap >= 0.35s exists (e.g. at edges), compress and re-loudnorm
        holes = audit_audio_silence_holes(out_wav, max_silence_sec=0.35)
        if len(holes) > 0:
            print(f"  [!] Post-mastering silence clean: found {len(holes)} holes >= 0.35s, compressing...")
            data_m, sr_m = sf.read(str(out_wav))
            cleaned_m = clean_silence_gaps(data_m, sr=sr_m, threshold_rms=0.0008, max_gap_s=0.35, target_gap_s=0.20, safety_pad_s=0.04)
            sf.write(str(tmp_master_wav), cleaned_m, sr_m)
            cmd_re = [
                "ffmpeg", "-y", "-i", str(tmp_master_wav),
                "-af", "loudnorm=I=-14.5:TP=-1.5:LRA=7.0",
                "-ar", "48000", "-ac", "2", "-c:a", "pcm_s24le",
                str(out_wav)
            ]
            subprocess.run(cmd_re, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            tmp_master_wav.unlink(missing_ok=True)
            holes = audit_audio_silence_holes(out_wav, max_silence_sec=0.35)

        # Cleanup intermediate files
        for tmp_f in [raw_wav, gated_wav, tmp_master_wav]:
            if tmp_f.exists():
                tmp_f.unlink()

        # Empirical measurements
        metrics = measure_audio_ebur128(out_wav)
        lufs_diff = -14.5 - metrics["integrated_lufs"]
        if abs(lufs_diff) > 0.3:
            tmp_cal = out_wav.parent / f"temp_cal_{sc_num}.wav"
            cmd_cal = [
                "ffmpeg", "-y", "-v", "warning",
                "-i", str(out_wav),
                "-af", f"volume={lufs_diff:+.2f}dB",
                "-ar", "48000",
                "-ac", "2",
                "-c:a", "pcm_s24le",
                str(tmp_cal)
            ]
            subprocess.run(cmd_cal, check=True)
            tmp_cal.replace(out_wav)
            metrics = measure_audio_ebur128(out_wav)

        measured_wpm = (sc["word_count"] / metrics["duration"]) * 60.0 if metrics["duration"] > 0 else 0

        print(f"  ✓ FINALIZED SCENE {sc_num:02d}:")
        print(f"    - Duration: {metrics['duration']:.2f}s")
        print(f"    - Integrated Loudness: {metrics['integrated_lufs']:.1f} LUFS (Target: -14.5 ± 0.5)")
        print(f"    - True Peak: {metrics['true_peak_dbtp']:.2f} dBTP (Target: <= -1.5 dBTP)")
        print(f"    - Cadence: {measured_wpm:.1f} WPM")
        print(f"    - Silence Holes >= 0.35s: {len(holes)}")
        print(f"    - ASR Word Coverage: {word_coverage}% (Clean: {verification_passed})")

        # Assert acoustic invariants
        assert abs(metrics["integrated_lufs"] - (-14.5)) <= 0.8, (
            f"Scene {sc_num}: Integrated LUFS {metrics['integrated_lufs']} outside [-15.3, -13.7]"
        )
        assert metrics["true_peak_dbtp"] <= -1.4, (
            f"Scene {sc_num}: True Peak {metrics['true_peak_dbtp']} exceeds -1.5 dBTP target"
        )
        assert len(holes) == 0, (
            f"Scene {sc_num}: Found {len(holes)} silence holes >= 0.35s!"
        )

        timing_entry = {
            "scene_num": sc_num,
            "scene_id": sc["scene_id"],
            "duration": round(metrics["duration"], 3),
            "words": sc["word_count"],
            "wpm": round(measured_wpm, 1),
            "temper": sc["temper"],
            "integrated_lufs": metrics["integrated_lufs"],
            "true_peak_dbtp": metrics["true_peak_dbtp"],
            "wav_file": str(out_wav.relative_to(REPO_ROOT))
        }
        scene_timings.append(timing_entry)

        asr_reports.append({
            "scene_num": sc_num,
            "scene_id": sc["scene_id"],
            "word_coverage_pct": word_coverage,
            "attempts_used": attempts_used,
            "verified_clean": verification_passed,
            "silence_holes_count": len(holes),
            "asr_transcript": best_asr_text
        })

    # Save timings and ASR reports
    timings_json = OUTPUT_DIR / "scene_timings.json"
    with open(timings_json, "w", encoding="utf-8") as f:
        json.dump(scene_timings, f, indent=2, ensure_ascii=False)
    print(f"\n✓ Saved scene timings to {timings_json}")

    asr_json = OUTPUT_DIR / "asr_verification_report.json"
    with open(asr_json, "w", encoding="utf-8") as f:
        json.dump(asr_reports, f, indent=2, ensure_ascii=False)
    print(f"✓ Saved ASR verification report to {asr_json}")

    # Concatenate master audio if all scenes 1..8 exist
    all_scenes_for_concat = [OUTPUT_DIR / f"scene_{i:02d}.wav" for i in range(1, 9)]
    all_exist = all(sf_p.exists() for sf_p in all_scenes_for_concat)

    if all_exist:
        print("\n[*] Assembling Master Audio: master_audio_series_01_tap_05.wav...")
        master_wav = OUTPUT_DIR / "master_audio_series_01_tap_05.wav"
        concat_list = OUTPUT_DIR / "concat_list.txt"

        with open(concat_list, "w", encoding="utf-8") as f:
            for sf_path in all_scenes_for_concat:
                f.write(f"file '{sf_path.resolve()}'\n")

        concat_cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_list),
            "-c:a", "pcm_s24le",
            "-ar", "48000",
            str(master_wav)
        ]
        subprocess.run(concat_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        concat_list.unlink(missing_ok=True)

        master_metrics = measure_audio_ebur128(master_wav)
        master_holes = audit_audio_silence_holes(master_wav, max_silence_sec=0.35)
        total_dur = master_metrics["duration"]
        mins = int(total_dur // 60)
        secs = total_dur % 60

        print(f"\n{'='*70}")
        print(f"🎉 MASTER AUDIO S1E5 COMPLETE:")
        print(f"   - File: {master_wav}")
        print(f"   - Total Duration: {total_dur:.2f}s ({mins:02d}:{secs:05.2f})")
        print(f"   - Integrated Loudness: {master_metrics['integrated_lufs']:.1f} LUFS (Target: -14.5 ± 0.5)")
        print(f"   - True Peak: {master_metrics['true_peak_dbtp']:.2f} dBTP (Target: <= -1.5 dBTP)")
        print(f"   - Silence Holes >= 0.35s: {len(master_holes)}")
        print(f"   - Total Wall Clock Time: {time.time() - t0_all:.1f}s")
        print(f"{'='*70}\n")
    else:
        print(f"\n[i] Partial run completed. Missing scenes for full master: {[p.name for p in all_scenes_for_concat if not p.exists()]}")


if __name__ == "__main__":
    main()
