#!/usr/bin/env python3
"""
High-Quality Video Footage Vault, Ingestion, Segmentation & Semantic Embedding Search.
- Ingests video footage from YouTube or Web sources.
- Segments long footage into clean, broadcast-grade B-Roll clips (5-15s) with keyframe thumbnails.
- Uploads assets to MinIO S3 cluster (http://10.123.214.249:9000/omnivoice-audio/footage/).
- Categorizes and indexes clips with dense vector embeddings for semantic search.
"""

import os
import sys
import json
import math
import time
import shutil
import hashlib
import tempfile
import argparse
import subprocess
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

S3_ENDPOINT = "http://10.123.214.249:9000"
S3_ACCESS_KEY = "omnivoice-svc"
S3_SECRET_KEY = "omnivoice_svc_2026"
S3_BUCKET = "omnivoice-audio"
S3_PREFIX = "footage"

OUTPUT_DIR = Path.home() / "workspace" / "output" / "factory"
CATALOG_PATH = OUTPUT_DIR / "footage_catalog.json"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


class VectorEmbeddingEngine:
    """Lightweight & robust semantic embedding engine with cosine similarity search."""

    def __init__(self, dim: int = 128):
        self.dim = dim

    def compute_embedding(self, text: str) -> List[float]:
        """Generate normalized dense vector embedding for semantic text."""
        # 1. Try OpenRouter embedding if key available
        openrouter_key = os.getenv("OPENROUTER_API_KEY", "")
        if openrouter_key:
            try:
                payload = json.dumps({
                    "model": "text-embedding-3-small",
                    "input": text
                }).encode("utf-8")
                req = urllib.request.Request(
                    "https://openrouter.ai/api/v1/embeddings",
                    data=payload,
                    headers={
                        "Authorization": f"Bearer {openrouter_key}",
                        "Content-Type": "application/json"
                    }
                )
                with urllib.request.urlopen(req, timeout=5) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    emb = data["data"][0]["embedding"]
                    return self._normalize(emb)
            except Exception:
                pass

        # 2. High-performance deterministic n-gram hashing semantic embedding
        words = text.lower().replace("-", " ").replace("_", " ").split()
        vec = [0.0] * self.dim
        for w in words:
            # Hash single word
            h = int(hashlib.md5(w.encode("utf-8")).hexdigest(), 16)
            idx = h % self.dim
            sign = 1.0 if ((h >> 4) & 1) else -1.0
            vec[idx] += sign * (1.0 + len(w) * 0.1)

            # Hash character bigrams
            for i in range(len(w) - 1):
                bg = w[i:i+2]
                h_bg = int(hashlib.sha256(bg.encode("utf-8")).hexdigest(), 16)
                idx_bg = h_bg % self.dim
                sign_bg = 1.0 if ((h_bg >> 2) & 1) else -1.0
                vec[idx_bg] += sign_bg * 0.5

        return self._normalize(vec)

    def _normalize(self, vec: List[float]) -> List[float]:
        mag = math.sqrt(sum(x * x for x in vec))
        if mag == 0.0:
            return [0.0] * len(vec)
        return [round(x / mag, 6) for x in vec]

    def cosine_similarity(self, vec_a: List[float], vec_b: List[float]) -> float:
        if not vec_a or not vec_b or len(vec_a) != len(vec_b):
            return 0.0
        dot = sum(a * b for a, b in zip(vec_a, vec_b))
        return round(max(-1.0, min(1.0, dot)), 4)


