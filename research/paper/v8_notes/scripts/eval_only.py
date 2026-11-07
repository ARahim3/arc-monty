"""v8 paper: re-derive every development comparator on PUBLIC-EVAL tasks only (no training tasks), from existing caches.
Same statistics code as research/monty_heldout (stats.py; B = 10,000, seed 0, cluster = task). No solver run.
usage: ../../../../.venv/bin/python eval_only.py > ../eval_only.txt ; writes ../eval_only.json"""
import os  # noqa: E402  (release: paths from the repo root)
_REPO = os.environ.get("ARC_MONTY_ROOT", os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..")))  # repo root
import collections, json, os, sys
ROOT = _REPO
sys.path.insert(0, os.path.join(ROOT, "research", "monty_heldout"))
import numpy as np
from hl_common import MODULES
from stats import Data, auroc_cluster, bucket, BUCKETS, count_diff, f, fmt, fmtc, fmtd, load_rows, prec, prec_diff

HERE = os.path.dirname(os.path.abspath(__file__))
rows_all = load_rows(os.path.join(ROOT, "research", "monty_heldout", "results", "dev_base.jsonl"))
print("splits", collections.Counter(r["split"] for r in rows_all.values()))
J = {}

def dataset(splits):
    rows = {k: dict(m=1, split=r["split"], n=r["n"], T=r["T"], cfg={c: {"0": o} for c, o in r["cfg"].items()})
            for k, r in rows_all.items() if r["split"] in splits}
    return rows, Data(rows, group=lambda k: rows[k]["split"], tasker=lambda k: k)

def loo1(o):
    return o["top_ok"] if (o["top_ev"] is not None and o["top_ev"] >= 0.99) else None

def table(name, splits):
    rows, d = dataset(splits)
    out = {"tasks": d.T, "mean_bound": float(np.mean([1 / (r["n"] + 1) for r in rows.values()]))}
    print(f"\n=== {name}: {d.T} tasks; mean 1/(n+1) = {out['mean_bound']:.4f}; multi-test tasks = {sum(r['T']>1 for r in rows.values())}")
    for rn, fld in (("FA-LOO+(c)", "fc"), ("FA-LOO (a)+(b)", "fa"), ("(a) only", "a"), ("v5", "v5"), ("v5 top", "v5t"), ("fit", "fit"), ("fit top", "fitt"), ("P4", "p4")):
        p = prec(d, *d.vec("full", f(fld)), d.T)
        out[fld] = p
        print(f"{rn:16s} {fmt(p)} cov {100*p['coverage']:.1f}% tasks_answered {p['tasks_answered']} tasks_wrong {p['tasks_wrong']}")
    p2 = d.vec("full", f("p2"))[0]
    out["pass2"] = float(p2.sum())
    print("pass@2", p2.sum(), f"{100*p2.sum()/d.T:.1f}%", "any candidate", int(d.vec("full", lambda o: 1.0 if o["has"] else None)[1].sum()))
    fc = d.vec("full", f("fc"))
    print("joint P(answer and wrong) FA-LOO+(c)", (fc[1]-fc[0]).sum(), f"{100*(fc[1]-fc[0]).sum()/d.T:.2f}%")
    out["joint"] = float((fc[1]-fc[0]).sum()/d.T)
    for x, y in (("v5", "fit"), ("fc", "fit"), ("a", "fit"), ("fc", "v5"), ("fc", "a")):
        D = prec_diff(d, d.vec("full", f(x)), d.vec("full", f(y)))
        out[f"{x}-{y}"] = D
        print(f"{x} minus {y}: {fmtd(D)}")
    hi = d.vec("full", lambda o: o["top_ok"] if (o["top_ev"] is not None and o["top_ev"] >= 0.99) else None)
    lo = d.vec("full", lambda o: o["top_ok"] if (o["top_ev"] is not None and o["top_ev"] < 0.99) else None)
    out["hi-lo"] = prec_diff(d, hi, lo)
    print("evidence >=0.99 minus below:", fmtd(out["hi-lo"]), fmt(prec(d, *hi)), fmt(prec(d, *lo)))
    au = auroc_cluster(d, "full")
    out["auroc"] = au
    print("AUROC", round(au["auroc"], 3), [round(x, 3) for x in au["ci"]], "n", au["n"])
    bk = {}
    for b in BUCKETS:
        g = lambda o: o["top_ok"] if (o["top_ev"] is not None and bucket(o["top_ev"]) == b) else None
        bk[b] = prec(d, *d.vec("full", g))
        print(" bucket", b, fmt(bk[b]))
    out["buckets"] = bk
    # modules
    keys = lambda cfg: {k for k in d.keys if rows[k]["cfg"][cfg]["0"]["p2"] > 0}
    alone = {m: keys(f"{m} alone") for m in MODULES}
    fullset = keys("full")
    union = set().union(*alone.values())
    cnt = collections.Counter(sum(x in alone[m] for m in MODULES) for x in union)
    print("modules: full", len(fullset), "union alone", len(union), "exactly one", cnt.get(1, 0), "lost by vote", sorted(union - fullset), "gained", sorted(fullset - union))
    mt = {}
    for m in MODULES:
        others = set().union(*(alone[j] for j in MODULES if j != m))
        lost = len(fullset - keys(f"-{m}"))
        l1 = prec(d, *d.vec(f"{m} alone", loo1))
        mt[m] = dict(alone=len(alone[m]), lost=lost, unique=len(alone[m] - others), loo1=l1)
        print(f"  {m:12s} alone {len(alone[m]):3d} lost {lost:3d} unique {len(alone[m]-others):3d} evidence>=.99 {l1['correct']:.0f}/{l1['answered']}")
    out["modules"] = mt
    out["modules_summary"] = dict(full=len(fullset), union=len(union), exactly_one=cnt.get(1, 0), lost_by_vote=sorted(union - fullset), gained=sorted(fullset - union))
    # no-vote baseline
    pool_h = d.vec("full", loo1)
    nvh = d.vec("full", lambda o: o["nv_ok"] if (o["nv_ev"] is not None and o["nv_ev"] >= 0.99) else None)
    nvp = count_diff(d, d.vec("full", f("p2"))[0], d.vec("full", f("nv_p2"))[0])
    many = d.vec("full", lambda o: o["top_ok"] if len(o["top_mods"]) >= 2 else None)
    one = d.vec("full", lambda o: o["top_ok"] if len(o["top_mods"]) == 1 else None)
    out["novote"] = dict(pool=prec(d, *pool_h), novote=prec(d, *nvh), diff=prec_diff(d, pool_h, nvh), p2=nvp, many=prec(d, *many), one=prec(d, *one))
    print("pool vs no-vote: pool", fmt(prec(d, *pool_h)), "novote", fmt(prec(d, *nvh)), fmtd(prec_diff(d, pool_h, nvh)), "| p2", fmtc(nvp))
    print("2+ modules", fmt(prec(d, *many)), "1 module", fmt(prec(d, *one)))
    # frames
    fr = {}
    for lvl, arms in (("beh", {"canon": "beh:canon", "abs": "beh:abs", "both": "behavior alone", "global": "beh:global"}),
                      ("sys", {"canon": "sys:canon", "abs": "sys:abs", "both": "full", "global": "sys:global", "none": "-behavior"})):
        fr[lvl] = {}
        for arm, cfg in arms.items():
            v = d.vec(cfg, f("p2"))[0]
            fr[lvl][arm] = dict(p2=float(v.sum()), loo1=prec(d, *d.vec(cfg, loo1)), v5=prec(d, *d.vec(cfg, f("v5"))), fc=prec(d, *d.vec(cfg, f("fc"))))
            print(f" {lvl} {arm:7s} p2 {v.sum():5.0f} >=.99 {fr[lvl][arm]['loo1']['correct']:.0f}/{fr[lvl][arm]['loo1']['answered']} v5 {fr[lvl][arm]['v5']['correct']:.0f}/{fr[lvl][arm]['v5']['answered']} fc {fr[lvl][arm]['fc']['correct']:.0f}/{fr[lvl][arm]['fc']['answered']}")
        for x, y in (("canon", "abs"), ("both", "canon"), ("canon", "global"), ("abs", "global")):
            cd = count_diff(d, d.vec(arms[x], f("p2"))[0], d.vec(arms[y], f("p2"))[0])
            fr[lvl][f"{x}-{y}"] = cd
            print(f" {lvl} {x} minus {y}: {fmtc(cd)}")
    out["frames"] = fr
    return out

J["public_eval_514"] = table("public eval, ARC-AGI-1 eval + ARC-AGI-2 eval (distinct)", {"agi1-eval", "agi2-eval"})
J["agi2_eval"] = table("ARC-AGI-2 public eval, 114 not in ARC-AGI-1", {"agi2-eval"})
J["agi1_eval"] = table("ARC-AGI-1 eval", {"agi1-eval"})

# rotation on the eval subset
rot = os.path.join(ROOT, "research", "paper", "review_scratch", "rotate_distinct.jsonl")
rrows = [json.loads(l) for l in open(rot)]
print("\n=== rotation, rotate_distinct.jsonl:", len(rrows), "tasks; splits", collections.Counter(r["split"] for r in rrows))

def analyse(r):
    m, H, F, Full = r["m"], r["truth"], r["folds"], r["full"]
    out = []
    for a in range(m):
        ans, E, preds = True, True, set()
        for b in range(m):
            if b == a:
                continue
            p = F[f"{a},{b}"]
            if p is None:
                ans = E = False
                continue
            if p[0] != H[b]:
                ans = E = False
            preds.add(p[1])
            if p[1] == H[a]:
                E = False
        ansb = ans and len(preds) == 1
        y = next(iter(preds)) if ansb else None
        c = ansb and Full[str(a)] == y
        out.append(dict(ans=ansb, c=c, wrong=ansb and y != H[a], E=E))
    return out

def rot_summary(name, sel):
    rs = [r for r in rrows if sel(r)]
    per = [(r, analyse(r)) for r in rs]
    ev = [sum(x["E"] for x in R) for _, R in per]
    n = len(rs)
    mean_bound = np.mean([1 / r["m"] for r in rs])
    real_ans = sum(R[-1]["c"] for _, R in per)
    real_wrong = sum(R[-1]["c"] and R[-1]["wrong"] for _, R in per)
    dem = [x for _, R in per for x in R[:-1]]
    demo_ans = sum(x["c"] for x in dem)
    demo_wrong = sum(x["c"] and x["wrong"] for x in dem)
    Jc = [sum(x["c"] and x["wrong"] for x in R) / r["m"] for r, R in per]
    A = [sum(x["c"] for x in R) / r["m"] for r, R in per]
    s = dict(tasks=n, with_event=sum(e >= 1 for e in ev), two_plus=sum(e >= 2 for e in ev), share=sum(e >= 1 for e in ev) / n, mean_bound=float(mean_bound),
             real=f"{real_ans-real_wrong}/{real_ans}", demo=f"{demo_ans-demo_wrong}/{demo_ans}", demo_roles=len(dem),
             role_joint=float(np.mean(Jc)), role_answer=float(np.mean(A)), role_precision=float(1 - sum(Jc) / sum(A)),
             event_times_bound=float(np.mean([(e >= 1) / r["m"] for e, (r, _) in zip(ev, per)])))
    print(name, json.dumps(s))
    return s

J["rotation"] = dict(all=rot_summary("all 1,147", lambda r: True),
                     public_eval=rot_summary("public eval", lambda r: r["split"] in ("agi1-eval", "agi2-eval")),
                     agi2_eval=rot_summary("agi2 eval", lambda r: r["split"] == "agi2-eval"))
sym_tot = sym_diff = 0
for r in rrows:
    m = r["m"]
    for a in range(m):
        for b in range(a + 1, m):
            p, q = r["folds"][f"{a},{b}"], r["folds"][f"{b},{a}"]
            sym_tot += 1
            same = (p is None and q is None) or (p is not None and q is not None and p[0] == q[1] and p[1] == q[0])
            sym_diff += not same
print("query-order symmetry", sym_tot, sym_diff)
J["rotation"]["symmetry"] = dict(pairs=sym_tot, differ=sym_diff)
json.dump(J, open(os.path.join(HERE, "..", "eval_only.json"), "w"), indent=1, default=float)
