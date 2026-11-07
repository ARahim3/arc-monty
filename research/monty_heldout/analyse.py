"""monty-heldout step 3: tables for a dataset from results/<TAG>_base.jsonl, _p8.jsonl and results/dev_base.jsonl.
Rules and buckets are those fixed in the plan (research/monty_heldout.md section 0).
usage: python analyse.py TAG -> results/<TAG>_tables.md, results/<TAG>_analysis.json"""
import collections
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hl_common import HERE, MODULES, task_of  # noqa: E402
import numpy as np  # noqa: E402
from stats import (BUCKETS, Data, auroc_cluster, bucket, count_ci, count_diff, f, fmt, fmtc, fmtd, load_dataset, load_dev,  # noqa: E402
                   prec, prec_diff)

TAG = sys.argv[1] if len(sys.argv) > 1 else "concept"
RES = os.path.join(HERE, "results")
L, J = [], {}


def w(s=""):
    L.append(s)


def loo1(o):
    return o["top_ok"] if (o["top_ev"] is not None and o["top_ev"] >= 0.99) else None


def p2vec(d, cfg, role="real", field="p2"):
    return d.vec(cfg, f(field), role)[0]


def solved_tasks(v):
    return int((v > 0).sum())


rows = load_dataset(TAG, "base")
TASKER = {"oned": lambda k: k.split("/")[0]}.get(TAG, task_of)  # 1D-ARC: cluster by generated type (plan addendum)
d = Data(rows, tasker=TASKER)
dev = load_dev()
real_n, demo_n = d.n_items("real"), d.n_items("demo")
w(f"Dataset `{TAG}`: {real_n} items (test pairs) in {d.T} tasks; {demo_n} demo-role items. Dev comparators: {dev.T} tasks, unit = task.")

# ---------------------------------------------------------------- acceptance rules
w("\n## Acceptance rules (real and demo roles)\n")
w("| Rule | Real role | Coverage | Demo roles | Dev (1,147, by task) |")
w("|---|---|---|---|---|")
J["rules"] = {}
RULES = [("FA-LOO + (c)", "fc"), ("FA-LOO (a)+(b)", "fa"), ("(a) only, full-data answer", "a"), ("v5 heuristic (2 attempts)", "v5"), ("v5 heuristic, top answer only", "v5t"),
         ("P4 confident (2 attempts)", "p4"), ("fit to demos only (2 attempts)", "fit"), ("fit to demos only, top answer only", "fitt")]
vecs = {}
for name, fld in RULES:
    r = d.vec("full", f(fld), "real")
    dm = d.vec("full", f(fld), "demo")
    dv = dev.vec("full", f(fld), "real")
    vecs[fld] = r
    pr, pd, pv = prec(d, *r, real_n), prec(d, *dm, demo_n), prec(dev, *dv, dev.T)
    J["rules"][fld] = dict(real=pr, demo=pd, dev=pv)
    w(f"| {name} | {fmt(pr)} | {100 * pr['coverage']:.1f}% | {fmt(pd)} | {fmt(pv)} |")
pv = count_ci(d, p2vec(d, "full"))
w(f"\npass@2, real role: {pv['total']:.0f}/{real_n} = {100 * pv['total'] / real_n:.1f}% (count CI [{pv['ci'][0]:.0f}, {pv['ci'][1]:.0f}]); tasks with at least one solve: {solved_tasks(p2vec(d, 'full'))}/{d.T}. "
  f"Items with any candidate: {int(d.vec('full', lambda o: 1.0 if o['has'] else None)[1].sum())}.")
J["pass2"] = dict(total=pv["total"], ci=pv["ci"], tasks=solved_tasks(p2vec(d, "full")))
fc = vecs["fc"]
j = (fc[1] - fc[0])
w(f"Joint P(answer and wrong), FA-LOO + (c), real role: {j.sum():.0f}/{real_n} = {100 * j.sum() / real_n:.2f}%. Task-level: {int((fc[1] > 0).sum())} tasks answered, {int(((fc[1] - fc[0]) > 0).sum())} with a wrong answer; "
  f"mean per-task precision {100 * J['rules']['fc']['real']['task_mean_precision']:.1f}%.")

