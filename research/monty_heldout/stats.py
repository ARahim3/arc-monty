"""monty-heldout: cluster bootstrap by task over per-item outcomes. All CIs are percentile, 10,000 resamples, seed 0."""
import collections
import json
import os
import sys

import numpy as np
from scipy import stats as st

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hl_common import HERE, task_of  # noqa: E402

B = 10000


class Data:
    """rows: key -> {m, cfg: {name: {str(role): outcome}}}; role m-1 is the real test role."""

    def __init__(self, rows, group=None, tasker=task_of):
        self.rows = rows
        self.keys = sorted(rows)
        self.tasks = sorted({tasker(k) for k in self.keys})
        self.tidx = {t: i for i, t in enumerate(self.tasks)}
        self.ktask = {k: self.tidx[tasker(k)] for k in self.keys}
        self.T = len(self.tasks)
        rng = np.random.default_rng(0)
        self.W = rng.multinomial(self.T, np.full(self.T, 1 / self.T), size=B)
        self.group = group or (lambda k: k.split("/")[0])

    def roles(self, key, role):
        m = self.rows[key]["m"]
        return [m - 1] if role == "real" else list(range(m - 1))

    def vec(self, cfg, get, role="real", keys=None):
        """Per-task (correct, answered) from get(outcome) -> None (abstain) or a score in [0, 1]."""
        c, a = np.zeros(self.T), np.zeros(self.T)
        for k in (keys if keys is not None else self.keys):
            for r in self.roles(k, role):
                v = get(self.rows[k]["cfg"][cfg][str(r)])
                if v is not None:
                    a[self.ktask[k]] += 1
                    c[self.ktask[k]] += float(v)
        return c, a

    def n_items(self, role="real", keys=None):
        return sum(len(self.roles(k, role)) for k in (keys if keys is not None else self.keys))


def f(field):
    return lambda o: o[field]


def clopper(k, n, alpha=0.05):
    if n == 0:
        return (None, None)
    lo = 0.0 if k == 0 else st.beta.ppf(alpha / 2, k, n - k + 1)
    hi = 1.0 if k == n else st.beta.ppf(1 - alpha / 2, k + 1, n - k)
    return (float(lo), float(hi))


def _pct(x):
    x = x[~np.isnan(x)]
    if not len(x):
        return (None, None)
    return (float(np.percentile(x, 2.5)), float(np.percentile(x, 97.5)))


def prec(d, c, a, n_items=None):
    with np.errstate(invalid="ignore", divide="ignore"):
        boot = (d.W @ c) / (d.W @ a)
    C, A = float(c.sum()), float(a.sum())
    out = dict(correct=round(C, 3), answered=int(A), wrong=round(A - C, 3), precision=(C / A if A else None), ci=_pct(boot) if A else (None, None),
               tasks_answered=int((a > 0).sum()), tasks_wrong=int(((a - c) > 1e-9).sum()), n_boot=int(np.sum(~np.isnan(boot))))
    if n_items:
        out["coverage"] = A / n_items
    # per answered task, each task one vote
    if A:
        tp = (c[a > 0] / a[a > 0])
        out["task_mean_precision"] = float(tp.mean())
        out["cp_tasks_all_right"] = clopper(int((tp >= 1 - 1e-9).sum()), len(tp))
    return out


def prec_diff(d, x, y):
    """precision(x) - precision(y); x, y = (c, a). Same resamples."""
    with np.errstate(invalid="ignore", divide="ignore"):
        bx = (d.W @ x[0]) / (d.W @ x[1])
        by = (d.W @ y[0]) / (d.W @ y[1])
    ax, ay = x[1].sum(), y[1].sum()
    est = (x[0].sum() / ax - y[0].sum() / ay) if ax and ay else None
    ci = _pct(bx - by)
    return dict(diff=est, ci=ci, separates=bool(ci[0] is not None and (ci[0] > 0 or ci[1] < 0)))


def count_ci(d, v):
    return dict(total=float(v.sum()), ci=_pct((d.W @ v).astype(float)))


