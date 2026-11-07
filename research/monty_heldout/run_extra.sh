#!/bin/zsh
ARC_MONTY_ROOT=${ARC_MONTY_ROOT:-$(cd "$(dirname "$0")/../.." && pwd)}  # repo root
# monty-heldout: the extra unseen datasets, one after another, never more than 8 workers. Data is read as JSON only; python -I -B.
cd $ARC_MONTY_ROOT/research/monty_heldout
source $ARC_MONTY_ROOT/.venv/bin/activate
X=$ARC_MONTY_ROOT/external
PY() { nice -n 15 python -I -B "$@" }
for spec in "minimal:$X/judge/conceptarc/repo/MinimalTasks" "mini:$X/heldout/mini-arc/data/MiniARC" "oned:$X/heldout/1d-arc/dataset"; do
  tag=${spec%%:*}; dir=${spec#*:}
  PY run_cache.py $dir $tag --persp 0 --procs 8 > logs/cache_${tag}_p0.log 2>&1
  PY run_cache.py $dir $tag --persp 0 --arm global --procs 8 > logs/cache_${tag}_global.log 2>&1
  PY revote.py $dir $tag base --procs 8 > logs/revote_${tag}_base.log 2>&1
  echo "$tag base done $(date -u)" >> logs/extra.log
done
for spec in "minimal:$X/judge/conceptarc/repo/MinimalTasks" "mini:$X/heldout/mini-arc/data/MiniARC" "oned:$X/heldout/1d-arc/dataset"; do
  tag=${spec%%:*}; dir=${spec#*:}
  PY run_cache.py $dir $tag --persp 1-7 --procs 8 > logs/cache_${tag}_p17.log 2>&1
  PY revote.py $dir $tag p8 --procs 8 > logs/revote_${tag}_p8.log 2>&1
  echo "$tag p8 done $(date -u)" >> logs/extra.log
done
echo finished >> logs/extra.log
