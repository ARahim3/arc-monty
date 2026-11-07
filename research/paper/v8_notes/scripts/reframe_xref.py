"""Reframe pass: print every cross-reference in paper.md (Section, subsection, Appendix, Table, Figure) with its line,
and whether its target exists as a heading or caption. Ends with a summary; exit code 1 if any target is missing.
    .venv/bin/python research/paper/v8_notes/scripts/reframe_xref.py [paper.md]"""
import os  # noqa: E402  (release: paths from the repo root)
_REPO = os.environ.get("ARC_MONTY_ROOT", os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..")))  # repo root
import re, sys

p = sys.argv[1] if len(sys.argv) > 1 else (_REPO + "/research/paper/v8/paper.md")
lines = open(p, encoding="utf8").read().split("\n")

# Targets
sec, sub, app, tab, fig = set(), set(), set(), set(), set()
for l in lines:
    if m := re.match(r"^## (\d+)\. ", l): sec.add(m.group(1))
    if m := re.match(r"^### (\d+\.\d+) ", l): sub.add(m.group(1))
    if m := re.match(r"^## Appendix ([A-Z])\. ", l): app.add(m.group(1))
    for m in re.finditer(r"\*\*Table ([A-Z]?\d+)\.", l): tab.add(m.group(1))
    for m in re.finditer(r"!\[\*\*Figure (\d+)\.", l): fig.add(m.group(1))
print("targets: sections", sorted(sec, key=int), "subsections", sorted(sub), "appendices", sorted(app))
print("         tables", sorted(tab, key=lambda t: (t[0].isalpha(), t[0] if t[0].isalpha() else "", int(re.sub(r"\D", "", t)))),
      "figures", sorted(fig))

LIST = r"([A-Z]?\d+(?:\.\d+)?(?:\s*(?:–|-|,| and |, and )\s*[A-Z]?\d+(?:\.\d+)?)*)"


def labels(txt):
    out = []
    for part in re.split(r"\s*(?:,| and )\s*", txt):
        part = part.strip()
        if not part:
            continue
        if "–" in part or re.search(r"\d-[A-Z\d]", part):
            a, b = re.split(r"–|-", part)
            pa, na, nb = re.match(r"([A-Z]?)(\d+)", a).groups()[0], int(re.sub(r"\D", "", a)), int(re.sub(r"\D", "", b))
            if "." in a:  # subsection range such as 5.1–5.4
                out += [a, b]
            else:
                out += [f"{pa}{k}" for k in range(na, nb + 1)]
        else:
            out.append(part)
    return out


def exists(kind, lab):
    if kind == "Section":
        return (lab in sub) if "." in lab else (lab in sec)
    if kind == "Appendix":
        return lab in app
    if kind == "Table":
        return lab in tab
    if kind == "Figure":
        return lab in fig


refs = []
in_refs = False
for i, l in enumerate(lines, 1):
    if l.startswith("## References"):
        in_refs = True
    elif l.startswith("## Appendix A"):
        in_refs = False
    if in_refs or l.startswith("#"):
        continue
    caption_own = re.findall(r"\*\*Table ([A-Z]?\d+)\.", l) + re.findall(r"!\[\*\*Figure (\d+)\.", l)
    for kind, pat in (("Section", r"\bSections? " + LIST), ("Appendix", r"\bAppendix ([A-Z])\b"),
                      ("Appendix", r"\bAppendices ([A-Z](?:(?:, | and |, and )[A-Z])*)"),
                      ("Table", r"\bTables? " + LIST), ("Figure", r"\bFigures? " + LIST)):
        for m in re.finditer(pat, l):
            labs = re.split(r", | and |, and ", m.group(1)) if kind == "Appendix" else labels(m.group(1))
            for lab in labs:
                if kind in ("Table", "Figure") and lab in caption_own and m.group(0).startswith(kind + " " + lab) and \
                        l[max(0, m.start() - 2):m.start()] in ("**", "[*"):
                    continue  # the caption's own label
                refs.append((i, kind, lab, l[max(0, m.start() - 30):m.end() + 20].replace("\n", " ")))
    # bare table labels such as "C10" and bare subsections such as "(6.1, 6.2)", "in 6.5", "which 5.4 uses"
    for m in re.finditer(r"(?<![A-Za-z ]Table )(?<!Tables )(?<!, )(?<! and )(?<!–)\b(C\d+)\b", l):
        if not re.search(r"Tables? [^.]*$", l[:m.start()][-40:]):
            refs.append((i, "Table", m.group(1), l[max(0, m.start() - 30):m.end() + 10]))
    for m in re.finditer(r"(?:\(|\bin |, |which |T2c in )(\d\.\d)(?=\)|,| uses|;)", l):
        if not re.search(r"Sections? [\d., and–]*$", l[:m.start() + 1]):
            refs.append((i, "Section", m.group(1), l[max(0, m.start() - 30):m.end() + 15]))
    if i < 60:  # Section 1 roadmap: "(7)", "(8)", "(9)"
        for m in re.finditer(r"\((\d)\)", l):
            refs.append((i, "Section", m.group(1), l[max(0, m.start() - 30):m.end() + 5]))

bad = 0
for i, kind, lab, ctx in sorted(refs):
    ok = exists(kind, lab)
    bad += not ok
    print(f"L{i:<4d} {kind:8s} {lab:5s} {'ok' if ok else 'MISSING'}  …{ctx}…")
print(f"\n{len(refs)} references; {bad} with no target.")
used = {(k, lab) for _, k, lab, _ in refs}
for kind, pool in (("Table", tab), ("Figure", fig), ("Appendix", app)):
    never = sorted(t for t in pool if (kind, t) not in used)
    print(f"{kind} targets never referred to in the text: {never}")
sys.exit(1 if bad else 0)
