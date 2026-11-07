"""Shared visual system for the v8 paper figures.

One sans face (Arial) at 8-9 pt final size, hairline recessive axes, two
categorical hues (validated with the dataviz skill's validate_palette.js on
white: CVD dE 24.7, normal dE 33.6, both >= 3:1), neutrals for references.
Figures are drawn at final print size in cm, so include them at 100% width.
"""
from pathlib import Path

import matplotlib as mpl

OUT = Path(__file__).resolve().parents[2] / "figures"

CM = 1 / 2.54

# Colour tokens (light, print). Text never wears a series colour.
SURFACE = "#ffffff"
INK = "#0b0b0b"          # primary ink
INK2 = "#52514e"         # secondary ink
MUTED = "#898781"        # axis labels, notes
GRID = "#e1e0d9"         # hairline grid
AXIS = "#c3c2b7"         # baseline / axis
BLUE = "#2a78d6"         # categorical slot 1
ORANGE = "#eb6834"       # categorical slot 2
BLUE_TINT = "#e3eefb"    # 12% blue on white, for highlighted cells/boxes
GREY_TINT = "#f3f2ef"    # neutral box fill
BAND = "#d9d8d2"         # neutral range band

MONO = "DejaVu Sans Mono"


def setup():
    mpl.rcParams.update({
        "font.family": "Arial",
        "font.size": 8,
        "axes.titlesize": 9,
        "axes.labelsize": 8,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "legend.fontsize": 8,
        "text.color": INK,
        "axes.labelcolor": INK2,
        "axes.edgecolor": AXIS,
        "axes.linewidth": 0.6,
        "xtick.color": AXIS,
        "ytick.color": AXIS,
        "xtick.labelcolor": INK2,
        "ytick.labelcolor": INK,
        "xtick.major.width": 0.6,
        "ytick.major.width": 0.6,
        "xtick.major.size": 2.5,
        "ytick.major.size": 0,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
        "savefig.facecolor": SURFACE,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "svg.fonttype": "path",
        "mathtext.fontset": "custom",
        "mathtext.rm": "Arial",
        "mathtext.it": "Arial:italic",
        "mathtext.bf": "Arial:bold",
        "mathtext.sf": "Arial",
        "mathtext.fallback": "stixsans",
    })


def save(fig, stem):
    OUT.mkdir(parents=True, exist_ok=True)
    for ext, kw in (("png", {"dpi": 300}), ("pdf", {}), ("svg", {})):
        fig.savefig(OUT / f"{stem}.{ext}", **kw)
    print("wrote", *(OUT / f"{stem}.{e}" for e in ("png", "pdf", "svg")))
