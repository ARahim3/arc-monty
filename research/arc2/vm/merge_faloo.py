"""Union two FA-LOO JSONL files by (kind, task_id, fold); a good record beats an error record. Usage: DST SRC (writes DST)."""
import json
import os
import sys

dst, src = sys.argv[1], sys.argv[2]
best = {}
for p in (dst, src):
    if not os.path.exists(p):
        continue
    for line in open(p):
        try:
            r = json.loads(line)
        except Exception:
            continue
        k = (r.get("kind"), r.get("task_id"), r.get("fold"))
        if k not in best or ("error" in best[k] and "error" not in r):
            best[k] = r
tmp = dst + ".tmp"
with open(tmp, "w") as f:
    for r in best.values():
        f.write(json.dumps(r) + "\n")
os.replace(tmp, dst)
