"""
scripts/onboarding_quality_gate.py
==================================
Mandatory Onboarding Quality Gate for Modal Fleet Infrastructure.
Enforces invariant standards across:
1. WorkerGPUOnboardingGate: Hardware Tier enum, Canonical 20 Workspaces, HTTPS ASGI URLs.
2. ModelArchitectureGate: DiT Architecture Types, VAE Tiling, Modal Cache Volume Mounts.
3. TemplateLifecycleGate: UTF-8 BOM Decoding, Kahn's Topological Sort (0 cycles),
   0 Dangling Links, Content-Addressable SHA-256 Versioning, Dynamic AST Parameter Schema.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse


# =============================================================================
# 1. Worker GPU Onboarding Gate
# =============================================================================

class WorkerGPUOnboardingGate:
    """
    Quality gate validating Worker GPU additions to the Modal Fleet.
    Enforces hardware tier enum, canonical 20 workspace profiles, and HTTPS ASGI endpoints.
    """

    HARDWARE_TIERS: List[str] = [
        "NVIDIA A100-80GB HBM2e",
        "NVIDIA T4 GPU",
        "Local ThinkPad P15 Quadro RTX 5000",
        "CPU Serverless",
    ]

    CANONICAL_20_PROFILES: List[str] = [
        # Group 1: just.ask.mr.zen@gmail.com (5)
        "just-ask-mr-zen", "zenpeace", "mindful", "zenguru", "zenmaster",
        # Group 2: nhatrophamvu@gmail.com (5)
        "asmr", "nhatrophamvu", "vi2vi", "pvvsf", "phi4",
        # Group 3: mojopham@gmail.com (5)
        "diatts", "mojopham", "mvlm", "motion", "vrag",
        # Group 4: zenonmind@gmail.com (5)
        "lovenovel", "vieturbo", "zenonmind", "insimind", "zenonts",
    ]

    def validate_hardware_tier(self, tier: str) -> bool:
        if tier not in self.HARDWARE_TIERS:
            raise ValueError(
                f"Invalid Hardware Tier '{tier}'. Must be one of: {self.HARDWARE_TIERS}"
            )
        return True

    def validate_workspace_profile(self, profile: str) -> bool:
        if profile not in self.CANONICAL_20_PROFILES:
            raise ValueError(
                f"Invalid Workspace Profile '{profile}'. Must be one of canonical 20 profiles: {self.CANONICAL_20_PROFILES}"
            )
        return True

    def validate_asgi_url(self, url: str) -> bool:
        if not isinstance(url, str) or not url.strip():
            raise ValueError(f"ASGI URL must be a non-empty string, got {type(url)}")
        parsed = urlparse(url)
        if parsed.scheme == "https" and parsed.netloc:
            return True
        if parsed.scheme == "http" and parsed.hostname in ("localhost", "127.0.0.1", "0.0.0.0"):
            return True
        raise ValueError(
            f"Invalid ASGI URL '{url}'. Remote Modal workers must expose an HTTPS ASGI URL (or http://localhost for local workstation)."
        )

    def validate_worker(self, worker_def: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validates a worker dictionary containing:
        - hardware_tier (or tier)
        - workspace_profile (or workspace)
        - asgi_url (or endpoint_url / url)
        Returns validated worker report or raises ValueError.
        """
        tier = worker_def.get("hardware_tier") or worker_def.get("tier")
        profile = worker_def.get("workspace_profile") or worker_def.get("workspace")
        url = worker_def.get("asgi_url") or worker_def.get("endpoint_url") or worker_def.get("url")

        errors: List[str] = []
        if not tier:
            errors.append("Missing hardware_tier")
        else:
            try:
                self.validate_hardware_tier(tier)
            except ValueError as e:
                errors.append(str(e))

        if not profile:
            errors.append("Missing workspace_profile")
        else:
            try:
                self.validate_workspace_profile(profile)
            except ValueError as e:
                errors.append(str(e))

        if not url:
            errors.append("Missing asgi_url")
        else:
            try:
                self.validate_asgi_url(url)
            except ValueError as e:
                errors.append(str(e))

        if errors:
            raise ValueError(f"Worker GPU Onboarding Gate Failed: {'; '.join(errors)}")

        return {
            "valid": True,
            "hardware_tier": tier,
            "workspace_profile": profile,
            "asgi_url": url,
            "status": "APPROVED",
        }


# =============================================================================
# 2. Model Architecture Gate
# =============================================================================

