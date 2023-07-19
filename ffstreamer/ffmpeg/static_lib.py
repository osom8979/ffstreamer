# -*- coding: utf-8 -*-

from copy import deepcopy
from os import environ, path
from typing import Optional

from static_ffmpeg import add_paths, run


class AlreadyEnteredException(Exception):
    def __init__(self):
        super().__init__("The context has already been entered")


class NotEnteredException(Exception):
    def __init__(self):
        super().__init__("The context has not been entered yet.")


class StaticFFmpegPaths:
    _original_path: Optional[str]
    _ffmpeg_path: Optional[str]
    _ffprobe_path: Optional[str]

    def __init__(self):
        self._original_path = None
        self._ffmpeg_path = None
        self._ffprobe_path = None

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    @property
    def entered(self) -> bool:
        return self._original_path is not None

    @property
    def ffmpeg_path(self) -> str:
        return self._ffmpeg_path if self._ffmpeg_path else str()

    @property
    def ffprobe_path(self) -> str:
        return self._ffprobe_path if self._ffprobe_path else str()

    def open(self) -> None:
        if self.entered:
            raise AlreadyEnteredException()

        self._original_path = deepcopy(environ["PATH"])

        add_paths()
        ffmpeg_path, ffprobe_path = run.get_or_fetch_platform_executables_else_raise()
        assert isinstance(ffmpeg_path, str)
        assert isinstance(ffprobe_path, str)
        assert path.isfile(ffmpeg_path)
        assert path.isfile(ffprobe_path)
        self._ffmpeg_path = ffmpeg_path
        self._ffprobe_path = ffprobe_path

    def close(self) -> None:
        if not self.entered:
            raise NotEnteredException()

        assert self._original_path is not None
        environ["PATH"] = self._original_path

        self._original_path = None
        self._ffmpeg_path = None
        self._ffprobe_path = None
