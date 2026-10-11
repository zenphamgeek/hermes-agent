#!/usr/bin/env python3
"""
SwapFace Target Folder Runner for Hermes Agent
==============================================
Performs high quality batch face swapping from a source face image into all target
videos/images in a specified folder (e.g. segments produced by video-face-segmenter).

Executes on the local LXC FaceFusion GPU Container (or Modal), with automatic GPU
lifecycle management (freeing GPU VRAM during batch and restoring Gradio UI on completion).
All output files and summary reports are saved to /output/swapface_batches/...
"""

import os
import sys
import time
import json
import glob
import re
import argparse
import subprocess
import shutil
from pathlib import Path
from typing import List, Dict, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.media_asset_catalog import resolve_asset, scan_assets

DEFAULT_OUTPUT_BASE = Path("/home/zen/workspace/output/swapface_batches")
LOCAL_FF_CONTAINER = "facefusion-ai"
VALID_MEDIA_EXTENSIONS = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".jpg", ".jpeg", ".png", ".webp"}


def natural_sort_key(s: str) -> list:
    """Sort strings with embedded numbers naturally (e.g. segment_2 before segment_10)."""
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', str(s))]


def resolve_path(p_str: str) -> Path:
    """Resolve paths, mapping /output to /home/zen/workspace/output if needed."""
    if str(p_str).startswith("/output"):
        rel = str(p_str)[len("/output"):].lstrip("/")
        return (Path("/home/zen/workspace/output") / rel).resolve()
    return Path(p_str).resolve()


