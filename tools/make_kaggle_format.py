"""Write ARC-AGI-2 public eval in the Kaggle file format (one challenges file, one solutions file).

The LLM harness (llm/arcllm/tasks.py) and research/paper/scripts/complementarity.py read
data/kaggle_format/agi2_eval_{challenges,solutions}.json (override the folder with $ARC_DATA).
Run after cloning ARC-AGI-2 into data/arc-agi-2 (see README):
    python tools/make_kaggle_format.py
"""
import glob
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "data", "arc-agi-2", "data", "evaluation")
OUT = os.path.join(ROOT, "data", "kaggle_format")

if __name__ == "__main__":
    challenges, solutions = {}, {}
    for f in sorted(glob.glob(os.path.join(SRC, "*.json"))):
        task = json.load(open(f))
        key = os.path.basename(f)[:-5]
        challenges[key] = {"train": task["train"], "test": [{"input": t["input"]} for t in task["test"]]}
        solutions[key] = [t["output"] for t in task["test"]]
    os.makedirs(OUT, exist_ok=True)
    json.dump(challenges, open(os.path.join(OUT, "agi2_eval_challenges.json"), "w"))
    json.dump(solutions, open(os.path.join(OUT, "agi2_eval_solutions.json"), "w"))
    print(f"wrote {len(challenges)} tasks to {OUT}")
