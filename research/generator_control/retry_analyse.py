"""generator_control add-on: score learner A' (folds may retry) on ARC-AGI-2 with the unchanged task_row of faloo_sampling_analyze, against stage 1.
POST HOC, on a seen split. A fold's output: the first sample that fits its own n-1 demonstrations; if none fits, the stage-1 output.
    python -I -B research/generator_control/retry_analyse.py
Writes results/retry.json and prints the comparison."""
import os  # noqa: E402  (release: paths from the repo root)
_REPO = os.environ.get("ARC_MONTY_ROOT", os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")))  # repo root
import json
import os
import sys

ROOT = _REPO
HERE = os.path.join(ROOT, "research", "generator_control")
sys.path.insert(0, os.path.join(ROOT, "research", "arc2"))
sys.path.insert(0, HERE)
import faloo_sampling_analyze as FA  # noqa: E402
from retry_jobs import retries  # noqa: E402


def table(rows, n):
    out = {}
    for name, key, val in (("verified", "full_verified", "full_correct"), ("ab", "faloo", "consensus_correct"), ("abc", "faloo_c", "consensus_correct")):
        r = FA.rate(rows, lambda x, k=key: x.get(k), val, n_cov=n)
        k = r["answered"]
        r["cp"] = FA.clopper_pearson(r["fully_right"], k) if k else None
        out[name] = r
    return out


def main():
    done, errs = FA.read_records(FA.STAGE_FILES[1])
    ch, sol = FA.load_agi2()
    rec = retries()
    new = dict(done)
    per = dict(folds_not_fitting=0, retried_1=0, fit_1=0, retried_2=0, fit_2=0, never_fit=0, tokens=0, runs=0)
    changed = {}
    for t in sorted(ch):
        if not FA.learner_output(done[("full", t, -1)])[1]:
            continue
        for i in range(len(ch[t]["train"])):
            if FA.learner_output(done[("fold", t, i)])[1]:
                continue
            per["folds_not_fitting"] += 1
            got = None
            for att in (1, 2):
                r = rec.get((t, i * 100 + att))
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
                per["never_fit"] += 1
            else:
                new[("fold", t, i)] = got
                changed[(t, i)] = got
    r0 = [FA.task_row(t, done, ch, sol) for t in sorted(ch)]
    r1 = [FA.task_row(t, new, ch, sol) for t in sorted(ch)]
    V = lambda rows: [x for x in rows if x.get("full_verified")]  # noqa: E731
    T0, T1 = table(r0, len(r0)), table(r1, len(r1))
    A0, A1 = FA.verified_analysis(r0), FA.verified_analysis(r1)
    keep = ("verified", "fully_right", "not_fully_right", "certified", "wrong_kept", "wrong_rejected", "hypergeom_p_kept_or_fewer")
    newly = [dict(task=x["task"], n=x["n_demos"], right=x["consensus_correct"], folds_changed=sum((x["task"], i) in changed for i in range(x["n_demos"])))
             for x, y in zip(r1, r0) if x.get("faloo_c") and not y.get("faloo_c")]
    lost = [x["task"] for x, y in zip(r1, r0) if y.get("faloo_c") and not x.get("faloo_c")]
    newly_ab = [dict(task=x["task"], right=x["consensus_correct"]) for x, y in zip(V(r1), V(r0)) if x.get("faloo") and not y.get("faloo")]
    # what the retried folds did, among those that now fit
    views = []
    for (t, i), r in changed.items():
        v = FA.run_view(r, t, ch, sol)
        views.append(dict(task=t, fold=i, held=v["h"], test=v["t"]))
    J = dict(label="post hoc, ARC-AGI-2 public eval, seen split", per=per, stage1=T0, retry=T1, stage1_verified=dict((k, A0[k]) for k in keep), retry_verified=dict((k, A1[k]) for k in keep),
             newly_certified=newly, lost_certified=lost, newly_ab_on_verified=newly_ab, retried_folds_now_fitting=len(views),
             of_those_predict_held=sum(x["held"] for x in views), of_those_test_right=round(sum(x["test"] for x in views), 2),
             of_those_predict_held_test_right=round(sum(x["test"] for x in views if x["held"]), 2),
             of_those_miss_held_test_right=round(sum(x["test"] for x in views if not x["held"]), 2))
    joint = sum(1 - x["consensus_correct"] for x in r1 if x.get("faloo_c")) / len(r1)
    J["joint_abc"] = joint
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    with open(os.path.join(HERE, "results", "retry.json"), "w") as fh:
        json.dump(J, fh, indent=1, default=float)
    print(json.dumps({k: J[k] for k in ("per", "stage1_verified", "retry_verified", "newly_certified", "lost_certified", "newly_ab_on_verified", "retried_folds_now_fitting", "of_those_predict_held", "of_those_test_right", "of_those_predict_held_test_right", "of_those_miss_held_test_right", "joint_abc")}, indent=1, default=float))
    for lab, T in (("stage1", T0), ("retry", T1)):
        print(lab, {k: (T[k]["answered"], T[k]["correct"], round(T[k].get("coverage", 0), 4), T[k]["cp"]) for k in T})


if __name__ == "__main__":
    main()
