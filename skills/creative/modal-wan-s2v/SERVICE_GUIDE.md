# Wan2.2-S2V-14B Production Service Guide & Template Architecture

> **Hermes Neural Video Architecture**  
> *Sovereign Production Standard for Audio-Driven Speech-to-Video (S2V) on Modal Serverless (NVIDIA A100-80GB) & Local ThinkPad P15*

---

## 1. Executive Summary & Production Overview

The **Wan2.2-S2V-14B** service provides autonomous, enterprise-grade Speech-to-Video generation for the **Hermes Agent Content Factory** (ZENPHAM, Biết Địa Lý Từ Ba Tôi, Tôi Đọc Sách, Reality Decode). It converts a single static portrait/avatar image and high-fidelity spoken voiceover (synthesized via the gold-standard **TTS V0-Sense**) into cinematic talking video with phoneme lip synchronization, natural facial micro-expressions, head gestures, and zero-jolt transitions.

```
                    ┌──────────────────────────────────────────────┐
                    │  TTS V0-Sense (CUDA Local VieNeu-TTS Turbo)  │
                    │  48kHz Stereo, -14.5 LUFS, Clause <= 75 char │
                    └──────────────────────┬───────────────────────┘
                                           │ .wav
                                           ▼
┌─────────────────────────┐       ┌────────────────────────────────┐
│ Anchor Character Image  │──────▶│   Wan2.2-S2V-14B Modal Engine  │
│ 16:9 / 9:16 Neo-Noir   │       │   (NVIDIA A100-80GB HBM2e)     │
└─────────────────────────┘       └────────────────┬───────────────┘
                                                   │
                         ┌─────────────────────────┴─────────────────────────┐
                         ▼                                                   ▼
         ┌───────────────────────────────┐                   ┌───────────────────────────────┐
         │       High-Level REST API     │                   │     ComfyUI Serverless API    │
         │  FastAPI / OpenAPI 3.1        │                   │  Custom JSON Workflow Graph   │
         │  Preset Template Dispatcher   │                   │  Flow Matching + VAE Tile     │
         └───────────────┬───────────────┘                   └───────────────┬───────────────┘
                         │                                                   │
                         └─────────────────────────┬─────────────────────────┘
                                                   ▼
                                  ┌─────────────────────────────────┐
                                  │ Final 1080p Muxed Cinema Video  │
                                  │ Masterclass 16:9 / Shorts 9:16  │
                                  └─────────────────────────────────┘
```

---

## 2. Ingested Production Templates & Node Graphs

Four highly-rated, mathematically validated ComfyUI JSON workflows are permanently ingested into `skills/creative/comfyui/workflows/`:

