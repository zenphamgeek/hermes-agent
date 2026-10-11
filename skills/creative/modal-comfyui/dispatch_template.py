#!/usr/bin/env python3
"""
skills/creative/modal-comfyui/dispatch_template.py
==================================================
Hermes Agent - Dispatch ComfyUI Template JSON Workflows to Local, Modal, or Cloud GPU.

Supported Templates:
  1. wan22_s2v_14b_api.json  - Wan2.2 S2V (Speech to Video 14B)
  2. ltx_video_25_api.json   - LTX-Video-2.5 (22B Cinema Video DiT)
  3. qwen_image_21_api.json  - Qwen-Image-2.1 (7B Single-Stream DiT)

Usage:
  # Local ComfyUI (ThinkPad P15 Quadro RTX 5000)
  python3 dispatch_template.py --template wan22_s2v_14b --prompt "A scholar explaining AI" --audio voice.wav --output output/s2v.mp4

  # Modal GPU Serverless (A100-80GB)
  python3 dispatch_template.py --host https://mojopham--hermes-comfyui-engine-web-ui.modal.run \
      --template ltx_video_25 --prompt "Cyberpunk city 8k" --output output/ltx.mp4
"""

import os
import sys
import json
import time
import argparse
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Dict, Any, Optional

WORKFLOWS_DIR = Path(__file__).resolve().parent.parent / "comfyui" / "workflows"


def load_template(template_name: str) -> Dict[str, Any]:
    """Finds and loads the template JSON from workflows directory."""
    candidates = []
    if template_name.endswith(".json"):
        candidates.append(template_name)
    else:
        candidates.extend([
            f"{template_name}.json",
            f"{template_name}_production.json",
            f"{template_name}_api.json",
        ])

    for cand in candidates:
        template_path = WORKFLOWS_DIR / cand
        if template_path.exists():
            with open(template_path, "r", encoding="utf-8") as f:
                return json.load(f)
        alt_path = Path(__file__).resolve().parent / "workflows" / cand
        if alt_path.exists():
            with open(alt_path, "r", encoding="utf-8") as f:
                return json.load(f)

    raise FileNotFoundError(
        f"Workflow template '{template_name}' not found. Searched candidates: {candidates} in {WORKFLOWS_DIR}"
    )


def list_templates() -> Dict[str, Dict[str, Any]]:
    """Discovers all available templates in WORKFLOWS_DIR with their metadata."""
    templates = {}
    if not WORKFLOWS_DIR.exists():
        return templates
    for f in sorted(WORKFLOWS_DIR.glob("*.json")):
        try:
            with open(f, "r", encoding="utf-8") as fp:
                data = json.load(fp)
                meta = data.get("_meta", {})
                templates[f.stem] = {
                    "file": f.name,
                    "title": meta.get("title", f.stem),
                    "description": meta.get("description", "No description provided"),
                    "model": meta.get("model", "Unknown"),
                    "aspect_ratio": meta.get("aspect_ratio", "N/A"),
                    "tier": meta.get("tier", meta.get("hardware_recommendation", "Standard GPU")),
                }
        except Exception:
            continue
    return templates


def inject_parameters(
    workflow: Dict[str, Any],
    prompt: Optional[str] = None,
    negative_prompt: Optional[str] = None,
    audio_path: Optional[str] = None,
    image_path: Optional[str] = None,
    seed: Optional[int] = None,
    width: Optional[int] = None,
    height: Optional[int] = None,
    steps: Optional[int] = None,
    cfg: Optional[float] = None,
) -> Dict[str, Any]:
    """Injects user arguments into node inputs across the workflow graph."""
    for node_id, node in workflow.items():
        if not isinstance(node, dict) or "class_type" not in node:
            continue

        inputs = node.get("inputs", {})
        cls = node.get("class_type", "")
        title = node.get("_meta", {}).get("title", "").lower()

        # Text prompt
        if cls in ["CLIPTextEncode", "TextEncodeQwenImageEdit"]:
            if "negative" not in title and prompt:
                if "text" in inputs:
                    inputs["text"] = prompt
                elif "prompt" in inputs:
                    inputs["prompt"] = prompt
            elif "negative" in title and negative_prompt:
                inputs["text"] = negative_prompt

        # Image & Audio file paths
        if cls == "LoadAudio" and audio_path:
            inputs["audio"] = os.path.basename(audio_path)
        if cls == "LoadImage" and image_path:
            inputs["image"] = os.path.basename(image_path)

        # Sampler & Face Restoration parameters
        if cls in ["KSampler", "SamplerCustom", "FaceDetailer"]:
            if seed is not None and "seed" in inputs:
                inputs["seed"] = seed
            if steps is not None and "steps" in inputs:
                inputs["steps"] = steps
            if cfg is not None and "cfg" in inputs:
                inputs["cfg"] = cfg

        # Video FPS
        if cls == "CreateVideo":
            if "fps" in inputs and hasattr(sys.modules.get(__name__), "fps") and getattr(sys.modules.get(__name__), "fps", None):
                inputs["fps"] = getattr(sys.modules.get(__name__), "fps")

        # Dimensions
        if cls in ["EmptyLTXVLatentVideo", "EmptyQwenImageLayeredLatentImage", "WanSoundImageToVideo"]:
            if width is not None and "width" in inputs:
                inputs["width"] = width
            if height is not None and "height" in inputs:
                inputs["height"] = height

    return workflow


