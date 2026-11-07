# Monty-ARC v5: failure analysis (ARC-AGI-2 eval and the 233 new ARC-AGI-2 training tasks)

Frozen v5 code (byte-identical to the published notebook). Data and scripts: `research/monty_eval/`. The numbers come
from `results/failure_data.json`, `near_miss.json`, `labels_merged.json`, `counterfactual_occluder.json`,
`vote_ablation.json` and `pooling_check.json`. Companion tables: `research/monty_ablations.md`.

## Summary (for the paper's "why it doesn't (yet) work" and "outlook")

1. **Monty-ARC fails by abstaining, not by guessing.** Of the 116 unsolved AGI-2 eval tasks, 109 get no
   candidate at all (94%). Of the 224 unsolved new-in-AGI-2 training tasks, 204 get none (91%). Not one AGI-2
   answer is confidently wrong (3/3 and 3/3).
2. **Every wrong answer on ARC-AGI-2 has leave-one-out evidence 0.** These are lookup-table hypotheses that fit
   each demo by memorising it. Their "near-miss" cell accuracy is illusory: only 12 of the 27 beat simply
   copying the test input.
3. **Across all 1,920 tasks, only 2 distinct tasks are confidently wrong, both from ARC-AGI-1.**
   - In both, the true rule is a counting rule (the shape that occurs twice; the majority colour) that lies
     outside the hypothesis space.
   - In one, a proxy (bottom-most object) fits every demo.
   - In the other, a `vote.pool` artifact lets 42 duplicate hypotheses from one module add up to "full"
     evidence.
4. **What is missing, by labelled primary gap** (unsolved AGI-2 eval, n = 116):
   - compositional / hierarchical structure 20%;
   - counting and relations 17%;
   - goal-directed search (fitting, packing, routing) 14%;
   - procedural behaviours outside the library 14%;
   - in-task symbols 13%;
   - geometry beyond D8 frames 13%;
   - within reach of an existing module 9%.

   Counting secondary labels too, composition is involved in 45% of tasks.
5. **Fixes that help ARC-AGI-1 do not help ARC-AGI-2.** A measured example: one generalised sensor (occluder =
   the vanishing colour) adds 5 AGI-1 eval tasks with 0 errors. On ARC-AGI-2 it adds 0 AGI-2-only tasks; its one
   AGI-2 eval gain, 981571dc, is an ARC-AGI-1 task.

## 0. Where the failures are

| | AGI-2 eval (120) | AGI-2 new-train (233) |
|---|---|---|
| solved (pass@2) | 4 (3 without the 6 tasks shared with ARC-AGI-1) | 9 |
| answered but wrong | 7 | 20 |
| abstained (no module produced a full-fit hypothesis) | 109 | 204 |
| unsolved, output same size as input | 78 / 116 (67%) | 166 / 224 (74%) |
| ... of which only background cells change ("drawing") | 18 | 40 |
| ... mixed changes (recolour + draw + erase) | 54 | 110 |
| unsolved, output a different size | 38, none a plain crop | 58, 4 plain crops |
| mean input size / colours / objects (unsolved) | 374 cells / 5.1 / 5.7 | 215 cells / 4.3 / 5.6 |

The answered tasks are almost all same-size grids where behavior or pattern produced a change table. On
different-size outputs (a third of AGI-2), only composition and self-model's crop can answer, and neither fits
any unsolved AGI-2 eval task.

## (a) Confident-but-wrong answers

- **AGI-2 eval and AGI-2 new-train: none.** Confident answers are 3/3 on each.
- **All 1,920 tasks: 4 instances, 2 distinct tasks, both ARC-AGI-1 tasks.**

| Task | Module, hypothesis | Pooled evidence | True rule | Why Monty was confident |
|---|---|---|---|---|
| f5aa3634 (AGI-1 eval; also in AGI-2 train) | composition `select multi8, prop=top, rule=min` (the bottom-most object, cropped) | 1.01 (two identical composition hypotheses) | Output the object shape that occurs twice in the grid. | "Bottom-most" happens to pick a repeated object in all 3 demos, and the learner-level LOO is 1.0. The real property, multiplicity, is not in the property list, so the proxy wins. **Gap: counting / relations.** |
| 9565186b (AGI-1 train; also in AGI-2 train) | behavior `color8/any/canon/R0/nearest` | 1.027, from 42 identical behavior hypotheses, best single LOO 0.75 | Keep the majority colour and paint everything else 5. | **Pooling artifact.** `vote.pool` adds 1% of the smaller evidence for every identical prediction, including the same module's duplicates, so a 0.75 answer crosses 0.99. The correct answer was also produced (multi8/any, LOO 0.79). **Gap: majority / counting.** |

