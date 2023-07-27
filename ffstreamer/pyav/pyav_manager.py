# -*- coding: utf-8 -*-

from asyncio import AbstractEventLoop, get_event_loop, run_coroutine_threadsafe
from multiprocessing import Event as NewEvent
from multiprocessing.synchronize import Event
from typing import Optional

from numpy import ndarray, uint8

from ffstreamer.memory.spsc_queue import SpscQueue
from ffstreamer.pyav.pyav_callbacks import PyavCallbacks, PyavCallbacksInterface
from ffstreamer.pyav.pyav_receiver import create_pyav_receiver_process
from ffstreamer.pyav.pyav_router import create_pyav_router_process
from ffstreamer.pyav.pyav_sender import create_pyav_sender_process


def _create_event() -> Event:
    return NewEvent()


class PyavManager:
    def __init__(
        self,
        source: str,
        destination: str,
        width: int,
        height: int,
        channels=3,
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
        self._shape = height, width, channels
        self._item_size = height * width * channels

        self._overlay_queue_size = 1
        self._overlay_shape = height, width, channels + 1
        self._overlay_item_size = height * width * channels
        assert self._overlay_queue_size == 1
        assert self._overlay_shape[-1] == 4

        self._receiver = SpscQueue(self._queue_size, self._item_size)
        self._improc = SpscQueue(self._queue_size, self._item_size)
        self._overlay = SpscQueue(self._overlay_queue_size, self._item_size)
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

    async def _on_image(self, image: ndarray) -> None:
        overlay_image = await self._callbacks.on_image(image)
        if overlay_image.shape != self._overlay_shape:
            raise ValueError("Overlay shape does not match")

        data = overlay_image.tobytes()
        self.overlay_producer.put(data)

    def run(self) -> None:
        self.start()
        try:
            while not self._manager_done.is_set():
                self.check_process_alive()
                data = self.improc_consumer.get()
                image: ndarray
                image = ndarray(self._shape, dtype=uint8, buffer=data)
                run_coroutine_threadsafe(self._on_image(image), self._loop)
        finally:
            self.join_safe()
            self.close_pipes()