# ---------------------------------------------------------------- T1
w("\n## Test 1. Frames\n")
J["frames"] = {}
ARMS = {"behaviour alone": {"canon": "beh:canon", "abs": "beh:abs", "both": "behavior alone", "global": "beh:global"},
        "system": {"canon": "sys:canon", "abs": "sys:abs", "both": "full", "global": "sys:global", "no behaviour": "-behavior"}}
for level, arms in ARMS.items():
    w(f"**{level}.**\n")
    w("| Arm | pass@2 (tasks) | top answer at evidence >= 0.99 | v5 rule | FA-LOO + (c) real | FA-LOO + (c) demo | Dev: pass@2; >=0.99; v5; FA-LOO + (c) |")
    w("|---|---|---|---|---|---|---|")
    J["frames"][level] = {}
    for arm, cfg in arms.items():
        pv = p2vec(d, cfg)
        pd = p2vec(dev, cfg)
        a, b, c, e = (prec(d, *d.vec(cfg, loo1)), prec(d, *d.vec(cfg, f("v5"))), prec(d, *d.vec(cfg, f("fc"))), prec(d, *d.vec(cfg, f("fc"), "demo")))
        da, db, dc = prec(dev, *dev.vec(cfg, loo1)), prec(dev, *dev.vec(cfg, f("v5"))), prec(dev, *dev.vec(cfg, f("fc")))
        J["frames"][level][arm] = dict(pass2=float(pv.sum()), pass2_tasks=solved_tasks(pv), loo1=a, v5=b, fc=c, fc_demo=e, dev=dict(pass2=float(pd.sum()), loo1=da, v5=db, fc=dc))
        w(f"| {arm} | {pv.sum():.0f} ({solved_tasks(pv)}) | {fmt(a)} | {fmt(b)} | {fmt(c)} | {fmt(e)} | {pd.sum():.0f}; {da['correct']:.0f}/{da['answered']}; {db['correct']:.0f}/{db['answered']}; {dc['correct']:.0f}/{dc['answered']} |")
    w("")
w("**Paired comparisons** (pass@2 total, pairs; CI on the paired difference; sign test on discordant tasks).\n")
w(f"| Level | Comparison | {TAG} real role | {TAG} demo roles | Dev |")
w("|---|---|---|---|---|")
J["frames"]["paired"] = {}
for level, arms in ARMS.items():
    for x, y in (("canon", "abs"), ("both", "canon"), ("canon", "global"), ("abs", "global")):
        cx, cy = arms[x], arms[y]
        A = count_diff(d, p2vec(d, cx), p2vec(d, cy))
        A2 = count_diff(d, p2vec(d, cx, "demo"), p2vec(d, cy, "demo"))
        D = count_diff(dev, p2vec(dev, cx), p2vec(dev, cy))
        J["frames"]["paired"][f"{level}:{x}-{y}"] = dict(real=A, demo=A2, dev=D)
        w(f"| {level} | {x} minus {y} | {fmtc(A)} | {fmtc(A2)} | {fmtc(D)} |")
w("\n**Wrong answers added by `both` over `canon`** (wrong count both minus canon; negative = fewer).\n")
w("| Level | Rule | Real role | Dev |")
w("|---|---|---|---|")
for level, arms in ARMS.items():
    for rn, g in (("evidence >= 0.99", loo1), ("v5", f("v5")), ("FA-LOO + (c)", f("fc"))):
        ca, aa = d.vec(arms["both"], g)
        cb, ab = d.vec(arms["canon"], g)
        wa, wb = aa - ca, ab - cb
        dca, daa = dev.vec(arms["both"], g)
        dcb, dab = dev.vec(arms["canon"], g)
        Dd = count_diff(dev, daa - dca, dab - dcb)
        A = count_diff(d, wa, wb)
        w(f"| {level} | {rn} | {fmtc(A)} | {fmtc(Dd)} |")
