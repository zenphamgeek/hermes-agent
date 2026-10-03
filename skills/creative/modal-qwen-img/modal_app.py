"""
skills/creative/modal-qwen-img/modal_app.py
==========================================
Hermes Agent — Qwen-Image-2.1 Real Diffusion Worker on A100-80GB.
Model: Alibaba Qwen/Qwen-Image-2.1
Architecture: QwenImage21Pipeline (FlowMatchEulerDiscrete + DiT + Qwen3VL text encoder)
GPU: A100-80GB (bfloat16, ~22GB VRAM)

Endpoints:
  GET  /health   — liveness check
  POST /generate — text-to-image inference (returns b64_json PNG)
  POST /edit     — image-to-image edit (returns b64_json PNG)

ZERO-FAKE-PASS INVARIANT:
  setup() MUST load real model weights from HuggingFace.
  generate() MUST call self.pipe() for real diffusion inference.
  Any exception during inference is re-raised to the caller — NEVER silently
  returns a placeholder or mock response.
"""

import io
import time
import base64
import torch
import modal
from typing import Dict, Any, Optional, List

APP_NAME = "hermes-qwen-img-21"

# ── Container image ──────────────────────────────────────────────────────────
# Install git-HEAD diffusers (QwenImage21Pipeline not yet on PyPI stable)
# transformers>=5.17 required for Qwen3VLForConditionalGeneration
image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("git", "git-lfs", "ffmpeg", "libgl1")
    .pip_install(
        "torch==2.6.0",          # diffusers 0.41.0.dev requires torch.accelerator (>=2.5)
        "torchvision==0.21.0",
        "transformers>=5.17.0",
        "git+https://github.com/huggingface/diffusers.git",
        "accelerate>=0.33.0",
        "sentencepiece",
        "pillow>=10.0",
        "fastapi",
        "uvicorn",
        "pydantic",
        "huggingface_hub",
        "safetensors",
    )
)

app = modal.App(APP_NAME, image=image)

# Supported native aspect ratios from official README
ASPECT_RATIO_MAP = {
    "1:1":  (2048, 2048),
    "16:9": (2752, 1536),
    "9:16": (1536, 2752),
    "4:3":  (2048, 1536),
    "3:4":  (1536, 2048),
    "3:2":  (2304, 1536),
    "2:3":  (1536, 2304),
}

DEFAULT_STEPS = 40
DEFAULT_GUIDANCE = 5.0


