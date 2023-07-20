# -*- coding: utf-8 -*-

import numpy as np

__version__ = "1.0.0"
__doc__ = "bytes to ndarray converter"


class Context:
    width: int
    height: int
    channels: int

    def open(self, *args, **kwargs) -> None:
        assert args is not None
        assert kwargs is not None
        self.width = kwargs["width"]
        self.height = kwargs["height"]
        self.channels = kwargs["channels"]
        print(self.height, self.width, self.channels)

    def frame(self, data: bytes) -> np.ndarray:
        return np.frombuffer(data, dtype=np.uint8).reshape(
            [self.height, self.width, self.channels]
        )


context = Context()


def on_open(*args, **kwargs) -> None:
    context.open(*args, **kwargs)


def on_frame(data: bytes) -> np.ndarray:
    return context.frame(data)
