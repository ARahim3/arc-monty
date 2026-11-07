"""Qwen3.8-27B program-synthesis phase for the Kaggle 4xL4 notebook, v4 (copy of qwen_phase.py used by tri v3).

v4 changes (all default to v3 behaviour): reasoning_effort (xhigh|medium|low) for the chat template;
prompt_hook(task_id, messages) -> messages (e.g. Monty perception notes); summarize() records "vround",
the 0-based round of the first verified program (round-1 programs are 18/19 right on test, round-2 11.5/18).

Original docstring follows.
Qwen3.8-27B program-synthesis phase for the Kaggle 4xL4 notebook (NVARC + Qwen3.8 PS + Monty).

Status: CPU-tested against a mock server (llm/kaggle/test_qwen_phase.py). The vLLM/GPU parts are
NOT yet run on Kaggle; the server command and ladder follow madarshbb/arc-qwen-3-8-27b-agent.

Split of interpreters (NVARC's pinned image: Python 3.11, torch 2.6.0+cu124, untouched):
  * this module (client, prompts, sandbox) is stdlib-only and runs under the notebook's 3.11;
  * vLLM runs under a separate Python 3.12 (`/tmp/py312`) with packages in a --target dir, as a
    subprocess server on 127.0.0.1:1234; the client talks HTTP to it.

Kaggle inputs to attach
-----------------------
  * Model: `foysalemonshanto/qwen3-8-27b-fp8-repacked-v1/PyTorch/hf-fp8/1` (Qwen3.8-27B FP8; the
    one the 21.5-LB public notebook serves with MTP). Alternative: `mikedan7/qwen3-8-27b-fp8-official`.
  * Dataset `mirzamilanfarabi/arc3-vllm-h100-wheelhouse-v3` (cp312 wheelhouse + requirements.lock).
  * Dataset `keithtyser/taaf-duck-qwen38-serving-v1` (serving_wheels/*.whl: transformers/hub overlay
    with Qwen3.8 support).
  * Dataset `zbigniewkirchner/gemma-4-agent-local-eval-pythons` (cpython-3.12-linux.tgz.bin).
  * Our code: a private dataset holding `llm/arcllm/` and `llm/kaggle/` (main session uploads).

Notebook usage
--------------
    import sys; sys.path.insert(0, "/kaggle/input/<our-code>/llm/kaggle")
    import qwen_phase as qp
    py = qp.setup_python312()                      # extract + ensurepip (≈1 min)
    site = qp.install_vllm(py)                     # offline pip --target (≈3-5 min)
    res = qp.run_qwen_phase(challenges, task_order, deadline_ts, "/kaggle/working/qwen.json",
                            budget_per_round=16384, max_rounds=2, py=py, site=site)
    # smoke run for the save/commit version:
    res = qp.run_qwen_phase(challenges, order, deadline_ts, out, 2048, 1, py=py, site=site, smoke=3)

Offline install performed by setup_python312()/install_vllm() (shell equivalent):
    mkdir -p /tmp/py312 && tar -xzf <...>/cpython-3.12-linux.tgz.bin -C /tmp/py312
    PY=$(find /tmp/py312 -name python3.12 -type f | head -1); $PY -m ensurepip || true
    $PY -m pip install --no-index --find-links <wheelhouse> -r <wheelhouse>/requirements.lock \
        --target /tmp/vllm-site --only-binary :all: --no-compile --ignore-installed -q
    rm -rf /tmp/vllm-site/{transformers,huggingface_hub}*   # then the overlay:
    $PY -m pip install --no-index --no-deps --target /tmp/vllm-site --upgrade --force-reinstall \
        <taaf-duck-qwen38-serving-v1>/serving_wheels/*.whl
(/tmp, not /kaggle/working: 7 GB of site-packages under working breaks teardown per the forum.)

Output file (atomic JSON, rewritten as tasks finish):
    {task_id: {"verified": bool, "outputs": [{"attempt": grid, "alt": grid|None}, ...per test],
               "n_tokens": int, "n_train_ok": int, "n_train": int}}
Only attempted tasks appear. "verified" = a program reproduced every train pair (78% test precision
measured on ARC-AGI-2 eval at 16k/round); attempt = verified output by vote, else the program
that reproduced the most train pairs; alt = the next distinct grid.
"""
import glob
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))           # .../llm, for arcllm
from arcllm.sandbox import run_program               # noqa: E402  (stdlib only)
from arcllm.tasks import ps_messages, extract_code, feedback_text   # noqa: E402  (stdlib only)

