"""icecuber_faloo: split the remaining (rid, cfg) work among VMs, using what has been pulled to raw/.
    python -I -B research/icecuber_faloo/make_slice.py VM1 VM2 ... [--sets concept,mini] [--limit-rows N]
Writes export/slice_<vm>.jsonl (jobs with at least one configuration missing) and export/done_<vm>.txt ('rid cfg' lines).
Jobs keep priority order: set order, then stage. Slices are by position, so every VM works on the top of the list."""
import os  # noqa: E402  (release: paths from the repo root)
_REPO = os.environ.get("ARC_MONTY_ROOT", os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")))  # repo root
import collections
import glob
import json
import os
import sys

HERE = (_REPO + "/research/icecuber_faloo")
CFGS = (3, 23, 33, 4)


def main():
    args = sys.argv[1:]
    sets = None
    if "--sets" in args:
        i = args.index("--sets")
        sets = set(args[i + 1].split(","))
        del args[i:i + 2]
    vms = args
    done = collections.defaultdict(set)
    for path in glob.glob(os.path.join(HERE, "raw", "runs_*.jsonl")):
        with open(path, errors="replace") as fh:
            for line in fh:
                try:
                    r = json.loads(line)
                    done[r["rid"]].add(int(r["cfg"]))
                except Exception:
                    pass
    jobs = []
    src = [os.path.join(HERE, "export", "jobs.jsonl")]
    chk = os.path.join(HERE, "export", "jobs_checks.jsonl")
    if os.path.exists(chk):
        src.append(chk)
    for p in src:
        with open(p) as fh:
            for line in fh:
                j = json.loads(line)
                if sets is not None and j["set"] not in sets:
                    continue
                if set(CFGS) - done.get(j["rid"], set()):
                    jobs.append(j)
    for k, vm in enumerate(vms):
        sl = jobs[k::len(vms)]
        with open(os.path.join(HERE, "export", f"slice_{vm}.jsonl"), "w") as fh:
            for j in sl:
                fh.write(json.dumps(j, separators=(",", ":")) + "\n")
        with open(os.path.join(HERE, "export", f"done_{vm}.txt"), "w") as fh:
            for j in sl:
                for c in sorted(done.get(j["rid"], ())):
                    fh.write(f"{j['rid']} {c}\n")
        print(vm, "jobs", len(sl), dict(collections.Counter(j["set"] for j in sl)))
    print("remaining jobs", len(jobs), "with records for", len(done), "rids")


if __name__ == "__main__":
    main()
