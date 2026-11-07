# Generator control: three learners on fresh i.i.d. pairs from `re-arc`

Agent: generator-control. Section 0 was written on 2026-11-01 before any task of this experiment was generated and before any learner output on them. It is not edited afterwards; later changes go in marked addenda.

## 0. Plan (written before the tasks exist)

**Why.** The paper's theorem says that under symmetry (S), a learner fixed in advance (F) and exchangeability (E), P(answer and wrong) <= 1/(n+1). The second blind judge (`research/paper/judge_v8b/review.md` §3.1 gap 3) pointed out that no row in the paper has the bound biting with credible premises: where (E) and (F) are credible, coverage is below the bound, so it says less than "you cannot err more often than you answer"; where coverage is high (Qwen on ConceptARC), (E) is doubtful. Here (E) holds by construction, and (F) holds for the pairs, because they do not exist yet. This run also calibrates the paper's direct test of (E): held-out rate against test rate. The result is reported whichever way it comes out.

**What this test is not.** These generators reverse-engineer the 400 ARC-AGI-1 training tasks. Monty-ARC was developed on those tasks, solutions included, and the 2020 program's author saw them; Qwen's weights may know them. So high precision here says nothing about generalising to new concepts. This test is about the bound and its premises.

**Known when this was written.** All results in `research/paper/v8/paper.md`, `research/monty_heldout.md`, `research/icecuber_faloo.md`, `research/arc2/faloo_qwen_sampling.md`, `research/paper/judge_v8b/review.md`. From `re-arc`, read on the VM as text: `LICENSE`, `README.md`, `main.py`, `utils.py`, and import lines of the other files. No generator body was read, no generator was run, and `re_arc.zip` was not opened. No learner output on any re-arc pair exists.

### Data
- **Source.** `michaelhodel/re-arc`, commit `e5b7f1d06362a76f9d3b8c25154ff1fafca897ce` (2025-02-24). Licence checked on the VM: MIT, copyright 2024 Michael Hodel. Not copied into this project; it stays on disposable spot VMs. Only JSON comes back.
- **Generators.** `select_generators.py`: rank the 400 ids by `sha256("20261101|generator_control|select|<id>")`, take the first 200 in hash order. The sha256 of the comma-joined 200 in hash order is `dee8823b703e79a8ccd88444ab070bbb672dded008b842ab1c1b39ccfeb03f55`; the list is `generator_control/data/selected_generators.json`. Nothing about a task's content enters the hash. A generator that gives no valid tuple within its limit is replaced by the next id in hash order; the number is reported.
- **Settings.** `diff_lb = 0`, `diff_ub = 1`, the defaults of `generate_dataset` and the values behind the repository's published dataset. They were not chosen to help coverage, and they give large grids (often up to 30×30), which may hurt it. Each pair draws its own difficulty.
- **Tuples.** For each generator: `random.seed(sha256("20261101|generator_control|seed|<id>")[:16] as an integer)`, `PYTHONHASHSEED=0`, then 4 draws. Draws 1-3 are the demonstrations, draw 4 is the test, decided by draw order and nothing else. `n = 3`, so 1/(n+1) = 0.25 on every task. One test input per task.
- **What a valid draw is:** re-arc's own filter in `generate_dataset`: the generator returns, both grids pass `is_grid`, `verifier(input) == output`, `input != output`. An invalid draw is redrawn. So draws are i.i.d. from the generator's law given validity. Each call has a 120 s limit (a timed-out call counts as invalid), each generator 1,800 s.
- **One deliberate difference from `generate_dataset`.** It rejects a repeated input draw by draw. That would break exchangeability: with unequal probabilities, P(a then b) != P(b then a) under successive sampling without replacement. Instead the whole 4-tuple is redrawn if any two of its inputs are equal. That conditions an i.i.d. tuple on a symmetric event, so the tuple stays exchangeable. The number of rejected tuples is reported. Seeds are per generator rather than one global seed, so a task does not depend on the others.
- **Generated once,** on a disposable VM, saved as JSON, brought back as data, parsed with `python -I` by scripts outside the data folder. Output: `generator_control/data/rearc_tasks.json`, plus one file per task in `generator_control/data/tasks/` in ARC format.
- **Checks, reported before any learner runs (Addendum).** Inputs distinct within a task; all grids 1-30 per side, cells 0-9; exact-pair overlap with Monty-ARC's 1,147 development tasks (`arcmonty.data.SPLITS`), with ConceptARC, Mini-ARC, 1D-ARC, MinimalTasks and with the repository's own `re_arc.zip` (that last one on the VM); grid area and difficulty by draw position (a sanity check of identical distribution). Tasks with an overlapping pair stay in, and a sensitivity row without them is given. No task is dropped for any other reason.

### Learners, all unchanged, all run on the same 200 tasks
- **Qwen3.8-27B.** The harness of stage 2 of `faloo_qwen_sampling.py`, imported, not edited: `ps` harness, xhigh template, sampling (T 1.0, top-p 0.95, top-k 20), 32,768 thinking per round, answer room 8,192, at most 2 rounds, canonical demo and query order through the unchanged `faloo_qwen.build`, 2 servers × TP4, `SEQS=40`, `MAXLEN=98304`, no prefix cache, at most 36 rounds in flight per server, server seed per boot, no per-request seed. Output = first verified program, else the last round's. Jobs: `full` and all 3 `fold`s per task, 800 jobs, in the fixed order `crc32("20261101|order|<task id>")`, so a partial run is a random subset of tasks. Spot handling as there: finished rounds checkpointed, earliest-started record kept, restarts reported.
- **The 2020 program.** `top-quarks/ARC-solution` at commit `9407072659de1270358c2ba34c527785214dd68b`, as in `research/icecuber_faloo.md` §0: one call `f(S, q)` = `./run 0 3`, `0 23`, `0 33`, `0 4` on canonical-order demonstrations and one query, merged as `safe_run.py`, 16 GiB and 3,600 s per process, at most 150 processes per VM and at most 80 depth-4 (fewer may be used when a VM also runs Qwen; only speed changes). VMs only. Runs: 1 full + 3 folds × 2 queries = 7 calls per task, then the rotation, 16 calls per task in all.
- **Monty-ARC v5.** Frozen `arcmonty/`, imported unchanged, wrappers only, on this Mac with 4 workers, on JSON data: `run_cache.run` and the `rules.py` re-vote with one view, every role and fold cached. Candidates, rules and thresholds as in `research/monty_heldout.md`.

### Rules, real test role, as each learner's earlier plan defines them
- **Top answer:** the learner's best answer on all 3 demonstrations, if it has one (Qwen: output of `full`; 2020 program: first of the merged list; Monty-ARC: top of `vote.pool`).
- **Fit:** Qwen, `full` verified on all demonstrations. 2020 program, top answer whose score shows it fits all demonstrations. Monty-ARC, its fit-only rule (`full_outcome["fit"]`, as in the paper), with the top-1 form in the JSON.
- **Plain (a):** every fold predicts its held-out demonstration; the answer is the full-data one.
- **(a)+(b):** also all folds give the same non-null test answer; the answer is that one. This is the rule the theorem covers.
- **(a)+(b)+(c), "FA-LOO + (c)":** also the full-data answer equals it (Qwen: and `full` verified, as in its plan).
- **Monty-ARC only:** the v5 heuristic, as an extra row.
Abstaining counts as wrong on a fold.

