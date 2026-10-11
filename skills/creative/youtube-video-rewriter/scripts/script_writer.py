#!/usr/bin/env python3
"""
script_writer.py — Multi-Track Production Scriptwriter Engine
============================================================
Part of the `youtube-video-rewriter` Skill ecosystem on ThinkPad P15.

Generates synchronized 4-track production scripts:
- Track 1: Timeline & Act Progression (6 Acts)
- Track 2: OmniVoice TTS Voiceover (Vietnamese phonetic pronunciation, breath pauses [pause 0.5s], 135-145 WPM)
- Track 3: Manim Animation Blueprint (4-Zone layout, ZenPalette, ASCII MathTex)
- Track 4: Footage B-Roll & SFX Cues (Screen capture, IDE terminal, whoosh, bass drop)
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Pronunciation Dictionary
PRONUNCIATION_DICT_PATH = (
    Path(__file__).resolve().parent.parent
    / "references"
    / "pronunciation_dictionary.json"
)

# LM Studio endpoint on ThinkPad P15
LM_STUDIO_URL = os.environ.get("LM_STUDIO_URL", "http://10.123.214.1:1234/v1")
FALLBACK_LM_URL = "http://127.0.0.1:1234/v1"

# Import PexelsVisualMatcher for B-roll contextual matching (>90% rule)
SCRIPTS_VIDEO_DIR = Path("/home/zen/hermes-agent/assets/scripts_video")
if str(SCRIPTS_VIDEO_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_VIDEO_DIR))

try:
    from pexels_visual_matcher import PexelsVisualMatcher
except Exception:
    PexelsVisualMatcher = None


def load_pronunciation_dict() -> Dict[str, str]:
    """Load phonetic translation mappings."""
    if not PRONUNCIATION_DICT_PATH.exists():
        return {}
    try:
        data = json.loads(PRONUNCIATION_DICT_PATH.read_text(encoding="utf-8"))
        return data.get("terms", {})
    except Exception:
        return {}


def phonetize_text(text: str, pron_dict: Dict[str, str]) -> str:
    """Replace technical English terms with Vietnamese phonetic equivalents for TTS."""
    result = text
    # Sort terms by length descending to match compound terms first (e.g. 'splay tree' before 'tree')
    sorted_terms = sorted(pron_dict.keys(), key=len, reverse=True)
    for term in sorted_terms:
        phonetic = pron_dict[term]
        pattern = r"\b" + re.escape(term) + r"\b"
        result = re.sub(pattern, f"{term} ({phonetic})", result, flags=re.IGNORECASE)
    return result


def query_llm_scriptwriting(
    title: str,
    domain: str,
    core_thesis: str,
    core_invariant: str,
    acts: List[Dict[str, Any]],
    manim_scenes: List[Dict[str, Any]],
    pron_dict: Dict[str, str],
) -> Optional[List[Dict[str, Any]]]:
    """Query local LM Studio (Qwen 3.5 9B) to write cinematic Vietnamese prose."""
    try:
        from openai import OpenAI

        client = None
        for url in [LM_STUDIO_URL, FALLBACK_LM_URL]:
            try:
                test_client = OpenAI(base_url=url, api_key="lm-studio")
                test_client.models.list()
                client = test_client
                break
            except Exception:
                continue

        if not client:
            return None

        prompt = f"""Bạn là Tác giả Kịch bản chính của series 'Tôi Làm Việc' trên kênh ZENPHAM.
Hãy viết lời thoại thuyết minh (Voiceover) tiếng Việt cho 6 hồi của video sau đây:

TIÊU ĐỀ: {title}
CHUYÊN NGÀNH: {domain}
THÔNG ĐIỆP CỐT LÕI: {core_thesis}
TIÊN ĐỀ BẤT BIẾN: {core_invariant}

QUY TẮC BẮT BUỘC:
1. Giọng văn: Trầm ấm, suy tư, sắc sảo về mặt kỹ thuật, mang tinh thần Digital Craftsmanship của ZenPham.
2. Ngắt nhịp thở cho TTS: Chèn rõ các thẻ [pause 0.5s], [pause 0.8s], [emphasis] vào các điểm ngắt ý.
3. Độ dài: Mỗi hồi khoảng 120-160 từ (khoảng 50-70 giây đọc ở tốc độ 140 từ/phút).
4. Phù hợp tuyệt đối với từng hồi sư phạm.

