from typing import Dict, List, Optional, Any, TYPE_CHECKING
from engine.core.rid import RID
from engine.math.datatypes.transform_3d import Transform3D
from engine.math.datatypes.vector3 import Vector3
from .enums import BodyStateEnums
from ..bodies.body_3d import Body3D
from ..enums import PhysicsServer3DEnums

if TYPE_CHECKING:
    from engine.servers.physics.storage.shape import ShapeStorage


class BodyStorage:
    class BodyData:
        def __init__(self):
            self.mode = PhysicsServer3DEnums.BODY_MODE_RIGID
            self.space: Optional[RID] = None
            self.transform = Transform3D()
            self.shapes: List[Dict] = []
            self.collision_layer = 1
            self.collision_mask = 1
            self.axis_lock = 0

            self.linear_velocity = Vector3()
            self.angular_velocity = Vector3()

            self.runtime_body: Optional[Body3D] = None

    def __init__(self):
        self._bodies: Dict[RID, BodyStorage.BodyData] = {}
        self._next_body_id: int = 1

    def body_create(self) -> RID:
        """
        Create a physics body and return a valid RID.
        """
        rid = RID()
        rid._assign(self._next_body_id)
        self._next_body_id += 1
        self._bodies[rid] = self.BodyData()
        return rid

    def body_set_space(self, body: RID, space: RID):
        """Set the space for a body - creates/destroys runtime Body3D"""
        if body not in self._bodies:
            return

        b_data = self._bodies[body]

        if b_data.space and b_data.space in self._spaces:
            old_space_data = self._spaces[b_data.space]
            old_space_data.body_rids.discard(body)

            if old_space_data.space_3d:
                old_space_data.space_3d.remove_body(body)

            b_data.runtime_body = None

        b_data.space = space

        if space and space in self._spaces:
            space_data = self._spaces[space]
            space_data.body_rids.add(body)

            if space_data.space_3d:
                from engine.servers.physics.bodies.body_3d import Body3D

                runtime_body = Body3D(body, space_data.space_3d, b_data.mode)
                runtime_body.transform = b_data.transform
                runtime_body.collision_layer = b_data.collision_layer
                runtime_body.collision_mask = b_data.collision_mask
                runtime_body.shapes = b_data.shapes
                runtime_body.linear_velocity = b_data.linear_velocity
                runtime_body.angular_velocity = b_data.angular_velocity
                runtime_body.axis_lock = b_data.axis_lock

                b_data.runtime_body = runtime_body
                space_data.space_3d.add_body(runtime_body)

    def body_set_mode(self, body: RID, mode: int):
        """Set body mode"""
        if body in self._bodies:
            b_data = self._bodies[body]
            b_data.mode = mode

            if b_data.runtime_body:
                b_data.runtime_body.set_mode(mode)

    def body_set_collision_layer(self, body: RID, layer: int):
        if body in self._bodies:
            self._bodies[body].collision_layer = layer

    def body_set_collision_mask(self, body: RID, mask: int):
        if body in self._bodies:
            self._bodies[body].collision_mask = mask

    def body_add_shape(
        self,
        body: RID,
        shape: RID,
        transform: Transform3D = None,
        disabled: bool = False,
    ):
        if body not in self._bodies:
            return

        if transform is None:
            transform = Transform3D()

        shape_info = {"shape": shape, "transform": transform, "disabled": disabled}
        self._bodies[body].shapes.append(shape_info)

        b_data = self._bodies[body]
        if b_data.runtime_body:
            b_data.runtime_body.shapes.append(shape_info)

    def body_set_state(self, body: RID, state: int, value: Any):
        """
        Set body state.
        """
        if body not in self._bodies:
            return

        b_data = self._bodies[body]

        if state == BodyStateEnums.BODY_STATE_TRANSFORM:
            if isinstance(value, Transform3D):
                b_data.transform = value
                if b_data.runtime_body:
                    b_data.runtime_body.transform = value

        elif state == BodyStateEnums.BODY_STATE_LINEAR_VELOCITY:
            if isinstance(value, Vector3):
                b_data.linear_velocity = value
                if b_data.runtime_body:
                    b_data.runtime_body.linear_velocity = value

        elif state == BodyStateEnums.BODY_STATE_ANGULAR_VELOCITY:
            if isinstance(value, Vector3):
                b_data.angular_velocity = value
                if b_data.runtime_body:
                    b_data.runtime_body.angular_velocity = value

        elif state == BodyStateEnums.BODY_STATE_CAN_SLEEP:
            if b_data.runtime_body:
                b_data.runtime_body.can_sleep = bool(value)

    def body_get_state(self, body: RID, state: BodyStateEnums) -> Any:
        """Get body state"""
        if body not in self._bodies:
            return None

        b_data = self._bodies[body]

        if b_data.runtime_body:
            if state == BodyStateEnums.BODY_STATE_TRANSFORM:
                return b_data.runtime_body.transform
            elif state == BodyStateEnums.BODY_STATE_LINEAR_VELOCITY:
                return b_data.runtime_body.linear_velocity
            elif state == BodyStateEnums.BODY_STATE_ANGULAR_VELOCITY:
                return b_data.runtime_body.angular_velocity

        if state == BodyStateEnums.BODY_STATE_TRANSFORM:
            return b_data.transform
        elif state == BodyStateEnums.BODY_STATE_LINEAR_VELOCITY:
            return b_data.linear_velocity
        elif state == BodyStateEnums.BODY_STATE_ANGULAR_VELOCITY:
            return b_data.angular_velocity

        return None

    def _get_runtime_body(self, body_rid: RID):
        if body_rid not in self._bodies:
            return None
        return self._bodies[body_rid].runtime_body
