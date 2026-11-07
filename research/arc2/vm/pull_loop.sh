#!/usr/bin/env bash
ARC_MONTY_ROOT=${ARC_MONTY_ROOT:-$(cd "$(dirname "$0")/../../.." && pwd)}  # repo root
# Laptop side: every 4 min copy this experiment's result files (qwen38_{ps,direct}_{low,medium,xhigh}*) + arm logs off the VM.
# Exits when the VM reports "all groups done" or when the VM is gone (preempted) for 3 checks in a row.
Z=${Z:-europe-west4-a}; VM=${VM:-arc-v6e}; DST=$ARC_MONTY_ROOT/llm/results; LG=$ARC_MONTY_ROOT/research/arc2/logs/$Z
mkdir -p $LG; miss=0
while true; do
  if gcloud compute tpus tpu-vm ssh $VM --zone=$Z --command='cd /mnt/data/arc_monty/llm/results && tar -czf /tmp/a2res.tgz qwen38_*_low*.jsonl qwen38_*_medium*.jsonl qwen38_*_xhigh*.jsonl 2>/dev/null; cd /mnt/data/logs && tar -czf /tmp/a2logs.tgz arms.log arms2.log arm_*.log 2>/dev/null; true' >/dev/null 2>&1 \
     && gcloud compute tpus tpu-vm scp $VM:/tmp/a2res.tgz $VM:/tmp/a2logs.tgz /tmp/ --zone=$Z >/dev/null 2>&1; then
    miss=0; T=$(mktemp -d); tar -xzf /tmp/a2res.tgz -C $T 2>/dev/null
    for f in $T/*.jsonl; do [ -f "$f" ] && python3 $ARC_MONTY_ROOT/llm/vm/merge_jsonl.py $DST/$(basename $f) $f >/dev/null; done
    rm -rf $T; tar -xzf /tmp/a2logs.tgz -C $LG 2>/dev/null
    echo "$(date -u +%H:%M) pulled: $(for f in $DST/qwen38_*_{low,medium,xhigh}*.jsonl; do [ -f $f ] && echo -n "$(basename $f .jsonl)=$(wc -l < $f) "; done)"
    [ -f /tmp/a2_stop ] && exit 0
  else
    miss=$((miss+1)); echo "$(date -u +%H:%M) pull failed ($miss)"
    [ $miss -ge 3 ] && { gcloud compute tpus queued-resources list --zone=$Z 2>&1 | grep arc; exit 2; }
  fi
  sleep 240
done
