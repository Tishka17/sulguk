from dataclasses import dataclass

from sulguk.render import State
from .base import Entity


@dataclass
class Stub(Entity):
    def add(self, entity: "Entity"):
        pass

    def render(self, state: State) -> None:
        pass
