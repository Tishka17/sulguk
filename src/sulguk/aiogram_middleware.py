import logging
from typing import Any, Callable, Dict, Type, TypeVar

from aiogram import Bot
from aiogram.client.session.middlewares.base import (
    BaseRequestMiddleware,
    NextRequestMiddlewareType,
)
from aiogram.methods import (
    AnswerInlineQuery,
    AnswerWebAppQuery,
    EditMessageMedia,
    Response,
    SendMediaGroup,
    TelegramMethod,
)
from aiogram.methods.base import TelegramType
from aiogram.types import (
    UNSET_PARSE_MODE,
    InlineQueryResult,
    InlineQueryResultArticle,
)

from sulguk.data import SULGUK_PARSE_MODE
from .wrapper import transform_html

logger = logging.getLogger(__name__)

M = TypeVar("M", bound=TelegramMethod)
Handler = Callable[[M, Bot], None]


class AiogramSulgukMiddleware(BaseRequestMiddleware):
    def __init__(self):
        self.handlers: Dict[Type[TelegramMethod], Handler] = {
            EditMessageMedia: self._process_edit_message_media,
            SendMediaGroup: self._process_send_media_group,
            AnswerWebAppQuery: self._process_answer_web_app_query,
            AnswerInlineQuery: self._process_answer_inline_query,
        }

    async def __call__(
            self,
            make_request: NextRequestMiddlewareType[TelegramType],
            bot: Bot,
            method: TelegramMethod[TelegramType],
    ) -> Response[TelegramType]:
        handler = self.handlers.get(type(method), self._process_generic)
        handler(method, bot)
        return await make_request(bot, method)

    def _process_inline_query_result(
            self, method: InlineQueryResult, bot: Bot,
    ) -> None:
        if isinstance(method, InlineQueryResultArticle):
            target = method.input_message_content
        else:
            target = method
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

    def _process_edit_message_media(
            self, method: EditMessageMedia, bot: Bot,
    ) -> None:
        self._transform_text_caption(method.media, bot)

    def _process_send_media_group(
            self, method: SendMediaGroup, bot: Bot,
    ) -> None:
        for media in method.media:
            self._transform_text_caption(media, bot)

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
            result = transform_html(method.caption)
            method.caption = result.text
            method.caption_entities = result.entities
        elif hasattr(method, "text"):
            result = transform_html(method.text)
            method.text = result.text
            method.entities = result.entities
        elif hasattr(method, "message_text"):
            result = transform_html(method.message_text)
            method.message_text = result.text
            method.entities = result.entities
        else:
            raise ValueError(
                f"Object of type {type(method)} does not have "
                f"a 'caption', 'text' or 'message_text' attribute.",
            )

        method.parse_mode = None

    def _is_parse_mode_supported(self, method: Any, bot: Bot) -> bool:
        parse_mode = getattr(method, "parse_mode", "")
        if parse_mode is UNSET_PARSE_MODE:
            parse_mode = bot.parse_mode
        return parse_mode == SULGUK_PARSE_MODE
