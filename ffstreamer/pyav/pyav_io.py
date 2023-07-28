# -*- coding: utf-8 -*-

import os
from asyncio import get_running_loop
from concurrent.futures.thread import ThreadPoolExecutor
from errno import EAGAIN
from threading import Event
from time import sleep
from typing import Final, List, Optional, Union

from av import AudioFrame, AVError, FFmpegError, VideoFrame  # noqa
from av import open as av_open  # noqa
from av.container import InputContainer, OutputContainer
from av.packet import Packet
from av.stream import Stream
from numpy import ndarray, uint8
from numpy.typing import NDArray

from ffstreamer.logging.logging import logger
from ffstreamer.pyav.pyav_callbacks import PyavCallbacks, PyavCallbacksInterface
from ffstreamer.pyav.pyav_helper import get_stream
from ffstreamer.pyav.pyav_options import (
    REALTIME_FORMATS,
    PyavHlsOutputOptions,
    PyavOptions,
)

PACKET_TYPE_VIDEO: Final[str] = "video"
PACKET_TYPE_AUDIO: Final[str] = "audio"
AUDIO_PTIME: Final[float] = 0.020  # 20ms audio packetization


class AlreadyStateError(Exception):
    def __init__(self):
        super().__init__("Already state")


class NotReadyStateError(Exception):
    def __init__(self):
        super().__init__("Not ready state")


