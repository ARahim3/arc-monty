#!/usr/bin/env python3
"""VM ONLY, stdlib only: exact-pair and exact-input overlap of the drawn tuples with the repository's published re_arc.zip.
    python gen_overlap.py /mnt/data/gc/re-arc/re_arc.zip /mnt/data/gc/rearc_tasks.jsonl > overlap_rearc_zip.json"""
import json
import sys
import zipfile


def key(g):
    return json.dumps(g, separators=(",", ":"))


def main():
    zp, tasks = sys.argv[1], sys.argv[2]
    z = zipfile.ZipFile(zp)
    names = {n.split("/")[-1][:-5]: n for n in z.namelist() if n.endswith(".json") and "/tasks/" in n}
    out = dict(zip_tasks=len(names), per_task={}, pairs=0, pair_hits=0, input_hits=0, tasks_with_pair_hit=0, tasks_with_input_hit=0)
    for line in open(tasks):
        r = json.loads(line)
        ex = json.loads(z.read(names[r["key"]]))
        P = {(key(e["input"]), key(e["output"])) for e in ex}
        I = {key(e["input"]) for e in ex}
        ph = [i for i, p in enumerate(r["pairs"]) if (key(p["input"]), key(p["output"])) in P]
        ih = [i for i, p in enumerate(r["pairs"]) if key(p["input"]) in I]
        out["pairs"] += len(r["pairs"])
        out["pair_hits"] += len(ph)
        out["input_hits"] += len(ih)
        out["tasks_with_pair_hit"] += bool(ph)
        out["tasks_with_input_hit"] += bool(ih)
        if ph or ih:
            out["per_task"][r["key"]] = dict(pair_positions=ph, input_positions=ih)
    json.dump(out, sys.stdout)


if __name__ == "__main__":
    main()
