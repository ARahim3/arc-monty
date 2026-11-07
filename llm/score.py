"""Pass@2 table, token distributions and harness combinations from results/*.jsonl.

    python score.py results/            # prints markdown tables
"""
import glob
import json
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from arcllm.tasks import load_eval, pass2, top2     # noqa: E402


def load(res_dir):
    runs = defaultdict(dict)     # (model, harness, budget) -> {(task, sample): rec}
    for p in glob.glob(os.path.join(res_dir, "*.jsonl")):
        if p.endswith(".ids.jsonl"):
            continue
        for line in open(p):
            try:
                r = json.loads(line)
            except Exception:
                continue
            if "error" in r or "arm" in r or "kind" in r or "model" not in r:
                continue  # research/arc2 arms ("arm") and FA-LOO folds ("kind") share this folder; not benchmark runs
            runs[(r["model"], r["harness"], r["budget"])][(r["task_id"], r["sample"])] = r
    return runs


def direct_cands(recs, tid, n_tests, samples=(0, 1), repaired=False):
    out = []
    for j in range(n_tests):
        cands = []
        for k in samples:
            r = recs.get((tid, k))
            g = r and (r.get("grids") or (repaired and r.get("grids_repaired")))
            if g and j < len(g):
                cands.append(g[j])
        out.append(top2(cands))
    return out


def ps_cands(recs, tid, n_tests, samples=(0, 1)):
    """Verified programs vote first; then unverified by train pairs solved."""
    out = []
    for j in range(n_tests):
        score, grids = {}, {}
        for k in samples:
            r = recs.get((tid, k))
            for rd in (r or {}).get("rounds", []):
                to = rd.get("test_out")
                if not to or j >= len(to) or to[j] is None:
                    continue
                key = json.dumps(to[j])
                grids[key] = to[j]
                s = score.get(key, (0, -1, 0))
                score[key] = (s[0] + bool(rd.get("verified")), max(s[1], rd.get("n_ok", -1)), s[2] + 1)
        ranked = sorted(score, key=lambda x: score[x], reverse=True)
        out.append([(grids[x], score[x][0] > 0) for x in ranked])
    return out


def pct(xs, q):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(q * len(xs)))] if xs else 0


def main():
    res_dir = sys.argv[1] if len(sys.argv) > 1 else "results"
    ch, sol = load_eval()
    n_sub = int(os.environ.get("TASKS_N", "0"))       # restrict to the first N sorted task ids
    if n_sub:
        keep = sorted(ch)[:n_sub]
        ch, sol = {t: ch[t] for t in keep}, {t: sol[t] for t in keep}
        print(f"(restricted to the first {n_sub} sorted tasks)")
    runs = load(res_dir)
    for k in runs:
        runs[k] = {kk: v for kk, v in runs[k].items() if kk[0] in ch}
    rows = []
    for (m, h, b), recs in sorted(runs.items()):
        tids = sorted({t for t, _ in recs})
        if not tids:
            continue
        sub, sub1 = {}, {}
        for t in ch:
            n = len(ch[t]["test"])
            if h == "direct":
                sub[t] = direct_cands(recs, t, n)
                sub1[t] = direct_cands(recs, t, n, samples=(0,))
            else:
                sub[t] = [[g for g, _ in c][:2] for c in ps_cands(recs, t, n)]
                sub1[t] = [[g for g, _ in c][:1] for c in ps_cands(recs, t, n, samples=(0,))]
        s2, _ = pass2(sub, sol)
        s1, _ = pass2(sub1, sol)
        if h == "direct" and any("grids_repaired" in r for r in recs.values()):
            sr, _ = pass2({t: direct_cands(recs, t, len(ch[t]["test"]), repaired=True) for t in ch}, sol)
            nrep = sum(bool(r.get("grids_repaired")) for r in recs.values())
            extra_rep = f"with grid repair {sr:.2f} ({nrep} repaired)"
        else:
            extra_rep = ""
        costs = [r["cost"] for r in recs.values()]
        per_task = defaultdict(int)
        for (t, _), r in recs.items():
            per_task[t] += r["cost"]
        forced = sum(bool(r.get("forced")) or any(x.get("forced") for x in r.get("rounds", []))
                     for r in recs.values())
        extra = extra_rep
        if h == "ps":
            ver = sum(r.get("verified", False) for r in recs.values())
            extra = f"verified samples {ver}"
        rows.append((m, h, b, len(tids), len(recs), s2, s1, pct(costs, .5), sum(costs) / len(costs),
                     pct(costs, .9), max(costs), sum(per_task.values()) / max(len(per_task), 1),
                     forced, extra))
    print(f"| model | harness | budget | tasks | samples | pass@2 (/{len(ch)}) | pass@2 % | pass@1 (s0) | "
          "median tok/sample | mean | p90 | max | mean tok/task (2 samples) | forced | note |")
    print("|" + "---|" * 15)
    for (m, h, b, nt, ns, s2, s1, med, mean, p90, mx, pt, forced, extra) in rows:
        print(f"| {m} | {h} | {b} | {nt} | {ns} | {s2:.2f} | {100 * s2 / len(ch):.1f} | {s1:.2f} | "
              f"{med} | {mean:.0f} | {p90} | {mx} | {pt:.0f} | {forced} | {extra} |")

    # combination: PS verified answer first, then direct answers (same model, same budget)
    print("\nCombinations (PS-verified first, then direct samples):")
    for (m, h, b), recs in sorted(runs.items()):
      for (m2, h2, b2) in sorted(runs):
        if h != "ps" or m2 != m or h2 != "direct":
            continue
        drecs = runs[(m, "direct", b2)]
        sub = {}
        for t in ch:
            n = len(ch[t]["test"])
            pc, dc = ps_cands(recs, t, n), direct_cands(drecs, t, n)
            sub[t] = [top2([g for g, v in pc[j] if v] + dc[j] + [g for g, v in pc[j] if not v])
                      for j in range(n)]
        s, _ = pass2(sub, sol)
        print(f"  {m} ps b{b} verified + direct b{b2} = {s:.2f}/{len(ch)} ({100 * s / len(ch):.1f}%)")

    # cross-model union (oracle-free: attempt_1 from model A, attempt_2 from model B)
    keys = [k for k in runs if k[1] == "direct"]
    models = sorted({k[0] for k in keys})
    if len(models) == 2:
        print("\nCross-model (direct, same budget): sample0 of each model as the two attempts")
        for b in sorted({k[2] for k in keys}):
            if (models[0], "direct", b) in runs and (models[1], "direct", b) in runs:
                ra, rb = runs[(models[0], "direct", b)], runs[(models[1], "direct", b)]
                sub = {t: [top2(direct_cands(ra, t, len(ch[t]["test"]), (0,))[j] +
                                direct_cands(rb, t, len(ch[t]["test"]), (0,))[j])
                           for j in range(len(ch[t]["test"]))] for t in ch}
                s, _ = pass2(sub, sol)
                print(f"  b{b}: {s:.2f}/{len(ch)} ({100 * s / len(ch):.1f}%)")


if __name__ == "__main__":
    main()
