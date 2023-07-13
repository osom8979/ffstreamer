# -*- coding: utf-8 -*-

from argparse import Namespace
from io import StringIO
from typing import Callable


class DefaultApp:
    def __init__(self, args: Namespace):
        self.ffmpeg_path = args.ffmpeg_path
        self.ffprobe_path = args.ffprobe_path
        self.ffmpeg_inputs = args.i
        self.ffmpeg_outputs = args.o
        self.stream_maps = args.map
        self.debug = args.debug
        self.verbose = args.verbose
        self.module_name = args.module
        self.opts = args.opts

        assert isinstance(self.ffmpeg_path, str)
        assert isinstance(self.ffprobe_path, str)
        assert isinstance(self.ffmpeg_inputs, list)
        assert isinstance(self.ffmpeg_outputs, list)
        assert isinstance(self.stream_maps, list)
        assert isinstance(self.debug, bool)
        assert isinstance(self.verbose, int)
        assert isinstance(self.module_name, str)
        assert isinstance(self.opts, list)

    def get_argument_info(self) -> str:
        buffer = StringIO()
        buffer.write("Default Application Arguments:")
        buffer.write(f"\n - FFmpeg path: '{self.ffmpeg_path}'")
        buffer.write(f"\n - FFprobe path: '{self.ffprobe_path}'")
        buffer.write(f"\n - FFmpeg input commands: {self.ffmpeg_inputs}")
        buffer.write(f"\n - Ffmpeg output commands: {self.ffmpeg_outputs}")
        buffer.write(f"\n - Stream maps: {self.stream_maps}")
        buffer.write(f"\n - Debug flag: {self.debug}")
        buffer.write(f"\n - Verbose level: {self.verbose}")
        buffer.write(f"\n - Module name: '{self.module_name}'")
        buffer.write(f"\n - Module arguments: {self.opts}")
        return buffer.getvalue()

    def run(self, printer: Callable[..., None] = print) -> int:
        if self.verbose >= 1:
            printer(self.get_argument_info())

        return 0


def main(args: Namespace, printer: Callable[..., None] = print) -> int:
    return DefaultApp(args).run(printer)
