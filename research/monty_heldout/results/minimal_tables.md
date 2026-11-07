Dataset `minimal`: 48 items (test pairs) in 16 tasks; 138 demo-role items. Dev comparators: 1147 tasks, unit = task.

## Acceptance rules (real and demo roles)

| Rule | Real role | Coverage | Demo roles | Dev (1,147, by task) |
|---|---|---|---|---|
| FA-LOO + (c) | 5/5 = 100.0% [100.0, 100.0] | 10.4% | 15/15 = 100.0% [100.0, 100.0] | 101/102 = 99.0% [96.7, 100.0] |
| FA-LOO (a)+(b) | 5/5 = 100.0% [100.0, 100.0] | 10.4% | 15/15 = 100.0% [100.0, 100.0] | 101/103 = 98.1% [95.0, 100.0] |
| (a) only, full-data answer | 5/5 = 100.0% [100.0, 100.0] | 10.4% | 15/15 = 100.0% [100.0, 100.0] | 102/104 = 98.1% [94.9, 100.0] |
| v5 heuristic (2 attempts) | 5/5 = 100.0% [100.0, 100.0] | 10.4% | 15/16 = 93.8% [0.0, 100.0] | 96/98 = 98.0% [94.7, 100.0] |
| v5 heuristic, top answer only | 5/5 = 100.0% [100.0, 100.0] | 10.4% | 15/16 = 93.8% [0.0, 100.0] | 96/98 = 98.0% [94.7, 100.0] |
| P4 confident (2 attempts) | 5/5 = 100.0% [100.0, 100.0] | 10.4% | 15/16 = 93.8% [0.0, 100.0] | 97/98 = 99.0% [96.6, 100.0] |
| fit to demos only (2 attempts) | 6/17 = 35.3% [0.0, 65.4] | 35.4% | 17/28 = 60.7% [13.6, 85.7] | 111/157 = 70.7% [63.4, 77.6] |
| fit to demos only, top answer only | 6/17 = 35.3% [0.0, 65.4] | 35.4% | 17/28 = 60.7% [13.6, 85.7] | 111/157 = 70.7% [63.4, 77.6] |

pass@2, real role: 7/48 = 14.6% (count CI [0, 15]); tasks with at least one solve: 3/16. Items with any candidate: 25.
Joint P(answer and wrong), FA-LOO + (c), real role: 0/48 = 0.00%. Task-level: 2 tasks answered, 0 with a wrong answer; mean per-task precision 100.0%.

## Test 1. Frames

**behaviour alone.**

| Arm | pass@2 (tasks) | top answer at evidence >= 0.99 | v5 rule | FA-LOO + (c) real | FA-LOO + (c) demo | Dev: pass@2; >=0.99; v5; FA-LOO + (c) |
|---|---|---|---|---|---|---|
| canon | 2 (1) | 0/0 | 0/0 | 0/0 | 0/0 | 29; 13/14; 13/13; 12/12 |
| abs | 2 (1) | 0/0 | 0/0 | 0/0 | 0/0 | 24; 11/12; 11/11; 9/9 |
| both | 2 (1) | 0/0 | 0/0 | 0/0 | 0/0 | 31; 13/16; 13/15; 11/11 |
| global | 5 (3) | 0/0 | 0/0 | 0/0 | 0/0 | 2; 1/2; 1/2; 1/1 |

**system.**

| Arm | pass@2 (tasks) | top answer at evidence >= 0.99 | v5 rule | FA-LOO + (c) real | FA-LOO + (c) demo | Dev: pass@2; >=0.99; v5; FA-LOO + (c) |
|---|---|---|---|---|---|---|
| canon | 7 (3) | 5/5 = 100.0% [100.0, 100.0] | 5/5 = 100.0% [100.0, 100.0] | 5/5 = 100.0% [100.0, 100.0] | 15/15 = 100.0% [100.0, 100.0] | 136; 101/103; 97/98; 103/104 |
| abs | 7 (3) | 5/5 = 100.0% [100.0, 100.0] | 5/5 = 100.0% [100.0, 100.0] | 5/5 = 100.0% [100.0, 100.0] | 15/15 = 100.0% [100.0, 100.0] | 133; 99/102; 96/98; 100/101 |
| both | 7 (3) | 5/5 = 100.0% [100.0, 100.0] | 5/5 = 100.0% [100.0, 100.0] | 5/5 = 100.0% [100.0, 100.0] | 15/15 = 100.0% [100.0, 100.0] | 138; 100/104; 96/98; 101/102 |
| global | 10 (5) | 5/5 = 100.0% [100.0, 100.0] | 5/5 = 100.0% [100.0, 100.0] | 5/5 = 100.0% [100.0, 100.0] | 15/15 = 100.0% [100.0, 100.0] | 118; 93/96; 90/93; 93/94 |
| no behaviour | 5 (2) | 5/5 = 100.0% [100.0, 100.0] | 5/5 = 100.0% [100.0, 100.0] | 5/5 = 100.0% [100.0, 100.0] | 15/16 = 93.8% [0.0, 100.0] | 116; 92/94; 89/91; 94/96 |

