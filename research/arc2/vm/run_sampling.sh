#!/usr/bin/env bash
# VM side (tmux "fs"): setup -> download Qwen3.8-27B -> 2 vLLM-TPU servers (TP4 each) -> FA-LOO sampling client (resumable).
#   VM_NAME=arc-v6e-r DIRECTION=forward CLIENT=1 STAGE=1 bash research/arc2/vm/run_sampling.sh
# CLIENT=0 stops after the servers are up. Each server boot gets its own --seed (server RNG must differ per boot and per server).
set -uo pipefail
GLOBAL_SEED=20261101
MAXLEN=${MAXLEN:-98304}; SEQS=${SEQS:-40}; VM_NAME=${VM_NAME:-unknown}
cd /mnt/data/arc_monty/llm/vm
bash setup.sh 2>&1 | tail -3
bash download.sh qwen38 2>&1 | tail -2
source /mnt/data/envs/vllm/bin/activate
[ -f /tmp/xla.tgz ] && [ ! -d /mnt/data/xla_cache ] && tar -xzf /tmp/xla.tgz -C /mnt/data && echo "xla cache restored: $(du -sh /mnt/data/xla_cache | cut -f1)"
up() { curl -sf -m 5 http://127.0.0.1:$1/v1/models >/dev/null; }
sseed() { python3 -c "import zlib,sys; print(zlib.crc32(sys.argv[1].encode()) & 0x7FFFFFFF)" "$GLOBAL_SEED|$VM_NAME|$1|$(date +%s)"; }
if ! up 8001 || ! up 8003; then
  tmux kill-session -t srv_a 2>/dev/null; tmux kill-session -t srv_b 2>/dev/null; sleep 5
  SA=$(sseed 8001); SB=$(sseed 8003)
  echo "$(date -u) server seeds 8001=$SA 8003=$SB maxlen=$MAXLEN seqs=$SEQS" | tee -a /mnt/data/logs/server_seeds.log
  tmux new-session -d -s srv_a "PREFIX=--no-enable-prefix-caching SEQS=$SEQS MAXLEN=$MAXLEN bash serve.sh qwen38 8001 4 0,1,2,3 --seed $SA"
  tmux new-session -d -s srv_b "PREFIX=--no-enable-prefix-caching SEQS=$SEQS MAXLEN=$MAXLEN bash serve.sh qwen38 8003 4 4,5,6,7 --seed $SB"
  bash wait_server.sh 8001 qwen38 && bash wait_server.sh 8003 qwen38 || { echo "servers failed"; exit 1; }
fi
echo "$(date -u) servers up"
[ "${CLIENT:-1}" = 1 ] || exit 0
cd /mnt/data/arc_monty
python research/arc2/faloo_qwen_sampling.py --url http://127.0.0.1:8001/v1,http://127.0.0.1:8003/v1 \
  --tokenizer /mnt/data/ram/models/qwen38 --stage ${STAGE:-1} --direction ${DIRECTION:-forward} --vm "$VM_NAME" \
  2>&1 | tee -a /mnt/data/logs/faloo_sampling.log
echo "$(date -u) sampling client finished (stage ${STAGE:-1})"
