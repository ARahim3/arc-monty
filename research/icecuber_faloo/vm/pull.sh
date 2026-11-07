#!/bin/bash
# Laptop side: append new result bytes from the VM's runs.jsonl to a local file, every INTERVAL seconds. Text only, offset
# based, so a dropped connection or a torn line heals on the next pull. Exits when the VM's "finished" marker exists and
# everything has been pulled, or after MAX_FAILS failed pulls in a row (VM probably preempted).
#   pull.sh VM ZONE LOCAL_FILE [INTERVAL] [MAX_FAILS]
VM=$1; Z=$2; LOCAL=$3; INTERVAL=${4:-180}; MAX_FAILS=${5:-20}
REMOTE=/mnt/data/ice/runs.jsonl
fails=0
touch "$LOCAL"
while true; do
  N=$(stat -f%z "$LOCAL")
  TMP="$LOCAL.part"
  if gcloud compute tpus tpu-vm ssh "$VM" --zone="$Z" --quiet --command="tail -c +$((N+1)) $REMOTE 2>/dev/null; true" > "$TMP" 2>/dev/null; then
    cat "$TMP" >> "$LOCAL"; rm -f "$TMP"; fails=0
    if gcloud compute tpus tpu-vm ssh "$VM" --zone="$Z" --quiet --command="test -f /mnt/data/ice/finished" 2>/dev/null; then
      N2=$(stat -f%z "$LOCAL")
      R=$(gcloud compute tpus tpu-vm ssh "$VM" --zone="$Z" --quiet --command="stat -c%s $REMOTE" 2>/dev/null)
      if [ "$N2" = "$R" ]; then echo "finished: $VM all pulled $N2 bytes"; exit 0; fi
    fi
  else
    rm -f "$TMP"; fails=$((fails+1))
    if [ "$fails" -ge "$MAX_FAILS" ]; then echo "pull failing: $VM $fails in a row"; exit 1; fi
  fi
  sleep "$INTERVAL"
done
