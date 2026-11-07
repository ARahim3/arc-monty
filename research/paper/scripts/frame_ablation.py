"""Theory check: does storing behaviour in the object's canonical (D8) frame matter? Read-only ablation.

Runs ONLY the behaviour learning module on every unique ARC-AGI-1/2 task (1,147), with its reference-frame
hypotheses restricted to ("canon",), ("abs",) or both (the shipped setting), by overriding arcmonty.behavior.FRAMES
inside the worker processes (no file in arcmonty/ is touched). Reports pass@2, answers at LOO evidence 1.0 and
their precision.  Usage: python research/paper/scripts/frame_ablation.py <nproc>  -> research/paper/data/frame_ablation.json
"""
import json
import multiprocessing as mp
import os
import sys
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from arcmonty import behavior  # noqa: E402
from arcmonty.data import load_split  # noqa: E402
from arcmonty.evaluate import score_task  # noqa: E402
from arcmonty.vote import attempts_from, pool  # noqa: E402

CONFIGS = {"both": ("canon", "abs"), "canon": ("canon",), "abs": ("abs",)}


def _init(frames):
    behavior.FRAMES = frames


def _one(item):
    key, task = item
    t0 = time.time()
    try:
        cands = behavior.candidates(task)
    except Exception:
        cands = []
    best = pool(cands)
    top = best[0] if best else None
    return dict(task=key, pass2=score_task(task, attempts_from(task, cands)) if cands else 0.0,
                ev=float(top["evidence"]) if top else None,
                top_ok=score_task(task, [[g] for g in top["preds"]]) if top else None, sec=time.time() - t0)


if __name__ == "__main__":
    nproc = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    tasks = {}
    for s in ("agi2-eval", "agi1-eval", "agi2-train", "agi1-train"):
        for k, t in load_split(s).items():
            tasks.setdefault(k, t)
    out = {}
    for name, frames in CONFIGS.items():
        with mp.Pool(nproc, initializer=_init, initargs=(frames,)) as p:
            rows = p.map(_one, list(tasks.items()), chunksize=2)
        full = [r for r in rows if r["ev"] is not None and r["ev"] >= 0.99]
        out[name] = dict(n=len(rows), pass2=sum(r["pass2"] for r in rows), answered=sum(r["ev"] is not None for r in rows),
                         loo1=len(full), loo1_correct=sum(r["top_ok"] for r in full),
                         sec=sum(r["sec"] for r in rows), solved=sorted(r["task"] for r in rows if r["pass2"] > 0))
        o = out[name]
        print(f"{name:5s} n={o['n']} pass@2={o['pass2']:.1f} answered={o['answered']} LOO=1.0: {o['loo1_correct']:.0f}/{o['loo1']} "
              f"cpu={o['sec']:.0f}s", flush=True)
    json.dump(out, open(os.path.join(ROOT, "research", "paper", "data", "frame_ablation.json"), "w"), indent=1)