def download_if_url(file_or_url: str, dest_dir: Path) -> Path:
    dest_dir.mkdir(parents=True, exist_ok=True)
    if file_or_url.startswith("http://") or file_or_url.startswith("https://"):
        import requests
        fname = file_or_url.split("/")[-1].split("?")[0] or f"dl_{int(time.time())}"
        out_path = dest_dir / fname
        print(f"[*] Downloading {file_or_url} -> {out_path}...", file=sys.stderr)
        resp = requests.get(file_or_url, stream=True, timeout=120)
        resp.raise_for_status()
        with open(out_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
        return out_path
    
    # 1. Direct path check (instant)
    p = Path(file_or_url).expanduser()
    if p.is_file():
        return p.resolve()

    # 2. Repo-relative check
    repo_cand = REPO_ROOT / file_or_url.lstrip("/")
    if repo_cand.is_file():
        return repo_cand.resolve()

    # 2b. Direct check in assets/faces/female, assets/faces/male, assets/faces
    clean_val = Path(file_or_url).stem.lower().strip()
    raw_val = Path(file_or_url).name.lower().strip()
    for fdir in [
        REPO_ROOT / "assets/faces/female",
        REPO_ROOT / "assets/faces/male",
        REPO_ROOT / "assets/faces",
    ]:
        if fdir.is_dir():
            for f in fdir.iterdir():
                if f.is_file() and f.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp"):
                    if clean_val == f.stem.lower() or clean_val in f.stem.lower() or raw_val == f.name.lower():
                        return f.resolve()

    # 3. Google Drive mount check (instant)
    cloud_root = Path("/home/zen/GoogleDrive/phamvuthang@gmail.com/Content Factory")
    if cloud_root.is_dir():
        cloud_cand = cloud_root / file_or_url.lstrip("/")
        if cloud_cand.is_file():
            return cloud_cand.resolve()
        for sub in [
            "02_Media/Images/Faces/female",
            "02_Media/Images/Faces/male",
            "02_Media/Images/Faces",
        ]:
            sdir = cloud_root / sub
            if sdir.is_dir():
                c = sdir / Path(file_or_url).name
                if c.is_file():
                    return c.resolve()
                for f in sdir.iterdir():
                    if f.is_file() and (clean_val in f.stem.lower() or raw_val == f.name.lower()):
                        return f.resolve()

    assets_root = Path(os.environ.get("HERMES_ASSETS_DIR", Path.cwd() / "assets"))
    return resolve_asset(file_or_url, scan_assets(assets_root), category="face")


def find_target_files(target_dir: Path, filter_mode: str = "ok_only") -> List[Path]:
    """Discover target media files in target_dir according to filter_mode."""
    if not target_dir.exists() or not target_dir.is_dir():
        raise NotADirectoryError(f"Target folder not found: {target_dir}")

    all_files = [p for p in target_dir.iterdir() if p.is_file() and p.suffix.lower() in VALID_MEDIA_EXTENSIONS]

    if filter_mode == "ok_only":
        # Match *_OK.mp4, *_ok.mp4, *_OK.jpg, etc.
        matched = [p for p in all_files if re.search(r'[_.-]ok\.[^.]+$', p.name, re.IGNORECASE)]
        # If no _OK files found (e.g. general folder), fall back to all media files
        if not matched:
            print(f"[!] No '_OK' files found in {target_dir.name}. Processing all media files instead.", file=sys.stderr)
            matched = all_files
    elif filter_mode == "not_only":
        matched = [p for p in all_files if re.search(r'[_.-]not\.[^.]+$', p.name, re.IGNORECASE)]
    elif filter_mode == "all":
        matched = all_files
    else:
        # Custom glob pattern
        pattern = filter_mode
        matched = [Path(p) for p in glob.glob(str(target_dir / pattern)) if Path(p).is_file()]

    matched.sort(key=lambda p: natural_sort_key(p.name))
    return matched


class FolderSwapFaceRunner:
    def __init__(
        self,
        source_face: str,
        target_folder: str,
        output_dir: Optional[str] = None,
        filter_mode: str = "ok_only",
        face_swapper_model: str = "inswapper_128_fp16",
        face_swapper_pixel_boost: str = "128x128",
        face_enhancer_model: Optional[str] = "codeformer",
        frame_enhancer_model: Optional[str] = None,
        face_detector_model: str = "yolo_face",
        execution_thread_count: int = 4,
        temp_frame_format: str = "bmp"
    ):
        self.work_dir = Path("/tmp/hermes_swapface_batch")
        self.work_dir.mkdir(parents=True, exist_ok=True)

        self.source_face = download_if_url(source_face, self.work_dir / "inputs")
        self.target_dir = resolve_path(target_folder)
        self.filter_mode = filter_mode

        self.face_swapper_model = face_swapper_model
        self.face_swapper_pixel_boost = face_swapper_pixel_boost
        self.face_enhancer_model = face_enhancer_model
        self.frame_enhancer_model = frame_enhancer_model
        self.face_detector_model = face_detector_model
        self.execution_thread_count = execution_thread_count
        self.temp_frame_format = temp_frame_format

        # Determine output folder
        if output_dir:
            self.out_dir = resolve_path(output_dir)
        else:
            folder_name = self.target_dir.name
            timestamp_str = time.strftime("%Y%m%d_%H%M%S")
            self.out_dir = DEFAULT_OUTPUT_BASE / f"{folder_name}_{timestamp_str}"

        self.out_dir.mkdir(parents=True, exist_ok=True)

        # Stage directory via shared mount
        self.staging_dir = Path("/home/zen/workspace/output/swapface_batches/.staging")
        self.staging_dir.mkdir(parents=True, exist_ok=True)

    def prepare_container(self):
        """Ensure LXC container is running and stop Gradio to free GPU."""
        print(f"[*] Checking FaceFusion container ({LOCAL_FF_CONTAINER})...", file=sys.stderr)
        subprocess.run(["lxc", "start", LOCAL_FF_CONTAINER], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        print("[*] Freeing GPU VRAM: stopping FaceFusion Gradio service...", file=sys.stderr)
        subprocess.run(["lxc", "exec", LOCAL_FF_CONTAINER, "--", "systemctl", "stop", "facefusion.service"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["lxc", "exec", LOCAL_FF_CONTAINER, "--", "bash", "-c", "pkill -f 'facefusion.py run' 2>/dev/null; true"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(2)

    def restore_container(self):
        """Restart FaceFusion Gradio Web UI service."""
        print("[*] Restoring FaceFusion Gradio service...", file=sys.stderr)
        subprocess.run(["lxc", "exec", LOCAL_FF_CONTAINER, "--", "systemctl", "start", "facefusion.service"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def swap_single_file(self, target_file: Path, idx: int, total: int) -> Dict:
        """Execute face swap on a single target file."""
        t_start = time.time()
        tgt_name = target_file.name
        stem = target_file.stem
        ext = target_file.suffix

        out_name = f"swapped_{stem}{ext}"
        final_out_path = self.out_dir / out_name

        # Staging paths
        staged_src = self.staging_dir / f"src_{int(time.time()*1000)}{self.source_face.suffix}"
        staged_tgt = self.staging_dir / f"tgt_{int(time.time()*1000)}{ext}"

        shutil.copy2(self.source_face, staged_src)
        shutil.copy2(target_file, staged_tgt)

        # Paths inside container via shared mount
        src_in = f"/output/swapface_batches/.staging/{staged_src.name}"
        tgt_in = f"/output/swapface_batches/.staging/{staged_tgt.name}"
        
        # Relative path for container output
        rel_out = self.out_dir.relative_to(Path("/home/zen/workspace/output"))
        container_out = f"/output/{rel_out}/{out_name}"

        processors = ["face_swapper"]
        use_face_enhancer = bool(
            self.face_enhancer_model
            and str(self.face_enhancer_model).strip().lower() not in ("none", "null", "false", "off", "disable", "disabled", "")
        )
        if use_face_enhancer:
            processors.append("face_enhancer")
        if self.frame_enhancer_model:
            processors.append("frame_enhancer")

        proc_str = " ".join(processors)

        cmd_parts = [
            "cd /opt/facefusion &&",
            "/opt/facefusion/venv/bin/python facefusion.py headless-run",
            f"--processors {proc_str}",
            f"-s {src_in}",
            f"-t {tgt_in}",
            f"-o {container_out}",
            f"--face-swapper-model {self.face_swapper_model}",
            f"--face-swapper-pixel-boost {self.face_swapper_pixel_boost}",
            f"--face-detector-model {self.face_detector_model}",
            f"--temp-frame-format {self.temp_frame_format}",
            "--output-video-encoder libx264",
            "--output-video-preset fast",
            "--execution-providers cuda",
            f"--execution-thread-count {self.execution_thread_count}"
        ]

        if use_face_enhancer:
            cmd_parts.append(f"--face-enhancer-model {self.face_enhancer_model}")
        if self.frame_enhancer_model:
            cmd_parts.append(f"--frame-enhancer-model {self.frame_enhancer_model}")

        cmd = " ".join(cmd_parts)
        print(f"  [{idx:02d}/{total:02d}] Swapping {tgt_name} -> {out_name}...", file=sys.stderr)

        p = subprocess.run(["lxc", "exec", LOCAL_FF_CONTAINER, "--", "bash", "-c", cmd])

        # Cleanup staged inputs
        staged_src.unlink(missing_ok=True)
        staged_tgt.unlink(missing_ok=True)

        elapsed = time.time() - t_start

        if p.returncode == 0 and final_out_path.exists():
            file_size_mb = final_out_path.stat().st_size / (1024 * 1024)
            print(f"  [{idx:02d}/{total:02d}] ✅ Done {out_name} ({file_size_mb:.1f} MB, {elapsed:.1f}s)", file=sys.stderr)
            return {
                "index": idx,
                "target_file": tgt_name,
                "target_path": str(target_file),
                "output_file": out_name,
                "output_path": str(final_out_path),
                "file_size_mb": round(file_size_mb, 2),
                "duration_sec": round(elapsed, 1),
                "status": "success"
            }
        else:
            print(f"  [{idx:02d}/{total:02d}] ❌ Failed {tgt_name} (code {p.returncode})", file=sys.stderr)
            return {
                "index": idx,
                "target_file": tgt_name,
                "target_path": str(target_file),
                "output_file": out_name,
                "output_path": str(final_out_path),
                "file_size_mb": 0.0,
                "duration_sec": round(elapsed, 1),
                "status": "failed",
                "error_code": p.returncode
            }

    def run(self) -> Dict:
        """Run batch swapface on all target files in folder."""
        targets = find_target_files(self.target_dir, self.filter_mode)
        total = len(targets)

        if total == 0:
            return {
                "status": "empty",
                "message": f"No matching media files found in {self.target_dir} (filter: {self.filter_mode})",
                "target_directory": str(self.target_dir),
                "output_directory": str(self.out_dir),
                "total_files": 0,
                "succeeded": 0,
                "failed": 0,
                "results": []
            }

        print(f"\n========================================================", file=sys.stderr)
        print(f"🚀 Batch SwapFace starting: {total} files in {self.target_dir.name}", file=sys.stderr)
        print(f"📁 Target Folder : {self.target_dir}", file=sys.stderr)
        print(f"📁 Output Folder : {self.out_dir}", file=sys.stderr)
        print(f"🔍 Filter Mode   : {self.filter_mode}", file=sys.stderr)
        print(f"🧠 Face Swapper  : {self.face_swapper_model}", file=sys.stderr)
        if self.face_enhancer_model:
            print(f"✨ Face Enhancer : {self.face_enhancer_model}", file=sys.stderr)
        print(f"========================================================\n", file=sys.stderr)

        start_all = time.time()
        file_results = []

        try:
            self.prepare_container()
            for idx, tgt in enumerate(targets, start=1):
                res = self.swap_single_file(tgt, idx, total)
                file_results.append(res)
        finally:
            self.restore_container()

        total_elapsed = time.time() - start_all
        succeeded = [r for r in file_results if r["status"] == "success"]
        failed = [r for r in file_results if r["status"] == "failed"]

        # Write batch summary JSON
        summary = {
            "source_face": str(self.source_face),
            "target_directory": str(self.target_dir),
            "output_directory": str(self.out_dir),
            "filter_mode": self.filter_mode,
            "models_used": {
                "face_swapper": self.face_swapper_model,
                "face_enhancer": self.face_enhancer_model,
                "frame_enhancer": self.frame_enhancer_model,
                "face_detector": self.face_detector_model
            },
            "total_files": total,
            "succeeded": len(succeeded),
            "failed": len(failed),
            "total_duration_sec": round(total_elapsed, 1),
            "results": file_results
        }

        summary_json = self.out_dir / "batch_summary.json"
        with open(summary_json, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        return summary


def main():
    parser = argparse.ArgumentParser(description="SwapFace Target Folder Runner for Hermes Agent")
    parser.add_argument("--source", "-s", required=True, help="Path or URL to source face image")
    parser.add_argument("--target-folder", "--target-dir", "-t", required=True, help="Path to folder containing target videos/images")
    parser.add_argument("--filter", "-f", default="ok_only", choices=["ok_only", "all", "not_only"], help="Filter target files (default: ok_only)")
    parser.add_argument("--output-dir", "-o", default=None, help="Output directory (default: /output/swapface_batches/<folder_name>_<time>)")
    parser.add_argument("--face-swapper-model", default="inswapper_128_fp16", help="Face swapper model (inswapper_128_fp16, simswap_256, uniface_256, ghost_2_256)")
    parser.add_argument("--face-swapper-pixel-boost", default="128x128", help="Face swapper pixel boost resolution (128x128, 256x256, 512x512)")
    parser.add_argument("--face-enhancer-model", default="codeformer", help="Face enhancer model (default: codeformer; gfpgan_1.4, gpen_bfr_512. Use 'none' to disable)")
    parser.add_argument("--no-face-enhancer", action="store_true", help="Disable face enhancer")
    parser.add_argument("--frame-enhancer-model", default=None, help="Frame enhancer model (real_esrgan_x4, etc.)")
    parser.add_argument("--face-detector-model", default="yolo_face", help="Face detector model (yolo_face, retinaface, scrfd)")
    parser.add_argument("--execution-thread-count", type=int, default=4, help="Execution thread count (default: 4)")
    parser.add_argument("--temp-frame-format", default="bmp", choices=["bmp", "jpeg", "png"], help="Temp frame format (default: bmp)")
    parser.add_argument("--json", action="store_true", help="Output result as JSON")

    args = parser.parse_args()

    enhancer = None if args.no_face_enhancer else args.face_enhancer_model

    runner = FolderSwapFaceRunner(
        source_face=args.source,
        target_folder=args.target_folder,
        output_dir=args.output_dir,
        filter_mode=args.filter,
        face_swapper_model=args.face_swapper_model,
        face_swapper_pixel_boost=args.face_swapper_pixel_boost,
        face_enhancer_model=enhancer,
        frame_enhancer_model=args.frame_enhancer_model,
        face_detector_model=args.face_detector_model,
        execution_thread_count=args.execution_thread_count,
        temp_frame_format=args.temp_frame_format
    )

    summary = runner.run()

    if args.json:
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    else:
        print(f"\n========================================================")
        print(f"🎉 Batch SwapFace Completed!")
        print(f"========================================================")
        print(f"📁 Output Directory: {summary['output_directory']}")
        print(f"📊 Summary:")
        print(f"   - Total Targets : {summary['total_files']}")
        print(f"   - ✅ Succeeded   : {summary['succeeded']}")
        print(f"   - ❌ Failed      : {summary['failed']}")
        print(f"   - ⏱ Total Time   : {summary['total_duration_sec']}s")
        print(f"📄 Batch Report  : {summary['output_directory']}/batch_summary.json")
        print(f"========================================================")
        if summary.get("results"):
            print("\n🎬 Swapped Files:")
            for r in summary["results"]:
                status_icon = "✅" if r["status"] == "success" else "❌"
                print(f"  {status_icon} {r['output_file']} ({r.get('file_size_mb', 0)} MB, {r['duration_sec']}s)")
        print(f"========================================================\n")


if __name__ == "__main__":
    main()
