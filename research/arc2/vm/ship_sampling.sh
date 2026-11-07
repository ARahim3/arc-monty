#!/usr/bin/env bash
ARC_MONTY_ROOT=${ARC_MONTY_ROOT:-$(cd "$(dirname "$0")/../../.." && pwd)}  # repo root
# Laptop side: ship code + data + pulled results to a VM and start run_sampling.sh in tmux "fs" (setup, servers, client).
#   Z=<zone> VM=<node id> DIRECTION=forward|backward STAGE=1|2 CLIENT=0|1 research/arc2/vm/ship_sampling.sh
# With CLIENT=0 it only brings the servers up. Re-running ships fresh code and starts the client if "fs" is not running.
set -euo pipefail
Z=${Z:?zone}; VM=${VM:?node id}; ROOT=$ARC_MONTY_ROOT
D=$(mktemp -d); TGZ=$D/fs.tgz
cd $ROOT && COPYFILE_DISABLE=1 tar --exclude=__pycache__ --exclude='*.DS_Store' --exclude=logs --exclude=results_archive \
  --exclude=xla_cache_store --exclude='*.ids.jsonl' -czf $TGZ llm research/arc2/*.py research/arc2/monty_hints.json research/arc2/vm \
  data/kaggle_format/agi2_eval_challenges.json data/kaggle_format/agi2_eval_solutions.json external/judge/conceptarc/repo/corpus
FILES=($TGZ)
if [ -d $ROOT/llm/xla_cache_store/xla_cache ]; then
  tar -czf $D/xla.tgz -C $ROOT/llm/xla_cache_store xla_cache; FILES+=($D/xla.tgz)
fi
gcloud compute tpus tpu-vm scp "${FILES[@]}" $VM:/tmp/ --zone=$Z
gcloud compute tpus tpu-vm ssh $VM --zone=$Z --command="sudo mkdir -p /mnt/data && sudo chown \$USER:\$USER /mnt/data && mkdir -p /mnt/data/arc_monty /mnt/data/logs && tar -xzf /tmp/fs.tgz -C /mnt/data/arc_monty && command -v tmux >/dev/null || (sudo apt-get update -qq && sudo apt-get install -y -qq tmux >/dev/null); cd /mnt/data/arc_monty && (tmux has-session -t fs 2>/dev/null && echo 'fs already running') || tmux new-session -d -s fs 'VM_NAME=$VM-$Z DIRECTION=${DIRECTION:-forward} STAGE=${STAGE:-1} CLIENT=${CLIENT:-1} bash research/arc2/vm/run_sampling.sh 2>&1 | tee -a /mnt/data/logs/run_sampling.log'; tmux ls"
rm -rf $D
