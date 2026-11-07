"""Judge v8c pass 1: the text edits to research/paper/v8/paper.md, each an exact, once-only replacement.
Text before this pass: research/paper/v8_notes/paper_before_v8c.md. Numbers come from v8c_qwen.txt (own recounts).
    .venv/bin/python research/paper/v8_notes/scripts/v8c_edit.py"""
import os  # noqa: E402  (release: paths from the repo root)
_REPO = os.environ.get("ARC_MONTY_ROOT", os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..")))  # repo root
import re

P = (_REPO + "/research/paper/v8/paper.md")
SRC = (_REPO + "/research/paper/v8_notes/paper_before_v8c.md")
s = open(SRC, encoding="utf8").read()


def rep(old, new, count=1):
    global s
    n = s.count(old)
    assert n == count, (n, old[:90])
    s = s.replace(old, new)


# Header: the exact version goes in at publication time.
rep("Notebook of the named submission: `kaggle.com/code/rahim3/monty-arc-qwen-nvarc`.",
    "Notebook of the named submission (version 3): {{NOTEBOOK_V3_URL}}.")

# Abstract (3.3 items 1, 2, 9).
rep("at most 1/(n+1) for any learner fixed in advance.", "at most 1/(n+1) for any symmetric learner fixed in advance.")
rep("all right: the first case we know of where the bound bites.", "all right: a case where the bound bites.")
rep("inside the band reported for unmodified NVARC forks (Table 1);", "inside the band reported for unmodified NVARC forks [10];")

# Section 2: CORA's held-out split (judge's sentence, checked against the quote) and the CV+ reading of the theorem.
rep("""still predicts the hidden one: 40 of 42 right on ARC-AGI-2 training tasks, and reported as "0 of 11 on an evaluation development split". It checks condition (a) of Section 5 and states no bound.""",
    """still predicts the hidden one, and it reports a held-out split like Section 6.1's: certified programs right 40 of 42 times on ARC-AGI-2 training tasks against 37 of 201 for the same search's uncertified train-perfect programs, and "0 of 11 on an evaluation development split". We extend it to four unrelated learners, with within-task controls, and add agreement (b) and its bound.""")
rep("The proof adapts the leave-two-out tournament of the jackknife+ [12] to exact-match answers with abstention.",
    "The proof adapts the leave-two-out tournament of the jackknife+ [12]. With 0–1 scores, (a)+(b) makes the CV+ (jackknife+) classification set [28] at $\\alpha=1/(n+1)$ the singleton $\\{\\hat y\\}$, so a confident error is a miscoverage, which the jackknife+ bounds by $2\\alpha$; at this $\\alpha$ it is a tournament event only one pair can win, hence $1/(n+1)$.")

# Section 4: the definition matches the counts (3.2 mismatch 1).
rep("*FA-LOO:* conditions (a), (b), (c) of Section 5, around the whole system.",
    "*FA-LOO:* conditions (a), (b), (c) of Section 5, around the whole system; for Qwen, (c) also requires the full run to verify, which matters only on `re-arc` (108/108 at 54.0% without it).")

# 5.1 pointer to Figure 2; 5.2 Figure 2 after the proof.
rep("and, optionally, (c) the model fitted on all $n$ demonstrations also outputs $\\hat y$.",
    "and, optionally, (c) the model fitted on all $n$ demonstrations also outputs $\\hat y$ (Figure 2).")
rep("In words: at most one of a task's $n+1$ pairs, playing test, can produce a confident error.\n",
    "In words: at most one of a task's $n+1$ pairs, playing test, can produce a confident error.\n\n"
    "![**Figure 2. FA-LOO on one task, and the proof's table for $n=3$.** Cells outside the highlighted row and column are illustrative.](../figures/fig2_faloo.png)\n")

# 5.4: the sibling sentence needs "marginally" (3.1 attempt 2).
rep("a program shown a test pair's siblings can fit it better than a held-out demonstration, with no difference between tests and demonstrations.",
    "a program shown a test pair's siblings can fit it better than a held-out demonstration even if each test is marginally exchangeable with the demonstrations, when tests are correlated among themselves.")

# Table 3: the one-input row (planned, Addendum 4 item 3; recounted), and Figure 1.
rep("| Qwen, ConceptARC | 94.5% | 45.8% | +48.7 | +36.7 (49) |\n",
    "| Qwen, ConceptARC | 94.5% | 45.8% | +48.7 | +36.7 (49) |\n| Qwen, ConceptARC, one test input | 96.0% | 48.4% | +47.6 | +41.0 (52) |\n")
rep("*Figure 1, to draw, the headline: this table as paired intervals.*",
    "![**Figure 1. The held-out split: Table 3 as points with 95% intervals.**](../figures/fig1_heldout_split.png)")
rep("A hand-written enumerator, an LLM, a classical search and one repeated algorithm all show the split,",
    "A hand-written enumerator, an LLM, a classical search and one repeated algorithm all show the split, as CORA's search did [11],")

# Table 4 caption (3.3 item 10, 3.5).
rep("Qwen counts tasks; its last column is the chance",
    "Qwen counts tasks (by pair, its ConceptARC coverage is 48.3%, which 5.4 uses); its last column is the chance")
rep("Other rows: post hoc for the 2020 program and fresh Monty-ARC rows; intervals in Table C9.**",
    "Other rows: post hoc for the 2020 program and fresh Monty-ARC rows; Monty-ARC's ConceptARC counts were known before its plan; intervals in Table C9.**")

# 6.3 (3.3 item 2).
rep("This is the first case we know of where the bound bites with its premises true,",
    "This is a case where the bound bites with its premises true,")

# 6.4: which run the retried-fold counts describe (3.2 mismatch 4), and the replication's.
rep("Retrying brings in no wrong answer, and it sorts as it goes: of 29 retried folds that came to fit, the 21 that predict their held-out demonstration are right on the test 15 times, and the other 8 never.",
    "Retrying brings in no wrong answer, and it sorts as it goes. Of the retried folds that came to fit, those that predict their held-out demonstration are right on the test 15 of 21 times post hoc and 12.5 of 19 in the replication; the others 0 of 8 and 0.5 of 3.")

# 6.5 (3.3 item 7).
rep("Easier tests would not raise confident errors on the test role;", "Easier tests need not raise confident errors on the test role;")

# Section 7: Table 8 random orders (3.2 mismatch 3), Figure 3, scope (3.3 items 3, 4).
rep("Random: mean (minimum, maximum) of 40 orders.", "Random: expected score over random orders (5th, 95th percentile).")
rep("| 3 | 55.0 | 52.0 (48.0, 55.5) | 45.5 | 57.0 | 51 |", "| 3 | 55.0 | 52.0 (49.0, 54.5) | 45.5 | 57.0 | 51 |")
rep("| 4 | 55.0 | 51.0 (47.0, 56.0) | 42.0 | 57.5 | 91 |\n",
    "| 4 | 55.0 | 50.4 (47.5, 53.5) | 42.0 | 57.5 | 91 |\n\n"
    "![**Figure 3. The ranking ceiling: Table 8 as curves.**](../figures/fig3_ranking_budget.png)\n")
rep("So verification takes nearly all that ranking can give,", "So at these sample counts verification takes nearly all that ranking can give,")
rep("against 17 and 0.7 if samples were independent at the same rate. More samples of the same prompt run out.",
    "against 17 and 0.7 if samples were independent at one rate for all tasks. Most unsolved tasks were never solved by any of four samples; with four samples we cannot tell a task at a few percent per sample from one at zero.")

# Section 9 (change 7).
rep("## 9. The named submission\n\nTri v3 runs offline on 4×L4 GPUs for 12 hours less a 10-minute buffer.",
    "## 9. The named submission\n\nThe named submission is an NVARC fork with a Qwen3.8-27B program-writing front end and Monty-ARC merged in; it does not contain FA-LOO or the 2020 program, which were evaluated offline. Tri v3 ({{NOTEBOOK_V3_URL}}; Kaggle's latest version of the kernel is v4-A) runs offline on 4×L4 GPUs for 12 hours less a 10-minute buffer.")
rep("temperature 1.0, top-p 0.95, top-k 20, a 10 s sandbox.",
    "temperature 1.0, top-p 0.95, top-k 20, a 10 s sandbox, demonstrations in native order (FA-LOO's offline evidence: 32k, canonical order).")
rep("verified Qwen output; confident Monty-ARC answer; NVARC's candidates;",
    "verified Qwen output; confident Monty-ARC answer (the v5 heuristic: evidence ≥ 0.99, 2:1 lead); NVARC's candidates;")
rep("""The first two distinct grids are kept.

**The notebook does not contain FA-LOO** or the 2020 program; the certificate was evaluated offline. A full public-evaluation run was beyond our GPU quota, so the named pipeline has no public-evaluation score. Offline without NVARC, its Qwen and Monty-ARC parts score 24.0 and 21.0 of 120 on two runs (Table C5).""",
    """The first two distinct grids are kept.

![**Figure 4. The named notebook, Tri v3.**](../figures/fig4_named_notebook.png)

A full public-evaluation run was beyond our GPU quota, so the named pipeline has no public-evaluation score; Table 10 scores its parts.

**Table 10. The notebook without NVARC on ARC-AGI-2 public evaluation (seen): one 16k sample per task; score of 120 (Table C5).**

| Parts | Run 1 | Run 2 |
|---|---|---|
| Qwen3.8-27B alone | 21.0 | 18.0 |
| With Monty-ARC merged | 24.0 | 21.0 |""")
rep("and checkable programs, where Qwen alone on public evaluation scores 21.0 and 18.0 of 120. A variant from a simulator's +1.7 prediction, v4-A, scored lower,",
    "and checkable programs (Table 10). A variant from a simulator's +1.7 prediction, v4-A, scored lower,")

# Cuts to pay for the additions: post hoc contrasts to Appendix C; repeats of what Section 9 now says.
rep("Post hoc, `re-arc` minus ARC-AGI-2 is −6.0 [−10.4, −1.7], minus ConceptARC +4.1 [+0.3, +7.9], and minus the one-input run +7.2 [+2.7, +11.6]. ", "")
rep("Scored on the one-input run's pairs only, the run with all test inputs shown gives −6.8 [−10.3, −3.3] (planned with the one-input run).",
    "Scored on the one-input run's pairs only, the run with all test inputs shown gives −6.8 [−10.3, −3.3] (planned with the one-input run). Post hoc, `re-arc` minus ARC-AGI-2 is −6.0 [−10.4, −1.7], minus ConceptARC +4.1 [+0.3, +7.9], and minus the one-input run +7.2 [+2.7, +11.6].")
rep("Its save run shows the code path works, but Kaggle gives no logs and other teams reported", "Its save run shows the code path works, but other teams reported")
rep("anything about the hidden set, since the rule is not in the notebook;", "anything about the hidden set;")
rep("We test the mean, not tasks by a 50:50 sign test, which has the wrong null: with one odd pair a task's difference is $+n$ when that pair draws the test role and $-1$ otherwise,",
    "We test the mean, not a 50:50 sign test over tasks: with one odd pair a task's difference is $+n$ if that pair is the test and $-1$ otherwise,")

# Section 10, item 2 (change 5).
rep("2. *Do not build a better ranker yet.* Verified-first takes nearly all that ranking can give, and stopping early adds nothing. Reach limits the score.",
    "2. *At small sample counts, verified-first ranking captures nearly all a ranker can (55.0 of 57.5 at four samples of one LLM); with many candidates per task, as in NVARC-style pipelines, this is untested.*")

# Table C7: plain (a) conditioning (3.2 mismatch 2).
rep("Qwen's one-input run, each task's first test pair only, is in Tables 4, 7, C9 and C10, not here.**",
    "Qwen's one-input run, each task's first test pair only, is in Tables 4, 7, C9 and C10, not here. For Qwen, FA-LOO and fit need the full run to verify, (a)+(b) and plain (a) do not; plain (a) with it is 248/261.**")

# Table C9: `ns` marks and the 3-task cell.
rep("| +70.6 [+41.7, +89.5] | 0.0 (3) |", "| +70.6 [+41.7, +89.5] | 0.0 ns (3 tasks, no interval) |")
i0 = s.index("**Table C9.")
i1 = s.index("† Post hoc. Spent:", i0)
block = s[i0:i1]
num = lambda t: float(t.replace("−", "-").replace("+", ""))


def mark(m):
    lo, hi = num(m.group(1)), num(m.group(2))
    return m.group(0) + (" ns" if lo <= 0 <= hi else "")


lines = []
for ln in block.split("\n"):
    if ln.startswith("| ") and not ln.startswith("| Learner") and not ln.startswith("|---"):
        ln = re.sub(r"\[([+−-]?[\d.]+), ([+−-]?[\d.]+)\]", mark, ln)
    lines.append(ln)
s = s[:i0] + "\n".join(lines) + s[i1:]

# One name for the LLM in every table row (figure panel: "Qwen3.8-27B").
s = re.sub(r"(?m)^\| Qwen, ", "| Qwen3.8-27B, ", s)

# Appendix D: the 16k one-sample runs of Tables C5 and 10 are also in native order.
rep("The notebook samples Qwen at 16k in native order, unlike the offline runs.",
    "The notebook samples Qwen at 16k in native order, as do the runs of Tables C5 and 10, unlike the FA-LOO runs (32k, canonical order).")

# References: [28], cited in Section 2.
rep("[27] neoneye. arc-dataset-collection.", "[27] neoneye. arc-dataset-collection.")
i = s.index("## Appendix A.")
s = s[:i].rstrip("\n") + "\n\n[28] Y. Romano, M. Sesia, E. J. Candès. Classification with Valid and Adaptive Coverage. NeurIPS 2020. arXiv:2006.02544.\n\n" + s[i:]

open(P, "w", encoding="utf8").write(s)
print("ok")
