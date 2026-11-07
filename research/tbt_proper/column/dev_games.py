"""Development only: ad-hoc column sets on the 12 tuning games. usage: python dev_games.py TAG sensors reaches [--rollouts]"""
import json, multiprocessing as mp, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import games as G

def _one(a):
    return G.run_game(*a)

if __name__ == "__main__":
    tag, sensors, reach = sys.argv[1:4]
    configs = [dict(kind=s, reach=int(r)) for s in sensors.split(",") for r in reach.split(",")]
    t0 = time.time()
    rows = []
    with mp.Pool(4, maxtasksperchild=1) as pool:
        for r in pool.imap_unordered(_one, [(g, configs, {}, None, "--rollouts" in sys.argv) for g in G.named("tuning")], chunksize=1):
            rows += r
    json.dump(rows, open(os.path.join(HERE, "dev", f"games_{tag}.json"), "w"))
    print(tag, G.summary(rows), "wall", round(time.time() - t0, 1))