Two more wrong top answers sit at pooled evidence ≥ 0.99, but neither is confident:
- **ea786f4a:** 84 duplicate behaviour hypotheses at 0.67 pool to 1.22.
- **54d9e175:** three behaviour hypotheses have *true* LOO 1.0 but fail because the test layout is outside the range
  of the demos. Four conflicting fully evidenced answers block confidence.

Counterfactual (analysis only, not in v5): pooling evidence only across distinct modules removes the 9565186b
false positive and gives AGI-1 train confident 59/59 and AGI-2 train 86/87, with no change in pass@2
(`monty_ablations.md`, Table 7).

**Lesson for the paper.** Leave-one-out evidence fails in two known ways:
- A proxy that is consistent with every demo while the true concept is missing from the hypothesis space. This is
  the classic hypothesis-space problem; LOO can't see what isn't there.
- A test input outside the demos' range. LOO only measures within-demo generalisation.

A third failure, double counting a module's correlated hypotheses, is an implementation choice that can be fixed.
Even so, LOO is what makes the system precise: replace it with fit-to-demos and confident precision on AGI-2 train
falls from 98% (85/87) to 70% (99/142).

## (b) Answered-but-wrong near misses, by module

All 27 answered-but-wrong ARC-AGI-2 tasks have top LOO evidence **0.0**. In each one, no hypothesis that fits all
demos predicts any held-out demo. So all 27 are flagged as guesses and none is confident.

| Split | Module of the top answer | Tasks | Median best cell accuracy | Median accuracy of copying the test input | Beat copy-input |
|---|---|---|---|---|---|
| AGI-2 eval | behavior | 4 | 83.5% | 82.4% | 1 |
| AGI-2 eval | pattern | 3 | 90.0% | 89.2% | 2 |
| AGI-2 new-train | behavior | 19 | 83.7% | 82.5% | 8 |
| AGI-2 new-train | pattern | 1 | 94.1% | 87.8% | 1 |

The mechanism is always the same. behavior (keys `size` / `holes` / `color`, radius 0–30) or pattern (a local
pattern library) memorises *what* changed next to each demo object. In LOO that model has never seen the held-out
demo's objects, so evidence is 0. On the test it writes plausible changes in the wrong places. Cell accuracy is
high only because most cells don't change. The closest cases:

- **9f8de559** (new-train, behavior, 99.0%; copy-input scores 99.5%). The rule: cast a ray along a line object's
  *own* diagonal axis from its marked end, and put one 7 where it meets the border band. Behavior writes one 7 in
  the band, but at a memorised position. *Gap: a behaviour whose direction comes from the object's shape (procedural
  behaviour).*
- **396d80d7** (new-train, behavior, 96.9% vs 95.3%) and **52df9849** (new-train, behavior, 96.9% vs 91.2%):
  instance-keyed change tables again.
- **97d7923e** (AGI-2 eval, pattern, 93% vs 92%). A top-left legend says which capped column gets filled, and
  pattern memorised column patterns of particular heights. *Gap: in-task symbol / count.*
- **16b78196** (AGI-2 eval, pattern, 90%): pieces must slide in and interlock with a jagged wall. *Gap: goal-directed
  fitting.*

So for ARC-AGI-2 "near miss" is the wrong frame. These tasks are not one parameter away; the evidence correctly
says the module doesn't understand them. Cell-level near misses that are real do exist, but they show up as
*abstentions*. The cleanest example: on **981571dc** (AGI-2 eval, also an ARC-AGI-1 task), self-model's existing
symmetry completion reproduces all 4 demos and the test *exactly*, once its occluder sensor accepts "every cell of
the vanishing colour" instead of "one solid rectangle". Verified with the frozen `symmetry.complete`.

## (c) What is missing: unsolved tasks by category (TBT terms)

**Method.**
- Six independent LLM labelling agents (Claude) read each unsolved task, rendered as text with its demos, test
  truth and Monty's per-module status.
- Each assigned a one-sentence rule, a primary missing capability from a fixed list of 8 (optional secondary), the
  closest Monty module, the gap, and a confidence.
- Coverage: all 116 unsolved AGI-2 eval tasks, plus a seeded random half (112 of 224, seed 2026) of the unsolved
  new-train tasks.
- Label confidence: eval 42 high / 55 medium / 19 low; new-train 45 / 53 / 14.
- The categories overlap and the labels are judgements, not proofs. The `gap` fields are hypotheses; in one
  checked case (981571dc) the labeller's diagnosis was wrong and the true gap was smaller (above).