class ModelArchitectureGate:
    """
    Quality gate validating Model Architecture definitions.
    Enforces DiT type (Flow Matching DiT, Single-Stream DiT), VAE tiling declaration,
    and Modal cache volume mounts.
    """

    VALID_DIT_TYPES: List[str] = [
        "Flow Matching DiT",
        "Single-Stream DiT",
    ]

    VALID_CACHE_VOLUMES: List[str] = [
        "hermes-comfyui-cache",
        "hermes-wan-s2v-cache",
        "hermes-ltx-cache",
    ]

    def validate_dit_type(self, dit_type: str) -> bool:
        if dit_type not in self.VALID_DIT_TYPES:
            raise ValueError(
                f"Invalid DiT type '{dit_type}'. Must be one of: {self.VALID_DIT_TYPES}"
            )
        return True

    def validate_vae_tiling(self, vae_tiling: Any) -> bool:
        if isinstance(vae_tiling, bool):
            if not vae_tiling:
                raise ValueError("VAE tiling must be enabled (vae_tiling=True) to prevent GPU OOM on high-resolution latents.")
            return True
        if isinstance(vae_tiling, dict):
            if not vae_tiling.get("enabled", True):
                raise ValueError("VAE tiling configuration must have enabled=True.")
            return True
        if isinstance(vae_tiling, str) and vae_tiling.lower() in ("enabled", "true", "3d_vae_tiling", "tiling_and_slicing"):
            return True
        raise ValueError(f"Invalid VAE tiling declaration: {vae_tiling}. Must declare enabled VAE tiling.")

    def validate_cache_volume(self, volume_name: str) -> bool:
        if volume_name not in self.VALID_CACHE_VOLUMES:
            raise ValueError(
                f"Invalid Modal cache volume mount '{volume_name}'. Must be one of: {self.VALID_CACHE_VOLUMES}"
            )
        return True

    def validate_model(self, model_def: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validates model architecture definition:
        - model_name / name
        - dit_type / architecture
        - vae_tiling
        - cache_volume / volume_mount
        """
        model_name = model_def.get("model_name") or model_def.get("name", "Unknown")
        dit_type = model_def.get("dit_type") or model_def.get("architecture")
        vae_tiling = model_def.get("vae_tiling")
        volume = model_def.get("cache_volume") or model_def.get("volume_mount") or model_def.get("volume")

        errors: List[str] = []
        if not dit_type:
            errors.append("Missing dit_type / architecture definition")
        else:
            try:
                self.validate_dit_type(dit_type)
            except ValueError as e:
                errors.append(str(e))

        if vae_tiling is None:
            errors.append("Missing vae_tiling declaration")
        else:
            try:
                self.validate_vae_tiling(vae_tiling)
            except ValueError as e:
                errors.append(str(e))

        if not volume:
            errors.append("Missing cache_volume mount definition")
        else:
            try:
                self.validate_cache_volume(volume)
            except ValueError as e:
                errors.append(str(e))

        if errors:
            raise ValueError(f"Model Architecture Gate Failed for '{model_name}': {'; '.join(errors)}")

        return {
            "valid": True,
            "model_name": model_name,
            "dit_type": dit_type,
            "vae_tiling": vae_tiling,
            "cache_volume": volume,
            "status": "APPROVED",
        }


# =============================================================================
# 3. Template Lifecycle Gate
# =============================================================================

class TemplateLifecycleGate:
    """
    Quality gate validating ComfyUI Workflow JSON templates.
    Enforces UTF-8 BOM safe decoding, Kahn's Topological Sort (0 cycles),
    0 dangling link references, content-addressable SHA-256 versioning,
    and dynamic AST parameter schema extraction.
    """

    def __init__(self, workflows_dir: Optional[Union[str, Path]] = None):
        self.workflows_dir = (
            Path(workflows_dir)
            if workflows_dir
            else Path("/home/zen/hermes-agent/skills/creative/comfyui/workflows")
        )
        self.version_registry: Dict[str, List[Dict[str, Any]]] = {}

    def decode_workflow_bytes(self, raw_bytes: bytes) -> Dict[str, Any]:
        """Safely decodes raw workflow bytes with UTF-8 BOM handling."""
        try:
            decoded_text = raw_bytes.decode("utf-8-sig")
            data = json.loads(decoded_text)
            if not isinstance(data, dict):
                raise ValueError("Workflow JSON root must be an object dictionary.")
            return data
        except Exception as e:
            raise ValueError(f"UTF-8 BOM / JSON decoding failure: {e}")

    def extract_graph_nodes(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extracts node dictionary, excluding top-level metadata and non-dict keys."""
        if "prompt" in raw_data and isinstance(raw_data["prompt"], dict) and any("class_type" in v for v in raw_data["prompt"].values() if isinstance(v, dict)):
            source = raw_data["prompt"]
        else:
            source = raw_data
        nodes = {str(k): v for k, v in source.items() if not str(k).startswith("_") and isinstance(v, dict)}
        return nodes

    def run_kahns_topological_sort(
        self, nodes: Dict[str, Any], raise_on_cycle: bool = True
    ) -> Dict[str, Any]:
        """
        Executes Kahn's algorithm for topological ordering, cycle detection, and dangling link detection.
        Raises ValueError if raise_on_cycle=True and cycles > 0 or dangling links > 0.
        """
        clean_nodes = {str(k): v for k, v in nodes.items() if isinstance(v, dict) and not str(k).startswith("_")}
        adj: Dict[str, List[str]] = {nid: [] for nid in clean_nodes}
        in_degree: Dict[str, int] = {nid: 0 for nid in clean_nodes}
        dangling_links = 0
        dangling_details: List[Dict[str, Any]] = []

        for nid, node in clean_nodes.items():
            inputs = node.get("inputs", {}) if isinstance(node, dict) else {}
            for param_name, param_val in inputs.items():
                if isinstance(param_val, list) and len(param_val) == 2:
                    src_id = str(param_val[0])
                    if src_id in clean_nodes:
                        adj[src_id].append(nid)
                        in_degree[nid] += 1
                    else:
                        dangling_links += 1
                        dangling_details.append({
                            "node_id": nid,
                            "param": param_name,
                            "missing_source": src_id,
                        })

        queue = [nid for nid in clean_nodes if in_degree[nid] == 0]
        visited_order: List[str] = []

        while queue:
            u = queue.pop(0)
            visited_order.append(u)
            for v in adj[u]:
                in_degree[v] -= 1
                if in_degree[v] == 0:
                    queue.append(v)

        cycles_count = len(clean_nodes) - len(visited_order)
        cycle_nodes = [nid for nid, deg in in_degree.items() if deg > 0]
        dag_valid = (cycles_count == 0) and (dangling_links == 0)

        if raise_on_cycle:
            if cycles_count > 0:
                raise ValueError(
                    f"Cycle detected in ComfyUI graph: {cycles_count} cycle nodes: {cycle_nodes}"
                )
            if dangling_links > 0:
                raise ValueError(
                    f"Dangling link references detected: {dangling_links} missing nodes: {dangling_details}"
                )

        return {
            "dag_valid": dag_valid,
            "cycles": cycles_count,
            "dangling_links": dangling_links,
            "visited_count": len(visited_order),
            "total_nodes": len(clean_nodes),
            "topological_order": visited_order,
            "cycle_nodes": cycle_nodes,
            "dangling_details": dangling_details,
        }

    def generate_parameter_schema(
        self, nodes: Dict[str, Any], template_id: str = ""
    ) -> Dict[str, Any]:
        """
        Extracts dynamic AST parameter schema detecting:
        - prompt / negative_prompt from CLIPTextEncode / WanVideoTextEncode
        - seed, steps, cfg from KSampler / BasicScheduler / etc.
        - width, height from EmptyLatentImage / EmptyLTXVLatentVideo / etc.
        - audio conditioning from LoadAudio / WanSoundImageToVideo
        - image conditioning from LoadImage / LoadImageMask / WanImageToVideo
        """
        clean_nodes = {str(k): v for k, v in nodes.items() if isinstance(v, dict) and not str(k).startswith("_")}
        schema: Dict[str, Any] = {}
        classes = {v.get("class_type", "") for v in clean_nodes.values()}

        default_prompt = ""
        default_negative = ""
        for nid, node in clean_nodes.items():
            cls = node.get("class_type", "")
            title = node.get("_meta", {}).get("title", "").lower()
            inputs = node.get("inputs", {})
            if cls in ["CLIPTextEncode", "TextEncodeQwenImageEdit", "WanVideoTextEncode"]:
                txt = inputs.get("text") or inputs.get("prompt") or ""
                if isinstance(txt, str):
                    if "negative" in title or "neg" in cls.lower():
                        default_negative = default_negative or txt
                    else:
                        default_prompt = default_prompt or txt

        schema["prompt"] = {
            "type": "string",
            "description": "Primary guiding prompt for synthesis",
            "required": True,
            "default": default_prompt or "Cinematic visual scene, 8k resolution, photorealistic",
        }
        schema["negative_prompt"] = {
            "type": "string",
            "description": "Negative guidance prompt to suppress artifacts",
            "required": False,
            "default": default_negative or "blurry, low quality, distorted, artifacting",
        }

        # Sampling parameters
        schema["seed"] = {
            "type": "integer",
            "description": "Random seed for reproducible synthesis",
            "default": 42,
        }
        schema["steps"] = {
            "type": "integer",
            "description": "Sampling iteration steps",
            "default": 30,
        }
        schema["cfg"] = {
            "type": "float",
            "description": "Classifier-Free Guidance scale",
            "default": 5.0,
        }

        # Latent dimensions
        width = 1024
        height = 704
        for node in clean_nodes.values():
            inputs = node.get("inputs", {})
            if (
                "width" in inputs
                and "height" in inputs
                and isinstance(inputs["width"], (int, float))
            ):
                width = int(inputs["width"])
                height = int(inputs["height"])
                break
        schema["width"] = {
            "type": "integer",
            "description": "Base latent width in pixels",
            "default": width,
        }
        schema["height"] = {
            "type": "integer",
            "description": "Base latent height in pixels",
            "default": height,
        }

        # Audio conditioning detection (AST node classes and inputs)
        has_audio = (
            any(c in ["LoadAudio", "WanSoundImageToVideo"] for c in classes)
            or any("audio" in v.get("inputs", {}) for v in clean_nodes.values())
            or "s2v" in template_id
            or "audio" in template_id
            or "avatar" in template_id
        )
        if has_audio:
            schema["audio"] = {
                "type": "string",
                "description": "Audio voiceover path (.wav, 48kHz Stereo, EBU R128 -14.5 LUFS)",
                "required": True,
                "default": "assets/audio/voiceover.wav",
            }

        # Image conditioning detection (AST node classes and inputs)
        has_image = (
            any(
                c in ["LoadImage", "LoadImageMask", "WanSoundImageToVideo", "WanImageToVideo"]
                for c in classes
            )
            or any("image" in v.get("inputs", {}) for v in clean_nodes.values())
            or "s2v" in template_id
            or "image" in template_id
            or "img2img" in template_id
            or "inpaint" in template_id
            or "upscale" in template_id
            or "avatar" in template_id
        )
        if has_image:
            schema["image"] = {
                "type": "string",
                "description": "Source portrait or conditioning image path (.png/.jpg)",
                "required": True,
                "default": "assets/portraits/anchor.png",
            }

        return schema

    def validate_template_file(
        self, file_path: Union[str, Path], update_registry: bool = True
    ) -> Dict[str, Any]:
        """Full gate lifecycle validation for a template file."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Template file not found: {path}")

        raw_bytes = path.read_bytes()
        file_sha256 = hashlib.sha256(raw_bytes).hexdigest()
        data = self.decode_workflow_bytes(raw_bytes)

        nodes = self.extract_graph_nodes(data)
        if not nodes:
            raise ValueError(f"Template {path.name} contains no valid graph nodes.")

        dag_res = self.run_kahns_topological_sort(nodes, raise_on_cycle=True)
        schema = self.generate_parameter_schema(nodes, template_id=path.stem)

        mtime = os.path.getmtime(path)
        record = {
            "sha256": file_sha256,
            "filename": path.name,
            "template_id": path.stem,
            "nodes_count": len(nodes),
            "mtime": mtime,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(mtime)),
            "status": "active",
            "dag_valid": dag_res["dag_valid"],
            "cycles": dag_res["cycles"],
            "dangling_links": dag_res["dangling_links"],
        }

        if update_registry:
            tid = path.stem
            if tid not in self.version_registry:
                self.version_registry[tid] = []
            if not any(r.get("sha256") == file_sha256 for r in self.version_registry[tid]):
                self.version_registry[tid].append(record)

        return {
            "valid": True,
            "template_id": path.stem,
            "sha256": file_sha256,
            "nodes_count": len(nodes),
            "dag": dag_res,
            "parameter_schema": schema,
            "record": record,
        }

    def validate_all_canonical_workflows(self) -> Dict[str, Any]:
        """Validates all 16 canonical workflows in skills/creative/comfyui/workflows/."""
        results: Dict[str, Any] = {}
        files = sorted(self.workflows_dir.glob("*.json"))
        if len(files) != 16:
            raise ValueError(f"Expected exactly 16 workflow files, found {len(files)}")

        for f in files:
            res = self.validate_template_file(f, update_registry=True)
            results[f.stem] = res

        return {
            "total_validated": len(results),
            "all_passed": True,
            "templates": results,
        }