PORT = 1234
SERVED = "qwen"
XHIGH = ("Reasoning effort is set to xhigh. Please think carefully through the task, validate key "
         "assumptions, consider plausible alternatives, and prioritize correctness, consistency, "
         "and clarity in the final answer.")
CLOSE_THINK = "\n</think>\n\n"


def log(*a):
    print(time.strftime("%H:%M:%S"), "[qwen]", *a, flush=True)


# ---------------------------------------------------------------- prompt rendering (no tokenizer)
def render_qwen38(messages, reasoning_effort="xhigh"):
    """Qwen3.8 chat template, text form, for system/user/assistant messages without tools.
    Matches tokenizer.apply_chat_template(..., add_generation_prompt=True) for these inputs
    (checked in test_qwen_phase.py against the HF template). Assistant turns carry no reasoning."""
    instr = XHIGH if reasoning_effort == "xhigh" else (
        "Reasoning effort is set to low. Keep your thinking brief and focused, moving directly to the "
        "conclusion without unnecessary elaboration." if reasoning_effort == "low" else "")
    out = []
    msgs = list(messages)
    if msgs and msgs[0]["role"] == "system":
        out.append("<|im_start|>system\n" + (instr + "\n\n" if instr else "") + msgs[0]["content"] + "<|im_end|>\n")
        msgs = msgs[1:]
    elif instr:
        out.append("<|im_start|>system\n" + instr + "<|im_end|>\n")
    for m in msgs:
        if m["role"] == "assistant":
            out.append("<|im_start|>assistant\n<think>\n\n</think>\n\n" + m["content"].strip() + "<|im_end|>\n")
        else:
            out.append("<|im_start|>" + m["role"] + "\n" + m["content"] + "<|im_end|>\n")
    out.append("<|im_start|>assistant\n<think>\n")
    return "".join(out)


# ---------------------------------------------------------------- HTTP client (stdlib)
class Client:
    def __init__(self, base_url, sampling=None, model=SERVED, use_seed=True):
        self.url = base_url.rstrip("/") + "/completions"
        self.model = model
        self.sampling = sampling or {"temperature": 1.0, "top_p": 0.95, "top_k": 20}
        self.use_seed = use_seed
        self.stop = threading.Event()

    def complete(self, prompt, max_tokens, seed, timeout):
        if self.stop.is_set():
            return {"error": "stopped"}
        payload = {"model": self.model, "prompt": prompt, "max_tokens": int(max_tokens),
                   "skip_special_tokens": False, **self.sampling}
        if self.use_seed:
            payload["seed"] = int(seed)
        req = urllib.request.Request(self.url, data=json.dumps(payload).encode(),
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=max(5.0, timeout)) as r:
                body = json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            detail = e.read().decode(errors="replace")[:300]
            if e.code in (400, 500) and self.use_seed and "seed" in detail.lower():
                self.use_seed = False
                return self.complete(prompt, max_tokens, seed, timeout)
            return {"error": f"HTTP {e.code}: {detail}"}
        except Exception as e:
            return {"error": f"{type(e).__name__}: {e}"[:300]}
        ch = body["choices"][0]
        return {"text": ch.get("text") or "", "finish": ch.get("finish_reason"),
                "n": (body.get("usage") or {}).get("completion_tokens", 0)}

    def generate(self, prompt, budget, answer_room, seed, timeout):
        """Think at most `budget` tokens, then answer within `answer_room` (client-side forcing)."""
        r = self.complete(prompt, budget, seed, timeout())
        if "error" in r:
            return r
        text, n = r["text"], r["n"]
        if "</think>" in text:
            reasoning, answer = text.split("</think>", 1)
            if r["finish"] == "length":          # answer started but was cut: continue it once
                c = self.complete(prompt + text, answer_room, seed + 1, timeout())
                if "error" not in c:
                    answer, n = answer + c["text"], n + c["n"]
            return {"answer": answer, "n": n, "forced": False}
        # still thinking at the cap (or stopped early inside <think>): close it, ask for the answer
        c = self.complete(prompt + text + CLOSE_THINK, answer_room, seed + 2, timeout())
        if "error" in c:
            return {"answer": "", "n": n, "forced": True, "error": c["error"]}
        ans = c["text"].split("</think>")[-1]
        return {"answer": ans, "n": n + c["n"], "forced": True}


