"""v8 revision: why the same-token comparison differs between scripts. Ties among candidates of equal tier decide which two survive.
Compares file order, fold-index order, vote-count order, and the average over random tie-breaks, in both arms. Output ../revise_ties.txt"""
import os  # noqa: E402  (release: paths from the repo root)
_REPO = os.environ.get("ARC_MONTY_ROOT", os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..")))  # repo root
import collections, json, random
import numpy as np
R = (_REPO + "/")
CH = json.load(open(R + "data/kaggle_format/agi2_eval_challenges.json")); SOL = json.load(open(R + "data/kaggle_format/agi2_eval_solutions.json"))
def canon(d): return sorted(d, key=lambda p: (len(p["input"]) * len(p["input"][0]), len(p["input"]), len(p["input"][0]), json.dumps(p["input"])))
def final(r):
    rs = [x for x in r.get("rounds", []) if "test_out" in x]
    if not rs: return None, False
    v = [x for x in rs if x.get("verified")]; x = v[0] if v else rs[-1]
    return dict(zip(r["query_ids"], x["test_out"])), bool(v)
FULL, FOLD = {}, collections.defaultdict(list)
for l in open(R + "llm/results/qwen38_faloo_greedy_b16384.jsonl"):
    r = json.loads(l)
    if r.get("kind") not in ("full", "fold") or "error" in r: continue
    t = r["task_id"]; nt = len(SOL[t]); o, v = final(r)
    tests = [None if o is None else o.get(f"test:{k}") for k in range(nt)]
    x = dict(ver=v, tests=tests)
    if r["kind"] == "full": FULL[t] = x
    else:
        x["held"] = bool(o is not None and o.get(f"demo:{r['fold']}") == canon(CH[t]["train"])[r["fold"]]["output"]); x["i"] = r["fold"]; FOLD[t].append(x)
print("folds in main file", sum(len(v) for v in FOLD.values()), "tasks", len(FOLD))
P = collections.defaultdict(list)
for fn in ("qwen38_ps_b16384.jsonl", "qwen38_ps_xhigh_b16384.jsonl"):
    for l in open(R + "llm/results/" + fn):
        r = json.loads(l)
        if "error" in r or r.get("task_id") not in SOL: continue
        t = r["task_id"]; nt = len(SOL[t]); rs = [x for x in r.get("rounds", []) if "n_ok" in x]; v = [x for x in rs if x.get("verified")]; c = v[0] if v else (rs[-1] if rs else None)
        P[t].append(dict(ver=bool(v), tests=[None] * nt if c is None or "test_out" not in c else (c["test_out"] + [None] * nt)[:nt]))
com = sorted(t for t in FULL if len(P[t]) >= 3)
def p2(cands, t, mode, rng=None):
    ok = 0
    for k in range(len(SOL[t])):
        G = [(r, x[k]) for r, x in cands if x[k] is not None]
        if mode == "random" and rng is not None: rng.shuffle(G)
        if mode == "vote":
            cnt = collections.Counter(json.dumps(g) for _, g in G); best = {}
            for r, g in G:
                s = json.dumps(g); best[s] = min(best.get(s, 9), r)
            order = sorted(best, key=lambda s: (best[s], -cnt[s]))
            ok += json.dumps(SOL[t][k]) in order[:2]; continue
        seen = []
        for r, g in sorted(G, key=lambda c: c[0]):
            if g not in seen: seen.append(g)
            if len(seen) == 2: break
        ok += SOL[t][k] in seen
    return ok / len(SOL[t])
def arms(t, sort_fold):
    fs = sorted(FOLD[t], key=lambda x: x["i"]) if sort_fold else FOLD[t]
    a = [(0 if x["ver"] else 1, x["tests"]) for x in P[t]]
    b = [(0 if FULL[t]["ver"] else 2, FULL[t]["tests"])] + [(0 if (x["ver"] and x["held"]) else (1 if x["ver"] else 2), x["tests"]) for x in fs]
    return a, b
def rep(lab, mode, sort_fold):
    A = {t: p2(arms(t, sort_fold)[0], t, mode) for t in com}; B = {t: p2(arms(t, sort_fold)[1], t, mode) for t in com}
    d = np.array([B[t] - A[t] for t in com]); W = np.random.default_rng(0).multinomial(len(com), np.full(len(com), 1 / len(com)), size=10000); ci = np.percentile(W @ d, [2.5, 97.5])
    print(f"{lab}: plain {sum(A.values()):.1f}; full+folds {sum(B.values()):.1f}; difference {d.sum():+.1f} [{ci[0]:+.1f}, {ci[1]:+.1f}]; better {int((d>0).sum())}, worse {int((d<0).sum())}")
rep("file order", "first", False)
rep("fold-index order", "first", True)
rep("tier, then vote count", "vote", True)
rs = random.Random(0); Da = []; Db = []
for s in range(200):
    Da.append(sum(p2(arms(t, True)[0], t, "random", rs) for t in com)); Db.append(sum(p2(arms(t, True)[1], t, "random", rs) for t in com))
print(f"random ties, 200 draws: plain mean {np.mean(Da):.2f}, full+folds mean {np.mean(Db):.2f}, difference {np.mean(Db)-np.mean(Da):+.2f}")
def verified_only():
    # one answer per task: the highest tier output; how many tasks have a top-tier candidate at all
    a = sum(any(x["ver"] for x in P[t]) for t in com); b = sum(FULL[t]["ver"] or any(x["ver"] and x["held"] for x in FOLD[t]) for t in com)
    print("tasks with a top-tier candidate: plain", a, "full+folds", b)
verified_only()

# ---- range check requested by the lead: tiers and plain-arm rule
def plain_cands(t, rule):
    out = []
    for fn in ("qwen38_ps_b16384.jsonl", "qwen38_ps_xhigh_b16384.jsonl"):
        for r in RAW[fn].get(t, []):
            nt = len(SOL[t])
            key = "n_ok" if rule == "n_ok" else "test_out"
            rs = [x for x in r.get("rounds", []) if key in x]
            v = [x for x in rs if x.get("verified")]
            c = v[0] if v else (rs[-1] if rs else None)
            out.append((0 if v else 1, [None] * nt if c is None or "test_out" not in c else (c["test_out"] + [None] * nt)[:nt]))
    return out
RAW = {}
for fn in ("qwen38_ps_b16384.jsonl", "qwen38_ps_xhigh_b16384.jsonl"):
    RAW[fn] = collections.defaultdict(list)
    for l in open(R + "llm/results/" + fn):
        r = json.loads(l)
        if "error" not in r and r.get("task_id") in SOL:
            RAW[fn][r["task_id"]].append(r)
def fold_cands(t, tiers, sort_fold):
    fs = sorted(FOLD[t], key=lambda x: x["i"]) if sort_fold else FOLD[t]
    top = (0 if FULL[t]["ver"] else (1 if tiers == 2 else 2), FULL[t]["tests"])
    rest = []
    for x in fs:
        if x["ver"] and x["held"]:
            rest.append((0, x["tests"]))
        elif tiers == 3 and x["ver"]:
            rest.append((1, x["tests"]))
        else:
            rest.append((tiers - 1, x["tests"]))
    return [top] + rest
print("\nRange check, first-seen within a tier")
A = {rule: {t: p2(plain_cands(t, rule), t, "first") for t in com} for rule in ("n_ok", "test_out")}
for rule in A:
    print(f"plain arm, last-round rule keyed on {rule}: {sum(A[rule].values()):.1f}")
for tiers, sf, lab in ((3, False, "three tiers, file order"), (3, True, "three tiers, canonical order"), (2, True, "two tiers, canonical order"), (2, False, "two tiers, file order")):
    B = {t: p2(fold_cands(t, tiers, sf), t, "first") for t in com}
    for rule in A:
        d = np.array([B[t] - A[rule][t] for t in com]); W = np.random.default_rng(0).multinomial(len(com), np.full(len(com), 1 / len(com)), size=10000); ci = np.percentile(W @ d, [2.5, 97.5])
        print(f"  {lab}: fold arm {sum(B.values()):.1f}; minus plain ({rule}) {d.sum():+.1f} [{ci[0]:+.1f}, {ci[1]:+.1f}]")
