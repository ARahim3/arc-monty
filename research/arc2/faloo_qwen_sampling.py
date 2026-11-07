"""FA-LOO on Qwen3.8-27B program synthesis with SAMPLING decoding at the natural budget (TPU client). Plan: faloo_qwen_sampling.md section 0.

Learner A(D): the `ps` harness of llm/run_bench.py, xhigh template, model-card sampling (run_bench.SAMPLING["qwen38"]), 32k thinking
per round, <= 2 rounds, canonical demo and query order (faloo_qwen.build, unchanged), output = first verified program, else the last
round's. Jobs: full = A(D); fold i = A(D minus canonical demo i). Stage 1 = all 120 ARC-AGI-2 public-eval tasks; stage 2 = ConceptARC.

Spot VMs: finished jobs and finished rounds are appended to files that the laptop pulls every few minutes. A restarted client continues
from the pulled files (a job restarts at its first unfinished round). Two VMs share the work through claims pushed by the laptop.
    python research/arc2/faloo_qwen_sampling.py --url URL1,URL2 --tokenizer DIR --stage 1 --direction forward --vm NAME
    python research/arc2/faloo_qwen_sampling.py --selftest
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
import run_bench as RB                                    # noqa: E402
from arcllm.engine import Engine                          # noqa: E402
from arcllm.sandbox import run_program                    # noqa: E402
from arcllm.tasks import extract_code, feedback_text, load_eval, ps_messages    # noqa: E402
from bench2 import fast_generate                          # noqa: E402
from faloo_qwen import build, learner_output              # noqa: E402

GLOBAL_SEED = 20261101
BUDGET, ANSWER_ROOM, ROUNDS, MAX_MODEL_LEN = 32768, 8192, 2, 98304
SAMPLING = RB.SAMPLING["qwen38"]
RES = os.path.join(ROOT, "llm/results")
OUT = {"1": os.path.join(RES, "qwen38_faloo_sampling_b32768.jsonl"),
       "1b": os.path.join(RES, "qwen38_faloo_sampling_plain_b32768.jsonl"),
       "2": os.path.join(RES, "qwen38_faloo_sampling_concept_b32768.jsonl")}
CONCEPT_DIR = os.path.join(ROOT, "external/judge/conceptarc/repo/corpus")


def ckpt_path(out):
    return out.replace(".jsonl", ".ckpt.jsonl")


def remote_path(out):
    return out.replace(".jsonl", ".remote.jsonl")


def claims_path(out, vm):
    return out.replace(".jsonl", f".claims_{vm}.txt")


def remote_claims_path(out):
    return out.replace(".jsonl", ".remote_claims.txt")


def load_concept():
    """ConceptARC corpus (third-party): JSON only. Test outputs go to `sol` and never reach the prompt."""
    import glob
    ch, sol = {}, {}
    for f in sorted(glob.glob(os.path.join(CONCEPT_DIR, "*", "*.json"))):
        d = json.load(open(f))
        tid = os.path.relpath(f, CONCEPT_DIR)[:-5]
        ch[tid] = {"train": [{"input": p["input"], "output": p["output"]} for p in d["train"]],
                   "test": [{"input": p["input"]} for p in d["test"]]}
        sol[tid] = [p["output"] for p in d["test"]]
    return ch, sol


def load_stage(stage):
    return load_concept() if stage == "2" else load_eval()


# ------------------------------------------------------------------------------------------------ jobs and seeds
def job_list(ch, direction="forward"):
    """All jobs, no selection: tasks in a fixed pseudo-random order (from the task id and the global seed, not from contents, so a
    partial stage is a random subset of tasks), each task's full run then its folds. `backward` is the same list reversed."""
    ids = sorted(ch, key=lambda t: zlib.crc32(f"{GLOBAL_SEED}|order|{t}".encode()))
    js = [j for t in ids for j in [("full", t, -1)] + [("fold", t, i) for i in range(len(ch[t]["train"]))]]
    return js if direction == "forward" else js[::-1]


def job_list_plain(ch, direction="forward", samples=(1, 2, 3)):
    """Stage 1b (plan addendum 2): three more plain runs per task, kind `plain`, fold = sample index; stage 1's `full` is sample 0.
    faloo_qwen.build treats `plain` exactly like `full`: all demos, test inputs only. Same fixed task order as job_list."""
    ids = sorted(ch, key=lambda t: zlib.crc32(f"{GLOBAL_SEED}|order|{t}".encode()))
    js = [("plain", t, k) for t in ids for k in samples]
    return js if direction == "forward" else js[::-1]


