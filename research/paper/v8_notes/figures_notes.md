# Figures for v8: files, captions, placement

All figures are drawn at their final print size, so include them at the width given and the type stays at 7.5–9 pt. One visual system across the four: Arial, hairline grey axes, blue `#2a78d6` and orange `#eb6834` as the only hues. That pair passes the dataviz palette validator on white (colour-blind ΔE 24.7, normal ΔE 33.6, both ≥ 3:1 contrast). Shape and fill repeat every colour distinction, so the figures also read in greyscale.

Each figure is in `research/paper/figures/` as `.png` (300 dpi), `.pdf` (vector, Arial subset embedded) and `.svg` (vector, text as paths). Typst 0.14+ takes PDF or SVG; use either. Scripts are in `research/paper/v8_notes/scripts/`: `fig_style.py` (shared tokens) and one `fig_N_*.py` per figure. Every number is typed in from the paper's tables, with the table named in the docstring. To rebuild:

    cd research/paper/v8_notes/scripts && ../../../../.venv/bin/python fig_1_heldout_split.py   # etc.

If you want the figures in the body face, change `font.family` in `fig_style.py` to `"STIX Two Text"` and re-run.

---

## Figure 1, the headline: `fig1_heldout_split.{png,pdf,svg}`, 16.0 × 9.1 cm

**Where.** Section 6.1. Replace the marker line after Table 3, `*Figure 1, to draw, the headline: this table as paired intervals.*`.

**Proposed caption.**

> **Figure 1. The held-out split across four learners: Table 3 as intervals.** Right on the test, in points: fold programs that predict their held-out demonstration minus those that miss it, with points and 95% intervals. Circles: between tasks. Diamonds: within a task, the mean paired difference over tasks that hold both kinds. Filled: planned. Hollow: post hoc (Monty-ARC's first three rows, and the 2020 program's within-task column before `re-arc`). `ns`: the interval reaches 0. Monty-ARC on the hand-made fresh sets has 3 tasks and no within-task interval. Counts and intervals are in Table C9; the one-column system's spent rows are there only.

**What it shows.** Eighteen rows, the rows of Table 3 in Table 3's order. Learners are the panels: Monty-ARC and Qwen3.8-27B on the left, the 2020 program and one column on the right. 16 of 18 between-task intervals and 13 of the 17 within-task intervals sit above zero. The rows that do not separate stay in, marked `ns`: Monty-ARC Mini-ARC within; 2020 program ARC-AGI-2 both; one column `arc-dataset-tama` within; one column PQA both.

**Values checked against the tables.** Every plotted point and interval matches Table C9, and every `ns` and post hoc mark matches Table 3 and the C9 daggers. Recomputing Predict minus Miss from the C9 counts reproduces every Between value to within 0.1.

---

## Figure 2: `fig2_faloo.{png,pdf,svg}`, 16.0 × 10.0 cm

**Where.** Section 5.2, after the proof's last paragraph ("… at most one of a task's $n+1$ pairs, playing test, can produce a confident error."), before `### 5.3`. It could instead go at the end of 5.1, since its top half is the rule. Add a pointer in the text, e.g. "(Figure 2)" after "FA-LOO answers $\hat y$ only if …" in 5.1.

**Proposed caption.**

> **Figure 2. FA-LOO, and why a confident error has probability at most $1/(n+1)$.** Top: the rule on one task. Each of $n$ folds is fitted without one demonstration and predicts it and the test; the full run is fitted on all $n$. FA-LOO answers $\hat y$ only if (a), (b) and, optionally, (c) pass, and otherwise abstains. Bottom: the proof's table for $n=3$, with pair 4 the test. $L(a,b)=1$ if $M_{ab}$, fitted without pairs $a$ and $b$, misses $y_a$. A confident error is the event $E_4$: row 4 all 1 and column 4 all 0. That column puts a 0 in every other row, so at most one $E_a$ occurs, and under (S), (F) and (E) each has probability at most $1/(n+1)$. Cells outside the highlighted row and column are illustrative.

**Notation.** As in 5.1–5.2: $Z_i=(x_i,y_i)$; $M_i=A(\{Z_j: j\le n, j\ne i\},\{x_i,x_{n+1}\},\xi_i)$; checks (a), (b), (c); $M_{ab}$; $L(a,b)$; $E_a$; and the real fold $M_i=M_{i,n+1}$ (drawn as $M_{i4}$).

**One deviation from the brief, on purpose.** The brief had rows as "the pair held out / fitted on the rest" and columns as "the pair predicted". The paper defines $L(a,b)=1$ if $M_{ab}$ mispredicts $y_a$, and $M_{ab}$ holds out both $a$ and $b$. So the grid follows the paper: rows $a$ are the pair scored, and columns $b$ are the other pair held out. With that reading, column 4 all 0 is check (a) and row 4 all 1 is check (b) with $\hat y\ne y_4$, exactly as in step 3 of the proof.

---

## Figure 3: `fig3_ranking_budget.{png,pdf,svg}`, 12.0 × 7.6 cm (include at 12 cm, centred)

**Where.** Section 7, directly after Table 8, before the paragraph that starts "**Ranking.**".

**Proposed caption.**

