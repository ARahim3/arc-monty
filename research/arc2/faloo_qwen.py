"""Fold-agreement LOO (FA-LOO) for Qwen3.8-27B program synthesis on the ARC-AGI-2 public eval (TPU runner).

Learner A(D) = Qwen3.8-27B PS exactly as llm/run_bench.py's "ps" harness (16k thinking per round, <=2 rounds with the
cell-diff feedback, xhigh template), made deterministic and demo-order-canonical:
  * greedy decoding (temperature 0), no seed;
  * demos in canonical order (input area, height, width, then grid text); the unlabeled query inputs (held-out demo
    input + every test input) are also shown in canonical order, so the prompt does not reveal which query is the
    held-out demo;
  * A's output = the final program (the first verified one, else the last round's program), run on every query.
Jobs (one JSONL record each, resumable, keyed by kind/task/fold):
  full  A(D) on all demos                      fold  A(D minus demo i), i = canonical index
  rev   A(D) with the demo order reversed      rep   A(D) again, same order (numeric determinism check)
Phases: A = full on all 120 tasks + folds for the tasks with a verified plain (stochastic) sample;
        B = folds for tasks whose greedy full run verified but are not in A;  C = rev + rep on tasks whose full run
        verified;  D (optional) = folds for every remaining task.
    python research/arc2/faloo_qwen.py --url URL[,URL2] --tokenizer DIR --phases A,B,C [--concurrency 80]
"""
import argparse
import json
import os
import sys
import threading
import time
import zlib
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "llm"))
sys.path.insert(0, HERE)
import run_bench as RB                                   # noqa: E402
from arcllm.engine import Engine                         # noqa: E402
from arcllm.tasks import load_eval                       # noqa: E402
from bench2 import fast_generate                         # noqa: E402

OUT = os.path.join(ROOT, "llm/results/qwen38_faloo_greedy_b16384.jsonl")
PLAIN = [os.path.join(ROOT, "llm/results/qwen38_ps_b16384.jsonl"), os.path.join(ROOT, "llm/results/qwen38_ps_xhigh_b16384.jsonl")]


def gkey(g):
    return (len(g) * len(g[0]), len(g), len(g[0]), json.dumps(g))


def build(task, sol, kind, fold):
    """Return (task_for_prompt, sol_for_queries, query_ids). query_ids name each shown test input: 'demo:j' or 'test:t'
    (j = canonical demo index, t = original test index)."""
    demos = sorted(task["train"], key=lambda p: gkey(p["input"]))
    if kind == "rev":
        demos = demos[::-1]
    queries = [("test:%d" % t, x["input"], sol[t]) for t, x in enumerate(task["test"])]
    train = demos
    if kind == "fold":
        train = [p for j, p in enumerate(demos) if j != fold]
        queries.append(("demo:%d" % fold, demos[fold]["input"], demos[fold]["output"]))
    queries.sort(key=lambda q: gkey(q[1]))
    t = {"train": [{"input": p["input"], "output": p["output"]} for p in train],
         "test": [{"input": q[1]} for q in queries]}
    return t, [q[2] for q in queries], [q[0] for q in queries]


def learner_output(rec):
    """Outputs of A's final program on the queries: first verified round, else the last round with a program."""
    rounds = [r for r in rec.get("rounds", []) if "test_out" in r]
    if not rounds:
        return None, False, -1
    v = [r for r in rounds if r.get("verified")]
    r = v[0] if v else rounds[-1]
    return r["test_out"], bool(v), r.get("n_ok", -1)


def load_done(path):
    done = {}
    if os.path.exists(path):
        for line in open(path):
            try:
                r = json.loads(line)
            except Exception:
                continue
            if "error" not in r:
                done[(r["kind"], r["task_id"], r["fold"])] = r
    return done


def plain_verified_tasks():
    out = set()
    for f in PLAIN:
        if not os.path.exists(f):
            continue
        for line in open(f):
            r = json.loads(line)
            if any(x.get("verified") for x in r.get("rounds", [])):
                out.add(r["task_id"])
    return out


def jobs_for(phase, ch, done):
    ids = sorted(ch)
    full_ok = {t for t in ids if ("full", t, -1) in done and learner_output(done[("full", t, -1)])[1]}
    folds = lambda ts: [("fold", t, i) for t in sorted(ts) for i in range(len(ch[t]["train"]))]
    if phase == "A":
        js = [("full", t, -1) for t in ids] + folds(plain_verified_tasks())
    elif phase == "B":
        js = folds(full_ok - plain_verified_tasks())
    elif phase == "C":
        js = [("rev", t, -1) for t in sorted(full_ok)] + [("rep", t, -1) for t in sorted(full_ok)]
    elif phase == "D":
        js = folds(set(ids) - full_ok - plain_verified_tasks())
    else:
        raise ValueError(phase)
    return [j for j in js if j not in done]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--tokenizer", required=True)
    ap.add_argument("--phases", default="A,B,C")
    ap.add_argument("--concurrency", type=int, default=80)
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--also-read", default="", help="extra result files whose records count as done (comma list)")
    ap.add_argument("--shard", default="0/1", help="k/N: run only jobs with crc32(job) %% N == k (two VMs)")
    a0 = ap.parse_args()
    a = argparse.Namespace(model="qwen38", budget=16384, answer_room=8192, rounds=2, max_model_len=57344,
                           sandbox_timeout=10.0)
    Engine.generate = fast_generate
    ch, sol = load_eval()
    urls = a0.url.split(",")
    first = Engine(urls[0], "qwen38", a0.tokenizer, {"temperature": 0.0}, {"reasoning_effort": "xhigh"})
    engines = [first]
    for u in urls[1:]:
        e = Engine.__new__(Engine)
        e.__dict__.update(first.__dict__)
        e.url = u.rstrip("/") + "/completions"
        engines.append(e)
    lock = threading.Lock()
    for phase in a0.phases.split(","):
        done = load_done(a0.out)
        for extra in filter(None, a0.also_read.split(",")):
            done.update(load_done(extra))
        jobs = jobs_for(phase, ch, done)
        k, nsh = map(int, a0.shard.split("/"))
        jobs = [j for j in jobs if zlib.crc32(repr(j).encode()) % nsh == k]
        print(f"phase {phase}: {len(jobs)} jobs", flush=True)
        st = {"n": 0, "t0": time.time()}

        def work(ij):
            i, (kind, tid, fold) = ij
            task, qsol, qids = build(ch[tid], sol[tid], kind, fold)
            try:
                rec, _ = RB.run_ps(engines[i % len(engines)], tid, task, qsol, 0, a)
            except Exception as e:
                rec = {"error": f"{type(e).__name__}: {e}"}
            rec.update(kind=kind, task_id=tid, fold=fold, query_ids=qids, n_demos=len(ch[tid]["train"]),
                       decoding="greedy", finished_at=time.time())
            with lock:
                with open(a0.out, "a") as f:
                    f.write(json.dumps(rec) + "\n")
                st["n"] += 1
                out, ver, nok = learner_output(rec)
                print(f"[{time.time() - st['t0']:6.0f}s] {kind:4s} {tid} {fold:2d} verified={ver} n_ok={nok} "
                      f"cost={rec.get('cost', 0)} | {st['n']}/{len(jobs)}", flush=True)

        with ThreadPoolExecutor(max_workers=a0.concurrency) as ex:
            list(ex.map(work, enumerate(jobs)))
        print(f"phase {phase} done in {time.time() - st['t0']:.0f}s", flush=True)


if __name__ == "__main__":
    main()
