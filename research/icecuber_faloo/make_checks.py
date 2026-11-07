"""icecuber_faloo: code checks on a fixed random sample of runs (seed 0, drawn from the run list, before any result).
  chk_rep_<rid>  the same run again: is the program deterministic under load, across VMs?
  chk_rev_<rid>  the same demonstrations reversed: does the raw program depend on demonstration order? The wrapper's
                 canonical order makes the learner symmetric whatever this shows.
Neither enters any rule. Output: export/jobs_checks.jsonl, set = 'check'."""
import os  # noqa: E402  (release: paths from the repo root)
_REPO = os.environ.get("ARC_MONTY_ROOT", os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")))  # repo root
import json
import os
import random

HERE = (_REPO + "/research/icecuber_faloo")


def main():
    jobs = [json.loads(line) for line in open(os.path.join(HERE, "export", "jobs.jsonl"))]
    jobs = [j for j in jobs if j["set"] in ("concept", "mini", "oned", "minimal")]
    rng = random.Random(0)
    out = []
    for tag, k in (("concept", 60), ("mini", 30), ("oned", 30), ("minimal", 10)):
        pool = sorted((j for j in jobs if j["set"] == tag and len(j["train"]) >= 2), key=lambda j: j["rid"])
        for j in rng.sample(pool, k):
            out.append(dict(rid="chk_rep_" + j["rid"], set="check", stage=2, orig=j["rid"], train=j["train"], query=j["query"]))
            out.append(dict(rid="chk_rev_" + j["rid"], set="check", stage=2, orig=j["rid"], train=j["train"][::-1], query=j["query"]))
    with open(os.path.join(HERE, "export", "jobs_checks.jsonl"), "w") as fh:
        for j in out:
            fh.write(json.dumps(j, separators=(",", ":")) + "\n")
    print(len(out), "check runs")


if __name__ == "__main__":
    main()
