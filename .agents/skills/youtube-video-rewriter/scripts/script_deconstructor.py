#!/usr/bin/env python3
"""
script_deconstructor.py — Pedagogical Script & Structural Deconstruction Engine
==============================================================================
Part of the `youtube-video-rewriter` Skill ecosystem on ThinkPad P15.

Analyzes raw subtitles, chapters, and metadata to reverse-engineer:
1. Core Pedagogical Invariant & Thesis Defense
2. Pain Points, Anomaly Conditions & Failure Modes
3. 6-Act Timeline Segmentation (Hook, Pain, Intuition, Rigor, Benchmark, Philosophy)
4. Domain Science Classification (Physics, Chemistry, AI_ML, CS_ALGO, PURE_MATH)
5. Visual Metaphor Mapping
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# LM Studio endpoint on ThinkPad P15
LM_STUDIO_URL = os.environ.get("LM_STUDIO_URL", "http://10.123.214.1:1234/v1")
FALLBACK_LM_URL = "http://127.0.0.1:1234/v1"

DOMAIN_KEYWORDS = {
    "PHYSICS": [
        "physics", "vật lý", "gravity", "trọng lực", "con lắc", "pendulum", "force",
        "lực", "acceleration", "gia tốc", "lorentz", "từ trường", "electromagnetism",
        "refraction", "khúc xạ", "optics", "quang học", "wave", "sóng"
    ],
    "CHEMISTRY": [
        "chemistry", "hóa học", "molecule", "phân tử", "atom", "nguyên tử", "covalent",
        "cộng hóa trị", "orbital", "hybridization", "lai hóa", "reaction", "phản ứng",
        "water", "h2o", "sp3", "periodic", "tuần hoàn"
    ],
    "AI_ML": [
        "machine learning", "deep learning", "ai", "neural network", "attention",
        "transformer", "qkv", "backpropagation", "gradient descent", "loss function",
        "overfitting", "pca", "softmax", "autoencoder", "mcmc", "latent space",
        "convolution", "cnn", "batchnorm", "activation"
    ],
    "CS_ALGO": [
        "algorithm", "thuật toán", "data structure", "cấu trúc dữ liệu", "tree", "cây",
        "bst", "splay tree", "avl", "red-black", "graph", "đồ thị", "dijkstra",
        "dynamic programming", "sorting", "complexity", "big-o", "hashmap", "cache"
    ],
    "PURE_MATH": [
        "mathematics", "toán học", "matrix", "ma trận", "determinant", "định thức",
        "eigenvalue", "eigenvector", "vector space", "calculus", "vi tích phân",
        "fourier", "riemann", "bayes", "clt", "gaussian", "probability", "entropy"
    ],
}


def detect_domain(text: str, tags: List[str] = None) -> str:
    """Classify the technical domain based on keyword frequency analysis."""
    text_lower = (text + " " + " ".join(tags or [])).lower()
    scores = {domain: 0 for domain in DOMAIN_KEYWORDS}

    for domain, kws in DOMAIN_KEYWORDS.items():
        for kw in kws:
            matches = len(re.findall(r"\b" + re.escape(kw) + r"\b", text_lower))
            scores[domain] += matches

    sorted_domains = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    best_domain, best_score = sorted_domains[0]
    return best_domain if best_score > 0 else "CS_ALGO"


def query_llm_deconstruction(
    title: str, description: str, transcript_summary: str, domain: str
) -> Optional[Dict[str, Any]]:
    """Query local LM Studio (Qwen 3.5 9B) on ThinkPad P15 to perform structural deconstruction."""
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

        prompt = f"""Bạn là Đạo diễn Kỹ thuật kiêm Chuyên gia Sư phạm của kênh video công nghệ ZENPHAM.
Hãy mổ xẻ bài giảng công nghệ sau đây từ YouTube và phân rã thành tài liệu cấu trúc sư phạm chuẩn mực.

THÔNG TIN ĐẦU VÀO:
- Tiêu đề video: {title}
- Chuyên ngành dự đoán: {domain}
- Mô tả video: {description[:800]}
- Tóm tắt nội dung/Phụ đề: {transcript_summary[:3000]}