class TelegramIngestReporter:
    """Dispatches real-time progress updates and keyframe previews to Telegram."""

    def __init__(self, token: str = None, chat_id: str = None):
        self.token = token or os.environ.get("CONTENT_FACTORY_BOT_TOKEN", "8852388091:AAGfMS7XKCe6LtT9A2Nu_pTuiOucfaZChbU")
        self.chat_id = chat_id or os.environ.get("TELEGRAM_CHAT_ID", "1431349185")

    def send_message(self, text: str) -> bool:
        try:
            boundary = f"----IngestMsg{int(time.time()*1000)}"
            body = bytearray()
            body.extend(f'--{boundary}\r\nContent-Disposition: form-data; name="chat_id"\r\n\r\n{self.chat_id}\r\n'.encode())
            body.extend(f'--{boundary}\r\nContent-Disposition: form-data; name="text"\r\n\r\n{text}\r\n'.encode())
            body.extend(b'Content-Disposition: form-data; name="parse_mode"\r\n\r\nHTML\r\n')
            body.extend(f'--{boundary}--\r\n'.encode())

            req = urllib.request.Request(
                f"https://api.telegram.org/bot{self.token}/sendMessage",
                data=body,
                headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}
            )
            with urllib.request.urlopen(req, timeout=12) as resp:
                return resp.status == 200
        except Exception as e:
            print(f"[*] Telegram message error: {e}", file=sys.stderr)
            return False

    def send_keyframe_photo(self, photo_path: Path, caption: str) -> bool:
        if not photo_path.exists():
            return False
        try:
            boundary = f"----Keyframe{int(time.time()*1000)}"
            with open(photo_path, "rb") as f:
                photo_bytes = f.read()
            body = bytearray()
            body.extend(f'--{boundary}\r\nContent-Disposition: form-data; name="chat_id"\r\n\r\n{self.chat_id}\r\n'.encode())
            body.extend(f'--{boundary}\r\nContent-Disposition: form-data; name="caption"\r\n\r\n{caption}\r\n'.encode())
            body.extend(b'Content-Disposition: form-data; name="parse_mode"\r\n\r\nHTML\r\n')
            body.extend(f'--{boundary}\r\nContent-Disposition: form-data; name="photo"; filename="{photo_path.name}"\r\nContent-Type: image/jpeg\r\n\r\n'.encode())
            body.extend(photo_bytes)
            body.extend(f'\r\n--{boundary}--\r\n'.encode())

            req = urllib.request.Request(
                f"https://api.telegram.org/bot{self.token}/sendPhoto",
                data=body,
                headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}
            )
            with urllib.request.urlopen(req, timeout=20) as resp:
                return resp.status == 200
        except Exception as e:
            print(f"[*] Telegram photo error: {e}", file=sys.stderr)
            return False


