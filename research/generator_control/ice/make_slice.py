"""generator_control: remaining (rid, cfg) work for one VM, from what has been pulled to ice/raw/ (as icecuber_faloo/make_slice.py).
    python -I -B research/generator_control/ice/make_slice.py [--stages 0,1]
Writes export/slice.jsonl.gz and export/done.txt. Jobs keep priority order: stage, then run id."""
import os  # noqa: E402  (release: paths from the repo root)
_REPO = os.environ.get("ARC_MONTY_ROOT", os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")))  # repo root
import glob
import gzip
import json
import os
import sys

HERE = (_REPO + "/research/generator_control/ice")
CFGS = (3, 23, 33, 4)


def main():
    args = sys.argv[1:]
    stages = None
    if "--stages" in args:
        stages = {int(x) for x in args[args.index("--stages") + 1].split(",")}
    done = {}
    for path in glob.glob(os.path.join(HERE, "raw", "runs_*.jsonl")):
        with open(path, errors="replace") as fh:
            for line in fh:
                try:
                    r = json.loads(line)
                    done.setdefault(r["rid"], set()).add(int(r["cfg"]))
                except Exception:
                    pass
    jobs = []
    with open(os.path.join(HERE, "export", "jobs.jsonl")) as fh:
        for line in fh:
            j = json.loads(line)
            if (stages is None or j["stage"] in stages) and set(CFGS) - done.get(j["rid"], set()):
                jobs.append(j)
    with gzip.open(os.path.join(HERE, "export", "slice.jsonl.gz"), "wt") as fh:
        for j in jobs:
            fh.write(json.dumps(j, separators=(",", ":")) + "\n")
    with open(os.path.join(HERE, "export", "done.txt"), "w") as fh:
        for j in jobs:
            for c in sorted(done.get(j["rid"], ())):
                fh.write(f"{j['rid']} {c}\n")
    print("remaining runs", len(jobs), "records for", len(done), "runs")


if __name__ == "__main__":
    main()
