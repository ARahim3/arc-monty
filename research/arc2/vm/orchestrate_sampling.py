#!/usr/bin/env python3
"""Laptop side: run FA-LOO sampling on whatever spot VMs exist (research/arc2/faloo_qwen_sampling.md). Runs until both stages are done,
the stop time passes or the stop file appears.

Rules (user, no exceptions): only requests named arc-v6e-r, arc-v6e-r2, ... are looked at or created; NOTHING IS EVER DELETED. A dead
request (SUSPENDED/FAILED) stays where it is and a new one is queued under the next name, at most 6 per zone. Always --zone, spot v6e-8.
Everything created is appended to research/arc2/logs/sampling/tpu_resources.txt.
Stage 2 starts only when stage 1 is complete in the laptop's merged file."""
import os  # noqa: E402  (release: paths from the repo root)
_REPO = os.environ.get("ARC_MONTY_ROOT", os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")))  # repo root
_GCP_PROJECT = os.environ["GCP_PROJECT"]  # your Google Cloud project id
import calendar
import json
import os
import re
import subprocess
import sys
import tempfile
import threading
import time

R = _REPO
RES = f"{R}/llm/results"
LOG = f"{R}/research/arc2/logs/sampling"
SHIP = f"{R}/research/arc2/vm/ship_sampling.sh"
MERGE = f"{R}/research/arc2/vm/merge_sampling.py"
STOP_FILE = f"{LOG}/stop"
STAGES = ["1", "1b", "2"]
STAGE_DEADLINE = {"1": calendar.timegm((2026, 11, 3, 12, 0, 0)), "1b": calendar.timegm((2026, 11, 3, 12, 0, 0)),
                  "2": calendar.timegm((2026, 11, 5, 12, 0, 0))}
DEADLINE = STAGE_DEADLINE["2"]
ZONES = ["us-east1-d", "europe-west4-a"]
OUT = {"1": f"{RES}/qwen38_faloo_sampling_b32768.jsonl", "1b": f"{RES}/qwen38_faloo_sampling_plain_b32768.jsonl",
       "2": f"{RES}/qwen38_faloo_sampling_concept_b32768.jsonl"}
EXPECT = {"1": 479, "1b": 360, "2": 587}
MAX_PER_ZONE = 6
PULL_EVERY = 180
NAME = re.compile(r"^arc-v6e-r(\d*)$")
os.makedirs(LOG, exist_ok=True)
sys.path.insert(0, f"{R}/research/arc2")


def log(*a):
    print(time.strftime("%H:%M:%S", time.gmtime()), *a, flush=True)


def sh(cmd, timeout=180):
    try:
        p = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired:
        return 124, "", "timeout"


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


def queue_next(z, reqs):
    """At most MAX_PER_ZONE of our requests may EXIST per zone (lead, 11-01); dead ones are cleared by the lead, never here. Names keep
    counting up past anything used before, so a VM's logs and claim files are never overwritten."""
    used = max((idx(n) for n in reqs), default=0)
    rf = f"{LOG}/tpu_resources.txt"
    if os.path.exists(rf):
        for line in open(rf):
            m = re.search(rf"create arc-v6e-r(\d*) zone {z} ", line)
            if m:
                used = max(used, int(m.group(1) or 1))
    if len(reqs) >= MAX_PER_ZONE:
        log(f"{z}: {len(reqs)} requests exist, at the limit of {MAX_PER_ZONE}; not queuing. Ask the lead to clear: {sorted(reqs)}")
        return False
    name = f"arc-v6e-r{used + 1}"
    rc, o, e = sh(f"gcloud compute tpus queued-resources create {name} --project={_GCP_PROJECT} --zone={z} --node-id={name} "
                  f"--accelerator-type=v6e-8 --runtime-version=v2-alpha-tpuv6e --spot", 180)
    with open(f"{LOG}/tpu_resources.txt", "a") as f:
        f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())} create {name} zone {z} node {name} spot v6e-8 rc={rc}\n")
    log(f"{z}: queued {name} rc={rc} {e.strip()[:200] if rc else ''}")
    return rc == 0


def n_good(path):
    keys = set()
    if not os.path.exists(path):
        return 0
    for line in open(path):
        try:
            r = json.loads(line)
        except Exception:
            continue
        if "error" not in r:
            keys.add((r["kind"], r["task_id"], r["fold"]))
    return len(keys)


def wanted_stage():
    """First incomplete stage still inside its deadline. A later stage starts only when the earlier ones are complete in the merged
    files on the laptop, or past their deadline."""
    now = time.time()
    for st in STAGES:
        if n_good(OUT[st]) < EXPECT[st] and now < STAGE_DEADLINE[st]:
            return st
    return None


