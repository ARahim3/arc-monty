Dataset `concept`: 480 items (test pairs) in 160 tasks; 1281 demo-role items. Dev comparators: 1147 tasks, unit = task.

## Acceptance rules (real and demo roles)

| Rule | Real role | Coverage | Demo roles | Dev (1,147, by task) |
|---|---|---|---|---|
| FA-LOO + (c) | 35/44 = 79.5% [64.4, 92.3] | 9.2% | 100/111 = 90.1% [79.1, 96.2] | 101/102 = 99.0% [96.7, 100.0] |
| FA-LOO (a)+(b) | 35/44 = 79.5% [64.4, 92.3] | 9.2% | 101/112 = 90.2% [79.4, 96.2] | 101/103 = 98.1% [95.0, 100.0] |
| (a) only, full-data answer | 35/44 = 79.5% [64.4, 92.3] | 9.2% | 100/112 = 89.3% [77.9, 95.6] | 102/104 = 98.1% [94.9, 100.0] |
| v5 heuristic (2 attempts) | 42/49 = 85.7% [74.2, 95.2] | 10.2% | 112/123 = 91.1% [81.1, 96.7] | 96/98 = 98.0% [94.7, 100.0] |
| v5 heuristic, top answer only | 42/49 = 85.7% [74.2, 95.2] | 10.2% | 112/123 = 91.1% [81.1, 96.7] | 96/98 = 98.0% [94.7, 100.0] |
| P4 confident (2 attempts) | 42/49 = 85.7% [74.2, 95.2] | 10.2% | 116/126 = 92.1% [82.6, 97.3] | 97/98 = 99.0% [96.6, 100.0] |
| fit to demos only (2 attempts) | 43/74 = 58.1% [41.4, 73.4] | 15.4% | 119/186 = 64.0% [48.0, 76.2] | 111/157 = 70.7% [63.4, 77.6] |
| fit to demos only, top answer only | 43/74 = 58.1% [41.4, 73.4] | 15.4% | 119/186 = 64.0% [48.0, 76.2] | 111/157 = 70.7% [63.4, 77.6] |

pass@2, real role: 58/480 = 12.1% (count CI [37, 81]); tasks with at least one solve: 26/160. Items with any candidate: 136.
Joint P(answer and wrong), FA-LOO + (c), real role: 9/480 = 1.88%. Task-level: 18 tasks answered, 7 with a wrong answer; mean per-task precision 76.9%.

## Test 1. Frames

**behaviour alone.**

| Arm | pass@2 (tasks) | top answer at evidence >= 0.99 | v5 rule | FA-LOO + (c) real | FA-LOO + (c) demo | Dev: pass@2; >=0.99; v5; FA-LOO + (c) |
|---|---|---|---|---|---|---|
| canon | 11 (9) | 3/6 = 50.0% [33.3, 66.7] | 3/4 = 75.0% [50.0, 100.0] | 3/6 = 50.0% [33.3, 66.7] | 6/9 = 66.7% [0.0, 100.0] | 29; 13/14; 13/13; 12/12 |
| abs | 5 (5) | 0/0 | 0/0 | 0/0 | 0/4 = 0.0% [0.0, 0.0] | 24; 11/12; 11/11; 9/9 |
| both | 11 (9) | 3/6 = 50.0% [33.3, 66.7] | 3/4 = 75.0% [50.0, 100.0] | 3/6 = 50.0% [33.3, 66.7] | 5/8 = 62.5% [0.0, 100.0] | 31; 13/16; 13/15; 11/11 |
| global | 5 (5) | 0/0 | 0/0 | 0/0 | 0/1 = 0.0% [0.0, 0.0] | 2; 1/2; 1/2; 1/1 |

**system.**

| Arm | pass@2 (tasks) | top answer at evidence >= 0.99 | v5 rule | FA-LOO + (c) real | FA-LOO + (c) demo | Dev: pass@2; >=0.99; v5; FA-LOO + (c) |
|---|---|---|---|---|---|---|
| canon | 58 (26) | 44/54 = 81.5% [69.0, 91.9] | 42/49 = 85.7% [74.2, 95.2] | 38/47 = 80.9% [66.7, 92.9] | 110/121 = 90.9% [80.8, 96.5] | 136; 101/103; 97/98; 103/104 |
| abs | 52 (22) | 41/48 = 85.4% [73.2, 95.1] | 39/45 = 86.7% [74.5, 96.4] | 35/41 = 85.4% [70.7, 96.4] | 104/116 = 89.7% [78.3, 95.5] | 133; 99/102; 96/98; 100/101 |
| both | 58 (26) | 44/54 = 81.5% [69.0, 91.9] | 42/49 = 85.7% [74.2, 95.2] | 35/44 = 79.5% [64.4, 92.3] | 100/111 = 90.1% [79.1, 96.2] | 138; 100/104; 96/98; 101/102 |
| global | 53 (23) | 41/48 = 85.4% [73.2, 95.1] | 39/45 = 86.7% [74.5, 96.4] | 33/39 = 84.6% [68.8, 96.2] | 99/107 = 92.5% [82.5, 97.7] | 118; 93/96; 90/93; 93/94 |
| no behaviour | 48 (18) | 41/48 = 85.4% [73.2, 95.1] | 39/45 = 86.7% [74.5, 96.4] | 41/47 = 87.2% [75.0, 96.9] | 114/124 = 91.9% [82.4, 97.2] | 116; 92/94; 89/91; 94/96 |