CÁC HỒI CẦN VIẾT:
{json.dumps(acts, ensure_ascii=False, indent=2)}

ĐẦU RA JSON DUY NHẤT (Dạng mảng 6 phần tử):
[
  {{
    "act_number": 1,
    "voiceover": "Lời thoại hồi 1 có thẻ [pause]...",
    "footage": "Mô tả cảnh quay B-roll / màn hình IDE / terminal...",
    "sfx": "sub_bass_drop, glitch_low..."
  }},
  ...
]
Chỉ xuất JSON thuần túy, không có text phụ.
"""

        response = client.chat.completions.create(
            model="qwen/qwen3.5-9b",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=3000,
        )
        content = response.choices[0].message.content or ""
        json_match = re.search(r"\[.*\]", content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))
    except Exception as e:
        print(f"    [!] LM Studio scriptwriting failed: {e}", file=sys.stderr)

    return None


def fallback_scriptwriting(
    title: str,
    domain: str,
    core_thesis: str,
    core_invariant: str,
    acts: List[Dict[str, Any]],
    pron_dict: Dict[str, str],
) -> List[Dict[str, Any]]:
    """Deterministic fallback script generator in ZenPham voice."""
    print("    [*] Using deterministic ZenPham scriptwriter template...")

    default_scripts = [
        # Act 1: Hook
        {
            "act_number": 1,
            "voiceover": (
                "[pause 0.5s] Một trong những ảo tưởng ngọt ngào nhất của người làm phần mềm... [emphasis] là tin rằng lý thuyết sách vở luôn hoàn hảo khi chạm vào dữ liệu thực tế. "
                "[pause 0.8s] Chúng ta được dạy rằng cấu trúc này đảm bảo độ phức tạp tối ưu ô-lốc-en (O(log N)). "
                "[pause 0.5s] Nhưng chỉ cần một dòng dữ liệu có trật tự bất lợi đổ vào, toàn bộ bảo chứng hiệu năng lập tức sụp đổ. "
                "[pause 0.6s] Hệ thống của bạn nghẽn đứng, và bài toán đặt ra không còn là code cho chạy — mà là hiểu thấu bản chất của sự suy biến."
            ),
            "footage": "Màn hình Terminal Linux htop tải 100% đỏ rực, log lỗi connection timeout cuộn nhanh.",
            "sfx": "sub_bass_drop tại 00:00, glitch_low khi hệ thống nghẽn, ambient_drone_dark.",
        },
        # Act 2: Pain Point
        {
            "act_number": 2,
            "voiceover": (
                "[pause 0.5s] Khi đào sâu vào từng byte bộ nhớ, nguyên nhân gốc rễ bắt đầu lộ diện. "
                "[pause 0.6s] Sự lười biếng trong việc tái cân bằng khiến các nút dữ liệu dồn về một phía, biến cấu trúc cây thành một danh sách liên kết thẳng đuột. "
                "[pause 0.8s] Mỗi truy vấn tìm kiếm giờ đây phải duyệt qua toàn bộ N phần tử. "
                "[pause 0.5s] Độ trễ P99 tăng vọt gấp một trăm lần. [pause 0.6s] Cái giá phải trả cho một quyết định kiến trúc thiếu chiều sâu... luôn được đo bằng sự kiệt quệ của hạ tầng."
            ),
            "footage": "IDE VS Code zoom cận cảnh hàm đệ quy không cân bằng, bộ nhớ RAM cấp phát liên tục.",
            "sfx": "keyboard_mechanical_clicks, warning_beep_soft.",
        },
        # Act 3: Intuition
        {
            "act_number": 3,
            "voiceover": (
                "[pause 0.5s] Để giải cứu hệ thống, chúng ta cần một mô hình tư duy hoàn toàn mới. "
                "[pause 0.7s] Thay vì cố gắng duy trì một trật tự cứng nhắc tốn kém, tại sao không để chính dữ liệu tự tái cấu trúc cấu trúc dữ liệu? "
                "[pause 0.8s] Quy luật thực nghiệm chỉ ra rằng: tám mươi phần trăm truy vấn luôn tập trung vào hai mươi phần trăm phần tử nóng. "
                "[pause 0.6s] Hãy để mỗi lần chạm vào dữ liệu là một lần đưa nó bay thẳng lên đỉnh. [pause 0.5s] Một sự tự tiến hóa kỳ diệu bằng trực quan hình học."
            ),
            "footage": "Mô phỏng 3D dòng xoáy dữ liệu hoặc sơ đồ mạng nơ-ron tự kết nối lại các nút tích cực.",
            "sfx": "whoosh_subtle, energy_transition_chime.",
        },
        # Act 4: Mathematical Rigor
        {
            "act_number": 4,
            "voiceover": (
                "[pause 0.5s] Nhưng cảm tính không bao giờ đủ để thuyết phục một kỹ sư chân chính. [pause 0.7s] Chúng ta cần toán học. "
                "[pause 0.8s] Bằng việc định nghĩa một hàm thế năng đo lường mức độ xáo trộn của cấu trúc, chúng ta chứng minh được rằng: "
                "[pause 0.6s] Mặc dù một thao tác đơn lẻ có thể tốn chi phí tuyến tính, nhưng trung bình trên một chuỗi M thao tác liên tiếp, chi phí trừ dần (Amortized Cost) vẫn bị chặn chắc chắn bởi ô-lốc-en. "
                "[pause 0.8s] Định lý bảo toàn năng lượng đã biến điều tưởng như nghịch lý thành chân lý hiển nhiên."
            ),
            "footage": "Bản PDF bài báo khoa học gốc của tác giả năm 1985 highlight phương trình thế năng Phi(T).",
            "sfx": "chalk_writing_soft, low_resonance_chord.",
        },
        # Act 5: Production Benchmark
        {
            "act_number": 5,
            "voiceover": (
                "[pause 0.5s] Rời khỏi trang giấy chứng minh, chúng ta đưa thuật toán vào chiến trường sản xuất. "
                "[pause 0.6s] Trong nhân Linux, trong hệ thống bộ đệm của cơ sở dữ liệu, và trong các bộ định tuyến mạng tốc độ cao. "
                "[pause 0.8s] Kết quả đo kiểm thực tế cho thấy thông lượng tăng vọt gấp ba lần so với các cấu trúc cây tĩnh. "
                "[pause 0.5s] Nhưng không có bữa trưa nào miễn phí. [pause 0.6s] Trong môi trường đa luồng (multi-threading), việc ghi đè liên tục khi đọc đòi hỏi kỹ thuật khóa đồng bộ cực kỳ tinh tế."
            ),
            "footage": "Biểu đồ Grafana nhảy số thông lượng (throughput req/s), terminal chạy lệnh benchmark ApacheBench.",
            "sfx": "digital_beep_fast, riser_accent.",
        },
        # Act 6: Craftsmanship
        {
            "act_number": 6,
            "voiceover": (
                "[pause 0.5s] Sau cùng, vẻ đẹp của một cấu trúc dữ liệu không nằm ở việc nó đứng yên hoàn hảo trong sách giáo khoa... "
                "[pause 0.8s] Mà nằm ở khả năng thích nghi bền bỉ trước sự hỗn loạn của thế giới thực. "
                "[pause 0.7s] Làm nghề phần mềm cũng vậy. [pause 0.5s] Đừng tìm kiếm một kiến trúc bất biến không tì vết. "
                "[pause 0.8s] Hãy xây dựng những hệ thống có khả năng tự sửa mình, tự tiến hóa sau mỗi va đập của dữ liệu. [pause 1.0s] Đó là cốt cách của một người thợ thủ công số."
            ),
            "footage": "Góc bàn làm việc đêm tối, màn hình ThinkPad hiển thị đoạn code hoàn chỉnh tĩnh lặng, tách trà bốc khói mờ.",
            "sfx": "piano_melancholy_chord, fade_to_silence.",
        },
    ]
    return default_scripts


def write_production_script(
    decon_data: Dict[str, Any],
    srs_data: Dict[str, Any],
    output_dir: Path,
) -> Dict[str, Any]:
    """Assemble complete 4-track production script."""
    output_dir.mkdir(parents=True, exist_ok=True)
    pron_dict = load_pronunciation_dict()

    title = decon_data.get("title", "")
    domain = decon_data.get("domain", "CS_ALGO")
    core_thesis = decon_data.get("core_thesis", "")
    core_invariant = decon_data.get("core_invariant", "")
    acts = decon_data.get("acts", [])
    scenes = srs_data.get("scenes", [])

    print(f"[*] Writing Multi-Track Script for: {title}")

    # Step 1: Query LLM or Fallback for Script Content
    script_beats = query_llm_scriptwriting(
        title, domain, core_thesis, core_invariant, acts, scenes, pron_dict
    )
    if not script_beats:
        script_beats = fallback_scriptwriting(
            title, domain, core_thesis, core_invariant, acts, pron_dict
        )

    # Step 2: Combine with Manim SRS & Footage Tracks
    multi_track_scenes = []
    total_words = 0
    matcher = PexelsVisualMatcher() if PexelsVisualMatcher else None

    for idx, act in enumerate(acts):
        beat = script_beats[idx] if idx < len(script_beats) else script_beats[-1]
        scene = scenes[idx] if idx < len(scenes) else scenes[-1]

        raw_vo = beat.get("voiceover", "")
        clean_text_for_counting = re.sub(r"\[[^\]]+\]", "", raw_vo)
        word_count = len(clean_text_for_counting.split())
        total_words += word_count
        est_duration_sec = round((word_count / 140) * 60, 1)

        raw_footage = beat.get("footage", "B-roll minh họa code và terminal.")
        pexels_stock_info = None
        use_pexels = False

        if matcher and raw_footage:
            try:
                best_cand, _ = matcher.match_context(raw_footage, orientation="landscape")
                if best_cand and best_cand.matches_90_percent:
                    pexels_stock_info = {
                        "id": best_cand.id,
                        "title": best_cand.title,
                        "url": best_cand.url,
                        "score": best_cand.score,
                        "rationale": best_cand.rationale,
                    }
                    use_pexels = True
            except Exception:
                pass

        if use_pexels and pexels_stock_info:
            footage_directive = (
                f"[VISUAL: PEXELS_STOCK #{pexels_stock_info['id']} (Khớp: {pexels_stock_info['score']:.1%}) — {pexels_stock_info['title']}] "
                f"{raw_footage} (URL: {pexels_stock_info['url']})"
            )
        else:
            footage_directive = f"[VISUAL: MANIM / B-ROLL FALLBACK] {raw_footage}"

        combined_scene = {
            "act_number": act["act_number"],
            "act_name": act["name"],
            "timeline": act.get("target_duration", f"{idx*60:02d}:00 - {(idx+1)*60:02d}:00"),
            "track_1_scene_title": f"Act {act['act_number']}: {act['name']}",
            "track_2_voiceover": raw_vo,
            "track_2_word_count": word_count,
            "track_2_est_seconds": est_duration_sec,
            "track_3_manim_blueprint": {
                "class_name": scene["scene_name"],
                "plan_type": scene["plan_type"],
                "style": scene["style"],
                "duotone_icon": scene["duotone_icon"],
                "zone_1_tracker": scene["spatial_blueprint"]["zone_1_tracker"],
                "zone_2_canvas": scene["spatial_blueprint"]["zone_2_canvas"],
                "zone_3_stack": scene["spatial_blueprint"]["zone_3_stack"],
                "zone_4_callout": scene["spatial_blueprint"]["zone_4_callout"],
                "subtitle_safe_zone": scene["spatial_blueprint"]["subtitle_safe_zone"],
            },
            "track_4_footage": footage_directive,
            "track_4_use_pexels": use_pexels,
            "track_4_pexels_info": pexels_stock_info,
            "track_4_sfx": beat.get("sfx", "whoosh_subtle, ambient_drone."),
        }
        multi_track_scenes.append(combined_scene)

    result = {
        "title": title,
        "domain": domain,
        "style": srs_data.get("style_preset", "neo_noir"),
        "total_words": total_words,
        "est_total_duration_minutes": round(total_words / 140, 1),
        "scenes": multi_track_scenes,
    }

    # Save JSON
    json_path = output_dir / "production_script.json"
    json_path.write_text(json.dumps(result, indent=2, ensure_ascii=False))

    # Generate Formatted Markdown Table
    md_content = f"""# KỊCH BẢN ĐA LUỒNG SẢN XUẤT (MULTI-TRACK PRODUCTION SCRIPT)
