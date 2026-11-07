"""generator_control stage C (Addendum 4): Qwen on ConceptARC, first test pair only. Task level, with the unchanged functions of faloo_sampling_analyze.
    python -I -B research/generator_control/analyse_c.py
Writes results/stage_c.json and prints the main numbers."""
import os  # noqa: E402  (release: paths from the repo root)
_REPO = os.environ.get("ARC_MONTY_ROOT", os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")))  # repo root
import json
import os
import random
import sys

ROOT = _REPO
HERE = os.path.join(ROOT, "research", "generator_control")
sys.path.insert(0, os.path.join(ROOT, "research", "arc2"))
sys.path.insert(0, HERE)
import faloo_sampling_analyze as FA  # noqa: E402
from cretry_jobs import MAIN, RETRY, best  # noqa: E402

B = 10000


def pct(xs):
    xs = sorted(xs)
    return xs[int(0.025 * len(xs))], xs[min(len(xs) - 1, int(0.975 * len(xs)))]


def rules(rows, mb, n=160):
    """Fit, (a)+(b), (a)+(b)+(c). rows: task_row outputs, one test pair per task."""
    out = {}
    for name, key, val in (("fit", "full_verified", "full_correct"), ("ab", "faloo", "consensus_correct"), ("abc", "faloo_c", "consensus_correct")):
        xs = [r for r in rows if r.get(key)]
        k = sum(r[val] for r in xs)
        wrong = len(xs) - k
        rng = random.Random(0)
        boot = []
        for _ in range(B):
            s = rng.choices(rows, k=len(rows))
            boot.append(sum(1 for r in s if r.get(key)) / len(rows))
        cov = len(xs) / n
        lo, hi = pct(boot)
        out[name] = dict(right=k, answered=len(xs), exact=FA.clopper_pearson(int(k), len(xs)) if xs else None, coverage=cov, coverage_ci=(lo, hi), wrong=wrong,
                         joint=wrong / n, joint_exact=FA.clopper_pearson(int(wrong), n), floor=(1 - mb / cov) if cov else None,
                         floor_ci=((1 - mb / lo) if lo else None, (1 - mb / hi) if hi else None), vacuous=cov <= mb,
                         wrong_tasks=[r["task"] for r in xs if r[val] < 1])
    return out


def first_pair_views(done, ch, sol):
    """Stage 2's folds, scored on each task's first test pair only: same h, t = right on test:0."""
    out = {}
    for t in sorted(ch):
        recs = [done.get(("fold", t, i)) for i in range(len(ch[t]["train"]))]
        if all(r is not None for r in recs):
            vs = []
            for r in recs:
                v = FA.run_view(r, t, ch, sol)
                vs.append(dict(h=float(v["h"]), t=float(v["tests"][0] == sol[t][0])))
            out[t] = vs
    return out


def mean_diff(vs):
    n = sum(len(x) for x in vs.values())
    return sum(y["h"] - y["t"] for x in vs.values() for y in x) / n


def main():
    full_ch, full_sol = FA.load_concept()
    ch = {t: dict(train=c["train"], test=c["test"][:1]) for t, c in full_ch.items()}
    sol = {t: s[:1] for t, s in full_sol.items()}
    done = best(MAIN)
    tasks = [t for t in sorted(ch) if ("full", t, -1) in done and all(("fold", t, i) in done for i in range(len(ch[t]["train"])))]
    mb = sum(1 / (len(ch[t]["train"]) + 1) for t in tasks) / len(tasks)
    rows = [FA.task_row(t, done, ch, sol) for t in tasks]
    J = dict(label="stage C, Addendum 4", tasks=len(tasks), mean_bound=mb, rules=rules(rows, mb, len(tasks)))
    fv = {t: [dict(FA.run_view(done[("fold", t, i)], t, ch, sol)) for i in range(len(ch[t]["train"]))] for t in tasks}
    P2 = FA.p2_exchangeability(fv)
    J["E"] = {k: P2[k] for k in ("tasks", "folds", "held_right", "test_right", "held_rate", "test_rate", "held_rate_ci", "test_rate_ci", "difference", "difference_ci", "discordant_held_only", "discordant_test_only")}
    J["E"]["half_width"] = (P2["difference_ci"][1] - P2["difference_ci"][0]) / 2
    J["split_verified"] = FA.p1_heldout_inside(fv)
    va = FA.verified_analysis(rows)
    J["verified"] = {k: va[k] for k in ("verified", "fully_right", "not_fully_right", "certified", "wrong_kept", "wrong_rejected", "hypergeom_p_kept_or_fewer")}
    tok = {}
    for k, r in done.items():
        tok[k[0]] = tok.get(k[0], 0) + r.get("gen_tokens", 0)
    rounds = [x for r in done.values() for x in r.get("rounds", [])]
    J["run"] = dict(records=len(done), tokens=tok, rounds=len(rounds), hit_cap=sum(bool(x.get("forced")) for x in rounds), no_code=sum(x.get("n_ok") == -1 for x in rounds),
                    skipped=sum("skipped" in x for x in rounds), max_prompt=max((x.get("prompt_len", 0) for x in rounds), default=0), resumed=sum(r.get("resumed_from_round", 0) > 0 for r in done.values()),
                    vms=sorted({r.get("vm") for r in done.values()}))
    # stage 2 on the same 160 first pairs, and the paired difference by task (comparison added in Addendum 4)
    d2, _ = FA.read_records(FA.STAGE_FILES[2])
    s2 = first_pair_views(d2, full_ch, full_sol)
    s2_all = FA.fold_views(d2, full_ch, full_sol)
    common = [t for t in tasks if t in s2]
    here = {t: [dict(h=float(v["h"]), t=float(v["t"])) for v in fv[t]] for t in common}
    rng = random.Random(0)
    bs, bh, bd = [], [], []
    for _ in range(B):
        idx = rng.choices(common, k=len(common))
        a = sum(y["h"] - y["t"] for t in idx for y in s2[t])
        b = sum(y["h"] - y["t"] for t in idx for y in here[t])
        n = sum(len(s2[t]) for t in idx)
        bs.append(a / n)
        bh.append(b / n)
        bd.append((b - a) / n)
    J["vs_stage2"] = dict(stage2_all_three=mean_diff({t: [dict(h=float(y["h"]), t=y["t"]) for y in s2_all[t]] for t in s2_all}),
                          stage2_first_pair=mean_diff({t: s2[t] for t in common}), stage2_first_pair_ci=pct(bs), here=mean_diff(here), here_ci_same_resamples=pct(bh),
                          c_minus_stage2_first_pair=mean_diff(here) - mean_diff({t: s2[t] for t in common}), c_minus_ci=pct(bd), tasks=len(common))
    # retries
    rec = best(RETRY)
    new = dict(done)
    per = dict(not_fitting=0, retried_1=0, fit_1=0, retried_2=0, fit_2=0, never=0, runs=0, tokens=0)
    incomplete = 0
    for t in tasks:
        if not FA.learner_output(done[("full", t, -1)])[1]:
            continue
        for i in range(len(ch[t]["train"])):
            if FA.learner_output(done[("fold", t, i)])[1]:
                continue
            per["not_fitting"] += 1
            got = None
            r1 = rec.get(("retry", t, i * 100 + 1))
            if r1 is None:
                incomplete += 1
            for att in (1, 2):
                r = rec.get(("retry", t, i * 100 + att))
                if r is None:
                    continue
                per[f"retried_{att}"] += 1
                per["runs"] += 1
                per["tokens"] += r.get("gen_tokens", 0)
                if FA.learner_output(r)[1]:
                    per[f"fit_{att}"] += 1
                    got = dict(r, kind="fold", fold=i)
                    break
            if got is None:
                per["never"] += 1
            else:
                new[("fold", t, i)] = got
    J["retry"] = dict(per=per, incomplete_folds=incomplete)
    if rec:
        r2 = [FA.task_row(t, new, ch, sol) for t in tasks]
        J["retry"]["rules"] = rules(r2, mb, len(tasks))
        va2 = FA.verified_analysis(r2)
        J["retry"]["verified"] = {k: va2[k] for k in ("verified", "fully_right", "not_fully_right", "certified", "wrong_kept", "wrong_rejected", "hypergeom_p_kept_or_fewer")}
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    with open(os.path.join(HERE, "results", "stage_c.json"), "w") as fh:
        json.dump(J, fh, indent=1, default=float)
    show = {k: v for k, v in J.items() if k != "split_verified"}
    sp = J["split_verified"]
    show["split"] = dict(hit=sp["predict_held"], miss=sp["miss_held"], diff=sp["difference"], ci=sp["difference_ci"], per_task=sp["per_task"])
    print(json.dumps(show, indent=0, default=float))


if __name__ == "__main__":
    main()
