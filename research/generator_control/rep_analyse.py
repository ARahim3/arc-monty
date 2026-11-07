"""generator_control replication (Addendum 2): score fresh folds with retries on ARC-AGI-2, full-data run = logged plain sample 1 of stage 1b. Task level,
with the unchanged task_row of faloo_sampling_analyze. Planned, but on a seen split.
    python -I -B research/generator_control/rep_analyse.py
Writes results/rep.json and prints the primary numbers."""
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
from rep_jobs import rep_records, verified_tasks  # noqa: E402


def score(rows, n_all=120):
    """Primary numbers on the verified tasks."""
    wrong = [r for r in rows if r["full_correct"] < 1]
    abc = [r for r in rows if r.get("faloo_c")]
    ab = [r for r in rows if r.get("faloo")]
    kept = [r for r in abc if r["full_correct"] < 1]
    fr = sum(r["consensus_correct"] == 1 for r in abc)
    return dict(verified=len(rows), verified_right=round(sum(r["full_correct"] for r in rows), 2), verified_wrong=len(wrong),
                abc_answered=len(abc), abc_right=round(sum(r["consensus_correct"] for r in abc), 2), abc_fully_right=fr,
                abc_exact=FA.clopper_pearson(fr, len(abc)) if abc else None, abc_coverage=len(abc) / n_all,
                wrong_kept=len(kept), wrong_rejected=len(wrong) - len(kept), hypergeom_p=FA.hypergeom_le(len(rows), len(wrong), len(abc), len(kept)) if rows else None,
                ab_answered=len(ab), ab_right=round(sum(r["consensus_correct"] for r in ab), 2),
                abc_tasks=sorted(r["task"] for r in abc), ab_tasks=sorted(r["task"] for r in ab),
                abc_wrong_tasks=[dict(task=r["task"], n=r["n_demos"], right=r["consensus_correct"]) for r in abc if r["consensus_correct"] < 1],
                ab_wrong_tasks=[dict(task=r["task"], n=r["n_demos"], right=r["consensus_correct"]) for r in ab if r["consensus_correct"] < 1])


def main():
    tasks, ch, plain = verified_tasks()
    _, sol = FA.load_agi2()
    rec = rep_records()
    base, base0 = {}, {}
    per = dict(folds=0, first_fit=0, retried_1=0, fit_1=0, retried_2=0, fit_2=0, never_fit=0, runs=0, tokens=0, missing=0)
    incomplete = set()
    for t in tasks:
        full = dict(plain[("plain", t, 1)], kind="full", fold=-1)
        base[("full", t, -1)] = full
        base0[("full", t, -1)] = full
        for i in range(len(ch[t]["train"])):
            per["folds"] += 1
            r0 = rec.get((t, i * 100))
            if r0 is None:
                per["missing"] += 1
                incomplete.add(t)
                continue
            per["runs"] += 1
            per["tokens"] += r0.get("gen_tokens", 0)
            first = dict(r0, kind="fold", fold=i)
            base0[("fold", t, i)] = first
            chosen = first
            if FA.learner_output(r0)[1]:
                per["first_fit"] += 1
            else:
                got = None
                for att in (1, 2):
                    r = rec.get((t, i * 100 + att))
                    if r is None:
                        if got is None and (att == 1 or not FA.learner_output(rec.get((t, i * 100 + 1)) or {})[1]):
                            incomplete.add(t)
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
                    chosen = got
            base[("fold", t, i)] = chosen
    done_tasks = [t for t in tasks if t not in incomplete]
    rows = [FA.task_row(t, base, ch, sol) for t in done_tasks]
    rows0 = [FA.task_row(t, base0, ch, sol) for t in done_tasks]
    J = dict(label="planned replication (Addendum 2), ARC-AGI-2 public eval, seen split", tasks_planned=len(tasks), tasks_complete=len(done_tasks), per=per,
             primary=score(rows), no_retry_same_runs=score(rows0))
    # descriptive: overlap with the first run
    p = os.path.join(HERE, "results", "retry.json")
    if os.path.exists(p):
        R = json.load(open(p))
        first_stage = sorted(FA_row_tasks(R))
        J["overlap"] = dict(with_first_run_15=sorted(set(J["primary"]["abc_tasks"]) & set(first_stage)), first_run_n=len(first_stage),
                            only_here=sorted(set(J["primary"]["abc_tasks"]) - set(first_stage)), only_first=sorted(set(first_stage) - set(J["primary"]["abc_tasks"])))
    with open(os.path.join(HERE, "results", "rep.json"), "w") as fh:
        json.dump(J, fh, indent=1, default=float)
    show = {k: v for k, v in J["primary"].items() if not k.endswith("_tasks") or k.endswith("wrong_tasks")}
    print(json.dumps(dict(tasks=J["tasks_complete"], per=per, primary=show, no_retry={k: v for k, v in J["no_retry_same_runs"].items() if k in ("abc_answered", "abc_right", "abc_exact", "ab_answered", "ab_right", "wrong_kept", "hypergeom_p")}, overlap=J.get("overlap")), indent=1, default=float))


def FA_row_tasks(R):
    """The first run's certified tasks: stage 1's 7 plus the add-on's newly certified."""
    done, _ = FA.read_records(FA.STAGE_FILES[1])
    ch, sol = FA.load_agi2()
    base = [t for t in ch if FA.task_row(t, done, ch, sol).get("faloo_c")]
    return set(base) | {x["task"] for x in R["newly_certified"]}


if __name__ == "__main__":
    main()
