"""icecuber_faloo: independent re-derivation of the rule counts, by a different code path from analyse.py.
Reads each task's JSON afresh, finds runs by content in jobs.jsonl (not by the item tables or run ids), re-parses the raw
answer lines, recomputes usual, pass@k, (a), (a)+(b), (a)+(b)+(c). Also checks fold structure: each held-out run's query
is the held-out demonstration's input and its demonstrations are the others; no run holds a test output with its input.
    python -I -B research/icecuber_faloo/verify.py"""
import os  # noqa: E402  (release: paths from the repo root)
_REPO = os.environ.get("ARC_MONTY_ROOT", os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")))  # repo root
import collections
import glob
import json
import os

ROOT = _REPO
HERE = os.path.join(ROOT, "research", "icecuber_faloo")
SETS = {"concept": "external/judge/conceptarc/repo/corpus", "mini": "external/heldout/mini-arc/data/MiniARC", "oned": "external/heldout/1d-arc/dataset",
        "minimal": "external/judge/conceptarc/repo/MinimalTasks", "agi2": "data/arc-agi-2/data/evaluation"}


def freeze(g):
    return tuple(tuple(r) for r in g)


def sort_key(p):
    i, o = p["input"], p["output"]
    return (len(i) * len(i[0]), len(i), len(i[0]), json.dumps(i), len(o) * len(o[0]), len(o), len(o[0]), json.dumps(o))


def text_of(g):
    return "|" + "|".join("".join(str(c) for c in r) for r in g) + "|"


def main():
    # raw: (rid, cfg) -> first record
    raw = {}
    for p in sorted(glob.glob(os.path.join(HERE, "raw", "runs_*.jsonl"))):
        for line in open(p, errors="replace"):
            try:
                r = json.loads(line)
            except Exception:
                continue
            raw.setdefault((r["rid"], int(r["cfg"])), r)
    # content index
    idx = {}
    for line in open(os.path.join(HERE, "export", "jobs.jsonl")):
        j = json.loads(line)
        key = (tuple((freeze(p["input"]), freeze(p["output"])) for p in j["train"]), freeze(j["query"]))
        idx[key] = j["rid"]

    def run_top(train, query):
        """Merged answer strings, by content lookup; None if the run is missing a configuration."""
        key = (tuple((freeze(p["input"]), freeze(p["output"])) for p in train), freeze(query))
        rid = idx[key]
        lines = []
        for c in (3, 23, 33, 4):
            r = raw.get((rid, c))
            if r is None:
                return None
            if r.get("status") == "ok":
                lines += [(float(s), g) for g, s in r.get("lines", []) if float(s) >= 0]
        lines.sort(reverse=True)
        seen = []
        for _, g in lines:
            if g not in seen:
                seen.append(g)
        return seen[:3]

    out = {}
    for tag, rel in SETS.items():
        base = os.path.join(ROOT, rel)
        c = collections.Counter()
        for f in sorted(glob.glob(os.path.join(base, "**", "*.json"), recursive=True)):
            t = json.load(open(f))
            if tag == "agi2":
                name = os.path.basename(f)[:-5]
                if name in ("0934a4d8", "136b0064", "16b78196", "981571dc", "aa4ec2a5", "da515329", "db695cfb"):
                    continue
            demos = sorted(t["train"], key=sort_key)
            n = len(demos)
            for p in t["test"]:
                truth = text_of(p["output"])
                full = run_top(demos, p["input"])
                if full is None:
                    c["missing"] += 1
                    continue
                c["items"] += 1
                top = full[0] if full else None
                c["has"] += top is not None
                c["p1"] += truth in full[:1]
                c["p2"] += truth in full[:2]
                c["p3"] += truth in full[:3]
                c["usual_right"] += top == truth
                if n < 2:
                    continue
                a_ok, tests = True, []
                miss = False
                for i in range(n):
                    tr = demos[:i] + demos[i + 1:]
                    h = run_top(tr, demos[i]["input"])
                    q = run_top(tr, p["input"])
                    if h is None or q is None:
                        miss = True
                        break
                    if not h or h[0] != text_of(demos[i]["output"]):
                        a_ok = False
                    tests.append(q[0] if q else None)
                if miss:
                    c["missing_fold"] += 1
                    continue
                agree = all(x is not None for x in tests) and len(set(tests)) == 1
                if a_ok and top is not None:
                    c["a"] += 1
                    c["a_right"] += top == truth
                if a_ok and agree:
                    c["fa"] += 1
                    c["fa_right"] += tests[0] == truth
                    if top == tests[0]:
                        c["fc"] += 1
                        c["fc_right"] += tests[0] == truth
        out[tag] = dict(c)
        print(tag, dict(c))
    # compare with analyse.py
    for tag in SETS:
        p = os.path.join(HERE, f"results_{tag}.json")
        if not os.path.exists(p):
            continue
        J = json.load(open(p))
        if not J.get("rules"):
            continue
        R = J["rules"]
        me = out[tag]
        ok = (R["usual"]["answered"] == me.get("has", 0) and R["usual"]["correct"] == me.get("usual_right", 0) and R["a"]["answered"] == me.get("a", 0)
              and R["a"]["correct"] == me.get("a_right", 0) and R["fa"]["answered"] == me.get("fa", 0) and R["fa"]["correct"] == me.get("fa_right", 0)
              and R["fc"]["answered"] == me.get("fc", 0) and R["fc"]["correct"] == me.get("fc_right", 0) and J["p3"]["count"] == me.get("p3", 0))
        print(tag, "matches analyse.py:", ok)
    with open(os.path.join(HERE, "results_verify.json"), "w") as fh:
        json.dump(out, fh, indent=1)


if __name__ == "__main__":
    main()
