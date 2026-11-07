"""monty-heldout: descriptive follow-ups (post hoc, labelled so in the notes). No rule or threshold is changed.
usage: python extras.py TAG -> results/<TAG>_extras.md, results/<TAG>_extras.json"""
import collections
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hl_common import HERE, MODULES, task_of  # noqa: E402
import numpy as np  # noqa: E402
from stats import Data, count_diff, f, fmt, fmtc, fmtd, load_dataset, load_dev, prec, prec_diff  # noqa: E402

TAG = sys.argv[1] if len(sys.argv) > 1 else "concept"
rows = load_dataset(TAG, "base")
TASKER = {"oned": lambda k: k.split("/")[0]}.get(TAG, task_of)
d = Data(rows, tasker=TASKER)
dev = load_dev()
L, J = [], {}
real = lambda k, c="full": rows[k]["cfg"][c][str(rows[k]["m"] - 1)]


def w(s=""):
    L.append(s)


# a. by number of demos
w("**By number of demos, real role (post hoc).**\n")
w("| n demos | Items | Tasks | FA-LOO + (c) | v5 | fit-only | pass@2 | Bound 1/(n+1) |")
w("|---|---|---|---|---|---|---|---|")
J["by_n"] = {}
for n in sorted({rows[k]["m"] - 1 for k in d.keys}):
    keys = [k for k in d.keys if rows[k]["m"] - 1 == n]
    a, b, c = (prec(d, *d.vec("full", f(x), "real", keys)) for x in ("fc", "v5", "fit"))
    p2 = sum(real(k)["p2"] for k in keys)
    J["by_n"][n] = dict(items=len(keys), fc=a, v5=b, fit=c, p2=p2)
    sh = lambda p: f"{p['correct']:.0f}/{p['answered']}"
    w(f"| {n} | {len(keys)} | {len({TASKER(k) for k in keys})} | {sh(a)} | {sh(b)} | {sh(c)} | {p2:.0f} | {1 / (n + 1):.3f} |")

# b. why FA-LOO abstains where v5 answers
w("\n**v5 answers that FA-LOO + (c) does not give (real role), with the reason.**\n")
J["v5_only"] = {}
for k in d.keys:
    o = real(k)
    if o["v5"] is not None and o["fc"] is None:
        J["v5_only"][k] = dict(why=o["why"], ok=o["v5"], n=rows[k]["m"] - 1, mods=o["top_mods"], ev=o["top_ev"])
        w(f"- {k}: {o['why']}, v5 {'right' if o['v5'] >= 1 else 'wrong'}, n = {rows[k]['m'] - 1}, top from {o['top_mods']}")
w("\n**FA-LOO + (c) answers that v5 declines (real role), with the number of fully evidenced distinct answers.**\n")
J["fc_only"] = {}
for k in d.keys:
    o = real(k)
    if o["fc"] is not None and o["v5"] is None:
        J["fc_only"][k] = dict(ok=o["fc"], n_strong=o["n_strong"], ev=o["top_ev"], mods=o["top_mods"], n=rows[k]["m"] - 1)
        w(f"- {k}: FA-LOO {'right' if o['fc'] else 'wrong'}, fully evidenced answers {o['n_strong']}, top evidence {o['top_ev']}, from {o['top_mods']}, n = {rows[k]['m'] - 1}")
both = [(real(k)["v5"], real(k)["fc"]) for k in d.keys if real(k)["v5"] is not None and real(k)["fc"] is not None]
w(f"\nBoth rules answer: {len(both)} items, FA-LOO right {sum(bool(b) for _, b in both)}, v5 right {sum(a >= 1 for a, _ in both)}.")
J["both_rules"] = dict(n=len(both), fc_right=sum(bool(b) for _, b in both), v5_right=sum(a >= 1 for a, _ in both))

# c. module-level: FA-LOO answer set vs evidence >= 0.99 answer set
w("\n**Module alone: FA-LOO + (c) answers vs top answers at evidence >= 0.99 (real role).**\n")
for m in MODULES:
    a = {k for k in d.keys if real(k, f"{m} alone")["fc"] is not None}
    b = {k for k in d.keys if (lambda o: o["top_ev"] is not None and o["top_ev"] >= 0.99)(real(k, f"{m} alone"))}
    w(f"- {m}: {len(a)} and {len(b)}, shared {len(a & b)}")
