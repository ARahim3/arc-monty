"""monty-heldout: shared helpers. Read-only on arcmonty and research/monty_eval (imported, never edited)."""
import os  # noqa: E402  (release: paths from the repo root)
_REPO = os.environ.get("ARC_MONTY_ROOT", os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")))  # repo root
import os
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_v, "1")
import glob
import hashlib
import json
import sys

ROOT = _REPO
HERE = os.path.join(ROOT, "research", "monty_heldout")
CACHE = os.path.join(HERE, "cache")
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "research", "monty_eval"))
import numpy as np  # noqa: E402

from arcmonty.data import _task  # noqa: E402

MODULES = ["self-model", "periodic", "behavior", "dynamics", "composition", "association", "pattern", "field"]
CONCEPT = os.path.join(ROOT, "external", "judge", "conceptarc", "repo", "corpus")


def h(a):
    """Same hash as paper-judge's rotate.py, so answers can be compared with rotate_concept.jsonl."""
    a = np.ascontiguousarray(a)
    return hashlib.md5(str(a.shape).encode() + a.astype(np.int8).tobytes()).hexdigest()[:12]


def items_from_dir(path):
    """One item per test pair, as rotate.py / concept_full.py: (key, pool), pool = demos + that test pair (last)."""
    out = []
    for f in sorted(glob.glob(os.path.join(path, "**", "*.json"), recursive=True)):
        try:
            with open(f) as fh:
                t = _task(json.load(fh))
        except Exception:
            continue
        if not t["test_out"]:
            continue
        k = os.path.relpath(f, path)[:-5]
        for ti, (x, y) in enumerate(zip(t["test"], t["test_out"])):
            out.append((f"{k}#{ti}", list(t["train"]) + [(x, y)]))
    return out


def task_of(key):
    return key.split("#")[0]


def group_of(key):
    return key.split("/")[0]


def read_done(path):
    """Tasks already cached; drops a torn last line left by a killed run."""
    done, good, torn = set(), [], False
    if os.path.exists(path):
        with open(path) as fh:
            for line in fh:
                try:
                    done.add(json.loads(line)["task"])
                    good.append(line if line.endswith("\n") else line + "\n")
                except Exception:
                    torn = True
        if torn:
            with open(path, "w") as fh:
                fh.writelines(good)
    return done
