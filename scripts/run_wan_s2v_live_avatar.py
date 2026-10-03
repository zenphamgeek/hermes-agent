#!/usr/bin/env python3
"""
scripts/run_wan_s2v_live_avatar.py
==================================
Dispatches Wan2.2-S2V-14B video generation to Modal A100-80GB Cloud Engine.
Uses master Ao Dai portrait and calibrated Vietnamese culture audio.
"""

import base64
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

ENDPOINT = "https://zenonmind--hermes-wan-s2v-api.modal.run/generate"
IMAGE_PATH = "/home/zen/hermes-agent/output/qwen_asian_girl_aodai_master_1024x1536.png"
AUDIO_PATH = "/home/zen/hermes-agent/output/vietnam_culture_intro_speech.wav"
OUTPUT_MP4 = "/home/zen/hermes-agent/output/wan22_s2v_aodai_vietnam_master.mp4"

def main():
    print("===================================================================")
    print(" 🎬 HERMES WAN 2.2 S2V LIVE AVATAR - MODAL A100 DISPATCH")
    print("===================================================================")

    if not os.path.exists(IMAGE_PATH):
        print(f"Error: Image not found at {IMAGE_PATH}")
        sys.exit(1)
    if not os.path.exists(AUDIO_PATH):
        print(f"Error: Audio not found at {AUDIO_PATH}")
        sys.exit(1)

    with open(IMAGE_PATH, "rb") as f:
        img_b64 = "data:image/png;base64," + base64.b64encode(f.read()).decode("utf-8")

    with open(AUDIO_PATH, "rb") as f:
        audio_b64 = "data:audio/wav;base64," + base64.b64encode(f.read()).decode("utf-8")

    payload = {
        "image": img_b64,
        "audio": audio_b64,
        "template": "shorts_vertical",
        "size": "704*1024",
        "sample_steps": 35,
        "guide_scale": 5.0,
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
        "seed": 42
    }

    print(f"Payload prepared:")
    print(f"- Image size: {len(img_b64)/(1024*1024):.2f} MB b64")
    print(f"- Audio size: {len(audio_b64)/(1024*1024):.2f} MB b64")
    print(f"- Target Resolution: 704*1024 -> 1080x1920 (9:16 Shorts Funnel)")
    print(f"- Sampling Steps: 35 | CFG: 5.0 | Seed: 42")
    print(f"- Endpoint: {ENDPOINT}")
    print("Sending POST request to Modal A100 Worker...")

    t0 = time.time()
    req_data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        ENDPOINT,
        data=req_data,
        headers={"Content-Type": "application/json", "User-Agent": "Hermes-Agent-Sovereign/1.0"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=1800) as resp:
            status = resp.status
            content_type = resp.headers.get("Content-Type")
            print(f"HTTP Response: {status} ({content_type})")
            video_bytes = resp.read()

        os.makedirs(os.path.dirname(OUTPUT_MP4), exist_ok=True)
        with open(OUTPUT_MP4, "wb") as f:
            f.write(video_bytes)

        elapsed = time.time() - t0
        mb_size = len(video_bytes) / (1024 * 1024)
        print(f"===================================================================")
        print(f" [✓] S2V Generation Succeeded in {elapsed:.1f}s ({elapsed/60:.2f} min)")
        print(f" [✓] Saved Output: {OUTPUT_MP4} ({mb_size:.2f} MB)")
        print(f"===================================================================")
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}: {e.reason}")
        error_body = e.read().decode("utf-8", errors="replace")
        print(f"Error details: {error_body[:1000]}")
        sys.exit(1)
    except Exception as e:
        print(f"Request failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
