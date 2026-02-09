from typing import Dict, Optional
from engine.math.datatypes.transform_3d import Transform3D
from engine.servers.physics.enums import PhysicsServer3DEnums
from engine.servers.physics.solver.result import CollisionResult


class CollisionSolver3D:
    """
    Collision solver dispatcher.
    Routes shape-pair collisions to appropriate narrowphase algorithms.
    """

    @staticmethod
    def solve_static(
        shape_A_type: int,
        transform_A: Transform3D,
        data_A: Dict,
        shape_B_type: int,
        transform_B: Transform3D,
        data_B: Dict,
    ) -> Optional[CollisionResult]:
        """
        Solve collision between two static shapes.

        This is the main entry point for narrowphase collision detection.
        Dispatches to specialized solvers based on shape type combinations.

        Args:
            shape_A_type: First shape type enum
            transform_A: First shape transform
            data_A: First shape data dict
            shape_B_type: Second shape type enum
            transform_B: Second shape transform
            data_B: Second shape data dict

        Returns:
            CollisionResult if collision, None otherwise
        """
        from engine.servers.physics.solver.sat import box_vs_box_sat
        from engine.servers.physics.solver.capsule import (
            capsule_vs_capsule,
            capsule_vs_sphere,
            capsule_vs_box,
            capsule_vs_plane,
        )
        from engine.servers.physics.solver.gjk import solve_gjk_epa

        if (
            shape_A_type == PhysicsServer3DEnums.SHAPE_SPHERE
            and shape_B_type == PhysicsServer3DEnums.SHAPE_SPHERE
        ):
            return solve_gjk_epa(
                shape_A_type, transform_A, data_A, shape_B_type, transform_B, data_B
            )

        elif (
            shape_A_type == PhysicsServer3DEnums.SHAPE_BOX
            and shape_B_type == PhysicsServer3DEnums.SHAPE_BOX
        ):
            return box_vs_box_sat(transform_A, data_A, transform_B, data_B)

        elif (
            shape_A_type == PhysicsServer3DEnums.SHAPE_CAPSULE
            and shape_B_type == PhysicsServer3DEnums.SHAPE_CAPSULE
        ):
            return capsule_vs_capsule(transform_A, data_A, transform_B, data_B)

        elif (
            shape_A_type == PhysicsServer3DEnums.SHAPE_CAPSULE
            and shape_B_type == PhysicsServer3DEnums.SHAPE_SPHERE
        ):
            return capsule_vs_sphere(transform_A, data_A, transform_B, data_B)
        elif (
            shape_A_type == PhysicsServer3DEnums.SHAPE_SPHERE
            and shape_B_type == PhysicsServer3DEnums.SHAPE_CAPSULE
        ):
            result = capsule_vs_sphere(transform_B, data_B, transform_A, data_A)
            if result:
                result.normal = -result.normal
            return result

        elif (
            shape_A_type == PhysicsServer3DEnums.SHAPE_CAPSULE
            and shape_B_type == PhysicsServer3DEnums.SHAPE_BOX
        ):
            return capsule_vs_box(transform_A, data_A, transform_B, data_B)
        elif (
            shape_A_type == PhysicsServer3DEnums.SHAPE_BOX
            and shape_B_type == PhysicsServer3DEnums.SHAPE_CAPSULE
        ):
            result = capsule_vs_box(transform_B, data_B, transform_A, data_A)
            if result:
                result.normal = -result.normal
            return result

        elif (
            shape_A_type == PhysicsServer3DEnums.SHAPE_CAPSULE
            and shape_B_type == PhysicsServer3DEnums.SHAPE_PLANE
        ):
            return capsule_vs_plane(transform_A, data_A, transform_B, data_B)
        elif (
            shape_A_type == PhysicsServer3DEnums.SHAPE_PLANE
            and shape_B_type == PhysicsServer3DEnums.SHAPE_CAPSULE
        ):
            result = capsule_vs_plane(transform_B, data_B, transform_A, data_A)
            if result:
                result.normal = -result.normal
            return result

        elif (
            shape_A_type == PhysicsServer3DEnums.SHAPE_SPHERE
            and shape_B_type == PhysicsServer3DEnums.SHAPE_BOX
        ) or (
            shape_A_type == PhysicsServer3DEnums.SHAPE_BOX
            and shape_B_type == PhysicsServer3DEnums.SHAPE_SPHERE
        ):
            return solve_gjk_epa(
                shape_A_type, transform_A, data_A, shape_B_type, transform_B, data_B
            )

        else:
            return solve_gjk_epa(
                shape_A_type, transform_A, data_A, shape_B_type, transform_B, data_B
            )
