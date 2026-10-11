#!/usr/bin/env python3
"""
30-Day Master Media Production Tracker & Prompt Matrix Generator.
Generates and manages 720 unique hourly video + photo prompt slots (30 days x 24 hours),
providing an end-to-end production calendar, status tracking, and metadata ingestion.
"""

import os
import sys
import json
import sqlite3
import argparse
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple

import importlib.util

SKILL_DIR = Path(__file__).resolve().parent
WORKSPACE_ROOT = Path("/home/zen/hermes-agent")
HERMES_HOME = Path(os.environ.get("HERMES_HOME", "/home/zen/.hermes"))
TRACKER_JSON_FILE = SKILL_DIR / "prompts_30days_tracker.json"
USER_TRACKER_JSON = HERMES_HOME / "prompts_30days_tracker.json"
TRACKER_SQLITE_FILE = WORKSPACE_ROOT / "storage" / "media_bank" / "metadata" / "monthly_tracker.sqlite"

# Load catalog_manager cleanly
_cat_spec = importlib.util.spec_from_file_location("catalog_manager", SKILL_DIR / "catalog_manager.py")
_cat_mod = importlib.util.module_from_spec(_cat_spec)
_cat_spec.loader.exec_module(_cat_mod)
MediaBankCatalog = _cat_mod.MediaBankCatalog

# 30 Distinct Daily Themes
DAILY_PILLARS = [
    ("Day 01", "ai_brain", "AI Agent Architectures & Autonomous Planning Loops"),
    ("Day 02", "dev_workspace", "Local LLM Hardware & ThinkPad GPU Acceleration"),
    ("Day 03", "dev_workspace", "Vibe Coding & Cursor / Claude Code Mastery"),
    ("Day 04", "cloud_infra", "Self-Hosted Homelab, LXD Containers & Linux Matrix"),
    ("Day 05", "fintech_market", "FinTech Intelligence, VN-Index AI & Market Radar"),
    ("Day 06", "podcast_studio", "Cyber-Zen Podcast Studio & Acoustic Atmosphere"),
    ("Day 07", "smart_city", "Futuristic Saigon (TP.HCM) Smart City & High-Speed Cyber Lights"),
    ("Day 08", "ai_brain", "Multi-Agent Swarm Orchestration & Consensus Protocols"),
    ("Day 09", "dev_workspace", "Open Source AI Tools, LM Studio & Model Quantization"),
    ("Day 10", "dev_workspace", "Midnight Coding, Mechanical Keyboards & Tea Rituals"),
    ("Day 11", "cloud_infra", "Fiber Optic Superhighways & Low-Latency Cloud Data Centers"),
    ("Day 12", "fintech_market", "Algorithmic Trading & Automated Risk Engines"),
    ("Day 13", "podcast_studio", "Voice AI, Audio Waveforms & Multimodal Synthesizers"),
    ("Day 14", "smart_city", "Modern Hanoi Tech Hub & Elevated Metro Drone Views"),
    ("Day 15", "ai_brain", "Cognitive Memory Architectures & Vector Database Graphs"),
    ("Day 16", "cloud_infra", "Edge AI Devices, Raspberry Pi Clusters & IoT Sensors"),
    ("Day 17", "dev_workspace", "Ergonomic Minimalist Workspaces & Ultrawide OLEDs"),
    ("Day 18", "cloud_infra", "Kubernetes, Docker & Distributed Microservices"),
    ("Day 19", "fintech_market", "Macroeconomics, Vietnam Corporate News & Financial Deep-Dives"),
    ("Day 20", "podcast_studio", "Zen Studio Lighting, Neon Tube Ambiance & Acoustic Panels"),
    ("Day 21", "smart_city", "Da Nang Tech Coastline & Dragon Bridge Cyber Glow"),
    ("Day 22", "ai_brain", "AI Vision, Neural Image Processing & Face Generation"),
    ("Day 23", "dev_workspace", "Developer Productivity Tools, Shell Scripting & Terminal TUI"),
    ("Day 24", "dev_workspace", "Bonsai Zen Workstations & Mindful Coding Flow"),
    ("Day 25", "cloud_infra", "Cybersecurity, Ethical Hacking & Defensive Agent Shields"),
    ("Day 26", "ai_brain", "Decentralized AI, Peer-to-Peer Compute & Web3 Protocols"),
    ("Day 27", "podcast_studio", "Audio Visualizers, Podcast Microphones & Sound Waves"),
    ("Day 28", "smart_city", "Hai Phong & Can Tho Smart Logistics, High-Tech Ports & Drone Corridors"),
    ("Day 29", "ai_brain", "Next-Gen AI Models, Reasoning Tokens & Synthetic Data"),
    ("Day 30", "dev_workspace", "The Future of Human-AI Symbiosis & Cyber-Zen Tech Philosophy"),
]