w("\nSum of the modules' answers at evidence >= 0.99 vs the system's (a portfolio has them equal):")
tot_c = sum(real(k, f"{m} alone")["top_ok"] for m in MODULES for k in d.keys if (lambda o: o["top_ev"] is not None and o["top_ev"] >= 0.99)(real(k, f"{m} alone")))
tot_a = sum(1 for m in MODULES for k in d.keys if (lambda o: o["top_ev"] is not None and o["top_ev"] >= 0.99)(real(k, f"{m} alone")))
w(f"{tot_c:.0f}/{tot_a} summed over modules; " + fmt(prec(d, *d.vec("full", lambda o: o["top_ok"] if (o["top_ev"] is not None and o["top_ev"] >= 0.99) else None))) + " system.")
J["sum_modules_hi"] = dict(correct=tot_c, answered=tot_a)

# d. frames: precision differences (secondary)
w("\n**Frames: paired precision differences at system level (secondary in the plan).**\n")
J["frame_prec"] = {}
for rn, g in (("v5", f("v5")), ("FA-LOO + (c)", f("fc"))):
    for x, y, cx, cy in (("canon", "abs", "sys:canon", "sys:abs"), ("both", "canon", "full", "sys:canon"), ("canon", "global", "sys:canon", "sys:global"), ("both", "no behaviour", "full", "-behavior")):
        r = prec_diff(d, d.vec(cx, g), d.vec(cy, g))
        r2 = prec_diff(d, d.vec(cx, g, "demo"), d.vec(cy, g, "demo")) if rn != "dev" else None
        dv = prec_diff(dev, dev.vec(cx, g), dev.vec(cy, g))
        J["frame_prec"][f"{rn}:{x}-{y}"] = dict(real=r, demo=r2, dev=dv)
        w(f"- {rn}, {x} minus {y}: real {fmtd(r)}; demo {fmtd(r2)}; dev {fmtd(dv)}")

# e. what the arms' solves look like: evidence of the solving answer
w("\n**Evidence of the items solved by behaviour alone, per arm (real role).**\n")
J["arm_evidence"] = {}
for arm, cfg in (("canon", "beh:canon"), ("abs", "beh:abs"), ("both", "behavior alone"), ("global", "beh:global")):
    rows_ = [(k, real(k, cfg)["top_ev"], real(k, cfg)["top_ok"]) for k in d.keys if real(k, cfg)["p2"] > 0]
    J["arm_evidence"][arm] = rows_
    w(f"- {arm}: " + "; ".join(f"{k} ev {e} top {'right' if t else 'wrong'}" for k, e, t in rows_))
w("\n**Evidence of the arms' solves on development data (behaviour alone).**\n")
for arm, cfg in (("canon", "beh:canon"), ("abs", "beh:abs"), ("global", "beh:global")):
    ev = [dev.rows[k]["cfg"][cfg]["0"]["top_ev"] for k in dev.keys if dev.rows[k]["cfg"][cfg]["0"]["p2"] > 0]
    w(f"- {arm}: {len(ev)} solves, evidence >= 0.99 in {sum(e >= .99 for e in ev)}, zero in {sum(e == 0 for e in ev)}")

# f. task-level recount
w("\n**Task-level recount, real role (a task counts once; right = every answered pair right).**\n")
w("| Rule | Tasks answered | Tasks with a wrong answer | Tasks all right | Mean per-task precision |")
w("|---|---|---|---|---|")
J["task_level"] = {}
for rn, fld in (("FA-LOO + (c)", "fc"), ("(a) only", "a"), ("v5", "v5"), ("fit-only", "fit")):
    p = prec(d, *d.vec("full", f(fld)))
    J["task_level"][fld] = p
    w(f"| {rn} | {p['tasks_answered']} | {p['tasks_wrong']} | {p['tasks_answered'] - p['tasks_wrong']} (CP [{100 * p['cp_tasks_all_right'][0]:.0f}, {100 * p['cp_tasks_all_right'][1]:.0f}]%) | {100 * p['task_mean_precision']:.1f}% |")

open(os.path.join(HERE, "results", f"{TAG}_extras.md"), "w").write("\n".join(L) + "\n")
json.dump(J, open(os.path.join(HERE, "results", f"{TAG}_extras.json"), "w"), indent=1, default=float)
print("\n".join(L))
