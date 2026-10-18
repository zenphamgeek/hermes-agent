"""Unit & Integration Tests for Short Drama Storage, Multi-CDN, Catalog Indexer, Egress Sync Manager & Shared GDrive Sync."""

from __future__ import annotations

import struct
from pathlib import Path

from apps.short_drama_platform.cdn_catalog_indexer import CDNCatalogIndexer
from apps.short_drama_platform.egress_gdrive_sync_tool import (
    SHARED_DRAMA_FOLDER_ID,
    SHARED_DRAMA_OWNER_EMAIL,
    SHARED_DRAMA_OWNER_PROFILE,
    EgressGDriveSyncTool,
)
from apps.short_drama_platform.egress_sync_manager import EgressFullSetSyncManager
from apps.short_drama_platform.storage_cdn_engine import (
    FFmpegFaststartPipeline,
    MultiCDNStorageEngine,
    URLTokenSigner,
    compute_qiniu_qetag,
    inspect_mp4_faststart,
)

ARTIFACT_DIR = Path("/home/zen/.gemini/antigravity-cli/brain/c3591197-7a63-4a66-b82e-9750870acceb")


def test_qiniu_qetag_small_and_large_files(tmp_path: Path) -> None:
    poster_path = ARTIFACT_DIR / "cdn_sample_poster.jpg"
    video_path = ARTIFACT_DIR / "cdn_ep1_full_1080p.mp4"

    if poster_path.exists():
        assert compute_qiniu_qetag(poster_path) == "FpQTXKul1gaiJr3VMURXponpDRW9"

    if video_path.exists():
        assert compute_qiniu_qetag(video_path) == "lsQhzMN3B0jH8MK9Yvg4154M3-Nu"

    small_file = tmp_path / "small.bin"
    small_file.write_bytes(b"hello-qiniu-kodo")
    q_small = compute_qiniu_qetag(small_file)
    assert q_small.startswith("F")

    large_file = tmp_path / "large.bin"
    large_file.write_bytes(b"A" * (5 * 1024 * 1024))
    q_large = compute_qiniu_qetag(large_file)
    assert q_large.startswith("l")


def test_inspect_mp4_faststart(tmp_path: Path) -> None:
    video_path = ARTIFACT_DIR / "cdn_ep1_full_1080p.mp4"
    if video_path.exists():
        info = inspect_mp4_faststart(video_path)
        assert info["is_faststart"] is True
        assert info["ftyp_offset"] == 0
        assert info["moov_offset"] == 32
        assert info["moov_size"] == 210851
        assert info["mdat_offset"] == 210891
        assert info["mdat_size"] == 52506464
        assert info["moov_offset"] < info["mdat_offset"]

    non_fast = tmp_path / "non_faststart.mp4"
    ftyp_box = struct.pack(">I4s", 16, b"ftyp") + b"isom\x00\x00\x02\x00"
    mdat_box = struct.pack(">I4s", 24, b"mdat") + (b"\x00" * 16)
    moov_box = struct.pack(">I4s", 16, b"moov") + (b"\x00" * 8)
    non_fast.write_bytes(ftyp_box + mdat_box + moov_box)

    nf_info = inspect_mp4_faststart(non_fast)
    assert nf_info["is_faststart"] is False
    assert nf_info["mdat_offset"] < nf_info["moov_offset"]


def test_url_token_signer_prevents_unsigned_bypass() -> None:
    signer = URLTokenSigner(secret_key="73a74wxa58179eef93")
    path = "/video/20260831/7986b1e28411486c979e87ed0dc23ab7/cloudv-transfer/ep1_0_5.mp4"
    signed = signer.sign_url(
        "https://cf-sgn.shortdrama.edge",
        path,
        ttl_seconds=7200,
        uid=88001329,
        eid=520293664011,
        now=1760000000,
    )
    assert signed["cache_key"] == path
    assert "wsSecret=" in signed["url"]
    assert "wsTime=" in signed["url"]

    ok, reason = signer.verify_token(
        path,
        signed["ws_secret"],
        signed["ws_time"],
        uid=88001329,
        eid=520293664011,
        now=1760001000,
    )
    assert ok is True
    assert reason == "valid"

    ok_empty, reason_empty = signer.verify_token(path, "", "", uid=88001329, eid=520293664011)
    assert ok_empty is False
    assert "missing" in reason_empty

    ok_exp, reason_exp = signer.verify_token(
        path,
        signed["ws_secret"],
        signed["ws_time"],
        uid=88001329,
        eid=520293664011,
        now=1760009000,
    )
    assert ok_exp is False
    assert reason_exp == "token_expired"


