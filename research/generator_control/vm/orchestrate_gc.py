#!/usr/bin/env python3
"""Laptop side: Qwen stages of generator_control on whatever spot VMs exist. Derived from research/arc2/vm/orchestrate_sampling.py; the original
is unchanged. Runs until every allowed stage is complete, the stop file appears, or the stop time passes.

Rules (user, no exceptions): only requests named arc-v6e-r<N> are looked at or created; NOTHING IS EVER DELETED. A dead request stays where it
is and a new one is queued under the next name, at most 6 per zone. Always --zone, spot v6e-8. Created requests are logged to
research/generator_control/logs/tpu_resources.txt. VMs named in logs/qwen/exclude_vms.txt get no Qwen work (arc-v6e-r5 runs the 2020 program).

Differences from the original, beyond paths: results come back as text through ssh with offsets, never as tar files, because a VM that ran
third-party code is untrusted; every ACTIVE request in a zone is used, not only the newest; a stage runs only if logs/qwen/allow_<stage> exists
(main is always allowed)."""
import os  # noqa: E402  (release: paths from the repo root)
_REPO = os.environ.get("ARC_MONTY_ROOT", os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")))  # repo root
_GCP_PROJECT = os.environ["GCP_PROJECT"]  # your Google Cloud project id
import calendar
import glob
import json
import os
import re
import subprocess
import tempfile
import threading
import time

R = _REPO
B = f"{R}/research/generator_control"
RAW = f"{B}/raw"
LOG = f"{B}/logs/qwen"
SHIP = f"{B}/vm/ship_gc.sh"
MERGE = f"{B}/vm/merge_gc.py"
PY = f"{R}/.venv/bin/python"
STOP_FILE = f"{LOG}/stop"
EXCL = f"{LOG}/exclude_vms.txt"
RESLOG = f"{B}/logs/tpu_resources.txt"
STAGES = ["main", "retry1", "retry2", "rep0", "rep1", "rep2", "rot", "cmain", "cretry1", "cretry2"]
OUT = {"main": f"{RAW}/gc_qwen_main.jsonl", "rot": f"{RAW}/gc_qwen_rot.jsonl", "retry1": f"{RAW}/gc_qwen_retry.jsonl", "retry2": f"{RAW}/gc_qwen_retry.jsonl",
       "rep0": f"{RAW}/gc_qwen_rep.jsonl", "rep1": f"{RAW}/gc_qwen_rep.jsonl", "rep2": f"{RAW}/gc_qwen_rep.jsonl",
       "cmain": f"{RAW}/gc_qwen_c1.jsonl", "cretry1": f"{RAW}/gc_qwen_c1_retry.jsonl", "cretry2": f"{RAW}/gc_qwen_c1_retry.jsonl"}
DEADLINE = calendar.timegm((2026, 11, 3, 12, 0, 0))
ZONES = ["us-east1-d", "europe-west4-a"]
MAX_PER_ZONE = 6
PULL_EVERY = 180
NAME = re.compile(r"^arc-v6e-r(\d*)$")
COOL = {}
os.makedirs(LOG, exist_ok=True)


def log(*a):
    print(time.strftime("%H:%M:%S", time.gmtime()), *a, flush=True)


def sh(cmd, timeout=180):
    try:
        p = subprocess.run(cmd, shell=True, capture_output=True, text=True, errors="replace", timeout=timeout)
        return p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired:
        return 124, "", "timeout"


def expected(stage):
    if stage == "main":
        return {("full" if i == 0 else "fold", t, -1 if i == 0 else i - 1) for t in tasks_rearc() for i in range(4)}
    if stage == "rot":
        return {("rot", t, k) for t in tasks_rearc() for k in range(3)}
    if stage == "cmain":
        out = set()
        d = f"{R}/external/judge/conceptarc/repo/corpus"
        for f in glob.glob(f"{d}/*/*.json"):
            t = os.path.relpath(f, d)[:-5]
            out.add(("full", t, -1))
            out |= {("fold", t, i) for i in range(len(json.load(open(f))["train"]))}
        return out
    p = f"{B}/data/{stage}.json"
    if not os.path.exists(p):
        return None
    kind = "rep" if stage.startswith("rep") and not stage.startswith("retry") else "retry"
    return {(kind, t, i * 100 + att) for t, i, att in json.load(open(p))}


_T = []


def tasks_rearc():
    if not _T:
        _T.extend(json.load(open(f"{B}/data/rearc_tasks.json"))["challenges"].keys())
    return _T


def good_keys(path):
    keys = set()
    if os.path.exists(path):
        with open(path, errors="replace") as fh:
            for line in fh:
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                if isinstance(r, dict) and "error" not in r:
                    keys.add((r.get("kind"), r.get("task_id"), r.get("fold")))
    return keys


def allowed(stage):
    return stage == "main" or os.path.exists(f"{LOG}/allow_{stage}")


def wanted_stage():
    """First allowed stage not complete in the laptop's merged file. A later stage starts only when the earlier allowed ones are complete."""
    for st in STAGES:
        if not allowed(st):
            continue
        if st in ("rep1", "rep2") and not os.path.exists(f"{B}/data/{st}.json"):
            # reached only when the earlier stages are complete; the list depends on their results
            rc, o, er = sh(f"{PY} -I -B {B}/rep_jobs.py {st[-1]}", 120)
            log(f"{st} job list: rc={rc} {o.strip()[:120]} {er.strip()[-200:] if rc else ''}")
        if st in ("cretry1", "cretry2") and not os.path.exists(f"{B}/data/{st}.json"):
            rc, o, er = sh(f"{PY} -I -B {B}/cretry_jobs.py {st[-1]}", 120)
            log(f"{st} job list: rc={rc} {o.strip()[:120]} {er.strip()[-200:] if rc else ''}")
        e = expected(st)
        if e is None:
            continue
        if e - good_keys(OUT[st]):
            return st
    return None


def progress():
    out = []
    for st in STAGES:
        if allowed(st):
            e = expected(st)
            if e is not None:
                out.append(f"{st} {len(e & good_keys(OUT[st]))}/{len(e)}")
    return " ".join(out)


def req_list(z):
    rc, o, e = sh(f"gcloud compute tpus queued-resources list --zone={z} --format='value(name,state.state)'", 90)
    if rc:
        return None
    out = {}
    for line in o.splitlines():
        p = line.split()
        if len(p) == 2 and NAME.match(p[0]):
            out[p[0]] = p[1]
    return out


def idx(name):
    return int(NAME.match(name).group(1) or 1)


def excluded():
    if not os.path.exists(EXCL):
        return set()
    return set(open(EXCL).read().split())


def queue_next(z, reqs, all_reqs):
    """Names count up past anything used anywhere, so a VM's files are never overwritten. At most MAX_PER_ZONE exist per zone."""
    if len(reqs) >= MAX_PER_ZONE:
        log(f"{z}: {len(reqs)} requests exist, at the limit of {MAX_PER_ZONE}; not queuing. Ask the lead to clear dead ones: {sorted(reqs)}")
        return False
    used = max((idx(n) for n in all_reqs), default=7)
    if os.path.exists(RESLOG):
        for line in open(RESLOG):
            m = re.search(r"create arc-v6e-r(\d+) .*rc=0", line)    # a failed create made nothing, so its name stays free
            if m:
                used = max(used, int(m.group(1)))
    name = f"arc-v6e-r{used + 1}"
    rc, o, e = sh(f"gcloud compute tpus queued-resources create {name} --project={_GCP_PROJECT} --zone={z} --node-id={name} "
                  f"--accelerator-type=v6e-8 --runtime-version=v2-alpha-tpuv6e --spot", 180)
    with open(RESLOG, "a") as f:
        f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())} create {name} zone {z} node {name} spot v6e-8 rc={rc}\n")
    log(f"{z}: queued {name} rc={rc} {e.strip()[-300:] if rc else ''}")
    if rc:
        COOL[z] = time.time() + 1800          # e.g. quota held by dead requests: try again in 30 minutes, not every minute
    return rc == 0