w("\nItems solved by exactly one of canon / abs, behaviour alone:")
cn, ab = p2vec(d, "beh:canon"), p2vec(d, "beh:abs")
ks = lambda cfg: {k for k in d.keys if rows[k]["cfg"][cfg][str(rows[k]["m"] - 1)]["p2"] > 0}
w(f"- canon only: {sorted(ks('beh:canon') - ks('beh:abs'))}")
w(f"- abs only: {sorted(ks('beh:abs') - ks('beh:canon'))}")
w(f"- global only (vs canon): {sorted(ks('beh:global') - ks('beh:canon'))}; canon only (vs global): {sorted(ks('beh:canon') - ks('beh:global'))}")
J["frames"]["sets"] = dict(canon_only=sorted(ks("beh:canon") - ks("beh:abs")), abs_only=sorted(ks("beh:abs") - ks("beh:canon")),
                           global_only=sorted(ks("beh:global") - ks("beh:canon")), canon_not_global=sorted(ks("beh:canon") - ks("beh:global")))

# ---------------------------------------------------------------- T2
w("\n## Test 2. Prediction\n")
w("**Precision of the top answer by evidence bucket** (buckets fixed on development data).\n")
J["buckets"] = {}


def bucket_row(data, cfg, ev="top_ev", ok="top_ok", role="real"):
    out = {}
    for b in BUCKETS:
        g = lambda o: o[ok] if (o[ev] is not None and bucket(o[ev]) == b) else None
        out[b] = prec(data, *data.vec(cfg, g, role))
    return out


w("| Column, role | >= 0.99 | [0.5, 0.99) | (0, 0.5) | 0 |")
w("|---|---|---|---|---|")
for lab, data, cfg, ev, ok, role in ([("full system, real", d, "full", "top_ev", "top_ok", "real"), ("full system, demo", d, "full", "top_ev", "top_ok", "demo"), ("full system, dev", dev, "full", "top_ev", "top_ok", "real")]
                                     + [(f"{m}, real", d, f"{m} alone", "top_ev", "top_ok", "real") for m in MODULES]
                                     + [(f"{m}, demo", d, f"{m} alone", "top_ev", "top_ok", "demo") for m in MODULES]
                                     + [(f"{m} raw, real", d, f"{m} alone", "raw_ev", "raw_ok", "real") for m in ("behavior", "pattern", "composition")]):
    r = bucket_row(data, cfg, ev, ok, role)
    J["buckets"][lab] = r
    w(f"| {lab} | " + " | ".join(fmt(r[b]) for b in BUCKETS) + " |")
w("\n**T2a. Evidence >= 0.99 minus below 0.99 (top answer, full system).**\n")
J["T2a"] = {}
for lab, data, role in (("real", d, "real"), ("demo", d, "demo"), ("dev", dev, "real")):
    hi = data.vec("full", lambda o: o["top_ok"] if (o["top_ev"] is not None and o["top_ev"] >= 0.99) else None, role)
    lo = data.vec("full", lambda o: o["top_ok"] if (o["top_ev"] is not None and o["top_ev"] < 0.99) else None, role)
    mid = data.vec("full", lambda o: o["top_ok"] if (o["top_ev"] is not None and 0.5 <= o["top_ev"] < 0.99) else None, role)
    low = data.vec("full", lambda o: o["top_ok"] if (o["top_ev"] is not None and o["top_ev"] < 0.5) else None, role)
    x = prec_diff(data, hi, lo)
    x2 = prec_diff(data, hi, mid)
    x3 = prec_diff(data, mid, low)
    au = auroc_cluster(data, "full", role=role)
    J["T2a"][lab] = dict(hi_lo=x, hi_mid=x2, mid_low=x3, auroc=au, hi=prec(data, *hi), lo=prec(data, *lo))
    w(f"- {lab}: {fmt(prec(data, *hi))} vs {fmt(prec(data, *lo))}: {fmtd(x)}. >=0.99 vs [0.5,0.99): {fmtd(x2)}. [0.5,0.99) vs below 0.5: {fmtd(x3)}. AUROC of evidence {au['auroc']:.3f} [{au['ci'][0]:.3f}, {au['ci'][1]:.3f}], n = {au['n']}.")
