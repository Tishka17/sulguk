from dataclasses import dataclass
from typing import Optional, Union
from urllib.parse import urlparse, parse_qs


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
        except ValueError:
            raise LinkParseError(f"Invalid post id: {path[1]}")
        comment_id_raw = params.get("comment")
        if not comment_id_raw:
            comment_id = None
        elif len(comment_id_raw) == 1:
            try:
                comment_id = int(comment_id_raw[0])
            except ValueError:
                raise LinkParseError(f"Invalid comment id: {path[1]}")
        else:
            raise LinkParseError(f"Cannot parse comment id: {parsed.query}")
        return Link(
            group_id=parse_group_id(path[0]),
            post_id=post_id,
            comment_id=comment_id,
        )
    else:
        raise LinkParseError(f"Invalid path: {parsed.path}")
