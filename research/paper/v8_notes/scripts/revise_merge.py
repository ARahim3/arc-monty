"""v8 revision: merge order with one Qwen sample per task vs the two-sample merge of the earlier table. Own code. 4 workers for Monty-ARC
(frozen, imported). Candidates per test output follow llm/kaggle/qwen_phase.py summarize(): every round's output, ranked by (verified count, best n_ok).
Output ../revise_merge.txt"""
import os  # noqa: E402  (release: paths from the repo root)
_REPO = os.environ.get("ARC_MONTY_ROOT", os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..")))  # repo root
import json, multiprocessing as mp, os, random, sys
for v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(v, "1")
ROOT = _REPO
sys.path.insert(0, ROOT)
import numpy as np
CH = json.load(open(ROOT + "/data/kaggle_format/agi2_eval_challenges.json"))
SOL = json.load(open(ROOT + "/data/kaggle_format/agi2_eval_solutions.json"))
def monty(item):
    from arcmonty import monty_arc
    from arcmonty.vote import attempts_from, confident
    k, raw = item
    g = lambda x: np.array(x, dtype=np.int8)
    task = {"train": [(g(p["input"]), g(p["output"])) for p in raw["train"]], "test": [g(p["input"]) for p in raw["test"]]}
    c = monty_arc.candidates(task)
    sure = attempts_from(task, c, 0.99) if confident(c) else [[] for _ in task["test"]]
    best = attempts_from(task, c)
    return k, dict(conf=[[a.tolist() for a in x[:1]] for x in sure], guess=[[a.tolist() for a in x[:2]] for x in best])
def top2(xs):
    o = []
    for x in xs:
        if x and x not in o:
            o.append(x)
        if len(o) == 2:
            break
    return o
def load(fn):
    d = {}
    for l in open(f"{ROOT}/llm/results/{fn}"):
        r = json.loads(l)
        if "error" not in r:
            d[(r["task_id"], r["sample"])] = r
    return d
def cands(D, samples):
    out = {}
    for t in CH:
        out[t] = []
        for j in range(len(CH[t]["test"])):
            S, G = {}, {}
            for k in samples:
                for rd in (D.get((t, k)) or {}).get("rounds", []):
                    to = rd.get("test_out")
                    if not to or j >= len(to) or to[j] is None:
                        continue
                    key = json.dumps(to[j]); G[key] = to[j]
                    s = S.get(key, (0, -1))
                    S[key] = (s[0] + bool(rd.get("verified")), max(s[1], rd.get("n_ok", -1)))
            r = sorted(S, key=lambda x: S[x], reverse=True)
            out[t].append(([G[x] for x in r if S[x][0] > 0], [G[x] for x in r if S[x][0] == 0]))
    return out
def score(C, M, order, rng=None):
    tot = 0.0
    for t in CH:
        n = len(CH[t]["test"]); hit = 0
        for j in range(n):
            qv, qu = C[t][j]
            g = dict(qv=qv, qu=qu, mc=M[t]["conf"][j] if j < len(M[t]["conf"]) else [], mg=M[t]["guess"][j] if j < len(M[t]["guess"]) else [])
            if order == "random":
                P = qv + qu + g["mc"] + g["mg"]; rng.shuffle(P); a = top2(P)
            else:
                a = top2(sum((g[k] for k in order), []))
            hit += SOL[t][j] in a
        tot += hit / n
    return tot
if __name__ == "__main__":
    with mp.Pool(4) as p:
        M = dict(p.imap_unordered(monty, list(CH.items()), chunksize=1))
    for fn in ("qwen38_ps_b16384.jsonl", "qwen38_ps_xhigh_b16384.jsonl"):
        D = load(fn)
        both = sum((t, 0) in D and (t, 1) in D for t in CH)
        print(fn, "records", len(D), "tasks with both samples", both)
        for lab, s in (("both samples", (0, 1)), ("sample 0", (0,)), ("sample 1", (1,))):
            have = sum(any((t, k) in D for k in s) for t in CH)
            C = cands(D, s)
            crowd = tot = 0
            for t in CH:
                for j in range(len(CH[t]["test"])):
                    qv, qu = C[t][j]; A = []
                    for x in qv + qu + (M[t]["conf"][j] if j < len(M[t]["conf"]) else []) + (M[t]["guess"][j] if j < len(M[t]["guess"]) else []):
                        if x and x not in A:
                            A.append(x)
                    tot += 1; crowd += len(A) > 2
            rs = [score(C, M, "random", random.Random(i)) for i in range(40)]
            print(f"  {lab}: tasks {have}; precision {score(C,M,['qv','mc','qu','mg'])}; conf ignored {score(C,M,['qv','qu','mg'])}; unverified first {score(C,M,['qu','qv','mc','mg'])}; guesses first {score(C,M,['mg','mc','qu','qv'])}; Qwen alone {score(C,M,['qv','qu'])}; random mean {np.mean(rs):.2f} ({min(rs)}, {max(rs)}); crowded {crowd} of {tot}")
