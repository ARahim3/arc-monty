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

### Table 12. Where v5 and FA-LOO + (c) disagree about answering (real role; post hoc, descriptive)

| Dataset | Both answer: right/n | v5 only: right/n | FA-LOO + (c) only: right/n |
|---|---|---|---|
| Development (1,147) | 91/92 | 5/6 | 10/10 |
| ConceptARC | 32/38 | 10/11 | 3/6 |
| Mini-ARC | 8/8 | 3/3 | 0/1 |
| 1D-ARC | 158/169 | 9/9 | 3/3 |
| Three unseen sets pooled (stratified cluster bootstrap) | 198/215 | 22/23 [83, 100] | 6/10 [22, 90]; v5 only minus FA-LOO only +35.7 [+2.1, +75.0] |

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
