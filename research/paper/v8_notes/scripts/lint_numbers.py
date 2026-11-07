"""Every numeric token in paper.md should occur in numbers.md, or be structural. Prints the rest for a human check."""
import os  # noqa: E402  (release: paths from the repo root)
_REPO = os.environ.get("ARC_MONTY_ROOT", os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..")))  # repo root
import re
ROOT = (_REPO + "/research/paper/v8/")
p = open(ROOT + "paper.md", encoding="utf8").read()
n = open(ROOT + "numbers.md", encoding="utf8").read()
p = p[:p.find("## References")] + p[p.find("## Appendix A"):]
p = re.sub(r"\$[^$]*\$", " ", p)
p = re.sub(r"`[^`]*`", " ", p)
p = re.sub(r"\[[0-9, –]+\](?!\()", lambda m: m.group(0) if re.search(r"[+−-]", m.group(0)) else " ", p)
toks = set(re.findall(r"\d[\d,]*\.?\d*", p))
miss = sorted(t.rstrip(",.") for t in toks if t.rstrip(",.") not in n)
print(len(toks), "tokens;", len(miss), "not found in numbers.md:")
print(miss)
