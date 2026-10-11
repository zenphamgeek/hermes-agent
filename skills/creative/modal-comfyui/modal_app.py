"""
skills/creative/modal-comfyui/modal_app.py
==========================================
Hermes Agent - Modal Serverless ComfyUI Engine with Template JSON Orchestration.

Features:
- Full Headless ComfyUI Server running with @modal.web_server(port=8188)
- Native Support for Template JSON workflows:
    1. Wan2.2-S2V-14B (Speech-to-Video Audio Conditioning)
    2. LTX-Video-2.5 (22B Cinema Video DiT with 3D VAE Tiling)
    3. Qwen-Image-2.1 (7B Single-Stream DiT Text-to-Image & Edit)
- Persistent Models Volume (/root/ComfyUI/models) to prevent re-downloads
- REST API (/run_template) for 1-click Agent execution of canonical templates
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

APP_NAME = "hermes-comfyui-engine"
COMFY_DIR = "/opt/ComfyUI"
CACHE_DIR = "/cache/comfyui"

app = modal.App(APP_NAME)

# Persistent volume for model checkpoints
models_volume = modal.Volume.from_name("hermes-comfyui-cache", create_if_missing=True)

# Container Image with ComfyUI & specialized video/image nodes
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
        "soundfile",
        "librosa"
    )
    .run_commands(
        # 1. Clone ComfyUI core
        "git clone https://github.com/comfyanonymous/ComfyUI.git /opt/ComfyUI",
        "cd /opt/ComfyUI && pip install -r requirements.txt",
        # 2. Install Wan Video & S2V custom nodes
        "git clone https://github.com/kijai/ComfyUI-WanVideoWrapper.git /opt/ComfyUI/custom_nodes/ComfyUI-WanVideoWrapper || true",
        # 3. Install LTX-Video custom nodes
        "git clone https://github.com/kijai/ComfyUI-LTXVideo.git /opt/ComfyUI/custom_nodes/ComfyUI-LTXVideo || true",
        # 4. Install Video Helper Suite for high quality video export
        "git clone https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite.git /opt/ComfyUI/custom_nodes/ComfyUI-VideoHelperSuite || true",
        # 5. Install Face Restoration and Impact Pack for FaceDetailer on GPU node
        "git clone https://github.com/capt-iv/comfyui-face-restoration.git /opt/ComfyUI/custom_nodes/comfyui-face-restoration || true",
        "git clone https://github.com/ltdrdata/ComfyUI-Impact-Pack.git /opt/ComfyUI/custom_nodes/ComfyUI-Impact-Pack || true",
        # 6. Remove existing models directory so Modal volume mounts cleanly without conflict
        "rm -rf /opt/ComfyUI/models",
    )
    .env({
        "HF_HOME": f"{CACHE_DIR}/huggingface",
        "TORCH_CUDA_ARCH_LIST": "8.0;9.0",
        "PYTHONPATH": f"{COMFY_DIR}:$PYTHONPATH",
    })
)


class TemplateRequest(BaseModel):
    template: str = Field(..., description="Template name: 'wan22_s2v_14b', 'ltx_video_25', or 'qwen_image_21'")
    prompt: Optional[str] = Field(None, description="Cinematic text prompt")
    negative_prompt: Optional[str] = Field(None, description="Negative prompt")
    image_url: Optional[str] = Field(None, description="Input reference/portrait image URL or base64")
    audio_url: Optional[str] = Field(None, description="Input speech audio URL or base64 (for S2V)")
    width: Optional[int] = Field(None, description="Render width (e.g. 1024 or 1280)")
    height: Optional[int] = Field(None, description="Render height (e.g. 704 or 720)")
    seed: Optional[int] = Field(None, description="Seed for deterministic generation")
    steps: Optional[int] = Field(None, description="Sampling steps")
    cfg: Optional[float] = Field(None, description="Guidance scale")


class InlineWorkflowRequest(BaseModel):
    workflow: Dict[str, Any] = Field(..., description="Full ComfyUI workflow JSON graph (prompt nodes mapping)")
    template_id: Optional[str] = Field("custom_inline", description="Template ID or name for tracking")
    sha256: Optional[str] = Field(None, description="Template content hash for verification")
    prompt: Optional[str] = Field(None, description="Cinematic text prompt to override in graph")
    negative_prompt: Optional[str] = Field(None, description="Negative prompt to override in graph")
    image_url: Optional[str] = Field(None, description="Input reference/portrait image URL or base64")
    audio_url: Optional[str] = Field(None, description="Input speech audio URL or base64 (for S2V)")
    width: Optional[int] = Field(None, description="Render width (e.g. 1024 or 1280)")
    height: Optional[int] = Field(None, description="Render height (e.g. 704 or 720)")
    seed: Optional[int] = Field(None, description="Seed for deterministic generation")
    steps: Optional[int] = Field(None, description="Sampling steps")
    cfg: Optional[float] = Field(None, description="Guidance scale")


@app.cls(
    image=comfy_image,
    gpu="A100-80GB",              # Required for 14B Wan S2V & 22B LTX 2.5
    timeout=1800,                 # 30-minute timeout buffer
    scaledown_window=300,         # Keep warm for 5 minutes between generation jobs
    volumes={"/opt/ComfyUI/models": models_volume},
)
class ComfyUIRunner:
    @modal.enter()
    def start_background_server(self):
        """Launches ComfyUI server in the background on port 8188 if not already running."""
        # Ensure model subdirectories exist
        for sub in ["checkpoints", "clip", "vae", "unet", "audio_encoders", "facerestore_models", "ultralytics/bbox", "sams", "custom_nodes", "loras", "upscale_models"]:
            os.makedirs(f"/opt/ComfyUI/models/{sub}", exist_ok=True)

        print("🚀 Starting ComfyUI serverless engine on port 8188...")
        cmd = ["python3", f"{COMFY_DIR}/main.py", "--listen", "0.0.0.0", "--port", "8188", "--preview-method", "none"]
        self.proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        
        # Wait up to 30s for server to become responsive
        start = time.time()
        ready = False
        while time.time() - start < 30:
            try:
                urllib.request.urlopen("http://127.0.0.1:8188/system_stats", timeout=2)
                ready = True
                break
            except Exception:
                time.sleep(1.0)
                
        if ready:
            print("✅ ComfyUI Engine is fully operational on http://127.0.0.1:8188")
        else:
            print("⚠️ ComfyUI did not respond within 30s, continuing anyway...")

    @modal.web_server(port=8188, startup_timeout=60)
    def web_ui(self):
        """Exposes the full ComfyUI Web GUI and REST/WebSocket API to the internet."""
        cmd = f"python3 {COMFY_DIR}/main.py --listen 0.0.0.0 --port 8188 --preview-method auto"
        subprocess.Popen(cmd, shell=True)

    @modal.fastapi_endpoint(method="GET")
    def health(self) -> Dict[str, Any]:
        """Health and hardware probe endpoint."""
        import torch
        device_name = torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU"
        vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3) if torch.cuda.is_available() else 0.0
        return {
            "status": "healthy",
            "engine": "ComfyUI Serverless",
            "gpu": device_name,
            "vram_gb": round(vram_gb, 2),
            "supported_templates": ["wan22_s2v_14b", "ltx_video_25", "qwen_image_21"],
            "endpoints": {
                "web_ui": "https://<workspace>--hermes-comfyui-engine-comfyuirunner-web-ui.modal.run",
                "run_template": "POST /run_template",
                "execute_workflow": "POST /execute_workflow",
                "comfy_prompt": "POST /prompt",
            }
        }

    @modal.fastapi_endpoint(method="POST")
    def execute_workflow(self, req: InlineWorkflowRequest) -> Dict[str, Any]:
        """
        Executes a dynamic ComfyUI workflow JSON graph received directly in the request body.
        Enables Real-Time Template Registry synchronization with zero worker redeployment.
        """
        import hashlib
        print(f"[ComfyUI] Executing inline workflow for template: {req.template_id}")

        raw_graph = req.workflow
        if not raw_graph or not isinstance(raw_graph, dict):
            raise HTTPException(status_code=400, detail="Invalid workflow graph: must be a non-empty JSON object.")

        # Clean metadata if present
        clean_workflow = {k: v for k, v in raw_graph.items() if k != "_meta"}

        # Calculate actual payload hash
        computed_sha = hashlib.sha256(json.dumps(clean_workflow, sort_keys=True).encode("utf-8")).hexdigest()
        if req.sha256 and req.sha256 != computed_sha:
            print(f"[ComfyUI] Warning: Provided sha256 ({req.sha256[:10]}...) differs from clean graph hash ({computed_sha[:10]}...)")

        # Optional parameter overrides injection into the graph
        for node_id, node in clean_workflow.items():
            if not isinstance(node, dict) or "class_type" not in node:
                continue
            inputs = node.get("inputs", {})
            cls = node.get("class_type")

            # Positive & negative prompts
            if cls in ["CLIPTextEncode", "TextEncodeQwenImageEdit"]:
                meta_title = node.get("_meta", {}).get("title", "").lower()
                if "negative" not in meta_title and req.prompt:
                    if "text" in inputs:
                        inputs["text"] = req.prompt
                    elif "prompt" in inputs:
                        inputs["prompt"] = req.prompt
                elif "negative" in meta_title and req.negative_prompt:
                    inputs["text"] = req.negative_prompt

            # KSampler parameters
            if cls in ["KSampler"]:
                if req.seed is not None:
                    inputs["seed"] = req.seed
                if req.steps is not None:
                    inputs["steps"] = req.steps
                if req.cfg is not None:
                    inputs["cfg"] = req.cfg

            # Dimensions
            if cls in ["EmptyLTXVLatentVideo", "EmptyQwenImageLayeredLatentImage", "WanSoundImageToVideo"]:
                if req.width is not None and "width" in inputs:
                    inputs["width"] = req.width
                if req.height is not None and "height" in inputs:
                    inputs["height"] = req.height

        # Submit workflow directly to ComfyUI port 8188
        client_id = f"hermes_inline_{int(time.time())}"
        payload = json.dumps({"prompt": clean_workflow, "client_id": client_id}).encode("utf-8")
        prompt_req = urllib.request.Request(
            "http://127.0.0.1:8188/prompt",
            data=payload,
            headers={"Content-Type": "application/json"}
        )

        with urllib.request.urlopen(prompt_req, timeout=10) as resp:
            submit_res = json.loads(resp.read().decode())

        prompt_id = submit_res.get("prompt_id")
        print(f"[ComfyUI] Submitted inline workflow job prompt_id: {prompt_id}")

        return {
            "success": True,
            "template_id": req.template_id,
            "sha256": computed_sha,
            "prompt_id": prompt_id,
            "nodes_count": len(clean_workflow),
            "status": "queued_or_executing",
            "message": "Inline workflow graph dispatched successfully into ComfyUI Serverless Graph Engine",
            "history_url": f"http://127.0.0.1:8188/history/{prompt_id}",
        }

    @modal.fastapi_endpoint(method="POST")
    def run_template(self, req: TemplateRequest) -> Dict[str, Any]:
        """Executes one of the canonical template JSONs with injected parameters."""
        print(f"[ComfyUI] Dispatching template: {req.template}")
        
        # 1. Load canonical template JSON
        template_file = Path(__file__).parent / f"workflows/{req.template}_api.json"
        if not template_file.exists():
            template_file = Path(f"/home/zen/hermes-agent/skills/creative/comfyui/workflows/{req.template}_api.json")
            
        if not template_file.exists():
            raise HTTPException(status_code=404, detail=f"Template {req.template} not found.")

        with open(template_file, "r", encoding="utf-8") as f:
            workflow = json.load(f)

        # 2. Inject dynamic parameters into the workflow graph
        for node_id, node in workflow.items():
            if not isinstance(node, dict) or "class_type" not in node:
                continue
            inputs = node.get("inputs", {})
            cls = node.get("class_type")

            # Positive Prompt injection
            if cls in ["CLIPTextEncode", "TextEncodeQwenImageEdit"]:
                meta_title = node.get("_meta", {}).get("title", "").lower()
                if "negative" not in meta_title and req.prompt:
                    if "text" in inputs:
                        inputs["text"] = req.prompt
                    elif "prompt" in inputs:
                        inputs["prompt"] = req.prompt
                elif "negative" in meta_title and req.negative_prompt:
                    inputs["text"] = req.negative_prompt

            # KSampler parameters injection
            if cls in ["KSampler"]:
                if req.seed is not None:
                    inputs["seed"] = req.seed
                if req.steps is not None:
                    inputs["steps"] = req.steps
                if req.cfg is not None:
                    inputs["cfg"] = req.cfg

            # Dimensions injection
            if cls in ["EmptyLTXVLatentVideo", "EmptyQwenImageLayeredLatentImage", "WanSoundImageToVideo"]:
                if req.width is not None and "width" in inputs:
                    inputs["width"] = req.width
                if req.height is not None and "height" in inputs:
                    inputs["height"] = req.height

        # 3. Submit workflow to local ComfyUI instance
        client_id = f"hermes_agent_{int(time.time())}"
        payload = json.dumps({"prompt": workflow, "client_id": client_id}).encode("utf-8")
        
        prompt_req = urllib.request.Request(
            "http://127.0.0.1:8188/prompt",
            data=payload,
            headers={"Content-Type": "application/json"}
        )
        
        with urllib.request.urlopen(prompt_req, timeout=10) as resp:
            submit_res = json.loads(resp.read().decode())

        prompt_id = submit_res.get("prompt_id")
        print(f"[ComfyUI] Submitted job prompt_id: {prompt_id}")

        return {
            "success": True,
            "template": req.template,
            "prompt_id": prompt_id,
            "status": "queued_or_executing",
            "message": "Workflow dispatched successfully into ComfyUI Serverless Graph Engine",
            "history_url": f"http://127.0.0.1:8188/history/{prompt_id}",
        }