**Paired comparisons** (pass@2 total, pairs; CI on the paired difference; sign test on discordant tasks).

| Level | Comparison | minimal real role | minimal demo roles | Dev |
|---|---|---|---|---|
| behaviour alone | canon minus abs | 2 vs 2: +0 [+0, +0]; tasks 0:0 does not separate | 6 vs 4: +2 [+0, +6]; tasks 1:0, sign p = 1.000 does not separate | 29 vs 24: +5 [-1, +11]; tasks 7:2, sign p = 0.180 does not separate |
| behaviour alone | both minus canon | 2 vs 2: +0 [+0, +0]; tasks 0:0 does not separate | 6 vs 6: +0 [+0, +0]; tasks 0:0 does not separate | 31 vs 29: +2 [+0, +5]; tasks 2:0, sign p = 0.500 does not separate |
| behaviour alone | canon minus global | 2 vs 5: -3 [-8, +0]; tasks 0:2, sign p = 0.500 does not separate | 6 vs 8: -2 [-10, +5]; tasks 1:2, sign p = 1.000 does not separate | 29 vs 2: +27 [+17, +38]; tasks 28:1, sign p = 0.000 separates |
| behaviour alone | abs minus global | 2 vs 5: -3 [-8, +0]; tasks 0:2, sign p = 0.500 does not separate | 4 vs 8: -4 [-13, +4]; tasks 1:2, sign p = 1.000 does not separate | 24 vs 2: +22 [+13, +32]; tasks 23:1, sign p = 0.000 separates |
| system | canon minus abs | 7 vs 7: +0 [+0, +0]; tasks 0:0 does not separate | 22 vs 20: +2 [+0, +6]; tasks 1:0, sign p = 1.000 does not separate | 136 vs 133: +3 [-2, +8]; tasks 5:2, sign p = 0.453 does not separate |
| system | both minus canon | 7 vs 7: +0 [+0, +0]; tasks 0:0 does not separate | 22 vs 22: +0 [+0, +0]; tasks 0:0 does not separate | 138 vs 136: +2 [+0, +5]; tasks 2:0, sign p = 0.500 does not separate |
| system | canon minus global | 7 vs 10: -3 [-8, +0]; tasks 0:2, sign p = 0.500 does not separate | 22 vs 23: -1 [-7, +5]; tasks 1:2, sign p = 1.000 does not separate | 136 vs 118: +18 [+9, +28]; tasks 20:2, sign p = 0.000 separates |
| system | abs minus global | 7 vs 10: -3 [-8, +0]; tasks 0:2, sign p = 0.500 does not separate | 20 vs 23: -3 [-11, +4]; tasks 1:2, sign p = 1.000 does not separate | 133 vs 118: +15 [+7, +24]; tasks 17:2, sign p = 0.001 separates |

**Wrong answers added by `both` over `canon`** (wrong count both minus canon; negative = fewer).

| Level | Rule | Real role | Dev |
|---|---|---|---|
| behaviour alone | evidence >= 0.99 | 0 vs 0: +0 [+0, +0]; tasks 0:0 does not separate | 3 vs 1: +2 [+0, +5]; tasks 2:0, sign p = 0.500 does not separate |
| behaviour alone | v5 | 0 vs 0: +0 [+0, +0]; tasks 0:0 does not separate | 2 vs 0: +2 [+0, +5]; tasks 2:0, sign p = 0.500 does not separate |
| behaviour alone | FA-LOO + (c) | 0 vs 0: +0 [+0, +0]; tasks 0:0 does not separate | 0 vs 0: +0 [+0, +0]; tasks 0:0 does not separate |
| system | evidence >= 0.99 | 0 vs 0: +0 [+0, +0]; tasks 0:0 does not separate | 4 vs 2: +2 [+0, +5]; tasks 2:0, sign p = 0.500 does not separate |
| system | v5 | 0 vs 0: +0 [+0, +0]; tasks 0:0 does not separate | 2 vs 1: +1 [+0, +3]; tasks 1:0, sign p = 1.000 does not separate |
| system | FA-LOO + (c) | 0 vs 0: +0 [+0, +0]; tasks 0:0 does not separate | 1 vs 1: +0 [+0, +0]; tasks 0:0 does not separate |

