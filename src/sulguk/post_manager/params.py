from argparse import ArgumentParser
from typing import List, Literal, Union

from .links import Link, parse_link


class SendArgs:
    command: Literal["send"]
    mode: Literal["poll", "getChat"]
    destination: Link
    file: List[str]


class EditArgs:
    command: Literal["edit"]
    destination: Link
    file: str


def init_parser():
    root = ArgumentParser(prog='Sulguk message manager')
    subparsers = root.add_subparsers(dest="command")
    sender = subparsers.add_parser("send")
    sender.add_argument(
        "destination", type=parse_link,
    )
    sender.add_argument(
        "file", nargs='+',
    )
    sender.add_argument(
        "-m", "--mode", choices=["poll", "getChat"],
        default="poll",
    )
    editor = subparsers.add_parser("edit")
    editor.add_argument(
        "destination", type=parse_link,
    )
    editor.add_argument(
        "file",
    )
    return root


def parse_args() -> Union[SendArgs, EditArgs]:
    parser = init_parser()
    return parser.parse_args()
