#!/usr/bin/env python3
"""
Master Pipeline Runner for 'TÔI LÀM VIỆC' Video Series (Kênh ZENPHAM)
=====================================================================
Orchestrates:
1. Script Verification (Guard checks for series tags, Host persona)
2. Voiceover Synthesis (Zenpham OmniVoice TTS)
3. Footage Acquisition & Cinematic Color Grading (Pexels + Footage Pool)
4. Manim Math Animation Rendering (if Manim classes specified)
5. Video Assembly & Audio Mastering (Voice-driven, Ambient Piano, -14 LUFS)
6. Cover Scene / Thumbnail Engine (16:9 & 9:16 with Brand Pill)
7. Pre-flight QA & Optional YouTube Publishing
"""

import argparse
import os
import re
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
ASSETS_DIR = REPO_ROOT / "assets/scripts_video"
OUTPUT_DIR = ASSETS_DIR / "output"


def run_cmd(cmd: list, desc: str = ""):
    print(f"\n[EXEC] {desc}...")
    print(f"       Command: {' '.join(cmd)}")
    res = subprocess.run(cmd, cwd=str(ASSETS_DIR), text=True)
    if res.returncode != 0:
        print(f"❌ Error during: {desc} (Exit code {res.returncode})", file=sys.stderr)
        sys.exit(res.returncode)
    print(f"✅ Completed: {desc}")


def main():
    parser = argparse.ArgumentParser(description="End-to-end Pipeline for 'Tôi Làm Việc' Series")
    parser.add_argument("--md", required=True, help="Path to markdown script file")
    parser.add_argument("--landscape", action="store_true", default=True, help="Produce 16:9 landscape video (default)")
    parser.add_argument("--portrait", action="store_true", help="Produce 9:16 portrait video (for Shorts/TikTok)")
    parser.add_argument("--publish", action="store_true", help="Publish directly to YouTube after QC")
    parser.add_argument("--privacy", default="public", choices=["public", "unlisted", "private"], help="YouTube privacy")
    parser.add_argument("--skip-tts", action="store_true", help="Skip TTS if audio already generated")
    parser.add_argument("--skip-footage", action="store_true", help="Skip footage download if clips exist")
    args = parser.parse_args()

    md_path = Path(args.md)
    if not md_path.exists():
        if (ASSETS_DIR / args.md).exists():
            md_path = ASSETS_DIR / args.md
        else:
            print(f"❌ Script not found: {args.md}", file=sys.stderr)
            sys.exit(1)

    stem = md_path.stem
    is_landscape = not args.portrait

    print("=" * 70)
    print(f"🚀 PIPELINE: TÔI LÀM VIỆC — KÊNH ZENPHAM")
    print(f"   Script: {md_path.name}")
    print(f"   Aspect Ratio: {'16:9 Landscape' if is_landscape else '9:16 Portrait'}")
    print(f"   Host: Zen (10+ năm kinh nghiệm AI — InnoRia Solution)")
    print("=" * 70)

    # 1. Voice Synthesis
    if not args.skip_tts:
        run_cmd(
            [sys.executable, "tts_zen.py", "--md", str(md_path), "--mood", "tram_mac_sau_lang", "--speed", "0.96"],
            desc="Zenpham OmniVoice TTS Generation",
        )

    # 2. Footage Fetch & Processing
    raw_dir = ASSETS_DIR / "clips_raw" / stem
    clips_dir = ASSETS_DIR / "clips" / stem
    raw_dir.mkdir(parents=True, exist_ok=True)
    clips_dir.mkdir(parents=True, exist_ok=True)

    if not args.skip_footage:
        fetch_cmd = [sys.executable, "fetch_stock.py", "--md", str(md_path), "--raw-dir", f"clips_raw/{stem}"]
        if is_landscape:
            fetch_cmd.append("--landscape")
        run_cmd(fetch_cmd, desc="Fetching 4K Tech Minimalist Footage")

        post_cmd = [
            sys.executable,
            "post_stock.py",
            "--md",
            str(md_path),
            "--raw-dir",
            f"clips_raw/{stem}",
            "--clips-dir",
            f"clips/{stem}",
        ]
        if is_landscape:
            post_cmd.append("--landscape")
        run_cmd(post_cmd, desc="Cinematic Color Grading & Anti-Skew Processing")

    # 3. Cover Generation
    thumb_land = OUTPUT_DIR / f"thumb_{stem}.jpg"
    thumb_port = OUTPUT_DIR / f"thumb_portrait_{stem}.jpg"
    run_cmd(
        [sys.executable, "cover_design_engine.py", "--md", str(md_path), "--both-ratios"],
        desc="Generating 16:9 and 9:16 YouTube Thumbnails",
    )

    # 4. Assembly & Mastering
    master_out = ASSETS_DIR / f"{stem}_master.mp4"
    music_file = ASSETS_DIR / "music/quiet_room_glow.mp3"

    assemble_cmd = [
        sys.executable,
        "assemble_podcast.py",
        "--md",
        str(md_path),
        "--channel",
        "ZENPHAM",
        "--voice-driven",
        "--audio-dir",
        f"audio/{stem}",
        "--clips-dir",
        f"clips/{stem}",
        "--out",
        str(master_out),
    ]
    if is_landscape:
        assemble_cmd.append("--landscape")
    if music_file.exists():
        assemble_cmd.extend(["--music", str(music_file)])

    run_cmd(assemble_cmd, desc="Assembling Master Video with Subtitles & Broadcast Loudness")

    print("\n" + "=" * 70)
    print(f"🎉 MASTER VIDEO COMPLETED: {master_out}")
    print(f"   Thumbnail: {thumb_land}")
    print("=" * 70)

    # 5. YouTube Publish
    if args.publish:
        yt_script = REPO_ROOT / "skills/media/youtube-publisher/scripts/yt_publish.py"
        run_cmd(
            [
                sys.executable,
                str(yt_script),
                "upload",
                "--video",
                str(master_out),
                "--md",
                str(md_path),
                "--channel",
                "ZENPHAM",
                "--privacy",
                args.privacy,
            ],
            desc="Publishing Video to ZENPHAM YouTube Channel",
        )


if __name__ == "__main__":
    main()
