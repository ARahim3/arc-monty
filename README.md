# Monty-ARC and FA-LOO: code for "Verified Is Not Generalised"

Code and result files for the ARC Prize 2026 paper-track writeup *"Verified Is Not Generalised: Held-Out
Re-Induction, a Distribution-Free Bound, and Where ARC Solvers Fail"* by **Abdur Rahim** (Kaggle, track ARC-AGI-2).
Paper (PDF): https://github.com/ARahim3/arc-monty/blob/main/paper/paper.pdf.

## What this release contains

- **The frozen Monty-ARC v5 solver** (`arcmonty/`): eight numpy learning modules, unchanged since the v5 Kaggle
  version. Every Monty-ARC number in the paper comes from this code, and the experiments below import it unchanged.
- **The FA-LOO rule's evaluation scripts**, for four learners:
  - Monty-ARC on the development sets (`research/monty_eval/`);
  - Monty-ARC on unseen sets: ConceptARC, MinimalTasks, Mini-ARC and 1D-ARC (`research/monty_heldout/`);
  - Qwen3.8-27B, greedy and sampling (`research/arc2/faloo_qwen*.py`, `faloo_analyze.py`,
    `faloo_sampling_analyze.py`, `research/arc2/vm/`);
  - the 2020 Kaggle first-place program (`research/icecuber_faloo/`, our wrapper scripts only).
- **The generator control** (`research/generator_control/`): three learners on 200 fresh tasks drawn from re-arc's
  generators, so exchangeability holds by construction. `data/` holds the generated tasks and checks.
- **The one-column system** (`research/tbt_proper/`): a new small program, not Monty. It has one column class in 42
  copies and was frozen by hash before any test data (`column/FROZEN.json`).
- **The named notebook**, version 3 of [`rahim3/monty-arc-qwen-nvarc`](https://www.kaggle.com/code/rahim3/monty-arc-qwen-nvarc?scriptVersionId=362731624) (submission 57726521, public
  score 32.64), and the hybrid notebook (57689321, 28.47). `kaggle/README.md` gives their SHA-256 and the byte-exact
  rebuild command. The `.ipynb` files are not included, because they embed NVARC code.
- **The paper**: `paper/paper.pdf` (19 pages), its Markdown source `paper/paper.md`, the Kaggle writeup
  `paper/writeup.md`, and `paper/figures/`.
- The paper's analysis scripts (`research/paper/v8_notes/scripts/`). The three independent judges' recount scripts
  are not included in this repository.
- The earlier experiments:
  - a Qwen3.8-27B program-synthesis harness (`llm/`);
  - the notebook builders (`tools/`);

