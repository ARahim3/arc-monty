"""generator_control: Qwen3.8-27B on the re-arc tasks and the ARC-AGI-2 retry add-on (TPU client). Plan: research/generator_control.md section 0.

The harness is not re-implemented: Pool, run_ps_resumable, Shared, make_args, make_engines, job_k are imported from
research/arc2/faloo_qwen_sampling.py, and the prompts from research/arc2/faloo_qwen.py `build`, all unchanged. New here: where tasks and
results live, the extra job kinds, and the job lists.
    python research/generator_control/qwen_gc.py --url URL1,URL2 --tokenizer DIR --stage main --direction forward --vm NAME
    python research/generator_control/qwen_gc.py --selftest
Stages:
  main    re-arc, 200 tasks: `full` and 3 `fold`s per task, 800 jobs, fixed pseudo-random task order
  rot     re-arc, rotation (labelled added): M_ij for demonstrations i < j, trained on the other demonstration and the test pair, 600 jobs
  retry1  add-on, ARC-AGI-2: first extra sample for each stage-1 fold that did not fit, on tasks whose `full` verified
  retry2  add-on, second extra sample for folds still not fitting after retry1 (job list written by retry_jobs.py)
  cmain, cretry1, cretry2  stage C (Addendum 4): ConceptARC, first test pair only, then retries (job lists written by cretry_jobs.py)
  rep0-2  planned replication of the retry rule on ARC-AGI-2 (Addendum 2): fresh folds and their retries (job lists written by rep_jobs.py)
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
sys.path.insert(0, os.path.join(ROOT, "research", "arc2"))
import faloo_qwen_sampling as F                          # noqa: E402
from faloo_qwen import build, gkey, learner_output       # noqa: E402

RAW = os.path.join(HERE, "raw")
DATA = os.path.join(HERE, "data")
OUT = {"main": os.path.join(RAW, "gc_qwen_main.jsonl"), "rot": os.path.join(RAW, "gc_qwen_rot.jsonl"),
       "retry1": os.path.join(RAW, "gc_qwen_retry.jsonl"), "retry2": os.path.join(RAW, "gc_qwen_retry.jsonl"),
       "rep0": os.path.join(RAW, "gc_qwen_rep.jsonl"), "rep1": os.path.join(RAW, "gc_qwen_rep.jsonl"), "rep2": os.path.join(RAW, "gc_qwen_rep.jsonl"),
       "cmain": os.path.join(RAW, "gc_qwen_c1.jsonl"), "cretry1": os.path.join(RAW, "gc_qwen_c1_retry.jsonl"), "cretry2": os.path.join(RAW, "gc_qwen_c1_retry.jsonl")}
ROT_PAIRS = [(0, 1), (0, 2), (1, 2)]


def load_rearc():
    d = json.load(open(os.path.join(DATA, "rearc_tasks.json")))
    return d["challenges"], d["solutions"]


def load_concept_one():
    """Stage C: ConceptARC with each task's first test pair by file order, so a prompt shows one test input (plus the held-out input in a fold)."""
    ch, sol = F.load_concept()
    return {t: dict(train=c["train"], test=c["test"][:1]) for t, c in ch.items()}, {t: s[:1] for t, s in sol.items()}


def pool_of(task, sol):
    return [dict(input=p["input"], output=p["output"]) for p in task["train"]] + [dict(input=task["test"][0]["input"], output=sol[0])]


def build_rot(task, sol, pair_index):
    """Rotation model M_ij (i < j canonical demonstration indices): trained on the other demonstration and the test pair, queries x_i, x_j.
    Same shape as faloo_qwen.build for a fold: canonical order of demonstrations and queries, no labels in the prompt."""
    assert len(task["test"]) == 1
    demos = sorted(task["train"], key=lambda p: gkey(p["input"]))
    i, j = ROT_PAIRS[pair_index]
    rest = [p for k, p in enumerate(demos) if k not in (i, j)] + [dict(input=task["test"][0]["input"], output=sol[0])]
    rest = sorted(rest, key=lambda p: gkey(p["input"]))
    queries = sorted([("demo:%d" % i, demos[i]["input"], demos[i]["output"]), ("demo:%d" % j, demos[j]["input"], demos[j]["output"])], key=lambda q: gkey(q[1]))
    t = {"train": [{"input": p["input"], "output": p["output"]} for p in rest], "test": [{"input": q[1]} for q in queries]}
    return t, [q[2] for q in queries], [q[0] for q in queries]


def job_list_main(ch):
    return F.job_list(ch, "forward")