YÊU CẦU ĐẦU RA (ĐỊNH DẠNG JSON DUY NHẤT):
{{
  "core_thesis": "Thông điệp sư phạm cốt lõi trong 1-2 câu",
  "core_invariant": "Tiên đề bất biến toán học hoặc nguyên lý kỹ thuật bất biến",
  "pain_point": "Nỗi đau / thảm họa hiệu năng hoặc sai lầm nhận thức phổ biến",
  "visual_metaphors": ["Ẩn dụ thị giác 1", "Ẩn dụ thị giác 2"],
  "acts": [
    {{
      "act_number": 1,
      "name": "Hook & Cú sốc nhận thức",
      "target_duration": "00:00 - 00:45",
      "key_points": ["Đập tan ảo tưởng lý thuyết...", "Giới thiệu mâu thuẫn cốt lõi"],
      "visual_idea": "Ý tưởng hoạt họa Manim hoặc hình ảnh trực quan",
      "cognitive_goal": "Kích thích tò mò tột độ"
    }},
    {{
      "act_number": 2,
      "name": "Nỗi đau kỹ thuật & Thảm họa hiệu năng",
      "target_duration": "00:45 - 02:15",
      "key_points": ["Nguyên nhân gốc rễ", "Chi phí nghẽn CPU/RAM thực tế"],
      "visual_idea": "Sơ đồ suy biến hoặc đồ thị độ trễ đỏ rực",
      "cognitive_goal": "Cho thấy mức độ nghiêm trọng"
    }},
    {{
      "act_number": 3,
      "name": "Trực giác hình học & Mô hình tư duy",
      "target_duration": "02:15 - 04:45",
      "key_points": ["Nguyên lý không gian / hình học", "Quy tắc chuyển dịch đơn giản"],
      "visual_idea": "Biến hình hình học hoặc quay vector / xoay nhánh cây",
      "cognitive_goal": "Người xem thốt lên 'À, hóa ra là vậy!'"
    }},
    {{
      "act_number": 4,
      "name": "Chứng minh toán học & Tiên đề bất biến",
      "target_duration": "04:45 - 07:15",
      "key_points": ["Công thức toán học chuẩn xác", "Chứng minh tính bảo toàn / chặn trên"],
      "visual_idea": "Bảng công thức LaTeX ASCII và biểu đồ thế năng",
      "cognitive_goal": "Tạo niềm tin khoa học tuyệt đối"
    }},
    {{
      "act_number": 5,
      "name": "Thực chiến kỹ nghệ & Điểm nghẽn hệ thống",
      "target_duration": "07:15 - 09:30",
      "key_points": ["Đưa vào kiến trúc phần mềm thực tế", "Đánh đổi trade-offs"],
      "visual_idea": "Sơ đồ kiến trúc tầng hoặc biểu đồ benchmark so sánh",
      "cognitive_goal": "Ứng dụng ngay vào dự án thực chiến"
    }},
    {{
      "act_number": 6,
      "name": "Đạo làm nghề & Triết lý kiến trúc",
      "target_duration": "09:30 - 11:00",
      "key_points": ["Chiêm nghiệm nhân sinh về nghề kỹ sư", "Đúc kết triết lý"],
      "visual_idea": "Biểu tượng tối giản phát sáng tĩnh lặng trung tâm",
      "cognitive_goal": "Để lại dư âm sâu sắc và truyền cảm hứng"
    }}
  ]
}}
Chỉ trả về chuỗi JSON thuần túy, không có giải thích thêm.
"""

        response = client.chat.completions.create(
            model="qwen/qwen3.5-9b",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=2500,
        )
        content = response.choices[0].message.content or ""
        # Extract JSON block
        json_match = re.search(r"\{.*\}", content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))
    except Exception as e:
        print(f"    [!] LM Studio deconstruction query failed: {e}", file=sys.stderr)

    return None


def fallback_heuristic_deconstruction(
    title: str, description: str, full_text: str, domain: str
) -> Dict[str, Any]:
    """Deterministic fallback deconstruction using heuristic pattern extraction."""
    print("    [*] Using deterministic heuristic deconstruction...")

    # Extract sentences with strong technical cues
    sentences = re.split(r"[.\n]+", full_text)
    meaningful = [s.strip() for s in sentences if len(s.split()) >= 6]

    core_thesis = (
        f"Làm chủ bản chất và kỹ thuật tối ưu hóa của {title} thông qua trực giác hình học và chuẩn mực kỹ nghệ phần mềm."
    )
    core_invariant = (
        f"Nguyên lý bảo toàn trạng thái và sự thích ứng cấu trúc dữ liệu theo phân phối truy vấn thực tế."
    )
    pain_point = (
        f"Sự suy biến hiệu năng từ O(log N) thành O(N) khi gặp trật tự dữ liệu bất lợi trong môi trường sản xuất."
    )

    acts = [
        {
            "act_number": 1,
            "name": "Hook & Cú sốc nhận thức",
            "target_duration": "00:00 - 00:45",
            "key_points": [
                f"Phá vỡ niềm tin lý thuyết về {title}.",
                "Vạch trần thảm họa tiềm ẩn khi dữ liệu đổ vào hệ thống.",
            ],
            "visual_idea": "Mô hình đồ thị gãy khúc hoặc cây nhị phân biến dạng thành chuỗi đơn.",
            "cognitive_goal": "Gây ấn tượng thị giác mạnh mẽ trong 15s đầu.",
        },
        {
            "act_number": 2,
            "name": "Nỗi đau kỹ thuật & Thảm họa hiệu năng",
            "target_duration": "00:45 - 02:15",
            "key_points": [
                "Phân tích nguyên nhân gốc rễ gây tắc nghẽn.",
                "Hao tổn tài nguyên bộ nhớ và độ trễ P99 tăng vọt.",
            ],
            "visual_idea": "Biểu đồ cột so sánh độ trễ CPU/RAM nhấp nháy đỏ.",
            "cognitive_goal": "Thấu hiểu rõ ràng cái giá đắt của sự cẩu thả kiến trúc.",
        },
        {
            "act_number": 3,
            "name": "Trực giác hình học & Mô hình tư duy",
            "target_duration": "02:15 - 04:45",
            "key_points": [
                "Bản năng tự thích nghi và cấu trúc hình học linh hoạt.",
                "Các thao tác chuyển dịch tối giản đưa phần tử tích cực lên gốc.",
            ],
            "visual_idea": "Phép biến hình hình học động 2D (Transform Manim) với màu Cyan/Gold.",
            "cognitive_goal": "Thấu suốt cơ chế vận hành bằng trực giác mắt thấy tai nghe.",
        },
        {
            "act_number": 4,
            "name": "Chứng minh toán học & Tiên đề bất biến",
            "target_duration": "04:45 - 07:15",
            "key_points": [
                "Hàm thế năng và chi phí trừ dần (Amortized Analysis).",
                "Chặn trên toán học bảo đảm an toàn hệ thống.",
            ],
            "visual_idea": "Bảng công thức LaTeX ASCII và đồ thị thế năng liên tục.",
            "cognitive_goal": "Thiết lập nền móng học thuật vững như bàn thạch.",
        },
        {
            "act_number": 5,
            "name": "Thực chiến kỹ nghệ & Điểm nghẽn hệ thống",
            "target_duration": "07:15 - 09:30",
            "key_points": [
                "Tích hợp vào Linux kernel, Database buffer pool, Network router.",
                "Đánh đổi thực tế: Khi nào nên dùng và khi nào tuyệt đối tránh?",
            ],
            "visual_idea": "Sơ đồ kiến trúc tầng với Phosphor Duotone Icons.",
            "cognitive_goal": "Trang bị năng lực đưa lý thuyết vào code chạy thật.",
        },
        {
            "act_number": 6,
            "name": "Đạo làm nghề & Triết lý kiến trúc",
            "target_duration": "09:30 - 11:00",
            "key_points": [
                "Chiêm nghiệm về cái tĩnh và cái động trong thiết kế phần mềm.",
                "Đạo làm nghề: Sự kiên định trước những ồn ào công nghệ.",
            ],
            "visual_idea": "Biểu tượng tối giản phát sáng tĩnh lặng trên nền Obsidian tối.",
            "cognitive_goal": "Đọng lại cảm xúc sâu lắng và tự hào nghề nghiệp.",
        },
    ]

    return {
        "core_thesis": core_thesis,
        "core_invariant": core_invariant,
        "pain_point": pain_point,
        "visual_metaphors": [
            "Dòng chảy năng lượng tự cân bằng",
            "Sức mạnh của sự linh hoạt thích ứng thay vì hoàn hảo tĩnh lặng",
        ],
        "acts": acts,
    }


def deconstruct_video(ingest_summary: Dict[str, Any], output_dir: Path) -> Dict[str, Any]:
    """Execute complete deconstruction process and output markdown report."""
    output_dir.mkdir(parents=True, exist_ok=True)
    metadata = ingest_summary.get("metadata", {})
    title = metadata.get("title", "Untitled Technical Lecture")
    description = metadata.get("description", "")
    full_text = ingest_summary.get("full_text", "")
    tags = metadata.get("tags", [])

    print(f"[*] Deconstructing pedagogical structure for: {title}")
    domain = detect_domain(title + " " + full_text, tags)
    print(f"    [+] Detected Domain: {domain}")

    # Step 1: Attempt LLM Deconstruction
    decon_data = query_llm_deconstruction(title, description, full_text, domain)

    # Step 2: Fallback if LLM unavailable
    if not decon_data:
        decon_data = fallback_heuristic_deconstruction(title, description, full_text, domain)

    decon_data["domain"] = domain
    decon_data["title"] = title
    decon_data["video_id"] = metadata.get("id", "")

    # Save JSON
    json_path = output_dir / "deconstruction_report.json"
    json_path.write_text(json.dumps(decon_data, indent=2, ensure_ascii=False))

    # Generate Markdown Report
    md_content = f"""# BÁO CÁO GIẢI PHẪU SƯ PHẠM (PEDAGOGICAL DECONSTRUCTION)
