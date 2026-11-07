# FA-LOO on sampling Qwen3.8-27B at its natural budget (ARC-AGI-2 public eval, then ConceptARC)

Status: **complete, 2026-11-01 07:45 UTC.** All stages finished before the stop rule. FA-LOO (a)+(b)+(c) answered 7/120 ARC-AGI-2 and 65/160 ConceptARC tasks with no wrong answer, against 72.6% and 92.7% for verification alone. It does not raise pass@2 at the same tokens, its AUROC is weak, and exchangeability looks imperfect on both sets. Results start at section 1; section 0 is the plan, unchanged since it was written apart from its timestamp being corrected before any output existed.

## 0. Plan (written 2026-10-31 ~21:55 UTC, before any model output of this experiment existed; not edited afterwards)

**Question.** The paper says fold-agreement leave-one-out (FA-LOO) works for any learner, including LLMs. Its only LLM evidence is weak: greedy Qwen3.8-27B at 16k thinking per round, 20 demo-verified tasks, 5 certified (all right), all 5 wrong ones rejected, and a random 5 of 20 avoids all five wrong with p = 19%. This run tries to get better evidence, whichever way it comes out. A null or bad result gets reported as such.

**What was already known when this was written.** The greedy results (`faloo_qwen.md`, `faloo_qwen.json`), including that run's post hoc AUROC 0.91; plain stochastic results at 16k (`arc2_improve.md`); Monty's ConceptARC numbers (`research/monty_heldout.md`). No output of this run, on any task. The server code (below) was read; the servers were still compiling.

**Theorem respected.** Learner symmetric in its demos, randomness independent of the data, demos and test exchangeable: P(answer and wrong) <= 1/(n+1). The file `faloo_qwen.md`'s "Determinism caveat" conclusion is wrong and is not repeated here: determinism is not a premise (`research/paper/judge_review.md` §3.1, ERROR 1). Exchangeability stays the substantive premise, and this run does not test it.

### Learner
`research/arc2/faloo_qwen_sampling.py`. The `ps` harness of `llm/run_bench.py`: same system and instruction prompts, xhigh template, cell-diff feedback, sandbox with a 10 s timeout, `fast_generate` as in the greedy run. Canonical demo and query order through the unchanged `faloo_qwen.build`, so a fold prompt shows the held-out demo input as just another "Test input" in canonical position. Output = the first verified program, else the last round's program with code, run on every query.

- **Decoding:** sampling with the model-card settings `run_bench.SAMPLING["qwen38"]` (temperature 1.0, top_p 0.95, top_k 20).
- **Budget:** 32,768 thinking tokens per round, answer room 8,192, at most 2 rounds, so about 64k tokens per run and about 30-33M for stage 1 (479 runs). Checked against `arc2_improve.md` §3: on 16k, 99.9% of greedy rounds hit the cap; on `direct_b32768` 13.5% of runs ended naturally, so most rounds will still hit 32k.
- **Server:** vLLM-TPU 0.32, 2 servers × TP4 on a spot v6e-8, `--no-enable-prefix-caching`, `MAXLEN=98304`, `SEQS=40`. MAXLEN: the harness needs prompt + 32,768 + 8,192 <= MAXLEN; the largest prompt in the greedy run was 11,249 tokens, so 98,304 leaves 57,344 of prompt room and no round should be skipped for context. It is also the setting of the earlier 32k direct run. SEQS differs from `run_faloo.sh` (48) for two reasons: `run_faloo.sh` only ever ran about 40 per server, and with 40 the KV cache holds 948,769 tokens against about 930,000 at 48; the existing small XLA cache is also for 40.
- **Concurrency:** at most 36 rounds in flight per server, least-loaded server first, round starts staggered (gap = mean round time / 36). Reason: 40 sequences all at 33k need 1.4M KV tokens; the earlier 32k direct run did that and fell to about 20 tok/s per sequence, against about 46 at 16k. Staggered sequences average about 20k, about 730k in total. These settings affect speed, not the distribution of any single run.

### Seeds and randomness
**Per-request seeds cannot reach this server.** vLLM-TPU rejects them (`tpu_inference/platforms/tpu_platform.py`: `raise ValueError("JAX does not support per-request seed.")`, the HTTP 500 noted in `arcllm/engine.py`), and the sampler draws from one server-wide stream (`tpu_runner._sample_from_logits`: `jax.random.split` each step, then one categorical draw per batch row). So the brief's "independent seed per job" is not possible as written. What is done instead:

