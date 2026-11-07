"""Finisher pass. Independent recount of every 2020-program number in paper.md from the raw run lines, plus the within-task control.
Written without importing analyse.py, revise_ice.py or stats.py. Raw lines and the sets on disk are parsed as data; nothing third-party is executed.
Output: ../finish_ice.txt (stdout) and ../finish_ice.json"""
import os  # noqa: E402  (release: paths from the repo root)
_REPO = os.environ.get("ARC_MONTY_ROOT", os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..")))  # repo root
import collections, glob, json, os, sys
import numpy as np
from scipy import stats as st
R = (_REPO + "/")
ICE = R + "research/icecuber_faloo/"
OUT = {}
B = 10000


def pct(x):
    x = np.asarray(x, float); x = x[~np.isnan(x)]
    return float(np.percentile(x, 2.5)), float(np.percentile(x, 97.5))


def wts(T):
    return np.random.default_rng(0).multinomial(T, np.full(T, 1 / T), size=B)


def fm(x, ci=None, s=True):
    f = (lambda v: f"{100*v:+.1f}") if s else (lambda v: f"{100*v:.1f}")
    return f(x) + (f" [{f(ci[0])}, {f(ci[1])}]" if ci else "")


# ---------------------------------------------------------------- raw lines
raw = collections.defaultdict(dict); dup = dup_diff = bad = 0
for p in sorted(glob.glob(ICE + "raw/runs_*.jsonl")):
    with open(p, errors="replace") as fh:
        for line in fh:
            try:
                r = json.loads(line)
            except Exception:
                bad += 1; continue
            k = int(r["cfg"])
            if k in raw[r["rid"]]:
                dup += 1
                if raw[r["rid"]][k].get("lines") != r.get("lines") or raw[r["rid"]][k].get("status") != r.get("status"):
                    dup_diff += 1
                continue
            raw[r["rid"]][k] = r
print(f"rids {len(raw)}, with all four configurations {sum(set(v) == {3, 23, 33, 4} for v in raw.values())}, malformed {bad}, duplicate lines {dup}, of which differ {dup_diff}")
stat = collections.Counter((r["set"], c, r.get("status")) for v in raw.values() for c, r in v.items())


def ok_img(s):
    if not (isinstance(s, str) and s.startswith("|") and s.endswith("|") and len(s) > 2):
        return False
    rows = s[1:-1].split("|")
    return all(x.isdigit() for x in rows) and len({len(x) for x in rows}) == 1


def merged(rid):
    """All answer lines of processes that finished, by (score, image) descending, first three distinct images; negative scores are the no-candidate placeholder."""
    if rid is None or rid not in raw or set(raw[rid]) != {3, 23, 33, 4}:
        return None
    c = []
    for cfg in (3, 23, 33, 4):
        r = raw[rid][cfg]
        if r.get("status") == "ok":
            c += [(float(a), i) for i, a in r.get("lines", []) if float(a) >= 0 and ok_img(i)]
    c.sort(key=lambda t: (t[0], t[1]), reverse=True)
    ans, sc = [], []
    for a, i in c:
        if i not in ans:
            ans.append(i); sc.append(a)
        if len(ans) == 3:
            break
    return dict(ans=ans, sc=sc, nd=raw[rid][3].get("nd"))


M = {rid: merged(rid) for rid in raw}
S = lambda g: "|" + "|".join("".join(map(str, r)) for r in g) + "|"
top = lambda rid: (M[rid]["ans"][0] if rid and M.get(rid) and M[rid]["ans"] else None)


# ---------------------------------------------------------------- sets on disk, and the run list
def gkey(p):
    g = p["input"]; o = p.get("output")
    return (len(g) * len(g[0]), len(g), len(g[0]), json.dumps(g), json.dumps(o))


jobs = {}
for f in ("jobs.jsonl", "jobs_native.jsonl", "jobs_checks.jsonl"):
    with open(ICE + "export/" + f) as fh:
        for l in fh:
            j = json.loads(l); jobs[j["rid"]] = j
print("jobs", len(jobs), "raw rids not in jobs", len(set(raw) - set(jobs)))


def disk(tag):
    d = {}
    if tag in ("concept", "minimal", "mini", "oned"):
        base = {"concept": "external/judge/conceptarc/repo/corpus", "minimal": "external/judge/conceptarc/repo/MinimalTasks", "mini": "external/heldout/mini-arc/data/MiniARC", "oned": "external/heldout/1d-arc/dataset"}[tag]
        for f in glob.glob(R + base + "/**/*.json", recursive=True):
            d[os.path.relpath(f, R + base)[:-5]] = json.load(open(f))
    else:
        ch = json.load(open(R + "data/kaggle_format/agi2_eval_challenges.json")); so = json.load(open(R + "data/kaggle_format/agi2_eval_solutions.json"))
        for t, v in ch.items():
            d[t] = dict(train=v["train"], test=[dict(input=q["input"], output=so[t][i]) for i, q in enumerate(v["test"])])
    return d


def load(tag):
    its = [json.loads(l) for l in open(ICE + f"export/items_{tag}.jsonl")]
    D = disk(tag)
    bad = collections.Counter()
    for it in its:
        t, k = it["key"].rsplit("#", 1); k = int(k)
        task = D.get(t) or D.get(t.split("/")[-1])
        if task is None:
            bad["no task"] += 1; continue
        tr = sorted(task["train"], key=gkey)
        if task["test"][k]["output"] != it["truth"]:
            bad["truth"] += 1
        if len(tr) != it["n"] or len(it["folds"]) != it["n"]:
            bad["n"] += 1
        fj = jobs.get(it["full"])
        if fj is None or fj["train"] != tr or fj["query"] != task["test"][k]["input"]:
            bad["full job"] += 1
        for x in it["folds"]:
            j = x["j"]; rest = tr[:j] + tr[j + 1:]
            if tr[j]["output"] != x["held_truth"]:
                bad["held truth"] += 1
            hj, tj = jobs.get(x["held_rid"]), jobs.get(x["test_rid"])
            if hj is None or hj["train"] != rest or hj["query"] != tr[j]["input"]:
                bad["held job"] += 1
            if tj is None or tj["train"] != rest or tj["query"] != task["test"][k]["input"]:
                bad["test job"] += 1
    print(f"{tag}: items {len(its)}, tasks {len({i['task'] for i in its})}, clusters {len({i['cluster'] for i in its})}; item vs disk mismatches {dict(bad)}")
    return its


def cp(k, n):
    lo = 0 if k == 0 else st.beta.ppf(.025, k, n - k + 1); hi = 1 if k == n else st.beta.ppf(.975, k + 1, n - k)
    return 100 * lo, 100 * hi


MONTY = R + "research/monty_heldout/results/{}_base.jsonl"


def within(rows, B_=B):
    """rows: (cluster-of-control, right, predict). Control per cluster: mean right among predicting minus among missing. Only clusters with both. Mean over clusters, bootstrap over those clusters."""
    g = collections.defaultdict(lambda: [[], []])
    for c, right, pred in rows:
        g[c][0 if pred else 1].append(right)
    both = sorted(c for c, v in g.items() if v[0] and v[1])
    d = np.array([np.mean(g[c][0]) - np.mean(g[c][1]) for c in both], float)
    if not len(d):
        return dict(clusters=0)
    W = wts(len(d)); b = (W @ d) / len(d)
    pos, neg = int((d > 1e-12).sum()), int((d < -1e-12).sum())
    return dict(clusters=len(both), diff=float(d.mean()), ci=pct(b), pos=pos, neg=neg, zero=len(d) - pos - neg, sign_p=float(st.binomtest(pos, pos + neg, .5).pvalue) if pos + neg else None,
                pred_mean=float(np.mean([np.mean(g[c][0]) for c in both])), miss_mean=float(np.mean([np.mean(g[c][1]) for c in both])), n_pred=int(sum(len(g[c][0]) for c in both)), n_miss=int(sum(len(g[c][1]) for c in both)))


def within_two_level(rows):
    """Task-level control, bootstrapped by higher cluster (1D-ARC types): rows (type, task, right, predict). Resample types, keep each type's tasks; statistic = mean over tasks of the resample."""
    g = collections.defaultdict(lambda: [[], []]); ty = {}
    for t, c, right, pred in rows:
        g[c][0 if pred else 1].append(right); ty[c] = t
    both = sorted(c for c, v in g.items() if v[0] and v[1])
    per = collections.defaultdict(list)
    for c in both:
        per[ty[c]].append(np.mean(g[c][0]) - np.mean(g[c][1]))
    types = sorted(per)
    s = np.array([sum(per[t]) for t in types]); n = np.array([len(per[t]) for t in types], float)
    W = wts(len(types))
    with np.errstate(invalid="ignore", divide="ignore"):
        b = (W @ s) / (W @ n)
    typed = np.array([np.mean(per[t]) for t in types])
    Wu = wts(len(types))
    return dict(tasks=len(both), types=len(types), diff=float(s.sum() / n.sum()), ci=pct(b), type_balanced=float(typed.mean()), type_balanced_ci=pct((Wu @ typed) / len(types)), per_type={t: (len(per[t]), round(float(np.mean(per[t])), 3)) for t in types})


def report(tag, name, monty):
    its = load(tag)
    cl = sorted({i["cluster"] for i in its}); ix = {c: i for i, c in enumerate(cl)}; T = len(cl)
    W = wts(T)
    r = {k: np.zeros((T, 2)) for k in ("top", "fit", "a", "ab", "fc")}
    Hs = np.zeros((T, 4)); Hf = np.zeros((T, 4)); EX = np.zeros((T, 5))
    p = [0, 0, 0]; bfail = bright = bwrong = cfail = apass = nofit = has = 0
    fc_key = {}; fc_task = collections.defaultdict(list); mb = []; prows = []; prows_fit = []; irows = []; tyrows = []
    byn = collections.Counter(); why = collections.Counter()
    for it in its:
        i = ix[it["cluster"]]; y = S(it["truth"]); n = it["n"]; mb.append(1 / (n + 1))
        f = M.get(it["full"]); a = f["ans"] if f else []; t0 = a[0] if a else None
        for k in range(3):
            p[k] += y in a[:k + 1]
        if t0 is not None:
            has += 1
            r["top"][i] += (t0 == y, 1)
            if f["sc"][0] > f["nd"] - 0.499:
                r["fit"][i] += (t0 == y, 1)
            else:
                nofit += 1
        hs, ts = [], []
        for x in it["folds"]:
            h, t = top(x["held_rid"]), top(x["test_rid"])
            hs.append(h); ts.append(t)
            hr, tr = (h is not None and h == S(x["held_truth"])), (t is not None and t == y)
            EX[i] += (hr, tr, hr and not tr, tr and not hr, 1)
            if t is not None:
                Hs[i] += (tr * hr, hr, tr * (not hr), not hr)
                prows.append((it["cluster"], float(tr), hr)); irows.append((it["key"], float(tr), hr)); tyrows.append((it["cluster"], it["task"], float(tr), hr))
                fr = M[x["test_rid"]]
                if fr["sc"][0] > fr["nd"] - 0.499:
                    prows_fit.append((it["task"], float(tr), hr))
                    Hf[i] += (tr * hr, hr, tr * (not hr), not hr)
        a_ok = n >= 2 and all(h is not None and h == S(x["held_truth"]) for h, x in zip(hs, it["folds"]))
        agree = n >= 2 and all(t is not None for t in ts) and len(set(ts)) == 1
        if a_ok:
            apass += 1
            if t0 is not None:
                r["a"][i] += (t0 == y, 1)
            if not agree:
                bfail += 1; bright += t0 == y; bwrong += t0 != y
            else:
                r["ab"][i] += (ts[0] == y, 1)
                if t0 == ts[0]:
                    r["fc"][i] += (ts[0] == y, 1)
                    fc_key[it["key"]] = ts[0] == y; fc_task[it["task"]].append(ts[0] == y)
                    byn[("n=2" if n == 2 else "n>=3", ts[0] == y)] += 1
                else:
                    cfail += 1
    N = len(its); mean_b = float(np.mean(mb))
    print(f"\n=== {name} ({tag}): items {N}, clusters {T}, mean 1/(n+1) {100*mean_b:.1f}%, have a top answer {has}")

    def pr(x):
        c, a = x[:, 0].sum(), x[:, 1].sum()
        if not a:
            return "0/0"
        with np.errstate(invalid="ignore", divide="ignore"):
            ci = pct((W @ x[:, 0]) / (W @ x[:, 1]))
        return f"{c:.0f}/{a:.0f} = {100*c/a:.1f}% [{100*ci[0]:.1f}, {100*ci[1]:.1f}]"

    def df(x, y):
        if not x[:, 1].sum() or not y[:, 1].sum():
            return "n/a"
        with np.errstate(invalid="ignore", divide="ignore"):
            b = (W @ x[:, 0]) / (W @ x[:, 1]) - (W @ y[:, 0]) / (W @ y[:, 1])
        return fm(x[:, 0].sum() / x[:, 1].sum() - y[:, 0].sum() / y[:, 1].sum(), pct(b))
    for k, lab in (("top", "top answer"), ("fit", "top answer, fits"), ("a", "plain (a)"), ("ab", "(a)+(b)"), ("fc", "FA-LOO")):
        print(f"  {lab}: {pr(r[k])}; coverage {100*r[k][:,1].sum()/N:.1f}%")
    print(f"  pass@1,2,3 {p}; FA-LOO minus top {df(r['fc'], r['top'])}; minus fit {df(r['fc'], r['fit'])}; minus (a) {df(r['fc'], r['a'])}")
    print(f"  top answers not fitting {nofit} of {has}; (a) passes {apass}; (b) fails {bfail}: right {bright}, wrong {bwrong}; (c) fails {cfail}; FA-LOO wrong {r['fc'][:,1].sum()-r['fc'][:,0].sum():.0f}, joint {100*(r['fc'][:,1].sum()-r['fc'][:,0].sum())/N:.2f}%")
    tk = len(fc_task); tw = sum(not all(v) for v in fc_task.values())
    print(f"  FA-LOO tasks {tk}, with a wrong answer {tw}; clusters answered {(r['fc'][:,1]>0).sum()}; Clopper-Pearson tasks all right {cp(tk-tw, tk) if tk else None}; by n {dict(byn)}")
    if r["fc"][:, 1].sum():
        print(f"  floor {100*(1 - mean_b/(r['fc'][:,1].sum()/N)):.1f}%")
    # Table 5
    with np.errstate(invalid="ignore", divide="ignore"):
        b = (W @ Hs[:, 0]) / (W @ Hs[:, 1]) - (W @ Hs[:, 2]) / (W @ Hs[:, 3])
    print(f"  Table 5: predict {Hs[:,0].sum():.0f}/{Hs[:,1].sum():.0f} = {100*Hs[:,0].sum()/Hs[:,1].sum():.1f}%; miss {Hs[:,2].sum():.0f}/{Hs[:,3].sum():.0f} = {100*Hs[:,2].sum()/Hs[:,3].sum():.1f}%; difference {fm(Hs[:,0].sum()/Hs[:,1].sum()-Hs[:,2].sum()/Hs[:,3].sum(), pct(b))}")
    # Table 4
    d = (W @ (EX[:, 0] - EX[:, 1])) / (W @ EX[:, 4])
    sg = EX[:, 0] - EX[:, 1]; more, less = int((sg > 0).sum()), int((sg < 0).sum())
    print(f"  Table 4: folds {EX[:,4].sum():.0f}; held {100*EX[:,0].sum()/EX[:,4].sum():.1f}% test {100*EX[:,1].sum()/EX[:,4].sum():.1f}%; diff {fm((EX[:,0].sum()-EX[:,1].sum())/EX[:,4].sum(), pct(d))}; held only {EX[:,2].sum():.0f} test only {EX[:,3].sum():.0f}; clusters {more}:{less}, sign p {st.binomtest(more, more+less, .5).pvalue if more+less else None}")
    if tag == "oned":
        tk_ = collections.defaultdict(float)
        for it in its:
            for x in it["folds"]:
                h, t = top(x["held_rid"]), top(x["test_rid"])
                tk_[it["task"]] += float(h is not None and h == S(x["held_truth"])) - float(t is not None and t == S(it["truth"]))
        m_, l_ = sum(v > 0 for v in tk_.values()), sum(v < 0 for v in tk_.values())
        print(f"  Table 4 by task, descriptive: tasks {m_}:{l_}, sign p {st.binomtest(m_, m_ + l_, .5).pvalue:.3f}")
    # within-task control
    J = dict(tag=tag)
    w = within([(c, a, b_) for c, a, b_ in prows]); J["within_cluster"] = w
    print(f"  WITHIN paper's cluster: {w}")
    if tag == "oned":
        w2 = within([(c, a, b_) for _, c, a, b_ in tyrows]); J["within_task"] = w2
        print(f"  WITHIN task, bootstrap over tasks: {w2}")
        w3 = within_two_level(tyrows); J["within_task_by_type"] = w3
        print(f"  WITHIN task, bootstrap over types: {w3}")
    wi = within(irows); J["within_item"] = wi
    print(f"  WITHIN item (task and test pair): {wi}")
    wf = within(prows_fit); J["within_task_fit_only"] = wf
    print(f"  WITHIN task, only fold answers that fit what the fold saw: {wf}")
    OUT[tag] = J
    # overlap with Monty-ARC
    if monty:
        fcm = {}
        for l in open(MONTY.format(monty)):
            x = json.loads(l); o = x["cfg"]["full"][str(x["m"] - 1)]
            if o["fc"] is not None:
                fcm[x["task"]] = float(o["fc"])
        bo = set(fcm) & set(fc_key)
        print(f"  overlap with Monty-ARC FA-LOO ({len(fcm)} answers, right {sum(fcm.values()):.0f}): both {len(bo)} (2020 right {sum(fc_key[k] for k in bo)}, Monty right {sum(fcm[k] for k in bo):.0f}, same? see below); 2020 only {len(set(fc_key)-set(fcm))}, right {sum(fc_key[k] for k in set(fc_key)-set(fcm))}; Monty only {len(set(fcm)-set(fc_key))}, right {sum(fcm[k] for k in set(fcm)-set(fc_key)):.0f}; union {len(set(fcm)|set(fc_key))}")
        if tag == "oned":
            noread = {it["key"] for it in its if not (M.get(it["full"]) and M[it["full"]]["ans"])}
            print(f"  1D-ARC: no full-data answer {len(noread)}; Monty-only answers on those {len((set(fcm)-set(fc_key)) & noread)}; union on readable {len((set(fcm)|set(fc_key)) - noread)}")
    return its


for t, nm, m in (("concept", "ConceptARC", "concept"), ("mini", "Mini-ARC", "mini"), ("oned", "1D-ARC", "oned"), ("minimal", "MinimalTasks", "minimal"), ("agi2", "ARC-AGI-2 eval", None)):
    report(t, nm, m)

# ---------------------------------------------------------------- authors' count, reproduction, native order, checks
sys.path.insert(0, R + "research/monty_heldout")
from xlsx_read import rows as xlrows  # project reader of the authors' sheet
X = xlrows(R + "external/judge/conceptarc/repo/data.xlsx")["Machine Solver Performance"]
hd = X[0]; ci_ = hd.index("First Place ARC-Kaggle")
auth = {}
for row in X[1:]:
    if row and row[0] and "Minimal" not in row[0]:
        auth[(row[0].replace(".json", ""), int(row[1]))] = row[ci_] == "CORRECT"
its = [json.loads(l) for l in open(ICE + "export/items_concept.jsonl")]
mine = {}
for it in its:
    a, b = it["key"].split("/")[1].split("#")
    mine[(a, int(b))] = S(it["truth"]) in M[it["full"]]["ans"][:3]
cm = set(mine) & set(auth)
print(f"\nAuthors' sheet: items {len(auth)}, right {sum(auth.values())}; mine canonical pass@3 {sum(mine.values())}; agree {sum(mine[k]==auth[k] for k in cm)}/{len(cm)} = {100*sum(mine[k]==auth[k] for k in cm)/len(cm):.1f}%")
tr = {it["key"]: S(it["truth"]) for it in its}
nat = {}
for l in open(ICE + "export/jobs_native.jsonl"):
    j = json.loads(l); a, b = j["key"].split("/")[1].split("#")
    nat[(a, int(b))] = tr[j["key"]] in M[j["rid"]]["ans"][:3]
print(f"native order: items {len(nat)}; pass@3 {sum(nat.values())}; agree {sum(nat[k]==auth[k] for k in nat)}/{len(nat)} = {100*sum(nat[k]==auth[k] for k in nat)/len(nat):.1f}%")
six = ["AboveBelow", "Count", "HorizontalVertical", "InsideOutside", "Order", "SameDifferent"]
for g in six:
    print(f"  group {g}: authors' count {sum(v for k, v in auth.items() if k[0].rstrip('0123456789') == g)} of {sum(1 for k in auth if k[0].rstrip('0123456789') == g)}")
rep = rev = rept = revt = revl = 0
for l in open(ICE + "export/jobs_checks.jsonl"):
    j = json.loads(l); a, b = M[j["orig"]]["ans"], M[j["rid"]]["ans"]
    if j["rid"].startswith("chk_rep_"):
        rep += 1; rept += a == b
    else:
        rev += 1; revt += a[:1] == b[:1]; revl += a == b
print(f"checks: repeat {rept} of {rep} same list; reversed top unchanged {revt} of {rev}, whole list {revl}")
wide = 0
for it in [json.loads(l) for l in open(ICE + "export/items_oned.jsonl")]:
    k = it["key"]; t, q = k.rsplit("#", 1)
    d = json.load(open(R + "external/heldout/1d-arc/dataset/" + t + ".json"))
    if max(len(r) for p in d["train"] + d["test"] for g in (p["input"], p["output"]) for r in g) > 30:
        wide += 1
print("1D-ARC tasks with a grid wider than 30 cells:", wide)
print("process statuses:", dict(collections.Counter((k[0], k[2]) for k in stat.elements())))
print("\nWithin-task control, 2020 program, in the paper's format (post hoc; paired difference over clusters with both kinds; 10,000 resamples, seed 0):")
for tag in ("concept", "mini", "minimal", "agi2"):
    w = OUT[tag]["within_cluster"]
    print(f"  {tag}: {fm(w['diff'], w['ci'])}, {w['clusters']} tasks, {w['pos']}:{w['neg']}, ties {w['zero']}, sign p {w['sign_p']:.3g}; predict {100*w['pred_mean']:.1f}% vs miss {100*w['miss_mean']:.1f}%")
w = OUT["oned"]["within_task_by_type"]; w0 = OUT["oned"]["within_task"]; w1 = OUT["oned"]["within_cluster"]
print(f"  oned, by task, resampling types (quoted in the paper): {fm(w['diff'], w['ci'])}, {w['tasks']} tasks in {w['types']} types; resampling tasks {fm(w0['diff'], w0['ci'])}, {w0['pos']}:{w0['neg']}, ties {w0['zero']}, sign p {w0['sign_p']:.3g}; predict {100*w0['pred_mean']:.1f}% vs miss {100*w0['miss_mean']:.1f}%")
print(f"  oned, within type, the paper's cluster (not a within-task control): {fm(w1['diff'], w1['ci'])}, {w1['clusters']} types, {w1['pos']}:{w1['neg']}")
print("  only fold answers that fit what the fold saw (Qwen's verified counterpart):", {t: fm(OUT[t]["within_task_fit_only"]["diff"], OUT[t]["within_task_fit_only"]["ci"]) + f" ({OUT[t]['within_task_fit_only']['clusters']})" for t in ("concept", "mini", "oned", "minimal", "agi2")})
json.dump(OUT, open(R + "research/paper/v8_notes/finish_ice.json", "w"), indent=1, default=float)
