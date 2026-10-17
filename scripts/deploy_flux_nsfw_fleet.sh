#!/usr/bin/env bash
# scripts/deploy_flux_nsfw_fleet.sh
# ==================================
# Deploy FLUX.1 Fill [dev] + NSFW LoRA ComfyUI Workers across top quota Modal nodes.

set -euo pipefail

WORKSPACE_TARGETS=("nhatrophamvu" "pvvsf" "asmr" "vi2vi")
MODAL_BIN="/home/zen/hermes-agent/.venv/bin/modal"
APP_FILE="skills/creative/modal-comfyui/modal_flux_fill_nsfw.py"

if [[ $# -gt 0 ]]; then
    WORKSPACE_TARGETS=("$@")
fi

echo "======================================================================"
echo "🚀 [Modal Fleet] Deploying FLUX.1 Fill [dev] NSFW Workers"
echo "Target Nodes (High Quota / Active): ${WORKSPACE_TARGETS[*]}"
echo "======================================================================"

DEPLOY_LOGS_DIR="output/modal_deploy_logs"
mkdir -p "$DEPLOY_LOGS_DIR"

for WS in "${WORKSPACE_TARGETS[@]}"; do
    echo ""
    # Invariant Guard: CWE-20 / CWE-78 Alphanumeric Workspace Identifier Validation
    if [[ ! "$WS" =~ ^[a-zA-Z0-9_-]+$ ]]; then
        echo "[SECURITY ERROR] CWE-20 Invalid workspace identifier: $WS" >&2
        exit 1
    fi
    echo "▶️ [Pre-Flight Credit Gate] Checking Workspace Profile: $WS (> \$15.00 required)"
    if ! python3 tools/modal_budget_guard.py check --profile "$WS" --action deploy; then
        echo "⛔ Skipping $WS due to Modal Credit Gate Violation."
        continue
    fi
    echo "▶️ [Deploying Worker] Target Workspace Profile: $WS"
    LOG_FILE="$DEPLOY_LOGS_DIR/deploy_${WS}_$(date +%Y%m%d_%H%M%S).log"
    
    # Run modal deploy under the target workspace profile
    MODAL_PROFILE="$WS" "$MODAL_BIN" deploy "$APP_FILE" 2>&1 | tee "$LOG_FILE" || {
        echo "⚠️ Deployment to $WS returned non-zero. Check $LOG_FILE for details."
    }
done

echo ""
echo "======================================================================"
echo "✅ [Deployment Complete] Auditing Active Deployed Apps..."
echo "======================================================================"

for WS in "${WORKSPACE_TARGETS[@]}"; do
    echo ""
    echo "🔍 Workspace: $WS"
    MODAL_PROFILE="$WS" "$MODAL_BIN" app list 2>&1 | grep -E "hermes-flux-fill-nsfw|Description" || true
done
