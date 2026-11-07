"""generator_control: prints Markdown tables from results/*.json and writes research/generator_control.json. Numbers only.
    .venv/bin/python -I -B research/generator_control/make_report.py"""
import os  # noqa: E402  (release: paths from the repo root)
_REPO = os.environ.get("ARC_MONTY_ROOT", os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")))  # repo root
import json
import os

ROOT = _REPO
HERE = os.path.join(ROOT, "research", "generator_control")
RES = os.path.join(HERE, "results")
NAMES = dict(qwen="Qwen3.8-27B", ice="2020 program", monty="Monty-ARC v5")
RULES = [("top", "Top answer"), ("fit", "Fit"), ("a", "Plain (a)"), ("fa", "(a)+(b)"), ("fc", "(a)+(b)+(c)"), ("v5", "v5 heuristic")]


def load(n):
    p = os.path.join(RES, f"{n}.json")
    return json.load(open(p)) if os.path.exists(p) else None


def pct(x, d=1):
    return "n/a" if x is None else f"{100 * x:.{d}f}"


def num(x):
    return f"{x:.0f}" if abs(x - round(x)) < 1e-9 else f"{x:.2f}"


def ci(c, d=1):
    if c is None or c[0] is None or c[1] is None:
        return "[n/a]"
    return f"[{100 * c[0]:.{d}f}, {100 * c[1]:.{d}f}]"


def sci(c, d=1):
    if c is None or c[0] is None or c[1] is None:
        return "[n/a]"
    return f"[{100 * c[0]:+.{d}f}, {100 * c[1]:+.{d}f}]"


def floor(p):
    if p["answered"] == 0:
        return "n/a"
    f = p["floor"]
    if p["vacuous"]:
        return f"vacuous ({100 * f:.0f}%)"
    lo, hi = p.get("floor_ci") or (None, None)
    s = f"**{100 * f:.1f}%**"
    return s + (f" [{100 * lo:.1f}, {100 * hi:.1f}]" if lo is not None else "")


def rule_table(J):
    out = ["| Rule | Correct/answered | Precision [CI] | Coverage [CI] | Tasks with a wrong answer | Joint P(answer and wrong) [exact CI] | Floor 1 − 0.25/c |", "|---|---|---|---|---|---|---|"]
    for k, lab in RULES:
        p = J["rules"].get(k)
        if p is None:
            continue
        pr = f"{pct(p['precision'])}% {ci(p['ci'])}" if p["answered"] else "n/a"
        out.append(f"| {lab} | {num(p['correct'])}/{p['answered']} | {pr} | {pct(p['coverage'])}% {ci(p['coverage_ci'])} | {p['tasks_wrong']} | {pct(p['joint'], 2)}% {ci(p['joint_cp'], 2)} | {floor(p) if k in ('fa', 'fc') else ''} |")
    return "\n".join(out)


def combined(L):
    out = ["| Learner | Top answer | Fit | (a)+(b) | FA-LOO + (c) | Coverage of + (c) | Joint of + (c) | Floor of + (c) | Mean h − t, points | Exact role p |", "|---|---|---|---|---|---|---|---|---|---|"]
    for n, J in L.items():
        r = J["rules"]
        f = lambda k: f"{num(r[k]['correct'])}/{r[k]['answered']} = {pct(r[k]['precision'])}%" if r[k]["answered"] else "0/0"  # noqa: E731
        e = J["E"]
        ro = J.get("rotation")
        p = "not run" if not ro else f"{ro['exact']['p_two_sided']:.3f}"
        c = r["fc"]
        out.append(f"| {NAMES[n]} | {f('top')} | {f('fit')} | {f('fa')} | {f('fc')} | {pct(c['coverage'])}% {ci(c['coverage_ci'])} | {pct(c['joint'], 2)}% | {floor(c)} | {100 * e['diff']:+.1f} {sci(e['ci'])} | {p} |")
    return "\n".join(out)


def etable(L):
    out = ["| Learner | Folds | Held-out | Test | Difference, points [CI] | CI half-width | Held-out only / test only |", "|---|---|---|---|---|---|---|"]
    for n, J in L.items():
        e = J["E"]
        out.append(f"| {NAMES[n]} | {e['folds']} | {pct(e['held_rate'])}% {ci(e['held_ci'])} | {pct(e['test_rate'])}% {ci(e['test_ci'])} | {100 * e['diff']:+.1f} {sci(e['ci'])} | {100 * e['half_width']:.1f} | {num(e['held_only'])} / {num(e['test_only'])} |")
    return "\n".join(out)


def stable(L):
    out = ["| Learner, fold programs | Predict held-out: right on test | Miss it: right on test | Difference, points [CI] | Within a task, points [CI] (tasks) |", "|---|---|---|---|---|"]
    for n, J in L.items():
        for key, lab in (("split", "with a test answer"), ("split_fit", "and fit what they saw")):
            if n == "monty" and key == "split_fit":
                continue
            s = J[key]
            if not s["pred_n"] and not s["miss_n"]:
                continue
            d = "n/a" if s["diff"] is None else f"{100 * s['diff']:+.1f} {sci(s['diff_ci'])}"
            w = "n/a" if s["within"] is None else f"{100 * s['within']:+.1f} {sci(s['within_ci'])} ({s['within_tasks']})"
            out.append(f"| {NAMES[n]}, {lab} | {pct(s['pred_rate'])}% ({s['pred_n']}) | {pct(s['miss_rate'])}% ({s['miss_n']}) | {d} | {w} |")
    return "\n".join(out)


def rtable(L):
    out = ["| Learner | Tasks | Identity broken | Tasks with 0 / 1 / ≥2 events | Events on the real role (expected) | Wrong FA-LOO not an event | Mean h − t, real role | Null SD | Exact two-sided p | Role-avg (a)+(b): coverage; joint | Role-avg floor | Role-avg + (c): coverage; joint |", "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for n, J in L.items():
        r = J.get("rotation")
        if not r:
            continue
        ev, ex = r["events"], r["exact"]
        fa = r["role_avg_fa"]
        fc = r.get("role_avg_fc")
        fl = "n/a" if fa["floor"] is None else (f"vacuous ({100 * fa['floor']:.0f}%)" if fa["coverage"] <= 0.25 else f"{100 * fa['floor']:.1f}%")
        fcs = "no full runs" if not fc else f"{pct(fc['coverage'])}% {ci(fc['coverage_ci'])}; {pct(fc['joint'], 2)}% {ci(fc['joint_ci'], 2)}"
        out.append(f"| {NAMES[n]} | {r['tasks']} | {r['identity_violations']} | {ev['tasks_0']} / {ev['tasks_1']} / {ev['tasks_2_or_more']} | {ev['on_real_role']} ({ev['expected_real_role']:.2f}) | {ev['wrong_faloo_not_an_event']} | {100 * ex['mean_obs']:+.2f} | {100 * ex['null_sd']:.2f} | {ex['p_two_sided']:.3f} | {pct(fa['coverage'])}% {ci(fa['coverage_ci'])}; {pct(fa['joint'], 2)}% {ci(fa['joint_ci'], 2)} | {fl} | {fcs} |")
    return "\n".join(out)


def main():
    L = {n: load(n) for n in ("qwen", "ice", "monty")}
    L = {n: J for n, J in L.items() if J and J.get("tasks")}
    print("### Combined\n\n" + combined(L) + "\n")
    for n, J in L.items():
        print(f"### {NAMES[n]} ({J['tasks']} of 200 tasks)\n\n" + rule_table(J) + "\n")
    print("### Test of (E), real role, abstain = wrong\n\n" + etable(L) + "\n")
    print("### Held-out split\n\n" + stable(L) + "\n")
    print("### Role rotation\n\n" + rtable(L) + "\n")
    out = dict(L)
    for extra in ("retry", "rep", "stage_c", "monty_direct", "qwen_extras", "ice_repeat"):
        J = load(extra)
        if J:
            out[extra] = J
    chk = os.path.join(HERE, "data", "checks.json")
    if os.path.exists(chk):
        out["data_checks"] = json.load(open(chk))
    with open(os.path.join(ROOT, "research", "generator_control.json"), "w") as fh:
        json.dump(out, fh, indent=1, default=float)


if __name__ == "__main__":
    main()