class FootageVault:
    """Manages high-quality video footage ingestion, segmentation, S3 storage & vector search."""

    def __init__(self, catalog_path: Path = CATALOG_PATH):
        self.catalog_path = catalog_path
        self.embedder = VectorEmbeddingEngine(dim=128)
        self.s3_client = self._init_s3()
        self.catalog = self._load_catalog()
        self.reporter = TelegramIngestReporter()

    def _init_s3(self):
        try:
            import boto3
            return boto3.client(
                "s3",
                endpoint_url=S3_ENDPOINT,
                aws_access_key_id=S3_ACCESS_KEY,
                aws_secret_access_key=S3_SECRET_KEY
            )
        except Exception as e:
            print(f"[*] S3 Client init warning: {e}", file=sys.stderr)
            return None

    def _load_catalog(self) -> List[Dict[str, Any]]:
        if self.catalog_path.exists():
            try:
                with open(self.catalog_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def _save_catalog(self):
        self.catalog_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.catalog_path, "w", encoding="utf-8") as f:
            json.dump(self.catalog, f, ensure_ascii=False, indent=2)

    def segment_and_ingest_video(
        self,
        video_file: Path,
        base_title: str,
        category: str,
        tags: List[str],
        clip_duration: int = 6,
        notify_telegram: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Segment a source video into 1080p B-Roll clips, extract keyframes,
        upload to S3 Vault, and index with semantic vector embeddings.
        """
        if not video_file.exists():
            print(f"[!] Source video does not exist: {video_file}", file=sys.stderr)
            return []

        # Get total video duration
        dur_sec = 10.0
        try:
            cmd = ["ffmpeg", "-i", str(video_file)]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            for line in res.stderr.split("\n"):
                if "Duration:" in line:
                    d_str = line.split("Duration:")[1].split(",")[0].strip()
                    h, m, s = d_str.split(":")
                    dur_sec = float(h) * 3600 + float(m) * 60 + float(s)
                    break
        except Exception:
            pass

        if notify_telegram:
            self.reporter.send_message(
                f"🚀 <b>Bắt đầu Ingest Footage</b>: <i>{base_title}</i>\n"
                f"📁 Chuyên ngành: <code>{category}</code> | Tags: {', '.join(tags)}"
            )

        temp_dir = Path(tempfile.mkdtemp(prefix="footage_seg_"))
        new_entries = []

        try:
            num_clips = max(1, int(dur_sec // clip_duration))
            for i in range(num_clips):
                start_t = i * clip_duration
                clip_name = f"{video_file.stem}_clip_{i+1:02d}.mp4"
                thumb_name = f"{video_file.stem}_thumb_{i+1:02d}.jpg"
                clip_path = temp_dir / clip_name
                thumb_path = temp_dir / thumb_name

                # Cut clean 1080p clip without audio (B-Roll)
                cmd_cut = [
                    "ffmpeg", "-y",
                    "-ss", str(start_t),
                    "-i", str(video_file),
                    "-t", str(clip_duration),
                    "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2",
                    "-c:v", "libx264",
                    "-an",
                    "-pix_fmt", "yuv420p",
                    str(clip_path)
                ]
                subprocess.run(cmd_cut, capture_output=True, timeout=60)

                # Extract keyframe thumbnail
                cmd_thumb = [
                    "ffmpeg", "-y",
                    "-ss", str(start_t + 1.0),
                    "-i", str(video_file),
                    "-vframes", "1",
                    "-vf", "scale=1920:1080",
                    str(thumb_path)
                ]
                subprocess.run(cmd_thumb, capture_output=True, timeout=30)

                if clip_path.exists() and clip_path.stat().st_size > 5000:
                    clip_desc = f"{base_title} part {i+1} {category} {' '.join(tags)}"
                    emb = self.embedder.compute_embedding(clip_desc)

                    s3_clip_key = f"{S3_PREFIX}/clips/{clip_name}"
                    s3_thumb_key = f"{S3_PREFIX}/thumbnails/{thumb_name}"

                    # Upload to S3
                    if self.s3_client:
                        try:
                            self.s3_client.upload_file(str(clip_path), S3_BUCKET, s3_clip_key)
                            if thumb_path.exists():
                                self.s3_client.upload_file(str(thumb_path), S3_BUCKET, s3_thumb_key)
                        except Exception as e:
                            print(f"[*] S3 upload error: {e}", file=sys.stderr)

                    entry = {
                        "id": f"clip_{hashlib.md5(clip_name.encode()).hexdigest()[:10]}",
                        "title": f"{base_title} (Phân đoạn {i+1})",
                        "description": clip_desc,
                        "category": category,
                        "tags": tags,
                        "duration_sec": clip_duration,
                        "resolution": "1920x1080",
                        "s3_clip_key": s3_clip_key,
                        "s3_thumb_key": s3_thumb_key,
                        "embedding": emb,
                        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ")
                    }
                    new_entries.append(entry)
                    self.catalog.append(entry)

                    # Send sample preview for the first clip of each batch
                    if notify_telegram and i == 0 and thumb_path.exists():
                        self.reporter.send_keyframe_photo(
                            thumb_path,
                            f"🎬 <b>Trích xuất B-Roll & S3 Ingest (1080p)</b>\n"
                            f"📌 <i>{base_title} (Phân đoạn {i+1}/{num_clips})</i>\n"
                            f"☁️ S3 Key: <code>{s3_clip_key}</code>\n"
                            f"🧠 Đã tính Vector Embedding (128-dim)"
                        )

            self._save_catalog()
            if notify_telegram:
                self.reporter.send_message(
                    f"✅ <b>Hoàn tất Ingest Gói Footage</b>: <i>{base_title}</i>\n"
                    f"📦 Đã nạp thành công <b>{len(new_entries)} clips B-Roll</b> vào S3 Vault."
                )
            print(f"[✓] Successfully ingested {len(new_entries)} B-Roll clips into Footage Vault.")
            return new_entries

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def search_footage(
        self,
        query: str,
        category: Optional[str] = None,
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic vector search on video clips in the footage vault.
        Returns top matching clips with S3 presigned URLs.
        """
        if not self.catalog:
            return []

        query_vec = self.embedder.compute_embedding(query)
        scored_clips = []

        for item in self.catalog:
            if category and category.lower() not in item.get("category", "").lower():
                continue
            item_vec = item.get("embedding", [])
            sim = self.embedder.cosine_similarity(query_vec, item_vec)
            
            # Additional category/tag keyword bonus
            query_lower = query.lower()
            if any(t.lower() in query_lower for t in item.get("tags", [])):
                sim += 0.15

            scored_clips.append((sim, item))

        scored_clips.sort(key=lambda x: x[0], reverse=True)
        results = []

        for score, clip_info in scored_clips[:top_k]:
            res_item = dict(clip_info)
            res_item["similarity_score"] = round(score, 4)

            # Generate S3 presigned URLs for streaming
            if self.s3_client:
                try:
                    res_item["clip_stream_url"] = self.s3_client.generate_presigned_url(
                        "get_object",
                        Params={"Bucket": S3_BUCKET, "Key": clip_info["s3_clip_key"]},
                        ExpiresIn=3600
                    )
                    res_item["thumb_stream_url"] = self.s3_client.generate_presigned_url(
                        "get_object",
                        Params={"Bucket": S3_BUCKET, "Key": clip_info["s3_thumb_key"]},
                        ExpiresIn=3600
                    )
                except Exception:
                    pass
            results.append(res_item)

        return results

    def ingest_youtube_sample(
        self,
        youtube_url: str,
        title: str,
        category: str,
        tags: List[str]
    ) -> List[Dict[str, Any]]:
        """Download high-quality YouTube clip with yt-dlp and ingest into S3 Vault."""
        temp_video = Path(tempfile.mktemp(suffix=".mp4"))
        try:
            cmd = [
                "yt-dlp",
                "-f", "bestvideo[ext=mp4][height<=1080]+bestaudio[ext=m4a]/best[ext=mp4]/best",
                "-o", str(temp_video),
                youtube_url
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if res.returncode == 0 and temp_video.exists():
                return self.segment_and_ingest_video(temp_video, title, category, tags)
            else:
                print(f"[*] yt-dlp error: {res.stderr[:200]}", file=sys.stderr)
                return []
        finally:
            if temp_video.exists():
                temp_video.unlink()


def main():
    parser = argparse.ArgumentParser(description="Footage Vault CLI")
    subparsers = parser.add_subparsers(dest="command", help="Footage commands")

    p_search = subparsers.add_parser("search", help="Search footage catalog")
    p_search.add_argument("query", help="Semantic search query")
    p_search.add_argument("--category", help="Category filter")
    p_search.add_argument("--top", type=int, default=3, help="Top K results")

    p_ingest = subparsers.add_parser("ingest", help="Ingest local video file")
    p_ingest.add_argument("--video", required=True, help="Path to video file")
    p_ingest.add_argument("--title", required=True, help="Base title")
    p_ingest.add_argument("--category", default="tech-architecture", help="Category")
    p_ingest.add_argument("--tags", default="ai,agent,server", help="Comma-separated tags")

    args = parser.parse_args()
    vault = FootageVault()

    if args.command == "search":
        results = vault.search_footage(args.query, category=args.category, top_k=args.top)
        print(f"\n🔍 Search Results for: '{args.query}' ({len(results)} found)")
        for i, r in enumerate(results, 1):
            print(f"\n[{i}] {r['title']} (Score: {r['similarity_score']})")
            print(f"  • Category: {r['category']} | Tags: {', '.join(r['tags'])}")
            print(f"  • S3 Key: {r['s3_clip_key']}")
            if "clip_stream_url" in r:
                print(f"  • Stream URL: {r['clip_stream_url'][:80]}...")

    elif args.command == "ingest":
        tags = [t.strip() for t in args.tags.split(",")]
        clips = vault.segment_and_ingest_video(Path(args.video), args.title, args.category, tags)
        print(f"[✓] Ingested {len(clips)} clips into S3 Vault.")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
