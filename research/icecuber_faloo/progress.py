"""Progress only: counts of finished (rid, cfg) per set and status, from raw/. Shows no accuracy."""
import os  # noqa: E402  (release: paths from the repo root)
_REPO = os.environ.get("ARC_MONTY_ROOT", os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")))  # repo root
import collections
import glob
import json
import os

HERE = (_REPO + "/research/icecuber_faloo")
jobs = collections.Counter()
stage = {}
for p in ("jobs.jsonl", "jobs_checks.jsonl"):
    with open(os.path.join(HERE, "export", p)) as fh:
        for line in fh:
            j = json.loads(line)
            jobs[(j["set"], j["stage"])] += 4
seen, st, cpu = set(), collections.Counter(), collections.Counter()
per = collections.Counter()
for path in glob.glob(os.path.join(HERE, "raw", "runs_*.jsonl")):
    with open(path, errors="replace") as fh:
        for line in fh:
            try:
                r = json.loads(line)
            except Exception:
                continue
            k = (r["rid"], r["cfg"])
            if k in seen:
                continue
            seen.add(k)
            g = (r.get("set"), r.get("stage"))
            per[g] += 1
            st[(r.get("set"), r.get("cfg"), r.get("status"))] += 1
            cpu[g] += float(r.get("cpu") or 0)
for g, n in sorted(jobs.items(), key=str):
    print(g, per[g], "/", n, f"cpu_h {cpu[g] / 3600:.1f}")
print({str(k): v for k, v in sorted(st.items(), key=str) if k[2] != "ok"})
