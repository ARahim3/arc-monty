# Plan: one column, frozen once

Agent: one-column, started 2026-11-01 ~16:25 UTC. Spec: `research/tbt_proper/proposal.md`, experiments E1 and E2. E3 and E4 are on hold. This file is section 0 of the report. It is written before any solver opens test data, and it is hashed at the freeze with the code (`FROZEN.json`). Anything added later goes under "Addenda" at the bottom, dated and marked.

**What this is, plainly.** A new, small program. It is not Monty, and no Monty code runs in it. Frozen Monty-ARC v5 runs only as a comparator. The test asks about functional claims the theory's authors make about a system built this way. It does not test or refute the Thousand Brains Theory as neuroscience (grid cells, layers, thalamus), and a null here does not refute the theory, which can blame the implementation; only a success would say much.

## 0.1 The system

**One algorithm.** One `Column` class in `column.py`. A column learns a transition (x, y) under a motor command: at each sensed context it counts what was sensed next, in every form that explains it (unchanged, an absolute colour, a displacement within the input, a whole-grid pose). It predicts by one rule: for each cell, among stored contexts under that command that match the sensation at the cell itself, those with the most counted evidence along the path (weight 1/(1+distance), out to the column's reach) decide; the first form that explains all their occurrences wins, else a strict plurality, else no answer (keep the input). Exact matches and the search are the same rule: `check_search.py` compares the fast search with brute force on development data. Predicting no change counts as an answer only if no change has been seen under that command.

**Unified matching, the first build step.** The spike used counted evidence on static tasks and longest-context hashing on games. There is now only counted evidence. Its cost on development data is in section 0.8.

**Columns differ only in their sensor, their reach and, for cell-level sensors, whether a query is read in all eight whole-grid poses.** A population holds one column for each sensor at each reach (nine sensors, reaches 1, 2, 3, 6), plus the eight-pose form of the two cell-level sensors at reaches 1, 2, 3: 42 columns. It ranks them by how well each predicted transitions it had not learned, ties in list order. Settings are in `settings.py`, one list for every task of every kind, games included. Sensors: cell colour; mask (shape without colour); child object ID at a location in the child's canonical frame, with (`objc`) and without (`obj`) colour; how many objects share this shape, at a location in the child's frame (`objn`, the count sensor); location in the nearest object's canonical frame, in four variants (`near`, `nearc`, `nears`, `nearsc`). The motor signal is the command itself.

**Two rule choices made on development data, for speed:** a stored context must match the sensation at the cell (hypotheses start from what is sensed here), and a click's frame reaches 8 cells, with one label beyond. On static development tasks the first nets to zero (−2, +1, +1 solves on ARC-AGI-1 eval, ARC-AGI-1 train and the new tasks). Neither lowered the game numbers in section 0.8 against the spike's.

**What differs between static tasks and games, all of it.** None of these is a branch by task family inside the column; `column.py` has no notion of family.
1. Delivery of data. Ordered data (a game) is a stream: each transition is predicted, then learned. Unordered data (a task's demos) gets held-out evidence by leaving each demo out. Both feed the same `learn` and `predict`, and the same evidence: how often a column predicted what it had not learned.
2. A static task has one motor command; a game has several. A click adds a click-centred frame to the sensor and says what it landed on. Static tasks have no clicks, so this never fires there.
3. The output frame. If a task's output size differs from its input size, `frames_for` offers resampled frames (up, tile, down). On equal sizes, which is every game, it offers only the identity.
4. Scoring. Static tasks: two attempts per test pair. Games: the top answer, on the playfield. The harness passes the game's UI mask (`research/arc3_wm/wm2.ui_mask`), used for scoring, for held-out evidence and for the moving frame's anchor.
5. The moving-frame sensor (M4) runs only on games, because a static task has no previous step to move from.

## 0.2 Data

Fresh sets come from `neoneye/arc-dataset-collection`, commit `41441c3f`, in `external/tbt_fresh/repo`, JSON read with `python -I`; nothing in that folder is run. Licence, size, quality and exact overlap are in `results/fresh_check.json`, recorded before any solver run.

| Set | Tasks / test pairs used | Clusters | Exact pairs shared with earlier sets | Other overlap, kept and disclosed | Licence per readme |
|---|---|---|---|---|---|
| `arc-community` | 23 / 26 | tasks | 0 of 90 | Inputs up to D8 and colour renaming: 6 of 86 | none stated |
| `nosound` | 9 / 9 | tasks | 0 of 36 | none | DbCL |
| `dbigham` | 20 / 20 (21 / 21 less one) | tasks | 2 of 76, both in `4938f0c2-easy`, **excluded** | `56dc2b01-easier` shares an exact input with development; up to D8 and colour 11 of 70 | MIT |
| `Sequence_ARC` | 25 / 25 | tasks | 0 of 103 | Up to D8 and colour 2 of 99 | Apache-2.0 |
| `arc-dataset-tama` | 1,000 / 1,567 | 50 types | 0 of 4,624 | One task shares an exact input with development; up to D8 and colour 31 of 3,630; 49 tasks have grids wider than 30 cells | MIT |
| `PQA` extract, secondary | 70 / 210 | 7 types | 0 of 700 | none | none stated |
| `IPARC`, excluded | 600 / 600 | not run | 0 of 3,970 | none | MIT |

Earlier sets checked: the 1,147 development tasks (ARC-AGI-1 train and eval, ARC-AGI-2 train and eval, including the 233 new tasks), ConceptARC corpus, MinimalTasks, Mini-ARC, 1D-ARC. The fresh sets share no pair with each other. Overlap by exact pair does not rule out overlap of concepts.

**Set list, fixed.**
- *Primary stratum A, hand-made fresh, pooled, clusters = tasks:* `arc-community`, `nosound`, `dbigham`, `Sequence_ARC`.
- *Primary stratum B, `arc-dataset-tama`, clusters = its 50 generated types.* Its tasks were generated by a program its author wrote, so this is not hand-made task by task, and tasks of a type are near-copies.
- *Secondary, labelled, not in any verdict:* `PQA` (the collection's extract of 10 tasks from each of 7 generated types), clusters = types; licence unspecified.
- *Excluded before any run:* `IPARC`. Its own catalogue entry says almost no task has been solved by humans, lists invalid tasks and advises avoiding it; 200 of its tasks also have 11 demos. Licence and overlap were fine; the reason is quality, and no result of any solver on it exists here.
- *Spent, labelled, plan fixed first:* ConceptARC (corpus, clusters = tasks), Mini-ARC (tasks), 1D-ARC (18 generated types). These feed S1, S2, S4 as labelled rows and are the only data for S3 and E2 static.
- *Games:* the 13 held-out ARC-AGI-3 games (`arc3_agent/v7/split.py`), main trajectories, 240 recorded transitions each, read as data; no game code runs.
- *Not used:* `research/generator_control/` tasks, `re-arc`.

**Licences.** `arc-community` and `PQA` state none, per the collection's readme; `nosound` DbCL; `dbigham`, `arc-dataset-tama`, `IPARC` MIT; `Sequence_ARC` Apache-2.0. Used as data here, not redistributed.

**Items.** One item = one test pair with its task's demos, as `research/monty_heldout/`; the other test inputs of a task are never shown to it. Monty's spent-set rows are read from `research/monty_heldout/results/*_base.jsonl`. On fresh sets frozen v5 runs through `monty_fresh.py` (`arcmonty/` imported unchanged, wrappers as `research/monty_heldout/`), real test role only, one view; demo roles are not run, to save CPU.

## 0.3 What was already known about each test set

- **13 held-out games.** The project has worked with them: agent v7, v8, and the world-model probe that produced the comparators, on all 25 games. The column has never seen them, and the spike did not open them. This agent read `HANDOFF.md` sections 0 and 4 (agent scores on these games; "Monty columns as next-frame world model: negative") and `research/paper/v8/paper.md` Appendix D, not `research/arc3_world_model.md`. It also saw, while checking a log's format, the first three lines of `research/arc3_wm/results/wm2_m2.log`, which include two held-out games' counts of Monty-ARC's confident non-identity answers (`ft09` 0/0, `dc22` 59/78). Every setting was chosen on the 12 tuning games only. Game mechanics may have shaped earlier project code, but no code from those projects is in the column.
- **ConceptARC, Mini-ARC, 1D-ARC.** Spent. This agent read all of `research/monty_heldout.md` and paper v8 sections 4, 6.1 and 6.4–6.6: Monty-ARC's results on them, by group, module and rule, the first-place program's and GPT-4's counts on ConceptARC, Qwen's and the 2020 program's held-out split, and that six ConceptARC groups give Monty-ARC 1 of 180. The column has never run on them.
- **The count sensor's motivation, disclosed.** The spike's author added the count sensor (`objn`) knowing those six groups give 1 of 180, including a group called Count. So S3 is not a clean test of a sensor chosen blind, and that sensor exists because of something known about ConceptARC. It predates this agent and adds nothing on development data. No sensor was added or changed by this agent for any reason drawn from ConceptARC.
- **Fresh sets.** Before the freeze this agent saw their readmes, file names, sizes, counts and overlap numbers, and no grid. Names show that `Sequence_ARC` tasks are 1-D versions of ARC-AGI-1 training tasks (they carry those ids) and that some `dbigham` tasks are variants of ARC-AGI-1 tasks. So exact-pair freshness does not mean concept freshness there, for the column or for Monty-ARC, both developed on ARC-AGI-1 training tasks. The readme of `arc-dataset-tama` and its folder names show its 50 generated types.

## 0.4 Tuning

Everything was chosen on development data only: ARC-AGI-1 train and eval, ARC-AGI-2 eval, the 233 new ARC-AGI-2 tasks, and the 12 tuning games. The proposal's spike numbers are development numbers and are not results. After the freeze no change is made to the column, its sensors or its settings. A crash on a static item counts as no answer and is reported; a crash on a game leaves that game out of that arm and is reported; a task over its budget (`settings.BUDGET`) gets no answer and is reported. Later changes to the analysis go in Addenda and are labelled post hoc.

## 0.5 Arms and falsifiers

Thresholds are the proposal's. Theory-specific claims are marked *. "Full" is the frozen population. All game comparisons are paired by transition, exact match on the playfield, on transitions where something changed on the playfield, CI by game. Static comparisons are pass@2 on test pairs, two attempts in every arm, CI by the set's clusters.

| Arm | Claim | Comparison | Fails if |
|---|---|---|---|
| M1 | A column needs the motor signal | Full minus the same population told nothing about the action (`nomotor`: one command, no click frame). 13 games | Loss under 5 points, or CI includes 0 |
| M2 | One column can replace eight modules as a world model | Full minus Monty-ARC columns (`M_play_fallback`, `research/arc3_wm/results/wm2_m2.jsonl`, k = 3), on the changed transitions shared with the probe | CI includes 0 or favours Monty-ARC |
| M3 | It adds something beyond a simple rule | Full minus object-relative repeat (`B1rel_play_play`, same rows) | CI includes 0 |
| M4a* | A location in a moving frame adds prediction | Local context plus moving-frame columns, minus local context (`local+moving` − `local`); and one column, colour × moving frame, minus colour at the same reach | Upper CI bound under +3 points |
| M4b* | A location in the nearest object's frame adds prediction | Local context plus nearest-object columns, minus local context (`local+near` − `local`); and one column, colour × nearest-object frame, minus colour | Upper CI bound under +3 points |
| M5* | Behaviour in the column's own frame adds prediction | Full minus full with next sensations stored only as unchanged or a colour (`colour_only`) | Upper CI bound under +3 points |
| M6 | Integrating actions with no new sensation holds up | Open-loop rollout minus unchanged frame, horizons 2, 4, 8, from every 12th transition, same level, no reset in between, top column at the start, exact playfield | Below baseline at horizon 4 |
| S1 | One algorithm covers the ground of eight | Column pass@2 / frozen Monty-ARC v5 pass@2, same test pairs, stratum A and stratum B | Ratio under 0.25. Supports if at least 0.5 with lower bound above 0.25; otherwise inconclusive |
| S2* | Objects as features or frames add solves | All sensors minus cell-level sensors only (colour, shape-free mask), two attempts each, stratum A and stratum B | CI includes 0 |
| S3a | Counting as a walk along a 1-D frame helps | With the count sensor minus Monty-ARC's 1 of 180, six weak ConceptARC groups (AboveBelow, Count, HorizontalVertical, InsideOutside, Order, SameDifferent), CI by task. Spent and labelled | No separation from 1 of 180 |
| S3b | The same, attributable to the sensor | With minus without the count sensor, same pairs | CI includes 0 |
| S4 | The trust rule holds on a fourth learner | Held-out split as paper Table 5: right on the test, fold programs that predict their held-out demo minus those that miss it, stratum A and stratum B; within-task control beside it | Between-task split doesn't separate |
| E2 static* | Models learned on earlier tasks help a new task of the same kind | ConceptARC, leave one task out, pass@2: same-concept library minus alone, CI by concept group (16). Other-concept library as the second arm, with equal bulk: 9 tasks drawn from other concepts | CI includes 0 or is negative |
| E2 games* | The same across games | `local` with a library from the 12 other held-out games (first 80 transitions each) minus `local` alone, leave one game out, all transitions, exact playfield | CI includes 0 or is negative |

"Local context" (`local`) means the cell-level sensors at every reach, with their eight-pose forms: 14 columns. S2's "cell-level sensors only" is the same set. "One column" means colour at reach 6.

Library use, one rule: a column's own evidence decides unless it is below 75% of the possible (fixed in the spike), and then memory answers where it has more evidence. E2 static uses every column; E2 games uses `local` columns only, for CPU. Libraries hold every labelled same-size pair of the chosen tasks.

**Tightenings and readings I add, disclosed.**
- "One column" in the proposal's M2 and S1 means one repeated algorithm. "Full" is 42 copies of it that differ in their sensors, ranked by held-out evidence. That is the frozen system, and it is what those arms test.
- M4 is measured two ways because the population can ignore a column it finds useless: the population with and without those columns, and one column with its sensor replaced, as in the spike. The falsifier applies to each. If only one clears it, the verdict is "mixed".
- M4 and M5 "hold" only if the gain's CI excludes 0. "Upper bound at least +3 but CI includes 0" is reported as "not falsified, no separation", not as support.
- M6 fails if the point estimate at horizon 4 is below baseline. Above baseline counts as holding only if the CI excludes 0.
- S3: the proposal's falsifier is S3a. I add S3b, because other sensors could lift the six groups with no help from counting. S3 as a claim about counting holds only if both separate.
- S4's falsifier is the between-task split. Its within-task control is reported beside it. A split that separates between tasks and not within means that it sorts easy tasks from hard ones rather than programs; I will say so.
- Fold programs, as paper Table 5: a fold is the whole population retrained on n−1 demos with its own held-out ranking. Its program is the top-ranked column that gives an answer on the test input. Programs that give no test answer are left out of the split, and count as wrong in the held-out-vs-test mean.

**Secondary, descriptive, in no verdict.** All-transition exact rates; the same comparators at k = 12; confident non-identity answers on games (the answering column predicted its last three transitions of this command), coverage and precision next to Monty-ARC's; per-game tables; leave-one-game-out ranges for every game comparison; E2 at first use of a command; FA-LOO + (c), (a)+(b), plain (a), fit and top-answer precision, and FA-LOO + (c) minus fit; held-out minus test as a mean with a cluster bootstrap; the same rules and split for frozen Monty-ARC v5 on fresh sets, which is its new clean row; PQA; spent-set rows.

## 0.6 Statistics

Percentile cluster bootstrap from `research/monty_heldout/stats.py`, 10,000 resamples, seed 0; paired differences on the same resamples. "Separates" = the 95% CI excludes 0. Clusters are games, tasks or generated types as listed. **No 50:50 sign test by task for held-out vs test:** it has the wrong null under exchangeability (`research/paper/judge_v8b/review.md` section 3.3, Error 1). That comparison is the mean with a cluster bootstrap. Bootstraps over few clusters run narrow: 13 games, 50 types, 16 concept groups.

**Primary comparisons: 17, with no multiplicity correction.** M1, M2, M3, M4a, M4b, M5, M6 (7); S1, S2, S4 on each of two strata (6); S3a, S3b (2); E2 static, E2 games (2). M4's two forms count as one each. A CI that just excludes 0 is weak evidence.

**Per-game breakdown is mandatory.** The proposal warns that spike gains came from `ls20`, `sc25`, `su15`. Those are tuning games, so they cannot appear here, but the same concentration can. Every game comparison is shown per game, with the range from leaving out one game.

## 0.7 What each outcome would mean

- **M1 holds:** expected and close to trivial; a column that isn't told the action can't say what it does. Fails: the column is broken, or changes in these games don't depend on the action.
- **M2 holds:** one repeated algorithm predicts changed frames better than eight hand-written modules wrapped as a world model. It says nothing about static tasks. Fails: no support for replacing the modules as a world model.
- **M3 holds:** the column adds something beyond repeating the last change. Fails, the likely outcome with 13 games: M2's win may be just what a simple rule gets.
- **M4, M5 hold:** first evidence for reference frames, or behaviours in their own frame, on a benchmark built by someone else; a real lead. Fail: these mechanisms don't earn their place on these games in this column. TBP could fairly reply that sprites rarely change pose, so these are a poor place to look; the static arm S2 is where pose varies.
- **M6:** whether integrating actions with no new sensation beats assuming nothing changes. Fails at horizon 4: path integration in this form does not hold up.
- **S1:** whether one algorithm covers the ground of eight on tasks neither has seen. Under 0.25: no. At least 0.5 with lower bound above 0.25: yes. In between: inconclusive.
- **S2:** whether objects as features or frames add solves. On tasks of the ARC-AGI-2 kind the proposal expects nothing.
- **S3:** whether counting as a walk along a 1-D frame reaches concept groups our modules miss. The sensor's motive is disclosed above, so a pass is weaker than usual, and a fail is the likely outcome.
- **S4:** whether the trust rule's held-out split holds on a fourth learner frozen before these sets, with premise (F) clean. Separates: a further row for the paper's Table 5.
- **E2 holds:** models persisting across tasks help a new task of the same kind. Fails, the likely outcome: exact features at locations don't carry, and transfer needs categories, which TBP lists as unfinished. Same-concept against other-concept separates a concept's transfer from generic bulk.
- **If M2 and S1 both fail, the column is a toy:** the paper keeps the proposition (proposal section 2.1) and reports the attempt in two lines.

## 0.8 Development numbers: what one rule costs

Development data only, chosen after looking at it, so flattered. Not results.

**Static tasks, pass@2.** Spike = two matching rules, chosen after looking at the data. "Cells only" and "no count" are the same switches S2 and S3b use.

| Split | Tasks | One rule, frozen columns | Spike | Monty-ARC v5 | Cells only | No count sensor | Top answer right at held-out evidence 1.0 |
|---|---|---|---|---|---|---|---|
| ARC-AGI-1 train | 400 | 44.5 | 44.3 | 80 | 35.5 | 44.5 | 27/30 |
| ARC-AGI-1 eval | 400 | 11.0 | 12.0 | 46 | 9.0 | 11.0 | 4/6 |
| ARC-AGI-2, 233 new | 233 | 1.0 | 2.3 | 9 | 2.0 | 1.0 | 1/2 |
| ARC-AGI-2 eval | 120 | 0 | 0 | 4 | not run | not run | 0/0 |

So one rule costs about 1 point on ARC-AGI-1 eval and 1.3 on the new tasks, and gains 0.2 on ARC-AGI-1 train. Eight-pose columns at reach 6 would give 12.5 on ARC-AGI-1 eval but cost about ten times the game CPU, so they stop at reach 3; that is part of this cost. The count sensor adds nothing on any development split, as the proposal said.

**Games, 12 tuning games, 2,880 transitions, 1,197 changed; exact playfield; CI by game.** One colour column at reach 6: all 66.5%, changed 29.7%, against the spike's 64.1% and 26.0%. So on games one rule gains 3.7 points on changed transitions. The full population gets more, from sensors the spike did not run on games.

| Arm | All transitions | Changed | Comparison on changed, points |
|---|---|---|---|
| Full | 68.6% (no change: 58.4%) | 34.2% | |
| No motor signal | 57.9% | 1.0% | Full minus this +33.2 [+20.3, +46.4] |
| Colour-only form | 70.0% | 38.3% | Full minus this −4.1 [−7.0, −1.3] |
| Local context | 66.2% | 28.1% | |
| Local + moving frame | 66.2% | 28.4% | Minus local +0.3 [−0.1, +0.8] |
| Local + nearest-object frame | 66.9% | 29.7% | Minus local +1.7 [0.0, +4.5] |
| One column, colour | 66.5% | 29.7% | |
| One column, × moving frame | 63.6% | 27.5% | Minus colour −2.2 [−5.5, +0.7] |
| One column, × nearest-object frame | 66.5% | 24.6% | Minus colour −5.1 [−11.6, +1.8] |
| Local + library | 64.6% | 27.9% | Minus local, all transitions −1.7 [−2.5, −0.9]; first use −33.3 [−41.8, −23.8] |

On the 1,081 changed transitions shared with the probe at k = 3: full 36.9%, Monty-ARC columns 8.6%, object-relative repeat 16.4%; +28.3 [+18.4, +39.2] and +20.5 [+4.6, +38.0]. Those gains are uneven: `ls20`, `sc25`, `su15` and `tr87` supply most of them, and against the repeat rule `bp35` and `g50t` go the other way. Open-loop rollouts minus unchanged frame: +10.0 [+2.1, +19.6], +6.4 [−3.0, +18.3], +5.8 [−4.2, +17.9] at horizons 2, 4, 8. Confident non-identity answers: column 10.1% coverage at 66.7% precision, Monty-ARC 3.6% at 63.2%.

**Checks run on development data.** Fast search against brute force: 29,595 queries, 0 mismatches. Stream against demos on the same column, full data: 73 of 73 answers equal. Monty wrapper against earlier recorded rows: 240 fields on 30 tasks, 0 differ. No-change labels equal the probe's on every shared transition. The whole pipeline, analysis included, ran on tuning games and on samples of 80 ARC-AGI-1 tasks.

**Size.** `column.py` is 369 lines of code, over the proposal's "about 300"; sensors take about 85 of them. `column.py` names no task family; `check_one_algorithm.py` counts such words in its code and finds none.

## 0.9 Order of work after the freeze

1. `freeze.py` records SHA-256 of `column.py`, `settings.py`, `static.py`, `games.py`, `data_sets.py`, `monty_fresh.py`, `run_all.py`, of `analyse.py` as it stands, and of this plan down to "## Addenda". `run_all.py` refuses to open test data unless the code hashes match.
2. Games, every arm. 3. Static sets, column. 4. Frozen v5 on fresh sets. 5. E2 on ConceptARC. 6. `analyse.py` writes `results/analysis.json`.
Before trusting numbers: no-change labels must equal the probe's on every shared transition, and frozen Monty-ARC's spent-set rows must be the recorded ones (`research/monty_heldout/results/`).

At most 4 CPU workers on this Mac, short checks included. Stop rule: if not frozen by 12:00 UTC 2026-11-04, stop and report. Report by 12:00 UTC 2026-11-05.

## Addenda

### Addendum 1, 2026-11-02 05:30 UTC, after all results. Post hoc, descriptive, in no verdict
`post_hoc.py`: top-answer counts, how often each system answers, concentration by type, and which column is first right. `verify.py`: frozen hash, re-score of a random sample of each set from raw JSON in a fresh process (all agree), one game re-run row by row (240 of 240), items whose test input equals a demo input (2 of 1,567 on `arc-dataset-tama`, none solved; none elsewhere). No frozen file changed, and `analyse.py` is as hashed. Under the plan's M4 reading, M4a is "mixed" (population not falsified, single column falsified) and M4b is "not falsified, no separation" in both forms.