### Analysis
One item = one task = one cluster (generators are distinct). Percentile cluster bootstrap by task, 10,000 resamples, seed 0, from `research/monty_heldout/stats.py`; Clopper-Pearson over tasks where the percentile interval degenerates. "Separates" means a 95% interval excludes 0. No correction for multiplicity.

**Table per learner, plus one combined.**
1. For each rule: correct/answered, precision, coverage, CI.
2. Joint P(answer and wrong) against 0.25, with a Clopper-Pearson interval.
3. **Floor** `1 - 0.25/c` for (a)+(b) and (a)+(b)+(c), with a bootstrap interval on c: does it exceed 0, that is, c > 0.25? Stated next to measured precision.
4. **Held-out split.** Precision on the test of fold programs that give a test answer, those that predict the held-out demonstration against those that miss it, pooled, and within tasks that hold both kinds (mean paired difference over tasks). Qwen as P1 of its plan (fold programs verified on their 2 demonstrations), and also over all fold programs with an answer; the 2020 program as its Comparison 2 (all, and fit only); Monty-ARC by fold top answers, and also its earlier measure, top answer at evidence >= 0.99 against below.
5. **The test of (E).** Over all 600 real-role folds, abstaining = wrong: mean h, mean t, **mean(h - t) with a cluster bootstrap CI.** Discordant counts are descriptive. **No 50:50 sign test** (review §3.3 Error 1: it has the wrong null under (E)). The primary is the mean.
6. **(b) failures** among roles passing (a), and how many of them with a fold abstaining.
7. **Role rotation** where all roles exist: Monty-ARC and the 2020 program, always; Qwen only as below. Models M_ab for all 6 unordered pairs of the 4 pairs. For a task, D_r = sum over i != r of [M_ir right on i - M_ir right on r]. Check Σ_r D_r = 0 for every task (an identity under (S)). **Exact role-permutation test of the mean:** under (E), (S), (F) the real role is uniform on the 4 and independent across tasks given each task's pairs, so the exact null of Σ_tasks D is the convolution of the tasks' four values; two-sided p = P(|S| >= |S_observed|). **At-most-one-event check:** count tasks with 0, 1, >= 2 events E_a, every confident error must be an event on its role. **Role-averaged joint rate and coverage** for (a)+(b), and with (c) where full runs on each role exist; role-averaged floor; mean over roles of the joint is <= 0.25 by the argument's step 1, deterministically, so it checks the code.

**Qwen rotation, only if the VMs are up, after everything else is finished, and labelled as such.** 3 more models per task: M_ij for demonstrations i < j, trained on the other demonstration and the test pair, queries x_i, x_j in canonical order. 600 jobs. It gives the same permutation test, event check and role-averaged (a)+(b). No full runs on other roles, so no (c) there.

### What each outcome would mean
- **Any learner with more than one event on a task, or a failed identity, or a joint rate whose interval lies above 0.25:** a bug, or (S) failing in code. I stop and find it before reading anything else.
- **Coverage above 0.25 for a learner:** the first row where the bound is non-vacuous with the premises true. The floor is reported next to the measured precision, and it will be a weak floor at anything near 0.25. It is a claim about a joint worst case, not an estimate of precision. "Clearly" only if the interval on c lies above 0.25.
- **Coverage at or below 0.25 for all three:** the floor stays vacuous even under ideal premises. The paper's §5.3 must then say so in one sentence: on these budgets and solvers the bound says less than coverage does, even when its premises hold.
- **Mean h - t for Qwen:**
  - Under (E), (S), (F), E[h - t] = 0 exactly, because each fold's two items can swap roles and the prompt cannot tell them apart. So here this tests the *harness and learner*, not the data.
  - *Interval excludes 0:* either a 5% false alarm or an asymmetry in learner or harness (for example a broken (S)), which is then also a candidate explanation for the ±5 on the human-designed sets. "People choose test pairs" loses its support, and the paper says so.
  - *Interval includes 0 and half-width at most 5 points:* the harness shows no asymmetry of the size seen on ARC-AGI-2 (+5.0) and ConceptARC (−5.1), so that asymmetry belongs to those sets or to premises that hold here and not there. This does **not** establish that people choose test pairs. What remains: (F) on ARC-AGI-2, whose tasks the harness was built on; memorisation of published pairs; sibling test inputs on ConceptARC (below).
  - *Half-width above 5 points:* inconclusive, stated as such.
- **Mean h - t for Monty-ARC and the 2020 program:** the same logic. These have the exact test too. Their p-values here treat tasks as independent, which is true by construction here, unlike on the earlier sets.
- **The add-on:** below.

### Known confounds, stated now
- **Qwen's prompt.** One test input here, so a fold prompt shows exactly two queries (held-out input, test input). On ConceptARC each prompt showed three test inputs, and on ARC-AGI-2 one or two. So this control has no sibling inputs. If Qwen's h - t is zero here, this control cannot tell whether ConceptARC's −5.1 came from siblings or from how test pairs are chosen. I do not extend the design to test it.
- **The concepts are known** (above).
- **Grid sizes** differ from the other sets: large grids and a wide spread within a task. Budgets, prompts and limits are unchanged. Depth-4 runs of the 2020 program will hit their memory limit more often than on ConceptARC. Those processes give no lines and the other three configurations still count, as in its plan. Coverage may be lower for this reason.
- **Monty-ARC's (S)** is empirical, not by construction; the rotation's identity and at-most-one checks test it here.
- **Qwen's noise** comes from a server-wide stream, with bf16 numerics depending slightly on batch composition (`faloo_qwen_sampling.md` §0). Spot restarts favour short rounds slightly. Both as in earlier runs, reported.
- **Spot deaths and the 2020 program.** A process killed by the wall-clock limit is the only thing that can vary with load; counted.
- **Overlap.** Exact pairs may repeat an original ARC pair or a published `re_arc.zip` pair by chance on small grids. Counted; sensitivity row.

### Add-on, only after everything above except the Qwen rotation; on Qwen and ARC-AGI-2 public eval, seen split, post hoc
Motivation (review §3.3 and "A cheap add-on"): on ARC-AGI-2, 22 of 31 failing folds on right tasks did not fit even their own n-1 demonstrations, so they look like search failures. Retrying is part of the learner, symmetric and fixed in advance, so the theorem's form still applies; (F) and (E) stay doubtful on this set, as before, so this is about usefulness and not about the bound.
- **Learner A':** on the 45 tasks whose stage-1 `full` verified, each stage-1 fold that did not fit its own n-1 demonstrations (no program counts as not fitting) gets another sample with the same prompt, same harness, and if that does not fit, one more: at most two more samples per fold. A fold's output is the first sample that fits; if none fits, it stays the stage-1 output. Tasks whose `full` did not verify cannot pass (c) and are left alone.
- **Score:** task level, exactly as stage 1 (`faloo_sampling_analyze.task_row`), against stage 1's 7/7, coverage 5.8%; (a)+(b) on those 45 tasks too. Kept and rejected counts among the 14 verified-but-wrong and 31 fully right tasks. Tokens spent. About 100-150 runs, 5M tokens.
- **Reading:** coverage at 12 of 120 or more with no wrong answer: a better rule at no cost to the proof, on a seen split, needing replication. Near 7: search failure was not the bottleneck. Any wrong answer: the 7/7 was partly luck, and we say so.