- **Server stream:** each server of each VM boot gets `--seed = crc32(global seed 20261101 | VM name | port | boot time)`, written to a log. Nothing about tasks enters it.
- **Job label:** each round still computes `seed_of("qwen38", "ps", task id, "20261101|kind|fold", round)` and records it, with `seed_sent = false`. It labels the job and does not affect the output.
- **Why the premise still holds:** at each step every running sequence gets fresh noise from a key that does not depend on any prompt, and rows and steps do not share noise. So each run's tokens are sampled from the model's own conditional distribution, independently of the data and of other runs, as far as the PRNG is good. Which row and step a run lands on depends on timing, but picking among fresh draws does not make them depend on the data.
- **One real deviation, tiny and stated:** bf16 logits depend slightly on batch composition (`faloo_qwen.md`: greedy reruns match 10/20), and batches contain other jobs, including other folds of the same task.
- **Check after this plan is fixed, on a toy non-ARC prompt only, reported in an addendum:** the seed appears in the server's args; a request with `seed` returns the 500; the same toy prompt repeated on one server and across both servers gives different outputs at temperature 1.

### Jobs and stages
No selection by verified status in either stage: for every task, one full-data run A(D) and every fold A(D minus canonical demo i). Tasks run in a fixed pseudo-random order, `crc32("20261101|order|task id")`, full run first, so a partial stage is a random subset of tasks.

- **Stage 1 (primary):** all 120 ARC-AGI-2 public-eval tasks, 479 jobs (359 folds). Output `llm/results/qwen38_faloo_sampling_b32768.jsonl`.
- **Stage 2, only after stage 1 is complete and pulled to the laptop:** ConceptARC corpus, 160 tasks, 480 test pairs, 587 jobs (427 folds); third-party data, parsed as JSON only, nothing from it run. Output `llm/results/qwen38_faloo_sampling_concept_b32768.jsonl`. This is 0 pairs shared with Monty's development tasks.
- **Stage 2 differs from Monty's run in one way that matters:** one Qwen prompt shows **all three of a task's test inputs** (plus the held-out demo input in a fold), as in stage 1. Monty ran one test pair per run. Re-running Qwen per pair would take about 3× the tokens. The bound still holds per pair, since the other inputs are symmetric side information, but it is not the same learner setting, and test pairs of a task are less independent here than in Monty's run. The comparison is labelled that way.
- **The one ConceptARC task with a single demo** gets a fold with no examples and is not special-cased; (a) can pass only by luck.

**Spot handling.** Finished rounds are checkpointed, so a job killed in round 2 keeps round 1. Results and logs are pulled every few minutes. If two VMs happen to run the same job, the record kept is the one *started* first, not the one finished first, so the choice cannot depend on the outcome. A killed in-flight round is rerun, which favours short rounds slightly over long ones because long rounds are more often in flight. Restart counts are reported, and the results are also given for tasks with no restarted round (descriptive).

### Rules
For a task with n demos:
- **verified-only:** A(D) reproduces every demo; answer = A(D)'s output.
- **(a)+(b):** every fold predicts its held-out demo exactly, and all folds give the same non-null output on every test input; answer = that consensus. This is the rule the theorem covers.
- **(a)+(b)+(c):** also A(D) is verified and its output equals the consensus. It only removes answers, so the bound holds.

### Units (consistent with `faloo_analyze.py`)
- **Task level, primary for stage 1 and the greedy comparison:** one task is one unit; (b) needs the whole tuple of test outputs to agree; a multi-test task counts its fraction of test outputs right; Wilson intervals on the rounded count over answered tasks, as `faloo_analyze.py`; coverage over tasks with all jobs done.
- **"Right" and "wrong" for the hypergeometric test and the AUROC:** right = all of the task's test outputs right; wrong = anything less (as `qwen_auc.py`, so a half-right task is wrong).
- **Pair level, primary for the Monty comparison in stage 2:** one item is one test pair; (a) is per task; (b) and (c) per test pair; percentile cluster bootstrap by task, 10,000 resamples, fixed seed (as `research/monty_heldout.md`). Stage 1 also reports it (descriptive). Clopper-Pearson over answered tasks where the percentile CI degenerates.

### Primary comparisons
1. **Precision and coverage** of verified-only, (a)+(b), (a)+(b)+(c), with Wilson intervals by task, per stage.
2. **Rejection of verified-but-wrong.** Among verified tasks with all folds: how many wrong are rejected by (a)+(b)+(c), and the exact hypergeometric P(a uniformly random subset of the certified size keeps at most as many wrong). If 0 are kept this equals the C(V-W, C)/C(V, C) that gave 19% before.
3. **AUROC** of held-out rate (folds predicting their held-out demo / n) vs right, among verified tasks. Exact one-sided permutation p (ties by midranks), bootstrap CI by task. Last time it was post hoc (0.91, p = 0.002); **this run is its first prespecified test.** Stage 1 is the test; stage 2 is a second, separate one.
4. **By number of demos:** the same counts per n, and joint P(answer and wrong) vs the worst case 1/(n+1), overall against the mean of 1/(n+1). Task-level joint = sum over answered tasks of (1 - fraction right) / tasks; pair-level joint = wrong answers / pairs. The bound is a joint worst case and implies no precision.
5. **Greedy vs sampling on the same 120 tasks (descriptive only; it differs in both decoding and budget, so nothing can be attributed to either alone):** verified, certified, overlap of certified sets, held-out rate, A(D) right.
6. **Stage 2 only:** the same table next to Monty's (`research/monty_heldout.md` Table 1: FA-LOO + (c), (a) only, fit-only, coverage, joint, worst case, tasks answered / with a wrong answer), task-clustered CIs. Descriptive: Monty's v5 heuristic has no Qwen counterpart, and A(D) right once is not pass@2.

