"""Paired A/B: Monty perception notes (hint) vs plain prompt, Qwen3.8-27B PS xhigh 16k/round <=2 rounds, public eval.
Per task: mean verified-correct over the samples each arm has (plain = original run s0/s1 + replicate s0/s1).
Bootstrap CI over tasks. Also reports excluding the 4 tasks Monty-ARC itself solves.
    python research/arc2/hint_ab.py
"""
import json
import os
import random
import sys
from collections import defaultdict

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
MONTY_SOLVED = {"0934a4d8", "135a2760", "1818057f", "dbff022c"}


def per_sample(path):
    out = defaultdict(dict)
    if not os.path.exists(path):
        return out
    for line in open(path):
        r = json.loads(line)
        if "error" in r:
            continue
        rs = [x for x in r["rounds"] if "n_ok" in x]
        v = [x for x in rs if x.get("verified")]
        vc = (sum(v[0]["correct"]) / len(v[0]["correct"])) if v else 0.0
        out[r["task_id"]][(os.path.basename(path), r["sample"])] = dict(vc=vc, v=bool(v), cost=r["cost"],
                                                                         r0=bool(v) and v[0]["round"] == 0)
    return out


def merge(*ds):
    m = defaultdict(dict)
    for d in ds:
        for t, s in d.items():
            m[t].update(s)
    return m


def summary(name, d, tasks):
    n = sum(len(d[t]) for t in tasks)
    vc = np.mean([np.mean([x["vc"] for x in d[t].values()]) for t in tasks]) * len(tasks)
    v = np.mean([np.mean([x["v"] for x in d[t].values()]) for t in tasks]) * len(tasks)
    cost = np.mean([x["cost"] for t in tasks for x in d[t].values()])
    r0 = np.mean([np.mean([x["r0"] for x in d[t].values()]) for t in tasks]) * len(tasks)
    print(f"{name:34s} samples {n:3d}  per-task-mean verified {v:5.1f}  verified-correct {vc:5.1f}  "
          f"verified in round 1 {r0:4.1f}  mean cost {cost / 1e3:4.1f}k")


def ab(a, b, tasks, reps=4000, seed=0):
    da = np.array([np.mean([x["vc"] for x in a[t].values()]) - np.mean([x["vc"] for x in b[t].values()]) for t in tasks])
    rng = random.Random(seed)
    boots = [sum(da[rng.randrange(len(da))] for _ in da) for _ in range(reps)]
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return da.sum(), lo, hi


if __name__ == "__main__":
    R = os.path.join(ROOT, "llm/results")
    plain = merge(per_sample(os.path.join(R, "qwen38_ps_b16384.jsonl")), per_sample(os.path.join(R, "qwen38_ps_xhigh_b16384.jsonl")))
    hint = per_sample(os.path.join(R, "qwen38_ps_xhigh_hint_b16384.jsonl"))
    orig = per_sample(os.path.join(R, "qwen38_ps_b16384.jsonl"))
    rep = per_sample(os.path.join(R, "qwen38_ps_xhigh_b16384.jsonl"))
    tasks = sorted(t for t in hint if t in plain)
    print(f"tasks with both arms: {len(tasks)}")
    summary("plain (orig + replicate)", plain, tasks)
    summary("hint (Monty perception notes)", hint, tasks)
    d, lo, hi = ab(hint, plain, tasks)
    print(f"hint - plain: {d:+.1f} verified-correct tasks per {len(tasks)} [95% CI {lo:+.1f}, {hi:+.1f}]")
    k = [t for t in tasks if t not in MONTY_SOLVED]
    d, lo, hi = ab(hint, plain, k)
    print(f"  excl. Monty-solved ({len(k)}): {d:+.1f} [{lo:+.1f}, {hi:+.1f}]")
    both = sorted(t for t in rep if t in orig)
    if both:
        d, lo, hi = ab(rep, orig, both)
        print(f"noise check, replicate - original (same config, {len(both)} tasks): {d:+.1f} [{lo:+.1f}, {hi:+.1f}]")


def detail():
    """Per-task view: where hint and plain differ, and train-verification vs test-correctness."""
    R = os.path.join(ROOT, "llm/results")
    plain = merge(per_sample(os.path.join(R, "qwen38_ps_b16384.jsonl")), per_sample(os.path.join(R, "qwen38_ps_xhigh_b16384.jsonl")))
    hint = per_sample(os.path.join(R, "qwen38_ps_xhigh_hint_b16384.jsonl"))
    tasks = sorted(t for t in hint if t in plain)
    m = lambda d, t, k: np.mean([x[k] for x in d[t].values()])
    rows = [(m(hint, t, "vc") - m(plain, t, "vc"), t, m(hint, t, "v"), m(plain, t, "v")) for t in tasks]
    rows.sort()
    print("largest losses:", [(t, round(d, 2)) for d, t, _, _ in rows[:6]])
    print("largest gains: ", [(t, round(d, 2)) for d, t, _, _ in rows[-6:]])
    hv = sum(m(hint, t, "v") for t in tasks); pv = sum(m(plain, t, "v") for t in tasks)
    hc = sum(m(hint, t, "vc") for t in tasks); pc = sum(m(plain, t, "vc") for t in tasks)
    print(f"precision of verified programs: hint {hc / max(hv, 1e-9):.2f} ({hc:.1f}/{hv:.1f}), plain {pc / max(pv, 1e-9):.2f} ({pc:.1f}/{pv:.1f})")
