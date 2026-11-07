# Submitted notebooks (not included)

This folder describes the two ARC-AGI-2 notebooks submitted to the Kaggle competition `arc-prize-2026-arc-agi-2`. The
`.ipynb` files themselves are **not included**, because they embed the NVARC fork's code (see below). Get them from
Kaggle, or rebuild the named notebook byte for byte with `tools/build_tri.py`. The SHA-256 values below identify the
exact files that were submitted.

| Notebook file | Kaggle notebook | Version | Submission ref | Public score | SHA-256 of the submitted file |
|---|---|---|---|---|---|
| `monty-arc-qwen-nvarc.ipynb` | [`rahim3/monty-arc-qwen-nvarc`](https://www.kaggle.com/code/rahim3/monty-arc-qwen-nvarc?scriptVersionId=362731624) | 3 | 57726521 | 32.64 | `2ead79a960be79636e46dd204b20e53cf7c3d36c9c1ef83d971da192e7fd5bf5` |
| `monty-arc-nvarc-hybrid.ipynb` | [`rahim3/monty-arc-nvarc-hybrid`](https://www.kaggle.com/code/rahim3/monty-arc-nvarc-hybrid) | 3 | 57689321 | 28.47 | `dd7405e44ea1ad29a171370fa46374a91ccc74f3b2522a9fec32d62d88755d67` |

## The named notebook: `rahim3/monty-arc-qwen-nvarc`, version 3

This is the paper's named submission, Tri v3. It runs three stages:

1. Qwen3.8-27B program synthesis for `QWEN_HOURS = 4.5`, on the tasks in reverse alphabetical order. The later
   Tri v4-A used `QWEN_HOURS = 3.0` and is not this notebook.
2. The NVARC fork, on every task without a verified Qwen program.
3. Monty-ARC v5 on CPU, throughout the run.

The merge priority is: verified program, then confident Monty-ARC answer, then NVARC, then guesses.

**Rebuild.** Pull the fork as described in the top-level README, then run `python tools/build_tri.py cheap`. This
writes `kaggle/tri/monty-arc-qwen-nvarc.ipynb` with the SHA-256 above. That was checked on 2026-11-07 against the fork
as pulled on 2026-10-26. If the fork has changed since then, the rebuild can differ.

## The hybrid notebook: `rahim3/monty-arc-nvarc-hybrid`, version 3

This is the NVARC fork plus Monty-ARC with 7 modules. `tools/build_hybrid.py` built it on 2026-10-26, before
`arcmonty/field.py` existed. Rebuilding today gives an 8-module notebook, so the rebuild is not byte-identical to the
submitted file.

## Third-party content

The notebooks on Kaggle contain cells of the public Kaggle notebook `mikelou1/arc-agi2-lb33-89-minimal-perfpatch`,
a fork of NVARC. NVARC upstream is github.com/1ytic/NVARC, which has no licence file. The fork's cells are
`arc_loader.py`, `arc_decoder.py`, `arc_solver.py`, `starter.py` and the fork's notes:

- `monty-arc-qwen-nvarc`:
  - cells 1, 2 and 6–9: verbatim (cell indexes are 0-based);
  - cell 10 (`starter.py`): patched so that NVARC skips tasks Qwen verified;
  - cells 11 and 12: the fork's launch and decoder cells, wrapped in `if not SKIP_ALL:`.
- `monty-arc-nvarc-hybrid`: cells 1 and 3–10, verbatim.

These cells are not covered by this repository's CC BY 4.0 licence; they remain their authors' work. The other cells
are this project's code, and this repository has their sources:

- the title cell and the run mode, written by `tools/build_tri.py`;
- the Monty-ARC cell (`arcmonty/` via `tools/build_hybrid.py`);
- the Qwen phase (`llm/kaggle/qwen_phase.py`, `llm/arcllm/`);
- the merge cell and the patches in cells 10–12.

**Inputs the notebooks attach** (public Kaggle resources, not included here):

- the model `sorokin/qwen3_4b_grids15_sft139` (NVARC);
- the model `foysalemonshanto/qwen3-8-27b-fp8-repacked-v1` (Qwen3.8-27B FP8, used by the named notebook only);
- the datasets `mirzamilanfarabi/arc3-vllm-h100-wheelhouse-v3`, `keithtyser/taaf-duck-qwen38-serving-v1` and
  `zbigniewkirchner/gemma-4-agent-local-eval-pythons` (named notebook only);
- the utility notebook `sorokin/pip-install-unsloth-flash-patch`.