No correction for multiplicity. Comparisons 1-4 are the prespecified set; everything else is descriptive and labelled so.

### Checks before trusting anything
- `faloo_sampling_analyze.py --check-greedy`: reproduce every summary field and every row of `faloo_qwen.json` from the old greedy file. **Passed before this plan:** 12 summary fields and 120 rows, 0 mismatches; hypergeometric 0.1937, AUROC 0.913, exact p 0.0023.
- `faloo_qwen_sampling.py --selftest`: 2,132 job-round seed labels all distinct; job lists have no selection (479 and 587 jobs); prompts have no labels, canonical query order, no held-out or test outputs; the resumable harness equals `run_ps` on a fake engine, and a resume gives the same record. **Passed before this plan.**
- After the runs: record counts per kind and task, one record per job, error records listed, tokens per kind.

### Stop rule
Finish whatever is complete by **12:00 UTC on 2026-11-03** and report. Only tasks with all their jobs done enter a table; the number complete is stated, and a partial stage is labelled partial. A job that errors is retried; error records are never counted as answers.

### Deliverables
This file and `faloo_qwen_sampling.json`; `faloo_sampling_analyze.py`; raw JSONL in `llm/results/`; a paper sentence of at most 60 words, true to the result, including any weakness.

## Addenda (written after section 0 was fixed; section 0 is unchanged)

### Addendum 1, 10-31 22:09 UTC: seed check (toy non-ARC prompt, before any ARC job)
`research/arc2/vm/seed_check.py`, output in the VM's `seed_check.txt`:
- A request with `seed=123` returns **HTTP 500** on both servers, as the code says. Per-request seeds do not reach this server.
- Boot seeds are passed: `--seed 1683102096` (8001) and `--seed 141133583` (8003), in `server_seeds.log` and each server's log.
- Same prompt, temperature 1: 4 of 4 outputs distinct on 8001, 4 of 4 distinct on 8003, 0 shared across servers.
- Control, temperature 0: 1 distinct output across 2 runs on 8001 and 1 on 8003. So the variation comes from sampling noise.

### Addendum 2, 2026-10-31 23:06 UTC: new comparisons and stage 1b, from the lead (written before any fold-level test accuracy of this run was seen)
**What I had seen from this run when writing this.** Record counts, tokens, throughput and server metrics, and the log lines of the first 8 finished jobs, which give demo verification and cost (`verified=True n_ok=2 cost=...`). No test accuracy and no held-out result from this run has been computed or read, for any rule. The new comparisons below are motivated by the lead's look at the **old greedy** file (numbers quoted are from there), so they are planned for this run but not blind to the idea.

**Correction to section 0.** Section 0 says this run does not test exchangeability. P2 below does test it directly.

**P1, the held-out check inside fold programs (planned).** Fold programs verified on the n-1 demos they saw. Compare precision on test (fraction of test outputs right) of those that also predict the held-out demo against those that miss it. Per run: pooled over programs, difference with a cluster bootstrap by task (10,000 resamples, fixed seed). Per task: the mean over tasks of each group's within-task precision, and the mean paired difference on tasks with programs in both groups. Old greedy: 86 programs, 54.3%; 57 predict it, 78.1%; 29 miss it, 7.5%; +70.5 [+55.3, +84.6] over 54 tasks.

**P2, a direct test of exchangeability (planned, stages 1 and 2).** Every fold model, program or not (no program counts as wrong on both), has two kinds of unseen item. h = 1 if it predicts its held-out demo; t = fraction of the task's test outputs right. Under exchangeability and symmetry E[h] = E[t]. Report:
- mean h, mean t and mean(h - t) over all folds, cluster bootstrap by task;
- discordant counts, sum of h(1-t) and sum of (1-h)t, and their difference;
- exact two-sided sign test by task on the sign of the sum of (h - t) over the task's folds, tasks with sum 0 dropped.
Mean h is also the label-free estimate of test accuracy at n-1 demos, and is reported as that. Old greedy: 19.8% vs 14.5%, +5.2 [+2.2, +8.7]; discordant 23.0 vs 4.2; tasks 17 vs 4.

**Stage 1b, plain samples.** After stage 1 is complete and pulled, before stage 2. All 120 tasks, kind `plain`, fold = sample index 1, 2, 3, so 360 jobs, about 23M tokens. Same prompt, canonical order, sampling and budget as stage 1's `full`, which serves as plain sample 0. Same pseudo-random task order, no selection. Output `llm/results/qwen38_faloo_sampling_plain_b32768.jsonl`.

