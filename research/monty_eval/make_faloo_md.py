"""WS4 / FA-LOO: research/monty_faloo.md + research/monty_faloo.json from results/faloo.json, module_loo_audit.json,
fold timing, vote_ablation.json and (optional) p8 results."""
import collections
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import BASE_SPLITS, CACHE, MODULES, ROOT, cache_for  # noqa: E402
from make_tables import distinct_items  # noqa: E402

RES = os.path.join(ROOT, "research", "monty_eval", "results")
LABEL = {"agi2-eval": "AGI-2 eval", "new233": "AGI-2 new-train (233)", "agi2-train": "AGI-2 train",
         "agi1-eval": "AGI-1 eval", "agi1-train": "AGI-1 train"}
ORDER = ["agi2-eval", "new233", "agi2-train", "agi1-eval", "agi1-train"]


def load(n):
    p = os.path.join(RES, n)
    return json.load(open(p)) if os.path.exists(p) else None


def fold_cpu():
    out = {}
    for s in BASE_SPLITS:
        path = os.path.join(CACHE, f"folds_p0_{s}.jsonl")
        tot, n = 0.0, 0
        if os.path.exists(path):
            for line in open(path):
                r = json.loads(line)
                tot += sum(m["cpu"] for f in r["folds"] for m in f["mods"].values())
                n += 1
        full = cache_for(s)
        base = sum(sum(m["cpu"] for m in full[k]["mods"].values()) for k in full)
        out[s] = dict(tasks=n, fold_cpu_s=round(tot, 0), full_cpu_s=round(base, 0),
                      ratio=round(tot / base, 2) if base else None, fold_cpu_per_task=round(tot / max(1, n), 2))
    return out


def distinct_summary(F, variant):
    """Aggregate FA-LOO over the 1,147 distinct tasks (rows from the split each task is counted in)."""
    rows = []
    for split, k, _row, _task in distinct_items():
        rr = F["p1"].get(split, {}).get("rows", {}).get(variant)
        if rr is None:
            continue
        r = next((x for x in rr if x["task"] == k), None)
        if r:
            rows.append(dict(r, split=split))
    return rows


def frac(c, n):
    return f"{c:.0f}/{n} ({100 * c / n:.1f}%)" if n else "0/0"


