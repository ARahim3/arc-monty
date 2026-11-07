#!/usr/bin/env bash
# VM side: wait for both servers, then run arm groups; arms inside a group run concurrently (resumable).
#   ARM_GROUPS="armA:conc,armB:conc;armC:conc" bash research/arc2/vm/run_arms.sh
set -uo pipefail
cd /mnt/data/arc_monty
source /mnt/data/envs/vllm/bin/activate
bash llm/vm/wait_server.sh 8001 qwen38 && bash llm/vm/wait_server.sh 8003 qwen38 || { echo "servers not up"; exit 1; }
URL=http://127.0.0.1:8001/v1,http://127.0.0.1:8003/v1
ARM_GROUPS=${ARM_GROUPS:-"ps_low_b16384:30,ps_medium_b16384:30,ps_xhigh_hint_b16384:30,direct_low_b16384:10"}
IFS=';' read -ra GS <<< "$ARM_GROUPS"
for G in "${GS[@]}"; do
  IFS=',' read -ra AS <<< "$G"
  for AC in "${AS[@]}"; do
    ARM=${AC%%:*}; REST=${AC#*:}; C=${REST%%:*}; SF=0; [ "$REST" != "$C" ] && SF=${REST#*:}   # arm:conc[:first_sample]
    echo "$(date -u) start $ARM conc $C"
    python research/arc2/bench2.py --arm $ARM --url $URL --tokenizer /mnt/data/ram/models/qwen38 --concurrency $C \
      --sample-from $SF --out llm/results > /mnt/data/logs/arm_${ARM}_s$SF.log 2>&1 &
  done
  wait
  echo "$(date -u) group done: $G"
done
echo "$(date -u) all groups done"
