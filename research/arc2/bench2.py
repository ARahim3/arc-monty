"""ARC-AGI-2 improvement experiments on TPU (public eval, Qwen3.8-27B): reasoning effort and Monty perception notes.

Arms reuse llm/run_bench.py's harnesses unchanged (same prompts, sandbox, feedback, seeds, forcing); only the
chat-template reasoning effort and, for *_hint arms, the PS prompt (Monty perception notes appended) change.
    python research/arc2/bench2.py --arm ps_low_b16384 --url URL[,URL2] --tokenizer DIR --out llm/results
Output: <out>/qwen38_<arm>.jsonl (resumable, one record per sample).
"""
import argparse
import json
import os
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "llm"))
import run_bench as RB                                    # noqa: E402
from arcllm.engine import Engine, is_loop as RB_is_loop   # noqa: E402
from arcllm.tasks import load_eval, ps_messages as PS0   # noqa: E402

HINTS = json.load(open(os.path.join(ROOT, "research/arc2/monty_hints.json")))


def fast_generate(self, prompt_ids, budget, answer_room, seed):
    """Engine.generate without the extra `answer_room` reasoning tokens it samples past the budget (those exist only
    for budget emulation). Same outputs in distribution, ~1/3 fewer tokens per forced round. Mirrors Engine.generate."""
    r = self.complete(prompt_ids, budget, seed)
    if "error" in r:
        return {"error": r["error"], "cost": 0}
    ids, calls, wall = r["ids"], 1, r["wall"]
    gen_tokens = len(ids)
    rec = {"seed": seed}
    if self.end_think in ids:
        p = ids.index(self.end_think)
        answer_ids = ids[p + 1:]
        if r["finish"] == "length":
            c = self.complete(prompt_ids + ids, answer_room, seed + 17)
            calls += 1
            if "error" not in c:
                answer_ids, gen_tokens, wall = answer_ids + c["ids"], gen_tokens + len(c["ids"]), wall + c["wall"]
        rec.update(reasoning_len=p, natural_end=True, forced=False, answer=self.decode(answer_ids),
                   cost=p + 1 + len(answer_ids), reasoning_ids=ids[:p])
    else:
        ans = self.force_answer(prompt_ids, ids, answer_room, seed + 31)
        calls += 1
        gen_tokens += ans.get("n", 0)
        wall += ans.get("wall", 0)
        rec.update(reasoning_len=len(ids), natural_end=False, forced=True, answer=ans.get("text", ""),
                   answer_error=ans.get("error"), cost=len(ids) + len(self.close_ids) + ans.get("n", 0),
                   reasoning_ids=ids)
    rec.update(calls=calls, gen_tokens=gen_tokens, wall=wall, loop=RB_is_loop(self.decode(rec["reasoning_ids"][-4000:])))
    return rec


def hinted_ps_messages(task):
    msgs = PS0(task)
    tid = task.get("_id")
    h = HINTS.get(tid, "")
    if h:
        msgs[1] = dict(msgs[1], content=msgs[1]["content"] + "\n\n" + h)
    return msgs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", required=True, help="<ps|direct>_<xhigh|medium|low>[_hint]_b<budget>[_r<rounds>]")
    ap.add_argument("--url", required=True)
    ap.add_argument("--tokenizer", required=True)
    ap.add_argument("--concurrency", type=int, default=80)
    ap.add_argument("--samples", type=int, default=1)
    ap.add_argument("--sample-from", type=int, default=0, help="first sample index (another VM may run the others)")
    ap.add_argument("--tasks", default="")
    ap.add_argument("--out", default="llm/results")
    ap.add_argument("--slow", action="store_true", help="use Engine.generate as in llm/run_bench.py (samples past the budget)")
    a0 = ap.parse_args()
    m = re.fullmatch(r"(ps|direct)_(xhigh|medium|low)(_hint)?_b(\d+)(?:_r(\d+))?", a0.arm)
    assert m, a0.arm
    harness, effort, hint, budget, rounds = m.group(1), m.group(2), bool(m.group(3)), int(m.group(4)), int(m.group(5) or 2)
    a = argparse.Namespace(model="qwen38", budget=budget, answer_room=8192, rounds=rounds, max_model_len=57344,
                           sandbox_timeout=10.0)
    if hint:
        RB.ps_messages = hinted_ps_messages
    ch, sol = load_eval()
    for k in ch:
        ch[k]["_id"] = k
    ids = sorted(ch)
    if a0.tasks:
        ids = ids[:int(a0.tasks)] if a0.tasks.isdigit() else a0.tasks.split(",")
    if not a0.slow:
        Engine.generate = fast_generate
    urls = a0.url.split(",")
    first = Engine(urls[0], "qwen38", a0.tokenizer, RB.SAMPLING["qwen38"], {"reasoning_effort": effort})
    engines = [first]
    for u in urls[1:]:
        e = Engine.__new__(Engine)
        e.__dict__.update(first.__dict__)
        e.url = u.rstrip("/") + "/completions"
        engines.append(e)
    path = os.path.join(a0.out, f"qwen38_{a0.arm}.jsonl")
    done = set()
    if os.path.exists(path):
        for line in open(path):
            try:
                r = json.loads(line)
                if "error" not in r:
                    done.add((r["task_id"], r["sample"]))
            except Exception:
                pass
    jobs = [(t, k) for k in range(a0.sample_from, a0.sample_from + a0.samples) for t in ids if (t, k) not in done]
    # big prompts last would leave a tail; interleave by prompt size is unnecessary at 80 concurrent
    fn = RB.run_ps if harness == "ps" else RB.run_direct
    lock = threading.Lock()
    st = {"n": 0, "tok": 0, "ok": 0, "t0": time.time()}
    print(f"{a0.arm}: {len(jobs)} jobs ({len(done)} done)", flush=True)

    def work(ij):
        i, (t, k) = ij
        eng = engines[i % len(engines)]
        try:
            rec, _ = fn(eng, t, ch[t], sol[t], k, a)
        except Exception as e:
            import traceback
            rec = {"error": f"{type(e).__name__}: {e}", "tb": traceback.format_exc()[-1500:]}
        rec.update(task_id=t, sample=k, model="qwen38", harness=harness, budget=budget, effort=effort, hint=hint,
                   arm=a0.arm, finished_at=time.time())
        if harness == "direct":
            rec.pop("reasoning_tail", None)
        with lock:
            with open(path, "a") as f:
                f.write(json.dumps(rec) + "\n")
            st["n"] += 1
            st["tok"] += rec.get("gen_tokens", 0)
            ok = any(rec.get("correct") or []) or any(any(r.get("correct") or []) and r.get("verified")
                                                      for r in rec.get("rounds", []))
            st["ok"] += bool(ok)
            el = time.time() - st["t0"]
            print(f"[{el:6.0f}s] {t}#{k} cost {rec.get('cost', 0):6d} {'OK ' if ok else '   '}"
                  f"{'ERR ' + rec['error'][:80] if 'error' in rec else ''}| {st['n']}/{len(jobs)} done, {st['ok']} right, "
                  f"{st['tok'] / max(el, 1):.0f} tok/s", flush=True)

    with ThreadPoolExecutor(max_workers=a0.concurrency) as ex:
        list(ex.map(work, enumerate(jobs)))
    print(f"DONE {a0.arm}: {st['n']} samples, {st['ok']} right, {time.time() - st['t0']:.0f}s", flush=True)


if __name__ == "__main__":
    main()
