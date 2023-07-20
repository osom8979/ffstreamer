# -*- coding: utf-8 -*-

import os
from importlib import import_module
from pkgutil import ModuleInfo, iter_modules
from types import ModuleType
from typing import List, Optional, Sequence

from ffstreamer.regex.access_filter import UnionPattern, access_filter


def get_module_directory(module: ModuleType) -> str:
    module_path = getattr(module, "__path__", None)
    if module_path:
        assert isinstance(module_path, list)
        return module_path[0]

    module_file = getattr(module, "__file__", None)
    if module_file:
        assert isinstance(module_file, str)
        return os.path.dirname(module_file)

    raise RuntimeError(f"The '{module.__name__}' module path is unknown")


def list_submodules(module: ModuleType) -> List[ModuleInfo]:
    module_path = getattr(module, "__path__")
    if module_path:
        return [submodule for submodule in iter_modules(module_path)]
    raise RuntimeError(f"'{module.__name__}' does not have attribute `__path__`")


def list_submodule_names(module: ModuleType) -> List[str]:
    return [m.name for m in list_submodules(module)]


def list_submodule_names_with_module_path(module_path: str) -> List[str]:
    return list_submodule_names(import_module(module_path))


def all_module_names() -> List[str]:
    return [m.name for m in iter_modules()]


def startswith_module_names(prefix: str) -> List[str]:
    return [m.name for m in iter_modules() if m.name.startswith(prefix)]


def startswith_module_names_with_module_prefix(module_prefix: str) -> List[str]:
    if module_prefix.endswith("."):
        submodules = list_submodule_names_with_module_path(module_prefix[0:-1])
        return list(map(lambda x: module_prefix + x, submodules))
    else:
        last_dot_index = module_prefix.rfind(".")
        if last_dot_index == -1:
            return startswith_module_names(module_prefix)
        else:
            module_prefix_tail_begin = last_dot_index + 1
            module_prefix_head = module_prefix[:last_dot_index]
            module_prefix_tail = module_prefix[module_prefix_tail_begin:]
            submodules = list_submodule_names_with_module_path(module_prefix_head)
            return list(
                map(
                    lambda x: f"{module_prefix_head}.{x}",
                    filter(
                        lambda x: x.startswith(module_prefix_tail),
                        submodules,
                    ),
                ),
            )


def filter_module_names(
    prefix: str,
    denies: Optional[Sequence[UnionPattern]] = None,
    allows: Optional[Sequence[UnionPattern]] = None,
) -> List[str]:
    return access_filter(
        names=startswith_module_names_with_module_prefix(prefix),
        denies=denies,
        allows=allows,
    )
