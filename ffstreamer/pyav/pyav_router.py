# -*- coding: utf-8 -*-

from multiprocessing import Process
from multiprocessing.synchronize import Event
from typing import Tuple

from numpy import ndarray, uint8, zeros

from ffstreamer.memory.spsc_queue import SpscQueueConsumer, SpscQueueProducer


class PyavRouter:
    def __init__(
        self,
        shape: Tuple[int, int, int],
        receiver_consumer: SpscQueueConsumer,
        improc_producer: SpscQueueProducer,
        overlay_consumer: SpscQueueConsumer,
        sender_producer: SpscQueueProducer,
        done: Event,
    ):
        if shape[-1] != 3:
            raise ValueError("Only 3 channels are supported")

        self._shape = shape
        self._receiver_consumer = receiver_consumer
        self._improc_producer = improc_producer
        self._overlay_consumer = overlay_consumer
        self._sender_producer = sender_producer
        self._done = done

        assert self._improc_producer.maxsize == 1
        assert self._overlay_consumer.maxsize == 1
        self._now_image_processing = False

        self._overlay_shape = (self._shape[0], self._shape[1], 4)
        self._overlay = zeros(self._overlay_shape, dtype=uint8)
        self._overlay_mask = self._overlay[:, :, -1]
        self._overlay_real = self._overlay[:, :, :-1]

    def update_overlay(self, data: bytes) -> None:
        self._overlay = ndarray(self._overlay_shape, dtype=uint8, buffer=data)
        self._overlay_mask = self._overlay[:, :, -1]
        self._overlay_real = self._overlay[:, :, :-1]

    def run(self) -> None:
        while not self._done.is_set():
            self._main()

    def _main(self):
        data = self._receiver_consumer.get()

        if not self._now_image_processing:
            self._improc_producer.pull_nowait()
            if not self._improc_producer.full:
                self._improc_producer.put_nowait(data)
                self._now_image_processing = True

        if self._now_image_processing:
            self._overlay_consumer.pull_nowait()
            if not self._overlay_consumer.empty:
                overlay_data = self._overlay_consumer.get_nowait()
                self.update_overlay(overlay_data)
                self._now_image_processing = False

        image = ndarray(self._shape, dtype=uint8, buffer=data)
        image[self._overlay_mask > 0] = self._overlay_real[self._overlay_mask > 0]

        self._sender_producer.put(image.tobytes())

    def close(self) -> None:
        self._receiver_consumer.close()
        self._improc_producer.close()
        self._overlay_consumer.close()
        self._sender_producer.close()


def _pyav_router_main(
    shape: Tuple[int, int, int],
    receiver_consumer: SpscQueueConsumer,
    improc_producer: SpscQueueProducer,
    overlay_consumer: SpscQueueConsumer,
    sender_producer: SpscQueueProducer,
    done: Event,
) -> None:
    receiver = PyavRouter(
        shape,
        receiver_consumer,
        improc_producer,
        overlay_consumer,
        sender_producer,
        done,
    )
    try:
        receiver.run()
    finally:
        receiver.close()


def create_pyav_router_process(
    shape: Tuple[int, int, int],
    receiver_consumer: SpscQueueConsumer,
    improc_producer: SpscQueueProducer,
    overlay_consumer: SpscQueueConsumer,
    sender_producer: SpscQueueProducer,
    done: Event,
) -> Process:
    return Process(
        target=_pyav_router_main,
        args=(
            shape,
            receiver_consumer,
            improc_producer,
            overlay_consumer,
            sender_producer,
            done,
        ),
    )
