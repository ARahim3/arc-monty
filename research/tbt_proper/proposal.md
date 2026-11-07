# Testing the Thousand Brains Theory itself on ARC: design and feasibility

Written 2026-11-01 by the TBT expert agent. Design study only; nothing here is a paper result. Every number marked SPIKE comes from small throwaway scripts on development data, chosen after looking at that data. Not opened: ConceptARC, Mini-ARC, 1D-ARC and `re-arc` tasks, the 13 held-out ARC-AGI-3 games (neither code nor recordings), and the task files of the candidate fresh sets in §3. No third-party code was run. Spikes and raw results are in `research/tbt_proper/spikes/`.

## 0. The answer

**Can we try the theory itself? In part, and the part that matters most is not on ARC-AGI-2.**

- **ARC cannot test TBT as neuroscience** (grid cells, cortical layers, the thalamus). It can test what the theory's authors say a system built this way should do.
- **On ARC-AGI-1/2, movement and voting cannot show anything.** The grid is exact, fully visible and free to read. A short proof (§2.1) shows that they can only change how many steps a system takes, never its answer. The reviewer is right that we didn't test them, and nobody can on these tasks.
- **Three claims can be tested on static tasks:** one repeated algorithm, objects as features of objects, and models that persist across tasks.
- **Movement can be tested only on ARC-AGI-3,** where an action is a real movement with a cost. There the claim becomes: a column learns to predict the next input given the action. Goal inference has to stay out, because the theory has no account of it yet.
- **Best experiment (E1):** one generic column, one code path, frozen once, run on unseen data from both ARCs, with each mechanism as a switch. About 10–14 agent-hours, CPU only, feasible by 11-06.
- **Likely outcome (SPIKE):** the motor signal matters hugely, and that part is close to trivial. One column predicts changed frames better than our eight modules. It does not clearly beat a simple repeat rule. Reference frames, behaviour-in-own-frame and persisting models add nothing on the games. On static tasks it reaches about a quarter of the eight modules' solves on the harder sets; object-level input adds a little on ARC-AGI-1 tasks (7 to 12 on public eval) and nothing on the new ARC-AGI-2 tasks.
- **This would not be a new way to solve tasks.** It solves 0 of 120 on ARC-AGI-2 public eval. It is a test of the theory, and a small new learner for the trust rule.

## 1. What TBT actually claims

Sources: H19 = Hawkins, Lewis, Klukas, Purdy, Ahmad, *Frontiers in Neural Circuits* 2019. C24 = Clay, Leadholm, Hawkins, arXiv:2412.18354. L25 = Leadholm et al., arXiv:2507.04494, *Neural Computation* 2026. H25 = Hawkins, Leadholm, Clay, arXiv:2507.05888v2 (now titled "The Thousand Brains Theory 2.0"). Docs = `external/tbp.monty/docs`. "Real Monty" = tbp.monty 0.55 as read in `research/monty_code_notes.md`.