def submit_workflow(host: str, workflow: Dict[str, Any]) -> str:
    """Submits workflow JSON to ComfyUI REST API and returns prompt_id."""
    url = f"{host.rstrip('/')}/prompt"
    client_id = f"hermes_dispatch_{int(time.time())}"
    # Strip any _meta tags before submitting to ComfyUI REST endpoint
    clean_prompt = {k: v for k, v in workflow.items() if k != "_meta"}
    data = json.dumps({"prompt": clean_prompt, "client_id": client_id}).encode("utf-8")

    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            res = json.loads(resp.read().decode())
            return res["prompt_id"]
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode()
        try:
            parsed = json.loads(err_msg)
            print(f"\n❌ ComfyUI Rejection ({e.code}):\n{json.dumps(parsed, indent=2)}")
        except Exception:
            print(f"\n❌ ComfyUI HTTP {e.code} Error:\n{err_msg}")
        raise RuntimeError(f"ComfyUI submission failed with status {e.code}") from e


def poll_output(host: str, prompt_id: str, timeout_sec: int = 600) -> Dict[str, Any]:
    """Polls ComfyUI /history/{prompt_id} until execution is complete."""
    start = time.time()
    url = f"{host.rstrip('/')}/history/{prompt_id}"

    print(f"⏳ Waiting for ComfyUI generation (prompt_id: {prompt_id})...")
    while time.time() - start < timeout_sec:
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
                if prompt_id in data:
                    item = data[prompt_id]
                    status = item.get("status", {})
                    if status.get("completed", False):
                        print("✅ Generation completed successfully!")
                        return item.get("outputs", {})
                    elif status.get("status_str") == "error":
                        raise RuntimeError(f"ComfyUI execution error: {status.get('messages')}")
        except Exception as e:
            if "ComfyUI execution error" in str(e):
                raise
        time.sleep(3.0)

    raise TimeoutError(f"Generation timed out after {timeout_sec}s")


def main():
    parser = argparse.ArgumentParser(description="Hermes Agent ComfyUI Template Dispatcher")
    parser.add_argument("--host", default="http://127.0.0.1:8188", help="ComfyUI host URL (local or Modal)")
    parser.add_argument("--template", help="Template name (e.g. wan22_s2v_talking_avatar, wan22_s2v_shorts_vertical, ltx_video_25, qwen_image_21)")
    parser.add_argument("--list-templates", action="store_true", help="List all available production and API templates")
    parser.add_argument("--prompt", help="Positive prompt")
    parser.add_argument("--negative-prompt", help="Negative prompt")
    parser.add_argument("--audio", help="Path to input audio (for Wan S2V)")
    parser.add_argument("--image", help="Path to input image (portrait or reference)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--width", type=int, help="Render width")
    parser.add_argument("--height", type=int, help="Render height")
    parser.add_argument("--steps", type=int, help="Diffusion sampling steps")
    parser.add_argument("--output", help="Output destination file")
    args = parser.parse_args()

    if args.list_templates:
        all_tpls = list_templates()
        print("================================================================================")
        print(f" 🎨 HERMES COMFYUI PRODUCTION TEMPLATES ({len(all_tpls)} registered)")
        print("================================================================================")
        for name, info in all_tpls.items():
            print(f" ▶ [{name}]")
            print(f"   Title  : {info['title']}")
            print(f"   Model  : {info['model']} | Aspect: {info['aspect_ratio']} | Tier: {info['tier']}")
            print(f"   Desc   : {info['description']}\n")
        return

    if not args.template:
        parser.error("--template is required unless --list-templates is provided.")

    print(f"📦 Loading template: {args.template}...")
    wf = load_template(args.template)

    print("🔧 Injecting parameters into graph...")
    wf = inject_parameters(
        wf,
        prompt=args.prompt,
        negative_prompt=args.negative_prompt,
        audio_path=args.audio,
        image_path=args.image,
        seed=args.seed,
        width=args.width,
        height=args.height,
        steps=args.steps,
    )

    print(f"🚀 Submitting job to ComfyUI host: {args.host}...")
    prompt_id = submit_workflow(args.host, wf)
    print(f"📋 Job queued. Prompt ID: {prompt_id}")

    outputs = poll_output(args.host, prompt_id)
    print("🎉 Outputs received:", list(outputs.keys()))


if __name__ == "__main__":
    main()
