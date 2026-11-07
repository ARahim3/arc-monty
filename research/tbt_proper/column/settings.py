"""All settings. One list of columns for every task of every kind; arms are switches on it. Fixed before any test data."""
SENSORS = ("color", "mask", "objc", "obj", "objn", "near", "nearc", "nears", "nearsc")
REACH = (1, 2, 3, 6)
CELL_SENSORS = ("color", "mask")
POSES, POSE_REACH = 8, (1, 2, 3)  # cell-level columns also come in a form that reads the query in all eight poses of the grid
POSED = [dict(kind=s, reach=r, poses=POSES) for s in CELL_SENSORS for r in POSE_REACH]
CONFIGS = [dict(kind=s, reach=r) for s in SENSORS for r in REACH] + POSED
COUNT_SENSOR = "objn"
NEAR_SENSORS = ("near", "nearc", "nears", "nearsc")
BUDGET = 600  # seconds per static task, folds included; a task over budget gets no answer
WORKERS = 4

_of = lambda kinds, reach=REACH: [dict(kind=k, reach=r) for k in kinds for r in reach]
LOCAL = _of(CELL_SENSORS) + POSED
TOP = (REACH[-1],)
GAME_ARMS = {
    "full": dict(configs=CONFIGS, rollouts=True),
    "nomotor": dict(configs=CONFIGS, common=dict(motor=False)),
    "colour_only": dict(configs=CONFIGS, common=dict(displacement=False)),
    "local": dict(configs=LOCAL),
    "local+moving": dict(configs=LOCAL + _of(("color+moving",))),
    "local+near": dict(configs=LOCAL + _of(NEAR_SENSORS)),
    "single": dict(configs=_of(("color",), TOP)),
    "single+moving": dict(configs=_of(("color+moving",), TOP)),
    "single+near": dict(configs=_of(("color+nears",), TOP)),
    "local+library": dict(configs=LOCAL, library=True),
}
TUNING_GAMES = ("ar25", "bp35", "cd82", "g50t", "lp85", "ls20", "s5i5", "sc25", "sk48", "su15", "tr87", "vc33")
HORIZONS, ROLL_EVERY, STREAK = (2, 4, 8), 12, 3
LIBRARY_TRANSITIONS = 80  # per other game
E2_LIBRARY_SIZE = 9  # tasks: a concept's other tasks, or as many drawn from the other concepts

FRESH_HAND = ("arc-community", "nosound", "dbigham", "sequence")
FRESH_GEN = ("tama",)
SECONDARY = ("pqa",)
SPENT = ("concept", "mini", "oned")
SET_ORDER = FRESH_HAND + FRESH_GEN + SECONDARY + SPENT
WEAK_GROUPS = ("AboveBelow", "Count", "HorizontalVertical", "InsideOutside", "Order", "SameDifferent")