| # | Mechanism | The claim, in their words | Monty-ARC v5 | Real Monty |
|---|---|---|---|---|
| 1 | Learning through movement, path integration | "The location representation is updated via a motor efference copy and path integration" (H19). "Although learning objects requires movement of the sensors, inference often occurs without movement" (H19) | No. Sees whole grids, no movement | Yes: displacement moves each hypothesis (`hypotheses_displacer.py:141-155`). Explicit coordinates; no grid cells yet (Docs FAQ) |
| 2 | Next-sensation prediction | "Successful models are ones that can predict the next input given the current state and an anticipated movement" (H19). "visual regions cannot understand or predict the next retinal input without knowing how the eyes are moving" (H25) | No. Leave-one-out over demos is cross-validation | Yes, for sensor movement |
| 3 | Features at locations in a reference frame | "An object is not just a bag of features. It is a collection of features at locations" (C24) | Partly: `behavior.py` stores output changes at locations in a D8-canonical object frame. The frame is computed by hand-written code, not learned through movement | Yes: `GridObjectModel`. Euclidean space is given |
| 4 | One repeated algorithm | "Core to its design is the use of a repeating computational unit" and "each using the same input and output interface" (C24). Mountcastle: "all regions of the neocortex are fundamentally the same" (H19). "The columns are agnostic to what type of input goes to L4" (Docs, object-behaviors) | No. Eight enumerators with no shared input format | Yes in practice. TBP's software allows other kinds if they speak the protocol: "There can be many types of learning modules as long as they adhere to the messaging protocol" (Docs FAQ) |
| 5 | Voting across columns on object and pose | Columns reach "consensus based on having observed different parts of an object"; "not simply a 'bag-of-features' operation" (L25, C24). "Monty is able to leverage voting, but is not dependent on it" (L25) | No. Identical answers pool across different modules; no pose, no parts | Yes (`evidence_matching/model.py:39-113`) |
| 6 | Model-based policy that moves to disambiguate | "use the most likely hypotheses to propose a goal state that would disambiguate them" (L25). Their effect is small: "accuracy 96.4% with vs. 95.6% without; median steps to convergence 28 with vs. 30 without" (L25) | Analogy only: attempt 2 is the strongest disagreeing answer | Yes for sensor moves, not for changing the world. Forum transcript, vclay: no current policy interacts with an object "to figure out how it works" |
| 7 | Hierarchy: objects as features | "the role of the hierarchical connections between columns is to learn compositional models" (H25). "use the recognized model ID as a feature in its own models" (C24) | No. `composition.py` is panels, select, tile, down | Bottom-up only, supervised, oracle sprite labels in the ARC fork. COWS small 28.95% compositional vs 35.71% monolithic; "not currently expected to have good performance" (`benchmarks/`, Docs) |
| 8 | Behaviours as models of change | "behavior models are sequences of changes at locations"; "it exists independently of the stapler" (Docs). Marked "relatively fresh", not in a journal | Partly: one-step changes in an object frame, in `behavior.py` | Not implemented: change-detecting sensor "open", behaviour test bed "paused" |
| 9 | Continual learning, models persist | "only this representation... other learned representations remain unaffected" (L25, 77 objects learned in sequence) | No. Every task learns alone | Yes for recognition. Generalising to new instances is listed under "Further Capabilities That we Are Currently Working On" |

**The theory stops short of what ARC-AGI-3 needs.** Docs on behaviours in action: "4 and 5 still have many unresolved questions". Vclay on inferring goals (forum transcript): "we have the most uncertainty about" it. Causality is a one-line idea from Hawkins in that talk ("a linking of two behaviors"). So anything we build for causal learning or goals is our invention, and a result on it would not be a test of TBT.

**TBP's own plan for ARC fixes the rule for a faithful test.** Forum transcript, Hawkins: "we shouldn't change the basic learning module at all"; sensors and actuators may change. So a faithful system has one column class, and only its sensors differ.

## 2. What can be tested on ARC at all

### 2.1 Static grids: movement and voting cannot show

**Proposition (exact data).** Let each hypothesis predict every cell of the grid, for example a model placed at a pose and offset. A column that has read the cells in P keeps exactly the hypotheses that agree on P. A vote passes surviving sets, so after voting the columns hold the intersection over their paths, which is the set agreeing on the union of the cells read. That is what one column would hold if it had read all those cells itself. So the survivors depend only on which cells were read. A full view gives the smallest possible survivor set in one step. Movement and voting can therefore change only speed. On ARC reading a cell costs nothing, so speed is worth nothing.

SPIKE, `spike_vote_equals_pool.py`, 480 trials, single objects from 60 ARC-AGI-1 training grids, median 100 cells. Vote equalled pooling after every step of every trial, by assertion. More sensors cut steps and not cells read. A hypothesis-driven read saves cells over a random walk, as any "twenty questions" would.

| Median to identify the placement | 1 sensor | 2 | 4 | 8 | Full view |
|---|---|---|---|---|---|
| Random walk: steps / cells read | 20 / 20 | 15.5 / 31 | 8.5 / 34 | 5 / 40 | 1 / 100 |
| Hypothesis-driven: steps / cells read | 15.5 / 15.5 | 7 / 14 | 3 / 12 | 2 / 16 | 1 / 100 |

