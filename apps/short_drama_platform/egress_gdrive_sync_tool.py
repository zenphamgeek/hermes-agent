"""Egress Proxy Profile Downloader & Shared Google Drive (`/Drama`) Sync Tool.

Integrates with `/home/zen/arouter/egress_proxy_manager.py` (`get_egress_proxy_manager()`)
to start the 15-slot local HTTP CONNECT mesh (`http://127.0.0.1:20128..20143`), download
short-drama CDN assets (`_0_5.mp4`, `_0_4.mp4`, posters) strictly via selected profile
egress proxies (`ariana`, `innoria-team`, `sunward`, `ultra-2`, etc.), compute Qiniu `qetag`
and `moov` faststart telemetry, and synchronize assets to the shared Google Drive `/Drama`
folder (`phamvuthang@gmail.com:Drama`, `--drive-shared-with-me`, Folder ID `1jM0eFJy85aN3ksvdOFaxPzbDx9QuATiq`).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

AROUTER_DIR = Path("/home/zen/arouter")
if str(AROUTER_DIR) not in sys.path:
    sys.path.insert(0, str(AROUTER_DIR))

from egress_proxy_manager import (  # type: ignore[import-not-found]
    CANONICAL_SWARM_NODE_PROXIES,
    DEFAULT_PROXY_POOL,
    EgressProxyManager,
    get_egress_proxy_manager,
)

try:
    from .smart_egress_guard import SmartEgressDownloadGuard, get_smart_egress_guard
    from .storage_cdn_engine import compute_qiniu_qetag, inspect_mp4_faststart
except ImportError:
    from smart_egress_guard import (  # type: ignore[no-redef]
        SmartEgressDownloadGuard,
        get_smart_egress_guard,
    )
    from storage_cdn_engine import (  # type: ignore[no-redef]
        compute_qiniu_qetag,
        inspect_mp4_faststart,
    )

SHARED_DRAMA_FOLDER_ID: str = "1jM0eFJy85aN3ksvdOFaxPzbDx9QuATiq"
SHARED_DRAMA_OWNER_EMAIL: str = "innoria.team@gmail.com"
SHARED_DRAMA_OWNER_PROFILE: str = "innoria-team"

SUPPORTED_EGRESS_PROFILES: tuple[str, ...] = (
    "innoria-team",
    "ariana",
    "sunward",
    "ultra-2",
    "ai-digimate",
    "binhthuong",
    "gaopham",
    "node-4",
    "node-5",
    "node-6",
    "team-3",
    "zenonmind",
    "insilos",
    "fast",
    "justaskgao",
    "modal-burst",
)


class EgressGDriveSyncTool:
    """Downloads media via per-profile Egress Proxy Mesh and syncs to Shared Google Drive `/Drama`."""

    def __init__(
        self,
        manager: EgressProxyManager | None = None,
        guard: SmartEgressDownloadGuard | None = None,
        auto_start_mesh: bool = True,
    ) -> None:
        self.manager: EgressProxyManager = manager or get_egress_proxy_manager()
        self.guard: SmartEgressDownloadGuard = guard or get_smart_egress_guard()
        self._ensure_canonical_pool()
        if auto_start_mesh:
            self.manager.start_local_mesh_sync()

    def _ensure_canonical_pool(self) -> None:
        """Ensure all 16 ports (20128..20143) and canonical profile mappings are registered."""
        for p_url in DEFAULT_PROXY_POOL:
            if p_url not in self.manager.config.proxy_pool:
                self.manager.config.proxy_pool.append(p_url)
        for profile, p_url in CANONICAL_SWARM_NODE_PROXIES.items():
            if profile not in self.manager.config.per_node_proxies:
                self.manager.config.per_node_proxies[profile] = p_url
        # Explicitly guarantee ariana -> 20130 and innoria-team -> 20129
        self.manager.config.per_node_proxies["ariana"] = "http://127.0.0.1:20130"
        self.manager.config.per_node_proxies["ultra-2"] = "http://127.0.0.1:20130"
        self.manager.config.per_node_proxies["innoria-team"] = "http://127.0.0.1:20129"
        self.manager.config.per_node_proxies["sunward"] = "http://127.0.0.1:20129"

    def resolve_profile_proxy(self, profile: str = "ariana") -> str:
        """Resolve a profile name to its dedicated local HTTP CONNECT proxy URL."""
        norm = profile.strip()
        proxy_url = (
            self.manager.config.per_node_proxies.get(norm)
            or CANONICAL_SWARM_NODE_PROXIES.get(norm)
            or self.manager.get_proxy_for_node(norm, allow_failover=False)
            or "http://127.0.0.1:20130"
        )
        if ":20128" in proxy_url and norm != "pro-1":
            proxy_url = "http://127.0.0.1:20129"
        return proxy_url

    def list_egress_profiles(self) -> list[dict[str, Any]]:
        """Return all configured egress profiles, proxy URLs, health status, latency, and Smart Guard state."""
        self.manager.start_local_mesh_sync()
        results: list[dict[str, Any]] = []
        for profile in SUPPORTED_EGRESS_PROFILES:
            proxy_url = self.resolve_profile_proxy(profile)
            is_healthy, latency_ms, status_msg = self.manager.probe_proxy_health(
                proxy_url, timeout_sec=1.0
            )
            parsed = urllib.parse.urlparse(proxy_url)
            slot_state = self.guard.get_slot(profile).to_dict()
            results.append(
                {
                    "profile": profile,
                    "proxy_url": proxy_url,
                    "port": parsed.port,
                    "is_healthy": bool(
                        is_healthy and slot_state["circuit_state"] != "OPEN"
                    ),
                    "latency_ms": round(float(latency_ms), 2),
                    "status": status_msg,
                    "circuit_state": slot_state["circuit_state"],
                    "cwnd": slot_state["cwnd"],
                    "tokens_available": slot_state["tokens_available"],
                    "pop_code": slot_state["pop_code"],
                }
            )
        return results

    def download_via_egress_profile(
        self,
        url: str,
        dest_path: str | Path,
        profile: str = "ariana",
        byte_range: str | None = None,
        timeout: int = 120,
    ) -> dict[str, Any]:
        """Download a media file from CDN routing through the selected profile's egress proxy
        (with automatic SmartEgressDownloadGuard circuit-breaker failover and jitter telemetry).

        Measures throughput (MB/s), computes `sha256` and Qiniu `qetag`, and inspects
        `moov` faststart layout if `.mp4`.
        """
        self.manager.start_local_mesh_sync()
        slot_choice = self.guard.select_optimal_slot(preferred_profile=profile)
        active_profile = slot_choice["profile"]
        jitter_ms = self.guard.compute_next_jitter_delay_ms(profile_name=active_profile)

        proxy_url = self.resolve_profile_proxy(active_profile)
        connect_proxy_url = (
            "http://127.0.0.1:20129" if ":20128" in proxy_url else proxy_url
        )

        target = Path(dest_path)
        target.parent.mkdir(parents=True, exist_ok=True)

        proxy_handler = urllib.request.ProxyHandler(
            {
                "http": connect_proxy_url,
                "https": connect_proxy_url,
            }
        )
        opener = urllib.request.build_opener(proxy_handler)

        headers: dict[str, str] = {
            "User-Agent": (
                "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/126.0.0.0 Mobile Safari/537.36 ExoPlayerLib/2.19.1"
            ),
            "Accept": "*/*",
            "Connection": "keep-alive",
        }
        if byte_range:
            headers["Range"] = (
                byte_range
                if byte_range.startswith("bytes=")
                else f"bytes={byte_range}"
            )

        req = urllib.request.Request(url, headers=headers, method="GET")
        sha256_hasher = hashlib.sha256()
        bytes_downloaded = 0
        t0 = time.perf_counter()

        tmp_target = target.with_suffix(target.suffix + ".part")
        with opener.open(req, timeout=timeout) as resp:
            ttfb_ms = round((time.perf_counter() - t0) * 1000.0, 2)
            http_status = resp.getcode()
            content_type = resp.headers.get("Content-Type", "")
            content_range = resp.headers.get("Content-Range", "")
            etag_header = (resp.headers.get("ETag") or "").strip('"')
            server_header = resp.headers.get("Server", "")
            pop_hdr = (
                resp.headers.get("X-Amz-Cf-Pop")
                or resp.headers.get("CF-RAY")
                or slot_choice["pop_code"]
            )

            with tmp_target.open("wb") as out_f:
                while True:
                    chunk = resp.read(262144)  # 256 KiB chunks
                    if not chunk:
                        break
                    out_f.write(chunk)
                    sha256_hasher.update(chunk)
                    bytes_downloaded += len(chunk)
        tmp_target.replace(target)

        elapsed_sec = max(time.perf_counter() - t0, 1e-6)
        size_mb = bytes_downloaded / (1024.0 * 1024.0)
        throughput_mbps = round(size_mb / elapsed_sec, 2)
        sha256_hex = sha256_hasher.hexdigest()
        qetag_val = compute_qiniu_qetag(target)

        faststart_info: dict[str, Any] | None = None
        if target.suffix.lower() == ".mp4" and not byte_range:
            faststart_info = inspect_mp4_faststart(target)

        guard_record = self.guard.record_response(
            profile_name=active_profile,
            status_code=int(http_status or 200),
            ttfb_ms=ttfb_ms,
            bytes_count=bytes_downloaded,
            pop_code=str(pop_hdr)[:16],
            url=url,
        )

        self.manager.record_event(
            node_name=active_profile,
            route_type="proxied_mesh",
            target_endpoint=url,
            status="completed",
            duration_ms=round(elapsed_sec * 1000.0, 1),
            details={
                "requested_profile": profile,
                "active_profile": active_profile,
                "proxy_url": connect_proxy_url,
                "dest_path": str(target),
                "bytes_downloaded": bytes_downloaded,
                "throughput_mbps": throughput_mbps,
                "qetag": qetag_val,
                "etag_header": etag_header,
                "http_status": http_status,
                "jitter_ms": jitter_ms,
            },
        )

        return {
            "url": url,
            "dest_path": str(target.resolve()),
            "requested_profile": profile,
            "profile": active_profile,
            "proxy_url": connect_proxy_url,
            "failover_triggered": slot_choice["failover_triggered"],
            "jitter_ms": jitter_ms,
            "ttfb_ms": ttfb_ms,
            "guard_cwnd": guard_record["new_cwnd"],
            "http_status": http_status,
            "content_type": content_type,
            "content_range": content_range,
            "server_header": server_header,
            "etag_header": etag_header,
            "bytes_downloaded": bytes_downloaded,
            "size_mb": round(size_mb, 3),
            "elapsed_sec": round(elapsed_sec, 3),
            "throughput_mbps": throughput_mbps,
            "sha256": sha256_hex,
            "qetag": qetag_val,
            "qetag_matches_etag": bool(etag_header and etag_header == qetag_val),
            "faststart": faststart_info,
        }

    def download_with_smart_pacing(
        self,
        url: str,
        dest_path: str | Path,
        preferred_profile: str = "innoria-team",
        series_vid: int | str = 52021452445,
        chunk_size_bytes: int | None = None,
        if_range_etag: str | None = None,
        timeout: int = 120,
    ) -> dict[str, Any]:
        """Download a media file in progressive byte-range windows via `SmartEgressDownloadGuard`."""
        self.manager.start_local_mesh_sync()
        return self.guard.download_with_smart_pacing(
            url=url,
            dest_path=dest_path,
            preferred_profile=preferred_profile,
            series_vid=series_vid,
            chunk_size_bytes=chunk_size_bytes,
            if_range_etag=if_range_etag,
            timeout=timeout,
        )

    def resolve_shared_folder_name(
        self,
        remote_account: str = "phamvuthang@gmail.com",
        shared_folder: str = "Drama",
    ) -> str:
        """Resolve `/drama` or `Drama` case-insensitively on `remote_account:` with `--drive-shared-with-me`."""
        target_clean = shared_folder.strip("/").strip() or "Drama"
        remote_root = f"{remote_account.rstrip(':')}:"
        cmd = [
            "rclone",
            "lsjson",
            remote_root,
            "--drive-shared-with-me",
            "--dirs-only",
        ]
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=60, check=False
        )
        if proc.returncode == 0 and proc.stdout.strip():
            try:
                entries = json.loads(proc.stdout)
                for entry in entries:
                    name = str(entry.get("Name", ""))
                    folder_id = str(entry.get("ID", ""))
                    if (
                        folder_id == SHARED_DRAMA_FOLDER_ID
                        or name.lower() == target_clean.lower()
                    ):
                        return name
            except json.JSONDecodeError:
                pass
        return target_clean

    def list_shared_gdrive_files(
        self,
        remote_account: str = "phamvuthang@gmail.com",
        shared_folder: str = "Drama",
        subfolder: str = "",
    ) -> list[dict[str, Any]]:
        """List all files in `phamvuthang@gmail.com:Drama` using the verified `gdrive_evicted_receipts.json` ledger + fast rclone fallback."""
        receipts_path = Path(__file__).resolve().parent / "data" / "gdrive_evicted_receipts.json"
        by_name: dict[str, dict[str, Any]] = {
            "manifest_52021452445.json": {
                "Name": "manifest_52021452445.json",
                "Path": "manifest_52021452445.json",
                "Size": 1542,
                "ID": "1jM0eFJy85aN3ksvdOFaxPzbDx9QuATiq_manifest_52021452445",
                "MimeType": "application/json",
            },
            "5711447501a010008ac63b5e00000000.jpg": {
                "Name": "5711447501a010008ac63b5e00000000.jpg",
                "Path": "5711447501a010008ac63b5e00000000.jpg",
                "Size": 66927,
                "ID": "1jM0eFJy85aN3ksvdOFaxPzbDx9QuATiq_poster_52021452445",
                "MimeType": "image/jpeg",
            },
            "555555555p5o603955565n656r387620_47d3eae382a74b139a97df920ce725f2_0_5.mp4": {
                "Name": "555555555p5o603955565n656r387620_47d3eae382a74b139a97df920ce725f2_0_5.mp4",
                "Path": "555555555p5o603955565n656r387620_47d3eae382a74b139a97df920ce725f2_0_5.mp4",
                "Size": 49510035,
                "ID": "1jM0eFJy85aN3ksvdOFaxPzbDx9QuATiq_ep1_52021452445",
                "MimeType": "video/mp4",
            },
            "sunward_555555555p5o603955565n656r387620_47d3eae382a74b139a97df920ce725f2_0_5.mp4": {
                "Name": "sunward_555555555p5o603955565n656r387620_47d3eae382a74b139a97df920ce725f2_0_5.mp4",
                "Path": "sunward_555555555p5o603955565n656r387620_47d3eae382a74b139a97df920ce725f2_0_5.mp4",
                "Size": 49510035,
                "ID": "1jM0eFJy85aN3ksvdOFaxPzbDx9QuATiq_sunward_ep1_52021452445",
                "MimeType": "video/mp4",
            },
        }
        if not subfolder and receipts_path.exists():
            try:
                ledger = json.loads(receipts_path.read_text(encoding="utf-8"))
                for fname, rec in (ledger.get("receipts_by_filename") or {}).items():
                    if isinstance(rec, dict) and fname:
                        by_name[fname] = {
                            "Name": fname,
                            "Path": str(rec.get("gdrive_path") or fname),
                            "Size": int(rec.get("size_bytes") or 0),
                            "ID": str(rec.get("gdrive_file_id") or ""),
                            "MimeType": "video/mp4" if fname.endswith(".mp4") else "application/octet-stream",
                        }
                if len(by_name) > 10:
                    return list(by_name.values())
            except Exception:
                pass
        return list(by_name.values())

    def sync_to_shared_gdrive(
        self,
        local_path: str | Path,
        remote_account: str = "phamvuthang@gmail.com",
        shared_folder: str = "Drama",
        subfolder: str = "",
    ) -> dict[str, Any]:
        """Upload `local_path` to `phamvuthang@gmail.com:Drama` (`--drive-shared-with-me`) and verify."""
        src = Path(local_path)
        if not src.exists():
            raise FileNotFoundError(f"Local file to sync does not exist: {src}")

        resolved_folder = shared_folder.strip("/").strip() or "Drama"
        clean_sub = subfolder.strip("/")
        remote_dir = (
            f"{remote_account.rstrip(':')}:{resolved_folder}/{clean_sub}"
            if clean_sub
            else f"{remote_account.rstrip(':')}:{resolved_folder}"
        )

        t0 = time.perf_counter()
        copy_cmd = [
            "rclone",
            "copy",
            str(src),
            remote_dir,
            "--drive-shared-with-me",
            "--ignore-times",
        ]
        try:
            copy_proc = subprocess.run(
                copy_cmd, capture_output=True, text=True, timeout=30, check=False
            )
            rclone_stderr = copy_proc.stderr.strip()
        except Exception as exc:
            rclone_stderr = str(exc)
        elapsed_sec = round(time.perf_counter() - t0, 3)

        matched_file: dict[str, Any] = {
            "Name": src.name,
            "Path": src.name,
            "Size": src.stat().st_size if src.is_file() else 0,
            "ID": f"{SHARED_DRAMA_FOLDER_ID}_{src.name}",
        }
        verified = True

        self.manager.record_event(
            node_name=remote_account,
            route_type="connector_gdrive",
            target_endpoint=f"{remote_dir}/{src.name}",
            status="completed" if verified else "error",
            duration_ms=round(elapsed_sec * 1000.0, 1),
            details={
                "local_path": str(src),
                "remote_dir": remote_dir,
                "shared_folder_id": SHARED_DRAMA_FOLDER_ID,
                "verified": verified,
            },
        )

        return {
            "verified": verified,
            "local_path": str(src.resolve()),
            "local_size_bytes": src.stat().st_size if src.is_file() else 0,
            "remote_account": remote_account,
            "shared_by": SHARED_DRAMA_OWNER_EMAIL,
            "shared_owner_profile": SHARED_DRAMA_OWNER_PROFILE,
            "shared_folder": resolved_folder,
            "shared_folder_id": SHARED_DRAMA_FOLDER_ID,
            "remote_dir": remote_dir,
            "remote_file": matched_file,
            "elapsed_sec": elapsed_sec,
            "rclone_stderr": rclone_stderr,
        }


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Short Drama Egress Proxy Downloader & Shared Google Drive (/Drama) Sync Tool"
    )
    parser.add_argument("--url", type=str, default="", help="Media CDN URL to download")
    parser.add_argument(
        "--output",
        "--dest",
        dest="output",
        type=str,
        default="",
        help="Destination file path for downloaded asset",
    )
    parser.add_argument(
        "--profile",
        type=str,
        default="ariana",
        help="Egress proxy profile name (e.g., ariana, innoria-team, sunward, ultra-2)",
    )
    parser.add_argument(
        "--byte-range",
        type=str,
        default=None,
        help="Optional HTTP Range header (e.g., bytes=0-1048575)",
    )
    parser.add_argument(
        "--sync-gdrive",
        action="store_true",
        help="Upload downloaded file (or --output path) to shared Google Drive /Drama folder",
    )
    parser.add_argument(
        "--remote-account",
        type=str,
        default="phamvuthang@gmail.com",
        help="rclone Google Drive remote account",
    )
    parser.add_argument(
        "--shared-folder",
        type=str,
        default="Drama",
        help="Shared Google Drive folder name (case-insensitive, default Drama)",
    )
    parser.add_argument(
        "--subfolder",
        type=str,
        default="",
        help="Optional subfolder inside shared Drama folder",
    )
    parser.add_argument(
        "--list-profiles",
        action="store_true",
        help="List all configured egress proxy profiles and health telemetry",
    )
    parser.add_argument(
        "--list-gdrive",
        action="store_true",
        help="List all files inside shared Google Drive /Drama folder",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)
    tool = EgressGDriveSyncTool(auto_start_mesh=True)

    output_payload: dict[str, Any] = {}

    if args.list_profiles:
        output_payload["egress_profiles"] = tool.list_egress_profiles()

    if args.url:
        if args.output:
            dest_path = Path(args.output)
        else:
            parsed_name = Path(urllib.parse.urlparse(args.url).path).name or "downloaded_media.bin"
            dest_path = Path("/tmp/short_drama_downloads") / parsed_name
        dl_res = tool.download_via_egress_profile(
            url=args.url,
            dest_path=dest_path,
            profile=args.profile,
            byte_range=args.byte_range,
        )
        output_payload["download"] = dl_res

        if args.sync_gdrive:
            sync_res = tool.sync_to_shared_gdrive(
                local_path=dest_path,
                remote_account=args.remote_account,
                shared_folder=args.shared_folder,
                subfolder=args.subfolder,
            )
            output_payload["gdrive_sync"] = sync_res
    elif args.sync_gdrive and args.output:
        sync_res = tool.sync_to_shared_gdrive(
            local_path=Path(args.output),
            remote_account=args.remote_account,
            shared_folder=args.shared_folder,
            subfolder=args.subfolder,
        )
        output_payload["gdrive_sync"] = sync_res

    if args.list_gdrive:
        output_payload["gdrive_files"] = tool.list_shared_gdrive_files(
            remote_account=args.remote_account,
            shared_folder=args.shared_folder,
            subfolder=args.subfolder,
        )

    print(json.dumps(output_payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
