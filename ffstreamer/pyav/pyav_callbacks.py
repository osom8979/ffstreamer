# -*- coding: utf-8 -*-

from abc import ABCMeta, abstractmethod

from numpy import ndarray
from overrides import override


class PyavCallbacksInterface(metaclass=ABCMeta):
    @abstractmethod
    async def on_image(self, image: ndarray) -> ndarray:
        raise NotImplementedError


class PyavCallbacks(PyavCallbacksInterface):
    @override
    async def on_image(self, image: ndarray) -> ndarray:
        return image
