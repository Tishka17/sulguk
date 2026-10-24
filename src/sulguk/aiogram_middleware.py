import logging
from typing import Any, Callable, Dict, Type, TypeVar

from aiogram import Bot
from aiogram.client.default import Default
from aiogram.client.session.middlewares.base import (
    BaseRequestMiddleware,
    NextRequestMiddlewareType,
)
from aiogram.methods import (
    AnswerInlineQuery,
    AnswerWebAppQuery,
    EditMessageMedia,
    EditMessageText,
    Response,
    SendMediaGroup,
    SendPoll,
    TelegramMethod,
)
from aiogram.methods.base import TelegramType
from aiogram.types import (
    InlineQueryResult,
    InlineQueryResultArticle,
)

try:
    from aiogram.methods import AnswerGuestQuery
except ImportError:
    class AnswerGuestQuery(TelegramMethod):
        pass

try:
    from aiogram.methods import SendMessageDraft
except ImportError:
    class SendMessageDraft(TelegramMethod):
        pass

try:
    from aiogram.types import InputRichMessage

    from .rich.message import SulgukRichMessage
except ImportError:  # aiogram without rich messages
    class SulgukRichMessage:  # type: ignore[no-redef]
        pass

    InputRichMessage = None  # type: ignore[assignment,misc]

from sulguk.data import RICH_FORMATS, SULGUK_PARSE_MODE, RichFormat
from .rich import transform_rich_blocks, transform_rich_html
from .wrapper import transform_html

logger = logging.getLogger(__name__)

M = TypeVar("M", bound=TelegramMethod)
Handler = Callable[[M, Bot], None]

RICH_MIN_AIOGRAM = "3.31"


def _rich_methods(required: bool) -> tuple:
    """Rich message methods.

    Without the support in aiogram fails only if ``required``.
    """
    try:
        from aiogram.methods import (
            EditEphemeralMessageText,
            SendRichMessage,
            SendRichMessageDraft,
        )
    except ImportError as e:
        if not required:
            return ()
        raise ImportError(
            "Rich messages are not supported by the installed aiogram, "
            f"aiogram>={RICH_MIN_AIOGRAM} is required",
        ) from e
    return SendRichMessage, SendRichMessageDraft, EditEphemeralMessageText