w("\n**T2b. Paired precision differences, real role (demo roles in brackets where measured).**\n")
J["T2b"] = {}
for x, y in (("v5", "fit"), ("fc", "fit"), ("a", "fit"), ("fc", "v5"), ("fc", "a"), ("v5t", "fitt"), ("fc", "v5t"), ("p4", "v5")):
    A = prec_diff(d, d.vec("full", f(x)), d.vec("full", f(y)))
    A2 = prec_diff(d, d.vec("full", f(x), "demo"), d.vec("full", f(y), "demo"))
    D = prec_diff(dev, dev.vec("full", f(x)), dev.vec("full", f(y)))
    J["T2b"][f"{x}-{y}"] = dict(real=A, demo=A2, dev=D)
    w(f"- {x} minus {y}: real {fmtd(A)}; demo {fmtd(A2)}; dev {fmtd(D)}")
w("\n**T2c. Demo roles minus real role, by rule.**\n")
J["T2c"] = {}
for rn, fld in (("FA-LOO + (c)", "fc"), ("(a) only", "a"), ("v5", "v5"), ("v5 top only", "v5t"), ("fit-only", "fit")):
    x = prec_diff(d, d.vec("full", f(fld), "demo"), d.vec("full", f(fld), "real"))
    J["T2c"][fld] = x
    w(f"- {rn}: {fmtd(x)}")
groups = sorted({k.split("/")[0] for k in d.keys}) if TAG in ("concept", "oned") else []
if groups:
    w("\n**FA-LOO + (c) by concept group, and the gap with each group left out.**\n")
    w("| Group | Real role | Demo roles | v5 real | Gap (demo - real) with this group left out |")
    w("|---|---|---|---|---|")
J["groups_fc"] = {}
for gname in groups:
    keys = [k for k in d.keys if k.split("/")[0] == gname]
    rest = [k for k in d.keys if k.split("/")[0] != gname]
    a, b, c = (prec(d, *d.vec("full", f("fc"), "real", keys)), prec(d, *d.vec("full", f("fc"), "demo", keys)), prec(d, *d.vec("full", f("v5"), "real", keys)))
    gap = prec_diff(d, d.vec("full", f("fc"), "demo", rest), d.vec("full", f("fc"), "real", rest))
    J["groups_fc"][gname] = dict(real=a, demo=b, v5=c, gap_without=gap)
    sh = lambda p: f"{p['correct']:.0f}/{p['answered']}"
    w(f"| {gname} | {sh(a)} | {sh(b)} | {sh(c)} | {fmtd(gap)} |")

# sets
w("\n**Answer sets, real role.**\n")
sets = {}
for fld in ("fc", "fa", "a", "v5", "fit"):
    sets[fld] = {k: rows[k]["cfg"]["full"][str(rows[k]["m"] - 1)][fld] for k in d.keys if rows[k]["cfg"]["full"][str(rows[k]["m"] - 1)][fld] is not None}


def desc(a, b):
    both, ao, bo = set(a) & set(b), set(a) - set(b), set(b) - set(a)
    return dict(both=len(both), both_right_a=sum(float(a[k]) for k in both), a_only=len(ao), a_only_right=sum(float(a[k]) for k in ao), b_only=len(bo), b_only_right=sum(float(b[k]) for k in bo),
                a_only_keys=sorted(ao), b_only_keys=sorted(bo))


J["sets"] = {}
for x, y in (("v5", "fc"), ("v5", "a"), ("fc", "fit"), ("v5", "fit")):
    s = desc(sets[x], sets[y])
    J["sets"][f"{x}|{y}"] = s
    w(f"- {x} vs {y}: both {s['both']} ({s['both_right_a']:.0f} right under {x}); {x} only {s['a_only']} ({s['a_only_right']:.0f} right): {s['a_only_keys']}; {y} only {s['b_only']} ({s['b_only_right']:.0f} right): {s['b_only_keys']}")
