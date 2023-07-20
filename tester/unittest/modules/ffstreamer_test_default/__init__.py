# -*- coding: utf-8 -*-

__version__ = "0.0.0"
__doc__ = "Documentation"


async def on_open(*args) -> None:
    assert isinstance(args, list)


async def on_frame(data):
    pass


async def on_close() -> None:
    pass
