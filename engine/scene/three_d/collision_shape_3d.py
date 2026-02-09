from engine.scene.three_d.node_3d import Node3D
from engine.core.rid import RID
from engine.logger import Logger


class CollisionShape3D(Node3D):
    """
    Godot CollisionShape3D.
    """

    def __init__(self):
        super().__init__()
        self.shape: RID | None = None
        self._parent_body = None

    def _enter_tree(self):
        super()._enter_tree()
        self._register_shape()

    def _exit_tree(self):
        if self._parent_body:
            self._parent_body = None
        super()._exit_tree()

    def _register_shape(self):
        parent = self.get_parent()
        if not parent:
            Logger.warn(
                f"CollisionShape3D '{self.name}' has no parent", "CollisionShape3D"
            )
            return

        if not hasattr(parent, "_add_shape"):
            Logger.warn(
                f"CollisionShape3D '{self.name}' parent '{parent.name}' "
                f"is not a CollisionObject3D",
                "CollisionShape3D",
            )
            return

        if not self.shape:
            Logger.error(
                f"CollisionShape3D '{self.name}' has no shape assigned. "
                f"Set shape property before adding to tree.",
                "CollisionShape3D",
            )
            return

        if not self.shape.is_valid():
            Logger.error(
                f"CollisionShape3D '{self.name}' has invalid shape RID. "
                f"Shape resource may not have initialized properly.",
                "CollisionShape3D",
            )
            return

        self._parent_body = parent
        parent._add_shape(self.shape)

        Logger.debug(
            f"CollisionShape3D '{self.name}' registered shape RID {self.shape.get_id()} "
            f"with parent '{parent.name}'",
            "CollisionShape3D",
        )
