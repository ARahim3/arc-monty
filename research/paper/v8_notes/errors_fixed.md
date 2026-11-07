# Errors in draft v7 and how v8 fixes them

Numbering follows `HANDOFF.md` §5. Section numbers refer to `research/paper/v8/paper.md`.

| # | Error in v7 | Fix in v8 | Where |
|---|---|---|---|
| 1 | LLM caveat wrong: "neither deterministic nor permutation-invariant, so here the bound is a heuristic". `research/arc2/faloo_qwen.md`'s "Determinism caveat" and "What this means for the paper" repeat it. | The theorem now states seeds i.i.d. and independent of the pairs and the proof carries the seed with each unordered pair. Text says decoding noise does not void the bound, greedy decoding is not needed, canonical order gives symmetry by construction, and the reversed-order test says nothing about symmetry because a reversed order is a different learner. What stays open for the LLM is stated: exchangeability and (F). | §5.1, §5.2 "In words", §6.2 "Status of the theorem" |
| 2a | CORA "33%" for uncertified. | 37 of 201 (18.4%), as its own table and project map give. | §2 |
| 2b | CORA "concurrent", "replication". | "CORA came first", July 2026 runs, public by 2026-10-07 at the latest, read before the system-level wrapper was built. | §2 |
| 2c | CORA's 0/11 on eval omitted. | Quoted verbatim. | §2 |
| 2d | Plain check performs the same as ours, unstated. | Stated with data: plain (a) and FA-LOO answer exactly the same items on public eval and all four unseen sets. "We add" lists the proof, the TBT test, the unseen test and the LLM test. | §1, §2, Table 6 caption, §6.1 |
| 3 | Perspective-voting errors presented as H/(n+1). | Double counting, shown on unseen sets: one voter per module removes nearly all added wrong answers. H/(n+1) is stated separately as a warning with "no measured instance", and the two are explicitly separated. | §5.3, §6.4, Table C2 |
| 4 | "Tri's 32.64 adds Qwen". | The named score lies inside the 28–34 band, and so does the hybrid's. "We cannot credit Qwen with the difference between them." | §7.2 |
| 5 | ARC-AGI-3 omitted that random outscores v3 on held-out games. | Appendix D says it in bold (0.163 vs 0.120), and that one game gives 0.10 of the 0.120. It also says one game gives 0.135 of random's 0.163. Moved to a short appendix, since it is not the named submission. | Appendix D |
| 6a | Bayesian link is an analogy stated as a result. | Deleted, with reference to Fong and Holmes. | n/a |
| 6b | CPU "2.6×". | 2.6× for folds, 3.6× with the full-data run. | §6.1 |
| 6c | "Removing a module loses exactly the tasks it alone solves" contradicts Figure 2's bars. | Sentence gone. Complementarity is stated as "solved by exactly one module" with counts; Appendix A lists solves alone. `module_contributions.png` is not used. | §6.4, Appendix A |
| 6d | [5] Chollet et al. uncited. | Cited as [2]. A strict regex check confirmed every reference is cited in the body. The ARC Prize blog is cited inline in Appendix D, not in the list. | §1 |
| 6e | [13] OPINE-World and Tycho overreach. | Sentence and references deleted. | n/a |
| 6f | arc-skill overreach (uncontrolled support for TBT). | Sentence and reference deleted. | n/a |
| 6g | "Composition ... listed as future work" is outdated. | Monty's documentation has compositional benchmarks with results, supervised, flagged as not yet expected to perform well; behaviours and repeating frames are plans. | §2 |
| 6h | No ARC introduction or conclusion. | §1 explains ARC; §9 is the conclusion. | §1, §9 |
| 6i | Train-set numbers in headlines. | Main tables use public eval as comparator (41/42, 35/36, 43/65) and unseen sets. No 1,147-task performance number appears at all. Development-wide figures are limited to labelled code checks and the 1.5% event rate. Save-run 30/240 is labelled a pipeline check. | Tables 5, 6, 7, 8, C1; §5.4; §7.2 |
| 7 | "99%" as headline. | Headline is 80–94% on unseen sets, compared with 52–66%. The text says "The number to carry away is 80–94% on easier unseen sets, not 98%". 99% does not appear. | Subtitle, abstract, §6.1 |

## Other points from `judge_review.md` that are also handled

- **"A floor, not the explanation":** gone. Now "joint, and a worst case".
- **Abstract implied a precision:** the abstract and §5.3 state the bound implies no precision, with the arithmetic.
- **"Why abstain at all?":** §7.3, with the merge-order numbers and the caveat that Monty-ARC was developed on that split.
- **Learner fixed before the data:** premise (F); §5.3.
- **Per-pair vs per-task:** §4 "Units"; §5.3 "The unit is a test pair".
- **H/(n+1) needs a family fixed in advance:** §5.3.
- **Population mixing:** every column of every table is one population, and the unit is named.
- **"Median 23×" and Figure 3:** dropped.
- **Completeness:** §7.1 describes the notebook, and says FA-LOO is not in it.
- **`tri_sim.py`, `progress_sim.py`:** not used as evidence. §7.2 mentions the simulator only as a failed prediction (+1.7 vs what v4-A then scored). The sentence "certificates cost more than they free" was removed from §7.3 because its only basis was that simulator.

## New findings while re-deriving, that change an earlier reading

1. **`judge_review.md` §3.4 "99% is probably flattered by development: real roles err 4× less than demo roles".** This holds only with training tasks. On public eval the real role is 41/42 and demo roles 144/148 (97.6% vs 97.3%). So the paper does not repeat the claim. What it says instead is that precision falls from public eval to ConceptARC.
2. **Event location (new, post hoc).** Tournament events land on the test role about as often as exchangeability predicts: 21 vs 19.8 over the three unseen sets. This is in Table 5, labelled post hoc.
3. **Answer sets (new).** Plain (a) and FA-LOO answer identical sets on public eval and all four unseen sets, and every real-role event is an FA-LOO error.

## Disagreements between HANDOFF or earlier reports and raw sources

| Where | Says | Raw source | Used |
|---|---|---|---|
| `HANDOFF.md` §3 | 3,544 teams on 10-30 | CSV of 10-30 21:11 UTC has 3,541 rows (may be a different time that day) | 3,541 |
| `HANDOFF.md` §4 | Worst case "mean 24.7–28.3%" | 22.7% on Mini-ARC, 24.2% on public eval | 22.7–28.3% |
| `judge_review.md` §3.5 | ConceptARC 0 of 907 pairs | 905 distinct pairs (`misc_checks2.txt`) | 905 |
| Draft v7 Table 2 | "120 semi-private tasks" | Rules and data page say 240 tasks, public and private; the split size is not stated there | Not stated |
| `HANDOFF.md`, `arc2_improve.md` | Perception notes +1.2 [−3.5, +5.7] | `hint_ab.py` prints +2.1 [−1.7, +6.0]. The engine-stratified +1.2 has no script on disk | Both given; flagged |
| `tbp_forum_theory_notes.md` | Title of arXiv:2507.05888 | arXiv metadata has a newer title | arXiv title |

