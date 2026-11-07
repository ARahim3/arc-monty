"""icecuber_faloo: build run lists and item tables from the JSON sets. Runs on the Mac; reads JSON only.
A *run* is one call of the program: canonical-order demonstrations + ONE query input (no test output ever goes in a run).
Output:
  export/jobs.jsonl          runs to send to the VM: {rid, set, stage, train:[{input,output}], query}. No test outputs.
  export/items_<set>.jsonl   Mac only: {key, cluster, n, full, folds:[{held_rid, test_rid, held_truth}], truth, ...}
The run id is a hash of the canonical demonstrations and the query, so identical runs are done once (fold runs on the
held-out demonstration are shared by all test pairs of a task).
Stage: 0 = full-data runs, 1 = fold runs (a set's stage 0 goes first, so the 249 check comes early)."""
import os  # noqa: E402  (release: paths from the repo root)
_REPO = os.environ.get("ARC_MONTY_ROOT", os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")))  # repo root
import glob
import hashlib
import json
import os
import sys

ROOT = _REPO
HERE = os.path.join(ROOT, "research", "icecuber_faloo")
OUT = os.path.join(HERE, "export")

SETS = [
    ("concept", "external/judge/conceptarc/repo/corpus", "task"),
    ("mini", "external/heldout/mini-arc/data/MiniARC", "task"),
    ("oned", "external/heldout/1d-arc/dataset", "type"),
    ("minimal", "external/judge/conceptarc/repo/MinimalTasks", "task"),
    ("agi2", "data/arc-agi-2/data/evaluation", "task"),
]


def gkey(g):
    """As research/arc2/faloo_qwen.py."""
    return (len(g) * len(g[0]), len(g), len(g[0]), json.dumps(g))


def canon(demos):
    """Total order on demonstrations, so the wrapper is symmetric by construction (ties in input broken by output)."""
    return sorted(demos, key=lambda p: (gkey(p["input"]), gkey(p["output"])))


def rid_of(train, query):
    s = json.dumps([[[p["input"], p["output"]] for p in train], query], separators=(",", ":"))
    return hashlib.sha1(s.encode()).hexdigest()[:20]


def pair_hash(p):
    return hashlib.sha1(json.dumps([p["input"], p["output"]], separators=(",", ":")).encode()).hexdigest()


def agi1_pairs():
    out = set()
    for f in glob.glob(os.path.join(ROOT, "data/arc-agi-1/data/*/*.json")):
        t = json.load(open(f))
        for p in t["train"] + t["test"]:
            if "output" in p:
                out.add(pair_hash(p))
    return out


def agi1_ids():
    return {os.path.basename(f)[:-5] for f in glob.glob(os.path.join(ROOT, "data/arc-agi-1/data/*/*.json"))}


def main():
    os.makedirs(OUT, exist_ok=True)
    jobs = {}
    a1, ids1 = agi1_pairs(), agi1_ids()
    summary = {}
    for tag, rel, cl in SETS:
        base = os.path.join(ROOT, rel)
        items, nf, skipped = [], 0, []
        for f in sorted(glob.glob(os.path.join(base, "**", "*.json"), recursive=True)):
            try:
                t = json.load(open(f))
                [(p["input"], p["output"]) for p in t["train"]]
                tests = [p for p in t["test"]]
            except Exception as e:
                skipped.append((f, repr(e)))
                continue
            if not all("output" in p for p in tests) or not tests:
                skipped.append((f, "no test output"))
                continue
            k = os.path.relpath(f, base)[:-5]
            if tag == "agi2":
                # comparator: only tasks with no id and no exact pair in ARC-AGI-1
                if os.path.basename(k) in ids1 or any(pair_hash(p) in a1 for p in t["train"] + tests):
                    skipped.append((f, "in ARC-AGI-1"))
                    continue
            nf += 1
            demos = canon(t["train"])
            n = len(demos)
            folds_held = []
            for j in range(n):
                tr = demos[:j] + demos[j + 1:]
                folds_held.append(dict(j=j, rid=None if not tr else rid_of(tr, demos[j]["input"]), truth=demos[j]["output"], tr=tr))
            for ti, p in enumerate(tests):
                key = f"{k}#{ti}"
                full = rid_of(demos, p["input"])
                jobs.setdefault(full, dict(rid=full, set=tag, stage=0, train=demos, query=p["input"]))
                folds = []
                for fh in folds_held:
                    if fh["rid"] is None:
                        folds.append(dict(j=fh["j"], held_rid=None, test_rid=None, held_truth=fh["truth"]))
                        continue
                    jobs.setdefault(fh["rid"], dict(rid=fh["rid"], set=tag, stage=1, train=fh["tr"], query=demos[fh["j"]]["input"]))
                    trid = rid_of(fh["tr"], p["input"])
                    jobs.setdefault(trid, dict(rid=trid, set=tag, stage=1, train=fh["tr"], query=p["input"]))
                    folds.append(dict(j=fh["j"], held_rid=fh["rid"], test_rid=trid, held_truth=fh["truth"]))
                cluster = k if cl == "task" else k.split("/")[0]
                items.append(dict(key=key, task=k, cluster=cluster, n=n, full=full, folds=folds, truth=p["output"]))
        with open(os.path.join(OUT, f"items_{tag}.jsonl"), "w") as fh:
            for it in items:
                fh.write(json.dumps(it, separators=(",", ":")) + "\n")
        summary[tag] = dict(tasks=nf, items=len(items), clusters=len({i["cluster"] for i in items}), skipped=len(skipped),
                            skipped_why=sorted({w for _, w in skipped}),
                            n1_items=sum(i["n"] == 1 for i in items), mean_bound=sum(1 / (i["n"] + 1) for i in items) / max(1, len(items)),
                            runs=sum(1 for j in jobs.values() if j["set"] == tag))
    order = {t: i for i, (t, _, _) in enumerate(SETS)}
    with open(os.path.join(OUT, "jobs.jsonl"), "w") as fh:
        for j in sorted(jobs.values(), key=lambda j: (order[j["set"]], j["stage"], j["rid"])):
            fh.write(json.dumps(j, separators=(",", ":")) + "\n")
    print(json.dumps(summary, indent=1))
    print("runs", len(jobs), "bytes", os.path.getsize(os.path.join(OUT, "jobs.jsonl")))


if __name__ == "__main__":
    sys.exit(main())
