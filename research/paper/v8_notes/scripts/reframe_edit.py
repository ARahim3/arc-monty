"""Reframe pass (2026-11-07): the author adopted the frame of research/paper/judge_v8c/review.md, Step 4 (iii) and
Step 5 changes 3, 8, 9. The contribution is the trust rule (FA-LOO) and what it shows about ARC; the Thousand Brains
Theory is named as the question's origin, and its section moves to Appendix D.

Rebuilds research/paper/v8/paper.md from research/paper/v8_notes/paper_before_reframe.md, and research/paper/v8/numbers.md
from research/paper/v8_notes/numbers_before_reframe.md. Every edit is an exact replacement that asserts how often its old
text occurs (once unless stated), as v8c_edit.py does; whole paragraphs are matched by a unique opening and ending.
No number, table cell or interval changes except Table 1's field line, recounted by reframe_lb.py (python -I).
    .venv/bin/python research/paper/v8_notes/scripts/reframe_edit.py"""
import os  # noqa: E402  (release: paths from the repo root)
_REPO = os.environ.get("ARC_MONTY_ROOT", os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..")))  # repo root

ROOT = (_REPO + "/research/paper/")
P, SRC = ROOT + "v8/paper.md", ROOT + "v8_notes/paper_before_reframe.md"
NP, NSRC = ROOT + "v8/numbers.md", ROOT + "v8_notes/numbers_before_reframe.md"
s = open(SRC, encoding="utf8").read()


def rep(old, new, count=1):
    global s
    n = s.count(old)
    assert n == count, (n, old[:90])
    s = s.replace(old, new)


def rep_par(start, end, new):
    """Replace the one paragraph (line) that starts with `start` and ends with `end`."""
    global s
    assert s.count(start) == 1, (s.count(start), start[:90])
    lines = s.split("\n")
    hits = [i for i, l in enumerate(lines) if l.startswith(start)]
    assert len(hits) == 1 and lines[hits[0]].endswith(end), (hits, start[:60], end[-60:])
    lines[hits[0]] = new
    s = "\n".join(lines)


# ---------------------------------------------------------------- title and subtitle (change 3)
rep("# When Can You Trust a Solver's Answer? Thousand Brains Principles Tested on Unseen ARC Tasks\n",
    "# Verified Is Not Generalised: Held-Out Re-Induction, a Distribution-Free Bound, and Where ARC Solvers Fail\n")
rep("held out separates right from wrong programs, gives a bound when folds agree,",
    "held out separates generalising programs from proxies, gives a bound when folds agree,")

# ---------------------------------------------------------------- abstract (change 3's shape; every number is in the body)
rep_par("An answer can fit every demonstration and still be wrong, so when can it be trusted?",
        "we test what the Thousand Brains Theory says such a system should do, as far as ARC can.",
        "A program that fits every demonstration can still be a proxy: about a quarter of an LLM's verified ARC-AGI-2 "
        "programs fail the test. Prompted by the Thousand Brains Theory's \"predict what you have not observed\", we "
        "re-run the whole solver with each demonstration held out, as CORA does, and answer only if every fold predicts "
        "its held-out demonstration and all folds agree on the test (FA-LOO). If demonstrations and test are "
        "exchangeable, the chance of answering wrongly is at most 1/(n+1) for any symmetric learner fixed in advance. "
        "On four learners, Monty-ARC among them, fold programs that predict their held-out demonstration beat those "
        "that miss it; within a task, by 18–47 points for an LLM and a program frozen in 2020. On fresh generated "
        "tasks, where the premises hold by construction, the LLM's rule answers 53.5% of tasks, all right: a case where "
        "the bound bites. On human-designed sets the same runs reject the premises for the LLM: there the rule is "
        "evidence, not a guarantee. On ARC-AGI-2, retrying failed folds gives 16 of 16 at 13.3% coverage (planned "
        "replication, seen split). The rule raises no score: at four samples, verification scores 55.0 of 120 and a "
        "perfect ranker 57.5, so proposal, not selection, is the bottleneck. The named submission scores 32.64, "
        "inside the band reported for unmodified NVARC forks [10]; Monty-ARC alone scores 0.00.")

# ---------------------------------------------------------------- Table 1 field line (change 10; reframe_lb.txt)
rep("*Field on 2026-10-30: 3,541 teams, top 88.06, median 29.31; the named submission ranks 252; 2,010 teams score 28–34.*",
    "*Final field, read 2026-11-07: 3,544 teams, top 88.06, median 29.31; the named submission ranks 220 (59 teams "
    "tied at 32.64, listed 220–278); 1,997 teams score 28–34.*")

# ---------------------------------------------------------------- Section 1: the reframed claim, one sentence of origin, new roadmap
rep_par("An answer can fit every demonstration and still be wrong: at ARC-AGI-2's budget",
        "So when has a solver generalised, and when can its answer be trusted?",
        "A program that reproduces every demonstration can still be a proxy, fitting the examples without the rule: at "
        "ARC-AGI-2's budget about a quarter of an LLM's verified programs fail on the test. Verified is not generalised. "
        "So which verified programs generalise? We give a held-out test that separates them from proxies within a task, "
        "a bound on its errors under stated premises, and what its failures say about where ARC solvers fail.")
rep("The question came from building a solver on the Thousand Brains Theory (TBT) [3–6], a theory of the neocortex. "
    "Its idea that a model is tested by what it predicts about observations not yet made gives a reusable rule:",
    "The question came from building a solver on the Thousand Brains Theory (TBT) [3–6], a theory of the neocortex "
    "in which a model is tested by what it predicts about observations not yet made. For ARC that gives a reusable rule:")
rep("A plain hold-out check is earlier work (CORA [11]); agreement is what makes a proof possible for any re-runnable learner.",
    "Re-induction with each demonstration held out is earlier work (CORA [11]); agreement is what makes a proof "
    "possible for any re-runnable learner.")
rep_par("We add the proof (Section 5); tests on four very different learners (6.1, 6.2);",
        "what the rule buys (7); and what TBT lets ARC test (8).",
        "We add the proof (Section 5); tests on four very different learners (6.1, 6.2); a case where the bound bites "
        "with its premises true (6.3); a cheap improvement, replicated (6.4); a test of exchangeability from the same "
        "runs (6.5); what the rule buys (7); the named submission (8); and what the failures say about where ARC "
        "solvers fail (9).\n\n"
        "**The theory.** Appendix D reports what ARC can and cannot test about TBT: on exact, fully visible "
        "grids, movement and voting change the number of steps, not the answer; Monty-ARC's object frames add solves, "
        "not trust; and in a one-column system built to the theory, frames, behaviour in its own frame, the count "
        "sensor and memory added nothing we could separate.")

# ---------------------------------------------------------------- Section 4: roles defined once, in their own paragraph (change 9)
rep("Sets count test pairs, unless marked tasks. In the *real role* the true test pair is the query; in *demo roles* "
    "each demonstration in turn plays test.",
    "Sets count test pairs, unless marked tasks.\n\n"
    "**Roles.** In the *real role* the task's own test pair is the query; in *demo roles* each demonstration in turn "
    "plays test; *rotating* runs every role.")
# Table C4's column heads use the two terms.
rep("**Table C4. Wrong confident answers, 8 views minus 1 view.**",
    "**Table C4. Wrong confident answers, 8 views minus 1 view. Real: the real role; demo: demo roles.**")

# 6.2: the paper's frame now says "verified is not generalised"; the 6.2 slogan repeated it.
rep("That is evidence, not assurance. Verified is not right: Qwen's verified programs",
    "That is evidence, not assurance. Qwen's verified programs")

# ---------------------------------------------------------------- Section 8 becomes Appendix D (change 8); D becomes E
start8 = "## 8. What the Thousand Brains Theory lets ARC test\n"
start9 = "## 9. The named submission\n"
assert s.count(start8) == 1 and s.count(start9) == 1
i8, i9 = s.index(start8), s.index(start9)
sec8 = s[i8:i9]
s = s[:i8] + s[i9:]
assert sec8.count("**Table 9. One column.") == 1 and "Table 9" not in s
sec8 = sec8.replace(start8, "## Appendix D. What ARC can and cannot test about the Thousand Brains Theory\n")
sec8 = sec8.replace("**Table 9. One column.", "**Table D1. One column.")
rep("## Appendix D. Reproducibility, credits, tools\n", "## Appendix E. Reproducibility, credits, tools\n")
iE = s.index("## Appendix E. Reproducibility, credits, tools\n")
s = s[:iE] + sec8.rstrip("\n") + "\n\n" + s[iE:]

# Sections 9, 10 become 8, 9; Table 10 becomes Table 9 (Table 9 is now D1).
rep(start9, "## 8. The named submission\n")
rep("## 10. Limits and conclusion\n", "## 9. Limits and conclusion\n")
rep("Table 10", "Table 9", count=3)
rep("Tables C5 and 10", "Tables C5 and 9")
rep("in few tasks (Section 10).", "in few tasks (Section 9).")

# ---------------------------------------------------------------- conclusion in the new frame (Section 9)
rep_par("**Conclusion.** When has a solver generalised rather than fitted a proxy?",
        "On human-designed sets it is evidence, not a guarantee.",
        "**Conclusion.** Verified is not generalised. Holding each demonstration out separates programs that generalise from proxies within a task, not only "
        "between tasks: on every set for Qwen, on all but ARC-AGI-2 for the 2020 program, and on some sets for "
        "Monty-ARC and the one-column system. With agreement, answers that pass are right more often than answers that "
        "merely fit: 73–100% against 30–94% on the rows of Table 4, at coverage of 3–54%. On known generators, with the "
        "premises true and a learner that answers enough, that is also a working bound. On human-designed sets it is "
        "evidence, not a guarantee.\n\n"
        "**Where ARC solvers fail.** Demonstrations under-determine the rule: on ConceptARC, 62 of 68 failing folds on "
        "rejected right tasks fit their own demonstrations and miss the held-out one; on ARC-AGI-2 most are search "
        "failures, which retrying partly cures (Section 6.4). Hand-read, Monty-ARC's confident errors on ConceptARC are "
        "mostly tests outside the demonstrations' range or proxies that fit every fold, as is Qwen's only wrong FA-LOO "
        "answer (Appendices B, C; judged). And proposal, not selection, is the bottleneck: 39 of 75 single-test tasks "
        "are solved by none of four samples, while a perfect ranker would add 2.5 points to verified-first (Section 7).")

# ---------------------------------------------------------------- placeholders must survive untouched
for ph in ("{{PDF_URL}}", "{{GITHUB_URL}}", "{{NOTEBOOK_V3_URL}}"):
    assert s.count(ph) == open(SRC, encoding="utf8").read().count(ph), ph

open(P, "w", encoding="utf8").write(s)

# ================================================================ numbers.md
s = open(NSRC, encoding="utf8").read()
rep("Rows marked v8c below are new or changed in that pass.",
    "Rows marked v8c below are new or changed in that pass. **Reframe pass (2026-11-07), own code:** `reframe_lb.py` "
    "→ `reframe_lb.txt` (both leaderboard CSVs, run with `python -I` from outside the data folder). Rows marked "
    "reframe are new or changed in that pass; section headings follow the new order (Section 8 → Appendix D, "
    "Table 9 → Table D1, Section 9 → 8, Section 10 → 9, Table 10 → Table 9).")
rep("| 3,541 teams, top 88.06, median 29.31; rank 252 (tied at 32.64 with ranks 203–256); 2,010 between 28 and 34 | "
    "`external/judge/lb/arc-prize-2026-arc-agi-2-publicleaderboard-2026-10-30T21:11:03.csv`, recounted by the last pass "
    "and the judge | R |",
    "| reframe: final field, 3,544 teams, top 88.06, median 29.31; ranks 220 (59 teams tied at 32.64, listed 220–278; 219 "
    "teams strictly above; Kaggle's Rank column, which orders ties, puts ours at 265); 1,997 between 28 and 34 "
    "inclusive | `external/judge/lb/arc-prize-2026-arc-agi-2-publicleaderboard-2026-11-07T12:23:22.csv`, the final "
    "public leaderboard, recounted by `reframe_lb.py` → `reframe_lb.txt`. The same script reproduces the 10-30 "
    "file's figures that this row replaces (3,541; rank column 252, ties 203–256; 2,010) | R |")
rep("| 2026-10-30 | Date in the CSV's name | D |", "| reframe: 2026-11-07 | Date in the CSV's name | D |")
rep("| 53.5%, 16 of 16, 13.3%, 55.0, 57.5 of 120, 45–85, 18–47 | As Sections 6.1, 6.3, 6.4, 7 | R |",
    "| 53.5%, 16 of 16, 13.3%, 55.0, 57.5 of 120, 45–85, 18–47 | As Sections 6.1, 6.3, 6.4, 7 (reframe: the abstract "
    "keeps all but 45–85, which stays in 6.1; about a quarter as Section 1; 32.64 and 0.00 as Table 1) | R |")
rep("## Section 8, Table 9\n", "## Appendix D, Table D1 (Section 8 and Table 9 before the reframe)\n")
rep("## Section 9\n", "## Section 8 (Section 9 before the reframe)\n")
rep("| 24.0 and 21.0; 21.0 and 18.0 (Table 10) |", "| 24.0 and 21.0; 21.0 and 18.0 (Table 9; Table 10 before the reframe) |")
rep("## Section 10\n", "## Section 9 (Section 10 before the reframe)\n")
rep("| 73–100; 30–94; 3–54 |",
    "| reframe: Where ARC solvers fail: 62 of 68; most of ARC-AGI-2's failing folds (22 of 31) | As Section 6.4 | R |\n"
    "| reframe: \"mostly\" outside the range or proxies (9 of 10 pairs: 5 and 4; 1 two rules) | Appendix B's grouping; judged causes | R |\n"
    "| reframe: 39 of 75 solved by no sample; a perfect ranker adds 2.5 | As Section 7 (+2.5 [0, +6.0]) | R |\n"
    "| reframe: within a task, every Qwen set, all but ARC-AGI-2 for the 2020 program, some sets for Monty-ARC "
    "(4 of 6) and the one-column system (1 of 3) | Table 3's `ns` marks | R |\n"
    "| 73–100; 30–94; 3–54 |")
open(NP, "w", encoding="utf8").write(s)
print("ok")
