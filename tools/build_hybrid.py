"""Build the hybrid notebook: NVARC public fork (mikelou1 perf-patch of the 33.89 baseline) + Monty-ARC columns.

Monty-ARC runs on CPU before the GPU pipeline (about a minute); after NVARC writes submission.json, every
test output where Monty-ARC reached a fully evidenced consensus and its answer is not already one of NVARC's two
attempts replaces NVARC's attempt_2 (pass@2 is order-free, so only NVARC's weaker guess is given up)."""
import copy
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_NB = os.path.join(ROOT, "kaggle/nvarc-fork-src/mikelou1/arc-agi2-lb33-89-minimal-perfpatch.ipynb")
SRC_META = os.path.join(ROOT, "kaggle/nvarc-fork-src/mikelou1/kernel-metadata.json")
OUT_DIR = os.path.join(ROOT, "kaggle/hybrid")
MODULES = ["__init__.py", "objects.py", "symmetry.py", "behavior.py", "dynamics.py", "composition.py", "association.py", "pattern.py", "periodic.py", "field.py", "vote.py", "monty_arc.py"]

MONTY_CELL = r'''# ===================== Monty-ARC columns (CPU, before the GPU pipeline) =====================
# Thousand-Brains-style learning modules (self-model + behavior), voted across D8 perspectives.
# Only fully evidenced consensus answers are kept; the merge cell at the end uses them.
import json, os, sys, time, signal, multiprocessing as mp
import numpy as np

MONTY_SOURCES = __MONTY_SOURCES__
_pkg = "/kaggle/working/_monty_pkg"
os.makedirs(os.path.join(_pkg, "arcmonty"), exist_ok=True)
for _n, _s in MONTY_SOURCES.items():
    with open(os.path.join(_pkg, "arcmonty", _n), "w") as _fh:
        _fh.write(_s)
with open("/kaggle/working/_monty_run.py", "w") as _fh:
    _fh.write("""
import json, os, sys, signal, time, multiprocessing as mp
import numpy as np
sys.path.insert(0, "/kaggle/working/_monty_pkg")
rerun = os.getenv("KAGGLE_IS_COMPETITION_RERUN")
base = "/kaggle/input/competitions/arc-prize-2026-arc-agi-2/"
path = base + ("arc-agi_test_challenges.json" if rerun else "arc-agi_evaluation_challenges.json")
def _alarm(*a): raise TimeoutError
def one(item):
    key, raw = item
    from arcmonty import monty_arc
    g = lambda x: np.array(x, dtype=np.int8)
    task = {"train": [(g(p["input"]), g(p["output"])) for p in raw["train"]], "test": [g(p["input"]) for p in raw["test"]]}
    signal.signal(signal.SIGALRM, _alarm); signal.alarm(120)
    try:
        from arcmonty.vote import attempts_from, confident
        cands = monty_arc.candidates(task)
        conf = confident(cands)
        best = attempts_from(task, cands)
        sure = attempts_from(task, cands, 0.99) if conf else [[] for _ in task["test"]]
    except Exception:
        conf, best, sure = False, [], []
    finally:
        signal.alarm(0)
    return key, {"confident": [[a.tolist() for a in x[:1]] for x in sure],
                 "guesses": [[a.tolist() for a in x[:2]] for x in best]}
if __name__ == "__main__":
    t0 = time.time()
    data = json.load(open(path))
    res = {}
    out = "/kaggle/working/monty_results.json"
    with mp.Pool(max(2, (os.cpu_count() or 2) // 2)) as pool:
        for n, (k, v) in enumerate(pool.imap_unordered(one, list(data.items()), chunksize=1), 1):
            if any(v["confident"]) or any(v["guesses"]):
                res[k] = v
            if n % 20 == 0 or n == len(data):  # incremental: a late kill still leaves usable results
                json.dump(res, open(out + ".tmp", "w"))
                os.replace(out + ".tmp", out)
    open("/kaggle/working/monty_done", "w").write("ok")
    n_conf = sum(any(v["confident"]) for v in res.values())
    print(f"[Monty-ARC] confident on {n_conf}/{len(data)} tasks, guesses on {len(res)} in {time.time()-t0:.0f}s")
""")
# start in the background at low priority: NVARC keeps its full GPU time budget; the merge waits a bounded time
import subprocess
_monty_proc = subprocess.Popen(["nice", "-n", "19", "python", "/kaggle/working/_monty_run.py"],
                               stdout=open("/kaggle/working/monty.log", "w"), stderr=subprocess.STDOUT)
print("[Monty-ARC] started in background, pid", _monty_proc.pid)
'''

