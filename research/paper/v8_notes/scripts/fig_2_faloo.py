"""Figure 2: FA-LOO as a flow (top) and the proof's table L(a,b) for n = 3 (bottom).

Notation follows research/paper/v8/paper.md, Sections 5.1-5.2: Z_i = (x_i, y_i),
fold M_i = A({Z_j: j<=n, j!=i}, {x_i, x_{n+1}}, xi_i); checks (a), (b), (c);
M_ab fitted on all pairs but a and b; L(a,b) = 1 if M_ab mispredicts y_a;
E_a: L(a,b) = 1 and L(b,a) = 0 for every b != a. The real fold M_i is M_{i,n+1}.
Cell values off the highlighted row and column are illustrative, not data.
"""
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle

import fig_style as S

S.setup()

W, H = 16.0, 10.0
fig = plt.figure(figsize=(W * S.CM, H * S.CM))
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, W)
ax.set_ylim(0, H)
ax.set_aspect("equal")
ax.axis("off")

FS = 8
LINE = 0.37  # cm between text lines at 8 pt


def mid(a, b):
    return (a + b) / 2


def box(x0, y0, x1, y1, fc=S.SURFACE, ec=S.AXIS, lw=0.8, z=2):
    ax.add_patch(FancyBboxPatch((x0, y0), x1 - x0, y1 - y0,
                                boxstyle="round,pad=0,rounding_size=0.12",
                                fc=fc, ec=ec, lw=lw, zorder=z))


def lines(x, y_mid, items, ha="center", color=S.INK, step=LINE):
    """items: list of (text, weight); block centred vertically on y_mid."""
    y_top = y_mid + (len(items) - 1) * step / 2
    for k, (t, wt) in enumerate(items):
        ax.text(x, y_top - k * step, t, ha=ha, va="center", fontsize=FS,
                fontweight=wt, color=color, zorder=5)


def arrow(x0, y0, x1, y1, color=S.INK2):
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="-|>",
                                 mutation_scale=7, lw=0.8, color=color,
                                 shrinkA=0, shrinkB=0, zorder=3))


def seg(xs, ys, color=S.INK2, lw=0.8):
    ax.plot(xs, ys, color=color, lw=lw, solid_capstyle="butt", zorder=3)


# =========================================================== top: the rule
ax.text(0.15, 9.85, "FA-LOO on one task", ha="left", va="top",
        fontsize=FS + 1, fontweight="bold")

# check boxes (a), (b), (c), stacked
CX0, CX1 = 7.75, 12.55
CH, CG = 1.22, 0.18
cy = {}
top = 9.15
for key in ("a", "b", "c"):
    cy[key] = (top - CH, top)
    top -= CH + CG
YB, YT = cy["c"][0], cy["a"][1]          # extent of the check column

checks = {
    "a": [("(a) every fold predicts", "bold"), ("its held-out demonstration", "bold"),
          (r"$M_i(x_i)=y_i$ for every $i\leq n$", "normal")],
    "b": [("(b) all folds agree on the test", "bold"),
          (r"$M_i(x_{n+1})=\hat{y}$ for every $i\leq n$", "normal")],
    "c": [("(c) full-data answer matches", "bold"),
          (r"the full run also outputs $\hat{y}$", "normal"), ("(optional)", "normal")],
}
for key, (y0, y1) in cy.items():
    box(CX0, y0, CX1, y1)
    lines(mid(CX0, CX1), mid(y0, y1), checks[key])

# task box
TX0, TX1 = 0.15, 2.2
box(TX0, YB, TX1, YT)
lines(mid(TX0, TX1), mid(YB, YT), [
    ("One task", "bold"), ("demonstrations", "normal"),
    (r"$Z_i=(x_i,y_i)$, $i\leq n$", "normal"), ("", "normal"),
    ("test input", "normal"), (r"$x_{n+1}$", "normal"),
])