def job_k(kind, fold):
    """The `k` of run_bench.seed_of: job identity + global seed. seed_of adds model, tid and round. Hash values are independent of
    the grids; an index that depends on canonical order only picks among such values, so seeds stay independent of the data."""
    return f"{GLOBAL_SEED}|{kind}|{fold}"


# ------------------------------------------------------------------------------------------------ the harness
class Pool:
    """Looks like an Engine to the harness; each generate() takes one slot on the least loaded server. Round starts are staggered by
    gap = mean round time / k per server, so that sequences of very different lengths share the KV cache (all at 32k at once does not
    fit). Speed only: nothing here touches a run's distribution."""

    def __init__(self, engines, k, gap):
        self.engines, self.k, self.gap = engines, k, gap
        self.inflight = [0] * len(engines)
        self.last = [0.0] * len(engines)
        self.cv = threading.Condition()
        self.tmean = None

    def render(self, *a, **kw):
        return self.engines[0].render(*a, **kw)

    def generate(self, prompt, budget, room, seed):
        with self.cv:
            while True:
                now = time.time()
                free = [i for i in range(len(self.engines)) if self.inflight[i] < self.k and now - self.last[i] >= self.gap]
                if free:
                    i = min(free, key=lambda j: self.inflight[j])
                    self.inflight[i] += 1
                    self.last[i] = now
                    break
                self.cv.wait(timeout=1.0)
        t0 = time.time()
        try:
            return self.engines[i].generate(prompt, budget, room, seed)
        finally:
            dt = time.time() - t0
            with self.cv:
                self.inflight[i] -= 1
                self.tmean = dt if self.tmean is None else 0.95 * self.tmean + 0.05 * dt
                self.gap = max(4.0, min(40.0, self.tmean / self.k))
                self.cv.notify_all()


def run_ps_resumable(eng, tid, task, sol, k, a, state=None, on_round=None):
    """llm/run_bench.py run_ps, line for line, with two additions: it can start from a saved state (finished rounds + the messages
    they added), and it calls on_round(state) after every round that leads to another round. --selftest checks it against run_ps."""
    msgs = ps_messages(task)
    train = task["train"]
    inputs = [p["input"] for p in train] + [t["input"] for t in task["test"]]
    rounds, cost, gen, wall, added, first = [], 0, 0, 0.0, [], 0
    if state:
        rounds, cost, gen, wall, added = list(state["rounds"]), state["cost"], state["gen"], state["wall"], list(state["added"])
        msgs = msgs + added
        first = len(rounds)
    for rnd in range(first, a.rounds):
        prompt = eng.render(msgs)
        if len(prompt) + a.budget + a.answer_room > a.max_model_len:
            rounds.append({"round": rnd, "skipped": "context"})
            break
        seed = RB.seed_of(a.model, "ps", tid, k, rnd)
        g = eng.generate(prompt, a.budget, a.answer_room, seed)
        if "error" in g:
            rounds.append({"round": rnd, "error": g["error"][:300]})
            break
        cost += g["cost"]
        gen += g["gen_tokens"]
        wall += g["wall"]
        code = extract_code(g["answer"])
        r = {"round": rnd, "prompt_len": len(prompt), "reasoning_len": g["reasoning_len"],
             "forced": g["forced"], "cost": g["cost"], "loop": g["loop"], "code": code, "seed": seed}
        new = [{"role": "assistant", "content": g["answer"][-6000:]}]
        if code is None:
            r["n_ok"] = -1
            rounds.append(r)
            new.append({"role": "user", "content": "No ```python block defining transform() was "
                        "found. Give the complete program in ONE ```python code block."})
            msgs = msgs + new
            added = added + new
            if on_round and rnd + 1 < a.rounds:
                on_round(dict(rounds=rounds, cost=cost, gen=gen, wall=wall, added=added))
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
        new.append({"role": "user", "content": feedback_text(tr, train)})
        msgs = msgs + new
        added = added + new
        if on_round and rnd + 1 < a.rounds:
            on_round(dict(rounds=rounds, cost=cost, gen=gen, wall=wall, added=added))
    rec = {"rounds": rounds, "cost": cost, "gen_tokens": gen, "wall": round(wall, 1),
           "verified": any(r.get("verified") for r in rounds)}
    if not any("error" not in r and "skipped" not in r for r in rounds):
        rec["error"] = "no successful round: " + str(rounds[-1].get("error", rounds[-1]))[:200]
    return rec, None


# ------------------------------------------------------------------------------------------------ files
def key_of(r):
    return (r["kind"], r["task_id"], r["fold"])