### Checks before trusting anything
- Data checks above; a fake-engine self-test of the new job lists (prompts have no labels and no outputs, prompts equal `faloo_qwen.build` for `full` and `fold`, seed labels distinct).
- 2020 program: binary sha256 prefix `83641dc4619c48c4` as in the earlier run, or a rebuild with the same setup checked by it; repeat of a fixed sample of calls for determinism if time allows.
- Monty-ARC: a direct `monty_arc` run on a random 20 tasks equals the cached re-vote; demonstration reversal on the same 20 changes no fold answer.
- An independent recount of the main counts from raw files, by separate code.
- One record per job, error records never counted as answers, tokens per kind, rounds skipped for context, restarts.

### Stop rule
Report by **12:00 UTC on 2026-11-03** with whatever is complete, labelled. Only tasks with all their jobs enter a table. The lead gets a message as soon as Qwen's main table is ready.

### Resources and limits
TPU: `arc-v6e-r5` (lent, live), new requests `arc-v6e-r6`, `arc-v6e-r7`, ..., spot v6e-8 only, in us-east1-d or europe-west4-a, no persistent disks, at most 6 of my requests per zone, nothing ever deleted, no tokens on any VM. Everything from `re-arc` or a VM is untrusted data on the Mac. `arcmonty/`, `research/paper/`, `HANDOFF.md` and earlier results are not changed. At most 4 CPU workers on the Mac.

### Deliverables
This file and `research/generator_control.json`; scripts and raw results in `research/generator_control/`; the task JSON; one sentence of at most 60 words for the paper, true to the result, including any weakness.

## Addenda (written after section 0 was fixed; section 0 is unchanged)

