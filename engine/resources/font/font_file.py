from __future__ import annotations

from engine.resources.font.font import Font


class FontFile(Font):
    """
    Font loaded from disk (TTF / OTF).
    """

    def __init__(self, path: str) -> None:
        super().__init__()
        self.path = path

    def _load(self) -> None:
        # Actual loading will be performed by TextServer implementation
        pass
