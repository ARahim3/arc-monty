"""Figure 1: the held-out split across four learners (Table 3 rows, values of Table C9).

Every number below is copied from research/paper/v8/paper.md, Table C9
(Appendix C); the row list and post hoc marks follow Table 3 and the C9
daggers; `ns` follows Table 3. Nothing is recomputed.
v8c: Qwen's one-input ConceptARC row added (Table 3 and C9; planned in
research/generator_control.md Addendum 4, item 3; recounted in v8c_qwen.txt section 4).
"""
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

import fig_style as S

S.setup()

# (set label, mono?, between (pt, lo, hi, posthoc, ns), within (pt, lo, hi, tasks, posthoc, ns))
# lo/hi = None where Table C9 gives no interval.
PANELS = [
    ("Monty-ARC", [
        ("ConceptARC", False, (73.3, 59.0, 84.9, True, False), (43.6, 22.2, 64.7, 12, True, False)),
        ("Mini-ARC", False, (67.2, 47.7, 82.8, True, False), (21.2, -6.1, 50.0, 11, True, True)),
        ("1D-ARC", False, (69.6, 52.5, 80.8, True, False), (35.0, 9.5, 66.7, 20, True, False)),
        ("hand-made fresh", False, (70.6, 41.7, 89.5, False, False), (0.0, None, None, 3, False, True)),
        ("arc-dataset-tama", True, (84.7, 71.6, 94.7, False, False), (21.2, 8.0, 45.8, 24, False, False)),
        ("re-arc", True, (76.4, 62.2, 88.9, False, False), (50.0, 12.5, 87.5, 7, False, False)),
    ]),
    ("Qwen3.8-27B", [
        ("ARC-AGI-2", False, (66.0, 53.6, 77.9, False, False), (37.5, 11.0, 61.8, 17, False, False)),
        ("ConceptARC", False, (48.7, 41.3, 56.3, False, False), (36.7, 26.5, 46.9, 49, False, False)),
        ("ConceptARC, 1 input", False, (47.6, 37.9, 57.1, False, False), (41.0, 27.6, 54.5, 52, False, False)),
        ("re-arc", True, (54.3, 40.8, 66.9, False, False), (28.6, 9.7, 47.4, 42, False, False)),
    ]),
    ("2020 program", [
        ("ConceptARC", False, (45.0, 35.3, 54.6, False, False), (17.6, 8.2, 27.2, 52, True, False)),
        ("Mini-ARC", False, (59.3, 47.8, 69.8, False, False), (28.0, 15.2, 41.5, 47, True, False)),
        ("1D-ARC", False, (67.3, 55.4, 75.8, False, False), (46.6, 34.4, 57.5, 232, True, False)),
        ("MinimalTasks", False, (64.4, 44.6, 80.3, False, False), (23.8, 11.9, 35.7, 7, True, False)),
        ("ARC-AGI-2", False, (16.0, -0.6, 48.8, False, True), (6.2, 0.0, 18.8, 4, True, True)),
        ("re-arc", True, (51.8, 39.9, 63.0, False, False), (30.4, 18.4, 42.9, 56, False, False)),
    ]),
    ("One column", [
        ("hand-made fresh", False, (80.4, 62.4, 93.1, False, False), (53.7, 14.1, 88.9, 9, False, False)),
        ("arc-dataset-tama", True, (66.7, 41.2, 82.3, False, False), (4.4, -3.3, 12.7, 62, False, True)),
        ("PQA", False, (-0.8, -1.7, 0.0, False, True), (-1.1, -5.6, 0.0, 5, False, True)),
    ]),
]

# Layout in cm (drawn at final size: include at 16 cm width).
W, ROW = 16.0, 0.56
LABEL_W, PLOT_W = 2.95, 4.65
COL_X = [0.05 + LABEL_W, 0.05 + LABEL_W + PLOT_W + 0.45 + LABEL_W]
TOP_BAND, TITLE_H, TICK_H, GAP, BOTTOM = 1.05, 0.55, 0.45, 0.25, 0.75
rows_top, rows_bot = 6, 4
H = TOP_BAND + TITLE_H + rows_top * ROW + TICK_H + GAP + TITLE_H + rows_bot * ROW + TICK_H + BOTTOM

XMIN, XMAX = -10, 100
OFF = 0.19  # vertical offset of the two estimates within a row (row units)
MS = 4.6

fig = plt.figure(figsize=(W * S.CM, H * S.CM))


def axes_cm(x, y_top, w, h):
    """Axes from a top-left corner in cm."""
    return fig.add_axes([x / W, (H - y_top - h) / H, w / W, h / H])


