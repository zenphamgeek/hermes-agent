#!/usr/bin/env python3
"""
Topic Barrier Gate — Scientific Topic Differentiation & Anti-Cannibalization Engine.
Validates prospective video topics against completed episodes in topic_memory_graph.json.

Rules:
1. Semantic Similarity Gate:
   - S >= 0.85: HARD REJECT (Trùng lặp trực tiếp với tập đã có)
   - 0.65 <= S < 0.85: CONDITIONAL GATE (Chỉ duyệt nếu là Deep-dive Kỹ nghệ Production / Edge Cases)
   - S < 0.65: PASS (Đề tài mới hợp lệ)
2. Taxonomy Level Separation:
   - Series tiếp theo (Series 2) ưu tiên Level 3 (Kiến trúc & Động lực học LLM) và Level 4 (Kỹ nghệ Hệ thống).
3. Synthesis Exception:
   - Cho phép video tổng hợp nếu kết nối >= 3 tập đã có dưới một Đại hợp âm (Macro-narrative).
"""

import sys
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple

SCRIPT_DIR = Path(__file__).resolve().parent
GRAPH_FILE = SCRIPT_DIR.parent / "references/topic_memory_graph.json"


def load_memory_graph() -> Dict:
    if not GRAPH_FILE.exists():
        raise FileNotFoundError(f"Missing memory graph at {GRAPH_FILE}")
    with open(GRAPH_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def tokenize(text: str) -> set:
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    words = [w.strip() for w in text.split() if len(w.strip()) > 2]
    return set(words)


def compute_similarity(new_keywords: List[str], new_title: str, episode: Dict) -> Tuple[float, List[str]]:
    """Calculates weighted keyword & semantic overlap between candidate topic and completed episode."""
    new_set = set(k.lower() for k in new_keywords) | tokenize(new_title)
    ep_set = set(k.lower() for k in episode.get("keywords", [])) | tokenize(episode.get("title", ""))
    for th in episode.get("core_theorems", []):
        ep_set |= tokenize(th)

    if not new_set or not ep_set:
        return 0.0, []

    intersection = new_set & ep_set
    overlap_score = len(intersection) / min(len(new_set), len(ep_set))
    jaccard = len(intersection) / len(new_set | ep_set)
    # Composite similarity metric
    sim = 0.7 * overlap_score + 0.3 * jaccard
    return round(min(sim, 1.0), 3), sorted(list(intersection))


def evaluate_candidate_topic(candidate: Dict) -> Dict:
    """
    Candidate format:
    {
      "title": "...",
      "keywords": ["..."],
      "core_theorems": ["..."],
      "level": 3,
      "is_synthesis": False,
      "linked_episodes": []
    }
    """
    graph = load_memory_graph()
    title = candidate.get("title", "")
    keywords = candidate.get("keywords", [])
    level = candidate.get("level", 3)
    is_synthesis = candidate.get("is_synthesis", False)
    linked = candidate.get("linked_episodes", [])

    # Synthesis Exception Evaluation
    if is_synthesis:
        if len(linked) < 3:
            return {
                "decision": "REJECT",
                "reason": f"Video tổng hợp (Synthesis) yêu cầu liên kết tối thiểu 3 tập đã hoàn thành (hiện có: {len(linked)}).",
                "max_similarity": 0.0,
                "matches": [],
            }
        return {
            "decision": "PASS (SYNTHESIS)",
            "reason": f"Hợp lệ: Video tổng hợp kết nối {len(linked)} tập ({', '.join(str(e) for e in linked)}) dưới Đại hợp âm vĩ mô.",
            "max_similarity": 1.0,
            "matches": [],
        }

    matches = []
    max_sim = 0.0
    most_similar_ep = None

    for ep in graph.get("episodes", []):
        sim, shared = compute_similarity(keywords, title, ep)
        if sim > 0.25:
            matches.append({
                "ep": ep["ep"],
                "title": ep["title"],
                "similarity": sim,
                "shared_keywords": shared,
            })
        if sim > max_sim:
            max_sim = sim
            most_similar_ep = ep

    matches.sort(key=lambda x: x["similarity"], reverse=True)

    # 1. HARD REJECT
    if max_sim >= 0.85:
        return {
            "decision": "REJECT (DUPLICATION)",
            "reason": (
                f"Đề tài bị từ chối do trùng lặp quá gần với Tập {most_similar_ep['ep']:02d} "
                f"('{most_similar_ep['title']}', Độ tương đồng: {max_sim * 100:.1f}%). "
                f"Từ khóa xung đột: {', '.join(matches[0]['shared_keywords'][:5])}."
            ),
            "max_similarity": max_sim,
            "matches": matches[:3],
        }

    # 2. CONDITIONAL DEEP-DIVE
    if max_sim >= 0.65:
        return {
            "decision": "CONDITIONAL PASS (DEEP-DIVE)",
            "reason": (
                f"Đề tài có độ giao thoa đáng kể với Tập {most_similar_ep['ep']:02d} ({max_sim * 100:.1f}%). "
                f"Chỉ được phê duyệt nếu tập trung 100% vào Kỹ nghệ Thực chiến/Hệ thống cấp cao (Level {level}), "
                f"tuyệt đối không giảng lại các định nghĩa lý thuyết đã trình bày ở Tập {most_similar_ep['ep']:02d}."
            ),
            "max_similarity": max_sim,
            "matches": matches[:3],
        }

    # 3. PASS
    return {
        "decision": "PASS (NEW TOPIC)",
        "reason": f"Đề tài mới hoàn toàn hợp lệ. Độ tương đồng cao nhất là {max_sim * 100:.1f}% (dưới ngưỡng 65%).",
        "max_similarity": max_sim,
        "matches": matches[:3],
    }


def main():
    if len(sys.argv) < 2:
        print("Sử dụng: python topic_barrier_gate.py 'Tiêu đề đề xuất' [keyword1,keyword2,...]")
        sys.exit(1)

    title = sys.argv[1]
    keywords = sys.argv[2].split(",") if len(sys.argv) > 2 else []
    res = evaluate_candidate_topic({"title": title, "keywords": keywords})
    print(json.dumps(res, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
