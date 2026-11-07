"""Cover image for the Kaggle Writeup (ARC Prize 2026, paper track): 1600 x 900 px, 16:9, 100 dpi.

Left: the title (any string, wrapped to fit; a colon splits it into a large head and a smaller tail),
a one-line subtitle, and the author and track at the bottom. Right: the held-out split for Qwen3.8-27B,
re-drawn from the Qwen rows of Figure 2 in the paper (fig1_heldout_split.png), same colours and marks.

Every plotted number is copied from research/paper/v8/paper.md, Table C9 (Qwen3.8-27B rows; all
planned, so all marks are filled). Nothing is recomputed.

Usage (from the project root):
  .venv/bin/python research/paper/v8_notes/scripts/make_cover_v8.py
  .venv/bin/python research/paper/v8_notes/scripts/make_cover_v8.py --title "Any Title: With a Tail" \
      --subtitle "One line under it." --out research/paper/figures/cover_v8.png
"""
import argparse
import os
import shlex
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.font_manager import FontProperties, findfont  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

ROOT = Path(__file__).resolve().parents[4]
DEFAULT_OUT = ROOT / "research" / "paper" / "figures" / "cover_v8.png"
DEFAULT_TITLE = ("Verified Is Not Generalised: Held-Out Re-Induction, a Distribution-Free Bound, "
                 "and Where ARC Solvers Fail")
DEFAULT_SUBTITLE = "A program that fits every demonstration can still be a proxy."
AUTHOR = "Abdur Rahim"
TRACK = "ARC Prize 2026, paper track"

# Tokens shared with the paper's figures (fig_style.py).
SURFACE = "#fcfcfb"
INK, INK2, MUTED = "#0b0b0b", "#52514e", "#898781"
GRID, AXIS = "#e1e0d9", "#c3c2b7"
BLUE, ORANGE = "#2a78d6", "#eb6834"

# Table C9, Qwen3.8-27B rows: (set, mono label?, between (pt, lo, hi), within (pt, lo, hi), tasks).
ROWS = [
    ("ARC-AGI-2", False, (66.0, 53.6, 77.9), (37.5, 11.0, 61.8), 17),
    ("ConceptARC", False, (48.7, 41.3, 56.3), (36.7, 26.5, 46.9), 49),
    ("ConceptARC, 1 input", False, (47.6, 37.9, 57.1), (41.0, 27.6, 54.5), 52),
    ("re-arc", True, (54.3, 40.8, 66.9), (28.6, 9.7, 47.4), 42),
]

W_PX, H_PX, DPI = 1600, 900, 100


def serif(italic=False):
    """STIX Two Text (macOS system font), else DejaVu Serif."""
    fname = "/System/Library/Fonts/Supplemental/STIXTwoText%s.ttf" % ("-Italic" if italic else "")
    if os.path.exists(fname):
        return FontProperties(fname=fname)
    return FontProperties(family="DejaVu Serif", style="italic" if italic else "normal")


def sans(**kw):
    try:
        findfont(FontProperties(family="Arial"), fallback_to_default=False)
        return FontProperties(family="Arial", **kw)
    except ValueError:
        return FontProperties(family="DejaVu Sans", **kw)


def text_width_px(fig, s, fp, size):
    r = fig.canvas.get_renderer()
    t = fig.text(0, 0, s, fontproperties=fp, fontsize=size)
    w = t.get_window_extent(renderer=r).width
    t.remove()
    return w


def wrap(fig, s, fp, size, max_w):
    """Greedy wrap by measured width; a single over-long word gets its own line."""
    lines, cur = [], ""
    for word in s.split():
        trial = (cur + " " + word).strip()
        if cur and text_width_px(fig, trial, fp, size) > max_w:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines


def fit_title(fig, title, box_w, box_h):
    """Split at the first colon into head and tail; shrink both until they fit the box."""
    if ":" in title:
        head, tail = title.split(":", 1)
        head, tail = head.strip() + ":", tail.strip()
    else:
        head, tail = title.strip(), ""
    fp = serif()
    for size in range(60, 17, -1):
        tail_size = round(size * 0.66)
        hl = wrap(fig, head, fp, size, box_w)
        tl = wrap(fig, tail, fp, tail_size, box_w) if tail else []
        h = len(hl) * size * 1.18 * DPI / 72 + (len(tl) * tail_size * 1.25 * DPI / 72 + 0.45 * size * DPI / 72 if tl else 0)
        widest = max([text_width_px(fig, l, fp, size) for l in hl] + [text_width_px(fig, l, fp, tail_size) for l in tl])
        if h <= box_h and widest <= box_w and len(hl) <= (3 if tail else 5):
            return size, hl, tail_size, tl
    return size, hl, tail_size, tl


