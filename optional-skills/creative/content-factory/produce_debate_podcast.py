#!/usr/bin/env python3
"""
Produce & Publish: Multi-Voice Tech Debate Podcast Video for YouTube & Telegram.
Topic: "Autonomous Personal AI Agent 2026: Đột Phá Năng Suất Hay Nguy Cơ Bảo Mật?"
Speakers:
  1. Huệ Kỷ Nguyên (Host / Moderator)
  2. Tuấn Anh (Visionary / Proponent)
  3. Hoàng Đặng (Skeptic / Security Purist)
"""

import os
import sys
import json
import time
import subprocess
import urllib.request
import urllib.parse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUTPUT_DIR = Path.home() / "workspace" / "output" / "factory"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
STUDIO_DIR = Path(__file__).parent.parent / "video-motion-studio"
FACTORY_DIR = Path(__file__).parent
sys.path.insert(0, str(STUDIO_DIR))
sys.path.insert(0, str(FACTORY_DIR))

from motion_studio import VideoMotionStudio
from factory_runner import ContentFactory


def get_voice_clone_reference(voice_name: str) -> tuple:
    ref_audio_url = ""
    ref_text = ""
    try:
        import boto3
        s3 = boto3.client(
            "s3",
            endpoint_url="http://10.123.214.249:9000",
            aws_access_key_id="omnivoice-svc",
            aws_secret_access_key="omnivoice_svc_2026"
        )
        res = s3.list_objects_v2(Bucket="omnivoice-audio", Prefix="voices/")
        contents = res.get("Contents", [])
        target_key = None
        target_txt_key = None

        for item in contents:
            key = item["Key"]
            if voice_name.lower() in key.lower():
                if key.endswith((".mp3", ".wav", ".m4a", ".ogg")):
                    target_key = key
                elif key.endswith(".txt"):
                    target_txt_key = key

        if target_key:
            ref_audio_url = s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": "omnivoice-audio", "Key": target_key},
                ExpiresIn=3600
            )
        if target_txt_key:
            ref_text = s3.get_object(Bucket="omnivoice-audio", Key=target_txt_key)["Body"].read().decode("utf-8").strip()
    except Exception as e:
        print(f"[*] S3 voice lookup warning for '{voice_name}': {e}", file=sys.stderr)

    return ref_audio_url, ref_text


def synthesize_speaker_audio(text: str, voice_name: str, out_path: Path) -> bool:
    """Synthesize speaker line via OmniVoice Voice Clone on GPU, fallback to edge-tts."""
    # 1. Primary: OmniVoice GPU Voice Clone
    try:
        ref_audio_url, ref_text = get_voice_clone_reference(voice_name)
        payload = {
            "text": text,
            "lang": "vi",
            "normalize_vi": True,
            "ref_audio": ref_audio_url,
            "ref_text": ref_text,
            "speed": 1.0
        }
        req = urllib.request.Request(
            "http://10.123.214.178/tts/omnivoice",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=180) as resp:
            with open(out_path, "wb") as f:
                f.write(resp.read())
            if out_path.exists() and out_path.stat().st_size > 2000:
                print(f"    [✓] Voice Clone audio created for {voice_name[:15]}: {out_path.stat().st_size // 1024} KB")
                return True
    except Exception as e:
        print(f"[*] OmniVoice error for {voice_name[:15]}: {e}, falling back...", file=sys.stderr)

    # 2. Fallback: edge-tts
    try:
        edge_voice = "vi-VN-NamMinhNeural" if "hoàng" in voice_name.lower() or "tuấn" in voice_name.lower() else "vi-VN-HoaiMyNeural"
        res = subprocess.run([
            "edge-tts",
            "--text", text,
            "--write-media", str(out_path),
            "--voice", edge_voice
        ], capture_output=True, timeout=30)
        return res.returncode == 0 and out_path.exists()
    except Exception:
        return False


def main():
    factory = ContentFactory()
    studio = VideoMotionStudio()

    topic = "Autonomous Personal AI Agent 2026: Đột Phá Năng Suất Hay Nguy Cơ Bảo Mật?"
    print(f"[*] Starting Multi-Voice Debate Podcast Production: '{topic}'...")

    # 1. Generate Debate Script
    script = factory.generate_debate_podcast_script(topic)
    turns = script["turns"]
    print(f"[✓] Generated Debate Script with {len(turns)} dynamic turns.")

    rendered_scenes = []

    # 2. Render each Debate Turn
    for t_idx, turn in enumerate(turns, start=1):
        spk = turn["speaker"]
        voice = turn["voice"]
        txt = turn["text"]
        key_pt = turn["key_point"]
        role = "Host" if "huệ" in spk.lower() else ("Visionary" if "tuấn" in spk.lower() else "Skeptic")

        print(f"\n[*] Processing Turn {t_idx}/{len(turns)}: {spk} ({role})...")
        audio_path = OUTPUT_DIR / f"podcast_turn_{t_idx}.wav"
        scene_mp4 = OUTPUT_DIR / f"podcast_turn_{t_idx}.mp4"

        # Synthesize Speaker Audio
        print(f"  • Synthesizing Voice ({spk} - {voice[:25]})...")
        synthesize_speaker_audio(txt, voice, audio_path)

        # Render Split-Screen Studio Video with Active Speaker Glow & Waveform
        print(f"  • Rendering Studio Video Scene...")
        ok = studio.render_debate_studio_scene(
            topic=topic,
            speaker_name=spk,
            speaker_role=role,
            speech_text=txt,
            key_point=key_pt,
            audio_path=audio_path,
            output_path=scene_mp4
        )
        if ok and scene_mp4.exists():
            print(f"  [✓] Turn {t_idx} rendered: {scene_mp4} ({scene_mp4.stat().st_size // 1024} KB)")
            rendered_scenes.append(scene_mp4)

    # 3. Concatenate Full Podcast Video
    print("\n[*] Concatenating Full Debate Podcast Episode...")
    concat_list_file = OUTPUT_DIR / "podcast_concat_list.txt"
    with open(concat_list_file, "w", encoding="utf-8") as f:
        for vf in rendered_scenes:
            f.write(f"file '{vf}'\n")

    final_video = OUTPUT_DIR / "debate_podcast_final.mp4"
    cmd_concat = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_list_file),
        "-c:v", "libx264",
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        str(final_video)
    ]
    subprocess.run(cmd_concat, capture_output=True, check=True)
    print(f"[✓] Full Podcast Video Created: {final_video} ({final_video.stat().st_size // 1024} KB)")

    # 4. Generate High-Impact Podcast Thumbnail
    thumb_path = OUTPUT_DIR / "debate_podcast_thumb.jpg"
    studio.generate_tech_infographic(
        title="TECH DEBATE PODCAST 2026",
        subtitle="Autonomous AI Agent: Đột Phá Năng Suất Hay Nguy Cơ Bảo Mật?",
        nodes=[
            {"title": "Visionary", "desc": "Tự hành 100% qua IDE & Telegram", "badge": "TUẤN ANH"},
            {"title": "Skeptic", "desc": "Rủi ro rò rỉ Secret & Injection", "badge": "HOÀNG ĐẶNG"},
            {"title": "Zero-Trust", "desc": "Cô lập Sandbox trên ThinkPad P15", "badge": "GIẢI PHÁP"},
            {"title": "Moderator", "desc": "Phân tích đa chiều chuẩn 2026", "badge": "HUỆ HOST"}
        ],
        output_path=thumb_path
    )
    print(f"[✓] Podcast Thumbnail Created: {thumb_path}")


if __name__ == "__main__":
    main()
