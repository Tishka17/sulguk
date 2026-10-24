from abc import abstractmethod
from dataclasses import dataclass, field
from typing import Any, ClassVar, Dict, List, Optional

from .base import RichBlock, RichEntity, RichText
from .text import RichTextList


class ButtonAction(RichEntity):
    """What a button does: the field of the button with the same name."""

    kind: ClassVar[str]

    @abstractmethod
    def to_value(self) -> Any:
        raise NotImplementedError

    def to_dict(self) -> Dict[str, Any]:
        return {self.kind: self.to_value()}


@dataclass
class UrlAction(ButtonAction):
    url: str
    kind = "url"

    def to_value(self) -> Any:
        return self.url


@dataclass
class CallbackDataAction(ButtonAction):
    data: str
    kind = "callback_data"

    def to_value(self) -> Any:
        return self.data


@dataclass
class WebAppAction(ButtonAction):
    url: str
    kind = "web_app"

    def to_value(self) -> Any:
        return {"url": self.url}


@dataclass
class LoginUrlAction(ButtonAction):
    url: str
    forward_text: Optional[str] = None
    bot_username: Optional[str] = None
    request_write_access: bool = False
    kind = "login_url"

    def to_value(self) -> Any:
        return self._fields()


@dataclass
class SwitchInlineQueryAction(ButtonAction):
    query: str
    kind = "switch_inline_query"

    def to_value(self) -> Any:
        return self.query


@dataclass
class SwitchInlineQueryCurrentChatAction(SwitchInlineQueryAction):
    kind = "switch_inline_query_current_chat"


@dataclass
class SwitchInlineQueryChosenChatAction(ButtonAction):
    query: str
    allow_user_chats: bool = False
    allow_bot_chats: bool = False
    allow_group_chats: bool = False
    allow_channel_chats: bool = False
    kind = "switch_inline_query_chosen_chat"

    def to_value(self) -> Any:
        # the query is sent even when it is empty
        return {**self._fields(), "query": self.query}


@dataclass
class CopyTextAction(ButtonAction):
    text: str
    kind = "copy_text"

    def to_value(self) -> Any:
        return {"text": self.text}


@dataclass
class DisabledAction(ButtonAction):
    kind = "disabled"

    def to_value(self) -> Any:
        return {}


@dataclass
class Button(RichEntity):
    text: RichTextList
    action: ButtonAction
    style: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {"text": self.text.to_dict()}
        if self.style:
            result["style"] = self.style
        result.update(self.action.to_dict())
        return result


@dataclass
class ButtonText(RichText):
    """A button inside of a text."""

    button: Button

    def to_dict(self) -> Dict[str, Any]:
        return {"type": "button", "button": self.button.to_dict()}

    def length(self) -> int:
        return 0


@dataclass
class ButtonRowBlock(RichBlock):
    buttons: List[Button] = field(default_factory=list)
    align: Optional[str] = None
    type = "buttons"
