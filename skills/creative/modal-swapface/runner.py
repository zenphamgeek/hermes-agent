#!/usr/bin/env python3
"""
FaceFusion & Modal SwapFace Runner for Hermes Agent
===================================================
Executes high quality face swapping on LXC FaceFusion GPU Container (or Modal Cloud),
supporting rich model suites (InsightFace, SimSwap, CodeFormer, GFPGAN, GPEN, RealESRGAN)
with all outputs saved to /output (/home/zen/workspace/output).
"""

import os
import sys
import time
import json
import argparse
import subprocess
from pathlib import Path
from typing import Optional

DEFAULT_OUTPUT_DIR = Path("/home/zen/workspace/output/swapface")
LOCAL_FF_CONTAINER = "facefusion-ai"
DEFAULT_PROFILE = os.environ.get("MODAL_PROFILE", "motion")

def resolve_output_path(out_arg: Optional[str], ext: str = ".mp4") -> Path:
    """Resolve destination path to shared workspace /output directory."""
    if not out_arg:
        DEFAULT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        return DEFAULT_OUTPUT_DIR / f"swapped_{int(time.time())}{ext}"
    
    p = Path(out_arg)
    # If path starts with /output, remap to /home/zen/workspace/output
    if str(p).startswith("/output"):
        rel = str(p)[len("/output"):].lstrip("/")
        p = Path("/home/zen/workspace/output") / rel
    
    p.parent.mkdir(parents=True, exist_ok=True)
    return p

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
    
    p = Path(file_or_url).resolve()
    if not p.exists():
        raise FileNotFoundError(f"Input file not found: {file_or_url}")
    return p

