#!/usr/bin/env python3
"""
manim_srs_planner.py — Manim SRS & Registry-First Scene Planning Engine
======================================================================
Part of the `youtube-video-rewriter` Skill ecosystem on ThinkPad P15.

Connects to `assets/scripts_video/manim_registry.json` (Single Source of Truth,
indexing 100 Scenes) to plan animation scenes with:
1. Registry-First Scene Reuse (Matches keywords against 100 existing scenes)
2. 4-Zone Spatial Partitioning (Zone 1 Tracker, Zone 2 Canvas 60%, Zone 3 Stack 40%, Zone 4 Callout)
3. Subtitle Safe Zone Enforcement (Y >= -2.6)
4. Phosphor Duotone Icon Integration (1,512 SVGs) & 4 YouTube Style Presets
5. Science Template Binding (Physics, Chemistry, AI/ML, CS/Algo, Pure Math)
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

REGISTRY_PATH = Path("/home/zen/hermes-agent/assets/scripts_video/manim_registry.json")
DUOTONE_DIR = Path("/home/zen/hermes-agent/assets/duotone")
TEMPLATES_DIR = Path(
    "/home/zen/hermes-agent/.agents/skills/manim-production/references/templates"
)

# Style Presets for YouTube
STYLES = ["neo_noir", "architecture", "minimal", "vibrant"]

# Science Templates Mapping
SCIENCE_TEMPLATES = {
    "PHYSICS": "template_physics.py",
    "CHEMISTRY": "template_chemistry.py",
    "AI_ML": "template_ml.py",
    "CS_ALGO": "template_cs_algo.py",
    "PURE_MATH": "template_math_3b1b.py",
}

# Icon suggestion map for common technical concepts
DUOTONE_SUGGESTIONS = {
    "tree": "tree-structure-duotone.svg",
    "splay": "arrows-clockwise-duotone.svg",
    "graph": "graph-duotone.svg",
    "network": "network-duotone.svg",
    "cpu": "cpu-duotone.svg",
    "gpu": "graphic-eq-duotone.svg",
    "memory": "hard-drives-duotone.svg",
    "database": "database-duotone.svg",
    "cache": "lightning-duotone.svg",
    "attention": "crosshair-duotone.svg",
    "matrix": "grid-four-duotone.svg",
    "physics": "atom-duotone.svg",
    "chemistry": "flask-duotone.svg",
    "math": "function-duotone.svg",
    "warning": "warning-duotone.svg",
    "check": "check-circle-duotone.svg",
    "code": "code-duotone.svg",
    "terminal": "terminal-window-duotone.svg",
    "security": "shield-check-duotone.svg",
    "speed": "gauge-duotone.svg",
}


def load_manim_registry() -> List[Dict[str, Any]]:
    """Load the 100-scene Manim Registry database."""
    if not REGISTRY_PATH.exists():
        print(f"[!] Warning: Registry not found at {REGISTRY_PATH}", file=sys.stderr)
        return []
    try:
        data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        return data.get("scenes", [])
    except Exception as e:
        print(f"[!] Failed to parse registry: {e}", file=sys.stderr)
        return []


def search_registry(
    scenes: List[Dict[str, Any]], query: str, domain: str = ""
) -> List[Dict[str, Any]]:
    """Search for matching scenes using keyword and domain filters."""
    query_lower = query.lower()
    matches = []

    for sc in scenes:
        name = sc.get("class_name", "").lower()
        doc = ' '.join([sc.get('script_context', sc.get('docstring', '')), sc.get('scientific_foundation', ''), ' '.join(sc.get('semantic_tags', []))]).lower()
        sc_domain = sc.get('domain', '').lower()
        if not query_lower or (domain and domain.lower() != sc_domain):
            continue
        formulas = ' '.join(sc.get('core_latex', sc.get('latex_formulas', []))).lower()

        score = 0
        if query_lower in name:
            score += 10
        if query_lower in doc:
            score += 5
        if query_lower in formulas:
            score += 4
        if score and domain:
            score += 2

        if score > 0:
            matches.append({"scene": sc, "score": score})

    matches.sort(key=lambda x: x["score"], reverse=True)
    return [m["scene"] for m in matches[:3]]


def find_best_duotone_icon(concept: str) -> str:
    """Find the most appropriate Phosphor Duotone icon from 1,512 assets."""
    concept_lower = concept.lower()
    for kw, icon_file in DUOTONE_SUGGESTIONS.items():
        if kw in concept_lower:
            target_path = DUOTONE_DIR / icon_file
            if target_path.exists():
                return icon_file

    return 'PLACEHOLDER:missing-icon'


def plan_manim_srs(
    decon_data: Dict[str, Any], output_dir: Path, style: str = "neo_noir"
) -> Dict[str, Any]:
    """Build full Manim SRS plan matching acts with existing or new scenes."""
    output_dir.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(REGISTRY_PATH.parent))
    from inventory_contract import final_eligible
    profile = decon_data.get('profile')
    final = decon_data.get('mode', 'preview') == 'final'
    registry_scenes = load_manim_registry()
    if final:
        if not profile:
            raise ValueError('Final planning requires an explicit profile')
        registry_scenes = [r for r in registry_scenes if final_eligible(r, profile, decon_data.get('capabilities', []))]
    domain = decon_data.get("domain", "CS_ALGO")
    title = decon_data.get("title", "")
    acts = decon_data.get("acts", [])

    print(f"[*] Planning Manim SRS for {len(acts)} acts in domain `{domain}` (Style: {style})")
    matched_scenes_plan = []

    for act in acts:
        act_num = act["act_number"]
        act_name = act["name"]
        key_terms = act.get("key_points", []) + [act.get("visual_idea", "")]
        search_query = " ".join(key_terms)

        # Search registry for matching scenes
        candidates = []
        for word in re.findall(r"\b\w{4,}\b", search_query.lower()):
            res = search_registry(registry_scenes, word, domain)
            for r in res:
                if r not in candidates:
                    candidates.append(r)

        reused_scene = None
        plan_type = "NEW_DESIGN"

        if candidates:
            top_candidate = candidates[0]
            plan_type = "REUSE"
            reused_scene = {
                "class_name": top_candidate["class_name"],
                "source_file": top_candidate.get("file_path", ""),
                "nature": top_candidate.get("nature", "DYNAMIC_ANIMATION"),
                "core_math": top_candidate.get("scientific_foundation", ""),
                "adaptation": f"Sử dụng animation gốc của {top_candidate['class_name']}, cập nhật nhãn văn bản theo ngữ cảnh {act_name}.",
            }

        # Select Duotone icon
        icon_name = find_best_duotone_icon(act_name + ' ' + search_query)
        if final:
            catalog = json.loads(REGISTRY_PATH.read_text(encoding='utf-8'))
            icon = next((r for r in catalog.get('assets', []) if r.get('id') == 'assets/duotone/' + icon_name.removesuffix('.svg')), None)
            if reused_scene is None or icon is None or not final_eligible(icon, profile, renderer='svg'):
                raise ValueError(f'Final inventory gap: act {act_num}; scene or icon lacks matching approval/license')
        elif not icon_name.startswith('PLACEHOLDER:'):
            from inventory_contract import inspect_svg
            try:
                inspect_svg(DUOTONE_DIR / icon_name)
            except (ValueError, OSError):
                icon_name = 'PLACEHOLDER:unsafe-icon'

        # Build 4-zone spatial blueprint
        spatial_blueprint = {
            "zone_1_tracker": {
                "component": "StateTrackerBar",
                "y_coord": 3.3,
                "active_step": act_num - 1,
                "label": act_name.split("&")[0].strip().upper(),
            },
            "zone_2_canvas": {
                "width_ratio": "60%",
                "x_range": [-6.0, 0.0],
                "visual_type": "Geometric / Dynamic Animation",
                "description": act.get("visual_idea", "Mô phỏng chuyển động trực quan"),
            },
            "zone_3_stack": {
                "width_ratio": "40%",
                "x_range": [1.0, 6.0],
                "components": [
                    {
                        "type": "ConceptBadge",
                        "text": act_name.split("&")[0].strip(),
                        "icon": icon_name,
                    },
                    {
                        "type": "SafeFormulaCard",
                        "formula": "ASCII_LATEX_FORMULA",
                        "description": "Công thức toán học cốt lõi",
                    },
                ],
            },
            "zone_4_callout": {
                "component": "BottomCalloutCard",
                "y_range": [-2.4, -1.8],
                "text": act.get("cognitive_goal", "Đúc kết nguyên lý cốt lõi"),
            },
            "subtitle_safe_zone": "Y >= -2.6 (Tuyệt đối không đặt Mobject cố định tại Y < -2.6)",
        }

        scene_spec = {
            "act_number": act_num,
            "scene_name": f"Scene_{act_num}_{re.sub(r'[^a-zA-Z0-9]', '', act_name)}",
            "plan_type": plan_type,
            "reused_scene": reused_scene,
            "style": style,
            "duotone_icon": icon_name,
            "spatial_blueprint": spatial_blueprint,
            "recommended_template": SCIENCE_TEMPLATES.get(
                domain, "template_cs_algo.py"
            ),
        }
        matched_scenes_plan.append(scene_spec)

    srs_result = {
        "title": title,
        "mode": 'final' if final else 'preview',
        "production_ready": False,
        "profile": profile,
        "domain": domain,
        "style_preset": style,
        "total_scenes": len(matched_scenes_plan),
        "reused_count": sum(
            1 for s in matched_scenes_plan if s["plan_type"] == "REUSE"
        ),
        "new_design_count": sum(
            1 for s in matched_scenes_plan if s["plan_type"] == "NEW_DESIGN"
        ),
        "scenes": matched_scenes_plan,
    }

    # Save JSON
    json_path = output_dir / "manim_srs_plan.json"
    json_path.write_text(json.dumps(srs_result, indent=2, ensure_ascii=False))

    # Generate Markdown Report
    md_content = f"""# ĐẶC TẢ HOẠT HỌA MANIM (MANIM SRS & REGISTRY-FIRST PLAN)
