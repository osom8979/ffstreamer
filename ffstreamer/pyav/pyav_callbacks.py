# -*- coding: utf-8 -*-

from abc import ABCMeta, abstractmethod
from typing import Iterable, Union

from numpy import ndarray, uint8
from numpy.typing import NDArray
from overrides import override

ImageArray = NDArray[uint8]
OnImageResult = Union[ImageArray, Iterable[ImageArray]]


class PyavCallbacksInterface(metaclass=ABCMeta):
    @abstractmethod
    async def on_image(self, image: ndarray) -> OnImageResult:
        raise NotImplementedError


class PyavCallbacks(PyavCallbacksInterface):
    @override
    async def on_image(self, image: ndarray) -> OnImageResult:
        return image
