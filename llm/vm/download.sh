#!/usr/bin/env bash
# Download both models (bf16) into tmpfs. Ingress is free. Usage: download.sh [qwen38|nanbeige|all]
set -euo pipefail
source /mnt/data/envs/vllm/bin/activate
export HF_HUB_ENABLE_HF_TRANSFER=0 HF_XET_HIGH_PERFORMANCE=1
WHICH=${1:-all}
dl() { local repo=$1 dir=$2
  if [ -f "$dir/.complete" ]; then echo "$repo already in $dir"; return; fi
  t=$(date +%s); hf download "$repo" --local-dir "$dir" --exclude "figures/*" >/dev/null
  touch "$dir/.complete"; echo "$repo -> $dir in $(( $(date +%s) - t ))s, $(du -sh "$dir" | cut -f1)"; }
[ "$WHICH" = all -o "$WHICH" = qwen38 ] && dl Qwen/Qwen3.8-27B /mnt/data/ram/models/qwen38
[ "$WHICH" = nanbeige ] && dl Nanbeige/Nanbeige4.3-33B /mnt/data/ram/models/nanbeige
ls /mnt/data/ram/models; df -h /mnt/data/ram | tail -1
