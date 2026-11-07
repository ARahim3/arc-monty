# FA-LOO for Qwen3.8-27B program synthesis (ARC-AGI-2 public eval)

Status: **complete** (10-30, 09:15–09:55 UTC TPU runs; analysis `research/arc2/faloo_analyze.py`). Numbers are task-level, and a multi-test task counts its fraction of test outputs right.

## Question

Does fold-agreement leave-one-out (FA-LOO, `research/innovation_scan.md` §2, `research/monty_faloo.md`) make an LLM's
demo-verified programs as reliable as Monty's certified answers? Plain "verified" (the program reproduces every demo) is right on
test **29.5/37 = 80% [66, 91]** of verified samples in the 10-27 run, and **54/75 = 72% [61, 81]** over every plain sample
(10-27 + 10-29 replicate).

## Method

**Learner A(D).** Qwen3.8-27B (bf16, vLLM-TPU 0.32, 2 × TP4 on a spot v6e-8). It is the `ps` harness of `llm/run_bench.py`,
unchanged: xhigh template, 16k thinking per round, ≤ 2 rounds with the cell-diff feedback, sandboxed runs. Changes, made so that A
is (as nearly as possible) a deterministic, demo-order-symmetric function of its demo set:
- **greedy decoding** (temperature 0, no seed);
- **canonical demo order**: input area, then height, width and grid text. The unlabeled query inputs (the held-out demo input and
  every test input) are shown in the same canonical order, so the prompt never reveals which "test input" is the held-out demo;
- **A's output** is its final program: the first verified one, or else the last round's.

**Rule.** For a task with n demos, the fold models are A_{−i} = A(D ∖ Z_i), i = 1..n, each run from scratch with the same prompt
and budget. A fresh full-data greedy run A(D) runs under the same settings, so that (c) compares like with like. Answer only if:
- (a) every A_{−i} predicts its held-out demo exactly;
- (b) all A_{−i} give the same output on every test input;
- (c) that output equals A(D)'s output, and A(D) is demo-verified.

(c) only removes answers, so the 1/(n+1) bound of (a)+(b) still applies.

**Runs** (`research/arc2/faloo_qwen.py`; records in `llm/results/qwen38_faloo_greedy_b16384.jsonl`, keyed by `kind`):
- `full`: all 120 tasks;
- `fold`: every task with a plain-verified sample (35 tasks, 111 folds), every task whose greedy full run verified, and, as an
  option, every other task;
- `rev`: the demo order reversed;
- `rep`: the same order repeated, for numeric determinism.

Analysis is in `research/arc2/faloo_analyze.py` → `research/arc2/faloo_qwen.json`.

## Results (120 public-eval tasks; folds for all 120)

| Rule (greedy learner unless noted) | answered | right | precision [95% Wilson] | coverage of 120 |
|---|---|---|---|---|
| plain verified, stochastic (10-27 run, verified samples) | 37 samples | 29.5 | 80% [66, 91] | — |
| plain verified, stochastic (all 4 plain runs) | 75 samples | 54.0 | 72% [61, 81] | — |
| greedy full-data verified | 20 tasks | 15.5 | 77.5% [58, 92] | 16.7% |
| **FA-LOO (a)+(b)+(c)**, the guaranteed rule | **5 tasks** | **5.0** | **100% [57, 100]** | **4.2%** |
| FA-LOO (a)+(b) without (c) | 5 | 5.0 | 100% [57, 100] | 4.2% |
| relaxed: ≥ n−1 folds predict their held-out demo *and* agree with A(D) (no bound) | 9 | 9.0 | 100% [70, 100] | 7.5% |
| relaxed: a majority of folds agree with A(D) on the test (no bound) | 10 | 9.0 | 90% [60, 98] | 8.3% |
| greedy verified but **not** FA-LOO-certified | 15 | 10.5 | 70% [42, 85] | — |

- **Every wrong verified answer is rejected.** The 5 greedy-verified tasks that are wrong on test (221dfab4, 38007db0 half,
  4c3d4a41, da515329, dbff022c) all fail (a): a fold program misses its held-out demo.