class PyavIo:
    _source: Union[str, int]
    _destination: Optional[Union[str, PyavHlsOutputOptions]]
    _callbacks: PyavCallbacksInterface
    _options: PyavOptions
    _input_container: Optional[InputContainer]
    _output_container: Optional[OutputContainer]
    _streams: List[Stream]
    _throttle_playback: bool
    _re_request_wait_seconds: float
    _thread_quit: Event

    def __init__(
        self,
        source: Union[str, int],
        destination: Optional[Union[str, PyavHlsOutputOptions]] = None,
        callbacks: Optional[PyavCallbacksInterface] = None,
        options: Optional[PyavOptions] = None,
    ):
        self._source = source
        self._destination = destination
        self._callbacks = callbacks if callbacks else PyavCallbacks()
        self._options = options if options else PyavOptions()
        self._input_container = None
        self._output_container = None
        self._streams = list()
        self._throttle_playback = False
        self._re_request_wait_seconds = 0.001
        self._thread_quit = Event()

    @property
    def throttle_playback(self) -> bool:
        return self._throttle_playback

    @property
    def is_realtime(self) -> bool:
        return not self._throttle_playback

    @property
    def name(self) -> str:
        return self._options.name if self._options and self._options.name else str()

    @property
    def class_name(self) -> str:
        if self.name:
            return f"{type(self).__name__}[name='{self.name}']"
        else:
            return type(self).__name__

    def __repr__(self) -> str:
        return self.class_name

    def __str__(self) -> str:
        return self.class_name

    def _create_input_container(self) -> InputContainer:
        logger.debug(
            "Input container opening ... ("
            f"file='{self._source}',"
            f"{self._options.input.get_format_name()},"
            f"{self._options.input.get_timeout_argument_message()}"
            ")"
        )
        input_container = av_open(
            file=self._source,
            mode="r",
            format=self._options.input.format,
            options=self._options.input.options,
            container_options=self._options.input.container_options,
            stream_options=self._options.input.stream_options,
            metadata_encoding=self._options.input.get_metadata_encoding(),
            metadata_errors=self._options.input.get_metadata_errors(),
            buffer_size=self._options.input.get_buffer_size(),
            timeout=self._options.input.get_timeout(),
        )
        assert isinstance(input_container, InputContainer)
        logger.info("Input container opened successfully")
        return input_container

    def _create_output_container(
        self,
        video_stream: Optional[Stream] = None,
        audio_stream: Optional[Stream] = None,
    ) -> OutputContainer:
        assert self._destination is not None
        if isinstance(self._destination, str):
            file = self._destination
            if self._options.output.options is None:
                options = dict()
            else:
                options = self._options.output.options
        elif isinstance(self._destination, PyavHlsOutputOptions):
            file = self._destination.get_hls_filename()
            options = self._destination.get_hls_options()
            if self._options.output.options is not None:
                assert isinstance(self._options.output.options, dict)
                options.update(self._options.output.options)
        else:
            assert False, "Inaccessible section"

        assert file is not None
        assert options is not None
        assert isinstance(file, str)
        assert isinstance(options, dict)

        logger.debug(
            "Output container opening ... ("
            f"file='{file}',"
            f"{self._options.output.get_format_name()},"
            f"{self._options.output.get_timeout_argument_message()}"
            ")"
        )
        output_container = av_open(
            file=file,
            mode="w",
            format=self._options.output.format,
            options=options,
            container_options=self._options.output.container_options,
            stream_options=self._options.output.stream_options,
            metadata_encoding=self._options.output.get_metadata_encoding(),
            metadata_errors=self._options.output.get_metadata_errors(),
            buffer_size=self._options.output.get_buffer_size(),
            timeout=self._options.output.get_timeout(),
        )
        assert isinstance(output_container, OutputContainer)
        logger.info("Output container opened successfully")

        if video_stream is not None:
            output_container.add_stream(template=video_stream)  # noqa
        if audio_stream is not None:
            output_container.add_stream(template=audio_stream)  # noqa

        return output_container

    def _create_media(self) -> None:
        if self._destination and isinstance(self._destination, PyavHlsOutputOptions):
            cache_dir = self._destination.cache_dir
            if not os.path.isdir(cache_dir):
                raise NotADirectoryError(f"Not found cache directory: '{cache_dir}'")
            if not os.access(cache_dir, os.W_OK):
                raise PermissionError(f"Write permission is required: '{cache_dir}'")

        video_index = self._options.input.video_index
        audio_index = self._options.input.audio_index
        go_faster = self._options.go_faster
        low_delay = self._options.low_delay
        speedup_tricks = self._options.speedup_tricks

        input_container = self._create_input_container()
        output_container: Optional[OutputContainer] = None

        try:
            video_stream = get_stream(
                index=video_index,
                streams=input_container.streams.video,
                go_faster=go_faster,
                low_delay=low_delay,
                speedup_tricks=speedup_tricks,
            )
            audio_stream = get_stream(
                index=audio_index,
                streams=input_container.streams.audio,
                go_faster=go_faster,
                low_delay=low_delay,
                speedup_tricks=speedup_tricks,
            )

            assert video_stream is not None
            assert audio_stream is not None

            streams = [s for s in (video_stream, audio_stream) if s is not None]

            if video_stream is not None or audio_stream is not None:
                if self._destination is not None:
                    use_video = self._options.output.use_input_video_template
                    use_audio = self._options.output.use_input_audio_template
                    output_container = self._create_output_container(
                        video_stream if use_video else None,
                        audio_stream if use_audio else None,
                    )

            # Check whether we need to throttle playback
            container_format = set(input_container.format.name.split(","))
            throttle_playback = not container_format.intersection(REALTIME_FORMATS)
        except:  # noqa
            input_container.close()
            if output_container is not None:
                output_container.close()
            raise
        else:
            self._input_container = input_container
            self._output_container = output_container
            self._streams = streams
            self._throttle_playback = throttle_playback

    def _destroy_media(self) -> None:
        if self._input_container:
            self._input_container.close()
            self._input_container = None
        if self._output_container:
            for output_stream in self._output_container.streams:
                assert isinstance(output_stream, Stream)
                for output_packet in output_stream.encode(None):
                    self._output_container.mux(output_packet)
            self._output_container.close()
            self._output_container = None
        self._streams.clear()
        self._throttle_playback = False

    def stop(self) -> None:
        self._thread_quit.set()

    def is_open(self) -> bool:
        return self._input_container is not None

    def open(self) -> None:
        if self.is_open():
            raise AlreadyStateError()

        try:
            assert self._input_container is None
            self._create_media()
        except BaseException as e:
            logger.error(e)
            if self._input_container:
                self._destroy_media()
            raise

    def close(self) -> None:
        if not self.is_open():
            raise NotReadyStateError()

        assert self._input_container is not None
        self._destroy_media()

    def run(self) -> None:
        if not self.is_open():
            raise NotReadyStateError()

        assert self._input_container is not None
        for packet in self._input_container.demux(*self._streams):
            if self._thread_quit.is_set():
                raise InterruptedError

            assert isinstance(packet, Packet)

            # We need to skip the `flushing` packets that `demux` generates.
            if packet.dts is None:
                return

            if packet.stream.type == PACKET_TYPE_VIDEO:
                self.on_video_packet(packet)
            elif packet.stream.type == PACKET_TYPE_AUDIO:
                self.on_audio_packet(packet)
            else:
                assert False, "Inaccessible section"

    def on_video_packet(self, packet: Packet) -> None:
        for frame in packet.decode():
            if self._thread_quit.is_set():
                raise InterruptedError
            result = self.on_video_frame(frame)
            if self._output_container is not None:
                output_stream = self._output_container.streams.video[0]
                for output_packet in output_stream.encode(result):
                    self._output_container.mux(output_packet)

    def on_audio_packet(self, packet: Packet) -> None:
        for frame in packet.decode():
            if self._thread_quit.is_set():
                raise InterruptedError
            result = self.on_audio_frame(frame)
            if self._output_container is not None:
                output_stream = self._output_container.streams.audio[0]
                for output_packet in output_stream.encode(result):
                    self._output_container.mux(output_packet)

    def on_video_frame(self, frame: VideoFrame) -> VideoFrame:
        image = frame.to_ndarray(format="bgr24")
        result = self.on_image(image)
        assert isinstance(result, ndarray)
        assert len(result.shape) == 3
        assert result.shape[-1] == 3
        assert result.dtype == uint8
        return VideoFrame.from_ndarray(result, format="bgr24")  # noqa

    def on_audio_frame(self, frame: AudioFrame) -> AudioFrame:
        sound = frame.to_ndarray(format="s16", layout="stereo")
        result = self.on_sound(sound)
        return AudioFrame.from_ndarray(result, format="s16", layout="stereo")  # noqa

    def on_image(self, image: NDArray[uint8]) -> NDArray[uint8]:
        assert self
        return image

    def on_sound(self, sound: NDArray[uint8]) -> NDArray[uint8]:
        assert self
        return sound

    def _thread_main(self) -> None:
        self.open()
        try:
            while not self._thread_quit.is_set():
                try:
                    self.run()
                except (AVError, StopIteration) as e:
                    if isinstance(e, FFmpegError) and e.errno == EAGAIN:
                        sleep(self._re_request_wait_seconds)
                        continue
                    else:
                        raise
                except InterruptedError:
                    logger.info(f"{self.class_name} Interrupt signal detected")
                    break
        finally:
            self.close()

    async def run_until_complete(self) -> None:
        with ThreadPoolExecutor(max_workers=1) as executor:
            await get_running_loop().run_in_executor(executor, self._thread_main)