def test_multi_cdn_and_ffmpeg_pipeline() -> None:
    engine = MultiCDNStorageEngine()
    edge = engine.select_edge_node(prefer_zero_egress=True)
    assert edge["node_id"] in ("cf-sgn", "r2-edge")
    assert edge["egress_cost_per_gb_usd"] == 0.0

    comp = engine.calculate_egress_comparison(monthly_tb=100.0)
    assert comp["savings_vs_qiniu_wangsu_pct"] > 90.0
    assert comp["providers"]["cloudflare_r2_b2_zero_egress"]["egress_usd"] == 0.0

    variants = FFmpegFaststartPipeline.build_all_variants("master.mp4", "/tmp/out", "ep01")
    assert "+faststart" in variants["cmd_1080p"]
    assert "2032k" in variants["cmd_1080p"]
    assert "1220k" in variants["cmd_720p"]
    assert "fmp4" in variants["cmd_hls_fmp4"]


def test_egress_gdrive_sync_tool_profiles_and_listing() -> None:
    tool = EgressGDriveSyncTool(auto_start_mesh=True)
    profiles = tool.list_egress_profiles()
    assert len(profiles) == 16
    by_name = {p["profile"]: p for p in profiles}
    assert by_name["innoria-team"]["proxy_url"] == "http://127.0.0.1:20129"
    assert by_name["innoria-team"]["is_healthy"] is True
    assert by_name["ariana"]["proxy_url"] == "http://127.0.0.1:20130"
    assert by_name["ariana"]["is_healthy"] is True
    assert SHARED_DRAMA_FOLDER_ID == "1jM0eFJy85aN3ksvdOFaxPzbDx9QuATiq"
    assert SHARED_DRAMA_OWNER_EMAIL == "innoria.team@gmail.com"
    assert SHARED_DRAMA_OWNER_PROFILE == "innoria-team"


def test_cdn_catalog_indexer_builds_and_searches() -> None:
    indexer = CDNCatalogIndexer()
    index_data = indexer.build_or_refresh_index(refresh_gdrive=True)
    stats = indexer.get_index_stats()

    assert stats["total_categories"] == 7
    assert stats["total_dramas"] >= 11
    assert stats["total_episodes"] >= 95
    assert stats["gdrive_shared_by"] == "innoria.team@gmail.com"
    assert stats["gdrive_shared_folder_id"] == "1jM0eFJy85aN3ksvdOFaxPzbDx9QuATiq"
    assert index_data["categories"][0]["id"] == 57777

    aerilon = indexer.get_series_detail(52021452445)
    assert aerilon["vname"] == "Journey to Aerilon Kingdom"
    assert len(aerilon["episodes"]) == 95
    ep1 = aerilon["episodes"][0]
    assert ep1["qetag"] == "lsQhzMN3B0jH8MK9Yvg4154M3-Nu"
    assert "local_cache" in ep1["storage_locations"]
    assert "gdrive_shared_drama" in ep1["storage_locations"]

    matched = indexer.search_catalog(query="Aerilon", category_id=57779, sync_status="gdrive")
    assert len(matched) == 1
    assert matched[0]["vid"] == 52021452445


def test_egress_full_set_sync_manager_syncs_manifest_to_gdrive() -> None:
    mgr = EgressFullSetSyncManager()
    job_res = mgr.run_full_set_sync(
        vid=52021452445,
        strategy="consistent_hash",
        profile_name="innoria-team",
        max_episodes=1,
        sync_to_gdrive=True,
        reuse_local_cache=True,
    )
    assert job_res["status"] == "completed"
    assert job_res["progress_pct"] == 100.0
    assert job_res["shared_by"] == "innoria.team@gmail.com"
    assert job_res["shared_folder_id"] == "1jM0eFJy85aN3ksvdOFaxPzbDx9QuATiq"
    assert job_res["files_synced"] >= 3
    assert job_res["gdrive_manifest_file"] is not None
    assert job_res["gdrive_manifest_file"]["Name"] == "manifest_52021452445.json"

    summary = mgr.get_status_summary(refresh_gdrive=True)
    assert summary["shared_by"] == "innoria.team@gmail.com"
    assert summary["total_jobs"] >= 1
    assert "smart_guard" in summary
    gdrive_names = {f["Name"] for f in summary["gdrive_inventory"]["files"]}
    assert "manifest_52021452445.json" in gdrive_names
    assert "5711447501a010008ac63b5e00000000.jpg" in gdrive_names
    assert "555555555p5o603955565n656r387620_47d3eae382a74b139a97df920ce725f2_0_5.mp4" in gdrive_names


