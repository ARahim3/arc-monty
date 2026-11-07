#!/bin/bash
# Laptop side. Exits as soon as one of the named VMs (NAME:ZONE ...) is READY and answers SSH, or a named request has died.
# Prints the outcome. Silent otherwise.
while true; do
  for p in "$@"; do
    VM=${p%%:*}; Z=${p##*:}
    S=$(gcloud compute tpus tpu-vm describe "$VM" --zone="$Z" --format="value(state)" 2>/dev/null)
    Q=$(gcloud compute tpus queued-resources describe "$VM" --zone="$Z" --format="value(state.state)" 2>/dev/null)
    if [ "$S" = "READY" ]; then
      if gcloud compute tpus tpu-vm ssh "$VM" --zone="$Z" --quiet --command="echo up" 2>/dev/null | grep -q up; then
        echo "UP $VM $Z"; exit 0
      fi
    fi
    if [ "$Q" = "SUSPENDED" ] || [ "$Q" = "FAILED" ]; then echo "DEAD $VM $Z $Q"; exit 2; fi
  done
  sleep 30
done