wr = {fld: {k for k, v in sets[fld].items() if float(v) < 1} for fld in sets}
w(f"\nWrong, v5: {sorted(wr['v5'])}\n\nWrong, FA-LOO + (c): {sorted(wr['fc'])}\n\nWrong in both: {sorted(wr['v5'] & wr['fc'])}\n\nWrong, v5 only: {sorted(wr['v5'] - wr['fc'])}\n\nWrong, FA-LOO + (c) only: {sorted(wr['fc'] - wr['v5'])}")
J["wrong"] = {fld: sorted(wr[fld]) for fld in wr}
why = collections.Counter(rows[k]["cfg"]["full"][str(rows[k]["m"] - 1)]["why"] for k in d.keys if rows[k]["cfg"]["full"][str(rows[k]["m"] - 1)]["has"])
w(f"\nWhy FA-LOO abstains on items that have a candidate: {dict(why)}")
J["why"] = dict(why)

# ---------------------------------------------------------------- T3
w("\n## Test 3. Voting\n")
w("**T3a. Module contributions, real role.**\n")


def module_table(data, role="real"):
    out = {}
    full = p2vec(data, "full", role)
    item_keys = lambda cfg: {(k, r) for k in data.keys for r in data.roles(k, role) if data.rows[k]["cfg"][cfg][str(r)]["p2"] > 0}
    alone = {m: item_keys(f"{m} alone") for m in MODULES}
    fullset = item_keys("full")
    for m in MODULES:
        others = set().union(*(alone[j] for j in MODULES if j != m))
        loo = item_keys(f"-{m}")
        out[m] = dict(alone=len(alone[m]), alone_tasks=len({data.ktask[k] for k, _ in alone[m]}), lost=len(fullset - loo), gained_when_removed=len(loo - fullset), unique=len(alone[m] - others),
                      unique_tasks=len({data.ktask[k] for k, _ in alone[m] - others}), loo1=prec(data, *data.vec(f"{m} alone", loo1, role)), v5=prec(data, *data.vec(f"{m} alone", f("v5"), role)),
                      fc=prec(data, *data.vec(f"{m} alone", f("fc"), role)), any_cand=int(data.vec(f"{m} alone", lambda o: 1.0 if o["has"] else None, role)[1].sum()))
    union = set().union(*alone.values())
    cnt = collections.Counter(sum(x in alone[m] for m in MODULES) for x in union)
    sm = dict(full=len(fullset), union_alone=len(union), exactly_one=cnt.get(1, 0), two=cnt.get(2, 0), three_plus=sum(v for k, v in cnt.items() if k >= 3),
              lost_by_vote=sorted(map(str, union - fullset)), gained_by_vote=sorted(map(str, fullset - union)))
    return out, sm


mt, ms = module_table(d)
mtd, msd = module_table(d, "demo")
mdev, mdevs = module_table(dev)
J["modules"] = dict(real=mt, real_summary=ms, demo=mtd, demo_summary=msd, dev=mdev, dev_summary=mdevs)
w("| Module | Any candidate | Solves alone (tasks) | Lost when removed | Unique solves (tasks) | Alone, evidence >= 0.99 | Alone, FA-LOO + (c) | Demo: alone / unique | Dev: alone / lost / unique |")
w("|---|---|---|---|---|---|---|---|---|")
for m in MODULES:
    x, y, z = mt[m], mtd[m], mdev[m]
    w(f"| {m} | {x['any_cand']} | {x['alone']} ({x['alone_tasks']}) | {x['lost']} | {x['unique']} ({x['unique_tasks']}) | {fmt(x['loo1'])} | {fmt(x['fc'])} | {y['alone']} / {y['unique']} | {z['alone']} / {z['lost']} / {z['unique']} |")
