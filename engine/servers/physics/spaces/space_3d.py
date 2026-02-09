from typing import Dict, List, Optional
from engine.core.rid import RID
from engine.math.datatypes.vector3 import Vector3
from engine.math.datatypes.transform_3d import Transform3D
from engine.math.datatypes.aabb import AABB
from engine.servers.physics.bodies.body_3d import Body3D, Contact3D
from engine.servers.physics.bodies.area_3d import Area3D
from engine.servers.physics.collision_solver_3d import CollisionSolver3D
from engine.servers.physics.spaces.broadphase.broadphase_3d import (
    Broadphase3D,
    compute_body_aabb,
)


class Space3D:
    """
    Physics simulation space.
    """

    __slots__ = (
        "rid",
        "bodies",
        "areas",
        "broadphase",
        "contact_debug_count",
        "body_linear_velocity_sleep_threshold",
        "body_angular_velocity_sleep_threshold",
        "body_time_to_sleep",
        "solver_iterations",
        "default_gravity",
        "default_linear_damp",
        "default_angular_damp",
        "_shape_storage",
        "_direct_state",
    )

    def __init__(self, rid: RID, shape_storage):
        """
        Initialize physics space.

        Args:
            rid: Space RID
            shape_storage: Reference to shape storage for shape data access
        """
        self.rid = rid
        self.bodies: Dict[RID, Body3D] = {}
        self.areas: Dict[RID, Area3D] = {}
        self.broadphase = Broadphase3D()
        self._shape_storage = shape_storage

        # Physics parameters
        self.default_gravity = Vector3(0, -9.8, 0)
        self.default_linear_damp = 0.1
        self.default_angular_damp = 0.1

        # Solver settings
        self.solver_iterations = 8
        self.contact_debug_count = 0

        # Sleep thresholds (for future island management)
        self.body_linear_velocity_sleep_threshold = 0.1
        self.body_angular_velocity_sleep_threshold = 0.1
        self.body_time_to_sleep = 0.5

        # Direct state (for queries)
        self._direct_state = None

    def add_body(self, body: Body3D):
        """Add a body to this space"""
        if body.rid in self.bodies:
            return

        self.bodies[body.rid] = body
        body.space = self
        aabb = compute_body_aabb(body, self._shape_storage)
        self.broadphase.add_body(body, aabb)

    def remove_body(self, body_rid: RID):
        """Remove a body from this space"""
        if body_rid not in self.bodies:
            return

        body = self.bodies[body_rid]
        self.broadphase.remove_body(body)
        del self.bodies[body_rid]

    def add_area(self, area: Area3D):
        """Add an area to this space"""
        if area.rid in self.areas:
            return

        self.areas[area.rid] = area
        area.space = self

    def remove_area(self, area_rid: RID):
        """Remove an area from this space"""
        if area_rid in self.areas:
            del self.areas[area_rid]

    def body_test_motion(
        self,
        body: Body3D,
        from_transform: Transform3D,
        motion: Vector3,
        margin: float,
        exclude_rids: List[RID],
        recovery_as_collision: bool = False,
    ) -> Dict:
        """
        Test body motion with collision detection.

        This is the core of kinematic character movement (CharacterBody3D).
        Performs swept collision detection along motion vector.

        Args:
            body: Body to test
            from_transform: Starting transform
            motion: Motion vector to test
            margin: Collision margin
            exclude_rids: Bodies to exclude from test
            recovery_as_collision: If true, report depenetration as collision

        Returns:
            Dictionary with collision results
        """
        result = {
            "collided": False,
            "collision_point": Vector3(),
            "collision_normal": Vector3(),
            "collision_depth": 0.0,
            "collider": None,
            "collider_rid": None,
            "collider_shape": 0,
            "collision_local_shape": 0,
            "remainder": motion,
            "travel": Vector3(),
            "collision_safe_fraction": 1.0,
            "collision_unsafe_fraction": 1.0,
        }

        if not body.shapes:
            result["travel"] = motion
            result["remainder"] = Vector3()
            return result

        if recovery_as_collision:
            initial_collision = self._check_static_collision(
                body, from_transform, margin, exclude_rids
            )
            if initial_collision:
                result["collided"] = True
                result["collision_point"] = initial_collision["point"]
                result["collision_normal"] = initial_collision["normal"]
                result["collision_depth"] = initial_collision["depth"]
                result["collider"] = initial_collision["collider"]
                result["collider_rid"] = initial_collision["collider_rid"]
                result["collider_shape"] = initial_collision["collider_shape"]
                result["collision_local_shape"] = initial_collision["local_shape"]
                result["travel"] = Vector3()
                result["remainder"] = motion
                return result

        motion_aabb = self._compute_motion_aabb(body, from_transform, motion)
        candidates = self.broadphase.query_aabb(motion_aabb, body.collision_mask)

        candidates = [
            b
            for b in candidates
            if b.rid != body.rid
            and b.rid not in exclude_rids
            and (body.collision_mask & b.collision_layer)
        ]

        if not candidates:
            result["travel"] = motion
            result["remainder"] = Vector3()
            return result

        best_collision = None
        min_safe_fraction = 1.0

        for shape_idx, my_shape_info in enumerate(body.shapes):
            if my_shape_info.get("disabled", False):
                continue

            my_shape_rid = my_shape_info["shape"]
            my_shape_data = self._shape_storage._get_shape_data(my_shape_rid)
            if not my_shape_data:
                continue

            my_local_transform = my_shape_info["transform"]

            for candidate in candidates:
                for other_shape_idx, other_shape_info in enumerate(candidate.shapes):
                    if other_shape_info.get("disabled", False):
                        continue

                    other_shape_rid = other_shape_info["shape"]
                    other_shape_data = self._shape_storage._get_shape_data(
                        other_shape_rid
                    )
                    if not other_shape_data:
                        continue

                    other_local_transform = other_shape_info["transform"]

                    collision = self._sweep_test(
                        my_shape_data.type,
                        from_transform * my_local_transform,
                        my_shape_data.data,
                        motion,
                        other_shape_data.type,
                        candidate.transform * other_local_transform,
                        other_shape_data.data,
                        margin,
                    )

                    if collision and collision["fraction"] < min_safe_fraction:
                        min_safe_fraction = collision["fraction"]
                        best_collision = {
                            **collision,
                            "collider": candidate,
                            "collider_rid": candidate.rid,
                            "collider_shape": other_shape_idx,
                            "local_shape": shape_idx,
                        }

        if best_collision:
            result["collided"] = True
            result["collision_point"] = best_collision["point"]
            result["collision_normal"] = best_collision["normal"]
            result["collision_depth"] = best_collision.get("depth", 0.0)
            result["collider"] = best_collision["collider"]
            result["collider_rid"] = best_collision["collider_rid"]
            result["collider_shape"] = best_collision["collider_shape"]
            result["collision_local_shape"] = best_collision["local_shape"]
            result["collision_safe_fraction"] = best_collision["fraction"]
            result["collision_unsafe_fraction"] = best_collision["fraction"]
            safe_travel = motion * best_collision["fraction"]
            result["travel"] = safe_travel
            result["remainder"] = motion - safe_travel
        else:
            result["travel"] = motion
            result["remainder"] = Vector3()

        return result

    def _check_static_collision(
        self,
        body: Body3D,
        transform: Transform3D,
        margin: float,
        exclude_rids: List[RID],
    ) -> Optional[Dict]:
        """
        Check for static collision at a given transform.
        Used when recovery_as_collision is enabled.

        Args:
            body: Body to test
            transform: Transform to test at
            margin: Collision margin
            exclude_rids: Bodies to exclude

        Returns:
            Collision dict if overlapping, None otherwise
        """
        aabb = self._compute_motion_aabb(body, transform, Vector3())
        candidates = self.broadphase.query_aabb(aabb, body.collision_mask)

        candidates = [
            b
            for b in candidates
            if b.rid != body.rid
            and b.rid not in exclude_rids
            and (body.collision_mask & b.collision_layer)
        ]

        if not candidates:
            return None

        for shape_idx, my_shape_info in enumerate(body.shapes):
            if my_shape_info.get("disabled", False):
                continue

            my_shape_rid = my_shape_info["shape"]
            my_shape_data = self._shape_storage._get_shape_data(my_shape_rid)
            if not my_shape_data:
                continue

            my_local_transform = my_shape_info["transform"]
            my_global_transform = transform * my_local_transform

            for candidate in candidates:
                for other_shape_idx, other_shape_info in enumerate(candidate.shapes):
                    if other_shape_info.get("disabled", False):
                        continue

                    other_shape_rid = other_shape_info["shape"]
                    other_shape_data = self._shape_storage._get_shape_data(
                        other_shape_rid
                    )
                    if not other_shape_data:
                        continue

                    other_local_transform = other_shape_info["transform"]
                    other_global_transform = candidate.transform * other_local_transform

                    from engine.servers.physics.collision_solver_3d import (
                        CollisionSolver3D,
                    )

                    col_result = CollisionSolver3D.solve_static(
                        my_shape_data.type,
                        my_global_transform,
                        my_shape_data.data,
                        other_shape_data.type,
                        other_global_transform,
                        other_shape_data.data,
                    )

                    if col_result and col_result.collided:
                        return {
                            "point": col_result.point,
                            "normal": col_result.normal,
                            "depth": col_result.depth,
                            "collider": candidate,
                            "collider_rid": candidate.rid,
                            "collider_shape": other_shape_idx,
                            "local_shape": shape_idx,
                        }

        return None

    def _sweep_test(
        self,
        shape_a_type: int,
        transform_a: Transform3D,
        data_a: dict,
        motion: Vector3,
        shape_b_type: int,
        transform_b: Transform3D,
        data_b: dict,
        margin: float,
    ) -> Optional[Dict]:
        """
        Swept collision detection between two shapes.

        This performs continuous collision detection (CCD) by
        testing discrete samples along the motion path.

        In production, this would use proper swept algorithms:
        - Conservative advancement
        - Time of impact (TOI) calculation
        - Bezier curve intersection

        For now, we use multi-step discrete testing.
        """
        steps = max(1, int(motion.length() / 0.1) + 1)
        steps = min(steps, 10)  # Cap for performance

        for i in range(steps + 1):
            fraction = i / steps
            test_transform = transform_a.translated(motion * fraction)

            col_result = CollisionSolver3D.solve_static(
                shape_a_type,
                test_transform,
                data_a,
                shape_b_type,
                transform_b,
                data_b,
            )

            if col_result and col_result.collided:
                # Found collision at this fraction
                # Back up slightly to find safe fraction
                if i > 0:
                    safe_fraction = (i - 1) / steps
                else:
                    safe_fraction = 0.0

                return {
                    "fraction": safe_fraction,
                    "point": col_result.point,
                    "normal": col_result.normal,
                    "depth": col_result.depth,
                }

        # No collision
        return None

    def _compute_motion_aabb(
        self, body: Body3D, from_transform: Transform3D, motion: Vector3
    ) -> AABB:
        """Compute AABB encompassing entire motion path"""
        # Compute AABB at start
        temp_body = type(body)(body.rid, self, body.mode)
        temp_body.shapes = body.shapes
        temp_body.transform = from_transform
        start_aabb = compute_body_aabb(temp_body, self._shape_storage)

        # Compute AABB at end
        temp_body.transform = from_transform.translated(motion)
        end_aabb = compute_body_aabb(temp_body, self._shape_storage)

        # Merge
        min_pos = Vector3(
            min(start_aabb.position.x, end_aabb.position.x),
            min(start_aabb.position.y, end_aabb.position.y),
            min(start_aabb.position.z, end_aabb.position.z),
        )
        max_pos = Vector3(
            max(start_aabb.end.x, end_aabb.end.x),
            max(start_aabb.end.y, end_aabb.end.y),
            max(start_aabb.end.z, end_aabb.end.z),
        )

        return AABB(min_pos, max_pos - min_pos)

    def step(self, delta: float):
        """
        Execute physics step.
        """
        if delta <= 0:
            return

        self._update_area_influences()

        for body in self.bodies.values():
            if body.is_rigid():
                body.integrate_forces(delta)

        self._detect_collisions()

        # TODO: Implement proper sequential impulse solver
        self._solve_collisions_simple(delta)

        for body in self.bodies.values():
            if body.is_active():
                body.integrate_velocities(delta)

                aabb = compute_body_aabb(body, self._shape_storage)
                self.broadphase.update_body(body, aabb)

    def _update_area_influences(self):
        """Compute area influences on all bodies"""
        # Reset influences
        for body in self.bodies.values():
            if not body.is_active():
                continue

            body.total_gravity = self.default_gravity
            body.total_linear_damp = self.default_linear_damp
            body.total_angular_damp = self.default_angular_damp

        # TODO: Implement proper area overlap testing and priority sorting
        for area in self.areas.values():
            if not area.is_active():
                continue

            for body in self.bodies.values():
                if not body.is_active():
                    continue

                gravity = area.compute_gravity(body.transform.origin)
                body.total_gravity = gravity
                body.total_linear_damp = area.linear_damp
                body.total_angular_damp = area.angular_damp

    def _detect_collisions(self):
        """Detect all collisions using broadphase + narrowphase"""
        for body in self.bodies.values():
            body.reset_contact_count()

        pairs = self.broadphase.get_collision_pairs()
        for body_a, body_b in pairs:
            self._test_body_pair(body_a, body_b)

    def _test_body_pair(self, body_a: Body3D, body_b: Body3D):
        """Test collision between two bodies (narrowphase)"""
        from engine.servers.physics.collision_solver_3d import CollisionSolver3D

        for i, shape_a_info in enumerate(body_a.shapes):
            if shape_a_info.get("disabled", False):
                continue

            shape_a_rid = shape_a_info["shape"]
            shape_a_data = self._shape_storage._get_shape_data(shape_a_rid)
            if not shape_a_data:
                continue

            transform_a = body_a.transform * shape_a_info["transform"]

            for j, shape_b_info in enumerate(body_b.shapes):
                if shape_b_info.get("disabled", False):
                    continue

                shape_b_rid = shape_b_info["shape"]
                shape_b_data = self._shape_storage._get_shape_data(shape_b_rid)
                if not shape_b_data:
                    continue

                transform_b = body_b.transform * shape_b_info["transform"]

                # Solve collision
                col_result = CollisionSolver3D.solve_static(
                    shape_a_data.type,
                    transform_a,
                    shape_a_data.data,
                    shape_b_data.type,
                    transform_b,
                    shape_b_data.data,
                )

                if col_result and col_result.collided:
                    # Create contacts
                    contact_a = Contact3D()
                    contact_a.local_pos = col_result.point_a
                    contact_a.local_normal = col_result.normal
                    contact_a.depth = col_result.depth
                    contact_a.collider = body_b
                    contact_a.collider_shape = j
                    contact_a.local_shape = i

                    contact_b = Contact3D()
                    contact_b.local_pos = col_result.point_b
                    contact_b.local_normal = -col_result.normal
                    contact_b.depth = col_result.depth
                    contact_b.collider = body_a
                    contact_b.collider_shape = i
                    contact_b.local_shape = j

                    body_a.add_contact(contact_a)
                    body_b.add_contact(contact_b)

    def _solve_collisions_simple(self, delta: float):
        """
        Simple collision response.

        In production, this would be a sequential impulse solver:
        - Build contact constraints
        - Solve iteratively
        - Apply impulses

        This is a placeholder doing simple depenetration.
        """
        for body in self.bodies.values():
            if not body.is_rigid() or not body.contacts:
                continue

            # Simple depenetration
            for contact in body.contacts:
                if contact.collider.is_static():
                    # Push away from static object
                    correction = contact.local_normal * (contact.depth * 0.5)
                    body.transform.origin += correction

                    # Stop velocity in collision direction
                    vel_along_normal = body.linear_velocity.dot(contact.local_normal)
                    if vel_along_normal < 0:
                        # Remove velocity component
                        body.linear_velocity -= contact.local_normal * vel_along_normal

    def get_direct_state(self):
        """Get DirectSpaceState for queries"""
        if not self._direct_state:
            from engine.servers.physics.spaces.direct_space_state_3d import (
                DirectSpaceState3D,
            )

            self._direct_state = DirectSpaceState3D(self)
        return self._direct_state

    def __repr__(self):
        return f"Space3D(RID={self.rid.get_id()}, bodies={len(self.bodies)}, areas={len(self.areas)})"
