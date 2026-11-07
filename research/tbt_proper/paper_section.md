### What the Thousand Brains Theory lets ARC test

*Draft to replace Sections 6.4, 6.5 and Appendix D of `research/paper/v8/paper.md`.*

**Movement and voting cannot show on these grids.** Let each hypothesis predict every cell. A column that has read some cells keeps the hypotheses agreeing on them. A vote passes surviving sets, so columns end with those agreeing on the union of cells read: exactly what one column would hold had it read them all. On exact, fully visible grids, where reading is free, movement and voting change the number of steps, never the answer. Our voting null therefore says nothing about the theory. Segmentation by coalitions of columns is not covered, and we did not score it.

**A separate test of what can fail.** We built a new program, not Monty: one column class and one matching rule, in 42 copies differing only in sensor and reach, frozen with a hash before any test data. Games are the 13 held-out ARC-AGI-3 games, as recordings; there an action is a real movement. There are 17 primary comparisons, uncorrected. * marks theory-specific claims.

| Claim | Difference, points or solves [95% CI] | Against its falsifier |
|---|---|---|
| Needs the motor signal | +35.8 [+22.2, +50.2] | Holds, near trivial |
| Beats our modules as a world model | +24.1 [+14.7, +34.6] | Holds |
| Beats a repeat rule | +19.5 [+7.9, +33.7] | Holds |
| Rollout beats unchanged frame, 4 steps | +11.3 [−0.8, +25.4] | No separation |
| Moving frame* | +1.1 [0.0, +3.4] | No separation; one game |
| Nearest-object frame* | +2.9 [−0.2, +7.0] | No separation |
| Behaviour in its own frame* | −2.4 [−7.0, +1.2] | Fails |
| Covers the modules' ground | 19 vs 9; 145 vs 139 | Supports |
| Object sensors* | +3 [0, +7]; +10 [+1, +25] | Fails; holds on 4 of 50 types |
| Count sensor* | +4 [0, +10] | Fails |
| Held-out split, trust rule | +80.4 [+62.4, +93.1]; +66.7 [+41.2, +82.3] | Holds |
| Same, within a task | +53.7 [+14.1, +88.9]; +4.4 [−3.3, +12.7] | Second does not separate |
| Memory, same concept* | −11 [−29, +3] | Fails |
| Memory, other games* | −2.3 [−3.9, −0.8] | Fails |

Game rows are changed transitions, CI by game. Paired static rows give hand-made fresh sets, then a generated set.

**Reading.** One repeated algorithm is a real learner. It predicts what changes better than our eight modules, and on unseen, easier sets it matches their solve count, on largely different tasks (5 and 36 shared). That is not a new solver: it answers far more often at low precision, and on the new ARC-AGI-2 tasks it solved 1 of 233 (development). The motor signal and local context do the work. Frames, behaviours, counting and memory add nothing we could separate. These nulls concern this implementation, and they do not refute the theory, whose neuroscience ARC cannot test.

---

**Two-line fallback.** On exact, fully visible grids, movement and voting can change only how many steps a system takes, never its answer, so ARC-AGI-1/2 cannot test them. A frozen one-algorithm column, separate from Monty-ARC, predicted held-out ARC-AGI-3 frames better than our modules (+24.1 points [+14.7, +34.6]), but frames, behaviours, counting and persisting models added nothing we could separate.
