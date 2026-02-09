from __future__ import annotations
from typing import Optional

from engine.core.rid import RID
from engine.scene.three_d.visual_instance_3d import VisualInstance3D
from engine.servers.rendering.server import RenderingServer


class GeometryInstance3D(VisualInstance3D):
    """
    Base class for all 3D geometry nodes.

    Godot 4.x equivalent: GeometryInstance3D
    """

    def __init__(self) -> None:
        super().__init__()
        self._material_override: Optional[object] = None

    @property
    def material_override(self) -> Optional[object]:
        """
        Get the material override for this geometry instance.

        Godot 4.x equivalent: GeometryInstance3D.material_override
        """
        return self._material_override

    @material_override.setter
    def material_override(self, value: Optional[object]) -> None:
        """
        Set a material override for this geometry instance.
        Overrides materials on all surfaces of the geometry.

        Args:
            value: Material to apply, or None to clear override
        """
        self._material_override = value
        rs = RenderingServer.get_singleton()

        if value is not None and hasattr(value, "get_rid"):
            rs.instance_geometry_set_material_override(
                self.get_instance(),
                value.get_rid(),
            )
        else:
            rs.instance_geometry_set_material_override(
                self.get_instance(),
                RID(),
            )