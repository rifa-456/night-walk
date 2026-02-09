from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from engine.core.rid import RID
from engine.servers.rendering.canvas.item import CanvasItemData

if TYPE_CHECKING:
    from engine.servers.rendering.utilities.render_state import RenderState


@dataclass
class CanvasLayerData:
    rid: RID
    canvas_rid: Optional[RID] = None
    order: int = 0


@dataclass
class CanvasData:
    rid: Any
    item_rids: List[Any] = field(default_factory=list)


class CanvasStorage:
    def __init__(self, render_state: "RenderState") -> None:
        self._render_state = render_state

        self._canvases: Dict[Any, CanvasData] = {}
        self._items: Dict[Any, CanvasItemData] = {}
        self._layers: Dict[Any, CanvasLayerData] = {}

        self._next_canvas_rid: int = 1
        self._next_item_rid: int = 1
        self._next_layer_rid: int = 1

    def canvas_create(self) -> Any:
        rid = self._next_canvas_rid
        self._next_canvas_rid += 1
        self._canvases[rid] = CanvasData(rid=rid)
        self._render_state.mark_canvas_dirty()
        return rid

    def canvas_free(self, canvas_rid: Any) -> None:
        canvas = self._canvases.pop(canvas_rid, None)
        if canvas is None:
            return
        for item_rid in list(canvas.item_rids):
            item = self._items.get(item_rid)
            if item is not None:
                item.canvas_rid = None
        self._render_state.mark_canvas_dirty()

    def canvas_get(self, canvas_rid: Any) -> Optional[CanvasData]:
        return self._canvases.get(canvas_rid)

    def canvas_exists(self, canvas_rid: Any) -> bool:
        return canvas_rid in self._canvases

    def canvas_item_create(self) -> Any:
        rid = self._next_item_rid
        self._next_item_rid += 1
        self._items[rid] = CanvasItemData(rid=rid)
        self._render_state.mark_canvas_dirty()
        return rid

    def canvas_item_free(self, item_rid: Any) -> None:
        item = self._items.pop(item_rid, None)
        if item is None:
            return

        if item.parent_rid is not None:
            parent = self._items.get(item.parent_rid)
            if parent is not None and item_rid in parent.children:
                parent.children.remove(item_rid)

        for child_rid in item.children:
            child = self._items.get(child_rid)
            if child is not None:
                child.parent_rid = None

        if item.canvas_rid is not None:
            canvas = self._canvases.get(item.canvas_rid)
            if canvas is not None and item_rid in canvas.item_rids:
                canvas.item_rids.remove(item_rid)

        self._render_state.mark_canvas_dirty()

    def canvas_item_get(self, item_rid: Any) -> Optional[CanvasItemData]:
        return self._items.get(item_rid)

    def canvas_item_exists(self, item_rid: Any) -> bool:
        return item_rid in self._items

    def canvas_layer_create(self) -> Any:
        rid = self._next_layer_rid
        self._next_layer_rid += 1
        self._layers[rid] = CanvasLayerData(rid=rid)
        self._render_state.mark_canvas_dirty()
        return rid

    def canvas_layer_free(self, layer_rid: Any) -> None:
        self._layers.pop(layer_rid, None)
        self._render_state.mark_canvas_dirty()

    def canvas_layer_get(self, layer_rid: Any) -> Optional[CanvasLayerData]:
        return self._layers.get(layer_rid)

    def canvas_layer_exists(self, layer_rid: Any) -> bool:
        return layer_rid in self._layers

    def clear(self) -> None:
        self._canvases.clear()
        self._items.clear()
        self._layers.clear()