Items solved by exactly one of canon / abs, behaviour alone:
- canon only: []
- abs only: []
- global only (vs canon): ['InsideOutsideMinimal#1', 'TopBottom2DMinimal#1', 'TopBottom2DMinimal#2']; canon only (vs global): []

## Test 2. Prediction

**Precision of the top answer by evidence bucket** (buckets fixed on development data).

| Column, role | >= 0.99 | [0.5, 0.99) | (0, 0.5) | 0 |
|---|---|---|---|---|
| full system, real | 5/5 = 100.0% [100.0, 100.0] | 2/3 = 66.7% [66.7, 66.7] | 0/0 | 0/17 = 0.0% [0.0, 0.0] |
| full system, demo | 15/16 = 93.8% [0.0, 100.0] | 4/7 = 57.1% [0.0, 66.7] | 0/0 | 2/22 = 9.1% [0.0, 25.0] |
| full system, dev | 100/104 = 96.2% [92.0, 99.1] | 25/34 = 73.5% [57.6, 88.0] | 0/4 = 0.0% [0.0, 0.0] | 9/97 = 9.3% [3.8, 15.4] |
| self-model, real | 2/2 = 100.0% [100.0, 100.0] | 0/0 | 0/0 | 0/0 |
| periodic, real | 0/0 | 0/0 | 0/0 | 0/0 |
| behavior, real | 0/0 | 2/3 = 66.7% [66.7, 66.7] | 0/0 | 0/17 = 0.0% [0.0, 0.0] |
| dynamics, real | 0/0 | 0/0 | 0/0 | 0/0 |
| composition, real | 3/3 = 100.0% [100.0, 100.0] | 0/0 | 0/0 | 0/0 |
| association, real | 0/0 | 0/0 | 0/0 | 0/0 |
| pattern, real | 0/0 | 0/0 | 0/0 | 0/0 |
| field, real | 0/0 | 0/0 | 0/0 | 0/0 |
| self-model, demo | 6/6 = 100.0% [100.0, 100.0] | 0/0 | 0/0 | 0/0 |
| periodic, demo | 0/0 | 0/0 | 0/0 | 0/0 |
| behavior, demo | 0/0 | 4/6 = 66.7% [66.7, 66.7] | 0/0 | 1/25 = 4.0% [0.0, 15.0] |
| dynamics, demo | 0/1 = 0.0% [0.0, 0.0] | 0/1 = 0.0% [0.0, 0.0] | 0/0 | 0/0 |
| composition, demo | 9/9 = 100.0% [100.0, 100.0] | 0/0 | 0/0 | 0/0 |
| association, demo | 0/0 | 0/0 | 0/0 | 0/0 |
| pattern, demo | 0/0 | 0/0 | 0/0 | 1/1 = 100.0% [100.0, 100.0] |
| field, demo | 0/0 | 0/0 | 0/0 | 0/0 |
| behavior raw, real | 0/0 | 2/3 = 66.7% [66.7, 66.7] | 0/0 | 0/17 = 0.0% [0.0, 0.0] |
| pattern raw, real | 0/0 | 0/0 | 0/0 | 0/0 |
| composition raw, real | 3/3 = 100.0% [100.0, 100.0] | 0/0 | 0/0 | 0/0 |

**T2a. Evidence >= 0.99 minus below 0.99 (top answer, full system).**