class VM(threading.Thread):
    """One live VM: ship once per stage, pull/merge/push every few minutes, exit after 3 failed pulls in a row (VM gone)."""
    live = {}
    lock = threading.Lock()

    def __init__(self, z, name):
        super().__init__(daemon=True)
        self.z, self.name = z, name
        self.stage_started = None
        self.stages = set()
        self.key = f"{z}:{name}"
        self.vmid = f"{name}-{z}"
        self.mirror = f"{RAW}/vm/{self.vmid}"
        os.makedirs(self.mirror, exist_ok=True)
        self.ld = f"{LOG}/{self.z}_{self.name}"
        os.makedirs(self.ld, exist_ok=True)

    def ssh(self, cmd, timeout=180):
        return sh(f"gcloud compute tpus tpu-vm ssh {self.name} --zone={self.z} --quiet --command='{cmd}'", timeout)

    def ship(self, stage):
        with VM.lock:
            direction = "backward" if any(v is not self and v.stage_started == stage for v in VM.live.values()) else "forward"
        write_claims(self, stage)
        env = f"Z={self.z} VM={self.name} DIRECTION={direction} STAGE={stage} CLIENT=1"
        rc, o, e = sh(f"{env} bash {SHIP}", 600)
        log(f"{self.key}: ship stage {stage} {direction} rc={rc} {[x for x in o.splitlines() if 'gcq' in x][:2]} {e.strip()[-150:] if rc else ''}")
        if rc == 0:
            self.stage_started = stage
            self.stages.add(stage)
        return rc == 0

    def detect_stage(self):
        rc, o, _ = self.ssh("pgrep -af qwen_gc.py | grep -o -- \"--stage [a-z0-9]*\" | head -1", 120)
        m = re.search(r"--stage ([a-z0-9]+)", o)
        if m and m.group(1) in OUT:
            self.stage_started = m.group(1)
            self.stages.add(self.stage_started)
            log(f"{self.key}: client already running stage {self.stage_started}")

    def run(self):
        self.detect_stage()
        miss = 0
        while not stopping():
            ok = pull(self)
            miss = 0 if ok else miss + 1
            if miss >= 3:
                log(f"{self.key}: 3 failed pulls in a row, VM treated as gone")
                break
            if self.stage_started is None:
                self.detect_stage()        # a client started by an earlier orchestrator may still be in bring-up
            w = wanted_stage()
            if ok and w is not None:
                rc, o, _ = self.ssh("tmux has-session -t gcq 2>/dev/null && echo GCQ_RUNNING || echo GCQ_FREE", 120)
                if "GCQ_FREE" in o and not self.ship(w):
                    miss += 1
            for _ in range(PULL_EVERY):
                if stopping():
                    break
                time.sleep(1)
        ok = pull(self)
        with VM.lock:
            VM.live.pop(self.key, None)
        log(f"{self.key}: thread exits (last pull ok={ok})")


