#!/usr/bin/env bash
# VM side (tmux "fa"): setup -> download Qwen3.8-27B -> 2 vLLM-TPU servers (TP4 each) -> FA-LOO phases (resumable).
#   SHARD=k/N PHASES=A,B,C,D bash research/arc2/vm/run_faloo.sh
set -uo pipefail
cd /mnt/data/arc_monty/llm/vm
bash setup.sh 2>&1 | tail -3
bash download.sh qwen38 2>&1 | tail -2
source /mnt/data/envs/vllm/bin/activate
up() { curl -sf -m 5 http://127.0.0.1:$1/v1/models >/dev/null; }
if ! up 8001 || ! up 8003; then
  tmux kill-session -t srv_a 2>/dev/null; tmux kill-session -t srv_b 2>/dev/null; sleep 5
  tmux new-session -d -s srv_a "PREFIX=--no-enable-prefix-caching SEQS=48 MAXLEN=57344 bash serve.sh qwen38 8001 4 0,1,2,3"
  tmux new-session -d -s srv_b "PREFIX=--no-enable-prefix-caching SEQS=48 MAXLEN=57344 bash serve.sh qwen38 8003 4 4,5,6,7"
  bash wait_server.sh 8001 qwen38 && bash wait_server.sh 8003 qwen38 || { echo "servers failed"; exit 1; }
fi
cd /mnt/data/arc_monty
python research/arc2/faloo_qwen.py --url http://127.0.0.1:8001/v1,http://127.0.0.1:8003/v1 \
  --tokenizer /mnt/data/ram/models/qwen38 --phases ${PHASES:-A,B,C,D} --concurrency ${CONC:-80} --shard ${SHARD:-0/1} \
  2>&1 | tee -a /mnt/data/logs/faloo.log
echo "$(date -u) faloo finished"
