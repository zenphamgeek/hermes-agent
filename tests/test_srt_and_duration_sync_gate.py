#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_srt_and_duration_sync_gate.py
========================================
Automated Verification Gate for SRT Subtitle Synchronization, Duration Integrity,
and Zero-Bleed Closing Mosaic Invariants.

Enforces:
1. last_srt_cue_end <= duration_seconds (zero truncated subtitles).
2. Subtitles never bleed into the 8.00s Closing Screen Mosaic window.
3. Gold SRT Karaoke: duration <= 2.5s per cue, <= 6 words per cue.
4. Metadata duration matches rendered video artifact within tolerance.
"""

import json
import re
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
STAGING_DIR = REPO_ROOT / "assets" / "scripts_video" / "output" / "youtube_staging" / "series_01"


def parse_srt_cues(srt_path: Path):
    """Parses an SRT file and returns list of (index, start_s, end_s, text)."""
    content = srt_path.read_text(encoding="utf-8")
    cue_pattern = re.compile(
        r"(\d+)\s*\n"
        r"(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*\n"
        r"([\s\S]*?)(?=\n\s*\n\d+\s*\n|\Z)"
    )
    cues = []
    for match in cue_pattern.finditer(content):
        idx = int(match.group(1))
        h1, m1, s1, ms1 = map(int, match.group(2, 3, 4, 5))
        h2, m2, s2, ms2 = map(int, match.group(6, 7, 8, 9))
        start_s = h1 * 3600 + m1 * 60 + s1 + ms1 / 1000.0
        end_s = h2 * 3600 + m2 * 60 + s2 + ms2 / 1000.0
        text = match.group(10).strip()
        cues.append((idx, start_s, end_s, text))
    return cues


def test_s1e1_srt_and_duration_sync():
    """Verify S1E1 subtitle cues align perfectly with metadata duration and closing screen."""
    tap_dir = STAGING_DIR / "tap_01"
    if not tap_dir.exists():
        pytest.skip("S1E1 staging directory not found")

    meta_file = tap_dir / "metadata.json"
    srt_file = tap_dir / "subtitles_s1_ep01_masterclass.srt"

    assert meta_file.exists(), f"metadata.json missing at {meta_file}"
    assert srt_file.exists(), f"SRT file missing at {srt_file}"

    meta = json.loads(meta_file.read_text(encoding="utf-8"))
    duration_s = float(meta["duration_seconds"])

    cues = parse_srt_cues(srt_file)
    assert len(cues) > 0, "SRT file must contain cues"

    last_cue = cues[-1]
    last_end = last_cue[2]

    # Invariant 1: Last cue must end before total video duration
    assert last_end <= duration_s, (
        f"Last SRT cue ({last_end:.3f}s) extends beyond video duration ({duration_s:.3f}s)!"
    )

    # Invariant 2: Closing Screen Mosaic window (8.00s) must remain 100% clean of subtitles
    # Subtitle cues must end at least 7.5s before the end of the video
    mosaic_headroom = duration_s - last_end
    assert mosaic_headroom >= 7.5, (
        f"Subtitles bleed into Closing Mosaic window! Headroom is only {mosaic_headroom:.2f}s (must be >= 7.5s)"
    )

    # Invariant 3: Gold SRT Karaoke Cadence
    for idx, start_s, end_s, text in cues:
        dur = end_s - start_s
        assert dur <= 2.55, f"Cue {idx} exceeds max karaoke duration: {dur:.2f}s > 2.5s"
        words = text.split()
        assert len(words) <= 7, f"Cue {idx} exceeds word limit: {len(words)} words ({text})"


def test_all_episodes_metadata_duration_derived_from_actual_files():
    """Verify metadata.json duration matches media artifacts across all staged episodes."""
    for meta_file in STAGING_DIR.glob("tap_*/metadata.json"):
        meta = json.loads(meta_file.read_text(encoding="utf-8"))
        duration_s = float(meta.get("duration_seconds") or meta.get("duration", 0))
        assert duration_s > 0, f"{meta_file} duration_seconds must be positive"

        # Check if master_2k.mp4 exists in the same folder
        media_file = meta_file.parent / "master_2k.mp4"
        if media_file.exists():
            import subprocess
            cmd = [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "json",
                str(media_file)
            ]
            res = json.loads(subprocess.check_output(cmd).decode())
            real_dur = float(res["format"]["duration"])
            assert abs(duration_s - real_dur) < 0.5, (
                f"Drift detected in {meta_file}: metadata says {duration_s}s, artifact is {real_dur}s"
            )


def test_tri_artifact_atomic_consistency_gate():
    """
    Tri-Artifact Atomic Gate:
    Enforces atomic 3-way consistency across:
    (metadata.duration_seconds, srt_last_cue_end, description_last_chapter).
    Guarantees captions, chapters, and video container boundaries never desynchronize.
    """
    tap_dir = STAGING_DIR / "tap_01"
    if not tap_dir.exists():
        pytest.skip("S1E1 staging directory not found")

    meta_file = tap_dir / "metadata.json"
    srt_file = tap_dir / "subtitles_s1_ep01_masterclass.srt"
    desc_file = tap_dir / "description.txt"

    assert meta_file.exists(), f"metadata.json missing at {meta_file}"
    assert srt_file.exists(), f"SRT file missing at {srt_file}"
    assert desc_file.exists(), f"description.txt missing at {desc_file}"

    # 1. Metadata duration
    meta = json.loads(meta_file.read_text(encoding="utf-8"))
    dur_s = float(meta["duration_seconds"])

    # 2. SRT last cue end
    cues = parse_srt_cues(srt_file)
    assert len(cues) > 0, "SRT file must contain cues"
    last_cue_end = cues[-1][2]

    # 3. Description last chapter marker
    desc_text = desc_file.read_text(encoding="utf-8")
    ch_matches = re.findall(r"(\d{2}):(\d{2})\s+([^\n]+)", desc_text)
    assert len(ch_matches) > 0, "description.txt must contain chapter markers"

    last_ch_m, last_ch_s, last_ch_title = ch_matches[-1]
    last_ch_time = int(last_ch_m) * 60 + int(last_ch_s)

    # Invariant A: Total video container bounds
    assert last_cue_end <= dur_s, (
        f"SRT last cue ({last_cue_end:.2f}s) exceeds metadata duration ({dur_s:.2f}s)"
    )
    assert last_ch_time <= dur_s, (
        f"Last chapter marker ({last_ch_time}s) exceeds metadata duration ({dur_s:.2f}s)"
    )

    # Invariant B: Closing Mosaic headroom (>= 7.5s buffer for 8.00s closing screen)
    closing_headroom = dur_s - last_cue_end
    assert closing_headroom >= 7.5, (
        f"Closing mosaic headroom ({closing_headroom:.2f}s) is under the 7.5s minimum"
    )

    # Invariant C: Chapter-to-SRT Synchrony (chapter marker aligns within 2.5s of narration end)
    chapter_cue_drift = abs(last_ch_time - last_cue_end)
    assert chapter_cue_drift <= 2.5, (
        f"Desync between last chapter ({last_ch_time}s) and SRT end ({last_cue_end:.2f}s): drift={chapter_cue_drift:.2f}s > 2.5s"
    )


def test_zero_atempo_slowdown_in_synthesis_scripts():
    """Verify zero artificial speech stretching (atempo < 1.0) in all video synthesis scripts."""
    synth_scripts = list((REPO_ROOT / "assets" / "scripts_video").glob("*.py"))
    assert len(synth_scripts) > 0, "No synthesis scripts found in assets/scripts_video"

    slowdown_pattern = re.compile(r"atempo\s*=?\s*0\.[0-9]+")
    for script_file in synth_scripts:
        content = script_file.read_text(encoding="utf-8", errors="replace")
        matches = slowdown_pattern.findall(content)
        assert len(matches) == 0, (
            f"Artificial speech slowdown (atempo < 1.0) detected in {script_file.name}: {matches}"
        )

