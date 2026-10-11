#!/usr/bin/env python3
"""Minimal TVC director: structured planning, routing, approval, budget, locks."""

from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable, Optional


_TEXT = {"type": "string"}
_SCENE_PROPERTIES = {
    "id": _TEXT,
    "duration_sec": {"type": "number", "minimum": 0.1},
    "visual": _TEXT,
    "voiceover": _TEXT,
    "image": {
        "type": "object",
        "properties": {"subject": _TEXT, "environment": _TEXT, "composition": _TEXT,
                       "lighting": _TEXT, "style": _TEXT, "negative": _TEXT},
    },
    "video": {
        "type": "object",
        "properties": {"action": _TEXT, "camera": _TEXT, "motion": _TEXT,
                       "transition": _TEXT, "references": {"type": "array", "items": _TEXT}},
    },
    "dialogue": {
        "type": "object",
        "properties": {"speaker": _TEXT, "line": _TEXT, "delivery": _TEXT, "language": _TEXT},
    },
    "cinematic": {
        "type": "object",
        "properties": {"shot": _TEXT, "lens": _TEXT, "framing": _TEXT,
                       "depth_of_field": _TEXT, "color_grade": _TEXT},
    },
    "audio": {
        "type": "object",
        "properties": {"ambience": _TEXT, "sfx": _TEXT, "music": _TEXT, "mix": _TEXT},
    },
}
TVC_SCHEMA = {
    "type": "object",
    "required": ["title", "duration_sec", "scenes"],
    "properties": {
        "title": _TEXT,
        "duration_sec": {"type": "number", "minimum": 1},
        "preset": _TEXT,
        "customization": {"type": "object"},
        "scenes": {"type": "array", "minItems": 1, "items": {
            "type": "object", "required": ["id", "duration_sec", "visual", "voiceover"],
            "properties": _SCENE_PROPERTIES,
        }},
    },
}

PROMPT_PRESETS = {
    "cinematic": {"cinematic": "cinematic commercial, controlled contrast", "motion": "natural, physically plausible motion"},
    "product": {"cinematic": "premium product photography, precise highlights", "motion": "smooth product reveal"},
    "presenter": {"cinematic": "clean medium shot, eye-level", "motion": "subtle natural gestures, stable face"},
}

RENDERERS = {
    "generic": {},
    "seedance": {"camera": "Describe one explicit camera move", "motion": "Use temporal action order; avoid conflicting motion"},
    "camera": {"camera": "Prioritize shot, lens, framing, then camera path"},
    "presenter": {"presenter": "Keep identity, gaze, lip movement and gestures consistent"},
    "motion": {"motion": "Specify subject motion, speed and direction independently from camera"},
}


class DirectorError(ValueError):
    pass


@dataclass(frozen=True)
class ModelRoute:
    model: str
    input_per_million: float
    output_per_million: float


DEFAULT_ROUTES = {
    "draft": ModelRoute("google/gemini-2.5-flash", 0.30, 2.50),
    "director": ModelRoute("anthropic/claude-sonnet-4", 3.00, 15.00),
}


def _validate_section(scene_id: str, name: str, value: Any) -> None:
    if not isinstance(value, dict):
        raise DirectorError(f"Scene {scene_id}: {name} phải là object")
    allowed = _SCENE_PROPERTIES[name]["properties"]
    unknown = set(value) - set(allowed)
    if unknown:
        raise DirectorError(f"Scene {scene_id}: trường {name} không hợp lệ: {', '.join(sorted(unknown))}")
    for key, item in value.items():
        expected = allowed[key]["type"]
        if expected == "string" and not isinstance(item, str):
            raise DirectorError(f"Scene {scene_id}: {name}.{key} phải là chuỗi")
        if expected == "array" and (not isinstance(item, list) or not all(isinstance(x, str) for x in item)):
            raise DirectorError(f"Scene {scene_id}: {name}.{key} phải là danh sách chuỗi")


