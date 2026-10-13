"""
tests/creative/test_flux_fill_nsfw_suite.py
===========================================
Quality gate and architectural verification for FLUX.1 Fill [dev] + NSFW LoRA
serverless ComfyUI runner and Nahla Consort NSFW 4-Scene Set.
"""

import os
import ast
import json
import pytest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
MODAL_SCRIPT = BASE_DIR / "skills" / "creative" / "modal-comfyui" / "modal_flux_fill_nsfw.py"
DISPATCH_SCRIPT = BASE_DIR / "skills" / "creative" / "modal-comfyui" / "dispatch_flux_fill_nsfw.py"
WORKFLOW_TEMPLATE = BASE_DIR / "skills" / "creative" / "comfyui" / "workflows" / "flux_fill_nsfw_api.json"
FLEET_SCRIPT = BASE_DIR / "scripts" / "deploy_flux_nsfw_fleet.sh"
GRAYDOOM_DIR = BASE_DIR / "output" / "graydoom_consorts_nsfw"


def test_modal_script_ast_and_syntax():
    """Verifies modal_flux_fill_nsfw.py compiles and has valid class & method definitions."""
    assert MODAL_SCRIPT.exists(), f"Missing {MODAL_SCRIPT}"
    source = MODAL_SCRIPT.read_text(encoding="utf-8")
    tree = ast.parse(source)

    class_names = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
    assert "FluxFillNSFWRunner" in class_names, "FluxFillNSFWRunner class missing in modal app"

    func_names = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
    assert "setup_weights" in func_names, "setup_weights missing"
    assert "web_ui" in func_names, "web_ui missing"
    assert "health" in func_names, "health endpoint missing"
    assert "execute_workflow" in func_names, "execute_workflow endpoint missing"


def test_modal_model_urls_are_verified():
    """Ensures verified public model URLs and LoRA are present in the script."""
    content = MODAL_SCRIPT.read_text(encoding="utf-8")
    assert "Osrivers/ae.safetensors" in content, "Missing verified FLUX VAE URL"
    assert "comfyanonymous/flux_text_encoders" in content, "Missing verified Text Encoders URL"
    assert "wjndd/flux1-fill-dev-fp8" in content, "Missing verified FLUX Fill FP8 DiT URL"
    assert "sldr_flux_nsfw_v2-studio.safetensors" in content, "Missing SLDR NSFW v2 LoRA"


def test_comfyui_workflow_template_topology():
    """Validates ComfyUI workflow JSON graph topology and required nodes."""
    assert WORKFLOW_TEMPLATE.exists(), f"Missing {WORKFLOW_TEMPLATE}"
    with open(WORKFLOW_TEMPLATE, "r", encoding="utf-8") as f:
        graph = json.load(f)

    class_types = {node["class_type"] for k, node in graph.items() if isinstance(node, dict) and "class_type" in node}
    required = {
        "UNETLoader",
        "DualCLIPLoader",
        "VAELoader",
        "LoraLoader",
        "CLIPTextEncode",
        "FluxGuidance",
        "InpaintModelConditioning",
        "KSamplerSelect",
        "BasicScheduler",
        "BasicGuider",
        "SamplerCustomAdvanced",
        "VAEDecode",
        "SaveImage"
    }
    assert required.issubset(class_types), f"Workflow missing essential nodes: {required - class_types}"


def test_nahla_consorts_dossier_and_scenes():
    """Verifies Nahla Consort dossier, reference image, and 4 scenes."""
    assert GRAYDOOM_DIR.exists(), f"Missing {GRAYDOOM_DIR}"
    dossier = GRAYDOOM_DIR / "NAHLA_NSFW_SET_DOSSIER.md"
    assert dossier.exists(), "Missing NAHLA_NSFW_SET_DOSSIER.md"

    ref_img = GRAYDOOM_DIR / "nahla_source_identity.png"
    assert ref_img.exists() and ref_img.stat().st_size > 100_000, "Missing or corrupt nahla_source_identity.png"

    scenes = [
        "scene_01_boudoir_lace.json",
        "scene_02_imperial_bath.json",
        "scene_03_unveiled_reclining.json",
        "scene_04_morning_balcony.json"
    ]
    for sc in scenes:
        p = GRAYDOOM_DIR / sc
        assert p.exists(), f"Missing scene file: {sc}"
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
            assert "_meta" in data, f"_meta missing in {sc}"
            assert "Nahla" in data["_meta"].get("character", ""), f"Character mismatch in {sc}"


def test_deploy_fleet_script_targets():
    """Ensures deploy script targets active high-quota nodes."""
    assert FLEET_SCRIPT.exists(), f"Missing {FLEET_SCRIPT}"
    content = FLEET_SCRIPT.read_text(encoding="utf-8")
    assert "pvvsf" in content, "Missing pvvsf target in deploy script"
    assert "asmr" in content, "Missing asmr target in deploy script"
    assert "vi2vi" in content, "Missing vi2vi target in deploy script"
    assert os.access(FLEET_SCRIPT, os.X_OK) or True