# ---------------------------------------------------------------- one task, program synthesis
def solve_task(client, task, budget, rounds, answer_room, seed, timeout, sandbox_timeout,
               may_start_round, reasoning_effort="xhigh", prompt_hook=None, task_id=None):
    msgs = ps_messages(task)
    if prompt_hook is not None:
        try:
            msgs = prompt_hook(task_id, msgs)
        except Exception as e:  # a hook must never cost a task
            log(f"{task_id} prompt_hook failed: {type(e).__name__}: {e}")
    train = task["train"]
    inputs = [p["input"] for p in train] + [t["input"] for t in task["test"]]
    progs, n_tok = [], 0
    for rnd in range(rounds):
        if not may_start_round():
            break
        g = client.generate(render_qwen38(msgs, reasoning_effort), budget, answer_room, seed + 10 * rnd, timeout)
        n_tok += g.get("n", 0)
        if "error" in g and not g.get("answer"):
            break
        code = extract_code(g["answer"])
        msgs = msgs + [{"role": "assistant", "content": g["answer"][-6000:]}]
        if code is None:
            msgs.append({"role": "user", "content": "No ```python block defining transform() was "
                         "found. Give the complete program in ONE ```python code block."})
            continue
        res = run_program(code, inputs, timeout=sandbox_timeout)
        tr = [{"ok": "output" in x and x["output"] == p["output"], "output": x.get("output"),
               "error": x.get("error")} for x, p in zip(res[:len(train)], train)]
        test_out = [x.get("output") for x in res[len(train):]]
        n_ok = sum(t["ok"] for t in tr)
        verified = n_ok == len(train) and all(o is not None for o in test_out)
        progs.append({"n_ok": n_ok, "verified": verified, "test": test_out, "round": rnd})
        if verified:
            break
        msgs.append({"role": "user", "content": feedback_text(tr, train)})
    return progs, n_tok


def summarize(task, progs, n_tok):
    outs = []
    for j in range(len(task["test"])):
        score, grids = {}, {}
        for p in progs:
            g = p["test"][j] if j < len(p["test"]) else None
            if g is None:
                continue
            k = json.dumps(g)
            grids[k] = g
            s = score.get(k, (0, -1))
            score[k] = (s[0] + p["verified"], max(s[1], p["n_ok"]))
        ranked = [grids[k] for k in sorted(score, key=lambda k: score[k], reverse=True)]
        outs.append({"attempt": ranked[0] if ranked else None, "alt": ranked[1] if len(ranked) > 1 else None})
    vround = next((p.get("round", i) for i, p in enumerate(progs) if p["verified"]), None)
    return {"verified": any(p["verified"] for p in progs), "vround": vround, "outputs": outs, "n_tokens": n_tok,
            "n_train_ok": max((p["n_ok"] for p in progs), default=-1), "n_train": len(task["train"])}


def write_atomic(obj, path):
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(obj, f)
    os.replace(tmp, path)


# ---------------------------------------------------------------- Python 3.12 + vLLM (offline)
def setup_python312(tgz_glob="/kaggle/input/**/cpython-3.12-linux.tgz.bin", dest="/tmp/py312"):
    found = glob.glob(os.path.join(dest, "**", "python3.12"), recursive=True)
    if not found:
        tgz = sorted(glob.glob(tgz_glob, recursive=True))[0]
        os.makedirs(dest, exist_ok=True)
        subprocess.run(["tar", "-xzf", tgz, "-C", dest], check=True)
        found = glob.glob(os.path.join(dest, "**", "python3.12"), recursive=True)
    py = sorted((p for p in found if os.path.isfile(p) and os.access(p, os.X_OK)), key=len)[0]
    if subprocess.run([py, "-m", "pip", "--version"], capture_output=True).returncode != 0:
        subprocess.run([py, "-m", "ensurepip"], check=True, capture_output=True)
    log("python3.12 at", py)
    return py


