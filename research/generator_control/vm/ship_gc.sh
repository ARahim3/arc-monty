#!/usr/bin/env bash
ARC_MONTY_ROOT=${ARC_MONTY_ROOT:-$(cd "$(dirname "$0")/../../.." && pwd)}  # repo root
# Laptop side: copy of research/arc2/vm/ship_sampling.sh with this experiment's files. Ships code + task JSON (never results) and starts
# run_gc.sh in tmux "gcq". No token goes to the VM.
#   Z=<zone> VM=<node id> DIRECTION=forward|backward STAGE=main|rot|retry1|retry2|rep0|rep1|rep2|cmain|cretry1|cretry2 CLIENT=0|1 research/generator_control/vm/ship_gc.sh
set -euo pipefail
Z=${Z:?zone}; VM=${VM:?node id}; ROOT=$ARC_MONTY_ROOT
D=$(mktemp -d); TGZ=$D/gc.tgz
cd $ROOT
EXTRA=()
for f in research/generator_control/data/retry1.json research/generator_control/data/retry2.json research/generator_control/data/rep0.json research/generator_control/data/rep1.json research/generator_control/data/rep2.json research/generator_control/data/cretry1.json research/generator_control/data/cretry2.json; do [ -f "$f" ] && EXTRA+=("$f"); done
COPYFILE_DISABLE=1 tar --exclude=__pycache__ --exclude='*.DS_Store' --exclude=logs --exclude=results --exclude=results_archive \
  --exclude=xla_cache_store --exclude='*.ids.jsonl' -czf $TGZ llm research/arc2/*.py research/arc2/monty_hints.json \
  research/generator_control/qwen_gc.py research/generator_control/vm research/generator_control/data/rearc_tasks.json ${EXTRA[@]+"${EXTRA[@]}"} \
  data/kaggle_format/agi2_eval_challenges.json data/kaggle_format/agi2_eval_solutions.json external/judge/conceptarc/repo/corpus
FILES=($TGZ)
if [ -d $ROOT/llm/xla_cache_store/xla_cache ]; then
  tar -czf $D/xla.tgz -C $ROOT/llm/xla_cache_store xla_cache; FILES+=($D/xla.tgz)
fi
gcloud compute tpus tpu-vm scp "${FILES[@]}" $VM:/tmp/ --zone=$Z --quiet
gcloud compute tpus tpu-vm ssh $VM --zone=$Z --quiet --command="sudo mkdir -p /mnt/data && sudo chown \$USER:\$USER /mnt/data && mkdir -p /mnt/data/arc_monty/llm/results /mnt/data/arc_monty/research/generator_control/raw /mnt/data/logs && tar -xzf /tmp/gc.tgz -C /mnt/data/arc_monty && { command -v tmux >/dev/null || (sudo apt-get update -qq && sudo apt-get install -y -qq tmux >/dev/null); }; cd /mnt/data/arc_monty && (tmux has-session -t gcq 2>/dev/null && echo 'gcq already running') || tmux new-session -d -s gcq 'VM_NAME=$VM-$Z DIRECTION=${DIRECTION:-forward} STAGE=${STAGE:-main} CLIENT=${CLIENT:-1} bash research/generator_control/vm/run_gc.sh 2>&1 | tee -a /mnt/data/logs/run_gc.log'; tmux ls"
rm -rf $D
