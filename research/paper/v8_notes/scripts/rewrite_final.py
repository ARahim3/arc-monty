"""Writes the body of paper.md (through Section 9) from this text; keeps References and appendices from the current file, then patches those."""
import os  # noqa: E402  (release: paths from the repo root)
_REPO = os.environ.get("ARC_MONTY_ROOT", os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..")))  # repo root
P = (_REPO + "/research/paper/v8/paper.md")
old = open(P, encoding="utf8").read()
i = old.index("## References")
tail = old[i:]
BODY = r"""# When Can You Trust a Solver's Answer? Thousand Brains Principles Tested on Unseen ARC Tasks

*Subtitle:* A held-out demonstration separates right from wrong programs by 45–75 points on three kinds of learner, one frozen in 2020 before the test sets existed; fold agreement adds a proof under exchangeability.

**Abdur Rahim**

Track: ARC-AGI-2. This document: {{PDF_URL}}. Code: {{GITHUB_URL}}. Notebook of the named submission: `kaggle.com/code/rahim3/monty-arc-qwen-nvarc`.

## Abstract

An answer can fit every demonstration and still be wrong, so when can it be trusted? Thousand Brains principles supply candidates, and the one that pays is a test: re-run the whole solver with each demonstration held out, and answer only if every fold predicts its held-out demonstration and all folds agree on the test. If demonstrations and test are exchangeable, the joint probability of answering and being wrong is at most 1/(n+1) for any learner fixed in advance; at low coverage that implies no precision. We test this on unseen ARC-style sets with three learners: Monty-ARC, our hand-written solver; Qwen3.8-27B; and the 2020 Kaggle winner, frozen before those sets existed, so that premise holds by construction. Programs that predict their held-out demonstration beat those that miss it by 45–75 points on the test (Table 5), and the rule beats the usual test wherever it answers. Exchangeability looks imperfect on the human-designed ARC-AGI-2 and ConceptARC, in opposite directions, so there only the rule's measured value remains. Object frames add solves but not trust, and voting between modules was barely exercised. It does not raise a score: Monty-ARC alone scores 0.00 on the hidden set, our leaderboard score comes from the neural solvers beside it (Table 1), and at these budgets, on one split, in a replay of logged runs, trust did not buy score.

**Table 1. Leaderboard (ARC-AGI-2, public score). Every leaderboard number for this competition is here.**

| Submission | Ref | Public LB | Role here |
|---|---|---|---|
| Tri v3: Qwen3.8-27B, NVARC fork, Monty-ARC v5 | 57726521 | 32.64 | **Named submission** (Section 7) |
| Tri v4-A: same components, scheduling changed | 57785855 | 27.36 | Variant, not named |
| Hybrid v3: NVARC fork, Monty-ARC with 7 modules | 57689321 | 28.47 | Public notebook |
| Monty-ARC v5 alone: 8 modules, CPU, no training | 57762908 | 0.00 | A learner under test |
| Monty-ARC v0: 2 modules, whole-task D8 voting | 57661715 | 0.00 | Early version |

*Field on 2026-10-30: 3,541 teams, top score 88.06, median 29.31. The named submission ranks 252 of 3,541. 2,010 teams score between 28 and 34.*

## 1. Introduction

An answer can fit every demonstration and still be wrong. At ARC-AGI-2's budget about a quarter of an LLM's programs that reproduce every demonstration fail on the test; on ConceptARC about 7% do (Section 6.2). So when can a solver's answer be trusted?

ARC-AGI [1, 2] is a good place to ask. A task shows a few demonstrations, typically two to five input-output grid pairs, and one or more test inputs. The solver must reproduce each test output exactly, with two attempts per output and no penalty for a wrong attempt. ARC-AGI-2 [2] is the harder 2025 version; the 2026 Kaggle competition scores it on 240 hidden tasks in a 12-hour offline run.

The Thousand Brains Theory (TBT) [3–6] is a theory of the neocortex, not of puzzles, but it supplies three candidates: **frames** (models are stored in object-centred reference frames), **prediction** (a model is tested by what it predicts about observations not yet made) and **voting** (many columns each hold models, and they vote). We built them into Monty-ARC and froze it. Prediction is the one that pays, and it gives a reusable rule:

> **Re-run the whole solver with each demonstration held out, and answer only if every fold predicts its held-out demonstration and all folds agree on the test.**

We call this fold-agreement leave-one-out (FA-LOO). A plain hold-out check is earlier work (CORA [11]). The agreement condition makes a proof possible for any re-runnable learner. We add, to our knowledge, the first test of TBT's functional claims on ARC-AGI-1/2, the proof, a test of the rule on three kinds of learner, a test of exchangeability, a label-free estimate of precision, and negative results.

## 2. Related work

**ARC solvers.** The 2020 Kaggle winner [21] is a hand-written search over a domain-specific language. NVARC [8], the 2025 winner, fine-tunes Qwen3-4B on synthetic ARC-like data and trains further on each task at test time, as in Akyürek et al. [18]. Forum reports put its public forks at about 28–34 from run to run [10]. Verifying programs first, with another solver as fallback, is from Li et al. [17]. Franzen et al. [9] vote over task augmentations and evaluate that for ranking, not calibration.

**TBT and Monty.** Monty, the Thousand Brains Project's implementation, recognises 3D objects and their poses [5, 7]. Its compositional benchmarks are supervised and not yet expected to perform well; behaviour models are plans [7]. Its own fork and a third-party agent target ARC-AGI-3, and CORA's code has an untested vote layer labelled Thousand Brains [11]. We found no test of TBT's claims on ARC-AGI-1/2.

**Hold-out certificates.** CORA [11] came first: July 2026 runs, code public by 2026-10-07 at the latest. We read it before building the system-level wrapper tested here; Monty-ARC's per-module evidence dates from 2026-10-26. CORA accepts a program only if the whole induction, re-run with each demonstration hidden, still predicts the hidden one. Its certified programs were right 40 of 42 times on ARC-AGI-2 training tasks, against 37 of 201 (18.4%) for rejected programs that fit every demonstration; it also reports "0 of 11 on an evaluation development split", and 0.00 on Kaggle. It also gated a per-task neural learner (3 of 3 right tasks pass at least one fold, 0 of 34 wrong tasks any). As its writeups describe it, CORA checks condition (a) of Section 5 and answers with the full-data program. It states no bound, and no agreement condition for program induction, though it suggests resample consistency for samplers.

**Guarantees.** The proof adapts the leave-two-out tournament of the jackknife+ [12] to exact-match answers with abstention; we found no earlier use on ARC. SynGuar [19] guarantees generalisation for programming by example, with far more examples than ARC gives. Zhou et al. [20] calibrate abstention for LLM code generation by comparing execution outcomes.

## 3. The three learners

**Monty-ARC** has eight numpy learning modules (Appendix A), with no training data and no memory across tasks. Each enumerates hypotheses, keeps those that reproduce every demonstration, scores them by held-out prediction and predicts the test. Identical answers pool evidence across modules, with a 2:1 consensus rule. It takes a mean 1.8 CPU-seconds per public evaluation task. We froze it, and turned each claim into a switch. *Frames:* behaviour stores output changes in each object's D8-canonical pose (`canon`), grid-aligned at the object (`abs`), both (`both`, shipped) or in grid coordinates with no anchor (`global`). *Prediction:* the rules of Section 4. *Voting:* modules removed or alone, a no-vote baseline, 8 whole-task D8 views, agreement among folds. *Figure 1: `research/paper/figures/system_diagram.png`.*

**Qwen3.8-27B** [16] writes programs: sampling at temperature 1.0, 32k thinking tokens per round, at most two rounds, TPU, canonical order, every fold from scratch. A program is *verified* if it reproduces every demonstration it was shown. It ran on all 120 ARC-AGI-2 public evaluation tasks, on which the harness was built, and all 160 ConceptARC tasks, never used to choose anything in it, though the weights may have seen either. The plan was fixed before any output. Its tests came from a first, post hoc look at a greedy run at 16k: 5 of 20 verified tasks certified, all right; verified fold programs right 78.1% against 7.5%; a held-out AUROC of 0.91; an identical rerun doing about as well as the certificate.

**The 2020 first-place program** [21] is a hand-written search frozen in 2020, before ConceptARC, Mini-ARC and 1D-ARC existed, so premise (F) below holds by construction. Its author saw ARC-AGI-1, so concept-level overlap is not ruled out. We ran its published recipe unchanged, with demonstrations in canonical order and a plan fixed before any output on these sets. It answers one query at a time, so a fold is two runs on the same $n-1$ demonstrations. It reproduces: pass@3 on ConceptARC is 251 against the ConceptARC authors' 249, with 97.9% item agreement (252 and 99.4% in native order). On 286 of 901 1D-ARC tasks the grids are wider than it can read, and it abstains.

**What this test can and cannot say.** TBT's central claim is about movement and sensorimotor learning, and it has no switch here, since ARC-AGI-1/2 grids are static and seen whole. We test three functional principles, not the theory. Leave-one-out is cross-validation, which long predates TBT: TBT supplies the question, not the mechanism, and a positive result does not separate TBT from other accounts that say the same. The modules are hand-written, so a null below is about these modules, not about the neocortex.

## 4. How the claims were tested

All Monty-ARC tests use v5, byte-identical to the published notebook. The plan was written before any per-module, per-frame, per-group or eight-view number on unseen data was seen; overall rule counts on ConceptARC were already known, and the plan says so. For Mini-ARC and 1D-ARC it was completed before any solver run. Rules, thresholds and buckets are those of development. Seven groups of primary comparisons were fixed; other analyses are marked post hoc.

**Table 2. Data. Overlap with Monty-ARC's development tasks is by exact pair; concept-level overlap is not ruled out.**

| Set | Items | Clusters | Pairs shared |
|---|---|---|---|
| ConceptARC [13]: 16 human-designed concept groups | 480 test pairs | 160 tasks | 0 of 905 |
| Mini-ARC [14]: 5×5 grids | 149 test pairs | 149 tasks | 0 of 671 |
| 1D-ARC [15]: generated, one-row grids | 901 test pairs | 18 types | 0 of 3,545 |
| ConceptARC MinimalTasks: attention checks | 48 test pairs | 16 tasks | 0 of 93 |

The comparator for Monty-ARC, *public eval*, is the 514 distinct ARC-AGI-1 and ARC-AGI-2 evaluation tasks. It was seen in development, and 376 of its tasks are in ARC-AGI-2's training split, so it is not held out. We report no training-set performance as a result; the few development-wide figures (code checks, the event rate) are labelled.

**Rules.** *Top answer:* the learner's best answer, always given. *Fit:* the top answer only if it reproduces all demonstrations (for Qwen, verified). Monty-ARC's fit-only rule is stricter: every hypothesis that fits counts as fully evidenced, then a 2:1 consensus applies. *v5 heuristic:* pooled leave-one-out evidence at least 0.99, and a 2:1 lead over any conflicting answer; no proof. *Plain (a):* every fold predicts its held-out demonstration; the answer is the full-data one. *FA-LOO:* conditions (a), (b), (c) of Section 5, around the whole system.

**Statistics.** Intervals are percentile cluster bootstraps, 10,000 resamples; "separates" means a difference's interval excludes 0, `ns` that it does not. Sets count test pairs, unless marked tasks. In the *real role* the true test pair is the query; in *demo roles* each demonstration in turn plays test.

## 5. The certificate

### 5.1 Rule and theorem

Let $Z_i=(x_i,y_i)$, $i\le n$, be the demonstrations and $Z_{n+1}=(x_{n+1},y_{n+1})$ the test pair. A learner $A(S,Q,\xi)$ takes labelled pairs $S$, unlabelled queries $Q$ and a seed $\xi$, and returns one prediction per query. Abstaining counts as mispredicting. Other test inputs of the task may be shown as extra queries; they count as fixed side information. Three premises:

- **(S) Symmetric.** $A$ depends on $S$ and on $Q$ only as unordered collections. An LLM satisfies this when demonstrations and queries are shown in a canonical order computed from their content.
- **(F) Fixed in advance.** $A$, including code, prompts and weights, is chosen without looking at these pairs. Seeds are i.i.d. and independent of the pairs; one shared seed, or none, also qualifies.
- **(E) Exchangeable.** The joint law of $(Z_1,\dots,Z_{n+1})$ is unchanged when the indices are permuted.

A fold $M_i=A(\{Z_j: j\le n,\ j\ne i\},\ \{x_i,x_{n+1}\},\ \xi_i)$ predicts both of its queries. FA-LOO answers $\hat y$ only if (a) $M_i(x_i)=y_i$ for every $i\le n$; (b) $M_i(x_{n+1})=\hat y$ for every $i\le n$; and, optionally, (c) the model fitted on all $n$ demonstrations also outputs $\hat y$.

**Theorem.** Under (S), (F) and (E), $P(\text{answer and } \hat y\ne y_{n+1})\le 1/(n+1)$. The same holds conditionally on the unordered multiset $\{Z_1,\dots,Z_{n+1}\}$, and after any further filter such as (c). The conditional form needs a weaker (F): $A$ may depend on the multiset, as long as it does not depend on which pair is the test. Tuning on a task's pairs regardless of role keeps the bound; tuning until the test output comes out right voids it.

### 5.2 Proof

For each unordered pair $\{a,b\}\subset\{1,\dots,n+1\}$ let $M_{ab}=A(\{Z_j: j\ne a,b\},\{x_a,x_b\},\xi_{ab})$ with i.i.d. seeds; by (S), $M_{ab}=M_{ba}$. Write $L(a,b)=1$ if $M_{ab}$ mispredicts $y_a$, else 0. Let $E_a$ be the event that $L(a,b)=1$ and $L(b,a)=0$ for every $b\ne a$: every model that held out $a$ gets its partner right and $a$ wrong.

1. *At most one event occurs.* If $a\ne c$, then $E_a$ requires $L(c,a)=0$ and $E_c$ requires $L(c,a)=1$. So $\sum_a P(E_a)\le 1$. This step needs neither (E) nor (F).
2. *The events are equally likely.* A permutation $\pi$ of the indices leaves the joint law of pairs and seeds unchanged, by (E) and (F), and by (S) it carries $E_a$ to $E_{\pi(a)}$. So $P(E_{n+1})\le 1/(n+1)$.
3. *Every confident error is $E_{n+1}$.* The real fold $M_i$ is $M_{i,n+1}$. Condition (a) says $L(i,n+1)=0$ for all $i$; (b) with $\hat y\ne y_{n+1}$ says $L(n+1,i)=1$ for all $i$.

The other models are never run; they exist only for the argument. Condition (c) only removes answers. For the conditional form, under (E) the arrangement of indices is uniform given the multiset, and the same steps apply. ∎

In words: at most one of a task's $n+1$ pairs, playing test, can produce a confident error. A fold's seed travels with its unordered pair, so a sampling LLM needs no greedy decoding, and decoding noise independent of the data does not void the bound.

### 5.3 What the theorem does not say

**It is joint, and a worst case.** With coverage $c$ it gives precision at least $1-\frac{1}{(n+1)c}$. Where the mean worst case (22.7–28.3%) exceeds coverage this is vacuous: on Monty-ARC's sets, Qwen's ARC-AGI-2 run, and every whole set for the 2020 program, closest on Mini-ARC and MinimalTasks. There precision is only measured. On Qwen's ConceptARC run, per pair, 48.3% coverage gives a floor of 41% (measured 232/232), though (E) is doubtful there. The bound is tight: if exactly one pair is odd and the learner finds the rule that fits the rest, an error occurs exactly when the odd pair draws the test role, with probability $1/(n+1)$.

**It needs a learner fixed before the data.** We developed Monty-ARC on public data, test outputs included, so (F) fails and the theorem says nothing about the 514 public-eval tasks. It can apply only to data unseen in development, and any change motivated by those sets would void them too.

**Selection outside the learner breaks it.** Choosing among $H$ structures on all demonstrations and re-fitting only parameters in each fold gives a union bound $H/(n+1)$, vacuous for $H\ge n+1$, with $H$ a family fixed in advance; lists generated from the demonstrations understate it. So FA-LOO wraps the whole system, and the v5 heuristic has no proof. We have no measured instance. The unit is a test pair: for a task with $k$ test pairs, "any answer wrong" has only the union bound $k/(n+1)$.

**Plain (a), and what agreement is for.** In general (a) alone has no bound: a learner right from $n-1$ demonstrations and wrong from $n$ passes every fold and is always wrong. For first-fit learners it needs no help. *Lemma.* Let $A$ return the first hypothesis, in an order fixed in advance, that fits $S$. If (a) holds, all folds return the full-data hypothesis $h^*$. *Proof.* By (a) each fold's hypothesis fits all $n$ demonstrations, so $h^*$ comes no later than it; $h^*$ fits each fold's subset, so each fold's hypothesis comes no later than $h^*$. ∎ So (b) and (c) follow, and the theorem covers plain (a) for such learners, including CORA's check wherever its induction is first-fit.

The three learners complete the argument. Monty-ARC is close to first-fit: of the 912 unseen-set roles that pass (a), out of 6,228, (b) fails in none (3 of 471 across all development tasks). So agreement is implied and inert there. The 2020 program is not first-fit: it ranks by a score that allows partial fits, and a third of its top answers on ConceptARC do not fit all demonstrations. Of roles passing (a), (b) fails in 4 of 21, 0 of 32, 21 of 205 and 0 of 12, rejecting 18 right and 7 wrong answers. So the lemma does not apply, plain (a) has no proof for it, and only agreement brings it under the theorem. On Qwen agreement does real work: (a) stops 12 of 14 verified-but-wrong tasks on ARC-AGI-2 and (b) the other 2; on ConceptARC (a) stops 11 of 22, (b) 7 more and (c) the last 4.

### 5.4 Why the error is so far below the worst case, and whether (E) holds

We measured the theorem's event by rotating every pair through the test role, in frozen Monty-ARC.

**Table 3. Tournament events, Monty-ARC. An item is a task with one test pair.**

| | Public eval (seen) | ConceptARC | Mini-ARC | 1D-ARC |
|---|---|---|---|---|
| Items with an event; with two or more | 5 of 514 (1.0%); 0 | 20 of 480 (4.2%); 0 | 4 of 149 (2.7%); 0 | 54 of 901 (6.0%); 0 |
| Events on the test role: observed / expected if roles are exchangeable (post hoc) | 1 / 1.15 | 9 / 5.53 | 1 / 0.76 | 11 / 13.5 |
| Joint P(answer and wrong), real role | 0.19% | 1.88% | 0.67% | 1.22% |
| Worst case, mean 1/(n+1) | 24.2% | 28.3% | 22.7% | 25.0% |

**The gap decomposes.** The joint rate is the event rate times the chance the event falls on the test role. The worst case assumes an event in every task; events occur in 1–6% of items (1.5% over all development tasks, training included), which puts the joint rate 15 to 34 times below the worst case on the unseen sets (125 on public eval). That is an identity. Judged, why events are rare: an event needs a rule right on $n$ of $n+1$ pairs and found again from every subset. A correct rule produces no misses, and a coincidental fit usually fails to re-appear and misses several pairs, so events mark a stable proxy. Hand-reading fits (Appendix B): of Monty-ARC's 10 wrong ConceptARC answers, 5 have a test outside the demonstrations' range, 4 a proxy that fits every fold, and 7 have only two demonstrations.

**Checks on (S)** (code, on development tasks). Swapping query order changes 0 of 8,266 models, random demonstration order 0 of 1,205 folds, two hash seeds none. No item in 2,725 has two events, and every wrong FA-LOO answer in 6,228 unseen-set roles is an event; given (S) both must hold, so they confirm the implementation, not (E). The 2020 program's raw output depends on demonstration order (top answer unchanged in 123 of 130 reversed runs), which is why it runs in canonical order.

**A direct test of (E).** Under the premises a fold model is as likely to be right on its held-out demonstration as on the test, because the two can swap roles. So discordant folds must balance in expectation.

**Table 4. Each real-role fold model: right on its held-out demonstration vs right on the test. Abstaining counts as wrong. Clusters: tasks, or types on 1D-ARC.**

| Learner, set | Folds | Held-out / test | Difference, points | Held-out only / test only | Clusters, more held-out : more test |
|---|---|---|---|---|---|
| Monty-ARC, ConceptARC | 1,281 | 12.7% / 11.8% | +0.9 [−0.8, +3.0] ns | 33 / 21 | 11:15 |
| Monty-ARC, Mini-ARC | 528 | 11.7% / 11.9% | −0.2 [−2.8, +2.5] ns | 15 / 16 | 7:10 |
| Monty-ARC, 1D-ARC | 2,703 | 20.9% / 22.1% | −1.2 [−2.8, +0.1] ns | 47 / 79 | 4:8 |
| Qwen, ARC-AGI-2, greedy 16k (post hoc) | 359 | 19.8% / 14.5% | **+5.2 [+2.1, +8.7]** | 23.0 / 4.2 | 17:4 (p = 0.007) |
| Qwen, ARC-AGI-2, sampling 32k (planned) | 359 | 32.9% / 27.9% | **+5.0 [+1.5, +8.6]** | 28.5 / 10.67 | 22:9 (p = 0.029) |
| Qwen, ConceptARC (planned) | 427 | 76.1% / 81.2% | **−5.1 [−8.1, −2.1]** | 18.67 / 40.33 | 29:46 (p = 0.064) |
| 2020 program, ConceptARC (planned) | 1,281 | 22.2% / 25.3% | −3.0 [−6.3, +0.2] ns | 113 / 152 | 27:54 (p = 0.004) |
| 2020 program, Mini-ARC (planned) | 528 | 38.4% / 37.9% | +0.6 [−4.6, +6.0] ns | 52 / 49 | 25:32 |
| 2020 program, 1D-ARC (planned) | 2,703 | 36.4% / 36.4% | **−0.1 [−1.0, +0.9]** ns | 149 / 151 | 5:6 |
| 2020 program, MinimalTasks (planned) | 138 | 45.7% / 50.7% | −5.1 [−14.0, +2.9] ns | 9 / 16 | 2:5 |

**Measured.** For Qwen, test outputs are harder than demonstrations on ARC-AGI-2, found post hoc and replicated in a planned test at the same size, and easier on ConceptARC, where the bootstrap excludes 0 and the sign test does not. The 2020 program leans the same way on ConceptARC, with the two statistics disagreeing the other way round. For Qwen the test strictly rejects (E) and (F) jointly; for the 2020 program (F) holds by construction. On 1D-ARC its difference is zero with a tight interval. Monty-ARC's folds are too sparse to see any of this: on ARC-AGI-2's 120 tasks they are right 12 times on each side, with no discordant fold.

**Judged.** On the generated set the premise holds tightly; on human-designed sets it fails in both directions, which is what you would expect if people choose test pairs deliberately while a generator does not. Mini-ARC does not reject it, with less power.

**What this means for the bound.** Where (E) fails, step 2 fails: the test role can carry more than its $1/(n+1)$ share of events. Steps 1 and 3 still hold, so a confident error still requires the test to be the task's one odd pair, but the bound is no longer a guarantee. On those sets what remains is the rule's measured value.

### 5.5 Estimating precision without test labels (post hoc)

Rotate roles among the demonstrations only: hold out two, fit the rest, score (a) and (b). On Monty-ARC, on tasks with $n\ge 3$, against real-role FA-LOO: ConceptARC 80.6% [58.3, 93.0] vs 88.0% [66.7, 100.0]; Mini-ARC 77.3% [46.2, 94.1] vs 88.9% [62.5, 100.0]; 1D-ARC 83.8% [34.0, 94.0] vs 93.6% [79.1, 98.3]. It runs 7–12 points low, as one demonstration fewer suggests; the gap separates only on 1D-ARC (−9.8 [−43.2, −1.0]). A notebook could calibrate this way on the hidden set during the scored run [10]. It is a set-level estimate, it cannot see $n=2$, and on an LLM it needs $n(n-1)/2$ syntheses per task. It assumes tests are like demonstrations; where they are not, it can be off either way. The cheap form is already in the fold runs: the mean held-out rate estimates test accuracy at $n-1$ demonstrations without labels. By Table 4 it is off by about 5 points on Qwen, in opposite directions on its two sets, and by 3 points or less for the other learners on the larger sets.

## 6. Results

### 6.1 The held-out split, across three learners

**Table 5. Right on the test, for fold programs that predict their held-out demonstration vs those that miss it (number of programs). All planned. Monty-ARC's rows use its closest measure, a different one: the system's top answer at evidence ≥ 0.99 vs below.**

| Learner | Set | Predict held-out | Miss it | Difference, points |
|---|---|---|---|---|
| Monty-ARC (evidence ≥ 0.99 vs below) | ConceptARC | 81.5% (54) | 13.4% (82) | +68.1 [+51.5, +82.6] |
| | Mini-ARC | 91.7% (12) | 20.9% (43) | +70.7 [+48.0, +87.9] |
| | 1D-ARC | 93.9% (181) | 19.2% (146) | +74.7 [+61.2, +82.9] |
| Qwen3.8-27B | ARC-AGI-2 eval | 83.3% (99) | 17.4% (47) | +66.0 [+53.6, +77.9] |
| | ConceptARC | 94.5% (321) | 45.8% (88) | +48.7 [+41.3, +56.3] |
| 2020 program, (F) by construction | ConceptARC | 60.4% (285) | 15.3% (993) | +45.0 [+35.3, +54.6] |
| | Mini-ARC | 74.4% (203) | 15.1% (325) | +59.3 [+47.8, +69.8] |
| | 1D-ARC | 84.8% (983) | 17.5% (862) | +67.3 [+55.4, +75.8] |
| | MinimalTasks | 85.7% (63) | 21.3% (75) | +64.4 [+44.6, +80.3] |
| | ARC-AGI-2 eval | 16.7% (6) | 0.6% (468) | +16.0 [−0.6, +48.8] ns |

**This is the case for portability.** A hand-written enumerator, an LLM and a classical search all show it, and the 2020 program's rows need no trust in us. On ARC-AGI-2 that program almost never predicts a held-out demonstration, so its row says little. Qwen and the 2020 program are measured on programs; Qwen, restricted to programs verified on what they saw. Within tasks that have both kinds, the cleanest control, Qwen gives +37.5 [+11.0, +61.8] (17 tasks) and +36.7 [+26.5, +46.9] (49 tasks). Sorting does not by itself make programs better: per run on ARC-AGI-2, passing fold programs are only a little more precise than plain verified samples, 83.3% [75.0, 90.9] against 75.2% [66.1, 83.5], barely separating.

### 6.2 The rule against the usual test

**Table 6. Real role. Fit: Monty-ARC, its fit-only rule; Qwen, verified; 2020 program, top answer that fits all demonstrations. Qwen counts tasks here; per pair in Table C7.**

| Learner, set | Top answer | Fit | FA-LOO | Coverage | FA-LOO minus fit, points |
|---|---|---|---|---|---|
| Monty-ARC, ConceptARC | 40.4% | 43/74 = 58.1% | 35/44 = 79.5% | 9.2% | +21.4 [+3.3, +40.3] |
| Monty-ARC, Mini-ARC | 36.4% | 15/29 = 51.7% | 8/9 = 88.9% | 6.0% | +37.2 [+8.7, +62.5] |
| Monty-ARC, 1D-ARC | 60.6% | 187/285 = 65.6% | 161/172 = 93.6% | 19.1% | +28.0 [+13.4, +45.7] |
| Qwen, ARC-AGI-2 eval | | 32.67/45 = 72.6% [59, 84] | 7/7 [65, 100] | 5.8% | |
| Qwen, ConceptARC | | 139/150 = 92.7% [87, 96] | 65/65 [94, 100] | 40.6% | |
| 2020 program, ConceptARC | 37.9% | 152/310 = 49.0% | 11/15 = 73.3% | 3.1% | +24.3 [−10.0, +50.4] ns |
| 2020 program, Mini-ARC | 44.3% | 48/76 = 63.2% | 29/32 = 90.6% | 21.5% | +27.5 [+14.9, +40.1] |
| 2020 program, 1D-ARC | 67.0% | 370/445 = 83.1% | 176/183 = 96.2% | 20.3% | +13.0 [+6.0, +22.5] |
| 2020 program, MinimalTasks | 64.6% | 29/41 = 70.7% | 12/12 = 100% | 25.0% | +29.3 [+13.9, +46.5] |

**Monty-ARC.** Fit-only is the same candidates with held-out evidence removed, so the comparison isolates that one thing. Precision also falls with evidence (ConceptARC 44/54, 4/10, 7/71 at ≥ 0.99, [0.5, 0.99), 0; the plan's fourth bucket has one item per set). Its FA-LOO does not separate from plain (a) or from the v5 heuristic, and on ConceptARC the estimate favours v5 (Table C6). Absolute precision falls from what development suggested: public eval minus ConceptARC is +18.1 [+4.3, +33.9]. The number to carry away is 80–94% on easier unseen sets, not 98%.

**Qwen.** FA-LOO answers 72 tasks with none wrong and rejects all 36 verified-but-wrong tasks; a random subset would avoid them with p = 0.058 on ARC-AGI-2 and p = 9.6 × 10⁻⁷ on ConceptARC, the strongest evidence for the rule. The price is coverage: it also rejects 24 of 31 and 63 of 128 fully right tasks. The held-out rate alone ranks weakly: the prespecified AUROC is 0.705 [0.52, 0.87], p = 0.013, so **the post hoc 0.91 did not hold at that size**, and 0.584 [0.45, 0.72], p = 0.083, on ConceptARC, with 11 of 87 verified tasks at rate 1.0 wrong. Beside Monty-ARC per pair (Table C7), its FA-LOO is 232/232 at 48.3% coverage against 35/44 at 9.2%. **Do not read this as the certificate being better on an LLM:** Qwen is simply much stronger here, right on 87.7% of pairs with one attempt and no rule, with little left to reject. The theorem's status is weaker too: (E) is doubtful on both sets, (F) is open, and the one memorisation check we ran, for long literal rows in programs, found none. So this tests usefulness, not the bound.

**The 2020 program.** FA-LOO minus top answer, as planned, is +35.4 [+1.1, +61.7], +46.3 [+35.1, +57.6], +29.2 [+12.8, +46.3], +35.4 [+18.8, +52.1], all separating. Against the fairer fit baseline ConceptARC does not separate. **It did not fix the thin ConceptARC evidence:** under the rule it answers 15 pairs in 6 tasks, against Monty-ARC's 44 in 18, and 3 of the 6 tasks hold a wrong answer. On ARC-AGI-2 it is right on 2 of 160 under the usual test, and the rule answers nothing.

**A portfolio of learners.** Monty-ARC's and the 2020 program's certified answers barely overlap: 7 of 52 pairs, 5 of 36, 14 of 341, 0 of 17. Each stays precise on what only it answers.

### 6.3 What the rule costs on an LLM (ARC-AGI-2)

**Cost.** On every task FA-LOO needs $n+1$ syntheses, 3.9× the tokens. But folds are needed only when the full-data run verifies: every (a)+(b)+(c) answer comes from such a task, and a further filter keeps the bound. At verified rate $v$ the price is about $1+vn$. Here, at $v=0.375$, that is 1.94× (133 folds), or 1.61× exiting at the first failed fold (91 folds).

**Folds instead of repeats (planned).** At the same runs per task, score of 120, folds against plain samples: two runs 45.5 vs 47.0, −1.5 [−6.0, +3.0]; three 52.0 vs 55.0, −3.0 [−10.0, +4.0]; four 53.5 vs 55.0, −1.5 [−9.0, +6.0]. None separates, plain leads on every point estimate, and tie-breaking order is about the size of the gap (56.0 with three tiers at four runs). So folds in place of repeats give the certificate for no extra tokens, at no measured cost in score, though small losses are not excluded. On the 75 tasks whose first sample did not verify, 33 of 225 resamples verify, 22.0 right, and 24 of 226 folds pass, 19.5 right: −0.011 [−0.041, +0.018] per run, so an earlier hint that folds beat resampling there did not replicate.

**Stopping (descriptive, a replay of logged runs on a seen split, not a forecast).** Score of 120 at 128k tokens per task: one pass with no stopping 49.0, stop at first verified 47.2, stop only when certified 46.5. At 192k: 55.0, logged runs exhausted (48.2 at 174k), and 52.0. Certification trails until about 290k, and only 7 tasks ever stop on it.

### 6.4 Frames: they add solves, not trust

Behaviour module alone (Table C1), `canon` minus `abs`: +6 [+1, +12], +4 [+1, +8], 0 pass@2 items on ConceptARC, Mini-ARC, 1D-ARC, with every discordant task going to `canon` (planned sign tests p = 0.06 and 0.13; 9:0 summed, p = 0.004, descriptive). This tests pose normalisation only, since `abs` keeps the object anchor. `canon` minus `global`, a weak baseline, is +6 [−1, +14] ns, +10 [+3, +18], +168 [+48, +313]. These solves are mostly not confident: of the 6 ConceptARC items only `canon` solves, 2 have a right top answer at evidence ≥ 0.99; of Mini-ARC's 4, none has evidence ≥ 0.99. At system level, `canon` minus `abs` in FA-LOO precision on ConceptARC is −4.5 [−12.5, 0.0] ns. Frames widen what can be reached; they do not tell the solver when it has reached the right thing.

### 6.5 Voting: a portfolio, and little power on the vote

**A portfolio.** Almost every Monty-ARC solve belongs to one module: 57/58, 15/20, 197/198 (Table C3); Mini-ARC falls below the plan's 80% line. Which module matters flips with the set (Appendix A). The vote gains and loses no item against the modules run alone, and a baseline with no pooling and no voter counts solves the same items at a precision that does not separate.

**The limit of this test (post hoc).** Modules differ in kind, so they rarely answer alike: 11 of 518 top answers, 7 right. All 9 answers the 2:1 rule vetoes on the unseen real roles are hypotheses of one module disagreeing; they are wrong 4 of 9 times against 18 of 238 kept (Fisher p = 0.004, items treated as independent), an ambiguity signal, not a vote. So voting between modules was barely exercised, and this null has little power.

**Copies.** Voting over eight D8 views counts one module's views as separate voters. Wrong answers rise in 4 of 6 populations (Table C4; +14 [+5, +24] on 1D-ARC's demo roles, +5 [+2, +9] on its real role). One voter per module, or FA-LOO, removes nearly all of them, so the mechanism is double counting. Gains are small: pass@2 changes by +2 [0, +5], 0, +2 [0, +6] on real roles and +12 [+2, +25], +3 [0, +7], +3 [0, +9] on demo roles, at 8.2–8.5× the CPU. Under an abstention threshold copies cost precision.

**A closer arm (post hoc).** The nearest thing here to columns sensing one object differently is the folds. Requiring them to agree on the test, with no held-out check, gives 39/54, 11/13, 166/178: +14.1 [−1.1, +29.3], +32.9 [+7.5, +57.4], +27.6 [+13.2, +44.6] over fit-only. Held-out prediction adds to it: 204 of 225 with both, 12 of 20 with agreement alone. This is not voting in Monty's sense, which speeds up 3D inference [5].

### 6.6 What is missing

Six ConceptARC groups (AboveBelow, Count, HorizontalVertical, InsideOutside, Order, SameDifferent) give Monty-ARC 1 of 180 test pairs, against 83–91% for humans. On all 480 pairs it solves 58 and the 2020 program 249 by the ConceptARC authors' count; humans average 91% (attempt rules differ). On ARC-AGI-2 public evaluation, 109 of its 116 unsolved tasks get no candidate. Judged: no module has numbers or orderings, a gap no reference frame would fill; every task learns alone; and LLM-assisted labels of the 116 point to composition (20%) and counting and relations (17%) first. The 2020 program solves 8–21 of 30 in those six groups, so the shortfall is at least partly primitives.

## 7. The named submission

Tri v3 (Table 1) runs offline on 4×L4 GPUs for 12 hours less a 10-minute buffer.

- **Qwen3.8-27B program synthesis, up to 4.5 h.** FP8 weights on vLLM across the four GPUs, up to 20 concurrent requests. One sample per task (temperature 1.0, top-p 0.95, top-k 20), at most two rounds, 16,384 thinking tokens per round plus 6,144 for the answer, a 10 s sandbox, cell-by-cell feedback, reverse alphabetical order.
- **NVARC fork, until the deadline.** A public fork (mikelou1's performance patch of the 33.89 baseline) of NVARC [8]: pretrained Qwen3-4B, per-task LoRA test-time training with 128 augmentations, depth-first decoding with 16, rescoring. It skips tasks with a verified Qwen program.
- **Monty-ARC v5, CPU throughout.** Code byte-identical to the frozen system, one view, low priority, a 120 s per-task alarm. A stale comment in that cell says "voted across D8 perspectives"; the code does not.
- **Merge, per test output.** Verified Qwen output; confident Monty-ARC answer; NVARC's candidates; then unverified Qwen output, a verified program's second grid and Monty-ARC guesses. The first two distinct grids are kept.

**The notebook does not contain FA-LOO.** The certificate was evaluated offline, on the same Monty-ARC code and on canonical-order runs of the Qwen harness; the notebook samples at 16k in native order. The 2020 program is not in it. Kaggle exposes no logs of scored runs, so we cannot say how many hidden tasks Qwen verified. A 44-minute smoke run validated every phase on a few tasks; a full public-eval run was beyond our GPU quota.

**What the score means.** The named score lies inside the 28–34 band reported for unmodified NVARC forks [10], and so does the hybrid's. We therefore **cannot credit Qwen with the difference between them**. Monty-ARC's contribution is likely near zero. Its 0.00 is a generalisation gap, not a bug (its save run solves 30 of the 240 visible training tasks, a pipeline check, not a result). We can explain the score only by components: NVARC's pretraining plus per-task training [8], and checkable programs, where Qwen alone on public eval (TPU, 16k, one sample per task) scores 21.0 of 120, and 18.0 on a replicate run. A variant, v4-A, came from a simulator's +1.7 prediction and scored lower, so we report no simulated gains.

**What is trust for?** At these budgets, on one split, in a replay, trust did not buy score. ARC does not penalise wrong answers, so trust could pay in two ways. *Ranking* pays when candidates outnumber attempts, which is rare at one sample per task (Table C5): 7 of 167 test outputs have more than two distinct candidates, and every merge order, random ones included, scores 22–24 of 120 (19–21 on the replicate). With two samples, 58 are crowded and orders span 18.5–28.5. So order is worth about 1–2 points in the notebook's configuration. *Stopping* would move compute away from trusted answers, and stopping on a verified or certified answer earned no more than simply not stopping (Section 6.3). That negative result should save other teams time. Trust still tells you which answers to believe, at no extra tokens if folds replace repeats, which matters wherever wrong answers cost something.

## 8. What separates and what does not

- **Few answered tasks on ConceptARC.** FA-LOO rests on 18 tasks for Monty-ARC (11 all right, Clopper-Pearson [36, 83]%) and 6 for the 2020 program ([12, 88]%). Bootstraps over so few clusters are anti-conservative.
- **1D-ARC is near-copies.** Three types supply 142 of Monty-ARC's 172 FA-LOO answers, and the 2020 program cannot read 286 of its 901 tasks. **No multiplicity correction:** an interval just excluding 0 is weak evidence.
- **Exchangeability** looks imperfect on human-designed sets, jointly with (F) for Qwen. The sets other than ARC-AGI-2 are easier: humans score 91% on ConceptARC.
- **Not established:** that FA-LOO is more precise than v5 on Monty-ARC (the sign goes the other way); that voting among independent columns is useless; anything about the hidden set. Monty-ARC's 0.00 leaves the certificate untested there: at 2.6% coverage (3 of 114 ARC-AGI-2-only tasks), 240 hidden tasks would give about six answers.

## 9. Conclusion

When can a solver's answer be trusted? When a learner that did not see a demonstration still predicts it and its re-runs agree. The held-out split separates right from wrong by 45–75 points on three kinds of learner, including a program frozen before the sets existed. Fold agreement adds a proof; it is implied for first-fit enumerators and does real work where folds can differ. On human-designed sets, where (E) looks imperfect, only the rule's measured value remains. Object frames extend reach and buy no trust; voting between modules was barely exercised; what fails first in Monty-ARC is relations and counting. The rule needs only a re-runnable learner: it has been tried here on a hand-written enumerator, an LLM and a classical search, and by CORA [11] on a per-task neural learner, but we have no test outside ARC-style tasks.

**What other teams can use.** We offer no way to solve more tasks: Monty-ARC scores 0.00 and nothing here reaches 85%. The usable results are these.

1. *At these budgets, on one split, in a replay, trust did not buy score:* ranking is worth 1–2 points at one sample per task, and stopping on a verified or certified answer earned no more than not stopping.
2. *Verified is not right:* on ARC-AGI-2, Qwen's verified programs are right 72–78% of the time across our runs.
3. *Held-out prediction sorts programs without test labels,* across learners (Table 5). Its rate alone ranks weakly; the full rule answered 72 of 72 right on Qwen.
4. *The certificate can replace repeats:* no extra tokens, no measured cost in score, small losses not excluded.
5. *Checks:* the discordant test shows whether tests differ from demonstrations; rotating roles among demonstrations estimates precision on hidden data.
6. *Nulls:* perception notes in the Qwen prompt (+2.1 per 120 tasks [−1.7, +6.0]); D8 voting under a threshold.

**Next tests, on fresh data only:** FA-LOO per module, not per system; modules with relations and counts.

"""
s = BODY + tail
# references
a = "[20] Y. Zhou, Y. Tan, S. Xu, Z. Li, Y. Yao, T. Chen, X. Ma. Task Abstention for Large Language Models in Code Generation. arXiv:2605.17029, 2026.\n"
assert s.count(a) == 1
s = s.replace(a, a + "\n[21] J. S. Wind. DSL solution to the ARC challenge, first place in the Kaggle Abstraction and Reasoning Challenge. github.com/top-quarks/ARC-solution, 2020 (commit 9407072; MIT licence; code not included here).\n")
# appendix A: figures
a = "*Figure A1, to draw: same content for ConceptARC as `research/paper/figures/heldout_modules.png`, with its development series replaced by public eval. Figure A2, to draw: FA-LOO as a flow, and a 4×4 grid of $L(a,b)$ with one pair's row and column highlighted, showing why two rows cannot both be all ones.*"
assert s.count(a) == 1
s = s.replace(a, "*Figure A1, to draw: same content for ConceptARC as `research/paper/figures/heldout_modules.png`, with its development series replaced by public eval. Figure A2, to draw: FA-LOO as a flow, and a 4×4 grid of $L(a,b)$ with one pair's row and column highlighted, showing why two rows cannot both be all ones. Figure A3, to draw: `research/paper/figures/heldout_precision_by_rule.png`, real role, with public eval in place of its development series.*")
# appendix C additions
a = "## Appendix D. A note on ARC-AGI-3"
assert s.count(a) == 1
s = s.replace(a, r"""**Table C6. Monty-ARC, acceptance rules, real role. Correct/answered = precision [95% CI]. On every set shown, plain (a) answers exactly the same items as FA-LOO.**

| Rule | Public eval (seen) | ConceptARC | Mini-ARC | 1D-ARC |
|---|---|---|---|---|
| Fit-only | 43/65 = 66.2% [54.2, 77.4] | 43/74 = 58.1% [41.4, 73.4] | 15/29 = 51.7% [33.3, 70.0] | 187/285 = 65.6% [39.5, 82.1] |
| v5 heuristic | 35/36 = 97.2% [90.6, 100.0] | 42/49 = 85.7% [74.2, 95.2] | 11/11 = 100% | 167/178 = 93.8% [82.9, 98.3] |
| FA-LOO | 41/42 = 97.6% [92.1, 100.0] | 35/44 = 79.5% [64.4, 92.3] | 8/9 = 88.9% [63.6, 100.0] | 161/172 = 93.6% [79.1, 98.3] |
| FA-LOO minus fit-only, points | +31.5 [+20.6, +43.1] | +21.4 [+3.3, +40.3] | +37.2 [+8.7, +62.5] | +28.0 [+13.4, +45.7] |
| v5 minus fit-only, points | +31.1 [+20.1, +42.9] | +27.6 [+11.3, +45.4] | +48.3 [+30.0, +66.7] | +28.2 [+13.4, +47.0] |
| FA-LOO minus v5, points | +0.4 [0.0, +1.6] ns | −6.2 [−15.1, +1.8] ns | −11.1 [−36.4, 0.0] ns | −0.2 [−4.2, +0.1] ns |
| Coverage, FA-LOO; pass@2, always answering | 8.2%; 9.5% | 9.2%; 12.1% | 6.0%; 13.4% | 19.1%; 22.0% |
| FA-LOO, clusters weighted equally; fit-only | | 76.9%; 51.4% | 88.9%; 51.7% | 75.9%; 45.0% |

Where FA-LOO and v5 disagree (post hoc), answers only v5 gives are right 22 of 23 times and answers only FA-LOO gives 6 of 10: a system-level wrapper pays for competition between modules. Against v5 the cost is 3.6× the CPU (2.6× for the folds). Without 1D-ARC's three dominant types, FA-LOO is 23/30 and fit-only 56/150. On ConceptARC, FA-LOO is 13/19 at $n=2$ and 22/25 at $n\ge3$; on the 120 ARC-AGI-2 tasks answers are too few to judge (FA-LOO 4/4, v5 3/3, fit-only 3/6). Evidence ≥ 0.99 against below uses the system's top answer. MinimalTasks (48 attention checks): FA-LOO and v5 5/5, fit-only 6/17.

**Table C7. ConceptARC per pair, FA-LOO and its parts. Qwen's prompt shows all three test inputs of a task; the others ran one pair per run.**

| Rule | Qwen3.8-27B | Monty-ARC | 2020 program |
|---|---|---|---|
| FA-LOO, (a)+(b)+(c) | 232/232 (over tasks 86/86, Clopper-Pearson [95.8, 100]) | 35/44 | 11/15 |
| (a)+(b) | 239/240 | 35/44 | 11/17 |
| Plain (a) | 249/264 = 94.3% | 35/44 | 14/21 |
| Fit | 417/450 = 92.7% | 43/74 | 152/310 |
| One attempt, no rule | 421/480 = 87.7% | top answer 55/136 | 182/480 |
| Coverage, FA-LOO; joint | 48.3%; 0/480 | 9.2%; 9/480 | 3.1%; 4/480 |

Where Qwen and Monty-ARC both answer, 23 pairs, Qwen is right on all and Monty-ARC on 18.

## Appendix D. A note on ARC-AGI-3""")
open(P, "w", encoding="utf8").write(s)
print("written")
