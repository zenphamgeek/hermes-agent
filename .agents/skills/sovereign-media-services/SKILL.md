---
name: sovereign-media-services
description: Sovereign Multimodal Media Generation Suite for Hermes Content Factory & AGY Fleet. Orchestrates Qwen-Image-2.1 Text-to-Image (anchor portrait at t=0, Vietnamese Áo Dài heritage, 1024x1536 & 1536x1024), Wan2.2-S2V-14B Speech-to-Video (live avatar, CFG 3.6 mouth dampening, -1.5dB audio headroom, CodeFormer face restoration), and 9Router AI Gateway (http://localhost:20128/v1) with 0% local GPU load.
---

# Sovereign Media Services — AGY Fleet & Content Factory Guide

> **Core Philosophy**: Zero-Local-GPU Compute • Cultural Authenticity • Evidence-First Multimodal Verification • Decoupled Tri-Tier Architecture

---

## 1. Sovereign Invariants & Architecture Topology

```
+-----------------------------------------------------------------------------------+
|                           TIER 1: DECISION & FLEET SWARM                          |
|                                     (AGY Fleet)                                   |
|   ultra-2 (Chief Architect) | pro-1 (Decomposer) | node-5 (Prompt Synthesizer)    |
|   node-7 (Cultural Lead)    | node-8 (Audio QA)  | ai-digimate (Lip-Sync Lead)    |
+------------------------------------------+----------------------------------------+
                                           | Bearer Auth / HTTP REST / SSE
                                           v
+-----------------------------------------------------------------------------------+
|                             TIER 2: UNIFIED AI GATEWAY                            |
|                                      (9Router)                                    |
|                              http://localhost:20128/v1                            |
|   Auth Sentinel | Priority Scheduling | Passive Token Ledger | SSE Multiplexer   |
+------------------------------------------+----------------------------------------+
                                           | Zero Local GPU (0% Workstation Load)
                                           v
+-----------------------------------------------------------------------------------+
|                           TIER 3: CLOUD COMPUTE WORKERS                           |
|                                   (Modal Fleet)                                   |
|   Worker Alpha: Wan2.2-S2V-14B (A100-80GB) | Worker Beta: Qwen-Image-2.1 (A10G)   |
|   Worker Gamma: ComfyUI CodeFormer (A10G)  | Worker Delta: VieNeu-TTS v3 Audio    |
+-----------------------------------------------------------------------------------+
```

### 1.1. Core Invariants
1. **Zero-Local-GPU Invariant**: Local workstation hardware (NVIDIA Quadro RTX 5000 16GB) compute utilization MUST strictly remain at **0%** during media synthesis. No diffusion, DiT, or heavy video rendering models are ever loaded into local VRAM.
2. **Audio Headroom Invariant (-1.5dB)**: Spoken audio fed into Wan2.2-S2V MUST maintain strict **-1.5dB True Peak headroom** (and EBU R128 loudness of **-14.5 ± 0.5 LUFS**). Acoustic clipping causes violent mouth deformation and lip-sync desynchronization.
3. **CFG 3.6 Mouth Dampening Invariant**: Classifier-Free Guidance for speech-to-video MUST be clamped to **3.6**. Over-driving CFG (>5.0) causes wide-mouth stretching; under-driving (<2.5) causes frozen lips.
4. **Master Visual Anchor Frame ($t=0$)**: Video generation MUST always branch from a pre-rendered master visual anchor frame generated via Qwen-Image-2.1 to guarantee character identity consistency across episodes.

---

## 2. Service Endpoints & Parameter Contracts

Target Gateway: `http://localhost:20128/v1`  
Bearer Token: `sk-thapsang-agent-alpha-889977`

### 2.1. Qwen-Image-2.1 (Text-to-Image Anchor)
- **Model**: `thapsang/qwen-image-2.1`
- **Endpoint**: `POST http://localhost:20128/v1/images/generations`
- **Compute Plane**: Modal Fast DiT Worker (NVIDIA A10G 24GB)
- **Standard Resolutions**:
  - `1024x1536` — 9:16 Vertical Shorts (Mobile First)
  - `1536x1024` — 16:9 Landscape Masterclass / Thumbnails
- **Sampling**: Flow Matching Euler / DPMSolver (28–35 steps)
- **Golden Cultural Recipe (Vietnamese Áo Dài)**:
  ```json
  {
    "model": "thapsang/qwen-image-2.1",
    "prompt": "An exquisite Vietnamese young woman wearing a royal blue silk Ao Dai with intricate gold phoenix embroidery, gentle dignity, natural skin texture, soft studio rim lighting, volumetric Tyndall god rays, 8k ultra cinematic portrait, pristine obsidian background",
    "negative_prompt": "deformed, distorted, ugly, extra limbs, blur, cartoon, 3d render, oversaturated, plastic skin",
    "size": "1024x1536"
  }
  ```

### 2.2. Wan2.2-S2V-14B (Speech-to-Video Live Avatar)
- **Model**: `thapsang/wan2.2-s2v`
- **Endpoint**: `POST http://localhost:20128/v1/video/generations`
- **Compute Plane**: Modal Heavy S2V Worker (NVIDIA A100-SXM4-80GB)
- **Key Parameters**:
  - `image`: Master visual anchor image path or base64
  - `audio`: Studio mastered WAV audio path or base64 (48kHz Stereo, -14.5 LUFS)
  - `cfg_scale`: `3.6` (strict mouth dampening)
  - `face_restoration`: `true` (CodeFormer face enhancement)
  - `fps`: `24` or `30`

---

## 3. AGY Fleet Multi-Node Production Workflow

When an Orchestrator receives a media generation task, dispatch responsibilities across Fleet nodes:

```
[User Request / Storyboard]
            │
            ▼
    [Orchestrator] ─── (Clef DAG Decomposition)
            │
            ├─► [node-7 / gaopham83]: Cultural Nuance & Wardrobe Styling Check
            ├─► [node-5 / synthesizer-5]: Generate Qwen Anchor Prompt & Negative Prompt
            ├─► [node-8 / zenonmind]: Audio Loudness & Headroom QA (-1.5dB True Peak)
            │
            ▼
    [9Router Gateway (:20128)] ───► [Modal Cloud A10G]: Generate Qwen Anchor Image
            │
            ▼
    [9Router Gateway (:20128)] ───► [Modal Cloud A100]: Generate Wan2.2 S2V Video
            │
            ▼
    [ultra-2 / lthn.Ariana]: Multi-Modal Quality Gate Verdict (AST, FFmpeg, Lip-Sync)
            │
            ▼
    [Asset Committed to Memory Graph & SHA-256 Ledger]
```

---

## 4. Verification & Quality Gate Checklist

Before declaring any media generation task complete:
1. [ ] **GPU Load Check**: Workstation GPU load remained at 0% (`nvidia-smi` confirms 0 compute processes).
2. [ ] **Audio EBU R128 Check**: `ffmpeg -i audio.wav -af ebur128 -f null -` reports True Peak $\le -1.5\text{dBTP}$ and LUFS $\in [-15.0, -14.0]$.
3. [ ] **Visual Integrity Check**: Contact sheet generated, zero facial artifacts, eyes open, mouth closed at resting beats.
4. [ ] **Asset Ledger Sync**: File path, resolution, duration, SHA-256 hash, and cost logged to `.asset_provenance_ledger.json`.
