# -*- coding: utf-8 -*-

from multiprocessing import Process
from multiprocessing.synchronize import Event
from typing import Tuple

from av import VideoFrame  # noqa
from av import open as av_open  # noqa
from numpy import ndarray, uint8
from numpy.typing import NDArray

from ffstreamer.memory.spsc_queue import SpscQueueConsumer


class PyavSender:
    def __init__(
        self,
        destination: str,
        file_format: str,
        shape: Tuple[int, int, int],
        sender_consumer: SpscQueueConsumer,
        done: Event,
    ):
        if shape[-1] != 3:
            raise ValueError("Only 3 channels are supported")

        self._output_container = av_open(destination, mode="w", format=file_format)
        self._shape = shape
        self._sender_consumer = sender_consumer
        self._done = done

        self._output_stream = self._output_container.add_stream("libx264")
        self._output_stream.height = self._shape[0]
        self._output_stream.width = self._shape[1]
        self._output_stream.pix_fmt = "yuv420p"
        self._output_stream.options = {
            "preset": "fast",
            "crf": "28",
            "turn": "zerolatency",
        }

    def run(self) -> None:
        while not self._done.is_set():
            data = self._sender_consumer.get()
            image: NDArray[uint8] = ndarray(self._shape, dtype=uint8, buffer=data)
            frame = VideoFrame.from_ndarray(image, format="bgr24")
            for packet in self._output_stream.encode(frame):
                self._output_container.mux(packet)

    def close(self) -> None:
        self._output_container.mux(self._output_stream.encode(None))
        self._output_container.close()
        self._sender_consumer.close()


def _pyav_sender_main(
    destination: str,
    file_format: str,
    shape: Tuple[int, int, int],
    sender_consumer: SpscQueueConsumer,
    done: Event,
) -> None:
    receiver = PyavSender(destination, file_format, shape, sender_consumer, done)
    try:
        receiver.run()
    finally:
        receiver.close()


def create_pyav_sender_process(
    destination: str,
    file_format: str,
    shape: Tuple[int, int, int],
    sender_consumer: SpscQueueConsumer,
    done: Event,
) -> Process:
    return Process(
        target=_pyav_sender_main,
        args=(destination, file_format, shape, sender_consumer, done),
    )
