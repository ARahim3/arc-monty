"""ARC tasks, prompts, answer parsing and pass@2 scoring for the LLM column.

Grids are shown as rows of digits with no separators plus explicit dimensions. Both
Qwen3.8 and Nanbeige4.3 tokenise every digit separately (checked 2026-10-26), so this
costs one token per cell, the cheapest unambiguous layout.
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.environ.get("ARC_DATA", os.path.join(HERE, "..", "..", "data", "kaggle_format"))


def load_eval(data_dir=DATA):
    ch = json.load(open(os.path.join(data_dir, "agi2_eval_challenges.json")))
    sol = json.load(open(os.path.join(data_dir, "agi2_eval_solutions.json")))
    return ch, sol


def grid_text(g):
    return "\n".join("".join(str(int(v)) for v in row) for row in g)


def show(g, name):
    return f"{name} ({len(g)}x{len(g[0]) if g else 0}):\n{grid_text(g)}"


def examples_text(task):
    parts = []
    for i, p in enumerate(task["train"], 1):
        parts += [f"## Example {i}", show(p["input"], "Input"), show(p["output"], "Output"), ""]
    for j, t in enumerate(task["test"], 1):
        parts += [f"## Test input {j}", show(t["input"], "Input"), ""]
    return "\n".join(parts).rstrip()


# ---------------------------------------------------------------- harness (a): direct
DIRECT_SYSTEM = ("You are an expert at solving ARC-AGI puzzles. Each puzzle has a few input->output "
                 "example pairs that share one hidden transformation rule. Grids are 2D arrays of "
                 "digits 0-9 (colours); 0 is usually the background.")

DIRECT_INSTRUCTIONS = """Solve this ARC puzzle. The examples share one hidden transformation rule. Work out the rule, check it against every example, then apply it to the test input(s).

At the very end of your answer, give each test output grid as rows of digits inside its own ```grid code block, in test order, with nothing else in the block."""


def direct_messages(task):
    return [{"role": "system", "content": DIRECT_SYSTEM},
            {"role": "user", "content": DIRECT_INSTRUCTIONS + "\n\n" + examples_text(task)}]


def parse_grids(text, n_tests):
    """The last n_tests digit-only fenced blocks (```grid preferred, any fence accepted)."""
    blocks = re.findall(r"```(?:grid)?[^\n]*\n(.*?)```", text or "", re.S)
    grids = []
    for b in blocks:
        rows = [r.strip().replace(" ", "").replace(",", "") for r in b.strip().splitlines() if r.strip()]
        if rows and all(r.isdigit() for r in rows) and len({len(r) for r in rows}) == 1:
            if len(rows) <= 30 and len(rows[0]) <= 30:
                grids.append([[int(c) for c in r] for r in rows])
    return grids[-n_tests:] if len(grids) >= n_tests else None


# ---------------------------------------------------------------- harness (b): program synthesis
PS_SYSTEM = ("You are an expert at solving ARC-AGI puzzles by writing Python programs. Each puzzle "
             "has a few input->output example pairs that share one hidden transformation rule. "
             "Grids are 2D lists of integers 0-9 (colours); 0 is usually the background.")

PS_INSTRUCTIONS = """Find the transformation rule that maps EVERY example input to its output, then write it as a Python function.

Requirements:
- Define `def transform(grid: list[list[int]]) -> list[list[int]]:`.
- Use only the Python standard library and numpy.
- The function must work for every example input AND the test input(s); do not hard-code example outputs.
- Return a new 2D list of ints 0-9 (numpy arrays are accepted).

Your program will be run on every example input and checked cell by cell. Reason about the rule first, then give the final program in ONE ```python code block."""


def ps_messages(task):
    return [{"role": "system", "content": PS_SYSTEM},
            {"role": "user", "content": PS_INSTRUCTIONS + "\n\n" + examples_text(task)}]


CODE_RE = re.compile(r"```(?:python|py)?[^\n]*\n(.*?)```", re.S)


def extract_code(text):
    if not text:
        return None
    blocks = [b for b in CODE_RE.findall(text) if "def transform" in b]
    if blocks:
        return blocks[-1].strip()
    i = text.rfind("def transform")
    return ("import numpy as np\n" + text[i:].strip()) if i >= 0 else None


def diff_text(expected, got, max_cells=900):
    re_, ce = len(expected), len(expected[0])
    rg, cg = len(got), len(got[0]) if got else 0
    if (re_, ce) != (rg, cg):
        return (f"Wrong output SIZE: expected {re_}x{ce}, your program returned {rg}x{cg}.\n"
                + show(expected, "Expected") + "\n" + show(got, "Your output"))
    wrong = sum(expected[r][c] != got[r][c] for r in range(re_) for c in range(ce))
    if re_ * ce > max_cells:
        return f"{wrong} of {re_ * ce} cells are wrong (grid too large to print the diff)."
    rows = ["".join("." if expected[r][c] == got[r][c] else str(got[r][c]) for c in range(ce))
            for r in range(re_)]
    return (f"{wrong} of {re_ * ce} cells are wrong.\n" + show(expected, "Expected") + "\n"
            + f"Your output, with CORRECT cells shown as '.' ({re_}x{ce}):\n" + "\n".join(rows))


def feedback_text(train_res, train, max_examples=2):
    n_ok = sum(r["ok"] for r in train_res)
    lines = [f"Your program reproduced {n_ok} of {len(train_res)} examples."]
    shown = 0
    for i, (r, pair) in enumerate(zip(train_res, train), 1):
        if r["ok"] or shown >= max_examples:
            continue
        shown += 1
        lines.append(f"\n## Example {i} failed")
        lines.append(f"Error: {r['error']}" if r.get("error") else diff_text(pair["output"], r["output"]))
    lines.append("\nRe-examine the rule against ALL examples, then give the corrected complete "
                 "program in ONE ```python code block.")
    return "\n".join(lines)


# ---------------------------------------------------------------- scoring
def pass2(sub, sol):
    """sub[tid] = list over tests of [grid1, grid2] (None allowed). Returns (score, per_task)."""
    per = {}
    for tid, truths in sol.items():
        rows = sub.get(tid) or []
        hit = 0
        for j, truth in enumerate(truths):
            cands = rows[j] if j < len(rows) else []
            hit += any(c is not None and c == truth for c in cands[:2])
        per[tid] = hit / len(truths)
    return sum(per.values()), per


def top2(cands):
    """Two distinct grids from an ordered candidate list."""
    out = []
    for g in cands:
        if g is not None and g not in out:
            out.append(g)
        if len(out) == 2:
            break
    return out
