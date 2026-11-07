**By number of demos, real role (post hoc).**

| n demos | Items | Tasks | FA-LOO + (c) | v5 | fit-only | pass@2 | Bound 1/(n+1) |
|---|---|---|---|---|---|---|---|
| 1 | 3 | 1 | 0/0 | 0/0 | 0/0 | 0 | 0.500 |
| 2 | 225 | 75 | 13/19 | 17/22 | 17/30 | 25 | 0.333 |
| 3 | 183 | 61 | 12/12 | 11/11 | 10/26 | 13 | 0.250 |
| 4 | 66 | 22 | 7/10 | 11/13 | 13/15 | 17 | 0.200 |
| 5 | 3 | 1 | 3/3 | 3/3 | 3/3 | 3 | 0.167 |

**v5 answers that FA-LOO + (c) does not give (real role), with the reason.**

- CompleteShape/CompleteShape9#1: (a), v5 wrong, n = 2, top from ['self-model']
- ExtendToBoundary/ExtendToBoundary5#0: (a), v5 right, n = 4, top from ['dynamics']
- ExtendToBoundary/ExtendToBoundary5#1: (a), v5 right, n = 4, top from ['dynamics']
- ExtendToBoundary/ExtendToBoundary5#2: (a), v5 right, n = 4, top from ['behavior', 'dynamics']
- ExtractObjects/ExtractObjects3#0: (a), v5 right, n = 2, top from ['composition']
- FilledNotFilled/FilledNotFilled9#0: (a), v5 right, n = 4, top from ['dynamics']
- FilledNotFilled/FilledNotFilled9#1: (a), v5 right, n = 4, top from ['dynamics']
- MoveToBoundary/MoveToBoundary3#0: (a), v5 right, n = 2, top from ['dynamics']
- MoveToBoundary/MoveToBoundary3#1: (a), v5 right, n = 2, top from ['dynamics']
- MoveToBoundary/MoveToBoundary3#2: (a), v5 right, n = 2, top from ['dynamics']
- MoveToBoundary/MoveToBoundary4#0: (a), v5 right, n = 2, top from ['dynamics']

**FA-LOO + (c) answers that v5 declines (real role), with the number of fully evidenced distinct answers.**

- CleanUp/CleanUp10#1: FA-LOO wrong, fully evidenced answers 2, top evidence 1.0, from ['periodic'], n = 2
- CompleteShape/CompleteShape5#2: FA-LOO wrong, fully evidenced answers 4, top evidence 1.07, from ['behavior'], n = 2
- ExtractObjects/ExtractObjects1#2: FA-LOO right, fully evidenced answers 2, top evidence 1.05, from ['composition'], n = 3
- ExtractObjects/ExtractObjects3#1: FA-LOO right, fully evidenced answers 4, top evidence 1.04, from ['composition'], n = 2
- TopBottom2D/TopBottom2D1#1: FA-LOO right, fully evidenced answers 0, top evidence 0.7725, from ['composition'], n = 4
- TopBottom3D/TopBottom3D8#2: FA-LOO wrong, fully evidenced answers 2, top evidence 1.05, from ['behavior'], n = 4

Both rules answer: 38 items, FA-LOO right 32, v5 right 32.

**Module alone: FA-LOO + (c) answers vs top answers at evidence >= 0.99 (real role).**

- self-model: 9 and 9, shared 9
- periodic: 4 and 4, shared 4
- behavior: 6 and 6, shared 6
- dynamics: 18 and 18, shared 18
- composition: 17 and 17, shared 16
- association: 0 and 0, shared 0
- pattern: 0 and 0, shared 0
- field: 0 and 0, shared 0

Sum of the modules' answers at evidence >= 0.99 vs the system's (a portfolio has them equal):
44/54 summed over modules; 44/54 = 81.5% [69.0, 91.9] system.

**Frames: paired precision differences at system level (secondary in the plan).**

