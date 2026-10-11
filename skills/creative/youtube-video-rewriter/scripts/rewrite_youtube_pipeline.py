#!/usr/bin/env python3
"""
rewrite_youtube_pipeline.py — End-to-End YouTube Video Rewriting & Production Pipeline
====================================================================================
Part of the `youtube-video-rewriter` Skill ecosystem on ThinkPad P15.

Orchestrates the complete 5-stage transformation:
1. Ingestion: SRT/Transcript harvesting (with local Faster-Whisper ASR fallback)
2. Deconstruction: Pedagogical deconstruction & 6-act timeline mapping
3. Manim SRS Planning: Registry-first scene matching from 100 scenes + 4-zone layout
4. Multi-Track Scriptwriting: Timeline, OmniVoice TTS phonetics, Manim blueprint, Footage/SFX
5. Hallucination Audit: Automated 5-dimension fact-check, math & AST rigor verification
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict

# Local script imports
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from srt_extractor import run_extraction
from script_deconstructor import deconstruct_video
from manim_srs_planner import plan_manim_srs
from script_writer import write_production_script
from hallucination_auditor import audit_script


def print_banner():
    print("""
================================================================================
🎬 ZENPHAM YOUTUBE REWRITE & DEEP TECH SCRIPT PIPELINE (P15 WORKSTATION)
   2K QHD 1440p | Manim 4-Zone | OmniVoice TTS | Hallucination Audit Engine
================================================================================
""")


def execute_pipeline(
    url: str,
    output_dir: Path,
    style: str = "neo_noir",
    force_whisper: bool = False,
    run_audit: bool = True,
) -> Dict[str, Any]:
    """Execute end-to-end pipeline across all 5 stages."""
    start_time = time.time()
    print_banner()
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"🎯 Target URL   : {url}")
    print(f"📁 Output Dir   : {output_dir}")
    print(f"🎨 Visual Style : {style}")
    print(f"⚙️ Whisper ASR  : {'FORCED' if force_whisper else 'AUTO-DETECT'}")
    print(f"🔍 Audit Mode   : {'ACTIVE' if run_audit else 'DISABLED'}\n")

    # -------------------------------------------------------------
    # STAGE 1: SRT & Metadata Ingestion
    # -------------------------------------------------------------
    print("-" * 70)
    print("🚀 [STAGE 1/5] INGESTION: Harvesting Subtitles, Transcripts & Audio...")
    print("-" * 70)
    ingest_dir = output_dir / "01_ingest"
    ingest_res = run_extraction(url, ingest_dir, force_whisper=force_whisper)

    # -------------------------------------------------------------
    # STAGE 2: Pedagogical Deconstruction
    # -------------------------------------------------------------
    print("\n" + "-" * 70)
    print("🧠 [STAGE 2/5] DECONSTRUCTION: Reverse-Engineering Pedagogical Invariants...")
    print("-" * 70)
    decon_dir = output_dir / "02_deconstruct"
    decon_res = deconstruct_video(ingest_res, decon_dir)

    # -------------------------------------------------------------
    # STAGE 3: Manim SRS & Registry-First Planning
    # -------------------------------------------------------------
    print("\n" + "-" * 70)
    print("📐 [STAGE 3/5] MANIM SRS: Querying 100-Scene Registry & 4-Zone Layout...")
    print("-" * 70)
    srs_dir = output_dir / "03_manim_srs"
    srs_res = plan_manim_srs(decon_res, srs_dir, style=style)

    # -------------------------------------------------------------
    # STAGE 4: Multi-Track Production Scriptwriting
    # -------------------------------------------------------------
    print("\n" + "-" * 70)
    print("✍️ [STAGE 4/5] SCRIPTWRITING: Crafting 4-Track Production Script & TTS...")
    print("-" * 70)
    script_dir = output_dir / "04_script"
    script_res = write_production_script(decon_res, srs_res, script_dir)

    # -------------------------------------------------------------
    # STAGE 5: Automated Hallucination & Fact-Checking Audit
    # -------------------------------------------------------------
    audit_res = None
    if run_audit:
        print("\n" + "-" * 70)
        print("🛡️ [STAGE 5/5] AUDIT: Running 5-Dimension Hallucination & Rigor Audit...")
        print("-" * 70)
        audit_dir = output_dir / "05_audit"
        raw_script_text = (script_dir / "production_script_multitrack.md").read_text(
            encoding="utf-8"
        )
        audit_res = audit_script(script_res, raw_script_text, audit_dir)

    # -------------------------------------------------------------
    # SUMMARY REPORT
    # -------------------------------------------------------------
    elapsed = round(time.time() - start_time, 2)
    print("\n" + "=" * 80)
    print("🏁 PIPELINE EXECUTION COMPLETED SUCCESSFULLY!")
    print("=" * 80)
    print(f"🎬 Video Title         : {ingest_res['metadata']['title']}")
    print(f"⏱️ Source Duration      : {ingest_res['metadata']['duration']} seconds")
    print(f"📚 Domain Classified   : {decon_res['domain']}")
    print(f"🎨 Visual Style Preset : {style}")
    print(f"🔄 Reused Scenes (DB)  : {srs_res['reused_count']} / {srs_res['total_scenes']}")
    print(f"✨ New 4-Zone Scenes   : {srs_res['new_design_count']} / {srs_res['total_scenes']}")
    print(f"📝 Script Word Count   : ~{script_res['total_words']} words (~{script_res['est_total_duration_minutes']} mins)")

    if audit_res:
        print(f"🛡️ Hallucination Score : {audit_res['risk_score']} / 100 ({audit_res['quality_rating']})")
        print(f"⚠️ Issues Identified   : {audit_res['total_findings']} (Critical: {audit_res['critical_count']})")

    print(f"⏳ Total Elapsed Time  : {elapsed} seconds")
    print(f"📂 Primary Script File : {script_dir / 'production_script_multitrack.md'}")
    if audit_res:
        print(f"📋 Audit Report File   : {output_dir / '05_audit' / 'hallucination_audit_report.md'}")
    print("=" * 80 + "\n")

    return {
        "ingest": ingest_res,
        "deconstruct": decon_res,
        "srs": srs_res,
        "script": script_res,
        "audit": audit_res,
        "elapsed_seconds": elapsed,
    }


def main():
    parser = argparse.ArgumentParser(
        description="End-to-End YouTube Video Rewriting & Production Pipeline"
    )
    parser.add_argument("url", help="YouTube video URL or Video ID")
    parser.add_argument(
        "--output-dir",
        default="./workspace/youtube_rewrite_output",
        help="Root output directory for all stage artifacts",
    )
    parser.add_argument(
        "--style",
        choices=["neo_noir", "architecture", "minimal", "vibrant"],
        default="neo_noir",
        help="Visual style preset for Manim & Duotone assets",
    )
    parser.add_argument(
        "--force-whisper",
        action="store_true",
        help="Force local Faster-Whisper ASR transcription",
    )
    parser.add_argument(
        "--skip-audit",
        action="store_true",
        help="Skip automated hallucination audit stage",
    )
    args = parser.parse_args()

    execute_pipeline(
        url=args.url,
        output_dir=Path(args.output_dir),
        style=args.style,
        force_whisper=args.force_whisper,
        run_audit=not args.skip_audit,
    )


if __name__ == "__main__":
    main()
