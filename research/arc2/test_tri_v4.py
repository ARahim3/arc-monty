"""Offline checks of the tri v4 build (no GPU):
  1. v4 with default knobs differs from the submitted v3 notebook only in the intended places;
  2. the patched NVARC queue (starter.py) orders/skips tasks as specified, for both order modes;
  3. the v4 merge cell ranks Qwen-verified > NVARC > Monty-confident > guesses;
  4. qwen_phase_v4 end-to-end against the mock server of test_qwen_phase.py, incl. effort, prompt hook, vround;
  5. the Monty-hint hook as the notebook builds it (monty_hints + arcmonty from the embedded sources).
    python research/arc2/test_tri_v4.py
"""
import importlib
import json
import os
import re
import sys
import tempfile
import time
import types

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, os.path.join(ROOT, "llm", "kaggle"))
CH = json.load(open(os.path.join(ROOT, "data/kaggle_format/agi2_eval_challenges.json")))
SOL = json.load(open(os.path.join(ROOT, "data/kaggle_format/agi2_eval_solutions.json")))


def build(tmp, **kw):
    B = importlib.import_module("build_tri_v4")
    B.OUT_DIR = tmp
    B.main("cheap", **kw)
    return json.load(open(os.path.join(tmp, "monty-arc-qwen-nvarc.ipynb")))


