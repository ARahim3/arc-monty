"""Block until every process of the named sets has been pulled, then print one line. Laptop side, reads raw/ as data.
    python -I -B wait_set.py concept[,mini,...] [stage]"""
import os  # noqa: E402  (release: paths from the repo root)
_REPO = os.environ.get("ARC_MONTY_ROOT", os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")))  # repo root
import glob
import json
import os
import sys
import time

HERE = (_REPO + "/research/icecuber_faloo")
sets = set(sys.argv[1].split(","))
stage = int(sys.argv[2]) if len(sys.argv) > 2 else None
need = set()
for p in ("jobs.jsonl", "jobs_checks.jsonl"):
    with open(os.path.join(HERE, "export", p)) as fh:
        for line in fh:
            j = json.loads(line)
            if j["set"] in sets and (stage is None or j["stage"] == stage):
                for c in (3, 23, 33, 4):
                    need.add((j["rid"], c))
offs = {}
while need:
    for path in glob.glob(os.path.join(HERE, "raw", "runs_*.jsonl")):
        with open(path, errors="replace") as fh:
            fh.seek(offs.get(path, 0))
            while True:
                pos = fh.tell()
                line = fh.readline()
                if not line or not line.endswith("\n"):
                    fh.seek(pos)
                    break
                try:
                    r = json.loads(line)
                    need.discard((r["rid"], int(r["cfg"])))
                except Exception:
                    pass
            offs[path] = fh.tell()
    if need:
        time.sleep(30)
print("all pulled:", sorted(sets), "stage", stage, time.strftime("%H:%M:%S UTC", time.gmtime()))
