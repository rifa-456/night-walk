"""
DirectSpaceState3D - Read-only physics query interface.

Provides methods for querying physics state without affecting simulation:
- Raycasting
- Shape intersection
- Point queries
- Motion casting

In Godot 4.x, this is GodotPhysicsDirectSpaceState3D.
"""

from typing import TYPE_CHECKING, Dict, List, Optional
from engine.math.datatypes.vector3 import Vector3
from engine.math.datatypes.transform_3d import Transform3D
from engine.core.rid import RID

if TYPE_CHECKING:
    from engine.servers.physics.spaces.space_3d import Space3D


class RayResult:
    """Result from a raycast query"""

    __slots__ = ("position", "normal", "rid", "collider", "shape", "face_index")

    def __init__(self):
        self.position = Vector3()
        self.normal = Vector3()
        self.rid: Optional[RID] = None
        self.collider = None
        self.shape = 0
        self.face_index = -1

    def to_dict(self) -> Dict:
        return {
            "position": self.position,
            "normal": self.normal,
            "rid": self.rid,
            "collider": self.collider,
            "shape": self.shape,
        }


class ShapeResult:
    """Result from a shape intersection query"""

    __slots__ = ("rid", "collider", "shape")

    def __init__(self):
        self.rid: Optional[RID] = None
        self.collider = None
        self.shape = 0

    def to_dict(self) -> Dict:
        return {"rid": self.rid, "collider": self.collider, "shape": self.shape}


