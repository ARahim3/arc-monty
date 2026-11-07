"""v8 revision: own re-derivations on Monty-ARC from existing caches (no solver run). Sections:
 1 discordant-pair test of exchangeability (each real-role fold model: right on held-out demo vs right on test; abstain = wrong)
 2 (a) passes but (b) fails, all roles
 3 fold-vote arm, cluster bootstrap against fit-only
 4 sensitivity: cluster-balanced precision, without dominant types, by n
 5 top answer that fits; four evidence buckets
 6 pass@2 8 views minus 1, real and demo roles
 7 vetoes of the 2:1 rule, from candidates, with frozen vote code
Output: ../revise_monty.txt (stdout) and ../revise_monty.json"""
import os  # noqa: E402  (release: paths from the repo root)
_REPO = os.environ.get("ARC_MONTY_ROOT", os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..")))  # repo root
import collections, json, os, sys
ROOT = _REPO
HL = os.path.join(ROOT, "research/monty_heldout")
sys.path.insert(0, HL); sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, "research/monty_eval"))
import numpy as np
from scipy import stats as st
from hl_common import items_from_dir, h, task_of
from stats import Data, f, load_rows, prec, prec_diff, count_diff, _pct
SETS = {"concept": "external/judge/conceptarc/repo/corpus", "mini": "external/heldout/mini-arc/data/MiniARC", "oned": "external/heldout/1d-arc/dataset"}
TASKER = {"oned": lambda k: k.split("/")[0]}
rng0 = lambda: np.random.default_rng(0)
J = {}
def boot_ci(num, den=None, B=10000):
    """cluster bootstrap of sum(num)/sum(den) or sum(num)"""
    T = len(num); W = rng0().multinomial(T, np.full(T, 1 / T), size=B)
    if den is None:
        return _pct((W @ num).astype(float))
    with np.errstate(invalid="ignore", divide="ignore"):
        return _pct((W @ num) / (W @ den))

print("== 1. Discordant-pair test, real role, each fold model. Abstain counts as wrong.")
def report(tag, per):  # per: cluster -> list of (held_right, test_right)
    cl = sorted(per)
    H = np.array([sum(x[0] for x in per[c]) for c in cl], float)
    Te = np.array([sum(x[1] for x in per[c]) for c in cl], float)
    N = np.array([len(per[c]) for c in cl], float)
    A = np.array([sum(x[0] * (1 - x[1]) for x in per[c]) for c in cl], float)
    Bb = np.array([sum((1 - x[0]) * x[1] for x in per[c]) for c in cl], float)
    ci = boot_ci(H - Te, N)
    more, less = int(((A - Bb) > 1e-9).sum()), int(((A - Bb) < -1e-9).sum())
    p = float(st.binomtest(more, more + less, 0.5).pvalue) if more + less else None
    out = dict(folds=int(N.sum()), held=float(H.sum()), test=float(Te.sum()), held_rate=float(H.sum() / N.sum()), test_rate=float(Te.sum() / N.sum()),
               diff=float((H.sum() - Te.sum()) / N.sum()), ci=ci, held_only=float(A.sum()), test_only=float(Bb.sum()), clusters=len(cl), clusters_more_held=more, clusters_more_test=less, sign_p=p)
    print(f"{tag:11s} folds {out['folds']:5d} clusters {len(cl):4d} | held {out['held']:.1f} ({100*out['held_rate']:.1f}%) test {out['test']:.1f} ({100*out['test_rate']:.1f}%) | diff {100*out['diff']:+.1f} [{100*ci[0]:+.1f}, {100*ci[1]:+.1f}] | discordant held-only {out['held_only']:.1f} test-only {out['test_only']:.1f} | clusters {more}:{less} sign p {p}")
    return out
