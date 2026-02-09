from typing import Dict, Set
from engine.core.rid import RID


class SpaceStorage:
    class SpaceData:
        def __init__(self, rid: RID, shape_storage):
            from engine.servers.physics.spaces.space_3d import Space3D

            self.space_3d = Space3D(rid, shape_storage)
            self.body_rids: set[RID] = set()
            self.area_rids: set[RID] = set()

    def __init__(self):
        self._spaces: Dict[RID, SpaceStorage.SpaceData] = {}
        self._active_spaces: Set[RID] = set()
        self._next_space_id: int = 1

    def space_create(self) -> RID:
        """
        Create a physics space and return a valid RID.
        """
        rid = RID()
        rid._assign(self._next_space_id)
        self._next_space_id += 1
        self._spaces[rid] = self.SpaceData(rid, self)
        return rid

    def space_set_active(self, space: RID, active: bool):
        if space not in self._spaces:
            return

        if active:
            self._active_spaces.add(space)
        else:
            self._active_spaces.discard(space)

    def space_get_direct_state(self, space: RID):
        if space not in self._spaces:
            return None
        return self._spaces[space].space_3d.get_direct_state()

    def _get_space_3d(self, space_rid: RID):
        if space_rid not in self._spaces:
            return None
        return self._spaces[space_rid].space_3d

    def _free_space(self, rid: RID):
        if rid in self._spaces:
            space_data = self._spaces[rid]
            space_data.space_3d.bodies.clear()
            space_data.space_3d.areas.clear()
            space_data.space_3d.broadphase.clear()

            del self._spaces[rid]
            self._active_spaces.discard(rid)
