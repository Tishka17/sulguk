import logging
from typing import Any

from aiogram import Bot
from aiogram.client.session.middlewares.base import (
    BaseRequestMiddleware,
    NextRequestMiddlewareType,
)
from aiogram.methods import (
    Response, TelegramMethod, AnswerInlineQuery, AnswerWebAppQuery,
    EditMessageMedia, SendMediaGroup,
)
from aiogram.methods.base import TelegramType
from aiogram.types import InlineQueryResultArticle

from sulguk.data import SULGUK_PARSE_MODE
from .wrapper import transform_html

logger = logging.getLogger(__name__)


class AiogramSulgukMiddleware(BaseRequestMiddleware):
    async def __call__(
            self,
            make_request: NextRequestMiddlewareType[TelegramType],
            bot: "Bot",
            method: TelegramMethod[TelegramType],
    ) -> Response[TelegramType]:
        if type(method) is EditMessageMedia:
            self._process_edit_message_media(method)
        elif type(method) is SendMediaGroup:
            self._process_send_media_group(method)
        elif type(method) is AnswerWebAppQuery:
            self._process_answer_inline_query(method)
        elif type(method) is AnswerInlineQuery:
            self._process_answer_web_app_query(method)
        else:
            self._process_generic(method)
        return await make_request(bot, method)

    def _process_answer_inline_query(self, object: AnswerInlineQuery):
        for result in object.results:
            if type(result) is InlineQueryResultArticle:
                self._transform_text_caption(result.input_message_content)
            else:
                self._transform_text_caption(result)

    def _process_answer_web_app_query(self, object: AnswerWebAppQuery):
        if type(object.result) is InlineQueryResultArticle:
            self._transform_text_caption(object.result.input_message_content)
        else:
            self._transform_text_caption(object.result)

    def _process_edit_message_media(self, object: EditMessageMedia):
        self._transform_text_caption(object.media)

    def _process_send_media_group(self, object: SendMediaGroup):
        for media in object.media:
            self._transform_text_caption(media)

    def _process_generic(self, object: Any):
        self._transform_text_caption(object)

    def _transform_text_caption(self, object: Any):
        if getattr(object, "parse_mode", "") == SULGUK_PARSE_MODE:
            if hasattr(object, "caption"):
                result = transform_html(object.caption)
                object.caption = result.text
                object.caption_entities = result.entities
            elif hasattr(object, "text"):
                result = transform_html(object.text)
                object.text = result.text
                object.entities = result.entities
            else:
                raise ValueError()
            del object.parse_mode
