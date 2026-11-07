#!/usr/bin/env python3
"""VM ONLY: draws the tuples from re-arc's generators (plan: research/generator_control.md section 0). Never run on the Mac.

    PYTHONHASHSEED=0 python gen_rearc.py --repo /mnt/data/gc/re-arc --sel selected_generators.json --out /mnt/data/gc/rearc_tasks.jsonl

One process per generator, at most --procs at a time. Each process seeds Python's global RNG from the plan's hash, then draws 4 valid
examples; the whole 4-tuple is redrawn if any two inputs are equal (symmetric event, so the tuple stays exchangeable). A valid draw is
re-arc's own filter: is_grid on both grids, verifier(input) == output, input != output. Output: one JSON line per generator, grids as
lists; draws 1-3 are demonstrations, draw 4 is the test, by draw order only."""
import argparse
import json
import multiprocessing as mp
import os
import random
import signal
import sys
import time

CALL_LIMIT = 120
GEN_LIMIT = 1800
MAX_TUPLES = 2000


class CallTimeout(BaseException):
    """BaseException, and the timer re-fires, because generators may hold bare excepts."""


def _alarm(sig, frm):
    raise CallTimeout()


def draw(gen, ver, is_grid, utils, lb, ub, st):
    """One valid example. An invalid or timed-out call is redrawn."""
    while True:
        st["calls"] += 1
        setattr(utils, "rng", [])
        signal.setitimer(signal.ITIMER_REAL, CALL_LIMIT, 5)
        try:
            ex = gen(lb, ub)
            ok = is_grid(ex["input"]) and is_grid(ex["output"]) and ver(ex["input"]) == ex["output"] and ex["input"] != ex["output"]
        except CallTimeout:
            st["call_timeouts"] += 1
            ok = False
        except Exception:
            st["call_errors"] += 1
            ok = False
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
        if ok:
            rng = getattr(utils, "rng")
            return ex, (sum(rng) / len(rng) if rng else None)
        st["invalid"] += 1


def worker(key, seed, repo, lb, ub, out):
    sys.path.insert(0, repo)
    os.chdir(repo)
    t0 = time.time()
    st = dict(calls=0, invalid=0, call_errors=0, call_timeouts=0, tuples_rejected=0)
    import generators
    import utils
    import verifiers
    gen, ver = getattr(generators, f"generate_{key}"), getattr(verifiers, f"verify_{key}")
    signal.signal(signal.SIGALRM, _alarm)
    random.seed(seed)
    for _ in range(MAX_TUPLES):
        tup = [draw(gen, ver, utils.is_grid, utils, lb, ub, st) for _ in range(4)]
        if len({x[0]["input"] for x in tup}) == 4:
            rec = dict(key=key, seed=seed, secs=round(time.time() - t0, 2), stats=st,
                       difficulty=[x[1] for x in tup],
                       pairs=[dict(input=[list(r) for r in x[0]["input"]], output=[list(r) for r in x[0]["output"]]) for x in tup])
            with open(out + f".{key}.tmp", "w") as fh:
                json.dump(rec, fh, separators=(",", ":"))
            os.replace(out + f".{key}.tmp", out + f".{key}.done")
            return
        st["tuples_rejected"] += 1
    with open(out + f".{key}.failed", "w") as fh:
        json.dump(dict(key=key, why="tuples", stats=st), fh)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--sel", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--procs", type=int, default=60)
    a = ap.parse_args()
    assert os.environ.get("PYTHONHASHSEED") == "0"
    sel = json.load(open(a.sel))
    order, seeds, lb, ub, want = sel["order"], sel["seeds"], sel["diff_lb"], sel["diff_ub"], sel["n_sample"]
    sys.path.insert(0, a.repo)
    src = open(os.path.join(a.repo, "generators.py")).read()
    names = {line[len("def generate_"):].split("(")[0] for line in src.splitlines() if line.startswith("def generate_")}
    assert names == set(order), (len(names), len(set(order)))
    print("re-arc generators", len(names), "equal the 400 ARC-AGI-1 training ids", flush=True)
    done, failed, running, nxt = {}, {}, {}, 0
    t0 = time.time()
    ctx = mp.get_context("fork")
    while len(done) < want:
        while len(running) < a.procs and len(done) + len(running) < want and nxt < len(order):
            k = order[nxt]
            nxt += 1
            p = ctx.Process(target=worker, args=(k, seeds[k], a.repo, lb, ub, a.out))
            p.start()
            running[k] = (p, time.time())
        for k, (p, ts) in list(running.items()):
            if p.is_alive() and time.time() - ts < GEN_LIMIT:
                continue
            why = None
            if p.is_alive():
                p.kill()
                why = "generator limit"
            p.join()
            del running[k]
            path = a.out + f".{k}.done"
            if why is None and os.path.exists(path):
                done[k] = json.load(open(path))
            else:
                failed[k] = why or f"exit {p.exitcode}"
                print("failed", k, failed[k], flush=True)
        if len(done) and len(done) % 20 == 0:
            print(f"{len(done)} done, {len(failed)} failed, {len(running)} running, {time.time() - t0:.0f}s", flush=True)
        if not running and nxt >= len(order):
            break
        time.sleep(0.5)
    chosen = [k for k in order if k in done]
    with open(a.out, "w") as fh:
        for k in chosen:
            fh.write(json.dumps(done[k], separators=(",", ":")) + "\n")
    with open(a.out + ".summary.json", "w") as fh:
        json.dump(dict(n=len(chosen), failed=failed, considered=nxt, secs=round(time.time() - t0, 1)), fh)
    print("finished", len(chosen), "failed", failed, f"{time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