**Paired comparisons** (pass@2 total, pairs; CI on the paired difference; sign test on discordant tasks).

| Level | Comparison | concept real role | concept demo roles | Dev |
|---|---|---|---|---|
| behaviour alone | canon minus abs | 11 vs 5: +6 [+1, +12]; tasks 5:0, sign p = 0.062 separates | 46 vs 28: +18 [+4, +37]; tasks 5:0, sign p = 0.062 separates | 29 vs 24: +5 [-1, +11]; tasks 7:2, sign p = 0.180 does not separate |
| behaviour alone | both minus canon | 11 vs 11: +0 [+0, +0]; tasks 0:0 does not separate | 45 vs 46: -1 [-3, +0]; tasks 0:1, sign p = 1.000 does not separate | 31 vs 29: +2 [+0, +5]; tasks 2:0, sign p = 0.500 does not separate |
| behaviour alone | canon minus global | 11 vs 5: +6 [-1, +14]; tasks 7:3, sign p = 0.344 does not separate | 46 vs 15: +31 [+4, +66]; tasks 7:3, sign p = 0.344 separates | 29 vs 2: +27 [+17, +38]; tasks 28:1, sign p = 0.000 separates |
| behaviour alone | abs minus global | 5 vs 5: +0 [-6, +6]; tasks 4:4, sign p = 1.000 does not separate | 28 vs 15: +13 [-6, +38]; tasks 3:3, sign p = 1.000 does not separate | 24 vs 2: +22 [+13, +32]; tasks 23:1, sign p = 0.000 separates |
| system | canon minus abs | 58 vs 52: +6 [+1, +12]; tasks 5:0, sign p = 0.062 separates | 180 vs 162: +18 [+4, +37]; tasks 5:0, sign p = 0.062 separates | 136 vs 133: +3 [-2, +8]; tasks 5:2, sign p = 0.453 does not separate |
| system | both minus canon | 58 vs 58: +0 [+0, +0]; tasks 0:0 does not separate | 179 vs 180: -1 [-3, +0]; tasks 0:1, sign p = 1.000 does not separate | 138 vs 136: +2 [+0, +5]; tasks 2:0, sign p = 0.500 does not separate |
| system | canon minus global | 58 vs 53: +5 [-2, +13]; tasks 6:3, sign p = 0.508 does not separate | 180 vs 157: +23 [+0, +55]; tasks 6:3, sign p = 0.508 does not separate | 136 vs 118: +18 [+9, +28]; tasks 20:2, sign p = 0.000 separates |
| system | abs minus global | 52 vs 53: -1 [-6, +4]; tasks 3:4, sign p = 1.000 does not separate | 162 vs 157: +5 [-8, +23]; tasks 2:3, sign p = 1.000 does not separate | 133 vs 118: +15 [+7, +24]; tasks 17:2, sign p = 0.001 separates |

**Wrong answers added by `both` over `canon`** (wrong count both minus canon; negative = fewer).

| Level | Rule | Real role | Dev |
|---|---|---|---|
| behaviour alone | evidence >= 0.99 | 3 vs 3: +0 [+0, +0]; tasks 0:0 does not separate | 3 vs 1: +2 [+0, +5]; tasks 2:0, sign p = 0.500 does not separate |
| behaviour alone | v5 | 1 vs 1: +0 [+0, +0]; tasks 0:0 does not separate | 2 vs 0: +2 [+0, +5]; tasks 2:0, sign p = 0.500 does not separate |
| behaviour alone | FA-LOO + (c) | 3 vs 3: +0 [+0, +0]; tasks 0:0 does not separate | 0 vs 0: +0 [+0, +0]; tasks 0:0 does not separate |
| system | evidence >= 0.99 | 10 vs 10: +0 [+0, +0]; tasks 0:0 does not separate | 4 vs 2: +2 [+0, +5]; tasks 2:0, sign p = 0.500 does not separate |
| system | v5 | 7 vs 7: +0 [+0, +0]; tasks 0:0 does not separate | 2 vs 1: +1 [+0, +3]; tasks 1:0, sign p = 1.000 does not separate |
| system | FA-LOO + (c) | 9 vs 9: +0 [+0, +0]; tasks 0:0 does not separate | 1 vs 1: +0 [+0, +0]; tasks 0:0 does not separate |

Items solved by exactly one of canon / abs, behaviour alone:
- canon only: ['CleanUp/CleanUp5#2', 'CompleteShape/CompleteShape5#0', 'CompleteShape/CompleteShape5#1', 'CompleteShape/CompleteShape6#0', 'SameDifferent/SameDifferent1#1', 'TopBottom3D/TopBottom3D8#2']
- abs only: []
- global only (vs canon): ['HorizontalVertical/HorizontalVertical7#2', 'InsideOutside/InsideOutside4#1', 'SameDifferent/SameDifferent1#2', 'SameDifferent/SameDifferent4#1']; canon only (vs global): ['Center/Center1#0', 'Center/Center9#0', 'CleanUp/CleanUp5#2', 'CompleteShape/CompleteShape5#0', 'CompleteShape/CompleteShape5#1', 'CompleteShape/CompleteShape6#0', 'ExtendToBoundary/ExtendToBoundary5#2', 'SameDifferent/SameDifferent1#1', 'TopBottom3D/TopBottom3D8#0', 'TopBottom3D/TopBottom3D8#2']

