# -*- coding: utf-8 -*-

from io import StringIO
from typing import Callable, List

from ffstreamer.logging.logging import logger
from ffstreamer.module.module import Module, find_and_strip_module_prefix
from ffstreamer.module.variables import MODULE_NAME_PREFIX


def _printable_module_information(
    module_names: List[str],
    module_prefix: str,
    with_version=False,
    with_doc=False,
) -> str:
    buffer = StringIO()

    for module_name in module_names:
        module = Module(module_prefix + module_name, isolate=True)
        version = module.version
        doc = module.doc

        buffer.write(module_name)
        if with_version and version:
            buffer.write(f" ({version})")
        if with_doc and doc:
            buffer.write(f" - {doc}")
        buffer.write("\n")

    return buffer.getvalue().strip()


def print_modules(
    module_prefix=MODULE_NAME_PREFIX,
    verbose=0,
    printer: Callable[..., None] = print,
) -> None:
    module_names = find_and_strip_module_prefix(module_prefix)
    with_version = verbose >= 1
    with_doc = verbose >= 2

    message = _printable_module_information(
        module_names,
        module_prefix,
        with_version,
        with_doc,
    )

    logger.debug(f"List of modules (with_version={with_version},with_doc={with_doc})")

    if message:
        printer(message)
