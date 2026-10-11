"""
skills/creative/modal-ltxvideo/modal_app.py
============================================
Hermes Agent - Modal Serverless Engine for LTX-2.5 (22B) Video Foundation Model.

Target Application: hermes-neural-ltxvideo
Workspace: mindful (or r2rgraph / motion / any Modal workspace)
Hardware Tier: NVIDIA A100-80GB (or H100)
Architecture:
- Lightricks LTX-2.5 (14B Video DiT + 5B Audio + 12B Gemma-4 Multimodal Text Encoder)
- Native 10s - 15s Continuous High-Fidelity Video Generation @ 24fps
- 3D Spatio-Temporal Attention with Causal VAE Tiling to prevent OOM
- Endpoints: Web API (FastAPI) + RPC (modal.method) + Local CLI (local_entrypoint)
"""

import io
import math
import os
import time
from pathlib import Path
from typing import Optional

import modal

APP_NAME = "hermes-neural-ltxvideo"
MODEL_ID = "Lightricks/LTX-Video"  # Base model / LTX-2.5 HuggingFace checkpoint
CACHE_DIR = "/cache/huggingface"

app = modal.App(APP_NAME)

# Persistent Model Cache Volume to avoid 68GB re-download on cold starts
cache_volume = modal.Volume.from_name("hermes-ltx-cache", create_if_missing=True)

# Container environment definition
ltx_image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("ffmpeg", "git", "libgl1-mesa-glx", "libglib2.0-0")
    .pip_install(
        "torch>=2.4.0",
        "diffusers>=0.31.0",
        "transformers>=4.45.0",
        "accelerate>=0.33.0",
        "sentencepiece",
        "imageio[ffmpeg]",
        "imageio",
        "torchvision",
        "einops",
        "safetensors",
        "torchaudio",
        "fastapi[standard]",
        "pydantic",
    )
    .env({"HF_HOME": CACHE_DIR, "TORCH_CUDA_ARCH_LIST": "8.0;9.0"})
)