## Video: {title}
- **Chuyên ngành (Domain)**: `{domain}`
- **Phong cách thị giác (Style)**: `{style}`
- **Tổng số phân cảnh**: {srs_result['total_scenes']} scenes
- **Tái sử dụng từ Registry**: {srs_result['reused_count']} scenes | **Thiết kế mới 4-Zone**: {srs_result['new_design_count']} scenes
- **Template nền tảng**: `{SCIENCE_TEMPLATES.get(domain, 'template_cs_algo.py')}`

---

## QUY CHUẨN BỐ CỤC 4 PHÂN VÙNG BẮT BUỘC (4-ZONE SPATIAL CONTRACT)
- **Zone 1 (Đỉnh)**: `StateTrackerBar` tại $Y \\approx +3.3$, theo dõi tiến trình 6 hồi.
- **Zone 2 (Trái 60%)**: Sân khấu hình học chính ($X \\in [-6.0, 0.0]$).
- **Zone 3 (Phải 40%)**: Chồng nhận thức xếp tầng ($X \\in [1.0, 6.0]$): `ConceptBadge` + `SafeFormulaCard` + `BulletRules`.
- **Zone 4 (Đáy)**: `BottomCalloutCard` ($Y \\in [-2.4, -1.8]$).
- **Vùng cấm phụ đề**: $Y < -2.6$ (Tuyệt đối không che subtitle tự động YouTube).

