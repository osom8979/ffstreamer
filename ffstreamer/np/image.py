# -*- coding: utf-8 -*-

from typing import Tuple

from numpy import ndarray, uint8
from numpy.typing import NDArray


def make_image_with_shape(shape: Tuple[int, int, int], data: bytes) -> NDArray[uint8]:
    return ndarray(shape, dtype=uint8, buffer=data)


def make_image(width: int, height: int, channels: int, data: bytes) -> NDArray[uint8]:
    return make_image_with_shape((height, width, channels), data)
