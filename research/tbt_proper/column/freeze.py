"""Record the hash of the frozen code and of the plan. usage: python freeze.py  -> FROZEN.json. Refuses to overwrite.
After this file exists, run_all.py opens test data only if every hash still matches."""
import datetime, hashlib, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
CORE = ("column.py", "settings.py", "static.py", "games.py", "data_sets.py", "monty_fresh.py", "run_all.py")
PLAN = os.path.join(HERE, "PLAN.md")
PATH = os.path.join(HERE, "FROZEN.json")


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def plan_hash():
    """SHA-256 of the plan up to the line '## Addenda'; anything added after the freeze goes below that line."""
    text = open(PLAN).read()
    return hashlib.sha256(text[:text.index("\n## Addenda")].encode()).hexdigest()


def core():
    return {f: sha(os.path.join(HERE, f)) for f in CORE}


def combined(hashes):
    return hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest()


def check():
    """Raises unless the frozen code is byte-identical."""
    rec = json.load(open(PATH))
    now = core()
    assert now == rec["files"], {k: (now[k], rec["files"][k]) for k in now if now[k] != rec["files"].get(k)}
    return rec


if __name__ == "__main__":
    assert not os.path.exists(PATH), "already frozen"
    h = core()
    rec = dict(frozen_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), files=h, code_sha256=combined(h), plan_section0_sha256=plan_hash(), analysis_at_freeze_sha256=sha(os.path.join(HERE, "analyse.py")))
    json.dump(rec, open(PATH, "w"), indent=1)
    print(json.dumps(rec, indent=1))
