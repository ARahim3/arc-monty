"""Merge result jsonl files record-wise: union by (task_id, sample[, budget]); a good record beats an
error record; first good one wins. Usage: python3 merge_jsonl.py DST SRC  (writes DST)."""
import json
import os
import sys


def key(r):
    return (r.get("task_id"), r.get("sample"), r.get("budget"), r.get("harness"))


def load(p):
    out = []
    if os.path.exists(p):
        for line in open(p):
            try:
                out.append(json.loads(line))
            except Exception:
                pass
    return out


dst, src = sys.argv[1], sys.argv[2]
def bad(r):
    rd = r.get("rounds")
    return "error" in r or (rd is not None and not any("error" not in x and "skipped" not in x for x in rd))


best = {}
for r in load(dst) + load(src):
    if bad(r):
        r = dict(r, error=r.get("error", "no successful round"))
    k = key(r)
    if k not in best or ("error" in best[k] and "error" not in r):
        best[k] = r
good = [r for r in best.values() if "error" not in r]
with open(dst + ".tmp", "w") as f:
    for r in good:
        f.write(json.dumps(r) + "\n")
os.replace(dst + ".tmp", dst)
print(f"{os.path.basename(dst)}: {len(good)} good records")