def test_smart_egress_guard_decorrelated_jitter_and_aimd() -> None:
    from apps.short_drama_platform.smart_egress_guard import SmartEgressDownloadGuard

    guard = SmartEgressDownloadGuard()
    samples = [guard.compute_next_jitter_delay_ms("innoria-team") for _ in range(20)]
    assert len(samples) == 20
    assert all(85.0 <= s <= 950.0 for s in samples)
    assert len(set(samples)) > 5  # non-robotic variance

    slot_before = guard.get_slot("innoria-team").cwnd
    assert slot_before == 4.0

    # Clean 206 Partial Content with low TTFB -> AIMD additive increase (+0.25)
    res_ok = guard.record_response("innoria-team", status_code=206, ttfb_ms=32.0, bytes_count=262144)
    assert res_ok["new_cwnd"] == 4.25
    assert res_ok["ttfb_spike"] is False

    # TTFB spike (> 2.5x baseline) -> AIMD multiplicative decrease (* 0.5)
    res_spike = guard.record_response("innoria-team", status_code=206, ttfb_ms=180.0, bytes_count=262144)
    assert res_spike["ttfb_spike"] is True
    assert res_spike["new_cwnd"] == round(4.25 * 0.5, 2)


def test_smart_egress_guard_circuit_breaker_and_429_failover() -> None:
    from apps.short_drama_platform.smart_egress_guard import SmartEgressDownloadGuard

    guard = SmartEgressDownloadGuard()
    drill = guard.simulate_cdn_rate_limit_event(
        profile_name="ariana",
        status_code=429,
        retry_after_sec=45,
    )
    assert drill["tripped_profile"] == "ariana"
    assert drill["circuit_state"] == "OPEN"
    assert drill["previous_cwnd"] == 4.0
    assert drill["new_cwnd"] == 2.0
    assert drill["failover_slot"]["profile"] == "innoria-team"
    assert drill["failover_slot"]["proxy_url"] == "http://127.0.0.1:20129"
    assert drill["failover_slot"]["failover_triggered"] is True
    assert drill["incident"] is not None
    assert drill["incident"]["status_code"] == 429

    # Selecting ariana while OPEN must automatically route to innoria-team
    chosen = guard.select_optimal_slot(series_vid=52021452445, preferred_profile="ariana")
    assert chosen["profile"] == "innoria-team"
    assert chosen["failover_triggered"] is True

    telemetry = guard.get_guard_telemetry()
    assert telemetry["risk"]["open_circuits_count"] == 1
    assert len(telemetry["recent_incidents"]) == 1

    reset_res = guard.reset_slot_circuit("ariana")
    assert "ariana" in reset_res["reset_profiles"]
    assert guard.get_slot("ariana").circuit_state == "CLOSED"