for lab, s in (("real", ms), ("demo", msd), ("dev", mdevs)):
    w(f"\n{lab}: full {s['full']}, union of modules alone {s['union_alone']}; solved by exactly one module {s['exactly_one']}, two {s['two']}, three or more {s['three_plus']} "
      f"(share exactly one {100 * s['exactly_one'] / max(1, s['union_alone']):.1f}%). Lost by the vote: {len(s['lost_by_vote'])} {s['lost_by_vote'][:12]}; gained by the vote: {len(s['gained_by_vote'])} {s['gained_by_vote'][:12]}.")

w("\n**T3b. Is it a vote? Agreement between modules, and a no-vote baseline.**\n")
J["T3b"] = {}
w("| Population | Top answer backed by 2+ modules | Top answer from 1 module | Difference | No-vote: pass@2 vs pool | No-vote vs pool, top answer at evidence >= 0.99 |")
w("|---|---|---|---|---|---|")
for lab, data, role in (("real", d, "real"), ("demo", d, "demo"), ("dev", dev, "real")):
    many = data.vec("full", lambda o: o["top_ok"] if len(o["top_mods"]) >= 2 else None, role)
    one = data.vec("full", lambda o: o["top_ok"] if len(o["top_mods"]) == 1 else None, role)
    many_h = data.vec("full", lambda o: o["top_ok"] if (len(o["top_mods"]) >= 2 and o["top_ev"] >= 0.99) else None, role)
    one_h = data.vec("full", lambda o: o["top_ok"] if (len(o["top_mods"]) == 1 and o["top_ev"] >= 0.99) else None, role)
    dd = prec_diff(data, many, one)
    dh = prec_diff(data, many_h, one_h)
    nvp = count_diff(data, p2vec(data, "full", role), p2vec(data, "full", role, "nv_p2"))
    nvh = data.vec("full", lambda o: o["nv_ok"] if (o["nv_ev"] is not None and o["nv_ev"] >= 0.99) else None, role)
    pool_h = data.vec("full", loo1, role)
    nvd = prec_diff(data, pool_h, nvh)
    J["T3b"][lab] = dict(many=prec(data, *many), one=prec(data, *one), many_hi=prec(data, *many_h), one_hi=prec(data, *one_h), diff=dd, diff_hi=dh, pool_vs_novote_p2=nvp, novote_hi=prec(data, *nvh), pool_hi=prec(data, *pool_h), pool_vs_novote_hi=nvd)
    w(f"| {lab} | {fmt(prec(data, *many))} | {fmt(prec(data, *one))} | {fmtd(dd)} | pool minus no-vote: {fmtc(nvp)} | pool {fmt(prec(data, *pool_h))}; no-vote {fmt(prec(data, *nvh))}; {fmtd(nvd)} |")
w("")
for lab, x in J["T3b"].items():
    w(f"- {lab}, top evidence >= 0.99 only: 2+ modules {fmt(x['many_hi'])}; 1 module {fmt(x['one_hi'])}; {fmtd(x['diff_hi'])}")

