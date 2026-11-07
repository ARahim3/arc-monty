"""Score a Kaggle save-run submission.json against known ARC-AGI-2 solutions (public eval + training).

The ARC-AGI-2 competition's visible arc-agi_test_challenges.json (used in save runs) holds 240 training tasks, so a
save run's output shows whether the notebook reproduces local accuracy inside Kaggle's environment.
Usage: python research/paper/scripts/score_kaggle_saverun.py research/paper/data/monty_v5_kaggle_saverun_submission.json
"""
import json
import sys
from pathlib import Path

sub = json.load(open(sys.argv[1]))
known = dict(json.load(open("data/kaggle_format/agi2_eval_solutions.json")))
for split in ("training", "evaluation"):
    for f in Path(f"data/arc-agi-2/data/{split}").glob("*.json"):
        known.setdefault(f.stem, [p["output"] for p in json.load(open(f))["test"]])
score = n = 0
for k, atts in sub.items():
    if k not in known:
        continue
    outs, n = known[k], n + 1
    score += sum(j < len(outs) and outs[j] in (a["attempt_1"], a["attempt_2"]) for j, a in enumerate(atts)) / len(outs)
print(f"{len(sub)} tasks in submission, {n} with known solutions: {score:.2f} correct ({100 * score / max(n, 1):.2f}%)")
