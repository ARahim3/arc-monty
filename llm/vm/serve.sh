#!/usr/bin/env bash
# Start a vLLM-TPU OpenAI server for one model. Run inside tmux.
#   serve.sh <qwen38|nanbeige> <port> [tp] [chips e.g. 0,1,2,3] [extra vllm args...]
# With chips given, the server sees only those chips (two models side by side on a v6e-8).
set -uo pipefail
source /mnt/data/envs/vllm/bin/activate
M=$1; PORT=$2; TP=${3:-8}; CHIPS=${4:-}; shift $(( $# < 4 ? $# : 4 ))
MAXLEN=${MAXLEN:-98304}; SEQS=${SEQS:-64}
if [ -n "$CHIPS" ]; then
  export TPU_VISIBLE_CHIPS=$CHIPS TPU_CHIPS_PER_PROCESS_BOUNDS=${BOUNDS:-2,2,1} TPU_PROCESS_BOUNDS=1,1,1
  export ALLOW_MULTIPLE_LIBTPU_LOAD=1 TPU_PROCESS_PORT=$((PORT + 7000)) TPU_PROCESS_ADDRESSES=localhost:$((PORT + 7000)) CLOUD_TPU_TASK_ID=0
fi
export VLLM_NO_USAGE_STATS=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export NUM_PRECOMPILE_WORKERS=${NUM_PRECOMPILE_WORKERS:-16} VLLM_XLA_CACHE_PATH=/mnt/data/xla_cache; mkdir -p /mnt/data/xla_cache
LOG=/mnt/data/logs/serve_${M}_${PORT}.log
echo "$(date -u) serve $M port $PORT tp $TP chips '${CHIPS}' maxlen $MAXLEN seqs $SEQS extra: $*" | tee -a $LOG
exec vllm serve /mnt/data/ram/models/$M --served-model-name $M --port $PORT --host 127.0.0.1 \
  --tensor-parallel-size $TP --max-model-len $MAXLEN --max-num-seqs $SEQS --max-num-batched-tokens ${MNBT:-2048} \
  --gpu-memory-utilization ${GMU:-0.92} ${PREFIX---enable-prefix-caching} --trust-remote-code "$@" 2>&1 | tee -a $LOG
