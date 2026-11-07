"""Union FA-LOO sampling JSONL files by (kind, task_id, fold): a good record beats an error record, and among good records the one
STARTED first is kept (never 'first to finish', so the choice cannot depend on the outcome). Error records are kept only if there is
no good one. Usage: merge_sampling.py DST SRC [SRC...] (writes DST atomically; prints the number of keys)."""
import json
import os
import sys

dst, srcs = sys.argv[1], sys.argv[2:]
best = {}
for p in [dst] + srcs:
    if not os.path.exists(p):
        continue
    for line in open(p):
        try:
            r = json.loads(line)
        except Exception:
            continue
        k = (r.get("kind"), r.get("task_id"), r.get("fold"))
        if k not in best:
            best[k] = r
            continue
        b = best[k]
        if "error" in b and "error" not in r:
            best[k] = r
        elif "error" not in b and "error" not in r and r.get("started_at", 0) < b.get("started_at", 0):
            best[k] = r
tmp = dst + ".tmp"
with open(tmp, "w") as f:
    for r in best.values():
        f.write(json.dumps(r) + "\n")
os.replace(tmp, dst)
print(len(best))
