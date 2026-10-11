#!/usr/bin/env python3
"""
Media Asset Bank Catalog & Metadata Manager.
Manages persistent SQLite & JSON metadata index for footage, images, prompts,
and asset taxonomy for YouTube, X, Facebook, and Podcast production.
"""

import os
import sys
import json
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple

WORKSPACE_ROOT = Path("/home/zen/hermes-agent")
STORAGE_ROOT = WORKSPACE_ROOT / "storage" / "media_bank"
HERMES_HOME = Path(os.environ.get("HERMES_HOME", "/home/zen/.hermes"))


class MediaBankCatalog:
    """Catalog manager for video footage, images, and brand assets."""

    def __init__(self, storage_dir: Optional[Path] = None):
        self.storage_dir = storage_dir or STORAGE_ROOT
        self.videos_dir = self.storage_dir / "videos"
        self.images_dir = self.storage_dir / "images"
        self.metadata_dir = self.storage_dir / "metadata"
        self.db_path = self.metadata_dir / "media_bank.sqlite"
        self.json_path = self.metadata_dir / "catalog.json"

        self._ensure_directories()
        self._init_sqlite()

    def _ensure_directories(self):
        """Ensure all storage folder structures exist."""
        subdirs = [
            self.videos_dir / "16_9",
            self.videos_dir / "9_16",
            self.videos_dir / "square",
            self.images_dir / "hero",
            self.images_dir / "b_roll",
            self.images_dir / "thumbnails",
            self.metadata_dir
        ]
        for d in subdirs:
            d.mkdir(parents=True, exist_ok=True)

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_sqlite(self):
        """Create SQLite schema and FTS5 search index."""
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS media_assets (
                    id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    title TEXT NOT NULL,
                    category TEXT NOT NULL,
                    media_type TEXT NOT NULL,
                    aspect_ratio TEXT NOT NULL,
                    resolution TEXT,
                    duration_seconds REAL,
                    style TEXT DEFAULT 'cyber_zen_tech',
                    prompt TEXT,
                    negative_prompt TEXT,
                    tags TEXT,
                    platforms TEXT,
                    local_path TEXT NOT NULL,
                    file_size_bytes INTEGER,
                    created_at TEXT NOT NULL
                )
            """)

            # Create FTS5 virtual table for lightning-fast search
            cur.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS media_fts USING fts5(
                    id UNINDEXED,
                    title,
                    category,
                    prompt,
                    tags,
                    platforms
                )
            """)
            conn.commit()

    def register_asset(
        self,
        asset_id: str,
        filename: str,
        title: str,
        category: str,
        media_type: str,
        aspect_ratio: str,
        local_path: Path,
        resolution: str = "720P",
        duration_seconds: float = 5.0,
        style: str = "cyber_zen_tech",
        prompt: Optional[str] = None,
        negative_prompt: Optional[str] = None,
        tags: Optional[List[str]] = None,
        platforms: Optional[List[str]] = None,
        file_size_bytes: Optional[int] = None
    ) -> Dict[str, Any]:
        """Register a new media asset with complete metadata."""
        local_path = Path(local_path)
        tags_list = tags or []
        platforms_list = platforms or ["youtube", "x", "facebook"]
        tags_str = ",".join(tags_list)
        platforms_str = ",".join(platforms_list)
        now_iso = datetime.now(timezone.utc).isoformat()

        if file_size_bytes is None and local_path.exists():
            file_size_bytes = local_path.stat().st_size

        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT OR REPLACE INTO media_assets (
                    id, filename, title, category, media_type, aspect_ratio,
                    resolution, duration_seconds, style, prompt, negative_prompt,
                    tags, platforms, local_path, file_size_bytes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                asset_id, filename, title, category, media_type, aspect_ratio,
                resolution, duration_seconds, style, prompt, negative_prompt,
                tags_str, platforms_str, str(local_path), file_size_bytes or 0, now_iso
            ))

            # Update FTS
            cur.execute("DELETE FROM media_fts WHERE id = ?", (asset_id,))
            cur.execute("""
                INSERT INTO media_fts (id, title, category, prompt, tags, platforms)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (asset_id, title, category, prompt or "", tags_str, platforms_str))
            conn.commit()

        self.export_catalog_json()

        return {
            "id": asset_id,
            "filename": filename,
            "title": title,
            "category": category,
            "media_type": media_type,
            "aspect_ratio": aspect_ratio,
            "local_path": str(local_path),
            "created_at": now_iso
        }

    def search_assets(
        self,
        query: Optional[str] = None,
        category: Optional[str] = None,
        media_type: Optional[str] = None,
        aspect_ratio: Optional[str] = None,
        platform: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Search media assets by keyword, category, aspect ratio, and platform."""
        conditions = []
        params = []

        if query:
            # Query FTS index
            clean_query = query.replace('"', '""')
            fts_sql = "SELECT id FROM media_fts WHERE media_fts MATCH ? ORDER BY rank LIMIT 100"
            with self._get_connection() as conn:
                cur = conn.cursor()
                try:
                    cur.execute(fts_sql, (f"{clean_query}*",))
                    matching_ids = [row["id"] for row in cur.fetchall()]
                except Exception:
                    cur.execute("SELECT id FROM media_assets WHERE title LIKE ? OR prompt LIKE ?", (f"%{query}%", f"%{query}%"))
                    matching_ids = [row["id"] for row in cur.fetchall()]

            if not matching_ids:
                return []
            placeholders = ",".join("?" for _ in matching_ids)
            conditions.append(f"id IN ({placeholders})")
            params.extend(matching_ids)

        if category:
            conditions.append("category = ?")
            params.append(category)

        if media_type:
            conditions.append("media_type = ?")
            params.append(media_type)

        if aspect_ratio:
            conditions.append("aspect_ratio = ?")
            params.append(aspect_ratio)

        if platform:
            conditions.append("platforms LIKE ?")
            params.append(f"%{platform}%")

        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
        sql = f"SELECT * FROM media_assets {where_clause} ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()

        results = []
        for r in rows:
            results.append({
                "id": r["id"],
                "filename": r["filename"],
                "title": r["title"],
                "category": r["category"],
                "media_type": r["media_type"],
                "aspect_ratio": r["aspect_ratio"],
                "resolution": r["resolution"],
                "duration_seconds": r["duration_seconds"],
                "style": r["style"],
                "prompt": r["prompt"],
                "tags": r["tags"].split(",") if r["tags"] else [],
                "platforms": r["platforms"].split(",") if r["platforms"] else [],
                "local_path": r["local_path"],
                "file_size_bytes": r["file_size_bytes"],
                "created_at": r["created_at"]
            })
        return results

    def get_asset(self, asset_id: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM media_assets WHERE id = ?", (asset_id,))
            row = cur.fetchone()
            if not row:
                return None
            return {
                "id": row["id"],
                "filename": row["filename"],
                "title": row["title"],
                "category": row["category"],
                "media_type": row["media_type"],
                "aspect_ratio": row["aspect_ratio"],
                "resolution": row["resolution"],
                "duration_seconds": row["duration_seconds"],
                "style": row["style"],
                "prompt": row["prompt"],
                "tags": row["tags"].split(",") if row["tags"] else [],
                "platforms": row["platforms"].split(",") if row["platforms"] else [],
                "local_path": row["local_path"],
                "file_size_bytes": row["file_size_bytes"],
                "created_at": row["created_at"]
            }

    def export_catalog_json(self) -> Path:
        """Export full SQLite database to a structured JSON file."""
        all_assets = self.search_assets(limit=1000)
        catalog_data = {
            "version": "1.0.0",
            "style": "cyber_zen_tech",
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "total_assets": len(all_assets),
            "assets": all_assets
        }
        with open(self.json_path, "w", encoding="utf-8") as f:
            json.dump(catalog_data, f, ensure_ascii=False, indent=2)
        return self.json_path

    def get_statistics(self) -> Dict[str, Any]:
        """Get summary statistics of the media asset bank."""
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT count(*) as total, sum(file_size_bytes) as total_bytes FROM media_assets")
            row = cur.fetchone()
            total_count = row["total"] or 0
            total_bytes = row["total_bytes"] or 0

            cur.execute("SELECT media_type, count(*) as count FROM media_assets GROUP BY media_type")
            by_type = {r["media_type"]: r["count"] for r in cur.fetchall()}

            cur.execute("SELECT category, count(*) as count FROM media_assets GROUP BY category")
            by_category = {r["category"]: r["count"] for r in cur.fetchall()}

            cur.execute("SELECT aspect_ratio, count(*) as count FROM media_assets GROUP BY aspect_ratio")
            by_ratio = {r["aspect_ratio"]: r["count"] for r in cur.fetchall()}

        return {
            "total_assets": total_count,
            "total_size_mb": round(total_bytes / (1024 * 1024), 2),
            "by_type": by_type,
            "by_category": by_category,
            "by_ratio": by_ratio,
            "db_path": str(self.db_path),
            "json_path": str(self.json_path)
        }


def main():
    catalog = MediaBankCatalog()
    stats = catalog.get_statistics()
    print("=== ZENPHAM Media Asset Bank Catalog ===")
    print(f"Total Assets: {stats['total_assets']} ({stats['total_size_mb']} MB)")
    print(f"By Type: {stats['by_type']}")
    print(f"By Category: {stats['by_category']}")
    print(f"By Aspect Ratio: {stats['by_ratio']}")


if __name__ == "__main__":
    main()
