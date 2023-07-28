# -*- coding: utf-8 -*-

import os.path
from dataclasses import dataclass, field
from tempfile import mkdtemp
from typing import Any, Dict, Final, List, Literal, Optional, Tuple, Union

# noinspection SpellCheckingInspection
REALTIME_FORMATS = (
    "alsa",
    "android_camera",
    "avfoundation",
    "bktr",
    "decklink",
    "dshow",
    "fbdev",
    "gdigrab",
    "iec61883",
    "jack",
    "kmsgrab",
    "openal",
    "oss",
    "pulse",
    "sndio",
    "rtsp",
    "v4l2",
    "vfwcap",
    "x11grab",
)

# noinspection SpellCheckingInspection
DEFAULT_RTSP_OPTIONS = {
    "rtsp_transport": "tcp",
    "fflags": "nobuffer",
}

DEFAULT_IO_BUFFER_SIZE: Final[int] = 24_883_200
"""Size of buffer for Python input/output operations in bytes.
Honored only when file is a file-like object.
Make it a buffer size for 4k RGB images.
3840 * 2160 * 3 = 24883200 byte
"""

DEFAULT_AV_OPEN_TIMEOUT: Final[float] = 20.0
DEFAULT_AV_READ_TIMEOUT: Final[float] = 8.0

DEFAULT_AV_TIMEOUT: Final[Tuple[float, float]] = (
    DEFAULT_AV_OPEN_TIMEOUT,
    DEFAULT_AV_READ_TIMEOUT,
)

HLS_MASTER_FILENAME: Final[str] = "master.m3u8"
HLS_SEGMENT_FILENAME: Final[str] = "%Y-%m-%d_%H-%M-%S.ts"


@dataclass
class CommonMediaOptions:
    format: Optional[str] = None
    """Specific format to use.
    Defaults to 'autodect'.
    """

    options: Optional[Dict[str, Any]] = None
    """Options to pass to the container and all streams.
    """

    container_options: Optional[Dict[str, Any]] = None
    """Options to pass to the container.
    """

    stream_options: Optional[List[str]] = None
    """Options to pass to each stream.
    """

    metadata_encoding: Optional[str] = None
    """Encoding to use when reading or writing file metadata.
    Defaults to 'utf-8'.
    """

    metadata_errors: Optional[str] = None
    """Specifies how to handle encoding errors; behaves like str.encode parameter.
    Defaults to 'strict'.
    """

    buffer_size: Optional[int] = None
    """Size of buffer for Python input/output operations in bytes.
    Honored only when file is a file-like object.
    Defaults to 32768 (32k).
    """

    timeout: Optional[Union[float, Tuple[float, float]]] = None
    """How many seconds to wait for data before giving up, as a float,
    or a (open timeout, read timeout) tuple.
    """

    def get_metadata_encoding(self) -> str:
        if self.metadata_encoding:
            return self.metadata_encoding
        else:
            return "utf-8"

    def get_metadata_errors(self) -> str:
        if self.metadata_errors:
            return self.metadata_errors
        else:
            return "strict"

    def get_buffer_size(self) -> int:
        if self.buffer_size is not None:
            if self.buffer_size >= 0:
                return self.buffer_size
        return DEFAULT_IO_BUFFER_SIZE

    def get_timeout(self) -> Union[float, Tuple[float, float]]:
        if self.timeout is not None:
            return self.timeout
        else:
            return DEFAULT_AV_TIMEOUT

    def get_format_name(self) -> str:
        return f"format={self.format}" if self.format else "format=autodect"

    def get_timeout_argument_message(self) -> str:
        timeout = self.get_timeout()
        if isinstance(timeout, tuple):
            assert len(timeout) == 2
            return f"timeout.open={timeout[0]}s,timeout.read={timeout[1]}s"
        else:
            return f"timeout={timeout}s"


@dataclass
class PyavInputOptions(CommonMediaOptions):
    video_index: Optional[int] = 0
    """The video index of the InputContainer.
    """

    audio_index: Optional[int] = None
    """The audio index of the InputContainer.
    """


@dataclass
class PyavOutputOptions(CommonMediaOptions):
    use_input_video_template: bool = True
    """Use video template from input container.
    """

    use_input_audio_template: bool = False
    """Use audio template from input container.
    """


@dataclass
class PyavOptions:
    input: PyavInputOptions = field(default_factory=PyavInputOptions)
    """Input file options.
    """

    output: PyavOutputOptions = field(default_factory=PyavOutputOptions)
    """Output file options.
    """

    name: Optional[str] = None
    """A unique, human-readable name.
    """

    go_faster: bool = True
    """Thread type is frame+slice.
    """

    low_delay: bool = True
    """Flag is low delay. This flag is force low delay.
    """

    speedup_tricks: bool = False
    """Flag2 is fast. This flag2 is allow non-spec compliant speedup tricks.
    """


@dataclass
class PyavHlsOutputOptions:
    destination_dir: str
    """Local directory to store processed segmentation files.
    """

    cache_dir: str = field(default_factory=lambda: mkdtemp())
    """Cache directory for temporarily storing HLS segmentation files.
    """

    strftime: bool = True
    """Use strftime() on filename to expand the segment filename with localtime.
    """

    strftime_mkdir: bool = True
    """It will create all subdirectories which is expanded in filename.
    """

    hls_time: int = 10
    """Set the target segment length.
    """

    hls_playlist_type: Union[str, Literal["vod", "event"]] = "vod"
    """
    "event"
        Emit `#EXT-X-PLAYLIST-TYPE:EVENT` in the m3u8 header.
        Forces hls_list_size to 0; the playlist can only be appended to.

    "vod"
        Emit `#EXT-X-PLAYLIST-TYPE:VOD` in the m3u8 header.
        Forces hls_list_size to 0; the playlist must not change.
    """

    drop_first_segment_file: bool = True
    """Remove the first segment file.
    The first segment file will most likely contain error packets.
    """

    def get_hls_filename(self) -> str:
        return os.path.join(self.cache_dir, HLS_MASTER_FILENAME)

    def get_hls_segment_filename(self) -> str:
        return os.path.join(self.cache_dir, HLS_SEGMENT_FILENAME)

    def get_hls_options(self) -> Dict[str, Any]:
        """
        <https://ffmpeg.org/ffmpeg-formats.html#hls-2>

        :return:
            FFmpeg HLS options dictionary.
        """

        options = dict()
        options["strftime"] = "1" if self.strftime else "0"
        options["strftime_mkdir"] = "1" if self.strftime_mkdir else "0"
        options["hls_time"] = str(self.hls_time)
        if self.hls_playlist_type:
            if self.hls_playlist_type in ("vod", "event"):
                options["hls_playlist_type"] = self.hls_playlist_type
            else:
                raise ValueError(f"Unknown hls_playlist_type: {self.hls_playlist_type}")
        options["hls_segment_filename"] = self.get_hls_segment_filename()
        # "hls_list_size": "0",
        # "hls_flags": "second_level_segment_index",
        return options
