from typing import Optional


class RID:
    """
    Resource ID.
    """

    __slots__ = ("_id",)

    _next_id: int = 1

    def __init__(self, from_rid: Optional["RID"] = None):
        if from_rid is not None:
            self._id = from_rid._id
        else:
            self._id = RID._next_id
            RID._next_id += 1

    def is_valid(self) -> bool:
        return self._id != 0

    def get_id(self) -> int:
        return self._id

    def _assign(self, new_id: int) -> None:
        self._id = new_id

    def __bool__(self):
        return self.is_valid()

    def __eq__(self, other):
        return isinstance(other, RID) and self._id == other._id

    def __lt__(self, other):
        return self._id < other._id

    def __le__(self, other):
        return self._id <= other._id

    def __gt__(self, other):
        return self._id > other._id

    def __ge__(self, other):
        return self._id >= other._id

    def __hash__(self):
        return hash(self._id)

    def __repr__(self):
        return f"RID({self._id})"