# folds (stacked look) spanning (a) and (b); full run level with (c)
FX0, FX1 = 2.75, 7.15
fy0, fy1 = cy["b"][0], cy["a"][1]
for d in (0.16, 0.08):
    box(FX0 + d, fy0 + d, FX1 + d, fy1 - 0.16 + d, lw=0.6, z=1)
box(FX0, fy0, FX1, fy1 - 0.16)
lines(mid(FX0, FX1), mid(fy0, fy1 - 0.16), [
    (r"$n$ folds, $i=1,\dots,n$", "bold"),
    (r"fit without $Z_i$; predict $x_i$ and $x_{n+1}$", "normal"),
    ("", "normal"),
    (r"$M_i=A(\{Z_j:\ j\leq n,\ j\neq i\},\ \{x_i,x_{n+1}\},\ \xi_i)$", "normal"),
])
gy0, gy1 = cy["c"]
box(FX0, gy0, FX1, gy1)
lines(mid(FX0, FX1), mid(gy0, gy1), [
    ("Full run", "bold"),
    (r"fit on all $n$ demonstrations", "normal"),
    (r"predict $x_{n+1}$", "normal"),
])

# arrows: task -> folds, task -> full run; folds -> (a), (b); full -> (c)
arrow(TX1, mid(fy0, fy1 - 0.16), FX0, mid(fy0, fy1 - 0.16))
arrow(TX1, mid(gy0, gy1), FX0, mid(gy0, gy1))
arrow(FX1 + 0.16, mid(*cy["a"]), CX0, mid(*cy["a"]))
arrow(FX1 + 0.16, mid(*cy["b"]), CX0, mid(*cy["b"]))
arrow(FX1, mid(*cy["c"]), CX0, mid(*cy["c"]))

# bracket gathering the checks, then the decision
BX = 12.85
ya, yc_ = mid(*cy["a"]), mid(*cy["c"])
for key in ("a", "b", "c"):
    seg([CX1, BX], [mid(*cy[key])] * 2)
seg([BX, BX], [yc_, ya])
yb = mid(*cy["b"])
OX0, OX1 = 13.65, 15.85
ans = (yb + 0.95 - 0.36, yb + 0.95 + 0.36)
abst = (yb - 0.95 - 0.36, yb - 0.95 + 0.36)
box(OX0, ans[0], OX1, ans[1], fc=S.BLUE_TINT, ec=S.BLUE, lw=1.0)
lines(mid(OX0, OX1), mid(*ans), [(r"Answer $\hat{y}$", "bold")])
box(OX0, abst[0], OX1, abst[1], fc=S.GREY_TINT, ec=S.AXIS)
lines(mid(OX0, OX1), mid(*abst), [("Abstain", "bold")])
seg([BX, BX + 0.38], [yb, yb])
ax.add_patch(FancyArrowPatch((BX + 0.38, yb), (OX0, mid(*ans)), arrowstyle="-|>",
                             connectionstyle="angle,angleA=90,angleB=180,rad=0",
                             mutation_scale=7, lw=0.8, color=S.INK2, shrinkA=0, shrinkB=0, zorder=3))
ax.add_patch(FancyArrowPatch((BX + 0.38, yb), (OX0, mid(*abst)), arrowstyle="-|>",
                             connectionstyle="angle,angleA=-90,angleB=180,rad=0",
                             mutation_scale=7, lw=0.8, color=S.INK2, shrinkA=0, shrinkB=0, zorder=3))
ax.text(mid(OX0, OX1), ans[1] + 0.08, "all three pass", ha="center", va="bottom",
        fontsize=7.5, color=S.INK2)
ax.text(mid(OX0, OX1), abst[0] - 0.08, "any check fails", ha="center", va="top",
        fontsize=7.5, color=S.INK2)

# divider
seg([0.15, 15.85], [4.95, 4.95], color=S.GRID, lw=0.6)

# =========================================================== bottom: the proof
ax.text(0.15, 4.72, r"Why at most one pair in $n+1$ can give a confident error ($n=3$; pair 4 is the test)",
        ha="left", va="top", fontsize=FS + 1, fontweight="bold")

