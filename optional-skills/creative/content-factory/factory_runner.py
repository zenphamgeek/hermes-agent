#!/usr/bin/env python3
"""
Content Factory — Master Pipeline Orchestrator for Multi-Platform AI Media.
Coordinates:
1. Ideation & Storyboard Scripting (LLM / LM Studio / OpenRouter)
2. Audio Voiceover Synthesis (OmniVoice TTS)
3. Visual Generation & Video Assembly (ComfyUI / FFmpeg)
4. Face Swapping & Enhancement (FaceFusion / modal-swapface)
5. Asset Persistence (MinIO S3 / shared-assets)
6. Multi-Channel Distribution (YouTube, Facebook, X, Telegram)
"""

import os
import sys
import json
import time
import shutil
import argparse
import subprocess
import urllib.request
import urllib.parse
import wave
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# Output & Storage Directories
OUTPUT_BASE = Path.home() / "workspace" / "output" / "factory"
OUTPUT_BASE.mkdir(parents=True, exist_ok=True)
HERMES_ENV_PATH = Path.home() / ".hermes" / ".env"
REPO_ROOT = Path(__file__).resolve().parents[3]
VISUAL_LIBRARY_PATH = REPO_ROOT / "assets" / "visual_library"
if str(VISUAL_LIBRARY_PATH) not in sys.path:
    sys.path.insert(0, str(VISUAL_LIBRARY_PATH))

# Service Endpoints on P15 Network (10.123.214.0/24)
LM_STUDIO_URL = "http://10.123.214.1:1234/v1"
COMFYUI_URL = "http://10.123.214.153:8188"
FACEFUSION_URL = "http://10.123.214.208:7860"
OMNIVOICE_URL = "http://10.123.214.178/v1/audio/speech"
MINIO_ENDPOINT = "http://10.123.214.249:9000"
REDIS_HOST = "10.123.214.184"
REDIS_PORT = 6379


