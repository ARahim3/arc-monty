"""generator_control: run checks and descriptive extras for Qwen on the re-arc tasks. None of this is a planned comparison; each number is labelled
in the write-up. Reads raw JSONL as data.
    .venv/bin/python -I -B research/generator_control/qwen_extras.py
Writes results/qwen_extras.json:
  stops      how many verified-but-wrong tasks each condition stops, as in faloo_qwen_sampling.md section 3
  restarts   jobs claimed more than once across VMs, jobs resumed from a checkpoint, and the rules on tasks with no restarted job
  kv         KV-cache preemptions and peak KV use from the server metric samples
  hypergeom  chance a random subset of the certified size avoids all verified-but-wrong tasks
  vs_other   post hoc: h - t here against ARC-AGI-2 and ConceptARC, from their raw files, independent cluster bootstraps"""
import os  # noqa: E402  (release: paths from the repo root)
_REPO = os.environ.get("ARC_MONTY_ROOT", os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")))  # repo root
import collections
import glob
import json
import os
import random
import re
import sys
from math import comb

ROOT = _REPO
HERE = os.path.join(ROOT, "research", "generator_control")
sys.path.insert(0, os.path.join(ROOT, "research", "arc2"))
sys.path.insert(0, os.path.join(ROOT, "research", "monty_heldout"))
import faloo_sampling_analyze as FA  # noqa: E402


def load_rows():
    import importlib.util
    spec = importlib.util.spec_from_file_location("gc_analyse", os.path.join(HERE, "analyse.py"))
    A = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(A)
    return A, A.qwen_rows()[0]


def h_minus_t_boot(fv, B=10000, seed=0):
    """Per-task sums, percentile cluster bootstrap by task, on the fold views of faloo_sampling_analyze. Returns estimate and resamples."""
    d = [(sum(x["h"] - x["t"] for x in fs), len(fs)) for fs in fv.values()]
    n = len(d)
    rng = random.Random(seed)
    out = []
    for _ in range(B):
        s = rng.choices(d, k=n)
        out.append(sum(a for a, _ in s) / sum(b for _, b in s))
    return sum(a for a, _ in d) / sum(b for _, b in d), out


def pct(xs):
    xs = sorted(xs)
    return xs[int(0.025 * len(xs))], xs[min(len(xs) - 1, int(0.975 * len(xs)))]


def main():
    A, rows = load_rows()
    J = {}
    # what stops the verified-but-wrong tasks
    V = [r["real"] for r in rows.values() if r["real"]["fit"] is not None]
    W = [o for o in V if o["fit"] is False]
    J["stops"] = dict(verified=len(V), right=sum(o["fit"] is True for o in V), wrong=len(W), by=dict(collections.Counter(o["why"] for o in W)),
                      right_rejected=dict(collections.Counter(o["why"] for o in V if o["fit"] is True and o["fc"] is None)))
    J["hypergeom_random_subset_avoids_all_wrong"] = comb(len(V) - len(W), 107) / comb(len(V), 107) if len(V) - len(W) >= 107 else None
    # restarts
    claims = collections.Counter()
    for p in glob.glob(os.path.join(HERE, "raw", "vm", "*", "gc_qwen_main.claims_*.txt")):
        with open(p, errors="replace") as fh:
            for line in fh:
                a = line.split()
                if len(a) == 5:
                    claims[(a[0], a[1], int(a[2]))] += 1
    main, _, _ = A.read_jsonl_best(os.path.join(HERE, "raw", "gc_qwen_main.jsonl"))
    resumed = [k for k, r in main.items() if r.get("resumed_from_round", 0) > 0]
    multi = {k for k, c in claims.items() if c > 1}
    tasks_r = {k[1] for k in multi} | {k[1] for k in resumed}
    sub = [rows[t]["real"] for t in rows if t not in tasks_r]
    J["restarts"] = dict(jobs_claimed_more_than_once=len(multi), jobs_resumed=len(resumed), tasks_with_a_restart=len(tasks_r), tasks_without=len(sub),
                         fit=[sum(o["fit"] is True for o in sub), sum(o["fit"] is not None for o in sub)], fa=[sum(o["fa"] is True for o in sub), sum(o["fa"] is not None for o in sub)],
                         fc=[sum(o["fc"] is True for o in sub), sum(o["fc"] is not None for o in sub)],
                         mean_h_minus_t=sum(sum(x["h"] - x["t"] for x in o["folds"]) for o in sub) / max(1, sum(len(o["folds"]) for o in sub)))
    # KV
    pre, peak, nvm = 0.0, 0.0, 0
    for p in glob.glob(os.path.join(HERE, "logs", "qwen", "*", "metrics_gc.log")):
        last = {}
        nvm += 1
        with open(p, errors="replace") as fh:
            lines = fh.read().splitlines()
        for line in lines:
            m = re.search(r"vllm:kv_cache_usage_perc ([0-9.e-]+)", line)
            if m:
                peak = max(peak, float(m.group(1)))
        vals = [float(m.group(1)) for line in lines for m in [re.search(r"vllm:num_preemptions_total ([0-9.e+-]+)", line)] if m]
        # two servers alternate in the log; take the largest value of each column as that server's total
        pre += max(vals[0::2], default=0) + max(vals[1::2], default=0)
    J["kv"] = dict(vm_logs=nvm, preemptions_total=pre, peak_kv=peak)
    # against the other two sets, post hoc
    here_rows = {t: [dict(h=float(x["h"]), t=float(x["t"])) for x in rows[t]["real"]["folds"]] for t in rows}
    e0, b0 = h_minus_t_boot(here_rows, seed=1)
    J["here"] = dict(diff=e0, ci=pct(b0))
    J["vs_other"] = {}
    for name, path, loader in (("ARC-AGI-2 eval", FA.STAGE_FILES[1], FA.load_agi2), ("ConceptARC", FA.STAGE_FILES[2], FA.load_concept)):
        done, _ = FA.read_records(path)
        ch, sol = loader()
        fv = FA.fold_views(done, ch, sol)
        e1, b1 = h_minus_t_boot(fv, seed=2)
        J["vs_other"][name] = dict(diff=e1, ci=pct(b1), here_minus_it=e0 - e1, here_minus_it_ci=pct([a - b for a, b in zip(b0, b1)]))
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    with open(os.path.join(HERE, "results", "qwen_extras.json"), "w") as fh:
        json.dump(J, fh, indent=1, default=float)
    print(json.dumps(J, indent=1, default=float))


if __name__ == "__main__":
    main()
