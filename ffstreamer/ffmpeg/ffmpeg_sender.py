# -*- coding: utf-8 -*-

from asyncio import create_subprocess_exec, subprocess
from logging import INFO, WARNING

from ffstreamer.aio.stream import logging_stream
from ffstreamer.ffmpeg.ffmpeg_process import FFmpegProcess
from ffstreamer.logging.logging import output_logger as logger


class FFmpegSender(FFmpegProcess):
    def __init__(
        self,
        *ffmpeg_args,
        ffmpeg_path="ffmpeg",
    ):
        super().__init__()
        self._ffmpeg_path = ffmpeg_path
        self._ffmpeg_args = ffmpeg_args

    async def open(self) -> None:
        process = await create_subprocess_exec(
            self._ffmpeg_path,
            *self._ffmpeg_args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        logger.info(f"Create ffmpeg sender subprocess: {process.pid}")
        self.init(process, self._logging_stdout(), self._logging_stderr())

    async def _logging_stdout(self) -> None:
        await logging_stream("SEND:OUT", self.stdout, logger, INFO)

    async def _logging_stderr(self) -> None:
        await logging_stream("SEND:ERR", self.stderr, logger, WARNING)