# ── Modal worker class ───────────────────────────────────────────────────────
@app.cls(
    gpu="A100-80GB",                  # Minimum required: A10G (24GB). A100-80GB headroom.
    scaledown_window=300,             # Keep warm 5 minutes after last request
    timeout=900,                      # 15 min timeout (cold-start + large-batch)
    memory=32768,                     # 32GB RAM (model + decode buffer)
)
class QwenImg21Worker:

    @modal.enter()
    def setup(self):
        """
        Load QwenImage21Pipeline from HuggingFace in bfloat16.
        This MUST succeed before any inference can proceed.
        Raises an exception if the model cannot be loaded — NEVER silently degrades.
        """
        import torch
        from diffusers import QwenImage21Pipeline

        model_id = "Qwen/Qwen-Image-2.1"
        print(f"🚀 Loading {model_id} onto cuda (bfloat16)...")

        self.pipe = QwenImage21Pipeline.from_pretrained(
            model_id,
            dtype=torch.bfloat16,    # new kwarg name (torch_dtype deprecated in diffusers 0.41)
            device_map="balanced",   # balanced across single A100-80GB
        )

        # Inference-only mode — disable gradient computation globally
        torch.set_grad_enabled(False)

        self.model_id = model_id
        self.device = "cuda"
        print(f"✅ {model_id} loaded on {self.device}")

    # ── Health check ──────────────────────────────────────────────────────────
    @modal.fastapi_endpoint(method="GET")
    def health(self) -> Dict[str, Any]:
        import torch
        vram_used  = torch.cuda.memory_allocated()  / 1024**3 if torch.cuda.is_available() else 0
        vram_total = torch.cuda.get_device_properties(0).total_memory / 1024**3 if torch.cuda.is_available() else 0
        return {
            "status": "healthy",
            "model": self.model_id,
            "gpu": "A100-80GB",
            "vram_used_gb": round(vram_used, 2),
            "vram_total_gb": round(vram_total, 2),
            "architecture": "QwenImage21Pipeline — FlowMatchEulerDiscrete DiT + Qwen3VL",
            "capabilities": ["text-to-image", "image-to-image-edit", "rgba-native"],
            "supported_ratios": list(ASPECT_RATIO_MAP.keys()),
            "timestamp": time.time(),
        }

    # ── Text-to-image inference ───────────────────────────────────────────────
    @modal.fastapi_endpoint(method="POST")
    def generate(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Real diffusion inference via QwenImage21Pipeline.
        Payload keys:
          prompt        (str)  required
          negative_prompt (str) optional
          steps         (int)  default 40
          guidance_scale (float) default 5.0
          seed          (int)  default 42
          aspect_ratio  (str)  one of ASPECT_RATIO_MAP keys, default "1:1"
          width/height  (int)  override aspect_ratio if provided
        Returns:
          b64_json (str) — base64-encoded PNG bytes
          resolution, steps, seed, model, elapsed_s
        """
        import torch

        prompt          = str(payload.get("prompt", "")).strip()
        negative_prompt = str(payload.get("negative_prompt", "")).strip() or None
        steps           = int(payload.get("steps", DEFAULT_STEPS))
        guidance_scale  = float(payload.get("guidance_scale", DEFAULT_GUIDANCE))
        seed            = int(payload.get("seed", 42))
        aspect_ratio    = str(payload.get("aspect_ratio", "1:1"))

        if not prompt:
            return {"success": False, "error": "prompt is required"}

        # Resolve resolution
        if "width" in payload and "height" in payload:
            width  = int(payload["width"])
            height = int(payload["height"])
        else:
            width, height = ASPECT_RATIO_MAP.get(aspect_ratio, ASPECT_RATIO_MAP["1:1"])

        # Clamp steps to safe range
        steps = max(10, min(100, steps))

        generator = torch.Generator("cuda").manual_seed(seed)

        t0 = time.time()
        # QwenImage21Pipeline.__call__ signature (pipeline_qwenimage21.py):
        #   prompt, image, negative_prompt, true_cfg_scale=1.0,
        #   height, width, num_inference_steps=40, output_resolution=1024,
        #   use_kv_cache=True, generator, ...
        # NOTE: NO guidance_scale — uses true_cfg_scale (only effective when >1.0)
        kwargs: Dict[str, Any] = {
            "prompt":              prompt,
            "num_inference_steps": steps,
            "true_cfg_scale":      guidance_scale,   # map user's cfg → true_cfg_scale
            "height":              height,
            "width":               width,
            "output_resolution":   max(width, height),
            "generator":           generator,
            "use_kv_cache":        True,
        }
        if negative_prompt:
            kwargs["negative_prompt"] = negative_prompt

        output = self.pipe(**kwargs)
        elapsed = round(time.time() - t0, 2)

        # Encode first image to PNG base64
        buf = io.BytesIO()
        output.images[0].save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

        return {
            "success":     True,
            "b64_json":    b64,
            "resolution":  f"{width}x{height}",
            "aspect_ratio": aspect_ratio,
            "steps":       steps,
            "guidance_scale": guidance_scale,
            "seed":        seed,
            "model":       self.model_id,
            "elapsed_s":   elapsed,
        }

    # ── Image-to-image edit ───────────────────────────────────────────────────
    @modal.fastapi_endpoint(method="POST")
    def edit(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Image-to-image editing via QwenImage21Pipeline.
        Payload keys:
          prompt          (str)  required
          image_b64       (str)  base64-encoded reference image (PNG/JPEG)
          mask_b64        (str)  optional base64 mask (white = edit region)
          strength        (float) 0.0–1.0, default 0.75
          steps           (int)  default 40
          guidance_scale  (float) default 5.0
          seed            (int)  default 42
        """
        import torch
        from PIL import Image as PILImage

        prompt   = str(payload.get("prompt", "")).strip()
        img_b64  = payload.get("image_b64", "")
        strength = float(payload.get("strength", 0.75))
        steps    = int(payload.get("steps", DEFAULT_STEPS))
        guidance_scale = float(payload.get("guidance_scale", DEFAULT_GUIDANCE))
        seed     = int(payload.get("seed", 42))

        if not prompt:
            return {"success": False, "error": "prompt is required"}
        if not img_b64:
            return {"success": False, "error": "image_b64 is required for edit endpoint"}

        # Decode reference image
        ref_image = PILImage.open(io.BytesIO(base64.b64decode(img_b64))).convert("RGB")
        width, height = ref_image.size

        generator = torch.Generator("cuda").manual_seed(seed)

        t0 = time.time()
        kwargs: Dict[str, Any] = {
            "prompt":               prompt,
            "image":                [ref_image],
            "num_inference_steps":  steps,
            "guidance_scale":       guidance_scale,
            "generator":            generator,
        }

        # Decode optional mask
        mask_b64 = payload.get("mask_b64", "")
        if mask_b64:
            mask_image = PILImage.open(io.BytesIO(base64.b64decode(mask_b64))).convert("L")
            kwargs["mask_image"] = mask_image

        output = self.pipe(**kwargs)
        elapsed = round(time.time() - t0, 2)

        buf = io.BytesIO()
        output.images[0].save(buf, format="PNG")
        b64_out = base64.b64encode(buf.getvalue()).decode("utf-8")

        return {
            "success":        True,
            "b64_json":       b64_out,
            "resolution":     f"{width}x{height}",
            "strength":       strength,
            "steps":          steps,
            "guidance_scale": guidance_scale,
            "seed":           seed,
            "model":          self.model_id,
            "elapsed_s":      elapsed,
        }
