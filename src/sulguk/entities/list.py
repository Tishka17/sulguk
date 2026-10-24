from dataclasses import dataclass, field
from typing import List, Optional

from sulguk.data import NumberFormat
from sulguk.render import State, int_to_number
from .base import Entity, Group, render_list_start_entities


@dataclass
class ListGroup(Entity):
    entities: List[Entity] = field(default_factory=list)
    numbered: bool = False
    reversed: bool = False
    format: NumberFormat = NumberFormat.DECIMAL
    start: Optional[int] = None

    def add(self, entity: Entity):
        self.entities.append(entity)

    def _first_number(self) -> int:
        if self.start is not None:
            return self.start
        if self.reversed:
            return sum(isinstance(e, ListItem) for e in self.entities)
        return 1

    def render(self, state: State) -> None:
        state.canvas.add_new_line_soft()
        number = self._first_number()
        step = -1 if self.reversed else 1
        for entity in self.entities:
            if isinstance(entity, ListItem):
                if entity.value is not None:
                    number = entity.value

                if self.numbered:
                    index_value = int_to_number(number, self.format)
                    mark = f"{index_value}. "
                else:
                    mark = "• "
                state.canvas.add_text(mark)
                number += step
            entity.render(state)
            state.canvas.add_new_line_soft()


@dataclass
class ListItem(Group):
    value: Optional[int] = None

    def render(self, state: State) -> None:
        indent = state.canvas.indent
        state.canvas.indent += 1
        try:
            render_list_start_entities(self.entities, state)
        finally:
            state.canvas.indent = indent
