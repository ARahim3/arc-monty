"""SPIKE analysis: tuning-half ARC-AGI-3 games only. Reads results/arc3_spike.json and the world-model probe's rows."""
import json
import os
from collections import defaultdict

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
d = json.load(open(os.path.join(HERE, "results", "arc3_spike.json")))
on, lib, pr = d["online"], d["lib"], d["probes"]


def boot(xs, clusters, n=4000, seed=0):
    rng = np.random.default_rng(seed)
    by = defaultdict(list)
    for x, c in zip(xs, clusters):
        by[c].append(x)
    keys = sorted(by)
    vals = []
    for _ in range(n):
        s = rng.choice(len(keys), len(keys))
        vals.append(np.concatenate([np.array(by[keys[i]], float) for i in s]).mean())
    return np.percentile(vals, [2.5, 97.5]).round(3).tolist()


print("transitions", len(on), "games", len({r["game"] for r in on}))
col = [r["col"] for r in on]
b0 = [r["b0"] for r in on]
print("exact playfield: column %.3f, no-change %.3f" % (np.mean(col), np.mean(b0)))
ch = [r for r in on if r["n_ch"] > 0]
print("changed transitions:", len(ch), "column exact %.3f" % np.mean([r["col"] for r in ch]),
      "changed-cell recall %.3f" % (sum(r["cc"] for r in ch) / sum(r["n_ch"] for r in ch)))

# same transitions as the world-model probe, k = 3 and k = 12
for fn, ks in (("wm2_m2.jsonl", (2, 3, 6)), ("wm2_m2_k8_12.jsonl", (12,))):
    rows = defaultdict(dict)
    for line in open(os.path.join(ROOT, "research", "arc3_wm", "results", fn)):
        r = json.loads(line)
        rows[(r["game"], r["i"], r["k"])] = r
    idx = {(r["game"], r["i"]): r for r in on}
    for k in ks:
        pick = [(idx[(g, i)], r) for (g, i, kk), r in rows.items() if kk == k and (g, i) in idx]
        if not pick:
            continue
        a = np.mean([x["col"] for x, _ in pick])
        print(f"k={k}: n={len(pick)} column {a:.3f} | B0 {np.mean([r['B0_play'] for _, r in pick]):.3f} "
              f"B1rel {np.mean([r['B1rel_play_play'] for _, r in pick]):.3f} "
              f"Monty any {np.mean([r.get('M_play_fallback', False) for _, r in pick]):.3f}")
        non = [(x, r) for x, r in pick if not r["B0_play"]]
        print(f"     on {len(non)} changed: column {np.mean([x['col'] for x, _ in non]):.3f} "
              f"B1rel {np.mean([r['B1rel_play_play'] for _, r in non]):.3f} "
              f"Monty any {np.mean([r.get('M_play_fallback', False) for _, r in non]):.3f}")

print("per game column / no-change")
for g in sorted({r["game"] for r in on}):
    s = [r for r in on if r["game"] == g]
    print(" ", g.split("-")[0], len(s), round(np.mean([r["col"] for r in s]), 3), round(np.mean([r["b0"] for r in s]), 3))

print("\nPersisting models: library from the 11 other games, colour-free")
for name, sel in (("first use of an action key", lambda r: r["uses"] == 0), ("uses 1-2", lambda r: 1 <= r["uses"] <= 2),
                  ("uses >= 3", lambda r: r["uses"] >= 3)):
    s = [r for r in lib if sel(r)]
    sc = [r for r in s if r["n_ch"] > 0]
    print(f" {name}: n={len(s)} alone {np.mean([r['col'] for r in s]):.3f} library {np.mean([r['lib'] for r in s]):.3f} "
          f"no-change {np.mean([r['b0'] for r in s]):.3f}; on {len(sc)} changed: alone "
          f"{np.mean([r['col'] for r in sc]) if sc else 0:.3f} library {np.mean([r['lib'] for r in sc]) if sc else 0:.3f}; "
          f"changed-cell recall alone {sum(r['cc'] for r in sc) / max(1, sum(r['n_ch'] for r in sc)):.3f} "
          f"library {sum(r['lib_cc'] for r in sc) / max(1, sum(r['n_ch'] for r in sc)):.3f}")
diff = [int(r["lib"]) - int(r["col"]) for r in lib]
print(" library minus alone, all transitions: %+.4f %s" % (np.mean(diff), boot(diff, [r["game"] for r in lib])))

print("\nHypothesis-driven action, probe states:", len(pr), "games", len({r["game"] for r in pr}))
print(" states where top-2 hypotheses disagree on some action:", round(np.mean([r["any_dis"] for r in pr]), 3))
for name, k, nk in (("hypothesis-testing", "ht_surprise", "ht_noop"), ("least-used", "lu_surprise", "lu_noop"),
                    ("largest predicted change", "pc_surprise", "pc_noop")):
    print(f" {name}: surprise {np.mean([r[k] for r in pr]):.3f}, no-op {np.mean([r[nk] for r in pr]):.3f}")
