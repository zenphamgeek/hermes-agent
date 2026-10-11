#!/usr/bin/env python3
"""
Hermes Agent Orchestrator for YouTube SRT Extractor
--------------------------------------------------
Acts as the background job worker and task orchestrator for Hermes Agent.
Features:
- Processes a bounded batch of videos per run (e.g. 20-30 videos) to stay well within YouTube limits
- Reports execution metrics, completed video titles, and storage statistics back to Hermes
- Integrates seamlessly with `hermes cron` scheduled ticks
- Automatically resumes from SQLite checkpoint
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
EXTRACTOR_SCRIPT = SKILL_DIR / "scripts" / "extractor.py"


def run_orchestrated_batch(
    channel_url: str,
    output_dir: str,
    chunk_size: int = 20,
    languages: str = "vi,en,auto",
    whisper_model: str = "large-v2",
    cookies_from_browser: str = None,
    keep_audio: bool = False
):
    cmd = [
        sys.executable,
        str(EXTRACTOR_SCRIPT),
        channel_url,
        "--limit", str(chunk_size),
        "--chunk-size", str(chunk_size),
        "--languages", languages,
        "--whisper-model", whisper_model,
        "--delay-min", "1.0",
        "--delay-max", "2.5",
        "--rest-seconds", "5.0",
    ]
    if output_dir:
        cmd.extend(["--output-dir", output_dir])
    if cookies_from_browser:
        cmd.extend(["--cookies-from-browser", cookies_from_browser])
    if keep_audio:
        cmd.append("--keep-audio")

    print(f"🎬 [Hermes Orchestrator] Starting scheduled extraction batch (Limit: {chunk_size} videos)...")
    result = subprocess.run(cmd, capture_output=False)
    
    # Read manifest summary if available
    out_path = Path(output_dir) if output_dir else Path("./output_srt")
    manifest_file = list(out_path.glob("**/manifest.json"))
    if manifest_file:
        try:
            with open(manifest_file[0], "r", encoding="utf-8") as f:
                data = json.load(f)
            stats = data.get("stats", {})
            print("\n📊 [Hermes Orchestrator Report]")
            print(f"- Total Recorded: {stats.get('total_records', 0)}")
            print(f"- Completed: {stats.get('completed', 0)} (YouTube Subs: {stats.get('youtube_auto', 0) + stats.get('youtube_manual', 0)}, WhisperX: {stats.get('whisperx', 0)})")
            print(f"- Failed / Retrying: {stats.get('failed', 0)}")
        except Exception:
            pass

    return result.returncode


def main():
    parser = argparse.ArgumentParser(description="Hermes Job Orchestrator for YouTube SRT Extractor")
    parser.add_argument("url", help="YouTube channel or playlist URL")
    parser.add_argument("-o", "--output-dir", help="Output directory")
    parser.add_argument("--batch-limit", type=int, default=20, help="Max videos to process in this scheduled tick")
    parser.add_argument("--languages", default="vi,en,auto", help="Languages priority")
    parser.add_argument("--whisper-model", default="large-v2", help="Whisper model for fallback")
    parser.add_argument("--cookies-from-browser", help="Browser name for cookies")
    parser.add_argument("--keep-audio", action="store_true", help="Keep audio files")
    args = parser.parse_args()

    sys.exit(run_orchestrated_batch(
        channel_url=args.url,
        output_dir=args.output_dir,
        chunk_size=args.batch_limit,
        languages=args.languages,
        whisper_model=args.whisper_model,
        cookies_from_browser=args.cookies_from_browser,
        keep_audio=args.keep_audio,
    ))


if __name__ == "__main__":
    main()