## Test 2. Prediction

**Precision of the top answer by evidence bucket** (buckets fixed on development data).

| Column, role | >= 0.99 | [0.5, 0.99) | (0, 0.5) | 0 |
|---|---|---|---|---|
| full system, real | 44/54 = 81.5% [69.0, 91.9] | 4/10 = 40.0% [0.0, 100.0] | 0/1 = 0.0% [0.0, 0.0] | 7/71 = 9.9% [1.7, 20.9] |
| full system, demo | 121/139 = 87.1% [76.3, 93.7] | 26/46 = 56.5% [31.6, 73.3] | 9/12 = 75.0% [0.0, 100.0] | 16/153 = 10.5% [2.8, 19.3] |
| full system, dev | 100/104 = 96.2% [92.0, 99.1] | 25/34 = 73.5% [57.6, 88.0] | 0/4 = 0.0% [0.0, 0.0] | 9/97 = 9.3% [3.8, 15.4] |
| self-model, real | 6/9 = 66.7% [66.7, 66.7] | 0/0 | 0/0 | 0/0 |
| periodic, real | 1/4 = 25.0% [0.0, 50.0] | 0/0 | 0/0 | 0/0 |
| behavior, real | 3/6 = 50.0% [33.3, 66.7] | 2/7 = 28.6% [0.0, 100.0] | 0/0 | 4/72 = 5.6% [1.2, 11.9] |
| dynamics, real | 17/18 = 94.4% [83.3, 100.0] | 0/3 = 0.0% [0.0, 0.0] | 0/0 | 3/3 = 100.0% [100.0, 100.0] |
| composition, real | 17/17 = 100.0% [100.0, 100.0] | 3/3 = 100.0% [100.0, 100.0] | 0/0 | 0/0 |
| association, real | 0/0 | 0/0 | 0/0 | 0/0 |
| pattern, real | 0/0 | 0/0 | 0/1 = 0.0% [0.0, 0.0] | 0/10 = 0.0% [0.0, 0.0] |
| field, real | 0/0 | 0/0 | 0/0 | 0/0 |
| self-model, demo | 12/12 = 100.0% [100.0, 100.0] | 0/0 | 0/0 | 0/0 |
| periodic, demo | 2/2 = 100.0% [100.0, 100.0] | 2/5 = 40.0% [0.0, 100.0] | 0/0 | 0/0 |
| behavior, demo | 9/19 = 47.4% [0.0, 80.0] | 16/32 = 50.0% [5.9, 76.0] | 9/12 = 75.0% [0.0, 100.0] | 10/146 = 6.8% [0.8, 13.8] |
| dynamics, demo | 49/57 = 86.0% [58.5, 97.1] | 4/5 = 80.0% [0.0, 100.0] | 0/0 | 6/6 = 100.0% [100.0, 100.0] |
| composition, demo | 51/53 = 96.2% [83.7, 100.0] | 13/18 = 72.2% [0.0, 90.9] | 0/0 | 0/0 |
| association, demo | 0/0 | 0/0 | 0/0 | 0/0 |
| pattern, demo | 0/0 | 0/0 | 0/0 | 1/19 = 5.3% [0.0, 20.0] |
| field, demo | 0/0 | 0/0 | 0/0 | 0/0 |
| behavior raw, real | 4/6 = 66.7% [66.7, 66.7] | 2/7 = 28.6% [0.0, 100.0] | 0/0 | 4/72 = 5.6% [1.2, 11.9] |
| pattern raw, real | 0/0 | 0/0 | 0/1 = 0.0% [0.0, 0.0] | 0/10 = 0.0% [0.0, 0.0] |
| composition raw, real | 17/17 = 100.0% [100.0, 100.0] | 3/3 = 100.0% [100.0, 100.0] | 0/0 | 0/0 |

**T2a. Evidence >= 0.99 minus below 0.99 (top answer, full system).**

- real: 44/54 = 81.5% [69.0, 91.9] vs 11/82 = 13.4% [3.9, 25.7]: +68.1 pts [+51.5, +82.6] separates. >=0.99 vs [0.5,0.99): +41.5 pts [-23.5, +86.4] does not separate. [0.5,0.99) vs below 0.5: +30.3 pts [-13.6, +94.7] does not separate. AUROC of evidence 0.873 [0.785, 0.945], n = 136.
- demo: 121/139 = 87.1% [76.3, 93.7] vs 51/211 = 24.2% [13.7, 35.2]: +62.9 pts [+48.4, +75.3] separates. >=0.99 vs [0.5,0.99): +30.5 pts [+12.9, +54.6] separates. [0.5,0.99) vs below 0.5: +41.4 pts [+14.1, +62.7] separates. AUROC of evidence 0.865 [0.795, 0.922], n = 350.
- dev: 100/104 = 96.2% [92.0, 99.1] vs 34/135 = 25.2% [18.0, 32.6]: +71.0 pts [+62.7, +79.2] separates. >=0.99 vs [0.5,0.99): +22.6 pts [+7.6, +39.3] separates. [0.5,0.99) vs below 0.5: +64.6 pts [+47.7, +80.2] separates. AUROC of evidence 0.922 [0.881, 0.957], n = 239.

