#!/usr/bin/env python3
"""
skills/creative/modal-comfyui/dispatch_flux_fill_nsfw.py
========================================================
Client dispatcher to submit generation/edit requests across the 3 FLUX NSFW Workers.
"""

import sys
import os
import json
import time
import argparse
import urllib.request
import urllib.parse
from pathlib import Path

# The 3 deployed worker endpoints on verified active nodes
WORKER_POOLS = {
    "worker-1": "https://pvvsf--hermes-flux-fill-nsfw-fluxfillnsfwrunner-web-ui.modal.run",
    "worker-2": "https://asmr--hermes-flux-fill-nsfw-fluxfillnsfwrunner-web-ui.modal.run",
    "worker-3": "https://vi2vi--hermes-flux-fill-nsfw-fluxfillnsfwrunner-web-ui.modal.run",
}

WORKFLOW_TEMPLATE = Path(__file__).resolve().parent.parent / "comfyui" / "workflows" / "flux_fill_nsfw_api.json"


def select_healthy_worker() -> str:
    """Probes all 3 workers and returns the first healthy/available worker endpoint."""
    for name, host in WORKER_POOLS.items():
        try:
            req = urllib.request.Request(f"{host}/system_stats", headers={"User-Agent": "Hermes-Client"})
            with urllib.request.urlopen(req, timeout=3) as resp:
                if resp.status == 200:
                    print(f"🎯 Selected active worker: {name} ({host})")
                    return host
        except Exception:
            continue
    # Default to worker-1 if cold start
    return list(WORKER_POOLS.values())[0]


def main():
    parser = argparse.ArgumentParser(description="Dispatch FLUX.1 Fill NSFW task to Modal ComfyUI Cluster")
    parser.add_argument("--prompt", type=str, required=True, help="Positive prompt / edit instructions")
    parser.add_argument("--image", type=str, default=None, help="Input image path for editing")
    parser.add_argument("--output", type=str, default="output/flux_fill_result.png", help="Output image file path")
    parser.add_argument("--worker", type=str, choices=["worker-1", "worker-2", "worker-3", "auto"], default="auto")
    parser.add_argument("--steps", type=int, default=24, help="Sampling steps")
    parser.add_argument("--guidance", type=float, default=3.5, help="Flux guidance")
    args = parser.parse_args()

    if args.worker == "auto":
        host = select_healthy_worker()
    else:
        host = WORKER_POOLS[args.worker]

    print(f"🚀 Dispatching task to {host}...")

    # Load workflow template
    with open(WORKFLOW_TEMPLATE, "r", encoding="utf-8") as f:
        workflow = json.load(f)

    # Inject prompt and parameters
    for node_id, node in workflow.items():
        if not isinstance(node, dict) or "class_type" not in node:
            continue
        if node.get("class_type") == "CLIPTextEncode" and "positive" in node.get("_meta", {}).get("title", "").lower():
            node["inputs"]["text"] = args.prompt
        if node.get("class_type") == "FluxGuidance":
            node["inputs"]["guidance"] = args.guidance
        if node.get("class_type") == "BasicScheduler":
            node["inputs"]["steps"] = args.steps

    # Submit to ComfyUI /prompt
    clean_graph = {k: v for k, v in workflow.items() if k != "_meta"}
    payload = json.dumps({"prompt": clean_graph, "client_id": f"hermes_{int(time.time())}"}).encode("utf-8")

    req = urllib.request.Request(
        f"{host}/prompt",
        data=payload,
        headers={"Content-Type": "application/json"}
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
            print(f"✅ Submitted successfully! Prompt ID: {data.get('prompt_id')}")
    except Exception as e:
        print(f"⚠️ Error dispatching request: {e}")
        print(f"👉 You can also open the Web GUI directly at: {host}")


if __name__ == "__main__":
    main()
