# -*- coding: utf-8 -*-

from argparse import Namespace
from io import StringIO
from typing import Callable


class DefaultApp:
    def __init__(self, args: Namespace):
        self.ffmpeg_path = args.ffmpeg_path
        self.ffmpeg_inputs = args.i
        self.ffmpeg_outputs = args.o
        self.stream_maps = args.map
        self.debug = args.debug
        self.verbose = args.verbose
        self.module = args.module
        self.opts = args.opts

        assert isinstance(self.ffmpeg_path, str)
        assert isinstance(self.ffmpeg_inputs, list)
        assert isinstance(self.ffmpeg_outputs, list)
        assert isinstance(self.stream_maps, list)
        assert isinstance(self.debug, bool)
        assert isinstance(self.verbose, int)
        assert isinstance(self.module, str)
        assert isinstance(self.opts, list)

    def get_argument_info(self) -> str:
        buffer = StringIO()
        buffer.write("Default Application Arguments:\n")
        buffer.write(f"-ffmpeg_path: '{self.ffmpeg_path}'\n")
        buffer.write(f"-ffmpeg_inputs: {self.ffmpeg_inputs}\n")
        buffer.write(f"-ffmpeg_outputs: {self.ffmpeg_outputs}\n")
        buffer.write(f"-stream_maps: {self.stream_maps}\n")
        buffer.write(f"-debug: {self.debug}\n")
        buffer.write(f"-verbose: {self.verbose}\n")
        buffer.write(f"-module: '{self.module}'\n")
        buffer.write(f"-opts: {self.opts}\n")
        return buffer.getvalue()

    def run(self, printer: Callable[..., None] = print) -> int:
        if self.verbose >= 1:
            printer(self.get_argument_info())

        return 0


def main(args: Namespace, printer: Callable[..., None] = print) -> int:
    return DefaultApp(args).run(printer)