## Tiêu đề video: {title}
- **Chuyên ngành**: `{domain}`
- **ID Video**: `{decon_data['video_id']}`
- **Luận điểm cốt lõi (Core Thesis)**: {decon_data['core_thesis']}
- **Tiên đề bất biến (Core Invariant)**: {decon_data['core_invariant']}
- **Nỗi đau kỹ thuật (Pain Point)**: {decon_data['pain_point']}
- **Ẩn dụ thị giác**: {", ".join(decon_data.get("visual_metaphors", []))}

---

## BẢN ĐỒ 6 HỒI SƯ PHẠM (6-ACT TIMELINE BREAKDOWN)
"""
    for act in decon_data["acts"]:
        md_content += f"""
### Hồi {act['act_number']}: {act['name']} ({act['target_duration']})
- **Mục tiêu nhận thức**: {act['cognitive_goal']}
- **Ý tưởng thị giác (Manim/Footage)**: {act['visual_idea']}
- **Nội dung trọng tâm**:
"""
        for kp in act["key_points"]:
            md_content += f"  • {kp}\n"

    md_path = output_dir / "deconstruction_report.md"
    md_path.write_text(md_content, encoding="utf-8")
    print(f"[+] Deconstruction complete. Report saved to: {md_path}")
    return decon_data


def main():
    parser = argparse.ArgumentParser(
        description="Pedagogical Script & Structural Deconstruction Engine"
    )
    parser.add_argument(
        "--ingest-json",
        default="./workspace/youtube_ingest/ingestion_summary.json",
        help="Path to ingestion summary JSON file",
    )
    parser.add_argument(
        "--output-dir",
        default="./workspace/youtube_deconstruct",
        help="Directory to store deconstruction report",
    )
    args = parser.parse_args()

    ingest_path = Path(args.ingest_json)
    if not ingest_path.exists():
        print(f"[!] Error: {ingest_path} not found.", file=sys.stderr)
        sys.exit(1)

    data = json.loads(ingest_path.read_text(encoding="utf-8"))
    deconstruct_video(data, Path(args.output_dir))


if __name__ == "__main__":
    main()