def px(x, y):
    """Figure coordinates from pixels measured from the top-left corner."""
    return x / W_PX, 1 - y / H_PX


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--title", default=DEFAULT_TITLE)
    ap.add_argument("--subtitle", default=DEFAULT_SUBTITLE)
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    a = ap.parse_args()

    fig = plt.figure(figsize=(W_PX / DPI, H_PX / DPI), dpi=DPI)
    fig.patch.set_facecolor(SURFACE)
    fig.canvas.draw()

    # ---- Left column: title, subtitle, byline -------------------------------------------
    LX, LW = 84, 700           # left edge and width of the text column, px
    TOP = 96                   # top of the title block, px
    TITLE_BOX_H = 520
    size, hl, tsize, tl = fit_title(fig, a.title, LW, TITLE_BOX_H)
    fp = serif()
    y = TOP
    for line in hl:
        fig.text(*px(LX, y), line, fontproperties=fp, fontsize=size, color=INK, va="top", ha="left")
        y += size * 1.18 * DPI / 72
    if tl:
        y += 0.45 * size * DPI / 72
        for line in tl:
            fig.text(*px(LX, y), line, fontproperties=fp, fontsize=tsize, color=INK2, va="top", ha="left")
            y += tsize * 1.25 * DPI / 72

    # Subtitle: one line; shrink to fit the column if needed.
    sub_fp = serif(italic=True)
    sub_size = 22
    while sub_size > 12 and text_width_px(fig, a.subtitle, sub_fp, sub_size) > LW:
        sub_size -= 1
    y += 34
    fig.add_artist(Line2D([LX / W_PX, (LX + 72) / W_PX], [1 - y / H_PX] * 2, color=BLUE, lw=3,
                          transform=fig.transFigure))
    y += 26
    fig.text(*px(LX, y), a.subtitle, fontproperties=sub_fp, fontsize=sub_size, color=INK2, va="top", ha="left")

    # Byline at the bottom.
    fig.text(*px(LX, H_PX - 92), AUTHOR, fontproperties=sans(weight="bold"), fontsize=17, color=INK,
             va="bottom", ha="left")
    fig.text(*px(LX, H_PX - 62), TRACK, fontproperties=sans(), fontsize=14, color=INK2, va="bottom", ha="left")

    # ---- Right column: the held-out split, Qwen rows -------------------------------------
    RX, RW = 1062, 460         # plot area (axes) left edge and width, px; labels sit to its left
    RT, RH = 300, 380          # axes top and height, px
    fig.text(*px(RX - 196, RT - 140), "The held-out split, Qwen3.8-27B", fontproperties=sans(weight="bold"),
             fontsize=17, color=INK, va="top", ha="left")
    fig.text(*px(RX - 196, RT - 106),
             "Right on the test: fold programs that predict their held-out\n"
             "demonstration minus those that miss it, points, 95% intervals",
             fontproperties=sans(), fontsize=12.5, color=INK2, va="top", ha="left", linespacing=1.35)

    ax = fig.add_axes([RX / W_PX, 1 - (RT + RH) / H_PX, RW / W_PX, RH / H_PX])
    ax.set_facecolor(SURFACE)
    ax.set_xlim(-5, 100)
    ax.set_ylim(len(ROWS) - 0.5, -0.5)
    for x in (25, 50, 75, 100):
        ax.axvline(x, color=GRID, lw=0.9, zorder=0)
    ax.axvline(0, color=INK2, lw=1.2, zorder=1)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(AXIS)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.tick_params(axis="x", colors=AXIS, labelcolor=INK2, labelsize=13, length=4)
    ax.tick_params(axis="y", length=0, pad=10)
    ax.set_yticks(range(len(ROWS)))
    ax.set_yticklabels([r[0] for r in ROWS], fontsize=14, color=INK)
    for lab, r in zip(ax.get_yticklabels(), ROWS):
        lab.set_fontfamily("DejaVu Sans Mono" if r[1] else sans().get_family()[0])
    OFF, MS = 0.17, 10
    for i, (_, _, b, w, _) in enumerate(ROWS):
        for (pt, lo, hi), dy, col, mk in ((b, -OFF, BLUE, "o"), (w, OFF, ORANGE, "D")):
            ax.plot([lo, hi], [i + dy] * 2, color=col, lw=3, solid_capstyle="butt", zorder=2)
            ax.plot([pt], [i + dy], marker=mk, ms=MS if mk == "o" else MS * 0.9, mfc=col, mec=col, ls="none",
                    zorder=3)
    handles = [Line2D([0], [0], color=BLUE, lw=3, marker="o", ms=MS, mfc=BLUE, mec=BLUE),
               Line2D([0], [0], color=ORANGE, lw=3, marker="D", ms=MS * 0.9, mfc=ORANGE, mec=ORANGE)]
    fig.legend(handles, ["Between tasks", "Within a task"], loc="upper left",
               bbox_to_anchor=px(RX - 196, RT + RH + 52), ncol=2, frameon=False, prop=sans(size=13),
               handlelength=2.0, columnspacing=1.8, handletextpad=0.6, borderaxespad=0)

    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=DPI, facecolor=SURFACE)
    print(f"wrote {out} (title {size} pt in {len(hl)}+{len(tl)} lines; subtitle {sub_size} pt)")
    script = os.path.relpath(__file__, ROOT)
    print("re-run with another title (from the project root):")
    print(f"  .venv/bin/python {script} --title {shlex.quote(a.title)}"
          f" --subtitle {shlex.quote(a.subtitle)} --out {shlex.quote(os.path.relpath(out, ROOT))}")


if __name__ == "__main__":
    sys.exit(main())
