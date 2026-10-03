#!/usr/bin/env python3
"""
Formalize Vietnamese Dharma Transcript for High Quality TTS Narration
----------------------------------------------------------------------
Cleans YouTube ASR artifacts, fixes Vietnamese spelling/homophone errors,
formats punctuation and sentences for natural audiobook reading.
"""

import concurrent.futures
import json
import logging
import os
import re
import sys
import time
import urllib.request
from pathlib import Path
from typing import List, Tuple

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("formalize_text")

LLM_ENDPOINT = os.environ.get("LLM_ENDPOINT", "http://localhost:20128/v1/chat/completions")
LLM_API_KEY = os.environ.get("LLM_API_KEY", "sk-2cf84041b445dfaf-dzzetv-8159ccdf")
LLM_MODEL = os.environ.get("LLM_MODEL", "codex")

SYSTEM_PROMPT = """Bạn là chuyên gia biên tập và chuẩn hóa văn bản tiếng Việt cao cấp, chuyên phục vụ giọng đọc Thính Pháp Âm / Audiobooks truyền cảm, sâu lắng.

Nhiệm vụ của bạn:
1. Xóa sạch mọi thẻ âm thanh YouTube như: [âm nhạc], [vỗ tay], [tiếng cười], (nhạc), v.v.
2. Sửa triệt để các lỗi nhận diện giọng nói (ASR/chính tả sai) trong tiếng Việt. Ví dụ:
   - "chật giật" -> "chật vật"
   - "tâm ươm" / "tâm ôn" -> "tâm ôm"
   - "tích lo" -> "ít lo"
   - "bám chất" -> "bám chấp"
   - "bỗng tay" -> "bỏng tay"
   - "nước lắn" -> "nước lắng"
   - "trước do" -> "trước gió"
   - "chuyền nhỏ" -> "chuyện nhỏ"
   - "khắc nhiệt" -> "khắc nghiệt"
   - "tích tù" -> "tích tụ"
   - "đôi tây" -> "đôi tay"
   - "tâm họ chiếu" -> "tâm họ chứa"
   - "bừng tĩnh" -> "bừng tỉnh"
   - "mãi miết" -> "mải miết"
   - "Đỗi khổ" -> "Nỗi khổ"
   - "mức mình có thể ôn" -> "mức mình có thể ôm"
   - "suô sẻ" -> "suôn sẻ"
   - "được nghĩ" -> "được nghỉ"
   - "người biết buôn" -> "người biết buông"
   - "bàn hít vào" -> "bạn hít vào"
   - "xuất hành trình" -> "suốt hành trình"
   - "trời cành" -> "rời cành"
   - "càng dữ lại càng mỏi mệt" -> "càng giữ lại càng mỏi mệt"
   - "bỏ mặt" -> "bỏ mặc"
   - "trặn trọc" -> "trằn trọc"
   - "nếu lấy điều đã qua" -> "níu lấy điều đã qua"
3. Chuyển đổi toàn bộ chữ số thành chữ tiếng Việt (ví dụ: "1 2 giờ sáng" -> "một, hai giờ sáng", "10" -> "mười", "100%" -> "một trăm phần trăm").
4. Ghép nối các dòng bị cắt vụn thành các câu văn và đoạn văn hoàn chỉnh, ngắt câu chuẩn xác với dấu chấm, dấu phẩy, dấu chấm hỏi, dấu ngoặc kép phù hợp với nhịp thở của người đọc.
5. Giữ nguyên vẹn 100% nội dung, ý tứ và tinh thần bài giảng Phật pháp, tuyệt đối không cắt bớt nội dung và không tự ý bịa thêm nội dung mới.
6. Chỉ trả về trực tiếp đoạn văn bản tiếng Việt đã được chuẩn hóa, không kèm bất kỳ lời dẫn, giải thích hay định dạng markdown code block nào.
"""

