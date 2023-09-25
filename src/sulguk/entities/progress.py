from dataclasses import dataclass

from sulguk.render import State
from .base import Entity


@dataclass
class Progress(Entity):
    value: float = 0
    min: float = 0
    max: float = 1
    is_meter: bool = False

    def add(self, entity: "Entity"):
        pass

    def _symbol(self) -> str:
        if self.is_meter:
            return "🟩"
        else:
            return "🟦"

    def _symbol_half(self) -> str:
        if self.is_meter:
            return "🟨"
        else:
            return "🟩"

    def _filling(self) -> str:
        return "⬜"

    def _max_legth(self) -> int:
        if self.is_meter:
            return 6
        else:
            return 10

    def render(self, state: State) -> None:
        max_normal = self.max - self.min
        if not max_normal:
            return
        value_normal = self.value - self.min
        if value_normal <= 0:
            return
        if value_normal < max_normal:
            raw_length = self._max_legth() * value_normal / max_normal
            text_length = int(raw_length)
            fractional = raw_length % 1
            if fractional < 0.25:
                half = False
            if fractional < 0.75:
                half = True
            else:
                half = False
                text_length += 1
        else:
            text_length = self._max_legth()
            half = False

        filling_length = self._max_legth() - text_length - int(half)

        state.canvas.add_text(self._symbol() * text_length)
        if half:
            state.canvas.add_text(self._symbol_half())

        state.canvas.add_text(self._filling() * filling_length)
