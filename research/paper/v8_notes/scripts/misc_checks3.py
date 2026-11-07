"""v8 paper: remaining re-derivations. Read-only; single process; no solver or model run."""
import os  # noqa: E402  (release: paths from the repo root)
_REPO = os.environ.get("ARC_MONTY_ROOT", os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..")))  # repo root
import json, os, re, sys
ROOT = _REPO
HL = os.path.join(ROOT, "research/monty_heldout")
sys.path.insert(0, HL)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "llm"))
sys.path.insert(0, os.path.join(ROOT, "research/paper/scripts"))
import numpy as np
from stats import Data, f, load_rows, prec_diff, fmtd
from hl_common import task_of
# frames and behaviour-removed precision differences, ConceptARC
r = load_rows(os.path.join(HL, "results/concept_base.jsonl"))
d = Data(r, tasker=task_of)
print("FA-LOO canon minus abs", fmtd(prec_diff(d, d.vec("sys:canon", f("fc")), d.vec("sys:abs", f("fc")))))
print("FA-LOO no behaviour minus full", fmtd(prec_diff(d, d.vec("-behavior", f("fc")), d.vec("full", f("fc")))))
print("FA-LOO both minus canon", fmtd(prec_diff(d, d.vec("full", f("fc")), d.vec("sys:canon", f("fc")))))
# disagreement table
D = json.load(open(os.path.join(HL, "results/disagree.json")))
print("disagree pooled", json.dumps(D.get("pooled"))[:500])
G = json.load(open(os.path.join(HL, "results/dev_gap.json")))
print("dev_gap keys", list(G)[:6], json.dumps(G.get("concept"))[:300])
# ARC-AGI-1 eval tasks also in ARC-AGI-2 training
from arcmonty.data import load_split
a1e, a2t, a1t, a2e = set(load_split("agi1-eval")), set(load_split("agi2-train")), set(load_split("agi1-train")), set(load_split("agi2-eval"))
print("agi1-eval in agi2-train", len(a1e & a2t), "agi1-train in agi2-train", len(a1t & a2t), "agi2-eval in agi1-eval", len(a2e & a1e), "union eval", len(a1e | a2e), "union all", len(a1e | a2e | a1t | a2t))
# Qwen alone and merge, as merge_order.py
from complementarity import _monty, _top2
from arcllm.tasks import load_eval, pass2
from score import load, ps_cands
ch, sol = load_eval()
mon = dict(_monty(x) for x in sorted(ch.items()))
recs = load(os.path.join(ROOT, "llm", "results"))[("qwen38", "ps", 16384)]
def score(order):
    sub = {}
    for t in ch:
        n = len(ch[t]["test"]); q = ps_cands(recs, t, n); m = mon[t]; sub[t] = []
        for j in range(n):
            g = dict(qv=[x for x, v in q[j] if v], qu=[x for x, v in q[j] if not v], mc=(m["confident"][j] if j < len(m["confident"]) else []), mg=(m["guesses"][j] if j < len(m["guesses"]) else []))
            sub[t].append(_top2(sum((g[k] for k in order), [])))
    return pass2(sub, sol)[0], sub
print("Qwen alone (qv, qu)", score(["qv", "qu"])[0], "| merged", score(["qv", "mc", "qu", "mg"])[0])
# Leadholm abstract mention of voting
x = open(os.path.join(ROOT, "external/judge/arxiv/refs.xml"), encoding="utf8").read()
for e in re.findall(r"<entry>.*?</entry>", x, flags=re.S):
    if "2507.04494" in e:
        s = re.search(r"<summary>(.*?)</summary>", e, flags=re.S).group(1).replace("\n", " ")
        i = s.lower().find("voting")
        print("Leadholm abstract:", s[max(0, i - 200):i + 200])