**T2b. Paired precision differences, real role (demo roles in brackets where measured).**

- v5 minus fit: real +27.6 pts [+11.3, +45.4] separates; demo +27.1 pts [+16.9, +39.4] separates; dev +27.3 pts [+20.2, +34.8] separates
- fc minus fit: real +21.4 pts [+3.3, +40.3] separates; demo +26.1 pts [+15.1, +39.0] separates; dev +28.3 pts [+21.5, +35.5] separates
- a minus fit: real +21.4 pts [+3.3, +40.3] separates; demo +25.3 pts [+14.2, +38.3] separates; dev +27.4 pts [+20.2, +34.9] separates
- fc minus v5: real -6.2 pts [-15.1, +1.8] does not separate; demo -1.0 pts [-7.9, +5.2] does not separate; dev +1.1 pts [+0.0, +3.3] does not separate
- fc minus a: real +0.0 pts [+0.0, +0.0] does not separate; demo +0.8 pts [+0.0, +2.8] does not separate; dev +0.9 pts [-0.0, +3.1] does not separate
- v5t minus fitt: real +27.6 pts [+11.3, +45.4] separates; demo +27.1 pts [+16.9, +39.4] separates; dev +27.3 pts [+20.2, +34.8] separates
- fc minus v5t: real -6.2 pts [-15.1, +1.8] does not separate; demo -1.0 pts [-7.9, +5.2] does not separate; dev +1.1 pts [+0.0, +3.3] does not separate
- p4 minus v5: real +0.0 pts [+0.0, +0.0] does not separate; demo +1.0 pts [+0.0, +3.1] does not separate; dev +1.0 pts [+0.0, +3.3] does not separate

**T2c. Demo roles minus real role, by rule.**

- FA-LOO + (c): +10.5 pts [-4.2, +24.5] does not separate
- (a) only: +9.7 pts [-4.5, +22.7] does not separate
- v5: +5.3 pts [-8.0, +16.8] does not separate
- v5 top only: +5.3 pts [-8.0, +16.8] does not separate
- fit-only: +5.9 pts [-8.3, +18.0] does not separate

**FA-LOO + (c) by concept group, and the gap with each group left out.**

| Group | Real role | Demo roles | v5 real | Gap (demo - real) with this group left out |
|---|---|---|---|---|
| AboveBelow | 0/0 | 0/0 | 0/0 | +10.5 pts [-4.2, +24.5] does not separate |
| Center | 0/0 | 0/1 | 0/0 | +11.4 pts [-3.2, +25.3] does not separate |
| CleanUp | 3/5 | 4/6 | 3/4 | +9.4 pts [-5.9, +24.8] does not separate |
| CompleteShape | 6/10 | 8/8 | 6/10 | +4.0 pts [-11.7, +18.6] does not separate |
| Copy | 3/3 | 9/9 | 3/3 | +11.2 pts [-4.7, +25.7] does not separate |
| Count | 0/0 | 0/1 | 0/0 | +11.4 pts [-3.2, +25.2] does not separate |
| ExtendToBoundary | 3/3 | 10/10 | 6/6 | +11.1 pts [-4.8, +25.4] does not separate |
| ExtractObjects | 5/5 | 12/13 | 4/4 | +12.9 pts [-3.2, +28.0] does not separate |
| FilledNotFilled | 3/4 | 13/14 | 5/6 | +9.7 pts [-6.1, +24.0] does not separate |
| HorizontalVertical | 0/0 | 0/0 | 0/0 | +10.5 pts [-4.2, +24.5] does not separate |
| InsideOutside | 0/0 | 0/0 | 0/0 | +10.5 pts [-4.2, +24.5] does not separate |
| MoveToBoundary | 2/2 | 5/9 | 6/6 | +14.6 pts [+0.0, +29.1] separates |
| Order | 0/0 | 0/0 | 0/0 | +10.5 pts [-4.2, +24.5] does not separate |
| SameDifferent | 0/0 | 0/0 | 0/0 | +10.5 pts [-4.2, +24.5] does not separate |
| TopBottom2D | 9/9 | 36/37 | 8/8 | +12.2 pts [-6.6, +28.6] does not separate |
| TopBottom3D | 1/3 | 3/3 | 1/2 | +6.9 pts [-7.4, +20.2] does not separate |

**Answer sets, real role.**

