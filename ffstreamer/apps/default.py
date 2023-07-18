# -*- coding: utf-8 -*-

from argparse import Namespace
from asyncio import StreamReader, Task, create_subprocess_exec, create_task, gather
from asyncio import run as asyncio_run
from asyncio import subprocess
from asyncio.exceptions import CancelledError, IncompleteReadError
from logging import INFO, WARNING, Logger
from signal import SIGINT
from typing import Callable, List, Optional

from ffstreamer.ffmpeg.ffprobe import inspect_source_size
from ffstreamer.logging.logging import input_logger, logger, output_logger
from ffstreamer.module.module import Module, module_pipeline_splitter


def argument_splitter(arg: str, **kwargs) -> List[str]:
    result = list()
    for a in arg.format(**kwargs).split():
        stripped_arg = a.strip()
        if stripped_arg:
            result.append(stripped_arg)
    return result


class DefaultApp:
    ffmpeg_input_process: Optional[subprocess.Process]
    ffmpeg_output_process: Optional[subprocess.Process]

    ffmpeg_input_stdout_task: Optional[Task]
    ffmpeg_input_stderr_task: Optional[Task]
    ffmpeg_output_stderr_task: Optional[Task]
    ffmpeg_output_stdout_task: Optional[Task]

    _modules: List[Module]

    def __init__(self, args: Namespace):
        self.ffmpeg_input_process = None
        self.ffmpeg_output_process = None

        self.ffmpeg_input_stdout_task = None
        self.ffmpeg_input_stderr_task = None
        self.ffmpeg_output_stderr_task = None
        self.ffmpeg_output_stdout_task = None

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

        logger.debug(f"Inspect the source size '{self._source}' ...")
        w, h = inspect_source_size(self._source, self._ffprobe_path)
        self._source_video_width = w
        self._source_video_height = h
        self._frame_buffer_size = w * h * self._input_channels

        args_kwargs = dict(
            src=self._source,
            width=self._source_video_width,
            height=self._source_video_height,
            format=self._format,
            dest=self._destination,
        )
        self._input_arguments = argument_splitter(self._input, **args_kwargs)
        self._output_arguments = argument_splitter(self._output, **args_kwargs)

        self._module_pipeline_args = module_pipeline_splitter(*self._opts)
        self._modules = list()

        logger.info(f"FFmpeg path: '{self._ffmpeg_path}'")
        logger.info(f"FFprobe path: '{self._ffprobe_path}'")
        logger.info(f"Frame buffer size is {self._frame_buffer_size} bytes")
        logger.info(f"The source size is {w}x{h}")
        logger.info(f"FFmpeg input arguments: {self._input_arguments}")
        logger.info(f"FFmpeg output arguments: {self._output_arguments}")
        logger.info(f"Preview flag: {self._preview}")
        logger.info(f"Module prefix: '{self._module_prefix}'")
        logger.info(f"Module pipeline: {self._module_pipeline_args}")
        logger.info(f"Debug flag: {self._debug}")
        logger.info(f"Verbose level: {self._verbose}")

    @property
    def input_pid(self) -> int:
        assert self.ffmpeg_input_process is not None
        return self.ffmpeg_input_process.pid

    @property
    def output_pid(self) -> int:
        assert self.ffmpeg_output_process is not None
        return self.ffmpeg_output_process.pid

    def init_modules(self) -> None:
        for module_pipeline in self._module_pipeline_args:
            module_name = self._module_prefix + module_pipeline[0]
            module_args = module_pipeline[1:]

            logger.debug(f"Initialize module '{module_name}' -> {module_args}")
            self._modules.append(Module(module_name, *module_args))
            logger.info(f"Initialized module '{module_name}'")

    def run(self) -> int:
        logger.debug("Initialize modules")
        self.init_modules()
        logger.info("Initialized modules")

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

    async def _read_ffmpeg_input_stdout(self) -> None:
        assert self.ffmpeg_input_process is not None
        stream_reader = self.ffmpeg_input_process.stdout
        assert stream_reader is not None

        frame_index = 0
        frame_index_step = 100

        try:
            input_logger.debug("Start recv frame ...")
            while not stream_reader.at_eof():
                buffer = await stream_reader.readexactly(self._frame_buffer_size)
                for module in self._modules:
                    buffer = await module.frame(buffer)

                # ----------------------------------------------------------------------
                # [WARNING]
                # Don't assert or save to another variable, just use stdin directly!
                self.ffmpeg_output_process.stdin.write(buffer)  # type: ignore[union-attr] # noqa
                # ----------------------------------------------------------------------

                if frame_index % frame_index_step == 0:
                    input_logger.debug(f"Recv frame #{frame_index} ...")
                frame_index += 1
        except IncompleteReadError as e:
            input_logger.exception(f"Remain partial data is {len(e.partial)} bytes")
        except CancelledError:
            input_logger.debug("Frame reader is cancelled")
        except BaseException as unknown_error:
            input_logger.exception(unknown_error)
        finally:
            # --------------------------------------------------------------------------
            # [WARNING]
            # Don't assert or save to another variable, just use stdin directly!
            await self.ffmpeg_output_process.stdin.drain()  # type: ignore[union-attr]
            # --------------------------------------------------------------------------

            input_logger.debug(f"Frame reader is complete: total {frame_index}")

    @staticmethod
    async def _read_stream(
        stream_name: str,
        stream_reader: StreamReader,
        stream_logger: Logger,
        logging_level: int,
    ) -> None:
        try:
            stream_logger.debug(f"Start reading the stream[{stream_name}] ...")
            while not stream_reader.at_eof():
                buff = await stream_reader.readline()
                line = str(buff, encoding="utf-8").rstrip()
                stream_logger.log(logging_level, line)
        except ValueError:
            # limit is reached
            pass
        except CancelledError:
            stream_logger.debug(f"Stream[{stream_name}] is cancelled")
        except BaseException as unknown_error:
            stream_logger.exception(unknown_error)
        finally:
            stream_logger.debug(f"Stream[{stream_name}] read finished.")

    async def _read_ffmpeg_input_stderr(self) -> None:
        assert self.ffmpeg_input_process is not None
        stream_reader = self.ffmpeg_input_process.stderr
        assert stream_reader is not None
        await self._read_stream("Input-Stderr", stream_reader, input_logger, WARNING)

    async def _read_ffmpeg_output_stdout(self) -> None:
        assert self.ffmpeg_output_process is not None
        stream_reader = self.ffmpeg_output_process.stdout
        assert stream_reader is not None
        await self._read_stream("Output-Stdout", stream_reader, output_logger, INFO)

    async def _read_ffmpeg_output_stderr(self) -> None:
        assert self.ffmpeg_output_process is not None
        stream_reader = self.ffmpeg_output_process.stderr
        assert stream_reader is not None
        await self._read_stream("Output-Stderr", stream_reader, output_logger, WARNING)

    async def _open_ffmpeg_input(self) -> None:
        self.ffmpeg_input_process = await create_subprocess_exec(
            self._ffmpeg_path,
            *self._input_arguments,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.ffmpeg_input_stdout_task = create_task(self._read_ffmpeg_input_stdout())
        self.ffmpeg_input_stderr_task = create_task(self._read_ffmpeg_input_stderr())

    async def _open_ffmpeg_output(self) -> None:
        self.ffmpeg_output_process = await create_subprocess_exec(
            self._ffmpeg_path,
            *self._output_arguments,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.ffmpeg_output_stdout_task = create_task(self._read_ffmpeg_output_stdout())
        self.ffmpeg_output_stderr_task = create_task(self._read_ffmpeg_output_stderr())

    async def _wait_ffmpeg_input(self) -> None:
        assert self.ffmpeg_input_process is not None
        assert self.ffmpeg_input_stdout_task is not None
        assert self.ffmpeg_input_stderr_task is not None

        await self.ffmpeg_input_process.wait()
        await gather(self.ffmpeg_input_stdout_task, self.ffmpeg_input_stderr_task)

    async def _wait_ffmpeg_output(self) -> None:
        if self.ffmpeg_output_process is None:
            return

        assert self.ffmpeg_output_process is not None
        assert self.ffmpeg_output_stdout_task is not None
        assert self.ffmpeg_output_stderr_task is not None

        await self.ffmpeg_output_process.wait()
        await gather(self.ffmpeg_output_stdout_task, self.ffmpeg_output_stderr_task)

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
        await self._open_ffmpeg_input()
        logger.info(f"Create FFmpeg input process: {self.input_pid}")

        await self._open_ffmpeg_output()
        logger.info(f"Create FFmpeg output process: {self.output_pid}")

        await self._wait_ffmpeg_input()

        assert self.ffmpeg_output_process is not None
        assert self.ffmpeg_output_process.stdin is not None
        await self.ffmpeg_output_process.stdin.drain()

        self.ffmpeg_output_process.send_signal(SIGINT)
        await self._wait_ffmpeg_output()


def main(args: Namespace, printer: Callable[..., None] = print) -> int:
    assert printer is not None
    return DefaultApp(args).run()