def stopping():
    return os.path.exists(STOP_FILE) or time.time() > DEADLINE


def write_claims(me, stage):
    """Claims of the OTHER live VMs, to be pushed to this VM (a dead VM's claims drop out with its thread)."""
    name = os.path.basename(OUT[stage]).replace(".jsonl", "")
    lines = []
    with VM.lock:
        others = [v for v in VM.live.values() if v is not me]
    for v in others:
        p = f"{v.mirror}/{name}.claims_{v.vmid}.txt"
        if os.path.exists(p):
            with open(p, errors="replace") as fh:
                lines += [x for x in fh.read().splitlines() if re.fullmatch(r"[a-z]+ [A-Za-z0-9_./-]+ -?\d+ \d+ [A-Za-z0-9-]+", x)]
    tmp = f"{RAW}/{name}.remote_claims.txt"
    with open(tmp + ".tmp", "w") as f:
        f.write("\n".join(lines) + ("\n" if lines else ""))
    os.replace(tmp + ".tmp", tmp)
    return tmp


def pull_offset(vm, remote, local):
    """Append new bytes of a remote text file to a local mirror. Returns False if ssh failed."""
    n = os.path.getsize(local) if os.path.exists(local) else 0
    try:
        p = subprocess.run(["gcloud", "compute", "tpus", "tpu-vm", "ssh", vm.name, f"--zone={vm.z}", "--quiet",
                            f"--command=tail -c +{n + 1} {remote} 2>/dev/null; true"], capture_output=True, timeout=240)
    except subprocess.TimeoutExpired:
        return False
    if p.returncode:
        return False
    with open(local, "ab") as fh:
        fh.write(p.stdout)
    return True


def pull(vm):
    rbase = "/mnt/data/arc_monty/research/generator_control/raw"
    cmd = ("cd /mnt/data/logs 2>/dev/null && { { date -u; for p in 8001 8003; do curl -s -m 5 http://127.0.0.1:$p/metrics | grep -E \"^vllm:(num_requests_running|num_requests_waiting|kv_cache_usage_perc|num_preemptions_total|generation_tokens_total)\" | sed \"s/{[^}]*}//\" | tr \"\\n\" \" \"; echo; done; tmux ls 2>/dev/null | cut -d: -f1 | tr \"\\n\" \" \"; echo; } >> metrics_gc.log; }; true")
    rc, _, _ = vm.ssh(cmd, 150)
    if rc:
        log(f"{vm.key}: pull ssh failed rc={rc}")
        return False
    ok = True
    for lf in ("gc_qwen.log", "run_gc.log", "server_seeds.log", "metrics_gc.log"):
        ok = pull_offset(vm, f"/mnt/data/logs/{lf}", f"{vm.ld}/{lf}") and ok
    for stage in sorted(vm.stages):
        name = os.path.basename(OUT[stage]).replace(".jsonl", "")
        for suffix in (".jsonl", ".ckpt.jsonl", f".claims_{vm.vmid}.txt"):
            ok = pull_offset(vm, f"{rbase}/{name}{suffix}", f"{vm.mirror}/{name}{suffix}") and ok
        sh(f"{PY} -I -B {MERGE} {OUT[stage]} {vm.mirror}/{name}.jsonl", 120)
        sh(f"{PY} -I -B {MERGE} {OUT[stage].replace('.jsonl', '.ckpt.jsonl')} {vm.mirror}/{name}.ckpt.jsonl", 120)
    if not ok:
        log(f"{vm.key}: pull incomplete")
        return False
    if vm.stage_started:
        push(vm, vm.stage_started)
    log(f"{vm.key}: {progress()} | {tail(vm.ld + '/gc_qwen.log')[:60]}")
    return True


