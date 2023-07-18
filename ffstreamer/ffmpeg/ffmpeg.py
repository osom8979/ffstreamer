# -*- coding: utf-8 -*-

from subprocess import check_output
from typing import Final, List, NamedTuple

BGR24_CHANNELS: Final[int] = 3
MINIMUM_REALTIME_FRAMES: Final[int] = 12
MEGA_BYTE_UNIT: Final[int] = 1024 * 1024
DEFAULT_BUFFER_SIZE: Final[int] = 100 * MEGA_BYTE_UNIT

# fmt: off
DEFAULT_FFMPEG_INPUT_FORMAT: Final[str] = (
    # global options
    "-hide_banner "
    # infile options
    "-i {src} "
    # outfile options
    "-f image2pipe -pix_fmt bgr24 -vcodec rawvideo pipe:1"
)
DEFAULT_FFMPEG_OUTPUT_FORMAT: Final[str] = (
    # global options
    "-hide_banner "
    # infile options
    "-f rawvideo -pix_fmt bgr24 -s {width}x{height} -i pipe:0 "
    # outfile options
    "-c:v libx264 -f {format} {dest}"
)
# fmt: on

FFMPEG_PIX_FMTS_HEADER_LINES: Final[int] = 8
"""
Skip unnecessary header lines in `ffmpeg -hide_banner -pix_fmts` command.
Perhaps something like this:

```
Pixel formats:
I.... = Supported Input  format for conversion
.O... = Supported Output format for conversion
..H.. = Hardware accelerated format
...P. = Paletted format
....B = Bitstream format
FLAGS NAME            NB_COMPONENTS BITS_PER_PIXEL
-----
```

For reference, the next line would look something like this:

```
IO... yuv420p                3            12
IO... yuyv422                3            16
IO... rgb24                  3            24
IO... bgr24                  3            24
IO... yuv422p                3            16
IO... yuv444p                3            24
IO... yuv410p                3             9
IO... yuv411p                3            12
IO... gray                   1             8
```
"""


class PixFmt(NamedTuple):
    supported_input_format: bool
    supported_output_format: bool
    hardware_accelerated_format: bool
    paletted_format: bool
    bitstream_format: bool
    name: str
    nb_components: int
    bits_per_pixel: int


def inspect_pix_fmts(ffmpeg_path="ffmpeg") -> List[PixFmt]:
    output = check_output([ffmpeg_path, "-hide_banner", "-pix_fmts"]).decode("utf-8")
    lines = output.splitlines()[FFMPEG_PIX_FMTS_HEADER_LINES:]

    result = list()
    for line in lines:
        cols = [c.strip() for c in line.split()]
        assert len(cols) == 4
        flags = cols[0]
        fmt = PixFmt(
            supported_input_format=(flags[0] == "I"),
            supported_output_format=(flags[1] == "O"),
            hardware_accelerated_format=(flags[2] == "H"),
            paletted_format=(flags[3] == "P"),
            bitstream_format=(flags[4] == "B"),
            name=cols[1],
            nb_components=int(cols[2]),
            bits_per_pixel=int(cols[3]),
        )
        result.append(fmt)
    return result


FFMPEG_FILE_FORMATS_HEADER_LINES: Final[int] = 4
"""
Skip unnecessary header lines in `ffmpeg -hide_banner -formats` command.
Perhaps something like this:

```
File formats:
 D. = Demuxing supported
 .E = Muxing supported
 --
```

For reference, the next line would look something like this:

```
 D  3dostr          3DO STR
  E 3g2             3GP2 (3GPP2 file format)
  E 3gp             3GP (3GPP file format)
 D  4xm             4X Technologies
  E a64             a64 - video for Commodore 64
 D  aa              Audible AA format files
 D  aac             raw ADTS AAC (Advanced Audio Coding)
 D  aax             CRI AAX
 DE ac3             raw AC-3
```
"""


class FileFormat(NamedTuple):
    supported_demuxing: bool
    supported_muxing: bool
    name: str
    description: str


def inspect_file_formats(ffmpeg_path="ffmpeg") -> List[FileFormat]:
    output = check_output([ffmpeg_path, "-hide_banner", "-formats"]).decode("utf-8")
    lines = output.splitlines()[FFMPEG_FILE_FORMATS_HEADER_LINES:]

    result = list()
    for line in lines:
        supported_demuxing = line[1] == "D"
        supported_muxing = line[2] == "E"
        name, desc = line[4:].split(maxsplit=1)
        fmt = FileFormat(
            supported_demuxing=supported_demuxing,
            supported_muxing=supported_muxing,
            name=name,
            description=desc,
        )
        result.append(fmt)
    return result


def calc_recommend_buffer_size(
    width: int,
    height: int,
    channels=BGR24_CHANNELS,
    frames=MINIMUM_REALTIME_FRAMES,
) -> int:
    assert channels >= 1
    assert frames >= 1
    return width * height * channels * frames


def calc_minimum_buffer_size(
    width: int,
    height: int,
    channels=BGR24_CHANNELS,
    frames=MINIMUM_REALTIME_FRAMES,
) -> int:
    recommend_size = calc_recommend_buffer_size(width, height, channels, frames)
    return min(DEFAULT_BUFFER_SIZE, recommend_size)