# ---------------------------------------------------------------- T3c
p8path = os.path.join(RES, f"{TAG}_p8.jsonl")
if os.path.exists(p8path):
    P8 = load_dataset(TAG, "p8")
    merged = {k: dict(m=rows[k]["m"], cfg=dict(rows[k]["cfg"], **P8[k]["cfg"])) for k in d.keys if k in P8}
    e = Data(merged, tasker=TASKER)
    w(f"\n**T3c. 8 D8 views vs 1 view** ({len(merged)} of {len(rows)} items).\n")
    w("| Rule | 1 view, real | 8 views, real | Wrong 8 minus 1 | Precision 8 minus 1 | 1 view, demo | 8 views, demo |")
    w("|---|---|---|---|---|---|---|")
    J["p8"] = {}
    for rn, fld in (("v5 rule", "v5"), ("v5 rule, top answer only", "v5t"), ("P4", "p4"), ("FA-LOO (v5 vote) + (c)", "fc"), ("FA-LOO (P4 vote) + (c)", "fc4"), ("FA-LOO (v5 vote)", "fa"), ("(a) only", "a")):
        a, b = e.vec("full", f(fld)), e.vec("p8", f(fld))
        a2, b2 = e.vec("full", f(fld), "demo"), e.vec("p8", f(fld), "demo")
        cw = count_diff(e, b[1] - b[0], a[1] - a[0])
        dp = prec_diff(e, b, a)
        J["p8"][fld] = dict(v1=prec(e, *a), v8=prec(e, *b), wrong_diff=cw, prec_diff=dp, v1_demo=prec(e, *a2), v8_demo=prec(e, *b2), wrong_diff_demo=count_diff(e, b2[1] - b2[0], a2[1] - a2[0]), prec_diff_demo=prec_diff(e, b2, a2))
        w(f"| {rn} | {fmt(prec(e, *a))} | {fmt(prec(e, *b))} | {fmtc(cw)} | {fmtd(dp)} | {fmt(prec(e, *a2))} | {fmt(prec(e, *b2))} |")
    w("")
    for x, y, lab in (("v5", "p4", "8-view v5 minus 8-view P4"), ("v5", "fc", "8-view v5 minus 8-view FA-LOO + (c)"), ("p4", "fc", "8-view P4 minus 8-view FA-LOO + (c)")):
        z = prec_diff(e, e.vec("p8", f(x)), e.vec("p8", f(y)))
        z2 = prec_diff(e, e.vec("p8", f(x), "demo"), e.vec("p8", f(y), "demo"))
        J["p8"][lab] = dict(real=z, demo=z2)
        w(f"- {lab}: real {fmtd(z)}; demo {fmtd(z2)}")
    pa, pb = p2vec(e, "full"), p2vec(e, "p8")
    J["p8"]["pass2"] = count_diff(e, pb, pa)
    w(f"- pass@2, 8 views minus 1 view: {fmtc(J['p8']['pass2'])}")
    getk = lambda cfg, fld, wrong: {k for k in e.keys if (lambda v: v is not None and (float(v) < 1 if wrong else True))(merged[k]["cfg"][cfg][str(merged[k]["m"] - 1)][fld])}
    w(f"- New wrong under 8-view v5: {sorted(getk('p8', 'v5', True) - getk('full', 'v5', True))}")
    w(f"- Wrong at 1-view v5 no longer wrong at 8 views: {sorted(getk('full', 'v5', True) - getk('p8', 'v5', True))}")
    w(f"- Wrong under 8-view P4: {sorted(getk('p8', 'p4', True))}")
    w(f"- Wrong under 8-view FA-LOO + (c): {sorted(getk('p8', 'fc', True))}")
    w(f"- 1-view v5 answers not answered at 8-view FA-LOO + (c): {len(getk('full', 'v5', False) - getk('p8', 'fc', False))}")
    J["p8"]["new_wrong_v5"] = sorted(getk("p8", "v5", True) - getk("full", "v5", True))
    J["p8"]["wrong_p4"] = sorted(getk("p8", "p4", True))
    J["p8"]["wrong_fc"] = sorted(getk("p8", "fc", True))

