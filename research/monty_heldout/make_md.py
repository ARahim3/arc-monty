"""monty-heldout: assemble research/monty_heldout.md = header + section 0 (the plan, verbatim) + report_body.md with the tables from
results/summary_tables.md put in place. usage: python make_md.py"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hl_common import HERE, ROOT  # noqa: E402

path = os.path.join(ROOT, "research", "monty_heldout.md")
cur = open(path).read()
start = cur.index("## 0. Planned comparisons")
m = re.search(r"^## 1\. Verdicts", cur, flags=re.M)
plan = cur[start:(m.start() if m else len(cur))].rstrip() + "\n"
body = open(os.path.join(HERE, "report_body.md")).read()
tabs = open(os.path.join(HERE, "results", "summary_tables.md")).read()
parts = re.split(r"(?=^### Table \d+\.)", tabs, flags=re.M)
T = {}
for p in parts:
    mm = re.match(r"### Table (\d+)\.", p)
    if mm:
        T[mm.group(1)] = p.strip()
body = re.sub(r"\{\{T(\d+)\}\}", lambda x: T[x.group(1)], body)
ins = open(os.path.join(HERE, "p8_text.txt")).read().split("\n---\n")
body = body.replace("@@P8VERDICT@@", ins[0].strip()).replace("@@P8READING@@", ins[1].strip())
assert "{{T" not in body and "@@" not in body
head = ("# Testing the Thousand Brains claims on unseen tasks (frozen Monty-ARC v5)\n\n"
        "Agent: monty-heldout. Status: **final, 2026-10-31.** Section 0 was written before any new run or analysis and is unchanged, apart from one addendum marked as such. "
        "Sets: ConceptARC, plus Mini-ARC, 1D-ARC and MinimalTasks. `ns` in a table = the 95% CI includes 0, i.e. the comparison does not separate.\n\n")
open(path, "w").write(head + plan + "\n" + body)
print(len(head + plan + body.split("\n")[0]), "ok")
