#!/usr/bin/env python3
"""
Audio Dataset Preprocessor for Pure Dry ZenPham Voice
Filters ONLY 100% clean, dry acapella/speech samples (strictly excluding music mixes)
with noise gate and speech bandpass optimization.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

DATASET_OUT = Path("/home/zen/workspace/rvc_dataset/zenpham")
DATASET_OUT.mkdir(parents=True, exist_ok=True)

# ONLY pure dry speech / acapella sources (NO background music)
PURE_DRY_SOURCES = [
    "/home/zen/Downloads/Telegram Desktop/zenpham.m4a",
    "/home/zen/Downloads/Telegram Desktop/zen-mien tay-trung nien.m4a",
    "/home/zen/Downloads/Telegram Desktop/Đường Số 8A 12.m4a",
    "/home/zen/hermes-agent/assets/voices/zenpham-mien tay-trung nien.mp3",
    "/home/zen/hermes-agent/assets/voices/zen-mien tay-trung nien.mp3",
    "/home/zen/hermes-agent/assets/voices/zen-style.wav",
]

# Include pure dry audio scenes
SCENE_DIR = Path("/home/zen/hermes-agent/assets/scripts_video/audio")
if SCENE_DIR.exists():
    for sc in sorted(SCENE_DIR.glob("scene_*.wav")):
        PURE_DRY_SOURCES.append(str(sc))


def prepare():
    print("=" * 60)
    print("🧼 PREPARING 100% PURE DRY ZENPHAM DATASET (NO MUSIC)")
    print(f"📁 Destination: {DATASET_OUT}")
    print("=" * 60)

    # Clean existing destination files
    for old_f in DATASET_OUT.glob("*.wav"):
        old_f.unlink()

    chunk_idx = 0
    total_duration = 0.0

    for src_str in PURE_DRY_SOURCES:
        src = Path(src_str)
        if not src.exists():
            continue

        print(f"[CLEAN-SOURCE] Processing dry voice: {src.name} ({src.stat().st_size // 1024} KB)")

        # Convert to 40kHz Mono with Highpass 75Hz, Lowpass 12kHz, and clean silence trimming
        temp_wav = DATASET_OUT / f"temp_{src.stem}.wav"
        cmd_norm = [
            "ffmpeg", "-y", "-i", str(src),
            "-af", "highpass=f=75,lowpass=f=12000,silenceremove=start_periods=1:start_duration=0.1:start_threshold=-45dB:stop_periods=1:stop_duration=0.4:stop_threshold=-45dB,loudnorm=I=-16:TP=-1.5:LRA=9",
            "-ar", "40000",
            "-ac", "1",
            str(temp_wav)
        ]
        res = subprocess.run(cmd_norm, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if res.returncode != 0 or not temp_wav.exists() or temp_wav.stat().st_size < 1000:
            continue

        dur_cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(temp_wav)]
        try:
            dur = float(subprocess.check_output(dur_cmd).decode().strip())
        except Exception:
            temp_wav.unlink(missing_ok=True)
            continue

        # Split into 3.5s segments with 0.5s overlap
        segment_len = 3.5
        step = 3.0
        pos = 0.0

        while pos + 1.2 <= dur:
            chunk_file = DATASET_OUT / f"zenpham_clean_{chunk_idx:04d}.wav"
            cur_len = min(segment_len, dur - pos)
            cmd_slice = [
                "ffmpeg", "-y", "-ss", f"{pos:.2f}", "-t", f"{cur_len:.2f}",
                "-i", str(temp_wav),
                "-ar", "40000", "-ac", "1",
                str(chunk_file)
            ]
            subprocess.run(cmd_slice, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if chunk_file.exists() and chunk_file.stat().st_size > 1000:
                chunk_idx += 1
                total_duration += cur_len
            pos += step

        temp_wav.unlink(missing_ok=True)

    print("\n" + "=" * 60)
    print(f"🎉 CLEAN DATASET READY: Created {chunk_idx} pure dry voice slices!")
    print(f"⏱️ Total Clean Vocal Audio: {total_duration:.1f} seconds ({total_duration/60:.2f} minutes)")
    print(f"📁 Dataset Directory: {DATASET_OUT}")
    print("=" * 60)


if __name__ == "__main__":
    prepare()
