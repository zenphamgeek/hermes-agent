#!/usr/bin/env python3
"""ZENPHAM script validator: format, topic duplication, philosopher density."""
import argparse, json, re
from pathlib import Path

SCRIPT_ROOT = Path("/home/zen/hermes-agent/assets/scripts_video")
REGISTRY = SCRIPT_ROOT / "topic_registry.json"
PHILOSOPHERS = (
    "Epictetus", "Sartre", "Camus", "Frankl", "Nietzsche", "Kierkegaard",
    "Arendt", "Heidegger", "Thích Nhất Hạnh", "Marcus Aurelius", "Seneca",
    "Lão Tử", "Trang Tử", "Phật",
)
STOPWORDS = {
    "va", "la", "cua", "nhung", "nhung", "voi", "trong", "mot", "nhung", "nhung",
    "cho", "nguoi", "minh", "nhung", "the", "nhung", "tai", "khi", "khong", "duoc",
}


def words(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-zA-ZÀ-ỹĐđ]{3,}", text.lower()) if w not in STOPWORDS}


def load_registry(registry_path: Path = REGISTRY) -> list[dict]:
    if not registry_path.exists():
        return []
    return json.loads(registry_path.read_text(encoding="utf-8")).get("topics", [])


def script_title(text: str) -> str:
    m = re.search(r'Kịch bản video ZENPHAM\s*[—-]\s*"(.+?)"', text)
    return m.group(1).strip() if m else ""


def core_topic_text(text: str) -> str:
    m = re.search(r"Chủ đề:\s*(.+)", text)
    return m.group(1).strip() if m else script_title(text)


def named_philosophers(text: str) -> list[str]:
    return [name for name in PHILOSOPHERS if re.search(rf"(?<!\w){re.escape(name)}(?!\w)", text, re.I)]


def max_philosophers(total_sec: int) -> int:
    """Names, not schools. One needs ~45s narrative room; cap protects depth."""
    if total_sec <= 90:
        return 1
    if total_sec <= 150:
        return 2
    return 3


def topic_overlap(candidate: str, published: dict) -> float:
    a = words(candidate)
    b = words(" ".join([published.get("title", ""), published.get("core_thesis", ""), " ".join(published.get("angles", []))]))
    return len(a & b) / max(1, len(a | b))


def validate_script(md_path: Path, registry_path: Path = REGISTRY) -> dict:
    """Validate format, topic novelty, philosopher density. Returns result dict."""
    text = md_path.read_text(encoding="utf-8")
    errors, warnings = [], []
    blocks = re.split(r"\nĐoạn \d+:", text)[1:]
    n = len(blocks)
    if n < 8:
        errors.append(f"Only {n} scenes, minimum 8")
    elif n > 20:
        errors.append(f"{n} scenes, maximum 20")
    total_sec = n * 10

    for i, block in enumerate(blocks, 1):
        if not re.search(r'Lời thoại:.*?"(.+?)"', block, re.S):
            errors.append(f"Scene {i}: missing Lời thoại with quoted dialogue")
        if not re.search(r"\[Pexels keywords:", block):
            warnings.append(f"Scene {i}: missing [Pexels keywords:]")
    if not re.search(r"Phong cách:\s*Cinematic Noir", text):
        warnings.append("Missing 'Phong cách: Cinematic Noir'")
    if not re.search(r"Giọng:\s*Sang Truong", text):
        warnings.append("Missing 'Giọng: Sang Truong (OmniVoice)'")
    if not re.search(r"END_TITLE:", text):
        warnings.append("Missing END_TITLE")

    philosophers = named_philosophers(text)
    philosopher_cap = max_philosophers(total_sec)
    if len(philosophers) > philosopher_cap:
        errors.append(
            f"{len(philosophers)} philosopher names for {total_sec}s; limit is {philosopher_cap}: "
            + ", ".join(philosophers)
        )

    topic = core_topic_text(text)
    overlaps = []
    for previous in load_registry(registry_path):
        if previous.get("script") == md_path.name:
            continue
        score = topic_overlap(topic, previous)
        if score >= 0.18:
            overlaps.append((previous.get("title", "untitled"), score))
    if overlaps:
        matches = ", ".join(f"{title} ({score:.0%})" for title, score in overlaps)
        errors.append(f"Topic overlaps produced work: {matches}. Pick a distinct thesis/angle.")

    return {
        "title": script_title(text),
        "topic": topic,
        "n_scenes": n,
        "total_sec": total_sec,
        "total_min": total_sec / 60,
        "philosophers": philosophers,
        "philosopher_cap": philosopher_cap,
        "overlaps": overlaps,
        "errors": errors,
        "warnings": warnings,
    }


def register_script(md_path: Path, registry_path: Path = REGISTRY) -> None:
    result = validate_script(md_path, registry_path)
    if result["errors"]:
        raise ValueError("Cannot register invalid script: " + "; ".join(result["errors"]))
    data = json.loads(registry_path.read_text(encoding="utf-8")) if registry_path.exists() else {"channel": "ZENPHAM", "topics": []}
    item = {
        "id": re.sub(r"[^a-z0-9]+", "-", result["title"].lower().replace("đ", "d")).strip("-"),
        "status": "scripted",
        "title": result["title"],
        "core_thesis": result["topic"],
        "angles": sorted(words(result["topic"])),
        "philosophers": result["philosophers"],
        "script": md_path.name,
        "duration_seconds": result["total_sec"],
    }
    data.setdefault("topics", []).append(item)
    registry_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("script", type=Path)
    p.add_argument("--registry", type=Path, default=REGISTRY)
    p.add_argument("--register", action="store_true", help="Append validated topic as scripted")
    args = p.parse_args()
    if not args.script.exists():
        p.error(f"File not found: {args.script}")
    result = validate_script(args.script, args.registry)
    print(f"Scenes: {result['n_scenes']} ({result['total_sec']}s = {result['total_min']:.1f}min)")
    print(f"Philosophers: {len(result['philosophers'])}/{result['philosopher_cap']} — {', '.join(result['philosophers']) or 'none'}")
    for e in result["errors"]:
        print(f"  ERROR: {e}")
    for w in result["warnings"]:
        print(f"  WARN: {w}")
    if result["errors"]:
        raise SystemExit(1)
    if args.register:
        register_script(args.script, args.registry)
        print(f"Registered: {result['title']}")

if __name__ == "__main__":
    main()