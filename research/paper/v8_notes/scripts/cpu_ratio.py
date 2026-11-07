"""v8 paper: CPU of 8-view vs 1-view per-module runs, from the held-out caches. Read-only."""
import os  # noqa: E402  (release: paths from the repo root)
_REPO = os.environ.get("ARC_MONTY_ROOT", os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..")))  # repo root
import json, os
C = (_REPO + "/research/monty_heldout/cache")
def total(path):
    tot = 0.0
    keys = None
    with open(path) as fh:
        for line in fh:
            r = json.loads(line)
            if keys is None:
                keys = list(r.keys()); rk = list(r["runs"].keys())[:2]; mk = list(next(iter(r["runs"].values())).keys())[:3]
                print(os.path.basename(path), keys, rk, mk, list(next(iter(next(iter(r["runs"].values())).values())).keys()))
            for run in r["runs"].values():
                for m in run.values():
                    tot += float(m.get("cpu", 0.0))
    return tot
for tag in ("concept", "mini", "oned"):
    a = total(os.path.join(C, f"{tag}_p0.jsonl"))
    b = total(os.path.join(C, f"{tag}_p1-7.jsonl"))
    print(tag, "p0 cpu", round(a, 1), "p1-7 cpu", round(b, 1), "8-view / 1-view", round((a + b) / a, 2) if a else None)
