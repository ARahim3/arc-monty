"""Task-level simulation of the tri notebook on a 240-task hidden set that looks like public eval (2 copies of the
120 public-eval tasks), using the measured per-task Qwen3.8 PS outcomes (sample 0, xhigh, 16k/round, <=2 rounds,
TPU) and the NVARC time model fitted on the tri v2 smoke run. NVARC correctness is drawn per task with
P(N | Qwen verified-correct) and P(N | not) from P(N)=0.31 and rho=0.43 (tri_model.cond_nvarc).

Compares Qwen task order x NVARC queue policy x QWEN_HOURS x Qwen throughput R x NVARC speed.
    python research/arc2/tri_sim.py
"""
import json
import os
import random
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
from tri_model import cond_nvarc, QWEN_SETUP_S, WALL_H  # noqa: E402

CH = json.load(open(os.path.join(ROOT, "data/kaggle_format/agi2_eval_challenges.json")))
PS = [json.loads(l) for l in open(os.path.join(ROOT, "llm/results/qwen38_ps_b16384.jsonl"))]


def qwen_outcomes(path=None, sample=0):
    recs = PS if path is None else [json.loads(l) for l in open(path)]
    out = {}
    for r in recs:
        if r.get("sample") != sample or "error" in r:
            continue
        rs = [x for x in r["rounds"] if "n_ok" in x]
        v = [x for x in rs if x.get("verified")]
        if v:
            frac = sum(v[0]["correct"]) / len(v[0]["correct"])
            out[r["task_id"]] = dict(v=True, vround=v[0]["round"], frac=frac, cost=r["cost"])
        else:
            b = max(rs, key=lambda x: x["n_ok"], default=None)
            frac = (sum(b["correct"]) / len(b["correct"])) if b and b.get("correct") else 0.0
            out[r["task_id"]] = dict(v=False, vround=None, frac=frac, cost=r["cost"])
    return out


def nv_time(t):
    task = CH[t]
    s = sum(len(g) * (len(g[0]) + 1) for p in task["train"] for g in (p["input"], p["output"]))
    s += sum(len(p["input"]) * (len(p["input"][0]) + 1) for p in task["test"])
    s = min(s, 8192)
    return min(0.0369 * s + 7.64e-6 * s * s + 300 * len(task["test"]), 1250) + 15


def cells(t):
    task = CH[t]
    return sum(len(g) * len(g[0]) for p in task["train"] for g in (p["input"], p["output"])) + \
        sum(len(p["input"]) * len(p["input"][0]) for p in task["test"])


def simulate(Q, qwen_hours, R, qorder, norder, nv_speed=1.0, nv_verified=False, p_n=0.31, rho=0.43, reps=200,
             seed=0, wall_h=WALL_H):
    rng = random.Random(seed)
    ids = sorted(CH)
    tasks = [(t, c) for c in range(2) for t in ids]           # 240 = 2 copies
    p_qc = np.mean([Q[t]["v"] * Q[t]["frac"] for t in ids])
    pn_qc, pn_nqc = cond_nvarc(p_qc, p_n, rho)
    tot = []
    for rep in range(reps):
        # NVARC correctness per task, conditioned on Qwen verified-correct
        nvok = {k: rng.random() < (pn_qc if Q[k[0]]["v"] and Q[k[0]]["frac"] > 0 else pn_nqc) for k in tasks}
        # Qwen order
        if qorder == "reverse":
            qo = sorted(tasks, key=lambda k: (k[0], k[1]), reverse=True)
        else:
            qo = sorted(tasks, key=lambda k: (cells(k[0]), k))
        budget = max(0.0, qwen_hours * 3600 - QWEN_SETUP_S) * 0.95 * R
        done, used = [], 0.0
        for k in qo:
            c = Q[k[0]]["cost"]
            if used + c > budget:
                break
            used += c
            done.append(k)
        q_h = min(qwen_hours, (QWEN_SETUP_S + used / R / 0.95) / 3600) if done else 0.0
        attempted = set(done)
        # NVARC queue
        def grp(k):
            if k not in attempted:
                return 0
            q = Q[k[0]]
            return 1 if not q["v"] else (2 if q["vround"] >= 1 else 3)
        val = {0: p_n, 1: pn_nqc, 2: 0.36 * pn_nqc, 3: 0.05 * pn_nqc}
        cand = [k for k in tasks if grp(k) <= 1 or nv_verified]
        if norder == "v3":
            cand = sorted([k for k in cand if grp(k) <= 1], key=lambda k: k)
        elif norder == "group":
            cand.sort(key=lambda k: (grp(k), nv_time(k[0]), k))
        elif norder == "density":
            cand.sort(key=lambda k: (-val[grp(k)] / nv_time(k[0]), k))
        T = (wall_h - q_h) * 3600
        free = [0.0] * 4
        nv_done = set()
        for k in cand:                                        # 4 workers pull from the shared queue
            w = min(range(4), key=lambda i: free[i])
            if free[w] >= T:
                break
            dt = nv_time(k[0]) / nv_speed
            if free[w] + dt <= T + 0.5 * dt:                  # a task cut half-way still leaves partial candidates
                nv_done.add(k)
            free[w] += dt
        s = 0.0
        for k in tasks:
            q = Q[k[0]]
            att = k in attempted
            if att and q["v"]:
                ok = q["frac"]
                if ok < 1 and k in nv_done and nvok[k]:       # NVARC as attempt 2 of a wrong verified program
                    ok = 1.0
                s += ok
            elif k in nv_done:
                s += 1.0 if nvok[k] else (q["frac"] * 0.3 if att else 0.0)   # unverified Qwen rarely gets a slot
            elif att:
                s += q["frac"]
        tot.append(100 * s / len(tasks))
    return float(np.mean(tot)), float(np.std(tot)), dict(q_tasks=len(done), q_h=round(q_h, 2),
                                                         nv_done=len(nv_done), nv_queue=len(cand))


if __name__ == "__main__":
    Q = qwen_outcomes()
    print("Qwen sample-0 on eval: verified", sum(q["v"] for q in Q.values()), "verified-correct",
          round(sum(q["v"] * q["frac"] for q in Q.values()), 1), "mean cost", round(np.mean([q["cost"] for q in Q.values()])))
    base = dict(qorder="reverse", norder="v3")
    configs = [("v3 (reverse, v3 queue)", base),
               ("small-first Qwen, v3 queue", dict(qorder="small", norder="v3")),
               ("reverse, group queue", dict(qorder="reverse", norder="group")),
               ("small, group queue", dict(qorder="small", norder="group")),
               ("small, density queue", dict(qorder="small", norder="density")),
               ("small, density, +NVARC on verified", dict(qorder="small", norder="density", nv_verified=True))]
    for R in (350, 500, 650):
        for sp in (0.8, 1.0, 1.25):
            print(f"\nR={R} tok/s, NVARC speed x{sp}")
            for name, cfg in configs:
                row = []
                for h in (0.0, 2.5, 3.5, 4.5, 6.0):
                    m, sd, d = simulate(Q, h, R, nv_speed=sp, reps=60, **cfg)
                    row.append(f"{h}h {m:4.1f}")
                print(f"  {name:38s} " + " | ".join(row))
