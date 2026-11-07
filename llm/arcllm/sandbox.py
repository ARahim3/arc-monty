"""Run model-written transform() programs in isolated subprocesses (timeout + memory cap)."""
import json
import os
import subprocess
import sys

MARK = "@@ARC_RESULT@@"
RUNNER = r'''
import sys, json, io, contextlib, copy, traceback
MARK = "@@ARC_RESULT@@"
job = json.loads(sys.stdin.read())
def clean(res):
    try:
        import numpy as np
        if isinstance(res, np.ndarray): res = res.tolist()
    except Exception: pass
    if isinstance(res, tuple): res = list(res)
    if not isinstance(res, list) or not res: return None, "output is not a non-empty list of rows"
    rows = []
    for row in res:
        if hasattr(row, "tolist"): row = row.tolist()
        if not isinstance(row, (list, tuple)) or not row: return None, "rows must be non-empty lists"
        out = []
        for v in row:
            try: iv = int(v)
            except Exception: return None, f"non-integer cell {v!r}"
            if iv != v or not 0 <= iv <= 9: return None, f"cell value {v!r} outside 0-9"
            out.append(iv)
        rows.append(out)
    if any(len(r) != len(rows[0]) for r in rows): return None, "output is not rectangular"
    if not (1 <= len(rows) <= 30 and 1 <= len(rows[0]) <= 30): return None, "size outside 1..30"
    return rows, None
results, sink, ns = [], io.StringIO(), {"__name__": "__arc_program__"}
try:
    with contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink):
        exec(compile(job["code"], "<program>", "exec"), ns)
    fn = ns.get("transform")
    if not callable(fn): raise NameError("no function named transform")
except Exception as e:
    msg = "".join(traceback.format_exception_only(type(e), e)).strip()
    results = [{"error": "program failed to load: " + msg[-400:]} for _ in job["inputs"]]
else:
    for grid in job["inputs"]:
        try:
            with contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink):
                res = fn(copy.deepcopy(grid))
            rows, err = clean(res)
            results.append({"output": rows} if err is None else {"error": err})
        except Exception:
            tb = traceback.format_exc().strip().splitlines()
            results.append({"error": " | ".join(tb[-3:])[-400:]})
sys.stdout.write(MARK + json.dumps(results) + "\n")
'''


def _limits(mem_bytes):
    def apply():
        try:
            import resource
            resource.setrlimit(resource.RLIMIT_AS, (mem_bytes, mem_bytes))
        except Exception:
            pass
    return apply


def run_program(code, inputs, timeout=10.0, mem_bytes=2 << 30):
    """[{output: grid} | {error: str}] per input; never raises."""
    try:
        p = subprocess.run([sys.executable, "-I", "-c", RUNNER],
                           input=json.dumps({"code": code, "inputs": inputs}),
                           capture_output=True, text=True, timeout=timeout,
                           preexec_fn=_limits(mem_bytes) if os.name == "posix" else None,
                           env=dict(os.environ, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1",
                                    MKL_NUM_THREADS="1", PYTHONHASHSEED="0"))
    except subprocess.TimeoutExpired:
        return [{"error": f"timed out after {timeout:.0f}s"} for _ in inputs]
    for line in reversed(p.stdout.splitlines()):
        if line.startswith(MARK):
            try:
                res = json.loads(line[len(MARK):])
                if len(res) == len(inputs):
                    return res
            except Exception:
                break
    tail = " | ".join((p.stderr or "").strip().splitlines()[-2:])[-300:]
    return [{"error": "program crashed: " + (tail or f"exit {p.returncode}")} for _ in inputs]
