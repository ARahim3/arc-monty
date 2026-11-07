#!/usr/bin/env bash
ARC_MONTY_ROOT=${ARC_MONTY_ROOT:-$(cd "$(dirname "$0")/../../.." && pwd)}  # repo root
# Laptop side: ship llm/ (code + existing results) + eval data + research/arc2 to the VM and start setup+download in tmux.
#   Z=europe-west4-a VM=arc-v6e research/arc2/vm/ship.sh [start]
set -euo pipefail
Z=${Z:-europe-west4-a}; VM=${VM:-arc-v6e}; ROOT=$ARC_MONTY_ROOT
TGZ=$(mktemp -d)/a2.tgz
cd $ROOT && COPYFILE_DISABLE=1 tar --exclude=__pycache__ --exclude='*.DS_Store' --exclude=logs --exclude=results_archive \
  --exclude=xla_cache_store --exclude='*.ids.jsonl' -czf $TGZ llm research/arc2 data/kaggle_format/agi2_eval_challenges.json \
  data/kaggle_format/agi2_eval_solutions.json
gcloud compute tpus tpu-vm scp $TGZ $VM:/tmp/a2.tgz --zone=$Z
gcloud compute tpus tpu-vm ssh $VM --zone=$Z --command='sudo mkdir -p /mnt/data && sudo chown $USER:$USER /mnt/data && mkdir -p /mnt/data/arc_monty /mnt/data/logs && tar -xzf /tmp/a2.tgz -C /mnt/data/arc_monty && echo shipped'
if [ "${1:-}" = start ]; then
  gcloud compute tpus tpu-vm ssh $VM --zone=$Z --command='command -v tmux >/dev/null || (sudo apt-get update -qq && sudo apt-get install -y -qq tmux >/dev/null); cd /mnt/data/arc_monty && (tmux has-session -t a2 2>/dev/null && echo "a2 already running") || tmux new-session -d -s a2 "bash research/arc2/vm/run_arc2.sh 2>&1 | tee -a /mnt/data/logs/arc2.log"; tmux ls'
fi
