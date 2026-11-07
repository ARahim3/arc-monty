"""All pre-stated comparisons, from raw rows. Bootstraps come from research/monty_heldout/stats.py: percentile cluster bootstrap,
10,000 resamples, seed 0; a difference "separates" if its 95% CI excludes 0.
usage: python -I -B analyse.py [--dev]  -> results/analysis.json (or dev/analysis_dev.json)"""
import argparse
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "research", "monty_heldout"))
import stats as ST  # noqa: E402  (read-only reuse: cluster bootstrap)
from static import rules  # noqa: E402
from settings import CELL_SENSORS, CONFIGS, COUNT_SENSOR, FRESH_GEN, FRESH_HAND, GAME_ARMS, SECONDARY, SPENT, WEAK_GROUPS  # noqa: E402
import data_sets as DS  # noqa: E402

RES = os.path.join(HERE, "results")
BOOT = ST.B


def data_on(keys, cluster):
    return ST.Data({k: dict(m=1, cfg={}) for k in keys}, tasker=cluster)


def pts(v):
    return None if v is None else round(100 * float(v), 2)


def ci_pts(ci):
    return [None if c is None else round(100 * c, 2) for c in ci]


# ------------------------------------------------------------------ games
def read_arm(name, res=RES):
    return json.load(open(os.path.join(res, "games", f"{name}.json")))


def comparator(k, names):
    """Rows of the world-model probe at history k (research/arc3_wm/results), for these games only."""
    fn = "wm2_m2_k8_12.jsonl" if k == 12 else "wm2_m2.jsonl"
    out = {}
    with open(os.path.join(ROOT, "research", "arc3_wm", "results", fn)) as fh:
        for line in fh:
            r = json.loads(line)
            if r["k"] == k and r["game"] in names:
                out[(r["game"], r["i"])] = r
    return out


def vec(rows, value, select, games):
    """Per game: sum of value over selected rows, and how many."""
    idx = {g: i for i, g in enumerate(games)}
    c, a = np.zeros(len(games)), np.zeros(len(games))
    for r in rows:
        if select(r):
            a[idx[r["game"]]] += 1
            c[idx[r["game"]]] += float(value(r))
    return c, a


def diff(games, x, y, a):
    """Pooled difference of two rates on the same transitions, CI by game, and a per-game table and leave-one-game-out range."""
    d = data_on(games, lambda k: k)
    res = ST.prec_diff(d, (x, a), (y, a))
    per = {g.split("-")[0]: dict(n=int(a[i]), x=pts(x[i] / a[i]) if a[i] else None, y=pts(y[i] / a[i]) if a[i] else None) for i, g in enumerate(games)}
    logo = []
    for i in range(len(games)):
        m = np.ones(len(games), bool)
        m[i] = False
        if a[m].sum():
            logo.append(float(x[m].sum() / a[m].sum() - y[m].sum() / a[m].sum()))
    return dict(diff=pts(res["diff"]), ci=ci_pts(res["ci"]), separates=res["separates"], n=int(a.sum()), x=pts(x.sum() / a.sum()), y=pts(y.sum() / a.sum()),
                per_game=per, leave_one_game_out=[pts(min(logo)), pts(max(logo))] if logo else None)