- v5, canon minus abs: real -1.0 pts [-5.0, +1.8] does not separate; demo +1.4 pts [-1.6, +6.1] does not separate; dev +1.0 pts [+0.0, +3.4] does not separate
- v5, both minus canon: real +0.0 pts [+0.0, +0.0] does not separate; demo -0.9 pts [-4.0, +1.7] does not separate; dev -1.0 pts [-3.3, +0.0] does not separate
- v5, canon minus global: real -1.0 pts [-5.0, +1.8] does not separate; demo +2.8 pts [-1.9, +10.0] does not separate; dev +2.2 pts [+0.0, +5.6] does not separate
- v5, both minus no behaviour: real -1.0 pts [-5.0, +1.8] does not separate; demo -2.0 pts [-5.7, +0.7] does not separate; dev +0.2 pts [-2.8, +3.3] does not separate
- FA-LOO + (c), canon minus abs: real -4.5 pts [-12.5, +0.0] does not separate; demo +1.3 pts [-1.5, +5.5] does not separate; dev +0.0 pts [+0.0, +0.1] does not separate
- FA-LOO + (c), both minus canon: real -1.3 pts [-5.0, +0.0] does not separate; demo -0.8 pts [-3.2, +0.0] does not separate; dev -0.0 pts [-0.1, +0.0] does not separate
- FA-LOO + (c), canon minus global: real -3.8 pts [-12.0, +1.9] does not separate; demo -1.6 pts [-6.7, +2.6] does not separate; dev +0.1 pts [+0.0, +0.4] does not separate
- FA-LOO + (c), both minus no behaviour: real -7.7 pts [-17.3, -1.2] separates; demo -1.8 pts [-8.1, +3.3] does not separate; dev +1.1 pts [+0.0, +3.6] does not separate

**Evidence of the items solved by behaviour alone, per arm (real role).**

- canon: Center/Center1#0 ev 0.615 top right; Center/Center9#0 ev 0.0 top right; CleanUp/CleanUp5#2 ev 0.0 top right; CompleteShape/CompleteShape5#0 ev 1.29 top right; CompleteShape/CompleteShape5#1 ev 1.29 top right; CompleteShape/CompleteShape6#0 ev 0.0 top wrong; ExtendToBoundary/ExtendToBoundary5#2 ev 0.6 top right; FilledNotFilled/FilledNotFilled10#2 ev 0.0 top right; SameDifferent/SameDifferent1#1 ev 0.0 top right; TopBottom3D/TopBottom3D8#0 ev 1.16 top right; TopBottom3D/TopBottom3D8#2 ev 1.05 top wrong
- abs: Center/Center1#0 ev 0.615 top right; Center/Center9#0 ev 0.0 top right; ExtendToBoundary/ExtendToBoundary5#2 ev 0.6 top right; FilledNotFilled/FilledNotFilled10#2 ev 0.0 top right; TopBottom3D/TopBottom3D8#0 ev 0.7925 top right
- both: Center/Center1#0 ev 0.735 top right; Center/Center9#0 ev 0.0 top right; CleanUp/CleanUp5#2 ev 0.0 top right; CompleteShape/CompleteShape5#0 ev 1.29 top right; CompleteShape/CompleteShape5#1 ev 1.29 top right; CompleteShape/CompleteShape6#0 ev 0.0 top wrong; ExtendToBoundary/ExtendToBoundary5#2 ev 0.705 top right; FilledNotFilled/FilledNotFilled10#2 ev 0.0 top right; SameDifferent/SameDifferent1#1 ev 0.0 top right; TopBottom3D/TopBottom3D8#0 ev 1.21 top right; TopBottom3D/TopBottom3D8#2 ev 1.05 top wrong
- global: FilledNotFilled/FilledNotFilled10#2 ev 0.0 top right; HorizontalVertical/HorizontalVertical7#2 ev 0.6733 top right; InsideOutside/InsideOutside4#1 ev 0.5475 top right; SameDifferent/SameDifferent1#2 ev 0.0 top right; SameDifferent/SameDifferent4#1 ev 0.0 top right

**Evidence of the arms' solves on development data (behaviour alone).**

- canon: 29 solves, evidence >= 0.99 in 13, zero in 7
- abs: 24 solves, evidence >= 0.99 in 11, zero in 5
- global: 2 solves, evidence >= 0.99 in 1, zero in 0

**Task-level recount, real role (a task counts once; right = every answered pair right).**

| Rule | Tasks answered | Tasks with a wrong answer | Tasks all right | Mean per-task precision |
|---|---|---|---|---|
| FA-LOO + (c) | 18 | 7 | 11 (CP [36, 83]%) | 76.9% |
| (a) only | 18 | 7 | 11 (CP [36, 83]%) | 76.9% |
| v5 | 19 | 6 | 13 (CP [43, 87]%) | 85.1% |
| fit-only | 37 | 20 | 17 (CP [29, 63]%) | 51.4% |
