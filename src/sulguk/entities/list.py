from dataclasses import dataclass, field
from typing import List, Optional

from sulguk.data import NumberFormat
from sulguk.render import State, int_to_number
from .base import Entity, Group


@dataclass
class ListGroup(Entity):
    entities: List[Entity] = field(default_factory=list)
    numbered: bool = False
    reversed: bool = False
    format: NumberFormat = NumberFormat.DECIMAL
    start: int = 1

    def add(self, entity: Entity):
        self.entities.append(entity)

    def render(self, state: State) -> None:
        state.canvas.add_new_line_soft()
        if self.reversed:
            index = len(self.entities)
            step = -1
        else:
            index = 0
            step = 1
        for entity in self.entities:
            if isinstance(entity, ListItem):
                if entity.value is not None:
                    index = entity.value
                else:
                    index += step

                if self.numbered:
                    index_value = int_to_number(index, self.format)
                    mark = f"{index_value}. "
                else:
                    mark = "• "
                state.canvas.add_text(mark)
            entity.render(state)
            state.canvas.add_new_line_soft()


@dataclass
class ListItem(Group):
    value: Optional[int] = None

    def render(self, state: State) -> None:
        indent = state.canvas.indent
        state.canvas.indent += 1
        super().render(state)
        state.canvas.indent = indent