# Revision round after the blind review (`research/paper/judge_v8/review.md`)

Each finding was re-derived with own code before use. The earlier text is saved as `paper_before_judge.md`.

| # | Finding | Re-derived? | Fix |
|---|---|---|---|
| E1 | Table 9 merged two Qwen samples per task; the notebook runs one | Yes, `revise_merge.py`. Sample 0: 24.0, 23.0, 23.0, 24.0, random 22–24, 7 crowded, Qwen alone 21.0. Replicate: 21, 19, 19, 21, random 19–21, 9 crowded, 18.0. Two samples reproduce the old numbers exactly | §7, Table C5, §9 item 5. "Our one design choice with a measured effect" removed |
| E2 | Certificate mispriced at 4× | Yes, `revise_llm.py`: 3.95×, 1.39×, 1.24× | §6.2, §9 item 3. "Too much for our 12-hour notebook" removed |
| E3 | Gains counted on real roles only | Yes, `revise_monty.py` §6: +12 [+2, +25], +3 [0, +7], +3 [0, +9] | §6.4 |
| E4 | "15 to 125 times" mixes populations | Yes: 15.1–33.9 on unseen, 124.6 on public eval | §5.4 |
| E5 | "Measured cause" is an identity | Yes, arithmetic | §5.4 "The gap decomposes"; "why events are rare" labelled judged |
| E6 | Only the summed sign test shown | Yes: 0.0625, 0.125 | §6.3 |
| E7 | CORA's code has a Thousand Brains layer | Yes, grep | §2 |
| E8 | Verified-first uncited | Yes, read in the PDF | §2, §7, ref [17] |
| E9 | Wilson computed at 16/20 | Yes: [55.7, 90.4] | §6.2 |
| E10 | "The same learners" | Yes: greedy, canonical order, 8,192 answer room vs sampling, native order, 6,144 | §7 |
| E11 | +1.2 not reproducible | Yes, no script exists | Dropped; only +2.1 [−1.7, +6.0] remains |
| E12 | "Usual acceptance test" | Yes: 40.4, 36.4, 60.6 | §4 calls fit-only a conservative baseline |
| E13 | Fourth bucket dropped silently | Yes: n = 1 per set | §6.1 discloses it |

**Also applied:** first-fit lemma and counterexample (checked by hand; (b) fails in 0 of the 912 unseen-set roles that pass (a), and 3 of 471 on development tasks); abstention line; weaker (F); side information; high-coverage floor; H/(n+1) vacuous for H ≥ n+1; tightness as arithmetic; sensitivity; stale comment; Table 1 footnote; first-person verdict language softened; TBT's movement claim stated as out of scope; "no route to a higher score" stated once, in §9; Appendix D cut to two sentences; related work added and checked.

**New claim changed.** "Exchangeability fails is not established" is replaced. Qwen's folds separate (+5.2 [+2.1, +8.7]); Monty-ARC's sets do not (all four intervals include 0). Abstract, §5.4, §8, §9 revised. §5.4 says the test strictly rejects (E) and (F) jointly, because (F) is open for Qwen on this split.

**Not applied, or changed from the review or the lead's note:**

1. Lead's same-token result of 31.0 vs 31.5 is order-dependent, as the later correction says. Own code gives fold arm 31.0–33.5 and plain 31.0–31.5; one fixed rule is reported with its interval (two tiers, canonical fold order, last round with a program: +2.5 [−5.0, +10.0]).
2. Reviewer's within-module figures (3/6 against 5/65; 154/159 against 24/138) were not used: not re-derived, not needed for the story, and my bucket table gives different denominators for "below".
3. Reviewer's Table 5-style replacement for "the plan is dated" (transcript hash) not added to the paper: it is a release decision for the lead. Plan timing: `research/monty_heldout.md` file birth time is after ConceptARC results, while the session transcript shows the plan first; worth releasing a hash.
4. Subtitle and first sentences of the abstract left as instructed, although the subtitle's last clause is now stronger than the body's "little power".
5. Intervals use seed 0 throughout, so a few differ from the reviewer's by under 0.7 points.

**Other discrepancies found this round:** `arc2/faloo_qwen.md` says folds on all tasks cost "17M"; that includes 1.14M of rerun checks (now 15.8M). `lead_holdback.py` reports +2.0 and +70.5 as bootstrap means; the paper gives point estimates (+2.2, +70.6).


# Revision round: new opening and the planned Qwen results

- **Opening:** title, subtitle, abstract and §1 now start from the question. The subtitle's voting clause matches the body. "What this test can and cannot say" stays; Appendix D adds the ARC-AGI-3 sentence (81% of planned steps, 0.061 vs 0.120), checked in `research/arc3_agent_v7.md`.
- **§6.2 rebuilt** on the planned run; greedy is a first, post hoc look in one sentence. Every count re-derived by `revise_sampling.py`, without importing the planned analysis script. Replay reproduced exactly; intervals within 0.7 points.
- **0.91 replaced:** it now appears only as the post hoc figure that did not hold (0.705 prespecified).
- **78.1/7.5 replaced** in the abstract and §9 by 83.3/17.4 and +37.5 within tasks.
- **Exchangeability:** Table 5 is now by rows, with both Qwen runs; §5.4 and §8 say post hoc, then planned at the same size, still jointly (E) and (F).
- **§5.3 and §6.1:** agreement is implied for enumerators, inert on Monty-ARC, and does real work where folds can differ.
- **Cost:** this run's own numbers (1.94×, 1.61× at v = 0.375), not the greedy 1.39×/1.24×.
- **Earlier hint removed:** folds beating resampling on hard tasks did not replicate; §6.2 says so.
- **§7 and §9:** answer "what is trust for?" with the negative result. "No way to solve more tasks" stays in §9 only.

**Small notes:** "(a) with the full-data answer 9 of 13": 14 tasks pass (a), and one (`c4d067a0`) has no full-data answer. Wilson for 32.67/45 follows the plan's rounding ([59, 84]); unrounded is [58, 84]. The same-token range for greedy (31.0–33.5) left the paper with the rebuild.


# Revision round: Qwen on ConceptARC