def main():
    F = load("faloo.json")
    A = load("module_loo_audit.json")
    V = load("vote_ablation.json")
    cpu = fold_cpu()
    md = []
    w = md.append
    S = {s: F["p1"][s]["summary"] for s in ORDER if s in F["p1"]}

    # distinct aggregates
    dv = {v: distinct_summary(F, v) for v in ("v5-top", "v5-conf", "p4-top", "p4-conf")}

    def agg(rows):
        a = [r for r in rows if r["answered"]]
        c = [r for r in rows if r["conf"]]
        ac = [r for r in a if r.get("agree_full")]
        return dict(n=len(rows), fa=len(a), fa_c=sum(r["score"] for r in a), conf=len(c),
                    fac=len(ac), fac_c=sum(r["score"] for r in ac), fac_wrong=[r["task"] for r in ac if r["score"] < 1],
                    fac_drop=[r["task"] for r in rows if r["conf"] and not (r["answered"] and r.get("agree_full"))],
                    fac_new=[r["task"] for r in rows if r["answered"] and r.get("agree_full") and not r["conf"]],
                    union=sum(1 for r in rows if (r["answered"] and r.get("agree_full")) or r["conf"]),
                    union_c=sum((r["score"] if (r["answered"] and r.get("agree_full")) else r["conf_score"]) for r in rows
                                if (r["answered"] and r.get("agree_full")) or r["conf"]),
                    conf_c=sum(r["conf_score"] for r in c),
                    both=sum(1 for r in rows if r["answered"] and r["conf"]),
                    drop=[r["task"] for r in rows if r["conf"] and not r["answered"]],
                    new=[r["task"] for r in rows if r["answered"] and not r["conf"]],
                    wrong=[r["task"] for r in a if r["score"] < 1],
                    conf_wrong=[r["task"] for r in c if r["conf_score"] < 1],
                    joint=sum(1 - r["score"] for r in a) / max(1, len(rows)),
                    bound=sum(1 / (r["n"] + 1) for r in rows) / max(1, len(rows)))
    D = {v: agg(rows) for v, rows in dv.items()}
    d = D["v5-top"]
    std = {k: sum(S[s]["v5-top"][k] for s in BASE_SPLITS) for k in ("faloo_answered", "faloo_correct", "conf_answered", "conf_correct", "both")}
    std["fac"] = sum(S[s]["v5-top"]["fa_c"]["answered"] for s in BASE_SPLITS)
    std["fac_c"] = sum(S[s]["v5-top"]["fa_c"]["correct"] for s in BASE_SPLITS)

    w("# Fold-agreement LOO (FA-LOO) for Monty-ARC v5\n")
    w("Frozen v5 code (byte-identical to the published notebook), wrapped from `research/monty_eval/` (`run_folds.py`, "
      "`faloo.py`, `module_loo_audit.py`, `run_persp.py`). Raw: `research/monty_faloo.json`, "
      "`research/monty_eval/results/faloo.json`.\n")
    w("**FA-LOO rule.** Learner A = the full 8-module Monty-ARC v5 system (its top pooled answer; no confidence rule). "
      "For each test input t and each demo i, A is re-run from scratch on the other n-1 demos (every module re-generates "
      "and re-selects its hypotheses: a true re-induction) and queried jointly on (x_i, x*_t), i.e. exactly the "
      "tournament model M_{i,n+1}. Answer y_hat only if (a) every fold model predicts its held-out demo and (b) all n "
      "fold models give the same test answer. A task is answered when every test input is.\n")

    w("## Headline\n")
    w(f"- **FA-LOO + (c) [the full-data system's top answer must equal the fold answer; this only removes answers, so "
      f"the bound still holds]: distinct tasks {frac(d['fac_c'], d['fac'])}, four standard splits "
      f"{frac(std['fac_c'], std['fac'])}, against v5 confident {frac(d['conf_c'], d['conf'])} and "
      f"{frac(std['conf_correct'], std['conf_answered'])}.** Wrong: {', '.join(d['fac_wrong']) or 'none'}. It drops "
      f"{len(d['fac_drop'])} v5 confident answers ({', '.join(d['fac_drop'])}) and adds {len(d['fac_new'])} "
      f"({', '.join(d['fac_new'])}).")
    w(f"- **Distinct tasks (n = {d['n']}): FA-LOO answers {frac(d['fa_c'], d['fa'])}; the v5 confident rule answers "
      f"{frac(d['conf_c'], d['conf'])}.** Both answer {d['both']}; FA-LOO drops {len(d['drop'])} v5 confident answers "
      f"and adds {len(d['new'])}. (v5's top answer has pooled evidence >= 0.99 in 104 distinct tasks, 100 correct; the "
      f"confident rule's 2:1 consensus keeps 98 of them.)")
    w(f"- **Four standard splits (1,920 task instances): FA-LOO {frac(std['faloo_correct'], std['faloo_answered'])} vs "
      f"v5 confident {frac(std['conf_correct'], std['conf_answered'])}.**")
    e2, n2 = S["agi2-eval"]["v5-top"], S["new233"]["v5-top"]
    w(f"- **ARC-AGI-2 only.** AGI-2 eval: FA-LOO + (c) {frac(e2['fa_c']['correct'], e2['fa_c']['answered'])}, v5 "
      f"{frac(e2['conf_correct'], e2['conf_answered'])}; it adds dbff022c, which v5 declines because two fully "
      f"evidenced hypotheses conflict. AGI-2 new-train: {frac(n2['fa_c']['correct'], n2['fa_c']['answered'])} vs "
      f"{frac(n2['conf_correct'], n2['conf_answered'])}; it loses the two n = 2 tasks.")
    P8h = load("p8_full.json")
    if P8h and F.get("p8", {}).get("agi1-train"):
        x8 = F["p8"]["agi1-train"]["summary"]["v5-top"]
        w(f"- **Perspective voting (AGI-1 train, 8 D8 views).** v5 rule: {frac(P8h['agi1-train']['v5 8 views']['correct'], P8h['agi1-train']['v5 8 views']['answered'])} "
          f"(4 false confident answers vs 1 with one view). FA-LOO with the v5 vote: {frac(x8['faloo_correct'], x8['faloo_answered'])}; "
          f"+ (c): {frac(x8['fa_c']['correct'], x8['fa_c']['answered'])}. P4: {frac(P8h['agi1-train']['P4 8 views']['correct'], P8h['agi1-train']['P4 8 views']['answered'])}. "
          "**FA-LOO stops the inflation.**")
    w(f"- Empirical joint rate P(answer and wrong) over distinct tasks: {100 * d['joint']:.2f}% vs the worst-case "
      f"bound mean 1/(n+1) = {100 * d['bound']:.1f}%.")
    tot_fold = sum(c["fold_cpu_s"] for c in cpu.values())
    tot_full = sum(c["full_cpu_s"] for c in cpu.values())
    w(f"- Cost: {tot_fold / 3600:.1f} CPU-hours for all folds of the 1,920 instances, {tot_fold / tot_full:.1f}x a "
      "single v5 pass (n x tests runs per task).\n")

    # ---- 1 per-module verdicts
    w("## 1. Per-module LOO: true re-induction or parameter re-fit after selection on all demos?\n")
    w("| Module | What its LOO re-runs per fold | Selected on all n demos | Verdict | Code |")
    w("|---|---|---|---|---|")
    w("| self-model | nothing: evidence = 1.0 for any configuration that reproduces every demo | configuration (mode, mask colour, "
      "symmetry kinds) | **no LOO** (fit only) | `symmetry.py:209-235` (`evidence=1.0` at :232) |")
    for name, lines, note in (
            ("periodic", "`periodic.py:116-129, 145-155`", "hypothesis list (vanishing colours from all demos)"),
            ("dynamics", "`dynamics.py:64-74, 151-155, 187-191, 210-243`", "hypothesis list (colours, object types from all demos); 3000 cap"),
            ("composition", "`composition.py:67-78, 127, 163-166, 194-216, 237-240, 256-284`", "hypothesis list (ratios, panel count, colours, output shape from all demos); 4000 cap"),
            ("association", "`association.py:42-48, 106-110, 123-153`", "hypothesis list (source colours from all demos)")):
        w(f"| {name} | the *learner* \"first hypothesis in a fixed order fitting the n-1 demos\" | {note} | **learner-level "
          f"re-induction over a leaked hypothesis list; the score is copied to every full-fit hypothesis; (b) not checked** | {lines} |")
    w("| behavior | the change table, for a structure (seg, key, frame, R, ownership) fixed on all n demos | structure: up to "
      "336 per task | **parameter re-fit after selection** (H/(n+1) regime) | `behavior.py:143-168` (filter :156, re-fit :163) |")
    w("| pattern | the pattern library, for a context type fixed on all n demos | context: 3 | **parameter re-fit after "
      "selection** (small H) | `pattern.py:88-108` (filter :97, re-fit :104) |")
    w("| field | the location->colour table, for an (anchor, code, period, write mask) structure fixed on all n demos "
      "(each demo must also fit alone) | structure: hundreds | **parameter re-fit after selection** | `field.py:98-150` "
      "(filter :128-131, re-fit :146) |")
    if A:
        s = A["summary"]
        w("\nMeasured on the 1,147 distinct tasks (`module_loo_audit.py`):\n")
        for m in ("behavior", "pattern", "field"):
            x = s[m]
            w(f"- **{m}**: {x['loo1_candidates']} structure candidates with LOO = 1.0 in {x['tasks']} tasks; condition "
              f"(b) holds automatically (every fold model predicts the test exactly as the full model) for "
              f"{x['b_automatic']}/{x['loo1_candidates']}" + (f"; a fold model meets an unseen object type on the "
              f"test in {x['fold_unseen_on_test']}" if m == "behavior" else "") + ".")
        for m in ("periodic", "dynamics", "composition", "association"):
            x = s[m]
            w(f"- **{m}**: LOO = 1.0 in {x['tasks_loo1']} tasks; {x['multi_distinct']} of them hand the 1.0 to more than one "
              f"distinct prediction (mean {x['mean_full_fit']} full-fit hypotheses); the hypothesis list generated from a "
              f"fold's own n-1 demos differs from the all-demo list in {x['hyp_list_leak']}; fold learners agree on the "
              f"test (b) in {x['b_monty_folds']} with Monty's list and {x['b_true_reinduction']} with true re-induction.")
    # module-alone FA-LOO
    w("\n**Module alone under system-level FA-LOO** (true re-induction of each module; distinct tasks):\n")
    w("| Module | FA-LOO correct / answered | module's own LOO = 1.0 top answers (Table 6 of monty_ablations.md) |")
    w("|---|---|---|")
    mt = load("../../monty_ablations.json") if False else json.load(open(os.path.join(ROOT, "research", "monty_ablations.json")))
    for m in MODULES:
        rows = distinct_summary(F, f"{m} alone")
        a = [r for r in rows if r["answered"]]
        c1 = mt["calibration_distinct"]["by_module"][m]["1.0"]
        w(f"| {m} | {frac(sum(r['score'] for r in a), len(a))} | {frac(c1[1], c1[0])} |")

    # ---- 2 system FA-LOO
    w("\n## 2. System-level FA-LOO vs the v5 confident rule\n")
    w("| Split | FA-LOO (v5 vote, top answer) | v5 confident | both | v5 confident dropped by FA-LOO | new FA-LOO answers | FA-LOO wrong |")
    w("|---|---|---|---|---|---|---|")
    for s in ORDER:
        if s not in S:
            continue
        x = S[s]["v5-top"]
        w(f"| {LABEL[s]} | {frac(x['faloo_correct'], x['faloo_answered'])} | {frac(x['conf_correct'], x['conf_answered'])} | "
          f"{x['both']} | {len(x['conf_dropped'])} | {len(x['faloo_new'])} | {' '.join(x['faloo_wrong']) or '-'} |")
    w(f"| **distinct (1,147), FA-LOO** | **{frac(d['fa_c'], d['fa'])}** | **{frac(d['conf_c'], d['conf'])}** | {d['both']} | "
      f"{len(d['drop'])} | {len(d['new'])} | {' '.join(d['wrong']) or '-'} |")
    w(f"| distinct, FA-LOO + (c) | **{frac(d['fac_c'], d['fac'])}** | {frac(d['conf_c'], d['conf'])} | | {len(d['fac_drop'])} | "
      f"{len(d['fac_new'])} | {' '.join(d['fac_wrong']) or '-'} |")
    w(f"| distinct, FA-LOO + (c) or v5 confident (no bound) | {frac(d['union_c'], d['union'])} | | | | | |")
    w("\nVariants (distinct tasks): " + "; ".join(
        f"*{v}*: FA-LOO {frac(D[v]['fa_c'], D[v]['fa'])}" for v in ("v5-top", "v5-conf", "p4-top", "p4-conf")) +
      ". (*-conf*: each fold model must itself pass the confident rule; *p4*: the P4 vote below.)\n")
    w(f"v5 confident answers dropped by FA-LOO (distinct): {', '.join(d['drop']) or 'none'}. Of the v5 confident "
      f"wrong answers ({', '.join(d['conf_wrong']) or 'none'}), FA-LOO answers: "
      f"{', '.join(t for t in d['conf_wrong'] if t not in d['drop']) or 'none'}.\n")
    w("**What changes, and why** (distinct tasks):\n")
    w("- *Dropped, correctly:* 9565186b, v5's pooling false positive (42 duplicate behavior hypotheses at LOO 0.75): a "
      "fold model mispredicts its held-out demo.")
    w("- *Dropped, correct answers lost to leakage:* 00576224, 8d5021e8, c9e6f938 (composition, per-tile D8 poses). "
      "`_tile_hypotheses` solves the poses on all n demos, so v5's LOO = 1.0 was inflated. Re-induced on n-1 demos, the "
      "pose is ambiguous and one fold picks a pose that is consistent with its demos but wrong on the held-out one.")
    w("- *Dropped, too little data:* aaef0977 (field) and ad38a9d0 (behavior), both n = 2. A one-demo fold cannot "
      "pin down the structure, and a memorising behavior hypothesis wins that fold.")
    w("- *Added (all correct):* tasks where v5's learner-level LOO was 0.67 because one fold's first-fit hypothesis was "
      "another period or tiling, while the whole system's fold answer was right (1d0a4b61, c663677b, ca8f78db, "
      "f823c43c, 1f85a75f, 3aa6fb7a, c3f564a4, cd3c21df, d56f2372). Also dbff022c: two fully evidenced hypotheses "
      "conflict on all demos, so v5 declines, yet every fold agrees.")
    w("- *Wrong under FA-LOO:*")
    w("  - f5aa3634: the bottom-most-object proxy is consistent with every fold. No LOO variant can see a concept "
      "that is missing from the hypothesis space.")
    w("  - 72ca375d: the tournament event itself. Two selection proxies (symmetry, density) fit every demo. Each fold "
      "model picks density, which is first in the property order, predicts its held-out demo and is wrong on the test. "
      "Rule (c) catches it, because the full-data top answer is symmetry, which is correct.\n")
    why = collections.Counter()
    for s in ("agi2-eval", "agi1-eval", "agi1-train", "new233"):
        for r in F["p1"][s]["rows"]["v5-top"]:
            if r["conf"] and not r["answered"]:
                why[r["why"]] += 1
    w("Why v5 confident answers are dropped (distinct): " + ", ".join(f"{k}: {v}" for k, v in why.items()) + ".\n")
    w("**By number of demos (distinct tasks):**\n")
    w("| n demos | tasks | FA-LOO | v5 confident | bound 1/(n+1) |")
    w("|---|---|---|---|---|")
    byn = collections.defaultdict(list)
    for r in dv["v5-top"]:
        byn[r["n"]].append(r)
    for nn in sorted(byn):
        rr = byn[nn]
        a = [r for r in rr if r["answered"]]
        c = [r for r in rr if r["conf"]]
        w(f"| {nn} | {len(rr)} | {frac(sum(r['score'] for r in a), len(a))} | {frac(sum(r['conf_score'] for r in c), len(c))} | {1 / (nn + 1):.3f} |")
    w("\n**CPU cost** (sum of module CPU seconds, M4 Pro, 1 BLAS thread):\n")
    w("| Split | tasks | v5 single pass | all FA-LOO folds | ratio | fold CPU-s per task |")
    w("|---|---|---|---|---|---|")
    for s, c in cpu.items():
        w(f"| {LABEL[s]} | {c['tasks']} | {c['full_cpu_s']:.0f} s | {c['fold_cpu_s']:.0f} s | {c['ratio']}x | {c['fold_cpu_per_task']} |")

    # ---- 3 P4
    w("\n## 3. P4: re-vote without same-module duplicate pooling and without duplicate D8 views\n")
    w("P4 counts voters per module (the 8 perspective views of one module are one voter) and accumulates evidence only "
      "across distinct modules. On v5's single perspective this equals the cross-module rule of `monty_ablations.md` "
      "Table 7.\n")
    w("| Split | v5 confident | P4 confident | FA-LOO with P4 vote |")
    w("|---|---|---|---|")
    for s in ORDER:
        if s not in S:
            continue
        x = S[s]["p4-top"]
        w(f"| {LABEL[s]} | {frac(S[s]['v5-top']['conf_correct'], S[s]['v5-top']['conf_answered'])} | "
          f"{frac(x['conf_correct'], x['conf_answered'])} | {frac(x['faloo_correct'], x['faloo_answered'])} |")
    p4d = D["p4-top"]
    w(f"| **distinct** | {frac(d['conf_c'], d['conf'])} | {frac(p4d['conf_c'], p4d['conf'])} | {frac(p4d['fa_c'], p4d['fa'])} |")

    # ---- 4 perspective voting
    P8 = load("p8_full.json")
    if P8:
        w("\n## 4. Whole-task D8 perspective voting (8 views): does FA-LOO or P4 stop the inflation?\n")
        w("Offline re-vote of a per-module, per-perspective cache (`run_persp.py`, `p8_full.py`). It reproduces the "
          "paper-writer's real 8-view run (`research/paper/data/agi1_train_p8.json`) with 0 confident-flag mismatches "
          "over 400 tasks.\n")
        w("| AGI-1 train (400) | confident correct / answered | wrong |")
        w("|---|---|---|")
        for s_, blk in P8.items():
            for nme in ("v5 1 view", "v5 8 views", "P4 1 view", "P4 8 views"):
                x = blk[nme]
                w(f"| {nme} | {frac(x['correct'], x['answered'])} | {' '.join(x['wrong']) or '-'} |")
            if F.get("p8", {}).get(s_):
                x8 = F["p8"][s_]["summary"]
                for v, lab in (("v5-top", "FA-LOO (v5 vote), 8 views"), ("p4-top", "FA-LOO (P4 vote), 8 views")):
                    w(f"| {lab} | {frac(x8[v]['faloo_correct'], x8[v]['faloo_answered'])} | {' '.join(x8[v]['faloo_wrong']) or '-'} |")
                    w(f"| {lab} + (c) | {frac(x8[v]['fa_c']['correct'], x8[v]['fa_c']['answered'])} | {' '.join(x8[v]['fa_c']['wrong']) or '-'} |")
            x1 = S[s_]["v5-top"]
            w(f"| FA-LOO (v5 vote), 1 view, for reference | {frac(x1['faloo_correct'], x1['faloo_answered'])} | {' '.join(x1['faloo_wrong']) or '-'} |")
        w("\nThe 4 false confident answers that 8-view v5 voting adds (0ca9ddb6, 7447852a, 834ec97d, a5f85a15) are "
          "behaviour answers whose pooled evidence (1.61-2.26) is built by counting the same module's views as separate "
          "voters. P4 (one voter per module, no cross-view accumulation) removes all 4. The error left under P4 at 8 views "
          "(9565186b) is a different mechanism: in some D8 view a behaviour structure reaches a genuine LOO of 1.0 for "
          "the wrong answer. Extra views add *hypotheses* (absolute-frame structures under rotation), not just copies of "
          "votes, and that is the H/(n+1) multiple-comparisons trap.\n")
        w("**FA-LOO stops both mechanisms.** A spurious structure that wins one view on all n demos rarely wins every "
          "fold and agrees on the test, and the view copies cannot raise a fold's top answer above a "
          "held-out-demo failure. With the v5 vote at 8 views, FA-LOO + (c) answers 58/58. Its one plain-FA-LOO error "
          "(72ca375d) is the 1-view tournament case above, unrelated to views. Cost: the 8-view folds took 1,767 s of "
          "wall time on 4 workers for AGI-1 train, about 7x the 1-view folds.\n")
    w("\n## 5. Caveats\n")
    w("- The bound needs the n demos and the test pair to be exchangeable; ARC test inputs are often chosen to be "
      "harder (54d9e175 is a measured case), so on ARC the bound is a heuristic and the measured rate is the evidence.")
    SY = load("sym_check.json")
    sy = "; ".join(f"{LABEL[k]}: top answer identical in {v['top_same']}/{v['n']}, confident flag identical in "
                   f"{v['conf_same']}/{v['n']}" + (f" (differ: {' '.join(v['differ'][:6])})" if v["differ"] else "")
                   for k, v in SY.items()) if SY else "not measured"
    w("- It needs A symmetric in its demo multiset. Monty-ARC's modules build hypothesis lists from sorted colour and "
      "shape sets and order-free tables, so A is symmetric up to tie-breaking order. Measured by reversing the demo "
      f"order (`sym_check.py`): {sy}.")
    w("- Fold models are queried on the pair (x_i, x*_t) jointly (Monty modules only keep hypotheses that predict every "
      "query); this is the same symmetric pair query in both directions of the tournament, so the argument holds.")
    w("- With n = 2 each fold model sees one demo. FA-LOO still answers 15 distinct n = 2 tasks, the same count as "
      "v5 but not the same set: it loses aaef0977 and ad38a9d0 and gains others. On the AGI-2-only training split "
      "(25% of its tasks have n = 2) it keeps 1 of v5's 3 confident answers.")
    w("- A system-level FA-LOO multiplies CPU by about n x (number of tests), measured at 2.6x.")
    with open(os.path.join(ROOT, "research", "monty_faloo.md"), "w") as fh:
        fh.write("\n".join(x for x in md if x is not None) + "\n")
    summary = dict(distinct=D, standard={s: {v: {k: val for k, val in S[s][v].items()} for v in S[s]} for s in S},
                   cpu=cpu, audit=A["summary"] if A else None,
                   p8={s: blk["summary"] for s, blk in F.get("p8", {}).items()},
                   vote_ablation_cross_module={s: V[s]["cross-module"] for s in V} if V else None)
    json.dump(summary, open(os.path.join(ROOT, "research", "monty_faloo.json"), "w"), indent=1, default=float)
    print("wrote research/monty_faloo.md / .json")


if __name__ == "__main__":
    main()
