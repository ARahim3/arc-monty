"""generator_control: fix which re-arc generators are used, and their seeds, before any task exists. Runs on the Mac; reads only the
names of the 400 ARC-AGI-1 training files (the same 400 ids as re-arc's generators, checked on the VM).
    python -I -B research/generator_control/select_generators.py
Writes data/selected_generators.json: all 400 ids in hash order (the first 200 are the sample, the rest are replacements, used in
order only if a generator cannot produce a valid tuple) with one seed per id. Nothing about a task's content enters the hash."""
import os  # noqa: E402  (release: paths from the repo root)
_REPO = os.environ.get("ARC_MONTY_ROOT", os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")))  # repo root
import glob
import hashlib
import json
import os

ROOT = _REPO
HERE = os.path.join(ROOT, "research", "generator_control")
TAG = "20261101|generator_control"


def rank(key):
    return hashlib.sha256(f"{TAG}|select|{key}".encode()).hexdigest()


def seed_of(key):
    return int(hashlib.sha256(f"{TAG}|seed|{key}".encode()).hexdigest()[:16], 16)


def main():
    keys = sorted(os.path.basename(f)[:-5] for f in glob.glob(os.path.join(ROOT, "data/arc-agi-1/data/training/*.json")))
    assert len(keys) == 400
    order = sorted(keys, key=rank)
    os.makedirs(os.path.join(HERE, "data"), exist_ok=True)
    out = dict(tag=TAG, n_sample=200, diff_lb=0, diff_ub=1, pairs_per_task=4, order=order, seeds={k: seed_of(k) for k in keys})
    path = os.path.join(HERE, "data", "selected_generators.json")
    with open(path, "w") as fh:
        json.dump(out, fh, indent=0)
    digest = hashlib.sha256(",".join(order[:200]).encode()).hexdigest()
    print("first 200 by hash, sorted:", " ".join(sorted(order[:200])))
    print("first five replacements:", order[200:205])
    print("sha256 of the comma-joined first 200 in hash order:", digest)


if __name__ == "__main__":
    main()