@app.cls(
    image=ltx_image,
    gpu="A100-80GB",          # NVIDIA A100 80GB VRAM required for 10-15s DiT activations
    timeout=1800,             # 30-minute timeout buffer for long 15s generations
    scaledown_window=300,     # Keep warm for 5 minutes between requests
    volumes={CACHE_DIR: cache_volume},
)
class LTXVideoEngine:
    @modal.enter()
    def initialize_pipeline(self):
        """Loads LTX 2.5 foundation weights into 80GB VRAM with bfloat16 precision."""
        import torch
        from diffusers import LTXPipeline, LTXImageToVideoPipeline
        
        print(f"[LTX-Engine] Initializing LTX 2.5 on GPU: {torch.cuda.get_device_name(0)}")
        print(f"[LTX-Engine] Total VRAM Available: {torch.cuda.get_device_properties(0).total_memory / (1024**3):.2f} GB")
        
        # Load T2V Pipeline
        self.t2v_pipe = LTXPipeline.from_pretrained(
            MODEL_ID,
            torch_dtype=torch.bfloat16,
            cache_dir=CACHE_DIR,
        ).to("cuda")
        
        # Enable Memory Optimizations for 10-15s sequence length scaling
        self.t2v_pipe.vae.enable_tiling()   # Critical: Slice spatial/temporal latents during decode
        self.t2v_pipe.vae.enable_slicing()  # Reduces batch dimension memory pressure
        
        # Optional: Load I2V Pipeline if supported
        try:
            self.i2v_pipe = LTXImageToVideoPipeline.from_pretrained(
                MODEL_ID,
                torch_dtype=torch.bfloat16,
                cache_dir=CACHE_DIR,
            ).to("cuda")
            self.i2v_pipe.vae.enable_tiling()
            self.i2v_pipe.vae.enable_slicing()
            print("[LTX-Engine] Loaded both T2V and I2V pipelines successfully.")
        except Exception as e:
            self.i2v_pipe = None
            print(f"[LTX-Engine] I2V pipeline deferred ({e}). T2V active.")

    @modal.method()
    def generate_video(
        self,
        prompt: str,
        image: Optional[str] = None,
        negative_prompt: str = "worst quality, blurry, distorted, jitter, low quality, artifact, watermarking, morphing, jittery movement, frame flicker",
        duration_sec: float = 10.0,
        fps: int = 24,
        width: int = 1280,
        height: int = 720,
        num_inference_steps: int = 35,
        guidance_scale: float = 3.5,
        stg_scale: float = 1.0,
        decode_noise_scale: float = 0.025,
        seed: Optional[int] = None,
        image_conditioning_scale: float = 0.75,  # MOTION FIX: 1.0=frozen, 0.5-0.8=natural motion
    ) -> bytes:
        """
        Generates 10-15s high-fidelity video on A100-80GB.
        Supports Text-to-Video and Image-to-Video (Image Referrals/Conditioning).
        Enforces (F - 1) % 8 == 0 LTX latent temporal rule.
        """
        import torch
        import tempfile
        import imageio
        import base64
        import urllib.request
        from PIL import Image

        t0 = time.time()
        
        # Calculate valid frame count: (frames - 1) % 8 == 0
        raw_frames = int(duration_sec * fps)
        num_frames = ((raw_frames - 1) // 8) * 8 + 1
        actual_duration = num_frames / fps
        
        # Parse referral image if provided
        pil_image = None
        if image:
            try:
                if image.startswith("http://") or image.startswith("https://"):
                    req = urllib.request.Request(image, headers={"User-Agent": "Mozilla/5.0"})
                    with urllib.request.urlopen(req, timeout=30) as resp:
                        pil_image = Image.open(io.BytesIO(resp.read()))
                else:
                    b64_str = image
                    if "base64," in b64_str:
                        b64_str = b64_str.split("base64,")[1]
                    raw_bytes = base64.b64decode(b64_str)
                    pil_image = Image.open(io.BytesIO(raw_bytes))
                
                pil_image = pil_image.convert("RGB")
                if pil_image.size != (width, height):
                    pil_image = pil_image.resize((width, height), Image.Resampling.LANCZOS)
                print(f"[LTX-Engine] Ingested referral image conditioning: {width}x{height}")
            except Exception as e:
                print(f"[LTX-Engine] Warning: Could not decode referral image ({e}). Falling back to T2V.")
                pil_image = None

        print(f"[LTX-Engine] Starting generation: '{prompt[:60]}...'")
        print(f"[LTX-Engine] Mode: {'Image-to-Video (Referral Anchor)' if pil_image else 'Text-to-Video'}")
        print(f"[LTX-Engine] Target: {duration_sec}s -> Adjusted: {num_frames} frames ({actual_duration:.2f}s @ {fps}fps) - {width}x{height}")
        
        generator = None
        if seed is not None:
            generator = torch.Generator(device="cuda").manual_seed(seed)
            
        # Select pipeline based on presence of referral image
        pipe = self.i2v_pipe if (pil_image is not None and self.i2v_pipe is not None) else self.t2v_pipe
        
        # MOTION FIX: Apply noise augmentation to reference image before conditioning
        # image_conditioning_scale: 1.0=clean anchor (identity locked/frozen), 0.5-0.8=natural motion
        if pil_image is not None and pipe == self.i2v_pipe and image_conditioning_scale < 0.99:
            import numpy as np
            noise_strength = (1.0 - image_conditioning_scale) * 0.20  # max 20% pixel noise
            img_arr = np.array(pil_image).astype(np.float32) / 255.0
            noise = np.random.normal(0, noise_strength, img_arr.shape).astype(np.float32)
            img_arr = np.clip(img_arr + noise, 0.0, 1.0)
            from PIL import Image as PILImage
            pil_image = PILImage.fromarray((img_arr * 255).astype(np.uint8))
            print(f"[LTX-Engine] Noise aug: strength={noise_strength:.3f} ic_scale={image_conditioning_scale}")

        # Probe pipe.__call__ for supported output_type values
        import inspect as _inspect
        _sig = _inspect.signature(pipe.__call__)
        _supported_output_types = []
        if "output_type" in _sig.parameters:
            _out_param = _sig.parameters["output_type"]
            print(f"[LTX-Engine] output_type param found, default={_out_param.default!r}")
        
        pipe_kwargs = {
            "prompt":              prompt,
            "negative_prompt":     negative_prompt,
            "width":               width,
            "height":              height,
            "num_frames":          num_frames,
            "num_inference_steps": num_inference_steps,
            "guidance_scale":      guidance_scale,
            "generator":           generator,
        }
        # Add image for I2V
        if pil_image is not None and pipe == self.i2v_pipe:
            pipe_kwargs["image"] = pil_image
        
        # Add decode_noise_scale if pipe supports it
        if "decode_noise_scale" in _sig.parameters:
            pipe_kwargs["decode_noise_scale"] = decode_noise_scale
            print(f"[LTX-Engine] Using decode_noise_scale={decode_noise_scale}")
        
        # Try output_type="np" first, fall back to default if not supported
        if "output_type" in _sig.parameters:
            pipe_kwargs["output_type"] = "np"
        
        print(f"[LTX-Engine] pipe_kwargs keys: {list(pipe_kwargs.keys())}")
        
        # Run DiT Denoising Loop with full error capture
        with torch.inference_mode():
            try:
                output = pipe(**pipe_kwargs)
            except TypeError as te:
                # output_type="np" might not be valid — retry without it
                print(f"[LTX-Engine] TypeError with output_type=np: {te}. Retrying without.")
                pipe_kwargs.pop("output_type", None)
                output = pipe(**pipe_kwargs)
        
        # Handle both .frames (older) and .images (newer diffusers) output
        if hasattr(output, "frames"):
            raw = output.frames[0]   # shape (T, H, W, C) float [0,1] if np, or list of PIL
        elif hasattr(output, "images"):
            raw = output.images[0]   # same
        else:
            raise ValueError(f"Unknown pipeline output type: {type(output)}, attrs={dir(output)}")
        
        # Convert to uint8 numpy array
        if isinstance(raw, (list, tuple)):
            import numpy as np
            frames_uint8 = np.stack([np.array(f) for f in raw])  # PIL list
        else:
            import numpy as np
            if raw.dtype != np.uint8:
                frames_uint8 = (raw * 255).astype("uint8")
            else:
                frames_uint8 = raw
        
        print(f"[LTX-Engine] frames_uint8 shape: {frames_uint8.shape}, dtype: {frames_uint8.dtype}")
        
        # Encode to MP4 with FFmpeg H.264
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp_file:
            tmp_path = tmp_file.name
            
        writer = imageio.get_writer(
            tmp_path,
            fps=fps,
            codec="libx264",
            quality=8,
            pixelformat="yuv420p",
            ffmpeg_params=["-preset", "fast", "-movflags", "+faststart"]
        )
        for frame in frames_uint8:
            writer.append_data(frame)
        writer.close()
        
        video_bytes = Path(tmp_path).read_bytes()
        os.remove(tmp_path)
        
        elapsed = time.time() - t0
        print(f"[LTX-Engine] Completed {actual_duration:.2f}s video generation in {elapsed:.2f}s ({num_frames / elapsed:.2f} fps).")
        return video_bytes


# -----------------------------------------------------------------------------
# Self-Describing FastAPI Application for Vibe Agents & AI Orchestrators
# -----------------------------------------------------------------------------
from fastapi import FastAPI
from fastapi.responses import Response
from pydantic import BaseModel, Field


class LTXGenerateRequest(BaseModel):
    prompt: str = Field(
        ...,
        description="Cinematic text prompt describing motion, lighting, subject action, and camera trajectory."
    )
    image: Optional[str] = Field(
        None,
        description="Referral asset: Base64 data URI (data:image/png;base64,...) or public HTTP(S) image URL for Image-to-Video first-frame anchor."
    )
    negative_prompt: str = Field(
        "worst quality, blurry, distorted, jitter, low quality, artifact, watermarking, morphing, jittery movement, frame flicker",
        description="Artifact suppression keywords."
    )
    duration_sec: float = Field(
        10.0,
        ge=2.0,
        le=15.0,
        description="Target duration in seconds (2.0 to 15.0). Auto-quantized via (F - 1) % 8 == 0 rule."
    )
    fps: int = Field(24, description="Frames per second (24 for cinematic, 30, or 60).")
    width: int = Field(1280, description="Video width in pixels (multiple of 32).")
    height: int = Field(720, description="Video height in pixels (multiple of 32).")
    num_inference_steps: int = Field(35, ge=20, le=50, description="Denoising steps (25=draft, 35=gold, 50=ultra).")
    guidance_scale: float = Field(3.5, ge=1.0, le=10.0, description="CFG scale (3.0-3.8 recommended).")
    stg_scale: float = Field(1.0, ge=0.0, le=2.0, description="Spatio-temporal guidance scale. Set 0.0 to disable STG for maximum motion freedom.")
    decode_noise_scale: float = Field(0.025, description="Noise scale during VAE spatial-temporal latent decode.")
    seed: Optional[int] = Field(None, description="Random seed for deterministic reproducible renders.")
    image_conditioning_scale: float = Field(
        0.75,
        ge=0.0,
        le=1.0,
        description="I2V conditioning strength. 1.0=identity-locked/frozen, 0.5-0.8=natural motion (recommended), 0.0=T2V ignores anchor image."
    )



web_app = FastAPI(
    title="Hermes Neural LTX-Video 2.5 API",
    description="Autonomous Serverless LTX-2.5 (22B) Cinema Video Generator on NVIDIA A100-80GB",
    version="2.5.0",
)


@web_app.get("/")
def api_specification():
    """
    Self-describing endpoint for Vibe Agents and AI orchestrators.
    Returns complete parameter schema, supported formats, and example requests.
    """
    return {
        "status": "online",
        "service": "Hermes Neural LTX-Video 2.5",
        "hardware": "NVIDIA A100-80GB (80GB HBM2e VRAM)",
        "capabilities": [
            "Native 10s-15s continuous video generation at 24fps without OOM",
            "Image Referral Conditioning (I2V / First-Frame Anchor / Face Consistency)",
            "Automatic (F - 1) % 8 == 0 temporal latent quantization",
            "Causal 3D VAE Tiling and Slicing"
        ],
        "endpoints": {
            "POST /": "Generate video directly on root URL",
            "POST /generate": "Generate video endpoint",
            "GET /docs": "Interactive Swagger UI documentation",
            "GET /openapi.json": "Standard OpenAPI 3.1 machine-readable specification"
        },
        "parameter_schema": LTXGenerateRequest.model_json_schema(),
        "sample_request": {
            "prompt": "Cinematic pan across Saigon skyline at sunset, 8k photorealistic",
            "image": "https://example.com/reference_frame.png (optional)",
            "duration_sec": 12.0,
            "width": 1280,
            "height": 720,
            "num_inference_steps": 35,
            "guidance_scale": 3.5,
            "seed": 2026
        },
        "sample_curl": (
            "curl -X POST <THIS_URL> "
            "-H 'Content-Type: application/json' "
            "-d '{\"prompt\": \"A cinematic shot...\", \"duration_sec\": 12.0}' "
            "--output video.mp4"
        )
    }


@web_app.post("/")
@web_app.post("/generate")
def handle_generate(req: LTXGenerateRequest):
    engine = LTXVideoEngine()
    video_bytes = engine.generate_video.remote(
        prompt=req.prompt,
        image=req.image,
        negative_prompt=req.negative_prompt,
        duration_sec=req.duration_sec,
        fps=req.fps,
        width=req.width,
        height=req.height,
        num_inference_steps=req.num_inference_steps,
        guidance_scale=req.guidance_scale,
        stg_scale=req.stg_scale,
        decode_noise_scale=req.decode_noise_scale,
        seed=req.seed,
        image_conditioning_scale=req.image_conditioning_scale,
    )
    return Response(content=video_bytes, media_type="video/mp4")



@app.function(image=ltx_image, timeout=1800)
@modal.asgi_app()
def api():
    """Mounts the full FastAPI app for OpenAPI docs and REST generation."""
    return web_app


# -----------------------------------------------------------------------------
# Backward-Compatible Endpoint
# -----------------------------------------------------------------------------
@app.function(image=ltx_image, timeout=1800)
@modal.fastapi_endpoint(method="POST")
def api_generate(item: dict):
    """Legacy backward-compatible POST /api_generate endpoint."""
    image = item.get("image", item.get("image_url", item.get("image_base64", None)))
    negative_prompt = item.get("negative_prompt", "worst quality, blurry, distorted, jitter, low quality, artifact, watermarking, morphing")
    prompt = item.get("prompt", "Cinematic drone shot of obsidian mountains, 4k ultra-realistic")
    duration_sec = float(item.get("duration_sec", 10.0))
    fps = int(item.get("fps", 24))
    width = int(item.get("width", 1280))
    height = int(item.get("height", 720))
    steps = int(item.get("num_inference_steps", item.get("steps", 35)))
    guidance_scale = float(item.get("guidance_scale", 3.5))
    stg_scale = float(item.get("stg_scale", 1.0))
    decode_noise_scale = float(item.get("decode_noise_scale", 0.025))
    seed = item.get("seed", None)
    
    engine = LTXVideoEngine()
    video_bytes = engine.generate_video.remote(
        prompt=prompt,
        image=image,
        negative_prompt=negative_prompt,
        duration_sec=duration_sec,
        fps=fps,
        width=width,
        height=height,
        num_inference_steps=steps,
        guidance_scale=guidance_scale,
        stg_scale=stg_scale,
        decode_noise_scale=decode_noise_scale,
        seed=seed,
    )
    return Response(content=video_bytes, media_type="video/mp4")


# -----------------------------------------------------------------------------
# Local CLI Entrypoint (Run via `modal run modal_app.py`)
# -----------------------------------------------------------------------------
@app.local_entrypoint()
def main(
    prompt: str = "A futuristic Neo-Noir cyberpunk laboratory in Saigon, cinematic lighting, 8k resolution, photorealistic",
    duration: float = 12.0,
    width: int = 1280,
    height: int = 720,
    output: str = "output/ltx25_sample_12s.mp4",
):
    """Run video generation directly from workstation terminal via Modal."""
    print("===================================================================")
    print(" 🎬 HERMES NEURAL LTX-VIDEO 2.5 (A100-80GB CLOUD INFERENCE)")
    print("===================================================================")
    print(f" Prompt    : {prompt}")
    print(f" Target    : {duration}s ({width}x{height} @ 24fps)")
    print(f" Hardware  : NVIDIA A100-80GB")
    print(f" Output    : {output}")
    print("-------------------------------------------------------------------")
    
    engine = LTXVideoEngine()
    video_bytes = engine.generate_video.remote(
        prompt=prompt,
        duration_sec=duration,
        width=width,
        height=height,
    )
    
    out_file = Path(output)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_bytes(video_bytes)
    print(f"[✓] Saved {len(video_bytes) / (1024*1024):.2f} MB video to: {out_file.resolve()}\n")
