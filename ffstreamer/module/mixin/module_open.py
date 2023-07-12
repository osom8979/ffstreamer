# -*- coding: utf-8 -*-

from inspect import iscoroutinefunction
from typing import Optional

from ffstreamer.module.errors import (
    ModuleCallbackInvalidStateError,
    ModuleCallbackRuntimeError,
)
from ffstreamer.module.mixin._module_base import ModuleBase
from ffstreamer.module.variables import NAME_ON_CLOSE, NAME_ON_FRAME, NAME_ON_OPEN


class ModuleOpen(ModuleBase):
    _opened: bool

    def __new__(cls, *args, **kwargs):
        instance = super().__new__(cls)
        instance._opened = False
        return instance

    @property
    def opened(self) -> bool:
        assert isinstance(self._opened, bool)
        return self._opened

    @property
    def has_on_open(self) -> bool:
        return self.has(NAME_ON_OPEN)

    @property
    def has_on_frame(self) -> bool:
        return self.has(NAME_ON_FRAME)

    @property
    def has_on_close(self) -> bool:
        return self.has(NAME_ON_CLOSE)

    def _raise_invalid_state(self, callback: str, detail: str) -> None:
        raise ModuleCallbackInvalidStateError(self.module_name, callback, detail)

    async def on_open(self) -> None:
        if self._opened:
            self._raise_invalid_state(NAME_ON_OPEN, "Already opened")

        callback = self.get(NAME_ON_OPEN)

        try:
            if callback is not None:
                if iscoroutinefunction(callback):
                    await callback()
                else:
                    callback()
        except BaseException as e:
            raise ModuleCallbackRuntimeError(self.module_name, NAME_ON_OPEN) from e
        else:
            self._opened = True

    async def on_frame(self, pipe: str, data: bytes) -> Optional[bytes]:
        if not self._opened:
            self._raise_invalid_state(NAME_ON_FRAME, "Not opened")

        callback = self.get(NAME_ON_FRAME)
        if iscoroutinefunction(callback):
            return await callback(pipe, data)
        else:
            return callback(pipe, data)

    async def on_close(self) -> None:
        if not self._opened:
            self._raise_invalid_state(NAME_ON_CLOSE, "Not opened")

        callback = self.get(NAME_ON_CLOSE)

        try:
            if callback is not None:
                if iscoroutinefunction(callback):
                    await callback()
                else:
                    callback()
        except BaseException as e:
            raise ModuleCallbackRuntimeError(self.module_name, NAME_ON_CLOSE) from e
        finally:
            self._opened = False