**What the proposition does not cover.** It assumes one object explained whole. With several objects, a coalition of columns agreeing on one placement is a form of segmentation, which is a real use of voting and is not the same as pooling. I see no way to score that by 11-06, because there is no ground truth.

**The authors agree.** L25 calls the design a deliberate rejection of "the false assumption that all useful information can be simultaneously perceived". On ARC-AGI-1/2 that assumption is true. The Docs say Monty "is not designed to learn from static datasets". Vclay on ARC (forum transcript): "we can just process the whole image at every frame", and voting isn't needed. And H19 lets inference run without movement, so a whole-grid view does not contradict the theory. Static grids neither support nor refute the movement claim.

**Two ways of rescuing it, both rejected.**
- *An imposed aperture* (read only a patch, pay per cell). This makes a cost we invented, and the table above already gives the answer: active reading beats a random walk on exact data, for reasons that have nothing to do with TBT.
- *"Thinking is movement in concept space."* The theory allows it (H19: inputs and movements "do not have to correspond to physical entities"), but any program search then counts as movement. That is the label trap the reviewer named.

### 2.2 ARC-AGI-3: where the claim becomes real, and where it does not

- **Not real: sensor movement.** The whole 64×64 frame arrives free on every step. A text search of the 12 tuning games' code finds a camera position write in only one game (`bp35`). So tracking a sensor by path integration has almost nothing to do.
- **Real: an action is a movement with a consequence and a price.** Score is `(baseline/actions)^2` per level. "Predict the next input given an anticipated movement" is now a claim that can fail, and hypothesis-driven action has a real cost to save.
- **Out of bounds: goals and causal links** (§1). So levels and score cannot be the primary outcome. Our past tests measured score, and goal inference swamped them (`research/arc3_world_model.md`, `research/arc3_agent_v7.md`: predict-and-halt held on 81% of planned steps, yet the held-out score fell). The outcome here has to be prediction per action.

### 2.3 Summary

| Claim | ARC-AGI-1/2 | ARC-AGI-3 |
|---|---|---|
| Movement, voting, sensor policy | Cannot show (§2.1) | Sensor side: no. Action side: yes (E1, E3) |
| Next sensation given movement | No movement exists | Yes (E1) |
| One repeated algorithm | Yes (E1) | Yes, the same code (E1) |
| Frames, objects as features | Yes (E1) | Yes (E1) |
| Behaviours in their own frame | Weakly: one step only | Yes (E1) |
| Persisting models | Yes (E2) | Yes (E2) |
| Goals, causality | Theory unfinished | Theory unfinished |

## 3. Candidate experiments

### E1. One column, frozen once, on unseen data from both ARCs (recommended)

**System.** One `Column` class, about 300 lines, new, under `research/tbt_proper/`. It stores what is sensed next, at a location or context, with counted evidence along a path. Only sensors differ: cell colour, shape without colour, child object ID at a location in the child's frame, location in the nearest object's canonical frame, and action. There is no branch by task family. "Next sensation" means the output cell on static tasks and the next frame's cell on games. This turns the existing behaviour idea into the theory's stated form, using one code path.

**Known gap to close first.** The spike used two matching rules: counted evidence on static tasks and longest-context hashing on games, for speed. "One algorithm" is false until these are one rule. This is the first build step, and it may move the numbers below.

**Exact claims and what would falsify them.** Theory-specific items are marked *.

