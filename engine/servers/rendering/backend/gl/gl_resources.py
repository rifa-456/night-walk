from __future__ import annotations
from typing import Tuple
from OpenGL import GL
from OpenGL.GL import shaders as _GL_shaders
from engine.servers.rendering.server_enums import (
    TextureFormat,
    TextureFilter,
    TextureRepeat,
)


class GLResourceError(Exception):
    """Raised when an OpenGL resource operation fails."""


def _texture_format_to_gl(fmt: TextureFormat) -> Tuple[int, int, int]:
    _MAP = {
        TextureFormat.TEXTURE_FORMAT_R8: ("GL_R8", "GL_RED", "GL_UNSIGNED_BYTE"),
        TextureFormat.TEXTURE_FORMAT_RG8: ("GL_RG8", "GL_RG", "GL_UNSIGNED_BYTE"),
        TextureFormat.TEXTURE_FORMAT_RGB8: ("GL_RGB8", "GL_RGB", "GL_UNSIGNED_BYTE"),
        TextureFormat.TEXTURE_FORMAT_RGBA8: ("GL_RGBA8", "GL_RGBA", "GL_UNSIGNED_BYTE"),
        TextureFormat.TEXTURE_FORMAT_R16: ("GL_R16", "GL_RED", "GL_UNSIGNED_SHORT"),
        TextureFormat.TEXTURE_FORMAT_RG16: ("GL_RG16", "GL_RG", "GL_UNSIGNED_SHORT"),
        TextureFormat.TEXTURE_FORMAT_RGB16: ("GL_RGB16", "GL_RGB", "GL_UNSIGNED_SHORT"),
        TextureFormat.TEXTURE_FORMAT_RGBA16: (
            "GL_RGBA16",
            "GL_RGBA",
            "GL_UNSIGNED_SHORT",
        ),
        TextureFormat.TEXTURE_FORMAT_R32F: ("GL_R32F", "GL_RED", "GL_FLOAT"),
        TextureFormat.TEXTURE_FORMAT_RG32F: ("GL_RG32F", "GL_RG", "GL_FLOAT"),
        TextureFormat.TEXTURE_FORMAT_RGB32F: ("GL_RGB32F", "GL_RGB", "GL_FLOAT"),
        TextureFormat.TEXTURE_FORMAT_RGBA32F: ("GL_RGBA32F", "GL_RGBA", "GL_FLOAT"),
    }

    if GL is None:
        raise GLResourceError("OpenGL not available")

    names = _MAP.get(fmt)

    if names is None:
        raise GLResourceError(f"Unsupported TextureFormat: {fmt}")

    return getattr(GL, names[0]), getattr(GL, names[1]), getattr(GL, names[2])


def _filter_to_gl(filt: TextureFilter) -> Tuple[int, int]:
    if GL is None:
        raise GLResourceError("OpenGL not available")
    _MAP = {
        TextureFilter.TEXTURE_FILTER_NEAREST: (GL.GL_NEAREST, GL.GL_NEAREST),
        TextureFilter.TEXTURE_FILTER_LINEAR: (GL.GL_LINEAR, GL.GL_LINEAR),
        TextureFilter.TEXTURE_FILTER_NEAREST_WITH_MIPMAPS: (
            GL.GL_NEAREST_MIPMAP_NEAREST,
            GL.GL_NEAREST,
        ),
        TextureFilter.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS: (
            GL.GL_LINEAR_MIPMAP_LINEAR,
            GL.GL_LINEAR,
        ),
    }
    return _MAP.get(filt, (GL.GL_LINEAR, GL.GL_LINEAR))


def _repeat_to_gl(rep: TextureRepeat) -> int:
    if GL is None:
        raise GLResourceError("OpenGL not available")
    return {
        TextureRepeat.TEXTURE_REPEAT_DISABLED: GL.GL_CLAMP_TO_EDGE,
        TextureRepeat.TEXTURE_REPEAT_ENABLED: GL.GL_REPEAT,
        TextureRepeat.TEXTURE_REPEAT_MIRRORED: GL.GL_MIRRORED_REPEAT,
    }.get(rep, GL.GL_CLAMP_TO_EDGE)


def texture_gen() -> int:
    """glGenTextures(1) → GL name."""
    if GL is None:
        raise GLResourceError("OpenGL not available")
    return int(GL.glGenTextures(1))


def texture_delete(name: int) -> None:
    """glDeleteTextures([name])."""
    if GL is None:
        return
    GL.glDeleteTextures(1, [name])


