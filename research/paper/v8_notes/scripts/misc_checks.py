"""v8 paper: small re-derivations from raw files. Read-only, single process, no solver or model run."""
import os  # noqa: E402  (release: paths from the repo root)
_REPO = os.environ.get("ARC_MONTY_ROOT", os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..")))  # repo root
import collections, json, os, sys, math
from math import comb
ROOT = _REPO
RS = os.path.join(ROOT, "research/paper/review_scratch")
# 1. symmetry: folds whose top answer changes under two random demo orders, and between hash seeds
for name in ("sym_h1", "sym_h2"):
    rows = [json.loads(l) for l in open(os.path.join(RS, name + ".jsonl"))]
    folds = sum(len(r["folds"]) for r in rows)
    diff = sum(any(a != f["base"] for a in f["alts"]) for r in rows for f in r["folds"])
    print(name, "tasks", len(rows), "folds", folds, "folds changed by demo order", diff)
h1 = {json.loads(l)["task"]: json.loads(l) for l in open(os.path.join(RS, "sym_h1.jsonl"))}
h2 = {json.loads(l)["task"]: json.loads(l) for l in open(os.path.join(RS, "sym_h2.jsonl"))}
print("folds differing between hash seeds", sum(f1["base"] != f2["base"] for t in h1 for f1, f2 in zip(h1[t]["folds"], h2[t]["folds"])))
# 2. Clopper-Pearson for 11 of 18
sys.path.insert(0, os.path.join(ROOT, "research/monty_heldout"))
from stats import clopper
print("Clopper-Pearson 11/18", [round(x, 3) for x in clopper(11, 18)], "| 5/5", [round(x, 3) for x in clopper(5, 5)])
# 3. random-5-of-20 chance
print("C(15,5)/C(20,5) =", round(comb(15, 5) / comb(20, 5), 4))
# 4. Qwen table
J = json.load(open(os.path.join(ROOT, "research/arc2/faloo_qwen.json")))
print("faloo_qwen.json keys", list(J)[:30])
rows = json.load(open(os.path.join(RS, "qwen_rows.json")))
V = {t: r for t, r in rows.items() if r["fv"]}
print("greedy verified", len(V), "sum right", sum(r["fc"] for r in V.values()), "certified", sum(r["cert"] for r in V.values()), "certified right", sum(r["fc"] for r in V.values() if r["cert"]),
      "not fully right", sorted(t for t, r in V.items() if r["fc"] < 1), "all rejected", all(not r["cert"] for r in V.values() if r["fc"] < 1))
print("folds on verified: held", sum(r["held"] for r in V.values()), "of", sum(r["n"] for r in V.values()))
print("rerun same on verified", sum(bool(r["rep"]) for r in V.values()), "| certified rerun same", sum(bool(r["rep"]) for r in V.values() if r["cert"]), "of", sum(r["cert"] for r in V.values()), "| uncertified rerun same", sum(bool(r["rep"]) for r in V.values() if not r["cert"]), "of", sum(not r["cert"] for r in V.values()))
print("rerun-agree right", sum(r["fc"] for r in V.values() if r["rep"]), "of", sum(bool(r["rep"]) for r in V.values()))
print("reversed same", sum(bool(r["rev"]) for r in V.values()), "certified", sum(bool(r["rev"]) for r in V.values() if r["cert"]), "uncertified", sum(bool(r["rev"]) for r in V.values() if not r["cert"]))
# stochastic plain samples
plain = collections.defaultdict(list)
for f in ("llm/results/qwen38_ps_b16384.jsonl", "llm/results/qwen38_ps_xhigh_b16384.jsonl"):
    for l in open(os.path.join(ROOT, f)):
        r = json.loads(l)
        if "error" in r:
            continue
        rs = [x for x in r["rounds"] if "n_ok" in x]
        v = [x for x in rs if x.get("verified")]
        if not rs:
            continue
        x = v[0] if v else rs[-1]
        plain[r["task_id"]].append(dict(v=bool(v), o=json.dumps(x.get("test_out")), cor=(sum(x["correct"]) / len(x["correct"])) if x.get("correct") else 0.0))
agree = {}
for t, xs in plain.items():
    v = [x for x in xs if x["v"]]
    c = collections.Counter(x["o"] for x in v)
    if c and c.most_common(1)[0][1] >= 2:
        o = c.most_common(1)[0][0]
        agree[t] = next(x["cor"] for x in v if x["o"] == o)
print("tasks where >=2 stochastic verified samples agree", len(agree), "right", sum(agree.values()), "wrong", sorted(t for t, v in agree.items() if v < 1))
print("those wrong: held-out folds", {t: (rows[t]["held"], rows[t]["n"]) for t in agree if agree[t] < 1})
tot = sum(1 for xs in plain.values() for x in xs if x["v"])
ok = sum(x["cor"] for xs in plain.values() for x in xs if x["v"])
print("plain verified samples", tot, "right", ok, "tasks", len(plain))
# 5. ConceptARC reference columns
C = json.load(open(os.path.join(ROOT, "research/monty_heldout/results/concept_analysis.json")))
print("concept totals", C["concept_groups_total"], "n_mach", C.get("n_mach"), "n_hum", C.get("n_hum"))
six = ["AboveBelow", "Count", "HorizontalVertical", "InsideOutside", "Order", "SameDifferent"]
print("six groups p2", sum(C["concept_groups"][g]["p2"] for g in six), "humans", [round(C["concept_groups"][g]["human"], 3) for g in six], "any candidate", [C["concept_groups"][g]["any_candidate"] for g in six], "kaggle1", [C["concept_groups"][g]["kaggle1"] for g in six])
# 6. CPU ratio
print("CPU folds/pass", (621 + 1866 + 2566 + 956) / (216 + 726 + 1007 + 367), "with (c)", 1 + (621 + 1866 + 2566 + 956) / (216 + 726 + 1007 + 367))
print("save-run check:", open(os.path.join(ROOT, "research/paper/data/monty_v5_kaggle_saverun_check.txt")).read()[:300])
print("merge complementarity:", {k: v for k, v in json.load(open(os.path.join(ROOT, "research/paper/data/complementarity.json"))).items() if not isinstance(v, (list, dict))})
