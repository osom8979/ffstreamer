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
    with_apis=False,
) -> str:
    buffer = StringIO()

    for module_name in module_names:
        module = Module(module_prefix + module_name, isolate=True)
        version = module.version
        doc = module.doc

        buffer.write(module_name)
        if with_version and version:
            buffer.write(f"-v{version}")

        if with_apis:
            has_on_open = "O" if module.has_on_open else "X"
            has_on_close = "O" if module.has_on_close else "X"
            has_on_frame = "O" if module.has_on_frame else "X"
            buffer.write(f" [open={has_on_open}")
            buffer.write(f",close={has_on_close}")
            buffer.write(f",frame={has_on_frame}]")

        if with_doc and doc:
            buffer.write(" ")
            buffer.write(doc)

        buffer.write("\n")

    return buffer.getvalue().strip()


def print_modules(
    module_prefix=MODULE_NAME_PREFIX,
    verbose=0,
    printer: Callable[..., None] = print,
) -> None:
    module_names: List[str]
    try:
        module_names = find_and_strip_module_prefix(module_prefix)
        module_names = list(filter(lambda x: x, module_names))
    except BaseException as e:
        logger.error(e)
        return

    with_version = verbose >= 1
    with_doc = verbose >= 2
    with_apis = verbose >= 3

    message = _printable_module_information(
        module_names,
        module_prefix,
        with_version,
        with_doc,
        with_apis,
    )

    args = f"with_version={with_version},with_doc={with_doc},with_apis={with_apis}"
    logger.debug(f"List of modules ({args})")

    if message:
        printer(message)
