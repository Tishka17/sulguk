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


def fix_text_normal(text: str, start_line: bool) -> str:
    print("fix_text_normal <-", repr(text))
    if start_line:
        text = NORMAL_SPACES_START.sub("", text)
    text = " ".join(NORMAL_SPACES.split(text))
    print("fix_text_normal ->", repr(text))
    return text


class Canvas:
    def __init__(self):
        self.text = ""
        self.size = 0
        self.state = State.NEW_LINE
        self.text_mode = TextMode.NORMAL

    def _trim_last_space(self):
        if not self.state == State.SPACE:
            return
        self.text = self.text[:-1]
        self.size -= 1

    def _add_text_raw(self, text: str):
        self.text += text
        self.size += len(text.encode("utf-16-le")) // 2

    def add_space(self):
        if not self.text:
            return
        if self.state != State.IN_TEXT:
            return
        self._add_text_raw(" ")
        self.state = State.SPACE

    def add_new_line_soft(self):
        if not self.text:
            return
        self._trim_last_space()
        if self.state in (State.NEW_LINE, State.EMPTY_LINE, State.START):
            return
        self._add_text_raw("\n")
        self.state = State.NEW_LINE

    def add_new_line(self):
        if not self.text:
            return
        self._trim_last_space()
        self._add_text_raw("\n")
        self.state = State.NEW_LINE

    def add_empty_line(self):
        if self.state in (State.EMPTY_LINE, State.START):
            return
        elif self.state == State.NEW_LINE:
            self._add_text_raw("\n")
        else:
            self._add_text_raw("\n\n")
        self.state = State.EMPTY_LINE

    def add_text(self, text):
        text = fix_text_normal(
            text=text,
            start_line=self.state in (State.START, State.NEW_LINE, State.EMPTY_LINE, State.SPACE)
        )
        if not text:
            return
        self._add_text_raw(text)
        if text.endswith(" "):
            self.state = State.SPACE
        else:
            self.state = State.IN_TEXT
