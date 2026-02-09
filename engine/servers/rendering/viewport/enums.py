from enum import IntEnum


class ViewportUpdateMode(IntEnum):
    UPDATE_DISABLED = 0
    UPDATE_ONCE = 1
    UPDATE_WHEN_VISIBLE = 2
    UPDATE_WHEN_PARENT_VISIBLE = 3
    UPDATE_ALWAYS = 4


class ViewportClearMode(IntEnum):
    CLEAR_ALWAYS = 0
    CLEAR_NEVER = 1
    CLEAR_ONCE = 2
