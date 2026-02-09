from typing import Dict, Any, Optional
from engine.core.rid import RID


class ShapeStorage:
    class ShapeData:
        def __init__(self, shape_type: int):
            self.type = shape_type
            self.data: Any = None

    def __init__(self):
        self._shapes: Dict[RID, ShapeStorage.ShapeData] = {}
        self._next_shape_id: int = 1

    def shape_create(self, shape_type: int) -> RID:
        """
        Create a collision shape and return a valid RID.
        """
        rid = RID()
        rid._assign(self._next_shape_id)
        self._next_shape_id += 1
        self._shapes[rid] = self.ShapeData(shape_type)
        return rid

    def shape_set_data(self, shape: RID, data: Any):
        if shape in self._shapes:
            self._shapes[shape].data = data

    def shape_get_data(self, shape: RID) -> Any:
        if shape in self._shapes:
            return self._shapes[shape].data
        return None

    def shape_get_type(self, shape: RID) -> int:
        return self._shapes[shape].type

    def _free_shape(self, shape: RID):
        if shape in self._shapes:
            del self._shapes[shape]

    def _get_shape_data(self, shape: RID) -> Optional["ShapeStorage.ShapeData"]:
        """
        Get shape data by RID.

        Args:
            shape: Shape RID

        Returns:
            ShapeData or None if not found
        """
        return self._shapes.get(shape)
