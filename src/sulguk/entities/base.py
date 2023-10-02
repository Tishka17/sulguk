from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional

from sulguk.data import MessageEntity
from sulguk.render import State


class Entity(ABC):
    @abstractmethod
    def add(self, entity: "Entity"):
        raise NotImplementedError

    @abstractmethod
    def render(self, state: State) -> None:
        raise NotImplementedError


@dataclass
class Group(Entity):
    entities: List[Entity] = field(default_factory=list)
    block: bool = False

    def add(self, entity: Entity):
        self.entities.append(entity)

    def render(self, state: State) -> None:
        if self.block:
            state.canvas.add_new_line_soft()
        for entity in self.entities:
            entity.render(state)
        if self.block:
            state.canvas.add_new_line_soft()


@dataclass
class DecoratedEntity(Group):
    @abstractmethod
    def _get_entity(self, offset: int, length: int) -> Optional[MessageEntity]:
        raise NotImplementedError

    def render(self, state: State) -> None:
        offset = state.canvas.size
        super().render(state)
        entity = self._get_entity(offset, state.canvas.size - offset)
        if entity:
            state.entities.append(entity)