# ---------------------------------------------------------------- T4
if TAG == "concept":
    from xlsx_read import rows as xl
    X = xl(os.path.join(os.path.dirname(HERE), "..", "external", "judge", "conceptarc", "repo", "data.xlsx"))
    head = X["Machine Solver Performance"][0]
    im = {n: head.index(n) for n in ("First Place ARC-Kaggle", "Second Place ARC-Kaggle", "GPT-4, Temperature 0")}
    mach = {}
    for r in X["Machine Solver Performance"][1:]:
        if not r or r[0] is None or "Minimal" in r[0]:
            continue
        name = r[0].replace(".json", "")
        gname = next((g for g in groups if name.startswith(g)), None)
        if gname and name[len(gname):].isdigit():
            mach[f"{gname}/{name}#{r[1]}"] = {n: (r[i] if i < len(r) else None) for n, i in im.items()}
    hum = {}
    for r in X["Human Performance"][1:]:
        if not r or r[0] is None or "Minimal" in r[0]:
            continue
        name = r[0].replace(".json", "")
        gname = next((g for g in groups if name.startswith(g)), None)
        if gname and name[len(gname):].isdigit():
            hum[f"{gname}/{name}#{r[1]}"] = (float(r[2]), float(r[4]))
    w("\n## Test 4. By concept group\n")
    w("| Group | pass@2 /30 [CI] | Tasks solved /10 | Any candidate | Solving modules (items) | Kaggle 1st | Kaggle 2nd | GPT-4 T0 | Humans | Solved by Monty and Kaggle 1st |")
    w("|---|---|---|---|---|---|---|---|---|---|")
    J["concept_groups"] = {}
    tot = collections.Counter()
    for gname in sorted(groups, key=lambda g: sum(rows[k]["cfg"]["full"][str(rows[k]["m"] - 1)]["p2"] for k in d.keys if k.split("/")[0] == g)):
        keys = [k for k in d.keys if k.split("/")[0] == gname]
        v = d.vec("full", f("p2"), "real", keys)[0]
        ci = count_ci(d, v)["ci"]
        mods = collections.Counter()
        for k in keys:
            for m in MODULES:
                if rows[k]["cfg"][f"{m} alone"][str(rows[k]["m"] - 1)]["p2"] > 0:
                    mods[m] += 1
        cand = sum(rows[k]["cfg"]["full"][str(rows[k]["m"] - 1)]["has"] for k in keys)
        c1 = sum(mach.get(k, {}).get("First Place ARC-Kaggle") == "CORRECT" for k in keys)
        c2 = sum(mach.get(k, {}).get("Second Place ARC-Kaggle") == "CORRECT" for k in keys)
        c3 = sum(mach.get(k, {}).get("GPT-4, Temperature 0") == "CORRECT" for k in keys)
        hs = [hum[k] for k in keys if k in hum]
        ha = np.mean([s / n for s, n in hs]) if hs else float("nan")
        both = sum((rows[k]["cfg"]["full"][str(rows[k]["m"] - 1)]["p2"] > 0) and mach.get(k, {}).get("First Place ARC-Kaggle") == "CORRECT" for k in keys)
        J["concept_groups"][gname] = dict(p2=float(v.sum()), ci=ci, tasks=int((v > 0).sum()), any_candidate=int(cand), modules=dict(mods), kaggle1=c1, kaggle2=c2, gpt4=c3, human=float(ha), both_kaggle1=both)
        tot.update(dict(p2=v.sum(), k1=c1, k2=c2, g=c3, both=both, cand=cand, m=len(keys)))
        w(f"| {gname} | {v.sum():.0f} [{ci[0]:.0f}, {ci[1]:.0f}] | {int((v > 0).sum())} | {cand} | " + (", ".join(f"{m} {n}" for m, n in mods.most_common()) or "-") + f" | {c1} | {c2} | {c3} | {100 * ha:.0f}% | {both} |")
    allh = [hum[k] for k in d.keys if k in hum]
    w(f"| **All** | {tot['p2']:.0f}/{real_n} | | {tot['cand']} | | {tot['k1']} | {tot['k2']} | {tot['g']} | {100 * np.mean([s / n for s, n in allh]):.0f}% | {tot['both']} |")
    J["concept_groups_total"] = {k: float(v) for k, v in tot.items()}
    J["concept_groups_total"]["human"] = float(np.mean([s / n for s, n in allh]))
    J["n_mach"] = len(mach)
    J["n_hum"] = len(hum)

open(os.path.join(RES, f"{TAG}_tables.md"), "w").write("\n".join(L) + "\n")
json.dump(J, open(os.path.join(RES, f"{TAG}_analysis.json"), "w"), indent=1, default=float)
print("wrote", TAG, "tables and analysis")
