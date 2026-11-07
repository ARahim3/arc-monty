"""monty-heldout: precision on development minus precision on each unseen set (independent cluster bootstraps, real role).
Also: is the system's set of confident answers really the union of the modules'? usage: python dev_gap.py -> results/dev_gap.json"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hl_common import HERE, MODULES, task_of  # noqa: E402
import numpy as np  # noqa: E402
from stats import Data, f, load_dataset, load_dev  # noqa: E402

dev = load_dev()
out = {}
for tag in ("concept", "mini", "oned"):
    rows = load_dataset(tag, "base")
    d = Data(rows, tasker={"oned": lambda k: k.split("/")[0]}.get(tag, task_of))
    W2 = np.random.default_rng(1).multinomial(d.T, np.full(d.T, 1 / d.T), size=10000)
    out[tag] = {}
    for fld in ("fc", "a", "v5", "fit"):
        c1, a1 = dev.vec("full", f(fld))
        c2, a2 = d.vec("full", f(fld))
        with np.errstate(invalid="ignore", divide="ignore"):
            diff = (dev.W @ c1) / (dev.W @ a1) - (W2 @ c2) / (W2 @ a2)
        diff = diff[~np.isnan(diff)]
        ci = [float(np.percentile(diff, 2.5)), float(np.percentile(diff, 97.5))]
        out[tag][fld] = dict(diff=float(c1.sum() / a1.sum() - c2.sum() / a2.sum()), ci=ci, separates=bool(ci[0] > 0 or ci[1] < 0))
    # union vs system at evidence >= 0.99
    real = lambda k, c: rows[k]["cfg"][c][str(rows[k]["m"] - 1)]
    hi = lambda o: o["top_ev"] is not None and o["top_ev"] >= 0.99
    sysset = {k for k in rows if hi(real(k, "full"))}
    per = {m: {k for k in rows if hi(real(k, f"{m} alone"))} for m in MODULES}
    union = set().union(*per.values())
    multi = {k for k in union if sum(k in per[m] for m in MODULES) >= 2}
    # does the system's top answer at >= 0.99 equal the answer of a module with evidence >= 0.99?
    same_top = sum(any(hi(real(k, f"{m} alone")) and real(k, f"{m} alone")["top_h"] == real(k, "full")["top_h"] for m in MODULES) for k in sysset)
    nosame = sorted(k for k in sysset if not any(hi(real(k, f"{m} alone")) and real(k, f"{m} alone")["top_h"] == real(k, "full")["top_h"] for m in MODULES))
    out[tag]["portfolio"] = dict(system=len(sysset), sum_modules=sum(len(v) for v in per.values()), union=len(union), in_two_or_more=sorted(multi), system_not_in_union=sorted(sysset - union), union_not_in_system=sorted(union - sysset),
                                 system_top_equals_a_module_top=same_top, system_top_not_from_single_module_at_99=nosame)
json.dump(out, open(os.path.join(HERE, "results", "dev_gap.json"), "w"), indent=1)
for tag, v in out.items():
    print(tag, {k: (round(100 * x["diff"], 1), [round(100 * c, 1) for c in x["ci"]], x["separates"]) for k, x in v.items() if k != "portfolio"})
    print(" ", v["portfolio"])