def draw(ax, title, rows, slots):
    k = len(rows)
    ax.set_xlim(XMIN, XMAX)
    ax.set_ylim(slots - 0.5, -0.5)  # a panel with fewer rows than slots keeps the same row spacing
    ax.set_xticks([0, 25, 50, 75, 100])
    for x in (25, 50, 75, 100):
        ax.axvline(x, color=S.GRID, lw=0.5, zorder=0)
    ax.axvline(0, color=S.INK2, lw=0.8, zorder=1)
    ax.spines["left"].set_visible(False)
    ax.set_yticks(range(k))
    ax.set_yticklabels([r[0] for r in rows])
    for lab, r in zip(ax.get_yticklabels(), rows):
        if r[1]:
            lab.set_fontfamily(S.MONO)
    ax.tick_params(axis="y", pad=3)
    ax.text(-LABEL_W / PLOT_W * 0.985, 1.0 + 0.10 / (ROW * slots / 1.0) * 1.0, title,
            transform=ax.transAxes, ha="left", va="bottom", fontsize=9,
            fontweight="bold", color=S.INK)

    for i, (_, _, b, w) in enumerate(rows):
        # One shared `ns` when both intervals are ns and end at the same place.
        shared_ns = b[-1] and w[-1] and w[1] is not None and abs(b[2] - w[2]) < 8
        if shared_ns:
            ax.text(max(b[2], w[2]) + 2.6, i, "ns", fontsize=7.5, color=S.INK2,
                    va="center", ha="left")
        for est, dy, col, mk in ((b, -OFF, S.BLUE, "o"), (w, +OFF, S.ORANGE, "D")):
            pt, lo, hi = est[0], est[1], est[2]
            posthoc, ns = est[-2], est[-1]
            y = i + dy
            if lo is not None:
                ax.plot([lo, hi], [y, y], color=col, lw=1.4, solid_capstyle="butt", zorder=2)
            ax.plot([pt], [y], marker=mk, ms=MS if mk == "o" else MS * 0.9,
                    mfc=("white" if posthoc else col), mec=col, mew=1.1,
                    ls="none", zorder=3)
            if ns and not shared_ns:
                if lo is not None:
                    ax.text(hi + 2.6, y, "ns", fontsize=7.5, color=S.INK2,
                            va="center", ha="left")
                else:  # Table C9 gives a point but no interval
                    ax.text(pt + 4.5, y, f"ns ({est[3]} tasks, no interval)",
                            fontsize=7.5, color=S.INK2, va="center", ha="left")


y = TOP_BAND
ax_tl = axes_cm(COL_X[0], y + TITLE_H, PLOT_W, rows_top * ROW)
ax_tr = axes_cm(COL_X[1], y + TITLE_H, PLOT_W, rows_top * ROW)
y2 = y + TITLE_H + rows_top * ROW + TICK_H + GAP
ax_bl = axes_cm(COL_X[0], y2 + TITLE_H, PLOT_W, rows_bot * ROW)
ax_br = axes_cm(COL_X[1], y2 + TITLE_H, PLOT_W, rows_bot * ROW)

for ax, (title, rows), slots in zip((ax_tl, ax_bl, ax_tr, ax_br), PANELS, (rows_top, rows_bot, rows_top, rows_bot)):
    draw(ax, title, rows, slots)

fig.text(0.5, 0.12 / H,
         "Right on the test, in points: fold programs that predict their held-out "
         "demonstration minus those that miss it",
         ha="center", va="bottom", fontsize=8, color=S.INK2)

# Legend: colour + shape for the estimate, fill for planned vs post hoc.
handles = [
    Line2D([0], [0], color=S.BLUE, lw=1.4, marker="o", ms=MS, mfc=S.BLUE, mec=S.BLUE),
    Line2D([0], [0], color=S.ORANGE, lw=1.4, marker="D", ms=MS * 0.9, mfc=S.ORANGE, mec=S.ORANGE),
    Line2D([0], [0], color=S.INK2, lw=0, marker="o", ms=MS, mfc=S.INK2, mec=S.INK2),
    Line2D([0], [0], color=S.INK2, lw=0, marker="o", ms=MS, mfc="white", mec=S.INK2, mew=1.1),
]
labels = ["Between tasks", "Within a task (mean paired)", "Planned", "Post hoc"]
fig.legend(handles, labels, loc="upper left", bbox_to_anchor=(0.05 / W, 1 - 0.12 / H),
           ncol=4, frameon=False, handlelength=1.8, columnspacing=1.6, handletextpad=0.5,
           borderaxespad=0)
fig.text(0.05 / W, 1 - 0.66 / H,
         "Point and 95% interval. ns: interval reaches 0 (Table 3).",
         fontsize=7.5, color=S.INK2, ha="left", va="top")

S.save(fig, "fig1_heldout_split")
