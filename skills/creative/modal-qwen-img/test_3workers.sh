#!/bin/bash
# test_3workers.sh — Fire 3 real Gray Doom image generation requests
# across 3 deployed Qwen-Image-2.1 A100 workers
# Usage: bash test_3workers.sh

set -euo pipefail

OUT_DIR="/tmp/qwen_a100_test_$(date +%s)"
mkdir -p "$OUT_DIR"

PROMPT_1="Atlantic Coalition Harbor Guard infantry, matte coastal blue power armor, photorealistic tactical sci-fi 8K, dramatic cinematic lighting, ultra detailed"
PROMPT_2="Northern Bloc Winter Recon operative, titanium frost white stealth suit, frozen tundra background, military sci-fi concept art, photorealistic"
PROMPT_3="Eastern Collective Heavy Siege Artillery mech, imperial jade green chassis, twin accelerator cannons, wasteland battleground, hyper-detailed 8K render"

W1="https://verticalresilience--hermes-qwen-img-21-qwenimg21worker-generate.modal.run"
W2="https://zenmaster--hermes-qwen-img-21-qwenimg21worker-generate.modal.run"
W3="https://r2rgraph--hermes-qwen-img-21-qwenimg21worker-generate.modal.run"

echo "🔥 Firing 3 real A100 inference requests in parallel..."
echo "Output dir: $OUT_DIR"
echo ""

fire_request() {
  local worker_url="$1"
  local prompt="$2"
  local out_file="$3"
  local label="$4"

  echo "[$label] POST → $worker_url"
  START=$(date +%s)

  RESPONSE=$(curl -sf -X POST "$worker_url" \
    -H "Content-Type: application/json" \
    -d "{
      \"prompt\": \"$prompt\",
      \"steps\": 40,
      \"guidance_scale\": 5.0,
      \"seed\": 8101,
      \"aspect_ratio\": \"16:9\"
    }" 2>&1)

  EXIT=$?
  END=$(date +%s)
  ELAPSED=$((END - START))

  if [ $EXIT -ne 0 ]; then
    echo "[$label] ❌ FAILED after ${ELAPSED}s — $RESPONSE"
    return 1
  fi

  SUCCESS=$(echo "$RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('success','false'))" 2>/dev/null || echo "false")
  
  if [ "$SUCCESS" != "True" ]; then
    echo "[$label] ❌ Worker returned success=false"
    echo "$RESPONSE" | python3 -m json.tool 2>/dev/null | head -20
    return 1
  fi

  # Decode base64 PNG
  echo "$RESPONSE" | python3 -c "
import sys, json, base64
d = json.load(sys.stdin)
b64 = d['b64_json']
png = base64.b64decode(b64)
with open('$out_file', 'wb') as f:
    f.write(png)
print(f'[$label] ✅ Saved {len(png):,} bytes → $out_file')
print(f'[$label] Resolution: {d[\"resolution\"]} | Steps: {d[\"steps\"]} | Elapsed: ${ELAPSED}s | Model: {d[\"model\"]}')
"
}

# Fire all 3 in parallel
fire_request "$W1" "$PROMPT_1" "$OUT_DIR/worker1_atlantic_guard.png"   "W1-verticalresilience" &
fire_request "$W2" "$PROMPT_2" "$OUT_DIR/worker2_northern_recon.png"   "W2-zenmaster"          &
fire_request "$W3" "$PROMPT_3" "$OUT_DIR/worker3_eastern_artillery.png" "W3-r2rgraph"          &

wait

echo ""
echo "=== RESULTS ==="
for f in "$OUT_DIR"/*.png; do
  if [ -f "$f" ]; then
    SIZE=$(wc -c < "$f")
    echo "✅ $(basename $f) — ${SIZE} bytes"
    # Validate it's a real PNG (first 8 bytes = PNG magic)
    MAGIC=$(xxd -l 8 "$f" | head -1)
    echo "   PNG magic: $MAGIC"
  fi
done
echo "Files in: $OUT_DIR"
