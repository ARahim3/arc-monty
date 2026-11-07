# Testing the Thousand Brains claims on unseen tasks (frozen Monty-ARC v5)

Agent: monty-heldout. Status: **final, 2026-10-31.** Section 0 was written before any new run or analysis and is unchanged, apart from one addendum marked as such. Sets: ConceptARC, plus Mini-ARC, 1D-ARC and MinimalTasks. `ns` in a table = the 95% CI includes 0, i.e. the comparison does not separate.

## 0. Planned comparisons (written before looking at any new result)

**Already known when this plan was written** (from the brief, `judge_review.md` and `concept_summary.txt`): pass@2 58/480; FA-LOO + (c) 35/44, (a) only 35/44, v5 42/49, fit-only 43/74; demo roles 100/111; the 9 wrong FA-LOO + (c) pair ids. Nothing else about ConceptARC has been looked at: no per-module, per-frame, per-group, per-bucket or 8-view numbers.

**Frozen.** `arcmonty/` is imported unchanged. Only wrappers and monkeypatches in `research/monty_heldout/`. No threshold, bucket, rule or module list is chosen from ConceptARC: every rule, bucket and threshold below is the one already used on development data (`monty_ablations.md`, `monty_faloo.md`), or is stated here in advance.

**Units.** One item = one test pair with its task's demos (480 in ConceptARC, as in the earlier runs). Cluster = task (160). All CIs: percentile cluster bootstrap by task, 10,000 resamples, fixed seed, recomputing the statistic on each resample; paired differences are computed on the same resample. "Separates" means the 95% CI of the difference excludes 0. Where a percentile CI degenerates (0 wrong answers) I also give a Clopper-Pearson interval over answered tasks. Real role = the true test pair is the query. Demo roles = each demo in turn plays test and the true test pair joins the demos (as `rotate.py`).

**Rules, as on development data.**
- `v5`: `vote.confident` on the pooled candidates; scored on `attempts_from(.., 0.99)`, which can hold **two** attempts. FA-LOO gives one answer, so I also report `v5 top-1` (same answer set, scored on the top answer only). This is a check of a known asymmetry; it does not replace the v5 number.
- `FA-LOO`: (a) every fold predicts its held-out demo; (b) folds agree on the test. `FA-LOO + (c)`: full-data top answer equals the fold answer. `(a) only`: (a) plus the full-data answer.
- `fit-only`: every candidate's evidence set to 1.0, then the v5 rule (`concept_full.py`).
- `P4`: one voter per module, evidence accumulates only across distinct modules (`faloo.pool_p4`).
- Evidence buckets: `>= 0.99`, `[0.5, 0.99)`, `(0, 0.5)`, `0` (Table 6 of `monty_ablations.md`), on the top pooled answer; the "raw" variant has no within-module accumulation.

### Test 1. Frames (claim: models live in object-centred reference frames)
Arms for `behavior.FRAMES`:
- `canon`: the object's D8-canonical frame.
- `abs`: object-anchored but grid-aligned (`ys - o.y0, xs - o.x0`). **Note:** this keeps the object anchor, so canon vs abs tests only pose normalisation, not the object-centred idea as a whole.
- `both`: the shipped setting.
- `global` (added arm, needs a monkeypatch of `behavior._frame_coords`): table indexed by absolute grid coordinates, no object anchor. It is the only arm that removes the object frame. Measured on development data too, as a comparator.
- `none`: behaviour module removed (system level only), as a floor.

Levels: behaviour alone, and system (8 modules with behaviour restricted to the arm; no other module has a FRAMES setting). Metrics: pass@2 solves (pairs and tasks), confident answers and precision (module alone: top answer at evidence >= 0.99, as `frame_ablation.py`; system: v5, FA-LOO + (c)), real and demo roles. Development comparators from the same code path (`frame_ablation.json`: behaviour alone 29 canon, 24 abs, both 31; LOO = 1.0: 13/14, 11/12, 13/16; system level recomputed from existing caches).
- **Primary T1a:** behaviour alone, canon minus abs, pass@2 solves (paired CI, plus exact sign test on discordant tasks).
- **Primary T1b:** both minus canon at system level: extra solves and extra wrong confident answers (dev: +2, +2).
- **Secondary:** canon minus global; abs minus global; precision differences.
- **Verdict rule:** "survives" if canon > abs in solves and the CI excludes 0; "same direction, does not separate" if canon >= abs and the CI includes 0; "not supported" if canon <= abs on both solves and precision.

### Test 2. Prediction (claim: test models by predicting what you haven't seen)
- **Primary T2a:** full-system top answer, precision at evidence >= 0.99 minus precision below 0.99 (paired CI). Precision by all four buckets, overall and per module, real role and demo roles. Ordered if precision falls from bucket to bucket (where n > 0); pairwise CIs given.
- **Primary T2b:** paired precision differences: v5 minus fit-only; FA-LOO + (c) minus fit-only; FA-LOO + (c) minus v5; FA-LOO + (c) minus (a) only.
- **Primary T2c:** FA-LOO + (c) demo roles minus real role; the same with each concept group left out in turn (is the gap concentrated?), plus per-group counts. With 16 groups this is descriptive: no per-group significance claim.
- **Secondary:** AUROC of top evidence vs correctness (dev comparator from caches). Venn of answer sets (v5, FA-LOO, (a) only, fit-only) in pairs and tasks; overlap of wrong answers; one short note per wrong answer (hand-read, labelled judged). Task-level recount (one vote per answered task), because dev's 101/102 counts tasks and most dev tasks have one test.
- **Verdict rule:** "survives" if the bucket order holds at system level, T2a's CI excludes 0, and at least one LOO rule beats fit-only with a CI excluding 0.

