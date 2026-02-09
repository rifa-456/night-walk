from typing import TYPE_CHECKING, List
from engine.math.datatypes.vector3 import Vector3
from engine.math.datatypes.transform_3d import Transform3D
from engine.core.rid import RID
from engine.servers.physics.bodies.contact_3d import Contact3D

if TYPE_CHECKING:
    from engine.servers.physics.spaces.space_3d import Space3D


class Body3D:
    """
    Runtime physics body.
    """

    __slots__ = (
        "rid",
        "space",
        "transform",
        "linear_velocity",
        "angular_velocity",
        "mode",
        "mass",
        "inverse_mass",
        "inertia",
        "inverse_inertia",
        "center_of_mass",
        "gravity_scale",
        "linear_damp",
        "angular_damp",
        "total_gravity",
        "total_linear_damp",
        "total_angular_damp",
        "applied_force",
        "applied_torque",
        "biased_linear_velocity",
        "biased_angular_velocity",
        "contacts",
        "collision_layer",
        "collision_mask",
        "shapes",
        "disabled",
        "axis_lock",
        "continuous_cd",
        "can_sleep",
        "island_index",
        "island_step",
        "_in_tree",
    )

    def __init__(self, rid: RID, space: "Space3D", mode: int):
        """
        Initialize runtime body.

        Args:
            rid: Resource ID linking to BodyData
            space: The Space3D this body belongs to
            mode: Body mode (STATIC, KINEMATIC, RIGID, etc.)
        """
        self.rid = rid
        self.space = space
        self.mode = mode

        # Transform state
        self.transform = Transform3D()

        # Motion state
        self.linear_velocity = Vector3()
        self.angular_velocity = Vector3()
        self.biased_linear_velocity = Vector3()
        self.biased_angular_velocity = Vector3()

        # Mass properties
        self.mass = 1.0
        self.inverse_mass = 1.0
        self.inertia = Vector3(1.0, 1.0, 1.0)
        self.inverse_inertia = Vector3(1.0, 1.0, 1.0)
        self.center_of_mass = Vector3()

        # Physics properties
        self.gravity_scale = 1.0
        self.linear_damp = 0.0
        self.angular_damp = 0.0

        # Area influence
        self.total_gravity = Vector3()
        self.total_linear_damp = 0.0
        self.total_angular_damp = 0.0

        # Force accumulation
        self.applied_force = Vector3()
        self.applied_torque = Vector3()

        # Collision state
        self.contacts: List[Contact3D] = []
        self.collision_layer = 1
        self.collision_mask = 1
        self.shapes: List = []

        # Flags
        self.disabled = False
        self.axis_lock = 0
        self.continuous_cd = False
        self.can_sleep = True

        # Island/sleeping state
        self.island_index = -1
        self.island_step = 0
        self._in_tree = False

    def is_static(self) -> bool:
        """Check if body is static (mode 0)"""
        from engine.servers.physics.enums import PhysicsServer3DEnums

        return self.mode == PhysicsServer3DEnums.BODY_MODE_STATIC

    def is_kinematic(self) -> bool:
        """Check if body is kinematic (mode 1)"""
        from engine.servers.physics.enums import PhysicsServer3DEnums

        return self.mode == PhysicsServer3DEnums.BODY_MODE_KINEMATIC

    def is_rigid(self) -> bool:
        """Check if body is rigid (mode 2 or 3)"""
        from engine.servers.physics.enums import PhysicsServer3DEnums

        return self.mode in (
            PhysicsServer3DEnums.BODY_MODE_RIGID,
            PhysicsServer3DEnums.BODY_MODE_RIGID_LINEAR,
        )

    def is_active(self) -> bool:
        """Check if body participates in simulation"""
        return not self.disabled and not self.is_static()

    def integrate_forces(self, delta: float):
        if not self.is_rigid():
            return

        linear_accel = self.total_gravity * self.gravity_scale

        linear_accel += self.applied_force * self.inverse_mass

        linear_damp_factor = max(0.0, 1.0 - self.total_linear_damp * delta)
        angular_damp_factor = max(0.0, 1.0 - self.total_angular_damp * delta)

        self.linear_velocity += linear_accel * delta
        self.linear_velocity *= linear_damp_factor

        angular_accel = Vector3(
            self.applied_torque.x * self.inverse_inertia.x,
            self.applied_torque.y * self.inverse_inertia.y,
            self.applied_torque.z * self.inverse_inertia.z,
        )
        self.angular_velocity += angular_accel * delta
        self.angular_velocity *= angular_damp_factor

        self.applied_force = Vector3()
        self.applied_torque = Vector3()

    def integrate_velocities(self, delta: float):
        if self.is_static():
            return

        lin_vel = self.biased_linear_velocity or self.linear_velocity
        ang_vel = self.biased_angular_velocity or self.angular_velocity

        from engine.servers.physics.enums import PhysicsServer3DEnums

        if self.axis_lock & PhysicsServer3DEnums.BODY_AXIS_LINEAR_X:
            lin_vel = Vector3(0, lin_vel.y, lin_vel.z)
        if self.axis_lock & PhysicsServer3DEnums.BODY_AXIS_LINEAR_Y:
            lin_vel = Vector3(lin_vel.x, 0, lin_vel.z)
        if self.axis_lock & PhysicsServer3DEnums.BODY_AXIS_LINEAR_Z:
            lin_vel = Vector3(lin_vel.x, lin_vel.y, 0)

        if self.axis_lock & PhysicsServer3DEnums.BODY_AXIS_ANGULAR_X:
            ang_vel = Vector3(0, ang_vel.y, ang_vel.z)
        if self.axis_lock & PhysicsServer3DEnums.BODY_AXIS_ANGULAR_Y:
            ang_vel = Vector3(ang_vel.x, 0, ang_vel.z)
        if self.axis_lock & PhysicsServer3DEnums.BODY_AXIS_ANGULAR_Z:
            ang_vel = Vector3(ang_vel.x, ang_vel.y, 0)

        self.transform.origin += lin_vel * delta

        ang_len = ang_vel.length()
        if ang_len > 1e-6:
            axis = ang_vel / ang_len
            angle = ang_len * delta
            self.transform = self.transform.rotated(axis, angle)

        self.biased_linear_velocity = Vector3()
        self.biased_angular_velocity = Vector3()

    def apply_central_impulse(self, impulse: Vector3):
        """Apply impulse at center of mass"""
        if self.is_rigid():
            self.linear_velocity += impulse * self.inverse_mass

    def apply_impulse(self, impulse: Vector3, position: Vector3):
        """Apply impulse at a specific position"""
        if self.is_rigid():
            self.apply_central_impulse(impulse)
            r = position - self.transform.origin
            torque = r.cross(impulse)
            angular_impulse = Vector3(
                torque.x * self.inverse_inertia.x,
                torque.y * self.inverse_inertia.y,
                torque.z * self.inverse_inertia.z,
            )
            self.angular_velocity += angular_impulse

    def apply_central_force(self, force: Vector3):
        """Apply continuous force at center of mass"""
        if self.is_rigid():
            self.applied_force += force

    def apply_force(self, force: Vector3, position: Vector3):
        """Apply continuous force at a specific position"""
        if self.is_rigid():
            self.applied_force += force
            r = position - self.transform.origin
            self.applied_torque += r.cross(force)

    def apply_torque(self, torque: Vector3):
        """Apply continuous torque"""
        if self.is_rigid():
            self.applied_torque += torque

    def apply_torque_impulse(self, torque: Vector3):
        """Apply instant torque impulse"""
        if self.is_rigid():
            angular_impulse = Vector3(
                torque.x * self.inverse_inertia.x,
                torque.y * self.inverse_inertia.y,
                torque.z * self.inverse_inertia.z,
            )
            self.angular_velocity += angular_impulse

    def set_mode(self, mode: int):
        """Change body mode (static/kinematic/rigid)"""
        from engine.servers.physics.enums import PhysicsServer3DEnums

        self.mode = mode

        if mode == PhysicsServer3DEnums.BODY_MODE_STATIC:
            self.linear_velocity = Vector3()
            self.angular_velocity = Vector3()
            self.applied_force = Vector3()
            self.applied_torque = Vector3()

    def wakeup(self):
        """Wake up sleeping body (for future island management)"""
        # TODO: Implement when island manager is added
        pass

    def reset_contact_count(self):
        self.contacts.clear()

    def add_contact(self, contact: Contact3D):
        self.contacts.append(contact)

    def __repr__(self):
        return f"Body3D(RID={self.rid.get_id()}, mode={self.mode}, pos={self.transform.origin})"