**P3, same-token score (planned, stages 1 + 1b).** For cap c in {2, 3, 4}, each task gets min(n+1, c) runs.
- **Plain arm:** samples 0, 1, 2, ... up to that number.
- **Fold arm:** the full run, then folds in a fixed pseudo-random order (ascending `crc32("20261101|p3|task id|fold i")`), up to that number.
- **Score:** pass@2 out of 120. Candidates per test output: verified programs first, then the others, each group in run order; keep the first two distinct non-null grids. In the fold arm a fold counts as verified only if it fits its n-1 demos and predicts its held-out demo.
- **Report:** each arm's score at each cap, the paired difference (fold minus plain) with a cluster bootstrap by task, and tokens actually spent per arm (`gen_tokens`).
- **Certificate:** FA-LOO is free only in the fold arm at full budget, so at cap 4 I state its coverage and precision on the tasks whose full fold set fits, n <= 3, and separately on all tasks at n+1 runs.
Old greedy, indicative only: 31.0 vs 31.5 of 114.

**Also from stages 1 + 1b.**
- **Yield (planned):** on tasks where sample 0 did not verify, per run: verified rate, precision, verified-and-right. Plain resamples (samples 1-3, verified on all demos) against folds (verified on n-1 and predicting the held-out demo). Cluster bootstrap on the difference in verified-and-right per run. Old: plain 32/354, 14.5 right; fold 26/301, 18.5 right.
- **Precision (planned):** plain verified (samples 0-3) against fold verified-and-held, per run, task-clustered.
- **Replay (descriptive only; a replay on a seen split, not a forecast).** Logged runs replayed at fixed mean token budgets (multiples of 32k per task, by `gen_tokens`). Passes over the tasks in the fixed task order; in each pass an active task consumes its next logged run; the replay stops once total tokens reach 120 x budget, or when logged runs run out, which is then stated.
  - (i) one pass, no stopping: plain samples 0-3, every task the same number.
  - (ii) stop a task at its first verified program: plain samples 0-3.
  - (iii) stop only when certified, otherwise keep sampling: full, folds in the P3 order, then plain samples 1-3; a task stops once (a)+(b)+(c) holds, and its certified answer goes first.
  - Scored with the same pass@2 rule as P3.

**Stop rule, replacing section 0's.** Stages 1 and 1b: whatever is complete by 12:00 UTC on 2026-11-03. Stage 2 may continue until 12:00 UTC on 2026-11-05. Stage 1 + 1b are reported as soon as they are done, without waiting for stage 2.

**Multiplicity.** No correction. P1, P2, P3 are planned; the rest stays as labelled.

### Addendum 3, 2026-10-31 23:10 UTC: what the old-data check of P1-P3 found (old files only; no test accuracy of this run seen)
My own code reproduces the lead's old-greedy P1, P2 and yield numbers exactly, except for two things worth knowing before reading P3:
- **P1's point estimate** is +70.6 (78.07 - 7.47); the lead's +70.5 is the centre of his bootstrap. My CI is [+55.3, +84.3]; his is [+55.3, +84.6]. The difference is the bootstrap seed.
- **The old fold-arm score depends on how candidates are ordered.** Same runs, 114 tasks: 31.0 with the lead's three tiers (verified-and-held, verified but missing, the rest) with folds in file order; 33.0 with three tiers in canonical order; 33.5 with the two tiers in Addendum 2 in canonical order. File order is finish order, which depends on the run, so it should not be used. **P3's primary is the two tiers and the fixed pseudo-random fold order, as written in Addendum 2**, chosen before seeing any of this run's accuracy. The three-tier score with the same fixed order is reported next to it as a sensitivity check.
- **The old plain score** is 31.0 with the "last round with a program" rule of `faloo_analyze.py` and 31.5 with the lead's script, which treats a last round without code as no program. This file uses the first rule throughout.
So a 2-point gap between arms in P3 can come from ordering alone.

## 1. Results, stage 1 (complete: 120/120 tasks, 479 jobs, 28.8M tokens, 0 error records)
Task level; a multi-test task counts its fraction of test outputs right; Wilson on the rounded count over answered tasks, as `faloo_analyze.py`.

| Rule | Answered | Right | Precision [95% Wilson] | Coverage of 120 |
|---|---|---|---|---|
| Verified only | 45 | 32.67 | 72.6% [59, 84] | 37.5% |
| FA-LOO (a)+(b), the rule the theorem covers | 9 | 9.0 | 100% [70, 100] | 7.5% |
| FA-LOO (a)+(b)+(c) | 7 | 7.0 | 100% [65, 100] | 5.8% |
| Verified but not certified | 38 | 25.67 | 67.5% [53, 81] | |

