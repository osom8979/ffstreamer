# -*- coding: utf-8 -*-

from asyncio import AbstractEventLoop, get_event_loop, run_coroutine_threadsafe
from multiprocessing import Event as NewEvent
from multiprocessing.synchronize import Event
from typing import Final, Optional, Tuple

from numpy import bool_ as np_bool
from numpy import concatenate, ndarray, uint8, where
from numpy.typing import NDArray

from ffstreamer.memory.spsc_queue import SpscQueue
from ffstreamer.pyav.pyav_callbacks import (
    OnImageResult,
    PyavCallbacks,
    PyavCallbacksInterface,
)
from ffstreamer.pyav.pyav_receiver import create_pyav_receiver_process
from ffstreamer.pyav.pyav_router import create_pyav_router_process
from ffstreamer.pyav.pyav_sender import create_pyav_sender_process

BLACK_COLOR: Final[Tuple[int, int, int]] = (0, 0, 0)
DEFAULT_CHROMA_COLOR: Final[Tuple[int, int, int]] = BLACK_COLOR
CHANNEL_MIN: Final[int] = 0
CHANNEL_MAX: Final[int] = 255


def _create_event() -> Event:
    return NewEvent()


def generate_mask(
    image: NDArray[uint8],
    chroma_color=DEFAULT_CHROMA_COLOR,
) -> NDArray[uint8]:
    assert image.dtype == uint8
    assert len(image.shape) == 3
    assert image.shape[-1] == 3

    channels_cmp: NDArray[np_bool] = image == chroma_color
    pixel_cmp: NDArray[np_bool] = channels_cmp.all(axis=-1, keepdims=True)
    return where(pixel_cmp, CHANNEL_MIN, CHANNEL_MAX)


def merge_to_bgra32(image: NDArray[uint8], mask: NDArray[uint8]) -> NDArray[uint8]:
    assert image.dtype == uint8
    assert len(image.shape) == 3
    assert image.shape[-1] == 3

    assert mask.dtype == uint8
    assert len(mask.shape) == 3
    assert mask.shape[-1] == 1

    return concatenate((image, mask), axis=-1)


