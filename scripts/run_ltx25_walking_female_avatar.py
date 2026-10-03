#!/usr/bin/env python3
"""
scripts/run_ltx25_walking_female_avatar.py
==========================================
Generates a long (8.7s) cinematic walking Live Avatar of a Vietnamese woman
in Ao Dai stepping forward towards the camera with female voiceover (Đoan Trang).
Runs 100% on Modal Cloud A100 GPU (0% local GPU compute).
"""

import base64
import json
import os
import sys
import subprocess
import time
import urllib.request
import urllib.error

ENDPOINT = "https://mojopham--hermes-neural-ltxvideo-api.modal.run/generate"
IMAGE_PATH = "/home/zen/hermes-agent/output/qwen_aodai_input_576x1024.png"
AUDIO_PATH = "/home/zen/hermes-agent/output/female_doan_trang_vietnam_speech.wav"
RAW_VIDEO = "/home/zen/hermes-agent/output/ltx25_walking_female_raw.mp4"
MASTER_MP4 = "/home/zen/hermes-agent/output/ltx25_walking_female_aodai_master.mp4"


def main():
    print("===================================================================")
    print(" 🎬 HERMES LTX-2.5 CINEMATIC WALKING LIVE AVATAR (MODAL A100)")
    print("===================================================================")

    if not os.path.exists(IMAGE_PATH):
        print(f"Error: Image not found at {IMAGE_PATH}")
        sys.exit(1)
    if not os.path.exists(AUDIO_PATH):
        print(f"Error: Audio not found at {AUDIO_PATH}")
        sys.exit(1)

    print("Encoding master image to Base64...")
    with open(IMAGE_PATH, "rb") as f:
        img_b64 = "data:image/png;base64," + base64.b64encode(f.read()).decode("utf-8")

    payload = {
        "prompt": (
            "Medium shot, camera smoothly dollying backward at matching speed, "
            "keeping the graceful Vietnamese young woman in royal blue and gold Ao Dai perfectly centered in frame "
            "from head to waist throughout the entire duration. "
            "She takes slow, elegant, graceful steps forward along the ancient temple courtyard walkway towards the camera, "
            "walking with gentle pacing, smiling warmly, speaking expressively, head nodding gently, "
            "perfectly framed, never clipping into camera lens, warm golden hour cinematic lighting, shallow depth of field, 8k photorealistic"
        ),
        "image": img_b64,
        "negative_prompt": (
            "walking out of frame, walking into camera lens, lens collision, extreme close up, "
            "face cut off, clipping, out of frame, distorted anatomy, blurry, jitter, low quality, "
            "morphing, frame flicker, cartoon, 3d render"
        ),
        "duration_sec": 8.7,
        "fps": 24,
        "width": 576,
        "height": 1024,
        "num_inference_steps": 30,
        "guidance_scale": 3.5,
        "seed": 101
    }

    print(f"Sending generation request to Modal LTX-Video-2.5 A100 endpoint...")
    print(f" - Endpoint : {ENDPOINT}")
    print(f" - Duration : 8.7s (209 frames @ 24fps)")
    print(f" - Dimension: 576x1024 (Vertical 9:16 Shorts)")
    print(f" - Voiceover: Female (Đoan Trang, 8.56s)")
    print(f" - Action   : Walking gracefully forward towards camera ('có đi đến')")

    req = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "User-Agent": "Hermes-LTX-WalkingAvatar/1.0"
        },
        method="POST"
    )

    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=600) as resp:
            video_bytes = resp.read()
            elapsed = time.time() - t0
            print(f"\n[✓] Video successfully generated on Modal Cloud A100 in {elapsed:.2f}s!")
            print(f" - Received: {len(video_bytes) / (1024*1024):.2f} MB")
            
            with open(RAW_VIDEO, "wb") as f:
                f.write(video_bytes)
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}: {e.read().decode('utf-8')}")
        sys.exit(1)
    except Exception as e:
        print(f"Connection error: {e}")
        sys.exit(1)

    print("\nMuxing video with 48kHz female speech voiceover...")
    cmd = [
        "ffmpeg", "-y",
        "-i", RAW_VIDEO,
        "-i", AUDIO_PATH,
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        MASTER_MP4
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"FFmpeg muxing error: {res.stderr}")
        sys.exit(1)

    mb = os.path.getsize(MASTER_MP4) / (1024 * 1024)
    print(f"\n===================================================================")
    print(f" 🚀 MASTER LIVE AVATAR DELIVERED: {MASTER_MP4} ({mb:.2f} MB)")
    print("===================================================================")


if __name__ == "__main__":
    main()