- **Rejection of verified-but-wrong (primary).** Of 45 verified tasks, 14 are not fully right; (a)+(b)+(c) certifies 7 and keeps none of the 14. A uniformly random 7 of 45 avoids all 14 with **p = 0.058** (19% in the greedy run). It also rejects 24 of the 31 fully right ones: the certificate is selective at a high cost in coverage.
- **AUROC of held-out rate vs right (first prespecified test): 0.705 [0.52, 0.87], exact one-sided p = 0.013.** The direction holds. The post hoc 0.91 from the greedy run does not hold at that size.
- **Joint P(answer and wrong):** 0 of 120 for both rules, against a mean worst case of 26.1%. The bound is a joint worst case, so this says nothing about precision beyond the table.
- **Pair level (167 test pairs, cluster bootstrap by task, descriptive):** (a)+(b)+(c) 7/7, 4.2%; (a)+(b) 10/10, 6.0%; (a) + A(D)'s answer 10/14 = 71.4% [43.8, 93.8], 8.4%; verified only 42/60 = 70.0% [55.7, 83.3], 35.9%. Clopper-Pearson over answered tasks: (a)+(b)+(c) 7/7 [59, 100]; (a)+(b) 9/9 [66, 100].
- **Fold agreement mattered here (descriptive).** (a) with A(D)'s answer gives 9 of 13 tasks all right; adding (b) gives 9 of 9. Two verified tasks with every fold predicting its held-out demo are wrong, `dbff022c` and `dfadab01`, and both are stopped by (b) or (c). This differs from Monty, where fold agreement added no measured precision. The two (a)+(b) answers without (c), `38007db0` and `c4d067a0`, are right while A(D) did not verify.

**By number of demos.**

| n | Tasks | Verified (right) | (a)+(b) (right) | (a)+(b)+(c) (right) | Joint | Bound 1/(n+1) |
|---|---|---|---|---|---|---|
| 2 | 34 | 11 (8.0) | 2 (2) | 1 (1) | 0 | 0.333 |
| 3 | 61 | 26 (18.17) | 6 (6) | 5 (5) | 0 | 0.250 |
| 4 | 18 | 7 (5.5) | 1 (1) | 1 (1) | 0 | 0.200 |
| 5 | 6 | 1 (1.0) | 0 | 0 | 0 | 0.167 |
| 6 | 1 | 0 | 0 | 0 | 0 | 0.143 |

**P1, the held-out check inside fold programs.** 146 fold programs verified on their n-1 demos, over 70 tasks, 62.1% right. The 99 that predict the held-out demo are 83.3% right; the 47 that miss it are 17.4%. Difference **+66.0 [+53.6, +77.9]** per run. Per task: 82.5% (51 tasks) vs 16.8% (36 tasks); on the 17 tasks with both kinds, +37.5 [+11.0, +61.8].

**P2, exchangeability.** Over all 359 folds: held-out demo right 118 = **32.9%** [26.3, 39.5], test right 100.17 = **27.9%** [21.9, 34.2], difference **+5.0 [+1.5, +8.6]**. Discordant: right on held-out only 28.5, right on test only 10.67, difference +17.83 [+5.5, +31.0]. By task 22 vs 9, **exact two-sided sign p = 0.029**. So exchangeability, the theorem's substantive premise, does not fully hold on this set: the test pairs are somewhat harder than the demos. As a label-free estimate of test accuracy at n-1 demos, the mean held-out rate reads 32.9% against a true 27.9%, an overestimate of 5.0 points. The size is the same as in the greedy run (+5.2).

**Greedy at 16k vs sampling at 32k, same 120 tasks (descriptive; decoding and budget both change, so neither can be credited alone).**

| | Sampling, 32k | Greedy, 16k |
|---|---|---|
| A(D) right, verified or not | 34.67 | 17.5 |
| Verified | 45 | 20 (16 in both) |
| Precision of verified | 72.6% | 77.5% |
| (a)+(b) | 9 | 5 |
| (a)+(b)+(c) | 7 | 5 (3 in both: `1818057f`, `2ba387bc`, `58490d8a`) |
| Fold held-out rate | 32.9% | 19.8% |

**Run checks.** One record per job, 120 tasks with all jobs, query ids all as expected, 838 rounds, 0 skipped for context (largest prompt 12,344 tokens), 37 rounds without code, 97.9% of rounds hit the 32k cap, `seed_sent` false everywhere. No KV-cache preemption in any of the 248 server metric samples, with peak KV use 87%. **Restarts:** 100 of 479 jobs were started more than once because of spot VM deaths, 35 continued from a checkpoint, 29 tasks had a restarted job. On the 91 tasks with none: verified 23.17/31 = 74.7%, (a)+(b) 7/7, (a)+(b)+(c) 6/6, so the picture does not change.

## 2. Results, stage 1b and the same-token comparison (complete: 360 plain jobs, 22.1M tokens, 0 error records; 8 jobs started twice, on 4 tasks)
Stage 1's `full` is plain sample 0. It behaves like samples 1-3: verified 37.5% vs 36.1%, right per run 28.9% vs 29.0%. Folds: verified on their n-1 demos 40.7%, right per run 27.9%, 59.7k tokens per run against 61.5k.

**P3, pass@2 out of 120 at the same number of runs per task (planned).**

