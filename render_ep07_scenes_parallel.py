#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
render_ep07_scenes_parallel.py
Renders all 6 scenes of Episode 07 in parallel using Docker Manim 2K QHD (2560x1440 @ 60fps).
"""

import concurrent.futures
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path("/home/zen/hermes-agent")
MEDIA_BASE = REPO_ROOT / "assets" / "scripts_video" / "output" / "manim_media" / "series_02" / "tap_07"
FINAL_MEDIA_DIR = MEDIA_BASE / "videos" / "manim_s2_tap_07_kv_cache" / "1440p60"
SCRIPT_REL_PATH = "assets/scripts_video/series_02/manim/manim_s2_tap_07_kv_cache.py"

SCENES = [
    "Tap07Scene01ColdOpen",
    "Tap07Scene02Architecture",
    "Tap07Scene03Mathematics",
    "Tap07Scene04Telemetry",
    "Tap07Scene05LabExperiment",
    "Tap07Scene06Outro",
]

def render_scene(scene_name: str) -> bool:
    t0 = time.time()
    part_media_dir = MEDIA_BASE / f"part_{scene_name}"
    part_media_dir.mkdir(parents=True, exist_ok=True)
    
    cmd = [
        "docker", "run", "--rm", "--user", "root",
        "-v", f"{REPO_ROOT}:/work:rw",
        "-v", "/home/zen/.local/share/fonts:/usr/local/share/fonts/host_fonts:ro",
        "-w", "/work",
        "manimcommunity/manim:latest",
        "manim", "-qh", "--fps", "60", "-r", "2560,1440",
        "--media_dir", f"assets/scripts_video/output/manim_media/series_02/tap_07/part_{scene_name}",
        SCRIPT_REL_PATH,
        scene_name
    ]
    print(f"[*] Starting render: {scene_name}...")
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    
    if res.returncode != 0:
        print(f"❌ Error rendering {scene_name}:\n{res.stdout[-1500:]}")
        return False
        
    src_mp4 = part_media_dir / "videos" / "manim_s2_tap_07_kv_cache" / "1440p60" / f"{scene_name}.mp4"
    dst_mp4 = FINAL_MEDIA_DIR / f"{scene_name}.mp4"
    
    if not src_mp4.exists():
        print(f"❌ Render finished but output mp4 not found: {src_mp4}")
        return False
        
    FINAL_MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src_mp4, dst_mp4)
    elapsed = time.time() - t0
    print(f"✅ Rendered {scene_name} in {elapsed:.1f}s ({dst_mp4.stat().st_size / 1024 / 1024:.2f} MB)")
    
    # Clean up part directory
    try:
        shutil.rmtree(part_media_dir)
    except Exception:
        pass
        
    return True

def main():
    FINAL_MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    t_start = time.time()
    print(f"=== Starting Parallel 2K Manim Render for Episode 07 ({len(SCENES)} scenes) ===")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(render_scene, scene): scene for scene in SCENES}
        results = {}
        for future in concurrent.futures.as_completed(futures):
            scene = futures[future]
            try:
                ok = future.result()
                results[scene] = ok
            except Exception as e:
                print(f"❌ Exception in {scene}: {e}")
                results[scene] = False
                
    total_time = time.time() - t_start
    all_ok = all(results.values())
    print(f"\n=== Render summary in {total_time:.1f}s ===")
    for s, ok in results.items():
        print(f"   {s}: {'PASS' if ok else 'FAIL'}")
        
    if not all_ok:
        sys.exit(1)
    print("All scenes rendered successfully!")

if __name__ == "__main__":
    main()
