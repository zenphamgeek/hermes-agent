"""
skills/creative/modal-wan-s2v/modal_app.py
===========================================
Hermes Agent - Modal Serverless Engine for Wan2.2-S2V-14B (Speech-to-Video).

Target Application: hermes-wan-s2v
Target Workspace: mvlm (or mojopham / motion / vrag)
Hardware Tier: NVIDIA A100-80GB
Architecture:
- Alibaba Wan2.2-S2V-14B (Speech-to-Video Foundation Model)
- Audio-Driven Cinematic Facial Motion & Phoneme Lip-Syncing
- Direct Audio Conditioning (TTS V0-Sense 48kHz WAV / MP3) + Portrait/Face Anchor
- Automatic Audio Muxing & Optional 1080p Super-Resolution Upscaling
- Endpoints: FastAPI Self-Describing (OpenAPI 3.1) + RPC + Local CLI
"""

import base64
import io
import os
import sys
import shutil
import subprocess
import tempfile
import time
import json
import re
import uuid
import asyncio
import urllib.request
from pathlib import Path
from typing import Optional, Dict, Any

import modal
from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel, Field

APP_NAME = "hermes-wan-s2v"
MODEL_REPO = "Wan-AI/Wan2.2-S2V-14B"
CACHE_DIR = "/cache"
MODEL_DIR = f"{CACHE_DIR}/Wan2.2-S2V-14B"

app = modal.App(APP_NAME)

# Persistent Model Cache Volume to store 30GB weights across cold starts
cache_volume = modal.Volume.from_name("hermes-wan-s2v-cache", create_if_missing=True)
job_store = modal.Dict.from_name("hermes-wan-jobs", create_if_missing=True)

# Container environment definition
wan_image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install(
        "ffmpeg",
        "git",
        "libsndfile1",
        "libgl1-mesa-glx",
        "libglib2.0-0",
        "curl",
        "wget",
    )
    .pip_install(
        "torch>=2.4.0",
        "torchvision",
        "torchaudio",
        "transformers>=4.49.0,<=4.51.3",
        "diffusers>=0.31.0",
        "tokenizers>=0.20.3",
        "accelerate>=1.2.0",
        "sentencepiece",
        "einops",
        "safetensors",
        "librosa",
        "soundfile",
        "imageio[ffmpeg]",
        "imageio",
        "imageio-ffmpeg",
        "pillow",
        "opencv-python-headless",
        "fastapi[standard]",
        "pydantic",
        "huggingface-hub[cli]",
        "easydict",
        "ftfy",
        "dashscope",
        "tqdm",
        "decord",
        "peft",
    )
    .run_commands(
        "pip install torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cu124",
        "pip install https://github.com/Dao-AILab/flash-attention/releases/download/v2.7.4.post1/flash_attn-2.7.4.post1+cu12torch2.5cxx11abiFALSE-cp311-cp311-linux_x86_64.whl",
        "rm -rf /opt/Wan2.2 && git clone https://github.com/Wan-Video/Wan2.2.git /opt/Wan2.2",
    )
    .env({
        "HF_HOME": f"{CACHE_DIR}/huggingface",
        "PYTHONPATH": "/opt/Wan2.2:$PYTHONPATH",
        "TORCH_CUDA_ARCH_LIST": "8.0;9.0",
    })
)


