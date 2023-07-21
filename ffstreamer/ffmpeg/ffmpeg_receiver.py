# -*- coding: utf-8 -*-

from asyncio import create_subprocess_exec, subprocess
from asyncio.exceptions import CancelledError, IncompleteReadError
from logging import WARNING
from typing import Any, Awaitable, Callable, Optional

from ffstreamer.aio.stream import logging_stream
from ffstreamer.ffmpeg.ffmpeg_process import FFmpegProcess
from ffstreamer.logging.logging import input_logger as logger


class FFmpegReceiver(FFmpegProcess):
    def __init__(
        self,
        frame_buffer_size: int,
        frame_callback: Callable[[Optional[bytes]], Awaitable[Any]],
        *ffmpeg_args,
        ffmpeg_path="ffmpeg",
        frame_logging_step=1000,
    ):
        super().__init__()
        self._frame_buffer_size = frame_buffer_size
        self._frame_callback = frame_callback
        self._ffmpeg_path = ffmpeg_path
        self._ffmpeg_args = ffmpeg_args
        self._frame_logging_step = frame_logging_step
        self._frame_index = 0

    async def open(self) -> None:
        process = await create_subprocess_exec(
            self._ffmpeg_path,
            *self._ffmpeg_args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        logger.info(f"Create ffmpeg receiver subprocess: {process.pid}")
        self.init(process, self._logging_stdout(), self._logging_stderr())

    async def _logging_stdout(self) -> None:
        try:
            logger.debug("Start receiving frames ...")
            while not self.stdout.at_eof():
                buffer = await self.stdout.readexactly(self._frame_buffer_size)
                await self._frame_callback(buffer)
                if self._frame_index % self._frame_logging_step == 0:
                    logger.debug(f"Recv frame #{self._frame_index} ...")
                self._frame_index += 1
        except IncompleteReadError as e:
            logger.exception(f"Remain partial data is {len(e.partial)} bytes")
        except CancelledError:
            logger.debug("Frame reader is cancelled")
        except BaseException as unknown_error:
            logger.exception(unknown_error)
        finally:
            await self._frame_callback(None)
            logger.debug(f"Frame reader is complete: total {self._frame_index}")

    async def _logging_stderr(self) -> None:
        await logging_stream("RECV:ERR", self.stderr, logger, WARNING)