- Per-task labels: `research/monty_eval/results/labels_merged.json`.

| Primary gap | TBT ingredient that is missing from Monty-ARC | AGI-2 eval (n=116) | incl. secondary | new-train sample (n=112) | incl. secondary |
|---|---|---|---|---|---|
| COMPOSITION: output assembled from parts, a rule acting on parts or groups, or several sub-rules chained | **Hierarchical, compositional models.** Objects as child objects at relative poses, and behaviours composed in sequence. Every Monty-ARC hypothesis is one family applied once; there is no hierarchy of learning modules. | 23 (20%) | 52 (45%) | 26 (23%) | 41 (37%) |
| COUNT_RELATION: counting, ranking/sorting, comparison, relations between objects | **Relational and numerosity features.** In TBT a relation is one object's location in another's reference frame. Monty-ARC keys objects only by intrinsic features (colour, size, shape, holes). | 20 (17%) | 34 (29%) | 23 (21%) | 31 (28%) |
| GOAL_SEARCH: fit, pack, dock or route to satisfy a constraint | **Goal states and model-based policy.** TBT's goal-state generator, with the output as a goal reached by actions. Monty-ARC predicts outputs directly and never searches. | 16 (14%) | 19 (16%) | 5 (4%) | 8 (7%) |
| BEHAVIOUR: trajectories and conditional actions (bounce, wrap, flow, turn at a cue) | **A learned, reusable library of behaviour models** (TBP future work). Monty-ARC has 4 hand-written dynamic families with fixed directions and per-task local change tables. | 16 (14%) | 32 (28%) | 10 (9%) | 22 (20%) |
| SYMBOL: legends, glyphs and markers with in-task meaning | **Binding between models:** one object's identity indexes another model's feature or action. association covers only 2-cell legends and same-shape templates. | 15 (13%) | 30 (26%) | 11 (10%) | 21 (19%) |
| GEOMETRY: scaling, rings and curves, layout extrapolation, non-rigid change | **Scale-invariant, continuous reference frames** (path integration). Monty-ARC frames are D8 × translation only. | 15 (13%) | 30 (26%) | 10 (9%) | 23 (21%) |
| CONTEXT: a different transform per instance, chosen by a cue | **Context-conditioned behaviour selection.** Rare as the primary gap, common as the secondary one. | 1 (1%) | 15 (13%) | 4 (4%) | 17 (15%) |
| NEAR_REACH: one family member, key or sensor parameter is missing | none conceptually | 10 (9%) | 10 (9%) | 23 (21%) | 24 (21%) |

The closest module is usually dynamics (eval 43, new 32) or composition (31, 31). The nearest families are the
parametric procedural ones; what they lack is that their parameters (direction, colour, stopping rule, which
object) come from a per-object cue rather than a global constant.

**ARC-AGI-2 eval is harder in kind, not just in size.** Compared with the new-train sample, it has 3× the
goal-search share (14% vs 4%) and less than half the near-reach share (9% vs 21%).

Illustrative tasks (primary label, high confidence where available; `e:` AGI-2 eval, `n:` new-train):

- **COMPOSITION**
  - e:38007db0: in each panel row, output the odd-one-out panel, stacked.
  - e:6e453dd6: slide shapes to a wall, *then* mark rows with enclosed holes.
  - e:7491f3cf: split one panel by its dividing line and fill an empty panel from two others.
  - e:b99e7126: tile-level pattern completion on a lattice of tiles.
  - n:25c199f5: stack the objects of three panels into one.
  - n:11dc524f: slide a shape to a block, *then* reshape the block as its mirror image.
- **COUNT_RELATION**
  - e:1ae2feb7: a dotted ray whose period equals the bar's length.
  - e:31f7f899: re-assign bar lengths in sorted order.
  - e:58490d8a: per-colour object counts drawn as dots.
  - e:581f7754: align each object's marker with a same-coloured reference cell.
  - n:878187ab: rectangle sides equal to two colour counts.
  - n:8abad3cf: k×k squares with k² = colour count, in ascending order.
- **GOAL_SEARCH**
  - e:446ef5d2: assemble jigsaw fragments into a framed rectangle.
  - e:7b3084d4: pack 4 pieces (with D8) into a solid square.
  - e:cbebaa4b: join shapes at matching connector dots.
  - e:f560132c: recolour 4 pieces by a key and fit them together.
  - n:7e576d6e: route a path through wall gates.