def games_analysis(games, arms, res=RES):
    A = {name: read_arm(name, res) for name in arms}
    names = set(games)
    full = {(r["game"], r["i"]): r for r in A["full"]}
    out = {}
    ch = lambda r: r["n_ch"] > 0
    hit = lambda r: r["col"]
    fx, fa = vec(A["full"], hit, ch, games)

    def vs(arm):
        return diff(games, fx, vec(A[arm], hit, ch, games)[0], fa)

    out["M1 motor signal, full minus told nothing"] = vs("nomotor")
    out["M5 displacement form, full minus colour-only form"] = vs("colour_only")
    lx, la = vec(A["local"], hit, ch, games)
    for key, arm in (("M4a moving frame", "local+moving"), ("M4b nearest-object frame", "local+near")):
        out[key + ", population, minus local context"] = diff(games, vec(A[arm], hit, ch, games)[0], lx, la)
    sx, sa = vec(A["single"], hit, ch, games)
    for key, arm in (("M4a moving frame", "single+moving"), ("M4b nearest-object frame", "single+near")):
        out[key + ", single column, minus local context"] = diff(games, vec(A[arm], hit, ch, games)[0], sx, sa)
    out["all transitions, exact playfield"] = dict(full=pts(np.mean([r["col"] for r in A["full"]])), no_change=pts(np.mean([r["b0"] for r in A["full"]])), n=len(A["full"]))
    # the probe's comparators, same transitions
    for k in (3, 12):
        comp = comparator(k, names)
        shared = [(full[key], r) for key, r in comp.items() if key in full]
        agree = float(np.mean([x["b0"] == r["B0_play"] for x, r in shared]))
        rows = [dict(game=x["game"], col=x["col"], b1=bool(r["B1rel_play_play"]), m=bool(r.get("M_play_fallback")), changed=not r["B0_play"]) for x, r in shared]
        for sel, tag in ((lambda r: r["changed"], "changed"), (lambda r: True, "all")):
            cx, ca = vec(rows, lambda r: r["col"], sel, games)
            bx, _ = vec(rows, lambda r: r["b1"], sel, games)
            mx, _ = vec(rows, lambda r: r["m"], sel, games)
            pre = "" if k == 3 and tag == "changed" else f"secondary k={k} {tag}: "
            out[pre + ("M2 column minus Monty-ARC columns" if not pre else "column minus Monty-ARC columns")] = diff(games, cx, mx, ca)
            out[pre + ("M3 column minus object-relative repeat" if not pre else "column minus object-relative repeat")] = diff(games, cx, bx, ca)
        out[f"label agreement with the probe at k={k}"] = round(agree, 4)
        conf = [r for x, r in shared if r.get("M_conf") and not r.get("M_identity")]
        cc = [x for x, r in shared if x["conf"]]
        out[f"confident non-identity answers at k={k}"] = dict(column_coverage=pts(len(cc) / len(shared)), column_precision=pts(np.mean([x["col"] for x in cc])) if cc else None,
                                                               monty_coverage=pts(len(conf) / len(shared)), monty_precision=pts(np.mean([bool(r.get("M_play")) for r in conf])) if conf else None)
    # M6
    for h in (2, 4, 8):
        s = [r for r in A["full"] if f"roll{h}" in r]
        rx, ra = vec(s, lambda r: r[f"roll{h}"], lambda r: True, games)
        ux, _ = vec(s, lambda r: r[f"still{h}"], lambda r: True, games)
        out[f"M6 open-loop rollout minus unchanged frame, horizon {h}"] = diff(games, rx, ux, ra)
    # persisting models
    if "local+library" in A:
        ax, aa = vec(A["local"], hit, lambda r: True, games)
        bx, _ = vec(A["local+library"], hit, lambda r: True, games)
        out["E2 games: library minus alone, all transitions"] = diff(games, bx, ax, aa)
        for sel, tag in ((lambda r: r["uses"] == 0, "first use of a command"), (ch, "changed transitions")):
            ax, aa = vec(A["local"], hit, sel, games)
            bx, _ = vec(A["local+library"], hit, sel, games)
            out[f"E2 games: library minus alone, {tag}"] = diff(games, bx, ax, aa)
    return out


# ------------------------------------------------------------------ static
def read_set(name, res=RES):
    rows = {}
    with open(os.path.join(res, f"static_{name}.jsonl")) as fh:
        for line in fh:
            r = json.loads(line)
            rows[r["task"]] = r
    return rows


def read_monty(name, res=RES):
    """Frozen v5 per item, real role: from this project's fresh run, or the earlier held-out results for spent sets."""
    path = os.path.join(res, f"monty_{name}.jsonl")
    if not os.path.exists(path):
        path = os.path.join(ROOT, "research", "monty_heldout", "results", f"{name}_base.jsonl")
    out = {}
    with open(path) as fh:
        for line in fh:
            r = json.loads(line)
            out[r["task"]] = r["cfg"]["full"][str(r["m"] - 1)]
    return out


def keep_of(sensors):
    return {i for i, c in enumerate(CONFIGS) if c["kind"] in sensors}


