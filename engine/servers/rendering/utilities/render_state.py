from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Optional, Set

from engine.core.rid import RID
from engine.math import Transform3D, Projection


@dataclass
class RenderState:
    frame_number: int = 0
    frame_time: float = 0.0

    dirty_textures: Set[RID] = field(default_factory=set)
    dirty_meshes: Set[RID] = field(default_factory=set)
    dirty_shaders: Set[RID] = field(default_factory=set)
    dirty_materials: Set[RID] = field(default_factory=set)
    viewport_dirty: Set[RID] = field(default_factory=set)

    canvas_dirty: bool = True
    scene_dirty: bool = True

    camera_position = None

    view_matrix: Optional[Transform3D] = field(default=None, repr=False)
    projection_matrix: Optional[Projection] = field(default=None, repr=False)

    _current_pipeline: Optional[Any] = field(default=None, repr=False)
    _current_vertex_array: Optional[Any] = field(default=None, repr=False)

    def advance_frame(self, delta: float) -> None:
        self.frame_number += 1
        self.frame_time = delta

    def clear(self) -> None:
        self.dirty_textures.clear()
        self.dirty_meshes.clear()
        self.dirty_shaders.clear()
        self.dirty_materials.clear()
        self.viewport_dirty.clear()

        self.canvas_dirty = False
        self.scene_dirty = False

        self._current_pipeline = None
        self._current_vertex_array = None

    def mark_texture_dirty(self, rid: RID) -> None:
        self.dirty_textures.add(rid)

    def mark_mesh_dirty(self, rid: RID) -> None:
        self.dirty_meshes.add(rid)
        self.scene_dirty = True

    def mark_material_dirty(self, rid: RID) -> None:
        self.dirty_materials.add(rid)

    def mark_shader_dirty(self, rid: RID) -> None:
        self.dirty_shaders.add(rid)

    def mark_canvas_dirty(self) -> None:
        self.canvas_dirty = True

    def mark_scene_dirty(self) -> None:
        self.scene_dirty = True

    def mark_viewport_dirty(self, rid: RID) -> None:
        self.viewport_dirty.add(rid)

    def begin_scene(self) -> None:
        """Reset per-scene binding state (called once per viewport scene pass)."""
        self._current_pipeline = None
        self._current_vertex_array = None

    def end_scene(self) -> None:
        """Finalise the scene pass."""
        self._current_pipeline = None
        self._current_vertex_array = None

    def bind_pipeline(self, pipeline: Any) -> bool:
        """Returns True if the pipeline changed and the caller should issue the bind."""
        if pipeline == self._current_pipeline:
            return False
        self._current_pipeline = pipeline
        return True

    def bind_vertex_array(self, vertex_array: Any) -> bool:
        """Returns True if the vertex array changed and the caller should issue the bind."""
        if vertex_array == self._current_vertex_array:
            return False
        self._current_vertex_array = vertex_array
        return True

    def set_camera_transform(self, transform):
        self.view_matrix = transform.affine_inverse()
        self.camera_position = transform.origin

