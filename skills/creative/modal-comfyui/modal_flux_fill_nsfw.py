"""
skills/creative/modal-comfyui/modal_flux_fill_nsfw.py
=====================================================
Hermes Agent - Multi-Worker Serverless FLUX.1 Fill [dev] + NSFW LoRA Engine on Modal.

Architecture:
- Black Forest Labs FLUX.1 Fill [dev] DiT (FP8) for native inpaint, edit & generation
- Dual CLIP: T5XXL FP8 + CLIP-L
- SLDR FLUX NSFW v2 Photorealism & Anatomy LoRA injection
- Native ComfyUI Headless Web GUI + REST API on port 8188
- Modal Persistent Volume cache (nsfw-flux-fill-cache) to persist weights across restarts
- Scale-to-zero idle timeout: 300s (5 minutes)
"""

import io
import os
import json
import time
import shutil
import urllib.request
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional

import modal
from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel, Field

APP_NAME = "hermes-flux-fill-nsfw"
COMFY_DIR = "/opt/ComfyUI"
CACHE_DIR = "/cache/comfyui"

app = modal.App(APP_NAME)

# Persistent volume for model checkpoints across worker restarts
models_volume = modal.Volume.from_name("nsfw-flux-fill-cache", create_if_missing=True)

# Container image definition
comfy_image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install(
        "git",
        "ffmpeg",
        "libgl1-mesa-glx",
        "libglib2.0-0",
        "wget",
        "curl",
        "libsndfile1"
    )
    .pip_install(
        "torch>=2.4.0",
        "torchvision",
        "torchaudio",
        "transformers>=4.48.0",
        "accelerate>=1.2.0",
        "sentencepiece",
        "einops",
        "safetensors",
        "fastapi[standard]",
        "pydantic",
        "pillow",
        "imageio[ffmpeg]",
        "websocket-client",
        "requests",
        "aiohttp",
        "huggingface_hub"
    )
    .run_commands(
        # 1. Clone ComfyUI core
        "git clone https://github.com/comfyanonymous/ComfyUI.git /opt/ComfyUI",
        "cd /opt/ComfyUI && pip install -r requirements.txt",
        # 2. Install specialized nodes for GGUF/FP8 and inpainting
        "git clone https://github.com/city96/ComfyUI-GGUF /opt/ComfyUI/custom_nodes/ComfyUI-GGUF || true",
        "git clone https://github.com/ltdrdata/ComfyUI-Impact-Pack.git /opt/ComfyUI/custom_nodes/ComfyUI-Impact-Pack || true",
    )
    .env({
        "HF_HOME": f"{CACHE_DIR}/huggingface",
        "TORCH_CUDA_ARCH_LIST": "8.0;8.6;8.9;9.0",
        "PYTHONPATH": f"{COMFY_DIR}:$PYTHONPATH",
    })
)


class InlineWorkflowRequest(BaseModel):
    workflow: Dict[str, Any] = Field(..., description="Full ComfyUI workflow JSON graph")
    client_id: Optional[str] = Field("hermes_flux_client", description="Client identifier")