def job_list_rot(ch):
    ids = sorted(ch, key=lambda t: zlib.crc32(f"{F.GLOBAL_SEED}|order|{t}".encode()))
    return [("rot", t, k) for t in ids for k in range(3)]


def job_list_retry(stage):
    """retry_jobs.py on the laptop writes data/retry_<stage>.json: [[task id, canonical fold index, attempt], ...]; fold code = i*100 + attempt."""
    kind = "rep" if stage.startswith("rep") and not stage.startswith("retry") else "retry"
    return [(kind, t, i * 100 + att) for t, i, att in json.load(open(os.path.join(DATA, f"{stage}.json")))]


def load_stage(stage):
    if stage in ("main", "rot"):
        return load_rearc()
    if stage.startswith("c"):
        return load_concept_one()
    return F.load_eval()


def jobs_for(stage, ch, direction):
    js = {"main": lambda: job_list_main(ch), "cmain": lambda: job_list_main(ch), "rot": lambda: job_list_rot(ch)}.get(stage, lambda: job_list_retry(stage))()
    return js if direction == "forward" else js[::-1]


def build_job(j, ch, sol):
    kind, tid, fold = j
    if kind == "rot":
        return build_rot(ch[tid], sol[tid], fold)
    if kind in ("retry", "rep"):
        return build(ch[tid], sol[tid], "fold", fold // 100)
    return build(ch[tid], sol[tid], kind, fold)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url")
    ap.add_argument("--tokenizer")
    ap.add_argument("--stage", default="main", choices=list(OUT))
    ap.add_argument("--direction", default="forward", choices=["forward", "backward"])
    ap.add_argument("--vm", default="local")
    ap.add_argument("--k", type=int, default=36)
    ap.add_argument("--gap", type=float, default=20.0)
    ap.add_argument("--selftest", action="store_true")
    a0 = ap.parse_args()
    if a0.selftest:
        selftest()
        return
    a = F.make_args()
    ch, sol = load_stage(a0.stage)
    urls = a0.url.split(",")
    pool = F.Pool(F.make_engines(urls, a0.tokenizer), a0.k, a0.gap)
    out = OUT[a0.stage]
    os.makedirs(RAW, exist_ok=True)
    jobs = jobs_for(a0.stage, ch, a0.direction)
    shared = F.Shared(out, a0.vm)
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
        task, qsol, qids = build_job(j, ch, sol)
        ck = shared.ckpt.get(j)
        started = ck["started_at"] if ck else time.time()
        append(F.claims_path(out, a0.vm), f"{kind} {tid.replace(' ', '_')} {fold} {time.time():.0f} {a0.vm}")

        def on_round(state):
            append(F.ckpt_path(out), json.dumps(dict(kind=kind, task_id=tid, fold=fold, started_at=started, vm=a0.vm, state=state)))

        try:
            rec, _ = F.run_ps_resumable(pool, tid, task, qsol, F.job_k(kind, fold), a, state=(ck or {}).get("state"), on_round=on_round)
        except Exception as e:
            rec = {"error": f"{type(e).__name__}: {e}"}
        rec.update(kind=kind, task_id=tid, fold=fold, query_ids=qids, n_demos=len(ch[tid]["train"]), decoding="sampling",
                   sampling=F.SAMPLING, budget=F.BUDGET, seed_sent=pool.engines[0].use_seed, started_at=started, finished_at=time.time(),
                   vm=a0.vm, resumed_from_round=len(ck["state"]["rounds"]) if ck else 0)
        append(out, json.dumps(rec))
        with lock:
            st["n"] += 1
            st["tok"] += rec.get("gen_tokens", 0)
            if "error" not in rec:
                shared.done[j] = rec
            el = time.time() - st["t0"]
            # no accuracy and no verification status in this log: progress only
            print(f"[{el:6.0f}s] {kind:5s} {tid} {fold:3d} cost={rec.get('cost', 0)} {'ERR ' + rec['error'][:100] if 'error' in rec else ''}"
                  f"| run {st['n']}, done {sum(x in shared.done for x in jobs)}/{len(jobs)}, {st['tok'] / max(el, 1):.0f} tok/s client", flush=True)

    running, futs = set(), {}
    ctl, last_print = "/mnt/data/sampling_k.txt", 0
    with ThreadPoolExecutor(max_workers=len(urls) * 40 + 4) as ex:
        while True:
            shared.refresh()
            if os.path.exists(ctl):
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


def selftest():
    import run_bench as RB
    from arcllm.tasks import ps_messages
    a = F.make_args()
    ch, sol = load_rearc()
    assert len(ch) == 200 and all(len(t["train"]) == 3 and len(t["test"]) == 1 for t in ch.values())
    assert all("output" not in q for t in ch.values() for q in t["test"])
    js = job_list_main(ch)
    assert len(js) == len(set(js)) == 800 and sum(j[0] == "fold" for j in js) == 600
    assert jobs_for("main", ch, "backward") == js[::-1]
    rot = job_list_rot(ch)
    assert len(rot) == len(set(rot)) == 600
    print("main: 800 jobs, 600 folds; rot: 600 jobs; no selection")
    labels = {}
    for kind, tid, fold in js + rot:
        for rnd in range(F.ROUNDS):
            s = RB.seed_of(a.model, "ps", tid, F.job_k(kind, fold), rnd)
            assert s not in labels, (kind, tid, fold, rnd)
            labels[s] = 1
    print(f"seed labels: {len(labels)} distinct")
    leaks = 0
    for tid, t in ch.items():
        demos = sorted(t["train"], key=lambda p: gkey(p["input"]))
        for j in [("full", tid, -1)] + [("fold", tid, i) for i in range(3)] + [("rot", tid, k) for k in range(3)]:
            task, qsol, qids = build_job(j, ch, sol)
            assert all(set(q) == {"input"} for q in task["test"])
            keys = [gkey(q["input"]) for q in task["test"]]
            assert keys == sorted(keys)
            text = ps_messages(task)[1]["content"]
            assert "held" not in text.lower() and "demo:" not in text and "test:" not in text
            assert sum(f"## Test input {q + 1}\n" in text for q in range(len(task["test"]))) == len(task["test"])
            for q, truth in zip(qids, qsol):
                # a query's answer is never in the prompt, unless it equals a shown output by coincidence
                assert (q.startswith("test:") and truth == sol[tid][0]) or (q.startswith("demo:") and truth == demos[int(q[5:])]["output"])
                body = "\n".join("".join(str(v) for v in r) for r in truth)
                gt = lambda g: "\n".join("".join(str(v) for v in r) for r in g)
                grids = [p["input"] for p in task["train"]] + [p["output"] for p in task["train"]] + [x["input"] for x in task["test"]]
                if len(truth) * len(truth[0]) > 4 and body in text and not any(body in gt(g) for g in grids):
                    leaks += 1
            if j[0] == "rot":
                assert len(task["train"]) == 2 and len(task["test"]) == 2 and all(q.startswith("demo:") for q in qids)
            if j[0] == "fold":
                assert len(task["train"]) == 2 and len(task["test"]) == 2 and sorted(q[:4] for q in qids) == ["demo", "test"]
            if j[0] == "full":
                assert len(task["train"]) == 3 and len(task["test"]) == 1
    print("prompts: no labels, canonical order, no query answers;", leaks, "possible coincidences")
    assert leaks == 0
    # the rotation's models are the folds of the other roles: M_ij on the pool equals the fold build when role j is the test
    tid = sorted(ch)[0]
    t, s = ch[tid], sol[tid]
    pool = pool_of(t, s[:1])
    demos = sorted(t["train"], key=lambda p: gkey(p["input"]))
    i, j = ROT_PAIRS[0]
    ta = dict(train=[p for p in pool if p not in (demos[i], demos[j])] + [demos[i]], test=[dict(input=demos[j]["input"])])
    b1, _, _ = build(ta, [demos[j]["output"]], "fold", sorted(ta["train"], key=lambda p: gkey(p["input"])).index(demos[i]))
    b2, _, _ = build_rot(t, s, 0)
    assert b1 == b2
    print("rotation prompt equals faloo_qwen.build with roles swapped")
    # stage C
    ch1, sol1 = load_concept_one()
    full2, _ = F.load_concept()
    js = jobs_for("cmain", ch1, "forward")
    assert len(ch1) == 160 and len(js) == len(set(js)) == 587 and all(len(t["test"]) == 1 and "output" not in t["test"][0] for t in ch1.values())
    for kind, tid, fold in js:
        task, qsol, qids = build_job((kind, tid, fold), ch1, sol1)
        text = ps_messages(task)[1]["content"]
        assert len(task["test"]) == (1 if kind == "full" else 2)
        assert ("## Test input 1\n" in text) and (kind == "full") == ("## Test input 2\n" not in text) and "## Test input 3\n" not in text
        assert task["train"] == build(full2[tid], F.load_concept()[1][tid], kind, fold)[0]["train"] if fold < 1 else True
        assert sorted(q[:4] for q in qids) == (["test"] if kind == "full" else ["demo", "test"])
    print("stage C: 587 jobs, one test input per prompt, plus the held-out input in a fold")
    print("selftest ok")


if __name__ == "__main__":
    main()
