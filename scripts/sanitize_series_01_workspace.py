#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sanitize_series_01_workspace.py
===============================
Sovereign Workspace Sanitization Script for ZenPham Series 1 (S1E1 to S1E5).
Safely purges obsolete scratch files, unapproved legacy video renders, and temporary caches
while strictly preserving 100% of approved Masters, audio scene masters, and approved Shorts.

Supports:
  --dry-run (default: reports files and sizes without deleting)
  --execute (performs deletion with post-verification against approvals)
"""

import sys
import os
import hashlib
import json
from pathlib import Path

REPO_ROOT = Path("/home/zen/hermes-agent")
APPROVALS_DIR = REPO_ROOT / "approvals"

# Explicit whitelist of approved master files (Must never be deleted)
WHITELIST_APPROVED_VIDEOS = {
    f"assets/scripts_video/output/youtube_staging/series_01/tap_{ep:02d}/master_2k.mp4"
    for ep in range(1, 6)
}

WHITELIST_APPROVED_AUDIOS = {
    f"assets/scripts_video/audio/series_01/tap_{ep:02d}/master_audio_series_01_tap_{ep:02d}.wav"
    for ep in range(1, 6)
}

# Candidate Root scratch files
SCRATCH_ROOT_FILES = [
    "test_chunk1_s1e2.wav",
    "test_clip_6m20_6m35.wav",
    "test_clip_new_master_6m20_6m35.wav",
    "test_crop.jpg",
    "test_edward_temp_0.53.wav",
    "test_para1_direct.wav",
    "test_para3_s1e2.wav",
    "test_s1e2_2m15_2m35.wav",
    "test_s1e2_master_2m25.wav",
    "test_s1e2_sc03_30_55.wav",
    "test_s1e2_sc3_clean.wav",
    "test_s1e4_master_6m27.wav",
    "test_s1e4_sc02_chinh_thuc.wav",
    "test_s1e4_sc6_clean.wav",
    "test_scene_06_10_22.wav",
    "test_sgd_clause.wav",
]

SCRATCH_ROOT_DIRS = [
    "temp_inspect_frames",
]

# Distorted audio backups
DISTORTED_AUDIO_FILES = [
    "assets/scripts_video/audio/series_01/tap_02/scene_06_distorted_backup.wav",
]

# Obsolete Manim Media Render Caches
OBSOLETE_MANIM_MEDIA_DIRS = [
    "assets/scripts_video/output/manim_media/series_01/tap_01_v3",
    "assets/scripts_video/output/manim_media/series_01/tap_01_v7",
    "assets/scripts_video/output/manim_media/series_01/tap_02_v7",
    "assets/scripts_video/output/manim_media/series_01/tap_03_v6",
    "assets/scripts_video/output/manim_media/series_01/tap_04_v7",
    "assets/scripts_video/output/manim_media/series_01/tap_05_v6",
    "assets/scripts_video/output/manim_media/series_01/tap_02",
]


def get_staging_purge_files():
    """Identify old unapproved mp4s and broken symlinks in staging folders for tap_01 to tap_05."""
    purge_list = []
    for ep in range(1, 6):
        staging_dir = REPO_ROOT / f"assets/scripts_video/output/youtube_staging/series_01/tap_{ep:02d}"
        if not staging_dir.exists():
            continue
        for item in staging_dir.iterdir():
            rel_path = str(item.relative_to(REPO_ROOT))
            # Never purge approved master
            if rel_path in WHITELIST_APPROVED_VIDEOS:
                continue
            # Purge extra mp4s
            if item.is_file() and item.suffix.lower() == ".mp4":
                purge_list.append(item)
            # Purge broken symlinks
            elif item.is_symlink() and not item.exists():
                purge_list.append(item)
            # Purge old scene renders
            elif item.name.startswith("scene_") and item.suffix.lower() == ".mp4":
                purge_list.append(item)
            # Purge old muxed cues
            elif item.name.startswith("muxed_") and item.suffix.lower() == ".mp4":
                purge_list.append(item)
    return purge_list


def verify_approved_masters():
    """Verify that all approved masters match their cryptographic seals."""
    print("🔒 Verifying Approved Masters cryptographic seals...")
    for ep in range(1, 6):
        approval_file = APPROVALS_DIR / f"S01_EP{ep:02d}_APPROVAL.json"
        with open(approval_file) as f:
            data = json.load(f)
        exp_v = data["asset_checksums"]["video_master_mp4"]
        exp_a = data["asset_checksums"]["audio_master_wav"]

        v_path = REPO_ROOT / f"assets/scripts_video/output/youtube_staging/series_01/tap_{ep:02d}/master_2k.mp4"
        a_path = REPO_ROOT / f"assets/scripts_video/audio/series_01/tap_{ep:02d}/master_audio_series_01_tap_{ep:02d}.wav"

        assert v_path.exists(), f"Approved video missing: {v_path}"
        assert a_path.exists(), f"Approved audio missing: {a_path}"

        def sha256(p):
            h = hashlib.sha256()
            with open(p, "rb") as f:
                while c := f.read(65536):
                    h.update(c)
            return h.hexdigest()

        act_v = sha256(v_path)
        act_a = sha256(a_path)
        assert act_v == exp_v, f"S1E{ep} Video SHA256 mismatch: {act_v} != {exp_v}"
        assert act_a == exp_a, f"S1E{ep} Audio SHA256 mismatch: {act_a} != {exp_a}"
        print(f"  ✅ S1E{ep:02d}: Video ({v_path.stat().st_size/1e6:.1f}MB) & Audio ({a_path.stat().st_size/1e6:.1f}MB) match 100%")


def run_sanitization(execute: bool = False):
    print("=" * 70)
    print(f"🧹 ZENPHAM SERIES 1 WORKSPACE SANITIZATION ({'EXECUTE' if execute else 'DRY RUN'})")
    print("=" * 70)

    # 1. Pre-flight check
    verify_approved_masters()

    total_bytes = 0
    items_to_delete = []

    # 2. Scratch Root Files
    for fn in SCRATCH_ROOT_FILES:
        p = REPO_ROOT / fn
        if p.exists() and p.is_file():
            sz = p.stat().st_size
            total_bytes += sz
            items_to_delete.append((p, sz, "Scratch root audio/image"))

    # 3. Scratch Root Dirs
    for dn in SCRATCH_ROOT_DIRS:
        p = REPO_ROOT / dn
        if p.exists() and p.is_dir():
            sz = sum(f.stat().st_size for f in p.rglob("*") if f.is_file())
            total_bytes += sz
            items_to_delete.append((p, sz, "Scratch root directory"))

    # 4. Distorted Audio
    for fn in DISTORTED_AUDIO_FILES:
        p = REPO_ROOT / fn
        if p.exists() and p.is_file():
            sz = p.stat().st_size
            total_bytes += sz
            items_to_delete.append((p, sz, "Distorted audio backup"))

    # 5. Staging Purge Files (old mp4s and broken symlinks)
    for p in get_staging_purge_files():
        sz = p.stat().st_size if (p.exists() and not p.is_symlink()) else 0
        total_bytes += sz
        items_to_delete.append((p, sz, "Old unapproved staging render"))

    # 6. Obsolete Manim Media Dirs
    for dn in OBSOLETE_MANIM_MEDIA_DIRS:
        p = REPO_ROOT / dn
        if p.exists() and p.is_dir():
            sz = sum(f.stat().st_size for f in p.rglob("*") if f.is_file())
            total_bytes += sz
            items_to_delete.append((p, sz, "Obsolete Manim render cache"))

    print(f"\n📋 Identified {len(items_to_delete)} items to purge. Total size: {total_bytes / (1024*1024):.2f} MB ({total_bytes / (1024*1024*1024):.2f} GB)")
    print("-" * 70)
    for p, sz, desc in items_to_delete:
        print(f"  [{desc}] {p.relative_to(REPO_ROOT)} ({sz / (1024*1024):.2f} MB)")

    if not execute:
        print("\n💡 This was a DRY RUN. Pass --execute to perform actual deletion.")
        return total_bytes

    print("\n🗑️ Executing deletion...")
    import shutil
    deleted_count = 0
    for p, sz, desc in items_to_delete:
        if p.is_file() or p.is_symlink():
            p.unlink()
            deleted_count += 1
        elif p.is_dir():
            shutil.rmtree(p)
            deleted_count += 1
    print(f"✅ Successfully deleted {deleted_count} items. Reclaimed {total_bytes / (1024*1024):.2f} MB.")

    # Post-deletion verification
    print("\n🔒 Post-sanitization Verification...")
    verify_approved_masters()
    print("🎉 Workspace Sanitization Completed Successfully! All approved masters intact.")
    return total_bytes


if __name__ == "__main__":
    exec_mode = "--execute" in sys.argv
    run_sanitization(execute=exec_mode)