| Arm | Claim | Comparison, all paired | Fails if | SPIKE |
|---|---|---|---|---|
| M1 | A column needs the motor signal | Column vs itself told nothing about the action; changed transitions | Loss under 5 points, or CI includes 0 | −24.9 [−40.5, −11.1] |
| M2 | One column can replace eight modules as a world model | Column vs Monty-ARC columns, changed transitions | CI includes 0 or favours Monty-ARC | +19.1 [+9.7, +31.6] |
| M3 | It adds something beyond a simple rule | Column vs object-relative repeat | CI includes 0 | +11.4 [−0.2, +28.5] |
| M4* | A location in a reference frame adds prediction | Moving frame and nearest-object frame vs local context | Upper CI bound under +3 points | −2.9 [−7.3, +1.2]; −2.3 [−8.7, +3.5] |
| M5* | Behaviour in the column's own frame adds prediction | Displacement form vs colour-only form of next sensation | Upper CI bound under +3 points | −3.3 [−6.6, −0.6] |
| M6 | Integrating actions with no new sensation holds up | Open-loop rollout vs unchanged frame, horizons 2, 4, 8 | Below baseline at horizon 4 | 53.7 vs 48.7; 35.4 vs 33.8; 19.2 vs 21.7 |
| S1 | One algorithm covers the ground of eight | Column / Monty v5 pass@2 on the same tasks | Ratio under 0.25. Supports if at least 0.5 with its lower bound above 0.25; otherwise inconclusive | 0.55, 0.26, 0.26, 0 (§6) |
| S2* | Objects as features or frames add solves | Cell-level sensors only vs all sensors, two attempts each | CI by task includes 0 | +5.0 [+1.0, +10.0] on ARC-1 eval; +7.5 [+2.0, +14.0] on ARC-1 train; 0 [−3, +3] on new233 |
| S3 | Counting as a walk along a 1-D frame helps | With and without the count sensor; six weak ConceptARC groups, baseline 1 of 180 | No separation from 1 of 180 | Adds 0 on every development split |
| S4 | The trust rule holds on a fourth learner | FA-LOO vs fit, as in the paper's Table 5 | Held-out split doesn't separate | Top answer at LOO 1: 26/30, 4/7, 1/3, 0/0 |

**What a failure means.** A failure on M4, M5, S2 or S1 means this mechanism does not earn its place on this benchmark in this column. It does not refute the theory. A null is weak evidence against a theory that can blame the implementation, and only a success says much. TBP could also fairly say M4 and M5 are a poor place to look, because game sprites rarely change pose. The static arm is where pose varies.

**Data and freshness.**
- *Games:* the 13 held-out games, 3,120 recorded main transitions already on disk, read as data, so **no game code needs to run**. Comparators for the same transitions already exist in `research/arc3_wm/results/`. This column has never seen them. The project has (v7, v8, world-model probe), and the plan must say so.
- *Static, truly fresh:* human-made sets from `neoneye/arc-dataset-collection` (public, JSON): `arc-community`, `arc-dataset-tama`, `nosound`, `dbigham`, `Sequence_ARC`; possibly `IPARC` and `PQA`. I listed folder names only. Licence, size, quality and pair overlap with all earlier sets still need checking. Frozen Monty v5 and the column both see them for the first time, which also gives Monty-ARC a new clean row.
- *Static, spent but usable:* ConceptARC, Mini-ARC and 1D-ARC with the plan fixed first. The column has never run on them, but we know Monty's aggregate results, including that six groups give 1 of 180. Disclose that this motivated the count sensor. No sensor may be added after this proposal for that reason. `re-arc` could add a fourth learner to the bound test after the generator agent reports; its concepts are development tasks here, so it cannot count for S1.
- *Development only:* ARC-AGI-1 train and eval, ARC-AGI-2 eval and new233, and the 12 tuning games.

**Effort and compute.** Unify matching, write the plan, freeze: 5–7 agent-hours. Fresh sets and overlap check: 1–2. Runs: 1. Analysis and report: 3–4. **Total 10–14.** CPU only, at most 4 workers: about 3 s per static task, a few minutes per arm on the games. No TPU, no Kaggle, no third-party code, `arcmonty/` only imported read-only.

**Likely result, honestly (my judgement).** M1 passes (near certain, and near trivial). M2 passes (likely). M3 does not separate with 13 games (likely). M4 and M5 show no gain (more likely than not), and the gains in M2 and M3 may come from a few games again: in the spike `ls20`, `sc25` and `su15`. S1 lands around 0.25–0.4, so inconclusive or a narrow fail. S2 small and positive on ARC-AGI-1-style sets, absent on ARC-AGI-2-style tasks (likely). S3 fails (likely). Roughly one chance in seven that frames or behaviours show a real gain on games.

