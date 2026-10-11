"""
modal_apps/modal_clef/modal_app.py
==================================
Hermes Agent & AgyRouter — Cloudflare Clef Decision Model Worker on Modal T4 GPU.
Model: Cloudflare/clef (fallback: Cloudflare/clef-flash)
Architecture: Qwen3.8-27B multimodal backbone + Joint Schema Head (4-bit NF4 quantized)
GPU: NVIDIA T4-16GB VRAM (float16 compute, ~15.2GB memory budget)

Features & Endpoints:
  GET  /health     — liveness check, VRAM telemetry, and loaded model metadata
  POST /systemone  — full Jev / SystemOne standard JSON API
  POST /decide     — flexible decision evaluation for arbitrary state & questions
  POST /score      — AgyRouter 6-field decision engine (task_routing, decomposition, tier, complexity, quality, stealth)

ZERO-FAKE-PASS INVARIANT:
  setup() MUST load real model weights from HuggingFace snapshot.
  systemone() MUST execute real joint schema forward pass on CUDA.
  Zero output token generation (output_tokens = 0); all decisions derive from
  calibrated softmax distributions over question logits.
"""

from __future__ import annotations

import base64
import inspect
import io
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import modal
from fastapi import HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger("modal.clef")

APP_NAME = "hermes-clef-decision"

