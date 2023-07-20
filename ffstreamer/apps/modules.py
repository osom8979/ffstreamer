# -*- coding: utf-8 -*-

from argparse import Namespace
from typing import Callable

from ffstreamer.module.module_printer import print_modules


def modules_main(args: Namespace, printer: Callable[..., None] = print) -> int:
    assert args is not None
    assert printer is not None

    assert isinstance(args.module_prefix, str)
    assert isinstance(args.verbose, int)

    print_modules(args.module_prefix, args.verbose, printer)

    return 0
