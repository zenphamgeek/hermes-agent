#!/usr/bin/env python3
"""
Free Quota Footage Harvester & Media Bank Ingestion Engine.
Enqueues curated prompts into Agnes AI Video Scheduler, ingests rendered media,
and indexes metadata into the Cyber-Zen Media Asset Bank.
"""

import os
import sys
import shutil
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import importlib.util

SKILL_DIR = Path(__file__).resolve().parent
WORKSPACE_ROOT = Path("/home/zen/hermes-agent")
PROMPTS_FILE = SKILL_DIR / "prompts_seed.json"

# Load catalog_manager cleanly
_cat_spec = importlib.util.spec_from_file_location("catalog_manager", SKILL_DIR / "catalog_manager.py")
_cat_mod = importlib.util.module_from_spec(_cat_spec)
_cat_spec.loader.exec_module(_mod := _cat_mod)
MediaBankCatalog = _cat_mod.MediaBankCatalog

# Load agnes scheduler cleanly
_sch_path = WORKSPACE_ROOT / "skills" / "creative" / "agnes-ai-video" / "scheduler.py"
if _sch_path.exists():
    _sch_spec = importlib.util.spec_from_file_location("agnes_scheduler", _sch_path)
    _sch_mod = importlib.util.module_from_spec(_sch_spec)
    _sch_spec.loader.exec_module(_sch_mod)
    VideoQueueManager = _sch_mod.VideoQueueManager
else:
    VideoQueueManager = None


