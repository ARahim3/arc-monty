"""v8 paper appendix: ARC-AGI-3 held-out numbers re-derived from raw result files. Read-only."""
import os  # noqa: E402  (release: paths from the repo root)
_REPO = os.environ.get("ARC_MONTY_ROOT", os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..")))  # repo root
import json, sys, collections
R = (_REPO + "/arc3_agent/v7/results/")
sys.path.insert(0, (_REPO + "/arc3_agent/v8"))
from split import HELDOUT, TUNE
def load(f): return [json.loads(l) for l in open(R + f)]
for tag, f in (("random", "random_all_30k.jsonl"), ("v3", "f_v3_30k.jsonl"), ("v7", "f_v7_30k.jsonl")):
    rows = load(f)
    for name, sel in (("held-out", HELDOUT), ("tune", TUNE), ("all", set(HELDOUT) | set(TUNE))):
        rs = [r for r in rows if r["game"].split("-")[0] in sel]
        seeds = sorted({r["seed"] for r in rs})
        off = [r["official"]["score"] if r.get("official") else float("nan") for r in rs]
        print(tag, name, "games", len({r["game"] for r in rs}), "seeds", seeds, "levels/seed", round(sum(r["levels"] for r in rs) / len(seeds), 2), "mean score", round(sum(off) / len(off), 3))
    rs = [r for r in rows if r["game"].split("-")[0] in HELDOUT]
    by = collections.defaultdict(float)
    per = collections.defaultdict(list)
    for r in rs:
        g = r["game"].split("-")[0]
        by[g] += (r["official"]["score"] if r.get("official") else 0.0) / len(rs)
        per[g].append(round(r["official"]["score"], 2) if r.get("official") else None)
    print("  contribution to the held-out mean:", {k: round(v, 3) for k, v in sorted(by.items(), key=lambda kv: -kv[1])[:4]}, "per seed", {k: per[k] for k in sorted(by, key=lambda k: -by[k])[:2]})