def code_cells(nb):
    return ["".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code"]


def test_diff_vs_v3():
    v3 = json.load(open(os.path.join(ROOT, "kaggle/tri/monty-arc-qwen-nvarc.ipynb")))
    v4 = build(tempfile.mkdtemp())
    a, b = code_cells(v3), code_cells(v4)
    assert len(a) == len(b), (len(a), len(b))
    diff = [i for i, (x, y) in enumerate(zip(a, b)) if x != y]
    kinds = []
    for i in diff:
        y = b[i]
        if y.startswith("%%writefile starter.py"):
            kinds.append("starter")
        elif "run mode" in y[:80]:
            kinds.append("mode")
        elif "phase Q" in y[:80]:
            kinds.append("qwen")
        elif "final merge" in y[:80]:
            kinds.append("merge")
        else:
            kinds.append("UNEXPECTED:" + y[:60])
    assert all(not k.startswith("UNEXPECTED") for k in kinds), kinds
    # the Monty cell, the NVARC solver and everything else are byte-identical to v3
    print("1. v4(default) vs v3: differing code cells", kinds, f"(of {len(b)})")
    return v4


def starter_queue(nb, legq, rerun=True):
    src = next(s for s in code_cells(nb) if s.startswith("%%writefile starter.py"))
    m = re.search(r"    legq = \{\}.*?    for key in keys:\n        queue.put\(key\)", src, re.S)
    assert m, "patched block not found"
    block = "\n".join(l[4:] for l in m.group(0).splitlines())

    class Q(list):
        put = list.append
    tmp = tempfile.mkdtemp()
    p = os.path.join(tmp, "induction_results.json")
    json.dump(legq, open(p, "w"))
    block = block.replace("/kaggle/working/induction_results.json", p)
    g = {"os": os, "json": json, "data": CH, "rerun_mode": rerun,
         "mp": types.SimpleNamespace(Manager=lambda: types.SimpleNamespace(Queue=Q))}
    exec(block, g)
    return list(g["queue"])


def test_queue():
    ids = sorted(CH)
    legq = {}
    for i, t in enumerate(ids[60:]):          # Qwen attempted the last 60
        legq[t] = {"verified": i % 4 == 0, "vround": (1 if i % 8 == 0 else 0) if i % 4 == 0 else None, "outputs": []}
    nb3 = build(tempfile.mkdtemp())
    q3 = starter_queue(nb3, legq)
    assert q3 == [t for t in ids if not legq.get(t, {}).get("verified")], "v3 order changed"
    nb4 = build(tempfile.mkdtemp(), order="density", nv_verified=1)
    q4 = starter_queue(nb4, legq)
    grp = lambda t: 0 if t not in legq else 1 if not legq[t]["verified"] else 2 if legq[t]["vround"] else 3
    def cost(k):                                   # same formula as the patched starter.py
        t, s = CH[k], 0
        s = sum(len(g) * (len(g[0]) + 1) for p in t["train"] for g in (p["input"], p["output"]))
        s = min(s + sum(len(p["input"]) * (len(p["input"][0]) + 1) for p in t["test"]), 8192)
        return 0.0369 * s + 7.64e-6 * s * s + 300 * len(t["test"])
    gain = {0: 0.31, 1: 0.23, 2: 0.08, 3: 0.012}
    dens = [gain[grp(t)] / cost(t) for t in q4]
    assert sorted(q4) == ids and all(a >= b - 1e-12 for a, b in zip(dens, dens[1:])), "not sorted by density"
    assert [grp(t) for t in q4][-1] in (2, 3)
    nb5 = build(tempfile.mkdtemp(), order="density", nv_verified=0)
    q5 = starter_queue(nb5, legq)
    assert set(q5) == set(q3) and len(q5) == len(q3)
    bad = dict(legq, **{ids[-1]: {"verified": True, "vround": "x"}})     # forces a TypeError in the ordering
    qb = starter_queue(nb4, bad)
    assert qb == ids, "fallback should queue every task alphabetically"
    qs = starter_queue(nb4, legq, rerun=False)
    assert sorted(qs) == ["0934a4d8", "36a08778", "981571dc", "aa4ec2a5"], qs
    print(f"2. NVARC queue: v3 {len(q3)} alphabetical; density+verified {len(q4)} by group "
          f"{[sum(grp(t) == g for t in q4) for g in range(4)]}; density {len(q5)}; save-run 4 tasks ok")


def test_merge(nb):
    src = next(s for s in code_cells(nb) if "final merge" in s[:80])
    tmp = tempfile.mkdtemp()
    cwd = os.getcwd()
    os.chdir(tmp)
    t1, t2, t3, t4 = sorted(CH)[:4]
    G = lambda v: [[v]]
    sub = {t: [{"attempt_1": [[0]], "attempt_2": [[0]]} for _ in CH[t]["test"]] for t in (t1, t2, t3, t4)}
    for t, a1, a2 in ((t1, G(1), G(2)), (t2, G(1), G(2)), (t3, [[0]], [[0]])):
        for e in sub[t]:
            e["attempt_1"], e["attempt_2"] = a1, a2
    json.dump(sub, open("submission.json", "w"))
    ntest = lambda t: len(CH[t]["test"])
    mon = {t: {"confident": [[G(7)]] * ntest(t), "guesses": [[G(8), G(9)]] * ntest(t)} for t in (t1, t2, t3, t4)}
    ind = {t1: {"verified": True, "vround": 0, "outputs": [{"attempt": G(5), "alt": None}] * ntest(t1)},
           t3: {"verified": False, "outputs": [{"attempt": G(6), "alt": None}] * ntest(t3)}}
    src = (src.replace("/kaggle/working/monty_results.json", os.path.join(tmp, "mon.json"))
              .replace("/kaggle/working/induction_results.json", os.path.join(tmp, "ind.json"))
              .replace("/kaggle/working/monty_done", os.path.join(tmp, "done")))
    json.dump(mon, open("mon.json", "w"))
    json.dump(ind, open("ind.json", "w"))
    open("done", "w").write("1")
    exec(src, {"RERUN": True, "_ch": CH, "global_end_time": time.time()})
    out = json.load(open("submission.json"))
    os.chdir(cwd)
    pick = lambda t: (out[t][0]["attempt_1"], out[t][0]["attempt_2"])
    assert pick(t1) == (G(5), G(1)), pick(t1)       # Qwen verified, then NVARC top (Monty confident after NVARC)
    assert pick(t2) == (G(1), G(2)), pick(t2)       # NVARC both; Monty does not displace NVARC's 2nd attempt
    assert pick(t3) == (G(7), G(6)), pick(t3)       # no NVARC: Monty confident, then Qwen unverified
    assert pick(t4) == (G(7), G(8)), pick(t4)       # nothing else: Monty confident, Monty guess
    print("3. merge priority ok:", {k: pick(k) for k in (t1, t2, t3, t4)})


def test_qwen_phase_v4():
    import qwen_phase_v4 as qp4
    import test_qwen_phase as T
    T.qp = qp4                                    # the mock recognises prompts via qp.render_qwen38(qp.ps_messages)
    seen = []

    def hook(tid, msgs):
        seen.append(tid)
        return msgs                               # keep the mock's prompt matching working
    srv = T.serve(18124)
    order = sorted(CH)[:12]
    out = os.path.join(tempfile.mkdtemp(), "q.json")
    res = qp4.run_qwen_phase(CH, order, time.time() + 3600, out, budget_per_round=512, max_rounds=2,
                             base_url="http://127.0.0.1:18124/v1", concurrency=6, answer_room=40000, min_round_s=0,
                             reasoning_effort="xhigh", prompt_hook=hook)
    ver = {t for t, r in res.items() if r["verified"]}
    exp = {t for t in order if sorted(CH).index(t) % 3 == 0}
    assert ver == exp, (ver, exp)
    assert all((r["vround"] is not None) == r["verified"] for r in res.values())
    assert sorted(set(seen)) == sorted(order)
    p_med = qp4.render_qwen38(qp4.ps_messages(CH[order[0]]), "medium")
    p_low = qp4.render_qwen38(qp4.ps_messages(CH[order[0]]), "low")
    assert "Reasoning effort" not in p_med and "set to low" in p_low
    srv.shutdown()
    print(f"4. qwen_phase_v4 mock run: 12 tasks, {len(ver)} verified, vround recorded, hook called; effort rendering ok")


def test_hint_hook(nb):
    src = next(s for s in code_cells(nb) if "phase Q" in s[:80])
    m = re.search(r"QWEN_SOURCES = (\{.*\})\n_qdir", src, re.S)
    srcs = eval(m.group(1))
    assert "monty_hints.py" in srcs and "qwen_phase_v4.py" in srcs
    tmp = tempfile.mkdtemp()
    open(os.path.join(tmp, "monty_hints.py"), "w").write(srcs["monty_hints.py"])
    sys.path.insert(0, tmp)
    sys.path.insert(0, ROOT)                      # stands in for /kaggle/working/_monty_pkg
    import monty_hints as mh
    t0 = time.time()
    n = sum(bool(mh.notes(CH[t])) for t in CH)
    print(f"5. hint hook: notes for {n}/120 tasks in {time.time() - t0:.1f}s")


if __name__ == "__main__":
    v4 = test_diff_vs_v3()
    test_queue()
    test_merge(v4)
    test_qwen_phase_v4()
    test_hint_hook(build(tempfile.mkdtemp(), hints=1))
    print("ALL OK")
