#!/usr/bin/env bash
ARC_MONTY_ROOT=${ARC_MONTY_ROOT:-$(cd "$(dirname "$0")/../../.." && pwd)}  # repo root
# Laptop side: ship code + data + current results to a VM and start run_faloo.sh in tmux "fa".
#   Z=<zone> SHARD=k/N PHASES=A,B,C,D research/arc2/vm/ship_faloo.sh
set -euo pipefail
Z=${Z:-us-east1-d}; VM=${VM:-arc-v6e}; ROOT=$ARC_MONTY_ROOT
TGZ=$(mktemp -d)/fa.tgz
cd $ROOT && COPYFILE_DISABLE=1 tar --exclude=__pycache__ --exclude='*.DS_Store' --exclude=logs --exclude=results_archive \
  --exclude=xla_cache_store --exclude='*.ids.jsonl' -czf $TGZ llm research/arc2/*.py research/arc2/monty_hints.json research/arc2/vm \
  data/kaggle_format/agi2_eval_challenges.json data/kaggle_format/agi2_eval_solutions.json
gcloud compute tpus tpu-vm scp $TGZ $VM:/tmp/fa.tgz --zone=$Z
gcloud compute tpus tpu-vm ssh $VM --zone=$Z --command="sudo mkdir -p /mnt/data && sudo chown \$USER:\$USER /mnt/data && mkdir -p /mnt/data/arc_monty /mnt/data/logs && tar -xzf /tmp/fa.tgz -C /mnt/data/arc_monty && command -v tmux >/dev/null || (sudo apt-get update -qq && sudo apt-get install -y -qq tmux >/dev/null); cd /mnt/data/arc_monty && (tmux has-session -t fa 2>/dev/null && echo 'fa already running') || tmux new-session -d -s fa 'SHARD=${SHARD:-0/1} PHASES=${PHASES:-A,B,C,D} bash research/arc2/vm/run_faloo.sh 2>&1 | tee -a /mnt/data/logs/run_faloo.log'; tmux ls"
