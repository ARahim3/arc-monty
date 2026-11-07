## 1. Verdicts

Each verdict applies the rule fixed in section 0. All results are for Monty-ARC v5 as implemented; a null here is a result about these modules, not about the neocortex.

- **Claim 1, object-centred frames: survives for solves, not for trust.** Canonical frames beat grid-aligned frames on the two unseen sets where pose can matter: ConceptARC +6 test pairs [+1, +12] (5:0 discordant tasks, sign p = 0.06), Mini-ARC +4 [+1, +8] (4:0, p = 0.13); on 1D-ARC the two arms are identical. Confident answers get no more precise (behaviour alone: ConceptARC 3/6 vs 0/0, Mini-ARC 5/6 vs 5/5; system FA-LOO + (c) on ConceptARC: -4.5 [-12.5, 0.0], does not separate), and `both` adds nothing over `canon` on unseen sets (0 solves, 0 wrong; dev +2, +2). Removing the object anchor altogether costs more on 1D-ARC (+168 [+48, +313]) and Mini-ARC (+10 [+3, +18]), but does not separate on ConceptARC (+6 [-1, +14]).
- **Claim 2, test by predicting the unseen: survives, and it is the strongest result.** Held-out evidence lifts precision over fit-to-demos by about the same margin on unseen sets as on development: v5 minus fit-only is +27.3 [+20.2, +34.8] on dev, +27.6 [+11.3, +45.4] on ConceptARC, +48.3 [+30.0, +66.7] on Mini-ARC, +28.2 [+13.4, +47.0] on 1D-ARC. Absolute precision falls: FA-LOO + (c) is 99.0% on dev and 79.5%, 88.9%, 93.6% on the unseen sets (dev minus set: +19.5 [+6.9, +34.7], +10.1 [-2.7, +36.4], +5.4 [+0.3, +20.7]); v5 is 98.0% and 85.7%, 100%, 93.8%. **Fold agreement adds no measured precision anywhere** (FA-LOO + (c) minus v5: -6.2 [-15.1, +1.8], -11.1 [-36.4, 0.0], -0.2 [-4.2, +0.1]; the rule's value here is its proof, not its accuracy).
- **Claim 3, many columns vote: complementarity survives, the vote itself shows no measured effect.** Almost every solve comes from one module (98.3%, 75.0%, 99.5%; Mini-ARC is below the planned 80% line). On all three unseen sets the items answered at evidence >= 0.99 are exactly the union of what the modules answer alone, and a baseline with no pooling and no voter counts solves the same items, with precision that does not separate from the pool's. Top answers backed by two or more modules are too rare to judge: 1/4, 5/5, 1/2 (dev 9/9). @@P8VERDICT@@
- **What is missing (judged, section 6):** relations and counting first. Six ConceptARC groups give 1 of 180 test pairs, against 83-91% for humans.

## 2. Data and method

| Set | Why it is unseen | Items | Clusters for CIs |
|---|---|---|---|
| ConceptARC corpus | 0 of 905 distinct pairs shared with the 1,147 development tasks | 480 test pairs | 160 tasks |
| Mini-ARC (Apache-2.0, `external/heldout/mini-arc`) | 0 of 671 | 149 | 149 tasks |
| 1D-ARC (MIT, `external/heldout/1d-arc`) | 0 of 3,545 | 901 | 18 generated types |
| ConceptARC MinimalTasks (attention checks, very easy) | 0 of 93 | 48 | 16 tasks |

Frozen `arcmonty/`, imported unchanged. Every module's candidates are cached for every role and fold (`run_cache.py`), then every rule and subset is re-voted offline with the frozen vote code (`revote.py`, `rules.py`). `global` needs a monkeypatch of `behavior._frame_coords`; nothing in `arcmonty/` is edited.

**Verification (`results/verify.json`), all exact:** 4,962 fold answers and 1,761 full-data answers match `rotate_concept.jsonl`; 480 of 480 v5, fit and pass@2 values match `concept_full.jsonl`; filtering cached hypotheses by frame equals a real run with `behavior.FRAMES` patched on all 480 items, both arms; the 8-view re-vote equals a real `monty_arc.candidates(perspectives=range(8))` on 60 random ConceptARC items; v5 and pass@2 at 1 and 8 views equal real runs on a random sample of each extra set (`verify_extra.py`); 20 published development numbers are reproduced (101/102, 96/98, frame ablation, Table 6). CIs differ from the lead's 79.5% [64.5, 92.2] by 0.1 because of the bootstrap seed.

## 3. Claim 1: frames

{{T5}}

{{T6}}

{{T7}}

Reading:
- **Solves.** The canon-minus-abs gap is the same size on ConceptARC as on development, and only development fails to separate. On 1D-ARC the two arms have identical solves and confident counts (judged cause: one-row objects have almost no pose to normalise). All discordant tasks go to `canon`: 9:0 summed over the unseen sets (descriptive; sign p = 0.004).
- **These solves are mostly not confident.** Of the 6 ConceptARC items only `canon` solves, 2 have evidence >= 0.99 and a right top answer (CompleteShape5 #0, #1), 1 has a wrong top answer at evidence >= 0.99 and only attempt 2 right (TopBottom3D8 #2), 1 has evidence 0 and a wrong top answer (CompleteShape6 #0), and 2 have evidence 0 and a right top answer. Of Mini-ARC's 4, 3 have evidence 0 and 1 has 0.94. At system level, canon minus abs in FA-LOO + (c) precision is -4.5 [-12.5, 0.0] on ConceptARC (+3 right, +3 wrong answers), and does not separate.
- **The dev result for `both` does not replicate.** On unseen sets `both` adds no solve and no wrong answer over `canon`. On ConceptARC it costs FA-LOO + (c) 3 right answers (35/44 vs 38/47, -1.3 [-5.0, 0.0], does not separate): the three ExtendToBoundary5 pairs, which come back when the `abs` hypotheses are removed.
- **`abs` is not the null for "object-centred".** It keeps the object anchor, so canon vs abs tests pose normalisation only. `global` removes the anchor (the table is indexed by grid coordinates; objects still choose the key and the cells). `canon` minus `global` is large on dev and 1D-ARC, +10 on Mini-ARC, and does not separate on ConceptARC's real role (+6 [-1, +14]; it does on demo roles, +31 [+4, +66]). At system level other modules fill part of the gap: it separates on dev and 1D-ARC only. Of `global`'s 5 ConceptARC solves, none has evidence >= 0.99.
- **Removing behaviour (post hoc observation).** It costs solves on every set: 58 to 48, 20 to 11, 198 to 20. On ConceptARC FA-LOO + (c) then improves (41/47 vs 35/44, +7.7 [+1.2, +17.3]), because behaviour hypotheses win folds (section 4). On Mini-ARC it loses answers (6/6 vs 8/9) and on 1D-ARC it collapses (14/19 vs 161/172), so this is not a general effect.

## 4. Claim 2: prediction

{{T1}}

{{T2}}

{{T3}}

{{T4}}

Reading:
- **Calibration order.** On every unseen set, real and demo roles, precision at evidence >= 0.99 is above [0.5, 0.99), which is above evidence 0. The (0, 0.5) bucket is too small to order (at most 1 real-role item per set; demo roles 9/12, 4/14, 0/5; dev 0/4). Evidence >= 0.99 minus below separates everywhere, at about the dev size: +68.1, +70.7, +74.7 against +71.0. The step from >= 0.99 to [0.5, 0.99) separates on 1D-ARC and ConceptARC's demo roles, but not on the real roles of ConceptARC (+41.5 [-23.5, +86.4], 4/10 in the middle bucket) or Mini-ARC (+20.2 [-16.7, +62.0]).
- **Per module on ConceptARC, calibration holds where solves are.** Composition 17/17 and dynamics 17/18 at evidence >= 0.99. Self-model falls from 9/9 on dev to 6/9, periodic from 4/4 to 1/4, behaviour from 13/16 to 3/6. All 10 wrong top answers at evidence >= 0.99 come from these: self-model 3, periodic 3, behaviour 3, dynamics 1. Self-model's evidence is fit-only by construction (`monty_faloo.md`), so its 1.0 never contained a held-out test. Dynamics is the module that falls on 1D-ARC (16/21).
- **Real test vs demo roles.** The ConceptARC gap (+10.5 [-4.2, +24.5]) **does not separate**, and neither do Mini-ARC (+2.0) or 1D-ARC (-0.6). The judge's reading that the gap "points at exchangeability failing" is not established by these numbers. CompleteShape is the largest single contributor: 6/10 real vs 8/8 demo, and leaving it out shrinks the gap to +4.0 [-11.7, +18.6] (Table 13). That is descriptive, with no per-group test.
- **Dev flattered the certificate.** Development's real role was above its demo roles (99.0% vs 95.9%), the opposite sign to ConceptARC's, which is consistent with the judge's view that development raised real-role precision but does not test it. Joint P(answer and wrong) is still far under the worst case on unseen sets (Table 1). The theorem is not contradicted; its bound stays loose.

{{T12}}

- **What FA-LOO changes against v5.** On dev its additions were 10/10. On unseen sets they are 6/10, while what it drops was 22/23 right (pooled v5 only minus FA-LOO only: +35.7 [+2.1, +75.0], descriptive, barely separates). On ConceptARC, all 3 wrong FA-LOO-only answers had two or more conflicting fully evidenced answers, which is what v5's 2:1 rule declines. So does Mini-ARC's single one.
- **The sets on ConceptARC.** Both rules answer 38 pairs, 32 right. v5 only: ExtendToBoundary5 #0-2, MoveToBoundary3 #0-2, MoveToBoundary4 #0, FilledNotFilled9 #0-1, ExtractObjects3 #0 (all right), CompleteShape9 #1 (wrong). FA-LOO + (c) only: ExtractObjects1 #2, ExtractObjects3 #1, TopBottom2D1 #1 (right), CleanUp10 #1, CompleteShape5 #2, TopBottom3D8 #2 (wrong). Wrong under both: 6 pairs, listed below.
- **Why FA-LOO drops right answers (measured).** All 11 v5-only answers on ConceptARC fail on (a). For 9 of the 10 right ones (dynamics), the dynamics module alone passes FA-LOO, and the full system passes once behaviour is removed: a behaviour hypothesis wins that fold's vote and mispredicts the held-out demo. The system-level wrapper is paying for competition between modules.
- **v5's second attempt does not flatter it.** Scoring v5 and fit-only on the top answer alone gives identical counts on all three unseen real roles (`results/*_tables.md`, rows "top answer only").

**The ConceptARC wrong answers (real role), hand-read. Causes are judged; everything else is measured.**

| Pair | Wrong under | Module, hypothesis | n | Cells wrong | Judged cause |
|---|---|---|---|---|---|
| CleanUp1 #2 | v5, FA-LOO | self-model, repair | 2 | 2 | Test noise forms 2-cell runs; demo noise is isolated cells. Test outside the demos' range. |
| CleanUp10 #1 | FA-LOO | periodic, extend/panels | 2 | 45 | Fills the grid solid. The right cross was the second fully evidenced answer; v5 declines the conflict, FA-LOO's folds all pick the wrong one. |
| CompleteShape1 #2 | v5, FA-LOO | self-model, repair | 2 | 9 | A whole block is missing in the test; demos miss only small parts. Test outside the demos' range. |
| CompleteShape5 #2 | FA-LOO | behaviour, colour/canon | 2 | 3 | Test has shapes and poses the table never saw. 4 conflicting answers, v5 declines. |
| CompleteShape7 #1, #2 | v5, FA-LOO | periodic, extend/frames | 2 | 15, 32 | Both demos fill the same region, so "fill that region" fits every fold. The test's region differs. Proxy for "bounding box of the marks". |
| CompleteShape9 #1 | v5 | self-model, repair | 2 | 1 | The hole sits near a triangle's apex; demo holes sit on straight edges. FA-LOO correctly abstains: a fold misses its held-out demo. |
| FilledNotFilled9 #2 | v5, FA-LOO | dynamics, connect | 4 | 3 | "Connect walls along each row" stands in for "fill the container", and the test's broken wall separates them. Same class as dev's f5aa3634: no LOO sees a concept outside the hypothesis space. |
| TopBottom3D8 #1 | v5, FA-LOO | behaviour, any/canon | 4 | 1 | Over/under stored as a local table instead of a depth relation; test crossing geometry differs. |
| TopBottom3D8 #2 | FA-LOO | behaviour, any/canon | 4 | 4 | Diagonal test line against straight demo lines. 2 conflicting answers, v5 declines. |

Grouped (judged): test outside the demos' range 5 pairs; a proxy that fits every fold 4; two fully evidenced rules, wrong one first 1. Seven of the 10 pairs have only 2 demos, where each fold sees one demo. Images: `research/monty_heldout/results/wrong_concept/`.

## 5. Claim 3: voting

{{T8}}

{{T9}}

{{T10}}

Reading:
- **Complementary: yes, and which module matters flips with the benchmark.** Composition makes 20 of ConceptARC's 58 solves and none on Mini-ARC or 1D-ARC; behaviour makes 179 of 198 on 1D-ARC. Association and field solve nothing on ConceptARC, and pattern solves nothing there either. Mini-ARC's 75.0% (all 5 shared items are behaviour with pattern) is below the planned 80% line.
- **It is a portfolio.** On all three unseen sets the items the system answers at evidence >= 0.99 are exactly the union of what the modules answer alone (ConceptARC: 44/54 = 6/9 + 1/4 + 3/6 + 17/18 + 17/17, no item shared; `results/dev_gap.json`). On real roles the vote gained no item on any set and lost none on the unseen sets (dev lost 1). Removing all pooling and voter counts changes no solve on any unseen set, and precision does not separate.
- **Agreement between modules.** It rarely happens: 11 of 518 top answers across the unseen real roles, in 10 clusters. It is 7/11 right, and 9/9 on dev. The "separates" entries in `results/*_tables.md` for this row rest on a handful of clusters with no variance, and do not support a claim either way.

{{T11}}

Reading: @@P8READING@@

## 6. What is missing

{{T13}}

The Kaggle first-place program and GPT-4 (temperature 0) are from the ConceptARC authors' `data.xlsx`, and human accuracy is from the same file (3 attempts). Attempt rules differ from our pass@2, so compare them loosely. Monty-ARC solves 58 test pairs, the first-place program 249, and 45 are shared.

**Judged, not measured.** Count and Order get no candidate at all: no module has numbers or orderings among its hypotheses, so this is a gap in relations and counting, and no reference frame would fill it. AboveBelow, HorizontalVertical, InsideOutside and SameDifferent do get candidates (27 items) with 1 solve: behaviour's object keys (colour, size, holes, symmetry, shape) cannot say "which object relative to which", so rules fit the demos without the concept. Center and Order look like goal inference: the output is defined by a target state, not by a local change around an object. Every task learns alone from 1-5 demos, so ten tasks of a concept share nothing, which is the learned-behaviour ingredient TBT would need. The first-place program solves 8-21 of 30 in those same groups with a hand-written DSL, so the shortfall is at least partly primitives, not only theory.

## 7. Caveats

- **n.** ConceptARC's real role rests on 18 answered tasks (FA-LOO + (c)), Mini-ARC's on 9. Bootstraps over so few clusters are anti-conservative: a CI like self-model's [66.7, 66.7] means zero between-task variance in 3 tasks, not certainty. Task-level recounts are in `results/*_extras.md` (ConceptARC FA-LOO + (c): 11 of 18 tasks all right, Clopper-Pearson [36, 83]%).
- **1D-ARC is near-copies.** Three generated types supply 142 of its 172 FA-LOO answers; clustering by type is why its CIs are wide despite 901 tasks.
- **Sets differ from the hidden set.** All three are easier in kind than ARC-AGI-2 (humans 91% on ConceptARC). No claim about the hidden set beyond what is known: Monty v5 scores 0.00 there.
- **Units.** Unseen sets count per test pair (ConceptARC 3 per task, each run with its own query); development counts per task, mostly one test.
- **Multiplicity.** Seven primary comparisons, no correction, many secondary ones. A CI just excluding 0 is weak evidence.
- **Post hoc, labelled as such above:** Table 12, the reasons for FA-LOO's drops, evidence of the arms' solves, the effect of removing behaviour. The `global` arm and T3b were planned before results; both were my additions to the brief.
- **These sets are no longer unseen for anyone who reads this file.** Any change to Monty-ARC motivated by these results voids them as held-out data. Two observations are worth testing on fresh data only, and I did not apply them: FA-LOO per module rather than per system would avoid the fold competition in section 4; and adding v5's 2:1 condition to FA-LOO would have declined all 4 wrong FA-LOO-only answers on ConceptARC and Mini-ARC, along with 6 right ones (3 on ConceptARC, 3 on 1D-ARC).
- **No bug found** in `arcmonty/`. **Disclosure:** short single-process analysis scripts ran beside the 8-worker pool, so a ninth low-priority process existed briefly. The Mini-ARC clone contains a Flask venv; nothing in it was run.

## 8. Files

- `research/monty_heldout.json`: all numbers.
- `research/monty_heldout/`: scripts; `results/*_tables.md`, `*_extras.md`, `summary_tables.md`, `verify.json`, `wrong_concept/`; caches in `cache/` (about 380 MB in all; safe to delete once checked, and about 1.5 h on 8 workers to rebuild).
- Figures: `research/paper/figures/heldout_precision_by_rule.png` (caption: *Precision of confident answers by acceptance rule, development vs unseen sets. Lines are 95% cluster-bootstrap intervals over tasks, or over 18 generated types for 1D-ARC. Held-out rules lift precision over fit-to-demos everywhere; all rules lose precision on ConceptARC.*) and `heldout_modules.png` (caption: *Modules on ConceptARC. Left: test pairs solved when run alone, and lost when removed. Right: precision of the module's top answer at evidence >= 0.99, development vs ConceptARC. Few answered tasks make these intervals too narrow.*).
- Reproduce: `run_cache.py`, then `revote.py`, `dev_global.py`, `dev_compare.py`, `analyse.py TAG`, `extras.py TAG`, `disagree.py`, `summary.py`, `make_figures.py`.