- real: 5/5 = 100.0% [100.0, 100.0] vs 2/20 = 10.0% [0.0, 30.8]: +90.0 pts [+69.2, +100.0] separates. >=0.99 vs [0.5,0.99): +33.3 pts [+33.3, +33.3] separates. [0.5,0.99) vs below 0.5: +66.7 pts [+66.7, +66.7] separates. AUROC of evidence 0.992 [0.925, 1.000], n = 25.
- demo: 15/16 = 93.8% [0.0, 100.0] vs 6/29 = 20.7% [0.0, 44.0]: +73.1 pts [-24.0, +95.2] does not separate. >=0.99 vs [0.5,0.99): +36.6 pts [-61.5, +100.0] does not separate. [0.5,0.99) vs below 0.5: +48.1 pts [-16.0, +66.7] does not separate. AUROC of evidence 0.913 [0.468, 0.986], n = 45.
- dev: 100/104 = 96.2% [92.0, 99.1] vs 34/135 = 25.2% [18.0, 32.6]: +71.0 pts [+62.7, +79.2] separates. >=0.99 vs [0.5,0.99): +22.6 pts [+7.6, +39.3] separates. [0.5,0.99) vs below 0.5: +64.6 pts [+47.7, +80.2] separates. AUROC of evidence 0.922 [0.881, 0.957], n = 239.

**T2b. Paired precision differences, real role (demo roles in brackets where measured).**

- v5 minus fit: real +64.7 pts [+33.3, +86.4] separates; demo +33.0 pts [-35.4, +60.0] does not separate; dev +27.3 pts [+20.2, +34.8] separates
- fc minus fit: real +64.7 pts [+33.3, +86.4] separates; demo +39.3 pts [+13.9, +72.7] separates; dev +28.3 pts [+21.5, +35.5] separates
- a minus fit: real +64.7 pts [+33.3, +86.4] separates; demo +39.3 pts [+13.9, +72.7] separates; dev +27.4 pts [+20.2, +34.9] separates
- fc minus v5: real +0.0 pts [+0.0, +0.0] does not separate; demo +6.2 pts [+0.0, +25.0] does not separate; dev +1.1 pts [+0.0, +3.3] does not separate
- fc minus a: real +0.0 pts [+0.0, +0.0] does not separate; demo +0.0 pts [+0.0, +0.0] does not separate; dev +0.9 pts [-0.0, +3.1] does not separate
- v5t minus fitt: real +64.7 pts [+33.3, +86.4] separates; demo +33.0 pts [-35.4, +60.0] does not separate; dev +27.3 pts [+20.2, +34.8] separates
- fc minus v5t: real +0.0 pts [+0.0, +0.0] does not separate; demo +6.2 pts [+0.0, +25.0] does not separate; dev +1.1 pts [+0.0, +3.3] does not separate
- p4 minus v5: real +0.0 pts [+0.0, +0.0] does not separate; demo +0.0 pts [+0.0, +0.0] does not separate; dev +1.0 pts [+0.0, +3.3] does not separate

**T2c. Demo roles minus real role, by rule.**

- FA-LOO + (c): +0.0 pts [+0.0, +0.0] does not separate
- (a) only: +0.0 pts [+0.0, +0.0] does not separate
- v5: -6.2 pts [-25.0, +0.0] does not separate
- v5 top only: -6.2 pts [-25.0, +0.0] does not separate
- fit-only: +25.4 pts [+4.8, +38.2] separates

**Answer sets, real role.**

- v5 vs fc: both 5 (5 right under v5); v5 only 0 (0 right): []; fc only 0 (0 right): []
- v5 vs a: both 5 (5 right under v5); v5 only 0 (0 right): []; a only 0 (0 right): []
- fc vs fit: both 5 (5 right under fc); fc only 0 (0 right): []; fit only 12 (1 right): ['CompleteShapeMinimal#2', 'CopyMinimal#1', 'FilledNotFilledMinimal#0', 'FilledNotFilledMinimal#2', 'HorizontalVerticalMinimal#0', 'HorizontalVerticalMinimal#2', 'InsideOutsideMinimal#1', 'InsideOutsideMinimal#2', 'MoveToBoundaryMinimal#0', 'MoveToBoundaryMinimal#1', 'MoveToBoundaryMinimal#2', 'TopBottom2DMinimal#2']
- v5 vs fit: both 5 (5 right under v5); v5 only 0 (0 right): []; fit only 12 (1 right): ['CompleteShapeMinimal#2', 'CopyMinimal#1', 'FilledNotFilledMinimal#0', 'FilledNotFilledMinimal#2', 'HorizontalVerticalMinimal#0', 'HorizontalVerticalMinimal#2', 'InsideOutsideMinimal#1', 'InsideOutsideMinimal#2', 'MoveToBoundaryMinimal#0', 'MoveToBoundaryMinimal#1', 'MoveToBoundaryMinimal#2', 'TopBottom2DMinimal#2']

