# -*- coding: utf-8 -*-

from argparse import Namespace
from asyncio import get_running_loop
from asyncio import run as asyncio_run
from asyncio.exceptions import CancelledError
from concurrent.futures.thread import ThreadPoolExecutor
from sys import version_info
from typing import Callable, Optional

if version_info >= (3, 11):
    from asyncio import Runner  # type: ignore[attr-defined]

from numpy import ndarray
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
from ffstreamer.pyav.pyav_callbacks import OnImageResult, PyavCallbacksInterface
from ffstreamer.pyav.pyav_manager import PyavManager


class PyavApp(PyavCallbacksInterface):
    _manager: Optional[PyavManager]

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
        frame_logging_step=100,
        use_uvloop=False,
        preview=False,
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

        self._source = source
        self._destination = destination
        self._width = width
        self._height = height
        self._channels = channels
        self._frame_buffer_size = frame_buffer_size
        self._pixel_format = pixel_format
        self._file_format = file_format
        self._queue_size = 8
        self._join_timeout = 8.0
        self._frame_logging_step = frame_logging_step

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
        self._preview = preview
        self._debug = debug
        self._verbose = verbose
        self._manager = None

        logger.info(f"FFmpeg path: '{ffmpeg_path}'")
        logger.info(f"FFprobe path: '{ffprobe_path}'")
        logger.info(f"Frame buffer size is {frame_buffer_size} bytes")
        logger.info(f"Source video size is {width}x{height}")
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

    def run(self) -> int:
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

    async def run_until_complete(self) -> None:
        try:
            for module in self._modules:
                await module.open()
            await self.run_pyav_manager_thread()
        except CancelledError:
            logger.debug("An cancelled signal was detected")
        finally:
            for module in self._modules:
                await module.close()

    async def run_pyav_manager_thread(self) -> None:
        with ThreadPoolExecutor(max_workers=1) as executor:
            loop = get_running_loop()
            self._manager = PyavManager(
                self._source,
                self._destination,
                self._file_format,
                self._width,
                self._height,
                self._channels,
                queue_size=self._queue_size,
                join_timeout=self._join_timeout,
                callbacks=self,
                loop=loop,
            )
            await loop.run_in_executor(executor, self.manager_join_thread)

    def manager_join_thread(self) -> None:
        assert self._manager is not None
        self._manager.start()
        self._manager.join_safe()

    @override
    async def on_image(self, image: ndarray) -> OnImageResult:
        return image


def pyav_main(args: Namespace, printer: Callable[..., None] = print) -> int:
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
    assert isinstance(args.preview, bool)
    assert isinstance(args.debug, bool)
    assert isinstance(args.verbose, int)

    app = PyavApp(
        args.source,
        args.destination,
        *args.opts,
        pixel_format=args.pixel_format,
        file_format=args.file_format,
        ffmpeg_path=args.ffmpeg_path,
        ffprobe_path=args.ffprobe_path,
        module_prefix=args.module_prefix,
        pipe_separator=args.pipe_separator,
        frame_logging_step=100,
        use_uvloop=args.use_uvloop,
        preview=args.preview,
        debug=args.debug,
        verbose=args.verbose,
    )
    return app.run()
