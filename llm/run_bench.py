"""Benchmark one served model on the ARC-AGI-2 public eval with one harness.

    python run_bench.py --model qwen38 --tokenizer /mnt/data/ram/models/qwen38 \
        --url http://127.0.0.1:8001/v1 --harness direct --budget 65536 --out results/

Harnesses
  direct  reason, then write the test grid(s) (2 samples = the 2 attempts).
  ps      reason, then write transform(); it is run on the train pairs in a sandbox; a
          program that reproduces every train output is VERIFIED. A failing program gets
          one feedback round (cell diff) up to --rounds. Attempts = verified outputs by
          vote, then the best unverified ones.

Every finished sample is appended to <out>/<model>_<harness>_b<budget>.jsonl (small, safe to
copy off the VM); reasoning token ids go to the matching .ids.jsonl (VM only, used by
emulate_budgets.py). Re-running skips samples already in the jsonl (spot preemptions).
"""
import argparse
import json
import os
import sys
import threading
import time
import zlib
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from arcllm.engine import Engine                                         # noqa: E402
from arcllm.sandbox import run_program                                   # noqa: E402
from arcllm.tasks import (load_eval, direct_messages, ps_messages, parse_grids,   # noqa: E402
                          extract_code, feedback_text)

SAMPLING = {   # model-card / generation_config recommendations
    "qwen38": {"temperature": 1.0, "top_p": 0.95, "top_k": 20},
    "nanbeige": {"temperature": 0.6, "top_p": 0.95},
}
TEMPLATE_KW = {"qwen38": {"reasoning_effort": "xhigh"}, "nanbeige": {}}


def seed_of(*parts):
    return zlib.crc32("|".join(map(str, parts)).encode()) & 0x7FFFFFFF


def make_engines(a):
    first = Engine(a.url.split(",")[0], a.served_name or a.model, a.tokenizer, SAMPLING[a.model],
                   TEMPLATE_KW[a.model])
    engines = [first]
    for u in a.url.split(",")[1:]:
        e = Engine.__new__(Engine)
        e.__dict__.update(first.__dict__)
        e.url = u.rstrip("/") + "/completions"
        engines.append(e)
    return engines


def run_direct(eng, tid, task, sol, k, a):
    msgs = direct_messages(task)
    prompt = eng.render(msgs)
    g = eng.generate(prompt, a.budget, a.answer_room, seed_of(a.model, tid, k))
    if "error" in g:
        return {"error": g["error"]}, None
    grids = parse_grids(g["answer"], len(task["test"]))
    rep = repair(eng, msgs, g["answer"], task) if not grids else {}
    rec = {"prompt_len": len(prompt), "reasoning_len": g["reasoning_len"], "forced": g["forced"],
           "natural_end": g["natural_end"], "cost": g["cost"], "gen_tokens": g["gen_tokens"],
           "calls": g["calls"], "wall": round(g["wall"], 1), "loop": g["loop"], "grids": grids,
           "correct": [x == s for x, s in zip(grids, sol)] if grids else None,
           "answer_tail": g["answer"][-1200:],
           "reasoning_tail": eng.decode(g["reasoning_ids"][-300:])}
    if rep:
        rg = rep.get("grids")
        rec.update(repair_cost=rep.get("n", 0), grids_repaired=rg,
                   correct_repaired=[x == s for x, s in zip(rg, sol)] if rg else None)
    return rec, {"prompt": prompt, "reasoning_ids": g["reasoning_ids"]}


REPAIR = ("Your final answer does not contain {n} valid grid(s): every row of a grid must have the same "
          "number of digits. The test output must have exactly the size your rule gives. Re-write the "
          "final test output grid(s), each as rows of digits in its own ```grid block, nothing else.")


def repair(eng, msgs, answer, task, max_tokens=4096):
    """One short no-thinking follow-up when no valid grid parsed (e.g. rows of unequal width)."""
    if not answer.strip():
        return {}
    n = len(task["test"])
    conv = msgs + [{"role": "assistant", "content": answer[-6000:]},
                   {"role": "user", "content": REPAIR.format(n=n)}]
    try:
        ids = eng.render(conv, enable_thinking=False)
    except Exception:
        return {}
    c = eng.complete(ids, max_tokens, 0)
    if "error" in c:
        return {}
    text = c["text"].split("</think>")[-1]
    return {"grids": parse_grids(text, n), "n": len(c["ids"])}


