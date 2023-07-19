# -*- coding: utf-8 -*-

from argparse import Namespace
from asyncio import run as asyncio_run
from asyncio.exceptions import CancelledError
from typing import Callable, List, Optional

from ffstreamer.argparse.argument_utils import argument_splitter
from ffstreamer.ffmpeg.ffmpeg import detect_file_format, inspect_pix_fmts
from ffstreamer.ffmpeg.ffmpeg_receiver import FFmpegReceiver
from ffstreamer.ffmpeg.ffmpeg_sender import FFmpegSender
from ffstreamer.ffmpeg.ffprobe import inspect_source_size
from ffstreamer.logging.logging import logger
from ffstreamer.module.module import Module, module_pipeline_splitter


class DefaultApp:
    _modules: List[Module]

    def __init__(self, args: Namespace):
        assert isinstance(args.ffmpeg_path, str)
        assert isinstance(args.ffprobe_path, str)
        assert isinstance(args.input, str)
        assert isinstance(args.input_channels, int)
        assert isinstance(args.source, str)
        assert isinstance(args.format, str)
        assert isinstance(args.destination, str)
        assert isinstance(args.output, str)
        assert isinstance(args.preview, bool)
        assert isinstance(args.module_prefix, str)
        assert isinstance(args.opts, list)
        assert isinstance(args.debug, bool)
        assert isinstance(args.verbose, int)

        self._ffmpeg_path = args.ffmpeg_path
        self._ffprobe_path = args.ffprobe_path
        self._input_channels = args.input_channels
        self._input = args.input
        self._output = args.output
        self._source = args.source
        self._format = args.format
        self._destination = args.destination
        self._preview = args.preview
        self._module_prefix = args.module_prefix
        self._opts = args.opts
        self._debug = args.debug
        self._verbose = args.verbose

        self._pix_fmts = inspect_pix_fmts(self._ffmpeg_path)

        if self._format.lower() == "auto":
            self._format = detect_file_format(self._destination, self._ffmpeg_path)

        logger.debug(f"Inspect the source size '{self._source}' ...")
        w, h = inspect_source_size(self._source, self._ffprobe_path)
        self._source_video_width = w
        self._source_video_height = h
        self._frame_buffer_size = w * h * self._input_channels
        self._frame_logging_step = 100

        args_kwargs = dict(
            src=self._source,
            width=self._source_video_width,
            height=self._source_video_height,
            format=self._format,
            dest=self._destination,
        )
        self._recv_arguments = argument_splitter(self._input, **args_kwargs)
        self._send_arguments = argument_splitter(self._output, **args_kwargs)

        self._module_pipeline_args = module_pipeline_splitter(*self._opts)
        self._modules = list()

        self._receiver = FFmpegReceiver(
            self._frame_buffer_size,
            self.on_buffing,
            *self._recv_arguments,
            ffmpeg_path=self._ffmpeg_path,
            frame_logging_step=self._frame_logging_step,
        )
        self._sender = FFmpegSender(
            *self._send_arguments,
            ffmpeg_path=self._ffmpeg_path,
        )

        logger.info(f"FFmpeg path: '{self._ffmpeg_path}'")
        logger.info(f"FFprobe path: '{self._ffprobe_path}'")
        logger.info(f"Frame buffer size is {self._frame_buffer_size} bytes")
        logger.info(f"The source size is {w}x{h}")
        logger.info(f"FFmpeg receiver arguments: {self._recv_arguments}")
        logger.info(f"FFmpeg sender arguments: {self._send_arguments}")
        logger.info(f"Preview flag: {self._preview}")
        logger.info(f"Module prefix: '{self._module_prefix}'")
        logger.info(f"Module pipeline: {self._module_pipeline_args}")
        logger.info(f"Debug flag: {self._debug}")
        logger.info(f"Verbose level: {self._verbose}")

    def init_modules(self) -> None:
        for module_pipeline in self._module_pipeline_args:
            module_name = self._module_prefix + module_pipeline[0]
            module_args = module_pipeline[1:]

            logger.debug(f"Initialize module '{module_name}' -> {module_args}")
            self._modules.append(Module(module_name, *module_args))
            logger.info(f"Initialized module '{module_name}'")

    def run(self) -> int:
        self.init_modules()

        try:
            asyncio_run(self.run_until_complete())
        except KeyboardInterrupt:
            logger.warning("An interrupt signal was detected")
            return 0
        except Exception as e:
            logger.exception(e)
            return 1
        else:
            return 0

    async def on_buffing(self, data: Optional[bytes]) -> None:
        if data is not None:
            buffer = data
            for module in self._modules:
                buffer = await module.frame(buffer)
            self._sender.stdin.write(buffer)
        else:
            await self._sender.stdin.drain()

    async def run_until_complete(self) -> None:
        try:
            for module in self._modules:
                await module.open()
            await self.run_ffmpeg_subprocess()
        except CancelledError:
            logger.debug("An cancelled signal was detected")
        finally:
            for module in self._modules:
                await module.close()

    async def run_ffmpeg_subprocess(self) -> None:
        await self._receiver.open()
        await self._sender.open()

        await self._receiver.wait()
        await self._sender.stdin.drain()

        self._sender.interrupt()
        await self._sender.wait()


def main(args: Namespace, printer: Callable[..., None] = print) -> int:
    assert printer is not None
    return DefaultApp(args).run()
