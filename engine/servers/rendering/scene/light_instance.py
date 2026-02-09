from dataclasses import dataclass
from engine.core.rid import RID
from engine.math.datatypes.transform_3d import Transform3D
from engine.math.datatypes.color import Color


@dataclass(slots=True)
class LightInstance3D:
    rid: RID
    scenario_rid: RID

    transform: Transform3D
    color: Color
    energy: float
    range: float

    spot_angle_inner: float  # radians
    spot_angle_outer: float  # radians
    spot_attenuation: float  # exponent

    enabled: bool = True