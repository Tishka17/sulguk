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
    start: Optional[int] = 1

    def add(self, entity: Entity):
        self.entities.append(entity)

    def render(self, state: State) -> None:
        state.canvas.add_new_line_soft()
        step = -1 if self.reversed else 1
        start = self.start
        if start is None:
            if self.reversed:
                start = sum(
                    isinstance(entity, ListItem) for entity in self.entities
                )
            else:
                start = 1
        index = start - step
        for entity in self.entities:
            if isinstance(entity, ListItem):
                if entity.value is not None:
                    index = entity.value
                else:
                    index += step

                if self.numbered:
                    index_value = (
                        int_to_number(index, self.format)
                        if index > 0 else str(index)
                    )
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
        try:
            render_list_start_entities(self.entities, state)
        finally:
            state.canvas.indent = indent
