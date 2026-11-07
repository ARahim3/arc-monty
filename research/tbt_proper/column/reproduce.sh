#!/bin/zsh
ARC_MONTY_ROOT=${ARC_MONTY_ROOT:-$(cd "$(dirname "$0")/../../.." && pwd)}  # repo root
# Reproduce the one-column results. Mac, at most 4 workers. Reads data as JSON or npz; runs no game code and nothing from external/.
# Order as in PLAN.md section 0.9. About 7 hours: games 5.4 h, static 0.6 h, frozen Monty-ARC 1 h, E2 4 min.
cd $ARC_MONTY_ROOT && source .venv/bin/activate
C=research/tbt_proper/column
python -I -B $C/fresh_check.py > /dev/null                 # overlap and quality check, JSON only; results/fresh_check.json
python -I -B $C/run_all.py games static monty library      # refuses to run unless FROZEN.json matches; resumable
python -I -B $C/analyse.py                                 # results/analysis.json, every planned comparison and verdict
python -I -B $C/post_hoc.py                                # results/post_hoc.json, labelled post hoc
python -I -B $C/verify.py                                  # results/verify.json: hash, re-score of samples, one game re-run
