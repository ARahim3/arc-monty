"""WS4 / FA-LOO: audit of each v5 module's leave-one-out (frozen code; module internals called, nothing edited).

Per-structure modules (behavior, pattern, field): the structure is filtered on all n demos, then LOO re-learns only
the parameters (table / library) on n-1 demos. For every candidate with LOO = 1.0 we re-learn each fold model and ask
whether condition (b) holds automatically: does every fold model predict the test exactly as the full model?
Learner-level modules (periodic, dynamics, composition, association): LOO scores the learner "first hypothesis in
a fixed order that fits the training demos", re-run per fold over a hypothesis list generated from ALL n demos; the
score is then given to every full-fit hypothesis. We measure (i) how many distinct full-fit predictions share an
LOO = 1.0 score, (ii) whether the hypothesis list generated from the fold's n-1 demos differs from the full list
(selection leakage), and (iii) whether the fold learners agree on the test (b).
usage: nice -n 10 python research/monty_eval/module_loo_audit.py   -> results/module_loo_audit.json
"""
import collections
import itertools
import json
import multiprocessing as mp
import os
import sys

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_v, "1")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402

from common import ROOT  # noqa: E402
from make_tables import distinct_items  # noqa: E402
from arcmonty import association, behavior, composition, dynamics, field, pattern, periodic  # noqa: E402


def eq(a, b):
    return a is not None and b is not None and a.shape == b.shape and np.array_equal(a, b)


def audit_behavior(task):
    pairs, tests = task["train"], task["test"]
    if not all(i.shape == o.shape for i, o in pairs) or all(np.array_equal(i, o) for i, o in pairs):
        return []
    out = []
    for seg, key, frame, R, own in itertools.product(behavior.SEGS, behavior.KEYS, behavior.FRAMES, behavior.RADII,
                                                     behavior.OWNERSHIP):
        if own == "union" and R > 2:
            continue
        model = behavior.learn(pairs, seg, key, frame, R, own)
        if model is None or any(not np.array_equal(behavior.predict(model, i, seg, key, frame, R, own)[0], o) for i, o in pairs):
            continue
        full = [behavior.predict(model, t, seg, key, frame, R, own) for t in tests]
        if any(p is None or u > 0 for p, u in full):
            continue
        loo, agree, unseen_test = 0, True, False
        for j in range(len(pairs)):
            m = behavior.learn(pairs[:j] + pairs[j + 1:], seg, key, frame, R, own)
            if m is None:
                agree = False
                continue
            p, u = behavior.predict(m, pairs[j][0], seg, key, frame, R, own)
            loo += p is not None and u == 0 and np.array_equal(p, pairs[j][1])
            for t, (fp, _) in zip(tests, full):
                q, uq = behavior.predict(m, t, seg, key, frame, R, own)
                unseen_test |= uq > 0
                agree &= uq == 0 and eq(q, fp)
        if loo == len(pairs):
            out.append(dict(b_auto=bool(agree), unseen_test=bool(unseen_test)))
    return out


def audit_pattern(task):
    pairs, tests = task["train"], task["test"]
    if not all(i.shape == o.shape for i, o in pairs) or all(np.array_equal(i, o) for i, o in pairs):
        return []
    out = []
    for ctx in pattern.CTX:
        lib = pattern.learn(pairs, ctx)
        if lib is None or any((p := pattern.predict(lib, i)) is None or not np.array_equal(p, o) for i, o in pairs):
            continue
        full = [pattern.predict(lib, t) for t in tests]
        if any(p is None for p in full) or all(np.array_equal(p, t) for p, t in zip(full, tests)):
            continue
        loo, agree = 0, True
        for j in range(len(pairs)):
            sub = pattern.learn(pairs[:j] + pairs[j + 1:], ctx)
            if sub is None:
                agree = False
                continue
            p = pattern.predict(sub, pairs[j][0])
            loo += p is not None and np.array_equal(p, pairs[j][1])
            agree &= all(eq(pattern.predict(sub, t), fp) for t, fp in zip(tests, full))
        if loo == len(pairs):
            out.append(dict(b_auto=bool(agree)))
    return out


def audit_field(task):
    pairs, tests = task["train"], task["test"]
    if not all(i.shape == o.shape for i, o in pairs) or all(np.array_equal(i, o) for i, o in pairs):
        return []
    out = []
    for p in field._hypotheses(pairs):
        if not all((t := field._learn([pr], p)) is not None and eq(field._predict(t, pr[0], p), pr[1]) for pr in pairs):
            continue
        table = field._learn(pairs, p)
        if table is None:
            continue
        full = [field._predict(table, t, p) for t in tests]
        if any(q is None for q in full):
            continue
        loo, agree = 0, True
        for j in range(len(pairs)):
            t = field._learn(pairs[:j] + pairs[j + 1:], p)
            q = None if t is None else field._predict(t, pairs[j][0], p)
            loo += q is not None and np.array_equal(q, pairs[j][1])
            agree &= t is not None and all(eq(field._predict(t, x, p), fp) for x, fp in zip(tests, full))
        if loo == len(pairs):
            out.append(dict(b_auto=bool(agree)))
        if len(out) >= 4:
            break
    return out