Wrong, v5: []

Wrong, FA-LOO + (c): []

Wrong in both: []

Wrong, v5 only: []

Wrong, FA-LOO + (c) only: []

Why FA-LOO abstains on items that have a candidate: {'answer': 5, 'fold abstains': 10, '(a)': 10}

## Test 3. Voting

**T3a. Module contributions, real role.**

| Module | Any candidate | Solves alone (tasks) | Lost when removed | Unique solves (tasks) | Alone, evidence >= 0.99 | Alone, FA-LOO + (c) | Demo: alone / unique | Dev: alone / lost / unique |
|---|---|---|---|---|---|---|---|---|
| self-model | 2 | 2 (1) | 2 | 2 (1) | 2/2 = 100.0% [100.0, 100.0] | 2/2 = 100.0% [100.0, 100.0] | 6 / 6 | 9 / 9 / 9 |
| periodic | 0 | 0 (0) | 0 | 0 (0) | 0/0 | 0/0 | 0 / 0 | 10 / 10 / 10 |
| behavior | 20 | 2 (1) | 2 | 2 (1) | 0/0 | 0/0 | 6 / 6 | 31 / 23 / 23 |
| dynamics | 0 | 0 (0) | 0 | 0 (0) | 0/0 | 0/0 | 0 / 0 | 10 / 8 / 8 |
| composition | 3 | 3 (1) | 3 | 3 (1) | 3/3 = 100.0% [100.0, 100.0] | 3/3 = 100.0% [100.0, 100.0] | 9 / 9 | 59 / 59 / 59 |
| association | 0 | 0 (0) | 0 | 0 (0) | 0/0 | 0/0 | 0 / 0 | 3 / 3 / 3 |
| pattern | 0 | 0 (0) | 0 | 0 (0) | 0/0 | 0/0 | 1 / 1 | 25 / 16 / 17 |
| field | 0 | 0 (0) | 0 | 0 (0) | 0/0 | 0/0 | 0 / 0 | 1 / 1 / 1 |

real: full 7, union of modules alone 7; solved by exactly one module 7, two 0, three or more 0 (share exactly one 100.0%). Lost by the vote: 0 []; gained by the vote: 0 [].

demo: full 22, union of modules alone 22; solved by exactly one module 22, two 0, three or more 0 (share exactly one 100.0%). Lost by the vote: 0 []; gained by the vote: 0 [].

dev: full 138, union of modules alone 139; solved by exactly one module 130, two 9, three or more 0 (share exactly one 93.5%). Lost by the vote: 1 ["('54d9e175', 0)"]; gained by the vote: 0 [].

**T3b. Is it a vote? Agreement between modules, and a no-vote baseline.**

| Population | Top answer backed by 2+ modules | Top answer from 1 module | Difference | No-vote: pass@2 vs pool | No-vote vs pool, top answer at evidence >= 0.99 |
|---|---|---|---|---|---|
| real | 0/0 | 7/25 = 28.0% [0.0, 55.0] | n/a | pool minus no-vote: 7 vs 7: +0 [+0, +0]; tasks 0:0 does not separate | pool 5/5 = 100.0% [100.0, 100.0]; no-vote 5/5 = 100.0% [100.0, 100.0]; +0.0 pts [+0.0, +0.0] does not separate |
| demo | 0/0 | 21/45 = 46.7% [10.0, 75.6] | n/a | pool minus no-vote: 22 vs 22: +0 [+0, +0]; tasks 0:0 does not separate | pool 15/16 = 93.8% [0.0, 100.0]; no-vote 15/16 = 93.8% [0.0, 100.0]; +0.0 pts [+0.0, +0.0] does not separate |
| dev | 9/9 = 100.0% [100.0, 100.0] | 125/230 = 54.3% [48.0, 60.7] | +45.7 pts [+39.3, +52.0] separates | pool minus no-vote: 138 vs 137: +1 [+0, +3]; tasks 1:0, sign p = 1.000 does not separate | pool 100/104 = 96.2% [92.0, 99.1]; no-vote 100/103 = 97.1% [93.4, 100.0]; -0.9 pts [-4.4, +2.1] does not separate |

