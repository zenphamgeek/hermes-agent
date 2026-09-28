#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
assemble_master_video_ep03.py
Assemble 2K QHD (2560x1440 @ 60fps) master video for ZenPham Series 2 Episode 03:
1. Matches each of the 6 audio scenes with its corresponding 2K Manim animation.
2. Applies FFmpeg tpad=stop_mode=clone to synchronize scene video duration with scene audio duration.
3. Concatenates video track and multiplexes with 5-stage mastered audio.
4. Outputs to assets/scripts_video/output/youtube_staging/series_02/tap_03/master_2k.mp4.
"""

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path("/home/zen/hermes-agent")
SCRIPTS_VIDEO_DIR = REPO_ROOT / "assets" / "scripts_video"
AUDIO_DIR = SCRIPTS_VIDEO_DIR / "audio" / "series_02" / "tap_03"
MANIM_MEDIA_DIR = SCRIPTS_VIDEO_DIR / "output" / "manim_media" / "series_02" / "tap_03" / "videos" / "manim_s2_tap_03_yarn" / "1440p60"
STAGING_DIR = SCRIPTS_VIDEO_DIR / "output" / "youtube_staging" / "series_02" / "tap_03"
CLIPS_DIR = STAGING_DIR / "scene_clips"

SCENE_MANIM_MAP = {
    1: "Tap03Scene01ColdOpen",
    2: "Tap03Scene02Architecture",
    3: "Tap03Scene03Mathematics",
    4: "Tap03Scene04Telemetry",
    5: "Tap03Scene05LabExperiment",
    6: "Tap03Scene06Outro",
}

def get_duration(p: Path) -> float:
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(p)
    ]
    return float(subprocess.check_output(cmd, text=True).strip())

def main():
    STAGING_DIR.mkdir(parents=True, exist_ok=True)
    CLIPS_DIR.mkdir(parents=True, exist_ok=True)

    master_audio = AUDIO_DIR / "master_audio_series_02_tap_03.wav"
    if not master_audio.exists():
        print(f"❌ Master audio missing: {master_audio}")
        sys.exit(1)

    audio_total_dur = get_duration(master_audio)
    print(f"[*] Master Audio Duration: {audio_total_dur:.2f}s ({audio_total_dur/60:.2f} min)")

    scene_audio_durs = {}
    for idx in range(1, 7):
        w = AUDIO_DIR / f"scene_{idx:02d}.wav"
        if not w.exists():
            print(f"❌ Missing scene audio: {w}")
            sys.exit(1)
        dur = get_duration(w)
        scene_audio_durs[idx] = dur
        print(f"   Scene {idx:02d} Audio: {dur:.2f}s")

    # Assemble 6 scene video clips with tpad sync
    clip_paths = []
    print("\n[*] Assembling 6 Scene Video Clips with tpad Synchronization...")
    for idx in range(1, 7):
        scene_name = SCENE_MANIM_MAP[idx]
        manim_mp4 = MANIM_MEDIA_DIR / f"{scene_name}.mp4"
        if not manim_mp4.exists():
            print(f"❌ Missing rendered scene mp4: {manim_mp4}")
            sys.exit(1)

        manim_dur = get_duration(manim_mp4)
        target_dur = scene_audio_durs[idx]
        pad_dur = max(0.0, target_dur - manim_dur)

        out_clip = CLIPS_DIR / f"clip_{idx:02d}_{scene_name}.mp4"
        clip_paths.append(out_clip)

        print(f"   [+] Encoding Clip {idx:02d} ({scene_name}): Manim {manim_dur:.2f}s -> Target {target_dur:.2f}s (pad +{pad_dur:.2f}s)...")

        cmd = [
            "ffmpeg", "-y", "-v", "warning",
            "-i", str(manim_mp4),
            "-vf", f"tpad=stop_mode=clone:stop_duration={pad_dur:.3f}",
            "-t", f"{target_dur:.3f}",
            "-c:v", "h264_nvenc",
            "-preset", "p6",
            "-cq", "19",
            "-pix_fmt", "yuv420p",
            "-r", "60",
            str(out_clip)
        ]
        subprocess.run(cmd, check=True)

    # Concat file list
    concat_list_file = STAGING_DIR / "concat_clips.txt"
    with open(concat_list_file, "w") as f:
        for cp in clip_paths:
            f.write(f"file '{cp.resolve()}'\n")

    # Final Master Assembly
    final_output = STAGING_DIR / "master_2k.mp4"
    print(f"\n[*] Concatenating clips and multiplexing audio -> {final_output}...")

    cmd_mux = [
        "ffmpeg", "-y", "-v", "warning",
        "-f", "concat", "-safe", "0", "-i", str(concat_list_file),
        "-i", str(master_audio),
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "320k",
        "-shortest",
        str(final_output)
    ]
    subprocess.run(cmd_mux, check=True)

    final_dur = get_duration(final_output)
    final_size = final_output.stat().st_size / (1024 * 1024)
    print(f"[✓] MASTER 2K QHD VIDEO ASSEMBLED SUCCESSFULLY!")
    print(f"   Path: {final_output}")
    print(f"   Duration: {final_dur:.2f}s ({final_dur/60:.2f} min)")
    print(f"   Size: {final_size:.2f} MB")

if __name__ == "__main__":
    main()