| Runs per task, min(n+1, c) | Plain | Fold | Fold minus plain [95% CI] | Tasks better, fold : plain | Fold, three tiers (sensitivity) | Tokens plain / fold |
|---|---|---|---|---|---|---|
| c = 2 | 47.0 | 45.5 | -1.5 [-6.0, +3.0] | 2 : 5 | 45.5 | 14.5M / 14.6M |
| c = 3 | 55.0 | 52.0 | -3.0 [-10.0, +4.0] | 5 : 10 | 53.0 | 22.0M / 21.7M |
| c = 4 | 55.0 | 53.5 | -1.5 [-9.0, +6.0] | 7 : 10 | 56.0 | 27.4M / 26.8M |

No cap separates. Plain is ahead by 1.5 to 3 points at every cap with the planned ranking, and three tiers moves the sign at c = 4, so ordering alone is about the size of the gap (Addendum 3).

**The certificate, free only in the fold arm at full budget.** At c = 4, on the 95 tasks with n <= 3: (a)+(b)+(c) 6/6, 6.3% coverage; (a)+(b) 8/8, 8.4%. All 120 at n+1 runs: 7/7, 5.8%; 9/9, 7.5%.

**Yield on the 75 tasks where sample 0 did not verify (planned).**

| Per run | Runs | Verified | Precision | Right | Right per run |
|---|---|---|---|---|---|
| Plain resample, samples 1-3 | 225 | 33 (14.7%) | 66.7% | 22.0 | 0.098 |
| Fold, verified and predicts held-out | 226 | 24 (10.6%) | 81.3% | 19.5 | 0.086 |

Fold minus plain, right per run: -0.011 [-0.041, +0.018].

**Precision per run over all tasks (planned).** Plain verified, samples 0-3: 131.67/175 = 75.2% [66.1, 83.5]. Fold verified and predicting held-out: 82.5/99 = 83.3% [75.0, 90.9]. Difference **+8.1 [+0.5, +16.2]**.

**Replay, descriptive only: logged runs on a seen split, not a forecast.** pass@2 out of 120 at a fixed mean token budget per task. Policies as in Addendum 2. A dash means the logged runs ran out: (i) at 246k per task, final 55.0; (ii) at 174k, final 48.17; (iii) final 60.5 at 359k.

| Budget per task | 32k | 64k | 96k | 128k | 160k | 192k | 224k | 256k | 288k | 320k |
|---|---|---|---|---|---|---|---|---|---|---|
| (i) one pass, no stopping | 15.67 | 34.67 | 42.5 | 49.0 | 53.5 | 55.0 | 55.0 | - | - | - |
| (ii) stop at first verified | 15.67 | 34.67 | 40.17 | 47.17 | 48.17 | - | - | - | - | - |
| (iii) stop only when certified | 15.67 | 35.67 | 40.5 | 46.5 | 50.0 | 52.0 | 51.0 | 54.5 | 56.5 | 59.0 |

From 96k on, stopping at the first verified program does worse than not stopping at the same budget. Certification needs its folds first, so it trails plain from 96k until about 290k per task, past where plain's logged runs end, so the two cannot be compared beyond that; only 7 tasks ever stop on it. A score can fall as a budget grows, because a new verified program can push a right unverified grid out of the top two.

## 3. Results, stage 2: ConceptARC (complete: 160/160 tasks, 480 test pairs, 587 jobs, 19.8M tokens, 0 error records)
Every prompt showed all three of a task's test inputs, while Monty ran one test pair per run (section 0). 62.7% of rounds hit the 32k cap, so this set is easier for Qwen than ARC-AGI-2.

**Task level, as stage 1** (the whole tuple of three outputs must agree).

| Rule | Answered | Right | Precision [95% Wilson] | Coverage of 160 |
|---|---|---|---|---|
| Verified only | 150 | 139.0 | 92.7% [87, 96] | 93.8% |
| FA-LOO (a)+(b) | 70 | 69.67 | 99.5% [95, 100] | 43.8% |
| FA-LOO (a)+(b)+(c) | 65 | 65.0 | 100% [94, 100] | 40.6% |
| Verified but not certified | 85 | 74.0 | 87.1% [78, 93] | |

- **Rejection of verified-but-wrong.** Of 150 verified tasks, 22 are not fully right; (a)+(b)+(c) certifies 65 and keeps none. A uniformly random 65 of 150 avoids all 22 with **p = 9.6 × 10⁻⁷**. This is the strongest evidence in this file for the rule itself.
- **AUROC of held-out rate vs right: 0.584 [0.45, 0.72], exact one-sided p = 0.083.** It does not reach 0.05 on this set. The held-out rate alone ranks poorly here: 11 of the 87 verified tasks at held-out rate 1.0 are wrong.
- **What stops the wrong ones.** On ConceptARC, of 22 verified-but-wrong tasks: (a) stops 11, (b) stops 7 more, (c) stops the last 4. On ARC-AGI-2, of 14: (a) stops 12, (b) stops 2. So the held-out check alone is not the rule, and on ConceptARC half the work is agreement.
- **Cost of the rule.** It also rejects 63 of the 128 fully right tasks (ARC-AGI-2: 24 of 31).
- **The one wrong (a)+(b) answer.** `ExtendToBoundary/ExtendToBoundary2`, n = 3: all folds agree on a wrong grid for one of three test pairs. A(D) is right on all three, so (c) stops it.
- **Multi-test caveat.** At task level (b) requires all three outputs to agree, which is stricter than Monty's per-pair (b). The pair-level table below is the fair comparison.