for tag, path in SETS.items():
    rows = load_rows(os.path.join(HL, "results", f"{tag}_base.jsonl"))
    items = dict(items_from_dir(os.path.join(ROOT, path)))
    per = collections.defaultdict(list)
    tk = TASKER.get(tag, task_of)
    for k, r in rows.items():
        m = r["m"]; H = [h(y) for _, y in items[k]]
        o = r["cfg"]["full"][str(m - 1)]
        for b in range(m - 1):
            p = o["fold_h"][str(b)]
            per[tk(k)].append((0.0, 0.0) if p is None else (float(p[0] == H[b]), float(p[1] == H[m - 1])))
    J["exch_" + tag] = report(tag, per)
    if tag == "oned":
        per2 = collections.defaultdict(list)
        # task-level clusters, descriptive
        for k, r in rows.items():
            m = r["m"]; H = [h(y) for _, y in items[k]]
            o = r["cfg"]["full"][str(m - 1)]
            for b in range(m - 1):
                p = o["fold_h"][str(b)]
                per2[task_of(k)].append((0.0, 0.0) if p is None else (float(p[0] == H[b]), float(p[1] == H[m - 1])))
        J["exch_oned_by_task"] = report("oned/task", per2)
rot = [json.loads(l) for l in open(os.path.join(ROOT, "research/paper/review_scratch/rotate_distinct.jsonl"))]
for name, sel in (("public eval", ("agi1-eval", "agi2-eval")), ("agi2 eval", ("agi2-eval",))):
    per = collections.defaultdict(list)
    for r in rot:
        if r["split"] not in sel:
            continue
        m, T, F = r["m"], r["truth"], r["folds"]
        for b in range(m - 1):
            p = F[f"{m-1},{b}"]
            per[r["task"]].append((0.0, 0.0) if p is None else (float(p[0] == T[b]), float(p[1] == T[m - 1])))
    J["exch_" + name.replace(" ", "_")] = report(name, per)

print("\n== 2. (a) passes and (b) fails")
tot = 0; passa = 0; bfail = 0
for tag, path in list(SETS.items()) + [("minimal", "external/judge/conceptarc/repo/MinimalTasks")]:
    rows = load_rows(os.path.join(HL, "results", f"{tag}_base.jsonl"))
    items = dict(items_from_dir(os.path.join(ROOT, path)))
    pa = bf = rr = 0
    for k, r in rows.items():
        m = r["m"]; H = [h(y) for _, y in items[k]]
        for a in range(m):
            rr += 1
            o = r["cfg"]["full"][str(a)]
            fh = o["fold_h"]
            if any(fh[str(b)] is None or fh[str(b)][0] != H[b] for b in range(m) if b != a):
                continue
            pa += 1
            if len({fh[str(b)][1] for b in range(m) if b != a}) > 1:
                bf += 1
    print(tag, "roles", rr, "pass (a)", pa, "(a) passes, (b) fails", bf)
    tot += rr; passa += pa; bfail += bf
print("unseen total roles", tot, "pass (a)", passa, "(b) fails", bfail)
J["b_unseen"] = dict(roles=tot, pass_a=passa, b_fail=bfail)
pa = bf = rr = 0; ev_pa = ev_bf = 0
for r in rot:
    m, T, F = r["m"], r["truth"], r["folds"]
    for a in range(m):
        rr += 1
        ps = [F[f"{a},{b}"] for b in range(m) if b != a]
        heldok = all(F[f"{a},{b}"] is not None and F[f"{a},{b}"][0] == T[b] for b in range(m) if b != a)
        if not heldok:
            continue
        pa += 1
        dis = len({p[1] for p in ps}) > 1
        bf += dis
        if r["split"] in ("agi1-eval", "agi2-eval"):
            ev_pa += 1; ev_bf += dis
print("development: roles", rr, "pass (a)", pa, "(b) fails", bf, "| public eval: pass (a)", ev_pa, "(b) fails", ev_bf)
J["b_dev"] = dict(roles=rr, pass_a=pa, b_fail=bf, eval_pass_a=ev_pa, eval_b_fail=ev_bf)

