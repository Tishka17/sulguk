from dataclasses import dataclass

from sulguk.render import State
from .base import Entity


@dataclass
class Text(Entity):
    text: str

    def render(self, state: State) -> None:
        state.canvas.add_text(self.text)

    def add(self, entity: Entity):
        raise ValueError("Text does not supports children")
