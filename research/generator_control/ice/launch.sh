#!/bin/bash
# On a VM with the 2020 program built at /mnt/data/ice/build (icecuber_faloo/vm/setup.sh). Same limits as icecuber_faloo/vm/launch.sh.
# launch.sh WORKERS DEEP_WORKERS
set -e
W=${1:-150}; D=${2:-80}
mkdir -p /mnt/data/gc/ice /dev/shm/ice && cd /mnt/data/gc/ice
cp /tmp/gc_runner.py runner.py
gunzip -c /tmp/gc_slice.jsonl.gz > slice.jsonl
cp /tmp/gc_done.txt done.txt
rm -f finished
tmux new-session -d -s gcice "cd /mnt/data/gc/ice && python3 runner.py --jobs slice.jsonl --out runs.jsonl --done done.txt --cfgs 3,23,33,4 --workers $W --deep-workers $D --time 3600 --mem-gb 16 --finished finished > runner.log 2>&1"
sleep 3; tmux ls; tail -1 runner.log; wc -l slice.jsonl; sha256sum /mnt/data/ice/build/run | cut -c1-16
