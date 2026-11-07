"""Development only: exercise S3, E2 and verdict code on relabelled development rows. No test data."""
import json, os, shutil, sys, zlib
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.dirname(HERE))
import analyse as A
from settings import WEAK_GROUPS
DRY = os.path.join(HERE, "dry"); T = os.path.join(HERE, "dry_fake"); os.makedirs(T, exist_ok=True)
GROUPS = list(WEAK_GROUPS) + ["CleanUp", "Copy"]
rows = [json.loads(l) for l in open(os.path.join(DRY, "static_tama.jsonl"))]
mont = {json.loads(l)["task"]: json.loads(l) for l in open(os.path.join(DRY, "monty_tama.jsonl"))}
def rename(k):
    t, i = k.split("#"); return f"{GROUPS[zlib.crc32(t.encode()) % len(GROUPS)]}/{t}#{i}"
for fn in ("static_concept", "library_same", "library_other"):
    with open(os.path.join(T, fn + ".jsonl"), "w") as fh:
        for r in rows:
            fh.write(json.dumps(dict(r, task=rename(r["task"]))) + "\n")
with open(os.path.join(T, "monty_concept.jsonl"), "w") as fh:
    for r in rows:
        fh.write(json.dumps(dict(mont[r["task"]], task=rename(r["task"]))) + "\n")
s3 = A.weak_groups(T); e2 = A.library(T)
print({k: (v if not isinstance(v, dict) else {a: v[a] for a in ("diff", "ci") if a in v}) for k, v in s3.items() if not k.startswith("by")})
print({k: (v if not isinstance(v, dict) else {a: v[a] for a in ("diff", "ci") if a in v}) for k, v in e2.items() if not k.startswith("by")})
d = A.jsonable(json.load(open(os.path.join(DRY, "analysis_dry.json"))))
d["strata"] = dict(hand=d["sets"]["arc-community"], tama=d["sets"]["tama"]); d["S3"] = A.jsonable(s3); d["E2"] = A.jsonable(e2)
print(json.dumps(A.verdicts(d), indent=0))
shutil.rmtree(T)