## Kênh: ZENPHAM — "Tôi Làm Việc"
- **Tiêu đề video**: {title}
- **Chuyên ngành**: `{domain}` | **Phong cách**: `{result['style']}`
- **Tổng số từ thuyết minh**: ~{total_words} từ (Khoảng {result['est_total_duration_minutes']} phút @ 140 WPM)
- **Tiên đề bất biến (Core Invariant)**: {core_invariant}

---

"""
    for sc in multi_track_scenes:
        manim_spec = sc["track_3_manim_blueprint"]
        md_content += f"""### HỒI {sc['act_number']}: {sc['act_name'].upper()} ({sc['timeline']})
*Dự kiến thời lượng lời thoại: ~{sc['track_2_est_seconds']}s ({sc['track_2_word_count']} từ)*

| Phân Luồng | Đặc Tả Chi Tiết |
| :--- | :--- |
| **Track 1: Timeline & Phân Cảnh** | `{sc['timeline']}` \| **{sc['track_1_scene_title']}** |
| **Track 2: Lời Thoại (OmniVoice TTS)** | {sc['track_2_voiceover']} |
| **Track 3: Hoạt Họa Manim (4 Phân Vùng)** | **Lớp**: `{manim_spec['class_name']}` ({manim_spec['plan_type']})<br>- **Icon Duotone**: `{manim_spec['duotone_icon']}`<br>- **Zone 1 (Tracker)**: `{manim_spec['zone_1_tracker']['label']}` (Bước {manim_spec['zone_1_tracker']['active_step']})<br>- **Zone 2 (Canvas 60%)**: {manim_spec['zone_2_canvas']['description']}<br>- **Zone 3 (Stack 40%)**: Badge `[{manim_spec['zone_3_stack']['components'][0]['text']}]` + Formula Card<br>- **Zone 4 (Callout)**: *"{manim_spec['zone_4_callout']['text']}"*<br>- **Ràng buộc phụ đề**: `{manim_spec['subtitle_safe_zone']}` |
| **Track 4: Footage & SFX Cues** | - **Footage B-Roll**: {sc['track_4_footage']}<br>- **SFX**: {sc['track_4_sfx']} |

