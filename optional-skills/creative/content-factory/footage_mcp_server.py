#!/usr/bin/env python3
"""
Footage Vault MCP (Model Context Protocol) Server & REST API.
Provides standardized programmatic access to the 500GB S3 Footage Vault for:
- External Agents & Subagents (Hermes, Trae, Antigravity, Claude Desktop, Cursor)
- HTTP REST Clients, Webhooks, and n8n automations.
"""

import os
import sys
import json
import time
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

FACTORY_DIR = Path(__file__).parent
STUDIO_DIR = Path(__file__).parent.parent / "video-motion-studio"
sys.path.insert(0, str(FACTORY_DIR))
sys.path.insert(0, str(STUDIO_DIR))

from footage_vault import FootageVault, CATALOG_PATH, S3_ENDPOINT, S3_BUCKET


def filter_footage_clips(
    catalog: List[Dict[str, Any]],
    query: str,
    vault: FootageVault,
    category: Optional[str] = None,
    aspect_ratio: Optional[str] = None,
    min_quality: Optional[str] = None,
    min_duration_sec: Optional[int] = None,
    max_duration_sec: Optional[int] = None,
    top_k: int = 3
) -> List[Dict[str, Any]]:
    """Filter and rank footage clips based on query embeddings and visual constraints."""
    # 1. Base semantic search from FootageVault
    base_results = vault.search_footage(query=query, category=category, top_k=50)

    filtered = []
    for r in base_results:
        # Check aspect ratio
        res_str = r.get("resolution", "1920x1080")
        w, h = 1920, 1080
        if "x" in res_str:
            try:
                w, h = map(int, res_str.split("x"))
            except Exception:
                pass
        clip_ratio = "16:9" if w > h else ("9:16" if h > w else "1:1")

        if aspect_ratio and aspect_ratio != clip_ratio:
            continue

        # Check quality
        if min_quality:
            min_q = min_quality.lower().replace("p", "")
            if min_q == "1080" and (w < 1920 and h < 1080):
                continue
            elif min_q == "4k" and (w < 3840 and h < 2160):
                continue

        # Check duration
        dur = r.get("duration_sec", 6)
        if min_duration_sec and dur < min_duration_sec:
            continue
        if max_duration_sec and dur > max_duration_sec:
            continue

        r["aspect_ratio"] = clip_ratio
        filtered.append(r)

    return filtered[:top_k]


# ── 1. Model Context Protocol (MCP) JSON-RPC Implementation ──────────────

