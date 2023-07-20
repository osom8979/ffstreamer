# -*- coding: utf-8 -*-

from argparse import Namespace
from typing import Callable

from ffstreamer.ffmpeg.ffmpeg import inspect_pix_fmts


def pixels_main(args: Namespace, printer: Callable[..., None] = print) -> int:
    assert args is not None
    assert printer is not None

    assert isinstance(args.ffmpeg_path, str)

    pixel_formats = inspect_pix_fmts(args.ffmpeg_path)
    for pixel_format in pixel_formats:
        printer(repr(pixel_format))

    return 0
