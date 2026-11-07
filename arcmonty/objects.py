"""Object segmentation and object-centric reference frames (D8 pose canonicalisation) for ARC grids."""
import numpy as np
from scipy.ndimage import label

_S4 = np.ones((3, 3), dtype=int)
_S4[0, 0] = _S4[0, 2] = _S4[2, 0] = _S4[2, 2] = 0
_S8 = np.ones((3, 3), dtype=int)


def background(grid):
    vals, counts = np.unique(grid, return_counts=True)
    return int(vals[np.argmax(counts)])


class Obj:
    __slots__ = ("cells", "y0", "x0", "patch", "mask", "color", "pose", "canon", "key_shape")

    def __init__(self, grid, ys, xs):
        self.y0, self.x0 = int(ys.min()), int(xs.min())
        h, w = int(ys.max()) - self.y0 + 1, int(xs.max()) - self.x0 + 1
        self.mask = np.zeros((h, w), dtype=bool)
        self.mask[ys - self.y0, xs - self.x0] = True
        self.patch = np.where(self.mask, grid[self.y0:self.y0 + h, self.x0:self.x0 + w], -1).astype(np.int16)
        self.cells = (ys, xs)
        cols = np.unique(grid[ys, xs])
        self.color = int(cols[0]) if len(cols) == 1 else -1
        # canonical pose: the D8 transform giving the lexicographically smallest (shape, mask) encoding
        best = None
        for k in range(8):
            m = d8(self.mask, k)
            enc = (m.shape, m.tobytes())
            if best is None or enc < best[0]:
                best = (enc, k)
        self.pose = best[1]
        self.key_shape = best[0]
        self.canon = d8(self.patch, self.pose)

    @property
    def size(self):
        return int(self.mask.sum())

    @property
    def holes(self):
        """Number of enclosed background regions inside the object (topology)."""
        from scipy.ndimage import binary_fill_holes, label as _label
        inner = binary_fill_holes(self.mask) & ~self.mask
        return int(_label(inner)[1]) if inner.any() else 0

    @property
    def symmetric(self):
        m = self.mask
        return bool((m == m[:, ::-1]).all() or (m == m[::-1]).all())


def d8(a, k):
    a = a.T if k >= 4 else a
    return np.rot90(a, k % 4)


_MAPS = {}


def d8_coord_map(k, h, w):
    """Affine map (y, x) -> (y', x') consistent with d8(patch_of_shape_(h, w), k), valid for any integer point."""
    key = (k, h, w)
    if key not in _MAPS:
        P = np.arange(h * w).reshape(h, w)
        Q = d8(P, k)
        oy, ox = [int(v[0]) for v in np.nonzero(Q == 0)]
        P3 = np.arange(9).reshape(3, 3)
        Q3 = d8(P3, k)
        a0 = np.array([int(v[0]) for v in np.nonzero(Q3 == 0)])
        ax = np.array([int(v[0]) for v in np.nonzero(Q3 == 1)]) - a0  # image of unit x step
        ay = np.array([int(v[0]) for v in np.nonzero(Q3 == 3)]) - a0  # image of unit y step
        A = np.stack([ay, ax], axis=1)  # columns: images of (1,0) and (0,1)
        _MAPS[key] = (A, np.array([oy, ox]))
    return _MAPS[key]


def to_frame(obj, ys, xs):
    """Absolute grid coords -> coords in the object's canonical frame."""
    h, w = obj.mask.shape
    A, o = d8_coord_map(obj.pose, h, w)
    rel = np.stack([np.asarray(ys) - obj.y0, np.asarray(xs) - obj.x0])
    out = A @ rel + o[:, None]
    return out[0], out[1]


def from_frame(obj, us, vs):
    """Canonical-frame coords -> absolute grid coords (inverse of to_frame)."""
    h, w = obj.mask.shape
    A, o = d8_coord_map(obj.pose, h, w)
    Ainv = np.round(np.linalg.inv(A)).astype(int)
    rel = Ainv @ (np.stack([np.asarray(us), np.asarray(vs)]) - o[:, None])
    return rel[0] + obj.y0, rel[1] + obj.x0


def segment(grid, mode="color8", bg=None):
    """mode: color4 / color8 (single-colour components) or multi8 (multi-colour non-background components)."""
    bg = background(grid) if bg is None else bg
    objs = []
    if mode.startswith("color"):
        st = _S4 if mode == "color4" else _S8
        for c in np.unique(grid):
            if c == bg:
                continue
            lab, n = label(grid == c, structure=st)
            for i in range(1, n + 1):
                ys, xs = np.nonzero(lab == i)
                objs.append(Obj(grid, ys, xs))
    else:
        lab, n = label(grid != bg, structure=_S8)
        for i in range(1, n + 1):
            ys, xs = np.nonzero(lab == i)
            objs.append(Obj(grid, ys, xs))
    return objs
