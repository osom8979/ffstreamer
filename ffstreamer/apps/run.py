# -*- coding: utf-8 -*-

from argparse import Namespace
from asyncio import run as asyncio_run
from asyncio.exceptions import CancelledError
from typing import Callable, Optional

from ffstreamer.argparse.argument_utils import argument_splitter
from ffstreamer.ffmpeg.ffmpeg import (
    AUTOMATIC_DETECT_FILE_FORMAT,
    DEFAULT_FFMPEG_RECV_FORMAT,
    DEFAULT_FFMPEG_SEND_FORMAT,
    DEFAULT_FILE_FORMAT,
    DEFAULT_PIXEL_FORMAT,
    detect_file_format,
    find_bits_per_pixel,
)
from ffstreamer.ffmpeg.ffmpeg_receiver import FFmpegReceiver
from ffstreamer.ffmpeg.ffmpeg_sender import FFmpegSender
from ffstreamer.ffmpeg.ffprobe import inspect_source_size
from ffstreamer.logging.logging import logger
from ffstreamer.module.module import Module, module_pipeline_splitter
from ffstreamer.module.variables import MODULE_NAME_PREFIX, MODULE_PIPE_SEPARATOR


class RunApp:
    def __init__(
        self,
        source: str,
        destination: str,
        *args,
        recv_commandline=DEFAULT_FFMPEG_RECV_FORMAT,
        send_commandline=DEFAULT_FFMPEG_SEND_FORMAT,
        pixel_format=DEFAULT_PIXEL_FORMAT,
        file_format=DEFAULT_FILE_FORMAT,
        ffmpeg_path="ffmpeg",
        ffprobe_path="ffprobe",
        module_prefix=MODULE_NAME_PREFIX,
        pipe_separator=MODULE_PIPE_SEPARATOR,
        frame_logging_step=100,
        preview=False,
        debug=False,
        verbose=0,
    ):
        bits_per_pixel = find_bits_per_pixel(pixel_format, ffmpeg_path)
        if bits_per_pixel % 8 != 0:
            raise ValueError("The pixel format only supports multiples of 8 bits")

        if file_format.lower() == AUTOMATIC_DETECT_FILE_FORMAT:
            file_format = detect_file_format(destination, ffmpeg_path)

        width, height = inspect_source_size(source, ffprobe_path)

        channels = bits_per_pixel // 8
        frame_buffer_size = width * height * channels

        kwargs = dict(
            source=source,
            destination=destination,
            width=width,
            height=height,
            channels=channels,
            frame_buffer_size=frame_buffer_size,
            pixel_format=pixel_format,
            file_format=file_format,
        )

        recv_arguments = argument_splitter(recv_commandline, **kwargs)
        send_arguments = argument_splitter(send_commandline, **kwargs)
        pipelines = module_pipeline_splitter(*args, separator=pipe_separator)

        self._modules = list()
        for pipeline in pipelines:
            module_name = pipeline[0]
            module_args = pipeline[1:]

            if module_name[0] == "@":
                module_path = "ffstreamer.module.defaults." + module_name[1:]
            else:
                module_path = module_prefix + module_name

            logger.debug(f"Initialize module: '{module_name}' -> {module_args}")
            self._modules.append(Module(module_path, *module_args, **kwargs))
            logger.info(f"Initialized module '{module_name}'")

        self._receiver = FFmpegReceiver(
            frame_buffer_size,
            self.on_buffing,
            *recv_arguments,
            ffmpeg_path=ffmpeg_path,
            frame_logging_step=frame_logging_step,
        )
        self._sender = FFmpegSender(
            *send_arguments,
            ffmpeg_path=ffmpeg_path,
        )

        self._preview = preview
        self._debug = debug
        self._verbose = verbose

        logger.info(f"FFmpeg path: '{ffmpeg_path}'")
        logger.info(f"FFprobe path: '{ffprobe_path}'")
        logger.info(f"Frame buffer size is {frame_buffer_size} bytes")
        logger.info(f"Source video size is {width}x{height}")
        logger.info(f"FFmpeg receiver arguments: {recv_arguments}")
        logger.info(f"FFmpeg sender arguments: {send_arguments}")
        logger.info(f"Module prefix: '{module_prefix}'")
        logger.info(f"Pipe separator: '{pipe_separator}'")
        logger.info(f"Module pipeline: {pipelines}")
        logger.info(f"Preview flag: {preview}")
        logger.info(f"Debug flag: {debug}")
        logger.info(f"Verbose level: {verbose}")

    @property
    def preview(self) -> bool:
        return self._preview

    @property
    def debug(self) -> bool:
        return self._debug

    @property
    def verbose(self) -> int:
        return self._verbose

    async def on_buffing(self, data: Optional[bytes]) -> None:
        if data is not None:
            buffer = data
            for i, module in enumerate(self._modules):
                buffer = await module.frame(buffer)
            self._sender.stdin.write(buffer)
        else:
            await self._sender.stdin.drain()

    def run(self) -> int:
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


def run_main(args: Namespace, printer: Callable[..., None] = print) -> int:
    assert printer is not None

    assert isinstance(args.source, str)
    assert isinstance(args.destination, str)
    assert isinstance(args.opts, list)
    assert isinstance(args.recv_commandline, str)
    assert isinstance(args.send_commandline, str)
    assert isinstance(args.pixel_format, str)
    assert isinstance(args.file_format, str)
    assert isinstance(args.ffmpeg_path, str)
    assert isinstance(args.ffprobe_path, str)
    assert isinstance(args.module_prefix, str)
    assert isinstance(args.pipe_separator, str)
    assert isinstance(args.preview, bool)
    assert isinstance(args.debug, bool)
    assert isinstance(args.verbose, int)

    app = RunApp(
        args.source,
        args.destination,
        *args.opts,
        recv_commandline=args.recv_commandline,
        send_commandline=args.send_commandline,
        pixel_format=args.pixel_format,
        file_format=args.file_format,
        ffmpeg_path=args.ffmpeg_path,
        ffprobe_path=args.ffprobe_path,
        module_prefix=args.module_prefix,
        pipe_separator=args.pipe_separator,
        frame_logging_step=100,
        preview=args.preview,
        debug=args.debug,
        verbose=args.verbose,
    )
    return app.run()
