"""Post hoc, descriptive, read-only: pass@1, who answers, concentration by type, which column wins, per-game breakdowns.
usage: python -I -B post_hoc.py -> results/post_hoc.json"""
import collections, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import analyse as A, data_sets as DS, static as S
from settings import CONFIGS, FRESH_HAND, SPENT
RES = A.RES
out = {}
clusters = {n: DS.SETS[n][1] for n in DS.SETS}
ALL = set(range(len(CONFIGS)))
for label, names in (("hand", list(FRESH_HAND)), ("tama", ["tama"]), ("pqa", ["pqa"]), ("concept", ["concept"]), ("mini", ["mini"]), ("oned", ["oned"])):
    rows, monty, cluster = A.load_many(names, clusters, RES)
    keys = sorted(rows)
    R = {k: S.rules(rows[k], ALL) for k in keys}
    p1c = sum(bool(R[k]["top_right"]) for k in keys)
    p1m = sum(float(monty[k].get("p1", 0) or 0) for k in keys)
    ans_c = sum(R[k]["top_right"] is not None for k in keys)
    ans_m = sum(bool(monty[k].get("has")) for k in keys)
    d = dict(items=len(keys), pass1_column=p1c, pass1_monty=p1m, answered_column=ans_c, answered_monty=ans_m,
             pass2_column=sum(R[k]["pass2"] for k in keys), pass2_monty=sum(float(monty[k]["p2"]) for k in keys))
    by = collections.Counter(); bm = collections.Counter(); tot = collections.Counter()
    for k in keys:
        by[cluster(k)] += R[k]["pass2"]; bm[cluster(k)] += float(monty[k]["p2"]); tot[cluster(k)] += 1
    d["clusters_with_a_column_solve"] = sum(v > 0 for v in by.values()); d["clusters_with_a_monty_solve"] = sum(v > 0 for v in bm.values()); d["clusters"] = len(tot)
    d["top_clusters_column"] = [(c.split(":", 1)[1], v, tot[c]) for c, v in by.most_common(6)]
    d["top_clusters_monty"] = [(c.split(":", 1)[1], v, tot[c]) for c, v in bm.most_common(6)]
    win = collections.Counter(); first = collections.Counter()
    for k in keys:
        rights = [c for c in rows[k]["full"] if c[3] is not None and c[4]]
        if rights:
            win["reach %d" % CONFIGS[rights[0][0]]["reach"]] += 1
            first[CONFIGS[rights[0][0]]["kind"] + ("/pose" if CONFIGS[rights[0][0]].get("poses") else "")] += 1
    d["first_right_column_by_sensor"] = first.most_common(); d["first_right_column_by_reach"] = win.most_common()
    keep = A.keep_of(("color", "mask"))
    d["pass2_cells_only"] = sum(S.rules(rows[k], keep)["pass2"] for k in keys)
    d["answers_by_ev"] = {b: (sum(1 for k in keys if R[k]["top_ev"] is not None and lo <= R[k]["top_ev"] < hi), sum(bool(R[k]["top_right"]) for k in keys if R[k]["top_ev"] is not None and lo <= R[k]["top_ev"] < hi)) for b, lo, hi in (("1.0", .99, 2), ("(0,1)", 1e-9, .99), ("0", -1, 1e-9))}
    out[label] = d
rows, monty, cluster = A.load_many(["concept"], {"concept": DS.SETS["concept"][1]}, RES)
from settings import WEAK_GROUPS
keep = A.keep_of(("color", "mask"))
out["six groups, cells only"] = sum(S.rules(rows[k], keep)["pass2"] for k in rows if k.split(":", 1)[1].split("/")[0] in WEAK_GROUPS)
g = {}
for k in rows:
    gr = k.split(":", 1)[1].split("/")[0]
    v = g.setdefault(gr, [0.0, 0.0])
    v[0] += S.rules(rows[k], ALL)["pass2"]; v[1] += float(monty[k]["p2"])
out["concept by group: column, Monty-ARC"] = g
json.dump(out, open(os.path.join(RES, "post_hoc.json"), "w"), indent=1, default=float)
print(json.dumps(out, indent=0, default=float)[:6500])
a = json.load(open(os.path.join(RES, "analysis.json")))["games"]
for k in ("M1 motor signal, full minus told nothing", "M2 column minus Monty-ARC columns", "M3 column minus object-relative repeat", "M4b nearest-object frame, population, minus local context", "M5 displacement form, full minus colour-only form", "M6 open-loop rollout minus unchanged frame, horizon 4", "E2 games: library minus alone, all transitions"):
    print(k, {g: (v["n"], v["x"], v["y"]) for g, v in a[k]["per_game"].items()})
