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
from aiogram.types import (
    InlineQueryResultArticle, UNSET_PARSE_MODE
)

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

        handlers = {
            EditMessageMedia: self._process_edit_message_media,
            SendMediaGroup: self._process_send_media_group,
            AnswerWebAppQuery: self._process_answer_web_app_query,
            AnswerInlineQuery: self._process_answer_inline_query
        }

        handler = handlers.get(type(method), self._process_generic)
        handler(method, bot)

        return await make_request(bot, method)

    def _process_inline_query_result(self, result, bot: "Bot"):
        target = result.input_message_content if isinstance(result, InlineQueryResultArticle) else result
        self._transform_text_caption(target, bot)

    def _process_answer_inline_query(self, object: AnswerInlineQuery, bot: "Bot"):
        for result in object.results:
            self._process_inline_query_result(result, bot)

    def _process_answer_web_app_query(self, object: AnswerWebAppQuery, bot: "Bot"):
        self._process_inline_query_result(object.result, bot)

    def _process_edit_message_media(self, object: EditMessageMedia, bot: "Bot"):
        self._transform_text_caption(object.media, bot)

    def _process_send_media_group(self, object: SendMediaGroup, bot: "Bot"):
        for media in object.media:
            self._transform_text_caption(media, bot)

    def _process_generic(self, object: Any, bot: "Bot"):
        self._transform_text_caption(object, bot)

    def _transform_text_caption(self, object: Any, bot: "Bot"):

        if self._check_pars_mode(object, bot):
            return

        content_attribute = None
        if hasattr(object, "caption"):
            content_attribute = 'caption'
        elif hasattr(object, "text"):
            content_attribute = 'text'

        if not content_attribute:
            raise ValueError("The object does not have a 'caption' or 'text' attribute.")

        original_content = getattr(object, content_attribute)
        transformed_content = transform_html(original_content)

        setattr(object, content_attribute, transformed_content.text)
        setattr(object, "entities", transformed_content.entities)

        object.parse_mode = None

    def _check_pars_mode(self, object: Any, bot: "Bot"):
        parse_mode = getattr(object, "parse_mode", "")
        is_obj_sulguk = parse_mode == SULGUK_PARSE_MODE
        is_bot_unset = bot.parse_mode == SULGUK_PARSE_MODE and parse_mode == UNSET_PARSE_MODE
        return not (is_obj_sulguk or is_bot_unset)
