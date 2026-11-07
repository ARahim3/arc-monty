"""icecuber_faloo: rules, planned comparisons and the reproduction check, from raw/runs_*.jsonl and export/items_*.jsonl.
Reads pulled results as untrusted JSON (grids are validated, nothing is executed). Statistics come from
research/monty_heldout/stats.py so numbers compare with paper Tables 5 and 6.
    python -B research/icecuber_faloo/analyse.py [concept mini oned minimal agi2]
Writes research/icecuber_faloo/results_<set>.json and prints tables."""
import os  # noqa: E402  (release: paths from the repo root)
_REPO = os.environ.get("ARC_MONTY_ROOT", os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")))  # repo root
import collections
import glob
import json
import os
import sys

ROOT = _REPO
HERE = os.path.join(ROOT, "research", "icecuber_faloo")
HL = os.path.join(ROOT, "research", "monty_heldout")
sys.path.insert(0, HL)
import numpy as np  # noqa: E402
from scipy import stats as st  # noqa: E402
from stats import Data, _pct, clopper, count_diff, f, prec, prec_diff  # noqa: E402

B = 10000
CFGS = (3, 23, 33, 4)  # the safe_run.py recipe


def valid_grid(g):
    if not isinstance(g, list) or not g or len(g) > 30:
        return False
    w = None
    for row in g:
        if not isinstance(row, list) or not row or len(row) > 30:
            return False
        if w is None:
            w = len(row)
        if len(row) != w or not all(isinstance(c, int) and not isinstance(c, bool) and 0 <= c <= 9 for c in row):
            return False
    return True


def parse_img(s):
    """'|123|456|' -> grid, or None if malformed. Text from the VM is data."""
    if not isinstance(s, str) or len(s) > 2000 or not s.startswith("|") or not s.endswith("|"):
        return None
    rows = s[1:-1].split("|")
    if not rows or not all(r.isdigit() for r in rows) or len({len(r) for r in rows}) != 1:
        return None
    g = [[int(c) for c in r] for r in rows]
    return g if valid_grid(g) else None


def merge(recs):
    """The safe_run.py merge, re-implemented: all answer lines of the finished configurations, sorted by (score, image)
    descending, first three distinct images. The placeholder a run writes when it has no candidate (score -1) is dropped."""
    cands = []
    for r in recs:
        if r.get("status") != "ok":
            continue
        for line in r.get("lines", []):
            try:
                img, sc = line
                sc = float(sc)
            except Exception:
                continue
            if sc < 0 or parse_img(img) is None:
                continue
            cands.append((sc, img))
    cands.sort(reverse=True)
    best = []
    for sc, img in cands:
        if img not in [b[1] for b in best]:
            best.append((sc, img))
            if len(best) == 3:
                break
    return [parse_img(b[1]) for b in best], [b[0] for b in best]


def load_runs(cfgs=CFGS):
    """rid -> merged record, for runs with a record for every configuration. Malformed lines are counted and dropped."""
    by, bad = collections.defaultdict(dict), 0
    for path in sorted(glob.glob(os.path.join(HERE, "raw", "runs_*.jsonl"))):
        with open(path, errors="replace") as fh:
            for line in fh:
                try:
                    r = json.loads(line)
                    if not isinstance(r["rid"], str) or int(r["cfg"]) not in cfgs:
                        raise ValueError
                except Exception:
                    bad += 1
                    continue
                by[r["rid"]].setdefault(int(r["cfg"]), r)
    runs = {}
    for rid, per in by.items():
        if not all(c in per for c in cfgs):
            continue
        recs = [per[c] for c in cfgs]
        ans, scores = merge(recs)
        nd = recs[0].get("nd")
        fits = [None if nd is None else bool(s > nd - 0.499) for s in scores]
        statuses = {str(c): per[c].get("status") for c in cfgs}
        runs[rid] = dict(rid=rid, status="ok" if any(s == "ok" for s in statuses.values()) else "failed", answers=ans, scores=scores, fits=fits, nd=nd, per=statuses,
                         secs=sum(float(per[c].get("secs") or 0) for c in cfgs))
    return runs, bad


def load_items(tag):
    with open(os.path.join(HERE, "export", f"items_{tag}.jsonl")) as fh:
        return [json.loads(line) for line in fh]


def top(runs, rid):
    """Top answer of a run: None if no answer, timeout or crash."""
    if rid is None:
        return None
    r = runs.get(rid)
    if r is None or r.get("status") != "ok" or not r.get("answers"):
        return None
    return r["answers"][0]


def done(runs, rid):
    return rid is None or rid in runs


def outcome(it, runs):
    """All rules on the real test role for one item (one test pair)."""
    fr = runs.get(it["full"])
    truth = it["truth"]
    o = dict(full_done=fr is not None)
    ans = fr.get("answers", []) if (fr and fr.get("status") == "ok") else []
    o["full_status"] = None if fr is None else fr.get("status")
    y_full = ans[0] if ans else None
    o["has"] = y_full is not None
    o["usual"] = None if y_full is None else bool(y_full == truth)
    o["p1"] = float(any(a == truth for a in ans[:1]))
    o["p2"] = float(any(a == truth for a in ans[:2]))
    o["p3"] = float(any(a == truth for a in ans[:3]))
    o["top_fits"] = None if (fr is None or not ans) else fr.get("fits", [None])[0]
    o["usual_fit"] = None if not o["top_fits"] else bool(y_full == truth)  # my added row: top answer only if it reproduces every demonstration
    o["y_full"] = y_full
    folds = it["folds"]
    o["folds_done"] = all(done(runs, x["held_rid"]) and done(runs, x["test_rid"]) for x in folds)
    held, tests = [], []
    for x in folds:
        h, t = top(runs, x["held_rid"]), top(runs, x["test_rid"])
        held.append(h)
        tests.append(t)
    def fit0(rid):
        r = runs.get(rid) if rid else None
        return bool(r and r.get("fits") and r["fits"][0])
    o["fold_rows"] = [dict(j=x["j"], held_given=h is not None, test_given=t is not None, held_ok=bool(h == x["held_truth"]) if h is not None else False,
                           test_ok=bool(t == truth) if t is not None else False, test_fits=fit0(x["test_rid"]), held_fits=fit0(x["held_rid"])) for x, h, t in zip(folds, held, tests)]
    a_ok = it["n"] >= 2 and all(h is not None and h == x["held_truth"] for h, x in zip(held, folds))
    agree = it["n"] >= 2 and all(t is not None for t in tests) and all(t == tests[0] for t in tests[1:])
    o["a_pass"] = bool(a_ok)
    o["b_pass"] = bool(agree)
    y = tests[0] if agree else None
    o["a"] = bool(y_full == truth) if (a_ok and y_full is not None) else None  # plain (a) with the full-data answer
    fa = a_ok and agree
    o["fa"] = bool(y == truth) if fa else None
    c = fa and y_full is not None and y_full == y
    o["fc"] = bool(y == truth) if c else None
    o["why"] = ("n=1" if it["n"] < 2 else "(a)" if not a_ok else "(b)" if not agree else "(c)" if not c else "answer")
    o["any_fold_test_abstain"] = it["n"] >= 2 and any(t is None for t in tests)
    o["fold_equals_full"] = None if not a_ok else [bool(t is not None and t == y_full) for t in tests]
    return o


def boot_ci(num, den=None):
    T = len(num)
    W = np.random.default_rng(0).multinomial(T, np.full(T, 1 / T), size=B)
    if den is None:
        return _pct((W @ num).astype(float))
    with np.errstate(invalid="ignore", divide="ignore"):
        return _pct((W @ num) / (W @ den))


def discordant(per):
    """As research/paper/v8_notes/scripts/revise_monty.py `report`. per: cluster -> [(held_right, test_right)]."""
    cl = sorted(per)
    H = np.array([sum(x[0] for x in per[c]) for c in cl], float)
    Te = np.array([sum(x[1] for x in per[c]) for c in cl], float)
    N = np.array([len(per[c]) for c in cl], float)
    A = np.array([sum(x[0] * (1 - x[1]) for x in per[c]) for c in cl], float)
    Bb = np.array([sum((1 - x[0]) * x[1] for x in per[c]) for c in cl], float)
    ci = boot_ci(H - Te, N)
    more, less = int(((A - Bb) > 1e-9).sum()), int(((A - Bb) < -1e-9).sum())
    p = float(st.binomtest(more, more + less, 0.5).pvalue) if more + less else None
    return dict(folds=int(N.sum()), held=float(H.sum()), test=float(Te.sum()), held_rate=float(H.sum() / N.sum()), test_rate=float(Te.sum() / N.sum()),
                diff=float((H.sum() - Te.sum()) / N.sum()), ci=ci, held_only=float(A.sum()), test_only=float(Bb.sum()), clusters=len(cl),
                clusters_more_held=more, clusters_more_test=less, sign_p=p)


def hold_split(per):
    """Comparison 2. per: cluster -> [(predicts_held, right_on_test)] over fold programs that give a test answer."""
    cl = sorted(per)
    pc = np.array([sum(t for h, t in per[c] if h) for c in cl], float)
    pa = np.array([sum(1 for h, t in per[c] if h) for c in cl], float)
    mc = np.array([sum(t for h, t in per[c] if not h) for c in cl], float)
    ma = np.array([sum(1 for h, t in per[c] if not h) for c in cl], float)
    T = len(cl)
    W = np.random.default_rng(0).multinomial(T, np.full(T, 1 / T), size=B)
    with np.errstate(invalid="ignore", divide="ignore"):
        bp, bm = (W @ pc) / (W @ pa), (W @ mc) / (W @ ma)
    return dict(pred_right=float(pc.sum()), pred_n=int(pa.sum()), pred_rate=float(pc.sum() / pa.sum()) if pa.sum() else None, pred_ci=_pct(bp),
                miss_right=float(mc.sum()), miss_n=int(ma.sum()), miss_rate=float(mc.sum() / ma.sum()) if ma.sum() else None, miss_ci=_pct(bm),
                diff=float(pc.sum() / pa.sum() - mc.sum() / ma.sum()) if pa.sum() and ma.sum() else None, diff_ci=_pct(bp - bm), clusters=T,
                clusters_with_answer=int(((pa + ma) > 0).sum()))


def item_rids(it):
    return [it["full"]] + [x[k] for x in it["folds"] for k in ("held_rid", "test_rid") if x[k]]


def all_crash(runs, rid):
    r = runs.get(rid)
    return bool(r) and all(v == "crash" for v in r["per"].values())


def analyse(tag, runs, verbose=True, subset=None, by_task=False):
    items = load_items(tag)
    if subset is not None:
        items = [it for it in items if subset(it)]
    if by_task:
        for it in items:
            it["cluster"] = it["task"]
    cl = {it["key"]: it["cluster"] for it in items}
    out = {it["key"]: outcome(it, runs) for it in items}
    complete = [it for it in items if out[it["key"]]["full_done"] and out[it["key"]]["folds_done"]]
    fulld = [it for it in items if out[it["key"]]["full_done"]]
    J = dict(set=tag, items=len(items), items_full_done=len(fulld), items_complete=len(complete), clusters=len({it["cluster"] for it in items}),
             partial=len(complete) < len(items))
    # Everything below is on items with every run back, so all rules share one population.
    rows = {it["key"]: dict(m=1, cfg={"full": {"0": out[it["key"]]}}) for it in complete}
    if not rows:
        return J, out
    d = Data(rows, tasker=lambda k: cl[k])
    n_items = len(rows)
    J["mean_bound"] = float(np.mean([1 / (it["n"] + 1) for it in complete]))
    J["rules"] = {}
    vecs = {}
    for name, field in (("usual", "usual"), ("usual_fit", "usual_fit"), ("a", "a"), ("fa", "fa"), ("fc", "fc")):
        v = d.vec("full", f(field))
        vecs[name] = v
        p = prec(d, *v, n_items=n_items)
        p["joint"] = float(p["wrong"] / n_items)
        J["rules"][name] = p
    for name in ("p1", "p2", "p3"):
        v = d.vec("full", f(name))[0]
        J[name] = dict(count=float(v.sum()), of=n_items, rate=float(v.sum() / n_items), ci=[None if x is None else x / n_items for x in _pct((d.W @ v).astype(float))])
    J["cmp1_fc_minus_usual"] = prec_diff(d, vecs["fc"], vecs["usual"])
    J["cmp1_fa_minus_usual"] = prec_diff(d, vecs["fa"], vecs["usual"])
    J["cmp1_fc_minus_a"] = prec_diff(d, vecs["fc"], vecs["a"])
    J["cmp1_fc_minus_usual_fit"] = prec_diff(d, vecs["fc"], vecs["usual_fit"])
    J["cmp1_a_minus_usual_fit"] = prec_diff(d, vecs["a"], vecs["usual_fit"])
    # 2, 3: fold level
    per_split = collections.defaultdict(list)
    per_fit = collections.defaultdict(list)
    per_disc = collections.defaultdict(list)
    for it in complete:
        o = out[it["key"]]
        for r in o["fold_rows"]:
            per_disc[it["cluster"]].append((float(r["held_ok"]), float(r["test_ok"])))
            per_split[it["cluster"]]
            per_fit[it["cluster"]]
            if r["test_given"]:
                per_split[it["cluster"]].append((r["held_ok"], float(r["test_ok"])))
                if r["test_fits"]:
                    per_fit[it["cluster"]].append((r["held_ok"], float(r["test_ok"])))
    J["cmp2_split"] = hold_split(per_split) if any(per_split.values()) else None
    J["cmp2_split_fit_only"] = hold_split(per_fit) if any(per_fit.values()) else None  # secondary: test answer reproduces every demonstration the fold saw
    J["cmp3_discordant"] = discordant(per_disc) if per_disc else None
    J["fold_answer_rate"] = dict(
        test_given=sum(r["test_given"] for it in complete for r in out[it["key"]]["fold_rows"]),
        held_given=sum(r["held_given"] for it in complete for r in out[it["key"]]["fold_rows"]),
        folds=sum(len(out[it["key"]]["fold_rows"]) for it in complete))
    # 4: (b) among roles passing (a), and distance from first-fit
    pa = [out[it["key"]] for it in complete if out[it["key"]]["a_pass"]]
    J["cmp4"] = dict(a_pass=len(pa), b_fail=sum(not o["b_pass"] for o in pa),
                     b_fail_rate=(sum(not o["b_pass"] for o in pa) / len(pa)) if pa else None,
                     b_fail_by_abstention=sum(o["any_fold_test_abstain"] for o in pa),
                     c_fail_given_ab=sum((o["fa"] is not None) and (o["fc"] is None) for o in pa),
                     lemma_violation_any_fold_differs_from_full=sum(not all(o["fold_equals_full"]) for o in pa),
                     a_right_b_fail=sum(o["a"] is True and not o["b_pass"] for o in pa),
                     a_wrong_b_fail=sum(o["a"] is False and not o["b_pass"] for o in pa),
                     whys=dict(collections.Counter(out[it["key"]]["why"] for it in complete)))
    # 5: floor
    c = J["rules"]["fc"].get("coverage", 0.0)
    J["cmp5"] = dict(coverage=c, mean_bound=J["mean_bound"], floor=(1 - J["mean_bound"] / c) if c else None, vacuous=(c <= J["mean_bound"]))
    # task-level
    st_ = collections.Counter(out[it["key"]]["full_status"] for it in complete)
    J["full_status"] = dict(st_)
    allr = sorted({r for it in complete for r in item_rids(it)})
    pc = collections.Counter()
    for r in allr:
        for c, s in runs[r]["per"].items():
            pc[(c, s)] += 1
    J["process_status"] = {f"cfg{c}:{s}": v for (c, s), v in sorted(pc.items())}
    J["runs"] = len(allr)
    J["runs_no_answer"] = sum(not runs[r]["answers"] for r in allr)
    J["runs_any_timeout"] = sum(any(v == "timeout" for v in runs[r]["per"].values()) for r in allr)
    J["runs_any_mem"] = sum(any(v == "mem" for v in runs[r]["per"].values()) for r in allr)
    J["runs_all_crash"] = sum(all_crash(runs, r) for r in allr)
    J["runs_secs_total"] = sum(runs[r].get("secs", 0) for r in allr)
    J["items_with_any_timeout"] = sum(any(any(v == "timeout" for v in runs[r]["per"].values()) for r in item_rids(it)) for it in complete)
    J["items_unreadable"] = sum(any(all_crash(runs, r) for r in item_rids(it)) for it in complete)
    J["items_n1"] = sum(it["n"] == 1 for it in complete)
    tops = [out[it["key"]] for it in complete if out[it["key"]]["has"]]
    J["top_fit_share"] = dict(n=len(tops), fits=sum(bool(o["top_fits"]) for o in tops), fit_right=sum(bool(o["top_fits"]) and o["usual"] for o in tops), nofit_right=sum((not o["top_fits"]) and o["usual"] for o in tops))
    byn = {}
    for lab, cond in (("n=2", lambda n: n == 2), ("n>=3", lambda n: n >= 3)):
        s = [it for it in complete if cond(it["n"])]
        ans = [out[it["key"]]["fc"] for it in s if out[it["key"]]["fc"] is not None]
        byn[lab] = dict(items=len(s), answered=len(ans), right=sum(ans))
    J["fc_by_n"] = byn
    J["fc_wrong_items"] = [dict(key=it["key"], n=it["n"]) for it in complete if out[it["key"]]["fc"] is False]
    J["fc_right_items"] = sum(1 for it in complete if out[it["key"]]["fc"] is True)
    if verbose:
        print(f"\n=== {tag}: {len(complete)} of {len(items)} items complete; clusters {J['clusters']}; mean 1/(n+1) {100 * J['mean_bound']:.1f}%")
        for nm in ("usual", "usual_fit", "a", "fa", "fc"):
            p = J["rules"][nm]
            print(f"{nm:6s} {p['correct']:.0f}/{p['answered']} = {100 * (p['precision'] or 0):.1f}% [{100 * (p['ci'][0] or 0):.1f}, {100 * (p['ci'][1] or 0):.1f}] cov {100 * p.get('coverage', 0):.1f}% joint {100 * p['joint']:.2f}% tasks {p['tasks_answered']}/{p['tasks_wrong']} wrong")
        print("pass@1,2,3", J["p1"]["count"], J["p2"]["count"], J["p3"]["count"], "of", n_items)
        print("cmp1", J["cmp1_fc_minus_usual"])
        print("cmp2", J["cmp2_split"])
        print("cmp3", J["cmp3_discordant"])
        print("cmp4", J["cmp4"])
        print("cmp5", J["cmp5"])
        print("status", J["full_status"], J["fold_answer_rate"])
        print("limits", {k: J[k] for k in ("runs", "runs_no_answer", "runs_any_timeout", "runs_any_mem", "runs_all_crash", "items_with_any_timeout", "items_unreadable", "items_n1")}, J["process_status"])
        print("top fit", J["top_fit_share"], "fc by n", J["fc_by_n"])
        print("cmp2 fit-only", J["cmp2_split_fit_only"])
    return J, out


def repro_concept(out):
    """Item-by-item against the authors' data.xlsx: pass@3 here vs their 'First Place ARC-Kaggle' (any of three guesses)."""
    sys.path.insert(0, HL)
    from xlsx_read import rows as xl
    X = xl(os.path.join(ROOT, "external", "judge", "conceptarc", "repo", "data.xlsx"))["Machine Solver Performance"]
    head = X[0]
    I = {n: head.index(n) for n in ("Task File", "Test Input Index", "First Place ARC-Kaggle", "ensemble_indices")}
    mine, theirs, idx = {}, {}, {}
    for key, o in out.items():
        if o["full_done"]:
            task = key.split("#")[0].split("/")[-1]
            mine[(task, int(key.split("#")[1]))] = o
    for row in X[1:]:
        if not row or not row[0] or "Minimal" in row[0]:
            continue
        row = row + [None] * (len(head) - len(row))
        k = (row[I["Task File"]][:-5], int(row[I["Test Input Index"]]))
        theirs[k] = row[I["First Place ARC-Kaggle"]] == "CORRECT"
        idx[k] = row[I["ensemble_indices"]]
    common = sorted(set(mine) & set(theirs))
    a = sum(mine[k]["p3"] > 0 and theirs[k] for k in common)
    b = sum(mine[k]["p3"] > 0 and not theirs[k] for k in common)
    c = sum(mine[k]["p3"] == 0 and theirs[k] for k in common)
    e = sum(mine[k]["p3"] == 0 and not theirs[k] for k in common)
    J = dict(common=len(common), mine_p3=sum(mine[k]["p3"] > 0 for k in common), theirs=sum(theirs[k] for k in common), both=a, only_mine=b, only_theirs=c, neither=e,
             agree=(a + e) / len(common) if common else None,
             only_mine_items=[f"{k[0]}#{k[1]}" for k in common if mine[k]["p3"] > 0 and not theirs[k]],
             only_theirs_items=[f"{k[0]}#{k[1]}" for k in common if mine[k]["p3"] == 0 and theirs[k]],
             only_theirs_status=dict(collections.Counter(mine[k]["full_status"] for k in common if mine[k]["p3"] == 0 and theirs[k])),
             mine_p1=sum(mine[k]["p1"] > 0 for k in common), mine_p2=sum(mine[k]["p2"] > 0 for k in common),
             their_idx_first=sum(1 for k in common if idx[k] and idx[k].split(",")[0].strip() == "1"))
    return J


def native_check(runs, out):
    """Addendum B: full-data runs in the file's native demonstration order, against the authors' two columns and the canonical runs."""
    sys.path.insert(0, HL)
    from xlsx_read import rows as xl
    path = os.path.join(HERE, "export", "jobs_native.jsonl")
    if not os.path.exists(path):
        return None
    items = {it["key"]: it for it in load_items("concept")}
    nat = {}
    with open(path) as fh:
        for line in fh:
            j = json.loads(line)
            r = runs.get(j["rid"])
            if r is None:
                continue
            truth = items[j["key"]]["truth"]
            pos = next((i + 1 for i, a in enumerate(r["answers"]) if a == truth), None)
            nat[j["key"]] = dict(pos=pos, top=r["answers"][0] if r["answers"] else None, per=r["per"])
    if len(nat) < len(items):
        return dict(done=len(nat), of=len(items))
    X = xl(os.path.join(ROOT, "external", "judge", "conceptarc", "repo", "data.xlsx"))["Machine Solver Performance"]
    head = X[0]
    I = {n: head.index(n) for n in ("Task File", "Test Input Index", "First Place ARC-Kaggle", "ensemble_indices")}
    first, ens = {}, {}
    for row in X[1:]:
        if not row or not row[0] or "Minimal" in row[0]:
            continue
        row = row + [None] * (len(head) - len(row))
        k = (row[I["Task File"]][:-5], int(row[I["Test Input Index"]]))
        first[k] = row[I["First Place ARC-Kaggle"]] == "CORRECT"
        ens[k] = row[I["ensemble_indices"]]
    def kk(key):
        return (key.split("#")[0].split("/")[-1], int(key.split("#")[1]))
    J = dict(done=len(nat), of=len(items))
    J["native_p1"] = sum(v["pos"] == 1 for v in nat.values())
    J["native_p2"] = sum(v["pos"] in (1, 2) for v in nat.values())
    J["native_p3"] = sum(v["pos"] is not None for v in nat.values())
    J["canonical_p3"] = sum(out[k]["p3"] > 0 for k in nat)
    for name, col in (("first", {k: v for k, v in first.items()}), ("ensemble", {k: v is not None for k, v in ens.items()})):
        for lab, mine in (("native", {k: nat[k]["pos"] is not None for k in nat}), ("canonical", {k: out[k]["p3"] > 0 for k in nat})):
            agree = sum(mine[k] == col[kk(k)] for k in nat)
            J[f"{lab}_vs_{name}"] = dict(agree=agree, only_mine=[k for k in nat if mine[k] and not col[kk(k)]], only_theirs=[k for k in nat if not mine[k] and col[kk(k)]])
    J["authors_first_vs_ensemble_disagree"] = sum(first[kk(k)] != (ens[kk(k)] is not None) for k in nat)
    J["native_vs_canonical_top_differs"] = sum(nat[k]["top"] != out[k]["y_full"] for k in nat)
    J["native_vs_canonical_p3_differs"] = [k for k in nat if (nat[k]["pos"] is not None) != (out[k]["p3"] > 0)]
    # attempt position against the ensemble column, on items both solve
    both = [k for k in nat if nat[k]["pos"] is not None and ens[kk(k)]]
    J["position_equal_ensemble"] = sum(str(nat[k]["pos"]) == ens[kk(k)].split(",")[0].strip() for k in both)
    J["position_compared"] = len(both)
    J["native_status"] = dict(collections.Counter(s for v in nat.values() for s in v["per"].values()))
    return J


def monty_overlap(tag, out, items):
    """Comparison 6, descriptive: FA-LOO + (c) answers of Monty-ARC (results/<tag>_base.jsonl, real role) vs icecuber."""
    M = {}
    with open(os.path.join(HL, "results", f"{tag}_base.jsonl")) as fh:
        for line in fh:
            r = json.loads(line)
            M[r["task"]] = r["cfg"]["full"][str(r["m"] - 1)]
    res = {}
    for rule_i, rule_m, name in (("fc", "fc", "faloo_c"), ("usual", "top_ok", "usual")):
        both = [0, 0, 0]  # n, ice right, monty right
        only_i = [0, 0]
        only_m = [0, 0]
        neither = 0
        for it in items:
            k = it["key"]
            oi, om = out[k], M[k]
            if not (oi["full_done"] and oi["folds_done"]):
                continue
            ai, am = oi[rule_i], om[rule_m]
            if ai is not None and am is not None:
                both[0] += 1
                both[1] += float(ai)
                both[2] += float(am)
            elif ai is not None:
                only_i[0] += 1
                only_i[1] += float(ai)
            elif am is not None:
                only_m[0] += 1
                only_m[1] += float(am)
            else:
                neither += 1
        res[name] = dict(both=both[0], both_ice_right=both[1], both_monty_right=both[2], ice_only=only_i[0], ice_only_right=only_i[1], monty_only=only_m[0], monty_only_right=only_m[1], neither=neither)
    return res


def checks(runs):
    """chk_rep: same run again. chk_rev: demonstrations reversed. Compare merged lists with the original run."""
    J = dict(rep=dict(n=0, same_top=0, same_list=0), rev=dict(n=0, same_top=0, same_list=0, diffs=[]))
    path = os.path.join(HERE, "export", "jobs_checks.jsonl")
    with open(path) as fh:
        js = [json.loads(line) for line in fh]
    by = {}
    for j in js:
        by[j["rid"]] = j
        kind = "rep" if j["rid"].startswith("chk_rep_") else "rev"
        o, c = runs.get(j["orig"]), runs.get(j["rid"])
        if not o or not c:
            continue
        J[kind]["n"] += 1
        same_top = (o["answers"][:1] == c["answers"][:1])
        J[kind]["same_top"] += same_top
        J[kind]["same_list"] += (o["answers"] == c["answers"])
        if kind == "rev" and not same_top:
            J[kind]["diffs"].append(dict(rid=j["orig"], nd=len(j["train"]), scores=[o["scores"][:1], c["scores"][:1]]))
        if kind == "rep" and not same_top:
            J[kind].setdefault("diffs", []).append(dict(rid=j["orig"], per=[o["per"], c["per"]]))
    return J


def main():
    tags = sys.argv[1:] or ["concept", "mini", "oned", "minimal", "agi2"]
    runs, bad = load_runs()
    print("runs", len(runs), "malformed lines dropped", bad, "status", dict(collections.Counter(r.get("status") for r in runs.values())))
    if os.path.exists(os.path.join(HERE, "export", "jobs_checks.jsonl")):
        C = checks(runs)
        print("checks", {k: {a: b for a, b in v.items() if a != "diffs"} for k, v in C.items()})
        with open(os.path.join(HERE, "results_checks.json"), "w") as fh:
            json.dump(C, fh, indent=1)
    for tag in tags:
        J, out = analyse(tag, runs)
        if tag == "concept":
            J["repro"] = repro_concept(out)
            print("repro", J["repro"])
            J["native"] = native_check(runs, out)
            print("native", J["native"])
        if tag in ("concept", "mini", "oned", "minimal") and J.get("items_complete"):
            J["cmp6_monty"] = monty_overlap(tag, out, load_items(tag))
            print("cmp6", J["cmp6_monty"])
        if tag == "oned" and J.get("items_complete"):
            readable = lambda it: all(done(runs, r) for r in item_rids(it)) and not any(all_crash(runs, r) for r in item_rids(it))  # noqa: E731
            print("\n--- oned, readable items only (Addendum A, secondary)")
            J["readable"], out_r = analyse(tag, runs, subset=readable)
            J["readable"]["cmp6_monty"] = monty_overlap(tag, out_r, [it for it in load_items(tag) if readable(it)])
            print("cmp6 readable", J["readable"]["cmp6_monty"])
            print("--- oned, clustered by task (planned, descriptive)")
            Jt, _ = analyse(tag, runs, verbose=False, by_task=True)
            J["by_task_cmp3"] = Jt.get("cmp3_discordant")
            print(J["by_task_cmp3"])
        with open(os.path.join(HERE, f"results_{tag}.json"), "w") as fh:
            json.dump(J, fh, indent=1)


if __name__ == "__main__":
    main()