| Template Key | Workflow JSON | Target Form Factor | Base Resolution | Steps / CFG / Shift | Use Case |
|---|---|---|---|---|---|
| `talking_avatar` | [`wan22_s2v_talking_avatar_production.json`](file:///home/zen/hermes-agent/skills/creative/comfyui/workflows/wan22_s2v_talking_avatar_production.json) | 16:9 Landscape | 1024x704 (1080p upscale) | 35 / 5.0 / 3.0 | Longform Masterclass, Systems Explainers |
| `shorts_vertical` | [`wan22_s2v_shorts_vertical_production.json`](file:///home/zen/hermes-agent/skills/creative/comfyui/workflows/wan22_s2v_shorts_vertical_production.json) | 9:16 Vertical | 704x1024 (1080x1920 upscale) | 35 / 5.0 / 3.0 | 50.00s YouTube Shorts Funnel, TikTok |
| `infinite_speech` | [`wan22_s2v_infinite_speech_production.json`](file:///home/zen/hermes-agent/skills/creative/comfyui/workflows/wan22_s2v_infinite_speech_production.json) | 16:9 Multi-Chunk | 1024x704 (Chained) | 35 / 5.0 / 3.0 | Continuous clause lecturing without seam jumps |
| `cinematic_motion` | [`wan22_s2v_cinematic_motion_production.json`](file:///home/zen/hermes-agent/skills/creative/comfyui/workflows/wan22_s2v_cinematic_motion_production.json) | 16:9 Dramatic | 1024x704 (1080p upscale) | 40 / 5.5 / 3.5 | Dramatic cold openers, emotional turning points |

### 2.1. Template 1: Standard 16:9 Talking Avatar
- **File**: `skills/creative/comfyui/workflows/wan22_s2v_talking_avatar_production.json`
- **Topology**:
  * UNET: `wan2.2_s2v_14B_bf16.safetensors`
  * Audio Encoder: `AudioEncoderEncode` extracting phoneme + acoustic feature maps.
  * Flow Shift: `ModelSamplingSD3` with `shift=3.0` (optimal for balanced temporal stability).
  * Sampler: `KSampler` with `uni_pc` sampler, `simple` scheduler, 35 steps, CFG 5.0.
  * Muxing: `SaveVideo` with 25.0 fps and high-fidelity AAC audio sync.

### 2.2. Template 2: 9:16 Vertical Shorts Funnel
- **File**: `skills/creative/comfyui/workflows/wan22_s2v_shorts_vertical_production.json`
- **Safe Zone Engineering**:
  * Viewport: $704 \times 1024$ pixels native latent grid, preserving 9:16 aspect ratio.
  * Mobile UX Guard: Top 15% clear of subject eyes; bottom 25% clear of mouth to prevent overlap with YouTube Shorts overlay controls (Title, Channel Icon, Sound Badge).
  * Subject Eye-Line: Centered vertically at 40% height ($Y \approx +1.5$).
  * Pacing: Designed for 81 frames (3.24s) to 125 frames (5.00s) clips matching the 4-Beat NLP Open Loop structure.

### 2.3. Template 3: Chained Infinite Speech (Multi-Chunk)
- **File**: `skills/creative/comfyui/workflows/wan22_s2v_infinite_speech_production.json`
- **Zero-Seam Latent Chaining**:
  * Chunk 1: Synthesizes initial frame latent via `WanSoundImageToVideo`.
  * Chunk 2: Takes Chunk 1's final latent state as `video_latent` inside `WanSoundImageToVideoExtend`, together with Chunk 2 audio embeddings.
  * Solves character identity shift and abrupt head pose snaps across sentence boundaries.
  * 100% compliant with TTS V0-Sense fine-grained clause guard ($\le 75$ characters).

### 2.4. Template 4: Cinematic Motion & Dramatic Lighting
- **File**: `skills/creative/comfyui/workflows/wan22_s2v_cinematic_motion_production.json`
- **Kinematic & Lighting Dynamics**:
  * Flow Shift: Boosted to `shift=3.5` for heightened physical motion fluidity.
  * Diffusion Steps: 40 steps at CFG 5.5 for high-contrast shadow definition.
  * Motion Prompting: Injects slow camera dolly push-in and subtle emotional transition cues (philosophical contemplation $\to$ enlightened conviction).

---

## 3. Acoustic Integration: TTS V0-Sense Gold Standard

Speech-to-Video quality depends critically on clean, uncorrupted audio input. All audio feeds MUST obey the following acoustic laws:

1. **Native Neural Inference**: 100% generated via Local VieNeu-TTS v3 Turbo on CUDA. Zero artificial speed reduction (`atempo < 1.0` is strictly forbidden).
2. **Clause Guard $\le 75$ Characters**: Every audio chunk must represent an acoustic clause $\le 75$ characters to prevent TTS distortion or slurring.
3. **Smart Silence Gating**: Audio waveform RMS scanned; dead silence $>0.35$s compressed down to $0.20-0.25$s.
4. **Mastering Standard**:
   - Sample Rate: **48,000 Hz Stereo (24-bit)**
   - Integrated Loudness: **$-14.5 \pm 0.5$ LUFS** (EBU R128)
   - Maximum True Peak: **$\le -1.5$ dBTP**

---

## 4. Prompt Engineering Formulas & Negative Constraints

Wan2.2-S2V interprets prompts not as a script transcript, but as **visual kinematics, facial micro-dynamics, and atmospheric lighting instructions**.

### 4.1. The 5-Element Prompt Formula

$$\text{Prompt} = [\text{Subject/Archetype}] + [\text{Emotional Delivery}] + [\text{Facial \& Head Kinematics}] + [\text{Lighting \& Space}] + [\text{Cinematic Tokens}]$$

- **Subject / Archetype**: `"A distinguished Vietnamese tech scholar"`, `"A visionary systems engineer"`
- **Emotional Delivery**: `"speaking with deep intellectual conviction"`, `"calm authoritative cadence"`
- **Facial & Head Kinematics**: `"direct eye contact, gentle thoughtful head nodding, micro-smiles, natural blinks"`
- **Lighting & Space**: `"warm studio key lighting, subtle cyan rim light on obsidian dark background, shallow depth of field"`
- **Cinematic Tokens**: `"35mm anamorphic lens, 8k photorealistic, pristine skin pores, ultra-detailed"`

### 4.2. Invariant Negative Constraints
Always supply the standard negative prompt to suppress temporal artifacts:
```
distorted teeth, unnatural mouth movements, blurry, jittery, low quality, artifacting, cartoon, eye drift, morphing lips, bad hair edges, flickering, plastic skin, static mannequin pose
```

---

## 5. Developer & Vibe Agent Integration

### 5.1. Option A: High-Level FastAPI REST Endpoint

Endpoint: `https://zenonmind--hermes-wan-s2v-api.modal.run/generate` (or local modal runner)

```python
import base64
import requests

# 1. Encode assets
with open("assets/audio/clause_01.wav", "rb") as f:
    audio_b64 = "data:audio/wav;base64," + base64.b64encode(f.read()).decode()

with open("assets/portraits/zen_scholar_16x9.png", "rb") as f:
    img_b64 = "data:image/png;base64," + base64.b64encode(f.read()).decode()

# 2. Dispatch request
payload = {
    "image": img_b64,
    "audio": audio_b64,
    "template": "talking_avatar",  # or 'shorts_vertical', 'infinite_speech', 'cinematic_motion'
    "prompt": "A Vietnamese scholar explaining computational geometry, warm studio rim light",
    "upscale_1080p": True,
}

response = requests.post(
    "https://zenonmind--hermes-wan-s2v-api.modal.run/generate",
    json=payload,
    timeout=600
)

with open("output/masterclass_scene02_s2v.mp4", "wb") as f:
    f.write(response.content)

print("✓ Video generated successfully.")
```

### 5.2. Option B: Low-Level ComfyUI Engine Dispatcher

Endpoint: `https://mojopham--hermes-comfyui-engine-comfyuirunner-web-ui.modal.run`

```bash
# List all available production templates
python3 skills/creative/modal-comfyui/dispatch_template.py --list-templates

# Dispatch vertical shorts template to Modal ComfyUI Engine
python3 skills/creative/modal-comfyui/dispatch_template.py \
    --host https://mojopham--hermes-comfyui-engine-comfyuirunner-web-ui.modal.run \
    --template wan22_s2v_shorts_vertical \
    --prompt "A charismatic tech host explaining neural scaling laws, obsidian background" \
    --image assets/portraits/host_vertical.png \
    --audio assets/audio/shorts_hook.wav \
    --output output/shorts_hook_s2v.mp4
```

### 5.3. Option C: Modal Direct Local CLI
```bash
modal run skills/creative/modal-wan-s2v/modal_app.py \
    --image assets/portraits/zen_scholar_16x9.png \
    --audio assets/audio/speech_masterclass.wav \
    --prompt "A distinguished scholar speaking with conviction, 8k" \
    --output output/wan_s2v_direct.mp4
```

---

## 6. Fleet Governance & Resource Management

1. **Hardware Tier**: NVIDIA A100-80GB (80GB HBM2e VRAM).
2. **Cold-Start Optimization**: Persistent Modal Volume `hermes-wan-s2v-cache` mounted at `/cache` holding pre-cached 30GB model weights. Container warm scaledown window set to 300s.
3. **Probe Quota Ceiling**: As mandated by sovereign fleet invariants, all automated monitoring agents MUST adhere to $\le 5$ health/usage calls per day with randomized intervals ($150-300$s) to prevent API rate-limiting or accidental cloud bill spikes.
4. **Local Prototyping Fallback**: For offline development on ThinkPad P15 (Quadro RTX 5000 16GB), generate preview clips using low-step quantization or route to Modal A100-80GB for production mastering.

---

## 7. Verification & Quality Gates

Before publishing or muxing into Longform Masterclass episodes or 50.00s Shorts:
- [ ] **Lip-Sync Check**: Spoken vowels (/a/, /o/, /u/) must exhibit clear mouth aperture matching audio amplitude peaks.
- [ ] **Artifact Gate**: Zero morphing teeth, eye rolling, or jaw tearing across transitions.
- [ ] **Audio Master Alignment**: Audio track must match original EBU R128 mastered $-14.5 \pm 0.5$ LUFS.
- [ ] **Frame Resolution**: Minimum 1080p Full HD (1920x1080 for 16:9, 1080x1920 for 9:16) verified via `ffprobe`.
