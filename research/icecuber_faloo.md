# FA-LOO on the 2020 Kaggle first-place program ("icecuber"), a learner frozen before the data existed

Agent: icecuber-faloo. Section 0 was written on 2026-11-01 before any output of the program on ConceptARC, Mini-ARC, 1D-ARC, MinimalTasks or ARC-AGI-2 existed. It is not edited afterwards; later changes go in marked addenda.

## 0. Plan (written before any result on these sets)

**Why.** The paper's rule, FA-LOO, has two weak spots in its evidence: Monty-ARC answers few tasks, and we developed Monty-ARC ourselves, so premise (F) rests on our word. icecuber was frozen in 2020 by someone else, before all of these sets existed, and it answers far more. A bad result for the rule will be reported as a result.

**Known when this was written.** Paper v8 tables and `research/monty_heldout.md`, so all of Monty-ARC's numbers. From the authors' `data.xlsx`: column totals only (first place 249 of 480; a column `ensemble_indices` non-empty on 252; the two columns disagree on 11 items; attempt positions 1 / 2 / 3 about 174 / 47 / 29 in that second column). From the ConceptARC paper: the program ran from its GitHub code, in the Kaggle text format, with three guesses per test input; depth and flags are not stated. Input grid sizes of each set. Timing on ARC-AGI-1 only (below). No output of the program on any set in this study has been seen.

**Program.** `top-quarks/ARC-solution`, commit `9407072659de1270358c2ba34c527785214dd68b`, licence MIT (copyright 2020 top-quarks; not copied into this project; it stays on the VMs). `git log -- src headers Makefile safe_run.py run.py`: the code last changed 2020-06-08; the 2025 commit touches only the README. Commit `613bb0c`, "Exactly as submitted with 0.794 LB", differs from this one by removal of unused code, base paths and the `eval` flag (31 files, 12 insertions, 3,125 deletions). Built on the VM with g++ 11.4, the repository's own Makefile (`-std=c++17 -g -O2`), with the one change the README documents for test data: `eval = 1` on line 75 of `src/runner.cpp`, which is also the as-submitted value. Binary sha256 starts `83641dc4619c48c4`, the same on three VMs. **Build check:** the unmodified build, depth 2, on the repository's own 419 ARC-AGI-1 evaluation test inputs gives 129 of 419, exactly the number the README states.

**What the code does (read on the VM).**
- *Ranking.* A candidate's score is `goods - 0.01 * (max_depth + 0.001 * cnt_pieces)`, with `goods` the number of demonstrations it reproduces. Candidates with `goods = 0` are dropped. Candidates are sorted by score (`std::sort`, deterministic, not stable) and the first three distinct test images are kept. It is not first-fit: it scores over everything it found.
- *Fit.* **Not every candidate fits all demonstrations.** Greedy composition runs over subsets of the demonstrations, so a candidate with `goods = 1` can be the top answer if nothing better exists. The score reveals the fit: I count an answer as fitting all `n` demonstrations it saw if its score exceeds `n - 0.499` (derived from the score formula, flip-run scores included).
- *Test input.* **It uses the query while fitting.** `bruteSize(test_in, train)` predicts the output size using the query; a DAG is built on the query too; a piece must exist on every DAG, the query's included, and a candidate is rejected if its image on the query is invalid. The query's content does not enter the match against demonstrations. Colour normalisation uses the demonstrations only. With `eval = 1` no test output is read, and none is ever sent to a VM.
- *Demonstration order.* The raw program can depend on it: the subset enumeration covers only the first five demonstrations (`min(1<<T, 32)`; flip runs double `T`, so this binds from `n = 3`), and tied scores keep the order of generation. So the wrapper fixes the order.

