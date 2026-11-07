"""monty-heldout: every acceptance rule, evaluated on candidate lists exactly as earlier scripts did (imports vote.py,
faloo.pool_p4, vote_ablation.pool unchanged). Works for any number of test inputs, so dev caches use the same code."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hl_common import MODULES, h  # noqa: E402
import numpy as np  # noqa: E402
from arcmonty import vote  # noqa: E402
from arcmonty.evaluate import score_task  # noqa: E402
from faloo import confident_p4, pool_p4  # noqa: E402  (research/monty_eval)
from vote_ablation import pool as vpool  # noqa: E402

CONF = vote.CONFIDENT
_ORDER = {m: j for j, m in enumerate(MODULES)}


def module_name(lm):
    """'behavior@3' -> 'behavior'; candidate lm names equal the display names except symmetry."""
    n = lm.split("@")[0]
    return "self-model" if n in ("symmetry", "self-model") else n


def build(rows, run_key, modules=None, frames=None, views=None, behavior_rows=None):
    """Candidates exactly as monty_arc.candidates returns them (perspective order, then module order, then within-module
    order). rows: cache rows (each with _np = list of arrays). frames restricts behaviour hypotheses by the frame field of
    their hyp string; behavior_rows replaces the behaviour module's candidates (global arm)."""
    out = []
    for row in rows:
        g = row["_np"]
        mods = row["runs"][run_key]
        for m in MODULES:
            if modules is not None and m not in modules:
                continue
            if m == "behavior" and behavior_rows is not None:
                continue
            for c in mods.get(m, {"cands": []})["cands"]:
                k = int(c["lm"].split("@")[1])
                if views is not None and k not in views:
                    continue
                if m == "behavior" and frames is not None and c["hyp"].split("/")[2] not in frames:
                    continue
                out.append(dict(lm=c["lm"], hyp=c["hyp"], evidence=c["ev"], preds=[g[i] for i in c["p"]], _m=m, _k=k))
    if behavior_rows is not None and (modules is None or "behavior" in modules):
        for row in behavior_rows:
            g = row["_np"]
            for c in row["runs"][run_key].get("behavior", {"cands": []})["cands"]:
                k = int(c["lm"].split("@")[1])
                if views is None or k in views:
                    out.append(dict(lm=c["lm"], hyp=c["hyp"], evidence=c["ev"], preds=[g[i] for i in c["p"]], _m="behavior", _k=k))
    out.sort(key=lambda c: (c["_k"], _ORDER[c["_m"]]))  # stable, so within-module order is kept
    return out


def same(a, b):
    return len(a) == len(b) and all(np.array_equal(x, y) for x, y in zip(a, b))


def top_of(cands, rule):
    best = vote.pool(cands) if rule == "v5" else pool_p4(cands)
    return best[0]["preds"] if best else None


def no_vote(cands):
    """Baseline without a vote: rank distinct answers by best single-hypothesis evidence; ties by candidate order. No pooling
    of evidence, no voter counts."""
    seen = []
    for c in sorted(cands, key=lambda c: -c["evidence"]):
        if not any(same(c["preds"], s["preds"]) for s in seen):
            seen.append(c)
    return seen


def full_outcome(task, C):
    """All rules that use only the full-data candidates."""
    o = {}
    att = vote.attempts_from(task, C)
    o["p2"] = score_task(task, att)
    o["p1"] = score_task(task, [a[:1] for a in att])
    o["has"] = bool(C)
    best = vote.pool(C)
    top = best[0] if best else None
    o["top_ev"] = None if top is None else round(float(top["evidence"]), 4)
    o["top_ok"] = None if top is None else score_task(task, [[g] for g in top["preds"]])
    o["top_mods"] = [] if top is None else sorted({module_name(v) for v in top["voters"]})
    o["top_voters"] = 0 if top is None else len(top["voters"])
    o["top_h"] = None if top is None else [h(g) for g in top["preds"]]
    o["n_strong"] = sum(p["evidence"] >= CONF for p in best)
    conf = vote.confident(C)
    o["v5"] = score_task(task, vote.attempts_from(task, C, CONF)) if conf else None
    o["v5t"] = o["top_ok"] if conf else None
    fit = [dict(c, evidence=1.0) for c in C]
    o["fit"] = score_task(task, vote.attempts_from(task, fit, CONF)) if vote.confident(fit) else None
    if fit and vote.confident(fit):
        o["fitt"] = score_task(task, [[g] for g in vote.pool(fit)[0]["preds"]])
    else:
        o["fitt"] = None
    # raw: no accumulation over a column's own duplicate hypotheses
    raw = vpool(C, cross_only=True)
    o["raw_ev"] = None if not raw else round(float(raw[0]["evidence"]), 4)
    o["raw_ok"] = None if not raw else score_task(task, [[g] for g in raw[0]["preds"]])
    # P4: one voter per module
    bp = pool_p4(C)
    if confident_p4(bp):
        a4 = [[] for _ in task["test"]]
        for p in bp:
            if p["evidence"] < CONF:
                break
            for a, g in zip(a4, p["preds"]):
                if len(a) < 2 and not any(np.array_equal(g, q) for q in a):
                    a.append(g)
        o["p4"] = score_task(task, a4)
        o["p4t"] = score_task(task, [[g] for g in bp[0]["preds"]])
    else:
        o["p4"] = o["p4t"] = None
    o["p4_ok_top"] = None if not bp else score_task(task, [[g] for g in bp[0]["preds"]])
    # no vote at all
    nv = no_vote(C)
    if nv:
        o["nv_ev"] = round(float(nv[0]["evidence"]), 4)
        o["nv_ok"] = score_task(task, [[g] for g in nv[0]["preds"]])
        natt = [[] for _ in task["test"]]
        for c in nv:
            for a, g in zip(natt, c["preds"]):
                if len(a) < 2 and not any(np.array_equal(g, q) for q in a):
                    a.append(g)
        o["nv_p2"] = score_task(task, natt)
    else:
        o["nv_ev"] = o["nv_ok"] = None
        o["nv_p2"] = 0.0
    return o


def faloo_role(y_full, truth, fold_tops, held):
    """One test input. fold_tops: {b: preds [at x_b, at test]}; held: {b: y_b}; y_full: full-data top answer (grid or None).
    Returns dict a, fa, fc and the first reason for abstaining, as concept_summary.py."""
    a_ok, tests, any_none = True, [], False
    for b, p in fold_tops.items():
        if p is None:
            a_ok, any_none = False, True
            continue
        if not np.array_equal(p[0], held[b]):
            a_ok = False
        tests.append(p[1])
    agree = (not any_none) and bool(tests) and all(np.array_equal(tests[0], q) for q in tests[1:])
    y = tests[0] if agree else None
    out = {}
    out["a"] = (bool(np.array_equal(y_full, truth))) if (a_ok and y_full is not None) else None
    fa = a_ok and agree
    out["fa"] = bool(np.array_equal(y, truth)) if fa else None
    c = fa and y_full is not None and np.array_equal(y_full, y)
    out["fc"] = bool(np.array_equal(y, truth)) if c else None
    out["why"] = ("fold abstains" if any_none else "(a)" if not a_ok else "(b)" if not agree else "(c)" if not c else "answer")
    return out