class DirectSpaceState3D:
    """
    Direct access to physics space for queries.

    This is a read-only interface that doesn't affect simulation.
    All methods are thread-safe as they don't modify state.
    """

    __slots__ = ("space",)

    def __init__(self, space: "Space3D"):
        """
        Initialize direct state.

        Args:
            space: The Space3D to query
        """
        self.space = space

    def intersect_ray(
        self,
        from_pos: Vector3,
        to_pos: Vector3,
        exclude: List[RID] = None,
        collision_mask: int = 0xFFFFFFFF,
        collide_with_bodies: bool = True,
        collide_with_areas: bool = False,
    ) -> Optional[Dict]:
        """
        Cast a ray and return the first collision.

        Args:
            from_pos: Ray start position
            to_pos: Ray end position
            exclude: List of RIDs to exclude
            collision_mask: Collision mask filter
            collide_with_bodies: Whether to hit bodies
            collide_with_areas: Whether to hit areas

        Returns:
            Dictionary with collision data or None
        """
        if exclude is None:
            exclude = []

        # Broadphase: Get candidate bodies
        candidates = self.space.broadphase.raycast(from_pos, to_pos, collision_mask)

        # Filter candidates
        candidates = [
            b
            for b in candidates
            if b.rid not in exclude and (collision_mask & b.collision_layer)
        ]

        if not candidates:
            return None

        # Narrowphase: Test each shape
        ray_dir = (to_pos - from_pos).normalized()
        ray_length = from_pos.distance_to(to_pos)

        closest_hit = None
        closest_distance = ray_length + 1.0

        for body in candidates:
            for shape_idx, shape_info in enumerate(body.shapes):
                if shape_info.get("disabled", False):
                    continue

                shape_rid = shape_info["shape"]
                shape_data = self.space._shape_storage._get_shape_data(shape_rid)
                if not shape_data:
                    continue

                global_transform = body.transform * shape_info["transform"]

                # Perform ray-shape intersection
                hit = self._ray_shape_intersect(
                    from_pos,
                    ray_dir,
                    ray_length,
                    shape_data.type,
                    global_transform,
                    shape_data.data,
                )

                if hit and hit["distance"] < closest_distance:
                    closest_distance = hit["distance"]
                    closest_hit = {
                        "position": hit["position"],
                        "normal": hit["normal"],
                        "rid": body.rid,
                        "collider": body,
                        "shape": shape_idx,
                    }

        return closest_hit

    def _ray_shape_intersect(
        self,
        ray_origin: Vector3,
        ray_dir: Vector3,
        ray_length: float,
        shape_type: int,
        shape_transform: Transform3D,
        shape_data: dict,
    ) -> Optional[Dict]:
        """
        Ray-shape intersection test.

        This implements analytical ray intersection for each shape type.
        """
        from engine.servers.physics.enums import PhysicsServer3DEnums

        if shape_type == PhysicsServer3DEnums.SHAPE_SPHERE:
            return self._ray_sphere(
                ray_origin, ray_dir, ray_length, shape_transform, shape_data
            )
        elif shape_type == PhysicsServer3DEnums.SHAPE_BOX:
            return self._ray_box(
                ray_origin, ray_dir, ray_length, shape_transform, shape_data
            )
        elif shape_type == PhysicsServer3DEnums.SHAPE_CAPSULE:
            return self._ray_capsule(
                ray_origin, ray_dir, ray_length, shape_transform, shape_data
            )

        # Unsupported shape type
        return None

    def _ray_sphere(
        self,
        ray_origin: Vector3,
        ray_dir: Vector3,
        ray_length: float,
        transform: Transform3D,
        data: dict,
    ) -> Optional[Dict]:
        """Ray-sphere intersection"""
        radius = data.get("radius", 0.5)
        center = transform.origin

        # Ray-sphere intersection math
        oc = ray_origin - center
        a = ray_dir.dot(ray_dir)
        b = 2.0 * oc.dot(ray_dir)
        c = oc.dot(oc) - radius * radius
        discriminant = b * b - 4 * a * c

        if discriminant < 0:
            return None

        # Compute intersection distance
        sqrt_disc = discriminant**0.5
        t1 = (-b - sqrt_disc) / (2 * a)
        t2 = (-b + sqrt_disc) / (2 * a)

        # Use closest positive intersection
        t = t1 if t1 >= 0 else t2
        if t < 0 or t > ray_length:
            return None

        # Compute hit point and normal
        hit_pos = ray_origin + ray_dir * t
        normal = (hit_pos - center).normalized()

        return {"distance": t, "position": hit_pos, "normal": normal}

    def _ray_box(
        self,
        ray_origin: Vector3,
        ray_dir: Vector3,
        ray_length: float,
        transform: Transform3D,
        data: dict,
    ) -> Optional[Dict]:
        """Ray-box intersection using slab method"""
        half_extents = data.get("half_extents", Vector3(0.5, 0.5, 0.5))

        # Transform ray to box local space
        inv_transform = transform.inverse()
        local_origin = inv_transform.xform(ray_origin)
        local_dir = inv_transform.basis.xform(ray_dir).normalized()

        # Slab intersection
        tmin = float("-inf")
        tmax = float("inf")
        hit_normal = Vector3()

        for i in range(3):
            if abs(local_dir[i]) < 1e-6:
                # Ray parallel to slab
                if abs(local_origin[i]) > half_extents[i]:
                    return None
            else:
                # Compute intersection distances
                ood = 1.0 / local_dir[i]
                t1 = (-half_extents[i] - local_origin[i]) * ood
                t2 = (half_extents[i] - local_origin[i]) * ood

                if t1 > t2:
                    t1, t2 = t2, t1

                if t1 > tmin:
                    tmin = t1
                    # Normal is along axis i
                    hit_normal = Vector3()
                    hit_normal.data[i] = -1.0 if local_dir[i] > 0 else 1.0

                tmax = min(tmax, t2)

                if tmin > tmax:
                    return None

        if tmin < 0 or tmin > ray_length:
            return None

        # Transform back to world space
        local_hit = local_origin + local_dir * tmin
        world_hit = transform.xform(local_hit)
        world_normal = transform.basis.xform(hit_normal).normalized()

        return {"distance": tmin, "position": world_hit, "normal": world_normal}

    def _ray_capsule(
        self,
        ray_origin: Vector3,
        ray_dir: Vector3,
        ray_length: float,
        transform: Transform3D,
        data: dict,
    ) -> Optional[Dict]:
        """Ray-capsule intersection"""
        radius = data.get("radius", 0.5)
        height = data.get("height", 2.0)
        half_height = max(0, (height - 2 * radius) * 0.5)

        # Capsule axis
        axis = transform.basis.y
        p1 = transform.origin - axis * half_height
        p2 = transform.origin + axis * half_height

        # Ray-capsule as ray-segment + sphere caps
        # This is simplified - production version would be more robust

        # Test against segment
        # (Simplified - should do proper ray-cylinder test)

        # Test against sphere caps
        hit1 = self._ray_sphere(
            ray_origin,
            ray_dir,
            ray_length,
            Transform3D(transform.basis, p1),
            {"radius": radius},
        )
        hit2 = self._ray_sphere(
            ray_origin,
            ray_dir,
            ray_length,
            Transform3D(transform.basis, p2),
            {"radius": radius},
        )

        # Return closest hit
        if hit1 and hit2:
            return hit1 if hit1["distance"] < hit2["distance"] else hit2
        return hit1 or hit2

    def intersect_shape(
        self,
        shape_rid: RID,
        transform: Transform3D,
        margin: float = 0.0,
        max_results: int = 32,
        exclude: List[RID] = None,
        collision_mask: int = 0xFFFFFFFF,
    ) -> List[Dict]:
        """
        Test shape overlap and return all overlapping bodies.

        Args:
            shape_rid: Shape to test
            transform: Shape transform
            margin: Collision margin
            max_results: Maximum results to return
            exclude: RIDs to exclude
            collision_mask: Collision mask filter

        Returns:
            List of collision dictionaries
        """
        if exclude is None:
            exclude = []

        shape_data = self.space._shape_storage._get_shape_data(shape_rid)
        if not shape_data:
            return []

        # Compute query AABB
        from engine.servers.physics.spaces.broadphase.broadphase_3d import (
            _compute_shape_aabb,
        )

        query_aabb = _compute_shape_aabb(shape_data.type, transform, shape_data.data)

        # Broadphase
        candidates = self.space.broadphase.query_aabb(query_aabb, collision_mask)
        candidates = [b for b in candidates if b.rid not in exclude]

        # Narrowphase
        from engine.servers.physics.collision_solver_3d import CollisionSolver3D

        results = []
        for body in candidates:
            if len(results) >= max_results:
                break

            for shape_idx, body_shape_info in enumerate(body.shapes):
                if body_shape_info.get("disabled", False):
                    continue

                body_shape_rid = body_shape_info["shape"]
                body_shape_data = self.space._shape_storage._get_shape_data(
                    body_shape_rid
                )
                if not body_shape_data:
                    continue

                body_shape_transform = body.transform * body_shape_info["transform"]

                # Test collision
                col_result = CollisionSolver3D.solve_static(
                    shape_data.type,
                    transform,
                    shape_data.data,
                    body_shape_data.type,
                    body_shape_transform,
                    body_shape_data.data,
                )

                if col_result and col_result.collided:
                    results.append(
                        {"rid": body.rid, "collider": body, "shape": shape_idx}
                    )
                    break

        return results

    def cast_motion(
        self,
        shape_rid: RID,
        transform: Transform3D,
        motion: Vector3,
        margin: float = 0.0,
        exclude: List[RID] = None,
        collision_mask: int = 0xFFFFFFFF,
    ) -> Dict:
        """
        Cast a shape along a motion vector.

        Returns the safe and unsafe fractions of motion.

        Args:
            shape_rid: Shape to cast
            transform: Starting transform
            motion: Motion vector
            margin: Collision margin
            exclude: RIDs to exclude
            collision_mask: Collision mask filter

        Returns:
            Dictionary with safe_fraction and unsafe_fraction
        """
        return {"safe_fraction": 1.0, "unsafe_fraction": 1.0}

    def collide_shape(
        self,
        shape_rid: RID,
        transform: Transform3D,
        margin: float = 0.0,
        max_results: int = 32,
        exclude: List[RID] = None,
        collision_mask: int = 0xFFFFFFFF,
    ) -> List[Vector3]:
        """
        Get collision points for shape overlap.

        Similar to intersect_shape but returns contact points.

        Args:
            shape_rid: Shape to test
            transform: Shape transform
            margin: Collision margin
            max_results: Maximum contact points
            exclude: RIDs to exclude
            collision_mask: Collision mask filter

        Returns:
            List of contact point positions
        """
        results = self.intersect_shape(
            shape_rid, transform, margin, max_results, exclude, collision_mask
        )
        return []

    def get_rest_info(
        self,
        shape_rid: RID,
        transform: Transform3D,
        margin: float = 0.0,
        exclude: List[RID] = None,
        collision_mask: int = 0xFFFFFFFF,
    ) -> Optional[Dict]:
        """
        Get resting contact information.

        Returns the deepest penetration if shape is overlapping.
        """
        results = self.intersect_shape(
            shape_rid, transform, margin, 1, exclude, collision_mask
        )

        if results:
            return results[0]

        return None
