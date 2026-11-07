"""Summarise selfcal_own output: inner precision, coverage, joint, against real-role FA-LOO on the same tasks; compare with the reviewer's raw rows."""
import os  # noqa: E402  (release: paths from the repo root)
_REPO = os.environ.get("ARC_MONTY_ROOT", os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..")))  # repo root
import collections, json, os, sys
ROOT = _REPO
sys.path.insert(0, os.path.join(ROOT, "research/monty_heldout"))
import numpy as np
from stats import load_rows, _pct
TK = {"oned": lambda k: k.split("/")[0]}
for tag in ("concept", "mini", "oned", "agi2eval"):
    p = f"{ROOT}/research/paper/v8_notes/selfcal/{tag}.jsonl"
    if not os.path.exists(p):
        continue
    S = {json.loads(l)["task"]: json.loads(l) for l in open(p)}
    if tag == "agi2eval":
        roles = [x for s in S.values() for x in s["roles"]]
        print(tag, "tasks", len(S), "(a)+(b)", sum(x["ab"] for x in roles), "right", sum(x["right"] for x in roles), "of roles", len(roles))
        continue
    tk = TK.get(tag, lambda k: k.split("#")[0])
    rows = load_rows(f"{ROOT}/research/monty_heldout/results/{tag}_base.jsonl")
    items = {k: r for k, r in rows.items() if k.split("#")[0] in S}
    cl = sorted({tk(k) for k in S}); ix = {c: i for i, c in enumerate(cl)}
    ic, ia, ic2, ia2, ro, ev, oc, oa, nit = [np.zeros(len(cl)) for _ in range(9)]
    for k, s in S.items():
        i = ix[tk(k)]
        for x in s["roles"]:
            ro[i] += 1; ia[i] += x["ab"]; ic[i] += x["right"]; ev[i] += x["E"]
            ia2[i] += x["abc"]; ic2[i] += x["right"] and x["abc"]
    for k, r in items.items():
        i = ix[tk(k)]; o = r["cfg"]["full"][str(r["m"] - 1)]; nit[i] += 1
        if o["fc"] is not None:
            oa[i] += 1; oc[i] += float(o["fc"])
    W = np.random.default_rng(0).multinomial(len(cl), np.full(len(cl), 1 / len(cl)), size=10000)
    with np.errstate(invalid="ignore", divide="ignore"):
        a = _pct((W @ ic) / (W @ ia)); b = _pct((W @ oc) / (W @ oa)); d = _pct((W @ ic) / (W @ ia) - (W @ oc) / (W @ oa))
    print(f"{tag}: tasks {len(S)}, items {len(items)}, clusters {len(cl)}")
    print(f"  inner (a)+(b): {ic.sum():.0f}/{ia.sum():.0f} = {100*ic.sum()/ia.sum():.1f}% [{100*a[0]:.1f}, {100*a[1]:.1f}]; coverage {100*ia.sum()/ro.sum():.1f}% of {ro.sum():.0f} roles; joint {100*(ia.sum()-ic.sum())/ro.sum():.2f}%; events {ev.sum():.0f}")
    print(f"  inner with (c): {ic2.sum():.0f}/{ia2.sum():.0f}")
    print(f"  real FA-LOO, same tasks: {oc.sum():.0f}/{oa.sum():.0f} = {100*oc.sum()/oa.sum():.1f}% [{100*b[0]:.1f}, {100*b[1]:.1f}]; coverage {100*oa.sum()/nit.sum():.1f}%; joint {100*(oa.sum()-oc.sum())/nit.sum():.2f}%")
    print(f"  inner minus real: {100*(ic.sum()/ia.sum()-oc.sum()/oa.sum()):+.1f} [{100*d[0]:+.1f}, {100*d[1]:+.1f}]")
    rp = f"{ROOT}/research/paper/judge_v8/raw/selfcal_{tag}.jsonl"
    if os.path.exists(rp):
        J = {json.loads(l)["task"]: json.loads(l) for l in open(rp)}
        diff = sum(1 for k in S for x, y in zip(S[k]["roles"], J[k]["roles"]) if (x["ab"], x["right"]) != (y["ans"], y["right"]))
        print(f"  compared with reviewer's raw rows: tasks {len(J)}, role mismatches {diff} of {sum(len(S[k]['roles']) for k in S)}")