- **BEHAVIOUR**
  - e:36a08778: streams flow down and wrap around bars.
  - e:5961cc34: a beam enters blobs and re-emits from them.
  - e:b9e38dc0: flood a container and pour out as a 45° cone.
  - e:e87109e9: a line that turns by a colour legend.
  - n:7e2bad24: a diagonal ray that passes through one colour and reflects off another.
- **SYMBOL**
  - e:136b0064: glyphs stand for strokes of a given direction and length.
  - e:3e6067c3: a legend sequence says which boxes to bridge.
  - e:9aaea919: bars act as commands for the column above them.
  - e:65b59efc: a key maps panels to colours, and a layout map is expanded.
  - n:22806e14: paint the centre of odd-sided squares in the marker's colour.
- **GEOMETRY**
  - e:45a5af55: stripes become concentric rings.
  - e:c4d067a0: extrapolate a large layout from a miniature key.
  - e:13e47133: concentric rings inside irregular regions.
  - n:e3f79277: corner arms become a scaled triangle.
  - n:2ccd9fef: extrapolate a growth sequence by one step.
- **CONTEXT**
  - e:b5ca7ac4: boxes slide left or right by frame colour.
  - n:320afe60: recolour and push objects by whether they enclose a hole.
  - n:4e7e0eb9: swap blocks only where a divider is present.
- **NEAR_REACH**
  - e:981571dc: self-model occluder sensor (verified).
  - e:8e5c0c38: per-object mirror repair by deletion.
  - e:bf45cf4b: Kronecker product of a mask with another tile.
  - n:6ca952ad: gravity only for objects of 4+ cells.
  - n:833966f4: a fixed positional permutation.
  - n:60d73be6: mirror across off-centre divider lines.

## (d) Outlook: two principled candidates (not built; v5 is frozen)

Base rate first. In v5, no module contributes more than 1 unique AGI-2 eval solve, and 6 of 8 contribute at most
one AGI-2 solve across both AGI-2 splits. A new hand-written family should therefore be expected to add about 1
AGI-2 eval task (≈ 0.8 points), not a category's full share. The shares in (c) are ceilings.

1. **Relational and numerosity features in a shared object frame.**
   - *The idea:* objects keyed and selected by counts, rank, multiplicity ("the shape that occurs twice"),
     contact/inside, and displacement to a same-coloured anchor. These would be shared by behavior, dynamics and
     composition, so a parameter such as direction, colour or which-object can come from a per-object cue.
   - *TBT grounding:* relations are locations of one object in another's reference frame. Counts are how many
     instances of one model are recognised.
   - *Addresses:* COUNT_RELATION (17% of eval unsolved, 29% with secondary labels) and the dynamics "gating"
     near-reaches (n:6ca952ad, n:17829a00, n:494ef9d7, n:825aa9e9). It would also give the true rule a place in the
     hypothesis space for **both** confidently wrong tasks (f5aa3634, 9565186b).
   - *Estimate:* +1–2 AGI-2 eval tasks and +3–5 on new-train, with fewer false positives.
   - *Risk:* a larger key space raises multiple-comparison false confidence. LOO must stay per hypothesis.
2. **Hierarchical composition: a second-level learning module over first-level hypotheses.**
   - *The idea:* hypotheses are chains (module A's transform, then module B's) or part-to-whole models (an object as
     parts at relative poses), scored by the same LOO over the whole chain.
   - *TBT grounding:* hierarchy of learning modules and compositional objects and behaviours.
   - *Addresses:* COMPOSITION, the largest gap (20% primary, 45% with secondary labels).
   - *Estimate:* +1–3 AGI-2 eval tasks.
   - *Costs:* the search grows with the square of the library. Today's modules return only full fits, so chains need
     partial-fit scoring. Precision depends on keeping LOO: the fit-only ablation drops it from 98% to 70%.

Goal-directed search (14% of eval) and the open-ended behaviour library are beyond hand-written modules. The natural
route is the hybrid already in the notebooks: an LLM proposes programs, and Monty's columns serve as verifiers and
calibrated voters.

Two cheap, measured fixes help ARC-AGI-1 rather than ARC-AGI-2, which is itself evidence for the paper:

| Fix (counterfactual) | AGI-1 eval | AGI-1 train | AGI-2 eval | AGI-2 new-train | Errors added |
|---|---|---|---|---|---|
| self-model occluder = the vanishing colour | +5 | +2 | +1 (981571dc, an ARC-AGI-1 task) | 0 | 0 |
| cross-module-only evidence pooling | pass@2 ±0; confident 33/34 | confident 58/59 → 59/59 | ±0 | ±0 | −1 false positive |
