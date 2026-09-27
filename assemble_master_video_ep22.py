#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
assemble_master_video_ep22.py
Assemble 2K QHD (2560x1440 @ 60fps) master video for ZenPham Series 2 Episode 22:
1. Matches each of the 6 audio scenes with its corresponding 2K Manim animation.
2. Applies FFmpeg tpad=stop_mode=clone to synchronize scene video duration with scene audio duration.
3. Concatenates video track and multiplexes with 5-stage mastered audio.
4. Outputs to assets/scripts_video/output/youtube_staging/series_02/tap_22/master_2k.mp4.
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
AUDIO_DIR = SCRIPTS_VIDEO_DIR / "audio" / "series_02" / "tap_22"
MANIM_MEDIA_DIR = SCRIPTS_VIDEO_DIR / "output" / "manim_media" / "series_02" / "tap_22" / "videos" / "manim_s2_tap_22_function_calling" / "1440p60"
STAGING_DIR = SCRIPTS_VIDEO_DIR / "output" / "youtube_staging" / "series_02" / "tap_22"
CLIPS_DIR = STAGING_DIR / "scene_clips"

# 6 scenes mapped directly to the 6 2K Manim scene animations
SCENE_MANIM_MAP = {
    1: "Tap22Scene01ColdOpen",
    2: "Tap22Scene02Architecture",
    3: "Tap22Scene03Mathematics",
    4: "Tap22Scene04Telemetry",
    5: "Tap22Scene05LabExperiment",
    6: "Tap22Scene06Outro",
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

    master_audio = AUDIO_DIR / "master_audio_series_02_tap_22.wav"
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
        manim_name = SCENE_MANIM_MAP[idx]
        manim_path = MANIM_MEDIA_DIR / f"{manim_name}.mp4"
        if not manim_path.exists():
            print(f"❌ Missing 2K Manim video: {manim_path}")
            sys.exit(1)

        m_dur = get_duration(manim_path)
        target_dur = scene_audio_durs[idx]
        out_clip = CLIPS_DIR / f"clip_{idx:02d}.mp4"
        clip_paths.append(out_clip)

        vf = (
            "scale=2560:1440:flags=lanczos:force_original_aspect_ratio=decrease,"
            "pad=2560:1440:(2560-iw)/2:(1440-ih)/2:color=#0c0d12,fps=60,format=yuv420p"
        )

        if m_dur >= target_dur:
            # Trim to exact target duration
            cmd = [
                "ffmpeg", "-y", "-v", "error",
                "-ss", "0", "-t", f"{target_dur:.3f}",
                "-i", str(manim_path),
                "-vf", vf,
                "-c:v", "h264_nvenc", "-preset", "p4", "-cq", "18", "-an",
                str(out_clip)
            ]
        else:
            # Clone final frame to reach target audio duration
            pad_dur = target_dur - m_dur
            vf_pad = f"{vf},tpad=stop_mode=clone:stop_duration={pad_dur:.3f}"
            cmd = [
                "ffmpeg", "-y", "-v", "error",
                "-i", str(manim_path),
                "-vf", vf_pad,
                "-c:v", "h264_nvenc", "-preset", "p4", "-cq", "18", "-an",
                str(out_clip)
            ]

        t0 = time.time()
        print(f"   Building Clip {idx:02d} ({manim_name}) -> target {target_dur:.2f}s (base {m_dur:.2f}s)...", end="", flush=True)
        subprocess.run(cmd, check=True)
        actual_dur = get_duration(out_clip)
        print(f" done ({time.time()-t0:.1f}s, actual: {actual_dur:.2f}s)")

    # Concatenate all 6 video clips
    concat_list = STAGING_DIR / "concat_clips.txt"
    with open(concat_list, "w") as f:
        for cp in clip_paths:
            f.write(f"file '{cp.resolve()}'\n")

    raw_video = STAGING_DIR / "raw_concat_video.mp4"
    print("\n[*] Concatenating 6 video clips...")
    cmd_concat = [
        "ffmpeg", "-y", "-v", "error",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_list),
        "-c", "copy",
        str(raw_video)
    ]
    subprocess.run(cmd_concat, check=True)
    raw_video_dur = get_duration(raw_video)
    print(f"[*] Concatenated Video Duration: {raw_video_dur:.2f}s")

    # Multiplex video with master audio
    final_output = STAGING_DIR / "master_2k.mp4"
    print(f"\n[*] Multiplexing with 5-stage mastered audio into {final_output.name}...")
    cmd_mux = [
        "ffmpeg", "-y", "-v", "error",
        "-i", str(raw_video),
        "-i", str(master_audio),
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "320k",
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-shortest",
        str(final_output)
    ]
    subprocess.run(cmd_mux, check=True)

    final_dur = get_duration(final_output)
    final_size_mb = final_output.stat().st_size / (1024 * 1024)
    print(f"\n=======================================================")
    print(f"✅ Master 2K Video Ready: {final_output}")
    print(f"   Resolution: 2560x1440 @ 60fps")
    print(f"   Duration:   {final_dur:.2f}s ({final_dur/60:.2f} min)")
    print(f"   Size:       {final_size_mb:.1f} MB")
    print(f"=======================================================")

if __name__ == "__main__":
    main()
