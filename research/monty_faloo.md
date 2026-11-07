# Fold-agreement LOO (FA-LOO) for Monty-ARC v5

Frozen v5 code (byte-identical to the published notebook), wrapped from `research/monty_eval/` (`run_folds.py`, `faloo.py`, `module_loo_audit.py`, `run_persp.py`). Raw: `research/monty_faloo.json`, `research/monty_eval/results/faloo.json`.

**FA-LOO rule.** Learner A = the full 8-module Monty-ARC v5 system (its top pooled answer; no confidence rule). For each test input t and each demo i, A is re-run from scratch on the other n-1 demos (every module re-generates and re-selects its hypotheses: a true re-induction) and queried jointly on (x_i, x*_t), i.e. exactly the tournament model M_{i,n+1}. Answer y_hat only if (a) every fold model predicts its held-out demo and (b) all n fold models give the same test answer. A task is answered when every test input is.

## Headline

- **FA-LOO + (c) [the full-data system's top answer must equal the fold answer; this only removes answers, so the bound still holds]: distinct tasks 101/102 (99.0%), four standard splits 187/189 (98.9%), against v5 confident 96/98 (98.0%) and 179/183 (97.8%).** Wrong: f5aa3634. It drops 6 v5 confident answers (8d5021e8, 9565186b, c9e6f938, 00576224, aaef0977, ad38a9d0) and adds 10 (1f85a75f, 3aa6fb7a, c3f564a4, 1d0a4b61, c663677b, ca8f78db, cd3c21df, d56f2372, f823c43c, dbff022c).
- **Distinct tasks (n = 1147): FA-LOO answers 101/103 (98.1%); the v5 confident rule answers 96/98 (98.0%).** Both answer 92; FA-LOO drops 6 v5 confident answers and adds 11. (v5's top answer has pooled evidence >= 0.99 in 104 distinct tasks, 100 correct; the confident rule's 2:1 consensus keeps 98 of them.)
- **Four standard splits (1,920 task instances): FA-LOO 187/191 (97.9%) vs v5 confident 179/183 (97.8%).**
- **ARC-AGI-2 only.** AGI-2 eval: FA-LOO + (c) 4/4 (100.0%), v5 3/3 (100.0%); it adds dbff022c, which v5 declines because two fully evidenced hypotheses conflict. AGI-2 new-train: 1/1 (100.0%) vs 3/3 (100.0%); it loses the two n = 2 tasks.
- **Perspective voting (AGI-1 train, 8 D8 views).** v5 rule: 62/66 (93.9%) (4 false confident answers vs 1 with one view). FA-LOO with the v5 vote: 58/59 (98.3%); + (c): 58/58 (100.0%). P4: 60/61 (98.4%). **FA-LOO stops the inflation.**
- Empirical joint rate P(answer and wrong) over distinct tasks: 0.17% vs the worst-case bound mean 1/(n+1) = 24.7%.
- Cost: 1.7 CPU-hours for all folds of the 1,920 instances, 2.6x a single v5 pass (n x tests runs per task).

## 1. Per-module LOO: true re-induction or parameter re-fit after selection on all demos?

| Module | What its LOO re-runs per fold | Selected on all n demos | Verdict | Code |
|---|---|---|---|---|
| self-model | nothing: evidence = 1.0 for any configuration that reproduces every demo | configuration (mode, mask colour, symmetry kinds) | **no LOO** (fit only) | `symmetry.py:209-235` (`evidence=1.0` at :232) |
| periodic | the *learner* "first hypothesis in a fixed order fitting the n-1 demos" | hypothesis list (vanishing colours from all demos) | **learner-level re-induction over a leaked hypothesis list; the score is copied to every full-fit hypothesis; (b) not checked** | `periodic.py:116-129, 145-155` |
| dynamics | the *learner* "first hypothesis in a fixed order fitting the n-1 demos" | hypothesis list (colours, object types from all demos); 3000 cap | **learner-level re-induction over a leaked hypothesis list; the score is copied to every full-fit hypothesis; (b) not checked** | `dynamics.py:64-74, 151-155, 187-191, 210-243` |
| composition | the *learner* "first hypothesis in a fixed order fitting the n-1 demos" | hypothesis list (ratios, panel count, colours, output shape from all demos); 4000 cap | **learner-level re-induction over a leaked hypothesis list; the score is copied to every full-fit hypothesis; (b) not checked** | `composition.py:67-78, 127, 163-166, 194-216, 237-240, 256-284` |
| association | the *learner* "first hypothesis in a fixed order fitting the n-1 demos" | hypothesis list (source colours from all demos) | **learner-level re-induction over a leaked hypothesis list; the score is copied to every full-fit hypothesis; (b) not checked** | `association.py:42-48, 106-110, 123-153` |
| behavior | the change table, for a structure (seg, key, frame, R, ownership) fixed on all n demos | structure: up to 336 per task | **parameter re-fit after selection** (H/(n+1) regime) | `behavior.py:143-168` (filter :156, re-fit :163) |
| pattern | the pattern library, for a context type fixed on all n demos | context: 3 | **parameter re-fit after selection** (small H) | `pattern.py:88-108` (filter :97, re-fit :104) |
| field | the location->colour table, for an (anchor, code, period, write mask) structure fixed on all n demos (each demo must also fit alone) | structure: hundreds | **parameter re-fit after selection** | `field.py:98-150` (filter :128-131, re-fit :146) |

Measured on the 1,147 distinct tasks (`module_loo_audit.py`):

- **behavior**: 1827 structure candidates with LOO = 1.0 in 14 tasks; condition (b) holds automatically (every fold model predicts the test exactly as the full model) for 1815/1827; a fold model meets an unseen object type on the test in 0.
- **pattern**: 18 structure candidates with LOO = 1.0 in 11 tasks; condition (b) holds automatically (every fold model predicts the test exactly as the full model) for 18/18.
- **field**: 2 structure candidates with LOO = 1.0 in 1 tasks; condition (b) holds automatically (every fold model predicts the test exactly as the full model) for 2/2.
- **periodic**: LOO = 1.0 in 4 tasks; 0 of them hand the 1.0 to more than one distinct prediction (mean 1.0 full-fit hypotheses); the hypothesis list generated from a fold's own n-1 demos differs from the all-demo list in 1; fold learners agree on the test (b) in 4 with Monty's list and 4 with true re-induction.
- **dynamics**: LOO = 1.0 in 10 tasks; 0 of them hand the 1.0 to more than one distinct prediction (mean 2.7 full-fit hypotheses); the hypothesis list generated from a fold's own n-1 demos differs from the all-demo list in 6; fold learners agree on the test (b) in 10 with Monty's list and 10 with true re-induction.
- **composition**: LOO = 1.0 in 56 tasks; 2 of them hand the 1.0 to more than one distinct prediction (mean 1.86 full-fit hypotheses); the hypothesis list generated from a fold's own n-1 demos differs from the all-demo list in 11; fold learners agree on the test (b) in 56 with Monty's list and 54 with true re-induction.
- **association**: LOO = 1.0 in 3 tasks; 1 of them hand the 1.0 to more than one distinct prediction (mean 2.0 full-fit hypotheses); the hypothesis list generated from a fold's own n-1 demos differs from the all-demo list in 0; fold learners agree on the test (b) in 3 with Monty's list and 3 with true re-induction.

**Module alone under system-level FA-LOO** (true re-induction of each module; distinct tasks):

| Module | FA-LOO correct / answered | module's own LOO = 1.0 top answers (Table 6 of monty_ablations.md) |
|---|---|---|
| self-model | 9/9 (100.0%) | 9/9 (100.0%) |
| periodic | 9/9 (100.0%) | 4/4 (100.0%) |
| behavior | 11/11 (100.0%) | 13/16 (81.2%) |
| dynamics | 10/10 (100.0%) | 10/10 (100.0%) |
| composition | 53/55 (96.4%) | 55/56 (98.2%) |
| association | 3/3 (100.0%) | 3/3 (100.0%) |
| pattern | 10/11 (90.9%) | 10/11 (90.9%) |
| field | 0/0 | 1/1 (100.0%) |

## 2. System-level FA-LOO vs the v5 confident rule

| Split | FA-LOO (v5 vote, top answer) | v5 confident | both | v5 confident dropped by FA-LOO | new FA-LOO answers | FA-LOO wrong |
|---|---|---|---|---|---|---|
| AGI-2 eval | 4/4 (100.0%) | 3/3 (100.0%) | 3 | 0 | 1 | - |
| AGI-2 new-train (233) | 1/1 (100.0%) | 3/3 (100.0%) | 1 | 2 | 0 | - |
| AGI-2 train | 86/88 (97.7%) | 85/87 (97.7%) | 81 | 6 | 7 | 72ca375d f5aa3634 |
| AGI-1 eval | 38/39 (97.4%) | 33/34 (97.1%) | 33 | 1 | 6 | f5aa3634 |
| AGI-1 train | 59/60 (98.3%) | 58/59 (98.3%) | 56 | 3 | 4 | 72ca375d |
| **distinct (1,147), FA-LOO** | **101/103 (98.1%)** | **96/98 (98.0%)** | 92 | 6 | 11 | 72ca375d f5aa3634 |
| distinct, FA-LOO + (c) | **101/102 (99.0%)** | 96/98 (98.0%) | | 6 | 10 | f5aa3634 |
| distinct, FA-LOO + (c) or v5 confident (no bound) | 106/108 (98.1%) | | | | | |

Variants (distinct tasks): *v5-top*: FA-LOO 101/103 (98.1%); *v5-conf*: FA-LOO 71/71 (100.0%); *p4-top*: FA-LOO 101/103 (98.1%); *p4-conf*: FA-LOO 71/71 (100.0%). (*-conf*: each fold model must itself pass the confident rule; *p4*: the P4 vote below.)

v5 confident answers dropped by FA-LOO (distinct): 8d5021e8, 9565186b, c9e6f938, 00576224, aaef0977, ad38a9d0. Of the v5 confident wrong answers (9565186b, f5aa3634), FA-LOO answers: f5aa3634.

**What changes, and why** (distinct tasks):

- *Dropped, correctly:* 9565186b, v5's pooling false positive (42 duplicate behavior hypotheses at LOO 0.75): a fold model mispredicts its held-out demo.
- *Dropped, correct answers lost to leakage:* 00576224, 8d5021e8, c9e6f938 (composition, per-tile D8 poses). `_tile_hypotheses` solves the poses on all n demos, so v5's LOO = 1.0 was inflated. Re-induced on n-1 demos, the pose is ambiguous and one fold picks a pose that is consistent with its demos but wrong on the held-out one.
- *Dropped, too little data:* aaef0977 (field) and ad38a9d0 (behavior), both n = 2. A one-demo fold cannot pin down the structure, and a memorising behavior hypothesis wins that fold.
- *Added (all correct):* tasks where v5's learner-level LOO was 0.67 because one fold's first-fit hypothesis was another period or tiling, while the whole system's fold answer was right (1d0a4b61, c663677b, ca8f78db, f823c43c, 1f85a75f, 3aa6fb7a, c3f564a4, cd3c21df, d56f2372). Also dbff022c: two fully evidenced hypotheses conflict on all demos, so v5 declines, yet every fold agrees.
- *Wrong under FA-LOO:*
  - f5aa3634: the bottom-most-object proxy is consistent with every fold. No LOO variant can see a concept that is missing from the hypothesis space.
  - 72ca375d: the tournament event itself. Two selection proxies (symmetry, density) fit every demo. Each fold model picks density, which is first in the property order, predicts its held-out demo and is wrong on the test. Rule (c) catches it, because the full-data top answer is symmetry, which is correct.

Why v5 confident answers are dropped (distinct): (a) fold mispredicts held-out demo: 6.

**By number of demos (distinct tasks):**

| n demos | tasks | FA-LOO | v5 confident | bound 1/(n+1) |
|---|---|---|---|---|
| 2 | 193 | 15/15 (100.0%) | 15/15 (100.0%) | 0.333 |
| 3 | 651 | 47/49 (95.9%) | 42/43 (97.7%) | 0.250 |
| 4 | 214 | 22/22 (100.0%) | 22/23 (95.7%) | 0.200 |
| 5 | 58 | 13/13 (100.0%) | 13/13 (100.0%) | 0.167 |
| 6 | 20 | 3/3 (100.0%) | 3/3 (100.0%) | 0.143 |
| 7 | 8 | 0/0 | 0/0 | 0.125 |
| 8 | 2 | 1/1 (100.0%) | 1/1 (100.0%) | 0.111 |
| 10 | 1 | 0/0 | 0/0 | 0.091 |

**CPU cost** (sum of module CPU seconds, M4 Pro, 1 BLAS thread):

| Split | tasks | v5 single pass | all FA-LOO folds | ratio | fold CPU-s per task |
|---|---|---|---|---|---|
| AGI-2 eval | 120 | 216 s | 621 s | 2.88x | 5.18 |
| AGI-1 eval | 400 | 726 s | 1866 s | 2.57x | 4.67 |
| AGI-2 train | 1000 | 1007 s | 2566 s | 2.55x | 2.57 |
| AGI-1 train | 400 | 367 s | 956 s | 2.6x | 2.39 |

## 3. P4: re-vote without same-module duplicate pooling and without duplicate D8 views

P4 counts voters per module (the 8 perspective views of one module are one voter) and accumulates evidence only across distinct modules. On v5's single perspective this equals the cross-module rule of `monty_ablations.md` Table 7.

| Split | v5 confident | P4 confident | FA-LOO with P4 vote |
|---|---|---|---|
| AGI-2 eval | 3/3 (100.0%) | 3/3 (100.0%) | 4/4 (100.0%) |
| AGI-2 new-train (233) | 3/3 (100.0%) | 3/3 (100.0%) | 1/1 (100.0%) |
| AGI-2 train | 85/87 (97.7%) | 86/87 (98.9%) | 86/88 (97.7%) |
| AGI-1 eval | 33/34 (97.1%) | 33/34 (97.1%) | 37/38 (97.4%) |
| AGI-1 train | 58/59 (98.3%) | 59/59 (100.0%) | 60/61 (98.4%) |
| **distinct** | 96/98 (98.0%) | 97/98 (99.0%) | 101/103 (98.1%) |

## 4. Whole-task D8 perspective voting (8 views): does FA-LOO or P4 stop the inflation?

Offline re-vote of a per-module, per-perspective cache (`run_persp.py`, `p8_full.py`). It reproduces the paper-writer's real 8-view run (`research/paper/data/agi1_train_p8.json`) with 0 confident-flag mismatches over 400 tasks.

| AGI-1 train (400) | confident correct / answered | wrong |
|---|---|---|
| v5 1 view | 58/59 (98.3%) | 9565186b |
| v5 8 views | 62/66 (93.9%) | 0ca9ddb6 7447852a 834ec97d a5f85a15 |
| P4 1 view | 59/59 (100.0%) | - |
| P4 8 views | 60/61 (98.4%) | 9565186b |
| FA-LOO (v5 vote), 8 views | 58/59 (98.3%) | 72ca375d |
| FA-LOO (v5 vote), 8 views + (c) | 58/58 (100.0%) | - |
| FA-LOO (P4 vote), 8 views | 60/61 (98.4%) | 72ca375d |
| FA-LOO (P4 vote), 8 views + (c) | 60/61 (98.4%) | 72ca375d |
| FA-LOO (v5 vote), 1 view, for reference | 59/60 (98.3%) | 72ca375d |

The 4 false confident answers that 8-view v5 voting adds (0ca9ddb6, 7447852a, 834ec97d, a5f85a15) are behaviour answers whose pooled evidence (1.61-2.26) is built by counting the same module's views as separate voters. P4 (one voter per module, no cross-view accumulation) removes all 4. The error left under P4 at 8 views (9565186b) is a different mechanism: in some D8 view a behaviour structure reaches a genuine LOO of 1.0 for the wrong answer. Extra views add *hypotheses* (absolute-frame structures under rotation), not just copies of votes, and that is the H/(n+1) multiple-comparisons trap.

**FA-LOO stops both mechanisms.** A spurious structure that wins one view on all n demos rarely wins every fold and agrees on the test, and the view copies cannot raise a fold's top answer above a held-out-demo failure. With the v5 vote at 8 views, FA-LOO + (c) answers 58/58. Its one plain-FA-LOO error (72ca375d) is the 1-view tournament case above, unrelated to views. Cost: the 8-view folds took 1,767 s of wall time on 4 workers for AGI-1 train, about 7x the 1-view folds.


## 5. Caveats

- The bound needs the n demos and the test pair to be exchangeable; ARC test inputs are often chosen to be harder (54d9e175 is a measured case), so on ARC the bound is a heuristic and the measured rate is the evidence.
- It needs A symmetric in its demo multiset. Monty-ARC's modules build hypothesis lists from sorted colour and shape sets and order-free tables, so A is symmetric up to tie-breaking order. Measured by reversing the demo order (`sym_check.py`): AGI-2 eval: top answer identical in 120/120, confident flag identical in 120/120; AGI-1 eval: top answer identical in 400/400, confident flag identical in 400/400.
- Fold models are queried on the pair (x_i, x*_t) jointly (Monty modules only keep hypotheses that predict every query); this is the same symmetric pair query in both directions of the tournament, so the argument holds.
- With n = 2 each fold model sees one demo. FA-LOO still answers 15 distinct n = 2 tasks, the same count as v5 but not the same set: it loses aaef0977 and ad38a9d0 and gains others. On the AGI-2-only training split (25% of its tasks have n = 2) it keeps 1 of v5's 3 confident answers.
- A system-level FA-LOO multiplies CPU by about n x (number of tests), measured at 2.6x.
