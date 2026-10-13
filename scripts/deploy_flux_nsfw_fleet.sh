#!/usr/bin/env bash
# scripts/deploy_flux_nsfw_fleet.sh
# ==================================
# Deploy FLUX.1 Fill [dev] + NSFW LoRA ComfyUI Workers across top quota Modal nodes.

set -euo pipefail

WORKSPACE_TARGETS=("pvvsf" "asmr" "vi2vi")
MODAL_BIN="/home/zen/hermes-agent/.venv/bin/modal"
APP_FILE="skills/creative/modal-comfyui/modal_flux_fill_nsfw.py"

echo "======================================================================"
echo "🚀 [Modal Fleet] Deploying 3x FLUX.1 Fill [dev] NSFW Workers"
echo "Target Nodes (High Quota / Active): ${WORKSPACE_TARGETS[*]}"
echo "======================================================================"

DEPLOY_LOGS_DIR="output/modal_deploy_logs"
mkdir -p "$DEPLOY_LOGS_DIR"

for WS in "${WORKSPACE_TARGETS[@]}"; do
    echo ""
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