### Addendum 1, 2026-11-01 14:15 UTC: the data, generated once, before any learner output
Generated on `arc-v6e-r5` by `vm/gen_rearc.py` at re-arc commit `e5b7f1d06362a76f9d3b8c25154ff1fafca897ce`, licence confirmed MIT (copyright 2024 Michael Hodel; `LICENSE` sha256 `60ea7c0e...`), `generators.py` sha256 `1f598cb1...`, `verifiers.py` `e11c1cee...`. Wall clock 8 s. File sha256 `f905b5e2767fd584...`, the same on the VM and the Mac. Checks by `make_tasks.py`, in `generator_control/data/checks.json`:
- All 200 planned generators gave a tuple; no replacement was needed. 833 generator calls, 33 invalid (32 failed re-arc's filter, 1 raised), 0 timed out. **0 tuples rejected**, so the whole-tuple rule never fired.
- 800 distinct pairs, inputs distinct within every task, all grids within 1-30 per side, cells 0-9, `input != output`. 4 tasks repeat an output within the task. 125 tasks keep the grid shape on all 4 pairs.
- **Identical distribution, sanity check.** Mean input area by draw position 293.7, 300.6, 311.5, 310.5 cells; mean re-arc difficulty 0.498, 0.490, 0.502, 0.502. Nothing to see. Input area is about 2.6 times ConceptARC's (115), and 248 of 800 inputs have a side of 26 or more.
- **Exact overlap.** 0 of 800 pairs with Monty-ARC's 1,147 development tasks (4,950 distinct pairs), and 0 inputs. 0 pairs with ConceptARC, MinimalTasks, Mini-ARC, 1D-ARC (1 input is shared with Mini-ARC, a pair is not). No pair repeats between the 200 tasks.
- **Overlap with the repository's published `re_arc.zip`:** 4 of 800 pairs, one each in `995c5fa3`, `feca6190`, `7fe24cdd`, `6e02f1e3`, all in demonstration positions, presumably because these generators have small output spaces. The sensitivity row drops those 4 tasks.
- The test pair is draw 4 by draw order. The data was not used to choose anything.

### Addendum 2, 2026-11-01 21:01 UTC: planned replication of the retry rule, from the lead, written before any of its runs
**Why.** The add-on (section 0) gave 15/15 at 12.5% coverage on ARC-AGI-2 public eval, against stage 1's 7/7 at 5.8%, post hoc on a seen split. The lead asked for a planned replication, ahead of Qwen's rotation.

**Known when this was written.** That result in full. From the stage 1b file: which tasks verified on plain sample 1 (45 tasks, 142 folds; 35 of the 45 also verified on stage 1's `full`). Earlier aggregate results over plain samples (`faloo_qwen_sampling.md` §2). I have not computed plain sample 1's accuracy on its own, and no new fold exists.

**Design, as the lead proposed; I see no better one at the same cost.**
- **Full-data run:** the logged plain sample 1 from stage 1b, `("plain", task, 1)` in `llm/results/qwen38_faloo_sampling_plain_b32768.jsonl`. It stands in for `full`. Same prompt and settings; it was drawn independently of stage 1's `full` and of the folds below. Chosen by index, in advance, not by result.
- **Tasks:** the 45 tasks where it verified. Tasks where it did not verify cannot pass (c) and get no runs.
- **Learner A':** the add-on's rule, unchanged. Every fold of those tasks gets a **fresh** sample, with no reuse of stage 1's folds or of the add-on's retries. A fold that does not fit its own n-1 demonstrations (no program counts as not fitting) gets another sample, and if that does not fit, one more: at most two more samples per fold. A fold's output is the first sample that fits; if none fits, it stays the first sample's output.
- **Settings:** the harness, prompts, budget and server settings of stage 1, imported unchanged. Job kind `rep`, fold code = i*100 + attempt (0, 1, 2), output `generator_control/raw/gc_qwen_rep.jsonl`, stages rep0, rep1, rep2; a later stage's job list is computed only when the earlier one is complete. Tasks in the fixed order `crc32("20261101|order|<task id>")`. Estimate: 142 first samples plus about 60 retries, about 12M tokens, somewhat above the 10M the lead estimated.
- **Not independent in every way:** same 120 tasks, same split, and 35 of the 45 tasks were also verified on the first run. The runs are a new draw; the tasks are not. **It stays a seen split, and any sentence about it says so.** (F) and (E) stay doubtful on this set, so this measures usefulness, not the bound.

**Primary, fixed now, task level with `faloo_sampling_analyze.task_row` as stage 1:**
1. (a)+(b)+(c): answered, right, with a Clopper-Pearson interval on fully right tasks over answered tasks; coverage of 120.
2. Verified-but-wrong (not fully right) tasks among the verified: how many are rejected; the hypergeometric P(a random subset of the certified size keeps at most as many wrong).
3. (a)+(b) on those verified tasks: answered, right.

**Secondary, planned:** the same counts on the same fresh runs with no retries (first samples only), which is the internal control for what retrying adds. Tokens, runs, folds that fit at each attempt.

**Descriptive:** overlap of answer sets with the first run's 15 and with stage 1's 7, and precision of the verified tasks.

**Reading, fixed now:**
- 12 or more answered of 120, with no wrong answer: the gain replicates, on a seen split.
- 8 to 11 with no wrong answer: a smaller gain than the first estimate, which is what regression to the mean would give.
- 7 or fewer: it does not replicate.
- Any wrong answer: reported with its task. The 15/15 was then partly luck, and the rule is not error-free even at this size.

**Order.** This runs before Qwen's rotation. The rotation's clients on `arc-v6e-r7` and `arc-v6e-r14` had been running for a few minutes and are stopped; those in-flight rounds are redone later, and any resulting restarts are counted.

### Addendum 3, 2026-11-01 23:39 UTC: how the run differed from section 0 and Addendum 2 (no rule changed)
- **`arc-v6e-r5` could not serve Qwen.** Two orphaned `VLLM::EngineCore` processes (PIDs 11073, 11081, parent 1, about 12 h old, from the earlier Qwen server) hold all 8 chips, so its servers failed with "Device or resource busy". The permission system denied my `kill -9` of them, and I did not work around it. r5 ran only the 2020 program and the re-arc generation. Qwen ran on other VMs.
- **The 2020 program ran with 130 workers, 70 of them depth-4** (the cap is 150 and 80), because I expected r5 to serve Qwen as well. Only speed changes. No process timed out.
- **Qwen's job order.** Most VMs took the list backward, because the orchestrator saw another VM on the same stage. Stage main finished, so no partial set arises. Both directions are fixed pseudo-random orders.
- **The orchestrator** was restarted several times with small fixes: re-detecting a client still in bring-up, not retrying a failed create every minute, keeping a failed create's name free. It is a copy, `vm/orchestrate_gc.py`; the original is unchanged. VM clients were not touched by the restarts. Stage main had 0 error records.
- **Addendum 2's last paragraph is wrong in one detail.** It says the rotation's clients were stopped. In fact no rotation client had started: `arc-v6e-r7` had just been preempted and `arc-v6e-r14` was still in bring-up. Nothing was stopped and no in-flight rotation round was lost.
- **The add-on cost less than estimated:** 55 runs and 3.4M tokens against 100-150 runs and 5M, because only 40 folds on the 45 verified tasks did not fit. The replication: 192 runs and 10.3M tokens against an estimate of about 200 runs and 12M.
- **Added after section 0, descriptive, none affects a rule.** `qwen_extras.py` (what stops verified-but-wrong tasks, restarts, KV preemptions, h - t against the other two sets); a repeat of 60 calls of the 2020 program (its planned determinism check, on a fixed random sample).
- **Dead requests were deleted by the lead,** never by me, on exact names I sent.

## 1. Results

Status: complete, 2026-11-02 03:45 UTC, before the stop rule. All 200 tasks are in every table. Qwen's rotation is complete and labelled as added.

**In short.** With the premises true, the bound bites for one learner of three. Qwen's rule answers 107 of 200 tasks, all right, at coverage 53.5% [46.5, 60.5], so the floor is 53.3% and the interval on coverage lies above 0.25. That is the row the paper lacked. The floor is far below measured precision, so it is a weak guarantee, and it is a worst case, not an estimate. Monty-ARC and the 2020 program answer too little (9.5%, 4.5%), so for them the bound stays vacuous even under ideal premises. Held-out and test rates do not separate for any learner (−1.0, −0.5, −1.3 points), and the code checks hold: no task has two events, and every wrong answer is an event. **These concepts come from ARC-AGI-1 training, so none of this says anything about new concepts.**

### Table 1. Combined, real test role, 200 tasks, n = 3, bound 0.25

| Learner | Top answer | Fit | (a)+(b) | FA-LOO + (c) | Coverage of + (c) | Joint of + (c) | Floor of + (c) | Mean h − t, points | Exact role p |
|---|---|---|---|---|---|---|---|---|---|
| Qwen3.8-27B | 163/189 = 86.2% | 159/171 = 93.0% | 111/111 = 100% | 107/107 = 100% | 53.5% [46.5, 60.5] | 0.00% | **53.3%** [46.2, 58.7] | −1.0 [−3.5, +1.5] | 0.569 (rotation, added) |
| 2020 program | 60/199 = 30.2% | 39/62 = 62.9% | 8/9 = 88.9% | 8/9 = 88.9% | 4.5% [2.0, 7.5] | 0.50% | vacuous (−456%) | −0.5 [−4.5, +3.7] | 0.836 |
| Monty-ARC v5 | 25/33 = 75.8% | 23/25 = 92.0% | 19/19 = 100% | 19/19 = 100% | 9.5% [5.5, 13.5] | 0.00% | vacuous (−163%) | −1.3 [−2.7, 0.0] | 0.146 |

Brackets are 95% cluster bootstrap intervals by task. On tasks all right, FA-LOO + (c) has exact intervals [96.6, 100] for Qwen, [82, 100] for Monty-ARC and [52, 99.7] for the 2020 program. The floor is 1 − 0.25/c, with its interval taken from the interval on c.

### Table 2. Qwen3.8-27B

| Rule | Correct/answered | Precision [CI] | Coverage [CI] | Tasks with a wrong answer | Joint [exact CI] | Floor |
|---|---|---|---|---|---|---|
| Top answer | 163/189 | 86.2% [81.1, 91.0] | 94.5% [91.0, 97.5] | 26 | 13.00% [8.67, 18.47] | |
| Fit (verified) | 159/171 | 93.0% [88.8, 96.6] | 85.5% [80.5, 90.0] | 12 | 6.00% [3.14, 10.25] | |
| Plain (a) | 113/118 | 95.8% [91.9, 99.1] | 59.0% [52.0, 66.0] | 5 | 2.50% [0.82, 5.74] | |
| (a)+(b) | 111/111 | 100% | 55.5% [48.5, 62.5] | 0 | 0.00% [0.00, 1.83] | **55.0%** [48.5, 60.0] |
| (a)+(b)+(c) | 107/107 | 100% | 53.5% [46.5, 60.5] | 0 | 0.00% [0.00, 1.83] | **53.3%** [46.2, 58.7] |

### Table 3. 2020 program

| Rule | Correct/answered | Precision [CI] | Coverage [CI] | Tasks with a wrong answer | Joint [exact CI] | Floor |
|---|---|---|---|---|---|---|
| Top answer | 60/199 | 30.2% [24.0, 36.7] | 99.5% [98.5, 100] | 139 | 69.50% [62.61, 75.80] | |
| Fit | 39/62 | 62.9% [50.8, 75.0] | 31.0% [24.5, 37.5] | 23 | 11.50% [7.43, 16.75] | |
| Plain (a) | 9/11 | 81.8% [55.6, 100] | 5.5% [2.5, 9.0] | 2 | 1.00% [0.12, 3.57] | |
| (a)+(b) | 8/9 | 88.9% [62.5, 100] | 4.5% [2.0, 7.5] | 1 | 0.50% [0.01, 2.75] | vacuous |
| (a)+(b)+(c) | 8/9 | 88.9% [62.5, 100] | 4.5% [2.0, 7.5] | 1 | 0.50% [0.01, 2.75] | vacuous |

### Table 4. Monty-ARC v5

| Rule | Correct/answered | Precision [CI] | Coverage [CI] | Tasks with a wrong answer | Joint [exact CI] | Floor |
|---|---|---|---|---|---|---|
| Top answer | 25/33 | 75.8% [60.0, 90.0] | 16.5% [11.5, 22.0] | 8 | 4.00% [1.74, 7.73] | |
| Fit-only rule | 23/25 | 92.0% [79.2, 100] | 12.5% [8.0, 17.0] | 2 | 1.00% [0.12, 3.57] | |
| Plain (a) | 19/19 | 100% | 9.5% [5.5, 13.5] | 0 | 0.00% [0.00, 1.83] | |
| (a)+(b) | 19/19 | 100% | 9.5% [5.5, 13.5] | 0 | 0.00% [0.00, 1.83] | vacuous |
| (a)+(b)+(c) | 19/19 | 100% | 9.5% [5.5, 13.5] | 0 | 0.00% [0.00, 1.83] | vacuous |
| v5 heuristic | 18/19 | 94.7% [82.4, 100] | 9.5% [5.5, 14.0] | 1 | 0.50% [0.01, 2.75] | |

### Table 5. The test of (E): each real-role fold, right on its held-out demonstration against right on the test. Abstaining counts as wrong.

| Learner | Folds | Held-out | Test | Difference, points [CI] | Half-width | Held-out only / test only |
|---|---|---|---|---|---|---|
| Qwen3.8-27B | 600 | 75.5% [70.5, 80.2] | 76.5% [71.5, 81.2] | −1.0 [−3.5, +1.5] | 2.5 | 27 / 33 |
| 2020 program | 600 | 21.2% [17.0, 25.7] | 21.7% [17.2, 26.5] | −0.5 [−4.5, +3.7] | 4.1 | 48 / 51 |
| Monty-ARC v5 | 600 | 12.0% [8.0, 16.3] | 13.3% [9.2, 17.8] | −1.3 [−2.7, 0.0] | 1.3 | 2 / 10 |

No sign test is reported (`research/paper/judge_v8b/review.md` §3.3 Error 1). Monty-ARC's interval touches 0; its exact role test does not separate.

### Table 6. Held-out split: right on the test, for fold programs that predict their held-out demonstration against those that miss it (number of programs)

| Learner, fold programs | Predict held-out | Miss it | Difference, points [CI] | Within a task, points [CI] (tasks) |
|---|---|---|---|---|
| Qwen, with a test answer | 94.0% (453) | 25.8% (128) | +68.3 [+59.2, +76.8] | +42.5 [+26.5, +57.8] (60) |
| Qwen, verified on what they saw (as P1) | 94.6% (447) | 40.3% (67) | +54.3 [+40.8, +66.9] | +28.6 [+9.7, +47.4] (42) |
| 2020 program, with a test answer | 62.7% (126) | 10.9% (466) | +51.8 [+39.9, +63.0] | +30.4 [+18.4, +42.9] (56) |
| 2020 program, and fit what they saw | 75.5% (98) | 22.7% (150) | +52.8 [+39.6, +65.1] | +36.4 [+20.6, +52.9] (33) |
| Monty-ARC, with a test answer | 97.2% (72) | 20.8% (48) | +76.4 [+62.2, +88.9] | +50.0 [+12.5, +87.5] (7) |

Monty-ARC's earlier measure, its top answer at evidence ≥ 0.99 against below: 19/20 = 95.0% against 6/13 = 46.2%, +48.8 [+18.6, +78.0].

### Table 7. Role rotation

Qwen's rotation was added after everything else finished, as the plan allowed: 600 jobs, 23.4M tokens. It has no full runs on other roles, so no (c) there.

| Learner | Identity broken | Tasks with 0 / 1 / ≥2 events | Events on the real role (expected) | Wrong (a)+(b) not an event | Mean h − t, real role | Null SD | Exact two-sided p | Role-avg (a)+(b): answered, precision | Role-avg coverage | Role-avg joint | Role-avg floor |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Qwen (added) | 0 | 190 / 10 / 0 | 0 (2.50) | 0 | −1.00 | 1.60 | 0.569 | 416/421 = 98.8% | 52.6% [46.8, 58.6] | 0.62% [0.12, 1.25] | **52.5%** [46.5, 57.4] |
| 2020 program | 0 | 188 / 12 / 0 | 2 (3.00) | 0 | −0.50 | 2.01 | 0.836 | 43/51 = 84.3% | 6.4% [3.8, 9.4] | 1.00% [0.38, 1.75] | vacuous |
| Monty-ARC v5 | 0 | 193 / 7 / 0 | 0 (1.75) | 0 | −1.33 | 0.87 | 0.146 | 79/86 = 91.9% | 10.8% [7.0, 14.9] | 0.88% [0.25, 1.50] | vacuous |

D_r is the sum over a role's folds of (held-out right − test right). "Identity broken" counts tasks where Σ_r D_r ≠ 0. The exact test: under (E), (S), (F) the real role is uniform on the 4 and independent across tasks, so the sum over tasks has an exact null by convolution. Tasks are independent here by construction, unlike on the earlier sets. Null SD is the null standard deviation of mean(h − t), in points. For the 2020 program and Monty-ARC, adding (c) on every role changes nothing.

### Reading, against section 0's list

- **Bug check: passed.** No task has two events on any of the three learners, the identity holds on every task, no wrong (a)+(b) answer falls outside an event, and every joint rate lies far below 0.25.
- **Coverage above 0.25: Qwen only, and clearly.** The interval on c, [46.5, 60.5], lies above 0.25, for (a)+(b) too (55.5% [48.5, 62.5], floor 55.0%). Rotating roles gives the same picture with more data: coverage 52.6%, floor 52.5%. This is the first row with a non-vacuous floor and premises true: (E) by construction, (F) for the pairs, because they did not exist when the learner was fixed. The measured joint is 0/200 (exact upper limit 1.83%) on the real role and 0.62% averaged over roles, against 0.25.
- **Coverage below 0.25: Monty-ARC and the 2020 program.** For them the bound still says less than "you cannot err more often than you answer", even under ideal premises. So the theorem's reach depends on the learner's coverage, not only on the premises.
- **Mean h − t for Qwen: the interval includes 0 and its half-width is 2.5 points, under the plan's 5; exact p = 0.57.** So the harness shows no asymmetry of the size seen on ARC-AGI-2 (+5.0) or ConceptARC (−5.1). That asymmetry belongs to those sets or to premises that hold here and not there. **This does not establish that people choose test pairs.** What remains open: (F) on ARC-AGI-2, whose tasks the harness was built on; memorisation of published pairs; and sibling test inputs on ConceptARC, which this control does not have (one test input per task, so it cannot separate them).
- **Post hoc, against those sets,** independent cluster bootstraps from their raw files: re-arc minus ARC-AGI-2 −6.0 [−10.4, −1.7]; re-arc minus ConceptARC +4.1 [+0.3, +7.9], which barely separates.
- **Mean h − t for the other two.** 2020 program −0.5 [−4.5, +3.7], exact p = 0.84; Monty-ARC −1.3 [−2.7, 0.0], exact p = 0.15, on only 12 discordant folds. Neither rejects (E), as they should not. The 2020 program's half-width (4.1) means a ±5 shift would only just separate. Monty-ARC's is narrow because its folds rarely answer.

### Other planned numbers

- **The real role flatters all three rows.** Rotating roles, (a)+(b) is right on 416/421 = 98.8% for Qwen (real role 111/111), 79/86 = 91.9% for Monty-ARC (19/19) and 43/51 = 84.3% for the 2020 program (8/9). None of the 10 Qwen events and none of the 7 Monty-ARC events fell on the real role, against 2.5 and 1.75 expected. That is not surprising by chance (probability about 6% and 13%), but the role-averaged figures, with four times the data, are the better estimates.
- **The sign test's null, measured (descriptive).** Tasks more held-out : more test, expected under the rotation null against observed: Qwen 19.25 : 25.75 against 19 : 24; 2020 program 28.25 : 36.0 against 28 : 37; Monty-ARC 3.0 : 7.0 against 1 : 9. So tasks lean to the test by construction, as the judge's Error 1 says, and a 50:50 sign test would be wrong here too.
- **What stops Qwen's verified-but-wrong tasks (descriptive).** Of 171 verified tasks, 12 are wrong. (a) stops 9, (b) 2, (c) 1, and none is kept. A random 107 of 171 avoids all 12 with p = 3.7 × 10⁻⁶. The rule also rejects 52 of the 159 right ones ((a) 47, (b) 5).
- **(b) failures among roles passing (a).** Real role: Qwen 7 of 118 (full-data answer right on 5, wrong on 2; no fold abstains; (c) then fails on 4 more); 2020 program 2 of 11 (1 right, 1 wrong); Monty-ARC 0 of 19. All roles: Qwen 28 of 449, 2020 program 8 of 59, Monty-ARC 1 of 87. So agreement does work on Qwen and the 2020 program and is nearly inert on Monty-ARC.
- **Sensitivity, without the 4 tasks sharing a pair with `re_arc.zip`:** Qwen 106/106 of 196, h − t −1.2; 2020 program 8/9, −0.3; Monty-ARC 18/18, −1.4.
- **Why Monty-ARC abstains:** on 173 of 200 tasks a fold has no answer at all; on 8 every fold answers but one misses; on 19 it answers.

## 2. The retry add-on and its replication (ARC-AGI-2 public eval, a seen split)

Task level, as stage 1. Neither run says anything about the bound: (F) and (E) stay doubtful on this set. It is about usefulness.

| | First run, post hoc (add-on) | Replication, planned (Addendum 2) | Replication's runs, no retries |
|---|---|---|---|
| Full-data run | stage 1 `full` | logged plain sample 1 | same |
| Verified tasks; of them wrong | 45; 14 | 45; 11 | 45; 11 |
| (a)+(b)+(c) | **15/15**, exact [78, 100] | **16/16**, exact [79, 100] | 11/11, exact [72, 100] |
| Coverage of 120 | **12.5%** (stage 1: 7/7, 5.8%) | **13.3%** | 9.2% |
| Verified-but-wrong rejected; hypergeometric p | 14 of 14; 0.0009 (stage 1: 0.058) | 11 of 11; 0.0034 | 11 of 11; 0.028 |
| (a)+(b) | 17/17 (all tasks; stage 1: 9/9) | 17/17 (verified tasks) | 12/12 |
| Runs; tokens | 55 extra; 3.4M | 192 (142 fresh folds, 50 retries); 10.3M | 142 |
| Folds that fit on a retry | 29 of 40 (23, then 6) | 22 of 33 (16, then 6) | |

**By the reading fixed in Addendum 2, the gain replicates: 16 answered, no wrong answer.** It is still a seen split. The runs are a new draw, the tasks are not: 35 of the 45 verified tasks were also verified on the first run, and 9 of the 16 answers are among the first run's 15. Retrying adds 5 tasks on the replication's own runs and 8 on the first run's, and it brings in no wrong answer in either. So search failure was a real part of the rejected right answers. Of the 29 retried folds that came to fit in the first run, 21 predict their held-out demonstration and 15 of those are right on the test; the 8 that miss it are right 0 times.

## 3. Run checks

- **Data:** Addendum 1.
- **Plan timing.** The first 16,919 bytes of this file (title, intro and section 0) have the sha256 `5eda96f7568caf06...` recorded at 14:10:12 UTC on 11-01 in `generator_control/logs/plan_hash.txt`, before any task was generated. I rechecked that it still matches. The hash is my own record, not an independent one.
- **Qwen, main:** 800 records, 0 error records, 30.6M tokens (7.9M full, 22.7M folds), 1,005 rounds, 741 hit the 32k cap, 33 without code, 0 skipped for context, largest prompt 6,785 tokens, `seed_sent` false throughout. By VM: `arc-v6e-r8` 416, `-r9` 64, `-r10` 89, `-r7` 231. **Restarts:** 223 jobs were started more than once and 28 resumed from a checkpoint, on 73 tasks. On the 127 tasks with none: fit 102/108, (a)+(b) 74/74, + (c) 71/71 (55.9%), h − t −1.8. An independent recount from raw files by separate code matches on all rules and on h and t.
- **Qwen, rotation:** 600 records, 0 error records, 23.4M tokens, 767 rounds, 576 at the cap, 19 without code, 0 skipped, largest prompt 6,820 tokens, 19 resumed; `arc-v6e-r14` 62, `arc-v6e-r21` 538. An independent recount matches: 421 answered, 5 wrong, 10 events, exact p = 0.5688.
- **KV-cache preemptions:** 30 across all Qwen stages, peak KV use 97.6%, unlike stage 1's zero; large grids likely explain it. Only speed should change.
- **Total Qwen tokens in this experiment:** 67.8M.
- **2020 program:** 3,200 calls, 12,800 processes, 121.5 core-hours, about 70 minutes on `arc-v6e-r5`. Binary sha256 prefix `83641dc4619c48c4`, as in the earlier run. No timeouts. Memory stopped 165 depth-4 processes. 21 calls gave no answer. 60 of 60 repeated calls gave the same list. Independent recount matches.
- **Monty-ARC:** frozen `arcmonty/`, 200 items, 0.93 CPU-hours, 14 minutes on 4 workers. A direct run of the system on 20 random tasks gives 80 of 80 answers equal to the re-vote, and reversing demonstrations changes none. Swapping query order changes none of the M_ab. Independent recount with only `vote.pool` matches.
- **Add-on and replication:** independent recount matches all counts.

## 4. What this does and does not show

- **Shown.** A row with the bound non-vacuous and premises true; a measured joint rate far below it; the theorem's deterministic checks hold on all three learners with all roles; the mean-based test of (E) does not fire when (E) is true, on three learners, with an exact version on all three.
- **Not shown: generalisation to new concepts.** The generators reverse-engineer ARC-AGI-1 training tasks. Monty-ARC was developed on them with solutions, the 2020 program's author saw them, and Qwen's weights may know them. 53.5% coverage is not a claim about unseen concepts.
- **Not shown: that precision is guaranteed at 100%.** The guarantee is the floor, about 53%. Measured precision is 107/107 on the real role and 416/421 for (a)+(b) across roles.
- **Not shown: why the rates differ on ARC-AGI-2 and ConceptARC.** This control removes a general harness asymmetry as the explanation, and nothing more. The sibling-input explanation for ConceptARC stays open, since these prompts have no siblings.
- **Limits of (S) and (F) here.** Qwen's noise comes from a server-wide stream, and bf16 numerics depend slightly on batch composition, as before; restarts favour short rounds slightly. (F) holds for the pairs; the generator code may be in Qwen's training data, which I cannot check. 4 of 800 pairs repeat a published `re_arc.zip` pair; dropping those tasks changes nothing.
- **Bootstrap intervals with no wrong answer** degenerate at 100%, so read the exact intervals there.

## 5. Sentences for the paper

Main (60 words):

> On 200 tasks from known generators, where exchangeability holds by construction and pairs are fresh, Qwen's certificate answered 53.5% with none wrong (rotating roles, 416/421), so the bound first bites (floor 53%), and held-out and test rates did not separate (−1.0 [−3.5, +1.5]). These concepts may be known to the learners; Monty-ARC (9.5%) and the 2020 program (4.5%) stay vacuous.

Add-on (51 words):

> Letting folds that do not fit their own demonstrations retry raised ARC-AGI-2 coverage from 7/7 (5.8%) to 15/15 (12.5%), post hoc; a planned replication with fresh runs gave 16/16 (13.3%), against 11/11 without retries. Both are on a seen split, where the theorem's premises stay doubtful, so this shows usefulness only.

## 6. Files and resources

**Files.** `research/generator_control.json`: all numbers. `research/generator_control/`: `select_generators.py`, `make_tasks.py`, `qwen_gc.py`, `retry_jobs.py`, `rep_jobs.py`, `analyse.py`, `retry_analyse.py`, `rep_analyse.py`, `qwen_extras.py`, `verify.py`, `make_report.py`; `vm/` (generation, orchestration and VM scripts, all copies; originals unchanged); `ice/` (run lists, runner copy, raw); `monty/` (wrapper, re-vote, cache, results); `raw/` (Qwen JSONL, per-VM mirrors); `data/` (the task JSON: `rearc_tasks.json`, `tasks/`, `checks.json`, `selected_generators.json`, `from_vm/`); `results/`; `logs/`.

**Third-party code.** `michaelhodel/re-arc`, commit `e5b7f1d06362a76f9d3b8c25154ff1fafca897ce`, MIT, copyright 2024 Michael Hodel; `top-quarks/ARC-solution`, commit `9407072659de1270358c2ba34c527785214dd68b`, MIT. Neither is in this project and neither ran on the Mac; both ran only on `arc-v6e-r5`. Only JSON and text came back, and results were read as data.

**TPU resources, 2026-11-02 03:40 UTC.** No credentials on any VM, no persistent disks. I deleted nothing.

| Request | Zone | State | Note |
|---|---|---|---|
| `arc-v6e-r5` (lent) | us-east1-d | **ACTIVE, VM READY, idle** | Ran the generation and the 2020 program. Third-party code in `/mnt/data/ice` and `/mnt/data/gc`. Two orphaned `VLLM::EngineCore` processes (11073, 11081) hold all its chips; my kill was denied by the permission system, and I did not work around it. |
| `arc-v6e-r21` | europe-west4-a | **ACTIVE, VM READY, idle** | Finished the rotation; Qwen servers still up. No third-party code. |
| `arc-v6e-r24` | us-east1-d | **PROVISIONING** | Queued by the orchestrator before the run ended; no work is left for it. It will sit idle if it comes up. |
| `arc-v6e-r23` | us-east1-d | SUSPENDED, VM PREEMPTED | Dead; can be cleared. |
| `arc-v6e-r6`, `-r8`, `-r9`, `-r10`, `-r14`, `-r19`; `-r13` | europe-west4-a | no longer listed | Cleared by the lead. |
| `arc-v6e-r7`, `-r11`, `-r12`, `-r15`, `-r16`, `-r17`, `-r18`, `-r20`, `-r22`; `-r13` | us-east1-d | no longer listed | Cleared by the lead. |

## Addendum 4, 2026-11-02 06:04 UTC: Stage C, Qwen on ConceptARC with one test input per prompt, from the lead, written before any of its runs

**Why.** The working bound (section 1) rests on known concepts, the retry rule on a seen split, and Qwen's −5.1 [−8.1, −2.1] on ConceptARC may come only from the sibling test inputs its prompts showed (`research/paper/judge_v8b/review.md` §3.1 gap 1). This run removes the siblings and changes nothing else.

**Known when this was written.** All of `research/arc2/faloo_qwen_sampling.md` §3 (stage 2 on the same tasks, with all three test inputs in each prompt), everything above in this file. No output of this stage exists. I have not computed stage 2's first-pair numbers.

**Learner.** Stage 2's harness and settings, imported unchanged (`faloo_qwen_sampling.py`, `faloo_qwen.build`): sampling, 32,768 thinking per round, at most 2 rounds, canonical order, same server settings. The only change: each task is given to `build` with only its first test input. So `full` shows one test input, and a fold shows that input plus its held-out demonstration input.

**Data.** All 160 ConceptARC corpus tasks, each task's first test pair by file order, 160 items, fixed by position and not by content. One `full` and every fold: 587 jobs (427 folds), about 20M tokens, in the fixed order `crc32("20261101|order|<task id>")`. The one task with a single demonstration gets a fold with no examples, as in stage 2. Stage `cmain`, output `generator_control/raw/gc_qwen_c1.jsonl`.

**Retries, after `cmain`.** The add-on's rule, unchanged: on tasks whose `full` verified, each fold that does not fit its own n−1 demonstrations (no program counts) gets another sample, then one more if needed; its output is the first sample that fits, else the first sample. Stages `cretry1`, `cretry2`, output `generator_control/raw/gc_qwen_c1_retry.jsonl`.

**Primary, fixed now. Task level, one test pair per task, with `faloo_sampling_analyze`'s `task_row`, `fold_views`, `p1_heldout_inside`; percentile cluster bootstrap by task, 10,000 resamples.**
1. **Mean held-out minus test** over all 427 folds, abstaining = wrong, with its interval and half-width. No sign test. Compared with stage 2's −5.1 [−8.1, −2.1], and, labelled as a comparison added here, with stage 2's folds scored on the same 160 first pairs only, plus the paired difference by task (stage C minus stage 2 first-pair).
2. **Fit, (a)+(b), (a)+(b)+(c):** correct/answered, Clopper-Pearson over answered tasks, coverage of 160 with interval, joint with exact interval, floor 1 − mean(1/(n+1))/c with mean(1/(n+1)) = 0.2832 over these tasks; verified-but-wrong rejected, hypergeometric p.
3. **Held-out split** among fold programs verified on what they saw, pooled and within tasks.
4. **The same rule table with retries:** coverage and any wrong answers.

**Reading, fixed now, on the interval of item 1:**
- **Includes 0 and excludes −5.1:** the −5.1 goes away without siblings, so sibling inputs explain it as far as this run can show. This is then a human-designed set, with concepts outside ARC-AGI-1 training, where the premises look credible and the floor may bite. The weights may still have seen ConceptARC (public since 2023), which I cannot check, so (F) is credible, not established.
- **Excludes 0 and includes −5.1:** it stays. Either tests really are easier than demonstrations on this set, or memorisation is at work, and the hypothesis about test selection stays open.
- **Includes both:** inconclusive between them, stated as such, with the point estimate.
- **Excludes both:** a partial effect, stated as such.
- **Coverage at or below 0.2832:** the floor is vacuous here, and I say so whatever the mean does.

**Caveats fixed now.** ConceptARC has now been seen by this project (stage 2 and others), though no setting here was chosen from it, and the retry rule was chosen on ARC-AGI-2. One pair per task is a different item set from stage 2's 480 pairs, so coverage and precision are not directly comparable; (b) here needs agreement on one output, not on three. Noise and restarts as in the earlier stages.

**Stop rule.** 12:00 UTC on 2026-11-03, whatever is complete, labelled. The lead gets the main table as soon as it is ready.

## 7. Stage C results (plan: Addendum 4)

*Filed by the lead from the agent's text. Section 7 supersedes the "sibling inputs stay open" lines in sections 1 and 4: that explanation is now ruled out.*


Status: complete, 2026-11-02 09:05 UTC. 160 tasks, each task's first test pair; 587 jobs plus 9 retries; 18.6M tokens; 0 error records.

**In short. Sibling inputs do not explain ConceptARC's gap.** With one test input per prompt, held-out minus test is −8.2 [−11.9, −4.5], half-width 3.7. By the reading fixed in Addendum 4 it stays: the interval excludes 0 and includes −5.1. Either tests really are easier than demonstrations on this set, or memorisation is at work, and test selection stays open as a hypothesis.

### Table 8. Mean held-out minus test, Qwen, abstaining = wrong

| Run | Held-out | Test | Difference, points [CI] |
|---|---|---|---|
| Stage C, one test input per prompt, 427 folds | 75.6% [70.6, 80.4] | 83.8% [79.8, 87.7] | **−8.2 [−11.9, −4.5]** |
| Stage 2, three test inputs per prompt, all pairs | 76.1% | 81.2% | −5.1 [−8.1, −2.1] |
| Stage 2, same 160 first pairs (comparison added in Addendum 4) | | | −6.8 [−10.3, −3.3] |
| Stage C minus stage 2 first pairs, paired by task | | | −1.4 [−4.8, +1.9], does not separate |
| re-arc, same harness, (E) true (section 1) | 75.5% | 76.5% | −1.0 [−3.5, +1.5] |
| re-arc minus stage C (post hoc) | | | +7.2 [+2.7, +11.6] |

Discordant folds, stage C: 13 held-out only, 48 test only. No sign test. The paired interval's upper limit of +1.9 excludes removing siblings closing a gap of 5 points.

### Table 9. Rules, stage C, mean(1/(n+1)) = 0.2832

| Rule | Correct/answered | Exact interval | Coverage [CI] | Joint [exact CI] | Floor 1 − 0.2832/c |
|---|---|---|---|---|---|
| Fit (verified) | 146/155 = 94.2% | [89.3, 97.3] | 96.9% [93.8, 99.4] | 5.63% [2.6, 10.4] | |
| (a)+(b) | 80/81 = 98.8% | [93.3, 99.97] | 50.6% [43.1, 58.8] | 0.63% [0.02, 3.43] | 44.1% [34.3, 51.8] |
| (a)+(b)+(c) | 79/80 = 98.8% | [93.2, 99.97] | 50.0% [42.5, 58.1] | 0.63% [0.02, 3.43] | 43.4% [33.4, 51.3] |
| (a)+(b), with retries | 81/82 = 98.8% | [93.4, 99.97] | 51.3% [43.8, 59.4] | 0.63% | 44.7% [35.3, 52.3] |
| (a)+(b)+(c), with retries | 80/81 = 98.8% | [93.3, 99.97] | 50.6% [43.1, 58.8] | 0.63% | 44.0% [34.3, 51.8] |

**Verified-but-wrong.** 8 of 9 rejected, hypergeometric p = 0.013; with retries, p = 0.012. **One wrong answer gets through, with and without retries: `AboveBelow/AboveBelow9`.** So this rule is not error-free on this set, unlike stage 2's 65/65 by task.

**Held-out split, fold programs verified on what they saw.** Predict held-out 96.0% (322), miss 48.4% (93), +47.6 [+37.9, +57.1]; within tasks +41.0 [+27.6, +54.5] (52 tasks).

**Retries add little here.** Only 8 folds on the 155 verified tasks did not fit, against 40 on ARC-AGI-2's 45; 8 of the 8 came to fit (7, then 1). Retrying adds 1 task, right, for 9 runs and 0.4M tokens.

### Reading

- **The floor.** Coverage is above 0.2832, so the floor is not vacuous by arithmetic: 43.4%. But item 1 rejects (E) for this learner, jointly with (F), so the floor is not a guarantee here. "Tests are easier" would not raise confident errors on the test role (judged, not measured), and the measured joint is 0.63%.
- **What is ruled out.** The harness, because the same harness shows no gap on re-arc where (E) is true. Sibling inputs, because removing them does not close the gap.
- **What remains.** People choosing test pairs deliberately, or memorisation of a public set: the weights may have seen ConceptARC (public since 2023), which I cannot check. This run does not separate those two.
- **Only one learner rejects.** On ConceptARC the 2020 program gives −3.0 [−6.3, +0.2] and Monty-ARC +0.9 [−0.8, +3.0], neither separating. Both ran one test pair per call. So this remains one learner's joint rejection of (E) and (F), not an established property of the benchmark.

### Run checks

587 records, 0 error records, 18.2M tokens (5.0M full, 13.2M folds), 647 rounds, 326 at the 32k cap, 1 without code, 0 skipped for context, largest prompt 3,734 tokens, 0 resumed, all on `arc-v6e-r21`. An independent recount from raw files by separate code matches: h 323, t 358, 427 folds; (a)+(b) 81 and 82, (a)+(b)+(c) 80 and 81, 1 wrong kept. Caveats: stage C uses one pair per task, so its rule table is not directly comparable with stage 2's 480 pairs or its tuple-level task table.

### Sentence for the paper (59 words)

> Removing sibling test inputs did not remove the gap: with one test input per prompt on ConceptARC, Qwen's held-out rate was 75.6% against 83.8% on the test (−8.2 [−11.9, −4.5]), while re-arc, with the same harness, showed none. So this asymmetry lies in the data or in memorisation, for one learner only; the rule answered 79/80 at 50% coverage.
