"""Storage, Multi-CDN Edge Steering, Qiniu QETag, MP4 Faststart & Hardened URL Token Signer.

Implements:
1. `compute_qiniu_qetag`: Exact Qiniu Cloud Kodo `qetag` algorithm (4 MiB block SHA1 tree).
2. `inspect_mp4_faststart`: ISO BMFF / MP4 top-level atom scanner (`ftyp`, `moov`, `mdat`, `free`).
3. `URLTokenSigner`: Hardened HMAC-SHA256 / Wangsu-compatible URL token signer & verifier
   that blocks the DramaOra unsigned URL bypass while preserving `cache_key: path`.
4. `MultiCDNStorageEngine`: Cloudflare R2 (`r2://short-drama-origin`) + Backblaze B2
   (`b2://short-drama-archive`) Bandwidth Alliance zero-egress storage & Multi-CDN steering
   (`cf-sgn`, `gcc-hkg`, `r2-edge`).
5. `FFmpegFaststartPipeline`: Deterministic FFmpeg command builder for `_0_5.mp4` (1080p),
   `_0_4.mp4` (720p), and HLS fMP4 `.m3u8` preload segments with `-movflags +faststart`.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import struct
import time
import urllib.parse
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

QINIU_CHUNK_SIZE: int = 4 * 1024 * 1024  # 4 MiB (4,194,304 bytes)


def compute_qiniu_qetag(file_path: str | Path) -> str:
    """Compute the exact Qiniu Cloud Kodo `qetag` hash for a file.

    Algorithm:
    - If file size <= 4 MiB (4 * 1024 * 1024 bytes):
      `urlsafe_b64encode(b"\\x16" + sha1(data))`
    - If file size > 4 MiB:
      Split into 4 MiB chunks, compute `sha1(chunk)` (20-byte raw digest) per chunk,
      concatenate all chunk digests, and compute:
      `urlsafe_b64encode(b"\\x96" + sha1(concat_digests))`
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found for qetag calculation: {path}")

    file_size = path.stat().st_size
    if file_size <= QINIU_CHUNK_SIZE:
        data = path.read_bytes()
        digest = hashlib.sha1(data).digest()
        return base64.urlsafe_b64encode(b"\x16" + digest).decode("ascii")

    chunk_digests: list[bytes] = []
    with path.open("rb") as f:
        while True:
            chunk = f.read(QINIU_CHUNK_SIZE)
            if not chunk:
                break
            chunk_digests.append(hashlib.sha1(chunk).digest())

    concat_digest = hashlib.sha1(b"".join(chunk_digests)).digest()
    return base64.urlsafe_b64encode(b"\x96" + concat_digest).decode("ascii")