ALL_COLS = set(range(len(CONFIGS)))


def per_cluster(keys, d, value):
    v = np.zeros(d.T)
    for k in keys:
        v[d.ktask[k]] += value(k)
    return v


def split_held(d, keys, programs):
    """Held-out split: precision on the test of fold programs that predict their held-out demo vs those that miss it."""
    c = {True: np.zeros(d.T), False: np.zeros(d.T)}
    a = {True: np.zeros(d.T), False: np.zeros(d.T)}
    for k in keys:
        for held, right in programs(k):
            a[held][d.ktask[k]] += 1
            c[held][d.ktask[k]] += right
    res = ST.prec_diff(d, (c[True], a[True]), (c[False], a[False]))
    return dict(predict=f"{int(c[True].sum())}/{int(a[True].sum())}", miss=f"{int(c[False].sum())}/{int(a[False].sum())}",
                predict_rate=pts(c[True].sum() / a[True].sum()) if a[True].sum() else None, miss_rate=pts(c[False].sum() / a[False].sum()) if a[False].sum() else None,
                diff=pts(res["diff"]), ci=ci_pts(res["ci"]), separates=res["separates"])


def within_task(d, keys, programs):
    """Mean over tasks holding both kinds of (right | predict) minus (right | miss); task means resampled by cluster."""
    tasks = {}
    for k in keys:
        tasks.setdefault((d.ktask[k], k.split("#")[0]), []).extend(programs(k))
    c, a = np.zeros(d.T), np.zeros(d.T)
    for (cl, _), ps in tasks.items():
        p = [r for h, r in ps if h]
        m = [r for h, r in ps if not h]
        if p and m:
            c[cl] += np.mean(p) - np.mean(m)
            a[cl] += 1
    if not a.sum():
        return dict(diff=None, ci=[None, None], tasks=0, separates=False)
    with np.errstate(invalid="ignore", divide="ignore"):
        boot = (d.W @ c) / (d.W @ a)
    ci = ST._pct(boot)
    return dict(diff=pts(c.sum() / a.sum()), ci=ci_pts(ci), tasks=int(a.sum()), separates=bool(ci[0] > 0 or ci[1] < 0))


def load_many(names, clusters, res):
    """Rows and Monty rows of one or more sets, with keys prefixed by the set's name, and the cluster of a key."""
    rows, monty = {}, {}
    for name in names:
        for k, r in read_set(name, res).items():
            rows[f"{name}:{k}"] = r
        for k, r in read_monty(name, res).items():
            monty[f"{name}:{k}"] = r

    def cluster(key):
        name, k = key.split(":", 1)
        return f"{name}:{clusters[name](k)}"

    return rows, monty, cluster


