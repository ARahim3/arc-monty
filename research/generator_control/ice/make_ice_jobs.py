"""generator_control: run lists for the 2020 program on the re-arc tasks, using the unchanged canon() and rid_of() of
research/icecuber_faloo/make_jobs.py. Runs on the Mac; reads our own validated task files only.
    python -I -B research/generator_control/ice/make_ice_jobs.py
A run = one call f(S, q), S in canonical order, q one query input. No answer of a query is in a run.
For each task, pool = demonstrations + test pair (4 pairs, role 3 = the real test). For each role r:
  full run: f(pool minus r, x_r); fold i: f(pool minus {i, r}, x_i) and f(pool minus {i, r}, x_r).
Identical runs share a run id, so a task has 4 full runs + 6 x 2 fold runs = 16 calls.
Output ice/export/jobs.jsonl {rid, set, stage, train, query}; stage 0 = real-role full, 1 = real-role folds, 2 = the rest (rotation).
items_rearc.jsonl = the real role, items_rearc_role<r>.jsonl = rotated roles (r = 0, 1, 2), in icecuber_faloo/analyse.py's item format."""
import os  # noqa: E402  (release: paths from the repo root)
_REPO = os.environ.get("ARC_MONTY_ROOT", os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")))  # repo root
import glob
import json
import os
import sys

ROOT = _REPO
HERE = os.path.join(ROOT, "research", "generator_control")
sys.path.insert(0, os.path.join(ROOT, "research", "icecuber_faloo"))
from make_jobs import canon, rid_of  # noqa: E402

OUT = os.path.join(HERE, "ice", "export")


def main():
    os.makedirs(OUT, exist_ok=True)
    jobs = {}
    per_role = {r: [] for r in range(4)}
    for f in sorted(glob.glob(os.path.join(HERE, "data", "tasks", "*.json"))):
        t = json.load(open(f))
        tid = os.path.basename(f)[:-5]
        pool = t["train"] + t["test"]
        assert len(pool) == 4
        for r in range(4):
            stage_full, stage_fold = (0, 1) if r == 3 else (2, 2)
            demos = canon([p for j, p in enumerate(pool) if j != r])
            query = pool[r]["input"]
            full = rid_of(demos, query)
            jobs.setdefault(full, dict(rid=full, set="rearc", stage=stage_full, train=demos, query=query))
            folds = []
            for j in range(3):
                tr = demos[:j] + demos[j + 1:]
                held = rid_of(tr, demos[j]["input"])
                test = rid_of(tr, query)
                # the same two runs serve role r and the role of the held-out pair; keep the earlier stage
                for rid, q in ((held, demos[j]["input"]), (test, query)):
                    if rid not in jobs or jobs[rid]["stage"] > stage_fold:
                        jobs[rid] = dict(rid=rid, set="rearc", stage=stage_fold, train=tr, query=q)
                folds.append(dict(j=j, held_rid=held, test_rid=test, held_truth=demos[j]["output"]))
            per_role[r].append(dict(key=f"{tid}#0", task=tid, cluster=tid, n=3, full=full, folds=folds, truth=pool[r]["output"], role=r))
    with open(os.path.join(OUT, "items_rearc.jsonl"), "w") as fh:
        for it in per_role[3]:
            fh.write(json.dumps(it, separators=(",", ":")) + "\n")
    for r in range(3):
        with open(os.path.join(OUT, f"items_rearc_role{r}.jsonl"), "w") as fh:
            for it in per_role[r]:
                fh.write(json.dumps(it, separators=(",", ":")) + "\n")
    # order: stage, then a fixed hash of the id (rids are content hashes), so a partial stage is an arbitrary subset
    order = sorted(jobs.values(), key=lambda j: (j["stage"], j["rid"]))
    with open(os.path.join(OUT, "jobs.jsonl"), "w") as fh:
        for j in order:
            fh.write(json.dumps(j, separators=(",", ":")) + "\n")
    c = {}
    for j in order:
        c[j["stage"]] = c.get(j["stage"], 0) + 1
    print("runs", len(order), "by stage", c, "tasks", len(per_role[3]), "bytes", os.path.getsize(os.path.join(OUT, "jobs.jsonl")))


if __name__ == "__main__":
    main()
