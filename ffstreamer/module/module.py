# -*- coding: utf-8 -*-

from typing import List

from ffstreamer.module.mixin.module_doc import ModuleDoc
from ffstreamer.module.mixin.module_frame import ModuleFrame
from ffstreamer.module.mixin.module_open import ModuleOpen
from ffstreamer.module.mixin.module_version import ModuleVersion
from ffstreamer.module.variables import MODULE_NAME_PREFIX, MODULE_PIPE_SEPARATOR
from ffstreamer.package.package_utils import filter_module_names


class Module(
    ModuleDoc,
    ModuleFrame,
    ModuleOpen,
    ModuleVersion,
):
    def __init__(self, module_name: str, *args, isolate=False):
        self._module = self.import_module(module_name, isolate=isolate)
        self._args = args

    async def open(self) -> None:
        if not self.has_on_open:
            return
        await self.on_open(*self._args)

    async def close(self) -> None:
        if not self.has_on_close:
            return
        try:
            await self.on_close()
        except BaseException as e:
            self.logger.exception(e)

    async def frame(self, data: bytes) -> bytes:
        if not self.has_on_frame:
            return data
        return await self.on_frame(data)


def find_and_strip_module_prefix(prefix=MODULE_NAME_PREFIX) -> List[str]:
    modules = filter_module_names(prefix)
    module_name_begin = len(prefix)
    return list(map(lambda x: x[module_name_begin:].strip(), modules))


def module_pipeline_splitter(*args, separator=MODULE_PIPE_SEPARATOR) -> List[List[str]]:
    result = list()
    module_and_args: List[str] = list()
    for arg in args:
        if arg == separator:
            result.append(module_and_args)
            module_and_args = list()
        else:
            module_and_args.append(arg)
    return result
