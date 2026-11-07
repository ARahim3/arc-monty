"""WS4: answers whose pooled evidence crosses the 0.99 confidence threshold only through vote.pool's accumulation
(max + 0.01*min per identical prediction), vs answers with a single fully evidenced hypothesis."""
import collections, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from common import BASE_SPLITS, ROOT, build_cands, cache_for, tasks_for
from arcmonty.evaluate import score_task
from arcmonty.vote import CONFIDENT, confident, pool, attempts_from

out = {}
for split in BASE_SPLITS + ["new233"]:
    rows, tasks = cache_for(split), tasks_for(split)
    st = collections.defaultdict(lambda: [0, 0.0]); ex = []
    for k, row in rows.items():
        cands = build_cands(row)
        best = pool(cands)
        if not best or best[0]["evidence"] < CONFIDENT:
            continue
        top = best[0]
        raw = [c["evidence"] for c in cands if len(c["preds"]) == len(top["preds"]) and all(np.array_equal(a, b) for a, b in zip(c["preds"], top["preds"]))]
        kind = "single>=0.99" if max(raw) >= CONFIDENT else "accumulated"
        ok = score_task(tasks[k], [[g] for g in top["preds"]])
        conf = confident(cands)
        st[(kind, conf)][0] += 1; st[(kind, conf)][1] += ok
        if kind == "accumulated":
            ex.append(dict(task=k, max_raw=max(raw), n_dup=len(raw), pooled=round(top["evidence"], 3), voters=sorted(top["voters"]), correct=ok, confident=conf))
    out[split] = dict(stats={f"{a}|confident={b}": v for (a, b), v in st.items()}, accumulated=ex)
    print(split, dict(out[split]["stats"]), [(e["task"], e["max_raw"], e["n_dup"], e["correct"], e["confident"]) for e in ex])
json.dump(out, open(os.path.join(ROOT, "research/monty_eval/results/pooling_check.json"), "w"), indent=1)
