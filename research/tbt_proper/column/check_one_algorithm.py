"""Development check that "one algorithm" is true of the code: the column file names no task family, and the two ways of
delivering data give the same column. usage: python check_one_algorithm.py"""
import ast, os, random, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(HERE))))
import numpy as np
import column as C
from arcmonty.data import load_split

src = open(os.path.join(HERE, "column.py")).read()
code = "\n".join(l.split("#")[0] for l in re.sub(r'""".*?"""', "", src, flags=re.S).splitlines())
for word in ("game", "arc3", "arc-agi", "static", "agi1", "agi2", "task", "family", "level", "playfield"):
    print(f"{word!r} in column.py code:", len(re.findall(word, code, flags=re.I)))
classes = [n.name for n in ast.parse(src).body if isinstance(n, ast.ClassDef)]
print("classes:", classes, "| code lines:", sum(1 for l in code.splitlines() if l.strip()))
tasks = load_split("agi1-train"); names = sorted(tasks); random.Random(2).shuffle(names)
n = same = 0
for k in names[:40]:
    t = tasks[k]
    if not all(i.shape == o.shape for i, o in t["train"]):
        continue
    cfgs = [dict(kind="color", reach=3), dict(kind="nears", reach=2), dict(kind="mask", reach=6)]
    pop = C.Population(cfgs)
    for x, y in t["train"]:
        pop.observe(pop.predictions(x), x, y)
    cands = {c["index"]: c for c in C.hold_out(cfgs, t["train"], t["test"])}
    for i, c in enumerate(pop.cols):
        if i in cands:
            n += 1
            same += all(np.array_equal(p, c.predict(q)) for p, q in zip(cands[i]["preds"], t["test"]))
print("same answers, stream vs demos, full data:", same, "of", n)
