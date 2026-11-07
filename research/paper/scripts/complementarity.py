"""Complementarity of Monty-ARC with the Qwen3.8-27B program-synthesis column on ARC-AGI-2 public eval (read-only).

Monty-ARC is re-run with the frozen arcmonty/ code; Qwen uses the saved TPU benchmark samples
(llm/results/qwen38_ps_b16384.jsonl, 2 samples x <=2 rounds, 16k thinking/round). The merge mirrors the tri notebook
(tools/build_tri.py): verified Qwen output > confident Monty-ARC > (NVARC: absent here) > unverified Qwen > Monty guesses.
Usage: python research/paper/scripts/complementarity.py [nproc]   ->  research/paper/data/complementarity.json
"""
import json
import multiprocessing as mp
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "llm"))
import numpy as np  # noqa: E402

from arcmonty import monty_arc  # noqa: E402
from arcmonty.vote import attempts_from, confident  # noqa: E402


def _monty(item):
    key, raw = item
    g = lambda x: np.array(x, dtype=np.int8)
    task = {"train": [(g(p["input"]), g(p["output"])) for p in raw["train"]], "test": [g(p["input"]) for p in raw["test"]]}
    cands = monty_arc.candidates(task)
    conf = confident(cands)
    best = attempts_from(task, cands)
    sure = attempts_from(task, cands, 0.99) if conf else [[] for _ in task["test"]]
    return key, {"confident": [[a.tolist() for a in x[:1]] for x in sure], "guesses": [[a.tolist() for a in x[:2]] for x in best]}


def _top2(seq):
    out = []
    for gr in seq:
        if gr and gr not in out:
            out.append(gr)
        if len(out) == 2:
            break
    return out


if __name__ == "__main__":
    from arcllm.tasks import load_eval, pass2  # noqa: E402
    from score import load, ps_cands  # noqa: E402
    nproc = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    ch, sol = load_eval()
    with mp.Pool(nproc) as p:
        mon = dict(p.map(_monty, sorted(ch.items()), chunksize=1))
    recs = load(os.path.join(ROOT, "llm", "results"))[("qwen38", "ps", 16384)]
    subs = {k: {} for k in ("qwen", "monty", "merge")}
    for t in ch:
        n = len(ch[t]["test"])
        q = ps_cands(recs, t, n)                       # [(grid, verified)] ranked, per test output
        m = mon[t]
        for name in subs:
            subs[name][t] = []
        for j in range(n):
            qv = [gr for gr, v in q[j] if v]
            qu = [gr for gr, v in q[j] if not v]
            mc = m["confident"][j] if j < len(m["confident"]) else []
            mg = m["guesses"][j] if j < len(m["guesses"]) else []
            subs["qwen"][t].append(_top2(qv + qu))
            subs["monty"][t].append(_top2(mg))
            subs["merge"][t].append(_top2(qv + mc + qu + mg))
    res = {}
    for name, s in subs.items():
        tot, per = pass2(s, sol)
        res[name] = dict(score=tot, solved=sorted(k for k, v in per.items() if v > 0), per=per)
        print(f"{name:6s} pass@2 {tot:5.2f}/120")
    only_m = sorted(set(res["monty"]["solved"]) - set(res["qwen"]["solved"]))
    lost = sorted(k for k in ch if res["merge"]["per"][k] < res["qwen"]["per"][k])
    print("Monty-only solves:", only_m, "| tasks the merge lost vs Qwen:", lost)
    res["monty_only"], res["merge_lost"] = only_m, lost
    json.dump(res, open(os.path.join(ROOT, "research", "paper", "data", "complementarity.json"), "w"), indent=1)
