"""Build the three-way notebook: Qwen3.8-27B program synthesis + NVARC public fork + Monty-ARC.

Timeline inside the 12 h Kaggle run (4x L4):
  CPU  : Monty-ARC runs in the background for the whole run (nice 19), writing results incrementally.
  GPUs : phase Q - Qwen3.8 program synthesis (vLLM, Python 3.12 side-environment) until QWEN_END; verified programs
         are written to /kaggle/working/induction_results.json; the server is then killed and the GPUs freed.
         phase N - NVARC (unchanged pipeline) on every task WITHOUT a verified Qwen program, until NVARC's deadline.
Merge per test output (pass@2 is order-free, so this only decides which two candidates survive):
  1. verified Qwen program output   2. confident Monty-ARC answer   3. NVARC's candidates
  4. remaining empty/duplicate slots: Qwen unverified output, then Monty-ARC guesses.
Save-run modes (env-free switch in the first code cell): "smoke" exercises every phase on a few tasks (validation),
"cheap" writes the fallback and stops (final versions; the competition rerun always runs everything).
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import build_hybrid as H  # noqa: E402  (reuses the Monty cell, sources list and NVARC base notebook)

OUT_DIR = os.path.join(ROOT, "kaggle/tri")
QWEN_FILES = ["llm/kaggle/qwen_phase.py"]  # plus its arcllm helpers, embedded verbatim
QWEN_PKG = "llm/arcllm"

# Patch point in NVARC's starter.py. It is not reproduced here, so this file distributes no NVARC text:
#   Kaggle notebook mikelou1/arc-agi2-lb33-89-minimal-perfpatch (the version pulled on 2026-10-26; see README),
#   cell 6 (0-based), the cell that starts "%%writefile starter.py": cell lines 49-55, which are lines 48-54 of the
#   written starter.py, the task-queue loop in its __main__ block. NVARC upstream: github.com/1ytic/NVARC.
# The loop runs from the line that creates the multiprocessing queue to the first put after it (7 lines).
# _queue_loop() finds those two lines in the fetched notebook at build time.
# v3 patch: LEGQ_HEAD goes before the loop and LEGQ_SKIP before the put, so NVARC skips tasks Qwen verified.
LEGQ_HEAD = '''    legq_skip = set()
    legq_path = "/kaggle/working/induction_results.json"
    if os.path.exists(legq_path):
        with open(legq_path) as f:
            legq_skip = {k for k, r in json.load(f).items() if isinstance(r, dict) and r.get("verified")}
        print(f"[LegQ] NVARC skips {len(legq_skip)} task(s) already solved by a verified Qwen program")

'''
LEGQ_SKIP = '''        if key in legq_skip:
            continue
'''


def _queue_loop(lines):
    """(first, last): indexes of the queue-creation line of the starter.py task loop and of the first put after it."""
    first = next(i for i, l in enumerate(lines) if l.lstrip().startswith("queue = ") and l.rstrip().endswith(".Queue()"))
    last = next(i for i in range(first + 1, len(lines)) if lines[i].lstrip().startswith("queue.put("))
    assert last - first == 6 and not lines[first + 1].strip(), "starter.py layout changed"
    return first, last


def _skip_patch(src):
    lines = src.splitlines(keepends=True)
    first, last = _queue_loop(lines)
    return "".join(lines[:first] + [LEGQ_HEAD] + lines[first:last] + [LEGQ_SKIP] + lines[last:])


MODE_CELL = r'''# ===================== run mode =====================
# The competition rerun always runs every phase. For the interactive save run:
#   "smoke": every phase on a few tasks with a small Qwen budget (validation; costs GPU quota)
#   "cheap": fallback submission only (final versions: the save run costs ~nothing)
SAVE_RUN_MODE = "__SAVE_RUN_MODE__"
QWEN_HOURS = __QWEN_HOURS__        # GPU time given to Qwen program synthesis before NVARC starts
QWEN_BUDGET_PER_ROUND = __QWEN_BUDGET__
QWEN_MAX_ROUNDS = __QWEN_ROUNDS__
import os, json, glob, time
RERUN = bool(os.getenv("KAGGLE_IS_COMPETITION_RERUN"))
_ch_path = ("/kaggle/input/competitions/arc-prize-2026-arc-agi-2/arc-agi_test_challenges.json" if RERUN else
            "/kaggle/input/competitions/arc-prize-2026-arc-agi-2/arc-agi_evaluation_challenges.json")
_ch = json.load(open(_ch_path))
with open("/kaggle/working/submission.json", "w") as _f:  # valid fallback before anything heavy
    json.dump({t: [{"attempt_1": x["input"], "attempt_2": x["input"]} for x in task["test"]] for t, task in _ch.items()}, _f)
SKIP_ALL = (not RERUN) and SAVE_RUN_MODE == "cheap"
print("rerun:", RERUN, "| save-run mode:", SAVE_RUN_MODE, "| skip heavy phases:", SKIP_ALL)
'''

QWEN_CELL = r'''# ===================== phase Q: Qwen3.8-27B program synthesis (before NVARC) =====================
# Python 3.12 side-environment (vLLM wheelhouse) runs the server; the client and sandbox run here (3.11, stdlib).
import os, sys, json, time, traceback
QWEN_SOURCES = __QWEN_SOURCES__
_qdir = "/kaggle/working/_qwen_pkg"
for _rel, _src in QWEN_SOURCES.items():
    _p = os.path.join(_qdir, _rel)
    os.makedirs(os.path.dirname(_p), exist_ok=True)
    open(_p, "w").write(_src)
sys.path.insert(0, _qdir)
if SKIP_ALL:
    print("[LegQ] skipped (cheap save run)")
else:
    try:
        from qwen_phase import run_qwen_phase
        _smoke = (not RERUN) and SAVE_RUN_MODE == "smoke"
        # reverse order: NVARC walks the tasks alphabetically and may not reach the last ones in 12 h,
        # so Qwen covers those first; NVARC later skips every task Qwen verified
        _order = sorted(_ch, reverse=True)
        if _smoke:
            _order = _order[:3]
        _deadline = min(global_end_time - 4 * 3600, time.time() + (0.6 if _smoke else QWEN_HOURS) * 3600)
        run_qwen_phase(_ch, _order, _deadline, "/kaggle/working/induction_results.json",
                       budget_per_round=(4096 if _smoke else QWEN_BUDGET_PER_ROUND),
                       max_rounds=(1 if _smoke else QWEN_MAX_ROUNDS))
    except Exception:
        traceback.print_exc()
        print("[LegQ] failed - NVARC and Monty-ARC continue unaffected")
try:
    _r = json.load(open("/kaggle/working/induction_results.json"))
    print(f"[LegQ] verified {sum(1 for v in _r.values() if v.get('verified'))}/{len(_r)} attempted tasks")
except Exception:
    print("[LegQ] no results file")
'''

MERGE_CELL = r'''# ===================== final merge: Qwen verified > Monty confident > NVARC > guesses =====================
import os, json, time
SUB, MON, IND = "submission.json", "/kaggle/working/monty_results.json", "/kaggle/working/induction_results.json"
_wait_until = min(time.time() + 300, globals().get("global_end_time", time.time()) + 240)
while not os.path.exists("/kaggle/working/monty_done") and time.time() < _wait_until:
    time.sleep(10)
sub = json.load(open(SUB))
mon = json.load(open(MON)) if os.path.exists(MON) else {}
ind = json.load(open(IND)) if os.path.exists(IND) else {}
EMPTY = [[0]]
stats = dict(qwen_verified=0, monty_confident=0, filled=0)
for tid, outs in sub.items():
    q = ind.get(tid) or {}
    m = mon.get(tid) or {}
    for ti, e in enumerate(outs):
        nv = [g for g in (e.get("attempt_1"), e.get("attempt_2")) if g and g != EMPTY]
        cands = []                                   # ordered by trust; duplicates dropped below
        qo = (q.get("outputs") or [])[ti] if ti < len(q.get("outputs") or []) else {}
        if q.get("verified") and qo.get("attempt"):
            cands.append(qo["attempt"]); stats["qwen_verified"] += 1
        ms = (m.get("confident") or [])[ti] if ti < len(m.get("confident") or []) else []
        if ms:
            cands.append(ms[0]); stats["monty_confident"] += 1
        cands += nv
        extra = []
        if qo.get("attempt") and not q.get("verified"):
            extra.append(qo["attempt"])
        if q.get("verified") and qo.get("alt"):
            extra.append(qo["alt"])
        extra += (m.get("guesses") or [])[ti] if ti < len(m.get("guesses") or []) else []
        final = []
        for g in cands + extra:
            if g and g != EMPTY and g not in final:
                final.append(g)
            if len(final) == 2:
                break
        stats["filled"] += sum(1 for g in final if g not in nv)
        while len(final) < 2:
            final.append(final[0] if final else _ch[tid]["test"][ti]["input"])
        e["attempt_1"], e["attempt_2"] = final[0], final[1]
json.dump(sub, open(SUB, "w"))
print("[merge]", stats)
if not RERUN:
    try:
        print("*** Score after merge:", data.validate_submission(json.load(open(SUB))))
    except Exception as ex:
        print("local score unavailable:", ex)
'''


def _code_cell(src):
    return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [],
            "source": src.splitlines(keepends=True)}


def main(save_run_mode="smoke", qwen_hours=4.5, budget=16384, rounds=2):
    monty_sources = {m: open(os.path.join(ROOT, "arcmonty", m)).read() for m in H.MODULES}
    qwen_sources = {}
    for f in QWEN_FILES:
        qwen_sources[os.path.basename(f)] = open(os.path.join(ROOT, f)).read()
    for f in sorted(os.listdir(os.path.join(ROOT, QWEN_PKG))):
        if f.endswith(".py"):
            qwen_sources["arcllm/" + f] = open(os.path.join(ROOT, QWEN_PKG, f)).read()

    nb = json.load(open(H.SRC_NB))
    cells = nb["cells"]
    # starter.py: NVARC skips tasks with a verified Qwen program
    for c in cells:
        src = "".join(c["source"])
        if src.startswith("%%writefile starter.py"):
            c["source"] = _skip_patch(src).splitlines(keepends=True)
    # NVARC must not run its pipeline in a cheap save run: guard the launch cell
    for c in cells:
        src = "".join(c["source"])
        if src.startswith("!UNSLOTH_DISABLE_STATISTICS"):
            cmd = src.lstrip("!").strip()
            assert "{global_end_time}" in cmd
            c["source"] = ("if not SKIP_ALL:\n    get_ipython().system(f" + json.dumps(cmd) + ")\n").splitlines(keepends=True)
        if "decoder = ArcDecoder" in src:
            c["source"] = ("if not SKIP_ALL:\n" + "".join("    " + l for l in src.splitlines(keepends=True))
                           ).splitlines(keepends=True)
    idx = next(i for i, c in enumerate(cells)
               if c["cell_type"] == "code" and "global_end_time = " in "".join(c["source"]))
    mode = (MODE_CELL.replace("__SAVE_RUN_MODE__", save_run_mode).replace("__QWEN_HOURS__", str(qwen_hours))
            .replace("__QWEN_BUDGET__", str(budget)).replace("__QWEN_ROUNDS__", str(rounds)))
    monty = H.MONTY_CELL.replace("__MONTY_SOURCES__", repr(monty_sources))
    monty = monty.replace("_monty_proc = subprocess.Popen(", "_monty_proc = None if SKIP_ALL else subprocess.Popen(")
    monty = monty.replace('print("[Monty-ARC] started in background, pid", _monty_proc.pid)',
                          'print("[Monty-ARC] started in background, pid", getattr(_monty_proc, "pid", None))')
    assert "getattr(_monty_proc" in monty
    qwen = QWEN_CELL.replace("__QWEN_SOURCES__", repr(qwen_sources))
    cells[idx + 1:idx + 1] = [_code_cell(mode), _code_cell(monty), _code_cell(qwen)]
    cells.append(_code_cell(MERGE_CELL))
    cells.insert(0, {"cell_type": "markdown", "metadata": {}, "source": [
        "# Monty-ARC x Qwen3.8 x NVARC\n",
        "Qwen3.8-27B program synthesis (verified on the demos) first, then the NVARC public fork on every task without a ",
        "verified program, with Monty-ARC (Thousand-Brains-style learning modules) on CPU throughout. Merge priority: ",
        "verified program > confident Monty-ARC > NVARC > guesses.\n"]})
    os.makedirs(OUT_DIR, exist_ok=True)
    json.dump(nb, open(os.path.join(OUT_DIR, "monty-arc-qwen-nvarc.ipynb"), "w"))
    meta = json.load(open(H.SRC_META))
    meta = {k: v for k, v in meta.items() if k != "id_no"}
    meta.update(id="rahim3/monty-arc-qwen-nvarc", title="Monty-ARC Qwen NVARC", code_file="monty-arc-qwen-nvarc.ipynb",
                is_private=True)
    meta["dataset_sources"] = sorted(set(meta.get("dataset_sources", [])) | {
        "mirzamilanfarabi/arc3-vllm-h100-wheelhouse-v3", "keithtyser/taaf-duck-qwen38-serving-v1",
        "zbigniewkirchner/gemma-4-agent-local-eval-pythons"})
    meta["model_sources"] = sorted(set(meta.get("model_sources", [])) | {
        "foysalemonshanto/qwen3-8-27b-fp8-repacked-v1/PyTorch/hf-fp8/1"})
    json.dump(meta, open(os.path.join(OUT_DIR, "kernel-metadata.json"), "w"), indent=2)
    print("built", OUT_DIR, "mode", save_run_mode, json.dumps(meta, indent=1))


if __name__ == "__main__":
    main(*(sys.argv[1:2] or ["smoke"]))
