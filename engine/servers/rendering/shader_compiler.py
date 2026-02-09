from engine.resources.material.base_material_3d import MaterialFeature
from engine.resources.material.standard_material_3d import TransparencyMode


class ShaderCompiler:
    @staticmethod
    def generate_standard_material_shader(
            features: MaterialFeature,
            transparency_mode: TransparencyMode = TransparencyMode.OPAQUE,
            use_instancing: bool = False,
    ) -> tuple[str, str]:
        # ------------------------------------------------------------------
        # Vertex Shader
        # ------------------------------------------------------------------

        vertex_inputs = """
        layout(location = 0) in vec3 a_position;
        layout(location = 1) in vec3 a_normal;
        layout(location = 2) in vec2 a_uv;
        """

        if use_instancing:
            vertex_inputs += """
            layout(location = 3) in vec4 i_transform_row0;
            layout(location = 4) in vec4 i_transform_row1;
            layout(location = 5) in vec4 i_transform_row2;
            layout(location = 6) in vec4 i_color;
            layout(location = 7) in vec4 i_custom_data;
            """

        if use_instancing:
            vertex_uniforms = """
        uniform mat4 u_view;
        uniform mat4 u_projection;
        """
        else:
            vertex_uniforms = """
        uniform mat4 u_model;
        uniform mat4 u_view;
        uniform mat4 u_projection;
        """

        vertex_uniforms += """
        uniform vec3 u_uv1_scale;
        uniform vec3 u_uv1_offset;
        """

        vertex_outputs = """
        out vec3 v_world_pos;
        out vec3 v_normal;
        out vec2 v_uv;
        """

        if use_instancing:
            vertex_outputs += """
        out vec4 v_instance_color;
        out vec4 v_instance_custom_data;
        """

        if use_instancing:
            vertex_main = """
        void main() {
            mat4 u_model = mat4(
                i_transform_row0,
                i_transform_row1,
                i_transform_row2,
                vec4(0.0, 0.0, 0.0, 1.0)
            );

            vec4 world_pos = u_model * vec4(a_position, 1.0);
            v_world_pos = world_pos.xyz;

            v_normal = mat3(u_model) * a_normal;

            v_uv = a_uv * u_uv1_scale.xy + u_uv1_offset.xy;

            v_instance_color = i_color;
            v_instance_custom_data = i_custom_data;

            gl_Position = u_projection * u_view * world_pos;
        }
        """
        else:
            vertex_main = """
        void main() {
            vec4 world_pos = u_model * vec4(a_position, 1.0);
            v_world_pos = world_pos.xyz;

            v_normal = mat3(u_model) * a_normal;

            v_uv = a_uv * u_uv1_scale.xy + u_uv1_offset.xy;

            gl_Position = u_projection * u_view * world_pos;
        }
        """

        vertex_code = f"""#version 330 core
        {vertex_inputs}
        {vertex_uniforms}
        {vertex_outputs}
        {vertex_main}
                """

        # ------------------------------------------------------------------
        # Fragment Shader
        # ------------------------------------------------------------------
        defines = []

        if features & MaterialFeature.ALBEDO_TEXTURE:
            defines.append("#define USE_ALBEDO_TEXTURE")

        if features & MaterialFeature.NORMAL_TEXTURE:
            defines.append("#define USE_NORMAL_TEXTURE")

        if features & MaterialFeature.ROUGHNESS_TEXTURE:
            defines.append("#define USE_ROUGHNESS_TEXTURE")

        if features & MaterialFeature.ALPHA_TEXTURE:
            defines.append("#define USE_ALPHA_TEXTURE")

        if transparency_mode == TransparencyMode.ALPHA_SCISSOR:
            defines.append("#define USE_ALPHA_SCISSOR")

        if features & MaterialFeature.LIGHTING_PHONG:
            defines.append("#define USE_PHONG_LIGHTING")

        if use_instancing:
            defines.append("#define USE_INSTANCING")

        defines_str = "\n".join(defines)

        fragment_varyings = """
        in vec3 v_world_pos;
        in vec3 v_normal;
        in vec2 v_uv;
        """

        if use_instancing:
            fragment_varyings += """
        in vec4 v_instance_color;
        in vec4 v_instance_custom_data;
        """

        fragment_code = f"""#version 330 core

        {defines_str}
        
        {fragment_varyings}
        
        out vec4 frag_color;
        
        uniform vec4 u_albedo_color;
        uniform float u_metallic;
        uniform float u_roughness;
        uniform float u_specular;
        uniform int u_use_blinn;
        
        #ifdef USE_ALBEDO_TEXTURE
        uniform sampler2D u_albedo_texture;
        #endif
        
        #ifdef USE_NORMAL_TEXTURE
        uniform sampler2D u_normal_texture;
        uniform float u_normal_scale;
        #endif
        
        #ifdef USE_ROUGHNESS_TEXTURE
        uniform sampler2D u_roughness_texture;
        #endif
        
        #ifdef USE_ALPHA_TEXTURE
        uniform sampler2D u_alpha_texture;
        #endif
        
        #ifdef USE_ALPHA_SCISSOR
        uniform float u_alpha_scissor_threshold;
        #endif
        
        uniform vec3 u_camera_position;
        
        #define MAX_LIGHTS 8
        
        struct Light {{
            vec3 position;
            vec3 direction;
            vec3 color;
            float energy;
            float range;
            float spot_angle_inner;
            float spot_angle_outer;
            float spot_attenuation;
        }};
        
        uniform int u_light_count;
        uniform Light u_lights[MAX_LIGHTS];
        
        float saturate(float v) {{
            return clamp(v, 0.0, 1.0);
        }}
        
        vec3 apply_normal_map(vec3 N, vec3 tangent_normal, float scale) {{
            vec3 Q1 = dFdx(v_world_pos);
            vec3 Q2 = dFdy(v_world_pos);
            vec2 st1 = dFdx(v_uv);
            vec2 st2 = dFdy(v_uv);
        
            vec3 T = normalize(Q1 * st2.t - Q2 * st1.t);
            vec3 B = -normalize(cross(N, T));
            mat3 TBN = mat3(T, B, N);
        
            vec3 scaled_normal = vec3(tangent_normal.xy * scale, tangent_normal.z);
            return normalize(TBN * scaled_normal);
        }}
        
        void main() {{
            vec3 N = normalize(v_normal);
        
            #ifdef USE_NORMAL_TEXTURE
            vec3 tangent_normal = texture(u_normal_texture, v_uv).xyz * 2.0 - 1.0;
            N = apply_normal_map(N, tangent_normal, u_normal_scale);
            #endif
        
            vec4 albedo = u_albedo_color;
        
            #ifdef USE_ALBEDO_TEXTURE
            albedo *= texture(u_albedo_texture, v_uv);
            #endif
        
            #ifdef USE_INSTANCING
            albedo *= v_instance_color;
            #endif
        
            float alpha = albedo.a;
        
            #ifdef USE_ALPHA_TEXTURE
            alpha *= texture(u_alpha_texture, v_uv).r;
            #endif
        
            #ifdef USE_ALPHA_SCISSOR
            if (alpha < u_alpha_scissor_threshold) {{
                discard;
            }}
            #endif
        
            vec3 V = normalize(u_camera_position - v_world_pos);
        
            vec3 lighting = vec3(0.0);
        
            #ifdef USE_PHONG_LIGHTING
            for (int i = 0; i < u_light_count; i++) {{
                Light light = u_lights[i];
        
                vec3 L = light.position - v_world_pos;
                float distance = length(L);
        
                if (distance > light.range) {{
                    continue;
                }}
        
                vec3 light_dir = normalize(L);
        
                float spot_cos = dot(
                    normalize(-light.direction),
                    light_dir
                );
        
                float cos_inner = cos(light.spot_angle_inner);
                float cos_outer = cos(light.spot_angle_outer);
        
                float angular_attenuation = smoothstep(
                    cos_outer,
                    cos_inner,
                    spot_cos
                );
        
                if (angular_attenuation <= 0.0) {{
                    continue;
                }}
        
                float distance_attenuation =
                    1.0 - saturate(distance / light.range);
        
                float attenuation =
                    angular_attenuation *
                    pow(spot_cos, light.spot_attenuation) *
                    distance_attenuation;
        
                float NdotL = max(dot(N, light_dir), 0.0);
        
                vec3 diffuse =
                    albedo.rgb *
                    light.color *
                    light.energy *
                    NdotL;
        
                float specular_term = 0.0;
        
                if (NdotL > 0.0 && u_specular > 0.0) {{
                    float roughness = u_roughness;
        
                    #ifdef USE_ROUGHNESS_TEXTURE
                    roughness *= texture(u_roughness_texture, v_uv).r;
                    #endif
        
                    roughness = clamp(roughness, 0.04, 1.0);
        
                    float alpha_sq = roughness * roughness;
                    float shininess = pow(2.0 / alpha_sq - 2.0, 0.25);
        
                    if (u_use_blinn == 1) {{
                        vec3 H = normalize(light_dir + V);
                        specular_term = pow(max(dot(N, H), 0.0), shininess);
                    }} else {{
                        vec3 R = reflect(-light_dir, N);
                        specular_term = pow(max(dot(V, R), 0.0), shininess);
                    }}
                }}
        
                vec3 specular =
                    light.color *
                    light.energy *
                    specular_term *
                    u_specular;
        
                lighting += (diffuse + specular) * attenuation;
            }}
            #endif
        
            frag_color = vec4(lighting, alpha);
        }}
        """

        return vertex_code, fragment_code
