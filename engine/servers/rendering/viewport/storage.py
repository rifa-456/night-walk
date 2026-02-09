from __future__ import annotations
from typing import Any, Dict, Optional, TYPE_CHECKING

from engine.core.rid import RID
from engine.servers.rendering.viewport.data import ViewportData
from engine.servers.rendering.server_enums import MSAAMode

if TYPE_CHECKING:
    from engine.servers.rendering.utilities.render_state import RenderState


class ViewportStorage:
    """
    Owns all ViewportData instances.
    """

    def __init__(self, render_state: "RenderState") -> None:
        self._render_state = render_state
        self._viewports: Dict[RID, ViewportData] = {}
        self._next_rid: int = 1

    def viewport_create(self) -> RID:
        """Create and return a new viewport RID."""
        rid = RID()
        rid._assign(self._next_rid)
        self._next_rid += 1
        self._viewports[rid] = ViewportData(rid=rid)
        self._render_state.mark_viewport_dirty(rid)
        return rid

    def viewport_free(self, rid: RID) -> None:
        """Destroy a viewport."""
        vp = self._viewports.get(rid)
        if vp and vp.msaa_fbo is not None:
            from OpenGL import GL
            if GL is not None:
                GL.glDeleteFramebuffers(1, [vp.msaa_fbo])
                if vp.resolve_fbo is not None:
                    GL.glDeleteFramebuffers(1, [vp.resolve_fbo])

        self._viewports.pop(rid, None)

    def viewport_get(self, rid: RID) -> Optional[ViewportData]:
        """Get viewport data by RID."""
        return self._viewports.get(rid)

    def viewport_exists(self, rid: RID) -> bool:
        """Check if viewport exists."""
        return rid in self._viewports

    def get_all_viewports(self) -> list[ViewportData]:
        """Get all viewports for rendering."""
        return list(self._viewports.values())

    def viewport_set_msaa(self, rid: RID, mode: MSAAMode) -> None:
        """
        Set MSAA mode for a viewport.

        Args:
            rid: Viewport RID
            mode: MSAA sample count (DISABLED, 2X, 4X, 8X)

        """
        vp = self._viewports.get(rid)
        if vp is None:
            return

        if vp.msaa_mode != mode:
            vp.msaa_mode = mode
            self._render_state.mark_viewport_dirty(rid)
            if mode == MSAAMode.MSAA_DISABLED and vp.msaa_fbo is not None:
                from OpenGL import GL
                if GL is not None:
                    GL.glDeleteFramebuffers(1, [vp.msaa_fbo])
                    if vp.resolve_fbo is not None:
                        GL.glDeleteFramebuffers(1, [vp.resolve_fbo])
                vp.msaa_fbo = None
                vp.resolve_fbo = None

    def viewport_get_msaa(self, rid: RID) -> MSAAMode:
        """Get current MSAA mode for a viewport."""
        vp = self._viewports.get(rid)
        if vp is None:
            return MSAAMode.MSAA_DISABLED
        return vp.msaa_mode

    def clear(self) -> None:
        """Free all viewports."""
        for rid in list(self._viewports.keys()):
            self.viewport_free(rid)