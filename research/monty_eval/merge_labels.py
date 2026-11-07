"""WS4: merge the per-batch failure labels (labels/<batch>.jsonl) into results/labels_merged.json.
A label is kept only from the batch whose .todo lists that task (the labelling agents shared a scratchpad and a few
lines landed in the wrong file); duplicates within a batch keep the last line.
"""
import collections
import glob
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.join(HERE, "labels")
CODES = ["BEHAVIOUR", "COMPOSITION", "CONTEXT", "SYMBOL", "COUNT_RELATION", "GOAL_SEARCH", "GEOMETRY", "NEAR_REACH"]
RANK = {"high": 0, "medium": 1, "low": 2}


def main():
    merged, missing, stray = {}, [], []
    for todo in sorted(glob.glob(os.path.join(LAB, "*.todo"))):
        batch = os.path.basename(todo)[:-5]
        want = [tuple(line.split()) for line in open(todo) if line.strip()]
        got = {}
        path = os.path.join(LAB, f"{batch}.jsonl")
        if os.path.exists(path):
            for line in open(path):
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                key = (r.get("split"), r.get("task"))
                if key in want:
                    got[key] = r
                else:
                    stray.append((batch, key))
        for key in want:
            if key in got:
                r = got[key]
                r["primary"] = (r.get("primary") or "").strip().upper()
                sec = r.get("secondary")
                r["secondary"] = None if sec in (None, "", "null", "None") else str(sec).strip().upper()
                r["batch"] = batch
                merged[key] = r
            else:
                missing.append((batch, key))
    out = {"n": len(merged), "missing": missing, "stray_ignored": stray, "by_split": {}}
    for split in ("agi2-eval", "new233"):
        rows = [r for (s, _), r in merged.items() if s == split]
        prim = collections.Counter(r["primary"] for r in rows)
        anym = collections.Counter(c for r in rows for c in {r["primary"], r["secondary"]} if c)
        conf = collections.Counter(r.get("confidence") for r in rows)
        closest = collections.Counter(r.get("closest_module") for r in rows)
        ex = {}
        for c in CODES:
            cand = sorted([r for r in rows if r["primary"] == c], key=lambda r: (RANK.get(r.get("confidence"), 3), r["task"]))
            ex[c] = [dict(task=r["task"], rule=r["rule"], gap=r["gap"], conf=r.get("confidence"),
                          closest=r.get("closest_module")) for r in cand[:6]]
        out["by_split"][split] = dict(n=len(rows), primary=dict(prim), primary_or_secondary=dict(anym),
                                      confidence=dict(conf), closest_module=dict(closest), examples=ex,
                                      near_reach=[dict(task=r["task"], closest=r.get("closest_module"), gap=r["gap"])
                                                  for r in rows if r["primary"] == "NEAR_REACH"])
        print(split, len(rows), dict(prim.most_common()), "| conf", dict(conf))
    print("missing:", missing, "| stray ignored:", len(stray))
    with open(os.path.join(HERE, "results", "labels_merged.json"), "w") as fh:
        json.dump(dict(out, labels=[r for r in merged.values()]), fh, indent=1)


if __name__ == "__main__":
    main()