- v5 vs fc: both 38 (32 right under v5); v5 only 11 (10 right): ['CompleteShape/CompleteShape9#1', 'ExtendToBoundary/ExtendToBoundary5#0', 'ExtendToBoundary/ExtendToBoundary5#1', 'ExtendToBoundary/ExtendToBoundary5#2', 'ExtractObjects/ExtractObjects3#0', 'FilledNotFilled/FilledNotFilled9#0', 'FilledNotFilled/FilledNotFilled9#1', 'MoveToBoundary/MoveToBoundary3#0', 'MoveToBoundary/MoveToBoundary3#1', 'MoveToBoundary/MoveToBoundary3#2', 'MoveToBoundary/MoveToBoundary4#0']; fc only 6 (3 right): ['CleanUp/CleanUp10#1', 'CompleteShape/CompleteShape5#2', 'ExtractObjects/ExtractObjects1#2', 'ExtractObjects/ExtractObjects3#1', 'TopBottom2D/TopBottom2D1#1', 'TopBottom3D/TopBottom3D8#2']
- v5 vs a: both 38 (32 right under v5); v5 only 11 (10 right): ['CompleteShape/CompleteShape9#1', 'ExtendToBoundary/ExtendToBoundary5#0', 'ExtendToBoundary/ExtendToBoundary5#1', 'ExtendToBoundary/ExtendToBoundary5#2', 'ExtractObjects/ExtractObjects3#0', 'FilledNotFilled/FilledNotFilled9#0', 'FilledNotFilled/FilledNotFilled9#1', 'MoveToBoundary/MoveToBoundary3#0', 'MoveToBoundary/MoveToBoundary3#1', 'MoveToBoundary/MoveToBoundary3#2', 'MoveToBoundary/MoveToBoundary4#0']; a only 6 (3 right): ['CleanUp/CleanUp10#1', 'CompleteShape/CompleteShape5#2', 'ExtractObjects/ExtractObjects1#2', 'ExtractObjects/ExtractObjects3#1', 'TopBottom2D/TopBottom2D1#1', 'TopBottom3D/TopBottom3D8#2']
- fc vs fit: both 30 (28 right under fc); fc only 14 (7 right): ['CleanUp/CleanUp10#1', 'CompleteShape/CompleteShape1#0', 'CompleteShape/CompleteShape1#1', 'CompleteShape/CompleteShape1#2', 'CompleteShape/CompleteShape5#0', 'CompleteShape/CompleteShape5#1', 'CompleteShape/CompleteShape5#2', 'CompleteShape/CompleteShape7#1', 'CompleteShape/CompleteShape7#2', 'ExtendToBoundary/ExtendToBoundary2#0', 'ExtractObjects/ExtractObjects1#2', 'ExtractObjects/ExtractObjects3#1', 'TopBottom3D/TopBottom3D8#1', 'TopBottom3D/TopBottom3D8#2']; fit only 44 (15 right): ['AboveBelow/AboveBelow10#0', 'AboveBelow/AboveBelow10#1', 'AboveBelow/AboveBelow10#2', 'AboveBelow/AboveBelow3#2', 'AboveBelow/AboveBelow6#1', 'AboveBelow/AboveBelow6#2', 'Center/Center1#0', 'Center/Center6#0', 'Center/Center6#1', 'CleanUp/CleanUp2#2', 'CompleteShape/CompleteShape10#0', 'CompleteShape/CompleteShape10#1', 'CompleteShape/CompleteShape2#2', 'CompleteShape/CompleteShape9#1', 'Copy/Copy2#2', 'Copy/Copy7#1', 'ExtendToBoundary/ExtendToBoundary3#0', 'ExtendToBoundary/ExtendToBoundary4#0', 'ExtendToBoundary/ExtendToBoundary5#2', 'ExtendToBoundary/ExtendToBoundary8#0', 'ExtendToBoundary/ExtendToBoundary8#1', 'ExtendToBoundary/ExtendToBoundary8#2', 'ExtractObjects/ExtractObjects3#0', 'FilledNotFilled/FilledNotFilled10#2', 'FilledNotFilled/FilledNotFilled9#0', 'FilledNotFilled/FilledNotFilled9#1', 'HorizontalVertical/HorizontalVertical5#0', 'HorizontalVertical/HorizontalVertical5#1', 'HorizontalVertical/HorizontalVertical5#2', 'HorizontalVertical/HorizontalVertical7#0', 'HorizontalVertical/HorizontalVertical7#1', 'HorizontalVertical/HorizontalVertical7#2', 'HorizontalVertical/HorizontalVertical9#0', 'MoveToBoundary/MoveToBoundary3#0', 'MoveToBoundary/MoveToBoundary3#1', 'MoveToBoundary/MoveToBoundary3#2', 'MoveToBoundary/MoveToBoundary4#0', 'SameDifferent/SameDifferent4#0', 'SameDifferent/SameDifferent7#0', 'SameDifferent/SameDifferent7#1', 'SameDifferent/SameDifferent7#2', 'TopBottom2D/TopBottom2D1#0', 'TopBottom2D/TopBottom2D1#2', 'TopBottom3D/TopBottom3D2#0']
- v5 vs fit: both 38 (35 right under v5); v5 only 11 (7 right): ['CompleteShape/CompleteShape1#0', 'CompleteShape/CompleteShape1#1', 'CompleteShape/CompleteShape1#2', 'CompleteShape/CompleteShape5#0', 'CompleteShape/CompleteShape5#1', 'CompleteShape/CompleteShape7#1', 'CompleteShape/CompleteShape7#2', 'ExtendToBoundary/ExtendToBoundary2#0', 'ExtendToBoundary/ExtendToBoundary5#0', 'ExtendToBoundary/ExtendToBoundary5#1', 'TopBottom3D/TopBottom3D8#1']; fit only 36 (8 right): ['AboveBelow/AboveBelow10#0', 'AboveBelow/AboveBelow10#1', 'AboveBelow/AboveBelow10#2', 'AboveBelow/AboveBelow3#2', 'AboveBelow/AboveBelow6#1', 'AboveBelow/AboveBelow6#2', 'Center/Center1#0', 'Center/Center6#0', 'Center/Center6#1', 'CleanUp/CleanUp2#2', 'CompleteShape/CompleteShape10#0', 'CompleteShape/CompleteShape10#1', 'CompleteShape/CompleteShape2#2', 'Copy/Copy2#2', 'Copy/Copy7#1', 'ExtendToBoundary/ExtendToBoundary3#0', 'ExtendToBoundary/ExtendToBoundary4#0', 'ExtendToBoundary/ExtendToBoundary8#0', 'ExtendToBoundary/ExtendToBoundary8#1', 'ExtendToBoundary/ExtendToBoundary8#2', 'FilledNotFilled/FilledNotFilled10#2', 'HorizontalVertical/HorizontalVertical5#0', 'HorizontalVertical/HorizontalVertical5#1', 'HorizontalVertical/HorizontalVertical5#2', 'HorizontalVertical/HorizontalVertical7#0', 'HorizontalVertical/HorizontalVertical7#1', 'HorizontalVertical/HorizontalVertical7#2', 'HorizontalVertical/HorizontalVertical9#0', 'SameDifferent/SameDifferent4#0', 'SameDifferent/SameDifferent7#0', 'SameDifferent/SameDifferent7#1', 'SameDifferent/SameDifferent7#2', 'TopBottom2D/TopBottom2D1#0', 'TopBottom2D/TopBottom2D1#1', 'TopBottom2D/TopBottom2D1#2', 'TopBottom3D/TopBottom3D2#0']