**Third-party code is not included.** NVARC, `michaelhodel/re-arc` and `top-quarks/ARC-solution` are fetched by the
user; see [Third-party notices](#third-party-notices).

## Monty-ARC

**Monty-ARC** is a solver for ARC-AGI-1/2 inspired by the Thousand Brains Theory and the Thousand Brains Project's
[Monty](https://github.com/thousandbrainsproject/tbp.monty). It re-implements Monty's ideas for discrete grids; it
contains no Monty code. It has eight numpy learning modules (self-model, periodic, behaviour, dynamics, composition,
association, pattern, field). It uses no training data and needs 1–2 CPU-seconds per task. Each module:

1. enumerates hypotheses, each a rule in an object-centric reference frame (D8-canonical poses);
2. keeps the hypotheses that reproduce every demonstration;
3. scores them by **leave-one-out (LOO) evidence**: it predicts each demonstration from the others, Monty's "predict
   the next sensation" test;
4. votes: identical answers pool evidence across modules.

Monty-ARC solves only 3.3% of ARC-AGI-2 public eval, but its confident answers are almost always right.
**Fold-agreement LOO (FA-LOO)** re-runs the whole system on every *n*−1 subset of the demos. It answers only when all
folds predict their held-out demo and agree on the test. That bounds P(answer ∧ wrong) by 1/(*n*+1) under
exchangeability. Under FA-LOO, Monty-ARC answers 102 of 1,147 distinct tasks and is wrong once.

## Kaggle notebooks

| Notebook | What |
|---|---|
| [rahim3/monty-arc-thousand-brains-arc-agi-2](https://www.kaggle.com/code/rahim3/monty-arc-thousand-brains-arc-agi-2) (v5) | Pure Monty-ARC, CPU only. Its script is `kaggle/monty-arc/monty_arc_kernel.py`. `python tools/build_kernel.py` rebuilds it byte for byte from `arcmonty/`. Its top docstring still describes v0 (2 modules); the embedded code is v5 (8 modules). |
| [rahim3/monty-arc-nvarc-hybrid](https://www.kaggle.com/code/rahim3/monty-arc-nvarc-hybrid) (v3) | The public NVARC fork plus Monty-ARC (7 modules: it was built before `field.py`). Submission 57689321, public score 28.47. The file is not included here, because it embeds NVARC code; its SHA-256 is in `kaggle/README.md`. |
| `rahim3/monty-arc-qwen-nvarc` (v3): https://www.kaggle.com/code/rahim3/monty-arc-qwen-nvarc?scriptVersionId=362731624 | **The named submission.** Qwen3.8-27B program synthesis for 4.5 h, then the NVARC fork, with Monty-ARC v5 on CPU throughout. Submission 57726521, public score 32.64. The file is not included here, because it embeds NVARC code. `python tools/build_tri.py cheap` rebuilds it byte for byte from the NVARC fork as pulled on 2026-10-26; its SHA-256 is in `kaggle/README.md`. |

`tools/build_tri_v4.py` builds the v4 variants. The builders pull the public NVARC fork themselves (see
[Notebook builders](#notebook-builders)). The submitted notebooks embed the fork's cells (`arc_loader.py`,
`arc_decoder.py`, `arc_solver.py`, `starter.py` and the fork's notes), so this repo does not include them. It contains no
NVARC text. `kaggle/README.md` gives their SHA-256 and lists which cells are the fork's.

## Repository layout

```
arcmonty/                 Monty-ARC v5: objects.py (frames, D8), symmetry.py (self-model), periodic.py, behavior.py,
                          dynamics.py, composition.py, association.py, pattern.py, field.py, vote.py, monty_arc.py
                          (module list); data.py, evaluate.py, report.py, bench.py (local helpers)
paper/                    the paper: paper.pdf (19 pages), paper.md (its Markdown source), writeup.md (the Kaggle
                          writeup), figures/ (the four figures and the cover, PNG)
kaggle/README.md          the two submitted notebooks (not included): Kaggle links, refs, scores, SHA-256, rebuild
kaggle/monty-arc/         the published pure-Monty Kaggle script (generated by tools/build_kernel.py) + metadata
tools/                    notebook builders (build_kernel, build_hybrid, build_tri, build_tri_v4), calibration.py,
                          make_cover.py, make_kaggle_format.py, gpu_quota.py
llm/                      Qwen program-synthesis harness: arcllm/ (engine, sandbox, tasks), run_bench.py, score.py,
                          emulate_budgets.py; kaggle/qwen_phase*.py (Kaggle 4xL4 phase + CPU test);
                          vm/ (vLLM-TPU setup/serve/run scripts); results/ (benchmark outputs, JSONL, and
                          qwen38_faloo_*.jsonl, the raw FA-LOO records the paper's Qwen tables are recounted from)
research/                 result files behind the writeup: report_v1e.txt, calibration.json,
                          monty_ablations.{md,json}, monty_faloo.{md,json}, monty_failure_analysis.md
research/monty_eval/      ablations, FA-LOO, per-module LOO audit, failure analysis; cache.tar.gz (cached module
                          candidates and folds, 1.2 MB); results/ (small JSON); labels/ (failure labels)
research/paper/           scripts/ (first-draft figures, subset runs, complementarity, word count), data/, figures/
                          (all figure files: PNG, PDF, SVG, written by the scripts); v8/numbers.md (the paper's number
                          ledger)
research/arc2/            tri-notebook improvement experiments (time model, Qwen arms, Monty hints); FA-LOO on
                          Qwen3.8, greedy (faloo_qwen.*) and sampling (faloo_qwen_sampling.*); vm/ (TPU scripts)
research/monty_heldout/   frozen Monty-ARC v5 on unseen sets: wrappers, analysis, small results
                          (report: research/monty_heldout.{md,json})
research/icecuber_faloo/  FA-LOO on the 2020 first-place program: job, check and analysis scripts, vm/ wrappers,
                          results_*.json (report: research/icecuber_faloo.{md,json})
research/generator_control/  the generator control: scripts, vm/, ice/ and monty/ wrappers, data/ (200 generated
                          tasks and checks), results/ (report: research/generator_control.{md,json})
research/tbt_proper/      the one-column system: column/ (frozen code, FROZEN.json, PLAN.md, reproduce.sh, summary
                          results), spikes/; proposal.md, report.{md,json}, paper_section.md
research/paper/v8_notes/  scripts/ (the paper's analysis scripts: figures, tables, number checks, cover), their .txt
                          and .json outputs, titles.md, errors_fixed.md, figures_notes.md
```

## Setup

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# ARC datasets from the official repos (not vendored). These are the commits used for every number here.
git clone https://github.com/fchollet/ARC-AGI data/arc-agi-1
git -C data/arc-agi-1 checkout 399030444e0ab0cc8b4e199870fb20b863846f34
git clone https://github.com/arcprize/ARC-AGI-2 data/arc-agi-2
git -C data/arc-agi-2 checkout f3283f727488ad98fe575ea6a5ac981e4a188e49
python tools/make_kaggle_format.py        # data/kaggle_format/agi2_eval_{challenges,solutions}.json (LLM harness)
```

`arcmonty.data` reads `data/arc-agi-{1,2}/data/{training,evaluation}/*.json`. Run every command from the repo root.

Scripts find the repo root from their own location; set `ARC_MONTY_ROOT` to override. `ARC_MONTY_SCRATCH` sets the
judges' scratch directory (default: the system temp directory). The TPU scripts under `*/vm/` need the `gcloud` CLI
and `GCP_PROJECT` (your Google Cloud project id).

## Reproducing the writeup

These tables cover the Monty-ARC and Qwen results. Their section and figure numbers refer to an earlier draft
of the writeup. The experiments added for the final paper are in the [next section](#experiments-added-for-the-final-paper).

Every number below comes from the listed command. Commands marked *(cached)* run in seconds from the shipped
results. The others re-run Monty-ARC; `arcmonty.report` and `tools/calibration.py` use 12 worker processes.

**Monty-ARC accuracy and timing (Table 1, abstract)**

| Claim | Command | Check against |
|---|---|---|
| pass@2: AGI-2 eval 3.3% (4/120; 3/114 without the 6 ARC-AGI-1 tasks), AGI-2 train 12.3%, AGI-1 eval 11.5%, AGI-1 train 20.0%; confident 3/3, 85/87, 33/34, 58/59; ~1–2 CPU-s/task | `python -m arcmonty.report agi2-eval agi1-eval agi2-train agi1-train` | `research/report_v1e.txt` (timings vary by machine) |
| 233 ARC-AGI-2-only training tasks: 9/233 (3.9%), confident 3/3 | `python research/paper/scripts/subset_eval.py agi2-only 1 3 research/paper/data/agi2_only_p1.json` | `research/paper/data/agi2_only_p1.json` |
| Cover: top-answer correctness by LOO evidence, 1,147 unique tasks (100/104 at LOO 1.0) | `python tools/calibration.py` (rewrites `research/calibration.json`), then `python research/paper/scripts/make_cover_unique.py` *(cached from the second step)* | `research/paper/figures/cover_calibration_unique.png` |
| Figure 1, the system diagram | `python research/paper/scripts/make_system_diagram.py` | `research/paper/figures/system_diagram.png` |

**LOO evidence and FA-LOO (§4)**

| Claim | Command | Check against |
|---|---|---|
| Rule table: FA-LOO + (c) 101/102 (99.0%; 187/189 over the 4 splits); v5 rule 96/98; perspective voting under FA-LOO 58/58; worst-case bound 24.7% vs measured 0.09%; 2.6× CPU; per-module LOO audit | `tar -xzf research/monty_eval/cache.tar.gz -C research/monty_eval`, then `python research/monty_eval/faloo.py --persp8 agi1-train`, then `python research/monty_eval/make_faloo_md.py` *(cached)* | `research/monty_faloo.md`, `research/monty_faloo.json` |
| Fit-to-demos only: 99/142 (70%) on AGI-2 training vs 85/87 with LOO | `python research/monty_eval/make_tables.py` *(cached, after extracting the cache)* | `research/monty_ablations.md` Table 7 |
| Perspective voting re-enabled: pass@2 83 vs 80, false confident answers 1 → 4 (AGI-1 train) | `python research/paper/scripts/subset_eval.py agi1-train 8 4 research/paper/data/agi1_train_p8.json` (~8 CPU-s/task) | `research/paper/data/agi1_train_p8.json` |
| Demo-order symmetry of the learner | `python research/monty_eval/sym_check.py agi2-eval agi1-eval` | `research/monty_eval/results/sym_check.json` |

**Ablations and failure analysis (§5, §6)**

| Claim | Command | Check against |
|---|---|---|
| Columns are complementary: removing a module loses exactly its unique solves; composition 58 of 126 ARC-AGI-1 solves, 1 of 13 ARC-AGI-2; Figure 2 | `python research/monty_eval/make_tables.py` and `python research/monty_eval/make_figure.py` *(cached)* | `research/monty_ablations.md`, `research/paper/figures/module_contributions.png` |
| Behaviour frames: canonical 29, grid-aligned 24, both 31 tasks | `python research/paper/scripts/frame_ablation.py 3` | `research/paper/data/frame_ablation.json` |
| Failure by abstention (94% of unsolved AGI-2 eval tasks get no candidate); missing-ingredient table | `python research/monty_eval/ablate.py` (writes `results/per_task_full.jsonl`), then `python research/monty_eval/failure_data.py` and `python research/monty_eval/merge_labels.py` *(cached, after extracting the cache)* | `research/monty_failure_analysis.md`, `research/monty_eval/results/{failure_data,labels_merged}.json` |

The labels in `research/monty_eval/labels/` were written by LLM labelling agents, as the writeup says.

**LLM column and leaderboard (§5)**

| Claim | Command | Check against |
|---|---|---|
| Qwen3.8-27B program synthesis on AGI-2 eval: 25.5/120 (21.2%) pass@2; verified programs right on test 29/37 | `cd llm && python score.py results/` *(cached)* | row `qwen38 ps 16384` |
| Qwen + Monty-ARC merge: 28.5/120, 0 tasks lost; Monty-only solves 0934a4d8, 135a2760, dbff022c | `python research/paper/scripts/complementarity.py 3` (re-runs Monty-ARC on eval) | `research/paper/data/complementarity.json` |
| Monty-ARC v5 inside Kaggle: 30/240 = 12.5% on the visible (training) tasks of the save run | `python research/paper/scripts/score_kaggle_saverun.py research/paper/data/monty_v5_kaggle_saverun_submission.json` *(cached)* | `research/paper/data/monty_v5_kaggle_saverun_check.txt` |
| Leaderboard scores (0.00, 0.00, 28.47, 32.64) | Kaggle submissions of the notebooks above; see [Notebook builders](#notebook-builders) | Kaggle leaderboard |

The Qwen results were generated on a TPU v6e-8 with vLLM-TPU 0.32.0 and bf16 weights: 16k thinking tokens per round,
≤ 2 rounds, 2 samples. The scripts are `llm/vm/setup.sh`, `download.sh qwen38`, `serve.sh qwen38 8001`, and
`run_model.sh qwen38 8001 ps`. The client works with any OpenAI-compatible `/v1/completions` server.

**Writeup length**: `python research/paper/scripts/wordcount.py <draft.md>` counts words the way the 1,500-word limit
is read: title, subtitle, body, tables and references.

**Rebuilding the cache from scratch** (CPU hours):
1. `python research/monty_eval/run_modules.py --procs 8 agi2-eval agi1-eval agi2-train agi1-train`
2. `python research/monty_eval/run_folds.py --procs 4 --persp 0 agi2-eval agi1-eval agi2-train agi1-train`
3. `python research/monty_eval/run_persp.py --procs 4 agi1-train`
4. `python research/monty_eval/run_folds.py --procs 4 --persp 1-7 agi1-train`

## Experiments added for the final paper

Each report starts with its plan (section 0), written before the data or the learner's output existed, and lists its
own commands. None of these experiments changes `arcmonty/`. The reports, summary JSON and scripts are included; the raw
model and program outputs are not (sizes below), except the raw Qwen FA-LOO records. Those are in `llm/results/qwen38_faloo_*.jsonl` (19 MB),
because the paper's Qwen tables are recounted from them. `llm/score.py` skips them: they carry a `kind` field. The ConceptARC stage of the sampling analysis also reads `research/monty_heldout/results/concept_base.jsonl` (15 MB), included.

| Experiment | Report | Scripts | Not included |
|---|---|---|---|
| Frozen Monty-ARC v5 on unseen sets | `research/monty_heldout.{md,json}` | `research/monty_heldout/` (`run_cache.py`, `analyse.py`, `extras.py`, `summary.py`, `make_md.py`) | ConceptARC with MinimalTasks, Mini-ARC, 1D-ARC (see below); the fold cache (297 MB) and per-task results (66 MB) |
| FA-LOO on greedy Qwen3.8-27B, ARC-AGI-2 eval | `research/arc2/faloo_qwen.{md,json}` | `research/arc2/faloo_qwen.py`, `faloo_analyze.py`, `vm/*faloo*` | a TPU v6e-8 and the Qwen3.8 weights, to re-generate. The raw records are included: `llm/results/qwen38_faloo_greedy_b16384.jsonl` and `_C.jsonl` |
| FA-LOO on sampling Qwen3.8-27B, ARC-AGI-2 eval and ConceptARC | `research/arc2/faloo_qwen_sampling.{md,json}` | `research/arc2/faloo_qwen_sampling.py`, `faloo_sampling_analyze.py`, `vm/orchestrate_sampling.py`, `vm/*sampling*` | the same, to re-generate; ConceptARC for stage 2. The raw records are included: `llm/results/qwen38_faloo_sampling{,_plain,_concept}_b32768.jsonl` |
| FA-LOO on the 2020 first-place program | `research/icecuber_faloo.{md,json}` | `research/icecuber_faloo/` (`make_jobs.py`, `make_checks.py`, `analyse.py`, `verify.py`, `make_report.py`), `vm/` | `top-quarks/ARC-solution`, built on a large CPU VM by `vm/setup.sh`; job files and raw runs (36 MB) |
| Generator control | `research/generator_control.{md,json}` | `research/generator_control/` (`select_generators.py`, `make_tasks.py`, `qwen_gc.py`, `analyse.py`, `verify.py`, `make_report.py`), `vm/`, `ice/`, `monty/` | `michaelhodel/re-arc` (needed only to regenerate `data/`); raw outputs (`raw/` 39 MB, `ice/raw` and `ice/export` 24 MB, `monty/cache` 2.5 MB) |
| One column, frozen once | `research/tbt_proper/report.{md,json}`, `paper_section.md`, `proposal.md` | `research/tbt_proper/column/reproduce.sh` (about 7 h on a Mac), `spikes/` | `neoneye/arc-dataset-collection`, ConceptARC, Mini-ARC, 1D-ARC, and the ARC-AGI-3 recordings made by `research/arc3_wm/record.py`; per-task results (23 MB) |

**Frozen files.** `research/tbt_proper/column/run_all.py` refuses to run unless the seven frozen files match
`FROZEN.json`. Two of them, `data_sets.py` and `monty_fresh.py`, set `ROOT` to the author's absolute project path. They
are left byte-identical so that the hashes still match. To run elsewhere, edit `ROOT` in both files. `run_all.py` will
then refuse to run, because the hashes no longer match, until you remove its check.

**Paper scripts.** `research/paper/v8_notes/scripts/` holds the scripts behind the final paper's figures, tables and
number checks. `fig_*.py` write to `research/paper/figures/`; `paper/figures/` holds PNG copies for the Markdown paper.
The scripts expect the paper at `research/paper/v8/paper.md` and `writeup.md`; in this repo those files are at
`paper/paper.md` and `paper/writeup.md`. Some of the scripts also read raw files that are not in this repo. They are
included as a record.

## Notebook builders

The ARC-AGI-2 builders embed `arcmonty/` (and, for tri, `llm/kaggle/qwen_phase*.py` and `llm/arcllm/`) into a
public NVARC-fork notebook. The fork is not in this repo. Fetch it first:

```bash
kaggle kernels pull mikelou1/arc-agi2-lb33-89-minimal-perfpatch -p kaggle/nvarc-fork-src/mikelou1 -m
python tools/build_kernel.py           # -> kaggle/monty-arc/   (pure Monty-ARC, byte-identical to the published v5)
python tools/build_hybrid.py           # -> kaggle/hybrid/      (NVARC fork + Monty-ARC)
python tools/build_tri.py cheap        # -> kaggle/tri/         (Qwen3.8 + NVARC + Monty-ARC, v3)
python tools/build_tri_v4.py cheap qwen_hours=3.0 order=density nv_verified=1 qorder=small   # -> kaggle/tri-v4/ (v4-A)
python research/arc2/test_tri_v4.py    # offline checks of the v4 build against the v3 build
```

The generated notebooks use these public Kaggle inputs, which are not part of this repo:
- the model `sorokin/qwen3_4b_grids15_sft139` (NVARC);
- the model `foysalemonshanto/qwen3-8-27b-fp8-repacked-v1` (Qwen3.8-27B FP8);
- the datasets `mirzamilanfarabi/arc3-vllm-h100-wheelhouse-v3`, `keithtyser/taaf-duck-qwen38-serving-v1` and
  `zbigniewkirchner/gemma-4-agent-local-eval-pythons`.

The generated folders are git-ignored.

Two caveats:
- The hybrid v3 that scored 28.47 was built before `field.py` existed. Rebuilding today gives an 8-module hybrid.
- The fork's code changes upstream, so a rebuild may differ from the submitted versions.

## Licence

The original code, scripts and result files in this repository are © 2026 Abdur Rahim (Kaggle `rahim3`,
GitHub `ARahim3`). They are licensed under the **Creative Commons Attribution 4.0 International** licence
([CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)); the full text is in [`LICENSE`](LICENSE). Third-party
material keeps its own licence (below).

## Third-party notices

The repo vendors no third-party source files, datasets or notebooks. It does reference, adapt or interoperate with
the following:

| Component | Licence | How it is used here |
|---|---|---|
| [ARC-AGI-1](https://github.com/fchollet/ARC-AGI), [ARC-AGI-2](https://github.com/arcprize/ARC-AGI-2) | Apache 2.0 | Data, cloned by the user (not vendored). Result files contain Monty-ARC's and Qwen's predicted grids for those tasks. |
| [Thousand Brains Project / Monty](https://github.com/thousandbrainsproject/tbp.monty) | MIT | Concepts only; no Monty code is included. |
| NVARC ([github.com/1ytic/NVARC](https://github.com/1ytic/NVARC); Kaggle fork `mikelou1/arc-agi2-lb33-89-minimal-perfpatch`) | GitHub repo: no licence file; Kaggle notebook: Kaggle's terms for public notebooks | Not vendored. The submitted notebooks contain the fork's cells, so they are not included (see `kaggle/README.md`). `tools/build_tri*.py` quote no NVARC lines: they find the fork's task-queue loop at build time by its first and last statements, and a comment gives its location. Get the fork with `kaggle kernels pull` (see [Notebook builders](#notebook-builders)). |
| [`michaelhodel/re-arc`](https://github.com/michaelhodel/re-arc), commit `e5b7f1d06362a76f9d3b8c25154ff1fafca897ce` | MIT (© 2024 Michael Hodel) | Not included. `research/generator_control/vm/gen_rearc.py` imports its generators on a VM. `research/generator_control/data/` holds the 200 tasks they generated. |
| [`top-quarks/ARC-solution`](https://github.com/top-quarks/ARC-solution) (the 2020 Kaggle first-place program), commit `9407072659de1270358c2ba34c527785214dd68b` | MIT (© 2020 top-quarks) | Not included. `research/icecuber_faloo/vm/setup.sh` clones and builds it on a VM and changes one line: `eval = 1` in `src/runner.cpp`, its README's switch for test data. The result files hold its answers on our jobs. |
| [ConceptARC](https://github.com/victorvikram/ConceptARC) (with MinimalTasks), commit `0e67da6af879e4bad3d7cd3c196e8d551b445725` | MIT | Not included; clone to `external/judge/conceptarc/repo`. The result files hold task names and scores only. |
| [Mini-ARC](https://github.com/KSB21ST/MINI-ARC), commit `792d082c40d496f2f106f63fa7125bb115c8230b` | Apache 2.0 | Not included; clone to `external/heldout/mini-arc`. |
| [1D-ARC](https://github.com/khalil-research/1D-ARC), commit `1e74dc4cb4c58d8160e1fbd0ba638eb745f37147` | MIT | Not included; clone to `external/heldout/1d-arc`. |
| [`neoneye/arc-dataset-collection`](https://github.com/neoneye/arc-dataset-collection), commit `41441c3f9a318c93682adb0225f59f3cdb693bd2` (subsets `arc-community`, `nosound`, `dbigham`, `Sequence_ARC`, `arc-dataset-tama`, `PQA`) | per subset; see each subset's readme | Not included; clone to `external/tbt_fresh/repo`. The result files hold task names and scores only. |
| [`madarshbb/arc-qwen-3-8-27b-agent`](https://www.kaggle.com/code/madarshbb/arc-qwen-3-8-27b-agent) (Kaggle notebook) | Kaggle's terms for public notebooks | `llm/kaggle/qwen_phase*.py` follow its vLLM flag ladder and its libcuda symlink fix (attributed in the code). |
| vLLM-TPU (`tpu_inference`) | Apache 2.0 | `llm/vm/patch_v4.py` patches the installed package in place on TPU v4. It quotes a two-line anchor from it. |
| Qwen3.8-27B (Qwen team) | see the model card | Model weights, downloaded by the user. |
| arc-skill ([github.com/pbshgthm/arc-skill](https://github.com/pbshgthm/arc-skill)), CORA, OPINE-World, Tycho, Reki's dead-signature heuristic | — | Cited in the writeup; no code used. |