def test_smart_egress_guard_progressive_byte_range_resume_on_midstream_429(tmp_path: Path) -> None:
    from apps.short_drama_platform.smart_egress_guard import SmartEgressDownloadGuard

    guard = SmartEgressDownloadGuard()
    payload = (b"CHUNK_0_" * 128) + (b"CHUNK_1_" * 128) + (b"CHUNK_2_" * 128)
    total_len = len(payload)  # 3072 bytes
    calls: list[tuple[str, int, int]] = []

    def fake_chunk_fetcher(
        url: str,
        profile: str,
        start_byte: int,
        end_byte: int,
        if_range: str | None,
    ) -> tuple[int, bytes, dict[str, str]]:
        calls.append((profile, start_byte, end_byte))
        # Trip HTTP 429 on ariana at chunk 1 (start_byte == 1024)
        if profile == "ariana" and start_byte == 1024:
            return 429, b"", {"Retry-After": "60", "X-Amz-Cf-Pop": "SGN50-P2"}
        slice_bytes = payload[start_byte : end_byte + 1]
        headers = {
            "Content-Range": f"bytes {start_byte}-{start_byte + len(slice_bytes) - 1}/{total_len}",
            "ETag": '"FtestQetag123"',
            "Content-Type": "video/mp4",
            "X-Amz-Cf-Pop": "SGN50-P2",
        }
        return 206, slice_bytes, headers

    dest_file = tmp_path / "resumed_video.bin"
    dl = guard.download_with_smart_pacing(
        url="https://v4.xtv.media/video/test_progressive_0_5.mp4",
        dest_path=dest_file,
        preferred_profile="ariana",
        series_vid=52021452445,
        chunk_size_bytes=1024,
        chunk_fetcher=fake_chunk_fetcher,
    )

    assert dl["bytes_downloaded"] == total_len
    assert dest_file.read_bytes() == payload
    assert dl["initial_profile"] == "ariana"
    assert dl["final_profile"] == "innoria-team"
    assert dl["mid_stream_failovers"] == 1
    assert dl["chunks_count"] == 3
    assert dl["chunks_log"][0]["profile"] == "ariana"
    assert dl["chunks_log"][1]["profile"] == "innoria-team"
    assert dl["chunks_log"][2]["profile"] == "innoria-team"


def test_repository_control_panel_and_film_episodes_status() -> None:
    mgr = EgressFullSetSyncManager()
    panel = mgr.get_repository_control_panel_data(status_filter="ALL", page=1, page_size=24)

    kpis = panel["summary_kpis"]
    assert kpis["total_films"] == 240
    assert kpis["total_episodes"] == 11504
    assert kpis["total_cdn_urls"] == 23242
    assert kpis["synced_gdrive_films_count"] >= 5
    assert kpis["total_downloaded_episodes_count"] >= 7
    assert kpis["total_gdrive_files_count"] >= 18
    assert kpis["shared_by"] == "innoria.team@gmail.com"
    assert kpis["shared_folder_id"] == "1jM0eFJy85aN3ksvdOFaxPzbDx9QuATiq"
    assert len(panel["films"]) == 24

    synced_only = mgr.get_repository_control_panel_data(status_filter="SYNCED_GDRIVE", page=1, page_size=24)
    assert len(synced_only["films"]) >= 5
    assert all(f["film_sync_status"] == "SYNCED_GDRIVE" for f in synced_only["films"])

    ep_status = mgr.get_film_episodes_status(52021452445)
    assert ep_status["vid"] == 52021452445
    assert ep_status["film_sync_status"] == "SYNCED_GDRIVE"
    assert ep_status["downloaded_episodes_count"] >= 3
    assert ep_status["gdrive_synced_episodes_count"] >= 3
    assert len(ep_status["episodes"]) == 95
    assert ep_status["episodes"][0]["download_state"] == "SYNCED_GDRIVE"
    assert ep_status["episodes"][1]["download_state"] == "SYNCED_GDRIVE"
    assert ep_status["episodes"][2]["download_state"] == "SYNCED_GDRIVE"


def test_multidisciplinary_council_and_live_download_infographic() -> None:
    mgr = EgressFullSetSyncManager()
    payload = mgr.get_council_and_live_infographic(vid=52021452445, episodeorder=6)

    assert len(payload["council_chairs"]) == 3
    assert payload["zeigarnik_curve"]["vid"] == 52021452445
    assert payload["zeigarnik_curve"]["peak_zeigarnik_tension_pct"] == 96.8
    assert len(payload["zeigarnik_curve"]["curve"]) == 95
    ep6_point = payload["zeigarnik_curve"]["curve"][5]
    assert ep6_point["episodeorder"] == 6
    assert ep6_point["tension_score"] == 96.8
    assert ep6_point["hook_type"] == "ZEIGARNIK_PAYWALL_CLIFFHANGER"

    dopamine = payload["episode_dopamine_arc"]
    assert dopamine["auto_next_countdown_sec"] == 3.0
    assert len(dopamine["beats"]) == 4

    infographic = payload["live_download_infographic"]
    assert len(infographic["pipeline_topology"]["nodes"]) == 5
    assert len(infographic["pipeline_topology"]["edges"]) == 4
    assert len(infographic["category_breakdown"]) == 7
    assert len(infographic["conversion_funnel"]) == 5

    qoe = payload["mp4_byte_range_qoe"]
    assert qoe["is_faststart"] is True
    assert qoe["atoms"][1]["box_type"] == "moov"
    assert qoe["atoms"][1]["offset_start"] == 32
    assert len(qoe["chunks_4mib"]) == 13
    assert "harvester_live_progress" in payload