def validate_tvc(plan: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(plan, dict):
        raise DirectorError("TVC phải là object")
    missing = [key for key in TVC_SCHEMA["required"] if key not in plan]
    if missing:
        raise DirectorError(f"Thiếu trường TVC: {', '.join(missing)}")
    if not isinstance(plan["title"], str) or not plan["title"].strip():
        raise DirectorError("title phải là chuỗi không rỗng")
    if not isinstance(plan["duration_sec"], (int, float)) or plan["duration_sec"] <= 0:
        raise DirectorError("duration_sec phải lớn hơn 0")
    if "preset" in plan and plan["preset"] not in PROMPT_PRESETS:
        raise DirectorError(f"Preset không hỗ trợ: {plan['preset']}")
    customization = plan.get("customization", {})
    if not isinstance(customization, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in customization.items()):
        raise DirectorError("customization phải là object chuỗi")
    scenes = plan["scenes"]
    if not isinstance(scenes, list) or not scenes:
        raise DirectorError("scenes phải là danh sách không rỗng")
    ids = set()
    total = 0.0
    for scene in scenes:
        required = {"id", "duration_sec", "visual", "voiceover"}
        if not isinstance(scene, dict) or not required.issubset(scene):
            raise DirectorError("Mỗi scene cần id, duration_sec, visual, voiceover")
        if not isinstance(scene["id"], str) or not scene["id"] or scene["id"] in ids:
            raise DirectorError("Scene id phải là chuỗi duy nhất")
        if not isinstance(scene["duration_sec"], (int, float)) or scene["duration_sec"] <= 0:
            raise DirectorError("Scene duration_sec phải lớn hơn 0")
        if not all(isinstance(scene[key], str) for key in ("visual", "voiceover")):
            raise DirectorError("visual và voiceover phải là chuỗi")
        for section in ("image", "video", "dialogue", "cinematic", "audio"):
            if section in scene:
                _validate_section(scene["id"], section, scene[section])
        if "dialogue" in scene and scene["voiceover"] and scene["dialogue"].get("line"):
            if scene["voiceover"].strip() != scene["dialogue"]["line"].strip():
                raise DirectorError(f"Scene {scene['id']}: voiceover và dialogue.line không nhất quán")
        ids.add(scene["id"])
        total += scene["duration_sec"]
    if abs(total - plan["duration_sec"]) > 0.01:
        raise DirectorError("Tổng thời lượng scene phải bằng duration_sec")
    return plan


def compile_scene_prompt(scene: dict[str, Any], renderer: str = "generic", preset: Optional[str] = None,
                         customization: Optional[dict[str, str]] = None) -> str:
    """Compile a validated scene into a deterministic renderer-facing prompt."""
    if renderer not in RENDERERS:
        raise DirectorError(f"Renderer không hỗ trợ: {renderer}")
    if preset is not None and preset not in PROMPT_PRESETS:
        raise DirectorError(f"Preset không hỗ trợ: {preset}")
    validate_tvc({"title": "scene", "duration_sec": scene.get("duration_sec", 0), "scenes": [scene]})
    parts = [f"Duration: {scene['duration_sec']}s", f"Visual: {scene['visual']}"]
    labels = {"image": "Image", "video": "Video", "dialogue": "Dialogue",
              "cinematic": "Cinematic", "audio": "Audio"}
    for section, label in labels.items():
        values = scene.get(section, {})
        if values:
            parts.append(f"{label}: " + "; ".join(f"{key}={value}" for key, value in values.items()))
    if scene["voiceover"] and "dialogue" not in scene:
        parts.append(f'Dialogue: line="{scene["voiceover"]}"')
    if preset:
        parts.append("Preset: " + "; ".join(f"{key}={value}" for key, value in PROMPT_PRESETS[preset].items()))
    if RENDERERS[renderer]:
        parts.append("Renderer guidance: " + "; ".join(RENDERERS[renderer].values()))
    if customization:
        if not isinstance(customization, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in customization.items()):
            raise DirectorError("customization phải là object chuỗi")
        parts.append("Customization: " + "; ".join(f"{key}={value}" for key, value in customization.items()))
    return "\n".join(parts)


def compile_tvc_prompts(plan: dict[str, Any], renderer: str = "generic", preset: Optional[str] = None,
                        customization: Optional[dict[str, str]] = None) -> dict[str, str]:
    validate_tvc(plan)
    selected_preset = preset if preset is not None else plan.get("preset")
    merged = dict(plan.get("customization", {}))
    if customization:
        merged.update(customization)
    return {scene["id"]: compile_scene_prompt(scene, renderer, selected_preset, merged) for scene in plan["scenes"]}


class DirectorAdapter:
    """OpenAI-compatible adapter for OpenRouter or 9Router."""

    def __init__(self, base_url: str, api_key: str, opener: Callable[..., Any] = urllib.request.urlopen):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.opener = opener

    def generate(self, brief: str, model: str) -> dict[str, Any]:
        body = json.dumps({
            "model": model,
            "messages": [{"role": "system", "content": "Return only a TVC storyboard JSON matching the supplied schema."},
                         {"role": "user", "content": brief}],
            "response_format": {"type": "json_schema", "json_schema": {"name": "tvc", "strict": True, "schema": TVC_SCHEMA}},
        }).encode()
        request = urllib.request.Request(
            f"{self.base_url}/chat/completions", data=body,
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
        )
        with self.opener(request, timeout=60) as response:
            payload = json.loads(response.read())
        return validate_tvc(json.loads(payload["choices"][0]["message"]["content"]))


class TVCDirector:
    def __init__(self, adapter: DirectorAdapter, budget_usd: float, routes: Optional[dict[str, ModelRoute]] = None):
        if budget_usd <= 0:
            raise DirectorError("budget_usd phải lớn hơn 0")
        self.adapter = adapter
        self.budget_usd = budget_usd
        self.routes = routes or DEFAULT_ROUTES
        self.plan: Optional[dict[str, Any]] = None
        self.approved = False
        self.locked_scenes: set[str] = set()

    def route(self, stage: str) -> ModelRoute:
        if stage not in self.routes:
            raise DirectorError(f"Không có model route cho stage: {stage}")
        return self.routes[stage]

    def estimate_cost(self, stage: str, input_tokens: int, output_tokens: int) -> float:
        route = self.route(stage)
        return (input_tokens * route.input_per_million + output_tokens * route.output_per_million) / 1_000_000

    def create_storyboard(self, brief: str, stage: str = "director", input_tokens: int = 4000, output_tokens: int = 3000) -> dict[str, Any]:
        estimated = self.estimate_cost(stage, input_tokens, output_tokens)
        if estimated > self.budget_usd:
            raise DirectorError(f"Ước tính ${estimated:.4f} vượt ngân sách ${self.budget_usd:.4f}")
        self.plan = self.adapter.generate(brief, self.route(stage).model)
        self.approved = False
        self.locked_scenes.clear()
        return self.plan

    def approve_storyboard(self) -> None:
        if self.plan is None:
            raise DirectorError("Chưa có storyboard để duyệt")
        self.approved = True

    def lock_scene(self, scene_id: str) -> None:
        if not self.approved:
            raise DirectorError("Storyboard phải được duyệt trước khi lock scene")
        if self.plan is None or scene_id not in {scene["id"] for scene in self.plan["scenes"]}:
            raise DirectorError(f"Không tìm thấy scene: {scene_id}")
        self.locked_scenes.add(scene_id)

    def update_scene(self, scene_id: str, changes: dict[str, Any]) -> None:
        if scene_id in self.locked_scenes:
            raise DirectorError(f"Scene đã lock: {scene_id}")
        if self.plan is None:
            raise DirectorError("Chưa có storyboard")
        scene = next((item for item in self.plan["scenes"] if item["id"] == scene_id), None)
        if scene is None:
            raise DirectorError(f"Không tìm thấy scene: {scene_id}")
        scene.update(changes)
        validate_tvc(self.plan)
        self.approved = False

    def kanban_handoff(self) -> dict[str, Any]:
        if not self.approved or self.plan is None:
            raise DirectorError("Storyboard chưa được duyệt")
        return {
            "summary": f"Storyboard TVC đã duyệt: {self.plan['title']}",
            "metadata": {
                "tvc": self.plan,
                "scene_locks": sorted(self.locked_scenes),
                "render_ready": len(self.locked_scenes) == len(self.plan["scenes"]),
            },
        }
