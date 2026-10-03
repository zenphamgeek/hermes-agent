#!/usr/bin/env python3
"""
scripts/dispatch_wan_s2v_async_events.py
=========================================
Hermes Agent - Asynchronous GPU Event Stream Client for Wan2.2-S2V-14B.

Architecture:
1. Submits generation job asynchronously via POST /v1/jobs/generate -> HTTP 202 Accepted.
2. Captures real-time GPU progress events via SSE (Server-Sent Events) or status polling.
3. Completely decoupled: GPU task runs detached on Modal A100-80GB and never gets cancelled
   by client disconnects, timeouts, or sleep states.
4. Auto-downloads finished MP4 upon receiving the 'completed' event.
"""

import base64
import json
import os
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

API_BASE = "https://zenonmind--hermes-wan-s2v-api.modal.run"
IMAGE_PATH = "/home/zen/hermes-agent/output/qwen_asian_girl_aodai_master_1024x1536.png"
AUDIO_PATH = "/home/zen/hermes-agent/output/vietnam_culture_intro_speech.wav"
OUTPUT_MP4 = "/home/zen/hermes-agent/output/wan22_s2v_aodai_vietnam_master.mp4"


def submit_job(image_b64: str, audio_b64: str, sample_steps: int = 30) -> dict:
    url = f"{API_BASE}/v1/jobs/generate"
    payload = {
        "image": image_b64,
        "audio": audio_b64,
        "template": "shorts_vertical",
        "size": "704*1024",
        "sample_steps": sample_steps,
        "guide_scale": 5.0,
        "seed": 42,
        "prompt": (
            "A graceful Vietnamese young woman wearing an elegant white silk Ao Dai, "
            "speaking warmly and passionately about Vietnamese culture and heritage, "
            "gentle subtle head nodding, micro-smiles, authentic eye contact, "
            "warm cinematic key lighting, shallow depth of field, 8k ultra photorealistic"
        ),
        "negative_prompt": (
            "worst quality, blurry, distorted mouth, jittery lips, morphing teeth, "
            "eye drift, bad anatomy, frame flicker, low resolution, artifact"
        ),
        "upscale_1080p": True,
        "num_clip": 1,
    }

    req_bytes = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=req_bytes,
        headers={"Content-Type": "application/json", "User-Agent": "Hermes-Async-EventClient/1.0"},
        method="POST"
    )

    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def poll_job_events(job_id: str, max_wait_seconds: int = 7200):
    status_url = f"{API_BASE}/v1/jobs/{job_id}"
    print(f"\n📡 [Hermes GPU Event Stream] Listening for events on: {status_url}")
    print("-------------------------------------------------------------------")

    last_step = -1
    last_status = None
    t0 = time.time()

    while time.time() - t0 < max_wait_seconds:
        try:
            req = urllib.request.Request(status_url, headers={"User-Agent": "Hermes-Async-EventClient/1.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            status = data.get("status")
            step = data.get("step", 0)
            tot_step = data.get("total_steps", 30)
            progress = data.get("progress", 0.0)
            msg = data.get("message", "")
            speed = data.get("speed", "")
            rem = data.get("remaining", "")

            if step != last_step or status != last_status:
                last_step = step
                last_status = status
                timestamp = time.strftime("%H:%M:%S")
                if status == "running":
                    print(f"[{timestamp}] ⚡ [GPU EVENT] Step {step}/{tot_step} ({progress:.1f}%) | Speed: {speed} | ETA: {rem}")
                elif status == "completed":
                    print(f"[{timestamp}] 🎉 [GPU EVENT: COMPLETED] All {tot_step} steps rendered! Total duration: {data.get('duration_seconds', 0)}s")
                    return data
                elif status == "failed":
                    print(f"[{timestamp}] ❌ [GPU EVENT: FAILED] {data.get('error', 'Unknown error')}")
                    return data
                else:
                    print(f"[{timestamp}] ⏳ [GPU EVENT: {status.upper()}] {msg}")

        except Exception as e:
            # Temporary network blip, continue polling without failing
            print(f"[Heartbeat Warning] Transient connection blip ({e}), retrying...")

        time.sleep(3.0)

    raise TimeoutError(f"Job {job_id} exceeded maximum wait time of {max_wait_seconds}s")


def download_video(job_id: str, target_file: str):
    download_url = f"{API_BASE}/v1/jobs/{job_id}/download"
    print(f"\n📥 Downloading master video from: {download_url} -> {target_file}")
    req = urllib.request.Request(download_url, headers={"User-Agent": "Hermes-Async-EventClient/1.0"})
    
    with urllib.request.urlopen(req, timeout=120) as resp:
        video_bytes = resp.read()

    os.makedirs(os.path.dirname(os.path.abspath(target_file)), exist_ok=True)
    with open(target_file, "wb") as f:
        f.write(video_bytes)

    mb = len(video_bytes) / (1024 * 1024)
    print(f" [✓] Download complete: {target_file} ({mb:.2f} MB)")


def main():
    print("===================================================================")
    print(" 🎬 HERMES WAN 2.2 S2V - ASYNCHRONOUS GPU EVENT DISPATCHER")
    print("===================================================================")

    if not os.path.exists(IMAGE_PATH):
        print(f"Error: Image not found at {IMAGE_PATH}")
        sys.exit(1)
    if not os.path.exists(AUDIO_PATH):
        print(f"Error: Audio not found at {AUDIO_PATH}")
        sys.exit(1)

    if len(sys.argv) > 1 and sys.argv[1].startswith("wan_s2v_"):
        job_id = sys.argv[1]
        print(f"\n[✓] Attaching to existing in-flight Job: {job_id}")
        print(f" - Status URL   : {API_BASE}/v1/jobs/{job_id}")
        print(f" - Events URL   : {API_BASE}/v1/jobs/{job_id}/events")
        print(f" - Download URL : {API_BASE}/v1/jobs/{job_id}/download")
    else:
        print("Encoding assets to Base64...")
        with open(IMAGE_PATH, "rb") as f:
            img_b64 = "data:image/png;base64," + base64.b64encode(f.read()).decode("utf-8")
        with open(AUDIO_PATH, "rb") as f:
            audio_b64 = "data:audio/wav;base64," + base64.b64encode(f.read()).decode("utf-8")

        print(f"Submitting job asynchronously to {API_BASE}/v1/jobs/generate ...")
        resp = submit_job(img_b64, audio_b64, sample_steps=30)
        job_id = resp["job_id"]
        print(f"\n[✓] Job Accepted: {job_id}")
        print(f" - Status URL   : {API_BASE}{resp['status_url']}")
        print(f" - Events URL   : {API_BASE}{resp['events_url']}")
        print(f" - Download URL : {API_BASE}{resp['download_url']}")

    # Listen for GPU events
    result = poll_job_events(job_id)
    if result.get("status") == "completed":
        download_video(job_id, OUTPUT_MP4)
        print("\n===================================================================")
        print(f" 🚀 S2V LIVE AVATAR PIPELINE FULLY DELIVERED: {OUTPUT_MP4}")
        print("===================================================================")
    else:
        print(f"\nPipeline failed: {result}")
        sys.exit(1)


if __name__ == "__main__":
    main()