Wrong, v5: ['CleanUp/CleanUp1#2', 'CompleteShape/CompleteShape1#2', 'CompleteShape/CompleteShape7#1', 'CompleteShape/CompleteShape7#2', 'CompleteShape/CompleteShape9#1', 'FilledNotFilled/FilledNotFilled9#2', 'TopBottom3D/TopBottom3D8#1']

Wrong, FA-LOO + (c): ['CleanUp/CleanUp1#2', 'CleanUp/CleanUp10#1', 'CompleteShape/CompleteShape1#2', 'CompleteShape/CompleteShape5#2', 'CompleteShape/CompleteShape7#1', 'CompleteShape/CompleteShape7#2', 'FilledNotFilled/FilledNotFilled9#2', 'TopBottom3D/TopBottom3D8#1', 'TopBottom3D/TopBottom3D8#2']

Wrong in both: ['CleanUp/CleanUp1#2', 'CompleteShape/CompleteShape1#2', 'CompleteShape/CompleteShape7#1', 'CompleteShape/CompleteShape7#2', 'FilledNotFilled/FilledNotFilled9#2', 'TopBottom3D/TopBottom3D8#1']

Wrong, v5 only: ['CompleteShape/CompleteShape9#1']

Wrong, FA-LOO + (c) only: ['CleanUp/CleanUp10#1', 'CompleteShape/CompleteShape5#2', 'TopBottom3D/TopBottom3D8#2']

Why FA-LOO abstains on items that have a candidate: {'(a)': 55, 'fold abstains': 37, 'answer': 44}

## Test 3. Voting

**T3a. Module contributions, real role.**

| Module | Any candidate | Solves alone (tasks) | Lost when removed | Unique solves (tasks) | Alone, evidence >= 0.99 | Alone, FA-LOO + (c) | Demo: alone / unique | Dev: alone / lost / unique |
|---|---|---|---|---|---|---|---|---|
| self-model | 9 | 6 (3) | 6 | 6 (3) | 6/9 = 66.7% [66.7, 66.7] | 6/9 = 66.7% [66.7, 66.7] | 12 / 12 | 9 / 9 / 9 |
| periodic | 4 | 2 (1) | 2 | 2 (1) | 1/4 = 25.0% [0.0, 50.0] | 1/4 = 25.0% [0.0, 50.0] | 4 / 4 | 10 / 10 / 10 |
| behavior | 85 | 11 (9) | 10 | 10 (8) | 3/6 = 50.0% [33.3, 66.7] | 3/6 = 50.0% [33.3, 66.7] | 45 / 37 | 31 / 23 / 23 |
| dynamics | 24 | 20 (7) | 19 | 19 (7) | 17/18 = 94.4% [83.3, 100.0] | 17/18 = 94.4% [83.3, 100.0] | 59 / 51 | 10 / 8 / 8 |
| composition | 20 | 20 (7) | 20 | 20 (7) | 17/17 = 100.0% [100.0, 100.0] | 17/17 = 100.0% [100.0, 100.0] | 66 / 66 | 59 / 59 / 59 |
| association | 0 | 0 (0) | 0 | 0 (0) | 0/0 | 0/0 | 0 / 0 | 3 / 3 / 3 |
| pattern | 11 | 0 (0) | 0 | 0 (0) | 0/0 | 0/0 | 1 / 1 | 25 / 16 / 17 |
| field | 0 | 0 (0) | 0 | 0 (0) | 0/0 | 0/0 | 0 / 0 | 1 / 1 / 1 |

