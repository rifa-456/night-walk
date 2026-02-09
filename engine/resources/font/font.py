from __future__ import annotations
from abc import ABC
from typing import Optional

from engine.core.resource import Resource
from engine.core.rid import RID
from engine.servers.text.text_server import TextServer


class Font(Resource, ABC):
    def __init__(self) -> None:
        super().__init__()
        self._font_rid: Optional[RID] = None

    def _ensure_font(self) -> RID:
        if self._font_rid is None:
            self._font_rid = TextServer.get_singleton().font_create()
        return self._font_rid

    def get_rid(self) -> RID:
        return self._ensure_font()

    def _free(self) -> None:
        if self._font_rid is not None:
            TextServer.get_singleton().font_free(self._font_rid)
            self._font_rid = None