def progress():
    return " ".join(f"s{st} {n_good(OUT[st])}/{EXPECT[st]}" for st in STAGES)


class VM(threading.Thread):
    """One live VM: ship once per stage, pull/merge/push every few minutes, exit after 3 failed pulls in a row (VM gone)."""
    live = {}
    lock = threading.Lock()

    def __init__(self, z, name, create):
        super().__init__(daemon=True)
        self.z, self.name, self.create = z, name, create
        self.stage_started = None
        self.key = f"{z}:{name}"
        self.vmid = f"{name}-{z}"

    def ssh(self, cmd, timeout=180):
        return sh(f"gcloud compute tpus tpu-vm ssh {self.name} --zone={self.z} --command='{cmd}'", timeout)

    def ship(self, stage):
        with VM.lock:
            direction = "backward" if any(v is not self and v.stage_started == stage for v in VM.live.values()) else "forward"
        write_claims(self, stage)
        env = f"Z={self.z} VM={self.name} DIRECTION={direction} STAGE={stage} CLIENT=1"
        rc, o, e = sh(f"{env} bash {SHIP}", 420)
        log(f"{self.key}: ship stage {stage} {direction} rc={rc} {[x for x in o.splitlines() if 'fs' in x][:2]}")
        if rc == 0:
            self.stage_started = stage
        return rc == 0

    def detect_stage(self):
        """A VM picked up again after a laptop hiccup: find which stage its client is running."""
        rc, o, _ = self.ssh("pgrep -af faloo_qwen_sampling.py | grep -o -- \"--stage [0-9][a-z]*\" | head -1", 120)
        m = re.search(r"--stage (1b|\d)", o)
        if m:
            self.stage_started = m.group(1)
            log(f"{self.key}: client already running stage {self.stage_started}")

    def run(self):
        ld = f"{LOG}/{self.z}_{self.name}"
        os.makedirs(ld, exist_ok=True)
        self.detect_stage()
        miss = 0
        while not stopping():
            ok = pull(self, ld)
            miss = 0 if ok else miss + 1
            if miss >= 3:
                log(f"{self.key}: 3 failed pulls in a row, VM treated as gone")
                break
            w = wanted_stage()
            if ok and w is not None:
                rc, o, _ = self.ssh("tmux has-session -t fs 2>/dev/null && echo FS_RUNNING || echo FS_FREE", 120)
                if "FS_FREE" in o and not self.ship(w):
                    miss += 1
            for _ in range(PULL_EVERY):
                if stopping():
                    break
                time.sleep(1)
        ok = pull(self, ld)                                   # one last pull on a stop
        with VM.lock:
            VM.live.pop(self.key, None)
        log(f"{self.key}: thread exits (last pull ok={ok})")


def stopping():
    return os.path.exists(STOP_FILE) or time.time() > DEADLINE


def write_claims(me, stage):
    """Claims of the OTHER live VMs, to be pushed to this VM (a dead VM's claims drop out with its thread)."""
    base = OUT[stage].replace(".jsonl", "")
    lines = []
    with VM.lock:
        others = [v for v in VM.live.values() if v is not me]
    for v in others:
        p = f"{base}.claims_{v.vmid}.txt"
        if os.path.exists(p):
            lines += open(p).read().splitlines()
    tmp = f"{base}.remote_claims.txt"
    with open(tmp + ".tmp", "w") as f:
        f.write("\n".join(lines) + ("\n" if lines else ""))
    os.replace(tmp + ".tmp", tmp)
    return tmp