**What the paper gets either way.**
- *Most likely result:* "We built what the theory describes. One column is a real learner and beats our eight modules at predicting what changes, but it does not replace them on static tasks. On games the motor signal and context length do the work, and the theory's distinctive machinery adds nothing we can measure. Object-level input helps a little on the easier static tasks." A clear statement of which parts earn their keep.
- *Frames or behaviours help (unlikely):* the first evidence for those claims on a benchmark built by someone else, and a real lead for the section.
- *The column is a toy (M2 and S1 fail):* keep the proposition, report the attempt in two lines, and TBT goes back to being motivation. Nothing in the paper breaks, since all of this is a separate system.

### E2. Persisting models (cheap add-on to E1)

- **Claim.** Models learned on earlier tasks help on a new task of the same kind (claim 9 in §1).
- **Falsifier.** Same-concept memory is no better than learning alone: CI by concept group includes 0 or is negative.
- **Comparison.** One column, three arms, leave one task out on ConceptARC's ten tasks per concept: alone; library from the other concepts; library from the same concept. The second arm separates transfer of a concept from generic bulk. On games: library from the other games, leave one game out.
- **Data.** ConceptARC with the plan fixed first; the 13 held-out games.
- **Effort.** 3–4 agent-hours after E1, under an hour of CPU.
- **Likely result.** Null or negative. SPIKE, games: the library lowers exact prediction by 1.7 points [−2.4, −1.0], and at first use of an action gives 16.1% against 55.9% for no library (n = 93). On those 93, the 41 where anything changed got 0 right in both arms. SPIKE, static: an exact-context library from 400 ARC-AGI-1 training tasks changes nothing on 202 evaluation tasks (3.0 vs 3.0), answering on average 3.9 cells a task. Exact features at locations do not carry. Transfer needs categories, which TBP itself lists as unfinished. ArcMemo (arXiv:2509.04439) gets a 7.5% relative gain with an LLM's concept notes, which is a useful contrast.
- **Paper.** One line and one number. A clean test across tasks, which nothing in our paper has. A negative here would say something the theory's own roadmap predicts.

### E3. Hypothesis-driven action on ARC-AGI-3 (only if E1 lands by 11-04)

- **Claim.** Acting where the top two hypotheses disagree identifies a game's mechanics in fewer actions. This extends the policy of §1 row 6 from sensors to the world, which vclay says Monty does not do.
- **Falsifier.** It does not beat random, "take the action predicted to change most" and our v3 explorer's action choices on the area under the learning curve.
- **Comparison.** Same column learning from each policy's actions: disagreement, largest predicted change, random, and v3's explorer (dead signatures). 1,000 actions, 3 seeds. Outcome: prediction on a fixed battery of state-action pairs that no policy sees, so goals play no part. Levels and score are reported as secondary.
- **Data.** 13 held-out games, live. This needs the official `arc_agi` toolkit, already installed and used in this project since 10-29 (`research/arc3_wm/.venv`). It is third-party code, so the lead should clear it.
- **Effort.** 8–12 agent-hours, 1–2 hours of CPU on 4 workers.
- **Likely result.** Beats random, ties the simple heuristic. SPIKE, 120 recorded probe states: disagreement picks an action that surprises the model 55.0% of the time, random 40.3% (+14.7 [+2.4, +28.5]), largest predicted change 51.7% (+3.3 [−7.5, +19.2]). Most of that is avoiding no-ops, which `research/arc3_agent.md`'s dead signatures already do. TBP's own effect is under one point.
- **Paper.** A first test of model-based action in a world with a price on actions. A win over random alone proves little.

### E4. A check against real Monty (optional; needs the user's yes)

- **Claim.** Our column agrees with Monty's `EvidenceGraphLM` on what it recognises, on exact ARC objects.
- **Comparison.** Drive the real learning module with hand-made messages, as its unit test does (`tests/unit/frameworks/models/evidence_matching/evidence_lm_test.py:79-125`, D8 as a rotation list, colours exact). Same objects, same poses, against the exact column. Falsifier: disagreement beyond timeouts. The proposition predicts agreement, with Monty slower.
- **Needs.** Running third-party code in a separate environment: torch, torch_geometric, numpy-quaternion, scipy, scikit-learn, Python as the repo requires; a throwaway VM or new venv. MIT licence.
- **Effort.** 3–6 agent-hours.
- **Paper.** It answers "no Monty code runs at all" with one honest sentence. It solves nothing and tests no claim: Monty has no output generation and no rule learning, so **real Monty cannot be the ARC solver**, and TBP's own fork says "No policy tries to win a game yet". I would run it only if a judge's objection on this point seems serious.