class FootageMCPServer:
    """Standard Model Context Protocol Server (JSON-RPC 2.0 over stdio)."""

    def __init__(self):
        self.vault = FootageVault()

    def get_tools_manifest(self) -> List[Dict[str, Any]]:
        """Return MCP tools definition schema."""
        return [
            {
                "name": "search_footage_vault",
                "description": "Query the 500GB S3 Footage Vault for high-quality video B-Roll clips using semantic keywords, category, aspect ratio, and resolution filters.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Semantic query or keywords (e.g. 'DNA double helix CRISPR', 'Zero-Trust cyber defense', 'calculus 3D torus')"
                        },
                        "category": {
                            "type": "string",
                            "enum": ["mathematics", "technology", "chemistry", "biology", "occupational-safety", "hologram-hud", "cyber-security", "cafe", "food", "logistics"],
                            "description": "Optional discipline / category filter"
                        },
                        "aspect_ratio": {
                            "type": "string",
                            "enum": ["16:9", "9:16", "1:1"],
                            "description": "Optional frame aspect ratio (16:9 for landscape, 9:16 for vertical Shorts/TikTok)"
                        },
                        "min_quality": {
                            "type": "string",
                            "enum": ["720p", "1080p", "4k"],
                            "description": "Minimum video resolution (default: 1080p)"
                        },
                        "min_duration_sec": {
                            "type": "integer",
                            "description": "Minimum clip duration in seconds"
                        },
                        "max_duration_sec": {
                            "type": "integer",
                            "description": "Maximum clip duration in seconds"
                        },
                        "top_k": {
                            "type": "integer",
                            "default": 3,
                            "description": "Maximum number of matching clips to return with S3 stream URLs"
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "get_footage_catalog_stats",
                "description": "Retrieve overview statistics, category distribution, and total volume of the S3 Footage Vault.",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "ingest_footage_asset",
                "description": "Ingest and segment a local or remote video asset into 1080p B-Roll clips, upload to S3, and index with vector embeddings.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "video_path": {"type": "string", "description": "Absolute path to the video file"},
                        "title": {"type": "string", "description": "Human-readable title of the footage"},
                        "category": {"type": "string", "description": "Category (e.g. mathematics, technology, biology)"},
                        "tags": {"type": "array", "items": {"type": "string"}, "description": "Semantic tags"}
                    },
                    "required": ["video_path", "title", "category"]
                }
            }
        ]

    def handle_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute MCP tool call."""
        if tool_name == "search_footage_vault":
            query = arguments.get("query", "")
            category = arguments.get("category")
            aspect_ratio = arguments.get("aspect_ratio")
            min_quality = arguments.get("min_quality")
            min_dur = arguments.get("min_duration_sec")
            max_dur = arguments.get("max_duration_sec")
            top_k = arguments.get("top_k", 3)

            results = filter_footage_clips(
                catalog=self.vault.catalog,
                query=query,
                vault=self.vault,
                category=category,
                aspect_ratio=aspect_ratio,
                min_quality=min_quality,
                min_duration_sec=min_dur,
                max_duration_sec=max_dur,
                top_k=top_k
            )
            return {
                "query": query,
                "total_matches": len(results),
                "clips": results
            }

        elif tool_name == "get_footage_catalog_stats":
            categories: Dict[str, int] = {}
            for item in self.vault.catalog:
                c = item.get("category", "uncategorized")
                categories[c] = categories.get(c, 0) + 1
            return {
                "total_clips": len(self.vault.catalog),
                "s3_endpoint": S3_ENDPOINT,
                "s3_bucket": S3_BUCKET,
                "categories": categories
            }

        elif tool_name == "ingest_footage_asset":
            video_p = Path(arguments.get("video_path", ""))
            title = arguments.get("title", "")
            cat = arguments.get("category", "general")
            tags = arguments.get("tags", [])
            clips = self.vault.segment_and_ingest_video(
                video_file=video_p,
                base_title=title,
                category=cat,
                tags=tags,
                clip_duration=6,
                notify_telegram=True
            )
            return {
                "status": "success",
                "ingested_clips_count": len(clips),
                "clips": clips
            }

        else:
            raise ValueError(f"Unknown tool: {tool_name}")

    def run_stdio_loop(self):
        """Run MCP Server over stdio stream."""
        for line in sys.stdin:
            line_s = line.strip()
            if not line_s:
                continue
            try:
                req = json.loads(line_s)
                msg_id = req.get("id")
                method = req.get("method")
                params = req.get("params", {})

                if method == "tools/list":
                    resp = {
                        "jsonrpc": "2.0",
                        "id": msg_id,
                        "result": {"tools": self.get_tools_manifest()}
                    }
                elif method == "tools/call":
                    name = params.get("name")
                    args = params.get("arguments", {})
                    res = self.handle_tool_call(name, args)
                    resp = {
                        "jsonrpc": "2.0",
                        "id": msg_id,
                        "result": {"content": [{"type": "text", "text": json.dumps(res, ensure_ascii=False, indent=2)}]}
                    }
                elif method == "initialize":
                    resp = {
                        "jsonrpc": "2.0",
                        "id": msg_id,
                        "result": {
                            "protocolVersion": "2024-11-05",
                            "capabilities": {"tools": {}},
                            "serverInfo": {"name": "hermes-footage-vault", "version": "1.0.0"}
                        }
                    }
                else:
                    resp = {
                        "jsonrpc": "2.0",
                        "id": msg_id,
                        "error": {"code": -32601, "message": f"Method not found: {method}"}
                    }
                print(json.dumps(resp, ensure_ascii=False), flush=True)
            except Exception as e:
                err_resp = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32603, "message": str(e)}
                }
                print(json.dumps(err_resp, ensure_ascii=False), flush=True)


# ── 2. HTTP REST API Server ──────────────────────────────────────────────

class FootageHTTPHandler(BaseHTTPRequestHandler):
    vault = FootageVault()

    def _set_headers(self, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers(200)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        qs = parse_qs(parsed.query)

        if path == "/health":
            self._set_headers(200)
            self.wfile.write(json.dumps({"status": "ok", "service": "footage-vault-api"}).encode("utf-8"))

        elif path == "/api/footage/stats" or path == "/api/footage/catalog":
            categories: Dict[str, int] = {}
            for item in self.vault.catalog:
                c = item.get("category", "uncategorized")
                categories[c] = categories.get(c, 0) + 1
            self._set_headers(200)
            self.wfile.write(json.dumps({
                "total_clips": len(self.vault.catalog),
                "s3_endpoint": S3_ENDPOINT,
                "s3_bucket": S3_BUCKET,
                "categories": categories
            }, ensure_ascii=False).encode("utf-8"))

        elif path == "/api/footage/search":
            query = qs.get("query", [""])[0]
            cat = qs.get("category", [None])[0]
            ratio = qs.get("aspect_ratio", [None])[0]
            qual = qs.get("min_quality", [None])[0]
            top_k = int(qs.get("top_k", [3])[0])

            results = filter_footage_clips(
                catalog=self.vault.catalog,
                query=query,
                vault=self.vault,
                category=cat,
                aspect_ratio=ratio,
                min_quality=qual,
                top_k=top_k
            )
            self._set_headers(200)
            self.wfile.write(json.dumps({
                "query": query,
                "total_matches": len(results),
                "clips": results
            }, ensure_ascii=False).encode("utf-8"))

        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Endpoint not found"}).encode("utf-8"))

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/footage/ingest":
            try:
                content_len = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_len)
                data = json.loads(body.decode("utf-8"))

                video_p = Path(data.get("video_path", ""))
                title = data.get("title", "")
                cat = data.get("category", "general")
                tags = data.get("tags", [])

                clips = self.vault.segment_and_ingest_video(
                    video_file=video_p,
                    base_title=title,
                    category=cat,
                    tags=tags,
                    clip_duration=6,
                    notify_telegram=True
                )
                self._set_headers(200)
                self.wfile.write(json.dumps({
                    "status": "success",
                    "ingested_clips_count": len(clips),
                    "clips": clips
                }, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self._set_headers(500)
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Endpoint not found"}).encode("utf-8"))


def run_http_server(host: str = "0.0.0.0", port: int = 8420):
    server = HTTPServer((host, port), FootageHTTPHandler)
    print(f"[*] Footage Vault HTTP REST API running on http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()


def main():
    parser = argparse.ArgumentParser(description="Footage Vault MCP & REST API Server")
    parser.add_argument("--mcp", action="store_true", help="Run in MCP (Model Context Protocol) stdio mode")
    parser.add_argument("--http", action="store_true", help="Run HTTP REST API server")
    parser.add_argument("--port", type=int, default=8420, help="HTTP API Port (default: 8420)")
    args = parser.parse_args()

    if args.mcp:
        server = FootageMCPServer()
        server.run_stdio_loop()
    else:
        run_http_server(port=args.port)


if __name__ == "__main__":
    main()
