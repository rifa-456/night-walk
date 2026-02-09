from typing import List, Tuple, Dict
from engine.math.datatypes.aabb import AABB
from engine.math.datatypes.vector3 import Vector3
from engine.math.datatypes.transform_3d import Transform3D
from engine.servers.physics.enums import PhysicsServer3DEnums


class BroadphaseEntry:
    """Represents a body or area in the broadphase"""

    __slots__ = ("body", "aabb", "collision_layer", "collision_mask")

    def __init__(self, body, aabb: AABB, layer: int, mask: int):
        self.body = body
        self.aabb = aabb
        self.collision_layer = layer
        self.collision_mask = mask


class Broadphase3D:
    def __init__(self):
        self._entries: Dict = {}

    def add_body(self, body, aabb: AABB):
        """Add a body to broadphase"""

        entry = BroadphaseEntry(body, aabb, body.collision_layer, body.collision_mask)
        self._entries[body.rid] = entry

    def remove_body(self, body):
        """Remove a body from broadphase"""
        if body.rid in self._entries:
            del self._entries[body.rid]

    def update_body(self, body, aabb: AABB):
        """Update body's AABB"""
        if body.rid in self._entries:
            self._entries[body.rid].aabb = aabb

    def get_collision_pairs(self) -> List[Tuple]:
        """
        Get all potentially colliding body pairs.

        Returns:
            List of (body_a, body_b) tuples that have overlapping AABBs
            and matching layer/mask
        """
        pairs = []
        entries = list(self._entries.values())

        for i in range(len(entries)):
            entry_a = entries[i]

            if entry_a.body.is_static():
                continue

            for j in range(i + 1, len(entries)):
                entry_b = entries[j]

                if entry_a.body.is_static() and entry_b.body.is_static():
                    continue

                if not (entry_a.collision_mask & entry_b.collision_layer):
                    continue
                if not (entry_b.collision_mask & entry_a.collision_layer):
                    continue

                if entry_a.aabb.intersects(entry_b.aabb):
                    pairs.append((entry_a.body, entry_b.body))

        return pairs

    def query_aabb(self, aabb: AABB, collision_mask: int = 0xFFFFFFFF) -> List:
        """
        Query all bodies overlapping an AABB.

        Args:
            aabb: Query AABB
            collision_mask: Collision mask filter

        Returns:
            List of bodies overlapping the AABB
        """
        results = []

        for entry in self._entries.values():
            if not (collision_mask & entry.collision_layer):
                continue

            if aabb.intersects(entry.aabb):
                results.append(entry.body)

        return results

    def raycast(
        self,
        from_pos: Vector3,
        to_pos: Vector3,
        collision_mask: int = 0xFFFFFFFF,
    ) -> List:
        """
        Broadphase raycast - returns bodies whose AABBs intersect ray.
        Narrowphase must do actual ray-shape intersection.

        Args:
            from_pos: Ray start
            to_pos: Ray end
            collision_mask: Collision mask filter

        Returns:
            List of bodies that might be hit
        """
        results = []

        min_x = min(from_pos.x, to_pos.x)
        min_y = min(from_pos.y, to_pos.y)
        min_z = min(from_pos.z, to_pos.z)
        max_x = max(from_pos.x, to_pos.x)
        max_y = max(from_pos.y, to_pos.y)
        max_z = max(from_pos.z, to_pos.z)

        ray_aabb = AABB(
            Vector3(min_x, min_y, min_z),
            Vector3(max_x - min_x, max_y - min_y, max_z - min_z),
        )

        for entry in self._entries.values():
            if not (collision_mask & entry.collision_layer):
                continue

            if ray_aabb.intersects(entry.aabb):
                results.append(entry.body)

        return results

    def clear(self):
        """Clear all entries"""
        self._entries.clear()

    def __len__(self):
        return len(self._entries)