real: full 58, union of modules alone 58; solved by exactly one module 57, two 1, three or more 0 (share exactly one 98.3%). Lost by the vote: 0 []; gained by the vote: 0 [].

demo: full 179, union of modules alone 179; solved by exactly one module 171, two 8, three or more 0 (share exactly one 95.5%). Lost by the vote: 0 []; gained by the vote: 0 [].

dev: full 138, union of modules alone 139; solved by exactly one module 130, two 9, three or more 0 (share exactly one 93.5%). Lost by the vote: 1 ["('54d9e175', 0)"]; gained by the vote: 0 [].

**T3b. Is it a vote? Agreement between modules, and a no-vote baseline.**

| Population | Top answer backed by 2+ modules | Top answer from 1 module | Difference | No-vote: pass@2 vs pool | No-vote vs pool, top answer at evidence >= 0.99 |
|---|---|---|---|---|---|
| real | 1/4 = 25.0% [0.0, 100.0] | 54/132 = 40.9% [28.5, 53.6] | -15.9 pts [-49.6, +61.7] does not separate | pool minus no-vote: 58 vs 58: +0 [+0, +0]; tasks 0:0 does not separate | pool 44/54 = 81.5% [69.0, 91.9]; no-vote 45/54 = 83.3% [72.3, 92.7]; -1.9 pts [-6.2, +0.0] does not separate |
| demo | 8/8 = 100.0% [100.0, 100.0] | 164/342 = 48.0% [35.1, 59.6] | +52.0 pts [+40.6, +65.0] separates | pool minus no-vote: 179 vs 179: +0 [+0, +0]; tasks 0:0 does not separate | pool 121/139 = 87.1% [76.3, 93.7]; no-vote 124/138 = 89.9% [79.4, 96.0]; -2.8 pts [-6.2, +0.0] does not separate |
| dev | 9/9 = 100.0% [100.0, 100.0] | 125/230 = 54.3% [48.0, 60.7] | +45.7 pts [+39.3, +52.0] separates | pool minus no-vote: 138 vs 137: +1 [+0, +3]; tasks 1:0, sign p = 1.000 does not separate | pool 100/104 = 96.2% [92.0, 99.1]; no-vote 100/103 = 97.1% [93.4, 100.0]; -0.9 pts [-4.4, +2.1] does not separate |

- real, top evidence >= 0.99 only: 2+ modules 1/1 = 100.0% [100.0, 100.0]; 1 module 43/53 = 81.1% [68.8, 91.7]; +18.9 pts [+8.2, +30.5] separates
- demo, top evidence >= 0.99 only: 2+ modules 8/8 = 100.0% [100.0, 100.0]; 1 module 113/131 = 86.3% [74.3, 93.5]; +13.7 pts [+7.4, +26.1] separates
- dev, top evidence >= 0.99 only: 2+ modules 8/8 = 100.0% [100.0, 100.0]; 1 module 92/96 = 95.8% [91.3, 99.1]; +4.2 pts [+0.9, +8.7] separates

**T3c. 8 D8 views vs 1 view** (480 of 480 items).

| Rule | 1 view, real | 8 views, real | Wrong 8 minus 1 | Precision 8 minus 1 | 1 view, demo | 8 views, demo |
|---|---|---|---|---|---|---|
| v5 rule | 42/49 = 85.7% [74.2, 95.2] | 44/50 = 88.0% [77.1, 97.2] | 6 vs 7: -1 [-4, +2]; tasks 1:2, sign p = 1.000 does not separate | +2.3 pts [-3.7, +9.0] does not separate | 112/123 = 91.1% [81.1, 96.7] | 121/139 = 87.1% [76.1, 94.0] |
| v5 rule, top answer only | 42/49 = 85.7% [74.2, 95.2] | 43/50 = 86.0% [75.0, 95.5] | 7 vs 7: +0 [-3, +3]; tasks 1:1, sign p = 1.000 does not separate | +0.3 pts [-4.6, +5.3] does not separate | 112/123 = 91.1% [81.1, 96.7] | 120/139 = 86.3% [75.3, 93.3] |
| P4 | 42/49 = 85.7% [74.2, 95.2] | 43/49 = 87.8% [76.5, 97.1] | 6 vs 7: -1 [-4, +2]; tasks 1:2, sign p = 1.000 does not separate | +2.0 pts [-3.6, +8.3] does not separate | 116/126 = 92.1% [82.6, 97.3] | 118/129 = 91.5% [81.7, 97.1] |
| FA-LOO (v5 vote) + (c) | 35/44 = 79.5% [64.4, 92.3] | 34/43 = 79.1% [65.2, 90.7] | 9 vs 9: +0 [-5, +4]; tasks 2:1, sign p = 1.000 does not separate | -0.5 pts [-8.6, +8.9] does not separate | 100/111 = 90.1% [79.1, 96.2] | 97/109 = 89.0% [77.9, 95.1] |
| FA-LOO (P4 vote) + (c) | 39/46 = 84.8% [72.4, 95.0] | 39/48 = 81.2% [68.8, 91.7] | 9 vs 7: +2 [+0, +5]; tasks 2:0, sign p = 0.500 does not separate | -3.5 pts [-9.5, +0.0] does not separate | 118/130 = 90.8% [80.5, 96.6] | 116/128 = 90.6% [80.2, 96.6] |
| FA-LOO (v5 vote) | 35/44 = 79.5% [64.4, 92.3] | 34/43 = 79.1% [65.2, 90.7] | 9 vs 9: +0 [-5, +4]; tasks 2:1, sign p = 1.000 does not separate | -0.5 pts [-8.6, +8.9] does not separate | 101/112 = 90.2% [79.4, 96.2] | 97/110 = 88.2% [76.5, 94.9] |
| (a) only | 35/44 = 79.5% [64.4, 92.3] | 34/45 = 75.6% [60.0, 88.6] | 11 vs 9: +2 [+0, +5]; tasks 2:0, sign p = 0.500 does not separate | -4.0 pts [-10.3, +1.1] does not separate | 100/112 = 89.3% [77.9, 95.6] | 97/110 = 88.2% [76.5, 94.9] |

