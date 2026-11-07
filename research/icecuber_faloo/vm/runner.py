#!/usr/bin/env python3
"""VM side, stdlib only. One record per process (rid, cfg) appended to runs.jsonl, so a preemption loses only what is in flight.
A process = `./run 0 CFG` on a directory holding one task file: the canonical-order demonstrations and one query input with
no output. The program writes output/answer_0_CFG.csv only when it finishes, so a killed process leaves no answer.

  runner.py --jobs jobs.jsonl --out runs.jsonl --cfgs 3,23,33,4 --workers 150 --deep-workers 80 --time 3600 --mem-gb 16 [--done done.txt]

Status: ok (exit 0, answer file read), timeout, mem (killed by RLIMIT_AS: bad_alloc abort), crash (other non-zero exit).
Time limit: wall clock on the process. Memory limit: RLIMIT_AS, per process."""
import argparse
import json
import os
import queue
import shutil
import signal
import subprocess
import threading
import time

BIN = "/mnt/data/ice/build/run"
TMP = "/dev/shm/ice"


def parse_answer_file(path):
    """Text lines: id, then `|123|456| score`. Returned as [[grid-string, score-string]]; validated on the laptop too."""
    out = []
    with open(path) as fh:
        lines = fh.read().strip().split("\n")
    for line in lines[1:]:
        a = line.split()
        if len(a) == 2:
            out.append([a[0], a[1]])
    return out


def run_one(job, cfg, tlimit, mem_bytes, bin_path=BIN):
    d = os.path.join(TMP, f"{job['rid']}_{cfg}_{os.getpid()}_{threading.get_ident()}")
    os.makedirs(os.path.join(d, "dataset", "test"))
    os.makedirs(os.path.join(d, "output"))
    with open(os.path.join(d, "dataset", "test", "aaaaaaaa.json"), "w") as fh:
        json.dump({"train": job["train"], "test": [{"input": job["query"]}]}, fh, separators=(",", ":"))

    t0 = time.time()
    rec = dict(rid=job["rid"], cfg=cfg, set=job.get("set"), stage=job.get("stage"), nd=len(job["train"]))
    kb = mem_bytes // 1024
    # ulimit in a shell, not preexec_fn: this process has many threads.
    cmd = f"ulimit -v {kb}; ulimit -c 0; exec {bin_path} 0 {int(cfg)}"
    with open(os.path.join(d, "err.txt"), "wb") as ferr:
        p = subprocess.Popen(["bash", "-c", cmd], cwd=d, stdout=subprocess.DEVNULL, stderr=ferr, start_new_session=True)
        rc, ru = None, None
        delay = 0.05
        while True:
            pid, st, ru = os.wait4(p.pid, os.WNOHANG)
            if pid:
                rc = os.waitstatus_to_exitcode(st)
                break
            if time.time() - t0 > tlimit:
                try:
                    os.killpg(p.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                _, st, ru = os.wait4(p.pid, 0)
                rc = None
                break
            time.sleep(delay)
            delay = min(delay * 1.5, 2.0)
        p.returncode = 0 if rc is None else rc
    rec["rss_mb"] = int(ru.ru_maxrss / 1024) if ru else None
    rec["cpu"] = round(ru.ru_utime + ru.ru_stime, 2) if ru else None
    rec["secs"] = round(time.time() - t0, 2)
    tail = b""
    try:
        with open(os.path.join(d, "err.txt"), "rb") as fh:
            fh.seek(0, 2)
            fh.seek(max(0, fh.tell() - 400))
            tail = fh.read()
    except OSError:
        pass
    af = os.path.join(d, "output", f"answer_0_{cfg}.csv")
    if rc is None:
        rec["status"] = "timeout"
    elif rc == 0 and os.path.exists(af):
        rec["status"] = "ok"
        rec["lines"] = parse_answer_file(af)
    else:
        rec["status"] = "mem" if (b"bad_alloc" in tail or b"Cannot allocate" in tail) else "crash"
        rec["rc"] = rc
        rec["tail"] = tail[-200:].decode("ascii", "replace")
    shutil.rmtree(d, ignore_errors=True)
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--done", default=None, help="lines 'rid cfg' already pulled to the laptop")
    ap.add_argument("--cfgs", default="3,23,33,4")
    ap.add_argument("--workers", type=int, default=150)
    ap.add_argument("--deep-workers", type=int, default=80)
    ap.add_argument("--time", type=float, default=3600)
    ap.add_argument("--mem-gb", type=float, default=8)
    ap.add_argument("--finished", default=None, help="file touched when the list is exhausted")
    a = ap.parse_args()
    cfgs = [int(x) for x in a.cfgs.split(",")]
    done = set()
    for path in (a.done, a.out):
        if path and os.path.exists(path):
            with open(path) as fh:
                for line in fh:
                    try:
                        if path == a.out:
                            r = json.loads(line)
                            done.add((r["rid"], int(r["cfg"])))
                        else:
                            rid, c = line.split()
                            done.add((rid, int(c)))
                    except Exception:
                        pass
    q, qd = queue.Queue(), queue.Queue()  # shallow, deep (cfg 4): deep has its own worker cap, so memory cannot exceed the host
    n = 0
    with open(a.jobs) as fh:
        jobs = [json.loads(line) for line in fh]
    # order: as listed, each job's shallow configurations first
    for job in jobs:
        for c in cfgs:
            if (job["rid"], c) not in done:
                (qd if c == 4 else q).put((job, c))
                n += 1
    print("to run", n, "processes of", len(jobs) * len(cfgs), flush=True)
    os.makedirs(TMP, exist_ok=True)
    lock = threading.Lock()
    out = open(a.out, "a")
    t0 = time.time()
    cnt = dict(n=0)
    mem = int(a.mem_gb * 2**30)

    def worker(deep):
        while True:
            try:
                job, c = (qd if deep else q).get_nowait()
            except queue.Empty:
                try:
                    job, c = q.get_nowait()
                except queue.Empty:
                    return
            try:
                rec = run_one(job, c, a.time, mem)
            except Exception as e:  # never lose a worker
                rec = dict(rid=job["rid"], cfg=c, set=job.get("set"), stage=job.get("stage"), status="wrapper_error", tail=repr(e)[:200])
            line = json.dumps(rec, separators=(",", ":"))
            with lock:
                out.write(line + "\n")
                out.flush()
                cnt["n"] += 1
                if cnt["n"] % 200 == 0:
                    print(cnt["n"], "/", n, f"{time.time() - t0:.0f}s", flush=True)

    ts = [threading.Thread(target=worker, args=(i < a.deep_workers,), daemon=True) for i in range(a.workers)]
    for t in ts:
        t.start()
    for t in ts:
        t.join()
    out.close()
    print("finished", cnt["n"], f"{time.time() - t0:.0f}s", flush=True)
    if a.finished:
        open(a.finished, "w").close()


if __name__ == "__main__":
    main()
