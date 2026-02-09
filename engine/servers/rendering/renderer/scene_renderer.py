from __future__ import annotations
from engine.logger import Logger
from engine.servers.rendering.scene.render_data import RenderData
from engine.servers.rendering.server_enums import PrimitiveType
from engine.servers.rendering.storage.renderer_storage import RendererStorage


class SceneRenderer:

    def __init__(self, device, render_state, renderer_storage):
        self._device = device
        self._render_state = render_state
        self._storage: RendererStorage = renderer_storage

    def render(self, render_data: RenderData) -> None:
        if not render_data.items:
            Logger.debug(
                "SceneRenderer.render: no items in RenderData — nothing to draw",
                "SceneRenderer",
            )
            return

        self._render_state.begin_scene()

        self._device.set_depth_test(True)
        self._device.set_depth_write(True)
        self._device.set_cull_face(1)

        self._render_state.current_lights = render_data.lights

        for item in render_data.mesh_items:
            self._draw_item(item, render_data.lights)

        for item in render_data.multimesh_items:
            self._draw_multimesh(item)

        self._render_state.end_scene()

    def _draw_multimesh(self, item):
        """Render a MultiMesh using GPU instancing.

        Creates a composite VAO combining mesh geometry with per-instance data,
        then issues a single instanced draw call.
        """
        storage = self._storage
        mm = storage.multimesh_storage.multimesh_get(item.multimesh_rid)

        if mm is None or mm.mesh_rid is None:
            Logger.debug(
                f"_draw_multimesh: MultiMesh {item.multimesh_rid} has no mesh",
                "SceneRenderer"
            )
            return

        if mm.instance_count <= 0:
            Logger.debug(
                f"_draw_multimesh: MultiMesh {item.multimesh_rid} has no instances",
                "SceneRenderer"
            )
            return

        mesh = storage.mesh_storage.mesh_get(mm.mesh_rid)
        if mesh is None or not mesh.surfaces:
            Logger.debug(
                f"_draw_multimesh: mesh {mm.mesh_rid} not found or has no surfaces",
                "SceneRenderer"
            )
            return

        surface = mesh.surfaces[0]

        material_rid = item.material_rid

        pipeline = storage.resolve_pipeline(material_rid, use_instancing=True)
        if pipeline is None:
            Logger.debug(
                f"_draw_multimesh: no pipeline for material {material_rid}",
                "SceneRenderer"
            )
            return

        if self._render_state.bind_pipeline(pipeline):
            self._device.shader_bind(pipeline)

        view = self._render_state.view_matrix
        proj = self._render_state.projection_matrix

        self._device.shader_set_uniform_mat4(
            pipeline, "u_view", view.to_opengl_matrix()
        )
        self._device.shader_set_uniform_mat4(
            pipeline, "u_projection", proj.to_opengl_matrix()
        )

        lights = self._render_state.current_lights or []
        light_count = min(len(lights), 8)
        self._device.shader_set_uniform_int(
            pipeline,
            "u_light_count",
            light_count,
        )

        for i in range(light_count):
            light = lights[i]
            pos = light.transform.origin
            direction = -light.transform.basis.z
            prefix = f"u_lights[{i}]"

            self._device.shader_set_uniform_vec3(
                pipeline, f"{prefix}.position", pos.x, pos.y, pos.z
            )
            self._device.shader_set_uniform_vec3(
                pipeline, f"{prefix}.direction", direction.x, direction.y, direction.z
            )
            self._device.shader_set_uniform_vec3(
                pipeline, f"{prefix}.color", light.color.r, light.color.g, light.color.b
            )
            self._device.shader_set_uniform_float(
                pipeline, f"{prefix}.energy", light.energy
            )
            self._device.shader_set_uniform_float(
                pipeline, f"{prefix}.range", light.range
            )
            self._device.shader_set_uniform_float(
                pipeline, f"{prefix}.spot_angle_inner", light.spot_angle_inner
            )
            self._device.shader_set_uniform_float(
                pipeline, f"{prefix}.spot_angle_outer", light.spot_angle_outer
            )
            self._device.shader_set_uniform_float(
                pipeline, f"{prefix}.spot_attenuation", light.spot_attenuation
            )

        camera_pos = self._render_state.camera_position
        if camera_pos is not None:
            self._device.shader_set_uniform_vec3(
                pipeline,
                "u_camera_position",
                camera_pos.x,
                camera_pos.y,
                camera_pos.z,
            )

        storage.bind_material(material_rid, self._device)

        vao_rid = storage.resolve_multimesh_vao(item.multimesh_rid, material_rid)
        if vao_rid is None:
            Logger.debug(
                f"_draw_multimesh: failed to resolve composite VAO",
                "SceneRenderer"
            )
            return

        if surface.index_data is not None:
            self._device.draw_list_draw(
                vao_rid,
                surface.primitive,
                surface.index_count,
                instance_count=mm.instance_count,
            )
        else:
            self._device.draw_list_draw_array(
                vao_rid,
                surface.primitive,
                surface.vertex_count,
                instance_count=mm.instance_count,
            )

    def _draw_item(self, item, lights) -> None:
        """
        Draw a mesh instance. Loops through all surfaces and draws each with its material.
        """
        mesh = self._storage.mesh_storage.mesh_get(item.mesh_rid)
        if mesh is None:
            Logger.debug(
                f"SceneRenderer._draw_item: mesh {item.mesh_rid} not found",
                "SceneRenderer",
            )
            return

        if not mesh.surfaces:
            Logger.debug(
                f"SceneRenderer._draw_item: mesh {item.mesh_rid} has no surfaces",
                "SceneRenderer",
            )
            return

        for surface_index in range(len(mesh.surfaces)):
            self._draw_surface(item, surface_index, lights)

    def _draw_surface(self, item, surface_index: int, lights) -> None:
        """
        Draw a single surface of a mesh.
        """
        material_rid = item.material_rid
        if material_rid is None:
            material_rid = self._storage.mesh_surface_get_material(item.mesh_rid, surface_index)

        pipeline = self._storage.resolve_pipeline(material_rid)
        if pipeline is None:
            Logger.debug(
                f"SceneRenderer._draw_surface: no pipeline for surface {surface_index} "
                f"(material_rid={material_rid})",
                "SceneRenderer",
            )
            return

        vertex_array = self._storage.resolve_vertex_array(item.mesh_rid, surface_index)
        if vertex_array is None:
            Logger.debug(
                f"SceneRenderer._draw_surface: no vertex array for surface {surface_index}",
                "SceneRenderer",
            )
            return

        if self._render_state.bind_pipeline(pipeline):
            self._device.shader_bind(pipeline)

        view = self._render_state.view_matrix
        if view is not None:
            self._device.shader_set_uniform_mat4(
                pipeline,
                "u_view",
                view.to_opengl_matrix(),
            )

        proj = self._render_state.projection_matrix
        if proj is not None:
            self._device.shader_set_uniform_mat4(
                pipeline,
                "u_projection",
                proj.to_opengl_matrix(),
            )

        self._device.shader_set_uniform_mat4(
            pipeline,
            "u_model",
            item.transform.to_opengl_matrix(),
        )

        light_count = min(len(lights), 8)
        self._device.shader_set_uniform_int(
            pipeline,
            "u_light_count",
            light_count,
        )

        for i in range(light_count):
            light = lights[i]

            pos = light.transform.origin
            direction = -light.transform.basis.z

            prefix = f"u_lights[{i}]"

            self._device.shader_set_uniform_vec3(
                pipeline,
                f"{prefix}.position",
                pos.x,
                pos.y,
                pos.z,
            )

            self._device.shader_set_uniform_vec3(
                pipeline,
                f"{prefix}.direction",
                direction.x,
                direction.y,
                direction.z,
            )

            self._device.shader_set_uniform_vec3(
                pipeline,
                f"{prefix}.color",
                light.color.r,
                light.color.g,
                light.color.b,
            )

            self._device.shader_set_uniform_float(
                pipeline,
                f"{prefix}.energy",
                light.energy,
            )

            self._device.shader_set_uniform_float(
                pipeline,
                f"{prefix}.range",
                light.range,
            )

            self._device.shader_set_uniform_float(
                pipeline,
                f"{prefix}.spot_angle_inner",
                light.spot_angle_inner,
            )

            self._device.shader_set_uniform_float(
                pipeline,
                f"{prefix}.spot_angle_outer",
                light.spot_angle_outer,
            )

            self._device.shader_set_uniform_float(
                pipeline,
                f"{prefix}.spot_attenuation",
                light.spot_attenuation,
            )

        camera_pos = self._render_state.camera_position
        if camera_pos is not None:
            self._device.shader_set_uniform_vec3(
                pipeline,
                "u_camera_position",
                camera_pos.x,
                camera_pos.y,
                camera_pos.z,
            )

        self._storage.bind_material(material_rid, self._device)

        vao_rid = vertex_array["vao"]
        has_indices = vertex_array["has_indices"]
        primitive = vertex_array.get("primitive", PrimitiveType.PRIMITIVE_TYPE_TRIANGLES)

        if has_indices:
            self._device.draw_list_draw(
                vao_rid,
                primitive,
                vertex_array["index_count"],
            )
        else:
            self._device.draw_list_draw_array(
                vao_rid,
                primitive,
                vertex_array["vertex_count"],
            )