class AiogramSulgukMiddleware(BaseRequestMiddleware):
    def __init__(
            self,
            base_url: str | None = None,
            rich: RichFormat | None = None,
    ) -> None:
        """Create the middleware.

        :param base_url: base for relative links
        :param rich: default format of ``SulgukRichMessage``: ``"html"``
            normalizes the ``html`` field, ``"blocks"`` converts it to
            the ``blocks`` field. ``None`` means ``"html"``. Plain
            ``InputRichMessage`` is always passed as is, ``markdown`` and
            ready ``blocks`` are never changed.
        """
        if rich is not None and rich not in RICH_FORMATS:
            raise ValueError(
                f"Unknown rich format: {rich!r}, "
                f"expected one of {RICH_FORMATS} or None",
            )
        self.handlers: Dict[Type[TelegramMethod], Handler] = {
            EditMessageMedia: self._process_edit_message_media,
            SendMediaGroup: self._process_send_media_group,
            AnswerWebAppQuery: self._process_answer_web_app_query,
            AnswerInlineQuery: self._process_answer_inline_query,
            SendPoll: self._process_send_poll,
            SendMessageDraft: self._process_send_message_draft,
            AnswerGuestQuery: self._process_answer_guest_query,
            # always registered: rich_message must not get a text from
            # the default parse mode
            EditMessageText: self._process_edit_message_text,
        }
        self._base_url = base_url
        self._rich = rich
        for method in _rich_methods(required=rich is not None):
            self.handlers[method] = self._process_rich_method

    async def __call__(
            self,
            make_request: NextRequestMiddlewareType[TelegramType],
            bot: Bot,
            method: TelegramMethod[TelegramType],
    ) -> Response[TelegramType]:
        handler = self.handlers.get(type(method), self._process_generic)
        handler(method, bot)
        return await make_request(bot, method)

    def _transform_rich_message(self, rich_message: Any) -> Any:
        """Process the html of SulgukRichMessage, other fields stay as is.

        A plain InputRichMessage is returned untouched. The result is
        a plain InputRichMessage (InputRichMessage is frozen in aiogram,
        so a new one is built), the sulguk-only ``format`` is dropped.
        """
        if not isinstance(rich_message, SulgukRichMessage):
            return rich_message
        if rich_message.html is None:
            return InputRichMessage(
                **rich_message.model_dump(exclude={"format"}),
            )

        fmt = rich_message.format or self._rich or "html"
        fields = rich_message.model_dump(exclude={"format"})
        if fmt == "blocks":
            result = transform_rich_blocks(
                rich_message.html, base_url=self._base_url,
            )
            # a new model is validated, so blocks become InputRichBlock*
            return InputRichMessage(
                **{**fields, "html": None, "blocks": result.blocks},
            )

        result = transform_rich_html(
            rich_message.html, base_url=self._base_url,
        )
        return InputRichMessage(**{**fields, "html": result.html})

    def _process_rich_method(self, method: Any, bot: Bot) -> None:
        if method.rich_message is not None:
            method.rich_message = self._transform_rich_message(
                method.rich_message,
            )

    def _process_edit_message_text(
            self, method: EditMessageText, bot: Bot,
    ) -> None:
        # getattr: old aiogram has no rich_message in EditMessageText
        rich_message = getattr(method, "rich_message", None)
        if rich_message is None:
            self._transform_text_caption(method, bot)
            return
        # rich_message replaces the text, so Telegram must not get
        # the sulguk parse mode together with it
        if self._is_parse_mode_supported(method, bot):
            method.parse_mode = None
        method.rich_message = self._transform_rich_message(rich_message)

    def _process_inline_query_result(
            self, method: InlineQueryResult, bot: Bot,
    ) -> None:
        if isinstance(method, InlineQueryResultArticle):
            target = method.input_message_content
        else:
            target = method
        rich_message = getattr(target, "rich_message", None)
        if rich_message is not None:
            target.rich_message = self._transform_rich_message(rich_message)
            return
        self._transform_text_caption(target, bot)

    def _process_answer_inline_query(
            self, method: AnswerInlineQuery, bot: Bot,
    ) -> None:
        for result in method.results:
            self._process_inline_query_result(result, bot)

    def _process_answer_web_app_query(
            self, method: AnswerWebAppQuery, bot: Bot,
    ) -> None:
        self._process_inline_query_result(method.result, bot)

    def _process_answer_guest_query(
            self, method: AnswerGuestQuery, bot: Bot,
    ) -> None:
        self._process_inline_query_result(method.result, bot)

    def _process_send_message_draft(
            self, method: SendMessageDraft, bot: Bot,
    ) -> None:
        self._transform_text_caption(method, bot)

    def _process_edit_message_media(
            self, method: EditMessageMedia, bot: Bot,
    ) -> None:
        self._transform_text_caption(method.media, bot)

    def _process_send_media_group(
            self, method: SendMediaGroup, bot: Bot,
    ) -> None:
        for media in method.media:
            self._transform_text_caption(media, bot)

    def _process_send_poll(self, method: SendPoll, bot: Bot):
        self._transform_poll(method, bot)

    def _process_generic(
            self, method: Any, bot: Bot,
    ) -> None:
        self._transform_text_caption(method, bot)

    def _transform_text_caption(
            self, method: Any, bot: Bot,
    ) -> None:
        if not self._is_parse_mode_supported(method, bot):
            return

        if hasattr(method, "caption"):
            result = transform_html(method.caption, base_url=self._base_url)
            method.caption = result.text
            method.caption_entities = result.entities
        elif hasattr(method, "text"):
            result = transform_html(method.text, base_url=self._base_url)
            method.text = result.text
            method.entities = result.entities
        elif hasattr(method, "message_text"):
            result = transform_html(
                method.message_text,
                base_url=self._base_url,
            )
            method.message_text = result.text
            method.entities = result.entities
        else:
            raise ValueError(
                f"Object of type {type(method)} does not have "
                f"a 'caption', 'text' or 'message_text' attribute.",
            )

        method.parse_mode = None

    def _transform_poll(self, method: SendPoll, bot: Bot):
        if not self._is_parse_mode_supported(
                method, bot, "explanation_parse_mode"):
            return

        explanation_result = transform_html(
            method.explanation,
            base_url=self._base_url,
        )
        method.explanation = explanation_result.text
        method.explanation_entities = explanation_result.entities
        method.explanation_parse_mode = None

        if not self._is_parse_mode_supported(
                method, bot, "question_parse_mode"):
            return

        question_result = transform_html(
            method.question,
            base_url=self._base_url,
        )
        method.question = question_result.text
        method.question_entities = question_result.entities
        method.question_parse_mode = None

    def _is_parse_mode_supported(
        self, method: Any, bot: Bot, parse_mode_attr: str = "parse_mode",
    ) -> bool:
        parse_mode = getattr(method, parse_mode_attr, "")
        if isinstance(parse_mode, Default):
            parse_mode = bot.default.parse_mode
        return parse_mode == SULGUK_PARSE_MODE