### Test 3. Voting (claim: many columns vote)
- **Primary T3a:** complementarity: per module alone, leave-one-module-out and unique solves (same definitions as Tables 2-4); share of solved items solved by exactly one module (dev: 115/123 on AGI-2 train, all on AGI-2 eval and new233; complementary = at least 80%).
- **Primary T3b (is it a vote at all?):** how many answered items have the top answer backed by two or more distinct modules, and precision of multi-module vs single-module top answers (paired CI where n allows). Baseline with no vote: take the highest single-hypothesis evidence, ties by module order, no pooling; compare pass@2 and precision at evidence >= 0.99 with the v5 pool. Same on development caches. Module complementarity alone describes a portfolio, not a vote, so a null here is a finding about the voting claim.
- **Primary T3c:** 8 D8 views vs 1 view: wrong confident answers and precision for v5, P4, FA-LOO (v5 vote) + (c), FA-LOO (P4 vote) + (c), real and demo roles. Dev comparator: AGI-1 train v5 1 -> 4 wrong; P4 8 views 60/61; FA-LOO + (c) 58/58. Paired CI for (8-view v5 wrong count minus 1-view v5 wrong count) and for precision differences.
- **Verdict rule:** complementarity is one line, voting another: "inflation replicates" if 8-view v5 adds wrong answers and P4 or FA-LOO removes at least most of them; say plainly if n is too small.

### Test 4. What is missing
pass@2 by the 16 concept groups, and which modules solve what, with CIs by task. 3-5 sentences linking the worst groups to TBT ingredients: **judged, not measured.**

### Test 5 (optional). One more unseen dataset
Candidates, only if public and quick: ConceptARC `MinimalTasks` (already on disk, 16 tasks), Mini-ARC, 1D-ARC. Overlap checked by hashing pairs against the 1,147 development tasks and ConceptARC. Same acceptance-rule table, no tuning. Downloads under `external/heldout/`, treated as untrusted data (parsed as JSON only, read with `python -I`-safe scripts kept outside that directory).

**Plan addendum (written after the overlap check, before any solver run on these sets).** Overlap by whole-pair hash: Mini-ARC (Apache-2.0, 149 tasks, 5x5 grids, 1 test each) 0 of 671 pairs shared with the 1,147 development tasks; 1D-ARC (MIT, 901 tasks in 18 generated types, 1 test each) 0 of 3,545; ConceptARC MinimalTasks (16 tasks) 0 of 93. All three run through the same scripts, with the same rules and the T1-T3 tables, not only the acceptance table. Clusters: Mini-ARC by task; 1D-ARC **by generated type (18 clusters)**, since tasks of one type are near-copies; MinimalTasks by task. Pooled estimates across datasets are not primary, because the datasets differ in kind; if shown, they are labelled descriptive, and each dataset stays separately visible. No Python inside `external/heldout/` is run (Mini-ARC ships a Flask venv): JSON only, scripts here, `python -I -B`.

### Multiplicity
Primary comparisons are the seven listed (T1a, T1b, T2a, T2b, T2c, T3a-c group). Everything else is descriptive. No correction is applied; with this many comparisons and this n, a single CI just excluding 0 is weak evidence and will be described as such.

### Verification planned before trusting the numbers
1. Re-vote from my per-module cache reproduces `rotate_concept.jsonl` (all fold and full answers, all 480 items) and `concept_full.jsonl` (v5, fit, p2).
2. Frame filtering of cached hypotheses equals a real run with `behavior.FRAMES` monkeypatched (ConceptARC, real role), and reproduces `frame_ablation.json` on development caches.
3. 8-view re-vote equals a real `monty_arc.candidates(task, perspectives=range(8))` on a random sample.
4. Dev numbers reproduced from dev caches: 101/102, 96/98, Table 2-4 rows.

## 1. Verdicts

Each verdict applies the rule fixed in section 0. All results are for Monty-ARC v5 as implemented; a null here is a result about these modules, not about the neocortex.

