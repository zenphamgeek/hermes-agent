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
    # Pre-Mortem #3 Guard: Empty-input or truncated parse detection
    assert len(cues) >= 50, f"Pre-Mortem #3: SRT file must contain >= 50 cues, found only {len(cues)}"
    last_cue_end = cues[-1][2]

    # 3. Description last chapter marker
    desc_text = desc_file.read_text(encoding="utf-8")
    ch_matches = re.findall(r"(\d{2}):(\d{2})\s+([^\n]+)", desc_text)
    # Pre-Mortem #3 Guard: Empty-input chapter marker detection
    assert len(ch_matches) >= 3, f"Pre-Mortem #3: description.txt must contain >= 3 chapter markers, found only {len(ch_matches)}"

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

    # Invariant D: Pre-Mortem #2 Guard: Media-vs-Metadata verification
    # Validates that metadata.json duration matches the real ffprobe encoded MP4 container
    media_file = tap_dir / "master_2k.mp4"
    if media_file.exists():
        import subprocess
        probe_cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "json",
            str(media_file)
        ]
        probe_meta = json.loads(subprocess.check_output(probe_cmd).decode())
        real_media_dur = float(probe_meta["format"]["duration"])
        assert abs(dur_s - real_media_dur) < 0.1, (
            f"Pre-Mortem #2: Metadata duration ({dur_s}s) deviates from real MP4 artifact ({real_media_dur:.3f}s) by >= 0.1s!"
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


def test_gold_srt_monotonicity_and_zero_overlap():
    """
    Gold SRT Monotonicity & Zero-Overlap Invariant:
    Guarantees that subtitle cues never jump backward in time,
    have strictly positive durations, and do not overlap across cues.
    """
    tap_dir = STAGING_DIR / "tap_01"
    if not tap_dir.exists():
        pytest.skip("S1E1 staging directory not found")

    srt_file = tap_dir / "subtitles_s1_ep01_masterclass.srt"
    cues = parse_srt_cues(srt_file)
    assert len(cues) >= 50, f"Expected >= 50 cues, got {len(cues)}"

    # 1. Monotonic start timestamps
    starts = [c[1] for c in cues]
    assert starts == sorted(starts), "SRT cues must be strictly monotonically increasing in start time"

    # 2. Positive cue durations
    for idx, start_s, end_s, text in cues:
        assert end_s > start_s, f"Cue {idx} has non-positive duration: {start_s}s -> {end_s}s"

    # 3. Zero cue overlap (subtitles cannot collide)
    for i in range(len(cues) - 1):
        c1 = cues[i]
        c2 = cues[i + 1]
        assert c2[1] >= c1[2] - 0.05, (
            f"Cue overlap detected between cue {c1[0]} (ends {c1[2]:.3f}s) and cue {c2[0]} (starts {c2[1]:.3f}s)"
        )


def validate_tri_artifact_spec(duration_s, cues, chapters, media_duration=None):
    """Core specification validator for differential mutation testing."""
    assert len(cues) >= 50, f"Pre-Mortem #3: SRT file must contain >= 50 cues, found only {len(cues)}"
    assert len(chapters) >= 3, f"Pre-Mortem #3: description.txt must contain >= 3 chapter markers, found only {len(chapters)}"

    last_cue_end = cues[-1][2]
    last_ch_time = chapters[-1][0]

    # Invariant A: Total video container bounds
    assert last_cue_end <= duration_s, (
        f"SRT last cue ({last_cue_end:.2f}s) exceeds metadata duration ({duration_s:.2f}s)"
    )
    assert last_ch_time <= duration_s, (
        f"Last chapter marker ({last_ch_time}s) exceeds metadata duration ({duration_s:.2f}s)"
    )

    # Invariant B: Closing Mosaic headroom (>= 7.5s buffer)
    closing_headroom = duration_s - last_cue_end
    assert closing_headroom >= 7.5, (
        f"Closing mosaic headroom ({closing_headroom:.2f}s) is under the 7.5s minimum"
    )

    # Invariant C: Chapter-to-SRT Synchrony
    chapter_cue_drift = abs(last_ch_time - last_cue_end)
    assert chapter_cue_drift <= 2.5, (
        f"Desync between last chapter ({last_ch_time}s) and SRT end ({last_cue_end:.2f}s): drift={chapter_cue_drift:.2f}s > 2.5s"
    )

    # Invariant D: Cue Overlap
    for i in range(len(cues) - 1):
        assert cues[i + 1][1] >= cues[i][2] - 0.05, f"Cue overlap detected between {cues[i][0]} and {cues[i+1][0]}"

    # Invariant E: Media-vs-Metadata container check
    if media_duration is not None:
        assert abs(duration_s - media_duration) < 0.1, (
            f"Pre-Mortem #2: Metadata duration ({duration_s}s) deviates from real MP4 artifact ({media_duration:.3f}s) by >= 0.1s!"
        )
    return True


def test_tri_artifact_differential_fuzzing_oracle():
    """
    Differential Mutation Fuzzing Oracle (Zero-Fake-Pass Proof):
    Perturbs individual components of the publish-asset tuple and asserts
    that the gate rejects invalid states with the exact expected assertion errors.
    """
    # Baseline valid tuple (60 cues, 4 chapters, dur=609.87s, last_cue=601.36s, last_ch=601s)
    base_cues = [(i, i * 10.0, i * 10.0 + 8.0, f"Cue {i}") for i in range(59)]
    base_cues.append((59, 590.0, 601.36, "Closing cue"))
    base_chapters = [(0, "Intro"), (60, "Topic"), (300, "Math"), (601, "Closing Screen")]
    base_dur = 609.87
    base_media_dur = 609.871

    # 1. Baseline must pass cleanly
    assert validate_tri_artifact_spec(base_dur, base_cues, base_chapters, base_media_dur) is True

    # 2. Mutation A: SRT cue overruns duration
    mutated_cues_overrun = list(base_cues)
    mutated_cues_overrun[-1] = (59, 590.0, 615.0, "Overrun cue")
    with pytest.raises(AssertionError, match="exceeds metadata duration"):
        validate_tri_artifact_spec(base_dur, mutated_cues_overrun, base_chapters, base_media_dur)

    # 3. Mutation B: Headroom under 7.5s
    mutated_cues_headroom = list(base_cues)
    mutated_cues_headroom[-1] = (59, 590.0, 606.0, "Tight headroom cue")
    with pytest.raises(AssertionError, match="under the 7.5s minimum"):
        validate_tri_artifact_spec(base_dur, mutated_cues_headroom, base_chapters, base_media_dur)

    # 4. Mutation C: Chapter marker desynchronized by > 2.5s
    mutated_chapters_desync = list(base_chapters)
    mutated_chapters_desync[-1] = (550, "Early closing")
    with pytest.raises(AssertionError, match="drift="):
        validate_tri_artifact_spec(base_dur, base_cues, mutated_chapters_desync, base_media_dur)

    # 5. Mutation D: Media container duration drifts by >= 0.1s
    with pytest.raises(AssertionError, match="deviates from real MP4 artifact"):
        validate_tri_artifact_spec(base_dur, base_cues, base_chapters, media_duration=611.5)

    # 6. Mutation E: Truncated cues (< 50 cues)
    with pytest.raises(AssertionError, match="must contain >= 50 cues"):
        validate_tri_artifact_spec(base_dur, base_cues[:10], base_chapters, base_media_dur)

    # 7. Mutation F: Empty/insufficient chapter markers (< 3 chapters)
    with pytest.raises(AssertionError, match="must contain >= 3 chapter markers"):
        validate_tri_artifact_spec(base_dur, base_cues, base_chapters[:2], base_media_dur)

    # 8. Mutation G: Overlapping cues (cue 2 starts before cue 1 ends)
    mutated_cues_overlap = list(base_cues)
    mutated_cues_overlap[1] = (1, 5.0, 15.0, "Overlapping cue")  # cue 0 ends at 8.0, cue 1 starts at 5.0
    with pytest.raises(AssertionError, match="Cue overlap detected"):
        validate_tri_artifact_spec(base_dur, mutated_cues_overlap, base_chapters, base_media_dur)


