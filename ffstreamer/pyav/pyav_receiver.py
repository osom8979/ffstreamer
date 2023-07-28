# -*- coding: utf-8 -*-

from multiprocessing import Process
from multiprocessing.synchronize import Event
from queue import Full

from av import open as av_open  # noqa

from ffstreamer.memory.spsc_queue import SpscQueueProducer


class PyavReceiver:
    def __init__(
        self,
        source: str,
        receiver_producer: SpscQueueProducer,
        done: Event,
        *,
        put_timeout=32.0,
        drop_if_put_timeout=True,
    ):
        if source.startswith("rtsp://"):
            format_options = {"rtsp_transport": "tcp", "fflags": "nobuffer"}
        else:
            format_options = None

        self._put_timeout = put_timeout
        self._drop_if_put_timeout = drop_if_put_timeout
        self._input_container = av_open(source, mode="r", options=format_options)
        self._receiver_producer = receiver_producer
        self._done = done

        self._video_stream = None
        for stream in self._input_container.streams:
            if stream.type == "video":
                self._video_stream = stream

        if self._video_stream is None:
            raise IndexError("Not found video stream")

        self._video_stream.thread_type = "AUTO"
        self._video_stream.codec_context.low_delay = True

    def run(self) -> None:
        for packet in self._input_container.demux(self._video_stream):
            if self._done.is_set():
                return

            # We need to skip the "flushing" packets that `demux` generates.
            if packet.dts is None:
                continue

            for frame in packet.decode():
                if not frame:
                    continue

                image = frame.to_ndarray(format="bgr24")
                data = image.tobytes()

                while True:
                    if self._done.is_set():
                        return

                    try:
                        self._receiver_producer.put(data, timeout=self._put_timeout)
                    except Full:
                        if self._drop_if_put_timeout:
                            break
                        else:
                            continue
                    else:
                        break

    def close(self) -> None:
        self._input_container.close()
        self._receiver_producer.close()


def _pyav_receiver_main(
    source: str,
    receiver_producer: SpscQueueProducer,
    done: Event,
) -> None:
    receiver = PyavReceiver(source, receiver_producer, done)
    try:
        receiver.run()
    finally:
        receiver.close()


def create_pyav_receiver_process(
    source: str,
    receiver_producer: SpscQueueProducer,
    done: Event,
) -> Process:
    return Process(
        target=_pyav_receiver_main,
        args=(source, receiver_producer, done),
    )