- **§6.2:** ConceptARC added. Table 7 sets the two LLM sets side by side, and a separate paragraph puts Qwen beside Monty-ARC per pair. "We have no LLM result on unseen tasks" is gone; the status paragraph says what (F) means here. Every number re-derived by `revise_concept_qwen.py`.
- **Exchangeability:** Table 5 has a ConceptARC row with the opposite sign. §5.4 and §8 say (E) looks imperfect in both directions, jointly with (F), and that the sign test does not separate on ConceptARC. §5.5 no longer says the estimate runs high; it says off by about 5 points both ways.
- **Precision floor:** §5.3 reports 41% per pair at Qwen's ConceptARC coverage, with the caveat on (E). "Vacuous" now covers Monty-ARC's sets and ARC-AGI-2 only. Per pair, because the theorem's unit is a test pair; at the task-level 40.6% coverage it would be 30.3%.
- **What stops the wrong ones:** in §5.3 beside the first-fit lemma.
- **Trim:** "trust did not buy score" stays only in the abstract, §7 and §9, each with "at these budgets, on one split, in a replay". Subtitle cut to one sentence. I changed the suggested "with a proof behind it" to "a proof bounds the error under exchangeability", because (E) is doubtful on both sets behind the 72 of 72. Abstract cut by about a third.
- **Moved to save length:** notebook ids to Appendix E; public eval row to prose; the 45-shared and GPT-4 figures dropped.
- **Own intervals** differ from the planned analysis's by at most 0.7 points; the paper quotes the planned ones.


# Finisher pass: after the three-learner rewrite (`rewrite_final.py`)

Text before this pass: `paper_before_finisher.md`. **`paper_before_icecuber.md` is byte-identical to it, so that copy holds the rewritten text, not the text before the icecuber pass.** All edits are in `scripts/finish_edit.py`, which rebuilds `paper.md` from the backup. Recounts, own code, no import of the scripts they check: `scripts/finish_ice.py`, `finish_qwen.py`, `finish_monty.py`, with outputs `finish_ice.txt`, `finish_qwen.txt`, `finish_monty.txt`.

**Result of the recount.** Every count and point estimate of the 2020 program (Tables 4, 5, 6, C7, §3, §5.3, §5.4, §6.2, §6.6), of Qwen on both sets, greedy and sampling, P3, yield, cost and the replay, and of Monty-ARC's rows in Tables 4, 5, 6, C6, C7 matches raw data. Each 2020-program run was also checked against the run list and the set on disk: truth, canonical order, held-out demonstration, query. The only flags in `finish_ice.txt` are the three test pairs of `FilledNotFilled6`, which has one demonstration, so its fold has no run and abstains, as planned. Only bootstrap intervals differ, by at most 0.7 points, where the paper quotes the planned analysis (`numbers.md` gives both). So the mismatches below are in what the text says about the numbers.

| # | Where | Said | Raw or check | Fix |
|---|---|---|---|---|
| F1 | §6.2 overlap | "7 of 52 pairs, 5 of 36, 14 of 341, 0 of 17", denominators unnamed | They are unions: pairs either learner answers (44 + 15 − 7 = 52). On 1D-ARC the overlap is structurally low: 112 of Monty-ARC's answers are on tasks the program cannot read; on readable tasks 14 of 229 | Stated, per set |
| F2 | Table 5 caption | Monty-ARC's rows are its "closest measure" | The rows are computed as the caption says (44/54 vs 11/82, and so on; T2a of the plan). But fold models exist for Monty-ARC, and the same measure as the other learners gives +73.3 [+59.0, +84.9], +67.2 [+47.7, +82.8], +69.6 [+52.5, +80.8] | "Its planned measure"; fold figures added in §6.1, post hoc. The headline 45–75 is unaffected |
| F3 | Brief: "why Monty-ARC's row has no such control" | Assumed no control exists | True of the row: one top answer per test pair, one task with both kinds across the three sets. Not true of Monty-ARC: fold models give +43.6 [+22.2, +64.7] (12 tasks), +21.2 [−6.1, +50.0] ns (11), +35.0 [+9.5, +66.7] (20) | One sentence in §6.1 says both |
| F4 | §4, Table 6 | Top answer "always given" | Monty-ARC has one on 136, 55, 327 pairs; the 2020 program on 615 of 901 on 1D-ARC (412/615 = 67.0%, 412/901 = 45.7%) | "If it has one"; denominators in the caption |
| F5 | Abstract | "the rule beats the usual test wherever it answers" | True of point estimates. Does not separate on Qwen ARC-AGI-2 (p = 0.058) or the 2020 program on ConceptARC (+24.3 ns) | "More precise ... though not separably on two of nine rows". "The usual test" is now defined as Fit in §4; §6.2's "under the usual test" for the top answer corrected |
| F6 | Abstract, last sentence | "It does not raise a score", after a sentence on voting | "It" read as voting | "The rule" |
| F7 | §6.1 | The 2020 program's rows "need no trust in us" | `research/icecuber_faloo.md` §5: we chose the wrapper, settings and order, and the plan's date is our word | "Owe nothing to our development: we chose only its wrapper, in a plan fixed before any output" |
| F8 | §3 | "published recipe unchanged" | Plan §0: fixed per-process limits, no global stop | Said so |
| F9 | Table 5, §6.2 | The 2020 program's ARC-AGI-2 row looks like Qwen's 120 tasks | 113 tasks: 7 excluded for sharing pairs with ARC-AGI-1 | §3 says so |
| F10 | §6.2 | (F) "is open" for Qwen | §3 and the Qwen report: prompts and budgets were chosen on ARC-AGI-2 | (F) fails on ARC-AGI-2, open on ConceptARC. §5.3, §5.4, §6.2 now agree |
| F11 | §6.2 | Monty-ARC's FA-LOO "does not separate from plain (a)" | §5.3 and Table C6: identical answer sets | "Answers the same items" |
| F12 | §5.4 Judged | "On the generated set the premise holds tightly" | True at type level. By task, discordant folds lean to the test: Monty-ARC 19:69 (p = 8 × 10⁻⁸), 2020 program 95:126 (p = 0.043) | Stated. "Fails in both directions" softened to "look imperfect in opposite directions", as in the abstract; the 2020 program's ConceptARC interval includes 0 |
| F13 | §6.3 | "Certification trails until about 290k" | At 64k certification is a point ahead (35.67 vs 34.67), before any task can certify; plain runs end at 246k | Stated |
| F14 | §6.3 | "$1+vn$ ... that is 1.94×" | The formula gives 2.11; 1.94× is the measured token ratio | Both given |
| F15 | §6.3 | Certificate "for no extra tokens" | At four runs the full fold set exists only for $n\le3$ | Added |
| F16 | Table 4 | −0.1 [−1.0, +0.9] bold and `ns`, while bold marks separation | Interval includes 0 | Unbolded |
| F17 | Table 4 | Monty-ARC's rows unmarked | Post hoc in `revise_monty.py` | Caption says so; row labels shortened |
| F18 | §6.5 | Wrong answers "rise in 4 of 6 populations" | 5 of 6 point estimates rise, 4 of 6 separate | "Rise separably" |
| F19 | §9 | "what fails first ... is relations and counting" | §6.6's labels put composition first (20%, 17%) | "Composition, relations and counting" |
| F20 | §3 | Qwen's first look included "an identical rerun doing about as well" | Not needed; length | Cut |
| F21 | Table C2 note | "fold-competition reason of Section 6.1" | §6.1 no longer has it; it is under Table C6 | Reference fixed |
| F22 | Appendix E | "Labels in Section 6.5" | They are in §6.6 | Fixed |
| F23 | Appendix E | Scripts list lacked the sampling harness and the 2020-program run | "Every number traces to a script" | Added |
| F24 | [21] | Commit 9407072 under "2020" | That commit is dated 2025 and touches only the README; source last changed 2020-06-08. Licence MIT, copyright 2020 top-quarks. Author as printed in arXiv:2402.03507 ref 59 | Citation says so |
| F25 | Table 6 caption, §4 | All intervals described as bootstraps | Qwen's in Table 6 are Wilson, as planned | Caption says so |

