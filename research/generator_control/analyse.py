"""generator_control: the planned analysis (research/generator_control.md section 0) for the three learners on the re-arc tasks. Results from
VMs are read as untrusted JSON; grids are compared as data; nothing from them is executed. Statistics: research/monty_heldout/stats.py (Data,
prec, _pct, clopper) so numbers compare with the paper. No sign test (review section 3.3, Error 1): the mean, with a cluster bootstrap, and an
exact role permutation where all roles exist.
    .venv/bin/python -I -B research/generator_control/analyse.py [qwen ice monty]
Writes results/<learner>.json and prints the main table. All learners share `summarise(rows)`, on this common form per task:
  rows[tid] = {"real": R, "roles": {0: R, 1: R, 2: R, 3: R} or None}
  R = dict(top, fit, a, fa, fc, [v5]: None if abstain else bool right; a_pass, b_pass, any_abstain, why; folds: [dict(h, t, given, fit)])
Role 3 is the real test. D_r = sum over folds of (h - t)."""
import os  # noqa: E402  (release: paths from the repo root)
_REPO = os.environ.get("ARC_MONTY_ROOT", os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")))  # repo root
import collections
import glob
import json
import os
import sys

import numpy as np

ROOT = _REPO
HERE = os.path.join(ROOT, "research", "generator_control")
sys.path.insert(0, os.path.join(ROOT, "research", "monty_heldout"))
from stats import Data, _pct, clopper, prec  # noqa: E402

RES = os.path.join(HERE, "results")
BOUND = 0.25
OVERLAP_TASKS = ["rearc_995c5fa3", "rearc_feca6190", "rearc_7fe24cdd", "rearc_6e02f1e3"]


# ------------------------------------------------------------------------------------------------ data
def load_tasks():
    d = json.load(open(os.path.join(HERE, "data", "rearc_tasks.json")))
    return d["challenges"], d["solutions"]


def gkey(g):
    """As research/arc2/faloo_qwen.py."""
    return (len(g) * len(g[0]), len(g), len(g[0]), json.dumps(g))


def valid_output(g):
    return isinstance(g, list) and bool(g)


def read_jsonl_best(path):
    """Earliest-started good record per key, as merge_sampling.py. Error records are counted, never used."""
    best, errs, bad = {}, 0, 0
    if not os.path.exists(path):
        return best, errs, bad
    with open(path, errors="replace") as fh:
        for line in fh:
            try:
                r = json.loads(line)
                k = (r["kind"], r["task_id"], r["fold"])
            except Exception:
                bad += 1
                continue
            if "error" in r:
                errs += 1
                continue
            if k not in best or r.get("started_at", 0) < best[k].get("started_at", 0):
                best[k] = r
    return best, errs, bad


def learner_output(rec):
    """As faloo_qwen.learner_output."""
    rounds = [r for r in rec.get("rounds", []) if "test_out" in r]
    if not rounds:
        return None, False
    v = [r for r in rounds if r.get("verified")]
    r = v[0] if v else rounds[-1]
    return r["test_out"], bool(v)


# ------------------------------------------------------------------------------------------------ Qwen
def role_from_models(r, truth, M, full=None):
    """Role r of a task. truth[i] = y_i; M[frozenset({i, r})] = (pred dict by role, verified). full = (answer, verified) if a full run on this role exists."""
    folds, tests, a = [], [], True
    for i in range(4):
        if i == r:
            continue
        preds, ver = M[frozenset((i, r))]
        h = preds.get(i)
        t = preds.get(r)
        hk, tk = h is not None and h == truth[i], t is not None and t == truth[r]
        folds.append(dict(h=hk, t=tk, given=t is not None, fit=bool(ver)))
        tests.append(t)
        a = a and hk
    b = all(t is not None for t in tests) and all(t == tests[0] for t in tests[1:])
    y = tests[0] if b else None
    o = dict(a_pass=a, b_pass=b, any_abstain=any(t is None for t in tests), folds=folds)
    o["fa"] = (y == truth[r]) if (a and b) else None
    if full is None:
        o.update(top=None, fit=None, a=None, fc=None, no_full=True)
        o["why"] = "(a)" if not a else "(b)" if not b else "answer"
        return o
    fa, fv = full
    o["top"] = None if fa is None else fa == truth[r]
    o["fit"] = None if (fa is None or not fv) else fa == truth[r]
    o["a"] = None if (fa is None or not a) else fa == truth[r]
    c = a and b and fv and fa == y
    o["fc"] = (y == truth[r]) if c else None
    o["why"] = "(a)" if not a else "(b)" if not b else "(c)" if not c else "answer"
    return o


def qwen_rows():
    ch, sol = load_tasks()
    main, e1, b1 = read_jsonl_best(os.path.join(HERE, "raw", "gc_qwen_main.jsonl"))
    rot, e2, b2 = read_jsonl_best(os.path.join(HERE, "raw", "gc_qwen_rot.jsonl"))
    rows, skipped = {}, []
    for tid, t in ch.items():
        demos = sorted(t["train"], key=lambda p: gkey(p["input"]))
        truth = {i: demos[i]["output"] for i in range(3)}
        truth[3] = sol[tid][0]
        recs = [main.get(("fold", tid, i)) for i in range(3)]
        full = main.get(("full", tid, -1))
        if full is None or any(r is None for r in recs):
            skipped.append(tid)
            continue
        M = {}
        for i, rec in enumerate(recs):
            out, ver = learner_output(rec)
            d = dict(zip(rec["query_ids"], out)) if out is not None else {}
            assert set(rec["query_ids"]) == {"demo:%d" % i, "test:0"}, rec["query_ids"]
            M[frozenset((i, 3))] = ({i: d.get("demo:%d" % i), 3: d.get("test:0")}, ver)
        fo, fv = learner_output(full)
        fa = fo[0] if fo else None
        real = role_from_models(3, truth, M, (fa, fv))
        R = dict(real=real, roles=None)
        rr = [rot.get(("rot", tid, k)) for k in range(3)]
        if all(r is not None for r in rr):
            for k, rec in enumerate(rr):
                i, j = [(0, 1), (0, 2), (1, 2)][k]
                out, ver = learner_output(rec)
                d = dict(zip(rec["query_ids"], out)) if out is not None else {}
                assert set(rec["query_ids"]) == {"demo:%d" % i, "demo:%d" % j}, rec["query_ids"]
                M[frozenset((i, j))] = ({i: d.get("demo:%d" % i), j: d.get("demo:%d" % j)}, ver)
            R["roles"] = {r: role_from_models(r, truth, M, (fa, fv) if r == 3 else None) for r in range(4)}
        rows[tid] = R
    info = dict(error_records=e1 + e2, malformed_lines=b1 + b2, tasks_incomplete=len(skipped), records_main=len(main), records_rot=len(rot))
    info.update(qwen_run_checks(main, "main"))
    if rot:
        info["rot"] = qwen_run_checks(rot, "rot")
    return rows, info


def qwen_run_checks(done, label):
    recs = list(done.values())
    rounds = [r for x in recs for r in x.get("rounds", [])]
    tok = collections.Counter()
    for x in recs:
        tok[x["kind"]] += x.get("gen_tokens", 0)
    return dict(records=len(recs), tokens=dict(tok), rounds=len(rounds), skipped_context=sum("skipped" in r for r in rounds),
                rounds_no_code=sum(r.get("n_ok") == -1 for r in rounds), rounds_error=sum("error" in r for r in rounds),
                hit_cap=sum(bool(r.get("forced")) for r in rounds), max_prompt=max((r.get("prompt_len", 0) for r in rounds), default=0),
                seed_sent=sum(bool(x.get("seed_sent")) for x in recs), resumed=sum(x.get("resumed_from_round", 0) > 0 for x in recs),
                vms=dict(collections.Counter(x.get("vm") for x in recs)))


# ------------------------------------------------------------------------------------------------ 2020 program
def ice_rows():
    # research/icecuber_faloo/analyse.py, unchanged, loaded by its path (this script has the same name); its paths point here through HERE
    import importlib.util
    spec = importlib.util.spec_from_file_location("icecuber_analyse", os.path.join(ROOT, "research", "icecuber_faloo", "analyse.py"))
    IA = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(IA)
    return _ice_rows(IA)


def _ice_rows(IA):
    IA.HERE = os.path.join(HERE, "ice")
    runs, bad = IA.load_runs()
    items = {3: IA.load_items("rearc")}
    for r in range(3):
        items[r] = IA.load_items(f"rearc_role{r}")
    rows, part = {}, 0

    def conv(o):
        fr = [dict(h=bool(x["held_ok"]), t=bool(x["test_ok"]), given=bool(x["test_given"]), fit=bool(x["test_fits"])) for x in o["fold_rows"]]
        return dict(top=o["usual"], fit=o["usual_fit"], a=o["a"], fa=o["fa"], fc=o["fc"], a_pass=o["a_pass"], b_pass=o["b_pass"],
                    any_abstain=o["any_fold_test_abstain"], why=o["why"], folds=fr, full_given=o["has"], p2=o["p2"], p3=o["p3"])

    for k, it in enumerate(items[3]):
        o = IA.outcome(it, runs)
        if not (o["full_done"] and o["folds_done"]):
            part += 1
            continue
        R = dict(real=conv(o), roles=None)
        all_r = {}
        for r in range(3):
            q = items[r][k]
            assert q["task"] == it["task"]
            ov = IA.outcome(q, runs)
            if ov["full_done"] and ov["folds_done"]:
                all_r[r] = conv(ov)
        if len(all_r) == 3:
            all_r[3] = R["real"]
            R["roles"] = all_r
        rows[it["task"]] = R
    st = collections.Counter()
    for rec in runs.values():
        for c, s in rec["per"].items():
            st[f"cfg{c}:{s}"] += 1
    info = dict(runs=len(runs), malformed_lines=bad, tasks_incomplete=part, process_status=dict(sorted(st.items())),
                runs_no_answer=sum(not r["answers"] for r in runs.values()), core_hours=round(sum(r.get("secs", 0) for r in runs.values()) / 3600, 1))
    return rows, info


# ------------------------------------------------------------------------------------------------ Monty-ARC
def monty_rows():
    rows, swap, st = {}, 0, collections.Counter()
    path = os.path.join(HERE, "monty", "results", "rearc_base.jsonl")
    if not os.path.exists(path):
        return {}, dict(items=0)
    cache_cpu = 0.0
    with open(path) as fh:
        for line in fh:
            r = json.loads(line)
            tid = r["task"].split("#")[0]
            truth, m = r["truth"], r["m"]
            assert m == 4
            swap += r["swap_diffs"]
            roles = {}
            for a in range(m):
                o = r["cfg"]["full"][str(a)]
                folds = []
                for b in range(m):
                    if b == a:
                        continue
                    fh_ = o["fold_h"][str(b)]
                    if fh_ is None:
                        folds.append(dict(h=False, t=False, given=False, fit=False))
                    else:
                        folds.append(dict(h=fh_[0] == truth[b], t=fh_[1] == truth[a], given=True, fit=True))
                # (b) from the fold answers themselves, abstaining counts as not agreeing
                ans = [o["fold_h"][str(b)] for b in range(m) if b != a]
                b_pass = all(x is not None for x in ans) and len({x[1] for x in ans}) == 1
                roles[a] = dict(top=None if o["top_ok"] is None else bool(o["top_ok"] > 0.5), fit=None if o["fit"] is None else bool(o["fit"] > 0.5),
                                fit_top1=None if o["fitt"] is None else bool(o["fitt"] > 0.5), v5=None if o["v5"] is None else bool(o["v5"] > 0.5),
                                a=o["a"], fa=o["fa"], fc=o["fc"], a_pass=all(x["h"] for x in folds), b_pass=b_pass,
                                any_abstain=any(not x["given"] for x in folds), why=o["why"], folds=folds,
                                top_ev=o["top_ev"], p2=o["p2"], top_mods=o["top_mods"])
                st[o["why"] if a == m - 1 else "role:" + o["why"]] += 1
            rows[tid] = dict(real=roles[m - 1], roles=roles)
    p = os.path.join(HERE, "monty", "cache", "rearc_p0.jsonl")
    if os.path.exists(p):
        with open(p) as fh:
            for line in fh:
                try:
                    cache_cpu += json.loads(line).get("cpu", 0)
                except Exception:
                    pass
    return rows, dict(items=len(rows), query_swap_diffs=swap, whys=dict(st), cpu_hours=round(cache_cpu / 3600, 2))


# ------------------------------------------------------------------------------------------------ statistics
def exact_role_test(D):
    """D: tasks x 4 integers, D[t, 3] the real role. Under the null the role is uniform and independent across tasks. Exact distribution of the
    sum by convolution. Two-sided: P(|S| >= |S_obs|). Returns also the mean and the null SD of the mean."""
    D = np.asarray(D, dtype=int)
    T = D.shape[0]
    off = int(np.abs(D).max()) if D.size else 0
    pmf = np.array([1.0])
    lo = 0
    for t in range(T):
        vals = D[t]
        a, b = int(vals.min()), int(vals.max())
        step = np.zeros(b - a + 1)
        for v in vals:
            step[int(v) - a] += 0.25
        pmf = np.convolve(pmf, step)
        lo += a
    s = np.arange(lo, lo + len(pmf))
    obs = int(D[:, 3].sum())
    p2 = float(pmf[np.abs(s) >= abs(obs)].sum())
    mean0 = float((pmf * s).sum())
    sd0 = float(np.sqrt((pmf * (s - mean0) ** 2).sum()))
    F = 3 * T
    return dict(S_obs=obs, mean_obs=obs / F, p_two_sided=min(1.0, p2), p_held_more=float(pmf[s >= obs].sum()), p_test_more=float(pmf[s <= obs].sum()),
                null_mean=mean0 / F, null_sd=sd0 / F, max_abs=off,
                expected_more_held=float(np.mean(D > 0, axis=1).sum()), expected_more_test=float(np.mean(D < 0, axis=1).sum()),
                observed_more_held=int((D[:, 3] > 0).sum()), observed_more_test=int((D[:, 3] < 0).sum()))


def summarise(rows, label=""):
    keys = sorted(rows)
    T = len(keys)
    J = dict(tasks=T)
    if not T:
        return J
    drows = {k: dict(m=1, cfg={"full": {"0": rows[k]["real"]}}) for k in keys}
    d = Data(drows, tasker=lambda k: k)
    J["rules"] = {}
    names = ["top", "fit", "a", "fa", "fc"]
    if "v5" in rows[keys[0]]["real"]:
        names.append("v5")
    if "fit_top1" in rows[keys[0]]["real"]:
        names.append("fit_top1")
    for name in names:
        c, a = d.vec("full", lambda o, n=name: o.get(n))
        p = prec(d, c, a, n_items=T)
        wrong = int(round(a.sum() - c.sum()))
        p["joint"] = wrong / T
        p["joint_cp"] = clopper(wrong, T)
        p["coverage_ci"] = _pct((d.W @ a) / T)
        cov = a.sum() / T
        p["floor"] = (1 - BOUND / cov) if cov else None
        p["floor_ci"] = None
        lo, hi = p["coverage_ci"]
        if lo:
            p["floor_ci"] = (1 - BOUND / lo, 1 - BOUND / hi)
        p["vacuous"] = bool(cov <= BOUND)
        p["vacuous_at_lower_ci"] = bool(lo is None or lo <= BOUND)
        J["rules"][name] = p
    # (E): mean(h - t) over real-role folds, abstain = wrong
    H = np.array([sum(x["h"] for x in rows[k]["real"]["folds"]) for k in keys], float)
    Te = np.array([sum(x["t"] for x in rows[k]["real"]["folds"]) for k in keys], float)
    N = np.array([len(rows[k]["real"]["folds"]) for k in keys], float)
    A = np.array([sum(x["h"] and not x["t"] for x in rows[k]["real"]["folds"]) for k in keys], float)
    B_ = np.array([sum(x["t"] and not x["h"] for x in rows[k]["real"]["folds"]) for k in keys], float)
    bd = (d.W @ (H - Te)) / (d.W @ N)
    J["E"] = dict(folds=int(N.sum()), held=float(H.sum()), test=float(Te.sum()), held_rate=float(H.sum() / N.sum()), test_rate=float(Te.sum() / N.sum()),
                  held_ci=_pct((d.W @ H) / (d.W @ N)), test_ci=_pct((d.W @ Te) / (d.W @ N)),
                  diff=float((H - Te).sum() / N.sum()), ci=_pct(bd), half_width=(lambda c: (c[1] - c[0]) / 2)(_pct(bd)),
                  held_only=float(A.sum()), test_only=float(B_.sum()))
    # held-out split: fold programs with a test answer; and those that fit what they saw
    J["split"] = split(rows, keys, d, lambda x: x["given"])
    J["split_fit"] = split(rows, keys, d, lambda x: x["given"] and x["fit"])
    # (b) among roles passing (a), real role
    pa = [rows[k]["real"] for k in keys if rows[k]["real"]["a_pass"]]
    J["b_given_a"] = dict(a_pass=len(pa), b_fail=sum(not o["b_pass"] for o in pa), b_fail_with_abstain=sum(o["any_abstain"] for o in pa if not o["b_pass"]),
                          a_right_b_fail=sum(o.get("a") is True and not o["b_pass"] for o in pa), a_wrong_b_fail=sum(o.get("a") is False and not o["b_pass"] for o in pa),
                          c_fail_given_ab=sum(o["fa"] is not None and o.get("fc") is None for o in pa),
                          whys=dict(collections.Counter(rows[k]["real"]["why"] for k in keys)))
    # sensitivity: without the tasks sharing a pair with re_arc.zip
    keep = [k for k in keys if k not in OVERLAP_TASKS]
    sub = [rows[k]["real"] for k in keep]
    J["sensitivity_no_overlap"] = dict(tasks=len(keep), fc_answered=sum(o["fc"] is not None for o in sub), fc_right=sum(o["fc"] is True for o in sub),
                                       fa_answered=sum(o["fa"] is not None for o in sub), fa_right=sum(o["fa"] is True for o in sub),
                                       mean_h_minus_t=float(np.mean([sum(x["h"] - x["t"] for x in o["folds"]) / 3 for o in sub])))
    # rotation
    rk = [k for k in keys if rows[k]["roles"] is not None]
    if rk:
        J["rotation"] = rotation(rows, rk)
    return J


def split(rows, keys, d, keep):
    pc, pa, mc, ma, within = [], [], [], [], []
    for k in keys:
        fs = [x for x in rows[k]["real"]["folds"] if keep(x)]
        hit = [x["t"] for x in fs if x["h"]]
        miss = [x["t"] for x in fs if not x["h"]]
        pc.append(sum(hit))
        pa.append(len(hit))
        mc.append(sum(miss))
        ma.append(len(miss))
        within.append(np.mean(hit) - np.mean(miss) if hit and miss else np.nan)
    pc, pa, mc, ma, within = (np.array(x, float) for x in (pc, pa, mc, ma, within))
    with np.errstate(invalid="ignore", divide="ignore"):
        bp, bm = (d.W @ pc) / (d.W @ pa), (d.W @ mc) / (d.W @ ma)
    has = ~np.isnan(within)
    w0 = np.nan_to_num(within)
    with np.errstate(invalid="ignore", divide="ignore"):
        bw = (d.W @ (w0 * has)) / (d.W @ has.astype(float))
    out = dict(pred_right=float(pc.sum()), pred_n=int(pa.sum()), pred_rate=float(pc.sum() / pa.sum()) if pa.sum() else None, pred_ci=_pct(bp),
               miss_right=float(mc.sum()), miss_n=int(ma.sum()), miss_rate=float(mc.sum() / ma.sum()) if ma.sum() else None, miss_ci=_pct(bm),
               tasks_with_answer=int(((pa + ma) > 0).sum()))
    out["diff"] = (out["pred_rate"] - out["miss_rate"]) if pa.sum() and ma.sum() else None
    out["diff_ci"] = _pct(bp - bm)
    out["within_tasks"] = int(has.sum())
    out["within"] = float(within[has].mean()) if has.any() else None
    out["within_ci"] = _pct(bw) if has.any() else (None, None)
    return out


def rotation(rows, keys):
    T = len(keys)
    D = np.zeros((T, 4), dtype=int)
    ev = np.zeros((T, 4), dtype=int)
    bad_err = 0
    J = {}
    has_full = not any(rows[k]["roles"][r].get("no_full") for k in keys for r in range(4))
    per = {n: dict(ans=np.zeros((T, 4)), wrong=np.zeros((T, 4))) for n in (("fa", "fc") if has_full else ("fa",))}
    pa_total, b_fail = 0, 0
    for i, k in enumerate(keys):
        for r in range(4):
            o = rows[k]["roles"][r]
            D[i, r] = sum(int(x["h"]) - int(x["t"]) for x in o["folds"])
            ev[i, r] = all(x["h"] and not x["t"] for x in o["folds"])
            if o["fa"] is False and not ev[i, r]:
                bad_err += 1
            pa_total += bool(o["a_pass"])
            b_fail += bool(o["a_pass"] and not o["b_pass"])
            for n in per:
                v = o.get(n)
                per[n]["ans"][i, r] = v is not None
                per[n]["wrong"][i, r] = v is False
    J["tasks"] = T
    J["identity_violations"] = int((D.sum(axis=1) != 0).sum())
    J["exact"] = exact_role_test(D)
    J["events"] = dict(tasks_0=int((ev.sum(axis=1) == 0).sum()), tasks_1=int((ev.sum(axis=1) == 1).sum()), tasks_2_or_more=int((ev.sum(axis=1) >= 2).sum()),
                       on_real_role=int(ev[:, 3].sum()), expected_real_role=float(ev.sum() / 4), events=int(ev.sum()),
                       wrong_faloo_not_an_event=bad_err)
    J["a_pass_roles"] = pa_total
    J["b_fail_roles"] = b_fail
    W = np.random.default_rng(0).multinomial(T, np.full(T, 1 / T), size=10000)
    for n, x in per.items():
        ans, wrong = x["ans"].mean(axis=1), x["wrong"].mean(axis=1)
        cov, joint = float(ans.mean()), float(wrong.mean())
        ci_c, ci_j = _pct((W @ ans) / T), _pct((W @ wrong) / T)
        wr_tot, an_tot = float(x["wrong"].sum()), float(x["ans"].sum())
        J[f"role_avg_{n}"] = dict(coverage=cov, coverage_ci=ci_c, joint=joint, joint_ci=ci_j, precision=(1 - wr_tot / an_tot) if an_tot else None,
                                  answered=int(an_tot), wrong=int(wr_tot), per_role_answered=[int(v) for v in x["ans"].sum(axis=0)], per_role_wrong=[int(v) for v in x["wrong"].sum(axis=0)],
                                  floor=(1 - BOUND / cov) if cov else None, floor_ci=((1 - BOUND / ci_c[0]) if ci_c[0] else None, (1 - BOUND / ci_c[1]) if ci_c[1] else None))
    return J


# ------------------------------------------------------------------------------------------------ main
def monty_extra(rows):
    """The earlier measure of Monty-ARC: top answer at evidence >= 0.99 against below, real role."""
    keys = sorted(rows)
    if not keys:
        return {}
    drows = {k: dict(m=1, cfg={"full": {"0": rows[k]["real"]}}) for k in keys}
    d = Data(drows, tasker=lambda k: k)
    hi = lambda o: None if o.get("top_ev") is None or o["top_ev"] < 0.99 else o["top"]   # noqa: E731
    lo = lambda o: None if o.get("top_ev") is None or o["top_ev"] >= 0.99 else o["top"]  # noqa: E731
    hc, ha = d.vec("full", hi)
    lc, la = d.vec("full", lo)
    with np.errstate(invalid="ignore", divide="ignore"):
        bh, bl = (d.W @ hc) / (d.W @ ha), (d.W @ lc) / (d.W @ la)
    return dict(hi_right=float(hc.sum()), hi_n=int(ha.sum()), lo_right=float(lc.sum()), lo_n=int(la.sum()),
                hi_rate=float(hc.sum() / ha.sum()) if ha.sum() else None, lo_rate=float(lc.sum() / la.sum()) if la.sum() else None,
                diff=float(hc.sum() / ha.sum() - lc.sum() / la.sum()) if ha.sum() and la.sum() else None, diff_ci=_pct(bh - bl))


def main():
    os.makedirs(RES, exist_ok=True)
    which = sys.argv[1:] or ["qwen", "ice", "monty"]
    for w in which:
        rows, info = dict(qwen=qwen_rows, ice=ice_rows, monty=monty_rows)[w]()
        J = summarise(rows, w)
        J["info"] = info
        if w == "monty":
            J["top_ev_split"] = monty_extra(rows)
        with open(os.path.join(RES, f"{w}.json"), "w") as fh:
            json.dump(J, fh, indent=1, default=float)
        print_table(w, J)


def print_table(w, J):
    print(f"\n=== {w}: {J['tasks']} tasks complete; info {J.get('info')}")
    if not J["tasks"]:
        return
    for n, p in J["rules"].items():
        ci = p["ci"]
        print(f"{n:8s} {p['correct']:.0f}/{p['answered']} = {100 * (p['precision'] or 0):.1f}% [{100 * (ci[0] or 0):.1f}, {100 * (ci[1] or 0):.1f}] cov {100 * p['coverage']:.1f}% "
              f"[{100 * p['coverage_ci'][0]:.1f}, {100 * p['coverage_ci'][1]:.1f}] joint {100 * p['joint']:.2f}% floor {p['floor'] if p['floor'] is None else round(100 * p['floor'], 1)} vacuous {p['vacuous']}")
    e = J["E"]
    print(f"(E) h {100 * e['held_rate']:.1f} t {100 * e['test_rate']:.1f} diff {100 * e['diff']:+.1f} [{100 * e['ci'][0]:+.1f}, {100 * e['ci'][1]:+.1f}] discordant {e['held_only']:.0f}/{e['test_only']:.0f}")
    print("split", {k: (round(v, 3) if isinstance(v, float) else v) for k, v in J["split"].items() if k in ("pred_right", "pred_n", "pred_rate", "miss_right", "miss_n", "miss_rate", "diff", "diff_ci", "within", "within_ci", "within_tasks")})
    print("split_fit", {k: (round(v, 3) if isinstance(v, float) else v) for k, v in J["split_fit"].items() if k in ("pred_n", "pred_rate", "miss_n", "miss_rate", "diff", "diff_ci", "within", "within_ci", "within_tasks")})
    print("b_given_a", J["b_given_a"])
    print("sens", J["sensitivity_no_overlap"])
    if "rotation" in J:
        r = J["rotation"]
        print("rotation identity_violations", r["identity_violations"], "events", r["events"], "exact", {k: r["exact"][k] for k in ("mean_obs", "p_two_sided", "null_sd", "expected_more_held", "expected_more_test", "observed_more_held", "observed_more_test")})
        for n in ("fa", "fc"):
            if f"role_avg_{n}" in r:
                print("role avg", n, r[f"role_avg_{n}"])


if __name__ == "__main__":
    main()