class FootageHarvester:
    """Orchestrates prompt harvesting, quota scheduling, and bank ingestion."""

    def __init__(self, catalog: Optional[MediaBankCatalog] = None, prompts_file: Optional[Path] = None):
        self.catalog = catalog or MediaBankCatalog()
        self.prompts_file = prompts_file or PROMPTS_FILE
        self.queue_mgr = VideoQueueManager() if VideoQueueManager else None

    def load_seed_prompts(self) -> List[Dict[str, Any]]:
        """Load all curated seed prompts from library."""
        if not self.prompts_file.exists():
            return []
        import json
        with open(self.prompts_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("prompts", [])

    def enqueue_seed_prompts(
        self,
        category: Optional[str] = None,
        aspect_ratio: Optional[str] = None,
        media_type: str = "video",
        limit: int = 10
    ) -> Dict[str, Any]:
        """Enqueue matching seed prompts into Agnes Video Quota Scheduler."""
        if not self.queue_mgr:
            return {"success": False, "error": "Agnes AI scheduler not available"}

        prompts = self.load_seed_prompts()
        matched = []
        for p in prompts:
            if category and p.get("category") != category:
                continue
            if aspect_ratio and p.get("aspect_ratio") != aspect_ratio:
                continue
            if media_type and p.get("media_type") != media_type:
                continue
            matched.append(p)

        enqueued = []
        for p in matched[:limit]:
            task = self.queue_mgr.enqueue_prompt(
                prompt=p["prompt"],
                aspect_ratio=p.get("aspect_ratio", "16:9"),
                seconds=str(p.get("seconds", "5")),
                model=p.get("model", "agnes-video-2.5"),
                title=p.get("title", p["prompt"][:50])
            )
            enqueued.append({
                "prompt_id": p.get("id"),
                "task_id": task["id"],
                "title": task["title"],
                "aspect_ratio": task["aspect_ratio"]
            })

        return {
            "success": True,
            "total_enqueued": len(enqueued),
            "tasks": enqueued
        }

    def ingest_completed_queue_items(self) -> Dict[str, Any]:
        """Scan completed tasks in Agnes Video Queue and register them into Media Bank."""
        if not self.queue_mgr:
            return {"success": False, "error": "Queue manager unavailable"}

        q_data = self.queue_mgr.load_queue()
        completed_tasks = [t for t in q_data.get("tasks", []) if t.get("status") == "completed"]
        seed_prompts = {p.get("title"): p for p in self.load_seed_prompts()}

        ingested_count = 0
        for task in completed_tasks:
            local_src = task.get("local_path")
            if not local_src or not Path(local_src).exists():
                continue

            src_path = Path(local_src)
            asset_id = task["id"]

            # Check if already registered
            if self.catalog.get_asset(asset_id):
                continue

            ratio = task.get("aspect_ratio", "16:9")
            ratio_folder = "16_9" if "16" in ratio and "9" in ratio and ratio.startswith("16") else ("9_16" if ratio.startswith("9") else "square")
            dest_dir = self.catalog.videos_dir / ratio_folder
            dest_path = dest_dir / src_path.name
            
            # Copy to storage bank
            shutil.copy2(src_path, dest_path)

            # Match metadata from seed prompt or default
            seed_info = seed_prompts.get(task.get("title"), {})
            category = seed_info.get("category", "ai_brain")
            tags = seed_info.get("tags", ["b_roll", "ai", "cyber_zen"])
            platforms = seed_info.get("platforms", ["youtube", "x", "facebook"])

            self.catalog.register_asset(
                asset_id=asset_id,
                filename=dest_path.name,
                title=task.get("title", src_path.stem),
                category=category,
                media_type="video",
                aspect_ratio=ratio,
                local_path=dest_path,
                resolution=task.get("size", "720P"),
                duration_seconds=float(task.get("seconds", 5)),
                prompt=task.get("prompt"),
                tags=tags,
                platforms=platforms
            )
            ingested_count += 1

        return {
            "success": True,
            "ingested_new_assets": ingested_count,
            "total_completed_tasks": len(completed_tasks)
        }


def main():
    parser = argparse.ArgumentParser(description="Harvest Free Quota & Ingest Media Asset Bank.")
    parser.add_argument("--enqueue-seed", action="store_true", help="Enqueue seed prompts to Agnes AI video scheduler")
    parser.add_argument("--category", choices=["ai_brain", "dev_workspace", "cloud_infra", "fintech_market", "podcast_studio", "smart_city"], help="Filter by category")
    parser.add_argument("--aspect-ratio", choices=["16:9", "9:16", "1:1"], help="Filter by aspect ratio")
    parser.add_argument("--limit", type=int, default=5, help="Number of prompts to enqueue")
    parser.add_argument("--ingest", action="store_true", help="Ingest completed videos from queue to Media Bank")
    parser.add_argument("--search", help="Search footage in Media Bank")
    parser.add_argument("--status", action="store_true", help="Show Media Bank & Quota status")
    args = parser.parse_args()

    harvester = FootageHarvester()

    if args.enqueue_seed:
        res = harvester.enqueue_seed_prompts(
            category=args.category,
            aspect_ratio=args.aspect_ratio,
            limit=args.limit
        )
        print(f"[✓] Enqueued {res.get('total_enqueued', 0)} prompts into Agnes Free Quota Scheduler:")
        for t in res.get("tasks", []):
            print(f"  - [{t['aspect_ratio']}] {t['title']} (ID: {t['task_id']})")

    elif args.ingest:
        res = harvester.ingest_completed_queue_items()
        print(f"[✓] Ingested {res.get('ingested_new_assets', 0)} new assets into Media Bank.")

    elif args.search:
        results = harvester.catalog.search_assets(query=args.search)
        print(f"=== Found {len(results)} assets matching '{args.search}' ===")
        for r in results:
            print(f" - [{r['aspect_ratio']}] [{r['category']}] {r['title']} -> {r['local_path']}")

    elif args.status or not len(sys.argv) > 1:
        stats = harvester.catalog.get_statistics()
        prompts = harvester.load_seed_prompts()
        print("=== ZENPHAM Cyber-Zen Media Asset Bank ===")
        print(f"Total Seed Prompts in Library: {len(prompts)}")
        print(f"Total Bank Assets: {stats['total_assets']} ({stats['total_size_mb']} MB)")
        print(f"By Type: {stats['by_type']}")
        print(f"By Category: {stats['by_category']}")
        print(f"By Aspect Ratio: {stats['by_ratio']}")


if __name__ == "__main__":
    main()
