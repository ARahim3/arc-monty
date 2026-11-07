#!/usr/bin/env bash
ARC_MONTY_ROOT=${ARC_MONTY_ROOT:-$(cd "$(dirname "$0")/../../.." && pwd)}  # repo root
# Laptop side: every 4 min merge the VM's FA-LOO results into llm/results (record-wise union) and copy its log.
# Exits on /tmp/fa_stop, or after 3 failed pulls in a row (VM gone).   Z=<zone> research/arc2/vm/pull_faloo.sh
Z=${Z:-us-east1-d}; VM=${VM:-arc-v6e}; R=$ARC_MONTY_ROOT; DST=$R/llm/results; LG=$R/research/arc2/logs/faloo_$Z
mkdir -p $LG; miss=0
while true; do
  if gcloud compute tpus tpu-vm ssh $VM --zone=$Z --command='cd /mnt/data/arc_monty/llm/results && tar -czf /tmp/fares.tgz qwen38_faloo_*.jsonl 2>/dev/null; cd /mnt/data/logs && tar -czf /tmp/falogs.tgz faloo.log run_faloo.log 2>/dev/null; true' >/dev/null 2>&1 \
     && gcloud compute tpus tpu-vm scp $VM:/tmp/fares.tgz $VM:/tmp/falogs.tgz $LG/ --zone=$Z >/dev/null 2>&1; then
    miss=0; T=$(mktemp -d); tar -xzf $LG/fares.tgz -C $T 2>/dev/null; tar -xzf $LG/falogs.tgz -C $LG 2>/dev/null
    for f in $T/*.jsonl; do [ -f "$f" ] && python3 $R/research/arc2/vm/merge_faloo.py $DST/$(basename $f) $f; done; rm -rf $T
    echo "$(date -u +%H:%M) $Z pulled: $(wc -l < $DST/qwen38_faloo_greedy_b16384.jsonl 2>/dev/null) records; $(tail -1 $LG/faloo.log 2>/dev/null | cut -c1-90)"
  else
    miss=$((miss+1)); echo "$(date -u +%H:%M) $Z pull failed ($miss)"
    [ $miss -ge 3 ] && { gcloud compute tpus queued-resources list --zone=$Z 2>&1 | grep arc; exit 2; }
  fi
  [ -f /tmp/fa_stop ] && exit 0
  sleep 240
done
