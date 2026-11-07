"""Derive direct-harness results at smaller thinking budgets from one top-budget run.

For a sample whose natural reasoning fits in B, the answer is the one already generated.
Otherwise the reasoning is cut at B tokens, "\n</think>\n\n" is appended, and the model
writes only the answer (exactly what a server-side thinking budget of B would do, given
the same sampled reasoning prefix).

    python emulate_budgets.py --model qwen38 --tokenizer ... --url ... \
        --src results/qwen38_direct_b65536 --budgets 8192,16384,32768
"""
import argparse
import json
import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from arcllm.tasks import load_eval, parse_grids        # noqa: E402
from run_bench import seed_of, make_engines, repair      # noqa: E402
from arcllm.tasks import direct_messages               # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--tokenizer", required=True)
    ap.add_argument("--url", required=True)
    ap.add_argument("--served-name", default=None)
    ap.add_argument("--src", required=True, help="results/<model>_direct_b<B> (without .jsonl)")
    ap.add_argument("--budgets", default="8192,16384,32768")
    ap.add_argument("--answer-room", type=int, default=8192)
    ap.add_argument("--concurrency", type=int, default=64)
    a = ap.parse_args()

    ch, sol = load_eval()
    engines = make_engines(a)
    eng = engines[0]
    light = {}
    for line in open(a.src + ".jsonl"):
        r = json.loads(line)
        if "error" not in r:
            light[(r["task_id"], r["sample"])] = r
    heavy = {}
    for line in open(a.src + ".ids.jsonl"):
        r = json.loads(line)
        heavy[(r["task_id"], r["sample"])] = r
    out_dir = os.path.dirname(a.src) or "."
    lock = threading.Lock()
    for B in [int(x) for x in a.budgets.split(",")]:
        path = os.path.join(out_dir, f"{a.model}_direct_b{B}.jsonl")
        done = set()
        if os.path.exists(path):
            done = {(json.loads(l)["task_id"], json.loads(l)["sample"]) for l in open(path)}
        jobs = [key for key in light if key not in done and key in heavy]
        print(f"budget {B}: {len(jobs)} samples to derive", flush=True)

        def work(ikey, B=B, path=path):
            i, key = ikey
            t, k = key
            eng = engines[i % len(engines)]
            src, h = light[key], heavy[key]
            rec = {kk: src[kk] for kk in ("task_id", "sample", "model", "prompt_len", "reasoning_len",
                                          "natural_end")}
            rec.update(harness="direct", budget=B, derived_from=src["budget"])
            if src["natural_end"] and src["reasoning_len"] <= B and not src["forced"]:
                rec.update(forced=False, grids=src["grids"], cost=src["cost"],
                           answer_tail=src["answer_tail"])
            else:
                ans = eng.force_answer(h["prompt"], h["reasoning_ids"][:B], a.answer_room,
                                       seed_of(a.model, t, k, "force", B))
                grids = parse_grids(ans.get("text", ""), len(ch[t]["test"]))
                rec.update(forced=True, grids=grids, cost=min(B, src["reasoning_len"]) + len(eng.close_ids) + ans.get("n", 0),
                           answer_tail=ans.get("text", "")[-1200:], answer_error=ans.get("error"))
            rec["correct"] = [x == s for x, s in zip(rec["grids"], sol[t])] if rec["grids"] else None
            if rec["forced"] is False and "grids_repaired" in src:       # reuse the source repair
                rec.update(grids_repaired=src["grids_repaired"], repair_cost=src.get("repair_cost", 0))
            elif not rec["grids"]:
                rep = repair(eng, direct_messages(ch[t]), rec["answer_tail"], ch[t])
                if rep:
                    rec.update(grids_repaired=rep.get("grids"), repair_cost=rep.get("n", 0))
            if "grids_repaired" in rec:
                rg = rec["grids_repaired"]
                rec["correct_repaired"] = [x == s for x, s in zip(rg, sol[t])] if rg else None
            with lock:
                with open(path, "a") as f:
                    f.write(json.dumps(rec) + "\n")

        with ThreadPoolExecutor(max_workers=a.concurrency) as ex:
            list(ex.map(work, enumerate(jobs)))
        print(f"budget {B}: done -> {path}", flush=True)


if __name__ == "__main__":
    main()