- real, top evidence >= 0.99 only: 2+ modules 0/0; 1 module 5/5 = 100.0% [100.0, 100.0]; n/a
- demo, top evidence >= 0.99 only: 2+ modules 0/0; 1 module 15/16 = 93.8% [0.0, 100.0]; n/a
- dev, top evidence >= 0.99 only: 2+ modules 8/8 = 100.0% [100.0, 100.0]; 1 module 92/96 = 95.8% [91.3, 99.1]; +4.2 pts [+0.9, +8.7] separates

**T3c. 8 D8 views vs 1 view** (48 of 48 items).

| Rule | 1 view, real | 8 views, real | Wrong 8 minus 1 | Precision 8 minus 1 | 1 view, demo | 8 views, demo |
|---|---|---|---|---|---|---|
| v5 rule | 5/5 = 100.0% [100.0, 100.0] | 7/8 = 87.5% [66.7, 100.0] | 1 vs 0: +1 [+0, +3]; tasks 1:0, sign p = 1.000 does not separate | -12.5 pts [-25.0, +0.0] does not separate | 15/16 = 93.8% [0.0, 100.0] | 19/20 = 95.0% [0.0, 100.0] |
| v5 rule, top answer only | 5/5 = 100.0% [100.0, 100.0] | 7/8 = 87.5% [66.7, 100.0] | 1 vs 0: +1 [+0, +3]; tasks 1:0, sign p = 1.000 does not separate | -12.5 pts [-25.0, +0.0] does not separate | 15/16 = 93.8% [0.0, 100.0] | 19/20 = 95.0% [0.0, 100.0] |
| P4 | 5/5 = 100.0% [100.0, 100.0] | 5/5 = 100.0% [100.0, 100.0] | 0 vs 0: +0 [+0, +0]; tasks 0:0 does not separate | +0.0 pts [+0.0, +0.0] does not separate | 15/16 = 93.8% [0.0, 100.0] | 14/15 = 93.3% [0.0, 100.0] |
| FA-LOO (v5 vote) + (c) | 5/5 = 100.0% [100.0, 100.0] | 5/5 = 100.0% [100.0, 100.0] | 0 vs 0: +0 [+0, +0]; tasks 0:0 does not separate | +0.0 pts [+0.0, +0.0] does not separate | 15/15 = 100.0% [100.0, 100.0] | 15/15 = 100.0% [100.0, 100.0] |
| FA-LOO (P4 vote) + (c) | 5/5 = 100.0% [100.0, 100.0] | 5/5 = 100.0% [100.0, 100.0] | 0 vs 0: +0 [+0, +0]; tasks 0:0 does not separate | +0.0 pts [+0.0, +0.0] does not separate | 15/15 = 100.0% [100.0, 100.0] | 15/15 = 100.0% [100.0, 100.0] |
| FA-LOO (v5 vote) | 5/5 = 100.0% [100.0, 100.0] | 5/5 = 100.0% [100.0, 100.0] | 0 vs 0: +0 [+0, +0]; tasks 0:0 does not separate | +0.0 pts [+0.0, +0.0] does not separate | 15/15 = 100.0% [100.0, 100.0] | 15/15 = 100.0% [100.0, 100.0] |
| (a) only | 5/5 = 100.0% [100.0, 100.0] | 5/5 = 100.0% [100.0, 100.0] | 0 vs 0: +0 [+0, +0]; tasks 0:0 does not separate | +0.0 pts [+0.0, +0.0] does not separate | 15/15 = 100.0% [100.0, 100.0] | 15/15 = 100.0% [100.0, 100.0] |

- 8-view v5 minus 8-view P4: real -12.5 pts [-25.0, +0.0] does not separate; demo +1.7 pts [+0.0, +80.0] does not separate
- 8-view v5 minus 8-view FA-LOO + (c): real -12.5 pts [-25.0, +0.0] does not separate; demo -5.0 pts [-23.5, +0.0] does not separate
- 8-view P4 minus 8-view FA-LOO + (c): real +0.0 pts [+0.0, +0.0] does not separate; demo -6.7 pts [-27.3, +0.0] does not separate
- pass@2, 8 views minus 1 view: 7 vs 7: +0 [+0, +0]; tasks 0:0 does not separate
- New wrong under 8-view v5: ['FilledNotFilledMinimal#2']
- Wrong at 1-view v5 no longer wrong at 8 views: []
- Wrong under 8-view P4: []
- Wrong under 8-view FA-LOO + (c): []
- 1-view v5 answers not answered at 8-view FA-LOO + (c): 0
