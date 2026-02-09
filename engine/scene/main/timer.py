from engine.scene.main.node import Node
from engine.scene.main.signal import Signal
from engine.scene.main.process_mode import ProcessMode


class Timer(Node):
    def __init__(self):
        super().__init__()

        self.wait_time: float = 1.0
        self.one_shot: bool = False
        self.autostart: bool = False
        self.time_left: float = 0.0
        self._running: bool = False

        self.process_callback: ProcessMode = ProcessMode.IDLE

        self.timeout = Signal("timeout")

    def _ready(self) -> None:
        if self.autostart:
            self.start()

    def start(self, time_sec: float | None = None) -> None:
        if time_sec is not None:
            self.wait_time = max(0.0, time_sec)

        self.time_left = self.wait_time
        self._running = True

        if self.process_callback == ProcessMode.IDLE:
            self.set_process(True)
        elif self.process_callback == ProcessMode.PHYSICS:
            self.set_physics_process(True)

    def stop(self) -> None:
        self._running = False
        self.time_left = 0.0
        self.set_process(False)
        self.set_physics_process(False)

    def is_stopped(self) -> bool:
        return not self._running

    def _advance(self, delta: float) -> None:
        if not self._running or self.is_paused():
            return

        self.time_left -= delta

        if self.time_left > 0:
            return

        self.timeout.emit()

        if self.one_shot:
            self.stop()
        else:
            self.time_left += self.wait_time
