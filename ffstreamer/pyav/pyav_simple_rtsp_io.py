# -*- coding: utf-8 -*-

from av import open as av_open  # noqa
from av import VideoFrame  # noqa
from av.container import InputContainer, OutputContainer
from av.stream import Stream
from numpy import uint8
from numpy.typing import NDArray

from ffstreamer.logging.logging import logger


class PyavSimpleRtspIo:
    _input_container: InputContainer
    _output_container: OutputContainer

    _input_stream: Stream
    _output_stream: Stream

    def __init__(self, source: str, destination: str, file_format: str):
        self._source = source
        self._destination = destination
        self._file_format = file_format
        self._format_options = {"rtsp_transport": "tcp", "fflags": "nobuffer"}
        logger.info(f"Source URL: {self._source}")
        logger.info(f"Destination URL: {self._destination}")

    def open_rtsp(self) -> None:
        self._input_container = av_open(
            self._source,
            mode="r",
            options=self._format_options,
        )
        self._output_container = av_open(
            self._destination,
            mode="w",
            format=self._file_format,
        )

        for stream in self._input_container.streams:
            if stream.type == "video":
                self._input_stream = stream
                break

        if self._input_stream is None:
            raise IndexError("Not found video stream from source")

        self._input_stream.thread_type = "AUTO"
        self._input_stream.codec_context.low_delay = True

        self._output_stream = self._output_container.add_stream("libx264")
        self._output_stream.width = self._input_stream.width
        self._output_stream.height = self._input_stream.height
        self._output_stream.pix_fmt = "yuv420p"
        self._output_stream.options = {
            "preset": "fast",
            "crf": "28",
            "turn": "zerolatency",
        }

    async def run_rtsp(self) -> None:
        for packet in self._input_container.demux(self._input_stream):
            # We need to skip the "flushing" packets that `demux` generates.
            if packet.dts is None:
                continue

            # Discard frames from previous packets to get the latest frame.
            frames = [frame for frame in packet.decode()]
            if not frames:
                continue

            if len(frames) >= 2:
                # Discard frames from previous packets to get the latest frame.
                logger.debug(f"Discard {len(frames) - 1} frames")

            latest_frame = frames[-1]
            image = latest_frame.to_ndarray(format="bgr24")
            result = await self.on_image(image)
            next_frame = VideoFrame.from_ndarray(result, format="bgr24")

            for output_packet in self._output_stream.encode(next_frame):
                self._output_container.mux(output_packet)

    def close_rtsp(self) -> None:
        self._input_container.close()
        self._output_container.mux(self._output_stream.encode(None))
        self._output_container.close()

    async def on_image(self, image: NDArray[uint8]) -> NDArray[uint8]:
        assert self
        return image
