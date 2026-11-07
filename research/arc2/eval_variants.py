"""Expected tri score for each measured Qwen arm (per-task outcomes from llm/results/qwen38_<arm>.jsonl) under the
v3 schedule and the v4 schedule, averaged over throughput x NVARC-speed scenarios (tri_sim.simulate).
    python research/arc2/eval_variants.py [arm ...]
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
from tri_sim import qwen_outcomes, simulate  # noqa: E402

SCEN = [(R, sp) for R in (350, 500, 650, 800) for sp in (0.8, 1.0, 1.25)]
V3 = dict(qorder="reverse", norder="v3")
V4 = dict(qorder="small", norder="density", nv_verified=True)


def expected(Q, hours, cfg, reps=40):
    xs = [simulate(Q, hours, R, nv_speed=sp, reps=reps, **cfg)[0] for R, sp in SCEN]
    return float(np.mean(xs)), float(np.min(xs)), float(np.max(xs))


if __name__ == "__main__":
    arms = sys.argv[1:] or ["ps_b16384"]
    base = qwen_outcomes()
    ref = expected(base, 4.5, V3)
    print(f"reference v3 (xhigh 16k, 4.5 h, v3 schedule): mean {ref[0]:.1f} [{ref[1]:.1f}, {ref[2]:.1f}]")
    for arm in arms:
        p = os.path.join(ROOT, f"llm/results/qwen38_{arm}.jsonl")
        Q = base if arm == "ps_b16384" else qwen_outcomes(p)
        miss = [t for t in base if t not in Q]
        if miss:                                    # incomplete arm: fill missing tasks from the baseline
            Q = dict(Q, **{t: base[t] for t in miss})
        out = []
        for h in (2.0, 3.0, 4.5):
            m, lo, hi = expected(Q, h, V4)
            out.append(f"v4 {h}h {m:.1f} [{lo:.1f},{hi:.1f}]")
        m3 = expected(Q, 4.5, V3)[0]
        print(f"{arm:24s} (missing {len(miss):3d}) v3-schedule 4.5h {m3:.1f} | " + " | ".join(out))


def pooled(reps=30):
    """v3 vs v4-A over every complete Qwen sample set we have (original s0/s1, replicate s0/s1; gaps filled from s0)."""
    base = qwen_outcomes()
    sets = {"orig s0": base}
    o1 = qwen_outcomes(sample=1)
    sets["orig s1"] = dict(base, **o1)
    rp = os.path.join(ROOT, "llm/results/qwen38_ps_xhigh_b16384.jsonl")
    for k in (0, 1):
        r = qwen_outcomes(rp, sample=k)
        if len(r) >= 100:
            sets[f"replicate s{k}"] = dict(base, **r)
    rows = []
    for name, Q in sets.items():
        vc = sum(q["v"] * q["frac"] for q in Q.values())
        a = expected(Q, 4.5, V3, reps)[0]
        b = expected(Q, 3.0, V4, reps)[0]
        rows.append((a, b))
        print(f"  {name:12s} Qwen verified-correct {vc:5.1f}/120 | v3 {a:.1f} | v4-A {b:.1f} | delta {b - a:+.1f}")
    a, b = np.mean(rows, axis=0)
    print(f"  pooled: v3 {a:.1f}  v4-A {b:.1f}  delta {b - a:+.1f}")
