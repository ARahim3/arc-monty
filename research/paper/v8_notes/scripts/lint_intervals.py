"""Every bracketed interval in paper.md must occur, after normalising signs and zeros, in a computed output file."""
import os  # noqa: E402  (release: paths from the repo root)
_REPO = os.environ.get("ARC_MONTY_ROOT", os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..")))  # repo root
import glob, json, re
N = (_REPO + "/research/paper/v8_notes/")
def norm(t):
    t = t.replace("−", "-").replace("+0.0", "0.0").replace("-0.0", "0.0")
    t = re.sub(r"(?<![\d.])\+0(?![\d.])", "0", t)
    t = re.sub(r"\[([+-]?[\d.]+),\s*([+-]?[\d.]+)\]", lambda m: f"[{m.group(1).lstrip('+')},{m.group(2).lstrip('+')}]", t)
    return t
corpus = ""
for f in glob.glob(N + "*.txt"):
    corpus += open(f, encoding="utf8").read() + "\n"
corpus += open((_REPO + "/research/arc2/faloo_qwen_sampling.md"), encoding="utf8").read() + "\n"
corpus = norm(corpus)
p = open((_REPO + "/research/paper/v8/paper.md"), encoding="utf8").read()
p = p[:p.find("## References")] + p[p.find("## Appendix A"):]
ivs = set(re.findall(r"\[[+−-]?[\d.]+, [+−-]?[\d.]+\]", p))
print(len(ivs), "intervals")
miss = [i for i in sorted(ivs) if norm(i) not in corpus]
print("not found in computed outputs:", miss)
# fractions in the paper's tables
fr = set(re.findall(r"\b\d+/\d+\b", p))
missf = [x for x in sorted(fr) if not re.search(r"(?<!\d)" + re.escape(x) + r"(?!\d)", corpus)]
print(len(fr), "fractions; not found:", missf)