@app.cls(
    image=wan_image,
    gpu="A100-80GB",          # NVIDIA A100 80GB VRAM for 14B S2V weights + temporal activations
    timeout=7200,             # 120-minute timeout buffer for multi-clip 14B DiT inference
    scaledown_window=300,     # Keep warm for 5 minutes between requests
    volumes={CACHE_DIR: cache_volume},
)
class WanS2VEngine:
    @modal.enter()
    def initialize_engine(self):
        """Pre-checks weights and verifies GPU environment on A100-80GB."""
        import torch
        import flash_attn
        device_name = torch.cuda.get_device_name(0) if torch.cuda.is_available() else "Unknown"
        total_vram = torch.cuda.get_device_properties(0).total_memory / (1024**3) if torch.cuda.is_available() else 0.0
        print(f"[Wan2.2-S2V] Initializing on GPU: {device_name}")
        print(f"[Wan2.2-S2V] Total VRAM Available: {total_vram:.2f} GB")
        print(f"[Wan2.2-S2V] Native Flash-Attention Active: v{flash_attn.__version__}")

        os.makedirs(CACHE_DIR, exist_ok=True)
        os.makedirs(MODEL_DIR, exist_ok=True)

        # Check if model checkpoint exists in Volume
        safetensor_files = list(Path(MODEL_DIR).glob("*.safetensors")) + list(Path(MODEL_DIR).glob("**/*.safetensors"))
        bin_files = list(Path(MODEL_DIR).glob("*.bin")) + list(Path(MODEL_DIR).glob("**/*.bin"))

        if not (safetensor_files or bin_files):
            print(f"[Wan2.2-S2V] Weights not found in {MODEL_DIR}. Downloading from HuggingFace ({MODEL_REPO})...")
            from huggingface_hub import snapshot_download
            snapshot_download(MODEL_REPO, local_dir=MODEL_DIR, local_dir_use_symlinks=False)
            cache_volume.commit()
            print("[Wan2.2-S2V] Checkpoint successfully downloaded and committed to volume.")
        else:
            print(f"[Wan2.2-S2V] Found existing model weights at {MODEL_DIR}.")

    @modal.method()
    def generate_s2v(
        self,
        image: str,
        audio: str,
        prompt: str = "A person speaking naturally, cinematic lighting, photorealistic, 8k",
        negative_prompt: str = "worst quality, blurry, distorted, jitter, low quality, artifact, watermarking, jittery lip motion, deformed face",
        size: str = "1024*704",
        sample_steps: int = 30,
        guide_scale: float = 5.0,
        seed: Optional[int] = None,
        upscale_1080p: bool = True,
        num_clip: Optional[int] = 1,
        job_id: Optional[str] = None,
        webhook_url: Optional[str] = None,
    ) -> bytes:
        """
        Executes Speech-to-Video generation using Wan2.2-S2V-14B on A100-80GB.
        Returns final MP4 video with synced audio, and reports real-time events to job_store.
        """
        import torch
        from PIL import Image

        t0 = time.time()
        work_dir = tempfile.mkdtemp(prefix="wan_s2v_")
        img_path = os.path.join(work_dir, "input_portrait.png")
        audio_path = os.path.join(work_dir, "input_speech.wav")
        raw_video_path = os.path.join(work_dir, "raw_output.mp4")
        final_video_path = os.path.join(work_dir, "final_s2v_1080p.mp4")

        if job_id:
            job_store[job_id] = {
                "job_id": job_id,
                "status": "initializing",
                "progress": 0.0,
                "step": 0,
                "total_steps": sample_steps,
                "message": "Initializing weights & audio conditioning on A100 GPU",
                "started_at": t0,
                "updated_at": t0,
            }

        try:
            # 1. Decode Image Input
            if image.startswith("http://") or image.startswith("https://"):
                req = urllib.request.Request(image, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=30) as resp:
                    pil_img = Image.open(io.BytesIO(resp.read())).convert("RGB")
            else:
                b64_str = image.split("base64,")[1] if "base64," in image else image
                pil_img = Image.open(io.BytesIO(base64.b64decode(b64_str))).convert("RGB")
            pil_img.save(img_path)

            # 2. Decode Audio Input
            if audio.startswith("http://") or audio.startswith("https://"):
                req = urllib.request.Request(audio, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=30) as resp:
                    audio_bytes = resp.read()
            else:
                b64_str = audio.split("base64,")[1] if "base64," in audio else audio
                audio_bytes = base64.b64decode(b64_str)

            with open(audio_path, "wb") as f:
                f.write(audio_bytes)

            # Convert audio to standard 16kHz/48kHz WAV via ffmpeg if necessary
            clean_audio_path = os.path.join(work_dir, "clean_speech.wav")
            subprocess.run([
                "ffmpeg", "-y", "-i", audio_path,
                "-ar", "16000", "-ac", "1", clean_audio_path
            ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            print(f"[Wan2.2-S2V] Starting S2V synthesis with prompt: '{prompt[:60]}...'")

            # 3. Invoke Wan2.2 S2V Inference
            cli_cmd = [
                sys.executable, "/opt/Wan2.2/generate.py",
                "--task", "s2v-14B",
                "--size", size,
                "--ckpt_dir", MODEL_DIR,
                "--prompt", prompt,
                "--image", img_path,
                "--audio", clean_audio_path,
                "--sample_steps", str(sample_steps),
                "--sample_guide_scale", str(guide_scale),
                "--offload_model", "False",
                "--save_file", raw_video_path,
            ]
            if seed is not None and seed >= 0:
                cli_cmd.extend(["--base_seed", str(seed)])
            if num_clip is not None and num_clip > 0:
                cli_cmd.extend(["--num_clip", str(num_clip)])

            print(f"[Wan2.2-S2V] Running command: {' '.join(cli_cmd)}")
            env_vars = os.environ.copy()
            env_vars["PYTHONPATH"] = f"/opt/Wan2.2:/usr/local/lib/python3.11/site-packages:{env_vars.get('PYTHONPATH', '')}"
            process = subprocess.Popen(
                cli_cmd,
                cwd="/opt/Wan2.2",
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                env=env_vars,
                bufsize=1,
            )

            full_logs = []
            for line in process.stdout:
                line_str = line.strip()
                if line_str:
                    full_logs.append(line_str)
                    if any(k in line_str.lower() for k in ["step", "%", "loading", "saving", "iter", "frame", "creating"]):
                        print(f"[Wan2.2-S2V] {line_str}")

                    if job_id:
                        m = re.search(r"(\d+)/(\d+)\s+\[([^<]+)<([^,]+),\s*([^\]]+)\]", line_str)
                        if m:
                            cur_s = int(m.group(1))
                            tot_s = int(m.group(2))
                            pct = round((cur_s / tot_s) * 100, 1)
                            job_store[job_id] = {
                                "job_id": job_id,
                                "status": "running",
                                "progress": pct,
                                "step": cur_s,
                                "total_steps": tot_s,
                                "elapsed": m.group(3).strip(),
                                "remaining": m.group(4).strip(),
                                "speed": m.group(5).strip(),
                                "message": f"Diffusion sampling step {cur_s}/{tot_s} ({pct}%)",
                                "updated_at": time.time(),
                            }

            process.wait()

            if process.returncode != 0:
                recent_logs = "\n".join(full_logs[-30:])
                print(f"[Wan2.2-S2V] STDERR / Recent logs:\n{recent_logs}")
                raise RuntimeError(f"Wan2.2-S2V inference failed with code {process.returncode}:\n{recent_logs[-800:]}")

            # Locate the generated video output
            if not os.path.exists(raw_video_path):
                # Search for output file in work_dir or /opt/Wan2.2
                mp4_candidates = list(Path(work_dir).glob("*.mp4")) + list(Path("/opt/Wan2.2").glob("*.mp4"))
                if mp4_candidates:
                    raw_video_path = str(sorted(mp4_candidates, key=os.path.getmtime)[-1])
                else:
                    raise FileNotFoundError(f"No output MP4 generated. Recent logs:\n" + "\n".join(full_logs[-15:]))

            print(f"[Wan2.2-S2V] Raw video generated at: {raw_video_path}")

            # 4. Mux Original High-Fidelity Audio + Optional 1080p Upscale
            vf_filters = []
            if upscale_1080p:
                parts = size.split("*")
                if len(parts) == 2 and int(parts[0]) < int(parts[1]):
                    # Portrait (e.g. 704*1024 or 704*1280 or 720*1280) -> 1080x1920
                    vf_filters.append("scale=1080:1920:flags=lanczos,unsharp=5:5:0.8:5:5:0.0")
                else:
                    # Landscape (e.g. 1024*704 or 1280*720) -> 1920x1080
                    vf_filters.append("scale=1920:1080:flags=lanczos,unsharp=5:5:0.8:5:5:0.0")

            vf_arg = ["-vf", ",".join(vf_filters)] if vf_filters else []

            mux_cmd = [
                "ffmpeg", "-y",
                "-i", raw_video_path,
                "-i", audio_path,
                *vf_arg,
                "-c:v", "libx264",
                "-preset", "medium",
                "-crf", "18",
                "-pix_fmt", "yuv420p",
                "-c:a", "aac",
                "-b:a", "192k",
                "-shortest",
                final_video_path
            ]
            subprocess.run(mux_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            with open(final_video_path, "rb") as f:
                output_bytes = f.read()

            try:
                os.makedirs(f"{CACHE_DIR}/jobs", exist_ok=True)
                job_video_path = f"{CACHE_DIR}/jobs/{job_id}.mp4" if job_id else f"{CACHE_DIR}/latest_s2v_video.mp4"
                shutil.copy2(final_video_path, job_video_path)
                shutil.copy2(final_video_path, f"{CACHE_DIR}/latest_s2v_video.mp4")
                cache_volume.commit()
                print(f"[Wan2.2-S2V] Volume snapshot committed to: {job_video_path}")
            except Exception as e:
                print(f"[Wan2.2-S2V] Warning: Volume commit failed: {e}")

            dt = time.time() - t0
            print(f"[✓ Wan2.2-S2V] Complete. Output size: {len(output_bytes)/(1024*1024):.2f} MB in {dt:.1f}s.")

            if job_id:
                job_store[job_id] = {
                    "job_id": job_id,
                    "status": "completed",
                    "progress": 100.0,
                    "step": sample_steps,
                    "total_steps": sample_steps,
                    "file_size_mb": round(len(output_bytes) / (1024 * 1024), 2),
                    "duration_seconds": round(dt, 1),
                    "download_url": f"/v1/jobs/{job_id}/download",
                    "message": "Video generation successfully completed",
                    "updated_at": time.time(),
                }
                if webhook_url:
                    try:
                        hook_data = json.dumps(dict(job_store[job_id])).encode("utf-8")
                        hook_req = urllib.request.Request(webhook_url, data=hook_data, headers={"Content-Type": "application/json"})
                        urllib.request.urlopen(hook_req, timeout=10)
                        print(f"[Wan2.2-S2V] Webhook notification sent to: {webhook_url}")
                    except Exception as e:
                        print(f"[Wan2.2-S2V] Warning: Webhook dispatch error: {e}")

            return output_bytes

        except Exception as e:
            if job_id:
                job_store[job_id] = {
                    "job_id": job_id,
                    "status": "failed",
                    "error": str(e),
                    "message": f"Inference failed: {str(e)[:200]}",
                    "updated_at": time.time(),
                }
            raise
        finally:
            shutil.rmtree(work_dir, ignore_errors=True)


# Production Template Presets
TEMPLATE_PRESETS = {
    "talking_avatar": {
        "title": "Wan2.2-S2V-14B Production: Standard 16:9 Talking Avatar",
        "size": "1024*704",
        "sample_steps": 35,
        "guide_scale": 5.0,
        "prompt_suffix": "gentle nodding, intellectual gaze, warm studio key lighting, 8k resolution, cinematic photorealism",
        "aspect_ratio": "16:9",
        "workflow_template": "wan22_s2v_talking_avatar_production.json"
    },
    "shorts_vertical": {
        "title": "Wan2.2-S2V-14B Production: 9:16 Vertical Shorts Funnel",
        "size": "704*1024",
        "sample_steps": 35,
        "guide_scale": 5.0,
        "prompt_suffix": "direct engaging eye contact, energetic subtle head nodding, micro-smiles, studio lighting with obsidian-cyan rim light, vertical 9:16 format",
        "aspect_ratio": "9:16",
        "workflow_template": "wan22_s2v_shorts_vertical_production.json"
    },
    "infinite_speech": {
        "title": "Wan2.2-S2V-14B Production: Chained Infinite Speech",
        "size": "1024*704",
        "sample_steps": 35,
        "guide_scale": 5.0,
        "prompt_suffix": "continuous lecturing, natural fluid head kinematics, calm eye contact, warm ambient studio lighting, neo-noir dark background",
        "aspect_ratio": "16:9",
        "workflow_template": "wan22_s2v_infinite_speech_production.json"
    },
    "cinematic_motion": {
        "title": "Wan2.2-S2V-14B Production: Cinematic Motion & Dramatic Lighting",
        "size": "1024*704",
        "sample_steps": 40,
        "guide_scale": 5.5,
        "prompt_suffix": "cinematic slow camera dolly push-in, intense intellectual conviction, expressive eye movements, deep atmospheric lighting, 35mm anamorphic, 8k masterclass",
        "aspect_ratio": "16:9",
        "workflow_template": "wan22_s2v_cinematic_motion_production.json"
    },
}


# -----------------------------------------------------------------------------
# REST API Definition (FastAPI + OpenAPI 3.1)
# -----------------------------------------------------------------------------
class WanS2VGenerateRequest(BaseModel):
    image: str = Field(
        ...,
        description="Reference portrait/character image as a public HTTP(S) URL or Base64 data string."
    )
    audio: str = Field(
        ...,
        description="Speech audio (.wav, .mp3, e.g. from TTS V0-Sense) as a public HTTP(S) URL or Base64 data string."
    )
    template: Optional[str] = Field(
        "talking_avatar",
        description="Production preset template: 'talking_avatar' (16:9), 'shorts_vertical' (9:16), 'infinite_speech', 'cinematic_motion'."
    )
    prompt: Optional[str] = Field(
        "A person speaking naturally, cinematic lighting, photorealistic, 8k",
        description="Guiding text prompt for facial expressions and visual atmosphere."
    )
    negative_prompt: Optional[str] = Field(
        "worst quality, blurry, distorted, jitter, low quality, artifact, watermarking, jittery lip motion",
        description="Negative prompt to suppress visual deformities."
    )
    size: Optional[str] = Field(
        None,
        description="Base generation grid size. If omitted, adopts preset default ('1024*704' for landscape, '704*1024' for vertical Shorts)."
    )
    sample_steps: Optional[int] = Field(
        None,
        description="Sampling diffusion steps. Standard: 30-40."
    )
    guide_scale: Optional[float] = Field(
        None,
        description="CFG Guidance scale."
    )
    seed: Optional[int] = Field(
        None,
        description="Random seed for reproducible lip kinematics."
    )
    upscale_1080p: Optional[bool] = Field(
        True,
        description="Auto-upscale base video to 1080p Full HD via high-fidelity neural Lanczos filtering."
    )
    webhook_url: Optional[str] = Field(
        None,
        description="Optional webhook URL to receive HTTP POST callback with completed video metadata."
    )
    num_clip: Optional[int] = Field(
        1,
        description="Number of 5-second video clips to generate. Default 1 (5.0s, ~25m). Set 2 for 10s (~50m)."
    )


web_app = FastAPI(
    title="Hermes Neural Wan2.2 Speech-to-Video (S2V) API",
    description="Autonomous Serverless Wan2.2-S2V-14B Cinema Engine on NVIDIA A100-80GB",
    version="2.2.0",
)


@web_app.get("/templates")
def list_available_templates():
    """Returns all available production templates with their recommended aspect ratios, parameters, and ComfyUI workflow files."""
    return {
        "status": "success",
        "service": "Hermes Wan2.2-S2V Production Templates",
        "count": len(TEMPLATE_PRESETS),
        "templates": TEMPLATE_PRESETS
    }


@web_app.get("/")
def api_specification():
    """
    Self-describing endpoint for Vibe Agents.
    Returns complete parameter schema, prompt guide, production templates, and sample pipelines.
    """
    return {
        "status": "online",
        "service": "Hermes Neural Wan2.2 Speech-to-Video 14B (S2V)",
        "hardware": "NVIDIA A100-80GB (80GB HBM2e VRAM)",
        "description": (
            "Autonomous serverless engine that transforms a static portrait image and an audio voiceover "
            "(e.g., from Hermes TTS V0-Sense) into a high-fidelity cinematic video with synchronized phoneme "
            "lip movements, micro-expressions, eye contact, and head gestures. Automatically muxes audio and "
            "upscales to pristine 1080p Full HD."
        ),
        "capabilities": [
            "Speech-to-Video phoneme lip-syncing driven directly by voiceover audio (.wav / .mp3)",
            "Natural facial micro-expressions (eye blinking, head gestures, emotional cadence)",
            "Automatic original audio muxing into final MP4",
            "Automated 1080p Full HD upscaling pipeline via high-precision Lanczos filtering",
            "Production template presets: talking_avatar, shorts_vertical, infinite_speech, cinematic_motion",
            "Full compatibility with Hermes Agent TTS V0-Sense audio"
        ],
        "production_templates": TEMPLATE_PRESETS,
        "prompt_guide": {
            "prompt_structure": "[Subject/Character] + [Emotional Tone/Cadence] + [Facial & Head Kinematics] + [Lighting & Background] + [Cinematic Quality]",
            "best_practices": [
                "Always describe subtle head motions ('gentle nodding', 'calm facial gestures') to prevent stiffness.",
                "Mention lighting and camera focus ('studio key lighting', 'shallow depth of field', '8k photorealistic').",
                "Do NOT include raw audio transcript in prompt; the audio waveform drives the mouth kinematics directly.",
                "For vertical Shorts (9:16), set template='shorts_vertical'. For landscape Masterclass (16:9), set template='talking_avatar'."
            ],
            "archetype_templates": {
                "academic_scholar": "A distinguished Vietnamese scholar passionately explaining complex concepts, intellectual gaze, gentle nodding, warm studio key lighting, 8k resolution, cinematic photorealism",
                "tech_news_anchor": "Confident female tech news anchor looking directly into camera, crisp speech articulation, subtle eyebrow movement, modern broadcast studio, 4k ultra-detailed",
                "philosophical_storyteller": "Wise elder storytelling by the fireplace, expressive weathered face, gentle emotional cadence, soft ambient candlelight, hyperrealistic depth of field"
            },
            "recommended_negative_prompt": "worst quality, blurry, distorted mouth, jittery lips, morphing teeth, eye drift, bad anatomy, frame flicker, low resolution, artifact"
        },
        "sample_pipeline": {
            "python": (
                "import requests, base64\n\n"
                "# 1. Read input audio and portrait image\n"
                "with open('speech.wav', 'rb') as f:\n"
                "    audio_b64 = 'data:audio/wav;base64,' + base64.b64encode(f.read()).decode()\n"
                "with open('avatar.png', 'rb') as f:\n"
                "    image_b64 = 'data:image/png;base64,' + base64.b64encode(f.read()).decode()\n\n"
                "# 2. Post request to Modal Wan2.2-S2V Endpoint\n"
                "payload = {\n"
                "    'image': image_b64,\n"
                "    'audio': audio_b64,\n"
                "    'template': 'shorts_vertical',  # or 'talking_avatar'\n"
                "    'prompt': 'A scholar speaking passionately, cinematic lighting, 8k',\n"
                "    'upscale_1080p': True\n"
                "}\n"
                "res = requests.post('<API_URL>/generate', json=payload)\n"
                "with open('output_1080p_s2v.mp4', 'wb') as f:\n"
                "    f.write(res.content)\n"
            ),
            "curl": (
                "curl -X POST <API_URL>/generate \\\n"
                "  -H 'Content-Type: application/json' \\\n"
                "  -d '{\"image\": \"https://example.com/portrait.png\", \"audio\": \"https://example.com/voice.wav\", \"template\": \"talking_avatar\", \"upscale_1080p\": true}' \\\n"
                "  --output output_1080p.mp4"
            )
        },
        "endpoints": {
            "POST /": "Generate video directly on root URL",
            "POST /generate": "Generate S2V video endpoint",
            "GET /templates": "List all production templates with ComfyUI workflow schemas",
            "GET /docs": "Interactive Swagger UI documentation",
            "GET /openapi.json": "Standard OpenAPI 3.1 machine-readable specification"
        },
        "parameter_schema": WanS2VGenerateRequest.model_json_schema()
    }


@web_app.post("/")
@web_app.post("/generate")
def handle_generate(req: WanS2VGenerateRequest):
    # Resolve preset defaults
    preset = TEMPLATE_PRESETS.get(req.template, TEMPLATE_PRESETS["talking_avatar"])
    size = req.size or preset["size"]
    sample_steps = req.sample_steps or preset["sample_steps"]
    guide_scale = req.guide_scale or preset["guide_scale"]
    
    # Prompt enhancement with template suffix if not present
    prompt = req.prompt or "A person speaking naturally, cinematic lighting, photorealistic, 8k"
    if preset.get("prompt_suffix") and preset["prompt_suffix"] not in prompt:
        prompt = f"{prompt}, {preset['prompt_suffix']}"

    engine = WanS2VEngine()
    video_bytes = engine.generate_s2v.remote(
        image=req.image,
        audio=req.audio,
        prompt=prompt,
        negative_prompt=req.negative_prompt,
        size=size,
        sample_steps=sample_steps,
        guide_scale=guide_scale,
        seed=req.seed,
        upscale_1080p=req.upscale_1080p,
        num_clip=req.num_clip,
    )
    return Response(content=video_bytes, media_type="video/mp4")


@web_app.post("/v1/jobs/generate", status_code=202)
@web_app.post("/generate_async", status_code=202)
def handle_generate_async(req: WanS2VGenerateRequest):
    """
    Submits Wan2.2-S2V-14B video generation asynchronously.
    Returns immediately with job_id, SSE events URL, and status URL.
    Does NOT block or time out.
    """
    job_id = f"wan_s2v_{uuid.uuid4().hex[:10]}"
    preset = TEMPLATE_PRESETS.get(req.template, TEMPLATE_PRESETS["talking_avatar"])
    size = req.size or preset["size"]
    sample_steps = req.sample_steps or preset["sample_steps"]
    guide_scale = req.guide_scale or preset["guide_scale"]
    
    prompt = req.prompt or "A person speaking naturally, cinematic lighting, photorealistic, 8k"
    if preset.get("prompt_suffix") and preset["prompt_suffix"] not in prompt:
        prompt = f"{prompt}, {preset['prompt_suffix']}"

    # Initialize job in Dict
    t_now = time.time()
    job_store[job_id] = {
        "job_id": job_id,
        "status": "queued",
        "progress": 0.0,
        "step": 0,
        "total_steps": sample_steps,
        "template": req.template,
        "size": size,
        "message": "Job queued for GPU worker dispatch",
        "created_at": t_now,
        "updated_at": t_now,
    }

    # Spawn task on A100 GPU worker in the cloud (detached execution)
    engine = WanS2VEngine()
    engine.generate_s2v.spawn(
        image=req.image,
        audio=req.audio,
        prompt=prompt,
        negative_prompt=req.negative_prompt,
        size=size,
        sample_steps=sample_steps,
        guide_scale=guide_scale,
        seed=req.seed,
        upscale_1080p=req.upscale_1080p,
        num_clip=req.num_clip,
        job_id=job_id,
        webhook_url=req.webhook_url,
    )

    return {
        "job_id": job_id,
        "status": "queued",
        "status_url": f"/v1/jobs/{job_id}",
        "events_url": f"/v1/jobs/{job_id}/events",
        "download_url": f"/v1/jobs/{job_id}/download",
    }


@web_app.get("/v1/jobs/{job_id}")
def get_job_status(job_id: str):
    """Returns current execution status, progress, step count, and download URL."""
    if job_id not in job_store:
        raise HTTPException(status_code=404, detail="Job not found")
    data = dict(job_store[job_id])
    if data.get("status") == "completed":
        data["download_url"] = f"/v1/jobs/{job_id}/download"
    return data


@web_app.get("/v1/jobs/{job_id}/events")
async def stream_job_events(job_id: str):
    """
    Streams real-time Server-Sent Events (SSE) directly from the GPU worker.
    Client receives live step updates (e.g. step 1..30, speed, ETA) and completion events.
    """
    async def event_generator():
        last_step = -1
        last_status = None
        while True:
            if job_id not in job_store:
                yield f"event: error\ndata: {json.dumps({'error': 'Job not found'})}\n\n"
                break
            info = dict(job_store[job_id])
            cur_step = info.get("step", -1)
            status = info.get("status")
            if cur_step != last_step or status != last_status:
                last_step = cur_step
                last_status = status
                yield f"event: {status}\ndata: {json.dumps(info)}\n\n"
            if status in ["completed", "failed"]:
                break
            await asyncio.sleep(1.0)
    return StreamingResponse(event_generator(), media_type="text/event-stream")


@web_app.get("/v1/jobs/{job_id}/download")
def download_job_video(job_id: str):
    """Streams the finished MP4 video file from the persistent cache volume."""
    if job_id not in job_store:
        raise HTTPException(status_code=404, detail="Job not found")
    info = dict(job_store[job_id])
    if info.get("status") != "completed":
        raise HTTPException(status_code=400, detail=f"Job not ready (status: {info.get('status')})")
    
    cache_volume.reload()
    job_video_path = f"{CACHE_DIR}/jobs/{job_id}.mp4"
    if not os.path.exists(job_video_path):
        job_video_path = f"{CACHE_DIR}/latest_s2v_video.mp4"
    if not os.path.exists(job_video_path):
        raise HTTPException(status_code=404, detail="Video file not found on volume")

    return FileResponse(
        job_video_path,
        media_type="video/mp4",
        filename=f"{job_id}.mp4"
    )


@web_app.get("/v1/jobs")
def list_jobs():
    """Lists recent jobs in the job store."""
    jobs_summary = []
    for jid in list(job_store.keys())[-30:]:
        jobs_summary.append(dict(job_store[jid]))
    return {"total": len(jobs_summary), "jobs": jobs_summary}


@app.function(image=wan_image, timeout=7200, volumes={CACHE_DIR: cache_volume})
@modal.asgi_app()
def api():
    """Mounts the full FastAPI app for OpenAPI docs and REST generation."""
    return web_app


# -----------------------------------------------------------------------------
# Local CLI Entrypoint (Run via `modal run modal_app.py`)
# -----------------------------------------------------------------------------
@app.local_entrypoint()
def main(
    image: str,
    audio: str,
    prompt: str = (
        "A graceful Vietnamese young woman wearing an elegant white silk Ao Dai, "
        "speaking warmly and passionately about Vietnamese culture and heritage, "
        "gentle subtle head nodding, micro-smiles, authentic eye contact, "
        "warm cinematic key lighting, shallow depth of field, 8k ultra photorealistic"
    ),
    negative_prompt: str = (
        "worst quality, blurry, distorted mouth, jittery lips, morphing teeth, "
        "eye drift, bad anatomy, frame flicker, low resolution, artifact"
    ),
    size: str = "704*1024",
    sample_steps: int = 30,
    guide_scale: float = 5.0,
    seed: int = 42,
    output: str = "output/wan22_s2v_aodai_vietnam_master.mp4",
    upscale_1080p: bool = True,
):
    """Run S2V generation directly from workstation terminal via Modal persistent gRPC channel."""
    import base64
    print("===================================================================")
    print(" 🎬 HERMES NEURAL WAN2.2-S2V-14B (A100-80GB CLOUD RPC INFERENCE)")
    print("===================================================================")
    print(f" Image   : {image}")
    print(f" Audio   : {audio}")
    print(f" Size    : {size} -> (1080x1920 Lanczos)")
    print(f" Steps   : {sample_steps} | CFG: {guide_scale} | Seed: {seed}")
    print(f" Output  : {output}")
    print("-------------------------------------------------------------------")

    # Read image
    if os.path.exists(image):
        with open(image, "rb") as f:
            img_payload = "data:image/png;base64," + base64.b64encode(f.read()).decode("utf-8")
    else:
        img_payload = image

    # Read audio
    if os.path.exists(audio):
        with open(audio, "rb") as f:
            audio_payload = "data:audio/wav;base64," + base64.b64encode(f.read()).decode("utf-8")
    else:
        audio_payload = audio

    engine = WanS2VEngine()
    video_bytes = engine.generate_s2v.remote(
        image=img_payload,
        audio=audio_payload,
        prompt=prompt,
        negative_prompt=negative_prompt,
        size=size,
        sample_steps=sample_steps,
        guide_scale=guide_scale,
        seed=seed,
        upscale_1080p=upscale_1080p,
    )

    out_file = Path(output)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_bytes(video_bytes)
    print(f"\n[✓] Successfully saved {len(video_bytes) / (1024*1024):.2f} MB S2V video to: {out_file.resolve()}\n")