def read_jsonl_good(path, into):
    """Keep the earliest-started good record per key (an outcome-independent rule; never 'first to finish')."""
    if not os.path.exists(path):
        return
    for line in open(path):
        try:
            r = json.loads(line)
        except Exception:
            continue
        if "error" in r:
            continue
        k = key_of(r)
        if k not in into or r.get("started_at", 0) < into[k].get("started_at", 0):
            into[k] = r


class Shared:
    """Local view of what is done, what is checkpointed and what other live VMs have claimed."""

    def __init__(self, out, vm):
        self.out, self.vm = out, vm
        self.done, self.ckpt, self.claims = {}, {}, {}
        self.mt = {}
        read_jsonl_good(out, self.done)
        read_jsonl_good(ckpt_path(out), self.ckpt)
        self.refresh()

    def _changed(self, p):
        try:
            m = os.path.getmtime(p)
        except OSError:
            return False
        if self.mt.get(p) == m:
            return False
        self.mt[p] = m
        return True

    def refresh(self):
        rp = remote_path(self.out)
        if self._changed(rp):
            read_jsonl_good(rp, self.done)
        cp = remote_path(ckpt_path(self.out))
        if self._changed(cp):
            read_jsonl_good(cp, self.ckpt)
        cl = remote_claims_path(self.out)
        if self._changed(cl):
            claims = {}
            for line in open(cl):
                p = line.split()
                if len(p) == 5:
                    claims[(p[0], p[1], int(p[2]))] = (float(p[3]), p[4])
            self.claims = claims

    def claimed_elsewhere(self, j, ttl=3600):
        c = self.claims.get(j)
        return bool(c and c[1] != self.vm and time.time() - c[0] < ttl)


# ------------------------------------------------------------------------------------------------ main
def make_args():
    return argparse.Namespace(model="qwen38", budget=BUDGET, answer_room=ANSWER_ROOM, rounds=ROUNDS, max_model_len=MAX_MODEL_LEN,
                              sandbox_timeout=10.0)


