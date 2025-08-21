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

from sulguk.data import SULGUK_PARSE_MODE
from .wrapper import transform_html

logger = logging.getLogger(__name__)

M = TypeVar("M", bound=TelegramMethod)
Handler = Callable[[M, Bot], None]


class AiogramSulgukMiddleware(BaseRequestMiddleware):
    def __init__(self, base_url: str | None = None) -> None:
        self.handlers: Dict[Type[TelegramMethod], Handler] = {
            EditMessageMedia: self._process_edit_message_media,
            SendMediaGroup: self._process_send_media_group,
            AnswerWebAppQuery: self._process_answer_web_app_query,
            AnswerInlineQuery: self._process_answer_inline_query,
            SendPoll: self._process_send_poll,
        }
        self._base_url = base_url

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