**Next to Monty (`research/monty_heldout.md` Table 1), pair level, real test role, cluster bootstrap by task.**

| Rule | Qwen3.8-27B, sampling, 32k | Monty-ARC v5 |
|---|---|---|
| FA-LOO + (c) | 232/232 = 100% [100, 100]; Clopper-Pearson over tasks 86/86 [95.8, 100] | 35/44 = 79.5% [64.4, 92.3] |
| FA-LOO (a)+(b) | 239/240 = 99.6% [98.7, 100] | 35/44 = 79.5% [64.4, 92.3] |
| (a) only, with A(D)'s answer | 249/264 = 94.3% [90.9, 97.3] | 35/44 = 79.5% [64.4, 92.3] |
| v5 heuristic | no counterpart | 42/49 = 85.7% [74.2, 95.2] |
| Verified / fit to demos only | 417/450 = 92.7% [89.2, 95.7] | 43/74 = 58.1% [41.4, 73.4] |
| Coverage, FA-LOO + (c) | 48.3% | 9.2% |
| Joint, FA-LOO + (c) | 0/480 | 9/480 = 1.88% |
| Joint, (a)+(b) | 1/480 = 0.21% | 9/480 = 1.88% |
| Worst case, mean 1/(n+1) | 28.3% | 28.3% |
| Tasks answered / with a wrong answer, FA-LOO + (c) | 86 / 0 | 18 / 7 |
| Right without a rule | A(D), one attempt: 421/480 = 87.7% | pass@2: 58/480 = 12.1% |

**Overlap, FA-LOO + (c) per pair (descriptive).** Both answer 23 pairs: Qwen right on all, Monty right on 18. Qwen alone answers 209, all right. Monty alone answers 21, 17 right. By task: Qwen 86, Monty 18, both 12.

Do not read this as "the certificate is better on an LLM" without the caveats below. Qwen is simply much stronger on this set, with 92.7% verified precision before any rule, so there is little left to reject.

**By number of demos.**

| n | Tasks | Verified (right) | (a)+(b) (right) | (a)+(b)+(c) (right) | Joint (a)+(b) | Joint (a)+(b)+(c) | Bound 1/(n+1) |
|---|---|---|---|---|---|---|---|
| 1 | 1 | 1 (1.0) | 0 | 0 | 0 | 0 | 0.500 |
| 2 | 75 | 70 (62.0) | 31 (31) | 28 (28) | 0 | 0 | 0.333 |
| 3 | 61 | 56 (53.67) | 25 (24.67) | 24 (24) | 0.0055 | 0 | 0.250 |
| 4 | 22 | 22 (21.33) | 14 (14) | 13 (13) | 0 | 0 | 0.200 |
| 5 | 1 | 1 (1.0) | 0 | 0 | 0 | 0 | 0.167 |

**P1.** 409 fold programs verified on their n-1 demos, over 159 tasks, 84.0% right. The 321 that predict the held-out demo are 94.5% right; the 88 that miss it are 45.8%. Difference **+48.7 [+41.3, +56.3]**. Per task: 93.3% (140 tasks) vs 46.7% (68 tasks); on the 49 tasks with both kinds, +36.7 [+26.5, +46.9].

**P2, exchangeability, with the opposite sign to ARC-AGI-2.** Over all 427 folds: held-out right 325 = **76.1%** [70.9, 80.9], test right 346.67 = **81.2%** [77.2, 84.9], difference **-5.1 [-8.1, -2.1]**. Discordant: held-out only 18.67, test only 40.33, difference -21.67 [-34.7, -9.0]. By task 29 vs 46, **exact two-sided sign p = 0.064**. The bootstrap CI excludes 0 and the sign test does not. As a label-free estimate of test accuracy at n-1 demos, the held-out rate reads 76.1% against a true 81.2%, an underestimate of 5.1 points.

So the label-free estimate is off by about 5 points on both sets, in opposite directions. Exchangeability looks imperfect on both: test pairs are harder than the demos on ARC-AGI-2 and easier on ConceptARC. This run does not explain why.

**Run checks.** One record per job, 664 rounds, 0 skipped for context (largest prompt 4,361 tokens), 5 rounds without code, `seed_sent` false everywhere. An independent recount of the pair-level numbers from the raw JSONL with separate code matches exactly (240/239, 232/232, 450/417, 421). No test pair equals a demo of its task, and no test input equals a demo input. No ConceptARC program contains a long literal grid row. **Restarts:** 69 jobs were started more than once, almost all because the two VMs met in the middle; no VM died during this stage. The earliest-started record is kept. On the 142 tasks with none: verified 122/133 = 91.7%, (a)+(b) 59.67/60, (a)+(b)+(c) 55/55.

