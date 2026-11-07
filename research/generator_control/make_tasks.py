"""generator_control: validate the JSON drawn on the VM, write ARC-format task files, run the plan's data checks. Stdlib only; treats
the input as untrusted data (nothing from it is executed; every grid is validated).
    python -I -B research/generator_control/make_tasks.py
Reads data/from_vm/rearc_tasks.jsonl; writes data/rearc_tasks.json (challenges and solutions), data/tasks/rearc_<id>.json,
data/checks.json, and prints the checks. Each task file: train = draws 1-3 in draw order, test = draw 4."""
import os  # noqa: E402  (release: paths from the repo root)
_REPO = os.environ.get("ARC_MONTY_ROOT", os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")))  # repo root
import collections
import glob
import hashlib
import json
import os
import sys

ROOT = _REPO
HERE = os.path.join(ROOT, "research", "generator_control")
DATA = os.path.join(HERE, "data")
OTHER = {
    "agi2-train": "data/arc-agi-2/data/training", "agi2-eval": "data/arc-agi-2/data/evaluation",
    "agi1-train": "data/arc-agi-1/data/training", "agi1-eval": "data/arc-agi-1/data/evaluation",
    "conceptarc": "external/judge/conceptarc/repo/corpus", "minimal": "external/judge/conceptarc/repo/MinimalTasks",
    "mini-arc": "external/heldout/mini-arc/data/MiniARC", "1d-arc": "external/heldout/1d-arc/dataset",
}
DEV = ("agi2-train", "agi2-eval", "agi1-train", "agi1-eval")


def valid_grid(g):
    if not isinstance(g, list) or not 0 < len(g) <= 30:
        return False
    w = None
    for row in g:
        if not isinstance(row, list) or not 0 < len(row) <= 30:
            return False
        if w is None:
            w = len(row)
        if len(row) != w or not all(type(c) is int and 0 <= c <= 9 for c in row):
            return False
    return True


def gk(g):
    return json.dumps(g, separators=(",", ":"))


def pairs_in(path):
    """(input, output) keys of every pair with an output, in all JSON files under a folder. Data only."""
    P, I, tasks = set(), set(), 0
    for f in glob.glob(os.path.join(ROOT, path, "**", "*.json"), recursive=True):
        try:
            t = json.load(open(f))
            ps = list(t.get("train", [])) + list(t.get("test", []))
        except Exception:
            continue
        tasks += 1
        for p in ps:
            if "output" in p:
                P.add((gk(p["input"]), gk(p["output"])))
                I.add(gk(p["input"]))
    return P, I, tasks


def main():
    sel = json.load(open(os.path.join(DATA, "selected_generators.json")))
    expect = sel["order"][:200]
    recs = []
    for line in open(os.path.join(DATA, "from_vm", "rearc_tasks.jsonl")):
        recs.append(json.loads(line))
    keys = [r.get("key") for r in recs]
    assert keys == expect, "tasks are not the planned 200 in hash order"
    os.makedirs(os.path.join(DATA, "tasks"), exist_ok=True)
    ch, sol = {}, {}
    area_pos, diff_pos = [[] for _ in range(4)], [[] for _ in range(4)]
    side = collections.Counter()
    stats = collections.Counter()
    dup_out, same_shape = 0, 0
    per_task = {}
    for r in recs:
        k = r["key"]
        assert r["seed"] == sel["seeds"][k], k
        ps = r["pairs"]
        assert isinstance(ps, list) and len(ps) == 4, k
        for p in ps:
            assert set(p) == {"input", "output"}, k
            assert valid_grid(p["input"]) and valid_grid(p["output"]), k
            assert p["input"] != p["output"], k
        inputs = [gk(p["input"]) for p in ps]
        assert len(set(inputs)) == 4, k
        dup_out += len({gk(p["output"]) for p in ps}) < 4
        same_shape += all(len(p["input"]) == len(p["output"]) and len(p["input"][0]) == len(p["output"][0]) for p in ps)
        for i, p in enumerate(ps):
            area_pos[i].append(len(p["input"]) * len(p["input"][0]))
            if r["difficulty"][i] is not None:
                diff_pos[i].append(float(r["difficulty"][i]))
            side[max(len(p["input"]), len(p["input"][0]))] += 1
        for s, v in r["stats"].items():
            stats[s] += int(v)
        tid = f"rearc_{k}"
        train = [dict(input=p["input"], output=p["output"]) for p in ps[:3]]
        test = [dict(input=ps[3]["input"], output=ps[3]["output"])]
        with open(os.path.join(DATA, "tasks", tid + ".json"), "w") as fh:
            json.dump(dict(train=train, test=test), fh, separators=(",", ":"))
        ch[tid] = dict(train=train, test=[dict(input=ps[3]["input"])])
        sol[tid] = [ps[3]["output"]]
        per_task[tid] = dict(calls=r["stats"]["calls"], invalid=r["stats"]["invalid"], tuples_rejected=r["stats"]["tuples_rejected"], secs=r["secs"])
    with open(os.path.join(DATA, "rearc_tasks.json"), "w") as fh:
        json.dump(dict(challenges=ch, solutions=sol), fh, separators=(",", ":"))
    C = dict(tasks=len(recs), pairs=len(recs) * 4, stats=dict(stats), tasks_with_rejected_tuple=sum(v["tuples_rejected"] > 0 for v in per_task.values()),
             tasks_with_repeated_output=dup_out, tasks_all_same_shape=same_shape,
             mean_area_by_position=[round(sum(a) / len(a), 1) for a in area_pos],
             mean_difficulty_by_position=[round(sum(a) / len(a), 3) for a in diff_pos],
             largest_side_hist={str(k): side[k] for k in sorted(side)},
             secs_total=round(sum(v["secs"] for v in per_task.values()), 1))
    # exact overlap
    mine = {tid: [(gk(p["input"]), gk(p["output"])) for p in ch[tid]["train"]] + [(gk(ch[tid]["test"][0]["input"]), gk(sol[tid][0]))] for tid in ch}
    flat = {x for v in mine.values() for x in v}
    C["distinct_pairs"] = len(flat)
    dev_p, dev_i, dev_ids = set(), set(), set()
    ov = {}
    for name, path in OTHER.items():
        P, I, n = pairs_in(path)
        if name in DEV:
            dev_p |= P
            dev_i |= I
            dev_ids |= {os.path.basename(f)[:-5] for f in glob.glob(os.path.join(ROOT, path, "*.json"))}
        ov[name] = dict(files=n, their_pairs=len(P), pairs_shared=len(flat & P), inputs_shared=len({x[0] for x in flat} & I),
                        tasks_with_shared_pair=sorted(t for t, v in mine.items() if any(x in P for x in v)))
    C["overlap"] = ov
    C["dev"] = dict(task_ids=len(dev_ids), distinct_pairs=len(dev_p), pairs_shared=len(flat & dev_p), inputs_shared=len({x[0] for x in flat} & dev_i),
                    tasks_with_shared_pair=sorted(t for t, v in mine.items() if any(x in dev_p for x in v)),
                    test_pair_shared=sorted(t for t, v in mine.items() if v[3] in dev_p),
                    tasks_with_shared_input=sorted(t for t, v in mine.items() if any(x[0] in dev_i for x in v)))
    between = collections.Counter(x for v in mine.values() for x in set(v))
    C["pairs_repeated_between_tasks"] = sum(c > 1 for c in between.values())
    zp = os.path.join(DATA, "from_vm", "overlap_rearc_zip.json")
    if os.path.exists(zp):
        Z = json.load(open(zp))
        C["re_arc_zip"] = {k: Z[k] for k in ("pairs", "pair_hits", "input_hits", "tasks_with_pair_hit", "tasks_with_input_hit", "per_task")}
    sc = os.path.join(DATA, "from_vm", "rearc_tasks.jsonl.summary.json")
    C["generation"] = json.load(open(sc))
    with open(os.path.join(DATA, "checks.json"), "w") as fh:
        json.dump(C, fh, indent=1)
    print(json.dumps(C, indent=1)[:6000])


if __name__ == "__main__":
    sys.exit(main())