def pull(vm, ld):
    """Tar the VM's results and logs, copy, merge into llm/results (record-wise), then push the merged view back."""
    cmd = ("tar -czf /tmp/fsres.tgz --files-from /dev/null; tar -czf /tmp/fslogs.tgz --files-from /dev/null; "
           "cd /mnt/data/arc_monty/llm/results 2>/dev/null && tar -czf /tmp/fsres.tgz --exclude=\"*.remote*\" qwen38_faloo_sampling_* 2>/dev/null; "
           "cd /mnt/data/logs 2>/dev/null && { { date -u; for p in 8001 8003; do curl -s -m 5 http://127.0.0.1:$p/metrics | grep -E \"^vllm:(num_requests_running|num_requests_waiting|kv_cache_usage_perc|num_preemptions_total|generation_tokens_total)\" | sed \"s/{[^}]*}//\" | tr \"\\n\" \" \"; echo; done; tmux ls 2>/dev/null | cut -d: -f1 | tr \"\\n\" \" \"; echo; } >> metrics.log; "
           "tar -czf /tmp/fslogs.tgz faloo_sampling.log run_sampling.log server_seeds.log metrics.log 2>/dev/null; }; true")
    rc, _, _ = vm.ssh(cmd, 150)
    if rc:
        log(f"{vm.key}: pull ssh failed rc={rc}")
        return False
    rc, _, e = sh(f"gcloud compute tpus tpu-vm scp {vm.name}:/tmp/fsres.tgz {vm.name}:/tmp/fslogs.tgz {ld}/ --zone={vm.z}", 180)
    if rc:
        log(f"{vm.key}: pull scp failed {e.strip()[:120]}")
        return False
    with tempfile.TemporaryDirectory() as t:
        sh(f"tar -xzf {ld}/fsres.tgz -C {t}; tar -xzf {ld}/fslogs.tgz -C {ld}", 60)
        for stage in STAGES:
            base = os.path.basename(OUT[stage]).replace(".jsonl", "")
            src = f"{t}/{base}.jsonl"
            if os.path.exists(src):
                sh(f"python3 {MERGE} {OUT[stage]} {src}", 120)
            src = f"{t}/{base}.ckpt.jsonl"
            if os.path.exists(src):
                sh(f"python3 {MERGE} {OUT[stage].replace('.jsonl', '.ckpt.jsonl')} {src}", 120)
            src = f"{t}/{base}.claims_{vm.vmid}.txt"
            if os.path.exists(src):
                os.replace(src, f"{OUT[stage].replace('.jsonl', '')}.claims_{vm.vmid}.txt")
    w = vm.stage_started
    if w:
        push(vm, w)
    log(f"{vm.key}: {progress()} | {tail(ld + '/faloo_sampling.log')[:40]}")
    return True


def slim_done(src, dst):
    """Keys of finished jobs only: the VM needs nothing else from them."""
    with open(dst, "w") as f:
        if os.path.exists(src):
            for line in open(src):
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                if "error" not in r:
                    f.write(json.dumps({k: r.get(k) for k in ("kind", "task_id", "fold", "started_at")}) + "\n")


def open_ckpts(ck_src, done_src, dst):
    """Checkpoints of jobs that are not finished yet, for a VM to continue from."""
    done = set()
    if os.path.exists(done_src):
        for line in open(done_src):
            try:
                r = json.loads(line)
            except Exception:
                continue
            if "error" not in r:
                done.add((r["kind"], r["task_id"], r["fold"]))
    with open(dst, "w") as f:
        if os.path.exists(ck_src):
            for line in open(ck_src):
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
                      f"{vm.name}:/mnt/data/arc_monty/llm/results/ --zone={vm.z}", 180)
    if rc:
        log(f"{vm.key}: push failed {e.strip()[:120]}")


def tail(p):
    try:
        with open(p, "rb") as f:
            f.seek(0, 2)
            f.seek(max(0, f.tell() - 200))
            return f.read().decode(errors="replace").splitlines()[-1][:110]
    except Exception:
        return ""


def main():
    log("orchestrator start; pid", os.getpid())
    dead_seen = {}
    while not stopping():
        if wanted_stage() is None:
            log("all stages complete")
            break
        for z in ZONES:
            reqs = req_list(z)
            if reqs is None:
                log(f"{z}: request list failed")
                continue
            if not reqs:
                log(f"{z}: no arc-v6e-r* request; queuing the first")
                queue_next(z, reqs)
                continue
            newest = max(reqs, key=idx)
            st = reqs[newest]
            if st in ("SUSPENDED", "FAILED"):
                log(f"{z}: {newest} is {st}: leaving it in place and queuing the next name")
                queue_next(z, reqs)
                continue
            if st == "ACTIVE":
                rc, o, e = sh(f"gcloud compute tpus tpu-vm describe {newest} --zone={z} --format='value(state,createTime)'", 90)
                p = o.split()
                key = f"{z}:{newest}"
                if rc == 0 and p and p[0] in ("PREEMPTED", "TERMINATED", "STOPPED"):
                    # the request can stay ACTIVE for a while after its VM is gone: treat it as dead, leave it in place
                    dead_seen[key] = dead_seen.get(key, 0) + 1
                    if dead_seen[key] >= 2:
                        log(f"{key}: request ACTIVE but VM {p[0]}: leaving both in place and queuing the next name")
                        queue_next(z, reqs)
                    continue
                with VM.lock:
                    running = key in VM.live
                if rc == 0 and p and p[0] == "READY" and not running:
                    log(f"{key}: READY, starting (created {p[1] if len(p) > 1 else '?'})")
                    v = VM(z, newest, p[1] if len(p) > 1 else "")
                    with VM.lock:
                        VM.live[key] = v
                    v.start()
        time.sleep(60)
    for _ in range(30):
        with VM.lock:
            if not VM.live:
                break
        time.sleep(10)
    # final pull already done by threads; print the state
    log(f"orchestrator exits: {progress()}")


if __name__ == "__main__":
    main()
