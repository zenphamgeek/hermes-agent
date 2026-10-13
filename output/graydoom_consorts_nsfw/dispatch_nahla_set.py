#!/usr/bin/env python3
"""
output/graydoom_consorts_nsfw/dispatch_nahla_set.py
===================================================
Automated dispatcher to execute the 4-Scene Nahla NSFW Set across Modal / ComfyUI.

Features:
- Auto-uploads reference character identity image (nahla_source_identity.png) to ComfyUI input directory
- Submits 4 cinematic scenes to ComfyUI REST API
- Polls execution status via /history/{prompt_id}
- Auto-downloads resulting 2K/4K renders to output/graydoom_consorts_nsfw/renders/
"""

import sys
import os
import json
import time
import argparse
import urllib.request
import urllib.parse
from pathlib import Path

SCENES = [
    ("scene_01_boudoir_lace.json", "nahla_scene01_boudoir.png"),
    ("scene_02_imperial_bath.json", "nahla_scene02_bath.png"),
    ("scene_03_unveiled_reclining.json", "nahla_scene03_unveiled.png"),
    ("scene_04_morning_balcony.json", "nahla_scene04_balcony.png"),
]

DIR = Path(__file__).resolve().parent
RENDERS_DIR = DIR / "renders"
RENDERS_DIR.mkdir(parents=True, exist_ok=True)


def upload_reference_image(host: str, image_path: Path):
    """Uploads the character identity image to ComfyUI /upload/image endpoint."""
    if not image_path.exists():
        print(f"⚠️ [Upload] Warning: Image {image_path} does not exist.")
        return False

    url = f"{host.rstrip('/')}/upload/image"
    boundary = f"----WebKitFormBoundary{int(time.time()*1000)}"
    filename = image_path.name

    with open(image_path, "rb") as f:
        file_bytes = f.read()

    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="image"; filename="{filename}"\r\n'
        f"Content-Type: image/png\r\n\r\n"
    ).encode("utf-8") + file_bytes + (
        f"\r\n--{boundary}\r\n"
        f'Content-Disposition: form-data; name="overwrite"\r\n\r\n'
        f"true\r\n--{boundary}--\r\n"
    ).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
            print(f"📥 [Upload] Reference image '{filename}' uploaded successfully: {data.get('name')}")
            return True
    except Exception as e:
        print(f"⚠️ [Upload] Failed to upload reference image to {url}: {e}")
        return False


def dispatch_scene(host: str, scene_file: str) -> str:
    """Submits workflow graph to ComfyUI /prompt."""
    file_path = DIR / scene_file
    with open(file_path, "r", encoding="utf-8") as f:
        graph = json.load(f)

    clean_graph = {k: v for k, v in graph.items() if k != "_meta"}
    title = graph.get("_meta", {}).get("title", scene_file)
    print(f"🎬 [Queueing] {title}...")

    payload = json.dumps({"prompt": clean_graph, "client_id": f"nahla_set_{int(time.time())}"}).encode("utf-8")
    req = urllib.request.Request(
        f"{host.rstrip('/')}/prompt",
        data=payload,
        headers={"Content-Type": "application/json"}
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
            prompt_id = data.get("prompt_id")
            print(f"   ✅ Queued with Prompt ID: {prompt_id}")
            return prompt_id
    except Exception as e:
        print(f"   ⚠️ Submission error: {e}")
        return ""


def wait_and_download(host: str, prompt_id: str, output_name: str, max_wait_sec: int = 300):
    """Polls /history/{prompt_id} and saves the rendered image when completed."""
    if not prompt_id:
        return None

    print(f"⏳ Waiting for render (Prompt ID: {prompt_id})...")
    start = time.time()
    while time.time() - start < max_wait_sec:
        try:
            url = f"{host.rstrip('/')}/history/{prompt_id}"
            req = urllib.request.Request(url, headers={"User-Agent": "Hermes-Client"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())

            if prompt_id in data:
                history = data[prompt_id]
                outputs = history.get("outputs", {})
                for node_id, node_out in outputs.items():
                    images = node_out.get("images", [])
                    if images:
                        img_info = images[0]
                        filename = img_info.get("filename")
                        subfolder = img_info.get("subfolder", "")
                        img_type = img_info.get("type", "output")

                        # Download image
                        view_url = f"{host.rstrip('/')}/view?filename={urllib.parse.quote(filename)}&subfolder={urllib.parse.quote(subfolder)}&type={urllib.parse.quote(img_type)}"
                        dest_path = RENDERS_DIR / output_name

                        with urllib.request.urlopen(view_url, timeout=30) as view_resp:
                            with open(dest_path, "wb") as f_out:
                                f_out.write(view_resp.read())

                        print(f"🎉 [Render Complete] Saved to: {dest_path} ({dest_path.stat().st_size:,} bytes)")
                        return dest_path

                status = history.get("status", {})
                if status.get("status_str") == "error":
                    print(f"❌ Render failed with error: {status.get('messages')}")
                    return None
        except Exception:
            pass

        time.sleep(5.0)

    print(f"⏰ Timeout waiting for prompt {prompt_id}")
    return None


def main():
    parser = argparse.ArgumentParser(description="Dispatch Nahla NSFW 4-Scene Set")
    parser.add_argument("--host", type=str, default="http://127.0.0.1:8188", help="ComfyUI host URL")
    parser.add_argument("--wait", action="store_true", help="Wait and download rendered images")
    args = parser.parse_args()

    print("======================================================================")
    print("🔥 Starting Nahla NSFW 4-Scene Cinematic Set Dispatch")
    print(f"Target Host: {args.host}")
    print("======================================================================")

    # 1. Upload reference identity image
    ref_image = DIR / "nahla_source_identity.png"
    upload_reference_image(args.host, ref_image)

    # 2. Dispatch all scenes
    active_jobs = []
    for sc_file, out_name in SCENES:
        pid = dispatch_scene(args.host, sc_file)
        if pid:
            active_jobs.append((pid, out_name))
        time.sleep(1.0)

    print(f"\n✨ Successfully submitted {len(active_jobs)} scenes to {args.host}")

    # 3. Wait and download if requested
    if args.wait:
        for pid, out_name in active_jobs:
            wait_and_download(args.host, pid, out_name)


if __name__ == "__main__":
    main()