---
"""

    md_path = output_dir / "production_script_multitrack.md"
    md_path.write_text(md_content, encoding="utf-8")
    print(f"[+] Multi-Track Production Script created: {md_path}")
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Multi-Track Production Scriptwriter Engine"
    )
    parser.add_argument(
        "--deconstruct-json",
        default="./workspace/youtube_deconstruct/deconstruction_report.json",
        help="Path to deconstruction report JSON",
    )
    parser.add_argument(
        "--manim-srs-json",
        default="./workspace/youtube_manim_srs/manim_srs_plan.json",
        help="Path to Manim SRS plan JSON",
    )
    parser.add_argument(
        "--output-dir",
        default="./workspace/youtube_script",
        help="Directory to save production script",
    )
    args = parser.parse_args()

    decon_p = Path(args.deconstruct_json)
    srs_p = Path(args.manim_srs_json)

    if not decon_p.exists() or not srs_p.exists():
        print("[!] Error: Required input JSON files missing.", file=sys.stderr)
        sys.exit(1)

    decon_data = json.loads(decon_p.read_text(encoding="utf-8"))
    srs_data = json.loads(srs_p.read_text(encoding="utf-8"))

    write_production_script(decon_data, srs_data, Path(args.output_dir))


if __name__ == "__main__":
    main()