GX0, GY1, CS, N1 = 2.05, 3.42, 0.66, 4
vals = {(1, 2): 1, (1, 3): 1, (2, 1): 0, (2, 3): 1, (3, 1): 1, (3, 2): 0}  # illustrative
for a in range(1, N1 + 1):
    for b in range(1, N1 + 1):
        x, y = GX0 + (b - 1) * CS, GY1 - a * CS
        if a == b:
            ax.add_patch(Rectangle((x, y), CS, CS, fc=S.GREY_TINT, ec=S.SURFACE, lw=1.5, zorder=2))
            ax.text(x + CS / 2, y + CS / 2, "\u2013", ha="center", va="center",
                    fontsize=FS, color=S.MUTED, zorder=5)
            continue
        hi = (a == N1) or (b == N1)
        ax.add_patch(Rectangle((x, y), CS, CS, fc=S.BLUE_TINT if hi else S.SURFACE,
                               ec=S.SURFACE if hi else S.GRID, lw=1.5 if hi else 0.6, zorder=2))
        v = 1 if a == N1 else 0 if b == N1 else vals[(a, b)]
        ax.text(x + CS / 2, y + CS / 2, str(v), ha="center", va="center",
                fontsize=FS + 1 if hi else FS, fontweight="bold" if hi else "normal",
                color=S.INK if hi else S.MUTED, zorder=5)
ax.add_patch(Rectangle((GX0, GY1 - N1 * CS), (N1 - 1) * CS, CS, fc="none", ec=S.BLUE, lw=1.1, zorder=4))
ax.add_patch(Rectangle((GX0 + (N1 - 1) * CS, GY1 - (N1 - 1) * CS), CS, (N1 - 1) * CS,
                       fc="none", ec=S.BLUE, lw=1.1, zorder=4))
for k in range(1, N1 + 1):
    ax.text(GX0 + (k - 0.5) * CS, GY1 + 0.07, str(k), ha="center", va="bottom", fontsize=FS, color=S.INK2)
    ax.text(GX0 - 0.10, GY1 - (k - 0.5) * CS, str(k), ha="right", va="center", fontsize=FS, color=S.INK2)
ax.text(GX0 + (N1 - 0.5) * CS, GY1 - N1 * CS - 0.07, "test", ha="center", va="top", fontsize=7.5, color=S.INK2)
ax.text(GX0 - 0.36, GY1 - (N1 - 0.5) * CS, "test", ha="right", va="center", fontsize=7.5, color=S.INK2)
ax.text(GX0 + N1 * CS / 2, GY1 + 0.07 + LINE + 0.02, r"$b$: other pair held out",
        ha="center", va="bottom", fontsize=FS, color=S.INK2)
ax.text(0.55, GY1 - N1 * CS / 2, r"$a$: pair scored", ha="center", va="center",
        fontsize=FS, color=S.INK2, rotation=90)

TX = 5.55
lines(TX, GY1 - N1 * CS / 2 + 0.05, [
    (r"$M_{ab}$ is fitted on all pairs but $a$ and $b$ and predicts both;  $L(a,b)=1$ if it misses $y_a$.", "normal"),
    (r"The real fold $M_i$ is $M_{i4}$; every other model exists only for the argument.", "normal"),
    ("", "normal"),
    (r"Highlighted: event $E_4$, the only way FA-LOO can answer wrongly.", "normal"),
    (r"Column 4 all 0 is check (a);  row 4 all 1 is check (b) with $\hat{y}\neq y_4$.", "normal"),
    (r"$E_4$ puts a 0 in every other row (row 1 would be all 1 but for it), so no $E_a$ with", "normal"),
    (r"$a\neq 4$ can occur with it. Under (S), (F) and (E) the four events are equally likely,", "normal"),
    (r"so $P(E_4)\leq 1/(n+1)=1/4$.", "normal"),
], ha="left")

S.save(fig, "fig2_faloo")
