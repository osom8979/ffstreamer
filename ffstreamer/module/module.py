# -*- coding: utf-8 -*-

from typing import List

from ffstreamer.module.mixin.module_doc import ModuleDoc
from ffstreamer.module.mixin.module_open import ModuleOpen
from ffstreamer.module.mixin.module_version import ModuleVersion
from ffstreamer.module.variables import MODULE_NAME_PREFIX
from ffstreamer.package.package_utils import filter_module_names


class Module(
    ModuleDoc,
    ModuleOpen,
    ModuleVersion,
):
    def __init__(self, module_name: str, isolate=False):
        self._module = self.import_module(module_name, isolate=isolate)


def find_and_strip_module_prefix(prefix=MODULE_NAME_PREFIX) -> List[str]:
    modules = filter_module_names(prefix)
    module_name_begin = len(prefix)
    return list(map(lambda x: x[module_name_begin:].strip(), modules))
