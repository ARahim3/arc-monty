"""v8 paper (post hoc, label as such): if pairs are exchangeable within a task, a tournament event falls on the test role with
probability 1/(n+1), given that it occurs. Label-free in the sense that only the task's own pairs are used. Reads existing files only.
Output: ../event_location.txt"""
import os  # noqa: E402  (release: paths from the repo root)
_REPO = os.environ.get("ARC_MONTY_ROOT", os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..")))  # repo root
import collections, json, os, sys
ROOT = _REPO
HL = os.path.join(ROOT, "research", "monty_heldout")
sys.path.insert(0, HL)
import numpy as np
from hl_common import items_from_dir, h, task_of
from stats import load_rows

SETS = {"concept": os.path.join(ROOT, "external/judge/conceptarc/repo/corpus"),
        "mini": os.path.join(ROOT, "external/heldout/mini-arc/data/MiniARC"),
        "oned": os.path.join(ROOT, "external/heldout/1d-arc/dataset")}

def poisson_binomial_upper(ps, k):
    d = np.array([1.0])
    for p in ps:
        d = np.convolve(d, [1 - p, p])
    return float(d[k:].sum())

for tag, path in SETS.items():
    rows = load_rows(os.path.join(HL, "results", f"{tag}_base.jsonl"))
    items = dict(items_from_dir(path))
    evs = []
    for k, r in rows.items():
        m = r["m"]
        H = [h(y) for _, y in items[k]]
        for a in range(m):
            o = r["cfg"]["full"][str(a)]
            if all((o["fold_h"][str(b)] is not None and o["fold_h"][str(b)][0] == H[b] and o["fold_h"][str(b)][1] != H[a]) for b in range(m) if b != a):
                evs.append((k, a, m))
    real = sum(a == m - 1 for _, a, m in evs)
    exp = sum(1 / m for _, _, m in evs)
    p = poisson_binomial_upper([1 / m for _, _, m in evs], real)
    tasks = collections.Counter(task_of(k) for k, _, _ in evs)
    # one vote per task: a task counts as "test role" if any of its events is at a real role
    per = collections.defaultdict(list)
    for k, a, m in evs:
        per[task_of(k)].append(a == m - 1)
    print(tag, "events", len(evs), "at test role", real, "expected if exchangeable", round(exp, 2), "one-sided p (items independent, optimistic)", round(p, 4),
          "tasks with an event", len(tasks), "tasks with an event at the test role", sum(any(v) for v in per.values()))
    print("  ", [f"{k}@{a}/{m}" for k, a, m in evs][:30])

# public eval
rot = [json.loads(l) for l in open(os.path.join(ROOT, "research/paper/review_scratch/rotate_distinct.jsonl"))]
evs = []
for r in rot:
    if r["split"] not in ("agi1-eval", "agi2-eval"):
        continue
    m, H, F = r["m"], r["truth"], r["folds"]
    for a in range(m):
        ok = True
        for b in range(m):
            if b == a:
                continue
            p = F[f"{a},{b}"]
            if p is None or p[0] != H[b] or p[1] == H[a]:
                ok = False
                break
        if ok:
            evs.append((r["task"], a, m))
print("public eval events", len(evs), "at test role", sum(a == m - 1 for _, a, m in evs), "expected", round(sum(1 / m for _, _, m in evs), 2), evs)
