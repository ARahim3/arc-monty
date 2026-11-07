"""generator_control add-on: job lists for fold retries on ARC-AGI-2 (plan section 0, "Add-on"). Reads JSON only; runs on the Mac.
    python -I -B research/generator_control/retry_jobs.py 1      # data/retry1.json, from stage 1 of faloo_qwen_sampling
    python -I -B research/generator_control/retry_jobs.py 2      # data/retry2.json, from retry1's results
On tasks whose stage-1 full run verified, each fold that did not fit its own n-1 demonstrations (no program counts) gets a new sample; a fold
that still does not fit gets one more. Entries: [task id, canonical fold index, attempt]. Order: the stage's fixed task order."""
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


def stage1():
    done, errs = FA.read_records(FA.STAGE_FILES[1])
    assert errs == 0
    ch, _ = FA.load_agi2()
    tasks = sorted((t for t in ch if FA.learner_output(done[("full", t, -1)])[1]), key=order)
    return done, ch, tasks


def retries():
    p = os.path.join(HERE, "raw", "gc_qwen_retry.jsonl")
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
    which = sys.argv[1]
    done, ch, tasks = stage1()
    print("tasks with a verified full run", len(tasks))
    jobs = []
    if which == "1":
        for t in tasks:
            for i in range(len(ch[t]["train"])):
                if not FA.learner_output(done[("fold", t, i)])[1]:
                    jobs.append([t, i, 1])
    else:
        rec = retries()
        missing = 0
        for t in tasks:
            for i in range(len(ch[t]["train"])):
                if not FA.learner_output(done[("fold", t, i)])[1]:
                    r = rec.get((t, i * 100 + 1))
                    if r is None:
                        missing += 1
                    elif not FA.learner_output(r)[1]:
                        jobs.append([t, i, 2])
        assert missing == 0, ("retry1 incomplete", missing)
    with open(os.path.join(HERE, "data", f"retry{which}.json"), "w") as fh:
        json.dump(jobs, fh)
    print(f"retry{which}:", len(jobs), "jobs on", len({j[0] for j in jobs}), "tasks")


if __name__ == "__main__":
    main()
