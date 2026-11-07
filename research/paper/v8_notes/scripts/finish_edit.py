"""Finisher pass: applies every text change to paper_before_finisher.md and writes paper.md. Each edit must match exactly once, so the script can be re-run from the backup."""
import os  # noqa: E402  (release: paths from the repo root)
_REPO = os.environ.get("ARC_MONTY_ROOT", os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..")))  # repo root
N = (_REPO + "/research/paper/")
s = open(N + "v8_notes/paper_before_finisher.md", encoding="utf8").read()


def R(old, new):
    global s
    assert s.count(old) == 1, (s.count(old), old[:90])
    s = s.replace(old, new)


# ---- headline: within-task size wherever 45-75 appears
R("separates right from wrong programs by 45–75 points on three kinds of learner, one frozen",
  "separates right from wrong programs by 45–75 points between tasks and 18–47 within a task, on three kinds of learner, one frozen")
R("beat those that miss it by 45–75 points on the test (Table 5), and the rule beats the usual test wherever it answers.",
  "beat those that miss it on the test by 45–75 points between tasks and 18–47 within a task (Table 5, one thin row apart), and the rule is more precise than the usual test wherever it answers, though not separably on two of nine rows (Table 6).")
R("It does not raise a score: Monty-ARC alone", "The rule does not raise a score: Monty-ARC alone")
R("The held-out split separates right from wrong by 45–75 points on three kinds of learner, including a program frozen before the sets existed.",
  "The held-out split separates right from wrong by 45–75 points between tasks and 18–47 within a task, on three kinds of learner, including a program frozen before the sets existed.")

# ---- Section 3
R("We ran its published recipe unchanged, with demonstrations in canonical order and a plan fixed before any output on these sets.",
  "We ran its published recipe, with fixed per-process limits in place of its global stop, demonstrations in canonical order and a plan fixed before any output on these sets.")
R("the grids are wider than it can read, and it abstains.",
  "the grids are wider than it can read, and it abstains. On ARC-AGI-2 it ran on the 113 evaluation tasks not shared with ARC-AGI-1.")
R("Its tests came from a first, post hoc look at a greedy run at 16k: 5 of 20 verified tasks certified, all right; verified fold programs right 78.1% against 7.5%; a held-out AUROC of 0.91; an identical rerun doing about as well as the certificate.",
  "Its tests came from a first, post hoc look at a greedy run at 16k: 5 of 20 verified tasks certified, all right; verified fold programs right 78.1% against 7.5%; a held-out AUROC of 0.91.")

# ---- Section 4
R("*Top answer:* the learner's best answer, always given. *Fit:* the top answer only if",
  "*Top answer:* the learner's best answer, if it has one. *Fit, the usual test:* the top answer only if")

# ---- Section 5.3: order of the four sets
R("Of roles passing (a), (b) fails in 4 of 21, 0 of 32, 21 of 205 and 0 of 12, rejecting 18 right and 7 wrong answers.",
  "Of roles passing (a), on the four unseen sets in Table 5's order, (b) fails in 4 of 21, 0 of 32, 21 of 205 and 0 of 12, rejecting 18 right and 7 wrong full-data answers.")

# ---- Section 5.4
R("That is an identity. Judged, why events are rare: an event needs a rule right on $n$ of $n+1$ pairs and found again from every subset. A correct rule produces no misses, and a coincidental fit usually fails to re-appear and misses several pairs, so events mark a stable proxy. Hand-reading fits (Appendix B): of Monty-ARC's 10 wrong ConceptARC answers, 5 have a test outside the demonstrations' range, 4 a proxy that fits every fold, and 7 have only two demonstrations.",
  "That is an identity. Judged, why events are rare: an event needs a rule right on $n$ of $n+1$ pairs and found again from every subset. A correct rule produces no misses, and a coincidental fit usually misses several pairs, so events mark a stable proxy. Hand-reading fits (Appendix B): of Monty-ARC's 10 wrong ConceptARC answers, 5 have a test outside the demonstrations' range and 4 a proxy that fits every fold.")
R("| **−0.1 [−1.0, +0.9]** ns |", "| −0.1 [−1.0, +0.9] ns |")
R("**Judged.** On the generated set the premise holds tightly; on human-designed sets it fails in both directions, which is what you would expect if people choose test pairs deliberately while a generator does not. Mini-ARC does not reject it, with less power.",
  "**Judged.** The generated set does not reject the premise at type level, though counted by task its discordant folds lean to the test (19:69 for Monty-ARC, 95:126 for the 2020 program). ConceptARC and ARC-AGI-2 look imperfect in opposite directions, which is what you would expect if people choose test pairs deliberately while a generator does not. Mini-ARC does not reject it, with less power.")

# ---- Section 5.5
R("ConceptARC 80.6% [58.3, 93.0] vs 88.0% [66.7, 100.0]; Mini-ARC 77.3% [46.2, 94.1] vs 88.9% [62.5, 100.0]; 1D-ARC 83.8% [34.0, 94.0] vs 93.6% [79.1, 98.3].",
  "ConceptARC 80.6% [58.3, 93.0] vs 88.0%; Mini-ARC 77.3% [46.2, 94.1] vs 88.9%; 1D-ARC 83.8% [34.0, 94.0] vs 93.6%.")

# ---- Section 6.1: Table 5 with the within-task column
R("**Table 5. Right on the test, for fold programs that predict their held-out demonstration vs those that miss it (number of programs). All planned. Monty-ARC's rows use its closest measure, a different one: the system's top answer at evidence ≥ 0.99 vs below.**",
  "**Table 5. Right on the test, for fold programs that predict their held-out demonstration vs those that miss it (number of programs). Last column: mean paired difference inside tasks with both kinds (number of tasks). All planned, except that column for the 2020 program, post hoc. Monty-ARC's rows use its planned measure, a different one: the system's top answer at evidence ≥ 0.99 vs below.**")
R("| Learner | Set | Predict held-out | Miss it | Difference, points |\n|---|---|---|---|---|",
  "| Learner | Set | Predict held-out | Miss it | Difference, points | Within a task, points (tasks) |\n|---|---|---|---|---|---|")
R("| 81.5% (54) | 13.4% (82) | +68.1 [+51.5, +82.6] |", "| 81.5% (54) | 13.4% (82) | +68.1 [+51.5, +82.6] | |")
R("| 91.7% (12) | 20.9% (43) | +70.7 [+48.0, +87.9] |", "| 91.7% (12) | 20.9% (43) | +70.7 [+48.0, +87.9] | |")
R("| 93.9% (181) | 19.2% (146) | +74.7 [+61.2, +82.9] |", "| 93.9% (181) | 19.2% (146) | +74.7 [+61.2, +82.9] | |")
R("| 83.3% (99) | 17.4% (47) | +66.0 [+53.6, +77.9] |", "| 83.3% (99) | 17.4% (47) | +66.0 [+53.6, +77.9] | +37.5 [+11.0, +61.8] (17) |")
R("| 94.5% (321) | 45.8% (88) | +48.7 [+41.3, +56.3] |", "| 94.5% (321) | 45.8% (88) | +48.7 [+41.3, +56.3] | +36.7 [+26.5, +46.9] (49) |")
R("| 60.4% (285) | 15.3% (993) | +45.0 [+35.3, +54.6] |", "| 60.4% (285) | 15.3% (993) | +45.0 [+35.3, +54.6] | +17.6 [+8.2, +27.2] (52) |")
R("| 74.4% (203) | 15.1% (325) | +59.3 [+47.8, +69.8] |", "| 74.4% (203) | 15.1% (325) | +59.3 [+47.8, +69.8] | +28.0 [+15.2, +41.5] (47) |")
R("| 84.8% (983) | 17.5% (862) | +67.3 [+55.4, +75.8] |", "| 84.8% (983) | 17.5% (862) | +67.3 [+55.4, +75.8] | +46.6 [+34.4, +57.5] (232) |")
R("| 85.7% (63) | 21.3% (75) | +64.4 [+44.6, +80.3] |", "| 85.7% (63) | 21.3% (75) | +64.4 [+44.6, +80.3] | +23.8 [+11.9, +35.7] (7) |")
R("| 16.7% (6) | 0.6% (468) | +16.0 [−0.6, +48.8] ns |", "| 16.7% (6) | 0.6% (468) | +16.0 [−0.6, +48.8] ns | +6.2 [0.0, +18.8] ns (4) |")
R("**This is the case for portability.** A hand-written enumerator, an LLM and a classical search all show it, and the 2020 program's rows need no trust in us. On ARC-AGI-2 that program almost never predicts a held-out demonstration, so its row says little. Qwen and the 2020 program are measured on programs; Qwen, restricted to programs verified on what they saw. Within tasks that have both kinds, the cleanest control, Qwen gives +37.5 [+11.0, +61.8] (17 tasks) and +36.7 [+26.5, +46.9] (49 tasks). Sorting does not by itself make programs better:",
  "**This is the case for portability.** A hand-written enumerator, an LLM and a classical search all show it, and the 2020 program's rows owe nothing to our development: we chose only its wrapper, in a plan fixed before any output. On ARC-AGI-2 that program almost never predicts a held-out demonstration, so its row says little. Qwen and the 2020 program are measured on fold programs that give a test answer; Qwen, restricted to those verified on what they saw.\n\n**Between tasks and within.** The difference column compares across tasks, and easy tasks produce both predicting programs and right answers. The last column removes that: it compares programs on one task's test (on 1D-ARC by task, resampling its 14 types). The split shrinks to 18–47 points and still separates on every row but the thin one. Monty-ARC's rows score one top answer per test pair and only one task holds both kinds, so they have no such control; its fold models, post hoc, give +73.3, +67.2, +69.6 between tasks, all separating, and within a task +43.6 [+22.2, +64.7] (12 tasks), +21.2 [−6.1, +50.0] ns (11), +35.0 [+9.5, +66.7] (20). Sorting does not by itself make programs better:")

# ---- Section 6.2
R("**Table 6. Real role. Fit: Monty-ARC, its fit-only rule; Qwen, verified; 2020 program, top answer that fits all demonstrations. Qwen counts tasks here; per pair in Table C7.**",
  "**Table 6. Real role. Top answer: share right where the learner has one (Monty-ARC on 136, 55, 327 pairs; the 2020 program on 615 of 901 on 1D-ARC). Fit: Monty-ARC, its fit-only rule; Qwen, verified; 2020 program, top answer that fits all demonstrations. Qwen counts tasks here, with Wilson intervals; per pair in Table C7.**")
R("Beside Monty-ARC per pair (Table C7), its FA-LOO is 232/232 at 48.3% coverage against 35/44 at 9.2%.",
  "Per pair (Table C7) its FA-LOO is 232/232 at 48.3% coverage, against Monty-ARC's 35/44 at 9.2%.")
R("(E) is doubtful on both sets, (F) is open, and the one memorisation check we ran, for long literal rows in programs, found none.",
  "(E) is doubtful on both sets; (F) fails on ARC-AGI-2, whose tasks the harness was built on, and is open on ConceptARC, where the one memorisation check we ran, for long literal rows in programs, found none.")
R("On ARC-AGI-2 it is right on 2 of 160 under the usual test, and the rule answers nothing.",
  "On ARC-AGI-2 its top answer is right on 2 of 160 pairs, and the rule answers nothing.")
R("Monty-ARC's and the 2020 program's certified answers barely overlap: 7 of 52 pairs, 5 of 36, 14 of 341, 0 of 17. Each stays precise on what only it answers.",
  "Monty-ARC's and the 2020 program's certified answers barely overlap: of the pairs either answers, both answer 7 of 52 on ConceptARC, 5 of 36 on Mini-ARC, 14 of 341 on 1D-ARC (14 of 229 on tasks the program can read) and 0 of 17 on MinimalTasks. Each stays precise on what only it answers.")

# ---- Section 6.3
R("At verified rate $v$ the price is about $1+vn$. Here, at $v=0.375$, that is 1.94× (133 folds), or 1.61× exiting at the first failed fold (91 folds).",
  "At verified rate $v$ the price is about $1+vn$ runs. Here $v=0.375$ predicts 2.1×; measured in tokens it is 1.94× (133 folds), or 1.61× exiting at the first failed fold (91 folds).")
R("So folds in place of repeats give the certificate for no extra tokens, at no measured cost in score, though small losses are not excluded. On the 75 tasks whose first sample did not verify, 33 of 225 resamples verify, 22.0 right, and 24 of 226 folds pass, 19.5 right: −0.011 [−0.041, +0.018] per run, so an earlier hint that folds beat resampling there did not replicate.",
  "So folds in place of repeats give the certificate for no extra tokens, at no measured cost in score, though small losses are not excluded. On the 75 tasks whose first sample did not verify, folds do not beat resampling either (24 of 226 pass, 19.5 right; 33 of 225 verify, 22.0 right; −0.011 [−0.041, +0.018] per run).")
R("At 192k: 55.0, logged runs exhausted (48.2 at 174k), and 52.0. Certification trails until about 290k, and only 7 tasks ever stop on it.",
  "At 192k: 55.0, logged runs exhausted (48.2 at 174k), and 52.0. Certification is a point ahead at 64k, before any task can certify, and trails from 96k until about 290k, past the 246k where plain runs end; only 7 tasks ever stop on it.")

# ---- Section 6.4: the table carries the intervals
R("`canon` minus `global`, a weak baseline, is +6 [−1, +14] ns, +10 [+3, +18], +168 [+48, +313]. These solves",
  "`canon` minus `global`, a weak baseline, separates on Mini-ARC and 1D-ARC only. These solves")

# ---- Section 6.5
R("Wrong answers rise in 4 of 6 populations (Table C4; +14 [+5, +24] on 1D-ARC's demo roles, +5 [+2, +9] on its real role).",
  "Wrong answers rise separably in 4 of 6 populations (Table C4).")

# ---- Section 7
R(" That negative result should save other teams time. Trust still tells you", " Trust still tells you")

# ---- Section 8: exchangeability is in 5.4 and in 9
R("- **Exchangeability** looks imperfect on human-designed sets, jointly with (F) for Qwen. The sets other than ARC-AGI-2 are easier: humans score 91% on ConceptARC.\n",
  "- **Easier sets.** The sets other than ARC-AGI-2 are easier: humans score 91% on ConceptARC.\n")

# ---- Section 9
R("what fails first in Monty-ARC is relations and counting.", "what fails first in Monty-ARC is composition, relations and counting.")
R("""**What other teams can use.** We offer no way to solve more tasks: Monty-ARC scores 0.00 and nothing here reaches 85%. The usable results are these.

1. *At these budgets, on one split, in a replay, trust did not buy score:* ranking is worth 1–2 points at one sample per task, and stopping on a verified or certified answer earned no more than not stopping.
2. *Verified is not right:* on ARC-AGI-2, Qwen's verified programs are right 72–78% of the time across our runs.
3. *Held-out prediction sorts programs without test labels,* across learners (Table 5). Its rate alone ranks weakly; the full rule answered 72 of 72 right on Qwen.
4. *The certificate can replace repeats:* no extra tokens, no measured cost in score, small losses not excluded.
5. *Checks:* the discordant test shows whether tests differ from demonstrations; rotating roles among demonstrations estimates precision on hidden data.
6. *Nulls:* perception notes in the Qwen prompt (+2.1 per 120 tasks [−1.7, +6.0]); D8 voting under a threshold.
""", """**What other teams can use.**

1. *Held-out prediction sorts programs without test labels,* across learners and within a task (Table 5). Its rate alone ranks weakly; the full rule answered 72 of 72 right on Qwen.
2. *Verified is not right:* on ARC-AGI-2, Qwen's verified programs are right 72–78% of the time across our runs.
3. *The certificate can replace repeats:* no extra tokens, no measured cost in score, small losses not excluded.
4. *Checks:* the discordant test shows whether tests differ from demonstrations; rotating roles among demonstrations estimates precision on hidden data.
5. *Nulls:* perception notes in the Qwen prompt (+2.1 per 120 tasks [−1.7, +6.0]); D8 voting under a threshold.
6. *At these budgets, on one split, in a replay, trust did not buy score:* ranking is worth 1–2 points at one sample per task, and stopping on a verified or certified answer earned no more than not stopping.

We offer no way to solve more tasks: Monty-ARC scores 0.00 and nothing here reaches 85%.
""")

# ---- References
R("github.com/top-quarks/ARC-solution, 2020 (commit 9407072; MIT licence; code not included here).",
  "github.com/top-quarks/ARC-solution, 2020 (commit 9407072, code unchanged since 2020-06-08; MIT licence, copyright 2020 top-quarks; code not included here).")

# ---- Appendix C
R("MinimalTasks (48 attention checks, 0 of 93 pairs shared) is too small to rely on: FA-LOO and v5 5/5, fit-only 6/17. Removing the behaviour module",
  "Removing the behaviour module")
R("for the fold-competition reason of Section 6.1, but on 1D-ARC", "for the reason under Table C6, but on 1D-ARC")
R(" Evidence ≥ 0.99 against below uses the system's top answer. MinimalTasks (48 attention checks): FA-LOO and v5 5/5, fit-only 6/17.",
  " MinimalTasks (48 attention checks), too small to rely on: FA-LOO and v5 5/5, fit-only 6/17.")

# ---- Appendix E
R("`research/arc2/faloo_qwen.py` and `faloo_analyze.py` (LLM), `tools/build_tri.py` (notebook).",
  "`research/arc2/faloo_qwen.py`, `faloo_analyze.py`, `faloo_qwen_sampling.py` and `faloo_sampling_analyze.py` (LLM), `research/icecuber_faloo/` (run lists, wrapper, raw output, analysis; the 2020 program's own code is not included), `research/paper/v8_notes/scripts/` (independent recounts), `tools/build_tri.py` (notebook).")
R("Labels in Section 6.5 are LLM-assisted", "Labels in Section 6.6 are LLM-assisted")

# ---- length: detail a table already carries, and repetition
R(" We report no training-set performance as a result; the few development-wide figures (code checks, the event rate) are labelled.", "")
R(" A notebook could calibrate this way on the hidden set during the scored run [10].", "")
R("(24 of 226 pass, 19.5 right; 33 of 225 verify, 22.0 right; −0.011 [−0.041, +0.018] per run)", "(−0.011 right per run [−0.041, +0.018])")
R(" With two samples, 58 are crowded and orders span 18.5–28.5.", "")
R("- **Easier sets.** The sets other than ARC-AGI-2 are easier: humans score 91% on ConceptARC.\n", "")
R("and a baseline with no pooling and no voter counts solves the same items at a precision that does not separate.", "and a no-vote baseline solves the same items at a precision that does not separate.")
R("The rule needs only a re-runnable learner: it has been tried here on a hand-written enumerator, an LLM and a classical search, and by CORA [11] on a per-task neural learner, but we have no test outside ARC-style tasks.",
  "The rule needs only a re-runnable learner: it has been tried on three kinds here and, by CORA [11], on a per-task neural learner, but on nothing outside ARC-style tasks.")

R(" Hand-reading fits (Appendix B): of Monty-ARC's 10 wrong ConceptARC answers, 5 have a test outside the demonstrations' range and 4 a proxy that fits every fold.", " Appendix B reads Monty-ARC's 10 wrong ConceptARC answers.")
R(" Frames widen what can be reached; they do not tell the solver when it has reached the right thing.", "")
# Table 4: Monty-ARC's rows were never marked post hoc; one caption sentence replaces the row labels
R("Abstaining counts as wrong. Clusters: tasks, or types on 1D-ARC.**", "Abstaining counts as wrong. Clusters: tasks, or types on 1D-ARC. Planned, except Monty-ARC's rows and the greedy row (post hoc).**")
R("| Qwen, ARC-AGI-2, greedy 16k (post hoc) |", "| Qwen, ARC-AGI-2, greedy 16k |")
R("| Qwen, ARC-AGI-2, sampling 32k (planned) |", "| Qwen, ARC-AGI-2, sampling 32k |")
R("| Qwen, ConceptARC (planned) |", "| Qwen, ConceptARC |")
for x in ("ConceptARC", "Mini-ARC", "1D-ARC", "MinimalTasks"):
    R(f"| 2020 program, {x} (planned) |", f"| 2020 program, {x} |")

# Section 6.2 said "does not separate" where Section 5.3 and Table C6 say the answer sets are identical
R("Its FA-LOO does not separate from plain (a) or from the v5 heuristic, and on ConceptARC the estimate favours v5 (Table C6).",
  "Its FA-LOO answers the same items as plain (a) (Section 5.3) and does not separate from the v5 heuristic; on ConceptARC the estimate favours v5 (Table C6).")

R("`canon` minus `global`, a weak baseline, separates on Mini-ARC and 1D-ARC only. These solves", "`canon` minus `global`, a weak baseline, separates on Mini-ARC and 1D-ARC, not on ConceptARC. These solves")
R("On human-designed sets, where (E) looks imperfect, only the rule's measured value remains.", "On ConceptARC and ARC-AGI-2, where (E) looks imperfect, only the rule's measured value remains.")
R("So folds in place of repeats give the certificate for no extra tokens, at no measured cost", "So folds in place of repeats give the certificate (at four runs, on tasks with $n\\le 3$) for no extra tokens, at no measured cost")

R(" We found no test of TBT's claims on ARC-AGI-1/2.\n", "\n")
R(" Against the fairer fit baseline ConceptARC does not separate.", "")
R("FP8 weights on vLLM across the four GPUs, up to 20 concurrent requests.", "FP8 weights on vLLM across the four GPUs.")

R("The split shrinks to 18–47 points and still separates on every row but the thin one.", "The split shrinks to 18–47 points and still separates on every row but the 2020 program's on ARC-AGI-2.")

open(N + "v8/paper.md", "w", encoding="utf8").write(s)
print("written", len(s))
