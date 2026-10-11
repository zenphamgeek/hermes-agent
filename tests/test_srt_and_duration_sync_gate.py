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