def static_set(names, clusters, res, keep_all=ALL_COLS):
    rows, monty, cluster = load_many(names, clusters, res)
    keys = sorted(rows)
    missing = [k for k in keys if k not in monty]
    assert not missing, (names, missing[:3])
    d = data_on(keys, cluster)
    R = {k: rules(rows[k], keep_all) for k in keys}
    col = per_cluster(keys, d, lambda k: R[k]["pass2"])
    mon = per_cluster(keys, d, lambda k: float(monty[k]["p2"]))
    out = dict(items=len(keys), clusters=d.T, timeouts=sum(bool(r.get("timeout")) for r in rows.values()), errors=sum(bool(r.get("error")) for r in rows.values()),
               column_pass2=round(float(col.sum()), 2), monty_pass2=round(float(mon.sum()), 2))
    # S1
    with np.errstate(invalid="ignore", divide="ignore"):
        boot = (d.W @ col) / (d.W @ mon)
    boot = np.where(np.isinf(boot), np.nan, boot)
    out["S1 ratio"] = None if not mon.sum() else round(float(col.sum() / mon.sum()), 3)
    out["S1 ratio ci"] = [None if c is None else round(c, 3) for c in ST._pct(boot)]
    both = sum(min(R[k]["pass2"], float(monty[k]["p2"])) for k in keys)
    out["S1 overlap"] = dict(both=both, column_only=int(sum(R[k]["pass2"] > float(monty[k]["p2"]) for k in keys)), monty_only=int(sum(R[k]["pass2"] < float(monty[k]["p2"]) for k in keys)))
    # S2
    cells = keep_of(CELL_SENSORS)
    cv = per_cluster(keys, d, lambda k: rules(rows[k], cells)["pass2"])
    out["S2 all minus cells"] = ST.count_diff(d, col, cv)
    # count sensor
    nocount = ALL_COLS - keep_of((COUNT_SENSOR,))
    nv = per_cluster(keys, d, lambda k: rules(rows[k], nocount)["pass2"])
    out["with minus without count sensor"] = ST.count_diff(d, col, nv)
    # S4
    programs = lambda k: R[k]["fold_programs"]
    out["S4 between tasks"] = split_held(d, keys, programs)
    out["S4 within task"] = within_task(d, keys, programs)
    for rule, field in (("FA-LOO + (c)", "fc"), ("(a)+(b)", "fa"), ("plain (a)", "a"), ("fit", "fit"), ("top answer", "top_right")):
        c, a = np.zeros(d.T), np.zeros(d.T)
        for k in keys:
            v = R[k][field]
            if v is not None:
                a[d.ktask[k]] += 1
                c[d.ktask[k]] += float(v)
        out[f"rule {rule}"] = ST.prec(d, c, a, len(keys))
        out[f"rule {rule}"]["line"] = ST.fmt(out[f"rule {rule}"])
        out.setdefault("_rv", {})[field] = (c, a)
    rv = out.pop("_rv")
    for a_, b_ in (("fc", "fit"), ("fc", "top_right"), ("fit", "top_right")):
        res = ST.prec_diff(d, rv[a_], rv[b_])
        out[f"rule diff {a_} minus {b_}"] = dict(diff=pts(res["diff"]), ci=ci_pts(res["ci"]), separates=res["separates"])
    # exchangeability: held-out rate vs test rate, every fold counted, abstain = wrong. The mean, never a task sign test.
    h, t, n = np.zeros(d.T), np.zeros(d.T), np.zeros(d.T)
    for k in keys:
        ps = R[k]["fold_programs"]
        cl = d.ktask[k]
        n[cl] += rows[k]["n"] if rows[k]["n"] > 1 else 0
        h[cl] += sum(p[0] for p in ps)
        t[cl] += sum(p[1] for p in ps)
    res = ST.prec_diff(d, (h, n), (t, n))
    out["held-out minus test, mean"] = dict(held_out=pts(h.sum() / n.sum()) if n.sum() else None, test=pts(t.sum() / n.sum()) if n.sum() else None, diff=pts(res["diff"]), ci=ci_pts(res["ci"]), separates=res["separates"])
    # the same analysis for frozen Monty-ARC v5
    out["monty"] = monty_rules(d, keys, monty)
    return out, rows, monty, d


def monty_rules(d, keys, monty):
    out = {}
    for rule, field in (("FA-LOO + (c)", "fc"), ("plain (a)", "a"), ("v5", "v5"), ("fit", "fit")):
        c, a = np.zeros(d.T), np.zeros(d.T)
        for k in keys:
            v = monty[k].get(field)
            if v is not None:
                a[d.ktask[k]] += 1
                c[d.ktask[k]] += float(v)
        p = ST.prec(d, c, a, len(keys))
        out[rule] = dict(line=ST.fmt(p), coverage=p.get("coverage"), tasks_answered=p["tasks_answered"], tasks_wrong=p["tasks_wrong"])
    if all("fold_programs" in monty[k] for k in keys):
        programs = lambda k: monty[k]["fold_programs"]
        out["held-out split, fold programs"] = split_held(d, keys, programs)
        out["held-out split, within task"] = within_task(d, keys, programs)
    ev = {True: [np.zeros(d.T), np.zeros(d.T)], False: [np.zeros(d.T), np.zeros(d.T)]}
    for k in keys:
        if monty[k].get("top_ev") is not None:
            b = monty[k]["top_ev"] >= 0.99
            ev[b][1][d.ktask[k]] += 1
            ev[b][0][d.ktask[k]] += float(monty[k]["top_ok"])
    res = ST.prec_diff(d, tuple(ev[True]), tuple(ev[False]))
    out["top answer, evidence >= 0.99 minus below"] = dict(high=f"{ev[True][0].sum():.0f}/{ev[True][1].sum():.0f}", low=f"{ev[False][0].sum():.0f}/{ev[False][1].sum():.0f}", diff=pts(res["diff"]), ci=ci_pts(res["ci"]), separates=res["separates"])
    return out


