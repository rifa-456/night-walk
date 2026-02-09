import time
import sdl2

from engine.scene.main.scene_tree import SceneTree
from engine.scene.main.window import Window
from engine.scene.main.input import Input

from engine.core.os.keyboard import Key
from engine.math.datatypes.vector2 import Vector2

from engine.servers.display.server.sdl import DisplayServerSDL
from engine.servers.rendering.server import RenderingServer

from game.autoload.settings import Settings


def setup_input_map():
    Input.register_action("move_left", [Key.A, Key.LEFT])
    Input.register_action("move_right", [Key.D, Key.RIGHT])
    Input.register_action("move_forward", [Key.W, Key.UP])
    Input.register_action("move_back", [Key.S, Key.DOWN])
    Input.register_action("sprint", [Key.SHIFT])


def main():
    display_server = DisplayServerSDL(
        Settings.TITLE,
        Settings.SCREEN_WIDTH,
        Settings.SCREEN_HEIGHT,
    )
    display_server.initialize()

    rendering_server = RenderingServer.get_singleton()
    rendering_server.initialize()

    from game.autoload.assets import Assets

    Assets.initialize()

    setup_input_map()

    window = Window(
        display_server=display_server,
        title=Settings.TITLE,
        size=Vector2(
            Settings.SCREEN_WIDTH,
            Settings.SCREEN_HEIGHT,
        ),
    )

    scene_tree = SceneTree(window)

    from game.levels.forest_level import ForestLevel

    scene_root = ForestLevel()
    window.add_child(scene_root)
    running = True
    last_time = time.time()

    while running:
        current_time = time.time()
        delta = current_time - last_time
        last_time = current_time

        if delta > 0.1:
            delta = 0.1

        Input.flush_buffered_events()

        window.process_os_events()

        if sdl2.SDL_QuitRequested():
            running = False

        scene_tree.process(delta)
        scene_tree.physics_process(delta)

        rendering_server.draw(delta)
        display_server.swap_buffers()

    sdl2.SDL_Quit()


if __name__ == "__main__":
    main()
