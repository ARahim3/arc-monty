#!/bin/bash
# on VM: launch.sh VMNAME
set -e
cd /mnt/data/ice
cp /tmp/runner.py runner.py
gunzip -f /tmp/slice_$1.jsonl.gz; mv /tmp/slice_$1.jsonl slice.jsonl
mv /tmp/done_$1.txt done.txt
rm -f finished
tmux new-session -d -s ice "cd /mnt/data/ice && python3 runner.py --jobs slice.jsonl --out runs.jsonl --done done.txt --cfgs 3,23,33,4 --workers 150 --deep-workers 80 --time 3600 --mem-gb 16 --finished finished > runner.log 2>&1"
sleep 2; tmux ls; tail -1 runner.log; wc -l slice.jsonl
