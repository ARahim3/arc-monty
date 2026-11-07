"""v8 paper: overlap of unseen sets with the 1,147 development tasks (whole-pair hash), 1D-ARC concentration, top-answer-only
check for v5/fit, public-eval task counts. Read-only; JSON only for third-party data."""
import os  # noqa: E402  (release: paths from the repo root)
_REPO = os.environ.get("ARC_MONTY_ROOT", os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..")))  # repo root
import collections, glob, hashlib, json, os, sys
ROOT = _REPO
HL = os.path.join(ROOT, "research/monty_heldout")
sys.path.insert(0, HL)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "research/monty_eval"))
from hl_common import items_from_dir
from stats import load_rows
from arcmonty.data import load_split
def hp(x, y):
    return hashlib.md5(json.dumps([x.tolist(), y.tolist()]).encode()).hexdigest()
dev = set()
for s in ("agi1-train", "agi1-eval", "agi2-train", "agi2-eval"):
    for k, t in load_split(s).items():
        for x, y in t["train"]:
            dev.add(hp(x, y))
        for x, y in zip(t["test"], t["test_out"]):
            dev.add(hp(x, y))
print("development distinct pairs", len(dev))
SETS = {"concept": "external/judge/conceptarc/repo/corpus", "mini": "external/heldout/mini-arc/data/MiniARC", "oned": "external/heldout/1d-arc/dataset", "minimal": "external/judge/conceptarc/repo/MinimalTasks"}
for tag, p in SETS.items():
    items = items_from_dir(os.path.join(ROOT, p))
    pairs = {hp(x, y) for _, pool in items for x, y in pool}
    print(tag, "items", len(items), "distinct pairs", len(pairs), "shared with development", len(pairs & dev))
r = load_rows(os.path.join(HL, "results/oned_base.jsonl"))
c = collections.Counter(k.split("/")[0] for k, v in r.items() if v["cfg"]["full"][str(v["m"] - 1)]["fc"] is not None)
print("1D-ARC FA-LOO answers by type", c.most_common(), "top 3 sum", sum(v for _, v in c.most_common(3)), "of", sum(c.values()), "types", len({k.split('/')[0] for k in r}))
for tag in ("concept", "mini", "oned"):
    r = load_rows(os.path.join(HL, f"results/{tag}_base.jsonl"))
    for a, b in (("v5", "v5t"), ("fit", "fitt")):
        ca = sum(float(v["cfg"]["full"][str(v["m"] - 1)][a]) for v in r.values() if v["cfg"]["full"][str(v["m"] - 1)][a] is not None)
        cb = sum(float(v["cfg"]["full"][str(v["m"] - 1)][b]) for v in r.values() if v["cfg"]["full"][str(v["m"] - 1)][b] is not None)
        print(tag, a, ca, b, cb)
d = load_rows(os.path.join(HL, "results/dev_base.jsonl"))
ev = {k: v for k, v in d.items() if v["split"] in ("agi1-eval", "agi2-eval")}
print("public eval tasks", len(ev), "single test", sum(v["T"] == 1 for v in ev.values()), "multi", sum(v["T"] > 1 for v in ev.values()))
fa = {k for k, v in ev.items() if v["cfg"]["full"]["fc"] is not None}
aa = {k for k, v in ev.items() if v["cfg"]["full"]["a"] is not None}
print("public eval: (a) set == FA-LOO+(c) set", fa == aa, len(fa))
print("FA-LOO wrong on public eval", [k for k in fa if ev[k]["cfg"]["full"]["fc"] < 1], "v5 wrong", [k for k, v in ev.items() if v["cfg"]["full"]["v5"] is not None and v["cfg"]["full"]["v5"] < 1])