- 8-view v5 minus 8-view P4: real +0.2 pts [-1.2, +1.9] does not separate; demo -4.4 pts [-10.0, -0.1] separates
- 8-view v5 minus 8-view FA-LOO + (c): real +8.9 pts [+0.6, +17.9] separates; demo -1.9 pts [-9.1, +5.4] does not separate
- 8-view P4 minus 8-view FA-LOO + (c): real +8.7 pts [+0.2, +17.9] separates; demo +2.5 pts [-3.9, +9.7] does not separate
- pass@2, 8 views minus 1 view: 60 vs 58: +2 [+0, +5]; tasks 2:0, sign p = 0.500 does not separate
- New wrong under 8-view v5: ['FilledNotFilled/FilledNotFilled1#1']
- Wrong at 1-view v5 no longer wrong at 8 views: ['CleanUp/CleanUp1#2', 'TopBottom3D/TopBottom3D8#1']
- Wrong under 8-view P4: ['CompleteShape/CompleteShape1#2', 'CompleteShape/CompleteShape7#1', 'CompleteShape/CompleteShape7#2', 'CompleteShape/CompleteShape9#1', 'FilledNotFilled/FilledNotFilled1#1', 'FilledNotFilled/FilledNotFilled9#2']
- Wrong under 8-view FA-LOO + (c): ['CleanUp/CleanUp1#2', 'CleanUp/CleanUp10#1', 'CompleteShape/CompleteShape1#2', 'CompleteShape/CompleteShape5#2', 'CompleteShape/CompleteShape7#1', 'CompleteShape/CompleteShape7#2', 'FilledNotFilled/FilledNotFilled1#1', 'FilledNotFilled/FilledNotFilled9#2', 'TopBottom2D/TopBottom2D6#1']
- 1-view v5 answers not answered at 8-view FA-LOO + (c): 14

## Test 4. By concept group

| Group | pass@2 /30 [CI] | Tasks solved /10 | Any candidate | Solving modules (items) | Kaggle 1st | Kaggle 2nd | GPT-4 T0 | Humans | Solved by Monty and Kaggle 1st |
|---|---|---|---|---|---|---|---|---|---|
| AboveBelow | 0 [0, 0] | 0 | 8 | - | 21 | 10 | 7 | 90% | 0 |
| Count | 0 [0, 0] | 0 | 0 | - | 18 | 12 | 4 | 88% | 0 |
| HorizontalVertical | 0 [0, 0] | 0 | 10 | - | 13 | 3 | 8 | 91% | 0 |
| InsideOutside | 0 [0, 0] | 0 | 2 | - | 17 | 3 | 3 | 91% | 0 |
| Order | 0 [0, 0] | 0 | 0 | - | 8 | 7 | 8 | 83% | 0 |
| SameDifferent | 1 [0, 3] | 1 | 7 | behavior 1 | 16 | 5 | 5 | 88% | 0 |
| Center | 2 [0, 5] | 2 | 9 | behavior 2 | 15 | 6 | 10 | 94% | 2 |
| TopBottom3D | 2 [0, 6] | 1 | 15 | behavior 2 | 18 | 1 | 6 | 93% | 1 |
| Copy | 3 [0, 9] | 1 | 10 | composition 3 | 7 | 8 | 7 | 94% | 3 |
| CleanUp | 5 [0, 12] | 3 | 8 | self-model 2, periodic 2, behavior 1 | 15 | 6 | 6 | 97% | 4 |
| ExtractObjects | 6 [0, 15] | 2 | 6 | composition 6 | 13 | 13 | 1 | 86% | 2 |
| FilledNotFilled | 6 [0, 14] | 3 | 10 | dynamics 5, behavior 1 | 22 | 13 | 5 | 96% | 6 |
| MoveToBoundary | 6 [0, 15] | 2 | 6 | dynamics 6 | 11 | 9 | 6 | 91% | 5 |
| CompleteShape | 7 [1, 15] | 4 | 18 | self-model 4, behavior 3 | 14 | 9 | 7 | 85% | 4 |
| ExtendToBoundary | 9 [0, 21] | 3 | 13 | dynamics 9, behavior 1 | 23 | 14 | 2 | 93% | 9 |
| TopBottom2D | 11 [2, 23] | 4 | 14 | composition 11 | 18 | 17 | 7 | 95% | 9 |
| **All** | 58/480 | | 136 | | 249 | 136 | 92 | 91% | 45 |
