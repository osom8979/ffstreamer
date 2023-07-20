# -*- coding: utf-8 -*-

from argparse import Namespace
from typing import Callable

from ffstreamer.ffmpeg.ffmpeg import inspect_file_formats


def files_main(args: Namespace, printer: Callable[..., None] = print) -> int:
    assert args is not None
    assert printer is not None

    assert isinstance(args.ffmpeg_path, str)

    file_formats = inspect_file_formats(args.ffmpeg_path)
    for file_format in file_formats:
        printer(repr(file_format))

    return 0