- **The price is recall.** FA-LOO keeps 5 of the 15.5 correct verified answers (32%). Fold programs, refit on n−1 demos,
  predict their held-out demo in only **33/58 folds (57%)** on greedy-verified tasks, and 71/359 (20%) over all tasks. An LLM
  given fewer demos often finds a different rule that also fits them, which is exactly the overfitting that (a) is there to catch.
- **Unverified tasks (optional run):** I ran folds on all 100 of them; none is certified. Only 7491f3cf passes (a), and its folds
  disagree on the test.
- **Within the lead's population** (35 tasks with a plain stochastic verified sample): 5 certified, 5 right.

**By number of demos** (greedy-verified → certified, certified right; bound 1/(n+1)):

| n | 2 | 3 | 4 | 5 |
|---|---|---|---|---|
| greedy-verified | 6 (3.5 right) | 11 (9.0) | 2 (2.0) | 1 (1.0) |
| FA-LOO certified | 1 (1 right) | 3 (3) | 1 (1) | 0 |
| bound 1/(n+1) | 0.333 | 0.25 | 0.20 | 0.167 |

**Per-task table** (every task that is greedy-verified or plain-verified). "held" is the number of folds that predict their
held-out demo; "rep" and "rev" say whether the repeated run and the reversed-order run give the same test output.

| task | n | A(D) verified | A(D) right | held / n | (a) | (b) | (c) | certified | rep | rev | plain verified samples |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 136b0064 | 3 | no | 0.00 | 2/3 | no | no | no | no | — | — | 3/4 |
| 1818057f | 3 | yes | 1.00 | 3/3 | yes | yes | yes | **yes** | yes | yes | 4/4 |
| 1ae2feb7 | 3 | yes | 1.00 | 2/3 | no | no | no | no | yes | yes | 4/4 |
| 221dfab4 | 2 | yes | 0.00 | 0/2 | no | no | no | no | no | no | 0/4 |
| 291dc1e1 | 4 | no | 0.00 | 1/4 | no | no | no | no | — | — | 1/4 |
| 2ba387bc | 4 | yes | 1.00 | 4/4 | yes | yes | yes | **yes** | yes | yes | 4/4 |
| 31f7f899 | 3 | yes | 1.00 | 2/3 | no | no | no | no | yes | yes | 4/4 |
| 36a08778 | 6 | no | 0.00 | 1/6 | no | no | no | no | — | — | 2/4 |
| 38007db0 | 2 | yes | 0.50 | 0/2 | no | no | no | no | no | no | 2/4 |
| 3dc255db | 3 | no | 0.00 | 1/3 | no | no | no | no | — | — | 1/4 |
| 3e6067c3 | 3 | no | 0.00 | 2/3 | no | no | no | no | — | — | 1/4 |
| 45a5af55 | 2 | yes | 1.00 | 2/2 | yes | yes | yes | **yes** | yes | no | 4/4 |
| 4c3d4a41 | 2 | yes | 0.00 | 0/2 | no | no | no | no | no | no | 0/4 |
| 58490d8a | 3 | yes | 1.00 | 3/3 | yes | yes | yes | **yes** | yes | yes | 3/4 |
| 58f5dbd5 | 3 | no | 0.00 | 1/3 | no | no | no | no | — | — | 1/4 |
| 5961cc34 | 4 | yes | 1.00 | 2/4 | no | no | no | no | no | no | 1/4 |
| 6e453dd6 | 3 | no | 0.00 | 1/3 | no | no | no | no | — | — | 4/4 |
| 7491f3cf | 4 | no | 0.00 | 4/4 | yes | no | no | no | — | — | 1/4 |
| 78332cb0 | 3 | no | 0.00 | 0/3 | no | no | no | no | — | — | 2/4 |
| 7b5033c1 | 2 | yes | 1.00 | 1/2 | no | no | no | no | yes | no | 4/4 |
| 7c66cb00 | 3 | yes | 1.00 | 1/3 | no | no | no | no | no | no | 1/4 |
| 7ed72f31 | 2 | yes | 1.00 | 0/2 | no | no | no | no | yes | no | 1/4 |
| 80a900e0 | 2 | no | 0.00 | 0/2 | no | no | no | no | — | — | 1/4 |
| 8f215267 | 3 | no | 0.00 | 1/3 | no | no | no | no | — | — | 1/3 |
| 97d7923e | 3 | no | 0.00 | 1/3 | no | no | no | no | — | — | 1/4 |
| 9aaea919 | 3 | no | 0.00 | 1/3 | no | no | no | no | — | — | 2/4 |
| aa4ec2a5 | 3 | yes | 1.00 | 2/3 | no | no | no | no | no | yes | 4/4 |
| b0039139 | 4 | no | 0.00 | 0/4 | no | no | no | no | — | — | 1/3 |
| b5ca7ac4 | 3 | yes | 1.00 | 0/3 | no | no | no | no | no | no | 0/3 |
| b99e7126 | 3 | no | 0.00 | 2/3 | no | no | no | no | — | — | 1/3 |
| bf45cf4b | 3 | yes | 1.00 | 3/3 | yes | yes | yes | **yes** | yes | yes | 4/4 |
| c4d067a0 | 3 | yes | 1.00 | 2/3 | no | no | no | no | yes | no | 1/3 |
| d35bdbdc | 3 | no | 0.00 | 0/3 | no | no | no | no | — | — | 3/3 |
| da515329 | 3 | yes | 0.00 | 0/3 | no | no | no | no | no | no | 0/3 |
| db695cfb | 5 | yes | 1.00 | 5/5 | yes | no | no | no | no | no | 1/3 |
| dbff022c | 3 | yes | 0.00 | 1/3 | no | no | no | no | no | yes | 1/3 |
| dd6b8c4b | 3 | no | 0.00 | 1/3 | no | no | no | no | — | — | 1/3 |
| dfadab01 | 4 | no | 0.00 | 3/4 | no | no | no | no | — | — | 3/3 |
| eee78d87 | 3 | no | 0.00 | 1/3 | no | no | no | no | — | — | 2/3 |

