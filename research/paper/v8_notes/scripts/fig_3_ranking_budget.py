"""Figure 3: the ranking ceiling as a budget curve.

Values copied from research/paper/v8/paper.md, Table 8 (Section 7): score of 120
on ARC-AGI-2 public evaluation by candidate order, Qwen at 32k, logged runs;
random = expected score over uniformly random orders, with the 5th-95th percentile
of 100,000 orders (v8c: recomputed from the logged runs in v8c_qwen.txt section 5,
replacing the mean, minimum and maximum of 40 orders); crowded = test outputs, of
167, with more than two candidates.
"""
import matplotlib.pyplot as plt

import fig_style as S

S.setup()

K = [1, 2, 3, 4]
VERIFIED = [34.7, 47.0, 55.0, 55.0]
RANDOM = [34.7, 47.0, 52.0, 50.4]
RAND_LO = [34.7, 47.0, 49.0, 47.5]   # 5th percentile
RAND_HI = [34.7, 47.0, 54.5, 53.5]   # 95th percentile
UNVERIFIED = [34.7, 47.0, 45.5, 42.0]
PERFECT = [34.7, 47.0, 57.0, 57.5]
CROWDED = [0, 0, 51, 91]

W, H = 12.0, 7.6
fig = plt.figure(figsize=(W * S.CM, H * S.CM))
L, B, PW, PH = 1.35, 1.85, 6.6, 5.4
ax = fig.add_axes([L / W, B / H, PW / W, PH / H])

ax.set_xlim(0.8, 4.2)
ax.set_ylim(30, 60)
ax.set_xticks(K)
ax.set_yticks([30, 40, 50, 60])
ax.tick_params(axis="y", length=0, labelcolor=S.INK2)
ax.spines["left"].set_visible(False)
for y in (40, 50, 60):
    ax.axhline(y, color=S.GRID, lw=0.5, zorder=0)
ax.set_ylabel("Score of 120", labelpad=4)
fig.text((L + PW / 2) / W, 0.12 / H, "Samples per task", ha="center", va="bottom",
         fontsize=8, color=S.INK2)

ax.fill_between(K[1:], RAND_LO[1:], RAND_HI[1:], color=S.BAND, lw=0, zorder=1)
MS = 4.6
# 1 and 2 samples: every order gives the same score, so one shared neutral segment
assert VERIFIED[:2] == RANDOM[:2] == UNVERIFIED[:2] == PERFECT[:2]
ax.plot(K[:2], VERIFIED[:2], color=S.INK2, lw=1.8, marker="o", ms=MS, mec=S.SURFACE, mew=0.8, zorder=6)
k = K[1:]
ax.plot(k, RANDOM[1:], color=S.MUTED, lw=1.5, marker="o", ms=MS - 1, mfc=S.MUTED, mec=S.SURFACE,
        mew=0.8, markevery=[1, 2], zorder=2)
ax.plot(k, UNVERIFIED[1:], color=S.ORANGE, lw=1.5, marker="D", ms=MS - 0.6, mec=S.SURFACE, mew=0.8,
        markevery=[1, 2], zorder=3)
ax.plot(k, PERFECT[1:], color=S.INK, lw=1.1, ls=(0, (3.5, 2)), marker="s", ms=MS - 1, mfc=S.SURFACE,
        mec=S.INK, mew=0.9, markevery=[1, 2], zorder=4)
ax.plot(k, VERIFIED[1:], color=S.BLUE, lw=1.8, marker="o", ms=MS, mec=S.SURFACE, mew=0.8,
        markevery=[1, 2], zorder=5)

# the shared values at 1 and 2 samples
ax.text(1.07, VERIFIED[0] - 0.3, f"{VERIFIED[0]:.1f}", fontsize=7.5, color=S.INK2, ha="left", va="top")
ax.text(2.0, VERIFIED[1] - 1.2, f"{VERIFIED[1]:.1f}", fontsize=7.5, color=S.INK2, ha="left", va="top")

# direct labels at the line ends (x = 4), values from Table 8
lab = dict(fontsize=8, va="center", ha="left", color=S.INK, clip_on=False)
X = 4.17
ax.text(X, 57.9, "Perfect ranker  57.5", **lab)
ax.text(X, 54.8, "Verified first  55.0", **lab)
ax.text(X, 51.2, "Random order  50.4", **lab)
ax.text(X, 49.2, "expected; band = 5th to 95th", fontsize=7.5, va="center", ha="left", color=S.INK2, clip_on=False)
ax.text(X, 47.3, "percentile (47.5 to 53.5)", fontsize=7.5, va="center", ha="left", color=S.INK2, clip_on=False)
ax.text(X, 42.0, "Unverified first  42.0", **lab)

# where order cannot matter
ax.annotate("At 1 and 2 samples every order\nscores the same: no test output\nhas more than two candidates",
            xy=(1.5, 41.4), xytext=(1.55, 55.6), fontsize=7.5, color=S.INK2,
            ha="center", va="center",
            arrowprops=dict(arrowstyle="-", color=S.MUTED, lw=0.6, shrinkA=2, shrinkB=3))

# crowded counts under the tick labels (Table 8, last column)
to_fig = lambda k: (L + (k - 0.8) / (4.2 - 0.8) * PW) / W
for k, c in zip(K, CROWDED):
    fig.text(to_fig(k), 0.98 / H, str(c), ha="center", va="top", fontsize=7.5, color=S.INK2)
fig.text(to_fig(0.8) - 0.05 / W, 0.98 / H, "Crowded", ha="right", va="top", fontsize=7.5, color=S.INK2)

S.save(fig, "fig3_ranking_budget")
