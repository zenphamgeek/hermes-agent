# Approvals Directory — ZenPham Series 2

This directory contains cryptographic, hash-bound episodic approval manifests for **ZenPham Series 2 ("The Anatomy of Modern LLMs", 25 episodes)**.

## Episodic Isolation & Reverse Production
Under the Episodic Isolation Protocol (Requirement R1):
- Each episode is executed as an atomic, isolated unit via `produce_episode_isolated.py --episode <k>`.
- Batch processing flags (`--all`, `--start`, `--end`) are strictly forbidden.
- Reverse production order ($25 \to 01$) requires that for any episode $k < 25$, the subsequent episode manifest `approvals/S02_EP{k+1:02d}_APPROVAL.json` must exist with `"decision": "approved"` before episode $k$ can be produced.

## Canonical Manifest Schema
Each approval file `approvals/S02_EP{k:02d}_APPROVAL.json` adheres to `canonical_manifest_schema.json` and records:
1. `git_hash`: Commit hash (`git rev-parse HEAD`) at the time of approval.
2. `asset_checksums`: Streaming SHA-256 digests of all core assets:
   - `script_md`: Pedagogical script markdown
   - `manim_py`: 2K QHD Manim mathematical animation source
   - `audio_master_wav`: TTS V0-Sense mastered audio
   - `video_master_mp4`: Rendered 2K QHD master video
   - `thumbnail_mosaic_png`: 5x5 Closing Thumbnail Mosaic asset
3. `closure_sha256`: Deterministic SHA-256 over canonicalized `{key, sha256}` asset manifest.
4. `quality_gates`: Verification status for `episodic_isolation`, `spatial_containment`, `anti_slide_deck`, `audio_ebur128`, and `mosaic_cta_grid`.
5. `metrics`: Measured video resolution, fps, audio loudness (LUFS/dBTP), and violation counters.
6. `decision`: `"approved"` or `"rejected"`.
