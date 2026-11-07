**By number of demos, real role (post hoc).**

| n demos | Items | Tasks | FA-LOO + (c) | v5 | fit-only | pass@2 | Bound 1/(n+1) |
|---|---|---|---|---|---|---|---|
| 2 | 12 | 4 | 0/0 | 0/0 | 0/4 | 0 | 0.333 |
| 3 | 30 | 10 | 5/5 | 5/5 | 6/13 | 7 | 0.250 |
| 4 | 6 | 2 | 0/0 | 0/0 | 0/0 | 0 | 0.200 |

**v5 answers that FA-LOO + (c) does not give (real role), with the reason.**


**FA-LOO + (c) answers that v5 declines (real role), with the number of fully evidenced distinct answers.**


Both rules answer: 5 items, FA-LOO right 5, v5 right 5.

**Module alone: FA-LOO + (c) answers vs top answers at evidence >= 0.99 (real role).**

- self-model: 2 and 2, shared 2
- periodic: 0 and 0, shared 0
- behavior: 0 and 0, shared 0
- dynamics: 0 and 0, shared 0
- composition: 3 and 3, shared 3
- association: 0 and 0, shared 0
- pattern: 0 and 0, shared 0
- field: 0 and 0, shared 0

Sum of the modules' answers at evidence >= 0.99 vs the system's (a portfolio has them equal):
5/5 summed over modules; 5/5 = 100.0% [100.0, 100.0] system.

**Frames: paired precision differences at system level (secondary in the plan).**

- v5, canon minus abs: real +0.0 pts [+0.0, +0.0] does not separate; demo +0.0 pts [+0.0, +0.0] does not separate; dev +1.0 pts [+0.0, +3.4] does not separate
- v5, both minus canon: real +0.0 pts [+0.0, +0.0] does not separate; demo +0.0 pts [+0.0, +0.0] does not separate; dev -1.0 pts [-3.3, +0.0] does not separate
- v5, canon minus global: real +0.0 pts [+0.0, +0.0] does not separate; demo +0.0 pts [+0.0, +0.0] does not separate; dev +2.2 pts [+0.0, +5.6] does not separate
- v5, both minus no behaviour: real +0.0 pts [+0.0, +0.0] does not separate; demo +0.0 pts [+0.0, +0.0] does not separate; dev +0.2 pts [-2.8, +3.3] does not separate
- FA-LOO + (c), canon minus abs: real +0.0 pts [+0.0, +0.0] does not separate; demo +0.0 pts [+0.0, +0.0] does not separate; dev +0.0 pts [+0.0, +0.1] does not separate
- FA-LOO + (c), both minus canon: real +0.0 pts [+0.0, +0.0] does not separate; demo +0.0 pts [+0.0, +0.0] does not separate; dev -0.0 pts [-0.1, +0.0] does not separate
- FA-LOO + (c), canon minus global: real +0.0 pts [+0.0, +0.0] does not separate; demo +0.0 pts [+0.0, +0.0] does not separate; dev +0.1 pts [+0.0, +0.4] does not separate
- FA-LOO + (c), both minus no behaviour: real +0.0 pts [+0.0, +0.0] does not separate; demo +6.2 pts [+0.0, +25.0] does not separate; dev +1.1 pts [+0.0, +3.6] does not separate

**Evidence of the items solved by behaviour alone, per arm (real role).**

- canon: FilledNotFilledMinimal#0 ev 0.7 top right; FilledNotFilledMinimal#1 ev 0.7 top right
- abs: FilledNotFilledMinimal#0 ev 0.7 top right; FilledNotFilledMinimal#1 ev 0.7 top right
- both: FilledNotFilledMinimal#0 ev 0.74 top right; FilledNotFilledMinimal#1 ev 0.74 top right
- global: FilledNotFilledMinimal#0 ev 0.35 top right; FilledNotFilledMinimal#1 ev 0.35 top right; InsideOutsideMinimal#1 ev 0.37 top right; TopBottom2DMinimal#1 ev 0.3567 top right; TopBottom2DMinimal#2 ev 0.3567 top right

**Evidence of the arms' solves on development data (behaviour alone).**

- canon: 29 solves, evidence >= 0.99 in 13, zero in 7
- abs: 24 solves, evidence >= 0.99 in 11, zero in 5
- global: 2 solves, evidence >= 0.99 in 1, zero in 0

**Task-level recount, real role (a task counts once; right = every answered pair right).**

| Rule | Tasks answered | Tasks with a wrong answer | Tasks all right | Mean per-task precision |
|---|---|---|---|---|
| FA-LOO + (c) | 2 | 0 | 2 (CP [16, 100]%) | 100.0% |
| (a) only | 2 | 0 | 2 (CP [16, 100]%) | 100.0% |
| v5 | 2 | 0 | 2 (CP [16, 100]%) | 100.0% |
| fit-only | 8 | 7 | 1 (CP [0, 53]%) | 27.1% |