def inspect_mp4_faststart(file_path: str | Path) -> dict[str, Any]:
    """Scan top-level ISO BMFF / MP4 atoms (`ftyp`, `moov`, `mdat`, `free`, etc.).

    Returns:
        {
            "is_faststart": bool,
            "ftyp_offset": int,
            "moov_offset": int,
            "moov_size": int,
            "mdat_offset": int,
            "mdat_size": int,
            "atoms": list[dict],
        }
        where `is_faststart` is True iff `moov_offset < mdat_offset` (and both are present).
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"MP4 file not found: {path}")

    file_size = path.stat().st_size
    atoms: list[dict[str, Any]] = []
    ftyp_offset = -1
    moov_offset = -1
    moov_size = 0
    mdat_offset = -1
    mdat_size = 0

    with path.open("rb") as f:
        offset = 0
        while offset + 8 <= file_size:
            f.seek(offset)
            header = f.read(8)
            if len(header) < 8:
                break

            box_size, raw_type = struct.unpack(">I4s", header)
            try:
                box_type = raw_type.decode("ascii")
            except UnicodeDecodeError:
                box_type = raw_type.decode("latin-1", errors="replace")

            header_size = 8
            if box_size == 1:
                ext = f.read(8)
                if len(ext) < 8:
                    break
                (box_size,) = struct.unpack(">Q", ext)
                header_size = 16
            elif box_size == 0:
                box_size = file_size - offset

            if box_size < header_size:
                break

            is_truncated_box = (offset + box_size) > file_size
            atoms.append(
                {
                    "type": box_type,
                    "offset": offset,
                    "size": box_size,
                    "header_size": header_size,
                    "truncated": is_truncated_box,
                }
            )

            if box_type == "ftyp" and ftyp_offset < 0:
                ftyp_offset = offset
            elif box_type == "moov" and moov_offset < 0:
                moov_offset = offset
                moov_size = box_size
            elif box_type == "mdat" and mdat_offset < 0:
                mdat_offset = offset
                mdat_size = box_size

            if is_truncated_box:
                break

            offset += box_size

    is_faststart = bool(
        moov_offset >= 0 and mdat_offset >= 0 and moov_offset < mdat_offset
    )

    return {
        "is_faststart": is_faststart,
        "ftyp_offset": ftyp_offset,
        "moov_offset": moov_offset,
        "moov_size": moov_size,
        "mdat_offset": mdat_offset,
        "mdat_size": mdat_size,
        "atoms": atoms,
    }


class URLTokenSigner:
    """Hardened HMAC-SHA256 / Wangsu-compatible URL token signer & verifier.

    Remediates the DramaOra CDN vulnerability where omitting `wsSecret` & `wsTime`
    bypassed edge signature enforcement and returned `HTTP 200 OK` on raw paths.
    Also enforces `cache_key = path` so CDN edge caches are not fragmented by per-user tokens.
    """

    def __init__(
        self,
        secret_key: str = "short-drama-sovereign-hmac-secret-2026",
        default_ttl_seconds: int = 7200,
    ) -> None:
        if not secret_key or not secret_key.strip():
            raise ValueError("secret_key must be non-empty")
        self.secret_key = secret_key
        self.default_ttl_seconds = default_ttl_seconds

    @staticmethod
    def _normalize_path(path: str) -> str:
        parsed = urllib.parse.urlsplit(path)
        clean_path = parsed.path or "/"
        if not clean_path.startswith("/"):
            clean_path = "/" + clean_path
        return clean_path

    def _compute_signature(
        self, path: str, ws_time: str, uid: int | str = 0, eid: int | str = 0
    ) -> str:
        norm_path = self._normalize_path(path)
        payload = f"{norm_path}:{ws_time}:{uid}:{eid}".encode("utf-8")
        return hmac.new(
            self.secret_key.encode("utf-8"), payload, hashlib.sha256
        ).hexdigest()

    def sign_url(
        self,
        base_url: str,
        path: str,
        ttl_seconds: int = 7200,
        uid: int | str = 0,
        eid: int | str = 0,
        now: int | None = None,
    ) -> dict[str, Any]:
        """Sign a media path with HMAC-SHA256 (`wsSecret`, `wsTime`, `uid`, `eid`) and `cache_key`."""
        norm_path = self._normalize_path(path)
        issued_at = int(time.time()) if now is None else int(now)
        expires_at = issued_at + max(1, int(ttl_seconds))
        ws_time = f"{expires_at:08x}"
        ws_secret = self._compute_signature(norm_path, ws_time, uid=uid, eid=eid)

        clean_base = base_url.rstrip("/")
        query = urllib.parse.urlencode(
            {
                "wsSecret": ws_secret,
                "wsTime": ws_time,
                "uid": uid,
                "eid": eid,
            }
        )
        signed_url = f"{clean_base}{norm_path}?{query}"

        return {
            "url": signed_url,
            "signed_url": signed_url,
            "base_url": clean_base,
            "path": norm_path,
            "cache_key": norm_path,
            "ws_secret": ws_secret,
            "wsSecret": ws_secret,
            "ws_time": ws_time,
            "wsTime": ws_time,
            "uid": uid,
            "eid": eid,
            "issued_at": issued_at,
            "expires_at": expires_at,
            "ttl_seconds": int(ttl_seconds),
        }

    def verify_token(
        self,
        path: str,
        ws_secret: str | None,
        ws_time: str | None,
        uid: int | str = 0,
        eid: int | str = 0,
        now: int | None = None,
    ) -> tuple[bool, str]:
        """Verify HMAC-SHA256 token and expiration.

        Strictly fails closed on empty/missing token parameters (preventing DramaOra's
        unsigned URL bypass).
        """
        if not path or not str(path).strip():
            return False, "missing_path"
        if not ws_secret or not str(ws_secret).strip():
            return False, "missing_ws_secret_unsigned_bypass_blocked"
        if not ws_time or not str(ws_time).strip():
            return False, "missing_ws_time_unsigned_bypass_blocked"

        raw_time = str(ws_time).strip()
        try:
            expires_at = int(raw_time, 16)
        except ValueError:
            try:
                expires_at = int(raw_time, 10)
            except ValueError:
                return False, "malformed_ws_time"

        current_ts = int(time.time()) if now is None else int(now)
        if current_ts > expires_at:
            return False, "token_expired"

        expected = self._compute_signature(path, raw_time, uid=uid, eid=eid)
        if not hmac.compare_digest(expected, str(ws_secret).strip().lower()):
            return False, "invalid_signature"

        return True, "valid"

    def derive_opaque_object_key(
        self,
        series_id: str | int,
        episode_index: int | str,
        profile: str = "0_5",
        prefix: str = "/v",
    ) -> str:
        """Derive a deterministic, non-enumerable object storage path using HMAC-SHA256 (Zero-DB KDF).

        Eliminates sequential folder/filename enumeration (e.g. `/series_1/ep_1_0_5.mp4` -> `ep_2_0_5.mp4`)
        without requiring any database lookup table at the Cloudflare Edge.
        """
        clean_profile = str(profile).strip().lstrip("_") or "0_5"
        clean_prefix = "/" + str(prefix).strip("/")
        msg = f"opaque_kdf:{series_id}:{episode_index}:{clean_profile}".encode("utf-8")
        digest = hmac.new(self.secret_key.encode("utf-8"), msg, hashlib.sha256).hexdigest()
        shard = digest[:2]
        asset_hash = digest[2:26]
        return f"{clean_prefix}/{shard}/{asset_hash}_{clean_profile}.mp4"

    def sign_stateless_entitlement(
        self,
        uid: str | int,
        series_id: str | int,
        max_unlocked_ep: int = 6,
        is_vip: bool = False,
        ttl_seconds: int = 86400,
        now: int | None = None,
    ) -> str:
        """Mint a compact, zero-database HMAC-SHA256 entitlement token for Cloudflare Free Tier Edge."""
        issued_at = int(time.time()) if now is None else int(now)
        exp = issued_at + max(60, int(ttl_seconds))
        vip_flag = 1 if is_vip else 0
        payload_str = f"{uid}|{series_id}|{int(max_unlocked_ep)}|{vip_flag}|{exp}"
        sig = hmac.new(
            self.secret_key.encode("utf-8"),
            f"entitlement:{payload_str}".encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()[:32]
        raw_token = f"{payload_str}|{sig}"
        return base64.urlsafe_b64encode(raw_token.encode("utf-8")).decode("ascii").rstrip("=")

    def verify_stateless_entitlement(
        self,
        token: str,
        requested_series_id: str | int,
        requested_ep: int,
        now: int | None = None,
    ) -> tuple[bool, str, dict[str, Any]]:
        """Verify a stateless entitlement token in <0.1ms RAM without any DB or KV lookup."""
        if not token or not str(token).strip():
            return False, "missing_entitlement_token", {}
        try:
            padded = str(token).strip() + "=" * ((4 - len(str(token).strip()) % 4) % 4)
            decoded = base64.urlsafe_b64decode(padded.encode("ascii")).decode("utf-8")
            parts = decoded.split("|")
            if len(parts) != 6:
                return False, "malformed_entitlement_token", {}
            uid_str, series_str, max_ep_str, vip_str, exp_str, sig_hex = parts
            max_ep = int(max_ep_str)
            vip_flag = int(vip_str)
            exp = int(exp_str)
        except Exception:
            return False, "corrupt_entitlement_token", {}

        payload_str = f"{uid_str}|{series_str}|{max_ep}|{vip_flag}|{exp}"
        expected_sig = hmac.new(
            self.secret_key.encode("utf-8"),
            f"entitlement:{payload_str}".encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()[:32]
        if not hmac.compare_digest(expected_sig, sig_hex):
            return False, "invalid_entitlement_signature", {}

        current_ts = int(time.time()) if now is None else int(now)
        if current_ts > exp:
            return False, "entitlement_expired", {}

        meta = {
            "uid": uid_str,
            "series_id": series_str,
            "max_unlocked_ep": max_ep,
            "is_vip": bool(vip_flag == 1),
            "expires_at": exp,
        }
        if vip_flag == 1:
            return True, "authorized_vip", meta
        if str(series_str) in (str(requested_series_id), "*") and int(requested_ep) <= max_ep:
            return True, "authorized_episode", meta
        return False, "episode_locked_requires_vip", meta


class CloudflareFreeTierStatelessEngine:
    """Zero-Database Stateless Edge & R2 Quota Reliability Engine for Cloudflare Free Tier.

    Hard Free-Tier Ceilings Enforced:
    - R2 Storage: 9.0 GB soft ceiling / 10.0 GB hard free limit (auto-LRU evicts cold series to GDrive/NVMe).
    - R2 Class B (Read) Ops: 850,000 / 1,000,000 per month (protected via `caches.default` normalized Cache-Key).
    - R2 Class A (Write/List) Ops: 85,000 / 100,000 per month (`ListObjectsV2` disabled on public edge).
    - Workers Free CPU & Daily Requests: < 1.0 ms CPU/req (WebCrypto HMAC), 85,000 / 100,000 req/day before
      offloading free episodes (EP 1..6) to zero-worker Cloudflare Cache Rules + Tunnel fallback.
    """

    R2_FREE_STORAGE_LIMIT_GB: float = 10.0
    R2_SAFE_STORAGE_CAP_GB: float = 9.0
    R2_FREE_CLASS_B_READS_MONTH: int = 1_000_000
    R2_SAFE_CLASS_B_CAP: int = 850_000
    R2_FREE_CLASS_A_WRITES_MONTH: int = 100_000
    R2_SAFE_CLASS_A_CAP: int = 85_000
    WORKERS_FREE_REQ_DAY: int = 100_000
    WORKERS_SAFE_REQ_DAY_CAP: int = 85_000

    def __init__(self, signer: URLTokenSigner | None = None) -> None:
        self.signer = signer or URLTokenSigner()

    def evaluate_free_tier_routing(
        self,
        series_id: str | int,
        episode_index: int,
        profile: str = "0_5",
        r2_used_gb: float = 4.2,
        r2_class_b_reads_mtd: int = 120_000,
        worker_requests_today: int = 15_000,
        uid: str | int = "anon",
        is_vip: bool = False,
        now: int | None = None,
    ) -> dict[str, Any]:
        """Determine reliable, zero-DB routing across Cloudflare Edge Cache, R2 Free Tier, and Tunnel Fallback."""
        opaque_path = self.signer.derive_opaque_object_key(series_id, episode_index, profile=profile)
        is_free_episode = int(episode_index) <= 6

        r2_storage_healthy = float(r2_used_gb) < self.R2_SAFE_STORAGE_CAP_GB
        r2_reads_healthy = int(r2_class_b_reads_mtd) < self.R2_SAFE_CLASS_B_CAP
        worker_quota_healthy = int(worker_requests_today) < self.WORKERS_SAFE_REQ_DAY_CAP

        if not is_free_episode and not is_vip:
            return {
                "allowed": False,
                "reason": "vip_entitlement_required_for_ep_gt_6",
                "opaque_path": opaque_path,
                "storage_tier": "BLOCKED_AT_EDGE_ZERO_DB",
                "r2_class_b_consumed": 0,
            }

        signed = self.signer.sign_url(
            "https://dramaly.space",
            opaque_path,
            ttl_seconds=14400 if is_free_episode else 3600,
            uid=uid,
            eid=f"{series_id}_{episode_index}",
            now=now,
        )
        entitlement_token = self.signer.sign_stateless_entitlement(
            uid=uid,
            series_id=series_id,
            max_unlocked_ep=999 if is_vip else 6,
            is_vip=is_vip,
            now=now,
        )

        if r2_reads_healthy and worker_quota_healthy:
            active_tier = "TIER_0_CF_EDGE_CACHE_OVER_R2_FREE"
            origin_mode = "r2_binding_with_caches_default"
        else:
            active_tier = "TIER_1_CF_EDGE_CACHE_OVER_ZERO_TRUST_TUNNEL"
            origin_mode = "cloudflared_tunnel_8899_fallback"

        return {
            "allowed": True,
            "reason": "stateless_verified",
            "series_id": str(series_id),
            "episode_index": int(episode_index),
            "opaque_path": opaque_path,
            "normalized_cache_key": f"https://dramaly.space{opaque_path}",
            "signed_url": signed["url"],
            "entitlement_token": entitlement_token,
            "storage_tier": active_tier,
            "origin_mode": origin_mode,
            "quotas": {
                "r2_used_gb": round(float(r2_used_gb), 2),
                "r2_safe_cap_gb": self.R2_SAFE_STORAGE_CAP_GB,
                "r2_lru_eviction_triggered": not r2_storage_healthy,
                "r2_class_b_reads_mtd": int(r2_class_b_reads_mtd),
                "r2_reads_healthy": r2_reads_healthy,
                "worker_requests_today": int(worker_requests_today),
                "worker_quota_healthy": worker_quota_healthy,
            },
            "cache_control_header": "public, s-maxage=2592000, max-age=86400, immutable",
            "zero_database_dependencies": True,
        }



@dataclass
class EdgeNodeSpec:
    node_id: str
    provider: str
    pop_location: str
    base_url: str
    egress_cost_per_gb_usd: float
    avg_rtt_ms: float
    weight: int = 100
    healthy: bool = True


class MultiCDNStorageEngine:
    """Multi-CDN & Zero-Egress Object Storage Engine.

    Models:
    - Origin Hot Tier: Cloudflare R2 (`r2://short-drama-origin`, $0.00/GB egress, $0.015/GB-month)
    - Archive Cold Tier: Backblaze B2 (`b2://short-drama-archive`, $0.00/GB egress via
      Cloudflare Bandwidth Alliance, $0.006/GB-month)
    - Multi-CDN Edge POPs:
      * `cf-sgn`: Cloudflare Edge Ho Chi Minh City / Singapore ($0.00/GB egress)
      * `r2-edge`: Cloudflare R2 Custom Domain Edge Worker ($0.00/GB egress)
      * `gcc-hkg`: Gcore / Wangsu Hong Kong Fallback Edge ($0.028/GB egress)
    """

    R2_ORIGIN_URI = "r2://short-drama-origin"
    B2_ARCHIVE_URI = "b2://short-drama-archive"

    def __init__(self, signer: URLTokenSigner | None = None) -> None:
        self.signer = signer or URLTokenSigner()
        self.edge_nodes: dict[str, EdgeNodeSpec] = {
            "cf-sgn": EdgeNodeSpec(
                node_id="cf-sgn",
                provider="Cloudflare CDN + R2 Origin",
                pop_location="SGN (Ho Chi Minh City / Singapore)",
                base_url="https://cf-sgn.shortdrama.edge",
                egress_cost_per_gb_usd=0.00,
                avg_rtt_ms=18.5,
                weight=70,
                healthy=True,
            ),
            "r2-edge": EdgeNodeSpec(
                node_id="r2-edge",
                provider="Cloudflare R2 Direct Edge Worker",
                pop_location="Global Anycast (Zero Egress)",
                base_url="https://r2-edge.shortdrama.edge",
                egress_cost_per_gb_usd=0.00,
                avg_rtt_ms=22.0,
                weight=25,
                healthy=True,
            ),
            "gcc-hkg": EdgeNodeSpec(
                node_id="gcc-hkg",
                provider="Gcore / Wangsu Multi-CDN Fallback",
                pop_location="HKG (Hong Kong)",
                base_url="https://gcc-hkg.shortdrama.edge",
                egress_cost_per_gb_usd=0.028,
                avg_rtt_ms=34.0,
                weight=5,
                healthy=True,
            ),
        }

    def get_storage_tiers(self) -> dict[str, Any]:
        return {
            "origin_hot": {
                "uri": self.R2_ORIGIN_URI,
                "provider": "Cloudflare R2",
                "egress_per_gb_usd": 0.00,
                "storage_per_gb_month_usd": 0.015,
                "role": "Primary MP4 (_0_5.mp4 1080p, _0_4.mp4 720p), HLS fMP4 segments & posters",
            },
            "archive_cold": {
                "uri": self.B2_ARCHIVE_URI,
                "provider": "Backblaze B2 (Cloudflare Bandwidth Alliance)",
                "egress_per_gb_usd": 0.00,
                "storage_per_gb_month_usd": 0.006,
                "role": "Master mezzanine ProRes/H.264 originals & disaster recovery replica",
            },
            "edge_nodes": {
                k: {
                    "node_id": v.node_id,
                    "provider": v.provider,
                    "pop_location": v.pop_location,
                    "base_url": v.base_url,
                    "egress_cost_per_gb_usd": v.egress_cost_per_gb_usd,
                    "avg_rtt_ms": v.avg_rtt_ms,
                    "weight": v.weight,
                    "healthy": v.healthy,
                }
                for k, v in self.edge_nodes.items()
            },
        }

    def select_edge_node(
        self, prefer_zero_egress: bool = True, preferred_id: str | None = None
    ) -> dict[str, Any]:
        """Select optimal healthy CDN edge node with zero-egress priority."""
        if preferred_id and preferred_id in self.edge_nodes:
            node = self.edge_nodes[preferred_id]
            if node.healthy:
                return {
                    "node_id": node.node_id,
                    "provider": node.provider,
                    "base_url": node.base_url,
                    "egress_cost_per_gb_usd": node.egress_cost_per_gb_usd,
                    "avg_rtt_ms": node.avg_rtt_ms,
                }

        candidates = [n for n in self.edge_nodes.values() if n.healthy]
        if not candidates:
            candidates = list(self.edge_nodes.values())

        if prefer_zero_egress:
            zero_egress = [n for n in candidates if n.egress_cost_per_gb_usd == 0.0]
            if zero_egress:
                candidates = zero_egress

        best = min(candidates, key=lambda n: (n.egress_cost_per_gb_usd, n.avg_rtt_ms))
        return {
            "node_id": best.node_id,
            "provider": best.provider,
            "base_url": best.base_url,
            "egress_cost_per_gb_usd": best.egress_cost_per_gb_usd,
            "avg_rtt_ms": best.avg_rtt_ms,
        }

    def build_episode_delivery_urls(
        self,
        video_path_1080p: str,
        video_path_720p: str,
        poster_path: str,
        uid: int | str = 0,
        eid: int | str = 0,
        ttl_seconds: int = 7200,
    ) -> dict[str, Any]:
        """Generate signed Multi-CDN URLs across `cf-sgn`, `r2-edge`, and `gcc-hkg`."""
        primary = self.select_edge_node(prefer_zero_egress=True)
        signed_1080p = self.signer.sign_url(
            primary["base_url"], video_path_1080p, ttl_seconds=ttl_seconds, uid=uid, eid=eid
        )
        signed_720p = self.signer.sign_url(
            primary["base_url"], video_path_720p, ttl_seconds=ttl_seconds, uid=uid, eid=eid
        )
        signed_poster = self.signer.sign_url(
            primary["base_url"], poster_path, ttl_seconds=ttl_seconds, uid=uid, eid=eid
        )
        fallback_urls = [
            self.signer.sign_url(
                node.base_url, video_path_1080p, ttl_seconds=ttl_seconds, uid=uid, eid=eid
            )["url"]
            for node_id, node in self.edge_nodes.items()
            if node_id != primary["node_id"]
        ]
        return {
            "origin_uri": f"{self.R2_ORIGIN_URI}{self.signer._normalize_path(video_path_1080p)}",
            "archive_uri": f"{self.B2_ARCHIVE_URI}{self.signer._normalize_path(video_path_1080p)}",
            "selected_edge": primary["node_id"],
            "video_1080p": signed_1080p,
            "video_720p": signed_720p,
            "poster": signed_poster,
            "fallback_1080p_urls": fallback_urls,
        }

    def calculate_egress_comparison(
        self, monthly_tb: float = 100.0, storage_tb: float = 10.0
    ) -> dict[str, Any]:
        """Compare monthly TCO for `monthly_tb` TB egress + `storage_tb` TB storage.

        Compares:
        1. Legacy DramaOra Stack (Qiniu Kodo + Wangsu CDN)
        2. AWS S3 + CloudFront Standard
        3. Sovereign R2 + Backblaze B2 Bandwidth Alliance + Multi-CDN (`cf-sgn` / `r2-edge` / `gcc-hkg`)
        """
        gb_egress = float(monthly_tb) * 1024.0
        gb_storage = float(storage_tb) * 1024.0

        # 1. Qiniu Kodo ($0.014/GB storage) + Wangsu CDN ($0.045/GB APAC egress)
        qiniu_wangsu_storage_usd = round(gb_storage * 0.014, 2)
        qiniu_wangsu_egress_usd = round(gb_egress * 0.045, 2)
        qiniu_wangsu_total_usd = round(
            qiniu_wangsu_storage_usd + qiniu_wangsu_egress_usd, 2
        )

        # 2. AWS S3 ($0.023/GB storage) + CloudFront ($0.085/GB egress)
        aws_storage_usd = round(gb_storage * 0.023, 2)
        aws_egress_usd = round(gb_egress * 0.085, 2)
        aws_total_usd = round(aws_storage_usd + aws_egress_usd, 2)

        # 3. Cloudflare R2 ($0.015/GB hot) + Backblaze B2 ($0.006/GB archive)
        #    95% traffic served via cf-sgn + r2-edge ($0.00/GB), 5% burst via gcc-hkg ($0.028/GB)
        r2_b2_storage_usd = round(gb_storage * (0.015 + 0.006), 2)
        r2_pure_zero_egress_usd = 0.0
        r2_pure_total_usd = round(r2_b2_storage_usd, 2)

        multi_cdn_burst_egress_usd = round((gb_egress * 0.05) * 0.028, 2)
        multi_cdn_total_usd = round(r2_b2_storage_usd + multi_cdn_burst_egress_usd, 2)

        savings_vs_qiniu_usd = round(qiniu_wangsu_total_usd - multi_cdn_total_usd, 2)
        savings_vs_qiniu_pct = (
            round((savings_vs_qiniu_usd / qiniu_wangsu_total_usd) * 100.0, 2)
            if qiniu_wangsu_total_usd > 0
            else 0.0
        )
        savings_vs_aws_usd = round(aws_total_usd - multi_cdn_total_usd, 2)
        savings_vs_aws_pct = (
            round((savings_vs_aws_usd / aws_total_usd) * 100.0, 2)
            if aws_total_usd > 0
            else 0.0
        )

        return {
            "monthly_tb": monthly_tb,
            "monthly_gb": gb_egress,
            "storage_tb": storage_tb,
            "origin_uri": self.R2_ORIGIN_URI,
            "archive_uri": self.B2_ARCHIVE_URI,
            "edge_nodes": list(self.edge_nodes.keys()),
            "providers": {
                "qiniu_kodo_wangsu_cdn": {
                    "storage_usd": qiniu_wangsu_storage_usd,
                    "egress_usd": qiniu_wangsu_egress_usd,
                    "total_monthly_usd": qiniu_wangsu_total_usd,
                },
                "aws_s3_cloudfront": {
                    "storage_usd": aws_storage_usd,
                    "egress_usd": aws_egress_usd,
                    "total_monthly_usd": aws_total_usd,
                },
                "cloudflare_r2_b2_zero_egress": {
                    "storage_usd": r2_b2_storage_usd,
                    "egress_usd": r2_pure_zero_egress_usd,
                    "total_monthly_usd": r2_pure_total_usd,
                },
                "sovereign_multi_cdn_95_5": {
                    "storage_usd": r2_b2_storage_usd,
                    "egress_usd": multi_cdn_burst_egress_usd,
                    "total_monthly_usd": multi_cdn_total_usd,
                },
            },
            "savings_vs_qiniu_wangsu_usd": savings_vs_qiniu_usd,
            "savings_vs_qiniu_wangsu_pct": savings_vs_qiniu_pct,
            "savings_vs_aws_usd": savings_vs_aws_usd,
            "savings_vs_aws_pct": savings_vs_aws_pct,
        }


class FFmpegFaststartPipeline:
    """FFmpeg Transcode & Faststart Remux Pipeline matching DramaOra `_0_5.mp4` and `_0_4.mp4` specs.

    - `_0_5.mp4`: 1080x1920 (9:16), H.264 High@L4.0 (`avc1.640028`), 2032 kbps video,
      AAC-LC 128 kbps 44.1kHz stereo, `-movflags +faststart`.
    - `_0_4.mp4`: 720x1280 (9:16), H.264 High@L3.1 (`avc1.64001F`), 1220 kbps video,
      AAC-LC 128 kbps 44.1kHz stereo, `-movflags +faststart`.
    - HLS fMP4 `.m3u8`: 2.0s fragmented MP4 segments (`init.mp4` + `seg_%03d.m4s`) for
      instant RecyclerView next-episode Byte-Range / segment preloading.
    """

    @staticmethod
    def build_1080p_command(
        input_path: str | Path, output_path: str | Path
    ) -> list[str]:
        """Build FFmpeg command for `_0_5.mp4` (1080x1920 H.264 High@L4.0 2032k + AAC 128k)."""
        return [
            "ffmpeg",
            "-y",
            "-i",
            str(input_path),
            "-vf",
            "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2",
            "-c:v",
            "libx264",
            "-profile:v",
            "high",
            "-level:v",
            "4.0",
            "-pix_fmt",
            "yuv420p",
            "-r",
            "30",
            "-g",
            "60",
            "-keyint_min",
            "60",
            "-sc_threshold",
            "0",
            "-b:v",
            "2032k",
            "-maxrate",
            "2400k",
            "-bufsize",
            "4064k",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-ar",
            "44100",
            "-ac",
            "2",
            "-movflags",
            "+faststart",
            str(output_path),
        ]

    @staticmethod
    def build_720p_command(
        input_path: str | Path, output_path: str | Path
    ) -> list[str]:
        """Build FFmpeg command for `_0_4.mp4` (720x1280 H.264 High@L3.1 1220k + AAC 128k)."""
        return [
            "ffmpeg",
            "-y",
            "-i",
            str(input_path),
            "-vf",
            "scale=720:1280:force_original_aspect_ratio=decrease,pad=720:1280:(ow-iw)/2:(oh-ih)/2",
            "-c:v",
            "libx264",
            "-profile:v",
            "high",
            "-level:v",
            "3.1",
            "-pix_fmt",
            "yuv420p",
            "-r",
            "30",
            "-g",
            "60",
            "-keyint_min",
            "60",
            "-sc_threshold",
            "0",
            "-b:v",
            "1220k",
            "-maxrate",
            "1500k",
            "-bufsize",
            "2440k",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-ar",
            "44100",
            "-ac",
            "2",
            "-movflags",
            "+faststart",
            str(output_path),
        ]

    @staticmethod
    def build_hls_fmp4_command(
        input_path: str | Path,
        output_dir: str | Path,
        playlist_name: str = "index.m3u8",
    ) -> list[str]:
        """Build FFmpeg command for HLS fMP4 `.m3u8` preload segments (`init.mp4` + `.m4s`)."""
        out_dir = Path(output_dir)
        playlist_path = out_dir / playlist_name
        segment_pattern = str(out_dir / "seg_%03d.m4s")
        return [
            "ffmpeg",
            "-y",
            "-i",
            str(input_path),
            "-c:v",
            "copy",
            "-c:a",
            "copy",
            "-f",
            "hls",
            "-hls_time",
            "2",
            "-hls_playlist_type",
            "vod",
            "-hls_segment_type",
            "fmp4",
            "-hls_fmp4_init_filename",
            "init.mp4",
            "-hls_segment_filename",
            segment_pattern,
            "-movflags",
            "+faststart",
            str(playlist_path),
        ]

    @classmethod
    def build_all_variants(
        cls,
        input_path: str | Path,
        output_dir: str | Path,
        episode_stem: str,
    ) -> dict[str, Any]:
        """Build complete command set for `_0_5.mp4`, `_0_4.mp4`, and HLS fMP4 `.m3u8`."""
        out_dir = Path(output_dir)
        out_1080p = out_dir / f"{episode_stem}_0_5.mp4"
        out_720p = out_dir / f"{episode_stem}_0_4.mp4"
        hls_dir = out_dir / f"{episode_stem}_hls"
        return {
            "output_1080p": str(out_1080p),
            "output_720p": str(out_720p),
            "output_hls_playlist": str(hls_dir / "index.m3u8"),
            "cmd_1080p": cls.build_1080p_command(input_path, out_1080p),
            "cmd_720p": cls.build_720p_command(input_path, out_720p),
            "cmd_hls_fmp4": cls.build_hls_fmp4_command(out_1080p, hls_dir),
        }


def extract_mp4_video_dimensions(file_path: str | Path) -> dict[str, Any]:
    """Parse ISO BMFF `moov` -> `tkhd` & `mvhd` boxes directly in Python (<1ms, 0 subprocess)
    to extract video track `width`, `height`, and `duration_sec`.
    """
    path = Path(file_path)
    if not path.exists() or not path.is_file():
        return {"width": 0, "height": 0, "duration_sec": 0.0}

    try:
        fast = inspect_mp4_faststart(path)
        moov_offset = int(fast.get("moov_offset", -1))
        moov_size = int(fast.get("moov_size", 0))
        if moov_offset < 0 or moov_size <= 8:
            return {"width": 0, "height": 0, "duration_sec": 0.0}

        with path.open("rb") as f:
            f.seek(moov_offset)
            moov_bytes = f.read(min(moov_size, 2 * 1024 * 1024))

        width = 0
        height = 0
        duration_sec = 0.0

        # Parse mvhd for movie duration
        mvhd_pos = moov_bytes.find(b"mvhd")
        if mvhd_pos >= 4 and mvhd_pos + 24 <= len(moov_bytes):
            version = moov_bytes[mvhd_pos + 4]
            if version == 0 and mvhd_pos + 24 <= len(moov_bytes):
                timescale, duration_units = struct.unpack(
                    ">II", moov_bytes[mvhd_pos + 16 : mvhd_pos + 24]
                )
                if timescale > 0:
                    duration_sec = round(duration_units / float(timescale), 2)
            elif version == 1 and mvhd_pos + 36 <= len(moov_bytes):
                timescale, duration_units = struct.unpack(
                    ">IQ", moov_bytes[mvhd_pos + 24 : mvhd_pos + 36]
                )
                if timescale > 0:
                    duration_sec = round(duration_units / float(timescale), 2)

        # Scan all tkhd boxes inside moov for the video track (width > 0 and height > 0)
        search_idx = 0
        while True:
            tkhd_pos = moov_bytes.find(b"tkhd", search_idx)
            if tkhd_pos < 4:
                break
            box_start = tkhd_pos - 4
            (tkhd_size,) = struct.unpack(">I", moov_bytes[box_start:tkhd_pos])
            if 84 <= tkhd_size <= 128 and box_start + tkhd_size <= len(moov_bytes):
                w_fixed, h_fixed = struct.unpack(
                    ">II",
                    moov_bytes[box_start + tkhd_size - 8 : box_start + tkhd_size],
                )
                w = w_fixed >> 16
                h = h_fixed >> 16
                if w > width and h > height:
                    width = w
                    height = h
            search_idx = tkhd_pos + 4

        return {
            "width": int(width),
            "height": int(height),
            "duration_sec": float(duration_sec),
        }
    except Exception:
        return {"width": 0, "height": 0, "duration_sec": 0.0}


def audit_mp4_integrity_no_fake_pass(
    file_path: str | Path,
    expected_etag: str | None = None,
    expected_content_length: int | None = None,
) -> dict[str, Any]:
    """5-Gate `ZeroFakePassMediaSentinel` Mathematical & Binary MP4 Integrity Auditor.

    Enforces:
    - Gate 1 (`highest_quality_1080p_suffix`): Filename ends with `_0_5.mp4` (or `cdn_ep1_full_1080p.mp4`).
    - Gate 2 (`iso_bmff_mdat_complete`): `is_faststart == True`, `mdat_offset > 0`, `mdat_size > 0`,
      and `disk_bytes >= mdat_offset + mdat_size > 5_000_000` (catches any 1MiB/2MiB/4MiB truncated slice!).
    - Gate 3 (`resolution_1080x1920_verified`): Parsed ISO BMFF `tkhd` video resolution is `>= 1080x1920`
      (catches any 720p `highUrl` stream saved under a `_0_5.mp4` filename!).
    - Gate 4 (`qetag_merkle_verified`): `compute_qiniu_qetag` starts with `l` (`0x96` multi-block >4MiB)
      and matches `expected_etag` if provided.
    - Gate 5 (`content_length_exact_match`): `disk_bytes == expected_content_length` if provided.
    """
    path = Path(file_path)
    if not path.exists() or not path.is_file():
        return {
            "passed": False,
            "gates_passed_count": 0,
            "gates_total": 5,
            "verdict": "FAKE_PASS_REJECTED",
            "failure_reasons": ["FILE_NOT_FOUND"],
            "disk_bytes": 0,
            "mdat_end_bytes": 0,
            "width": 0,
            "height": 0,
            "duration_sec": 0.0,
            "qetag": "",
        }

    disk_bytes = path.stat().st_size
    fname = path.name
    failure_reasons: list[str] = []

    # Gate 1: Highest-quality 1080p suffix (_0_5.mp4)
    gate1_ok = fname.endswith("_0_5.mp4") or fname == "cdn_ep1_full_1080p.mp4"
    if not gate1_ok:
        failure_reasons.append("NOT_1080P_0_5_MP4_FILENAME")

    # Gate 2: ISO BMFF mdat completeness (disk_bytes >= mdat_offset + mdat_size > 5 MB)
    fast = inspect_mp4_faststart(path)
    mdat_offset = int(fast.get("mdat_offset", -1))
    mdat_size = int(fast.get("mdat_size", 0))
    mdat_end_bytes = (mdat_offset + mdat_size) if (mdat_offset > 0 and mdat_size > 0) else 0
    gate2_ok = bool(
        fast.get("is_faststart")
        and mdat_offset > 0
        and mdat_size > 0
        and disk_bytes >= mdat_end_bytes
        and disk_bytes > 5_000_000
    )
    if not gate2_ok:
        failure_reasons.append(
            f"TRUNCATED_MDAT_INCOMPLETE(disk={disk_bytes},expected_mdat_end={mdat_end_bytes})"
        )

    # Gate 3: Video Track Resolution >= 1080x1920 (or 1920x1080)
    dims = extract_mp4_video_dimensions(path)
    w = int(dims.get("width", 0))
    h = int(dims.get("height", 0))
    gate3_ok = (w >= 1080 and h >= 1920) or (w >= 1920 and h >= 1080)
    if not gate3_ok:
        failure_reasons.append(f"DOWNGRADED_RESOLUTION_{w}x{h}_BELOW_1080P")

    # Gate 4: Qiniu Merkle qetag starts with 'l' (> 4 MiB) & matches expected_etag
    qetag = compute_qiniu_qetag(path) if disk_bytes > 0 else ""
    clean_expected_etag = (expected_etag or "").strip().strip('"')
    gate4_ok = qetag.startswith("l") and (
        not clean_expected_etag or qetag == clean_expected_etag
    )
    if not gate4_ok:
        failure_reasons.append(
            f"QETAG_MISMATCH(computed={qetag},expected={clean_expected_etag or 'l*'})"
        )

    # Gate 5: Exact Content-Length match
    gate5_ok = (
        expected_content_length is None
        or int(expected_content_length) <= 0
        or disk_bytes == int(expected_content_length)
    )
    if not gate5_ok:
        failure_reasons.append(
            f"CONTENT_LENGTH_MISMATCH(disk={disk_bytes},expected={expected_content_length})"
        )

    gates_bools = [gate1_ok, gate2_ok, gate3_ok, gate4_ok, gate5_ok]
    gates_passed = sum(1 for g in gates_bools if g)
    passed = all(gates_bools)

    return {
        "file_path": str(path.resolve()),
        "filename": fname,
        "passed": passed,
        "gates_passed_count": gates_passed,
        "gates_total": 5,
        "verdict": "VERIFIED_1080P_FULL" if passed else "FAKE_PASS_REJECTED",
        "failure_reasons": failure_reasons,
        "disk_bytes": disk_bytes,
        "disk_mb": round(disk_bytes / (1024.0 * 1024.0), 2),
        "mdat_offset": mdat_offset,
        "mdat_size": mdat_size,
        "mdat_end_bytes": mdat_end_bytes,
        "is_faststart": bool(fast.get("is_faststart")),
        "width": w,
        "height": h,
        "duration_sec": float(dims.get("duration_sec", 0.0)),
        "qetag": qetag,
    }