**Within-task control (new, post hoc for this learner; the plan in `research/icecuber_faloo.md` §0 does not name it).** Paired difference in right-on-test rate over clusters with both predicting and missing fold programs, 10,000 resamples, seed 0: ConceptARC +17.6 [+8.2, +27.2], 52 tasks; Mini-ARC +28.0 [+15.2, +41.5], 47; 1D-ARC +46.6 [+34.4, +57.5], 232 tasks in 14 types; MinimalTasks +23.8 [+11.9, +35.7], 7; ARC-AGI-2 +6.2 [0.0, +18.8] ns, 4. **On 1D-ARC the paper's cluster is the type, and a within-type difference does not hold the task fixed,** so the paper quotes the difference by task, resampling types. The within-type figure is +49.3 [+38.5, +59.7] over 14 types (`numbers.md`). Point estimates confirmed through `analyse.py`'s own parsing. Headline in subtitle, abstract and §9: 45–75 between tasks, 18–47 within a task.

**Bookkeeping.** `numbers.md` rewritten: table numbers match the paper, last-pass numbers point at the recounts, rows for numbers no longer in the paper removed (1,530; 52–66%; 21–48 points; the 58% and 69% floors; 21 vs 19.8, p = 0.07; Table 5's old public-eval row; +10.5; 1D-ARC by task −1.2 and other unused entries). New check `scripts/lint_numbers_back.py` runs the reverse of `lint_numbers.py`. `fallback.md` re-checked: its items now use the current section and list numbers, old §6.2 and §9 item 5 corrected, C retired, B unchanged in substance (ref 57851152 still pending when read on 11-01).

**Length.** Cut from the body: detail Tables C1, C4 and C5 carry, the hand-read counts Appendix B carries, repetition between §5.4, §6 and §8 (§8's exchangeability bullet, the fit-baseline sentence in §6.2), the calibration aside in §5.5. Trial layout in `todo_for_pdf.md`.

**Unchanged and not re-derived this pass:** the `S` rows of `numbers.md`, and the rows that rest on earlier outputs (`eval_only.txt`, `verify_numbers.txt`, `revise_merge.txt`, and others), which `lint_intervals.py` checks against those outputs rather than against raw data.

# Final pass (2026-11-02), against `research/paper/judge_v8b/review.md`

Text before this pass: `paper_before_final_pass.md`. Own recounts, importing no analysis script they check: `scripts/final_qwen.py`, `final_roles.py`, `final_column.py`, `final_tables.py`, `final_s_check.py`, with `final_*.txt` beside this file. `scripts/final_lint.py` checks every interval and fraction against computed outputs and the primary reports; `scripts/wc_body.py` counts words. `numbers.md` rewritten and `lint_numbers.py` clean in both directions (the back direction lists only unrounded values and one tie range).

## Applied

| # | Must-fix | Re-derived | Now |
|---|---|---|---|
| 1 | Sign test in the exchangeability table | `final_roles.txt`: expected splits 13.5:25.4, 7.5:10.3, 26.2:57.5, as the judge says | Column dropped from Tables 7, C10. Mean, with exact role permutation where all roles exist. One sentence on why, in 6.5 |
| 2 | "Imperfect in opposite directions", "people choose test pairs" | Qwen +5.2, +5.0, −5.1, −1.0; `re-arc` minus the two sets −6.0, +4.1 (`final_qwen.txt`, own intervals within 0.1) | 6.5 reports what is measured; deliberate choice is a hypothesis; (F), memorisation and sibling inputs left open; T2c +10.5 [−4.2, +24.5] reported from `concept_analysis.json` |
| 3 | (E) conditional on other test inputs | Judge's gap checked by reading the proof: step 2 needs it | (E) restated; sibling sentence in 5.4 |
| 4 | Vacuous bounds | Coverage against 1/(n+1) on every row; `re-arc` floor 53.3, rotated 416/421, 52.6%, floor 52.5 (`final_qwen.txt`) | Said plainly in 5.4, once; Qwen on ConceptARC named as the row with doubtful (E); Monty-ARC and the 2020 program vacuous even with premises true |
| 5 | "Plan fixed before any output" | First job 22:10:53, Addendum 2 23:06, 55.1 min, 85 of 479 finished; 35 resumed (`final_qwen.txt` §7) | Section 4 states the addition, seeds, batch composition and resumed jobs |
| 6 | "Trust did not buy score" | 55.0, 51.0 (47–56), 42.0, 57.5; +13.0 [+7.0, +19.5]; +2.5 [0, +6.0]; 39, 13 of 75; 17, 0.69 if independent (`final_qwen.txt` §6) | Section 7, Table 8; the negative is stated once. One-sample numbers (7 of 167, 22–24) kept for the notebook |
| 7 | Monty-ARC's row a different measure | +73.3, +67.2, +69.6; within +43.6, +21.2, +35.0 from my own direct run (`final_tables.txt`) | Fold level in Table 3, post hoc; the planned evidence measure moved to Appendix C with values |
| 8 | "No measured cost, small losses not excluded" | −1.5 [−9.0, +6.0] (`finish_qwen.txt`) | "Up to 9 of 120 is not excluded"; plain leads on every point estimate |
| 9 | "72–78%" | 76.1, 85.7, 64.3, 64.7; 54.0/75 = 72.0 (`final_qwen.txt` §11) | 64–86% per run, 72% pooled |
| 10 | Monty-ARC's 0.00 "not a bug" | Ref 57894567 = 0.00 read from Kaggle; threads 751344, 751598 read | "Likely", no logs, spurious zeros, re-run reduces the doubt. "30 of 240 training tasks" removed, as the official page says not to report train performance |
| 11 | C5 row label | `['mg','mc','qu','qv']` in `revise_merge.py`; whole table reproduced by my own code | "Reversed: ..." |
| 12 | Table 6 last column, 2020 program | Plan's Comparison 1 is against `usual` | Table 4's caption marks it post hoc |
| 13 | "Seven groups" | `research/monty_heldout.md` line 56 | Section 4: seven primary comparisons, all reported, T2c named |
| 14 | (S) on unseen sets | My own direct run of frozen `arcmonty`: 0 of 4,650, query swap and reversal | 5.4, Appendix C |
| 15 | One test at a time | Judge's reading; notebook cell | Half a clause in Section 9 |
| 16 | Qwen reach | `llm/kaggle/qwen_phase.py`: "assume >= 20 tok/s per sequence", `concurrency=20`; 400 × 16,200 s = 6.48M; 240 × 45,056 = 10.81M | Section 9, stated as a floor, true rate unknown |
| 17 | Related work | Read [22] Definition 6 and [23]'s enumeration algorithm in the PDFs, [24]'s abstract; [25]'s chapter title from a listing only | Three sentences in Section 2. KWIK and selective classification both need a class fixed in advance on noise-free data, which I confirmed. [25] cited only for its existence |

New material added and re-derived: generator control (6.3), retry rule and replication (6.4), one-column system and proposition (8), Table 1's two rows, fresh Monty-ARC rows (3, 4). All counts match their reports. Sections on frames and voting, Appendix D's ARC-AGI-3 note and the old Section 5.5 are gone from the body; detail is in Appendix C. CORA's per-task neural learner, the "third-party agent" and Monty's ARC-AGI-3 fork are dropped. Added after this pass (text before it: `paper_before_stage_c.md`): Stage C, Qwen on ConceptARC with one test input per prompt (`research/generator_control.md` Addendum 4, §7), as "the one-input run" in Sections 4, 5.4, 6.2, 6.5, 10 and Tables 4, 7, C7, C9, C10. `scripts/final_stage_c.py` recounts it from raw with its own code (`final_stage_c.txt`): every count matches §7 and `generator_control.json` (427 folds, 323 and 358 right, fit 146/155, 80/81, 79/80, AboveBelow9 kept, 8 rejected, 309/322 and 45/93, retries 81/82 and 80/81, 587 records, 0 errors, 18,203,560 tokens), and stage 2's first-pair −6.8 and the paired −1.4 are re-derived from `llm/results/` with the same intervals.

## Not applied as written, and why

- **"45–75 → 45–73".** 45–73 is right for the old rows on fold programs (re-derived). The new rows the same brief asks for go higher: Monty-ARC +76.4 on `re-arc` and +84.7 on `arc-dataset-tama`, the column +80.4 and +77.7. So the headline is **45–85**, on every row but two. 18–47 within a task holds for Qwen and the 2020 program including their `re-arc` rows, and the text says which learners it covers.
- **"No learner with (F) by construction separates".** True on ARC-AGI-2 and ConceptARC, which is what the judge meant. It is not true of everything: the column, frozen before the hand-made fresh sets, gives −4.7 [−9.2, −0.5] there, and the report makes no claim from it. Stated with its scope, and that row is reported. Monty-ARC's 1D-ARC exact test also rejects.
- **Monty-ARC's exact p on 1D-ARC: 0.04, not 0.035.** My exact convolution, P(|S| ≥ |obs|), gives 0.039. The judge's 0.035 is a Monte Carlo two-tail estimate. 0.24 and 0.95 stand.
- **"73–100% against 49–93%, coverage 3–41%" in Step 5's conclusion.** With the new rows it is 73–100% against 30–93%, coverage 3–54%.
- **Judge's "moving only Monty's guesses first scores 28.0".** With the notebook's ranking inside a tier it is 28.5. Not quoted; the row is renamed and that is enough.
- **Judge's new title and frame.** Title deferred by the user. The candidates are in `titles.md`.
- **A run of the named notebook on public eval (Step 5, change 5).** Out of scope here; Section 9 says plainly that no such score exists.

## Could not be verified

The `S` rows of `numbers.md`: 1.8 CPU-seconds, 3.6× CPU, the 20% and 17% labels, +1.7, forum-reported scores and the hidden-set sizes. [25]'s chapter was seen only in a listing. Qwen's true token rate in scored runs is unknowable, since Kaggle keeps no logs. Table C8's public-eval column rests on `eval_only.txt`; neither the judge nor I re-ran its rotation. Stage C: the cause given for AboveBelow9's wrong answer is my hand reading of the three programs' code (judged); the interval of the post hoc +7.2 is only in `generator_control.md` §7, and my own independent bootstrap gives [+2.9, +11.7] against its [+2.7, +11.6].

## Words

`scripts/wc_body.py`-style count, title to conclusion: see the report back. Numeric tokens in running text fell from about 16 per 100 to about 8.

# Judge v8c, pass 1 (2026-11-03), against `research/paper/judge_v8c/review.md`

Text before this pass: `paper_before_v8c.md`; `numbers.md` before it: `numbers_before_v8c.md`. Every edit is one exact, once-only replacement in `scripts/v8c_edit.py`, which rebuilds `paper.md` from `paper_before_v8c.md`. Own recounts, importing nothing from the judge's audit or from the scripts they check: `scripts/v8c_qwen.py` → `v8c_qwen.txt`, and `scripts/v8c_monty_nb.py` → `v8c_monty_nb.json` (frozen `arcmonty` in the notebook's mode, run with `-B`, nothing written under `arcmonty/`). Scope: the review's frame-independent fixes only (Step 5, changes 4–7, and its 3.2, 3.3, 3.5 items); title, abstract frame, Section 1's question and Section 8's place are the author's.

## Applied

| # | Item | Re-derived | Now |
|---|---|---|---|
| 1 | Change 6: definition vs counts (3.2, mismatch 1) | `v8c_qwen.txt` §1: (a)+(b)+(c) as 5.1 writes it gives 108/108 at 54.0% on `re-arc` (the extra task, `rearc_db3e9e38`, has a full run that does not verify but outputs the folds' right answer); with the full run verified, 107/107 at 53.5%. ARC-AGI-2 7/7, ConceptARC 232/232 and the one-input run 79/80 do not change. The Qwen plans fix the condition (`faloo_qwen_sampling.md` §0, "(a)+(b)+(c): also A(D) is verified") | Section 4, Rules: "for Qwen, (c) also requires the full run to verify, which matters only on `re-arc` (108/108 at 54.0% without it)" |
| 2 | Change 6: Table C7 plain (a) (mismatch 2) | §2: 249/264 = 94.3% as printed (no verification); 248/261 = 95.0% with it; the three pairs that differ are Copy8's | Caption footnote: which rows need the full run to verify, and plain (a) with it, 248/261. Cell unchanged |
| 3 | Change 6: 6.4's retried folds (mismatch 4) | §3: post hoc 29 came to fit, 21 predict (right 15), 8 miss (right 0); replication 22, 19 predict (right 12.5), 3 miss (right 0.5). Halves: two folds on two-test tasks, scored by fraction of test outputs as Table 6 is. Same §3 re-derives Table 6 (7/7, 15/15, 11/11, 16/16; p 0.0579, 0.0009, 0.0282, 0.0034). Matches the judge | "Of the retried folds that came to fit, those that predict their held-out demonstration are right on the test 15 of 21 times post hoc and 12.5 of 19 in the replication; the others 0 of 8 and 0.5 of 3." |
| 4 | Change 4: CORA's held-out split (3.3 item 5) | Quote verified in `external/judge/cora/repo/kaggle/writeup_certificates_historical.md` line 13 (E1, "95.3% of the time versus 18.4%"; commit 2026-10-25). The same split appears as counts in `docs/PROJECT_MAP.md` line 29, the source of the 40 of 42 the paper already cited: "certified programs right 40 of 42 times, uncertified train-perfect ones 37 of 201" (37/201 = 18.4%; 40/42 = 95.2%, so the writeup's 95.3% rests on a slightly different count) | Section 2 uses the counts, so the sentence quotes one record: "and it reports a held-out split like Section 6.1's: certified programs right 40 of 42 times on ARC-AGI-2 training tasks against 37 of 201 for the same search's uncertified train-perfect programs, and "0 of 11 on an evaluation development split". We extend it to four unrelated learners, with within-task controls, and add agreement (b) and its bound." 6.1 adds "as CORA's search did [11]" |
| 5 | Change 4: CV+/jackknife+ (3.1 item 5, 3.6) | Derivation below; [28]'s eq. (11) and Theorem 2 read in the arXiv PDF; title, authors and NeurIPS 2020 from the arXiv API | Section 2, after the jackknife+ sentence: "With 0–1 scores, (a)+(b) makes the CV+ (jackknife+) classification set [28] at α = 1/(n+1) the singleton {ŷ}, so a confident error is a miscoverage, which the jackknife+ bounds by 2α; at this α it is a tournament event only one pair can win, hence 1/(n+1)." Reference [28] added |
| 6 | Change 5: scope the advice (3.3 items 3, 4) | Table 8: 55.0 and 57.5 at four samples. §5: of 75 single-test tasks verified-first misses 41, and 39 of them no sample solves, so "most unsolved tasks were never solved by any of four samples" holds; the 17 and 0.69 are a single common rate, 0.310 | Section 10 item 2 is the judge's text. Section 7: "More samples of the same prompt run out" replaced by the judge's sentence; the null reads "independent at one rate for all tasks"; "So at these sample counts verification takes nearly all …" |
| 7 | Change 7: Section 9 | Notebook (read only): `QWEN_BUDGET_PER_ROUND = 16384`; the embedded `qwen_phase.solve_task` uses `task["train"]` in file order; `confident()` in the embedded `vote.py` (byte-identical to `arcmonty/vote.py`): `CONFIDENT = 0.99`, best fully evidenced answer needs at least twice the voters of the next. Offline FA-LOO: 32,768 per round, canonical order (`faloo_qwen_sampling.md` §0). Table 10 from §6: the notebook's own merge cell re-implemented (attempt and alt from `summarize()`, then confident Monty-ARC, extras), Qwen alone 21.0 and 18.0, with Monty-ARC 24.0 and 21.0, using Monty-ARC from this pass's own run (equal to the earlier notebook-mode cache on 120 of 120 tasks). v4-A as Kaggle's latest: the judge's pull in `judge_v8c/audit/out/kmeta/` (`QWEN_HOURS = 3.0`, `QWEN_ORDER = "small"`) | Opening sentence on what the submission is and is not; "Tri v3 ({{NOTEBOOK_V3_URL}}; Kaggle's latest version of the kernel is v4-A)"; header link replaced by the same placeholder; native order and FA-LOO's 32k canonical evidence in the Qwen bullet; "(the v5 heuristic: evidence ≥ 0.99, 2:1 lead)"; Table 10 replaces two sentences that carried the same four numbers. Appendix D's "unlike the offline runs" corrected: the 16k runs of Tables C5 and 10 are also native order |
| 8 | 3.3 items 1, 2, 9 (abstract) | | "symmetric learner"; "a case where the bound bites" (also 6.3); "(Table 1)" → "[10]" |
| 9 | 3.3 item 6 (5.4 siblings) | Judge's argument checked: under joint exchangeability of all n + k pairs, conditioning on siblings changes nothing, so the sentence needs marginal exchangeability with correlated tests | "… even if each test is marginally exchangeable with the demonstrations, when tests are correlated among themselves." |
| 10 | 3.3 item 7 | | 6.5: "need not raise" |
| 11 | 3.3 item 10 | 65 of 160 tasks = 40.6%; 232 of 480 pairs = 48.3% (§1) | Table 4 caption: "Qwen counts tasks (by pair, its ConceptARC coverage is 48.3%, which 5.4 uses)" |
| 12 | 3.2 mismatch 3: Table 8 random orders | §5: exact expectation over uniformly random orders of each test output's candidates (all permutations enumerated) and the 5th and 95th percentiles of 100,000 orders: 52.0 (49.0, 54.5) at three samples, 50.4 (47.5, 53.5) at four. The 40-order mean at four samples was 51.0; the exact one is 50.4. Neither percentile reaches verified-first's 55.0 | Table 8's column and caption; Figure 3 redrawn (`fig_3_ranking_budget.py`), PNG checked |
| 13 | 3.5: Monty-ARC rule counts known before the plan | `research/monty_heldout.md` line 7 lists only ConceptARC's (FA-LOO + (c) 35/44, fit-only 43/74, v5 42/49); Mini-ARC and 1D-ARC were added by an addendum "before any solver run on these sets" | Table 4 caption: "Monty-ARC's ConceptARC counts were known before its plan". Mini-ARC and 1D-ARC are not marked, since the record says they were not known |
| 14 | Figures (change 9's cheap wins, figures_notes.md) | Figure 1 gains the one-input row (planned, Addendum 4 item 3), and Table 3 gains it too: §4 recounts 309/322, 45/93, +47.6 [+38.2, +56.8], within +41.0 over 52 tasks [+27.9, +54.5] (C9's planned intervals [+37.9, +57.1], [+27.6, +54.5]). `fig_1_heldout_split.py` edited (row, label "ConceptARC, 1 input", a panel keeps row spacing when it has fewer rows), re-run, PNG checked | Figures 1–4 inserted where `figures_notes.md` puts them, captions cut to one line each, since the figures carry their own legends and labels; the "Figure 1, to draw" marker replaced; "(Figure 2)" pointer in 5.1 |
| 15 | Table C9 `ns`; the 3-task cell | Marks follow the intervals (an interval that includes 0, or ends at 0.0, is `ns`, as in Table 3 and Table 4) | 10 marks, including the hand-made fresh within cell, now "0.0 ns (3 tasks, no interval)" |
| 16 | One name for the LLM | | Every table row "Qwen, …" now "Qwen3.8-27B, …" (Tables 3, 4, 7, C9, C10), as in Figure 1, Table 5 and Table C7. Prose keeps "Qwen", defined in Section 3 |

**The CV+ derivation (item 5).** Write $s_i=1[M_i(x_i)\ne y_i]$ for fold $i$'s held-out score and $s_i(y)=1[M_i(x_{n+1})\ne y]$ for a candidate $y$, abstention counting as 1. [28]'s eq. (11) keeps $y$ iff $\#\{i: s_i<s_i(y)\}<(1-\alpha)(n+1)$, which is $n$ at $\alpha=1/(n+1)$. With 0–1 scores $s_i<s_i(y)$ means $s_i=0$ and $M_i(x_{n+1})\ne y$. So $y$ is excluded iff every fold predicts its held-out demonstration and no fold predicts $y$. If (a) fails, no label is excluded; if (a) holds, the set is the set of labels some fold predicts. (a)+(b) therefore makes it $\{\hat y\}$; the converse needs no fold to abstain on the test input (a fold abstaining there excludes every label), so "exactly", the judge's word, is true only without abstention, and the paper says "makes". Miscoverage of $y_{n+1}$ is then "every fold right on its held-out pair and wrong on the test", which is $L(i,n+1)=0$ and $L(n+1,i)=1$ for all $i$, the event $E_{n+1}$ of 5.2 (folds need not agree). Its probability is at most $1/(n+1)$ by 5.2's steps 1–2, against the general jackknife+ bound $2\alpha$ (Theorem 2, eq. (13), $K=n$). One correction to the judge's wording: the halving comes from the threshold $(1-\alpha)(n+1)=n$, at which only one pair can beat all others, not from restricting to wrong singletons; at this $\alpha$ every miscoverage is a tournament win. Agreement is what turns the set into one answer whose error is a miscoverage. The paper's sentence says that.

## Not applied, and why

- **Changes 1, 2, 3, 8, 9, 10 and the experiment.** Out of scope for this pass: notebook visibility and version (author), the Writeup, title and abstract frame, Section 8's place, moving tables to a supplement, the leaderboard field after tonight's close (lead). The leaderboard numbers (rank 252 of 3,541 on 10-30) are unchanged.
- **The judge's CORA sentence verbatim.** Its percentages (95.3%, 18.4%) are from the historical writeup; the paper already quotes CORA's 40 of 42 from `docs/PROJECT_MAP.md`, whose same line gives 37 of 201 (18.4%). I used those counts, so the sentence does not mix two of CORA's tallies (40/42 is 95.2%, not 95.3%). Its last clause is shortened because Section 1 already says agreement is what makes the proof possible.
- **The judge's CV+ sentence verbatim.** "Exactly" holds only when no fold abstains on the test input, and the factor of two is lost at this α for every miscoverage, not only for wrong singletons. The paper states the true version (above).
- **Section 9's component table, third line (the NVARC fork band, 28–34).** Left in the text: that band is a public-leaderboard range on the hidden set, from forum reports, and would sit in a table of public-evaluation scores of 120 on a different scale.
- **"Known before the plan" for Monty-ARC's Mini-ARC and 1D-ARC rows.** The plan's own record says only ConceptARC's counts were known.
- **The version link.** Left as `{{NOTEBOOK_V3_URL}}`, in the header and Section 9, as instructed.
- **Figure numbering.** Kept as `figures_notes.md` numbers them, so Figure 2 (5.2) appears before Figure 1 (6.1). Swapping the two numbers in the paper would put them in order of appearance; it touches only the two captions and the "(Figure 2)" pointer, but the Writeup and the judge refer to the held-out split as Figure 1, so it is the lead's call.
- **Table C5's random merge orders** still report the mean (min, max) of 40 orders; the review asked only about Table 8.

## Could not be verified

Kaggle's current kernel version was not re-pulled (no Kaggle calls in this pass); "v4-A is the latest" rests on the judge's pull of 2026-11-02 in `judge_v8c/audit/out/kmeta/`. The pre-existing `final_lint.py` misses (`[0, +6.0]`, `[36, 83]`, `[−1.7, +6.0]`, ten fractions such as 423/447, and the citation brackets `[1, 2]`, `[5, 7]`) are unchanged by this pass and are format differences in the outputs (for example `(0.0, 6.0)`, `423 447`), not wrong values.

## Words

`scripts/wc_body.py`, title to conclusion: 6,057 before, 6,284 after (+227). Of that, the four figure captions are 49 words, and Table 10 with its caption and Table 3's new row about 46, so the text itself grew by about 130. Cuts made to pay for it: 6.5's post hoc contrasts moved to the Table C10 notes; Section 9's two sentences that Table 10 replaces, its repeated "no logs" and the "notebook does not contain" paragraph (now the opening sentence); Section 10's repeated "the rule is not in the notebook"; a shorter sign-test sentence in 6.5.

## Reframe pass, 2026-11-07

The author adopted the frame of `research/paper/judge_v8c/review.md` (Step 4 (iii); Step 5, changes 3, 8, 9): the contribution is FA-LOO and what it shows about ARC, not a Thousand Brains test. Text before this pass: `paper_before_reframe.md`; `numbers.md` before it: `numbers_before_reframe.md`. Every edit is in `scripts/reframe_edit.py`, which rebuilds both from those copies with exact replacements that assert their counts (whole paragraphs matched by a unique opening and ending). No number, table cell or interval changed except Table 1's field line. No experiment was re-run.

**Moved.**

| Before | After |
|---|---|
| Section 8, "What the Thousand Brains Theory lets ARC test", with Table 9 | Appendix D, "What ARC can and cannot test about the Thousand Brains Theory", with Table D1; text verbatim |
| Section 9, The named submission, with Table 10 and Figure 4 | Section 8, with Table 9 and Figure 4 |
| Section 10, Limits and conclusion | Section 9 |
| Appendix D, Reproducibility, credits, tools | Appendix E |
| Section 4's role definitions, inside "Statistics" | Section 4, their own "Roles" paragraph, with *rotating* defined there too |

Cross-references updated: "(Section 10)" in 6.2 → Section 9; "Table 10" (three times) → Table 9; "Tables C5 and 10" in Appendix E → "Tables C5 and 9"; Section 1's roadmap. The moved text had no section, subsection or table references other than its own Table 9 and "Tables C1–C4", which still resolve. `scripts/reframe_xref.py` lists every Section, subsection, Appendix, Table and Figure reference with its line: 59 references, 0 without a target (the pre-reframe text: 53, 0). Never referred to in the text, as before: Tables 1, 2, 5, 6, A1, C7, D1 (was 9), Figures 2–4 (placed with captions), Appendix E (was D).

**Rewritten.** Title (the judge's, as working title; three candidates in `titles.md`); subtitle ("generalising programs from proxies"); abstract in the judge's shape (change 3), with "symmetric learner fixed in advance", "a case where the bound bites", the fork band and [10], 32.64, Monty-ARC's 0.00 and "Monty-ARC among them", CORA credited, and one clause on the Thousand Brains origin; Section 1's opening (proxy, a quarter of verified programs fail, the question, what the paper gives), its TBT sentence (one sentence), the CORA sentence ("Re-induction with each demonstration held out is earlier work"), the roadmap in the new order, and a 61-word "The theory" pointer to Appendix D; Section 9's conclusion in the new frame, and a new "Where ARC solvers fail" paragraph (62 of 68 from 6.4; Appendix B's grouping and Qwen's AboveBelow9, marked judged; 39 of 75 and +2.5 from Section 7). "What other teams can use" and the last paragraph are unchanged. Table C4's caption says what "real" and "demo" mean.

**Field line** (change 10). `scripts/reframe_lb.py`, run with `python -I` from outside the data folder, → `reframe_lb.txt`. Final public leaderboard (`external/judge/lb/arc-prize-2026-arc-agi-2-publicleaderboard-2026-11-07T12:23:22.csv`): 3,544 teams, top 88.06, median 29.31, 1,997 scoring 28–34 inclusive; 219 teams strictly above 32.64 and 59 tied at it, Rank column 220–278. Convention change, stated here so it is not read as a gain: the 10-30 line's "252" was Kaggle's Rank column, which orders ties (the same script reproduces 3,541, 252, ties 203–256, 2,010 from the 10-30 file). On the final file that column puts the named team at 265; the paper now gives the competition rank, 220, with the tie and its listed span: "ranks 220 (59 teams tied at 32.64, listed 220–278)".

**Cut.** The old Section 8 (402 prose words and Table 9) out of the body. From the abstract: "Separately, we test what the Thousand Brains Theory says …" (now Appendix D and the pointer); the between-task "45–85 points … on nearly every set" (kept in 6.1; the within-task 18–47 is the claim the confound does not touch); "on the public leaderboard" (Table 1 says it); "per task". From 6.2: "Verified is not right:", which the paper's frame now states once. The old conclusion's opening question, which Section 1 no longer asks in that form.

**Not done, and why.**
- **Table 2 stays in Section 4.** It is the only place the nine data sets are introduced, sized and cited ([13]–[15], [26], [27]); a one-sentence summary that keeps the sets and citations costs about the same words. Moving it would also leave Tables 1, 3, … with a gap, and renumbering Tables 3–8 would break Figure 1's embedded legend ("ns: interval reaches 0 (Table 3)"), `figures_notes.md` and any Writeup references. The body target was met without it.
- **Tables 3–8 keep their numbers.** Only the old Table 10 is renumbered (to 9), because Table 9 left the body.
- **The suggested clause "the other principles earned nothing separable"** is not used: Monty-ARC's object frames add solves (Tables C1, C2), and the one-column system's object sensors separate on `arc-dataset-tama` (+10 [+1, +25], 4 of 50 types). The pointer uses Appendix D's own wording: frames add solves, not trust; frames, behaviour in its own frame, the count sensor and memory added nothing separable in the one-column system.
- **From the judge's draft abstract:** "doubles certified coverage" (only post hoc, 5.8% → 12.5%; planned, 9.2% → 13.3%); "guarantees at least 53% precision, and 107 of 107" (the abstract keeps the shorter "answers 53.5% of tasks, all right"; Table 5 has the 53.3% floor and 107/107); "(200 fresh `re-arc` tasks)" (budget). All are true in the body; none is needed for the frame.
- **Section 9 order** stays Limits, Conclusion, Where ARC solvers fail, What other teams can use.
- **Notes outside `paper.md`.** `fallback.md` and `todo_for_pdf.md` get a one-line header note with the section map and the new rank, because both give edit instructions by section number. `figures_notes.md` (a design record) and the figure scripts' docstrings still use the old numbers; Figure 4's embedded text says "Sections 5–6", which is unchanged.

**Checks.** `final_lint.py`: 181 intervals and 155 fractions, misses identical to before this pass (the five format-only intervals and ten fractions listed under Judge v8c). `lint_numbers.py`: 797 tokens, 0 missing. `lint_numbers_back.py`: 18 tokens in `numbers.md` not in the paper, 17 before; the new ones are 219 and 265, which explain the rank in the field row, and the old 256 is gone. Placeholders `{{PDF_URL}}`, `{{GITHUB_URL}}`, `{{NOTEBOOK_V3_URL}}` unchanged (the script asserts their counts).

**Words.** `scripts/wc_body.py`, title to conclusion: 6,284 before, 6,005 after (prose 5,429 → 5,268, tables 855 → 737). Abstract paragraph 221 → 225; field line 18 → 26; Section 1, 264 → 368 prose (the new opening and the 59-word pointer); Section 4, 303 → 309; Section 6, 1,391 → 1,387; Section 9 (was 10), 353 → 477; old Section 8, 402 → 0. Appendices, by whitespace split from Appendix A: 5,182 → 5,766.

## Lead, 2026-11-07 after the reframe

Three clarity edits from the Writeup writer's notes, no numbers changed: §6.2 "about one FA-LOO answer in four or five is still wrong" now names Monty-ARC and the 2020 program (Qwen on ConceptARC is 65/65); §6.2 "Qwen's other three rows" now names them (ARC-AGI-2, ConceptARC, `re-arc`); §7 "every merge order scores 22–24" now says "in the notebook run" (Table C5's replicate column is 19–21). `{{NOTEBOOK_V3_URL}}` filled with the version-3 link after the notebook was made public at 12:27 UTC.
