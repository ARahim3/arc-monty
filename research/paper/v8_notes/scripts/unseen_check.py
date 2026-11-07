"""v8 paper: independent recount of the unseen-set numbers from results/*_base.jsonl, tournament events per role, and
public-eval minus unseen differences. Reads existing files only; no solver run. Output: ../unseen_check.txt/.json"""
import os  # noqa: E402  (release: paths from the repo root)
_REPO = os.environ.get("ARC_MONTY_ROOT", os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..")))  # repo root
import collections, json, os, sys
ROOT = _REPO
HL = os.path.join(ROOT, "research", "monty_heldout")
sys.path.insert(0, HL)
import numpy as np
from hl_common import items_from_dir, h, task_of, group_of
from stats import Data, f, load_rows, prec, _pct

HERE = os.path.dirname(os.path.abspath(__file__))
SETS = {"concept": os.path.join(ROOT, "external/judge/conceptarc/repo/corpus"),
        "mini": os.path.join(ROOT, "external/heldout/mini-arc/data/MiniARC"),
        "oned": os.path.join(ROOT, "external/heldout/1d-arc/dataset"),
        "minimal": os.path.join(ROOT, "external/judge/conceptarc/repo/MinimalTasks")}
TASKER = {"oned": lambda k: k.split("/")[0]}
J = {}
for tag, path in SETS.items():
    rows = load_rows(os.path.join(HL, "results", f"{tag}_base.jsonl"))
    items = dict(items_from_dir(path))
    assert set(items) == set(rows), (tag, len(items), len(rows))
    real = {}
    for fld in ("fc", "fa", "a", "v5", "fit"):
        c = a = 0
        S = set()
        for k, r in rows.items():
            v = r["cfg"]["full"][str(r["m"] - 1)][fld]
            if v is not None:
                a += 1
                c += float(v)
                S.add(k)
        real[fld] = (c, a, S)
    p2 = sum(r["cfg"]["full"][str(r["m"] - 1)]["p2"] for r in rows.values())
    # tournament events from fold hashes: E_a = every fold (a,b) predicts b and misses a
    ev_items = two = 0
    ev_real = 0
    answered_wrong_outside_E = 0
    per_task = collections.defaultdict(int)
    role_tot = 0
    for k, r in rows.items():
        m = r["m"]
        pool = items[k]
        H = [h(y) for _, y in pool]
        cnt = 0
        for a in range(m):
            role_tot += 1
            o = r["cfg"]["full"][str(a)]
            E = True
            for b in range(m):
                if b == a:
                    continue
                p = o["fold_h"][str(b)]
                if p is None or p[0] != H[b] or p[1] == H[a]:
                    E = False
                    break
            cnt += E
            if E and a == m - 1:
                ev_real += 1
            fa = o["fa"]
            if fa is not None and float(fa) < 1 and not E:
                answered_wrong_outside_E += 1
        ev_items += cnt >= 1
        two += cnt >= 2
    n = len(rows)
    mean_b = np.mean([1 / r["m"] for r in rows.values()])
    m_hist = collections.Counter(r["m"] - 1 for r in rows.values())
    J[tag] = dict(items=n, pass2=p2, tasks=len({task_of(k) for k in rows}), counts={x: (real[x][0], real[x][1]) for x in real},
                  a_equals_fc=real["a"][2] == real["fc"][2], fa_equals_fc=real["fa"][2] == real["fc"][2],
                  items_with_event=ev_items, share=ev_items / n, two_plus=two, event_real=ev_real, mean_bound=float(mean_b),
                  joint=(real["fc"][1] - real["fc"][0]) / n, wrong_outside_E=answered_wrong_outside_E, roles=role_tot, n_hist=dict(m_hist))
    print(tag, json.dumps({k: v for k, v in J[tag].items()}, default=float))

# public eval minus unseen, independent resamples, as summary.py
dev = load_rows(os.path.join(HL, "results", "dev_base.jsonl"))
ev = {k: dict(m=1, cfg={"full": {"0": r["cfg"]["full"]}}) for k, r in dev.items() if r["split"] in ("agi1-eval", "agi2-eval")}
D = Data(ev, tasker=lambda k: k)
for tag in ("concept", "mini", "oned"):
    rows = load_rows(os.path.join(HL, "results", f"{tag}_base.jsonl"))
    d = Data(rows, tasker=TASKER.get(tag, task_of))
    out = {}
    for fld in ("fc", "v5", "fit"):
        x, y = D.vec("full", f(fld)), d.vec("full", f(fld))
        with np.errstate(invalid="ignore", divide="ignore"):
            bx = (D.W @ x[0]) / (D.W @ x[1])
            by = (d.W @ y[0]) / (d.W @ y[1])
        est = x[0].sum() / x[1].sum() - y[0].sum() / y[1].sum()
        ci = _pct(bx - by)
        out[fld] = dict(diff=float(est), ci=ci, separates=bool(ci[0] > 0 or ci[1] < 0))
        print(f"public eval minus {tag}, {fld}: {100*est:+.1f} [{100*ci[0]:+.1f}, {100*ci[1]:+.1f}]")
    J[tag]["eval_minus"] = out
json.dump(J, open(os.path.join(HERE, "..", "unseen_check.json"), "w"), indent=1, default=float)
