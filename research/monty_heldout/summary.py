"""monty-heldout: paper-ready tables across datasets, written to results/summary_tables.md and research/monty_heldout.json.
usage: python summary.py"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hl_common import HERE, MODULES, ROOT  # noqa: E402
import numpy as np  # noqa: E402
from scipy import stats as st  # noqa: E402

RES = os.path.join(HERE, "results")
TAGS = [("concept", "ConceptARC"), ("mini", "Mini-ARC"), ("oned", "1D-ARC"), ("minimal", "MinimalTasks")]
A = {t: json.load(open(os.path.join(RES, f"{t}_analysis.json"))) for t, _ in TAGS}
X = {t: json.load(open(os.path.join(RES, f"{t}_extras.json"))) for t, _ in TAGS if os.path.exists(os.path.join(RES, f"{t}_extras.json"))}
L = []


def w(s=""):
    L.append(s)


def fp(p, ci=True):
    if not p or not p["answered"]:
        return "0/0"
    c = p["correct"]
    s = f"{c:.0f}/{p['answered']} = {100 * p['precision']:.1f}%"
    if ci and p["ci"][0] is not None:
        s += f" [{100 * p['ci'][0]:.1f}, {100 * p['ci'][1]:.1f}]"
    return s


def sh(p):
    return "0/0" if not p or not p["answered"] else f"{p['correct']:.0f}/{p['answered']}"


def fd(x):
    if x.get("diff") is None or x["ci"][0] is None:
        return "n/a"
    return f"{100 * x['diff']:+.1f} [{100 * x['ci'][0]:+.1f}, {100 * x['ci'][1]:+.1f}]" + ("" if x["separates"] else " ns")


def fc(x, tasks=True):
    s = f"{x['diff']:+.0f} [{x['ci'][0]:+.0f}, {x['ci'][1]:+.0f}]"
    if tasks:
        s += f"; {x['tasks_x_more']}:{x['tasks_y_more']}"
    return s + ("" if x["separates"] else " ns")


# dev demo roles, from the paper-judge's rotation on all 1,147 tasks (same logic, cluster bootstrap here)
rot = [json.loads(l) for l in open(os.path.join(ROOT, "research", "paper", "review_scratch", "rotate_distinct.jsonl"))]
c, a = np.zeros(len(rot)), np.zeros(len(rot))
for i, r in enumerate(rot):
    m, H, F, Fu = r["m"], r["truth"], r["folds"], r["full"]
    for role in range(m - 1):
        preds, ok = set(), True
        for b in range(m):
            if b == role:
                continue
            p = F[f"{role},{b}"]
            if p is None:
                ok = False
                preds = None
                break
            if p[0] != H[b]:
                ok = False
            preds.add(p[1])
        if ok and preds is not None and len(preds) == 1 and Fu[str(role)] == next(iter(preds)):
            a[i] += 1
            c[i] += next(iter(preds)) == H[role]
rng = np.random.default_rng(0)
W = rng.multinomial(len(rot), np.full(len(rot), 1 / len(rot)), size=10000)
bt = (W @ c) / (W @ a)
dev_demo = dict(correct=float(c.sum()), answered=int(a.sum()), precision=float(c.sum() / a.sum()), ci=(float(np.percentile(bt, 2.5)), float(np.percentile(bt, 97.5))))

# ------------------------------------------------------------------
w("### Table 1. Acceptance rules, real test role (correct/answered = precision [95% CI]; coverage in the last rows)\n")
w("| Rule | Development (1,147) | ConceptARC | Mini-ARC | 1D-ARC | MinimalTasks |")
w("|---|---|---|---|---|---|")
for rn, r in (("FA-LOO + (c)", "fc"), ("(a) only", "a"), ("v5 heuristic", "v5"), ("Fit to demos only", "fit")):
    w(f"| {rn} | {fp(A['concept']['rules'][r]['dev'])} | " + " | ".join(fp(A[t]["rules"][r]["real"]) for t, _ in TAGS) + " |")
for rn, r in (("Coverage, FA-LOO + (c)", "fc"), ("Coverage, v5", "v5")):
    w(f"| {rn} | {100 * A['concept']['rules'][r]['dev']['coverage']:.1f}% | " + " | ".join(f"{100 * A[t]['rules'][r]['real']['coverage']:.1f}%" for t, _ in TAGS) + " |")
w("| pass@2 | 138/1,147 = 12.0% | " + " | ".join(f"{A[t]['pass2']['total']:.0f}/{sum(1 for _ in open(os.path.join(RES, t + '_base.jsonl')))} = {100 * A[t]['pass2']['total'] / sum(1 for _ in open(os.path.join(RES, t + '_base.jsonl'))):.1f}%" for t, _ in TAGS) + " |")
w("| Items; clusters | 1,147; 1,147 tasks | 480; 160 tasks | 149; 149 tasks | 901; 18 types | 48; 16 tasks |")
GAP = json.load(open(os.path.join(RES, "dev_gap.json")))
for rn, r in (("Dev minus this set, FA-LOO + (c), pts", "fc"), ("Dev minus this set, v5, pts", "v5"), ("Dev minus this set, fit-only, pts", "fit")):
    w(f"| {rn} | | " + " | ".join(fd(GAP[t][r]) if t in GAP else "n/a" for t, _ in TAGS) + " |")
def joint(t):
    rows = [json.loads(l) for l in open(os.path.join(RES, t + "_base.jsonl"))]
    wrong = sum(1 for r in rows if (lambda o: o["fc"] is False)(r["cfg"]["full"][str(r["m"] - 1)]))
    return wrong, len(rows), float(np.mean([1 / r["m"] for r in rows]))
J_ = {t: joint(t) for t, _ in TAGS}
dvp = A["concept"]["rules"]["fc"]["dev"]
w(f"| Joint P(answer and wrong), FA-LOO + (c) | {100 * dvp['wrong'] / 1147:.2f}% | " + " | ".join(f"{100 * J_[t][0] / J_[t][1]:.2f}% ({J_[t][0]}/{J_[t][1]})" for t, _ in TAGS) + " |")
w("| Worst case, mean 1/(n+1) | 24.7% | " + " | ".join(f"{100 * J_[t][2]:.1f}%" for t, _ in TAGS) + " |")
w("| Tasks answered / with a wrong answer, FA-LOO + (c) | " + f"{dvp['tasks_answered']} / {dvp['tasks_wrong']} | " + " | ".join(f"{A[t]['rules']['fc']['real']['tasks_answered']} / {A[t]['rules']['fc']['real']['tasks_wrong']}" for t, _ in TAGS) + " |")
w("| Tasks answered / with a wrong answer, v5 | " + f"{A['concept']['rules']['v5']['dev']['tasks_answered']} / {A['concept']['rules']['v5']['dev']['tasks_wrong']} | " + " | ".join(f"{A[t]['rules']['v5']['real']['tasks_answered']} / {A[t]['rules']['v5']['real']['tasks_wrong']}" for t, _ in TAGS) + " |")

w("\n### Table 2. The same rules, demo-as-test roles\n")
w("| Rule | Development | ConceptARC | Mini-ARC | 1D-ARC | MinimalTasks |")
w("|---|---|---|---|---|---|")
for rn, r in (("FA-LOO + (c)", "fc"), ("(a) only", "a"), ("v5 heuristic", "v5"), ("Fit to demos only", "fit")):
    d0 = fp(dev_demo) if r == "fc" else "not run"
    w(f"| {rn} | {d0} | " + " | ".join(fp(A[t]["rules"][r]["demo"]) for t, _ in TAGS) + " |")
w("| FA-LOO + (c), demo roles minus real role | " + f"{100 * (dev_demo['precision'] - A['concept']['rules']['fc']['dev']['precision']):+.1f} (from the two rows; judge's rotation) | " + " | ".join(fd(A[t]["T2c"]["fc"]) for t, _ in TAGS) + " |")

w("\n### Table 3. What held-out prediction adds (percentage points [95% CI]; `ns` = the CI includes 0)\n")
w("| Comparison | Development | ConceptARC | Mini-ARC | 1D-ARC | MinimalTasks |")
w("|---|---|---|---|---|---|")
for rn, kk in (("v5 minus fit-only", "v5-fit"), ("FA-LOO + (c) minus fit-only", "fc-fit"), ("(a) only minus fit-only", "a-fit"), ("FA-LOO + (c) minus v5", "fc-v5"), ("FA-LOO + (c) minus (a) only", "fc-a")):
    w(f"| {rn} | {fd(A['concept']['T2b'][kk]['dev'])} | " + " | ".join(fd(A[t]["T2b"][kk]["real"]) for t, _ in TAGS) + " |")
w(f"| Top answer: evidence >= 0.99 minus below | {fd(A['concept']['T2a']['dev']['hi_lo'])} | " + " | ".join(fd(A[t]["T2a"]["real"]["hi_lo"]) for t, _ in TAGS) + " |")
au = lambda x: "n/a" if x["auroc"] is None else f"{x['auroc']:.3f} [{x['ci'][0]:.3f}, {x['ci'][1]:.3f}]"
w(f"| AUROC of evidence vs correct | {au(A['concept']['T2a']['dev']['auroc'])} | " + " | ".join(au(A[t]["T2a"]["real"]["auroc"]) for t, _ in TAGS) + " |")

w("\n### Table 4. Evidence buckets, top answer (correct/top answers)\n")
w("| Column, role | >= 0.99 | [0.5, 0.99) | (0, 0.5) | 0 |")
w("|---|---|---|---|---|")
B = ("1.0", "[0.5,1)", "(0,0.5)", "0")
w("| Development, full system | " + " | ".join(fp(A["concept"]["buckets"]["full system, dev"][b], False) for b in B) + " |")
for t, n in TAGS[:3]:
    for rl in ("real", "demo"):
        w(f"| {n}, full system, {rl} | " + " | ".join(fp(A[t]["buckets"][f"full system, {rl}"][b], False) for b in B) + " |")
for m in MODULES:
    r = A["concept"]["buckets"][f"{m}, real"]
    if any(r[b]["answered"] for b in B):
        w(f"| ConceptARC, {m}, real | " + " | ".join(sh(r[b]) for b in B) + " |")
for m in ("behavior", "pattern", "dynamics", "periodic", "field"):
    r = A["mini"]["buckets"][f"{m}, real"]
    if any(r[b]["answered"] for b in B):
        w(f"| Mini-ARC, {m}, real | " + " | ".join(sh(r[b]) for b in B) + " |")
for m in ("behavior", "dynamics", "pattern"):
    r = A["oned"]["buckets"][f"{m}, real"]
    if any(r[b]["answered"] for b in B):
        w(f"| 1D-ARC, {m}, real | " + " | ".join(sh(r[b]) for b in B) + " |")

w("\n### Table 5. Frames, behaviour module alone (pass@2 items; top answer at evidence >= 0.99)\n")
w("| Arm | Development | ConceptARC | Mini-ARC | 1D-ARC |")
w("|---|---|---|---|---|")
F = lambda t, lev, arm: A[t]["frames"][lev][arm]
for arm, lab in (("canon", "canon (D8 object frame)"), ("abs", "abs (object-anchored, grid-aligned)"), ("both", "both (shipped)"), ("global", "global (grid coordinates, no object anchor)")):
    d = F("concept", "behaviour alone", arm)["dev"]
    w(f"| {lab} | {d['pass2']:.0f}; {sh(d['loo1'])} | " + " | ".join(f"{F(t, 'behaviour alone', arm)['pass2']:.0f}; {sh(F(t, 'behaviour alone', arm)['loo1'])}" for t, _ in TAGS[:3]) + " |")
w("\n### Table 6. Frames, full system (pass@2 items; v5; FA-LOO + (c), real role)\n")
w("| Arm | Development | ConceptARC | Mini-ARC | 1D-ARC |")
w("|---|---|---|---|---|")
for arm, lab in (("canon", "canon"), ("abs", "abs"), ("both", "both (shipped)"), ("global", "global"), ("no behaviour", "behaviour removed")):
    d = F("concept", "system", arm)["dev"]
    w(f"| {lab} | {d['pass2']:.0f}; {sh(d['v5'])}; {sh(d['fc'])} | " + " | ".join(f"{F(t, 'system', arm)['pass2']:.0f}; {sh(F(t, 'system', arm)['v5'])}; {sh(F(t, 'system', arm)['fc'])}" for t, _ in TAGS[:3]) + " |")
w("\n### Table 7. Frames, paired differences in pass@2 items (difference [95% CI]; discordant clusters first:second; `ns` = the CI includes 0)\n")
w("| Comparison | Development | ConceptARC real | ConceptARC demo | Mini-ARC real | Mini-ARC demo | 1D-ARC real |")
w("|---|---|---|---|---|---|---|")
for lev in ("behaviour alone", "system"):
    for x, y in (("canon", "abs"), ("both", "canon"), ("canon", "global"), ("abs", "global")):
        k = f"{lev}:{x}-{y}"
        c = A["concept"]["frames"]["paired"][k]
        m = A["mini"]["frames"]["paired"][k]
        o = A["oned"]["frames"]["paired"][k]
        w(f"| {lev}: {x} minus {y} | {fc(c['dev'])} | {fc(c['real'])} | {fc(c['demo'])} | {fc(m['real'])} | {fc(m['demo'])} | {fc(o['real'])} |")
pool = {}
for x, y in (("canon", "abs"), ("canon", "global")):
    k = f"behaviour alone:{x}-{y}"
    a_, b_ = 0, 0
    for t in ("concept", "mini", "oned"):
        r = A[t]["frames"]["paired"][k]["real"]
        a_ += r["tasks_x_more"]
        b_ += r["tasks_y_more"]
    pool[f"{x}-{y}"] = dict(x=a_, y=b_, sign_p=float(st.binomtest(a_, a_ + b_, 0.5).pvalue))
w(f"\nDescriptive only, discordant clusters summed over the three unseen sets, real role, behaviour alone: canon vs abs {pool['canon-abs']['x']}:{pool['canon-abs']['y']} (sign p = {pool['canon-abs']['sign_p']:.4f}); canon vs global {pool['canon-global']['x']}:{pool['canon-global']['y']} (sign p = {pool['canon-global']['sign_p']:.2g}).")

w("\n### Table 8. Modules (alone / lost when removed / unique, pass@2 items, real role)\n")
w("| Module | Development | ConceptARC | Mini-ARC | 1D-ARC |")
w("|---|---|---|---|---|")
for m in MODULES:
    d = A["concept"]["modules"]["dev"][m]
    w(f"| {m} | {d['alone']} / {d['lost']} / {d['unique']} | " + " | ".join("{alone} / {lost} / {unique}".format(**A[t]["modules"]["real"][m]) for t, _ in TAGS[:3]) + " |")
sm = lambda s: f"{s['exactly_one']}/{s['union_alone']} = {100 * s['exactly_one'] / max(1, s['union_alone']):.1f}%"
w(f"| Solved by exactly one module | {sm(A['concept']['modules']['dev_summary'])} | " + " | ".join(sm(A[t]["modules"]["real_summary"]) for t, _ in TAGS[:3]) + " |")
w(f"| Same, demo roles | not run | " + " | ".join(sm(A[t]["modules"]["demo_summary"]) for t, _ in TAGS[:3]) + " |")
w(f"| Lost by the vote / gained by the vote | {len(A['concept']['modules']['dev_summary']['lost_by_vote'])} / {len(A['concept']['modules']['dev_summary']['gained_by_vote'])} | " + " | ".join(f"{len(A[t]['modules']['real_summary']['lost_by_vote'])} / {len(A[t]['modules']['real_summary']['gained_by_vote'])}" for t, _ in TAGS[:3]) + " |")

w("\n### Table 9. Module alone: top answer at evidence >= 0.99, real role (development: distinct tasks)\n")
w("| Module | Development | ConceptARC | Mini-ARC | 1D-ARC |")
w("|---|---|---|---|---|")
for m in MODULES:
    w(f"| {m} | {sh(A['concept']['modules']['dev'][m]['loo1'])} | " + " | ".join(sh(A[t]["modules"]["real"][m]["loo1"]) for t, _ in TAGS[:3]) + " |")

w("\n### Table 10. Is it a vote? Top answers backed by two or more modules, and a no-vote baseline (real role)\n")
w("| Quantity | Development | ConceptARC | Mini-ARC | 1D-ARC |")
w("|---|---|---|---|---|")
V = lambda t: A[t]["T3b"]["real"]
D = A["concept"]["T3b"]["dev"]
w(f"| Top answers from 2+ modules: correct/n (clusters) | {sh(D['many'])} ({D['many']['tasks_answered']}) | " + " | ".join(f"{sh(V(t)['many'])} ({V(t)['many']['tasks_answered']})" for t, _ in TAGS[:3]) + " |")
w(f"| Top answers from 1 module | {sh(D['one'])} | " + " | ".join(sh(V(t)["one"]) for t, _ in TAGS[:3]) + " |")
w(f"| Pool minus no-vote, pass@2 items | {fc(D['pool_vs_novote_p2'])} | " + " | ".join(fc(V(t)["pool_vs_novote_p2"]) for t, _ in TAGS[:3]) + " |")
w(f"| Top answer at evidence >= 0.99, pool | {fp(D['pool_hi'], False)} | " + " | ".join(fp(V(t)["pool_hi"], False) for t, _ in TAGS[:3]) + " |")
w(f"| Top answer at evidence >= 0.99, no-vote | {fp(D['novote_hi'], False)} | " + " | ".join(fp(V(t)["novote_hi"], False) for t, _ in TAGS[:3]) + " |")
w(f"| Pool minus no-vote, precision | {fd(D['pool_vs_novote_hi'])} | " + " | ".join(fd(V(t)["pool_vs_novote_hi"]) for t, _ in TAGS[:3]) + " |")

w("\n### Table 11. Eight D8 views vs one view\n")
w("| Population | Rule | 1 view | 8 views | Wrong, 8 minus 1 |")
w("|---|---|---|---|---|")
for t, n in TAGS[:3]:
    if "p8" not in A[t]:
        continue
    for rl, a1, a8, wd in (("real", "v1", "v8", "wrong_diff"), ("demo", "v1_demo", "v8_demo", "wrong_diff_demo")):
        for rn, r in (("v5 rule", "v5"), ("P4", "p4"), ("FA-LOO (v5 vote) + (c)", "fc"), ("FA-LOO (P4 vote) + (c)", "fc4")):
            p = A[t]["p8"][r]
            w(f"| {n}, {rl} | {rn} | {fp(p[a1])} | {fp(p[a8])} | {fc(p[wd])} |")
w("| Development, AGI-1 train only (`monty_faloo.md`) | v5 rule | 58/59 | 62/66 | 1 -> 4 |")
w("| same | P4 | 59/59 | 60/61 | 0 -> 1 |")
w("| same | FA-LOO (v5 vote) + (c) | 59/59 | 58/58 | 0 -> 0 |")
w("| same | FA-LOO (P4 vote) + (c) | 60/61 | 60/61 | 1 -> 1 |")
for t, n in TAGS[:3]:
    if "p8" in A[t]:
        w(f"\n{n}, pass@2 items, 8 views minus 1: {fc(A[t]['p8']['pass2'])}. 8-view v5 minus 8-view P4, precision: real {fd(A[t]['p8']['8-view v5 minus 8-view P4']['real'])}; demo {fd(A[t]['p8']['8-view v5 minus 8-view P4']['demo'])}.")

DG = json.load(open(os.path.join(RES, "disagree.json")))
w("\n### Table 12. Where v5 and FA-LOO + (c) disagree about answering (real role; post hoc, descriptive)\n")
w("| Dataset | Both answer: right/n | v5 only: right/n | FA-LOO + (c) only: right/n |")
w("|---|---|---|---|")
w("| Development (1,147) | 91/92 | 5/6 | 10/10 |")
for t, n in TAGS[:3]:
    x = DG[t]
    w(f"| {n} | {x['bc']:.0f}/{x['ba']:.0f} | {x['vc']:.0f}/{x['va']:.0f} | {x['fc']:.0f}/{x['fa']:.0f} |")
x = DG["pooled"]
w(f"| Three unseen sets pooled (stratified cluster bootstrap) | {x['bc']:.0f}/{x['ba']:.0f} | {x['vc']:.0f}/{x['va']:.0f} [{100 * x['v5_only'][0]:.0f}, {100 * x['v5_only'][1]:.0f}] | {x['fc']:.0f}/{x['fa']:.0f} [{100 * x['fa_only'][0]:.0f}, {100 * x['fa_only'][1]:.0f}]; v5 only minus FA-LOO only {100 * x['diff']:+.1f} [{100 * x['diff_ci'][0]:+.1f}, {100 * x['diff_ci'][1]:+.1f}] |")

w("\n### Table 13. ConceptARC by concept group (real role, 30 test pairs each)\n")
G = A["concept"]["concept_groups"]
GF = A["concept"]["groups_fc"]
w("| Group | pass@2 [CI] | Tasks /10 | Any candidate | Solving modules (alone) | v5 | FA-LOO + (c) real | FA-LOO + (c) demo | Kaggle 1st | GPT-4 T0 | Humans |")
w("|---|---|---|---|---|---|---|---|---|---|---|")
for g, v in G.items():
    mods = ", ".join(f"{m} {k}" for m, k in sorted(v["modules"].items(), key=lambda z: -z[1])) or "-"
    w(f"| {g} | {v['p2']:.0f} [{v['ci'][0]:.0f}, {v['ci'][1]:.0f}] | {v['tasks']} | {v['any_candidate']} | {mods} | {sh(GF[g]['v5'])} | {sh(GF[g]['real'])} | {sh(GF[g]['demo'])} | {v['kaggle1']} | {v['gpt4']} | {100 * v['human']:.0f}% |")
T = A["concept"]["concept_groups_total"]
w(f"| **All** | {T['p2']:.0f}/480 | 26 | {T['cand']:.0f} | | 42/49 | 35/44 | 100/111 | {T['k1']:.0f} | {T['g']:.0f} | {100 * T['human']:.0f}% |")
w("\nGap (FA-LOO + (c), demo minus real) with one group left out: " + "; ".join(f"{g} {fd(GF[g]['gap_without'])}" for g in sorted(GF, key=lambda z: GF[z]['gap_without']['diff'])) + ".")

open(os.path.join(RES, "summary_tables.md"), "w").write("\n".join(L) + "\n")
out = dict(generated="monty-heldout, research/monty_heldout/summary.py", analyses=A, extras=X, dev_demo_fc=dev_demo, pooled_discordant=pool, disagree=DG, dev_gap=GAP, joint={t: dict(wrong=J_[t][0], items=J_[t][1], mean_bound=J_[t][2]) for t, _ in TAGS},
           verify=json.load(open(os.path.join(RES, "verify.json"))))
json.dump(out, open(os.path.join(ROOT, "research", "monty_heldout.json"), "w"), indent=1, default=float)
print("\n".join(L))