print("\n== 3. Fold-vote arm, real role: all folds answer and agree on the test (n >= 2), no held-out check")
for tag, path in SETS.items():
    rows = load_rows(os.path.join(HL, "results", f"{tag}_base.jsonl"))
    items = dict(items_from_dir(os.path.join(ROOT, path)))
    tk = TASKER.get(tag, task_of)
    cl = sorted({tk(k) for k in rows}); ix = {c: i for i, c in enumerate(cl)}
    vc, va, fc, fa, bc, ba, nc, na = [np.zeros(len(cl)) for _ in range(8)]
    for k, r in rows.items():
        m = r["m"]; n = m - 1; H = [h(y) for _, y in items[k]]; i = ix[tk(k)]
        o = r["cfg"]["full"][str(m - 1)]; fh = o["fold_h"]
        if o["fit"] is not None:
            fc[i] += float(o["fit"]); fa[i] += 1
        ans = [fh[str(b)][1] for b in range(n) if fh[str(b)] is not None]
        if n >= 2 and len(ans) == n and len(set(ans)) == 1:
            right = float(ans[0] == H[n])
            vc[i] += right; va[i] += 1
            if all(fh[str(b)][0] == H[b] for b in range(n)):
                bc[i] += right; ba[i] += 1
            else:
                nc[i] += right; na[i] += 1
    W = rng0().multinomial(len(cl), np.full(len(cl), 1 / len(cl)), size=10000)
    with np.errstate(invalid="ignore", divide="ignore"):
        d = (W @ vc) / (W @ va) - (W @ fc) / (W @ fa)
    ci = _pct(d)
    est = vc.sum() / va.sum() - fc.sum() / fa.sum()
    print(f"{tag}: folds agree {vc.sum():.0f}/{va.sum():.0f} = {100*vc.sum()/va.sum():.1f}%; fit {fc.sum():.0f}/{fa.sum():.0f}; minus fit {100*est:+.1f} [{100*ci[0]:+.1f}, {100*ci[1]:+.1f}]; with (a) {bc.sum():.0f}/{ba.sum():.0f}; without (a) {nc.sum():.0f}/{na.sum():.0f}")
    J["vote_" + tag] = dict(agree=(float(vc.sum()), float(va.sum())), fit=(float(fc.sum()), float(fa.sum())), diff=float(est), ci=ci, with_a=(float(bc.sum()), float(ba.sum())), without_a=(float(nc.sum()), float(na.sum())))

print("\n== 4. Sensitivity")
for tag in SETS:
    rows = load_rows(os.path.join(HL, "results", f"{tag}_base.jsonl"))
    tk = TASKER.get(tag, task_of)
    out = {}
    for fld in ("fc", "fit", "v5"):
        per = collections.defaultdict(list)
        for k, r in rows.items():
            v = r["cfg"]["full"][str(r["m"] - 1)][fld]
            if v is not None:
                per[tk(k)].append(float(v))
        c = sum(sum(v) for v in per.values()); a = sum(len(v) for v in per.values())
        bal = np.mean([np.mean(v) for v in per.values()])
        out[fld] = dict(pair=c / a, balanced=float(bal), clusters=len(per), c=c, a=a)
        print(f"{tag} {fld}: pair-weighted {c:.0f}/{a} = {100*c/a:.1f}%; cluster-balanced {100*bal:.1f}% over {len(per)} clusters")
    J["sens_" + tag] = out
    if tag == "oned":
        top3 = {"1d_pcopy_1c", "1d_pcopy_mc", "1d_recolor_cnt"}
        for fld in ("fc", "fit", "v5"):
            c = a = 0
            for k, r in rows.items():
                if k.split("/")[0] in top3:
                    continue
                v = r["cfg"]["full"][str(r["m"] - 1)][fld]
                if v is not None:
                    c += float(v); a += 1
            print(f"  1D-ARC without the three dominant types, {fld}: {c:.0f}/{a} = {100*c/max(a,1):.1f}%")
            J[f"oned_wo3_{fld}"] = (c, a)
    if tag == "concept":
        for lab, sel in (("n=2", lambda n: n == 2), ("n>=3", lambda n: n >= 3)):
            c = a = 0
            for k, r in rows.items():
                if sel(r["m"] - 1):
                    v = r["cfg"]["full"][str(r["m"] - 1)]["fc"]
                    if v is not None:
                        c += float(v); a += 1
            print(f"  ConceptARC FA-LOO {lab}: {c:.0f}/{a}")
            J["concept_" + lab] = (c, a)