def jsonable(x):
    if isinstance(x, dict):
        return {str(k): jsonable(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [jsonable(v) for v in x]
    if isinstance(x, (np.floating, np.integer, np.bool_)):
        return x.item()
    return x


# ------------------------------------------------------------------ S3 and E2, ConceptARC only
def weak_groups(res):
    rows, monty, cluster = load_many(["concept"], {"concept": DS.SETS["concept"][1]}, res)
    keys = sorted(k for k in rows if k.split(":", 1)[1].split("/")[0] in WEAK_GROUPS)
    d = data_on(keys, cluster)
    nocount = ALL_COLS - keep_of((COUNT_SENSOR,))
    w = per_cluster(keys, d, lambda k: rules(rows[k], ALL_COLS)["pass2"])
    wo = per_cluster(keys, d, lambda k: rules(rows[k], nocount)["pass2"])
    m = per_cluster(keys, d, lambda k: float(monty[k]["p2"]))
    groups = {}
    for k in keys:
        g = k.split(":", 1)[1].split("/")[0]
        v = groups.setdefault(g, [0.0, 0.0, 0.0])
        v[0] += rules(rows[k], ALL_COLS)["pass2"]
        v[1] += rules(rows[k], nocount)["pass2"]
        v[2] += float(monty[k]["p2"])
    return {"items": len(keys), "S3a with count minus Monty-ARC": ST.count_diff(d, w, m), "S3b with count minus without count": ST.count_diff(d, w, wo), "by group: with, without, Monty-ARC": groups}


def library(res):
    alone, _, _ = load_many(["concept"], {"concept": DS.SETS["concept"][1]}, res)
    same = {f"concept:{k}": r for k, r in _plain(os.path.join(res, "library_same.jsonl")).items()}
    other = {f"concept:{k}": r for k, r in _plain(os.path.join(res, "library_other.jsonl")).items()}
    keys = sorted(alone)
    assert not [k for k in keys if k not in same or k not in other]
    group = lambda k: k.split(":", 1)[1].split("/")[0]
    d = data_on(keys, group)
    v = {n: per_cluster(keys, d, lambda k: rules(r[k], ALL_COLS)["pass2"]) for n, r in (("alone", alone), ("same", same), ("other", other))}
    out = {"pass2": {n: float(x.sum()) for n, x in v.items()}, "items": len(keys), "clusters": d.T, "timeouts": sum(bool(same[k].get("timeout") or other[k].get("timeout")) for k in keys)}
    out["E2 same concept minus alone, CI by concept group"] = ST.count_diff(d, v["same"], v["alone"])
    out["other concepts minus alone, CI by concept group"] = ST.count_diff(d, v["other"], v["alone"])
    out["same concept minus other concepts, CI by concept group"] = ST.count_diff(d, v["same"], v["other"])
    out["by group: alone, same, other"] = {g: [float(v[n][d.tidx[g]]) for n in ("alone", "same", "other")] for g in d.tasks}
    tk = data_on(keys, lambda k: k.split("#")[0])
    t = {n: per_cluster(keys, tk, lambda k: rules(r[k], ALL_COLS)["pass2"]) for n, r in (("alone", alone), ("same", same))}
    out["secondary: same concept minus alone, CI by task"] = ST.count_diff(tk, t["same"], t["alone"])
    return out


def _plain(path):
    return {json.loads(line)["task"]: json.loads(line) for line in open(path)}


# ------------------------------------------------------------------ verdicts, exactly as fixed in the plan
def s1_verdict(ratio, ci):
    if ratio is None:
        return "undefined: Monty-ARC solves none here"
    if ratio < 0.25:
        return "FAILS: ratio under 0.25"
    if ratio >= 0.5 and ci[0] is not None and ci[0] > 0.25:
        return "SUPPORTS: at least 0.5, lower bound above 0.25"
    return "inconclusive"


def verdicts(out):
    g, v = out["games"], {}
    v["M1"] = "FAILS" if g["M1 motor signal, full minus told nothing"]["diff"] < 5 or not g["M1 motor signal, full minus told nothing"]["separates"] else "holds"
    m2 = g["M2 column minus Monty-ARC columns"]
    v["M2"] = "FAILS" if not m2["separates"] or m2["diff"] < 0 else "holds"
    m3 = g["M3 column minus object-relative repeat"]
    v["M3"] = "FAILS" if not m3["separates"] or m3["diff"] < 0 else "holds"
    for k in ("M4a moving frame", "M4b nearest-object frame"):
        for tag in ("population", "single column"):
            e = g[f"{k}, {tag}, minus local context"]
            v[f"{k[:3]} {tag}"] = "FAILS: upper bound under +3" if e["ci"][1] < 3 else ("holds: gain separates" if e["ci"][0] > 0 else "not falsified, no separation")
    m5 = g["M5 displacement form, full minus colour-only form"]
    v["M5"] = "FAILS: upper bound under +3" if m5["ci"][1] < 3 else ("holds: gain separates" if m5["ci"][0] > 0 else "not falsified, no separation")
    m6 = g["M6 open-loop rollout minus unchanged frame, horizon 4"]
    v["M6"] = "FAILS: below baseline at horizon 4" if m6["diff"] < 0 else ("holds: above baseline, separates" if m6["ci"][0] > 0 else "not below baseline, no separation")
    for label, key in (("hand-made fresh", "hand"), ("tama", "tama")):
        r = out["strata"][key]
        v[f"S1 {label}"] = s1_verdict(r["S1 ratio"], r["S1 ratio ci"])
        s2 = r["S2 all minus cells"]
        v[f"S2 {label}"] = "holds" if s2["ci"][0] is not None and s2["ci"][0] > 0 else "FAILS: CI includes 0" if s2["separates"] is False else "FAILS: negative"
        s4 = r["S4 between tasks"]
        v[f"S4 {label}"] = "holds" if s4["separates"] and s4["diff"] > 0 else "FAILS: split does not separate"
        v[f"S4 {label}, within a task"] = "separates" if r["S4 within task"]["separates"] and r["S4 within task"]["diff"] > 0 else "does not separate"
    a, b = out["S3"]["S3a with count minus Monty-ARC"], out["S3"]["S3b with count minus without count"]
    v["S3a"] = "holds: separates from 1 of 180" if a["ci"][0] > 0 else "FAILS: no separation from 1 of 180"
    v["S3b"] = "holds: the count sensor itself adds" if b["ci"][0] > 0 else "FAILS: the count sensor adds nothing that separates"
    e = out["E2"]["E2 same concept minus alone, CI by concept group"]
    v["E2 static"] = "holds" if e["ci"][0] > 0 else "FAILS: CI includes 0 or negative"
    e = g.get("E2 games: library minus alone, all transitions")
    if e:
        v["E2 games"] = "holds" if e["separates"] and e["diff"] > 0 else "FAILS: CI includes 0 or negative"
    return v


def main(res=RES, games=None):
    import games as G
    names = games or G.named("heldout")
    out = dict(frozen=json.load(open(os.path.join(HERE, "FROZEN.json"))) if os.path.exists(os.path.join(HERE, "FROZEN.json")) else None)
    out["games"] = games_analysis(names, GAME_ARMS, res)
    clusters = {n: DS.SETS[n][1] for n in DS.SETS}
    out["sets"] = {}
    for n in list(FRESH_HAND) + list(FRESH_GEN) + list(SECONDARY) + list(SPENT):
        out["sets"][n] = static_set([n], clusters, res)[0]
    out["strata"] = dict(hand=static_set(list(FRESH_HAND), clusters, res)[0], tama=out["sets"]["tama"])
    out["S3"] = weak_groups(res)
    out["E2"] = library(res)
    out["verdicts"] = verdicts(jsonable(out))
    json.dump(jsonable(out), open(os.path.join(res, "analysis.json"), "w"), indent=1, default=float)
    print(json.dumps(out["verdicts"], indent=1))


if __name__ == "__main__":
    main()
