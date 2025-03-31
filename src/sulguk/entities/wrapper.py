from sulguk.entities import Entity
from sulguk.render import State


class Wrapper(Entity):
    def __init__(self, head: Entity, *tree: Entity):
        self.head = head
        self.tail = head
        for item in tree:
            self.add(item)

    def enter(self, entity: "Entity"):
        self.add(entity)
        self.tail = entity

    def add(self, entity: "Entity"):
        self.tail.add(entity)

    def render(self, state: State) -> None:
        return self.head.render(state)