def make_engines(urls, tokenizer):
    Engine.generate = fast_generate
    first = Engine(urls[0], "qwen38", tokenizer, SAMPLING, {"reasoning_effort": "xhigh"})
    engines = [first]
    for u in urls[1:]:
        e = Engine.__new__(Engine)
        e.__dict__.update(first.__dict__)
        e.url = u.rstrip("/") + "/completions"
        engines.append(e)
    return engines


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url")
    ap.add_argument("--tokenizer")
    ap.add_argument("--stage", default="1", choices=["1", "1b", "2"])
    ap.add_argument("--direction", default="forward", choices=["forward", "backward"])
    ap.add_argument("--vm", default="local")
    ap.add_argument("--k", type=int, default=36, help="rounds in flight per server")
    ap.add_argument("--gap", type=float, default=20.0, help="first gap between round starts per server, then mean round time / k")
    ap.add_argument("--selftest", action="store_true")
    a0 = ap.parse_args()
    if a0.selftest:
        selftest()
        return
    a = make_args()
    ch, sol = load_stage(a0.stage)
    urls = a0.url.split(",")
    pool = Pool(make_engines(urls, a0.tokenizer), a0.k, a0.gap)
    out = OUT[a0.stage]
    jobs = job_list_plain(ch, a0.direction) if a0.stage == "1b" else job_list(ch, a0.direction)
    shared = Shared(out, a0.vm)
    lock = threading.Lock()
    st = {"n": 0, "t0": time.time(), "tok": 0}
    attempts = {}
    print(f"stage {a0.stage} vm {a0.vm}: {len(jobs)} jobs, {sum(j in shared.done for j in jobs)} done, {len(shared.ckpt)} checkpoints; "
          f"seed sent={pool.engines[0].use_seed}; k={a0.k} gap={a0.gap}", flush=True)

    def append(path, line):
        with lock:
            with open(path, "a") as f:
                f.write(line + "\n")

    def work(j):
        kind, tid, fold = j
        task, qsol, qids = build(ch[tid], sol[tid], kind, fold)
        ck = shared.ckpt.get(j)
        started = ck["started_at"] if ck else time.time()
        append(claims_path(out, a0.vm), f"{kind} {tid.replace(' ', '_')} {fold} {time.time():.0f} {a0.vm}")

        def on_round(state):
            append(ckpt_path(out), json.dumps(dict(kind=kind, task_id=tid, fold=fold, started_at=started, vm=a0.vm, state=state)))

        try:
            rec, _ = run_ps_resumable(pool, tid, task, qsol, job_k(kind, fold), a, state=(ck or {}).get("state"), on_round=on_round)
        except Exception as e:
            rec = {"error": f"{type(e).__name__}: {e}"}
        rec.update(kind=kind, task_id=tid, fold=fold, query_ids=qids, n_demos=len(ch[tid]["train"]), decoding="sampling",
                   sampling=SAMPLING, budget=BUDGET, seed_sent=pool.engines[0].use_seed, started_at=started, finished_at=time.time(),
                   vm=a0.vm, resumed_from_round=len(ck["state"]["rounds"]) if ck else 0)
        append(out, json.dumps(rec))
        with lock:
            st["n"] += 1
            st["tok"] += rec.get("gen_tokens", 0)
            if "error" not in rec:
                shared.done[j] = rec
            o, ver, nok = learner_output(rec)
            el = time.time() - st["t0"]
            print(f"[{el:6.0f}s] {kind:4s} {tid} {fold:2d} verified={ver} n_ok={nok} cost={rec.get('cost', 0)} "
                  f"{'ERR ' + rec['error'][:100] if 'error' in rec else ''}| run {st['n']}, done {sum(x in shared.done for x in jobs)}/{len(jobs)}, "
                  f"{st['tok'] / max(el, 1):.0f} tok/s client", flush=True)

    running, futs = set(), {}
    ctl, last_print = "/mnt/data/sampling_k.txt", 0
    with ThreadPoolExecutor(max_workers=len(urls) * 40 + 4) as ex:
        while True:
            shared.refresh()
            if os.path.exists(ctl):                     # optional live tuning of the in-flight cap (<= SEQS); speed only
                try:
                    pool.k = min(40, max(1, int(open(ctl).read().strip())))
                except Exception:
                    pass
            if time.time() - last_print > 300:
                last_print = time.time()
                print(f"# inflight={pool.inflight} k={pool.k} gap={pool.gap:.1f}s mean_round={pool.tmean}s running_jobs={len(running)}", flush=True)
            for j, f in list(futs.items()):
                if f.done():
                    running.discard(j)
                    futs.pop(j)
                    attempts[j] = attempts.get(j, 0) + 1
                    if j not in shared.done and attempts[j] >= 3:
                        print(f"giving up on {j} in this client after 3 errors", flush=True)
            remaining = [j for j in jobs if j not in shared.done]
            if not remaining and not running:
                break
            candidates = [j for j in remaining if j not in running and attempts.get(j, 0) < 3 and not shared.claimed_elsewhere(j)]
            if not candidates and not running and all(attempts.get(j, 0) >= 3 for j in remaining):
                print("only failing jobs are left; exiting", flush=True)
                break
            for j in candidates[:max(0, len(urls) * pool.k + 2 - len(running))]:
                running.add(j)
                futs[j] = ex.submit(work, j)
            time.sleep(2)
    print(f"stage {a0.stage} finished on {a0.vm} in {time.time() - st['t0']:.0f}s, {st['n']} jobs run here, {st['tok']} tokens", flush=True)


# ------------------------------------------------------------------------------------------------ tests (no server needed)
class FakeEngine:
    """Deterministic stand-in: answer depends only on the prompt and the seed, so run_ps and run_ps_resumable must match."""

    def __init__(self):
        self.prompts = []

    def render(self, msgs, **kw):
        s = json.dumps(msgs)
        self.prompts.append(s)
        return [ord(c) for c in s]

    def generate(self, prompt, budget, room, seed):
        n = sum(1 for x in prompt if x == ord("#"))
        code = "def transform(grid):\n    return [list(r) for r in grid]\n" if seed % 3 else "def transform(grid):\n    return [[1]]\n"
        ans = f"thinking {n} {seed}\n```python\n{code}```\n"
        return dict(answer=ans, cost=100 + seed % 7, gen_tokens=100 + seed % 7, wall=1.0, reasoning_len=90, forced=True, loop=False, seed=seed)


