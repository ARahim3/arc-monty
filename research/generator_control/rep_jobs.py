"""generator_control replication (Addendum 2): job lists for fresh folds with retries on ARC-AGI-2. Reads JSON only; runs on the Mac.
    python -I -B research/generator_control/rep_jobs.py 0|1|2
rep0: every fold of the tasks where plain sample 1 of stage 1b verified. rep1: first samples that did not fit. rep2: first retries that did not fit.
Writes data/rep<N>.json: [[task id, canonical fold index, attempt], ...]; the fold code is i*100 + attempt. Exits non-zero if the earlier stage is incomplete."""
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


def order(tid):
    return zlib.crc32(f"{FA.GLOBAL_SEED}|order|{tid}".encode())


def verified_tasks():
    d, errs = FA.read_records(FA.STAGE_FILES["1b"])
    assert errs == 0
    ch, _ = FA.load_agi2()
    return sorted((t for t in ch if FA.learner_output(d[("plain", t, 1)])[1]), key=order), ch, d


def rep_records():
    p = os.path.join(HERE, "raw", "gc_qwen_rep.jsonl")
    best = {}
    if os.path.exists(p):
        with open(p, errors="replace") as fh:
            for line in fh:
                try:
                    r = json.loads(line)
                    k = (r["task_id"], r["fold"])
                except Exception:
                    continue
                if "error" not in r and (k not in best or r.get("started_at", 0) < best[k].get("started_at", 0)):
                    best[k] = r
    return best


def main():
    which = int(sys.argv[1])
    tasks, ch, _ = verified_tasks()
    jobs = []
    if which == 0:
        jobs = [[t, i, 0] for t in tasks for i in range(len(ch[t]["train"]))]
    else:
        rec = rep_records()
        prev = json.load(open(os.path.join(HERE, "data", f"rep{which - 1}.json")))
        missing = 0
        for t, i, att in prev:
            r = rec.get((t, i * 100 + att))
            if r is None:
                missing += 1
            elif not FA.learner_output(r)[1]:
                jobs.append([t, i, att + 1])
        if missing:
            print(f"rep{which - 1} incomplete: {missing} missing")
            return 1
    with open(os.path.join(HERE, "data", f"rep{which}.json"), "w") as fh:
        json.dump(jobs, fh)
    print(f"rep{which}:", len(jobs), "jobs on", len({j[0] for j in jobs}), "tasks")
    return 0


if __name__ == "__main__":
    sys.exit(main())
