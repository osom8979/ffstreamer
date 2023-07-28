# -*- coding: utf-8 -*-

from multiprocessing import Process
from multiprocessing.synchronize import Event
from queue import Empty, Full
from typing import Tuple

from numpy import ndarray, newaxis, uint8, zeros
from numpy.typing import NDArray

from ffstreamer.memory.spsc_queue import SpscQueueConsumer, SpscQueueProducer
from ffstreamer.np.mask import split_mask_on_off


class PyavRouter:
    _overlay: NDArray[uint8]
    _overlay_mask: NDArray[uint8]
    _overlay_real: NDArray[uint8]
    _overlay_mask_on: NDArray[uint8]
    _overlay_mask_off: NDArray[uint8]

    def __init__(
        self,
        shape: Tuple[int, int, int],
        receiver_consumer: SpscQueueConsumer,
        improc_producer: SpscQueueProducer,
        overlay_consumer: SpscQueueConsumer,
        sender_producer: SpscQueueProducer,
        done: Event,
        synchronize=False,
        get_timeout=1.0,
        put_timeout=8.0,
    ):
        if shape[-1] != 3:
            raise ValueError("Only 3 channels are supported")

        self._shape = shape
        self._receiver_consumer = receiver_consumer
        self._improc_producer = improc_producer
        self._overlay_consumer = overlay_consumer
        self._sender_producer = sender_producer
        self._done = done
        self._synchronize = synchronize
        self._get_timeout = get_timeout
        self._put_timeout = put_timeout

        assert self._improc_producer.maxsize == 1
        assert self._overlay_consumer.maxsize == 1
        self._now_image_processing = False

        self._overlay_shape = self._shape[0], self._shape[1], 4
        self._overlay = zeros(self._overlay_shape, dtype=uint8)
        self._overlay_mask = self._overlay[:, :, -1][:, :, newaxis]
        self._overlay_real = self._overlay[:, :, :-1]
        mask_on, mask_off = split_mask_on_off(self._overlay_mask)
        self._overlay_mask_on = mask_on
        self._overlay_mask_off = mask_off

    def update_overlay(self, data: bytes) -> None:
        self._overlay = ndarray(self._overlay_shape, dtype=uint8, buffer=data)
        self._overlay_mask = self._overlay[:, :, -1][:, :, newaxis]
        self._overlay_real = self._overlay[:, :, :-1]
        mask_on, mask_off = split_mask_on_off(self._overlay_mask)
        self._overlay_mask_on = mask_on
        self._overlay_mask_off = mask_off

    def merge_overlay(self, image: NDArray[uint8]) -> NDArray[uint8]:
        # image[self._overlay_mask > 0] = self._overlay_real[self._overlay_mask > 0]
        background: NDArray[uint8] = image * self._overlay_mask_off
        overlay: NDArray[uint8] = self._overlay_real * self._overlay_mask_on
        return background + overlay

    def data_to_image(self, data: bytes) -> NDArray[uint8]:
        return ndarray(self._shape, dtype=uint8, buffer=data)

    def run(self) -> None:
        while not self._done.is_set():
            try:
                data = self._receiver_consumer.get(self._get_timeout)
            except Empty:
                continue

            if not self._now_image_processing:
                if self._synchronize:
                    while True:
                        if self._done.is_set():
                            return
                        try:
                            self._improc_producer.put(data, timeout=self._put_timeout)
                        except Full:
                            continue
                        else:
                            self._now_image_processing = True
                            break
                else:
                    self._improc_producer.pull_nowait()
                    if not self._improc_producer.full:
                        self._improc_producer.put_nowait(data)
                        self._now_image_processing = True

            if self._now_image_processing:
                if self._synchronize:
                    while True:
                        if self._done.is_set():
                            return
                        try:
                            overlay_data = self._overlay_consumer.get(self._get_timeout)
                        except Empty:
                            continue
                        else:
                            self.update_overlay(overlay_data)
                            self._now_image_processing = False
                            break
                else:
                    self._overlay_consumer.pull_nowait()
                    if not self._overlay_consumer.empty:
                        overlay_data = self._overlay_consumer.get_nowait()
                        self.update_overlay(overlay_data)
                        self._now_image_processing = False

            image = self.data_to_image(data)
            merged_image = self.merge_overlay(image)
            merged_image_data = merged_image.tobytes()

            try:
                self._sender_producer.put(merged_image_data, timeout=self._put_timeout)
            except Full:
                continue

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
    synchronize=False,
) -> None:
    receiver = PyavRouter(
        shape,
        receiver_consumer,
        improc_producer,
        overlay_consumer,
        sender_producer,
        done,
        synchronize,
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
    synchronize=False,
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
            synchronize,
        ),
    )