def selftest():
    a = make_args()
    ch, sol = load_eval()
    ch2, sol2 = load_concept()
    assert len(ch) == 120 and len(ch2) == 160 and sum(len(v) for v in sol2.values()) == 480
    assert all("output" not in q for t in ch2.values() for q in t["test"])
    # 1. seeds differ between jobs and rounds, and do not depend on the grids
    all_seeds = {}
    for c in (ch, ch2):
        for kind, tid, fold in job_list(c):
            for rnd in range(ROUNDS):
                s = RB.seed_of(a.model, "ps", tid, job_k(kind, fold), rnd)
                assert s not in all_seeds, ("seed collision", kind, tid, fold, rnd, all_seeds[s])
                all_seeds[s] = (kind, tid, fold, rnd)
    print(f"seeds: {len(all_seeds)} distinct over all stage 1 and 2 job rounds")
    # 2. job lists: no selection; every task has one full run and all folds
    for c, name in ((ch, "stage 1"), (ch2, "stage 2")):
        js = job_list(c)
        assert len(js) == len(set(js)) == sum(1 + len(t["train"]) for t in c.values())
        assert job_list(c, "backward") == js[::-1]
        print(f"{name}: {len(c)} tasks, {len(js)} jobs ({sum(j[0] == 'fold' for j in js)} folds)")
    # 2b. stage 1b: plain == full in prompt and query order; seeds labels still distinct
    js = job_list_plain(ch)
    assert len(js) == len(set(js)) == 360
    for kind, tid, k in js:
        assert build(ch[tid], sol[tid], kind, k) == build(ch[tid], sol[tid], "full", -1)
    lab = {RB.seed_of(a.model, "ps", t, job_k(kd, f), r) for kd, t, f in js for r in range(ROUNDS)}
    assert len(lab) == 720 and not (lab & set(all_seeds))
    print("stage 1b: 360 jobs, prompts identical to the full run, seed labels distinct")
    # 3. the prompt cannot tell the held-out demo from a test input, and test outputs never reach it
    leaks = 0
    for c, s in ((ch, sol), (ch2, sol2)):
        for tid, t in c.items():
            demos = sorted(t["train"], key=lambda p: (len(p["input"]) * len(p["input"][0]), len(p["input"]), len(p["input"][0]), json.dumps(p["input"])))
            for i in range(len(demos)):
                task, qsol, qids = build(t, s[tid], "fold", i)
                # every query is a bare input with no other field, and in canonical order
                assert all(set(q) == {"input"} for q in task["test"])
                keys = [(len(q["input"]) * len(q["input"][0]), len(q["input"]), len(q["input"][0]), json.dumps(q["input"])) for q in task["test"]]
                assert keys == sorted(keys)
                # relabelling: replacing the held-out demo's query id changes nothing in the prompt, because the prompt has only inputs
                text = ps_messages(task)[1]["content"]
                assert "held" not in text.lower() and "demo:" not in text and "test:" not in text
                assert sum(f"## Test input {q + 1}\n" in text for q in range(len(task["test"]))) == len(task["test"])
                assert len(task["train"]) == len(demos) - 1 and all(p is not demos[i] for p in task["train"])
                # the held-out output is not in the prompt unless it also occurs elsewhere by coincidence
                out_text = "\n".join("".join(str(v) for v in r) for r in demos[i]["output"])
                others = [p for j, p in enumerate(demos) if j != i]
                if out_text in text and not any(out_text in "\n".join("".join(str(v) for v in r) for r in g) for p in others for g in (p["input"], p["output"])) \
                        and not any(out_text in "\n".join("".join(str(v) for v in r) for r in q["input"]) for q in task["test"]):
                    leaks += 1
                for tt in s[tid]:
                    tt_text = "\n".join("".join(str(v) for v in r) for r in tt)
                    if len(tt) > 3 and tt_text in text and not any(tt_text in "\n".join("".join(str(v) for v in r) for r in g) for p in others for g in (p["input"], p["output"])) \
                            and not any(tt_text in "\n".join("".join(str(v) for v in r) for r in q["input"]) for q in task["test"]):
                        leaks += 1
    assert leaks == 0, leaks
    print("prompts: no labels, canonical order, no outputs of the held-out demo or test pairs")
    # 4. the resumable harness equals run_ps; a resume gives the same record
    n_eq = 0
    for tid in sorted(ch)[:40]:
        task, qsol, qids = build(ch[tid], sol[tid], "fold", 0)
        k = job_k("fold", 0)
        r1, _ = RB.run_ps(FakeEngine(), tid, task, qsol, k, a)
        saved = []
        r2, _ = run_ps_resumable(FakeEngine(), tid, task, qsol, k, a, on_round=lambda st: saved.append(json.loads(json.dumps(st))))
        for x in r2["rounds"]:
            x.pop("seed")
        assert r1 == r2, (r1, r2)
        if saved:
            r3, _ = run_ps_resumable(FakeEngine(), tid, task, qsol, k, a, state=saved[0])
            for x in r3["rounds"]:
                x.pop("seed", None)
            assert r3 == r2, (r3, r2)
        n_eq += 1
    print(f"harness: run_ps_resumable == run_ps on {n_eq} fake tasks, and resuming after round 0 gives the same record")
    print("selftest ok")


if __name__ == "__main__":
    main()
