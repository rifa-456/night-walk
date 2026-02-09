from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, Optional, TYPE_CHECKING

from engine.core.rid import RID
from engine.servers.rendering.server_enums import (
    TextureFormat,
    TextureFilter,
    TextureRepeat,
)

if TYPE_CHECKING:
    from engine.servers.rendering.backend.rendering_device import RenderingDevice
    from engine.servers.rendering.utilities.render_state import RenderState


@dataclass
class TextureData:
    """All engine-side metadata for a single texture.

    Attributes
    ----------
    rid : Any
        The opaque RID returned to callers.
    gpu_rid : Any
    width : int
    height : int
    format : TextureFormat
    filter_mode : TextureFilter
    repeat_mode : TextureRepeat
    mipmaps : int
        Number of mipmap levels currently uploaded.  0 = base only.
    """

    rid: RID
    gpu_rid: int
    width: int
    height: int
    format: TextureFormat
    filter_mode: TextureFilter = TextureFilter.TEXTURE_FILTER_LINEAR
    repeat_mode: TextureRepeat = TextureRepeat.TEXTURE_REPEAT_DISABLED
    generate_mipmaps: bool = True
    mipmaps: int = 0


class TextureStorage:
    def __init__(
        self,
        rendering_device: "RenderingDevice",
        render_state: "RenderState",
    ) -> None:
        self._device: RenderingDevice = rendering_device
        self._render_state: RenderState = render_state
        self._textures: Dict[RID, TextureData] = {}

    def texture_create(
            self,
            width: int,
            height: int,
            format: TextureFormat = TextureFormat.TEXTURE_FORMAT_RGBA8,
            filter_mode: TextureFilter = TextureFilter.TEXTURE_FILTER_LINEAR,
            repeat_mode: TextureRepeat = TextureRepeat.TEXTURE_REPEAT_DISABLED,
            generate_mipmaps: bool = True,
    ) -> RID:
        """Create a new texture.
        """
        assert isinstance(format, TextureFormat), (
            "Invalid TextureFormat passed to TextureStorage"
        )
        gpu_rid = self._device.texture_create(
            width, height, format, filter_mode, repeat_mode, generate_mipmaps
        )
        rid = RID()
        self._textures[rid] = TextureData(
            rid=rid,
            gpu_rid=gpu_rid,
            width=width,
            height=height,
            format=format,
            filter_mode=filter_mode,
            repeat_mode=repeat_mode,
            generate_mipmaps=generate_mipmaps,
        )

        from engine.logger import Logger
        mipmap_str = "with GPU mipmaps" if generate_mipmaps else "without mipmaps"
        Logger.debug(
            f"TextureStorage: Created texture RID={rid} -> GPU RID={gpu_rid}, "
            f"format={format}, size={width}x{height}, {mipmap_str}",
            "TextureStorage"
        )

        return rid

    def texture_set_data(self, rid: RID, data: bytes, level: int = 0) -> None:
        """Upload raw pixel bytes to an existing texture.

        Raises
        ------
        KeyError
            If *rid* does not correspond to a known texture.
        """
        tex = self._textures[rid]
        self._device.texture_upload(tex.gpu_rid, data, level)
        self._render_state.mark_texture_dirty(rid)

    def texture_free(self, rid: RID) -> None:
        """Destroy a texture.  After this call *rid* is invalid."""
        tex = self._textures.pop(rid, None)
        if tex is not None:
            self._device.texture_free(tex.gpu_rid)

    def texture_get_gpu_rid(self, texture_rid: RID) -> Optional[Any]:
        """Return the GPU-side RID for a given logical texture RID."""
        tex = self._textures.get(texture_rid)
        if tex is None:
            from engine.logger import Logger
            Logger.warn(
                f"texture_get_gpu_rid: RID {texture_rid} not found in storage! "
                f"Available RIDs: {list(self._textures.keys())}",
                "TextureStorage"
            )
            return None


        return tex.gpu_rid