def slim_done(src, dst):
    with open(dst, "w") as f:
        if os.path.exists(src):
            with open(src, errors="replace") as fh:
                for line in fh:
                    try:
                        r = json.loads(line)
                    except Exception:
                        continue
                    if "error" not in r:
                        f.write(json.dumps({k: r.get(k) for k in ("kind", "task_id", "fold", "started_at")}) + "\n")


def open_ckpts(ck_src, done_src, dst):
    done = good_keys(done_src)
    with open(dst, "w") as f:
        if os.path.exists(ck_src):
            with open(ck_src, errors="replace") as fh:
                for line in fh:
                    try:
                        r = json.loads(line)
                    except Exception:
                        continue
                    if (r.get("kind"), r.get("task_id"), r.get("fold")) not in done:
                        f.write(json.dumps(r) + "\n")


def push(vm, stage):
    base = OUT[stage]
    name = os.path.basename(base).replace(".jsonl", "")
    with tempfile.TemporaryDirectory() as tmp:
        slim_done(base, f"{tmp}/{name}.remote.jsonl")
        open_ckpts(base.replace(".jsonl", ".ckpt.jsonl"), base, f"{tmp}/{name}.ckpt.remote.jsonl")
        claims = write_claims(vm, stage)
        sh(f"cp {claims} {tmp}/", 30)
        rc, _, e = sh(f"gcloud compute tpus tpu-vm scp {tmp}/{name}.remote.jsonl {tmp}/{name}.ckpt.remote.jsonl {tmp}/{name}.remote_claims.txt "
                      f"{vm.name}:/mnt/data/arc_monty/research/generator_control/raw/ --zone={vm.z} --quiet", 180)
    if rc:
        log(f"{vm.key}: push failed {e.strip()[:120]}")


def tail(p):
    try:
        with open(p, "rb") as f:
            f.seek(0, 2)
            f.seek(max(0, f.tell() - 300))
            return f.read().decode(errors="replace").splitlines()[-1][:110]
    except Exception:
        return ""


def main():
    log("orchestrator start; pid", os.getpid(), "allowed:", [s for s in STAGES if allowed(s)])
    dead_seen = {}
    while not stopping():
        if wanted_stage() is None:
            log("all allowed stages complete")
            break
        excl = excluded()
        lists = {z: req_list(z) for z in ZONES}
        all_reqs = {n for v in lists.values() if v for n in v}
        for z in ZONES:
            reqs = lists[z]
            if reqs is None:
                log(f"{z}: request list failed")
                continue
            alive = False
            for name, st in sorted(reqs.items(), key=lambda kv: idx(kv[0])):
                if name in excl or idx(name) < 5:
                    continue
                if st in ("SUSPENDED", "FAILED", "SUSPENDING", "DELETING"):
                    continue
                if st != "ACTIVE":
                    alive = True           # still waiting or provisioning
                    continue
                rc, o, e = sh(f"gcloud compute tpus tpu-vm describe {name} --zone={z} --format='value(state,createTime)'", 90)
                p = o.split()
                key = f"{z}:{name}"
                if rc == 0 and p and p[0] in ("PREEMPTED", "TERMINATED", "STOPPED"):
                    dead_seen[key] = dead_seen.get(key, 0) + 1
                    if dead_seen[key] < 2:
                        alive = True       # look again before queuing
                    continue
                alive = True
                with VM.lock:
                    running = key in VM.live
                if rc == 0 and p and p[0] == "READY" and not running:
                    log(f"{key}: READY, starting (created {p[1] if len(p) > 1 else '?'})")
                    v = VM(z, name)
                    with VM.lock:
                        VM.live[key] = v
                    v.start()
            if not alive and time.time() >= COOL.get(z, 0):
                log(f"{z}: no live request for Qwen: leaving dead ones in place and queuing the next name")
                queue_next(z, reqs, all_reqs)
                lists[z] = req_list(z)
                all_reqs = {n for v in lists.values() if v for n in v}
        time.sleep(60)
    for _ in range(30):
        with VM.lock:
            if not VM.live or not os.path.exists(STOP_FILE):
                break
        time.sleep(10)
    log(f"orchestrator exits: {progress()}")


if __name__ == "__main__":
    main()