---

## KẾ HOẠCH PHÂN CẢNH CHI TIẾT THEO HỒI
"""
    for sc in matched_scenes_plan:
        reuse_str = (
            f"Tái sử dụng lớp `{sc['reused_scene']['class_name']}` từ `{sc['reused_scene']['source_file']}`"
            if sc["plan_type"] == "REUSE"
            else "Thiết kế mới hoàn toàn theo bố cục 4 phân vùng"
        )
        md_content += f"""
### Phân cảnh {sc['act_number']}: {sc['scene_name']}
- **Chế độ dựng**: `{sc['plan_type']}` ({reuse_str})
- **Biểu tượng Duotone**: `{sc['duotone_icon']}` (Phosphor SVG)
- **Zone 1 (Tracker)**: Bước {sc['spatial_blueprint']['zone_1_tracker']['active_step']} ({sc['spatial_blueprint']['zone_1_tracker']['label']})
- **Zone 2 (Canvas 60%)**: {sc['spatial_blueprint']['zone_2_canvas']['description']}
- **Zone 3 (Stack 40%)**: Badge `[{sc['spatial_blueprint']['zone_3_stack']['components'][0]['text']}]` + Formula Box
- **Zone 4 (Callout)**: *"{sc['spatial_blueprint']['zone_4_callout']['text']}"*
- **Ràng buộc an toàn**: {sc['spatial_blueprint']['subtitle_safe_zone']}
"""

    md_path = output_dir / "manim_srs_plan.md"
    md_path.write_text(md_content, encoding="utf-8")
    print(f"[+] Manim SRS plan completed: {md_path}")
    return srs_result


def main():
    parser = argparse.ArgumentParser(
        description="Manim SRS & Registry-First Scene Planning Engine"
    )
    parser.add_argument(
        "--deconstruct-json",
        default="./workspace/youtube_deconstruct/deconstruction_report.json",
        help="Path to deconstruction report JSON",
    )
    parser.add_argument(
        "--output-dir",
        default="./workspace/youtube_manim_srs",
        help="Directory to save Manim SRS plan",
    )
    parser.add_argument(
        "--style",
        choices=STYLES,
        default="neo_noir",
        help="Visual style preset for YouTube",
    )
    args = parser.parse_args()

    decon_path = Path(args.deconstruct_json)
    if not decon_path.exists():
        print(f"[!] Error: {decon_path} not found.", file=sys.stderr)
        sys.exit(1)

    data = json.loads(decon_path.read_text(encoding="utf-8"))
    plan_manim_srs(data, Path(args.output_dir), args.style)


if __name__ == "__main__":
    main()
