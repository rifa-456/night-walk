from engine.servers.physics.storage.body import BodyStorage
from engine.servers.physics.storage.shape import ShapeStorage
from engine.servers.physics.storage.space import SpaceStorage


class PhysicsServer3DStorage(BodyStorage, ShapeStorage, SpaceStorage):
    """
    Combined storage for physics server.
    """

    def __init__(self):
        BodyStorage.__init__(self)
        ShapeStorage.__init__(self)
        SpaceStorage.__init__(self)

    def free_rid(self, rid):
        """
        Free any type of RID.

        Determines type and calls appropriate free method.
        """
        if rid in self._bodies:
            body_data = self._bodies[rid]
            if body_data.space and body_data.space in self._spaces:
                space_data = self._spaces[body_data.space]
                space_data.body_rids.discard(rid)
                if space_data.space_3d:
                    space_data.space_3d.remove_body(rid)

            del self._bodies[rid]

        elif rid in self._shapes:
            self._free_shape(rid)

        elif rid in self._spaces:
            self._free_space(rid)