def run_ps(eng, tid, task, sol, k, a):
    msgs = ps_messages(task)
    train = task["train"]
    inputs = [p["input"] for p in train] + [t["input"] for t in task["test"]]
    rounds, cost, gen, wall = [], 0, 0, 0.0
    for rnd in range(a.rounds):
        prompt = eng.render(msgs)
        if len(prompt) + a.budget + a.answer_room > a.max_model_len:
            rounds.append({"round": rnd, "skipped": "context"})
            break
        g = eng.generate(prompt, a.budget, a.answer_room, seed_of(a.model, "ps", tid, k, rnd))
        if "error" in g:
            rounds.append({"round": rnd, "error": g["error"][:300]})
            break
        cost += g["cost"]
        gen += g["gen_tokens"]
        wall += g["wall"]
        code = extract_code(g["answer"])
        r = {"round": rnd, "prompt_len": len(prompt), "reasoning_len": g["reasoning_len"],
             "forced": g["forced"], "cost": g["cost"], "loop": g["loop"], "code": code}
        msgs = msgs + [{"role": "assistant", "content": g["answer"][-6000:]}]
        if code is None:
            r["n_ok"] = -1
            rounds.append(r)
            msgs.append({"role": "user", "content": "No ```python block defining transform() was "
                         "found. Give the complete program in ONE ```python code block."})
            continue
        res = run_program(code, inputs, timeout=a.sandbox_timeout)
        tr = [{"ok": "output" in x and x["output"] == p["output"], "output": x.get("output"),
               "error": x.get("error")} for x, p in zip(res[:len(train)], train)]
        test_out = [x.get("output") for x in res[len(train):]]
        r.update(n_ok=sum(t["ok"] for t in tr), n_train=len(train), test_out=test_out,
                 correct=[x == s for x, s in zip(test_out, sol)],
                 verified=all(t["ok"] for t in tr) and all(o is not None for o in test_out))
        rounds.append(r)
        if r["verified"]:
            break
        msgs.append({"role": "user", "content": feedback_text(tr, train)})
    rec = {"rounds": rounds, "cost": cost, "gen_tokens": gen, "wall": round(wall, 1),
           "verified": any(r.get("verified") for r in rounds)}
    if not any("error" not in r and "skipped" not in r for r in rounds):
        rec["error"] = "no successful round: " + str(rounds[-1].get("error", rounds[-1]))[:200]
    return rec, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True, choices=list(SAMPLING))
    ap.add_argument("--tokenizer", required=True)
    ap.add_argument("--url", required=True)
    ap.add_argument("--served-name", default=None)
    ap.add_argument("--harness", choices=["direct", "ps"], default="direct")
    ap.add_argument("--budget", type=int, default=65536, help="thinking-token budget per call")
    ap.add_argument("--answer-room", type=int, default=8192)
    ap.add_argument("--rounds", type=int, default=2, help="ps: generation rounds per sample")
    ap.add_argument("--samples", type=int, default=2)
    ap.add_argument("--concurrency", type=int, default=64)
    ap.add_argument("--max-model-len", type=int, default=98304)
    ap.add_argument("--sandbox-timeout", type=float, default=10.0)
    ap.add_argument("--tasks", default="", help="comma list or N (first N sorted ids)")
    ap.add_argument("--data", default=None)
    ap.add_argument("--out", default="results")
    a = ap.parse_args()

    ch, sol = load_eval(a.data) if a.data else load_eval()
    ids = sorted(ch)
    if a.tasks:
        ids = ids[:int(a.tasks)] if a.tasks.isdigit() else a.tasks.split(",")
    os.makedirs(a.out, exist_ok=True)
    tag = f"{a.model}_{a.harness}_b{a.budget}"
    path = os.path.join(a.out, tag + ".jsonl")
    ids_path = os.path.join(a.out, tag + ".ids.jsonl")
    done = set()
    if os.path.exists(path):
        for line in open(path):
            try:
                r = json.loads(line)
                if "error" not in r:
                    done.add((r["task_id"], r["sample"]))
            except Exception:
                pass
    # --url may list several servers (data parallel): job i goes to server i % n
    engines = make_engines(a)
    # sample-major: every task gets sample 0 before any gets sample 1
    jobs = [(t, k) for k in range(a.samples) for t in ids if (t, k) not in done]
    print(f"{tag}: {len(jobs)} jobs ({len(done)} already done), concurrency {a.concurrency}", flush=True)
    lock = threading.Lock()
    stats = {"tok": 0, "n": 0, "t0": time.time(), "solved": 0}
    fn = run_direct if a.harness == "direct" else run_ps

    def work(ij):
        i, (t, k) = ij
        eng = engines[i % len(engines)]
        try:
            rec, heavy = fn(eng, t, ch[t], sol[t], k, a)
        except Exception as e:
            import traceback
            rec, heavy = {"error": f"{type(e).__name__}: {e}", "tb": traceback.format_exc()[-1500:]}, None
        rec.update(task_id=t, sample=k, model=a.model, harness=a.harness, budget=a.budget,
                   finished_at=time.time())
        with lock:
            with open(path, "a") as f:
                f.write(json.dumps(rec) + "\n")
            if heavy is not None:
                with open(ids_path, "a") as f:
                    f.write(json.dumps(dict(heavy, task_id=t, sample=k)) + "\n")
            stats["tok"] += rec.get("gen_tokens", 0)
            stats["n"] += 1
            ok = any(rec.get("correct") or []) or any(any(r.get("correct") or []) and r.get("verified")
                                                      for r in rec.get("rounds", []))
            stats["solved"] += bool(ok)
            el = time.time() - stats["t0"]
            print(f"[{el:6.0f}s] {t}#{k} cost {rec.get('cost', 0):6d} reas {rec.get('reasoning_len', '-')!s:>6} "
                  f"{'OK ' if ok else '   '}{'ERR ' + rec['error'][:80] if 'error' in rec else ''} | "
                  f"{stats['n']}/{len(jobs)} done, {stats['solved']} right, "
                  f"client-side {stats['tok'] / max(el, 1):.0f} tok/s", flush=True)

    with ThreadPoolExecutor(max_workers=a.concurrency) as ex:
        list(ex.map(work, enumerate(jobs)))
    el = time.time() - stats["t0"]
    print(f"DONE {tag}: {stats['n']} samples, {stats['tok']} tokens in {el:.0f}s "
          f"= {stats['tok'] / max(el, 1):.0f} tok/s; {stats['solved']} samples right", flush=True)


if __name__ == "__main__":
    main()
