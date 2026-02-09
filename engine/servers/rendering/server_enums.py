from __future__ import annotations
from enum import IntEnum, auto

class TextureFormat(IntEnum):
    TEXTURE_FORMAT_R8 = auto()
    TEXTURE_FORMAT_RG8 = auto()
    TEXTURE_FORMAT_RGB8 = auto()
    TEXTURE_FORMAT_RGBA8 = auto()
    TEXTURE_FORMAT_R16 = auto()
    TEXTURE_FORMAT_RG16 = auto()
    TEXTURE_FORMAT_RGB16 = auto()
    TEXTURE_FORMAT_RGBA16 = auto()
    TEXTURE_FORMAT_R32F = auto()
    TEXTURE_FORMAT_RG32F = auto()
    TEXTURE_FORMAT_RGB32F = auto()
    TEXTURE_FORMAT_RGBA32F = auto()


class TextureFilter(IntEnum):
    TEXTURE_FILTER_NEAREST = auto()
    TEXTURE_FILTER_LINEAR = auto()
    TEXTURE_FILTER_NEAREST_WITH_MIPMAPS = auto()
    TEXTURE_FILTER_LINEAR_WITH_MIPMAPS = auto()


class TextureRepeat(IntEnum):
    TEXTURE_REPEAT_DISABLED = auto()
    TEXTURE_REPEAT_ENABLED = auto()
    TEXTURE_REPEAT_MIRRORED = auto()


class BlendMode(IntEnum):
    BLEND_MODE_NORMAL = auto()
    BLEND_MODE_ADD = auto()
    BLEND_MODE_SUB = auto()
    BLEND_MODE_MUL = auto()
    BLEND_MODE_PREMULTIPLIED_ALPHA = auto()


class ShaderMode(IntEnum):
    SHADER_MODE_RENDERING = auto()
    SHADER_MODE_CANVAS_ITEM = auto()
    SHADER_MODE_PARTICLES = auto()
    SHADER_MODE_SKY = auto()
    SHADER_MODE_FOG = auto()


class PrimitiveType(IntEnum):
    PRIMITIVE_TYPE_POINTS = auto()
    PRIMITIVE_TYPE_LINES = auto()
    PRIMITIVE_TYPE_LINE_STRIPS = auto()
    PRIMITIVE_TYPE_TRIANGLES = auto()
    PRIMITIVE_TYPE_TRIANGLE_STRIPS = auto()


class MSAAMode(IntEnum):
    MSAA_DISABLED = auto()
    MSAA_2X = auto()
    MSAA_4X = auto()
    MSAA_8X = auto()

    @staticmethod
    def to_sample_count(mode: "MSAAMode") -> int:
        """Convert MSAAMode to OpenGL sample count."""
        return {
            MSAAMode.MSAA_DISABLED: 1,
            MSAAMode.MSAA_2X: 2,
            MSAAMode.MSAA_4X: 4,
            MSAAMode.MSAA_8X: 8,
        }.get(mode, 1)