def compute_body_aabb(body, shape_storage) -> AABB:
    """
    Compute the combined AABB for all shapes in a body.

    Args:
        body: Body3D instance
        shape_storage: Reference to shape storage for shape data

    Returns:
        Combined AABB in world space
    """
    if not body.shapes:
        return AABB(
            body.transform.origin - Vector3(0.1, 0.1, 0.1), Vector3(0.2, 0.2, 0.2)
        )

    first_shape_info = body.shapes[0]
    if first_shape_info.get("disabled", False):
        for shape_info in body.shapes:
            if not shape_info.get("disabled", False):
                first_shape_info = shape_info
                break

    shape_rid = first_shape_info["shape"]
    shape_transform = first_shape_info["transform"]
    global_transform = body.transform * shape_transform

    shape_data = shape_storage._get_shape_data(shape_rid)
    if not shape_data:
        return AABB(
            body.transform.origin - Vector3(0.1, 0.1, 0.1), Vector3(0.2, 0.2, 0.2)
        )

    combined_aabb = _compute_shape_aabb(
        shape_data.type, global_transform, shape_data.data
    )

    for shape_info in body.shapes[1:]:
        if shape_info.get("disabled", False):
            continue

        shape_rid = shape_info["shape"]
        shape_transform = shape_info["transform"]
        global_transform = body.transform * shape_transform

        shape_data = shape_storage._get_shape_data(shape_rid)
        if not shape_data:
            continue

        shape_aabb = _compute_shape_aabb(
            shape_data.type, global_transform, shape_data.data
        )

        min_pos = Vector3(
            min(combined_aabb.position.x, shape_aabb.position.x),
            min(combined_aabb.position.y, shape_aabb.position.y),
            min(combined_aabb.position.z, shape_aabb.position.z),
        )
        max_pos = Vector3(
            max(combined_aabb.end.x, shape_aabb.end.x),
            max(combined_aabb.end.y, shape_aabb.end.y),
            max(combined_aabb.end.z, shape_aabb.end.z),
        )
        combined_aabb = AABB(min_pos, max_pos - min_pos)

    return combined_aabb


def _compute_shape_aabb(shape_type: int, transform: Transform3D, data: dict) -> AABB:
    """
    Compute AABB for a single shape.

    This is a helper that computes tight AABBs for different shape types.
    """
    if shape_type == PhysicsServer3DEnums.SHAPE_SPHERE:
        radius = data.get("radius", 0.5)
        center = transform.origin
        return AABB(
            center - Vector3(radius, radius, radius),
            Vector3(radius * 2, radius * 2, radius * 2),
        )

    elif shape_type == PhysicsServer3DEnums.SHAPE_BOX:
        half_extents = data.get("half_extents", Vector3(0.5, 0.5, 0.5))

        corners = [
            Vector3(half_extents.x, half_extents.y, half_extents.z),
            Vector3(half_extents.x, half_extents.y, -half_extents.z),
            Vector3(half_extents.x, -half_extents.y, half_extents.z),
            Vector3(half_extents.x, -half_extents.y, -half_extents.z),
            Vector3(-half_extents.x, half_extents.y, half_extents.z),
            Vector3(-half_extents.x, half_extents.y, -half_extents.z),
            Vector3(-half_extents.x, -half_extents.y, half_extents.z),
            Vector3(-half_extents.x, -half_extents.y, -half_extents.z),
        ]

        transformed = [transform.xform(c) for c in corners]

        min_pos = Vector3(
            min(c.x for c in transformed),
            min(c.y for c in transformed),
            min(c.z for c in transformed),
        )
        max_pos = Vector3(
            max(c.x for c in transformed),
            max(c.y for c in transformed),
            max(c.z for c in transformed),
        )
        return AABB(min_pos, max_pos - min_pos)

    elif shape_type == PhysicsServer3DEnums.SHAPE_CAPSULE:
        radius = data.get("radius", 0.5)
        height = data.get("height", 2.0)
        half_height = max(0, (height - 2 * radius) * 0.5)

        axis = transform.basis.y
        p1 = transform.origin - axis * half_height
        p2 = transform.origin + axis * half_height

        min_pos = Vector3(
            min(p1.x, p2.x) - radius,
            min(p1.y, p2.y) - radius,
            min(p1.z, p2.z) - radius,
        )
        max_pos = Vector3(
            max(p1.x, p2.x) + radius,
            max(p1.y, p2.y) + radius,
            max(p1.z, p2.z) + radius,
        )
        return AABB(min_pos, max_pos - min_pos)

    elif shape_type == PhysicsServer3DEnums.SHAPE_PLANE:
        huge_size = 10000.0
        center = transform.origin

        return AABB(
            center - Vector3(huge_size, 0.1, huge_size),
            Vector3(huge_size * 2, 0.2, huge_size * 2),
        )

    return AABB(transform.origin - Vector3(0.5, 0.5, 0.5), Vector3(1, 1, 1))