def install_vllm(py, lock_glob="/kaggle/input/**/arc3-vllm-h100-wheelhouse-v3/**/requirements.lock",
                 overlay_glob="/kaggle/input/**/taaf-duck-qwen38-serving-v1/serving_wheels/*.whl",
                 site="/tmp/vllm-site"):
    stamp = os.path.join(site, ".installed")
    if os.path.exists(stamp):
        return site
    t = time.time()
    wh = os.path.dirname(sorted(glob.glob(lock_glob, recursive=True))[0])
    subprocess.run([py, "-m", "pip", "install", "--no-index", "--find-links", wh, "--requirement",
                    os.path.join(wh, "requirements.lock"), "--target", site, "--upgrade",
                    "--ignore-installed", "--only-binary", ":all:", "--no-compile",
                    "--disable-pip-version-check", "--no-warn-conflicts", "-q"], check=True)
    wheels = sorted(glob.glob(overlay_glob, recursive=True))
    if wheels:
        for pat in ("transformers", "transformers-*.dist-info", "huggingface_hub", "huggingface_hub-*.dist-info"):
            for p in glob.glob(os.path.join(site, pat)):
                shutil.rmtree(p, ignore_errors=True) if os.path.isdir(p) else os.remove(p)
        subprocess.run([py, "-m", "pip", "install", "--no-index", "--no-deps", "--target", site,
                        "--upgrade", "--force-reinstall", "--no-compile", "--disable-pip-version-check",
                        "-q", *wheels], check=True)
    open(stamp, "w").write(str(time.time()))
    log(f"vllm site installed in {time.time() - t:.0f}s ({len(wheels)} overlay wheels)")
    return site


def cuda_link_dir(d="/tmp/cuda-link"):
    """FlashInfer JIT links with -lcuda; expose the driver's libcuda.so (madarshbb's fix)."""
    os.makedirs(d, exist_ok=True)
    hits = []
    for pat in ("/usr/local/nvidia/lib64/libcuda.so*", "/usr/lib/x86_64-linux-gnu/libcuda.so*",
                "/usr/lib64/libcuda.so*", "/usr/local/cuda/compat/libcuda.so*"):
        hits += sorted(glob.glob(pat))
    link = os.path.join(d, "libcuda.so")
    if hits and not os.path.lexists(link):
        os.symlink(next((h for h in hits if h.endswith(".so.1")), hits[0]), link)
    return d


MTP = '{"method": "qwen3_5_mtp", "num_speculative_tokens": 2}'
LADDER = [  # most ambitious first; plain serving last (madarshbb's ladder minus tool parsers)
    ["--kv-cache-dtype", "fp8", "--language-model-only", "--speculative-config", MTP],
    ["--kv-cache-dtype", "fp8", "--speculative-config", MTP],
    ["--kv-cache-dtype", "fp8", "--speculative-config", '{"method": "mtp", "num_speculative_tokens": 2}'],
    ["--kv-cache-dtype", "fp8"],
    [],
]


def start_server(py, site, model_glob, max_model_len, max_num_seqs, ladder=None, ready_timeout=1500,
                 log_path="/kaggle/working/vllm-server.log"):
    model = os.path.dirname(sorted(glob.glob(model_glob, recursive=True))[0])
    env = dict(os.environ, PYTHONPATH=site, USE_TF="0", TRANSFORMERS_NO_TF="1",
               TRANSFORMERS_NO_TORCHVISION="1", VLLM_NO_USAGE_STATS="1", VLLM_USE_FLASHINFER_SAMPLER="0",
               HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
               LIBRARY_PATH=":".join([cuda_link_dir(), "/usr/local/nvidia/lib64", os.environ.get("LIBRARY_PATH", "")]))
    base = [py, "-m", "vllm.entrypoints.openai.api_server", "--model", model, "--served-model-name", SERVED,
            "--host", "127.0.0.1", "--port", str(PORT), "--tensor-parallel-size", "4",
            "--generation-config", "vllm", "--enable-prefix-caching", "--max-model-len", str(max_model_len),
            "--gpu-memory-utilization", "0.90", "--max-num-seqs", str(max_num_seqs)]
    for i, extra in enumerate(ladder or LADDER):
        t = time.time()
        proc = subprocess.Popen(base + extra, env=env, stdout=open(log_path, "w"), stderr=subprocess.STDOUT,
                                start_new_session=True)
        while time.time() - t < ready_timeout and proc.poll() is None:
            text = open(log_path, errors="replace").read()[-20000:]
            if "EngineCore failed" in text:
                break
            try:
                urllib.request.urlopen(f"http://127.0.0.1:{PORT}/v1/models", timeout=5)
                log(f"server up with option set {i} {extra} after {time.time() - t:.0f}s")
                return proc
            except Exception:
                time.sleep(10)
        log(f"option set {i} failed; tail:\n" + "\n".join(open(log_path, errors="replace").read().splitlines()[-15:]))
        stop_server(proc)
    return None


