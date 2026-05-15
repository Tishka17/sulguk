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

    def is_whitespace_only(self) -> bool:
        return False

    def render_list_start(self, state: State) -> bool:
        self.render(state)
        return False


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

    def render_list_start(self, state: State) -> bool:
        if not self.block:
            self.render(state)
            return False

        render_list_start_entities(self.entities, state)
        state.canvas.add_new_line_soft()
        return False


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

    def render_list_start(self, state: State) -> bool:
        self.render(state)
        return False


def render_list_start_entities(
    entities: List[Entity],
    state: State,
) -> None:
    first_index = _first_meaningful_index(entities)
    if first_index is None:
        return

    first_entity = entities[first_index]
    flattened = first_entity.render_list_start(state)
    rest = entities[first_index + 1 :]
    if flattened and _first_meaningful_index(rest) is not None:
        state.canvas.add_new_line_soft()

    for entity in rest:
        entity.render(state)


def _first_meaningful_index(entities: List[Entity]) -> Optional[int]:
    for index, entity in enumerate(entities):
        if entity.is_whitespace_only():
            continue
        return index
    return None