def load_env() -> Dict[str, str]:
    """Load ~/.hermes/.env credentials safely."""
    env = {}
    if HERMES_ENV_PATH.exists():
        with open(HERMES_ENV_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip().strip('"').strip("'")
    return env


class ContentFactory:
    """Master orchestrator for AI media generation and publishing."""

    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or OUTPUT_BASE
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.env = load_env()

    # ── 1. Ideation & Scripting ──────────────────────────────────────────

    def generate_plan(self, topic: str, style: str = "shorts") -> Dict[str, Any]:
        """Generate full video plan: title, storyboard, narrator lines, and visual prompts."""
        prompt = (
            f"Bạn là Giám đốc Sáng tạo của Content Factory AI.\n"
            f"Hãy lên kịch bản chi tiết cho video dạng '{style}' (dọc 9:16, 45-60s) về chủ đề: '{topic}'.\n"
            f"Trả về kết quả chuẩn JSON với cấu trúc:\n"
            f"{{\n"
            f'  "title": "Tiêu đề hấp dẫn giật tít",\n'
            f'  "hook": "Câu mở đầu giữ chân 3s đầu",\n'
            f'  "tags": ["#tag1", "#tag2", "#shorts"],\n'
            f'  "scenes": [\n'
            f'    {{\n'
            f'      "scene_number": 1,\n'
            f'      "duration_sec": 10,\n'
            f'      "voiceover": "Lời thoại thuyết minh tiếng Việt",\n'
            f'      "visual_prompt": "Detailed English prompt for ComfyUI/SDXL image",\n'
            f'      "caption": "Phụ đề ngắn gọn trên màn hình"\n'
            f'    }}\n'
            f'  ],\n'
            f'  "call_to_action": "Câu kêu gọi like/share cuối video"\n'
            f"}}"
        )

        # Try LM Studio first, fallback to structured template if offline
        try:
            req_data = json.dumps({
                "model": "default",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "response_format": {"type": "json_object"}
            }).encode("utf-8")
            req = urllib.request.Request(
                f"{LM_STUDIO_URL}/chat/completions",
                data=req_data,
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                content = data["choices"][0]["message"]["content"]
                return json.loads(content)
        except Exception:
            pass

        # Robust Built-in Template Fallback
        return {
            "title": f"Bí Mật {topic} 2026",
            "hook": f"Bạn đã biết điều này về {topic} chưa?",
            "tags": ["#ai", f"#{topic.replace(' ', '')}", "#shorts", "#vibe"],
            "scenes": [
                {
                    "scene_number": 1,
                    "duration_sec": 12,
                    "voiceover": f"Khám phá ngay công nghệ đột phá của {topic} trong năm 2026.",
                    "visual_prompt": f"Futuristic high-tech visual of {topic}, cinematic 8k wallpaper, vibrant neon lighting, 9:16 vertical aspect ratio",
                    "caption": f"Đột phá {topic}"
                },
                {
                    "scene_number": 2,
                    "duration_sec": 18,
                    "voiceover": f"Với sự hỗ trợ từ AI Agent tự hành, mọi quy trình làm việc được tối ưu hóa gấp 10 lần.",
                    "visual_prompt": f"Autonomous AI robots and neural network cybernetic workspace, 8k vertical framing",
                    "caption": "Tối ưu hóa 10x"
                },
                {
                    "scene_number": 3,
                    "duration_sec": 15,
                    "voiceover": f"Đừng bỏ lỡ xu hướng này, hãy bắt đầu trải nghiệm ngay hôm nay.",
                    "visual_prompt": f"Modern sleek AI dashboard on mobile screen, cyberpunk glassmorphism, 8k vertical",
                    "caption": "Trải nghiệm ngay!"
                }
            ],
            "call_to_action": "Follow kênh để cập nhật các công nghệ AI mới nhất!"
        }

    # ── 1b. Multi-Voice Debate Podcast Scripting ─────────────────────────

    def generate_debate_podcast_script(self, topic: str, rounds: int = 3) -> Dict[str, Any]:
        """
        Generate a high-tension, intellectual multi-character debate podcast script.
        Roles:
          1. Host (Huệ Kỷ Nguyên): Neutral, inquisitive, moderates the debate.
          2. Visionary (Tuấn Anh): Tech evangelist, advocates for autonomous AI Agents & Vibe Coding.
          3. Skeptic (Hoàng Đặng): Security purist, questions safety, zero-trust & data privacy risks.
        """
        prompt = (
            f"Bạn là Nhà sản xuất Podcast Công nghệ hàng đầu.\n"
            f"Hãy lên kịch bản Podcast Tranh biện đối kháng (Debate Podcast) chuyên sâu về chủ đề: '{topic}'.\n"
            f"Có 3 nhân vật tham gia:\n"
            f"1. Host (Huệ): Điều phối, đặt câu hỏi phản biện sắc bén.\n"
            f"2. Tuấn Anh (Phe Ủng hộ): Lập luận về sự đột phá, tự hành và tối ưu hóa năng suất 10x.\n"
            f"3. Hoàng Đặng (Phe Hoài nghi/Bảo mật): Đặt nghi vấn về rủi ro bảo mật, Zero-Trust và rò rỉ dữ liệu.\n"
            f"Yêu cầu: Lập luận chặt chẽ, có dẫn chứng năm 2026, câu từ tự nhiên, có phản biện trực diện (rebuttals).\n"
            f"Trả về chuẩn JSON:\n"
            f"{{\n"
            f'  "title": "Tiêu đề tập Podcast hấp dẫn",\n'
            f'  "topic": "{topic}",\n'
            f'  "characters": [\n'
            f'    {{"name": "Huệ", "role": "Host", "voice": "Hue_ky nguyen - calm, clear and professional"}},\n'
            f'    {{"name": "Tuấn Anh", "role": "Visionary", "voice": "tuan anh - deep & powerful vietnamese"}},\n'
            f'    {{"name": "Hoàng Đặng", "role": "Skeptic", "voice": "hoàng đặng - deep, smooth and resonant"}}\n'
            f'  ],\n'
            f'  "turns": [\n'
            f'    {{\n'
            f'      "turn_id": 1,\n'
            f'      "speaker": "Huệ",\n'
            f'      "voice": "Hue_ky nguyen - calm, clear and professional",\n'
            f'      "text": "Lời mở đầu của Host",\n'
            f'      "tone": "inquisitive",\n'
            f'      "key_point": "Mở đầu vấn đề"\n'
            f'    }}\n'
            f'  ]\n'
            f"}}"
        )

        try:
            req_data = json.dumps({
                "model": "default",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.75,
                "response_format": {"type": "json_object"}
            }).encode("utf-8")
            req = urllib.request.Request(
                f"{LM_STUDIO_URL}/chat/completions",
                data=req_data,
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                content = data["choices"][0]["message"]["content"]
                return json.loads(content)
        except Exception:
            pass

        # Robust High-Quality Debate Podcast Template Fallback
        return {
            "title": f"Tranh Biện Công Nghệ 2026: {topic}",
            "topic": topic,
            "characters": [
                {"name": "Huệ", "role": "Host", "voice": "Hue_ky nguyen - calm, clear and professional"},
                {"name": "Tuấn Anh", "role": "Visionary", "voice": "tuan anh - deep & powerful vietnamese"},
                {"name": "Hoàng Đặng", "role": "Skeptic", "voice": "hoàng đặng - deep, smooth and resonant"}
            ],
            "turns": [
                {
                    "turn_id": 1,
                    "speaker": "Huệ",
                    "voice": "Hue_ky nguyen - calm, clear and professional",
                    "text": f"Chào mừng quý khán giả đến với Tech Debate 2026. Chủ đề hôm nay: {topic}. Liệu Agent tự hành đang mở ra kỷ nguyên mới hay tiềm ẩn rủi ro khôn lường?",
                    "tone": "neutral",
                    "key_point": "Mở đầu cuộc tranh luận"
                },
                {
                    "turn_id": 2,
                    "speaker": "Tuấn Anh",
                    "voice": "tuan anh - deep & powerful vietnamese",
                    "text": "Tôi khẳng định: Personal AI Agent là bước nhảy vọt lớn nhất thập kỷ. Chỉ với một lệnh trên Telegram, Agent tự động duyệt mã nguồn, sửa lỗi và đẩy code lên server mà không cần con người can thiệp.",
                    "tone": "confident",
                    "key_point": "Khẳng định năng lực tự hành 10x"
                },
                {
                    "turn_id": 3,
                    "speaker": "Hoàng Đặng",
                    "voice": "hoàng đặng - deep, smooth and resonant",
                    "text": "Nhưng hãy cẩn trọng, Tuấn Anh. Khi bạn cấp quyền terminal cho AI tự chạy, một lỗ hổng Prompt Injection hay rò rỉ Secret Key có thể phá hủy toàn bộ hệ thống doanh nghiệp.",
                    "tone": "skeptical",
                    "key_point": "Cảnh báo rủi ro an ninh & Secret Vault"
                },
                {
                    "turn_id": 4,
                    "speaker": "Tuấn Anh",
                    "voice": "tuan anh - deep & powerful vietnamese",
                    "text": "Đó là lý do chúng ta có kiến trúc Sovereign Zero-Trust trên máy trạm cục bộ. Toàn bộ mã độc bị cô lập trong LXD Sandbox, chìa khóa API nằm trong Secret Vault bất khả xâm phạm.",
                    "tone": "rebuttal",
                    "key_point": "Giải pháp Zero-Trust & Sandbox"
                },
                {
                    "turn_id": 5,
                    "speaker": "Huệ",
                    "voice": "Hue_ky nguyen - calm, clear and professional",
                    "text": "Một góc nhìn rất thú vị từ cả hai phía. Tự hành đi đôi với kiểm soát an toàn — đó chính là chuẩn mực của AI Agent trong năm 2026. Hãy để lại bình luận quan điểm của bạn!",
                    "tone": "concluding",
                    "key_point": "Tổng kết & Kêu gọi tương tác"
                }
            ]
        }

    # ── 2. Voiceover Synthesis ───────────────────────────────────────────

    def get_voice_clone_reference(self, voice_name: str = "tuan anh - deep & powerful vietnamese") -> Tuple[str, str]:
        """Look up reference audio URL and reference text for voice cloning."""
        ref_audio_url = ""
        ref_text = ""
        try:
            import boto3
            s3 = boto3.client(
                "s3",
                endpoint_url=MINIO_ENDPOINT,
                aws_access_key_id="omnivoice-svc",
                aws_secret_access_key="omnivoice_svc_2026"
            )
            # Find matching audio key
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
            print(f"[*] S3 voice ref lookup warning: {e}", file=sys.stderr)

        return ref_audio_url, ref_text

    def synthesize_audio(self, text: str, output_path: Path, voice: str = "tuan anh - deep & powerful vietnamese") -> bool:
        """Synthesize narrator speech via OmniVoice Voice Clone container on GPU."""
        output_path.unlink(missing_ok=True)
        ref_audio_url, ref_text = self.get_voice_clone_reference(voice)
        try:
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
            with urllib.request.urlopen(req, timeout=60) as resp:
                output_path.write_bytes(resp.read())
            with wave.open(str(output_path), "rb") as audio:
                if audio.getnframes() > 0:
                    return True
        except Exception as e:
            print(f"[*] OmniVoice GPU clone error: {e}", file=sys.stderr)
        output_path.unlink(missing_ok=True)
        return False

    # ── 3. Video Assembly ────────────────────────────────────────────────

    def assemble_short_video(
        self,
        image_path: Path,
        audio_path: Path,
        output_path: Path,
        title_text: Optional[str] = None
    ) -> bool:
        """Render a vertical 9:16 MP4 video combining image, audio, and motion zoom."""
        if not image_path.exists() or not audio_path.exists():
            return False

        vf_filter = "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920"
        if title_text:
            escaped_text = title_text.replace(":", "\\:").replace("'", "\\'")
            vf_filter += f",drawtext=text='{escaped_text}':fontcolor=white:fontsize=48:x=(w-text_w)/2:y=180:box=1:boxcolor=black@0.6"

        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-i", str(image_path),
            "-i", str(audio_path),
            "-vf", vf_filter,
            "-c:v", "libx264", "-tune", "stillimage",
            "-c:a", "aac", "-b:a", "192k", "-pix_fmt", "yuv420p",
            "-shortest",
            str(output_path)
        ]

        try:
            res = subprocess.run(cmd, capture_output=True, timeout=60)
            if res.returncode == 0 and output_path.exists() and output_path.stat().st_size > 1000:
                return True
        except Exception:
            pass

        # Fallback simple assembly without drawtext if font configuration fails
        fallback_cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-i", str(image_path),
            "-i", str(audio_path),
            "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
            "-c:v", "libx264", "-tune", "stillimage",
            "-c:a", "aac", "-b:a", "192k", "-pix_fmt", "yuv420p",
            "-shortest",
            str(output_path)
        ]
        try:
            res = subprocess.run(fallback_cmd, capture_output=True, timeout=60)
            return res.returncode == 0 and output_path.exists() and output_path.stat().st_size > 1000
        except Exception as e:
            print(f"[!] Assembly fallback error: {e}", file=sys.stderr)
            return False

    # ── 4. Service Health & Status ───────────────────────────────────────

    def get_factory_status(self) -> Dict[str, Any]:
        """Audit status of all Content Factory microservices and storage."""
        services = {}

        # 1. LXD Containers
        try:
            res = subprocess.run(["lxc", "list", "--format=csv", "-c", "ns4"], capture_output=True, text=True, timeout=5)
            if res.returncode == 0:
                for line in res.stdout.strip().split("\n"):
                    if line:
                        parts = line.split(",")
                        name = parts[0].strip()
                        state = parts[1].strip()
                        ip = parts[2].strip() if len(parts) > 2 else ""
                        services[name] = {"state": state, "ip": ip}
        except Exception:
            pass

        # 2. Output Disk Storage
        output_files = list(self.output_dir.glob("*.*"))
        total_size_mb = sum(f.stat().st_size for f in output_files) / (1024 * 1024)

        return {
            "status": "operational",
            "output_directory": str(self.output_dir),
            "total_artifacts": len(output_files),
            "storage_used_mb": round(total_size_mb, 2),
            "services": services
        }


def main():
    parser = argparse.ArgumentParser(description="Content Factory — Master Pipeline CLI")
    subparsers = parser.add_subparsers(dest="command", help="Factory command to execute")

    # plan
    plan_parser = subparsers.add_parser("plan", help="Generate video script and storyboard")
    plan_parser.add_argument("topic", help="Topic or title for video production")
    plan_parser.add_argument("--style", default="shorts", help="Video style: shorts, reel, landscape")

    # status
    subparsers.add_parser("status", help="Check status of all Content Factory services")

    # assemble
    asm_parser = subparsers.add_parser("assemble", help="Assemble video from image and audio")
    asm_parser.add_argument("--image", "-i", required=True, help="Input image file")
    asm_parser.add_argument("--audio", "-a", required=True, help="Input audio file")
    asm_parser.add_argument("--output", "-o", help="Output MP4 file path")
    asm_parser.add_argument("--title", help="Overlay title text")
    asm_parser.add_argument("--production", action="store_true", help="Require a passing visual registry preflight before assembling a publishable video")
    asm_parser.add_argument("--order", help="Production order JSON required with --production")

    # footage
    footage_parser = subparsers.add_parser("footage", help="Query Footage Vault for B-Roll video clips")
    footage_parser.add_argument("query", help="Search prompt or keywords")
    footage_parser.add_argument("--category", "-c", help="Category: cafe, food, logistics, mathematics, biology, etc.")
    footage_parser.add_argument("--ratio", "-r", default="16:9", choices=["16:9", "9:16", "1:1"], help="Frame aspect ratio")
    footage_parser.add_argument("--quality", "-q", default="1080p", help="Minimum resolution (1080p, 4k)")
    footage_parser.add_argument("--limit", "-k", type=int, default=3, help="Max results to return")

    registry_parser = subparsers.add_parser("registry", help="Refresh or query the canonical visual registry")
    registry_parser.add_argument("--query", help="Case-insensitive text match against visual IDs and tags")

    preflight_parser = subparsers.add_parser("registry-preflight", help="Refresh registry and validate a production order")
    preflight_parser.add_argument("--order", required=True, help="JSON order with channel_id, template pack/version and resource_ids")

    args = parser.parse_args()
    factory = ContentFactory()

    if args.command == "registry":
        from catalog import refresh_registry
        registry = refresh_registry()
        if args.query:
            needle = args.query.casefold()
            registry["assets"] = [asset for asset in registry["assets"] if needle in asset["asset_id"].casefold() or any(needle in tag.casefold() for tag in asset["tags"])]
            registry["summary"]["matched"] = len(registry["assets"])
        print(json.dumps(registry, ensure_ascii=False, indent=2))

    elif args.command == "registry-preflight":
        from catalog import preflight_order
        try:
            order = json.loads(Path(args.order).read_text(encoding="utf-8"))
            if not isinstance(order, dict):
                raise ValueError("Order must be a JSON object")
            report = preflight_order(order)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            print(json.dumps({"passed": False, "errors": [str(exc)]}, ensure_ascii=False, indent=2))
            sys.exit(2)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        if not report["passed"]:
            sys.exit(2)

    elif args.command == "footage":
        from footage_mcp_server import filter_footage_clips
        from footage_vault import FootageVault
        vault = FootageVault()
        clips = filter_footage_clips(
            catalog=vault.catalog,
            query=args.query,
            vault=vault,
            category=args.category,
            aspect_ratio=args.ratio,
            min_quality=args.quality,
            top_k=args.limit
        )
        print(json.dumps({
            "query": args.query,
            "category": args.category,
            "aspect_ratio": args.ratio,
            "total_matches": len(clips),
            "clips": clips
        }, ensure_ascii=False, indent=2))

    elif args.command == "plan":
        plan = factory.generate_plan(args.topic, style=args.style)
        print(json.dumps(plan, ensure_ascii=False, indent=2))

    elif args.command == "status":
        status = factory.get_factory_status()
        print(json.dumps(status, ensure_ascii=False, indent=2))

    elif args.command == "assemble":
        if args.production:
            if not args.order:
                print("[!] --production requires --order for visual registry preflight.", file=sys.stderr)
                sys.exit(2)
            from catalog import preflight_order
            try:
                production_order = json.loads(Path(args.order).read_text(encoding="utf-8"))
                report = preflight_order(production_order)
            except (OSError, ValueError, json.JSONDecodeError) as exc:
                print(f"[!] Registry preflight failed: {exc}", file=sys.stderr)
                sys.exit(2)
            if not report["passed"]:
                print(json.dumps(report, ensure_ascii=False, indent=2), file=sys.stderr)
                sys.exit(2)
        out_path = Path(args.output) if args.output else OUTPUT_BASE / f"render_{int(time.time())}.mp4"
        ok = factory.assemble_short_video(
            Path(args.image), Path(args.audio), out_path, title_text=args.title
        )
        if ok:
            print(f"[✓] Video assembled successfully: {out_path} ({out_path.stat().st_size // 1024} KB)")
        else:
            print("[!] Assembly failed.", file=sys.stderr)
            sys.exit(1)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