@app.cls(
    image=comfy_image,
    gpu=os.environ.get("MODAL_GPU", "A10G"),  # A10G (24GB) or L4 (24GB)
    timeout=1800,                            # 30 minutes execution buffer
    scaledown_window=300,                    # 5-minute scale-to-zero keep-warm window
    volumes={"/opt/ComfyUI/models": models_volume},
)
class FluxFillNSFWRunner:

    def _ensure_dir_and_file(self, target_path: str, url: str, min_size: int, label: str):
        """Helper to download model file to persistent volume if missing or corrupt."""
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        if os.path.exists(target_path) and os.path.getsize(target_path) >= min_size:
            print(f"✅ [FLUX Engine] {label} verified ({os.path.getsize(target_path):,} bytes).")
            return

        print(f"📥 [FLUX Engine] Downloading {label} from {url}...")
        tmp_path = f"{target_path}.tmp"
        cmd = ["curl", "-f", "-L", url, "-o", tmp_path]
        res = subprocess.run(cmd)
        if res.returncode != 0:
            # Fallback to wget
            subprocess.run(["wget", "-c", url, "-O", tmp_path], check=True)

        if os.path.exists(tmp_path) and os.path.getsize(tmp_path) >= min_size:
            os.rename(tmp_path, target_path)
            print(f"✅ [FLUX Engine] {label} downloaded and verified.")
        else:
            raise RuntimeError(f"Failed to download valid file for {label} (min_size={min_size})")

    @modal.enter()
    def setup_weights(self):
        """Initializes model directory structure and downloads verified weights to volume."""
        subdirs = ["checkpoints", "clip", "vae", "unet", "loras", "custom_nodes", "input", "output"]
        for s in subdirs:
            os.makedirs(f"/opt/ComfyUI/models/{s}", exist_ok=True)

        clip_dir = "/opt/ComfyUI/models/clip"
        vae_dir = "/opt/ComfyUI/models/vae"
        unet_dir = "/opt/ComfyUI/models/unet"
        lora_dir = "/opt/ComfyUI/models/loras"

        # 1. FLUX VAE (335MB) - Public Hugging Face mirror
        self._ensure_dir_and_file(
            f"{vae_dir}/ae.safetensors",
            "https://huggingface.co/Osrivers/ae.safetensors/resolve/main/ae.safetensors",
            300_000_000,
            "FLUX VAE (ae.safetensors)"
        )

        # 2. CLIP-L (246MB) - Public Comfy repo
        self._ensure_dir_and_file(
            f"{clip_dir}/clip_l.safetensors",
            "https://huggingface.co/comfyanonymous/flux_text_encoders/resolve/main/clip_l.safetensors",
            200_000_000,
            "CLIP-L Text Encoder"
        )

        # 3. T5XXL FP8 (4.9GB) - Public Comfy repo
        self._ensure_dir_and_file(
            f"{clip_dir}/t5xxl_fp8_e4m3fn.safetensors",
            "https://huggingface.co/comfyanonymous/flux_text_encoders/resolve/main/t5xxl_fp8_e4m3fn.safetensors",
            4_000_000_000,
            "T5XXL FP8 Text Encoder"
        )

        # 4. FLUX.1 Fill [dev] FP8 (11.9GB Inpaint & Edit DiT) - Public mirror
        self._ensure_dir_and_file(
            f"{unet_dir}/flux1-fill-dev-fp8.safetensors",
            "https://huggingface.co/wjndd/flux1-fill-dev-fp8/resolve/main/flux1-fill-dev-fp8.safetensors",
            10_000_000_000,
            "FLUX.1 Fill [dev] FP8 DiT"
        )

        # 5. SLDR FLUX NSFW v2 Photorealism & Anatomy LoRA (160MB)
        lora_target = f"{lora_dir}/sldr_flux_nsfw_v2-studio.safetensors"
        self._ensure_dir_and_file(
            lora_target,
            "https://huggingface.co/xey/sldr_flux_nsfw_v2-studio/resolve/main/sldr_flux_nsfw_v2-studio.safetensors",
            50_000_000,
            "SLDR FLUX NSFW v2 LoRA"
        )
        # Also symlink to flux_nsfw_detailer.safetensors for compatibility
        alias_target = f"{lora_dir}/flux_nsfw_detailer.safetensors"
        if not os.path.exists(alias_target):
            try:
                os.symlink(lora_target, alias_target)
            except Exception:
                shutil.copyfile(lora_target, alias_target)

        models_volume.commit()
        print("💾 [FLUX Volume] Persistent volume committed successfully.")

    def _ensure_comfyui_process(self):
        """Starts ComfyUI server if not already responding on port 8188."""
        try:
            with urllib.request.urlopen("http://127.0.0.1:8188/system_stats", timeout=1) as resp:
                if resp.status == 200:
                    return
        except Exception:
            pass

        print("🚀 [FLUX Engine] Launching ComfyUI server on port 8188...")
        cmd = f"python3 {COMFY_DIR}/main.py --listen 0.0.0.0 --port 8188 --preview-method auto"
        subprocess.Popen(cmd, shell=True)

    @modal.web_server(port=8188, startup_timeout=600)
    def web_ui(self):
        """Exposes the ComfyUI Interactive Web GUI & REST API on port 8188."""
        self._ensure_comfyui_process()

    @modal.fastapi_endpoint(method="GET")
    def health(self) -> Dict[str, Any]:
        """Probes worker health, VRAM, and GPU status."""
        self._ensure_comfyui_process()
        import torch
        device_name = torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU"
        vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3) if torch.cuda.is_available() else 0.0
        return {
            "status": "healthy",
            "model": "FLUX.1 Fill [dev] FP8 + NSFW LoRA",
            "gpu": device_name,
            "vram_gb": round(vram_gb, 2),
            "tier": os.environ.get("MODAL_GPU", "A10G"),
            "endpoints": {
                "web_ui": "https://<workspace>--hermes-flux-fill-nsfw-fluxfillnsfwrunner-web-ui.modal.run",
                "health": "GET /health",
                "execute_workflow": "POST /execute_workflow"
            }
        }

    @modal.fastapi_endpoint(method="POST")
    def execute_workflow(self, req: InlineWorkflowRequest) -> Dict[str, Any]:
        """Submits an arbitrary ComfyUI prompt graph directly to the local server."""
        self._ensure_comfyui_process()
        clean_workflow = {k: v for k, v in req.workflow.items() if k != "_meta"}
        client_id = req.client_id or f"hermes_flux_{int(time.time())}"

        payload = json.dumps({"prompt": clean_workflow, "client_id": client_id}).encode("utf-8")
        prompt_req = urllib.request.Request(
            "http://127.0.0.1:8188/prompt",
            data=payload,
            headers={"Content-Type": "application/json"}
        )

        with urllib.request.urlopen(prompt_req, timeout=10) as resp:
            submit_res = json.loads(resp.read().decode())

        prompt_id = submit_res.get("prompt_id")
        return {
            "status": "submitted",
            "prompt_id": prompt_id,
            "client_id": client_id,
            "message": "Workflow queued successfully in ComfyUI"
        }