HOURLY_VARIATIONS = [
    ("00:00", "Midnight Deep Flow", "16:9", "hero", "35mm anamorphic wide shot in deep dark obsidian room"),
    ("01:00", "Quantum Particle Core", "9:16", "b_roll", "vertical macro 85mm lens showing intricate glowing quantum particles"),
    ("02:00", "Silent Compute Matrix", "16:9", "b_roll", "slow horizontal camera pan across glowing server indicator LEDs"),
    ("03:00", "Subtle Data Ripples", "9:16", "b_roll", "vertical fluid particle wave reflecting cyan and gold lights"),
    ("04:00", "Dawn Atmospheric Haze", "16:9", "hero", "volumetric dawn light beams cutting through minimalist workspace"),
    ("05:00", "Early Morning Zen Brew", "16:9", "b_roll", "macro shot of hot steaming ceramic tea cup beside glowing keyboard"),
    ("06:00", "Sunrise Golden Horizon", "16:9", "hero", "cinematic 4k drone sunrise over futuristic glass skyline"),
    ("07:00", "System Boot & Diagnostics", "9:16", "b_roll", "vertical high-speed diagnostic telemetry scrolling on OLED"),
    ("08:00", "Morning Market Briefing", "16:9", "hero", "3d holographic charts floating above clean wooden executive desk"),
    ("09:00", "High-Throughput Processing", "16:9", "b_roll", "fast-moving data packets traversing isometric neural mesh"),
    ("10:00", "Vibe Coding Focus", "9:16", "b_roll", "vertical close-up of hands typing on custom mechanical keyboard"),
    ("11:00", "Neural Weight Synthesis", "16:9", "b_roll", "close-up of glowing semiconductor chip with gold traces"),
    ("12:00", "Noon High-Efficiency Matrix", "16:9", "hero", "sleek studio overview with dual vertical displays and soft ambient neon"),
    ("13:00", "Acoustic Voice Resonance", "9:16", "b_roll", "vertical sound visualizer with undulating glowing waveform"),
    ("14:00", "Distributed Agent Consensus", "16:9", "b_roll", "multi-node holographic cluster pulsing in synchronized harmony"),
    ("15:00", "Afternoon Tea & Code Review", "16:9", "hero", "minimalist desk with ceramic teapot, open laptop with clean code"),
    ("16:00", "Cloud Highway Traffic", "9:16", "b_roll", "vertical optical fiber core carrying high-speed photon bursts"),
    ("17:00", "Sunset Golden Hour Skyline", "16:9", "hero", "dusk aerial view of glowing architectural landmarks and river"),
    ("18:00", "Evening Studio Warmth", "16:9", "hero", "intimate podcast lounge with Shure SM7B mic and warm amber backlights"),
    ("19:00", "Traffic Light Trails", "9:16", "b_roll", "vertical high-angle long exposure of city traffic light streams"),
    ("20:00", "Prime Time Intelligence", "16:9", "hero", "holographic radar interface highlighting key insights in dark room"),
    ("21:00", "Nighttime Deep Work", "16:9", "b_roll", "low-angle tracking shot of laptop illuminated by cool screen glow"),
    ("22:00", "Bonsai Glow Reflection", "9:16", "b_roll", "vertical macro of illuminated bonsai leaves beside terminal"),
    ("23:00", "Quiet Obsidian Reflections", "16:9", "hero", "peaceful dark minimalist room with subtle cyan sleep lights"),
]