def count_diff(d, x, y):
    """Paired difference of totals, with an exact two-sided sign test on discordant tasks."""
    dv = x - y
    ci = _pct((d.W @ dv).astype(float))
    px, py = int((dv > 1e-9).sum()), int((dv < -1e-9).sum())
    p = float(st.binomtest(px, px + py, 0.5).pvalue) if px + py else None
    return dict(x=float(x.sum()), y=float(y.sum()), diff=float(dv.sum()), ci=ci, tasks_x_more=px, tasks_y_more=py, sign_p=p,
                separates=bool(ci[0] is not None and (ci[0] > 0 or ci[1] < 0)))


def bucket(e):
    return "1.0" if e >= 0.99 else ("[0.5,1)" if e >= 0.5 else ("(0,0.5)" if e > 0 else "0"))


BUCKETS = ("1.0", "[0.5,1)", "(0,0.5)", "0")


def auroc(scores, labels):
    scores, labels = np.asarray(scores, float), np.asarray(labels, float)
    pos, neg = (labels > 0.5).sum(), (labels <= 0.5).sum()
    if not pos or not neg:
        return np.nan
    ranks = st.rankdata(scores)
    return (ranks[labels > 0.5].sum() - pos * (pos + 1) / 2) / (pos * neg)


def auroc_cluster(d, cfg, ev="top_ev", ok="top_ok", role="real", nboot=10000):
    per = collections.defaultdict(list)
    for k in d.keys:
        for r in d.roles(k, role):
            o = d.rows[k]["cfg"][cfg][str(r)]
            if o[ev] is not None:
                per[d.ktask[k]].append((o[ev], o[ok]))
    base = [x for v in per.values() for x in v]
    if not base:
        return dict(auroc=None, ci=(None, None), n=0)
    a = auroc(*zip(*base))
    rng = np.random.default_rng(0)
    vals = []
    for _ in range(nboot):
        s = []
        for t in rng.integers(0, d.T, d.T):
            s.extend(per.get(int(t), []))
        if s:
            vals.append(auroc(*zip(*s)))
    return dict(auroc=float(a), ci=_pct(np.array(vals)), n=len(base))


def load_rows(path):
    rows = {}
    with open(path) as fh:
        for line in fh:
            r = json.loads(line)
            rows[r["task"]] = r
    return rows


def load_dataset(tag, which="base"):
    return load_rows(os.path.join(HERE, "results", f"{tag}_{which}.jsonl"))


def load_dev():
    """Dev rows in the same shape: one role per task (the real one), m = 1."""
    rows = {}
    for k, r in load_rows(os.path.join(HERE, "results", "dev_base.jsonl")).items():
        rows[k] = dict(m=1, split=r["split"], n=r["n"], cfg={c: {"0": o} for c, o in r["cfg"].items()})
    return Data(rows, group=lambda k: rows[k]["split"], tasker=lambda k: k)


def fmt(p, pct=True):
    """'35/44 = 79.5% [64.5, 92.2]'"""
    if not p["answered"]:
        return "0/0"
    lo, hi = p["ci"]
    c = p["correct"]
    cs = f"{c:.0f}" if abs(c - round(c)) < 1e-9 else f"{c:.1f}"
    return f"{cs}/{p['answered']} = {100 * p['precision']:.1f}% [{100 * lo:.1f}, {100 * hi:.1f}]"


def fmtd(x):
    lo, hi = x["ci"]
    if x.get("diff") is None or lo is None:
        return "n/a"
    return f"{100 * x['diff']:+.1f} pts [{100 * lo:+.1f}, {100 * hi:+.1f}]" + (" separates" if x["separates"] else " does not separate")


def fmtc(x):
    lo, hi = x["ci"]
    s = f"{x['x']:.0f} vs {x['y']:.0f}: {x['diff']:+.0f} [{lo:+.0f}, {hi:+.0f}]; tasks {x['tasks_x_more']}:{x['tasks_y_more']}"
    if x["sign_p"] is not None:
        s += f", sign p = {x['sign_p']:.3f}"
    return s + (" separates" if x["separates"] else " does not separate")
