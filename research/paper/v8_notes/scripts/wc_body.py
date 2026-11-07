"""Body word counts for paper.md: title through conclusion (before ## References). Words split on whitespace, with table bars and math left as tokens."""
import os  # noqa: E402  (release: paths from the repo root)
_REPO = os.environ.get("ARC_MONTY_ROOT", os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..")))  # repo root
import re, sys
s = open(sys.argv[1] if len(sys.argv) > 1 else (_REPO + "/research/paper/v8/paper.md")).read()
body = s[: s.index("## References")]
intro_i = body.index("## 1.")
def stats(t, name):
    lines = t.split("\n")
    table = [l for l in lines if l.lstrip().startswith("|")]
    prose = [l for l in lines if not l.lstrip().startswith("|")]
    pw = " ".join(prose).split(); tw = [w for w in " ".join(table).split() if w.strip("|-: ") != ""]
    num = lambda L: sum(bool(re.search(r"\d", w)) for w in L)
    print(f"{name}: prose words {len(pw)}, table words {len(tw)}, total {len(pw) + len(tw)}; numeric tokens per 100 words: prose {100 * num(pw) / max(1, len(pw)):.1f}, all {100 * (num(pw) + num(tw)) / max(1, len(pw) + len(tw)):.1f}")
stats(body, "title to conclusion")
stats(body[intro_i:], "section 1 to conclusion")
for m in re.finditer(r"^## (.+)$", body, re.M):
    pass
secs = re.split(r"(?m)^(?=## )", body)
for sec in secs:
    h = sec.split("\n")[0][:40]
    p = [l for l in sec.split("\n") if not l.lstrip().startswith("|")]
    print(f"  {h:42s} prose {len(' '.join(p).split()):5d}")
