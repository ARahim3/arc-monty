"""Reframe pass: recount the final public leaderboard (read 2026-11-07) for Table 1's field line.
Run isolated, from outside the data folder:
    .venv/bin/python -I research/paper/v8_notes/scripts/reframe_lb.py > research/paper/v8_notes/reframe_lb.txt"""
import os  # noqa: E402  (release: paths from the repo root)
_REPO = os.environ.get("ARC_MONTY_ROOT", os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..")))  # repo root
import csv, statistics, sys

D = (_REPO + "/external/judge/lb/")
FILES = ["arc-prize-2026-arc-agi-2-publicleaderboard-2026-10-30T21:11:03.csv",
         "arc-prize-2026-arc-agi-2-publicleaderboard-2026-11-07T12:23:22.csv"]
OWN = "rahim3"

for f in FILES:
    with open(D + f, encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))
    sc = [float(r["Score"]) for r in rows]
    own = [r for r in rows if OWN in r["TeamMemberUserNames"].split(",")]
    print(f)
    print("  teams", len(rows), "; distinct TeamId", len({r["TeamId"] for r in rows}))
    print("  top", max(sc), "; median", statistics.median(sc))
    print("  scoring 28 to 34 inclusive", sum(28 <= x <= 34 for x in sc))
    for r in own:
        s = float(r["Score"])
        tied = [int(q["Rank"]) for q in rows if float(q["Score"]) == s]
        above = sum(x > s for x in sc)
        print(f"  own team {r['TeamName']!r}: Rank column {r['Rank']}, score {s}; teams strictly above {above}; "
              f"tied at {s}: {len(tied)} teams, Rank column {min(tied)}-{max(tied)}")
    print("  Rank column is 1..n in file order:", [int(r["Rank"]) for r in rows] == list(range(1, len(rows) + 1)))
