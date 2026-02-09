from enum import auto


class PhysicsServer3DEnums:
    # Body Modes
    BODY_MODE_STATIC = auto()
    BODY_MODE_KINEMATIC = auto()
    BODY_MODE_RIGID = auto()
    BODY_MODE_RIGID_LINEAR = auto()

    # Shape Types
    SHAPE_WORLD_BOUNDARY = auto()
    SHAPE_SEPARATION_RAY = auto()
    SHAPE_SPHERE = auto()
    SHAPE_BOX = auto()
    SHAPE_PLANE = auto()
    SHAPE_CAPSULE = auto()
    SHAPE_CYLINDER = auto()
    SHAPE_CONVEX_POLYGON = auto()
    SHAPE_CONCAVE_POLYGON = auto()
    SHAPE_HEIGHTMAP = auto()
    SHAPE_CUSTOM = auto()

    # Area Param
    AREA_PARAM_GRAVITY = auto()
    AREA_PARAM_GRAVITY_VECTOR = auto()
    AREA_PARAM_GRAVITY_IS_POINT = auto()
    AREA_PARAM_LINEAR_DAMP = auto()
    AREA_PARAM_ANGULAR_DAMP = auto()
    AREA_PARAM_PRIORITY = auto()
    AREA_PARAM_GRAVITY_OVERRIDE_MODE = auto()

    # Area Space Override Mode
    AREA_SPACE_OVERRIDE_DISABLED = auto()
    AREA_SPACE_OVERRIDE_COMBINE = auto()
    AREA_SPACE_OVERRIDE_COMBINE_REPLACE = auto()
    AREA_SPACE_OVERRIDE_REPLACE = auto()
    AREA_SPACE_OVERRIDE_REPLACE_COMBINE = auto()

    # Body Axis Lock
    BODY_AXIS_LINEAR_X = auto()
    BODY_AXIS_LINEAR_Y = auto()
    BODY_AXIS_LINEAR_Z = auto()
    BODY_AXIS_ANGULAR_X = auto()
    BODY_AXIS_ANGULAR_Y = auto()
    BODY_AXIS_ANGULAR_Z = auto()
