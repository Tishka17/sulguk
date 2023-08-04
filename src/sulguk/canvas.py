import re
from enum import Enum, auto


class State(Enum):
    START = auto()
    NEW_LINE = auto()
    EMPTY_LINE = auto()
    SPACE = auto()
    IN_TEXT = auto()


class TextMode(Enum):
    NORMAL = auto()
    PRE = auto()


# carriage return, line feed, tab and space
NORMAL_SPACES = re.compile("[\x0d\x0a\x09\x20]+")
NORMAL_SPACES_START = re.compile("^[\x0d\x0a\x09\x20]+")


def fix_text_normal(text: str) -> str:
    text = NORMAL_SPACES_START.sub("", text)
    return " ".join(NORMAL_SPACES.split(text))


class Canvas:
    def __init__(self):
        self.text = ""
        self.state = State.NEW_LINE
        self.text_mode = TextMode.NORMAL

    def add_space(self):
        if not self.text:
            return
        if self.state != State.IN_TEXT:
            return
        self.text += " "
        self.state = State.SPACE

    def add_new_line_soft(self):
        if not self.text:
            return
        if self.state == State.SPACE:
            self.text = self.text[:-1]
        if self.state in (State.NEW_LINE, State.EMPTY_LINE, State.START):
            return
        self.text += "\n"
        self.state = State.NEW_LINE

    def add_new_line(self):
        if not self.text:
            return
        if self.state == State.SPACE:
            self.text = self.text[:-1]
        self.text += "\n"
        self.state = State.NEW_LINE

    def add_empty_line(self):
        if self.state in (State.EMPTY_LINE, State.START):
            return
        elif self.state == State.NEW_LINE:
            self.text += "\n"
        else:
            self.text += "\n\n"
        self.state = State.EMPTY_LINE

    def add_text(self, text):
        text = fix_text_normal(text)
        if not text:
            return
        self.text += text
        if text.endswith(" "):
            self.text = State.SPACE
        else:
            self.text = State.IN_TEXT
