from dataclasses import dataclass
from typing import Optional, Union
from urllib.parse import parse_qs, urlparse

from aiogram.types import Chat, Message


@dataclass
class Link:
    group_id: Union[str, int]
    post_id: Optional[int] = None
    comment_id: Optional[int] = None


class LinkParseError(ValueError):
    pass


def parse_group_id(group_id: str) -> Union[int, str]:
    try:
        return int(group_id)
    except ValueError:
        if group_id.startswith("@"):
            return group_id
        return "@" + group_id


def parse_link(link: str) -> Link:
    if not link.startswith("https://"):
        return Link(group_id=parse_group_id(link))
    parsed = urlparse(link)
    if parsed.scheme != "https":
        raise LinkParseError(f"Invalid scheme: {parsed.scheme}")
    if parsed.hostname != "t.me":
        raise LinkParseError(f"Invalid hostname: {parsed.hostname}")
    path = parsed.path[1:].split("/")  # remove starting /
    if len(path) == 1:
        return Link(parse_group_id(path[0]))
    elif len(path) == 2:
        params = parse_qs(parsed.query)
        try:
            post_id = int(path[1])
        except ValueError as e:
            raise LinkParseError(f"Invalid post id: {path[1]}") from e
        comment_id_raw = params.get("comment")
        if not comment_id_raw:
            comment_id = None
        elif len(comment_id_raw) == 1:
            try:
                comment_id = int(comment_id_raw[0])
            except ValueError as e:
                raise LinkParseError(f"Invalid comment id: {path[1]}") from e
        else:
            raise LinkParseError(f"Cannot parse comment id: {parsed.query}")
        return Link(
            group_id=parse_group_id(path[0]),
            post_id=post_id,
            comment_id=comment_id,
        )
    else:
        raise LinkParseError(f"Invalid path: {parsed.path}")


def unparse_link(link: Link) -> str:
    if isinstance(link.group_id, str):
        group_id = link.group_id.lstrip("@")
    else:
        group_id = link.group_id
    result = f"https://t.me/{group_id}/"
    if link.post_id:
        result += f"{link.post_id}"
    if link.comment_id:
        result += f"?comment={link.comment_id}"
    return result


def make_link(
        chat: Chat,
        message: Optional[Message] = None,
        comment: Optional[Message] = None,
) -> Link:
    link = Link(
        group_id=chat.username,
    )
    if message:
        link.post_id = message.message_id
    if comment:
        link.comment_id = comment.message_id
    return link
