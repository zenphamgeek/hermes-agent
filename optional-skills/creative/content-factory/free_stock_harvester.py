#!/usr/bin/env python3
"""
Free Stock Real-Life Video Footage Harvester & Ingestion Engine.
Connects to Free Stock APIs (Wikimedia Commons Video API, Pexels, Pixabay, Internet Archive)
to fetch REAL-LIFE recorded 1080p/4K footage (quay thật), segments them into B-Roll clips,
extracts keyframes, indexes vector embeddings, and uploads to MinIO S3 Vault with Telegram reporting.
"""

import os
import sys
import json
import time
import shutil
import tempfile
import argparse
import subprocess
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Dict, List, Any, Optional

FACTORY_DIR = Path(__file__).parent
sys.path.insert(0, str(FACTORY_DIR))

from footage_vault import FootageVault, TelegramIngestReporter, S3_ENDPOINT, S3_BUCKET


class FreeStockHarvester:
    """Harvests real-life stock videos from Wikimedia Commons, Pexels, and public domain repositories."""

    def __init__(self):
        self.vault = FootageVault()
        self.reporter = TelegramIngestReporter()
        self.env_path = Path.home() / ".hermes" / ".env"
        self.pexels_api_key = self._get_env_key("PEXELS_API_KEY")
        self.pixabay_api_key = self._get_env_key("PIXABAY_API_KEY")

    def _get_env_key(self, key: str) -> Optional[str]:
        if self.env_path.exists():
            with open(self.env_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith(f"{key}="):
                        return line.strip().split("=", 1)[1].strip().strip('"').strip("'")
        return os.environ.get(key)

    def search_commons_videos(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Query Wikimedia Commons Media API for CC/Public Domain real-life videos."""
        try:
            url = (
                f"https://commons.wikimedia.org/w/api.php?action=query&format=json&generator=search"
                f"&gsrnamespace=6&gsrsearch=filetype:video+{urllib.parse.quote(query)}"
                f"&gsrlimit={limit}&prop=imageinfo&iiprop=url|mime|size|extmetadata"
            )
            req = urllib.request.Request(url, headers={"User-Agent": "HermesFootageVault/2026 (zen@thinkpad; Contact: zenpham)"})
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                pages = data.get("query", {}).get("pages", {})
                results = []
                for pid, page in pages.items():
                    title_raw = page.get("title", "").replace("File:", "").replace(".webm", "").replace(".ogv", "").replace(".mp4", "")
                    title = f"Real Stock: {title_raw.replace('_', ' ')}"
                    imageinfo = page.get("imageinfo", [{}])[0]
                    media_url = imageinfo.get("url")
                    if media_url:
                        results.append({
                            "title": title,
                            "url": media_url,
                            "tags": [query.lower(), "real-life", "free-stock", "wikimedia-commons"],
                            "source": "wikimedia_commons"
                        })
                return results
        except Exception as e:
            print(f"[!] Wikimedia Commons search error for '{query}': {e}", file=sys.stderr)
            return []

    def search_pexels_videos(self, query: str, per_page: int = 3, orientation: str = "landscape") -> List[Dict[str, Any]]:
        """Query Pexels Video API for real stock footage if API key is present."""
        if not self.pexels_api_key:
            return []
        
        try:
            url = f"https://api.pexels.com/videos/search?query={urllib.parse.quote(query)}&per_page={per_page}&orientation={orientation}"
            req = urllib.request.Request(url, headers={"Authorization": self.pexels_api_key})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                results = []
                for v in data.get("videos", []):
                    video_files = sorted(v.get("video_files", []), key=lambda x: x.get("width", 0), reverse=True)
                    if video_files:
                        best = video_files[0]
                        results.append({
                            "title": f"Pexels Real Stock: {query.title()} (ID: {v.get('id')})",
                            "url": best.get("link"),
                            "width": best.get("width"),
                            "height": best.get("height"),
                            "duration_sec": v.get("duration", 10),
                            "tags": [query.lower(), "pexels", "real-life", "free-stock"],
                            "source": "pexels_api"
                        })
                return results
        except Exception as e:
            print(f"[!] Pexels search error: {e}", file=sys.stderr)
            return []

    def download_and_transcode_stream(self, url: str, target_mp4: Path) -> bool:
        """Download raw video stream (webm/ogv/mp4) and transcode to standard 1080p MP4."""
        temp_raw = target_mp4.parent / f"temp_download_{int(time.time()*1000)}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64)"})
            with urllib.request.urlopen(req, timeout=30) as resp, open(temp_raw, "wb") as out_f:
                shutil.copyfileobj(resp, out_f)
            
            if not temp_raw.exists() or temp_raw.stat().st_size < 5000:
                return False

            # Transcode with FFmpeg to clean 1080p H.264 MP4
            cmd = [
                "ffmpeg", "-y", "-i", str(temp_raw),
                "-vf", "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080",
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "fast",
                "-an",
                str(target_mp4)
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
            return res.returncode == 0 and target_mp4.exists() and target_mp4.stat().st_size > 10000
        except Exception as e:
            print(f"[!] Transcode error for {url}: {e}", file=sys.stderr)
            return False
        finally:
            if temp_raw.exists():
                temp_raw.unlink(missing_ok=True)

    def harvest_real_stock_by_keywords(
        self,
        keywords: str,
        category: str,
        max_videos: int = 2,
        notify_telegram: bool = True
    ) -> List[Dict[str, Any]]:
        """Harvest real stock videos by keyword query from Wikimedia/Pexels."""
        category = category.lower().strip()
        feeds = []

        # 1. Check Pexels API
        if self.pexels_api_key:
            feeds.extend(self.search_pexels_videos(keywords, per_page=max_videos))

        # 2. Check Wikimedia Commons Video API
        if len(feeds) < max_videos:
            commons_items = self.search_commons_videos(keywords, limit=max_videos - len(feeds))
            feeds.extend(commons_items)

        if not feeds:
            print(f"[!] No real stock videos found for keywords: '{keywords}'")
            return []

        temp_dir = Path(tempfile.mkdtemp(prefix=f"real_stock_{category}_"))
        all_ingested = []

        try:
            for i, item in enumerate(feeds[:max_videos]):
                title = item.get("title", f"Real Stock: {keywords.title()}")
                url = item.get("url", "")
                tags = item.get("tags", [keywords, category, "real-stock"])

                print(f"[*] Downloading & Transcoding Real Stock [{i+1}/{min(len(feeds), max_videos)}]: {title}...")
                local_1080p = temp_dir / f"master_real_{category}_{i}.mp4"

                if self.download_and_transcode_stream(url, local_1080p):
                    size_kb = local_1080p.stat().st_size // 1024
                    print(f"  • Ingesting & Segmenting 1080p real stock into S3 ({size_kb} KB)...")
                    clips = self.vault.segment_and_ingest_video(
                        video_file=local_1080p,
                        base_title=title,
                        category=category,
                        tags=tags + ["source_real_stock"],
                        clip_duration=6,
                        notify_telegram=notify_telegram
                    )
                    all_ingested.extend(clips)
                    print(f"  [✓] {len(clips)} real-life B-Roll clips indexed.")

            return all_ingested
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


def main():
    parser = argparse.ArgumentParser(description="Real-Life Free Stock Footage Harvester")
    parser.add_argument("keywords", nargs="?", help="Search keywords (e.g. 'latte art barista', 'cooking chef restaurant')")
    parser.add_argument("--category", "-c", default="general", help="Category: cafe, food, logistics, chemistry, etc.")
    parser.add_argument("--limit", "-k", type=int, default=2, help="Max videos to harvest")
    args = parser.parse_args()

    if not args.keywords:
        parser.print_help()
        return

    harvester = FreeStockHarvester()
    clips = harvester.harvest_real_stock_by_keywords(
        keywords=args.keywords,
        category=args.category,
        max_videos=args.limit,
        notify_telegram=True
    )
    print(f"\n[✓] Finished Harvesting: {len(clips)} real-life stock clips added to S3 Vault.")


if __name__ == "__main__":
    main()
