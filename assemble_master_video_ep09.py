#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
assemble_master_video_ep09.py
Assemble 2K QHD (2560x1440 @ 60fps) master video for ZenPham Series 2 Episode 09:
1. Matches each of the 6 audio scenes with its corresponding 2K Manim animation.
2. Applies FFmpeg tpad=stop_mode=clone to synchronize scene video duration with scene audio duration.
3. Concatenates video track and multiplexes with 5-stage mastered audio.
4. Outputs to assets/scripts_video/output/youtube_staging/series_02/tap_09/master_2k.mp4.
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
AUDIO_DIR = SCRIPTS_VIDEO_DIR / "audio" / "series_02" / "tap_09"
MANIM_MEDIA_DIR = SCRIPTS_VIDEO_DIR / "output" / "manim_media" / "series_02" / "tap_09" / "videos" / "manim_s2_tap_09_flashattention" / "1440p60"
STAGING_DIR = SCRIPTS_VIDEO_DIR / "output" / "youtube_staging" / "series_02" / "tap_09"
CLIPS_DIR = STAGING_DIR / "scene_clips"

SCENE_MANIM_MAP = {
    1: "Tap09Scene01ColdOpen",
    2: "Tap09Scene02Architecture",
    3: "Tap09Scene03Mathematics",
    4: "Tap09Scene04Telemetry",
    5: "Tap09Scene05LabExperiment",
    6: "Tap09Scene06Outro",
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

    master_audio = AUDIO_DIR / "master_audio_series_02_tap_09.wav"
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
            print(f"❌ Missing Manim MP4: {manim_mp4}")
            sys.exit(1)

        manim_dur = get_duration(manim_mp4)
        target_dur = scene_audio_durs[idx]
        pad_dur = max(0.0, target_dur - manim_dur)
        out_clip = CLIPS_DIR / f"clip_{idx:02d}.mp4"
        clip_paths.append(out_clip)

        print(f"   [+] Encoding Clip {idx:02d} ({scene_name}): Manim {manim_dur:.2f}s -> Target {target_dur:.2f}s (pad +{pad_dur:.2f}s)...")

        # Use GPU NVENC for high-speed encoding
        cmd = [
            "ffmpeg", "-y", "-v", "error",
            "-i", str(manim_mp4),
            "-vf", f"scale=2560:1440:flags=lanczos:force_original_aspect_ratio=decrease,pad=2560:1440:(2560-iw)/2:(1440-ih)/2:color=#0c0d12,fps=60,format=yuv420p,tpad=stop_mode=clone:stop_duration={pad_dur:.3f}",
            "-c:v", "h264_nvenc",
            "-preset", "p4",
            "-cq", "18",
            "-an",
            str(out_clip)
        ]
        res = subprocess.run(cmd)
        if res.returncode != 0:
            print(f"⚠️ NVENC failed, falling back to libx264 for clip {idx:02d}...")
            cmd_cpu = [
                "ffmpeg", "-y", "-v", "error",
                "-i", str(manim_mp4),
                "-vf", f"scale=2560:1440:flags=lanczos:force_original_aspect_ratio=decrease,pad=2560:1440:(2560-iw)/2:(1440-ih)/2:color=#0c0d12,fps=60,format=yuv420p,tpad=stop_mode=clone:stop_duration={pad_dur:.3f}",
                "-c:v", "libx264",
                "-preset", "veryfast",
                "-crf", "18",
                "-an",
                str(out_clip)
            ]
            subprocess.run(cmd_cpu, check=True)

    # Concat clips using concat demuxer
    concat_list = STAGING_DIR / "concat_list.txt"
    with open(concat_list, "w") as f:
        for p in clip_paths:
            f.write(f"file '{p.resolve()}'\n")

    video_track = STAGING_DIR / "video_track_2k.mp4"
    print(f"\n[*] Concatenating 6 clips to video track: {video_track}...")
    concat_cmd = [
        "ffmpeg", "-y", "-v", "error",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_list),
        "-c", "copy",
        str(video_track)
    ]
    subprocess.run(concat_cmd, check=True)
    v_dur = get_duration(video_track)
    print(f"   [✓] Video Track Assembled: {v_dur:.2f}s")

    # Multiplex with master audio into final master_2k.mp4
    master_video = STAGING_DIR / "master_2k.mp4"
    print(f"\n[*] Multiplexing Video and Audio into Final Master: {master_video}...")
    mux_cmd = [
        "ffmpeg", "-y", "-v", "error",
        "-i", str(video_track),
        "-i", str(master_audio),
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "320k",
        "-shortest",
        str(master_video)
    ]
    subprocess.run(mux_cmd, check=True)

    final_size_mb = master_video.stat().st_size / (1024 * 1024)
    final_dur = get_duration(master_video)
    print("\n" + "=" * 60)
    print(f"🎉 MASTER 2K EPISODE 09 ASSEMBLED SUCCESSFULLY!")
    print(f"   File:     {master_video}")
    print(f"   Size:     {final_size_mb:.1f} MB")
    print(f"   Duration: {final_dur:.2f}s ({final_dur/60:.2f} min)")
    print("=" * 60)

if __name__ == "__main__":
    main()
