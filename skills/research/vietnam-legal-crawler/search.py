#!/usr/bin/env python3
"""
Legal Document Search & Query Utility
Searches downloaded Vietnamese legal documents and signed attachments.
"""

import sys
import sqlite3
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

DEFAULT_OUTPUT_DIR = Path("/home/zen/hermes-agent/output_legal_docs")


def search_legal_documents(
    query: str,
    output_dir: Optional[Path] = None,
    limit: int = 10
) -> List[Dict[str, Any]]:
    out_dir = output_dir or DEFAULT_OUTPUT_DIR
    db_path = out_dir / "history.sqlite"
    if not db_path.exists():
        return []

    q = f"%{query.strip()}%"
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM legal_documents 
            WHERE so_hieu LIKE ? 
               OR trich_yeu LIKE ? 
               OR loai_van_ban LIKE ?
               OR co_quan_ban_hanh LIKE ?
            ORDER BY ngay_ban_hanh DESC
            LIMIT ?
        """, (q, q, q, q, limit))
        return [dict(r) for r in cursor.fetchall()]


def format_search_results_telegram(query: str, results: List[Dict[str, Any]]) -> str:
    """Format search results for Telegram HTML."""
    if not results:
        return (
            f"🔍 <b>TÌM KIẾM VĂN BẢN PHÁP LUẬT</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"❓ Không tìm thấy văn bản nào khớp với từ khóa: <code>{query}</code>\n"
            f"💡 Hãy thử tìm theo số hiệu (VD: <code>8631</code>, <code>08/2015</code>) hoặc cơ quan ban hành."
        )

    items = []
    for idx, r in enumerate(results, 1):
        so_hieu = r.get("so_hieu") or r.get("doc_id")
        loai = r.get("loai_van_ban") or "Văn bản"
        co_quan = r.get("co_quan_ban_hanh") or "Chính phủ"
        ngay = r.get("ngay_ban_hanh") or "N/A"
        trich = r.get("trich_yeu", "")[:120]
        url = r.get("url", "")
        link_str = f" [<a href='{url}'>Chi tiết</a>]" if url else ""
        items.append(
            f"{idx}. 📌 <b>{so_hieu}</b> ({loai} - {co_quan})\n"
            f"   🗓️ <i>Ngày BH: {ngay}</i>{link_str}\n"
            f"   📝 {trich}..."
        )

    body = "\n\n".join(items)
    return (
        f"🔍 <b>KẾT QUẢ TÌM KIẾM: \"{query}\"</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 Tìm thấy <b>{len(results)}</b> văn bản phù hợp:\n\n"
        f"{body}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🤖 <i>Hermes Legal Intelligence</i>"
    )


def main():
    parser = argparse.ArgumentParser(description="Search Vietnamese Legal Documents Database.")
    parser.add_argument("query", help="Keyword, document number, or topic to search")
    parser.add_argument("-o", "--output-dir", help="Output directory containing history.sqlite")
    parser.add_argument("-n", "--limit", type=int, default=10, help="Max results to display (default: 10)")
    parser.add_argument("--telegram", action="store_true", help="Format output for Telegram")
    args = parser.parse_args()

    out_p = Path(args.output_dir) if args.output_dir else None
    results = search_legal_documents(args.query, output_dir=out_p, limit=args.limit)

    if args.telegram:
        print(format_search_results_telegram(args.query, results))
    else:
        print(f"=== Search Results for: '{args.query}' ({len(results)} found) ===")
        for idx, r in enumerate(results, 1):
            print(f"{idx}. [{r.get('so_hieu')}] {r.get('loai_van_ban')} - {r.get('co_quan_ban_hanh')} ({r.get('ngay_ban_hanh')})")
            print(f"   {r.get('trich_yeu')[:100]}...")
            print(f"   URL: {r.get('url')}\n")


if __name__ == "__main__":
    main()