### Considered and rejected

| Idea | Why not |
|---|---|
| Real voting on static grids, vote vs pooling | Equal by proof and in 480 trials (§2.1). Only steps change, and steps cost nothing |
| Moving sensor or aperture on static grids | A cost we invented, with a known answer (§2.1) |
| Path integration as sensor tracking on ARC-AGI-3 | The full frame is free, and the camera is written in 1 of 12 tuning games. The open-loop rollout (M6) is the meaningful version |
| Hierarchy as its own experiment | Same column; a switch inside E1 (S2, S3). A separate relation module would repeat the reviewer's objection |
| TBP's fork as is (game classification, sprite maps) | It reports recognition with oracle labels, which is no test of a claim. It also needs Python 3.13 and third-party code |
| Levels or score as the primary outcome | Dominated by goal inference, on which the theory has nothing yet |

## 4. Recommendation

**Run E1, with E2 as its add-on. Hold E3 and E4 unless E1 is done by 11-04 and the user wants them.**

Why E1. It is the only design that answers the reviewer's objections in one go: a single repeated algorithm, prediction of the next sensation given a movement, and a clear statement on voting. The data is ready and the cost is low. A bad result does no harm because it's a separate system. And the spike shows it gets off the ground.

**Schedule (UTC).** Plan and freeze by 12:00 11-03, with plan section 0 written before any test run and the code hash recorded. Runs on 11-03. Report by 12:00 11-04, or 11-05 at the latest. That leaves the writer time before 11-09, and the Mac can do all of it. **Stop rule:** if not frozen by 12:00 11-04, drop E1 and keep the proposition and a short honest note.

**Would it solve tasks others can't?** I see no evidence for that. It reaches some tasks Monty-ARC doesn't (23, 5 and 3 tasks on the three splits where it solves any), and I did not compare those with the 2020 program or Qwen on these splits. On ARC-AGI-2 public eval it solves 0 of 120 with no confident answer, against Monty-ARC's 4, Qwen's 32.7 of 120 from its verified programs (one sampling run) and 2 of 160 test pairs for the 2020 program. Past Paper Award winners offered a new way to solve tasks; this isn't one. Its value is that it is a real test of the theory, the first number from a column built to the theory's description on either ARC as far as I can find, and an extra learner under the trust rule with premise (F) clean. Any gain on the rubric would come through Theory and Novelty, not Accuracy or Progress.

**The proposition is worth keeping whatever happens.** It costs nothing and turns "voting was barely exercised, little power" (§6.5 of v8) into "this cannot show on these tasks, and here is why".

## 5. What would change in the paper

- **Title and lead stay as the user chooses;** the trust question remains the main story. Title wording is decided later.
- **"Tested" gets narrower and truer.** After E1 the paper may claim: we tested one repeated algorithm, objects as features, reference frames, and next-sensation prediction, in a column built to the theory's description, on unseen ARC data. It still may not claim "we tested the Thousand Brains Theory" or that anything confirms or refutes it, and it must say no Monty code runs (unless E4 is done).
- **Structure.** One new section of at most about 400–500 words with one table replaces §6.4, most of §6.5 and Appendix D, and rewrites the "What this test can and cannot say" paragraph of §3. The second judge asked for one story and about 4,500 body words, and v8 is well over that, so this must not add net length. If E1 ends badly, a two-line note and the proposition replace those parts.
- **Risk.** A judge may still prefer less TBT overall. That is a fair worry and the reason this is the user's call.

## 6. Spike results (development data, exploratory)

**One column on static tasks** (`spike_counted.py`, `results/column_summary.txt`). Same-size tasks plus simple resampled output frames. All-or-nothing context matching solved 1.5 of 60, so I moved to counted evidence. Sensors were added after looking at 100 ARC-AGI-1 training tasks, so that row is flattered. Monty v5 was developed on all of these. 2 to 3 CPU-seconds per task.