> **Figure 3. The ranking ceiling.** Score of 120 on ARC-AGI-2 public evaluation against samples per task, by candidate order. Qwen at 32k, logged runs on a seen split; descriptive. Random: the mean of 40 orders, with a band from minimum to maximum. Crowded: test outputs, of 167, with more than two candidates. At one and two samples there are none, so every order scores the same. At four samples verified first leads unverified first by 13.0 [+7.0, +19.5], and a perfect ranker adds 2.5 [0, +6.0]. Values in Table 8.

**Values plotted (Table 8).** Verified first 34.7, 47.0, 55.0, 55.0. Random 34.7, 47.0, 52.0 (48.0–55.5), 51.0 (47.0–56.0). Unverified first 34.7, 47.0, 45.5, 42.0. Perfect ranker 34.7, 47.0, 57.0, 57.5. Crowded 0, 0, 51, 91. The 1–2-sample part is drawn as one shared grey segment, because all four series are equal there.

---

## Figure 4, optional: `fig4_named_notebook.{png,pdf,svg}`, 16.0 × 7.9 cm

**Where.** Section 9, after the four bullets and before "**The notebook does not contain FA-LOO** …". If space is short, drop it: the bullets say the same.

**Proposed caption.**

> **Figure 4. The named notebook, Tri v3.** Qwen3.8-27B writes programs for up to 4.5 h. The NVARC fork then runs until the deadline and skips tasks with a verified Qwen program. Monty-ARC v5 runs on CPU throughout. For each test output, candidates are taken in the order shown and the first two distinct grids are submitted. The notebook does not contain FA-LOO or the 2020 program; the certificate was evaluated offline.

**How it was drawn.** New, from Section 9's text only. It does not reuse or imitate `system_diagram.png`: there is no banner, no "predict the next sensation" line and no "evidence = 1.0". The "confident" label in the merge reads "(v5 heuristic: evidence ≥ 0.99, 2:1 lead)". That definition is Appendix C's. I checked it against the notebook's `confident()` in `kaggle/tri/monty-arc-qwen-nvarc.ipynb`, read only: `CONFIDENT = 0.99` and a 2:1 out-vote. "One view" matches the notebook's `perspectives=(0,)`.

---

## Inconsistencies and things to check (nothing in the paper was changed)

1. **Table C9 gives no within-task interval for "Monty-ARC, hand-made fresh"**: the cell is `0.0 (3)`, while Table 3 marks it `0.0 ns (3)`. Figure 1 plots the point without an interval and labels it "ns (3 tasks, no interval)". Either add the interval to C9, or say in C9 that 3 tasks are too few for one.
2. **C9 carries no `ns` marks; Table 3 does.** They agree wherever I checked. Intervals that end exactly at 0.0 are treated as `ns`: 2020 program on ARC-AGI-2 within, [0.0, +18.8], and one column on PQA, both columns. That matches the paper's convention elsewhere (Table C1, Table 4's `re-arc` row). If C9 is meant to stand alone, it needs the `ns` marks or a note.
3. **Rounding, not errors.** Predict minus Miss from the rounded percentages gives 45.1, 65.9 and 16.1 for 2020 program ConceptARC, Qwen ARC-AGI-2 and 2020 program ARC-AGI-2. The tables give 45.0, 66.0 and 16.0, presumably from unrounded rates. A careful reader may notice.
4. **Table 8: the best random order beats verified first.** Random's maximum is above verified first at three samples (55.5 vs 55.0) and four (56.0 vs 55.0). That is consistent with "nearly all", but it is visible in Figure 3 and might draw a question.
5. **"Two samples" means different things in Table C5 and Table 8.** In C5 (Qwen + Monty-ARC merged, 75 tasks, 58 crowded) order matters. In Table 8 (Qwen alone, 0 crowded) it cannot. A reader moving between Section 7's text and Table C5 could be confused.
6. **Section 9 never defines "confident Monty-ARC answer".** Figure 4 ties it to the v5 heuristic of Appendix C. Consider adding "(the v5 heuristic)" to the merge bullet so the text and figure match.
7. **Panel labels.** Figure 1 uses "Qwen3.8-27B" as its panel title, as the brief asked; Table 3 says "Qwen".

---

## Changed in judge v8c, pass 1 (2026-11-03)

- **Figure 1** has 19 rows: Qwen's one-input ConceptARC row (planned; Table 3 and C9) is added as "ConceptARC, 1 input", with C9's intervals (+47.6 [+37.9, +57.1], +41.0 [+27.6, +54.5], 52 tasks). The Qwen3.8-27B panel has four rows; the one-column panel keeps the same row spacing with an empty last slot. Table 3 now has the row too, and its rows read "Qwen3.8-27B", as the panel does.
- **Figure 3**: random order is now the exact expectation over random orders, with a band from the 5th to the 95th percentile of 100,000 orders (`v8c_qwen.txt` §5): 52.0 (49.0–54.5) at three samples, 50.4 (47.5–53.5) at four. The old band was the minimum and maximum of 40 orders, and its top crossed verified first; the new one does not.
- **In the paper**, the captions are one line each (the figures carry their own legends): Figure 1 after Table 3, Figure 2 after the proof in 5.2 with a pointer in 5.1, Figure 3 after Table 8, Figure 4 after Section 9's bullets. Items 1, 2, 6 and 7 of the list above are resolved in the paper (C9's `ns` marks and 3-task cell, the v5-heuristic gloss, one LLM name). Figure 2 now appears before Figure 1; see `errors_fixed.md`, Judge v8c pass 1.
