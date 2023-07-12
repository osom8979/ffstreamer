# -*- coding: utf-8 -*-

from argparse import Namespace
from typing import Callable


def default_main(args: Namespace, printer: Callable[..., None] = print) -> int:
    assert args is not None
    assert printer is not None

    debug = args.debug
    verbose = args.verbose

    assert isinstance(debug, bool)
    assert isinstance(verbose, int)

    return 0