print("\n== 5. Top answer that fits, and four buckets")
dev = {k: r for k, r in load_rows(os.path.join(HL, "results/dev_base.jsonl")).items() if r["split"] in ("agi1-eval", "agi2-eval")}
c = sum(r["cfg"]["full"]["top_ok"] for r in dev.values() if r["cfg"]["full"]["top_ok"] is not None); a = sum(r["cfg"]["full"]["top_ok"] is not None for r in dev.values())
print(f"public eval top answer {c:.1f}/{a} = {100*c/a:.1f}%")
J["top_eval"] = (float(c), int(a))
for tag in SETS:
    rows = load_rows(os.path.join(HL, "results", f"{tag}_base.jsonl"))
    c = a = 0; bk = collections.defaultdict(lambda: [0.0, 0])
    for r in rows.values():
        o = r["cfg"]["full"][str(r["m"] - 1)]
        if o["top_ok"] is not None:
            c += float(o["top_ok"]); a += 1
            e = o["top_ev"]; b = ">=.99" if e >= .99 else "[.5,.99)" if e >= .5 else "(0,.5)" if e > 0 else "0"
            bk[b][0] += float(o["top_ok"]); bk[b][1] += 1
    print(f"{tag} top answer {c:.0f}/{a} = {100*c/a:.1f}%; buckets", {k: f"{v[0]:.0f}/{v[1]}" for k, v in bk.items()})
    J["top_" + tag] = (float(c), int(a))

print("\n== 6. pass@2, 8 views minus 1")
for tag in SETS:
    rows = load_rows(os.path.join(HL, "results", f"{tag}_base.jsonl"))
    P8 = load_rows(os.path.join(HL, "results", f"{tag}_p8.jsonl"))
    merged = {k: dict(m=rows[k]["m"], cfg=dict(rows[k]["cfg"], **P8[k]["cfg"])) for k in rows if k in P8}
    e = Data(merged, tasker=TASKER.get(tag, task_of))
    for role in ("real", "demo"):
        x = count_diff(e, e.vec("p8", f("p2"), role)[0], e.vec("full", f("p2"), role)[0])
        print(f"{tag} {role}: {x['y']:.0f} -> {x['x']:.0f}: {x['diff']:+.0f} [{x['ci'][0]:+.0f}, {x['ci'][1]:+.0f}] {x['tasks_x_more']}:{x['tasks_y_more']} separates={x['separates']}")
        J[f"p2_8_{tag}_{role}"] = x

print("\n== 7. Vetoes: top evidence >= .99 but the 2:1 rule declines, real role, from candidates with frozen vote code")
from rules import build
from arcmonty import vote
tot_cnt = collections.Counter(); veto_w = veto_a = kept_w = kept_a = 0
for tag in SETS:
    rows = load_rows(os.path.join(HL, "results", f"{tag}_base.jsonl"))
    want = {k for k, r in rows.items() if (lambda o: o["top_ev"] is not None and o["top_ev"] >= .99 and o["v5"] is None)(r["cfg"]["full"][str(r["m"] - 1)])}
    for r in rows.values():
        o = r["cfg"]["full"][str(r["m"] - 1)]
        if o["top_ev"] is not None and o["top_ev"] >= .99:
            if o["v5"] is None:
                veto_a += 1; veto_w += 1 - float(o["top_ok"])
            else:
                kept_a += 1; kept_w += 1 - float(o["top_ok"])
    cnt = collections.Counter(); det = []
    for l in open(os.path.join(HL, "cache", f"{tag}_p0.jsonl")):
        r = json.loads(l)
        if r["task"] not in want:
            continue
        r["_np"] = [np.array(g, dtype=np.int8) for g in r["grids"]]
        a = r["m"] - 1
        C = build([r], f"F{a}", views={0})
        strong = [p for p in vote.pool(C) if p["evidence"] >= vote.CONFIDENT]
        mods = [sorted({v.split("@")[0] for v in p["voters"]}) for p in strong]
        kind = "across modules" if len({x for s in mods for x in s}) > 1 else "within one module"
        cnt[kind] += 1; det.append((r["task"], mods))
    print(tag, dict(cnt), det)
    tot_cnt.update(cnt)
print("total", dict(tot_cnt), "vetoed: wrong", veto_w, "of", veto_a, "| kept: wrong", kept_w, "of", kept_a)
tab = [[veto_w, veto_a - veto_w], [kept_w, kept_a - kept_w]]
print("Fisher p", st.fisher_exact(np.round(tab))[1])
J["veto"] = dict(kinds=dict(tot_cnt), veto_wrong=veto_w, veto=veto_a, kept_wrong=kept_w, kept=kept_a)
json.dump(J, open(os.path.join(ROOT, "research/paper/v8_notes/revise_monty.json"), "w"), indent=1, default=float)