print(f" random action (mean over actions): surprise {np.mean([r['r_surprise'] for r in pr]):.3f}, "
      f"no-op {np.mean([r['r_noop'] for r in pr]):.3f}")
for name, k in (("HT - random", "ht_surprise"), ("least-used - random", "lu_surprise"), ("pred-change - random", "pc_surprise")):
    diff = [float(r[k]) - r["r_surprise"] for r in pr]
    print(f" {name}: {np.mean(diff):+.3f} {boot(diff, [r['game'] for r in pr])}")
diff = [float(r["ht_surprise"]) - float(r["lu_surprise"]) for r in pr]
print(f" HT - least-used: {np.mean(diff):+.3f} {boot(diff, [r['game'] for r in pr])}")

# ---- switches on the same column, and paired checks against the probe's baselines
sw_path = os.path.join(HERE, "results", "arc3_switches.json")
if os.path.exists(sw_path):
    sw = json.load(open(sw_path))
    base = {(r["game"], r["i"]): r for r in sw["full"]}
    print("\nSwitches (same column, 12 tuning games, paired by transition, CI by game)")
    for arm, rows in sw.items():
        ch = [r for r in rows if r["n_ch"] > 0]
        line = f" {arm:7s} exact {np.mean([r['col'] for r in rows]):.3f}, on changed {np.mean([r['col'] for r in ch]):.3f}, " \
               f"changed-cell recall {sum(r['cc'] for r in ch) / sum(r['n_ch'] for r in ch):.3f}"
        conf = [r for r in rows if r["conf"]]
        line += f"; calibrated non-identity: coverage {len(conf) / len(rows):.3f}, precision {np.mean([r['col'] for r in conf]) if conf else 0:.3f}"
        if arm != "full":
            diff = [int(r["col"]) - int(base[(r["game"], r["i"])]["col"]) for r in ch]
            line += f"; minus full on changed {np.mean(diff):+.3f} {boot(diff, [r['game'] for r in ch])}"
        print(line)
    print("\nOpen-loop rollouts (no new sensation; exact playfield at k steps, against 'still looks like the start')")
    for h in (2, 4, 8):
        s = [r for r in sw["full"] if f"roll{h}" in r]
        print(f" k={h}: n={len(s)} rollout {np.mean([r[f'roll{h}'] for r in s]):.3f}, unchanged-frame baseline {np.mean([r[f'still{h}'] for r in s]):.3f}")
    # alignment with the probe's rows, then the paired comparison with B1rel and Monty-ARC columns
    for fn, k in (("wm2_m2.jsonl", 3), ("wm2_m2.jsonl", 6), ("wm2_m2_k8_12.jsonl", 12)):
        rows = []
        for line in open(os.path.join(ROOT, "research", "arc3_wm", "results", fn)):
            r = json.loads(line)
            if r["k"] == k and (r["game"], r["i"]) in base:
                rows.append((base[(r["game"], r["i"])], r))
        agree = np.mean([x["b0"] == r["B0_play"] for x, r in rows])
        ch = [(x, r) for x, r in rows if not r["B0_play"]]
        print(f"\n k={k}: {len(rows)} transitions; no-change labels agree with the probe on {agree:.4f}; {len(ch)} changed")
        for name, key in (("B1rel", "B1rel_play_play"), ("Monty any", "M_play_fallback")):
            d1 = [int(x["col"]) - int(bool(r.get(key))) for x, r in rows]
            d2 = [int(x["col"]) - int(bool(r.get(key))) for x, r in ch]
            print(f"   column minus {name}: all {np.mean(d1):+.3f} {boot(d1, [r['game'] for _, r in rows])}; "
                  f"changed {np.mean(d2):+.3f} {boot(d2, [r['game'] for _, r in ch])}")
        conf = [(x, r) for x, r in rows if r.get("M_conf") and not r.get("M_identity")]
        cc = [(x, r) for x, r in rows if x["conf"]]
        print(f"   calibrated non-identity: column coverage {len(cc) / len(rows):.3f} precision "
              f"{np.mean([x['col'] for x, _ in cc]) if cc else 0:.3f}; Monty coverage {len(conf) / len(rows):.3f} precision "
              f"{np.mean([bool(r.get('M_play')) for _, r in conf]) if conf else 0:.3f}")
    print("\nPer game, changed transitions: column, B1rel (k=3)")
    per = {}
    for line in open(os.path.join(ROOT, "research", "arc3_wm", "results", "wm2_m2.jsonl")):
        r = json.loads(line)
        if r["k"] == 3 and (r["game"], r["i"]) in base and not r["B0_play"]:
            per.setdefault(r["game"], []).append((base[(r["game"], r["i"])]["col"], r["B1rel_play_play"], bool(r.get("M_play_fallback"))))
    for g, v in sorted(per.items()):
        a = np.array(v, float)
        print(f"  {g.split('-')[0]} n={len(v)} column {a[:, 0].mean():.3f} B1rel {a[:, 1].mean():.3f} Monty {a[:, 2].mean():.3f}")
