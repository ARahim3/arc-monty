# numbers.md: every number in `paper.md` and where it comes from

Paths are relative to the project root. **Status:** **R** = re-derived from raw files or caches by a script (this pass's scripts are named); **D** = read directly from a primary source on disk or from a read-only API; **S** = taken from an earlier report, not re-derived (reason given).

Scripts are in `research/paper/v8_notes/scripts/`, with outputs one folder up. **This pass, own code, no import of the scripts they check:** `final_qwen.py` → `final_qwen.txt` (Qwen on `re-arc`, retry, replication, ranking, failing folds, plan timing, merge orders); `final_roles.py` → `final_roles.txt` (Monty-ARC role tests from caches with only the frozen `vote.pool`; 2020 program on `re-arc` from raw lines); `final_column.py` → `final_column.txt` (one-column rows and games from raw); `final_tables.py` → `final_tables.txt` (new FA-LOO minus fit rows, development counts, fold-level Monty-ARC); `final_s_check.py` (direct run of frozen `arcmonty`, real role, on the four unseen sets, 3 workers, about 11 minutes; item files stay in the session scratchpad and are summarised in `final_tables.txt`); `final_stage_c.py` → `final_stage_c.txt` (Qwen's one-input run on ConceptARC, Stage C of `research/generator_control.md` Addendum 4 and §7, from `research/generator_control/raw/gc_qwen_c1.jsonl` and `gc_qwen_c1_retry.jsonl`, with stage 2's `llm/results/qwen38_faloo_sampling_concept_b32768.jsonl` and `gc_qwen_main.jsonl` for the comparisons; added after this pass). **Earlier recounts still used:** `finish_ice.txt`, `finish_qwen.txt`, `finish_monty.txt`, `eval_only.txt`, `unseen_check.txt`, `event_location.txt`, `verify_numbers.txt`, `misc_checks.txt`, `misc_checks2.txt`, `misc_checks3.txt`, `cpu_ratio.txt`, `hint_ab_rerun.txt`, `revise_monty.txt`, `revise_merge.txt`, `selfcal_own.txt`. A blind judge also recomputed most of those from raw (`research/paper/judge_v8b/audit/`). **Judge v8c, pass 1 (2026-11-03), own code:** `v8c_qwen.py` → `v8c_qwen.txt` (FA-LOO as 5.1 writes it against the Qwen plans' rule; Table C7's plain (a); retried folds in both runs; the one-input split row; Table 8's random orders; the notebook's merge for Table 10) and `v8c_monty_nb.py` → `v8c_monty_nb.json` (frozen Monty-ARC run in the notebook's mode on the 120 public-evaluation tasks, about one minute). Rows marked v8c below are new or changed in that pass. **Reframe pass (2026-11-07), own code:** `reframe_lb.py` → `reframe_lb.txt` (both leaderboard CSVs, run with `python -I` from outside the data folder). Rows marked reframe are new or changed in that pass; section headings follow the new order (Section 8 → Appendix D, Table 9 → Table D1, Section 9 → 8, Section 10 → 9, Table 10 → Table 9).

**Intervals.** Percentile cluster bootstrap, 10,000 resamples. Seed 0 throughout, except the Qwen rows marked "planned interval", which are the planned analysis's own (`research/arc2/faloo_qwen_sampling.md`), and rows from `research/generator_control.json` and `research/tbt_proper/report.json`, which are those reports' own. This pass's recomputations with its own resampling differ from them by at most 0.8 points on between-task and rule rows, and by up to about 3 points on within-task rows, which rest on few tasks; none of this changes whether a row separates. Point estimates and counts match exactly unless stated.

## Header, abstract, Table 1 and field

| Number | Source | Status |
|---|---|---|
| 57726521, 32.64; 57851152, 29.72; 57785855, 27.36; 57689321, 28.47; 57762908, 0.00; 57894567, 0.00; 57661715, 0.00 | `kaggle competitions submissions arc-prize-2026-arc-agi-2 --csv`, read 2026-11-02 in this pass | D |
| Spread 2.92 | 32.64 − 29.72 | R |
| reframe: final field, 3,544 teams, top 88.06, median 29.31; ranks 220 (59 teams tied at 32.64, listed 220–278; 219 teams strictly above; Kaggle's Rank column, which orders ties, puts ours at 265); 1,997 between 28 and 34 inclusive | `external/judge/lb/arc-prize-2026-arc-agi-2-publicleaderboard-2026-11-07T12:23:22.csv`, the final public leaderboard, recounted by `reframe_lb.py` → `reframe_lb.txt`. The same script reproduces the 10-30 file's figures that this row replaces (3,541; rank column 252, ties 203–256; 2,010) | R |
| 7 modules in the hybrid; 8 in tri v3 and Monty v5; 2 in v0 | Notebook cells; tri's embedded `arcmonty` compared byte for byte; submission description of v0 | R |
| reframe: 2026-11-07 | Date in the CSV's name | D |
| 1/(n+1) | Proved in the paper | R |
| 53.5%, 16 of 16, 13.3%, 55.0, 57.5 of 120, 45–85, 18–47 | As Sections 6.1, 6.3, 6.4, 7 (reframe: the abstract keeps all but 45–85, which stays in 6.1; about a quarter as Section 1; 32.64 and 0.00 as Table 1) | R |

## Section 1

| Number | Source | Status |
|---|---|---|
| About a quarter | 100 − 72.6 | R |
| Two attempts, no penalty, exact match | `research/paper/sources/arc-prize-2026-arc-agi-2__evaluation.md` | D |
| 240 hidden tasks | `…__data-description.md` | D |
| 12-hour run | `…__code requirements.md`; notebook cell | D |
| Typically two to five demonstrations | by-n table in `research/monty_faloo.md` | D |
| "Harder" ARC-AGI-2 | `research/arc_agi2_sota.md`. S: competition history, nothing to re-derive | S |

## Section 2

| Number | Source | Status |
|---|---|---|
| CORA 40 of 42; "0 of 11 on an evaluation development split"; July 2026 | `external/judge/cora/repo`: `docs/PROJECT_MAP.md`, `kaggle/writeup.md`, `kaggle/writeup_certificates_historical.md`, `README.md`; `external/novelty/chimdiwalter/paper_DRAFT.md` | D |
| v8c: CORA's held-out split, certified 40 of 42 against uncertified train-perfect 37 of 201 (18.4%) | `external/judge/cora/repo/docs/PROJECT_MAP.md` line 29 ("certified programs right 40 of 42 times, uncertified train-perfect ones 37 of 201"); the same split as "95.3% of the time versus 18.4%" in `kaggle/writeup_certificates_historical.md` line 13 (E1), committed 2026-10-25; read as data | D |
| v8c: CV+ (jackknife+) set at α = 1/(n+1), miscoverage bound 2α, 1/(n+1) | [28] eq. (11) (strict inequality, include y if the count is below (1 − α)(n + 1)) and Theorem 2, eq. (13) for K = n, read in the arXiv PDF; the reduction to the tournament event is derived in `research/paper/v8_notes/errors_fixed.md`, Judge v8c pass 1 | R |
| CORA public by 2026-10-07 | `gh api repos/ChimdiWalter/Symbolic_Reasoning_LLM_ARC-AGI/events`, read 2026-11-01 | D |
| Monty-ARC evidence dates from 2026-10-26 | File dates in `arcmonty/`; `research/report_v1e.txt` | D |
| About 28–34 | `research/kaggle_intel.md`; forum 745846 (28.06, 31.39, 31.53), 748895 (30.83); fork name 33.89. S: participant reports, not ours to re-run | S |
| 2025 winner | `research/arc_agi2_sota.md`. S: history | S |

## Section 3

| Number | Source | Status |
|---|---|---|
| Eight modules; 2:1 (Appendix A) | `arcmonty/`; `arcmonty/vote.py` | D |
| Temperature 1.0; 32k; two rounds; 120, 160, 200 tasks | `research/arc2/faloo_qwen_sampling.md` §0; raw `sampling` and `budget` fields; `final_qwen.txt` | R |
| 251, 249 | `finish_ice.txt`, against the authors' `external/judge/conceptarc/repo/data.xlsx` | R |
| 286 of 901 | `finish_ice.txt` | R |
| 113 tasks | `research/icecuber_faloo/export/items_agi2.jsonl`; plan's reason in `research/icecuber_faloo.md` §0 | R |
| 42 copies | `research/tbt_proper/column/settings.py`; `research/tbt_proper/report.md` §2 | D |

## Section 4, Table 2

| Number | Source | Status |
|---|---|---|
| 167 pairs, 120 tasks | `data/kaggle_format/agi2_eval_challenges.json`; `final_qwen.txt` | R |
| 0 of 905, 671, 3,545, 93 | `misc_checks2.txt`, whole-pair hash | R |
| 480, 149, 901, 48; 160, 149, 18, 16 clusters | `finish_ice.txt`, `finish_monty.txt` | R |
| 5×5 | `external/heldout/mini-arc/README.md` | D |
| `re-arc`: 200 tasks, 200 pairs; 0 of 800 | `research/generator_control/data/checks.json`; `research/generator_control.md` Addendum 1; `final_qwen.txt` counts the tasks | D/R |
| Hand-made fresh: 80 pairs, 77 tasks, one task excluded; `arc-dataset-tama` 1,567, 50, 0 of 4,624; PQA 210, 7, 0 of 700 | `research/tbt_proper/column/results/fresh_check.json`; `PLAN.md` §0.2; `final_column.txt` counts items and clusters | D/R |
| 13 games, 3,120 steps | `final_column.txt` (240 per game, E2 row) | R |
| Seven primary comparisons | `research/monty_heldout.md` §0, line "Primary comparisons are the seven listed" | D |
| 55 minutes; no accuracy computed | First job 22:10:53 UTC, Addendum 2 23:06 UTC (`final_qwen.txt` section 7, 55.1 min, 85 of 479 finished); the addendum's own statement | R |
| Seeds; batch composition | `research/arc2/faloo_qwen_sampling.md` §0, Addendum 1 | D |
| 35 of 479 resumed | `final_qwen.txt` section 7 (`resumed_from_round` > 0) | R |
| One-input run: Qwen, ConceptARC, one test input per prompt; planned 2026-11-02 (06:04 UTC), after the other results; no setting chosen on ConceptARC; retry rule from ARC-AGI-2 | `research/generator_control.md` Addendum 4 ("Known when this was written", "Caveats fixed now") | D |
| 17 primary comparisons | `research/tbt_proper/report.md` §0 | D |
| 10,000 | `research/monty_heldout/stats.py` | D |

| v8c: FA-LOO as 5.1 writes it, `re-arc`: 108/108 at 54.0% (the extra task, `rearc_db3e9e38`, has a full run that does not verify but outputs the folds' right answer); with the Qwen plans' rule 107/107 at 53.5%; ARC-AGI-2 7/7, ConceptARC 232/232 and the one-input run 79/80 unchanged | `v8c_qwen.txt` §1; rule in `research/arc2/faloo_qwen_sampling.md` §0 ("(a)+(b)+(c): also A(D) is verified") | R |

## Sections 5.1–5.4

| Number | Source | Status |
|---|---|---|
| 1/(n+1), H/(n+1), k/(n+1) (Appendix C), first-fit lemma, precision floor | Proved in the paper; re-checked by the judge | R |
| 912 roles pass (a), (b) fails in 0 | `final_roles.txt` ((a)+(b) answered 156 + 42 + 694 + 20); `revise_monty.txt` §2 | R |
| Of 22, (a) stops 11, (b) and (c) the rest | `finish_qwen.txt` (11, 7, 4) | R |
| 23–28% | Table C8 row; 2020 program's sets 28.3, 22.7, 25.0, 26.5 in `finish_ice.txt`; Qwen 26.11 and 28.32 in `finish_qwen.txt`; `re-arc` 25.0 | R |
| Floor 41%: 48.3% coverage, 232/232 (1 − 0.2832/0.4833 = 41.4) | `finish_qwen.txt` | R |
| One-input run: 50.0% coverage, floor 43% (1 − 0.2832/0.500 = 43.4), 79/80 | `final_stage_c.txt` §0 (mean 1/(n+1) = 0.2832 over the 160 tasks), §2; `research/generator_control.json` `stage_c.rules.abc` | R |
| (E) rejected for Qwen on ConceptARC, jointly with (F) | Section 6.5: −5.1 [−8.1, −2.1] and −8.2 [−11.9, −4.5] both exclude 0 | R |
| 1–6% | Table C8 | R |
| 4,650 folds, 0 changed | `final_tables.txt`: 1,281 + 528 + 2,703 + 138 real-role folds, query swap 0, demonstration reversal 0, from `final_s_check.py` | R |

## Section 6.1, Table 3, Table C9 (split columns)

| Number | Source | Status |
|---|---|---|
| Monty-ARC ConceptARC, Mini-ARC, 1D-ARC: 130/163, 21/324, +73.3 [+59.0, +84.9], +43.6 [+22.2, +64.7] (12); 47/62, 16/185, +67.2 [+47.7, +82.8], +21.2 [−6.1, +50.0] (11); 519/566, 79/358, +69.6 [+52.5, +80.8], +35.0 [+9.5, +66.7] (20 tasks, resampling types) | `final_tables.txt` (own run; intervals within 0.7); intervals quoted from `finish_monty.txt`. Post hoc | R |
| Monty-ARC hand-made, tama: 20/25, 3/32, +70.6 [+41.7, +89.5], 0.0 (3); 438/482, 35/568, +84.7 [+71.6, +94.7], +21.2 [+8.0, +45.8] (24) | `final_column.txt`; intervals `research/tbt_proper/report.json` | R |
| Monty-ARC `re-arc`: 70/72, 10/48, +76.4 [+62.2, +88.9], +50.0 [+12.5, +87.5] (7) | `final_roles.txt`, from the cache with only the frozen `vote.pool`; intervals `research/generator_control.json` (own within 2) | R |
| Qwen ARC-AGI-2, ConceptARC: 83.3 (99), 17.4 (47), +66.0 [+53.6, +77.9], +37.5 [+11.0, +61.8] (17); 94.5 (321), 45.8 (88), +48.7 [+41.3, +56.3], +36.7 [+26.5, +46.9] (49) | `finish_qwen.txt`; planned intervals | R |
| Qwen `re-arc`: 423/447, 27/67, +54.3 [+40.8, +66.9], +28.6 [+9.7, +47.4] (42) | `final_qwen.txt` (+54.3, +28.6, own intervals within 0.4); intervals from `research/generator_control.json` | R |
| 2020 program, five sets: 60.4 (285), 15.3 (993), +45.0 [+35.3, +54.6]; 74.4 (203), 15.1 (325), +59.3 [+47.8, +69.8]; 84.8 (983), 17.5 (862), +67.3 [+55.4, +75.8]; 85.7 (63), 21.3 (75), +64.4 [+44.6, +80.3]; 16.7 (6), 0.6 (468), +16.0 [−0.6, +48.8] | `finish_ice.txt` | R |
| 2020 program within task: +17.6 [+8.2, +27.2] (52); +28.0 [+15.2, +41.5] (47); +46.6 [+34.4, +57.5] (232); +23.8 [+11.9, +35.7] (7); +6.2 [0.0, +18.8] (4). Post hoc | `finish_ice.txt` | R |
| 2020 program `re-arc`: 79/126, 51/466, +51.8 [+39.9, +63.0], +30.4 [+18.4, +42.9] (56) | `final_roles.txt`, from raw lines; intervals `research/generator_control.json` (own within 0.4) | R |
| One column: 23/26, 14/174, +80.4 [+62.4, +93.1], +53.7 [+14.1, +88.9] (9); 290/411, 105/2,732, +66.7 [+41.2, +82.3], +4.4 [−3.3, +12.7] (62); 0/27, 11/1,443, −0.8 [−1.7, 0.0], −1.1 [−5.6, 0.0] (5); spent 51/91, 50/847, +50.1 [+34.9, +67.3], +17.1 [−1.2, +36.9] (13); 74/91, 16/436, +77.7 [+65.6, +87.0], +27.3 [+11.1, +44.1] (25); 483/703, 232/1,967, +56.9 [+42.3, +64.1], +21.1 [+9.9, +29.2] (232) | `final_column.txt`; intervals `research/tbt_proper/report.json` | R |
| 45–85; 18–47 | Lowest +45.0, highest +84.7, excluding two rows (+16.0, −0.8 ns). Within: lowest +17.6, highest +46.6 on Qwen and the 2020 program, excluding +6.2 ns. Monty-ARC and the one column are stated separately in the text | R |
| 83.3 vs 75.2; +8.1 [+0.5, +16.2] | `finish_qwen.txt`; planned interval | R |

## Section 6.2, Table 4, Table C9 (rule columns)

| Number | Source | Status |
|---|---|---|
| Monty-ARC first three rows: 43/74, 35/44, 9.2%, +21.4 [+3.3, +40.3]; 15/29, 8/9, 6.0%, +37.2 [+8.7, +62.5]; 187/285, 161/172, 19.1%, +28.0 [+13.4, +45.7] | `finish_monty.txt` | R |
| Monty-ARC fresh: 7/11, 7/7, 8.8%, +36.4 [+9.1, +66.7]; 128/175, 111/116, 7.4%, +22.5 [+7.7, +40.1]; `re-arc` 23/25, 19/19, 9.5%, +8.0 [0.0, +20.6] | `final_column.txt`, `final_tables.txt`, `final_roles.txt` | R |
| Qwen: 32.67/45, 7/7, 5.8%, p = 0.058; 139/150, 65/65, 40.6%, p = 9.6 × 10⁻⁷; 159/171, 107/107, 53.5%, p = 3.7 × 10⁻⁶ | `final_qwen.txt` (the first two also `finish_qwen.txt`; the third is `hyper` in section 1 of the output) | R |
| 2020 program: 152/310, 11/15, 3.1%, +24.3 [−10.0, +50.4]; 48/76, 29/32, 21.5%, +27.5 [+14.9, +40.1]; 370/445, 176/183, 20.3%, +13.0 [+6.0, +22.5]; 29/41, 12/12, 25.0%, +29.3 [+13.9, +46.5] | `finish_ice.txt` | R |
| 2020 program `re-arc`: 39/62, 8/9, 4.5%, +26.0 [+1.3, +45.5] | `final_tables.txt` from raw lines | R |
| One column: 13/28, 6/6, 7.5%, +53.6 [+33.3, +72.7]; 104/344, 73/76, 4.9%, +65.8 [+48.8, +85.3]; spent 35/159, 11/16, +46.7 [+19.6, +78.4]; 28/85, 10/10, +67.1 [+56.7, +76.7]; 321/566, 76/86, +31.7 [+17.8, +48.0]; PQA 1/24, 0/0 | `final_column.txt`; intervals `report.json` | R |
| v8c: Table 4 caption, Qwen ConceptARC coverage 48.3% by pair (40.6% by task); Monty-ARC's ConceptARC counts known before its plan | `v8c_qwen.txt` §1 (232 of 480 pairs, 65 of 160 tasks); `research/monty_heldout.md` line 7 (FA-LOO + (c) 35/44, fit-only 43/74 already known; Mini-ARC and 1D-ARC added by an addendum before any run on them) | R |
| All but three | Monty-ARC `re-arc` ns, Qwen ARC-AGI-2 p = 0.058, 2020 program ConceptARC ns; the one-input row's p = 0.013 separates | R |
| 64–86% per run, 72% pooled | `final_qwen.txt` section 11: 76.1, 85.7, 64.3, 64.7; 54.0/75 = 72.0 | R |
| One in four or five wrong | 35/44, 11/15: `finish_monty.txt`, `finish_ice.txt` | R |
| 179; 48; 139 of 318 (Qwen's other three rows) | 7 + 65 + 107; 14 + 22 + 12; 24 + 63 + 52 of 31 + 128 + 159: `final_qwen.txt` sections 1, 3, 5, 9 and `finish_qwen.txt` | R |
| AUROC 0.705, 0.584 (C9: [0.52, 0.87], p = 0.013; [0.45, 0.72], p = 0.083; 11 of 87) | `finish_qwen.txt` | R |
| Table 4 one-input row: 94.2% (155) = 146/155; 98.8% (80) = 79/80; 50.0% = 80/160; p = 0.013 (0.0131 = P(kept ≤ 1), 155 verified, 9 wrong, 80 certified) | `final_stage_c.txt` §2; `research/generator_control.json` `stage_c.rules`, `stage_c.verified`; `research/generator_control.md` §7 Table 9 | R |
| One-input run: 80 tasks, one wrong (AboveBelow9); Qwen's only wrong real-role FA-LOO answer | `final_stage_c.txt` §2. Every other Qwen real-role FA-LOO count in the paper has none wrong: 7/7, 65/65 (232/232 per pair), 107/107, 15/15, 11/11, 16/16, greedy 5 of 20 (`final_qwen.txt`, `finish_qwen.txt`) | R |

## Section 6.3, Table 5

| Number | Source | Status |
|---|---|---|
| 200 of 400 by hash; draws; n = 3; 0.25 | `research/generator_control.md` §0, Addendum 1; `data/checks.json` | D |
| Qwen 159/171, 107/107, 53.5% [46.5, 60.5], floor 53.3%, 0 of 200, 1.83% | `final_qwen.txt` section 1 | R |
| Rotated 416/421; 52.6%; 52.5%; no two events; every wrong answer an event; exact p 0.57 | `final_qwen.txt` section 2 | R |
| Qwen −1.0 [−3.5, +1.5], half-width 2.5 | `final_qwen.txt` section 1 | R |
| 2020 program 39/62, 8/9, 4.5%, 43/51, −0.5 [−4.5, +3.7], exact p 0.84 | `final_roles.txt` | R |
| Monty-ARC 23/25, 19/19, 9.5%, 79/86, −1.3 [−2.7, 0.0], exact p 0.15 | `final_roles.txt`; interval from `generator_control.json` | R |

## Section 6.4, Table 6

| Number | Source | Status |
|---|---|---|
| 22 of 31; 62 of 68 | `final_qwen.txt` section 5 | R |
| 7/7, 5.8%, p = 0.058; 15/15, 12.5%, 14 of 14, p = 0.0009 (0.00087) | `final_qwen.txt` section 3 | R |
| 16/16, 13.3%, 11 of 11, p = 0.0034; 11/11, 9.2%, p = 0.028 | `final_qwen.txt` section 4 | R |
| 45 tasks each time | `final_qwen.txt` sections 3, 4 | R |
| [59, 100], [78, 100], [72, 100], [79, 100] | Clopper-Pearson with all right: 0.025^(1/k) | R |
| v8c: retried folds that came to fit: post hoc 21 predict (right 15), 8 miss (right 0), of 29; replication 19 predict (right 12.5), 3 miss (right 0.5), of 22; halves from two-test tasks, scored by fraction of test outputs as Table 6 | `v8c_qwen.txt` §3 (also re-derives Table 6: 7/7, 15/15, 11/11, 16/16, p 0.0579, 0.0009, 0.0282, 0.0034); `final_qwen.txt` section 12 for the post hoc run | R |
| 2.4× (2.41), 1.94× | `final_qwen.txt` section 10 | R |
| 9 of 16 among the first 15 | `final_qwen.txt` section 4 | R |

## Section 6.5, Tables 7 and C10

| Number | Source | Status |
|---|---|---|
| Qwen +5.2 [+2.1, +8.7] (greedy); +5.0 [+1.5, +8.6]; −5.1 [−8.1, −2.1]; folds, rates, discordant | `finish_qwen.txt`; `final_qwen.txt` section 8 recomputes the last two | R |
| Qwen `re-arc` 600, 75.5/76.5, 27/33 | `final_qwen.txt` section 1 | R |
| 2020 program rows: 1,281, 22.2/25.3, −3.0 [−6.3, +0.2], 113/152; 483, 1.2/0.8, +0.4 [−0.6, +1.6], 5/3; 528, 38.4/37.9, +0.6 [−4.6, +6.0], 52/49; 2,703, 36.4/36.4, −0.1 [−1.0, +0.9], 149/151; 138, 45.7/50.7, −5.1 [−14.0, +2.9], 9/16 | `finish_ice.txt` | R |
| 2020 program `re-arc` 600, 21.2/21.7, 48/51 | `research/generator_control.json` `ice.E`; difference and interval recomputed in `final_roles.txt` | R |
| Monty-ARC rows: 1,281, 12.7/11.8, +0.9 [−0.8, +3.0], 33/21; 528, 11.7/11.9, −0.2 [−2.8, +2.5], 15/16; 2,703, 20.9/22.1, −1.2 [−2.8, +0.1], 47/79 | `final_tables.txt` (rates, discordant); intervals `finish_monty.txt` | R |
| Monty-ARC `re-arc` 600, 12.0/13.3, 2/10 | `final_roles.txt`; interval `research/generator_control.json` | R |
| One column: 236, 11.0/15.7, −4.7 [−9.2, −0.5]; 4,904, 8.4/8.1, +0.3 [−0.4, +1.1]; 1,470, 1.8/0.7, +1.1 [−0.3, +2.9]; 1,278, 7.1/7.9, −0.8 [−3.0, +1.6]; 528, 17.2/17.0, +0.2 [−2.5, +2.8]; 2,703, 26.0/26.5, −0.4 [−3.4, +2.2] | `final_column.txt`; intervals `report.json` (it rounds PQA's test rate to 0.75, 1.09) | R |
| Exact p: Monty-ARC 0.24, 0.95, 0.04 (0.238, 0.951, 0.039), 0.15; 2020 program 0.84; Qwen 0.57 | `final_roles.txt`, `final_qwen.txt`: convolution, P(\|S\| ≥ \|obs\|). The judge's 0.035 was a Monte Carlo two-tail estimate | R |
| Expected sign splits 13.5:25.4, 7.5:10.3, 26.2:57.5 | `final_roles.txt` | R |
| 19.25:25.75 | `research/generator_control.md` §1 | D |
| 2020 program ARC-AGI-2 +0.4 | `finish_ice.txt` | R |
| −6.0 [−10.4, −1.7]; +4.1 [+0.3, +7.9] | `research/generator_control.json` `qwen_extras.vs_other`; `final_qwen.txt` section 8 gets −6.0 [−10.3, −1.7], +4.1 [+0.2, +8.0] with its own resampling | R |
| One-input run: −8.2 [−11.9, −4.5] (Table 7, C10, 6.5); 427 folds; 75.6% / 83.8% (323, 358 of 427); 13 / 48 (C10) | `final_stage_c.txt` §1: counts exact, own seed-0 interval [−11.8, −4.5]; interval from `research/generator_control.json` `stage_c.E` (the report's own) | R |
| −1.4 [−4.8, +1.9], paired by task; −6.8 [−10.3, −3.3], stage 2 on the same first pairs (C10) | `final_stage_c.txt` §5, own code, seed 0: −1.41 [−4.75, +1.90], −6.79 [−10.26, −3.31], equal to `generator_control.json` `stage_c.vs_stage2` | R |
| +7.2 [+2.7, +11.6], `re-arc` minus the one-input run, post hoc | `research/generator_control.md` §7 Table 8 (the interval is not in the JSON); `final_stage_c.txt` §6 gets +7.2 [+2.9, +11.7] with independent seed-0 bootstraps | R |
| 0.63% (1 of 160 = 0.625%) | `final_stage_c.txt` §2; `generator_control.json` `stage_c.rules.abc.joint` | R |
| ConceptARC public since 2023 | Reference [13]: TMLR 2023, arXiv:2305.07141 | D |
| T2c +10.5 [−4.2, +24.5] | `research/monty_heldout/results/concept_analysis.json`, `T2c.fc` | D |
| 77 hand-made tasks | `final_column.txt` | R |
| 9 events vs 5.53, one-sided p = 0.07 (C10) | `final_roles.txt` (0.071); `event_location.txt` | R |
| 12 each side (C10) | `revise_monty.txt` §1, row agi2 eval | R |
| Memorisation check (C10) | `revise_concept_qwen.txt` | R |
| 1–8 points (C10) | Table C10, Qwen rows: 1.0, 5.0, 5.1, 5.2, 8.2 | R |

## Section 7, Table 8

| Number | Source | Status |
|---|---|---|
| All of Table 8: 34.7, 47.0, 55.0, 45.5, 57.0, 51; 55.0, 42.0, 57.5, 91; 167 | `final_qwen.txt` section 6; `v8c_qwen.txt` §5 | R |
| v8c: Table 8 random column and Figure 3: 52.0 (49.0, 54.5) at three samples, 50.4 (47.5, 53.5) at four | `v8c_qwen.txt` §5: exact expectation over uniformly random orders of each test output's candidates; 5th and 95th percentiles of 100,000 orders. Replaces the mean, minimum and maximum of 40 orders, 52.0 (48.0, 55.5) and 51.0 (47.0, 56.0) | R |
| v8c: most unsolved tasks never solved by any of four samples: of the 75 single-test tasks, verified-first misses 41, of which 39 no sample solves | `v8c_qwen.txt` §5 | R |
| +13.0 [+7.0, +19.5]; +2.5 [0, +6.0] | `final_qwen.txt` section 6 | R |
| 7 of 167; 22–24 | `final_qwen.txt` section 11; `revise_merge.txt` | R |
| 49.0, 47.2, 46.5 at 128k | `finish_qwen.txt`, own replay, equal to the planned table | R |
| 3.9× (3.91), 1.94× | `final_qwen.txt` section 10 | R |
| n ≤ 3 at four runs | `research/arc2/faloo_qwen_sampling.md` §2 | D |
| 53.5, 55.0, −1.5 [−9.0, +6.0]; up to 9 of 120 | `finish_qwen.txt`; planned interval | R |
| 75 tasks; 39 and 13; 17 and 0.7 | `final_qwen.txt` section 6 (17.0, 0.69) | R |

## Appendix D, Table D1 (Section 8 and Table 9 before the reframe)

| Number | Source | Status |
|---|---|---|
| Motor +35.8 [+22.2, +50.2]; +24.1 [+14.7, +34.6]; +19.5 [+7.9, +33.7]; rollout +11.3 [−0.8, +25.4]; moving +1.1 [0.0, +3.4]; nearest +2.9 [−0.2, +7.0]; displacement −2.4 [−7.0, +1.2]; memory games −2.3 [−3.9, −0.8] | `final_column.txt` from raw game rows (own intervals within 0.4); intervals `report.json` | R |
| 19 vs 9; 145 vs 139 | `final_column.txt` | R |
| Object sensors +3 [0, +7]; +10 [+1, +25]; 4 of 50 types | `research/tbt_proper/column/results/analysis.json`, printed in `final_column.txt` | D |
| Count +4 [0, +10]; memory −11 [−29, +3] | same | D |
| 1 of 233; 0 of 120 | `final_tables.txt` from `column/dev/` | R |
| 11 of 518 | `revise_monty.txt`; 136 + 55 + 327 | R |
| 1 of 180; 83–91% | `misc_checks.txt`, from `concept_analysis.json` and `data.xlsx` | R |
| 109 of 116 | `research/monty_failure_analysis.md`. Judge: 109 with no candidate on `merge_c5.py`'s direct run | R |

## Section 8 (Section 9 before the reframe)

| Number | Source | Status |
|---|---|---|
| 4×L4; 12 h minus 10 min; 4.5 h; 16,384; 6,144; T 1.0, 0.95, 20; 10 s; 120 s; two rounds | `kaggle/tri/monty-arc-qwen-nvarc.ipynb`, `tools/build_tri.py`, `llm/kaggle/qwen_phase.py`, `kaggle/tri/kernel-metadata.json`; re-read this pass | D |
| 128 and 16 augmentations; 33.89 baseline | Notebook cells | D |
| 24.0 and 21.0; 21.0 and 18.0 (Table 9; Table 10 before the reframe) | `final_qwen.txt` section 11; `revise_merge.txt`; v8c: `v8c_qwen.txt` §6 re-implements the notebook's own merge cell (attempt and alt from `summarize()`, then confident Monty-ARC, extras) on `qwen38_ps_b16384.jsonl` and `qwen38_ps_xhigh_b16384.jsonl` sample 0, with Monty-ARC from this pass's own run (`v8c_monty_nb.json`, equal on 120 of 120 tasks to the earlier notebook-mode cache) | R |
| v8c: the v5 heuristic in the merge: evidence ≥ 0.99, 2:1 lead | Notebook's embedded `vote.py` (byte-identical to `arcmonty/vote.py`): `CONFIDENT = 0.99`; `confident()` needs the best fully evidenced answer to have at least twice the voters of the next | D |
| v8c: notebook at 16k in native order; FA-LOO's offline evidence at 32k in canonical order | Notebook: `QWEN_BUDGET_PER_ROUND = 16384`, embedded `qwen_phase.solve_task` takes `task["train"]` in file order; `research/arc2/faloo_qwen_sampling.md` §0 (32,768 per round; canonical order through `faloo_qwen.build`) | D |
| v8c: Kaggle's latest version of the kernel is v4-A | `research/paper/judge_v8c/audit/out/kmeta/` (the judge's pull of 2026-11-02: `QWEN_HOURS = 3.0`, `QWEN_ORDER = "small"`, `is_private: true`); not re-pulled in this pass (no Kaggle calls) | D |
| 20 tokens/s, 20 sequences; 6.5M; 10.8M; 60% | `llm/kaggle/qwen_phase.py` ("assume >= 20 tok/s per sequence", `concurrency=20`); 400 × 16,200 s = 6.48M; 240 × 2 × (16,384 + 6,144) = 10.81M; ratio 0.60. Public eval used 1.94 rounds per sample at 16k. An estimate from the code's floor; the true rate is not logged | R |
| Hidden tasks sized like training | Forum 745846 (median max input area 184.5 vs 551; 7.1% vs 40.8% multi-test). S: a participant's measure | S |
| 28–34 band | as Section 2 | S |
| +1.7 | `research/arc2_improve.md` §3(d). S: simulator output, reported only as a failed prediction | S |
| 1.25%; 3.3% | 1 − 0.05^(1/240) = 1.24%; 4/120 (`research/paper/judge_v8b/audit/merge_c5.py`, `eval_only.txt`) | R |
| Spurious zeros | Forum 751344, 751598. S: participants' reports | S |

## Section 9 (Section 10 before the reframe)

| Number | Source | Status |
|---|---|---|
| 18 tasks, 11 all right, [36, 83]; 6 tasks, [12, 88] | `misc_checks.txt`; `finish_ice.txt` | R |
| reframe: Where ARC solvers fail: 62 of 68; most of ARC-AGI-2's failing folds (22 of 31) | As Section 6.4 | R |
| reframe: "mostly" outside the range or proxies (9 of 10 pairs: 5 and 4; 1 two rules) | Appendix B's grouping; judged causes | R |
| reframe: 39 of 75 solved by no sample; a perfect ranker adds 2.5 | As Section 7 (+2.5 [0, +6.0]) | R |
| reframe: within a task, every Qwen set, all but ARC-AGI-2 for the 2020 program, some sets for Monty-ARC (4 of 6) and the one-column system (1 of 3) | Table 3's `ns` marks | R |
| 73–100; 30–94; 3–54 | Table 4: FA-LOO lowest 73.3; fit lowest 30.2, highest 94.2 (Qwen's one-input row); coverage 3.1–53.5 | R |
| 16 of 16, 13.3%, 2.4× | Section 6.4 | R |
| v8c: item 2, 55.0 of 57.5 at four samples | Table 8 | R |
| +2.1 [−1.7, +6.0] | `research/arc2/hint_ab.py`, re-run (`hint_ab_rerun.txt`) | R |
| 85% | `research/paper/sources/arc-prize-2026-arc-agi-2__prizes.md` | D |

## Appendices

| Number | Source | Status |
|---|---|---|
| 1.8 CPU-seconds | `research/monty_ablations.md` Table 1. S: a timing, not re-measured | S |
| Table A1 | `eval_only.txt`, `verify_numbers.txt` | R |
| Appendix B: lists and n | Wrong lists R, n R; causes judged | R/S |
| 514; 376 | `misc_checks3.txt` | R |
| Table C1, C2 arm counts, including 179, 148/154 | `eval_only.txt`, `verify_numbers.txt` | R |
| `canon` differences, including +168 [+48, +313]; p = 0.06, 0.13; 9:0, p = 0.004 | same; 2^−8 two-sided | R |
| 6 and 4 `canon`-only items; 2 confident and right | `research/monty_heldout.md`, frame table. S: a hand reading of per-item rows; the judge confirms | S |
| −4.5 [−12.5, 0.0]; +7.7 [+1.2, +17.3]; 41/47 vs 35/44 | `misc_checks3.txt` | R |
| Table C3, including 170/181; 164/175 | `eval_only.txt`, `verify_numbers.txt` | R |
| 9 vetoes; 4 of 9 vs 18 of 238; p = 0.004 | `revise_monty.txt` §7 | R |
| 39/54, 11/13, 166/178; +14.1, +32.9, +27.6 with intervals; 204 of 225; 12 of 20 | `revise_monty.txt` §3 | R |
| Table C4; 4 of 6; pass@2 changes | `verify_numbers.txt`; `revise_monty.txt` §6 | R |
| 8.2–8.5× CPU | `cpu_ratio.txt` | R |
| Table C5 | `final_qwen.txt` section 11, own code, equal to `revise_merge.txt`. "Reversed" is `['mg','mc','qu','qv']` in `revise_merge.py` | R |
| Table C6 unseen columns | `finish_monty.txt` | R |
| Table C6 public eval column | `eval_only.txt` | R |
| Coverage and pass@2; clusters equal | `finish_monty.txt`, `revise_monty.txt` §4 | R |
| 22 of 23; 6 of 10 | `results/disagree.json` (`misc_checks3.txt`) | R |
| 3.6× and 2.6× CPU | `misc_checks.txt`, from `research/monty_faloo.md`. S: not re-measured | S/R |
| 142 of 172; 23/30, 56/150; 13/19, 22/25 | `misc_checks2.txt`; `revise_monty.txt` §4 | R |
| 4/4, 3/3, 3/6; 2.6% (3 of 114) | `research/monty_faloo.md`; `eval_only.txt` | R/S |
| 5/5; 6/17 | `finish_monty.txt` | R |
| +18.1 [+4.3, +33.9]; 44/54, 4/10, 7/71 | `unseen_check.txt`; `finish_monty.txt` | R |
| Table C7 | `finish_qwen.txt`, `finish_monty.txt`, `finish_ice.txt` | R |
| v8c: Table C7 caption, plain (a) with the full run verified 248/261 (without, 249/264 = 94.3%, three Copy8 pairs differ) | `v8c_qwen.txt` §2 | R |
| Table C7 caption: the one-input run uses each task's first test pair only | `final_stage_c.txt` §0 (every record's query ids name `test:0` only); Addendum 4 ("first test pair by file order") | R |
| Table C8: events 5 of 514, 20, 4, 54; none with two; 1/1.15, 9/5.53, 1/0.76, 11/13.5; 0.19, 1.88, 0.67, 1.22%; worst case | `final_roles.txt` for the three unseen sets; `eval_only.txt` and `event_location.txt` for public eval (not recomputed by the judge either) | R |
| 15 to 34 times; 125 | Ratios 15.1, 33.9, 20.5; 124.6 | R |
| 8,266; 1,205; 2,725; 6,228 | `eval_only.txt`, `misc_checks.txt`, `final_roles.txt` (roles 1,761 + 677 + 3,604 + 186) | R |
| 123 of 130 | `finish_ice.txt` | R |
| Evidence measure: 44/54, 11/82, +68.1 [+51.5, +82.6]; 11/12, 9/43, +70.7 [+48.0, +87.9]; 170/181, 28/146, +74.7 [+61.2, +82.9]; 19/20, 6/13, +48.8 [+18.6, +78.0]; 8/8, 1/9; 120/128, 17/125 | `finish_monty.txt`; `generator_control.json`; `research/tbt_proper/report.md` §6 | R/D |
| Top answer 40.4, 36.4, 60.6; 37.9, 44.3, 67.0, 64.6; +35.4, +46.3, +29.2, +35.4 with intervals | `finish_monty.txt`, `finish_ice.txt` | R |
| Wilson [65, 100], [94, 100] | `finish_qwen.txt` | R |
| 0.91; 5 of 20; 78.1%, 7.5% | `finish_qwen.txt`, greedy section | R |
| Overlap 7 of 52, 5 of 36, 14 of 341, 0 of 17 | `finish_ice.txt` | R |
| Stops 12, 2; 11, 7, 4; `re-arc` 9, 2, 1 | `finish_qwen.txt`, `final_qwen.txt` | R |
| One-input run: stops 6, 1, 1 of 9, one passes; p = 0.013 | `final_stage_c.txt` §2 (first failing condition, as for the other runs) | R |
| AboveBelow9: the full run and both folds give one output, which keeps the lower half; contact 1 cell against 3 in both demonstrations, 1 against 4 in the test | `final_stage_c.txt` §7. The programs' rule (keep the side touching the line with fewer cells) is hand-read from the raw records' code; judged | R/S |
| Retrying 8 non-fitting folds adds one task, right: 80/81 | `final_stage_c.txt` §4 (8 not fitting, 7 fit at the first retry, 1 at the second; 9 runs; Copy3 added); `generator_control.json` `stage_c.retry` | R |
| v8c: Table C9 `ns` marks: every interval that includes 0 (ends at 0.0 included, as in Table 3); hand-made fresh within-task cell, 3 tasks, no interval | The intervals in the table; Table 3's marks | R |
| Table C9 one-input row: 96.0% (322) = 309/322; 48.4% (93) = 45/93; +47.6 [+37.9, +57.1]; +41.0 [+27.6, +54.5] (52); 146/155; 79/80 | `final_stage_c.txt` §3, §2: counts exact, own seed-0 intervals [+38.2, +57.0], [+27.9, +54.8]; intervals from `generator_control.json` `stage_c.split_verified` | R |
| 3 of 471; 1 of 87 | `revise_monty.txt` §2; `final_roles.txt`/`research/generator_control.json` | R/D |
| 4 of 21, 0 of 32, 21 of 205, 0 of 12; 18, 7; a third (170 of 480) | `finish_ice.txt` | R |
| Generator extras: no replacement; 4 of 800; 106/106, 8/9, 18/18; 127 tasks, 71/71, 55.9%; 30 preemptions | `research/generator_control.md` Addendum 1, §1, §3 | D |
| 7–12 points; 80.6 [58.3, 93.0], 88.0; 77.3 [46.2, 94.1], 88.9; 83.8 [34.0, 94.0], 93.6 | `selfcal_own.txt` | R |
| Replay at 192k: 55.0, 52.0; 48.2 at 174k; 64k; about 290k; 246k; 7 tasks | `finish_qwen.txt` | R |
| Folds vs plain: 45.5, 47.0, −1.5 [−6.0, +3.0]; 52.0, 55.0, −3.0 [−10.0, +4.0]; 56.0; −0.011 [−0.041, +0.018]; 1.61×; 0.375, 2.1× | `finish_qwen.txt`, `final_qwen.txt` section 10; planned intervals | R |
| Column extras: 369 lines; 22:17 UTC; 5 of 23, 36 of 248; 16 of 66, 9 of 17; 126 of 960, 137 of 253; 21, 1; 0 of 30; −4.4 [−11.1, +1.7]; −2.7 [−13.1, +5.5]; 1.0, 9, 4 | `research/tbt_proper/report.md`, `report.json`, `column/results/post_hoc.json`, `final_column.txt`, `final_tables.txt`, `column/PLAN.md` §0.8 | R/D |
| Hand-made sets: 26, 9, 20, 25 pairs; 2 pairs excluded | `column/PLAN.md` §0.2 | D |
| 58, 249, 91%; 8–21 of 30 | `misc_checks.txt`; `finish_ice.txt` | R |
| 20%, 17% labels | `research/monty_failure_analysis.md`. S: LLM-assisted, judged | S |
| 44-minute smoke run | `kaggle/tri/push_smoke2.log` | D |

## Rates and intervals derived from the counts above

So that every token traces. Each rate is the count it comes from, rounded.

| Number | Source | Status |
|---|---|---|
| v8c: Table 3 one-input row: 96.0, 48.4, +47.6, +41.0 (52); planned (Addendum 4, item 3) | `v8c_qwen.txt` §4: 309/322, 45/93, +47.6, own seed-0 interval [+38.2, +56.8]; within +41.0 over 52 tasks [+27.9, +54.5]; C9's intervals are the planned analysis's | R |
| Table 3, rates: 79.8, 6.5; 75.8, 8.6; 91.7, 22.1; 80.0, 9.4; 90.9, 6.2; 97.2, 20.8; 94.6, 40.3; 62.7, 10.9; 88.5, 8.0; 70.6, 3.8; 0.0, 0.8 | The split counts in Table C9 | R |
| Table 4, rates: 58.1, 79.5; 51.7, 88.9; 65.6, 93.6; 63.6; 73.1, 95.7; 92.0; 72.6; 92.7; 94.2, 98.8; 93.0; 49.0, 73.3; 63.2, 90.6; 83.1, 96.2; 70.7; 62.9, 88.9; 46.4; 30.2, 96.1 | The rule counts in Table C9 | R |
| Table C3: 48/49 = 98.0, 57/58 = 98.3, 15/20 = 75.0, 197/198 = 99.5; 36/37; 45/54; 11/12; −1.9 [−6.2, 0.0]; +0.2 [0.0, +2.3] | `eval_only.txt`, `verify_numbers.txt` | R |
| Table C5: 24.0, 21.0, 28.5; 23.0, 19.0, 26.5; 23.5 (22.0, 24.0), 20.2 (19.0, 21.0), 23.9 (20.5, 26.5); 24.0, 21.0, 20.5; 23.0, 19.0, 18.5; 21.0, 18.0, 25.5; 7, 9, 58 | `final_qwen.txt` section 11 | R |
| Table C6: 43/65 = 66.2 [54.2, 77.4]; 43/74 = 58.1 [41.4, 73.4]; 15/29 = 51.7 [33.3, 70.0]; 187/285 = 65.6 [39.5, 82.1]; 35/36 = 97.2 [90.6, 100.0]; 42/49 = 85.7 [74.2, 95.2]; 11/11; 167/178 = 93.8 [82.9, 98.3]; 41/42 = 97.6 [92.1, 100.0]; 35/44 = 79.5 [64.4, 92.3]; 8/9 = 88.9 [63.6, 100.0]; 161/172 = 93.6 [79.1, 98.3]; +31.5 [+20.6, +43.1]; +31.1 [+20.1, +42.9]; +27.6 [+11.3, +45.4]; +48.3 [+30.0, +66.7]; +28.2 [+13.4, +47.0]; +0.4 [0.0, +1.6]; −6.2 [−15.1, +1.8]; −11.1 [−36.4, 0.0]; −0.2 [−4.2, +0.1]; 8.2, 9.5; 9.2, 12.1; 6.0, 13.4; 19.1, 22.0; 76.9, 51.4; 88.9, 51.7; 75.9, 45.0 | `finish_monty.txt`, `eval_only.txt`, `revise_monty.txt` §4 | R |
| Table C7: 86/86 [95.8, 100]; 239/240; 249/264 = 94.3; 417/450 = 92.7; 421/480 = 87.7; 48.3; 0/480; 11/17; 14/21; 182/480; 9/480; 4/480; 55/136; 23, 18 | `finish_qwen.txt`, `finish_monty.txt`, `finish_ice.txt` | R |
| Table C9: FA-LOO minus top answer intervals [+1.1, +61.7], [+35.1, +57.6], [+12.8, +46.3], [+18.8, +52.1]; [+7.5, +57.4], [+13.2, +44.6] and [−1.1, +29.3] of fold agreement | `finish_ice.txt`, `revise_monty.txt` §3 | R |
| Table C10, Qwen: 359, 19.8/14.5, 23.0/4.2; 32.9/27.9, 28.5/10.67; 427, 76.1/81.2, 18.67/40.33 | `finish_qwen.txt` | R |
| Table C10, one-input row: 427, 75.6/83.8, 13/48; Table C9: 96.0, 48.4 | `final_stage_c.txt` §1, §3 | R |
| Evidence ≥ 0.99, the rule's threshold | `arcmonty/vote.py`, `research/monty_heldout.md` §0 | D |
| Table C8: 1.0, 4.2, 2.7, 6.0; 24.2, 28.3, 22.7, 25.0 | `eval_only.txt`, `final_roles.txt` | R |

## Citations

| Ref | Checked against | Note |
|---|---|---|
| [1], [13], [15], [17], [18], [19], [20] | arXiv API, read 2026-11-01 | [17]: "attempting induction first, then transduction" read in the PDF. [18]: current arXiv title. [20]: abstract read |
| [2], [4], [5], [6], [9], [12] | `external/judge/arxiv/refs.xml` | [6]: current arXiv title |
| [3] | Frontiers article page, read 2026-11-01 | Article number not shown, so not cited |
| [7] | `external/tbp.monty` on disk | |
| [8] | Repository page, read 2026-11-01 | Authors confirmed |
| [10] | `.claude/skills/nvidia-kaggle-skill/data/discussions.db` | Threads 745846, 751344, 751598 read this pass |
| [11] | `external/judge/cora/repo`; author from its git log | |
| [14] | `external/heldout/mini-arc/README.md` | |
| [16] | Hugging Face model card, read 2026-11-01 | |
| [21] | `research/icecuber_faloo.md` §0 and §7; `gh api` read 2026-11-01 | Author as printed in arXiv:2402.03507, ref 59 |
| [22] | JMLR page and PDF, read 2026-11-02 | Definition 6: the consistent selective strategy takes any hypothesis in the version space, and rejects points not in the maximal agreement set. Noise-free, finite class in that part |
| [23] | ICML 2008 PDF, read 2026-11-02 | The enumeration algorithm answers only when all hypotheses in the version space agree; class finite, observations noise free. Pages 568–575 not printed in the reference |
| [24] | arXiv abstract, read 2026-11-02 | Uses self-agreement of sampled answers and conformal prediction to set the threshold |
| [25] | Listing of the second edition, read 2026-11-02 via web search | Chapter title "Testing Exchangeability" seen in a publisher-derived listing, not the chapter itself. Cited only for its existence |
| [26] | `research/generator_control.md` §0 and Addendum 1 | Commit and licence checked on the VM by that agent |
| [27] | `research/tbt_proper/column/PLAN.md` §0.2 | Commit `41441c3f` |
| [28] | arXiv API and PDF of 2006.02544, read 2026-11-03 | Title and authors as printed; journal_ref "Advances in Neural Information Processing Systems 33 (NeurIPS 2020)"; CV+ set eq. (11), Theorem 2 |