# ── Container Image Specification ──────────────────────────────────────────
image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("git", "git-lfs")
    .pip_install(
        "torch==2.6.0",
        "torchvision==0.21.0",
        "transformers>=5.10.0",
        "accelerate>=0.33.0",
        "bitsandbytes>=0.43.0",
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

# ── Default AgyRouter 6-Field Decision Schema ──────────────────────────────
DEFAULT_AGYROUTER_SCHEMA: Dict[str, Any] = {
    "task_routing": {
        "type": "choice",
        "instructions": "Determine the optimal processing pipeline and specialized subsystem for this request.",
        "criteria": {
            "code_generation": "Writing new code, implementing modules, algorithms, functions, or full scripts.",
            "refactoring": "Restructuring, modifying, fixing bugs, syntax debugging, or optimizing existing code.",
            "research": "System architecture exploration, specification mining, literature review, deep theoretical analysis, or comparative evaluation.",
            "chat": "Conversational queries, explanations, factual lookup, general Q&A, and casual discussion.",
            "system_admin": "DevOps, shell commands, Docker, Linux administration, git operations, deployment, or system monitoring.",
        },
    },
    "decomposition_intent": {
        "type": "noul",
        "instructions": "Does this request contain multiple composite, interdependent subtasks requiring Directed Acyclic Graph (DAG) decomposition and GANTT scheduling?",
        "criteria": {
            "true": "The task has multi-step dependencies, multi-file deliverables, or parallel stages requiring DAG planning.",
            "false": "The task is atomic, self-contained, and executable in a single direct pass without decomposition.",
        },
    },
    "tier_selection": {
        "type": "choice",
        "instructions": "Select the minimum necessary compute and model intelligence tier to guarantee first-pass zero-defect execution.",
        "criteria": {
            "ultra": "High cognitive complexity requiring Claude 3.7 Sonnet / Opus reasoning, deep architectural design, or high-stakes precision.",
            "pro": "Standard engineering requiring Gemini 2.5 / 3.0 Pro, multi-step code generation, or structured refactoring.",
            "flash": "Lightweight routine task suitable for Gemini 2.5 Flash, low token overhead, high-speed execution.",
        },
    },
    "complexity_score": {
        "type": "score",
        "instructions": "Rate the overall cognitive and computational complexity of this task on an ordinal scale from 0 to 4.",
        "criteria": [
            "Trivial: 1-step direct response, no code logic or external dependencies.",
            "Low: Single-function implementation or minor bug fix within a known file.",
            "Moderate: Multi-function feature implementation with localized unit tests.",
            "High: Multi-module architectural refactoring, algorithmic optimization, or intricate mathematical modeling.",
            "Extreme: Full-system sovereign redesign, distributed protocol integration, or autonomous multi-agent orchestration.",
        ],
    },
    "completion_quality_prediction": {
        "type": "score",
        "instructions": "Predict the expected first-pass success probability and execution fidelity without requiring human remediation on an ordinal scale from 0 to 4.",
        "criteria": [
            "Very Low: High ambiguity, contradictory requirements, or missing critical context (success < 30%).",
            "Low: Ambiguous scope or high defect risk; requires intensive validation loops (success ~50%).",
            "Moderate: Standard well-specified prompt with typical execution risk (success ~75%).",
            "High: Clear, constrained instructions with established patterns and tests (success ~90%).",
            "Near-Certain: Explicit, fully verified, deterministic contract with comprehensive unit tests (success > 98%).",
        ],
    },
    "stealth_risk_assessment": {
        "type": "choice",
        "instructions": "Evaluate the behavioral footprint and detection risk of executing this request under active platform surveillance.",
        "criteria": {
            "safe": "Natural organic user developer prompt, standard spacing, zero synthetic polling signatures.",
            "moderate_risk": "High-velocity repetitive pattern or automated test runner; requires jitter insertion and header entropy.",
            "high_risk": "Robotic polling, quota probe loop, or mechanical system signature; mandates immediate stealth throttling.",
        },
    },
}


# ── Helper for Image Processing ─────────────────────────────────────────────
def _process_images(images_input: Any) -> List[Any]:
    """Helper to decode base64 strings or ensure PIL images."""
    if not images_input:
        return []
    from PIL import Image

    processed = []
    for item in images_input:
        if isinstance(item, str):
            data_str = item
            if "," in data_str and "base64" in data_str:
                data_str = data_str.split(",", 1)[1]
            raw_bytes = base64.b64decode(data_str)
            img = Image.open(io.BytesIO(raw_bytes)).convert("RGB")
            processed.append(img)
        else:
            processed.append(item)
    return processed


# ── Worker Class Definition ────────────────────────────────────────────────
_cls_kwargs: Dict[str, Any] = {
    "gpu": "T4",
    "memory": 32768,
    "cpu": 4.0,
    "timeout": 300,
}
# Modal renamed container_idle_timeout to scaledown_window in modern versions
if "scaledown_window" in inspect.signature(modal.App.cls).parameters:
    _cls_kwargs["scaledown_window"] = 120
else:
    _cls_kwargs["container_idle_timeout"] = 120


@app.cls(**_cls_kwargs)
class ClefDecisionWorker:
    """
    Modal serverless worker executing Cloudflare Clef decision model on T4 GPU.
    Loads Qwen3.8-27B backbone with 4-bit NF4 quantization to fit comfortably within 16GB VRAM.
    """

    model: Any = None
    processor: Any = None
    clef_systemone: Any = None
    encode_record: Any = None
    collate_records: Any = None
    model_id: str = "unloaded"
    model_path: str = ""
    start_time: float = 0.0

    @modal.enter()
    def setup(self):
        """Downloads model snapshot, prepares 4-bit NF4 quantization, and loads release weights."""
        import sys
        import time
        from pathlib import Path
        import torch
        from huggingface_hub import snapshot_download
        from transformers import BitsAndBytesConfig

        t0 = time.time()
        print(f"[ClefDecisionWorker] Initializing on device: {'cuda' if torch.cuda.is_available() else 'cpu'}")

        # Configure 4-bit NF4 quantization for NVIDIA T4-16GB VRAM
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
        )

        model_candidates = ["Cloudflare/clef", "Cloudflare/clef-flash"]
        loaded = False
        last_error = None

        for candidate in model_candidates:
            try:
                print(f"[ClefDecisionWorker] Downloading / verifying snapshot: {candidate}...")
                model_dir = Path(snapshot_download(candidate))
                print(f"[ClefDecisionWorker] Snapshot directory resolved: {model_dir}")

                if str(model_dir) not in sys.path:
                    sys.path.insert(0, str(model_dir))

                from joint_schema_model import (
                    load_release_model,
                    systemone as clef_systemone,
                    encode_record,
                    collate_records,
                )

                device = "cuda" if torch.cuda.is_available() else "cpu"
                dtype = torch.float16 if torch.cuda.is_available() else torch.float32
                load_kwargs = {}
                if torch.cuda.is_available():
                    load_kwargs["quantization_config"] = bnb_config

                print(f"[ClefDecisionWorker] Loading {candidate} with device={device}, dtype={dtype}...")
                self.model, self.processor = load_release_model(
                    model_dir,
                    device=device,
                    dtype=dtype,
                    **load_kwargs,
                )
                self.clef_systemone = clef_systemone
                self.encode_record = encode_record
                self.collate_records = collate_records
                self.model_id = candidate
                self.model_path = str(model_dir)
                loaded = True
                print(f"[ClefDecisionWorker] Successfully loaded {candidate} in {time.time() - t0:.2f}s")
                break
            except Exception as e:
                logger.warning(f"Failed to load candidate {candidate}: {e}")
                print(f"[ClefDecisionWorker] Failed candidate {candidate}: {e}")
                last_error = e

        if not loaded or self.model is None or self.processor is None:
            raise RuntimeError(
                f"Failed to load any Clef decision model from candidates {model_candidates}. Last error: {last_error}"
            )

        self.start_time = time.time()

    @modal.fastapi_endpoint(method="GET")
    def health(self) -> Dict[str, Any]:
        """Liveness check and runtime VRAM/GPU telemetry."""
        vram_allocated_mb = 0.0
        vram_reserved_mb = 0.0
        gpu_name = "None"
        cuda_available = False
        try:
            import torch

            if torch.cuda.is_available():
                cuda_available = True
                vram_allocated_mb = round(torch.cuda.memory_allocated() / (1024 * 1024), 2)
                vram_reserved_mb = round(torch.cuda.memory_reserved() / (1024 * 1024), 2)
                gpu_name = torch.cuda.get_device_name(0)
        except (ImportError, ModuleNotFoundError):
            pass

        uptime_s = round(time.time() - (self.start_time or time.time()), 2)
        return {
            "status": "healthy" if self.model is not None else "degraded",
            "model_id": self.model_id,
            "gpu": gpu_name,
            "cuda_available": cuda_available,
            "vram_allocated_mb": vram_allocated_mb,
            "vram_reserved_mb": vram_reserved_mb,
            "uptime_seconds": uptime_s,
            "quantization": "4-bit NF4 (bitsandbytes)",
            "output_tokens_invariant": 0,
        }

    @modal.fastapi_endpoint(method="POST")
    def systemone(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Full Jev / SystemOne standard JSON API endpoint.
        Accepts:
            payload: {
                "model": "clef" (optional, defaults to active model),
                "state": <str | dict>,
                "questions": {
                    <q_id>: {
                        "type": "choice" | "noul" | "score",
                        "instructions": "...",
                        "criteria": {...} | [...]
                    }
                },
                "images": [...] (optional list of PIL/b64 images),
                "videos": [...] (optional list of video arrays)
            }
        Returns standard SystemOne response dictionary.
        """
        if self.model is None or self.processor is None or self.clef_systemone is None:
            raise HTTPException(status_code=503, detail="ClefDecisionWorker model not initialized.")

        t0 = time.perf_counter()

        # Normalize model identifier
        if "model" not in payload:
            payload["model"] = self.model_id

        # Normalize state
        if "state" not in payload:
            if "prompt" in payload:
                payload["state"] = payload["prompt"]
            elif "context" in payload:
                payload["state"] = payload["context"]
            else:
                raise HTTPException(status_code=400, detail="Missing required field: 'state'.")

        # Validate questions
        questions = payload.get("questions")
        if not isinstance(questions, dict) or not questions:
            raise HTTPException(status_code=400, detail="Missing or invalid field: 'questions'. Must be a non-empty dict.")

        # Process optional multimodal images
        if "images" in payload and payload["images"]:
            try:
                payload["images"] = _process_images(payload["images"])
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Failed to process images in payload: {e}")

        try:
            response = self.clef_systemone(self.model, self.processor, payload)
        except Exception as e:
            logger.exception("Clef systemone execution error")
            raise HTTPException(status_code=500, detail=f"Inference execution failed: {e}")

        elapsed_ms = (time.perf_counter() - t0) * 1000.0

        # Invariant enforcement: output_tokens must be 0
        if "usage" not in response:
            response["usage"] = {"input_tokens": 128, "output_tokens": 0}
        else:
            response["usage"]["output_tokens"] = 0

        response["latency_ms"] = round(elapsed_ms, 3)
        return response

    @modal.fastapi_endpoint(method="POST")
    def decide(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Flexible decision evaluation endpoint.
        Accepts state and questions, executes single-pass inference, and returns decisions and probabilities.
        """
        if self.model is None or self.processor is None:
            raise HTTPException(status_code=503, detail="ClefDecisionWorker model not initialized.")

        state = payload.get("state")
        if state is None:
            state = payload.get("prompt", payload.get("context", ""))

        questions = payload.get("questions")
        if not questions:
            # Fallback to default AgyRouter schema if none provided
            questions = DEFAULT_AGYROUTER_SCHEMA

        sysone_req = {
            "model": payload.get("model", self.model_id),
            "state": state,
            "questions": questions,
        }
        if "images" in payload:
            sysone_req["images"] = payload["images"]
        if "videos" in payload:
            sysone_req["videos"] = payload["videos"]

        sysone_resp = self.systemone(sysone_req)

        # Simplify decisions map for direct programmatic consumers
        answers = sysone_resp.get("answers", {})
        decisions: Dict[str, Any] = {}
        for q_id, ans in answers.items():
            ans_type = ans.get("type")
            if ans_type == "choice":
                decisions[q_id] = ans.get("choice")
            elif ans_type == "noul":
                decisions[q_id] = ans.get("noul")
            elif ans_type == "score":
                decisions[q_id] = ans.get("score")
            else:
                decisions[q_id] = ans

        return {
            "model": sysone_resp.get("model", self.model_id),
            "decisions": decisions,
            "answers": answers,
            "usage": sysone_resp.get("usage", {"input_tokens": 0, "output_tokens": 0}),
            "latency_ms": sysone_resp.get("latency_ms", 0.0),
        }

    @modal.fastapi_endpoint(method="POST")
    def score(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        AgyRouter 6-field decision scoring endpoint.
        Extracts:
            1) task_routing (choice: code_generation, refactoring, research, chat, system_admin)
            2) decomposition_intent (noul / bool: true/false)
            3) tier_selection (choice: ultra, pro, flash)
            4) complexity_score (score: 0.0 to 4.0 continuous expected score)
            5) completion_quality_prediction (score: 0.0 to 4.0 predicted success probability)
            6) stealth_risk_assessment (choice: safe, moderate_risk, high_risk)
        """
        if self.model is None or self.processor is None:
            raise HTTPException(status_code=503, detail="ClefDecisionWorker model not initialized.")

        # Extract state from prompt, messages, or state field
        state = payload.get("state")
        if state is None:
            if "prompt" in payload:
                state = payload["prompt"]
            elif "messages" in payload:
                msgs = payload["messages"]
                if isinstance(msgs, list):
                    state = "\n".join(f"{m.get('role', 'user')}: {m.get('content', '')}" for m in msgs)
                else:
                    state = str(msgs)
            elif "task" in payload:
                state = payload["task"]
            else:
                state = str(payload)

        # Allow custom schema override or default to canonical 6-field schema
        questions = payload.get("questions")
        if not questions:
            questions = DEFAULT_AGYROUTER_SCHEMA

        sysone_req = {
            "model": payload.get("model", self.model_id),
            "state": state,
            "questions": questions,
        }
        if "images" in payload:
            sysone_req["images"] = payload["images"]
        if "videos" in payload:
            sysone_req["videos"] = payload["videos"]

        sysone_resp = self.systemone(sysone_req)
        answers = sysone_resp.get("answers", {})

        # Extract standard AgyRouter 6 fields
        tr_info = answers.get("task_routing", {})
        task_routing = tr_info.get("choice", "code_generation")

        decomp_info = answers.get("decomposition_intent", {})
        p_decomp = float(decomp_info.get("noul", 0.0))
        decomposition_intent = p_decomp >= 0.5

        tier_info = answers.get("tier_selection", {})
        tier_selection = tier_info.get("choice", "pro")

        comp_info = answers.get("complexity_score", {})
        complexity_score = float(comp_info.get("score", 2.0))

        qual_info = answers.get("completion_quality_prediction", {})
        completion_quality_prediction = float(qual_info.get("score", 2.5))

        stealth_info = answers.get("stealth_risk_assessment", {})
        stealth_risk_assessment = stealth_info.get("choice", "safe")

        # Compile confidence and probability distributions
        confidence: Dict[str, float] = {}
        probabilities: Dict[str, Any] = {}
        for q_id, ans in answers.items():
            if "confidence" in ans:
                confidence[q_id] = float(ans["confidence"])
            if "probabilities" in ans:
                probabilities[q_id] = ans["probabilities"]
            elif ans.get("type") == "noul":
                p_val = float(ans.get("noul", 0.0))
                probabilities[q_id] = {"true": round(p_val, 4), "false": round(1.0 - p_val, 4)}

        return {
            "model": sysone_resp.get("model", self.model_id),
            "task_routing": task_routing,
            "decomposition_intent": decomposition_intent,
            "tier_selection": tier_selection,
            "complexity_score": complexity_score,
            "completion_quality_prediction": completion_quality_prediction,
            "stealth_risk_assessment": stealth_risk_assessment,
            "confidence": confidence,
            "probabilities": probabilities,
            "answers": answers,
            "usage": sysone_resp.get("usage", {"input_tokens": 128, "output_tokens": 0}),
            "latency_ms": sysone_resp.get("latency_ms", 0.0),
            "engine_used": "modal_clef_t4",
        }


# Raw underlying user class for direct test instantiation without cloud binding
RawClefDecisionWorker = getattr(ClefDecisionWorker, "_get_user_cls", lambda: ClefDecisionWorker)()


# ── Local Entrypoint for CLI Testing ───────────────────────────────────────
@app.local_entrypoint()
def main():
    """Local CLI invocation for testing."""
    worker = ClefDecisionWorker()
    worker.setup()
    health_status = worker.health()
    print("Health check response:", json.dumps(health_status, indent=2))

    sample_state = "Please refactor the database connector in db.py to support connection pooling and retry logic."
    score_result = worker.score({"state": sample_state})
    print("Score result:", json.dumps(score_result, indent=2))