## 4. What this does and does not show
- **The rule holds up where it can be tested.** Across both sets, (a)+(b)+(c) answered 72 tasks with no wrong answer, and it rejected all 36 verified-but-wrong tasks. Against chance, p = 0.058 on ARC-AGI-2 alone and p < 10⁻⁶ on ConceptARC. Zero wrong answers is well under the theorem's worst case, which only bounds the joint probability and implies no precision.
- **Coverage on the set that matters is low:** 5.8% on ARC-AGI-2, and the rule discards most right answers there (24 of 31).
- **It does not raise the score.** At the same tokens, the fold arm did not separate from plain resampling on pass@2. Plain was numerically ahead on the planned ranking, and the CIs are wide (c = 4: -9 to +6). At c = 4 the fold arm spends about the same tokens as plain and gets the certificate on tasks with n <= 3, but it does not earn more points, and it could plausibly cost a few.
- **The prespecified AUROC is weak.** 0.705 on ARC-AGI-2, significant but well below the post hoc 0.91; 0.584 on ConceptARC, not significant.
- **Exchangeability, the only substantive premise, looks imperfect on both sets**, so the 1/(n+1) bound may not strictly apply to them.
- **Not established here:**
  - ARC-AGI-2 public eval is not a clean held-out set for this harness: its prompts and budgets were chosen on these tasks. ConceptARC was never used to choose anything here.
  - Both sets are public, and Qwen's training data is unknown to me, so memorisation is not excluded. No evidence for it was found beyond the absence of long literal rows in ConceptARC programs.
  - One decoding and budget only; the greedy comparison confounds both.
  - The randomness comes from a server-wide stream, not per-job seeds (Addendum 1), and batches mix jobs slightly through bf16 numerics.
  - Spot restarts favour short rounds slightly; the sensitivity checks above do not change the picture.

## 5. Paper sentence (58 words)
"Fold-agreement certification carries over to sampling Qwen3.8-27B: 7/120 ARC-AGI-2 tasks certified, all right (verification alone 72.6%; chance p = 0.058), and 65/160 ConceptARC tasks, all right (92.7%; p < 10⁻⁶). It shows no same-token score gain, and held-out and test accuracy differ by 5 points in opposite directions, so exchangeability, the theorem's premise, is doubtful on both sets."

## 6. Tokens, TPU resources, files
**Tokens:** stage 1 28.82M, stage 1b 22.13M, stage 2 19.85M, total **70.80M**.

| Request (node id) | Zone | Queued | Outcome | Final state |
|---|---|---|---|---|
| `arc-v6e-r` | us-east1-d | queued by the lead | ran stage 1, about 84 min | deleted by the lead, 11-01 06:05 UTC |
| `arc-v6e-r` | europe-west4-a | queued by the lead | about 20 min, no records of its own kept | deleted by the lead, 11-01 06:05 UTC |
| `arc-v6e-r2` | europe-west4-a | 10-31 22:45 | ran stage 1, about 3.4 h, 370 records | deleted by the lead, 11-01 06:05 UTC |
| `arc-v6e-r2` | us-east1-d | 10-31 23:12 | died during bring-up, about 25 min, no records | deleted by the lead, 11-01 06:05 UTC |
| `arc-v6e-r3` | us-east1-d | 10-31 23:42 | died within about 10 min, before any work | deleted by the lead, 11-01 06:05 UTC |
| `arc-v6e-r4` | us-east1-d | 11-01 01:14 | died during bring-up, about 17 min, no records | deleted by the lead, 11-01 06:05 UTC |
| `arc-v6e-r5` | us-east1-d | 11-01 01:46 | ran stages 1, 1b, 2 | **live, ACTIVE, VM READY, left running** |
| `arc-v6e-r3` | europe-west4-a | 11-01 03:38 | ran stages 1b, 2 | **live, ACTIVE, VM READY, left running** |

Nothing was deleted by this agent. The deletions above were done by the lead, on the user's direct approval to the lead. `lab-*`, `arc-v6e-q`, `arc-v6e` and `arc-ice-*` were not touched. No disks. Log: `research/arc2/logs/sampling/tpu_resources.txt`, `orchestrate.log`.

**Files.** Raw: `llm/results/qwen38_faloo_sampling_b32768.jsonl`, `_plain_b32768.jsonl`, `_concept_b32768.jsonl`, with `.ckpt.jsonl` and `.claims_*` beside them. Code: `research/arc2/faloo_qwen_sampling.py`, `faloo_sampling_analyze.py`, `vm/run_sampling.sh`, `vm/ship_sampling.sh`, `vm/merge_sampling.py`, `vm/orchestrate_sampling.py`, `vm/seed_check.py`. Numbers: `research/arc2/faloo_qwen_sampling.json`.