class MonthlyMediaTracker:
    """Manages 30-day 720-slot prompt calendar and execution states."""

    def __init__(self, json_file: Optional[Path] = None, db_file: Optional[Path] = None):
        self.json_file = json_file or TRACKER_JSON_FILE
        self.db_file = db_file or TRACKER_SQLITE_FILE
        self.json_file.parent.mkdir(parents=True, exist_ok=True)
        self.db_file.parent.mkdir(parents=True, exist_ok=True)
        self._init_sqlite()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_file))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_sqlite(self):
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS monthly_slots (
                    slot_id TEXT PRIMARY KEY,
                    day_index INTEGER NOT NULL,
                    day_label TEXT NOT NULL,
                    hour_index INTEGER NOT NULL,
                    hour_label TEXT NOT NULL,
                    category TEXT NOT NULL,
                    day_theme TEXT NOT NULL,
                    title TEXT NOT NULL,
                    aspect_ratio TEXT NOT NULL,
                    video_prompt TEXT NOT NULL,
                    photo_prompt TEXT NOT NULL,
                    tags TEXT,
                    platforms TEXT,
                    status TEXT DEFAULT 'pending',
                    video_id TEXT,
                    photo_id TEXT,
                    video_path TEXT,
                    photo_path TEXT,
                    completed_at TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            conn.commit()

    def generate_30day_master_plan(self, start_date: Optional[str] = None) -> Dict[str, Any]:
        """Generate/Refresh the entire 720-slot (30 days x 24 hours) plan."""
        start_dt = datetime.strptime(start_date, "%Y-%m-%d") if start_date else datetime.now(timezone(timedelta(hours=7)))
        slots = []
        now_iso = datetime.now(timezone.utc).isoformat()

        with self._get_connection() as conn:
            cur = conn.cursor()

            for day_idx, (day_label, category, day_theme) in enumerate(DAILY_PILLARS):
                current_day_dt = start_dt + timedelta(days=day_idx)
                date_str = current_day_dt.strftime("%Y-%m-%d")

                for hour_idx, (hour_str, var_title, aspect_ratio, img_type, camera_desc) in enumerate(HOURLY_VARIATIONS):
                    slot_id = f"D{day_idx+1:02d}_H{hour_idx:02d}"
                    slot_title = f"{day_theme} — {var_title}"

                    # Contextual Brand Signature for ZENPHAM
                    brand_signatures = {
                        "ai_brain": "displaying sleek illuminated typography 'ZENPHAM AI CORE'",
                        "dev_workspace": "featuring custom dark leather desk mat debossed with 'ZENPHAM' and clean syntax code",
                        "cloud_infra": "with server cluster LED status panel displaying 'ZENPHAM INFRA'",
                        "fintech_market": "featuring 3d holographic financial terminal header 'ZENPHAM CAPITAL // INTELLIGENCE'",
                        "podcast_studio": "with warm glowing neon tube sign on acoustic slatted wall spelling 'ZENPHAM STUDIO'",
                        "smart_city": "with modern skyscraper rooftop holographic sign glowing 'ZENPHAM TECH'"
                    }
                    brand_tagline = brand_signatures.get(category, "with subtle luxury brand watermark 'ZENPHAM'")

                    # Construct Cyber-Zen Prompts with Brand Signature
                    video_prompt = (
                        f"cinematic slow-motion 3d footage of {day_theme.lower()}, {var_title.lower()}, {brand_tagline}, "
                        f"in dark obsidian cyber-zen studio, {camera_desc}, volumetric electric cyan and amber rim lighting, "
                        f"8k resolution, photorealistic, smooth dynamic camera movement, commercial luxury tech look"
                    )
                    photo_prompt = (
                        f"photorealistic 8k commercial photography of {day_theme.lower()}, {var_title.lower()}, {brand_tagline}, "
                        f"minimalist obsidian workspace, {camera_desc}, soft neon reflections, sharp focus, 35mm anamorphic lens"
                    )

                    tags = ["cyber_zen", "zenpham", category, f"day_{day_idx+1}", f"hour_{hour_idx}"]
                    platforms = ["youtube", "facebook", "x", "podcast"]


                    slot_data = {
                        "slot_id": slot_id,
                        "date": date_str,
                        "day_index": day_idx + 1,
                        "day_label": day_label,
                        "hour_index": hour_idx,
                        "hour_label": hour_str,
                        "category": category,
                        "day_theme": day_theme,
                        "title": slot_title,
                        "aspect_ratio": aspect_ratio,
                        "image_type": img_type,
                        "video_prompt": video_prompt,
                        "photo_prompt": photo_prompt,
                        "tags": tags,
                        "platforms": platforms,
                        "status": "pending",
                        "video_id": None,
                        "photo_id": None,
                        "video_path": None,
                        "photo_path": None,
                        "completed_at": None,
                        "created_at": now_iso
                    }
                    slots.append(slot_data)

                    # Upsert into SQLite
                    cur.execute("""
                        INSERT OR REPLACE INTO monthly_slots (
                            slot_id, day_index, day_label, hour_index, hour_label,
                            category, day_theme, title, aspect_ratio, video_prompt,
                            photo_prompt, tags, platforms, status, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?)
                    """, (
                        slot_id, day_idx + 1, day_label, hour_idx, hour_str,
                        category, day_theme, slot_title, aspect_ratio, video_prompt,
                        photo_prompt, ",".join(tags), ",".join(platforms), now_iso
                    ))

            conn.commit()

        master_plan = {
            "version": "1.0.0",
            "style": "cyber_zen_tech",
            "start_date": start_dt.strftime("%Y-%m-%d"),
            "total_days": 30,
            "total_slots": len(slots),
            "generated_at": now_iso,
            "slots": slots
        }

        # Save to JSON files
        with open(self.json_file, "w", encoding="utf-8") as f:
            json.dump(master_plan, f, ensure_ascii=False, indent=2)

        if USER_TRACKER_JSON.parent.exists():
            with open(USER_TRACKER_JSON, "w", encoding="utf-8") as f:
                json.dump(master_plan, f, ensure_ascii=False, indent=2)

        return master_plan

    def load_tracker_data(self) -> Dict[str, Any]:
        """Load current tracker JSON or generate if missing."""
        if not self.json_file.exists():
            return self.generate_30day_master_plan()
        with open(self.json_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_slot_by_current_time(self) -> Optional[Dict[str, Any]]:
        """Get the specific planned slot matching current Day & Hour."""
        data = self.load_tracker_data()
        start_str = data.get("start_date")
        if not start_str:
            return None

        now_vn = datetime.now(timezone(timedelta(hours=7)))
        start_dt = datetime.strptime(start_str, "%Y-%m-%d").replace(tzinfo=now_vn.tzinfo)
        day_diff = (now_vn.date() - start_dt.date()).days
        day_index = (day_diff % 30) + 1
        hour_index = now_vn.hour

        slot_id = f"D{day_index:02d}_H{hour_index:02d}"
        for s in data.get("slots", []):
            if s["slot_id"] == slot_id:
                return s
        return None

    def update_slot_execution(
        self,
        slot_id: str,
        status: str,
        video_id: Optional[str] = None,
        photo_id: Optional[str] = None,
        video_path: Optional[str] = None,
        photo_path: Optional[str] = None
    ) -> bool:
        """Mark a slot as completed or in_progress."""
        now_iso = datetime.now(timezone.utc).isoformat()

        # Update SQLite
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                UPDATE monthly_slots
                SET status = ?, video_id = ?, photo_id = ?, video_path = ?, photo_path = ?, completed_at = ?
                WHERE slot_id = ?
            """, (status, video_id, photo_id, video_path, photo_path, now_iso, slot_id))
            conn.commit()

        # Update JSON
        data = self.load_tracker_data()
        for s in data.get("slots", []):
            if s["slot_id"] == slot_id:
                s["status"] = status
                s["video_id"] = video_id
                s["photo_id"] = photo_id
                s["video_path"] = video_path
                s["photo_path"] = photo_path
                s["completed_at"] = now_iso
                break

        with open(self.json_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return True

    def get_progress_statistics(self) -> Dict[str, Any]:
        """Calculate complete statistics of the 30-day master tracker."""
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT count(*) as total, sum(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed FROM monthly_slots")
            row = cur.fetchone()
            total = row["total"] or 0
            completed = row["completed"] or 0

            cur.execute("SELECT category, count(*) as count, sum(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as comp FROM monthly_slots GROUP BY category")
            by_category = {r["category"]: {"total": r["count"], "completed": r["comp"] or 0} for r in cur.fetchall()}

            cur.execute("SELECT day_index, day_theme, count(*) as count, sum(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as comp FROM monthly_slots GROUP BY day_index ORDER BY day_index LIMIT 10")
            daily_samples = [{"day": r["day_index"], "theme": r["day_theme"], "completed": r["comp"] or 0, "total": r["count"]} for r in cur.fetchall()]

        return {
            "total_slots": total,
            "completed_slots": completed,
            "percent_completed": round((completed / total * 100) if total else 0, 1),
            "target_videos": total,
            "target_photos": total,
            "by_category": by_category,
            "daily_samples": daily_samples,
            "json_path": str(self.json_file),
            "sqlite_path": str(self.db_file)
        }


def main():
    parser = argparse.ArgumentParser(description="30-Day Master Media Production Tracker.")
    parser.add_argument("--generate-30days", action="store_true", help="Generate/Refresh 30-Day Master Plan (720 slots)")
    parser.add_argument("--start-date", help="Start date (YYYY-MM-DD), defaults to today")
    parser.add_argument("--status", action="store_true", help="Show 30-Day Master Tracker progress")
    parser.add_argument("--current-slot", action="store_true", help="Show current hour's planned slot")
    args = parser.parse_args()

    tracker = MonthlyMediaTracker()

    if args.generate_30days:
        res = tracker.generate_30day_master_plan(start_date=args.start_date)
        print(f"[✓] Generated 30-Day Master Plan: {res['total_slots']} Slots (30 Days x 24 Hours).")
        print(f"  • JSON: {tracker.json_file}")
        print(f"  • SQLite: {tracker.db_file}")

    elif args.current_slot:
        slot = tracker.get_slot_by_current_time()
        if slot:
            print(f"=== Current Slot: {slot['slot_id']} [{slot['date']} {slot['hour_label']}] ===")
            print(f"Theme: {slot['title']} (#{slot['category']})")
            print(f"Aspect Ratio: {slot['aspect_ratio']}")
            print(f"Video Prompt: {slot['video_prompt'][:80]}...")
            print(f"Status: {slot['status']}")
        else:
            print("[*] No current slot found.")

    elif args.status or not len(sys.argv) > 1:
        stats = tracker.get_progress_statistics()
        print("=== ZENPHAM 30-Day Media Production Tracker ===")
        print(f"Progress: {stats['completed_slots']}/{stats['total_slots']} Slots ({stats['percent_completed']}%)")
        print(f"Target: {stats['target_videos']} Videos + {stats['target_photos']} Photos")
        print(f"Categories Breakdown: {stats['by_category']}")


if __name__ == "__main__":
    main()
