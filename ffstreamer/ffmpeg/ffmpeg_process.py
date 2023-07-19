# -*- coding: utf-8 -*-

from asyncio import StreamReader, StreamWriter, Task, create_task, gather, subprocess
from signal import SIGINT
from typing import Optional


class FFmpegProcess:
    _process: Optional[subprocess.Process]
    _stdout_task: Optional[Task]
    _stderr_task: Optional[Task]

    def __init__(self):
        self._process = None
        self._stdout_task = None
        self._stderr_task = None

    def init(
        self,
        process: subprocess.Process,
        stdout_callback,
        stderr_callback,
    ) -> None:
        assert process is not None
        assert stdout_callback is not None
        assert stderr_callback is not None
        self._process = process
        self._stdout_task = create_task(stdout_callback)
        self._stderr_task = create_task(stderr_callback)

    @property
    def process(self) -> subprocess.Process:
        assert self._process is not None
        return self._process

    @property
    def stdin(self) -> StreamWriter:
        assert self._process is not None
        assert self._process.stdin is not None
        return self._process.stdin

    @property
    def stdout(self) -> StreamReader:
        assert self._process is not None
        assert self._process.stdout is not None
        return self._process.stdout

    @property
    def stderr(self) -> StreamReader:
        assert self._process is not None
        assert self._process.stderr is not None
        return self._process.stderr

    @property
    def stdout_task(self) -> Task:
        assert self._stdout_task is not None
        return self._stdout_task

    @property
    def stderr_task(self) -> Task:
        assert self._stderr_task is not None
        return self._stderr_task

    @property
    def spawned(self) -> bool:
        if self._process is not None:
            return self._process.returncode is not None
        else:
            return False

    @property
    def pid(self) -> int:
        return self.process.pid

    async def wait(self) -> None:
        await self.process.wait()
        await gather(self.stdout_task, self.stderr_task)

    async def drain(self) -> None:
        await self.stdin.drain()

    def interrupt(self) -> None:
        self.process.send_signal(SIGINT)

    def terminate(self):
        self.process.terminate()

    def kill(self):
        self.process.kill()