def texture_upload_2d(
    gl_name: int,
    width: int,
    height: int,
    data: bytes,
    fmt: TextureFormat,
    filt: TextureFilter,
    rep: TextureRepeat,
    level: int = 0,
    generate_mipmaps: bool = True,
) -> None:
    if GL is None:
        raise GLResourceError("OpenGL not available")

    internal_fmt, src_fmt, src_type = _texture_format_to_gl(fmt)

    actual_filter = filt
    if generate_mipmaps and level == 0:
        if filt == TextureFilter.TEXTURE_FILTER_LINEAR:
            actual_filter = TextureFilter.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
        elif filt == TextureFilter.TEXTURE_FILTER_NEAREST:
            actual_filter = TextureFilter.TEXTURE_FILTER_NEAREST_WITH_MIPMAPS

    min_f, mag_f = _filter_to_gl(actual_filter)
    wrap = _repeat_to_gl(rep)

    GL.glBindTexture(GL.GL_TEXTURE_2D, gl_name)
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, min_f)
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, mag_f)
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_S, wrap)
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_T, wrap)

    GL.glTexImage2D(
        GL.GL_TEXTURE_2D,
        level,
        internal_fmt,
        width,
        height,
        0,
        src_fmt,
        src_type,
        data,
    )

    if generate_mipmaps and level == 0:
        GL.glGenerateMipmap(GL.GL_TEXTURE_2D)


def buffer_gen() -> int:
    if GL is None:
        raise GLResourceError("OpenGL not available")
    return int(GL.glGenBuffers(1))


def buffer_delete(name: int) -> None:
    if GL is None:
        return
    GL.glDeleteBuffers(1, [name])


def buffer_data(name: int, target: int, data: bytes, usage: int) -> None:
    if GL is None:
        raise GLResourceError("OpenGL not available")
    GL.glBindBuffer(target, name)
    GL.glBufferData(target, len(data), data, usage)


def buffer_subdata(name: int, target: int, offset: int, data: bytes) -> None:
    if GL is None:
        raise GLResourceError("OpenGL not available")
    GL.glBindBuffer(target, name)
    GL.glBufferSubData(target, offset, len(data), data)


def vao_gen() -> int:
    if GL is None:
        raise GLResourceError("OpenGL not available")
    return int(GL.glGenVertexArrays(1))


def vao_delete(name: int) -> None:
    if GL is None:
        return
    GL.glDeleteVertexArrays(1, [name])


def shader_compile(source: str, shader_type: int) -> int:
    """Compile a single shader stage.  Returns the GL shader object name.

    Raises GLResourceError with the info-log on failure.
    """
    if GL is None or _GL_shaders is None:
        raise GLResourceError("OpenGL not available")

    shader = GL.glCreateShader(shader_type)
    GL.glShaderSource(shader, source)
    GL.glCompileShader(shader)

    status = GL.glGetShaderiv(shader, GL.GL_COMPILE_STATUS)
    if not status:
        log = GL.glGetShaderInfoLog(shader)
        GL.glDeleteShader(shader)
        raise GLResourceError(f"Shader compile failed: {log}")

    return int(shader)


def shader_link(vertex_shader: int, fragment_shader: int) -> int:
    if GL is None:
        raise GLResourceError("OpenGL not available")

    program = GL.glCreateProgram()
    GL.glAttachShader(program, vertex_shader)
    GL.glAttachShader(program, fragment_shader)
    GL.glLinkProgram(program)

    status = GL.glGetProgramiv(program, GL.GL_LINK_STATUS)
    if not status:
        log = GL.glGetProgramInfoLog(program)
        GL.glDeleteProgram(program)
        raise GLResourceError(f"Shader link failed: {log}")

    GL.glDetachShader(program, vertex_shader)
    GL.glDetachShader(program, fragment_shader)
    GL.glDeleteShader(vertex_shader)
    GL.glDeleteShader(fragment_shader)

    return int(program)


def shader_delete(program: int) -> None:
    if GL is None:
        return
    GL.glDeleteProgram(program)


def shader_get_uniform_location(program: int, name: str) -> int:
    """Returns -1 if the uniform does not exist (same as GL spec)."""
    if GL is None:
        raise GLResourceError("OpenGL not available")
    return int(GL.glGetUniformLocation(program, name.encode("ascii")))


def shader_get_attrib_location(program: int, name: str) -> int:
    if GL is None:
        raise GLResourceError("OpenGL not available")
    return int(GL.glGetAttribLocation(program, name.encode("ascii")))