GENS = {"dynamics": (dynamics, ("_fill_hypotheses", "_connect_hypotheses", "_move_hypotheses", "_ray_hypotheses"), 3000),
        "composition": (composition, ("_tile_hypotheses", "_corner_hypotheses", "_down_hypotheses", "_panels_hypotheses",
                                      "_select_hypotheses"), 4000),
        "association": (association, ("_template_hypotheses", "_legend_hypotheses"), 500),
        "periodic": (periodic, ("_hypotheses",), 10 ** 9)}


def hyp_list(mod, gens, cap, pairs):
    hyps = []
    for g in gens:
        for p in getattr(mod, g)(pairs) or []:
            if len(hyps) >= cap:
                break
            hyps.append(p)
    return hyps


def fits(mod, name, p, pairs):
    out = []
    for i, o in pairs:
        q = mod._apply(i, p)
        out.append(q is not None and (q.shape == o.shape if name == "composition" else True) and eq(q, o))
    return out


def audit_learner(task, name):
    mod, gens, cap = GENS[name]
    pairs, tests = task["train"], task["test"]
    if name != "composition" and (not all(i.shape == o.shape for i, o in pairs) or all(np.array_equal(i, o) for i, o in pairs)):
        return None
    hyps = hyp_list(mod, gens, cap, pairs)
    if not hyps:
        return None
    F = np.array([fits(mod, name, p, pairs) for p in hyps], dtype=bool)
    n = len(pairs)
    loo = 0
    for j in range(n):
        rest = np.delete(F, j, axis=1).all(axis=1) if n > 1 else np.ones(len(hyps), dtype=bool)
        first = np.flatnonzero(rest)
        loo += int(len(first) > 0 and bool(F[first[0], j]))
    if loo != n:
        return None
    full_fit = [h for h in np.flatnonzero(F.all(axis=1))
                if all(mod._apply(t, hyps[h]) is not None for t in tests)]
    if not full_fit:
        return None
    preds = [tuple(mod._apply(t, hyps[h]).tobytes() + bytes(mod._apply(t, hyps[h]).shape) for t in tests) for h in full_fit[:8]]
    first_full = [mod._apply(t, hyps[full_fit[0]]) for t in tests]
    # true re-induction: hypothesis list generated from the fold's own n-1 demos
    leak, b_true, b_monty = False, True, True
    for j in range(n):
        fold = pairs[:j] + pairs[j + 1:]
        hj = hyp_list(mod, gens, cap, fold)
        leak |= [str(h) for h in hj] != [str(h) for h in hyps]
        firstj = next((p for p in hj if all(fits(mod, name, p, fold))), None)
        b_true &= firstj is not None and all(eq(mod._apply(t, firstj), f) for t, f in zip(tests, first_full))
        rest = np.delete(F, j, axis=1).all(axis=1) if n > 1 else np.ones(len(hyps), dtype=bool)
        fm = np.flatnonzero(rest)
        b_monty &= len(fm) > 0 and all(eq(mod._apply(t, hyps[fm[0]]), f) for t, f in zip(tests, first_full))
    return dict(n_full_fit=len(full_fit[:8]), n_distinct=len(set(preds)), leak=bool(leak), b_true=bool(b_true),
                b_monty=bool(b_monty))


def one(item):
    split, key, _row, task = item
    out = dict(task=key, split=split)
    for name, fn in (("behavior", audit_behavior), ("pattern", audit_pattern), ("field", audit_field)):
        try:
            out[name] = fn(task)
        except Exception as e:
            out[name] = repr(e)[:100]
    for name in GENS:
        try:
            out[name] = audit_learner(task, name)
        except Exception as e:
            out[name] = repr(e)[:100]
    return out


def main():
    items = distinct_items()
    with mp.Pool(4) as p:
        rows = p.map(one, items, chunksize=2)
    summ = {}
    for name in ("behavior", "pattern", "field"):
        c = [x for r in rows if isinstance(r[name], list) for x in r[name]]
        summ[name] = dict(loo1_candidates=len(c), b_automatic=sum(x["b_auto"] for x in c),
                          tasks=sum(1 for r in rows if isinstance(r[name], list) and r[name]))
        if name == "behavior":
            summ[name]["fold_unseen_on_test"] = sum(x["unseen_test"] for x in c)
    for name in GENS:
        c = [r[name] for r in rows if isinstance(r[name], dict)]
        summ[name] = dict(tasks_loo1=len(c), multi_distinct=sum(x["n_distinct"] > 1 for x in c),
                          mean_full_fit=round(float(np.mean([x["n_full_fit"] for x in c])), 2) if c else None,
                          hyp_list_leak=sum(x["leak"] for x in c), b_true_reinduction=sum(x["b_true"] for x in c),
                          b_monty_folds=sum(x["b_monty"] for x in c))
    errs = collections.Counter(n for r in rows for n in list(GENS) + ["behavior", "pattern", "field"] if isinstance(r[n], str))
    print(json.dumps(summ, indent=1), "errors", dict(errs))
    json.dump(dict(summary=summ, rows=rows, errors=dict(errs)),
              open(os.path.join(ROOT, "research", "monty_eval", "results", "module_loo_audit.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
