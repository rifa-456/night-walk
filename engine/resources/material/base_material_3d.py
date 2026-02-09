from enum import Flag, auto
from engine.core.resource import Resource


class MaterialFeature(Flag):
    NONE = 0
    ALBEDO_TEXTURE = auto()
    NORMAL_TEXTURE = auto()
    ROUGHNESS_TEXTURE = auto()
    ALPHA_TEXTURE = auto()
    TRANSPARENCY = auto()
    LIGHTING_PHONG = auto()


class BaseMaterial3D(Resource):
    def __init__(self) -> None:
        super().__init__()
        self._features: MaterialFeature = MaterialFeature.NONE
        # Don't create RID in __init__ - wait for _create_rid() call
        self._rid = None

    def _create_rid(self) -> None:
        """
        Create the rendering server RID for this material.

        Godot 4.x equivalent: Called during Material initialization,
        but separate from __init__ to allow proper duplication.
        """
        from engine.servers.rendering.server import RenderingServer

        self._rid = RenderingServer.get_singleton().material_create(self)

    def _set_feature(self, feature: MaterialFeature, enabled: bool) -> None:
        old = self._features
        if enabled:
            self._features |= feature
        else:
            self._features &= ~feature

        if self._features != old:
            self.emit_changed()

    def _changed(self) -> None:
        """
        Notify rendering server that material properties changed.

        Godot 4.x equivalent: Material::_update_shader()
        """
        if self._rid is None:
            return

        from engine.servers.rendering.server import RenderingServer

        RenderingServer.get_singleton().material_set_dirty(self._rid)

    def get_features(self) -> MaterialFeature:
        return self._features

    def _copy_properties_to(self, target: 'BaseMaterial3D', subresources: bool) -> None:
        """
        Copy base material properties to target.

        Godot 4.x equivalent: Resource::_duplicate_properties()

        Args:
            target: Target material to copy to
            subresources: If True, sub-resources are duplicated
        """
        super()._copy_properties_to(target, subresources)

        # Copy feature flags
        target._features = self._features