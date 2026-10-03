#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/empirical_shorts_stress_test.py
=======================================
Empirical Stress-Test & Forensic Quality Audit Harness for Milestone 3 YouTube Shorts:
- 10 Shorts across Tap 02 (S1E2) and Tap 03 (S1E3)
- Measures exact physical waveforms, loudness, timestamps, visual constraints, and subtitles.
"""

import json
import os
import re
import subprocess
import sys
import wave
from pathlib import Path
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = REPO_ROOT / "output" / "series_01_shorts"

BROKEN_COMPOUND_PAIRS = [
    ("ngẫu", "nhiên"),
    ("xác", "suất"),
    ("tất", "định"),
    ("bất", "định"),
    ("trí", "tuệ"),
    ("nhân", "tạo"),
    ("Claude", "Shannon"),
    ("Quỷ", "Laplace"),
    ("Thomas", "Bayes"),
    ("Isaac", "Newton"),
    ("John", "Rupert"),
    ("Rupert", "Firth"),
    ("Gradient", "Descent"),
    ("Gradient", "Clipping"),
    ("Polyak", "Momentum"),
    ("Saddle", "Point"),
    ("Condition", "Number"),
    ("véc", "tơ"),
    ("thuật", "toán"),
]

def get_audio_info(wav_path: Path):
    with wave.open(str(wav_path), "rb") as w:
        nchannels = w.getnchannels()
        sampwidth = w.getsampwidth()
        framerate = w.getframerate()
        nframes = w.getnframes()
        duration = nframes / framerate
        raw_bytes = w.readframes(nframes)
        if sampwidth == 2:
            data = np.frombuffer(raw_bytes, dtype=np.int16).astype(np.float32) / 32768.0
        elif sampwidth == 4:
            data = np.frombuffer(raw_bytes, dtype=np.int32).astype(np.float32) / 2147483648.0
        else:
            data = np.frombuffer(raw_bytes, dtype=np.uint8).astype(np.float32) / 128.0 - 1.0
        if nchannels > 1:
            data = data.reshape(-1, nchannels).mean(axis=1)
    return {
        "channels": nchannels,
        "sampwidth": sampwidth,
        "framerate": framerate,
        "nframes": nframes,
        "duration": duration,
        "samples": data
    }

def detect_speech_boundaries(samples: np.ndarray, sr: int = 48000, frame_s: float = 0.02, threshold: float = 0.008):
    frame_len = int(frame_s * sr)
    n_frames = len(samples) // frame_len
    energies = [np.sqrt(np.mean(samples[i*frame_len : (i+1)*frame_len]**2)) for i in range(n_frames)]
    energies = np.array(energies)

    active_indices = np.where(energies > threshold)[0]
    if len(active_indices) == 0:
        return 0.0, 0.0, []

    start_sec = active_indices[0] * frame_s
    end_sec = (active_indices[-1] + 1) * frame_s

    # Find internal silence gaps between start and end
    # Speech silence gap: where energy drops below threshold for consecutive frames
    internal_energies = energies[active_indices[0] : active_indices[-1] + 1]
    is_silent = internal_energies < threshold

    gaps = []
    cur_gap_len = 0
    cur_gap_start = 0
    for idx, sil in enumerate(is_silent):
        if sil:
            if cur_gap_len == 0:
                cur_gap_start = (active_indices[0] + idx) * frame_s
            cur_gap_len += 1
        else:
            if cur_gap_len > 0:
                gap_dur = cur_gap_len * frame_s
                if gap_dur >= 0.35:
                    gaps.append((cur_gap_start, cur_gap_start + gap_dur, gap_dur))
                cur_gap_len = 0
    if cur_gap_len > 0:
        gap_dur = cur_gap_len * frame_s
        if gap_dur >= 0.35:
            gaps.append((cur_gap_start, cur_gap_start + gap_dur, gap_dur))

    return start_sec, end_sec, gaps

def detect_dead_silence_holes(samples: np.ndarray, sr: int = 48000, frame_s: float = 0.02, threshold: float = 0.0008):
    frame_len = int(frame_s * sr)
    n_frames = len(samples) // frame_len
    energies = [np.sqrt(np.mean(samples[i*frame_len : (i+1)*frame_len]**2)) for i in range(n_frames)]
    energies = np.array(energies)
    is_silent = energies < threshold

    gaps = []
    cur_gap_len = 0
    cur_gap_start = 0
    for idx, sil in enumerate(is_silent):
        if sil:
            if cur_gap_len == 0:
                cur_gap_start = idx * frame_s
            cur_gap_len += 1
        else:
            if cur_gap_len > 0:
                gap_dur = cur_gap_len * frame_s
                if gap_dur >= 0.35:
                    gaps.append((cur_gap_start, cur_gap_start + gap_dur, gap_dur))
                cur_gap_len = 0
    if cur_gap_len > 0:
        gap_dur = cur_gap_len * frame_s
        if gap_dur >= 0.35:
            gaps.append((cur_gap_start, cur_gap_start + gap_dur, gap_dur))

    init_frames = int(0.40 / frame_s)
    initial_muted = all(is_silent[:init_frames])

    trail_frames = int(0.50 / frame_s)
    trailing_muted = all(is_silent[-trail_frames:])

    return initial_muted, trailing_muted, gaps

def measure_ebur128(file_path: Path):
    cmd = [
        "ffmpeg", "-nostats", "-i", str(file_path),
        "-filter_complex", "ebur128=peak=true",
        "-f", "null", "-"
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    out = res.stderr

    i_lufs = None
    tp_dbtp = None
    lra = None

    m_i = re.search(r"Integrated loudness:\s+I:\s+([-\d\.]+)\s+LUFS", out)
    if m_i:
        i_lufs = float(m_i.group(1))

    m_tp = re.search(r"True peak:\s+Peak:\s+([-\d\.]+)\s+dBFS", out)
    if m_tp:
        tp_dbtp = float(m_tp.group(1))

    m_lra = re.search(r"Loudness range:\s+LRA:\s+([-\d\.]+)\s+LU", out)
    if m_lra:
        lra = float(m_lra.group(1))

    return i_lufs, tp_dbtp, lra

def parse_srt(srt_text: str):
    entries = []
    blocks = re.split(r"\n\s*\n", srt_text.strip())
    for block in blocks:
        lines = [line.strip() for line in block.split("\n") if line.strip()]
        if len(lines) >= 3:
            cue_num = lines[0]
            time_match = re.match(r"(\d{2}:\d{2}:\d{2}[,\.]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[,\.]\d{3})", lines[1])
            if time_match:
                start_str, end_str = time_match.groups()
                def to_sec(ts: str) -> float:
                    ts = ts.replace(",", ".")
                    h, m, s = ts.split(":")
                    return int(h) * 3600 + int(m) * 60 + float(s)

                start_sec = to_sec(start_str)
                end_sec = to_sec(end_str)
                text = " ".join(lines[2:])
                entries.append({
                    "num": int(cue_num),
                    "start": start_sec,
                    "end": end_sec,
                    "duration": end_sec - start_sec,
                    "text": text,
                    "lines_count": len(lines) - 2
                })
    return entries

def audit_subtitles(srt_path: Path):
    if not srt_path.exists():
        return False, ["SRT file does not exist"], {}
    text = srt_path.read_text(encoding="utf-8")
    cues = parse_srt(text)
    if not cues:
        return False, ["No cues parsed from SRT"], {}

    issues = []
    max_chars = 0
    max_words = 0
    min_words = 999
    max_dur = 0.0
    min_dur = 999.0

    for i, c in enumerate(cues):
        t = c["text"]
        w = len(t.split())
        chars = len(t)
        d = c["duration"]

        if chars > max_chars: max_chars = chars
        if w > max_words: max_words = w
        if w < min_words: min_words = w
        if d > max_dur: max_dur = d
        if d < min_dur: min_dur = d

        # Check max characters (hard limit 34 or 35)
        if chars > 35:
            issues.append(f"Cue #{c['num']} exceeds 35 chars ({chars} chars): '{t}'")
        # Check words (target 3-5, hard limit 2-6)
        if w < 2 or w > 6:
            issues.append(f"Cue #{c['num']} word count outside 2-6 ({w} words): '{t}'")
        # Check duration
        if d < 0.6 or d > 2.8:
            issues.append(f"Cue #{c['num']} duration abnormal ({d:.2f}s): '{t}'")
        # Check dangling hyphen
        if " - " in t:
            issues.append(f"Cue #{c['num']} contains dangling hyphen: '{t}'")
        # Check broken compounds with next cue
        if i < len(cues) - 1:
            c1_clean = re.sub(r"[^\w\s]", "", t)
            c2_clean = re.sub(r"[^\w\s]", "", cues[i+1]["text"])
            for w1, w2 in BROKEN_COMPOUND_PAIRS:
                if c1_clean.endswith(w1) and c2_clean.startswith(w2):
                    issues.append(f"Cue #{c['num']} -> #{cues[i+1]['num']} breaks compound '{w1} {w2}'")

    stats = {
        "total_cues": len(cues),
        "max_chars": max_chars,
        "min_words": min_words,
        "max_words": max_words,
        "min_duration": round(min_dur, 2),
        "max_duration": round(max_dur, 2),
    }
    return len(issues) == 0, issues, stats

def probe_video(video_path: Path):
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height,r_frame_rate,duration,nb_frames",
        "-show_entries", "format=duration,size",
        "-of", "json",
        str(video_path)
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        return None
    data = json.loads(res.stdout)
    stream = data["streams"][0]
    fmt = data["format"]
    r_fps = eval(stream["r_frame_rate"]) if "/" in stream.get("r_frame_rate", "") else float(stream.get("r_frame_rate", 0))
    return {
        "width": int(stream.get("width", 0)),
        "height": int(stream.get("height", 0)),
        "fps": r_fps,
        "duration": float(fmt.get("duration", 0)),
        "size_bytes": int(fmt.get("size", 0))
    }

def audit_scene_py(scene_py_path: Path):
    if not scene_py_path.exists():
        return False, ["scene_short.py does not exist"]
    code = scene_py_path.read_text(encoding="utf-8")
    violations = []

    # Rule 29 Card Box Check
    forbidden_tokens = ["COLOR_CARD_BG", "RoundedRectangle", "card_bg", "card_box"]
    for tok in forbidden_tokens:
        if tok in code:
            violations.append(f"Rule 29 violation: found '{tok}' in scene code")

    # Safe Zones Check
    # Look for coordinates in body
    if "X > 3.1" in code or "Y < -6.2" in code:
        violations.append("Contains out-of-safe-zone coordinate references")

    # Check 3-Zone structure
    if "ZONE 1" not in code:
        violations.append("Missing ZONE 1 comment/structure")
    if "ZONE 2" not in code:
        violations.append("Missing ZONE 2 comment/structure")
    if "ZONE 3" not in code:
        violations.append("Missing ZONE 3 comment/structure")

    # Check safe_text / typography
    if "floating_kinetic_header" not in code:
        violations.append("Missing floating_kinetic_header")
    if "floating_nlp_cta" not in code:
        violations.append("Missing floating_nlp_cta")

    return len(violations) == 0, violations

def main():
    print("=" * 100)
    print("EMPIRICAL STRESS-TEST & AUDIT HARNESS FOR ALL 10 YOUTUBE SHORTS (MILESTONE 3)")
    print("=" * 100)

    all_results = []
    short_dirs = []
    for ep in [2, 3]:
        for idx in range(1, 6):
            short_dirs.append((ep, idx, OUTPUT_ROOT / f"tap_{ep:02d}" / f"short_{idx:02d}"))

    summary_table = []

    for ep, idx, sdir in short_dirs:
        short_id = f"S1E{ep:02d}_Short_{idx:02d}"
        print(f"\n[{short_id}] Auditing folder: {sdir.relative_to(REPO_ROOT)}")

        # 1. Packaging & file existence
        files_check = {
            "script.md": (sdir / "script.md").exists(),
            "scene_short.py": (sdir / "scene_short.py").exists(),
            "short_master_2k60.mp4": (sdir / "short_master_2k60.mp4").exists(),
            "metadata_seo.json": (sdir / "metadata_seo.json").exists(),
            "thumbnail_9x16.jpg": (sdir / "thumbnail_9x16.jpg").exists(),
            "short_subtitles.srt": (sdir / "short_subtitles.srt").exists(),
            "audio_master.wav": (sdir / "audio_master.wav").exists(),
            "audio_speech_clean.wav": (sdir / "audio_speech_clean.wav").exists(),
        }
        all_files_ok = all(files_check.values())

        # 2. Video checks
        v_info = probe_video(sdir / "short_master_2k60.mp4")

        # 3. Audio Speech Clean checks
        speech_info = get_audio_info(sdir / "audio_speech_clean.wav")
        speech_start, speech_end, speech_gaps = detect_speech_boundaries(speech_info["samples"], speech_info["framerate"])

        # In master video audio, speech is padded by 0.25s
        actual_speech_start_in_master = 0.25 + speech_start
        actual_speech_end_in_master = 0.25 + speech_end
        trailing_speech_gap_in_master = 50.0 - actual_speech_end_in_master

        # 4. Audio Master checks (lo-fi ambient + loudnorm)
        master_info = get_audio_info(sdir / "audio_master.wav")
        init_muted, trail_muted, master_dead_holes = detect_dead_silence_holes(master_info["samples"], master_info["framerate"])

        # 5. EBU R128 Loudness
        i_lufs, tp_dbtp, lra = measure_ebur128(sdir / "audio_master.wav")
        v_i_lufs, v_tp_dbtp, v_lra = measure_ebur128(sdir / "short_master_2k60.mp4")

        # 6. Scene Python audit (Safe Zones & Rule 29)
        scene_ok, scene_violations = audit_scene_py(sdir / "scene_short.py")

        # 7. Subtitles audit
        srt_ok, srt_violations, srt_stats = audit_subtitles(sdir / "short_subtitles.srt")

        # 8. SEO Metadata audit
        meta_ok = False
        meta_data = {}
        if (sdir / "metadata_seo.json").exists():
            try:
                meta_data = json.loads((sdir / "metadata_seo.json").read_text(encoding="utf-8"))
                meta_ok = len(meta_data.get("title", "")) < 70 and bool(meta_data.get("related_video_id") or meta_data.get("related_video_title"))
            except Exception:
                meta_ok = False

        res_record = {
            "short_id": short_id,
            "all_files_ok": all_files_ok,
            "video_duration": v_info["duration"] if v_info else None,
            "video_resolution": f"{v_info['width']}x{v_info['height']}@{v_info['fps']}fps" if v_info else None,
            "video_size_mb": round(v_info["size_bytes"] / 1024 / 1024, 2) if v_info else None,
            "speech_start_s": round(actual_speech_start_in_master, 3),
            "speech_end_s": round(actual_speech_end_in_master, 3),
            "trailing_silence_s": round(trailing_speech_gap_in_master, 3),
            "speech_internal_gaps_ge_350ms": len(speech_gaps),
            "speech_gaps_details": speech_gaps,
            "master_init_muted_400ms": init_muted,
            "master_trail_muted_500ms": trail_muted,
            "master_dead_holes_ge_350ms": len(master_dead_holes),
            "master_i_lufs": i_lufs,
            "master_tp_dbtp": tp_dbtp,
            "video_i_lufs": v_i_lufs,
            "video_tp_dbtp": v_tp_dbtp,
            "scene_rule_29_ok": scene_ok,
            "scene_violations": scene_violations,
            "srt_ok": srt_ok,
            "srt_violations_count": len(srt_violations),
            "srt_violations": srt_violations,
            "srt_stats": srt_stats,
            "meta_ok": meta_ok,
            "meta_title": meta_data.get("title"),
        }
        all_results.append(res_record)

        print(f"  - Video: {res_record['video_resolution']}, {res_record['video_duration']}s, {res_record['video_size_mb']}MB")
        print(f"  - Speech Active: start={res_record['speech_start_s']}s, end={res_record['speech_end_s']}s, trailing={res_record['trailing_silence_s']}s")
        print(f"  - Speech Silence Holes >=0.35s: {res_record['speech_internal_gaps_ge_350ms']}")
        print(f"  - Master Dead Silence Holes >=0.35s: {res_record['master_dead_holes_ge_350ms']}")
        print(f"  - EBU R128 Master: I={i_lufs} LUFS, TP={tp_dbtp} dBTP | Video: I={v_i_lufs} LUFS, TP={v_tp_dbtp} dBTP")
        print(f"  - Scene Code Rule 29 & Safe Zones: {'PASS' if scene_ok else 'FAIL: ' + str(scene_violations)}")
        print(f"  - Subtitles Gold SRT: {'PASS' if srt_ok else 'FAIL: ' + str(srt_violations[:2])}")
        print(f"  - SEO Metadata: {'PASS' if meta_ok else 'FAIL'} (Title: '{meta_data.get('title')}')")

    # Output JSON summary
    summary_path = REPO_ROOT / "output" / "series_01_shorts" / "SHORTS_EMPIRICAL_AUDIT_REPORT.json"
    summary_path.write_text(json.dumps(all_results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n✓ Saved full empirical audit JSON report to: {summary_path.relative_to(REPO_ROOT)}")

if __name__ == "__main__":
    main()
