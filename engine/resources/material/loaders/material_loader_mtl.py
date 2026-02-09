from __future__ import annotations
from pathlib import Path
from typing import Dict

from engine.resources.material.standard_material_3d import (
    StandardMaterial3D,
    TransparencyMode,
)
from engine.core.resource_loader import ResourceLoader


class MTLMaterial:
    def __init__(self, name: str):
        self.name = name
        self.albedo_texture: str | None = None
        self.normal_texture: str | None = None
        self.roughness_texture: str | None = None
        self.alpha_texture: str | None = None

        self.specular = 0.5
        self.roughness = 0.5


class MaterialLoaderMTL:
    @staticmethod
    def load(path: str) -> Dict[str, StandardMaterial3D]:
        materials: Dict[str, MTLMaterial] = {}
        current: MTLMaterial | None = None

        base_dir = Path(path).parent

        with open(path, "r", encoding="utf-8") as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue

                tokens = line.split()
                cmd = tokens[0]

                if cmd == "newmtl":
                    current = MTLMaterial(tokens[1])
                    materials[current.name] = current

                elif current is None:
                    continue

                elif cmd == "map_Kd":
                    current.albedo_texture = str(base_dir / tokens[1])

                elif cmd in ("bump", "map_Bump"):
                    current.normal_texture = str(base_dir / tokens[-1])

                elif cmd == "map_Ns":
                    current.roughness_texture = str(base_dir / tokens[1])

                elif cmd == "Ks":
                    current.specular = float(tokens[1])

                elif cmd == "Ns":
                    ns = float(tokens[1])
                    current.roughness = 1.0 - min(ns / 256.0, 1.0)

                elif cmd == "map_d":
                    current.alpha_texture = str(base_dir / tokens[1])

        result: Dict[str, StandardMaterial3D] = {}

        for name, src in materials.items():
            mat = StandardMaterial3D()

            mat.specular = src.specular
            mat.roughness = src.roughness

            from engine.resources.texture.image_texture import ImageTexture

            if src.albedo_texture:
                mat.albedo_texture = ResourceLoader.load(src.albedo_texture, ImageTexture)

            if src.normal_texture:
                mat.normal_texture = ResourceLoader.load(src.normal_texture, ImageTexture)

            if src.roughness_texture:
                mat.roughness_texture = ResourceLoader.load(src.roughness_texture, ImageTexture)

            if src.alpha_texture:
                mat.transparency_mode = TransparencyMode.ALPHA_BLEND
                mat.alpha_texture = ResourceLoader.load(src.alpha_texture, ImageTexture)

            result[name] = mat

        return result
