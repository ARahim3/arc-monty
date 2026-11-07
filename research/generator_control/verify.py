"""generator_control: independent recount of the main counts from raw files, by separate code from analyse.py. No rule code is shared with it:
tasks are read afresh, canonical order and rules are re-derived here. Reads VM results as data.
    .venv/bin/python -I -B research/generator_control/verify.py [qwen ice monty direct]
direct: a real run of frozen Monty-ARC on 20 random tasks (real role) against the re-vote, and the same with the demonstrations reversed."""
import os  # noqa: E402  (release: paths from the repo root)
_REPO = os.environ.get("ARC_MONTY_ROOT", os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")))  # repo root
import json
import os
import random
import sys

ROOT = _REPO
HERE = os.path.join(ROOT, "research", "generator_control")
RES = os.path.join(HERE, "results")


def tasks():
    out = {}
    for fn in sorted(os.listdir(os.path.join(HERE, "data", "tasks"))):
        with open(os.path.join(HERE, "data", "tasks", fn)) as fh:
            out[fn[:-5]] = json.load(fh)
    return out


def order_key(g):
    return (len(g) * len(g[0]), len(g), len(g[0]), json.dumps(g))


def recount(per_task):
    """per_task: tid -> dict(full, fit, folds=[(held_right, test_answer)], truth). Counts by the rules' definitions."""
    c = dict(tasks=len(per_task), top=[0, 0], fit=[0, 0], a=[0, 0], fa=[0, 0], fc=[0, 0], h=0, t=0, folds=0)
    for v in per_task.values():
        truth, full, fit = v["truth"], v["full"], v["fit"]
        fs = v["folds"]
        if full is not None:
            c["top"][1] += 1
            c["top"][0] += full == truth
            if fit:
                c["fit"][1] += 1
                c["fit"][0] += full == truth
        a = all(h for h, _ in fs)
        answers = [t for _, t in fs]
        agree = all(t is not None for t in answers) and all(t == answers[0] for t in answers)
        c["h"] += sum(bool(h) for h, _ in fs)
        c["t"] += sum(t is not None and t == truth for t in answers)
        c["folds"] += len(fs)
        if a and full is not None:
            c["a"][1] += 1
            c["a"][0] += full == truth
        if a and agree:
            c["fa"][1] += 1
            c["fa"][0] += answers[0] == truth
            if v.get("c_needs_fit", False) and not fit:
                continue
            if full is not None and full == answers[0]:
                c["fc"][1] += 1
                c["fc"][0] += answers[0] == truth
    return c


def from_analyse(name):
    J = json.load(open(os.path.join(RES, f"{name}.json")))
    out = {k: [round(J["rules"][k]["correct"]), J["rules"][k]["answered"]] for k in ("top", "fit", "a", "fa", "fc")}
    out.update(tasks=J["tasks"], h=round(J["E"]["held"]), t=round(J["E"]["test"]), folds=J["E"]["folds"])
    return out


def compare(name, mine, fields=("top", "fit", "a", "fa", "fc", "tasks", "h", "t", "folds")):
    theirs = from_analyse(name)
    diff = {k: (mine[k], theirs[k]) for k in fields if mine[k] != theirs[k]}
    print(name, "recount", {k: mine[k] for k in fields})
    print(name, "MATCH" if not diff else f"DIFF {diff}")
    return not diff


def last_program_output(rec):
    best = None
    for r in rec.get("rounds", []):
        if "test_out" not in r:
            continue
        if r.get("verified"):
            return r["test_out"], True
        best = r["test_out"]
    return best, False


def qwen():
    T = tasks()
    recs = {}
    for line in open(os.path.join(HERE, "raw", "gc_qwen_main.jsonl"), errors="replace"):
        try:
            r = json.loads(line)
        except Exception:
            continue
        if "error" in r:
            continue
        k = (r["kind"], r["task_id"], r["fold"])
        if k not in recs or r["started_at"] < recs[k]["started_at"]:
            recs[k] = r
    per = {}
    for tid, t in T.items():
        demos = sorted(t["train"], key=lambda p: order_key(p["input"]))
        if ("full", tid, -1) not in recs or any(("fold", tid, i) not in recs for i in range(3)):
            continue
        fo, fv = last_program_output(recs[("full", tid, -1)])
        folds = []
        for i in range(3):
            rec = recs[("fold", tid, i)]
            o, _ = last_program_output(rec)
            ans = {} if o is None else {q: g for q, g in zip(rec["query_ids"], o)}
            folds.append((ans.get(f"demo:{i}") == demos[i]["output"] and ans.get(f"demo:{i}") is not None, ans.get("test:0")))
        per[tid] = dict(truth=t["test"][0]["output"], full=None if fo is None else fo[0], fit=fv, folds=folds, c_needs_fit=True)
    return compare("qwen", recount(per))


def parse_answer(s):
    rows = s.strip("|").split("|")
    return [[int(c) for c in row] for row in rows]


def ice():
    T = tasks()
    lines = {}
    raw = os.path.join(HERE, "ice", "raw")
    for fn in sorted(os.listdir(raw)):
        if not fn.endswith(".jsonl"):
            continue
        for line in open(os.path.join(raw, fn), errors="replace"):
            try:
                r = json.loads(line)
                k = (r["rid"], int(r["cfg"]))
            except Exception:
                continue
            lines.setdefault(k, r)

    def answer(rid):
        """(top grid or None, its score, all four records present?)"""
        recs = [lines.get((rid, c)) for c in (3, 23, 33, 4)]
        if any(x is None for x in recs):
            return None, None, False
        cands = []
        for x in recs:
            if x.get("status") == "ok":
                for img, sc in x.get("lines", []):
                    if float(sc) >= 0:
                        cands.append((float(sc), img))
        if not cands:
            return None, None, True
        sc, img = max(cands)
        return parse_answer(img), sc, True

    per = {}
    with open(os.path.join(HERE, "ice", "export", "items_rearc.jsonl")) as fh:
        for line in fh:
            it = json.loads(line)
            full, sc, ok = answer(it["full"])
            folds, complete = [], ok
            for x in it["folds"]:
                h, _, a = answer(x["held_rid"])
                t, _, b = answer(x["test_rid"])
                complete = complete and a and b
                folds.append((h is not None and h == x["held_truth"], t))
            if complete:
                per[it["task"]] = dict(truth=it["truth"], full=full, fit=(sc is not None and sc > 3 - 0.499), folds=folds)
    return compare("ice", recount(per))


def monty():
    """Re-derive the rules from the cache's fold and full top answers with the frozen vote code only (not rules.py)."""
    sys.path.insert(0, os.path.join(ROOT, "research", "monty_heldout"))
    from hl_common import items_from_dir  # noqa: F401  (sets sys.path and thread limits)
    import numpy as np
    from arcmonty import vote
    per = {}
    order = ["self-model", "periodic", "behavior", "dynamics", "composition", "association", "pattern", "field"]
    for line in open(os.path.join(HERE, "monty", "cache", "rearc_p0.jsonl")):
        row = json.loads(line)
        grids = [np.array(g, dtype=np.int8) for g in row["grids"]]

        def top(run):
            C = []
            for m in order:
                for c in row["runs"][run].get(m, {"cands": []})["cands"]:
                    C.append(dict(lm=c["lm"], hyp=c["hyp"], evidence=c["ev"], preds=[grids[i] for i in c["p"]]))
            best = vote.pool(C)
            return best[0]["preds"] if best else None

        tid = row["task"].split("#")[0]
        task = json.load(open(os.path.join(HERE, "data", "tasks", tid + ".json")))
        pool = task["train"] + task["test"]
        truth = task["test"][0]["output"]
        f = top("F3")
        folds = []
        for b in range(3):
            p = top(f"3,{b}")
            if p is None:
                folds.append((False, None))
            else:
                folds.append((p[0].tolist() == pool[b]["output"], p[1].tolist()))
        per[tid] = dict(truth=truth, full=None if f is None else f[0].tolist(), fit=False, folds=folds)
    c = recount(per)
    theirs = from_analyse("monty")
    fields = ("top", "a", "fa", "fc", "tasks", "h", "t", "folds")
    diff = {k: (c[k], theirs[k]) for k in fields if c[k] != theirs[k]}
    print("monty recount", {k: c[k] for k in fields})
    print("monty", "MATCH" if not diff else f"DIFF {diff}")
    return not diff


def direct():
    """A real run of the frozen system on 20 random tasks against the re-vote; then the same with the demonstrations reversed."""
    sys.path.insert(0, os.path.join(ROOT, "research", "monty_heldout"))
    from hl_common import h, items_from_dir
    from arcmonty import behavior, monty_arc, symmetry, vote
    items = items_from_dir(os.path.join(HERE, "data", "tasks"))
    res = {}
    with open(os.path.join(HERE, "monty", "results", "rearc_base.jsonl")) as fh:
        for line in fh:
            r = json.loads(line)
            res[r["task"]] = r
    random.seed(0)
    sample = random.sample(items, 20)
    checks, bad, rev_bad = 0, 0, 0

    def top(train, queries):
        symmetry._CACHE.clear()
        behavior._SEG_CACHE.clear()
        C = monty_arc.candidates({"train": train, "test": queries}, perspectives=(0,))
        b = vote.pool(C)
        return b[0]["preds"] if b else None

    for k, pool in sample:
        o = res[k]["cfg"]["full"]["3"]
        tr, x = pool[:3], pool[3][0]
        f = top(tr, [x])
        fr = top(tr[::-1], [x])
        checks += 1
        bad += (None if f is None else h(f[0])) != o["full_h"]
        rev_bad += (None if fr is None else h(fr[0])) != o["full_h"]
        for b in range(3):
            rest = [p for j, p in enumerate(tr) if j != b]
            p = top(rest, [pool[b][0], x])
            pr = top(rest[::-1], [pool[b][0], x])
            want = o["fold_h"][str(b)]
            checks += 1
            bad += (None if p is None else [h(p[0]), h(p[1])]) != want
            rev_bad += (None if pr is None else [h(pr[0]), h(pr[1])]) != want
    print(f"direct: {checks} answers on {len(sample)} tasks; differ from the re-vote: {bad}; with demonstrations reversed: {rev_bad}")
    with open(os.path.join(RES, "monty_direct.json"), "w") as fh:
        json.dump(dict(tasks=len(sample), answers=checks, differ=bad, differ_reversed=rev_bad), fh)


def addon_counts(full_of, fold_recs, retry_recs, ch, sol, tasks):
    """Task level, by separate code from task_row: (a) every fold's chosen sample predicts its held-out demonstration; (b) all folds give the same complete
    tuple of test outputs; (c) the full run verified and gives that tuple. A fold's chosen sample: the first that fits, else the first sample."""
    ab, abc, ab_right, abc_right, wrong_kept, wrong = 0, 0, 0.0, 0.0, 0, 0
    for t in tasks:
        task, s = ch[t], sol[t]
        demos = sorted(task["train"], key=lambda p: order_key(p["input"]))
        nt = len(task["test"])
        fo, fv = last_program_output(full_of(t))
        fd = dict(zip(full_of(t)["query_ids"], fo)) if fo is not None else {}
        ftuple = [fd.get(f"test:{k}") for k in range(nt)]
        fright = sum(g == s[k] for k, g in enumerate(ftuple)) / nt
        if fv and fright < 1:
            wrong += 1
        tuples, a = [], True
        for i in range(len(demos)):
            chain = [fold_recs(t, i)] + [retry_recs(t, i, att) for att in (1, 2)]
            chain = [r for r in chain if r is not None]
            chosen = next((r for r in chain if last_program_output(r)[1]), chain[0])
            o, _ = last_program_output(chosen)
            d = dict(zip(chosen["query_ids"], o)) if o is not None else {}
            a = a and d.get(f"demo:{i}") is not None and d.get(f"demo:{i}") == demos[i]["output"]
            tuples.append([d.get(f"test:{k}") for k in range(nt)])
        b = all(g is not None for g in tuples[0]) and all(x == tuples[0] for x in tuples)
        if a and b:
            r = sum(g == s[k] for k, g in enumerate(tuples[0])) / nt
            ab += 1
            ab_right += r
            if fv and ftuple == tuples[0]:
                abc += 1
                abc_right += r
                wrong_kept += r < 1
    return dict(ab=ab, ab_right=round(ab_right, 2), abc=abc, abc_right=round(abc_right, 2), wrong=wrong, wrong_kept=wrong_kept)


def addons():
    """The add-on (retry.json) and the replication (rep.json), recounted."""
    d = os.path.join(ROOT, "data", "kaggle_format")
    ch, sol = json.load(open(os.path.join(d, "agi2_eval_challenges.json"))), json.load(open(os.path.join(d, "agi2_eval_solutions.json")))

    def read(path):
        out = {}
        for line in open(path, errors="replace"):
            try:
                r = json.loads(line)
            except Exception:
                continue
            if "error" in r:
                continue
            k = (r["kind"], r["task_id"], r["fold"])
            if k not in out or r["started_at"] < out[k]["started_at"]:
                out[k] = r
        return out

    res = os.path.join(ROOT, "llm", "results")
    s1 = read(os.path.join(res, "qwen38_faloo_sampling_b32768.jsonl"))
    s1b = read(os.path.join(res, "qwen38_faloo_sampling_plain_b32768.jsonl"))
    rt = read(os.path.join(HERE, "raw", "gc_qwen_retry.jsonl"))
    rp = read(os.path.join(HERE, "raw", "gc_qwen_rep.jsonl"))
    first = addon_counts(lambda t: s1[("full", t, -1)], lambda t, i: s1[("fold", t, i)], lambda t, i, a: rt.get(("retry", t, i * 100 + a)), ch, sol, sorted(ch))
    v1 = sorted(t for t in ch if last_program_output(s1b[("plain", t, 1)])[1])
    second = addon_counts(lambda t: s1b[("plain", t, 1)], lambda t, i: rp[("rep", t, i * 100)], lambda t, i, a: rp.get(("rep", t, i * 100 + a)), ch, sol, v1)
    no_retry = addon_counts(lambda t: s1b[("plain", t, 1)], lambda t, i: rp[("rep", t, i * 100)], lambda t, i, a: None, ch, sol, v1)
    R, P = json.load(open(os.path.join(RES, "retry.json"))), json.load(open(os.path.join(RES, "rep.json")))
    print("add-on recount", first, "| analyse: abc", R["retry"]["abc"]["answered"], R["retry"]["abc"]["correct"], "ab", R["retry"]["ab"]["answered"], R["retry"]["ab"]["correct"], "wrong kept", R["retry_verified"]["wrong_kept"], "of", R["retry_verified"]["not_fully_right"])
    print("replication recount", second, "| analyse: abc", P["primary"]["abc_answered"], P["primary"]["abc_right"], "ab", P["primary"]["ab_answered"], P["primary"]["ab_right"], "wrong kept", P["primary"]["wrong_kept"], "of", P["primary"]["verified_wrong"])
    print("no-retry recount", no_retry, "| analyse: abc", P["no_retry_same_runs"]["abc_answered"], "ab", P["no_retry_same_runs"]["ab_answered"])


def rot():
    """Qwen's rotation, by separate code from analyse.py: all 6 models per task, events, role-averaged (a)+(b), and the exact role test by dictionary convolution."""
    T = tasks()
    recs = {}
    for fn in ("gc_qwen_main.jsonl", "gc_qwen_rot.jsonl"):
        for line in open(os.path.join(HERE, "raw", fn), errors="replace"):
            try:
                r = json.loads(line)
            except Exception:
                continue
            if "error" in r:
                continue
            k = (r["kind"], r["task_id"], r["fold"])
            if k not in recs or r["started_at"] < recs[k]["started_at"]:
                recs[k] = r
    answered, wrong, events, multi, wrong_not_event, broken = 0, 0, 0, 0, 0, 0
    null = {0: 1.0}
    observed = 0
    for tid, t in T.items():
        demos = sorted(t["train"], key=lambda p: order_key(p["input"]))
        y = [d["output"] for d in demos] + [t["test"][0]["output"]]
        pred = {}
        for i in range(3):
            rec = recs[("fold", tid, i)]
            o, _ = last_program_output(rec)
            d = {} if o is None else dict(zip(rec["query_ids"], o))
            pred[(i, 3)] = {i: d.get(f"demo:{i}"), 3: d.get("test:0")}
        for k, (i, j) in enumerate([(0, 1), (0, 2), (1, 2)]):
            rec = recs[("rot", tid, k)]
            o, _ = last_program_output(rec)
            d = {} if o is None else dict(zip(rec["query_ids"], o))
            pred[(i, j)] = {i: d.get(f"demo:{i}"), j: d.get(f"demo:{j}")}
        D, ev = [], 0
        for r in range(4):
            hs, ts, answers = [], [], []
            for i in range(4):
                if i == r:
                    continue
                m = pred[(min(i, r), max(i, r))]
                hs.append(m[i] is not None and m[i] == y[i])
                ts.append(m[r] is not None and m[r] == y[r])
                answers.append(m[r])
            D.append(sum(hs) - sum(ts))
            e = all(a and not b for a, b in zip(hs, ts))
            ev += e
            if all(hs) and all(a is not None for a in answers) and all(a == answers[0] for a in answers):
                answered += 1
                if answers[0] != y[r]:
                    wrong += 1
                    wrong_not_event += not e
        events += ev
        multi += ev > 1
        broken += sum(D) != 0
        observed += D[3]
        nxt = {}
        for s, p in null.items():
            for v in D:
                nxt[s + v] = nxt.get(s + v, 0.0) + p / 4
        null = nxt
    pv = sum(p for s, p in null.items() if abs(s) >= abs(observed))
    print(dict(answered=answered, wrong=wrong, events=events, tasks_with_two=multi, wrong_not_event=wrong_not_event, identity_broken=broken, S_obs=observed, exact_p=round(pv, 4)))
    r = json.load(open(os.path.join(RES, "qwen.json")))["rotation"]
    print("analyse:", r["role_avg_fa"]["answered"], r["role_avg_fa"]["wrong"], r["events"]["events"], r["events"]["tasks_2_or_more"], r["events"]["wrong_faloo_not_an_event"], r["identity_violations"], r["exact"]["S_obs"], round(r["exact"]["p_two_sided"], 4))


def stagec():
    """Stage C, by separate code from analyse_c.py: reads tasks and raw files afresh, h and t over all folds, rule counts with and without retries."""
    d = os.path.join(ROOT, "external", "judge", "conceptarc", "repo", "corpus")
    ch, sol = {}, {}
    for g in sorted(os.listdir(d)):
        if not os.path.isdir(os.path.join(d, g)):
            continue
        for fn in sorted(os.listdir(os.path.join(d, g))):
            if fn.endswith(".json"):
                t = json.load(open(os.path.join(d, g, fn)))
                k = f"{g}/{fn[:-5]}"
                ch[k] = dict(train=t["train"], test=[dict(input=t["test"][0]["input"])])
                sol[k] = [t["test"][0]["output"]]

    def read(path):
        out = {}
        for line in open(path, errors="replace"):
            try:
                r = json.loads(line)
            except Exception:
                continue
            if "error" not in r:
                k = (r["kind"], r["task_id"], r["fold"])
                if k not in out or r["started_at"] < out[k]["started_at"]:
                    out[k] = r
        return out

    m = read(os.path.join(HERE, "raw", "gc_qwen_c1.jsonl"))
    rt = read(os.path.join(HERE, "raw", "gc_qwen_c1_retry.jsonl"))
    h = t = F = 0
    for k, c in ch.items():
        demos = sorted(c["train"], key=lambda p: order_key(p["input"]))
        for i in range(len(demos)):
            rec = m[("fold", k, i)]
            o, _ = last_program_output(rec)
            q = dict(zip(rec["query_ids"], o)) if o is not None else {}
            h += q.get(f"demo:{i}") is not None and q.get(f"demo:{i}") == demos[i]["output"]
            t += q.get("test:0") is not None and q.get("test:0") == sol[k][0]
            F += 1
    tasks = sorted(ch)
    fo = lambda k: m[("full", k, -1)]  # noqa: E731
    print("recount h, t, folds", h, t, F, "diff", round(100 * (h - t) / F, 2))
    print("no retries", addon_counts(fo, lambda k, i: m[("fold", k, i)], lambda k, i, a: None, ch, sol, tasks))
    print("with retries", addon_counts(fo, lambda k, i: m[("fold", k, i)], lambda k, i, a: rt.get(("retry", k, i * 100 + a)), ch, sol, tasks))


def main():
    which = sys.argv[1:] or ["qwen", "ice", "monty"]
    for w in which:
        dict(qwen=qwen, ice=ice, monty=monty, direct=direct, addons=addons, rot=rot, stagec=stagec)[w]()


if __name__ == "__main__":
    main()
