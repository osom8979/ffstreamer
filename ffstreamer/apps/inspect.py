# -*- coding: utf-8 -*-

from argparse import Namespace
from json import dumps
from typing import Callable

from ffstreamer.ffmpeg.ffprobe import inspect_source


def inspect_main(args: Namespace, printer: Callable[..., None] = print) -> int:
    assert args is not None
    assert printer is not None

    assert isinstance(args.source, str)
    assert isinstance(args.ffprobe_path, str)

    inspect_result = inspect_source(args.source, args.ffprobe_path)
    printer(dumps(inspect_result, indent=2))

    return 0