def run_facefusion_lxc(
    source_file: Path,
    target_file: Path,
    output_file: Path,
    face_swapper_model: str = "inswapper_128",
    face_enhancer_model: Optional[str] = None,
    frame_enhancer_model: Optional[str] = None,
    face_detector_model: str = "retinaface"
) -> dict:
    """Execute real face swap via local LXD facefusion-ai GPU container with full model suites."""
    print(f"[*] Executing FaceFusion GPU container ({LOCAL_FF_CONTAINER})...", file=sys.stderr)
    
    # Ensure container is running
    subprocess.run(["lxc", "start", LOCAL_FF_CONTAINER], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Stop Gradio Web UI to free GPU exclusively for headless processing
    # (prevents GPU contention/deadlock when two FaceFusion processes share CUDA)
    print("[*] Stopping FaceFusion Gradio service to free GPU...", file=sys.stderr)
    subprocess.run(["lxc", "exec", LOCAL_FF_CONTAINER, "--", "systemctl", "stop", "facefusion.service"],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["lxc", "exec", LOCAL_FF_CONTAINER, "--", "bash", "-c", "pkill -f 'facefusion.py run' 2>/dev/null; true"],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2)
    
    # Stage inputs via shared /output mount (avoids lxc file push permission issues)
    import shutil
    staging_dir = Path("/home/zen/workspace/output/swapface/.staging")
    staging_dir.mkdir(parents=True, exist_ok=True)
    
    src_ext = source_file.suffix
    tgt_ext = target_file.suffix
    src_staged = staging_dir / f"source_in{src_ext}"
    tgt_staged = staging_dir / f"target_in{tgt_ext}"
    
    shutil.copy2(source_file, src_staged)
    shutil.copy2(target_file, tgt_staged)
    
    # Paths as seen from inside the container (via /output mount)
    src_in = f"/output/swapface/.staging/source_in{src_ext}"
    tgt_in = f"/output/swapface/.staging/target_in{tgt_ext}"

    # Output directly inside container /output mount
    out_fname = output_file.name
    container_out = f"/output/swapface/{out_fname}"

    processors = ["face_swapper"]
    if face_enhancer_model:
        processors.append("face_enhancer")
    if frame_enhancer_model:
        processors.append("frame_enhancer")

    proc_str = " ".join(processors)
    
    cmd_parts = [
        "cd /opt/facefusion &&",
        "/opt/facefusion/venv/bin/python facefusion.py headless-run",
        f"--processors {proc_str}",
        f"-s {src_in}",
        f"-t {tgt_in}",
        f"-o {container_out}",
        f"--face-swapper-model {face_swapper_model}",
        f"--face-detector-model {face_detector_model}",
        "--execution-providers cuda"
    ]
    
    if face_enhancer_model:
        cmd_parts.append(f"--face-enhancer-model {face_enhancer_model}")
    if frame_enhancer_model:
        cmd_parts.append(f"--frame-enhancer-model {frame_enhancer_model}")

    cmd = " ".join(cmd_parts)
    print(f"[*] Running command: {cmd}", file=sys.stderr)

    p = subprocess.run(["lxc", "exec", LOCAL_FF_CONTAINER, "--", "bash", "-c", cmd])
    
    # Because /output in container maps directly to /home/zen/workspace/output on host
    shared_host_file = Path("/home/zen/workspace/output/swapface") / out_fname
    
    # Restart Gradio Web UI after headless processing
    print("[*] Restarting FaceFusion Gradio service...", file=sys.stderr)
    subprocess.run(["lxc", "exec", LOCAL_FF_CONTAINER, "--", "systemctl", "start", "facefusion.service"],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    if p.returncode == 0 and shared_host_file.exists():
        # If user requested a custom destination path other than default shared folder, copy it
        if output_file.resolve() != shared_host_file.resolve():
            import shutil
            shutil.copy2(shared_host_file, output_file)

        return {
            "status": "success",
            "engine": "local_facefusion_cuda",
            "models_used": {
                "face_swapper": face_swapper_model,
                "face_enhancer": face_enhancer_model,
                "frame_enhancer": frame_enhancer_model,
                "face_detector": face_detector_model
            },
            "output_path": str(output_file),
            "file_size": output_file.stat().st_size if output_file.exists() else shared_host_file.stat().st_size
        }
    
    return {
        "status": "error",
        "engine": "local_facefusion",
        "output_path": str(output_file),
        "message": f"FaceFusion exited with code {p.returncode}"
    }

def main():
    parser = argparse.ArgumentParser(description="FaceFusion & Modal SwapFace Runner for Hermes Agent")
    parser.add_argument("--source", "-s", required=True, help="Path or URL to source face image")
    parser.add_argument("--target", "-t", required=True, help="Path or URL to target video/image")
    parser.add_argument("--output", "-o", default=None, help="Output path (default: /home/zen/workspace/output/swapface/...)")
    parser.add_argument("--face-swapper-model", default="inswapper_128", help="Face swapper model (inswapper_128, simswap_256, uniface_256, ghost_2_256, etc.)")
    parser.add_argument("--face-enhancer-model", default=None, help="Face enhancer model (codeformer, gfpgan_1.4, gpen_bfr_512, etc.)")
    parser.add_argument("--frame-enhancer-model", default=None, help="Frame enhancer model (real_esrgan_x4, nomos8k_sc_x4, etc.)")
    parser.add_argument("--face-detector-model", default="retinaface", help="Face detector model (retinaface, scrfd, yolo_face, yunet)")
    parser.add_argument("--profile", "-p", default=DEFAULT_PROFILE, help=f"Modal profile name (default: {DEFAULT_PROFILE})")
    parser.add_argument("--engine", choices=["local", "modal"], default="local", help="Execution engine (default: local LXC GPU)")
    parser.add_argument("--json", action="store_true", help="Print result as JSON")
    args = parser.parse_args()

    work_dir = Path("/tmp/hermes_swapface")
    work_dir.mkdir(parents=True, exist_ok=True)

    try:
        src = download_if_url(args.source, work_dir / "inputs")
        tgt = download_if_url(args.target, work_dir / "inputs")
        ext = tgt.suffix or ".mp4"
        out = resolve_output_path(args.output, ext)

        res = run_facefusion_lxc(
            source_file=src,
            target_file=tgt,
            output_file=out,
            face_swapper_model=args.face_swapper_model,
            face_enhancer_model=args.face_enhancer_model,
            frame_enhancer_model=args.frame_enhancer_model,
            face_detector_model=args.face_detector_model
        )

        if args.json:
            print(json.dumps(res, indent=2, ensure_ascii=False))
        else:
            if res.get("status") == "success":
                print(f"\n========================================================")
                print(f"✅ Hoàn thành hoán đổi khuôn mặt (FaceSwap)!")
                print(f"========================================================")
                print(f"🎬 File kết quả : {res.get('output_path')}")
                print(f"📁 Thư mục lưu  : /output/swapface ({out.parent})")
                print(f"⚡ Engine       : {res.get('engine')}")
                print(f"🧠 Models       : {res.get('models_used')}")
                print(f"📦 Dung lượng   : {res.get('file_size', 0) / (1024*1024):.2f} MB")
                print(f"========================================================")
            else:
                print(f"\n❌ Lỗi: {res.get('message', res.get('status'))}", file=sys.stderr)
                sys.exit(1)

    except Exception as e:
        err = {"status": "error", "error": str(e)}
        if args.json:
            print(json.dumps(err, ensure_ascii=False))
        else:
            print(f"❌ Lỗi: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
