"""monty-heldout: answers where v5 and FA-LOO + (c) disagree on answering, per dataset and pooled (stratified cluster bootstrap;
pooled is descriptive). usage: python disagree.py"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hl_common import HERE, task_of  # noqa: E402
import numpy as np  # noqa: E402
from stats import load_dataset, load_dev  # noqa: E402

TASKER = {"oned": lambda k: k.split("/")[0]}
out = {}
vecs = {}
for tag in ("concept", "mini", "oned"):
    rows = load_dataset(tag, "base")
    tk = TASKER.get(tag, task_of)
    tasks = sorted({tk(k) for k in rows})
    ix = {t: i for i, t in enumerate(tasks)}
    v = {n: np.zeros(len(tasks)) for n in ("vc", "va", "fc", "fa", "bc", "ba")}
    for k, r in rows.items():
        o = r["cfg"]["full"][str(r["m"] - 1)]
        i = ix[tk(k)]
        if o["v5"] is not None and o["fc"] is None:
            v["va"][i] += 1
            v["vc"][i] += o["v5"]
        if o["fc"] is not None and o["v5"] is None:
            v["fa"][i] += 1
            v["fc"][i] += float(o["fc"])
        if o["fc"] is not None and o["v5"] is not None:
            v["ba"][i] += 1
            v["bc"][i] += float(o["fc"])
    vecs[tag] = v
    out[tag] = {n: float(x.sum()) for n, x in v.items()}
rng = np.random.default_rng(0)
B = 10000
tot = {n: np.zeros(B) for n in ("vc", "va", "fc", "fa")}
per = {}
for tag, v in vecs.items():
    T = len(v["vc"])
    W = rng.multinomial(T, np.full(T, 1 / T), size=B)
    p = {}
    for n in tot:
        b = W @ v[n]
        tot[n] += b
        p[n] = b
    with np.errstate(invalid="ignore", divide="ignore"):
        dd = p["vc"] / p["va"] - p["fc"] / p["fa"]
    dd = dd[~np.isnan(dd)]
    out[tag]["diff_v5only_minus_faonly"] = dict(est=(v["vc"].sum() / v["va"].sum() - v["fc"].sum() / v["fa"].sum()) if v["fa"].sum() and v["va"].sum() else None, ci=[float(np.percentile(dd, 2.5)), float(np.percentile(dd, 97.5))], n_boot=len(dd))
with np.errstate(invalid="ignore", divide="ignore"):
    a_, b_ = tot["vc"] / tot["va"], tot["fc"] / tot["fa"]
s = {n: sum(out[t][n] for t in vecs) for n in ("vc", "va", "fc", "fa", "bc", "ba")}
out["pooled"] = dict(s, v5_only=[float(np.percentile(a_, 2.5)), float(np.percentile(a_, 97.5))], fa_only=[float(np.percentile(b_, 2.5)), float(np.percentile(b_, 97.5))],
                     diff=s["vc"] / s["va"] - s["fc"] / s["fa"], diff_ci=[float(np.percentile(a_ - b_, 2.5)), float(np.percentile(a_ - b_, 97.5))])
json.dump(out, open(os.path.join(HERE, "results", "disagree.json"), "w"), indent=1)
print(json.dumps(out, indent=1))
