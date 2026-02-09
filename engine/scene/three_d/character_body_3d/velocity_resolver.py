from engine.math.datatypes.vector3 import Vector3


class VelocityResolver:
    """
    Pure math helper for resolving velocity vectors against normals.
    """

    @staticmethod
    def slide(velocity: Vector3, normal: Vector3) -> Vector3:
        """Removes the component of velocity parallel to the normal."""
        return velocity - normal * velocity.dot(normal)

    @staticmethod
    def project_on_floor(velocity: Vector3, normal: Vector3) -> Vector3:
        """Projects velocity onto the floor plane, maintaining horizontal magnitude if needed."""
        return VelocityResolver.slide(velocity, normal)