**Learner, fixed before running on any set here.** One learner call is `f(S, q)`: the recipe of `safe_run.py` that made the Kaggle submission, on a single task file holding the demonstrations `S` in canonical order and one query `q`.
- Four processes: `./run 0 3` (depth 3), `./run 0 23` and `./run 0 33` (depth 3 with each demonstration also given flipped, two flip types), `./run 0 4` (depth 4).
- Merge as `safe_run.py`, re-implemented in my script: all answer lines of the finished processes, sorted by (score, image) descending, first three distinct images. The placeholder a process writes when it has no candidate (score −1) is dropped, so "no answer" stays no answer.
- Canonical order: sorted by (area, height, width, grid text) of the input, as `gkey` in `research/arc2/faloo_qwen.py`, with ties broken the same way on the output. So the learner is symmetric in `S` by construction.
- Limits, one setting for all sets: 16 GiB address space per process (`ulimit -v`; the Kaggle machine had 16 GB in all and `safe_run.py` kills above 15.6 GB in total); 3,600 s wall clock per process; at most 150 processes per VM, at most 80 of them depth 4. A process that hits a limit gives no answer lines; the other three still count, as in `safe_run.py`. A call with no answer from any process abstains. Counts of `mem`, `timeout` and `crash` are reported per set.
- Why this setting: it is what was submitted, and the likeliest thing the ConceptARC authors ran (their paper gives no depth), and it is feasible. **Difference from `safe_run.py`:** its limits scale with the depth-3 run (depth 4 gets 40× its time and memory) and it stops everything at 8.55 h on 4 cores; here limits are fixed and there is no global stop, so every process gets its chance.
- **Timing used to choose this.** The first 60 files in sorted order of the repository's `dataset/evaluation` (ARC-AGI-1 public evaluation), first test input, native order, all four configurations, 60 workers, one VM; 389 s wall. Accuracy on them was not computed. Depth 3 median 8 s, max 34 s; flip runs median 20 s, max 144 s; depth 4 median 122 s, max 334 s; 12 of 60 depth-4 processes ran out of 16 GiB, all on tasks with demonstrations of at least 600 cells in total. Mean about 3.3 core-minutes per call. ConceptARC's median task (277 cells) is half the size of that sample's population (543), so the time limit should rarely bind.

**Folds.** The program answers one query at a time, so a fold on queries {held-out input, test input} is **two runs on the same `n−1` demonstrations**: `M_i(x_i) = f(S\i, x_i)` and `M_i(x_test) = f(S\i, x_test)`. This fits the theorem: `A(S, {a, b}) = (f(S, a), f(S, b))` is symmetric in `S` and in the queries, so `M_ab = M_ba`, and the program has no seed. A fold's "top answer" is the first of its merged list. A task with one demonstration gives a fold with no examples: abstain. No answer counts as wrong on a fold. Other test inputs of a task are never shown. A process killed by the wall-clock limit is the one thing that can vary with machine load; it is counted and reported.

**Items, clusters, statistics.** One item is one test pair with its task's demonstrations, keys as in `research/monty_heldout/` (checked equal to Monty's on all four sets). Clusters: ConceptARC by task (160), Mini-ARC by task (149), 1D-ARC by generated type (18), MinimalTasks by task (16), ARC-AGI-2 by task. Percentile cluster bootstrap, 10,000 resamples, seed 0, from `research/monty_heldout/stats.py`. "Separates" means the 95% CI of a difference excludes 0. Multiplicity is not corrected. All numbers for a set use the items with every run back; anything partial is labelled.

**Rules, real test role.**
- `usual`: the top answer of the full-data merged list. pass@2 and pass@3 from the same list.
- `(a)`: every fold predicts its held-out demonstration; the answer is the full-data top answer.
- `FA-LOO (a)+(b)`: (a), and all folds give the same test answer; the answer is that one.
- `FA-LOO + (c)`: and the full-data top answer is the same.
- Row I added, not in the brief: `usual + fit`, the top answer only if it fits all demonstrations, as the nearest thing to the paper's "fit to demos".
Each is reported as correct/answered, precision with CI, coverage, tasks answered and tasks with a wrong answer, joint P(answer and wrong) against mean 1/(n+1).

