"""Final pass lint: every bracketed interval and every fraction in paper.md must occur in a computed output or a primary report. Prints what does not."""
import os  # noqa: E402  (release: paths from the repo root)
_REPO = os.environ.get("ARC_MONTY_ROOT", os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..")))  # repo root
import glob, json, re
R = (_REPO + "/research/")
N = R + "paper/v8_notes/"
def norm(t):
    t = t.replace("−", "-").replace("+0.0", "0.0").replace("-0.0", "0.0")
    t = re.sub(r"(?<![\d.])\+0(?![\d.])", "0", t)
    t = re.sub(r"\(([+-]?[\d.]+),\s*([+-]?[\d.]+)\)", lambda m: f"[{float(m.group(1)):.1f},{float(m.group(2)):.1f}]", t)
    t = re.sub(r"\[([+-]?[\d.]+),\s*([+-]?[\d.]+)\]", lambda m: f"[{m.group(1).lstrip('+')},{m.group(2).lstrip('+')}]", t)
    return t
corpus = ""
for f in glob.glob(N + "*.txt"):
    corpus += open(f, encoding="utf8").read() + "\n"
for f in ("arc2/faloo_qwen_sampling.md", "generator_control.md", "tbt_proper/report.md", "tbt_proper/paper_section.md", "icecuber_faloo.md"):
    corpus += open(R + f, encoding="utf8").read() + "\n"
corpus = norm(corpus).replace(",", ",").replace(" ", " ")
compact = corpus.replace(", ", ",")
p = open(R + "paper/v8/paper.md", encoding="utf8").read()
p = p[:p.find("## References")] + p[p.find("## Appendix A"):]
ivs = set(re.findall(r"\[[+−-]?[\d.]+, [+−-]?[\d.]+\]", p))
miss = [i for i in sorted(ivs) if norm(i).replace(", ", ",") not in compact]
print(len(ivs), "intervals; not found:", miss)
fr = set(re.findall(r"\b\d[\d,]*/\d[\d,]*\b", p))
c2 = compact.replace(",", "")
missf = []
for x in sorted(fr):
    y = x.replace(",", "")
    if not re.search(r"(?<!\d)" + re.escape(y) + r"(?!\d)", c2):
        missf.append(x)
print(len(fr), "fractions; not found:", missf)
