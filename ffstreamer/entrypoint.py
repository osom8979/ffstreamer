# -*- coding: utf-8 -*-

from sys import exit as sys_exit
from typing import Callable, List, Optional

from ffstreamer.apps.default import main as default_main
from ffstreamer.arguments import get_default_arguments
from ffstreamer.logging.logging import (
    SEVERITY_NAME_DEBUG,
    logger,
    set_colored_formatter_logging_config,
    set_root_level,
    set_simple_logging_config,
)
from ffstreamer.module.module_printer import print_modules


def main(
    cmdline: Optional[List[str]] = None,
    printer: Callable[..., None] = print,
) -> int:
    args = get_default_arguments(cmdline)

    if args.colored_logging and args.simple_logging:
        printer("The 'colored_logging' and 'simple_logging' flags cannot coexist")
        return 1

    colored_logging = args.colored_logging
    simple_logging = args.simple_logging
    severity = args.severity
    debug = args.debug
    verbose = args.verbose

    assert isinstance(colored_logging, bool)
    assert isinstance(simple_logging, bool)
    assert isinstance(severity, str)
    assert isinstance(debug, bool)
    assert isinstance(verbose, int)

    if colored_logging:
        set_colored_formatter_logging_config()
    elif simple_logging:
        set_simple_logging_config()

    if debug:
        set_root_level(SEVERITY_NAME_DEBUG)
    else:
        set_root_level(severity)

    logger.debug(f"Arguments: {args}")

    module_prefix = args.module_prefix
    module_list = args.list
    assert isinstance(module_prefix, str)
    assert isinstance(module_list, bool)

    if module_list:
        print_modules(module_prefix, verbose, printer)
        return 0

    try:
        return default_main(args, printer=printer)
    except BaseException as e:
        logger.exception(e)
        return 1


if __name__ == "__main__":
    sys_exit(main())
