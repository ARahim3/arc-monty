#!/usr/bin/env bash
ARC_MONTY_ROOT=${ARC_MONTY_ROOT:-$(cd "$(dirname "$0")/../../.." && pwd)}  # repo root
# Laptop side: watch both v6e zones; when an arc-v6e VM is READY, ship + start FA-LOO there and start its pull loop.
# First VM: phases A,B,C,D. A VM that comes up while another runs: phases D,C,B,A (they meet at the end; merge dedups).
# A VM whose request dies is re-queued (dead requests only). Stops on /tmp/fa_stop.
R=$ARC_MONTY_ROOT; S=$R/research/arc2/vm; M=$R/research/arc2/logs/fa_markers; mkdir -p $M
log() { echo "$(date -u +%H:%M:%S) $*"; }
while [ ! -f /tmp/fa_stop ]; do
  for Z in us-east1-d europe-west4-a; do
    st=$(gcloud compute tpus queued-resources list --zone=$Z --format='value(name,state.state)' 2>/dev/null | awk '$1=="arc-v6e-q"{print $2}')
    vm=$(gcloud compute tpus tpu-vm describe arc-v6e --zone=$Z --format='value(state,createTime)' 2>/dev/null | tr '\t' ' ')
    key="$Z ${vm#* }"
    if [ "$st" = "ACTIVE" ] && [ "${vm%% *}" = "READY" ] && [ ! -f "$M/$(echo $key | tr ' :' '__')" ]; then
      other=$(ls $M | grep -v "^$(echo $Z | tr ' :' '__')" | wc -l)
      running=0; for p in $(pgrep -f "pull_faloo[.]sh"); do running=$((running+1)); done
      PH=A,B,C,D; [ $running -gt 0 ] && PH=D,C,B,A
      log "start $Z (create ${vm#* }) phases $PH (pull loops running: $running)"
      Z=$Z PHASES=$PH bash $S/ship_faloo.sh 2>&1 | grep -E "fa:|already|ERROR" | tail -2
      touch "$M/$(echo $key | tr ' :' '__')"
      (Z=$Z bash $S/pull_faloo.sh >> $R/research/arc2/logs/pull_faloo_$Z.txt 2>&1 &)
    fi
    if [ "$st" = "SUSPENDED" ] || [ "$st" = "FAILED" ]; then
      log "$Z request $st -> delete and re-queue (dead request, runbook §4)"
      gcloud compute tpus queued-resources delete arc-v6e-q --zone=$Z --force --quiet >/dev/null 2>&1
      gcloud compute tpus queued-resources create arc-v6e-q --project=${GCP_PROJECT:?set GCP_PROJECT to your Google Cloud project id} --zone=$Z --node-id=arc-v6e \
        --accelerator-type=v6e-8 --runtime-version=v2-alpha-tpuv6e --spot >/dev/null 2>&1 && log "$Z re-queued"
    fi
  done
  sleep 60
done
log "stop file seen; orchestrator exits"
