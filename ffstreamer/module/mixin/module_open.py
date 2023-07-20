# -*- coding: utf-8 -*-

from inspect import iscoroutinefunction

from ffstreamer.module.errors import (
    ModuleCallbackAlreadyStateError,
    ModuleCallbackNotReadyStateError,
    ModuleCallbackRuntimeError,
)
from ffstreamer.module.mixin._module_base import ModuleBase
from ffstreamer.module.variables import NAME_ON_CLOSE, NAME_ON_OPEN


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
    def has_on_close(self) -> bool:
        return self.has(NAME_ON_CLOSE)

    async def on_open(self, *args, **kwargs) -> None:
        if self._opened:
            raise ModuleCallbackAlreadyStateError(self.module_name, NAME_ON_OPEN)

        callback = self.get(NAME_ON_OPEN)

        try:
            if callback is not None:
                if iscoroutinefunction(callback):
                    await callback(*args, **kwargs)
                else:
                    callback(*args, **kwargs)
        except BaseException as e:
            raise ModuleCallbackRuntimeError(self.module_name, NAME_ON_OPEN) from e
        else:
            self._opened = True

    async def on_close(self) -> None:
        if not self._opened:
            raise ModuleCallbackNotReadyStateError(self.module_name, NAME_ON_CLOSE)

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
