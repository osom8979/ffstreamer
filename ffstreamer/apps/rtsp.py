# -*- coding: utf-8 -*-

from argparse import Namespace
from asyncio import run as asyncio_run
from asyncio.exceptions import CancelledError
from sys import version_info
from typing import Callable

if version_info >= (3, 11):
    from asyncio import Runner  # type: ignore[attr-defined]

from numpy import uint8
from numpy.typing import NDArray
from overrides import override
from uvloop import install as uvloop_install
from uvloop import new_event_loop as uvloop_new_event_loop

from ffstreamer.ffmpeg.ffmpeg import (
    AUTOMATIC_DETECT_FILE_FORMAT,
    DEFAULT_FILE_FORMAT,
    DEFAULT_PIXEL_FORMAT,
    detect_file_format,
    find_bits_per_pixel,
)
from ffstreamer.ffmpeg.ffprobe import inspect_source_size
from ffstreamer.logging.logging import logger
from ffstreamer.module.module import Module, module_pipeline_splitter
from ffstreamer.module.variables import MODULE_NAME_PREFIX, MODULE_PIPE_SEPARATOR
from ffstreamer.pyav.pyav_simple_rtsp_io import PyavSimpleRtspIo


class RtspApp(PyavSimpleRtspIo):
    def __init__(
        self,
        source: str,
        destination: str,
        *args,
        pixel_format=DEFAULT_PIXEL_FORMAT,
        file_format=DEFAULT_FILE_FORMAT,
        ffmpeg_path="ffmpeg",
        ffprobe_path="ffprobe",
        module_prefix=MODULE_NAME_PREFIX,
        pipe_separator=MODULE_PIPE_SEPARATOR,
        use_uvloop=False,
        debug=False,
        verbose=0,
    ):
        bits_per_pixel = find_bits_per_pixel(pixel_format, ffmpeg_path)
        if bits_per_pixel % 8 != 0:
            raise ValueError("The pixel format only supports multiples of 8 bits")

        if file_format.lower() == AUTOMATIC_DETECT_FILE_FORMAT.lower():
            file_format = detect_file_format(destination, ffmpeg_path)

        width, height = inspect_source_size(source, ffprobe_path)
        channels = bits_per_pixel // 8
        frame_buffer_size = width * height * channels

        super().__init__(source, destination, file_format)

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

        self._use_uvloop = use_uvloop
        self._debug = debug
        self._verbose = verbose

        logger.info(f"FFmpeg path: '{ffmpeg_path}'")
        logger.info(f"FFprobe path: '{ffprobe_path}'")
        logger.info(f"Frame buffer size is {frame_buffer_size} bytes")
        logger.info(f"Source video size is {width}x{height}")
        logger.info(f"Module prefix: '{module_prefix}'")
        logger.info(f"Pipe separator: '{pipe_separator}'")
        logger.info(f"Module pipeline: {pipelines}")
        logger.info(f"Debug flag: {debug}")
        logger.info(f"Verbose level: {verbose}")

    @property
    def debug(self) -> bool:
        return self._debug

    @property
    def verbose(self) -> int:
        return self._verbose

    def run(self) -> int:
        self.open_rtsp()
        try:
            if self._use_uvloop:
                if version_info >= (3, 11):
                    with Runner(loop_factory=uvloop_new_event_loop) as runner:
                        runner.run(self.run_until_complete())
                else:
                    uvloop_install()
                    asyncio_run(self.run_until_complete())
            else:
                asyncio_run(self.run_until_complete())
        except KeyboardInterrupt:
            logger.warning("An interrupt signal was detected")
            return 0
        except Exception as e:
            logger.exception(e)
            return 1
        else:
            return 0
        finally:
            self.close_rtsp()

    async def run_until_complete(self) -> None:
        try:
            for module in self._modules:
                await module.open()
            await self.run_rtsp()
        except CancelledError:
            logger.debug("An cancelled signal was detected")
        finally:
            for module in self._modules:
                if module.opened:
                    await module.close()

    @override
    async def on_image(self, image: NDArray[uint8]) -> NDArray[uint8]:
        buffer = image
        for module in self._modules:
            buffer = module.frame_sync(buffer)
        return buffer


def rtsp_main(args: Namespace, printer: Callable[..., None] = print) -> int:
    assert printer is not None

    assert isinstance(args.source, str)
    assert isinstance(args.destination, str)
    assert isinstance(args.opts, list)
    assert isinstance(args.pixel_format, str)
    assert isinstance(args.file_format, str)
    assert isinstance(args.ffmpeg_path, str)
    assert isinstance(args.ffprobe_path, str)
    assert isinstance(args.module_prefix, str)
    assert isinstance(args.pipe_separator, str)
    assert isinstance(args.use_uvloop, bool)
    assert isinstance(args.debug, bool)
    assert isinstance(args.verbose, int)

    app = RtspApp(
        args.source,
        args.destination,
        *args.opts,
        pixel_format=args.pixel_format,
        file_format=args.file_format,
        ffmpeg_path=args.ffmpeg_path,
        ffprobe_path=args.ffprobe_path,
        module_prefix=args.module_prefix,
        pipe_separator=args.pipe_separator,
        use_uvloop=args.use_uvloop,
        debug=args.debug,
        verbose=args.verbose,
    )
    return app.run()
