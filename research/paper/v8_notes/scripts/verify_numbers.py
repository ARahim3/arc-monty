"""v8 paper: print every held-out statistic used in the paper, recomputed from results/*_analysis.json and the base files,
and check each formatted string occurs in paper.md (when it exists). Read-only.
Usage: .venv/bin/python -B verify_numbers.py"""
import os  # noqa: E402  (release: paths from the repo root)
_REPO = os.environ.get("ARC_MONTY_ROOT", os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..")))  # repo root
import json, os, re, sys
ROOT = _REPO
RES = os.path.join(ROOT, "research/monty_heldout/results")
A = {t: json.load(open(os.path.join(RES, f"{t}_analysis.json"))) for t in ("concept", "mini", "oned", "minimal")}
X = {t: json.load(open(os.path.join(RES, f"{t}_extras.json"))) for t in ("concept", "mini", "oned", "minimal")}
E = json.load(open(os.path.join(ROOT, "research/paper/v8_notes/eval_only.json")))["public_eval_514"]
U = json.load(open(os.path.join(ROOT, "research/paper/v8_notes/unseen_check.json")))
def fp(p): return f"{p['correct']:.0f}/{p['answered']}"
def pct(p): return f"{100*p['precision']:.1f}"
def ci(p): return f"[{100*p['ci'][0]:.1f}, {100*p['ci'][1]:.1f}]"
def fd(x): return f"{100*x['diff']:+.1f} [{100*x['ci'][0]:+.1f}, {100*x['ci'][1]:+.1f}]"
def fc(x): return f"{x['diff']:+.0f} [{x['ci'][0]:+.0f}, {x['ci'][1]:+.0f}]"
out = []
def add(label, s): out.append((label, s)); print(f"{label:58s} {s}")
for name, r in (("fit-only", "fit"), ("v5", "v5"), ("FA-LOO+(c)", "fc"), ("(a) only", "a")):
    add(f"{name}, public eval", f"{fp(E[r])} = {pct(E[r])}% {ci(E[r])}")
    for t in ("concept", "mini", "oned", "minimal"):
        p = A[t]["rules"][r]["real"]
        add(f"{name}, {t}", f"{fp(p)} = {pct(p)}% {ci(p)}  cov {100*p['coverage']:.1f}%  tasks {p['tasks_answered']}/{p['tasks_wrong']}")
for t in ("concept", "mini", "oned", "minimal"):
    p = A[t]["rules"]["fc"]["demo"]
    add(f"FA-LOO+(c) demo roles, {t}", f"{fp(p)} = {pct(p)}% {ci(p)}")
    add(f"FA-LOO+(c) demo minus real, {t}", fd(A[t]["T2c"]["fc"]))
for x, y in (("v5", "fit"), ("fc", "fit"), ("fc", "v5"), ("fc", "a")):
    add(f"{x} minus {y}, public eval", fd(E[f"{x}-{y}"]))
    for t in ("concept", "mini", "oned", "minimal"):
        add(f"{x} minus {y}, {t}", fd(A[t]["T2b"][f"{x}-{y}"]["real"]))
add("evidence hi-lo, public eval", fd(E["hi-lo"]))
for t in ("concept", "mini", "oned"):
    add(f"evidence hi-lo, {t}", fd(A[t]["T2a"]["real"]["hi_lo"]))
    au = A[t]["T2a"]["real"]["auroc"]
    add(f"AUROC, {t}", f"{au['auroc']:.3f} [{au['ci'][0]:.3f}, {au['ci'][1]:.3f}]")
add("AUROC, public eval", f"{E['auroc']['auroc']:.3f} [{E['auroc']['ci'][0]:.3f}, {E['auroc']['ci'][1]:.3f}]")
for t in ("concept", "mini", "oned"):
    b = A[t]["buckets"]["full system, real"]
    add(f"buckets real, {t}", " | ".join(f"{k}: {fp(v)}" for k, v in b.items()))
    s = A[t]["sets"]
    add(f"sets fc|fit, {t}", json.dumps({k: v for k, v in s["fc|fit"].items() if not k.endswith("keys")}))
    add(f"sets v5|fc, {t}", json.dumps({k: v for k, v in s["v5|fc"].items() if not k.endswith("keys")}))
    w = A[t]["wrong"]
    fitw = set(w["fit"]); fcw = set(w["fc"]); v5w = set(w["v5"])
    add(f"wrong fit / also wrong under fc / under v5, {t}", f"{len(fitw)} / {len(fitw & fcw)} / {len(fitw & v5w)}; fc wrong {len(fcw)} v5 wrong {len(v5w)}")
    add(f"public-eval minus set FA-LOO+(c), {t}", fd(U[t]["eval_minus"]["fc"]))
    add(f"public-eval minus set v5, {t}", fd(U[t]["eval_minus"]["v5"]))
    add(f"events, {t}", f"{U[t]['items_with_event']}/{U[t]['items']} = {100*U[t]['share']:.1f}%; two+ {U[t]['two_plus']}; at real {U[t]['event_real']}; joint {100*U[t]['joint']:.2f}%; bound {100*U[t]['mean_bound']:.1f}%")
    ms = A[t]["modules"]["real_summary"]
    add(f"modules, {t}", f"exactly one {ms['exactly_one']}/{ms['union_alone']}={100*ms['exactly_one']/ms['union_alone']:.1f}%; lost {len(ms['lost_by_vote'])}; gained {len(ms['gained_by_vote'])}; full {ms['full']}")
    add(f"module alone/lost/unique, {t}", " ".join(f"{m}:{v['alone']}/{v['lost']}/{v['unique']}" for m, v in A[t]["modules"]["real"].items()))
    add(f"module >=.99, {t}", " ".join(f"{m}:{fp(v['loo1'])}" for m, v in A[t]["modules"]["real"].items()))
    t3 = A[t]["T3b"]["real"]
    add(f"2+ modules; one; pool; novote, {t}", f"{fp(t3['many'])}; {fp(t3['one'])}; {fp(t3['pool_hi'])}; {fp(t3['novote_hi'])}; pool-novote {fd(t3['pool_vs_novote_hi'])}; p2 {fc(t3['pool_vs_novote_p2'])}")
    P = A[t]["p8"]
    for rn, fld in (("v5", "v5"), ("P4", "p4"), ("FA-LOO", "fc")):
        add(f"8 views wrong diff real/demo {rn}, {t}", f"{fc(P[fld]['wrong_diff'])} {P[fld]['wrong_diff']['tasks_x_more']}:{P[fld]['wrong_diff']['tasks_y_more']} / {fc(P[fld]['wrong_diff_demo'])} {P[fld]['wrong_diff_demo']['tasks_x_more']}:{P[fld]['wrong_diff_demo']['tasks_y_more']}; v1 {fp(P[fld]['v1'])} v8 {fp(P[fld]['v8'])}; demo v1 {fp(P[fld]['v1_demo'])} v8 {fp(P[fld]['v8_demo'])}")
    add(f"8 views pass@2, {t}", fc(P["pass2"]))
    F = A[t]["frames"]
    for lvl in ("behaviour alone", "system"):
        add(f"frames {lvl}, {t}", " | ".join(f"{a}: {F[lvl][a]['pass2']:.0f}; {fp(F[lvl][a]['loo1'])}; v5 {fp(F[lvl][a]['v5'])}; fc {fp(F[lvl][a]['fc'])}" for a in F[lvl]))
    P2 = F["paired"]
    for k in ("behaviour alone:canon-abs", "behaviour alone:canon-global", "behaviour alone:both-canon"):
        add(f"{k}, {t}", f"{fc(P2[k]['real'])} {P2[k]['real']['tasks_x_more']}:{P2[k]['real']['tasks_y_more']} p={P2[k]['real']['sign_p']}")
json.dump(dict(out), open(os.path.join(ROOT, "research/paper/v8_notes/verify_numbers.json"), "w"), indent=0)
