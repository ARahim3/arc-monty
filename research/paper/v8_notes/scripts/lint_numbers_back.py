"""Reverse of lint_numbers.py: numeric tokens in numbers.md's first column that no longer occur in paper.md. Prints them for a human check."""
import os  # noqa: E402  (release: paths from the repo root)
_REPO = os.environ.get("ARC_MONTY_ROOT", os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..")))  # repo root
import re
ROOT = (_REPO + "/research/paper/v8/")
p = open(ROOT + "paper.md", encoding="utf8").read()
n = open(ROOT + "numbers.md", encoding="utf8").read()
toks_p = set(t.rstrip(",.") for t in re.findall(r"\d[\d,]*\.?\d*", p))
out = []
for line in n.splitlines():
    if not line.startswith("|") or line.startswith("|---") or line.startswith("| Number") or line.startswith("| Ref"):
        continue
    first = line.split("|")[1]
    first = re.sub(r"`[^`]*`", " ", first)
    for t in re.findall(r"\d[\d,]*\.?\d*", first):
        t = t.rstrip(",.")
        if t not in toks_p:
            out.append((t, first.strip()[:70]))
print(len(out), "tokens in numbers.md, first column, not in paper.md:")
for x in out:
    print(" ", x)
