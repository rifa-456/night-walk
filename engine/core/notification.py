from enum import IntEnum, auto


class Notification(IntEnum):
    # --- Object / Node lifecycle ---
    ENTER_TREE = auto()
    EXIT_TREE = auto()
    READY = auto()
    PAUSED = auto()
    UNPAUSED = auto()
    PHYSICS_PROCESS = auto()
    PROCESS = auto()

    # --- Rendering / Canvas ---
    DRAW = auto()
    ENTER_CANVAS = auto()
    EXIT_CANVAS = auto()
    VISIBILITY_CHANGED = auto()
    LOCAL_TRANSFORM_CHANGED = auto()
    ENTER_WORLD = auto()
    EXIT_WORLD = auto()

    # --- UI / Theme ---
    THEME_CHANGED = auto()
    RESIZED = auto()
    SORT_CHILDREN = auto()
    FOCUS_ENTER = auto()
    FOCUS_EXIT = auto()

    TRANSFORM_CHANGED = auto()

    WM_SIZE_CHANGED = auto()