## Determinism caveat (important)

The bound needs a deterministic, demo-order-symmetric learner. I tested both premises, and **neither fully holds**:
- **Greedy decoding on vLLM-TPU is not bit-deterministic.** Re-running the identical greedy full-data job gives the same test
  output in only **10/20** greedy-verified tasks (bf16 numerics depend on the batch composition, and the effect compounds over
  16k reasoning tokens).
- **Demo order** matters about as much: with the order reversed, the output is the same in **8/20**. That is
  indistinguishable from the rerun noise, so I cannot separate order effects from numerics.
- **An LLM is not permutation-invariant over its prompt.** Canonical ordering makes A a function of the demo *set*, but only up
  to that numeric noise. A different canonical order is a different learner.
- **Interesting side result:** the certified programs are the stable ones. Rerun same output 5/5 and reversed order 4/5,
  against 5/15 and 4/15 for the verified-but-uncertified programs. FA-LOO selects programs that are robust to perturbation.
- **What this means for the paper:** for Qwen, the 1/(n+1) guarantee is a heuristic, not a theorem. The empirical precision (5/5)
  is the evidence, and its CI is wide [57, 100]. Exchangeability between ARC demos and the (often harder) test is the second,
  shared caveat.

## Cost

FA-LOO needs n+1 program-synthesis runs per task, against 1 (mean n ≈ 3.2): ~33k tokens per run, 359 fold runs + 120 full runs
+ 40 checks ≈ 17M tokens, ~45 min on two v6e-8. On Kaggle's 4×L4 it is ~4× the Qwen budget per task. **Not affordable inside the
12 h run, and useless for the LB:** pass@2 scoring makes candidate order irrelevant, and certification only reorders.

## Paper sentence (≤ 60 words)

"FA-LOO transfers to an LLM. Re-running Qwen3.8-27B program synthesis on every leave-one-out fold certified 5 of 20
demo-verified ARC-AGI-2 evaluation programs, all correct (verification alone: 77.5%), and rejected all five wrong ones.
Coverage is the price: refit on fewer demonstrations, the LLM rediscovers the rule in 57% of folds, and greedy decoding is not
fully deterministic."  (56 words)