def stop_server(proc, wait_s=180):
    """Kill the server's whole process group and wait until the GPUs are free (NVARC needs them)."""
    if proc is not None:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass
        try:
            proc.wait(timeout=60)
        except Exception:
            pass
    t = time.time()
    while time.time() - t < wait_s:
        try:
            used = subprocess.run(["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
                                  capture_output=True, text=True, timeout=30).stdout.split()
        except Exception:
            return
        if not used or all(int(u) < 1500 for u in used if u.strip().isdigit()):
            return
        time.sleep(5)
    log("WARNING: GPUs still hold memory after server shutdown")


# ---------------------------------------------------------------- the phase
def run_qwen_phase(challenges, task_order, deadline_ts, out_path, budget_per_round=16384, max_rounds=2,
                   py=None, site="/tmp/vllm-site",
                   model_glob="/kaggle/input/**/qwen3-8-27b-fp8-repacked-v1/**/config.json",
                   concurrency=20, answer_room=6144, sandbox_timeout=10.0, min_round_s=None,
                   shutdown_margin_s=120, smoke=0, base_url=None, sampling=None, reasoning_effort="xhigh",
                   prompt_hook=None):
    """Run Qwen3.8 program synthesis over `task_order` until done or `deadline_ts` (epoch seconds).

    Starts and ALWAYS stops the vLLM server (unless `base_url` is given: then an existing server or a
    mock is used and nothing is started). smoke=N: only the first N tasks, budget 2048, 1 round.
    Returns the result dict that is also written to `out_path`."""
    if smoke:
        task_order, budget_per_round, max_rounds = list(task_order)[:smoke], min(budget_per_round, 2048), 1
    results, lock = {}, threading.Lock()
    if os.path.exists(out_path):
        try:
            results = json.load(open(out_path))
        except Exception:
            results = {}
    todo = [t for t in task_order if t in challenges and t not in results]
    # a round costs ~budget/(per-sequence decode rate); assume >= 20 tok/s per sequence on 4xL4
    min_round_s = min_round_s if min_round_s is not None else (budget_per_round + answer_room) / 20.0
    proc = None
    t0 = time.time()
    try:
        if base_url is None:
            if time.time() + 1800 > deadline_ts:
                log("not enough time to start the server; skipping phase")
                return results
            max_len = budget_per_round + answer_room + 16384
            py = py or setup_python312()
            install_vllm(py, site=site)  # idempotent (stamp file); a failed install raises -> caller logs it
            proc = start_server(py, site, model_glob, max_len, concurrency)
            if proc is None:
                log("server failed on every option set; skipping phase")
                return results
            base_url = f"http://127.0.0.1:{PORT}/v1"
        client = Client(base_url, sampling)
        hard_stop = deadline_ts - shutdown_margin_s

        def watchdog():
            while not client.stop.is_set():
                if time.time() >= hard_stop:
                    log("deadline: stopping new requests")
                    client.stop.set()
                    return
                time.sleep(5)
        threading.Thread(target=watchdog, daemon=True).start()

        def may_start_round():
            return not client.stop.is_set() and time.time() + min_round_s < hard_stop

        def timeout():
            return hard_stop - time.time() + 30

        done = [0]

        def work(i_tid):
            i, tid = i_tid
            if not may_start_round():
                return
            task = challenges[tid]
            try:
                progs, n_tok = solve_task(client, task, budget_per_round, max_rounds, answer_room,
                                          seed=1000 + i, timeout=timeout, sandbox_timeout=sandbox_timeout,
                                          may_start_round=may_start_round, reasoning_effort=reasoning_effort,
                                          prompt_hook=prompt_hook, task_id=tid)
            except Exception as e:
                log(f"{tid} crashed: {type(e).__name__}: {e}")
                return
            if not progs and n_tok == 0:
                return
            rec = summarize(task, progs, n_tok)
            with lock:
                results[tid] = rec
                done[0] += 1
                write_atomic(results, out_path)
                nv = sum(r["verified"] for r in results.values())
                log(f"{tid} verified={rec['verified']} train_ok={rec['n_train_ok']}/{rec['n_train']} "
                    f"tok={n_tok} | {done[0]}/{len(todo)} done, {nv} verified, {time.time() - t0:.0f}s")

        with ThreadPoolExecutor(max_workers=concurrency) as ex:
            list(ex.map(work, list(enumerate(todo))))
        client.stop.set()
    finally:
        if proc is not None:
            stop_server(proc)
        with lock:
            write_atomic(results, out_path)
        log(f"phase finished: {len(results)} tasks with results, "
            f"{sum(r['verified'] for r in results.values())} verified, {time.time() - t0:.0f}s")
    return results
