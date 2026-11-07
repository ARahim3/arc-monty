#!/usr/bin/env bash
# Full benchmark pipeline for one served model (run inside tmux; resumable: re-run after a crash).
#   run_model.sh <qwen38|nanbeige> <port> [stages: smoke,direct,emulate,ps]
set -uo pipefail
source /mnt/data/envs/vllm/bin/activate
M=$1; PORT=$2; STAGES=${3:-smoke,direct,emulate,ps}
BMAX=${BMAX:-32768}; PSB=${PSB:-16384}; CONC=${CONC:-64}
cd /mnt/data/arc_monty/llm
URL=${URL:-http://127.0.0.1:$PORT/v1}
COMMON="--model $M --tokenizer /mnt/data/ram/models/$M --url $URL --concurrency $CONC"
TASKARG=${TASKS:+--tasks $TASKS}
LOG=/mnt/data/logs/run_$M.log
has() { [[ ",$STAGES," == *",$1,"* ]]; }
has smoke   && python run_bench.py $COMMON --harness direct --budget 2048 --answer-room 4096 --tasks 2 --samples 1 --out results_smoke 2>&1 | tee -a $LOG
has direct  && python run_bench.py $COMMON --harness direct --budget $BMAX $TASKARG --out results 2>&1 | tee -a $LOG
has emulate && python emulate_budgets.py $COMMON --src results/${M}_direct_b$BMAX --budgets ${EMU:-4096,8192,16384} 2>&1 | tee -a $LOG
has ps      && python run_bench.py $COMMON --harness ps --budget $PSB --rounds 2 $TASKARG --out results 2>&1 | tee -a $LOG
echo "$(date -u) run_model $M finished stages $STAGES" | tee -a $LOG