- **Claim 1, object-centred frames: survives for solves, not for trust.** Canonical frames beat grid-aligned frames on the two unseen sets where pose can matter: ConceptARC +6 test pairs [+1, +12] (5:0 discordant tasks, sign p = 0.06), Mini-ARC +4 [+1, +8] (4:0, p = 0.13); on 1D-ARC the two arms are identical. Confident answers get no more precise (behaviour alone: ConceptARC 3/6 vs 0/0, Mini-ARC 5/6 vs 5/5; system FA-LOO + (c) on ConceptARC: -4.5 [-12.5, 0.0], does not separate), and `both` adds nothing over `canon` on unseen sets (0 solves, 0 wrong; dev +2, +2). Removing the object anchor altogether costs more on 1D-ARC (+168 [+48, +313]) and Mini-ARC (+10 [+3, +18]), but does not separate on ConceptARC (+6 [-1, +14]).
- **Claim 2, test by predicting the unseen: survives, and it is the strongest result.** Held-out evidence lifts precision over fit-to-demos by about the same margin on unseen sets as on development: v5 minus fit-only is +27.3 [+20.2, +34.8] on dev, +27.6 [+11.3, +45.4] on ConceptARC, +48.3 [+30.0, +66.7] on Mini-ARC, +28.2 [+13.4, +47.0] on 1D-ARC. Absolute precision falls: FA-LOO + (c) is 99.0% on dev and 79.5%, 88.9%, 93.6% on the unseen sets (dev minus set: +19.5 [+6.9, +34.7], +10.1 [-2.7, +36.4], +5.4 [+0.3, +20.7]); v5 is 98.0% and 85.7%, 100%, 93.8%. **Fold agreement adds no measured precision anywhere** (FA-LOO + (c) minus v5: -6.2 [-15.1, +1.8], -11.1 [-36.4, 0.0], -0.2 [-4.2, +0.1]; the rule's value here is its proof, not its accuracy).
- **Claim 3, many columns vote: complementarity survives, the vote itself shows no measured effect.** Almost every solve comes from one module (98.3%, 75.0%, 99.5%; Mini-ARC is below the planned 80% line). On all three unseen sets the items answered at evidence >= 0.99 are exactly the union of what the modules answer alone, and a baseline with no pooling and no voter counts solves the same items, with precision that does not separate from the pool's. Top answers backed by two or more modules are too rare to judge: 1/4, 5/5, 1/2 (dev 9/9). **Voting over view copies inflates false confidence, as on development, in four of the six unseen populations, and gains nothing:** 8-view v5 adds wrong confident answers on all three sets' demo roles (ConceptARC +7 [+2, +13], Mini-ARC +6 [+2, +11], 1D-ARC +14 [+5, +24]) and on 1D-ARC's real role (+5 [+2, +9]), but not on ConceptARC's real role (7 to 6, -1 [-4, +2]) or Mini-ARC's (0 to 1, +1 [0, +3]); one voter per module or FA-LOO + (c) removes nearly all of it, and no gain in solves separates.
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

### Table 5. Frames, behaviour module alone (pass@2 items; top answer at evidence >= 0.99)

| Arm | Development | ConceptARC | Mini-ARC | 1D-ARC |
|---|---|---|---|---|
| canon (D8 object frame) | 29; 13/14 | 11; 3/6 | 14; 5/6 | 179; 148/154 |
| abs (object-anchored, grid-aligned) | 24; 11/12 | 5; 0/0 | 10; 5/5 | 179; 148/154 |
| both (shipped) | 31; 13/16 | 11; 3/6 | 14; 5/6 | 179; 154/160 |
| global (grid coordinates, no object anchor) | 2; 1/2 | 5; 0/0 | 4; 2/2 | 11; 4/4 |

### Table 6. Frames, full system (pass@2 items; v5; FA-LOO + (c), real role)

| Arm | Development | ConceptARC | Mini-ARC | 1D-ARC |
|---|---|---|---|---|
| canon | 136; 97/98; 103/104 | 58; 42/49; 38/47 | 20; 11/11; 8/9 | 198; 161/172; 161/172 |
| abs | 133; 96/98; 100/101 | 52; 39/45; 35/41 | 16; 11/11; 9/9 | 198; 161/172; 161/172 |
| both (shipped) | 138; 96/98; 101/102 | 58; 42/49; 35/44 | 20; 11/11; 8/9 | 198; 167/178; 161/172 |
| global | 118; 90/93; 93/94 | 53; 39/45; 33/39 | 15; 9/9; 7/7 | 31; 20/25; 17/22 |
| behaviour removed | 116; 89/91; 94/96 | 48; 39/45; 41/47 | 11; 7/7; 6/6 | 20; 16/21; 14/19 |

### Table 7. Frames, paired differences in pass@2 items (difference [95% CI]; discordant clusters first:second; `ns` = the CI includes 0)

| Comparison | Development | ConceptARC real | ConceptARC demo | Mini-ARC real | Mini-ARC demo | 1D-ARC real |
|---|---|---|---|---|---|---|
| behaviour alone: canon minus abs | +5 [-1, +11]; 7:2 ns | +6 [+1, +12]; 5:0 | +18 [+4, +37]; 5:0 | +4 [+1, +8]; 4:0 | +12 [+4, +22]; 8:0 | +0 [+0, +0]; 0:0 ns |
| behaviour alone: both minus canon | +2 [+0, +5]; 2:0 ns | +0 [+0, +0]; 0:0 ns | -1 [-3, +0]; 0:1 ns | +0 [+0, +0]; 0:0 ns | -2 [-5, +0]; 0:2 ns | +0 [+0, +0]; 0:0 ns |
| behaviour alone: canon minus global | +27 [+17, +38]; 28:1 | +6 [-1, +14]; 7:3 ns | +31 [+4, +66]; 7:3 | +10 [+3, +18]; 12:2 | +27 [+4, +53]; 16:4 | +168 [+48, +313]; 10:0 |
| behaviour alone: abs minus global | +22 [+13, +32]; 23:1 | +0 [-6, +6]; 4:4 ns | +13 [-6, +38]; 3:3 ns | +6 [+0, +13]; 8:2 ns | +15 [-6, +39]; 10:4 ns | +168 [+48, +313]; 10:0 |
| system: canon minus abs | +3 [-2, +8]; 5:2 ns | +6 [+1, +12]; 5:0 | +18 [+4, +37]; 5:0 | +4 [+1, +8]; 4:0 | +9 [+2, +19]; 7:1 | +0 [+0, +0]; 0:0 ns |
| system: both minus canon | +2 [+0, +5]; 2:0 ns | +0 [+0, +0]; 0:0 ns | -1 [-3, +0]; 0:1 ns | +0 [+0, +0]; 0:0 ns | -3 [-7, +0]; 0:3 ns | +0 [+0, +0]; 0:0 ns |
| system: canon minus global | +18 [+9, +28]; 20:2 | +5 [-2, +13]; 6:3 ns | +23 [+0, +55]; 6:3 ns | +5 [-1, +11]; 7:2 ns | +14 [-6, +36]; 11:5 ns | +167 [+47, +312]; 10:0 |
| system: abs minus global | +15 [+7, +24]; 17:2 | -1 [-6, +4]; 3:4 ns | +5 [-8, +23]; 2:3 ns | +1 [-3, +6]; 3:2 ns | +5 [-12, +24]; 6:4 ns | +167 [+47, +312]; 10:0 |

Descriptive only, discordant clusters summed over the three unseen sets, real role, behaviour alone: canon vs abs 9:0 (sign p = 0.0039); canon vs global 29:5 (sign p = 3.9e-05).

Reading:
- **Solves.** The canon-minus-abs gap is the same size on ConceptARC as on development, and only development fails to separate. On 1D-ARC the two arms have identical solves and confident counts (judged cause: one-row objects have almost no pose to normalise). All discordant tasks go to `canon`: 9:0 summed over the unseen sets (descriptive; sign p = 0.004).
- **These solves are mostly not confident.** Of the 6 ConceptARC items only `canon` solves, 2 have evidence >= 0.99 and a right top answer (CompleteShape5 #0, #1), 1 has a wrong top answer at evidence >= 0.99 and only attempt 2 right (TopBottom3D8 #2), 1 has evidence 0 and a wrong top answer (CompleteShape6 #0), and 2 have evidence 0 and a right top answer. Of Mini-ARC's 4, 3 have evidence 0 and 1 has 0.94. At system level, canon minus abs in FA-LOO + (c) precision is -4.5 [-12.5, 0.0] on ConceptARC (+3 right, +3 wrong answers), and does not separate.
- **The dev result for `both` does not replicate.** On unseen sets `both` adds no solve and no wrong answer over `canon`. On ConceptARC it costs FA-LOO + (c) 3 right answers (35/44 vs 38/47, -1.3 [-5.0, 0.0], does not separate): the three ExtendToBoundary5 pairs, which come back when the `abs` hypotheses are removed.
- **`abs` is not the null for "object-centred".** It keeps the object anchor, so canon vs abs tests pose normalisation only. `global` removes the anchor (the table is indexed by grid coordinates; objects still choose the key and the cells). `canon` minus `global` is large on dev and 1D-ARC, +10 on Mini-ARC, and does not separate on ConceptARC's real role (+6 [-1, +14]; it does on demo roles, +31 [+4, +66]). At system level other modules fill part of the gap: it separates on dev and 1D-ARC only. Of `global`'s 5 ConceptARC solves, none has evidence >= 0.99.
- **Removing behaviour (post hoc observation).** It costs solves on every set: 58 to 48, 20 to 11, 198 to 20. On ConceptARC FA-LOO + (c) then improves (41/47 vs 35/44, +7.7 [+1.2, +17.3]), because behaviour hypotheses win folds (section 4). On Mini-ARC it loses answers (6/6 vs 8/9) and on 1D-ARC it collapses (14/19 vs 161/172), so this is not a general effect.

## 4. Claim 2: prediction

### Table 1. Acceptance rules, real test role (correct/answered = precision [95% CI]; coverage in the last rows)

| Rule | Development (1,147) | ConceptARC | Mini-ARC | 1D-ARC | MinimalTasks |
|---|---|---|---|---|---|
| FA-LOO + (c) | 101/102 = 99.0% [96.7, 100.0] | 35/44 = 79.5% [64.4, 92.3] | 8/9 = 88.9% [63.6, 100.0] | 161/172 = 93.6% [79.1, 98.3] | 5/5 = 100.0% [100.0, 100.0] |
| (a) only | 102/104 = 98.1% [94.9, 100.0] | 35/44 = 79.5% [64.4, 92.3] | 8/9 = 88.9% [63.6, 100.0] | 161/172 = 93.6% [79.1, 98.3] | 5/5 = 100.0% [100.0, 100.0] |
| v5 heuristic | 96/98 = 98.0% [94.7, 100.0] | 42/49 = 85.7% [74.2, 95.2] | 11/11 = 100.0% [100.0, 100.0] | 167/178 = 93.8% [82.9, 98.3] | 5/5 = 100.0% [100.0, 100.0] |
| Fit to demos only | 111/157 = 70.7% [63.4, 77.6] | 43/74 = 58.1% [41.4, 73.4] | 15/29 = 51.7% [33.3, 70.0] | 187/285 = 65.6% [39.5, 82.1] | 6/17 = 35.3% [0.0, 65.4] |
| Coverage, FA-LOO + (c) | 8.9% | 9.2% | 6.0% | 19.1% | 10.4% |
| Coverage, v5 | 8.5% | 10.2% | 7.4% | 19.8% | 10.4% |
| pass@2 | 138/1,147 = 12.0% | 58/480 = 12.1% | 20/149 = 13.4% | 198/901 = 22.0% | 7/48 = 14.6% |
| Items; clusters | 1,147; 1,147 tasks | 480; 160 tasks | 149; 149 tasks | 901; 18 types | 48; 16 tasks |
| Dev minus this set, FA-LOO + (c), pts | | +19.5 [+6.9, +34.7] | +10.1 [-2.7, +36.4] ns | +5.4 [+0.3, +20.7] | n/a |
| Dev minus this set, v5, pts | | +12.2 [+2.0, +24.3] | -2.0 [-5.3, +0.0] ns | +4.1 [-1.4, +15.8] ns | n/a |
| Dev minus this set, fit-only, pts | | +12.6 [-4.2, +31.5] ns | +19.0 [-0.9, +39.3] ns | +5.1 [-13.2, +32.1] ns | n/a |
| Joint P(answer and wrong), FA-LOO + (c) | 0.09% | 1.88% (9/480) | 0.67% (1/149) | 1.22% (11/901) | 0.00% (0/48) |
| Worst case, mean 1/(n+1) | 24.7% | 28.3% | 22.7% | 25.0% | 26.5% |
| Tasks answered / with a wrong answer, FA-LOO + (c) | 102 / 1 | 18 / 7 | 9 / 1 | 12 / 6 | 2 / 0 |
| Tasks answered / with a wrong answer, v5 | 98 / 2 | 19 / 6 | 11 / 0 | 13 / 6 | 2 / 0 |

### Table 2. The same rules, demo-as-test roles

| Rule | Development | ConceptARC | Mini-ARC | 1D-ARC | MinimalTasks |
|---|---|---|---|---|---|
| FA-LOO + (c) | 350/365 = 95.9% [93.5, 97.8] | 100/111 = 90.1% [79.1, 96.2] | 30/33 = 90.9% [76.0, 100.0] | 479/515 = 93.0% [70.5, 97.5] | 15/15 = 100.0% [100.0, 100.0] |
| (a) only | not run | 100/112 = 89.3% [77.9, 95.6] | 30/33 = 90.9% [76.0, 100.0] | 479/516 = 92.8% [69.6, 97.4] | 15/15 = 100.0% [100.0, 100.0] |
| v5 heuristic | not run | 112/123 = 91.1% [81.1, 96.7] | 44/45 = 97.8% [91.7, 100.0] | 493/531 = 92.8% [75.2, 97.2] | 15/16 = 93.8% [0.0, 100.0] |
| Fit to demos only | not run | 119/186 = 64.0% [48.0, 76.2] | 50/90 = 55.6% [38.8, 70.1] | 543/801 = 67.8% [40.6, 83.2] | 17/28 = 60.7% [13.6, 85.7] |
| FA-LOO + (c), demo roles minus real role | -3.1 (from the two rows; judge's rotation) | +10.5 [-4.2, +24.5] ns | +2.0 [-19.0, +26.4] ns | -0.6 [-8.5, +2.7] ns | +0.0 [+0.0, +0.0] ns |

### Table 3. What held-out prediction adds (percentage points [95% CI]; `ns` = the CI includes 0)

| Comparison | Development | ConceptARC | Mini-ARC | 1D-ARC | MinimalTasks |
|---|---|---|---|---|---|
| v5 minus fit-only | +27.3 [+20.2, +34.8] | +27.6 [+11.3, +45.4] | +48.3 [+30.0, +66.7] | +28.2 [+13.4, +47.0] | +64.7 [+33.3, +86.4] |
| FA-LOO + (c) minus fit-only | +28.3 [+21.5, +35.5] | +21.4 [+3.3, +40.3] | +37.2 [+8.7, +62.5] | +28.0 [+13.4, +45.7] | +64.7 [+33.3, +86.4] |
| (a) only minus fit-only | +27.4 [+20.2, +34.9] | +21.4 [+3.3, +40.3] | +37.2 [+8.7, +62.5] | +28.0 [+13.4, +45.7] | +64.7 [+33.3, +86.4] |
| FA-LOO + (c) minus v5 | +1.1 [+0.0, +3.3] ns | -6.2 [-15.1, +1.8] ns | -11.1 [-36.4, +0.0] ns | -0.2 [-4.2, +0.1] ns | +0.0 [+0.0, +0.0] ns |
| FA-LOO + (c) minus (a) only | +0.9 [-0.0, +3.1] ns | +0.0 [+0.0, +0.0] ns | +0.0 [+0.0, +0.0] ns | +0.0 [+0.0, +0.0] ns | +0.0 [+0.0, +0.0] ns |
| Top answer: evidence >= 0.99 minus below | +71.0 [+62.7, +79.2] | +68.1 [+51.5, +82.6] | +70.7 [+48.0, +87.9] | +74.7 [+61.2, +82.9] | +90.0 [+69.2, +100.0] |
| AUROC of evidence vs correct | 0.922 [0.881, 0.957] | 0.873 [0.785, 0.945] | 0.894 [0.794, 0.977] | 0.913 [0.807, 0.954] | 0.992 [0.925, 1.000] |

### Table 4. Evidence buckets, top answer (correct/top answers)

| Column, role | >= 0.99 | [0.5, 0.99) | (0, 0.5) | 0 |
|---|---|---|---|---|
| Development, full system | 100/104 = 96.2% | 25/34 = 73.5% | 0/4 = 0.0% | 9/97 = 9.3% |
| ConceptARC, full system, real | 44/54 = 81.5% | 4/10 = 40.0% | 0/1 = 0.0% | 7/71 = 9.9% |
| ConceptARC, full system, demo | 121/139 = 87.1% | 26/46 = 56.5% | 9/12 = 75.0% | 16/153 = 10.5% |
| Mini-ARC, full system, real | 11/12 = 91.7% | 5/7 = 71.4% | 1/1 = 100.0% | 3/35 = 8.6% |
| Mini-ARC, full system, demo | 44/47 = 93.6% | 9/18 = 50.0% | 4/14 = 28.6% | 8/120 = 6.7% |
| 1D-ARC, full system, real | 170/181 = 93.9% | 9/17 = 52.9% | 0/1 = 0.0% | 19/128 = 14.8% |
| 1D-ARC, full system, demo | 504/549 = 91.8% | 30/57 = 52.6% | 0/5 = 0.0% | 58/309 = 18.8% |
| ConceptARC, self-model, real | 6/9 | 0/0 | 0/0 | 0/0 |
| ConceptARC, periodic, real | 1/4 | 0/0 | 0/0 | 0/0 |
| ConceptARC, behavior, real | 3/6 | 2/7 | 0/0 | 4/72 |
| ConceptARC, dynamics, real | 17/18 | 0/3 | 0/0 | 3/3 |
| ConceptARC, composition, real | 17/17 | 3/3 | 0/0 | 0/0 |
| ConceptARC, pattern, real | 0/0 | 0/0 | 0/1 | 0/10 |
| Mini-ARC, behavior, real | 5/6 | 4/6 | 2/2 | 3/32 |
| Mini-ARC, pattern, real | 3/3 | 4/4 | 0/0 | 0/4 |
| Mini-ARC, dynamics, real | 2/2 | 0/0 | 0/0 | 0/0 |
| Mini-ARC, periodic, real | 1/1 | 0/0 | 0/0 | 0/0 |
| Mini-ARC, field, real | 1/1 | 0/0 | 0/0 | 0/0 |
| 1D-ARC, behavior, real | 154/160 | 5/11 | 0/0 | 20/130 |
| 1D-ARC, dynamics, real | 16/21 | 1/2 | 0/0 | 0/0 |
| 1D-ARC, pattern, real | 0/0 | 3/4 | 0/1 | 0/4 |

Reading:
- **Calibration order.** On every unseen set, real and demo roles, precision at evidence >= 0.99 is above [0.5, 0.99), which is above evidence 0. The (0, 0.5) bucket is too small to order (at most 1 real-role item per set; demo roles 9/12, 4/14, 0/5; dev 0/4). Evidence >= 0.99 minus below separates everywhere, at about the dev size: +68.1, +70.7, +74.7 against +71.0. The step from >= 0.99 to [0.5, 0.99) separates on 1D-ARC and ConceptARC's demo roles, but not on the real roles of ConceptARC (+41.5 [-23.5, +86.4], 4/10 in the middle bucket) or Mini-ARC (+20.2 [-16.7, +62.0]).
- **Per module on ConceptARC, calibration holds where solves are.** Composition 17/17 and dynamics 17/18 at evidence >= 0.99. Self-model falls from 9/9 on dev to 6/9, periodic from 4/4 to 1/4, behaviour from 13/16 to 3/6. All 10 wrong top answers at evidence >= 0.99 come from these: self-model 3, periodic 3, behaviour 3, dynamics 1. Self-model's evidence is fit-only by construction (`monty_faloo.md`), so its 1.0 never contained a held-out test. Dynamics is the module that falls on 1D-ARC (16/21).
- **Real test vs demo roles.** The ConceptARC gap (+10.5 [-4.2, +24.5]) **does not separate**, and neither do Mini-ARC (+2.0) or 1D-ARC (-0.6). The judge's reading that the gap "points at exchangeability failing" is not established by these numbers. CompleteShape is the largest single contributor: 6/10 real vs 8/8 demo, and leaving it out shrinks the gap to +4.0 [-11.7, +18.6] (Table 13). That is descriptive, with no per-group test.
- **Dev flattered the certificate.** Development's real role was above its demo roles (99.0% vs 95.9%), the opposite sign to ConceptARC's, which is consistent with the judge's view that development raised real-role precision but does not test it. Joint P(answer and wrong) is still far under the worst case on unseen sets (Table 1). The theorem is not contradicted; its bound stays loose.

### Table 12. Where v5 and FA-LOO + (c) disagree about answering (real role; post hoc, descriptive)

| Dataset | Both answer: right/n | v5 only: right/n | FA-LOO + (c) only: right/n |
|---|---|---|---|
| Development (1,147) | 91/92 | 5/6 | 10/10 |
| ConceptARC | 32/38 | 10/11 | 3/6 |
| Mini-ARC | 8/8 | 3/3 | 0/1 |
| 1D-ARC | 158/169 | 9/9 | 3/3 |
| Three unseen sets pooled (stratified cluster bootstrap) | 198/215 | 22/23 [83, 100] | 6/10 [22, 90]; v5 only minus FA-LOO only +35.7 [+2.1, +75.0] |

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

### Table 8. Modules (alone / lost when removed / unique, pass@2 items, real role)

| Module | Development | ConceptARC | Mini-ARC | 1D-ARC |
|---|---|---|---|---|
| self-model | 9 / 9 / 9 | 6 / 6 / 6 | 0 / 0 / 0 | 0 / 0 / 0 |
| periodic | 10 / 10 / 10 | 2 / 2 / 2 | 1 / 1 / 1 | 0 / 0 / 0 |
| behavior | 31 / 23 / 23 | 11 / 10 / 10 | 14 / 9 / 9 | 179 / 178 / 178 |
| dynamics | 10 / 8 / 8 | 20 / 19 / 19 | 2 / 2 / 2 | 17 / 16 / 16 |
| composition | 59 / 59 / 59 | 20 / 20 / 20 | 0 / 0 / 0 | 0 / 0 / 0 |
| association | 3 / 3 / 3 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| pattern | 25 / 16 / 17 | 0 / 0 / 0 | 7 / 2 / 2 | 3 / 3 / 3 |
| field | 1 / 1 / 1 | 0 / 0 / 0 | 1 / 1 / 1 | 0 / 0 / 0 |
| Solved by exactly one module | 130/139 = 93.5% | 57/58 = 98.3% | 15/20 = 75.0% | 197/198 = 99.5% |
| Same, demo roles | not run | 171/179 = 95.5% | 54/68 = 79.4% | 596/598 = 99.7% |
| Lost by the vote / gained by the vote | 1 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |

### Table 9. Module alone: top answer at evidence >= 0.99, real role (development: distinct tasks)

| Module | Development | ConceptARC | Mini-ARC | 1D-ARC |
|---|---|---|---|---|
| self-model | 9/9 | 6/9 | 0/0 | 0/0 |
| periodic | 4/4 | 1/4 | 1/1 | 0/0 |
| behavior | 13/16 | 3/6 | 5/6 | 154/160 |
| dynamics | 10/10 | 17/18 | 2/2 | 16/21 |
| composition | 55/56 | 17/17 | 0/0 | 0/0 |
| association | 3/3 | 0/0 | 0/0 | 0/0 |
| pattern | 10/11 | 0/0 | 3/3 | 0/0 |
| field | 1/1 | 0/0 | 1/1 | 0/0 |

### Table 10. Is it a vote? Top answers backed by two or more modules, and a no-vote baseline (real role)

| Quantity | Development | ConceptARC | Mini-ARC | 1D-ARC |
|---|---|---|---|---|
| Top answers from 2+ modules: correct/n (clusters) | 9/9 (9) | 1/4 (3) | 5/5 (5) | 1/2 (2) |
| Top answers from 1 module | 125/230 | 54/132 | 15/50 | 197/325 |
| Pool minus no-vote, pass@2 items | +1 [+0, +3]; 1:0 ns | +0 [+0, +0]; 0:0 ns | +0 [+0, +0]; 0:0 ns | +0 [+0, +0]; 0:0 ns |
| Top answer at evidence >= 0.99, pool | 100/104 = 96.2% | 44/54 = 81.5% | 11/12 = 91.7% | 170/181 = 93.9% |
| Top answer at evidence >= 0.99, no-vote | 100/103 = 97.1% | 45/54 = 83.3% | 11/12 = 91.7% | 164/175 = 93.7% |
| Pool minus no-vote, precision | -0.9 [-4.4, +2.1] ns | -1.9 [-6.2, +0.0] ns | +0.0 [+0.0, +0.0] ns | +0.2 [+0.0, +2.3] ns |

Reading:
- **Complementary: yes, and which module matters flips with the benchmark.** Composition makes 20 of ConceptARC's 58 solves and none on Mini-ARC or 1D-ARC; behaviour makes 179 of 198 on 1D-ARC. Association and field solve nothing on ConceptARC, and pattern solves nothing there either. Mini-ARC's 75.0% (all 5 shared items are behaviour with pattern) is below the planned 80% line.
- **It is a portfolio.** On all three unseen sets the items the system answers at evidence >= 0.99 are exactly the union of what the modules answer alone (ConceptARC: 44/54 = 6/9 + 1/4 + 3/6 + 17/18 + 17/17, no item shared; `results/dev_gap.json`). On real roles the vote gained no item on any set and lost none on the unseen sets (dev lost 1). Removing all pooling and voter counts changes no solve on any unseen set, and precision does not separate.
- **Agreement between modules.** It rarely happens: 11 of 518 top answers across the unseen real roles, in 10 clusters. It is 7/11 right, and 9/9 on dev. The "separates" entries in `results/*_tables.md` for this row rest on a handful of clusters with no variance, and do not support a claim either way.

### Table 11. Eight D8 views vs one view

| Population | Rule | 1 view | 8 views | Wrong, 8 minus 1 |
|---|---|---|---|---|
| ConceptARC, real | v5 rule | 42/49 = 85.7% [74.2, 95.2] | 44/50 = 88.0% [77.1, 97.2] | -1 [-4, +2]; 1:2 ns |
| ConceptARC, real | P4 | 42/49 = 85.7% [74.2, 95.2] | 43/49 = 87.8% [76.5, 97.1] | -1 [-4, +2]; 1:2 ns |
| ConceptARC, real | FA-LOO (v5 vote) + (c) | 35/44 = 79.5% [64.4, 92.3] | 34/43 = 79.1% [65.2, 90.7] | +0 [-5, +4]; 2:1 ns |
| ConceptARC, real | FA-LOO (P4 vote) + (c) | 39/46 = 84.8% [72.4, 95.0] | 39/48 = 81.2% [68.8, 91.7] | +2 [+0, +5]; 2:0 ns |
| ConceptARC, demo | v5 rule | 112/123 = 91.1% [81.1, 96.7] | 121/139 = 87.1% [76.1, 94.0] | +7 [+2, +13]; 6:0 |
| ConceptARC, demo | P4 | 116/126 = 92.1% [82.6, 97.3] | 118/129 = 91.5% [81.7, 97.1] | +1 [+0, +3]; 1:0 ns |
| ConceptARC, demo | FA-LOO (v5 vote) + (c) | 100/111 = 90.1% [79.1, 96.2] | 97/109 = 89.0% [77.9, 95.1] | +1 [-2, +5]; 2:1 ns |
| ConceptARC, demo | FA-LOO (P4 vote) + (c) | 118/130 = 90.8% [80.5, 96.6] | 116/128 = 90.6% [80.2, 96.6] | +0 [+0, +0]; 0:0 ns |
| Mini-ARC, real | v5 rule | 11/11 = 100.0% [100.0, 100.0] | 15/16 = 93.8% [78.9, 100.0] | +1 [+0, +3]; 1:0 ns |
| Mini-ARC, real | P4 | 11/11 = 100.0% [100.0, 100.0] | 11/12 = 91.7% [71.4, 100.0] | +1 [+0, +3]; 1:0 ns |
| Mini-ARC, real | FA-LOO (v5 vote) + (c) | 8/9 = 88.9% [63.6, 100.0] | 10/11 = 90.9% [70.0, 100.0] | +0 [+0, +0]; 0:0 ns |
| Mini-ARC, real | FA-LOO (P4 vote) + (c) | 8/9 = 88.9% [63.6, 100.0] | 9/10 = 90.0% [66.7, 100.0] | +0 [+0, +0]; 0:0 ns |
| Mini-ARC, demo | v5 rule | 44/45 = 97.8% [91.7, 100.0] | 49/56 = 87.5% [75.6, 95.6] | +6 [+2, +11]; 6:0 |
| Mini-ARC, demo | P4 | 38/39 = 97.4% [90.5, 100.0] | 45/47 = 95.7% [87.2, 100.0] | +1 [+0, +3]; 1:0 ns |
| Mini-ARC, demo | FA-LOO (v5 vote) + (c) | 30/33 = 90.9% [76.0, 100.0] | 40/43 = 93.0% [81.2, 100.0] | +0 [-3, +3]; 1:1 ns |
| Mini-ARC, demo | FA-LOO (P4 vote) + (c) | 30/33 = 90.9% [76.0, 100.0] | 38/41 = 92.7% [80.0, 100.0] | +0 [-3, +3]; 1:1 ns |
| 1D-ARC, real | v5 rule | 167/178 = 93.8% [82.9, 98.3] | 173/189 = 91.5% [77.6, 96.4] | +5 [+2, +9]; 5:0 |
| 1D-ARC, real | P4 | 161/172 = 93.6% [80.6, 98.2] | 161/172 = 93.6% [80.6, 98.2] | +0 [+0, +0]; 0:0 ns |
| 1D-ARC, real | FA-LOO (v5 vote) + (c) | 161/172 = 93.6% [79.1, 98.3] | 161/172 = 93.6% [79.1, 98.3] | +0 [+0, +0]; 0:0 ns |
| 1D-ARC, real | FA-LOO (P4 vote) + (c) | 162/173 = 93.6% [79.8, 98.3] | 162/173 = 93.6% [79.8, 98.3] | +0 [+0, +0]; 0:0 ns |
| 1D-ARC, demo | v5 rule | 493/531 = 92.8% [75.2, 97.2] | 511/563 = 90.8% [71.6, 95.8] | +14 [+5, +24]; 7:0 |
| 1D-ARC, demo | P4 | 475/509 = 93.3% [73.3, 97.6] | 477/509 = 93.7% [75.4, 97.7] | -2 [-5, +0]; 0:2 ns |
| 1D-ARC, demo | FA-LOO (v5 vote) + (c) | 479/515 = 93.0% [70.5, 97.5] | 478/517 = 92.5% [68.1, 97.2] | +3 [+0, +8]; 2:0 ns |
| 1D-ARC, demo | FA-LOO (P4 vote) + (c) | 480/517 = 92.8% [69.9, 97.4] | 479/518 = 92.5% [68.2, 97.1] | +2 [+0, +6]; 1:0 ns |
| Development, AGI-1 train only (`monty_faloo.md`) | v5 rule | 58/59 | 62/66 | 1 -> 4 |
| same | P4 | 59/59 | 60/61 | 0 -> 1 |
| same | FA-LOO (v5 vote) + (c) | 59/59 | 58/58 | 0 -> 0 |
| same | FA-LOO (P4 vote) + (c) | 60/61 | 60/61 | 1 -> 1 |

ConceptARC, pass@2 items, 8 views minus 1: +2 [+0, +5]; 2:0 ns. 8-view v5 minus 8-view P4, precision: real +0.2 [-1.2, +1.9] ns; demo -4.4 [-10.0, -0.1].

Mini-ARC, pass@2 items, 8 views minus 1: +0 [+0, +0]; 0:0 ns. 8-view v5 minus 8-view P4, precision: real +2.1 [+0.0, +8.9] ns; demo -8.2 [-17.0, -1.8].

1D-ARC, pass@2 items, 8 views minus 1: +2 [+0, +6]; 1:0 ns. 8-view v5 minus 8-view P4, precision: real -2.1 [-6.0, -0.2]; demo -2.9 [-6.8, -0.9].

Reading: - **The inflation replicates, with exceptions.** Planned rule: it replicates if 8-view v5 adds wrong answers and P4 or FA-LOO removes at least most of them. That holds on all three demo-role populations and on 1D-ARC's real role. It does not hold on ConceptARC's real role, where wrong answers go from 7 to 6 (FilledNotFilled1 #1 is new; CleanUp1 #2 and TopBottom3D8 #1 go away), and Mini-ARC's real role does not separate (one new wrong answer, `clock`).
- **The mechanism is the one seen on development, double counting.** Under P4 the wrong-answer change is +1, +1, -2 on the demo roles and 0 on 1D-ARC's real role. Under FA-LOO + (c) it is +1, 0, +3 and 0. Precision of 8-view v5 minus 8-view P4 separates on ConceptARC demo (-4.4 [-10.0, -0.1]), Mini-ARC demo (-8.2 [-17.0, -1.8]), 1D-ARC real (-2.1 [-6.0, -0.2]) and 1D-ARC demo (-2.9 [-6.8, -0.9]); it does not separate on the other two real roles.
- **No benefit to set against it.** pass@2, 8 views minus 1: +2 [0, +5], 0, +2 [0, +6]; none separates. Cost, measured: 8.2-8.5x CPU.

## 6. What is missing

### Table 13. ConceptARC by concept group (real role, 30 test pairs each)

| Group | pass@2 [CI] | Tasks /10 | Any candidate | Solving modules (alone) | v5 | FA-LOO + (c) real | FA-LOO + (c) demo | Kaggle 1st | GPT-4 T0 | Humans |
|---|---|---|---|---|---|---|---|---|---|---|
| AboveBelow | 0 [0, 0] | 0 | 8 | - | 0/0 | 0/0 | 0/0 | 21 | 7 | 90% |
| Count | 0 [0, 0] | 0 | 0 | - | 0/0 | 0/0 | 0/1 | 18 | 4 | 88% |
| HorizontalVertical | 0 [0, 0] | 0 | 10 | - | 0/0 | 0/0 | 0/0 | 13 | 8 | 91% |
| InsideOutside | 0 [0, 0] | 0 | 2 | - | 0/0 | 0/0 | 0/0 | 17 | 3 | 91% |
| Order | 0 [0, 0] | 0 | 0 | - | 0/0 | 0/0 | 0/0 | 8 | 8 | 83% |
| SameDifferent | 1 [0, 3] | 1 | 7 | behavior 1 | 0/0 | 0/0 | 0/0 | 16 | 5 | 88% |
| Center | 2 [0, 5] | 2 | 9 | behavior 2 | 0/0 | 0/0 | 0/1 | 15 | 10 | 94% |
| TopBottom3D | 2 [0, 6] | 1 | 15 | behavior 2 | 1/2 | 1/3 | 3/3 | 18 | 6 | 93% |
| Copy | 3 [0, 9] | 1 | 10 | composition 3 | 3/3 | 3/3 | 9/9 | 7 | 7 | 94% |
| CleanUp | 5 [0, 12] | 3 | 8 | self-model 2, periodic 2, behavior 1 | 3/4 | 3/5 | 4/6 | 15 | 6 | 97% |
| ExtractObjects | 6 [0, 15] | 2 | 6 | composition 6 | 4/4 | 5/5 | 12/13 | 13 | 1 | 86% |
| FilledNotFilled | 6 [0, 14] | 3 | 10 | dynamics 5, behavior 1 | 5/6 | 3/4 | 13/14 | 22 | 5 | 96% |
| MoveToBoundary | 6 [0, 15] | 2 | 6 | dynamics 6 | 6/6 | 2/2 | 5/9 | 11 | 6 | 91% |
| CompleteShape | 7 [1, 15] | 4 | 18 | self-model 4, behavior 3 | 6/10 | 6/10 | 8/8 | 14 | 7 | 85% |
| ExtendToBoundary | 9 [0, 21] | 3 | 13 | dynamics 9, behavior 1 | 6/6 | 3/3 | 10/10 | 23 | 2 | 93% |
| TopBottom2D | 11 [2, 23] | 4 | 14 | composition 11 | 8/8 | 9/9 | 36/37 | 18 | 7 | 95% |
| **All** | 58/480 | 26 | 136 | | 42/49 | 35/44 | 100/111 | 249 | 92 | 91% |

Gap (FA-LOO + (c), demo minus real) with one group left out: CompleteShape +4.0 [-11.7, +18.6] ns; TopBottom3D +6.9 [-7.4, +20.2] ns; CleanUp +9.4 [-5.9, +24.8] ns; FilledNotFilled +9.7 [-6.1, +24.0] ns; AboveBelow +10.5 [-4.2, +24.5] ns; HorizontalVertical +10.5 [-4.2, +24.5] ns; InsideOutside +10.5 [-4.2, +24.5] ns; Order +10.5 [-4.2, +24.5] ns; SameDifferent +10.5 [-4.2, +24.5] ns; ExtendToBoundary +11.1 [-4.8, +25.4] ns; Copy +11.2 [-4.7, +25.7] ns; Center +11.4 [-3.2, +25.3] ns; Count +11.4 [-3.2, +25.2] ns; TopBottom2D +12.2 [-6.6, +28.6] ns; ExtractObjects +12.9 [-3.2, +28.0] ns; MoveToBoundary +14.6 [+0.0, +29.1].

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
