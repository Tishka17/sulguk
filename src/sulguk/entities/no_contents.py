from abc import ABC

from sulguk.render import State
from .base import Entity


class NoContents(Entity, ABC):
    def add(self, entity: Entity):
        raise ValueError(f"Unsupported contents for {type(self)} widget")


class NewLine(NoContents):
    def render(self, state: State) -> None:
        state.canvas.add_new_line()


class HorizontalLine(NoContents):
    def render(self, state: State) -> None:
        state.canvas.add_new_line_soft()
        state.canvas.add_text("⎯" * 10)
        state.canvas.add_new_line_soft()


class ZeroWidthSpace(NoContents):
    def render(self, state: State) -> None:
        state.canvas.add_text("\u200b")
