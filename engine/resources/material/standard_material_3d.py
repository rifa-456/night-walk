from enum import Enum, auto
from typing import Optional

from engine.math import Vector3
from engine.math.datatypes import Color
from engine.resources.material.base_material_3d import (
    BaseMaterial3D,
    MaterialFeature,
)
from engine.resources.texture.texture_2d import Texture2D


class TransparencyMode(Enum):
    OPAQUE = auto()
    ALPHA_BLEND = auto()
    ALPHA_SCISSOR = auto()


class StandardMaterial3D(BaseMaterial3D):

    def __init__(self) -> None:
        super().__init__()
        self._albedo_color = Color(1, 1, 1, 1)
        self._metallic = 0.0
        self._roughness = 1.0
        self._albedo_texture: Texture2D | None = None
        self._normal_texture: Texture2D | None = None
        self._normal_scale = 1.0
        self._roughness_texture: Texture2D | None = None
        self._alpha_texture: Texture2D | None = None
        self._uv1_scale = Vector3(1, 1, 1)
        self._uv1_offset = Vector3(0, 0, 0)
        self._specular = 0.5
        self._use_blinn = True
        self._transparency_mode = TransparencyMode.OPAQUE
        self._alpha_scissor_threshold = 0.5

        # NOW create RID after all properties are initialized
        self._create_rid()

    @property
    def albedo_color(self) -> Color:
        return self._albedo_color

    @albedo_color.setter
    def albedo_color(self, value: Color) -> None:
        self._albedo_color = value
        self.emit_changed()

    @property
    def albedo_texture(self) -> Texture2D | None:
        return self._albedo_texture

    @albedo_texture.setter
    def albedo_texture(self, value: Texture2D | None) -> None:
        self._albedo_texture = value
        self._set_feature(MaterialFeature.ALBEDO_TEXTURE, value is not None)
        self.emit_changed()

    @property
    def metallic(self) -> float:
        return self._metallic

    @metallic.setter
    def metallic(self, value: float) -> None:
        self._metallic = value
        self.emit_changed()

    @property
    def normal_scale(self) -> float:
        return self._normal_scale

    @normal_scale.setter
    def normal_scale(self, value: float) -> None:
        self._normal_scale = value
        self.emit_changed()

    @property
    def roughness(self) -> float:
        return self._roughness

    @roughness.setter
    def roughness(self, value: float) -> None:
        self._roughness = max(0.0, min(1.0, value))
        self.emit_changed()

    @property
    def normal_texture(self) -> Texture2D | None:
        return self._normal_texture

    @normal_texture.setter
    def normal_texture(self, value: Texture2D | None) -> None:
        self._normal_texture = value
        self._set_feature(MaterialFeature.NORMAL_TEXTURE, value is not None)
        self.emit_changed()

    @property
    def roughness_texture(self) -> Texture2D | None:
        return self._roughness_texture

    @roughness_texture.setter
    def roughness_texture(self, value: Texture2D | None) -> None:
        self._roughness_texture = value
        self._set_feature(MaterialFeature.ROUGHNESS_TEXTURE, value is not None)
        self.emit_changed()

    @property
    def alpha_texture(self) -> Texture2D | None:
        return self._alpha_texture

    @alpha_texture.setter
    def alpha_texture(self, value: Texture2D | None) -> None:
        self._alpha_texture = value
        self._set_feature(MaterialFeature.ALPHA_TEXTURE, value is not None)
        self.emit_changed()

    @property
    def uv1_scale(self) -> Vector3:
        return self._uv1_scale

    @uv1_scale.setter
    def uv1_scale(self, value: Vector3) -> None:
        self._uv1_scale = value
        self.emit_changed()

    @property
    def uv1_offset(self) -> Vector3:
        return self._uv1_offset

    @uv1_offset.setter
    def uv1_offset(self, value: Vector3) -> None:
        self._uv1_offset = value
        self.emit_changed()

    @property
    def specular(self) -> float:
        return self._specular

    @specular.setter
    def specular(self, value: float) -> None:
        self._specular = max(0.0, min(1.0, value))
        self.emit_changed()

    @property
    def use_blinn(self) -> bool:
        return self._use_blinn

    @use_blinn.setter
    def use_blinn(self, value: bool) -> None:
        self._use_blinn = value
        self.emit_changed()

    @property
    def transparency_mode(self) -> TransparencyMode:
        return self._transparency_mode

    @transparency_mode.setter
    def transparency_mode(self, value: TransparencyMode) -> None:
        if self._transparency_mode == value:
            return

        self._transparency_mode = value

        self._set_feature(
            MaterialFeature.TRANSPARENCY,
            value != TransparencyMode.OPAQUE
        )

        self.emit_changed()

    @property
    def alpha_scissor_threshold(self) -> float:
        return self._alpha_scissor_threshold

    @alpha_scissor_threshold.setter
    def alpha_scissor_threshold(self, value: float) -> None:
        self._alpha_scissor_threshold = max(0.0, min(1.0, value))
        self.emit_changed()

    def get_features(self):
        features = super().get_features()
        features |= MaterialFeature.LIGHTING_PHONG
        return features

    def _copy_properties_to(self, target: 'StandardMaterial3D', subresources: bool) -> None:
        """
        Copy all StandardMaterial3D properties to target.

        Godot 4.x equivalent: StandardMaterial3D::_duplicate_properties()

        Args:
            target: Target material to copy to
            subresources: If True, textures are duplicated. If False, textures are shared.
        """
        super()._copy_properties_to(target, subresources)

        # Copy color values
        target._albedo_color = Color(
            self._albedo_color.r,
            self._albedo_color.g,
            self._albedo_color.b,
            self._albedo_color.a
        )

        # Copy scalar properties
        target._metallic = self._metallic
        target._roughness = self._roughness
        target._normal_scale = self._normal_scale
        target._specular = self._specular
        target._alpha_scissor_threshold = self._alpha_scissor_threshold

        # Copy boolean flags
        target._use_blinn = self._use_blinn

        # Copy enum
        target._transparency_mode = self._transparency_mode

        # Copy UV transform
        target._uv1_scale = Vector3(
            self._uv1_scale.x,
            self._uv1_scale.y,
            self._uv1_scale.z
        )
        target._uv1_offset = Vector3(
            self._uv1_offset.x,
            self._uv1_offset.y,
            self._uv1_offset.z
        )

        # Copy or share texture references
        if subresources:
            target._albedo_texture = (
                self._albedo_texture.duplicate()
                if self._albedo_texture and hasattr(self._albedo_texture, 'duplicate')
                else self._albedo_texture
            )
            target._normal_texture = (
                self._normal_texture.duplicate()
                if self._normal_texture and hasattr(self._normal_texture, 'duplicate')
                else self._normal_texture
            )
            target._roughness_texture = (
                self._roughness_texture.duplicate()
                if self._roughness_texture and hasattr(self._roughness_texture, 'duplicate')
                else self._roughness_texture
            )
            target._alpha_texture = (
                self._alpha_texture.duplicate()
                if self._alpha_texture and hasattr(self._alpha_texture, 'duplicate')
                else self._alpha_texture
            )
        else:
            # Share texture references (shallow copy)
            target._albedo_texture = self._albedo_texture
            target._normal_texture = self._normal_texture
            target._roughness_texture = self._roughness_texture
            target._alpha_texture = self._alpha_texture

        # Update feature flags based on textures
        target._set_feature(MaterialFeature.ALBEDO_TEXTURE, target._albedo_texture is not None)
        target._set_feature(MaterialFeature.NORMAL_TEXTURE, target._normal_texture is not None)
        target._set_feature(MaterialFeature.ROUGHNESS_TEXTURE, target._roughness_texture is not None)
        target._set_feature(MaterialFeature.ALPHA_TEXTURE, target._alpha_texture is not None)
        target._set_feature(
            MaterialFeature.TRANSPARENCY,
            target._transparency_mode != TransparencyMode.OPAQUE
        )

        # CRITICAL: Create RID for duplicated material and mark dirty
        # This ensures the rendering server has a valid material instance
        target._create_rid()
        target.emit_changed()