| Split | Tasks | Column | Monty v5 | Ratio | Both | Column only | Monty only | Top answer at LOO 1 |
|---|---|---|---|---|---|---|---|---|
| ARC-AGI-1 train | 400 | 44.3 | 80 | 0.55 | 23.0 | 23 tasks | 57 | 26/30 |
| ARC-AGI-1 eval | 400 | 12.0 | 46 | 0.26 | 8.0 | 5 | 38 | 4/7 |
| ARC-AGI-2 new233 | 233 | 2.3 | 9 | 0.26 | 0 | 3 | 9 | 1/3 |
| ARC-AGI-2 eval | 120 | 0 | 4 | 0 | 0 | 0 | 4 | 0/0 |

Sensors as a switch, same column, two attempts in every arm, CI by task:

| Split | Cells only | + object ID | + object frame | + count | All minus cells |
|---|---|---|---|---|---|
| ARC-AGI-1 train | 36.8 | 40.3 | 44.3 | 44.3 | +7.5 [+2.0, +14.0] |
| ARC-AGI-1 eval | 7.0 | 10.0 | 12.0 | 12.0 | +5.0 [+1.0, +10.0] |
| ARC-AGI-2 new233 | 2.3 | 2.3 | 2.3 | 2.3 | 0 [−3, +3] |

**One column on games** (`spike_arc3.py`, `spike_arc3b.py`, `results/arc3_spike_summary.txt`). 12 tuning games, 2,880 recorded transitions, predict then learn, playfield only. CIs by game. No-change labels match the earlier probe's on every shared transition. The column keeps all earlier transitions; comparators use the last k. k = 12 rows read the same.

| On the 2,621 transitions shared at k = 3 | No change | Repeat rule (B1rel) | Monty-ARC columns | Column |
|---|---|---|---|---|
| Exact playfield | 58.8% | 63.1% | 61.5% | 65.1% |
| On the 1,081 where something changed | 0% | 16.4% | 8.6% | 27.8% |

- Column minus repeat rule: all +1.9 [−4.2, +8.3], changed +11.4 [−0.2, +28.5]. Column minus Monty-ARC columns: all +3.5 [−2.4, +9.8], changed +19.1 [+9.7, +31.6].
- The gain is uneven. Changed transitions, column vs repeat rule: `ls20` 51 vs 7, `sc25` 68 vs 11, `su15` 35 vs 0, `ar25` 51 vs 52, `g50t` 31 vs 35, `bp35` 6 vs 12, `cd82` 0 vs 4.
- **Monty-ARC keeps the better calibration.** Confident non-identity answers: column 9.5% coverage at 49% precision, Monty-ARC 3.6% at 63% (k = 3) and 5.2% at 96% (k = 12). A held-out check on the column is an obvious thing to add before the freeze.

| Switch, on all 12 games (changed transitions; full column 26.0%) | Result | Minus full, CI by game |
|---|---|---|
| Motor signal off | 1.1% | −24.9 [−40.5, −11.1] |
| Reach 1 / reach 3 / reach 6 (full) | 1.6% / 7.8% / 26.0% | −24.4 [−39.9, −10.5]; −18.2 [−30.4, −8.1] |
| Displacement form removed | 29.3% | +3.3 [+0.6, +6.6] |
| Moving frame added | 23.1% | −2.9 [−7.3, +1.2] |
| Nearest-object canonical frame added | 23.7% | −2.3 [−8.7, +3.5] |

**Caveats on all of this.** Spike code, sensors and arms were chosen after seeing these games and tasks. Twelve games is few, and frames here are mostly pose-free. The two matching rules aren't yet one. A spike is a reason to run the test, not a result.

**Other prior art checked.** TBP's fork has no policy and reports no numbers; `CyclicCipher/cipher_tbt_agent` and the forum's `anon_anon` have no official scores (`research/tbp_forum_theory_notes.md`). A web search found no TBT result on ARC-AGI-1/2 beyond ours, and no Monty behaviour-model results. The search wasn't exhaustive. Forum quotes come from our own transcript notes, not checked against the video.