MERGE_CELL = r'''# ===================== Monty-ARC merge (after the submission cell) =====================
# 1) A confident Monty-ARC answer that NVARC did not already produce replaces NVARC's attempt_2.
# 2) Slots NVARC left empty ([[0]] placeholder: task not reached in time) or duplicated get Monty's best guesses.
import os, json, time
SUB, MON = "submission.json", "/kaggle/working/monty_results.json"
# Monty normally finished hours ago; cap the wait so the notebook stays well inside the 12 h limit
_wait_until = min(time.time() + 300, globals().get("global_end_time", time.time()) + 240)
while not os.path.exists("/kaggle/working/monty_done") and time.time() < _wait_until:
    time.sleep(10)
try:
    print(open("/kaggle/working/monty.log").read()[-2000:])
except Exception:
    pass
sub = json.load(open(SUB))
mon = json.load(open(MON)) if os.path.exists(MON) else {}
EMPTY = [[0]]
replaced = agreed = filled = 0
for tid, rec in mon.items():
    if tid not in sub:
        continue
    for ti, e in enumerate(sub[tid]):
        sure = rec["confident"][ti] if ti < len(rec["confident"]) else []
        guesses = rec["guesses"][ti] if ti < len(rec["guesses"]) else []
        a1, a2 = e.get("attempt_1"), e.get("attempt_2")
        if sure:
            g = sure[0]
            if g in (a1, a2):
                agreed += 1
            elif a1 == EMPTY:
                e["attempt_1"] = g
                replaced += 1
            else:
                e["attempt_2"] = g
                replaced += 1
            continue
        for g in guesses:
            a1, a2 = e.get("attempt_1"), e.get("attempt_2")
            if g in (a1, a2):
                continue
            if a1 == EMPTY:
                e["attempt_1"] = g
                filled += 1
            elif a2 == EMPTY or a2 == a1:
                e["attempt_2"] = g
                filled += 1
json.dump(sub, open(SUB, "w"))
print(f"[Monty-ARC merge] confident: agreed-with-NVARC={agreed} replaced={replaced} | guesses filled empty/duplicate slots={filled}")
if not os.getenv("KAGGLE_IS_COMPETITION_RERUN"):
    try:
        print("*** Score after Monty merge:", data.validate_submission(json.load(open(SUB))))
    except Exception as ex:
        print("local score unavailable:", ex)
'''


def _code_cell(src):
    return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [],
            "source": src.splitlines(keepends=True)}


def main():
    sources = {}
    for m in MODULES:
        with open(os.path.join(ROOT, "arcmonty", m)) as fh:
            sources[m] = fh.read()
    nb = json.load(open(SRC_NB))
    cells = nb["cells"]
    # cell 1 sets global_end_time; insert Monty right after it, and the merge cell at the very end
    idx = next(i for i, c in enumerate(cells) if "global_end_time" in "".join(c["source"]))
    cells.insert(idx + 1, _code_cell(MONTY_CELL.replace("__MONTY_SOURCES__", repr(sources))))
    cells.append(_code_cell(MERGE_CELL))
    md = {"cell_type": "markdown", "metadata": {}, "source": [
        "# Monty-ARC × NVARC hybrid\n",
        "NVARC public fork (mikelou1 perf-patch of the 33.89 baseline, unchanged) plus Monty-ARC: Thousand-Brains-style ",
        "learning modules (object-centric reference frames, evidence over pose hypotheses, voting) whose fully evidenced ",
        "answers replace NVARC's second attempt when they differ.\n"]}
    cells.insert(0, md)
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, "monty-arc-nvarc-hybrid.ipynb"), "w") as fh:
        json.dump(nb, fh)
    meta = json.load(open(SRC_META))
    meta = {k: v for k, v in meta.items() if k not in ("id_no",)}
    meta.update(id="rahim3/monty-arc-nvarc-hybrid", title="Monty-ARC NVARC Hybrid",
                code_file="monty-arc-nvarc-hybrid.ipynb", is_private=True)
    with open(os.path.join(OUT_DIR, "kernel-metadata.json"), "w") as fh:
        json.dump(meta, fh, indent=2)
    print("built", OUT_DIR, json.dumps(meta, indent=1))


if __name__ == "__main__":
    main()