def call_llm_formalize(batch_text: str, batch_idx: int, total_batches: int, retry_count: int = 3) -> str:
    user_prompt = f"Hãy chuẩn hóa và sửa lỗi đoạn văn sau cho giọng đọc Thính Pháp Âm:\n\n{batch_text}"
    payload = {
        "model": LLM_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.2,
    }
    data_bytes = json.dumps(payload).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LLM_API_KEY}"
    }

    for attempt in range(retry_count + 1):
        try:
            req = urllib.request.Request(LLM_ENDPOINT, data=data_bytes, headers=headers)
            with urllib.request.urlopen(req, timeout=60) as resp:
                res_json = json.loads(resp.read().decode("utf-8"))
                content = res_json["choices"][0]["message"]["content"].strip()
                # Clean any markdown code blocks if LLM returned them
                content = re.sub(r"^```(?:markdown|text)?\s*", "", content)
                content = re.sub(r"\s*```$", "", content)
                return content.strip()
        except Exception as e:
            logger.warning(f"Batch [{batch_idx+1}/{total_batches}] attempt {attempt+1} failed: {e}")
            if attempt == retry_count:
                raise RuntimeError(f"Failed to formalize batch {batch_idx+1} after {retry_count} retries: {e}")
            time.sleep(2.0 * (attempt + 1))
    return ""


def partition_text(lines: List[str], target_lines_per_batch: int = 70) -> List[List[str]]:
    """Partition lines into logical chunks on natural pause boundaries."""
    batches = []
    current_batch = []
    
    for i, line in enumerate(lines):
        current_batch.append(line)
        # Check if we reached target lines and at a line that might end a sentence
        if len(current_batch) >= target_lines_per_batch:
            if line.endswith((".", "!", "?", "…")) or len(current_batch) >= target_lines_per_batch + 20 or i == len(lines) - 1:
                batches.append(current_batch)
                current_batch = []
                
    if current_batch:
        batches.append(current_batch)
    return batches


def formalize_file(input_file: Path, output_file: Path, max_workers: int = 4):
    start_time = time.time()
    raw_text = input_file.read_text(encoding="utf-8")
    lines = [l.strip() for l in raw_text.splitlines() if l.strip()]
    logger.info(f"Loaded {len(lines)} lines from {input_file.name} ({len(raw_text):,} chars)")

    batches = partition_text(lines, target_lines_per_batch=70)
    total_batches = len(batches)
    logger.info(f"Split into {total_batches} batches for parallel formalization (Workers: {max_workers})...")

    cache_dir = input_file.parent / ".formalize_cache" / input_file.stem
    cache_dir.mkdir(parents=True, exist_ok=True)

    results = [None] * total_batches
    tasks_to_run = {}

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        for idx, batch_lines in enumerate(batches):
            cache_file = cache_dir / f"batch_{idx:03d}.txt"
            if cache_file.exists() and cache_file.stat().st_size > 10:
                results[idx] = cache_file.read_text(encoding="utf-8").strip()
            else:
                batch_text = "\n".join(batch_lines)
                future = executor.submit(call_llm_formalize, batch_text, idx, total_batches)
                tasks_to_run[future] = (idx, cache_file)

        cached_count = sum(1 for r in results if r is not None)
        if cached_count > 0:
            logger.info(f"Loaded {cached_count}/{total_batches} batches from cache.")

        for future in concurrent.futures.as_completed(tasks_to_run):
            idx, cache_file = tasks_to_run[future]
            try:
                content = future.result()
                results[idx] = content
                cache_file.write_text(content, encoding="utf-8")
                done_count = sum(1 for r in results if r is not None)
                logger.info(f"Formalized [{done_count}/{total_batches}] batches ({done_count/total_batches*100:.1f}%)...")
            except Exception as e:
                logger.error(f"Error processing batch {idx+1}: {e}")
                raise e

    # Combine all formalized batches
    final_text = "\n\n".join(results).strip()
    # Normalize multiple blank lines
    final_text = re.sub(r"\n{3,}", "\n\n", final_text)
    
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(final_text, encoding="utf-8")

    elapsed = time.time() - start_time
    logger.info(f" [✓] Formalization completed in {elapsed:.1f}s!")
    logger.info(f"Output saved to: {output_file} ({len(final_text):,} chars, {len(final_text.split()):,} words)")
    return output_file


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Formalize transcript text for TTS.")
    parser.add_argument("input", help="Input transcript text file")
    parser.add_argument("-o", "--output", help="Output formalized text file")
    parser.add_argument("-w", "--workers", type=int, default=4, help="Concurrency workers")
    args = parser.parse_args()

    inp = Path(args.input)
    if not inp.exists():
        logger.error(f"Input file not found: {args.input}")
        sys.exit(1)

    out = Path(args.output) if args.output else inp.parent / f"{inp.stem.replace('.vi-orig', '')}.formalized.txt"
    formalize_file(inp, out, max_workers=args.workers)