**Planned comparisons, per set.**
1. FA-LOO + (c) minus `usual`, precision, paired CI.
2. Held-out split: among fold programs that give a test answer, precision on the test of those that predict their held-out demonstration against those that miss it, paired CI. Secondary, my addition: the same among those whose test answer fits every demonstration the fold saw (the counterpart of Qwen's "verified").
3. Exchangeability: right on held-out against right on test across real-role folds, abstain = wrong, discordant counts, clusters with more of each, sign test; same code as paper Table 5 (`revise_monty.py`). For 1D-ARC also clustered by task, descriptive. Power, reported honestly: the CI half-width and the discordant count, next to Qwen's +5.2.
4. How often (b) fails among roles passing (a), how many of those are a fold abstaining; how often (c) fails given (a)+(b); distance from first-fit (lemma of §5.3): among roles passing (a), how many have any fold test answer different from the full-data answer; share of `usual` top answers that do not fit all demonstrations.
5. Floor: `1 - mean(1/(n+1)) / c` with `c` the coverage of FA-LOO + (c). Does it exceed 0 on any set?
6. Next to Monty-ARC, descriptive, FA-LOO + (c) of each, real role, same items: both answer (precision of each), only one answers (precision), neither. Also the same for top answers.

**Check before trusting anything.** Full-data pass@3 on ConceptARC against the authors' 249, item by item against their column `First Place ARC-Kaggle` (their criterion is any of three guesses). Pass if pass@3 is within 249 ± 15 and item agreement is at least 90%; the bounds are mine, set from their own two columns disagreeing on 2.3% of items. If it fails, stop and find out why before any fold result is reported. Differences are listed either way.

**Code checks on a fixed sample (seed 0; 130 runs from the run list, `make_checks.py`; no rule uses them).** The same run again: is the program deterministic under load and across VMs? Demonstrations reversed: how much does the raw program depend on order? (The wrapper is symmetric whatever this shows.) All four configurations.

**Sets, in order.** ConceptARC corpus (480), Mini-ARC (149), 1D-ARC (901), MinimalTasks (48). Then, as a comparator, ARC-AGI-2 public evaluation without ARC-AGI-1 tasks: **113 tasks, not 114.** Six share an id with ARC-AGI-1, and `db695cfb` has a different id but shares 5 of its 6 pairs with ARC-AGI-1's `55783887`; the author saw those, so it is excluded before any result. ARC-AGI-1 tasks are not results for (F). Pairs: `CenterMinimal#1`'s test pair equals one of its demonstrations in the published data; it stays in.

**Where it runs.** Only on disposable spot VMs: `arc-ice-*`, and `arc-v6e-r5`, `arc-v6e-r3` lent by the lead. Only text and JSON come back; results are parsed as data, grids validated.

**Stop rule.** Report by 12:00 UTC 2026-11-03 with whatever is complete, partial results labelled. ConceptARC's numbers go to the lead as soon as they are in.

### Addendum A to the plan (2026-11-01 08:25 UTC; written after seeing process status counts only, before any accuracy on any set)

**1D-ARC has grids the program cannot read.** 286 of its 901 tasks have a grid wider than 30 cells (widths up to 93), outside ARC's format, and the program's reader stops on an assertion (`src/read.cpp:140`). All of `1d_denoising_1c`, `1d_denoising_mc`, `1d_pcopy_1c`, `1d_pcopy_mc` and 43 of 50 `1d_padded_fill`, plus a few in other types. No other set has such grids. The rule does not change: those runs have no answer, so they abstain and count as wrong on folds. Precision is unaffected. Coverage and the exchangeability test get diluted, so I add, for 1D-ARC, the same numbers on the items where every run was readable, marked secondary. Padding or cutting the grids would be a modification of the input and is not done.

**Status of the lent VM.** `arc-v6e-r3` and `arc-ice-3` were preempted at about 08:03–08:10 UTC, about ten minutes into the run; `arc-v6e-r5` finished its slice and took over the rest. Results from the dead VMs up to the last pull are kept; what was lost is re-run.

### Addendum B to the plan (2026-11-01 08:29 UTC; after the reproduction check on full-data runs, before any fold result on any set)

The check passed (numbers in section 1). To explain the 10 item differences I add one run list not in the plan: full-data runs on all 480 ConceptARC test pairs **in the file's native demonstration order**, which is what the authors presumably ran, same four configurations. It enters no rule. It tells whether the canonical order accounts for the differences and whether it costs solves.

## 1. Results

Generated by `research/icecuber_faloo/make_report.py` from `results_*.json`; the reading is mine. Brackets are 95% cluster-bootstrap intervals; `ns` = the interval includes 0. All sets complete, nothing partial. 11,637 calls of the program, 99 core-hours, about 55 minutes wall clock on one to three VMs.

**In short.** On a learner nobody here touched, the rule's sorting holds up on the four unseen sets where it can answer. Fold programs that predict their held-out demonstration are right 60–86% of the time, those that miss it 15–21%. FA-LOO + (c) lifts precision over the usual test by 29–46 points. **But the hoped-for fix did not happen on ConceptARC:** icecuber answers more than Monty-ARC only under the usual test. Under FA-LOO + (c) it answers 15 pairs in 6 tasks against Monty-ARC's 44 in 18, so ConceptARC's evidence stays thin, and its 73.3% has a very wide interval. On ARC-AGI-2 the rule answers nothing, because the program solves almost nothing there. The floor `1 - 1/((n+1)c)` stays vacuous on every whole set.

### Table 1. Main result, real test role

| Set | Items | Clusters | Usual test | Coverage | FA-LOO + (c) | Coverage | Clusters answered / with a wrong answer | Joint P(answer and wrong) | Mean 1/(n+1) |
|---|---|---|---|---|---|---|---|---|---|
| ConceptARC | 480 | 160 | 182/480 = 37.9% [32.1, 43.8] | 100.0% | 11/15 = 73.3% [38.5, 100.0] | 3.1% | 6 / 3 | 0.83% | 28.3% |
| Mini-ARC | 149 | 149 | 66/149 = 44.3% [36.2, 52.3] | 100.0% | 29/32 = 90.6% [79.3, 100.0] | 21.5% | 32 / 3 | 2.01% | 22.7% |
| 1D-ARC | 901 | 18 | 412/615 = 67.0% [48.6, 84.1] | 68.3% | 176/183 = 96.2% [89.7, 99.3] | 20.3% | 12 / 4 | 0.78% | 25.0% |
| MinimalTasks | 48 | 16 | 31/48 = 64.6% [47.9, 81.2] | 100.0% | 12/12 = 100.0% [100.0, 100.0] | 25.0% | 4 / 0 | 0.00% | 26.5% |
| ARC-AGI-2 eval (comparator) | 160 | 113 | 2/160 = 1.2% [0.0, 3.2] | 100.0% | 0/0 | 0.0% | 0 / 0 | 0.00% | 26.0% |

### Table 2. All rules, correct/answered = precision [CI]; coverage in the next row of each pair

| Rule | ConceptARC | Mini-ARC | 1D-ARC | MinimalTasks | ARC-AGI-2 eval (comparator) |
|---|---|---|---|---|---|
| Usual: top answer | 182/480 = 37.9% [32.1, 43.8] | 66/149 = 44.3% [36.2, 52.3] | 412/615 = 67.0% [48.6, 84.1] | 31/48 = 64.6% [47.9, 81.2] | 2/160 = 1.2% [0.0, 3.2] |
| coverage | 100.0% | 100.0% | 68.3% | 100.0% | 100.0% |
| Top answer, only if it fits all demonstrations (my added row) | 152/310 = 49.0% [41.9, 56.0] | 48/76 = 63.2% [52.1, 73.8] | 370/445 = 83.1% [70.5, 91.9] | 29/41 = 70.7% [53.1, 86.1] | 1/5 = 20.0% [0.0, 50.0] |
| coverage | 64.6% | 51.0% | 49.4% | 85.4% | 3.1% |
| Plain (a), full-data answer | 14/21 = 66.7% [33.3, 93.3] | 29/32 = 90.6% [79.3, 100.0] | 192/205 = 93.7% [86.8, 97.2] | 12/12 = 100.0% [100.0, 100.0] | 0/0 |
| coverage | 4.4% | 21.5% | 22.8% | 25.0% | 0.0% |
| FA-LOO (a)+(b) | 11/17 = 64.7% [27.3, 93.3] | 29/32 = 90.6% [79.3, 100.0] | 177/184 = 96.2% [89.7, 99.3] | 12/12 = 100.0% [100.0, 100.0] | 0/0 |
| coverage | 3.5% | 21.5% | 20.4% | 25.0% | 0.0% |
| FA-LOO + (c) | 11/15 = 73.3% [38.5, 100.0] | 29/32 = 90.6% [79.3, 100.0] | 176/183 = 96.2% [89.7, 99.3] | 12/12 = 100.0% [100.0, 100.0] | 0/0 |
| coverage | 3.1% | 21.5% | 20.3% | 25.0% | 0.0% |
| pass@1; @2; @3 | 182; 226; 251 of 480 | 66; 76; 78 of 149 | 412; 445; 461 of 901 | 31; 37; 38 of 48 | 2; 2; 2 of 160 |
| FA-LOO + (c), tasks all right (Clopper-Pearson) | [12, 88]% | [75, 98]% | [35, 90]% | [40, 100]% | n/a |
| FA-LOO + (c), n = 2; n >= 3 | 1/4; 10/11 | 0/0; 29/32 | 0/0; 176/183 | 0/0; 12/12 | 0/0; 0/0 |

1D-ARC on the 615 items where every run was readable (Addendum A, secondary; 14 types): usual 412/615 = 67.0% [48.8, 84.2], FA-LOO + (c) 176/183 = 96.2% [90.1, 99.2], coverage 29.8%. ConceptARC at n = 2 is 1/4 and at n >= 3 is 10/11, the same pattern as Monty-ARC (13/19 and 22/25).

## 2. Did it reproduce?

**Yes.** Full-data pass@3 on ConceptARC is 251 against the authors' 249, with 470 of 480 items agreeing (97.9%), inside the plan's bounds. No process hit a limit on these items in either order; in the canonical full-data runs depth 4 peaked at 182 s and 7.0 GB, inside `safe_run.py`'s per-process limits.

**The differences (Addendum B).** With the file's native demonstration order, pass@3 is 252 and agreement with the authors is 477 of 480 (99.4%), with nothing only they solve. So 7 of the 10 differences come from my canonical order. The other 3 (`AboveBelow3#0`, `AboveBelow3#1`, `InsideOutside8#2`) I solve and their sheet marks wrong. There the right answer is the top answer of plain depth 3 in my run, so neither depth nor limits explain it; I cannot explain these three, and the published data or their scoring may have changed. Their sheet's other column, `ensemble_indices`, disagrees with `First Place` on 11 items and with my native run on 14; what that column is, the sheet does not say, but on the 245 items both it and my native run solve, the right answer sits at the same position in the top three in 245 of 245. That exact match is good evidence the authors ran this same recipe. **Canonical order costs almost nothing:** pass@1 182 in both, pass@2 226 vs 229, pass@3 251 vs 252.

The README's own number also reproduces on this build: depth 2 gives 129 of 419 on ARC-AGI-1 evaluation.

## 3. Planned comparisons

### Comparison 1. FA-LOO + (c) minus the usual test, precision points

| Set | FA-LOO + (c) minus usual (planned) | FA-LOO + (c) minus plain (a) | FA-LOO + (c) minus top-that-fits (my added row) |
|---|---|---|---|
| ConceptARC | +35.4 [+1.1, +61.7] | +6.7 [-2.8, +13.3] ns | +24.3 [-10.0, +50.4] ns |
| Mini-ARC | +46.3 [+35.1, +57.6] | +0.0 [+0.0, +0.0] ns | +27.5 [+14.9, +40.1] |
| 1D-ARC | +29.2 [+12.8, +46.3] | +2.5 [+1.2, +3.9] | +13.0 [+6.0, +22.5] |
| MinimalTasks | +35.4 [+18.8, +52.1] | +0.0 [+0.0, +0.0] ns | +29.3 [+13.9, +46.5] |
| ARC-AGI-2 eval (comparator) | n/a | n/a | n/a |

It separates on all four sets with answers. ConceptARC's lower limit is barely above 0 and rests on 6 tasks, and bootstraps over so few clusters are anti-conservative. Against the fairer baseline, an answer that at least fits, the lift does not separate on ConceptARC. Fold agreement and (c) add a measurable +2.5 over plain (a) on 1D-ARC, unlike on Monty-ARC, where they never separated; they add nothing on Mini-ARC or MinimalTasks. That +2.5 rests on 18 clusters and 22 rejected answers, so it is weak.

### Comparison 2. Held-out split: precision on the test of fold programs that give an answer

| Set | Predict held-out: right on test | Miss held-out: right on test | Difference (planned) | Same, only answers that fit all the fold saw (my addition) |
|---|---|---|---|---|
| ConceptARC | 60.4% [50.6, 69.4] of 285 | 15.3% [12.4, 18.4] of 993 | +45.0 [+35.3, +54.6] | +47.6 [+36.5, +58.0] |
| Mini-ARC | 74.4% [63.7, 83.8] of 203 | 15.1% [10.4, 20.1] of 325 | +59.3 [+47.8, +69.8] | +67.4 [+55.6, +77.4] |
| 1D-ARC | 84.8% [73.0, 91.7] of 983 | 17.5% [12.5, 25.1] of 862 | +67.3 [+55.4, +75.8] | +62.6 [+52.9, +69.8] |
| MinimalTasks | 85.7% [68.9, 95.2] of 63 | 21.3% [9.3, 35.2] of 75 | +64.4 [+44.6, +80.3] | +68.1 [+46.5, +85.8] |
| ARC-AGI-2 eval (comparator) | 16.7% [0.0, 50.0] of 6 | 0.6% [0.0, 1.7] of 468 | +16.0 [-0.6, +48.8] ns | +21.4 [-3.4, +46.4] ns |

This is the strongest result, and it needs no trust in us: the learner was frozen in 2020. Qwen's counterpart is 83.3% vs 17.4%. On ARC-AGI-2 there are 6 predicting programs, so that row says little.

### Comparison 3. Exchangeability: right on held-out vs right on test, real-role folds, abstain = wrong (paper Table 5)

| Set | Folds | Held-out / test | Difference, points | CI half-width | Held-out only / test only | Clusters more held-out : more test | Sign p | Monty-ARC, difference; discordant |
|---|---|---|---|---|---|---|---|---|
| ConceptARC | 1281 | 22.2% / 25.3% | -3.0 [-6.3, +0.2] | 3.3 | 113 / 152 | 27:54 | 0.004 | +0.9 [-0.8, +3.0]; 33 / 21 |
| Mini-ARC | 528 | 38.4% / 37.9% | +0.6 [-4.6, +6.0] | 5.3 | 52 / 49 | 25:32 | 0.427 | -0.2 [-2.8, +2.5]; 15 / 16 |
| 1D-ARC | 2703 | 36.4% / 36.4% | -0.1 [-1.0, +0.9] | 0.9 | 149 / 151 | 5:6 | 1.000 | -1.2 [-2.8, +0.1]; 47 / 79 |
| MinimalTasks | 138 | 45.7% / 50.7% | -5.1 [-14.0, +2.9] | 8.4 | 9 / 16 | 2:5 | 0.453 | - |
| ARC-AGI-2 eval (comparator) | 483 | 1.2% / 0.8% | +0.4 [-0.6, +1.6] | 1.1 | 5 / 3 | 3:2 | 1.000 | - |

1D-ARC clustered by task (descriptive): -0.1 [-1.6, +1.5], tasks 95:126, sign p = 0.043; rates on readable items only 53.3% / 53.4%.

**Reading, including power.** This test has far more discordant folds than Monty-ARC's (265 vs 54 on ConceptARC, 300 vs 126 on 1D-ARC). A shift of Qwen's size, +5.2, would separate on ConceptARC (half-width 3.3) and 1D-ARC (0.9), is about the width of the interval on Mini-ARC (5.3), and would not separate on MinimalTasks (8.4). **On ConceptARC the two statistics disagree:** the planned interval just includes 0, while the cluster sign test gives 27:54, p = 0.004. If anything real is there, test outputs are *easier* than demonstrations for this program, the opposite sign to Qwen on ARC-AGI-2 and to Monty-ARC's lean on the same set (+0.9), so the direction depends on the learner. I report it as a possible failure of (E), not an established one, with no correction for multiplicity. Test and demonstration inputs are about the same size (115 vs 116 cells, post hoc), so size does not explain it. Mini-ARC and 1D-ARC show no difference in rates; 1D-ARC by task leans the same way only in the sign test (95:126). Judged: tests easier than demonstrations would mean fewer confident errors on the test role, not more, so this direction would not threaten the bound. ARC-AGI-2 has almost nothing to compare: 8 discordant folds. So this learner **neither confirms nor contradicts** Qwen's finding there.

### Comparison 4. How far from first-fit

| Set | Roles passing (a) | (b) fails | Of those, a fold abstains | Full-data answer on those | (c) fails given (a)+(b) | Any fold differs from full-data answer | Top answers not fitting all demonstrations |
|---|---|---|---|---|---|---|---|
| ConceptARC | 21 | 4 (19.0%) | 0 | 2 right, 2 wrong | 2 | 6 | 170 of 480 |
| Mini-ARC | 32 | 0 (0.0%) | 0 | 0 right, 0 wrong | 0 | 0 | 73 of 149 |
| 1D-ARC | 205 | 21 (10.2%) | 0 | 16 right, 5 wrong | 1 | 22 | 170 of 615 |
| MinimalTasks | 12 | 0 (0.0%) | 0 | 0 right, 0 wrong | 0 | 0 | 7 of 48 |
| ARC-AGI-2 eval (comparator) | 0 | 0 (n/a) | 0 | 0 right, 0 wrong | 0 | 0 | 155 of 160 |

**icecuber is not first-fit, and it shows.** It ranks by a score that allows partial fits, a third of its top answers on ConceptARC do not fit all demonstrations, and (b) fails in 19% of ConceptARC's and 10% of 1D-ARC's roles passing (a), against 0 of 912 for Monty-ARC (its count includes demo roles). So the lemma of §5.3 does not apply: for this learner plain (a) has no proof, and only the agreement condition brings it under the theorem. Agreement rejects both right and wrong answers: 18 right and 7 wrong across the two sets.

### Comparison 5. The floor `1 - mean(1/(n+1)) / c`

| Set | Coverage, FA-LOO + (c) | Mean 1/(n+1) | Floor | Vacuous |
|---|---|---|---|---|
| ConceptARC | 3.1% | 28.3% | -806.3% | yes |
| Mini-ARC | 21.5% | 22.7% | -5.8% | yes |
| 1D-ARC | 20.3% | 25.0% | -23.1% | yes |
| MinimalTasks | 25.0% | 26.5% | -5.8% | yes |
| ARC-AGI-2 eval (comparator) | 0.0% | 26.0% | n/a | yes |
| 1D-ARC, readable items (secondary) | 29.8% | 25.0% | 16.0% | no |

**Vacuous on every whole set.** Mini-ARC and MinimalTasks come close (coverage 21.5% vs 22.7%, 25.0% vs 26.5%). It stops being vacuous only on 1D-ARC's readable items, a secondary subset, and there it guarantees 16% against 96.2% measured. So the theorem still gives no useful precision here; every precision is measured.

### Comparison 6. Next to Monty-ARC (descriptive), same items, real role

| Set | FA-LOO + (c), both answer: right | icecuber only: right/n | Monty only: right/n | Neither | Top answers, both have one: right |
|---|---|---|---|---|---|
| ConceptARC | 7: icecuber 4, Monty 5 | 7/8 | 30/37 | 428 | 136: icecuber 66, Monty 55 |
| Mini-ARC | 5: icecuber 4, Monty 4 | 25/27 | 4/4 | 113 | 55: icecuber 25, Monty 20 |
| 1D-ARC | 14: icecuber 14, Monty 9 | 162/169 | 152/158 | 560 | 191: icecuber 121, Monty 80 |
| MinimalTasks | 0: icecuber 0, Monty 0 | 12/12 | 5/5 | 31 | 25: icecuber 15, Monty 7 |
| 1D-ARC, readable items | 14: icecuber 14, Monty 9 | 162/169 | 41/46 | 386 | - |

**The two certificates barely overlap:** 7 of 52 answered pairs on ConceptARC, 5 of 36 on Mini-ARC, 14 of 341 on 1D-ARC, 0 of 17 on MinimalTasks. Both rules stay precise on what only they answer. Monty-ARC has the larger set on ConceptARC, icecuber on Mini-ARC and MinimalTasks; on 1D-ARC they are about equal, but 112 of Monty-ARC's answers are on tasks icecuber cannot read.

**Where both answer (post hoc, 26 pairs):** they give the same grid on 16, and all 16 are right (4, 3 and 9 on ConceptARC, Mini-ARC and 1D-ARC). They differ on 10, so at least one is wrong there; icecuber is right on 6 of those, Monty-ARC on 2, neither on 2. Two of icecuber's four wrong ConceptARC answers, `CompleteShape7 #1` and `#2`, are wrong under Monty-ARC's FA-LOO too (paper Appendix B), with different wrong grids. So those two pairs defeat two very different learners in different ways.

## 4. Code checks

- **Determinism:** the same run again, under full load: 130 of 130 identical merged lists.
- **Order in the raw program:** demonstrations reversed: top answer unchanged in 123 of 130, whole list in 101 of 130. So the raw program does depend on order, and premise (S) needs the canonical order. The wrapper sorts before running, so the learner is symmetric by construction.
- **Limits:** no process timed out on any set. Memory stopped 90 depth-4 processes, all on ARC-AGI-2. 2002 1D-ARC calls could not read their grids (Addendum A), which is 286 of 901 items.
- **Leak:** no run holds a test output; test outputs never left the laptop. `CenterMinimal#1`'s test pair equals one of its demonstrations in the published data.
- **Independent recount:** `verify.py` reads tasks afresh, finds runs by content, re-parses raw lines and recomputes all counts by another code path; it matches `analyse.py` on all five sets. Monty-ARC's counts in comparison 6 add up to its published totals.

## 5. Caveats

- **Few answered tasks on ConceptARC.** FA-LOO + (c) rests on 6 tasks, 3 of them with a wrong answer; tasks all right, Clopper-Pearson [12, 88]%. The planned CI [38.5, 100] says the same. Bootstraps over so few clusters are anti-conservative.
- **1D-ARC.** 286 of 901 tasks are unreadable, so coverage is understated and whole types are missing; the remaining types are near-copies, clustered by type. Monty-ARC's table includes those tasks, so its row is not on the same population.
- **What (F) gives.** The program is frozen, but I chose the wrapper, the settings and the canonical order. All of it was fixed before any output on these sets, in writing, but the plan's timestamp is my word too: this file has no independent hash. The program's author saw ARC-AGI-1, and the sets share no exact pair with it (checked earlier in `research/monty_heldout.md`), though concept-level overlap is not ruled out.
- **Fit is inferred** from the score, not observed, and is conservative for answers from flip runs. It affects only the rows I added.
- **The test input enters the search,** as a filter on what can be built and through output-size prediction. That is allowed, since each fold run is then one symmetric function of (demonstrations, query), but it means a fold's two predictions come from two different searches, not one program applied twice. "Fold program" here means that pair of runs.
- **No demo-role rotation was run** (not in the brief), so tournament events and the leave-two-out split of Table 4 have no counterpart here.
- **Multiplicity.** No correction. A CI just excluding 0, like ConceptARC's comparison 1, is weak evidence.

## 6. Sentence for the paper

> On the 2020 Kaggle winner, frozen before these sets existed, FA-LOO + (c) lifted precision from 38–67% to 73–100% on four unseen sets, and fold programs predicting their held-out demonstration were right 60–86% against 15–21%; but coverage was 3–25%, ConceptARC rests on six tasks, it cannot read 286 of 901 1D-ARC tasks, and ARC-AGI-2 got no answers.

(57 words, counting `+` and `(c)` as words.)

## 7. Files and resources

- `research/icecuber_faloo.json`: all numbers. `research/icecuber_faloo/`: scripts (`make_jobs.py`, `make_checks.py`, `make_slice.py`, `analyse.py`, `verify.py`, `make_report.py`, `vm/`), `results_*.json`, raw JSONL in `raw/`, run lists in `export/`. Icecuber's code is not in this project; it was built and run only on the VMs.
- Program: `top-quarks/ARC-solution`, commit `9407072659de1270358c2ba34c527785214dd68b`, MIT licence (copyright 2020 top-quarks). Re-run: `make_jobs.py`, `make_checks.py`, `make_slice.py VM`, `vm/setup.sh` and `vm/runner.py` on the VM, `vm/pull.sh`, then `analyse.py`, `verify.py`, `make_report.py`.
- Reproduce on a VM only: this runs third-party code, and the user's approval covered that one repository on disposable spot VMs.
- **TPU, 2026-11-01 08:59 UTC.** Created by me: `arc-ice-1` (us-east1-d, still PROVISIONING, never used), `arc-ice-2` and `arc-ice-3` (europe-west4-a, both SUSPENDED, VMs PREEMPTED; `arc-ice-2` was preempted before SSH came up). Lent by the lead: `arc-v6e-r3` (europe-west4-a, SUSPENDED, preempted during this run) and `arc-v6e-r5` (us-east1-d, ACTIVE, READY, idle now). I stopped `srv_a` and `srv_b` on both lent VMs, as the lead allowed. **Third-party code ran on `arc-v6e-r5`, and its clone, build and last results are in `/mnt/data/ice`; do not put tokens on that VM.** Nothing was deleted.
