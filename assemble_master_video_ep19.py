#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
assemble_master_video_ep19.py
Assemble 2K QHD (2560x1440 @ 60fps) master video for ZenPham Series 2 Episode 19:
1. Matches each of the 6 audio scenes with its corresponding 2K Manim animation.
2. Applies FFmpeg tpad=stop_mode=clone to synchronize scene video duration with scene audio duration.
3. Concatenates video track and multiplexes with 5-stage mastered audio.
4. Outputs to assets/scripts_video/output/youtube_staging/series_02/tap_19/master_2k.mp4.
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
AUDIO_DIR = SCRIPTS_VIDEO_DIR / "audio" / "series_02" / "tap_19"
MANIM_MEDIA_DIR = SCRIPTS_VIDEO_DIR / "output" / "manim_media" / "series_02" / "tap_19" / "videos" / "manim_s2_tap_19_grpo" / "1440p60"
STAGING_DIR = SCRIPTS_VIDEO_DIR / "output" / "youtube_staging" / "series_02" / "tap_19"
CLIPS_DIR = STAGING_DIR / "scene_clips"

SCENE_MANIM_MAP = {
    1: "Tap19Scene01ColdOpen",
    2: "Tap19Scene02Architecture",
    3: "Tap19Scene03Mathematics",
    4: "Tap19Scene04Telemetry",
    5: "Tap19Scene05LabExperiment",
    6: "Tap19Scene06Outro",
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

    master_audio = AUDIO_DIR / "master_audio_series_02_tap_19.wav"
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
            cmd = [
                "ffmpeg", "-y", "-v", "error",
                "-ss", "0", "-t", f"{target_dur:.3f}",
                "-i", str(manim_path),
                "-vf", vf,
                "-c:v", "h264_nvenc", "-preset", "p4", "-cq", "18", "-an",
                str(out_clip)
            ]
        else:
            pad_dur = target_dur - m_dur
            cmd = [
                "ffmpeg", "-y", "-v", "error",
                "-i", str(manim_path),
                "-vf", f"{vf},tpad=stop_mode=clone:stop_duration={pad_dur:.3f}",
                "-c:v", "h264_nvenc", "-preset", "p4", "-cq", "18", "-an",
                str(out_clip)
            ]

        print(f"   [+] Encoding Clip {idx:02d} ({manim_name}): Manim {m_dur:.2f}s -> Target {target_dur:.2f}s (pad +{max(0.0, target_dur - m_dur):.2f}s)...")
        subprocess.run(cmd, check=True)

    # Concat clips into master video
    concat_list = STAGING_DIR / "concat_clips.txt"
    with open(concat_list, "w", encoding="utf-8") as f:
        for cp in clip_paths:
            f.write(f"file '{cp.resolve()}'\n")

    video_only = STAGING_DIR / "video_track_2k.mp4"
    print(f"\n[*] Concatenating 6 clips to video track: {video_only}...")
    cmd_cat = [
        "ffmpeg", "-y", "-v", "error",
        "-f", "concat", "-safe", "0", "-i", str(concat_list),
        "-c", "copy",
        str(video_only)
    ]
    subprocess.run(cmd_cat, check=True)
    concat_list.unlink(missing_ok=True)

    video_dur = get_duration(video_only)
    print(f"   [✓] Video Track Assembled: {video_dur:.2f}s")

    # Final Master Mux with Master Audio
    final_master = STAGING_DIR / "master_2k.mp4"
    print(f"\n[*] Multiplexing Video and Audio into Final Master: {final_master}...")
    cmd_mux = [
        "ffmpeg", "-y", "-v", "error",
        "-i", str(video_only),
        "-i", str(master_audio),
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "320k",
        "-shortest",
        str(final_master)
    ]
    subprocess.run(cmd_mux, check=True)

    master_dur = get_duration(final_master)
    master_size = final_master.stat().st_size / (1024 * 1024)
    print(f"\n" + "=" * 60)
    print(f"🎉 MASTER 2K EPISODE 19 ASSEMBLED SUCCESSFULLY!")
    print(f"   File:     {final_master}")
    print(f"   Size:     {master_size:.1f} MB")
    print(f"   Duration: {master_dur:.2f}s ({master_dur/60:.2f} min)")
    print("=" * 60)

if __name__ == "__main__":
    main()
