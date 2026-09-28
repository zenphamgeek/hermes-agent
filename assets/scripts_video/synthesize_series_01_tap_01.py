#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
synthesize_series_01_tap_01.py
==============================
Synthesizes all 8 scenes for Series 1 Episode 1 (S1E1) from
assets/scripts_video/s1_e1_masterclass_blueprint.md using TTS V0-Sense on CUDA.

Produces:
- assets/scripts_video/audio/series_01/tap_01/scene_01.wav .. scene_08.wav
- assets/scripts_video/audio/series_01/tap_01/master_audio_series_01_tap_01.wav
- assets/scripts_video/audio/series_01/tap_01/scene_timings.json
"""

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Ensure vieneu package importable
VIENEU_SRC = REPO_ROOT / "vieneu_tts_test" / "src"
if str(VIENEU_SRC) not in sys.path:
    sys.path.insert(0, str(VIENEU_SRC))

from assets.scripts_video.tts_v0_sense_synthesizer import TtsV0SenseEngine, DEFAULT_REF_WAV

BLUEPRINT_PATH = REPO_ROOT / "assets" / "scripts_video" / "s1_e1_masterclass_blueprint.md"
OUTPUT_DIR = REPO_ROOT / "assets" / "scripts_video" / "audio" / "series_01" / "tap_01"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

NARR_STARTS = [
    "Một cú búng tay", "Năm 1814", "Mùa hè năm 1948",
    "Khi đối diện", "Giờ đây", "Ở cấp độ", "Nhưng quy luật", "Nhìn thấu qua"
]

def parse_blueprint_scenes():
    assert BLUEPRINT_PATH.exists(), f"Blueprint not found at {BLUEPRINT_PATH}"
    content = BLUEPRINT_PATH.read_text(encoding="utf-8")
    
    parsed = []
    lines = content.splitlines()
    for line in lines:
        line_s = line.strip()
        if line_s.startswith("| **S1E1_Scene"):
            sc_num = len(parsed) + 1
            p1 = line_s.find("|")
            p2 = line_s.find("|", p1 + 1)
            col1 = line_s[p1+1:p2].strip()

            ns = NARR_STARTS[sc_num - 1]
            ns_pos = line_s.find(ns)
            assert ns_pos != -1, f"Narration start '{ns}' not found in scene {sc_num}"
            
            m_audio = re.search(r"\|\s*(\*\*\d+:\d+(?:\.\d+)?:\*\*.*?)\|", line_s[ns_pos:])
            assert m_audio, f"Audio start marker not found in scene {sc_num}"
            audio_rel_pos = ns_pos + m_audio.start()
            col3 = line_s[ns_pos:audio_rel_pos].strip()

            # Dynamic Temper
            m_temp = re.search(r"Dynamic Temper:\s*`([0-9.]+)`", col1)
            temper = float(m_temp.group(1)) if m_temp else (0.58 if sc_num == 1 else 0.54)

            # Clean HTML tags
            clean_narr = col3.replace("<br><br>", "\n\n").replace("<br>", " ").strip()
            
            parsed.append({
                "scene_num": sc_num,
                "scene_id": f"S1E1_Scene{sc_num:02d}",
                "temper": temper,
                "narration": clean_narr,
                "word_count": len(clean_narr.split())
            })

    assert len(parsed) == 8, f"Expected 8 scenes, got {len(parsed)}"
    return parsed

def main():
    print("=" * 70)
    print("TTS V0-SENSE PRODUCTION — SERIES 1 EPISODE 1 (S1E1)")
    print(f"Reference Voice: {DEFAULT_REF_WAV.name}")
    print(f"Output Directory: {OUTPUT_DIR}")
    print("=" * 70)

    scenes = parse_blueprint_scenes()
    total_words = sum(s["word_count"] for s in scenes)
    print(f"✓ Parsed {len(scenes)} scenes ({total_words} words total)\n")

    engine = TtsV0SenseEngine(ref_wav=DEFAULT_REF_WAV, device="cuda")

    scene_timings = []
    scene_files = []

    for sc in scenes:
        sc_num = sc["scene_num"]
        out_wav = OUTPUT_DIR / f"scene_{sc_num:02d}.wav"
        scene_files.append(out_wav)

        print(f"\n--- Scene {sc_num:02d}: {sc['scene_id']} ({sc['word_count']} words, temper={sc['temper']}) ---")
        res = engine.synthesize(
            raw_text=sc["narration"],
            output_wav=out_wav,
            temper=sc["temper"],
            scene_index=sc_num,
            target_lufs=-14.5,
            target_tp=-1.5
        )

        wpm = (sc["word_count"] / res["duration"]) * 60.0 if res["duration"] > 0 else 0
        scene_timings.append({
            "scene_num": sc_num,
            "scene_id": sc["scene_id"],
            "duration": round(res["duration"], 3),
            "words": sc["word_count"],
            "wpm": round(wpm, 1),
            "temper": sc["temper"],
            "wav_file": str(out_wav.relative_to(REPO_ROOT))
        })

    # Save timing manifest
    timings_json = OUTPUT_DIR / "scene_timings.json"
    with open(timings_json, "w", encoding="utf-8") as f:
        json.dump(scene_timings, f, indent=2, ensure_ascii=False)
    print(f"\n✓ Saved scene timings to {timings_json}")

    # Concatenate master audio
    print("\n[*] Assembling full master audio file...")
    master_wav = OUTPUT_DIR / "master_audio_series_01_tap_01.wav"
    concat_list = OUTPUT_DIR / "concat_list.txt"
    with open(concat_list, "w", encoding="utf-8") as f:
        for sf in scene_files:
            f.write(f"file '{sf.resolve()}'\n")

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

    # Master audit
    probe_cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "json", str(master_wav)
    ]
    meta = json.loads(subprocess.check_output(probe_cmd).decode())
    total_dur = float(meta["format"]["duration"])
    mins = int(total_dur // 60)
    secs = int(total_dur % 60)

    # EBU R128 Loudness Audit
    ebur_cmd = [
        "ffmpeg", "-i", str(master_wav),
        "-af", "ebur128=framelog=verbose",
        "-f", "null", "-"
    ]
    ebur_out = subprocess.run(ebur_cmd, capture_output=True, text=True).stderr
    
    i_lufs = re.search(r"I:\s*(-?[\d.]+)\s*LUFS", ebur_out)
    tp_db = re.search(r"Peak:\s*(-?[\d.]+)\s*dBFS", ebur_out)
    
    lufs_val = i_lufs.group(1) if i_lufs else "N/A"
    tp_val = tp_db.group(1) if tp_db else "N/A"

    print("\n" + "=" * 70)
    print("MASTER AUDIO SYNTHESIS COMPLETE!")
    print(f"Master File: {master_wav}")
    print(f"Total Duration: {mins}m {secs:02d}s ({total_dur:.2f}s)")
    print(f"EBU R128 Integrated Loudness: {lufs_val} LUFS (Target: -14.5 LUFS)")
    print(f"True Peak: {tp_val} dBFS (Target: <= -1.5 dBTP)")
    print("=" * 70)

if __name__ == "__main__":
    main()
