"""generator_control stage C: job lists for fold retries on ConceptARC, first test pair only (Addendum 4). Reads JSON only; runs on the Mac.
    python -I -B research/generator_control/cretry_jobs.py 1|2
Writes data/cretry<N>.json: [[task id, canonical fold index, attempt], ...]. Same rule as retry_jobs.py. Exits non-zero if the earlier stage is incomplete."""
import os  # noqa: E402  (release: paths from the repo root)
_REPO = os.environ.get("ARC_MONTY_ROOT", os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")))  # repo root
import json
import os
import sys
import zlib

ROOT = _REPO
HERE = os.path.join(ROOT, "research", "generator_control")
sys.path.insert(0, os.path.join(ROOT, "research", "arc2"))
import faloo_sampling_analyze as FA  # noqa: E402

MAIN = os.path.join(HERE, "raw", "gc_qwen_c1.jsonl")
RETRY = os.path.join(HERE, "raw", "gc_qwen_c1_retry.jsonl")


def best(path):
    """Earliest-started good record per key."""
    out = {}
    if os.path.exists(path):
        with open(path, errors="replace") as fh:
            for line in fh:
                try:
                    r = json.loads(line)
                    k = (r["kind"], r["task_id"], r["fold"])
                except Exception:
                    continue
                if "error" not in r and (k not in out or r.get("started_at", 0) < out[k].get("started_at", 0)):
                    out[k] = r
    return out


def main():
    which = int(sys.argv[1])
    ch, _ = FA.load_concept()
    done = best(MAIN)
    order = lambda t: zlib.crc32(f"{FA.GLOBAL_SEED}|order|{t}".encode())  # noqa: E731
    missing = sum(("full", t, -1) not in done or any(("fold", t, i) not in done for i in range(len(ch[t]["train"]))) for t in ch)
    if missing:
        print("cmain incomplete:", missing)
        return 1
    tasks = sorted((t for t in ch if FA.learner_output(done[("full", t, -1)])[1]), key=order)
    jobs = []
    if which == 1:
        jobs = [[t, i, 1] for t in tasks for i in range(len(ch[t]["train"])) if not FA.learner_output(done[("fold", t, i)])[1]]
    else:
        rec = best(RETRY)
        for t, i, att in json.load(open(os.path.join(HERE, "data", "cretry1.json"))):
            r = rec.get(("retry", t, i * 100 + att))
            if r is None:
                print("cretry1 incomplete")
                return 1
            if not FA.learner_output(r)[1]:
                jobs.append([t, i, 2])
    with open(os.path.join(HERE, "data", f"cretry{which}.json"), "w") as fh:
        json.dump(jobs, fh)
    print(f"cretry{which}:", len(jobs), "jobs on", len({j[0] for j in jobs}), "tasks; verified tasks", len(tasks))
    return 0


if __name__ == "__main__":
    sys.exit(main())