class PyavManager:
    def __init__(
        self,
        source: str,
        destination: str,
        file_format: str,
        width: int,
        height: int,
        channels=3,
        chroma_color=DEFAULT_CHROMA_COLOR,
        *,
        queue_size=8,
        join_timeout=8.0,
        callbacks: Optional[PyavCallbacksInterface] = None,
        loop: Optional[AbstractEventLoop] = None,
    ):
        if channels != 3:
            raise ValueError("Only 3 channels are supported")

        self._loop = loop if loop else get_event_loop()
        self._callbacks = callbacks if callbacks else PyavCallbacks()
        self._join_timeout = join_timeout
        self._queue_size = queue_size
        self._chroma_color = chroma_color
        self._shape = height, width, channels
        self._item_size = height * width * channels

        self._overlay_shape = height, width, channels + 1
        self._overlay_mask_shape = height, width, 1
        assert self._overlay_shape[-1] == 4
        self._overlay_item_size = height * width * self._overlay_shape[-1]

        self._receiver = SpscQueue(self._queue_size, self._item_size)
        self._improc = SpscQueue(1, self._item_size)
        self._overlay = SpscQueue(1, self._overlay_item_size)
        self._sender = SpscQueue(self._queue_size, self._item_size)

        receiver_producer = self._receiver.producer
        receiver_consumer = self._receiver.consumer
        improc_producer = self._improc.producer
        # improc_consumer = self._improc.consumer
        # overlay_producer = self._overlay.producer
        overlay_consumer = self._overlay.consumer
        sender_producer = self._sender.producer
        sender_consumer = self._sender.consumer

        self._manager_done = _create_event()
        self._receiver_done = _create_event()
        self._router_done = _create_event()
        self._sender_done = _create_event()

        self._receiver_process = create_pyav_receiver_process(
            source=source,
            receiver_producer=receiver_producer,
            done=self._receiver_done,
        )
        self._router_process = create_pyav_router_process(
            shape=(height, width, channels),
            receiver_consumer=receiver_consumer,
            improc_producer=improc_producer,
            overlay_consumer=overlay_consumer,
            sender_producer=sender_producer,
            done=self._router_done,
        )
        self._sender_process = create_pyav_sender_process(
            destination=destination,
            file_format=file_format,
            shape=(height, width, channels),
            sender_consumer=sender_consumer,
            done=self._sender_done,
        )

    @property
    def improc_consumer(self):
        return self._improc.consumer

    @property
    def overlay_producer(self):
        return self._overlay.producer

    def start(self) -> None:
        self._sender_process.start()
        self._router_process.start()
        self._receiver_process.start()

    def check_process_alive(self) -> None:
        if not self._sender_process.is_alive():
            raise RuntimeError("Sender process is not alive")
        if not self._router_process.is_alive():
            raise RuntimeError("Router process is not alive")
        if not self._receiver_process.is_alive():
            raise RuntimeError("Receiver process is not alive")

    def done(self) -> None:
        self._manager_done.set()
        self._receiver_done.set()
        self._router_done.set()
        self._sender_done.set()

    def join_safe(self) -> None:
        if not self._manager_done.is_set():
            self._manager_done.set()
        if not self._receiver_done.is_set():
            self._receiver_done.set()
        if not self._router_done.is_set():
            self._router_done.set()
        if not self._sender_done.is_set():
            self._sender_done.set()

        self._receiver_process.join(self._join_timeout)
        self._router_process.join(self._join_timeout)
        self._sender_process.join(self._join_timeout)

        if self._receiver_process.is_alive():
            self._receiver_process.kill()
        if self._router_process.is_alive():
            self._router_process.kill()
        if self._sender_process.is_alive():
            self._sender_process.kill()

    def close_pipes(self) -> None:
        self.improc_consumer.close()
        self.overlay_producer.close()

    def split_overlay_and_mask(
        self, image_result: OnImageResult
    ) -> Tuple[NDArray[uint8], NDArray[uint8]]:
        if isinstance(image_result, ndarray):
            if len(image_result.shape) != 3:
                raise ValueError("The shape size of the resulting image should be 3")
            overlay = image_result
            mask = generate_mask(overlay, self._chroma_color)
        elif isinstance(image_result, (tuple, list)):
            if len(image_result) >= 2:
                overlay = image_result[0]
                mask = image_result[1]
            elif len(image_result) == 1:
                overlay = image_result[0]
                mask = generate_mask(overlay, self._chroma_color)
            elif len(image_result) == 0:
                raise TypeError("Empty result list")
            else:
                assert False, "Inaccessible section"
        else:
            raise TypeError(f"Unsupported result type: {type(image_result)}")

        return overlay, mask

    def validate_overlay_and_mask(
        self, overlay: NDArray[uint8], mask: NDArray[uint8]
    ) -> None:
        if not isinstance(overlay, ndarray):
            raise TypeError(f"Overlay type is not NDArray: {type(overlay)}")
        if not isinstance(mask, ndarray):
            raise TypeError(f"Mask type is not NDArray: {type(mask)}")

        if overlay.dtype != uint8:
            raise TypeError(f"Overlay dtype is not uint8: {overlay.dtype}")
        if mask.dtype != uint8:
            raise TypeError(f"Mask dtype is not uint8: {mask.dtype}")

        if overlay.shape != self._overlay_shape:
            raise ValueError(
                "Overlay shape does not match: "
                f"{overlay.shape} != {self._overlay_shape}"
            )
        if mask.shape != self._overlay_mask_shape:
            raise ValueError(
                "Mask shape does not match: "
                f"{mask.shape} != {self._overlay_mask_shape}"
            )

    async def _on_image(self, image: NDArray[uint8]) -> None:
        result = await self._callbacks.on_image(image)
        overlay, mask = self.split_overlay_and_mask(result)
        self.validate_overlay_and_mask(overlay, mask)
        bgra32 = merge_to_bgra32(image, mask)
        self.overlay_producer.put(bgra32.tobytes())

    def run(self) -> None:
        self.start()
        try:
            while not self._manager_done.is_set():
                self.check_process_alive()
                data = self.improc_consumer.get()
                image: NDArray[uint8] = ndarray(self._shape, dtype=uint8, buffer=data)
                run_coroutine_threadsafe(self._on_image(image), self._loop)
        finally:
            self.join_safe()
            self.close_pipes()