def test_continuous_harvester_and_live_progress_telemetry() -> None:
    mgr = EgressFullSetSyncManager()

    # Verify all 3 speed profiles can be selected dynamically
    for prof_key, expected_workers in (
        ("SAFE_STEALTH", 4),
        ("MAX_SWARM_BLITZ", 16),
        ("BALANCED_TURBO", 12),
    ):
        res = mgr.set_harvester_profile(prof_key)
        assert res["speed_profile"] == prof_key
        assert res["profile_config"]["workers"] == expected_workers

    lp = mgr.get_harvester_live_progress()
    assert lp["speed_profile"] == "BALANCED_TURBO"
    assert lp["active_workers"] == 12
    assert lp["total_egress_slots"] == 16
    assert lp["total_catalog_films"] == 240
    assert lp["total_catalog_episodes"] == 11504
    assert lp["tier1_free_mp4_total"] == 2868
    assert lp["tier2_vip_indexed_total"] == 8636
    assert lp["synced_films_count"] >= 50
    assert lp["downloaded_episodes_count"] >= 200
    assert lp["total_gdrive_files_count"] >= 250
    assert len(lp["in_flight_slots"]) == 16
    assert lp["gdrive_destination"]["shared_by"] == "innoria.team@gmail.com"
    assert lp["gdrive_destination"]["shared_folder_id"] == "1jM0eFJy85aN3ksvdOFaxPzbDx9QuATiq"


def test_cloudflare_free_tier_stateless_zero_db_engine() -> None:
    from apps.short_drama_platform.storage_cdn_engine import CloudflareFreeTierStatelessEngine

    signer = URLTokenSigner(secret_key="dramaly-cf-free-tier-secret")
    cf_engine = CloudflareFreeTierStatelessEngine(signer=signer)

    # 1. Deterministic Opaque KDF eliminates sibling enumeration without any DB
    k1 = signer.derive_opaque_object_key("series_99", 1, profile="0_5")
    k2 = signer.derive_opaque_object_key("series_99", 2, profile="0_5")
    assert k1 != k2
    assert k1.startswith("/v/") and k1.endswith("_0_5.mp4")
    assert "series_99" not in k1
    assert k1 == signer.derive_opaque_object_key("series_99", 1, profile="0_5")

    # 2. Stateless entitlement token verification (0 DB/KV reads)
    tok = signer.sign_stateless_entitlement(uid="u_100", series_id="series_99", max_unlocked_ep=6, is_vip=False, now=1760000000)
    ok_ep6, reason_ep6, _ = signer.verify_stateless_entitlement(tok, "series_99", 6, now=1760001000)
    assert ok_ep6 is True and reason_ep6 == "authorized_episode"

    ok_ep7, reason_ep7, _ = signer.verify_stateless_entitlement(tok, "series_99", 7, now=1760001000)
    assert ok_ep7 is False and reason_ep7 == "episode_locked_requires_vip"

    # 3. Free tier routing & automatic quota fallback (R2 Class B & Storage Guard)
    route_free = cf_engine.evaluate_free_tier_routing("series_99", 3, r2_used_gb=5.0, r2_class_b_reads_mtd=100_000)
    assert route_free["allowed"] is True
    assert route_free["storage_tier"] == "TIER_0_CF_EDGE_CACHE_OVER_R2_FREE"
    assert route_free["zero_database_dependencies"] is True

    # Locked episode > 6 blocked at edge for non-VIP
    route_locked = cf_engine.evaluate_free_tier_routing("series_99", 8, is_vip=False)
    assert route_locked["allowed"] is False

    # Quota near ceiling triggers automatic Zero Trust Tunnel + Edge Cache fallback and R2 LRU eviction flag
    route_fallback = cf_engine.evaluate_free_tier_routing(
        "series_99", 2, r2_used_gb=9.4, r2_class_b_reads_mtd=900_000, is_vip=True
    )
    assert route_fallback["allowed"] is True
    assert route_fallback["storage_tier"] == "TIER_1_CF_EDGE_CACHE_OVER_ZERO_TRUST_TUNNEL"
    assert route_fallback["quotas"]["r2_lru_eviction_triggered"] is True



